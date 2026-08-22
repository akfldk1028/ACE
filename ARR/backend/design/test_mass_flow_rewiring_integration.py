import hashlib
import json
from dataclasses import replace
from math import cos, pi, sin
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import Polygon

from design.maas.book_language import (
    candidate_generation,
    portfolio_benchmark,
    portfolio_replenishment,
)
from design.maas.book_language.candidate_analysis import (
    _Candidate,
    _fingerprint,
    _plan_family,
    _solid_morphology_metrics,
)
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.projected_visual_contract import (
    final_floorwise_visual_geometry_hash,
)
from design.maas.geometry_language.source_bridge import source_surface_payload_hash
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume


def _surface(
    role: str,
    vertices: tuple[tuple[float, float, float], ...],
) -> SourceSurface:
    return SourceSurface(
        role=role,
        volume_role="primary_mass",
        verb="geometry_program",
        surface_type="profiled_recursive_solid_mesh",
        vertices_m=vertices,
        operator="authored_projection",
        semantic_patch_id=role,
    )


def _box_surfaces(
    role: str,
    footprint: Polygon,
    lower_z: float,
    upper_z: float,
) -> tuple[SourceSurface, ...]:
    minx, miny, maxx, maxy = footprint.bounds
    a, b, c, d = (
        (minx, miny),
        (maxx, miny),
        (maxx, maxy),
        (minx, maxy),
    )
    triangles = (
        ((a[0], a[1], lower_z), (c[0], c[1], lower_z), (b[0], b[1], lower_z)),
        ((a[0], a[1], lower_z), (d[0], d[1], lower_z), (c[0], c[1], lower_z)),
        ((a[0], a[1], upper_z), (b[0], b[1], upper_z), (c[0], c[1], upper_z)),
        ((a[0], a[1], upper_z), (c[0], c[1], upper_z), (d[0], d[1], upper_z)),
        ((a[0], a[1], lower_z), (b[0], b[1], lower_z), (b[0], b[1], upper_z)),
        ((a[0], a[1], lower_z), (b[0], b[1], upper_z), (a[0], a[1], upper_z)),
        ((b[0], b[1], lower_z), (c[0], c[1], lower_z), (c[0], c[1], upper_z)),
        ((b[0], b[1], lower_z), (c[0], c[1], upper_z), (b[0], b[1], upper_z)),
        ((c[0], c[1], lower_z), (d[0], d[1], lower_z), (d[0], d[1], upper_z)),
        ((c[0], c[1], lower_z), (d[0], d[1], upper_z), (c[0], c[1], upper_z)),
        ((d[0], d[1], lower_z), (a[0], a[1], lower_z), (a[0], a[1], upper_z)),
        ((d[0], d[1], lower_z), (a[0], a[1], upper_z), (d[0], d[1], upper_z)),
    )
    return tuple(
        _surface(f"{role}_{index}", triangle)
        for index, triangle in enumerate(triangles)
    )


def _tiered_payload(offset: float = 0.0) -> tuple[
    Polygon, Polygon, tuple[SourceVolume, ...], tuple[SourceSurface, ...]
]:
    tiers = (
        Polygon([(offset, 0), (offset + 9, 0), (offset + 9, 7), (offset, 7)]),
        Polygon([(offset + 1, 1), (offset + 8, 1), (offset + 8, 6), (offset + 1, 6)]),
        Polygon([(offset + 2, 2), (offset + 7, 2), (offset + 7, 5), (offset + 2, 5)]),
        Polygon([(offset + 3, 2.5), (offset + 6, 2.5), (offset + 6, 4.5), (offset + 3, 4.5)]),
    )
    volumes = tuple(
        SourceVolume(
            role=f"tier_{index}",
            footprint=footprint,
            bottom_fraction=index / 4,
            top_fraction=(index + 1) / 4,
            verb="terrace",
        )
        for index, footprint in enumerate(tiers)
    )
    surfaces = tuple(
        surface
        for index, footprint in enumerate(tiers)
        for surface in _box_surfaces(
            f"tier_{index}",
            footprint,
            index * 3.0,
            (index + 1) * 3.0,
        )
    )
    return tiers[0], tiers[-1], volumes, surfaces


def _faceted_payload(offset: float = 14.0) -> tuple[
    Polygon, None, tuple[SourceVolume, ...], tuple[SourceSurface, ...]
]:
    points = tuple(
        (
            offset + 5.0 + 5.0 * cos(2 * pi * index / 20),
            5.0 + 3.5 * sin(2 * pi * index / 20),
        )
        for index in range(20)
    )
    footprint = Polygon(points)
    volume = SourceVolume(
        role="faceted_body",
        footprint=footprint,
        bottom_fraction=0.0,
        top_fraction=1.0,
        verb="bend",
    )
    surfaces = tuple(
        _surface(
            f"facet_{index}",
            (
                (left[0], left[1], 0.0),
                (right[0], right[1], 0.0),
                (left[0], left[1], 12.0),
            ),
        )
        for index, (left, right) in enumerate(
            zip(points, (*points[1:], points[0]))
        )
    )
    return footprint, None, (volume,), surfaces


def _courtyard_payload() -> tuple[
    Polygon, None, tuple[SourceVolume, ...], tuple[SourceSurface, ...]
]:
    footprint = Polygon(
        [(40, 0), (52, 0), (52, 10), (40, 10)],
        holes=[[(43, 3), (49, 3), (49, 7), (43, 7)]],
    )
    volume = SourceVolume(
        role="courtyard_ring",
        footprint=footprint,
        bottom_fraction=0.0,
        top_fraction=1.0,
        verb="carve_void",
    )
    surfaces = (
        _surface("ring_roof", ((40, 0, 12), (52, 0, 12), (40, 10, 12))),
        _surface("outer_wall", ((40, 0, 0), (52, 0, 0), (40, 0, 12))),
        _surface("court_wall", ((43, 3, 0), (49, 3, 0), (43, 3, 12))),
    )
    return footprint, None, (volume,), surfaces


def _certified_candidate(
    name: str,
    *,
    payload: tuple[
        Polygon,
        Polygon | None,
        tuple[SourceVolume, ...],
        tuple[SourceSurface, ...],
    ],
    operator: str,
    section_operator: str,
    family: str,
    parent_key: str,
    development_parent: bool = False,
    score: float = 0.8,
) -> _Candidate:
    footprint, upper_footprint, volumes, surfaces = payload
    base_node = GeometryNode(
            id="mass",
            kind="primitive",
            operator="box",
            parameters={
                "width": footprint.bounds[2] - footprint.bounds[0],
                "depth": footprint.bounds[3] - footprint.bounds[1],
                "height": 12.0,
            },
            semantic_role="primary_mass",
        )
    form_node = GeometryNode(
        id="form",
        kind="modifier" if operator == "bend" else "macro",
        operator=operator,
        inputs=("mass",),
        parameters={},
        semantic_role="primary_mass",
    )
    program = GeometryProgram(
        nodes=(base_node,) if operator == "box" else (base_node, form_node),
        root_id="mass" if operator == "box" else "form",
        name=name,
    )
    source = SourceMass(
        name=name,
        footprint=footprint,
        upper_footprint=upper_footprint,
        volumes=volumes,
        surfaces=surfaces,
        metadata={},
    )
    program_hash = program.program_hash()
    geometry_hash = final_floorwise_visual_geometry_hash(source)
    surface_hash = source_surface_payload_hash(source.surfaces)
    hard_pass = not development_parent
    source = replace(source, metadata={
        "final_geometry_hash": geometry_hash,
        "final_program_hash": program_hash,
        "final_surface_payload_hash": surface_hash,
        "geometry_program": program.to_dict(),
        "family": family,
        "geometry_program_compilation": {
            "metrics": {
                "component_count": 1,
                "genus": 1 if operator == "carve_void" else 0,
            },
        },
        "program_section_graph_evidence": {
            "graph_operators": [section_operator],
        },
        "geometry_program_bridge_evidence": {
            "status": "materialized",
            "program_hash": program_hash,
            "geometry_hash": geometry_hash,
            "surface_payload_hash": surface_hash,
        },
        "authored_projection_identity": {
            "schema_version": "arr.maas.authored_projection_identity.v1",
            "hard_pass": True,
        },
        "authored_legal_projection_certificate": {
            "schema_version": "arr.maas.authored_legal_projection_certificate.v1",
            "status": "verified",
            "hard_pass": True,
            "input_authored_program_hash": program_hash,
            "projected_surface_hash": geometry_hash,
            "projected_surface_payload_hash": surface_hash,
        },
        "book_generation_lineage": {
            "schema_version": "arr.maas.book_generation_lineage.v1",
            "stage": "base" if development_parent else "descendant",
            "parent_key": parent_key,
        },
        "program_gate_result": {"hard_pass": hard_pass},
        "program_review_authority": {
            "hard_pass": hard_pass,
            "legal_archive_authority": True,
            "selection_eligible": hard_pass,
            "development_review_eligible": development_parent,
        },
        "legal_capacity_authority": {"legal_hard_pass": True},
        "shared_floor_contract": {"hard_pass": True},
    })
    return _Candidate(
        principle_id=(
            "book:base:development"
            if development_parent
            else f"book:operative:{family}"
        ),
        principle_kind="base_operative",
        operation="" if development_parent else family,
        sequence=SimpleNamespace(name=name),
        source=source,
        feature={
            "type": "Feature",
            "properties": {
                "book_scope": {"base_volume_label": "1/1"},
                "capacity_alternative_projection": {
                    "alternative_id": family,
                },
            },
        },
        score=score,
    )


class _DeterministicCompatibility:
    @staticmethod
    def distance(left: _Candidate, right: _Candidate) -> float:
        names = {left.sequence.name, right.sequence.name}
        return 0.01 if names == {"stepped", "stepped-near"} else 0.9

    def compatibility_matrix(self, candidates):
        return [
            [
                left is right or self.distance(left, right) >= 0.10
                for right in candidates
            ]
            for left in candidates
        ]

    @staticmethod
    def evidence() -> dict[str, object]:
        return {"mode": "deterministic_geometry_distance"}


class MassFlowRewiringIntegrationTests(SimpleTestCase):
    def test_real_two_phase_live_reserve_selector_feedback_flow(self):
        parent_key = "parent:certified-development-base"
        development_parent = _certified_candidate(
            "development-parent",
            payload=_faceted_payload(offset=-12.0),
            operator="box",
            section_operator="flat_roof",
            family="development_base",
            parent_key=parent_key,
            development_parent=True,
        )
        stepped = _certified_candidate(
            "stepped",
            payload=_tiered_payload(offset=0.2),
            operator="terrace",
            section_operator="stepped_section",
            family="stepped_family",
            parent_key=parent_key,
            score=0.95,
        )
        oblique_curved = _certified_candidate(
            "oblique-curved",
            payload=_faceted_payload(),
            operator="bend",
            section_operator="folded_roof",
            family="oblique_curved_family",
            parent_key=parent_key,
            score=0.9,
        )
        voided = _certified_candidate(
            "voided-body",
            payload=_courtyard_payload(),
            operator="carve_void",
            section_operator="flat_roof",
            family="voided_body_family",
            parent_key=parent_key,
            score=0.85,
        )
        descendants = [stepped, oblique_curved, voided]
        stepped_near = _certified_candidate(
            "stepped-near",
            payload=_tiered_payload(),
            operator="terrace",
            section_operator="stepped_section",
            family="stepped_near_family",
            parent_key=parent_key,
            score=0.1,
        )
        detached_archive = {
            "schema_version": "arr.maas.legal_mass_archive.v1",
            "program_hash": stepped.source.metadata["final_program_hash"],
            "geometry_hash": stepped.source.metadata["final_geometry_hash"],
        }

        active_cycle = 0
        events = []
        downstream_by_cycle = []
        final_review_by_cycle = []
        descendant_synthesis_by_cycle = []
        stage_counts = []

        def base_review(pool, **_kwargs):
            self.assertEqual(pool, [development_parent])
            events.append((active_cycle, "base_review"))
            metadata = development_parent.source.metadata
            geometry_hash = metadata["final_geometry_hash"]
            review_fingerprint = hashlib.sha256(json.dumps(
                {"geometry_hash": geometry_hash},
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")).hexdigest()
            metadata["base_book_vlm_audit"] = {
                "response_id": f"base-review-cycle-{active_cycle}",
                "review_stage": "book_base_operative",
                "reviewed_exact_post_book_geometry": True,
                "descendant_development_hard_pass": True,
                "geometry_hash": geometry_hash,
                "program_hash": metadata["final_program_hash"],
                "base_review_fingerprint": review_fingerprint,
                "authored_legal_projection_certificate": dict(
                    metadata["authored_legal_projection_certificate"]
                ),
            }
            return list(pool), {
                "schema_version": "arr.maas.book_base_stage_vlm_gate.v2",
                "required": True,
                "status": "complete",
                "reviewed_parent_keys": [parent_key],
                "reviewed_parent_fingerprints": [review_fingerprint],
            }

        def single_phase(*_args, **kwargs):
            phase = kwargs["_generation_phase"]
            if phase == "base":
                events.append((active_cycle, "base_generated"))
                return [development_parent], {
                    "_runtime_directed_seeds": ("certified-base-seed",),
                    "evaluated": 1,
                    "compiled": 1,
                    "clean": 1,
                    "program_passed": 0,
                    "legal_mass_archive": {
                        "records": [{
                            "geometry_hash": development_parent.source.metadata[
                                "final_geometry_hash"
                            ],
                        }],
                    },
                    "phase_durations_seconds": {},
                    "geometry_program_llm_author_stage_counts": {
                        "base_development_reviewed": 1,
                    },
                }
            self.assertEqual(phase, "descendant")
            descendant_synthesis_by_cycle.append((
                active_cycle,
                list(kwargs["synthesis_requests"]),
            ))
            self.assertEqual(
                kwargs["_reviewed_base_registry"],
                {
                    parent_key: development_parent.source.metadata[
                        "final_geometry_hash"
                    ],
                },
            )
            audit = kwargs["_reviewed_base_audits"][parent_key]
            self.assertTrue(audit["descendant_development_hard_pass"])
            self.assertEqual(
                kwargs["_directed_seeds_override"],
                ("certified-base-seed",),
            )
            released = descendants if active_cycle == 1 else []
            events.append((active_cycle, "descendants_generated"))
            return list(released), {
                "evaluated": len(released),
                "compiled": len(released),
                "clean": len(released),
                "program_passed": len(released),
                "legal_mass_archive": {
                    "records": [
                        {
                            "geometry_hash": candidate.source.metadata[
                                "final_geometry_hash"
                            ],
                        }
                        for candidate in released
                    ],
                },
                "phase_durations_seconds": {},
                "geometry_program_llm_author_stage_counts": {
                    "base_development_reviewed": 1,
                    "directed_geometry_materialized": len(released),
                    "program_hard_passed": len(released),
                },
            }

        def downstream(pool, **_kwargs):
            downstream_by_cycle.append(list(pool))
            events.append((active_cycle, "downstream"))
            return {
                "rows": [
                    {
                        "combined_hard_pass": True,
                        "semantic_projection_hard_gate": {"hard_pass": True},
                    }
                    for _candidate in pool
                ],
            }

        def final_review(pool, **_kwargs):
            final_review_by_cycle.append(list(pool))
            events.append((active_cycle, "final_review"))
            return SimpleNamespace(
                selection_pool=list(pool),
                initial_vlm_passes=list(pool),
                initial_vlm_gate={"audit_records": []},
                repair_pool=[],
                repair_vlm_passes=[],
                repair_evidence={
                    "final_book_vlm_gate": {
                        "input_count": 0,
                        "audit_records": [],
                    },
                },
                final_vlm_gate={"hard_pass_count": len(pool)},
            )

        def run_cycle(index, reserve, reviewed, synthesis_requests):
            nonlocal active_cycle
            active_cycle = index
            result = portfolio_replenishment.run_replenishment_cycle(
                cycle_index=index,
                parent_variant_index=index,
                retained_selection_pool=[],
                retained_live_qd_reserve=reserve,
                reviewed_final_vlm_fingerprints=reviewed,
                excluded_parent_keys=set(),
                excluded_parent_fingerprints=set(),
                excluded_program_hashes=set(),
                generation_site=SimpleNamespace(),
                building_type="neighborhood_living",
                height=14.0,
                floors=4,
                generation_context=SimpleNamespace(),
                typed_graph_mutations=[],
                geometry_program_mutations=[],
                synthesis_requests=synthesis_requests,
                outcome_graph=None,
                recursive_only=True,
                target_count=5,
                exact_compile_limit=12,
                program_dimensional_context={},
                site_boundary_source="deterministic_test",
                site_access_context={},
                site_access_geometry={},
                runtime_live_vlm=True,
                live_vlm_selection_required=False,
                base_capacity_contract={},
                trusted_legal_floor_field={},
                trusted_legal_floor_field_hash="",
                trusted_clear_span_floor_plan={},
                capacity_site=SimpleNamespace(),
                output_dir=Path("test-output"),
                program_slug="neighborhood",
                visual_directive={},
                downstream_context={},
                hard_gate_summary=lambda _report, candidates: {
                    "candidate_count": len(candidates),
                },
            )
            stage_counts.append(dict(
                result.evidence["geometry_program_llm_author_stage_counts"]
            ))
            return result

        original_family_deficits = (
            portfolio_benchmark.family_supply_deficits_for_candidates
        )

        def family_deficits_with_missing_descriptor(candidates, **kwargs):
            return {
                **original_family_deficits(candidates, **kwargs),
                "missing_descriptor_cells": ["body:winged"],
            }

        initial_request = {
            "candidate_count": 3,
            "llm_author_count": 3,
            "intent_tags": ["initial_supply"],
        }
        with (
            patch.object(candidate_generation, "_program_pool_single_phase", side_effect=single_phase),
            patch.object(portfolio_replenishment, "audit_book_base_stage_with_vlm", side_effect=base_review),
            patch.object(portfolio_replenishment, "evaluate_accepted_sources_downstream", side_effect=downstream),
            patch.object(portfolio_replenishment, "_bind_final_visual_authority_for_review"),
            patch.object(portfolio_replenishment, "run_final_vlm_cycle", side_effect=final_review),
            patch.object(
                portfolio_benchmark,
                "family_supply_deficits_for_candidates",
                side_effect=family_deficits_with_missing_descriptor,
            ),
        ):
            cycle_1 = run_cycle(1, [], set(), [initial_request])
            selected, selection_trace, selector_state = (
                portfolio_benchmark._select_with_replenishment_state(
                    phase="cycle_1_selection",
                    selection_pool=[*descendants, stepped_near],
                    target_count=3,
                    visual_directive={},
                    compatibility_analysis=_DeterministicCompatibility(),
                    allow_diagnostic_fallback=False,
                    exact_repair_evidence=cycle_1.evidence.get(
                        "exact_post_book_typed_repair"
                    ),
                    stage_outcomes=cycle_1.evidence.get("stage_outcomes") or [],
                    final_vlm_gate=cycle_1.evidence.get("final_book_vlm_gate"),
                )
            )
            next_inputs, next_feedback = (
                portfolio_benchmark._next_synthesis_inputs_from_selector_state(
                    selector_state,
                    synthesis_requests=[initial_request],
                    authored_visual_authority_replenishment_feedback=[],
                    legal_fit_repair_feedback=[],
                    capacity_authoring_deficits=[],
                    progressive_target=None,
                    base_book_vlm_replenishment_feedback=[],
                    selected_count=len(selected),
                    selected_scope_count=len(selected),
                    target_count=4,
                    required_scope_count=4,
                    exact_compile_remaining=3,
                    cycle_index=2,
                    cycle_budget=2,
                    author_replenishment_remaining=1,
                )
            )
            cycle_2 = run_cycle(
                2,
                [*cycle_1.live_qd_reserve, detached_archive],
                cycle_1.reviewed_final_vlm_fingerprints,
                next_inputs["synthesis_requests"],
            )

        expected_fingerprints = {_fingerprint(candidate) for candidate in descendants}
        measured = {
            candidate.sequence.name: _solid_morphology_metrics(candidate)
            for candidate in descendants
        }
        self.assertEqual(measured["stepped"]["body_phenotype"], "stepped")
        self.assertEqual(measured["stepped"]["section_phenotype"], "stepped")
        self.assertEqual(
            measured["oblique-curved"]["body_phenotype"],
            "curved",
        )
        self.assertEqual(
            measured["oblique-curved"]["section_phenotype"],
            "oblique",
        )
        self.assertEqual(measured["voided-body"]["body_phenotype"], "voided")
        self.assertEqual(_plan_family(voided), "courtyard")
        self.assertEqual(
            {_fingerprint(candidate) for candidate in cycle_1.live_qd_reserve},
            expected_fingerprints,
        )
        self.assertEqual(
            {_fingerprint(candidate) for candidate in cycle_2.live_qd_reserve},
            expected_fingerprints,
        )
        self.assertNotIn(detached_archive, cycle_2.live_qd_reserve)
        self.assertNotIn(development_parent, cycle_1.live_qd_reserve)
        self.assertEqual(downstream_by_cycle, [descendants, descendants])
        self.assertEqual(final_review_by_cycle, [descendants, []])
        self.assertEqual(
            cycle_2.reviewed_final_vlm_fingerprints,
            expected_fingerprints,
        )
        self.assertTrue(selection_trace)
        feedback_reasons = {item.get("reason") for item in next_feedback}
        self.assertIn("silhouette_near_duplicate", feedback_reasons)
        self.assertIn("missing_descriptor_cells", feedback_reasons)
        self.assertEqual(
            [cycle for cycle, _requests in descendant_synthesis_by_cycle],
            [1, 2],
        )
        self.assertNotEqual(
            descendant_synthesis_by_cycle[0][1],
            descendant_synthesis_by_cycle[1][1],
        )
        request_feedback = descendant_synthesis_by_cycle[1][1][0][
            "authored_visual_authority_replenishment_feedback"
        ]
        self.assertTrue(
            {"silhouette_near_duplicate", "missing_descriptor_cells"}
            <= {item.get("reason") for item in request_feedback}
        )
        self.assertEqual(events, [
            (1, "base_generated"),
            (1, "base_review"),
            (1, "descendants_generated"),
            (1, "downstream"),
            (1, "final_review"),
            (2, "base_generated"),
            (2, "base_review"),
            (2, "descendants_generated"),
            (2, "downstream"),
            (2, "final_review"),
        ])
        self.assertEqual(stage_counts, [
            {
                "base_development_reviewed": 1,
                "directed_geometry_materialized": 3,
                "program_hard_passed": 3,
            },
            {
                "base_development_reviewed": 1,
                "directed_geometry_materialized": 0,
                "program_hard_passed": 0,
            },
        ])
