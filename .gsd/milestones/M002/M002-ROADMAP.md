# M002: Distribution & Polish

**Vision:** Parsec goes from `cargo tauri dev` to a real downloadable app — a macOS DMG that installs with a double-click, auto-update client wiring ready for M003's release workflow, and a polished UI that feels like a finished product.

## Success Criteria

- A macOS DMG built from `cargo tauri build` installs cleanly, launches the app, and processes a file to searchable PDF — with the PyInstaller sidecar bundled inside
- The Tauri updater plugin is wired up with signing keypair and endpoint config, so when M003 publishes releases with `latest.json`, existing installations will detect and install updates
- The UI is rethemed to match Parsec's icon identity — black/off-white/emerald-green palette, new geometric typography, white processing accents, green completion states, icon in header, and all bundle icons regenerated

## Key Risks / Unknowns

- **Sidecar `--onedir` folder bundling** — Tauri's `externalBin` only bundles a single file, but PyInstaller `--onedir` produces a main binary + `_internal/` directory. Must use `bundle.resources` for `_internal/` and ensure the sidecar binary can find it at runtime inside the app bundle. If the directory layout doesn't work, the entire distribution strategy needs rethinking.
- **Updater plugin integration** — First time wiring `tauri-plugin-updater`. Endpoint config, signing keypair generation, CSP implications, and the JS-side `check()` → `downloadAndInstall()` → `relaunch()` flow are all new territory for this codebase.

## Proof Strategy

- **Sidecar bundling** → retire in S01 by building a macOS DMG, installing it, and processing a real file to searchable PDF from the installed app (not dev mode)
- **Updater plugin** → retire in S02 by wiring the plugin, configuring a static endpoint, and verifying `check()` executes without error (actual update delivery depends on M003 releases)

## Verification Classes

- Contract verification: `cargo tauri build` succeeds, DMG mounts, app launches, sidecar spawns, file processes
- Integration verification: Installed app (not dev mode) processes files end-to-end; updater `check()` call completes
- Operational verification: Clean install from DMG → process file → verify output; updater detects "no update available" gracefully
- UAT / human verification: Visual identity assessment — UI palette, typography, and icon match Parsec brand; transitions and states feel finished

## Milestone Definition of Done

This milestone is complete only when all are true:

- macOS DMG installs cleanly and the app processes files to searchable PDF from the installed binary
- PyInstaller sidecar binary + `_internal/` folder are bundled inside the app and spawn correctly
- Updater plugin is configured with signing keypair and endpoint, and `check()` runs without error
- UI is rethemed to match icon identity with new palette, typography, and bundle icons
- All changes verified against the installed app, not just `cargo tauri dev`

## Requirement Coverage

- Covers: R013 (downloadable installer — macOS DMG proven, Windows/Linux deferred to M003 CI)
- Partially covers: R010 (cross-platform — macOS proven, Windows/Linux verification deferred to M003)
- Leaves for later: R017, R018, R019, R020 (already deferred)
- New capability (no existing requirement): Auto-update client wiring, visual identity retheme (icon-driven palette, typography, bundle icons)
- Orphan risks: none

## Slices

- [x] **S01: Sidecar Bundling & macOS Installer** `risk:high` `depends:[]`
  > After this: `cargo tauri build` produces a macOS DMG. Installing the DMG and launching the app processes a dropped file to searchable PDF — verified from the installed app, not dev mode.
- [x] **S02: Auto-Update Wiring** `risk:medium` `depends:[S01]`
  > After this: The app checks for updates on launch via `tauri-plugin-updater` with a configured GitHub Releases endpoint. When no update is available, it silently continues. The signing keypair and updater config are in place for M003's release workflow to complete the loop.
- [ ] **S03: Visual Identity Retheme** `risk:low` `depends:[]`
  > After this: The entire UI is rethemed to match the Parsec icon's visual identity — black/off-white/emerald-green palette replacing the amber industrial aesthetic. New typography pairing that matches the icon's bold geometric character. White/off-white accent for processing states, green for completion. Icon integrated into the app header. All Tauri bundle icons (.icns, .ico, sized PNGs) regenerated from `icon.png`. Smooth card animations, completion summary, and "clear completed" action included as part of the polish pass.

## Boundary Map

### S01 → S02

Produces:
- Working `cargo tauri build` pipeline that produces a functional macOS app bundle with sidecar
- `bundle.resources` config pattern for bundling the PyInstaller `_internal/` directory
- Updated `tauri.conf.json` with bundle config that S02 extends with updater settings

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- Proven app bundle that S03's polish changes can be verified against (installed app, not just dev mode)

### S02 (standalone)

Produces:
- `tauri-plugin-updater` + `tauri-plugin-process` wired into the Rust plugin chain
- Updater permissions in capabilities config
- `TAURI_SIGNING_PRIVATE_KEY` and public key config for signing builds
- Update-check UI element (status indicator or notification)

Consumes:
- Working `tauri.conf.json` bundle config from S01

### S03 (standalone)

Produces:
- Full visual retheme: new CSS custom properties, palette (black/off-white/emerald-green), typography pairing
- White/off-white processing accent system, green completion states (replacing amber)
- Icon in app header, regenerated Tauri bundle icons (.icns, .ico, sized PNGs) from `icon.png`
- Smooth card animations, completion summary component, "clear completed" action
- Updated `index.html` with new font imports

Consumes:
- Existing M001 UI code (`src/main.ts`, `src/styles.css`, `index.html`)
- `icon.png` at repo root
