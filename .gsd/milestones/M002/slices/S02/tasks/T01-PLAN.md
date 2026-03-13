---
estimated_steps: 7
estimated_files: 6
---

# T01: Wire updater and process plugins with signing keypair and startup check

**Slice:** S02 — Auto-Update Wiring
**Milestone:** M002

## Description

Wire the complete auto-update infrastructure in one pass: Rust plugins, JS packages, signing keypair, Tauri config, capabilities, and frontend update check. Every piece depends on the others — the updater can't be verified without config + capabilities + Rust registration all in place.

The updater plugin has a quirk: it must be registered inside `setup()` via `app.handle().plugin()`, not in the builder chain like other plugins. The process plugin uses the normal `init()` pattern.

The signing keypair is permanent infrastructure — it must be backed up (D040). Generate without a password for CI compatibility.

## Steps

1. Add `tauri-plugin-updater = "2"` and `tauri-plugin-process = "2"` to `src-tauri/Cargo.toml` dependencies
2. In `src-tauri/src/lib.rs`: register `tauri_plugin_process::init()` in the builder `.plugin()` chain, and register `tauri_plugin_updater::Builder::new().build()` inside the existing `setup()` closure via `app.handle().plugin()`
3. Run `pnpm add @tauri-apps/plugin-updater @tauri-apps/plugin-process` to install JS packages
4. Generate the signing keypair: `pnpm tauri signer generate -w ~/.tauri/parsec.key` (no password — press Enter when prompted). Record the public key from stdout
5. Update `src-tauri/tauri.conf.json`: add `"createUpdaterArtifacts": "v2"` to `bundle`, add `"plugins": { "updater": { "pubkey": "<public-key>", "endpoints": ["https://github.com/zakkeown/parsec/releases/latest/download/latest.json"] } }`
6. Update `src-tauri/capabilities/default.json`: add `"updater:default"` and `"process:allow-restart"` to the permissions array
7. Add `checkForUpdates()` in `src/main.ts`: import `check` from `@tauri-apps/plugin-updater`, call it after app initialization, catch errors (404 from missing endpoint is expected until M003 publishes releases), console-log the result. Must not block the UI or delay sidecar initialization.

## Must-Haves

- [ ] Updater plugin registered in `setup()` (not builder chain)
- [ ] Process plugin registered in builder chain
- [ ] Signing keypair at `~/.tauri/parsec.key` with public key in tauri.conf.json
- [ ] `createUpdaterArtifacts: "v2"` in bundle config
- [ ] GitHub Releases endpoint in updater config
- [ ] `updater:default` and `process:allow-restart` capabilities granted
- [ ] Non-blocking `checkForUpdates()` call on startup that handles 404 gracefully

## Verification

- `cargo tauri dev` starts without errors — no Rust panics, no capability denials
- Open browser console: confirm update check log message appears (e.g. "No update available" or "Update check failed: ..." for the 404)
- Keypair file exists: `test -f ~/.tauri/parsec.key && echo "OK"`
- Release build verification: `TAURI_SIGNING_PRIVATE_KEY="$(cat ~/.tauri/parsec.key)" cargo tauri build` succeeds and `.sig` files appear in bundle output

## Inputs

- `src-tauri/src/lib.rs` — existing plugin chain with shell + store, setup closure spawning sidecar
- `src-tauri/tauri.conf.json` — bundle config from S01 with `externalBin` and `macOS.files`
- `src-tauri/capabilities/default.json` — existing permissions for shell and store
- `src/main.ts` — 333-line frontend with drag-drop, progress channel, settings init
- S02 research — plugin registration quirks, endpoint format, CSP non-issue confirmed

## Expected Output

- `src-tauri/Cargo.toml` — two new plugin dependencies
- `src-tauri/src/lib.rs` — updater in setup(), process in builder chain
- `src-tauri/tauri.conf.json` — `createUpdaterArtifacts`, `plugins.updater` with pubkey + endpoint
- `src-tauri/capabilities/default.json` — updater + process permissions added
- `package.json` / `pnpm-lock.yaml` — two new JS dependencies
- `src/main.ts` — `checkForUpdates()` function, called during initialization
- `~/.tauri/parsec.key` — Ed25519 signing keypair (permanent infrastructure)
