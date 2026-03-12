import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

const statusEl = document.querySelector("#status") as HTMLParagraphElement;
const greetBtn = document.querySelector("#greet-btn") as HTMLButtonElement;
const responseEl = document.querySelector("#response") as HTMLPreElement;

// Track connection state.
let connected = false;

function setStatus(state: "connecting" | "connected" | "disconnected" | "error") {
  connected = state === "connected";
  greetBtn.disabled = !connected;

  const labels: Record<string, string> = {
    connecting: "⏳ Connecting to sidecar...",
    connected: "✅ Sidecar connected",
    disconnected: "❌ Sidecar disconnected",
    error: "⚠️ Sidecar error",
  };

  statusEl.textContent = labels[state] ?? state;
  statusEl.className = `status status-${state}`;
}

// Listen for sidecar status events from the Rust backend.
listen<string>("sidecar-status", (event) => {
  const state = event.payload as "connected" | "disconnected" | "error";
  setStatus(state);
});

// Greet button handler — sends hello to sidecar via Tauri command.
greetBtn.addEventListener("click", async () => {
  greetBtn.disabled = true;
  responseEl.textContent = "Sending...";

  try {
    const result = await invoke("greet_sidecar");
    responseEl.textContent = JSON.stringify(result, null, 2);
  } catch (err) {
    responseEl.textContent = `Error: ${err}`;
    console.error("greet_sidecar failed:", err);
  } finally {
    greetBtn.disabled = !connected;
  }
});

// Initial state.
setStatus("connecting");
