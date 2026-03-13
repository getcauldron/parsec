mod sidecar;

use serde_json::{json, Value};
use std::sync::mpsc;
use std::time::Duration;
use tauri::ipc::Channel;
use tauri::{Emitter, Listener, Manager};
use uuid::Uuid;

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

/// Tauri command: fetch the list of supported languages from the sidecar.
///
/// Sends `{"cmd":"get_languages"}` and waits for the response (routed via the
/// global `sidecar-response` event since it's not a progress event).
#[tauri::command]
async fn get_languages(app: tauri::AppHandle) -> Result<Value, String> {
    let (tx, rx) = mpsc::channel::<Value>();

    let id = app.listen("sidecar-response", move |event| {
        if let Ok(payload) = serde_json::from_str::<Value>(event.payload()) {
            // Capture the languages response (has "languages" array and "status":"ok")
            if payload.get("languages").is_some() {
                let _ = tx.send(payload);
            }
        }
    });

    sidecar::send_command(&app, &json!({"cmd": "get_languages"}))?;

    let result = rx
        .recv_timeout(Duration::from_secs(10))
        .map_err(|_| "get_languages response timeout (10s)".to_string());

    app.unlisten(id);
    result
}

/// Tauri command: process files through the OCR sidecar with streaming progress.
///
/// Files are dispatched sequentially (PaddleOCR is single-threaded). Each file
/// gets a UUID request ID. Progress events from the sidecar are streamed back
/// through the Channel to the frontend in real-time.
///
/// Progress event shape: `{"type":"progress","id":"...","stage":"queued|initializing|processing|complete|error",...}`
#[tauri::command]
async fn process_files(
    app: tauri::AppHandle,
    paths: Vec<String>,
    language: Option<String>,
    deskew: Option<bool>,
    rotate_pages: Option<bool>,
    clean: Option<bool>,
    force_ocr: Option<bool>,
    channel: Channel<Value>,
) -> Result<(), String> {
    let lang = language.as_deref().unwrap_or("en");
    eprintln!(
        "[parsec] process_files called with {} path(s), language={lang}",
        paths.len()
    );

    for path in &paths {
        let request_id = Uuid::new_v4().to_string();
        eprintln!("[parsec] dispatching file path={path} id={request_id}");

        // Check if sidecar is running before registering channel.
        {
            let state = app.state::<SidecarState>();
            let guard = state.child.lock().unwrap();
            if guard.is_none() {
                eprintln!("[parsec] sidecar not running, sending error for id={request_id}");
                let error_event = json!({
                    "type": "progress",
                    "id": request_id,
                    "stage": "error",
                    "error": "Sidecar is not running",
                    "input_path": path,
                });
                let _ = channel.send(error_event);
                continue;
            }
        }

        // Register progress channel for this request ID.
        let state = app.state::<SidecarState>();
        let mut rx = state.register_channel(request_id.clone());

        // Send the process_file command to sidecar.
        let mut cmd = json!({
            "cmd": "process_file",
            "id": request_id,
            "input_path": path,
            "language": lang,
        });
        // Forward preprocessing options when set
        if let Some(v) = deskew {
            cmd["deskew"] = json!(v);
        }
        if let Some(v) = rotate_pages {
            cmd["rotate_pages"] = json!(v);
        }
        if let Some(v) = clean {
            cmd["clean"] = json!(v);
        }
        if let Some(v) = force_ocr {
            cmd["force_ocr"] = json!(v);
        }

        if let Err(e) = sidecar::send_command(&app, &cmd) {
            eprintln!("[parsec] failed to send command for id={request_id}: {e}");
            state.unregister_channel(&request_id);
            let error_event = json!({
                "type": "progress",
                "id": request_id,
                "stage": "error",
                "error": format!("Failed to send command to sidecar: {e}"),
                "input_path": path,
            });
            let _ = channel.send(error_event);
            continue;
        }

        // Read progress events from the per-request channel and forward to the
        // frontend Channel. Stop when we see a terminal stage (complete or error).
        loop {
            match rx.recv().await {
                Some(event) => {
                    let stage = event
                        .get("stage")
                        .and_then(|v| v.as_str())
                        .unwrap_or("")
                        .to_owned();

                    eprintln!(
                        "[parsec] forwarding progress id={request_id} stage={stage}"
                    );

                    // Inject input_path so the frontend can correlate
                    // events to files (sidecar events only carry the id).
                    let mut enriched = event;
                    if let Value::Object(ref mut map) = enriched {
                        map.entry("input_path")
                            .or_insert_with(|| Value::String(path.clone()));
                    }
                    let _ = channel.send(enriched);

                    // Terminal stages — stop listening for this file.
                    if stage == "complete" || stage == "error" {
                        eprintln!("[parsec] file {stage} id={request_id}");
                        break;
                    }
                }
                None => {
                    // Channel closed (sidecar died or channel dropped).
                    eprintln!(
                        "[parsec] progress channel closed unexpectedly for id={request_id}"
                    );
                    let error_event = json!({
                        "type": "progress",
                        "id": request_id,
                        "stage": "error",
                        "error": "Progress channel closed unexpectedly (sidecar may have crashed)",
                        "input_path": path,
                    });
                    let _ = channel.send(error_event);
                    break;
                }
            }
        }

        // Clean up the channel registration.
        let state = app.state::<SidecarState>();
        state.unregister_channel(&request_id);
    }

    eprintln!("[parsec] process_files complete");
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .manage(SidecarState::new())
        .setup(|app| {
            // Updater must be registered inside setup() via app.handle().plugin(),
            // not in the builder chain — this is a tauri-plugin-updater requirement.
            app.handle()
                .plugin(tauri_plugin_updater::Builder::new().build())?;

            let handle = app.handle().clone();

            // Spawn sidecar after plugins are initialized.
            if let Err(e) = sidecar::spawn_sidecar(&handle) {
                eprintln!("[parsec] failed to spawn sidecar: {e}");
                let _ = handle.emit("sidecar-status", "error");
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![greet_sidecar, get_languages, process_files])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                sidecar::kill_sidecar(&window.app_handle());
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
