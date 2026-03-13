# Secrets Manifest

**Milestone:** M002
**Generated:** 2026-03-12

### TAURI_SIGNING_PRIVATE_KEY

**Service:** Tauri Updater (self-generated Ed25519 keypair)
**Dashboard:** N/A — generated locally via `pnpm tauri signer generate`
**Format hint:** Base64-encoded Ed25519 private key (starts with a long base64 string, ~88 chars)
**Status:** pending
**Destination:** dotenv

1. Run `pnpm tauri signer generate -w ~/.tauri/parsec.key` to generate the Ed25519 keypair
2. The command outputs the public key to stdout — copy it into `tauri.conf.json` under `plugins.updater.pubkey`
3. The private key is written to `~/.tauri/parsec.key` — this file's contents become the `TAURI_SIGNING_PRIVATE_KEY` env var
4. Set `TAURI_SIGNING_PRIVATE_KEY` in `.env` for local builds (Tauri reads it during `cargo tauri build`)
5. For CI (M003), store as a GitHub Actions secret

### TAURI_SIGNING_PRIVATE_KEY_PASSWORD

**Service:** Tauri Updater (optional password for the signing key)
**Dashboard:** N/A — set during `pnpm tauri signer generate` if a password is chosen
**Format hint:** Freeform passphrase (can be empty if no password set during generation)
**Status:** pending
**Destination:** dotenv

1. During `pnpm tauri signer generate`, you're prompted for an optional password
2. If a password is set, it must be provided as `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` during builds
3. For simplicity, consider generating without a password for local dev (press Enter to skip)
4. If using a password, set it in `.env` for local builds and as a GitHub Actions secret for CI
