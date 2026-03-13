---
estimated_steps: 4
estimated_files: 1
---

# T01: Create full CI workflow with quality summary

**Slice:** S02 — Full OCR Quality CI
**Milestone:** M003

## Description

Write `.github/workflows/ci-full.yml` — a GitHub Actions workflow that runs the complete pytest suite (including CER/WER quality benchmarks) on every push to main and on a weekly cron schedule. The workflow must cache PaddlePaddle pip packages and PaddleOCR models aggressively to keep cached runs under ~8 minutes. After tests pass, a summary step extracts CER/WER scores and writes a Markdown table to `$GITHUB_STEP_SUMMARY` for inline visibility in the Actions UI.

## Steps

1. Write `.github/workflows/ci-full.yml` with:
   - Triggers: `push: branches: [main]` and `schedule: cron: '0 6 * * 1'` (weekly Monday 6am UTC)
   - Concurrency group: `ci-full-${{ github.ref }}` with `cancel-in-progress: true`
   - Single job on `ubuntu-latest` with `timeout-minutes: 20`
   - `actions/checkout@v4`, `actions/setup-python@v5` with python `3.10` and pip cache
   - `actions/cache@v4` for `~/.paddlex/official_models/` keyed on paddleocr version
   - `sudo apt-get install -y tesseract-ocr`
   - Pinned pip install: `paddlepaddle==3.2.2 paddleocr==3.2.0` then `pip install -e .[dev]` from backend/
   - `pytest -v -s --tb=short --junitxml=results.xml` with `PYTHONUNBUFFERED: "1"` env and `working-directory: backend`
   - Post-test step that parses CER/WER lines from pytest stdout and writes a summary table to `$GITHUB_STEP_SUMMARY`
2. Install `actionlint` locally (`brew install actionlint`)
3. Run `actionlint .github/workflows/ci-full.yml` and fix any issues
4. Verify YAML parses with Python's yaml module as a second check

## Must-Haves

- [ ] Workflow triggers on push-to-main and weekly cron
- [ ] pip cache keyed on `backend/pyproject.toml` hash
- [ ] PaddleOCR model cache at `~/.paddlex/official_models/` with stable key
- [ ] `tesseract-ocr` installed via apt
- [ ] Pinned `paddlepaddle==3.2.2` and `paddleocr==3.2.0`
- [ ] Python 3.10, `PYTHONUNBUFFERED=1`, `pytest -v -s`
- [ ] Quality summary step writes CER/WER table to `$GITHUB_STEP_SUMMARY`
- [ ] Concurrency group separate from fast CI
- [ ] `timeout-minutes: 20`
- [ ] Passes `actionlint` validation

## Verification

- `actionlint .github/workflows/ci-full.yml` exits 0
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci-full.yml'))"` succeeds
- Workflow structure manually reviewed for consistency with `ci.yml` conventions

## Inputs

- `.github/workflows/ci.yml` — S01's fast CI workflow, establishes action versions and caching patterns
- `backend/tests/test_quality.py` — CER/WER thresholds and print format (used to design summary extraction)
- `backend/pyproject.toml` — dependency versions and pytest config
- `backend/tests/conftest.py` — session-scoped engine fixture pattern
- S02 research — caching strategy, constraints, pitfalls

## Expected Output

- `.github/workflows/ci-full.yml` — complete, validated workflow file ready to run on GitHub Actions
