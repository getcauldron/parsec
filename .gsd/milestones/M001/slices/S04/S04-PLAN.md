# S04: Multi-Language & Settings

**Goal:** Users can select a non-English language in a settings panel and OCR documents in that language through the existing drop-and-go pipeline.
**Demo:** Open settings, pick Korean (or another non-English language), drop a document in that language, get a searchable PDF with correctly recognized text.

## Must-Haves

- Language registry with all 49 plugin-supported languages (display name, short code, Tesseract mapping)
- Sidecar `get_languages` command returning the full language list
- Language field threaded through sidecar → pipeline → OCRmyPDF for `process_file`
- Collapsible settings panel in the header area with language picker (R014)
- Language selection persists across app restarts via Tauri store plugin
- CSP updated to allow Google Fonts loading (pre-existing S03 issue)
- Settings panel follows D030 industrial dark aesthetic

## Proof Level

- This slice proves: integration (language flows from UI → Rust → sidecar → OCRmyPDF)
- Real runtime required: yes (sidecar must respond to get_languages and process with non-English language)
- Human/UAT required: yes (visual inspection of settings panel aesthetic, non-English OCR quality)

## Verification

- `cd backend && python -m pytest tests/test_languages.py -v` — language registry completeness, code validation, get_languages sidecar command
- `cd backend && python -m pytest tests/test_sidecar_language.py -v` — sidecar threads language through to pipeline
- Launch app with `cargo tauri dev`, open settings, select a language, confirm it persists after restart
- Drop a non-English document with the selected language and verify the output PDF contains correct text

## Observability / Diagnostics

- Runtime signals: sidecar logs selected language on each `process_file` command; pipeline logs Tesseract code used
- Inspection surfaces: `get_languages` sidecar command returns full registry; browser console logs language on processing
- Failure visibility: invalid language code → sidecar returns error stage with descriptive message; store load failure → console warning, falls back to English

## Integration Closure

- Upstream surfaces consumed: `backend/parsec/pipeline.py` (process_file, _LANG_TO_TESSERACT), `backend/parsec/sidecar.py` (command dispatch), `src-tauri/src/lib.rs` (process_files command), `src/main.ts` (processDroppedPaths)
- New wiring introduced in this slice: store plugin registration in Rust, language parameter in Tauri command signature, settings panel DOM in index.html, `get_languages` sidecar command
- What remains before the milestone is truly usable end-to-end: S05 (PDF input + preprocessing), S06 (integration testing)

## Tasks

- [x] **T01: Build language registry and thread language through sidecar protocol** `est:1h`
  - Why: The backend currently ignores the language field in process_file commands and only has 12 language mappings. This task creates the authoritative language registry, extends the mapping to all 49 plugin-supported languages, threads language through the sidecar to the pipeline, and adds a `get_languages` command so the frontend can populate its picker dynamically.
  - Files: `backend/parsec/languages.py`, `backend/parsec/pipeline.py`, `backend/parsec/sidecar.py`, `backend/tests/test_languages.py`
  - Do: Create `languages.py` with all 49 languages (display name, short code, Tesseract code, script group). Replace `_LANG_TO_TESSERACT` in pipeline.py with import from languages.py. In sidecar.py, read `language` from process_file commands and pass via OcrOptions. Add `get_languages` command handler. Write tests for registry completeness, code validation, and sidecar language threading.
  - Verify: `cd backend && python -m pytest tests/test_languages.py -v` passes; manual sidecar stdin test with `get_languages` command returns 49 entries
  - Done when: All 49 plugin-supported languages are registered, `get_languages` returns the list, and `process_file` with a `language` field passes it through to OcrOptions

- [x] **T02: Settings panel with language picker, persistence, and Rust language forwarding** `est:2h`
  - Why: The frontend has no settings UI and no way to change language. This task adds the store plugin for persistence, extends the Rust command to forward language, builds the collapsible settings panel with language picker, fixes the CSP for fonts, and wires everything together end-to-end.
  - Files: `src-tauri/Cargo.toml`, `src-tauri/src/lib.rs`, `src-tauri/capabilities/default.json`, `package.json`, `src-tauri/tauri.conf.json`, `src/main.ts`, `src/settings.ts`, `src/styles.css`, `index.html`
  - Do: Add `tauri-plugin-store` to Cargo.toml and `@tauri-apps/plugin-store` to package.json. Register store plugin in lib.rs and add `store:default` permission. Extend `process_files` command to accept `language` param and include it in sidecar JSON. Fix CSP to allow Google Fonts. Create `settings.ts` module with collapsible settings panel, language picker populated via sidecar `get_languages`, and persistence via store. Wire settings into main.ts — read stored language on startup, pass to processDroppedPaths. Style the panel to match D030 aesthetic (dark bg, DM Mono/Sans, amber accents). Load frontend-design skill for the settings panel UI.
  - Verify: `cargo tauri dev` launches; settings panel opens/closes; language picker shows 49 languages; selected language persists after app restart; dropping a file sends the selected language through the pipeline
  - Done when: Language selection flows from UI → store → Rust → sidecar → OCRmyPDF, settings panel is collapsible and visually consistent with D030, and language persists across restarts

## Files Likely Touched

- `backend/parsec/languages.py` (new)
- `backend/parsec/pipeline.py`
- `backend/parsec/sidecar.py`
- `backend/tests/test_languages.py` (new)
- `src-tauri/Cargo.toml`
- `src-tauri/src/lib.rs`
- `src-tauri/capabilities/default.json`
- `src-tauri/tauri.conf.json`
- `package.json`
- `src/main.ts`
- `src/settings.ts` (new)
- `src/styles.css`
- `index.html`
