# Contributing

Thanks for your interest in contributing to Parsec. This guide covers development setup, workflow, and expectations.

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

| Tool | Version | Notes |
|------|---------|-------|
| **Node.js** | 22+ | Frontend build tooling |
| **pnpm** | 10+ | Package manager (`corepack enable` to activate) |
| **Rust** | stable | Tauri compiles a native binary |
| **Python** | 3.10+ | OCR sidecar backend |

You also need the platform-specific system dependencies for Tauri. See the [Tauri prerequisites guide](https://v2.tauri.app/start/prerequisites/) for your OS.

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

| Prefix | Purpose |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation changes |
| `chore/` | Tooling, CI, dependencies |

Example: `feat/batch-ocr-processing`

## Pull Request Workflow

1. Create a branch from `main` with the appropriate prefix
2. Make your changes, keeping commits focused
3. Run all three linters locally
4. Push and open a PR using the provided template
5. Fill in the description — explain *what* changed and *why*
6. Wait for CI to pass and request review

### PR Guidelines

- **One logical change per PR** — don't bundle unrelated changes
- **Include tests** for new behavior where applicable
- **Write a clear description** — reviewers aren't mind-readers
- **Keep it small** — smaller PRs get faster, better reviews

## Reporting Issues

Use the issue templates on [GitHub](https://github.com/getcauldron/parsec/issues):

- **Bug report** — include reproduction steps, OS, and version
- **Feature request** — describe the use case and expected behavior

## Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) code of conduct. Be respectful and constructive.
