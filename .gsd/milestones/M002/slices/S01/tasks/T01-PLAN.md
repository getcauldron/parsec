---
estimated_steps: 6
estimated_files: 3
---

# T01: Configure bundle.resources for PyInstaller _internal/ folder

**Slice:** S01 — Sidecar Bundling & macOS Installer
**Milestone:** M002

## Description

Tauri's `externalBin` only bundles a single binary file per entry. The PyInstaller `--onedir` output produces a `parsec-sidecar` executable plus a large `_internal/` directory containing the Python runtime, all dependencies (PaddleOCR, OCRmyPDF, etc.), and shared libraries. The `_internal/` folder must be included in the app bundle via `bundle.resources` so it's available at runtime when the sidecar binary is launched.

## Steps

1. Build the PyInstaller sidecar with `./backend/build_sidecar.sh` to ensure `backend/dist/parsec-sidecar/` exists with the `_internal/` directory
2. Add `bundle.resources` entry to `src-tauri/tauri.conf.json` mapping the `_internal/` directory into the app bundle
3. Update `build.rs` to copy the actual PyInstaller binary (from `backend/dist/parsec-sidecar/parsec-sidecar`) to the `binaries/` directory with the target-triple suffix, instead of relying on the shell wrapper
4. Handle the dev vs production distinction — `build.rs` should only copy the PyInstaller binary when it exists (production build), falling back to the shell wrapper for dev
5. Run `cargo tauri build --target aarch64-apple-darwin` to test the bundle assembly
6. Inspect the resulting app bundle (`Parsec.app/Contents/`) to verify `_internal/` is present and the sidecar binary is in the expected location

## Must-Haves

- [ ] `bundle.resources` entry in `tauri.conf.json` includes `_internal/` directory
- [ ] `build.rs` copies PyInstaller binary with target-triple suffix for production builds
- [ ] Dev mode (`cargo tauri dev`) still works with the shell wrapper fallback

## Verification

- `cargo tauri build --target aarch64-apple-darwin` completes bundle assembly (may stop at code signing — that's OK for this task)
- Inspect `src-tauri/target/release/bundle/macos/Parsec.app/Contents/` — `_internal/` directory exists and contains Python runtime files
- Sidecar binary exists with correct name in the app bundle
- `cargo tauri dev` still launches successfully with the shell wrapper (regression check)

## Inputs

- `src-tauri/tauri.conf.json` — current bundle config with `externalBin: ["binaries/parsec-sidecar"]`
- `src-tauri/build.rs` — current build script that copies sidecar binary with triple suffix
- `backend/dist/parsec-sidecar/` — PyInstaller output (must be built first)

## Expected Output

- `src-tauri/tauri.conf.json` — updated with `bundle.resources` entry
- `src-tauri/build.rs` — updated to copy PyInstaller binary for production builds
