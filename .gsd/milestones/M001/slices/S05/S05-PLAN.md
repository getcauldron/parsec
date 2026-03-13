# S05: PDF Input + Preprocessing

**Goal:** Dropping a skewed non-searchable PDF produces a deskewed searchable PDF with improved OCR accuracy. Preprocessing toggles (deskew, rotate, clean) are exposed in settings.
**Demo:** Drop a non-searchable PDF and a skewed image onto the app → both produce searchable PDFs. Toggle deskew on, drop a skewed input → improved OCR output. Already-searchable PDFs are handled gracefully.

## Must-Haves

- PDF files (`.pdf`) accepted as input in both frontend and sidecar
- Already-searchable PDFs handled via `skip_text=True` (OCR only non-text pages)
- Encrypted/password-protected PDFs surface a clear error message
- `OcrOptions` extended with `deskew`, `rotate_pages`, `clean`, `skip_text`, `force_ocr`
- Pipeline passes preprocessing flags through to `ocrmypdf.ocr()`
- Sidecar reads preprocessing options from command JSON
- Rust `process_files` command forwards preprocessing options to sidecar
- Settings UI has preprocessing toggles (deskew, rotate pages, clean) with persistence
- Frontend sends preprocessing options with `process_files` invocation
- Non-searchable PDF test fixture generated and quality tested

## Proof Level

- This slice proves: integration (PDF + preprocessing through full pipeline)
- Real runtime required: yes (OCRmyPDF must actually process PDFs and apply preprocessing)
- Human/UAT required: no (automated tests cover pipeline; visual spot-check optional)

## Verification

- `cd backend && python -m pytest tests/test_pipeline_pdf.py -v` — PDF input tests pass (non-searchable PDF → searchable, already-searchable handled, encrypted rejected)
- `cd backend && python -m pytest tests/test_sidecar.py -v` — existing + new sidecar tests pass (PDF extension accepted, preprocessing options forwarded)
- `cd backend && python -m pytest tests/ -v` — all backend tests pass
- `cd src-tauri && cargo check` — compiles clean with extended command signature
- `pnpm build` — TypeScript builds clean
- `cargo tauri dev` → settings panel shows preprocessing toggles → drop a PDF → searchable PDF produced

## Observability / Diagnostics

- Runtime signals: sidecar stderr logs preprocessing options and PDF handling mode per file; pipeline logs `skip_text`/`force_ocr` mode
- Inspection surfaces: `echo '{"cmd":"process_file","id":"t","input_path":"test.pdf","deskew":true}' | python -m parsec.sidecar` — verify preprocessing passthrough
- Failure visibility: encrypted PDF → `stage: "error"` with `"Encrypted PDF"` message; missing `unpaper` → error with clear dependency message
- Redaction constraints: none

## Integration Closure

- Upstream surfaces consumed: `process_files` command (S03), settings module (S04), pipeline + sidecar (S01/S03)
- New wiring introduced: preprocessing options threaded through settings → invoke → Rust → sidecar → pipeline → OCRmyPDF kwargs; `.pdf` added to both extension gates
- What remains before the milestone is truly usable end-to-end: S06 (integration testing across mixed inputs)

## Tasks

- [x] **T01: Extend backend + Rust with PDF support and preprocessing flags** `est:45m`
  - Why: Backend pipeline, sidecar protocol, and Rust command must all accept PDFs and thread preprocessing options before the UI can use them
  - Files: `backend/parsec/models.py`, `backend/parsec/pipeline.py`, `backend/parsec/sidecar.py`, `src-tauri/src/lib.rs`, `backend/tests/test_pipeline_pdf.py`, `backend/tests/fixtures/generate_fixtures.py`
  - Do: Extend `OcrOptions` with preprocessing booleans. Extend pipeline to pass `deskew`, `rotate_pages`, `clean`, `clean_final`, `skip_text`, `force_ocr` to `ocrmypdf.ocr()`. Handle `ExitCode.already_done_ocr` as success when `skip_text` is active. Handle `ExitCode.encrypted_pdf` with clear error. Add `.pdf` to sidecar `ALLOWED_EXTENSIONS`. Read preprocessing options from sidecar command JSON. Apply `skip_text=True` default for PDF inputs. Extend Rust `process_files` signature with optional preprocessing params and forward in sidecar JSON. Generate non-searchable PDF fixture (image-in-PDF) and skewed variant. Write `test_pipeline_pdf.py`.
  - Verify: `cd backend && python -m pytest tests/test_pipeline_pdf.py tests/test_sidecar.py -v` passes; `cd src-tauri && cargo check` clean
  - Done when: pipeline processes non-searchable PDFs, handles already-searchable gracefully, rejects encrypted PDFs, and preprocessing flags reach `ocrmypdf.ocr()` kwargs

- [x] **T02: Add preprocessing toggles to settings UI and wire PDF acceptance in frontend** `est:30m`
  - Why: Users need to enable/disable preprocessing and drop PDFs — both require frontend changes wired to the extended backend
  - Files: `src/main.ts`, `src/settings.ts`, `src/styles.css`
  - Do: Add `.pdf` to `ACCEPTED_EXTENSIONS` in main.ts. Extend settings module with three toggles (deskew, rotate pages, clean) in a "Preprocessing" group below the language picker. Persist toggle state via store plugin. Export a `getPreprocessingOptions()` function. Wire `processDroppedPaths` to read preprocessing options and pass them through `invoke("process_files", ...)`. Match existing D030 aesthetic for toggle styling.
  - Verify: `pnpm build` clean; `cargo tauri dev` → toggles visible in settings, PDF files accepted in drop zone, preprocessing options logged in sidecar stderr
  - Done when: PDFs can be dropped and processed, preprocessing toggles persist across restarts, options flow from UI through to sidecar

## Files Likely Touched

- `backend/parsec/models.py`
- `backend/parsec/pipeline.py`
- `backend/parsec/sidecar.py`
- `backend/tests/test_pipeline_pdf.py`
- `backend/tests/fixtures/generate_fixtures.py`
- `src-tauri/src/lib.rs`
- `src/main.ts`
- `src/settings.ts`
- `src/styles.css`
