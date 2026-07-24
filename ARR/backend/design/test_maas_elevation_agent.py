import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, override_settings

from design.maas.agents.elevation_agent import generate_elevation_bundle
from design.maas.geometry_language import GeometryProgramBuilder, compile_geometry_program
from design.maas.single_execution import execute_single_mass


class MaasElevationAgentTest(SimpleTestCase):
    @staticmethod
    def _program():
        builder = GeometryProgramBuilder("elevation_box")
        base = builder.add(
            "primitive",
            "box",
            parameters={"width": 12, "depth": 8, "height": 6},
            semantic_role="base_seed",
        )
        mass = builder.add(
            "modifier",
            "taper",
            inputs=(base,),
            parameters={"axis": "z", "end_scale": [0.72, 0.82]},
            semantic_role="main",
        )
        return builder.build(mass)

    def test_compiled_mesh_generates_six_hash_bound_elevation_views(self):
        compilation = compile_geometry_program(self._program())

        with TemporaryDirectory() as directory:
            bundle = generate_elevation_bundle(
                compilation,
                Path(directory),
                execution_id="elevation-test",
            )
            views = {row["view"]: row for row in bundle["views"]}

            self.assertEqual(bundle["status"], "generated")
            self.assertEqual(
                set(views),
                {"front", "right", "back", "left", "top", "axon"},
            )
            self.assertEqual(bundle["program_hash"], compilation.program.program_hash())
            self.assertEqual(bundle["geometry_hash"], compilation.geometry_hash)
            self.assertTrue(Path(bundle["manifest_path"]).is_file())
            self.assertTrue(Path(bundle["condition_pack_path"]).is_file())
            for row in views.values():
                axes = row["projection_axes"]
                horizontal = axes["horizontal"]
                vertical = axes["vertical"]
                depth = axes["depth"]
                self.assertAlmostEqual(sum(value * value for value in horizontal), 1.0, places=6)
                self.assertAlmostEqual(sum(value * value for value in vertical), 1.0, places=6)
                self.assertAlmostEqual(sum(value * value for value in depth), 1.0, places=6)
                self.assertAlmostEqual(sum(a * b for a, b in zip(horizontal, vertical)), 0.0, places=6)
                self.assertAlmostEqual(sum(a * b for a, b in zip(horizontal, depth)), 0.0, places=6)
                self.assertAlmostEqual(sum(a * b for a, b in zip(vertical, depth)), 0.0, places=6)
                self.assertEqual(row["view_matrix4"][3], [0.0, 0.0, 0.0, 1.0])
                image = Path(row["path"])
                self.assertTrue(image.is_file())
                self.assertEqual(
                    row["sha256"],
                    hashlib.sha256(image.read_bytes()).hexdigest(),
                )

    def test_single_execution_materializes_active_elevation_agent_path(self):
        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                self._program(),
                output_root=directory,
                execution_id="elevation-integrated",
            )

            elevation_manifest = result.output_directory / "elevation" / "manifest.json"
            nodes = {
                node["id"]: node
                for node in result.passport["activation_graph"]["nodes"]
            }
            edges = {
                edge["relation"]: edge
                for edge in result.passport["activation_graph"]["edges"]
            }

            self.assertTrue(elevation_manifest.is_file())
            self.assertEqual(nodes["elevation:mesh_handoff"]["status"], "generated")
            self.assertEqual(nodes["elevation:condition_pack"]["status"], "generated")
            self.assertEqual(nodes["elevation:result"]["status"], "generated")
            self.assertTrue(nodes["elevation:result"]["evidence"]["artifact_exists"])
            self.assertEqual(nodes["elevation:result"]["evidence"]["view_count"], 6)
            self.assertTrue(nodes["elevation:result"]["evidence"]["preview_url"].endswith("/front/"))
            self.assertEqual(edges["generates_elevation"]["activation"], 1.0)

    def test_generated_elevation_view_is_served_by_the_single_execution_api(self):
        with TemporaryDirectory() as directory:
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=directory):
                execute_single_mass(
                    self._program(),
                    output_root=directory,
                    execution_id="elevation-http",
                )
                response = self.client.get(
                    "/design/maas/single-executions/elevation-http/elevation/front/",
                )
                payload = b"".join(response.streaming_content)
                response.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(payload.startswith(b"\x89PNG"))
