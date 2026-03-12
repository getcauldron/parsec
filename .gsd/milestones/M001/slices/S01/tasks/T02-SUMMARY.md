---
id: T02
parent: S01
milestone: M001
provides:
  - process_file() function producing searchable PDFs from image inputs via OCRmyPDF + PaddleOCR plugin
  - Language code mapping from short codes (en) to Tesseract ISO 639-2 (eng) for OCRmyPDF compatibility
key_files:
  - backend/parsec/pipeline.py
  - backend/tests/test_pipeline.py
key_decisions:
  - Used ocrmypdf-paddleocr pip package (v0.1.1) instead of vendoring — it works with PaddleOCR 3.2.0
  - PaddleOCR downgraded from 3.4.0 to 3.2.0 by plugin dependency — predict() API still compatible
  - Pipeline maps OcrOptions.language short codes to Tesseract ISO 639-2 codes for OCRmyPDF validation
patterns_established:
  - process_file() returns ProcessResult with timing/error info — never raises exceptions for expected failures
  - Output directory auto-created by pipeline before calling OCRmyPDF
observability_surfaces:
  - parsec.pipeline logger: logs input/output paths at start, duration at completion, full error on failure
  - ProcessResult.success/error/duration_seconds for programmatic inspection
  - Manual test: `python -c "from parsec.pipeline import process_file; from pathlib import Path; r = process_file(Path('img.png'), Path('out.pdf')); print(r)"`
duration: ~25min
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T02: OCRmyPDF pipeline producing searchable PDFs from images

**Wired OCRmyPDF with the ocrmypdf-paddleocr plugin to produce searchable PDFs from PNG/JPEG/TIFF images.**

## What Happened

Installed the `ocrmypdf-paddleocr` plugin (v0.1.1) from PyPI. It downgraded PaddleOCR from 3.4.0→3.2.0 and PaddlePaddle from 3.3.0→3.2.2 due to its dependency pins. Verified the predict() API remains compatible — all T01 engine tests still pass.

Built `pipeline.py` with `process_file()` that calls `ocrmypdf.ocr()` programmatically with the PaddleOCR plugin, `output_type="pdf"` (no Ghostscript needed), `image_dpi=300` for images without DPI metadata, and `jobs=1` (PaddlePaddle isn't multi-process safe).

Hit one issue: OCRmyPDF validates language codes against the plugin's Tesseract-style supported languages set (`eng`, not `en`). Added `_to_tesseract_lang()` mapping in the pipeline to bridge our short codes to ISO 639-2.

Wrote 6 pipeline tests covering PNG input, JPEG input, ProcessResult population, missing file error handling, custom OcrOptions, and auto-creation of output directories. All use Pillow-generated test images with known text and verify extracted text via pdfminer.six.

## Verification

- `cd backend && python -m pytest tests/test_pipeline.py -v` — 6/6 passed
- `cd backend && python -m pytest tests/test_engine.py -v` — 7/7 passed (T01 tests unbroken by PaddleOCR downgrade)
- Full suite: 13 tests pass in 16s
- pdfminer extracts "quick", "brown", "fox", "lazy", "dog" from PNG output PDF
- pdfminer extracts "hello", "world" from JPEG output PDF
- Observability verified: parsec.pipeline logger emits input/output paths and duration

### Slice-level verification status

- ✅ `cd backend && python -m pytest tests/test_engine.py -v` — passes
- ✅ `cd backend && python -m pytest tests/test_pipeline.py -v` — passes
- ⬜ `cd backend && python -m pytest tests/test_quality.py -v` — not yet created (T03)

## Diagnostics

- Call `process_file()` directly and inspect the returned ProcessResult
- Enable logging: `logging.basicConfig(level=logging.INFO)` to see pipeline timing
- On failure: ProcessResult.success=False, ProcessResult.error contains exception type and message
- Ghostscript not needed (output_type="pdf" skips PDF/A conversion)
- Tesseract 5.5.2 present but only used by OCRmyPDF for language validation, not for OCR

## Deviations

- Task plan suggested vendoring the plugin if incompatible — the published pip package (v0.1.1) works, so no vendoring was needed (D016)
- PaddleOCR downgraded from 3.4.0 to 3.2.0 by plugin dependency pins — acceptable since predict() API is compatible
- Task plan's `process_file` signature included `engine: OcrEngine | None = None` parameter — omitted because the pipeline delegates to OCRmyPDF which manages its own engine via the plugin system. Our OcrEngine interface is for direct OCR; the pipeline uses OCRmyPDF's plugin architecture instead.

## Known Issues

- Ghostscript not installed — prevents PDF/A output type if needed later (`brew install ghostscript`)
- PaddleOCR pinned to 3.2.0 by ocrmypdf-paddleocr — may miss upstream improvements until plugin updates
- `RequestsDependencyWarning` from urllib3/chardet version mismatch — cosmetic, doesn't affect functionality

## Files Created/Modified

- `backend/parsec/pipeline.py` — process_file() orchestrating OCRmyPDF + PaddleOCR plugin with language mapping
- `backend/tests/test_pipeline.py` — 6 integration tests verifying searchable PDF generation and text extraction
