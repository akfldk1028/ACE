"""
§119 / §86 datum 가중평균 수식.

순수 수학 모듈 — I/O는 elevation_api.py가 담당. 이 모듈은 polygon/line + 표고
데이터를 받아 datum elevation(m)을 계산.

수식 (시행령 §119②):
    H_datum = Σ(L_i × h_i) / Σ(L_i)
    L_i = 외벽 둘레 segment 수평거리 (m)
    h_i = 해당 segment 위치 지표면 표고 (m)
"""

from __future__ import annotations

import logging

from shapely.geometry import LineString, Polygon
from shapely.ops import transform
from pyproj import Transformer

from land import config as land_config
from land.services.datum import elevation_api

logger = logging.getLogger(__name__)

# Korea UTM zone 52N (수평거리 정확 측정용)
_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32652", always_xy=True)


def _wgs_to_utm(geom):
    return transform(_to_utm.transform, geom)


def _denoise_median_filter(values: list[float], window: int = 3) -> list[float]:
    """1D circular median filter (polygon ring 가정).

    각 점을 자신과 좌우 (window-1)/2 이웃의 중앙값으로 대체. 90m DEM 격자 인접
    셀 차이는 spike 형태(한 점만 튐)라 median이 흡수하고, 실제 경사면(점진적
    증가)은 그대로 유지된다.

    window<2 또는 len(values)<window면 원본 그대로 반환.
    """
    if window < 2 or len(values) < window:
        return list(values)
    n = len(values)
    radius = window // 2
    out: list[float] = []
    for i in range(n):
        # circular neighborhood (polygon ring)
        nb = sorted(values[(i + k - radius) % n] for k in range(window))
        out.append(nb[len(nb) // 2])
    return out


def parcel_datum_119(parcel_wgs: Polygon) -> tuple[float, list[dict]]:
    """
    §119②: 외벽 둘레 가중평균 datum.

    각 polygon edge에서 표고를 sample → segment 길이 가중평균.

    `config.DATUM_EDGE_SUBSAMPLE=true` (default) 면 길이 > THRESHOLD_M(10m)인 edge를
    STEP_M(5m) 간격 sub-segment로 분할하고 각 sub-segment 중점에서 sample. §119②
    "수평거리에 따라 가중평균"의 수치적분 정밀도가 향상됨 (큰 필지에서 edge 1점
    대표의 손실 제거).

    `config.DATUM_MEDIAN_FILTER=true` (default) 면 fetch 직후 ring 형태로 median
    filter 적용 (window=3). 90m DEM 격자 인접 셀 spike noise 흡수, 실제 경사 유지.

    Args:
        parcel_wgs: 필지 polygon (WGS84 lng,lat)

    Returns:
        (datum_m, segments)
        segments[i] = {"edge_idx", "length_m", "midpoint_lng", "midpoint_lat",
                       "midpoint_elev_m"}
        sub-sample 활성시 같은 edge_idx가 여러 segment에 나타날 수 있음.
    """
    parcel_utm = _wgs_to_utm(parcel_wgs)
    coords_wgs = list(parcel_wgs.exterior.coords)
    coords_utm = list(parcel_utm.exterior.coords)

    use_subsample = land_config.DATUM_EDGE_SUBSAMPLE
    sub_threshold = land_config.DATUM_EDGE_SUBSAMPLE_THRESHOLD_M
    sub_step = land_config.DATUM_EDGE_SUBSAMPLE_STEP_M
    use_median = land_config.DATUM_MEDIAN_FILTER
    median_window = land_config.DATUM_MEDIAN_FILTER_WINDOW

    midpoints_wgs: list[tuple[float, float]] = []   # (lat, lng) for elevation_api
    sample_lengths_m: list[float] = []
    sample_midpoints_lnglat: list[tuple[float, float]] = []
    sample_edge_indices: list[int] = []

    for i in range(len(coords_utm) - 1):
        x1, y1 = coords_utm[i][0], coords_utm[i][1]
        x2, y2 = coords_utm[i + 1][0], coords_utm[i + 1][1]
        L_total = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if L_total < 0.1:
            continue

        lng1, lat1 = coords_wgs[i][0], coords_wgs[i][1]
        lng2, lat2 = coords_wgs[i + 1][0], coords_wgs[i + 1][1]

        if not use_subsample or L_total <= sub_threshold:
            # 단일 중점 (기존 동작)
            mlng = (lng1 + lng2) / 2.0
            mlat = (lat1 + lat2) / 2.0
            sample_lengths_m.append(L_total)
            sample_midpoints_lnglat.append((mlng, mlat))
            midpoints_wgs.append((mlat, mlng))
            sample_edge_indices.append(i)
        else:
            # 긴 edge 분할: STEP_M 간격 sub-segment, 각 중점에서 sample.
            n_sub = max(2, int(round(L_total / sub_step)))
            seg_len = L_total / n_sub
            for k in range(n_sub):
                t = (k + 0.5) / n_sub   # k-th sub-segment midpoint
                slng = lng1 + (lng2 - lng1) * t
                slat = lat1 + (lat2 - lat1) * t
                sample_lengths_m.append(seg_len)
                sample_midpoints_lnglat.append((slng, slat))
                midpoints_wgs.append((slat, slng))
                sample_edge_indices.append(i)

    if not sample_lengths_m:
        raise ValueError(
            "parcel_datum_119: polygon has no usable edges "
            "(all edges < 0.1m or empty). Provide a valid Polygon."
        )

    elevations = elevation_api.fetch_elevations(midpoints_wgs)

    if use_median:
        elevations = _denoise_median_filter(list(elevations), window=median_window)

    total_length = sum(sample_lengths_m)
    if total_length <= 0:
        return 0.0, []

    weighted_sum = sum(L * h for L, h in zip(sample_lengths_m, elevations))
    datum_m = weighted_sum / total_length

    segments = [
        {
            "edge_idx": ei,
            "length_m": round(L, 3),
            "midpoint_lng": round(mp[0], 6),
            "midpoint_lat": round(mp[1], 6),
            "midpoint_elev_m": round(h, 3),
        }
        for ei, L, mp, h in zip(
            sample_edge_indices, sample_lengths_m, sample_midpoints_lnglat, elevations
        )
    ]
    return datum_m, segments


def road_datum_119(
    road_centerline_wgs: LineString,
    sample_step_m: float = 5.0,
) -> tuple[float, list[dict]]:
    """
    §119① 5호 가목: 전면도로 중심선 가중평균 datum.

    Centerline 위 sample_step_m 간격으로 점 sample → segment 길이 가중평균.

    Args:
        road_centerline_wgs: 도로 중심선 LineString (WGS84)
        sample_step_m: sample 간격 (기본 5m)

    Returns:
        (datum_m, samples)
    """
    line_utm = _wgs_to_utm(road_centerline_wgs)
    total_len_m = line_utm.length
    if total_len_m <= 0:
        return 0.0, []

    n_samples = max(2, int(total_len_m / sample_step_m) + 1)
    sample_distances = [i * total_len_m / (n_samples - 1) for i in range(n_samples)]

    points_wgs: list[tuple[float, float]] = []
    points_lnglat: list[tuple[float, float]] = []
    for d in sample_distances:
        pt = road_centerline_wgs.interpolate(d / total_len_m, normalized=True)
        points_wgs.append((pt.y, pt.x))   # (lat, lng)
        points_lnglat.append((pt.x, pt.y))

    elevations = elevation_api.fetch_elevations(points_wgs)

    # 각 sample은 인접 segment 길이의 절반 가중치 (사다리꼴)
    if len(elevations) < 2:
        datum_m = elevations[0] if elevations else 0.0
        samples = [{"dist_m": 0.0, "elev_m": datum_m}]
        return datum_m, samples

    seg_lens: list[float] = []
    weighted_sum = 0.0
    for i in range(len(elevations)):
        if i == 0:
            w = (sample_distances[1] - sample_distances[0]) / 2.0
        elif i == len(elevations) - 1:
            w = (sample_distances[-1] - sample_distances[-2]) / 2.0
        else:
            w = (sample_distances[i + 1] - sample_distances[i - 1]) / 2.0
        seg_lens.append(w)
        weighted_sum += w * elevations[i]

    total_w = sum(seg_lens)
    datum_m = weighted_sum / total_w if total_w > 0 else 0.0

    samples = [
        {"dist_m": round(d, 3), "lng": round(p[0], 6), "lat": round(p[1], 6),
         "elev_m": round(h, 3)}
        for d, p, h in zip(sample_distances, points_lnglat, elevations)
    ]
    return datum_m, samples


def neighbor_avg_datum_86(my_datum_m: float, neighbor_datum_m: float) -> float:
    """§86: 정북인접지와 고저차 있는 경우 두 가중평균면의 평균."""
    return (my_datum_m + neighbor_datum_m) / 2.0


def site_above_road_119(parcel_datum_m: float, road_datum_m: float) -> float:
    """
    §119① 5호 나목: 대지가 전면도로보다 높을 때
    "고저차의 1/2의 높이만큼 올라온 위치에 도로면이 있다고 봄"

    → effective road datum = road_datum + (parcel_datum - road_datum) / 2
                           = (parcel_datum + road_datum) / 2

    대지가 도로보다 낮으면(parcel_datum < road_datum) 그대로 도로 datum 사용.
    """
    if parcel_datum_m <= road_datum_m:
        return road_datum_m
    return (parcel_datum_m + road_datum_m) / 2.0


def split_3m_segments(
    parcel_wgs: Polygon, max_diff_m: float = 3.0,
) -> list[Polygon] | None:
    """
    §119② 단서: 고저차 >3m면 3m 이내 영역마다 datum 분할.

    Phase 1 stub — 미구현. 호출자가 None을 받으면 단일 datum 사용.

    Phase 4에서 구현 예정 (등고선 따라 polygon 분할).
    """
    return None
