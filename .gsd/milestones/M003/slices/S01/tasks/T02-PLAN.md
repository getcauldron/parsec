---
estimated_steps: 5
estimated_files: 7
---

# T02: Create fast CI workflow and repo hygiene files

**Slice:** S01 — Fast CI & Repo Hygiene
**Milestone:** M003

## Description

Create the GitHub Actions fast CI workflow that runs on every PR push (ruff, tsc, cargo check/clippy) and add all standard open-source repo files: MIT LICENSE, README with build instructions, CONTRIBUTING guide, issue templates, and PR template. This is the slice's primary deliverable — after this, a PR push triggers lint checks and the repo presents as a credible OSS project.

## Steps

1. Create `.github/workflows/ci.yml` with:
   - Trigger: `pull_request` (all branches) and `push` to `main`
   - Concurrency group: `ci-${{ github.ref }}` with `cancel-in-progress: true`
   - Three parallel jobs: `python-lint`, `typescript-check`, `rust-check`
   - `python-lint`: ubuntu-latest, setup-python 3.10, pip cache, install ruff, run `ruff check backend/`
   - `typescript-check`: ubuntu-latest, setup-node 22, pnpm 10, `pnpm install --frozen-lockfile`, `npx tsc --noEmit`
   - `rust-check`: ubuntu-latest, install Rust stable, cargo cache (`~/.cargo/registry`, `~/.cargo/git`, `src-tauri/target`), `cargo clippy --all-targets -- -D warnings` in `src-tauri/`
   - Target total runtime under 5 minutes
2. Create `LICENSE` with MIT license text, copyright holder "Zak Keown", year 2025.
3. Create `README.md`: project name and description, what it does (desktop OCR app using PaddleOCR + OCRmyPDF via Tauri), architecture overview (Tauri Rust shell → Python sidecar → PaddleOCR engine → OCRmyPDF PDF output), prerequisites (Node 22+, pnpm 10+, Rust, Python 3.10+, system deps), build and run instructions (`pnpm install`, `pip install -e ./backend`, `pnpm tauri dev`), license badge.
4. Create `CONTRIBUTING.md`: development setup (clone, install deps), running linters (`ruff check`, `cargo clippy`, `tsc`), branch naming, PR expectations, code of conduct pointer.
5. Create `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, `.github/pull_request_template.md` with standard fields.

## Must-Haves

- [ ] `.github/workflows/ci.yml` triggers on `pull_request` and `push` to main
- [ ] CI has three parallel jobs covering Python, TypeScript, and Rust
- [ ] CI uses caching for pip, pnpm, and cargo
- [ ] Concurrency group cancels stale runs
- [ ] `LICENSE` is MIT with correct copyright
- [ ] `README.md` has build prerequisites and working build instructions
- [ ] `CONTRIBUTING.md` covers dev setup and lint commands
- [ ] Issue templates and PR template exist with useful fields

## Verification

- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` exits 0 (or `yq` / `python3 -c` YAML parse)
- `grep -q 'pull_request' .github/workflows/ci.yml` — trigger present
- `grep -q 'ruff' .github/workflows/ci.yml` — python lint step present
- `grep -q 'clippy' .github/workflows/ci.yml` — rust check present
- `grep -q 'tsc' .github/workflows/ci.yml` — typescript check present
- All 7 files exist and have >10 lines of content each
- `head -1 LICENSE` contains "MIT"

## Inputs

- T01's clean lint baseline — all linters pass, configs are in place
- `backend/pyproject.toml` — ruff config from T01
- `package.json` — scripts and deps for README build instructions
- `src-tauri/Cargo.toml` — Rust dep info for README

## Expected Output

- `.github/workflows/ci.yml` — complete fast CI workflow
- `LICENSE` — MIT license
- `README.md` — project overview with build instructions
- `CONTRIBUTING.md` — contributor guide
- `.github/ISSUE_TEMPLATE/bug_report.md` — bug report template
- `.github/ISSUE_TEMPLATE/feature_request.md` — feature request template
- `.github/pull_request_template.md` — PR template
