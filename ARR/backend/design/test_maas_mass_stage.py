from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language import candidate_generation
from design.maas.book_language.candidate_generation import (
    _eligible_smoke_floor_candidate,
)
from design.maas.book_language.capacity_routing import (
    route_capacity_target_hard_passes,
)
from design.maas.book_language import portfolio_benchmark, portfolio_selection
from design.maas.book_language.candidate_analysis import _Candidate
from design.maas.book_language.downstream_hard_gate import _evaluate_candidate
from design.maas.geometry_language import (
    architectural_shape_programs,
    compile_geometry_program_to_source_mass,
)
from design.maas.geometry_language.floorwise_visual_projection import (
    projected_surface_visual_hash,
)
from design.maas.geometry_language.projected_visual_contract import (
    validate_projected_visual_artifact,
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


class MaasStageHardContractTests(SimpleTestCase):
    def test_capacity_miss_is_rejected_before_paid_visual_review(self):
        miss = _candidate("authored-winged", capacity_pass=False)

        routed, evidence = route_capacity_target_hard_passes(
            [miss],
            stage="initial_final_book_paid_vlm",
        )

        self.assertEqual(routed, [])
        self.assertEqual(evidence["hard_pass_count"], 0)
        self.assertEqual(evidence["rejected_before_paid_vlm_count"], 1)

    def test_selector_universe_excludes_measured_capacity_miss(self):
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

        self.assertEqual(universe, [exact])
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

    def test_capacity_misses_cannot_fill_final_mass_slots(self):
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
        self.assertEqual(trace["capacity_target_gate_rejected_count"], 12)

    def test_floor_targets_use_canonical_projected_visible_mass_and_visual_hash(self):
        footprint = box(0.0, 0.0, 12.0, 8.0)
        authored_surface = SourceSurface(
            role="authored-wing",
            volume_role="wing",
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=((0.0, 0.0, 0.0), (12.0, 0.0, 0.0), (3.0, 8.0, 1.0)),
            semantic_patch_id="authored-wing",
        )
        source = SourceMass(
            name="authored-wing",
            footprint=footprint,
            volumes=(SourceVolume("wing", footprint, 0.0, 1.0, "geometry_program"),),
            surfaces=(authored_surface,),
        )

        def floorwise_materializer(item, **kwargs):
            scale = float(kwargs["target_floor_areas_m2"][0]) / 40.0
            transformed_surface = replace(
                authored_surface,
                vertices_m=(
                    (0.0, 0.0, 0.0),
                    (6.0 * scale, 0.0, 0.0),
                    (1.5 * scale, 4.0, 1.0),
                ),
            )
            sibling_footprint = box(0.0, 0.0, 6.0 * scale, 4.0)
            return replace(
                item,
                footprint=sibling_footprint,
                volumes=(
                    SourceVolume(
                        "floorwise-sibling",
                        sibling_footprint,
                        0.0,
                        1.0,
                        "floorwise_legal_matrix4",
                    ),
                ),
                surfaces=(transformed_surface,),
                metadata={
                    **item.metadata,
                    "floorwise_legal_matrix_stack": {
                        "status": "materialized",
                        "target_floor_areas_m2": list(
                            kwargs["target_floor_areas_m2"]
                        ),
                    },
                    "floorwise_visual_projection": {
                        "schema_version": "arr.maas.floorwise_visual_projection.v1",
                        "status": "certified",
                        "hard_pass": True,
                        "failure_reasons": [],
                        "visual_hash": projected_surface_visual_hash(
                            (transformed_surface,)
                        ),
                        "source_surface_count": 1,
                        "projected_surface_count": 1,
                        "legal_sample_count": 1,
                        "capacity_gfa_m2": 80.0,
                        "capacity_authority": "floorwise_legal_volumes",
                        "source_surface_coordinate_frame": (
                            "source_footprint_centroid_local_xy_normalized_z"
                        ),
                        "projected_surface_coordinate_frame": (
                            "capacity_source_centroid_local_xy_normalized_z"
                        ),
                        "matrix_convention": "row_major_column_vector",
                    },
                },
            )

        sequence = SimpleNamespace(
            notes=("geometry_program_directive=authored-wing",)
        )
        patches = (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"authored-wing": object()},
            ),
            patch.object(
                candidate_generation,
                "apply_book_projection_to_geometry_program",
                side_effect=lambda program, _sequence: program,
            ),
            patch.object(
                candidate_generation,
                "project_program_requirements",
                side_effect=lambda program, **_kwargs: program,
            ),
            patch.object(
                candidate_generation,
                "replace_source_dominant_with_geometry_program",
                side_effect=lambda item, _program, **_kwargs: item,
            ),
            patch.object(
                candidate_generation,
                "materialize_floorwise_legal_source",
                side_effect=floorwise_materializer,
            ),
            patch.object(
                candidate_generation,
                "recursive_book_projection_evidence",
                return_value={"status": "materialized"},
            ),
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            low_target = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                floor_containment_hosts=(box(0, 0, 20, 20),) * 2,
                target_floor_areas_m2=(32.0, 32.0),
            )
            high_target = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                floor_containment_hosts=(box(0, 0, 20, 20),) * 2,
                target_floor_areas_m2=(48.0, 48.0),
            )

        self.assertIsNotNone(low_target)
        self.assertIsNotNone(high_target)
        assert low_target is not None and high_target is not None
        for projected in (low_target, high_target):
            self.assertEqual(
                projected.metadata["floorwise_visual_projection"]["visual_hash"],
                projected_surface_visual_hash(projected.surfaces),
            )
            self.assertEqual(
                projected.metadata["floorwise_visual_projection"][
                    "projected_surface_coordinate_frame"
                ],
                "capacity_source_centroid_local_xy_normalized_z",
            )
        self.assertNotEqual(
            low_target.metadata["floorwise_visual_projection"]["visual_hash"],
            high_target.metadata["floorwise_visual_projection"]["visual_hash"],
        )

    def test_generator_fails_closed_when_canonical_projection_is_unavailable(self):
        source = SourceMass(
            name="authored-overhang",
            footprint=box(0.0, 0.0, 12.0, 8.0),
            volumes=(
                SourceVolume(
                    "overhang",
                    box(0.0, 0.0, 12.0, 8.0),
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            surfaces=(
                SourceSurface(
                    role="authored-overhang",
                    volume_role="overhang",
                    verb="geometry_program",
                    surface_type="profiled_recursive_solid_mesh",
                    vertices_m=(
                        (0.0, 0.0, 0.0),
                        (12.0, 0.0, 0.0),
                        (18.0, 8.0, 1.0),
                    ),
                ),
            ),
        )
        sequence = SimpleNamespace(
            notes=("geometry_program_directive=authored-overhang",)
        )
        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"authored-overhang": object()},
            ),
            patch.object(
                candidate_generation,
                "apply_book_projection_to_geometry_program",
                side_effect=lambda program, _sequence: program,
            ),
            patch.object(
                candidate_generation,
                "project_program_requirements",
                side_effect=lambda program, **_kwargs: program,
            ),
            patch.object(
                candidate_generation,
                "replace_source_dominant_with_geometry_program",
                side_effect=lambda item, _program, **_kwargs: item,
            ),
            patch.object(
                candidate_generation,
                "materialize_floorwise_legal_source",
                return_value=None,
            ),
            patch.object(
                candidate_generation,
                "recursive_book_projection_evidence",
                return_value={"status": "materialized"},
            ),
        ):
            projected = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                floor_containment_hosts=(box(0, 0, 10, 10),) * 2,
                target_floor_areas_m2=(80.0, 80.0),
            )

        self.assertIsNone(projected)

    def test_authored_visual_certificate_survives_archive_serializer_roundtrip(self):
        source = _authored_profiled_box_source("authored-curved")
        sequence = SimpleNamespace(
            notes=("geometry_program_directive=authored-curved",)
        )
        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={"authored-curved": object()},
            ),
            patch.object(
                candidate_generation,
                "apply_book_projection_to_geometry_program",
                side_effect=lambda program, _sequence: program,
            ),
            patch.object(
                candidate_generation,
                "project_program_requirements",
                side_effect=lambda program, **_kwargs: program,
            ),
            patch.object(
                candidate_generation,
                "replace_source_dominant_with_geometry_program",
                side_effect=lambda item, _program, **_kwargs: item,
            ),
            patch.object(
                candidate_generation,
                "recursive_book_projection_evidence",
                return_value={"status": "materialized"},
            ),
        ):
            projected = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                floor_containment_hosts=(box(-10, -10, 10, 10),) * 2,
                target_floor_areas_m2=(100.0, 100.0),
                minimum_host_plan_coverage=0.5,
                floor_capacity_plan_hash="canonical-plan",
            )

        self.assertIsNotNone(projected)
        assert projected is not None
        try:
            artifact = portfolio_benchmark._certified_projected_visual_artifact(
                projected
            )
        except ValueError as exc:
            self.fail(f"archive serializer rejected MASS certificate: {exc}")
        artifact["identity"] = {
            "geometryHash": artifact["projectedVisualGeometryHash"],
        }
        rebound = validate_projected_visual_artifact(artifact)
        self.assertIsNotNone(rebound)
        self.assertEqual(
            rebound.visual_hash,
            projected.metadata["floorwise_visual_projection"]["visual_hash"],
        )
        self.assertEqual(
            projected.metadata["floorwise_legal_matrix_stack"][
                "floor_capacity_plan_hash"
            ],
            "canonical-plan",
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

    def test_real_selector_excludes_measured_capacity_misses(self):
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
        self.assertEqual(labelled, [])

    def test_rebalance_compares_only_capacity_hard_pass_alternatives(self):
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
                    "target_hard_pass": True,
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
