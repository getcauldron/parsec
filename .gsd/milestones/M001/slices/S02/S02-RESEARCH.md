# S02: Tauri Shell + Python Sidecar — Research

**Date:** 2026-03-12
**Updated:** 2026-03-12 (post-implementation revision with proven findings)

## Summary

S02 proved three things: (1) a Tauri v2 app scaffolded with Vanilla TypeScript launches and compiles, (2) a PyInstaller `--onedir` binary of the S01 backend spawns as a sidecar and runs correctly, and (3) bidirectional NDJSON communication works reliably over stdin/stdout with no buffering issues. All three risks from the roadmap — sidecar bundling, communication reliability, and integration plumbing — are retired.

The Tauri side was straightforward. The PyInstaller packaging required careful import collection (`--collect-all paddleocr`, `--collect-data paddle/scipy/shapely`) and produces a 652MB `--onedir` output. The critical insight was that PyInstaller binaries fully buffer stdout when spawned from a parent process — `sys.stdout.reconfigure(line_buffering=True)` at the top of the entrypoint (before any other imports) is mandatory, not optional.

The frontend framework decision was resolved: Vanilla TypeScript. The UI surface is minimal (status indicator + hello button for S02), and a framework can be introduced in S03 if the drop-zone UI warrants it. Vite dev server at port 1420 with HMR is the dev setup.

## Recommendation

The approach taken worked and is proven:
1. **Manual Tauri scaffold** (not `create-tauri-app`) to avoid conflicts with existing `backend/` directory (D020)
2. **Separated entrypoints**: `sidecar.py` for protocol logic (testable), `sidecar_entry.py` for PyInstaller-specific concerns (unbuffered stdout, paddle noise suppression)
3. **Dev-mode shell wrapper** at `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` that tries PyInstaller binary first, falls back to venv Python — keeps `cargo tauri dev` working without building PyInstaller
4. **Event-driven command/response**: Rust registers a one-shot listener, sends command to stdin, waits for response with 5s timeout via `mpsc` channel
5. **Sidecar lifecycle**: spawned in `setup()`, stored in `Mutex<Option<CommandChild>>`, killed on `WindowEvent::Destroyed`

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Sidecar spawning + stdin/stdout | `tauri-plugin-shell` v2 | Official API, handles target triple resolution, process lifecycle, permission scoping — proven working |
| Python→binary packaging | PyInstaller 6.19.0 `--onedir` | Works with Python 3.13 + PaddlePaddle 3.2.2 — `--onefile` is slower and breaks working directory assumptions |
| JSON line protocol | `json` stdlib + NDJSON | No external deps needed, one JSON object per line, works reliably |
| Build tooling | Vite + TypeScript | Standard Tauri v2 setup, port 1420, HMR works |

## Existing Code and Patterns

- `backend/parsec/sidecar.py` — NDJSON protocol handler. Forces `sys.stdout.reconfigure(line_buffering=True)` before any imports. Handles `hello`, `status`, unknown commands. All logging to stderr. Exits cleanly on stdin EOF or SIGTERM.
- `backend/parsec/sidecar_entry.py` — PyInstaller entrypoint. Sets `GLOG_minloglevel=3`, `FLAGS_minloglevel=3`, `PADDLE_LOG_LEVEL=ERROR`, `KMP_WARNINGS=0` to suppress PaddleOCR C++ noise, then calls `sidecar.main()`.
- `backend/build_sidecar.sh` — Reproducible PyInstaller build script with all `--collect-all` and `--hidden-import` flags. Single command to rebuild.
- `src-tauri/src/sidecar.rs` — Rust sidecar manager: `spawn_sidecar()`, `send_command()`, `kill_sidecar()`. Uses `Mutex<Option<CommandChild>>` managed state. Stdout parsed as JSON and emitted as `sidecar-response` events. Stderr forwarded with `[sidecar]` prefix.
- `src-tauri/src/lib.rs` — Tauri app setup. Shell plugin initialized. `greet_sidecar` command uses event-driven pattern (one-shot listener + mpsc + 5s timeout). Sidecar killed on window destroy.
- `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` — Shell wrapper that resolves project root by walking up directories. Tries PyInstaller binary first, falls back to venv Python.
- `src-tauri/build.rs` — Extended to copy sidecar binary with target-triple suffix (Tauri quirk: `tauri_build::build()` strips the triple but runtime expects it).
- `src/main.ts` — Frontend with status indicator (connecting/connected/disconnected/error) and greet button.
- `backend/tests/test_sidecar.py` — 9 subprocess-based protocol tests covering hello, status, unknown, malformed JSON, EOF, stdout purity, stderr logging.
- `backend/parsec/pipeline.py` — `process_file(input_path, output_path, options)` → `ProcessResult`. Not yet wired into the sidecar protocol (S03 scope).
- `backend/parsec/models.py` — `ProcessResult`, `OcrOptions`, `TextRegion` dataclasses. These form the JSON serialization boundary for S03.

## Constraints

- **Target triple naming**: Sidecar binary must be at `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin`. Tauri appends the triple automatically — `tauri.conf.json` `externalBin` uses just `binaries/parsec-sidecar`.
- **Capability permission name**: Uses `binaries/parsec-sidecar` with `sidecar: true` in `shell:allow-spawn`. May need adjustment for production bundling.
- **PyInstaller binary is 652MB**: PaddlePaddle alone is ~500MB. Acceptable for dev but will need stripping for distribution.
- **Python 3.13 + PyInstaller 6.19.0 + PaddlePaddle 3.2.2**: This specific combination works but is lightly tested in the community.
- **`--onedir` not `--onefile`**: `--onefile` extracts on every launch (5-10s overhead) and breaks working directory assumptions.
- **PaddleOCR stdout corruption**: PaddleOCR dumps C++ output during init/predict. Must suppress via env vars AND keep sidecar_entry.py as the PyInstaller entrypoint (not sidecar.py directly).
- **macOS code signing**: PyInstaller output has unsigned dylibs (paddle's libblas.dylib, liblapack.dylib with SDK version 0,0,0). Needs addressing for production distribution (M002 scope).

## Common Pitfalls

- **Stdout buffering in PyInstaller** — PyInstaller binaries ignore `PYTHONUNBUFFERED`. When spawned from Tauri, stdout is fully buffered — parent gets nothing until process exits. **Fix**: `sys.stdout.reconfigure(line_buffering=True)` as the very first thing in the entrypoint, before any other imports. Already solved in `sidecar_entry.py`.
- **Status event timing** — Sidecar `connected` event fires during Tauri `setup()` before frontend mounts its listener. **Fix**: 500ms delayed emit from a separate thread. Pragmatic solution; query-based approach would be more robust for production.
- **build.rs target-triple copy** — `tauri_build::build()` copies the sidecar without the target triple suffix, but runtime `sidecar()` looks for `parsec-sidecar-{target_triple}`. **Fix**: build.rs copies with correct suffix. Already solved.
- **sidecar() name resolution** — Use `shell.sidecar("parsec-sidecar")` not `shell.sidecar("binaries/parsec-sidecar")`. Tauri resolves the `binaries/` prefix from `externalBin` config.
- **PaddleOCR hidden imports** — PyInstaller misses many deps. Working recipe in `build_sidecar.sh`: `--collect-all paddleocr/pyclipper/skimage/imgaug/lmdb`, `--collect-data paddle/scipy/shapely`, plus explicit `--hidden-import` for PIL, cv2, yaml, requests, tqdm, packaging, and all parsec modules.

## Open Risks

- **Full OCR inference through PyInstaller binary untested** — S02 proved hello/status protocol commands work. Actual `process_file()` through the PyInstaller binary (PaddleOCR model loading, inference, OCRmyPDF PDF generation) has not been tested. This is S03's first integration risk.
- **ocrmypdf-paddleocr plugin in PyInstaller** — The plugin does dynamic imports that PyInstaller may not detect. The `--hidden-import` list may need expansion when S03 wires `process_file`.
- **Binary size for distribution** — 652MB is large. Need to strip unused modules, investigate UPX compression effectiveness, or consider download-on-demand for PaddlePaddle models.
- **500ms connected delay** — If frontend takes longer than 500ms to load, it misses the status event. Should be replaced with a query-based approach (frontend asks for status on mount) in S03.
- **Orphan process risk** — Sidecar is killed on `WindowEvent::Destroyed`, but if the app crashes without firing that event, the sidecar may be orphaned. Need a health-check mechanism or PID file.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Tauri v2 | `nodnarbnitram/claude-code-extensions@tauri-v2` | available (2.3K installs) — covers Tauri v2 patterns, commands, plugins |
| Tauri v2 | `martinholovsky/claude-skills-generator@tauri` | available (233 installs) |
| PyInstaller | none found | no skills on skills.sh |

## Sources

- Tauri v2 sidecar API: `spawn()`, `CommandEvent::Stdout`, `child.write()` pattern (source: [Tauri v2 Sidecar Docs](https://v2.tauri.app/develop/sidecar/))
- Sidecar binary must be named with target triple suffix, e.g. `parsec-sidecar-aarch64-apple-darwin` (source: [Tauri v2 Sidecar Docs](https://v2.tauri.app/develop/sidecar/))
- Shell plugin permissions require `shell:allow-spawn` with `sidecar: true` in capabilities JSON (source: [Tauri v2 Shell Plugin](https://v2.tauri.app/plugin/shell/))
- PyInstaller binaries do not respect PYTHONUNBUFFERED; stdout is fully buffered when spawned from parent process (source: [PyInstaller Issue #8426](https://github.com/pyinstaller/pyinstaller/issues/8426))
- PyInstaller + PaddleOCR needs extensive `--collect-all` flags (source: [PaddleOCR Discussion #6875](https://github.com/PaddlePaddle/PaddleOCR/discussions/6875))
- Tauri v2 shell plugin requires `shell:allow-spawn` for long-lived sidecar processes, `shell:allow-execute` is for short-lived commands (source: [Tauri v2 Shell Plugin Docs via Context7](https://github.com/tauri-apps/tauri-docs))
