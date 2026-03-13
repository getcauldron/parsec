# S02: Auto-Update Wiring — Research

**Date:** 2026-03-12

## Summary

This slice wires up `tauri-plugin-updater` and `tauri-plugin-process` so the app can check for updates via a GitHub Releases endpoint. The work is well-scoped: add two Rust plugins, two npm packages, generate a signing keypair, configure `tauri.conf.json` with the public key + endpoint, add updater + process permissions to capabilities, and add a lightweight update-check flow in the frontend. No custom update server, no download-progress UI needed for this slice — M003's release workflow will produce the actual `latest.json` + signed artifacts.

The biggest risk was CSP blocking the update check HTTP call, but that's a non-issue — `check()` calls into the Rust plugin via IPC, and the actual HTTP request to GitHub happens on the Rust side, completely outside the WebView's CSP. The only real unknowns are: (1) whether `createUpdaterArtifacts` changes the build output in any surprising way, and (2) the `TAURI_SIGNING_PRIVATE_KEY` env var must be set during `cargo tauri build` for signing to work — it's not read from `.env`. Both are easy to verify during execution.

No active requirements explicitly cover auto-updates (M002 Research flagged this gap). This slice implements capability described in the M002 roadmap and established by D040 (auto-update via GitHub Releases). The closest requirement is R013 (downloadable installer), which this slice extends with update delivery infrastructure.

## Recommendation

Wire everything in one pass: Rust plugins → npm packages → keypair → tauri.conf.json → capabilities → frontend update check. Verify by running `cargo tauri dev`, confirming the app starts without errors, and calling `check()` — it should hit the (non-existent) `latest.json` endpoint and gracefully handle the 404 as "no update available." Then do a release build to verify `createUpdaterArtifacts` produces `.sig` files alongside the bundle artifacts.

Keep the frontend update check minimal — a non-blocking call on app startup that logs the result. No modal dialogs, no download progress bars. If an update is found (which won't happen until M003 publishes releases), console-log it. The UI surface for presenting updates can be added in S03 or M003 as needed.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Update check + download + install | `tauri-plugin-updater` (Rust + JS) | Official Tauri v2 plugin, handles signature verification, platform-specific install, download progress callbacks |
| App relaunch after update | `tauri-plugin-process` (Rust + JS) | Official plugin, `relaunch()` function, needed after `downloadAndInstall()` |
| Signing keypair generation | `pnpm tauri signer generate -w ~/.tauri/parsec.key` | Ed25519 keypair, outputs public key to stdout and private key to file |
| Update artifact generation | `createUpdaterArtifacts: true` in `tauri.conf.json` | Tauri build automatically generates `.sig` files + update bundles when `TAURI_SIGNING_PRIVATE_KEY` is set |
| `latest.json` publishing | `tauri-apps/tauri-action` in CI (M003) | Automatically generates `latest.json` with platform URLs and signatures during release builds |

## Existing Code and Patterns

- `src-tauri/src/lib.rs` — Plugin chain: `tauri_plugin_shell::init()` then `tauri_plugin_store::Builder::new().build()`. Updater uses a different pattern: `app.handle().plugin(tauri_plugin_updater::Builder::new().build())` inside `.setup()` — **must be registered in setup, not in the builder chain**. Process plugin uses the normal `tauri_plugin_process::init()` pattern.
- `src-tauri/Cargo.toml` — Currently has `tauri`, `tauri-plugin-shell`, `tauri-plugin-store`, `serde`, `serde_json`, `uuid`, `tokio`. Needs `tauri-plugin-updater` and `tauri-plugin-process` added.
- `package.json` — Has `@tauri-apps/api`, `@tauri-apps/plugin-shell`, `@tauri-apps/plugin-store`. Needs `@tauri-apps/plugin-updater` and `@tauri-apps/plugin-process`.
- `src-tauri/tauri.conf.json` — Needs `"createUpdaterArtifacts": true` in `bundle`, and `plugins.updater` section with `pubkey` and `endpoints`. Currently has no `plugins` key at all.
- `src-tauri/capabilities/default.json` — Needs `"updater:default"` and `"process:allow-restart"` added to permissions array. The updater `default` permission includes `allow-check`, `allow-download`, `allow-download-and-install`, and `allow-install`.
- `src/main.ts` — 333 lines. Update check goes here — a small async function called during initialization, after sidecar status setup. Pattern: `check()` → if update, log/notify → done. No blocking the UI.
- `src-tauri/build.rs` — No changes needed. `createUpdaterArtifacts` is handled by the Tauri bundler, not build.rs.
- `index.html` — Could add an update notification element, but keeping minimal for this slice. Console logging is sufficient.

## Constraints

- **`TAURI_SIGNING_PRIVATE_KEY` must be set as env var during build** — Tauri explicitly does not read this from `.env` files. For local builds: `export TAURI_SIGNING_PRIVATE_KEY=$(cat ~/.tauri/parsec.key)`. For CI (M003): GitHub secret. The private key is permanent infrastructure — losing it means existing users can't update (D040 notes).
- **`TAURI_SIGNING_PRIVATE_KEY_PASSWORD`** — Optional. If the keypair is generated with a password, this must also be set during build. Recommend generating without a password for simplicity (CI compat), relying on file permissions and GitHub secret encryption for security.
- **Updater plugin must be registered in `setup()`, not builder chain** — Unlike most plugins, `tauri_plugin_updater::Builder::new().build()` returns a plugin that must be passed to `app.handle().plugin()` inside the setup closure. This is because it needs the app handle to resolve config.
- **Updater requires HTTPS endpoints in production** — Tauri enforces TLS for update endpoints in release builds. GitHub Releases URLs are HTTPS, so this is fine. Dev mode may need a `dangerousInsecureTransportProtocol` flag or just accept that check() fails in dev (which is expected — no `latest.json` exists yet).
- **`createUpdaterArtifacts` changes build output** — When enabled and `TAURI_SIGNING_PRIVATE_KEY` is set, the build produces additional `.sig` files alongside the normal bundle artifacts. If the key is NOT set, the build may warn or skip signature generation. Need to verify behavior when key is absent (dev builds).
- **GitHub Releases endpoint format** — The URL should be `https://github.com/zakkeown/parsec/releases/latest/download/latest.json`. This is a static JSON file that `tauri-action` in M003 will generate and upload alongside release artifacts. Until M003 creates this, `check()` will 404 and the app should handle this gracefully.
- **Platform keys in `latest.json`** — Format is `OS-ARCH`: `darwin-aarch64`, `darwin-x86_64`, `linux-x86_64`, `windows-x86_64`. M003 CI matrix must match these exactly.

## Common Pitfalls

- **Updater `check()` errors on no endpoint** — If the GitHub endpoint returns 404 (no release published yet), the updater should handle this as "no update available" rather than an error. Need to verify this behavior — may need a try/catch wrapper to treat network errors as "no update."
- **Keypair loss breaks all existing installs** — The private key must be backed up. If lost, every existing installation's updater becomes permanently broken because new releases can't be signed with the old key. Store in a password manager or encrypted backup alongside the CI secret.
- **Forgetting `process:allow-restart`** — The `relaunch()` call requires the process plugin permission. Without it, the app can check and download updates but can't restart to apply them. Easy to miss since it's in a different plugin.
- **`createUpdaterArtifacts` without signing key** — If someone runs `cargo tauri build` without `TAURI_SIGNING_PRIVATE_KEY` set, the build behavior with `createUpdaterArtifacts: true` is unclear — it may error, warn, or silently skip. Need to verify and document.
- **Version string must be valid SemVer** — The `version` in `tauri.conf.json` (currently `"0.1.0"`) is used for update comparison. M003's release tags must also be valid SemVer for the updater to compare versions correctly.

## Open Risks

- **`check()` behavior on 404 endpoint** — Until M003 publishes a release, the GitHub endpoint doesn't exist. The updater might throw an error, return null, or silently fail. This determines whether we need error handling in the frontend call. Low risk — worst case is a try/catch wrapper.
- **`createUpdaterArtifacts` behavior without signing key** — Dev builds won't have the key set. If this causes build failures, we may need to conditionally set this config or accept warnings. Low risk — Tauri likely handles this gracefully.
- **Updater artifact size implications** — `createUpdaterArtifacts` may produce additional bundle formats (e.g., `.tar.gz` + `.sig` on macOS alongside the `.dmg`). This could increase build time and disk usage. Informational only — M003 handles the CI build.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Tauri v2 | `nodnarbnitram/claude-code-extensions@tauri-v2` | available (2.3K installs) — `npx skills add nodnarbnitram/claude-code-extensions@tauri-v2` |
| Tauri v2 | `robinebers/openusage@tauri-v2` | available (33 installs) |

The `nodnarbnitram/claude-code-extensions@tauri-v2` skill at 2.3K installs likely covers updater plugin patterns. Already noted in M002 research. The work here is straightforward enough that docs suffice, but the skill would be useful for S03 and M003 Tauri work.

## Sources

- Tauri updater plugin JS API: `check()`, `downloadAndInstall(progressCallback)` (source: [plugins-workspace](https://github.com/tauri-apps/plugins-workspace/blob/v2/plugins/updater/README.md))
- Tauri updater config: `createUpdaterArtifacts`, `plugins.updater.pubkey`, `plugins.updater.endpoints` (source: [v2.tauri.app/plugin/updater](https://v2.tauri.app/plugin/updater))
- Tauri signer CLI: `pnpm tauri signer generate -w path` generates Ed25519 keypair (source: [v2.tauri.app/reference/cli](https://v2.tauri.app/reference/cli))
- Tauri process plugin: `relaunch()` for post-update restart (source: [plugins-workspace process README](https://github.com/tauri-apps/plugins-workspace/blob/v2/plugins/process/README.md))
- Static JSON format: `version`, `platforms.{OS-ARCH}.{url, signature}`, optional `notes` and `pub_date` (source: [v2.tauri.app/plugin/updater](https://v2.tauri.app/plugin/updater))
- Updater permissions: `updater:default` grants `allow-check`, `allow-download`, `allow-download-and-install`, `allow-install` (source: [plugins-workspace updater permissions](https://github.com/tauri-apps/plugins-workspace/blob/v2/plugins/updater/permissions/autogenerated/reference.md))
- CSP non-issue: `check()` calls Rust via IPC; HTTP to GitHub happens Rust-side, outside WebView CSP — confirmed by Tauri plugin architecture (updater registered as Rust plugin, not a WebView fetch)
