---
id: T02
parent: S01
milestone: M002
provides:
  - Sidecar binary finds PyInstaller dependencies at runtime inside installed .app bundle
  - PyInstaller _internal/ correctly mapped to Contents/Frameworks/ (macOS bundle convention)
  - Dev mode sidecar spawning unaffected
key_files:
  - src-tauri/tauri.conf.json
key_decisions:
  - "D043: _internal/ mapped to Contents/Frameworks/ instead of Contents/MacOS/_internal/ — PyInstaller bootloader expects Frameworks/ path inside .app bundles"
patterns_established:
  - "PyInstaller --onedir bundles inside Tauri macOS apps must map _internal/ to Contents/Frameworks/, not Contents/MacOS/_internal/"
observability_surfaces:
  - "Direct sidecar test: echo '{\"cmd\":\"hello\"}' | Parsec.app/Contents/MacOS/parsec-sidecar"
  - "ps aux | grep parsec-sidecar — verify sidecar running from bundle path"
  - "PyInstaller bootloader error '[PYI-*:ERROR] Failed to load Python shared library' indicates wrong Frameworks path"
duration: 15m
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T02: Update sidecar launcher for installed-app paths

**Changed `_internal/` bundle mapping from `Contents/MacOS/_internal/` to `Contents/Frameworks/` to match PyInstaller bootloader's macOS app bundle convention.**

## What Happened

T01 placed `_internal/` at `Contents/MacOS/_internal/` — adjacent to the sidecar binary. This seemed correct since PyInstaller `--onedir` normally expects `_internal/` as a sibling. However, testing the actual built binary from inside the `.app` bundle revealed a critical failure:

```
[PYI-20950:ERROR] Failed to load Python shared library '.../Contents/Frameworks/Python'
```

The PyInstaller bootloader (C code compiled into the binary) detects it's running inside a `.app/Contents/MacOS/` path and remaps its library search from the relative `_internal/` directory to `Contents/Frameworks/` — the standard macOS framework location. This is confirmed by `sys._MEIPASS` being set to `Contents/Frameworks` in the Python runtime hooks.

The fix was a one-line change in `tauri.conf.json`: mapping `_internal/` source to `Frameworks` instead of `MacOS/_internal` in `bundle.macOS.files`. No changes needed to `sidecar.rs` or the shell wrapper — the bootloader handles path resolution automatically once the files are in the right place.

## Verification

- **Sidecar from bundle (direct):** `echo '{"cmd":"hello"}' | Parsec.app/Contents/MacOS/parsec-sidecar` → `{"status":"ok","message":"parsec sidecar ready","version":"0.1.0"}`
- **Bundle layout:** `Contents/Frameworks/` has 156 entries (Python, Python.framework, cv2, paddle, etc.); `Contents/MacOS/` has only `parsec` and `parsec-sidecar`
- **App launch:** `open Parsec.app` → app window appears, `ps aux | grep parsec-sidecar` shows sidecar running from bundle path
- **App quit:** Quit Parsec → sidecar process disappears from `ps aux`
- **Dev mode:** Shell wrapper (`binaries/parsec-sidecar-aarch64-apple-darwin`) responds to `hello` command, PyInstaller binary path outside bundle works normally

### Slice-level verification (partial — T02 of 3):
- ✅ `cargo tauri build --target aarch64-apple-darwin` produces DMG (235MB)
- ✅ Launch .app from build output — app window appears, sidecar spawns
- ✅ Sidecar process visible while running, gone after quit
- ⬜ Mount DMG, drag to Applications, launch (T03)
- ⬜ Drop test PNG → searchable PDF output (T03)

## Diagnostics

- PyInstaller bootloader error `[PYI-*:ERROR] Failed to load Python shared library` → `_internal/` is in wrong location relative to bundle structure
- `ls Parsec.app/Contents/Frameworks/Python` — must exist for sidecar to start
- `file Parsec.app/Contents/MacOS/parsec-sidecar` — must be `Mach-O 64-bit executable arm64`
- PyInstaller runtime checks: `sys._MEIPASS` ends with `Contents/Frameworks` when inside a macOS app bundle

## Deviations

- **No sidecar.rs changes needed:** Task plan anticipated possible `current_dir` or `DYLD_LIBRARY_PATH` changes. Not needed — PyInstaller bootloader handles all path resolution once files are in `Contents/Frameworks/`.
- **No shell wrapper changes needed:** The shell wrapper is only used in dev mode. Production builds use the real PyInstaller binary which finds dependencies via the bootloader's built-in macOS bundle detection.
- **Superseded D041:** T01's mapping (`MacOS/_internal`) was incorrect for runtime. Changed to `Frameworks` mapping (D043).

## Known Issues

- Release build still overwrites committed shell wrapper in `binaries/` with 43MB PyInstaller binary (same issue from T01). `git checkout` restores it. T03 or a follow-up should address this.

## Files Created/Modified

- `src-tauri/tauri.conf.json` — Changed `bundle.macOS.files` key from `"MacOS/_internal"` to `"Frameworks"` to match PyInstaller bootloader's macOS bundle convention
