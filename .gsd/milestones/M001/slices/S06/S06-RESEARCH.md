# S06: End-to-End Integration Testing — Research

**Date:** 2026-03-12

## Summary

S06 is the final verification slice for M001. It needs to prove the entire system works as a whole — mixed inputs (images, PDFs, multi-language, skewed, corrupt) all process correctly through the sidecar, quality thresholds hold, and error handling is verified. The existing test surface is solid at the unit and module level (73 tests across 6 files) but has clear gaps at the integration and end-to-end level.

The main work is: (1) a sidecar-level batch integration test sending multiple mixed files in sequence and verifying all complete correctly, (2) extending CER/WER quality benchmarks to cover PDF fixtures, (3) a TIFF fixture to cover the R003 gap, (4) error-resilience testing (bad file in a batch doesn't crash the rest), (5) preprocessing quality validation (deskew actually improves CER on skewed input), and (6) running the full app with `cargo tauri dev` for the milestone's Final Integrated Acceptance (manual, as Tauri webview automation isn't practical).

No new libraries are needed. No architectural changes required. This is pure test authoring using the existing patterns.

## Recommendation

Organize S06 into two tasks:

**T01: Backend integration test suite** — A new `test_integration.py` file with:
- Multi-file batch sidecar test (PNG + JPEG + PDF + skewed PDF sent sequentially, all must complete)
- Error resilience test (batch with a corrupt/unsupported file, remaining files still process)
- TIFF fixture generation + pipeline test
- PDF quality benchmark (CER/WER on `pdf_nosearch_01` and `pdf_skewed_01` fixtures)
- Preprocessing quality test (skewed fixture with deskew=True should produce lower CER than without)
- Language threading integration (non-English language code flows through sidecar → pipeline correctly)

**T02: Full-stack verification + milestone acceptance** — Run `cargo tauri dev`, visually verify the Final Integrated Acceptance criteria from M001-CONTEXT.md, run the full backend test suite (existing + new), verify `cargo check` and `pnpm build` still pass, and write the S06 and M001 summaries.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Sidecar subprocess testing | `_run_sidecar()` in `test_sidecar.py` | Battle-tested helper that handles stdin/stdout NDJSON, already used by 18 tests |
| CER/WER measurement | `measure_quality()` in `test_quality.py` | Handles normalization, empty recognition edge case, returns structured result |
| Fixture generation | `generate_fixtures.py` | Existing Pillow-based generators for clean/multicol/degraded/PDF images |
| PDF text extraction | `pdfminer.high_level.extract_text()` | Already used in pipeline tests to verify text layers |
| Session-scoped engine | `conftest.py` engine fixture | Avoids 4s cold start per test |

## Existing Code and Patterns

- `backend/tests/test_sidecar.py` — `_run_sidecar()` helper sends NDJSON lines and collects parsed responses. Extend for multi-command batch tests. Pattern: send commands → collect responses → filter by `type=="progress"` → assert stages.
- `backend/tests/test_quality.py` — `_discover_fixtures()` auto-discovers `{category}_*.png` files by glob. PDF fixtures use different naming (`pdf_nosearch_01.pdf`), so either add a `pdf` category or parametrize manually.
- `backend/tests/conftest.py` — Session-scoped `PaddleOcrEngine` fixture avoids repeated cold starts. Integration tests that call the sidecar subprocess don't need this (sidecar manages its own engine).
- `backend/tests/test_pipeline.py` — `_create_test_image()` helper generates test images with Pillow. Reuse for TIFF fixture generation.
- `backend/parsec/sidecar.py` — Sidecar processes files sequentially. Multi-file batch test must send multiple `process_file` commands and collect interleaved progress events, filtering by `id`.
- `src/main.ts` — Frontend exposes `__parsec_test.processDroppedPaths` in DEV mode, but using it requires a running Tauri app. Manual verification is more practical for T02.

## Constraints

- **Sidecar tests are slow** — each `_run_sidecar()` call spawns a Python subprocess, and `process_file` with real OCR takes 5-15s per file. A 5-file batch test will run ~60s. Mark with `@pytest.mark.slow` or similar.
- **No Tauri integration test framework** — Tauri v2 has no official headless test harness for the full app (webview + sidecar). The Final Integrated Acceptance is necessarily manual or semi-automated via `cargo tauri dev` + browser tools.
- **PaddleOCR is single-threaded** (`jobs=1`) — sidecar processes files sequentially, so multi-file tests must account for cumulative time.
- **`clean` preprocessing requires `unpaper` binary** — tests using `clean=True` may skip if `unpaper` is not installed. Don't make the integration suite depend on it.
- **OCRmyPDF multiprocessing on macOS** — test files need `if __name__ == '__main__'` guard (already established pattern).
- **S05 summary is a placeholder** — doctor-created stub. The task summaries are authoritative. S06 should not depend on S05-SUMMARY.md content.

## Common Pitfalls

- **Interleaved progress events in batch tests** — Multiple `process_file` commands sent sequentially still produce interleaved stdout events. Must filter by `id` field, not by order. The existing `_run_sidecar()` returns all responses flat.
- **Flaky CER/WER thresholds on PDF fixtures** — PDF fixtures are derived from clean_01.png. The PDF→image→OCR roundtrip may introduce artifacts that inflate error rates. Set generous thresholds (e.g., CER < 0.10 for PDF category) and tighten after initial measurement.
- **TIFF save format** — Pillow's `Image.save()` with format="TIFF" works, but OCRmyPDF may treat TIFF DPI metadata differently. Explicitly set DPI in the save call.
- **Timeout in multi-file sidecar tests** — Default 10s timeout in `_run_sidecar()` is too short for batch processing. Use 180s+ for multi-file tests.
- **Engine cold start in first sidecar test** — First `process_file` triggers ~4s engine init. Batch tests hitting the sidecar will pay this once; subsequent files are warm.

## Open Risks

- **PDF quality thresholds unknown** — No existing CER/WER data for PDF fixtures. Need to measure first, then set thresholds. If the PDF→image roundtrip degrades quality significantly, the threshold may be close to the degraded category (CER < 0.15).
- **Deskew effectiveness on synthetic skewed fixtures** — The `pdf_skewed_01.pdf` fixture has a 3° rotation. OCRmyPDF's deskew may or may not improve CER meaningfully on such a small skew. If the delta is negligible, the test should assert "at least not worse" rather than "strictly better."
- **TIFF pipeline coverage** — R003 lists TIFF support but it has never been tested. Should be straightforward (OCRmyPDF handles it), but worth verifying with a fixture.
- **Full-stack manual verification scope** — M001 Final Integrated Acceptance requires dropping 5 mixed files in the running app. This is inherently manual. Risk of regression between test suite pass and manual verification is low but nonzero.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Tauri v2 | `nodnarbnitram/claude-code-extensions@tauri-v2` | available (2.3K installs) — useful for Tauri-specific patterns but not critical for test authoring |
| pytest | `github/awesome-copilot@pytest-coverage` | available (7K installs) — coverage-focused, not needed for integration test design |

No skills are essential for this slice. The work is test authoring in established patterns.

## Sources

- Existing codebase: 73 tests across 6 files, sidecar subprocess testing pattern, CER/WER framework, fixture generation
- M001-CONTEXT.md: Final Integrated Acceptance criteria define the acceptance bar
- S04-SUMMARY.md: Language threading works through sidecar, 49 languages
- S05 task summaries: PDF input + preprocessing flags wired through entire stack
- D034: No separate `pdf_input.py` or `preprocessing.py` — OCRmyPDF handles everything natively
- D036: Preprocessing toggles default off — tests should verify both on and off states
