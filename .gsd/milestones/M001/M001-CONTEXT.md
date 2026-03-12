# M001: Core App — Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

## Project Description

Parsec is a cross-platform desktop app that wraps PaddleOCR and OCRmyPDF behind a pleasant drag-and-drop UI, turning scanned documents into searchable PDFs. The free alternative to ABBYY FineReader.

## Why This Milestone

This milestone builds the entire working product end-to-end: the OCR Python backend, the Tauri desktop shell, and the glue connecting them. After M001, a user on macOS can launch the app, drop files, and get searchable PDFs. M002 handles cross-platform installers and polish.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Launch Parsec, drag image files (PNG/JPEG/TIFF) onto the window, and receive searchable PDFs next to the originals
- Drop non-searchable PDFs and get searchable versions with text layers
- See per-file progress during OCR processing
- Select from 80+ languages in a settings panel
- Toggle preprocessing options (deskew, rotation, contrast)
- Receive clear error messages when something goes wrong

### Entry point / environment

- Entry point: `cargo tauri dev` (development), bundled app binary (production)
- Environment: local desktop — macOS primary for M001, cross-platform verification in M002
- Live dependencies involved: PaddleOCR Python sidecar process, OCRmyPDF library

## Completion Class

- Contract complete means: OCR engine interface is tested, Python pipeline produces correct searchable PDFs from test fixtures, CER/WER meet thresholds
- Integration complete means: Tauri app spawns Python sidecar, files dropped in UI flow through to searchable PDF output on disk
- Operational complete means: app launches cleanly, sidecar starts/stops with app lifecycle, errors surface to UI

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Drop 5 mixed files (PNG, JPEG, TIFF, non-searchable PDF, skewed scan) onto the running app → all 5 produce searchable PDFs next to originals
- Change language to a non-English language, drop a document in that language → text layer contains correct characters
- Drop a corrupt/unsupported file → error message appears in UI, other files still process
- OCR quality on test fixture set meets CER/WER thresholds

## Risks and Unknowns

- **Python sidecar bundling** — packaging PaddleOCR + OCRmyPDF + dependencies into a standalone binary that Tauri can spawn. This is the hardest integration problem.
- **PaddleOCR ↔ OCRmyPDF integration** — OCRmyPDF has a plugin system but PaddleOCR integration maturity is uncertain. May need to write our own bridge.
- **Sidecar communication** — streaming progress events from Python to Tauri frontend via stdin/stdout JSON protocol. Needs to be reliable and not buffer.
- **PaddleOCR model download** — models are ~15MB but need to be bundled or downloaded on first run. Download-on-first-run adds complexity.
- **Cross-platform Python packaging** — PyInstaller binaries are OS-specific. M001 focuses on macOS; M002 must prove Windows/Linux.

## Existing Codebase / Prior Art

- Empty repository — no existing code
- `.gitignore` exists (standard)

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R001 through R016, R024 — all active requirements except R013 (installers, M002)
- See `.gsd/REQUIREMENTS.md` for full details

## Scope

### In Scope

- Python OCR backend with PaddleOCR engine and swappable interface
- OCRmyPDF integration for searchable PDF generation
- Tauri v2 desktop app shell
- Python sidecar spawning and lifecycle management
- Drag-and-drop file input UI
- Per-file progress reporting
- Multi-language support with language picker
- Settings panel (language, preprocessing toggles)
- Auto-preprocessing (deskew, rotate, contrast)
- PDF input processing
- Error handling with user-visible messages
- Test fixture set with CER/WER quality benchmarks
- Output next to originals with _ocr suffix

### Out of Scope / Non-Goals

- Cross-platform installer packaging (M002)
- Auto-updates (M002)
- Cloud OCR / data leaving the machine
- Document management / organization
- Handwriting recognition
- Batch merge into single PDF
- Text export

## Technical Constraints

- Tauri v2 for desktop shell (Rust + WebView)
- Python 3.10+ for OCR backend
- PaddleOCR (PP-OCRv5) as default engine
- OCRmyPDF for PDF/A generation
- PyInstaller for Python sidecar bundling
- stdin/stdout JSON protocol for Tauri ↔ Python communication

## Integration Points

- **PaddleOCR** — Python library, loads models on init, runs inference on images
- **OCRmyPDF** — Python library/CLI, handles PDF plumbing (text layer, optimization, deskew)
- **Tauri sidecar API** — Rust-side process management, stdin/stdout communication
- **PyInstaller** — compiles Python + dependencies into standalone binary per platform

## Open Questions

- **OCRmyPDF plugin vs subprocess** — should we use OCRmyPDF's Python API directly, its plugin interface for PaddleOCR, or shell out to it? Need to evaluate the ocrmypdf-paddleocr plugin maturity.
- **Model bundling strategy** — bundle PaddleOCR models inside the PyInstaller binary, or download on first launch? Bundling adds ~15MB to installer but eliminates first-run friction.
- **Frontend framework** — vanilla JS, Svelte, React, or something else for the Tauri webview UI? Should be lightweight given the minimal UI surface.
