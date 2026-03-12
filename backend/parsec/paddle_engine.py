"""PaddleOCR engine implementation using PP-OCRv5 (R005).

Lazy-initializes PaddleOCR on first recognize() call to avoid cold-start
penalty until inference is actually needed (~4s model load).
"""

from __future__ import annotations

import contextlib
import io
import logging
import os
import time
from pathlib import Path

from parsec.engine import OcrEngine
from parsec.models import OcrOptions, TextRegion

logger = logging.getLogger(__name__)


class PaddleOcrEngine(OcrEngine):
    """OCR engine backed by PaddleOCR PP-OCRv5.

    Uses the predict() API (PaddleOCR 3.x) with word-level bounding boxes.
    Models are auto-downloaded on first init (~15MB to ~/.paddleocr/).
    """

    def __init__(self) -> None:
        self._ocr = None
        self._version_str: str | None = None

    def _ensure_initialized(self, language: str = "en") -> None:
        """Lazy-initialize PaddleOCR, suppressing its noisy stdout."""
        if self._ocr is not None:
            return

        start = time.monotonic()

        # PaddleOCR dumps a lot to stdout/stderr during init — suppress it
        with (
            open(os.devnull, "w") as devnull,
            contextlib.redirect_stdout(devnull),
            contextlib.redirect_stderr(devnull),
        ):
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )

        elapsed = time.monotonic() - start
        logger.info("PaddleOCR initialized in %.1fs", elapsed)

        # Capture version after import
        try:
            import paddleocr

            self._version_str = getattr(paddleocr, "__version__", "unknown")
        except Exception:
            self._version_str = "unknown"

    def recognize(self, image_path: Path, options: OcrOptions | None = None) -> list[TextRegion]:
        """Run OCR on an image and return recognized text regions.

        Args:
            image_path: Path to the input image.
            options: OCR options. Defaults to OcrOptions() if not provided.

        Returns:
            List of TextRegion with text, bounding box, and confidence.

        Raises:
            FileNotFoundError: If image_path doesn't exist.
            RuntimeError: If PaddleOCR fails to process the image.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        options = options or OcrOptions()
        self._ensure_initialized(language=options.language)

        start = time.monotonic()

        try:
            # Suppress PaddleOCR's predict() stdout noise
            with (
                open(os.devnull, "w") as devnull,
                contextlib.redirect_stdout(devnull),
                contextlib.redirect_stderr(devnull),
            ):
                results = self._ocr.predict(
                    input=str(image_path),
                    return_word_box=True,
                )
        except Exception as e:
            raise RuntimeError(
                f"PaddleOCR failed to process {image_path}: {e}"
            ) from e

        elapsed = time.monotonic() - start
        logger.info("OCR completed on %s in %.2fs", image_path.name, elapsed)

        return self._parse_results(results)

    def _parse_results(self, results) -> list[TextRegion]:
        """Convert PaddleOCR predict() output to TextRegion list.

        The predict() API returns an iterable of result objects. Each result
        has rec_texts, rec_scores, and dt_polys (polygon coordinates).
        """
        regions: list[TextRegion] = []

        if results is None:
            return regions

        for result in results:
            # Result object attributes from PaddleOCR 3.x predict() API
            rec_texts = getattr(result, "rec_texts", None)
            rec_scores = getattr(result, "rec_scores", None)
            dt_polys = getattr(result, "dt_polys", None)

            if rec_texts is None:
                # Try dict-style access (some versions return dicts)
                if isinstance(result, dict):
                    rec_texts = result.get("rec_texts", [])
                    rec_scores = result.get("rec_scores", [])
                    dt_polys = result.get("dt_polys", [])
                else:
                    continue

            for i, text in enumerate(rec_texts):
                if not text or not text.strip():
                    continue

                score = float(rec_scores[i]) if rec_scores is not None and i < len(rec_scores) else 0.0

                # Convert polygon to axis-aligned bounding box (x1, y1, x2, y2)
                bbox = self._poly_to_bbox(dt_polys[i]) if dt_polys is not None and i < len(dt_polys) else (0.0, 0.0, 0.0, 0.0)

                regions.append(TextRegion(text=text, bbox=bbox, confidence=score))

        return regions

    @staticmethod
    def _poly_to_bbox(polygon) -> tuple[float, float, float, float]:
        """Convert a polygon (list of [x, y] points) to an axis-aligned bbox.

        Returns (x1, y1, x2, y2) — top-left and bottom-right corners.
        """
        try:
            xs = [float(p[0]) for p in polygon]
            ys = [float(p[1]) for p in polygon]
            return (min(xs), min(ys), max(xs), max(ys))
        except (TypeError, IndexError, ValueError):
            return (0.0, 0.0, 0.0, 0.0)

    def name(self) -> str:
        return "PaddleOCR"

    def version(self) -> str:
        if self._version_str is None:
            try:
                import paddleocr

                self._version_str = getattr(paddleocr, "__version__", "unknown")
            except ImportError:
                return "not installed"
        return self._version_str
