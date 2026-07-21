from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import os
from types import SimpleNamespace

from django.test import SimpleTestCase

from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph
from design.maas.geometry_language import executed_archive


class MaasOutcomeRenderMemoryTest(SimpleTestCase):
    def test_executed_archive_keeps_success_and_failed_runs_in_time_order(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_root = root / "docs" / "playwright" / "design-route-live-verify"
            for order, (run_id, record_count) in enumerate((
                ("book-program-portfolios-run-a", 1),
                ("book-program-portfolios-run-b", 0),
            ), start=1):
                run = archive_root / run_id
                run.mkdir(parents=True)
                archive = run / "maas-book-exact-geometry-artifacts.json"
                summary = run / "maas-book-programs-summary.json"
                archive.write_text(json.dumps({
                    "pnu": "test-pnu",
                    "record_count": record_count,
                    "records": ([{"placeholder": True}] if record_count else []),
                }), encoding="utf-8")
                summary.write_text(json.dumps({"status": "PASS" if record_count else "FAIL"}), encoding="utf-8")
                timestamp = 1_700_000_000 + order
                os.utime(archive, (timestamp, timestamp))
                os.utime(summary, (timestamp, timestamp))

            executed_archive._read_json.cache_clear()
            with patch.object(executed_archive, "workspace_root", return_value=root):
                manifest = executed_archive.executed_mass_manifest(
                    "book-program-portfolios-run-b"
                )
            executed_archive._read_json.cache_clear()

            self.assertEqual(manifest["run_count"], 2)
            self.assertEqual(
                [item["run_id"] for item in manifest["runs"]],
                ["book-program-portfolios-run-a", "book-program-portfolios-run-b"],
            )
            self.assertTrue(manifest["runs"][0]["replayable"])
            self.assertFalse(manifest["runs"][1]["replayable"])
            self.assertEqual(manifest["selected_run_id"], "book-program-portfolios-run-b")
            self.assertEqual(manifest["mass_count"], 0)

    def test_mass_png_card_is_bound_to_typed_geometry_identity(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            graph_path = root / "outcome.json"
            board = root / "portfolio.png"
            candidate = SimpleNamespace(
                principle_id="book:operative:shift",
                sequence=SimpleNamespace(name="slab__book_shift"),
                source=SimpleNamespace(metadata={
                    "geometry_program": {
                        "name": "shifted_slab",
                        "root_id": "result",
                        "nodes": [],
                        "metadata": {
                            "pre_book_program_hash": "program-parent",
                            "base_seed": "slab",
                        },
                    },
                    "geometry_program_bridge_evidence": {
                        "program_hash": "program-projected",
                        "geometry_hash": "geometry-exact",
                        "source_seed": "slab",
                    },
                    "program_book_projection_evidence": {
                        "scope": {"base_volume_label": "1/2"},
                    },
                    "capacity_alternative_projection": {
                        "alternative_id": "maximum_feasible",
                        "target_utilization": 0.98,
                        "achieved_utilization": 0.94,
                        "target_hard_pass": False,
                    },
                }),
            )
            graph = GeometryOutcomeGraph.load(graph_path, pnu="test-pnu")
            graph.observe_portfolio_render(
                program_slug="office",
                candidates=[candidate],
                board_path=board,
                render_evidence=[{
                    "card_index": 1,
                    "crop_box": [0, 72, 384, 332],
                    "rendered_mass_pixel_count": 1200,
                    "rendered_mass_pixel_ratio": 0.012,
                    "hard_pass": True,
                }],
            )
            payload = graph.save()

            observation = next(item for item in payload["observations"] if item["stage"] == "mass_png_render")
            self.assertEqual(observation["projected_program_hash"], "program-projected")
            self.assertEqual(observation["geometry_hash"], "geometry-exact")
            self.assertEqual(observation["render_artifact"]["crop_box"], [0, 72, 384, 332])
            self.assertEqual(observation["capacity_alternative_id"], "maximum_feasible")
            self.assertEqual(observation["capacity_target_utilization"], 0.98)
            self.assertEqual(observation["capacity_achieved_utilization"], 0.94)
            self.assertTrue(observation["render_artifact"]["direct_png_review_required"])
            render_node = next(item for item in payload["nodes"] if item["kind"] == "render_artifact")
            self.assertEqual(render_node["attributes"]["board_png"], str(board))
            self.assertIn("rendered_as", {item["kind"] for item in payload["edges"]})

            restored = GeometryOutcomeGraph.load(graph_path, pnu="test-pnu")
            self.assertEqual(restored.to_dict()["observation_count"], 1)
