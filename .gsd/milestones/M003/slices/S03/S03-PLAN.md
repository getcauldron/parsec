# S03: Cross-Platform Release Workflow

**Goal:** A version tag push triggers a GitHub Actions release workflow that builds macOS DMG, Windows NSIS installer, and Linux AppImage with bundled PyInstaller sidecar, and attaches them to a GitHub Release.
**Demo:** `release.yml` passes `actionlint`, `build_sidecar.py` runs successfully on macOS producing the same sidecar output as `build_sidecar.sh`, `build.rs` handles `.exe` suffix on Windows, and `tauri.conf.json` has platform-conditional `_internal/` placement config for all three platforms.

## Must-Haves

- `backend/build_sidecar.py` cross-platform sidecar build script replicating all PyInstaller flags from `build_sidecar.sh`
- `.github/workflows/release.yml` tag-triggered workflow with 3-platform matrix using `tauri-apps/tauri-action@v0`
- `src-tauri/build.rs` handles `.exe` suffix on Windows
- `src-tauri/tauri.conf.json` has `bundle.windows` and `bundle.linux` config for `_internal/` placement
- Workflow requires `TAURI_SIGNING_PRIVATE_KEY` secret (with empty password documented)

## Proof Level

- This slice proves: contract (workflow YAML valid, build script runs, config structurally correct)
- Real runtime required: no — live cross-platform proof requires pushing to GitHub (outward-facing action)
- Human/UAT required: no

## Verification

- `actionlint .github/workflows/release.yml` exits 0
- `python3 -c "import ast; ast.parse(open('backend/build_sidecar.py').read())"` exits 0 (valid Python)
- `cd backend && python3 build_sidecar.py --help` runs without error (script is importable and has CLI)
- `cd src-tauri && cargo check` passes with the updated `build.rs`
- `python3 -c "import json; c=json.load(open('src-tauri/tauri.conf.json')); assert 'windows' in c['bundle'] or 'resources' in c['bundle']; print('OK')"` — bundle config has platform-specific entries

## Tasks

- [x] **T01: Create cross-platform sidecar build script and fix build.rs for Windows** `est:45m`
  - Why: `build_sidecar.sh` is bash-only with hardcoded `.venv/bin/python` — won't work on Windows CI runners. `build.rs` doesn't append `.exe` on Windows. Both must be fixed before the release workflow can use them.
  - Files: `backend/build_sidecar.py`, `src-tauri/build.rs`, `src-tauri/tauri.conf.json`
  - Do: Write `build_sidecar.py` using `pathlib` and `subprocess` that: detects OS, uses system Python (no venv), replicates all `--hidden-import`/`--collect-all`/`--collect-data`/`--copy-metadata` flags from `build_sidecar.sh` exactly, produces output at `backend/dist/parsec-sidecar/parsec-sidecar[.exe]`. Fix `build.rs` to append `.exe` when target contains `windows`. Add `bundle.windows.nsis.installerIcon` placeholder and `bundle.resources` map for Windows/Linux `_internal/` placement. Keep existing `bundle.macOS.files` untouched.
  - Verify: `python3 backend/build_sidecar.py --help` works; `cd src-tauri && cargo check` passes; JSON schema valid
  - Done when: build script is syntactically valid Python, runs `--help` without error, replicates all PyInstaller flags; `build.rs` compiles; tauri.conf.json has platform config for all 3 OSes

- [x] **T02: Create tag-triggered release workflow with 3-platform matrix** `est:45m`
  - Why: This is the core deliverable — the GitHub Actions workflow that builds and publishes release artifacts on tag push.
  - Files: `.github/workflows/release.yml`
  - Do: Create `release.yml` triggered on `v*` tag push. 3-entry matrix: `macos-latest` (ARM), `ubuntu-22.04`, `windows-latest`. Each entry: (1) checkout, (2) setup Python 3.10 + pip cache, (3) install PyInstaller + all backend deps from requirements, (4) run `build_sidecar.py`, (5) setup Node 22 + pnpm 10 + pnpm install, (6) setup Rust stable, (7) `tauri-apps/tauri-action@v0` with `tagName`, `releaseName`, `releaseDraft: true`. Linux job installs system deps (webkit, appindicator, etc). Use `swatinem/rust-cache@v2`. Environment: `TAURI_SIGNING_PRIVATE_KEY` and `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` from secrets. Concurrency group on tag ref.
  - Verify: `actionlint .github/workflows/release.yml` exits 0
  - Done when: actionlint passes with no errors; workflow structure matches the Tauri v2 release pipeline pattern

## Files Likely Touched

- `backend/build_sidecar.py`
- `src-tauri/build.rs`
- `src-tauri/tauri.conf.json`
- `.github/workflows/release.yml`
