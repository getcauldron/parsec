# S04: Multi-Language & Settings — Research

**Date:** 2026-03-12

## Summary

S04 adds language selection and a settings panel to the existing drop-and-go pipeline. The plumbing is straightforward — the hardest part is already done by the `ocrmypdf_paddleocr` plugin, which has a built-in `lang_map.py` with 49 Tesseract→PaddleOCR mappings and handles engine reinitialization on language change. The work breaks into four layers: a backend language registry (mapping user-facing names to the short codes the pipeline uses), sidecar protocol extension to carry language through, Rust-side forwarding of the language field, and a frontend settings panel with a language picker and persistence via Tauri's store plugin.

The main subtlety is that switching languages triggers PaddleOCR model download (~8-80MB) and engine reinitialization (~4-5s). The user needs to know this will happen. The settings panel should be collapsible (R014 says "should not interfere with the minimal default experience") and persist across sessions via `@tauri-apps/plugin-store`.

## Recommendation

Thread language through the existing pipeline without redesigning it. The chain is: **user picks display language → frontend stores short code → sidecar command includes `language` field → pipeline passes to OcrOptions → ocrmypdf passes Tesseract code → plugin converts to PaddleOCR code**. The plugin already handles the Tesseract→PaddleOCR mapping, so we only need to maintain short-code→Tesseract in `pipeline.py` (already has 12 entries, extend to cover all 49 plugin-supported languages).

Build a `backend/parsec/languages.py` module with the full language registry (display name, short code, script group) — this serves both the UI (language picker list) and the pipeline (validation). Expose it via a new sidecar command `get_languages` so the frontend can populate the picker dynamically.

Use Tauri's `@tauri-apps/plugin-store` for settings persistence — it's the official v2 approach, handles serialization, and auto-saves. No need to build custom persistence.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Settings persistence | `@tauri-apps/plugin-store` | Official Tauri v2 plugin, auto-save, key-value API, handles app data paths |
| Tesseract→PaddleOCR lang mapping | `ocrmypdf_paddleocr.lang_map` | Already installed, 49 languages mapped, used by the plugin internally |
| Language validation | Plugin's `SUPPORTED_LANGUAGES` set | Authoritative source of what the engine can actually process |

## Existing Code and Patterns

- `backend/parsec/pipeline.py` — `_LANG_TO_TESSERACT` map (12 entries) converts short codes to Tesseract codes; `process_file()` accepts `OcrOptions` with `language` field. Extend map to 49 entries.
- `backend/parsec/models.py` — `OcrOptions(language="en")` already carries language. No changes needed.
- `backend/parsec/sidecar.py` — `_handle_process_file()` currently ignores language. Must read `language` from command JSON and pass to `process_file()` via `OcrOptions`.
- `backend/.venv/.../ocrmypdf_paddleocr/lang_map.py` — Authoritative mapping of 49 Tesseract codes to PaddleOCR codes. Plugin re-creates PaddleOCR engine when language changes (see `_get_paddle_engine()`).
- `backend/.venv/.../ocrmypdf_paddleocr/engine.py` — `_get_paddle_engine()` caches engine instance, reinitializes when language changes. This causes a ~4-5s pause per language switch.
- `src/main.ts` — File processing via `invoke("process_files", { paths, channel })`. Must extend to pass `language` option.
- `src-tauri/src/lib.rs` — `process_files` command takes `paths` and `channel`. Must extend to accept `language` parameter and include it in sidecar commands.
- `src-tauri/src/sidecar.rs` — `send_command()` writes arbitrary JSON to sidecar stdin. No changes needed — just construct command with language field.
- `index.html` — Header with app title and sidecar status. Settings panel goes in the header area or as a sidebar.
- `src/styles.css` — Dark industrial theme (D030). Settings panel must follow established color/typography tokens.

## Constraints

- **CSP blocks Google Fonts** — The current CSP (`default-src 'self'; script-src 'self'`) blocks the Google Fonts stylesheets and font files loaded in `index.html`. This is a pre-existing issue from S03 (fonts may load in dev mode but fail in production builds). Must update CSP to add `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com` and `font-src https://fonts.gstatic.com`. Alternatively, bundle fonts locally.
- **Plugin supports 49 languages, not 80+** — The `ocrmypdf_paddleocr` plugin maps 49 Tesseract codes. PaddleOCR itself supports ~90+ via different script-family models (Latin, Cyrillic, Arabic, Devanagari). To reach 80+, we'd need to extend the plugin's lang_map or bypass it. For S04, targeting the 49 plugin-supported languages is practical and honest. R007 says "80+ languages" — flag this gap but don't block on it.
- **Language switch triggers model download** — Switching from English to, say, Korean causes PaddleOCR to download ~8-80MB of recognition models on first use. Downloads happen silently in `paddleocr.PaddleOCR(lang=...)` constructor. No progress callback available. UX should warn user or at minimum show "initializing" stage.
- **Language switch causes engine reinitialization** — The plugin caches one engine instance. Changing language drops the old engine and creates a new one (~4-5s). This is acceptable for a settings change (not per-file).
- **Detection model is language-agnostic** — PP-OCRv5_server_det (84MB) is shared across all languages. Only the recognition model changes per language. Already downloaded.
- **Store plugin requires Cargo + npm dependency** — Must add `tauri-plugin-store` to Cargo.toml and `@tauri-apps/plugin-store` to package.json, plus register the plugin in `lib.rs` and add `store:default` permission.
- **No framework** — Frontend is vanilla TypeScript/HTML. Settings panel must be built with DOM APIs, matching the pattern in `main.ts`. No React/Svelte/etc.

## Common Pitfalls

- **Forgetting to thread language through all layers** — Language must flow: frontend → Tauri command → sidecar JSON → OcrOptions → ocrmypdf `language=[...]`. Missing any layer silently defaults to English. Test with a non-Latin language (e.g., Chinese or Korean) to catch this.
- **Incomplete `_LANG_TO_TESSERACT` map** — If a user picks a language that's in the UI list but not in `_LANG_TO_TESSERACT`, the raw short code passes through as-is to OCRmyPDF, which may reject it. Must keep the map in sync with the language registry.
- **Store not initialized before first read** — `load('settings.json')` is async. If the user drops a file before the store loads, the language defaults to English silently. Load store eagerly at app start and block processing until ready.
- **CSP breaking fonts in production** — Dev mode with Vite may proxy/serve differently than the production Tauri webview. Test with `cargo tauri build` or at minimum verify the CSP allows font loading.
- **Settings panel fighting the drop zone** — The drop zone listens for drag events on the whole window. A settings panel that overlaps or interferes could capture drag events. Keep settings in the header area or use a collapsible sidebar that doesn't cover the drop zone.

## Open Risks

- **49 vs 80+ language gap** — The plugin only maps 49 languages. Reaching R007's "80+ languages" claim requires either extending `ocrmypdf_paddleocr`'s `lang_map.py` (which we don't own) or creating our own extended mapping that bypasses the plugin's validation. For S04, ship 49 languages and document the gap. Can extend in S06 or a follow-up.
- **Model download failures** — If the user is offline or has restricted network access, switching to an unsupported language will fail during PaddleOCR initialization. The error will surface as a pipeline error, but the message may be cryptic (PaddlePaddle download errors). Consider catching and wrapping this.
- **PaddleOCR engine re-creation on every language change** — The plugin's `_get_paddle_engine()` only caches one language. If a user switches back and forth, each switch pays the init cost. Acceptable for a settings-level change, but worth noting.
- **Google Fonts loading** — If fonts are blocked by CSP in production, the UI falls back to system fonts. Functional but visually different from the dev experience. Low severity but worth fixing in this slice since we're touching the UI.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Tauri v2 | `nodnarbnitram/claude-code-extensions@tauri-v2` | available (2.3K installs) |
| Tauri v2 | `martinholovsky/claude-skills-generator@tauri` | available (233 installs) |
| Frontend UI | `frontend-design` | installed |

The `nodnarbnitram/claude-code-extensions@tauri-v2` skill (2.3K installs) could be useful for Tauri-specific patterns. The `frontend-design` skill is already installed and should be loaded for the settings panel UI work.

## Sources

- `ocrmypdf_paddleocr` plugin source (installed at `.venv/lib/python3.13/site-packages/ocrmypdf_paddleocr/`) — lang_map.py has 49 language mappings; engine.py shows PaddleOCR engine caching per language
- PaddleOCR `_pipelines/ocr.py` source — `_get_ocr_model_names()` defines LATIN_LANGS, ARABIC_LANGS, ESLAV_LANGS, CYRILLIC_LANGS, DEVANAGARI_LANGS covering 90+ codes
- Tauri Store plugin docs (source: Context7 /tauri-apps/tauri-docs) — `@tauri-apps/plugin-store` provides `load()`, `set()`, `get()` for persistent key-value storage
- Tauri CSP configuration docs (source: Context7 /tauri-apps/tauri-docs) — CSP can use object format with per-directive arrays, including `font-src` and `style-src`
- `~/.paddlex/official_models/` — current models: det (84MB shared), server_rec (81MB), en_mobile_rec (7.7MB). Non-English languages will download additional rec models.
