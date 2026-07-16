"""Program-neutral synthesis of recursive architectural solid graphs.

This module deliberately does not contain parcel coordinates or completed
building templates.  It turns a normalized base seed, architectural intent
tags and bounded variation indices into a typed :class:`GeometryProgram`.
The compiler remains the only authority that can turn the graph into a solid.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

from .ast import GeometryNode, GeometryProgram
from .base_seeds import BASE_SEED_SPECS, base_seed_program
from .section_profiles import SECTION_PROFILES, section_profile_controls


_PROFILE_FAMILY_INTENTS: dict[str, tuple[str, ...]] = {
    "courtyard": ("carved_void",),
    "void_notch": ("carved_void",),
    "bend": ("continuous_curve",),
    "slender_bar": ("long_span", "continuous_curve"),
    "sloped_roof": ("profiled_span_section", "long_span", "daylight_section", "oblique_section"),
    "terrace_link": ("stepped_section", "lifted_ground"),
    "offset": ("stepped_section",),
    "stepback_tower": ("stepped_section", "vertical_landmark"),
    "nested_stack": ("stepped_section", "carved_void"),
    "split": ("distributed_wings", "lifted_ground"),
    "diagonal_connect": ("distributed_wings", "oblique_section"),
    "array_cluster": ("distributed_wings",),
    "taper": ("vertical_landmark",),
}


_TAG_OPERATOR_PALETTE: dict[str, tuple[str, ...]] = {
    "calm_prismatic": ("identity",),
    "continuous_curve": ("bend", "bent_bar", "inflate"),
    "long_span": ("split_wing", "identity", "bend", "inflate"),
    "oblique_section": ("slice", "shear", "cut_corner"),
    "stepped_section": ("setback", "stepped_mass", "terrace"),
    "carved_void": ("courtyard", "notch", "carve_void", "puncture"),
    "lifted_ground": ("lift", "cantilever", "split_wing"),
    "daylight_section": ("puncture", "inflate", "setback"),
    "distributed_wings": ("cross_mass", "radial_array", "split_wing"),
    "vertical_landmark": ("taper", "shear", "twist"),
    # Repetition weights the general section-profile operator so bounded
    # synthesis explores several roof/section graphs before generic cuts and
    # setbacks. The profiles remain parameters, not named building templates.
    "profiled_span_section": ("profiled_hall", "profiled_hall", "profiled_hall", "profiled_hall", "profiled_hall", "profiled_hall"),
}

_BODY_PHENOTYPE_INTENTS: dict[str, str] = {
    "prismatic": "calm_prismatic",
    "curved": "continuous_curve",
    "stepped": "stepped_section",
    "voided": "carved_void",
    "oblique": "oblique_section",
    "winged": "distributed_wings",
    "lifted": "lifted_ground",
}

_OPERATOR_KIND: dict[str, str] = {
    "bend": "modifier",
    "taper": "modifier",
    "twist": "modifier",
    "inflate": "modifier",
    "pinch": "modifier",
    "slice": "modifier",
    "cut_corner": "modifier",
    "shear": "transform",
    "radial_array": "pattern",
    "courtyard": "macro",
    "notch": "macro",
    "carve_void": "macro",
    "setback": "macro",
    "terrace": "macro",
    "cantilever": "macro",
    "lift": "macro",
    "puncture": "macro",
    "cross_mass": "macro",
    "bent_bar": "macro",
    "split_wing": "macro",
    "stepped_mass": "macro",
    "profiled_hall": "macro",
}


def synthesize_architectural_programs(
    request: dict[str, Any],
    *,
    building_type: str,
) -> tuple[GeometryProgram, ...]:
    """Create bounded graph alternatives from intent, not named forms.

    ``request`` may choose base seeds and intent tags, but it cannot provide
    world coordinates.  Parameter samples are deterministic so every program
    can be reproduced, hashed, compared and revised by a later VLM critic.
    """
    if not isinstance(request, dict):
        return ()
    known_seeds = {item.seed_id for item in BASE_SEED_SPECS}
    raw_seeds = request.get("base_seeds") or ("slab", "bar", "block")
    base_seeds = tuple(dict.fromkeys(
        str(value) for value in raw_seeds if str(value) in known_seeds
    ))
    if not base_seeds:
        return ()
    intent_tags = tuple(dict.fromkeys(
        str(value) for value in (request.get("intent_tags") or ())
        if str(value) in _TAG_OPERATOR_PALETTE
    ))
    try:
        # A strict program/VLM critic is expected to reject a meaningful
        # fraction of authored programs.  Capping the author pool at 24 made
        # a 20-alternative portfolio mathematically depend on near-perfect
        # critic acceptance.  Keep the search bounded, but allow enough
        # genotype supply for hard rejection instead of weakening gates.
        target_count = max(1, min(64, int(request.get("candidate_count") or 12)))
        maximum_depth = max(1, min(3, int(request.get("maximum_operator_depth") or 2)))
        variation_offset = max(0, min(4096, int(request.get("variation_offset") or 0)))
    except (TypeError, ValueError):
        return ()
    required_terminal_operator = str(request.get("required_terminal_operator") or "").strip().lower()
    if required_terminal_operator and required_terminal_operator != "profiled_hall":
        return ()
    inferred_intents = tuple(
        _BODY_PHENOTYPE_INTENTS[str(value)]
        for value in (request.get("required_body_phenotypes") or ())
        if str(value) in _BODY_PHENOTYPE_INTENTS
    )
    if required_terminal_operator == "profiled_hall":
        inferred_intents = (*inferred_intents, "long_span")
    intent_tags = tuple(dict.fromkeys((*intent_tags, *inferred_intents)))
    if not intent_tags:
        return ()

    raw_palette = tuple(
        operator
        for tag in intent_tags
        for operator in _TAG_OPERATOR_PALETTE[tag]
    )
    palette = _weighted_operator_palette(raw_palette)
    records: list[GeometryProgram] = []
    seen_hashes: set[str] = set()
    cursor = variation_offset
    attempts = 0
    # A low-discrepancy traversal of seed/operator pairs avoids making the
    # first tag or first base seed dominate a bounded batch.
    attempt_budget = max(target_count * 8, len(base_seeds) * len(palette) * 2)
    while len(records) < target_count and attempts < attempt_budget:
        # Cycle the first operator directly.  A fixed multiplier can share a
        # divisor with the runtime palette length and accidentally collapse a
        # 14-operator language to only bend/setback.
        first = palette[cursor % len(palette)]
        seed_id = _base_seed_for_operator(
            first,
            base_seeds,
            cursor=cursor,
            palette_size=len(palette),
            intent_tags=intent_tags,
        )
        operators = [first]
        operator_variant_indices = [_operator_occurrence_index(palette, cursor, first)]
        if maximum_depth >= 2 and len(palette) > 1 and cursor % 3 != 0:
            second = palette[(cursor * 5 + 3) % len(palette)]
            if second != first and second != "profiled_hall" and _compatible_stack(first, second):
                operators.append(second)
                operator_variant_indices.append(_operator_occurrence_index(palette, cursor, second))
        if maximum_depth >= 3 and len(palette) > 2 and cursor % 7 == 0:
            third = palette[(cursor * 13 + 5) % len(palette)]
            if third != "profiled_hall" and third not in operators and all(_compatible_stack(item, third) for item in operators):
                operators.append(third)
                operator_variant_indices.append(_operator_occurrence_index(palette, cursor, third))
        if required_terminal_operator and required_terminal_operator not in operators:
            operators.append(required_terminal_operator)
            operator_variant_indices.append(cursor)
        program = _program_from_stack(
            seed_id,
            operators,
            operator_variant_indices=operator_variant_indices,
            variation_index=cursor,
            variation_offset=variation_offset,
            intent_tags=intent_tags,
            building_type=building_type,
            required_terminal_operator=required_terminal_operator,
        )
        cursor += 1
        attempts += 1
        errors = [issue for issue in program.validate() if issue.severity == "error"]
        if errors:
            continue
        program_hash = program.program_hash()
        if program_hash in seen_hashes:
            continue
        seen_hashes.add(program_hash)
        records.append(program)
    return tuple(records)


def synthesis_requests_from_program_profile(
    building_type: str,
    *,
    source_seeds: Iterable[str],
    candidates_per_lineage: int = 12,
) -> tuple[dict[str, Any], ...]:
    """Infer graph-search intent from program semantics, not named forms.

    The profile contributes program requirements and preferred language words.
    This adapter maps those words to operator *capabilities*. It never reads a
    profile's hand-authored section controls, parcel coordinates, or completed
    geometry. Two source role lineages are enough to keep entry/service/gallery
    semantics while the recursive agent authors the dominant solid.
    """
    from design.maas.program_massing.profiles import resolve_program_profile

    profile = resolve_program_profile(building_type)
    preferred = tuple(str(value) for value in profile.get("preferred_families") or ())
    intents = tuple(dict.fromkeys(
        intent
        for family in preferred
        for intent in _PROFILE_FAMILY_INTENTS.get(family, ())
    ))
    if not intents:
        intents = ("carved_void", "stepped_section", "oblique_section")
    # Every search needs one topology-preserving control.  Without it the
    # preferred-language list can contain only setbacks/cuts and an otherwise
    # diverse program collapses into one wedge or terrace phenotype.  This is
    # a grammar capability, not a prescribed box-shaped final answer.
    intents = tuple(dict.fromkeys(("calm_prismatic", *intents)))
    text = " ".join((
        str(profile.get("id") or ""),
        str(profile.get("design_intent") or ""),
        *preferred,
    )).lower()
    base_seeds: list[str] = ["block", "slab"]
    if any(token in text for token in ("bar", "span", "street", "wing")):
        base_seeds.insert(0, "bar")
    if any(token in text for token in ("court", "gallery", "museum", "public", "civic")):
        base_seeds.append("profiled_prism")
    if any(token in text for token in ("tower", "vertical")):
        base_seeds.append("tower")
    bases = list(dict.fromkeys(base_seeds))
    lineage_names = tuple(dict.fromkeys(str(value) for value in source_seeds if str(value)))[:2]
    return tuple({
        "source_seed": source_seed,
        "base_seeds": bases,
        "intent_tags": list(intents),
        "candidate_count": max(4, min(24, int(candidates_per_lineage))),
        "maximum_operator_depth": 2,
        "legal_fit_strengths": [0.2, 0.6],
        "rationale": (
            "agent-inferred recursive geometry search from program design intent "
            "and preferred language capabilities; named section templates ignored"
        ),
        "inference_evidence": {
            "profile_id": str(profile.get("id") or "generic"),
            "preferred_families": list(preferred),
            "section_control_templates_used": False,
            "parcel_coordinates_used": False,
        },
    } for source_seed in lineage_names)


def _program_from_stack(
    seed_id: str,
    operators: Iterable[str],
    *,
    operator_variant_indices: Iterable[int] | None = None,
    variation_index: int,
    variation_offset: int = 0,
    intent_tags: tuple[str, ...],
    building_type: str,
    required_terminal_operator: str = "",
) -> GeometryProgram:
    seed = base_seed_program(seed_id)
    nodes = list(seed.nodes)
    root_id = seed.root_id
    operator_records = list(zip(
        operators,
        operator_variant_indices or (),
    ))
    if not operator_records:
        operator_records = [(operator, variation_index) for operator in operators]
    # Section is a terminal invariant over all body mutations.  Sorting only
    # this one relation leaves the other authored operator order unchanged.
    operator_records.sort(key=lambda item: item[0] == "profiled_hall")
    operator_path: list[str] = []
    for stack_index, (operator, operator_variant_index) in enumerate(operator_records, start=1):
        if operator == "identity":
            continue
        kind = _OPERATOR_KIND[operator]
        node_id = f"agent_{stack_index:02d}_{operator}"
        parameters = _bounded_parameters(
            operator,
            operator_variant_index if operator == "profiled_hall" else variation_index + stack_index * 17,
            intent_tags=intent_tags,
        )
        nodes.append(GeometryNode(
            id=node_id,
            kind=kind,
            operator=operator,
            inputs=(root_id,),
            parameters=parameters,
            semantic_role=("program_section_invariant" if operator == "profiled_hall" else "dominant_mass"),
            provenance={
                "source": "procedural_geometry_synthesis_agent",
                "intent_tags": list(intent_tags),
                "variation_index": variation_index,
                "bounded_parameter_generation": True,
                "parcel_coordinates_used": False,
                "completed_building_template": False,
                "program_invariant": operator == "profiled_hall",
            },
        ))
        root_id = node_id
        operator_path.append(operator)
    family = "agent_" + ("_".join(operator_path) if operator_path else "prismatic")
    digest = hashlib.sha256(json.dumps({
        "seed": seed_id,
        "operators": operator_path,
        "variation": variation_index,
        "intent": intent_tags,
    }, sort_keys=True).encode("utf-8")).hexdigest()[:10]
    safe_program = re.sub(r"[^A-Za-z0-9]+", "_", building_type).strip("_").lower() or "program"
    return GeometryProgram(
        nodes=tuple(nodes),
        root_id=root_id,
        name=f"synth_{safe_program}_{seed_id}_{digest}",
        metadata={
            "family": family,
            "language_layer": "agent_synthesized_recursive_geometry",
            "base_seed": seed_id,
            "intent_tags": list(intent_tags),
            "operator_path": operator_path or ["prismatic"],
            "variation_index": variation_index,
            "variation_offset": variation_offset,
            "author_provider": "bounded_procedural_geometry_agent",
            "parcel_coordinates_in_program": False,
            "completed_building_template": False,
            "required_terminal_operator": required_terminal_operator,
        },
    )


def _compatible_stack(left: str, right: str) -> bool:
    # Keep one readable dominant rule.  Multiple repetition or void macros in
    # one short stack tend to create fragments or nested Boolean instability.
    if "identity" in {left, right}:
        return True
    repetition = {"radial_array", "cross_mass", "split_wing"}
    voids = {"courtyard", "notch", "carve_void"}
    steps = {"setback", "stepped_mass", "terrace"}
    if left in repetition and right in repetition:
        return False
    if left in voids and right in voids:
        return False
    if left in steps and right in steps:
        return False
    return not ({left, right} & repetition and {left, right} & voids)


def _weighted_operator_palette(raw_palette: tuple[str, ...]) -> tuple[str, ...]:
    """Interleave weighted capabilities without starving other intent tags."""
    if not raw_palette:
        return ()
    unique = list(dict.fromkeys(raw_palette))
    counts = {operator: raw_palette.count(operator) for operator in unique}
    # Four or more repetitions are an explicit capability weight. Lower
    # counts usually come from the same operator appearing naturally in two
    # related intent tags and must not crowd out the rest of the grammar.
    weighted = [operator for operator in unique if counts[operator] >= 4]
    if not weighted:
        return tuple(unique)
    others = [operator for operator in unique if operator not in weighted]
    scheduled: list[str] = []
    if others:
        scheduled.append(others.pop(0))
    remaining = {operator: counts[operator] for operator in weighted}
    while any(remaining.values()) or others:
        for operator in weighted:
            if remaining[operator] > 0:
                scheduled.append(operator)
                remaining[operator] -= 1
        if others:
            scheduled.append(others.pop(0))
    return tuple(scheduled)


def _operator_occurrence_index(palette: tuple[str, ...], cursor: int, operator: str) -> int:
    """Return the zero-based visit count for one weighted operator."""
    if not palette:
        return 0
    cycles, remainder = divmod(max(0, int(cursor)), len(palette))
    return cycles * palette.count(operator) + sum(
        item == operator for item in palette[:remainder]
    )


def _base_seed_for_operator(
    operator: str,
    base_seeds: tuple[str, ...],
    *,
    cursor: int,
    palette_size: int,
    intent_tags: tuple[str, ...],
) -> str:
    """Choose a primitive/operator pairing from architectural capabilities.

    A base seed is not a frozen form.  Still, a compact profiled prism cannot
    serve as the only host for a long-span cut: it repeatedly failed coverage
    before the cut was even judged.  Pair longitudinal modifiers with BAR/SLAB
    when the program asks for long span, while later palette cycles may still
    explore every requested seed.  This is shape grammar compatibility, never
    parcel coordinates or a completed mass recipe.
    """
    choices = base_seeds
    if operator == "slice" and "long_span" in intent_tags:
        long_span = tuple(seed for seed in ("bar", "slab") if seed in base_seeds)
        if long_span:
            choices = long_span
    cycle = cursor // max(1, palette_size)
    return choices[(cursor + cycle) % len(choices)]


def _bounded_parameters(
    operator: str,
    index: int,
    *,
    intent_tags: tuple[str, ...] = (),
) -> dict[str, Any]:
    u = _halton(index + 1, 2)
    v = _halton(index + 1, 3)
    if operator == "bend":
        return {"axis": "x", "angle_degrees": round(20.0 + 34.0 * u, 3), "subdivisions": 4}
    if operator == "bent_bar":
        return {"axis": "x", "angle_degrees": round(18.0 + 38.0 * u, 3), "subdivisions": 4}
    if operator == "taper":
        return {"axis": "z", "start_scale": [1.0, 1.0], "end_scale": [round(0.52 + 0.30 * u, 3), round(0.60 + 0.28 * v, 3)], "subdivisions": 3}
    if operator == "twist":
        return {"axis": "z", "angle_degrees": round(-28.0 + 56.0 * u, 3), "subdivisions": 4}
    if operator == "inflate":
        return {"axis": "z", "middle_scale": round(1.10 + 0.28 * u, 3), "subdivisions": 4}
    if operator == "pinch":
        return {"axis": "x", "waist_scale": round(0.44 + 0.32 * u, 3), "subdivisions": 4}
    if operator == "slice":
        return {
            "normal": [round(0.55 + 0.35 * u, 3), round(-0.2 + 0.4 * v, 3), -1.0],
            "offset_ratio": round(0.08 + 0.12 * u, 3),
            "keep_side": "positive",
        }
    if operator == "cut_corner":
        return {"corner": ("ne", "nw", "se", "sw")[index % 4], "ratio": round(0.16 + 0.18 * u, 3)}
    if operator == "shear":
        return {"axis": "x", "direction": "z", "amount": round(-0.18 + 0.36 * u, 3)}
    if operator == "radial_array":
        return {"count": 3 + index % 3, "total_angle_degrees": round(42.0 + 48.0 * u, 3), "pivot": "center"}
    if operator in {"courtyard", "carve_void"}:
        return {"margin_ratio": round(0.18 + 0.16 * u, 3)}
    if operator == "notch":
        return {"corner": ("ne", "nw", "se", "sw")[index % 4], "ratio": round(0.16 + 0.16 * u, 3), "height_ratio": round(0.48 + 0.28 * v, 3)}
    if operator in {"setback", "stepped_mass", "terrace"}:
        return {"levels": 3 + index % 2, "setback_ratio": round(0.08 + 0.10 * u, 3), "shift_per_level": [round(0.02 + 0.08 * v, 3), 0.0, 0.0]}
    if operator == "profiled_hall":
        families = tuple(SECTION_PROFILES)
        family = families[index % len(families)]
        cycle = (index // len(families)) % 4
        gain, eave_shift = (
            (1.0, 0.0),
            (0.86, 0.025),
            (1.12, -0.02),
            (0.96, 0.045),
        )[cycle]
        controls = section_profile_controls(family)
        eave = min(value[1] for value in controls)
        controls = [
            [
                value[0],
                round(max(0.18, min(1.20, eave + eave_shift + (value[1] - eave) * gain)), 4),
            ]
            for value in controls
        ]
        return {
            "span_axis": "x",
            "section_family": family,
            "section_controls": controls,
            "section_variant_index": cycle,
        }
    if operator == "cantilever":
        return {"start_ratio": round(0.48 + 0.22 * u, 3), "vector": [round(0.08 + 0.18 * v, 3), 0.0, 0.0]}
    if operator == "lift":
        return {"rise_ratio": round(0.12 + 0.20 * u, 3), "support_ratio": round(0.06 + 0.06 * v, 3)}
    if operator == "puncture":
        return {"axis": "x" if index % 2 == 0 else "y", "count": 2 + index % 2, "ratio": round(0.10 + 0.10 * u, 3)}
    if operator == "cross_mass":
        return {"angle_degrees": round(68.0 + 34.0 * u, 3)}
    if operator == "split_wing":
        long_span = "long_span" in intent_tags
        return {
            "axis": "x",
            "gap_ratio": round((0.06 + 0.08 * u) if long_span else (0.10 + 0.15 * u), 3),
            "bridge": True,
            "height_ratio": round(0.48 + 0.24 * v, 3),
            "height": round(0.12 + 0.18 * u, 3),
            "ground_spine": long_span,
            "ground_spine_width_ratio": round(0.30 + 0.18 * v, 3),
            "ground_spine_height_ratio": round(0.16 + 0.12 * u, 3),
        }
    return {}


def _halton(index: int, base: int) -> float:
    result = 0.0
    factor = 1.0
    value = max(1, int(index))
    while value:
        factor /= base
        value, remainder = divmod(value, base)
        result += remainder * factor
    return result


__all__ = ["synthesize_architectural_programs", "synthesis_requests_from_program_profile"]
