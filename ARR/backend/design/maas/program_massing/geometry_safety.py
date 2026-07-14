"""Shared defensive boundary for serialized source-volume polygons."""

from __future__ import annotations

from typing import Any, Iterable

from shapely.errors import GEOSException
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, shape
from shapely.ops import unary_union
from shapely.validation import make_valid


def _repair_polygon(geometry) -> Polygon | None:
    if geometry is None or geometry.is_empty:
        return None
    try:
        repaired = geometry if geometry.is_valid else make_valid(geometry)
    except GEOSException:
        try:
            repaired = geometry.buffer(0)
        except GEOSException:
            return None
    if isinstance(repaired, Polygon):
        return repaired
    if isinstance(repaired, (MultiPolygon, GeometryCollection)):
        polygons = [item for item in repaired.geoms if isinstance(item, Polygon) and not item.is_empty]
        return max(polygons, key=lambda item: item.area) if polygons else None
    return None


def repaired_volume_records(feature: dict[str, Any]) -> list[tuple[dict[str, Any], Any]]:
    """Parse and repair each serialized volume without aborting the population."""
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    repaired: list[tuple[dict[str, Any], Any]] = []
    for record in props.get("mass_volumes") or []:
        if not isinstance(record, dict) or not record.get("geometry"):
            continue
        try:
            polygon = _repair_polygon(shape(record["geometry"]))
        except (GEOSException, TypeError, ValueError):
            polygon = None
        if polygon is not None and not polygon.is_empty:
            repaired.append((record, polygon))
    return repaired


def safe_unary_union(geometries: Iterable[Any]):
    """Union repaired polygons; return ``None`` for one irreparable candidate."""
    items = [
        repaired
        for geometry in geometries
        if geometry is not None and not geometry.is_empty
        for repaired in [_repair_polygon(geometry)]
        if repaired is not None and not repaired.is_empty
    ]
    if not items:
        return None
    try:
        return unary_union(items)
    except GEOSException:
        retry = [_repair_polygon(item.buffer(0)) for item in items]
        retry = [item for item in retry if item is not None and not item.is_empty]
        try:
            return unary_union(retry) if retry else None
        except GEOSException:
            return None


__all__ = ["repaired_volume_records", "safe_unary_union"]
