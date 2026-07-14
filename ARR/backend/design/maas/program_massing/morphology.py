"""Pose-invariant morphology metrics for MAAS archive diversity.

This module is intentionally independent from the search/selection policy so
the representation can later be replaced by voxel, mesh-embedding or learned
metrics without rewriting the archive loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import atan2, degrees

from shapely.affinity import rotate, scale, translate
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.wkb import loads as load_wkb

from design.maas.source_geometry.ir import SourceMass


LayeredFootprint = tuple[Polygon, float, float]
MorphologyKey = tuple[tuple[str, float, float], ...]


@dataclass(frozen=True)
class MorphologyNoveltyPolicy:
    """Replaceable archive thresholds, separated by semantic relationship."""

    generic_duplicate: float = 0.20
    same_principle_repeat: float = 0.28
    same_topology_repeat: float = 0.30
    graph_audit_neighbor: float = 0.35

    def repeat_kind(
        self,
        distance: float,
        *,
        same_principle: bool,
        same_topology: bool,
    ) -> str | None:
        if distance < self.generic_duplicate:
            return "intrinsic_geometry_duplicate"
        if same_topology and distance < self.same_topology_repeat:
            return "same_topology_morphology_repeat"
        if same_principle and distance < self.same_principle_repeat:
            return "same_principle_morphology_repeat"
        return None


DEFAULT_NOVELTY_POLICY = MorphologyNoveltyPolicy()


def intrinsic_shape_distance(left: SourceMass, right: SourceMass) -> tuple[float, float]:
    """Return rotation/reflection/translation/scale-invariant 3D and plan distance.

    The normalization removes pose and overall size while retaining plan
    proportion, voids, relative component placement and vertical band logic.
    Site fit is intentionally evaluated by a separate channel.
    """
    left_key = source_morphology_key(left)
    right_key = source_morphology_key(right)
    if right_key < left_key:
        left_key, right_key = right_key, left_key
    return intrinsic_shape_distance_from_keys(left_key, right_key)


@lru_cache(maxsize=131_072)
def intrinsic_shape_distance_from_keys(
    left_key: MorphologyKey,
    right_key: MorphologyKey,
) -> tuple[float, float]:
    """Cached pair distance; selectors revisit the same pairs many times."""
    left_volumes = _principal_frame_from_key(left_key)
    right_variants = _symmetry_variants_from_key(right_key)
    if not left_volumes or not right_variants:
        return 1.0, 1.0
    left_plan = unary_union([footprint for footprint, _, _ in left_volumes])
    best_volume = best_plan = 1.0
    best_joint = float("inf")
    for transformed in right_variants:
        right_plan = unary_union([footprint for footprint, _, _ in transformed])
        plan_union = left_plan.union(right_plan)
        plan_distance = float(left_plan.symmetric_difference(right_plan).area) / max(
            float(plan_union.area),
            1e-9,
        )
        volume_distance = layered_volume_distance(left_volumes, transformed)
        joint = volume_distance * 0.7 + plan_distance * 0.3
        if joint < best_joint:
            best_joint = joint
            best_volume = volume_distance
            best_plan = plan_distance
    return min(1.0, best_volume), min(1.0, best_plan)


def principal_frame_volumes(source: SourceMass) -> list[LayeredFootprint]:
    return list(_principal_frame_from_key(source_morphology_key(source)))


def source_morphology_key(source: SourceMass) -> MorphologyKey:
    return tuple(sorted(
        (
            volume.footprint.wkb_hex,
            round(float(volume.bottom_fraction), 6),
            round(float(volume.top_fraction), 6),
        )
        for volume in source.volumes
        if not volume.footprint.is_empty
    ))


@lru_cache(maxsize=8192)
def _principal_frame_from_key(key: MorphologyKey) -> tuple[LayeredFootprint, ...]:
    volumes = tuple(
        (load_wkb(bytes.fromhex(wkb_hex)), bottom, top)
        for wkb_hex, bottom, top in key
    )
    footprints = [footprint for footprint, _, _ in volumes]
    if not footprints:
        return ()
    union = unary_union(footprints)
    if union.is_empty:
        return ()
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
        return ()
    center = union.centroid
    normalized: list[LayeredFootprint] = []
    for volume_footprint, bottom, top in volumes:
        footprint = translate(volume_footprint, xoff=-center.x, yoff=-center.y)
        footprint = rotate(footprint, -major_angle, origin=(0.0, 0.0), use_radians=False)
        footprint = scale(
            footprint,
            xfact=1.0 / major_length,
            yfact=1.0 / major_length,
            origin=(0.0, 0.0),
        )
        normalized.append((footprint, bottom, top))
    return tuple(normalized)


@lru_cache(maxsize=8192)
def _symmetry_variants_from_key(
    key: MorphologyKey,
) -> tuple[tuple[LayeredFootprint, ...], ...]:
    volumes = _principal_frame_from_key(key)
    return tuple(
        tuple(
            (dihedral_transform(footprint, angle=angle, mirror_x=mirror_x), bottom, top)
            for footprint, bottom, top in volumes
        )
        for angle in (0.0, 90.0, 180.0, 270.0)
        for mirror_x in (False, True)
    )


def dihedral_transform(footprint: Polygon, *, angle: float, mirror_x: bool) -> Polygon:
    transformed = footprint
    if mirror_x:
        transformed = scale(transformed, xfact=-1.0, yfact=1.0, origin=(0.0, 0.0))
    if angle:
        transformed = rotate(transformed, angle, origin=(0.0, 0.0), use_radians=False)
    return transformed


def layered_volume_distance(left: list[LayeredFootprint], right: list[LayeredFootprint]) -> float:
    levels = sorted({
        round(value, 6)
        for volumes in (left, right)
        for _, bottom, top in volumes
        for value in (bottom, top)
    })
    union_volume = difference_volume = 0.0
    for lower, upper in zip(levels, levels[1:]):
        thickness = upper - lower
        if thickness <= 1e-9:
            continue
        middle = (lower + upper) / 2.0
        left_active = [footprint for footprint, bottom, top in left if bottom <= middle < top]
        right_active = [footprint for footprint, bottom, top in right if bottom <= middle < top]
        left_slice = unary_union(left_active) if left_active else None
        right_slice = unary_union(right_active) if right_active else None
        if left_slice is None and right_slice is None:
            continue
        if left_slice is None:
            slice_union = slice_difference = float(right_slice.area)
        elif right_slice is None:
            slice_union = slice_difference = float(left_slice.area)
        else:
            slice_union = float(left_slice.union(right_slice).area)
            slice_difference = float(left_slice.symmetric_difference(right_slice).area)
        union_volume += slice_union * thickness
        difference_volume += slice_difference * thickness
    return min(1.0, difference_volume / max(union_volume, 1e-9))


__all__ = [
    "DEFAULT_NOVELTY_POLICY",
    "MorphologyNoveltyPolicy",
    "intrinsic_shape_distance",
    "intrinsic_shape_distance_from_keys",
    "principal_frame_volumes",
    "source_morphology_key",
]
