"""Shared pytest fixtures for OCR quality tests.

Provides a session-scoped engine instance (avoids ~4s cold start per test),
fixture directory path, and ground truth loading helpers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from parsec.paddle_engine import PaddleOcrEngine

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def engine() -> PaddleOcrEngine:
    """Session-scoped PaddleOCR engine — single cold start for entire suite."""
    return PaddleOcrEngine()


@pytest.fixture
def fixture_dir() -> Path:
    """Path to the test fixtures directory."""
    return FIXTURE_DIR


def load_ground_truth(image_path: Path) -> str:
    """Load the ground truth text for a fixture image.

    Expects a .gt.txt file alongside the image with the same stem.
    Example: clean_01.png -> clean_01.gt.txt
    """
    gt_path = image_path.with_suffix(".gt.txt")
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth not found: {gt_path}")
    return gt_path.read_text(encoding="utf-8").strip()
