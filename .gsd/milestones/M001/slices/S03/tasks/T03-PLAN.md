---
estimated_steps: 5
estimated_files: 3
---

# T03: Build drop zone UI with file list, progress states, and drag-and-drop wiring

**Slice:** S03 — Drop-and-Go Pipeline
**Milestone:** M001

## Description

Replace the S02 hello-world UI with the real Parsec interface: a drag-and-drop zone that accepts image files, a file list showing per-file progress through OCR stages, and error handling for rejected files. This is vanilla TypeScript with manual DOM manipulation (no framework). Uses `getCurrentWebview().onDragDropEvent()` for native drag-and-drop and Tauri `Channel` for streaming progress from the Rust command. Apply the frontend-design skill for a polished, distinctive look — this is the product's first impression.

## Steps

1. Design the UI layout and aesthetic direction. The app is a document utility — clean, functional, trustworthy. The drop zone is the primary interaction surface. When empty, it dominates the window with clear affordance. When files are processing, the file list takes center stage. Choose a distinctive design direction (not generic blue-on-white) that feels purposeful for a productivity tool.
2. Rewrite `index.html` with the drop zone layout: a large drop area (full-window when no files), a file list container, and a minimal header. Keep the sidecar status indicator (useful for diagnostics) but make it subtle.
3. Rewrite `src/main.ts`:
   - Import `getCurrentWebview` from `@tauri-apps/api/webview` and `Channel` from `@tauri-apps/api/core`
   - Wire `onDragDropEvent`: on `enter` show drop-active visual, on `leave` remove it, on `drop` process the paths, ignore `over` (fires continuously — don't update UI on every event)
   - File extension filtering: accept `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif` — create error entries for rejected files immediately (R003, R015)
   - File state management: track each file's state (queued/initializing/processing/complete/error), render as cards in the file list
   - Create a `Channel` with `onmessage` callback that updates file cards as progress events arrive
   - Invoke `process_files` with accepted paths and the Channel
   - Update file cards on each progress event: stage text, timing, error messages
   - Show "Initializing OCR engine..." on first file's initializing stage
   - On complete: show checkmark, duration, output filename
   - On error: show error message from the pipeline
4. Rewrite `src/styles.css` with the chosen design direction. Key states to style: empty drop zone (large, inviting), drag-active (visual feedback that something will happen), file cards with stage indicators (queued=muted, processing=active animation, complete=success, error=attention), and the overall app chrome.
5. End-to-end verification: `cargo tauri dev`, drop a test PNG from Finder, watch it process, verify `_ocr.pdf` exists. Drop a `.txt` file — verify error appears. Drop 3 PNGs — verify sequential processing with individual progress. Check sidecar status indicator works.

## Must-Haves

- [ ] Drag-and-drop zone accepts files from the OS (Tauri `onDragDropEvent`)
- [ ] File extension filtering with immediate error for unsupported types
- [ ] Per-file status cards showing queued → initializing → processing → complete/error
- [ ] Progress events streamed from Rust Channel update UI in real-time
- [ ] "Initializing OCR engine..." shown during first-file cold start
- [ ] Error states display pipeline error messages (R015)
- [ ] Complete state shows output filename and duration
- [ ] Polished, distinctive visual design (not scaffolding)

## Verification

- `cargo tauri dev` → drop `backend/tests/fixtures/clean_01.png` → file card shows queued → processing → complete, `clean_01_ocr.pdf` exists next to original
- Drop a `.txt` file → immediate error card, no crash
- Drop 3 fixture PNGs → all process sequentially, each with its own progress
- `pnpm build` compiles TypeScript without errors
- Visual inspection: UI is polished, drop zone has clear affordance, states are visually distinct

## Inputs

- T02 output: `process_files` Tauri command with Channel streaming
- `@tauri-apps/api/webview` — `getCurrentWebview().onDragDropEvent()`
- `@tauri-apps/api/core` — `invoke()` and `Channel` class
- Sidecar status events from `src-tauri/src/sidecar.rs` (existing `sidecar-status` event)

## Expected Output

- `index.html` — drop zone layout replacing S02 hello-world scaffold
- `src/main.ts` — complete frontend: drag-drop handling, progress streaming, file state management
- `src/styles.css` — polished design with all interaction states styled
- Proven: full end-to-end pipeline — drop files, see progress, get searchable PDFs
