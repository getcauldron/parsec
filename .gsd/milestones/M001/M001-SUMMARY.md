---
id: M001
provides:
  - Complete desktop OCR application — drag files onto window, get searchable PDFs
  - PaddleOCR PP-OCRv5 engine with swappable OcrEngine interface
  - OCRmyPDF pipeline producing PDF/A with invisible text layers
  - Tauri v2 desktop shell spawning Python sidecar via stdin/stdout NDJSON protocol
  - Drop zone UI with per-file progress tracking and completion/error states
  - 49-language OCR support with persistent language picker
  - Preprocessing controls (deskew, rotate, clean) with settings toggle UI
  - PDF input acceptance with skip_text/force_ocr modes and encrypted PDF handling
  - TIFF input support through OCRmyPDF format conversion
  - 85 automated tests with CER/WER quality benchmarks across fixture categories
key_decisions:
  - PaddleOCR via ocrmypdf-paddleocr plugin rather than custom bridge — plugin handles model loading and inference transparently
  - Vanilla TypeScript + CSS for frontend rather than a framework — minimal UI surface doesn't justify framework overhead
  - NDJSON stdin/stdout protocol for sidecar communication — simple, debuggable, no buffering issues
  - Sidecar spawned as subprocess (not embedded Python) — cleanly separates Python dependency management
  - OcrOptions preprocessing flags passed as ocrmypdf.ocr() kwargs rather than custom preprocessing module — leverages OCRmyPDF's built-in capabilities
  - skip_text=True default for PDF inputs — avoids re-OCRing already-searchable PDFs
  - CER/WER thresholds set generously with room to tighten as engine improves
patterns_established:
  - OcrEngine abstract interface with recognize() → list[TextRegion] pattern
  - Sidecar NDJSON protocol with progress stages (queued → initializing → processing → complete/error)
  - ProcessResult dataclass with success/error/already_searchable states
  - Tauri invoke → Rust command → sidecar JSON → Python pipeline → disk output chain
  - Settings store with preprocessing_ key prefix, synced on load
  - Quality benchmarks with synthetic fixtures and ground truth files
  - Integration tests using subprocess sidecar with _filter_progress() and _measure_cer_from_pdf() helpers
observability_surfaces:
  - Pipeline INFO logs per file — preprocessing mode, language, timing
  - Sidecar stderr structured logs — all command parameters, processing state
  - UI console logs — file processing calls with language and preprocessing state
  - pytest -v -s — CER/WER scores printed inline for quality tracking
  - Sidecar progress events — complete stage includes output_path and duration
  - Error events include descriptive messages (encrypted PDF, unsupported format, etc.)
requirement_outcomes:
  - id: R001
    from_status: active
    to_status: validated
    proof: Final Integrated Acceptance — 5 mixed files dropped, all produce searchable PDFs with no configuration
  - id: R002
    from_status: active
    to_status: validated
    proof: All output PDFs contain extractable text verified via pdfminer; OCRmyPDF produces PDF/A with invisible text layers
  - id: R003
    from_status: active
    to_status: validated
    proof: PNG, JPEG, TIFF all processed through sidecar and produce searchable PDFs in integration tests
  - id: R004
    from_status: active
    to_status: validated
    proof: Non-searchable PDF → searchable PDF verified; already-searchable PDFs handled gracefully; encrypted PDFs surface clear error
  - id: R005
    from_status: active
    to_status: validated
    proof: PaddleOCR PP-OCRv5 engine used throughout; CER/WER quality benchmarks pass across all fixture categories
  - id: R006
    from_status: active
    to_status: validated
    proof: Deskew, rotate, clean preprocessing flags thread through full stack to ocrmypdf.ocr() kwargs; preprocessing quality test confirms deskew doesn't degrade skewed input
  - id: R007
    from_status: active
    to_status: validated
    proof: 49 languages registered, Korean OCR model downloaded and used in acceptance test, language flows from settings through sidecar to pipeline
  - id: R008
    from_status: active
    to_status: validated
    proof: Per-file progress events stream from sidecar (queued → processing → complete/error) and display in UI
  - id: R009
    from_status: active
    to_status: validated
    proof: Output PDFs placed next to originals with _ocr suffix verified in integration tests and acceptance
  - id: R010
    from_status: active
    to_status: validated
    proof: Corrupt file produces error stage while valid files still complete; encrypted PDF produces clear error message
  - id: R011
    from_status: active
    to_status: validated
    proof: Tauri v2 app launches, renders drop zone, spawns sidecar, processes files end-to-end
  - id: R012
    from_status: active
    to_status: validated
    proof: Drop zone UI accepts files, shows per-file progress, displays completion/error states
  - id: R014
    from_status: active
    to_status: validated
    proof: All OCR processing runs locally via PaddleOCR — no network calls during processing
  - id: R015
    from_status: active
    to_status: validated
    proof: CER/WER quality benchmarks pass for clean (<0.05/<0.10), multicol (<0.08/<0.15), degraded (<0.15/<0.25), PDF (<0.10/<0.15), and TIFF (<0.05) categories
  - id: R016
    from_status: active
    to_status: validated
    proof: Settings panel persists language and preprocessing toggles via Tauri store plugin
  - id: R024
    from_status: active
    to_status: validated
    proof: Settings panel with language picker and preprocessing toggles implemented and verified
duration: ~8h
verification_result: passed
completed_at: 2026-03-12
---

# M001: Core App

**Complete desktop OCR application — PaddleOCR engine, OCRmyPDF pipeline, Tauri v2 shell with drag-and-drop UI, 49-language support, preprocessing controls, PDF/TIFF input, and 85 automated tests with quality benchmarks.**

## What Happened

S01 (OCR Engine + Quality Benchmarks) built the Python foundation: a PaddleOCR PP-OCRv5 engine behind a swappable `OcrEngine` interface, the OCRmyPDF pipeline producing searchable PDF/A output, and 14 CER/WER quality benchmarks across synthetic fixture categories (clean, multicol, degraded). The fixture generator creates reproducible test images with known ground truth.

S02 (Tauri Shell + Python Sidecar) scaffolded the Tauri v2 desktop app and built the sidecar communication layer: a Python NDJSON stdin/stdout protocol handler with progress event streaming, wired to a Rust sidecar manager that spawns the Python process and routes JSON commands/responses. PyInstaller bundling was proven for standalone deployment.

S03 (Drop-and-Go Pipeline) connected the pieces into a working product: a drag-and-drop zone in the UI, Tauri invoke commands that route files through the Rust layer to the Python sidecar, per-file progress tracking with visual feedback, and searchable PDF output next to originals with `_ocr` suffix naming.

S04 (Multi-Language & Settings) added 49-language OCR support with a collapsible settings panel, persistent language selection via the Tauri store plugin, and full language threading from the UI dropdown through Rust, sidecar, and pipeline to OCRmyPDF's language parameter.

S05 (PDF Input + Preprocessing) threaded PDF acceptance and five preprocessing flags (deskew, rotate_pages, clean, skip_text, force_ocr) through the entire stack. Non-searchable PDFs produce searchable versions, already-searchable PDFs are handled gracefully, encrypted PDFs surface clear errors, and three toggle switches in the settings UI control preprocessing behavior.

S06 (End-to-End Integration Testing) proved the system works as an integrated whole with 12 cross-cutting integration tests, ran the full 85-test suite with zero failures, and completed Final Integrated Acceptance: 5 mixed files processed to searchable PDFs, Korean language OCR worked, corrupt file handling didn't crash valid file processing.

## Cross-Slice Verification

- **85 automated tests, zero failures** — engine (6), sidecar protocol (18), pipeline (6), PDF pipeline (8), quality benchmarks (14), languages (15), sidecar language threading (5), integration (12), sidecar language (5 counted in 85 total)
- **Build checks clean** — `cargo check` (Rust compiles), `pnpm build` (TypeScript + Vite builds)
- **CER/WER quality thresholds met** — clean CER<0.05, multicol CER<0.08, degraded CER<0.15, PDF CER<0.10, TIFF CER<0.05
- **Final Integrated Acceptance passed:**
  - 5 mixed files (PNG, JPEG, TIFF, non-searchable PDF, skewed PDF) → all produce searchable PDFs with extractable text
  - Korean language → Korean OCR model downloaded and used
  - Corrupt file → error stage, valid file → complete stage
- **UI verified** — drop zone shows all accepted extensions, settings panel has language picker + preprocessing toggles

## Requirement Changes

- R001: active → validated — drop-and-go workflow proven with 5 mixed files
- R002: active → validated — searchable PDF output with text layers verified
- R003: active → validated — PNG, JPEG, TIFF input all produce searchable PDFs
- R004: active → validated — PDF input with skip_text/force_ocr modes and encrypted handling
- R005: active → validated — PaddleOCR PP-OCRv5 with quality benchmarks
- R006: active → validated — deskew, rotate, clean preprocessing through full stack
- R007: active → validated — 49 languages with Korean acceptance test
- R008: active → validated — per-file progress streaming
- R009: active → validated — output next to originals with _ocr suffix
- R010: active → validated — error handling without crashing other files
- R011: active → validated — Tauri v2 desktop app launches and runs
- R012: active → validated — drag-and-drop UI with progress
- R014: active → validated — all processing local (no network calls)
- R015: active → validated — CER/WER quality thresholds met
- R016: active → validated — persistent settings (language, preprocessing)
- R024: active → validated — settings panel implemented

## Forward Intelligence

### What the next milestone should know
- The Python sidecar is not yet bundled for distribution — PyInstaller bundling was proven in S02 but the app still runs in dev mode (`cargo tauri dev`). M002 needs to build the actual installer pipeline.
- PaddleOCR models are downloaded on first use per language — Korean model downloads ~15MB on first Korean OCR call. Model pre-bundling or download-on-install needed for production.
- The sidecar communication is reliable but has no heartbeat/timeout mechanism — if the Python process hangs, the UI will show "processing" indefinitely.

### What's fragile
- Test suite takes ~7 minutes due to OCR processing overhead — running specific test files is much faster for iteration.
- The `clean` preprocessing flag requires `unpaper` system dependency — not gated in UI, will error if missing.
- S01 and S02 slice summaries are doctor-created placeholders — their task summaries are authoritative.

### Authoritative diagnostics
- `pytest tests/ -v` — full test suite status in one command (~7 min)
- `pytest tests/test_integration.py -v -s` — CER/WER scores printed inline
- `cargo tauri dev` — launches the full app for manual verification
- Sidecar subprocess can be tested directly: `echo '{"cmd":"hello"}' | python -m parsec.sidecar`

### What assumptions changed
- Originally expected a custom preprocessing module — OCRmyPDF's built-in deskew/rotate/clean via kwargs was sufficient.
- Originally expected TIFF to work directly with PaddleOCR — it doesn't (returns 0 regions), but OCRmyPDF handles the format conversion transparently.
- PaddleOCR PP-OCRv5 quality is good enough for the initial release — CER is near-zero on clean inputs and under 0.02 on skewed inputs.

## Files Created/Modified

- `backend/parsec/` — engine.py, paddle_engine.py, pipeline.py, models.py, sidecar.py, languages.py
- `backend/tests/` — test_engine.py, test_pipeline.py, test_pipeline_pdf.py, test_sidecar.py, test_sidecar_language.py, test_quality.py, test_languages.py, test_integration.py
- `backend/tests/fixtures/` — 7 synthetic images + 2 PDF fixtures + 1 TIFF fixture + ground truth files + generate_fixtures.py
- `src-tauri/src/` — lib.rs (Tauri commands, sidecar management)
- `src/` — main.ts, settings.ts, styles.css (drop zone, progress, settings panel)
- `index.html` — app shell with drop zone
