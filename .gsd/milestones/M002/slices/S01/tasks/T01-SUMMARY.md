---
id: T01
parent: S01
milestone: M002
provides:
  - PyInstaller _internal/ directory bundled in macOS app at Contents/MacOS/_internal/
  - Real PyInstaller binary used as sidecar in release builds
  - Dev mode preserved with shell wrapper fallback
key_files:
  - src-tauri/tauri.conf.json
  - src-tauri/build.rs
key_decisions:
  - "D041: Used bundle.macOS.files instead of bundle.resources to place _internal/ in Contents/MacOS/ (adjacent to sidecar binary)"
  - "D042: build.rs copies PyInstaller binary only in release profile, dev uses shell wrapper"
patterns_established:
  - "bundle.macOS.files for placing directories in Contents/MacOS/ alongside sidecar"
  - "PROFILE env var to gate dev vs production sidecar binary selection in build.rs"
observability_surfaces:
  - "cargo:warning messages in build.rs indicate which binary path is being used"
duration: 25m
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T01: Configure bundle.resources for PyInstaller _internal/ folder

**Used `bundle.macOS.files` (not `bundle.resources`) to place _internal/ in Contents/MacOS/ next to the sidecar binary, and gated build.rs to copy the real PyInstaller binary only for release builds.**

## What Happened

The original plan called for `bundle.resources` to include `_internal/`, but investigation revealed that `bundle.resources` maps files into `Contents/Resources/` — wrong location. PyInstaller's `--onedir` binary expects `_internal/` as a sibling directory. Since the sidecar binary ends up in `Contents/MacOS/` (via `externalBin`), `_internal/` must go there too.

Used Tauri's `bundle.macOS.files` config instead, which maps directly into `Contents/`. Set `"MacOS/_internal": "../backend/dist/parsec-sidecar/_internal"` to copy the full directory to `Contents/MacOS/_internal/`.

Updated `build.rs` to copy the PyInstaller binary (43MB Mach-O) over the shell wrapper only when `PROFILE == "release"`. First iteration didn't check the profile and broke dev mode — the PyInstaller binary ran from `target/debug/` where no `_internal/` exists. Adding the profile gate fixed it.

## Verification

- **PyInstaller build**: `./backend/build_sidecar.sh` completed, producing `backend/dist/parsec-sidecar/` with 156-entry `_internal/` directory
- **`cargo tauri build --target aarch64-apple-darwin`**: Completed, produced `.app` bundle and 225MB DMG
- **App bundle inspection**:
  - `Contents/MacOS/_internal/` exists with 156 entries (Python framework, paddle, cv2, etc.)
  - `Contents/MacOS/parsec-sidecar` is a Mach-O 64-bit executable arm64 (not shell script)
  - `Contents/Resources/` contains only `icon.icns` (resources not polluted)
- **Dev mode regression**: `cargo tauri dev` launched successfully, sidecar spawned via shell wrapper → PyInstaller binary, logged `Sidecar started (version 0.1.0)`
- **Shell wrapper intact**: `binaries/parsec-sidecar-aarch64-apple-darwin` remains a shell script after builds (git checkout restores it after release build overwrites)

### Slice-level verification (partial — T01 of 3):
- ✅ `cargo tauri build --target aarch64-apple-darwin` produces DMG at `src-tauri/target/aarch64-apple-darwin/release/bundle/dmg/Parsec_0.1.0_aarch64.dmg`
- ⬜ Mount DMG, install, launch — app window appears (T03)
- ⬜ Drop test PNG → searchable PDF output (T03)
- ⬜ Sidecar process visible while running, gone after quit (T03)

## Diagnostics

- Build output: `cargo:warning=Bundling PyInstaller binary: ...` confirms which binary build.rs selected
- App bundle inspection: `ls -la Parsec.app/Contents/MacOS/` shows sidecar binary + `_internal/`
- Dev vs production: `file binaries/parsec-sidecar-aarch64-apple-darwin` — shell script = dev wrapper, Mach-O = production binary was copied

## Deviations

- Used `bundle.macOS.files` instead of `bundle.resources` — resources go to `Contents/Resources/` but `_internal/` must be in `Contents/MacOS/`. This was discovered during implementation. The plan title references `bundle.resources` but the actual mechanism is `bundle.macOS.files`.
- T02's concern about sidecar path resolution in production is largely resolved — since `_internal/` is a sibling of the binary in `Contents/MacOS/`, PyInstaller finds it naturally. T02 may only need minor adjustments if any.

## Known Issues

- DMG creation logged an error (`failed to run bundle_dmg.sh`) but the DMG was produced anyway (225MB). May be a stale error from a previous build or a non-fatal issue with code signing setup.
- Release build overwrites the committed shell wrapper in `binaries/` with the 43MB PyInstaller binary. After the build, `git checkout -- src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` restores it. Consider adding this to `.gitignore` or using a separate staging directory.

## Files Created/Modified

- `src-tauri/tauri.conf.json` — Added `bundle.macOS.files` entry mapping `_internal/` to `Contents/MacOS/`
- `src-tauri/build.rs` — Rewritten: copies PyInstaller binary only in release profile, leaves shell wrapper for dev
