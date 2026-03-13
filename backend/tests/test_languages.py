"""Tests for the language registry and get_languages sidecar command.

Validates registry completeness against the ocrmypdf_paddleocr plugin,
lookup helpers, error handling, and the sidecar get_languages command.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from parsec.languages import (
    LANGUAGES,
    Language,
    all_languages,
    get_language,
    get_tesseract_code,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
SIDECAR_MODULE = "parsec.sidecar"


# ─── Registry completeness ────────────────────────────────────────────────


def test_registry_has_49_languages():
    """Registry must contain exactly 49 languages matching the plugin."""
    assert len(LANGUAGES) == 49


def test_all_tesseract_codes_in_plugin():
    """Every Tesseract code in the registry must be in the plugin's SUPPORTED_LANGUAGES set."""
    from ocrmypdf_paddleocr.lang_map import SUPPORTED_LANGUAGES

    for lang in LANGUAGES:
        assert lang.tesseract_code in SUPPORTED_LANGUAGES, (
            f"{lang.short_code} maps to {lang.tesseract_code!r} "
            f"which is not in the plugin's SUPPORTED_LANGUAGES"
        )


def test_plugin_codes_all_covered():
    """Every code in the plugin's SUPPORTED_LANGUAGES must have a registry entry."""
    from ocrmypdf_paddleocr.lang_map import SUPPORTED_LANGUAGES

    registry_tess_codes = {lang.tesseract_code for lang in LANGUAGES}
    for tess_code in SUPPORTED_LANGUAGES:
        assert tess_code in registry_tess_codes, (
            f"Plugin supports {tess_code!r} but no registry entry maps to it"
        )


def test_short_codes_are_unique():
    """Short codes must be unique across the registry."""
    codes = [lang.short_code for lang in LANGUAGES]
    assert len(codes) == len(set(codes)), f"Duplicate short codes: {[c for c in codes if codes.count(c) > 1]}"


def test_english_is_first():
    """English must be the first entry (system default)."""
    assert LANGUAGES[0].short_code == "en"
    assert LANGUAGES[0].display_name == "English"


# ─── Lookup helpers ────────────────────────────────────────────────────────


def test_get_tesseract_code_english():
    """get_tesseract_code('en') returns 'eng'."""
    assert get_tesseract_code("en") == "eng"


def test_get_tesseract_code_korean():
    """get_tesseract_code('korean') returns 'kor'."""
    assert get_tesseract_code("korean") == "kor"


def test_get_tesseract_code_chinese_simplified():
    """get_tesseract_code('ch') returns 'chi_sim'."""
    assert get_tesseract_code("ch") == "chi_sim"


def test_get_tesseract_code_unknown_raises():
    """Unknown code raises ValueError with descriptive message."""
    with pytest.raises(ValueError, match="Unsupported language"):
        get_tesseract_code("klingon")


def test_get_language_returns_dataclass():
    """get_language returns a Language instance with correct fields."""
    lang = get_language("en")
    assert isinstance(lang, Language)
    assert lang.display_name == "English"
    assert lang.tesseract_code == "eng"
    assert lang.script_group == "Latin"


def test_get_language_unknown_raises():
    """Unknown code raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported language"):
        get_language("xx_invalid")


# ─── all_languages() serialization ────────────────────────────────────────


def test_all_languages_returns_list_of_dicts():
    """all_languages() returns a list of dicts with expected keys."""
    langs = all_languages()
    assert isinstance(langs, list)
    assert len(langs) == 49

    expected_keys = {"display_name", "short_code", "tesseract_code", "script_group"}
    for entry in langs:
        assert isinstance(entry, dict)
        assert set(entry.keys()) == expected_keys


def test_all_languages_is_json_serializable():
    """all_languages() output can be serialized to JSON without error."""
    langs = all_languages()
    serialized = json.dumps(langs)
    roundtripped = json.loads(serialized)
    assert roundtripped == langs


# ─── Sidecar get_languages command ────────────────────────────────────────


def _run_sidecar(input_lines: list[str], timeout: float = 10.0) -> list[dict]:
    """Send NDJSON lines to the sidecar process and collect responses."""
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


def test_sidecar_get_languages():
    """get_languages sidecar command returns 49 languages with expected shape."""
    responses = _run_sidecar(['{"cmd":"get_languages","id":"lang-1"}'])
    assert len(responses) == 1

    resp = responses[0]
    assert resp["status"] == "ok"
    assert resp["id"] == "lang-1"
    assert "languages" in resp

    langs = resp["languages"]
    assert len(langs) == 49

    # Verify shape of each entry
    for entry in langs:
        assert "display_name" in entry
        assert "short_code" in entry
        assert "tesseract_code" in entry
        assert "script_group" in entry

    # English is first
    assert langs[0]["short_code"] == "en"
    assert langs[0]["display_name"] == "English"


def test_sidecar_invalid_language():
    """process_file with an invalid language code returns error stage."""
    cmd = json.dumps({
        "cmd": "process_file",
        "id": "badlang-1",
        "input_path": "/tmp/fake.png",
        "language": "klingon",
    })
    responses = _run_sidecar([cmd])

    progress = [r for r in responses if r.get("type") == "progress"]
    assert len(progress) >= 1
    assert progress[0]["stage"] == "error"
    assert "Unsupported language" in progress[0]["error"]
