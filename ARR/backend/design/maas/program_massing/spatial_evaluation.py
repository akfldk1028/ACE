"""Geometry-based architectural checks beyond family labels and counters."""

from __future__ import annotations

from typing import Any

from .profiles import resolve_program_profile
from .semantic_projection import project_spatial_roles
from .geometry_safety import repaired_volume_records, safe_unary_union


ROLE_GROUPS = {
    "housing": (("living_",), ("entry_core", "circulation_bridge", "gateway"), ("north_living", "south_living", "west_living", "east_living", "podium", "gateway", "cantilever")),
    "cafe": (("room",), ("canopy", "roof"), ("service", "hearth", "court_room_west")),
    "neighborhood_living": (("primary_",), ("podium", "terrace", "platform", "ribbon"), ("tower", "folded", "shifted", "upper", "canopy", "lane_2")),
    "gymnasium": (("main", "hall"), ("service",), ("entry", "daylight", "monitor", "canopy")),
}

DOMINANT_RANGES = {"housing": (0.28, 0.58), "cafe": (0.38, 0.74), "neighborhood_living": (0.38, 0.82), "gymnasium": (0.62, 0.90)}
COVERAGE_RANGES = {"housing": (0.28, 0.72), "cafe": (0.22, 0.62), "neighborhood_living": (0.38, 0.92), "gymnasium": (0.48, 0.84)}


def attach_program_spatial_evidence(feature: dict[str, Any], *, building_type: str, site_area_m2: float | None = None) -> dict[str, Any]:
    props = feature.setdefault("properties", {})
    profile_id = resolve_program_profile(building_type)["id"]
    repaired = repaired_volume_records(feature)
    records = [record for record, _ in repaired]
    geometries = [geometry for _, geometry in repaired]
    areas = [float(item.area) for item in geometries]
    total_component_area = sum(areas)
    union = safe_unary_union(geometries)
    union_area = float(union.area) if union is not None and not union.is_empty else 0.0
    denominator = float(site_area_m2 or props.get("benchmark_site_area_m2") or union_area or 1.0)
    coverage = union_area / max(denominator, 1e-9)
    geometric_dominant = max(areas, default=0.0) / max(total_component_area, 1e-9)
    dominant = geometric_dominant
    roles = [str(item.get("role") or "").lower() for item in records]
    groups = ROLE_GROUPS.get(profile_id, ())
    role_projection = project_spatial_roles(feature)
    if profile_id == "neighborhood_living":
        role_hits = [
            bool(role_projection["primary_mass_present"]),
            bool(role_projection["active_ground_mass_present"]),
            bool(role_projection["public_spatial_gesture_present"]),
        ]
    else:
        role_hits = [any(any(token in role for token in group) for role in roles) for group in groups]
    role_score = sum(role_hits) / len(role_hits) if role_hits else 0.6
    top_levels = {round(float(item.get("top_height") or 0.0), 2) for item in records}
    bottom_levels = {round(float(item.get("bottom_height") or 0.0), 2) for item in records}
    hierarchy_score = min(1.0, (len(top_levels) - 1) / 2 + (0.2 if len(bottom_levels) > 1 else 0.0))
    signature = props.get("source_signature") if isinstance(props.get("source_signature"), dict) else {}
    coherence = signature.get("coherence_evidence") if isinstance(signature.get("coherence_evidence"), dict) else {}
    continuous_surface = (
        signature.get("continuous_surface_evidence")
        if isinstance(signature.get("continuous_surface_evidence"), dict)
        else {}
    )
    profiled_patch_count = int(continuous_surface.get("profiled_volume_count") or 0)
    single_solid_profiled_field = bool(
        len(geometries) == 1
        and continuous_surface.get("hard_pass")
        and profiled_patch_count >= 2
    )
    if single_solid_profiled_field:
        # The legal/FAR proxy is deliberately one watertight union, while the
        # executable roof field retains distinct trunk/arm patches.  Use those
        # geometry patches for hierarchy rather than penalizing the clean
        # solid as a monolithic box.
        dominant = 1.0 / profiled_patch_count
        hierarchy_score = max(hierarchy_score, min(1.0, (profiled_patch_count - 1) / 2.0))
    dominant_score = _range_score(dominant, DOMINANT_RANGES.get(profile_id, (0.3, 0.85)))
    if bool(coherence.get("intentional_cluster_exception")):
        # A balanced 3-4 member field intentionally has no 38% dominant
        # object. Judge its hierarchy by the expected 1/n share rather than a
        # monolithic-building range; all other spatial hard gates still bind.
        dominant_score = max(dominant_score, _range_score(dominant, (0.20, 0.42)))
    coverage_score = _range_score(coverage, COVERAGE_RANGES.get(profile_id, (0.2, 0.85)))
    coherence_score = float(coherence.get("score") or 0.0)
    score = role_score * 0.34 + dominant_score * 0.20 + coverage_score * 0.18 + hierarchy_score * 0.14 + coherence_score * 0.14
    evidence = {
        "schema_version": "arr.maas.program_spatial_evidence.v1",
        "profile_id": profile_id,
        "roles": roles,
        "required_role_hits": role_hits,
        "spatial_role_projection": role_projection,
        "role_coverage_score": round(role_score, 3),
        "dominant_component_ratio": round(dominant, 3),
        "geometric_dominant_component_ratio": round(geometric_dominant, 3),
        "profiled_design_patch_count": profiled_patch_count,
        "single_solid_profiled_field": single_solid_profiled_field,
        "dominant_ratio_score": round(dominant_score, 3),
        "site_coverage_ratio": round(coverage, 3),
        "site_coverage_score": round(coverage_score, 3),
        "height_level_count": len(top_levels),
        "section_level_count": len(bottom_levels),
        "hierarchy_score": round(hierarchy_score, 3),
        "coherence_score": round(coherence_score, 3),
        "architectural_score": round(max(0.0, min(1.0, score)), 3),
        "hard_pass": bool(all(role_hits) and dominant_score >= 0.55 and coverage_score >= 0.55 and hierarchy_score >= 0.5 and coherence.get("hard_pass", False)),
    }
    props["program_spatial_evidence"] = evidence
    return evidence


def _range_score(value: float, target: tuple[float, float]) -> float:
    low, high = target
    if low <= value <= high:
        center = (low + high) / 2
        half = max((high - low) / 2, 1e-9)
        return max(0.75, 1.0 - abs(value - center) / half * 0.25)
    distance = low - value if value < low else value - high
    return max(0.0, 0.75 - distance * 3.0)


__all__ = ["attach_program_spatial_evidence"]
