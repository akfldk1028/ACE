"""Generator-independent geometric coherence objective for MAAS masses."""

from __future__ import annotations

from typing import Any

from shapely.ops import unary_union

from .ir import SourceVolume


COHERENCE_SCHEMA_VERSION = "arr.maas.mass_coherence.v1"


def evaluate_source_volume_coherence(volumes: tuple[SourceVolume, ...]) -> dict[str, Any]:
    if not volumes:
        return {"schema_version": COHERENCE_SCHEMA_VERSION, "status": "missing", "score": 0.0, "hard_pass": False}
    areas = [max(float(volume.footprint.area), 1e-9) for volume in volumes]
    total_area = max(sum(areas), 1e-9)
    main_ratio = max(areas) / total_area
    redundant_pairs = 0
    collision_energy = 0.0
    for index, left in enumerate(volumes):
        left_height = max(float(left.top_fraction - left.bottom_fraction), 1e-9)
        for right in volumes[:index]:
            vertical = max(
                0.0,
                min(left.top_fraction, right.top_fraction) - max(left.bottom_fraction, right.bottom_fraction),
            ) / min(left_height, max(float(right.top_fraction - right.bottom_fraction), 1e-9))
            if vertical <= 0.0:
                continue
            planar = float(left.footprint.intersection(right.footprint).area) / min(
                max(float(left.footprint.area), 1e-9), max(float(right.footprint.area), 1e-9)
            )
            occupancy = vertical * planar
            collision_energy += max(0.0, occupancy - 0.28)
            if occupancy >= 0.58:
                redundant_pairs += 1
    connected = unary_union([volume.footprint.buffer(0.12) for volume in volumes])
    component_count = len(getattr(connected, "geoms", (connected,)))
    fragment_count = sum(1 for area in areas if area < max(areas) * 0.16 and area < total_area * 0.10)
    complexity = max(0, len(volumes) - 5)
    hierarchy_penalty = max(0.0, 0.26 - main_ratio) * 2.0
    energy = (
        collision_energy * 0.42
        + redundant_pairs * 0.18
        + max(0, component_count - 2) * 0.22
        + fragment_count * 0.16
        + complexity * 0.20
        + hierarchy_penalty
    )
    score = max(0.0, min(1.0, 1.0 - energy))
    hard_pass = (
        len(volumes) <= 5
        and redundant_pairs <= 1
        and component_count <= 2
        and fragment_count <= 1
        and score >= 0.62
    )
    return {
        "schema_version": COHERENCE_SCHEMA_VERSION,
        "status": "measured",
        "score": round(score, 3),
        "hard_pass": hard_pass,
        "volume_count": len(volumes),
        "main_mass_area_ratio": round(main_ratio, 3),
        "redundant_overlap_pair_count": redundant_pairs,
        "collision_energy": round(collision_energy, 3),
        "plan_component_count": component_count,
        "small_fragment_count": fragment_count,
    }


__all__ = ["COHERENCE_SCHEMA_VERSION", "evaluate_source_volume_coherence"]
