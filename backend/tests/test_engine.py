"""Integration tests for PaddleOcrEngine.

Generates a test image with known text using Pillow, runs OCR,
and verifies the engine returns meaningful results.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from parsec.models import OcrOptions, TextRegion
from parsec.paddle_engine import PaddleOcrEngine


def _create_test_image(text: str, path: Path, width: int = 800, height: int = 200) -> Path:
    """Generate a simple test image with black text on white background."""
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Use a large font size for reliable OCR detection
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=48)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=48)
        except (OSError, IOError):
            # Fall back to default font — scaled up via image size
            font = ImageFont.load_default()

    draw.text((50, 60), text, fill="black", font=font)
    img.save(path)
    return path


@pytest.fixture(scope="module")
def engine() -> PaddleOcrEngine:
    """Shared engine instance — avoids repeated cold starts (~4s each)."""
    return PaddleOcrEngine()


class TestPaddleOcrEngine:
    """Tests for PaddleOcrEngine."""

    def test_name(self, engine: PaddleOcrEngine) -> None:
        assert engine.name() == "PaddleOCR"

    def test_version_is_string(self, engine: PaddleOcrEngine) -> None:
        version = engine.version()
        assert isinstance(version, str)
        assert version != ""

    def test_recognize_returns_text_regions(self, engine: PaddleOcrEngine) -> None:
        """Core test: OCR a generated image and verify we get results back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = _create_test_image("Hello World", Path(tmpdir) / "hello.png")
            regions = engine.recognize(img_path)

            assert isinstance(regions, list)
            assert len(regions) > 0, "Expected at least one TextRegion from 'Hello World' image"

            for region in regions:
                assert isinstance(region, TextRegion)
                assert region.confidence > 0, f"Expected confidence > 0, got {region.confidence}"
                assert region.text.strip(), "Expected non-empty text"

    def test_recognized_text_matches_input(self, engine: PaddleOcrEngine) -> None:
        """Verify recognized text contains the expected words."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = _create_test_image("Hello World", Path(tmpdir) / "match.png")
            regions = engine.recognize(img_path)

            all_text = " ".join(r.text for r in regions).lower()
            assert "hello" in all_text, f"Expected 'hello' in recognized text, got: {all_text}"
            assert "world" in all_text, f"Expected 'world' in recognized text, got: {all_text}"

    def test_bounding_boxes_are_valid(self, engine: PaddleOcrEngine) -> None:
        """Verify bounding boxes have positive dimensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = _create_test_image("Test Bboxes", Path(tmpdir) / "bbox.png")
            regions = engine.recognize(img_path)

            assert len(regions) > 0
            for region in regions:
                x1, y1, x2, y2 = region.bbox
                assert x2 > x1, f"Expected x2 > x1, got bbox {region.bbox}"
                assert y2 > y1, f"Expected y2 > y1, got bbox {region.bbox}"

    def test_file_not_found_raises(self, engine: PaddleOcrEngine) -> None:
        """Verify FileNotFoundError for missing images."""
        with pytest.raises(FileNotFoundError):
            engine.recognize(Path("/nonexistent/image.png"))

    def test_options_default(self, engine: PaddleOcrEngine) -> None:
        """Verify recognize works with explicit default options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = _create_test_image("Options Test", Path(tmpdir) / "opts.png")
            options = OcrOptions(language="en", dpi=300)
            regions = engine.recognize(img_path, options=options)
            assert len(regions) > 0
