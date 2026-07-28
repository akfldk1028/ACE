"""Focused regressions for the executable MASS generation flow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from PIL import Image
from shapely.geometry import box

from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.affine_matrix import identity_matrix4
from design.maas.geometry_language.floorwise_visual_projection import (
    project_floorwise_visual_mesh,
)
from design.maas.geometry_language.program_projection import project_program_requirements
from design.maas.geometry_language.run_state import tracked_mass_command, update_run_progress
from design.maas.geometry_language.universal_form_bank import universal_form_programs
from design.maas.geometry_language.base_seeds import base_seed_program
from design.maas.preference.mesh_rasterizer import (
    RasterTriangle,
    rasterize_depth_tested_triangles,
)
from design.maas.book_language.portfolio_replenishment import (
    replenishment_cycle_budget_for_run,
)
from design.maas.book_language.portfolio_benchmark import default_outcome_graph_path
from design.maas.book_language import portfolio_benchmark
from design.maas.book_language.candidate_analysis import _design_concept_descriptor
from design.maas.program_massing.search import source_feature
from design.maas.program_massing.sequences import program_seed_sequences
from design.maas.geometry_language.executed_archive import compile_executed_mass
from design.maas.geometry_language.elevation_handoff import (
    build_executed_mass_elevation_handoff,
)
from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume


class MaasFlowRegressionTest(SimpleTestCase):
    @staticmethod
    def _projected_visual_source() -> tuple[SourceMass, str]:
        surfaces = (
            SourceSurface(
                role="main:skin:000",
                volume_role="main",
                verb="extrude",
                surface_type="profiled_triangle",
                vertices_m=(
                    (0.123456789, 0.0, 0.0),
                    (4.0, 0.0, 0.0),
                    (0.0, 3.0, 1.0),
                ),
                semantic_patch_id="main:skin:000",
            ),
            SourceSurface(
                role="main:skin:001",
                volume_role="main",
                verb="extrude",
                surface_type="profiled_triangle",
                vertices_m=(
                    (4.0, 0.0, 0.0),
                    (4.0, 3.0, 1.0),
                    (0.0, 3.0, 1.0),
                ),
                semantic_patch_id="main:skin:001",
            ),
        )
        hash_payload = [
            {
                "role": surface.role,
                "volume_role": surface.volume_role,
                "surface_type": surface.surface_type,
                "semantic_patch_id": surface.semantic_patch_id,
                "vertices": [
                    [round(float(x), 8), round(float(y), 8), round(float(z), 8)]
                    for x, y, z in surface.vertices_m
                ],
            }
            for surface in surfaces
        ]
        visual_hash = hashlib.sha256(json.dumps(
            hash_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        source = SourceMass(
            name="projected-visual",
            footprint=box(0, 0, 4, 3),
            surfaces=surfaces,
            metadata={
                "floorwise_visual_projection": {
                    "schema_version": "arr.maas.floorwise_visual_projection.v1",
                    "status": "certified",
                    "hard_pass": True,
                    "failure_reasons": [],
                    "visual_hash": visual_hash,
                    "source_surface_count": 2,
                    "projected_surface_count": 2,
                    "legal_sample_count": 6,
                    "capacity_gfa_m2": 24.0,
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
        return source, visual_hash

    @staticmethod
    def _write_projected_visual_archive(
        root: Path,
        *,
        artifact: dict,
        run_id: str = "book-program-portfolios-projected-visual",
    ) -> tuple[str, Path]:
        run_dir = (
            root / "docs" / "playwright" / "design-route-live-verify" / run_id
        )
        run_dir.mkdir(parents=True)
        (run_dir / "maas-book-exact-geometry-artifacts.json").write_text(
            json.dumps({
                "schema_version": "arr.maas.geometry_artifact_archive.v1",
                "pnu": "test-pnu",
                "record_count": 1,
                "records": [{
                    "trace_sequence_name": "projected-visual",
                    "geometry_artifact": artifact,
                }],
            }),
            encoding="utf-8",
        )
        (run_dir / "maas-book-programs-summary.json").write_text(
            json.dumps({
                "status": "pass",
                "pnu": "test-pnu",
                "programs": [{
                    "rows": [{
                        "source_sequence": "projected-visual",
                        "variant_id": "maas_01",
                    }],
                }],
            }),
            encoding="utf-8",
        )
        preview = run_dir / "preview.png"
        Image.new("RGB", (384, 322), (220, 120, 50)).save(preview)
        return run_id, preview

    def _projected_visual_artifact(
        self,
        source: SourceMass | None = None,
    ) -> tuple[dict, str]:
        if source is None:
            source, visual_hash = self._projected_visual_source()
        else:
            visual_hash = str(
                source.metadata["floorwise_visual_projection"]["visual_hash"]
            )
        binding = portfolio_benchmark._certified_projected_visual_artifact(source)
        program = base_seed_program("block")
        capacity_compilation = compile_geometry_program(program)
        self.assertEqual(capacity_compilation.status, "compiled")
        artifact = {
            "schemaVersion": "arr.maas.geometry_artifact.v1",
            "programType": "neighborhood",
            "programLabel": "Neighborhood",
            "sourceSequence": "projected-visual",
            "geometryProgram": program.to_dict(),
            "compilation": capacity_compilation.to_dict(include_mesh=False),
            "identity": {
                "programHash": program.program_hash(),
                "geometryHash": visual_hash,
            },
            "hardGates": {"combinedHardPass": True},
            **binding,
        }
        return artifact, visual_hash

    @staticmethod
    def _real_task1_projected_visual_source() -> SourceMass:
        footprint = box(-5.0, -5.0, 5.0, 5.0)
        authored = SourceMass(
            name="real-task1-projected-visual",
            footprint=footprint,
            surfaces=(
                SourceSurface(
                    role="recursive_primary:skin:000",
                    volume_role="recursive_primary",
                    verb="geometry_program",
                    surface_type="profiled_recursive_solid_mesh",
                    vertices_m=(
                        (-1.0, -1.0, 0.0),
                        (1.0, -1.0, 0.0),
                        (0.0, 1.0, 1.0),
                    ),
                    operator="loft",
                    semantic_patch_id="recursive_primary:profiled_triangle",
                ),
            ),
            metadata={
                "geometry_program_bridge_evidence": {
                    "status": "materialized",
                    "raw_mesh_triangle_count": 1,
                    "exported_surface_count": 1,
                },
            },
        )
        legal = box(-10.0, -10.0, 10.0, 10.0)
        capacity_plate = SourceVolume(
            role="recursive_primary",
            footprint=legal,
            bottom_fraction=0.0,
            top_fraction=1.0,
            verb="floorwise_legal_matrix4",
        )
        projection = project_floorwise_visual_mesh(
            authored,
            legal_sections=(legal,),
            floor_matrices=(identity_matrix4(),),
            capacity_plates=(capacity_plate,),
            output_origin=(0.0, 0.0),
        )
        if not projection.certificate.hard_pass:
            raise AssertionError(projection.certificate)
        return SourceMass(
            name=authored.name,
            footprint=legal,
            volumes=(capacity_plate,),
            surfaces=projection.surfaces,
            metadata={
                "floorwise_visual_projection": projection.certificate.to_dict(),
            },
        )

    def test_projected_visual_identity_survives_board_archive_and_elevation(self):
        source = self._real_task1_projected_visual_source()
        artifact, visual_hash = self._projected_visual_artifact(source)
        feature = source_feature(
            source,
            program_seed_sequences("neighborhood_living")[0],
            building_type="neighborhood_living",
            height=24.0,
            floors=8,
            site_area=float(source.footprint.area),
        )
        feature["properties"]["geometry_artifact"] = artifact
        self.assertEqual(artifact["authority"], "certified_projected_visual_mesh")
        self.assertEqual(
            artifact["geometryProgramRole"],
            "capacity_replay_metadata_and_provenance",
        )
        self.assertEqual(artifact["projectedVisualGeometryHash"], visual_hash)
        self.assertTrue(feature["properties"]["source_surfaces"])
        self.assertTrue(all(
            surface["surface_type"] == "profiled_recursive_solid_mesh"
            for surface in feature["properties"]["source_surfaces"]
        ))
        expected_vertices = [
            list(vertex)
            for surface in source.surfaces
            for vertex in surface.vertices_m
        ]
        self.assertEqual(
            [
                vertex
                for triangle in artifact["projectedVisualMesh"]["triangles"]
                for vertex in triangle["vertices_m"]
            ],
            expected_vertices,
        )

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, preview = self._write_projected_visual_archive(
                root,
                artifact=artifact,
            )
            portfolio_benchmark.render_archive_sheet(
                [feature],
                preview,
                title="Task 1 projected visual identity",
            )
            projected_visual_hashes = [
                str(
                    (
                        feature["properties"].get("geometry_artifact")
                        or {}
                    ).get("projectedVisualGeometryHash")
                    or ""
                )
            ]
            board_evidence = portfolio_benchmark._archive_render_evidence(
                preview,
                1,
                projected_visual_hashes=projected_visual_hashes,
            )
            self.assertEqual(len(board_evidence), 1)
            self.assertTrue(board_evidence[0]["hard_pass"], board_evidence[0])
            self.assertGreater(
                board_evidence[0]["rendered_mass_pixel_count"],
                0,
            )
            self.assertEqual(
                board_evidence[0]["projected_visual_geometry_hash"],
                visual_hash,
            )

            with patch(
                "design.maas.geometry_language.executed_archive.workspace_root",
                return_value=root,
            ):
                compilation, archived, _row, _path = compile_executed_mass(
                    1,
                    run_id,
                )
                self.assertEqual(compilation.geometry_hash, visual_hash)
                self.assertEqual(
                    [list(vertex) for vertex in compilation.vertices],
                    expected_vertices,
                )
                with (
                    patch(
                        "design.maas.geometry_language.elevation_handoff.executed_mass_manifest",
                        return_value={"pnu": "test-pnu"},
                    ),
                    patch(
                        "design.maas.geometry_language.elevation_handoff.materialize_executed_mass_passport",
                        return_value={"executed_mass": {"hard_pass": True}},
                    ),
                    patch(
                        "design.maas.geometry_language.elevation_handoff.materialize_executed_mass_preview",
                        return_value=preview,
                    ),
                ):
                    handoff = build_executed_mass_elevation_handoff(
                        run_id=run_id,
                        index=1,
                    )

            self.assertEqual(archived["projectedVisualGeometryHash"], visual_hash)
            self.assertEqual(handoff["identity"]["geometry_hash"], visual_hash)
            self.assertEqual(
                handoff["authority"]["source"],
                "validated_archived_projected_visual_mesh",
            )
            self.assertEqual(
                handoff["indexed_triangle_mesh"]["coordinate_space"],
                "capacity_source_centroid_local_xy_normalized_z",
            )
            self.assertEqual(
                handoff["indexed_triangle_mesh"]["vertices"],
                [list(vertex) for vertex in compilation.vertices],
            )

    def test_archive_passport_rebinds_certified_visual_identity_and_card_render(self):
        from design.maas.book_language.mass_passport_bridge import (
            selected_candidate_execution_passport,
        )
        from design.maas.geometry_language.execution_passport import (
            build_mass_execution_passport,
        )

        artifact, visual_hash = self._projected_visual_artifact()
        program = portfolio_benchmark.GeometryProgram.from_dict(
            artifact["geometryProgram"]
        )
        capacity_compilation = compile_geometry_program(program)
        certified_compilation = replace(
            capacity_compilation,
            geometry_hash=visual_hash,
        )
        stale_passport = build_mass_execution_passport(capacity_compilation)

        with TemporaryDirectory() as temporary:
            board = Path(temporary) / "board.png"
            Image.new("RGB", (384, 332), (220, 120, 50)).save(board)
            render_evidence = {
                "status": "passed",
                "path": str(board),
                "views": ["portfolio_card"],
                "card_index": 1,
                "crop_box": [0, 72, 384, 332],
                "rendered_mass_pixel_count": 7612,
                "render_hard_pass": True,
                "projected_visual_geometry_hash": visual_hash,
                "geometry_authority": "certified_projected_visual_mesh",
            }
            passport = selected_candidate_execution_passport(
                compilation={
                    "execution_passport": stale_passport,
                    "certified_compilation": certified_compilation,
                    "archive_render_evidence": render_evidence,
                    "combined_hard_pass": True,
                },
                downstream_row={
                    "legal_generation_context_evidence": {
                        "status": "passed",
                        "pnu": "1168011800104170004",
                    },
                    "legal_projection": {
                        "evaluated": True,
                        "hard_pass": True,
                    },
                    "parking_hard_gate": {
                        "evaluated": True,
                        "hard_pass": True,
                        "required_spaces": 2,
                        "provided_spaces": 2,
                    },
                },
                source_metadata={
                    "capacity_alternative_projection": {
                        "requested_capacity_alternative_id": "maximum_feasible",
                        "requested_target_utilization": 0.95,
                        "target_hard_pass": False,
                        "selectable_capacity_alternative_id": "balanced_yield",
                        "selectable_capacity_target_utilization": 0.80,
                        "selectable_capacity_hard_pass": True,
                    },
                    "source_capacity_measurement": {
                        "schema_version": "arr.maas.source_capacity_measurement.v1",
                        "feasible_capacity_utilization": 0.8241,
                    },
                },
                program_evidence={"evaluated": True, "hard_pass": True},
                descriptor={"capacity_target_hard_pass": False},
                pnu="1168011800104170004",
            )

        self.assertEqual(passport["program_hash"], program.program_hash())
        self.assertEqual(passport["geometry_hash"], visual_hash)
        self.assertEqual(passport["status"], "in_progress")
        self.assertFalse(passport["full_flow_complete"])
        self.assertFalse(passport["final_hard_pass"])
        stages = {stage["id"]: stage for stage in passport["stages"]}
        self.assertEqual(stages["law"]["status"], "passed")
        self.assertEqual(stages["parking"]["status"], "passed")
        self.assertEqual(stages["render"]["status"], "passed")
        self.assertEqual(
            stages["render"]["evidence"]["projected_visual_geometry_hash"],
            visual_hash,
        )
        self.assertEqual(stages["vlm"]["status"], "not_evaluated")
        self.assertEqual(stages["agent_collaboration"]["status"], "not_evaluated")
        self.assertEqual(passport["agent_collaboration"], {})
        graph_nodes = {
            node["id"]: node for node in passport["activation_graph"]["nodes"]
        }
        self.assertEqual(graph_nodes["render:mass_png"]["status"], "passed")
        self.assertEqual(
            graph_nodes["render:mass_png"]["evidence"][
                "projected_visual_geometry_hash"
            ],
            visual_hash,
        )
        self.assertNotIn("agent:law_graph_agent", graph_nodes)

    def test_archive_render_evidence_requires_certified_geometry_hash(self):
        from design.maas.geometry_language.execution_passport import (
            build_mass_execution_passport,
        )

        compilation = compile_geometry_program(base_seed_program("block"))
        with TemporaryDirectory() as temporary:
            board = Path(temporary) / "board.png"
            Image.new("RGB", (32, 24), (220, 120, 50)).save(board)
            with self.assertRaisesRegex(
                ValueError,
                "render evidence geometry identity is required",
            ):
                build_mass_execution_passport(
                    compilation,
                    render_evidence={
                        "board_png": str(board),
                        "hard_pass": True,
                        "crop_box": [0, 0, 32, 24],
                    },
                )

    def test_archive_render_evidence_requires_decodable_png(self):
        from design.maas.geometry_language.execution_passport import (
            build_mass_execution_passport,
        )

        compilation = compile_geometry_program(base_seed_program("block"))
        with TemporaryDirectory() as temporary:
            board = Path(temporary) / "board.png"
            board.write_bytes(b"not a png")
            with self.assertRaisesRegex(ValueError, "render evidence PNG is invalid"):
                build_mass_execution_passport(
                    compilation,
                    render_evidence={
                        "board_png": str(board),
                        "hard_pass": True,
                        "crop_box": [0, 0, 1, 1],
                        "projected_visual_geometry_hash": compilation.geometry_hash,
                    },
                )

    def test_archive_render_evidence_rejects_crop_outside_png(self):
        from design.maas.geometry_language.execution_passport import (
            build_mass_execution_passport,
        )

        compilation = compile_geometry_program(base_seed_program("block"))
        with TemporaryDirectory() as temporary:
            board = Path(temporary) / "board.png"
            Image.new("RGB", (32, 24), (220, 120, 50)).save(board)
            with self.assertRaisesRegex(
                ValueError,
                "render evidence crop is invalid",
            ):
                build_mass_execution_passport(
                    compilation,
                    render_evidence={
                        "board_png": str(board),
                        "hard_pass": True,
                        "crop_box": [0, 0, 33, 24],
                        "projected_visual_geometry_hash": compilation.geometry_hash,
                    },
                )

    def test_explicit_failed_geometry_gate_cannot_render_as_passed(self):
        from design.maas.geometry_language.execution_passport import (
            build_mass_execution_passport,
        )

        compilation = compile_geometry_program(base_seed_program("block"))
        passport = build_mass_execution_passport(
            compilation,
            geometry_gate_evidence={
                "hard_pass": False,
                "authority": "benchmark_final_hard_gates",
            },
        )

        geometry_gate = next(
            stage for stage in passport["stages"] if stage["id"] == "geometry_gate"
        )
        self.assertEqual(geometry_gate["status"], "failed")
        self.assertFalse(geometry_gate["evidence"]["hard_pass"])
        graph_gate = next(
            node
            for node in passport["activation_graph"]["nodes"]
            if node["id"] == "flow:geometry_gate"
        )
        self.assertEqual(graph_gate["status"], "failed")
        compiler_gate_edge = next(
            edge
            for edge in passport["activation_graph"]["edges"]
            if edge["source"] == "flow:compiler"
            and edge["target"] == "flow:geometry_gate"
        )
        self.assertEqual(compiler_gate_edge["activation"], 0.0)

    def test_stripped_certified_metrics_are_remeasured_before_downstream_pass(self):
        from design.maas.geometry_language.execution_passport import (
            build_mass_execution_passport,
        )

        measured = compile_geometry_program(base_seed_program("block"))
        stripped = replace(
            measured,
            metrics={
                "vertex_count": len(measured.vertices),
                "triangle_count": len(measured.triangles),
                "coordinate_space": (
                    "capacity_source_centroid_local_xy_normalized_z"
                ),
                "geometry_authority": "certified_projected_visual_mesh",
                "exact_payload_hash": "certified-visual-payload",
                "capacity_geometry_hash": measured.geometry_hash,
                "capacity_replay_metrics": dict(measured.metrics),
            },
        )

        passport = build_mass_execution_passport(
            stripped,
            geometry_gate_evidence={
                "hard_pass": True,
                "authority": "benchmark_final_hard_gates",
            },
        )

        geometry_gate = next(
            stage for stage in passport["stages"] if stage["id"] == "geometry_gate"
        )
        self.assertEqual(geometry_gate["status"], "passed")
        self.assertTrue(geometry_gate["evidence"]["hard_pass"])
        self.assertEqual(geometry_gate["evidence"]["issues"], [])
        self.assertTrue(
            geometry_gate["evidence"]["metrics"]["certified_mesh_revalidated"]
        )
        self.assertTrue(geometry_gate["evidence"]["metrics"]["watertight"])
        self.assertGreater(geometry_gate["evidence"]["metrics"]["volume"], 0.0)

    def test_certified_geometry_gate_remeasures_mesh_instead_of_capacity_metrics(self):
        from design.maas.geometry_language.execution_passport import (
            build_mass_execution_passport,
        )

        capacity = compile_geometry_program(base_seed_program("block"))
        open_certified_mesh = replace(
            capacity,
            triangles=capacity.triangles[:-1],
            geometry_hash="f" * 64,
            metrics={
                **capacity.metrics,
                "geometry_authority": "certified_projected_visual_mesh",
                "capacity_geometry_hash": capacity.geometry_hash,
                "exact_payload_hash": "e" * 64,
            },
        )

        passport = build_mass_execution_passport(
            open_certified_mesh,
            geometry_gate_evidence={
                "hard_pass": True,
                "authority": "benchmark_final_hard_gates",
            },
        )

        compiler = next(
            stage for stage in passport["stages"] if stage["id"] == "compiler"
        )
        geometry_gate = next(
            stage for stage in passport["stages"] if stage["id"] == "geometry_gate"
        )
        self.assertEqual(compiler["status"], "failed")
        self.assertEqual(geometry_gate["status"], "failed")
        self.assertFalse(geometry_gate["evidence"]["hard_pass"])
        self.assertIn(
            "certified_mesh_not_manifold",
            {
                issue["code"]
                for issue in geometry_gate["evidence"]["issues"]
            },
        )

    def test_passport_floor_capacity_plan_identity_uses_hash_or_unresolved_sentinel(self):
        from design.maas.geometry_language.execution_passport import (
            build_mass_execution_passport,
        )

        compilation = compile_geometry_program(base_seed_program("block"))
        cases = (
            ({}, "FLOOR_CAPACITY_PLAN_HASH_UNRESOLVED"),
            (
                {
                    "capacity": {
                        "evaluated": True,
                        "hard_pass": True,
                        "floor_capacity_plan_hash": "floor-plan-measured",
                    },
                },
                "floor-plan-measured",
            ),
        )
        for downstream, expected in cases:
            with self.subTest(expected=expected):
                passport = build_mass_execution_passport(
                    compilation,
                    downstream_evidence=downstream,
                )
                self.assertEqual(
                    passport["floor_capacity_plan_hash"],
                    expected,
                )

    def test_render_observation_uses_certified_projected_visual_hash(self):
        source, visual_hash = self._projected_visual_source()
        source = replace(
            source,
            metadata={
                **source.metadata,
                "geometry_program": {
                    "name": "visual",
                    "root_id": "root",
                    "nodes": [],
                    "metadata": {},
                },
                "geometry_program_bridge_evidence": {
                    "program_hash": "projected-program",
                    "geometry_hash": "capacity-geometry",
                },
            },
        )
        candidate = SimpleNamespace(
            principle_id="book:visual",
            sequence=SimpleNamespace(name="visual-seed"),
            source=source,
        )
        with TemporaryDirectory() as directory:
            graph = GeometryOutcomeGraph.load(
                Path(directory) / "outcome.json",
                pnu="test-pnu",
            )
            graph.observe_portfolio_render(
                program_slug="neighborhood_living",
                candidates=[candidate],
                board_path=Path(directory) / "board.png",
                render_evidence=[{
                    "card_index": 1,
                    "hard_pass": True,
                    "projected_visual_geometry_hash": visual_hash,
                }],
            )
            payload = graph.to_dict()

        observation = next(
            item
            for item in payload["observations"]
            if item["stage"] == "mass_png_render"
        )
        self.assertEqual(observation["geometry_hash"], visual_hash)
        self.assertEqual(
            observation["capacity_geometry_hash"],
            "capacity-geometry",
        )
        self.assertEqual(
            observation["render_artifact"]["projected_visual_geometry_hash"],
            visual_hash,
        )

    def test_render_observation_rejects_visual_hash_certificate_mismatch(self):
        source, _visual_hash = self._projected_visual_source()
        source = replace(
            source,
            metadata={
                **source.metadata,
                "geometry_program": {
                    "name": "visual",
                    "root_id": "root",
                    "nodes": [],
                    "metadata": {},
                },
                "geometry_program_bridge_evidence": {
                    "program_hash": "projected-program",
                    "geometry_hash": "capacity-geometry",
                },
            },
        )
        candidate = SimpleNamespace(
            principle_id="book:visual",
            sequence=SimpleNamespace(name="visual-seed"),
            source=source,
        )
        with TemporaryDirectory() as directory:
            graph = GeometryOutcomeGraph.load(
                Path(directory) / "outcome.json",
                pnu="test-pnu",
            )
            with self.assertRaisesRegex(
                ValueError,
                "projected visual render hash mismatch",
            ):
                graph.observe_portfolio_render(
                    program_slug="neighborhood_living",
                    candidates=[candidate],
                    board_path=Path(directory) / "board.png",
                    render_evidence=[{
                        "card_index": 1,
                        "hard_pass": True,
                        "projected_visual_geometry_hash": "0" * 64,
                    }],
                )

    def test_render_observation_rejects_missing_visual_certificate(self):
        source, visual_hash = self._projected_visual_source()
        source = replace(
            source,
            metadata={
                "geometry_program": {
                    "name": "legacy",
                    "root_id": "root",
                    "nodes": [],
                    "metadata": {},
                },
                "geometry_program_bridge_evidence": {
                    "program_hash": "projected-program",
                    "geometry_hash": "capacity-geometry",
                },
            },
        )
        candidate = SimpleNamespace(
            principle_id="book:legacy",
            sequence=SimpleNamespace(name="legacy-seed"),
            source=source,
        )
        with TemporaryDirectory() as directory:
            graph = GeometryOutcomeGraph.load(
                Path(directory) / "outcome.json",
                pnu="test-pnu",
            )
            with self.assertRaisesRegex(
                ValueError,
                "certified=missing",
            ):
                graph.observe_portfolio_render(
                    program_slug="neighborhood_living",
                    candidates=[candidate],
                    board_path=Path(directory) / "board.png",
                    render_evidence=[{
                        "card_index": 1,
                        "hard_pass": True,
                        "projected_visual_geometry_hash": visual_hash,
                    }],
                )

    def test_render_observation_rejects_fabricated_empty_visual_certificate(self):
        source = SourceMass(
            name="fabricated-empty",
            footprint=box(0, 0, 4, 3),
            surfaces=(),
            metadata={
                "geometry_program": {
                    "name": "fabricated",
                    "root_id": "root",
                    "nodes": [],
                    "metadata": {},
                },
                "geometry_program_bridge_evidence": {
                    "program_hash": "projected-program",
                    "geometry_hash": "capacity-geometry",
                },
                "floorwise_visual_projection": {
                    "schema_version": "arr.maas.floorwise_visual_projection.v1",
                    "status": "certified",
                    "hard_pass": True,
                    "visual_hash": "f" * 64,
                    "projected_surface_count": 0,
                },
            },
        )
        candidate = SimpleNamespace(
            principle_id="book:fabricated",
            sequence=SimpleNamespace(name="fabricated"),
            source=source,
        )
        with TemporaryDirectory() as directory:
            graph = GeometryOutcomeGraph.load(
                Path(directory) / "outcome.json",
                pnu="test-pnu",
            )
            with self.assertRaisesRegex(
                ValueError,
                "certified projected visual mesh is missing or invalid",
            ):
                graph.observe_portfolio_render(
                    program_slug="neighborhood_living",
                    candidates=[candidate],
                    board_path=Path(directory) / "board.png",
                    render_evidence=[{
                        "card_index": 1,
                        "hard_pass": True,
                        "projected_visual_geometry_hash": "f" * 64,
                    }],
                )

    def test_projected_visual_archive_tamper_fails_closed(self):
        artifact, _visual_hash = self._projected_visual_artifact()
        artifact["projectedVisualMesh"]["triangles"][0]["vertices_m"][0][0] += 0.5
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, _preview = self._write_projected_visual_archive(
                root,
                artifact=artifact,
                run_id="book-program-portfolios-tampered-visual",
            )
            with patch(
                "design.maas.geometry_language.executed_archive.workspace_root",
                return_value=root,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "projected visual (?:exact payload|mesh) hash mismatch",
                ):
                    compile_executed_mass(1, run_id)

    def test_certified_profiled_recursive_surface_type_round_trips_archive(self):
        source = self._real_task1_projected_visual_source()
        artifact, visual_hash = self._projected_visual_artifact(source)
        self.assertEqual(
            artifact["projectedVisualMesh"]["triangles"][0]["surface_type"],
            "profiled_recursive_solid_mesh",
        )
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, _preview = self._write_projected_visual_archive(
                root,
                artifact=artifact,
                run_id="book-program-portfolios-production-profiled-type",
            )
            with patch(
                "design.maas.geometry_language.executed_archive.workspace_root",
                return_value=root,
            ):
                compilation, _artifact, _row, _path = compile_executed_mass(
                    1,
                    run_id,
                )
        self.assertEqual(compilation.geometry_hash, visual_hash)
        self.assertEqual(
            len(compilation.triangles),
            source.metadata["floorwise_visual_projection"][
                "projected_surface_count"
            ],
        )

    def test_real_task1_projector_output_has_exact_transport_identity(self):
        source = self._real_task1_projected_visual_source()
        artifact, visual_hash = self._projected_visual_artifact(source)
        self.assertEqual(
            artifact["projectedVisualCertificate"]["visual_hash"],
            visual_hash,
        )
        self.assertEqual(
            len(artifact["projectedVisualMesh"]["triangles"]),
            source.metadata["floorwise_visual_projection"][
                "projected_surface_count"
            ],
        )
        self.assertTrue(artifact["projectedVisualMesh"]["triangles"])
        self.assertRegex(artifact["projectedVisualPayloadHash"], r"^[0-9a-f]{64}$")

    def test_production_archive_replay_retains_separate_capacity_geometry_hash(self):
        artifact, visual_hash = self._projected_visual_artifact()
        capacity_hash = str(artifact["compilation"]["geometry_hash"])
        self.assertNotEqual(capacity_hash, visual_hash)
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, _preview = self._write_projected_visual_archive(
                root,
                artifact=artifact,
                run_id="book-program-portfolios-capacity-hash",
            )
            with patch(
                "design.maas.geometry_language.executed_archive.workspace_root",
                return_value=root,
            ):
                compilation, _artifact, _row, _path = compile_executed_mass(
                    1,
                    run_id,
                )

        self.assertEqual(compilation.geometry_hash, visual_hash)
        self.assertEqual(
            compilation.metrics["capacity_geometry_hash"],
            capacity_hash,
        )

    def test_projected_archive_rejects_tampered_stored_capacity_hash(self):
        artifact, _visual_hash = self._projected_visual_artifact()
        artifact["compilation"]["geometry_hash"] = "0" * 64
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, _preview = self._write_projected_visual_archive(
                root,
                artifact=artifact,
                run_id="book-program-portfolios-tampered-capacity-hash",
            )
            with patch(
                "design.maas.geometry_language.executed_archive.workspace_root",
                return_value=root,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "capacity replay compilation identity mismatch",
                ):
                    compile_executed_mass(1, run_id)

    def test_projected_archive_rejects_tampered_stored_capacity_bounds(self):
        artifact, _visual_hash = self._projected_visual_artifact()
        artifact["compilation"]["metrics"]["bounds"][1][2] = 100.0
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, _preview = self._write_projected_visual_archive(
                root,
                artifact=artifact,
                run_id="book-program-portfolios-tampered-capacity-bounds",
            )
            with patch(
                "design.maas.geometry_language.executed_archive.workspace_root",
                return_value=root,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "capacity replay compilation metrics mismatch",
                ):
                    compile_executed_mass(1, run_id)

    def test_authored_profiled_source_without_projection_certificate_fails_closed(self):
        source = replace(
            self._real_task1_projected_visual_source(),
            metadata={},
        )

        with self.assertRaisesRegex(
            ValueError,
            "authored profiled visual source has no certified projection",
        ):
            portfolio_benchmark._certified_projected_visual_artifact(source)

    def test_authored_profiled_source_with_not_applicable_certificate_fails_closed(self):
        source = self._real_task1_projected_visual_source()
        certificate = dict(source.metadata["floorwise_visual_projection"])
        certificate["status"] = "not_applicable_no_authored_mesh"
        source = replace(
            source,
            metadata={"floorwise_visual_projection": certificate},
        )

        with self.assertRaisesRegex(
            ValueError,
            "authored profiled visual source has no certified projection",
        ):
            portfolio_benchmark._certified_projected_visual_artifact(source)

    def test_proxy_only_source_without_projection_certificate_remains_legacy(self):
        proxy = SourceMass(
            name="proxy-only-legacy",
            footprint=box(-5.0, -5.0, 5.0, 5.0),
            volumes=(
                SourceVolume(
                    role="main",
                    footprint=box(-5.0, -5.0, 5.0, 5.0),
                    bottom_fraction=0.0,
                    top_fraction=1.0,
                    verb="legacy_proxy",
                ),
            ),
        )

        self.assertEqual(
            portfolio_benchmark._certified_projected_visual_artifact(proxy),
            {},
        )

    def test_sub_eight_decimal_projected_visual_tamper_fails_closed(self):
        artifact, _visual_hash = self._projected_visual_artifact()
        artifact["projectedVisualMesh"]["triangles"][0]["vertices_m"][0][0] += 1e-10
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, _preview = self._write_projected_visual_archive(
                root,
                artifact=artifact,
                run_id="book-program-portfolios-sub-eight-decimal-tamper",
            )
            with patch(
                "design.maas.geometry_language.executed_archive.workspace_root",
                return_value=root,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "projected visual exact payload hash mismatch",
                ):
                    compile_executed_mass(1, run_id)

    def test_projected_authority_markers_prevent_field_deletion_downgrade(self):
        artifact, _visual_hash = self._projected_visual_artifact()
        for field in (
            "projectedVisualMesh",
            "projectedVisualCertificate",
            "projectedVisualGeometryHash",
            "projectedVisualPayloadHash",
        ):
            artifact.pop(field, None)
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, _preview = self._write_projected_visual_archive(
                root,
                artifact=artifact,
                run_id="book-program-portfolios-projected-downgrade",
            )
            with patch(
                "design.maas.geometry_language.executed_archive.workspace_root",
                return_value=root,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "incomplete projected visual archive binding",
                ):
                    compile_executed_mass(1, run_id)

    def test_genuine_legacy_elevation_keeps_geometry_program_authority_label(self):
        artifact, _visual_hash = self._projected_visual_artifact()
        capacity_hash = str(artifact["compilation"]["geometry_hash"])
        artifact["authority"] = "final_legal_floorwise_geometry_program"
        artifact.pop("geometryProgramRole", None)
        for field in (
            "projectedVisualMesh",
            "projectedVisualCertificate",
            "projectedVisualGeometryHash",
            "projectedVisualPayloadHash",
        ):
            artifact.pop(field, None)
        artifact["identity"]["geometryHash"] = capacity_hash

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_id, preview = self._write_projected_visual_archive(
                root,
                artifact=artifact,
                run_id="book-program-portfolios-genuine-legacy",
            )
            with (
                patch(
                    "design.maas.geometry_language.executed_archive.workspace_root",
                    return_value=root,
                ),
                patch(
                    "design.maas.geometry_language.elevation_handoff.executed_mass_manifest",
                    return_value={"pnu": "test-pnu"},
                ),
                patch(
                    "design.maas.geometry_language.elevation_handoff.materialize_executed_mass_passport",
                    return_value={"executed_mass": {"hard_pass": True}},
                ),
                patch(
                    "design.maas.geometry_language.elevation_handoff.materialize_executed_mass_preview",
                    return_value=preview,
                ),
            ):
                handoff = build_executed_mass_elevation_handoff(
                    run_id=run_id,
                    index=1,
                )

        self.assertEqual(
            handoff["authority"]["source"],
            "recompiled_executed_geometry_program",
        )
        self.assertEqual(
            handoff["geometry_program_role"],
            "executable_geometry",
        )
        self.assertTrue(
            handoff["authority"]["capacity_replay_program_visual_authority"]
        )

    def test_spatial_chassis_and_frontage_controller_form_one_ground_strategy(self):
        def descriptor(chassis: str, controller: str) -> dict:
            parameters = (
                {"access_side": "west"}
                if controller == "lift"
                else {"side": "west"}
            )
            source = SourceMass(
                name=f"{chassis}-{controller}",
                footprint=box(0, 0, 10, 8),
                metadata={
                    "program_context": {"site_access_side_in_program_frame": "west"},
                    "geometry_program": {
                        "metadata": {"base_seed": "block"},
                        "nodes": [
                            {
                                "id": "chassis",
                                "operator": chassis,
                                "parameters": {"margin_ratio": 0.24},
                                "semantic_role": "main",
                                "provenance": {"source": "executable_language_probe"},
                            },
                            {
                                "id": "threshold",
                                "operator": controller,
                                "parameters": parameters,
                                "semantic_role": "public_threshold",
                                "provenance": {
                                    "source": "post_book_program_projection",
                                    "program_invariant": True,
                                },
                            },
                        ],
                    },
                },
            )
            return _design_concept_descriptor(source)

        self.assertEqual(
            descriptor("courtyard", "lift")["ground_strategy"],
            "frontage_court_threshold",
        )
        self.assertEqual(
            descriptor("split_wing", "notch")["ground_strategy"],
            "frontage_split_threshold",
        )

    def test_default_outcome_graph_is_owned_by_the_run_directory(self):
        with TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            self.assertEqual(
                default_outcome_graph_path(output_dir),
                output_dir.resolve() / "maas-geometry-mutation-outcome-graph.json",
            )

    def test_nonlive_diagnostic_cycle_budget_is_explicit_and_bounded(self):
        with patch.dict(
            "os.environ",
            {"MAAS_BOOK_NONLIVE_REPLENISHMENT_CYCLES": "1"},
        ):
            self.assertEqual(replenishment_cycle_budget_for_run(live_vlm=False), 1)
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(replenishment_cycle_budget_for_run(live_vlm=False), 7)
        with patch.dict(
            "os.environ",
            {"MAAS_BOOK_SMOKE_REPLENISHMENT_CYCLES": "0"},
        ):
            self.assertEqual(
                replenishment_cycle_budget_for_run(
                    live_vlm=False,
                    smoke_mode=True,
                ),
                0,
            )

    def test_neighborhood_projection_supplies_three_or_more_real_threshold_languages(self):
        threshold_operators = set()
        for program in universal_form_programs():
            projected = project_program_requirements(
                program,
                building_type="neighborhood living",
                access_side="west",
            )
            projection = projected.metadata["program_projection"]
            controller = projected.node_map[projection["threshold_controller_node_id"]]
            threshold_operators.add(controller.operator)
            compilation = compile_geometry_program(projected)
            self.assertEqual(
                compilation.status,
                "compiled",
                (program.name, controller.operator, compilation.issues),
            )
            self.assertEqual(
                compilation.metrics["component_count"],
                1,
                (program.name, controller.operator, program.metadata),
            )

        self.assertGreaterEqual(len(threshold_operators), 3)
        self.assertTrue({"courtyard", "split_wing"} & threshold_operators)

    def test_nonorthogonal_profile_uses_footprint_preserving_threshold(self):
        triangular = base_seed_program("profiled_prism", variation_index=1)
        projected = project_program_requirements(
            triangular,
            building_type="neighborhood living",
            access_side="west",
        )
        projection = projected.metadata["program_projection"]
        controller = projected.node_map[projection["threshold_controller_node_id"]]

        self.assertEqual(controller.operator, "lift")
        compilation = compile_geometry_program(projected)
        self.assertEqual(compilation.status, "compiled", compilation.issues)
        self.assertEqual(compilation.metrics["component_count"], 1)

    def test_recursive_mesh_preview_uses_per_pixel_depth_not_draw_order(self):
        image = Image.new("RGBA", (32, 32), "white")
        near = RasterTriangle(
            points=((4.0, 4.0), (28.0, 4.0), (16.0, 28.0)),
            depths=(2.0, 2.0, 2.0),
            color=(20, 180, 80, 255),
        )
        far = RasterTriangle(
            points=((4.0, 4.0), (28.0, 4.0), (16.0, 28.0)),
            depths=(1.0, 1.0, 1.0),
            color=(220, 40, 40, 255),
        )

        covered = rasterize_depth_tested_triangles(
            image,
            (near, far),
            clip_box=(0, 0, 32, 32),
        )

        self.assertGreater(covered, 0)
        self.assertEqual(image.getpixel((16, 12)), (20, 180, 80, 255))

    def test_run_state_reads_persisted_summary_when_django_handle_returns_none(self):
        with TemporaryDirectory() as temporary:
            output_dir = Path(temporary)

            @tracked_mass_command
            def fake_handle(_command, *args, **options):
                update_run_progress(
                    Path(options["output_dir"]),
                    phase="replenishment",
                    cycle_index=1,
                    cycle_budget=1,
                )
                (Path(options["output_dir"]) / "maas-book-programs-summary.json").write_text(
                    json.dumps({
                        "status": "fail",
                        "programs": [{"selected_count": 16}],
                    }),
                    encoding="utf-8",
                )
                return None

            command_result = fake_handle(
                SimpleNamespace(),
                output_dir=str(output_dir),
                pnu="test-pnu",
                program=["neighborhood"],
                recursive_only=True,
                live_vlm=False,
                outcome_graph=None,
            )
            self.assertIsNone(command_result)
            state = json.loads((output_dir / "maas-run-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "completed_with_failed_gate")
            self.assertEqual(state["result_status"], "fail")
            self.assertEqual(state["selected_mass_count"], 16)
            self.assertEqual(state["phase"], "replenishment")
            self.assertEqual(state["cycle_index"], 1)

    def test_run_progress_keeps_lifecycle_identity_and_bounded_cycle_counts(self):
        with TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            update_run_progress(
                output_dir,
                phase="replenishment",
                program="neighborhood",
                cycle_index=1,
                cycle_budget=7,
                selection_pool_count=125,
                selected_mass_count=18,
                ignored_mesh_payload={"vertices": [1, 2, 3]},
            )
            state = json.loads((output_dir / "maas-run-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "running")
            self.assertEqual(state["phase"], "replenishment")
            self.assertEqual(state["selected_mass_count"], 18)
            self.assertNotIn("ignored_mesh_payload", state)

    def test_failed_run_preserves_last_truthful_progress_checkpoint(self):
        with TemporaryDirectory() as temporary:
            output_dir = Path(temporary)

            @tracked_mass_command
            def fake_handle(_command, *args, **options):
                update_run_progress(
                    Path(options["output_dir"]),
                    phase="replenishment",
                    cycle_index=2,
                    selected_mass_count=17,
                )
                raise RuntimeError("diagnostic stop")

            with self.assertRaisesRegex(RuntimeError, "diagnostic stop"):
                fake_handle(
                    SimpleNamespace(),
                    output_dir=str(output_dir),
                    pnu="test-pnu",
                    program=["neighborhood"],
                    recursive_only=True,
                    live_vlm=False,
                    outcome_graph=None,
                )
            state = json.loads((output_dir / "maas-run-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "failed")
            self.assertEqual(state["phase"], "replenishment")
            self.assertEqual(state["cycle_index"], 2)
            self.assertEqual(state["selected_mass_count"], 17)
