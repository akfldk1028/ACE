import json
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings

from design.maas.geometry_language import GeometryProgramBuilder
from design.maas.single_execution import execute_single_mass


def _box_program():
    builder = GeometryProgramBuilder("single_mass_catalog_box")
    root = builder.add(
        "primitive",
        "box",
        parameters={"width": 12, "depth": 8, "height": 5},
        semantic_role="base_seed",
    )
    return builder.build(root, family="single_mass_catalog_test")


class MaasSingleExecutionCatalogTest(SimpleTestCase):
    def test_catalog_exposes_full_flow_and_vlm_acceptance(self):
        with TemporaryDirectory() as directory:
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=directory):
                result = execute_single_mass(
                    _box_program(),
                    output_root=directory,
                    execution_id="accepted-vlm-mass",
                )
                manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
                manifest["full_flow_status"] = "accepted"
                manifest["vlm_review"] = {
                    "status": "live_scored",
                    "hard_pass": True,
                    "model": "test-vlm",
                }
                result.manifest_path.write_text(
                    json.dumps(manifest),
                    encoding="utf-8",
                )
                passport = json.loads(result.passport_path.read_text(encoding="utf-8"))
                vlm_stage = next(
                    stage for stage in passport["stages"] if stage["id"] == "vlm"
                )
                vlm_stage["status"] = "live_scored"
                vlm_stage["evidence"] = {
                    "status": "live_scored",
                    "hard_pass": True,
                    "model": "test-vlm",
                }
                result.passport_path.write_text(
                    json.dumps(passport),
                    encoding="utf-8",
                )

                payload = self.client.get("/design/maas/executed-masses/").json()
                run = next(
                    row
                    for row in payload["runs"]
                    if row["run_id"] == "single-execution:accepted-vlm-mass"
                )

        self.assertEqual(run["full_flow_status"], "accepted")
        self.assertEqual(run["vlm_status"], "live_scored")
        self.assertTrue(run["vlm_hard_pass"])
