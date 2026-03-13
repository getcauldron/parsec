#!/usr/bin/env bash
# Build the Parsec sidecar as a PyInstaller --onedir binary.
#
# Output: backend/dist/parsec-sidecar/parsec-sidecar
# Usage: ./backend/build_sidecar.sh
#
# The binary is placed at a path that can be symlinked or copied into
# src-tauri/binaries/ for Tauri to spawn as a sidecar.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PYTHON=".venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "ERROR: venv Python not found at $SCRIPT_DIR/$VENV_PYTHON" >&2
  exit 1
fi

echo "=== Building parsec-sidecar with PyInstaller ==="
echo "Python: $($VENV_PYTHON --version)"
echo "PyInstaller: $($VENV_PYTHON -m PyInstaller --version)"
echo ""

$VENV_PYTHON -m PyInstaller \
  --name parsec-sidecar \
  --onedir \
  --noconfirm \
  --clean \
  --log-level WARN \
  --collect-all paddleocr \
  --collect-all pyclipper \
  --collect-all skimage \
  --collect-all imgaug \
  --collect-all lmdb \
  --collect-data paddle \
  --collect-data scipy \
  --collect-data shapely \
  --hidden-import PIL \
  --hidden-import PIL._tkinter_finder \
  --hidden-import cv2 \
  --hidden-import lmdb \
  --hidden-import pyclipper \
  --hidden-import shapely \
  --hidden-import skimage \
  --hidden-import scipy.io \
  --hidden-import scipy.special \
  --hidden-import scipy.ndimage \
  --hidden-import yaml \
  --hidden-import requests \
  --hidden-import tqdm \
  --hidden-import packaging \
  --hidden-import parsec.sidecar \
  --hidden-import parsec.paddle_engine \
  --hidden-import parsec.engine \
  --hidden-import parsec.models \
  --hidden-import parsec.pipeline \
  --hidden-import ocrmypdf_paddleocr \
  --collect-all ocrmypdf_paddleocr \
  --collect-all ocrmypdf \
  parsec/sidecar_entry.py

echo ""
echo "=== Build complete ==="
du -sh dist/parsec-sidecar/
echo "Binary: dist/parsec-sidecar/parsec-sidecar"
