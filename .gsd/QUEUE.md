# Queue

<!-- Append-only log of queued milestones. -->

## 2026-03-12

### M003: Documentation & CI

- **Why:** Public repo has no README, no CI, no license, no docs. R024 requires CER/WER in CI (unmet). Release builds need automation before M002 can ship.
- **Scope:** CI quality gates (two-tier: fast on PR, full on merge), release build workflows (3 platforms), VitePress docs site on GitHub Pages, README + contributing guide, repo hygiene (MIT license, branch protection, issue/PR templates).
- **Sequence:** After M001, before M002. M003 produces the release build workflow that M002's auto-update system depends on.
- **Impact on existing milestones:** Release builds and CI/CD moved out of M002. M002 now focuses on auto-updates, UX polish, code signing, and cross-platform verification.
