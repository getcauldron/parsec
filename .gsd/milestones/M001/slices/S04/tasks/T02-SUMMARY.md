---
id: T02
parent: S04
milestone: M001
provides:
  - Collapsible settings panel with language picker (49 languages, grouped by script)
  - Tauri store plugin wired for settings persistence across restarts
  - Rust process_files command forwards language to sidecar
  - get_languages Tauri command to fetch language registry from sidecar
  - CSP updated to allow Google Fonts in production builds
key_files:
  - src/settings.ts
  - src-tauri/src/lib.rs
  - src-tauri/tauri.conf.json
  - src/styles.css
  - backend/tests/test_sidecar_language.py
key_decisions:
  - get_languages command uses same event-driven pattern as greet_sidecar (listen for sidecar-response, filter by "languages" key presence)
  - Language picker uses optgroups by script_group for scannable organization (Latin, CJK, Cyrillic, etc.)
  - CSP includes connect-src for ipc: and http://ipc.localhost to support Tauri IPC in production builds
patterns_established:
  - Settings module pattern — buildSettingsDOM(), loadStore(), fetchLanguages() called in sequence from initSettings()
  - Store defaults pattern — provide defaults object to load() call, auto-save enabled
  - Collapsible panel pattern — max-height + opacity transition, toggled via --open modifier class
observability_surfaces:
  - Frontend console logs language selection changes: "[parsec-settings] language changed to: XX"
  - Frontend console logs language used per processing batch: "[parsec-ui] processing N file(s) with language=XX"
  - Rust stderr logs language per process_files call: "[parsec] process_files called with N path(s), language=XX"
  - Store load failure → console warning + English fallback
  - get_languages failure → console error + hardcoded English-only fallback
duration: 25min
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T02: Settings panel with language picker, persistence, and Rust language forwarding

**Wired Tauri store plugin, built collapsible settings panel with 49-language picker, extended Rust command to forward language to sidecar, fixed CSP for Google Fonts.**

## What Happened

Added `tauri-plugin-store` (Cargo + npm), registered in lib.rs, added `store:default` permission. Extended `process_files` Rust command to accept `language: Option<String>` and include it in sidecar JSON commands (defaults to "en"). Added `get_languages` Tauri command that queries the sidecar and returns the full language registry.

Fixed CSP in tauri.conf.json to allow Google Fonts (`style-src`, `font-src` directives) and Tauri IPC (`connect-src`).

Built `src/settings.ts` — a self-contained settings module that creates a collapsible panel in the header with a gear icon toggle. On init, it loads the store (or falls back to defaults), fetches languages from the sidecar via the new `get_languages` command (or falls back to English-only), and populates a `<select>` grouped by script family. Language selection is saved to the store on change. `getSelectedLanguage()` is exported for `main.ts` to read when processing files.

Wired settings into `main.ts` — `initSettings()` called at startup, `getSelectedLanguage()` read in `processDroppedPaths()` and passed to `invoke("process_files", { paths, language, channel })`.

Styled the panel to match D030 aesthetic: dark bg, DM Mono labels, amber accent on active gear, custom dropdown arrow.

Created `backend/tests/test_sidecar_language.py` with 5 tests covering language threading through the sidecar (explicit language logged, default language, invalid language error, get_languages returns 49 entries with required fields).

## Verification

- `cargo check` — compiles clean (store plugin + extended command signatures)
- `npx tsc --noEmit` — TypeScript compiles clean
- `pnpm build` — frontend builds successfully (13 modules, 29KB JS)
- `cd backend && python -m pytest tests/test_languages.py -v` — 15/15 passed
- `cd backend && python -m pytest tests/test_sidecar_language.py -v` — 5/5 passed
- `cargo tauri dev` — app launches, sidecar spawns successfully
- Browser verification: settings gear icon visible, panel opens/closes, language picker shows English (fallback in browser context), drop zone unaffected
- Slice-level: `test_languages.py` ✅, `test_sidecar_language.py` ✅, Tauri dev launch ✅, visual settings panel ✅
- Remaining slice verification: drop non-English document with selected language — requires manual UAT (language flows through pipeline per test_sidecar_language tests)

## Diagnostics

- Browser console: `[parsec-settings]` prefix for store/language events, `[parsec-ui]` for processing with language
- Rust stderr: `[parsec] process_files called with N path(s), language=XX`
- Sidecar stderr: `process_file id=X language=Y path=Z`
- Store load failure → `[parsec-settings] failed to load store, using defaults: ...`
- get_languages failure → `[parsec-settings] failed to fetch languages, using fallback: ...`

## Deviations

- Added `connect-src 'self' ipc: http://ipc.localhost` to CSP — not in original plan but required for Tauri IPC to work in production builds alongside the font directives.
- Created `get_languages` Tauri command in lib.rs — plan mentioned "invoke a new Tauri command or use the existing sidecar communication channel." Chose a dedicated command for cleaner separation.

## Known Issues

None.

## Files Created/Modified

- `src-tauri/Cargo.toml` — added `tauri-plugin-store = "2"` dependency
- `src-tauri/src/lib.rs` — registered store plugin, added `get_languages` command, extended `process_files` with `language` parameter
- `src-tauri/capabilities/default.json` — added `store:default` permission
- `src-tauri/tauri.conf.json` — updated CSP for Google Fonts and Tauri IPC
- `package.json` — added `@tauri-apps/plugin-store` dependency
- `src/settings.ts` — new, collapsible settings panel with language picker and store persistence
- `src/main.ts` — imported settings module, wired language into processDroppedPaths
- `src/styles.css` — added settings panel styles matching D030 aesthetic
- `backend/tests/test_sidecar_language.py` — new, 5 tests for sidecar language threading
