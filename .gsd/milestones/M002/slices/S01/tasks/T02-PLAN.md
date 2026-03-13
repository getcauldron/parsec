---
estimated_steps: 5
estimated_files: 3
---

# T02: Update sidecar launcher for installed-app paths

**Slice:** S01 — Sidecar Bundling & macOS Installer
**Milestone:** M002

## Description

The current sidecar launcher is a shell wrapper that walks up the directory tree to find `backend/`. Inside an installed app bundle, there's no `backend/` directory — the sidecar binary lives inside `Parsec.app/Contents/MacOS/` or a resource directory, and `_internal/` lives in `Parsec.app/Contents/Resources/`. The PyInstaller binary expects `_internal/` to be a sibling directory. This task ensures the sidecar binary can find `_internal/` regardless of whether it's running in dev mode or from an installed app bundle.

## Steps

1. Examine the actual app bundle layout from T01's build to understand where Tauri places the `externalBin` binary and `resources` files
2. Determine whether `_internal/` ends up adjacent to the sidecar binary (ideal — PyInstaller finds it automatically) or in a separate `Resources/` path (requires intervention)
3. If `_internal/` is not adjacent: either adjust `bundle.resources` target mapping to place it next to the binary, or modify the Rust sidecar spawn code to set the working directory / environment so the binary finds its dependencies
4. If the Rust sidecar spawn needs changes, update `sidecar.rs` to set `DYLD_LIBRARY_PATH` or `current_dir` when spawning the sidecar in production mode
5. Test by building and launching the installed app — sidecar must spawn and respond to the `hello` command

## Must-Haves

- [ ] Sidecar binary finds `_internal/` at runtime inside the installed app bundle
- [ ] No changes break dev mode (`cargo tauri dev`) sidecar spawning
- [ ] Sidecar responds to commands (hello, process_file) from inside the bundle

## Verification

- Build with `cargo tauri build`, mount DMG, install app
- Launch installed app — sidecar status indicator shows "Engine ready"
- Check `ps aux | grep parsec-sidecar` — sidecar process is running
- Check Console.app or stderr for `[parsec] sidecar spawned` log line
- Quit app — sidecar process disappears from `ps aux`

## Inputs

- App bundle layout from T01 (inspect `Parsec.app/Contents/`)
- `src-tauri/src/sidecar.rs` — current sidecar spawn logic
- `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` — current shell wrapper

## Expected Output

- Working sidecar spawn from inside the installed app bundle
- Possibly updated `sidecar.rs` with production path handling
- Possibly updated `tauri.conf.json` resource mapping
- Possibly updated/replaced shell wrapper in `src-tauri/binaries/`
