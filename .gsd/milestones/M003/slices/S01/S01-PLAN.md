# S01: Fast CI & Repo Hygiene

**Goal:** Every PR push runs fast CI (ruff, tsc, cargo check/clippy) and the repo has standard open-source hygiene files (LICENSE, README, CONTRIBUTING, issue/PR templates).
**Demo:** Push a commit to a PR branch → fast CI workflow runs green within 5 minutes. Repo root contains LICENSE (MIT), README with build instructions, CONTRIBUTING guide, and `.github/` has issue templates and PR template.

## Must-Haves

- Ruff config in `backend/pyproject.toml` with clean baseline (no violations)
- Cargo clippy passes with zero warnings
- TypeScript `tsc --noEmit` passes (already clean — must stay clean)
- `.github/workflows/ci.yml` fast CI workflow: triggers on PR push, runs ruff, tsc, cargo check + clippy
- `LICENSE` — MIT
- `README.md` — project description, architecture overview, build prerequisites, build/run instructions
- `CONTRIBUTING.md` — clone-to-PR guide, linting expectations, PR conventions
- `.github/ISSUE_TEMPLATE/bug_report.md` and `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/pull_request_template.md`

## Verification

- `cd backend && python3 -m ruff check .` exits 0
- `cd src-tauri && cargo clippy --all-targets -- -D warnings` exits 0
- `npx tsc --noEmit` exits 0
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` parses without error (or equivalent YAML validation)
- All hygiene files exist: `LICENSE`, `README.md`, `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, `.github/pull_request_template.md`
- CI workflow contains jobs for ruff, tsc, and cargo clippy with correct trigger on `pull_request`

## Tasks

- [x] **T01: Add linter configs and fix all lint violations** `est:30m`
  - Why: CI can't enforce lint rules until the codebase passes them. Ruff has no config yet, clippy has 2 warnings. Establishing a clean baseline is prerequisite to the CI workflow.
  - Files: `backend/pyproject.toml`, `src-tauri/src/lib.rs`
  - Do: Add `[tool.ruff]` config to pyproject.toml (target py310, select sensible defaults). Install ruff in backend venv. Run ruff and fix any violations. Fix the 2 clippy warnings (too_many_arguments allow, needless_borrow fix). Verify tsc still passes.
  - Verify: `ruff check backend/` exits 0, `cargo clippy --all-targets -- -D warnings` exits 0, `tsc --noEmit` exits 0
  - Done when: All three linters pass with zero errors and zero warnings

- [x] **T02: Create fast CI workflow and repo hygiene files** `est:45m`
  - Why: The slice demo — CI runs on PR push and the repo looks like a credible open-source project. Depends on T01's clean lint baseline.
  - Files: `.github/workflows/ci.yml`, `LICENSE`, `README.md`, `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, `.github/pull_request_template.md`
  - Do: Create fast CI workflow with 3 parallel jobs (python-lint, typescript-check, rust-check) using setup-python/setup-node+pnpm/setup-rust actions, pip cache, pnpm cache, cargo cache. Add concurrency group to cancel stale runs. Create MIT LICENSE. Write README with project overview, architecture (Tauri + PaddleOCR + OCRmyPDF), prerequisites, build instructions. Write CONTRIBUTING with dev setup, lint commands, PR process. Add issue templates (bug report, feature request) and PR template. Validate workflow YAML syntax.
  - Verify: YAML parses correctly, all files exist and have substantive content, workflow structure matches the 3-job design from D049
  - Done when: All hygiene files committed, CI workflow YAML valid, lint still passes

## Files Likely Touched

- `backend/pyproject.toml`
- `src-tauri/src/lib.rs`
- `.github/workflows/ci.yml`
- `LICENSE`
- `README.md`
- `CONTRIBUTING.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/pull_request_template.md`
