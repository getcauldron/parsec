"""Data models for the OCR pipeline.

These form the boundary contract consumed by S02+ (sidecar protocol, UI).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class TextRegion:
    """A recognized text region with location and confidence.

    Attributes:
        text: Recognized text content.
        bbox: Bounding box as (x1, y1, x2, y2) — top-left and bottom-right corners.
        confidence: Recognition confidence score, 0.0–1.0.
    """

    text: str
    bbox: tuple[float, float, float, float]
    confidence: float


@dataclass
class OcrOptions:
    """Options controlling OCR behavior.

    Attributes:
        language: Language code for recognition (e.g. "en", "ch", "fr").
        dpi: Image DPI — used when source image lacks DPI metadata.
        deskew: Correct page skew (rotation) before OCR.
        rotate_pages: Detect and correct 90°/180°/270° page rotation.
        clean: Remove scan artifacts via unpaper (requires unpaper binary).
        skip_text: OCR only pages without existing text (PDF inputs only).
        force_ocr: Re-OCR all pages, ignoring existing text layers.
    """

    language: str = "en"
    dpi: int = 300
    deskew: bool = False
    rotate_pages: bool = False
    clean: bool = False
    skip_text: bool = False
    force_ocr: bool = False


@dataclass
class ProcessResult:
    """Result of processing a single document through the OCR pipeline.

    Attributes:
        input_path: Path to the source image/document.
        output_path: Path to the generated searchable PDF.
        regions: Recognized text regions from OCR.
        duration_seconds: Wall-clock time for the entire process.
        success: Whether processing completed without errors.
        error: Error message if processing failed, None otherwise.
    """

    input_path: Path
    output_path: Path
    regions: list[TextRegion] = field(default_factory=list)
    duration_seconds: float = 0.0
    success: bool = True
    error: str | None = None
    already_searchable: bool = False
