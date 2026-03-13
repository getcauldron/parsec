# S04: Multi-Language & Settings — UAT

**Milestone:** M001
**Written:** 2026-03-12

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: Backend language registry fully tested via pytest. UI settings panel and end-to-end flow need live runtime verification.

## Preconditions

- `cargo tauri dev` running (spawns sidecar automatically)
- At least one non-English test document available

## Smoke Test

Open the app, click gear icon, verify settings panel opens with language picker showing multiple languages grouped by script family.

## Test Cases

### 1. Settings panel opens and closes

1. Launch app with `cargo tauri dev`
2. Click gear icon in header
3. **Expected:** Settings panel slides open, language picker visible with English selected

4. Click gear icon again
5. **Expected:** Panel closes smoothly

### 2. Language picker shows all 49 languages

1. Open settings panel
2. Click language dropdown
3. **Expected:** Languages grouped by script (Latin, CJK, Cyrillic, etc.), ~49 entries

### 3. Language selection persists across restart

1. Open settings, select "Korean"
2. Close app (Cmd+Q)
3. Relaunch with `cargo tauri dev`
4. Open settings
5. **Expected:** Korean still selected

### 4. Selected language flows through pipeline

1. Select non-English language
2. Drop test image onto drop zone
3. Check sidecar stderr
4. **Expected:** Log shows correct language code

## Edge Cases

### Sidecar not ready on startup

1. Launch app and immediately open settings
2. **Expected:** Picker shows at least English (fallback), populates fully once sidecar connects

## Failure Signals

- Settings gear icon missing or non-functional
- Language picker empty after sidecar connected
- Language lost after restart
- Sidecar stderr shows `language=en` when different language selected
- CSP errors in console for Google Fonts

## Requirements Proved By This UAT

- R014 — Language selection with 49 languages, persistent, flowing through pipeline

## Not Proven By This UAT

- OCR quality for each non-English language
- All 49 languages producing correct output

## Notes for Tester

- Language picker may briefly show English-only on cold start — known race, not a bug
- Google Fonts should load without CSP errors
