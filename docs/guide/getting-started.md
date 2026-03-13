# Getting Started

This guide walks you through setting up Parsec for local development.

## Prerequisites

You'll need the following installed before building:

| Tool | Version | Notes |
|------|---------|-------|
| **Node.js** | 22+ | JavaScript runtime for the frontend build |
| **pnpm** | 10+ | Package manager (`corepack enable` to activate) |
| **Rust** | stable | Tauri compiles a native shell binary |
| **Python** | 3.10+ | Runs the OCR sidecar backend |

You also need the platform-specific system dependencies for Tauri. See the [Tauri prerequisites guide](https://v2.tauri.app/start/prerequisites/) for your OS.

## Clone and Install

```bash
# Clone the repository
git clone https://github.com/getcauldron/parsec.git
cd parsec

# Install frontend dependencies
pnpm install

# Install the Python backend in editable mode (with dev extras)
pip install -e "./backend[dev]"
```

The editable install (`-e`) means changes to Python files in `backend/parsec/` take effect immediately without reinstalling.

## Run in Development Mode

```bash
pnpm tauri dev
```

This starts:

1. **Vite dev server** — serves the frontend with hot module replacement
2. **Tauri shell** — compiles the Rust binary and opens the desktop window
3. **Python sidecar** — spawned automatically by Tauri when the app needs OCR

The first build takes a few minutes while Rust compiles. Subsequent starts are fast.

## Project Structure

```
parsec/
├── backend/          # Python sidecar — OCR pipeline
│   ├── parsec/       # Package source
│   └── tests/        # Python tests
├── src/              # Frontend (TypeScript + Vite)
├── src-tauri/        # Tauri Rust shell
│   └── src/
├── docs/             # This documentation site (VitePress)
└── .github/          # CI workflows and templates
```

## Verify Your Setup

After `pnpm tauri dev` launches, the app window should appear. Try dropping an image or PDF onto it — if it produces a searchable PDF, everything is wired up correctly.

If something goes wrong, check the [FAQ](./faq.md) for common issues.

## Next Steps

- **[Usage](./usage.md)** — learn about supported formats, OCR options, and language codes
- **[Architecture](./architecture.md)** — understand how the pieces fit together
- **[Contributing](./contributing.md)** — set up your dev environment for contributions
