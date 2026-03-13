---
id: T01
parent: S04
milestone: M001
provides:
  - Authoritative 49-language registry (backend/parsec/languages.py)
  - get_languages sidecar command for frontend language picker
  - Language threading through sidecar → OcrOptions → pipeline
  - Language validation with descriptive error on unsupported codes
key_files:
  - backend/parsec/languages.py
  - backend/parsec/pipeline.py
  - backend/parsec/sidecar.py
  - backend/tests/test_languages.py
key_decisions:
  - Short codes match PaddleOCR codes (en, ch, korean, japan, etc.) since that's what flows through the system — no translation layer
  - Unknown language codes raise ValueError rather than falling back silently — explicit failure over silent wrong-language OCR
patterns_established:
  - Language dataclass with display_name, short_code, tesseract_code, script_group
  - Lookup indexes built once at import time (_BY_SHORT_CODE, _SHORT_TO_TESSERACT)
  - Sidecar validates language before queuing — errors returned immediately, not after pipeline runs
observability_surfaces:
  - Sidecar logs "process_file id=X language=Y path=Z" at INFO on every process_file command
  - Invalid language code → immediate error stage with "Unsupported language: XX" message
  - get_languages command returns full registry for runtime inspection
duration: 15min
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T01: Build language registry and thread language through sidecar protocol

**Created 49-language registry, threaded language through sidecar→pipeline, added get_languages command.**

## What Happened

Built `backend/parsec/languages.py` with all 49 languages from the ocrmypdf_paddleocr plugin's lang_map.py. Each entry is a `Language` dataclass with display_name, short_code, tesseract_code, and script_group. English is first (system default). Lookup helpers `get_language()`, `get_tesseract_code()`, and `all_languages()` provide the API surface.

Replaced the inline 12-entry `_LANG_TO_TESSERACT` dict in pipeline.py with an import from languages.py. The `_to_tesseract_lang()` function now delegates to `get_tesseract_code()`.

In sidecar.py, `_handle_process_file()` now reads `language` from the command JSON (defaulting to "en"), validates it against the registry before queuing, and constructs `OcrOptions(language=language)` for the pipeline. Added `get_languages` command handler that returns the full registry as JSON.

## Verification

- `cd backend && python -m pytest tests/test_languages.py -v` — 15/15 passed (registry completeness, plugin coverage, lookups, sidecar commands)
- `cd backend && python -m pytest tests/ -v` — 56/56 passed (zero regressions)
- `echo '{"cmd":"get_languages"}' | .venv/bin/python -m parsec.sidecar` — returns 49 languages, English first
- `echo '{"cmd":"process_file","id":"test-1","input_path":"tests/fixtures/clean_01.png","language":"en"}' | .venv/bin/python -m parsec.sidecar` — stderr shows `language=en` in log output
- Slice-level checks: `test_languages.py` passes (✅), `test_sidecar_language.py` not yet created (T02 scope), Tauri dev launch (T02 scope)

## Diagnostics

- `grep "language=" <sidecar-stderr>` — shows language used per process_file
- `echo '{"cmd":"get_languages"}' | python -m parsec.sidecar` — runtime registry dump
- Invalid language → immediate error stage: `{"type":"progress","id":"...","stage":"error","error":"Unsupported language: 'klingon'. Use all_languages() to see valid codes."}`

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/parsec/languages.py` — new, authoritative 49-language registry with lookup helpers
- `backend/parsec/pipeline.py` — replaced inline _LANG_TO_TESSERACT with import from languages.py
- `backend/parsec/sidecar.py` — language threading in process_file, get_languages command, language validation
- `backend/tests/test_languages.py` — new, 15 tests covering registry, lookups, sidecar commands
