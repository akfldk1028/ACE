"""Shared canonical fixtures for Task 5 regression tests."""

from dataclasses import replace

from shapely.geometry import Polygon, box

from design.maas.grammar.component_graph import graph_from_sequence
from design.maas.program_massing import program_seed_sequences
from design.maas.program_massing.semantic_carriers import (
    rebind_semantic_projection_capacity,
    semantic_site_context_hash,
)
from design.maas.source_geometry.ir import SourceMass, SourceVolume


TASK5_TEST_PNU = "1168011800104170004"


def canonical_gym_semantic_source(name: str) -> SourceMass:
    """Return a real supported-program role/component graph for handoff tests."""

    footprint = box(0.0, 0.0, 10.0, 10.0)
    component_graph = graph_from_sequence(
        program_seed_sequences("gymnasium")[0]
    ).to_dict()
    return SourceMass(
        name=name,
        footprint=footprint,
        volumes=(
            SourceVolume(
                "gym_main_long_span_hall",
                footprint,
                0.0,
                1.0,
                "geometry_program",
            ),
            SourceVolume(
                "gym_service_spine",
                box(1.0, 4.0, 3.0, 6.0),
                0.0,
                0.5,
                "attach",
            ),
            SourceVolume(
                "gym_entry_canopy",
                box(7.0, 4.0, 8.5, 6.0),
                0.0,
                0.5,
                "attach",
            ),
        ),
        metadata={"component_graph": component_graph},
    )


def canonical_gym_materialization_context(
    *,
    capacity_alternative_id: str,
    site: Polygon,
) -> dict[str, str]:
    """Return honest pre-measurement identities for final materialization."""

    return {
        "building_type": "gymnasium",
        "site_access_side": "south",
        "pnu": TASK5_TEST_PNU,
        "capacity_alternative_id": capacity_alternative_id,
        "capacity_measurement_hash": "pending_capacity_measurement",
        "site_context_hash": semantic_site_context_hash(
            pnu=TASK5_TEST_PNU,
            building_type="gymnasium",
            site=site,
        ),
    }


def legal_generation_context_for_site(site):
    """Return the production generation-context contract for a test site."""

    from design.maas.book_language.downstream_hard_gate import (
        LegalGenerationContext,
    )

    return LegalGenerationContext(
        envelope=None,
        generation_site=site,
        sunlight_ring=(),
        evidence={},
    )


def rebind_pending_unknown_capacity(source: SourceMass) -> SourceMass:
    """Represent a measured miss without inventing an achieved band or hash."""

    metadata = dict(source.metadata)
    evidence = dict(metadata["program_semantic_carrier_evidence"])
    metadata["program_semantic_carrier_evidence"] = (
        rebind_semantic_projection_capacity(
            evidence,
            achieved_capacity_band="",
            capacity_measurement_hash="pending_capacity_measurement",
        )
    )
    context = dict(metadata["final_semantic_projection_context"])
    context.update({
        "achieved_capacity_band": "",
        "capacity_measurement_hash": "pending_capacity_measurement",
    })
    metadata["final_semantic_projection_context"] = context
    return replace(source, metadata=metadata)
