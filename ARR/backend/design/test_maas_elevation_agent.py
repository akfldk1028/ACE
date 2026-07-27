import hashlib
import base64
from io import BytesIO
from io import StringIO
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import types
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from PIL import Image

from design.maas.aesthetic.adapters.openai_image import (
    OpenAIImageAdapter,
    _composite_locked_mass_output,
    _prepare_locked_mass_sheet,
    _safe_id as _openai_safe_id,
    _write_locked_mass_mask,
)
try:
    from design.maas.aesthetic.adapters.openai_elevation_critic import (
        OpenAIElevationCritic,
    )
except ImportError:
    OpenAIElevationCritic = None
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
try:
    from design.maas.agents.elevation_agent.multi_view_consistency import (
        _largest_foreground_component,
        evaluate_multi_view_consistency,
    )
except ImportError:
    _largest_foreground_component = None
    evaluate_multi_view_consistency = None
try:
    from design.maas.agents.elevation_agent.multi_view_proposal import (
        generate_multi_view_elevation_proposal,
    )
except ImportError:
    generate_multi_view_elevation_proposal = None
from design.maas.geometry_language import GeometryProgramBuilder, compile_geometry_program
from design.maas.single_execution import execute_single_mass
try:
    from design.maas.elevation_proposal_batch import (
        generate_execution_multi_view_elevation_proposal,
    )
except ImportError:
    generate_execution_multi_view_elevation_proposal = None


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


class _MultiViewImageAdapter:
    name = "recording-multi-view-image"

    def __init__(self, output_directory: Path) -> None:
        self.output_directory = output_directory
        self.calls = []

    def generate(self, job, reference):
        self.calls.append((job, reference))
        self.output_directory.mkdir(parents=True, exist_ok=True)
        view = job["view"]
        attempt = sum(call[0]["view"] == view for call in self.calls)
        output = self.output_directory / f"{view}-{attempt}.png"
        output.write_bytes(Path(reference.uri).read_bytes())
        return ProviderResult(
            provider=self.name,
            status="complete",
            assets=[{
                "asset_id": f"asset:test:{view}:{attempt}",
                "uri": str(output),
                "media_type": "image/png",
                "role": "generated_facade_view",
            }],
            metadata={
                "model": "fake-image-model",
                "request_id": f"request-{view}-{attempt}",
                "view": view,
                "retry_count": 0,
                "post_composite_silhouette_lock": True,
                "outside_mask_changed_pixels": 0,
            },
        )


class _RecordingMultiViewCritic:
    name = "recording-multi-view-critic"

    def __init__(self, results=None) -> None:
        self.results = list(results or [self.passed()])
        self.calls = []

    def evaluate(self, **kwargs):
        self.calls.append(kwargs)
        return self.results.pop(0)

    @staticmethod
    def passed():
        return {
            "schema_version": "arr.elevation_agent.multi_view_critic.v1",
            "status": "passed",
            "failed_views": [],
            "issues": [],
            "summary": "consistent",
            "request_count": 1,
            "paid_request_attempt_count": 1,
            "retry_count": 0,
        }

    @staticmethod
    def failed(*views):
        return {
            "schema_version": "arr.elevation_agent.multi_view_critic.v1",
            "status": "failed",
            "failed_views": list(views),
            "issues": [{
                "code": "corner_mismatch",
                "views": list(views),
                "message": "repair the shared corner",
                "repair_instruction": "match adjacent corner returns",
            }],
            "summary": "inconsistent",
            "request_count": 1,
            "paid_request_attempt_count": 1,
            "retry_count": 0,
        }


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

    def test_multi_view_gate_requires_exact_identity_and_four_facades(self):
        self.assertIsNotNone(evaluate_multi_view_consistency)
        compilation = compile_geometry_program(self._program())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = generate_elevation_bundle(
                compilation,
                root / "elevation",
                execution_id="multi-view-missing-left",
            )
            artifacts = self._copy_facade_artifacts(
                bundle,
                root / "generated",
                views=("front", "right", "back"),
            )
            result = evaluate_multi_view_consistency(bundle, artifacts)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failed_views"], ["left"])
        self.assertIn(
            "missing_required_view",
            {issue["code"] for issue in result["issues"]},
        )

    def test_multi_view_gate_rejects_pixels_changed_outside_locked_mask(self):
        self.assertIsNotNone(evaluate_multi_view_consistency)
        compilation = compile_geometry_program(self._program())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = generate_elevation_bundle(
                compilation,
                root / "elevation",
                execution_id="multi-view-outside-change",
            )
            artifacts = self._copy_facade_artifacts(
                bundle,
                root / "generated",
            )
            front_path = Path(artifacts["front"]["artifact"]["path"])
            with Image.open(front_path) as image:
                changed = image.convert("RGB")
            changed.putpixel((0, 0), (0, 0, 0))
            changed.save(front_path, format="PNG")
            artifacts["front"]["artifact"]["sha256"] = hashlib.sha256(
                front_path.read_bytes()
            ).hexdigest()

            result = evaluate_multi_view_consistency(bundle, artifacts)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failed_views"], ["front"])
        self.assertIn(
            "outside_mask_changed",
            {issue["code"] for issue in result["issues"]},
        )

    def test_multi_view_gate_tolerates_minor_bright_material_segmentation_noise(self):
        self.assertIsNotNone(evaluate_multi_view_consistency)
        compilation = compile_geometry_program(self._program())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = generate_elevation_bundle(
                compilation,
                root / "elevation",
                execution_id="multi-view-bright-material",
            )
            artifacts = self._copy_facade_artifacts(
                bundle,
                root / "generated",
            )
            front_path = Path(artifacts["front"]["artifact"]["path"])
            with Image.open(front_path) as image:
                changed = image.convert("RGBA")
            mask = sorted(_largest_foreground_component(changed))
            background = changed.getpixel((0, 0))
            for point in mask[::160]:
                changed.putpixel(point, background)
            changed.save(front_path, format="PNG")
            artifacts["front"]["artifact"]["sha256"] = hashlib.sha256(
                front_path.read_bytes()
            ).hexdigest()

            result = evaluate_multi_view_consistency(bundle, artifacts)

        front_check = result["checks"]["front"]
        self.assertGreaterEqual(front_check["silhouette_registration_iou"], 0.99)
        self.assertLess(front_check["silhouette_registration_iou"], 0.995)
        self.assertEqual(result["status"], "passed")

    def test_multi_view_proposal_calls_four_views_then_one_critic(self):
        self.assertIsNotNone(generate_multi_view_elevation_proposal)
        compilation = compile_geometry_program(self._program())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = generate_elevation_bundle(
                compilation,
                root / "elevation",
                execution_id="multi-view-initial-pass",
            )
            adapter = _MultiViewImageAdapter(root / "provider")
            critic = _RecordingMultiViewCritic()
            proposal = generate_multi_view_elevation_proposal(
                bundle,
                adapter=adapter,
                critic=critic,
                strategy=select_facade_strategy(self._program(), compilation),
            )

        self.assertEqual(
            [call[0]["view"] for call in adapter.calls],
            ["front", "right", "back", "left"],
        )
        self.assertEqual(len(critic.calls), 1)
        self.assertEqual(proposal["paid_request_attempt_count"], 5)
        self.assertEqual(proposal["status"], "accepted")

    def test_single_storey_multi_view_prompt_forbids_intermediate_floor_bands(self):
        self.assertIsNotNone(generate_multi_view_elevation_proposal)
        compilation = compile_geometry_program(self._program())
        strategy = select_facade_strategy(self._program(), compilation)
        strategy["measured_features"]["height_profile"] = "single_storey_low"

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = generate_elevation_bundle(
                compilation,
                root / "elevation",
                execution_id="multi-view-single-storey-prompt",
            )
            adapter = _MultiViewImageAdapter(root / "provider")
            generate_multi_view_elevation_proposal(
                bundle,
                adapter=adapter,
                critic=_RecordingMultiViewCritic(),
                strategy=strategy,
            )

        for job, _reference in adapter.calls:
            prompt = job["prompt"]["prompt"].lower()
            self.assertIn("exactly one storey", prompt)
            self.assertIn("no intermediate floor", prompt)

    def test_multi_view_proposal_repairs_only_failed_view_once(self):
        self.assertIsNotNone(generate_multi_view_elevation_proposal)
        compilation = compile_geometry_program(self._program())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = generate_elevation_bundle(
                compilation,
                root / "elevation",
                execution_id="multi-view-repair-right",
            )
            adapter = _MultiViewImageAdapter(root / "provider")
            critic = _RecordingMultiViewCritic([
                _RecordingMultiViewCritic.failed("right"),
                _RecordingMultiViewCritic.passed(),
            ])
            proposal = generate_multi_view_elevation_proposal(
                bundle,
                adapter=adapter,
                critic=critic,
                strategy=select_facade_strategy(self._program(), compilation),
            )

        self.assertEqual(
            [call[0]["view"] for call in adapter.calls],
            ["front", "right", "back", "left", "right"],
        )
        self.assertEqual(len(critic.calls), 2)
        self.assertEqual(proposal["paid_request_attempt_count"], 7)
        self.assertEqual(proposal["repair_count_by_view"]["right"], 1)
        self.assertEqual(proposal["status"], "accepted")

    def test_accepted_matching_multi_view_manifest_is_reused(self):
        self.assertIsNotNone(generate_multi_view_elevation_proposal)
        compilation = compile_geometry_program(self._program())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = generate_elevation_bundle(
                compilation,
                root / "elevation",
                execution_id="multi-view-reuse",
            )
            adapter = _MultiViewImageAdapter(root / "provider")
            critic = _RecordingMultiViewCritic()
            strategy = select_facade_strategy(self._program(), compilation)
            first = generate_multi_view_elevation_proposal(
                bundle,
                adapter=adapter,
                critic=critic,
                strategy=strategy,
            )
            second = generate_multi_view_elevation_proposal(
                bundle,
                adapter=adapter,
                critic=critic,
                strategy=strategy,
            )

        self.assertEqual(first["status"], "accepted")
        self.assertEqual(second["status"], "accepted")
        self.assertTrue(second["skipped_existing"])
        self.assertEqual(len(adapter.calls), 4)
        self.assertEqual(len(critic.calls), 1)

    def test_legacy_accepted_manifest_is_archived_and_regenerated(self):
        self.assertIsNotNone(generate_multi_view_elevation_proposal)
        compilation = compile_geometry_program(self._program())

        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = generate_elevation_bundle(
                compilation,
                root / "elevation",
                execution_id="multi-view-pipeline-upgrade",
            )
            adapter = _MultiViewImageAdapter(root / "provider")
            critic = _RecordingMultiViewCritic([
                _RecordingMultiViewCritic.passed(),
                _RecordingMultiViewCritic.passed(),
            ])
            strategy = select_facade_strategy(self._program(), compilation)
            first = generate_multi_view_elevation_proposal(
                bundle,
                adapter=adapter,
                critic=critic,
                strategy=strategy,
            )
            manifest_path = Path(first["manifest_path"])
            legacy = json.loads(manifest_path.read_text(encoding="utf-8"))
            legacy.pop("pipeline_version", None)
            manifest_path.write_text(
                json.dumps(legacy, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            second = generate_multi_view_elevation_proposal(
                bundle,
                adapter=adapter,
                critic=critic,
                strategy=strategy,
            )
            archived = list(
                (manifest_path.parent / "history").glob("*/proposal.json")
            )

        self.assertFalse(second["skipped_existing"])
        self.assertEqual(len(adapter.calls), 8)
        self.assertEqual(len(critic.calls), 2)
        self.assertEqual(len(archived), 1)

    def test_execution_multi_view_proposal_updates_one_passport_graph(self):
        self.assertIsNotNone(generate_execution_multi_view_elevation_proposal)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            execution = execute_single_mass(
                self._program(),
                output_root=root,
                execution_id="multi-view-passport",
            )
            graph_id = execution.passport["activation_graph"]["graph_id"]
            adapter = _MultiViewImageAdapter(root / "provider")
            critic = _RecordingMultiViewCritic()

            proposal = generate_execution_multi_view_elevation_proposal(
                root,
                "multi-view-passport",
                adapter=adapter,
                critic=critic,
            )
            passport = json.loads(
                (execution.output_directory / "mass.png.passport.json").read_text(
                    encoding="utf-8"
                )
            )

        edges = {
            edge["relation"]: edge
            for edge in passport["activation_graph"]["edges"]
        }
        self.assertEqual(proposal["status"], "accepted")
        self.assertEqual(
            passport["elevation_evidence"]["multi_view_proposal"]["status"],
            "accepted",
        )
        self.assertEqual(passport["activation_graph"]["graph_id"], graph_id)
        self.assertEqual(edges["accepts_multi_view_elevation"]["activation"], 1.0)

    def test_multi_view_artifact_api_serves_only_allow_listed_files(self):
        self.assertIsNotNone(generate_execution_multi_view_elevation_proposal)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=root):
                execute_single_mass(
                    self._program(),
                    output_root=root,
                    execution_id="multi-view-http",
                )
                generate_execution_multi_view_elevation_proposal(
                    root,
                    "multi-view-http",
                    adapter=_MultiViewImageAdapter(root / "provider"),
                    critic=_RecordingMultiViewCritic(),
                )
                response = self.client.get(
                    "/design/maas/single-executions/multi-view-http/"
                    "elevation-proposals/multi-view-alt-01/front/",
                )
                payload = b"".join(response.streaming_content)
                response.close()
                denied = self.client.get(
                    "/design/maas/single-executions/multi-view-http/"
                    "elevation-proposals/multi-view-alt-01/secret/",
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(payload.startswith(b"\x89PNG"))
        self.assertEqual(denied.status_code, 404)

    def test_multi_view_management_command_targets_one_execution(self):
        recorded = {
            "status": "accepted",
            "paid_request_attempt_count": 5,
        }
        stdout = StringIO()
        with TemporaryDirectory() as directory, patch(
            "design.management.commands.generate_maas_elevation_proposals."
            "generate_execution_multi_view_elevation_proposal",
            return_value=recorded,
            create=True,
        ) as generate:
            call_command(
                "generate_maas_elevation_proposals",
                mode="multi-view",
                execution_id="command-multi-view",
                output_root=directory,
                stdout=stdout,
            )

        self.assertEqual(generate.call_count, 1)
        args, kwargs = generate.call_args
        self.assertEqual(args[1], "command-multi-view")
        self.assertEqual(kwargs["adapter"].__class__.__name__, "OpenAIImageAdapter")
        self.assertEqual(kwargs["critic"].__class__.__name__, "OpenAIElevationCritic")
        self.assertEqual(json.loads(stdout.getvalue())["status"], "accepted")

    def test_multi_view_evidence_api_serves_only_proposal_and_critic_json(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=root):
                execute_single_mass(
                    self._program(),
                    output_root=root,
                    execution_id="multi-view-evidence-http",
                )
                generate_execution_multi_view_elevation_proposal(
                    root,
                    "multi-view-evidence-http",
                    adapter=_MultiViewImageAdapter(root / "provider"),
                    critic=_RecordingMultiViewCritic(),
                )
                proposal = self.client.get(
                    "/design/maas/single-executions/multi-view-evidence-http/"
                    "elevation-proposals/multi-view-alt-01/evidence/proposal/",
                )
                denied = self.client.get(
                    "/design/maas/single-executions/multi-view-evidence-http/"
                    "elevation-proposals/multi-view-alt-01/evidence/secret/",
                )

        self.assertEqual(proposal.status_code, 200)
        self.assertEqual(proposal.json()["status"], "accepted")
        self.assertEqual(denied.status_code, 404)

    @staticmethod
    def _copy_facade_artifacts(
        bundle,
        output_directory: Path,
        *,
        views=("front", "right", "back", "left"),
    ):
        output_directory.mkdir(parents=True, exist_ok=True)
        identity = {
            "execution_id": bundle["execution_id"],
            "program_hash": bundle["program_hash"],
            "geometry_hash": bundle["geometry_hash"],
        }
        source_views = {
            row["view"]: row
            for row in bundle["views"]
            if row["view"] in views
        }
        artifacts = {}
        for view in views:
            source = source_views[view]
            source_path = Path(source["path"])
            output_path = output_directory / f"{view}.png"
            output_path.write_bytes(source_path.read_bytes())
            artifacts[view] = {
                "view": view,
                "identity": {**identity, "view": view},
                "source": {
                    "path": str(source_path),
                    "sha256": source["sha256"],
                },
                "artifact": {
                    "path": str(output_path),
                    "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
                },
            }
        return artifacts

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

    def test_openai_locked_elevation_view_uses_one_edit_without_input_fidelity(self):
        with TemporaryDirectory() as directory:
            result, requests, _source_path = self._run_locked_elevation_adapter(
                Path(directory),
            )

        self.assertEqual(result.status, "complete")
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["model"], "gpt-image-2")
        self.assertEqual(requests[0]["n"], 1)
        self.assertIn("mask", requests[0])
        self.assertNotIn("input_fidelity", requests[0])
        self.assertEqual(result.metadata["view"], "front")
        self.assertEqual(result.metadata["retry_count"], 0)

    def test_openai_locked_elevation_view_preserves_all_outside_pixels(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            result, _requests, source_path = self._run_locked_elevation_adapter(root)
            output_path = Path(result.assets[0]["uri"])
            with Image.open(source_path) as source, Image.open(output_path) as output:
                source_rgb = source.convert("RGB")
                output_rgb = output.convert("RGB")
                self.assertEqual(output_rgb.size, source_rgb.size)
                self.assertEqual(output_rgb.getpixel((0, 0)), source_rgb.getpixel((0, 0)))
                self.assertEqual(output_rgb.getpixel((8, 8)), source_rgb.getpixel((8, 8)))

        self.assertTrue(result.metadata["post_composite_silhouette_lock"])
        self.assertEqual(result.metadata["outside_mask_changed_pixels"], 0)

    def test_openai_multi_view_critic_submits_four_images_once_and_parses_schema(self):
        self.assertIsNotNone(OpenAIElevationCritic)
        parsed = {
            "status": "pass",
            "failed_views": [],
            "issues": [],
            "summary": "All four facade views share one coherent system.",
        }
        response = types.SimpleNamespace(
            id="response-elevation-critic",
            output_text=json.dumps(parsed),
            usage=types.SimpleNamespace(
                model_dump=lambda: {
                    "input_tokens": 120,
                    "output_tokens": 30,
                    "total_tokens": 150,
                },
            ),
        )
        requests = []

        class _RawResponse:
            headers = {"x-request-id": "request-elevation-critic"}

            @staticmethod
            def parse():
                return response

        class _Responses:
            def __init__(self):
                self.with_raw_response = self

            @staticmethod
            def create(**kwargs):
                requests.append(kwargs)
                return _RawResponse()

        class _OpenAI:
            def __init__(self, **_kwargs):
                self.responses = _Responses()

        with TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = {}
            for view, color in zip(
                ("front", "right", "back", "left"),
                ("red", "green", "blue", "yellow"),
            ):
                source_path = root / f"{view}-source.png"
                Image.new("RGB", (32, 32), "white").save(source_path)
                path = root / f"{view}.png"
                Image.new("RGB", (32, 32), color).save(path)
                artifacts[view] = {
                    "view": view,
                    "source": {
                        "path": str(source_path),
                        "sha256": hashlib.sha256(
                            source_path.read_bytes()
                        ).hexdigest(),
                    },
                    "artifact": {
                        "path": str(path),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    },
                }
            montage = root / "critic-montage.png"
            Image.new("RGB", (64, 64), "white").save(montage)
            critic = OpenAIElevationCritic()
            with patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "test-key",
                    "OPENAI_ELEVATION_CRITIC_MODEL": "test-critic-model",
                },
                clear=False,
            ), patch.dict(
                sys.modules,
                {"openai": types.SimpleNamespace(OpenAI=_OpenAI)},
            ):
                evidence = critic.evaluate(
                    identity={
                        "execution_id": "critic-execution",
                        "program_hash": "critic-program",
                        "geometry_hash": "critic-geometry",
                    },
                    strategy={"strategy_id": "critic-strategy"},
                    artifacts=artifacts,
                    montage_path=montage,
                )

        content = requests[0]["input"][0]["content"]
        self.assertEqual(sum(part["type"] == "input_image" for part in content), 8)
        critic_text = " ".join(
            part["text"]
            for part in content
            if part["type"] == "input_text"
        ).lower()
        self.assertIn("locked source", critic_text)
        self.assertIn("generated output", critic_text)
        self.assertEqual(requests[0]["text"]["format"]["type"], "json_schema")
        self.assertTrue(requests[0]["text"]["format"]["strict"])
        self.assertEqual(evidence["status"], "passed")
        self.assertEqual(evidence["response_id"], "response-elevation-critic")
        self.assertEqual(evidence["request_id"], "request-elevation-critic")
        self.assertEqual(evidence["usage"]["total_tokens"], 150)
        self.assertEqual(evidence.get("paid_request_attempt_count"), 1)
        self.assertEqual(evidence["retry_count"], 0)

    def test_openai_multi_view_asset_identity_includes_view_and_attempt(self):
        base = {
            "source_bundle_id": "execution-1",
            "candidate_id": "geometry-1",
        }

        front = _openai_safe_id({**base, "view": "front", "attempt": 1})
        right = _openai_safe_id({**base, "view": "right", "attempt": 1})
        repaired_front = _openai_safe_id({
            **base,
            "view": "front",
            "attempt": 2,
        })

        self.assertNotEqual(front, right)
        self.assertNotEqual(front, repaired_front)

    @staticmethod
    def _run_locked_elevation_adapter(root: Path):
        source = Image.new("RGB", (64, 64), (248, 248, 246))
        for x in range(16, 48):
            for y in range(20, 54):
                source.putpixel((x, y), (190, 190, 187))
        source_path = root / "front.png"
        source.save(source_path, format="PNG")
        generated = Image.new("RGB", (1024, 1024), (15, 25, 35))
        generated_buffer = BytesIO()
        generated.save(generated_buffer, format="PNG")
        response = types.SimpleNamespace(
            data=[types.SimpleNamespace(
                b64_json=base64.b64encode(generated_buffer.getvalue()).decode(),
                url=None,
            )],
            usage=None,
        )
        requests = []

        class _RawResponse:
            headers = {"x-request-id": "locked-front-request"}

            @staticmethod
            def parse():
                return response

        class _Images:
            def __init__(self):
                self.with_raw_response = self

            @staticmethod
            def edit(**kwargs):
                requests.append(kwargs)
                return _RawResponse()

        class _OpenAI:
            def __init__(self, **_kwargs):
                self.images = _Images()

        adapter = OpenAIImageAdapter(output_dir=root / "provider")
        reference = RenderedReference(
            asset_id="asset:locked-elevation:front",
            uri=str(source_path),
            metadata={
                "reference_type": "locked_elevation_view",
                "view": "front",
                "identity": {
                    "execution_id": "locked-front",
                    "program_hash": "program-front",
                    "geometry_hash": "geometry-front",
                },
            },
        )
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_IMAGE_MODEL": "gpt-image-2",
                "OPENAI_IMAGE_SIZE": "1024x1024",
            },
            clear=False,
        ), patch.dict(
            sys.modules,
            {"openai": types.SimpleNamespace(OpenAI=_OpenAI)},
        ):
            result = adapter.generate(
                {
                    "source_bundle_id": "locked-front",
                    "candidate_id": "geometry-front",
                    "view": "front",
                    "prompt": {
                        "prompt": "shared stone and glass facade",
                        "negative_prompt": "changed mass",
                    },
                },
                reference,
            )
        return result, requests, source_path

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
