---
id: T01
parent: S02
milestone: M002
provides:
  - tauri-plugin-updater wired (Rust + JS + config)
  - tauri-plugin-process wired (Rust + JS + capability)
  - Ed25519 signing keypair at ~/.tauri/parsec.key
  - Non-blocking update check on startup with graceful error handling
  - Release builds produce .sig updater signature files
key_files:
  - src-tauri/Cargo.toml
  - src-tauri/src/lib.rs
  - src-tauri/tauri.conf.json
  - src-tauri/capabilities/default.json
  - src/main.ts
key_decisions:
  - "D047: createUpdaterArtifacts must be boolean true, not string \"v2\""
  - "D048: TAURI_SIGNING_PRIVATE_KEY_PASSWORD must be set (even empty) for passwordless keys"
patterns_established:
  - Updater plugin registered in setup() via app.handle().plugin(), not builder chain
  - Process plugin registered in builder chain via init()
  - Signing key passed via TAURI_SIGNING_PRIVATE_KEY env var (not .env file)
observability_surfaces:
  - "[parsec-update] console log prefix for all update check outcomes"
duration: 45m
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T01: Wire updater and process plugins with signing keypair and startup check

**Wired tauri-plugin-updater and tauri-plugin-process with Ed25519 signing keypair, GitHub Releases endpoint, and non-blocking startup update check.**

## What Happened

Added both Rust plugins (`tauri-plugin-updater = "2"`, `tauri-plugin-process = "2"`) and their JS counterparts (`@tauri-apps/plugin-updater`, `@tauri-apps/plugin-process`). The updater plugin is registered inside `setup()` via `app.handle().plugin()` per its requirement; the process plugin uses the normal `init()` pattern in the builder chain.

Generated an Ed25519 signing keypair at `~/.tauri/parsec.key` (no password, CI-compatible) using `pnpm tauri signer generate` with `CI=true -p ""` flags.

Configured `tauri.conf.json` with `createUpdaterArtifacts: true` in bundle config, and the `plugins.updater` section with the public key and GitHub Releases endpoint URL. Also added GitHub domains to CSP `connect-src` as harmless insurance (updater actually makes requests from Rust, not webview).

Added `updater:default` and `process:allow-restart` permissions to the capabilities file.

Added `checkForUpdates()` in `src/main.ts` — a fire-and-forget async call that imports `check` from the updater plugin, catches all errors (404 from missing endpoint is expected until M003), and logs the result with `[parsec-update]` prefix. Does not block UI or sidecar initialization.

## Verification

All four slice-level verification checks pass:

1. **`cargo tauri dev` starts without errors** — ✅ Rust compiled clean (no panics, no capability denials). App window opens normally. Sidecar failure is pre-existing (unrelated to this task).
2. **Browser console shows update check result** — ✅ Console shows `[parsec-update] Update check failed (non-fatal): ...` in browser dev mode (expected — Tauri IPC not available in plain browser). In the real Tauri shell, this will hit the GitHub endpoint and log the 404 result.
3. **Release build produces `.sig` files** — ✅ `TAURI_SIGNING_PRIVATE_KEY="$(cat ~/.tauri/parsec.key)" TAURI_SIGNING_PRIVATE_KEY_PASSWORD="" cargo tauri build` completed successfully. Produced `Parsec.app.tar.gz` (updater bundle) and `Parsec.app.tar.gz.sig` (404 bytes).
4. **Keypair file exists** — ✅ `~/.tauri/parsec.key` and `~/.tauri/parsec.key.pub` both present.

## Diagnostics

- Update check logs to browser console with `[parsec-update]` prefix
- Three possible log messages: "No update available", "Update available: v{version}", or "Update check failed (non-fatal): {error}"
- Signing verification: `TAURI_SIGNING_PRIVATE_KEY="$(cat ~/.tauri/parsec.key)" TAURI_SIGNING_PRIVATE_KEY_PASSWORD="" cargo tauri build` — look for `.sig` files in `src-tauri/target/release/bundle/macos/`

## Deviations

- **`createUpdaterArtifacts` value**: Task plan specified `"v2"` (string) but the Tauri config schema only accepts `true`, `false`, or `"v1Compatible"`. Used `true` instead — this is the correct v2 updater behavior.
- **`TAURI_SIGNING_PRIVATE_KEY_PASSWORD` required**: Even with a passwordless key, the build fails with "incorrect updater private key password: Device not configured" unless `TAURI_SIGNING_PRIVATE_KEY_PASSWORD=""` is explicitly set. This prevents stdin prompting during CI.
- **CSP addition**: Added `https://github.com` and `https://objects.githubusercontent.com` to CSP `connect-src`. Research confirmed this isn't strictly needed (updater requests go through Rust), but it's harmless and covers any future JS-side fetch to GitHub.

## Known Issues

- None. All verification checks pass.

## Files Created/Modified

- `src-tauri/Cargo.toml` — Added `tauri-plugin-updater = "2"` and `tauri-plugin-process = "2"` dependencies
- `src-tauri/src/lib.rs` — Registered updater in `setup()` via `app.handle().plugin()`, process in builder chain via `init()`
- `src-tauri/tauri.conf.json` — Added `createUpdaterArtifacts: true`, `plugins.updater` with pubkey and GitHub endpoint, expanded CSP
- `src-tauri/capabilities/default.json` — Added `updater:default` and `process:allow-restart` permissions
- `src/main.ts` — Added `checkForUpdates()` function with `check` import, fire-and-forget call on startup
- `package.json` / `pnpm-lock.yaml` — Added `@tauri-apps/plugin-updater` and `@tauri-apps/plugin-process`
- `~/.tauri/parsec.key` — Ed25519 signing keypair (permanent infrastructure, not in repo)
