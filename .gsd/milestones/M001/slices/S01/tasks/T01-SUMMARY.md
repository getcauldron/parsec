---
id: T01
parent: S01
milestone: M001
provides:
  - OcrEngine ABC with recognize/name/version methods
  - PaddleOcrEngine implementation using PP-OCRv5 predict() API
  - TextRegion, ProcessResult, OcrOptions dataclasses
  - Python project scaffold with all S01 dependencies
key_files:
  - backend/parsec/engine.py
  - backend/parsec/paddle_engine.py
  - backend/parsec/models.py
  - backend/pyproject.toml
key_decisions:
  - Used Python 3.13 venv (PaddlePaddle 3.x requires >=3.10, system Python is 3.9)
  - PaddleOCR initialized with doc orientation/unwarping/textline orientation disabled for speed — these are OCRmyPDF's job
  - Lazy init with stdout/stderr suppression during both init and predict — PaddleOCR is extremely noisy
  - Module-scoped pytest fixture for engine to avoid repeated ~60s cold starts
patterns_established:
  - Lazy singleton pattern for PaddleOcrEngine — first recognize() call triggers model load
  - stdout/stderr suppression via contextlib.redirect for noisy C++ backends
  - Polygon-to-bbox conversion for PaddleOCR dt_polys → axis-aligned TextRegion.bbox
  - Test image generation with Pillow for deterministic OCR test fixtures
observability_surfaces:
  - PaddleOCR init timing logged at INFO level
  - Per-image OCR duration logged at INFO level
  - FileNotFoundError with path context for missing images
  - RuntimeError wrapping PaddleOCR failures with input path context
duration: 15m
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T01: Python project scaffold + PaddleOCR engine implementation

**Built the Python backend scaffold and proved PaddleOCR PP-OCRv5 loads, recognizes text, and returns structured TextRegion results.**

## What Happened

Created the project from scratch: pyproject.toml with all S01 dependencies (paddlepaddle 3.3.0, paddleocr 3.4.0, ocrmypdf, jiwer, pillow, pdfminer.six), data models (TextRegion, OcrOptions, ProcessResult), OcrEngine ABC, and PaddleOcrEngine implementation.

PaddleOcrEngine uses the v3.x `predict()` API with `return_word_box=True`. It lazy-initializes on first `recognize()` call, suppresses PaddleOCR's noisy stdout during both init and inference, and maps the result structure (rec_texts, rec_scores, dt_polys) to TextRegion instances with axis-aligned bounding boxes.

The venv uses Python 3.13 since PaddlePaddle 3.x requires >=3.10 and the system Python is 3.9.

## Verification

- `cd backend && pip install -e ".[dev]"` — clean install, all deps resolved
- `cd backend && python -m pytest tests/test_engine.py -v` — **7/7 tests passed** in 62.6s
  - Engine name/version metadata correct
  - Recognizes "Hello World" from generated test image
  - Recognized text contains expected words
  - Bounding boxes have positive dimensions
  - FileNotFoundError raised for missing images
  - Works with explicit OcrOptions

Slice-level verification: 1/3 checks passing (test_engine.py ✅, test_pipeline.py ⬜ T02, test_quality.py ⬜ T03)

## Diagnostics

- Manual engine test: `cd backend && source .venv/bin/activate && python -c "from parsec.paddle_engine import PaddleOcrEngine; e = PaddleOcrEngine(); print(e.recognize('path/to/image.png'))"`
- PaddleOCR models cached at `~/.paddleocr/` (~15MB, auto-downloaded on first run)
- Init takes ~4-5s on first call (model load), subsequent calls are fast
- Logging: `logging.basicConfig(level=logging.INFO)` to see init/inference timing

## Deviations

None.

## Known Issues

- PaddleOCR's `return_word_box=True` param is passed but may not affect all model configurations — word-level vs line-level detection depends on the model. Currently returns line-level boxes which is sufficient for S01 quality measurement.
- Two deprecation-style warnings from requests/paddle during test runs — cosmetic, not functional.

## Files Created/Modified

- `backend/pyproject.toml` — project metadata, all S01 dependencies, pytest config
- `backend/parsec/__init__.py` — package init
- `backend/parsec/models.py` — TextRegion, OcrOptions, ProcessResult dataclasses
- `backend/parsec/engine.py` — OcrEngine ABC (R012 swappable interface)
- `backend/parsec/paddle_engine.py` — PaddleOcrEngine with lazy init and predict() API
- `backend/tests/__init__.py` — test package init
- `backend/tests/test_engine.py` — 7 integration tests for PaddleOcrEngine
