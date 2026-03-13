# S06: End-to-End Integration Testing

**Goal:** Prove the entire Parsec system works as an integrated whole — mixed inputs process correctly through the sidecar, quality thresholds hold for all fixture types, error resilience is verified, and the milestone's Final Integrated Acceptance criteria pass.
**Demo:** A batch of mixed inputs (PNG, JPEG, PDF, skewed PDF) sent through the sidecar all produce valid searchable PDFs. A corrupt file in the batch doesn't crash the rest. CER/WER thresholds hold for PDF fixtures. TIFF pipeline works. Running `cargo tauri dev` and dropping 5 mixed files satisfies the M001 acceptance bar.

## Must-Haves

- Multi-file batch sidecar test: PNG + JPEG + PDF + skewed PDF sent sequentially through a single sidecar process, all complete successfully
- Error resilience: a corrupt/unsupported file in a batch doesn't prevent remaining files from processing
- TIFF fixture + pipeline test (closes R003 coverage gap)
- CER/WER quality benchmarks for PDF fixtures (`pdf_nosearch_01`, `pdf_skewed_01`)
- Preprocessing quality test: deskew on skewed input produces CER at least as good as without deskew
- All 73+ existing tests still pass (zero regressions)
- `cargo check` and `pnpm build` clean
- Manual Final Integrated Acceptance via `cargo tauri dev`

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes (sidecar subprocess + OCR engine for integration tests, Tauri app for acceptance)
- Human/UAT required: yes (Final Integrated Acceptance is manual — drop 5 mixed files in the running app)

## Verification

- `cd backend && .venv/bin/python -m pytest tests/test_integration.py -v` — all new integration tests pass
- `cd backend && .venv/bin/python -m pytest tests/ -v` — full suite passes, zero regressions
- `cd src-tauri && cargo check` — compiles clean
- `pnpm build` — frontend builds clean
- `cargo tauri dev` — manual: drop 5 mixed files → all produce searchable PDFs, error file shows error state, language change works

## Integration Closure

- Upstream surfaces consumed: all S01-S05 outputs — `pipeline.py`, `sidecar.py`, `languages.py`, preprocessing flags, PDF input, Tauri commands, drop zone UI, settings panel
- New wiring introduced in this slice: none — pure verification of existing wiring
- What remains before the milestone is truly usable end-to-end: nothing after this slice

## Tasks

- [x] **T01: Backend integration test suite** `est:45m`
  - Why: The existing 73 tests cover individual modules but not cross-cutting integration — no test sends multiple mixed files through a single sidecar session, no CER/WER for PDF fixtures, no TIFF coverage, no error-resilience-in-batch verification
  - Files: `backend/tests/test_integration.py`, `backend/tests/fixtures/generate_fixtures.py`
  - Do: Create `test_integration.py` with: (1) multi-file batch sidecar test sending PNG + JPEG + PDF + skewed PDF sequentially via `_run_sidecar()` with 180s timeout, filtering responses by `id` and asserting all reach `complete` stage, (2) error resilience test including a corrupt file in the batch and verifying remaining files still complete, (3) TIFF fixture generation in `generate_fixtures.py` + TIFF pipeline test, (4) PDF fixture CER/WER benchmarks using `measure_quality()` with generous thresholds (CER < 0.10 for pdf category), (5) preprocessing quality test comparing deskew=True vs without on skewed fixture (assert CER with deskew ≤ CER without + small epsilon), (6) language threading integration test verifying non-English language code flows through sidecar correctly. Use existing `_run_sidecar()` helper, `measure_quality()`, and `_create_test_image()` patterns. Mark slow sidecar tests with `@pytest.mark.slow`. Skip `clean=True` tests if `unpaper` is absent.
  - Verify: `cd backend && .venv/bin/python -m pytest tests/test_integration.py -v` passes all tests
  - Done when: all new integration tests pass, existing 73 tests still pass

- [x] **T02: Full-stack verification and milestone acceptance** `est:30m`
  - Why: Closes M001 by running the complete test suite, verifying the app end-to-end via `cargo tauri dev`, and writing completion artifacts (S06-SUMMARY, M001-SUMMARY, STATE.md updates, roadmap checkbox)
  - Files: `backend/tests/`, `.gsd/milestones/M001/slices/S06/S06-SUMMARY.md`, `.gsd/milestones/M001/M001-SUMMARY.md`, `.gsd/milestones/M001/M001-ROADMAP.md`, `.gsd/STATE.md`, `.gsd/milestones/M001/slices/S05/S05-SUMMARY.md`
  - Do: (1) Run full backend test suite and record results, (2) verify `cargo check` and `pnpm build` are clean, (3) launch `cargo tauri dev` and perform Final Integrated Acceptance — drop 5 mixed files (PNG, JPEG, TIFF, non-searchable PDF, skewed PDF), verify all produce searchable PDFs, change language, drop corrupt file and verify error state, (4) regenerate S05-SUMMARY.md from its task summaries (replacing the doctor placeholder), (5) write S06-SUMMARY.md, (6) write M001-SUMMARY.md, (7) mark S06 complete in roadmap, (8) update STATE.md
  - Verify: all tests pass, `cargo check` clean, `pnpm build` clean, acceptance criteria met visually
  - Done when: M001 milestone is fully documented and all acceptance criteria verified

## Files Likely Touched

- `backend/tests/test_integration.py` (created)
- `backend/tests/fixtures/generate_fixtures.py` (TIFF fixture generation)
- `.gsd/milestones/M001/slices/S06/S06-SUMMARY.md`
- `.gsd/milestones/M001/slices/S05/S05-SUMMARY.md`
- `.gsd/milestones/M001/M001-SUMMARY.md`
- `.gsd/milestones/M001/M001-ROADMAP.md`
- `.gsd/STATE.md`
