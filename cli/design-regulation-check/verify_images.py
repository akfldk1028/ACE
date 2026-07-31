#!/usr/bin/env python3
"""Pixel-level QA for generated legal section PNGs.

This checks that matplotlib artifacts are not blank and that expected colored
datum/envelope lines are actually present in the rendered image.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parent


COLORS: dict[str, tuple[int, int, int]] = {
    "parcel_yellow": (234, 179, 8),
    "road_orange": (249, 115, 22),
    "neighbor_blue": (37, 99, 235),
    "avg86_green": (22, 163, 74),
    "sunlight_pink": (236, 72, 153),
    "daylight_purple": (126, 34, 206),
    "mass_gray": (148, 163, 184),
}


def close_to(pixel: tuple[int, int, int], rgb: tuple[int, int, int], tolerance: int) -> bool:
    return all(abs(int(pixel[i]) - rgb[i]) <= tolerance for i in range(3))


def count_color(image: Image.Image, rgb: tuple[int, int, int], tolerance: int = 28) -> int:
    img = image.convert("RGB")
    count = 0
    for pixel in iter_pixels(img):
        if close_to(pixel, rgb, tolerance):
            count += 1
    return count


def iter_pixels(image: Image.Image):
    if hasattr(image, "get_flattened_data"):
        return image.get_flattened_data()
    return image.getdata()


def non_background_ratio(image: Image.Image) -> float:
    img = image.convert("RGB")
    total = img.width * img.height
    non_bg = 0
    for r, g, b in iter_pixels(img):
        # White plot/background and pale grid are considered background.
        if not (r > 235 and g > 235 and b > 235):
            non_bg += 1
    return non_bg / total if total else 0.0


def expected_counts(case: dict[str, Any]) -> dict[str, int]:
    expected = {
        # Datum lines can overlap at identical elevations; later lines cover part
        # of earlier dashed lines, so these thresholds assert presence, not length.
        "parcel_yellow": 80,
        "road_orange": 80,
        "neighbor_blue": 80,
        "avg86_green": 80,
        "daylight_purple": 250,
        "mass_gray": 500,
    }
    if case.get("sunlightDatum") is not None:
        expected["sunlight_pink"] = 250
    return expected


def verify_image(case: dict[str, Any]) -> dict[str, Any]:
    if not case.get("pass", False) or not case.get("file"):
        return {
            "name": case.get("name", "unknown"),
            "file": case.get("file"),
            "pass": False,
            "checks": [f"FAIL upstream render failed: {case.get('error', 'missing file')}"],
            "counts": {},
        }
    file_path = Path(case["file"])
    result: dict[str, Any] = {
        "name": case["name"],
        "file": str(file_path),
        "pass": True,
        "checks": [],
        "counts": {},
    }
    if not file_path.exists():
        result["pass"] = False
        result["checks"].append("FAIL image file missing")
        return result

    image = Image.open(file_path)
    result["size"] = [image.width, image.height]
    if image.width < 1000 or image.height < 700:
        result["pass"] = False
        result["checks"].append(f"FAIL image too small: {image.width}x{image.height}")

    ratio = non_background_ratio(image)
    result["nonBackgroundRatio"] = ratio
    if ratio < 0.01:
        result["pass"] = False
        result["checks"].append(f"FAIL image appears blank: nonBackgroundRatio={ratio:.4f}")

    for key, threshold in expected_counts(case).items():
        count = count_color(image, COLORS[key])
        result["counts"][key] = count
        if count < threshold:
            result["pass"] = False
            result["checks"].append(f"FAIL missing {key}: count={count}, expected>={threshold}")

    if result["pass"]:
        result["checks"].append("PASS image pixel checks")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(ROOT / "out" / "pysections" / "summary.json"))
    parser.add_argument("--out", default=str(ROOT / "out" / "pysections" / "image-check.json"))
    args = parser.parse_args()

    summary_path = Path(args.summary)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    results = [verify_image(case) for case in summary.get("outputs", [])]
    payload = {
        "sourceSummary": str(summary_path),
        "pass": all(item["pass"] for item in results),
        "results": results,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
