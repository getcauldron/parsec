---
estimated_steps: 5
estimated_files: 2
---

# T01: Add linter configs and fix all lint violations

**Slice:** S01 — Fast CI & Repo Hygiene
**Milestone:** M003

## Description

Establish a clean lint baseline across all three codebases (Python, TypeScript, Rust) so the CI workflow can enforce zero-tolerance lint checks. Ruff needs a config and may surface violations. Clippy has 2 known warnings to fix. TypeScript already passes clean.

## Steps

1. Add `[tool.ruff]` section to `backend/pyproject.toml` — target Python 3.10, select `E`, `F`, `W`, `I` rules (pyflakes, pycodestyle errors/warnings, isort). Add `ruff` to dev dependencies.
2. Install ruff and run `ruff check backend/` — fix any violations found (likely import ordering, unused imports).
3. Run `ruff format --check backend/` to verify formatting. If the diff is small, apply `ruff format`. If large, skip format enforcement for now (config only `ruff check` in CI).
4. Fix clippy warnings in `src-tauri/src/lib.rs`: add `#[allow(clippy::too_many_arguments)]` to `process_files`, remove the needless borrow on `window.app_handle()`.
5. Verify all three linters pass: `ruff check`, `cargo clippy -- -D warnings`, `tsc --noEmit`.

## Must-Haves

- [ ] `[tool.ruff]` config in `backend/pyproject.toml` with sensible rule selection
- [ ] `ruff` added to `[project.optional-dependencies] dev`
- [ ] `ruff check backend/` exits 0
- [ ] `cargo clippy --all-targets -- -D warnings` exits 0
- [ ] `tsc --noEmit` exits 0

## Verification

- Run `cd /Users/zakkeown/Code/getcauldron/parsec/backend && python3 -m ruff check .` → exit 0
- Run `cd /Users/zakkeown/Code/getcauldron/parsec/src-tauri && cargo clippy --all-targets -- -D warnings` → exit 0
- Run `cd /Users/zakkeown/Code/getcauldron/parsec && npx tsc --noEmit` → exit 0

## Inputs

- `backend/pyproject.toml` — current config, no ruff section
- `src-tauri/src/lib.rs` — 2 clippy warnings (too_many_arguments on line 77, needless_borrow on line 237)
- `tsconfig.json` — strict mode already enabled, currently passes clean

## Expected Output

- `backend/pyproject.toml` — updated with `[tool.ruff]` config and ruff in dev deps
- `src-tauri/src/lib.rs` — clippy warnings resolved
- All Python source files — any ruff violations fixed (import order, unused imports, etc.)
