# S01: Sidecar Bundling & macOS Installer

**Goal:** `cargo tauri build` produces a macOS DMG where the PyInstaller sidecar binary + `_internal/` folder are bundled inside the app and work correctly from the installed location.

**Demo:** Install the DMG on macOS, launch Parsec, drop a PNG file, get a searchable PDF output.

## Must-Haves

- PyInstaller `--onedir` output (`parsec-sidecar` binary + `_internal/` folder) bundled inside the app via `bundle.resources`
- Sidecar binary in `externalBin` resolves correctly inside the installed app bundle
- `_internal/` directory is adjacent to (or findable by) the sidecar binary at runtime
- `cargo tauri build` completes without error and produces a mountable DMG
- Installed app launches, spawns sidecar, processes at least one file to searchable PDF

## Proof Level

- This slice proves: operational (installed app processes files)
- Real runtime required: yes — installed DMG, not dev mode
- Human/UAT required: yes — manual install and file drop on installed app

## Verification

- `cargo tauri build --target aarch64-apple-darwin` succeeds and produces a DMG in `src-tauri/target/release/bundle/dmg/`
- Mount DMG, drag Parsec to Applications, launch — app window appears
- Drop a test PNG onto the app — file processes to searchable PDF with `_ocr.pdf` suffix
- After verification, unmount DMG and delete from Applications (clean uninstall)
- Sidecar process visible via `ps aux | grep parsec-sidecar` while app is running
- Sidecar process gone after app quit

## Observability / Diagnostics

- Runtime signals: Sidecar stderr logs (prefixed `[sidecar]`) visible in Console.app or Tauri's stderr
- Inspection surfaces: `ps aux | grep parsec-sidecar` to verify sidecar is running; app bundle contents inspectable via `ls -R /Applications/Parsec.app/Contents/`
- Failure visibility: Sidecar spawn failure surfaces as "Engine not ready" in the UI status indicator; `[parsec]` prefixed Rust logs in stderr
- Redaction constraints: none

## Integration Closure

- Upstream surfaces consumed: M001's complete Tauri app, PyInstaller build script, sidecar launcher
- New wiring introduced in this slice: `bundle.resources` for `_internal/`, updated `build.rs` for production sidecar copy, sidecar launcher logic for installed-app paths
- What remains before the milestone is truly usable end-to-end: Auto-update (S02), UI polish (S03), but the app is functional for manual distribution after this slice

## Tasks

- [x] **T01: Configure bundle.resources for PyInstaller _internal/ folder** `est:1h`
  - Why: Tauri's `externalBin` only bundles a single file. The PyInstaller `--onedir` output has a `parsec-sidecar` binary + `_internal/` directory (~hundreds of files). The `_internal/` folder must be bundled via `bundle.resources` so it ends up in the app bundle.
  - Files: `src-tauri/tauri.conf.json`, `src-tauri/build.rs`
  - Do: Add `bundle.resources` entry mapping `../backend/dist/parsec-sidecar/_internal` to the app bundle. Update `build.rs` to copy the actual PyInstaller binary (not the shell wrapper) as the sidecar with the target-triple suffix. The `externalBin` entry stays as `["binaries/parsec-sidecar"]` — Tauri handles the triple suffix.
  - Verify: `cargo tauri build --target aarch64-apple-darwin` starts (may fail at signing, but bundle assembly should work). Inspect the app bundle to confirm `_internal/` is present alongside the sidecar binary.
  - Done when: App bundle contains both the sidecar binary and `_internal/` folder in the correct relative positions.

- [x] **T02: Update sidecar launcher for installed-app paths** `est:1h`
  - Why: The current shell wrapper (`parsec-sidecar-aarch64-apple-darwin`) walks up the directory tree to find `backend/`. In an installed app, there's no `backend/` — the sidecar binary is inside the app bundle and `_internal/` is in `Resources/`. The sidecar needs to find `_internal/` relative to its own location inside the bundle.
  - Files: `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin`, `src-tauri/src/sidecar.rs`
  - Do: Replace the shell wrapper with logic that works in both dev and production. Options: (a) in production, the `externalBin` points to the real PyInstaller binary which already knows where `_internal/` is (it's a sibling dir), so no wrapper needed — just ensure `build.rs` copies the right binary; (b) if `_internal/` ends up in `Resources/` instead of adjacent to the binary, set `DYLD_LIBRARY_PATH` or use a wrapper that symlinks/copies. Investigate the actual bundle layout first, then implement the simplest working solution.
  - Verify: `cargo tauri build` produces a DMG. Mount it, launch the app, check that the sidecar spawns (visible in `ps aux`). Check Console.app for `[parsec]` and `[sidecar]` log lines.
  - Done when: Sidecar spawns successfully from inside the installed app bundle.

- [x] **T03: Build PyInstaller sidecar and verify end-to-end from DMG** `est:1h30m`
  - Why: Integration proof — build the sidecar, build the app, install from DMG, and process a real file. This is the slice's acceptance test.
  - Files: `backend/build_sidecar.sh`, possibly `src-tauri/tauri.conf.json` (fixes from T01/T02)
  - Do: Run `./backend/build_sidecar.sh` to produce the PyInstaller output. Run `cargo tauri build --target aarch64-apple-darwin`. Mount the resulting DMG. Install Parsec. Launch it. Drop a test PNG file. Verify the output `_ocr.pdf` is created and contains extractable text. Fix any issues discovered during this integration pass. Document the final bundle layout.
  - Verify: Fresh install from DMG → launch → drop file → searchable PDF output. `pdftotext` or equivalent confirms text extraction works on the output. Sidecar process starts and stops cleanly with the app.
  - Done when: A person can install Parsec from the DMG, process a file, and get a searchable PDF. The full cycle works without `cargo tauri dev`.

## Files Likely Touched

- `src-tauri/tauri.conf.json`
- `src-tauri/build.rs`
- `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin`
- `src-tauri/src/sidecar.rs` (possibly, if path resolution changes needed)
- `backend/build_sidecar.sh` (possibly, if build adjustments needed)
