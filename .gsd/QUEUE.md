# Queue

<!-- Append-only log of queued milestones. -->

## 2026-03-12

### M003: Documentation & CI

- **Why:** Public repo has no README, no CI, no license, no docs. R024 requires CER/WER in CI (unmet). Release builds need automation before M002 can ship.
- **Scope:** CI quality gates (two-tier: fast on PR, full on merge), release build workflows (3 platforms), VitePress docs site on GitHub Pages, README + contributing guide, repo hygiene (MIT license, branch protection, issue/PR templates).
- **Sequence:** After M001, before M002. M003 produces the release build workflow that M002's auto-update system depends on.
- **Impact on existing milestones:** Release builds and CI/CD moved out of M002. M002 now focuses on auto-updates, UX polish, code signing, and cross-platform verification.

### M002/S03 scope rewrite: Visual Identity Retheme (was UX Polish)

- **Why:** New app icon (`icon.png`) establishes a brand identity — black bg, off-white "P" mark, emerald green accent — that the current amber/industrial UI doesn't match. Full retheme to align UI with icon.
- **Scope:** Replace color palette (black/off-white/emerald-green), new geometric typography pairing, white/off-white processing accents (replacing amber), green completion states, icon in app header, regenerate all Tauri bundle icons from `icon.png`. Original S03 polish items (animations, completion summary, clear completed) folded into the retheme.
- **Impact:** Supersedes D030 (amber industrial aesthetic). No new milestone — rewrites M002/S03's scope. S03 remains `risk:low`, `depends:[]`.
