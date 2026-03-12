# S02: Tauri Shell + Python Sidecar

**Goal:** A Tauri v2 desktop app spawns the Python OCR backend as a sidecar process, and bidirectional JSON communication over stdin/stdout is proven.
**Demo:** Launch the Tauri app → it spawns the Python sidecar → sends `{"cmd": "hello"}` → receives `{"status": "ok", ...}` → displays the result in the window.

## Must-Haves

- Tauri v2 app scaffolded with Vanilla TypeScript, launches a window
- Python sidecar protocol handler (`backend/parsec/sidecar.py`) reads newline-delimited JSON from stdin, dispatches commands, writes JSON responses to stdout
- Rust sidecar manager spawns the Python process, sends commands to stdin, receives responses from stdout
- `tauri-plugin-shell` configured with correct capabilities for sidecar spawning
- Dev-mode shell wrapper script so `cargo tauri dev` works without PyInstaller
- PyInstaller `--onedir` binary of the backend runs identically to the unbundled Python
- Hello-world JSON exchange proven through Tauri → sidecar → Tauri roundtrip
- PaddleOCR stdout noise does not corrupt JSON protocol

## Proof Level

- This slice proves: integration (Tauri ↔ Python sidecar communication)
- Real runtime required: yes (Tauri app must launch, sidecar must spawn)
- Human/UAT required: no (JSON exchange is machine-verifiable)

## Verification

- `cd backend && python -c "from parsec.sidecar import main; print('import ok')"` — sidecar module loads
- `echo '{"cmd":"hello"}' | python -u backend/parsec/sidecar.py` — prints valid JSON with `status: "ok"`
- `cd src-tauri && cargo build` — Tauri app compiles
- `cargo tauri dev` — app window opens, sidecar spawns, hello exchange completes (manual verification during T02)
- PyInstaller binary: `echo '{"cmd":"hello"}' | src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` — identical JSON output to unbundled version
- `cd backend && python -m pytest tests/test_sidecar.py -v` — sidecar protocol unit tests pass

## Observability / Diagnostics

- Runtime signals: sidecar writes `{"type":"log","level":"info",...}` events to stderr (not stdout — stdout is reserved for protocol). Rust side logs sidecar lifecycle events via `tracing` or `log`.
- Inspection surfaces: sidecar responds to `{"cmd":"status"}` with process uptime and engine readiness
- Failure visibility: sidecar wraps all errors in `{"status":"error","error":"..."}` JSON — never crashes silently. Rust side detects sidecar exit and surfaces the exit code.
- Redaction constraints: none (no secrets in sidecar protocol)

## Integration Closure

- Upstream surfaces consumed: `backend/parsec/models.py` (ProcessResult, OcrOptions for JSON serialization), `backend/parsec/pipeline.py` (process_file — wired but not exercised until S03)
- New wiring introduced: Tauri app lifecycle → sidecar spawn/kill, frontend ↔ Rust commands ↔ sidecar stdin/stdout
- What remains before milestone is truly usable end-to-end: S03 wires file drop → process_file through the sidecar, S04 adds language settings, S05 adds PDF input + preprocessing

## Tasks

- [x] **T01: Scaffold Tauri v2 app and write Python sidecar protocol** `est:2h`
  - Why: Creates both sides of the integration boundary — a launchable Tauri app and a Python stdin/stdout JSON protocol handler — so T02 can wire them together
  - Files: `src-tauri/`, `src/`, `package.json`, `backend/parsec/sidecar.py`, `backend/tests/test_sidecar.py`
  - Do: Install tauri-cli. Scaffold Tauri v2 app with `pnpm create tauri-app` (Vanilla TS). Install `tauri-plugin-shell`. Write `sidecar.py` with line-buffered stdout, stderr for logging, `hello` and `status` command handlers, PaddleOCR noise suppression. Write unit tests for the protocol.
  - Verify: `cargo build` in src-tauri succeeds. `echo '{"cmd":"hello"}' | python -u backend/parsec/sidecar.py` returns valid JSON. `pytest tests/test_sidecar.py` passes.
  - Done when: Tauri app compiles and shows a window. Sidecar protocol handles hello/status/unknown commands correctly with unit tests passing.

- [x] **T02: Wire Rust sidecar manager and prove hello-world JSON exchange** `est:2h`
  - Why: The core integration proof — Tauri spawns the sidecar, sends a command, receives a response, and displays it. This retires the "sidecar communication reliability" risk from the roadmap.
  - Files: `src-tauri/src/lib.rs`, `src-tauri/src/sidecar.rs`, `src-tauri/capabilities/default.json`, `src-tauri/tauri.conf.json`, `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin`, `src/main.ts`, `src/index.html`
  - Do: Create dev-mode shell wrapper script at correct binary path. Configure `externalBin` in tauri.conf.json and shell permissions in capabilities. Write `sidecar.rs` — spawn sidecar on app start, send hello command, receive response via CommandEvent::Stdout. Expose a Tauri command to frontend. Update frontend to invoke the command and display the result.
  - Verify: `cargo tauri dev` launches app, spawns sidecar, and displays the hello response in the window. Closing the app kills the sidecar (no orphan processes).
  - Done when: Full roundtrip Tauri → sidecar → Tauri proven. Dev-mode workflow is smooth — `cargo tauri dev` just works.

- [x] **T03: Build PyInstaller binary and verify identical sidecar behavior** `est:2h`
  - Why: Retires the "Python sidecar bundling" risk — the hardest integration problem in the roadmap. Proves the packaged binary works identically to the unbundled Python, including stdout buffering behavior.
  - Files: `backend/parsec/sidecar_entry.py`, `backend/parsec.spec` (or `build_sidecar.py`), `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin`
  - Do: Create PyInstaller entrypoint with unbuffered stdout setup before any imports. Build `--onedir` binary with `--collect-all` flags for paddleocr and dependencies. Replace dev wrapper with the real binary. Test hello command, verify stdout is not buffered (response appears immediately, not on exit). Test that `cargo tauri dev` still works with the PyInstaller binary.
  - Verify: `echo '{"cmd":"hello"}' | src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` returns valid JSON immediately. `cargo tauri dev` spawns the PyInstaller binary and completes the hello exchange. Binary size is documented.
  - Done when: PyInstaller binary produces identical JSON output to unbundled Python. Tauri can spawn the binary and exchange messages. Stdout buffering is confirmed solved.

## Files Likely Touched

- `package.json` — pnpm workspace root with Tauri deps
- `src/index.html` — minimal frontend shell
- `src/main.ts` — frontend JS invoking Tauri commands
- `src-tauri/Cargo.toml` — Rust dependencies
- `src-tauri/tauri.conf.json` — app config, externalBin, window settings
- `src-tauri/capabilities/default.json` — shell plugin permissions
- `src-tauri/src/lib.rs` — Tauri app setup, command registration
- `src-tauri/src/sidecar.rs` — Rust sidecar manager
- `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` — sidecar binary (wrapper then real)
- `backend/parsec/sidecar.py` — Python JSON protocol handler
- `backend/parsec/sidecar_entry.py` — PyInstaller entrypoint
- `backend/tests/test_sidecar.py` — sidecar protocol unit tests
