from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from design.maas.book_language.portfolio_witness import (
    persist_portfolio_witness,
)
from design.maas.book_language.portfolio_benchmark import (
    _candidate_program_hash,
)


class PortfolioWitnessTests(SimpleTestCase):
    def test_witness_renderer_excludes_uncertified_authored_profiled_feature(self):
        rendered = []

        def renderer(features, path, *, title):
            rendered.append(features)
            self.assertEqual(len(features), 1)
            self.assertEqual(
                features[0]["properties"]["portfolio_witness"]["candidate_id"],
                "certified-mass",
            )
            Path(path).write_bytes(b"certified-witness")

        certified_feature = {
            "properties": {
                "source_surfaces": [{
                    "surface_type": "profiled_triangle",
                    "vertices_m": [[0, 0, 0], [1, 0, 0], [0, 1, 1]],
                }],
                "floorwise_visual_projection": {
                    "schema_version": "arr.maas.floorwise_visual_projection.v1",
                    "status": "certified",
                    "hard_pass": True,
                    "visual_hash": "visual-certified",
                    "projected_surface_count": 1,
                },
                "geometry_artifact": {
                    "projectedVisualGeometryHash": "visual-certified",
                },
                "source_signature": {
                    "geometry_program_bridge_evidence": {
                        "raw_mesh_triangle_count": 1,
                    },
                },
            },
        }
        development_feature = {
            "properties": {
                "source_surfaces": [],
                "source_signature": {
                    "geometry_program_bridge_evidence": {
                        "raw_mesh_triangle_count": 12,
                    },
                },
            },
        }
        records = [
            {"candidate_id": "certified-mass", "status": "hard_pass_not_selected"},
            {"candidate_id": "development-mass", "status": "rejected"},
        ]

        with TemporaryDirectory() as temporary:
            evidence = persist_portfolio_witness(
                Path(temporary),
                program_slug="neighborhood",
                target_count=5,
                selected_count=1,
                records=records,
                features=[certified_feature, development_feature],
                failure_histogram={"strict_portfolio_not_selected": 1},
                renderer=renderer,
            )

        self.assertEqual(len(rendered), 1)
        self.assertEqual(evidence["rendered_candidate_count"], 1)
        self.assertEqual(evidence["excluded_feature_count"], 1)
        self.assertEqual(evidence["feature_exclusions"], [{
            "candidate_id": "development-mass",
            "feature_index": 1,
            "reason": "witness_feature_uncertified_authored_visual",
            "authority": {
                "schema_version": "",
                "status": "",
                "hard_pass": False,
                "visual_hash_present": False,
                "projected_surface_count": 0,
                "source_surface_count": 0,
                "profiled_surface_count": 0,
                "artifact_hash_matches": False,
            },
        }])

    def test_analysis_candidate_without_program_hash_method_is_supported(self):
        candidate = SimpleNamespace(
            principle_id="mass-a",
            source=SimpleNamespace(
                metadata={"final_legal_program_hash": "program-a"},
            ),
        )

        self.assertEqual(_candidate_program_hash(candidate), "program-a")

    def test_failed_strict_portfolio_persists_separate_png_and_json(self):
        rendered = []

        def renderer(features, path, *, title):
            rendered.append((features, Path(path), title))
            Path(path).write_bytes(b"png-witness")

        records = [
            {
                "candidate_id": "mass-a",
                "program_hash": "program-a",
                "geometry_hash": "geometry-a",
                "visual_hash": "visual-a",
                "status": "hard_pass_not_selected",
                "failure_reasons": ["portfolio_pair_incompatible"],
            },
            {
                "candidate_id": "mass-b",
                "program_hash": "program-b",
                "geometry_hash": "geometry-b",
                "visual_hash": "visual-b",
                "status": "rejected",
                "failure_reasons": ["final_vlm_program_fit_failed"],
            },
        ]
        certified_features = []
        for index in range(2):
            visual_hash = f"visual-{index}"
            certified_features.append({
                "properties": {
                    "source_surfaces": [{
                        "surface_type": "profiled_triangle",
                        "vertices_m": [[0, 0, 0], [1, 0, 0], [0, 1, 1]],
                    }],
                    "floorwise_visual_projection": {
                        "schema_version": "arr.maas.floorwise_visual_projection.v1",
                        "status": "certified",
                        "hard_pass": True,
                        "visual_hash": visual_hash,
                        "projected_surface_count": 1,
                    },
                    "geometry_artifact": {
                        "projectedVisualGeometryHash": visual_hash,
                    },
                },
            })
        with TemporaryDirectory() as temporary:
            evidence = persist_portfolio_witness(
                Path(temporary),
                program_slug="neighborhood",
                target_count=3,
                selected_count=0,
                records=records,
                features=certified_features,
                failure_histogram={
                    "portfolio_pair_incompatible": 1,
                    "final_vlm_program_fit_failed": 1,
                },
                renderer=renderer,
            )

            self.assertEqual(evidence["status"], "failed_portfolio_witness")
            self.assertFalse(evidence["publishable"])
            self.assertEqual(evidence["candidate_count"], 2)
            self.assertTrue(Path(evidence["board_path"]).is_file())
            self.assertTrue(Path(evidence["manifest_path"]).is_file())
            self.assertEqual(len(rendered), 1)
            self.assertIn("NOT SELECTED", rendered[0][2])

    def test_completed_target_does_not_emit_failure_witness(self):
        with TemporaryDirectory() as temporary:
            evidence = persist_portfolio_witness(
                Path(temporary),
                program_slug="neighborhood",
                target_count=3,
                selected_count=3,
                records=[],
                features=[],
                failure_histogram={},
                renderer=lambda *_args, **_kwargs: None,
            )

        self.assertEqual(evidence["status"], "not_required")
