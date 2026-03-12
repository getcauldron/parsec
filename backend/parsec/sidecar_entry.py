"""PyInstaller entrypoint for the Parsec sidecar.

This is a thin wrapper around sidecar.main() that:
1. Forces line-buffered stdout BEFORE any imports (critical for PyInstaller)
2. Suppresses PaddleOCR/PaddlePaddle C++ noise during import
3. Calls the real protocol handler

Separated from sidecar.py so the protocol handler stays importable
for tests without PyInstaller-specific hacks.
"""

# === STDOUT MUST BE LINE-BUFFERED BEFORE ANYTHING ELSE ===
# PyInstaller binaries fully buffer stdout when spawned from a parent process.
# This breaks the NDJSON sidecar protocol — the parent gets nothing until exit.
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, line_buffering=True)

# === SUPPRESS PADDLEOCR C++ NOISE ===
# PaddleOCR and PaddlePaddle dump noisy C++ output to stdout/stderr during
# import. This would corrupt the JSON protocol if it lands on stdout.
import os
import contextlib

# Set env vars that suppress various paddle/MKL noise before importing anything
os.environ["GLOG_minloglevel"] = "3"  # Suppress glog (paddle's C++ logger)
os.environ["FLAGS_minloglevel"] = "3"
os.environ["PADDLE_LOG_LEVEL"] = "ERROR"
os.environ["KMP_WARNINGS"] = "0"  # Suppress OpenMP warnings
os.environ["MKL_THREADING_LAYER"] = "GNU"

# Now import and run the sidecar
from parsec.sidecar import main

if __name__ == "__main__":
    main()
