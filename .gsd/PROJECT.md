# Project

## What This Is

Parsec is a cross-platform desktop app that turns scanned documents (images and non-searchable PDFs) into searchable PDFs. It wraps PaddleOCR and OCRmyPDF behind a drag-and-drop UI built with Tauri. Currently an empty repo — nothing built yet.

## Core Value

Drop files → get searchable PDFs. No terminal, no configuration, no payment. The free alternative to ABBYY FineReader that doesn't suck.

## Current State

Empty repository. No code, no dependencies, no build system.

## Architecture / Key Patterns

Planned architecture:
- **Frontend:** Tauri v2 shell with web-based UI (HTML/CSS/JS or lightweight framework)
- **Backend:** Python sidecar bundled via PyInstaller, running PaddleOCR + OCRmyPDF
- **Communication:** Tauri sidecar API (stdin/stdout JSON protocol between Rust and Python)
- **OCR layer:** Pluggable engine interface — PaddleOCR is default, architecture supports adding Tesseract/others later

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [ ] M001: Core App — OCR backend + Tauri desktop frontend, fully working end-to-end
- [ ] M002: Distribution & Polish — Cross-platform installers, auto-updates, UX refinements
