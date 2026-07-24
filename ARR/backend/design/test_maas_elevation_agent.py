import hashlib
import base64
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import types
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from design.maas.aesthetic.adapters.openai_image import OpenAIImageAdapter
from design.maas.aesthetic.contracts import ProviderResult, RenderedReference
from design.maas.agents.elevation_agent import (
    generate_elevation_bundle,
    generate_elevation_image_proposal,
    select_facade_strategy,
)
from design.maas.geometry_language import GeometryProgramBuilder, compile_geometry_program
from design.maas.single_execution import execute_single_mass


class _RecordingImageAdapter:
    name = "recording-image"

    def __init__(self, output_directory: Path) -> None:
        self.output_directory = output_directory
        self.calls = []

    def generate(self, job, reference):
        self.calls.append((job, reference))
        self.output_directory.mkdir(parents=True, exist_ok=True)
        output = self.output_directory / "provider-output.png"
        output.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\rIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff\x89\x99=\x1d"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return ProviderResult(
            provider=self.name,
            status="complete",
            assets=[{
                "asset_id": "asset:test:elevation-alt-01",
                "uri": str(output),
                "media_type": "image/png",
                "role": "generated_facade_image",
            }],
            metadata={"model": "fake-image-model", "request_id": "fake-request-1"},
        )


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

    def test_facade_strategy_is_derived_from_mass_geometry_without_world_coordinates(self):
        tower = self._program()
        tower_compilation = compile_geometry_program(tower)
        tower_strategy = select_facade_strategy(tower, tower_compilation)

        builder = GeometryProgramBuilder("courtyard_box")
        base = builder.add(
            "primitive",
            "box",
            parameters={"width": 14, "depth": 12, "height": 5},
            semantic_role="base_seed",
        )
        void = builder.add(
            "macro",
            "carve_void",
            inputs=(base,),
            parameters={"margin_ratio": 0.24, "open_side": "north"},
            semantic_role="main",
        )
        courtyard = builder.build(void)
        courtyard_strategy = select_facade_strategy(
            courtyard,
            compile_geometry_program(courtyard),
        )

        self.assertNotEqual(
            tower_strategy["strategy_id"],
            courtyard_strategy["strategy_id"],
        )
        self.assertIn("measured_features", tower_strategy)
        serialized = str(tower_strategy).lower()
        self.assertNotIn("world_coordinate", serialized)
        self.assertNotIn("position", serialized)
        self.assertEqual(tower_strategy["geometry_mutation_allowed"], False)

    def test_image_proposal_calls_provider_once_with_exact_mass_identity(self):
        compilation = compile_geometry_program(self._program())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            mass_preview = root / "mass.png"
            mass_preview.write_bytes(
                b"\x89PNG\r\n\x1a\n"
                b"\x00\x00\x00\rIHDR"
                b"\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
                b"\x00\x00\x00\rIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff\x89\x99=\x1d"
                b"\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            bundle = generate_elevation_bundle(
                compilation,
                root / "elevation",
                execution_id="elevation-proposal-test",
            )
            adapter = _RecordingImageAdapter(root / "provider")
            strategy = select_facade_strategy(self._program(), compilation)

            proposal = generate_elevation_image_proposal(
                bundle,
                mass_preview,
                adapter=adapter,
                strategy=strategy,
            )

            self.assertEqual(len(adapter.calls), 1)
            job, reference = adapter.calls[0]
            identity = job["identity"]
            self.assertEqual(identity["execution_id"], "elevation-proposal-test")
            self.assertEqual(identity["program_hash"], compilation.program.program_hash())
            self.assertEqual(identity["geometry_hash"], compilation.geometry_hash)
            self.assertEqual(reference.uri, str(mass_preview.resolve()))
            self.assertEqual(
                reference.metadata["identity"],
                identity,
            )
            self.assertEqual(proposal["status"], "complete")
            self.assertEqual(proposal["request_count"], 1)
            self.assertEqual(proposal["retry_count"], 0)
            self.assertEqual(proposal["identity"], identity)
            self.assertTrue(Path(proposal["artifact"]["path"]).is_file())
            self.assertTrue(Path(proposal["manifest_path"]).is_file())

    def test_openai_adapter_records_non_fabricated_request_and_hash_evidence(self):
        png = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\rIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff\x89\x99=\x1d"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        class _Usage:
            def model_dump(self):
                return {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}

        response = types.SimpleNamespace(
            data=[types.SimpleNamespace(b64_json=base64.b64encode(png).decode(), url=None)],
            usage=_Usage(),
        )

        class _RawResponse:
            headers = {"x-request-id": "request-from-provider"}

            @staticmethod
            def parse():
                return response

        class _Images:
            def __init__(self):
                self.with_raw_response = self

            @staticmethod
            def edit(**_kwargs):
                return _RawResponse()

        class _OpenAI:
            def __init__(self, **_kwargs):
                self.images = _Images()

        fake_module = types.SimpleNamespace(OpenAI=_OpenAI)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            reference_path = root / "reference.png"
            reference_path.write_bytes(png)
            adapter = OpenAIImageAdapter(output_dir=root / "generated")
            job = {
                "source_bundle_id": "execution-one",
                "candidate_id": "geometry-one",
                "prompt": {"prompt": "stone facade", "negative_prompt": "changed mass"},
            }
            reference = RenderedReference(
                asset_id="asset:reference",
                uri=str(reference_path),
                metadata={"reference_type": "multi_view_pack"},
            )
            with patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "test-key",
                    "OPENAI_IMAGE_MODEL": "test-image-model",
                    "OPENAI_IMAGE_SIZE": "1024x1024",
                },
                clear=False,
            ), patch.dict(sys.modules, {"openai": fake_module}):
                result = adapter.generate(job, reference)

        self.assertEqual(result.status, "complete")
        self.assertEqual(result.metadata["request_id"], "request-from-provider")
        self.assertEqual(result.metadata["usage"]["total_tokens"], 30)
        self.assertEqual(result.metadata["retry_count"], 0)
        self.assertEqual(
            result.metadata["input_image_sha256"],
            hashlib.sha256(png).hexdigest(),
        )
        self.assertEqual(
            result.metadata["output_image_sha256"],
            hashlib.sha256(png).hexdigest(),
        )
        self.assertEqual(len(result.metadata["prompt_sha256"]), 64)
