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
    if provider == "ngii_5m":
        raise NotImplementedError("ngii_5m provider not yet implemented; use open_meteo")
    raise ValueError(f"Unknown ELEVATION_PROVIDER: {provider!r}")


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
