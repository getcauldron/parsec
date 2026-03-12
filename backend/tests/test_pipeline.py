"""Integration tests for the OCR pipeline.

Generates test images with known text using Pillow, runs them through
process_file(), and verifies the output PDFs contain extractable text.

Note: The ``if __name__ == '__main__'`` guard is required on macOS because
OCRmyPDF uses multiprocessing internally.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont
from pdfminer.high_level import extract_text

from parsec.models import OcrOptions, ProcessResult
from parsec.pipeline import process_file


def _get_font(size: int = 48) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Get a font for test image generation, with fallbacks."""
    for font_path in (
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(font_path, size=size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _create_test_image(
    text: str,
    path: Path,
    *,
    width: int = 800,
    height: int = 400,
    fmt: str = "PNG",
) -> Path:
    """Generate a test image with black text on white background.

    Args:
        text: Text to render. Supports newlines for multi-line content.
        path: Output image path.
        width: Image width in pixels.
        height: Image height in pixels.
        fmt: Image format — 'PNG' or 'JPEG'.
    """
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    font = _get_font(size=36)

    y_offset = 40
    for line in text.split("\n"):
        draw.text((50, y_offset), line, fill="black", font=font)
        y_offset += 50

    img.save(path, format=fmt)
    return path


class TestProcessFile:
    """Tests for process_file() pipeline integration."""

    def test_png_produces_searchable_pdf(self, tmp_path: Path) -> None:
        """Core test: PNG input → searchable PDF with extractable text."""
        input_img = _create_test_image(
            "The quick brown fox\njumps over the lazy dog",
            tmp_path / "input.png",
        )
        output_pdf = tmp_path / "output.pdf"

        result = process_file(input_img, output_pdf)

        assert result.success, f"Pipeline failed: {result.error}"
        assert result.duration_seconds > 0
        assert output_pdf.exists(), "Output PDF was not created"

        # Extract text from the PDF and verify it matches
        extracted = extract_text(str(output_pdf)).strip().lower()
        assert "quick" in extracted, f"Expected 'quick' in extracted text: {extracted!r}"
        assert "brown" in extracted, f"Expected 'brown' in extracted text: {extracted!r}"
        assert "fox" in extracted, f"Expected 'fox' in extracted text: {extracted!r}"
        assert "lazy" in extracted, f"Expected 'lazy' in extracted text: {extracted!r}"
        assert "dog" in extracted, f"Expected 'dog' in extracted text: {extracted!r}"

    def test_jpeg_produces_searchable_pdf(self, tmp_path: Path) -> None:
        """JPEG input also produces a searchable PDF."""
        input_img = _create_test_image(
            "Hello World",
            tmp_path / "input.jpg",
            fmt="JPEG",
        )
        output_pdf = tmp_path / "output.pdf"

        result = process_file(input_img, output_pdf)

        assert result.success, f"Pipeline failed: {result.error}"
        assert output_pdf.exists()

        extracted = extract_text(str(output_pdf)).strip().lower()
        assert "hello" in extracted, f"Expected 'hello' in extracted text: {extracted!r}"
        assert "world" in extracted, f"Expected 'world' in extracted text: {extracted!r}"

    def test_result_populated_correctly(self, tmp_path: Path) -> None:
        """Verify ProcessResult fields are populated."""
        input_img = _create_test_image("Result Test", tmp_path / "input.png")
        output_pdf = tmp_path / "output.pdf"

        result = process_file(input_img, output_pdf)

        assert isinstance(result, ProcessResult)
        assert result.input_path == input_img
        assert result.output_path == output_pdf
        assert result.success is True
        assert result.error is None
        assert result.duration_seconds > 0

    def test_missing_input_returns_error(self, tmp_path: Path) -> None:
        """Missing input file produces a failed ProcessResult, not an exception."""
        result = process_file(
            tmp_path / "nonexistent.png",
            tmp_path / "output.pdf",
        )

        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower()

    def test_custom_options(self, tmp_path: Path) -> None:
        """process_file works with explicit OcrOptions."""
        input_img = _create_test_image("Options Test", tmp_path / "input.png")
        output_pdf = tmp_path / "output.pdf"

        result = process_file(
            input_img,
            output_pdf,
            options=OcrOptions(language="en", dpi=300),
        )

        assert result.success, f"Pipeline failed: {result.error}"
        assert output_pdf.exists()

    def test_output_directory_created(self, tmp_path: Path) -> None:
        """Output parent directories are created automatically."""
        input_img = _create_test_image("Dir Test", tmp_path / "input.png")
        output_pdf = tmp_path / "subdir" / "nested" / "output.pdf"

        result = process_file(input_img, output_pdf)

        assert result.success, f"Pipeline failed: {result.error}"
        assert output_pdf.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
