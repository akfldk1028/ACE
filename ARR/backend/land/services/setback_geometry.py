"""
Setback Geometry — 필지 polygon + 규제 수치 → 규제선 GeoJSON 생성.

건축법 규제선 7종 중 6종 생성:
1. buildable_area: 건축가능영역 (인접이격 buffer)
2. north_setback: 정북 일조사선 (§61①, 령§86①)
3. adjacent_setback: 인접대지 이격선 (§58, 령§80조의2)
4. road_setback: 건축선 후퇴 (§46-47) — 최장변=도로 휴리스틱
5. corner_cutoff: 가각전제 (령§31) — 도로변 교차 삼각 클립
6. daylight_distance: 채광 인동간격 (§61②, 령§86③) — 매스 쌍 입력시

7. building_designation_line: 건축지정선/한계선 (지구단위계획 §49-52) — 도로변 기준 기본값
pyproj Transformer는 design/services/site_geometry.py와 동일 CRS지만
land↔design 의존성을 피하기 위해 독립 인스턴스 사용.
"""

import logging
import math

from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon, mapping, shape
from shapely.ops import transform
from pyproj import Transformer

logger = logging.getLogger(__name__)

# Korea UTM zone 52N
_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32652", always_xy=True)
_to_wgs = Transformer.from_crs("EPSG:32652", "EPSG:4326", always_xy=True)


def _wgs_to_utm(geom):
    return transform(_to_utm.transform, geom)


def _utm_to_wgs(geom):
    return transform(_to_wgs.transform, geom)


def compute_setback_lines(parcel_geojson: dict, regulations: dict) -> dict:
    """
    필지 polygon + 규제 수치 → 규제선 GeoJSON dict.

    Args:
        parcel_geojson: GeoJSON geometry (Polygon from Vworld)
        regulations: regulation_calculator.calculate_all() 결과

    Returns:
        {
            "buildable_area": GeoJSON polygon | None,
            "north_setback": GeoJSON LineString/MultiLineString | None,
            "adjacent_setback": GeoJSON LineString/MultiLineString | None,
            "road_setback": GeoJSON LineString/MultiLineString | None,
        }
    """
    result = {
        "buildable_area": None,
        "north_setback": None,
        "adjacent_setback": None,
        "road_setback": None,
        "corner_cutoff": None,                # 가각전제 삼각 클립
        "sunlight_envelope": None,            # 3D 일조사선 경사면 (wall vertices + heights)
        "building_designation_line": None,    # 건축지정선/한계선 (지구단위계획)
        "daylight_diagonal_envelope": None,   # 채광사선제한 3D (§86③, 공동주택)
    }

    # Validate geometry input
    if not isinstance(parcel_geojson, dict):
        return result
    if "type" not in parcel_geojson or "coordinates" not in parcel_geojson:
        return result

    try:
        parcel = shape(parcel_geojson)
        if not parcel.is_valid or parcel.is_empty:
            return result
        # MultiPolygon → 최대 면적 Polygon 추출
        if isinstance(parcel, MultiPolygon):
            parcel = max(parcel.geoms, key=lambda g: g.area)
        if not isinstance(parcel, Polygon):
            return result
        parcel_utm = _wgs_to_utm(parcel)
    except Exception as e:
        logger.warning(f"setback_geometry: parcel parse failed: {e}")
        return result

    adjacent_m = regulations.get("adjacent_setback_m") or 0.5
    road_setback_m = regulations.get("building_line_setback_m") or 1.0
    sunlight_applies = regulations.get("sunlight_applies", False)
    sunlight_rules = regulations.get("sunlight_rules", [])
    corner_cutoff_required = regulations.get("corner_cutoff_required", False)

    # Step 1: 건축가능영역 (일괄 buffer)
    result["buildable_area"] = _compute_buildable_area(parcel_utm, adjacent_m)

    # Step 2: 변별 규제선
    edges = _extract_edges(parcel_utm)
    if not edges:
        return result

    classified = _classify_edges(edges, parcel_utm)

    # 정북 일조사선 (2D multi-height lines + 3D envelope)
    if sunlight_applies and classified["north"]:
        result["north_setback"] = _compute_sunlight_setback_lines(
            classified["north"], parcel_utm, sunlight_rules,
        )
        result["sunlight_envelope"] = _compute_sunlight_envelope(
            classified["north"], parcel_utm, sunlight_rules,
        )

    # 인접대지 이격선
    if classified["adjacent"] and adjacent_m > 0:
        result["adjacent_setback"] = _offset_edges_inward(
            classified["adjacent"], parcel_utm, adjacent_m,
        )

    # 도로변 건축선 후퇴 (§46-47)
    if classified["road"] and road_setback_m > 0:
        result["road_setback"] = _offset_edges_inward(
            classified["road"], parcel_utm, road_setback_m,
        )

    # 가각전제 (령§31): 도로변 교차 꼭짓점에서 삼각 클립
    # cutoff_m: 조례/zone override 또는 도로폭 기반 동적 계산
    corner_cutoff_m = regulations.get("corner_cutoff_m")  # None = 동적 계산
    if corner_cutoff_required and classified["road"]:
        result["corner_cutoff"] = _compute_corner_cutoff(
            classified["road"], parcel_utm, cutoff_m=corner_cutoff_m,
        )

    # 건축지정선/한계선 (국토계획법 §49-52): 지구단위계획구역 도로변 기준
    designation_applies = regulations.get("building_designation_applies", False)
    designation_setback = regulations.get("building_designation_setback_m")
    if designation_applies and classified["road"] and designation_setback and designation_setback > 0:
        result["building_designation_line"] = _offset_edges_inward(
            classified["road"], parcel_utm, designation_setback,
        )

    # 채광사선제한 3D 경사면 (시행령 §86③): 공동주택, 인접경계선에서 H ≤ 거리 × mult
    daylight_mult = regulations.get("daylight_diagonal_multiplier")
    if daylight_mult and classified["adjacent"]:
        result["daylight_diagonal_envelope"] = _compute_daylight_diagonal_envelope(
            classified["adjacent"], parcel_utm, daylight_mult,
        )

    return result


def _compute_buildable_area(parcel_utm: Polygon, setback_m: float) -> dict | None:
    """필지 → buffer(-setback) → 건축가능영역 GeoJSON."""
    try:
        buildable = parcel_utm.buffer(-setback_m)
        if buildable.is_empty or buildable.area < 1.0:
            return None
        # buffer can produce MultiPolygon on concave shapes → take largest
        if isinstance(buildable, MultiPolygon):
            buildable = max(buildable.geoms, key=lambda g: g.area)
        buildable_wgs = _utm_to_wgs(buildable)
        return mapping(buildable_wgs)
    except Exception as e:
        logger.warning(f"buildable_area failed: {e}")
        return None


def _extract_edges(polygon_utm: Polygon) -> list[tuple]:
    """Polygon 외곽선 → [(LineString, azimuth)] 리스트."""
    coords = list(polygon_utm.exterior.coords)
    edges = []
    for i in range(len(coords) - 1):
        p1 = coords[i]
        p2 = coords[i + 1]
        line = LineString([p1, p2])
        if line.length < 0.1:
            continue
        az = _azimuth(p1, p2)
        edges.append((line, az))
    return edges


def _inward_normal(edge: LineString, centroid: Point) -> tuple[float, float]:
    """Compute unit inward-pointing normal of an edge relative to polygon centroid."""
    dx = edge.coords[1][0] - edge.coords[0][0]
    dy = edge.coords[1][1] - edge.coords[0][1]
    length = math.sqrt(dx * dx + dy * dy)
    if length < 0.01:
        return (0.0, 0.0)
    # Left-turn normal
    nx = -dy / length
    ny = dx / length
    # Flip to point inward (toward centroid)
    mid = edge.interpolate(0.5, normalized=True)
    to_cx = centroid.x - mid.x
    to_cy = centroid.y - mid.y
    if nx * to_cx + ny * to_cy < 0:
        nx, ny = -nx, -ny
    return (nx, ny)


def _azimuth(p1: tuple, p2: tuple) -> float:
    """두 점 사이 방위각 (0=북, 90=동, 180=남, 270=서). UTM 좌표 기준."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    az = math.degrees(math.atan2(dx, dy)) % 360
    return az


def _classify_edges(edges: list[tuple], parcel_utm: Polygon) -> dict:
    """
    변의 바깥쪽 법선 방향으로 분류:
    - north: 바깥 법선이 정북(y+) 방향인 변 → 일조사선 적용
      법선 방위각 300°~60° (정북 ±60°)
      건축법 §61①: "정북(正北) 방향으로의 인접 대지경계선"
      NOTE: UTM Zone 52N의 Grid North ≈ True North (한국 중부 자오선 수렴각 <0.5°)
    - road: 최장변 1개 (한국 필지 관행: 전면도로 = 가장 긴 변).
      코너 필지면 최장변과 꼭지점을 공유하는 인접 변 중 최장변 70% 이상 길이의 변도 도로변.
      **최대 2개로 제한** (정사각형 필지가 전부 road 되는 버그 방지).
    - adjacent: 나머지 (인접대지) — 항상 최소 1개 이상 보존.
    """
    classified = {"north": [], "road": [], "adjacent": []}

    if not edges:
        return classified

    centroid = parcel_utm.centroid

    # ── 1단계: 모든 변에 대해 북향 판정 + 바깥 법선 계산
    edge_meta = []
    for line, az in edges:
        dx = line.coords[1][0] - line.coords[0][0]
        dy = line.coords[1][1] - line.coords[0][1]
        length = math.sqrt(dx * dx + dy * dy)
        if length < 0.01:
            continue

        nx = -dy / length
        ny = dx / length
        mid = line.interpolate(0.5, normalized=True)
        to_center_x = centroid.x - mid.x
        to_center_y = centroid.y - mid.y
        if nx * to_center_x + ny * to_center_y > 0:
            nx, ny = -nx, -ny
        normal_az = math.degrees(math.atan2(nx, ny)) % 360
        is_north_facing = normal_az >= 300 or normal_az <= 60
        edge_meta.append((line, line.length, is_north_facing))

    if not edge_meta:
        return classified

    # ── 2단계: 도로변 선정 (최장변 1개 + 선택적 코너 1개, 최대 2개)
    edge_meta.sort(key=lambda m: -m[1])  # 긴 순
    longest_line = edge_meta[0][0]
    max_length = edge_meta[0][1]
    road_threshold = max_length * 0.70
    road_lines = [longest_line]

    # 두번째 도로 후보: 최장변과 꼭지점 공유 + 길이 ≥ 70%
    for m in edge_meta[1:]:
        cand, length, _ = m
        if length < road_threshold:
            break
        # 꼭지점 공유 체크
        ep_long = {longest_line.coords[0], longest_line.coords[1]}
        ep_cand = {cand.coords[0], cand.coords[1]}
        if ep_long & ep_cand:
            road_lines.append(cand)
            break  # 최대 2개

    # ── 3단계: 분류 (road 우선, 나머지는 북향 or 인접)
    road_set = {id(l) for l in road_lines}
    for line, _, is_north_facing in edge_meta:
        if id(line) in road_set:
            classified["road"].append(line)
            if is_north_facing:
                classified["north"].append(line)
        elif is_north_facing:
            classified["north"].append(line)
        else:
            classified["adjacent"].append(line)

    # ── 방어: adjacent가 하나도 없으면 (극히 작은 필지) 도로 아닌 모든 변 복귀
    if not classified["adjacent"] and len(edge_meta) > len(road_lines):
        for line, _, _ in edge_meta:
            if id(line) not in road_set and line not in classified["north"]:
                classified["adjacent"].append(line)

    return classified


def _sunlight_offset(sunlight_rules: list) -> float:
    """
    일조사선 규칙에서 기본 이격거리 산출.

    건축법 시행령 §86①제1호 (2023.9.12 개정):
    - H ≤ 10m: 1.5m 이상 이격 (개정 전 9m)
    - H > 10m: H/2 이상 이격

    높이 미정이므로 기본값 1.5m (10m 이하 건물 기준).
    sunlight_rules에 setback_m 있으면 최대값 사용.
    """
    if not sunlight_rules:
        return 1.5

    max_setback = 1.5
    for rule in sunlight_rules:
        if isinstance(rule, dict):
            sb = rule.get("setback_m")
            if sb is not None and isinstance(sb, (int, float)):
                max_setback = max(max_setback, sb)
    return max_setback


def _compute_sunlight_setback_lines(
    north_edges: list[LineString],
    parcel_utm: Polygon,
    sunlight_rules: list,
) -> dict | None:
    """
    정북일조 사선을 높이별로 여러 선 생성 → GeoJSON FeatureCollection.

    건축법 시행령 §86①:
    - H ≤ 10m: 1.5m 이격
    - H > 10m: H/2 이격

    여러 높이(10m, 20m, 30m, 40m)에 대해 사선 위치를 표시하면
    지도에서 사선 범위가 명확하게 보임.

    모든 선은 필지 polygon 내부로 클리핑됨.
    """
    # 높이별 (높이, 이격거리, 라벨)
    height_steps = [
        (10, 1.5, "H=10m → 1.5m"),
        (20, 10.0, "H=20m → 10m"),
        (30, 15.0, "H=30m → 15m"),
        (40, 20.0, "H=40m → 20m"),
    ]

    centroid = parcel_utm.centroid
    features = []

    for height_m, offset_m, label in height_steps:
        lines_for_height = []
        for edge in north_edges:
            nx, ny = _inward_normal(edge, centroid)
            if nx == 0.0 and ny == 0.0:
                continue
            offset_coords = [
                (c[0] + nx * offset_m, c[1] + ny * offset_m)
                for c in edge.coords
            ]
            line = LineString(offset_coords)
            # 필지 내부로 클리핑 — 밖으로 돌출 방지
            clipped = line.intersection(parcel_utm)
            if clipped.is_empty:
                continue
            if isinstance(clipped, (LineString, MultiLineString)) and clipped.length > 0.1:
                lines_for_height.append(clipped)

        if not lines_for_height:
            continue

        if len(lines_for_height) == 1:
            geom = lines_for_height[0]
        else:
            all_lines = []
            for g in lines_for_height:
                if isinstance(g, MultiLineString):
                    all_lines.extend(g.geoms)
                else:
                    all_lines.append(g)
            geom = MultiLineString(all_lines) if len(all_lines) > 1 else all_lines[0]

        geom_wgs = _utm_to_wgs(geom)
        features.append({
            "type": "Feature",
            "properties": {
                "height_m": height_m,
                "offset_m": offset_m,
                "label": label,
            },
            "geometry": mapping(geom_wgs),
        })

    if not features:
        return None

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def _offset_edges_inward(
    edges: list[LineString],
    parcel_utm: Polygon,
    distance: float,
) -> dict | None:
    """
    변들을 필지 안쪽으로 offset → GeoJSON LineString/MultiLineString.

    각 변을 법선(normal) 방향으로 inward offset.
    """
    try:
        offset_lines = []
        centroid = parcel_utm.centroid

        for edge in edges:
            nx, ny = _inward_normal(edge, centroid)
            if nx == 0.0 and ny == 0.0:
                continue

            # offset 적용
            offset_coords = [
                (c[0] + nx * distance, c[1] + ny * distance)
                for c in edge.coords
            ]
            offset_line = LineString(offset_coords)
            if not offset_line.is_empty and offset_line.length > 0.1:
                offset_lines.append(offset_line)

        if not offset_lines:
            return None

        if len(offset_lines) == 1:
            result_geom = _utm_to_wgs(offset_lines[0])
        else:
            result_geom = _utm_to_wgs(MultiLineString(offset_lines))

        return mapping(result_geom)

    except Exception as e:
        logger.warning(f"offset_edges_inward failed: {e}")
        return None


def _compute_sunlight_envelope(
    north_edges: list[LineString],
    parcel_utm: Polygon,
    sunlight_rules: list,
) -> dict | None:
    """
    정북 일조사선 3D 경사면 생성 (건축법 시행령 §86①, 2023.9.12 개정).

    법규 단면 (북측 경계에서 남쪽으로 x 진행):
        H (m)
        |                            /     ← slope 2:1 (H = 2x, 연속 경사면)
        |                          /
        |                        /
        | 10 ────┐──────────────         ← 수평 평탄부 (x=1.5 ~ 5m)
        |        │
        |        │                      ← 수직 직각벽 (x=1.5m, H=0→10m)
        |        │
        | 0 ─────┴──────────────────→ x
             0  1.5  5m    inward

    렌더 구성 (Cesium primitive 3종):
    1. **수직 직각벽** (Wall): x=1.5m, H=0→10m — 법규의 "10m까지 직각"
    2. **수평 평탄부** (Polygon, flat at H=10m): x=1.5m ~ 5m 직사각형 지붕
    3. **경사면** (Polygon w/ perPositionHeight=true): x=5m~max 로 기울어진 사각형
       내측이 높고 경계쪽이 낮은 **진짜 slanted 지붕** — 계단 아님.

    Returns: {
        walls: [...],           # 수직 벽 (Cesium Wall primitive)
        slanted_polygons: [...],# 연속 경사면 (Cesium Polygon + perPositionHeight)
        slope, base_setback_m, base_height_m, max_depth_m,
        thresholds: [...]
    }
    """
    try:
        if not north_edges:
            return None

        centroid = parcel_utm.centroid
        base_setback = 1.5   # 수직벽 이격 (m) — §86①제1호
        base_height = 10.0   # 수직벽 최대 높이 (m) — 2023.9.12 개정 9→10m
        slope = 2.0          # 경사면 기울기 H=2x (§86①제2호 "H/2 이격"의 역수)

        # 사선은 법규 시각화용 — 필지 밖까지 길게 이어져도 괜찮음 (개념적 선).
        # 고정 값 사용: slope가 H=50m까지 올라가도록 max_depth=25m.
        #   plateau_end=5m (H=10m) → max_depth=25m (H=50m, slope 2:1)
        max_depth_cap = 25.0
        plateau_end = 5.0  # §86① H=10m 평탄 끝

        walls = []
        slanted_polygons = []
        thresholds = []

        def _offset_coord(coord, nx, ny, dist):
            return (coord[0] + nx * dist, coord[1] + ny * dist)

        def _wgs_pt(utm_pt):
            wgs = _utm_to_wgs(Point(utm_pt[0], utm_pt[1]))
            return [wgs.x, wgs.y]

        def _clip_to_parcel(corners_utm_h: list[list]) -> list[list] | None:
            """
            2D 외곽선 (corners의 x,y만)을 필지에 clip.
            기존 corners의 h 값을 barycentric-like하게 interpolate.
            polygon이 너무 작거나 필지 밖이면 None.
            """
            ring = [(c[0], c[1]) for c in corners_utm_h]
            try:
                poly2d = Polygon(ring)
                if not poly2d.is_valid:
                    poly2d = poly2d.buffer(0)
                clipped = poly2d.intersection(parcel_utm)
            except Exception:
                return None
            if clipped.is_empty:
                return None
            if isinstance(clipped, MultiPolygon):
                clipped = max(clipped.geoms, key=lambda g: g.area)
            if not isinstance(clipped, Polygon) or clipped.area < 1.0:
                return None

            # 원 polygon이 2 high-height corners + 2 low-height corners인 기울어진 사각형.
            # clipped polygon의 각 vertex에 대해 "두 원본 low-height 코너가 이루는 edge로부터의
            # 거리 비율"을 기준으로 높이 보간.
            low_h = min(c[2] for c in corners_utm_h)
            high_h = max(c[2] for c in corners_utm_h)
            if abs(high_h - low_h) < 0.01:
                # 평탄 polygon — 그냥 같은 높이 유지
                return [[x, y, low_h] for (x, y) in clipped.exterior.coords[:-1]]

            # 기울기 방향: low → high 벡터 (원 corners에서 low와 high 중점 간)
            low_pts = [(c[0], c[1]) for c in corners_utm_h if abs(c[2] - low_h) < 0.01]
            high_pts = [(c[0], c[1]) for c in corners_utm_h if abs(c[2] - high_h) < 0.01]
            if not low_pts or not high_pts:
                return [[x, y, low_h] for (x, y) in clipped.exterior.coords[:-1]]
            low_cx = sum(p[0] for p in low_pts) / len(low_pts)
            low_cy = sum(p[1] for p in low_pts) / len(low_pts)
            high_cx = sum(p[0] for p in high_pts) / len(high_pts)
            high_cy = sum(p[1] for p in high_pts) / len(high_pts)
            dx = high_cx - low_cx
            dy = high_cy - low_cy
            span_sq = dx * dx + dy * dy
            if span_sq < 1e-6:
                return [[x, y, low_h] for (x, y) in clipped.exterior.coords[:-1]]

            out = []
            for (x, y) in list(clipped.exterior.coords)[:-1]:
                # projection of (x-low_cx, y-low_cy) onto (dx, dy) / span = t in [0,1]
                t = ((x - low_cx) * dx + (y - low_cy) * dy) / span_sq
                t = max(0.0, min(1.0, t))
                h = low_h + t * (high_h - low_h)
                out.append([x, y, h])
            return out

        # 시각 혼란 방지: 여러 north edge 중 '가장 대표적인 북쪽 경계' 1개만 사용.
        # 기준: edge.length × max(0, -ny) (길고 남쪽향 법선 가진 edge)
        def _pick_primary_edge(edges: list) -> tuple | None:
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

        primary = _pick_primary_edge(north_edges)
        primary_edges = [primary[0]] if primary else []

        # ── shapely buffer 기반 재설계 ──
        # 개별 edge offset은 convex/concave 꼭지점에서 parcel 밖으로 튀어나가는 버그.
        # 대신 parcel polygon 자체를 buffer(-dist)로 inset하면 모든 꼭지점이 parcel 내부 보장.
        #
        # 1. buffer(-1.5m) = 인접이격 1.5m 들어간 polygon (수직벽 위치)
        # 2. buffer(-5m)   = 평탄 끝 polygon (H=10m 수평 끝)
        # 3. 둘의 차집합 = plateau 영역 (annulus, 가로 3.5m 고리)
        # 4. slope polygon = primary edge의 외측 방향으로 x=5m→25m 사각형
        #    (사선은 필지 밖까지 이어져도 OK)
        try:
            inset_base = parcel_utm.buffer(-base_setback)
            inset_plat = parcel_utm.buffer(-plateau_end)
        except Exception as e:
            logger.warning(f"buffer failed: {e}")
            inset_base = None
            inset_plat = None

        for edge in primary_edges:
            nx, ny = _inward_normal(edge, centroid)
            if nx == 0.0 and ny == 0.0:
                continue
            coords_utm = list(edge.coords)
            if len(coords_utm) < 2:
                continue
            a_utm, b_utm = coords_utm[0], coords_utm[-1]

            # ── 1. 수직 직각벽 — inset_base polygon 중 primary edge에 평행한 부분만 ──
            # 단순화: primary edge를 base_setback 만큼 inward offset한 선을 Cesium Wall로.
            # buffer 사용하면 parcel 꼭지점 둥글려지므로 edge 직선 offset이 더 법규 충실.
            vert_utm = [_offset_coord(c, nx, ny, base_setback) for c in coords_utm]
            # parcel 내부로 clip (LineString 교차)
            vert_line = LineString(vert_utm)
            clipped_vert = vert_line.intersection(parcel_utm)
            if not clipped_vert.is_empty:
                if hasattr(clipped_vert, 'geoms'):
                    clipped_vert = max(clipped_vert.geoms, key=lambda g: g.length)
                if isinstance(clipped_vert, LineString):
                    vert_coords = list(clipped_vert.coords)
                else:
                    vert_coords = vert_utm
            else:
                vert_coords = vert_utm
            walls.append({
                "positions": [_wgs_pt(p) for p in vert_coords],
                "min_heights": [0.0] * len(vert_coords),
                "max_heights": [base_height] * len(vert_coords),
                "label": f"수직 직각벽 (x={base_setback}m, H=0→{base_height}m)",
            })
            thresholds.append({"distance_m": base_setback, "max_height_m": base_height,
                                "kind": "vertical"})

            # ── 2. 평탄 지붕 — inset_base ∖ inset_plat = annulus ──
            if inset_base is not None and not inset_base.is_empty:
                if inset_plat is not None and not inset_plat.is_empty:
                    plat_ring = inset_base.difference(inset_plat)
                else:
                    plat_ring = inset_base
                if plat_ring.area >= 1.0:
                    # take exterior ring of outermost poly
                    if isinstance(plat_ring, MultiPolygon):
                        plat_ring = max(plat_ring.geoms, key=lambda g: g.area)
                    if isinstance(plat_ring, Polygon):
                        corners_wgs = [
                            [*_wgs_pt((pt[0], pt[1])), base_height]
                            for pt in list(plat_ring.exterior.coords)[:-1]
                        ]
                        slanted_polygons.append({
                            "corners": corners_wgs,
                            "label": f"평탄 지붕 (x={base_setback}~{plateau_end}m, H={base_height}m)",
                            "kind": "plateau",
                        })
                        thresholds.append({"distance_m": plateau_end,
                                            "max_height_m": base_height,
                                            "kind": "plateau_end"})

            # ── 3. 경사 지붕 — primary edge 기준 사각형 (필지 밖까지 이어짐) ──
            if max_depth_cap > plateau_end:
                h_top = slope * max_depth_cap
                slope_utm_h = [
                    [*_offset_coord(a_utm, nx, ny, plateau_end), base_height],
                    [*_offset_coord(b_utm, nx, ny, plateau_end), base_height],
                    [*_offset_coord(b_utm, nx, ny, max_depth_cap), h_top],
                    [*_offset_coord(a_utm, nx, ny, max_depth_cap), h_top],
                ]
                corners_wgs = [[*_wgs_pt((c[0], c[1])), c[2]] for c in slope_utm_h]
                slanted_polygons.append({
                    "corners": corners_wgs,
                    "label": f"경사 지붕 slope 2:1 (x={plateau_end}~{max_depth_cap:.1f}m, "
                              f"H={base_height}→{h_top:.1f}m)",
                    "kind": "slope",
                })
                thresholds.append({"distance_m": max_depth_cap, "max_height_m": h_top,
                                    "kind": "slope_top"})

        # ── 4. 프로파일 폴리라인 — 대표 edge 중앙 1개만 (혼란 방지)
        # 법규 img_5의 빨간 점선에 대응 (수직→평탄→경사)
        profile_polylines = []
        for edge in primary_edges:
            nx, ny = _inward_normal(edge, centroid)
            if nx == 0.0 and ny == 0.0:
                continue
            coords_utm = list(edge.coords)
            if len(coords_utm) < 2:
                continue
            # edge 중간점에서 내측으로 프로파일 그리기
            mid = edge.interpolate(0.5, normalized=True)
            mid_xy = (mid.x, mid.y)
            pts_utm_h = [
                (mid_xy[0] + nx * base_setback, mid_xy[1] + ny * base_setback, 0.0),
                (mid_xy[0] + nx * base_setback, mid_xy[1] + ny * base_setback, base_height),
            ]
            if plateau_end > base_setback:
                pts_utm_h.append(
                    (mid_xy[0] + nx * plateau_end, mid_xy[1] + ny * plateau_end, base_height)
                )
            if max_depth_cap > plateau_end:
                pts_utm_h.append(
                    (mid_xy[0] + nx * max_depth_cap, mid_xy[1] + ny * max_depth_cap,
                     slope * max_depth_cap)
                )
            pts_wgs_h = [[*_wgs_pt((p[0], p[1])), p[2]] for p in pts_utm_h]
            profile_polylines.append({
                "points": pts_wgs_h,
                "label": "단면 프로파일 (수직→평탄→경사)",
            })

        # ── 5. 계단식 envelope 층 — img_5의 건물 볼륨 시각화
        # 각 height 레이어에서 필지의 "건축 가능 footprint"를 계산해 extruded polygon.
        # 누적하면 img_5처럼 stepped building profile이 보임.
        envelope_layers = []

        def _offset_north_edges_buffer(offset_m: float):
            """
            'H 이하에서 건축 가능한 footprint' 반환.
            가장 "북향"에 가까운 edge 1개를 기준으로 half-plane intersect.
            복수 north edge가 있어도 over-constrain하지 않도록 대표 1개 사용.
            """
            if not north_edges:
                return None
            # 대표 edge: '길이가 길고 inward가 남쪽'에 가장 잘 맞는 edge.
            # 짧은 북향 edge 1개만 쓰면 half-plane이 필지의 작은 귀퉁이만 덮음.
            best_edge = None
            best_score = -1.0
            for edge in north_edges:
                nx, ny = _inward_normal(edge, centroid)
                if nx == 0.0 and ny == 0.0:
                    continue
                # score = edge.length × (inward가 남향인 정도, -ny clamped 0~1)
                north_weight = max(0.0, -ny)
                score = edge.length * north_weight
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
                (b[0] + nx * big,      b[1] + ny * big),
                (a[0] + nx * big,      a[1] + ny * big),
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

        # 법규 §86① 기준 적응형 레이어. 필지 크기에 따라 몇 개 층이 fit할지 자동 결정.
        # 각 층 h_top에 필요한 offset = max(1.5m, h_top × 0.5)
        # 필지가 작으면 위 층이 자동으로 생략됨.
        candidate_heights = [10.0, 15.0, 20.0, 25.0, 30.0]
        h_bot = 0.0
        prev_offset = base_setback
        kind_names = ["base", "mid", "high", "high2", "top"]
        for i, h_top in enumerate(candidate_heights):
            if h_top > slope * max_depth_cap + 0.01:
                break
            offset_req = max(base_setback, h_top * 0.5)
            fp = _offset_north_edges_buffer(offset_req)
            if fp is None:
                break  # 이 층부터는 필지에 fit 안 됨
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
            prev_offset = offset_req

        # Use cap value to satisfy later return structure.
        max_depth = max_depth_cap

        if not walls and not slanted_polygons and not envelope_layers:
            return None

        return {
            "walls": walls,
            "slanted_polygons": slanted_polygons,
            "profile_polylines": profile_polylines,
            "envelope_layers": envelope_layers,
            "slope": slope,
            "base_setback_m": base_setback,
            "base_height_m": base_height,
            "max_depth_m": max_depth,
            "thresholds": thresholds,
            "law_basis": "건축법 §61①, 시행령 §86① (2023.9.12 개정 9→10m)",
        }

    except Exception as e:
        logger.warning(f"sunlight_envelope failed: {e}")
        return None


# ---------------------------------------------------------------------------
# 3b. 도로사선제한 3D 경사면 (시행령 §82)
# ---------------------------------------------------------------------------

def _compute_daylight_diagonal_envelope(
    adjacent_edges: list[LineString],
    parcel_utm: Polygon,
    multiplier: float,
) -> dict | None:
    """
    채광사선제한 3D 경사면 생성.

    건축법 §61②, 시행령 §86③:
    - 공동주택 채광창 → 인접대지경계선 수평거리 × multiplier 이하
    - 일반: multiplier=2, 근린상업/준주거: multiplier=4

    인접경계선에서 안쪽으로 경사면:
    - 경계선: H = 0
    - 안쪽 d미터: H = d × multiplier

    구간별 별도 wall. max_depth = 필지 폭의 절반으로 제한 (밖으로 안 나감).

    Returns: {"walls": [...], "multiplier": float} or None
    """
    try:
        if not adjacent_edges:
            return None

        centroid = parcel_utm.centroid
        # 필지 크기 기반 max_depth (밖으로 돌출 방지)
        bounds = parcel_utm.bounds  # (minx, miny, maxx, maxy)
        parcel_span = min(bounds[2] - bounds[0], bounds[3] - bounds[1])
        # 시각화 보수적: 필지 최소 차원 40% 또는 12m cap (이전 30m는 너무 큼)
        max_depth = min(parcel_span * 0.4, 12.0)
        if max_depth < 3.0:
            return None
        depth_pairs = [(0.0, max_depth * 0.5), (max_depth * 0.5, max_depth)]
        walls = []

        for edge in adjacent_edges:
            nx, ny = _inward_normal(edge, centroid)
            if nx == 0.0 and ny == 0.0:
                continue

            edge_coords = list(edge.coords)

            for d_start, d_end in depth_pairs:
                h_start = d_start * multiplier
                h_end = d_end * multiplier

                # 사각형: edge@d_start → edge@d_end (sunlight wall 패턴)
                positions = []
                min_h = []
                max_h = []

                # edge 양 끝점 at d_start
                for coord in edge_coords:
                    positions.append((
                        coord[0] + nx * d_start,
                        coord[1] + ny * d_start,
                    ))
                    min_h.append(0.0)
                    max_h.append(h_start)

                # edge 양 끝점 at d_end (역순으로 사각형 닫기)
                for coord in reversed(edge_coords):
                    positions.append((
                        coord[0] + nx * d_end,
                        coord[1] + ny * d_end,
                    ))
                    min_h.append(0.0)
                    max_h.append(h_end)

                # UTM → WGS84
                positions_wgs = []
                for pt in positions:
                    wgs_pt = _utm_to_wgs(Point(pt[0], pt[1]))
                    positions_wgs.append([wgs_pt.x, wgs_pt.y])

                walls.append({
                    "positions": positions_wgs,
                    "min_heights": min_h,
                    "max_heights": max_h,
                })

        if not walls:
            return None

        return {
            "walls": walls,
            "multiplier": multiplier,
            "max_depth_m": max_depth,
        }

    except Exception as e:
        logger.warning(f"daylight_diagonal_envelope failed: {e}")
        return None


# ---------------------------------------------------------------------------
# 4. 가각전제 (령§31) — 도로변 교차 꼭짓점 삼각 클립
# ---------------------------------------------------------------------------

def _compute_corner_cutoff(
    road_edges: list[LineString],
    parcel_utm: Polygon,
    cutoff_m: float | None = None,
) -> dict | None:
    """
    가각전제: 두 도로변이 만나는 꼭짓점에서 삼각형 잘라내기.

    건축법 시행령 §31: 너비 8m 미만 도로 교차부.
    도로폭/교차각에 따라 절삭 거리 차등 적용:
      교차각 < 90°: 6~8m도로=4m, 4~6m도로=3m
      90~120°: 6~8m도로=3m, 4~6m도로=2m
      ≥ 120°: 적용 안 함

    Args:
        road_edges: 도로변으로 분류된 LineString 리스트
        parcel_utm: UTM 투영 필지 Polygon
        cutoff_m: 조례 override 절삭 길이. None이면 교차각 기반 동적 계산.

    Returns:
        GeoJSON Polygon (잘린 삼각형 영역) or None
    """
    if len(road_edges) < 2:
        return None

    try:
        # 도로변들의 끝점 공유 → 교차 꼭짓점 찾기
        corners = []
        for i in range(len(road_edges)):
            for j in range(i + 1, len(road_edges)):
                shared = _find_shared_vertex(road_edges[i], road_edges[j])
                if shared:
                    corners.append((shared, road_edges[i], road_edges[j]))

        if not corners:
            return None

        triangles = []
        for corner_pt, edge_a, edge_b in corners:
            # 교차각 기반 절삭 거리 계산 (조례 override 없을 때)
            actual_cutoff = cutoff_m if cutoff_m is not None else _corner_cutoff_by_angle(edge_a, edge_b, corner_pt)
            if actual_cutoff <= 0:
                continue
            pt_a = _point_along_edge_from(edge_a, corner_pt, actual_cutoff)
            pt_b = _point_along_edge_from(edge_b, corner_pt, actual_cutoff)
            if pt_a and pt_b:
                tri = Polygon([corner_pt, pt_a, pt_b, corner_pt])
                if tri.is_valid and tri.area > 0.01:
                    triangles.append(tri)

        if not triangles:
            return None

        # 삼각형들을 합쳐서 반환
        from shapely.ops import unary_union
        merged = unary_union(triangles)
        merged_wgs = _utm_to_wgs(merged)
        return mapping(merged_wgs)

    except Exception as e:
        logger.warning(f"corner_cutoff failed: {e}")
        return None


def _corner_cutoff_by_angle(
    edge_a: LineString, edge_b: LineString, shared_vertex: tuple | None = None,
) -> float:
    """
    시행령 §31 교차각 기반 가각전제 절삭 거리 (m).

    | 교차각   | 절삭 거리 |
    |---------|----------|
    | < 90°   | 3m       |
    | 90~120° | 2m       |
    | ≥ 120°  | 0 (없음)  |
    """
    # Orient vectors AWAY from shared vertex for correct angle
    if shared_vertex:
        sx, sy = shared_vertex
        # Pick the endpoint of each edge that is NOT the shared vertex
        d0a = (edge_a.coords[0][0] - sx) ** 2 + (edge_a.coords[0][1] - sy) ** 2
        d1a = (edge_a.coords[1][0] - sx) ** 2 + (edge_a.coords[1][1] - sy) ** 2
        if d0a < d1a:
            dx_a = edge_a.coords[1][0] - sx
            dy_a = edge_a.coords[1][1] - sy
        else:
            dx_a = edge_a.coords[0][0] - sx
            dy_a = edge_a.coords[0][1] - sy

        d0b = (edge_b.coords[0][0] - sx) ** 2 + (edge_b.coords[0][1] - sy) ** 2
        d1b = (edge_b.coords[1][0] - sx) ** 2 + (edge_b.coords[1][1] - sy) ** 2
        if d0b < d1b:
            dx_b = edge_b.coords[1][0] - sx
            dy_b = edge_b.coords[1][1] - sy
        else:
            dx_b = edge_b.coords[0][0] - sx
            dy_b = edge_b.coords[0][1] - sy
    else:
        dx_a = edge_a.coords[1][0] - edge_a.coords[0][0]
        dy_a = edge_a.coords[1][1] - edge_a.coords[0][1]
        dx_b = edge_b.coords[1][0] - edge_b.coords[0][0]
        dy_b = edge_b.coords[1][1] - edge_b.coords[0][1]

    len_a = math.sqrt(dx_a * dx_a + dy_a * dy_a)
    len_b = math.sqrt(dx_b * dx_b + dy_b * dy_b)
    if len_a < 0.01 or len_b < 0.01:
        return 3.0

    # Interior angle between vectors pointing away from shared vertex
    cos_angle = (dx_a * dx_b + dy_a * dy_b) / (len_a * len_b)
    cos_angle = min(1.0, max(-1.0, cos_angle))
    angle_deg = math.degrees(math.acos(cos_angle))

    if angle_deg >= 120:
        return 0.0  # 120° 이상: 가각전제 불필요
    elif angle_deg >= 90:
        return 2.0  # 90~120°: 보수적 2m
    else:
        return 3.0  # 90° 미만: 보수적 3m


def _find_shared_vertex(
    edge_a: LineString, edge_b: LineString, tolerance: float = 0.5,
) -> tuple | None:
    """두 LineString이 공유하는 꼭짓점 찾기 (tolerance 이내)."""
    for pa in edge_a.coords:
        for pb in edge_b.coords:
            dist = math.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
            if dist < tolerance:
                return ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
    return None


def _point_along_edge_from(
    edge: LineString, start_pt: tuple, distance: float,
) -> tuple | None:
    """edge 위에서 start_pt로부터 distance(m)만큼 떨어진 점 반환."""
    coords = list(edge.coords)
    # start_pt에 가까운 쪽이 시작점
    d0 = math.sqrt((coords[0][0] - start_pt[0]) ** 2 + (coords[0][1] - start_pt[1]) ** 2)
    d1 = math.sqrt((coords[-1][0] - start_pt[0]) ** 2 + (coords[-1][1] - start_pt[1]) ** 2)
    if d1 < d0:
        coords = list(reversed(coords))

    # 시작점에서 distance만큼 이동
    remaining = distance
    for i in range(len(coords) - 1):
        seg_len = math.sqrt(
            (coords[i + 1][0] - coords[i][0]) ** 2 +
            (coords[i + 1][1] - coords[i][1]) ** 2,
        )
        if seg_len < 0.001:
            continue
        if remaining <= seg_len:
            ratio = remaining / seg_len
            return (
                coords[i][0] + ratio * (coords[i + 1][0] - coords[i][0]),
                coords[i][1] + ratio * (coords[i + 1][1] - coords[i][1]),
            )
        remaining -= seg_len

    return None


# ---------------------------------------------------------------------------
# 5. 채광 인동간격 (§61②, 령§86③) — 매스 쌍 입력시
# ---------------------------------------------------------------------------

def compute_daylight_distance(
    building_a: dict,
    building_b: dict,
    is_urban_living: bool = False,
    footprint_a: dict | None = None,
    footprint_b: dict | None = None,
) -> dict:
    """
    두 건물 매스 간 채광 인동간격 검증.

    건축법 §61②, 시행령 §86③:
    - 같은 대지 내 공동주택 동 간: H × 0.5 이상 (일반)
    - 도시형 생활주택: H × 0.25 이상
    - 인접대지경계선 방향: 채광창~경계선 수평거리 × 2 이하 높이

    Args:
        building_a: {"height": float, "centroid": [x, y] (WGS84)}
        building_b: {"height": float, "centroid": [x, y] (WGS84)}
        is_urban_living: 도시형 생활주택 ���부

    Returns:
        {
            "distance_m": float,     # 두 동 간 실제 거리
            "required_m": float,     # 최소 이격거리
            "ratio": float,          # 이격비 (H 대비)
            "compliant": bool,       # 기준 충족 여부
            "taller_height_m": float,
            "formula": str,
        }
    """
    h_a = building_a.get("height", 0)
    h_b = building_b.get("height", 0)
    taller = max(h_a, h_b)

    multiplier = 0.25 if is_urban_living else 0.5
    required = taller * multiplier

    # 두 동 간 거리 (UTM 변환)
    # footprint(GeoJSON) 있으면 면 대 면 최단거리, 없으면 centroid 간 거리
    try:
        if footprint_a and footprint_b:
            fp_a_utm = _wgs_to_utm(shape(footprint_a))
            fp_b_utm = _wgs_to_utm(shape(footprint_b))
            distance = fp_a_utm.distance(fp_b_utm)
        else:
            pt_a = _wgs_to_utm(Point(building_a["centroid"][0], building_a["centroid"][1]))
            pt_b = _wgs_to_utm(Point(building_b["centroid"][0], building_b["centroid"][1]))
            distance = pt_a.distance(pt_b)
    except Exception:
        distance = 0.0

    return {
        "distance_m": round(distance, 2),
        "required_m": round(required, 2),
        "ratio": round(distance / taller, 3) if taller > 0 else 0,
        "compliant": distance >= required,
        "taller_height_m": taller,
        "formula": f"H×{multiplier} = {taller}×{multiplier} = {required:.1f}m",
    }
