import hashlib
import base64
from io import BytesIO
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import types
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from PIL import Image

from design.maas.aesthetic.adapters.openai_image import (
    OpenAIImageAdapter,
    _composite_locked_mass_output,
    _prepare_locked_mass_sheet,
    _write_locked_mass_mask,
)
from design.maas.aesthetic.contracts import ProviderResult, RenderedReference
from design.maas.agents.elevation_agent import (
    generate_elevation_bundle,
    generate_elevation_image_proposal,
    select_facade_strategy,
)
from design.maas.agents.elevation_agent.panel_roles import (
    apply_roof_semantic_guard,
    locked_sheet_panel_roles,
    roof_mass_mask,
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


class _NeedsReviewImageAdapter(_RecordingImageAdapter):
    def generate(self, job, reference):
        result = super().generate(job, reference)
        result.metadata["roof_semantic_guard"] = {
            "status": "needs_review",
            "changed_pixel_count": 12,
        }
        return result


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
            self.assertEqual(
                job["presentation"]["kind"],
                "architectural_render_sheet",
            )
            top_role = next(
                row
                for row in job["presentation"]["panel_roles"]
                if row["role"] == "top"
            )
            self.assertEqual(top_role["surface"], "roof_only")
            self.assertIn("roof-only", job["prompt"]["prompt"].lower())
            self.assertEqual(proposal["status"], "complete")
            self.assertEqual(proposal["request_count"], 1)
            self.assertEqual(proposal["retry_count"], 0)
            self.assertEqual(proposal["identity"], identity)
            self.assertEqual(
                proposal["presentation"]["authority"],
                "generated_design_proposal",
            )
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

    def test_image_proposal_marks_unresolved_roof_grid_as_needs_review(self):
        compilation = compile_geometry_program(self._program())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            mass_preview = root / "mass.png"
            Image.new("RGB", (8, 8), (170, 105, 34)).save(mass_preview)
            bundle = generate_elevation_bundle(
                compilation,
                root / "elevation",
                execution_id="elevation-roof-review",
            )
            adapter = _NeedsReviewImageAdapter(root / "provider")

            proposal = generate_elevation_image_proposal(
                bundle,
                mass_preview,
                adapter=adapter,
                strategy=select_facade_strategy(self._program(), compilation),
            )

        self.assertEqual(proposal["status"], "needs_review")
        self.assertEqual(proposal["request_count"], 1)
        self.assertEqual(proposal["retry_count"], 0)
        self.assertTrue(proposal["artifact"]["path"])

    def test_openai_locked_sheet_records_applied_roof_semantic_guard(self):
        locked = Image.new("RGB", (100, 100), "white")
        generated = Image.new("RGB", (100, 100), "white")
        for x in range(10, 40):
            for y in range(60, 90):
                locked.putpixel((x, y), (170, 105, 34))
                tone = 45 if (x // 2 + y // 2) % 2 == 0 else 210
                generated.putpixel((x, y), (tone, tone, tone))
        output_buffer = BytesIO()
        generated.save(output_buffer, format="PNG")
        output_png = output_buffer.getvalue()
        response = types.SimpleNamespace(
            data=[types.SimpleNamespace(
                b64_json=base64.b64encode(output_png).decode(),
                url=None,
            )],
            usage=None,
        )

        class _RawResponse:
            headers = {"x-request-id": "roof-guard-request"}

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

        with TemporaryDirectory() as directory:
            root = Path(directory)
            reference_path = root / "locked-sheet.png"
            locked.save(reference_path)
            adapter = OpenAIImageAdapter(output_dir=root / "generated")
            reference = RenderedReference(
                asset_id="asset:locked-sheet",
                uri=str(reference_path),
                metadata={
                    "reference_type": "locked_mass_sheet",
                    "presentation": {
                        "panel_roles": list(locked_sheet_panel_roles()),
                    },
                },
            )
            with patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "test-key",
                    "OPENAI_IMAGE_MODEL": "test-image-model",
                    "OPENAI_IMAGE_SIZE": "256x256",
                },
                clear=False,
            ), patch.dict(
                sys.modules,
                {"openai": types.SimpleNamespace(OpenAI=_OpenAI)},
            ):
                result = adapter.generate(
                    {
                        "source_bundle_id": "roof-guard",
                        "candidate_id": "geometry-roof-guard",
                        "presentation": {
                            "panel_roles": list(locked_sheet_panel_roles()),
                        },
                        "prompt": {
                            "prompt": "architectural render",
                            "negative_prompt": "facade grid on roof",
                        },
                    },
                    reference,
                )

        guard = result.metadata["roof_semantic_guard"]
        self.assertEqual(result.status, "complete")
        self.assertEqual(guard["status"], "applied")
        self.assertGreater(guard["changed_pixel_count"], 0)
        self.assertEqual(result.metadata["retry_count"], 0)

    def test_locked_mass_mask_opens_only_colored_mass_pixels(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            image = Image.new("RGB", (8, 8), "white")
            for x in range(2, 6):
                for y in range(3, 7):
                    image.putpixel((x, y), (170, 105, 34))
            image.save(source)

            mask_path, editable_ratio = _write_locked_mass_mask(
                source,
                root / "mask.png",
            )
            with Image.open(mask_path) as mask:
                alpha = mask.getchannel("A")
                self.assertEqual(alpha.getpixel((0, 0)), 255)
                self.assertEqual(alpha.getpixel((3, 4)), 0)

        self.assertAlmostEqual(editable_ratio, 16 / 64)

    def test_roof_role_mask_selects_only_bottom_left_top_panel_mass_pixels(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "four-panel.png"
            image = Image.new("RGB", (100, 100), "white")
            for origin_x, origin_y in ((10, 10), (60, 10), (10, 60), (60, 60)):
                for x in range(origin_x, origin_x + 20):
                    for y in range(origin_y, origin_y + 20):
                        image.putpixel((x, y), (170, 105, 34))
            image.save(reference)

            mask = roof_mass_mask(reference, locked_sheet_panel_roles())

        self.assertEqual(mask.getpixel((15, 65)), 255)
        self.assertEqual(mask.getpixel((65, 65)), 0)
        self.assertEqual(mask.getpixel((15, 15)), 0)

    def test_roof_semantic_guard_reduces_facade_grid_only_inside_top_mass(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            locked_path = root / "locked.png"
            generated_path = root / "generated.png"
            locked = Image.new("RGB", (100, 100), "white")
            generated = Image.new("RGB", (100, 100), (245, 245, 245))
            for x in range(10, 40):
                for y in range(60, 90):
                    locked.putpixel((x, y), (170, 105, 34))
                    tone = 45 if (x // 2 + y // 2) % 2 == 0 else 210
                    generated.putpixel((x, y), (tone, tone, tone))
            locked.save(locked_path)
            generated.save(generated_path)
            outside_before = generated.getpixel((70, 70))

            evidence = apply_roof_semantic_guard(
                generated_path,
                locked_path,
                locked_sheet_panel_roles(),
            )

            with Image.open(generated_path) as guarded:
                outside_after = guarded.convert("RGB").getpixel((70, 70))

        self.assertEqual(evidence["status"], "applied")
        self.assertGreater(evidence["changed_pixel_count"], 0)
        self.assertLess(
            evidence["after_grid_score"],
            evidence["before_grid_score"],
        )
        self.assertEqual(outside_after, outside_before)

    def test_locked_output_composite_cannot_change_pixels_outside_mass(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            source_image = Image.new("RGB", (8, 8), "white")
            for x in range(2, 6):
                for y in range(3, 7):
                    source_image.putpixel((x, y), (170, 105, 34))
            source_image.save(source)
            prepared = _prepare_locked_mass_sheet(
                source,
                root / "prepared.png",
                "256x256",
            )
            mask_path, _ = _write_locked_mass_mask(
                prepared,
                root / "mask.png",
            )
            generated = root / "generated.png"
            Image.new("RGB", (256, 256), "black").save(generated)

            _composite_locked_mass_output(
                generated,
                prepared,
                mask_path,
            )

            with Image.open(generated) as result:
                self.assertEqual(result.convert("RGB").getpixel((0, 0)), (255, 255, 255))
                self.assertEqual(result.convert("RGB").getpixel((128, 128)), (0, 0, 0))
            Image.new("RGB", (256, 256), "white").save(generated)
            repaired = _composite_locked_mass_output(
                generated,
                prepared,
                mask_path,
            )
            with Image.open(generated) as result, Image.open(prepared) as locked:
                self.assertEqual(
                    result.convert("RGB").getpixel((128, 128)),
                    locked.convert("RGB").getpixel((128, 128)),
                )
            self.assertGreater(repaired, 0)
