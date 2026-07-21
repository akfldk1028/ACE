"""Pose-invariant orthographic silhouettes including profiled surfaces."""

from __future__ import annotations

from collections import OrderedDict
from functools import lru_cache
from math import atan2, cos, degrees, radians, sin
from typing import TypeAlias

from shapely.affinity import rotate, scale, translate
from shapely.geometry import Polygon, box
from shapely.wkb import loads as load_wkb

from design.maas.source_geometry.ir import SourceMass
from .geometry_safety import safe_symmetric_difference_ratio, safe_unary_union


VolumeKey: TypeAlias = tuple[tuple[str, str, float, float], ...]
SurfaceVertices: TypeAlias = tuple[tuple[float, float, float], ...]
ProfiledSurface: TypeAlias = tuple[str, SurfaceVertices]
SurfaceKey: TypeAlias = tuple[ProfiledSurface, ...]
VisualSilhouetteKey: TypeAlias = tuple[VolumeKey, SurfaceKey]
LayeredFootprint: TypeAlias = tuple[str, Polygon, float, float]


# A portfolio compares the same source against many neighbours.  Serialising
# every recursive triangle and rebuilding its three projections for every pair
# dominated the PNU benchmark.  Keep bounded, process-local caches; the source
# object itself is retained in the entry, so Python object-id reuse cannot
# return another source's key.
_SOURCE_KEY_CACHE: OrderedDict[int, tuple[SourceMass, VisualSilhouetteKey]] = OrderedDict()
_SOURCE_KEY_CACHE_LIMIT = 1_024


def source_visual_silhouette_key(source: SourceMass) -> VisualSilhouetteKey:
    """Serialize mass solids and renderer-visible profiled surfaces locally."""
    cache_id = id(source)
    cached = _SOURCE_KEY_CACHE.get(cache_id)
    if cached is not None and cached[0] is source:
        _SOURCE_KEY_CACHE.move_to_end(cache_id)
        return cached[1]
    center = source.footprint.centroid
    volumes = tuple(sorted(
        (
            volume.role,
            translate(volume.footprint, xoff=-center.x, yoff=-center.y).wkb_hex,
            round(float(volume.bottom_fraction), 6),
            round(float(volume.top_fraction), 6),
        )
        for volume in source.volumes
        if not volume.footprint.is_empty
    ))
    surfaces = tuple(sorted(
        (
            surface.volume_role,
            tuple(
                (
                    # vertices_m is already local to the source-footprint
                    # centroid; subtracting a world centroid again corrupts
                    # the surface-aware duplicate metric.
                    round(float(x), 6),
                    round(float(y), 6),
                    round(float(z), 6),
                )
                for x, y, z in surface.vertices_m
            ),
        )
        for surface in source.surfaces
        if surface.surface_type.startswith("profiled_") and len(surface.vertices_m) >= 3
    ))
    key = (volumes, surfaces)
    _SOURCE_KEY_CACHE[cache_id] = (source, key)
    _SOURCE_KEY_CACHE.move_to_end(cache_id)
    while len(_SOURCE_KEY_CACHE) > _SOURCE_KEY_CACHE_LIMIT:
        _SOURCE_KEY_CACHE.popitem(last=False)
    return key


def visual_silhouette_distance(left: SourceMass, right: SourceMass) -> float:
    left_key = source_visual_silhouette_key(left)
    right_key = source_visual_silhouette_key(right)
    if right_key < left_key:
        left_key, right_key = right_key, left_key
    return visual_silhouette_distance_from_keys(left_key, right_key)


@lru_cache(maxsize=131_072)
def visual_silhouette_distance_from_keys(
    left_key: VisualSilhouetteKey,
    right_key: VisualSilhouetteKey,
) -> float:
    left_views = _cached_views(left_key, angle=0.0, mirror_x=False)
    if left_views is None:
        return 1.0
    best = 1.0
    for angle in (0.0, 90.0, 180.0, 270.0):
        for mirror_x in (False, True):
            right_views = _cached_views(right_key, angle=angle, mirror_x=mirror_x)
            if right_views is None:
                continue
            distances = tuple(
                safe_symmetric_difference_ratio(a, b)
                for a, b in zip(left_views, right_views)
            )
            best = min(best, distances[0] * 0.40 + distances[1] * 0.30 + distances[2] * 0.30)
    return min(1.0, best)


@lru_cache(maxsize=8_192)
def _principal_frame(
    key: VisualSilhouetteKey,
) -> tuple[tuple[LayeredFootprint, ...], SurfaceKey] | None:
    volume_key, surfaces = key
    volumes = tuple(
        (role, load_wkb(bytes.fromhex(wkb_hex)), bottom, top)
        for role, wkb_hex, bottom, top in volume_key
    )
    if not volumes:
        return None
    union = safe_unary_union([footprint for _, footprint, _, _ in volumes])
    if union is None or union.is_empty:
        return None
    rectangle = union.minimum_rotated_rectangle
    coordinates = list(rectangle.exterior.coords)
    edges = [
        (
            ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5,
            degrees(atan2(y2 - y1, x2 - x1)),
        )
        for (x1, y1), (x2, y2) in zip(coordinates, coordinates[1:])
    ]
    major_length, major_angle = max(edges, key=lambda item: item[0])
    if major_length <= 1e-9:
        return None
    normalized_volumes = tuple(
        (
            role,
            scale(
                rotate(footprint, -major_angle, origin=(0.0, 0.0)),
                xfact=1.0 / major_length,
                yfact=1.0 / major_length,
                origin=(0.0, 0.0),
            ),
            bottom,
            top,
        )
        for role, footprint, bottom, top in volumes
    )
    angle = radians(-major_angle)
    normalized_surfaces = tuple(
        (volume_role, tuple(
            (
                (x * cos(angle) - y * sin(angle)) / major_length,
                (x * sin(angle) + y * cos(angle)) / major_length,
                z,
            )
            for x, y, z in vertices
        ))
        for volume_role, vertices in surfaces
    )
    return normalized_volumes, normalized_surfaces


@lru_cache(maxsize=32_768)
def _cached_views(
    key: VisualSilhouetteKey,
    *,
    angle: float,
    mirror_x: bool,
) -> tuple[Polygon, Polygon, Polygon] | None:
    frame = _principal_frame(key)
    if frame is None:
        return None
    if angle or mirror_x:
        frame = _transform_geometry(*frame, angle=angle, mirror_x=mirror_x)
    return _views(*frame)


def _transform_geometry(
    volumes: tuple[LayeredFootprint, ...],
    surfaces: SurfaceKey,
    *,
    angle: float,
    mirror_x: bool,
) -> tuple[tuple[LayeredFootprint, ...], SurfaceKey]:
    transformed_volumes = tuple(
        (
            role,
            rotate(
                scale(footprint, xfact=-1.0 if mirror_x else 1.0, yfact=1.0, origin=(0.0, 0.0)),
                angle,
                origin=(0.0, 0.0),
            ),
            bottom,
            top,
        )
        for role, footprint, bottom, top in volumes
    )
    theta = radians(angle)
    transformed_surfaces: list[ProfiledSurface] = []
    for volume_role, vertices in surfaces:
        transformed: list[tuple[float, float, float]] = []
        for x, y, z in vertices:
            mirrored_x = -x if mirror_x else x
            transformed.append((
                mirrored_x * cos(theta) - y * sin(theta),
                mirrored_x * sin(theta) + y * cos(theta),
                z,
            ))
        transformed_surfaces.append((volume_role, tuple(transformed)))
    return transformed_volumes, tuple(transformed_surfaces)


def _projection_polygon(vertices: SurfaceVertices, axes: tuple[int, int]) -> Polygon | None:
    coordinates = [(vertex[axes[0]], vertex[axes[1]]) for vertex in vertices]
    candidate = Polygon(coordinates)
    if candidate.is_empty or candidate.area <= 1e-9:
        return None
    if not candidate.is_valid:
        candidate = candidate.buffer(0)
    return candidate if isinstance(candidate, Polygon) and not candidate.is_empty else None


def _views(
    volumes: tuple[LayeredFootprint, ...],
    surfaces: SurfaceKey,
) -> tuple[Polygon, Polygon, Polygon]:
    profiled_roles = {volume_role for volume_role, _ in surfaces}
    volume_top = [footprint for _, footprint, _, _ in volumes]
    volume_front = [
        box(footprint.bounds[0], bottom, footprint.bounds[2], top)
        for role, footprint, bottom, top in volumes
        if role not in profiled_roles
    ]
    volume_side = [
        box(footprint.bounds[1], bottom, footprint.bounds[3], top)
        for role, footprint, bottom, top in volumes
        if role not in profiled_roles
    ]
    projected_top = [polygon for _, vertices in surfaces if (polygon := _projection_polygon(vertices, (0, 1))) is not None]
    projected_front = [polygon for _, vertices in surfaces if (polygon := _projection_polygon(vertices, (0, 2))) is not None]
    projected_side = [polygon for _, vertices in surfaces if (polygon := _projection_polygon(vertices, (1, 2))) is not None]
    return (
        safe_unary_union([*volume_top, *projected_top]) or Polygon(),
        safe_unary_union([*volume_front, *projected_front]) or Polygon(),
        safe_unary_union([*volume_side, *projected_side]) or Polygon(),
    )


__all__ = [
    "source_visual_silhouette_key",
    "visual_silhouette_distance",
    "visual_silhouette_distance_from_keys",
]
