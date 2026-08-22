from contextlib import ExitStack
from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import MultiPolygon, Polygon, box

from design.maas.book_language import candidate_generation
from design.maas.book_language.candidate_generation import (
    _eligible_smoke_floor_candidate,
)
from design.maas.book_language.capacity_routing import (
    route_capacity_target_hard_passes,
)
from design.maas.book_language import portfolio_selection
from design.maas.book_language.candidate_analysis import _Candidate
from design.maas.book_language.downstream_hard_gate import _evaluate_candidate
from design.maas.geometry_language import (
    architectural_shape_programs,
    base_seed_programs,
    compile_geometry_program_to_source_mass,
)
from design.maas.geometry_language.floorwise_visual_projection import (
    certify_authored_visual_mesh,
    projected_surface_visual_hash,
)
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume
from design.maas.grammar.verb_sequence import VerbSequence


def _candidate(name: str, *, capacity_pass: bool):
    return SimpleNamespace(
        name=name,
        score=1.0,
        source=SimpleNamespace(
            metadata={
                "capacity_alternative_projection": {
                    "alternative_id": "brief_target",
                    "target_hard_pass": capacity_pass,
                },
                "source_capacity_measurement": {
                    "hard_pass": capacity_pass,
                    "feasible_capacity_utilization": 0.42,
                },
            },
        ),
    )


def _authored_profiled_box_source(name: str) -> SourceMass:
    lower = (
        (-5.0, -5.0, 0.0),
        (5.0, -5.0, 0.0),
        (5.0, 5.0, 0.0),
        (-5.0, 5.0, 0.0),
    )
    upper = tuple((x + 1.5, y, 1.0) for x, y, _z in lower)
    vertices = (*lower, *upper)
    triangles = (
        (0, 2, 1),
        (0, 3, 2),
        (4, 5, 6),
        (4, 6, 7),
        (0, 1, 5),
        (0, 5, 4),
        (1, 2, 6),
        (1, 6, 5),
        (2, 3, 7),
        (2, 7, 6),
        (3, 0, 4),
        (3, 4, 7),
    )
    surfaces = tuple(
        SourceSurface(
            role=f"mesh-{index}",
            volume_role="recursive-primary",
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=tuple(vertices[vertex] for vertex in triangle),
            operator="loft",
            semantic_patch_id="recursive-primary:profiled-box",
        )
        for index, triangle in enumerate(triangles)
    )
    footprint = box(-5.0, -5.0, 5.0, 5.0)
    return SourceMass(
        name=name,
        footprint=footprint,
        volumes=(
            SourceVolume(
                "recursive-primary",
                footprint,
                0.0,
                1.0,
                "geometry_program",
            ),
        ),
        surfaces=surfaces,
        metadata={
            "geometry_program_bridge_evidence": {
                "status": "materialized",
                "raw_mesh_triangle_count": len(triangles),
                "exported_surface_count": len(surfaces),
                "surface_coordinate_frame": (
                    "source_footprint_centroid_local_xy_normalized_z"
                ),
            },
        },
    )


def _r293_legal_sections() -> tuple[Polygon, ...]:
    caps = (102.931, 102.931, 74.989, 51.471)
    return tuple(
        box(-area ** 0.5 / 2.0, -area ** 0.5 / 2.0, area ** 0.5 / 2.0, area ** 0.5 / 2.0)
        for area in caps
    )


def _final_projected_block_program(
    legal_sections: tuple[Polygon, ...],
    target_floor_areas_m2: tuple[float, ...],
):
    from design.maas.geometry_language import (
        append_floorwise_legal_projection,
        compile_geometry_program,
    )
    from design.maas.geometry_language.source_bridge import (
        append_site_placement_matrix,
        derive_host_fit_transform,
    )

    program = next(
        item
        for item in base_seed_programs()
        if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
        == "block"
    )
    compilation = compile_geometry_program(program)
    fit = derive_host_fit_transform(
        compilation,
        legal_sections[0],
        target_plan_area=max(target_floor_areas_m2),
        minimum_plan_area=max(target_floor_areas_m2),
    )
    assert fit is not None
    return append_floorwise_legal_projection(
        append_site_placement_matrix(program, fit),
        legal_sections=legal_sections,
        target_floor_areas_m2=target_floor_areas_m2,
        floor_capacity_plan_hash="task3-fix-round",
    )


def _authored_affine_export_program(
    legal_sections: tuple[Polygon, ...],
    target_floor_areas_m2: tuple[float, ...],
):
    from design.maas.geometry_language.legal_field_affine_placement import (
        select_legal_field_affine_projection,
    )

    program = next(
        item
        for item in base_seed_programs()
        if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
        == "slab"
    )
    selected = select_legal_field_affine_projection(
        program,
        legal_sections=legal_sections,
        target_floor_areas_m2=target_floor_areas_m2,
        floor_capacity_plan_hash="authored-affine-export-fixture",
        maximum_exact_candidates=4,
    )
    return selected.projection if selected is not None else None


class MaasStageHardContractTests(SimpleTestCase):
    def test_floorwise_legal_fit_uses_legal_plate_not_design_distribution(self):
        from design.maas.geometry_language.source_bridge import (
            _floor_target_fit_is_legal,
        )

        self.assertTrue(
            _floor_target_fit_is_legal(
                achieved_area_m2=38.192736,
                maximum_legal_area_m2=100.0,
            )
        )
        self.assertTrue(
            _floor_target_fit_is_legal(
                achieved_area_m2=92.639,
                maximum_legal_area_m2=100.0,
            )
        )
        self.assertFalse(
            _floor_target_fit_is_legal(
                achieved_area_m2=100.001,
                maximum_legal_area_m2=100.0,
            )
        )
        from design.maas.geometry_language.source_bridge import (
            _floor_visual_section_matches_occupied,
        )
        self.assertTrue(
            _floor_visual_section_matches_occupied(
                measured_area_m2=38.192736,
                occupied_area_m2=38.192736,
            )
        )
        self.assertFalse(
            _floor_visual_section_matches_occupied(
                measured_area_m2=38.0,
                occupied_area_m2=38.192736,
            )
        )

    def test_floorwise_materializer_rejects_certified_projection_without_surfaces(self):
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        source = replace(
            _authored_profiled_box_source("empty-certified-projection"),
            surfaces=(),
        )
        failure_sink = []
        result = materialize_floorwise_legal_source(
            source,
            legal_sections=(box(-10.0, -10.0, 10.0, 10.0),),
            target_plan_coverage=0.5,
            floor_capacity_plan_hash="empty-projection-plan",
            target_floor_areas_m2=(50.0,),
            terminal_failure_sink=failure_sink,
        )

        self.assertIsNone(result)
        self.assertEqual(
            [{
                "stage": "authored_visual_authority",
                "evidence": {
                    "repair_reason": (
                        "authored_visual_projection_empty_surface_payload"
                    ),
                },
            }],
            failure_sink,
        )

    def test_floorwise_legal_section_loft_is_withheld_when_authored_paths_fail(self):
        from design.maas.geometry_language.floorwise_visual_projection import (
            FloorwiseVisualProjection,
            FloorwiseVisualProjectionCertificate,
        )
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        source_plan = box(-5.0, -5.0, 5.0, 5.0)
        stale_outside_surface = SourceSurface(
            role="pre-csg-matrix-surface",
            volume_role="recursive-primary",
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=((0.0, 0.0, 0.0), (30.0, 0.0, 0.5), (0.0, 30.0, 1.0)),
        )
        source = SourceMass(
            name="pre-csg-mesh-exits-host",
            footprint=source_plan,
            volumes=(
                SourceVolume(
                    "recursive-primary",
                    source_plan,
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            surfaces=(stale_outside_surface,),
            metadata={"geometry_program_bridge_evidence": {
                "program_hash": "pre-csg-program",
                "geometry_hash": "pre-csg-geometry",
            }},
        )
        legal = (
            box(-6.0, -5.0, 4.0, 5.0),
            box(-4.0, -4.0, 6.0, 4.0),
            box(-2.0, -3.0, 6.0, 3.0),
        )
        rejected_projection = FloorwiseVisualProjection(
            surfaces=(),
            certificate=FloorwiseVisualProjectionCertificate(
                status="failed",
                hard_pass=False,
                failure_reasons=("projected_visual_mesh_outside_legal_section",),
            ),
        )

        failure_sink = []
        with (
            patch(
                "design.maas.geometry_language.floorwise_visual_projection."
                "project_floorwise_visual_mesh",
                return_value=rejected_projection,
            ),
            patch(
                "design.maas.geometry_language.floorwise_profiled_legal_clip."
                "clip_profiled_mesh_to_floorwise_legal_solids",
                return_value=rejected_projection,
            ),
        ):
            result = materialize_floorwise_legal_source(
                source,
                legal_sections=legal,
                target_plan_coverage=0.5,
                floor_capacity_plan_hash="csg-loft-plan",
                target_floor_areas_m2=(50.0, 40.0, 30.0),
                terminal_failure_sink=failure_sink,
            )

        self.assertIsNone(result)
        self.assertEqual(
            [{
                "stage": "authored_visual_authority",
                "evidence": {
                    "repair_reason": "authored_profiled_legal_clip_failed",
                    "failure_reason": "projected_visual_mesh_outside_legal_section",
                },
            }],
            failure_sink,
        )

    def test_diagnostic_generation_cap_prefers_exact_evaluation_budget(self):
        reached = candidate_generation._diagnostic_generation_cap_reached

        self.assertFalse(reached(
            evaluated=12,
            program_passed=12,
            evaluation_cap=36,
            candidate_cap=12,
        ))
        self.assertTrue(reached(
            evaluated=36,
            program_passed=0,
            evaluation_cap=36,
            candidate_cap=12,
        ))
        self.assertTrue(reached(
            evaluated=0,
            program_passed=12,
            evaluation_cap=0,
            candidate_cap=12,
        ))

    def test_diagnostic_round_zero_visits_36_unique_genotypes_once(self):
        from design.maas.geometry_language.universal_form_bank import (
            universal_form_programs,
        )

        programs = universal_form_programs(0)[:36]
        seeds = tuple(
            VerbSequence(
                name=f"diagnostic-genotype-{index:02d}",
                label=f"diagnostic-genotype-{index:02d}",
                calls=(),
                notes=(
                    f"geometry_program_directive=diagnostic-genotype-{index:02d}",
                    f"geometry_program_source_seed=diagnostic-genotype-{index:02d}",
                    "geometry_program_payload="
                    + json.dumps(program.to_dict(), sort_keys=True),
                ),
            )
            for index, program in enumerate(programs)
        )
        trace = []
        scope_labels = ("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")

        with (
            patch.object(
                candidate_generation,
                "_agent_mutated_seeds",
                return_value=seeds,
            ),
            patch.object(
                candidate_generation,
                "program_seed_variants",
                side_effect=lambda seed, **_kwargs: (seed,),
            ),
            patch.object(
                candidate_generation,
                "build_capacity_alternative",
                return_value={},
            ),
            patch.object(
                candidate_generation,
                "capacity_alternative_for_host",
                return_value={},
            ),
            patch.object(
                candidate_generation,
                "capacity_contract_for_alternative",
                return_value={},
            ),
            patch.object(
                candidate_generation,
                "compile_sequence_to_source_mass",
                return_value=None,
            ),
        ):
            _pool, evidence = candidate_generation._program_pool(
                box(0.0, 0.0, 20.0, 20.0),
                "program",
                12.0,
                4,
                recursive_only=True,
                diagnostic_scope_labels=scope_labels,
                diagnostic_book_probe_count=12,
                diagnostic_evaluation_cap=36,
                diagnostic_candidate_cap=12,
                diagnostic_evaluation_trace_callback=trace.append,
            )

        self.assertEqual(evidence["evaluated"], 36)
        self.assertEqual(len(trace), 36)
        self.assertEqual(
            [record["capacity_schedule_index"] for record in trace],
            list(range(36)),
        )
        self.assertEqual(
            len({record["genotype_hash"] for record in trace}),
            36,
        )
        self.assertEqual(
            [record["form_bank_lane"] for record in trace].count(
                "executable_core_language"
            ),
            16,
        )
        self.assertTrue(all(record["book_stage"] == "base" for record in trace))
        self.assertTrue(all(record["book_stage_order"] == 1 for record in trace))
        self.assertEqual(
            [record["scope_label"] for record in trace],
            [scope_labels[index % len(scope_labels)] for index in range(36)],
        )
        self.assertEqual(
            len({record["parent_key"] for record in trace}),
            36,
        )
        self.assertEqual(
            len({
                (record["genotype_hash"], record["variant_index"])
                for record in trace
            }),
            36,
        )

    def test_capacity_miss_is_advisory_before_paid_visual_review(self):
        miss = _candidate("authored-winged", capacity_pass=False)

        routed, evidence = route_capacity_target_hard_passes(
            [miss],
            stage="initial_final_book_paid_vlm",
        )

        self.assertEqual(routed, [miss])
        self.assertEqual(evidence["hard_pass_count"], 0)
        self.assertEqual(evidence["advisory_miss_count"], 1)
        self.assertEqual(evidence["rejected_before_paid_vlm_count"], 0)
        self.assertEqual(evidence["capacity_target_authority"], "diagnostic_only")

    def test_selector_universe_keeps_measured_capacity_miss(self):
        miss = _candidate("authored-curved", capacity_pass=False)
        exact = _candidate("authored-stepped", capacity_pass=True)

        with patch.object(
            portfolio_selection,
            "_fingerprint",
            side_effect=lambda item: (item.name,),
        ):
            universe, measured = portfolio_selection._target_hard_pass_universe(
                [miss, exact],
            )

        self.assertEqual(universe, [miss, exact])
        self.assertEqual(measured, [miss, exact])

    def test_smoke_early_stop_is_disabled_before_downstream_hard_gates(self):
        source = SimpleNamespace(
            status="compiled",
            volumes=(object(),),
            surfaces=(object(),),
            metadata={
                "book_generation_lineage": {
                    "stage": "base",
                    "parent_key": "authored-base",
                },
            },
        )

        self.assertFalse(_eligible_smoke_floor_candidate(
            source,
            {"hard_pass": True},
            {"hard_pass": True},
            {"target_hard_pass": True},
            set(),
        ))

        with (
            patch.object(candidate_generation, "_agent_mutated_seeds", return_value=()),
            patch.object(candidate_generation, "program_seed_sequences", return_value=()),
        ):
            _pool, evidence = candidate_generation._program_pool(
                box(0.0, 0.0, 20.0, 20.0),
                "program",
                12.0,
                4,
                stop_after_shared_floor_hard_passes=1,
            )

        self.assertFalse(evidence["hard_acceptance_early_stop"]["active"])
        self.assertFalse(evidence["hard_acceptance_early_stop"]["stopped_early"])
        self.assertEqual(
            evidence["hard_acceptance_early_stop"]["requested_target"],
            1,
        )

    def test_all_miss_noncanonical_target_ten_is_explicitly_infeasible(self):
        candidates = [
            SimpleNamespace(
                key=f"mass-{index:02d}",
                scope=f"1/{index + 1}",
                principle_kind="base_operative",
                operation=f"operation-{index:02d}",
                score=1.0 - index / 100.0,
                seed=f"seed-{index:02d}",
                section=f"section-{index:02d}",
                roof=f"roof-{index:02d}",
                chassis=f"chassis-{index:02d}",
                phenotype=f"phenotype-{index:02d}",
                family=f"family-{index:02d}",
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "alternative_id": "brief_target",
                        "target_hard_pass": False,
                    },
                }),
            )
            for index in range(12)
        ]
        trace = {}

        with (
            patch.object(
                portfolio_selection,
                "_fingerprint",
                side_effect=lambda item: (item.key,),
            ),
            patch.object(
                portfolio_selection, "_scope_key", side_effect=lambda item: item.scope
            ),
            patch.object(
                portfolio_selection,
                "_seed_family",
                side_effect=lambda item: item.seed,
            ),
            patch.object(
                portfolio_selection,
                "_section_family",
                side_effect=lambda item: item.section,
            ),
            patch.object(
                portfolio_selection,
                "_roof_archetype",
                side_effect=lambda item: item.roof,
            ),
            patch.object(
                portfolio_selection,
                "_chassis_family",
                side_effect=lambda item: item.chassis,
            ),
            patch.object(
                portfolio_selection,
                "_geometry_program_family",
                side_effect=lambda item: item.family,
            ),
            patch.object(
                portfolio_selection,
                "_solid_morphology_metrics",
                side_effect=lambda item: {
                    "phenotype": item.phenotype,
                    "wedge_like": False,
                    "pyramidal_like": False,
                },
            ),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(
                portfolio_selection,
                "_design_concept_descriptor",
                side_effect=lambda item: {
                    "ground_strategy": f"ground-{item.key}",
                    "concept_key": item.key,
                    "frontage_aligned": False,
                },
            ),
            patch.object(
                portfolio_selection,
                "_rebalance_measured_morphologies",
                side_effect=lambda selected, *_args, **_kwargs: selected,
            ),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=10,
                selection_trace=trace,
            )

        self.assertEqual(selected, [])
        self.assertEqual(trace["capacity_target_gate_measured_count"], 12)
        self.assertEqual(trace["capacity_target_gate_pass_count"], 0)
        self.assertEqual(trace["capacity_target_gate_advisory_miss_count"], 12)
        self.assertEqual(trace["capacity_target_gate_rejected_count"], 0)
        self.assertFalse(trace["joint_ten_card_solver_target_reached"])
        infeasibility = trace["joint_ten_card_infeasibility_certificate"]
        self.assertEqual(infeasibility["status"], "infeasible")
        self.assertTrue(infeasibility["unsatisfied_constraints"])

    def test_real_slab_uses_final_floorwise_program_as_geometry_authority(self):
        from design.maas.program_massing.semantic_carriers import (
            semantic_site_context_hash,
        )
        from design.test_task5_regression_fixtures import (
            canonical_gym_materialization_context,
            canonical_gym_semantic_source,
        )

        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "slab"
        )
        lower = box(-15.0, -10.0, 15.0, 10.0)
        sequence = VerbSequence(
            "real-slab",
            "real-slab",
            (),
            ("geometry_program_directive=real-slab",),
        )
        semantic_context = canonical_gym_materialization_context(
            capacity_alternative_id="balanced_yield",
            site=lower,
        )

        with patch.object(
            candidate_generation,
            "_geometry_program_registry",
            return_value={"real-slab": program},
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                canonical_gym_semantic_source("source-placeholder"),
                sequence,
                containment_host=lower,
                upper_containment_host=lower,
                floor_containment_hosts=(lower, lower, lower, lower),
                floor_capacity_plan_hash="contained-stack-plan",
                target_floor_areas_m2=(180.0, 180.0, 180.0, 180.0),
                **semantic_context,
            )

        self.assertIsNotNone(materialized)
        assert materialized is not None
        persisted_context = materialized.metadata[
            "final_semantic_projection_context"
        ]
        self.assertEqual(
            persisted_context["site_context_hash"],
            semantic_site_context_hash(
                pnu=semantic_context["pnu"],
                building_type=semantic_context["building_type"],
                site=lower,
            ),
        )
        self.assertEqual(
            persisted_context["capacity_measurement_hash"],
            "pending_capacity_measurement",
        )
        self.assertEqual(
            persisted_context["achieved_capacity_band"],
            persisted_context["capacity_alternative_id"],
        )
        bridge = materialized.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(
            materialized.metadata["geometry_authority"],
            "final_floorwise_legal_geometry_program",
        )
        self.assertNotIn(
            "floorwise_legal_sibling_evidence",
            materialized.metadata,
        )
        self.assertEqual(
            materialized.metadata["final_geometry_hash"],
            bridge["geometry_hash"],
        )
        self.assertEqual(
            materialized.metadata["final_program_hash"],
            bridge["program_hash"],
        )
        self.assertEqual(
            materialized.metadata["legal_field_affine_placement"][
                "projection_mode"
            ],
            "authored_affine_preserved",
        )

    def test_real_block_shrinking_stack_rejects_closed_band_legal_escape(self):
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )
        from design.test_task5_regression_fixtures import (
            canonical_gym_materialization_context,
            canonical_gym_semantic_source,
        )

        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "block"
        )
        lower = box(-15.0, -10.0, 15.0, 10.0)
        middle = box(-11.5, -8.0, 11.5, 8.0)
        upper = box(-8.0, -6.0, 8.0, 6.0)
        sequence = VerbSequence(
            "real-block-shrinking-stack-rejection",
            "real-block-shrinking-stack-rejection",
            (),
            (
                "geometry_program_directive="
                "real-block-shrinking-stack-rejection",
            ),
        )
        semantic_context = canonical_gym_materialization_context(
            capacity_alternative_id="balanced_yield",
            site=lower,
        )

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={
                    "real-block-shrinking-stack-rejection": program,
                },
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                wraps=select_legal_field_affine_projection,
            ) as selector,
            patch.object(
                candidate_generation,
                "build_program_semantic_carrier_evidence",
                side_effect=AssertionError(
                    "semantic projection must not run after legal rejection"
                ),
            ),
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                canonical_gym_semantic_source(
                    "real-block-shrinking-stack-source"
                ),
                sequence,
                containment_host=lower,
                upper_containment_host=upper,
                floor_containment_hosts=(lower, lower, middle, upper),
                floor_capacity_plan_hash="shrinking-stack-plan",
                target_floor_areas_m2=(180.0, 180.0, 180.0, 180.0),
                **semantic_context,
            )

        self.assertIsNone(materialized)
        self.assertEqual(selector.call_count, 1)

    def test_r293_targets_survive_contained_slab_semantic_handoff(self):
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )
        from design.maas.program_massing.semantic_carriers import (
            semantic_site_context_hash,
        )
        from design.test_task5_regression_fixtures import (
            canonical_gym_materialization_context,
            canonical_gym_semantic_source,
        )

        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "slab"
        )
        host = box(-15.0, -10.0, 15.0, 10.0)
        target_floor_areas = (102.931, 102.931, 74.989, 51.471)
        requested_floor_area = sum(target_floor_areas)
        sequence = VerbSequence(
            "r293-contained-slab",
            "r293-contained-slab",
            (),
            ("geometry_program_directive=r293-contained-slab",),
        )
        semantic_context = canonical_gym_materialization_context(
            capacity_alternative_id="maximum_feasible",
            site=host,
        )

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"r293-contained-slab": program},
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                wraps=select_legal_field_affine_projection,
            ) as selector,
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                canonical_gym_semantic_source("r293-contained-slab-source"),
                sequence,
                containment_host=host,
                upper_containment_host=host,
                floor_containment_hosts=(host, host, host, host),
                minimum_host_plan_coverage=0.5,
                floor_capacity_plan_hash="r293-contained-capacity-plan",
                target_floor_areas_m2=target_floor_areas,
                **semantic_context,
            )

        self.assertIsNotNone(materialized)
        self.assertEqual(selector.call_count, 1)
        assert materialized is not None
        persisted_context = materialized.metadata[
            "final_semantic_projection_context"
        ]
        self.assertEqual(
            persisted_context["site_context_hash"],
            semantic_site_context_hash(
                pnu=semantic_context["pnu"],
                building_type=semantic_context["building_type"],
                site=host,
            ),
        )
        self.assertEqual(
            persisted_context["floor_capacity_plan_hash"],
            "r293-contained-capacity-plan",
        )
        self.assertEqual(
            persisted_context["candidate_target_gfa_m2"],
            requested_floor_area,
        )
        self.assertEqual(
            persisted_context["capacity_measurement_hash"],
            "pending_capacity_measurement",
        )
        self.assertEqual(
            persisted_context["achieved_capacity_band"],
            persisted_context["capacity_alternative_id"],
        )
        self.assertTrue(
            materialized.metadata["program_semantic_carrier_evidence"][
                "hard_pass"
            ],
        )
        capacity_measurement = materialized.metadata[
            "capacity_projection_measurement"
        ]
        self.assertEqual(
            capacity_measurement["requested_floor_area_m2"],
            requested_floor_area,
        )
        self.assertTrue(
            capacity_measurement["requested_capacity_satisfied"],
        )
        self.assertGreaterEqual(
            capacity_measurement["achieved_floor_area_m2"],
            capacity_measurement["requested_floor_area_m2"] * 0.995,
        )
        bridge = materialized.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(
            materialized.metadata["geometry_authority"],
            "final_floorwise_legal_geometry_program",
        )
        self.assertEqual(
            materialized.metadata["final_program_hash"],
            bridge["program_hash"],
        )
        self.assertEqual(
            materialized.metadata["final_geometry_hash"],
            bridge["geometry_hash"],
        )
        self.assertEqual(
            materialized.metadata["legal_field_affine_placement"][
                "projection_mode"
            ],
            "authored_affine_preserved",
        )
        self.assertNotIn(
            "floorwise_legal_sibling_evidence",
            materialized.metadata,
        )

    def test_real_pnu_shrinking_field_uses_floorwise_matrix_mesh_projection(self):
        from design.test_task5_regression_fixtures import (
            canonical_gym_materialization_context,
            canonical_gym_semantic_source,
        )

        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "slab"
        )
        legal_sections = (
            box(-5.0, -5.14655, 5.0, 5.14655),
            box(-5.0, -5.14655, 5.0, 5.14655),
            box(-5.0, -3.74945, 5.0, 3.74945),
            box(-5.0, -2.57355, 5.0, 2.57355),
        )
        target_floor_areas = (92.638, 92.638, 67.49, 46.324)
        source = canonical_gym_semantic_source(
            "real-pnu-shrinking-floor-field-source"
        )
        source = replace(
            source,
            metadata={
                **source.metadata,
                "candidate_floor_context": {
                    "height_m": 14.0,
                    "floors": 4,
                },
            },
        )
        sequence = VerbSequence(
            "real-pnu-shrinking-floor-field",
            "real-pnu-shrinking-floor-field",
            (),
            (
                "geometry_program_directive="
                "real-pnu-shrinking-floor-field",
            ),
        )
        semantic_context = canonical_gym_materialization_context(
            capacity_alternative_id="maximum_feasible",
            site=legal_sections[0],
        )

        with patch.object(
            candidate_generation,
            "_geometry_program_registry",
            return_value={"real-pnu-shrinking-floor-field": program},
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                containment_host=legal_sections[0],
                upper_containment_host=legal_sections[-1],
                floor_containment_hosts=legal_sections,
                minimum_host_plan_coverage=0.9,
                floor_capacity_plan_hash="real-pnu-shrinking-field-plan",
                target_floor_areas_m2=target_floor_areas,
                **semantic_context,
            )

        self.assertIsNotNone(materialized)
        assert materialized is not None
        self.assertEqual(
            materialized.metadata["floorwise_legal_matrix_stack"]["status"],
            "materialized",
        )
        self.assertTrue(
            materialized.metadata["floorwise_visual_projection"]["hard_pass"],
        )
        self.assertEqual(
            materialized.metadata["geometry_authority"],
            "final_floorwise_legal_geometry_program",
        )
        self.assertAlmostEqual(
            materialized.metadata["capacity_projection_measurement"][
                "requested_floor_area_m2"
            ],
            sum(target_floor_areas),
            places=6,
        )
        self.assertTrue(
            materialized.metadata["capacity_projection_measurement"][
                "requested_capacity_satisfied"
            ],
        )
        self.assertTrue(materialized.metadata["final_program_hash"])
        self.assertTrue(materialized.metadata["final_geometry_hash"])
        from design.maas.geometry_language.projected_visual_contract import (
            final_floorwise_visual_geometry_hash,
        )
        self.assertEqual(
            materialized.metadata["final_geometry_hash"],
            final_floorwise_visual_geometry_hash(materialized),
        )
        self.assertEqual(
            materialized.metadata["floorwise_legal_projection"][
                "final_geometry_hash"
            ],
            materialized.metadata["final_geometry_hash"],
        )
        self.assertGreater(len(materialized.surfaces), 0)
        from design.maas.geometry_language.source_bridge import (
            _exact_authored_mesh_section,
        )
        actual_visual_floor_areas = tuple(
            float(section.area)
            for floor_index in range(len(target_floor_areas))
            if (
                section := _exact_authored_mesh_section(
                    materialized,
                    height_fraction=(
                        floor_index + 0.5
                    ) / len(target_floor_areas),
                )
            )
            is not None
        )
        self.assertEqual(
            len(actual_visual_floor_areas),
            len(target_floor_areas),
        )
        self.assertTrue(all(
            actual + 1e-7 >= target * 0.995
            for actual, target in zip(
                actual_visual_floor_areas,
                target_floor_areas,
            )
        ))

    def test_r293_block_full_cap_shrinking_field_rejects_before_semantics(self):
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )
        from design.test_task5_regression_fixtures import (
            canonical_gym_materialization_context,
            canonical_gym_semantic_source,
        )

        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "block"
        )
        legal_sections = _r293_legal_sections()
        target_floor_areas = (102.931, 102.931, 74.989, 51.471)
        sequence = VerbSequence(
            "r293-full-cap-shrinking-rejection",
            "r293-full-cap-shrinking-rejection",
            (),
            (
                "geometry_program_directive="
                "r293-full-cap-shrinking-rejection",
            ),
        )
        semantic_context = canonical_gym_materialization_context(
            capacity_alternative_id="maximum_feasible",
            site=legal_sections[0],
        )

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={
                    "r293-full-cap-shrinking-rejection": program,
                },
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                wraps=select_legal_field_affine_projection,
            ) as selector,
            patch.object(
                candidate_generation,
                "build_program_semantic_carrier_evidence",
                side_effect=AssertionError(
                    "semantic projection must not run after legal rejection"
                ),
            ),
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                canonical_gym_semantic_source(
                    "r293-full-cap-shrinking-source"
                ),
                sequence,
                containment_host=legal_sections[0],
                upper_containment_host=legal_sections[-1],
                floor_containment_hosts=legal_sections,
                minimum_host_plan_coverage=0.5,
                floor_capacity_plan_hash="r293-capacity-plan",
                target_floor_areas_m2=target_floor_areas,
                **semantic_context,
            )

        self.assertIsNone(materialized)
        self.assertEqual(selector.call_count, 1)
        selector_kwargs = selector.call_args.kwargs
        self.assertEqual(
            selector_kwargs["floor_capacity_plan_hash"],
            "r293-capacity-plan",
        )
        self.assertEqual(
            selector_kwargs["target_floor_areas_m2"],
            target_floor_areas,
        )

    def test_contained_slab_export_preserves_exact_source_volume_containment(self):
        """Every exported authored band must remain inside its exact host."""
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )
        from design.maas.geometry_language.source_bridge import (
            compile_site_bound_geometry_program_to_source_mass,
        )

        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "slab"
        )
        host = box(-15.0, -10.0, 15.0, 10.0)
        target_floor_areas = (102.931, 102.931, 74.989, 51.471)
        selected = select_legal_field_affine_projection(
            program,
            legal_sections=(host, host, host, host),
            target_floor_areas_m2=target_floor_areas,
            floor_capacity_plan_hash="r293-contained-volume-plan",
        )
        self.assertIsNotNone(selected)
        assert selected is not None
        source = compile_site_bound_geometry_program_to_source_mass(
            selected.projection.program,
            host,
            name="r293-contained-slab-source",
        )

        self.assertIsNotNone(source)
        assert source is not None
        self.assertTrue(source.volumes)
        for volume in source.volumes:
            self.assertTrue(host.covers(volume.footprint))
            self.assertEqual(
                float(volume.footprint.difference(host).area),
                0.0,
            )
        self.assertEqual(
            selected.evidence["projection_mode"],
            "authored_affine_preserved",
        )
        self.assertGreaterEqual(
            selected.evidence["achieved_aggregate_area_m2"],
            sum(target_floor_areas) * 0.995,
        )
        bridge = source.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(
            bridge["program_hash"],
            selected.projection.program.program_hash(),
        )
        self.assertEqual(
            bridge["geometry_hash"],
            selected.projection.certificate["final_geometry_hash"],
        )
        self.assertNotIn(
            "floorwise_legal_sibling_evidence",
            source.metadata,
        )

    def test_capacity_shortfall_block_shrinking_stack_rejects_before_semantics(
        self,
    ):
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )
        from design.test_task5_regression_fixtures import (
            canonical_gym_materialization_context,
            canonical_gym_semantic_source,
        )

        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "block"
        )
        lower = box(-15.0, -10.0, 15.0, 10.0)
        middle = box(-11.5, -8.0, 11.5, 8.0)
        upper = box(-8.0, -6.0, 8.0, 6.0)
        sequence = VerbSequence(
            "capacity-shortfall",
            "capacity-shortfall",
            (),
            ("geometry_program_directive=capacity-shortfall",),
        )
        semantic_context = canonical_gym_materialization_context(
            capacity_alternative_id="brief_target",
            site=lower,
        )

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"capacity-shortfall": program},
            ),
            patch.object(
                candidate_generation,
                "select_legal_field_affine_projection",
                wraps=select_legal_field_affine_projection,
            ) as selector,
            patch.object(
                candidate_generation,
                "build_program_semantic_carrier_evidence",
                side_effect=AssertionError(
                    "semantic projection must not run after legal rejection"
                ),
            ),
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                canonical_gym_semantic_source("capacity-shortfall-source"),
                sequence,
                containment_host=lower,
                floor_containment_hosts=(lower, lower, middle, upper),
                floor_capacity_plan_hash="capacity-shortfall-plan",
                target_floor_areas_m2=(192.0, 192.0, 192.0, 192.0),
                **semantic_context,
            )

        self.assertIsNone(materialized)
        self.assertEqual(selector.call_count, 1)
        selector_kwargs = selector.call_args.kwargs
        self.assertEqual(
            selector_kwargs["floor_capacity_plan_hash"],
            "capacity-shortfall-plan",
        )
        self.assertEqual(
            selector_kwargs["target_floor_areas_m2"],
            (192.0, 192.0, 192.0, 192.0),
        )

    def test_nonstepped_block_cannot_enter_floorwise_legal_projection(self):
        legal = (box(-10.0, -10.0, 10.0, 10.0),)

        projected = _final_projected_block_program(legal, (100.0,))

        self.assertIsNone(projected)

    def test_certified_site_bound_export_keeps_more_than_2048_triangles(self):
        from design.maas.geometry_language import compile_geometry_program
        from design.maas.geometry_language import source_bridge

        legal = (box(-10.0, -10.0, 10.0, 10.0),)
        projected = _authored_affine_export_program(legal, (100.0,))
        self.assertIsNotNone(projected)
        assert projected is not None
        compilation = compile_geometry_program(projected.program)
        repeats = 2050 // len(compilation.triangles) + 1
        expanded = replace(
            compilation,
            triangles=(compilation.triangles * repeats)[:2050],
        )

        with patch.object(
            source_bridge,
            "_compile_geometry_program_cached",
            return_value=expanded,
        ):
            source = (
                source_bridge.compile_site_bound_geometry_program_to_source_mass(
                    projected.program,
                    legal[0],
                )
            )

        self.assertIsNotNone(source)
        assert source is not None
        bridge = source.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(len(source.surfaces), 2050)
        self.assertEqual(bridge["raw_mesh_triangle_count"], 2050)
        self.assertEqual(bridge["exported_surface_count"], 2050)
        self.assertTrue(bridge["surface_export_complete"])
        self.assertTrue(bridge["surface_payload_hash"])

    def test_certified_site_bound_export_rejects_incomplete_surfaces(self):
        from design.maas.geometry_language import source_bridge

        legal = (box(-10.0, -10.0, 10.0, 10.0),)
        projected = _authored_affine_export_program(legal, (100.0,))
        self.assertIsNotNone(projected)
        assert projected is not None
        original = source_bridge._mesh_surfaces

        def incomplete(*args, **kwargs):
            return original(*args, **kwargs)[:-1]

        with patch.object(
            source_bridge,
            "_mesh_surfaces",
            side_effect=incomplete,
        ):
            source = (
                source_bridge.compile_site_bound_geometry_program_to_source_mass(
                    projected.program,
                    legal[0],
                )
            )

        self.assertIsNone(source)

    def test_certified_site_bound_export_preserves_every_multipart_floor_part(self):
        from design.maas.geometry_language import compile_geometry_program
        from design.maas.geometry_language import source_bridge

        legal = (
            box(-10.0, -10.0, 10.0, 10.0),
            box(-10.0, -10.0, 10.0, 10.0),
        )
        projected = _authored_affine_export_program(
            legal,
            (100.0, 100.0),
        )
        self.assertIsNotNone(projected)
        assert projected is not None
        compilation = compile_geometry_program(projected.program)
        multipart = MultiPolygon((
            box(-8.0, -2.0, -2.0, 2.0),
            box(2.0, -1.5, 6.0, 1.5),
        ))

        with patch.object(
            source_bridge,
            "_mesh_section_polygon",
            return_value=multipart,
        ):
            source = source_bridge._compile_geometry_program_to_source_mass(
                projected.program,
                legal[0],
                max_volume_bands=2,
                _site_bound_compilation=compilation,
            )

        self.assertIsNotNone(source)
        assert source is not None
        self.assertEqual(len(source.volumes), 4)
        self.assertEqual(
            {
                (volume.bottom_fraction, volume.top_fraction)
                for volume in source.volumes
            },
            {(0.0, 0.5), (0.5, 1.0)},
        )

    def test_certified_site_bound_export_preserves_all_sixty_five_bands(self):
        from design.maas.geometry_language import compile_geometry_program
        from design.maas.geometry_language import source_bridge

        legal = (box(-10.0, -10.0, 10.0, 10.0),)
        projected = _authored_affine_export_program(legal, (100.0,))
        self.assertIsNotNone(projected)
        assert projected is not None
        compilation = compile_geometry_program(projected.program)

        with patch.object(
            source_bridge,
            "_mesh_section_polygon",
            return_value=box(-5.0, -5.0, 5.0, 5.0),
        ):
            source = source_bridge._compile_geometry_program_to_source_mass(
                projected.program,
                legal[0],
                max_volume_bands=65,
                _site_bound_compilation=compilation,
            )

        self.assertIsNotNone(source)
        assert source is not None
        bridge = source.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(len(source.volumes), 65)
        self.assertEqual(bridge["requested_proxy_band_count"], 65)
        self.assertEqual(bridge["exported_proxy_band_count"], 65)
        self.assertEqual(bridge["exported_proxy_part_count"], 65)
        self.assertEqual(bridge["proxy_band_part_counts"], [1] * 65)
        self.assertTrue(bridge["proxy_volume_payload_hash"])

    def test_certified_site_bound_export_rejects_a_missing_upper_band(self):
        from design.maas.geometry_language import compile_geometry_program
        from design.maas.geometry_language import source_bridge

        legal = (box(-10.0, -10.0, 10.0, 10.0),)
        projected = _authored_affine_export_program(legal, (100.0,))
        self.assertIsNotNone(projected)
        assert projected is not None
        compilation = compile_geometry_program(projected.program)

        def missing_upper_band(_vertices, _triangles, z):
            return box(-5.0, -5.0, 5.0, 5.0) if z < 0.5 else None

        with patch.object(
            source_bridge,
            "_mesh_section_polygon",
            side_effect=missing_upper_band,
        ):
            source = source_bridge._compile_geometry_program_to_source_mass(
                projected.program,
                legal[0],
                max_volume_bands=2,
                _site_bound_compilation=compilation,
            )

        self.assertIsNone(source)

    def test_certified_site_bound_export_keeps_quarter_square_meter_part(self):
        from design.maas.geometry_language import compile_geometry_program
        from design.maas.geometry_language import source_bridge

        legal = (box(-10.0, -10.0, 10.0, 10.0),)
        projected = _authored_affine_export_program(legal, (100.0,))
        self.assertIsNotNone(projected)
        assert projected is not None
        compilation = compile_geometry_program(projected.program)
        multipart = MultiPolygon((
            box(-8.0, -2.0, -2.0, 2.0),
            box(5.0, 5.0, 5.5, 5.5),
        ))

        with patch.object(
            source_bridge,
            "_mesh_section_polygon",
            return_value=multipart,
        ):
            source = source_bridge._compile_geometry_program_to_source_mass(
                projected.program,
                legal[0],
                max_volume_bands=1,
                _site_bound_compilation=compilation,
            )

        self.assertIsNotNone(source)
        assert source is not None
        bridge = source.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(
            sorted(round(volume.footprint.area, 6) for volume in source.volumes),
            [0.25, 24.0],
        )
        self.assertEqual(bridge["exported_proxy_part_count"], 2)
        self.assertTrue(bridge["proxy_volume_payload_hash"])

    def test_authored_visual_certificate_buffers_each_legal_section_once(self):
        source = _authored_profiled_box_source("authored-buffer-cache")
        legal_sections = (box(-20.0, -20.0, 20.0, 20.0),) * 4
        original_buffer = Polygon.buffer
        buffer_calls = []

        def counting_buffer(section, *args, **kwargs):
            buffer_calls.append(section)
            return original_buffer(section, *args, **kwargs)

        with patch.object(Polygon, "buffer", counting_buffer):
            result = certify_authored_visual_mesh(source, legal_sections)

        self.assertTrue(result.certificate.hard_pass)
        self.assertLessEqual(len(buffer_calls), len(legal_sections))

    def test_authored_visual_certifier_fails_closed_for_invalid_surface_exports(self):
        from design.maas.geometry_language.floorwise_visual_projection import (
            certify_authored_visual_mesh,
        )

        valid = _authored_profiled_box_source("valid-authored")
        invalid_sources = (
            replace(valid, surfaces=()),
            replace(valid, surfaces=(
                replace(
                    valid.surfaces[0],
                    vertices_m=(
                        (0.0, 0.0, 0.0),
                        (1.0, 0.0, 0.0),
                        (2.0, 0.0, 0.0),
                    ),
                ),
            )),
            replace(valid, surfaces=(
                replace(
                    valid.surfaces[0],
                    vertices_m=(
                        (0.0, 0.0, 0.0),
                        (float("nan"), 0.0, 0.0),
                        (0.0, 1.0, 1.0),
                    ),
                ),
            )),
            replace(valid, surfaces=valid.surfaces[:-1]),
        )

        for source in invalid_sources:
            with self.subTest(surface_count=len(source.surfaces)):
                result = certify_authored_visual_mesh(
                    source,
                    (box(-20.0, -20.0, 20.0, 20.0),) * 2,
                )
                self.assertFalse(result.certificate.hard_pass)
                self.assertEqual(result.certificate.status, "failed")
                self.assertEqual(result.surfaces, ())

    def test_authored_visual_certifier_rejects_open_matching_count_export(self):
        from design.maas.geometry_language.floorwise_visual_projection import (
            certify_authored_visual_mesh,
        )

        valid = _authored_profiled_box_source("open-matching-counts")
        open_surfaces = valid.surfaces[:-1]
        bridge = valid.metadata["geometry_program_bridge_evidence"]
        source = replace(
            valid,
            surfaces=open_surfaces,
            metadata={
                **valid.metadata,
                "geometry_program_bridge_evidence": {
                    **bridge,
                    "raw_mesh_triangle_count": len(open_surfaces),
                    "exported_surface_count": len(open_surfaces),
                },
            },
        )

        result = certify_authored_visual_mesh(
            source,
            (box(-20.0, -20.0, 20.0, 20.0),) * 2,
        )

        self.assertFalse(result.certificate.hard_pass)
        self.assertEqual(
            result.certificate.failure_reasons,
            ("unproven_authored_mesh_completeness",),
        )
        self.assertEqual(result.surfaces, ())

    def test_complete_export_accepts_kernel_certified_csg_triangle_soup(self):
        from design.maas.geometry_language.floorwise_visual_projection import (
            _profiled_export_completeness_failure,
        )

        valid = _authored_profiled_box_source("kernel-certified-csg")
        # Manifold CSG can retain redundant coplanar facets in its transport
        # mesh. The directed-edge shortcut rejects that representation even
        # when the authoritative manifold kernel certifies the full export.
        surfaces = (*valid.surfaces, valid.surfaces[0])
        bridge = valid.metadata["geometry_program_bridge_evidence"]
        source = replace(
            valid,
            surfaces=surfaces,
            metadata={
                **valid.metadata,
                "geometry_program_bridge_evidence": {
                    **bridge,
                    "raw_mesh_triangle_count": len(surfaces),
                    "exported_surface_count": len(surfaces),
                },
            },
        )

        with patch(
            "design.maas.geometry_language.floorwise_visual_projection."
            "revalidated_profiled_mesh",
            return_value=SimpleNamespace(
                status="compiled",
                metrics={"closed_solid": True, "manifold": True},
            ),
        ) as revalidate:
            failure = _profiled_export_completeness_failure(source, surfaces)

        self.assertEqual(failure, "")
        revalidate.assert_called_once()

    def test_morphology_accepts_the_same_kernel_certified_csg_triangle_soup(self):
        from design.maas.program_massing.morphology import (
            authoritative_surface_morphology,
        )

        valid = _authored_profiled_box_source("kernel-certified-morphology")
        source = replace(valid, surfaces=(*valid.surfaces, valid.surfaces[0]))

        with patch(
            "design.maas.geometry_language.floorwise_visual_projection."
            "revalidated_profiled_mesh",
            return_value=SimpleNamespace(
                status="compiled",
                metrics={"closed_solid": True, "manifold": True},
            ),
        ):
            metrics = authoritative_surface_morphology(source)

        self.assertTrue(metrics["hard_pass"])
        self.assertTrue(metrics["phenotype"])

    def test_authored_visual_certifier_fails_closed_for_malformed_vertices(self):
        from design.maas.geometry_language.floorwise_visual_projection import (
            certify_authored_visual_mesh,
        )

        valid = _authored_profiled_box_source("malformed-vertices")
        malformed_vertices = (
            (
                (0.0, 0.0),
                (1.0, 0.0),
                (0.0, 1.0),
            ),
            (
                (0.0, 0.0, 0.0),
                ("not-numeric", 0.0, 0.0),
                (0.0, 1.0, 0.0),
            ),
        )

        for vertices in malformed_vertices:
            with self.subTest(vertices=vertices):
                source = replace(
                    valid,
                    surfaces=(
                        replace(valid.surfaces[0], vertices_m=vertices),
                        *valid.surfaces[1:],
                    ),
                )

                result = certify_authored_visual_mesh(
                    source,
                    (box(-20.0, -20.0, 20.0, 20.0),) * 2,
                )

                self.assertFalse(result.certificate.hard_pass)
                self.assertEqual(result.certificate.status, "failed")
                self.assertTrue(result.certificate.failure_reasons)
                self.assertEqual(result.surfaces, ())

    def test_initial_generation_rejects_any_missing_authored_legal_section(self):
        from design.test_task5_regression_fixtures import (
            legal_generation_context_for_site,
        )

        source = _authored_profiled_box_source("missing-legal-section")
        seed = VerbSequence(
            "authored-seed",
            "authored-seed",
            (),
            ("geometry_program_directive=authored-seed",),
        )
        principle = {
            "principle_id": "book:test:authored-legal-sections",
            "execution_verbs": (),
            "generation_stage_order": 1,
        }
        program = object()
        original_materializer = (
            candidate_generation._materialize_directed_geometry
        )

        class InitialMaterializationObserved(Exception):
            pass

        for legal_sections in (
            (box(-20.0, -20.0, 20.0, 20.0), None),
            (None, None),
        ):
            observed = []

            def generation_section(_context, band_height):
                band_index = 0 if float(band_height) < 6.0 else 1
                return legal_sections[band_index]

            def observe_initial_materialization(*args, **kwargs):
                result = original_materializer(*args, **kwargs)
                observed.append(
                    (kwargs["floor_containment_hosts"], result)
                )
                raise InitialMaterializationObserved

            patchers = (
                patch.object(
                    candidate_generation,
                    "_agent_mutated_seeds",
                    return_value=(seed,),
                ),
                patch.object(
                    candidate_generation,
                    "program_seed_variants",
                    side_effect=lambda item, **_kwargs: (item,),
                ),
                patch.object(
                    candidate_generation,
                    "build_book_language_registry",
                    return_value={"principles": (principle,)},
                ),
                patch.object(
                    candidate_generation,
                    "staged_principle_schedule",
                    return_value=((0, principle),),
                ),
                patch.object(
                    candidate_generation,
                    "book_variation_indices",
                    return_value=(0, 1, 2),
                ),
                patch.object(
                    candidate_generation,
                    "book_sentence_variants",
                    return_value=((), (), ()),
                ),
                patch.object(
                    candidate_generation,
                    "book_probe_scope",
                    return_value=("1/1", "horizontal"),
                ),
                patch.object(
                    candidate_generation,
                    "lineage_record",
                    return_value={},
                ),
                patch.object(
                    candidate_generation,
                    "compose_program_with_book_operations",
                    return_value=seed,
                ),
                patch.object(
                    candidate_generation,
                    "build_capacity_alternative",
                    return_value={},
                ),
                patch.object(
                    candidate_generation,
                    "capacity_alternative_for_host",
                    return_value={},
                ),
                patch.object(
                    candidate_generation,
                    "capacity_contract_for_alternative",
                    return_value={},
                ),
                patch.object(
                    candidate_generation,
                    "compile_sequence_to_source_mass",
                    return_value=source,
                ),
                patch.object(
                    candidate_generation,
                    "generation_site_at_height",
                    side_effect=generation_section,
                ),
                patch.object(
                    candidate_generation,
                    "recursive_plan_coverage_floor",
                    return_value=0.5,
                ),
                patch.object(
                    candidate_generation,
                    "_site_access_side_in_principal_frame",
                    return_value="closed",
                ),
                patch.object(
                    candidate_generation,
                    "_geometry_program_registry",
                    return_value={"authored-seed": program},
                ),
                patch.object(
                    candidate_generation,
                    "apply_book_projection_to_geometry_program",
                    return_value=program,
                ),
                patch.object(
                    candidate_generation,
                    "project_program_requirements",
                    return_value=program,
                ),
                patch.object(
                    candidate_generation,
                    "recursive_book_projection_evidence",
                    return_value={"status": "materialized"},
                ),
                patch.object(
                    candidate_generation,
                    "_materialize_directed_geometry",
                    side_effect=observe_initial_materialization,
                ),
            )
            with ExitStack() as stack:
                for patcher in patchers:
                    stack.enter_context(patcher)
                with self.assertRaises(InitialMaterializationObserved):
                    candidate_generation._program_pool(
                        box(-20.0, -20.0, 20.0, 20.0),
                        "program",
                        6.0,
                        2,
                        generation_context=legal_generation_context_for_site(
                            box(-20.0, -20.0, 20.0, 20.0),
                        ),
                        recursive_only=True,
                    )

            self.assertEqual(observed[0][0], legal_sections)
            self.assertIsNone(observed[0][1])

    def test_shared_floor_target_miss_fails_gate_without_changing_authored_metrics(self):
        footprint = box(0.0, 0.0, 10.0, 10.0)
        source = SourceMass(
            name="authored-legal",
            footprint=footprint,
            volumes=(
                SourceVolume(
                    "authored",
                    footprint,
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            metadata={
                "shared_floor_contract": {
                    "schema_version": "arr.maas.shared_floor_contract.v1",
                    "hard_pass": False,
                    "failure_reasons": [
                        "insufficient_floor_area",
                        "insufficient_clear_floor_depth",
                        "insufficient_structural_support",
                        "capacity_target_miss",
                    ],
                    "floor_contract_hash": "advisory-miss",
                    "totals": {
                        "total_floor_area_m2": 20.0,
                        "requested_floors": 4,
                    },
                    "plates": [
                        {
                            "hard_pass": False,
                            "top_height_m": 3.0,
                            "occupied_geometry_utm": (
                                box(0.0, 0.0, 5.0, 5.0).__geo_interface__
                            ),
                        },
                    ],
                },
            },
        )
        candidate = SimpleNamespace(
            source=source,
            feature={"properties": {"variant_id": "authored-legal"}},
            sequence=SimpleNamespace(name="authored-legal"),
            principle_id="book:authored-legal",
        )
        envelope = SimpleNamespace(
            buildable_footprint=box(0.0, 0.0, 20.0, 20.0),
            bcr_limit=50.0,
            far_limit=150.0,
            height_limit=20.0,
            outputs_def=[],
        )
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                return_value={
                    "status": "computed",
                    "required_spaces": 0,
                    "accessible": {"accessible_min": 0},
                },
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {
                        "status": "pass",
                        "provided_spaces": 0,
                    },
                },
            ),
        ):
            row = _evaluate_candidate(
                candidate,
                site_local_utm=box(0.0, 0.0, 20.0, 20.0),
                envelope=envelope,
                sunlight_ring=[],
                pnu="test",
                building_type="neighborhood",
                height_m=12.0,
                floors=4,
                rules={},
                parking_options={},
            )

        self.assertFalse(row["legal_projection"]["hard_pass"])
        self.assertTrue(row["parking_hard_gate"]["hard_pass"])
        self.assertFalse(row["semantic_projection_hard_gate"]["hard_pass"])
        self.assertFalse(row["combined_hard_pass"])
        self.assertIn(
            "shared_floor_contract_failed",
            row["legal_projection"]["failure_reasons"],
        )
        self.assertEqual(row["original_metrics"]["footprint_area_m2"], 100.0)
        self.assertEqual(row["original_metrics"]["floor_area_m2"], 400.0)
        self.assertEqual(row["original_metrics"]["bcr_pct"], 25.0)
        self.assertEqual(row["original_metrics"]["far_pct"], 100.0)
        self.assertEqual(row["original_metrics"]["height_m"], 12.0)

    def test_target_floor_plates_do_not_change_authored_legal_metrics(self):
        footprint = box(0.0, 0.0, 10.0, 10.0)
        facility_areas: list[float] = []

        def candidate(target: str, plate, total_floor_area: float):
            source = SourceMass(
                name=f"authored-{target}",
                footprint=footprint,
                volumes=(
                    SourceVolume(
                        "authored",
                        footprint,
                        0.0,
                        1.0,
                        "geometry_program",
                    ),
                ),
                metadata={
                    "shared_floor_contract": {
                        "schema_version": "arr.maas.shared_floor_contract.v1",
                        "hard_pass": True,
                        "failure_reasons": [],
                        "floor_contract_hash": target,
                        "totals": {
                            "total_floor_area_m2": total_floor_area,
                            "requested_floors": 4,
                        },
                        "plates": [
                            {
                                "hard_pass": True,
                                "top_height_m": 3.0,
                                "occupied_geometry_utm": plate.__geo_interface__,
                            },
                        ],
                    },
                },
            )
            return SimpleNamespace(
                source=source,
                feature={"properties": {"variant_id": target}},
                sequence=SimpleNamespace(name=target),
                principle_id=f"book:{target}",
            )

        def parking_requirement(**kwargs):
            facility_areas.append(float(kwargs["facility_area_m2"]))
            return {
                "status": "computed",
                "required_spaces": 0,
                "accessible": {"accessible_min": 0},
            }

        envelope = SimpleNamespace(
            buildable_footprint=box(0.0, 0.0, 20.0, 20.0),
            bcr_limit=80.0,
            far_limit=300.0,
            height_limit=20.0,
            outputs_def=[],
        )
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                side_effect=parking_requirement,
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {
                        "status": "pass",
                        "provided_spaces": 0,
                    },
                },
            ),
        ):
            rows = [
                _evaluate_candidate(
                    item,
                    site_local_utm=box(0.0, 0.0, 20.0, 20.0),
                    envelope=envelope,
                    sunlight_ring=[],
                    pnu="test",
                    building_type="neighborhood",
                    height_m=12.0,
                    floors=4,
                    rules={},
                    parking_options={},
                )
                for item in (
                    candidate("low-target", box(0.0, 0.0, 5.0, 5.0), 20.0),
                    candidate("high-target", box(0.0, 0.0, 15.0, 15.0), 900.0),
                )
            ]

        self.assertTrue(all(
            row["legal_projection"]["hard_pass"]
            and row["parking_hard_gate"]["hard_pass"]
            for row in rows
        ))
        self.assertTrue(all(
            not row["semantic_projection_hard_gate"]["hard_pass"]
            and not row["combined_hard_pass"]
            for row in rows
        ))
        metric_keys = (
            "footprint_area_m2",
            "floor_area_m2",
            "bcr_pct",
            "far_pct",
            "height_m",
            "open_pct",
        )
        for key in metric_keys:
            self.assertEqual(
                rows[0]["original_metrics"][key],
                rows[1]["original_metrics"][key],
            )
            self.assertEqual(
                rows[0]["projected_metrics"][key],
                rows[1]["projected_metrics"][key],
            )
            self.assertEqual(
                rows[0]["original_metrics"][key],
                rows[0]["projected_metrics"][key],
            )
        self.assertEqual(facility_areas, [400.0, 400.0])

    def test_authored_legal_threshold_and_containment_failures_still_reject(self):
        site = box(0.0, 0.0, 20.0, 20.0)
        cases = (
            (
                "bcr",
                box(0.0, 0.0, 15.0, 15.0),
                SimpleNamespace(
                    buildable_footprint=site,
                    bcr_limit=50.0,
                    far_limit=1000.0,
                    height_limit=30.0,
                    outputs_def=[],
                ),
                "bcr_limit_exceeded",
            ),
            (
                "far",
                box(0.0, 0.0, 10.0, 10.0),
                SimpleNamespace(
                    buildable_footprint=site,
                    bcr_limit=100.0,
                    far_limit=80.0,
                    height_limit=30.0,
                    outputs_def=[],
                ),
                "far_limit_exceeded",
            ),
            (
                "height",
                box(0.0, 0.0, 10.0, 10.0),
                SimpleNamespace(
                    buildable_footprint=site,
                    bcr_limit=100.0,
                    far_limit=1000.0,
                    height_limit=10.0,
                    outputs_def=[],
                ),
                "height_limit_exceeded",
            ),
            (
                "containment",
                box(0.0, 0.0, 10.0, 10.0),
                SimpleNamespace(
                    buildable_footprint=box(0.0, 0.0, 9.0, 10.0),
                    bcr_limit=100.0,
                    far_limit=1000.0,
                    height_limit=30.0,
                    outputs_def=[],
                ),
                "authored_mass_outside_legal_envelope",
            ),
        )
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                return_value={
                    "status": "computed",
                    "required_spaces": 0,
                    "accessible": {"accessible_min": 0},
                },
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {
                        "status": "pass",
                        "provided_spaces": 0,
                    },
                },
            ),
        ):
            for name, footprint, envelope, expected_failure in cases:
                source = SourceMass(
                    name=name,
                    footprint=footprint,
                    volumes=(
                        SourceVolume(
                            "authored",
                            footprint,
                            0.0,
                            1.0,
                            "geometry_program",
                        ),
                    ),
                    metadata={
                        "shared_floor_contract": {
                            "schema_version": (
                                "arr.maas.shared_floor_contract.v1"
                            ),
                            "hard_pass": True,
                            "failure_reasons": [],
                            "floor_contract_hash": f"misleading-{name}",
                            "totals": {
                                "total_floor_area_m2": 1.0,
                                "requested_floors": 4,
                            },
                            "plates": [
                                {
                                    "hard_pass": True,
                                    "top_height_m": 1.0,
                                    "occupied_geometry_utm": (
                                        box(0.0, 0.0, 1.0, 1.0).__geo_interface__
                                    ),
                                },
                            ],
                        },
                    },
                )
                candidate = SimpleNamespace(
                    source=source,
                    feature={"properties": {"variant_id": name}},
                    sequence=SimpleNamespace(name=name),
                    principle_id=f"book:{name}",
                )
                with self.subTest(case=name):
                    row = _evaluate_candidate(
                        candidate,
                        site_local_utm=site,
                        envelope=envelope,
                        sunlight_ring=[],
                        pnu="test",
                        building_type="neighborhood",
                        height_m=12.0,
                        floors=4,
                        rules={},
                        parking_options={},
                    )
                    self.assertFalse(row["combined_hard_pass"])
                    self.assertIn(
                        expected_failure,
                        row["legal_projection"]["failure_reasons"],
                    )

    def test_authored_mass_escaping_legal_envelope_is_rejected_not_clipped(self):
        footprint = box(0.0, 0.0, 12.0, 10.0)
        source = SourceMass(
            name="escaping-wing",
            footprint=footprint,
            volumes=(SourceVolume("wing", footprint, 0.0, 1.0, "geometry_program"),),
        )
        candidate = SimpleNamespace(
            source=source,
            feature={"properties": {"variant_id": "escaping-wing"}},
            sequence=SimpleNamespace(name="escaping-wing"),
            principle_id="book:wing",
        )
        envelope = SimpleNamespace(
            buildable_footprint=box(0.0, 0.0, 10.0, 10.0),
            bcr_limit=100.0,
            far_limit=1000.0,
            height_limit=30.0,
            outputs_def=[],
        )
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                return_value={
                    "status": "computed",
                    "required_spaces": 0,
                    "accessible": {"accessible_min": 0},
                },
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {"status": "pass", "provided_spaces": 0},
                },
            ),
        ):
            row = _evaluate_candidate(
                candidate,
                site_local_utm=box(0.0, 0.0, 20.0, 20.0),
                envelope=envelope,
                sunlight_ring=[],
                pnu="test",
                building_type="neighborhood",
                height_m=12.0,
                floors=4,
                rules={},
                parking_options={},
            )

        self.assertFalse(row["combined_hard_pass"])
        self.assertIn(
            "authored_mass_outside_legal_envelope",
            row["legal_projection"]["failure_reasons"],
        )
        self.assertEqual(source.footprint, footprint)

    def test_surface_only_overhang_with_legal_volumes_is_rejected(self):
        source = _authored_profiled_box_source("surface-only-overhang")
        candidate = SimpleNamespace(
            source=source,
            feature={
                "properties": {"variant_id": "surface-only-overhang"}
            },
            sequence=SimpleNamespace(name="surface-only-overhang"),
            principle_id="book:surface-only-overhang",
        )
        envelope = SimpleNamespace(
            buildable_footprint=box(-5.0, -5.0, 5.0, 5.0),
            bcr_limit=100.0,
            far_limit=1000.0,
            height_limit=30.0,
            outputs_def=[],
        )
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                return_value={
                    "status": "computed",
                    "required_spaces": 0,
                    "accessible": {"accessible_min": 0},
                },
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {
                        "status": "pass",
                        "provided_spaces": 0,
                    },
                },
            ),
        ):
            row = _evaluate_candidate(
                candidate,
                site_local_utm=box(-10.0, -10.0, 10.0, 10.0),
                envelope=envelope,
                sunlight_ring=[],
                pnu="test",
                building_type="neighborhood",
                height_m=12.0,
                floors=4,
                rules={},
                parking_options={},
            )

        self.assertFalse(row["combined_hard_pass"])
        self.assertIn(
            "authored_visual_surface_outside_legal_envelope",
            row["legal_projection"]["failure_reasons"],
        )
        self.assertEqual(
            max(
                x
                for surface in source.surfaces
                for x, _y, _z in surface.vertices_m
            ),
            6.5,
        )

    def test_sub_point_one_square_meter_escape_still_fails_containment(self):
        legal = box(0.0, 0.0, 10.0, 10.0)
        footprint = box(0.0, 0.0, 10.0005, 10.0)
        source = SourceMass(
            name="tiny-escape",
            footprint=footprint,
            volumes=(SourceVolume("tiny", footprint, 0.0, 1.0, "geometry_program"),),
        )
        candidate = SimpleNamespace(
            source=source,
            feature={"properties": {"variant_id": "tiny-escape"}},
            sequence=SimpleNamespace(name="tiny-escape"),
            principle_id="book:tiny",
        )
        envelope = SimpleNamespace(
            buildable_footprint=legal,
            bcr_limit=100.0,
            far_limit=1000.0,
            height_limit=30.0,
            outputs_def=[],
        )
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                return_value={
                    "status": "computed",
                    "required_spaces": 0,
                    "accessible": {"accessible_min": 0},
                },
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {"status": "pass", "provided_spaces": 0},
                },
            ),
        ):
            row = _evaluate_candidate(
                candidate,
                site_local_utm=box(0.0, 0.0, 20.0, 20.0),
                envelope=envelope,
                sunlight_ring=[],
                pnu="test",
                building_type="neighborhood",
                height_m=12.0,
                floors=4,
                rules={},
                parking_options={},
            )

        self.assertAlmostEqual(
            footprint.difference(legal).area,
            0.005,
            places=6,
        )
        self.assertFalse(row["combined_hard_pass"])
        self.assertIn(
            "authored_mass_outside_legal_envelope",
            row["legal_projection"]["failure_reasons"],
        )

    def test_authored_curved_stepped_voided_and_winged_mesh_hashes_differ(self):
        fixtures = {
            "curved": ((0.0, 0.0, 0.0), (4.0, 0.5, 0.0), (1.5, 3.5, 1.0)),
            "stepped": ((0.0, 0.0, 0.0), (4.0, 0.0, 0.3), (2.0, 3.0, 1.0)),
            "voided": ((0.0, 0.0, 0.2), (3.0, 0.0, 0.0), (1.0, 4.0, 0.8)),
            "winged": ((-1.0, 0.0, 0.0), (5.0, 0.0, 0.0), (0.5, 2.0, 1.0)),
        }
        hashes = {
            name: projected_surface_visual_hash((
                SourceSurface(
                    role=name,
                    volume_role=name,
                    verb="geometry_program",
                    surface_type="profiled_recursive_solid_mesh",
                    vertices_m=vertices,
                    semantic_patch_id=name,
                ),
            ))
            for name, vertices in fixtures.items()
        }

        self.assertEqual(len(set(hashes.values())), len(fixtures))

    def test_real_selector_is_invariant_to_advisory_capacity_labels(self):
        host = box(0.0, 0.0, 40.0, 30.0)
        sources = [
            compile_geometry_program_to_source_mass(program, host)
            for program in architectural_shape_programs()[:12]
        ]
        self.assertTrue(all(source is not None for source in sources))

        def pool(*, labelled: bool):
            candidates = []
            for index, source in enumerate(sources):
                assert source is not None
                alternative = (
                    "spatial_reserve" if index < 10 else "maximum_feasible"
                )
                candidates.append(_Candidate(
                    principle_id=f"real:{index:02d}",
                    principle_kind="base_operative",
                    operation=f"operation:{index:02d}",
                    sequence=VerbSequence(
                        f"real-seed-{index:02d}",
                        f"real seed {index:02d}",
                        (),
                    ),
                    source=replace(source, metadata={
                        **source.metadata,
                        "capacity_alternative_projection": (
                            {
                                "alternative_id": alternative,
                                "target_hard_pass": False,
                            }
                            if labelled
                            else {}
                        ),
                    }),
                    feature={"type": "Feature", "properties": {}},
                    score=round(1.0 - index * 0.01, 6),
                ))
            return candidates

        directive = {
            "max_solid_phenotype_count": 10,
            "max_wedge_like_count": 10,
            "max_pyramidal_like_count": 10,
        }
        baseline = portfolio_selection._select(
            pool(labelled=False),
            target=8,
            visual_directive=directive,
        )
        labelled = portfolio_selection._select(
            pool(labelled=True),
            target=8,
            visual_directive=directive,
        )

        self.assertTrue(baseline)
        self.assertEqual(
            [candidate.principle_id for candidate in labelled],
            [candidate.principle_id for candidate in baseline],
        )

    def test_rebalance_is_invariant_to_advisory_capacity_labels(self):
        source = _authored_profiled_box_source("rebalance")

        def candidate(
            principle_id: str,
            *,
            score: float,
            phenotype: str,
            alternative: str = "",
        ) -> _Candidate:
            metadata = dict(source.metadata)
            if alternative:
                metadata["capacity_alternative_projection"] = {
                    "alternative_id": alternative,
                    "target_hard_pass": False,
                }
            return _Candidate(
                principle_id=principle_id,
                principle_kind="base_operative",
                operation=principle_id,
                sequence=VerbSequence(principle_id, principle_id, ()),
                source=replace(source, name=principle_id, metadata=metadata),
                feature={
                    "type": "Feature",
                    "properties": {"phenotype": phenotype},
                },
                score=score,
            )

        def run(*, labelled: bool) -> list[str]:
            removed = candidate(
                "removed",
                score=0.1,
                phenotype="prismatic",
                alternative="brief_target" if labelled else "",
            )
            kept = candidate(
                "kept",
                score=0.9,
                phenotype="prismatic",
                alternative="balanced_yield" if labelled else "",
            )
            replacement = candidate(
                "replacement",
                score=0.8,
                phenotype="curved",
                alternative="balanced_yield" if labelled else "",
            )
            with (
                patch.object(
                    portfolio_selection,
                    "_solid_morphology_metrics",
                    side_effect=lambda item: {
                        "phenotype": item.feature["properties"]["phenotype"],
                        "wedge_like": False,
                        "pyramidal_like": False,
                    },
                ),
                patch.object(portfolio_selection, "_scope_key", return_value="1/1"),
                patch.object(
                    portfolio_selection,
                    "_seed_family",
                    side_effect=lambda item: item.principle_id,
                ),
                patch.object(portfolio_selection, "_section_family", return_value="section"),
                patch.object(portfolio_selection, "_roof_archetype", return_value="roof"),
                patch.object(portfolio_selection, "_chassis_family", return_value="chassis"),
                patch.object(
                    portfolio_selection,
                    "_design_concept_descriptor",
                    side_effect=lambda item: {
                        "ground_strategy": "direct_edge",
                        "concept_key": item.principle_id,
                        "frontage_aligned": False,
                    },
                ),
            ):
                result = portfolio_selection._rebalance_measured_morphologies(
                    [removed, kept],
                    [removed, kept, replacement],
                    target=2,
                    visual_directive={
                        "required_solid_phenotypes": ["curved"],
                        "max_solid_phenotype_count": 2,
                    },
                    capacity_alternative_quotas={
                        "brief_target": 1,
                        "balanced_yield": 1,
                    },
                    compatibility_analysis=SimpleNamespace(
                        distance=lambda _left, _right: 1.0,
                    ),
                )
            return [item.principle_id for item in result]

        self.assertEqual(run(labelled=True), run(labelled=False))

    def test_mass_stage_design_score_is_independent_of_capacity_fit(self):
        low_capacity = candidate_generation._mass_stage_design_score(
            program_fit_score=0.74,
            architectural_score=0.82,
            advisory_capacity_score=0.05,
        )
        high_capacity = candidate_generation._mass_stage_design_score(
            program_fit_score=0.74,
            architectural_score=0.82,
            advisory_capacity_score=0.99,
        )

        self.assertEqual(low_capacity, high_capacity)
