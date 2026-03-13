---
estimated_steps: 5
estimated_files: 4
---

# T02: Wire Rust process_files command with Channel streaming and sequential dispatch

**Slice:** S03 — Drop-and-Go Pipeline
**Milestone:** M001

## Description

Replace the S02 one-shot event pattern with a request-ID–correlated dispatch system. The new `process_files` Tauri command receives file paths and a `Channel<Value>`, generates a UUID per file, sends `process_file` commands to the sidecar one at a time (sequential — PaddleOCR is single-threaded), and forwards all progress events from sidecar stdout through the Channel back to the frontend. The existing global `sidecar-response` event broadcast is replaced with a targeted routing mechanism: stdout events with a `type: "progress"` field get routed to a registered channel by their `id`, while non-progress responses (hello, status) continue working via the existing event pattern.

## Steps

1. Add `uuid` crate to `Cargo.toml` with `v4` feature for request-ID generation.
2. Extend `SidecarState` in `sidecar.rs` with a progress channel registry: `HashMap<String, mpsc::Sender<Value>>` (or `tokio::sync::mpsc`) protected by a Mutex. When stdout receives a JSON object with `type: "progress"`, look up the `id` in the registry and forward through that sender. Non-progress messages continue as global `sidecar-response` events. This lets `greet_sidecar` keep working unchanged.
3. Add helper methods to `SidecarState` or `sidecar.rs`: `register_channel(id, sender)` and `unregister_channel(id)`. These are called from the Tauri command to set up routing before sending a `process_file` command.
4. Implement `process_files` async Tauri command:
   - Takes `paths: Vec<String>` and `channel: Channel<Value>` parameters
   - For each path sequentially: generate UUID, register an `mpsc::channel`, send `{"cmd":"process_file","id":"<uuid>","input_path":"<path>"}` to sidecar stdin, loop receiving from the mpsc channel and forwarding each event through `channel.send()`, until a `complete` or `error` stage arrives, then unregister
   - If the sidecar is not running, send an error event through the Channel for each file
   - Return `Ok(())` on completion (all progress is streamed, not returned)
5. Register `process_files` in the `invoke_handler` in `lib.rs`. Keep `greet_sidecar` registered too — it still works via the global event path.

## Must-Haves

- [ ] `process_files` Tauri command accepts file paths and a Channel
- [ ] Files dispatched to sidecar sequentially (one at a time)
- [ ] Progress events routed from sidecar stdout to the correct Channel by request ID
- [ ] `greet_sidecar` command still works (non-progress events unaffected)
- [ ] Sidecar-not-running errors produce error events through Channel (no panic)
- [ ] `cargo build` in `src-tauri/` compiles clean with no warnings

## Verification

- `cd src-tauri && cargo build` — compiles clean
- `cargo tauri dev` → browser console: `await window.__TAURI__.core.invoke('greet_sidecar')` still returns hello response
- `cargo tauri dev` → invoke `process_files` from console with a test fixture path → progress events arrive in the Channel callback, `_ocr.pdf` file created

## Observability Impact

- Signals added: `eprintln!` logging for channel registration/unregistration, progress event routing, and dispatch errors
- How a future agent inspects this: Tauri console stderr shows `[parsec] routing progress for <id>`, `[parsec] dispatching file <path>`, `[parsec] file complete/error`
- Failure state exposed: Channel receives `{"type":"progress","stage":"error","error":"..."}` for both sidecar errors and sidecar-not-running

## Inputs

- `src-tauri/src/sidecar.rs` — existing spawn/send/kill with global event broadcast
- `src-tauri/src/lib.rs` — existing `greet_sidecar` command and app setup
- T01 output: sidecar `process_file` command with progress events and request-ID correlation

## Expected Output

- `src-tauri/src/sidecar.rs` — extended with channel registry and progress event routing
- `src-tauri/src/lib.rs` — new `process_files` command registered alongside `greet_sidecar`
- `src-tauri/Cargo.toml` — `uuid` dependency added
- Proven: Rust dispatches files to sidecar and streams progress events through a typed Channel
