# Architecture

Parsec is a desktop OCR application built from four main components: a Tauri shell, a Python sidecar, PaddleOCR, and OCRmyPDF. This page explains how they fit together.

## System Overview

```
┌──────────────────┐     NDJSON/stdin      ┌──────────────────┐
│   Tauri Shell    │ ───────────────────▶  │  Python Sidecar  │
│   (Rust)         │ ◀───────────────────  │  (parsec)        │
│                  │     NDJSON/stdout      │                  │
│  Desktop window  │                       │  ┌────────────┐  │
│  File handling   │                       │  │ PaddleOCR  │  │
│  System tray     │                       │  │ Engine     │  │
└──────────────────┘                       │  └─────┬──────┘  │
                                           │        │         │
                                           │  ┌─────▼──────┐  │
                                           │  │ OCRmyPDF   │  │
                                           │  │ Pipeline   │  │
                                           │  └────────────┘  │
                                           └──────────────────┘
```

**Data flow:** The user drops a file onto the Tauri window → Tauri sends a `process_file` command to the sidecar via stdin → the sidecar runs PaddleOCR for text recognition → OCRmyPDF produces a searchable PDF → progress events stream back to Tauri via stdout.

## Tauri Shell

The Rust-based Tauri shell handles:

- **Desktop window** — native OS window via webview
- **Sidecar lifecycle** — spawns and manages the Python process via Tauri's `externalBin` mechanism
- **File I/O** — receives drag-and-drop files, writes output PDFs
- **IPC** — bridges frontend JavaScript calls to sidecar commands

Tauri was chosen over Electron for its smaller binary size, lower memory usage, and native system integration.

## NDJSON Sidecar Protocol

The Tauri shell and Python sidecar communicate over stdin/stdout using newline-delimited JSON (NDJSON). Stderr is reserved for logging — it never carries protocol data.

### Commands

**hello** — Health check. Returns the sidecar version.

```json
→ {"cmd": "hello"}
← {"status": "ok", "message": "parsec sidecar ready", "version": "0.1.0", "id": null}
```

**status** — Runtime status including uptime and engine state.

```json
→ {"cmd": "status"}
← {"status": "ok", "uptime_seconds": 12.3, "engine_ready": false, "id": null}
```

**process_file** — The core operation. Emits progress events as the file moves through the pipeline.

```json
→ {"cmd": "process_file", "id": "req-1", "input_path": "/path/to/scan.png"}
← {"type": "progress", "id": "req-1", "stage": "queued"}
← {"type": "progress", "id": "req-1", "stage": "processing"}
← {"type": "progress", "id": "req-1", "stage": "complete", "output_path": "...", "duration": 1.23}
```

**get_languages** — Returns the full list of supported languages with codes.

All responses include the `id` from the request (or `null` for commands that don't require one). Errors return `{"status": "error", "error": "message", "id": ...}`.

### Buffering

Stdout is forced to line-buffered mode at sidecar startup. This is critical — PyInstaller binaries fully buffer stdout when spawned from a parent process, which would silently break communication. The sidecar calls `sys.stdout.reconfigure(line_buffering=True)` before any other imports.

## Abstract Engine Interface

The OCR engine is behind an abstract interface (`OcrEngine`), making it straightforward to swap PaddleOCR for another engine (Tesseract, EasyOCR, etc.) without changing the pipeline.

```python
class OcrEngine(ABC):
    @abstractmethod
    def recognize(self, image_path: Path, options: OcrOptions | None = None) -> list[TextRegion]:
        """Run OCR on an image and return recognized text regions."""

    @abstractmethod
    def name(self) -> str:
        """Return the engine's human-readable name."""

    @abstractmethod
    def version(self) -> str:
        """Return the engine's version string."""
```

Each `TextRegion` contains the recognized `text`, a bounding `bbox` (x1, y1, x2, y2), and a `confidence` score (0.0–1.0).

## OCRmyPDF Pipeline

The pipeline module (`parsec.pipeline`) orchestrates the final PDF production:

1. Validates the input file exists and has a supported extension
2. Translates the PaddleOCR language code to Tesseract's ISO 639-2 format
3. Applies preprocessing options (deskew, rotation, cleaning)
4. Calls OCRmyPDF with the PaddleOCR plugin to produce a searchable PDF
5. Returns a `ProcessResult` with timing, status, and file paths

OCRmyPDF handles the complex work of layering invisible text over the original image at the correct positions, making the result searchable while preserving the visual appearance.

## Sidecar Bundling

For distribution, the Python sidecar is packaged as a standalone binary using PyInstaller. This means end users don't need Python installed.

The binary is placed in the Tauri `externalBin` directory and shipped alongside the app. Tauri's sidecar mechanism handles platform-specific binary naming and spawning.

```
src-tauri/
├── binaries/
│   └── parsec-sidecar-{target-triple}   # PyInstaller binary
└── tauri.conf.json                       # externalBin config
```

The build pipeline compiles the sidecar for each target platform (macOS, Windows, Linux) as part of the CI release process.
