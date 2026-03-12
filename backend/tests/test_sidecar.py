"""Tests for the sidecar NDJSON protocol.

Uses subprocess to test the actual sidecar process — this catches
buffering issues that unit-testing the dispatch function alone would miss.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

SIDECAR_MODULE = "parsec.sidecar"
BACKEND_DIR = Path(__file__).resolve().parent.parent


def _run_sidecar(input_lines: list[str], timeout: float = 10.0) -> list[dict]:
    """Send NDJSON lines to the sidecar process and collect responses.

    Returns parsed JSON responses from stdout.
    """
    stdin_data = "\n".join(input_lines) + "\n"

    result = subprocess.run(
        [sys.executable, "-m", SIDECAR_MODULE],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(BACKEND_DIR),
    )

    responses = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line:
            responses.append(json.loads(line))

    return responses


def test_hello_command():
    """hello command returns expected response shape."""
    responses = _run_sidecar(['{"cmd":"hello"}'])
    assert len(responses) == 1

    resp = responses[0]
    assert resp["status"] == "ok"
    assert resp["message"] == "parsec sidecar ready"
    assert "version" in resp
    assert resp["version"] == "0.1.0"


def test_status_command():
    """status command returns uptime and engine_ready fields."""
    responses = _run_sidecar(['{"cmd":"status"}'])
    assert len(responses) == 1

    resp = responses[0]
    assert resp["status"] == "ok"
    assert "uptime_seconds" in resp
    assert isinstance(resp["uptime_seconds"], (int, float))
    assert resp["uptime_seconds"] >= 0
    assert "engine_ready" in resp
    assert resp["engine_ready"] is False


def test_unknown_command():
    """Unknown command returns error response with command name."""
    responses = _run_sidecar(['{"cmd":"frobnicate"}'])
    assert len(responses) == 1

    resp = responses[0]
    assert resp["status"] == "error"
    assert "frobnicate" in resp["error"]


def test_malformed_json():
    """Malformed JSON input produces error response without crashing."""
    responses = _run_sidecar(["this is not json"])
    assert len(responses) == 1

    resp = responses[0]
    assert resp["status"] == "error"
    assert "invalid JSON" in resp["error"]


def test_non_object_json():
    """JSON array/number/string produces error response."""
    responses = _run_sidecar(['[1, 2, 3]'])
    assert len(responses) == 1

    resp = responses[0]
    assert resp["status"] == "error"
    assert "expected JSON object" in resp["error"]


def test_multiple_commands():
    """Multiple commands in sequence all get responses."""
    responses = _run_sidecar([
        '{"cmd":"hello"}',
        '{"cmd":"status"}',
        '{"cmd":"unknown_cmd"}',
    ])
    assert len(responses) == 3
    assert responses[0]["status"] == "ok"
    assert responses[0]["message"] == "parsec sidecar ready"
    assert responses[1]["status"] == "ok"
    assert "uptime_seconds" in responses[1]
    assert responses[2]["status"] == "error"


def test_stdin_eof_clean_exit():
    """Stdin EOF causes clean exit (exit code 0)."""
    result = subprocess.run(
        [sys.executable, "-m", SIDECAR_MODULE],
        input="",
        capture_output=True,
        text=True,
        timeout=10.0,
        cwd=str(BACKEND_DIR),
    )
    assert result.returncode == 0


def test_no_non_json_on_stdout():
    """Stdout contains only valid JSON lines — no log noise, no debug output."""
    result = subprocess.run(
        [sys.executable, "-m", SIDECAR_MODULE],
        input='{"cmd":"hello"}\n{"cmd":"status"}\n',
        capture_output=True,
        text=True,
        timeout=10.0,
        cwd=str(BACKEND_DIR),
    )

    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Every non-empty stdout line must be valid JSON
        parsed = json.loads(line)
        assert isinstance(parsed, dict), f"Expected JSON object, got: {line}"


def test_logging_goes_to_stderr():
    """Sidecar log messages appear on stderr, not stdout."""
    result = subprocess.run(
        [sys.executable, "-m", SIDECAR_MODULE],
        input='{"cmd":"hello"}\n',
        capture_output=True,
        text=True,
        timeout=10.0,
        cwd=str(BACKEND_DIR),
    )

    # stderr should have log output (at minimum the startup and shutdown messages)
    assert result.stderr.strip(), "Expected log output on stderr"
    assert "Sidecar started" in result.stderr or "sidecar" in result.stderr.lower()
