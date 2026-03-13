# S05: PDF Input + Preprocessing — Research

**Date:** 2026-03-12

## Summary

S05 delivers R004 (PDF input) and R006 (auto-preprocessing: deskew, rotation, contrast). The good news: OCRmyPDF already handles both natively. PDF files are a first-class input type — `ocrmypdf.ocr()` accepts them directly. Preprocessing is exposed as boolean flags (`deskew`, `rotate_pages`, `clean`, `clean_final`). The actual work is plumbing: removing the PDF exclusion from sidecar + frontend, extending `OcrOptions` with preprocessing flags, threading those flags through sidecar protocol → pipeline → OCRmyPDF, adding UI toggles, and handling the `already_done_ocr` exit code for PDFs that already have text layers.

No new Python dependencies are needed for core functionality. The `clean`/`clean_final` options require the `unpaper` system binary (already installed on dev via Homebrew), but deskew and rotate work without it. A separate `preprocessing.py` module (mentioned in the boundary map) is unnecessary — OCRmyPDF handles preprocessing internally and applying it in the right order.

The riskiest part is handling already-searchable PDFs correctly. OCRmyPDF returns `ExitCode.already_done_ocr` (code 6) by default when a PDF already contains text. We need a strategy: `skip_text=True` (OCR only pages without text, preserving existing text) is the safest default for user-facing behavior.

## Recommendation

Thread preprocessing flags and PDF support through the existing stack rather than building a separate preprocessing module. Use OCRmyPDF's native capabilities:

1. **PDF input:** Add `.pdf` to both sidecar `ALLOWED_EXTENSIONS` and frontend `ACCEPTED_EXTENSIONS`. Pipeline already accepts PDFs — the only gates are extension checks. Use `skip_text=True` as default to handle already-searchable PDFs gracefully (OCR only non-text pages). Users get `force_ocr` as an advanced option if they want to redo everything.

2. **Preprocessing:** Extend `OcrOptions` with `deskew: bool = False`, `rotate_pages: bool = False`, `clean: bool = False`. Pipeline passes these through to `ocrmypdf.ocr()`. Sidecar protocol accepts them in the `process_file` command. Settings UI gets toggles for each.

3. **Test fixtures:** Generate non-searchable PDF fixtures (image-only PDFs) and a skewed version. Extend quality tests to verify preprocessing improves CER/WER on skewed inputs.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| PDF page extraction to images | OCRmyPDF internals | OCRmyPDF handles PDF→image→OCR→PDF internally — no need for a separate `pdf_input.py` module |
| Deskew correction | `ocrmypdf.ocr(deskew=True)` | Uses Leptonica under the hood, battle-tested, applies at the right pipeline stage |
| Page rotation correction | `ocrmypdf.ocr(rotate_pages=True)` | Detects and corrects 90°/180°/270° rotation using OCR confidence |
| Image cleaning (noise removal) | `ocrmypdf.ocr(clean=True)` via `unpaper` | Removes scan artifacts, dark edges, background noise |
| Already-searchable PDF detection | `ExitCode.already_done_ocr` + `skip_text=True` | Built-in — no need to pre-check PDF text layers |

## Existing Code and Patterns

- `backend/parsec/pipeline.py` — calls `ocrmypdf.ocr()` with language, DPI, plugin, output_type. **Extend** kwargs with `deskew`, `rotate_pages`, `clean`, `clean_final`, `skip_text`, `force_ocr` from OcrOptions.
- `backend/parsec/models.py` — `OcrOptions(language, dpi)`. **Extend** with preprocessing booleans and a `skip_text` flag.
- `backend/parsec/sidecar.py` — `ALLOWED_EXTENSIONS` excludes `.pdf`. **Add** `.pdf`. `_handle_process_file` reads `language` from cmd — **add** preprocessing option reads. Output path computation (`stem + "_ocr.pdf"`) works for PDF inputs too (doc.pdf → doc_ocr.pdf).
- `src/main.ts` — `ACCEPTED_EXTENSIONS` excludes `.pdf`. **Add** `.pdf`. `processDroppedPaths` sends `language` — **add** preprocessing options from settings store.
- `src/settings.ts` — has language picker in collapsible panel. **Add** preprocessing toggle group (deskew, rotate pages, clean) below language picker. Persist via same store plugin.
- `src-tauri/src/lib.rs` — `process_files` takes `(paths, language, channel)`. **Extend** signature with optional preprocessing params or an options struct, forward to sidecar command JSON.
- `backend/tests/fixtures/generate_fixtures.py` — generates clean, multicol, degraded images. **Extend** with a function to create non-searchable PDFs (image wrapped in PDF) and skewed PDF variants.

## Constraints

- **`unpaper` is a system dependency** — required for `clean`/`clean_final`. Present on dev (Homebrew), needs to be documented for M002 packaging. Deskew and rotate work without it.
- **`skip_text` and `force_ocr` are mutually exclusive** in OCRmyPDF — can't pass both. `redo_ocr` is a third option (removes existing OCR layer, re-OCRs, preserves printable text). Default to `skip_text=True` for PDF inputs.
- **PaddleOCR is single-threaded** — `jobs=1` must remain. Multi-page PDFs process sequentially within OCRmyPDF internally.
- **OCRmyPDF exit code 6 (`already_done_ocr`)** — currently treated as failure in pipeline. Must handle gracefully: either use `skip_text` to prevent it, or catch the exit code and report success with a "no OCR needed" message.
- **CSP and store plugin** — already configured from S04. Preprocessing toggles use the same `@tauri-apps/plugin-store` persistence.
- **Output naming for PDFs** — `doc.pdf` → `doc_ocr.pdf` works naturally with the existing `stem + "_ocr.pdf"` convention. No edge case issues.

## Common Pitfalls

- **Forgetting `skip_text=True` for PDF input** — without it, OCRmyPDF returns `already_done_ocr` for any PDF with existing text (even a watermark), which the pipeline currently reports as an error. Users would see failures on PDFs that "should work."
- **`clean` without `unpaper` installed** — OCRmyPDF raises `MissingDependencyError`. The UI toggle must be safe to enable even if `unpaper` isn't installed — catch the error and surface it clearly, or detect `unpaper` availability and disable the toggle.
- **Passing both `skip_text` and `force_ocr`** — OCRmyPDF rejects this combination. The pipeline must ensure only one mode is active. Default: `skip_text=True` for PDFs, no mode flag for images (images always need OCR).
- **Frontend extension filter mismatch** — if the sidecar allows `.pdf` but the frontend still rejects it, dropped PDFs get "rejected" cards. Both gates must be updated together.
- **Preprocessing on images vs PDFs** — deskew/rotate/clean work on both, but `skip_text` only makes sense for PDFs. The pipeline should apply `skip_text` only when input is PDF, not for images.

## Open Risks

- **`unpaper` availability on Windows/Linux** — packaging `unpaper` in PyInstaller is non-trivial. If `clean` is promoted as a default-on feature, it could fail on user machines without `unpaper`. Safest: keep `clean` off by default, document as optional.
- **Multi-page PDF performance** — a 50-page scanned PDF will take minutes. Current progress protocol reports `processing` as a single stage per file with no page-level granularity. Users will see a spinner for a long time. Not a blocker for S05, but worth noting for UX.
- **Encrypted/password-protected PDFs** — OCRmyPDF returns `ExitCode.encrypted_pdf` (code 8). Need to catch and surface as a clear error message.
- **Digital signatures invalidation** — OCRmyPDF has an `invalidate_digital_signatures` param. By default it may refuse to process signed PDFs. Need to decide policy.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Tauri v2 | `nodnarbnitram/claude-code-extensions@tauri-v2` | available (2.3K installs) |
| PaddleOCR | `aidenwu0209/paddleocr-skills@paddleocr-text-recognition` | available (748 installs) |
| OCRmyPDF | (none found) | none found |

## Sources

- OCRmyPDF preprocessing options: `deskew`, `rotate_pages`, `clean`, `clean_final` are native `ocrmypdf.ocr()` kwargs (source: OCRmyPDF readthedocs — cookbook, API reference)
- PDF handling modes: `skip_text`, `force_ocr`, `redo_ocr` control behavior for PDFs with existing text (source: OCRmyPDF readthedocs — errors section)
- Exit codes: `already_done_ocr=6`, `encrypted_pdf=8` (source: `ocrmypdf.ExitCode` enum, verified in venv)
- `unpaper` dependency for `clean`/`clean_final` options (source: OCRmyPDF readthedocs — advanced section)
- Existing pipeline, sidecar, and frontend code reviewed in full (source: local codebase)
