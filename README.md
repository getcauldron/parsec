# Parsec

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Desktop OCR application that turns scanned documents and images into searchable PDFs. Built with [Tauri](https://tauri.app), [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR), and [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF).

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Tauri Shell │────▶│  Python Sidecar  │────▶│  PaddleOCR   │
│  (Rust)      │     │  (parsec)        │     │  Engine      │
└──────────────┘     └──────────────────┘     └──────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │  OCRmyPDF        │
                     │  (PDF output)    │
                     └──────────────────┘
```

The Tauri Rust shell manages the desktop window and spawns a Python sidecar process. The sidecar runs PaddleOCR for text recognition and pipes results through OCRmyPDF to produce searchable PDF output.

## Prerequisites

- **Node.js** 22+ and **pnpm** 10+
- **Rust** (stable toolchain)
- **Python** 3.10+
- System dependencies for Tauri — see the [Tauri prerequisites guide](https://v2.tauri.app/start/prerequisites/)

## Getting Started

```bash
# Clone the repo
git clone https://github.com/getcauldron/parsec.git
cd parsec

# Install frontend dependencies
pnpm install

# Install the Python backend in editable mode
pip install -e ./backend

# Run the app in development mode
pnpm tauri dev
```

## Project Structure

```
parsec/
├── backend/          # Python sidecar — OCR pipeline
│   ├── parsec/       # Package source
│   └── tests/        # Python tests
├── src/              # Frontend (TypeScript + Vite)
├── src-tauri/        # Tauri Rust shell
│   └── src/
└── .github/          # CI workflows and templates
```

## Development

```bash
# Lint Python
ruff check backend/

# Type-check TypeScript
npx tsc --noEmit

# Lint Rust
cd src-tauri && cargo clippy --all-targets -- -D warnings
```

## License

[MIT](LICENSE)
