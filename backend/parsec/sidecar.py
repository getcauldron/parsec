"""Parsec sidecar — stdin/stdout JSON protocol handler.

Reads newline-delimited JSON commands from stdin, dispatches by `cmd` field,
writes single-line JSON responses to stdout. Stderr is reserved for logging.
Stdout is forced to line-buffered mode before any other imports to prevent
buffering issues when spawned by Tauri or PyInstaller.

Protocol (NDJSON):
    → {"cmd": "hello"}
    ← {"status": "ok", "message": "parsec sidecar ready", "version": "0.1.0"}
    → {"cmd": "status"}
    ← {"status": "ok", "uptime_seconds": 12.3, "engine_ready": false}
    → {"cmd": "unknown"}
    ← {"status": "error", "error": "unknown command: unknown"}
"""

from __future__ import annotations

# Force line-buffered stdout BEFORE any other imports.
# This is critical — PyInstaller binaries fully buffer stdout when spawned
# from a parent process, which silently breaks sidecar communication.
import sys

sys.stdout.reconfigure(line_buffering=True)

import json
import logging
import signal
import time

VERSION = "0.1.0"

logger = logging.getLogger("parsec.sidecar")


def _configure_logging() -> None:
    """Send all log output to stderr — stdout is reserved for protocol."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def _send(response: dict) -> None:
    """Write a single-line JSON response to stdout and flush."""
    sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _handle_command(cmd_obj: dict, start_time: float) -> dict:
    """Dispatch a command and return the response dict."""
    cmd = cmd_obj.get("cmd")

    if cmd == "hello":
        return {
            "status": "ok",
            "message": "parsec sidecar ready",
            "version": VERSION,
        }

    if cmd == "status":
        return {
            "status": "ok",
            "uptime_seconds": round(time.monotonic() - start_time, 3),
            "engine_ready": False,
        }

    return {"status": "error", "error": f"unknown command: {cmd}"}


def main() -> None:
    """Run the sidecar protocol loop.

    Reads NDJSON from stdin, dispatches commands, writes responses to stdout.
    Exits cleanly on stdin EOF or SIGTERM.
    """
    _configure_logging()

    start_time = time.monotonic()
    running = True

    def _shutdown(signum: int, frame: object) -> None:
        nonlocal running
        logger.info("Received signal %d, shutting down", signum)
        running = False

    signal.signal(signal.SIGTERM, _shutdown)

    logger.info("Sidecar started (version %s)", VERSION)

    try:
        while running:
            try:
                line = sys.stdin.readline()
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt, shutting down")
                break

            # EOF — parent closed stdin or process is terminating
            if not line:
                logger.info("Stdin EOF, shutting down")
                break

            line = line.strip()
            if not line:
                continue

            try:
                cmd_obj = json.loads(line)
            except json.JSONDecodeError as exc:
                _send({"status": "error", "error": f"invalid JSON: {exc}"})
                continue

            if not isinstance(cmd_obj, dict):
                _send({"status": "error", "error": "expected JSON object"})
                continue

            response = _handle_command(cmd_obj, start_time)
            _send(response)

    except Exception:
        logger.exception("Unexpected error in sidecar main loop")
        raise
    finally:
        logger.info("Sidecar exiting")


if __name__ == "__main__":
    main()
