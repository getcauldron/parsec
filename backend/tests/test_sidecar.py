"""Tests for the sidecar NDJSON protocol.

Uses subprocess to test the actual sidecar process — this catches
buffering issues that unit-testing the dispatch function alone would miss.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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


# ─── process_file tests ───────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def test_process_file_happy_path(tmp_path):
    """process_file with a real fixture image emits progress events and produces a PDF."""
    # Copy fixture to tmp_path so output lands somewhere clean
    import shutil

    src = FIXTURES_DIR / "clean_01.png"
    input_file = tmp_path / "clean_01.png"
    shutil.copy2(src, input_file)

    cmd = json.dumps({
        "cmd": "process_file",
        "id": "happy-1",
        "input_path": str(input_file),
    })

    responses = _run_sidecar([cmd], timeout=120.0)

    # Should get at least: queued, initializing (first file), processing, complete
    stages = [r.get("stage") for r in responses if r.get("type") == "progress"]
    assert "queued" in stages, f"Expected 'queued' stage, got stages: {stages}"
    assert "processing" in stages, f"Expected 'processing' stage, got stages: {stages}"
    assert "complete" in stages, f"Expected 'complete' stage, got stages: {stages}"

    # Verify the complete event has output_path and duration
    complete_event = next(r for r in responses if r.get("stage") == "complete")
    assert "output_path" in complete_event
    assert "duration" in complete_event
    assert complete_event["duration"] > 0

    # Verify PDF was actually created
    output_pdf = Path(complete_event["output_path"])
    assert output_pdf.exists(), f"Expected output PDF at {output_pdf}"
    assert output_pdf.stat().st_size > 0


def test_process_file_missing_file():
    """process_file with a nonexistent path emits an error stage."""
    cmd = json.dumps({
        "cmd": "process_file",
        "id": "missing-1",
        "input_path": "/nonexistent/path/ghost.png",
    })

    responses = _run_sidecar([cmd], timeout=30.0)

    # Should get progress events ending with error (pipeline returns error for missing file)
    progress = [r for r in responses if r.get("type") == "progress"]
    assert len(progress) >= 1

    last = progress[-1]
    assert last["stage"] == "error"
    assert last["id"] == "missing-1"
    assert "error" in last


def test_process_file_unsupported_extension(tmp_path):
    """process_file with a .txt file emits immediate error — no queued/processing stages."""
    txt_file = tmp_path / "readme.txt"
    txt_file.write_text("not an image")

    cmd = json.dumps({
        "cmd": "process_file",
        "id": "ext-1",
        "input_path": str(txt_file),
    })

    responses = _run_sidecar([cmd], timeout=10.0)

    # Should be a single error progress event (validation rejects before queuing)
    progress = [r for r in responses if r.get("type") == "progress"]
    assert len(progress) == 1
    assert progress[0]["stage"] == "error"
    assert progress[0]["id"] == "ext-1"
    assert "Unsupported file extension" in progress[0]["error"]


def test_process_file_id_correlation(tmp_path):
    """All progress events carry the same id from the request."""
    import shutil

    src = FIXTURES_DIR / "clean_01.png"
    input_file = tmp_path / "corr_test.png"
    shutil.copy2(src, input_file)

    test_id = "correlation-test-42"
    cmd = json.dumps({
        "cmd": "process_file",
        "id": test_id,
        "input_path": str(input_file),
    })

    responses = _run_sidecar([cmd], timeout=120.0)

    progress = [r for r in responses if r.get("type") == "progress"]
    assert len(progress) >= 3, f"Expected at least 3 progress events, got {len(progress)}"

    for event in progress:
        assert event["id"] == test_id, f"Expected id={test_id}, got id={event.get('id')} in event: {event}"


def test_process_file_output_path(tmp_path):
    """Output file is named correctly: scan.png → scan_ocr.pdf."""
    import shutil

    src = FIXTURES_DIR / "clean_01.png"
    input_file = tmp_path / "scan.png"
    shutil.copy2(src, input_file)

    cmd = json.dumps({
        "cmd": "process_file",
        "id": "path-1",
        "input_path": str(input_file),
    })

    responses = _run_sidecar([cmd], timeout=120.0)

    complete = [r for r in responses if r.get("stage") == "complete"]
    assert len(complete) == 1

    output_path = Path(complete[0]["output_path"])
    assert output_path.name == "scan_ocr.pdf"
    assert output_path.parent == tmp_path


# ─── PDF extension and preprocessing tests ─────────────────────────────


def test_process_file_pdf_extension_accepted(tmp_path):
    """PDF files are accepted by the sidecar (no unsupported extension error)."""
    import shutil

    src = FIXTURES_DIR / "pdf_nosearch_01.pdf"
    input_file = tmp_path / "document.pdf"
    shutil.copy2(src, input_file)

    cmd = json.dumps({
        "cmd": "process_file",
        "id": "pdf-ext-1",
        "input_path": str(input_file),
    })

    responses = _run_sidecar([cmd], timeout=120.0)

    progress = [r for r in responses if r.get("type") == "progress"]
    stages = [r.get("stage") for r in progress]

    # Should NOT get an "Unsupported file extension" error
    for r in progress:
        if r.get("stage") == "error":
            assert "Unsupported file extension" not in r.get("error", ""), \
                f"PDF should be accepted, got error: {r['error']}"

    # Should reach at least queued + processing
    assert "queued" in stages, f"Expected 'queued' stage, got: {stages}"
    assert "processing" in stages or "complete" in stages, \
        f"Expected processing or complete, got: {stages}"


def test_process_file_pdf_output_naming(tmp_path):
    """PDF input: document.pdf → document_ocr.pdf."""
    import shutil

    src = FIXTURES_DIR / "pdf_nosearch_01.pdf"
    input_file = tmp_path / "document.pdf"
    shutil.copy2(src, input_file)

    cmd = json.dumps({
        "cmd": "process_file",
        "id": "pdf-name-1",
        "input_path": str(input_file),
    })

    responses = _run_sidecar([cmd], timeout=120.0)

    complete = [r for r in responses if r.get("stage") == "complete"]
    assert len(complete) == 1
    output_path = Path(complete[0]["output_path"])
    assert output_path.name == "document_ocr.pdf"


def test_process_file_preprocessing_options_logged(tmp_path):
    """Preprocessing options from command JSON appear in sidecar stderr logs."""
    import shutil

    src = FIXTURES_DIR / "pdf_nosearch_01.pdf"
    input_file = tmp_path / "preproc_test.pdf"
    shutil.copy2(src, input_file)

    cmd = json.dumps({
        "cmd": "process_file",
        "id": "preproc-1",
        "input_path": str(input_file),
        "deskew": True,
        "rotate_pages": True,
        "force_ocr": True,
    })

    stdin_data = cmd + "\n"
    result = subprocess.run(
        [sys.executable, "-m", SIDECAR_MODULE],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=120.0,
        cwd=str(BACKEND_DIR),
    )

    # Preprocessing options should be logged in stderr
    stderr = result.stderr
    assert "deskew=True" in stderr, f"Expected deskew=True in stderr: {stderr[:500]}"
    assert "rotate=True" in stderr or "rotate_pages=True" in stderr, \
        f"Expected rotate=True in stderr: {stderr[:500]}"
    assert "force_ocr=True" in stderr, f"Expected force_ocr=True in stderr: {stderr[:500]}"


def test_process_file_pdf_default_skip_text(tmp_path):
    """PDF inputs default to skip_text=True when no explicit mode is set."""
    import shutil

    src = FIXTURES_DIR / "pdf_nosearch_01.pdf"
    input_file = tmp_path / "default_skip.pdf"
    shutil.copy2(src, input_file)

    cmd = json.dumps({
        "cmd": "process_file",
        "id": "skip-default-1",
        "input_path": str(input_file),
        # No skip_text or force_ocr specified — should default to skip_text=True
    })

    stdin_data = cmd + "\n"
    result = subprocess.run(
        [sys.executable, "-m", SIDECAR_MODULE],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=120.0,
        cwd=str(BACKEND_DIR),
    )

    # stderr should show skip_text=True as the default for PDFs
    assert "skip_text=True" in result.stderr, \
        f"Expected skip_text=True in stderr for PDF default: {result.stderr[:500]}"
