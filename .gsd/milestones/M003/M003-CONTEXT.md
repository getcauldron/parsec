# M003: Documentation & CI — Context

**Gathered:** 2026-03-12
**Status:** Queued — pending auto-mode execution

## Project Description

Parsec is a cross-platform desktop app that turns scanned documents into searchable PDFs using PaddleOCR. M003 adds the project infrastructure that a public open-source repo needs: CI pipelines, documentation, and repo hygiene.

## Why This Milestone

The app is being built in M001 but the repo has no README, no license, no CI, no contributing guide, no docs site, and no branch protection. A public repo without these signals is effectively invisible and uninviting. CI also catches regressions automatically — R024 explicitly calls for CER/WER thresholds in CI, and that's currently unmet. Release builds need automation before M002's installer distribution can ship.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Visit the GitHub repo and find a clear README with project description, screenshots, build instructions, and architecture overview
- Read user-facing documentation on a VitePress site deployed to GitHub Pages (usage guide, FAQ, supported formats)
- Open a PR and see automated checks (lint, typecheck, Rust check) pass or fail within minutes
- See OCR quality benchmarks run on merge to main, catching regressions automatically
- Trigger a release build that produces platform-specific installers via GitHub Actions
- Find contributing guidelines, issue templates, and PR templates that lower the barrier to contribution

### Entry point / environment

- Entry point: GitHub repo page, GitHub Actions, GitHub Pages docs site
- Environment: GitHub (CI runners: ubuntu-latest, macos-latest, windows-latest), GitHub Pages
- Live dependencies involved: GitHub Actions, GitHub Pages, PaddleOCR models (cached in CI)

## Completion Class

- Contract complete means: CI workflows run green on a test PR; docs site builds and deploys; README renders correctly on GitHub
- Integration complete means: Branch protection enforces CI checks; release workflow produces downloadable artifacts for all 3 platforms; docs site is live at the GitHub Pages URL
- Operational complete means: A new contributor can clone, build, test, and submit a PR guided entirely by repo documentation; a maintainer can cut a release by tagging

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Push a commit to a PR branch → fast CI (lint, typecheck, Rust check) runs and reports status within 5 minutes
- Merge a PR to main → full test suite including OCR quality benchmarks runs and reports CER/WER
- Create a version tag → release workflow builds macOS DMG, Windows MSI, and Linux AppImage and attaches them to a GitHub Release
- Visit the GitHub Pages URL → docs site loads with usage guide, architecture overview, and contributing guide
- A fresh clone following only the README instructions → successful build and test run

## Risks and Unknowns

- **PaddleOCR in CI** — PaddlePaddle is ~1GB installed. CI caching strategy (pip cache + model cache) is critical for keeping full-suite runs under 10 minutes. If caching is unreliable, full tests become prohibitively slow.
- **Cross-platform release builds** — PyInstaller produces OS-specific binaries. The sidecar must be built on each platform's runner, then Tauri bundles it. This is a multi-step workflow that hasn't been proven yet.
- **GitHub Pages deployment** — VitePress build + deploy needs a working workflow. Low risk but needs to be wired up.
- **Branch protection vs solo dev** — If the user is the only contributor right now, strict branch protection may slow them down. Need to calibrate rules appropriately.

## Existing Codebase / Prior Art

- `backend/pyproject.toml` — Python project config with pytest setup, dependencies listed
- `backend/tests/` — 4 test files (test_engine.py, test_pipeline.py, test_quality.py, test_sidecar.py) — all need PaddleOCR + OCRmyPDF
- `backend/build_sidecar.sh` — PyInstaller build script for the Python sidecar
- `src-tauri/Cargo.toml` — Rust project config
- `package.json` — pnpm project with Vite + TypeScript + Tauri CLI
- `backend/tests/test_quality.py` — CER/WER benchmarks with per-category thresholds (clean < 0.05 CER, multicol < 0.08, degraded < 0.15)
- `backend/tests/fixtures/` — 7 test images with ground truth text files

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R024 — Automated OCR quality regression testing: CI runs CER/WER benchmarks (primary deliverable)
- R013 — Downloadable installer: release build workflow produces platform installers (supports M002)
- R010 — Cross-platform desktop app: CI proves builds work on all 3 platforms

## Scope

### In Scope

- **CI — Fast tier (every PR):** Rust cargo check/clippy, TypeScript typecheck, Python lint (ruff), frontend lint
- **CI — Full tier (merge to main / nightly):** All fast checks + pytest with PaddleOCR integration tests + CER/WER quality benchmarks
- **CI — Release builds:** GitHub Actions workflow triggered by version tags, builds macOS/Windows/Linux installers via Tauri bundler + PyInstaller sidecar
- **Repo hygiene:** MIT LICENSE file, repo description/topics, issue templates, PR template, branch protection rules on main
- **Documentation — README:** Project description, screenshots/demo, quick start, build from source, architecture overview, contributing pointer
- **Documentation — Contributing:** Dev environment setup, code style, testing guide, PR workflow
- **Documentation — User site:** VitePress static site deployed to GitHub Pages with usage guide, supported formats, FAQ, architecture deep-dive
- **PaddleOCR model caching** in CI to keep full-suite runs fast

### Out of Scope / Non-Goals

- Auto-update mechanism (stays in M002)
- UX polish (stays in M002)
- Code signing (stays in M002 — requires paid certificates)
- Platform-specific bug fixes (stays in M002)
- New OCR features or engines
- Custom domain for docs site

## Technical Constraints

- GitHub Actions for CI (free tier for public repos)
- GitHub Pages for docs hosting (free for public repos)
- VitePress for docs site generator (already using Vite)
- Two-tier CI: fast checks on every PR, full OCR suite on merge/nightly (PaddlePaddle is too heavy for every PR)
- Release builds need runners for all 3 platforms (macOS, Windows, Linux)
- MIT license (user chose this; OCRmyPDF is MPL-2.0, compatible)

## Integration Points

- **GitHub Actions** — CI runner infrastructure for all workflows
- **GitHub Pages** — Docs site hosting, deployed from a CI workflow
- **GitHub Releases** — Release build artifacts attached to tagged releases
- **GitHub branch protection** — Enforces CI checks before merge to main
- **PaddleOCR models** — Must be cached in CI; ~15MB download on cache miss
- **PaddlePaddle** — ~1GB pip install; must be cached aggressively
- **Tauri bundler** — Generates platform-specific installers in release workflow
- **PyInstaller** — Builds platform-specific sidecar binary in release workflow

## Open Questions

- **Docs site path prefix** — Will the GitHub Pages site be at `getcauldron.github.io/parsec/` or a custom domain? Affects VitePress base config.
- **Release workflow trigger** — Tag push (`v*`) vs GitHub Release creation vs manual dispatch? Tag push is simplest.
- **Branch protection strictness** — Require up-to-date branches? Require reviews? Need to calibrate for current team size (solo dev).
- **Nightly schedule** — Should full OCR tests run on a cron schedule in addition to merge-to-main, or is merge-triggered sufficient?
