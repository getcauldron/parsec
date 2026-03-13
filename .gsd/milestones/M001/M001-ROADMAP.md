# M001: Core App

**Vision:** Build Parsec's complete OCR pipeline and desktop UI — from a working PaddleOCR backend to a Tauri drop-and-go interface — so a user can drag documents onto the app and get searchable PDFs.

## Success Criteria

- User can launch Parsec and see a drag-and-drop interface
- Dropping image files (PNG/JPEG/TIFF) produces searchable PDFs next to the originals
- Dropping non-searchable PDFs produces searchable versions
- Per-file progress is visible during processing
- Skewed/rotated scans are auto-corrected before OCR
- Non-English documents can be processed by selecting a language
- Corrupt or unsupported files produce clear error messages without crashing
- OCR quality meets CER/WER thresholds on the test fixture set

## Key Risks / Unknowns

- **Python sidecar bundling** — packaging PaddleOCR + OCRmyPDF into a standalone binary Tauri can spawn is the hardest integration problem
- **PaddleOCR ↔ OCRmyPDF bridge** — the ocrmypdf-paddleocr plugin exists but maturity is uncertain; may need a custom bridge
- **Sidecar communication reliability** — streaming progress over stdin/stdout JSON must not buffer or deadlock
- **PaddleOCR model size/download** — ~15MB models need to be bundled or downloaded; affects installer size and first-run experience

## Proof Strategy

- Python sidecar bundling → retire in S02 by proving Tauri can spawn a PyInstaller-built Python binary and exchange JSON messages
- PaddleOCR ↔ OCRmyPDF bridge → retire in S01 by proving the pipeline produces a valid searchable PDF from an image
- Sidecar communication → retire in S03 by proving progress events stream from Python to the UI in real-time
- Model bundling → retire in S01 by proving PaddleOCR loads and runs with bundled models

## Verification Classes

- Contract verification: pytest suite for OCR engine interface, CER/WER threshold tests on fixture set, file output assertions
- Integration verification: Tauri spawns sidecar, files flow from UI drop → Python processing → PDF on disk
- Operational verification: app launches cleanly, sidecar starts/stops with app lifecycle, errors don't crash the app
- UAT / human verification: visual inspection of searchable PDF quality, UI responsiveness, drag-and-drop feel

## Milestone Definition of Done

This milestone is complete only when all are true:

- All six slices are complete and verified
- Python OCR backend produces searchable PDFs that pass CER/WER thresholds
- Tauri app spawns Python sidecar and manages its lifecycle
- Drag-and-drop UI processes files with visible progress
- Multi-language OCR works via settings
- Auto-preprocessing improves OCR on skewed/rotated inputs
- PDF inputs are processed correctly
- Error handling surfaces failures to the user without crashing
- Final integrated acceptance: 5 mixed files dropped → 5 searchable PDFs, including non-English and skewed inputs

## Requirement Coverage

- Covers: R001, R002, R003, R005, R006, R007, R008, R009, R010, R011, R012, R014, R015, R016, R024
- Partially covers: R004 (PDF input in S05)
- Leaves for later: R013 (installers → M002), R017, R018, R019, R020 (all deferred)
- Orphan risks: none

## Slices

- [x] **S01: OCR Engine + Quality Benchmarks** `risk:high` `depends:[]`
  > After this: a Python script takes an image, OCRs it with PaddleOCR, produces a searchable PDF, and CER/WER are measured against ground truth fixtures.

- [x] **S02: Tauri Shell + Python Sidecar** `risk:high` `depends:[S01]`
  > After this: launching the Tauri app spawns the Python sidecar, and a hello-world JSON exchange proves bidirectional communication.

- [x] **S03: Drop-and-Go Pipeline** `risk:medium` `depends:[S01,S02]`
  > After this: dropping an image file onto the app window shows progress and produces a searchable PDF next to the original.

- [x] **S04: Multi-Language & Settings** `risk:low` `depends:[S03]`
  > After this: selecting a non-English language in settings and dropping a document in that language produces correct OCR output.

- [x] **S05: PDF Input + Preprocessing** `risk:medium` `depends:[S03]`
  > After this: dropping a skewed non-searchable PDF produces a deskewed searchable PDF with improved OCR accuracy.

- [ ] **S06: End-to-End Integration Testing** `risk:low` `depends:[S04,S05]`
  > After this: a batch of mixed inputs (images, PDFs, multi-language, skewed) all process correctly, quality thresholds pass, and error handling is verified.

## Boundary Map

### S01 → S02

Produces:
- `backend/parsec/engine.py` → `OcrEngine` abstract interface (recognize method: image path → list of TextRegion with text, bbox, confidence)
- `backend/parsec/paddle_engine.py` → `PaddleOcrEngine` implementing `OcrEngine`
- `backend/parsec/pipeline.py` → `process_file(input_path, output_path, engine, options) → ProcessResult` (orchestrates OCR + PDF generation)
- `backend/parsec/models.py` → `TextRegion`, `ProcessResult`, `OcrOptions` dataclasses
- `backend/tests/fixtures/` → 15-20 test images with ground truth text files
- `backend/tests/test_quality.py` → CER/WER measurement and threshold assertions

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- Same as S01 → S02, plus:
- `backend/parsec/sidecar.py` → JSON stdin/stdout protocol handler (receives commands, streams progress events, returns results)

Consumes:
- nothing (first slice)

### S02 → S03

Produces:
- `src-tauri/src/sidecar.rs` → Rust-side sidecar manager (spawn, kill, send command, receive events)
- `src-tauri/src/main.rs` → Tauri app with window, sidecar lifecycle management
- `src/` → minimal web UI scaffold (HTML/CSS/JS)
- Proven: PyInstaller binary of the Python backend runs when spawned by Tauri

Consumes from S01:
- `backend/parsec/sidecar.py` → JSON protocol (command/response format)

### S03 → S04

Produces:
- `src/` → drop zone UI with file list, per-file progress bars, completion/error states
- `src-tauri/src/commands.rs` → Tauri commands for file processing (invoke from frontend)
- Proven: full pipeline from UI drop → sidecar → PDF on disk with progress streaming

Consumes from S01:
- `backend/parsec/pipeline.py` → `process_file()`
- `backend/parsec/sidecar.py` → progress event streaming

Consumes from S02:
- `src-tauri/src/sidecar.rs` → sidecar manager

### S03 → S05

Produces:
- Same as S03 → S04

Consumes:
- Same as S03 → S04

### S04 → S06

Produces:
- `src/` → settings panel with language picker, preprocessing toggles
- `backend/parsec/languages.py` → language list, model availability, language code mapping
- Proven: non-English OCR works through the full UI pipeline

Consumes from S03:
- Drop zone UI, Tauri commands, progress streaming

Consumes from S01:
- `backend/parsec/paddle_engine.py` → language parameter support

### S05 → S06

Produces:
- `backend/parsec/preprocessing.py` → deskew, rotation correction, contrast enhancement functions
- `backend/parsec/pdf_input.py` → PDF page extraction to images for OCR
- Proven: skewed/rotated PDFs produce deskewed searchable output

Consumes from S03:
- Drop zone UI, Tauri commands, progress streaming

Consumes from S01:
- `backend/parsec/pipeline.py` → `process_file()` extended with preprocessing options
