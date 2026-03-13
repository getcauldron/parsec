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

# === PADDLEX OFFLINE MODEL PATCH ===
# PaddleX 3.x requires network health checks before loading models, even when
# they're already cached locally (a design limitation). In a PyInstaller bundle,
# the HTTPS health checks may fail due to SSL/cert resolution differences.
# This patch allows PaddleX to use locally cached models without network access.
def _patch_paddlex_offline():
    """Monkey-patch PaddleX _ModelManager to check local cache before requiring network."""
    try:
        from paddlex.inference.utils import official_models
        from pathlib import Path

        original_get = official_models._ModelManager._get_model_local_path

        def _get_model_local_path_offline(self, model_name):
            # Check local cache first — if models exist on disk, use them directly
            model_dir = self._save_dir / f"{model_name}"
            if model_dir.exists():
                import logging
                logging.getLogger("paddlex").info(
                    "Using cached model (offline): %s", model_dir
                )
                return model_dir
            # Fall back to original behavior (requires network)
            return original_get(self, model_name)

        official_models._ModelManager._get_model_local_path = _get_model_local_path_offline
    except Exception:
        pass  # If paddlex isn't available, skip silently

_patch_paddlex_offline()

# Now import and run the sidecar
from parsec.sidecar import main

if __name__ == "__main__":
    main()
