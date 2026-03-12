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
