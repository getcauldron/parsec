---
id: T01
parent: S06
milestone: M001
provides:
  - Cross-cutting integration test suite covering batch sidecar, error resilience, TIFF, PDF quality, preprocessing quality
  - TIFF fixture with DPI metadata and ground truth
  - JPEG fixture for multi-format batch testing
key_files:
  - backend/tests/test_integration.py
  - backend/tests/fixtures/generate_fixtures.py
  - backend/tests/fixtures/tiff_01.tiff
  - backend/tests/fixtures/tiff_01.gt.txt
  - backend/tests/fixtures/clean_01.jpg
key_decisions:
  - TIFF quality test goes through pipeline (process_file → extract PDF text) not engine.recognize() directly, since PaddleOCR returns 0 regions for TIFF input while OCRmyPDF handles the conversion correctly
  - CER thresholds set at measured values with margin — pdf_nosearch CER<0.10 (actual 0.00), pdf_skewed CER<0.20 (actual 0.016), tiff CER<0.05 (actual 0.025)
  - Deskew comparison uses epsilon=0.02 for non-determinism rather than asserting strict improvement, since 3° synthetic skew produces near-identical CER with and without deskew
patterns_established:
  - _filter_progress() helper for extracting sidecar progress events by file ID from interleaved responses
  - _measure_cer_from_pdf() helper for measuring CER from pipeline output PDFs via pdfminer text extraction
observability_surfaces:
  - PDF quality benchmarks print CER/WER scores in test output for regression tracking
  - Preprocessing comparison prints both CER values and delta for diagnostic context
  - TIFF pipeline quality test prints CER
duration: 1 session
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T01: Backend integration test suite

**Created 12 integration tests covering batch sidecar processing, error resilience, TIFF pipeline, PDF quality benchmarks, and preprocessing quality comparison.**

## What Happened

Added TIFF fixture generation to `generate_fixtures.py` — creates `tiff_01.tiff` from clean_01's content with LZW compression and explicit 300 DPI metadata, plus `tiff_01.gt.txt` ground truth. Also created `clean_01.jpg` for JPEG coverage in batch tests.

Created `test_integration.py` with 5 test classes:
- **TestMultiFileBatch** (2 tests): Sends PNG, JPEG, PDF, and skewed PDF through a single sidecar session with 180s timeout, filtering interleaved responses by ID. All 4 file types reach `complete` with valid output PDFs and positive durations.
- **TestErrorResilience** (2 tests): Batch with unsupported `.xyz` file alongside valid PNG — bad file gets `error` stage, valid file still completes. Same for nonexistent file path.
- **TestPdfQualityBenchmarks** (4 tests): CER/WER on `pdf_nosearch_01.pdf` (CER<0.10, WER<0.15) and `pdf_skewed_01.pdf` (CER<0.20, WER<0.30) using `measure_quality()` from test_quality.py.
- **TestPreprocessingQuality** (1 test): Processes skewed PDF through pipeline twice (with/without deskew), extracts text from output PDFs, compares CER. Asserts deskew doesn't degrade quality (epsilon=0.02).
- **TestTiffPipeline** (3 tests): Verifies TIFF accepted by pipeline and sidecar, produces searchable PDF with text layer, and CER<0.05 on pipeline output.

Calibrated thresholds against actual measurements before setting them.

## Verification

- `cd backend && .venv/bin/python -m pytest tests/test_integration.py -v` — 12 tests passed
- `cd backend && .venv/bin/python -m pytest tests/ -v` — 85 tests passed (73 existing + 12 new), zero regressions
- `cd src-tauri && cargo check` — compiles clean
- `pnpm build` — frontend builds clean
- `cargo tauri dev` manual verification — deferred to T02

## Diagnostics

- Run `pytest tests/test_integration.py -v -s` to see CER/WER scores and preprocessing deltas in stdout
- PDF quality thresholds are intentionally generous; can be tightened as the engine improves

## Deviations

- TIFF quality test uses pipeline output (process_file → extract PDF text → CER) instead of engine.recognize() directly. PaddleOCR returns 0 regions for TIFF input; OCRmyPDF handles TIFF→image conversion internally. This is the correct approach since the pipeline is the product surface.
- Created clean_01.jpg fixture manually (not in generate_fixtures.py) for batch test JPEG coverage. Straightforward Pillow PNG→JPEG conversion.

## Known Issues

None.

## Files Created/Modified

- `backend/tests/test_integration.py` — 12 new integration tests across 5 test classes
- `backend/tests/fixtures/generate_fixtures.py` — added `_generate_tiff()` and TIFF fixture generation in `generate_all()`
- `backend/tests/fixtures/tiff_01.tiff` — TIFF fixture (300 DPI, LZW compression, from clean_01 content)
- `backend/tests/fixtures/tiff_01.gt.txt` — TIFF ground truth
- `backend/tests/fixtures/clean_01.jpg` — JPEG fixture for batch tests
