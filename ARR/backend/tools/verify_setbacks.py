"""
CLI: verify all setback regulation lines for a parcel.

Calls Django `/design/site-boundary/` + `/design/auto-constraints/` and prints:
  - zone + BCR/FAR numerical values vs 법 상한 reference
  - all 7 regulation lines (distance_m, geometry type, vertex count)
  - which lines are N/A and why
  - 3D envelope walls (heights min/max)
  - law articles total count

Usage:
    python tools/verify_setbacks.py <PNU> [--building-type "공동주택"]
    python tools/verify_setbacks.py 1168010100106770000
    python tools/verify_setbacks.py 1168010100106770000 --building-type 근린생활시설
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx

DEFAULT_BACKEND = "http://localhost:8000"

# Reference 법 상한 for 주요 zone (국계법 시행령 §84, §85)
ZONE_REFERENCE: dict[str, dict[str, Any]] = {
    "제1종전용주거지역": {"bcr": 50, "far_min": 50, "far_max": 100, "sunlight": True},
    "제2종전용주거지역": {"bcr": 50, "far_min": 50, "far_max": 150, "sunlight": True},
    "제1종일반주거지역": {"bcr": 60, "far_min": 100, "far_max": 200, "sunlight": True},
    "제2종일반주거지역": {"bcr": 60, "far_min": 100, "far_max": 250, "sunlight": True},
    "제3종일반주거지역": {"bcr": 50, "far_min": 100, "far_max": 300, "sunlight": True},
    "준주거지역": {"bcr": 70, "far_min": 200, "far_max": 500, "sunlight": False},
    "중심상업지역": {"bcr": 90, "far_min": 200, "far_max": 1500, "sunlight": False},
    "일반상업지역": {"bcr": 80, "far_min": 200, "far_max": 1300, "sunlight": False},
    "근린상업지역": {"bcr": 70, "far_min": 200, "far_max": 900, "sunlight": False},
    "유통상업지역": {"bcr": 80, "far_min": 200, "far_max": 1100, "sunlight": False},
}

# Expected setback line types and their legal basis
LINE_SPEC = {
    "buildable_area":            ("건축가능영역",    "모든 이격/사선 적용 후 실제 건축 가능한 폴리곤"),
    "north_setback":             ("정북 일조사선",    "건축법 §61, 시행령 §86 — 전용주거+일반주거만 적용"),
    "adjacent_setback":          ("인접대지 이격",    "건축법 §58 — 전 용도지역 공통 (기본 0.5m)"),
    "road_setback":              ("건축선 후퇴",     "건축법 §46-47 — 전면도로 확장"),
    "corner_cutoff":             ("가각전제",        "시행령 §31 — 8m 미만 도로 모퉁이, 교차각별 cutoff"),
    "building_designation_line": ("건축지정선",      "지구단위계획구역에서만 적용 (없으면 N/A)"),
    "sunlight_envelope":         ("정북 일조 경사면(3D)", "H≤10m→1.5m, H>10m→H×0.5 (Cesium 3D wall)"),
    "daylight_diagonal_envelope":("채광사선 경사면(3D)", "시행령 §86 — 공동주택 인접경계, H/수평거리 비율"),
}


def pick(d: dict | None, *keys, default=None):
    cur = d or {}
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
    return cur


def check_mark(ok: bool) -> str:
    return "✓" if ok else "✗"


def call_site_boundary(client: httpx.Client, pnu: str) -> dict:
    r = client.post("/design/site-boundary/", json={"pnu": pnu}, timeout=30.0)
    r.raise_for_status()
    return r.json()


def call_auto_constraints(
    client: httpx.Client, pnu: str, site_polygon: dict, building_type: str
) -> dict:
    r = client.post(
        "/design/auto-constraints/",
        json={"pnu": pnu, "site_polygon": site_polygon, "building_type": building_type},
        timeout=90.0,
    )
    r.raise_for_status()
    return r.json()


def describe_geometry(g: dict | None) -> str:
    if not isinstance(g, dict):
        return "no geometry"
    t = g.get("type", "?")
    coords = g.get("coordinates")
    if t == "Polygon" and isinstance(coords, list):
        return f"Polygon (꼭지점 {len(coords[0]) if coords else 0}개)"
    if t == "MultiPolygon" and isinstance(coords, list):
        return f"MultiPolygon ({len(coords)} part)"
    if t == "LineString" and isinstance(coords, list):
        return f"LineString ({len(coords)} 점)"
    if t == "MultiLineString" and isinstance(coords, list):
        seg_lens = [len(seg) for seg in coords]
        return f"MultiLineString ({len(coords)} 세그먼트, 각 {seg_lens} 점)"
    return f"{t}"


def describe_walls(walls: list | None) -> str:
    if not isinstance(walls, list) or not walls:
        return "walls 없음"
    heights: list[float] = []
    for w in walls:
        mh = w.get("max_heights") if isinstance(w, dict) else None
        if isinstance(mh, list):
            heights.extend(float(h) for h in mh if isinstance(h, (int, float)))
    if heights:
        return f"{len(walls)} walls, 최대높이 {max(heights):.1f}m, 최소 {min(heights):.1f}m"
    return f"{len(walls)} walls (heights 없음)"


def verify(pnu: str, building_type: str, backend: str) -> int:
    client = httpx.Client(base_url=backend)
    print(f"=== 규제선 검증 (PNU: {pnu}, 건물용도: {building_type}) ===\n")

    # 1) site-boundary
    try:
        sb = call_site_boundary(client, pnu)
    except Exception as e:
        print(f"✗ site-boundary 실패: {e}")
        return 1
    site_area = sb.get("area_m2")
    site_polygon = sb.get("geometry")
    print(f"대지면적: {site_area:.2f} m²" if site_area else "대지면적: ?")
    print(f"필지 polygon: {describe_geometry(site_polygon)}\n")

    # 2) auto-constraints (규제선 계산 + 법조항)
    try:
        ac = call_auto_constraints(client, pnu, site_polygon, building_type)
    except Exception as e:
        print(f"✗ auto-constraints 실패: {e}")
        return 1

    zones = ac.get("zones") or []
    reg = ac.get("regulations") or {}
    sg = ac.get("setback_geometries") or {}
    law = ac.get("law_articles") or {}

    # 3) BCR/FAR 수치 vs 법 상한 대조
    print("─── 용도지역 / BCR / FAR ───")
    zone = zones[0] if zones else None
    print(f"용도지역: {zone or '(미확인)'}")
    if zone and zone in ZONE_REFERENCE:
        ref = ZONE_REFERENCE[zone]
        bcr = reg.get("bcr_pct")
        far = reg.get("far_pct")
        bcr_ok = bcr == ref["bcr"]
        far_ok = far is not None and ref["far_min"] <= far <= ref["far_max"]
        print(f"  {check_mark(bcr_ok)} BCR: {bcr}%  (법 상한 {ref['bcr']}%)")
        print(f"  {check_mark(far_ok)} FAR: {far}%  (법 범위 {ref['far_min']}~{ref['far_max']}%)")
        print(f"  ※ 정북일조 적용: {'예' if ref['sunlight'] else '아니오 (상업/준주거)'}")
        sunlight_flag = reg.get("sunlight_applies")
        sunlight_ok = sunlight_flag == ref["sunlight"]
        print(f"  {check_mark(sunlight_ok)} sunlight_applies 플래그: {sunlight_flag}  (기대 {ref['sunlight']})")
    else:
        print(f"  (레퍼런스 테이블 없음) BCR={reg.get('bcr_pct')}%, FAR={reg.get('far_pct')}%")
    print(f"  이격거리: adjacent={reg.get('adjacent_setback_m')}m, "
          f"corner_cutoff_required={reg.get('corner_cutoff_required')}, "
          f"daylight_multiplier={reg.get('daylight_diagonal_multiplier')}")

    # 4) 규제선 7종 검증
    print("\n─── 규제선 (setback_geometries) ───")
    sunlight_applicable = (
        ZONE_REFERENCE.get(zone, {}).get("sunlight", False) if zone else False
    )
    drawn = 0
    skipped_ok = 0
    drawn_bad = 0
    for key, (ko, basis) in LINE_SPEC.items():
        v = sg.get(key)
        if v is None:
            # Expected to be absent in certain zones
            if key in ("north_setback", "sunlight_envelope") and not sunlight_applicable:
                print(f"  ✗ {ko} ({key}): N/A (상업/준주거 — 법상 적용 제외) — 정상")
                skipped_ok += 1
            elif key == "building_designation_line":
                print(f"  ✗ {ko} ({key}): N/A (지구단위계획구역 아님) — 정상")
                skipped_ok += 1
            else:
                print(f"  ✗ {ko} ({key}): 누락 ⚠️  (기대됨: {basis})")
                drawn_bad += 1
            continue

        # envelope vs geometry
        if "walls" in v:
            walls_desc = describe_walls(v["walls"])
            print(f"  ✓ {ko} ({key}): {walls_desc}")
            drawn += 1
        else:
            geom = v.get("geometry")
            dist = v.get("distance_m")
            label = v.get("label", "")
            desc = describe_geometry(geom)
            dist_str = f"{dist}m" if dist is not None else "?"
            print(f"  ✓ {ko} ({key}): {desc}, 이격={dist_str}  [{label}]")
            drawn += 1

    # 5) Law articles
    print("\n─── 법조항 ───")
    print(f"검색된 법조항: {law.get('total_count', 0)}건")
    errors = law.get("errors") or []
    if errors:
        print(f"  ⚠️ 검색 에러 {len(errors)}건: {errors[:2]}")

    # 6) Summary
    print("\n─── 종합 ───")
    total_expected = len(LINE_SPEC)
    print(f"그려진 선: {drawn}/{total_expected}")
    print(f"법상 N/A (정상): {skipped_ok}")
    print(f"누락 (문제): {drawn_bad}")
    return 0 if drawn_bad == 0 else 2


def main() -> int:
    p = argparse.ArgumentParser(description="필지 규제선 CLI 검증")
    p.add_argument("pnu", help="19자리 PNU")
    p.add_argument("--building-type", default="공동주택", help="건물 용도 (기본: 공동주택)")
    p.add_argument("--backend", default=DEFAULT_BACKEND, help=f"백엔드 URL (기본 {DEFAULT_BACKEND})")
    args = p.parse_args()
    return verify(args.pnu, args.building_type, args.backend)


if __name__ == "__main__":
    sys.exit(main())
