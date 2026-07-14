"""Deterministic curve operators for graph-authored early massing.

These operators own no parcel template or architectural style. They turn an
agent-authored control polyline into a stable continuous path and a clipped
sweep footprint that can be shared by ribbon, bridge and circulation graphs.
"""

from __future__ import annotations

from math import hypot

from shapely.geometry import LineString, MultiPolygon, Polygon


Point2D = tuple[float, float]


def catmull_rom_path(control_points: tuple[Point2D, ...], *, samples_per_span: int = 3) -> tuple[Point2D, ...]:
    """Interpolate a C1 continuous path through the supplied control points."""
    if len(control_points) < 3:
        return control_points
    resolution = max(2, min(8, int(samples_per_span)))
    padded = (control_points[0], *control_points, control_points[-1])
    result: list[Point2D] = []
    for span in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[span - 1:span + 3]
        for sample in range(resolution):
            t = sample / resolution
            t2, t3 = t * t, t * t * t
            x = 0.5 * (
                2.0 * p1[0]
                + (-p0[0] + p2[0]) * t
                + (2.0 * p0[0] - 5.0 * p1[0] + 4.0 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3.0 * p1[0] - 3.0 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                2.0 * p1[1]
                + (-p0[1] + p2[1]) * t
                + (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3
            )
            result.append((x, y))
    result.append(control_points[-1])
    return tuple(_deduplicate(result))


def swept_ribbon(
    control_points: tuple[Point2D, ...],
    *,
    half_width: float,
    clip: Polygon,
    samples_per_span: int = 3,
) -> Polygon | None:
    """Create one clean, clipped sweep instead of a chain of box fragments."""
    if len(control_points) < 2 or half_width <= 0 or clip.is_empty:
        return None
    path = catmull_rom_path(control_points, samples_per_span=samples_per_span)
    if len(path) < 2:
        return None
    swept = LineString(path).buffer(half_width, cap_style=2, join_style=1, resolution=2)
    # Keep a readable curve while bounding facade tessellation for review PNGs.
    swept = swept.simplify(max(half_width * 0.08, 0.01), preserve_topology=True).intersection(clip)
    if isinstance(swept, MultiPolygon):
        swept = max(swept.geoms, key=lambda item: item.area)
    if not isinstance(swept, Polygon) or swept.is_empty:
        return None
    return swept


def path_curvature_evidence(points: tuple[Point2D, ...]) -> dict[str, float | int]:
    smooth = catmull_rom_path(points)
    length = sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(smooth, smooth[1:]))
    chord = hypot(smooth[-1][0] - smooth[0][0], smooth[-1][1] - smooth[0][1]) if len(smooth) > 1 else 0.0
    return {
        "control_point_count": len(points),
        "sample_count": len(smooth),
        "path_length_m": round(length, 3),
        "curvature_ratio": round(length / max(chord, 1e-9), 4),
    }


def _deduplicate(points: list[Point2D]) -> list[Point2D]:
    result: list[Point2D] = []
    for point in points:
        if not result or hypot(point[0] - result[-1][0], point[1] - result[-1][1]) > 1e-7:
            result.append(point)
    return result


__all__ = ["catmull_rom_path", "path_curvature_evidence", "swept_ribbon"]
