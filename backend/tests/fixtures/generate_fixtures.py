#!/usr/bin/env python3
"""Generate synthetic test images with perfectly known ground truth.

Produces fixture images across three categories for OCR quality benchmarking:
- clean: Printed English paragraph text at 300 DPI
- multicol: Two-column layouts with a dividing gap
- degraded: Clean text with mild rotation, noise, or reduced contrast

Each image gets a matching .gt.txt file with the exact rendered text.
Run: cd backend && python tests/fixtures/generate_fixtures.py
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FIXTURE_DIR = Path(__file__).parent

# ─── Text content ────────────────────────────────────────────────────

CLEAN_TEXTS = [
    (
        "The quick brown fox jumps over the lazy dog. "
        "Pack my box with five dozen liquor jugs. "
        "How vexingly quick daft zebras jump."
    ),
    (
        "A journey of a thousand miles begins with a single step. "
        "Knowledge is power, and wisdom is its application. "
        "The only limit to our realization of tomorrow is our doubts of today."
    ),
    (
        "In the beginning was the Word, and the Word was with God. "
        "To be or not to be, that is the question. "
        "All that glitters is not gold, but it certainly catches the eye."
    ),
]

MULTICOL_TEXTS = [
    (
        # Left column
        (
            "Document processing has evolved\n"
            "significantly over the past decade.\n"
            "Modern OCR engines can recognize\n"
            "text with remarkable accuracy."
        ),
        # Right column
        (
            "Quality benchmarks ensure that\n"
            "recognition meets standards.\n"
            "Automated testing prevents\n"
            "regressions in performance."
        ),
    ),
    (
        (
            "The first column contains text\n"
            "that flows naturally from top\n"
            "to bottom like a newspaper.\n"
            "Each line is a separate phrase."
        ),
        (
            "The second column mirrors the\n"
            "layout of the first column.\n"
            "This tests multi-column OCR\n"
            "reading order detection."
        ),
    ),
]

DEGRADED_TEXTS = [
    (
        "Slightly tilted text tests the robustness of OCR engines. "
        "Even a small rotation can challenge recognition accuracy."
    ),
    (
        "Noisy backgrounds simulate real world scanning conditions. "
        "Dust and grain affect character segmentation quality."
    ),
]


# ─── Font loading ────────────────────────────────────────────────────

def _load_font(size: int = 32) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a TrueType font with macOS/Linux fallbacks."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Times.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except (OSError, IOError):
            continue
    # Last resort — default bitmap font (lower quality but works everywhere)
    return ImageFont.load_default()


# ─── Generators ──────────────────────────────────────────────────────

def _generate_clean(text: str, output_path: Path, font_size: int = 32) -> str:
    """Generate a clean printed text image. Returns the ground truth text."""
    font = _load_font(font_size)
    # 300 DPI A5-ish dimensions
    width, height = 2400, 800
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Word-wrap text to fit the image width with margins
    margin = 100
    max_text_width = width - 2 * margin
    lines = _word_wrap(draw, text, font, max_text_width)
    ground_truth = "\n".join(lines)

    y = margin
    line_spacing = font_size + 12
    for line in lines:
        draw.text((margin, y), line, fill="black", font=font)
        y += line_spacing

    img.save(output_path, dpi=(300, 300))
    return ground_truth


def _generate_multicol(
    left_text: str, right_text: str, output_path: Path, font_size: int = 28
) -> str:
    """Generate a two-column layout image. Returns ground truth (left then right)."""
    font = _load_font(font_size)
    width, height = 2400, 800
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    margin = 100
    col_gap = 160
    col_width = (width - 2 * margin - col_gap) // 2
    line_spacing = font_size + 10

    # Left column
    left_lines = left_text.split("\n")
    y = margin
    for line in left_lines:
        draw.text((margin, y), line, fill="black", font=font)
        y += line_spacing

    # Right column
    right_lines = right_text.split("\n")
    right_x = margin + col_width + col_gap
    y = margin
    for line in right_lines:
        draw.text((right_x, y), line, fill="black", font=font)
        y += line_spacing

    img.save(output_path, dpi=(300, 300))

    # Ground truth: interleave left/right lines by row position.
    # PaddleOCR reads top-to-bottom, left-to-right across columns,
    # producing: left-line-1, right-line-1, left-line-2, right-line-2, etc.
    interleaved: list[str] = []
    max_lines = max(len(left_lines), len(right_lines))
    for i in range(max_lines):
        if i < len(left_lines):
            interleaved.append(left_lines[i])
        if i < len(right_lines):
            interleaved.append(right_lines[i])
    ground_truth = "\n".join(interleaved)
    return ground_truth


def _generate_degraded_rotated(text: str, output_path: Path, font_size: int = 32) -> str:
    """Generate text with mild rotation (~2°). Returns ground truth."""
    font = _load_font(font_size)
    width, height = 2400, 800
    # Render on a larger canvas to avoid clipping after rotation
    pad = 200
    img = Image.new("RGB", (width + pad * 2, height + pad * 2), color="white")
    draw = ImageDraw.Draw(img)

    margin = 100 + pad
    max_text_width = width - 200
    lines = _word_wrap(draw, text, font, max_text_width)
    ground_truth = "\n".join(lines)

    y = margin
    line_spacing = font_size + 12
    for line in lines:
        draw.text((margin, y), line, fill="black", font=font)
        y += line_spacing

    # Rotate 2 degrees
    img = img.rotate(2, resample=Image.BICUBIC, fillcolor="white")
    # Crop back to original size
    img = img.crop((pad, pad, pad + width, pad + height))

    img.save(output_path, dpi=(300, 300))
    return ground_truth


def _generate_degraded_noisy(text: str, output_path: Path, font_size: int = 32) -> str:
    """Generate text with Gaussian noise overlay. Returns ground truth."""
    font = _load_font(font_size)
    width, height = 2400, 800
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    margin = 100
    max_text_width = width - 2 * margin
    lines = _word_wrap(draw, text, font, max_text_width)
    ground_truth = "\n".join(lines)

    y = margin
    line_spacing = font_size + 12
    for line in lines:
        draw.text((margin, y), line, fill="black", font=font)
        y += line_spacing

    # Add mild Gaussian noise
    arr = np.array(img, dtype=np.float32)
    noise = np.random.default_rng(42).normal(0, 12, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    # Slight blur to simulate scan quality
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    img.save(output_path, dpi=(300, 300))
    return ground_truth


# ─── Utilities ───────────────────────────────────────────────────────

def _word_wrap(
    draw: ImageDraw.ImageDraw, text: str, font, max_width: int
) -> list[str]:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current_line: list[str] = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


# ─── Main ────────────────────────────────────────────────────────────

def generate_all() -> dict[str, list[tuple[Path, Path]]]:
    """Generate all fixture images and ground truth files.

    Returns a dict mapping category -> list of (image_path, gt_path) tuples.
    """
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    fixtures: dict[str, list[tuple[Path, Path]]] = {
        "clean": [],
        "multicol": [],
        "degraded": [],
    }

    # ── Clean fixtures ──
    for i, text in enumerate(CLEAN_TEXTS, start=1):
        img_path = FIXTURE_DIR / f"clean_{i:02d}.png"
        gt_path = FIXTURE_DIR / f"clean_{i:02d}.gt.txt"
        ground_truth = _generate_clean(text, img_path)
        gt_path.write_text(ground_truth, encoding="utf-8")
        fixtures["clean"].append((img_path, gt_path))
        print(f"  ✓ {img_path.name} ({len(ground_truth)} chars)")

    # ── Multi-column fixtures ──
    for i, (left, right) in enumerate(MULTICOL_TEXTS, start=1):
        img_path = FIXTURE_DIR / f"multicol_{i:02d}.png"
        gt_path = FIXTURE_DIR / f"multicol_{i:02d}.gt.txt"
        ground_truth = _generate_multicol(left, right, img_path)
        fixtures["multicol"].append((img_path, gt_path))
        gt_path.write_text(ground_truth, encoding="utf-8")
        print(f"  ✓ {img_path.name} ({len(ground_truth)} chars)")

    # ── Degraded fixtures ──
    degraded_generators = [_generate_degraded_rotated, _generate_degraded_noisy]
    for i, (text, gen_fn) in enumerate(
        zip(DEGRADED_TEXTS, degraded_generators), start=1
    ):
        img_path = FIXTURE_DIR / f"degraded_{i:02d}.png"
        gt_path = FIXTURE_DIR / f"degraded_{i:02d}.gt.txt"
        ground_truth = gen_fn(text, img_path)
        gt_path.write_text(ground_truth, encoding="utf-8")
        fixtures["degraded"].append((img_path, gt_path))
        print(f"  ✓ {img_path.name} ({len(ground_truth)} chars)")

    return fixtures


if __name__ == "__main__":
    print("Generating OCR test fixtures...")
    results = generate_all()
    total = sum(len(v) for v in results.values())
    print(f"\nGenerated {total} fixtures in {FIXTURE_DIR}")
    for category, items in results.items():
        print(f"  {category}: {len(items)} images")
