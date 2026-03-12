"""CER/WER quality benchmarks for OCR pipeline.

Measures Character Error Rate and Word Error Rate against synthetic fixtures
with known ground truth. Tests are parametrized by category with per-category
thresholds:
  - clean:    CER < 0.05, WER < 0.10
  - multicol: CER < 0.08, WER < 0.15
  - degraded: CER < 0.15, WER < 0.25

CER/WER scores are printed in test output for visibility and regression tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import jiwer
import pytest

from parsec.paddle_engine import PaddleOcrEngine
from tests.conftest import FIXTURE_DIR, load_ground_truth

# ─── Text normalization ──────────────────────────────────────────────

# Transforms applied before comparison to handle benign OCR differences:
# - Strip leading/trailing whitespace
# - Lowercase (OCR may capitalize differently)
# - Collapse multiple spaces into one
_WER_TRANSFORMS = jiwer.Compose([
    jiwer.Strip(),
    jiwer.ToLowerCase(),
    jiwer.RemoveMultipleSpaces(),
    jiwer.ReduceToListOfListOfWords(),
])

_CER_TRANSFORMS = jiwer.Compose([
    jiwer.Strip(),
    jiwer.ToLowerCase(),
    jiwer.RemoveMultipleSpaces(),
    jiwer.ReduceToListOfListOfChars(),
])


# ─── Quality measurement ─────────────────────────────────────────────

@dataclass
class QualityResult:
    """CER and WER measurement for a single image."""
    image_name: str
    cer: float
    wer: float
    recognized_text: str
    ground_truth: str


def measure_quality(
    image_path: Path,
    ground_truth_path: Path,
    engine: PaddleOcrEngine,
) -> QualityResult:
    """OCR an image and measure CER/WER against ground truth.

    Args:
        image_path: Path to the fixture image.
        ground_truth_path: Path to the .gt.txt ground truth file.
        engine: Initialized PaddleOCR engine.

    Returns:
        QualityResult with CER, WER, and both text strings.
    """
    ground_truth = load_ground_truth(image_path)
    regions = engine.recognize(image_path)

    # Concatenate all recognized text regions
    recognized = " ".join(r.text for r in regions)

    # Handle empty recognition (would cause division errors)
    if not recognized.strip():
        return QualityResult(
            image_name=image_path.name,
            cer=1.0,
            wer=1.0,
            recognized_text="",
            ground_truth=ground_truth,
        )

    # Normalize newlines in ground truth to spaces for comparison
    # (OCR engines typically don't preserve line breaks)
    gt_normalized = ground_truth.replace("\n", " ")

    cer = jiwer.cer(
        gt_normalized,
        recognized,
        reference_transform=_CER_TRANSFORMS,
        hypothesis_transform=_CER_TRANSFORMS,
    )
    wer = jiwer.wer(
        gt_normalized,
        recognized,
        reference_transform=_WER_TRANSFORMS,
        hypothesis_transform=_WER_TRANSFORMS,
    )

    return QualityResult(
        image_name=image_path.name,
        cer=cer,
        wer=wer,
        recognized_text=recognized,
        ground_truth=ground_truth,
    )


# ─── Fixture discovery ───────────────────────────────────────────────

@dataclass
class FixtureCase:
    """A single test fixture with its category and thresholds."""
    image_path: Path
    gt_path: Path
    category: str
    max_cer: float
    max_wer: float

    @property
    def id(self) -> str:
        return self.image_path.stem


# Category thresholds
_THRESHOLDS = {
    "clean":    {"max_cer": 0.05, "max_wer": 0.10},
    "multicol": {"max_cer": 0.08, "max_wer": 0.15},
    "degraded": {"max_cer": 0.15, "max_wer": 0.25},
}


def _discover_fixtures() -> list[FixtureCase]:
    """Find all fixture images grouped by category prefix."""
    cases: list[FixtureCase] = []
    for category, thresholds in _THRESHOLDS.items():
        pattern = f"{category}_*.png"
        images = sorted(FIXTURE_DIR.glob(pattern))
        for img_path in images:
            gt_path = img_path.with_suffix(".gt.txt")
            if gt_path.exists():
                cases.append(FixtureCase(
                    image_path=img_path,
                    gt_path=gt_path,
                    category=category,
                    max_cer=thresholds["max_cer"],
                    max_wer=thresholds["max_wer"],
                ))
    return cases


_FIXTURES = _discover_fixtures()


# ─── Parametrized tests ──────────────────────────────────────────────

@pytest.mark.parametrize(
    "fixture",
    _FIXTURES,
    ids=[f.id for f in _FIXTURES],
)
class TestOcrQuality:
    """CER/WER quality benchmarks across all fixture categories."""

    def test_cer_threshold(self, fixture: FixtureCase, engine: PaddleOcrEngine) -> None:
        """Assert CER is below the category threshold."""
        result = measure_quality(fixture.image_path, fixture.gt_path, engine)

        # Always print for visibility
        print(
            f"\n  {result.image_name} [{fixture.category}]: "
            f"CER={result.cer:.4f} (max {fixture.max_cer}), "
            f"WER={result.wer:.4f} (max {fixture.max_wer})"
        )

        assert result.cer < fixture.max_cer, (
            f"{result.image_name}: CER {result.cer:.4f} >= threshold {fixture.max_cer}\n"
            f"  Ground truth: {result.ground_truth[:100]}...\n"
            f"  Recognized:   {result.recognized_text[:100]}..."
        )

    def test_wer_threshold(self, fixture: FixtureCase, engine: PaddleOcrEngine) -> None:
        """Assert WER is below the category threshold."""
        result = measure_quality(fixture.image_path, fixture.gt_path, engine)

        print(
            f"\n  {result.image_name} [{fixture.category}]: "
            f"CER={result.cer:.4f}, WER={result.wer:.4f} (max {fixture.max_wer})"
        )

        assert result.wer < fixture.max_wer, (
            f"{result.image_name}: WER {result.wer:.4f} >= threshold {fixture.max_wer}\n"
            f"  Ground truth: {result.ground_truth[:100]}...\n"
            f"  Recognized:   {result.recognized_text[:100]}..."
        )
