"""
Batch verify all regulation lines for curated test parcels.

Loads tools/test_parcels.json and runs verify_setbacks.verify() on each,
collecting pass/fail counts by zone type. Produces a compact table.

Usage:
    cd ARR/backend
    PYTHONIOENCODING=utf-8 python tools/verify_all.py
    PYTHONIOENCODING=utf-8 python tools/verify_all.py --backend http://localhost:8000
    PYTHONIOENCODING=utf-8 python tools/verify_all.py --filter 주거  # partial zone name filter
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "test_parcels.json"

MARK_OK = "✓"
MARK_FAIL = "✗"
MARK_NA = "-"


def load_fixtures() -> list[dict]:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    return data["parcels"]


def verify_one(client: httpx.Client, parcel: dict) -> dict:
    """Run one parcel through boundary + auto-constraints, compare to expected."""
    pnu = parcel["pnu"]
    expected = parcel["expected"]
    want_drawn = set(parcel["expected_lines_drawn"])
    want_na = set(parcel["expected_na"])

    result = {
        "pnu": pnu,
        "address": parcel["address"],
        "expected_zone": parcel["zone"],
        "actual_zone": None,
        "bcr_match": False,
        "far_match": False,
        "sunlight_match": False,
        "lines_drawn": [],
        "lines_missing": [],
        "unexpected_na": [],
        "law_total": 0,
        "error": None,
    }

    try:
        sb = client.post("/design/site-boundary/", json={"pnu": pnu}, timeout=30.0).json()
        poly = sb.get("geometry")
        if not poly:
            result["error"] = "no boundary"
            return result
        ac = client.post(
            "/design/auto-constraints/",
            json={"pnu": pnu, "site_polygon": poly, "building_type": "공동주택"},
            timeout=120.0,
        ).json()
    except Exception as e:
        result["error"] = f"http: {e}"
        return result

    zones = ac.get("zones") or []
    reg = ac.get("regulations") or {}
    sg = ac.get("setback_geometries") or {}
    law = ac.get("law_articles") or {}

    result["actual_zone"] = zones[0] if zones else None
    result["bcr_match"] = reg.get("bcr_pct") == expected["bcr_pct"]
    result["far_match"] = reg.get("far_pct") == expected["far_pct"]
    result["sunlight_match"] = reg.get("sunlight_applies") == expected["sunlight_applies"]
    result["actual_bcr"] = reg.get("bcr_pct")
    result["actual_far"] = reg.get("far_pct")
    result["actual_sunlight"] = reg.get("sunlight_applies")

    drawn = {k for k, v in sg.items() if v}
    result["lines_drawn"] = sorted(drawn)
    result["lines_missing"] = sorted(want_drawn - drawn)
    result["unexpected_na"] = sorted(want_na & drawn)  # N/A expected but was drawn
    result["law_total"] = law.get("total_count", 0)
    return result


def format_result(r: dict) -> str:
    if r["error"]:
        return f"{MARK_FAIL} {r['pnu']}  {r['address']}  → {r['error']}"
    zone_ok = r["actual_zone"] == r["expected_zone"]
    bcr_mark = MARK_OK if r["bcr_match"] else MARK_FAIL
    far_mark = MARK_OK if r["far_match"] else MARK_FAIL
    sun_mark = MARK_OK if r["sunlight_match"] else MARK_FAIL
    zone_mark = MARK_OK if zone_ok else MARK_FAIL
    lines_part = f"lines={len(r['lines_drawn'])}"
    if r["lines_missing"]:
        lines_part += f" missing={r['lines_missing']}"
    if r["unexpected_na"]:
        lines_part += f" unexpected={r['unexpected_na']}"
    return (
        f"{r['pnu']}  {r['address']}\n"
        f"    {zone_mark} zone={r['actual_zone']}  (기대 {r['expected_zone']})\n"
        f"    {bcr_mark} BCR={r['actual_bcr']}%  {far_mark} FAR={r['actual_far']}%  "
        f"{sun_mark} sunlight={r['actual_sunlight']}\n"
        f"    {MARK_OK if not r['lines_missing'] and not r['unexpected_na'] else MARK_FAIL} {lines_part}  law={r['law_total']}건"
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Batch regulation-line verification")
    p.add_argument("--backend", default="http://localhost:8000")
    p.add_argument("--filter", default=None, help="partial zone name filter (e.g. 주거)")
    args = p.parse_args()

    parcels = load_fixtures()
    if args.filter:
        parcels = [p for p in parcels if args.filter in p["zone"]]
    if not parcels:
        print("no parcels matched", file=sys.stderr)
        return 1

    client = httpx.Client(base_url=args.backend)
    print(f"=== 배치 검증: {len(parcels)}개 필지 ===\n")

    all_pass = True
    zone_stats: dict[str, dict[str, int]] = {}
    for parcel in parcels:
        r = verify_one(client, parcel)
        print(format_result(r))
        print()
        zone = parcel["zone"]
        stat = zone_stats.setdefault(zone, {"total": 0, "pass": 0})
        stat["total"] += 1
        ok = (
            not r.get("error")
            and r.get("bcr_match")
            and r.get("far_match")
            and r.get("sunlight_match")
            and not r.get("lines_missing")
            and not r.get("unexpected_na")
        )
        if ok:
            stat["pass"] += 1
        else:
            all_pass = False

    print("─── 용도지역별 요약 ───")
    for zone, stat in sorted(zone_stats.items()):
        mark = MARK_OK if stat["pass"] == stat["total"] else MARK_FAIL
        print(f"  {mark} {zone}: {stat['pass']}/{stat['total']}")

    return 0 if all_pass else 2


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.exit(main())
