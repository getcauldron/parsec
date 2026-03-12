//! Sidecar process manager — spawns and communicates with the Python OCR backend.
//!
//! The sidecar speaks NDJSON over stdin/stdout: one JSON object per line in each
//! direction. Stderr carries log output only and is forwarded to the Tauri log.
//!
//! Lifecycle:
//! - `spawn_sidecar()` — called during app setup, stores the `CommandChild`.
//! - `send_command()` — writes a JSON line to stdin, returns immediately.
//! - Stdout events are parsed and forwarded to the frontend via Tauri events.
//! - `kill_sidecar()` — called on app exit to clean up the child process.

use std::sync::Mutex;

use serde_json::Value;
use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

/// Managed state holding the sidecar child process.
pub struct SidecarState {
    pub child: Mutex<Option<CommandChild>>,
}

impl SidecarState {
    pub fn new() -> Self {
        Self {
            child: Mutex::new(None),
        }
    }
}

/// Spawn the Python sidecar and wire up event handlers.
///
/// Stores the `CommandChild` in managed state so other commands can write to
/// its stdin or kill it later.
pub fn spawn_sidecar(app: &AppHandle) -> Result<(), String> {
    let shell = app.shell();
    let sidecar_cmd = shell
        .sidecar("parsec-sidecar")
        .map_err(|e| format!("failed to create sidecar command: {e}"))?;

    let (mut rx, child) = sidecar_cmd
        .spawn()
        .map_err(|e| format!("failed to spawn sidecar: {e}"))?;

    eprintln!("[parsec] sidecar spawned (pid: {})", child.pid());

    // Store the child so we can write to stdin and kill later.
    let state = app.state::<SidecarState>();
    {
        let mut guard = state.child.lock().unwrap();
        *guard = Some(child);
    }

    // Spawn async task to read sidecar stdout/stderr events.
    let app_handle = app.clone();

    // Emit connected status after a short delay so the frontend has time to
    // register its event listener.
    let status_handle = app.clone();
    std::thread::spawn(move || {
        std::thread::sleep(std::time::Duration::from_millis(500));
        let _ = status_handle.emit("sidecar-status", "connected");
    });

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line_bytes) => {
                    let line = String::from_utf8_lossy(&line_bytes);
                    let line = line.trim();
                    if line.is_empty() {
                        continue;
                    }

                    match serde_json::from_str::<Value>(line) {
                        Ok(json) => {
                            let _ = app_handle.emit("sidecar-response", json);
                        }
                        Err(e) => {
                            eprintln!("[parsec] sidecar stdout parse error: {e} — raw: {line}");
                        }
                    }
                }
                CommandEvent::Stderr(line_bytes) => {
                    let line = String::from_utf8_lossy(&line_bytes);
                    eprint!("[sidecar] {line}");
                }
                CommandEvent::Terminated(payload) => {
                    eprintln!(
                        "[parsec] sidecar terminated (code: {:?}, signal: {:?})",
                        payload.code, payload.signal
                    );
                    // Clear the stored child — it's gone.
                    let state = app_handle.state::<SidecarState>();
                    let mut guard = state.child.lock().unwrap();
                    *guard = None;
                    let _ = app_handle.emit("sidecar-status", "disconnected");
                }
                CommandEvent::Error(err) => {
                    eprintln!("[parsec] sidecar event error: {err}");
                }
                _ => {}
            }
        }
    });

    Ok(())
}

/// Send a JSON command to the sidecar's stdin.
pub fn send_command(app: &AppHandle, cmd: &Value) -> Result<(), String> {
    let state = app.state::<SidecarState>();
    let mut guard = state.child.lock().unwrap();

    let child = guard
        .as_mut()
        .ok_or_else(|| "sidecar is not running".to_string())?;

    let mut line = serde_json::to_string(cmd).map_err(|e| format!("JSON serialize error: {e}"))?;
    line.push('\n');

    child
        .write(line.as_bytes())
        .map_err(|e| format!("failed to write to sidecar stdin: {e}"))?;

    Ok(())
}

/// Kill the sidecar process if it's running.
pub fn kill_sidecar(app: &AppHandle) {
    let state = app.state::<SidecarState>();
    let mut guard = state.child.lock().unwrap();

    if let Some(child) = guard.take() {
        eprintln!("[parsec] killing sidecar (pid: {})", child.pid());
        let _ = child.kill();
    }
}
