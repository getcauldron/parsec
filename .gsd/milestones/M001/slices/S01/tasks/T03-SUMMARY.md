---
id: T03
parent: S01
milestone: M001
provides:
  - Synthetic fixture generator producing test images with known ground truth across 3 categories
  - CER/WER quality measurement using jiwer 4.x with text normalization transforms
  - Parametrized pytest quality benchmarks with per-category threshold assertions
  - Shared conftest.py with session-scoped engine and ground truth loading helpers
key_files:
  - backend/tests/fixtures/generate_fixtures.py
  - backend/tests/test_quality.py
  - backend/tests/conftest.py
  - backend/tests/fixtures/*.png
  - backend/tests/fixtures/*.gt.txt
key_decisions:
  - "D018: Multi-column ground truth uses interleaved row order (left-1, right-1, left-2, right-2) matching PaddleOCR's reading order"
  - "D019: jiwer 4.x uses reference_transform (not truth_transform); cer() needs ReduceToListOfListOfChars, wer() needs ReduceToListOfListOfWords"
patterns_established:
  - "Fixture discovery by glob pattern prefix (clean_*.png, multicol_*.png, degraded_*.png) with matching .gt.txt files"
  - "QualityResult dataclass encapsulates CER/WER + both text strings for diagnostic output"
  - "Parametrized test class with FixtureCase dataclass carrying thresholds per category"
observability_surfaces:
  - "CER/WER scores printed per fixture in test output (visible with pytest -s)"
  - "Failed assertions include ground truth and recognized text snippets for quick diagnosis"
duration: 25m
verification_result: passed
completed_at: 2025-03-12
blocker_discovered: false
---

# T03: Test fixtures + CER/WER quality benchmarks

**Built synthetic OCR test fixtures across 3 categories and parametrized CER/WER quality benchmarks using jiwer — all 14 tests pass with 0% error rates.**

## What Happened

Built the fixture generator that creates 7 synthetic test images using Pillow with TrueType fonts (Helvetica on macOS, DejaVu fallback on Linux): 3 clean printed English, 2 multi-column layouts with column gap, and 2 degraded (one with 2° rotation, one with Gaussian noise). Each image gets a matching `.gt.txt` file with the exact rendered text.

The multi-column ground truth required careful handling — PaddleOCR reads row-by-row across both columns (interleaving left and right lines by y-position), not column-by-column. Initial ground truth used all-left-then-all-right ordering, which inflated CER to ~60% despite perfect character recognition. Fixed by interleaving ground truth lines to match the actual reading order.

Implemented quality measurement using jiwer 4.0.0 with text normalization transforms (strip, lowercase, collapse whitespace). The task plan referenced jiwer 3.x API (`truth_transform`) — jiwer 4.x uses `reference_transform` instead.

Created parametrized pytest tests with per-category thresholds: clean < 5% CER / 10% WER, multi-column < 8% / 15%, degraded < 15% / 25%. PaddleOCR PP-OCRv5 achieves 0.0% CER/WER on all synthetic fixtures — the thresholds serve as regression safety nets.

## Verification

- `cd backend && python tests/fixtures/generate_fixtures.py` — generates 7 fixtures (3 clean, 2 multicol, 2 degraded)
- `cd backend && python -m pytest tests/test_quality.py -v -s` — 14/14 passed, all CER/WER = 0.0000
- `cd backend && python -m pytest tests/test_engine.py -v` — 7/7 passed (no regression from conftest.py)
- `cd backend && python -m pytest tests/test_pipeline.py -v` — 6/6 passed (no regression)

Slice-level verification (all three checks pass):
- ✅ `test_engine.py` — PaddleOCR engine loads, recognizes text, returns TextRegion list
- ✅ `test_pipeline.py` — process_file produces searchable PDF with extractable text layer
- ✅ `test_quality.py` — CER/WER thresholds pass on fixture set (clean < 5% CER, multi-column < 8% CER)

## Diagnostics

- Run `cd backend && python -m pytest tests/test_quality.py -v -s` to see per-fixture CER/WER scores
- Regenerate fixtures: `cd backend && python tests/fixtures/generate_fixtures.py`
- On threshold failure: assertion message includes ground truth and recognized text snippets
- Quality measurement available standalone: import `measure_quality()` from `tests/test_quality.py`

## Deviations

- jiwer 4.0.0 API differs from task plan's research notes (3.x API): `truth_transform` → `reference_transform`, `cer()` requires `ReduceToListOfListOfChars` transform
- Multi-column ground truth changed from sequential (all-left-then-all-right) to interleaved (row-by-row) to match PaddleOCR's actual reading order
- 7 fixtures instead of ~10 — 7 covers all 3 categories well; additional fixtures would be diminishing returns for S01

## Known Issues

- None

## Files Created/Modified

- `backend/tests/fixtures/generate_fixtures.py` — synthetic image generator with clean/multicol/degraded categories
- `backend/tests/fixtures/clean_01.png`, `clean_02.png`, `clean_03.png` — clean printed English fixtures
- `backend/tests/fixtures/multicol_01.png`, `multicol_02.png` — two-column layout fixtures
- `backend/tests/fixtures/degraded_01.png`, `degraded_02.png` — rotated and noisy degraded fixtures
- `backend/tests/fixtures/*.gt.txt` — ground truth text files (7 total, one per image)
- `backend/tests/conftest.py` — shared pytest fixtures (session-scoped engine, fixture_dir, load_ground_truth)
- `backend/tests/test_quality.py` — CER/WER measurement helpers and parametrized threshold tests
