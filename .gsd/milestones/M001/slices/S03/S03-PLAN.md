# S03: Drop-and-Go Pipeline

**Goal:** Dropping image files onto the Parsec app window triggers OCR processing with visible progress and produces searchable PDFs next to the originals.
**Demo:** Launch `cargo tauri dev`, drag a PNG onto the window, see it appear in a file list with stage-based progress (queued → processing → complete), find `<name>_ocr.pdf` next to the original.

## Must-Haves

- Sidecar `process_file` command with request-ID correlation and stage-based progress events
- Rust `process_files` Tauri command using `Channel<T>` for ordered progress streaming
- Sequential file dispatch (PaddleOCR is single-threaded) with queue management in Rust
- Drop zone UI accepting PNG/JPEG/TIFF with drag-over visual feedback
- Per-file status cards showing queued/initializing/processing/complete/error states
- Output path computation: `scan.png → scan_ocr.pdf` (R008)
- File extension validation in frontend (immediate feedback) and sidecar (defense in depth)
- Per-file error display without crashing the app (R015)
- Cold-start UX: "Initializing OCR engine..." on first file when PaddleOCR loads

## Proof Level

- This slice proves: integration (full pipeline from UI drop → sidecar OCR → PDF on disk)
- Real runtime required: yes — Tauri app + Python sidecar + PaddleOCR inference
- Human/UAT required: yes — visual inspection of drop zone UX and progress states

## Verification

- `cd backend && python -m pytest tests/test_sidecar.py -v` — all existing + new `process_file` tests pass
- `cargo tauri dev` → drop a test image → `_ocr.pdf` appears next to original
- Progress events stream to UI: file appears as "queued", transitions to "processing", ends at "complete"
- Drop an unsupported file type (e.g. `.txt`) → shows validation error in UI, no crash
- Drop multiple images → all process sequentially with correct individual progress

## Observability / Diagnostics

- Runtime signals: sidecar emits `{"type":"progress","id":"...","stage":"queued|initializing|processing|complete|error"}` on stdout; Rust logs sidecar communication with `eprintln!`
- Inspection surfaces: browser console shows progress events via `Channel.onmessage`; sidecar stderr shows pipeline timing
- Failure visibility: per-file error messages with the pipeline's error string; sidecar logs `ProcessResult.error` on failure
- Redaction constraints: file paths may contain usernames — no special handling needed (local-only app)

## Integration Closure

- Upstream surfaces consumed: `backend/parsec/pipeline.py` `process_file()`, `backend/parsec/sidecar.py` protocol loop, `src-tauri/src/sidecar.rs` spawn/send/kill, `backend/parsec/models.py` `ProcessResult`
- New wiring introduced: Tauri `process_files` command → sidecar `process_file` command → `pipeline.process_file()` → PDF on disk, with `Channel<T>` streaming progress back to frontend
- What remains before milestone is truly usable end-to-end: S04 (multi-language settings), S05 (PDF input + preprocessing), S06 (integration testing)

## Tasks

- [x] **T01: Extend sidecar protocol with process_file command and progress events** `est:1h`
  - Why: The sidecar needs to accept file processing commands, invoke the OCR pipeline, emit stage-based progress events, and return results — all with request-ID correlation for concurrent safety
  - Files: `backend/parsec/sidecar.py`, `backend/tests/test_sidecar.py`
  - Do: Add `process_file` command handler that takes `{cmd, id, input_path}`, computes output path (`_ocr.pdf` suffix), emits progress events (`queued`, `initializing` on first run, `processing`, `complete`/`error`), calls `pipeline.process_file()`, returns final result. Add request-ID field to all responses. Add file extension validation (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`). Write subprocess-based tests for the new command including happy path, missing file, unsupported extension, and progress event streaming.
  - Verify: `cd backend && python -m pytest tests/test_sidecar.py -v` — all tests pass including new ones
  - Done when: sidecar accepts `process_file`, emits progress events with IDs, produces `_ocr.pdf` output, and rejects unsupported extensions

- [x] **T02: Wire Rust process_files command with Channel streaming and sequential dispatch** `est:1h`
  - Why: The Rust layer receives file paths from the frontend, dispatches them one-at-a-time to the sidecar, and streams progress events back through a typed Channel — replacing the one-shot event pattern (D022) with request-ID correlation
  - Files: `src-tauri/src/sidecar.rs`, `src-tauri/src/lib.rs`, `src-tauri/Cargo.toml`
  - Do: Add `uuid` crate dependency. Extend `sidecar.rs` stdout handler to parse `type` field and route `progress` events via a channel registry (map of request-ID → sender). Add `process_files` async Tauri command that takes `Vec<String>` paths and a `Channel<Value>`, iterates sequentially: generates UUID, registers channel, sends `process_file` to sidecar stdin, waits for `complete`/`error` response, forwards all progress events through the Channel, unregisters. Keep `greet_sidecar` working. Update `invoke_handler` registration.
  - Verify: `cd src-tauri && cargo build` compiles clean; `cargo tauri dev` → invoke `process_files` from browser console with a test image path → progress events arrive, PDF created
  - Done when: `process_files` command dispatches files sequentially to sidecar, streams progress events through Channel, and handles errors without panic

- [x] **T03: Build drop zone UI with file list, progress states, and drag-and-drop wiring** `est:1.5h`
  - Why: The user-facing interface — drop zone for drag-and-drop, file list showing per-file progress through all stages, error display, and the complete visual experience of the product
  - Files: `index.html`, `src/main.ts`, `src/styles.css`
  - Do: Replace S02 hello-world UI entirely. Build drop zone using `getCurrentWebview().onDragDropEvent()` — visual feedback on drag-enter/leave, file list population on drop. File cards show name, stage (queued/initializing/processing/complete/error), and timing. Filter accepted extensions in frontend (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`) with immediate error for rejected files. Invoke `process_files` with `Channel` for progress streaming, update file cards on each event. Show "Initializing OCR engine..." on first file. Error states show the pipeline error message. Apply frontend-design skill for a polished, distinctive UI — not generic scaffolding.
  - Verify: `cargo tauri dev` → drop PNG → see progress → verify `_ocr.pdf` exists; drop `.txt` → see error; drop 3 images → all process sequentially with individual progress
  - Done when: full end-to-end pipeline works visually — drop files, see progress, get PDFs — with error handling and polished design

## Files Likely Touched

- `backend/parsec/sidecar.py`
- `backend/tests/test_sidecar.py`
- `src-tauri/src/sidecar.rs`
- `src-tauri/src/lib.rs`
- `src-tauri/Cargo.toml`
- `index.html`
- `src/main.ts`
- `src/styles.css`
