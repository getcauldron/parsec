---
id: T02
parent: S02
milestone: M001
provides:
  - Rust sidecar manager (spawn, send, kill) with managed state
  - Dev-mode wrapper script that resolves venv Python automatically
  - Frontend with button, status display, and sidecar response rendering
  - Full Tauri → Python sidecar → Tauri hello-world JSON roundtrip
  - build.rs fix for target-triple sidecar binary naming
key_files:
  - src-tauri/src/sidecar.rs
  - src-tauri/src/lib.rs
  - src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin
  - src-tauri/build.rs
  - src/main.ts
  - index.html
key_decisions:
  - "sidecar() name: use just 'parsec-sidecar' not 'binaries/parsec-sidecar' — Tauri resolves the binaries/ prefix from externalBin config"
  - "Delayed connected emit: 500ms delay before emitting sidecar-status connected, so frontend event listener has time to mount"
  - "build.rs copies sidecar binary with target-triple suffix — tauri_build strips the triple but runtime needs it"
  - "Capability name uses binaries/ prefix: 'binaries/parsec-sidecar' in shell:allow-spawn permission"
patterns_established:
  - "Event-driven command/response: greet_sidecar registers a one-shot listener, sends command to stdin, waits for response with 5s timeout via mpsc channel"
  - "Sidecar lifecycle: spawned in setup(), stored in Mutex<Option<CommandChild>>, killed on WindowEvent::Destroyed"
  - "Dev wrapper script uses walk-up search for project root — works from both src-tauri/binaries/ and target/debug/"
observability_surfaces:
  - "eprintln! for sidecar spawn/kill/terminate events with PID and exit codes"
  - "Frontend status indicator: connecting/connected/disconnected/error states"
  - "Sidecar stderr forwarded to Tauri console with [sidecar] prefix"
  - "Sidecar event errors logged with [parsec] prefix"
duration: 1h
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T02: Wire Rust sidecar manager and prove hello-world JSON exchange

**Full Tauri ↔ Python sidecar roundtrip proven: app spawns sidecar, sends hello command, receives JSON response, displays it in the window.**

## What Happened

Created the dev-mode wrapper script that walks up the directory tree to find the project root (works from both source and target locations). Configured `externalBin` in tauri.conf.json. Wrote `sidecar.rs` with spawn/send/kill functions using `Mutex<Option<CommandChild>>` managed state. Wired into `lib.rs` with a `greet_sidecar` Tauri command that uses an event-driven pattern (one-shot listener + mpsc channel + 5s timeout). Built the frontend with status indicator and response display.

Hit two issues during integration:
1. **Sidecar binary path resolution** — Tauri's build system copies the sidecar to `target/debug/parsec-sidecar` (without target triple), but at runtime `sidecar()` looks for `parsec-sidecar-aarch64-apple-darwin`. Fixed by adding a build.rs step that copies with the triple suffix.
2. **Status event timing** — The `sidecar-status: connected` event fired during `setup()` before the frontend loaded its listener. Fixed with a 500ms delayed emit from a separate thread.

Both fixes are durable — the build.rs approach handles future rebuilds automatically, and the delayed emit is a standard pattern for Tauri event timing.

## Verification

- `cargo build` in src-tauri — compiles clean, no warnings
- `pnpm build` — TypeScript and Vite build succeed
- `cargo tauri dev` — app window opens, sidecar spawns, status shows "✅ Sidecar connected"
- Button click shows `{"message": "parsec sidecar ready", "status": "ok", "version": "0.1.0"}` in the window
- App close kills sidecar — `pgrep -f sidecar.py` returns empty after app exit
- Dev wrapper script: `echo '{"cmd":"hello"}' | src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` returns valid JSON

Slice-level checks:
- ✅ `cd backend && python -c "from parsec.sidecar import main; print('import ok')"` — passes
- ✅ `echo '{"cmd":"hello"}' | python -u backend/parsec/sidecar.py` — valid JSON with status ok
- ✅ `cd src-tauri && cargo build` — compiles
- ✅ `cargo tauri dev` — app + sidecar + hello exchange works
- ⬜ PyInstaller binary test — T03 scope
- ✅ `pytest tests/test_sidecar.py -v` — 9/9 pass

## Diagnostics

- `cargo tauri dev` console shows `[parsec] sidecar spawned (pid: N)` on startup
- Sidecar stderr appears with `[sidecar]` prefix in console
- `[parsec] sidecar terminated (code: N, signal: N)` on exit
- Frontend shows connecting/connected/disconnected/error status
- If sidecar dies, frontend shows "❌ Sidecar disconnected" automatically

## Deviations

- **build.rs extended** — Plan didn't anticipate the need for a build.rs step to copy the sidecar binary with the target-triple suffix. This is a Tauri v2 quirk where `tauri_build::build()` strips the triple during copy but the runtime API expects it.
- **Delayed status emit** — Added 500ms delay for connected status event (not in plan). Standard Tauri pattern for setup → frontend event timing.

## Known Issues

- The 500ms delay for connected status is a pragmatic solution. If the frontend takes longer than 500ms to load, it could miss the event. For production, a query-based approach (frontend asks for current status on mount) would be more robust. Not worth overengineering for this proof-of-concept.
- The capability permission name includes `binaries/` prefix (`binaries/parsec-sidecar`) — if this doesn't match what Tauri expects at production bundle time, it may need adjustment in T03.

## Files Created/Modified

- `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` — dev-mode bash wrapper, walks up to find venv Python
- `src-tauri/src/sidecar.rs` — Rust sidecar manager: spawn, send, kill, event handling
- `src-tauri/src/lib.rs` — Tauri app setup with sidecar lifecycle, greet_sidecar command
- `src-tauri/build.rs` — Extended to copy sidecar binary with target-triple suffix
- `src-tauri/tauri.conf.json` — Added `externalBin` configuration
- `src-tauri/capabilities/default.json` — Updated permission name to `binaries/parsec-sidecar`
- `index.html` — Added button, status element, response display
- `src/main.ts` — Frontend: Tauri event listeners, greet_sidecar invocation, status management
- `src/styles.css` — Added button, pre, and status styles
