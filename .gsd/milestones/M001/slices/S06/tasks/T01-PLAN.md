---
estimated_steps: 6
estimated_files: 2
---

# T01: Backend integration test suite

**Slice:** S06 — End-to-End Integration Testing
**Milestone:** M001

## Description

Create `backend/tests/test_integration.py` with cross-cutting integration tests that exercise the full pipeline through the sidecar subprocess. The existing 73 tests cover individual modules (engine, pipeline, sidecar protocol, languages, quality) but no test sends multiple mixed file types through a single sidecar session, measures CER/WER on PDF fixtures, tests TIFF support, or verifies error resilience in batch scenarios. This task closes those gaps.

## Steps

1. Add TIFF fixture generation to `generate_fixtures.py` — create `tiff_01.tiff` from clean_01's content with explicit DPI metadata, plus `tiff_01.gt.txt` ground truth. Run the generator to produce the fixture files.
2. Create `test_integration.py` with a multi-file batch sidecar test: send `process_file` commands for a PNG, JPEG, non-searchable PDF, and skewed PDF through a single `_run_sidecar()` call with 180s timeout. Filter responses by `id` and assert each file reaches `complete` stage with a valid `output_path`.
3. Add error resilience test: send a batch that includes a file with an unsupported extension (e.g., `.xyz`) or a path to a non-existent file alongside valid files. Assert the bad file gets `error` stage while the valid files still reach `complete`.
4. Add PDF fixture CER/WER benchmarks: use `measure_quality()` from `test_quality.py` to measure CER/WER on `pdf_nosearch_01.pdf` and `pdf_skewed_01.pdf`. Use the session-scoped engine fixture. Set initial thresholds generously (CER < 0.10 for pdf_nosearch, CER < 0.20 for pdf_skewed) and tighten after first measurement.
5. Add preprocessing quality test: process the skewed PDF fixture through the sidecar twice — once with default options (no deskew) and once with `deskew: true`. Extract text from both output PDFs and compare CER. Assert CER with deskew ≤ CER without deskew (allow small epsilon for non-determinism).
6. Add TIFF pipeline test: verify `process_file()` accepts a TIFF input and produces a searchable PDF. Add a sidecar-level test confirming TIFF extension is accepted.

## Must-Haves

- [ ] Multi-file batch sidecar test with 4+ file types, all reaching `complete`
- [ ] Error resilience test — bad file in batch gets `error`, valid files still `complete`
- [ ] TIFF fixture created with DPI metadata and ground truth
- [ ] TIFF pipeline test passes
- [ ] PDF CER/WER benchmarks with explicit thresholds
- [ ] Preprocessing quality comparison (deskew vs no-deskew on skewed input)
- [ ] All existing 73 tests still pass

## Verification

- `cd backend && .venv/bin/python -m pytest tests/test_integration.py -v` — all new tests pass
- `cd backend && .venv/bin/python -m pytest tests/ -v` — full suite 80+ tests pass, zero regressions

## Observability Impact

- PDF quality benchmarks print CER/WER scores in test output (same pattern as `test_quality.py`) for regression tracking visibility
- Preprocessing comparison prints both CER values for diagnostic context

## Inputs

- `backend/tests/test_sidecar.py` — `_run_sidecar()` helper pattern for subprocess testing
- `backend/tests/test_quality.py` — `measure_quality()` function and threshold assertion pattern
- `backend/tests/conftest.py` — session-scoped engine fixture, `FIXTURE_DIR`, `load_ground_truth`
- `backend/tests/fixtures/generate_fixtures.py` — fixture generation patterns
- `backend/tests/fixtures/pdf_nosearch_01.pdf`, `pdf_skewed_01.pdf` — PDF fixtures from S05
- S06-RESEARCH.md — timeout guidance (180s for batch), threshold guidance, interleaved response filtering

## Expected Output

- `backend/tests/test_integration.py` — 8-12 new integration tests covering batch, error resilience, TIFF, PDF quality, preprocessing quality, language threading
- `backend/tests/fixtures/tiff_01.tiff` — TIFF test fixture
- `backend/tests/fixtures/tiff_01.gt.txt` — TIFF ground truth
- `backend/tests/fixtures/generate_fixtures.py` — extended with TIFF generation
