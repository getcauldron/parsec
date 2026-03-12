---
estimated_steps: 5
estimated_files: 7
---

# T01: Python project scaffold + PaddleOCR engine implementation

**Slice:** S01 — OCR Engine + Quality Benchmarks
**Milestone:** M001

## Description

Set up the Python backend project from scratch and prove PaddleOCR works. This is the highest-risk task in the slice — if PaddleOCR doesn't install, load models, or recognize text correctly with the PP-OCRv5 `predict()` API, we find out here before building anything on top of it.

Delivers the `OcrEngine` abstract interface (R012), `PaddleOcrEngine` implementation (R005), and data models that form the boundary contract consumed by S02+.

## Steps

1. Create `backend/pyproject.toml` with project metadata and dependencies: `paddlepaddle>=3.0.0`, `paddleocr>=3.0.0`, `ocrmypdf>=17.0.0`, `jiwer>=3.0.0`, `pillow>=10.0.0`, `pdfminer.six`. Dev dependencies: `pytest>=8.0.0`. Set up `[tool.pytest.ini_options]` with `testpaths = ["tests"]`.
2. Create `backend/parsec/models.py` with dataclasses: `TextRegion` (text: str, bbox: tuple of 4 floats for x1/y1/x2/y2, confidence: float), `OcrOptions` (language: str = "en", dpi: int = 300), `ProcessResult` (input_path: Path, output_path: Path, regions: list[TextRegion], duration_seconds: float, success: bool, error: str | None = None).
3. Create `backend/parsec/engine.py` with `OcrEngine` ABC: abstract methods `recognize(image_path: Path, options: OcrOptions) -> list[TextRegion]`, `name() -> str`, `version() -> str`. Keep it minimal — this is the swappable interface (R012).
4. Create `backend/parsec/paddle_engine.py` with `PaddleOcrEngine(OcrEngine)`: lazy-initialize PaddleOCR on first `recognize()` call (avoid cold start until needed), use `predict()` API with `return_word_box=True`, map PaddleOCR result structure to `TextRegion` list. Log initialization time. Handle PaddleOCR's noisy stdout (suppress or redirect).
5. Create `backend/tests/test_engine.py`: generate a simple test image with Pillow (white background, black text "Hello World"), instantiate `PaddleOcrEngine`, call `recognize()`, assert at least one TextRegion returned with non-empty text and confidence > 0. Install deps with `pip install -e ".[dev]"` and run tests.

## Must-Haves

- [ ] `OcrEngine` ABC with `recognize`, `name`, `version` methods
- [ ] `PaddleOcrEngine` implementing `OcrEngine` using PP-OCRv5 `predict()` API
- [ ] `TextRegion`, `ProcessResult`, `OcrOptions` dataclasses
- [ ] PaddleOCR loads models and recognizes text from a test image
- [ ] pytest passes with engine test

## Verification

- `cd backend && pip install -e ".[dev]"` installs without errors
- `cd backend && python -m pytest tests/test_engine.py -v` passes
- PaddleOcrEngine returns TextRegion list with recognized text matching input image content

## Inputs

- No prior work (first task, first slice)
- Research: PP-OCRv5 uses `ocr.predict()` not `ocr.ocr()`, returns `rec_texts`, `rec_scores`, `dt_polys`
- Research: PaddleOCR cold start ~4.2s, lazy init recommended
- Research: `return_word_box=True` for word-level bounding boxes

## Expected Output

- `backend/pyproject.toml` — project definition with all S01 dependencies
- `backend/parsec/__init__.py` — package init
- `backend/parsec/models.py` — TextRegion, ProcessResult, OcrOptions
- `backend/parsec/engine.py` — OcrEngine ABC
- `backend/parsec/paddle_engine.py` — PaddleOcrEngine implementation
- `backend/tests/__init__.py` — test package init
- `backend/tests/test_engine.py` — engine integration test
