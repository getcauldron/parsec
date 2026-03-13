#!/usr/bin/env python3
"""Cross-platform PyInstaller build script for the Parsec sidecar.

Replicates every flag from build_sidecar.sh in a platform-independent way.
Designed for CI (no venv assumption) but works locally too.

Usage:
    python3 backend/build_sidecar.py             # build the sidecar
    python3 backend/build_sidecar.py --dry-run    # print PyInstaller command only
    python3 backend/build_sidecar.py --help       # show help
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# --- PyInstaller flag catalog (source of truth: build_sidecar.sh) -----------

COLLECT_ALL = [
    "paddleocr",
    "pyclipper",
    "skimage",
    "imgaug",
    "lmdb",
    "ocrmypdf_paddleocr",
    "ocrmypdf",
]

COLLECT_DATA = [
    "paddle",
    "paddlex",
    "scipy",
    "shapely",
]

HIDDEN_IMPORTS = [
    "PIL",
    "PIL._tkinter_finder",
    "cv2",
    "lmdb",
    "pyclipper",
    "shapely",
    "skimage",
    "scipy.io",
    "scipy.special",
    "scipy.ndimage",
    "yaml",
    "requests",
    "tqdm",
    "packaging",
    "parsec.sidecar",
    "parsec.paddle_engine",
    "parsec.engine",
    "parsec.models",
    "parsec.pipeline",
    "ocrmypdf_paddleocr",
]

COPY_METADATA = [
    "imagesize",
    "opencv-contrib-python",
    "pyclipper",
    "pypdfium2",
    "shapely",
]

SIDECAR_NAME = "parsec-sidecar"
ENTRY_POINT = "parsec/sidecar_entry.py"


def build_pyinstaller_args(backend_dir: Path) -> list[str]:
    """Assemble the full PyInstaller argument list."""
    args: list[str] = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        SIDECAR_NAME,
        "--onedir",
        "--noconfirm",
        "--clean",
        "--log-level",
        "WARN",
    ]

    for pkg in COLLECT_ALL:
        args += ["--collect-all", pkg]

    for pkg in COLLECT_DATA:
        args += ["--collect-data", pkg]

    for mod in HIDDEN_IMPORTS:
        args += ["--hidden-import", mod]

    for pkg in COPY_METADATA:
        args += ["--copy-metadata", pkg]

    args.append(str(backend_dir / ENTRY_POINT))

    return args


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the Parsec sidecar with PyInstaller (cross-platform).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the PyInstaller command without executing it.",
    )
    opts = parser.parse_args()

    # Resolve backend/ directory relative to this script
    backend_dir = Path(__file__).resolve().parent

    args = build_pyinstaller_args(backend_dir)

    if opts.dry_run:
        print("[dry-run] Would execute:")
        print(" ".join(args))
        return 0

    print(f"=== Building {SIDECAR_NAME} with PyInstaller ===")
    print(f"Python: {sys.executable} ({sys.version.split()[0]})")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {backend_dir}")
    print()

    result = subprocess.run(args, cwd=str(backend_dir))

    if result.returncode != 0:
        print(f"\nERROR: PyInstaller exited with code {result.returncode}", file=sys.stderr)
        return result.returncode

    # Locate output binary
    dist_dir = backend_dir / "dist" / SIDECAR_NAME
    if sys.platform == "win32":
        binary_path = dist_dir / f"{SIDECAR_NAME}.exe"
    else:
        binary_path = dist_dir / SIDECAR_NAME

    print()
    print("=== Build complete ===")
    if binary_path.exists():
        size_mb = binary_path.stat().st_size / (1024 * 1024)
        print(f"Binary: {binary_path}")
        print(f"Size:   {size_mb:.1f} MB")
    else:
        print(f"WARNING: Expected binary not found at {binary_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
