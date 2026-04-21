"""
정북 일조사선 envelope (건축법 §61①, 시행령 §86①, 2023.9.12 개정).

**⚠️ LOCKED SPEC — DO NOT MODIFY** without reading
    `memory/arr/session14/envelope-locked-spec.md`
이 구현은 session14 (2026-04-21) 사용자 검증을 거친 결과.

================================================================
법규 §86① 단면 (북측 경계에서 남쪽으로 x 진행)
================================================================
    H (m)
    |                            /     ← slope 2:1 (H = 2x, §86①제2호)
    |                          /
    | 50 ────────────────────      ← cap (max_depth × slope)
    |                          /
    |                        /
    | 10 ────┐──────────────        ← H=10m plateau 시작 (§86①제1호)
    |        │
    |        │                     ← 수직 직각벽 (x=1.5m, H=0→10m)
    | 0 ─────┴──────────────────→ x
             1.5            25m
             ↑ base_setback

================================================================
Output 구조 (frontend renderer와 계약)
================================================================
{
  "walls": [                            # 북쪽 수직 직각벽 (§86①제1호)
    {"positions": [[lng, lat], [lng, lat]],
     "min_heights": [0.0, 0.0],
     "max_heights": [10.0, 10.0],
     "kind": "north_vertical"},
    ...
  ],
  "slanted_polygons": [                  # §86①제2호 경사면 (per-vertex 높이)
    {"corners": [[lng, lat, h], ...],    # h = max(10, d×2), cap 50
     "label": "...",
     "kind": "slope"},
  ],
  "profile_polylines": [...],            # 2D 단면도용 (수직→평탄→경사)
  "envelope_layers": [...],              # 계단식 시각화 (선택)
  "slope": 2.0,
  "base_setback_m": 1.5,
  "base_height_m": 10.0,
  "max_depth_m": 25.0,
  "thresholds": [...],
  "law_basis": "건축법 §61①, 시행령 §86① (2023.9.12 개정 9→10m)",
}

================================================================
설계 결정 (과거 세션에서 반복 실패 후 확정)
================================================================
1. **envelope footprint = parcel.buffer(-1.5m)** (inner polygon, 42 corners)
   - 필지 외곽선에서 직접 솟으면 "떠 있는" 느낌 → 1.5m 안쪽에서 솟도록.
   - §86① "인접경계에서 1.5m 이격 내부에 건축 가능" 반영.
2. **per-vertex 높이 = max(10, d×2), cap 50m** (Ladybug solar_rights 수식)
   - d = 해당 점에서 북측 경계 MultiLineString까지 최단거리
   - 북측 edge 정의: inward normal의 -ny > 0.3 (정북 ±~72°)
3. **walls = 북쪽 edge만** (H=10m 바로 아래로 내려오는 수직벽)
   - 사용자 img_18 피드백: "직선→사선 올라가는 면은 있고,
     사선→바닥 떨어지는 수직면은 없어야 함"
   - 구현: slanted polygon corners 중 H≈10m인 인접 쌍을 wall로.
4. **남/동/서쪽 측벽 없음** (사선이 그대로 이어짐)
"""

from __future__ import annotations

import logging
import math

from pyproj import Transformer
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.ops import transform

logger = logging.getLogger(__name__)

# ── 법규 상수 (§86①) — 수정 금지 ────────────────────────
BASE_SETBACK_M = 1.5       # §86①제1호: 인접경계 수직 이격
BASE_HEIGHT_M = 10.0       # §86①제1호: 수직벽 최대 높이 (2023.9.12 개정 9→10m)
SLOPE = 2.0                # §86①제2호: H = 2x (H/2 이격의 역수)
MAX_DEPTH_CAP_M = 25.0     # 시각화 cap: slope × max_depth = 50m (H_max)
PLATEAU_END_M = 5.0        # H=10m 평탄부 끝 (x=1.5~5m)
NORTH_EDGE_NY_THRESHOLD = 0.3  # 정북 법선 판정: -ny > 0.3 (±~72°)

_to_wgs = Transformer.from_crs("EPSG:32652", "EPSG:4326", always_xy=True)


def _utm_to_wgs(geom):
    return transform(_to_wgs.transform, geom)


def _inward_normal(edge: LineString, centroid: Point) -> tuple[float, float]:
    """edge의 내측 법선 벡터 (centroid 방향). 단위 벡터."""
    dx = edge.coords[1][0] - edge.coords[0][0]
    dy = edge.coords[1][1] - edge.coords[0][1]
    length = math.sqrt(dx * dx + dy * dy)
    if length < 0.01:
        return (0.0, 0.0)
    nx = -dy / length
    ny = dx / length
    mid = edge.interpolate(0.5, normalized=True)
    if nx * (centroid.x - mid.x) + ny * (centroid.y - mid.y) < 0:
        nx, ny = -nx, -ny
    return (nx, ny)


def _wgs_pt(utm_pt: tuple) -> list:
    p = _utm_to_wgs(Point(utm_pt[0], utm_pt[1]))
    return [p.x, p.y]


def compute_sunlight_envelope(
    north_edges: list[LineString],
    parcel_utm: Polygon,
    sunlight_rules: list | None = None,
) -> dict | None:
    """
    정북 일조사선 envelope 생성.

    Args:
        north_edges: _classify_edges()["north"] 리스트 (LineString, UTM)
        parcel_utm: 필지 Polygon (UTM EPSG:32652)
        sunlight_rules: 법규 rule (미사용, 호환 위해 유지)

    Returns:
        dict (위 모듈 docstring 구조) or None (북측 edge 없음).
    """
    try:
        if not north_edges:
            return None

        centroid = parcel_utm.centroid
        walls: list = []
        slanted_polygons: list = []
        profile_polylines: list = []
        envelope_layers: list = []
        thresholds: list = []

        # ── 1. 대표 북측 edge (혼란 방지용) ────────────────
        primary = _pick_primary_edge(north_edges, centroid)
        primary_edges = [primary[0]] if primary else []

        # ── 2. envelope slanted polygon + 북쪽 수직벽 생성 ──
        _emit_slanted_polygon_and_walls(
            north_edges, parcel_utm, centroid,
            slanted_polygons, walls, thresholds,
        )

        # ── 3. 2D 단면 프로파일 (수직→평탄→경사) ───────────
        _emit_profile_polylines(primary_edges, centroid, profile_polylines)

        # ── 4. 계단식 envelope 층 (선택적 시각화) ──────────
        _emit_envelope_layers(north_edges, parcel_utm, centroid, envelope_layers)

        if not walls and not slanted_polygons and not envelope_layers:
            return None

        return {
            "walls": walls,
            "slanted_polygons": slanted_polygons,
            "profile_polylines": profile_polylines,
            "envelope_layers": envelope_layers,
            "slope": SLOPE,
            "base_setback_m": BASE_SETBACK_M,
            "base_height_m": BASE_HEIGHT_M,
            "max_depth_m": MAX_DEPTH_CAP_M,
            "thresholds": thresholds,
            "law_basis": "건축법 §61①, 시행령 §86① (2023.9.12 개정 9→10m)",
        }

    except Exception as e:
        logger.warning(f"sunlight_envelope failed: {e}")
        return None


# ───────────────────────────────────────────────────────────────
# Internal helpers
# ───────────────────────────────────────────────────────────────


def _pick_primary_edge(edges: list[LineString], centroid: Point) -> tuple | None:
    """북측 edge 중 '가장 대표적인' edge 1개 선택. 기준: length × max(0, -ny)."""
    best = None
    best_score = -1.0
    for e in edges:
        nx_, ny_ = _inward_normal(e, centroid)
        if nx_ == 0 and ny_ == 0:
            continue
        sc = e.length * max(0.0, -ny_)
        if sc > best_score:
            best_score = sc
            best = (e, nx_, ny_)
    return best


def _emit_slanted_polygon_and_walls(
    north_edges: list[LineString],
    parcel_utm: Polygon,
    centroid: Point,
    slanted_polygons: list,
    walls: list,
    thresholds: list,
) -> None:
    """
    핵심 로직. 북측 경계로부터 per-vertex distance 기반 envelope 생성.

    - envelope footprint = parcel.buffer(-1.5m) 의 외곽 ring
    - 각 vertex: d = 북쪽 MultiLineString 최단거리
    - H = min(50, max(10, d × 2))
    - walls: H ≈ 10m 인접 쌍 → 북쪽 수직벽 (H=0→10m)
    """
    try:
        # 정북 edge 필터 (inward -ny > 0.3 = 정북 ±~72°)
        north_lines = [
            e for e in north_edges
            if -_inward_normal(e, centroid)[1] > NORTH_EDGE_NY_THRESHOLD
        ]
        if not north_lines:
            north_lines = list(north_edges)

        if not north_lines:
            return

        north_mls = (
            MultiLineString(north_lines) if len(north_lines) > 1 else north_lines[0]
        )

        # envelope 바닥 outline: parcel을 1.5m 안쪽으로 이격
        try:
            inner_poly = parcel_utm.buffer(-BASE_SETBACK_M)
            if isinstance(inner_poly, MultiPolygon):
                inner_poly = max(inner_poly.geoms, key=lambda g: g.area)
            if not isinstance(inner_poly, Polygon) or inner_poly.area < 1.0:
                inner_poly = parcel_utm
        except Exception:
            inner_poly = parcel_utm

        ring_utm = list(inner_poly.exterior.coords)[:-1]
        corners_utm_h: list[list] = []
        for pt in ring_utm:
            d = north_mls.distance(Point(pt[0], pt[1]))
            h = min(SLOPE * MAX_DEPTH_CAP_M, max(BASE_HEIGHT_M, d * SLOPE))
            corners_utm_h.append([pt[0], pt[1], h])

        corners_wgs = [[*_wgs_pt((c[0], c[1])), c[2]] for c in corners_utm_h]
        slanted_polygons.append({
            "corners": corners_wgs,
            "label": "정북일조 envelope (§86① H = max(10, d×2), 1.5m 이격 내부)",
            "kind": "slope",
        })

        min_h = min(c[2] for c in corners_utm_h)
        max_h = max(c[2] for c in corners_utm_h)
        thresholds.append({"distance_m": 0.0, "max_height_m": min_h, "kind": "vertical"})
        thresholds.append({"distance_m": MAX_DEPTH_CAP_M, "max_height_m": max_h,
                           "kind": "slope_top"})

        # 북쪽 수직벽: H≈10m 인접 쌍 → 바닥까지 내려오는 수직벽
        # (사용자 img_18: "직선→사선 올라가는 면" 유지)
        n = len(corners_utm_h)
        for i in range(n):
            c1 = corners_utm_h[i]
            c2 = corners_utm_h[(i + 1) % n]
            if (abs(c1[2] - BASE_HEIGHT_M) < 0.5
                    and abs(c2[2] - BASE_HEIGHT_M) < 0.5):
                walls.append({
                    "positions": [_wgs_pt((c1[0], c1[1])), _wgs_pt((c2[0], c2[1]))],
                    "min_heights": [0.0, 0.0],
                    "max_heights": [BASE_HEIGHT_M, BASE_HEIGHT_M],
                    "kind": "north_vertical",
                })
    except Exception as e:
        logger.warning(f"envelope from north boundary failed: {e}")


def _emit_profile_polylines(
    primary_edges: list[LineString],
    centroid: Point,
    profile_polylines: list,
) -> None:
    """2D 단면도용 프로파일 (수직→평탄→경사)."""
    for edge in primary_edges:
        nx, ny = _inward_normal(edge, centroid)
        if nx == 0.0 and ny == 0.0:
            continue
        if len(edge.coords) < 2:
            continue
        mid = edge.interpolate(0.5, normalized=True)
        mid_xy = (mid.x, mid.y)

        pts_utm_h = [
            (mid_xy[0] + nx * BASE_SETBACK_M, mid_xy[1] + ny * BASE_SETBACK_M, 0.0),
            (mid_xy[0] + nx * BASE_SETBACK_M, mid_xy[1] + ny * BASE_SETBACK_M, BASE_HEIGHT_M),
        ]
        if PLATEAU_END_M > BASE_SETBACK_M:
            pts_utm_h.append(
                (mid_xy[0] + nx * PLATEAU_END_M, mid_xy[1] + ny * PLATEAU_END_M, BASE_HEIGHT_M)
            )
        if MAX_DEPTH_CAP_M > PLATEAU_END_M:
            pts_utm_h.append(
                (mid_xy[0] + nx * MAX_DEPTH_CAP_M, mid_xy[1] + ny * MAX_DEPTH_CAP_M,
                 SLOPE * MAX_DEPTH_CAP_M)
            )
        pts_wgs_h = [[*_wgs_pt((p[0], p[1])), p[2]] for p in pts_utm_h]
        profile_polylines.append({
            "points": pts_wgs_h,
            "label": "단면 프로파일 (수직→평탄→경사)",
        })


def _emit_envelope_layers(
    north_edges: list[LineString],
    parcel_utm: Polygon,
    centroid: Point,
    envelope_layers: list,
) -> None:
    """적응형 계단식 envelope 층 (필지 크기에 따라 자동)."""
    candidate_heights = [10.0, 15.0, 20.0, 25.0, 30.0]
    kind_names = ["base", "mid", "high", "high2", "top"]
    h_bot = 0.0
    for i, h_top in enumerate(candidate_heights):
        if h_top > SLOPE * MAX_DEPTH_CAP_M + 0.01:
            break
        offset_req = max(BASE_SETBACK_M, h_top * 0.5)
        fp = _offset_north_edges_footprint(north_edges, parcel_utm, centroid, offset_req)
        if fp is None:
            break
        kind = kind_names[i] if i < len(kind_names) else "top"
        ring_wgs = [_wgs_pt(p) for p in fp.exterior.coords[:-1]]
        envelope_layers.append({
            "footprint_wgs": ring_wgs,
            "h_bottom": h_bot,
            "h_top": h_top,
            "offset_m": offset_req,
            "kind": kind,
            "label": f"H={h_bot:.0f}~{h_top:.0f}m (offset≥{offset_req:.1f}m)",
        })
        h_bot = h_top


def _offset_north_edges_footprint(
    north_edges: list[LineString],
    parcel_utm: Polygon,
    centroid: Point,
    offset_m: float,
) -> Polygon | None:
    """H 이하 층에서 건축 가능한 footprint (north half-plane ∩ parcel)."""
    if not north_edges:
        return None
    best_edge = None
    best_score = -1.0
    for edge in north_edges:
        nx, ny = _inward_normal(edge, centroid)
        if nx == 0.0 and ny == 0.0:
            continue
        score = edge.length * max(0.0, -ny)
        if score > best_score:
            best_score = score
            best_edge = (edge, nx, ny)
    if not best_edge:
        return None
    edge, nx, ny = best_edge
    coords_u = list(edge.coords)
    a, b = coords_u[0], coords_u[-1]
    big = 200.0
    hp_coords = [
        (a[0] + nx * offset_m, a[1] + ny * offset_m),
        (b[0] + nx * offset_m, b[1] + ny * offset_m),
        (b[0] + nx * big, b[1] + ny * big),
        (a[0] + nx * big, a[1] + ny * big),
    ]
    try:
        half = Polygon(hp_coords)
        if not half.is_valid:
            half = half.buffer(0)
        result = parcel_utm.intersection(half)
    except Exception:
        return None
    if result.is_empty:
        return None
    if isinstance(result, MultiPolygon):
        result = max(result.geoms, key=lambda g: g.area)
    if not isinstance(result, Polygon) or result.area < 1.0:
        return None
    return result
