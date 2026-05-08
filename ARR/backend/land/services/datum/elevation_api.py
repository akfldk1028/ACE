"""
Elevation API — 좌표 → 표고 (datum elevation 계산용).

§119 가중평균 datum 계산에 필요한 표고 데이터를 외부 DEM에서 가져옴.

Provider:
    - "open_meteo" (default): Open-Meteo Elevation API, 90m Copernicus GLO-90, 무료, 인증 X
    - "ngii_5m" (향후): NGII 5m DEM self-host (R2 + opentopodata Docker)

Vworld는 표고 API 없음 (2019 3D Open API 폐쇄).

Failure semantics
-----------------
한 batch(<=100점) 안에서 **전체 실패**시 ElevationFetchError 발생.
caller(cases.py)가 catch하여 datum_source="failed" 로 표시.
부분 실패는 0.0 fallback + warning log (주로 batch>100 multi-call에서만 발생 가능).
"""

from __future__ import annotations

import logging

from land import config

logger = logging.getLogger(__name__)


class ElevationFetchError(RuntimeError):
    """Open-Meteo 호출 전체 실패 (네트워크/HTTP/파싱). caller가 datum 신뢰도 표시용."""


# 모듈 스코프 좌표→표고 캐시. round 5자리 (~1m 격자) 단위로 dedupe.
_ELEVATION_CACHE: dict[tuple[float, float], float] = {}


def cache_clear() -> None:
    """테스트 격리용. fetch_elevations 가 캐시 사용하므로 mock 사이에 호출."""
    _ELEVATION_CACHE.clear()


def cache_size() -> int:
    return len(_ELEVATION_CACHE)


def fetch_elevations(points: list[tuple[float, float]]) -> list[float]:
    """
    좌표 리스트 → 표고 리스트(m).

    Args:
        points: [(lat, lng), ...] (Open-Meteo 표준 순서)

    Returns:
        [m, ...] same length. 캐시에 있으면 캐시값, 없으면 Open-Meteo 호출.

    Raises:
        ElevationFetchError: 단일 batch(<=100점) 전체 실패시.
        ValueError: 알 수 없는 ELEVATION_PROVIDER.
        NotImplementedError: provider="ngii_5m" (Phase 3).
    """
    if not points:
        return []
    provider = config.ELEVATION_PROVIDER
    if provider == "open_meteo":
        return _open_meteo_batch(points)
    if provider == "ngii_lidar_1m":
        return _ngii_lidar_1m_batch(points)
    # 그 외 모두 opentopodata sidecar/공개 인스턴스 dataset name으로 처리.
    # 알려진 값: copernicus_glo30, ngii_5m, srtm30m, aster30m, mapzen, eudem25m, etc.
    # 미커버시 Open-Meteo 자동 폴백 (opentopodata 응답 None 또는 HTTP 실패).
    return _opentopodata_batch(points, dataset=provider)


def _open_meteo_batch(points: list[tuple[float, float]]) -> list[float]:
    """100점/req cap. 각 batch 호출은 독립적이며 부분 실패 가능."""
    out: list[float] = []
    BATCH = 100
    for i in range(0, len(points), BATCH):
        chunk = points[i:i + BATCH]
        out.extend(_open_meteo_call_with_cache(chunk))
    return out


def _open_meteo_call_with_cache(chunk: list[tuple[float, float]]) -> list[float]:
    """캐시 hit → 그대로 사용. miss → 모아서 1 HTTP call. 전체 실패시 raise."""
    rounded = [(round(p[0], 5), round(p[1], 5)) for p in chunk]
    out: list[float] = [0.0] * len(rounded)
    miss_idx: list[int] = []
    miss_pts: list[tuple[float, float]] = []
    for i, p in enumerate(rounded):
        cached = _ELEVATION_CACHE.get(p)
        if cached is not None:
            out[i] = cached
        else:
            miss_idx.append(i)
            miss_pts.append(p)

    if not miss_pts:
        return out

    fresh = _open_meteo_http(miss_pts)
    for i, p, e in zip(miss_idx, miss_pts, fresh):
        out[i] = e
        _ELEVATION_CACHE[p] = e
    return out


def _open_meteo_http(points: list[tuple[float, float]]) -> list[float]:
    """단일 HTTP call. 전체 실패 → ElevationFetchError. shape 불일치 → ElevationFetchError."""
    if not points:
        return []
    lats = ",".join(f"{p[0]:.5f}" for p in points)
    lngs = ",".join(f"{p[1]:.5f}" for p in points)
    try:
        resp = config.open_meteo_client.get(
            config.OPEN_METEO_URL,
            params={"latitude": lats, "longitude": lngs},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("open_meteo http failed (%d points): %s", len(points), e)
        raise ElevationFetchError(f"Open-Meteo HTTP failed: {e}") from e

    elevations = data.get("elevation")
    if not isinstance(elevations, list) or len(elevations) != len(points):
        logger.warning(
            "open_meteo: unexpected response shape (got %s len=%s, expected list of %d)",
            type(elevations).__name__,
            len(elevations) if isinstance(elevations, list) else "n/a",
            len(points),
        )
        raise ElevationFetchError(
            f"Open-Meteo response shape mismatch: expected {len(points)} elevations"
        )

    return [float(e) if isinstance(e, (int, float)) else 0.0 for e in elevations]


# ─── NGII 1m LiDAR DEM (opentopodata sidecar) ───────────────────
# 데이터 출처: NGII 항공LiDAR 1m DEM (2005~2021 도시 구축, 2년 주기 갱신).
# 라이선스: 이용허락범위 제한 없음 (무료, 상업 가능). map.ngii.go.kr 회원가입 후 다운로드.
# 호스팅: opentopodata Docker (`config.NGII_LIDAR_URL`).
# Fallback: NGII 미커버(산악/외곽) → Open-Meteo 자동 폴백.

def _ngii_lidar_1m_batch(points: list[tuple[float, float]]) -> list[float]:
    """NGII 1m LiDAR DEM batch. opentopodata 호환 응답 (`results[].elevation`)."""
    return _opentopodata_batch(points, dataset="ngii_lidar_1m")


def _opentopodata_batch(
    points: list[tuple[float, float]], *, dataset: str,
) -> list[float]:
    """opentopodata 일반 batch. dataset 이름으로 endpoint 지정."""
    out: list[float] = []
    BATCH = 100
    for i in range(0, len(points), BATCH):
        chunk = points[i:i + BATCH]
        out.extend(_opentopodata_call_with_cache(chunk, dataset=dataset))
    return out


def _opentopodata_call_with_cache(
    chunk: list[tuple[float, float]], *, dataset: str,
) -> list[float]:
    """캐시 hit → 그대로. miss → opentopodata 1 HTTP. None(커버리지 밖) → Open-Meteo 폴백."""
    rounded = [(round(p[0], 5), round(p[1], 5)) for p in chunk]
    out: list[float] = [0.0] * len(rounded)
    miss_idx: list[int] = []
    miss_pts: list[tuple[float, float]] = []
    for i, p in enumerate(rounded):
        cached = _ELEVATION_CACHE.get(p)
        if cached is not None:
            out[i] = cached
        else:
            miss_idx.append(i)
            miss_pts.append(p)

    if not miss_pts:
        return out

    try:
        fresh = _opentopodata_http(miss_pts, dataset=dataset)
    except ElevationFetchError as e:
        # opentopodata 자체 실패 → 전체 Open-Meteo 폴백
        logger.warning("opentopodata %s failed, fallback to open_meteo: %s", dataset, e)
        try:
            fresh = _open_meteo_http(miss_pts)
        except ElevationFetchError as e2:
            logger.warning("open_meteo fallback also failed: %s", e2)
            fresh = [0.0] * len(miss_pts)

    # 격자 미커버시 None → Open-Meteo 폴백 (한 번 더 HTTP, 결과 캐시)
    fallback_idx = [j for j, e in enumerate(fresh) if e is None]
    if fallback_idx:
        try:
            fb = _open_meteo_http([miss_pts[j] for j in fallback_idx])
            for j, e in zip(fallback_idx, fb):
                fresh[j] = e
        except ElevationFetchError as e:
            logger.warning("%s miss + open_meteo fallback failed: %s", dataset, e)
            for j in fallback_idx:
                fresh[j] = 0.0

    for i, p, e in zip(miss_idx, miss_pts, fresh):
        e_val = float(e) if e is not None else 0.0
        out[i] = e_val
        _ELEVATION_CACHE[p] = e_val
    return out


def _opentopodata_http(
    points: list[tuple[float, float]], *, dataset: str,
) -> list[float | None]:
    """opentopodata sidecar 일반 호출. results[i].elevation 이 None이면 커버리지 밖."""
    if not points:
        return []
    locations = "|".join(f"{p[0]:.5f},{p[1]:.5f}" for p in points)
    try:
        resp = config.ngii_client.get(
            f"{config.NGII_LIDAR_URL}/v1/{dataset}",
            params={"locations": locations},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("opentopodata %s http failed (%d points): %s", dataset, len(points), e)
        raise ElevationFetchError(f"opentopodata {dataset} HTTP failed: {e}") from e

    results = data.get("results")
    if not isinstance(results, list) or len(results) != len(points):
        raise ElevationFetchError(
            f"opentopodata {dataset} response shape mismatch: expected {len(points)} results"
        )

    out: list[float | None] = []
    for r in results:
        elev = r.get("elevation") if isinstance(r, dict) else None
        if elev is None:
            out.append(None)   # 커버리지 밖 → caller가 폴백
        elif isinstance(elev, (int, float)):
            out.append(float(elev))
        else:
            out.append(None)
    return out
