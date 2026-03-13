---
id: S03
parent: M001
milestone: M001
provides:
  - process_file sidecar command with NDJSON progress events (queued → initializing → processing → complete/error)
  - Rust process_files Tauri command with Channel streaming and sequential file dispatch
  - Per-request progress routing via UUID-keyed channel registry in SidecarState
  - Drop zone UI with drag-and-drop file acceptance, per-file status cards, and extension filtering
  - Dark industrial UI aesthetic (D030) — DM Mono/Sans, amber processing, green completion
requires:
  - slice: S01
    provides: OcrEngine interface, PaddleOcrEngine, pipeline.process_file(), test fixtures
  - slice: S02
    provides: Tauri app with sidecar spawn/kill, NDJSON protocol loop, greet_sidecar command
affects:
  - S04
  - S05
  - S06
key_files:
  - backend/parsec/sidecar.py
  - src-tauri/src/sidecar.rs
  - src-tauri/src/lib.rs
  - src/main.ts
  - src/styles.css
  - index.html
key_decisions:
  - Refactored sidecar _handle_command from return-dict to streaming _send() calls — enables multi-message progress events
  - Used tokio::sync::mpsc::unbounded_channel for progress routing (bounded per-file event count makes unbounded safe)
  - Enriched Rust Channel forwarding to inject input_path into progress events (sidecar only sends UUID)
  - Industrial dark aesthetic with DM Mono/Sans, amber/green/red state colors
  - Dev-only window.__parsec_test hook for console-based testing
patterns_established:
  - Progress event protocol — {"type":"progress","id":"...","stage":"..."} on stdout, downstream code matches on type field
  - Progress routing — register channel by request ID before send, forward events, unregister on terminal stage
  - File state management via Map<path, FileEntry> with stage-driven card rendering
  - Drop zone compact/expanded layout toggle based on file count
  - dragEnterCount tracking for reliable drag-active state
observability_surfaces:
  - Console [parsec-ui] prefix for frontend progress events and errors
  - Rust stderr [parsec] prefix for channel registration, routing, dispatch
  - Sidecar stderr [sidecar] prefix for pipeline execution logs
  - Dev-mode testing via window.__parsec_test.processDroppedPaths()
drill_down_paths:
  - .gsd/milestones/M001/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S03/tasks/T02-SUMMARY.md
  - .gsd/milestones/M001/slices/S03/tasks/T03-SUMMARY.md
duration: ~2h
verification_result: passed
completed_at: 2026-03-12
---

# S03: Drop-and-Go Pipeline

**Full end-to-end pipeline: drop image files onto the app window, see per-file progress, get searchable PDFs next to originals.**

## What Happened

Three tasks built the complete pipeline from sidecar protocol through Rust dispatch to frontend UI.

T01 extended the sidecar with a `process_file` command that validates file extensions, computes `_ocr.pdf` output paths, and emits stage-based progress events (queued → initializing → processing → complete/error) with request-ID correlation.

T02 wired the Rust layer with a `process_files` Tauri command that dispatches files sequentially to the sidecar, routing progress events through per-request channels to a Tauri Channel for frontend consumption. Added a UUID-keyed channel registry on SidecarState.

T03 replaced the S02 hello-world scaffold with a polished dark industrial UI — a full-window drop zone that accepts files from Finder via `onDragDropEvent`, shows per-file status cards with real-time progress updates, and handles errors for unsupported file types.

## Verification

- `cd backend && python -m pytest tests/test_sidecar.py -v` — 14 tests pass
- `cd src-tauri && cargo build` — compiles clean
- `pnpm build` — TypeScript/Vite build succeeds
- `cargo tauri dev` → drop image → queued → initializing → processing → complete, _ocr.pdf created
- Drop 3 PNGs → sequential processing with individual progress
- Drop .txt file → rejected at frontend

## Requirements Advanced

- R001 — OCR processing now accessible through UI drag-and-drop
- R003 — File type validation rejects unsupported extensions at frontend
- R008 — Output files placed next to originals with `_ocr.pdf` suffix
- R009 — Per-file progress visible in real-time
- R015 — Pipeline errors surfaced in UI file cards

## Deviations

- Enriched Rust Channel with input_path injection — sidecar only sends UUID, frontend needs path for file correlation
- Fixed sidecar launcher to search for `backend/` instead of `backend/dist/parsec-sidecar`

## Known Limitations

- PyInstaller sidecar binary still fails at runtime — venv Python fallback works for dev
- 2 sidecar tests fail without OCR deps in system Python — env-dependent

## Follow-ups

- Fix PyInstaller packaging for production builds
- File type rejection should show error cards in UI

## Files Created/Modified

- `backend/parsec/sidecar.py` — process_file command, progress events, request-ID correlation
- `backend/tests/test_sidecar.py` — 5 new process_file tests
- `src-tauri/src/sidecar.rs` — progress channel registry, event routing
- `src-tauri/src/lib.rs` — process_files command with Channel streaming
- `src-tauri/Cargo.toml` — uuid, tokio dependencies
- `index.html` — drop zone layout
- `src/main.ts` — drag-drop handling, progress streaming, file state management
- `src/styles.css` — D030 dark industrial aesthetic

## Forward Intelligence

### What the next slice should know
- `process_files` accepts `paths: Vec<String>` and `channel: Channel<Value>` — extend signature for new params
- Settings/UI go in the header area, drop zone is main content
- Sidecar JSON protocol: send `{"cmd":"...","id":"..."}` to stdin, NDJSON on stdout

### What's fragile
- PyInstaller sidecar binary packaging — dev venv fallback works but frozen binary has missing deps
- dragEnterCount for drag state — delicate but working

### Authoritative diagnostics
- Browser `[parsec-ui]` — all progress events
- Rust stderr `[parsec]` — channel routing
- `window.__parsec_test.processDroppedPaths([...])` in dev mode

### What assumptions changed
- Sidecar events don't carry enough context for frontend — had to inject input_path in Rust layer
