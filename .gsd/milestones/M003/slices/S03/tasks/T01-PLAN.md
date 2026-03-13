---
estimated_steps: 5
estimated_files: 3
---

# T01: Create cross-platform sidecar build script and fix build.rs for Windows

**Slice:** S03 — Cross-Platform Release Workflow
**Milestone:** M003

## Description

Replace the bash-only `build_sidecar.sh` with a cross-platform Python script (`build_sidecar.py`) that works in CI on macOS, Windows, and Linux. Fix `build.rs` to handle the `.exe` suffix on Windows targets. Add platform-conditional bundle config to `tauri.conf.json` for `_internal/` placement on Windows and Linux.

The bash script stays for local dev convenience — `build_sidecar.py` is the CI-facing equivalent.

## Steps

1. **Read `build_sidecar.sh` and extract every PyInstaller flag.** Catalog all `--hidden-import`, `--collect-all`, `--collect-data`, `--copy-metadata` flags, the entry point, and the `--name`/`--onedir`/`--noconfirm`/`--clean`/`--log-level` options. These must be replicated exactly.

2. **Write `backend/build_sidecar.py`.** Use `argparse` for a `--help` flag. Use `pathlib.Path` for all paths. Use `subprocess.run` to invoke `python -m PyInstaller` (system Python, no venv assumption). Detect platform with `sys.platform`. On Windows, verify the output binary has `.exe` extension. Add `--dry-run` flag that prints the command without executing (useful for CI debugging). Print summary at end (output path, size).

3. **Fix `src-tauri/build.rs` for Windows `.exe` suffix.** When `target_triple` contains `windows`, the source binary path must include `.exe` and the destination sidecar name must include `.exe`. Tauri's `externalBin` system expects `parsec-sidecar-x86_64-pc-windows-msvc.exe` on Windows.

4. **Add platform bundle config to `tauri.conf.json`.** Add `bundle.windows` with `resources` map: `{"../backend/dist/parsec-sidecar/_internal/**/*": "_internal/"}` to place `_internal/` adjacent to the sidecar in the install directory. Add `bundle.linux` with matching `resources` config. Keep existing `bundle.macOS.files` untouched (proven in M002).

5. **Verify.** Run `python3 backend/build_sidecar.py --help` and `--dry-run`. Run `cd src-tauri && cargo check`. Validate `tauri.conf.json` is valid JSON with the expected structure.

## Must-Haves

- [ ] `build_sidecar.py` replicates every PyInstaller flag from `build_sidecar.sh` — no flags dropped
- [ ] `build_sidecar.py` uses `pathlib` / `os.path` (no hardcoded `/` separators)
- [ ] `build_sidecar.py` works without a venv — uses `sys.executable` or `python -m PyInstaller`
- [ ] `build.rs` appends `.exe` on Windows targets for both source and destination paths
- [ ] `tauri.conf.json` has `bundle.windows` and `bundle.linux` config for `_internal/` placement
- [ ] Existing `bundle.macOS.files` is untouched

## Verification

- `python3 backend/build_sidecar.py --help` exits 0
- `python3 backend/build_sidecar.py --dry-run` prints the full PyInstaller command without executing
- `cd src-tauri && cargo check` passes
- `python3 -c "import json; c=json.load(open('src-tauri/tauri.conf.json')); assert 'windows' in c['bundle']; assert 'linux' in c['bundle']; print('OK')"` passes

## Inputs

- `backend/build_sidecar.sh` — source of truth for all PyInstaller flags
- `src-tauri/build.rs` — current sidecar copy logic (needs `.exe` fix)
- `src-tauri/tauri.conf.json` — current bundle config (macOS-only)
- S03-RESEARCH.md — platform-specific `_internal/` placement strategy

## Expected Output

- `backend/build_sidecar.py` — cross-platform sidecar build script with `--help` and `--dry-run`
- `src-tauri/build.rs` — updated with Windows `.exe` suffix handling
- `src-tauri/tauri.conf.json` — updated with `bundle.windows` and `bundle.linux` resource mapping
