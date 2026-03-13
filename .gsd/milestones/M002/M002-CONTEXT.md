# M002: Distribution & Polish — Context

**Gathered:** 2026-03-12
**Status:** Waiting for M001

## Project Description

Parsec is a cross-platform desktop app that turns scanned documents into searchable PDFs. M002 takes the working app from M001 and makes it distributable and polished.

## Why This Milestone

M001 delivers a working app on macOS via `cargo tauri dev`. M002 packages it for real users: downloadable installers for macOS/Windows/Linux, auto-updates, UX polish based on real usage, and any cross-platform issues that surface during packaging.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Download Parsec from a releases page and install it with a double-click on macOS, Windows, or Linux
- Receive automatic update notifications when new versions are available
- Experience a polished, responsive UI with smooth animations and clear feedback

### Entry point / environment

- Entry point: Downloaded installer → installed app binary
- Environment: macOS (DMG), Windows (MSI), Linux (AppImage/deb)
- Live dependencies involved: PaddleOCR sidecar (bundled inside installer), auto-update server

## Completion Class

- Contract complete means: Installers build on CI for all three platforms, app launches and processes files on each
- Integration complete means: Auto-update flow works end-to-end (check → download → install)
- Operational complete means: Clean install, uninstall, and upgrade paths work on all platforms

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Fresh install from DMG/MSI/AppImage on each platform → app launches, processes a file, produces searchable PDF
- Auto-update notification appears when a new version is available
- Uninstall cleanly removes all app files

## Risks and Unknowns

- **PyInstaller cross-platform builds** — need CI runners for macOS, Windows, Linux to produce platform-specific sidecar binaries
- **Code signing** — macOS and Windows require signed binaries for smooth install experience; unsigned apps trigger warnings
- **Auto-update infrastructure** — need a server or GitHub Releases integration for update checks
- **Platform-specific bugs** — WebView rendering differences, file path handling, permissions

## Existing Codebase / Prior Art

- Everything built in M001 — Tauri app, Python sidecar, OCR pipeline

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions.

## Relevant Requirements

- R013 — Downloadable installer (primary)
- R010 — Cross-platform desktop app (verification on Windows/Linux)

## Scope

### In Scope

- Auto-update mechanism (Tauri updater plugin + GitHub Releases integration)
- UX polish and responsive design improvements
- Platform-specific testing and bug fixes
- Code signing (if feasible without paid certificates)
- Cross-platform verification (install + run on macOS, Windows, Linux)

### Out of Scope / Non-Goals

- CI/CD pipeline for builds and quality gates (moved to M003)
- Release build workflows (moved to M003)
- Documentation (moved to M003)
- New OCR features (engines, languages beyond what M001 ships)
- Document management features
- Cloud anything

### Dependency

- M003 must complete first — M002 depends on CI release builds from M003 to produce the installers that auto-update distributes

## Technical Constraints

- Tauri updater plugin for auto-update
- Platform-specific code signing requirements (Apple Developer Program, Windows code signing certificate)

## Integration Points

- **Tauri updater plugin** — checks for updates, downloads, installs
- **GitHub Releases** — update distribution channel (release artifacts produced by M003 workflows)
- **Platform-specific installers** — built by M003 release workflow, verified by M002

## Open Questions

- **Code signing cost** — Apple Developer Program ($99/yr) and Windows code signing certificates add cost to a free project. Worth it?
- **Update channel** — GitHub Releases vs custom update server vs Tauri's built-in updater?
- **Linux packaging** — AppImage vs Flatpak vs deb/rpm? AppImage is simplest but some distros prefer others.
