---
estimated_steps: 6
estimated_files: 9
---

# T02: Settings panel with language picker, persistence, and Rust language forwarding

**Slice:** S04 — Multi-Language & Settings
**Milestone:** M001

## Description

The frontend has no settings UI and no mechanism to change the OCR language. This task wires the Tauri store plugin for persistence, extends the Rust `process_files` command to forward a language parameter to the sidecar, builds a collapsible settings panel with a language picker populated from the sidecar's `get_languages` command, fixes the CSP to allow Google Fonts, and tests the complete chain: UI selection → store → Rust → sidecar → OCRmyPDF.

## Steps

1. **Add store plugin dependencies** — Add `tauri-plugin-store` to `src-tauri/Cargo.toml` dependencies. Add `@tauri-apps/plugin-store` to `package.json` dependencies. Run `pnpm install`. Register `.plugin(tauri_plugin_store::Builder::new().build())` in `lib.rs`. Add `"store:default"` to `src-tauri/capabilities/default.json` permissions array.

2. **Extend Rust `process_files` command** — Add `language: Option<String>` parameter to the `process_files` function signature. When constructing the sidecar command JSON for each file, include `"language": language` (defaulting to `"en"` if None). No changes to `sidecar.rs` needed — it already writes arbitrary JSON to stdin.

3. **Fix CSP for Google Fonts** — Update the `security.csp` field in `src-tauri/tauri.conf.json` to allow `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com` and `font-src https://fonts.gstatic.com`. This fixes a pre-existing S03 issue where fonts may fail in production builds.

4. **Create `src/settings.ts`** — Build a collapsible settings panel module. On init, call `get_languages` via sidecar (invoke a new Tauri command or use the existing sidecar communication channel) to populate the language picker. Use `@tauri-apps/plugin-store` to load/save the selected language. Export `getSelectedLanguage(): string` for use by `main.ts`. The panel should be a collapsible section in the header area with a gear icon toggle — must not interfere with the drop zone. Follow D030 aesthetic: dark background, DM Mono for labels, amber accent on active selection.

5. **Wire settings into `src/main.ts`** — Import settings module. On startup, initialize settings (loads store, populates picker). In `processDroppedPaths()`, read `getSelectedLanguage()` and pass it to the `invoke("process_files", { paths, language, channel })` call. Update the `ACCEPTED_EXTENSIONS` comment and drop hint if needed.

6. **Integration test** — Launch with `cargo tauri dev`. Verify: settings gear icon visible in header, clicking it opens/closes settings panel, language picker shows ~49 languages with English as default, selecting a language persists after app restart (close and reopen), dropping a file with a non-English language selected sends the correct language through the pipeline (verify via sidecar stderr logs).

## Must-Haves

- [ ] Store plugin registered and working (settings persist across restarts)
- [ ] Rust `process_files` accepts and forwards `language` parameter to sidecar
- [ ] CSP allows Google Fonts (style-src and font-src directives)
- [ ] Settings panel is collapsible and doesn't interfere with drop zone
- [ ] Language picker populated dynamically from sidecar's `get_languages`
- [ ] Selected language flows through to OCRmyPDF when processing files
- [ ] Settings panel matches D030 dark industrial aesthetic

## Verification

- `cargo tauri dev` launches without errors
- Settings panel opens/closes via gear icon in header
- Language picker shows 49 languages, English selected by default
- Changing language and restarting app preserves the selection
- Dropping a file with non-English language selected — sidecar stderr shows `language=XX`
- Google Fonts load without CSP errors (check browser console)

## Observability Impact

- Signals added/changed: frontend console logs selected language on each process invocation; sidecar stderr shows language used
- How a future agent inspects this: browser console for language selection, sidecar stderr for language in pipeline
- Failure state exposed: store load failure → console warning + English fallback; `get_languages` failure → console error + hardcoded English-only fallback

## Inputs

- `backend/parsec/languages.py` — language registry from T01 (get_languages command)
- `backend/parsec/sidecar.py` — updated in T01 to handle language in process_file and get_languages
- `src-tauri/src/lib.rs` — existing process_files command to extend
- `src/main.ts` — existing processDroppedPaths to wire language into
- `index.html` — header area where settings panel goes
- `src/styles.css` — D030 design tokens to match
- S04-RESEARCH.md constraints on store plugin, CSP, and panel placement

## Expected Output

- `src-tauri/Cargo.toml` — store plugin dependency added
- `src-tauri/src/lib.rs` — store plugin registered, process_files accepts language param
- `src-tauri/capabilities/default.json` — store:default permission added
- `src-tauri/tauri.conf.json` — CSP updated for fonts
- `package.json` — @tauri-apps/plugin-store dependency added
- `src/settings.ts` — collapsible settings panel with language picker and store persistence
- `src/main.ts` — settings integration, language passed to process_files
- `src/styles.css` — settings panel styles matching D030
- `index.html` — settings panel markup in header area
