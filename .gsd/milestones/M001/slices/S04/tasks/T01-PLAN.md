---
estimated_steps: 5
estimated_files: 4
---

# T01: Build language registry and thread language through sidecar protocol

**Slice:** S04 — Multi-Language & Settings
**Milestone:** M001

## Description

The backend currently has a 12-entry `_LANG_TO_TESSERACT` map in `pipeline.py` and the sidecar ignores the `language` field in `process_file` commands. This task creates `backend/parsec/languages.py` as the authoritative language registry covering all 49 languages supported by the `ocrmypdf_paddleocr` plugin, threads the language field through the sidecar to the pipeline, and adds a `get_languages` command so the frontend can dynamically populate its language picker.

## Steps

1. **Create `backend/parsec/languages.py`** — Define a `Language` dataclass (display_name, short_code, tesseract_code, script_group). Build the `LANGUAGES` list with all 49 entries derived from `ocrmypdf_paddleocr/lang_map.py`. Add lookup helpers: `get_language(short_code)`, `get_tesseract_code(short_code)`, `all_languages()` (returns list of dicts suitable for JSON serialization). The short codes should match PaddleOCR's codes (en, ch, korean, japan, etc.) since that's what flows through the system. English must be first/default.

2. **Update `backend/parsec/pipeline.py`** — Replace the inline `_LANG_TO_TESSERACT` dict and `_to_tesseract_lang()` function with an import from `languages.py`. The `process_file()` function already receives `OcrOptions` with a `language` field — ensure `_to_tesseract_lang()` now delegates to `languages.get_tesseract_code()`.

3. **Thread language in `backend/parsec/sidecar.py`** — In `_handle_process_file()`, read `cmd_obj.get("language", "en")` and construct `OcrOptions(language=language)` to pass to `process_file()`. Add a `get_languages` command handler in `_handle_command()` that returns `{"status": "ok", "languages": [...], "id": req_id}` using `all_languages()`. Log the selected language at INFO level.

4. **Write `backend/tests/test_languages.py`** — Test registry completeness (49 languages), all Tesseract codes are in the plugin's `SUPPORTED_LANGUAGES` set, `get_tesseract_code("en")` returns `"eng"`, unknown codes raise or return a sensible fallback. Test `get_languages` sidecar command via subprocess stdin/stdout (send JSON, parse response, assert 49 entries with expected shape).

5. **Validate manually** — Run `echo '{"cmd":"get_languages"}' | python -m parsec.sidecar` and verify 49 languages in response. Run `echo '{"cmd":"process_file","id":"test-1","input_path":"tests/fixtures/clean_paragraph.png","language":"en"}' | python -m parsec.sidecar` and verify language appears in log output.

## Must-Haves

- [ ] `languages.py` has all 49 languages from the `ocrmypdf_paddleocr` plugin's lang_map
- [ ] Every Tesseract code in the registry is in the plugin's `SUPPORTED_LANGUAGES` set
- [ ] `_handle_process_file()` reads language from command JSON and passes to OcrOptions
- [ ] `get_languages` sidecar command returns the full list with display names and short codes
- [ ] Existing pipeline tests still pass (no regression from replacing inline map)

## Verification

- `cd backend && python -m pytest tests/test_languages.py -v` — all pass
- `cd backend && python -m pytest tests/ -v` — no regressions
- `echo '{"cmd":"get_languages"}' | cd backend && .venv/bin/python -m parsec.sidecar` — returns 49 languages

## Observability Impact

- Signals added/changed: sidecar logs `language=XX` on each process_file command at INFO level
- How a future agent inspects this: grep sidecar stderr for "language=" to see what language was used
- Failure state exposed: invalid language code → process_file returns error stage with "unsupported language: XX"

## Inputs

- `backend/.venv/lib/python3.13/site-packages/ocrmypdf_paddleocr/lang_map.py` — authoritative Tesseract→PaddleOCR mapping (49 entries)
- `backend/parsec/pipeline.py` — existing `_LANG_TO_TESSERACT` (12 entries) and `process_file()` function
- `backend/parsec/sidecar.py` — existing command dispatch, `_handle_process_file()` ignores language
- `backend/parsec/models.py` — `OcrOptions(language="en")` already carries language field

## Expected Output

- `backend/parsec/languages.py` — authoritative language registry with 49 entries, lookup helpers
- `backend/parsec/pipeline.py` — `_LANG_TO_TESSERACT` replaced with import from languages.py
- `backend/parsec/sidecar.py` — language threaded through process_file, get_languages command added
- `backend/tests/test_languages.py` — registry completeness tests, sidecar command tests
