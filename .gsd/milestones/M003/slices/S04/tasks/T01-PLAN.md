---
estimated_steps: 5
estimated_files: 8
---

# T01: Scaffold VitePress site with all content pages

**Slice:** S04 — Documentation Site
**Milestone:** M003

## Description

Install VitePress, create the site config, write all 6 documentation pages (landing + 5 guide pages), and add package.json scripts. This is the bulk of the slice — producing a working local docs site with substantive content derived from README, CONTRIBUTING, and backend source docstrings.

## Steps

1. Install `vitepress` as a devDependency (`pnpm add -D vitepress`). If pnpm hoisting issues arise with Vue, add `shamefully-hoist=true` to `.npmrc` or use `public-hoist-pattern[]=vue`.
2. Add `"docs:dev": "vitepress dev docs"` and `"docs:build": "vitepress build docs"` scripts to `package.json`.
3. Create `docs/.vitepress/config.ts` — set `base: '/parsec/'`, site title "Parsec", description, theme config with sidebar (Guide section listing all 5 pages), nav bar, social links (GitHub repo), and footer.
4. Write all 6 markdown pages with substantive content:
   - `docs/index.md` — VitePress hero layout with tagline, action buttons (Get Started, GitHub), features section (PaddleOCR, searchable PDFs, 49 languages, cross-platform)
   - `docs/guide/getting-started.md` — prerequisites, clone, install, run (expanded from README)
   - `docs/guide/usage.md` — supported formats, OCR options (language, DPI, deskew, rotate, force OCR, skip text), language support table or grouped list
   - `docs/guide/architecture.md` — system diagram, Tauri→sidecar→PaddleOCR→OCRmyPDF flow, NDJSON protocol spec, abstract engine interface, sidecar bundling strategy (PyInstaller + Tauri externalBin)
   - `docs/guide/faq.md` — common questions: supported OS, offline usage, file size, language codes, troubleshooting
   - `docs/guide/contributing.md` — link to CONTRIBUTING.md content, dev setup, lint commands, branch naming, PR workflow
5. Run `pnpm docs:build` and verify all pages render to HTML without errors.

## Must-Haves

- [ ] VitePress installed as devDependency
- [ ] `docs:dev` and `docs:build` scripts in package.json
- [ ] Config with `base: '/parsec/'` and sidebar navigation
- [ ] All 6 pages contain real content (no stubs, no TODOs)
- [ ] All internal links use relative markdown paths
- [ ] `pnpm docs:build` exits 0

## Verification

- `pnpm docs:build` exits 0
- `find docs/.vitepress/dist -name '*.html' | wc -l` returns 6 or more
- `grep -l 'TODO\|PLACEHOLDER\|STUB' docs/**/*.md` returns nothing
- Spot-check: `docs/.vitepress/dist/index.html` contains the hero tagline

## Inputs

- `README.md` — project description, architecture diagram, prerequisites, getting started steps
- `CONTRIBUTING.md` — dev setup, lint commands, branch naming, PR workflow
- `backend/parsec/sidecar.py` — NDJSON protocol spec in docstring
- `backend/parsec/engine.py` — abstract OcrEngine interface
- `backend/parsec/models.py` — OcrOptions fields (language, dpi, deskew, rotate_pages, etc.)
- `backend/parsec/languages.py` — 49 supported languages with codes and display names
- `backend/parsec/pipeline.py` — OCRmyPDF integration

## Expected Output

- `docs/.vitepress/config.ts` — VitePress site configuration
- `docs/index.md` — landing page with hero layout
- `docs/guide/getting-started.md` — setup instructions
- `docs/guide/usage.md` — usage guide with OCR options and language support
- `docs/guide/architecture.md` — technical architecture deep-dive
- `docs/guide/faq.md` — frequently asked questions
- `docs/guide/contributing.md` — contributor guide
- `package.json` — updated with vitepress dep and docs scripts
- `pnpm-lock.yaml` — updated lockfile
