# S01: OCR Engine + Quality Benchmarks — Research

**Date:** 2026-03-12

## Summary

S01's job is to prove the PaddleOCR → searchable PDF pipeline works and establish quality measurement. The critical discovery is that `clefru/ocrmypdf-paddleocr` already exists — a working OCRmyPDF plugin (17 stars, PaddleOCR 3.x word-level bounding boxes, hOCR generation, language code mapping) that bridges PaddleOCR into OCRmyPDF's OcrEngine plugin interface. This eliminates the riskiest unknown in the entire milestone: whether we'd need to hand-roll the PaddleOCR ↔ OCRmyPDF bridge.

The recommended approach is to use OCRmyPDF's Python API with the PaddleOCR plugin for searchable PDF generation, wrap PaddleOCR behind our own `OcrEngine` abstract interface (separate from OCRmyPDF's plugin interface) for the swappable engine requirement (R012), and use `jiwer` for CER/WER quality measurement against a curated fixture set.

OCRmyPDF natively accepts single images (PNG/JPEG/TIFF) as input — it converts them to PDF internally before processing. This means the image → searchable PDF pipeline is `ocrmypdf.ocr(image_path, output_path, plugins=['ocrmypdf_paddleocr'])` — one function call.

## Recommendation

**Use OCRmyPDF + PaddleOCR plugin as the PDF generation backbone. Build our own thin `OcrEngine` interface on top for engine swappability.**

Why: OCRmyPDF handles all PDF plumbing (text layer placement, PDF/A output, image optimization, deskew/rotate). The `ocrmypdf-paddleocr` plugin handles PaddleOCR → hOCR conversion with pixel-accurate word bounding boxes. Writing our own PDF generation would be a multi-week effort with worse results.

Our `OcrEngine` interface (R012) wraps PaddleOCR's `predict()` API and returns structured text regions. This interface is what S02+ will use for the sidecar protocol. The `pipeline.py` orchestrator calls both: our engine for raw OCR results (progress reporting, text extraction) and OCRmyPDF for final PDF generation.

**Architecture:**
```
pipeline.py  ─┬─> OcrEngine.recognize(image) → TextRegion[]   (our interface, for progress/text)
               └─> ocrmypdf.ocr(input, output, plugins=[...])  (OCRmyPDF, for PDF generation)
```

This avoids duplicating OCR work in most cases — OCRmyPDF's plugin calls PaddleOCR internally. The `OcrEngine.recognize()` path is for quality measurement, text extraction, and progress reporting. For the actual PDF output, OCRmyPDF does the heavy lifting.

Alternative considered: calling PaddleOCR directly and generating PDFs with `fpdf2` or `reportlab`. Rejected — we'd be reimplementing OCRmyPDF's text layer positioning, PDF/A compliance, and image optimization. Not worth it.

## Requirements Served

| Req | What S01 Must Deliver |
|-----|----------------------|
| R002 | Prove searchable PDF output with invisible text layer via OCRmyPDF |
| R003 | Prove image inputs (PNG/JPEG/TIFF) are accepted |
| R005 | Prove PaddleOCR PP-OCRv5 as default engine |
| R012 | Deliver swappable `OcrEngine` interface |
| R016 | Measure PaddleOCR quality vs baseline CER/WER thresholds |
| R024 | Deliver test fixture set with CER/WER regression tests |

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| PaddleOCR → searchable PDF | `ocrmypdf` + `ocrmypdf-paddleocr` plugin | Handles text layer, PDF/A, optimization, deskew. Plugin has word-level bounding boxes. |
| CER/WER measurement | `jiwer` | Standard library, C++ backend via RapidFuzz, supports both `wer()` and `cer()` with alignment |
| Image → PDF conversion | `ocrmypdf` natively | Accepts PNG/JPEG/TIFF directly, converts internally before OCR |
| PDF text extraction for verification | `pdfminer.six` or `pikepdf` | Extract text layer from output PDF to compare against ground truth |

## Existing Code and Patterns

- **No existing code** — empty repository. Everything is greenfield.
- `clefru/ocrmypdf-paddleocr` — reference implementation for OCRmyPDF plugin with PaddleOCR. Key patterns:
  - hOCR generation from PaddleOCR polygon results
  - Language code mapping (Tesseract codes → PaddleOCR codes)
  - PaddleOCR 3.x `return_word_box=True` for word-level bounding boxes
  - Token merging for split words (umlauts, punctuation)
  - Polygon edge averaging for tight vertical bounds
- `ocrmypdf/OCRmyPDF-EasyOCR` — another reference plugin (alpha status, 104 stars). Still requires Tesseract for orientation detection.

## Constraints

- **Tesseract still required** — OCRmyPDF plugins (including `ocrmypdf-paddleocr`) still rely on Tesseract for page orientation detection and deskew angle estimation. Tesseract must be installed as a system dependency even though PaddleOCR does the OCR. This is noted in both the EasyOCR and PaddleOCR plugin docs.
- **PaddleOCR cold start** — ~4.2 seconds to initialize (loads 3 neural networks). Acceptable for batch processing but matters for UX. Engine should be initialized once and reused.
- **PP-OCRv5 model auto-download** — models (~15MB) are downloaded on first `PaddleOCR()` initialization to `~/.paddleocr/`. For development this is fine; for bundled app (S02), models need to be included in the PyInstaller binary.
- **Python 3.10+** — PaddlePaddle 3.0 requires Python 3.10+. PaddleOCR 3.x requires PaddlePaddle 3.0+.
- **OCRmyPDF requires Ghostscript** — for PDF/A conversion and rasterization. Must be installed as system dependency (`brew install ghostscript` on macOS).
- **PP-OCRv5 unified model** — single model handles Chinese, Traditional Chinese, English, Japanese, Pinyin. For other languages (French, German, Korean, etc.), separate language-specific recognition models exist with per-language download.
- **`ocrmypdf-paddleocr` maturity** — 11 commits, no PyPI release, requires `pip install` from git. Should vendor or fork key logic rather than depend on it as an external package.

## Common Pitfalls

- **Double OCR execution** — if our `OcrEngine.recognize()` runs PaddleOCR AND then OCRmyPDF's plugin also runs PaddleOCR, we're doing OCR twice per image. For S01 this is acceptable (quality measurement needs raw results, PDF generation needs OCRmyPDF). Optimize in later slices by using OCRmyPDF's `--sidecar` option to extract text alongside PDF generation.
- **DPI not set on images** — scanner images without DPI metadata cause OCRmyPDF to guess, which affects text layer positioning. Use `--image-dpi` when DPI is missing or wrong.
- **PaddleOCR `predict()` API change** — PP-OCRv5 uses `ocr.predict()` not the old `ocr.ocr()`. The result structure changed significantly. Code examples must use the v3.x API.
- **Fixture ground truth encoding** — ground truth text files must be UTF-8 with consistent line endings. CER/WER are sensitive to whitespace normalization — use jiwer transforms to strip and normalize.
- **OCRmyPDF `if __name__ == '__main__'` guard** — required on macOS and Windows due to multiprocessing. The Python API docs explicitly note this.
- **CER can exceed 100%** — when OCR produces many insertions. This is expected behavior, not a bug. Thresholds should be expressed as "CER < X" not "accuracy > Y".

## Open Risks

- **`ocrmypdf-paddleocr` compatibility with latest PaddleOCR** — plugin's pyproject.toml lists `paddleocr>=2.7.0` but PaddleOCR 3.x changed APIs significantly (e.g., `predict()` vs `ocr()`). Need to verify the plugin works with current PaddleOCR version during execution.
- **Tesseract as hard dependency** — even with PaddleOCR doing OCR, Tesseract must be installed for OCRmyPDF's orientation detection. This adds installation complexity. If this becomes a blocker for PyInstaller bundling (S02), we may need to handle orientation detection ourselves.
- **PP-OCRv5 quality on English-only clean documents** — the benchmark data showing 0.08 CER comes from a mixed dataset. Our fixtures need to establish our own baseline. The 13% improvement claim is on PaddleOCR's internal benchmarks, not peer-reviewed.
- **Ghostscript licensing** — Ghostscript has AGPL licensing. OCRmyPDF uses it for PDF/A conversion. Need to verify this doesn't conflict with Parsec's distribution model. Alternative: use `--output-type pdf` instead of `--output-type pdfa` to skip Ghostscript requirement.

## Quality Thresholds

Based on benchmark research, recommended thresholds for the S01 fixture set:

| Category | CER Threshold | WER Threshold | Rationale |
|----------|--------------|---------------|-----------|
| Clean printed English | < 0.05 (5%) | < 0.10 (10%) | PaddleOCR benchmarks ~0.08 CER on mixed; clean should be better |
| Clean printed multi-column | < 0.08 (8%) | < 0.15 (15%) | Column detection adds complexity |
| Slightly skewed (< 5°) | < 0.10 (10%) | < 0.20 (20%) | PaddleOCR handles mild skew internally |
| Low contrast / aged | < 0.15 (15%) | < 0.25 (25%) | Quality degrades on poor inputs |

These are initial targets. Adjust after running the actual fixture set — if PaddleOCR consistently beats these, tighten them. If it misses, investigate preprocessing or accept looser bounds with rationale.

## Test Fixture Strategy

The roadmap calls for 15-20 test images with ground truth. Recommended categories:

1. **Clean printed English** (5 images) — typed letters, book pages, forms
2. **Multi-column layout** (3 images) — newspaper-style, two-column documents
3. **Mixed content** (2 images) — text with images, headers, footers
4. **Slightly degraded** (3 images) — mild skew, slight blur, aged paper
5. **Non-English** (3 images) — French, German, CJK (for S04 forward compatibility)
6. **Edge cases** (2 images) — very small text, rotated 90°, mostly whitespace

Ground truth: manually transcribed `.txt` files, UTF-8, one per image. Named `{image_stem}.gt.txt`.

For S01, focus on categories 1-4 (English quality baseline). Categories 5-6 are forward-looking for S04/S06.

## Fixture Sources

Use freely-licensed document images. Options:
- Render text ourselves (Pillow/reportlab → image) for perfectly controlled ground truth
- Public domain documents from Project Gutenberg (photograph existing scans)
- Generate synthetic "scanned" documents with known text for reliable ground truth

Recommendation: **generate synthetic test images** from known text using Pillow/reportlab. This gives perfect ground truth, reproducible results, and avoids copyright issues. Add 2-3 real scan samples for realism.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| PaddleOCR | `aidenwu0209/paddleocr-skills@paddleocr-text-recognition` | available (743 installs) |
| PaddleOCR | `paddlepaddle/paddleocr@paddleocr-text-recognition` | available (16 installs) |
| OCRmyPDF | (none found) | none found |

The PaddleOCR skill with 743 installs may provide useful implementation guidance. Consider installing if PaddleOCR API integration proves tricky during execution.

## Key Dependencies for S01

```
# Python dependencies
paddlepaddle>=3.0.0      # Deep learning framework (CPU version for dev)
paddleocr>=3.0.0         # OCR toolkit with PP-OCRv5
ocrmypdf>=17.0.0         # PDF generation with text layer
jiwer>=3.0.0             # CER/WER measurement
pillow>=10.0.0           # Image handling
pdfminer.six             # PDF text extraction for verification

# System dependencies
tesseract                # Required by OCRmyPDF (even with PaddleOCR plugin)
ghostscript              # Required by OCRmyPDF for PDF/A (optional if --output-type pdf)
```

## Sources

- OCRmyPDF plugin interface: `OcrEngine` abstract base with `_generate_hocr`, `_generate_pdf`, `_languages`, `_version` methods (source: [OCRmyPDF docs](https://ocrmypdf.readthedocs.io/en/latest/plugins))
- `clefru/ocrmypdf-paddleocr`: working PaddleOCR plugin for OCRmyPDF with word-level bounding boxes (source: [GitHub](https://github.com/clefru/ocrmypdf-paddleocr))
- PaddleOCR PP-OCRv5 API: uses `ocr.predict()`, returns `rec_texts`, `rec_scores`, `dt_polys`, `rec_boxes` (source: [PaddleOCR docs](https://github.com/paddlepaddle/paddleocr))
- PP-OCRv5 models ~15MB total (det 4.4MB + rec 10.5MB), competitive accuracy with 13x smaller models than EasyOCR (source: [benchmark comparison](https://tildalice.io/ocr-tesseract-easyocr-paddleocr-benchmark/))
- jiwer: standard CER/WER library with RapidFuzz C++ backend, `jiwer.cer()` and `jiwer.wer()` (source: [PyPI](https://pypi.org/project/jiwer/), [GitHub](https://github.com/jitsi/jiwer))
- OCRmyPDF accepts image files directly as input, converts internally (source: [OCRmyPDF cookbook](https://ocrmypdf.readthedocs.io/en/latest/cookbook.html))
- OCRmyPDF-EasyOCR: reference plugin, still requires Tesseract for orientation detection (source: [GitHub](https://github.com/ocrmypdf/OCRmyPDF-EasyOCR))
