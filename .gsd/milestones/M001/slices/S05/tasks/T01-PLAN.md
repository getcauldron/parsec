---
estimated_steps: 8
estimated_files: 8
---

# T01: Extend backend + Rust with PDF support and preprocessing flags

**Slice:** S05 — PDF Input + Preprocessing
**Milestone:** M001

## Description

Thread PDF acceptance and preprocessing options through the entire backend stack: OcrOptions → pipeline → sidecar protocol → Rust command. Generate PDF test fixtures and write tests proving the pipeline handles non-searchable PDFs, already-searchable PDFs, and encrypted PDFs correctly.

## Steps

1. **Extend `OcrOptions` in `models.py`** — add `deskew: bool = False`, `rotate_pages: bool = False`, `clean: bool = False`, `skip_text: bool = False`, `force_ocr: bool = False` fields.

2. **Extend `pipeline.process_file()` in `pipeline.py`** — pass preprocessing flags from `OcrOptions` to `ocrmypdf.ocr()` kwargs. Apply `skip_text` only for PDF inputs (check extension). Handle `ExitCode.already_done_ocr` (code 6) as success with a note. Handle `ExitCode.encrypted_pdf` (code 8) with clear error message. Pass `clean_final=options.clean` alongside `clean=options.clean`.

3. **Extend sidecar `ALLOWED_EXTENSIONS` and `_handle_process_file()`** — add `.pdf` to `ALLOWED_EXTENSIONS`. Read `deskew`, `rotate_pages`, `clean`, `skip_text`, `force_ocr` from command JSON. Construct `OcrOptions` with all fields. For PDF inputs where no explicit mode is set, default to `skip_text=True`.

4. **Extend Rust `process_files` command** — add optional `deskew`, `rotate_pages`, `clean`, `force_ocr` params (all `Option<bool>`). Forward them in the sidecar command JSON alongside `input_path` and `language`.

5. **Generate PDF fixtures** — extend `generate_fixtures.py` with a function that wraps an existing fixture image into a non-searchable PDF (image-only, no text layer). Generate `pdf_nosearch_01.pdf` from `clean_01.png` and `pdf_skewed_01.pdf` from a skewed version. Create matching `.gt.txt` ground truth files.

6. **Write `test_pipeline_pdf.py`** — tests: (a) non-searchable PDF produces searchable PDF, (b) preprocessing flags reach OCRmyPDF (deskew=True on skewed input), (c) already-searchable PDF with skip_text returns success, (d) encrypted PDF returns clear error.

7. **Extend sidecar tests** — add tests for PDF extension acceptance and preprocessing option passthrough in `test_sidecar.py`.

8. **Run full test suite and cargo check** — verify no regressions.

## Must-Haves

- [ ] `OcrOptions` has `deskew`, `rotate_pages`, `clean`, `skip_text`, `force_ocr` fields
- [ ] Pipeline passes preprocessing kwargs to `ocrmypdf.ocr()`
- [ ] `ExitCode.already_done_ocr` handled as success (not error) when skip_text is active
- [ ] `ExitCode.encrypted_pdf` produces clear error message
- [ ] `.pdf` in sidecar `ALLOWED_EXTENSIONS`
- [ ] Sidecar reads preprocessing options from command JSON
- [ ] Sidecar defaults to `skip_text=True` for PDF inputs when no explicit mode set
- [ ] Rust forwards preprocessing options in sidecar command JSON
- [ ] Non-searchable PDF test fixture generated
- [ ] `test_pipeline_pdf.py` passes

## Verification

- `cd backend && python -m pytest tests/test_pipeline_pdf.py -v` — all PDF-specific tests pass
- `cd backend && python -m pytest tests/test_sidecar.py -v` — all sidecar tests pass including new PDF/preprocessing tests
- `cd backend && python -m pytest tests/ -v` — full suite passes, no regressions
- `cd src-tauri && cargo check` — compiles clean with extended command signature

## Observability Impact

- Signals added/changed: pipeline logs preprocessing mode (`skip_text`, `force_ocr`, `deskew` etc.) per file; sidecar stderr logs preprocessing options received
- How a future agent inspects this: `echo '{"cmd":"process_file","id":"t","input_path":"test.pdf","deskew":true}' | python -m parsec.sidecar` — check stderr for option passthrough
- Failure state exposed: encrypted PDF → `stage: "error"` with `"Encrypted or password-protected PDF"` message; `already_done_ocr` → success with `"already_searchable": true` flag in complete event

## Inputs

- `backend/parsec/models.py` — current `OcrOptions(language, dpi)`
- `backend/parsec/pipeline.py` — current `process_file()` with `ocrmypdf.ocr()` call
- `backend/parsec/sidecar.py` — current `_handle_process_file()` with extension check and option reading
- `src-tauri/src/lib.rs` — current `process_files(paths, language, channel)` signature
- `backend/tests/fixtures/clean_01.png` — source image for PDF fixture generation
- S05-RESEARCH.md — OCRmyPDF kwargs, exit codes, mutual exclusivity constraints

## Expected Output

- `backend/parsec/models.py` — `OcrOptions` with 5 new boolean fields
- `backend/parsec/pipeline.py` — extended `ocrmypdf.ocr()` call with preprocessing kwargs, exit code handling
- `backend/parsec/sidecar.py` — `.pdf` in allowed extensions, preprocessing option reads, PDF-default skip_text
- `src-tauri/src/lib.rs` — extended `process_files` with preprocessing params forwarded to sidecar
- `backend/tests/fixtures/generate_fixtures.py` — PDF fixture generation functions
- `backend/tests/fixtures/pdf_nosearch_01.pdf` — non-searchable PDF fixture
- `backend/tests/fixtures/pdf_skewed_01.pdf` — skewed non-searchable PDF fixture
- `backend/tests/test_pipeline_pdf.py` — PDF pipeline tests
