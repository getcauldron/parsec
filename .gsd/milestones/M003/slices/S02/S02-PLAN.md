# S02: Full OCR Quality CI

**Goal:** A merge-to-main workflow runs the full pytest suite including CER/WER quality benchmarks and surfaces scores in the GitHub Actions UI.
**Demo:** `.github/workflows/ci-full.yml` exists, passes `actionlint` validation, follows established CI conventions, and includes pip+model caching with a quality summary step.

## Must-Haves

- Workflow triggers on push-to-main and weekly cron schedule
- pip cache keyed on `pyproject.toml` hash, PaddleOCR model cache keyed on paddleocr version
- `tesseract-ocr` installed via apt
- Pinned `paddlepaddle==3.2.2` and `paddleocr==3.2.0` for CI determinism
- Python 3.10, `PYTHONUNBUFFERED=1`, `pytest -v -s`
- Quality summary table written to `$GITHUB_STEP_SUMMARY` with per-category CER/WER scores
- Separate concurrency group from fast CI (`ci-full-${{ github.ref }}`)
- `timeout-minutes: 20` for first-run safety
- Workflow passes `actionlint` validation

## Proof Level

- This slice proves: contract (workflow YAML is valid and structurally correct)
- Real runtime required: no (running the workflow requires pushing to GitHub — outward-facing)
- Human/UAT required: no

## Verification

- `actionlint .github/workflows/ci-full.yml` exits 0
- `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci-full.yml'))"` parses without error
- Manual inspection: workflow structure follows `ci.yml` conventions (concurrency group, action versions, cache patterns)

## Tasks

- [x] **T01: Create full CI workflow with quality summary** `est:45m`
  - Why: This is the entire slice — one workflow file with caching, test execution, and quality reporting
  - Files: `.github/workflows/ci-full.yml`
  - Do: Write the workflow YAML with: (1) push-to-main + weekly cron triggers, (2) separate concurrency group, (3) pip cache via setup-python + model cache via actions/cache, (4) apt install tesseract-ocr, (5) pinned pip install of paddlepaddle/paddleocr + editable backend install, (6) pytest with `-v -s` and `PYTHONUNBUFFERED=1`, (7) post-test step that parses pytest output and writes a CER/WER summary table to `$GITHUB_STEP_SUMMARY` using `--junitxml` or grep-based extraction. Install `actionlint` and validate.
  - Verify: `actionlint .github/workflows/ci-full.yml` exits 0; YAML parses cleanly
  - Done when: Workflow file exists, is valid, and covers all must-haves from this plan

## Files Likely Touched

- `.github/workflows/ci-full.yml`
