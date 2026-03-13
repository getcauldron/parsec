# S04: Documentation Site

**Goal:** VitePress docs site builds locally with usage guide, architecture overview, FAQ, and contributing guide; GitHub Pages deployment workflow exists.
**Demo:** `pnpm docs:build` succeeds, producing a static site in `docs/.vitepress/dist/`; `.github/workflows/docs.yml` is a valid GitHub Actions workflow that deploys to GitHub Pages on push to main.

## Must-Haves

- VitePress installed as devDependency with `docs:dev` and `docs:build` scripts in package.json
- `docs/.vitepress/config.ts` with `base: '/parsec/'`, sidebar nav, and project metadata
- Landing page (`docs/index.md`) with hero section and quick-start link
- Content pages: Getting Started, Usage Guide, Architecture, FAQ, Contributing
- All internal links use relative markdown paths (no absolute `/` links that break with base path)
- `docs:build` completes without errors
- `.github/workflows/docs.yml` deploys to GitHub Pages via `actions/deploy-pages@v4`
- Workflow uses pnpm 10 + Node 22 (matching existing CI conventions)
- Workflow has correct permissions (`pages: write`, `id-token: write`) and concurrency group

## Verification

- `pnpm docs:build` exits 0 and produces `docs/.vitepress/dist/index.html`
- `find docs/.vitepress/dist -name '*.html' | wc -l` shows 6+ HTML files (one per page)
- `actionlint .github/workflows/docs.yml` passes (or manual YAML structure review if actionlint unavailable)
- All markdown files in `docs/` contain substantive content (not stubs or TODOs)

## Tasks

- [x] **T01: Scaffold VitePress site with all content pages** `est:1h`
  - Why: The docs site is the entire deliverable of this slice — needs VitePress config, all 6 content pages, and package.json scripts to produce a working local build
  - Files: `package.json`, `docs/.vitepress/config.ts`, `docs/index.md`, `docs/guide/getting-started.md`, `docs/guide/usage.md`, `docs/guide/architecture.md`, `docs/guide/faq.md`, `docs/guide/contributing.md`
  - Do: Install `vitepress` as devDependency. Create `docs/.vitepress/config.ts` with `base: '/parsec/'`, site title/description, sidebar nav for guide pages, and social links. Write `docs/index.md` hero landing page. Write 5 guide pages extracting/expanding content from README, CONTRIBUTING, and backend docstrings (sidecar protocol, engine interface, OCR options, 49 languages, pipeline). Add `docs:dev` and `docs:build` scripts to package.json. Use relative markdown links only. Ensure each page has real substantive content — not stubs.
  - Verify: `pnpm docs:build` exits 0; `find docs/.vitepress/dist -name '*.html' | wc -l` shows 6+; spot-check that dist/index.html contains hero content
  - Done when: All 6 pages render to HTML via VitePress build with no errors or warnings

- [x] **T02: Add GitHub Pages deployment workflow** `est:20m`
  - Why: The docs site needs a deployment path — GitHub Pages via Actions is the chosen approach (D052)
  - Files: `.github/workflows/docs.yml`
  - Do: Create workflow triggered on push to main (path filter: `docs/**`). Use pnpm 10 + Node 22 setup matching ci.yml conventions. Build with `pnpm docs:build`. Upload artifact with `actions/upload-pages-artifact@v3` pointing at `docs/.vitepress/dist`. Deploy with `actions/deploy-pages@v4`. Set permissions (`pages: write`, `id-token: write`). Set concurrency group `pages` with `cancel-in-progress: false`. Add `workflow_dispatch` trigger for manual deploys.
  - Verify: YAML is valid (actionlint or manual structure review); workflow structure matches VitePress official deployment template; permissions and concurrency are correct
  - Done when: `.github/workflows/docs.yml` exists, is valid YAML, and follows the VitePress GitHub Pages deployment pattern

## Files Likely Touched

- `package.json`
- `pnpm-lock.yaml`
- `docs/.vitepress/config.ts`
- `docs/index.md`
- `docs/guide/getting-started.md`
- `docs/guide/usage.md`
- `docs/guide/architecture.md`
- `docs/guide/faq.md`
- `docs/guide/contributing.md`
- `.github/workflows/docs.yml`
