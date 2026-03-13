---
estimated_steps: 5
estimated_files: 4
---

# T02: Add preprocessing toggles to settings UI and wire PDF acceptance in frontend

**Slice:** S05 — PDF Input + Preprocessing
**Milestone:** M001

## Description

Add `.pdf` to the frontend's accepted extensions so PDFs can be dropped. Extend the settings panel with preprocessing toggles (deskew, rotate pages, clean) below the language picker. Persist toggle state via the Tauri store plugin. Wire `processDroppedPaths` to pass preprocessing options through `invoke("process_files", ...)` to the Rust layer.

## Steps

1. **Add `.pdf` to `ACCEPTED_EXTENSIONS` in `main.ts`** — PDFs should be accepted by the drop zone filter alongside images. Ensure the file card renders correctly for `.pdf` inputs.

2. **Add preprocessing toggles to `settings.ts`** — create a "Preprocessing" group in the settings panel with three toggle checkboxes: "Auto-deskew", "Auto-rotate pages", "Clean scan artifacts". Persist each via store plugin keys (`preprocessing_deskew`, `preprocessing_rotate`, `preprocessing_clean`). All default to `false`. Export `getPreprocessingOptions()` returning `{ deskew: boolean, rotate_pages: boolean, clean: boolean }`.

3. **Wire preprocessing options into `processDroppedPaths`** — call `getPreprocessingOptions()` alongside `getSelectedLanguage()` and pass the values to `invoke("process_files", { paths, language, channel, deskew, rotate_pages, clean })`.

4. **Style preprocessing toggles** — match D030 aesthetic. Toggle group with label and description text. Toggles use custom checkbox styling consistent with the settings panel's industrial look.

5. **Build and verify** — `pnpm build` clean; `cargo tauri dev` → open settings → toggles visible, toggle state persists on reload, dropped PDF accepted and processed.

## Must-Haves

- [ ] `.pdf` in frontend `ACCEPTED_EXTENSIONS`
- [ ] Preprocessing toggles visible in settings panel
- [ ] Toggle state persists across app restarts via store plugin
- [ ] `processDroppedPaths` sends preprocessing options in `invoke` call
- [ ] PDF files show correct cards in file list (not rejected)

## Verification

- `pnpm build` — TypeScript builds clean with no errors
- `cargo tauri dev` → open settings → three preprocessing toggles visible below language picker
- Toggle deskew on, close and reopen settings → toggle remains on
- Drop a `.pdf` file → file card appears with "queued" stage (not "rejected")
- Check sidecar stderr → preprocessing options present in process_file command

## Inputs

- `src/main.ts` — current `ACCEPTED_EXTENSIONS` and `processDroppedPaths`
- `src/settings.ts` — current settings module with language picker
- `src/styles.css` — current D030 styling
- T01 outputs — Rust `process_files` accepts `deskew`, `rotate_pages`, `clean` params

## Expected Output

- `src/main.ts` — `.pdf` in `ACCEPTED_EXTENSIONS`, preprocessing options in invoke call
- `src/settings.ts` — preprocessing toggle group, store persistence, `getPreprocessingOptions()` export
- `src/styles.css` — toggle group styling matching D030 aesthetic
