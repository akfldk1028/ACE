"""Program-independent base-seed and chassis population.

The form bank is deliberately authored before a building use is known.  It
contains only normalized host proportions and topological relations.  BOOK
scope/operations are projected later, and program roles plus VLM judgement are
downstream consumers rather than geometry authors for this stage.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from typing import Any

from .ast import GeometryProgram
from .base_seeds import BASE_SEED_SPECS
from .chassis_taxonomy import classify_geometry_program
from .programs import architectural_shape_programs
from .synthesis import synthesize_architectural_programs
from .typology_priors import TYPOLOGY_PRIORS


UNIVERSAL_FORM_BANK_SCHEMA = "arr.maas.universal_form_bank.v2"

_UNIVERSAL_INTENTS = (
    "calm_prismatic",
    "continuous_curve",
    "long_span",
    "oblique_section",
    "stepped_section",
    "carved_void",
    "lifted_ground",
    "daylight_section",
    "distributed_wings",
    "vertical_landmark",
    "profiled_span_section",
    "face_composition",
)

_UNIVERSAL_MACROS = (
    "courtyard",
    "carve_void",
    "notch",
    "setback",
    "terrace",
    "cantilever",
    "lift",
    "puncture",
    "cross_mass",
    "grid_mass",
    "bent_bar",
    "split_wing",
    "stepped_mass",
    "profiled_hall",
    "attach",
)


def universal_form_bank_contract() -> dict[str, Any]:
    """Return the immutable stage contract exposed to audits and the UI."""
    return {
        "schema_version": UNIVERSAL_FORM_BANK_SCHEMA,
        "stage_order": (
            "base_seed",
            "chassis",
            "base_volume",
            "book_principle",
            "book_variation",
            "program_projection",
            "capacity_alternative_projection",
            "hard_gates",
            "live_vlm",
        ),
        "program_conditioned": False,
        "parcel_coordinates_used": False,
        "base_seed_ids": tuple(spec.seed_id for spec in BASE_SEED_SPECS),
        "chassis_ids": tuple(prior.typology_id for prior in TYPOLOGY_PRIORS),
        "intent_tags": _UNIVERSAL_INTENTS,
        "operator_sampling": "balanced_unique_round_robin",
        "synthesis_lane_program_count": 64,
        "replenishment_page_size": 64,
        "maximum_cached_variation_pages": 8,
        "replenishment_rule": "advance_low_discrepancy_geometry_program_page",
        "executable_core_lane_program_count": len(architectural_shape_programs()),
        "executable_core_lane": (
            "bent_linear", "radial_fan", "l_mass", "u_mass", "courtyard",
            "attached_volume", "overlap", "setback", "cross", "taper",
            "lean", "notch", "slice", "cut_corner", "loft", "sweep",
            "split_bridge", "twist",
        ),
        "synthesis_capabilities": (
            "triangular_profiled_prism",
            "trapezoidal_profiled_prism",
            "chamfered_profiled_prism",
            "host_face_attachment",
        ),
    }


@lru_cache(maxsize=8)
def universal_form_programs(variation_page: int = 0) -> tuple[GeometryProgram, ...]:
    """Build one deterministic page of the program-independent form bank.

    Page zero is the public baseline and also carries the 18 executable core
    language examples.  Later pages continue the same low-discrepancy
    parameter lattice without replaying those fixed examples.  This gives a
    bounded replenishment cycle genuinely new Geometry Programs instead of
    renaming the same payload through a legacy program-role parent variant.
    """
    page = max(0, min(7, int(variation_page)))
    request = {
        "base_seeds": [spec.seed_id for spec in BASE_SEED_SPECS],
        "intent_tags": list(_UNIVERSAL_INTENTS),
        "typology_priors": [prior.typology_id for prior in TYPOLOGY_PRIORS],
        "candidate_count": 64,
        # One readable chassis relation precedes the later BOOK operation.
        "maximum_operator_depth": 1,
        "downstream_body_rule_reserve": 0,
        "allowed_macro_operators": list(_UNIVERSAL_MACROS),
        "balanced_operator_sampling": True,
        "variation_offset": page * 64,
    }
    synthesis_programs = synthesize_architectural_programs(
        request,
        building_type="unconditioned_form_bank",
    )
    lanes = (
        *((program, "bounded_synthesis") for program in synthesis_programs),
        *(
            tuple(
                (program, "executable_core_language")
                for program in architectural_shape_programs()
            )
            if page == 0
            else ()
        ),
    )
    records: list[GeometryProgram] = []
    seen_hashes: set[str] = set()
    for program, lane in lanes:
        source_operators = tuple(node.operator for node in program.nodes)
        taxonomy = classify_geometry_program(
            family=str(program.metadata.get("family") or ""),
            source_operators=source_operators,
            declared_base_seed=program.metadata.get("base_seed"),
        )
        normalized = replace(program, metadata={
            **program.metadata,
            "language_layer": "universal_form_bank",
            "form_bank_schema_version": UNIVERSAL_FORM_BANK_SCHEMA,
            "form_bank_lane": lane,
            "form_bank_variation_page": page,
            "program_conditioned": False,
            "program_projection_applied": False,
            "parcel_coordinates_in_program": False,
            "base_seed": taxonomy["base_seed"],
            "chassis": taxonomy["chassis"],
            "chassis_taxonomy_authority": taxonomy["authority"],
        })
        program_hash = normalized.program_hash()
        if program_hash in seen_hashes:
            continue
        seen_hashes.add(program_hash)
        records.append(normalized)
    return tuple(records)


def universal_form_program_pages(
    variation_pages: tuple[int, ...] | list[int],
) -> tuple[GeometryProgram, ...]:
    """Resolve a bounded ordered set of form-bank pages once for a caller."""

    pages = tuple(sorted({
        max(0, min(7, int(page))) for page in variation_pages
    })) or (0,)
    return tuple(
        program
        for page in pages
        for program in universal_form_programs(page)
    )


__all__ = [
    "UNIVERSAL_FORM_BANK_SCHEMA",
    "universal_form_bank_contract",
    "universal_form_program_pages",
    "universal_form_programs",
]
