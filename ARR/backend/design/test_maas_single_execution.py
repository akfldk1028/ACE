import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote

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
            self.assertTrue(manifest["created_at"].endswith("+00:00"))
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

    def test_single_execution_is_replayed_through_the_existing_mass_archive_contract(self):
        with TemporaryDirectory() as directory:
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=directory):
                execute_single_mass(
                    _box_program(),
                    output_root=directory,
                    execution_id="source-run",
                )
                run_id = "single-execution:source-run"
                query = quote(run_id, safe="")

                manifest_response = self.client.get(
                    f"/design/maas/executed-masses/?run_id={query}",
                )
                self.assertEqual(manifest_response.status_code, 200)
                manifest = manifest_response.json()
                self.assertEqual(manifest["run_id"], run_id)
                self.assertEqual(manifest["mass_count"], 1)
                self.assertEqual(manifest["masses"][0]["image_role"], "single_mass_execution_render")
                self.assertEqual(manifest["masses"][0]["geometry_ready"], True)
                self.assertIn(run_id, {row["run_id"] for row in manifest["runs"]})

                preview = self.client.get(
                    f"/design/maas/executed-masses/1/?run_id={query}",
                )
                self.assertEqual(preview.status_code, 200)
                b"".join(preview.streaming_content)
                preview.close()
                passport = self.client.get(
                    f"/design/maas/executed-masses/1/passport/?run_id={query}",
                )
                self.assertEqual(passport.status_code, 200)
                self.assertEqual(passport.json()["geometry_hash"], manifest["masses"][0]["geometry_hash"])
                outcome = self.client.get(
                    "/design/maas/outcome-graph/",
                    {"pnu": "test-pnu", "run_id": run_id},
                )
                self.assertEqual(outcome.status_code, 200)
                self.assertEqual(outcome.json()["status"], "not_found")

    def test_post_can_reexecute_a_selected_archive_mass_and_return_its_new_run_id(self):
        with TemporaryDirectory() as directory:
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=directory):
                execute_single_mass(
                    _box_program(),
                    output_root=directory,
                    execution_id="source-run",
                )
                response = self.client.post(
                    "/design/maas/single-executions/",
                    data=json.dumps({
                        "source_run_id": "single-execution:source-run",
                        "source_mass_index": 1,
                        "title": "frontend selected MASS replay",
                    }),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 201)
                payload = response.json()
                self.assertEqual(payload["archive_run_id"], f"single-execution:{payload['execution_id']}")
                replay = self.client.get(
                    "/design/maas/executed-masses/",
                    {"run_id": payload["archive_run_id"]},
                )
                self.assertEqual(replay.status_code, 200)
                self.assertEqual(replay.json()["masses"][0]["geometry_hash"], payload["geometry_hash"])

                second = self.client.post(
                    "/design/maas/single-executions/",
                    data=json.dumps({
                        "source_run_id": "single-execution:source-run",
                        "source_mass_index": 1,
                    }),
                    content_type="application/json",
                )
                self.assertEqual(second.status_code, 201)
                self.assertNotEqual(second.json()["archive_run_id"], payload["archive_run_id"])
                latest_catalog = self.client.get(
                    "/design/maas/executed-masses/",
                    {"run_id": second.json()["archive_run_id"]},
                ).json()
                single_runs = [
                    row for row in latest_catalog["runs"]
                    if row.get("run_type") == "single_execution"
                ]
                self.assertEqual(len(single_runs), 3)
