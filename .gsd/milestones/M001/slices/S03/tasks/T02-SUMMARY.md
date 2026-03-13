---
id: T02
parent: S03
milestone: M001
provides:
  - process_files Tauri command with Channel streaming and sequential dispatch
  - Progress event routing from sidecar stdout to per-request channels by ID
  - UUID-based request-ID generation for file dispatch
key_files:
  - src-tauri/src/sidecar.rs
  - src-tauri/src/lib.rs
  - src-tauri/Cargo.toml
key_decisions:
  - Used tokio::sync::mpsc::unbounded_channel for progress routing — unbounded is safe here because sidecar events per file are bounded (5-6 events max per file lifecycle)
  - Progress channel registry lives on SidecarState behind std::sync::Mutex — the lock is held briefly for insert/remove/lookup, no async work under lock
  - Non-progress stdout messages (hello, status) continue through global sidecar-response event unchanged — greet_sidecar works without modification
patterns_established:
  - Progress routing pattern — register channel by request ID before sending command, forward events from mpsc receiver to Tauri Channel, unregister on terminal stage (complete/error)
  - Sequential dispatch loop — for each path, register → send → drain events → unregister, one file at a time
  - Sidecar-not-running handled per-file — each file gets its own error event through the Channel, loop continues
observability_surfaces:
  - eprintln! logs for channel registration/unregistration, progress routing with stage, dispatch start/completion
  - Error events through Channel for sidecar-not-running and send failures include input_path for attribution
  - Log format: "[parsec] routed progress for id=<uuid> stage=<stage>", "[parsec] dispatching file path=<path> id=<uuid>", "[parsec] file complete/error id=<uuid>"
duration: 15m
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T02: Wire Rust process_files command with Channel streaming and sequential dispatch

**Added `process_files` Tauri command with per-request progress channel registry routing sidecar events through Tauri Channel for sequential file dispatch.**

## What Happened

Extended `SidecarState` with a `HashMap<String, mpsc::UnboundedSender<Value>>` progress channel registry. The stdout event handler now checks for `type: "progress"` messages and routes them to the matching channel by `id` instead of broadcasting as global events. Non-progress messages continue through the existing `sidecar-response` event path, keeping `greet_sidecar` working unchanged.

Implemented `process_files` async Tauri command that takes `Vec<String>` paths and a `Channel<Value>`. For each path: generates a UUID, registers an mpsc channel, sends `process_file` to sidecar stdin, loops receiving progress events and forwarding through the Channel until a terminal stage arrives, then unregisters. Sidecar-not-running and send-failure cases produce error events through the Channel per-file without panicking.

Added `uuid` (v4) and `tokio` (sync feature) dependencies to Cargo.toml.

## Verification

- `cd src-tauri && cargo build` — compiles clean with zero warnings
- `cd backend && python3 -m pytest tests/test_sidecar.py -v` — 12 passed, 2 failed (pre-existing: `test_process_file_happy_path` and `test_process_file_output_path` fail due to PaddleOCR not installed in dev environment — same failures as T01)
- Code review: `greet_sidecar` path unchanged — non-progress messages still emit as `sidecar-response` global events
- Code review: sidecar-not-running produces error event per-file through Channel (no panic)
- Runtime verification (cargo tauri dev + browser console invocation) deferred to T03 where the full pipeline is wired end-to-end with UI

## Slice Verification Status

- ✅ `cd src-tauri && cargo build` — clean
- ⬜ `cd backend && python -m pytest tests/test_sidecar.py -v` — 12/14 pass (2 pre-existing failures from T01, environment-dependent)
- ⬜ `cargo tauri dev` → drop test image → `_ocr.pdf` appears (requires T03 UI)
- ⬜ Progress events stream to UI (requires T03)
- ⬜ Drop unsupported file → validation error (requires T03)
- ⬜ Drop multiple images → sequential processing (requires T03)

## Diagnostics

Inspect progress routing at runtime via Tauri console stderr:
```
[parsec] registered progress channel for id=<uuid>
[parsec] dispatching file path=<path> id=<uuid>
[parsec] routed progress for id=<uuid> stage=queued
[parsec] forwarding progress id=<uuid> stage=queued
[parsec] file complete id=<uuid>
[parsec] unregistered progress channel for id=<uuid>
```

Error cases produce Channel events with `stage: "error"` and descriptive `error` field.

## Deviations

- Added `tokio` dependency (sync feature only) for `tokio::sync::mpsc` — the existing `std::sync::mpsc` doesn't work well in async context (blocking recv). Tauri already uses tokio internally so this adds no new runtime.

## Known Issues

- Pre-existing: 2 sidecar tests fail due to PaddleOCR not being installed in the dev environment. These are environment-dependent, not code bugs.

## Files Created/Modified

- `src-tauri/src/sidecar.rs` — Extended SidecarState with progress channel registry, routing logic in stdout handler
- `src-tauri/src/lib.rs` — Added `process_files` Tauri command with Channel streaming, registered in invoke_handler
- `src-tauri/Cargo.toml` — Added `uuid` and `tokio` dependencies
