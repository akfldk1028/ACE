"""Fast, measured BOOK-operation portfolios on one real parcel.

This benchmark is intentionally bounded: it compiles typed operations over
program assemblies once, filters by clean/program gates, and performs measured
shape-diverse selection.  It is the synchronous diagnostic counterpart to the
slower evolutionary/VLM loop, not a replacement for legal/FAR/parking repair.
"""

from __future__ import annotations

import json
import hashlib
import os
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, replace
from math import pi, sqrt
from pathlib import Path
from time import perf_counter
from typing import Any

from PIL import Image
from shapely.errors import GEOSException
from shapely.geometry import Polygon

from design.maas.geometry_language import (
    GeometryOutcomeGraph,
    GeometryProgram,
    apply_book_projection_to_geometry_program,
    apply_geometry_edits,
    architectural_shape_programs,
    reference_language_programs,
    replace_source_dominant_with_geometry_program,
    openai_vlm_geometry_critic,
    retrieve_geometry_reference_matches,
    run_geometry_program_a2a_loop,
    synthesize_architectural_programs,
    synthesis_requests_from_program_profile,
)
from design.maas.grammar.verb_sequence import VerbSequence
from design.maas.program_massing import (
    ProgramSectionGraphEdit,
    book_sentence_variants,
    compose_program_with_book_operations,
    mutate_program_section_sequence,
    program_reference_contract,
    program_seed_sequences,
    resolve_program_profile,
)
from design.maas.program_massing.assembly import program_component_chassis
from design.maas.program_massing.benchmark import render_archive_sheet
from design.maas.program_massing.morphology import (
    intrinsic_section_profile_distance,
    intrinsic_shape_distance,
    intrinsic_silhouette_distance,
)
from design.maas.program_massing.scoring import attach_program_massing_evidence
from design.maas.program_massing.search import program_seed_variants, source_feature
from design.maas.source_geometry import compile_sequence_to_source_mass

from .registry import build_book_language_registry
from .semantics import BASE_VOLUME_FRACTIONS
from .downstream_hard_gate import (
    LegalGenerationContext,
    build_legal_generation_context,
    evaluate_accepted_sources_downstream,
    fit_source_to_sunlight_field,
    generation_site_at_height,
)


PROGRAMS = (
    ("neighborhood", "근린생활시설", 15.0, 5),
    ("gymnasium", "체육관", 18.0, 3),
    ("cultural", "미술관", 15.0, 4),
)


@dataclass(frozen=True)
class _Candidate:
    principle_id: str
    principle_kind: str
    operation: str
    sequence: VerbSequence
    source: Any
    feature: dict[str, Any]
    score: float


def _distance(left: _Candidate, right: _Candidate) -> float:
    volume, plan = intrinsic_shape_distance(left.source, right.source)
    return min(1.0, float(volume) * 0.72 + float(plan) * 0.28)


def _silhouette_distance(left: _Candidate, right: _Candidate) -> float:
    visual = float(intrinsic_silhouette_distance(left.source, right.source))
    left_recursive = bool((left.source.metadata.get("geometry_program_bridge_evidence") or {}).get("status") == "materialized")
    right_recursive = bool((right.source.metadata.get("geometry_program_bridge_evidence") or {}).get("status") == "materialized")
    if left_recursive or right_recursive:
        # The full manifold mesh already contributes top/front/side surfaces.
        # Mixing in the legacy seed's section controls made genuinely distinct
        # recursive solids appear 50% identical and collapsed selection.
        return visual
    section = float(intrinsic_section_profile_distance(left.source, right.source))
    left_section = left.source.metadata.get("program_section_graph_evidence") or {}
    right_section = right.source.metadata.get("program_section_graph_evidence") or {}
    has_profiles = bool(
        isinstance(left_section, dict) and left_section.get("materialized_nodes")
        and isinstance(right_section, dict) and right_section.get("materialized_nodes")
    )
    return min(1.0, visual * 0.50 + section * 0.50) if has_profiles else visual


def _scope_key(candidate: _Candidate) -> str:
    evidence = candidate.source.metadata.get("program_book_projection_evidence") or {}
    scope = evidence.get("scope") if isinstance(evidence, dict) else {}
    return str(scope.get("base_volume_label") or "1/1") if isinstance(scope, dict) else "1/1"


def _seed_family(candidate: _Candidate) -> str:
    return candidate.sequence.name.split("__book_", 1)[0].split("__search_", 1)[0]


def _section_family(candidate: _Candidate) -> str:
    geometry_family = _geometry_program_family(candidate)
    if geometry_family:
        morphology = _solid_morphology_metrics(candidate)
        if morphology.get("profiled_section_family"):
            return f"recursive_section:{morphology['profiled_section_family']}"
        return f"recursive:{morphology['phenotype']}"
    evidence = candidate.source.metadata.get("program_section_graph_evidence") or {}
    nodes = evidence.get("materialized_nodes") if isinstance(evidence, dict) else ()
    operators = tuple(
        str(node.get("operator") or "")
        for node in (nodes or ())
        if isinstance(node, dict) and node.get("operator")
    )
    if operators:
        graph_operators = set(evidence.get("graph_operators") or ())
        modifiers = graph_operators & {"carved_entry", "daylight_monitor"}
        return "+".join(sorted(set(operators) | modifiers))
    signature = candidate.source.signature()
    return str(signature.get("formal_principle") or signature.get("family") or "flat_proxy")


def _roof_archetype(candidate: _Candidate) -> str:
    """Collapse decorative graph variants into their visible roof genotype."""
    geometry_family = _geometry_program_family(candidate)
    if geometry_family:
        morphology = _solid_morphology_metrics(candidate)
        if morphology.get("profiled_section_family"):
            return f"recursive_roof:{morphology['profiled_section_family']}"
        return f"recursive:{morphology['phenotype']}"
    evidence = candidate.source.metadata.get("program_section_graph_evidence") or {}
    operators = set(evidence.get("graph_operators") or ()) if isinstance(evidence, dict) else set()
    for operator, archetype in (
        ("ridge_roof", "gable_ridge"),
        ("flat_roof", "flat_box"),
        ("shed_roof", "mono_shed"),
        ("barrel_roof", "barrel_vault"),
        ("folded_roof", "folded"),
        ("sawtooth_roof", "sawtooth"),
        ("stepped_section", "stepped"),
    ):
        if operator in operators:
            return archetype
    return "flat_proxy"


def _chassis_family(candidate: _Candidate) -> str:
    """Return the normalized program-plan chassis independently of its roof."""
    geometry_family = _geometry_program_family(candidate)
    if geometry_family:
        program = candidate.source.metadata.get("geometry_program") or {}
        metadata = program.get("metadata") if isinstance(program, dict) else {}
        return f"recursive_base:{str((metadata or {}).get('base_seed') or 'unknown')}"
    return program_component_chassis(candidate.sequence.name) or "generic_chassis"


def _geometry_program_family(candidate: _Candidate) -> str:
    evidence = candidate.source.metadata.get("geometry_program_bridge_evidence") or {}
    if not isinstance(evidence, dict) or evidence.get("status") != "materialized":
        return ""
    program = candidate.source.metadata.get("geometry_program") or {}
    metadata = program.get("metadata") if isinstance(program, dict) else {}
    return str(
        (metadata or {}).get("family")
        or candidate.source.metadata.get("family")
        or "recursive_solid"
    )


def _geometry_program_metadata(candidate: _Candidate) -> dict[str, Any]:
    program = candidate.source.metadata.get("geometry_program") or {}
    metadata = program.get("metadata") if isinstance(program, dict) else {}
    return metadata if isinstance(metadata, dict) else {}


def _vlm_reviewed_program_candidate(candidate: _Candidate) -> bool:
    metadata = _geometry_program_metadata(candidate)
    return bool(
        metadata.get("vlm_geometry_critic_active")
        and metadata.get("vlm_program_fit_hard_pass")
    )


def _solid_morphology_metrics(candidate: Any) -> dict[str, Any]:
    """Measure the rendered recursive mesh, not its family label."""
    source = candidate.source if hasattr(candidate, "source") else candidate
    cached = source.metadata.get("measured_solid_morphology")
    if isinstance(cached, dict):
        return cached
    total_area = horizontal_area = vertical_area = sloped_area = 0.0
    dimensional_context = source.metadata.get("program_dimensional_context") or {}
    legal_context = source.metadata.get("legal_generation_context_evidence") or {}
    height_scale = float(
        dimensional_context.get("effective_height_m")
        or legal_context.get("requested_program_height_m")
        or 1.0
    )
    normal_bins: set[tuple[int, int, int]] = set()
    horizontal_levels: set[int] = set()
    triangle_count = 0
    z_values: list[float] = []
    for surface in source.surfaces:
        if surface.surface_type != "profiled_recursive_solid_mesh" or len(surface.vertices_m) < 3:
            continue
        a, b, c = tuple(
            (float(vertex[0]), float(vertex[1]), float(vertex[2]) * height_scale)
            for vertex in surface.vertices_m[:3]
        )
        z_values.extend((float(a[2]), float(b[2]), float(c[2])))
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        magnitude = sqrt(nx * nx + ny * ny + nz * nz)
        if magnitude <= 1e-12:
            continue
        area = magnitude / 2.0
        nx, ny, nz = nx / magnitude, ny / magnitude, nz / magnitude
        absolute_z = abs(nz)
        total_area += area
        triangle_count += 1
        normal_bins.add((round(nx * 4), round(ny * 4), round(nz * 4)))
        if absolute_z >= 0.90:
            horizontal_area += area
            horizontal_levels.add(round(sum(vertex[2] for vertex in (a, b, c)) / 3.0 * 20))
        elif absolute_z <= 0.12:
            vertical_area += area
        else:
            sloped_area += area
    denominator = max(total_area, 1e-9)
    program = source.metadata.get("geometry_program") or {}
    nodes = program.get("nodes") if isinstance(program, dict) else ()
    operators = {
        str(node.get("operator") or "")
        for node in (nodes or ())
        if isinstance(node, dict)
    }
    curved_intent = bool(operators & {"bend", "bent_bar", "sweep", "inflate", "twist"})
    oblique_intent = bool(operators & {"slice", "clip"})
    stepped_intent = bool(operators & {"setback", "stepped_mass", "terrace", "stack"})
    voided_intent = bool(operators & {"courtyard", "carve_void", "notch", "puncture"})
    winged_intent = bool(operators & {"cross_mass", "split_wing", "radial_array", "mirror_array", "linear_array"})
    sloped_ratio = sloped_area / denominator
    horizontal_ratio = horizontal_area / denominator
    normal_bin_count = len(normal_bins)
    compilation = source.metadata.get("geometry_program_compilation") or {}
    compilation_metrics = compilation.get("metrics") if isinstance(compilation, dict) else {}
    genus = int((compilation_metrics or {}).get("genus") or 0)
    component_count = int((compilation_metrics or {}).get("component_count") or 1)
    footprint = source.footprint
    convex_hull_area = float(footprint.convex_hull.area) if not footprint.is_empty else 0.0
    plan_convexity = float(footprint.area) / max(convex_hull_area, 1e-9)
    upper_area_ratio = (
        float(source.upper_footprint.area) / max(float(footprint.area), 1e-9)
        if source.upper_footprint is not None and not source.upper_footprint.is_empty
        else 1.0
    )
    oriented_plan_aspect = _oriented_aspect(footprint) if not footprint.is_empty else 1.0
    profiled_section_family = next((
        str((node.get("parameters") or {}).get("section_family") or "")
        for node in (nodes or ())
        if isinstance(node, dict) and node.get("operator") == "profiled_hall"
    ), "")
    measured_profiled_hall = bool(
        profiled_section_family
        and oriented_plan_aspect >= 1.45
        and component_count == 1
    )
    horizontal_level_count = len(horizontal_levels)
    wedge_like, pyramidal_like = _section_silhouette_flags(
        sloped_surface_ratio=sloped_ratio,
        upper_area_ratio=upper_area_ratio,
        horizontal_level_count=horizontal_level_count,
        vertical_surface_ratio=vertical_area / denominator,
    )
    collapsed_profiled_tent_like = bool(
        measured_profiled_hall
        and (
            (
                # A usable hall needs a retained occupied enclosure below its
                # roof. If the upper occupied band falls below ten percent and
                # almost no vertical envelope remains, the result is a canopy
                # or tent regardless of how many triangulation levels it has.
                upper_area_ratio < 0.10
                and vertical_area / denominator < 0.03
            )
            or
            (
                upper_area_ratio <= 0.14
                and horizontal_ratio >= 0.90
                and vertical_area / denominator <= 0.03
                and horizontal_level_count >= 6
            )
            or (
                # A second failure mode is a shallow stack of sloped/horizontal
                # caps whose upper occupied plate almost disappears. It reads
                # as a tent even though the roof profile node itself is valid.
                upper_area_ratio <= 0.20
                and horizontal_ratio >= 0.84
                and sloped_ratio <= 0.17
                and vertical_area / denominator <= 0.03
                and horizontal_level_count >= 10
            )
            or (
                # A broader low-vertical barrel/canopy can keep more upper
                # plan area yet still collapse the occupied hall enclosure
                # into one triangular tent silhouette.
                upper_area_ratio <= 0.35
                and horizontal_ratio >= 0.80
                and sloped_ratio <= 0.20
                and vertical_area / denominator <= 0.03
                and horizontal_level_count >= 12
            )
        )
    )
    if measured_profiled_hall:
        # A measured elongated hall with an executable transverse section is
        # not automatically a compact pyramid merely because its ridge
        # reduces upper plan area.  The exception must not hide a collapsed
        # terrace/tent whose upper enclosure has nearly disappeared.
        pyramidal_like = collapsed_profiled_tent_like
        wedge_like = profiled_section_family == "shed"
    degenerate_sheet_like = bool(
        (
            upper_area_ratio < 0.06
            and horizontal_level_count >= 6
        )
        or (
            horizontal_ratio >= 0.94
            and vertical_area / denominator <= 0.01
            and sloped_ratio <= 0.06
            and normal_bin_count >= 20
        )
    )

    # Intent labels are only priors.  The final compiled solid is the
    # authority: a scoped cross/step/notch that disappears inside a union must
    # not make an otherwise calm prism count as a different phenotype.
    measured_void = genus > 0
    measured_wing = (
        winged_intent
        and (plan_convexity <= 0.84 or component_count > 1)
    )
    measured_curve = (
        curved_intent
        and normal_bin_count >= 11
        and (sloped_ratio >= 0.025 or normal_bin_count >= 14)
    )
    measured_step = (
        (not measured_profiled_hall and horizontal_level_count >= 4)
        or (stepped_intent and horizontal_level_count >= 3 and normal_bin_count >= 8)
    )
    measured_prism = (
        genus == 0
        and component_count == 1
        and sloped_ratio < 0.06
        and horizontal_level_count <= 3
        and normal_bin_count <= 10
        and plan_convexity >= 0.88
    )
    measured_oblique = (
        oblique_intent
        and sloped_ratio >= 0.055
        and normal_bin_count <= 10
        and component_count == 1
    )
    section_graph_evidence = source.metadata.get("program_section_graph_evidence") or {}
    section_graph_operators = set(
        section_graph_evidence.get("graph_operators") or ()
    ) if isinstance(section_graph_evidence, dict) else set()
    section_graph_phenotype = _program_section_phenotype(section_graph_operators)
    section_phenotype = (
        {
            "barrel": "curved",
            "sawtooth": "stepped",
            "stepped": "stepped",
            "ridge": "oblique",
            "shed": "oblique",
            "folded": "oblique",
        }.get(profiled_section_family, "oblique")
        if measured_profiled_hall
        else section_graph_phenotype
    )
    # Roof/section language is already measured independently.  Do not let a
    # barrel or sawtooth terminal node erase the body's courtyard, wing,
    # curve, lift or oblique mutation.  Portfolio diversity must compare both
    # axes instead of counting the roof twice.
    if measured_void:
        phenotype = "voided"
    elif measured_wing:
        phenotype = "winged"
    elif measured_oblique:
        phenotype = "oblique"
    elif measured_curve:
        phenotype = "curved"
    elif measured_step:
        phenotype = "stepped"
    elif triangle_count == 0 and section_graph_phenotype:
        # Legacy/program-role solids do not carry recursive-mesh surface tags,
        # but their executable typed section graph still changes the rendered
        # roof.  Treating every one as a prism hid gable/folded/barrel/sawtooth
        # repetition and made the phenotype cap meaningless.
        phenotype = section_graph_phenotype
    elif sloped_ratio >= 0.24:
        phenotype = "oblique"
    elif measured_prism:
        phenotype = "prismatic"
    elif voided_intent and plan_convexity <= 0.82:
        # An open notch has genus zero, but a clearly concave plan still
        # carries a void/carve phenotype in the rendered mass.
        phenotype = "voided"
    elif winged_intent and plan_convexity <= 0.90:
        phenotype = "winged"
    else:
        phenotype = "prismatic"
    result = {
        "phenotype": phenotype,
        "wedge_like": wedge_like,
        "pyramidal_like": pyramidal_like,
        "collapsed_profiled_tent_like": collapsed_profiled_tent_like,
        "body_phenotype": phenotype,
        "section_phenotype": section_phenotype or "none",
        "degenerate_sheet_like": degenerate_sheet_like,
        "horizontal_surface_ratio": round(horizontal_ratio, 4),
        "vertical_surface_ratio": round(vertical_area / denominator, 4),
        "sloped_surface_ratio": round(sloped_ratio, 4),
        "normal_direction_bin_count": normal_bin_count,
        "horizontal_level_count": horizontal_level_count,
        "plan_convexity": round(plan_convexity, 4),
        "upper_area_ratio": round(upper_area_ratio, 4),
        "genus": genus,
        "component_count": component_count,
        "oriented_plan_aspect_ratio": round(oriented_plan_aspect, 4),
        "profiled_section_family": profiled_section_family,
        "measured_profiled_hall": measured_profiled_hall,
        "recursive_triangle_count": triangle_count,
        "solid_height_m": round(max(z_values) - min(z_values), 4) if z_values else 0.0,
        "measurement_authority": (
            "profiled_recursive_solid_mesh"
            if triangle_count
            else "compiled_program_section_graph"
        ),
    }
    source.metadata["measured_solid_morphology"] = result
    return result


def _section_silhouette_flags(
    *,
    sloped_surface_ratio: float,
    upper_area_ratio: float,
    horizontal_level_count: int,
    vertical_surface_ratio: float,
) -> tuple[bool, bool]:
    """Classify visible convergence without topology-based exemptions.

    A carved, multi-component, or highly faceted solid can still read as the
    same wedge/pyramid silhouette on a review board.  Genus, component count,
    and normal-bin complexity therefore must not excuse that repetition.
    """
    wedge_like = bool(
        sloped_surface_ratio >= 0.18
        or (sloped_surface_ratio >= 0.10 and upper_area_ratio <= 0.74)
    )
    pyramidal_like = bool(
        (upper_area_ratio <= 0.68 and horizontal_level_count >= 4)
        or (
            sloped_surface_ratio >= 0.08
            and horizontal_level_count >= 10
            and vertical_surface_ratio <= 0.03
        )
    )
    return wedge_like, pyramidal_like


def _program_form_gate(source: Any, building_type: str) -> dict[str, Any]:
    """Reject measured forms that erase a program's dominant spatial relation.

    This is deliberately relation-based rather than a named-form template.
    A gym may be rectilinear, curved, gabled, folded, sawtoothed, or stepped,
    but its dominant mass must still enclose a usable long-span hall.  A stack
    of horizontal plates with virtually no vertical enclosure cannot satisfy
    that invariant even when its metadata calls it a hall.
    """
    metrics = _solid_morphology_metrics(source)
    program_key = str(building_type or "").strip().lower()
    failures: list[str] = []
    composition = _architectural_articulation_metrics(source)
    evidence: dict[str, Any] = {
        "program": program_key,
        "measured_morphology": metrics,
        "architectural_articulation": composition,
        "rule": "program invariant retained by compiled solid",
    }
    if composition["body_rule_count"] > 2:
        failures.append("architectural_body_rule_budget_exceeded")
    if composition["duplicated_structural_families"]:
        failures.append("architectural_body_rule_family_repeated")
    if "gym" in program_key or "체육" in program_key:
        level_count = int(metrics.get("horizontal_level_count") or 0)
        horizontal_ratio = float(metrics.get("horizontal_surface_ratio") or 0.0)
        vertical_ratio = float(metrics.get("vertical_surface_ratio") or 0.0)
        sloped_ratio = float(metrics.get("sloped_surface_ratio") or 0.0)
        cake_tier_without_hall_enclosure = bool(
            level_count >= 8
            and horizontal_ratio >= 0.78
            and vertical_ratio <= 0.04
        )
        sloped_cascade_without_hall_enclosure = bool(
            level_count >= 4
            and horizontal_ratio >= 0.55
            and sloped_ratio >= 0.28
            and vertical_ratio <= 0.04
        )
        cascade_without_hall_enclosure = bool(
            cake_tier_without_hall_enclosure
            or sloped_cascade_without_hall_enclosure
        )
        evidence["required_relation"] = "dominant clear-span hall with vertical enclosure and legible roof/section"
        evidence["cake_tier_without_hall_enclosure"] = cake_tier_without_hall_enclosure
        evidence["sloped_cascade_without_hall_enclosure"] = sloped_cascade_without_hall_enclosure
        evidence["cascade_without_hall_enclosure"] = cascade_without_hall_enclosure
        measured_profiled_hall = bool(metrics.get("measured_profiled_hall"))
        evidence["measured_profiled_hall"] = measured_profiled_hall
        dominant_enclosure_erased = bool(
            float(metrics.get("upper_area_ratio") or 1.0) < 0.10
            and vertical_ratio < 0.03
        )
        evidence["dominant_enclosure_erased"] = dominant_enclosure_erased
        dimensional_context = (
            source.metadata.get("program_dimensional_context")
            if hasattr(source, "metadata") and isinstance(source.metadata, dict)
            else {}
        ) or {}
        short_span, long_span = _oriented_plan_dimensions(getattr(source, "footprint", None))
        solid_height = float(metrics.get("solid_height_m") or 0.0)
        minimum_span = float(dimensional_context.get("minimum_clear_span_m") or 0.0)
        maximum_height_ratio = float(
            dimensional_context.get("maximum_height_to_clear_span_ratio") or 0.0
        )
        height_to_span = solid_height / max(short_span, 1e-9) if short_span > 0 and solid_height > 0 else 0.0
        evidence["dimensional_context"] = deepcopy(dimensional_context)
        evidence["measured_clear_span_m"] = round(short_span, 3)
        evidence["measured_long_axis_m"] = round(long_span, 3)
        evidence["measured_solid_height_m"] = round(solid_height, 3)
        evidence["height_to_clear_span_ratio"] = round(height_to_span, 3)
        if minimum_span and short_span + 1e-6 < minimum_span:
            failures.append("gym_clear_span_below_program_minimum")
        if maximum_height_ratio and height_to_span > maximum_height_ratio + 1e-6:
            failures.append("gym_height_to_clear_span_ratio_exceeded")
        if bool(metrics.get("pyramidal_like")) or dominant_enclosure_erased or (
            not measured_profiled_hall and cascade_without_hall_enclosure
        ):
            failures.append("gym_dominant_hall_erased_by_cascade_or_pyramid")
    return {
        **evidence,
        "hard_pass": not failures,
        "failures": failures,
    }


_BODY_RULE_FAMILIES = {
    "bend": "deformation",
    "bent_bar": "deformation",
    "twist": "deformation",
    "inflate": "deformation",
    "pinch": "deformation",
    "taper": "deformation",
    "shear": "deformation",
    "setback": "step",
    "stepped_mass": "step",
    "terrace": "step",
    "courtyard": "void",
    "carve_void": "void",
    "notch": "void",
    "puncture": "void",
    "cut_corner": "void",
    "slice": "cut",
    "clip": "cut",
    "radial_array": "array",
    "linear_array": "array",
    "mirror_array": "array",
    "cross_mass": "array",
    "split_wing": "array",
    "cantilever": "support",
    "lift": "support",
    "scale": "transform",
    "translate": "transform",
    "rotate": "transform",
    "union": "composition",
    "intersection": "composition",
    "difference": "composition",
}


def _architectural_articulation_metrics(source: Any) -> dict[str, Any]:
    """Return a cross-layer body-rule budget from the actual recursive AST.

    Program synthesis and BOOK projection used to validate independently. A
    stepped/cantilever body could therefore receive stack+bend and still pass
    because the final Boolean was one manifold component. The resulting object
    is technically clean but architecturally reads as accumulated effects.

    One synthesized node is one program rule. A BOOK call may expand to helper
    nodes (for example rotate+intersection), so it is counted once through the
    causal ``book_call_index`` written by the adapter. Administrative p.3
    clip/recompose nodes and the protected roof/section invariant are excluded.
    """
    payload = source.metadata.get("geometry_program") if hasattr(source, "metadata") else None
    nodes = payload.get("nodes") if isinstance(payload, dict) else ()
    program_rules: list[dict[str, Any]] = []
    book_groups: dict[int | str, list[dict[str, Any]]] = {}
    for order, raw in enumerate(nodes or ()):
        if not isinstance(raw, dict):
            continue
        operator = str(raw.get("operator") or "")
        if operator == "profiled_hall":
            continue
        provenance = raw.get("provenance") if isinstance(raw.get("provenance"), dict) else {}
        source_kind = str(provenance.get("source") or "")
        if source_kind == "procedural_geometry_synthesis_agent":
            family = _BODY_RULE_FAMILIES.get(operator)
            if family:
                program_rules.append({
                    "layer": "program",
                    "operator": operator,
                    "family": family,
                    "node_id": str(raw.get("id") or ""),
                    "order": order,
                })
            continue
        if source_kind != "book_recursive_projection":
            continue
        verb = str(provenance.get("book_verb") or "")
        call_index = provenance.get("book_call_index", -1)
        if verb in {"select_book_scope", "recompose_book_scope"} or int(call_index or -1) < 0:
            continue
        book_groups.setdefault(call_index, []).append({
            "operator": operator,
            "verb": verb,
            "node_id": str(raw.get("id") or ""),
            "order": order,
        })

    book_rules: list[dict[str, Any]] = []
    for call_index, group in sorted(book_groups.items(), key=lambda item: int(item[0])):
        terminal = max(group, key=lambda item: item["order"])
        family = _BODY_RULE_FAMILIES.get(terminal["operator"])
        if not family:
            continue
        book_rules.append({
            "layer": "book",
            "operator": terminal["operator"],
            "verb": terminal["verb"],
            "family": family,
            "call_index": int(call_index),
            "node_id": terminal["node_id"],
            "order": terminal["order"],
        })

    rules = sorted((*program_rules, *book_rules), key=lambda item: item["order"])
    family_counts = Counter(rule["family"] for rule in rules)
    duplicated_structural_families = sorted(
        family for family in {"void", "step", "array", "support"}
        if family_counts[family] > 1
    )
    return {
        "body_rule_count": len(rules),
        "program_rule_count": len(program_rules),
        "book_rule_count": len(book_rules),
        "rules": [
            {key: value for key, value in rule.items() if key != "order"}
            for rule in rules
        ],
        "family_counts": dict(sorted(family_counts.items())),
        "duplicated_structural_families": duplicated_structural_families,
        "hard_pass": len(rules) <= 2 and not duplicated_structural_families,
        "budget": 2,
        "section_invariant_excluded": True,
        "scope_administration_excluded": True,
    }


def _program_section_phenotype(operators: set[str]) -> str:
    """Map an executable roof/section graph to its visible broad phenotype."""
    if "barrel_roof" in operators:
        return "curved"
    if operators & {"ridge_roof", "shed_roof", "folded_roof"}:
        return "oblique"
    if operators & {"sawtooth_roof", "stepped_section"}:
        return "stepped"
    if "flat_roof" in operators:
        return "prismatic"
    return ""


def _oriented_aspect(poly: Polygon) -> float:
    rectangle = poly.minimum_rotated_rectangle
    coordinates = list(rectangle.exterior.coords)
    lengths = sorted(
        (((right[0] - left[0]) ** 2 + (right[1] - left[1]) ** 2) ** 0.5)
        for left, right in zip(coordinates, coordinates[1:])
        if left != right
    )
    return float(lengths[-1] / max(lengths[0], 1e-9)) if lengths else 1.0


def _oriented_plan_dimensions(poly: Polygon) -> tuple[float, float]:
    if poly is None or poly.is_empty:
        return (0.0, 0.0)
    rectangle = poly.minimum_rotated_rectangle
    coordinates = list(rectangle.exterior.coords)
    lengths = sorted(
        (((right[0] - left[0]) ** 2 + (right[1] - left[1]) ** 2) ** 0.5)
        for left, right in zip(coordinates, coordinates[1:])
        if left != right
    )
    if len(lengths) < 2:
        return (0.0, 0.0)
    return (float(lengths[0]), float(lengths[-1]))


def _program_dimensional_context(
    generation_site: Polygon,
    building_type: str,
    requested_height_m: float,
    requested_floors: int,
) -> dict[str, Any]:
    """Select a feasible program subtype before authoring geometry.

    The previous gym benchmark forced an 18 m hall onto every parcel. On the
    current 103 m2 legal host this produced 3--6 m short spans with height/span
    ratios above 3, so pyramids were inevitable. Dimensional requirements are
    program data and normalized site measurements, never parcel templates.
    """
    profile = resolve_program_profile(building_type)
    requirements = profile.get("dimensional_requirements")
    short_axis, long_axis = _oriented_plan_dimensions(generation_site)
    span_capacity = short_axis * 0.92
    base = {
        "schema_version": "arr.maas.program_dimensional_context.v1",
        "program_id": str(profile.get("id") or "generic"),
        "requested_height_m": round(float(requested_height_m), 3),
        "requested_floors": int(requested_floors),
        "generation_host_area_m2": round(float(generation_site.area), 3),
        "generation_host_short_axis_m": round(short_axis, 3),
        "generation_host_long_axis_m": round(long_axis, 3),
        "estimated_clear_span_capacity_m": round(span_capacity, 3),
        "parcel_coordinates_used": False,
    }
    if not isinstance(requirements, dict) or not requirements.get("subtypes"):
        return {
            **base,
            "status": "not_required",
            "selected_subtype": "generic",
            "effective_height_m": round(float(requested_height_m), 3),
            "effective_floors": int(requested_floors),
        }
    selected = next((
        dict(item)
        for item in requirements.get("subtypes") or ()
        if isinstance(item, dict)
        and span_capacity >= float(item.get("minimum_clear_span_m") or 0.0)
        and float(generation_site.area) >= float(item.get("minimum_host_area_m2") or 0.0)
    ), None)
    if selected is None:
        return {
            **base,
            "status": "infeasible",
            "selected_subtype": "none",
            "effective_height_m": 0.0,
            "effective_floors": 0,
            "failure_reasons": ["legal_generation_site_cannot_fit_minimum_program_span"],
            "available_subtypes": [str(item.get("id") or "") for item in requirements.get("subtypes") or ()],
        }
    minimum_height = float(selected.get("minimum_height_m") or 0.0)
    maximum_height = float(selected.get("maximum_height_m") or requested_height_m)
    maximum_ratio = float(selected.get("maximum_height_to_clear_span_ratio") or 1.0)
    target_ratio = float(selected.get("target_height_to_clear_span_ratio") or maximum_ratio)
    ratio_height = span_capacity * min(target_ratio, maximum_ratio)
    effective_height = min(float(requested_height_m), maximum_height, ratio_height)
    if effective_height < minimum_height:
        return {
            **base,
            "status": "infeasible",
            "selected_subtype": str(selected.get("id") or "none"),
            "effective_height_m": round(effective_height, 3),
            "effective_floors": 0,
            "failure_reasons": ["clear_span_cannot_support_minimum_program_height"],
        }
    return {
        **base,
        "status": "adapted" if effective_height < float(requested_height_m) else "feasible",
        "selected_subtype": str(selected.get("id") or "generic"),
        "minimum_clear_span_m": float(selected.get("minimum_clear_span_m") or 0.0),
        "maximum_height_to_clear_span_ratio": maximum_ratio,
        "target_height_to_clear_span_ratio": target_ratio,
        "effective_height_m": round(effective_height, 3),
        "effective_floors": min(int(requested_floors), int(selected.get("maximum_floors") or requested_floors)),
    }


def _scope_coverage_anchors(
    candidates: list[_Candidate],
    *,
    seed_family_cap: int,
    section_family_cap: int,
    roof_archetype_caps: dict[str, int],
    chassis_family_cap: int,
    required_phenotypes: tuple[str, ...] = (),
) -> list[_Candidate]:
    """Find joint scope/phenotype anchors before greedy portfolio filling."""
    by_scope = {
        label: sorted(
            (candidate for candidate in candidates if _scope_key(candidate) == label),
            key=lambda candidate: candidate.score,
            reverse=True,
        )
        for label, _fraction in BASE_VOLUME_FRACTIONS
    }
    if any(not options for options in by_scope.values()):
        return []
    available_phenotypes = {_solid_morphology_metrics(candidate)["phenotype"] for candidate in candidates}
    required_phenotypes = tuple(
        value for value in dict.fromkeys(required_phenotypes)
        if value in available_phenotypes
    )

    def solve(phenotype_requirements: tuple[str, ...]) -> list[_Candidate] | None:
        requirements = tuple(
            [("scope", label) for label, _fraction in BASE_VOLUME_FRACTIONS]
            + [("phenotype", value) for value in phenotype_requirements]
        )

        def visit(
            picked: list[_Candidate],
            operation_usage: Counter,
            seed_usage: Counter,
            section_usage: Counter,
            roof_usage: Counter,
            chassis_usage: Counter,
        ) -> list[_Candidate] | None:
            covered_scopes = {_scope_key(candidate) for candidate in picked}
            covered_phenotypes = {_solid_morphology_metrics(candidate)["phenotype"] for candidate in picked}
            missing = [
                requirement for requirement in requirements
                if (
                    requirement[1] not in covered_scopes
                    if requirement[0] == "scope"
                    else requirement[1] not in covered_phenotypes
                )
            ]
            if not missing:
                return list(picked)

            def eligible(requirement: tuple[str, str]) -> list[_Candidate]:
                result = []
                for candidate in candidates:
                    if any(candidate is item for item in picked):
                        continue
                    if requirement[0] == "scope" and _scope_key(candidate) != requirement[1]:
                        continue
                    if requirement[0] == "phenotype" and _solid_morphology_metrics(candidate)["phenotype"] != requirement[1]:
                        continue
                    seed = _seed_family(candidate)
                    section = _section_family(candidate)
                    roof = _roof_archetype(candidate)
                    chassis = _chassis_family(candidate)
                    if operation_usage[candidate.operation] >= 2:
                        continue
                    if (
                        seed_usage[seed] >= seed_family_cap
                        or section_usage[section] >= section_family_cap
                        or roof_usage[roof] >= roof_archetype_caps.get(roof, 999)
                        or chassis_usage[chassis] >= chassis_family_cap
                    ):
                        continue
                    if any(_silhouette_distance(candidate, other) < 0.10 for other in picked):
                        continue
                    result.append(candidate)
                return result

            requirement_options = [(requirement, eligible(requirement)) for requirement in missing]
            requirement, options = min(
                requirement_options,
                key=lambda item: (len(item[1]), item[0][0], item[0][1]),
            )
            if not options:
                return None
            options.sort(key=lambda candidate: (
                seed_usage[_seed_family(candidate)],
                section_usage[_section_family(candidate)],
                roof_usage[_roof_archetype(candidate)],
                chassis_usage[_chassis_family(candidate)],
                -candidate.score,
            ))
            for candidate in options:
                seed = _seed_family(candidate)
                section = _section_family(candidate)
                roof = _roof_archetype(candidate)
                chassis = _chassis_family(candidate)
                operation_usage[candidate.operation] += 1
                seed_usage[seed] += 1
                section_usage[section] += 1
                roof_usage[roof] += 1
                chassis_usage[chassis] += 1
                picked.append(candidate)
                result = visit(
                    picked, operation_usage, seed_usage, section_usage,
                    roof_usage, chassis_usage,
                )
                if result is not None:
                    return result
                picked.pop()
                operation_usage[candidate.operation] -= 1
                seed_usage[seed] -= 1
                section_usage[section] -= 1
                roof_usage[roof] -= 1
                chassis_usage[chassis] -= 1
            return None

        return visit([], Counter(), Counter(), Counter(), Counter(), Counter())

    # If all requested phenotypes cannot coexist under hard silhouette/family
    # constraints, preserve the six BOOK scopes and let the explicit failure
    # remain visible. Never fabricate or relax a geometry threshold.
    return solve(required_phenotypes) or solve(()) or []


def _fingerprint(candidate: _Candidate) -> tuple[Any, ...]:
    volume_key = tuple(sorted((
        tuple(round(value, 3) for value in volume.footprint.bounds),
        round(float(volume.footprint.area), 3),
        round(float(volume.bottom_fraction), 3),
        round(float(volume.top_fraction), 3),
    ) for volume in candidate.source.volumes))
    section = candidate.source.metadata.get("program_section_graph_evidence") or {}
    section_key = tuple(
        (
            str(node.get("operator") or ""),
            tuple(tuple(round(float(value), 4) for value in item) for item in (node.get("section_controls") or ())),
        )
        for node in (section.get("materialized_nodes") or ())
        if isinstance(node, dict)
    ) if isinstance(section, dict) else ()
    geometry_evidence = candidate.source.metadata.get("geometry_program_bridge_evidence") or {}
    geometry_key = str(geometry_evidence.get("geometry_hash") or "") if isinstance(geometry_evidence, dict) else ""
    return volume_key, section_key, geometry_key


def _inside_site(source: Any, site: Polygon) -> bool:
    try:
        return all(
            volume.footprint.is_valid
            and volume.footprint.difference(site).area <= 1e-6
            for volume in source.volumes
        )
    except (GEOSException, ValueError):
        return False


def _load_visual_directive(output_dir: Path, pnu: str) -> dict[str, Any]:
    path = output_dir / "maas-book-programs-vlm-directive.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != "arr.maas.portfolio_vlm_directive.v1"
        or str(payload.get("pnu") or "") != pnu
        or payload.get("status") != "active"
    ):
        return {}
    return payload


def _agent_mutated_seeds(
    building_type: str,
    mutations: list[dict[str, Any]] | None,
    geometry_mutations: list[dict[str, Any]] | None = None,
    synthesis_requests: list[dict[str, Any]] | None = None,
    outcome_graph: GeometryOutcomeGraph | None = None,
) -> tuple[VerbSequence, ...]:
    """Apply agent/VLM graph edits to reusable role seeds, never finished forms."""
    seeds = list(program_seed_sequences(building_type))
    originals = {sequence.name: sequence for sequence in seeds}
    for index, record in enumerate(mutations or ()):  # bounded external genotype proposals
        if not isinstance(record, dict):
            continue
        source = originals.get(str(record.get("source_seed") or ""))
        if source is None:
            continue
        edit_records = record.get("edits") if isinstance(record.get("edits"), list) else [record]
        typed_edits: list[ProgramSectionGraphEdit] = []
        replacement = "genotype"
        for edit_record in edit_records:
            if not isinstance(edit_record, dict):
                continue
            operation = str(edit_record.get("operation") or "")
            if operation not in {"replace_roof_operator", "set_parameter", "set_section_control"}:
                continue
            operator_value = str(edit_record.get("operator_value") or "") or None
            if operator_value:
                replacement = operator_value
            try:
                numeric_value = (
                    float(edit_record["numeric_value"])
                    if edit_record.get("numeric_value") is not None
                    else None
                )
                control_index = (
                    int(edit_record["control_index"])
                    if edit_record.get("control_index") is not None
                    else None
                )
            except (TypeError, ValueError):
                continue
            typed_edits.append(ProgramSectionGraphEdit(
                operation=operation,
                target_node_id=str(edit_record.get("target_node_id") or "roof"),
                parameter_name=str(edit_record.get("parameter_name") or "operator"),
                numeric_value=numeric_value,
                control_index=control_index,
                operator_value=operator_value,
                rationale=str(edit_record.get("rationale") or record.get("rationale") or "agent-directed genotype mutation"),
            ))
        if not typed_edits:
            continue
        try:
            mutated = mutate_program_section_sequence(
                source,
                typed_edits,
                director="vlm_portfolio_critic",
                name_suffix=f"genotype_{index}_{replacement}",
            )
        except ValueError:
            continue
        if mutated.name != source.name:
            seeds.append(mutated)
    # A geometry directive creates another typed program seed, not a frozen
    # mesh.  The same program roles and BOOK projection compile first; only
    # then is the dominant role replaced by the recursive solid program.
    for index, record in enumerate(geometry_mutations or ()):
        if not isinstance(record, dict):
            continue
        source = originals.get(str(record.get("source_seed") or ""))
        program_id = str(record.get("geometry_program") or "")
        if source is None or program_id not in _geometry_program_registry():
            continue
        raw_strengths = (
            record.get("legal_fit_strengths")
            if isinstance(record.get("legal_fit_strengths"), list)
            else [record.get("legal_fit_strength") or 0.0]
        )
        try:
            legal_fit_strengths = tuple(dict.fromkeys(
                max(0.0, min(1.0, float(value))) for value in raw_strengths
            ))
        except (TypeError, ValueError):
            continue
        edit_records = record.get("geometry_edits") if isinstance(record.get("geometry_edits"), list) else []
        for strength_index, legal_fit_strength in enumerate(legal_fit_strengths):
            notes = tuple((*source.notes,
                f"geometry_program_directive={program_id}",
                f"geometry_program_source_seed={source.name}",
                f"geometry_program_edits={json.dumps(edit_records, sort_keys=True, separators=(',', ':'))}",
                f"geometry_program_rationale={str(record.get('rationale') or 'agent-authored recursive solid mutation')}",
                f"geometry_program_legal_fit_strength={legal_fit_strength}",
                "geometry_program_source=typed_agent_directive",
            ))
            seeds.append(replace(
                source,
                name=f"{source.name}__geometry_genotype_{index}_{strength_index}_{program_id}",
                notes=notes,
            ))
    # Program-profile inference is the deterministic control lane.  A live
    # VLM/session directive must add an experimental lane, never replace the
    # control and erase rare-but-required phenotypes from the search pool.
    # Exact legacy section controls, parcel coordinates, and finished forms
    # remain excluded from both lanes.
    profile_requests = tuple({
        **dict(request),
        "synthesis_request_source": "program_profile_control",
    } for request in synthesis_requests_from_program_profile(
        building_type,
        source_seeds=tuple(originals),
    ))
    directive_requests = tuple({
        **dict(request),
        "synthesis_request_source": "vlm_or_session_directive",
    } for request in (synthesis_requests or ()) if isinstance(request, dict))
    effective_synthesis_requests = tuple((*profile_requests, *directive_requests))

    # A synthesis request describes architectural intent and normalized base
    # seeds.  The agent expands it into recursive ASTs; unlike the legacy
    # geometry_program registry, no named completed-form record is selected.
    for request_index, request in enumerate(effective_synthesis_requests):
        if not isinstance(request, dict):
            continue
        source = originals.get(str(request.get("source_seed") or ""))
        if source is None:
            continue
        programs = synthesize_architectural_programs(request, building_type=building_type)
        vlm_status = "not_requested"
        if bool(request.get("live_vlm_revision")):
            live_opt_in = os.getenv("MAAS_LIVE_GEOMETRY_VLM", "").strip().lower() in {"1", "true", "yes", "on"}
            rotated_credential_confirmed = os.getenv("MAAS_LIVE_VLM_CREDENTIAL_ROTATED", "").strip().lower() in {"1", "true", "yes", "on"}
            if not live_opt_in:
                vlm_status = "inactive_requires_explicit_MAAS_LIVE_GEOMETRY_VLM_opt_in"
            elif not rotated_credential_confirmed:
                vlm_status = "inactive_requires_rotated_credential_confirmation"
            elif not os.getenv("OPENAI_API_KEY"):
                vlm_status = "inactive_missing_rotated_environment_key"
            else:
                try:
                    reference_contract = program_reference_contract(building_type)
                    reference_matches = [
                        item for item in (request.get("reference_matches") or ())
                        if isinstance(item, dict)
                    ]
                    loop = run_geometry_program_a2a_loop(
                        context={
                            "building_type": building_type,
                            "intent_tags": list(request.get("intent_tags") or ()),
                            "base_seeds": list(request.get("base_seeds") or ()),
                            "instruction": "critic must propose typed node edits, never a completed mesh",
                        },
                        target_count=len(programs),
                        author_programs=lambda _context, authored=programs: authored,
                        critic_program=openai_vlm_geometry_critic(
                            reference_provider=lambda program, explicit=reference_matches: retrieve_geometry_reference_matches(
                                program,
                                building_type=building_type,
                                explicit_matches=explicit,
                                limit=max(3, min(8, int(request.get("reference_limit") or 5))),
                            ),
                            memory_provider=(
                                lambda program: outcome_graph.agent_neighborhood(
                                    source_seed=source.name,
                                    program_hash=program.program_hash(),
                                )
                                if outcome_graph is not None
                                else {}
                            ),
                            building_type=building_type,
                            program_context=reference_contract,
                            model=str(request.get("vlm_model") or "") or None,
                        ),
                        max_generations=max(1, min(3, int(request.get("vlm_generations") or 2))),
                        author_provider="bounded_procedural_geometry_agent",
                        critic_provider="openai_vlm",
                    )
                    if outcome_graph is not None:
                        outcome_graph.observe_vlm_loop(
                            program_slug=building_type,
                            source_seed=source.name,
                            trace=loop.trace,
                        )
                    if loop.archive:
                        programs = tuple(replace(
                            candidate.program,
                            metadata={
                                **candidate.program.metadata,
                                "vlm_critic_score": round(float(candidate.critic_score), 4),
                                "vlm_revision_generation": int(candidate.generation),
                                "vlm_geometry_critic_active": True,
                                "vlm_geometry_revision_count": int(loop.trace.get("geometry_revision_count") or 0),
                                "vlm_unique_geometry_count": int(loop.trace.get("unique_geometry_count") or 0),
                                "vlm_model": str(candidate.critic_payload.get("model") or ""),
                                "vlm_response_id": str(candidate.critic_payload.get("response_id") or ""),
                                "vlm_program_fit_hard_pass": bool(
                                    candidate.critic_payload.get("program_fit_hard_pass", True)
                                ),
                                "vlm_program_appropriateness": float(
                                    (candidate.critic_payload.get("concept_scores") or {}).get("program_appropriateness") or 0.0
                                ),
                                "vlm_section_program_fit": float(
                                    (candidate.critic_payload.get("concept_scores") or {}).get("section_program_fit") or 0.0
                                ),
                                "vlm_reference_assessments": list(
                                    candidate.critic_payload.get("reference_assessments") or ()
                                ),
                                "vlm_reference_count": len(
                                    ((candidate.critic_payload.get("maas_causal_context") or {}).get("reference_matches") or ())
                                ),
                                "vlm_memory_observation_count": int(
                                    (((candidate.critic_payload.get("maas_causal_context") or {}).get("outcome_memory") or {}).get("observation_count") or 0)
                                ),
                            },
                        ) for candidate in loop.archive)
                    else:
                        # An all-rejected live lane is evidence of failure,
                        # not permission to silently restore its unreviewed
                        # parent programs into the accepted candidate pool.
                        programs = ()
                    vlm_status = str(loop.trace.get("status") or "completed")
                except Exception as exc:
                    # The deterministic graph author and hard gates remain
                    # usable when an external critic is unavailable. Record
                    # the failure; never fabricate a synthetic VLM score.
                    vlm_status = f"error:{type(exc).__name__}"
        raw_strengths = request.get("legal_fit_strengths")
        if not isinstance(raw_strengths, list):
            raw_strengths = [0.0, 0.25, 0.5, 0.75, 1.0]
        try:
            fallback_strengths = tuple(dict.fromkeys(
                max(0.0, min(1.0, round(float(value), 4))) for value in raw_strengths
            ))
        except (TypeError, ValueError):
            fallback_strengths = (0.0, 0.25, 0.5, 0.75, 1.0)
        for program_index, program in enumerate(programs):
            strengths = (
                outcome_graph.preferred_strengths(
                    source_seed=source.name,
                    program_hash=program.program_hash(),
                    fallback=fallback_strengths,
                    limit=2,
                )
                if outcome_graph is not None
                else fallback_strengths
            )
            payload = json.dumps(program.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            family = str(program.metadata.get("family") or "agent_recursive")
            for strength_index, legal_fit_strength in enumerate(strengths):
                notes = tuple((*source.notes,
                    f"geometry_program_payload={payload}",
                    f"geometry_program_source_seed={source.name}",
                    "geometry_program_edits=[]",
                    f"geometry_program_rationale=agent synthesis from normalized base and intent tags: {','.join(program.metadata.get('intent_tags') or ())}",
                    f"geometry_program_legal_fit_strength={legal_fit_strength}",
                    "geometry_program_source=procedural_geometry_synthesis_agent",
                    f"geometry_program_synthesis_request_source={str(request.get('synthesis_request_source') or 'program_profile_control')}",
                    f"geometry_program_vlm_status={vlm_status}",
                    f"geometry_program_vlm_reference_count={int(program.metadata.get('vlm_reference_count') or 0)}",
                    f"geometry_program_vlm_memory_observation_count={int(program.metadata.get('vlm_memory_observation_count') or 0)}",
                    f"geometry_program_vlm_revision_count={int(program.metadata.get('vlm_geometry_revision_count') or 0)}",
                ))
                seeds.append(replace(
                    source,
                    name=(
                        f"{source.name}__synth_{request_index}_{program_index}_{strength_index}_"
                        f"{family}_{program.program_hash()[:10]}"
                    ),
                    notes=notes,
                ))
    return tuple(seeds)


def _geometry_program_registry() -> dict[str, Any]:
    references = reference_language_programs()
    programs = tuple((*references.values(), *architectural_shape_programs()))
    registry: dict[str, Any] = dict(references)
    for program in programs:
        family = str(program.metadata.get("family") or "")
        for key in (program.name, family):
            if key:
                registry.setdefault(key, program)
    return registry


def _materialize_directed_geometry(
    source: Any,
    sequence: VerbSequence,
    *,
    containment_host: Polygon | None = None,
    upper_containment_host: Polygon | None = None,
) -> Any | None:
    directive = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_directive=")
    ), "")
    raw_payload = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_payload=")
    ), "")
    if not directive and not raw_payload:
        return source
    raw_fit_strength = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_legal_fit_strength=")
    ), "0")
    try:
        fit_strength = max(0.0, min(1.0, float(raw_fit_strength)))
    except (TypeError, ValueError):
        return None
    if raw_payload:
        try:
            program = GeometryProgram.from_dict(json.loads(raw_payload))
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
    else:
        program = _geometry_program_registry().get(directive)
    if program is None:
        return None
    raw_edits = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_edits=")
    ), "[]")
    try:
        edit_records = json.loads(raw_edits)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if edit_records:
        mutation = apply_geometry_edits(program, edit_records)
        if mutation.status != "revised" or mutation.program is None:
            return None
        program = mutation.program
    # BOOK p.3 scope and ordered operations must mutate the same recursive
    # manifold later rendered and gated. The old SourceMass projection remains
    # as program/legal evidence, but it is no longer the geometry authority.
    try:
        program = apply_book_projection_to_geometry_program(program, sequence)
    except (TypeError, ValueError):
        return None
    materialized = replace_source_dominant_with_geometry_program(
        source,
        program,
        containment_host=containment_host,
        upper_containment_host=upper_containment_host,
        upper_fit_strength=fit_strength,
    )
    if materialized is None:
        return None
    source_seed = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_source_seed=")
    ), "")
    metadata = deepcopy(materialized.metadata)
    bridge = deepcopy(metadata.get("geometry_program_bridge_evidence") or {})
    bridge["source_seed"] = source_seed
    bridge["author_provider"] = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_source=")
    ), "unknown")
    metadata["geometry_program_bridge_evidence"] = bridge
    return replace(materialized, metadata=metadata)


def _select(
    pool: list[_Candidate],
    target: int = 20,
    *,
    visual_directive: dict[str, Any] | None = None,
) -> list[_Candidate]:
    unique: dict[tuple[Any, ...], _Candidate] = {}
    for candidate in pool:
        fingerprint = _fingerprint(candidate)
        current = unique.get(fingerprint)
        if current is None or candidate.score > current.score:
            unique[fingerprint] = candidate
    candidates = list(unique.values())
    candidate_universe = list(candidates)
    selected: list[_Candidate] = []
    operation_usage: dict[str, int] = {}
    scope_usage: dict[str, int] = {}
    seed_usage: dict[str, int] = {}
    section_usage: dict[str, int] = {}
    roof_usage: dict[str, int] = {}
    chassis_usage: dict[str, int] = {}
    available_scopes = {_scope_key(candidate) for candidate in candidates}
    seed_families = {_seed_family(candidate) for candidate in candidates}
    roof_archetypes = {_roof_archetype(candidate) for candidate in candidates}
    chassis_families = {_chassis_family(candidate) for candidate in candidates}
    seed_family_cap = max(2, (target + max(1, len(seed_families)) - 1) // max(1, len(seed_families)) + 1)
    section_family_cap = max(3, target // 2)
    default_roof_cap = target if len(roof_archetypes) <= 1 else max(4, target // 4)
    roof_archetype_caps = {archetype: default_roof_cap for archetype in roof_archetypes}
    directive = visual_directive or {}
    for archetype, cap in (directive.get("max_roof_archetype_counts") or {}).items():
        if str(archetype) in roof_archetypes:
            roof_archetype_caps[str(archetype)] = max(1, min(target, int(cap)))
    chassis_family_cap = max(
        1,
        min(
            target,
            int(directive.get("max_chassis_family_count") or (
                target if len(chassis_families) <= 1 else max(4, target // max(1, len(chassis_families)) + 2)
            )),
        ),
    )
    anchors = _scope_coverage_anchors(
        candidates,
        seed_family_cap=seed_family_cap,
        section_family_cap=section_family_cap,
        roof_archetype_caps=roof_archetype_caps,
        chassis_family_cap=chassis_family_cap,
        required_phenotypes=tuple(
            str(value) for value in directive.get("required_solid_phenotypes") or ()
        ),
    )
    anchor_ids = {id(candidate) for candidate in anchors}
    candidates = [candidate for candidate in candidates if id(candidate) not in anchor_ids]
    for winner in anchors:
        selected.append(winner)
        operation_usage[winner.operation] = operation_usage.get(winner.operation, 0) + 1
        scope_usage[_scope_key(winner)] = scope_usage.get(_scope_key(winner), 0) + 1
        seed_usage[_seed_family(winner)] = seed_usage.get(_seed_family(winner), 0) + 1
        section_usage[_section_family(winner)] = section_usage.get(_section_family(winner), 0) + 1
        roof_usage[_roof_archetype(winner)] = roof_usage.get(_roof_archetype(winner), 0) + 1
        chassis_usage[_chassis_family(winner)] = chassis_usage.get(_chassis_family(winner), 0) + 1

    # A VLM critic may require missing visual genotypes, but it can only select
    # candidates that were produced by typed graph mutations and passed all
    # geometry/program/legal gates.  It never injects a finished mesh.
    required_roofs = tuple(dict.fromkeys(
        str(value) for value in (directive.get("required_roof_archetypes") or ())
        if str(value) in roof_archetypes
    ))
    for required_roof in required_roofs:
        if len(selected) >= target or roof_usage.get(required_roof, 0):
            continue
        options = [
            candidate for candidate in candidates
            if _roof_archetype(candidate) == required_roof
            and operation_usage.get(candidate.operation, 0) < 2
            and seed_usage.get(_seed_family(candidate), 0) < seed_family_cap
            and section_usage.get(_section_family(candidate), 0) < section_family_cap
            and roof_usage.get(required_roof, 0) < roof_archetype_caps.get(required_roof, target)
            and chassis_usage.get(_chassis_family(candidate), 0) < chassis_family_cap
            and all(_silhouette_distance(candidate, other) >= 0.10 for other in selected)
        ]
        if not options:
            continue
        winner = max(options, key=lambda candidate: candidate.score)
        selected.append(winner)
        operation_usage[winner.operation] = operation_usage.get(winner.operation, 0) + 1
        scope_usage[_scope_key(winner)] = scope_usage.get(_scope_key(winner), 0) + 1
        seed_usage[_seed_family(winner)] = seed_usage.get(_seed_family(winner), 0) + 1
        section_usage[_section_family(winner)] = section_usage.get(_section_family(winner), 0) + 1
        roof_usage[_roof_archetype(winner)] = roof_usage.get(_roof_archetype(winner), 0) + 1
        chassis_usage[_chassis_family(winner)] = chassis_usage.get(_chassis_family(winner), 0) + 1
        candidates.remove(winner)
    available_geometry_families = {
        _geometry_program_family(candidate)
        for candidate in candidates
        if _geometry_program_family(candidate)
    }
    required_geometry_families = tuple(dict.fromkeys(
        str(value) for value in (directive.get("required_geometry_program_families") or ())
        if str(value) in available_geometry_families
    ))
    for required_family in required_geometry_families:
        if len(selected) >= target or any(
            _geometry_program_family(candidate) == required_family
            for candidate in selected
        ):
            continue
        options = [
            candidate for candidate in candidates
            if _geometry_program_family(candidate) == required_family
            and operation_usage.get(candidate.operation, 0) < 2
            and seed_usage.get(_seed_family(candidate), 0) < seed_family_cap
            and section_usage.get(_section_family(candidate), 0) < section_family_cap
            and roof_usage.get(_roof_archetype(candidate), 0) < roof_archetype_caps.get(_roof_archetype(candidate), target)
            and chassis_usage.get(_chassis_family(candidate), 0) < chassis_family_cap
            and all(_silhouette_distance(candidate, other) >= 0.10 for other in selected)
        ]
        if not options:
            continue
        winner = max(options, key=lambda candidate: candidate.score)
        selected.append(winner)
        operation_usage[winner.operation] = operation_usage.get(winner.operation, 0) + 1
        scope_usage[_scope_key(winner)] = scope_usage.get(_scope_key(winner), 0) + 1
        seed_usage[_seed_family(winner)] = seed_usage.get(_seed_family(winner), 0) + 1
        section_usage[_section_family(winner)] = section_usage.get(_section_family(winner), 0) + 1
        roof_usage[_roof_archetype(winner)] = roof_usage.get(_roof_archetype(winner), 0) + 1
        chassis_usage[_chassis_family(winner)] = chassis_usage.get(_chassis_family(winner), 0) + 1
        candidates.remove(winner)
    while candidates and len(selected) < target:
        def eligible_with_operation_cap(operation_cap: int) -> list[_Candidate]:
            return [
                candidate for candidate in candidates
                if operation_usage.get(candidate.operation, 0) < operation_cap
                and seed_usage.get(_seed_family(candidate), 0) < seed_family_cap
                and section_usage.get(_section_family(candidate), 0) < section_family_cap
                and roof_usage.get(_roof_archetype(candidate), 0) < roof_archetype_caps.get(_roof_archetype(candidate), target)
                and chassis_usage.get(_chassis_family(candidate), 0) < chassis_family_cap
                and all(_silhouette_distance(candidate, other) >= 0.10 for other in selected)
            ]

        eligible = eligible_with_operation_cap(2)
        if not eligible:
            # Only after the two-use diversity cap is exhausted may the same
            # BOOK sentence appear once more on another program/section
            # family. Silhouette and family caps remain unchanged.
            eligible = eligible_with_operation_cap(3)
        if not eligible:
            break
        uncovered_scopes = available_scopes - set(scope_usage)
        if uncovered_scopes:
            # BOOK p.3 scope coverage is a portfolio constraint. Start with
            # the rarest surviving scope so a high-scoring 1/1 family cannot
            # crowd a valid 1/16 or 1/8 candidate out of the final archive.
            target_scope = min(
                uncovered_scopes,
                key=lambda scope: (
                    sum(_scope_key(candidate) == scope for candidate in eligible),
                    scope,
                ),
            )
            scoped = [candidate for candidate in eligible if _scope_key(candidate) == target_scope]
            if scoped:
                eligible = scoped

        def selection_key(candidate: _Candidate) -> tuple[float, float]:
            novelty = 1.0 if not selected else min(
                _distance(candidate, other) * 0.55 + _silhouette_distance(candidate, other) * 0.45
                for other in selected
            )
            new_language_bonus = 0.08 if operation_usage.get(candidate.operation, 0) == 0 else 0.0
            new_scope_bonus = 0.05 if scope_usage.get(_scope_key(candidate), 0) == 0 else 0.0
            new_seed_bonus = 0.06 if seed_usage.get(_seed_family(candidate), 0) == 0 else 0.0
            new_section_bonus = 0.05 if section_usage.get(_section_family(candidate), 0) == 0 else 0.0
            new_roof_bonus = 0.09 if roof_usage.get(_roof_archetype(candidate), 0) == 0 else 0.0
            new_chassis_bonus = 0.06 if chassis_usage.get(_chassis_family(candidate), 0) == 0 else 0.0
            return (
                candidate.score * 0.44
                + novelty * 0.56
                + new_language_bonus
                + new_scope_bonus
                + new_seed_bonus
                + new_section_bonus
                + new_roof_bonus
                + new_chassis_bonus,
                candidate.score,
            )

        winner = max(eligible, key=selection_key)
        selected.append(winner)
        operation_usage[winner.operation] = operation_usage.get(winner.operation, 0) + 1
        scope_usage[_scope_key(winner)] = scope_usage.get(_scope_key(winner), 0) + 1
        seed_usage[_seed_family(winner)] = seed_usage.get(_seed_family(winner), 0) + 1
        section_usage[_section_family(winner)] = section_usage.get(_section_family(winner), 0) + 1
        roof_usage[_roof_archetype(winner)] = roof_usage.get(_roof_archetype(winner), 0) + 1
        chassis_usage[_chassis_family(winner)] = chassis_usage.get(_chassis_family(winner), 0) + 1
        candidates.remove(winner)
    return _rebalance_measured_morphologies(
        selected,
        candidate_universe,
        target=target,
        visual_directive=directive,
    )


def _selection_capacity_diagnostics(
    pool: list[_Candidate],
    selected: list[_Candidate],
    *,
    target: int,
    visual_directive: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Explain why a hard-pass pool cannot fill the requested portfolio.

    This is observation only. It never relaxes a diversity cap or changes
    selection; it exposes whether supply is lost to exact equivalence,
    silhouette resemblance, BOOK repetition, genotype, roof or chassis caps.
    """
    unique: dict[tuple[Any, ...], _Candidate] = {}
    for candidate in pool:
        fingerprint = _fingerprint(candidate)
        current = unique.get(fingerprint)
        if current is None or candidate.score > current.score:
            unique[fingerprint] = candidate
    universe = list(unique.values())
    selected_ids = {id(candidate) for candidate in selected}
    remaining = [candidate for candidate in universe if id(candidate) not in selected_ids]
    directive = visual_directive or {}
    seed_families = {_seed_family(candidate) for candidate in universe}
    roof_archetypes = {_roof_archetype(candidate) for candidate in universe}
    chassis_families = {_chassis_family(candidate) for candidate in universe}
    seed_cap = max(2, (target + max(1, len(seed_families)) - 1) // max(1, len(seed_families)) + 1)
    section_cap = max(3, target // 2)
    default_roof_cap = target if len(roof_archetypes) <= 1 else max(4, target // 4)
    roof_caps = {archetype: default_roof_cap for archetype in roof_archetypes}
    for archetype, cap in (directive.get("max_roof_archetype_counts") or {}).items():
        if str(archetype) in roof_caps:
            roof_caps[str(archetype)] = max(1, min(target, int(cap)))
    chassis_cap = max(1, min(
        target,
        int(directive.get("max_chassis_family_count") or (
            target if len(chassis_families) <= 1 else max(4, target // max(1, len(chassis_families)) + 2)
        )),
    ))
    operation_usage = Counter(candidate.operation for candidate in selected)
    seed_usage = Counter(_seed_family(candidate) for candidate in selected)
    section_usage = Counter(_section_family(candidate) for candidate in selected)
    roof_usage = Counter(_roof_archetype(candidate) for candidate in selected)
    chassis_usage = Counter(_chassis_family(candidate) for candidate in selected)
    reason_counts: Counter[str] = Counter()
    exclusive_counts: Counter[str] = Counter()
    signature_counts: Counter[str] = Counter()
    minimum_distances: list[float] = []
    for candidate in remaining:
        distances = [_silhouette_distance(candidate, other) for other in selected]
        minimum_distance = min(distances, default=1.0)
        minimum_distances.append(minimum_distance)
        reasons: list[str] = []
        if operation_usage[candidate.operation] >= 3:
            reasons.append("book_operation_cap")
        if seed_usage[_seed_family(candidate)] >= seed_cap:
            reasons.append("genotype_cap")
        if section_usage[_section_family(candidate)] >= section_cap:
            reasons.append("section_family_cap")
        if roof_usage[_roof_archetype(candidate)] >= roof_caps.get(_roof_archetype(candidate), target):
            reasons.append("roof_archetype_cap")
        if chassis_usage[_chassis_family(candidate)] >= chassis_cap:
            reasons.append("chassis_family_cap")
        if minimum_distance < 0.10:
            reasons.append("silhouette_near_duplicate")
        for reason in reasons:
            reason_counts[reason] += 1
        if len(reasons) == 1:
            exclusive_counts[reasons[0]] += 1
        signature_counts["+".join(sorted(reasons)) or "eligible"] += 1
    return {
        "schema_version": "arr.maas.selection_capacity_diagnostics.v1",
        "raw_pool_count": len(pool),
        "unique_fingerprint_count": len(universe),
        "exact_fingerprint_collapsed_count": len(pool) - len(universe),
        "selected_count": len(selected),
        "target_count": target,
        "remaining_candidate_count": len(remaining),
        "reason_counts": dict(sorted(reason_counts.items())),
        "exclusive_reason_counts": dict(sorted(exclusive_counts.items())),
        "failure_signature_counts": dict(sorted(signature_counts.items())),
        "minimum_silhouette_distance_summary": {
            "minimum": round(min(minimum_distances, default=1.0), 4),
            "mean": round(sum(minimum_distances) / max(1, len(minimum_distances)), 4),
            "maximum": round(max(minimum_distances, default=1.0), 4),
        },
        "caps": {
            "book_operation": 3,
            "genotype": seed_cap,
            "section_family": section_cap,
            "roof_archetype_default": default_roof_cap,
            "chassis_family": chassis_cap,
            "silhouette_distance_minimum": 0.10,
        },
    }


def _rebalance_measured_morphologies(
    selected: list[_Candidate],
    universe: list[_Candidate],
    *,
    target: int,
    visual_directive: dict[str, Any],
) -> list[_Candidate]:
    """Replace measured wedge/family excess with hard-pass mesh alternatives.

    This is phenotype selection, not a form template: categories and wedge
    status are measured from triangle normals/topology after site fitting.
    """
    result = list(selected)
    available = {_solid_morphology_metrics(candidate)["phenotype"] for candidate in universe}
    required = tuple(
        phenotype for phenotype in dict.fromkeys(
            str(value) for value in visual_directive.get("required_solid_phenotypes") or ()
        )
        if phenotype in available
    )
    wedge_cap = max(0, min(target, int(visual_directive.get("max_wedge_like_count", max(3, target // 5)))))
    pyramidal_cap = max(0, min(target, int(visual_directive.get("max_pyramidal_like_count", 2))))
    phenotype_cap = max(2, min(target, int(visual_directive.get("max_solid_phenotype_count", max(4, target // 4)))))

    def counts(items: list[_Candidate]) -> tuple[Counter[str], Counter[str], int]:
        return (
            Counter(_solid_morphology_metrics(item)["phenotype"] for item in items),
            Counter(_scope_key(item) for item in items),
            sum(bool(_solid_morphology_metrics(item)["wedge_like"]) for item in items),
        )

    def replacement_options(
        removed: _Candidate,
        *,
        wanted_phenotype: str = "",
        require_non_wedge: bool = False,
        require_non_pyramidal: bool = False,
    ) -> list[_Candidate]:
        remaining = [item for item in result if item is not removed]
        phenotype_counts, scope_counts, wedge_count = counts(remaining)
        pyramidal_count = sum(
            bool(_solid_morphology_metrics(item)["pyramidal_like"])
            for item in remaining
        )
        used = {id(item) for item in remaining}
        removed_scope = _scope_key(removed)
        must_restore_scope = scope_counts.get(removed_scope, 0) == 0
        options = []
        for candidate in universe:
            if id(candidate) in used:
                continue
            metrics = _solid_morphology_metrics(candidate)
            phenotype = metrics["phenotype"]
            if wanted_phenotype and phenotype != wanted_phenotype:
                continue
            if require_non_wedge and metrics["wedge_like"]:
                continue
            if require_non_pyramidal and metrics["pyramidal_like"]:
                continue
            if must_restore_scope and _scope_key(candidate) != removed_scope:
                continue
            if phenotype_counts[phenotype] >= phenotype_cap:
                continue
            if metrics["wedge_like"] and wedge_count >= wedge_cap:
                continue
            if metrics["pyramidal_like"] and pyramidal_count >= pyramidal_cap:
                continue
            if any(_silhouette_distance(candidate, other) < 0.10 for other in remaining):
                continue
            options.append(candidate)
        return options

    def swap_for(
        wanted_phenotype: str = "",
        *,
        reduce_wedge: bool = False,
        reduce_pyramidal: bool = False,
        excess_phenotype: str = "",
    ) -> bool:
        phenotype_counts, _scope_counts, _wedge_count = counts(result)
        if wanted_phenotype:
            # A required calm/curved/etc. candidate is often close to exactly
            # one already selected neighbour.  The old greedy swap tested an
            # unrelated low-score victim first, left that neighbour in place,
            # and then rejected the required candidate as a duplicate. Search
            # candidate/victim pairs causally and remove the actual conflict.
            candidates = sorted(
                (
                    candidate for candidate in universe
                    if _solid_morphology_metrics(candidate)["phenotype"] == wanted_phenotype
                    and not any(candidate is item for item in result)
                ),
                key=lambda item: item.score,
                reverse=True,
            )
            required_set = set(required)
            for candidate in candidates:
                conflicts = [
                    item for item in result
                    if _silhouette_distance(candidate, item) < 0.10
                ]
                if len(conflicts) > 1:
                    continue
                victims = conflicts or sorted(result, key=lambda item: item.score)
                for removed in victims:
                    removed_phenotype = _solid_morphology_metrics(removed)["phenotype"]
                    if (
                        removed_phenotype in required_set
                        and removed_phenotype != wanted_phenotype
                        and phenotype_counts[removed_phenotype] <= 1
                    ):
                        continue
                    remaining = [item for item in result if item is not removed]
                    remaining_scopes = Counter(_scope_key(item) for item in remaining)
                    if (
                        remaining_scopes.get(_scope_key(removed), 0) == 0
                        and _scope_key(candidate) != _scope_key(removed)
                    ):
                        continue
                    candidate_metrics = _solid_morphology_metrics(candidate)
                    remaining_counts, _unused_scope_counts, remaining_wedges = counts(remaining)
                    if remaining_counts[wanted_phenotype] >= phenotype_cap:
                        continue
                    if candidate_metrics["wedge_like"] and remaining_wedges >= wedge_cap:
                        continue
                    if candidate_metrics["pyramidal_like"] and sum(
                        bool(_solid_morphology_metrics(item)["pyramidal_like"])
                        for item in remaining
                    ) >= pyramidal_cap:
                        continue
                    if any(_silhouette_distance(candidate, other) < 0.10 for other in remaining):
                        continue
                    result[result.index(removed)] = candidate
                    return True
            return False
        removable = [
            candidate for candidate in result
            if (
                (reduce_wedge and _solid_morphology_metrics(candidate)["wedge_like"])
                or (reduce_pyramidal and _solid_morphology_metrics(candidate)["pyramidal_like"])
                or (excess_phenotype and _solid_morphology_metrics(candidate)["phenotype"] == excess_phenotype)
                or (
                    wanted_phenotype
                    and phenotype_counts[_solid_morphology_metrics(candidate)["phenotype"]] > 1
                )
            )
            and not (
                _solid_morphology_metrics(candidate)["phenotype"] in set(required)
                and phenotype_counts[_solid_morphology_metrics(candidate)["phenotype"]] <= 1
            )
        ]
        removable.sort(key=lambda item: item.score)
        for removed in removable:
            options = replacement_options(
                removed,
                wanted_phenotype=wanted_phenotype,
                require_non_wedge=reduce_wedge,
                require_non_pyramidal=reduce_pyramidal,
            )
            if not options:
                continue
            remaining = [item for item in result if item is not removed]
            winner = max(options, key=lambda candidate: (
                candidate.score
                + (min((_silhouette_distance(candidate, other) for other in remaining), default=1.0) * 0.45),
                -float((candidate.source.metadata.get("geometry_program_bridge_evidence") or {}).get("legal_fit_strength") or 0.0),
            ))
            result[result.index(removed)] = winner
            return True
        return False

    # First guarantee each available requested phenotype, then constrain the
    # visually observed wedge and dominant-phenotype shares.
    for phenotype in required:
        if not any(_solid_morphology_metrics(item)["phenotype"] == phenotype for item in result):
            swap_for(phenotype)
    while sum(bool(_solid_morphology_metrics(item)["wedge_like"]) for item in result) > wedge_cap:
        if not swap_for(reduce_wedge=True):
            break
    while sum(bool(_solid_morphology_metrics(item)["pyramidal_like"]) for item in result) > pyramidal_cap:
        if not swap_for(reduce_pyramidal=True):
            break
    while True:
        phenotype_counts, _scope_counts, _wedge_count = counts(result)
        excess = next((key for key, count in phenotype_counts.most_common() if count > phenotype_cap), "")
        if not excess or not swap_for(excess_phenotype=excess):
            break
    if len(result) < target:
        for candidate in sorted(universe, key=lambda item: item.score, reverse=True):
            if any(candidate is item for item in result):
                continue
            metrics = _solid_morphology_metrics(candidate)
            phenotype_counts, _scope_counts, wedge_count = counts(result)
            if phenotype_counts[metrics["phenotype"]] >= phenotype_cap:
                continue
            if metrics["wedge_like"] and wedge_count >= wedge_cap:
                continue
            if metrics["pyramidal_like"] and sum(
                bool(_solid_morphology_metrics(item)["pyramidal_like"])
                for item in result
            ) >= pyramidal_cap:
                continue
            if any(_silhouette_distance(candidate, other) < 0.10 for other in result):
                continue
            result.append(candidate)
            if len(result) >= target:
                break
    return result[:target]


def _bounded_visual_selection_pool(
    pool: list[_Candidate],
    *,
    per_family_scope: int = 3,
    per_seed_scope: int = 2,
) -> list[_Candidate]:
    """Bound expensive mesh comparison without losing scope/genotype breadth."""
    family_scope: Counter[tuple[str, str]] = Counter()
    seed_scope: Counter[tuple[str, str]] = Counter()
    fingerprints: set[tuple[Any, ...]] = set()
    retained: list[_Candidate] = []
    for candidate in sorted(pool, key=lambda item: item.score, reverse=True):
        fingerprint = _fingerprint(candidate)
        if fingerprint in fingerprints:
            continue
        scope = _scope_key(candidate)
        family = _geometry_program_family(candidate) or _roof_archetype(candidate)
        seed = _seed_family(candidate)
        if family_scope[(family, scope)] >= max(1, int(per_family_scope)):
            continue
        if seed_scope[(seed, scope)] >= max(1, int(per_seed_scope)):
            continue
        fingerprints.add(fingerprint)
        family_scope[(family, scope)] += 1
        seed_scope[(seed, scope)] += 1
        retained.append(candidate)
    return retained


def _program_pool(
    site: Polygon,
    building_type: str,
    height: float,
    floors: int,
    *,
    generation_context: LegalGenerationContext | None = None,
    parent_variant_indices: tuple[int, ...] = (0,),
    typed_graph_mutations: list[dict[str, Any]] | None = None,
    geometry_program_mutations: list[dict[str, Any]] | None = None,
    synthesis_requests: list[dict[str, Any]] | None = None,
    outcome_graph: GeometryOutcomeGraph | None = None,
    recursive_only: bool = False,
    program_dimensional_context: dict[str, Any] | None = None,
) -> tuple[list[_Candidate], dict[str, Any]]:
    accepted: list[_Candidate] = []
    evaluated = compiled = clean = program_passed = 0
    scope_stage_counts = {
        label: {
            "evaluated": 0,
            "compiled": 0,
            "projection_materialized": 0,
            "projection_failed": 0,
            "clean": 0,
            "program_passed": 0,
        }
        for label, _fraction in BASE_VOLUME_FRACTIONS
    }
    gate_names = ("role_coverage", "dominant_ratio", "site_coverage", "hierarchy", "coherence", "program_form")
    gate_diagnostics = {label: _empty_gate_diagnostic() for label, _fraction in BASE_VOLUME_FRACTIONS}
    geometry_gate_diagnostics: dict[str, dict[str, Any]] = {}
    requested_parent_indices = tuple(sorted({max(0, int(index)) for index in parent_variant_indices})) or (0,)
    directed_seeds = _agent_mutated_seeds(
        building_type,
        typed_graph_mutations,
        geometry_program_mutations,
        synthesis_requests,
        outcome_graph,
    )
    if recursive_only:
        directed_seeds = tuple(
            seed for seed in directed_seeds
            if any(
                note.startswith(("geometry_program_directive=", "geometry_program_payload="))
                for note in seed.notes
            )
        )
    parent_seeds = tuple(
        variant
        for seed_index, seed in enumerate(directed_seeds)
        for variant_index, variant in enumerate(program_seed_variants(
            seed,
            count=max(requested_parent_indices) + 1,
            random_seed=417 + seed_index * 97,
        ))
        if variant_index in requested_parent_indices
    )
    principles = tuple(build_book_language_registry()["principles"])
    for seed_index, seed in enumerate(parent_seeds):
        recursive_seed = any(
            note.startswith(("geometry_program_directive=", "geometry_program_payload="))
            for note in seed.notes
        )
        recursive_program: GeometryProgram | None = None
        if recursive_seed:
            payload = next((
                note.split("=", 1)[1]
                for note in seed.notes
                if note.startswith("geometry_program_payload=")
            ), "")
            try:
                recursive_program = GeometryProgram.from_dict(json.loads(payload))
            except (TypeError, ValueError, json.JSONDecodeError):
                recursive_program = None
        # The exhaustive 59/59 BOOK compiler audit remains a separate hard
        # regression. In portfolio synthesis, multiplying every recursive AST
        # by all 59 sentences and all three probes mostly relabelled the same
        # geometry thousands of times. Give each genotype a deterministic,
        # scope-balanced BOOK neighbourhood so the compute budget explores
        # more actual graph topologies instead.
        scheduled_principles = (
            _recursive_principle_schedule(principles, seed_index, count=12)
            if recursive_seed
            else tuple(enumerate(principles))
        )
        if recursive_seed and outcome_graph is not None:
            source_seed_name = next((
                note.split("=", 1)[1]
                for note in seed.notes
                if note.startswith("geometry_program_source_seed=")
            ), "")
            genotype_hash = recursive_program.program_hash() if recursive_program is not None else ""
            if genotype_hash and source_seed_name:
                principle_by_id = {
                    str(principle["principle_id"]): (index, principle)
                    for index, principle in enumerate(principles)
                }
                preferred_ids = outcome_graph.preferred_book_principle_ids(
                    source_seed=source_seed_name,
                    program_hash=genotype_hash,
                    fallback=(str(principle["principle_id"]) for _index, principle in scheduled_principles),
                    limit=12,
                )
                scheduled_principles = tuple(
                    principle_by_id[principle_id]
                    for principle_id in preferred_ids
                    if principle_id in principle_by_id
                )
        recursive_family = str((recursive_program.metadata if recursive_program else {}).get("family") or "")
        if recursive_program is not None:
            # Every agent genotype receives one topology-preserving vertical
            # EXTRUDE baseline before graph-memory reordering.  Otherwise a
            # scoped BOOK Boolean can erase the authored curve/void/wing/cut,
            # making it impossible to tell whether the genotype itself was
            # viable.  This is a generic mutation control, not a form template.
            principle_by_id = {
                str(principle["principle_id"]): (index, principle)
                for index, principle in enumerate(principles)
            }
            ordered_ids = tuple(dict.fromkeys((
                "book:operative:extrude",
                *(
                    ("book:operative:expand",)
                    if recursive_family == "agent_prismatic"
                    else ()
                ),
                *(str(item[1]["principle_id"]) for item in scheduled_principles),
            )))
            scheduled_principles = tuple(
                principle_by_id[principle_id]
                for principle_id in ordered_ids
                if principle_id in principle_by_id
            )[:12]
        for schedule_index, (principle_index, principle) in enumerate(scheduled_principles):
            execution_verbs = tuple(principle["execution_verbs"])
            # One BOOK sentence is a typed operator family, not one frozen
            # geometry.  Execute three bounded schema-derived parameter probes
            # so selection can compare real alternatives without parcel or
            # finished-form templates.
            sentence_variants = tuple(book_sentence_variants(execution_verbs, count=3))
            scheduled_variants = (
                (
                    (2, sentence_variants[2]),
                )
                if recursive_seed and (seed_index + principle_index) % 3 == 0
                else (
                    (0, sentence_variants[0]),
                )
                if recursive_seed
                else tuple(enumerate(sentence_variants))
            )
            for variant_index, operations in scheduled_variants:
                evaluated += 1
                suffix = str(principle["principle_id"]).split("book:", 1)[-1].replace(":", "_")
                scope_index = schedule_index if recursive_seed else principle_index
                base_volume_label = BASE_VOLUME_FRACTIONS[scope_index % len(BASE_VOLUME_FRACTIONS)][0]
                orientation = (
                    "vertical"
                    if recursive_program is not None and principle["principle_id"] == "book:operative:extrude"
                    else ("long_axis", "short_axis", "vertical")[(scope_index // len(BASE_VOLUME_FRACTIONS)) % 3]
                )
                scope_counts = scope_stage_counts[base_volume_label]
                scope_counts["evaluated"] += 1
                composed = compose_program_with_book_operations(
                    seed,
                    operations,
                    name_suffix=suffix,
                    base_volume_label=base_volume_label,
                    orientation=orientation,
                )
                sequence = VerbSequence(
                    name=f"{composed.name}__search_v{variant_index}",
                    label=composed.label,
                    calls=composed.calls,
                    notes=composed.notes,
                )
                compile_site = site
                generation_host_mode = "horizontal_buildable_envelope"
                recursive_directed = any(
                    note.startswith(("geometry_program_directive=", "geometry_program_payload="))
                    for note in sequence.notes
                )
                # The third typed parameter probe also explores the vertical
                # legal field.  Its base host is the sunlight-safe section at
                # the requested program height, so the resulting geometry is
                # born inside the envelope instead of repaired after selection.
                use_height_safe_host = variant_index == 2 or (
                    base_volume_label == "1/16" and variant_index == 0
                )
                if generation_context is not None and use_height_safe_host:
                    # Use the section at two thirds of design height.  The
                    # remaining cap is still measured by the exact downstream
                    # retention gate, while the host remains large enough to
                    # carry a coherent long-span/program role graph.
                    generation_section_ratio = 2.0 / 3.0
                    height_safe_site = generation_site_at_height(
                        generation_context,
                        height * generation_section_ratio,
                    )
                    if height_safe_site is not None:
                        compile_site = height_safe_site
                        generation_host_mode = "height_safe_sunlight_section"
                source = compile_sequence_to_source_mass(compile_site, sequence)
                if source is None:
                    continue
                source = _materialize_directed_geometry(
                    source,
                    sequence,
                    containment_host=compile_site,
                    upper_containment_host=(
                        generation_site_at_height(generation_context, height)
                        if recursive_directed and generation_context is not None
                        else None
                    ),
                )
                if source is None:
                    continue
                if program_dimensional_context:
                    source = replace(source, metadata={
                        **deepcopy(source.metadata),
                        "program_dimensional_context": deepcopy(program_dimensional_context),
                    })
                if generation_context is not None:
                    metadata = deepcopy(source.metadata)
                    legal_evidence = deepcopy(generation_context.evidence)
                    legal_evidence.update({
                        "generation_host_mode": generation_host_mode,
                        "candidate_generation_site_area_m2": round(float(compile_site.area), 3),
                        "requested_program_height_m": float(height),
                        "generation_host_section_height_m": (
                            round(float(height) * generation_section_ratio, 3)
                            if generation_host_mode == "height_safe_sunlight_section"
                            else 0.0
                        ),
                    })
                    metadata["legal_generation_context_evidence"] = legal_evidence
                    source = replace(source, metadata=metadata)
                    if (
                        not recursive_directed
                        and base_volume_label == "1/16"
                        and generation_host_mode == "horizontal_buildable_envelope"
                    ):
                        source = fit_source_to_sunlight_field(
                            source,
                            generation_context,
                            height_m=height,
                            floors=floors,
                        )
                compiled += 1
                scope_counts["compiled"] += 1
                projection_evidence = source.metadata.get("program_book_projection_evidence") or {}
                if projection_evidence.get("status") != "materialized":
                    scope_counts["projection_failed"] += 1
                    continue
                scope_counts["projection_materialized"] += 1
                signature = source.signature()
                raw_surfaces = int(signature.get("surface_count") or 0)
                effective_surfaces = int(signature.get("effective_surface_count") or raw_surfaces)
                profiled = bool((signature.get("continuous_surface_evidence") or {}).get("hard_pass"))
                recursive_mesh = bool(source.metadata.get("geometry_program_bridge_evidence"))
                # A manifold solid may need hundreds of kernel triangles for
                # a smooth bend or array. Those triangles are not hundreds of
                # architectural surfaces. Keep the clean-mass gate on visible
                # volumes and semantic/effective surfaces while retaining a
                # generous corruption guard for the render transport.
                raw_surface_limit = 2048 if recursive_mesh else (160 if profiled else 48)
                if len(source.volumes) > 5 or raw_surfaces > raw_surface_limit or effective_surfaces > 28:
                    continue
                compilation_metrics = (
                    source.metadata.get("geometry_program_compilation") or {}
                ).get("metrics") or {}
                if (
                    recursive_mesh
                    and int(compilation_metrics.get("component_count") or 1) > 1
                    and float(compilation_metrics.get("minimum_component_volume_ratio") or 0.0) < 0.08
                ):
                    # A technically manifold speck is still a disconnected
                    # Lego fragment. Every visible component must carry at
                    # least 8% of the compiled solid volume.
                    continue
                if not _inside_site(source, compile_site):
                    continue
                clean += 1
                scope_counts["clean"] += 1
                feature = source_feature(
                    source,
                    sequence,
                    building_type=building_type,
                    height=height,
                    floors=floors,
                    site_area=float(compile_site.area),
                )
                program = attach_program_massing_evidence(feature, building_type=building_type)
                spatial = feature["properties"]["program_spatial_evidence"]
                program_form_gate = _program_form_gate(source, building_type)
                feature["properties"]["program_form_gate"] = program_form_gate
                gate_pass = {
                    "role_coverage": bool(all(spatial.get("required_role_hits") or ())),
                    "dominant_ratio": float(spatial.get("dominant_ratio_score") or 0.0) >= 0.55,
                    "site_coverage": float(spatial.get("site_coverage_score") or 0.0) >= 0.55,
                    "hierarchy": float(spatial.get("hierarchy_score") or 0.0) >= 0.50,
                    "coherence": bool((feature["properties"].get("source_signature", {}).get("coherence_evidence") or {}).get("hard_pass", False)),
                    "program_form": bool(program_form_gate["hard_pass"]),
                }
                failed_gates = tuple(name for name in gate_names if not gate_pass[name])
                combined_program_hard_pass = bool(program["hard_pass"]) and bool(program_form_gate["hard_pass"])
                _record_gate_diagnostic(
                    gate_diagnostics[base_volume_label],
                    spatial=spatial,
                    hard_pass=combined_program_hard_pass,
                    failed_gates=failed_gates,
                    program_form_failures=tuple(program_form_gate.get("failures") or ()),
                )
                geometry_family = str(source.metadata.get("family") or "") if source.metadata.get("geometry_program_bridge_evidence") else ""
                if geometry_family:
                    _record_gate_diagnostic(
                        geometry_gate_diagnostics.setdefault(geometry_family, _empty_gate_diagnostic()),
                        spatial=spatial,
                        hard_pass=combined_program_hard_pass,
                        failed_gates=failed_gates,
                        program_form_failures=tuple(program_form_gate.get("failures") or ()),
                    )
                    if outcome_graph is not None:
                        outcome_graph.observe_program_evaluation(
                            program_slug=next(
                                (slug for slug, label, _height, _floors in PROGRAMS if label == building_type),
                                str(building_type),
                            ),
                            source=source,
                            sequence_name=sequence.name,
                            principle_id=str(principle["principle_id"]),
                            spatial=spatial,
                            failed_gates=failed_gates,
                        )
                if not combined_program_hard_pass:
                    continue
                program_passed += 1
                scope_counts["program_passed"] += 1
                score = float(program["program_fit_score"]) * 0.56 + float(spatial["architectural_score"]) * 0.44
                bridge = source.metadata.get("geometry_program_bridge_evidence") or {}
                fit_strength = float(bridge.get("legal_fit_strength") or 0.0) if isinstance(bridge, dict) else 0.0
                # Selection must not reward a legal interpolation that erases
                # the AST's section language. Hard gates already decide legal
                # validity; this small tie-break preserves design geometry.
                score -= fit_strength * 0.10
                accepted.append(_Candidate(
                    str(principle["principle_id"]),
                    str(principle["kind"]),
                    str(principle["label"]),
                    sequence,
                    source,
                    feature,
                    round(score, 6),
                ))
    summarized_gate_diagnostics = {
        label: _summarize_gate_diagnostic(diagnostic)
        for label, diagnostic in gate_diagnostics.items()
    }
    return accepted, {
        "evaluated": evaluated,
        "compiled": compiled,
        "clean": clean,
        "program_passed": program_passed,
        "base_role_seed_count": len(program_seed_sequences(building_type)),
        "agent_mutated_seed_count": max(0, len(directed_seeds) - len(program_seed_sequences(building_type))),
        "recursive_geometry_seed_count": sum(
            any(
                note.startswith(("geometry_program_directive=", "geometry_program_payload="))
                for note in seed.notes
            )
            for seed in directed_seeds
        ),
        "geometry_synthesis_request_source": (
            "program_profile_control+vlm_or_session_directive"
            if synthesis_requests
            else "program_profile_control"
        ),
        "geometry_synthesis_request_count": (
            min(2, len(program_seed_sequences(building_type)))
            + len(tuple(record for record in (synthesis_requests or ()) if isinstance(record, dict)))
        ),
        "geometry_program_vlm_status_counts": dict(sorted(Counter(
            note.split("=", 1)[1]
            for seed in directed_seeds
            for note in seed.notes
            if note.startswith("geometry_program_vlm_status=")
        ).items())),
        "geometry_program_vlm_causal_trace": {
            "maximum_reference_count": max((
                int(note.split("=", 1)[1])
                for seed in directed_seeds for note in seed.notes
                if note.startswith("geometry_program_vlm_reference_count=")
            ), default=0),
            "maximum_memory_observation_count": max((
                int(note.split("=", 1)[1])
                for seed in directed_seeds for note in seed.notes
                if note.startswith("geometry_program_vlm_memory_observation_count=")
            ), default=0),
            "geometry_revision_count": max((
                int(note.split("=", 1)[1])
                for seed in directed_seeds for note in seed.notes
                if note.startswith("geometry_program_vlm_revision_count=")
            ), default=0),
        },
        "program_passed_by_seed_family": dict(sorted(Counter(_seed_family(candidate) for candidate in accepted).items())),
        "program_passed_by_section_family": dict(sorted(Counter(_section_family(candidate) for candidate in accepted).items())),
        "scope_stage_counts": scope_stage_counts,
        "program_gate_diagnostics_by_scope": summarized_gate_diagnostics,
        "program_gate_diagnostics_by_recursive_geometry_family": {
            family: _summarize_gate_diagnostic(diagnostic)
            for family, diagnostic in sorted(geometry_gate_diagnostics.items())
        },
        "program_gate_diagnostics_total": _merge_gate_diagnostics(summarized_gate_diagnostics),
    }


def _recursive_principle_schedule(
    principles: tuple[dict[str, Any], ...],
    seed_index: int,
    *,
    count: int,
) -> tuple[tuple[int, dict[str, Any]], ...]:
    """Assign a reproducible BOOK neighbourhood with all six p.3 scopes.

    Step 5 is coprime to the 59-principle corpus and also walks every residue
    modulo six, while the seed offset prevents every genotype from seeing the
    same small subset. No geometry or parcel coordinate is encoded here.
    """
    if not principles:
        return ()
    total = len(principles)
    wanted = max(6, min(total, int(count)))
    indices: list[int] = []
    cursor = (int(seed_index) * 7) % total
    while len(indices) < wanted:
        if cursor not in indices:
            indices.append(cursor)
        cursor = (cursor + 5) % total
    return tuple((index, principles[index]) for index in indices)


def _empty_gate_diagnostic() -> dict[str, Any]:
    gate_names = ("role_coverage", "dominant_ratio", "site_coverage", "hierarchy", "coherence", "program_form")
    return {
        "candidate_count": 0,
        "hard_pass_count": 0,
        "failed_candidate_count": 0,
        "gate_failed_counts": {name: 0 for name in gate_names},
        "exclusive_gate_failed_counts": {name: 0 for name in gate_names},
        "failure_signature_counts": {},
        "program_form_failure_counts": {},
        "metric_samples": {
            "role_coverage_score": [],
            "dominant_component_ratio": [],
            "dominant_ratio_score": [],
            "site_coverage_ratio": [],
            "site_coverage_score": [],
            "hierarchy_score": [],
            "coherence_score": [],
        },
    }


def _record_gate_diagnostic(
    diagnostic: dict[str, Any],
    *,
    spatial: dict[str, Any],
    hard_pass: bool,
    failed_gates: tuple[str, ...],
    program_form_failures: tuple[str, ...] = (),
) -> None:
    diagnostic["candidate_count"] += 1
    diagnostic["hard_pass_count" if hard_pass else "failed_candidate_count"] += 1
    for name in failed_gates:
        diagnostic["gate_failed_counts"][name] += 1
    if len(failed_gates) == 1:
        diagnostic["exclusive_gate_failed_counts"][failed_gates[0]] += 1
    signature = "+".join(failed_gates) if failed_gates else "none"
    diagnostic["failure_signature_counts"][signature] = diagnostic["failure_signature_counts"].get(signature, 0) + 1
    for reason in program_form_failures:
        diagnostic["program_form_failure_counts"][reason] = (
            diagnostic["program_form_failure_counts"].get(reason, 0) + 1
        )
    for name in diagnostic["metric_samples"]:
        diagnostic["metric_samples"][name].append(float(spatial.get(name) or 0.0))


def _metric_summary(values: list[float]) -> dict[str, float | int]:
    if not values:
        return {"count": 0, "minimum": 0.0, "mean": 0.0, "maximum": 0.0}
    return {
        "count": len(values),
        "minimum": round(min(values), 4),
        "mean": round(sum(values) / len(values), 4),
        "maximum": round(max(values), 4),
    }


def _summarize_gate_diagnostic(diagnostic: dict[str, Any]) -> dict[str, Any]:
    result = {key: deepcopy(value) for key, value in diagnostic.items() if key != "metric_samples"}
    result["metric_summaries"] = {
        name: _metric_summary(values)
        for name, values in diagnostic["metric_samples"].items()
    }
    return result


def _merge_gate_diagnostics(by_scope: dict[str, dict[str, Any]]) -> dict[str, Any]:
    gate_names = ("role_coverage", "dominant_ratio", "site_coverage", "hierarchy", "coherence", "program_form")
    total = {
        "candidate_count": sum(item["candidate_count"] for item in by_scope.values()),
        "hard_pass_count": sum(item["hard_pass_count"] for item in by_scope.values()),
        "failed_candidate_count": sum(item["failed_candidate_count"] for item in by_scope.values()),
        "gate_failed_counts": {
            name: sum(item["gate_failed_counts"][name] for item in by_scope.values())
            for name in gate_names
        },
        "exclusive_gate_failed_counts": {
            name: sum(item["exclusive_gate_failed_counts"][name] for item in by_scope.values())
            for name in gate_names
        },
        "failure_signature_counts": {},
        "program_form_failure_counts": {},
    }
    for item in by_scope.values():
        for signature, count in item["failure_signature_counts"].items():
            total["failure_signature_counts"][signature] = total["failure_signature_counts"].get(signature, 0) + count
        for reason, count in item["program_form_failure_counts"].items():
            total["program_form_failure_counts"][reason] = total["program_form_failure_counts"].get(reason, 0) + count
    return total


def _candidate_language_descriptor(candidate: _Candidate) -> dict[str, Any]:
    source = candidate.source
    poly = source.footprint
    aspect = _oriented_aspect(poly)
    compactness = 4.0 * pi * float(poly.area) / max(float(poly.length) ** 2, 1e-9)
    spatial = candidate.feature.get("properties", {}).get("program_spatial_evidence", {})
    section = source.metadata.get("program_section_graph_evidence") or {}
    materialized = section.get("materialized_nodes") if isinstance(section, dict) else ()
    controls = tuple(
        tuple(tuple(float(value) for value in item) for item in (node.get("section_controls") or ()))
        for node in (materialized or ())
        if isinstance(node, dict) and node.get("section_controls")
    )
    role_tokens = Counter()
    for volume in source.volumes:
        role = str(volume.role).lower()
        for token in (
            "hall", "service", "entry", "monitor", "canopy", "gallery",
            "public", "bridge", "ramp", "court", "street", "terrace", "ribbon",
        ):
            if token in role:
                role_tokens[token] += 1
    for zone in source.metadata.get("program_space_zones") or ():
        role = str(zone.get("role") or "").lower() if isinstance(zone, dict) else ""
        for token in (
            "hall", "service", "entry", "monitor", "canopy", "gallery",
            "public", "bridge", "ramp", "court", "street", "terrace", "ribbon",
        ):
            if token in role:
                role_tokens[token] += 1
    morphology = _solid_morphology_metrics(candidate)
    articulation = _architectural_articulation_metrics(source)
    program_form = candidate.feature.get("properties", {}).get("program_form_gate", {})
    return {
        "seed_family": _seed_family(candidate),
        "section_family": _section_family(candidate),
        "roof_archetype": _roof_archetype(candidate),
        "chassis_family": _chassis_family(candidate),
        "geometry_program_family": _geometry_program_family(candidate) or "none",
        "solid_phenotype": morphology["phenotype"],
        "body_phenotype": morphology.get("body_phenotype") or morphology["phenotype"],
        "section_phenotype": morphology.get("section_phenotype") or "none",
        "wedge_like": morphology["wedge_like"],
        "pyramidal_like": morphology["pyramidal_like"],
        "collapsed_profiled_tent_like": bool(morphology.get("collapsed_profiled_tent_like")),
        "degenerate_sheet_like": morphology["degenerate_sheet_like"],
        "horizontal_surface_ratio": morphology["horizontal_surface_ratio"],
        "vertical_surface_ratio": morphology["vertical_surface_ratio"],
        "sloped_surface_ratio": morphology["sloped_surface_ratio"],
        "normal_direction_bin_count": morphology["normal_direction_bin_count"],
        "horizontal_level_count": morphology["horizontal_level_count"],
        "plan_convexity": morphology["plan_convexity"],
        "upper_area_ratio": morphology["upper_area_ratio"],
        "solid_genus": morphology["genus"],
        "solid_component_count": morphology["component_count"],
        "book_scope": _scope_key(candidate),
        "oriented_plan_aspect_ratio": round(aspect, 4),
        "plan_compactness": round(compactness, 4),
        "plan_family": "bar" if aspect >= 2.2 else ("compact" if aspect <= 1.35 else "intermediate"),
        "dominant_component_ratio": round(float(spatial.get("dominant_component_ratio") or 0.0), 4),
        "site_coverage_ratio": round(float(spatial.get("site_coverage_ratio") or 0.0), 4),
        "hierarchy_score": round(float(spatial.get("hierarchy_score") or 0.0), 4),
        "section_control_signature": controls,
        "semantic_role_tokens": dict(sorted(role_tokens.items())),
        "body_rule_count": articulation["body_rule_count"],
        "program_body_rule_count": articulation["program_rule_count"],
        "book_body_rule_count": articulation["book_rule_count"],
        "body_rule_family_counts": articulation["family_counts"],
        "body_rules": articulation["rules"],
        "measured_clear_span_m": float(program_form.get("measured_clear_span_m") or 0.0),
        "measured_solid_height_m": float(program_form.get("measured_solid_height_m") or 0.0),
        "height_to_clear_span_ratio": float(program_form.get("height_to_clear_span_ratio") or 0.0),
    }


def _portfolio_language_metrics(selected: list[_Candidate]) -> dict[str, Any]:
    descriptors = [_candidate_language_descriptor(candidate) for candidate in selected]
    seed_counts = Counter(item["seed_family"] for item in descriptors)
    section_counts = Counter(item["section_family"] for item in descriptors)
    roof_archetype_counts = Counter(item["roof_archetype"] for item in descriptors)
    chassis_counts = Counter(item["chassis_family"] for item in descriptors)
    geometry_program_counts = Counter(
        item["geometry_program_family"]
        for item in descriptors
        if item["geometry_program_family"] != "none"
    )
    phenotype_counts = Counter(item["solid_phenotype"] for item in descriptors)
    section_phenotype_counts = Counter(item["section_phenotype"] for item in descriptors)
    wedge_like_count = sum(bool(item["wedge_like"]) for item in descriptors)
    pyramidal_like_count = sum(bool(item["pyramidal_like"]) for item in descriptors)
    plan_counts = Counter(item["plan_family"] for item in descriptors)
    control_signatures = {
        json.dumps(item["section_control_signature"], sort_keys=True)
        for item in descriptors
        if item["section_control_signature"]
    }

    def mean(name: str) -> float:
        values = [float(item[name]) for item in descriptors]
        return round(sum(values) / len(values), 4) if values else 0.0

    total = max(1, len(descriptors))
    return {
        "schema_version": "arr.maas.program_language_metrics.v1",
        "candidate_count": len(descriptors),
        "seed_family_counts": dict(sorted(seed_counts.items())),
        "seed_family_count": len(seed_counts),
        "dominant_seed_family_share": round(max(seed_counts.values(), default=0) / total, 4),
        "roof_section_family_counts": dict(sorted(section_counts.items())),
        "roof_section_family_count": len(section_counts),
        "dominant_roof_section_family_share": round(max(section_counts.values(), default=0) / total, 4),
        "roof_archetype_counts": dict(sorted(roof_archetype_counts.items())),
        "roof_archetype_count": len(roof_archetype_counts),
        "dominant_roof_archetype_share": round(max(roof_archetype_counts.values(), default=0) / total, 4),
        "chassis_family_counts": dict(sorted(chassis_counts.items())),
        "chassis_family_count": len(chassis_counts),
        "dominant_chassis_family_share": round(max(chassis_counts.values(), default=0) / total, 4),
        "recursive_geometry_program_counts": dict(sorted(geometry_program_counts.items())),
        "recursive_geometry_program_count": sum(geometry_program_counts.values()),
        "recursive_geometry_family_count": len(geometry_program_counts),
        "solid_phenotype_counts": dict(sorted(phenotype_counts.items())),
        "solid_phenotype_count": len(phenotype_counts),
        "dominant_solid_phenotype_share": round(max(phenotype_counts.values(), default=0) / total, 4),
        "section_phenotype_counts": dict(sorted(section_phenotype_counts.items())),
        "section_phenotype_count": len(section_phenotype_counts),
        "collapsed_profiled_tent_like_count": sum(
            bool(item["collapsed_profiled_tent_like"]) for item in descriptors
        ),
        "wedge_like_count": wedge_like_count,
        "wedge_like_share": round(wedge_like_count / total, 4),
        "pyramidal_like_count": pyramidal_like_count,
        "pyramidal_like_share": round(pyramidal_like_count / total, 4),
        "mean_horizontal_surface_ratio": mean("horizontal_surface_ratio"),
        "mean_vertical_surface_ratio": mean("vertical_surface_ratio"),
        "mean_sloped_surface_ratio": mean("sloped_surface_ratio"),
        "section_control_signature_count": len(control_signatures),
        "plan_family_counts": dict(sorted(plan_counts.items())),
        "mean_oriented_plan_aspect_ratio": mean("oriented_plan_aspect_ratio"),
        "mean_plan_compactness": mean("plan_compactness"),
        "mean_dominant_component_ratio": mean("dominant_component_ratio"),
        "mean_site_coverage_ratio": mean("site_coverage_ratio"),
        "mean_hierarchy_score": mean("hierarchy_score"),
        "mean_volume_count": round(sum(len(candidate.source.volumes) for candidate in selected) / total, 4),
        "mean_effective_surface_count": round(
            sum(int(candidate.source.signature().get("effective_surface_count") or 0) for candidate in selected) / total,
            4,
        ),
        "mean_body_rule_count": mean("body_rule_count"),
        "maximum_body_rule_count": max((int(item["body_rule_count"]) for item in descriptors), default=0),
        "body_rule_family_counts": dict(sorted(sum((Counter(item["body_rule_family_counts"]) for item in descriptors), Counter()).items())),
        "semantic_role_token_counts": dict(sorted(sum((Counter(item["semantic_role_tokens"]) for item in descriptors), Counter()).items())),
    }


def _cross_program_language_comparison(
    selected_by_program: dict[str, list[_Candidate]],
    metrics_by_program: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    slugs = tuple(selected_by_program)
    pairs: list[dict[str, Any]] = []
    for index, left_slug in enumerate(slugs):
        for right_slug in slugs[:index]:
            left = selected_by_program[left_slug]
            right = selected_by_program[right_slug]
            distances = [
                _silhouette_distance(left_candidate, right_candidate)
                for left_candidate in left
                for right_candidate in right
            ]
            left_sections = set(metrics_by_program[left_slug]["roof_section_family_counts"])
            right_sections = set(metrics_by_program[right_slug]["roof_section_family_counts"])
            union = left_sections | right_sections
            jaccard_distance = 1.0 - len(left_sections & right_sections) / max(1, len(union))
            pairs.append({
                "programs": [right_slug, left_slug],
                "mean_cross_program_silhouette_distance": round(sum(distances) / len(distances), 4) if distances else 0.0,
                "minimum_cross_program_silhouette_distance": round(min(distances), 4) if distances else 0.0,
                "roof_section_family_jaccard_distance": round(jaccard_distance, 4),
                "mean_plan_aspect_ratio_delta": round(abs(
                    metrics_by_program[left_slug]["mean_oriented_plan_aspect_ratio"]
                    - metrics_by_program[right_slug]["mean_oriented_plan_aspect_ratio"]
                ), 4),
                "mean_plan_compactness_delta": round(abs(
                    metrics_by_program[left_slug]["mean_plan_compactness"]
                    - metrics_by_program[right_slug]["mean_plan_compactness"]
                ), 4),
                "mean_dominant_ratio_delta": round(abs(
                    metrics_by_program[left_slug]["mean_dominant_component_ratio"]
                    - metrics_by_program[right_slug]["mean_dominant_component_ratio"]
                ), 4),
            })
    return {
        "schema_version": "arr.maas.cross_program_language_comparison.v1",
        "program_metrics": metrics_by_program,
        "pairwise_comparisons": pairs,
        "interpretation": "Measured geometry descriptors; visual review remains required.",
    }


def _hard_gate_count_summary(
    report: dict[str, Any] | None,
    candidates: list[_Candidate],
) -> dict[str, Any]:
    candidate_count = len(candidates)
    if report is None:
        return {"status": "not_run", "candidate_count": candidate_count}
    summary = {
        key: report[key]
        for key in (
            "candidate_count",
            "legal_hard_pass_count",
            "geometry_retention_pass_count",
            "parking_hard_pass_count",
            "combined_hard_pass_count",
            "mean_volume_retention",
            "minimum_volume_retention",
            "legal_failure_reason_counts",
            "geometry_failure_reason_counts",
            "parking_failure_reason_counts",
        )
    }
    by_scope: dict[str, dict[str, int]] = {}
    by_host_mode: Counter[str] = Counter()
    hard_pass_by_host_mode: Counter[str] = Counter()
    by_geometry_family: dict[str, dict[str, Any]] = {}
    by_geometry_genotype: dict[str, dict[str, Any]] = {}
    for candidate, row in zip(candidates, report["rows"]):
        scope = str(row.get("book_scope") or "1/1")
        bucket = by_scope.setdefault(scope, {
            "candidate_count": 0,
            "legal_hard_pass_count": 0,
            "geometry_retention_pass_count": 0,
            "parking_hard_pass_count": 0,
            "combined_hard_pass_count": 0,
        })
        bucket["candidate_count"] += 1
        bucket["legal_hard_pass_count"] += int(bool(row["legal_projection"]["hard_pass"]))
        bucket["geometry_retention_pass_count"] += int(bool(row["legal_projection"]["geometry_retention_pass"]))
        bucket["parking_hard_pass_count"] += int(bool(row["parking_hard_gate"]["hard_pass"]))
        bucket["combined_hard_pass_count"] += int(bool(row["combined_hard_pass"]))
        host_mode = str(row.get("generation_host_mode") or "horizontal_buildable_envelope")
        by_host_mode[host_mode] += 1
        if row["combined_hard_pass"]:
            hard_pass_by_host_mode[host_mode] += 1
        geometry_family = _geometry_program_family(candidate)
        if geometry_family:
            empty_bucket = lambda: {
                "candidate_count": 0,
                "geometry_retention_pass_count": 0,
                "combined_hard_pass_count": 0,
                "volume_retentions": [],
                "failure_reason_counts": Counter(),
            }
            for bucket in (
                by_geometry_family.setdefault(geometry_family, empty_bucket()),
                by_geometry_genotype.setdefault(_seed_family(candidate), empty_bucket()),
            ):
                bucket["candidate_count"] += 1
                bucket["geometry_retention_pass_count"] += int(bool(row["legal_projection"]["geometry_retention_pass"]))
                bucket["combined_hard_pass_count"] += int(bool(row["combined_hard_pass"]))
                bucket["volume_retentions"].append(float(row["legal_projection"].get("volume_retention") or 0.0))
                bucket["failure_reason_counts"].update(row["legal_projection"].get("geometry_failure_reasons") or ())
    summary["by_scope"] = dict(sorted(by_scope.items()))
    summary["candidate_count_by_generation_host"] = dict(sorted(by_host_mode.items()))
    summary["combined_hard_pass_by_generation_host"] = dict(sorted(hard_pass_by_host_mode.items()))
    def serialize_geometry_buckets(buckets: dict[str, dict[str, Any]]) -> dict[str, Any]:
        return {
        family: {
            "candidate_count": bucket["candidate_count"],
            "geometry_retention_pass_count": bucket["geometry_retention_pass_count"],
            "combined_hard_pass_count": bucket["combined_hard_pass_count"],
            "mean_volume_retention": round(sum(bucket["volume_retentions"]) / len(bucket["volume_retentions"]), 4),
            "minimum_volume_retention": round(min(bucket["volume_retentions"]), 4),
            "failure_reason_counts": dict(sorted(bucket["failure_reason_counts"].items())),
        }
        for family, bucket in sorted(buckets.items())
        }

    summary["by_recursive_geometry_family"] = serialize_geometry_buckets(by_geometry_family)
    summary["by_recursive_geometry_genotype"] = serialize_geometry_buckets(by_geometry_genotype)
    return summary


def run_book_program_portfolios(
    site: Polygon,
    *,
    pnu: str,
    output_dir: Path,
    site_origin_utm: tuple[float, float] = (0.0, 0.0),
    constraints: list[dict[str, Any]] | None = None,
    regulation_evidence: dict[str, Any] | None = None,
    sunlight_envelope: dict[str, Any] | None = None,
    parking_options: dict[str, Any] | None = None,
    program_slugs: tuple[str, ...] | None = None,
    recursive_only: bool = False,
    visual_directive_path: Path | None = None,
    outcome_graph_path: Path | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    directive_dir = visual_directive_path.parent if visual_directive_path is not None else output_dir
    visual_directive_payload = _load_visual_directive(directive_dir, pnu)
    outcome_graph_path = outcome_graph_path or (output_dir / "maas-geometry-mutation-outcome-graph.json")
    outcome_graph = GeometryOutcomeGraph.load(outcome_graph_path, pnu=pnu)
    program_results: list[dict[str, Any]] = []
    selected_by_program: dict[str, list[_Candidate]] = {}
    metrics_by_program: dict[str, dict[str, Any]] = {}
    board_paths: list[Path] = []
    requested_slugs = set(program_slugs or ())
    for slug, building_type, height, floors in PROGRAMS:
        if requested_slugs and slug not in requested_slugs:
            continue
        started = perf_counter()
        outcome_graph.begin_program_run(slug)
        program_visual_directive = dict(
            (visual_directive_payload.get("programs") or {}).get(slug) or {}
        )
        typed_graph_mutations = program_visual_directive.get("typed_graph_mutations") or []
        geometry_program_mutations = program_visual_directive.get("geometry_program_mutations") or []
        synthesis_requests = program_visual_directive.get("geometry_synthesis_requests") or []
        if synthesis_requests:
            live_requested = bool(program_visual_directive.get("live_geometry_vlm_revision"))
            reference_matches = [
                {
                    "local_path": str(path),
                    "title": Path(str(path)).stem,
                    "selection_role": "operation_language_reference_not_shape_template",
                    "source": "portfolio_vlm_directive",
                }
                for path in visual_directive_payload.get("reference_images") or ()
            ]
            synthesis_requests = [
                {
                    **dict(request),
                    "live_vlm_revision": bool(request.get("live_vlm_revision", live_requested)),
                    "reference_matches": reference_matches,
                    "required_body_phenotypes": list(
                        program_visual_directive.get("required_solid_phenotypes") or ()
                    ),
                }
                for request in synthesis_requests
                if isinstance(request, dict)
            ]
        geometry_program_authority = bool(
            recursive_only or synthesis_requests or geometry_program_mutations
        )
        generation_context = (
            build_legal_generation_context(
                site_local_utm=site,
                site_origin_utm=site_origin_utm,
                building_type=building_type,
                constraints=constraints,
                sunlight_envelope=sunlight_envelope,
            )
            if constraints is not None
            else None
        )
        generation_site = generation_context.generation_site if generation_context is not None else site
        dimensional_context = _program_dimensional_context(
            generation_site,
            building_type,
            height,
            floors,
        )
        if dimensional_context["status"] == "infeasible":
            empty_metrics = _portfolio_language_metrics([])
            board = output_dir / f"maas-book-{slug}-20.png"
            render_archive_sheet(
                [],
                board,
                title=f"MAAS BOOK × {building_type} · PNU {pnu} · PROGRAM INFEASIBLE",
            )
            board_paths.append(board)
            selected_by_program[slug] = []
            metrics_by_program[slug] = empty_metrics
            program_results.append({
                "program": building_type,
                "slug": slug,
                "status": "fail",
                "selected_count": 0,
                "book_operation_count": 0,
                "book_principle_kind_counts": {},
                "visual_language_count": 0,
                "book_base_volume_scope_count": 0,
                "book_base_volume_scopes": [],
                "near_duplicate_pair_count": 0,
                "program_language_metrics": empty_metrics,
                "program_dimensional_context": dimensional_context,
                "vlm_portfolio_directive": {"active": bool(program_visual_directive)},
                "downstream_hard_gate": {"status": "not_run", "candidate_count": 0},
                "counts": {},
                "failures": list(dimensional_context.get("failure_reasons") or ("program_dimensional_infeasible",)),
                "missing_vlm_required_roof_archetypes": [],
                "missing_required_solid_phenotypes": [],
                "duration_seconds": round(perf_counter() - started, 3),
                "rows": [],
                "png": str(board),
            })
            continue
        height = float(dimensional_context["effective_height_m"])
        floors = int(dimensional_context["effective_floors"])
        pool, counts = _program_pool(
            generation_site,
            building_type,
            height,
            floors,
            generation_context=generation_context,
            typed_graph_mutations=typed_graph_mutations,
            geometry_program_mutations=geometry_program_mutations,
            synthesis_requests=synthesis_requests,
            outcome_graph=outcome_graph,
            recursive_only=geometry_program_authority,
            program_dimensional_context=dimensional_context,
        )
        counts["program_dimensional_context"] = deepcopy(dimensional_context)
        preselection_hard_gate = None
        selection_pool = pool
        if generation_context is not None:
            preselection_hard_gate = evaluate_accepted_sources_downstream(
                pool,
                site_local_utm=site,
                site_origin_utm=site_origin_utm,
                pnu=pnu,
                building_type=building_type,
                height_m=height,
                floors=floors,
                constraints=constraints,
                regulation_evidence=regulation_evidence or {},
                sunlight_envelope=sunlight_envelope,
                parking_options=parking_options,
                generation_context=generation_context,
            )
            selection_pool = [
                candidate
                for candidate, row in zip(pool, preselection_hard_gate["rows"])
                if row["combined_hard_pass"]
            ]
        counts["preselection_hard_gate"] = _hard_gate_count_summary(preselection_hard_gate, pool)
        counts["geometry_program_authority"] = {
            "required": geometry_program_authority,
            "reason": (
                "recursive_only_flag"
                if recursive_only
                else (
                    "geometry_synthesis_request"
                    if synthesis_requests
                    else "geometry_program_mutation"
                )
            ) if geometry_program_authority else "legacy_and_recursive_allowed",
            "legacy_geometry_final_selection_allowed": not geometry_program_authority,
        }
        live_vlm_selection_required = bool(
            program_visual_directive.get("live_geometry_vlm_revision")
            and program_visual_directive.get("geometry_synthesis_requests")
        )
        pre_vlm_selection_count = len(selection_pool)
        if live_vlm_selection_required:
            selection_pool = [
                candidate for candidate in selection_pool
                if _vlm_reviewed_program_candidate(candidate)
            ]
        counts["vlm_final_selection_gate"] = {
            "required": live_vlm_selection_required,
            "input_count": pre_vlm_selection_count,
            "reviewed_program_fit_pass_count": len(selection_pool),
            "unreviewed_or_program_rejected_count": pre_vlm_selection_count - len(selection_pool),
        }
        degenerate_sheet_count = sum(
            bool(_solid_morphology_metrics(candidate)["degenerate_sheet_like"])
            for candidate in selection_pool
        )
        selection_pool = [
            candidate for candidate in selection_pool
            if not _solid_morphology_metrics(candidate)["degenerate_sheet_like"]
        ]
        raw_selection_pool_count = len(selection_pool)
        selection_pool = _bounded_visual_selection_pool(selection_pool)
        counts["visual_selection_pool"] = {
            "input_count": raw_selection_pool_count,
            "bounded_count": len(selection_pool),
            "per_geometry_family_scope_cap": 3,
            "per_seed_scope_cap": 2,
            "degenerate_sheet_like_rejected_count": degenerate_sheet_count,
            "measured_solid_phenotype_counts": dict(sorted(Counter(
                _solid_morphology_metrics(candidate)["phenotype"]
                for candidate in selection_pool
            ).items())),
            "measured_wedge_like_count": sum(
                bool(_solid_morphology_metrics(candidate)["wedge_like"])
                for candidate in selection_pool
            ),
            "measured_pyramidal_like_count": sum(
                bool(_solid_morphology_metrics(candidate)["pyramidal_like"])
                for candidate in selection_pool
            ),
        }
        selected = _select(selection_pool, 20, visual_directive=program_visual_directive)
        outcome_graph.observe_candidates(
            program_slug=slug,
            candidates=pool,
            downstream_report=preselection_hard_gate,
            selected=selected,
        )
        missing_scope = len({_scope_key(candidate) for candidate in selected}) < len(BASE_VOLUME_FRACTIONS)
        replenishment_pool: list[_Candidate] = []
        replenishment_hard_gate = None
        if not recursive_only and (len(selected) < 20 or missing_scope):
            replenishment_pool, replenishment_counts = _program_pool(
                generation_site,
                building_type,
                height,
                floors,
                generation_context=generation_context,
                parent_variant_indices=(1,),
                typed_graph_mutations=typed_graph_mutations,
                geometry_program_mutations=geometry_program_mutations,
                synthesis_requests=synthesis_requests,
                outcome_graph=outcome_graph,
                recursive_only=geometry_program_authority,
                program_dimensional_context=dimensional_context,
            )
            replenishment_hard_gate = None
            replenishment_selection_pool = replenishment_pool
            if generation_context is not None:
                replenishment_hard_gate = evaluate_accepted_sources_downstream(
                    replenishment_pool,
                    site_local_utm=site,
                    site_origin_utm=site_origin_utm,
                    pnu=pnu,
                    building_type=building_type,
                    height_m=height,
                    floors=floors,
                    constraints=constraints,
                    regulation_evidence=regulation_evidence or {},
                    sunlight_envelope=sunlight_envelope,
                    parking_options=parking_options,
                    generation_context=generation_context,
                )
                replenishment_selection_pool = [
                    candidate
                    for candidate, row in zip(replenishment_pool, replenishment_hard_gate["rows"])
                    if row["combined_hard_pass"]
                ]
            if live_vlm_selection_required:
                replenishment_selection_pool = [
                    candidate for candidate in replenishment_selection_pool
                    if _vlm_reviewed_program_candidate(candidate)
                ]
            replenishment_degenerate_count = sum(
                bool(_solid_morphology_metrics(candidate)["degenerate_sheet_like"])
                for candidate in replenishment_selection_pool
            )
            replenishment_selection_pool = [
                candidate for candidate in replenishment_selection_pool
                if not _solid_morphology_metrics(candidate)["degenerate_sheet_like"]
            ]
            counts["bounded_parent_replenishment"] = {
                **replenishment_counts,
                "preselection_hard_gate": _hard_gate_count_summary(
                    replenishment_hard_gate,
                    replenishment_pool,
                ),
                "degenerate_sheet_like_rejected_count": replenishment_degenerate_count,
            }
            selection_pool = _bounded_visual_selection_pool([
                *selection_pool,
                *replenishment_selection_pool,
            ])
            selected = _select(selection_pool, 20, visual_directive=program_visual_directive)
            outcome_graph.observe_candidates(
                program_slug=slug,
                candidates=replenishment_pool,
                downstream_report=replenishment_hard_gate,
                selected=selected,
            )
            # The final selection can displace a first-pass incumbent. Update
            # observation flags instead of leaving stale selected=true memory.
            outcome_graph.observe_candidates(
                program_slug=slug,
                candidates=pool,
                downstream_report=preselection_hard_gate,
                selected=selected,
            )
        counts["final_hard_pass_selection_pool_count"] = len(selection_pool)
        counts["selection_capacity_diagnostics"] = _selection_capacity_diagnostics(
            selection_pool,
            selected,
            target=20,
            visual_directive=program_visual_directive,
        )
        selected_by_program[slug] = selected
        language_metrics = _portfolio_language_metrics(selected)
        metrics_by_program[slug] = language_metrics
        downstream_hard_gate = (
            evaluate_accepted_sources_downstream(
                selected,
                site_local_utm=site,
                site_origin_utm=site_origin_utm,
                pnu=pnu,
                building_type=building_type,
                height_m=height,
                floors=floors,
                constraints=constraints,
                regulation_evidence=regulation_evidence or {},
                sunlight_envelope=sunlight_envelope,
                parking_options=parking_options,
                generation_context=generation_context,
            )
            if constraints is not None
            else {
                "schema_version": "arr.maas.book_downstream_hard_gate.v1",
                "status": "not_run",
                "same_accepted_source": True,
                "candidate_count": len(selected),
            }
        )
        features: list[dict[str, Any]] = []
        rows: list[dict[str, Any]] = []
        for index, candidate in enumerate(selected):
            feature = deepcopy(candidate.feature)
            props = feature["properties"]
            props["archive_variant_id"] = props["variant_id"]
            props["variant_id"] = f"maas_{index + 1:02d}"
            props["mass_shape"] = candidate.operation
            props["review_status"] = "accept"
            props["review_reasons"] = ["program hard pass", "clean mass pass"]
            features.append(feature)
            signature = candidate.source.signature()
            descriptor = _candidate_language_descriptor(candidate)
            rows.append({
                "variant_id": props["variant_id"],
                "source_sequence": candidate.sequence.name,
                "book_operation": candidate.operation,
                "book_principle_id": candidate.principle_id,
                "book_principle_kind": candidate.principle_kind,
                "book_scope": candidate.source.metadata.get("program_book_projection_evidence", {}).get("scope", {}),
                "score": candidate.score,
                "volume_count": len(candidate.source.volumes),
                "surface_count": int(signature.get("effective_surface_count") or signature.get("surface_count") or 0),
                "inside_site": _inside_site(candidate.source, generation_site),
                "generation_host_mode": str((
                    candidate.source.metadata.get("legal_generation_context_evidence") or {}
                ).get("generation_host_mode") or "unconstrained_site"),
                "legal_generation_context_evidence": deepcopy(
                    candidate.source.metadata.get("legal_generation_context_evidence") or {}
                ),
                "program_hard_pass": bool(props["program_massing_evidence"]["hard_pass"]),
                "vlm_geometry_critic_active": bool(
                    _geometry_program_metadata(candidate).get("vlm_geometry_critic_active")
                ),
                "vlm_program_fit_hard_pass": bool(
                    _geometry_program_metadata(candidate).get("vlm_program_fit_hard_pass")
                ),
                "vlm_critic_score": _geometry_program_metadata(candidate).get("vlm_critic_score"),
                "vlm_program_appropriateness": _geometry_program_metadata(candidate).get("vlm_program_appropriateness"),
                "vlm_section_program_fit": _geometry_program_metadata(candidate).get("vlm_section_program_fit"),
                "seed_family": descriptor["seed_family"],
                "roof_section_family": descriptor["section_family"],
                "roof_archetype": descriptor["roof_archetype"],
                "chassis_family": descriptor["chassis_family"],
                "solid_phenotype": descriptor["solid_phenotype"],
                "body_phenotype": descriptor["body_phenotype"],
                "section_phenotype": descriptor["section_phenotype"],
                "wedge_like": descriptor["wedge_like"],
                "pyramidal_like": descriptor["pyramidal_like"],
                "collapsed_profiled_tent_like": descriptor["collapsed_profiled_tent_like"],
                "degenerate_sheet_like": descriptor["degenerate_sheet_like"],
                "horizontal_surface_ratio": descriptor["horizontal_surface_ratio"],
                "vertical_surface_ratio": descriptor["vertical_surface_ratio"],
                "sloped_surface_ratio": descriptor["sloped_surface_ratio"],
                "normal_direction_bin_count": descriptor["normal_direction_bin_count"],
                "horizontal_level_count": descriptor["horizontal_level_count"],
                "plan_convexity": descriptor["plan_convexity"],
                "upper_area_ratio": descriptor["upper_area_ratio"],
                "solid_genus": descriptor["solid_genus"],
                "solid_component_count": descriptor["solid_component_count"],
                "oriented_plan_aspect_ratio": descriptor["oriented_plan_aspect_ratio"],
                "plan_compactness": descriptor["plan_compactness"],
                "plan_family": descriptor["plan_family"],
                "dominant_component_ratio": descriptor["dominant_component_ratio"],
                "site_coverage_ratio": descriptor["site_coverage_ratio"],
                "hierarchy_score": descriptor["hierarchy_score"],
                "section_control_signature": descriptor["section_control_signature"],
                "semantic_role_tokens": descriptor["semantic_role_tokens"],
                "body_rule_count": descriptor["body_rule_count"],
                "program_body_rule_count": descriptor["program_body_rule_count"],
                "book_body_rule_count": descriptor["book_body_rule_count"],
                "body_rule_family_counts": descriptor["body_rule_family_counts"],
                "body_rules": descriptor["body_rules"],
                "measured_clear_span_m": descriptor["measured_clear_span_m"],
                "measured_solid_height_m": descriptor["measured_solid_height_m"],
                "height_to_clear_span_ratio": descriptor["height_to_clear_span_ratio"],
            })
        board = output_dir / f"maas-book-{slug}-20.png"
        render_archive_sheet(
            features,
            board,
            title=f"MAAS BOOK × {building_type} · PNU {pnu} · {len(features)}/20 silhouette-distinct masses",
        )
        board_paths.append(board)
        near_duplicates = sum(
            1
            for index, left in enumerate(selected)
            for right in selected[:index]
            if _silhouette_distance(left, right) < 0.10
        )
        failures = []
        if len(selected) != 20:
            failures.append("selected_count_below_20")
        operation_count = len({candidate.principle_id for candidate in selected})
        if operation_count < 10:
            failures.append("book_operation_count_below_10")
        visual_languages: list[_Candidate] = []
        for candidate in selected:
            if all(_silhouette_distance(candidate, representative) >= 0.16 for representative in visual_languages):
                visual_languages.append(candidate)
        if len(visual_languages) < 10:
            failures.append("visual_language_count_below_10")
        scope_count = len({_scope_key(candidate) for candidate in selected})
        if scope_count < len(BASE_VOLUME_FRACTIONS):
            failures.append("book_base_volume_scope_count_below_6")
        if any(not row["inside_site"] or not row["program_hard_pass"] for row in rows):
            failures.append("hard_gate_failure_in_selected_portfolio")
        if language_metrics["dominant_seed_family_share"] > 0.40:
            failures.append("repeated_seed_footprint_family_above_40_percent")
        if language_metrics["dominant_roof_section_family_share"] > 0.50:
            failures.append("repeated_roof_section_family_above_50_percent")
        if (
            language_metrics["roof_archetype_count"] > 1
            and language_metrics["dominant_roof_archetype_share"] > 0.30
        ):
            failures.append("repeated_roof_archetype_above_30_percent")
        missing_required_roofs = sorted(
            set(program_visual_directive.get("required_roof_archetypes") or ())
            - set(language_metrics["roof_archetype_counts"])
        )
        if missing_required_roofs:
            failures.append("vlm_required_roof_archetype_missing")
        required_phenotypes = set(program_visual_directive.get("required_solid_phenotypes") or ())
        missing_required_phenotypes = sorted(
            required_phenotypes - set(language_metrics["solid_phenotype_counts"])
        )
        if missing_required_phenotypes:
            failures.append("required_solid_phenotype_missing")
        wedge_cap = int(program_visual_directive.get("max_wedge_like_count", max(3, len(selected) // 5)))
        if language_metrics["wedge_like_count"] > wedge_cap:
            failures.append("wedge_like_count_above_measured_cap")
        pyramidal_cap = int(program_visual_directive.get("max_pyramidal_like_count", 2))
        if language_metrics["pyramidal_like_count"] > pyramidal_cap:
            failures.append("pyramidal_like_count_above_measured_cap")
        phenotype_cap = int(program_visual_directive.get("max_solid_phenotype_count", max(4, len(selected) // 4)))
        if max(language_metrics["solid_phenotype_counts"].values(), default=0) > phenotype_cap:
            failures.append("solid_phenotype_count_above_measured_cap")
        program_results.append({
            "program": building_type,
            "slug": slug,
            "status": "pass" if not failures else "fail",
            "selected_count": len(selected),
            "book_operation_count": operation_count,
            "book_principle_kind_counts": {
                kind: sum(candidate.principle_kind == kind for candidate in selected)
                for kind in ("base_operative", "combination", "aggregation")
            },
            "visual_language_count": len(visual_languages),
            "book_base_volume_scope_count": scope_count,
            "book_base_volume_scopes": sorted({_scope_key(candidate) for candidate in selected}),
            "near_duplicate_pair_count": near_duplicates,
            "program_language_metrics": language_metrics,
            "program_dimensional_context": dimensional_context,
            "vlm_portfolio_directive": {
                "active": bool(program_visual_directive),
                "provider": visual_directive_payload.get("provider") if program_visual_directive else None,
                "typed_graph_mutation_count": len(typed_graph_mutations),
                "geometry_synthesis_request_count": int(counts.get("geometry_synthesis_request_count") or 0),
                "geometry_synthesis_request_source": counts.get("geometry_synthesis_request_source"),
                "geometry_program_vlm_status_counts": counts.get("geometry_program_vlm_status_counts") or {},
                "geometry_program_vlm_causal_trace": counts.get("geometry_program_vlm_causal_trace") or {},
                "required_roof_archetypes": list(program_visual_directive.get("required_roof_archetypes") or ()),
                "required_solid_phenotypes": list(program_visual_directive.get("required_solid_phenotypes") or ()),
                "max_wedge_like_count": wedge_cap,
                "max_pyramidal_like_count": pyramidal_cap,
            },
            "downstream_hard_gate": downstream_hard_gate,
            "counts": counts,
            "failures": failures,
            "missing_vlm_required_roof_archetypes": missing_required_roofs,
            "missing_required_solid_phenotypes": missing_required_phenotypes,
            "duration_seconds": round(perf_counter() - started, 3),
            "rows": rows,
            "png": str(board),
        })
    summary_board = output_dir / "maas-book-programs-60-summary.png"
    images = [Image.open(path).convert("RGB") for path in board_paths]
    combined = Image.new("RGB", (max(image.width for image in images), sum(image.height for image in images)), "#07111f")
    y = 0
    for image in images:
        combined.paste(image, (0, y))
        y += image.height
    combined.save(summary_board)
    book_program_numeric_status = "pass" if all(item["status"] == "pass" for item in program_results) else "fail"
    downstream_status = (
        "pass"
        if program_results and all(item["downstream_hard_gate"]["status"] == "pass" for item in program_results)
        else ("not_run" if all(item["downstream_hard_gate"]["status"] == "not_run" for item in program_results) else "fail")
    )
    result = {
        "schema_version": "arr.maas.book_program_portfolios.v1",
        "status": "pass" if book_program_numeric_status == "pass" and downstream_status in {"pass", "not_run"} else "fail",
        "book_program_numeric_status": book_program_numeric_status,
        "downstream_hard_gate_status": downstream_status,
        "pnu": pnu,
        "site_area_m2": round(float(site.area), 3),
        "program_count": len(program_results),
        "programs": program_results,
        "cross_program_language_comparison": _cross_program_language_comparison(
            selected_by_program,
            metrics_by_program,
        ),
        "legal_parking_checked": downstream_status != "not_run",
        "visual_duplicate_metric": "pose-invariant top/front/side silhouette distance",
        "summary_png": str(summary_board),
    }
    review_fingerprint_payload = [
        {
            "slug": item["slug"],
            "status": item["status"],
            "selected": [
                (
                    row.get("source_sequence"), row.get("book_principle_id"),
                    (row.get("book_scope") or {}).get("base_volume_label"),
                    row.get("solid_phenotype"), row.get("roof_archetype"),
                )
                for row in item.get("rows") or ()
            ],
        }
        for item in program_results
    ]
    result["visual_review_fingerprint"] = hashlib.sha256(
        json.dumps(review_fingerprint_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    outcome_graph_payload = outcome_graph.save()
    result["geometry_mutation_outcome_graph"] = {
        "status": "materialized",
        "path": str(outcome_graph_path),
        "node_count": outcome_graph_payload["node_count"],
        "edge_count": outcome_graph_payload["edge_count"],
        "observation_count": outcome_graph_payload["observation_count"],
        "neo4j_mirror": outcome_graph.mirror_to_neo4j(),
    }
    visual_review_path = output_dir / "maas-book-programs-visual-review.json"
    if visual_review_path.exists():
        try:
            visual_review = json.loads(visual_review_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            visual_review = {}
        if (
            isinstance(visual_review, dict)
            and str(visual_review.get("pnu") or "") == pnu
            and str(visual_review.get("source_summary_fingerprint") or "") == result["visual_review_fingerprint"]
        ):
            result["numeric_status"] = book_program_numeric_status
            result["visual_design_review"] = visual_review
            result["visual_design_review_path"] = str(visual_review_path)
            if visual_review.get("status") == "fail":
                result["status"] = "fail"
        elif isinstance(visual_review, dict) and str(visual_review.get("pnu") or "") == pnu:
            result["visual_design_review"] = {
                "status": "not_run_for_current_fingerprint",
                "stale_review_ignored": True,
            }
    (output_dir / "maas-book-programs-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


__all__ = ["PROGRAMS", "run_book_program_portfolios"]
