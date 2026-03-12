mod sidecar;

use serde_json::{json, Value};
use std::sync::mpsc;
use std::time::Duration;
use tauri::{Emitter, Listener, Manager};

use crate::sidecar::SidecarState;

/// Tauri command: send `{"cmd":"hello"}` to the sidecar and return the response.
///
/// This uses an event-driven pattern: register a one-shot listener for the
/// sidecar's response event, send the command, then wait for the reply with
/// a timeout.
#[tauri::command]
async fn greet_sidecar(app: tauri::AppHandle) -> Result<Value, String> {
    let (tx, rx) = mpsc::channel::<Value>();

    // Listen for the next sidecar response.
    let id = app.listen("sidecar-response", move |event| {
        if let Ok(payload) = serde_json::from_str::<Value>(event.payload()) {
            let _ = tx.send(payload);
        }
    });

    // Send the hello command.
    sidecar::send_command(&app, &json!({"cmd": "hello"}))?;

    // Wait for response with timeout.
    let result = rx
        .recv_timeout(Duration::from_secs(5))
        .map_err(|_| "sidecar response timeout (5s)".to_string());

    // Clean up the listener.
    app.unlisten(id);

    result
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SidecarState::new())
        .setup(|app| {
            let handle = app.handle().clone();

            // Spawn sidecar after plugins are initialized.
            if let Err(e) = sidecar::spawn_sidecar(&handle) {
                eprintln!("[parsec] failed to spawn sidecar: {e}");
                let _ = handle.emit("sidecar-status", "error");
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![greet_sidecar])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                sidecar::kill_sidecar(&window.app_handle());
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
