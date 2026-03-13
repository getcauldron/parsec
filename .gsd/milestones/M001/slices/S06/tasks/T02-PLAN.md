---
estimated_steps: 5
estimated_files: 6
---

# T02: Full-stack verification and milestone acceptance

**Slice:** S06 — End-to-End Integration Testing
**Milestone:** M001

## Description

Close M001 by running the complete test suite, performing the Final Integrated Acceptance via `cargo tauri dev`, replacing the S05 placeholder summary, and writing S06 and M001 completion artifacts. This is the final task of the milestone.

## Steps

1. Run the full backend test suite (`python -m pytest tests/ -v`) and record the total count and pass/fail result. Run `cargo check` and `pnpm build` to confirm no regressions.
2. Regenerate `S05-SUMMARY.md` from its T01 and T02 task summaries, replacing the doctor-created placeholder with real content following the summary template.
3. Launch `cargo tauri dev` and perform Final Integrated Acceptance: (a) drop 5 mixed files — PNG, JPEG, TIFF, non-searchable PDF, skewed PDF — and verify all 5 produce `_ocr.pdf` files next to originals, (b) change language to a non-English language and drop a document, (c) drop a corrupt/unsupported file and verify error state in UI without crashing other files.
4. Write `S06-SUMMARY.md` with verification results, files created/modified, decisions made, and forward intelligence for M002.
5. Mark S06 complete in `M001-ROADMAP.md`, write `M001-SUMMARY.md` summarizing the milestone, and update `STATE.md` to reflect M001 completion.

## Must-Haves

- [ ] Full backend test suite passes (80+ tests, zero failures)
- [ ] `cargo check` and `pnpm build` clean
- [ ] Final Integrated Acceptance performed and documented
- [ ] S05-SUMMARY.md regenerated from task summaries (no longer placeholder)
- [ ] S06-SUMMARY.md written
- [ ] M001-SUMMARY.md written
- [ ] STATE.md updated
- [ ] M001-ROADMAP.md S06 checkbox marked complete

## Verification

- `cd backend && .venv/bin/python -m pytest tests/ -v` — all pass
- `cd src-tauri && cargo check` — clean
- `pnpm build` — clean
- Visual verification via `cargo tauri dev` documented in S06-SUMMARY.md

## Inputs

- `backend/tests/test_integration.py` — new integration tests from T01
- `.gsd/milestones/M001/slices/S05/tasks/T01-SUMMARY.md` — S05 T01 authoritative summary
- `.gsd/milestones/M001/slices/S05/tasks/T02-SUMMARY.md` — S05 T02 authoritative summary
- `~/.gsd/agent/extensions/gsd/templates/summary.md` — summary template format

## Expected Output

- `.gsd/milestones/M001/slices/S05/S05-SUMMARY.md` — regenerated from task summaries
- `.gsd/milestones/M001/slices/S06/S06-SUMMARY.md` — slice completion summary
- `.gsd/milestones/M001/M001-SUMMARY.md` — milestone completion summary
- `.gsd/milestones/M001/M001-ROADMAP.md` — S06 checkbox marked `[x]`
- `.gsd/STATE.md` — updated to reflect M001 complete
