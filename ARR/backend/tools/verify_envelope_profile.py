"""
Verify 정북일조 envelope profile matches 건축법 시행령 §86①.

Checks that the envelope has correct shape:
1. Vertical wall at x=1.5m, H=0→10m (직각)
2. Plateau termination at x=5m, H=10m (slope 시작점)
3. Sloped layer walls at x ∈ {7.5, 10, 12.5, 15, 20, 25, 30m} with H=2x

Usage:
    cd ARR/backend
    PYTHONIOENCODING=utf-8 python tools/verify_envelope_profile.py <PNU>
    PYTHONIOENCODING=utf-8 python tools/verify_envelope_profile.py 1168011800104670003
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

import httpx


def verify(pnu: str, backend: str) -> int:
    client = httpx.Client(base_url=backend, timeout=120.0)
    sb = client.post("/design/site-boundary/", json={"pnu": pnu}).json()
    poly = sb.get("geometry")
    if not poly:
        print(f"✗ no boundary for {pnu}")
        return 1
    ac = client.post(
        "/design/auto-constraints/",
        json={"pnu": pnu, "site_polygon": poly, "building_type": "공동주택"},
    ).json()
    zone = (ac.get("zones") or ["?"])[0]
    env = ac.get("setback_geometries", {}).get("sunlight_envelope")

    print(f"=== 정북일조 envelope profile 검증 (PNU: {pnu}, zone: {zone}) ===\n")

    if not env:
        reg = ac.get("regulations", {})
        if not reg.get("sunlight_applies"):
            print(f"sunlight_applies=False ({zone} 미적용). 검증 대상 아님.")
            return 0
        print("✗ sunlight_applies=True 인데 envelope 없음 — BUG")
        return 2

    thresholds = env.get("thresholds", [])
    # Unique (dist, h_max) per edge collapsed
    unique: dict[tuple, str] = {}
    for t in thresholds:
        key = (round(t["distance_m"], 2), round(t["max_height_m"], 2))
        unique[key] = t["kind"]

    # Expected profile per §86① (base_setback=1.5m, base_height=10m, slope=2:1)
    expected = [
        (1.5, 10.0, "vertical",     "수직 직각벽 at x=1.5m, H=0→10m"),
        (5.0, 10.0, "plateau_end",  "평탄부 한계 at x=5m, H=10m (slope 시작)"),
        (7.5, 15.0, "slope",        "사선 H=2×7.5=15m"),
        (10.0, 20.0, "slope",       "H=20m"),
        (12.5, 25.0, "slope",       "H=25m"),
        (15.0, 30.0, "slope",       "H=30m"),
        (20.0, 40.0, "slope",       "H=40m"),
        (25.0, 50.0, "slope",       "H=50m"),
        (30.0, 60.0, "slope",       "H=60m"),
    ]

    print(f"law_basis: {env.get('law_basis')}")
    print(f"base_setback={env.get('base_setback_m')}m, "
          f"base_height={env.get('base_height_m')}m, slope={env.get('slope')}:1")
    print(f"max_depth={env.get('max_depth_m')}m, walls={len(env.get('walls') or [])}\n")

    print(f"{'x(m)':>6}  {'H(m)':>6}  {'kind':<14}  {'spec 설명':<35}  status")
    fails = 0
    for dist, h, kind, desc in expected:
        actual = unique.get((dist, h))
        ok = actual == kind
        if not ok:
            # Some tail samples clamped by max_depth — allow missing but not wrong
            if actual is None and dist > env.get("max_depth_m", 30):
                mark = "–"  # skipped (max_depth)
            else:
                fails += 1
                mark = "✗"
        else:
            mark = "✓"
        print(f"{dist:>6.1f}  {h:>6.1f}  {(actual or 'MISSING'):<14}  {desc:<35}  {mark}")

    print()
    if fails == 0:
        print("✓ envelope profile 법규(§86①) 일치")
        return 0
    print(f"✗ {fails}개 불일치")
    return 2


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("pnu")
    p.add_argument("--backend", default="http://localhost:8000")
    args = p.parse_args()
    return verify(args.pnu, args.backend)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.exit(main())
