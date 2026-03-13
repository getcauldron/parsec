"""Tests that the sidecar threads language through to the pipeline.

Validates:
- process_file with explicit language includes it in progress events
- process_file with no language defaults to "en"
- process_file with invalid language returns an error stage
- get_languages returns all 49 languages with correct structure
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
SIDECAR_MODULE = "parsec.sidecar"
FIXTURE_DIR = BACKEND_DIR / "tests" / "fixtures"


def _run_sidecar(commands: list[dict], timeout: float = 30.0) -> tuple[list[dict], str]:
    """Send commands to the sidecar and return (stdout_jsons, stderr_text).

    Each command is sent as a JSON line to stdin.
    Returns all parsed JSON lines from stdout and the full stderr text.
    """
    input_text = "\n".join(json.dumps(c) for c in commands) + "\n"

    result = subprocess.run(
        [sys.executable, "-m", SIDECAR_MODULE],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(BACKEND_DIR),
    )

    stdout_lines = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line:
            stdout_lines.append(json.loads(line))

    return stdout_lines, result.stderr


class TestSidecarLanguageThreading:
    """Test that language flows through the sidecar to the pipeline."""

    def test_process_file_with_explicit_language_logs_it(self):
        """Sidecar stderr should show the language used per process_file."""
        # Use a fixture image that exists
        fixtures = list(FIXTURE_DIR.glob("*.png"))
        if not fixtures:
            pytest.skip("No PNG fixtures available")

        input_path = str(fixtures[0])
        cmd = {
            "cmd": "process_file",
            "id": "lang-test-1",
            "input_path": input_path,
            "language": "french",
        }

        _responses, stderr = _run_sidecar([cmd])

        # Verify language appears in sidecar log
        assert "language=french" in stderr, (
            f"Expected 'language=french' in sidecar stderr, got:\n{stderr}"
        )

    def test_process_file_default_language_is_english(self):
        """Without explicit language, sidecar should default to 'en'."""
        fixtures = list(FIXTURE_DIR.glob("*.png"))
        if not fixtures:
            pytest.skip("No PNG fixtures available")

        input_path = str(fixtures[0])
        cmd = {
            "cmd": "process_file",
            "id": "lang-test-2",
            "input_path": input_path,
            # No language field — should default to "en"
        }

        _responses, stderr = _run_sidecar([cmd])

        assert "language=en" in stderr, (
            f"Expected 'language=en' in sidecar stderr, got:\n{stderr}"
        )

    def test_invalid_language_returns_error_stage(self):
        """An invalid language code should produce an error stage immediately."""
        cmd = {
            "cmd": "process_file",
            "id": "lang-test-bad",
            "input_path": "/tmp/doesnt_matter.png",
            "language": "klingon",
        }

        responses, _stderr = _run_sidecar([cmd])

        # Find the error response for our request
        error_events = [
            r for r in responses
            if r.get("id") == "lang-test-bad" and r.get("stage") == "error"
        ]
        assert len(error_events) >= 1, (
            f"Expected error stage for invalid language, got: {responses}"
        )
        assert "klingon" in error_events[0].get("error", "").lower()

    def test_get_languages_returns_49_entries(self):
        """get_languages should return all 49 registered languages."""
        responses, _stderr = _run_sidecar([{"cmd": "get_languages"}])

        assert len(responses) == 1
        resp = responses[0]
        assert resp["status"] == "ok"
        assert len(resp["languages"]) == 49

        # Verify structure of first entry
        first = resp["languages"][0]
        assert first["display_name"] == "English"
        assert first["short_code"] == "en"
        assert "tesseract_code" in first
        assert "script_group" in first

    def test_get_languages_all_have_required_fields(self):
        """Every language entry must have display_name, short_code, tesseract_code, script_group."""
        responses, _stderr = _run_sidecar([{"cmd": "get_languages"}])
        langs = responses[0]["languages"]

        required = {"display_name", "short_code", "tesseract_code", "script_group"}
        for lang in langs:
            missing = required - set(lang.keys())
            assert not missing, (
                f"Language {lang.get('short_code', '?')} missing fields: {missing}"
            )
