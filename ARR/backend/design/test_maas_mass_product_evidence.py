from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management.base import CommandError
from django.test import SimpleTestCase
from PIL import Image
from shapely.geometry import box, mapping

from design.maas.geometry_language import GeometryProgramBuilder
from design.maas.mass_product_evidence import serialize_mass_product_evidence
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume


class MaasMassProductEvidenceTest(SimpleTestCase):
    def test_serializes_floor_product_from_typed_contract_without_recalculation(self):
        builder = GeometryProgramBuilder("plan_aware_mass")
        floor = builder.add(
            "primitive",
            "box",
            parameters={
                "width": 12.0,
                "depth": 8.0,
                "height": 3.0,
            },
            semantic_role="floor_volume",
        )
        program = builder.build(
            floor,
            shared_floor_contract={
                "schema_version": "arr.maas.shared_floor_contract.v1",
                "floor_capacity_plan_hash": "capacity-plan-123",
                "floor_contract_hash": "floor-contract-123",
                "floor_height_m": 3.0,
                "totals": {
                    "num_floors": 5,
                    "total_floor_area_m2": 294.2,
                    "far_pct": 111.287,
                },
            },
            floorwise_legal_matrix_stack={
                "matrix_convention": "row_major_column_vector",
                "floor_capacity_plan_hash": "capacity-plan-123",
            },
        )
        evidence = serialize_mass_product_evidence(
            program=program,
            hard_gates={
                "projectedMetrics": {
                    "bcr_pct": 55.4,
                    "far_pct": 111.287,
                    "floor_area_m2": 294.2,
                    "floor_contract_hash": "floor-contract-123",
                },
                "parking": {
                    "required_spaces": 2,
                    "provided_spaces": 2,
                },
            },
            passport={
                "activation_graph": {
                    "nodes": [{
                        "id": "elevation:result",
                        "status": "blocked",
                        "evidence": {},
                    }],
                },
            },
        )

        self.assertEqual(evidence["num_floors"], 5)
        self.assertEqual(evidence["floor_height_m"], 3.0)
        self.assertEqual(evidence["total_floor_area_m2"], 294.2)
        self.assertEqual(evidence["bcr_pct"], 55.4)
        self.assertEqual(evidence["far_pct"], 111.287)
        self.assertEqual(evidence["parking_required"], 2)
        self.assertEqual(evidence["parking_provided"], 2)
        self.assertEqual(evidence["floor_contract_hash"], "floor-contract-123")
        self.assertEqual(evidence["floor_capacity_plan_hash"], "capacity-plan-123")
        self.assertEqual(evidence["elevation_status"], "blocked")
        self.assertEqual(evidence["matrix_convention"], "row_major_column_vector")
        self.assertEqual(len(evidence["floor_matrix_stack"]), 1)
        self.assertEqual(
            evidence["floor_matrix_stack"][0]["matrix4"],
            [
                [12.0, 0.0, 0.0, 0.0],
                [0.0, 8.0, 0.0, 0.0],
                [0.0, 0.0, 3.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        )

    def test_missing_product_evidence_is_explicitly_not_evaluated(self):
        builder = GeometryProgramBuilder("legacy_mass")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )

        evidence = serialize_mass_product_evidence(program=builder.build(root))

        self.assertIsNone(evidence["num_floors"])
        self.assertIsNone(evidence["total_floor_area_m2"])
        self.assertEqual(evidence["floor_capacity_plan_hash"], "")
        self.assertEqual(evidence["elevation_status"], "not_evaluated")
        self.assertEqual(len(evidence["floor_matrix_stack"]), 1)

    def test_final_legal_geometry_hash_is_not_replaced_by_authored_upstream_hashes(self):
        builder = GeometryProgramBuilder("hash_bound_mass")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 2.0, "depth": 3.0, "height": 4.0},
        )
        final_hash = "f" * 64
        authored_hash = "a" * 64
        capacity_hash = "c" * 64

        evidence = serialize_mass_product_evidence(
            program=builder.build(root),
            compilation={
                "geometry_hash": final_hash,
                "authored_geometry_hash": authored_hash,
                "metrics": {
                    "capacity_geometry_hash": capacity_hash,
                },
            },
            passport={
                "final_legal_geometry_hash": final_hash,
                "elevation_evidence": {
                    "final_legal_geometry_hash": final_hash,
                },
            },
        )

        self.assertEqual(evidence["final_legal_geometry_hash"], final_hash)
        self.assertEqual(
            evidence["upstream_geometry_hashes"],
            {
                "authored_geometry_hash": authored_hash,
                "capacity_geometry_hash": capacity_hash,
            },
        )
        self.assertNotIn(
            evidence["final_legal_geometry_hash"],
            evidence["upstream_geometry_hashes"].values(),
        )

    def test_authored_hash_alone_cannot_substitute_for_final_legal_geometry_hash(self):
        builder = GeometryProgramBuilder("upstream_only_mass")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 2.0, "depth": 3.0, "height": 4.0},
        )

        evidence = serialize_mass_product_evidence(
            program=builder.build(root),
            compilation={"authored_geometry_hash": "a" * 64},
        )

        self.assertEqual(evidence["final_legal_geometry_hash"], "")
        self.assertEqual(
            evidence["upstream_geometry_hashes"]["authored_geometry_hash"],
            "a" * 64,
        )

    def test_diagnostic_target_is_strictly_bounded_and_never_completes_portfolio(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            Command,
            _apply_diagnostic_summary_policy,
        )

        parser = Command().create_parser("manage.py", "benchmark")
        options = vars(parser.parse_args(["--diagnostic-target", "3"]))
        self.assertEqual(options["diagnostic_target"], 3)
        with self.assertRaises(CommandError):
            parser.parse_args(["--diagnostic-target", "4"])

        options = vars(parser.parse_args(["--diagnostic-target", "20"]))
        self.assertEqual(options["diagnostic_target"], 20)

        summary = {
            "status": "pass",
            "programs": [{
                "status": "pass",
                "portfolio_requirement": {
                    "minimum_count": 10,
                    "selection_target": 10,
                },
                "portfolio_completion": {
                    "hard_pass": True,
                    "failures": [],
                },
            }],
        }
        _apply_diagnostic_summary_policy(summary, target=20)

        self.assertTrue(summary["diagnostic_only"])
        self.assertEqual(summary["diagnostic_target"], 20)
        self.assertEqual(summary["status"], "diagnostic_only")
        program = summary["programs"][0]
        self.assertTrue(program["diagnostic_only"])
        self.assertEqual(program["status"], "diagnostic_only")
        self.assertFalse(program["portfolio_completion"]["hard_pass"])
        self.assertEqual(
            program["portfolio_requirement"]["selection_target"],
            10,
            "diagnostic mode must not weaken the production exact-ten contract",
        )

    def test_cross_pnu_runner_builds_isolated_commands_and_hash_summary(self):
        from tools.verify_single_authority_mass_pnus import (
            build_benchmark_command,
            summarize_pnu_result,
            unique_output_directory,
        )

        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = unique_output_directory(
                root,
                pnu="1168011800104170004",
                ordinal=1,
            )
            second = unique_output_directory(
                root,
                pnu="1168011800104670003",
                ordinal=2,
            )
            first_command = build_benchmark_command(
                pnu="1168011800104170004",
                output_directory=first,
                diagnostic_target=3,
            )

        self.assertNotEqual(first, second)
        self.assertIn("--pnu", first_command)
        self.assertIn("1168011800104170004", first_command)
        self.assertIn("--diagnostic-target", first_command)
        self.assertIn("3", first_command)
        self.assertIn(str(first), first_command)
        self.assertNotIn("--outcome-graph", first_command)

        final_hash = "f" * 64
        summary = summarize_pnu_result({
            "pnu": "1168011800104170004",
            "diagnostic_only": True,
            "summary_png": "summary.png",
            "programs": [{
                "selected_count": 3,
                "book_base_volume_scope_count": 3,
                "counts": {
                    "capacity_alternative_diagnostics": {
                        "selected_achieved_band_counts": {
                            "floor": 1,
                            "balanced": 1,
                            "maximum": 1,
                        },
                    },
                },
                "language_metrics": {
                    "stepped_count": 1,
                    "roof_archetype_count": 2,
                    "solid_phenotype_count": 3,
                },
                "rows": [{
                    "far_pct": 101.5,
                    "final_legal_geometry_hash": final_hash,
                    "archive_render_evidence": {
                        "final_legal_geometry_hash": final_hash,
                    },
                    "mass_execution_passport": {
                        "final_legal_geometry_hash": final_hash,
                    },
                    "elevation_evidence": {
                        "final_legal_geometry_hash": final_hash,
                    },
                    "law_graph_evidence_hash": "l" * 64,
                    "parking_required": 2,
                    "parking_layout_status": "pass",
                }],
                "png": "program.png",
                "failures": [],
            }],
        })

        self.assertEqual(summary["final_count"], 3)
        self.assertEqual(summary["far_range"], [101.5, 101.5])
        self.assertEqual(summary["law_graph_evidence_hashes"], ["l" * 64])
        self.assertTrue(summary["final_geometry_hash_agreement"])
        self.assertEqual(
            summary["png_paths"],
            ["program.png", "summary.png"],
        )

    def test_portfolio_render_evidence_exposes_final_hash_alias(self):
        from design.maas.book_language.portfolio_benchmark import (
            _archive_render_evidence,
        )

        final_hash = "f" * 64
        with TemporaryDirectory() as directory:
            board = Path(directory) / "board.png"
            Image.new("RGB", (32, 32), "black").save(board)
            evidence = _archive_render_evidence(
                board,
                1,
                projected_visual_hashes=[final_hash],
            )[0]

        self.assertEqual(evidence["projected_visual_geometry_hash"], final_hash)
        self.assertEqual(evidence["final_legal_geometry_hash"], final_hash)

    def test_diagnostic_target_bounds_generation_axes_without_changing_defaults(self):
        from design.maas.book_language.portfolio_benchmark import (
            diagnostic_generation_budget,
        )

        self.assertIsNone(diagnostic_generation_budget(None))
        budget = diagnostic_generation_budget(3)

        self.assertEqual(budget["scope_labels"], ("1/1", "3/8", "1/2"))
        self.assertEqual(budget["parent_variant_indices"], (0,))
        self.assertEqual(budget["book_probe_count"], 1)
        self.assertEqual(budget["evaluation_cap"], 36)
        self.assertEqual(budget["candidate_cap"], 12)
        self.assertEqual(budget["replenishment_cycle_cap"], 1)

    def test_diagnostic_target_five_searches_all_book_scopes_with_bounded_budget(self):
        from design.maas.book_language.portfolio_benchmark import (
            diagnostic_generation_budget,
        )

        budget = diagnostic_generation_budget(5)

        self.assertEqual(
            budget["scope_labels"],
            ("1/1", "3/8", "1/2", "1/4", "1/8", "1/16"),
        )
        self.assertEqual(budget["parent_variant_indices"], (0,))
        self.assertEqual(budget["book_probe_count"], 1)
        self.assertEqual(budget["evaluation_cap"], 60)
        self.assertEqual(budget["candidate_cap"], 20)
        self.assertEqual(budget["replenishment_cycle_cap"], 1)

    def test_diagnostic_generation_progress_persists_evaluated_and_compiled_counts(self):
        from design.maas.book_language.portfolio_benchmark import (
            persist_diagnostic_generation_progress,
        )

        with TemporaryDirectory() as directory:
            state_path = persist_diagnostic_generation_progress(
                Path(directory),
                program="neighborhood",
                target=3,
                counters={
                    "evaluated_count": 7,
                    "compiled_count": 4,
                    "program_passed_count": 2,
                },
            )
            state = __import__("json").loads(
                state_path.read_text(encoding="utf-8")
            )

        self.assertEqual(state["phase"], "candidate_generation")
        self.assertEqual(state["program"], "neighborhood")
        self.assertEqual(state["diagnostic_target"], 3)
        self.assertEqual(state["evaluated_count"], 7)
        self.assertEqual(state["compiled_count"], 4)
        self.assertEqual(state["program_passed_count"], 2)

    def test_diagnostic_generation_budget_supports_twenty(self):
        from design.maas.book_language.portfolio_benchmark import (
            diagnostic_generation_budget,
        )

        budget = diagnostic_generation_budget(20)

        self.assertEqual(
            budget["scope_labels"],
            tuple(("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")),
        )
        self.assertEqual(budget["parent_variant_indices"], (0, 1))
        self.assertEqual(budget["book_probe_count"], 1)
        self.assertEqual(budget["evaluation_cap"], 240)
        self.assertEqual(budget["candidate_cap"], 80)
        self.assertEqual(budget["replenishment_cycle_cap"], 2)

    def _task3_floorwise_gym_sources(self):
        from design.maas.grammar.component_graph import graph_from_sequence
        from design.maas.program_massing import program_seed_sequences
        canonical_graph = graph_from_sequence(
            program_seed_sequences("gymnasium")[0]
        ).to_dict()
        authored = SourceMass(
            name="task3_authored_gym",
            footprint=box(0.0, 0.0, 10.0, 10.0),
            volumes=(
                SourceVolume(
                    "gym_main_long_span_hall",
                    box(0.0, 0.0, 10.0, 10.0),
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
            metadata={"component_graph": canonical_graph},
        )
        from design.maas.geometry_language import (
            GeometryProgramBuilder,
            compile_geometry_program,
        )
        from design.maas.program_massing.semantic_carriers import (
            bind_source_role_scaffold_to_program,
        )
        builder = GeometryProgramBuilder("task3_semantic_origin_fixture")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 10.0, "depth": 10.0, "height": 1.0},
            semantic_role="main",
        )
        final_program = bind_source_role_scaffold_to_program(
            builder.build(root),
            authored,
            program_id="gymnasium",
        )
        self.assertIsNotNone(final_program)
        final_compilation = compile_geometry_program(final_program)
        self.assertEqual(final_compilation.status, "compiled")
        self._task3_final_program_hash = final_program.program_hash()
        self._task3_final_geometry_hash = final_compilation.geometry_hash
        surfaces = tuple(
            SourceSurface(
                role=f"final_surface_{index}",
                volume_role="gym_main_long_span_hall",
                verb="geometry_program",
                surface_type="profiled_recursive_solid_mesh",
                vertices_m=tuple(
                    (
                        float(final_compilation.vertices[vertex_index][0])
                        - 5.0,
                        float(final_compilation.vertices[vertex_index][1])
                        - 5.0,
                        float(final_compilation.vertices[vertex_index][2]),
                    )
                    for vertex_index in triangle
                ),
                operator="union",
                semantic_patch_id=f"final:{index}",
            )
            for index, triangle in enumerate(final_compilation.triangles)
        )
        from design.maas.geometry_language.source_bridge import (
            source_surface_payload_hash,
        )
        surface_hash = source_surface_payload_hash(surfaces)
        final = SourceMass(
            name="task3_final_floorwise_gym",
            footprint=box(0.0, 0.0, 10.0, 10.0),
            volumes=(
                SourceVolume(
                    "gym_main_long_span_hall",
                    box(0.0, 0.0, 10.0, 10.0),
                    0.0,
                    0.5,
                    "geometry_program",
                ),
                SourceVolume(
                    "gym_main_long_span_hall",
                    box(0.0, 0.0, 10.0, 10.0),
                    0.5,
                    1.0,
                    "geometry_program",
                ),
            ),
            surfaces=surfaces,
            metadata={
                "geometry_authority": "authored_projected_surface_payload",
                "legal_proxy_role": "analysis_only_gfa_parking_containment",
                "floorwise_visual_replay_allowed": False,
                "geometry_program_bridge_evidence": {
                    "program_hash": self._task3_final_program_hash,
                    "geometry_hash": self._task3_final_geometry_hash,
                    "surface_payload_hash": surface_hash,
                    "surface_export_complete": True,
                    "raw_mesh_triangle_count": len(surfaces),
                    "exported_surface_count": len(surfaces),
                },
                "geometry_program": final_program.to_dict(),
                "final_program_hash": self._task3_final_program_hash,
                "final_geometry_hash": self._task3_final_geometry_hash,
                "final_surface_payload_hash": surface_hash,
                "coherence_evidence": {
                    "hard_pass": True,
                    "score": 1.0,
                },
                "shared_floor_contract": {
                    "schema_version": "arr.maas.shared_floor_contract.v1",
                    "floor_contract_hash": "task3-floor-contract",
                    "floor_capacity_plan_hash": "floor-plan-1",
                    "hard_pass": True,
                    "failure_reasons": [],
                },
                "final_semantic_projection_context": {
                    "floor_capacity_plan_hash": "floor-plan-1",
                    "pnu": "1168011800104170004",
                    "site_context_hash": "site-1",
                    "capacity_alternative_id": "spatial_reserve",
                    "achieved_capacity_band": "spatial_reserve",
                    "capacity_measurement_hash": "m" * 64,
                },
            },
        )
        return authored, final

    def _task3_floorwise_gym_feature(self, final):
        return {
            "type": "Feature",
            "geometry": mapping(final.footprint),
            "properties": {
                "benchmark_site_area_m2": 130.0,
                "source_signature": final.signature(),
                "mass_volumes": [
                    {
                        "geometry": mapping(volume.footprint),
                        "bottom_height": 10.0 * volume.bottom_fraction,
                        "top_height": 10.0 * volume.top_fraction,
                        "role": volume.role,
                    }
                    for volume in final.volumes
                ],
            },
        }

    def _task3_semantic_projection_kwargs(self):
        return {
            "program_id": "gymnasium",
            "final_program_hash": self._task3_final_program_hash,
            "final_geometry_hash": self._task3_final_geometry_hash,
            "floor_capacity_plan_hash": "floor-plan-1",
            "pnu": "1168011800104170004",
            "site_context_hash": "site-1",
            "capacity_alternative_id": "spatial_reserve",
            "achieved_capacity_band": "spatial_reserve",
            "capacity_measurement_hash": "m" * 64,
        }

    def _task3_below_capacity_semantic_source(self):
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
            rebind_semantic_projection_capacity,
        )

        authored, final = self._task3_floorwise_gym_sources()
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )
        evidence = rebind_semantic_projection_capacity(
            evidence,
            achieved_capacity_band="",
            capacity_measurement_hash="u" * 64,
        )
        context = {
            **final.metadata["final_semantic_projection_context"],
            "achieved_capacity_band": "",
            "capacity_measurement_hash": "u" * 64,
        }
        metadata = {
            **final.metadata,
            "program_semantic_carrier_evidence": evidence,
            "final_semantic_projection_context": context,
            "source_capacity_measurement": {
                "hard_pass": False,
                "feasible_capacity_utilization": 0.60,
            },
            "capacity_alternative_projection": {
                "alternative_id": "spatial_reserve",
                "target_hard_pass": False,
                "selectable_capacity_hard_pass": False,
                "selectable_capacity_alternative_id": "",
            },
        }
        return SourceMass(
            name=final.name,
            footprint=final.footprint,
            volumes=final.volumes,
            surfaces=final.surfaces,
            metadata=metadata,
        )

    def test_spatial_carriers_remain_geometry_verified_below_capacity_without_downstream_bypass(self):
        from design.maas.program_massing.semantic_carriers import (
            audit_source_semantic_projection,
        )
        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )

        source = self._task3_below_capacity_semantic_source()
        spatial = attach_program_spatial_evidence(
            self._task3_floorwise_gym_feature(source),
            building_type="gymnasium",
            site_area_m2=130.0,
        )
        downstream = audit_source_semantic_projection(
            source,
            building_type="gymnasium",
            expected_context={
                **self._task3_semantic_projection_kwargs(),
                "achieved_capacity_band": "",
                "capacity_measurement_hash": "u" * 64,
            },
        )

        self.assertTrue(
            spatial["semantic_carrier_audit"]["hard_pass"],
            spatial["semantic_carrier_audit"],
        )
        self.assertEqual(
            spatial["semantic_carrier_audit"]["schema_version"],
            "arr.maas.final_semantic_geometry_audit.v1",
        )
        self.assertGreater(spatial["verified_semantic_carrier_count"], 0)
        self.assertGreaterEqual(spatial["dominant_ratio_score"], 0.55)
        self.assertTrue(spatial["hard_pass"], spatial)
        self.assertFalse(
            source.metadata["source_capacity_measurement"]["hard_pass"]
        )
        self.assertFalse(
            source.metadata["capacity_alternative_projection"][
                "selectable_capacity_hard_pass"
            ]
        )
        self.assertFalse(downstream["hard_pass"], downstream)
        self.assertIn(
            "achieved_capacity_band_mismatch",
            downstream["failures"],
        )

    def test_below_capacity_spatial_geometry_audit_rejects_program_geometry_surface_and_carrier_tamper(self):
        from design.maas.program_massing.semantic_carriers import (
            canonical_semantic_carrier_payload_hash,
        )
        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )

        source = self._task3_below_capacity_semantic_source()
        cases = []

        program_metadata = deepcopy(source.metadata)
        program_metadata["geometry_program_bridge_evidence"][
            "program_hash"
        ] = "x" * 64
        cases.append(("program", source.surfaces, program_metadata))

        geometry_metadata = deepcopy(source.metadata)
        geometry_metadata["geometry_program_bridge_evidence"][
            "geometry_hash"
        ] = "y" * 64
        cases.append(("geometry", source.surfaces, geometry_metadata))

        changed_surfaces = (
            replace(
                source.surfaces[0],
                vertices_m=(
                    (0.0, 0.0, 0.0),
                    (9.5, 0.0, 0.0),
                    (0.0, 10.0, 0.0),
                ),
            ),
            *source.surfaces[1:],
        )
        cases.append(("surface", changed_surfaces, deepcopy(source.metadata)))

        carrier_metadata = deepcopy(source.metadata)
        carrier_evidence = carrier_metadata[
            "program_semantic_carrier_evidence"
        ]
        carrier_evidence["carriers"][0]["final_polygon_utm"] = mapping(
            box(100.0, 100.0, 101.0, 101.0)
        )
        carrier_evidence["carriers"][0]["measured_area_m2"] = 1.0
        carrier_evidence["carrier_payload_hash"] = (
            canonical_semantic_carrier_payload_hash(
                carrier_evidence["carriers"]
            )
        )
        cases.append(("carrier", source.surfaces, carrier_metadata))

        semantic_hash_metadata = deepcopy(source.metadata)
        semantic_hash_metadata["program_semantic_carrier_evidence"][
            "semantic_projection_hash"
        ] = "0" * 64
        cases.append((
            "semantic_projection_hash",
            source.surfaces,
            semantic_hash_metadata,
        ))

        for label, surfaces, metadata in cases:
            with self.subTest(label=label):
                tampered = SourceMass(
                    name=source.name,
                    footprint=source.footprint,
                    volumes=source.volumes,
                    surfaces=surfaces,
                    metadata=metadata,
                )
                spatial = attach_program_spatial_evidence(
                    self._task3_floorwise_gym_feature(tampered),
                    building_type="gymnasium",
                    site_area_m2=130.0,
                )

                self.assertFalse(
                    spatial["semantic_carrier_audit"]["hard_pass"],
                    spatial["semantic_carrier_audit"],
                )
                self.assertNotIn(
                    "achieved_capacity_band_mismatch",
                    spatial["semantic_carrier_audit"]["failures"],
                )
                self.assertEqual(
                    spatial["verified_semantic_carrier_count"],
                    0,
                )
                self.assertFalse(spatial["hard_pass"], spatial)

    def test_final_semantic_projection_preserves_seed_roles_on_same_hash_solid(self):
        from design.maas.program_massing.semantic_carriers import (
            audit_source_semantic_projection,
            build_program_semantic_carrier_evidence,
        )
        from design.maas.preference.loop import (
            feature_preview_png,
            _require_certified_authored_visual,
        )
        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        geometry_before = [
            volume.signature() for volume in final.volumes
        ]
        surfaces_before = [
            surface.signature() for surface in final.surfaces
        ]
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )
        final = SourceMass(
            name=final.name,
            footprint=final.footprint,
            volumes=final.volumes,
            surfaces=final.surfaces,
            metadata={
                **final.metadata,
                "program_semantic_carrier_evidence": evidence,
            },
        )

        spatial = attach_program_spatial_evidence(
            self._task3_floorwise_gym_feature(final),
            building_type="gymnasium",
            site_area_m2=130.0,
        )

        self.assertTrue(evidence["hard_pass"], evidence)
        self.assertTrue(evidence["all_carriers_contained"])
        self.assertTrue(evidence["all_carriers_disjoint"])
        self.assertTrue(all(
            carrier["measured_area_m2"] > 0.0
            and carrier["final_polygon_utm"]
            for carrier in evidence["carriers"]
        ))
        self.assertEqual(spatial["geometric_dominant_component_ratio"], 1.0)
        self.assertGreaterEqual(spatial["dominant_ratio_score"], 0.55)
        self.assertEqual(spatial["required_role_hits"], [True, True, True])
        self.assertTrue(spatial["semantic_carrier_audit"]["hard_pass"])
        self.assertTrue(spatial["hard_pass"], spatial)
        self.assertEqual(
            [volume.signature() for volume in final.volumes],
            geometry_before,
        )
        self.assertEqual(
            [surface.signature() for surface in final.surfaces],
            surfaces_before,
        )

    def test_task3_semantic_carriers_reject_hash_center_and_empty_tampering(self):
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
            canonical_semantic_carrier_payload_hash,
        )
        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        valid = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )
        tampered_cases = []
        bad_hash = deepcopy(valid)
        bad_hash["carrier_payload_hash"] = "0" * 64
        tampered_cases.append(("payload_hash", bad_hash))
        outside = deepcopy(valid)
        outside["carriers"][0]["final_polygon_utm"] = mapping(
            box(100.0, 100.0, 101.0, 101.0)
        )
        outside["carriers"][0]["measured_area_m2"] = 1.0
        outside["carrier_payload_hash"] = canonical_semantic_carrier_payload_hash(
            outside["carriers"]
        )
        tampered_cases.append(("outside_polygon", outside))
        empty = deepcopy(valid)
        empty["carriers"] = []
        empty["carrier_payload_hash"] = canonical_semantic_carrier_payload_hash([])
        tampered_cases.append(("empty_carriers", empty))

        for label, evidence in tampered_cases:
            with self.subTest(label=label):
                invalid = SourceMass(
                    name=final.name,
                    footprint=final.footprint,
                    volumes=final.volumes,
                    surfaces=final.surfaces,
                    metadata={
                        **final.metadata,
                        "program_semantic_carrier_evidence": evidence,
                    },
                )
                spatial = attach_program_spatial_evidence(
                    self._task3_floorwise_gym_feature(invalid),
                    building_type="gymnasium",
                    site_area_m2=130.0,
                )
                self.assertFalse(spatial["semantic_carrier_audit"]["hard_pass"])
                self.assertFalse(all(spatial["required_role_hits"]))
                self.assertFalse(spatial["hard_pass"])

    def test_task3_semantic_carriers_reject_final_geometry_hash_mismatch(self):
        from design.maas.program_massing.semantic_carriers import (
            audit_source_semantic_projection,
            build_program_semantic_carrier_evidence,
        )
        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **{
                **self._task3_semantic_projection_kwargs(),
                "final_geometry_hash": "h" * 64,
            },
        )
        invalid = SourceMass(
            name=final.name,
            footprint=final.footprint,
            volumes=final.volumes,
            surfaces=final.surfaces,
            metadata={
                **final.metadata,
                "program_semantic_carrier_evidence": evidence,
            },
        )

        spatial = attach_program_spatial_evidence(
            self._task3_floorwise_gym_feature(invalid),
            building_type="gymnasium",
            site_area_m2=130.0,
        )

        self.assertFalse(spatial["semantic_carrier_audit"]["hard_pass"])
        self.assertIn(
            "final_geometry_hash_mismatch",
            spatial["semantic_carrier_audit"]["failures"],
        )
        self.assertFalse(spatial["hard_pass"])

    def test_stale_upstream_program_space_zones_are_rejected(self):
        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )

        _authored, final = self._task3_floorwise_gym_sources()
        stale = SourceMass(
            name=final.name,
            footprint=final.footprint,
            volumes=final.volumes,
            surfaces=final.surfaces,
            metadata={
                **final.metadata,
                "program_space_zones": [
                    {"role": "gym_service_spine", "plan_area_ratio": 0.2},
                    {"role": "gym_entry_canopy", "plan_area_ratio": 0.15},
                ],
            },
        )

        spatial = attach_program_spatial_evidence(
            self._task3_floorwise_gym_feature(stale),
            building_type="gymnasium",
            site_area_m2=130.0,
        )

        self.assertFalse(spatial["semantic_carrier_audit"]["hard_pass"])
        self.assertEqual(spatial["required_role_hits"], [True, False, False])
        self.assertLess(spatial["dominant_ratio_score"], 0.55)
        self.assertFalse(spatial["hard_pass"])

    def test_semantic_projection_rejects_final_geometry_surface_or_program_tamper(self):
        from dataclasses import replace
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
        )
        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )
        cases = []
        program_tamper = deepcopy(final.metadata)
        program_tamper["geometry_program_bridge_evidence"]["program_hash"] = "x" * 64
        cases.append(("program", final.surfaces, program_tamper))
        geometry_tamper = deepcopy(final.metadata)
        geometry_tamper["geometry_program_bridge_evidence"]["geometry_hash"] = "y" * 64
        cases.append(("geometry", final.surfaces, geometry_tamper))
        changed_surface = (
            replace(
                final.surfaces[0],
                vertices_m=((0.0, 0.0, 0.0), (9.5, 0.0, 0.0), (0.0, 10.0, 0.0)),
            ),
            *final.surfaces[1:],
        )
        cases.append(("surface", changed_surface, deepcopy(final.metadata)))

        for label, surfaces, metadata in cases:
            with self.subTest(label=label):
                tampered = SourceMass(
                    name=final.name,
                    footprint=final.footprint,
                    volumes=final.volumes,
                    surfaces=surfaces,
                    metadata={
                        **metadata,
                        "program_semantic_carrier_evidence": evidence,
                    },
                )
                spatial = attach_program_spatial_evidence(
                    self._task3_floorwise_gym_feature(tampered),
                    building_type="gymnasium",
                    site_area_m2=130.0,
                )
                self.assertFalse(spatial["semantic_carrier_audit"]["hard_pass"])
                self.assertFalse(spatial["hard_pass"])

    def test_semantic_projection_rejects_role_string_spoof(self):
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
        )
        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )

        _authored, final = self._task3_floorwise_gym_sources()
        spoofed = SourceMass(
            name="spoofed_authored_gym",
            footprint=box(0.0, 0.0, 10.0, 10.0),
            volumes=(
                SourceVolume(
                    "fake_main_hall",
                    box(0.0, 0.0, 10.0, 10.0),
                    0.0,
                    1.0,
                    "geometry_program",
                ),
                SourceVolume(
                    "fake_service",
                    box(1.0, 4.0, 3.0, 6.0),
                    0.0,
                    0.5,
                    "attach",
                ),
                SourceVolume(
                    "fake_entry",
                    box(7.0, 4.0, 8.5, 6.0),
                    0.0,
                    0.5,
                    "attach",
                ),
            ),
        )
        evidence = build_program_semantic_carrier_evidence(
            spoofed,
            final,
            **self._task3_semantic_projection_kwargs(),
        )
        projected = SourceMass(
            name=final.name,
            footprint=final.footprint,
            volumes=final.volumes,
            surfaces=final.surfaces,
            metadata={
                **final.metadata,
                "program_semantic_carrier_evidence": evidence,
            },
        )

        spatial = attach_program_spatial_evidence(
            self._task3_floorwise_gym_feature(projected),
            building_type="gymnasium",
            site_area_m2=130.0,
        )

        self.assertFalse(spatial["semantic_carrier_audit"]["hard_pass"])
        self.assertLess(sum(spatial["required_role_hits"]), 3)
        self.assertFalse(spatial["hard_pass"])

    def test_semantic_projection_rejects_copied_graph_without_reachable_ast_origin(self):
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        copied = SourceMass(
            name="copied_canonical_metadata_and_roles",
            footprint=authored.footprint,
            volumes=authored.volumes,
            metadata={
                "component_graph": deepcopy(
                    authored.metadata["component_graph"]
                ),
            },
        )
        unbound_metadata = deepcopy(final.metadata)
        unbound_metadata.pop("geometry_program", None)
        unbound_final = SourceMass(
            name=final.name,
            footprint=final.footprint,
            volumes=final.volumes,
            surfaces=final.surfaces,
            metadata=unbound_metadata,
        )
        evidence = build_program_semantic_carrier_evidence(
            copied,
            unbound_final,
            **self._task3_semantic_projection_kwargs(),
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn(
            "source_role_scaffold_not_bound_to_reachable_final_ast",
            evidence["failures"],
        )

    def test_downstream_combined_gate_rejects_missing_stale_or_tampered_semantics(self):
        from design.maas.book_language.downstream_hard_gate import (
            _evaluate_candidate,
        )
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )
        cases = []
        missing = deepcopy(final.metadata)
        cases.append(("missing", missing))
        stale = deepcopy(final.metadata)
        stale["program_space_zones"] = [
            {"role": "gym_service_spine", "plan_area_ratio": 0.2},
            {"role": "gym_entry_canopy", "plan_area_ratio": 0.15},
        ]
        cases.append(("stale", stale))
        tampered = deepcopy(final.metadata)
        bad_evidence = deepcopy(evidence)
        bad_evidence["semantic_projection_hash"] = "0" * 64
        tampered["program_semantic_carrier_evidence"] = bad_evidence
        cases.append(("tampered", tampered))
        replayed = deepcopy(final.metadata)
        replayed_context = {
            **replayed["final_semantic_projection_context"],
            "pnu": "OTHER-PNU",
            "site_context_hash": "OTHER-SITE",
            "floor_capacity_plan_hash": "OTHER-PLAN",
            "achieved_capacity_band": "maximum_feasible",
            "capacity_measurement_hash": "r" * 64,
        }
        replayed_evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **{
                **self._task3_semantic_projection_kwargs(),
                **replayed_context,
            },
        )
        replayed["final_semantic_projection_context"] = replayed_context
        replayed["program_semantic_carrier_evidence"] = replayed_evidence
        cases.append(("self_consistent_external_replay", replayed))
        envelope = SimpleNamespace(
            buildable_footprint=box(-1.0, -1.0, 11.0, 11.0),
            bcr_limit=100.0,
            far_limit=1000.0,
            height_limit=30.0,
            outputs_def=[],
        )
        for label, metadata in cases:
            with self.subTest(label=label):
                source = SourceMass(
                    name=final.name,
                    footprint=final.footprint,
                    volumes=final.volumes,
                    surfaces=final.surfaces,
                    metadata=metadata,
                )
                candidate = SimpleNamespace(
                    source=source,
                    feature={"properties": {"variant_id": label}},
                    sequence=SimpleNamespace(name=f"{label}-sequence"),
                    principle_id="book:test",
                )
                with (
                    patch(
                        "design.maas.book_language.downstream_hard_gate._final_source_geometry_identity",
                        return_value=("g" * 64, [], "g" * 64, source.signature()["actual_surface_payload_hash"], True),
                    ),
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
                        site_local_utm=envelope.buildable_footprint,
                        envelope=envelope,
                        sunlight_ring=[],
                        pnu="1168011800104170004",
                        building_type="gymnasium",
                        height_m=10.0,
                        floors=2,
                        rules={},
                        parking_options={},
                    )

                self.assertTrue(row["legal_projection"]["hard_pass"])
                self.assertTrue(row["parking_hard_gate"]["hard_pass"])
                self.assertFalse(
                    row["semantic_projection_hard_gate"]["hard_pass"]
                )
                self.assertFalse(row["combined_hard_pass"])

    def test_semantic_projection_uses_measured_disjoint_area(self):
        from shapely.geometry import shape
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )

        self.assertTrue(evidence["all_carriers_disjoint"], evidence)
        for floor_index in {item["floor_index"] for item in evidence["carriers"]}:
            carriers = [
                shape(item["final_polygon_utm"])
                for item in evidence["carriers"]
                if item["floor_index"] == floor_index
            ]
            measured_sum = sum(item.area for item in carriers)
            host_area = final.volumes[floor_index].footprint.area
            self.assertLessEqual(measured_sum, host_area + 1e-7)
            for index, carrier in enumerate(carriers):
                self.assertTrue(final.volumes[floor_index].footprint.covers(carrier))
                for other in carriers[index + 1:]:
                    self.assertLessEqual(carrier.intersection(other).area, 1e-9)

    def test_required_carrier_projection_empty_rejects_candidate(self):
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
        )

        _authored, final = self._task3_floorwise_gym_sources()
        outside = SourceMass(
            name="outside_authored_gym",
            footprint=box(0.0, 0.0, 10.0, 10.0),
            volumes=(
                SourceVolume(
                    "gym_main_long_span_hall",
                    box(0.0, 0.0, 10.0, 10.0),
                    0.0,
                    1.0,
                    "geometry_program",
                ),
                SourceVolume(
                    "gym_service_spine",
                    box(40.0, 40.0, 42.0, 42.0),
                    0.0,
                    0.5,
                    "attach",
                ),
                SourceVolume(
                    "gym_entry_canopy",
                    box(50.0, 50.0, 52.0, 52.0),
                    0.0,
                    0.5,
                    "attach",
                ),
            ),
        )

        evidence = build_program_semantic_carrier_evidence(
            outside,
            final,
            **self._task3_semantic_projection_kwargs(),
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertTrue(any(
            "empty" in failure or "outside" in failure
            for failure in evidence["failures"]
        ))

    def test_spatial_geometry_rejects_plan_pnu_site_and_requested_alternative_context_tamper(self):
        from design.maas.program_massing.semantic_carriers import (
            audit_source_semantic_projection,
            build_program_semantic_carrier_evidence,
        )
        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )
        for key, value in (
            ("floor_capacity_plan_hash", "floor-plan-replay"),
            ("pnu", "1168011800104670003"),
            ("site_context_hash", "site-replay"),
            ("capacity_alternative_id", "maximum"),
        ):
            with self.subTest(key=key):
                context = {
                    **final.metadata["final_semantic_projection_context"],
                    key: value,
                }
                replayed = SourceMass(
                    name=final.name,
                    footprint=final.footprint,
                    volumes=final.volumes,
                    surfaces=final.surfaces,
                    metadata={
                        **final.metadata,
                        "final_semantic_projection_context": context,
                        "program_semantic_carrier_evidence": evidence,
                    },
                )
                spatial = attach_program_spatial_evidence(
                    self._task3_floorwise_gym_feature(replayed),
                    building_type="gymnasium",
                    site_area_m2=130.0,
                )
                downstream = audit_source_semantic_projection(
                    replayed,
                    building_type="gymnasium",
                    expected_context=context,
                )
                self.assertFalse(
                    spatial["semantic_carrier_audit"]["hard_pass"],
                    spatial["semantic_carrier_audit"],
                )
                self.assertFalse(spatial["hard_pass"], spatial)
                self.assertIn(
                    f"{key}_mismatch",
                    spatial["semantic_carrier_audit"]["failures"],
                )
                self.assertFalse(downstream["hard_pass"], downstream)
                self.assertIn(f"{key}_mismatch", downstream["failures"])

    def test_spatial_geometry_ignores_only_achieved_capacity_result_context_mismatch(self):
        from design.maas.program_massing.semantic_carriers import (
            audit_source_semantic_projection,
            build_program_semantic_carrier_evidence,
        )
        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )
        for key, value in (
            ("achieved_capacity_band", "maximum_feasible"),
            ("capacity_measurement_hash", "z" * 64),
        ):
            with self.subTest(key=key):
                context = {
                    **final.metadata["final_semantic_projection_context"],
                    key: value,
                }
                replayed = SourceMass(
                    name=final.name,
                    footprint=final.footprint,
                    volumes=final.volumes,
                    surfaces=final.surfaces,
                    metadata={
                        **final.metadata,
                        "final_semantic_projection_context": context,
                        "program_semantic_carrier_evidence": evidence,
                    },
                )
                spatial = attach_program_spatial_evidence(
                    self._task3_floorwise_gym_feature(replayed),
                    building_type="gymnasium",
                    site_area_m2=130.0,
                )
                downstream = audit_source_semantic_projection(
                    replayed,
                    building_type="gymnasium",
                    expected_context=context,
                )
                self.assertTrue(
                    spatial["semantic_carrier_audit"]["hard_pass"],
                    spatial["semantic_carrier_audit"],
                )
                self.assertTrue(spatial["hard_pass"], spatial)
                self.assertFalse(downstream["hard_pass"], downstream)
                self.assertIn(f"{key}_mismatch", downstream["failures"])

    def test_semantic_projection_rejects_self_consistent_empty_surface_payload(self):
        from design.maas.geometry_language.source_bridge import (
            source_surface_payload_hash,
        )
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        empty_hash = source_surface_payload_hash(())
        metadata = deepcopy(final.metadata)
        metadata["geometry_program_bridge_evidence"]["surface_payload_hash"] = empty_hash
        metadata["geometry_program_bridge_evidence"]["surface_export_complete"] = True
        metadata["geometry_program_bridge_evidence"]["raw_mesh_triangle_count"] = 0
        metadata["geometry_program_bridge_evidence"]["exported_surface_count"] = 0
        metadata["final_surface_payload_hash"] = empty_hash
        empty = SourceMass(
            name=final.name,
            footprint=final.footprint,
            volumes=final.volumes,
            surfaces=(),
            metadata=metadata,
        )

        evidence = build_program_semantic_carrier_evidence(
            authored,
            empty,
            **self._task3_semantic_projection_kwargs(),
        )

        self.assertFalse(evidence["hard_pass"])
        self.assertIn("final_surface_payload_incomplete", evidence["failures"])

    def test_semantic_projection_binds_achieved_capacity_measurement(self):
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )

        self.assertEqual(evidence["achieved_capacity_band"], "spatial_reserve")
        self.assertEqual(evidence["capacity_measurement_hash"], "m" * 64)
        changed = build_program_semantic_carrier_evidence(
            authored,
            final,
            **{
                **self._task3_semantic_projection_kwargs(),
                "achieved_capacity_band": "maximum_feasible",
                "capacity_measurement_hash": "z" * 64,
            },
        )
        self.assertNotEqual(
            evidence["semantic_projection_hash"],
            changed["semantic_projection_hash"],
        )

    def test_in_scope_missing_or_changed_final_authority_is_never_not_required(self):
        from design.maas.program_massing.semantic_carriers import (
            audit_source_semantic_projection,
        )

        authored, final = self._task3_floorwise_gym_sources()
        for authority in ("", "site_bound_geometry_program"):
            with self.subTest(authority=authority):
                source = SourceMass(
                    name=authored.name,
                    footprint=authored.footprint,
                    volumes=authored.volumes,
                    surfaces=final.surfaces,
                    metadata={
                        **final.metadata,
                        "geometry_authority": authority,
                    },
                )
                audit = audit_source_semantic_projection(
                    source,
                    building_type="gymnasium",
                    expected_context={
                        **self._task3_semantic_projection_kwargs(),
                    },
                )
                self.assertFalse(audit["hard_pass"])
                self.assertNotEqual(audit.get("status"), "not_required")
                self.assertIn(
                    "authored_surface_geometry_authority_required",
                    audit["failures"],
                )

    def test_capacity_resolution_names_below_minimum_without_approving_it(self):
        from design.maas.book_language.mass_passport_bridge import (
            resolve_capacity_band_evidence,
        )

        resolution = resolve_capacity_band_evidence(
            {
                "requested_capacity_alternative_id": "balanced_yield",
                "selectable_capacity_alternative_id": "",
                "selectable_capacity_target_utilization": 0.0,
                "selectable_capacity_hard_pass": False,
                "feasible_minimum_utilization": 0.70,
            },
            capacity_measurement={
                "feasible_capacity_utilization": 0.44,
                "hard_pass": False,
            },
        )

        self.assertEqual(
            resolution["resolved_capacity_alternative_id"],
            "below_feasible_minimum",
        )
        self.assertFalse(resolution["resolved_capacity_hard_pass"])

    def test_downstream_candidate_accepts_explicit_generation_site_identity(self):
        from dataclasses import replace
        from design.maas.book_language.downstream_hard_gate import (
            _evaluate_candidate,
        )
        from design.maas.book_language.mass_passport_bridge import (
            resolve_capacity_band_evidence,
        )
        from design.maas.geometry_language.source_bridge import (
            source_surface_payload_hash,
        )
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
            semantic_capacity_measurement_hash,
            semantic_site_context_hash,
        )

        authored, final = self._task3_floorwise_gym_sources()
        parcel = box(-5.0, -5.0, 15.0, 15.0)
        generation_site = box(-1.0, -1.0, 11.0, 11.0)
        surfaces = tuple(
            replace(surface, surface_type="triangle_mesh")
            for surface in final.surfaces
        )
        surface_hash = source_surface_payload_hash(surfaces)
        projection = {
            "alternative_id": "spatial_reserve",
            "target_utilization": 0.8,
            "target_hard_pass": True,
        }
        measurement = {"utilization_ratio": 0.8}
        resolution = resolve_capacity_band_evidence(
            projection,
            capacity_measurement=measurement,
        )
        context = {
            "floor_capacity_plan_hash": "floor-plan-1",
            "pnu": "1168011800104170004",
            "site_context_hash": semantic_site_context_hash(
                pnu="1168011800104170004",
                building_type="gymnasium",
                site=generation_site,
            ),
            "capacity_alternative_id": (
                resolution["requested_capacity_alternative_id"]
            ),
            "achieved_capacity_band": (
                resolution["resolved_capacity_alternative_id"]
            ),
            "capacity_measurement_hash": semantic_capacity_measurement_hash(
                measurement,
                projection,
            ),
        }
        metadata = deepcopy(final.metadata)
        metadata["geometry_program_bridge_evidence"][
            "surface_payload_hash"
        ] = surface_hash
        metadata["final_surface_payload_hash"] = surface_hash
        metadata["shared_floor_contract"] = {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "floor_contract_hash": "floor-contract-1",
            "floor_capacity_plan_hash": "floor-plan-1",
            "hard_pass": True,
            "failure_reasons": [],
        }
        metadata["capacity_alternative_projection"] = projection
        metadata["source_capacity_measurement"] = measurement
        site_bound = SourceMass(
            name=final.name,
            footprint=final.footprint,
            volumes=final.volumes,
            surfaces=surfaces,
            metadata=metadata,
        )
        evidence = build_program_semantic_carrier_evidence(
            authored,
            site_bound,
            **{
                **self._task3_semantic_projection_kwargs(),
                **context,
            },
        )
        metadata["program_semantic_carrier_evidence"] = evidence
        metadata["final_semantic_projection_context"] = context
        source = replace(site_bound, metadata=metadata)
        candidate = SimpleNamespace(
            source=source,
            feature={"properties": {"variant_id": "site-identity"}},
            sequence=SimpleNamespace(name="site-identity-sequence"),
            principle_id="book:test",
        )
        envelope = SimpleNamespace(
            buildable_footprint=generation_site,
            bcr_limit=100.0,
            far_limit=1000.0,
            height_limit=30.0,
            outputs_def=[],
        )

        def evaluate(semantic_site, *, shared_floor_contract=...):
            evaluated_source = source
            if shared_floor_contract is not ...:
                evaluated_metadata = deepcopy(source.metadata)
                if shared_floor_contract is None:
                    evaluated_metadata.pop("shared_floor_contract", None)
                else:
                    evaluated_metadata["shared_floor_contract"] = deepcopy(
                        shared_floor_contract
                    )
                evaluated_source = replace(
                    source,
                    metadata=evaluated_metadata,
                )
            evaluated_candidate = SimpleNamespace(
                source=evaluated_source,
                feature={"properties": {"variant_id": "site-identity"}},
                sequence=SimpleNamespace(name="site-identity-sequence"),
                principle_id="book:test",
            )
            with (
                patch(
                    "design.maas.book_language.downstream_hard_gate._final_source_geometry_identity",
                    return_value=(
                        self._task3_final_geometry_hash,
                        [],
                        self._task3_final_geometry_hash,
                        surface_hash,
                        True,
                    ),
                ),
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
                return _evaluate_candidate(
                    evaluated_candidate,
                    site_local_utm=parcel,
                    semantic_site_utm=semantic_site,
                    envelope=envelope,
                    sunlight_ring=[],
                    pnu="1168011800104170004",
                    building_type="gymnasium",
                    height_m=10.0,
                    floors=2,
                    rules={},
                    parking_options={},
                )

        accepted = evaluate(generation_site)
        self.assertTrue(
            accepted["semantic_projection_hard_gate"]["hard_pass"],
            accepted["semantic_projection_hard_gate"],
        )
        self.assertTrue(accepted["combined_hard_pass"], accepted)
        failed_contract = deepcopy(
            source.metadata["shared_floor_contract"]
        )
        failed_contract.update({
            "hard_pass": False,
            "failure_reasons": ["insufficient_clear_floor_depth"],
        })
        for label, contract in (
            ("false", failed_contract),
            ("missing", None),
        ):
            with self.subTest(shared_floor_contract=label):
                rejected = evaluate(
                    generation_site,
                    shared_floor_contract=contract,
                )
                self.assertFalse(
                    rejected["legal_projection"]["hard_pass"],
                    rejected,
                )
                self.assertFalse(rejected["combined_hard_pass"], rejected)
                self.assertIn(
                    (
                        "shared_floor_contract_failed"
                        if label == "false"
                        else "shared_floor_contract_missing_or_invalid"
                    ),
                    rejected["legal_projection"]["failure_reasons"],
                )
        mismatched = evaluate(parcel)
        self.assertFalse(
            mismatched["semantic_projection_hard_gate"]["hard_pass"]
        )
        self.assertIn(
            "site_context_hash_mismatch",
            mismatched["semantic_projection_hard_gate"]["failures"],
        )
        self.assertFalse(mismatched["combined_hard_pass"])

    def test_final_authority_vlm_repair_cannot_return_legacy_zone_source(self):
        from design.maas.book_language.vlm_review import (
            _final_authority_repair_requires_canonical_reprojection,
            _repair_exact_post_book_candidates_from_vlm,
        )
        from design.maas.book_language.candidate_analysis import _Candidate
        from design.maas.program_massing import program_seed_sequences

        _authored, final = self._task3_floorwise_gym_sources()
        self.assertTrue(
            _final_authority_repair_requires_canonical_reprojection(final)
        )
        legacy = SourceMass(
            name=final.name,
            footprint=final.footprint,
            volumes=final.volumes,
            metadata={
                "program_space_zones": [
                    {"role": "stale_service", "plan_area_ratio": 0.2},
                ],
            },
        )
        self.assertFalse(
            _final_authority_repair_requires_canonical_reprojection(legacy)
        )
        sequence = program_seed_sequences("gymnasium")[0]
        candidate = _Candidate(
            "book:test",
            "geometry",
            "repair",
            sequence,
            final,
            {"properties": {}},
            1.0,
        )
        with patch(
            "design.maas.book_language.vlm_review.replace_source_dominant_with_geometry_program",
            side_effect=AssertionError(
                "legacy materializer must not receive final authority"
            ),
        ):
            repaired, counts = _repair_exact_post_book_candidates_from_vlm(
                [candidate],
                {
                    "audit_records": [{
                        "source_sequence": sequence.name,
                        "hard_pass": False,
                        "geometry_edits": [{}],
                    }],
                },
                generation_site=box(0.0, 0.0, 10.0, 10.0),
                building_type="gymnasium",
                height=10.0,
                floors=2,
                generation_context=None,
                program_dimensional_context={},
                site_boundary_source="test",
                site_access_context={},
                site_access_geometry={},
                repair_budget=1,
            )
        self.assertEqual(repaired, [])
        self.assertEqual(counts["source_materialized_count"], 0)
        self.assertEqual(
            counts["failure_counts"],
            {
                "final_authority_vlm_repair_canonical_"
                "reprojection_unsupported": 1,
            },
        )
        self.assertNotIn("program_space_zones", str(counts))

    def test_final_floorwise_authority_serializes_exact_surfaces_without_legacy_visual_sibling(self):
        from design.maas.preference.loop import (
            feature_preview_png,
            _require_certified_authored_visual,
        )
        from design.maas.geometry_language.projected_visual_contract import (
            exact_triangle_payload_hash,
            serialize_certified_projected_visual,
            validate_projected_visual_artifact,
        )
        from design.maas.geometry_language.outcome_graph import (
            GeometryOutcomeGraph,
        )
        from design.maas.program_massing.semantic_carriers import (
            audit_source_semantic_projection,
            build_program_semantic_carrier_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )
        metadata = deepcopy(final.metadata)
        metadata["program_semantic_carrier_evidence"] = evidence
        metadata.pop("floorwise_visual_projection", None)
        source = replace(final, metadata=metadata)
        external_audit = audit_source_semantic_projection(
            source,
            building_type="gymnasium",
            expected_context=self._task3_semantic_projection_kwargs(),
        )

        artifact = serialize_certified_projected_visual(
            source,
            final_semantic_audit=external_audit,
        )
        artifact["identity"] = {
            "programHash": self._task3_final_program_hash,
            "geometryHash": artifact["projectedVisualGeometryHash"],
            "finalLegalGeometryHash": self._task3_final_geometry_hash,
        }
        expected_semantic_context = deepcopy(
            external_audit["audited_context"]
        )
        expected_semantic_projection_hash = evidence[
            "semantic_projection_hash"
        ]
        import hashlib
        import json

        def canonical_hash(payload):
            return hashlib.sha256(json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("utf-8")).hexdigest()

        expected_semantic_audit_payload_hash = canonical_hash(
            external_audit
        )
        validated = validate_projected_visual_artifact(
            artifact,
            expected_semantic_context=expected_semantic_context,
            expected_semantic_projection_hash=(
                expected_semantic_projection_hash
            ),
            expected_semantic_audit_payload_hash=(
                expected_semantic_audit_payload_hash
            ),
        )
        with self.assertRaisesRegex(
            ValueError,
            "external semantic anchor",
        ):
            validate_projected_visual_artifact(artifact)
        preview_properties = {
            "source_surfaces": deepcopy(
                artifact["projectedVisualMesh"]["triangles"]
            ),
            "source_signature": source.signature(),
            "geometry_artifact": artifact,
            "final_semantic_anchor": {
                "expected_semantic_context": deepcopy(
                    expected_semantic_context
                ),
                "expected_semantic_projection_hash": (
                    expected_semantic_projection_hash
                ),
                "expected_semantic_audit_payload_hash": (
                    expected_semantic_audit_payload_hash
                ),
            },
            "height": 10.0,
            "shape_name": "final-floorwise-authority-preview",
        }
        _require_certified_authored_visual(
            preview_properties,
            feature_geometry=mapping(source.footprint),
        )
        preview_feature = {
            "type": "Feature",
            "geometry": mapping(source.footprint),
            "properties": preview_properties,
        }
        with TemporaryDirectory() as directory:
            preview_path = feature_preview_png(
                preview_feature,
                Path(directory),
            )
            self.assertTrue(preview_path.exists())
            with Image.open(preview_path) as preview_image:
                self.assertGreater(preview_image.width, 0)
                self.assertGreater(preview_image.height, 0)
            graph = GeometryOutcomeGraph.load(
                Path(directory) / "outcome.json",
                pnu="test-pnu",
            )
            selected_candidate_feature = deepcopy(preview_feature)
            selected_candidate_feature["properties"].pop(
                "geometry_artifact",
                None,
            )
            selected_candidate_feature["properties"].pop(
                "final_semantic_anchor",
                None,
            )
            selected_candidate = SimpleNamespace(
                source=source,
                feature=selected_candidate_feature,
                principle_id="book:test-final-authority",
                sequence=SimpleNamespace(name="final-authority"),
            )
            graph.observe_portfolio_render(
                program_slug="gymnasium",
                candidates=[selected_candidate],
                render_features=[preview_feature],
                board_path=preview_path,
                render_evidence=[{
                    "card_index": 1,
                    "hard_pass": True,
                    "projected_visual_geometry_hash": artifact[
                        "projectedVisualGeometryHash"
                    ],
                    "final_legal_geometry_hash": artifact[
                        "finalLegalGeometryHash"
                    ],
                }],
            )
            render_observation = next(
                item
                for item in graph.to_dict()["observations"]
                if item.get("stage") == "mass_png_render"
            )
            self.assertEqual(
                render_observation["geometry_hash"],
                artifact["projectedVisualGeometryHash"],
            )
            self.assertEqual(
                render_observation["final_legal_geometry_hash"],
                artifact["finalLegalGeometryHash"],
            )
            with self.assertRaisesRegex(
                ValueError,
                "final legal render hash mismatch",
            ):
                graph.observe_portfolio_render(
                    program_slug="gymnasium",
                    candidates=[selected_candidate],
                    render_features=[preview_feature],
                    board_path=preview_path,
                    render_evidence=[{
                        "card_index": 1,
                        "hard_pass": True,
                        "projected_visual_geometry_hash": artifact[
                            "projectedVisualGeometryHash"
                        ],
                        "final_legal_geometry_hash": "0" * 64,
                    }],
                )
            aligned_render_evidence = [{
                "card_index": 1,
                "hard_pass": True,
                "projected_visual_geometry_hash": artifact[
                    "projectedVisualGeometryHash"
                ],
                "final_legal_geometry_hash": artifact[
                    "finalLegalGeometryHash"
                ],
            }]
            cardinality_cases = (
                (
                    "missing_render_feature",
                    [selected_candidate],
                    aligned_render_evidence,
                    [],
                ),
                (
                    "missing_render_evidence",
                    [selected_candidate],
                    [],
                    [preview_feature],
                ),
                (
                    "extra_render_feature",
                    [],
                    [],
                    [preview_feature],
                ),
            )
            for (
                name,
                candidates,
                evidence_records,
                rendered_features,
            ) in cardinality_cases:
                with self.subTest(render_collection_boundary=name):
                    with self.assertRaisesRegex(
                        ValueError,
                        "render observation cardinality mismatch",
                    ):
                        graph.observe_portfolio_render(
                            program_slug="gymnasium",
                            candidates=candidates,
                            render_features=rendered_features,
                            board_path=preview_path,
                            render_evidence=evidence_records,
                        )
            with self.assertRaisesRegex(
                ValueError,
                "invalid rendered feature",
            ):
                graph.observe_portfolio_render(
                    program_slug="gymnasium",
                    candidates=[selected_candidate],
                    render_features=[None],
                    board_path=preview_path,
                    render_evidence=aligned_render_evidence,
                )
            with self.assertRaisesRegex(
                ValueError,
                "render observation cardinality mismatch",
            ):
                graph.observe_portfolio_render(
                    program_slug="gymnasium",
                    candidates=[selected_candidate],
                    board_path=preview_path,
                    render_evidence=[],
                )
        tampered_feature = deepcopy(preview_feature)
        tampered_feature["properties"][
            "source_surfaces"
        ][0]["vertices_m"][0][0] += 0.125
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                ValueError,
                "authored profiled visual mesh requires certified",
            ):
                feature_preview_png(
                    tampered_feature,
                    Path(directory),
                )
        moved_feature = deepcopy(preview_feature)
        moved_feature["geometry"] = mapping(
            box(100.0, 0.0, 110.0, 10.0)
        )
        with self.subTest(adversarial="moved_feature_centroid"):
            with TemporaryDirectory() as directory:
                with self.assertRaisesRegex(
                    ValueError,
                    "authored profiled visual mesh requires certified",
                ):
                    feature_preview_png(
                        moved_feature,
                        Path(directory),
                    )

        with self.subTest(adversarial="separate_visual_and_final_hashes"):
            self.assertEqual(
                artifact["projectedVisualGeometryHash"],
                artifact["projectedVisualCertificate"]["visual_hash"],
            )
            self.assertEqual(
                artifact["finalLegalGeometryHash"],
                self._task3_final_geometry_hash,
            )
            self.assertNotEqual(
                artifact["projectedVisualGeometryHash"],
                artifact["finalLegalGeometryHash"],
            )
        self.assertEqual(
            artifact["projectedVisualCertificate"]["certification_mode"],
            "authored_projected_surface_authority",
        )
        self.assertEqual(
            artifact["projectedVisualMesh"]["coordinateSpace"],
            "source_footprint_centroid_local_xy_normalized_z",
        )
        self.assertEqual(
            artifact["projectedVisualPayloadHash"],
            exact_triangle_payload_hash(
                artifact["projectedVisualMesh"]["triangles"]
            ),
        )
        self.assertEqual(
            len(artifact["projectedVisualMesh"]["triangles"]),
            len(source.surfaces),
        )
        self.assertEqual(
            [
                triangle["vertices_m"]
                for triangle in artifact["projectedVisualMesh"]["triangles"]
            ],
            [
                [list(vertex) for vertex in surface.vertices_m]
                for surface in source.surfaces
            ],
        )
        self.assertTrue(all(
            0.0 <= float(vertex[2]) <= 1.0
            for triangle in artifact["projectedVisualMesh"]["triangles"]
            for vertex in triangle["vertices_m"]
        ))
        self.assertEqual(
            validated.visual_hash,
            artifact["projectedVisualGeometryHash"],
        )
        self.assertEqual(
            validated.coordinate_space,
            "source_footprint_centroid_local_xy_normalized_z",
        )
        self.assertEqual(len(validated.triangles), len(source.surfaces))
        self_consistent_surface_tamper = deepcopy(artifact)
        self_consistent_surface_tamper[
            "projectedVisualMesh"
        ]["triangles"][0]["vertices_m"][0][0] += 0.125
        tampered_payload_hash = exact_triangle_payload_hash(
            self_consistent_surface_tamper[
                "projectedVisualMesh"
            ]["triangles"]
        )
        self_consistent_surface_tamper[
            "projectedVisualPayloadHash"
        ] = tampered_payload_hash
        self_consistent_surface_tamper[
            "projectedVisualCertificate"
        ]["exact_surface_payload_hash"] = tampered_payload_hash
        with self.assertRaisesRegex(
            ValueError,
            "(?:projected visual mesh hash mismatch|"
            "invalid final floorwise visual authority certificate)",
        ):
            validate_projected_visual_artifact(
                self_consistent_surface_tamper,
                expected_semantic_context=expected_semantic_context,
                expected_semantic_projection_hash=(
                    expected_semantic_projection_hash
                ),
                expected_semantic_audit_payload_hash=(
                    expected_semantic_audit_payload_hash
                ),
            )
        for field in (
            "semantic_projection_hash",
            "final_surface_payload_hash",
        ):
            certificate_tamper = deepcopy(artifact)
            certificate_tamper[
                "projectedVisualCertificate"
            ][field] = "x" * 64
            with self.subTest(artifact_certificate_field=field):
                with self.assertRaisesRegex(
                    ValueError,
                    "authored projected surface authority",
                ):
                    validate_projected_visual_artifact(
                        certificate_tamper,
                        expected_semantic_context=(
                            expected_semantic_context
                        ),
                        expected_semantic_projection_hash=(
                            expected_semantic_projection_hash
                        ),
                        expected_semantic_audit_payload_hash=(
                            expected_semantic_audit_payload_hash
                        ),
                    )

        semantic_replay = deepcopy(artifact)
        replay_audit = semantic_replay["semanticProjectionAudit"]
        replay_audit["audited_context"]["pnu"] = "REPLAYED-PNU"
        replay_audit["audited_context_hash"] = canonical_hash(
            replay_audit["audited_context"]
        )
        replay_payload_hash = canonical_hash(replay_audit)
        semantic_replay[
            "semanticProjectionAuditPayloadHash"
        ] = replay_payload_hash
        semantic_replay["projectedVisualCertificate"][
            "semantic_audit_context_hash"
        ] = replay_audit["audited_context_hash"]
        semantic_replay["projectedVisualCertificate"][
            "semantic_audit_payload_hash"
        ] = replay_payload_hash
        with self.assertRaisesRegex(
            ValueError,
            "external semantic anchor",
        ):
            validate_projected_visual_artifact(
                semantic_replay,
                expected_semantic_context=expected_semantic_context,
                expected_semantic_projection_hash=(
                    expected_semantic_projection_hash
                ),
                expected_semantic_audit_payload_hash=(
                    expected_semantic_audit_payload_hash
                ),
            )
        semantic_hash_replay = deepcopy(artifact)
        semantic_hash_replay["semanticProjectionHash"] = "x" * 64
        semantic_hash_replay["projectedVisualCertificate"][
            "semantic_projection_hash"
        ] = "x" * 64
        semantic_hash_replay["semanticProjectionAudit"][
            "semantic_projection_hash"
        ] = "x" * 64
        semantic_hash_replay_hash = canonical_hash(
            semantic_hash_replay["semanticProjectionAudit"]
        )
        semantic_hash_replay[
            "semanticProjectionAuditPayloadHash"
        ] = semantic_hash_replay_hash
        semantic_hash_replay["projectedVisualCertificate"][
            "semantic_audit_payload_hash"
        ] = semantic_hash_replay_hash
        with self.assertRaisesRegex(
            ValueError,
            "external semantic anchor",
        ):
            validate_projected_visual_artifact(
                semantic_hash_replay,
                expected_semantic_context=expected_semantic_context,
                expected_semantic_projection_hash=(
                    expected_semantic_projection_hash
                ),
                expected_semantic_audit_payload_hash=(
                    expected_semantic_audit_payload_hash
                ),
            )
        carrier_replay = deepcopy(artifact)
        carrier_replay["semanticProjectionAudit"][
            "accepted_carriers"
        ][0]["measured_area_m2"] = 999999.0
        carrier_replay["semanticProjectionAudit"][
            "accepted_carriers"
        ][0]["final_polygon_utm"] = {
            "type": "Polygon",
            "coordinates": [],
        }
        carrier_replay_hash = canonical_hash(
            carrier_replay["semanticProjectionAudit"]
        )
        carrier_replay[
            "semanticProjectionAuditPayloadHash"
        ] = carrier_replay_hash
        carrier_replay["projectedVisualCertificate"][
            "semantic_audit_payload_hash"
        ] = carrier_replay_hash
        with self.assertRaisesRegex(
            ValueError,
            "external semantic anchor",
        ):
            validate_projected_visual_artifact(
                carrier_replay,
                expected_semantic_context=expected_semantic_context,
                expected_semantic_projection_hash=(
                    expected_semantic_projection_hash
                ),
                expected_semantic_audit_payload_hash=(
                    expected_semantic_audit_payload_hash
                ),
            )

    def test_final_floorwise_visual_serialization_rejects_identity_surface_or_semantic_tamper(self):
        from design.maas.geometry_language.projected_visual_contract import (
            serialize_certified_projected_visual,
        )
        from design.maas.program_massing.semantic_carriers import (
            audit_source_semantic_projection,
            build_program_semantic_carrier_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        evidence = build_program_semantic_carrier_evidence(
            authored,
            final,
            **self._task3_semantic_projection_kwargs(),
        )
        base = deepcopy(final.metadata)
        base["program_semantic_carrier_evidence"] = evidence
        certified_source = replace(final, metadata=base)
        external_audit = audit_source_semantic_projection(
            certified_source,
            building_type="gymnasium",
            expected_context=self._task3_semantic_projection_kwargs(),
        )
        with self.assertRaisesRegex(
            ValueError,
            "authored projected surface authority identity audit failed",
        ):
            serialize_certified_projected_visual(
                certified_source,
                final_semantic_audit={
                    "hard_pass": True,
                    "semantic_projection_hash": evidence[
                        "semantic_projection_hash"
                    ],
                    "failures": [],
                },
            )
        cases = []
        missing_final_hash = deepcopy(base)
        missing_final_hash["geometry_program_bridge_evidence"].pop(
            "geometry_hash",
            None,
        )
        cases.append(("missing_final_hash", final.surfaces, missing_final_hash))
        tampered_program = deepcopy(base)
        tampered_program["geometry_program_bridge_evidence"][
            "program_hash"
        ] = "x" * 64
        cases.append(("program_hash", final.surfaces, tampered_program))
        tampered_surface = (
            replace(
                final.surfaces[0],
                vertices_m=(
                    (0.0, 0.0, 0.0),
                    (9.0, 0.0, 0.0),
                    (0.0, 10.0, 0.0),
                ),
            ),
            *final.surfaces[1:],
        )
        cases.append(("surface", tampered_surface, deepcopy(base)))
        tampered_semantic = deepcopy(base)
        tampered_semantic["program_semantic_carrier_evidence"][
            "semantic_projection_hash"
        ] = "s" * 64
        cases.append(("semantic", final.surfaces, tampered_semantic))

        for label, surfaces, metadata in cases:
            with self.subTest(label=label):
                source = SourceMass(
                    name=final.name,
                    footprint=final.footprint,
                    volumes=final.volumes,
                    surfaces=surfaces,
                    metadata=metadata,
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "authored projected surface authority identity audit failed",
                ):
                    serialize_certified_projected_visual(
                        source,
                        final_semantic_audit=external_audit,
                    )

    def test_multipart_floor_carriers_cover_all_retained_parts_without_truncation(self):
        from shapely.geometry import shape
        from shapely.ops import unary_union
        from design.maas.program_massing.semantic_carriers import (
            build_program_semantic_carrier_evidence,
        )

        authored, final = self._task3_floorwise_gym_sources()
        multipart = SourceMass(
            name=final.name,
            footprint=final.footprint,
            volumes=(
                SourceVolume(
                    "gym_main_long_span_hall",
                    box(0.0, 0.0, 4.0, 10.0),
                    0.0,
                    1.0,
                    "geometry_program",
                ),
                SourceVolume(
                    "gym_main_long_span_hall",
                    box(6.0, 0.0, 10.0, 10.0),
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            surfaces=final.surfaces,
            metadata=final.metadata,
        )
        evidence = build_program_semantic_carrier_evidence(
            authored,
            multipart,
            **self._task3_semantic_projection_kwargs(),
        )
        carrier_union = unary_union([
            shape(carrier["final_polygon_utm"])
            for carrier in evidence["carriers"]
            if carrier["floor_index"] == 0
        ])
        host_union = unary_union([
            volume.footprint for volume in multipart.volumes
        ])

        self.assertTrue(evidence["hard_pass"], evidence)
        self.assertLessEqual(
            carrier_union.symmetric_difference(host_union).area,
            1e-8,
        )

    def test_final_materialization_handoff_persists_verified_semantic_projection(self):
        from design.maas.book_language import candidate_generation
        from design.maas.geometry_language.base_seeds import base_seed_programs
        from design.maas.grammar.verb_sequence import VerbSequence

        authored, _final = self._task3_floorwise_gym_sources()
        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "slab"
        )
        host = box(-10.0, -10.0, 10.0, 10.0)
        sequence = VerbSequence(
            "task5-semantic-handoff",
            "task5-semantic-handoff",
            (),
            ("geometry_program_directive=task5-semantic-handoff",),
        )
        with patch.object(
            candidate_generation,
            "_geometry_program_registry",
            return_value={"task5-semantic-handoff": program},
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                authored,
                sequence,
                building_type="gymnasium",
                site_access_side="south",
                containment_host=host,
                floor_containment_hosts=(host,),
                floor_capacity_plan_hash="floor-plan-1",
                target_floor_areas_m2=(200.0,),
                pnu="1168011800104170004",
                capacity_alternative_id="spatial_reserve",
            )

        self.assertIsNotNone(materialized)
        assert materialized is not None
        evidence = materialized.metadata["program_semantic_carrier_evidence"]
        bridge = materialized.metadata["geometry_program_bridge_evidence"]
        self.assertTrue(evidence["hard_pass"], evidence)
        self.assertEqual(evidence["status"], "verified")
        self.assertEqual(
            {
                carrier["source_relation"]
                for carrier in evidence["carriers"]
            },
            {
                "dominant_hall",
                "public_entry_daylight",
                "service_support",
            },
        )
        self.assertEqual(
            evidence["final_program_hash"],
            bridge["program_hash"],
        )
        self.assertEqual(
            evidence["final_geometry_hash"],
            bridge["geometry_hash"],
        )
        self.assertEqual(
            evidence["final_surface_payload_hash"],
            bridge["surface_payload_hash"],
        )
        self.assertEqual(
            materialized.metadata["final_semantic_projection_context"]["pnu"],
            "1168011800104170004",
        )

    def test_final_materialization_rejects_block_when_service_carrier_is_in_final_void(self):
        from design.maas.book_language import candidate_generation
        from design.maas.geometry_language.base_seeds import base_seed_programs
        from design.maas.grammar.verb_sequence import VerbSequence

        authored, _final = self._task3_floorwise_gym_sources()
        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "block"
        )
        host = box(-10.0, -10.0, 10.0, 10.0)
        sequence = VerbSequence(
            "task5-semantic-handoff-block-rejection",
            "task5-semantic-handoff-block-rejection",
            (),
            (
                "geometry_program_directive="
                "task5-semantic-handoff-block-rejection",
            ),
        )
        captured: dict[str, object] = {}
        build_semantic_evidence = (
            candidate_generation.build_program_semantic_carrier_evidence
        )

        def capture_semantic_evidence(*args, **kwargs):
            evidence = build_semantic_evidence(*args, **kwargs)
            captured["evidence"] = evidence
            return evidence

        with (
            patch.object(
                candidate_generation,
                "_geometry_program_registry",
                return_value={
                    "task5-semantic-handoff-block-rejection": program,
                },
            ),
            patch.object(
                candidate_generation,
                "build_program_semantic_carrier_evidence",
                side_effect=capture_semantic_evidence,
            ),
        ):
            materialized = candidate_generation._materialize_directed_geometry(
                authored,
                sequence,
                building_type="gymnasium",
                site_access_side="south",
                containment_host=host,
                floor_containment_hosts=(host,),
                floor_capacity_plan_hash="floor-plan-1",
                target_floor_areas_m2=(200.0,),
                pnu="1168011800104170004",
                capacity_alternative_id="spatial_reserve",
            )

        self.assertIsNone(materialized)
        evidence = captured["evidence"]
        assert isinstance(evidence, dict)
        self.assertFalse(evidence["hard_pass"], evidence)
        self.assertEqual(evidence["status"], "rejected")
        self.assertEqual(
            evidence["failures"],
            ["required_carrier_projection_empty:service_support"],
        )
