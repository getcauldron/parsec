---
id: T01
parent: S05
milestone: M001
provides:
  - OcrOptions with 5 preprocessing boolean fields (deskew, rotate_pages, clean, skip_text, force_ocr)
  - Pipeline preprocessing kwargs passthrough to ocrmypdf.ocr()
  - ExitCode.already_done_ocr and ExitCode.encrypted_pdf handling
  - PDF extension acceptance in sidecar
  - Sidecar preprocessing option reads with PDF default skip_text=True
  - Rust process_files extended with optional preprocessing params
  - Non-searchable PDF and skewed PDF test fixtures
  - ProcessResult.already_searchable field
key_files:
  - backend/parsec/models.py
  - backend/parsec/pipeline.py
  - backend/parsec/sidecar.py
  - src-tauri/src/lib.rs
  - backend/tests/test_pipeline_pdf.py
  - backend/tests/test_sidecar.py
  - backend/tests/fixtures/generate_fixtures.py
  - backend/tests/fixtures/pdf_nosearch_01.pdf
  - backend/tests/fixtures/pdf_skewed_01.pdf
key_decisions:
  - force_ocr takes precedence over skip_text when both are set (mutual exclusivity)
  - clean=True also sets clean_final=True for consistent unpaper behavior
  - skip_text is only applied for PDF inputs, silently ignored for images
  - Sidecar defaults to skip_text=True for PDF inputs when neither skip_text nor force_ocr is explicitly set
  - ProcessResult gets already_searchable boolean rather than encoding it in error/success differently
patterns_established:
  - Preprocessing kwargs are built as a dict and spread into ocrmypdf.ocr(**ocr_kwargs) rather than always passing all flags
  - Sidecar logs all preprocessing option values in a single structured log line for debuggability
  - Rust forwards preprocessing options conditionally (only when Some) to keep sidecar JSON clean
observability_surfaces:
  - Pipeline logs preprocessing mode, deskew, rotate, clean per file (INFO level)
  - Sidecar stderr logs all preprocessing options received per process_file command
  - already_searchable flag in complete event when PDF had existing text layer
  - Encrypted PDF produces stage:"error" with "Encrypted or password-protected PDF" message
duration: 25m
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T01: Extend backend + Rust with PDF support and preprocessing flags

**Threaded PDF acceptance and 5 preprocessing flags through OcrOptions → pipeline → sidecar → Rust, with exit code handling and 12 new tests.**

## What Happened

Extended `OcrOptions` with `deskew`, `rotate_pages`, `clean`, `skip_text`, `force_ocr` booleans. Pipeline builds an `ocr_kwargs` dict from these and spreads it into `ocrmypdf.ocr()`. Added `already_done_ocr` handling (success + `already_searchable=True`) and `encrypted_pdf` handling (clear error message). Added `ProcessResult.already_searchable` field.

Sidecar now includes `.pdf` in `ALLOWED_EXTENSIONS`, reads all 5 preprocessing options from command JSON, and defaults to `skip_text=True` for PDF inputs when no explicit mode is set. The sidecar emits `already_searchable: true` in the complete event when relevant.

Rust `process_files` command takes 4 new optional params (`deskew`, `rotate_pages`, `clean`, `force_ocr`) and conditionally forwards them in the sidecar command JSON.

Generated two PDF test fixtures: `pdf_nosearch_01.pdf` (image-only PDF from clean_01.png) and `pdf_skewed_01.pdf` (3° rotated version). Extended `generate_fixtures.py` with `_generate_pdf_nosearch()` and `_generate_pdf_skewed()` functions.

Wrote 8 tests in `test_pipeline_pdf.py` covering: non-searchable PDF → searchable, deskew on skewed input, preprocessing flags reaching ocrmypdf, clean_final passthrough, skip_text only for PDFs, already-searchable success, encrypted error, force_ocr/skip_text mutual exclusion. Added 4 tests to `test_sidecar.py` covering: PDF extension acceptance, PDF output naming, preprocessing option logging, and PDF default skip_text.

## Verification

- `cd backend && python -m pytest tests/test_pipeline_pdf.py -v` — 8/8 passed ✅
- `cd backend && python -m pytest tests/test_sidecar.py -v` — 18/18 passed (14 existing + 4 new) ✅
- `cd backend && python -m pytest tests/ -v` — 73/73 passed, zero regressions ✅
- `cd src-tauri && cargo check` — compiles clean ✅

### Slice-level verification status
- ✅ `test_pipeline_pdf.py` passes
- ✅ `test_sidecar.py` passes
- ✅ all backend tests pass
- ✅ `cargo check` clean
- ⏳ `pnpm build` — requires T02 (frontend changes)
- ⏳ `cargo tauri dev` + UI verification — requires T02

## Diagnostics

- `echo '{"cmd":"process_file","id":"t","input_path":"test.pdf","deskew":true}' | python -m parsec.sidecar` — check stderr for `deskew=True` in log line
- Pipeline logs `Preprocessing mode=skip_text deskew=False rotate=False clean=False` at INFO level per file
- Encrypted PDF → `stage: "error"` with `"Encrypted or password-protected PDF"` message
- Already-searchable PDF → `stage: "complete"` with `"already_searchable": true` in event

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/parsec/models.py` — added 5 preprocessing booleans to OcrOptions, added already_searchable to ProcessResult
- `backend/parsec/pipeline.py` — preprocessing kwargs passthrough, already_done_ocr and encrypted_pdf exit code handling
- `backend/parsec/sidecar.py` — .pdf in ALLOWED_EXTENSIONS, preprocessing option reads, PDF default skip_text, already_searchable in complete event
- `src-tauri/src/lib.rs` — process_files extended with deskew, rotate_pages, clean, force_ocr params
- `backend/tests/test_pipeline_pdf.py` — 8 new PDF pipeline tests (created)
- `backend/tests/test_sidecar.py` — 4 new sidecar tests for PDF and preprocessing
- `backend/tests/fixtures/generate_fixtures.py` — PDF fixture generation functions
- `backend/tests/fixtures/pdf_nosearch_01.pdf` — non-searchable PDF fixture (created)
- `backend/tests/fixtures/pdf_skewed_01.pdf` — skewed non-searchable PDF fixture (created)
- `backend/tests/fixtures/pdf_nosearch_01.gt.txt` — ground truth for PDF fixture (created)
- `backend/tests/fixtures/pdf_skewed_01.gt.txt` — ground truth for skewed PDF fixture (created)
