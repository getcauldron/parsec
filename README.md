# Parsec

[![CI](https://github.com/getcauldron/parsec/actions/workflows/ci.yml/badge.svg)](https://github.com/getcauldron/parsec/actions/workflows/ci.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](LICENSE)

Desktop app that turns scanned documents and images into searchable PDFs. Drop files in, get searchable PDFs out. Supports 49 languages, runs entirely offline.

Built with [Tauri](https://tauri.app), [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR), and [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF).

## Usage

**Drop files onto the window** — Parsec accepts `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`, and `.pdf` files. You can drop one file or many at once. Each file is processed and saved as a searchable PDF alongside the original.

Processing happens locally on your machine. No files are uploaded anywhere.

### OCR Settings

Click the gear icon to configure:

| Setting | Default | What it does |
|---------|---------|--------------|
| **Language** | English | Recognition language — match this to your document for best accuracy. 49 languages available. |
| **DPI** | 300 | Resolution hint for images without embedded DPI metadata. Higher = better for small text, slower. |
| **Deskew** | off | Straightens slightly rotated scans before OCR. |
| **Rotate Pages** | off | Auto-corrects 90°/180°/270° page rotation. |
| **Clean** | off | Removes scan artifacts (noise, dust, shadows) via `unpaper`. |
| **Skip Text** | off | PDF-only. Skips pages that already have a text layer. |
| **Force OCR** | off | Re-OCRs all pages even if text already exists. |

### Supported Languages

Latin script — English, French, German, Spanish, Portuguese, Italian, Dutch, Norwegian, Swedish, Danish, Finnish, Polish, Czech, Slovak, Slovenian, Croatian, Romanian, Hungarian, Turkish, Estonian, Latvian, Lithuanian, Indonesian, Malay, Vietnamese, Latin

CJK — Chinese (Simplified), Chinese (Traditional), Japanese, Korean

Cyrillic — Russian, Ukrainian, Bulgarian

Arabic script — Arabic, Persian, Urdu

Devanagari/Indic — Hindi, Marathi, Nepali, Bengali, Tamil, Telugu, Kannada

Other — Greek, Hebrew, Thai, Myanmar, Khmer, Lao

Full language codes are in the [docs](https://getcauldron.github.io/parsec/guide/usage.html).

### Output

Each input file produces a PDF with an invisible text layer overlaid on the original image. The text is searchable and selectable in any PDF viewer, but the visual appearance is unchanged — you see the original scan with copy-pasteable text underneath.

Output files are saved next to the originals with `_ocr.pdf` appended to the name.

## Install

Download the latest release for your platform from [GitHub Releases](https://github.com/getcauldron/parsec/releases).

| Platform | Format |
|----------|--------|
| macOS (Apple Silicon) | `.dmg` |
| Windows | `.msi` |
| Linux | `.AppImage` |

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Tauri Shell │────▶│  Python Sidecar  │────▶│  PaddleOCR   │
│  (Rust)      │ IPC │  (NDJSON)        │     │  Engine      │
└──────────────┘     └──────────────────┘     └──────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │  OCRmyPDF        │
                     │  (PDF rendering) │
                     └──────────────────┘
```

The Tauri Rust shell manages the desktop window and spawns a Python sidecar process. They communicate over stdin/stdout using NDJSON (newline-delimited JSON). The sidecar runs PaddleOCR for text detection and recognition, then pipes results through OCRmyPDF to produce the final searchable PDF.

The sidecar is bundled as a standalone PyInstaller binary — no Python installation required for end users.

## Build from Source

### Prerequisites

- **Node.js** 22+ and **pnpm** 10+
- **Rust** (stable toolchain)
- **Python** 3.11+
- System dependencies for Tauri — see the [Tauri prerequisites guide](https://v2.tauri.app/start/prerequisites/)

### Setup

```bash
git clone https://github.com/getcauldron/parsec.git
cd parsec

# Frontend dependencies
pnpm install

# Python backend (editable install in a venv)
cd backend
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .[dev]
cd ..

# Run in development mode
pnpm tauri dev
```

### Project Structure

```
parsec/
├── src/              # Frontend (TypeScript + Vite)
├── src-tauri/        # Tauri Rust shell
├── backend/          # Python sidecar — OCR pipeline
│   ├── parsec/       # Package source
│   └── tests/        # Pytest suite + quality benchmarks
├── docs/             # VitePress documentation site
└── .github/          # CI workflows and templates
```

### Lint

```bash
ruff check backend/                                         # Python
npx tsc --noEmit                                            # TypeScript
cd src-tauri && cargo clippy --all-targets -- -D warnings   # Rust
```

### Test

```bash
cd backend
pytest -v
```

The test suite includes CER/WER quality benchmarks that run against reference images. These run automatically on every merge to main via CI.

## Documentation

Full docs at **[getcauldron.github.io/parsec](https://getcauldron.github.io/parsec/)** — usage guide, architecture deep-dive, FAQ, and contributing guide.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, code style, and PR workflow.

## License

[GPL-3.0](LICENSE)
