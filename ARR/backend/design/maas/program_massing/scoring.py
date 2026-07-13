"""Quantitative program-fit evidence for legal MAAS candidates."""

from __future__ import annotations

from typing import Any

from .profiles import resolve_program_profile
from .spatial_evaluation import attach_program_spatial_evidence


def attach_program_massing_evidence(feature: dict[str, Any], *, building_type: str) -> dict[str, Any]:
    props = feature.setdefault("properties", {})
    profile = resolve_program_profile(building_type)
    signature = props.get("source_signature") if isinstance(props.get("source_signature"), dict) else {}
    family = str(signature.get("family") or props.get("operator_family") or props.get("typology_family") or "")
    volumes = props.get("mass_volumes") if isinstance(props.get("mass_volumes"), list) else []
    volume_count = len(volumes) or int(signature.get("volume_count") or 1)
    floors = int(props.get("num_floors") or 1)
    volume_min, volume_max = [int(value) for value in profile.get("target_volume_range", [1, 4])]
    floor_min, floor_max = [int(value) for value in profile.get("target_floor_range", [1, 40])]
    volume_fit = 1.0 if volume_min <= volume_count <= volume_max else max(0.0, 1.0 - min(abs(volume_count - volume_min), abs(volume_count - volume_max)) * 0.28)
    floor_fit = 1.0 if floor_min <= floors <= floor_max else max(0.0, 1.0 - min(abs(floors - floor_min), abs(floors - floor_max)) * 0.12)
    preferred = [str(item) for item in profile.get("preferred_families") or []]
    family_fit = 1.0 if any(token in family for token in preferred) else (0.55 if preferred else 0.75)
    coherence = signature.get("coherence_evidence") if isinstance(signature.get("coherence_evidence"), dict) else {}
    coherence_fit = float(coherence.get("score") or 0.65)
    spatial = attach_program_spatial_evidence(
        feature,
        building_type=building_type,
        site_area_m2=props.get("benchmark_site_area_m2"),
    )
    spatial_fit = float(spatial.get("architectural_score") or 0.0)
    score = volume_fit * 0.14 + floor_fit * 0.14 + family_fit * 0.18 + coherence_fit * 0.16 + spatial_fit * 0.38
    evidence = {
        "schema_version": "arr.maas.program_massing_evidence.v1",
        "profile_id": profile["id"],
        "building_type": building_type,
        "design_intent": profile["design_intent"],
        "family": family,
        "preferred_families": preferred,
        "volume_count": volume_count,
        "floor_count": floors,
        "volume_fit": round(volume_fit, 3),
        "floor_fit": round(floor_fit, 3),
        "family_fit": round(family_fit, 3),
        "coherence_fit": round(coherence_fit, 3),
        "spatial_fit": round(spatial_fit, 3),
        "program_fit_score": round(max(0.0, min(1.0, score)), 3),
        "hard_pass": bool(
            volume_fit >= 0.44
            and floor_fit >= 0.40
            and bool(coherence.get("hard_pass", coherence_fit >= 0.70))
            and bool(spatial.get("hard_pass"))
        ),
    }
    props["program_massing_evidence"] = evidence
    model = props.get("maas_model") if isinstance(props.get("maas_model"), dict) else None
    if model is not None:
        model["program_massing_evidence"] = evidence
    return evidence


__all__ = ["attach_program_massing_evidence"]
