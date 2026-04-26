"""
CLI: PNU 입력 → §119 datum elevation 6 케이스 자동 판정 + Open-Meteo raw 표고 출력.

Usage:
    cd ARR/backend
    PYTHONIOENCODING=utf-8 python tools/verify_datum_119.py <PNU>
    PYTHONIOENCODING=utf-8 python tools/verify_datum_119.py 1168010100106770003

검증 대상:
- 평탄지 (강남구 역삼동 677): 1168010100106770003
- 평탄지 (성북동): 1129010100103300000
- 경사지 (TBD): 한남동, 이태원, 청담 산기슭

출력:
- DatumCase + datum_m + basis
- parcel edge별 표고 (edge_idx, length, midpoint elev)
- 고저차 (max - min)
- §119 적용 여부 판단 근거
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from shapely.geometry import shape, MultiPolygon, Polygon  # noqa: E402

from land.services.datum import (  # noqa: E402
    DatumContext,
    compute_datum_elevation,
)


def verify(pnu: str, backend: str) -> int:
    client = httpx.Client(base_url=backend, timeout=60.0)
    print(f"=== §119 Datum 자동 검증 (PNU {pnu}) ===\n")

    # 1. PNU → polygon
    sb = client.post("/design/site-boundary/", json={"pnu": pnu}).json()
    if "geometry" not in sb:
        print(f"✗ site-boundary 응답에 geometry 없음: {sb}")
        return 1

    parcel = shape(sb["geometry"])
    if isinstance(parcel, MultiPolygon):
        parcel = max(parcel.geoms, key=lambda g: g.area)
    if not isinstance(parcel, Polygon):
        print(f"✗ Polygon 아님: {type(parcel).__name__}")
        return 1

    bb = parcel.bounds
    print(f"Parcel bounds: lon {bb[0]:.6f}~{bb[2]:.6f}, lat {bb[1]:.6f}~{bb[3]:.6f}")
    print(f"Parcel centroid: ({parcel.centroid.x:.6f}, {parcel.centroid.y:.6f})\n")

    # 2. compute_datum_elevation (Open-Meteo 호출)
    print("─── §119② 대지 자체 datum 계산 (도로 정보 없음) ───")
    ctx = DatumContext(parcel_wgs=parcel)
    result = compute_datum_elevation(ctx)

    print(f"  case        : {result.case.value}")
    print(f"  basis       : {result.basis}")
    print(f"  datum_m     : {result.elevation_m:.3f} m")
    if result.parcel_datum_m is not None:
        print(f"  parcel datum: {result.parcel_datum_m:.3f} m")

    # 3. Edge별 표고 출력
    if result.parcel_segments:
        elevs = [s["midpoint_elev_m"] for s in result.parcel_segments]
        diff = max(elevs) - min(elevs)
        print(f"\n─── Edge별 표고 ({len(result.parcel_segments)} edges) ───")
        for s in result.parcel_segments:
            print(
                f"  edge[{s['edge_idx']:2d}] L={s['length_m']:7.2f}m  "
                f"({s['midpoint_lng']:.5f}, {s['midpoint_lat']:.5f})  "
                f"elev={s['midpoint_elev_m']:7.2f}m"
            )
        print(f"\n  고저차 (max - min): {diff:.2f} m")
        if diff < 0.5:
            print("  → 평탄지 (variance < 0.5m)")
        elif diff <= 3.0:
            print("  → 경사지 §119② 가중평균 적용 (≤3m)")
        else:
            print("  → 경사지 §119② 단서 적용 대상 (>3m, 분할 필요)")

    if result.notes:
        print("\n─── Notes ───")
        for n in result.notes:
            print(f"  ⚠ {n}")

    # 4. JSON dump (디버그용)
    print("\n─── Raw result (JSON) ───")
    payload = {
        "case": result.case.value,
        "basis": result.basis,
        "elevation_m": round(result.elevation_m, 3),
        "parcel_datum_m": (
            round(result.parcel_datum_m, 3)
            if result.parcel_datum_m is not None else None
        ),
        "parcel_segments": result.parcel_segments,
        "notes": result.notes,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def main():
    p = argparse.ArgumentParser(description="§119 datum elevation 자동 검증 CLI")
    p.add_argument("pnu", help="19-digit PNU (e.g. 1168010100106770003)")
    p.add_argument("--backend", default="http://localhost:8000",
                   help="Django backend URL")
    args = p.parse_args()
    sys.exit(verify(args.pnu, args.backend))


if __name__ == "__main__":
    main()
