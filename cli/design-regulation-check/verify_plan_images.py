#!/usr/bin/env python3
"""QA for generated plan-view datum PNGs.

The section verifier intentionally expects section-only colors such as the
daylight envelope. Plan PNGs are different: they verify that parcel, road, and
neighbor datum samples are present and attached to plausible geometry.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parent


def non_background_ratio(image: Image.Image) -> float:
    img = image.convert("RGB")
    total = img.width * img.height
    non_bg = 0
    pixels = img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata()
    for r, g, b in pixels:
        if not (r > 238 and g > 238 and b > 238):
            non_bg += 1
    return non_bg / total if total else 0.0


def number(value: Any) -> float | None:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n if n == n else None


def verify_case(case: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": case.get("name", "unknown"),
        "pnu": case.get("pnu"),
        "file": case.get("file"),
        "pass": True,
        "checks": [],
    }

    if not case.get("pass"):
        result["pass"] = False
        result["checks"].append("FAIL upstream plan geometry checks failed")

    path = Path(str(case.get("file", "")))
    if not path.exists():
        result["pass"] = False
        result["checks"].append("FAIL image file missing")
        return result

    image = Image.open(path)
    result["size"] = [image.width, image.height]
    if image.width < 1000 or image.height < 700:
        result["pass"] = False
        result["checks"].append(f"FAIL image too small: {image.width}x{image.height}")

    ratio = non_background_ratio(image)
    result["nonBackgroundRatio"] = ratio
    if ratio < 0.03:
        result["pass"] = False
        result["checks"].append(f"FAIL plan image appears blank: nonBackgroundRatio={ratio:.4f}")

    source = case.get("source")
    if source != "ngii_local_dem":
        result["pass"] = False
        result["checks"].append(f"FAIL source={source}; expected ngii_local_dem")

    required_numbers = {
        "parcelDatum": case.get("parcelDatum"),
        "roadDatum": case.get("roadDatum"),
        "neighborDatum": case.get("neighborDatum"),
        "neighborAvgDatum": case.get("neighborAvgDatum"),
    }
    for key, value in required_numbers.items():
        if number(value) is None:
            result["pass"] = False
            result["checks"].append(f"FAIL missing numeric {key}")

    minimum_counts = {
        "parcelSamples": 8,
        "roadSamples": 1,
        "neighborSamples": 1,
        "roadFrontages": 1,
        "neighborParcels": 1,
    }
    for key, minimum in minimum_counts.items():
        value = number(case.get(key))
        if value is None or value < minimum:
            result["pass"] = False
            result["checks"].append(f"FAIL {key}={case.get(key)}; expected >= {minimum}")

    if result["pass"]:
        result["checks"].append("PASS plan datum image checks")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=str(ROOT / "out" / "plan" / "summary.json"))
    parser.add_argument("--out", default=str(ROOT / "out" / "plan" / "image-check.json"))
    args = parser.parse_args()

    summary_path = Path(args.summary)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    results = [verify_case(case) for case in summary.get("outputs", [])]
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
