---
id: S04
parent: M001
milestone: M001
provides:
  - Authoritative 49-language registry (backend/parsec/languages.py) with lookup helpers
  - get_languages sidecar command for dynamic language picker population
  - Language threading through sidecar → OcrOptions → pipeline → OCRmyPDF
  - Collapsible settings panel with language picker grouped by script family
  - Tauri store plugin for settings persistence across app restarts
  - CSP updated for Google Fonts and Tauri IPC in production builds
requires:
  - slice: S03
    provides: process_files Tauri command, drop zone UI, sidecar progress protocol
affects:
  - S06
key_files:
  - backend/parsec/languages.py
  - backend/parsec/sidecar.py
  - backend/parsec/pipeline.py
  - src/settings.ts
  - src-tauri/src/lib.rs
  - src-tauri/tauri.conf.json
key_decisions:
  - Language short codes match PaddleOCR codes (en, ch, korean, japan) — no translation layer
  - Unknown language codes raise ValueError — explicit failure over silent wrong-language OCR
  - get_languages uses same event-driven pattern as greet_sidecar
  - Language picker uses optgroups by script_group for scannable organization
patterns_established:
  - Language dataclass with display_name, short_code, tesseract_code, script_group
  - Lookup indexes built once at import time
  - Settings module pattern — buildSettingsDOM(), loadStore(), fetchLanguages() in sequence
  - Store defaults pattern with auto-save
  - Collapsible panel via max-height + opacity transition
observability_surfaces:
  - Frontend console [parsec-settings] for language changes
  - Rust stderr process_files language=XX
  - Sidecar stderr process_file language=XX
  - Invalid language → immediate error stage
drill_down_paths:
  - .gsd/milestones/M001/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M001/slices/S04/tasks/T02-SUMMARY.md
duration: ~40min
verification_result: passed
completed_at: 2026-03-12
---

# S04: Multi-Language & Settings

**49-language OCR support with collapsible settings panel, persistent language selection, and full pipeline threading from UI to OCRmyPDF.**

## What Happened

T01 created `backend/parsec/languages.py` with all 49 languages from the ocrmypdf_paddleocr plugin. Replaced inline 12-entry map in pipeline.py. Extended sidecar to read/validate language, pass through OcrOptions, and added `get_languages` command.

T02 wired the frontend: store plugin for persistence, extended Rust command with `language` param, built collapsible settings panel with gear icon, populated picker from sidecar, fixed CSP for fonts and IPC.

## Verification

- `cd backend && python -m pytest tests/test_languages.py -v` — 15/15 passed
- `cd backend && python -m pytest tests/test_sidecar_language.py -v` — 5/5 passed
- `cd backend && python -m pytest tests/ -v` — 56/56 passed
- `cargo check` — clean
- `pnpm build` — clean (13 modules, 29KB JS)
- `cargo tauri dev` — settings panel works, language picker populated, drop zone unaffected

## Requirements Advanced

- R014 — Language selection UI with 49 languages, persistent across restarts

## Deviations

- Added connect-src for Tauri IPC in CSP
- Created dedicated get_languages Tauri command instead of reusing sidecar channel

## Known Limitations

- Language picker may show English-only fallback briefly on cold start before sidecar responds

## Follow-ups

- UAT with non-English document OCR
- Consider static language fallback to avoid sidecar race

## Files Created/Modified

- `backend/parsec/languages.py` — 49-language registry
- `backend/parsec/pipeline.py` — replaced inline lang map
- `backend/parsec/sidecar.py` — language threading, get_languages
- `backend/tests/test_languages.py` — 15 tests
- `backend/tests/test_sidecar_language.py` — 5 tests
- `src-tauri/Cargo.toml` — tauri-plugin-store
- `src-tauri/src/lib.rs` — store plugin, get_languages, language param
- `src-tauri/capabilities/default.json` — store:default permission
- `src-tauri/tauri.conf.json` — CSP
- `src/settings.ts` — settings panel with language picker
- `src/main.ts` — settings integration
- `src/styles.css` — settings panel styles

## Forward Intelligence

### What the next slice should know
- `process_files` signature: `(paths, language, channel)` — add more optional params for preprocessing
- Language validation happens in sidecar before pipeline — unsupported codes get immediate error
- Settings module at `src/settings.ts` — extend for preprocessing toggles

### What's fragile
- Language picker population depends on sidecar readiness
- CSP is getting complex — new external resources need updates in tauri.conf.json

### Authoritative diagnostics
- `echo '{"cmd":"get_languages"}' | python -m parsec.sidecar` — verify registry
- Browser `[parsec-settings]` — language events
- Sidecar stderr `language=XX` — verify pipeline receives correct language

### What assumptions changed
- Inline 12-lang map was insufficient — needed full 49-language registry from plugin
