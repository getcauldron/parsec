---
estimated_steps: 5
estimated_files: 7
---

# T02: Wire Rust sidecar manager and prove hello-world JSON exchange

**Slice:** S02 — Tauri Shell + Python Sidecar
**Milestone:** M001

## Description

The core integration proof. Creates a dev-mode shell wrapper script so Tauri can spawn the Python sidecar during development, writes the Rust sidecar manager that handles spawning and stdin/stdout communication, configures shell plugin permissions, and proves the full roundtrip: Tauri sends `{"cmd":"hello"}` → Python sidecar responds → Tauri displays the result in the window.

This retires the "sidecar communication reliability" risk from the M001 roadmap.

## Steps

1. Create the dev-mode shell wrapper script at `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin`. This is a bash script that invokes `python -u backend/parsec/sidecar.py` using the backend venv's Python. Make it executable. The `-u` flag adds unbuffered IO as an extra safety layer on top of sidecar.py's own line buffering.
2. Configure `src-tauri/tauri.conf.json`: add `"externalBin": ["binaries/parsec-sidecar"]` under `bundle` (Tauri auto-appends the target triple). Configure shell plugin permissions in `src-tauri/capabilities/default.json` with `shell:allow-spawn` and `sidecar: true` scoping.
3. Write `src-tauri/src/sidecar.rs`:
   - Use `tauri_plugin_shell::ShellExt` to get the shell handle.
   - `spawn_sidecar()` — spawns `parsec-sidecar`, stores the `CommandChild` in `Mutex<Option<CommandChild>>` managed state.
   - `send_command()` — writes a JSON line to the sidecar's stdin.
   - Handle `CommandEvent::Stdout` — parse JSON lines, forward to frontend via Tauri events.
   - Handle `CommandEvent::Terminated` — log exit status, clear the stored child.
   - `kill_sidecar()` — kills the stored child process.
4. Wire into `src-tauri/src/lib.rs`:
   - Register the sidecar state.
   - Spawn sidecar on app setup (after plugins are initialized).
   - Expose a `greet_sidecar` Tauri command that sends hello and returns the response.
   - Kill sidecar on app exit.
5. Update `src/main.ts` and `src/index.html`:
   - Add a button that invokes `greet_sidecar` command.
   - Display the sidecar's response in the page.
   - Show connection status (spawning / connected / error).

## Must-Haves

- [ ] Dev wrapper script at correct binary path, executable, uses venv Python
- [ ] `tauri.conf.json` has `externalBin` configured correctly (no target triple in config)
- [ ] Shell plugin capabilities include `shell:allow-spawn` with sidecar scope
- [ ] Rust sidecar manager spawns process, reads stdout events, writes to stdin
- [ ] Frontend can invoke `greet_sidecar` and see the response
- [ ] Sidecar is killed when the app closes (no orphan processes)
- [ ] Dev workflow: `cargo tauri dev` launches app and sidecar with zero manual steps

## Verification

- `cargo tauri dev` — app window opens, sidecar spawns automatically
- Click "Hello Sidecar" button → response appears in the window
- Close the app → verify no orphan `parsec-sidecar` or `python` processes remain (`pgrep -f sidecar`)
- The dev wrapper script resolves the correct venv Python path

## Observability Impact

- Signals added: Rust `log::info!` for sidecar spawn/exit events, `log::error!` for communication failures
- How a future agent inspects this: `cargo tauri dev` console output shows sidecar lifecycle events
- Failure state exposed: sidecar exit code logged, frontend shows error state if sidecar dies

## Inputs

- `backend/parsec/sidecar.py` — the protocol handler from T01
- `src-tauri/` — scaffolded Tauri app from T01
- S02 research — `tauri-plugin-shell` API patterns, `CommandEvent::Stdout`, `child.write()`, capability JSON format

## Expected Output

- `src-tauri/binaries/parsec-sidecar-aarch64-apple-darwin` — dev wrapper script
- `src-tauri/src/sidecar.rs` — Rust sidecar manager module
- `src-tauri/src/lib.rs` — updated with sidecar integration
- `src-tauri/tauri.conf.json` — updated with externalBin
- `src-tauri/capabilities/default.json` — updated with shell permissions
- `src/main.ts` — frontend invoking greet_sidecar
- `src/index.html` — button and response display area
