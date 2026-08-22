from dataclasses import replace

import pytest
from shapely.geometry import box

from design.maas.geometry_language import GeometryNode, GeometryProgram
from design.maas.geometry_language.source_bridge import source_surface_payload_hash
from design.maas.program_massing.semantic_carriers import (
    bind_source_role_scaffold_to_program,
    build_program_semantic_carrier_evidence,
)
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume


PROGRAM_ID = "neighborhood_living"
GRAPH = {
    "schema_version": "arr.maas.component_graph.v2",
    "name": "program_neighborhood_stepback_corner__r69_repair",
    "notes": ["program_profile=neighborhood_living"],
}


def _program() -> GeometryProgram:
    return GeometryProgram(
        nodes=(GeometryNode(
            id="repaired_book_root",
            kind="primitive",
            operator="box",
            parameters={"width": 10.0, "depth": 10.0, "height": 14.0},
            semantic_role="repaired_book_mass",
        ),),
        root_id="repaired_book_root",
        name="r69_repaired_book_descendant",
    )


def _authored_source(*, primary_width: float) -> SourceMass:
    footprint = box(0.0, 0.0, 10.0, 10.0)
    return SourceMass(
        name="r69_neighborhood_repaired",
        footprint=footprint,
        volumes=(
            SourceVolume(
                role=(
                    "neighborhood_primary_ground_corner"
                    "__program_section_band__book_carve_0"
                ),
                footprint=box(0.0, 0.0, primary_width, 8.0),
                bottom_fraction=0.0,
                top_fraction=1.0,
                verb="book_carve",
            ),
            SourceVolume(
                role="neighborhood_public_corner_room__book_carve_0",
                footprint=box(7.5, 0.0, 10.0, 4.0),
                bottom_fraction=0.0,
                top_fraction=1.0,
                verb="book_carve",
            ),
        ),
        metadata={"component_graph": GRAPH},
    )


def _bound_program(source: SourceMass) -> GeometryProgram:
    failures = []
    bound = bind_source_role_scaffold_to_program(
        _program(), source, program_id=PROGRAM_ID, failure_sink=failures
    )
    assert failures == []
    assert bound is not None
    return bound


def _final_source(program: GeometryProgram) -> SourceMass:
    footprint = box(0.0, 0.0, 10.0, 10.0)
    surfaces = (SourceSurface(
        role="final_surface",
        volume_role="final_mass",
        verb="legal_projection",
        surface_type="triangle",
        vertices_m=((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 10.0, 14.0)),
    ),)
    return SourceMass(
        name="r69_final_repaired",
        footprint=footprint,
        volumes=(SourceVolume(
            role="final_mass",
            footprint=footprint,
            bottom_fraction=0.0,
            top_fraction=1.0,
            verb="legal_projection",
        ),),
        surfaces=surfaces,
        metadata={
            "geometry_program": program.to_dict(),
            "geometry_program_bridge_evidence": {
                "program_hash": "repaired-program-hash",
                "geometry_hash": "repaired-geometry-hash",
                "surface_payload_hash": source_surface_payload_hash(surfaces),
                "surface_export_complete": True,
                "raw_mesh_triangle_count": 1,
                "exported_surface_count": 1,
            },
        },
    )


def _issue_evidence(authored_source: SourceMass, program: GeometryProgram):
    return build_program_semantic_carrier_evidence(
        authored_source,
        _final_source(program),
        program_id=PROGRAM_ID,
        final_program_hash="repaired-program-hash",
        final_geometry_hash="repaired-geometry-hash",
        floor_capacity_plan_hash="floor-plan-hash",
        pnu="r69-pnu",
        site_context_hash="site-context-hash",
        capacity_alternative_id="capacity-alternative",
        achieved_capacity_band="competition-band",
        capacity_measurement_hash="capacity-measurement-hash",
    )


def test_r69_primary_section_band_preserves_proven_active_ground_relation():
    bound = _bound_program(_authored_source(primary_width=8.0))

    bindings = [
        node.parameters["source_role_relation_binding"]
        for node in bound.nodes
        if node.semantic_role == "source_role_relation_binding"
    ]
    by_relation = {binding["source_relation"]: binding for binding in bindings}

    assert set(by_relation) == {
        "primary_program_mass",
        "active_ground_program",
        "public_spatial_gesture",
    }
    assert by_relation["primary_program_mass"]["semantic_role"] == (
        "neighborhood_primary_ground_corner"
    )
    assert by_relation["active_ground_program"]["semantic_role"] == (
        "neighborhood_primary_ground_corner"
    )
    assert (
        by_relation["primary_program_mass"]["source_component_id"]
        != by_relation["active_ground_program"]["source_component_id"]
    )


def test_r69_authority_uses_bound_reachable_origin_after_materialization_drift():
    bound = _bound_program(_authored_source(primary_width=8.0))

    evidence = _issue_evidence(
        _authored_source(primary_width=7.0),
        bound,
    )

    assert evidence["hard_pass"] is True
    assert evidence["failures"] == []
    assert {
        record["source_relation"]
        for record in evidence["source_role_scaffold"]
    } == {
        "primary_program_mass",
        "active_ground_program",
        "public_spatial_gesture",
    }


@pytest.mark.parametrize("tamper", ["unreachable", "unrelated_role"])
def test_r69_authority_rejects_unreachable_or_unrelated_bound_origin(tamper):
    bound = _bound_program(_authored_source(primary_width=8.0))
    if tamper == "unreachable":
        tampered = replace(bound, root_id="repaired_book_root")
    else:
        nodes = list(bound.nodes)
        index = next(
            i for i, node in enumerate(nodes)
            if node.semantic_role == "source_role_relation_binding"
        )
        binding = dict(nodes[index].parameters["source_role_relation_binding"])
        binding["semantic_role"] = "unrelated_cross_program_role"
        parameters = dict(nodes[index].parameters)
        parameters["source_role_relation_binding"] = binding
        nodes[index] = replace(nodes[index], parameters=parameters)
        tampered = replace(bound, nodes=tuple(nodes))

    evidence = _issue_evidence(_authored_source(primary_width=7.0), tampered)

    assert evidence["hard_pass"] is False
    assert "source_role_scaffold_not_bound_to_reachable_final_ast" in evidence[
        "failures"
    ]
