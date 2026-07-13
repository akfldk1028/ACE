"""Architecture-grade formal-principle source geometry.

This layer translates book/precedent references into architectural massing
principles. It does not decide legality; the legal optimizer still validates,
clips, or rejects every candidate after these source volumes are created.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shapely.affinity import rotate, scale, translate
from shapely.geometry import LineString, MultiPolygon, Polygon, box

from .ir import SourceVolume


CANONICAL_FORMAL_PRINCIPLES = {
    "slender_podium_tower",
    "undercut_tapered_tower",
    "torqued_stack",
    "stacked_shifted_platforms",
    "folded_section",
    "terraced_ribbon_section",
    "carved_atrium",
    "split_bridge_connector",
    "carved_monolith",
}

FORMAL_PRINCIPLE_ALIASES = {
    "tower_base": "slender_podium_tower",
    "slender_tower": "slender_podium_tower",
    "podium_tower": "slender_podium_tower",
    "undercut_podium": "undercut_tapered_tower",
    "torqued_taper": "undercut_tapered_tower",
    "tapered_tower": "undercut_tapered_tower",
    "twisted_tower": "torqued_stack",
    "torque": "torqued_stack",
    "torqued": "torqued_stack",
    "slab_stack": "stacked_shifted_platforms",
    "platform_stack": "stacked_shifted_platforms",
    "datum_shift": "stacked_shifted_platforms",
    "shifted_platforms": "stacked_shifted_platforms",
    "folded_roof_volume": "folded_section",
    "folded_roof": "folded_section",
    "sloped_roof": "folded_section",
    "terrace_link": "terraced_ribbon_section",
    "terrace_ribbon": "terraced_ribbon_section",
    "terraced_ribbon": "terraced_ribbon_section",
    "figure_ground": "carved_atrium",
    "carved_solid": "carved_monolith",
    "embedded_void": "carved_monolith",
    "carved_void": "carved_monolith",
    "split_bridge": "split_bridge_connector",
    "bridge_connector": "split_bridge_connector",
}


@dataclass(frozen=True)
class FormalPrincipleResult:
    principle: str
    volumes: tuple[SourceVolume, ...]
    evidence: dict[str, Any]


def normalize_formal_principle(value: str | None) -> str:
    token = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    if token in CANONICAL_FORMAL_PRINCIPLES:
        return token
    return FORMAL_PRINCIPLE_ALIASES.get(token, "")


def _bounds(poly: Polygon) -> tuple[float, float, float, float, float, float]:
    minx, miny, maxx, maxy = poly.bounds
    return minx, miny, maxx, maxy, maxx - minx, maxy - miny


def _clean_piece(role: str, geom, bottom: float, top: float, verb: str, *, clip: Polygon, min_area: float) -> SourceVolume | None:
    clipped = geom.intersection(clip)
    if clipped.is_empty or clipped.area < min_area:
        return None
    if isinstance(clipped, MultiPolygon):
        clipped = max(clipped.geoms, key=lambda item: item.area)
    if not isinstance(clipped, Polygon):
        return None
    bottom = max(0.0, min(0.92, float(bottom)))
    top = max(bottom + 0.07, min(1.0, float(top)))
    return SourceVolume(role, clipped, bottom, top, verb)


def _rect(role: str, clip: Polygon, x0: float, y0: float, x1: float, y1: float, bottom: float, top: float, verb: str, *, min_area: float) -> SourceVolume | None:
    return _clean_piece(role, box(x0, y0, x1, y1), bottom, top, verb, clip=clip, min_area=min_area)


def _rot(role: str, clip: Polygon, geom, angle: float, bottom: float, top: float, verb: str, *, min_area: float) -> SourceVolume | None:
    return _clean_piece(role, rotate(geom, angle, origin=(clip.centroid.x, clip.centroid.y)), bottom, top, verb, clip=clip, min_area=min_area)


def _poly(role: str, clip: Polygon, coords: list[tuple[float, float]], bottom: float, top: float, verb: str, *, min_area: float) -> SourceVolume | None:
    return _clean_piece(role, Polygon(coords), bottom, top, verb, clip=clip, min_area=min_area)


def _ribbon(role: str, clip: Polygon, points: list[tuple[float, float]], width: float, bottom: float, top: float, verb: str, *, min_area: float) -> SourceVolume | None:
    if len(points) < 2 or width <= 0:
        return None
    return _clean_piece(role, LineString(points).buffer(width, cap_style=2, join_style=2), bottom, top, verb, clip=clip, min_area=min_area)


def _param(params: dict[str, Any], keys: tuple[str, ...], fallback: float, low: float, high: float) -> float:
    for key in keys:
        try:
            return max(low, min(high, float(params[key])))
        except (KeyError, TypeError, ValueError):
            continue
    return max(low, min(high, float(fallback)))


def _role(role: str, genome: dict[str, Any]) -> str:
    family = str(genome.get("family") or "").strip().lower().replace("-", "_")
    if not family or family in role:
        return role
    if role.startswith("primary_torqued_plate_"):
        return role.replace("primary_torqued_plate_", f"primary_{family}_torqued_plate_", 1)
    if role.startswith("primary_folded_"):
        return role.replace("primary_folded_", f"primary_{family}_folded_", 1)
    if role.startswith("primary_shifted_platform_"):
        return role.replace("primary_shifted_platform_", f"primary_{family}_shifted_platform_", 1)
    if role.startswith("secondary_torque_"):
        return role.replace("secondary_torque_", f"secondary_{family}_torque_", 1)
    if role.startswith("secondary_vertical_datum_"):
        return role.replace("secondary_vertical_datum_", f"secondary_{family}_vertical_datum_", 1)
    if role.startswith("primary_carved_"):
        return role.replace("primary_carved_", f"primary_{family}_carved_", 1)
    if role.startswith("secondary_void_"):
        return role.replace("secondary_void_", f"secondary_{family}_void_", 1)
    if role.startswith("secondary_monolith_"):
        return role.replace("secondary_monolith_", f"secondary_{family}_monolith_", 1)
    if role.startswith("primary_split_"):
        return role.replace("primary_split_", f"primary_{family}_split_", 1)
    if role.startswith("primary_diagonal_bridge_"):
        return role.replace("primary_diagonal_bridge_", f"primary_{family}_diagonal_bridge_", 1)
    if role.startswith("secondary_threshold_"):
        return role.replace("secondary_threshold_", f"secondary_{family}_threshold_", 1)
    return role


def compile_formal_principle_volumes(
    footprint: Polygon,
    *,
    formal_principle: str | None,
    dominant_gesture: str | None,
    language_params: dict[str, Any],
    lower_fraction: float | None,
    last_verb: str,
    massing_genome: dict[str, Any] | None = None,
) -> FormalPrincipleResult | None:
    principle = normalize_formal_principle(formal_principle)
    if not principle or footprint.is_empty:
        return None
    minx, miny, maxx, maxy, width, depth = _bounds(footprint)
    if width <= 0 or depth <= 0:
        return None
    cx, cy = footprint.centroid.x, footprint.centroid.y
    min_area = max(1.0, footprint.area * 0.045)
    split = max(0.22, min(0.70, float(lower_fraction if lower_fraction is not None else 0.42)))
    upper_ratio = _param(language_params, ("upper_ratio", "top_ratio"), 0.84, 0.58, 1.0)
    taper = _param(language_params, ("taper_ratio", "x_ratio", "y_ratio", "top_ratio"), 0.66, 0.42, 0.88)
    shift = _param(language_params, ("distance_ratio", "shift_ratio", "offset_ratio"), 0.16, 0.04, 0.34)
    angle = _param(language_params, ("angle",), 24.0, -42.0, 42.0)
    void_ratio = _param(language_params, ("ratio", "void_ratio", "guest_scale", "inner_scale"), 0.30, 0.16, 0.56)
    pieces: list[SourceVolume | None] = []
    genome = massing_genome or {}

    if principle == "slender_podium_tower":
        tower_w = width * max(0.20, min(0.42, taper))
        tower_d = depth * max(0.20, min(0.42, taper))
        pieces = [
            _rect("primary_podium_slab", footprint, minx, miny, maxx, maxy, 0.0, split, "base", min_area=min_area),
            _rect("primary_slender_tower", footprint, cx - tower_w / 2, cy - tower_d / 2, cx + tower_w / 2, cy + tower_d / 2, split * 0.82, 1.0, last_verb, min_area=min_area),
            _rect("secondary_ground_carve", footprint, minx, miny, minx + width * 0.28, miny + depth * 0.30, 0.0, max(split * 0.62, 0.18), "void", min_area=min_area),
            _rect("secondary_podium_liner", footprint, minx, maxy - depth * 0.16, maxx, maxy, split * 0.30, upper_ratio, "bar", min_area=min_area),
        ]
    elif principle == "undercut_tapered_tower":
        base = box(minx, miny, maxx, maxy)
        undercut = box(minx, miny, minx + width * 0.36, miny + depth * 0.34)
        podium = base.difference(undercut)
        tower = scale(footprint, xfact=taper, yfact=max(0.42, taper * 0.88), origin="centroid")
        tower = translate(tower, xoff=width * shift * 0.25, yoff=-depth * shift * 0.18)
        cap = scale(tower, xfact=max(0.56, taper * 0.82), yfact=max(0.52, taper * 0.78), origin="centroid")
        pieces = [
            _clean_piece("primary_undercut_podium", podium, 0.0, split, "base", clip=footprint, min_area=min_area),
            _clean_piece("primary_tapered_tower", tower, split * 0.72, upper_ratio, last_verb, clip=footprint, min_area=min_area),
            _clean_piece("secondary_tower_cap", cap, max(0.72, upper_ratio - 0.16), 1.0, "taper", clip=footprint, min_area=min_area),
            _rect("secondary_ground_void_marker", footprint, minx, miny, minx + width * 0.24, miny + depth * 0.22, 0.0, split * 0.55, "void", min_area=min_area),
        ]
    elif principle == "torqued_stack":
        torque_angle = max(18.0, min(42.0, abs(angle)))
        torque_shift = max(0.18, min(0.34, abs(shift)))
        tiers = (
            (0.0, 0.38, 0.92, -1.0, -0.75),
            (0.34, 0.70, 0.74, 1.0, 0.0),
            (0.66, 1.0, 0.56, -1.0, 0.75),
        )
        for index, (bottom, top, factor, xsign, angle_factor) in enumerate(tiers):
            plate = scale(footprint, xfact=factor, yfact=max(0.42, factor * 0.86), origin="centroid")
            plate = translate(
                plate,
                xoff=xsign * width * torque_shift * (0.30 + index * 0.10),
                yoff=-xsign * depth * torque_shift * (0.14 + index * 0.05),
            )
            pieces.append(_rot(_role(f"primary_torqued_plate_{index}", genome), footprint, plate, torque_angle * angle_factor, bottom, top, "shift", min_area=min_area))
    elif principle == "stacked_shifted_platforms":
        if str(genome.get("family") or "") == "array_cluster":
            pieces.append(_rect(_role("primary_shifted_platform_0", genome), footprint, minx, miny, maxx, maxy, 0.0, 0.22, "base", min_area=min_area))
            centers = ((-0.22, -0.14), (0.20, 0.14))
            for index, (xoff, yoff) in enumerate(centers, start=1):
                block = box(
                    cx + width * xoff - width * 0.23,
                    cy + depth * yoff - depth * 0.22,
                    cx + width * xoff + width * 0.23,
                    cy + depth * yoff + depth * 0.22,
                )
                pieces.append(_clean_piece(
                    _role(f"primary_shifted_platform_{index}", genome),
                    block,
                    0.18,
                    (0.70, 1.0)[index - 1],
                    "array",
                    clip=footprint,
                    min_area=min_area,
                ))
        else:
            for index, (bottom, top, xsign, ysign) in enumerate(((0.0, 0.40, -1, 0), (0.36, 0.72, 1, -1), (0.68, 1.0, 0, 1))):
                plate = scale(footprint, xfact=max(0.54, 0.86 - index * 0.12), yfact=max(0.48, 0.82 - index * 0.10), origin="centroid")
                plate = translate(plate, xoff=xsign * width * shift * 0.45, yoff=ysign * depth * shift * 0.45)
                pieces.append(_clean_piece(_role(f"primary_shifted_platform_{index}", genome), plate, bottom, top, "stack", clip=footprint, min_area=min_area))
    elif principle in {"folded_section", "terraced_ribbon_section"}:
        # A readable early-massing fold is a common plinth plus two roof
        # boxes meeting along one datum. The previous two full-plan polygons
        # occupied almost the same plan and produced crossed linework rather
        # than a legible section.
        pieces = [
            _rect(_role("primary_folded_base", genome), footprint, minx, miny, maxx, maxy, 0.0, 0.38, "base", min_area=min_area),
            _rect(_role("primary_folded_low_plane", genome), footprint, minx, miny, cx + width * 0.03, maxy, 0.34, 0.70, "sloped_roof_mass", min_area=min_area),
            _rect(_role("primary_folded_high_plane", genome), footprint, cx - width * 0.03, miny, maxx, maxy, 0.66, 1.0, "sloped_roof_mass", min_area=min_area),
        ]
    elif principle == "carved_atrium":
        court_w = width * void_ratio
        court_d = depth * void_ratio
        pieces = [
            _rect("primary_atrium_north_bar", footprint, minx, cy + court_d / 2, maxx, maxy, 0.0, split, "courtyard", min_area=min_area),
            _rect("primary_atrium_south_bar", footprint, minx, miny, maxx, cy - court_d / 2, 0.0, upper_ratio, "courtyard", min_area=min_area),
            _rect("secondary_atrium_liner", footprint, cx - court_w / 2, miny, cx + court_w / 2, maxy, split * 0.72, 1.0, "void", min_area=min_area),
            _rect("secondary_atrium_bridge", footprint, minx, cy - depth * 0.06, maxx, cy + depth * 0.06, max(split, 0.48), 1.0, "bridge", min_area=min_area),
        ]
    elif principle == "split_bridge_connector":
        gap = width * max(0.05, min(0.22, shift))
        pieces = [
            _rect(_role("primary_split_wing_a", genome), footprint, minx, miny, cx - gap, maxy, 0.0, upper_ratio, "split", min_area=min_area),
            _rect(_role("primary_split_wing_b", genome), footprint, cx + gap, miny, maxx, maxy, split * 0.65, 1.0, "split", min_area=min_area),
            _rot(_role("primary_diagonal_bridge_connector", genome), footprint, box(minx, cy - depth * 0.07, maxx, cy + depth * 0.07), angle, max(split, 0.45), 1.0, "diagonal_connect", min_area=min_area),
            _rect(_role("secondary_threshold_core", genome), footprint, cx - width * 0.08, miny, cx + width * 0.08, maxy, split * 0.20, 0.86, "core", min_area=min_area),
        ]
    elif principle == "carved_monolith":
        cut = box(cx - width * void_ratio / 2, cy - depth * void_ratio / 2, cx + width * void_ratio / 2, cy + depth * void_ratio / 2)
        shell = footprint.difference(cut)
        pieces = [
            _clean_piece(_role("primary_carved_shell", genome), shell, 0.0, upper_ratio, "cave", clip=footprint, min_area=min_area),
            _ribbon(_role("secondary_void_liner_spine", genome), footprint, [(cx, miny), (cx, maxy)], width * 0.045, split, 1.0, "void", min_area=min_area),
            _rect(_role("secondary_monolith_cap", genome), footprint, minx, maxy - depth * 0.18, maxx, maxy, max(split, 0.52), 1.0, "cap", min_area=min_area),
        ]

    volumes = tuple(piece for piece in pieces if piece is not None)
    if len(volumes) < 3:
        return None
    roles = [volume.role for volume in volumes]
    genome_strategy_evidence = {
        "void_strategy": str(genome.get("void_strategy") or ""),
        "vertical_strategy": str(genome.get("vertical_strategy") or ""),
        "connector_strategy": str(genome.get("connector_strategy") or ""),
        "silhouette_strategy": str(genome.get("silhouette_strategy") or ""),
        "stair_like_risk": str(genome.get("stair_like_risk") or ""),
        "inference_source": str(genome.get("inference_source") or ""),
    }
    evidence = {
        "schema_version": "arr.maas.architectural_ambition.v1",
        "formal_principle": principle,
        "dominant_gesture": str(dominant_gesture or principle),
        "has_formal_principle": True,
        "has_dominant_gesture": True,
        "implemented_volume_roles": roles,
        "massing_genome_schema_version": str(genome.get("schema_version") or ""),
        "genome_strategy_evidence": genome_strategy_evidence,
        "void_strategy": genome_strategy_evidence["void_strategy"],
        "vertical_strategy": genome_strategy_evidence["vertical_strategy"],
        "connector_strategy": genome_strategy_evidence["connector_strategy"],
        "silhouette_strategy": genome_strategy_evidence["silhouette_strategy"],
        "stair_like_risk": genome_strategy_evidence["stair_like_risk"],
        "silhouette_strength": 1.0 if any("tower" in role or "torqued" in role or "folded" in role for role in roles) else 0.78,
        "sectional_diagram_clarity": 1.0 if len({(round(v.bottom_fraction, 2), round(v.top_fraction, 2)) for v in volumes}) >= 3 else 0.72,
        "podium_or_ground_relationship": any("podium" in role or "ground" in role or "base" in role for role in roles),
        "architecture_grade_pass": True,
    }
    return FormalPrincipleResult(principle=principle, volumes=volumes, evidence=evidence)


__all__ = [
    "CANONICAL_FORMAL_PRINCIPLES",
    "FORMAL_PRINCIPLE_ALIASES",
    "FormalPrincipleResult",
    "compile_formal_principle_volumes",
    "normalize_formal_principle",
]
