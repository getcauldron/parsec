# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|------|-------|----------|--------|-----------|------------|
| D001 | M001 | arch | Desktop framework | Tauri v2 | Cross-platform, tiny bundle size (~10MB vs Electron's 100MB+), native WebView, Rust core | No |
| D002 | M001 | arch | OCR engine default | PaddleOCR (PP-OCRv5) | Better accuracy than Tesseract on complex layouts, small models (~15MB), user chose this | No |
| D003 | M001 | arch | OCR engine architecture | Swappable interface | User explicitly didn't want to marry to one engine; abstract OcrEngine interface | No |
| D004 | M001 | arch | PDF generation | OCRmyPDF | Handles PDF/A, text layer placement, optimization — no reason to reimplement PDF plumbing | Yes — if OCRmyPDF proves too rigid |
| D005 | M001 | arch | Python ↔ Tauri communication | Sidecar via stdin/stdout JSON | Tauri's native sidecar API, proven pattern, avoids HTTP overhead | Yes — if IPC becomes bottleneck |
| D006 | M001 | arch | Python packaging | PyInstaller | Compiles Python + deps into standalone binary per platform, Tauri bundles it | Yes — if PyInstaller causes issues (Nuitka as fallback) |
| D007 | M001 | pattern | Output naming | `_ocr.pdf` suffix next to original | Predictable, no data loss, no configuration needed | No |
| D008 | M001 | pattern | File processing mode | Per-file (1 input → 1 output) | Simple mental model, no merge decisions | Yes — if batch merge added later |
| D009 | M001 | scope | Cross-platform verification | macOS primary in M001, all platforms in M002 | Dev is on macOS; cross-platform packaging is its own problem | No |
| D010 | M001 | scope | Quality assurance | Test fixture set with CER/WER thresholds | Catches regressions automatically, curated for real use cases | No |
| D011 | S01 | pattern | Test fixtures | Synthetic generated images | Perfect ground truth, reproducible, no copyright issues — prefer over real scans for baseline | Yes — add real scans later for realism |
| D012 | S01 | pattern | PDF output type | `--output-type pdf` not `pdfa` | Avoids Ghostscript AGPL dependency for now; revisit PDF/A when distribution model is clear | Yes — switch to PDF/A if licensing resolved |
| D013 | S01 | pattern | ocrmypdf-paddleocr plugin | Vendor key logic if incompatible | Plugin has no PyPI release, 11 commits, uncertain PaddleOCR 3.x compat — vendor rather than depend on external | Yes — use published package if it matures |
| D014 | S01 | infra | Python runtime | Python 3.13 venv (backend/.venv) | System Python is 3.9; PaddlePaddle 3.x requires >=3.10. Homebrew Python 3.13 available, PaddlePaddle 3.3.0 supports it | Yes — pin to 3.12 if 3.13 compat issues arise |
| D015 | S01 | pattern | PaddleOCR init strategy | Lazy init with stdout suppression | PaddleOCR dumps noisy C++ output during init/predict; contextlib.redirect_stdout/stderr to devnull. Init on first recognize() call (~4-5s cold start) | No |
| D016 | S01 | infra | ocrmypdf-paddleocr plugin | Use published pip package (v0.1.1) | Plugin works with PaddleOCR 3.2.0/PaddlePaddle 3.2.2 — pins older versions but predict() API is compatible. No vendoring needed. | Yes — vendor if plugin breaks with future PaddleOCR updates |
| D017 | S01 | pattern | Language code mapping | Pipeline maps short codes (en) to Tesseract ISO 639-2 (eng) | OcrOptions uses short codes user-facing; OCRmyPDF + plugin validate against Tesseract lang list. Pipeline._to_tesseract_lang() bridges them | No |
| D018 | S01 | pattern | Multi-column ground truth order | Interleaved by row (left-1, right-1, left-2, right-2) | PaddleOCR reads top-to-bottom, left-to-right across columns. Ground truth must match reading order for meaningful CER/WER. Sequential (all-left-then-all-right) inflates error rates to ~60% even with perfect character recognition | No |
| D019 | S01 | infra | jiwer API version | Use jiwer 4.x `reference_transform` param | jiwer 4.0.0 renamed `truth_transform` to `reference_transform`. `cer()` needs `ReduceToListOfListOfChars`, `wer()` needs `ReduceToListOfListOfWords` | No |
