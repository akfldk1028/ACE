import json
from dataclasses import replace
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from django.core.management import call_command
from PIL import Image

from design.maas.agents.shared.types import AgentEvidence
from design.maas.aesthetic.contracts import ProviderResult
from design.maas.elevation_proposal_batch import (
    generate_execution_elevation_proposal,
)
from design.maas.geometry_language import GeometryProgramBuilder, compile_geometry_program
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.single_execution import execute_single_mass
from design.maas.single_execution.vlm_review import _resolve_building_type


def _box_program():
    builder = GeometryProgramBuilder("single_mass_box")
    root = builder.add(
        "primitive",
        "box",
        parameters={"width": 12, "depth": 8, "height": 5},
        semantic_role="base_seed",
    )
    return builder.build(root, family="single_mass_test")


def _certified_visual_compilation():
    capacity = compile_geometry_program(_box_program())
    minimum_z = float(capacity.metrics["bounds"][0][2])
    maximum_z = float(capacity.metrics["bounds"][1][2])
    height = maximum_z - minimum_z
    return replace(
        capacity,
        vertices=tuple(
            (x, y, (z - minimum_z) / height)
            for x, y, z in capacity.vertices
        ),
        geometry_hash="f" * 64,
        metrics={
            **capacity.metrics,
            "geometry_authority": "certified_projected_visual_mesh",
            "exact_payload_hash": "e" * 64,
            "capacity_geometry_hash": capacity.geometry_hash,
            "coordinate_space": (
                "capacity_source_centroid_local_xy_normalized_z"
            ),
        },
    )


class _SingleExecutionImageAdapter:
    name = "single-execution-test-image"

    def __init__(self, output_directory):
        self.output_directory = Path(output_directory)
        self.calls = []

    def generate(self, job, reference):
        self.calls.append((job, reference))
        output = self.output_directory / "provider-alt.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (4, 4), "white").save(output)
        return ProviderResult(
            provider=self.name,
            status="complete",
            assets=[{
                "asset_id": "asset:test:single-execution-alt",
                "uri": str(output),
                "media_type": "image/png",
            }],
            metadata={"model": "fake-image-model", "request_id": "fake-request"},
        )


class _RaisingImageAdapter:
    name = "raising-image"

    @staticmethod
    def generate(_job, _reference):
        raise RuntimeError("provider unavailable")


class MaasSingleExecutionTest(SimpleTestCase):
    def test_certified_normalized_z_is_rendered_at_physical_capacity_height(self):
        capacity = compile_geometry_program(_box_program())
        certified = replace(
            capacity,
            vertices=tuple((x, y, z / 5.0) for x, y, z in capacity.vertices),
            geometry_hash="f" * 64,
            metrics={
                "geometry_authority": "certified_projected_visual_mesh",
                "exact_payload_hash": "e" * 64,
                "coordinate_space": (
                    "capacity_source_centroid_local_xy_normalized_z"
                ),
                "capacity_geometry_hash": capacity.geometry_hash,
                "capacity_replay_metrics": capacity.metrics,
            },
        )
        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                certified.program,
                output_root=directory,
                execution_id="physical-height",
                execution_mode="exact_replay",
                validated_compilation=certified,
            )

        elevation = result.passport["elevation_evidence"]
        self.assertEqual(result.geometry_hash, "f" * 64)
        self.assertEqual(elevation["geometry_hash"], "f" * 64)
        self.assertEqual(
            elevation["condition_pack"]["floor_guides_m"],
            [0.0, 3.3, 5.0],
        )
        self.assertEqual(
            elevation["condition_pack"]["facade_planes"][0]["extent"][1],
            5.0,
        )
        self.assertGreater(
            elevation["condition_pack"]["facade_planes"][0]["extent"][1],
            1.0,
        )
        front_bounds = elevation["condition_pack"]["silhouette"]["front"][
            "projected_bounds"
        ]
        self.assertEqual(front_bounds[1][1] - front_bounds[0][1], 5.0)

    def test_exact_replay_uses_certified_visual_compilation_for_every_identity(self):
        certified = _certified_visual_compilation()
        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                certified.program,
                output_root=directory,
                execution_id="certified-visual-replay",
                execution_mode="exact_replay",
                validated_compilation=certified,
            )

            passport = result.passport

        self.assertEqual(result.geometry_hash, "f" * 64)
        self.assertEqual(passport["geometry_hash"], "f" * 64)
        self.assertEqual(
            passport["agent_collaboration"]["identity"]["geometry_hash"],
            "f" * 64,
        )
        self.assertEqual(
            passport["elevation_evidence"]["geometry_hash"],
            "f" * 64,
        )

    def test_exact_replay_rejects_certified_compilation_for_another_program(self):
        certified = _certified_visual_compilation()
        other_builder = GeometryProgramBuilder("other")
        other_root = other_builder.add(
            "primitive",
            "box",
            parameters={"width": 4, "depth": 4, "height": 4},
        )
        other = other_builder.build(other_root)

        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                ValueError,
                "validated compilation program identity mismatch",
            ):
                execute_single_mass(
                    other,
                    output_root=directory,
                    execution_id="wrong-program",
                    execution_mode="exact_replay",
                    validated_compilation=certified,
                )

    def test_exact_replay_keeps_certified_pre_normalization_program_identity(self):
        raw_program = GeometryProgram(
            name="raw-box",
            root_id="root",
            nodes=(
                GeometryNode(
                    id="root",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 12, "depth": 8, "height": 5},
                ),
            ),
        )
        compiled = compile_geometry_program(raw_program)
        certified = replace(
            compiled,
            program=raw_program,
            vertices=tuple(
                (x, y, z / 5.0)
                for x, y, z in compiled.vertices
            ),
            geometry_hash="f" * 64,
            metrics={
                **compiled.metrics,
                "geometry_authority": "certified_projected_visual_mesh",
                "exact_payload_hash": "e" * 64,
                "capacity_geometry_hash": compiled.geometry_hash,
                "coordinate_space": (
                    "capacity_source_centroid_local_xy_normalized_z"
                ),
            },
        )

        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                raw_program,
                output_root=directory,
                execution_id="pre-normalization-identity",
                execution_mode="exact_replay",
                validated_compilation=certified,
            )

        self.assertEqual(result.program_hash, raw_program.program_hash())
        self.assertEqual(result.geometry_hash, "f" * 64)

    def test_archive_capacity_replay_preserves_selected_band_and_floor_contract(self):
        from design.maas.geometry_language.executed_archive import (
            _archived_capacity_evidence,
        )

        floor_contract = {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "floor_contract_hash": "floor-contract-123",
            "floor_capacity_plan_hash": "floor-plan-123",
            "hard_pass": True,
            "plates": [],
        }
        artifact = {
            "capacityAlternative": {
                "requested_capacity_alternative_id": "brief_target",
                "target_hard_pass": False,
                "selectable_capacity_alternative_id": "spatial_reserve",
                "selectable_capacity_hard_pass": True,
            },
            "executionPassport": {
                "stages": [{
                    "id": "capacity",
                    "evidence": {
                        "measurement": {"utilization_ratio": 0.7033},
                        "shared_floor_contract": floor_contract,
                        "floor_contract_hash": "floor-contract-123",
                    },
                }],
            },
        }

        capacity = _archived_capacity_evidence(artifact)

        self.assertTrue(capacity["hard_pass"])
        self.assertEqual(
            capacity["shared_floor_contract"]["floor_contract_hash"],
            "floor-contract-123",
        )
        self.assertEqual(capacity["measurement"]["utilization_ratio"], 0.7033)

    def test_passport_replay_restores_stage_status_for_elevation_handoff(self):
        from design.maas.single_execution.replay import (
            downstream_evidence_from_passport,
        )

        passport = {
            "stages": [
                {
                    "id": stage_id,
                    "status": "passed",
                    "evidence": (
                        {
                            "selected": True,
                            "shared_floor_contract": {
                                "schema_version": "arr.maas.shared_floor_contract.v1",
                                "floor_contract_hash": "floor-contract-123",
                                "hard_pass": True,
                            },
                        }
                        if stage_id == "selector"
                        else (
                            {
                                "hard_pass": True,
                                "shared_floor_contract": {
                                    "schema_version": "arr.maas.shared_floor_contract.v1",
                                    "floor_contract_hash": "floor-contract-123",
                                    "hard_pass": True,
                                },
                            }
                            if stage_id == "capacity"
                            else {"hard_pass": True}
                        )
                    ),
                }
                for stage_id in (
                    "site",
                    "capacity",
                    "law",
                    "parking",
                    "program_fit",
                    "selector",
                )
            ],
        }

        replay = downstream_evidence_from_passport(passport)

        self.assertEqual(replay["site"]["status"], "passed")
        self.assertTrue(replay["selector"]["hard_pass"])
        self.assertEqual(
            replay["shared_floor_contract"]["floor_contract_hash"],
            "floor-contract-123",
        )

    def test_specialist_evidence_materializes_the_same_downstream_flow_nodes(self):
        def evidence(agent, status):
            def execute(identity, _accumulated):
                return AgentEvidence(
                    evidence_id=f"evidence:{agent}",
                    agent=agent,
                    status=status,
                    summary=f"{agent} status={status}",
                    identity=identity,
                    evidence={"source": "test-specialist"},
                )

            return execute

        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                _box_program(),
                output_root=directory,
                execution_id="specialist-flow-nodes",
                collaboration_executors={
                    "maas_geometry_agent": evidence("maas_geometry_agent", "passed"),
                    "law_graph_agent": evidence("law_graph_agent", "needs_evidence"),
                    "parking_agent": evidence("parking_agent", "needs_evidence"),
                    "review_agent": evidence("review_agent", "needs_evidence"),
                },
            )

        stages = {row["id"]: row for row in result.passport["stages"]}
        nodes = {
            row["id"]: row
            for row in result.passport["activation_graph"]["nodes"]
        }
        self.assertEqual(stages["law"]["status"], "needs_evidence")
        self.assertEqual(stages["parking"]["status"], "needs_evidence")
        self.assertEqual(stages["selector"]["status"], "needs_evidence")
        self.assertEqual(stages["law"]["evidence"]["source_agent"], "law_graph_agent")
        self.assertEqual(stages["parking"]["evidence"]["source_agent"], "parking_agent")
        self.assertEqual(nodes["flow:law"]["activation"], 1.0)
        self.assertEqual(nodes["flow:parking"]["activation"], 1.0)
        self.assertEqual(nodes["flow:selector"]["activation"], 1.0)

    def test_single_execution_catalog_exposes_one_isometric_mass_thumbnail(self):
        with TemporaryDirectory() as directory:
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=directory):
                result = execute_single_mass(
                    _box_program(),
                    output_root=directory,
                    execution_id="thumbnail-source",
                )
                run_id = "single-execution:thumbnail-source"
                manifest = self.client.get(
                    "/design/maas/executed-masses/",
                    {"run_id": run_id},
                ).json()
                run = next(row for row in manifest["runs"] if row["run_id"] == run_id)

                self.assertEqual(run["geometry_hash"], result.geometry_hash)
                self.assertEqual(run["site_context_status"], "unresolved")
                self.assertEqual(
                    run["thumbnail_url"],
                    "/design/maas/single-executions/thumbnail-source/thumbnail/",
                )

                response = self.client.get(run["thumbnail_url"])
                self.assertEqual(response.status_code, 200)
                payload = b"".join(response.streaming_content)
                response.close()
                with Image.open(BytesIO(payload)) as thumbnail:
                    self.assertEqual(thumbnail.format, "PNG")
                    self.assertLess(thumbnail.width, 900)
                    self.assertLess(thumbnail.height, 680)

    def test_single_execution_catalog_maps_book_projection_to_graph_node_id(self):
        program = _box_program()
        program.metadata["book_recursive_projection"] = {
            "active": True,
            "scope_label": "1/1",
            "scope_orientation": "long_axis",
            "ordered_verbs": ["offset"],
        }
        with TemporaryDirectory() as directory:
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=directory):
                execute_single_mass(
                    program,
                    output_root=directory,
                    execution_id="book-offset-graph-path",
                    execution_mode="fresh_synthesis",
                )
                manifest = self.client.get(
                    "/design/maas/executed-masses/",
                    {"run_id": "single-execution:book-offset-graph-path"},
                ).json()

        self.assertEqual(
            manifest["masses"][0]["book_principle_id"],
            "book:operative:offset",
        )
        self.assertEqual(manifest["masses"][0]["book_scope"], "1/1")
        self.assertEqual(manifest["masses"][0]["book_orientation"], "long_axis")
        graph = self.client.get("/design/maas/language-system/").json()["exploration_graph"]
        node_ids = {node["id"] for node in graph["nodes"]}
        self.assertIn("book:orientation:long_axis", node_ids)
        self.assertIn("book:operative:offset", node_ids)
        reachable = {"book:orientation:long_axis"}
        while True:
            expanded = reachable | {
                edge["target"]
                for edge in graph["edges"]
                if edge["source"] in reachable and edge.get("scope") == "execution"
            }
            if expanded == reachable:
                break
            reachable = expanded
        self.assertIn("book:operative:offset", reachable)

    def test_vlm_reference_identity_uses_nested_program_projection(self):
        program = _box_program()
        program.metadata.pop("building_type", None)
        program.metadata.pop("program_id", None)
        program.metadata["family"] = "agent_stepped_mass"
        program.metadata["program_projection"] = {
            "program_id": "neighborhood_living",
            "building_type": "neighborhood housing",
        }

        self.assertEqual(
            _resolve_building_type(program.metadata, explicit=""),
            "neighborhood housing",
        )

    def test_one_program_materializes_a_fast_auditable_execution_bundle(self):
        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                _box_program(),
                output_root=Path(directory),
                execution_id="test-box",
            )

            self.assertEqual(result.status, "geometry_ready")
            self.assertTrue(result.geometry_ready)
            self.assertEqual(result.full_flow_status, "needs_evidence")
            self.assertEqual(
                list(result.timings_ms),
                ["parse_validate", "compile", "geometry_gate", "render", "elevation_agent", "agent_collaboration", "passport", "persist", "total"],
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
                "needs_evidence",
            )
            self.assertEqual(
                passport["elevation_evidence"]["image_proposal"]["status"],
                "not_evaluated",
            )
            self.assertEqual(
                passport["elevation_evidence"]["image_proposal"]["request_count"],
                0,
            )

    def test_image_adapter_is_bound_once_to_passport_graph_and_proposal_api(self):
        with TemporaryDirectory() as directory:
            adapter = _SingleExecutionImageAdapter(Path(directory) / "provider")
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=directory):
                result = execute_single_mass(
                    _box_program(),
                    output_root=directory,
                    execution_id="image-proposal-bound",
                    elevation_image_adapter=adapter,
                )
                response = self.client.get(
                    "/design/maas/single-executions/"
                    "image-proposal-bound/elevation-proposals/alt-01/",
                )
                payload = b"".join(response.streaming_content)
                response.close()

        self.assertEqual(len(adapter.calls), 1)
        proposal = result.passport["elevation_evidence"]["image_proposal"]
        self.assertEqual(proposal["status"], "complete")
        self.assertEqual(proposal["identity"]["execution_id"], result.execution_id)
        self.assertEqual(proposal["identity"]["program_hash"], result.program_hash)
        self.assertEqual(proposal["identity"]["geometry_hash"], result.geometry_hash)
        nodes = {
            row["id"]: row
            for row in result.passport["activation_graph"]["nodes"]
        }
        edges = {
            row["relation"]: row
            for row in result.passport["activation_graph"]["edges"]
        }
        self.assertEqual(nodes["elevation:image_agent"]["status"], "complete")
        self.assertEqual(nodes["elevation:proposal"]["status"], "complete")
        self.assertIn(
            "Architectural Render Agent",
            nodes["elevation:image_agent"]["label"],
        )
        self.assertIn(
            "Render ALT 01",
            nodes["elevation:proposal"]["label"],
        )
        self.assertEqual(edges["requests_facade_proposal"]["activation"], 1.0)
        self.assertEqual(edges["generates_facade_proposal"]["activation"], 1.0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(payload.startswith(b"\x89PNG"))

    def test_image_provider_failure_does_not_discard_technical_elevations(self):
        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                _box_program(),
                output_root=directory,
                execution_id="image-proposal-failed",
                elevation_image_adapter=_RaisingImageAdapter(),
            )

        elevation = result.passport["elevation_evidence"]
        self.assertEqual(elevation["status"], "generated")
        self.assertEqual(elevation["view_count"], 6)
        self.assertEqual(elevation["image_proposal"]["status"], "failed")
        self.assertEqual(elevation["image_proposal"]["request_count"], 1)
        self.assertIn("provider unavailable", elevation["image_proposal"]["issues"][0]["message"])

    def test_explicit_second_stage_generates_once_and_is_idempotent(self):
        with TemporaryDirectory() as directory:
            execute_single_mass(
                _box_program(),
                output_root=directory,
                execution_id="explicit-proposal-stage",
            )
            adapter = _SingleExecutionImageAdapter(Path(directory) / "provider")
            first = generate_execution_elevation_proposal(
                directory,
                "explicit-proposal-stage",
                adapter=adapter,
            )
            second = generate_execution_elevation_proposal(
                directory,
                "explicit-proposal-stage",
                adapter=adapter,
            )
            passport = json.loads(
                (
                    Path(directory)
                    / "explicit-proposal-stage"
                    / "mass.png.passport.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(len(adapter.calls), 1)
        self.assertFalse(first["skipped_existing"])
        self.assertTrue(second["skipped_existing"])
        self.assertEqual(
            passport["elevation_evidence"]["image_proposal"]["status"],
            "complete",
        )
        nodes = {
            row["id"]: row
            for row in passport["activation_graph"]["nodes"]
        }
        self.assertEqual(nodes["elevation:proposal"]["activation"], 1.0)

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

    def test_execution_bundle_is_immutable_and_cannot_be_overwritten(self):
        with TemporaryDirectory() as directory:
            execute_single_mass(
                _box_program(),
                output_root=directory,
                execution_id="immutable-run",
            )
            changed = _box_program().to_dict()
            changed["nodes"][0]["parameters"]["width"] = 18

            with self.assertRaisesRegex(ValueError, "already exists"):
                execute_single_mass(
                    changed,
                    output_root=directory,
                    execution_id="immutable-run",
                )

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
                    data=json.dumps({
                        "program": _box_program().to_dict(),
                        "execution_mode": "fresh_synthesis",
                    }),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 201)
                payload = response.json()
                self.assertEqual(payload["execution_mode"], "fresh_synthesis")
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

    def test_vlm_review_endpoint_is_bounded_and_updates_the_same_passport(self):
        downstream = {
            stage_id: {"evaluated": True, "hard_pass": True, "selected": stage_id == "selector"}
            for stage_id in ("site", "capacity", "law", "parking", "program_fit", "selector")
        }
        mock_result = {
            "schema_version": "arr.maas.vlm_concept_scores.v1",
            "prompt_contract_version": "test-prompt-v1",
            "provider": "openai",
            "model": "test-paid-vlm",
            "response_id": "response-test",
            "cache_hit": False,
            "program_fit_hard_pass": True,
            "concept_scores": {"gesture_clarity": 0.82},
            "critic_actions": [],
            "rationale": "coherent mass",
            "api_usage": {"input_tokens": 120, "output_tokens": 20, "total_tokens": 140},
            "reference_massing_gate": {"accepted": [], "rejected": []},
            "maas_causal_context": {},
        }
        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                _box_program(),
                output_root=directory,
                execution_id="vlm-bounded",
                downstream_evidence=downstream,
            )
            with override_settings(MAAS_SINGLE_EXECUTION_ROOT=directory), patch(
                "design.maas.single_execution.vlm_review.retrieve_geometry_reference_matches",
                return_value=[{"source_id": "ref-1"}, {"source_id": "ref-2"}],
            ) as retrieve, patch(
                "design.maas.single_execution.vlm_review.score_geometry_program_with_openai_vlm",
                return_value=mock_result,
            ) as score:
                response = self.client.post(
                    "/design/maas/single-executions/vlm-bounded/vlm-review/",
                    data=json.dumps({"reference_limit": 2}),
                    content_type="application/json",
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["hard_pass"])
            self.assertEqual(payload["cost_observation"]["max_http_attempts"], 3)
            self.assertEqual(payload["cost_observation"]["usage"]["total_tokens"], 140)
            self.assertEqual(retrieve.call_args.kwargs["limit"], 2)
            self.assertEqual(score.call_args.kwargs["max_retries"], 0)
            self.assertFalse(score.call_args.kwargs["write_passport_sidecar"])
            passport = json.loads(result.passport_path.read_text(encoding="utf-8"))
            vlm_stage = next(stage for stage in passport["stages"] if stage["id"] == "vlm")
            self.assertEqual(vlm_stage["status"], "live_scored")
            self.assertTrue(vlm_stage["evidence"]["hard_pass"])
            self.assertEqual(passport["status"], "needs_evidence")

    def test_management_command_executes_one_built_in_shape(self):
        with TemporaryDirectory() as directory:
            output = StringIO()
            call_command(
                "execute_maas_single_mass",
                shape_index=10,
                execution_mode="fresh_synthesis",
                output_root=directory,
                stdout=output,
            )

            payload = json.loads(output.getvalue())
            self.assertEqual(payload["execution_mode"], "fresh_synthesis")
            self.assertEqual(payload["status"], "geometry_ready")
            self.assertTrue(Path(payload["artifacts"]["preview"]).is_file())
            self.assertLess(payload["timings_ms"]["total"], 5_000)

    def test_management_archive_replay_preserves_source_site_and_law_evidence(self):
        compilation = _certified_visual_compilation()
        source_passport = {
            "stages": [
                {
                    "id": "site",
                    "status": "passed",
                    "evidence": {
                        "evaluated": True,
                        "hard_pass": True,
                        "pnu": "1168011800104170004",
                    },
                },
                {
                    "id": "law",
                    "status": "passed",
                    "evidence": {
                        "evaluated": True,
                        "hard_pass": True,
                        "far_pct": 123.4,
                    },
                },
            ],
        }
        with TemporaryDirectory() as directory, patch(
            "design.management.commands.execute_maas_single_mass.compile_executed_mass",
            return_value=(compilation, {}, {}, Path(directory) / "archive.json"),
        ), patch(
            "design.management.commands.execute_maas_single_mass.materialize_executed_mass_passport",
            return_value=source_passport,
        ):
            output = StringIO()
            call_command(
                "execute_maas_single_mass",
                run_id="portfolio-source",
                mass_index=1,
                execution_id="preserved-context",
                output_root=directory,
                stdout=output,
            )

            payload = json.loads(output.getvalue())
            self.assertEqual(payload["execution_mode"], "exact_replay")
            self.assertEqual(payload["source_run_id"], "portfolio-source")
            self.assertEqual(payload["source_mass_index"], 1)
            self.assertEqual(payload["geometry_hash"], "f" * 64)
            passport = json.loads(
                Path(payload["artifacts"]["passport"]).read_text(encoding="utf-8"),
            )

        stages = {stage["id"]: stage for stage in passport["stages"]}
        self.assertEqual(passport["geometry_hash"], "f" * 64)
        self.assertEqual(stages["site"]["evidence"]["pnu"], "1168011800104170004")
        self.assertEqual(stages["law"]["evidence"]["far_pct"], 123.4)

    def test_http_archive_replay_retains_certified_visual_compilation(self):
        compilation = _certified_visual_compilation()
        with TemporaryDirectory() as directory, override_settings(
            MAAS_SINGLE_EXECUTION_ROOT=directory,
        ), patch(
            "design.views.compile_executed_mass",
            return_value=(compilation, {}, {}, Path(directory) / "archive.json"),
        ), patch(
            "design.views.materialize_executed_mass_passport",
            return_value={"stages": []},
        ):
            response = self.client.post(
                "/design/maas/single-executions/",
                data=json.dumps({
                    "source_run_id": "portfolio-source",
                    "source_mass_index": 1,
                }),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["geometry_hash"], "f" * 64)

    def test_http_single_execution_replay_fails_closed_without_original_archive(self):
        certified = _certified_visual_compilation()
        with TemporaryDirectory() as directory, override_settings(
            MAAS_SINGLE_EXECUTION_ROOT=directory,
        ):
            execute_single_mass(
                certified.program,
                output_root=directory,
                execution_id="visual-source",
                execution_mode="exact_replay",
                validated_compilation=certified,
            )
            response = self.client.post(
                "/design/maas/single-executions/",
                data=json.dumps({
                    "source_run_id": "single-execution:visual-source",
                    "source_mass_index": 1,
                }),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn(
            "original certified archive is unavailable",
            response.json()["error"],
        )

    def test_http_single_execution_replay_recovers_original_certified_archive(self):
        certified = _certified_visual_compilation()
        with TemporaryDirectory() as directory, override_settings(
            MAAS_SINGLE_EXECUTION_ROOT=directory,
        ):
            execute_single_mass(
                certified.program,
                output_root=directory,
                execution_id="visual-source",
                execution_mode="exact_replay",
                source_run_id="portfolio-source",
                source_mass_index=1,
                validated_compilation=certified,
            )
            with patch(
                "design.views.compile_executed_mass",
                return_value=(certified, {}, {}, Path(directory) / "archive.json"),
            ):
                response = self.client.post(
                    "/design/maas/single-executions/",
                    data=json.dumps({
                        "source_run_id": "single-execution:visual-source",
                        "source_mass_index": 1,
                    }),
                    content_type="application/json",
                )

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["geometry_hash"], "f" * 64)

    def test_http_single_execution_replay_rejects_tampered_archive_identity(self):
        certified = _certified_visual_compilation()
        tampered = replace(certified, geometry_hash="0" * 64)
        with TemporaryDirectory() as directory, override_settings(
            MAAS_SINGLE_EXECUTION_ROOT=directory,
        ):
            execute_single_mass(
                certified.program,
                output_root=directory,
                execution_id="visual-source",
                execution_mode="exact_replay",
                source_run_id="portfolio-source",
                source_mass_index=1,
                validated_compilation=certified,
            )
            with patch(
                "design.views.compile_executed_mass",
                return_value=(tampered, {}, {}, Path(directory) / "archive.json"),
            ):
                response = self.client.post(
                    "/design/maas/single-executions/",
                    data=json.dumps({
                        "source_run_id": "single-execution:visual-source",
                        "source_mass_index": 1,
                    }),
                    content_type="application/json",
                )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn(
            "certified compilation identity mismatch",
            response.json()["error"],
        )

    def test_http_replay_rejects_bogus_program_hash_before_capacity_early_return(self):
        with TemporaryDirectory() as directory, override_settings(
            MAAS_SINGLE_EXECUTION_ROOT=directory,
        ):
            execute_single_mass(
                _box_program(),
                output_root=directory,
                execution_id="capacity-source",
            )
            passport_path = Path(directory) / "capacity-source" / "mass.png.passport.json"
            passport = json.loads(passport_path.read_text(encoding="utf-8"))
            passport["program_hash"] = "0" * 64
            passport_path.write_text(json.dumps(passport), encoding="utf-8")

            response = self.client.post(
                "/design/maas/single-executions/",
                data=json.dumps({
                    "source_run_id": "single-execution:capacity-source",
                    "source_mass_index": 1,
                }),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 400, response.content)
        self.assertIn("program identity mismatch", response.json()["error"])

    def test_cli_replays_single_execution_chain_from_original_archive(self):
        certified = _certified_visual_compilation()
        with TemporaryDirectory() as directory:
            execute_single_mass(
                certified.program,
                output_root=directory,
                execution_id="visual-source",
                execution_mode="exact_replay",
                source_run_id="portfolio-source",
                source_mass_index=1,
                validated_compilation=certified,
            )

            def compile_origin(index, run_id):
                if (index, run_id) != (1, "portfolio-source"):
                    raise ValueError(f"unexpected archive origin: {run_id}:{index}")
                return certified, {}, {}, Path(directory) / "archive.json"

            with patch(
                "design.management.commands.execute_maas_single_mass.compile_executed_mass",
                side_effect=compile_origin,
            ):
                output = StringIO()
                call_command(
                    "execute_maas_single_mass",
                    run_id="single-execution:visual-source",
                    mass_index=1,
                    execution_id="cli-chain",
                    output_root=directory,
                    stdout=output,
                )

        payload = json.loads(output.getvalue())
        self.assertEqual(payload["geometry_hash"], "f" * 64)
        self.assertEqual(payload["source_run_id"], "single-execution:visual-source")

    def test_cli_single_execution_replay_missing_origin_fails_closed(self):
        certified = _certified_visual_compilation()
        with TemporaryDirectory() as directory:
            execute_single_mass(
                certified.program,
                output_root=directory,
                execution_id="orphan",
                execution_mode="exact_replay",
                validated_compilation=certified,
            )
            with self.assertRaisesRegex(
                Exception,
                "original certified archive is unavailable",
            ):
                call_command(
                    "execute_maas_single_mass",
                    run_id="single-execution:orphan",
                    mass_index=1,
                    execution_id="cli-orphan",
                    output_root=directory,
                )

    def test_cli_single_execution_replay_cycle_fails_closed(self):
        certified = _certified_visual_compilation()
        with TemporaryDirectory() as directory:
            for execution_id, origin in (("cycle-a", "cycle-b"), ("cycle-b", "cycle-a")):
                execute_single_mass(
                    certified.program,
                    output_root=directory,
                    execution_id=execution_id,
                    execution_mode="exact_replay",
                    source_run_id=f"single-execution:{origin}",
                    source_mass_index=1,
                    validated_compilation=certified,
                )
            with self.assertRaisesRegex(Exception, "provenance cycle"):
                call_command(
                    "execute_maas_single_mass",
                    run_id="single-execution:cycle-a",
                    mass_index=1,
                    execution_id="cli-cycle",
                    output_root=directory,
                )

    def test_cli_single_execution_replay_intermediate_tamper_fails_closed(self):
        certified = _certified_visual_compilation()
        with TemporaryDirectory() as directory:
            execute_single_mass(
                certified.program,
                output_root=directory,
                execution_id="origin-link",
                execution_mode="exact_replay",
                source_run_id="portfolio-source",
                source_mass_index=1,
                validated_compilation=certified,
            )
            execute_single_mass(
                certified.program,
                output_root=directory,
                execution_id="requested-link",
                execution_mode="exact_replay",
                source_run_id="single-execution:origin-link",
                source_mass_index=1,
                validated_compilation=certified,
            )
            intermediate = (
                Path(directory) / "origin-link" / "mass.png.passport.json"
            )
            passport = json.loads(intermediate.read_text(encoding="utf-8"))
            passport["program_hash"] = "0" * 64
            intermediate.write_text(json.dumps(passport), encoding="utf-8")
            with self.assertRaisesRegex(Exception, "program identity mismatch"):
                call_command(
                    "execute_maas_single_mass",
                    run_id="single-execution:requested-link",
                    mass_index=1,
                    execution_id="cli-tampered",
                    output_root=directory,
                )

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
                self.assertEqual(payload["execution_mode"], "exact_replay")
                self.assertEqual(payload["source_run_id"], "single-execution:source-run")
                self.assertEqual(payload["source_mass_index"], 1)
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
                replay_run = next(
                    row for row in single_runs
                    if row["run_id"] == payload["archive_run_id"]
                )
                self.assertEqual(replay_run["execution_mode"], "exact_replay")
