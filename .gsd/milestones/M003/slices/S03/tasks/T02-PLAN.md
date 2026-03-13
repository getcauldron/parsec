---
estimated_steps: 4
estimated_files: 1
---

# T02: Create tag-triggered release workflow with 3-platform matrix

**Slice:** S03 — Cross-Platform Release Workflow
**Milestone:** M003

## Description

Create `.github/workflows/release.yml` — a GitHub Actions workflow triggered by version tag push (`v*`) that builds the Tauri app on macOS ARM, Windows x64, and Linux x64, then attaches the installers (DMG, NSIS, AppImage) to a GitHub Release. Uses `tauri-apps/tauri-action@v0` which handles the Tauri build, artifact upload, and `latest.json` generation for the updater.

## Steps

1. **Define workflow trigger and matrix.** Trigger on `push.tags: ['v*']`. Matrix with 3 entries: `{ platform: macos-latest, target: aarch64-apple-darwin }`, `{ platform: ubuntu-22.04, target: x86_64-unknown-linux-gnu }`, `{ platform: windows-latest, target: x86_64-pc-windows-msvc }`. Single job `build-and-release`. Concurrency group `release-${{ github.ref }}`.

2. **Write the shared setup steps.** Checkout (`actions/checkout@v4`). Setup Python 3.10 with pip cache (`actions/setup-python@v5`). Install backend dependencies: `pip install -r backend/requirements.txt pyinstaller`. Run sidecar build: `python backend/build_sidecar.py`. Setup Node 22 (`actions/setup-node@v4`). Setup pnpm 10 (`pnpm/action-setup@v4`). Run `pnpm install --frozen-lockfile`. Setup Rust stable (`dtolnay/rust-toolchain@stable`). Use `swatinem/rust-cache@v2` with `workspaces: src-tauri`.

3. **Add platform-conditional steps.** Linux: install system deps (libwebkit2gtk-4.1-dev, libappindicator3-dev, librsvg2-dev, patchelf) — reuse the pattern from `ci.yml`. No extra steps for macOS or Windows.

4. **Wire `tauri-apps/tauri-action@v0`.** Set `tagName: ${{ github.ref_name }}`, `releaseName: "Parsec ${{ github.ref_name }}"`, `releaseDraft: true`, `prerelease: false`. Environment variables: `TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}`, `TAURI_SIGNING_PRIVATE_KEY_PASSWORD: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY_PASSWORD }}`. Add `permissions: contents: write` for release creation.

## Must-Haves

- [ ] Workflow triggers on `v*` tag push only (not branches)
- [ ] 3-platform matrix: macOS ARM, Ubuntu x64, Windows x64
- [ ] Each platform builds sidecar via `python backend/build_sidecar.py` before Tauri build
- [ ] `tauri-apps/tauri-action@v0` handles build + release
- [ ] `TAURI_SIGNING_PRIVATE_KEY` and `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` from secrets
- [ ] Linux job installs system dependencies
- [ ] `actionlint` passes on the workflow file
- [ ] `releaseDraft: true` so releases can be reviewed before publishing

## Verification

- `actionlint .github/workflows/release.yml` exits 0
- Visual inspection: workflow has correct trigger, matrix entries, sidecar build step, tauri-action step, signing env vars

## Inputs

- `backend/build_sidecar.py` — T01 output, called in workflow
- `.github/workflows/ci.yml` — reference for established patterns (caching, system deps)
- S03-RESEARCH.md — tauri-action usage, matrix entries, env vars, constraints
- M002 D048 — `TAURI_SIGNING_PRIVATE_KEY_PASSWORD=""` required even for empty passwords

## Expected Output

- `.github/workflows/release.yml` — complete release workflow, `actionlint`-clean
