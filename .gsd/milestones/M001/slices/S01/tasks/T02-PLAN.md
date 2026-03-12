---
estimated_steps: 4
estimated_files: 3
---

# T02: OCRmyPDF pipeline producing searchable PDFs from images

**Slice:** S01 — OCR Engine + Quality Benchmarks
**Milestone:** M001

## Description

Wire OCRmyPDF with the PaddleOCR plugin to produce searchable PDFs from image files. This proves the core product capability (R002) — an image goes in, a PDF with an invisible text layer comes out.

The critical unknown here is whether the `ocrmypdf-paddleocr` plugin works with the current PaddleOCR version. If it doesn't, we vendor the hOCR generation logic from it rather than depending on an immature external package.

## Steps

1. Install `ocrmypdf-paddleocr` plugin (pip install from git). Test basic invocation: `ocrmypdf --plugin ocrmypdf_paddleocr input.png output.pdf`. If the plugin is incompatible with current PaddleOCR, vendor the key logic (hOCR generation from PaddleOCR results) into `backend/parsec/ocrmypdf_plugin.py`.
2. Implement `backend/parsec/pipeline.py` with `process_file(input_path: Path, output_path: Path, engine: OcrEngine | None = None, options: OcrOptions | None = None) -> ProcessResult`. Core logic: call `ocrmypdf.ocr()` with the PaddleOCR plugin, `--image-dpi 300` for images without DPI metadata, `--output-type pdf` (skip PDF/A to avoid Ghostscript dependency for now). Wrap in try/except for typed error handling. Time the operation and populate ProcessResult.
3. Write `backend/tests/test_pipeline.py`: generate test images (Pillow — white background with paragraphs of text), call `process_file()`, assert output PDF exists, extract text from output PDF using `pdfminer.six`, assert extracted text contains expected words. Test both PNG and JPEG inputs. Use `if __name__ == '__main__'` guard per OCRmyPDF requirement.
4. Verify Tesseract and Ghostscript are available as system dependencies (OCRmyPDF needs them). If missing, document installation commands. Run full test suite to confirm pipeline works end-to-end.

## Must-Haves

- [ ] `process_file()` function producing searchable PDF from PNG/JPEG/TIFF input
- [ ] OCRmyPDF + PaddleOCR plugin integration working (or vendored fallback)
- [ ] Output PDF contains extractable invisible text layer
- [ ] ProcessResult populated with timing, success/error status
- [ ] pytest pipeline tests pass

## Verification

- `cd backend && python -m pytest tests/test_pipeline.py -v` passes
- Output PDF opened in a PDF reader shows original image with selectable text overlay
- `pdfminer` extracts text from output PDF that matches input image content

## Observability Impact

- Signals added/changed: `process_file()` logs input/output paths, processing duration, and any OCRmyPDF warnings
- How a future agent inspects this: call `process_file()` directly from Python REPL and check the returned ProcessResult
- Failure state exposed: ProcessResult.success=False with ProcessResult.error containing the exception message and type

## Inputs

- `backend/parsec/models.py` — TextRegion, ProcessResult, OcrOptions from T01
- `backend/parsec/engine.py` — OcrEngine interface from T01
- `backend/parsec/paddle_engine.py` — PaddleOcrEngine from T01
- Research: `ocrmypdf-paddleocr` plugin may have compatibility issues with PaddleOCR 3.x
- Research: OCRmyPDF accepts images directly, `--image-dpi` for missing DPI metadata
- Research: `if __name__ == '__main__'` guard required on macOS

## Expected Output

- `backend/parsec/pipeline.py` — process_file() orchestrating OCRmyPDF + PaddleOCR
- `backend/parsec/ocrmypdf_plugin.py` — (only if vendoring is needed) PaddleOCR plugin for OCRmyPDF
- `backend/tests/test_pipeline.py` — pipeline integration tests with PDF text extraction verification
