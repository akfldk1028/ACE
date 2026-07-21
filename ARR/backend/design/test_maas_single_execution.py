import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings
from django.core.management import call_command

from design.maas.geometry_language import GeometryProgramBuilder
from design.maas.single_execution import execute_single_mass


def _box_program():
    builder = GeometryProgramBuilder("single_mass_box")
    root = builder.add(
        "primitive",
        "box",
        parameters={"width": 12, "depth": 8, "height": 5},
        semantic_role="base_seed",
    )
    return builder.build(root, family="single_mass_test")


class MaasSingleExecutionTest(SimpleTestCase):
    def test_one_program_materializes_a_fast_auditable_execution_bundle(self):
        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                _box_program(),
                output_root=Path(directory),
                execution_id="test-box",
            )

            self.assertEqual(result.status, "geometry_ready")
            self.assertTrue(result.geometry_ready)
            self.assertEqual(result.full_flow_status, "in_progress")
            self.assertEqual(
                list(result.timings_ms),
                ["parse_validate", "compile", "geometry_gate", "render", "passport", "persist", "total"],
            )
            self.assertTrue(all(value >= 0 for value in result.timings_ms.values()))
            self.assertTrue(result.preview_path.is_file())
            self.assertTrue(result.passport_path.is_file())
            self.assertTrue(result.manifest_path.is_file())
            self.assertTrue(result.program_path.is_file())

            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            passport = json.loads(result.passport_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], "arr.maas.single_execution.v1")
            self.assertEqual(manifest["execution_id"], "test-box")
            self.assertEqual(manifest["geometry_hash"], result.geometry_hash)
            self.assertEqual(passport["geometry_hash"], result.geometry_hash)
            self.assertEqual(passport["activation_graph"]["result_node_ids"], ["result:mass"])
            self.assertEqual(
                next(stage for stage in passport["stages"] if stage["id"] == "law")["status"],
                "not_evaluated",
            )

    def test_invalid_program_persists_truthful_failure_without_a_fake_png(self):
        invalid = _box_program().to_dict()
        invalid["nodes"][0]["parameters"]["width"] = 0

        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                invalid,
                output_root=Path(directory),
                execution_id="invalid-box",
            )

            self.assertFalse(result.geometry_ready)
            self.assertEqual(result.status, "invalid_program")
            self.assertFalse(result.preview_path.exists())
            self.assertTrue(result.manifest_path.is_file())
            payload = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["gate_issues"][0]["code"], "non_positive_dimension")

    def test_compiled_mass_that_fails_geometry_gate_is_not_reported_as_compiled_success(self):
        builder = GeometryProgramBuilder("too_many_components")
        base = builder.add(
            "primitive",
            "box",
            parameters={"width": 1, "depth": 1, "height": 1},
        )
        root = builder.add(
            "pattern",
            "linear_array",
            inputs=(base,),
            parameters={"count": 6, "vector": [3, 0, 0]},
        )

        with TemporaryDirectory() as directory:
            result = execute_single_mass(builder.build(root), output_root=directory)

            self.assertEqual(result.status, "geometry_gate_failed")
            self.assertFalse(result.geometry_ready)
            self.assertFalse(result.preview_path.exists())
            self.assertIn(
                "disconnected_component_budget_exceeded",
                {issue["code"] for issue in result.gate_issues},
            )

    def test_post_endpoint_returns_discoverable_preview_and_manifest_urls(self):
        with TemporaryDirectory() as directory:
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=directory):
                response = self.client.post(
                    "/design/maas/single-executions/",
                    data=json.dumps({"program": _box_program().to_dict()}),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 201)
                payload = response.json()
                self.assertEqual(payload["status"], "geometry_ready")
                self.assertTrue(payload["geometry_ready"])
                self.assertTrue(payload["preview_url"].endswith("/preview/"))
                self.assertTrue(payload["manifest_url"].endswith("/manifest/"))
                preview_response = self.client.get(payload["preview_url"])
                self.assertEqual(preview_response.status_code, 200)
                b"".join(preview_response.streaming_content)
                preview_response.close()
                manifest_response = self.client.get(payload["manifest_url"])
                self.assertEqual(manifest_response.status_code, 200)
                self.assertEqual(manifest_response.json()["execution_id"], payload["execution_id"])

    def test_management_command_executes_one_built_in_shape(self):
        with TemporaryDirectory() as directory:
            output = StringIO()
            call_command(
                "execute_maas_single_mass",
                shape_index=10,
                output_root=directory,
                stdout=output,
            )

            payload = json.loads(output.getvalue())
            self.assertEqual(payload["status"], "geometry_ready")
            self.assertTrue(Path(payload["artifacts"]["preview"]).is_file())
            self.assertLess(payload["timings_ms"]["total"], 5_000)
