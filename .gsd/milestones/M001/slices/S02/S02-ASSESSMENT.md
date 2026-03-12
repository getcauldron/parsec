# S02 Assessment — Roadmap Reassessment

## Verdict: Roadmap unchanged

S02 retired its target risk: Tauri spawning a PyInstaller-built Python binary with bidirectional JSON exchange. All three tasks passed verification. The proof strategy item ("Python sidecar bundling → retire in S02") is satisfied.

## Risk Retirement

- **Python sidecar bundling** — retired. PyInstaller --onedir binary (652MB) builds, runs through Tauri, responds in 85ms with clean JSON. Wrapper script provides dev-mode fallback to venv Python.
- **Sidecar communication reliability** — partially de-risked. Line-buffered stdout proven. Full progress streaming (the S03 risk) not yet tested, but the buffering foundation is solid.

## Boundary Map Accuracy

S02 → S03 boundary matches what was built:
- `sidecar.rs` — spawn, send, kill with Mutex managed state ✅
- `lib.rs` — Tauri app with sidecar lifecycle and `greet_sidecar` command ✅
- `src/` — minimal web UI scaffold ✅
- PyInstaller binary proven ✅

S03 will need to extend the sidecar protocol with `process_file` command and progress streaming — this was always planned and is covered by the S01 → S03 boundary.

## Success Criteria Coverage

- User can launch Parsec and see a drag-and-drop interface → S03
- Dropping image files (PNG/JPEG/TIFF) produces searchable PDFs next to the originals → S03
- Dropping non-searchable PDFs produces searchable versions → S05
- Per-file progress is visible during processing → S03
- Skewed/rotated scans are auto-corrected before OCR → S05
- Non-English documents can be processed by selecting a language → S04
- Corrupt or unsupported files produce clear error messages without crashing → S03
- OCR quality meets CER/WER thresholds on the test fixture set → S01 (done), S06

All criteria have at least one remaining owning slice. Coverage check passes.

## Requirement Coverage

No changes to requirement ownership. S02's primary requirement (R010: cross-platform desktop app) is partially proven — macOS verified, other platforms deferred to M002 per D009. All 17 active requirements remain mapped to slices with unchanged ownership.

## New Risks / Known Issues (non-blocking)

- **Binary size (652MB):** Expected for PaddlePaddle. Distribution concern for M002, not M001.
- **macOS code signing warnings:** paddle's libblas/liblapack have SDK version 0,0,0. Needs addressing for production distribution (M002).
- **Full OCR through PyInstaller binary:** `process_file()` not yet tested through the binary — comes in S03 when the pipeline is wired.

## Decisions Added

D020–D024 recorded during S02 execution. No decisions need revision.
