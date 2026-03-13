---
estimated_steps: 5
estimated_files: 2
---

# T01: Extend sidecar protocol with process_file command and progress events

**Slice:** S03 — Drop-and-Go Pipeline
**Milestone:** M001

## Description

Add the `process_file` command to the sidecar's NDJSON protocol. This is the bridge between the Tauri shell and the OCR pipeline — it receives a file path, validates the extension, computes the output path (`_ocr.pdf` suffix next to the original), runs `pipeline.process_file()`, and emits stage-based progress events throughout. All messages carry a request `id` for correlation. The sidecar processes files synchronously (PaddleOCR is single-threaded), so there's no concurrency to manage here — but the protocol must support the Rust layer sending multiple requests.

## Steps

1. Add request-ID correlation to the protocol. Every response/event includes the `id` from the incoming command (or `null` for commands without one like `hello`/`status`). Update `_handle_command` signature to return a list of messages (for progress events) or refactor to allow streaming via `_send()` during command handling.
2. Implement `process_file` command handler:
   - Validate required fields: `input_path` required, `id` required
   - Validate file extension against allowed set (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`)
   - Compute output path: strip extension, append `_ocr.pdf` (e.g. `scan.png → scan_ocr.pdf`)
   - Emit `{"type":"progress","id":"...","stage":"queued"}` immediately
   - Emit `{"type":"progress","id":"...","stage":"initializing"}` if PaddleOCR hasn't been used yet (first file)
   - Emit `{"type":"progress","id":"...","stage":"processing"}` before calling pipeline
   - Call `pipeline.process_file(input_path, output_path)`
   - Emit final `{"type":"progress","id":"...","stage":"complete","output_path":"...","duration":N}` or `{"type":"progress","id":"...","stage":"error","error":"..."}`
3. Handle the "initializing" detection: track whether the engine has been used before (simple boolean flag). First `process_file` emits `initializing` stage. Subsequent files skip it.
4. Ensure stdout cleanliness: `pipeline.process_file()` calls OCRmyPDF which loads PaddleOCR — verify no C++ noise leaks to stdout. The existing suppression in `sidecar_entry.py` and `paddle_engine.py` should handle this, but add a `redirect_stdout` context manager around the pipeline call as defense in depth.
5. Write tests in `test_sidecar.py`:
   - `test_process_file_happy_path` — send process_file with a real fixture image, verify progress events stream (queued → processing → complete), verify `_ocr.pdf` exists on disk
   - `test_process_file_missing_file` — nonexistent path → error stage with descriptive message
   - `test_process_file_unsupported_extension` — `.txt` file → immediate error response
   - `test_process_file_id_correlation` — verify all events carry the same `id` from the request
   - `test_process_file_output_path` — verify output is named correctly (`scan.png → scan_ocr.pdf`)

## Must-Haves

- [ ] `process_file` command accepts `{cmd, id, input_path}` and produces a searchable PDF
- [ ] All protocol messages include the request `id` field
- [ ] Stage-based progress events emitted: queued → [initializing] → processing → complete/error
- [ ] Output path computed as `_ocr.pdf` suffix next to original (R008)
- [ ] File extension validation rejects non-image files with error event
- [ ] Existing `hello` and `status` commands still work
- [ ] No C++ noise on stdout during OCR processing

## Verification

- `cd backend && python -m pytest tests/test_sidecar.py -v` — all tests pass (existing 9 + new ~5)
- Manual: `echo '{"cmd":"process_file","id":"test-1","input_path":"tests/fixtures/clean_01.png"}' | python -u -m parsec.sidecar` — emits progress events and produces `clean_01_ocr.pdf`

## Observability Impact

- Signals added: `process_file` progress events on stdout with `type`, `id`, `stage` fields
- How a future agent inspects this: pipe JSON commands to sidecar stdin, read progress events from stdout
- Failure state exposed: `stage: "error"` with `error` field containing the pipeline's error message

## Inputs

- `backend/parsec/sidecar.py` — existing protocol loop with `_handle_command()` dispatch
- `backend/parsec/pipeline.py` — `process_file(input_path, output_path, options)` → `ProcessResult`
- `backend/parsec/models.py` — `ProcessResult` with `success`, `error`, `duration_seconds`
- `backend/tests/fixtures/clean_01.png` — test image for happy-path test
- `backend/tests/test_sidecar.py` — existing 9 tests to keep passing

## Expected Output

- `backend/parsec/sidecar.py` — extended with `process_file` handler, request-ID correlation, progress event streaming
- `backend/tests/test_sidecar.py` — extended with ~5 new tests covering `process_file` scenarios
- Proven: sidecar processes an image file and produces a searchable PDF via the NDJSON protocol
