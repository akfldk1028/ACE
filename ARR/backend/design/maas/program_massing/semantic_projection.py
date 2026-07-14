"""Project anonymous source geometry into program-relevant spatial roles.

The source compiler deliberately describes formal operations (bend, court,
fold, terrace).  Program evaluation must not require those volumes to carry a
small, pre-agreed list of role names: that collapses an open language archive
back onto a few hand-authored seeds.  This module derives roles from geometry
and section relations, so reference/VLM-authored graphs remain evaluable.
"""

from __future__ import annotations

from typing import Any

from .geometry_safety import repaired_volume_records, safe_unary_union


def project_spatial_roles(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    repaired = repaired_volume_records(feature)
    records = [record for record, _ in repaired]
    geometries = [geometry for _, geometry in repaired]
    areas = [float(geometry.area) for geometry in geometries]
    total = sum(areas)
    primary_index = max(range(len(areas)), key=areas.__getitem__) if areas else None
    grounded = [
        index for index, item in enumerate(records)
        if float(item.get("bottom_height") or 0.0) <= 0.02
    ]
    significant_grounded = [index for index in grounded if areas[index] / max(total, 1e-9) >= 0.10]
    top_levels = {round(float(item.get("top_height") or 0.0), 2) for item in records}
    bottom_levels = {round(float(item.get("bottom_height") or 0.0), 2) for item in records}
    union = safe_unary_union(geometries)
    envelope_void_ratio = 0.0
    if union is not None and not union.is_empty and union.envelope.area > 0:
        envelope_void_ratio = max(0.0, 1.0 - float(union.area) / float(union.envelope.area))
    non_rectilinear = sum(
        1 for geometry in geometries
        if hasattr(geometry, "exterior") and len(list(geometry.exterior.coords)) - 1 > 5
    )
    profiled_roof = any(
        isinstance(item, dict) and "roof" in str(item.get("surface_type") or "")
        and str(item.get("surface_type") or "").startswith("profiled_")
        for item in props.get("source_surfaces") or []
    )
    # A public spatial gesture is measurable as a court/canyon in plan, a
    # legible sectional hierarchy, or a deliberately profiled/non-rectilinear
    # envelope.  No topology or volume-name whitelist is involved.
    public_gesture = bool(
        envelope_void_ratio >= 0.12
        or len(top_levels) >= 2
        or len(bottom_levels) >= 2
        or profiled_roof
        or non_rectilinear > 0
    )
    return {
        "schema_version": "arr.maas.spatial_role_projection.v1",
        "method": "geometry_relations_not_role_names",
        "primary_component_index": primary_index,
        "primary_mass_present": primary_index is not None,
        "grounded_component_indices": grounded,
        "active_ground_mass_present": bool(significant_grounded),
        "secondary_mass_present": len(records) >= 2,
        "public_spatial_gesture_present": public_gesture,
        "envelope_void_ratio": round(envelope_void_ratio, 3),
        "height_level_count": len(top_levels),
        "section_level_count": len(bottom_levels),
        "non_rectilinear_component_count": non_rectilinear,
        "profiled_roof_present": profiled_roof,
    }


__all__ = ["project_spatial_roles"]
