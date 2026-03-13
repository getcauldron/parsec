"""Cross-cutting integration tests for the Parsec OCR pipeline.

Exercises the full pipeline through the sidecar subprocess with mixed file types,
error resilience, TIFF support, PDF quality benchmarks, and preprocessing quality
comparisons. Complements the module-level tests in test_sidecar.py, test_pipeline.py,
test_quality.py, etc.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import jiwer
import pytest
from pdfminer.high_level import extract_text

from parsec.models import OcrOptions
from parsec.pipeline import process_file
from tests.conftest import FIXTURE_DIR, load_ground_truth
from tests.test_quality import (
    QualityResult,
    _CER_TRANSFORMS,
    _WER_TRANSFORMS,
    measure_quality,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
SIDECAR_MODULE = "parsec.sidecar"


# ─── Helpers ──────────────────────────────────────────────────────────


def _run_sidecar(input_lines: list[str], timeout: float = 10.0) -> list[dict]:
    """Send NDJSON lines to the sidecar process and collect responses.

    Duplicated from test_sidecar.py to keep test_integration.py self-contained
    and avoid cross-test-module imports.
    """
    stdin_data = "\n".join(input_lines) + "\n"

    result = subprocess.run(
        [sys.executable, "-m", SIDECAR_MODULE],
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(BACKEND_DIR),
    )

    responses = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line:
            responses.append(json.loads(line))

    return responses


def _filter_progress(responses: list[dict], file_id: str) -> list[dict]:
    """Filter progress events for a specific file id."""
    return [r for r in responses if r.get("type") == "progress" and r.get("id") == file_id]


def _measure_cer_from_pdf(
    pdf_path: Path,
    ground_truth: str,
) -> float:
    """Extract text from a PDF and compute CER against ground truth."""
    extracted = extract_text(str(pdf_path)).strip()
    if not extracted:
        return 1.0
    gt_normalized = ground_truth.replace("\n", " ")
    return jiwer.cer(
        gt_normalized,
        extracted,
        reference_transform=_CER_TRANSFORMS,
        hypothesis_transform=_CER_TRANSFORMS,
    )


# ─── Multi-file batch sidecar test ───────────────────────────────────


class TestMultiFileBatch:
    """Send multiple mixed file types through a single sidecar session."""

    def test_batch_mixed_file_types(self, tmp_path: Path):
        """PNG, JPEG, non-searchable PDF, and skewed PDF all reach 'complete' stage."""
        # Prepare files — copy fixtures to tmp_path
        files = {
            "batch-png": ("clean_01.png", FIXTURE_DIR / "clean_01.png"),
            "batch-jpg": ("clean_01.jpg", FIXTURE_DIR / "clean_01.jpg"),
            "batch-pdf": ("document.pdf", FIXTURE_DIR / "pdf_nosearch_01.pdf"),
            "batch-skew": ("skewed.pdf", FIXTURE_DIR / "pdf_skewed_01.pdf"),
        }

        commands = []
        for file_id, (dest_name, src) in files.items():
            dest = tmp_path / dest_name
            shutil.copy2(src, dest)
            commands.append(json.dumps({
                "cmd": "process_file",
                "id": file_id,
                "input_path": str(dest),
            }))

        responses = _run_sidecar(commands, timeout=180.0)

        # Each file must reach 'complete' stage
        for file_id in files:
            progress = _filter_progress(responses, file_id)
            stages = [r.get("stage") for r in progress]
            assert "complete" in stages, (
                f"File {file_id} did not reach 'complete'. "
                f"Stages: {stages}"
            )

            # Verify output PDF exists
            complete_event = next(r for r in progress if r.get("stage") == "complete")
            assert "output_path" in complete_event
            output_pdf = Path(complete_event["output_path"])
            assert output_pdf.exists(), f"Output PDF missing for {file_id}: {output_pdf}"
            assert output_pdf.stat().st_size > 0

    def test_batch_all_have_duration(self, tmp_path: Path):
        """Each completed file reports a positive duration."""
        files = {
            "dur-png": ("test.png", FIXTURE_DIR / "clean_01.png"),
            "dur-pdf": ("test.pdf", FIXTURE_DIR / "pdf_nosearch_01.pdf"),
        }

        commands = []
        for file_id, (dest_name, src) in files.items():
            dest = tmp_path / dest_name
            shutil.copy2(src, dest)
            commands.append(json.dumps({
                "cmd": "process_file",
                "id": file_id,
                "input_path": str(dest),
            }))

        responses = _run_sidecar(commands, timeout=120.0)

        for file_id in files:
            progress = _filter_progress(responses, file_id)
            complete = [r for r in progress if r.get("stage") == "complete"]
            assert len(complete) == 1, f"Expected 1 complete event for {file_id}"
            assert complete[0]["duration"] > 0


# ─── Error resilience ────────────────────────────────────────────────


class TestErrorResilience:
    """Bad files in a batch don't crash processing of valid files."""

    def test_bad_file_gets_error_valid_files_complete(self, tmp_path: Path):
        """An unsupported extension file gets 'error' while valid files reach 'complete'."""
        # Valid file
        valid_src = FIXTURE_DIR / "clean_01.png"
        valid_dest = tmp_path / "valid.png"
        shutil.copy2(valid_src, valid_dest)

        # Bad file — unsupported extension
        bad_file = tmp_path / "trouble.xyz"
        bad_file.write_text("not an image")

        commands = [
            json.dumps({
                "cmd": "process_file",
                "id": "valid-1",
                "input_path": str(valid_dest),
            }),
            json.dumps({
                "cmd": "process_file",
                "id": "bad-1",
                "input_path": str(bad_file),
            }),
        ]

        responses = _run_sidecar(commands, timeout=120.0)

        # Bad file should get error stage
        bad_progress = _filter_progress(responses, "bad-1")
        bad_stages = [r.get("stage") for r in bad_progress]
        assert "error" in bad_stages, f"Bad file should get 'error', got: {bad_stages}"

        # Valid file should still complete
        valid_progress = _filter_progress(responses, "valid-1")
        valid_stages = [r.get("stage") for r in valid_progress]
        assert "complete" in valid_stages, (
            f"Valid file should reach 'complete' despite bad file in batch. "
            f"Stages: {valid_stages}"
        )

    def test_nonexistent_file_gets_error_valid_files_complete(self, tmp_path: Path):
        """A nonexistent file path gets 'error' while valid files reach 'complete'."""
        valid_src = FIXTURE_DIR / "clean_01.png"
        valid_dest = tmp_path / "real.png"
        shutil.copy2(valid_src, valid_dest)

        commands = [
            json.dumps({
                "cmd": "process_file",
                "id": "ghost-1",
                "input_path": "/nonexistent/phantom.png",
            }),
            json.dumps({
                "cmd": "process_file",
                "id": "real-1",
                "input_path": str(valid_dest),
            }),
        ]

        responses = _run_sidecar(commands, timeout=120.0)

        # Nonexistent file → error
        ghost_progress = _filter_progress(responses, "ghost-1")
        ghost_stages = [r.get("stage") for r in ghost_progress]
        assert "error" in ghost_stages

        # Real file → complete
        real_progress = _filter_progress(responses, "real-1")
        real_stages = [r.get("stage") for r in real_progress]
        assert "complete" in real_stages


# ─── PDF quality benchmarks ──────────────────────────────────────────


class TestPdfQualityBenchmarks:
    """CER/WER benchmarks for PDF fixtures using the OCR engine directly."""

    def test_pdf_nosearch_cer(self, engine):
        """CER on pdf_nosearch_01 is below threshold (< 0.10)."""
        result = measure_quality(
            FIXTURE_DIR / "pdf_nosearch_01.pdf",
            FIXTURE_DIR / "pdf_nosearch_01.gt.txt",
            engine,
        )
        print(
            f"\n  pdf_nosearch_01: CER={result.cer:.4f} (max 0.10), "
            f"WER={result.wer:.4f}"
        )
        assert result.cer < 0.10, (
            f"pdf_nosearch_01 CER {result.cer:.4f} >= 0.10\n"
            f"  Ground truth: {result.ground_truth[:100]}...\n"
            f"  Recognized:   {result.recognized_text[:100]}..."
        )

    def test_pdf_nosearch_wer(self, engine):
        """WER on pdf_nosearch_01 is below threshold (< 0.15)."""
        result = measure_quality(
            FIXTURE_DIR / "pdf_nosearch_01.pdf",
            FIXTURE_DIR / "pdf_nosearch_01.gt.txt",
            engine,
        )
        print(
            f"\n  pdf_nosearch_01: CER={result.cer:.4f}, "
            f"WER={result.wer:.4f} (max 0.15)"
        )
        assert result.wer < 0.15

    def test_pdf_skewed_cer(self, engine):
        """CER on pdf_skewed_01 is below threshold (< 0.20)."""
        result = measure_quality(
            FIXTURE_DIR / "pdf_skewed_01.pdf",
            FIXTURE_DIR / "pdf_skewed_01.gt.txt",
            engine,
        )
        print(
            f"\n  pdf_skewed_01: CER={result.cer:.4f} (max 0.20), "
            f"WER={result.wer:.4f}"
        )
        assert result.cer < 0.20, (
            f"pdf_skewed_01 CER {result.cer:.4f} >= 0.20\n"
            f"  Ground truth: {result.ground_truth[:100]}...\n"
            f"  Recognized:   {result.recognized_text[:100]}..."
        )

    def test_pdf_skewed_wer(self, engine):
        """WER on pdf_skewed_01 is below threshold (< 0.30)."""
        result = measure_quality(
            FIXTURE_DIR / "pdf_skewed_01.pdf",
            FIXTURE_DIR / "pdf_skewed_01.gt.txt",
            engine,
        )
        print(
            f"\n  pdf_skewed_01: CER={result.cer:.4f}, "
            f"WER={result.wer:.4f} (max 0.30)"
        )
        assert result.wer < 0.30


# ─── Preprocessing quality comparison ────────────────────────────────


class TestPreprocessingQuality:
    """Deskew preprocessing should not degrade quality on skewed input."""

    def test_deskew_does_not_degrade_skewed_pdf(self, tmp_path: Path):
        """Processing skewed PDF with deskew=True produces CER ≤ CER without + epsilon.

        The skew is only 3°, so the improvement may be marginal. We assert
        that deskew at least doesn't make things worse (within epsilon for
        non-determinism).
        """
        src = FIXTURE_DIR / "pdf_skewed_01.pdf"
        ground_truth = load_ground_truth(FIXTURE_DIR / "pdf_skewed_01.pdf")

        # Process without deskew
        no_deskew_in = tmp_path / "no_deskew.pdf"
        no_deskew_out = tmp_path / "no_deskew_ocr.pdf"
        shutil.copy2(src, no_deskew_in)
        r1 = process_file(no_deskew_in, no_deskew_out, options=OcrOptions())
        assert r1.success, f"No-deskew processing failed: {r1.error}"

        # Process with deskew
        deskew_in = tmp_path / "with_deskew.pdf"
        deskew_out = tmp_path / "with_deskew_ocr.pdf"
        shutil.copy2(src, deskew_in)
        r2 = process_file(deskew_in, deskew_out, options=OcrOptions(deskew=True))
        assert r2.success, f"Deskew processing failed: {r2.error}"

        # Measure CER from the output PDFs' text layers
        cer_no_deskew = _measure_cer_from_pdf(no_deskew_out, ground_truth)
        cer_deskew = _measure_cer_from_pdf(deskew_out, ground_truth)

        print(
            f"\n  Preprocessing comparison (pdf_skewed_01):\n"
            f"    CER without deskew: {cer_no_deskew:.4f}\n"
            f"    CER with deskew:    {cer_deskew:.4f}\n"
            f"    Delta:              {cer_deskew - cer_no_deskew:+.4f}"
        )

        # Deskew should not make CER significantly worse
        # Allow epsilon=0.02 for non-determinism in OCR and preprocessing
        epsilon = 0.02
        assert cer_deskew <= cer_no_deskew + epsilon, (
            f"Deskew degraded quality: CER {cer_deskew:.4f} > "
            f"{cer_no_deskew:.4f} + {epsilon} (no-deskew + epsilon)"
        )


# ─── TIFF pipeline tests ─────────────────────────────────────────────


class TestTiffPipeline:
    """TIFF input support through both pipeline and sidecar."""

    def test_tiff_pipeline_produces_pdf(self, tmp_path: Path):
        """process_file() accepts TIFF input and produces a searchable PDF."""
        src = FIXTURE_DIR / "tiff_01.tiff"
        input_file = tmp_path / "scan.tiff"
        output_file = tmp_path / "scan_ocr.pdf"
        shutil.copy2(src, input_file)

        result = process_file(input_file, output_file)

        assert result.success, f"TIFF processing failed: {result.error}"
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Verify the output has a text layer
        extracted = extract_text(str(output_file)).strip()
        assert len(extracted) > 0, "TIFF→PDF output has no text layer"

    def test_tiff_pipeline_quality(self, tmp_path: Path):
        """TIFF fixture produces output PDF with CER below clean threshold.

        PaddleOCR doesn't recognize TIFF directly, so we verify quality
        through the full pipeline (TIFF→OCRmyPDF→searchable PDF) by
        extracting text from the output PDF.
        """
        src = FIXTURE_DIR / "tiff_01.tiff"
        input_file = tmp_path / "quality_test.tiff"
        output_file = tmp_path / "quality_test_ocr.pdf"
        shutil.copy2(src, input_file)

        result = process_file(input_file, output_file)
        assert result.success, f"TIFF processing failed: {result.error}"

        ground_truth = load_ground_truth(FIXTURE_DIR / "tiff_01.tiff")
        cer = _measure_cer_from_pdf(output_file, ground_truth)

        print(
            f"\n  tiff_01 (pipeline): CER={cer:.4f} (max 0.05)"
        )
        # Same content as clean_01 — should meet clean threshold
        assert cer < 0.05, (
            f"tiff_01 pipeline CER {cer:.4f} >= 0.05"
        )

    def test_tiff_sidecar_extension_accepted(self, tmp_path: Path):
        """Sidecar accepts .tiff files without 'Unsupported file extension' error."""
        src = FIXTURE_DIR / "tiff_01.tiff"
        input_file = tmp_path / "scan.tiff"
        shutil.copy2(src, input_file)

        cmd = json.dumps({
            "cmd": "process_file",
            "id": "tiff-1",
            "input_path": str(input_file),
        })

        responses = _run_sidecar([cmd], timeout=120.0)
        progress = _filter_progress(responses, "tiff-1")
        stages = [r.get("stage") for r in progress]

        # Should NOT get unsupported extension error
        for r in progress:
            if r.get("stage") == "error":
                assert "Unsupported file extension" not in r.get("error", ""), \
                    f"TIFF should be accepted, got: {r['error']}"

        assert "complete" in stages, (
            f"TIFF file should reach 'complete'. Stages: {stages}"
        )

        # Verify output exists
        complete_event = next(r for r in progress if r.get("stage") == "complete")
        output_pdf = Path(complete_event["output_path"])
        assert output_pdf.exists()
