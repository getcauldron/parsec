---
estimated_steps: 5
estimated_files: 8
---

# T01: Scaffold Tauri v2 app and write Python sidecar protocol

**Slice:** S02 — Tauri Shell + Python Sidecar
**Milestone:** M001

## Description

Creates both halves of the integration boundary. On the Rust side: scaffold a Tauri v2 app using the Vanilla TypeScript template with `tauri-plugin-shell` installed. On the Python side: write `sidecar.py` — a stdin/stdout JSON protocol handler that the sidecar will run. The two halves are independent at this point; T02 wires them together.

The sidecar protocol is newline-delimited JSON (NDJSON). The sidecar reads one JSON object per line from stdin, dispatches by `cmd` field, writes one JSON response per line to stdout. Stderr is reserved for logging — never protocol messages. Stdout must be line-buffered from the very first byte to prevent buffering issues when spawned by Tauri or PyInstaller.

## Steps

1. Install `tauri-cli` via cargo: `cargo install tauri-cli --locked`.
2. Scaffold Tauri v2 app with `pnpm create tauri-app` using Vanilla TypeScript template. Resolve any conflicts with existing `backend/` directory (the scaffolder creates project files at the root). Install `@tauri-apps/plugin-shell` (frontend) and `tauri-plugin-shell` (Rust).
3. Verify the scaffolded app compiles and launches: `cargo tauri dev` should show a window (may need to kill after confirming).
4. Write `backend/parsec/sidecar.py`:
   - Force unbuffered stdout immediately: `sys.stdout.reconfigure(line_buffering=True)` before any other imports.
   - Suppress PaddleOCR stdout noise using the pattern from `paddle_engine.py` (redirect stdout/stderr to devnull during import).
   - Main loop: read lines from stdin, parse as JSON, dispatch by `cmd` field.
   - Commands: `hello` → `{"status":"ok","message":"parsec sidecar ready","version":"0.1.0"}`, `status` → `{"status":"ok","uptime_seconds":...,"engine_ready":false}`, unknown → `{"status":"error","error":"unknown command: ..."}`.
   - All responses are single-line JSON written to stdout with flush.
   - Logging goes to stderr via the `logging` module.
   - Graceful shutdown on stdin EOF or SIGTERM.
5. Write `backend/tests/test_sidecar.py`:
   - Test hello command returns expected response shape.
   - Test status command returns uptime and engine_ready fields.
   - Test unknown command returns error response.
   - Test malformed JSON input produces error response without crashing.
   - Test stdin EOF causes clean exit.
   - Use subprocess to test the actual sidecar process (not just unit-test the dispatch function) — this catches buffering issues.

## Must-Haves

- [ ] Tauri v2 app compiles with `cargo build` in `src-tauri/`
- [ ] `tauri-plugin-shell` is in Cargo.toml dependencies and initialized in app setup
- [ ] `sidecar.py` forces line-buffered stdout before any imports
- [ ] `sidecar.py` handles `hello`, `status`, and unknown commands correctly
- [ ] `sidecar.py` never writes non-JSON to stdout (logging → stderr only)
- [ ] `test_sidecar.py` exercises the protocol via subprocess and passes

## Verification

- `cd src-tauri && cargo build` — compiles without errors
- `echo '{"cmd":"hello"}' | python -u backend/parsec/sidecar.py` — returns `{"status":"ok",...}`
- `echo '{"cmd":"status"}' | python -u backend/parsec/sidecar.py` — returns `{"status":"ok","uptime_seconds":...}`
- `echo 'garbage' | python -u backend/parsec/sidecar.py` — returns `{"status":"error",...}`
- `cd backend && python -m pytest tests/test_sidecar.py -v` — all tests pass

## Inputs

- `backend/parsec/models.py` — ProcessResult, OcrOptions dataclasses (needed for future serialization, referenced but not deeply used yet)
- `backend/parsec/paddle_engine.py` — stdout suppression pattern to reuse
- S02 research — Tauri v2 scaffold commands, plugin installation, sidecar constraints

## Expected Output

- `package.json` — root package with Tauri dev dependencies
- `src/index.html`, `src/main.ts`, `src/styles.css` — minimal frontend scaffold
- `src-tauri/Cargo.toml` — Rust project with tauri + shell plugin deps
- `src-tauri/tauri.conf.json` — app configuration
- `src-tauri/src/lib.rs` — Tauri app entry with shell plugin
- `backend/parsec/sidecar.py` — JSON protocol handler
- `backend/tests/test_sidecar.py` — protocol unit tests
