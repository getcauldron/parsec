# Contributing to Parsec

Thanks for your interest in contributing. This guide covers development setup, workflow, and expectations.

## Development Setup

```bash
# Clone and enter the repo
git clone https://github.com/getcauldron/parsec.git
cd parsec

# Install frontend dependencies
pnpm install

# Install the Python backend in editable mode (with dev dependencies)
pip install -e "./backend[dev]"

# Verify everything builds
pnpm tauri dev
```

### Prerequisites

- Node.js 22+ and pnpm 10+
- Rust stable toolchain
- Python 3.10+
- System dependencies for Tauri — see the [Tauri prerequisites guide](https://v2.tauri.app/start/prerequisites/)

## Running Linters

CI runs these checks on every PR. Run them locally before pushing:

```bash
# Python — ruff (E/F/W/I rules, line-length 120)
ruff check backend/

# TypeScript — strict type checking
npx tsc --noEmit

# Rust — clippy with warnings as errors
cd src-tauri && cargo clippy --all-targets -- -D warnings
```

All three must pass before a PR will be merged.

## Branch Naming

Use descriptive branch names with a prefix:

- `feat/` — new features
- `fix/` — bug fixes
- `docs/` — documentation changes
- `chore/` — tooling, CI, dependencies

Example: `feat/batch-ocr-processing`

## Pull Requests

- Keep PRs focused — one logical change per PR.
- Fill out the PR template when you open it.
- Make sure CI passes before requesting review.
- Write a clear description of *what* changed and *why*.
- If the PR adds new behavior, include tests or demonstrate the change.

## Reporting Issues

Use the issue templates provided:

- **Bug report** — for something that's broken
- **Feature request** — for new functionality

Include reproduction steps for bugs and a clear use case for features.

## Code of Conduct

Be respectful and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) code of conduct.
