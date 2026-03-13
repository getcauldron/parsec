# GSD State

**Active Milestone:** M002 — Distribution & Polish
**Active Slice:** None (roadmap planned, ready for S01 execution)
**Phase:** planned
**Requirements Status:** 17 active · 0 validated · 4 deferred · 3 out of scope

## Milestone Registry
- ✅ **M001:** Core App
- 🔄 **M002:** Distribution & Polish — roadmap planned, 3 slices (S01 bundling, S02 auto-update, S03 polish), S01 plan + tasks written
- ⬜ **M003:** Documentation & CI

## Recent Decisions
- D037: Code signing deferred — ship unsigned, revisit when user base justifies cost
- D038: Cross-platform verification deferred to M003 — prove on macOS only
- D039: PyInstaller `_internal/` via `bundle.resources` instead of `--onefile`
- D040: Auto-update via `tauri-plugin-updater` + GitHub Releases

## Blockers
- None

## Next Action
Execute S01: Sidecar Bundling & macOS Installer (T01 → T02 → T03)
