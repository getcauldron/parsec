"""Tests for PDF input handling and preprocessing flags in the OCR pipeline.

Covers:
- Non-searchable PDF → searchable PDF
- Preprocessing flags reach ocrmypdf.ocr() kwargs
- Already-searchable PDF with skip_text returns success
- Encrypted PDF returns clear error
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from pdfminer.high_level import extract_text

from parsec.models import OcrOptions
from parsec.pipeline import process_file

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class TestPdfInput:
    """Tests for PDF file processing through the pipeline."""

    def test_nonsearchable_pdf_produces_searchable_pdf(self, tmp_path: Path) -> None:
        """Non-searchable (image-only) PDF → searchable PDF with extractable text."""
        input_pdf = FIXTURES_DIR / "pdf_nosearch_01.pdf"
        assert input_pdf.exists(), f"Fixture missing: {input_pdf}"

        output_pdf = tmp_path / "output.pdf"
        result = process_file(input_pdf, output_pdf)

        assert result.success, f"Pipeline failed: {result.error}"
        assert result.duration_seconds > 0
        assert output_pdf.exists(), "Output PDF was not created"

        # The source is clean_01.png text — verify some words are extractable
        extracted = extract_text(str(output_pdf)).strip().lower()
        assert "quick" in extracted, f"Expected 'quick' in extracted text: {extracted!r}"
        assert "brown" in extracted, f"Expected 'brown' in extracted text: {extracted!r}"
        assert "fox" in extracted, f"Expected 'fox' in extracted text: {extracted!r}"

    def test_pdf_with_deskew(self, tmp_path: Path) -> None:
        """Skewed PDF processed with deskew=True produces a result."""
        input_pdf = FIXTURES_DIR / "pdf_skewed_01.pdf"
        assert input_pdf.exists(), f"Fixture missing: {input_pdf}"

        output_pdf = tmp_path / "output.pdf"
        options = OcrOptions(deskew=True, force_ocr=True)
        result = process_file(input_pdf, output_pdf, options=options)

        assert result.success, f"Pipeline failed: {result.error}"
        assert output_pdf.exists(), "Output PDF was not created"

    def test_preprocessing_flags_reach_ocrmypdf(self, tmp_path: Path) -> None:
        """Verify preprocessing kwargs are actually passed to ocrmypdf.ocr()."""
        input_pdf = FIXTURES_DIR / "pdf_nosearch_01.pdf"
        output_pdf = tmp_path / "output.pdf"

        options = OcrOptions(
            deskew=True,
            rotate_pages=True,
            force_ocr=True,
        )

        with patch("parsec.pipeline.ocrmypdf.ocr") as mock_ocr:
            from ocrmypdf import ExitCode
            mock_ocr.return_value = ExitCode.ok

            process_file(input_pdf, output_pdf, options=options)

            mock_ocr.assert_called_once()
            call_kwargs = mock_ocr.call_args
            # Check preprocessing kwargs were forwarded
            assert call_kwargs.kwargs.get("deskew") is True or \
                   (len(call_kwargs) > 1 and call_kwargs[1].get("deskew") is True), \
                   f"deskew not in call kwargs: {call_kwargs}"

            # Access via the actual call — ocrmypdf.ocr uses keyword args
            _, kwargs = call_kwargs
            assert kwargs.get("deskew") is True
            assert kwargs.get("rotate_pages") is True
            assert kwargs.get("force_ocr") is True

    def test_clean_passes_clean_final(self, tmp_path: Path) -> None:
        """clean=True should also set clean_final=True in ocrmypdf.ocr()."""
        input_pdf = FIXTURES_DIR / "pdf_nosearch_01.pdf"
        output_pdf = tmp_path / "output.pdf"

        options = OcrOptions(clean=True, force_ocr=True)

        with patch("parsec.pipeline.ocrmypdf.ocr") as mock_ocr:
            from ocrmypdf import ExitCode
            mock_ocr.return_value = ExitCode.ok

            process_file(input_pdf, output_pdf, options=options)

            _, kwargs = mock_ocr.call_args
            assert kwargs.get("clean") is True
            assert kwargs.get("clean_final") is True

    def test_skip_text_only_for_pdf(self, tmp_path: Path) -> None:
        """skip_text flag should only be passed for PDF inputs, not images."""
        input_img = FIXTURES_DIR / "clean_01.png"
        output_pdf = tmp_path / "output.pdf"

        options = OcrOptions(skip_text=True)

        with patch("parsec.pipeline.ocrmypdf.ocr") as mock_ocr:
            from ocrmypdf import ExitCode
            mock_ocr.return_value = ExitCode.ok

            process_file(input_img, output_pdf, options=options)

            _, kwargs = mock_ocr.call_args
            # skip_text should NOT be passed for a .png input
            assert "skip_text" not in kwargs, \
                f"skip_text should not be passed for PNG input, got: {kwargs}"

    def test_already_searchable_pdf_returns_success(self, tmp_path: Path) -> None:
        """A PDF that already has text returns success with already_searchable=True."""
        input_pdf = FIXTURES_DIR / "pdf_nosearch_01.pdf"
        output_pdf = tmp_path / "output.pdf"

        with patch("parsec.pipeline.ocrmypdf.ocr") as mock_ocr:
            from ocrmypdf import ExitCode
            mock_ocr.return_value = ExitCode.already_done_ocr

            result = process_file(input_pdf, output_pdf)

            assert result.success is True, f"Expected success, got error: {result.error}"
            assert result.already_searchable is True

    def test_encrypted_pdf_returns_clear_error(self, tmp_path: Path) -> None:
        """An encrypted PDF returns a clear error message."""
        input_pdf = FIXTURES_DIR / "pdf_nosearch_01.pdf"
        output_pdf = tmp_path / "output.pdf"

        with patch("parsec.pipeline.ocrmypdf.ocr") as mock_ocr:
            from ocrmypdf import ExitCode
            mock_ocr.return_value = ExitCode.encrypted_pdf

            result = process_file(input_pdf, output_pdf)

            assert result.success is False
            assert result.error is not None
            assert "encrypted" in result.error.lower() or "password" in result.error.lower(), \
                f"Expected 'encrypted' or 'password' in error: {result.error!r}"

    def test_force_ocr_and_skip_text_mutual_exclusion(self, tmp_path: Path) -> None:
        """force_ocr takes precedence over skip_text (they're mutually exclusive)."""
        input_pdf = FIXTURES_DIR / "pdf_nosearch_01.pdf"
        output_pdf = tmp_path / "output.pdf"

        options = OcrOptions(force_ocr=True, skip_text=True)

        with patch("parsec.pipeline.ocrmypdf.ocr") as mock_ocr:
            from ocrmypdf import ExitCode
            mock_ocr.return_value = ExitCode.ok

            process_file(input_pdf, output_pdf, options=options)

            _, kwargs = mock_ocr.call_args
            assert kwargs.get("force_ocr") is True
            assert "skip_text" not in kwargs, \
                "skip_text should not be set when force_ocr is True"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
