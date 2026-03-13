# M002: Distribution & Polish — Research

**Date:** 2026-03-12

## Summary

M002 has a dependency inversion problem. The context says "M003 must complete first — M002 depends on CI release builds from M003 to produce the installers that auto-update distributes." But auto-update configuration, UX polish, and cross-platform verification are all things that need working installers to test. The practical approach: M002 should wire up the updater plugin, polish the UI, and handle sidecar bundling concerns locally — then rely on M003's CI workflows to produce the actual release artifacts. The bulk of M002's work is things that can be built and tested on the local machine or with local `cargo tauri build` invocations.

The biggest technical risk is **sidecar bundling for distribution**. The current PyInstaller `--onedir` mode produces a folder (`parsec-sidecar/` + `_internal/`), but Tauri's `externalBin` only bundles a single binary file. This is a known Tauri limitation (see tauri-apps/tauri#5719). The two paths are: (1) switch to `--onefile` mode which produces a single binary but has a known process-kill bug where Tauri can't kill the PyInstaller bootloader's child process, or (2) keep `--onedir` and use Tauri's `resources` config to bundle the `_internal/` folder alongside the main binary. Option 2 is better — it avoids the kill bug, has faster startup (no temp extraction), and the sidecar module already handles process lifecycle.

Auto-update is well-supported by Tauri v2. The `tauri-plugin-updater` with `createUpdaterArtifacts: true` in the bundle config, plus a signing keypair, plus `tauri-action` in CI (M003), produces `latest.json` + `.sig` files automatically. M002's job is to wire up the plugin, generate the signing keypair, configure the endpoint, and add the update-check UI. The actual CI workflow that builds and publishes releases belongs to M003.

## Recommendation

**Prove sidecar bundling first.** This is the riskiest unknown — if `--onedir` + `resources` doesn't work, the entire distribution strategy needs rethinking. Build a local macOS DMG with `cargo tauri build`, verify the sidecar launches from inside the bundle, processes a file, and gets killed cleanly on exit.

Then wire up auto-update (plugin + config + keypair + UI), then do UX polish. Cross-platform verification comes last since it's blocked on M003 CI runners for Windows/Linux.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Auto-update checking/downloading | `tauri-plugin-updater` + `tauri-plugin-process` (relaunch) | Official Tauri v2 plugin, handles signature verification, download progress, platform-specific install logic |
| Update artifact signing | `pnpm tauri signer generate` | Generates Ed25519 keypair; `TAURI_SIGNING_PRIVATE_KEY` env var signs bundles during build; `.sig` files auto-generated |
| Update endpoint JSON | `tauri-action` with `createUpdaterArtifacts: true` | Automatically generates `latest.json` with platform URLs and signatures when building releases in CI |
| Cross-platform CI builds | `tauri-apps/tauri-action@v0` GitHub Action | Matrix strategy across macOS/Windows/Linux runners, handles Rust/Node setup, uploads release artifacts |
| macOS code signing | Apple Developer Certificate + Tauri's built-in signing support | `tauri.conf.json` `mac.signingIdentity` + keychain import in CI; hardened runtime for notarization |
| Windows code signing | `tauri.conf.json` `windows.certificateThumbprint` | Tauri handles signing during MSI build; timestamp server for long-term verification |

## Existing Code and Patterns

- `src-tauri/tauri.conf.json` — Bundle config with `externalBin: ["binaries/parsec-sidecar"]`. Needs `createUpdaterArtifacts`, `plugins.updater` config, and `resources` for sidecar `_internal/` folder
- `src-tauri/build.rs` — Copies sidecar binary with target-triple suffix. May need adjustment for `--onedir` folder bundling
- `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` — Shell wrapper script that falls back to venv Python in dev mode. For distribution, this needs to be the actual PyInstaller binary
- `backend/build_sidecar.sh` — PyInstaller `--onedir` build script with extensive `--collect-all` and `--hidden-import` flags. Working spec file at `parsec-sidecar.spec`
- `backend/parsec/sidecar_entry.py` — PyInstaller entrypoint with stdout line-buffering and C++ noise suppression. Critical for binary mode
- `src-tauri/src/sidecar.rs` — Sidecar process manager with spawn/kill lifecycle. Uses `ShellExt::sidecar()` which expects target-triple-suffixed binary in `externalBin`
- `src-tauri/src/lib.rs` — App setup with `tauri_plugin_shell` and `tauri_plugin_store`. Needs `tauri_plugin_updater` added to plugin chain
- `src/main.ts` — Drop zone UI with progress tracking. Polish candidates: animations, responsive layout, empty state, completion summary
- `src/settings.ts` — Settings panel with language picker and preprocessing toggles. Already uses `@tauri-apps/plugin-store` for persistence
- `src/styles.css` — Industrial dark theme (D030). Polish candidates: transitions, hover states, scrollbar styling, typography refinement
- `src-tauri/capabilities/default.json` — Permission config. Needs updater permissions added

## Constraints

- **PyInstaller `--onedir` folder bundling** — Tauri's `externalBin` only bundles a single file. The `_internal/` directory (~hundreds of MB) must go through `bundle.resources` and the sidecar must be able to find it at runtime. This requires either: (a) setting `LD_LIBRARY_PATH`/`DYLD_LIBRARY_PATH` or (b) ensuring PyInstaller's `_internal/` folder is adjacent to the binary in the installed app
- **Sidecar binary is platform-specific** — PyInstaller output is not cross-platform. Each OS needs its own CI runner to build the sidecar. The bash wrapper script in `src-tauri/binaries/` must be replaced with actual binaries for each target triple
- **Signing keypair for updates** — `TAURI_SIGNING_PRIVATE_KEY` must be set during build (not in `.env` — Tauri explicitly doesn't support that). The public key goes in `tauri.conf.json`. Keypair must be generated once and stored securely
- **Code signing certificates cost money** — Apple Developer Program ($99/yr), Windows Authenticode certificates (~$200-500/yr). Without them, macOS shows Gatekeeper warnings and Windows shows SmartScreen warnings. Functional but not smooth for end users
- **PaddleOCR models downloaded on first use** — ~15MB per language model. Production app may need to pre-bundle English model or handle first-run download gracefully
- **`unpaper` system dependency** — The `clean` preprocessing toggle requires `unpaper` which may not be on the user's system. Need UI gating or bundling
- **Python 3.13 venv** — Current dev uses Homebrew Python 3.13. PyInstaller binary embeds the Python runtime, so version matters less for distribution, but CI runners need matching Python version
- **macOS universal binary** — Supporting both aarch64 and x86_64 means either two separate builds or a universal binary. `tauri-action` supports both targets in matrix strategy

## Common Pitfalls

- **PyInstaller `--onefile` process kill bug** — Using `--onefile` mode means the PyInstaller bootloader extracts to a temp dir and spawns a child process. Tauri's `child.kill()` only kills the bootloader, leaving the real Python process orphaned. The current `--onedir` mode avoids this. Don't switch to `--onefile` just because bundling is simpler
- **Sidecar can't find `_internal/` at runtime** — When bundled via `resources`, the `_internal/` folder may not end up adjacent to the sidecar binary. PyInstaller's `--onedir` binary expects `_internal/` to be a sibling directory. Need to verify the final installed directory layout on each platform and potentially adjust `resources` source/target mapping
- **Update signature mismatch** — If the keypair is regenerated, existing installations can't verify new updates. The private key must be treated as permanent infrastructure. Losing it means all existing users must manually reinstall
- **CSP blocks update checks** — Current CSP in `tauri.conf.json` is `connect-src 'self' ipc: http://ipc.localhost`. The updater needs to reach GitHub's API. Tauri's updater plugin may bypass CSP (it runs in Rust, not WebView), but the JS-side `check()` call needs verification
- **macOS Gatekeeper without notarization** — Even with code signing, macOS Sequoia and later may quarantine apps that aren't notarized with Apple. Notarization requires `xcrun notarytool submit` in CI, which needs Apple ID + app-specific password
- **Bundle size explosion** — PyInstaller `--onedir` with `--collect-all paddleocr` pulls in NumPy, SciPy, OpenCV, PaddlePaddle, etc. Expect 500MB-1GB+ sidecar folder. This is the installed size — DMG/MSI compression helps but the download is still large
- **Windows path length limits** — PyInstaller `_internal/` contains deeply nested Python packages. Windows has a 260-char path limit by default. `--onedir` with long package names can hit this during extraction or install

## Open Risks

- **Sidecar bundling may require architecture changes** — If `resources` + `externalBin` doesn't work for `--onedir`, may need to switch to spawning the sidecar differently (e.g., `Command::new()` with explicit path instead of `ShellExt::sidecar()`)
- **Cross-platform sidecar builds need CI (M003)** — Can only build/test macOS sidecar locally. Windows and Linux sidecar binaries must wait for M003 CI workflows. M002 can prove the pattern on macOS; cross-platform verification may be partially deferred
- **Bundle size may be unacceptable** — If the PaddleOCR sidecar is 800MB+, the download experience is poor. Mitigation options: strip unused packages from PyInstaller, use `--exclude` flags, or investigate Nuitka as alternative compiler (D006 notes this as fallback)
- **`unpaper` dependency for `clean` toggle** — Not available on all platforms, not easy to bundle. May need to disable or gate the toggle when `unpaper` is missing
- **Code signing decision** — Open question from context. Without signing: macOS Gatekeeper "unidentified developer" warning, Windows SmartScreen "unknown publisher" warning. Both are dismissible but hurt trust. Decision needed before M002 execution

## Candidate Requirements

These emerged from research and should be explicitly decided during roadmap planning:

- **Auto-update notification + install flow** — Currently R013 (downloadable installer) exists but no requirement for auto-updates. The M002 context describes auto-update as in-scope. Consider adding a requirement for it
- **First-run model download UX** — PaddleOCR downloads models on first use. No requirement exists for handling this gracefully (progress indicator, offline fallback, pre-bundled English model)
- **Bundle size budget** — No requirement constrains the installer download size. With PaddleOCR dependencies, this could be 500MB+. Should there be a target?
- **Unsigned app warning handling** — If code signing is deferred, the app should at minimum not break when Gatekeeper/SmartScreen intervenes. May need documentation or UI guidance for users

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Tauri v2 | `nodnarbnitram/claude-code-extensions@tauri-v2` | available (2.3K installs) |
| Tauri v2 | `martinholovsky/claude-skills-generator@tauri` | available (233 installs) |
| PyInstaller | (search timed out) | none found |

The `tauri-v2` skill at 2.3K installs is worth considering — it may have useful patterns for updater plugin wiring and bundle configuration. Install command: `npx skills add nodnarbnitram/claude-code-extensions@tauri-v2`

## Sources

- Tauri v2 updater plugin docs (source: [v2.tauri.app/plugin/updater](https://v2.tauri.app/plugin/updater)) — static JSON file format, signing keypair generation, endpoint configuration, `createUpdaterArtifacts` bundle option
- Tauri v2 sidecar docs (source: [v2.tauri.app/develop/sidecar](https://v2.tauri.app/develop/sidecar)) — `externalBin` expects target-triple-suffixed binaries, only bundles single files per entry
- Tauri v2 resources docs (source: [v2.tauri.app/develop/resources](https://v2.tauri.app/develop/resources)) — `bundle.resources` for additional files/directories, supports glob patterns, preserves directory structure under `$RESOURCES/`
- Tauri v2 macOS signing docs (source: [v2.tauri.app/distribute/sign/macos](https://v2.tauri.app/distribute/sign/macos)) — certificate import in CI, `signingIdentity` config, keychain management
- Tauri v2 GitHub Actions pipeline (source: [v2.tauri.app/distribute/pipelines/github](https://v2.tauri.app/distribute/pipelines/github)) — `tauri-action@v0` matrix strategy, release artifact uploading
- Tauri plugins workspace (source: [github.com/tauri-apps/plugins-workspace](https://github.com/tauri-apps/plugins-workspace)) — updater plugin JS API: `check()`, `downloadAndInstall()`, `relaunch()`
- M001 summary — forward intelligence about sidecar bundling, model downloads, and missing heartbeat/timeout
