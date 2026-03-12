---
estimated_steps: 5
estimated_files: 6
---

# T03: Test fixtures + CER/WER quality benchmarks

**Slice:** S01 — OCR Engine + Quality Benchmarks
**Milestone:** M001

## Description

Build the quality safety net for the OCR pipeline. Generate synthetic test images with perfectly known ground truth, measure CER/WER using jiwer, and assert thresholds in pytest. This delivers R016 (quality on par with Tesseract) and R024 (automated quality regression testing).

Synthetic fixtures are preferred over real scans because they give perfect ground truth, are reproducible, and avoid copyright issues. The generator creates realistic "printed document" images using Pillow with controlled degradation variants.

## Steps

1. Create `backend/tests/fixtures/generate_fixtures.py` — a script that generates test images from known text. Categories: (a) 3 clean printed English images — paragraph text rendered at 300 DPI with a standard serif/sans font, (b) 2 multi-column layouts — text in two columns with a dividing gap, (c) 2 slightly degraded — clean text with mild rotation (2-3°), Gaussian noise, or reduced contrast. Each image gets a matching `.gt.txt` file with the exact rendered text. Use Pillow's `ImageDraw.text()` with a TrueType font. Total: ~7 fixtures for S01 (non-English deferred to S04).
2. Run the generator to produce fixtures in `backend/tests/fixtures/`. Commit the generated images and ground truth files so tests are reproducible without regeneration.
3. Create `backend/tests/conftest.py` with shared fixtures: engine instance (session-scoped to avoid repeated cold starts), fixture directory path, helper to load ground truth text.
4. Implement quality measurement helpers in `backend/tests/test_quality.py`: use `jiwer` with transforms (`jiwer.Compose([jiwer.Strip(), jiwer.ToLowerCase(), jiwer.RemoveMultipleSpaces(), jiwer.ReduceToListOfListOfWords()])`) to normalize text before comparison. Helper function `measure_quality(image_path, ground_truth_path, engine) -> (cer, wer)`.
5. Write parametrized pytest tests in `test_quality.py` that iterate over fixture categories, OCR each image, measure CER/WER, print scores, and assert thresholds: clean < 0.05 CER / 0.10 WER, multi-column < 0.08 CER / 0.15 WER, degraded < 0.15 CER / 0.25 WER. Use `pytest.mark.parametrize` with category metadata so failures identify which category and fixture broke.

## Must-Haves

- [ ] Fixture generator producing synthetic test images with known ground truth
- [ ] At least 7 fixture images across 3 categories (clean, multi-column, degraded)
- [ ] Ground truth `.gt.txt` files matching each fixture image exactly
- [ ] CER/WER measurement using jiwer with text normalization
- [ ] Parametrized pytest tests with per-category threshold assertions
- [ ] CER/WER scores printed in test output for visibility

## Verification

- `cd backend && python tests/fixtures/generate_fixtures.py` produces fixture images and ground truth files
- `cd backend && python -m pytest tests/test_quality.py -v` passes with all thresholds met
- Test output shows per-fixture CER/WER scores (e.g., "clean_01.png: CER=0.02, WER=0.05")

## Inputs

- `backend/parsec/paddle_engine.py` — PaddleOcrEngine from T01 (used to OCR fixtures)
- `backend/parsec/pipeline.py` — process_file() from T02 (may use for PDF-based quality check)
- `backend/parsec/models.py` — OcrOptions from T01
- Research: jiwer transforms for text normalization (Strip, ToLowerCase, RemoveMultipleSpaces)
- Research: CER can exceed 100% with many insertions — use "CER < X" thresholds
- Research: quality thresholds from benchmark data — clean <5%, multi-column <8%, degraded <15%

## Expected Output

- `backend/tests/fixtures/generate_fixtures.py` — fixture image generator
- `backend/tests/fixtures/clean_01.png`, `clean_02.png`, `clean_03.png` — clean printed English
- `backend/tests/fixtures/multicol_01.png`, `multicol_02.png` — multi-column layouts
- `backend/tests/fixtures/degraded_01.png`, `degraded_02.png` — slightly degraded
- `backend/tests/fixtures/*.gt.txt` — ground truth text for each fixture
- `backend/tests/conftest.py` — shared pytest fixtures (engine, paths, helpers)
- `backend/tests/test_quality.py` — CER/WER measurement and threshold tests
