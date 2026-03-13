---
id: T01
parent: S03
milestone: M001
provides:
  - process_file sidecar command with progress events and request-ID correlation
  - File extension validation in sidecar protocol
  - Output path computation (_ocr.pdf suffix)
  - engine_ready status tracking
key_files:
  - backend/parsec/sidecar.py
  - backend/tests/test_sidecar.py
key_decisions:
  - Refactored _handle_command to call _send() directly instead of returning a dict, enabling multi-message commands (progress events)
  - stdout redirected to /dev/null during pipeline execution as defense-in-depth against C++ noise
  - Lazy pipeline import inside _handle_process_file to avoid loading OCRmyPDF at sidecar startup
patterns_established:
  - Progress events use {"type":"progress","id":"...","stage":"..."} shape — downstream code should match on type field
  - _SidecarState class holds mutable session state (engine_used flag) — extend this for future stateful tracking
  - All protocol responses now include "id" field (null for commands without one)
observability_surfaces:
  - process_file emits stage-based progress events on stdout (queued → initializing → processing → complete/error)
  - engine_ready field in status command reflects whether OCR has been used
  - Error stage includes pipeline error message string
duration: 20min
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T01: Extend sidecar protocol with process_file command and progress events

**Added `process_file` command to sidecar NDJSON protocol with request-ID correlation, stage-based progress events, file extension validation, and output path computation.**

## What Happened

Refactored `_handle_command` from returning a single dict to calling `_send()` directly — this enables `process_file` to emit multiple progress events during execution. Added `_SidecarState` class to track whether the OCR engine has been used (controls the `initializing` stage on first file and the `engine_ready` status response field).

The `process_file` handler validates the `id` and `input_path` fields, checks file extension against the allowed set, computes the output path (`stem + _ocr.pdf`), and emits progress events through the pipeline lifecycle. Pipeline import is deferred to avoid loading OCRmyPDF at sidecar startup. Stdout is redirected to `/dev/null` during pipeline execution to prevent C++ noise from corrupting the protocol.

All existing protocol responses now include the request `id` field (null for hello/status).

## Verification

- `cd backend && python -m pytest tests/test_sidecar.py -v` — **14 tests pass** (9 existing + 5 new)
- Manual: piped `process_file` command to sidecar stdin — emits `queued → initializing → processing → complete` events with correct output path and timing
- Verified no C++ noise on stdout — every line parses as valid JSON
- Verified `engine_ready` flips from `false` to `true` after first `process_file`
- Verified existing `hello`, `status`, and error handling still work unchanged

### Slice-level verification (partial — T01 of 3):
- ✅ `cd backend && python -m pytest tests/test_sidecar.py -v` — all existing + new process_file tests pass
- ⬜ `cargo tauri dev` → drop a test image → `_ocr.pdf` appears (T02/T03)
- ⬜ Progress events stream to UI (T03)
- ⬜ Drop unsupported file type → validation error in UI (T03)
- ⬜ Drop multiple images → sequential processing (T02/T03)

## Diagnostics

Pipe JSON commands to sidecar stdin, read progress events from stdout:
```
echo '{"cmd":"process_file","id":"test-1","input_path":"path/to/image.png"}' | python -u -m parsec.sidecar
```
Progress events: `{"type":"progress","id":"...","stage":"queued|initializing|processing|complete|error"}`
Complete event includes `output_path` and `duration`. Error event includes `error` message string.

## Deviations

- Removed a dead `with_suffix("_ocr.pdf")` call that crashed (Python's `Path.with_suffix` rejects suffixes with underscores). Replaced with simple string concatenation `stem + "_ocr.pdf"` which was the intended approach.

## Known Issues

None.

## Files Created/Modified

- `backend/parsec/sidecar.py` — Added `process_file` handler, `_SidecarState`, request-ID correlation on all responses, stdout protection during pipeline execution
- `backend/tests/test_sidecar.py` — Added 5 tests: happy_path, missing_file, unsupported_extension, id_correlation, output_path
