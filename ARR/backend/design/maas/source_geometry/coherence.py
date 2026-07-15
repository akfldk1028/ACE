"""Generator-independent geometric coherence objective for MAAS masses."""

from __future__ import annotations

from typing import Any

from shapely.ops import unary_union

from .ir import SourceVolume
from .polygon_quality import evaluate_polygon_quality


COHERENCE_SCHEMA_VERSION = "arr.maas.mass_coherence.v2"


def evaluate_source_volume_coherence(volumes: tuple[SourceVolume, ...]) -> dict[str, Any]:
    if not volumes:
        return {"schema_version": COHERENCE_SCHEMA_VERSION, "status": "missing", "score": 0.0, "hard_pass": False}
    areas = [max(float(volume.footprint.area), 1e-9) for volume in volumes]
    continuous_field = all(
        "continuous_ribbon_lane" in str(volume.role) or "branched_ribbon" in str(volume.role)
        for volume in volumes
    )
    intentional_cluster = (
        len(volumes) >= 3
        and sum("_unit_" in str(volume.role).lower() for volume in volumes) >= 3
    )
    component_allowance = 4 if intentional_cluster else (3 if continuous_field else 2)

    def is_linear_architectural_role(volume: SourceVolume) -> bool:
        role = str(volume.role).lower()
        return any(token in role for token in (
            "ribbon", "bridge", "connector", "spine", "ramp", "program_section_band",
        ))

    polygon_evidence = [
        evaluate_polygon_quality(
            volume.footprint,
            # A bridge or ribbon is intentionally linear; judging it with the
            # compact-monolith perimeter limit rejects even a clean rectangle.
            # Hairline width and overlap remain independent hard gates.
            linear_field=is_linear_architectural_role(volume),
        )
        for volume in volumes
    ]
    polygon_failure_count = sum(1 for evidence in polygon_evidence if not evidence["hard_pass"])
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
        + max(0, component_count - component_allowance) * 0.22
        + fragment_count * 0.16
        + complexity * 0.20
        + hierarchy_penalty
        + polygon_failure_count * 0.30
    )
    score = max(0.0, min(1.0, 1.0 - energy))
    hard_pass = (
        len(volumes) <= 5
        and redundant_pairs <= 1
        and component_count <= component_allowance
        and fragment_count <= 1
        and polygon_failure_count == 0
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
        "polygon_quality_hard_pass": polygon_failure_count == 0,
        "polygon_quality_failure_count": polygon_failure_count,
        "polygon_quality": polygon_evidence,
        "continuous_field_exception": continuous_field,
        "intentional_cluster_exception": intentional_cluster,
        "plan_component_allowance": component_allowance,
    }


__all__ = ["COHERENCE_SCHEMA_VERSION", "evaluate_source_volume_coherence"]
