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

from parsec.languages import get_tesseract_code
from parsec.models import OcrOptions, ProcessResult

logger = logging.getLogger(__name__)

# The plugin module path for ocrmypdf-paddleocr
_PADDLEOCR_PLUGIN = "ocrmypdf_paddleocr"


def _to_tesseract_lang(lang: str) -> str:
    """Convert a PaddleOCR short code to Tesseract's ISO 639-2 code.

    Delegates to the authoritative language registry in languages.py.
    """
    return get_tesseract_code(lang)


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

    is_pdf = input_path.suffix.lower() == ".pdf"

    # Build preprocessing kwargs from options
    ocr_kwargs: dict = {}
    if options.deskew:
        ocr_kwargs["deskew"] = True
    if options.rotate_pages:
        ocr_kwargs["rotate_pages"] = True
    if options.clean:
        ocr_kwargs["clean"] = True
        ocr_kwargs["clean_final"] = True

    # skip_text and force_ocr are mutually exclusive; skip_text only for PDFs
    if options.force_ocr:
        ocr_kwargs["force_ocr"] = True
    elif options.skip_text and is_pdf:
        ocr_kwargs["skip_text"] = True

    preprocess_mode = "force_ocr" if options.force_ocr else (
        "skip_text" if (options.skip_text and is_pdf) else "default"
    )
    logger.info(
        "Preprocessing mode=%s deskew=%s rotate=%s clean=%s for %s",
        preprocess_mode, options.deskew, options.rotate_pages, options.clean,
        input_path.name,
    )

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
            **ocr_kwargs,
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

    # Handle special exit codes
    if exit_code == ExitCode.already_done_ocr:
        logger.info(
            "PDF already searchable for %s (%.2fs) — no OCR needed",
            input_path.name, elapsed,
        )
        return ProcessResult(
            input_path=input_path,
            output_path=output_path,
            duration_seconds=elapsed,
            success=True,
            already_searchable=True,
        )

    if exit_code == ExitCode.encrypted_pdf:
        error_msg = "Encrypted or password-protected PDF — cannot process"
        logger.error("Pipeline failed for %s: %s", input_path.name, error_msg)
        return ProcessResult(
            input_path=input_path,
            output_path=output_path,
            duration_seconds=elapsed,
            success=False,
            error=error_msg,
        )

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
