"""Parsec sidecar — stdin/stdout JSON protocol handler.

Reads newline-delimited JSON commands from stdin, dispatches by `cmd` field,
writes single-line JSON responses to stdout. Stderr is reserved for logging.
Stdout is forced to line-buffered mode before any other imports to prevent
buffering issues when spawned by Tauri or PyInstaller.

Protocol (NDJSON):
    → {"cmd": "hello"}
    ← {"status": "ok", "message": "parsec sidecar ready", "version": "0.1.0", "id": null}
    → {"cmd": "status"}
    ← {"status": "ok", "uptime_seconds": 12.3, "engine_ready": false, "id": null}
    → {"cmd": "process_file", "id": "req-1", "input_path": "/path/to/scan.png"}
    ← {"type": "progress", "id": "req-1", "stage": "queued"}
    ← {"type": "progress", "id": "req-1", "stage": "processing"}
    ← {"type": "progress", "id": "req-1", "stage": "complete", "output_path": "...", "duration": 1.23}
    → {"cmd": "unknown"}
    ← {"status": "error", "error": "unknown command: unknown", "id": null}
"""

from __future__ import annotations

# Force line-buffered stdout BEFORE any other imports.
# This is critical — PyInstaller binaries fully buffer stdout when spawned
# from a parent process, which silently breaks sidecar communication.
import sys

sys.stdout.reconfigure(line_buffering=True)

import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import signal  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

VERSION = "0.1.0"

# Supported file extensions for process_file
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".pdf"}

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


def _handle_command(cmd_obj: dict, start_time: float, state: _SidecarState) -> None:
    """Dispatch a command and send response(s) to stdout.

    Some commands (like process_file) emit multiple progress events,
    so this function calls _send() directly rather than returning a single dict.
    All responses include the request ``id`` from the incoming command.
    """
    cmd = cmd_obj.get("cmd")
    req_id = cmd_obj.get("id")  # None for hello/status, required for process_file

    if cmd == "hello":
        _send({
            "status": "ok",
            "message": "parsec sidecar ready",
            "version": VERSION,
            "id": req_id,
        })
        return

    if cmd == "status":
        _send({
            "status": "ok",
            "uptime_seconds": round(time.monotonic() - start_time, 3),
            "engine_ready": state.engine_used,
            "id": req_id,
        })
        return

    if cmd == "process_file":
        _handle_process_file(cmd_obj, req_id, state)
        return

    if cmd == "get_languages":
        from parsec.languages import all_languages

        _send({
            "status": "ok",
            "languages": all_languages(),
            "id": req_id,
        })
        return

    _send({"status": "error", "error": f"unknown command: {cmd}", "id": req_id})


def _handle_process_file(
    cmd_obj: dict, req_id: str | None, state: _SidecarState
) -> None:
    """Handle the process_file command — validate, run pipeline, emit progress."""
    # --- Validate required fields ---
    input_path_str = cmd_obj.get("input_path")
    if not req_id:
        _send({
            "status": "error",
            "error": "process_file requires an 'id' field",
            "id": req_id,
        })
        return

    if not input_path_str:
        _send({
            "type": "progress",
            "id": req_id,
            "stage": "error",
            "error": "process_file requires an 'input_path' field",
        })
        return

    input_path = Path(input_path_str)

    # --- Validate file extension ---
    ext = input_path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        _send({
            "type": "progress",
            "id": req_id,
            "stage": "error",
            "error": f"Unsupported file extension: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        })
        return

    # --- Read language (defaults to English) ---
    language = cmd_obj.get("language", "en")

    # --- Read preprocessing options ---
    deskew = cmd_obj.get("deskew", False)
    rotate_pages = cmd_obj.get("rotate_pages", False)
    clean = cmd_obj.get("clean", False)
    skip_text = cmd_obj.get("skip_text", False)
    force_ocr = cmd_obj.get("force_ocr", False)

    # Default to skip_text=True for PDF inputs when no explicit mode is set
    is_pdf = ext == ".pdf"
    if is_pdf and not skip_text and not force_ocr:
        skip_text = True

    logger.info(
        "process_file id=%s language=%s path=%s deskew=%s rotate=%s clean=%s skip_text=%s force_ocr=%s",
        req_id, language, input_path, deskew, rotate_pages, clean, skip_text, force_ocr,
    )

    # --- Validate language code ---
    try:
        from parsec.languages import get_language

        get_language(language)
    except ValueError as exc:
        _send({
            "type": "progress",
            "id": req_id,
            "stage": "error",
            "error": str(exc),
        })
        return

    # --- Compute output path: strip ext, append _ocr.pdf ---
    # "scan.png" → "scan_ocr.pdf", "my.photo.jpg" → "my.photo_ocr.pdf"
    output_path = input_path.parent / (input_path.stem + "_ocr.pdf")

    # --- Emit queued ---
    _send({"type": "progress", "id": req_id, "stage": "queued"})

    # --- Emit initializing if this is the first file ---
    if not state.engine_used:
        _send({"type": "progress", "id": req_id, "stage": "initializing"})
        state.engine_used = True

    # --- Emit processing ---
    _send({"type": "progress", "id": req_id, "stage": "processing"})

    # --- Run the pipeline with stdout protection ---
    try:
        from parsec.models import OcrOptions
        from parsec.pipeline import process_file as run_pipeline

        ocr_options = OcrOptions(
            language=language,
            deskew=deskew,
            rotate_pages=rotate_pages,
            clean=clean,
            skip_text=skip_text,
            force_ocr=force_ocr,
        )

        # Defense in depth: redirect stdout to devnull during pipeline execution
        # to prevent any C++ noise from PaddleOCR/PaddlePaddle corrupting the protocol.
        real_stdout = sys.stdout
        try:
            sys.stdout = open(os.devnull, "w")
            result = run_pipeline(input_path, output_path, options=ocr_options)
        finally:
            sys.stdout.close()
            sys.stdout = real_stdout

    except Exception as exc:
        logger.exception("Pipeline crashed for %s", input_path)
        _send({
            "type": "progress",
            "id": req_id,
            "stage": "error",
            "error": f"{type(exc).__name__}: {exc}",
        })
        return

    # --- Emit result ---
    if result.success:
        complete_event: dict = {
            "type": "progress",
            "id": req_id,
            "stage": "complete",
            "output_path": str(result.output_path),
            "duration": round(result.duration_seconds, 3),
        }
        if result.already_searchable:
            complete_event["already_searchable"] = True
        _send(complete_event)
    else:
        _send({
            "type": "progress",
            "id": req_id,
            "stage": "error",
            "error": result.error or "Unknown pipeline error",
        })


class _SidecarState:
    """Mutable state for the sidecar session."""

    __slots__ = ("engine_used",)

    def __init__(self) -> None:
        self.engine_used: bool = False


def main() -> None:
    """Run the sidecar protocol loop.

    Reads NDJSON from stdin, dispatches commands, writes responses to stdout.
    Exits cleanly on stdin EOF or SIGTERM.
    """
    _configure_logging()

    start_time = time.monotonic()
    state = _SidecarState()
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

            _handle_command(cmd_obj, start_time, state)

    except Exception:
        logger.exception("Unexpected error in sidecar main loop")
        raise
    finally:
        logger.info("Sidecar exiting")


if __name__ == "__main__":
    main()
