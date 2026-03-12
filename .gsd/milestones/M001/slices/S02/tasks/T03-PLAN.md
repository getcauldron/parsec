---
estimated_steps: 5
estimated_files: 4
---

# T03: Build PyInstaller binary and verify identical sidecar behavior

**Slice:** S02 — Tauri Shell + Python Sidecar
**Milestone:** M001

## Description

Retires the highest-risk item in the M001 roadmap: packaging PaddleOCR + OCRmyPDF + the sidecar protocol into a standalone binary that Tauri can spawn. Uses PyInstaller `--onedir` mode (D006). The key concerns from research are: stdout buffering corruption, hidden imports for PaddleOCR/PaddlePaddle, and potential performance degradation.

The approach: create a dedicated entrypoint script that configures unbuffered stdout before any imports, build with extensive `--collect-all` flags, then verify the binary produces identical protocol output to the unbundled Python. If the binary works with `echo '{"cmd":"hello"}'`, swap the dev wrapper for the real binary and re-verify through Tauri.

## Steps

1. Create `backend/parsec/sidecar_entry.py` — a thin entrypoint for PyInstaller:
   - First line after shebang: reconfigure stdout to line-buffered (`sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)`)
   - Then suppress PaddleOCR C++ noise (redirect stdout/stderr to devnull during paddle imports)
   - Then call `sidecar.main()`
   - This separation from `sidecar.py` keeps the protocol handler importable for tests while giving PyInstaller a clean entrypoint.
2. Create the PyInstaller build script (`backend/build_sidecar.sh` or `backend/build_sidecar.py`):
   - Use `--onedir` mode (not `--onefile` — per D006 and research)
   - `--name parsec-sidecar`
   - `--collect-all paddleocr --collect-all pyclipper --collect-all skimage --collect-all imgaug --collect-all scipy.io --collect-all lmdb`
   - `--collect-data paddle`
   - Additional hidden imports as discovered during iterative debugging
   - Output to `backend/dist/parsec-sidecar/`
3. Build the binary, iterate on hidden imports until `echo '{"cmd":"hello"}' | backend/dist/parsec-sidecar/parsec-sidecar` returns valid JSON.
4. Verify stdout buffering is solved: the response must appear immediately when input is piped, not buffered until exit. Test with a short timeout to catch buffering: `timeout 5 bash -c 'echo "{\"cmd\":\"hello\"}" | backend/dist/parsec-sidecar/parsec-sidecar'` must succeed (if buffered, it would hang waiting for more input or exit).
5. Replace the dev wrapper script with a symlink or copy to the PyInstaller binary at `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin`. Run `cargo tauri dev` and verify the hello exchange still works through the Tauri UI. Document the binary size.

## Must-Haves

- [ ] PyInstaller `--onedir` binary builds without errors
- [ ] `echo '{"cmd":"hello"}'` piped to the binary returns valid JSON with `status: "ok"`
- [ ] Response is immediate (not buffered until process exit)
- [ ] PaddleOCR C++ noise does not appear in stdout (would corrupt JSON protocol)
- [ ] Binary works when spawned by Tauri via `cargo tauri dev`
- [ ] Binary size documented (expected: large due to PaddlePaddle, but needs to be known)

## Verification

- `echo '{"cmd":"hello"}' | backend/dist/parsec-sidecar/parsec-sidecar` — returns `{"status":"ok",...}`
- `timeout 5 bash -c 'echo "{\"cmd\":\"hello\"}" | backend/dist/parsec-sidecar/parsec-sidecar'` — exits 0 (not timeout)
- `echo '{"cmd":"hello"}' | src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` — same output
- `cargo tauri dev` — hello exchange works through the Tauri UI with the PyInstaller binary
- `du -sh backend/dist/parsec-sidecar/` — binary size documented in task summary

## Inputs

- `backend/parsec/sidecar.py` — protocol handler from T01
- `backend/parsec/paddle_engine.py` — stdout suppression pattern
- `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` — dev wrapper from T02 (will be replaced)
- S02 research — PyInstaller flags, known pitfalls, buffering fixes

## Expected Output

- `backend/parsec/sidecar_entry.py` — PyInstaller entrypoint with unbuffered stdout
- `backend/build_sidecar.sh` — reproducible build script for the PyInstaller binary
- `backend/dist/parsec-sidecar/` — the `--onedir` output (gitignored)
- `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` — updated to point at/be the PyInstaller binary
