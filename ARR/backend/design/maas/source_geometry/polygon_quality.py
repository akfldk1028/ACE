"""Scale-independent repair and quality evidence for MAAS plan polygons.

This layer removes numerical clipping debris.  It deliberately does not turn a
poor massing idea into a good one and does not approximate authored 3D roof
surfaces; those remain separate generator and surface-quality concerns.
"""

from __future__ import annotations

from math import hypot, pi, sqrt
from collections.abc import Iterable
from typing import Any

from shapely.geometry import MultiPolygon, Polygon


POLYGON_QUALITY_SCHEMA_VERSION = "arr.maas.polygon_quality.v1"
SITE_CONTAINMENT_SCHEMA_VERSION = "arr.maas.site_containment.v1"


def _largest_polygon(geometry) -> Polygon | None:
    if geometry is None or geometry.is_empty:
        return None
    repaired = geometry if geometry.is_valid else geometry.buffer(0)
    if repaired.is_empty:
        return None
    if isinstance(repaired, Polygon):
        return repaired
    if isinstance(repaired, MultiPolygon):
        polygons = [part for part in repaired.geoms if not part.is_empty]
        return max(polygons, key=lambda part: part.area) if polygons else None
    return None


def _edge_lengths(polygon: Polygon) -> list[float]:
    coordinates = list(polygon.exterior.coords)
    return [
        hypot(right[0] - left[0], right[1] - left[1])
        for left, right in zip(coordinates, coordinates[1:])
    ]


def _minimum_rotated_width(polygon: Polygon) -> float:
    rectangle = polygon.minimum_rotated_rectangle
    edges = _edge_lengths(rectangle)
    return min(edges) if edges else 0.0


def repair_source_polygon(geometry, *, minimum_area: float = 0.0) -> Polygon | None:
    """Repair invalidity and short-edge noise without erasing courts or notches."""

    polygon = _largest_polygon(geometry)
    if polygon is None or polygon.area < minimum_area:
        return None
    original_area = float(polygon.area)
    scale = sqrt(max(original_area, 1e-9))
    # A small topology-preserving simplification removes clipping spikes and
    # near-duplicate vertices while retaining intentional concavity and holes.
    simplified = _largest_polygon(polygon.simplify(scale * 0.0025, preserve_topology=True))
    if simplified is None:
        return polygon
    area_retention = float(simplified.area) / max(original_area, 1e-9)
    if area_retention < 0.97 or simplified.area < minimum_area:
        return polygon
    return simplified


def evaluate_polygon_quality(polygon: Polygon | None, *, linear_field: bool = False) -> dict[str, Any]:
    """Return normalized evidence; thresholds work across parcel sizes."""

    if polygon is None or polygon.is_empty:
        return {
            "schema_version": POLYGON_QUALITY_SCHEMA_VERSION,
            "status": "missing",
            "hard_pass": False,
            "failure_reasons": ["missing_polygon"],
        }
    area = float(polygon.area)
    scale = sqrt(max(area, 1e-9))
    edges = _edge_lengths(polygon)
    min_edge_ratio = min(edges, default=0.0) / scale
    short_edge_count = sum(1 for length in edges if length / scale < 0.004)
    width_ratio = _minimum_rotated_width(polygon) / scale
    # Judge silhouette tortuosity from the exterior only. Courtyard/atrium
    # perimeters are intentional void language and must not make a clean outer
    # mass look artificially fragmented.
    compactness = float(polygon.exterior.length) ** 2 / max(4.0 * pi * area, 1e-9)
    vertex_count = max(0, len(polygon.exterior.coords) - 1)
    failure_reasons: list[str] = []
    if not polygon.is_valid:
        failure_reasons.append("invalid_polygon")
    if area <= 1e-6:
        failure_reasons.append("zero_area")
    if width_ratio < 0.055:
        failure_reasons.append("hairline_polygon")
    if short_edge_count > 2:
        failure_reasons.append("clipping_spikes_or_short_edges")
    # P^2/(4*pi*A) is 1.0 for a circle and about 1.27 for a square.  Values
    # above 3 are usually starburst/interlock debris: technically connected,
    # but visually read as thin LEGO arms rather than one architectural mass.
    # This is scale independent and intentionally stricter than validity.
    # P^2/A necessarily rises with aspect ratio, so the compact-monolith
    # threshold misclassifies a clean occupiable bar/ribbon as tortuous. The
    # separate minimum-width and short-edge gates still reject hairlines and
    # clipped spikes; 7.5 allows a smooth architectural spine while remaining
    # far below the pathological fragmented outlines caught by those gates.
    tortuosity_limit = 7.5 if linear_field and vertex_count <= 24 and short_edge_count <= 2 else 2.65
    if compactness > tortuosity_limit:
        failure_reasons.append("over_tortuous_mass_outline")
    if vertex_count > 96:
        failure_reasons.append("excessive_plan_vertices")
    return {
        "schema_version": POLYGON_QUALITY_SCHEMA_VERSION,
        "status": "measured",
        "hard_pass": not failure_reasons,
        "failure_reasons": failure_reasons,
        "valid": bool(polygon.is_valid),
        "area_m2": round(area, 3),
        "vertex_count": vertex_count,
        "hole_count": len(polygon.interiors),
        "minimum_edge_ratio": round(min_edge_ratio, 5),
        "short_edge_count": short_edge_count,
        "minimum_width_ratio": round(width_ratio, 5),
        "compactness": round(compactness, 3),
        "linear_field": bool(linear_field),
        "tortuosity_limit": tortuosity_limit,
    }


def evaluate_site_containment(
    site: Polygon,
    footprints: Iterable[Polygon],
    *,
    linear_tolerance_m: float = 0.002,
) -> dict[str, Any]:
    """Measure metric-site containment without treating GEOS dust as a breach.

    The buffered predicate is only a numerical robustness check. The summed
    outside area is independently capped, so it cannot absorb a meaningful
    setback or parcel-boundary violation.
    """

    polygons = [polygon for polygon in footprints if polygon is not None and not polygon.is_empty]
    area_tolerance_m2 = min(0.005, max(0.0005, float(site.area) * 0.000005))
    outside_areas = [float(polygon.difference(site).area) for polygon in polygons]
    outside_area_m2 = sum(outside_areas)
    buffered_site = site.buffer(max(0.0, float(linear_tolerance_m)))
    buffered_covers = all(buffered_site.covers(polygon) for polygon in polygons)
    hard_pass = bool(polygons) and buffered_covers and outside_area_m2 <= area_tolerance_m2
    failure_reasons: list[str] = []
    if not polygons:
        failure_reasons.append("missing_mass_footprints")
    if not buffered_covers:
        failure_reasons.append("outside_site_linear_tolerance")
    if outside_area_m2 > area_tolerance_m2:
        failure_reasons.append("outside_site_area_tolerance")
    return {
        "schema_version": SITE_CONTAINMENT_SCHEMA_VERSION,
        "hard_pass": hard_pass,
        "failure_reasons": failure_reasons,
        "footprint_count": len(polygons),
        "outside_area_m2": round(outside_area_m2, 9),
        "maximum_piece_outside_area_m2": round(max(outside_areas, default=0.0), 9),
        "linear_tolerance_m": float(linear_tolerance_m),
        "area_tolerance_m2": round(area_tolerance_m2, 9),
        "buffered_covers": buffered_covers,
    }


__all__ = [
    "POLYGON_QUALITY_SCHEMA_VERSION",
    "SITE_CONTAINMENT_SCHEMA_VERSION",
    "evaluate_polygon_quality",
    "evaluate_site_containment",
    "repair_source_polygon",
]
