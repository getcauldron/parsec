---
estimated_steps: 7
estimated_files: 2
---

# T03: Build PyInstaller sidecar and verify end-to-end from DMG

**Slice:** S01 — Sidecar Bundling & macOS Installer
**Milestone:** M002

## Description

Full integration proof: build the PyInstaller sidecar, build the Tauri app, install from the resulting DMG, and process a real file. This is the slice's acceptance test — it proves the complete chain works from installed binary through to searchable PDF output. Any issues discovered during this integration pass get fixed here.

## Steps

1. Run `./backend/build_sidecar.sh` to produce fresh PyInstaller output in `backend/dist/parsec-sidecar/`
2. Run `cargo tauri build --target aarch64-apple-darwin` to produce the DMG
3. Mount the DMG, drag Parsec to a test location (e.g., Desktop — not Applications, to avoid polluting the real install)
4. Launch the installed Parsec app
5. Wait for "Engine ready" status indicator
6. Drop a test PNG file (use one from `backend/tests/fixtures/`) onto the app
7. Verify the output `_ocr.pdf` file is created next to the input and contains extractable text (use `pdftotext` or `python -c "from pdfminer..."`)

## Must-Haves

- [ ] DMG mounts and app installs by drag
- [ ] App launches and shows "Engine ready" within ~10 seconds
- [ ] Dropped file processes to completion (green checkmark in UI)
- [ ] Output PDF contains extractable text
- [ ] App quits cleanly and sidecar process terminates

## Verification

- `cargo tauri build --target aarch64-apple-darwin` produces DMG at `src-tauri/target/release/bundle/dmg/Parsec_*.dmg`
- Installed app launches without Gatekeeper blocking (unsigned apps can be opened via right-click → Open)
- After dropping `backend/tests/fixtures/clean_simple.png`, a file `clean_simple_ocr.pdf` appears in the fixtures directory
- `pdftotext clean_simple_ocr.pdf -` outputs recognizable text
- After quitting app: `ps aux | grep parsec-sidecar | grep -v grep` returns nothing

## Inputs

- Working `tauri.conf.json` and `build.rs` from T01
- Working sidecar path resolution from T02
- `backend/tests/fixtures/clean_simple.png` — test input file
- `backend/build_sidecar.sh` — sidecar build script

## Expected Output

- Verified working DMG at `src-tauri/target/release/bundle/dmg/Parsec_*.dmg`
- Any fixes applied to config or code discovered during integration
- Documentation of the final app bundle layout (as comments in tauri.conf.json or build.rs)
