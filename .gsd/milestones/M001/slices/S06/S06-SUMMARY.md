---
id: S06
parent: M001
milestone: M001
provides:
  - 12 cross-cutting integration tests covering batch sidecar, error resilience, TIFF, PDF quality, preprocessing quality
  - TIFF fixture with DPI metadata and ground truth
  - Final Integrated Acceptance verification confirming M001 completion criteria
  - Regenerated S05-SUMMARY.md from task summaries
requires:
  - slice: S01
    provides: Pipeline, engine, sidecar, quality measurement infrastructure
  - slice: S02
    provides: Tauri shell, sidecar manager
  - slice: S03
    provides: Drop zone UI, file processing commands, progress streaming
  - slice: S04
    provides: Language picker, settings panel, 49-language registry
  - slice: S05
    provides: PDF acceptance, preprocessing flags, encrypted/already-searchable handling
affects: []
key_files:
  - backend/tests/test_integration.py
  - backend/tests/fixtures/tiff_01.tiff
  - backend/tests/fixtures/generate_fixtures.py
key_decisions:
  - TIFF quality test goes through full pipeline (process_file → extract PDF text) not engine.recognize() directly, since PaddleOCR returns 0 regions for TIFF input while OCRmyPDF handles the format conversion
  - CER thresholds set at measured values with margin — pdf_nosearch CER<0.10 (actual 0.00), pdf_skewed CER<0.20 (actual 0.016), tiff CER<0.05 (actual 0.025)
  - Final Integrated Acceptance performed via sidecar subprocess (equivalent to Tauri app pipeline) since browser-based drag-drop requires native Tauri APIs not available in webview dev mode
patterns_established:
  - _filter_progress() helper for extracting sidecar progress events by file ID from interleaved responses
  - _measure_cer_from_pdf() helper for measuring CER from pipeline output PDFs via pdfminer text extraction
observability_surfaces:
  - pytest -v -s on test_integration.py shows CER/WER scores and preprocessing deltas in stdout
  - PDF quality thresholds are intentionally generous — can be tightened as the engine improves
drill_down_paths:
  - .gsd/milestones/M001/slices/S06/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S06/tasks/T02-SUMMARY.md
duration: 75m
verification_result: passed
completed_at: 2026-03-12
---

# S06: End-to-End Integration Testing

**Proved the full Parsec system works as an integrated whole — 85 tests pass across 8 modules, mixed-format batch processing succeeds, error resilience holds, quality thresholds met, and Final Integrated Acceptance criteria satisfied.**

## What Happened

T01 created 12 cross-cutting integration tests in `test_integration.py` covering: multi-file batch sidecar processing (PNG + JPEG + PDF + skewed PDF all reach `complete` stage), error resilience (corrupt files get `error` while valid files complete), TIFF pipeline support (TIFF → searchable PDF with CER < 0.05), PDF quality benchmarks (CER/WER for non-searchable and skewed PDF fixtures), and preprocessing quality comparison (deskew doesn't degrade skewed input). A TIFF fixture with 300 DPI metadata and ground truth was generated.

T02 ran the full test suite (85 tests, zero failures), verified `cargo check` and `pnpm build` clean, and performed Final Integrated Acceptance: 5 mixed files (PNG, JPEG, TIFF, non-searchable PDF, skewed PDF) all processed to searchable PDFs with extractable text, Korean language processing downloaded and used the Korean OCR model, and a corrupt file produced an error while the subsequent valid file still completed. S05-SUMMARY.md was regenerated from its task summaries.

## Verification

- `pytest tests/test_integration.py -v` — 12/12 passed ✅
- `pytest tests/ -v` — 85/85 passed, zero failures ✅
- `cargo check` — compiles clean ✅
- `pnpm build` — builds clean ✅
- Final Integrated Acceptance (via sidecar subprocess):
  - 5 mixed files → all 5 reached `complete` stage, 4 unique `_ocr.pdf` files produced ✅
  - All output PDFs contain extractable text (verified via pdfminer) ✅
  - Korean language → Korean OCR model downloaded and used ✅
  - Corrupt file → `error` stage, subsequent valid file → `complete` stage ✅
- UI verification (via browser at localhost:1420):
  - Drop zone shows `.png .jpg .jpeg .tiff .tif .pdf` ✅
  - Settings panel shows language picker + 3 preprocessing toggles ✅

## Deviations

- Final Integrated Acceptance performed via sidecar subprocess rather than native Tauri drag-drop, since the browser dev tools cannot invoke Tauri-specific drag-drop APIs. The sidecar subprocess exercises the identical pipeline code path that the Tauri app uses.
- PNG and JPEG with the same base name (`clean_01`) produce the same `_ocr.pdf` output — this is correct behavior (4 unique files from 5 inputs since two share a basename).

## Known Limitations

- Screen Recording permission not available, so no native Tauri window screenshots were captured. UI verified via browser webview at localhost:1420.
- Test suite takes ~7 minutes to run fully due to OCR processing overhead (PaddleOCR model loading + inference).

## Follow-ups

- None — M001 is complete.

## Files Created/Modified

- `backend/tests/test_integration.py` — 12 cross-cutting integration tests (created in T01)
- `backend/tests/fixtures/tiff_01.tiff` — TIFF fixture with 300 DPI and ground truth (created in T01)
- `backend/tests/fixtures/tiff_01.gt.txt` — TIFF ground truth (created in T01)
- `backend/tests/fixtures/generate_fixtures.py` — TIFF fixture generation (modified in T01)
- `.gsd/milestones/M001/slices/S05/S05-SUMMARY.md` — regenerated from task summaries (T02)
- `.gsd/milestones/M001/slices/S06/S06-SUMMARY.md` — this file (T02)
- `.gsd/milestones/M001/M001-SUMMARY.md` — milestone completion summary (T02)
- `.gsd/milestones/M001/M001-ROADMAP.md` — S06 checkbox marked complete (T02)
- `.gsd/STATE.md` — updated to reflect M001 completion (T02)

## Forward Intelligence

### What the next slice should know
- The full test suite is ~7 minutes. For iteration speed, run specific test files rather than the full suite.
- CER/WER thresholds are intentionally generous. As the engine improves (PaddleOCR updates, model improvements), thresholds can be tightened.

### What's fragile
- Integration tests depend on PaddleOCR model availability — if models fail to download, tests will fail with opaque errors.
- Sidecar tests use subprocess with 180s timeout — on slower machines, tests may time out.

### Authoritative diagnostics
- `pytest tests/test_integration.py -v -s` — shows CER/WER scores inline with test output
- `pytest tests/ -v` — full suite status in one command

### What assumptions changed
- Originally expected TIFF quality testing to use engine.recognize() directly — PaddleOCR returns 0 regions for TIFF input, so quality testing goes through the full pipeline (TIFF → OCRmyPDF → searchable PDF → text extraction).
