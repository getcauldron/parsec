"""OCR pipeline orchestrating OCRmyPDF + PaddleOCR plugin.

Takes image files (PNG, JPEG, TIFF) and produces searchable PDFs with
invisible text layers. This is the core product capability (R002).
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import ocrmypdf
from ocrmypdf import ExitCode

from parsec.models import OcrOptions, ProcessResult

logger = logging.getLogger(__name__)

# The plugin module path for ocrmypdf-paddleocr
_PADDLEOCR_PLUGIN = "ocrmypdf_paddleocr"

# Map our short language codes to Tesseract's ISO 639-2 codes.
# OCRmyPDF validates languages against the engine's supported set,
# and the PaddleOCR plugin uses Tesseract-style codes internally.
_LANG_TO_TESSERACT: dict[str, str] = {
    "en": "eng",
    "ch": "chi_sim",
    "fr": "fra",
    "de": "deu",
    "es": "spa",
    "pt": "por",
    "it": "ita",
    "ru": "rus",
    "ja": "jpn",
    "ko": "kor",
    "ar": "ara",
    "hi": "hin",
}


def _to_tesseract_lang(lang: str) -> str:
    """Convert a short language code to Tesseract's ISO 639-2 code."""
    return _LANG_TO_TESSERACT.get(lang, lang)


def process_file(
    input_path: Path,
    output_path: Path,
    *,
    options: OcrOptions | None = None,
) -> ProcessResult:
    """Process an image file through OCRmyPDF with PaddleOCR, producing a searchable PDF.

    Args:
        input_path: Path to input image (PNG, JPEG, TIFF) or PDF.
        output_path: Path where the searchable PDF will be written.
        options: OCR options (language, DPI). Defaults to OcrOptions() if not provided.

    Returns:
        ProcessResult with timing, success/error status, and file paths.

    The output PDF contains the original image with an invisible text layer
    overlay, making the text selectable and searchable.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    options = options or OcrOptions()

    logger.info("Processing %s -> %s", input_path, output_path)

    if not input_path.exists():
        return ProcessResult(
            input_path=input_path,
            output_path=output_path,
            success=False,
            error=f"Input file not found: {input_path}",
        )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    start = time.monotonic()

    try:
        tess_lang = _to_tesseract_lang(options.language)
        exit_code = ocrmypdf.ocr(
            input_file_or_options=input_path,
            output_file=output_path,
            language=[tess_lang],
            image_dpi=options.dpi,
            output_type="pdf",  # Skip PDF/A to avoid Ghostscript dependency
            plugins=[_PADDLEOCR_PLUGIN],
            jobs=1,  # PaddlePaddle is not multi-process safe
            progress_bar=False,
        )
    except Exception as exc:
        elapsed = time.monotonic() - start
        error_msg = f"{type(exc).__name__}: {exc}"
        logger.error("Pipeline failed for %s after %.2fs: %s", input_path, elapsed, error_msg)
        return ProcessResult(
            input_path=input_path,
            output_path=output_path,
            duration_seconds=elapsed,
            success=False,
            error=error_msg,
        )

    elapsed = time.monotonic() - start

    if exit_code != ExitCode.ok:
        error_msg = f"OCRmyPDF exited with {exit_code.name} ({exit_code.value})"
        logger.error("Pipeline failed for %s after %.2fs: %s", input_path, elapsed, error_msg)
        return ProcessResult(
            input_path=input_path,
            output_path=output_path,
            duration_seconds=elapsed,
            success=False,
            error=error_msg,
        )

    logger.info("Pipeline completed for %s in %.2fs", input_path.name, elapsed)

    return ProcessResult(
        input_path=input_path,
        output_path=output_path,
        duration_seconds=elapsed,
        success=True,
    )
