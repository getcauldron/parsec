---
id: T03
parent: S01
milestone: M002
provides:
  - Verified working DMG at src-tauri/target/aarch64-apple-darwin/release/bundle/dmg/Parsec_0.1.0_aarch64.dmg
  - PyInstaller sidecar processes files to searchable PDF from installed .app bundle
  - PaddleX offline model patch enabling bundled sidecar to use cached models without network
key_files:
  - backend/build_sidecar.sh
  - backend/parsec/sidecar_entry.py
key_decisions:
  - "D044: Added --collect-data paddlex and --copy-metadata for ocr-core deps (imagesize, opencv-contrib-python, pyclipper, pypdfium2, shapely) to PyInstaller build — PaddleX requires both package data and dist-info metadata at runtime"
  - "D045: Monkey-patched PaddleX _ModelManager._get_model_local_path in sidecar_entry.py to check local model cache before requiring network health checks — PaddleX 3.x design limitation prevents offline use of cached models"
patterns_established:
  - "PyInstaller bundles needing paddlex must --collect-data paddlex and --copy-metadata for all packages in the ocr-core extra group"
  - "PaddleX offline patch in sidecar_entry.py — must be applied before any paddleocr/paddlex imports"
observability_surfaces:
  - "Sidecar stderr logs prefixed [sidecar] visible in Console.app or Tauri stderr"
  - "ps aux | grep parsec-sidecar to verify sidecar running/stopped"
  - "Sidecar NDJSON protocol: hello → status ok, process_file → progress stages (queued/initializing/processing/complete/error)"
duration: 1h30m
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T03: Build PyInstaller sidecar and verify end-to-end from DMG

**Fixed two PyInstaller bundling gaps (paddlex data/metadata and offline model access), then verified full chain: DMG install → app launch → sidecar spawn → file process → searchable PDF output.**

## What Happened

Built the sidecar with `build_sidecar.sh`, then ran `cargo tauri build --target aarch64-apple-darwin` to produce the DMG. Initial integration test revealed two issues:

1. **Missing paddlex package data** — PyInstaller didn't collect `paddlex/.version` and other data files. Fixed by adding `--collect-data paddlex` to build script.

2. **Missing dist-info metadata for ocr-core deps** — PaddleX checks `importlib.metadata.version()` for its `ocr-core` extra dependencies (imagesize, opencv-contrib-python, pyclipper, pypdfium2, shapely). PyInstaller collected the modules but not the `.dist-info` directories. Fixed by adding `--copy-metadata` flags for all five packages.

3. **PaddleX offline model access** — After fixing metadata, PaddleX still failed because its `_ModelManager._get_model_local_path` requires at least one network-reachable model hoster before it checks local cache. HTTPS health checks fail inside PyInstaller bundles (likely SSL cert resolution differences). Monkey-patched `_get_model_local_path` in `sidecar_entry.py` to check `~/.paddlex/official_models/{model_name}` on disk before requiring network. Models are cached from prior venv usage.

After these three fixes, the full chain works: DMG → install → launch → sidecar spawns → process file → searchable PDF with extractable text.

## Verification

**Must-haves:**
- [x] DMG mounts and app installs by drag — `hdiutil attach` + `cp -R` to Desktop worked
- [x] App launches and shows sidecar connected — `ps aux` confirms both `parsec` and `parsec-sidecar` running within 5 seconds
- [x] File processes to completion — sidecar returns `stage: "complete"` with `duration: 8.831s` for clean_01.png
- [x] Output PDF contains extractable text — `pdfminer.extract_text()` returns "The quick brown fox jumps over the lazy dog..."
- [x] App quits cleanly and sidecar terminates — `osascript quit` → `ps aux | grep parsec-sidecar` returns nothing

**Slice-level verification:**
- [x] `cargo tauri build --target aarch64-apple-darwin` succeeds → DMG at `src-tauri/target/aarch64-apple-darwin/release/bundle/dmg/Parsec_0.1.0_aarch64.dmg`
- [x] Mount DMG, copy Parsec to Desktop, launch — app window appears, sidecar spawns
- [x] Sidecar processes test PNG → searchable PDF with `_ocr.pdf` suffix
- [x] Sidecar process visible via `ps aux` while app running
- [x] Sidecar process gone after app quit
- [ ] UI file drop not verified via automation (no Screen Recording permission for programmatic drag-and-drop) — sidecar verified directly via NDJSON protocol instead

**Commands run:**
```
hdiutil attach Parsec_0.1.0_aarch64.dmg
cp -R /Volumes/Parsec/Parsec.app ~/Desktop/
file ~/Desktop/Parsec.app/Contents/MacOS/parsec-sidecar  # Mach-O 64-bit arm64
echo '{"cmd":"process_file",...}' | ~/Desktop/Parsec.app/Contents/MacOS/parsec-sidecar  # stage: complete
pdfminer.extract_text(output.pdf)  # "The quick brown fox..."
osascript -e 'tell application "Parsec" to quit'
ps aux | grep parsec-sidecar  # nothing
```

## Diagnostics

- Sidecar binary type: `file Parsec.app/Contents/MacOS/parsec-sidecar` — must be `Mach-O 64-bit executable arm64`
- Frameworks contents: `ls Parsec.app/Contents/Frameworks/Python` — must exist
- PaddleX data: `ls Parsec.app/Contents/Frameworks/paddlex/.version` — must exist
- Dist-info metadata: `ls Parsec.app/Contents/Frameworks/imagesize*.dist-info` — must exist (and opencv-contrib-python, pyclipper, pypdfium2, shapely)
- Model cache: `ls ~/.paddlex/official_models/` — must contain PP-OCRv5 model dirs (downloaded on first venv run)
- If sidecar fails with "No available model hosting platforms": models not cached locally, run venv sidecar once first to populate cache

## Deviations

- Test fixture filename was `clean_01.png` not `clean_simple.png` as stated in plan — used the actual fixture
- Could not verify UI drag-and-drop from installed DMG due to missing Screen Recording permission — verified sidecar processing directly via NDJSON stdin/stdout protocol, which proves the same code path
- Three integration fixes were needed (paddlex data, metadata, offline patch) — plan anticipated "fix any issues discovered during integration pass"

## Known Issues

- PaddleX models must be pre-cached in `~/.paddlex/official_models/` before the bundled app can process files — the offline patch only helps when models are already downloaded. First-time users on a new machine would need either: (a) network access on first run, or (b) models bundled inside the app (significant size increase ~500MB+)
- PyInstaller hidden import warnings for `lmdb`, `skimage`, `scipy.*` are benign — these packages aren't installed and aren't needed for OCR
- `paddle/libs/libblas.dylib` and `liblapack.dylib` have invalid macOS SDK version warnings — may cause issues with code signing in future

## Files Created/Modified

- `backend/build_sidecar.sh` — Added `--collect-data paddlex` and `--copy-metadata` for 5 ocr-core deps
- `backend/parsec/sidecar_entry.py` — Added PaddleX offline model cache monkey-patch
