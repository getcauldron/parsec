---
id: T01
parent: S02
milestone: M001
provides:
  - Tauri v2 app scaffold with shell plugin (compiles and produces binary)
  - Python sidecar NDJSON protocol handler with hello/status/unknown commands
  - Subprocess-based test suite for sidecar protocol
key_files:
  - src-tauri/Cargo.toml
  - src-tauri/src/lib.rs
  - src-tauri/tauri.conf.json
  - src-tauri/capabilities/default.json
  - backend/parsec/sidecar.py
  - backend/tests/test_sidecar.py
key_decisions:
  - D020: Manual Tauri scaffold instead of `pnpm create tauri-app` to avoid conflicts with existing backend/ directory
patterns_established:
  - Sidecar NDJSON protocol: one JSON object per line on stdin, one JSON response per line on stdout, logging to stderr only
  - Line-buffered stdout via sys.stdout.reconfigure(line_buffering=True) before any imports
  - _send() helper writes compact JSON + newline + flush for every response
observability_surfaces:
  - sidecar responds to {"cmd":"status"} with uptime_seconds and engine_ready
  - sidecar logs lifecycle events (start, shutdown, errors) to stderr via logging module
  - all errors wrapped in {"status":"error","error":"..."} — never crashes silently
duration: 15m
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T01: Scaffold Tauri v2 app and write Python sidecar protocol

**Built both halves of the Tauri ↔ Python integration boundary: a compiling Tauri v2 app with shell plugin, and a tested NDJSON sidecar protocol handler.**

## What Happened

Created the Tauri v2 app structure manually (package.json, vite.config.ts, index.html, src-tauri/) rather than using the interactive `pnpm create tauri-app` scaffolder, which would conflict with the existing `backend/` directory. Installed `tauri-plugin-shell` (Rust) and `@tauri-apps/plugin-shell` (JS). Shell plugin is initialized in `lib.rs` and capabilities are configured for sidecar spawning.

Wrote `backend/parsec/sidecar.py` — a stdin/stdout NDJSON protocol handler. Forces `sys.stdout.reconfigure(line_buffering=True)` as the very first thing after `import sys` to prevent buffering issues in PyInstaller binaries. Handles `hello`, `status`, and unknown commands. All logging goes to stderr via the `logging` module — stdout is reserved exclusively for protocol JSON. Handles graceful shutdown on stdin EOF and SIGTERM.

Wrote `backend/tests/test_sidecar.py` with 9 tests exercising the protocol via subprocess (not unit-testing the dispatch function directly). This catches real buffering issues. Tests cover: hello, status, unknown command, malformed JSON, non-object JSON, multiple commands in sequence, clean exit on EOF, no non-JSON on stdout, and logging goes to stderr.

## Verification

- `cd src-tauri && cargo build` — ✅ compiles, produces 30MB debug binary
- `echo '{"cmd":"hello"}' | python -u backend/parsec/sidecar.py` — ✅ returns `{"status":"ok","message":"parsec sidecar ready","version":"0.1.0"}`
- `echo '{"cmd":"status"}' | python -u backend/parsec/sidecar.py` — ✅ returns `{"status":"ok","uptime_seconds":0.0,"engine_ready":false}`
- `echo 'garbage' | python -u backend/parsec/sidecar.py` — ✅ returns `{"status":"error","error":"invalid JSON: ..."}`
- `cd backend && python -m pytest tests/test_sidecar.py -v` — ✅ 9/9 tests pass
- `cd backend && python -c "from parsec.sidecar import main; print('import ok')"` — ✅ sidecar module loads

Slice-level checks not yet applicable (T02/T03 scope):
- ⬜ `cargo tauri dev` — T02
- ⬜ PyInstaller binary — T03

## Diagnostics

- Test the protocol: `echo '{"cmd":"hello"}' | backend/.venv/bin/python -u backend/parsec/sidecar.py`
- Run tests: `cd backend && .venv/bin/python -m pytest tests/test_sidecar.py -v`
- Verify Rust compiles: `cd src-tauri && cargo build`
- Sidecar logs appear on stderr (startup, shutdown, signal handling)

## Deviations

- Used manual scaffold instead of `pnpm create tauri-app` — the interactive scaffolder would overwrite the root and conflict with the existing `backend/` directory. Created equivalent files directly.
- Placed `index.html` at project root (Vite convention) rather than in `src/` as listed in the task plan's expected output.

## Known Issues

None.

## Files Created/Modified

- `package.json` — pnpm workspace root with Tauri + Vite + shell plugin deps
- `tsconfig.json` — TypeScript configuration
- `vite.config.ts` — Vite dev server config for Tauri (port 1420, HMR)
- `.npmrc` — pnpm build configuration
- `index.html` — minimal frontend shell (at root, Vite convention)
- `src/main.ts` — frontend JS placeholder
- `src/styles.css` — base styles with dark mode support
- `src-tauri/Cargo.toml` — Rust deps: tauri, tauri-plugin-shell, serde, serde_json
- `src-tauri/build.rs` — Tauri build script
- `src-tauri/tauri.conf.json` — app config with Vite dev URL, window settings
- `src-tauri/capabilities/default.json` — shell plugin permissions for sidecar spawning
- `src-tauri/src/lib.rs` — Tauri app entry with shell plugin initialization
- `src-tauri/src/main.rs` — binary entry point
- `src-tauri/icons/` — generated placeholder icons (all sizes)
- `backend/parsec/sidecar.py` — NDJSON protocol handler
- `backend/tests/test_sidecar.py` — 9 protocol tests via subprocess
