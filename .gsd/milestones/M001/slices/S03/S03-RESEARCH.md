# S03: Drop-and-Go Pipeline — Research

**Date:** 2026-03-12

## Summary

S03 connects the three pieces built in S01/S02 — the OCR pipeline, the sidecar protocol, and the Tauri shell — into a working end-to-end product flow: drop images, see progress, get searchable PDFs. The primary challenge is protocol design for concurrent file processing with progress streaming, not any single API gap.

Tauri v2 provides `onDragDropEvent` on the webview (enter/over/drop/leave events with native file paths) and `tauri::ipc::Channel` for ordered streaming from Rust to the frontend. The sidecar already handles NDJSON over stdin/stdout; it needs a `process_file` command and progress event emission. OCRmyPDF doesn't expose a progress callback for single-image processing, so progress will be stage-based (queued → processing → complete/error) rather than percentage-based. This is honest — single-image OCR takes 2-5 seconds and a progress bar would be theatrical.

The current sidecar command/response pattern (D022) uses one-shot event listeners with no request correlation — this breaks with concurrent files. The protocol needs a `request_id` field (already flagged in D022 as "may need request-id correlation for concurrent commands"). Since OCRmyPDF/PaddleOCR are not multi-process safe (`jobs=1`), files should be processed sequentially in the sidecar, with the Rust side managing the queue. This simplifies the protocol — only one file processes at a time, progress events carry a file identifier.

## Recommendation

**Three-layer approach: frontend queue → Rust orchestrator → sidecar worker.**

1. **Frontend**: Drop zone UI collects file paths, displays per-file status cards. Uses Tauri `invoke` with a `Channel` for streaming progress events per-file.
2. **Rust command**: A single `process_files` Tauri command receives the file list and a Channel. It sends files one-at-a-time to the sidecar (sequential, since PaddleOCR is single-threaded), forwards progress events from sidecar stdout back through the Channel.
3. **Python sidecar**: New `process_file` command takes `{cmd: "process_file", id: "<uuid>", input_path: "...", output_path: "..."}`, emits progress events `{type: "progress", id: "<uuid>", stage: "processing"|"complete"|"error", ...}`, and returns a final result.

Use Tauri's `Channel<T>` instead of `app.emit()` for progress streaming — it's ordered, typed, and scoped to the invoking command. The existing event-based pattern in `sidecar.rs` still parses stdout, but routes `progress` events through the Channel rather than broadcasting globally.

File extension validation happens in the frontend (immediate feedback) and again in Python (defense in depth). Accepted: `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`. Output naming follows R008: `scan.png → scan_ocr.pdf`.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Drag-and-drop file input | `getCurrentWebview().onDragDropEvent()` from `@tauri-apps/api/webview` | Native OS drag-drop, provides real file paths, handles enter/over/drop/leave states |
| Streaming progress to frontend | `tauri::ipc::Channel<T>` | Ordered, typed, scoped to command invocation — better than global events for per-file progress |
| File path → searchable PDF | `pipeline.process_file()` from S01 | Already working, tested, uses OCRmyPDF + PaddleOCR plugin |
| Sidecar spawn/kill/stdin | `sidecar.rs` from S02 | Already working with managed state, event forwarding, lifecycle management |
| UUID generation for request IDs | `uuid` crate (Rust), `uuid` stdlib-alternative or inline (Python) | Request-ID correlation for concurrent protocol messages |

## Existing Code and Patterns

- `backend/parsec/sidecar.py` — NDJSON protocol loop with `_handle_command()` dispatch. Extend with `process_file` command. The `_send()` helper is ready for streaming multiple events per command.
- `backend/parsec/pipeline.py` — `process_file(input_path, output_path, options)` → `ProcessResult`. Blocking call, 2-5s per image. No modification needed for S03 — call it from the sidecar.
- `backend/parsec/models.py` — `ProcessResult` has `success`, `error`, `duration_seconds`. Serialize to JSON for protocol responses.
- `src-tauri/src/sidecar.rs` — `send_command()` writes JSON to stdin, stdout events parsed and emitted globally. Extend to route progress events through Channels instead of global emit.
- `src-tauri/src/lib.rs` — `greet_sidecar` uses mpsc pattern (D022). Replace/supplement with `process_files` command using Channel pattern.
- `src/main.ts` — Minimal hello-world UI. Replace entirely with drop zone + file list UI.
- `index.html` — Scaffold HTML. Replace content with drop zone layout.

## Constraints

- **PaddleOCR is not multi-process safe** — `jobs=1` in `ocrmypdf.ocr()`. Files must be processed sequentially in the sidecar. Concurrency is managed in the Rust layer (queue + serial dispatch).
- **OCRmyPDF has no progress callback** — For single images, the entire OCR is one blocking call. Progress is stage-based: queued → processing → complete/error. Percentage progress is not available without forking OCRmyPDF.
- **PaddleOCR cold start is ~4-5 seconds** — First file will be slow due to model loading (`_ensure_initialized` in `PaddleOcrEngine`). Subsequent files are fast. The UI should communicate this (e.g., "Initializing OCR engine..." on first file).
- **Sidecar stdout is shared** — All protocol messages (responses, progress events) go through the same stdout pipe. The Rust side must distinguish between direct command responses and streaming progress events. Use a `type` field in all JSON messages.
- **Vanilla TypeScript frontend** — No framework (React/Svelte). UI updates are manual DOM manipulation. This is fine for the scope — the UI is a drop zone, a file list, and status indicators.
- **File paths come from the OS** — Tauri's `onDragDropEvent` provides absolute native paths. The sidecar process (native binary) can read them directly. No Tauri FS plugin needed.
- **Output path computation** — R008 says output goes next to original with `_ocr.pdf` suffix. This can be computed in either Rust or Python. Recommend Python side (sidecar) since it's closer to the pipeline and avoids path-encoding issues across the IPC boundary.
- **CSP** — Current CSP is `default-src 'self'; script-src 'self'`. No changes needed for this slice since we're not loading external resources.

## Common Pitfalls

- **Sidecar stdout corruption** — PaddleOCR and its C++ dependencies can dump noise to stdout, corrupting the JSON protocol. `sidecar_entry.py` already suppresses this with env vars and `redirect_stdout`, but `process_file` invokes `ocrmypdf.ocr()` which may trigger additional C++ output. The suppression context in `pipeline.py` (via the PaddleOCR plugin) should handle this, but test thoroughly.
- **Blocking the Tauri main thread** — `process_files` Tauri command must be `async` to avoid freezing the UI. The sidecar communication is already async (mpsc channels), but the command handler must not block on synchronous IO.
- **Stdin/stdout ordering** — If we send multiple `process_file` commands before the first finishes, responses could interleave. Solution: send one at a time (sequential processing) and use the `id` field to correlate. Don't pipeline requests.
- **Large file paths with special characters** — File paths from the OS may contain spaces, unicode, or special characters. JSON serialization handles this, but verify that Python's `Path()` handles all macOS path edge cases.
- **Drop zone event flood** — `onDragDropEvent` fires `over` continuously while dragging. Throttle UI updates to avoid jank. `enter`/`leave` are the right signals for visual feedback, not `over`.
- **First-file cold start UX** — If the user drops one file and sees 5+ seconds of nothing, they'll think it's broken. The UI should show "Initializing OCR engine..." during the first file's processing phase. The sidecar can emit a `stage: "initializing"` progress event when PaddleOCR loads for the first time.

## Open Risks

- **OCR inference through PyInstaller binary not yet tested** — S02/T03 noted that "Full OCR inference through the PyInstaller binary (PaddleOCR model loading, actual recognize()) not yet tested." The dev wrapper falls back to venv Python, which works, but the PyInstaller binary may fail when loading PaddleOCR models. This is a risk for distribution but not for `cargo tauri dev` development.
- **OCRmyPDF subprocess spawning inside PyInstaller** — OCRmyPDF may try to spawn subprocesses (e.g., for optimization). These may fail inside a PyInstaller --onedir bundle if they can't find the Python interpreter. Test with the binary, not just venv.
- **macOS file permission dialogs** — When the user drops files from a protected location (e.g., ~/Downloads), macOS may prompt for file access permissions. Tauri should inherit the app's permission scope, but this hasn't been tested.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Tauri v2 | `nodnarbnitram/claude-code-extensions@tauri-v2` | available (2.3K installs) |
| Tauri v2 | `martinholovsky/claude-skills-generator@tauri` | available (233 installs) |
| Frontend design | `frontend-design` | installed |

The `tauri-v2` skill from nodnarbnitram has high install count and may be useful for Tauri-specific patterns. Worth considering if Tauri integration proves tricky.

## Sources

- Tauri v2 `onDragDropEvent` API — `DragDropEvent` type has `enter|over|drop|leave` with `paths: string[]` and `position: PhysicalPosition` (source: `@tauri-apps/api@2.10.1` installed type definitions)
- Tauri `ipc::Channel` for ordered streaming — Rust command accepts `Channel<T>` param, frontend creates `Channel` with `onmessage` callback (source: [Tauri docs — calling frontend](https://github.com/tauri-apps/tauri-docs/blob/v2/src/content/docs/develop/calling-frontend.mdx))
- S01/T03 summary — CER/WER quality benchmarks pass, PaddleOCR PP-OCRv5 achieves 0% error on synthetic fixtures
- S02/T02 summary — Sidecar communication proven with hello-world roundtrip, event-driven command/response pattern established (D022)
- S02/T03 summary — PyInstaller binary builds (652MB), full OCR inference through binary **not yet tested**
- D022 — Current pattern "may need request-id correlation for concurrent commands"

## Requirements Covered

| Requirement | Role | Key Concern |
|-------------|------|-------------|
| R001 — Drop-and-go OCR workflow | **primary owner** | Core flow: drop files → get PDFs. No configuration required. |
| R002 — Searchable PDF output | supporting | Pipeline already produces searchable PDFs (S01). S03 wires it to the UI. |
| R003 — Image input support (PNG/JPEG/TIFF) | **primary owner** | File extension filtering in drop zone + sidecar validation. |
| R008 — Output next to originals with _ocr suffix | **primary owner** | Output path computation: `scan.png → scan_ocr.pdf`. |
| R009 — Per-file output | **primary owner** | 1 input → 1 output. Sequential processing in sidecar. |
| R011 — Progress feedback during OCR | **primary owner** | Stage-based progress (queued/processing/complete/error). Not percentage. |
| R015 — Graceful error handling | **primary owner** | Per-file error states in UI. Pipeline errors don't crash app. |
