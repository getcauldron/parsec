# S01: OCR Engine + Quality Benchmarks

**Goal:** A Python backend that takes image files, OCRs them with PaddleOCR, produces searchable PDFs, and measures quality against ground truth fixtures.
**Demo:** `python -m pytest backend/tests/ -v` passes — PaddleOCR recognizes text, OCRmyPDF produces searchable PDFs with extractable text layers, and CER/WER meet thresholds on the fixture set.

## Must-Haves

- `OcrEngine` abstract interface with `PaddleOcrEngine` implementation (R012)
- `process_file()` pipeline producing searchable PDF from image input via OCRmyPDF + PaddleOCR plugin (R002, R005)
- Image inputs: PNG, JPEG, TIFF accepted (R003 support)
- Data models: `TextRegion`, `ProcessResult`, `OcrOptions` (boundary contract for S02+)
- Synthetic test fixture set with ground truth text files (R024)
- CER/WER measurement with jiwer, threshold assertions in pytest (R016, R024)
- PaddleOCR PP-OCRv5 loads and runs with auto-downloaded models (R005)

## Proof Level

- This slice proves: contract + integration (Python-level — PaddleOCR → OCRmyPDF → searchable PDF, quality measured)
- Real runtime required: yes (PaddleOCR must load models and run inference)
- Human/UAT required: no (quality is measured numerically via CER/WER)

## Verification

- `cd backend && python -m pytest tests/test_engine.py -v` — PaddleOCR engine loads, recognizes text from test image, returns TextRegion list
- `cd backend && python -m pytest tests/test_pipeline.py -v` — process_file produces searchable PDF with extractable text layer
- `cd backend && python -m pytest tests/test_quality.py -v` — CER/WER thresholds pass on fixture set (clean printed < 5% CER, multi-column < 8% CER)

## Observability / Diagnostics

- Runtime signals: PaddleOCR initialization timing logged, per-image OCR duration logged, CER/WER scores printed during test runs
- Inspection surfaces: `python -c "from parsec.paddle_engine import PaddleOcrEngine; e = PaddleOcrEngine(); print(e.recognize('path'))"` for manual engine testing
- Failure visibility: OCR failures raise typed exceptions with input file path and engine error; quality test failures print actual vs threshold CER/WER
- Redaction constraints: none (no secrets in OCR pipeline)

## Integration Closure

- Upstream surfaces consumed: none (first slice)
- New wiring introduced: `OcrEngine` interface, `process_file()` function, `TextRegion`/`ProcessResult`/`OcrOptions` models — these form the boundary contract for S02 sidecar protocol
- What remains before milestone is truly usable end-to-end: S02 (sidecar), S03 (UI pipeline), S04 (languages), S05 (PDF input + preprocessing), S06 (integration testing)

## Tasks

- [x] **T01: Python project scaffold + PaddleOCR engine implementation** `est:1h`
  - Why: Establishes the project structure, installs dependencies, and proves PaddleOCR loads and recognizes text — the highest-risk unknown in this slice
  - Files: `backend/pyproject.toml`, `backend/parsec/__init__.py`, `backend/parsec/models.py`, `backend/parsec/engine.py`, `backend/parsec/paddle_engine.py`, `backend/tests/test_engine.py`
  - Do: Create Python project with pyproject.toml (paddlepaddle, paddleocr, ocrmypdf, jiwer, pdfminer.six, pillow). Implement `OcrEngine` ABC with `recognize(image_path) → list[TextRegion]` and engine metadata methods. Implement `PaddleOcrEngine` using PP-OCRv5 `predict()` API with singleton initialization. Define `TextRegion` (text, bbox, confidence), `ProcessResult`, `OcrOptions` dataclasses. Write pytest tests that load the engine and OCR a simple generated test image.
  - Verify: `cd backend && python -m pytest tests/test_engine.py -v` passes
  - Done when: PaddleOcrEngine returns recognized text regions from a test image with >0 confidence scores

- [x] **T02: OCRmyPDF pipeline producing searchable PDFs from images** `est:45m`
  - Why: Proves the full image → searchable PDF pipeline using OCRmyPDF + PaddleOCR plugin, retiring the riskiest integration unknown and delivering R002
  - Files: `backend/parsec/pipeline.py`, `backend/tests/test_pipeline.py`
  - Do: Implement `process_file(input_path, output_path, engine, options) → ProcessResult` that calls `ocrmypdf.ocr()` with the PaddleOCR plugin. Handle image DPI defaults (`--image-dpi 300`). Verify the `ocrmypdf-paddleocr` plugin works with current PaddleOCR — if incompatible, vendor the key hOCR generation logic. Write tests that process PNG/JPEG images and assert output PDFs have extractable text via pdfminer.
  - Verify: `cd backend && python -m pytest tests/test_pipeline.py -v` passes
  - Done when: Input PNG/JPEG → output PDF with invisible text layer that pdfminer can extract, matching the input image content

- [x] **T03: Test fixtures + CER/WER quality benchmarks** `est:1h`
  - Why: Establishes the quality safety net (R016, R024) — synthetic fixtures with known ground truth, jiwer-based measurement, and pytest threshold assertions that catch regressions
  - Files: `backend/tests/fixtures/generate_fixtures.py`, `backend/tests/fixtures/*.png`, `backend/tests/fixtures/*.gt.txt`, `backend/tests/test_quality.py`, `backend/tests/conftest.py`
  - Do: Build a fixture generator that renders known text onto images using Pillow (clean printed, multi-column, slightly degraded variants). Generate ~10 fixture images with matching `.gt.txt` ground truth files. Implement CER/WER measurement helpers using jiwer with appropriate text normalization (strip, lowercase, collapse whitespace). Write pytest tests that OCR each fixture, measure CER/WER against ground truth, and assert thresholds: clean < 5% CER / 10% WER, multi-column < 8% CER / 15% WER, degraded < 15% CER / 25% WER.
  - Verify: `cd backend && python -m pytest tests/test_quality.py -v` passes with all thresholds met
  - Done when: pytest quality suite passes, CER/WER scores are printed per fixture, and any future engine/preprocessing change that degrades quality will fail the tests

## Files Likely Touched

- `backend/pyproject.toml`
- `backend/parsec/__init__.py`
- `backend/parsec/models.py`
- `backend/parsec/engine.py`
- `backend/parsec/paddle_engine.py`
- `backend/parsec/pipeline.py`
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/test_engine.py`
- `backend/tests/test_pipeline.py`
- `backend/tests/test_quality.py`
- `backend/tests/fixtures/generate_fixtures.py`
- `backend/tests/fixtures/*.png`
- `backend/tests/fixtures/*.gt.txt`
