import { invoke, Channel } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWebview } from "@tauri-apps/api/webview";
import { initSettings, getSelectedLanguage } from "./settings";

// --- Types ---

type FileStage = "queued" | "initializing" | "processing" | "complete" | "error" | "rejected";

interface FileEntry {
  /** Display name (basename) */
  name: string;
  /** Full path on disk */
  path: string;
  stage: FileStage;
  /** Error message for error/rejected state */
  error?: string;
  /** Output filename for complete state */
  outputName?: string;
  /** Duration string for complete state */
  duration?: string;
  /** The DOM card element */
  el: HTMLDivElement;
}

interface ProgressEvent {
  type: string;
  id: string;
  stage: string;
  input_path?: string;
  output_path?: string;
  duration?: number;
  error?: string;
}

// --- State ---

const ACCEPTED_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".tiff", ".tif"]);
const files: Map<string, FileEntry> = new Map();
let isFirstFile = true;
let sidecarConnected = false;

// --- DOM refs ---

const dropZone = document.getElementById("drop-zone") as HTMLDivElement;
const fileList = document.getElementById("file-list") as HTMLDivElement;
const statusIndicator = document.getElementById("sidecar-status") as HTMLDivElement;
const statusLabel = statusIndicator.querySelector(".indicator-label") as HTMLSpanElement;

// --- Sidecar status ---

function setSidecarStatus(state: "connecting" | "connected" | "disconnected" | "error") {
  sidecarConnected = state === "connected";
  statusIndicator.dataset.state = state;

  const labels: Record<string, string> = {
    connecting: "Connecting...",
    connected: "Engine ready",
    disconnected: "Disconnected",
    error: "Error",
  };
  statusLabel.textContent = labels[state] ?? state;
}

listen<string>("sidecar-status", (event) => {
  setSidecarStatus(event.payload as "connected" | "disconnected" | "error");
});

setSidecarStatus("connecting");

// --- Helpers ---

function basename(path: string): string {
  const sep = path.includes("\\") ? "\\" : "/";
  return path.split(sep).pop() ?? path;
}

function getExtension(filename: string): string {
  const dot = filename.lastIndexOf(".");
  return dot === -1 ? "" : filename.slice(dot).toLowerCase();
}

function formatDuration(seconds: number): string {
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  return `${seconds.toFixed(1)}s`;
}

// --- File card rendering ---

function createFileCard(name: string, path: string, stage: FileStage, error?: string): HTMLDivElement {
  const card = document.createElement("div");
  card.className = `file-card file-card--${stage}`;
  card.dataset.path = path;

  card.innerHTML = `
    <div class="file-card-icon">${stageIcon(stage)}</div>
    <div class="file-card-body">
      <span class="file-card-name">${escapeHtml(name)}</span>
      <span class="file-card-status">${stageLabel(stage, error)}</span>
    </div>
  `;

  return card;
}

function updateFileCard(entry: FileEntry): void {
  const card = entry.el;
  // Update class for stage
  card.className = `file-card file-card--${entry.stage}`;

  const iconEl = card.querySelector(".file-card-icon") as HTMLDivElement;
  const statusEl = card.querySelector(".file-card-status") as HTMLSpanElement;

  iconEl.innerHTML = stageIcon(entry.stage);
  statusEl.innerHTML = stageLabel(entry.stage, entry.error, entry.outputName, entry.duration);
}

function stageIcon(stage: FileStage): string {
  switch (stage) {
    case "queued":
      return `<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 2"/></svg>`;
    case "initializing":
      return `<svg class="spin" width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.5" stroke-dasharray="8 12" stroke-linecap="round"/></svg>`;
    case "processing":
      return `<svg class="spin" width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.5" stroke-dasharray="8 12" stroke-linecap="round"/></svg>`;
    case "complete":
      return `<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M7 10l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    case "error":
    case "rejected":
      return `<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M8 8l4 4M12 8l-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`;
  }
}

function stageLabel(stage: FileStage, error?: string, outputName?: string, duration?: string): string {
  switch (stage) {
    case "queued":
      return "Queued";
    case "initializing":
      return "Initializing OCR engine…";
    case "processing":
      return "Processing…";
    case "complete": {
      const parts: string[] = [];
      if (outputName) parts.push(`→ <span class="file-card-output">${escapeHtml(outputName)}</span>`);
      if (duration) parts.push(`<span class="file-card-duration">${duration}</span>`);
      return parts.length ? parts.join(" ") : "Complete";
    }
    case "error":
      return error ? `Error: ${escapeHtml(error)}` : "Error";
    case "rejected":
      return error ? escapeHtml(error) : "Unsupported file type";
  }
}

function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// --- Drop zone state ---

function updateDropZoneVisibility(): void {
  const hasFiles = files.size > 0;
  dropZone.classList.toggle("drop-zone--compact", hasFiles);
}

// --- File processing ---

function addFile(path: string, stage: FileStage, error?: string): FileEntry {
  const name = basename(path);
  const card = createFileCard(name, path, stage, error);
  fileList.appendChild(card);

  const entry: FileEntry = { name, path, stage, error, el: card };
  files.set(path, entry);
  updateDropZoneVisibility();
  return entry;
}

async function processDroppedPaths(paths: string[]): Promise<void> {
  const accepted: string[] = [];

  // Partition into accepted and rejected
  for (const path of paths) {
    const ext = getExtension(basename(path));
    if (ACCEPTED_EXTENSIONS.has(ext)) {
      addFile(path, "queued");
      accepted.push(path);
    } else {
      addFile(path, "rejected", `Unsupported file type: ${ext || "(no extension)"}`);
    }
  }

  if (accepted.length === 0) return;

  if (!sidecarConnected) {
    // Mark all as error if sidecar isn't ready
    for (const path of accepted) {
      const entry = files.get(path);
      if (entry) {
        entry.stage = "error";
        entry.error = "OCR engine not ready — try again in a moment";
        updateFileCard(entry);
      }
    }
    return;
  }

  // Create channel for progress events
  const channel = new Channel<ProgressEvent>();

  channel.onmessage = (event: ProgressEvent) => {
    // Find the file entry by input_path from the event
    // The sidecar sends input_path in progress events
    const inputPath = event.input_path;
    if (!inputPath) {
      console.warn("[parsec-ui] progress event without input_path:", event);
      return;
    }

    const entry = files.get(inputPath);
    if (!entry) {
      console.warn("[parsec-ui] progress event for unknown file:", inputPath);
      return;
    }

    const stage = event.stage as FileStage;
    entry.stage = stage;

    switch (stage) {
      case "initializing":
        if (isFirstFile) {
          // Show initializing state — cold engine start
          entry.stage = "initializing";
          isFirstFile = false;
        } else {
          // After first file, engine is warm — just show processing
          entry.stage = "processing";
        }
        break;
      case "complete":
        if (event.output_path) {
          entry.outputName = basename(event.output_path);
        }
        if (event.duration != null) {
          entry.duration = formatDuration(event.duration);
        }
        break;
      case "error":
        entry.error = event.error ?? "Unknown error";
        break;
    }

    updateFileCard(entry);
    console.log(`[parsec-ui] ${entry.name}: ${entry.stage}`);
  };

  const language = getSelectedLanguage();
  console.log(`[parsec-ui] processing ${accepted.length} file(s) with language=${language}`);

  try {
    await invoke("process_files", { paths: accepted, language, channel });
  } catch (err) {
    console.error("[parsec-ui] process_files invoke error:", err);
    // Mark any still-processing files as errored
    for (const path of accepted) {
      const entry = files.get(path);
      if (entry && entry.stage !== "complete" && entry.stage !== "error") {
        entry.stage = "error";
        entry.error = `Command failed: ${err}`;
        updateFileCard(entry);
      }
    }
  }
}

// --- Drag and drop wiring ---

let dragEnterCount = 0;

async function setupDragDrop(): Promise<void> {
  const webview = getCurrentWebview();

  await webview.onDragDropEvent((event) => {
    switch (event.payload.type) {
      case "enter":
        dragEnterCount++;
        dropZone.classList.add("drop-zone--active");
        break;

      case "leave":
        dragEnterCount--;
        if (dragEnterCount <= 0) {
          dragEnterCount = 0;
          dropZone.classList.remove("drop-zone--active");
        }
        break;

      case "drop":
        dragEnterCount = 0;
        dropZone.classList.remove("drop-zone--active");
        if (event.payload.paths.length > 0) {
          processDroppedPaths(event.payload.paths);
        }
        break;

      // 'over' fires continuously — ignore it
    }
  });
}

setupDragDrop().catch((err) => {
  console.error("[parsec-ui] failed to set up drag-drop:", err);
});

// Initialize settings panel (loads store, fetches languages from sidecar)
initSettings().catch((err) => {
  console.error("[parsec-ui] failed to initialize settings:", err);
});

// Dev-only: expose processDroppedPaths for testing from console/automation
if (import.meta.env.DEV) {
  (window as any).__parsec_test = { processDroppedPaths };
}
