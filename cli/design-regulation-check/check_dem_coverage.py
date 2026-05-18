#!/usr/bin/env python3
"""Check which bundled /design cases are covered by the configured NGII DEM.

This is separate from the legal-section gate because a parcel outside the local
DEM tile should be reported as coverage missing, not patched with a non-NGII
elevation source.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib import request


ROOT = Path(__file__).resolve().parent


def post_json(url: str, payload: dict[str, Any], timeout_s: float) -> tuple[int, dict[str, Any]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_s) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI report should include transport errors.
        return 0, {"error": str(exc)}


def check_case(base: str, case: dict[str, Any], timeout_s: float) -> dict[str, Any]:
    site_status, site = post_json(f"{base}/design/site-boundary/", {"pnu": case["input"]}, timeout_s)
    if site_status != 200 or not site.get("geometry"):
        covered = False
        datum = {}
        errors = [site.get("error") or f"site-boundary failed: {site_status}"]
    else:
        auto_status, auto = post_json(
            f"{base}/design/auto-constraints/",
            {
                "pnu": site.get("pnu", case["input"]),
                "site_polygon": site["geometry"],
                "building_type": case.get("buildingType", "공동주택"),
            },
            timeout_s,
        )
        datum = ((auto.get("setback_geometries") or {}).get("datum_result") or {})
        covered = auto_status == 200 and datum.get("elevation_source") == "ngii_local_dem"
        errors = [auto.get("error")] if auto.get("error") else []

    expected = case.get("expectedCovered")
    pass_case = expected is None or covered is bool(expected)
    return {
        "name": case["name"],
        "input": case["input"],
        "pnu": site.get("pnu", case["input"]) if isinstance(site, dict) else case["input"],
        "expectedCovered": expected,
        "covered": covered,
        "pass": pass_case,
        "datum": {
            "source": datum.get("elevation_source"),
            "case": datum.get("case"),
            "parcel": datum.get("parcel_datum_m"),
            "road": datum.get("road_datum_m"),
            "neighbor": datum.get("neighbor_datum_m"),
            "neighborAvg": datum.get("neighbor_avg_datum_m"),
            "notes": datum.get("notes") or [],
        },
        "errors": [e for e in errors if e],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--cases", default=str(ROOT / "coverage-cases.json"))
    parser.add_argument("--out", default=str(ROOT / "out" / "dem-coverage.json"))
    parser.add_argument("--timeout", type=float, default=240.0)
    args = parser.parse_args()

    base = args.base.rstrip("/")
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    results = [check_case(base, case, args.timeout) for case in cases]
    payload = {
        "baseUrl": base,
        "pass": all(item["pass"] for item in results),
        "results": results,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
