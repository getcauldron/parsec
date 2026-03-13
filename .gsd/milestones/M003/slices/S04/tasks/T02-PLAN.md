---
estimated_steps: 3
estimated_files: 1
---

# T02: Add GitHub Pages deployment workflow

**Slice:** S04 — Documentation Site
**Milestone:** M003

## Description

Create the GitHub Actions workflow that builds the VitePress site and deploys it to GitHub Pages on push to main. Follows the official VitePress deployment template adapted for this project's pnpm 10 + Node 22 conventions.

## Steps

1. Create `.github/workflows/docs.yml` with triggers: `push` to `main` (path filter `docs/**`, `.github/workflows/docs.yml`), plus `workflow_dispatch` for manual runs.
2. Define two jobs: `build` (checkout, setup pnpm 10 + Node 22, install, `pnpm docs:build`, upload pages artifact from `docs/.vitepress/dist`) and `deploy` (deploy-pages action, needs build).
3. Set workflow-level permissions (`pages: write`, `id-token: write`, `contents: read`), concurrency group `pages` with `cancel-in-progress: false`, and environment `github-pages` with the pages URL.

## Must-Haves

- [ ] Workflow triggers on push to main with docs path filter + workflow_dispatch
- [ ] pnpm 10 + Node 22 setup matches ci.yml conventions
- [ ] Build step runs `pnpm docs:build`
- [ ] Upload artifact from `docs/.vitepress/dist`
- [ ] Deploy step uses `actions/deploy-pages@v4`
- [ ] Permissions: `pages: write`, `id-token: write`
- [ ] Concurrency group `pages` with `cancel-in-progress: false`

## Verification

- YAML is syntactically valid (`python -c "import yaml; yaml.safe_load(open('.github/workflows/docs.yml'))"` or actionlint)
- Workflow has both `build` and `deploy` jobs
- `deploy` job has `needs: build`
- Permissions include `pages: write` and `id-token: write`
- Concurrency group is `pages`

## Inputs

- `.github/workflows/ci.yml` — pnpm/Node setup pattern to follow
- `docs/.vitepress/dist` output path from T01's VitePress build
- VitePress official GitHub Pages deployment template (from S04-RESEARCH.md sources)

## Expected Output

- `.github/workflows/docs.yml` — complete GitHub Pages deployment workflow
