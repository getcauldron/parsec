# S02: Auto-Update Wiring

**Goal:** The app has `tauri-plugin-updater` and `tauri-plugin-process` fully wired — Rust plugins registered, JS packages installed, signing keypair generated, updater endpoint configured for GitHub Releases, capabilities granted, and a non-blocking update check runs on startup.
**Demo:** `cargo tauri dev` launches without errors. The app calls `check()` on startup, which hits the (nonexistent) GitHub Releases endpoint, handles the 404 gracefully, and logs "no update available" to the console. A release build with `TAURI_SIGNING_PRIVATE_KEY` set produces `.sig` files alongside bundle artifacts.

## Must-Haves

- `tauri-plugin-updater` and `tauri-plugin-process` registered in Rust plugin chain
- `@tauri-apps/plugin-updater` and `@tauri-apps/plugin-process` installed as JS dependencies
- Ed25519 signing keypair generated and stored at `~/.tauri/parsec.key`
- `tauri.conf.json` has `createUpdaterArtifacts`, `plugins.updater.pubkey`, and `plugins.updater.endpoints` configured
- `updater:default` and `process:allow-restart` permissions in capabilities
- Frontend calls `check()` on startup, handles errors gracefully (no crash on 404)

## Proof Level

- This slice proves: integration (plugin registration + config + frontend call all work together)
- Real runtime required: yes — `cargo tauri dev` must start and the update check must execute
- Human/UAT required: no

## Verification

- `cargo tauri dev` starts without errors — app window opens, no Rust panics
- Browser console shows update check result (either "no update available" or a handled error from 404)
- `cargo tauri build` with `TAURI_SIGNING_PRIVATE_KEY` set completes and produces `.sig` files in the bundle output directory
- Keypair file exists at `~/.tauri/parsec.key`

## Integration Closure

- Upstream surfaces consumed: `tauri.conf.json` bundle config from S01, `src-tauri/src/lib.rs` plugin chain from M001
- New wiring introduced in this slice: updater + process Rust plugins, updater config in tauri.conf.json, frontend update check in `src/main.ts`
- What remains before the milestone is truly usable end-to-end: S03 (visual identity retheme) — update infrastructure is complete after this slice; actual update delivery depends on M003 publishing releases

## Tasks

- [x] **T01: Wire updater and process plugins with signing keypair and startup check** `est:45m`
  - Why: This is the entire slice — all pieces (Rust plugins, JS packages, config, keypair, capabilities, frontend check) must be wired together for any of them to be verifiable
  - Files: `src-tauri/Cargo.toml`, `src-tauri/src/lib.rs`, `src-tauri/tauri.conf.json`, `src-tauri/capabilities/default.json`, `package.json`, `src/main.ts`
  - Do: (1) Add `tauri-plugin-updater` and `tauri-plugin-process` to Cargo.toml deps. (2) Register updater in `setup()` via `app.handle().plugin(tauri_plugin_updater::Builder::new().build())` and process via `tauri_plugin_process::init()` in builder chain. (3) Install `@tauri-apps/plugin-updater` and `@tauri-apps/plugin-process` via pnpm. (4) Generate signing keypair with `pnpm tauri signer generate -w ~/.tauri/parsec.key` (no password). (5) Add `createUpdaterArtifacts: "v2"` to bundle config, add `plugins.updater` section with pubkey and GitHub Releases endpoint. (6) Add `updater:default` and `process:allow-restart` to capabilities. (7) Add a non-blocking `checkForUpdates()` async function in main.ts that calls `check()`, catches errors (404 = no release yet), and console-logs the result. Call it after sidecar status is established.
  - Verify: `cargo tauri dev` starts clean; browser console shows update check log; `cargo tauri build` with signing key produces `.sig` files
  - Done when: App starts without errors, update check executes and handles missing endpoint gracefully, signing keypair exists and release builds produce signatures

## Files Likely Touched

- `src-tauri/Cargo.toml`
- `src-tauri/src/lib.rs`
- `src-tauri/tauri.conf.json`
- `src-tauri/capabilities/default.json`
- `package.json`
- `src/main.ts`
