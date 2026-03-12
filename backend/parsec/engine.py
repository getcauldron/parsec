"""Abstract OCR engine interface (R012 — swappable engine support).

Implementations: PaddleOcrEngine (default), future: TesseractEngine, etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from parsec.models import OcrOptions, TextRegion


class OcrEngine(ABC):
    """Abstract base class for OCR engines.

    Subclasses must implement recognize(), name(), and version().
    The interface is intentionally minimal — just enough to swap engines
    without coupling the pipeline to any specific OCR toolkit.
    """

    @abstractmethod
    def recognize(self, image_path: Path, options: OcrOptions | None = None) -> list[TextRegion]:
        """Run OCR on an image and return recognized text regions.

        Args:
            image_path: Path to the input image (PNG, JPEG, TIFF).
            options: OCR options (language, DPI). Defaults to English/300dpi.

        Returns:
            List of TextRegion with text, bounding box, and confidence.

        Raises:
            FileNotFoundError: If image_path doesn't exist.
            RuntimeError: If the engine fails to process the image.
        """

    @abstractmethod
    def name(self) -> str:
        """Return the engine's human-readable name (e.g. 'PaddleOCR')."""

    @abstractmethod
    def version(self) -> str:
        """Return the engine's version string."""
