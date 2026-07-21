"""Focused regressions for the executable MASS generation flow."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from PIL import Image
from shapely.geometry import box

from design.maas.geometry_language.compiler import compile_geometry_program
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
from design.maas.book_language.candidate_analysis import _design_concept_descriptor
from design.maas.source_geometry.ir import SourceMass


class MaasFlowRegressionTest(SimpleTestCase):
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
