from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command, get_commands
from django.test import SimpleTestCase
from PIL import Image, ImageChops

from design.maas.geometry_language.programs import GeometryProgramBuilder
from design.maas import creative_program_author
from design.maas.agents.elevation_agent.projection import (
    render_mesh_views as render_research_views,
)


class CreativeFloorPortfolioCommandTests(SimpleTestCase):
    def test_cache_pool_reads_only_unique_accepted_exact_llm_programs(self):
        first_builder = GeometryProgramBuilder("cache_pool_first")
        first_root = first_builder.add(
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 0.8, "height": 1.0},
        )
        first = first_builder.build(first_root)
        second_builder = GeometryProgramBuilder("cache_pool_second")
        second_box = second_builder.add(
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 0.8, "height": 1.0},
        )
        second_root = second_builder.add(
            "macro",
            "cut_corner",
            inputs=(second_box,),
            parameters={"corner": "ne", "ratio": 0.24},
        )
        second = second_builder.build(second_root)
        invalid_builder = GeometryProgramBuilder("cache_pool_disconnected")
        invalid_box = invalid_builder.add(
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        invalid_root = invalid_builder.add(
            "pattern",
            "linear_array",
            inputs=(invalid_box,),
            parameters={"count": 2, "vector": [3.0, 0.0, 0.0]},
        )
        invalid = invalid_builder.build(invalid_root)
        no_base_builder = GeometryProgramBuilder("cache_pool_no_unitbox")
        no_base_root = no_base_builder.add(
            "primitive",
            "cylinder",
            parameters={"height": 1.0, "radius": 0.5, "segments": 16},
        )
        no_base = no_base_builder.build(no_base_root)

        with TemporaryDirectory() as temporary:
            cache_root = Path(temporary)
            accepted = {
                "cache_schema_version": (
                    "arr.maas.geometry_llm_author_cache.v3"
                ),
                "validation_status": "accepted",
                "model": "cache-pool-model",
                "response_id": "resp-cache-pool",
                "compiled_programs": [
                    invalid.to_dict(),
                    no_base.to_dict(),
                    first.to_dict(),
                    second.to_dict(),
                    first.to_dict(),
                ],
            }
            (cache_root / "01-accepted.json").write_text(
                json.dumps(accepted),
                encoding="utf-8",
            )
            (cache_root / "02-rejected.json").write_text(
                json.dumps({
                    **accepted,
                    "validation_status": "rejected",
                }),
                encoding="utf-8",
            )
            (cache_root / "03-malformed.json").write_text(
                "{not-json",
                encoding="utf-8",
            )

            reader = getattr(
                creative_program_author,
                "authored_programs_from_cache_pool",
                None,
            )
            self.assertTrue(
                callable(reader),
                "accepted cache-pool reader is missing",
            )
            programs = reader(cache_root, expected_count=2)

        self.assertEqual(
            [item.program.name for item in programs],
            ["cache_pool_first", "cache_pool_second"],
        )
        self.assertEqual(
            len({item.program.program_hash() for item in programs}),
            2,
        )
        self.assertTrue(all(
            item.author_evidence["cache_hit"] is True
            and item.author_evidence["response_id"] == "resp-cache-pool"
            for item in programs
        ))

    def test_cache_pool_author_mode_writes_candidates_without_provider_calls(
        self,
    ):
        programs = []
        for index in range(2):
            builder = GeometryProgramBuilder(f"cache_command_{index + 1}")
            box = builder.add(
                "primitive",
                "box",
                parameters={
                    "width": 1.0,
                    "depth": 0.75 + index * 0.1,
                    "height": 1.0,
                },
            )
            root = (
                builder.add(
                    "macro",
                    "cut_corner",
                    inputs=(box,),
                    parameters={"corner": "ne", "ratio": 0.24},
                )
                if index
                else box
            )
            programs.append(builder.build(root))

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache_root = root / "cache"
            cache_root.mkdir()
            (cache_root / "accepted.json").write_text(
                json.dumps({
                    "cache_schema_version": (
                        "arr.maas.geometry_llm_author_cache.v3"
                    ),
                    "validation_status": "accepted",
                    "model": "cached-command-model",
                    "response_id": "resp-cached-command",
                    "compiled_programs": [
                        program.to_dict() for program in programs
                    ],
                }),
                encoding="utf-8",
            )
            try:
                call_command(
                    "generate_maas_creative_100",
                    count=2,
                    pnu="1168011800104170004",
                    output_root=str(root),
                    run_id="cache-pool-command-test",
                    author_mode="cache_pool",
                    author_cache_root=str(cache_root),
                    verbosity=0,
                )
            except Exception as exc:
                self.fail(f"cache_pool author mode is unavailable: {exc}")
            run_directory = root / "cache-pool-command-test"
            candidates = sorted(
                (run_directory / "candidates").glob("creative-*.json")
            )
            portfolio = json.loads((
                run_directory / "maas-creative-portfolio.json"
            ).read_text(encoding="utf-8"))

        self.assertEqual(len(candidates), 2)
        self.assertEqual(portfolio["paid_author_request_count"], 0)
        self.assertEqual(portfolio["paid_vlm_request_count"], 0)
        self.assertEqual(portfolio["legal_review_status"], "not_evaluated")

    def test_twenty_candidate_board_is_five_by_four_and_prelegal(self):
        from design.management.commands import generate_maas_creative_100

        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            items = []
            for index in range(20):
                preview = root / f"candidate-{index + 1:02d}.png"
                Image.new(
                    "RGB",
                    (900, 680),
                    (230 - index, 235, 240),
                ).save(preview)
                items.append((f"candidate-{index + 1:02d}", preview))
            output = root / "board.png"

            evidence = generate_maas_creative_100._write_board(
                items,
                output,
            )
            with Image.open(output) as board:
                board_size = board.size

        self.assertEqual(evidence["candidate_count"], 20)
        self.assertEqual(evidence["columns"], 5)
        self.assertEqual(evidence["rows"], 4)
        self.assertEqual(
            evidence["status"],
            "pre_legal_not_evaluated",
        )
        self.assertEqual(board_size, (1500, 1000))

    def test_payload_author_mode_uses_exact_llm_program_without_recipe_fallback(
        self,
    ):
        builder = GeometryProgramBuilder("payload_authored_mass")
        body = builder.add(
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 0.8, "height": 1.2},
        )
        program = builder.build(
            body,
            author_provider="saved_llm_payload",
            author_model="payload-model",
            author_response_id="payload-response",
        )
        with TemporaryDirectory() as temporary:
            payload_path = Path(temporary) / "author-payload.json"
            payload_path.write_text(
                json.dumps({"geometry_programs": [program.to_dict()]}),
                encoding="utf-8",
            )
            try:
                call_command(
                    "generate_maas_creative_100",
                    count=1,
                    pnu="1168011800104170004",
                    output_root=temporary,
                    run_id="payload-author-test",
                    author_mode="payload",
                    author_payload=str(payload_path),
                    verbosity=0,
                )
            except TypeError as exc:
                self.fail(f"payload author mode is unavailable: {exc}")
            candidate = json.loads((
                Path(temporary)
                / "payload-author-test"
                / "candidates"
                / "creative-001.json"
            ).read_text(encoding="utf-8"))
            portfolio = json.loads((
                Path(temporary)
                / "payload-author-test"
                / "maas-creative-portfolio.json"
            ).read_text(encoding="utf-8"))

        self.assertEqual(
            candidate["author_evidence"]["source_kind"],
            "llm_authored_geometry_program",
        )
        self.assertEqual(
            candidate["author_evidence"]["provider"],
            "saved_llm_payload",
        )
        self.assertTrue(candidate["family"].startswith("morph-"))
        self.assertIn("paid_author_request_count", portfolio)
        self.assertEqual(portfolio["paid_author_request_count"], 0)

    def test_llm_author_mode_missing_credentials_fails_without_fixture_fallback(
        self,
    ):
        with TemporaryDirectory() as temporary, patch.dict(
            os.environ,
            {"OPENAI_API_KEY": ""},
        ):
            try:
                with self.assertRaisesRegex(
                    Exception,
                    "OPENAI_API_KEY is not set",
                ):
                    call_command(
                        "generate_maas_creative_100",
                        count=1,
                        pnu="1168011800104170004",
                        output_root=temporary,
                        run_id="missing-llm-credentials",
                        author_mode="llm",
                        verbosity=0,
                    )
            except TypeError as exc:
                self.fail(f"LLM author mode is unavailable: {exc}")

    def test_count_three_writes_graph_ready_choice_pool_without_paid_or_legal_claims(
        self,
    ):
        self.assertIn("generate_maas_creative_100", get_commands())
        with TemporaryDirectory() as temporary:
            call_command(
                "generate_maas_creative_100",
                count=3,
                pnu="1168011800104170004",
                capacity_ceiling_m2=332.322,
                output_root=temporary,
                run_id="creative-command-test",
                author_mode="recipe_fixture",
                verbosity=0,
            )
            run_directory = Path(temporary) / "creative-command-test"
            portfolio_path = (
                run_directory / "maas-creative-portfolio.json"
            )
            candidate_paths = sorted(
                (run_directory / "candidates").glob("creative-*.json")
            )
            preview_paths = sorted(
                (run_directory / "renders").glob("creative-*.png")
            )
            mass_directories = sorted(
                (run_directory / "masses").glob("creative-*")
            )
            board_path = run_directory / "maas-creative-board.png"

            self.assertTrue(portfolio_path.is_file())
            self.assertTrue(board_path.is_file())
            self.assertEqual(len(candidate_paths), 3)
            self.assertEqual(len(preview_paths), 3)
            self.assertEqual(len(mass_directories), 3)

            portfolio = json.loads(
                portfolio_path.read_text(encoding="utf-8")
            )
            candidates = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in candidate_paths
            ]
            first_mass = mass_directories[0]
            mass_manifest = json.loads((
                first_mass / "manifest.json"
            ).read_text(encoding="utf-8"))
            elevation_handoff = json.loads((
                first_mass / "elevation-research" / "handoff.json"
            ).read_text(encoding="utf-8"))
            view_paths_exist = all(
                (first_mass / elevation_handoff["views"][view]["path"]).is_file()
                for view in elevation_handoff["views"]
            )
            required_files = {
                "program/geometry-program.json",
                "program/author-evidence.json",
                "transforms/matrix4-trace.json",
                "mesh/indexed-mesh.json",
                "mesh/vertices.csv",
                "mesh/triangles.csv",
                "mesh/mass.obj",
                "elevation-research/floor-guides.json",
                "elevation-research/camera-poses.json",
                "elevation-research/surface-normals.json",
                "elevation-research/facade-planes.json",
            }
            required_files_exist = all(
                (first_mass / relative_path).is_file()
                for relative_path in required_files
            )
            indexed_mesh = json.loads((
                first_mass / "mesh" / "indexed-mesh.json"
            ).read_text(encoding="utf-8"))
            vertex_csv_rows = (
                first_mass / "mesh" / "vertices.csv"
            ).read_text(encoding="utf-8").strip().splitlines()
            triangle_csv_rows = (
                first_mass / "mesh" / "triangles.csv"
            ).read_text(encoding="utf-8").strip().splitlines()
            obj_rows = (
                first_mass / "mesh" / "mass.obj"
            ).read_text(encoding="utf-8").splitlines()
            normal_payload = json.loads((
                first_mass
                / "elevation-research"
                / "surface-normals.json"
            ).read_text(encoding="utf-8"))
            manifest_hashes_match = all(
                hashlib.sha256(
                    (
                        first_mass / record["path"]
                    ).read_bytes()
                ).hexdigest()
                == record["sha256"]
                for record in mass_manifest["artifacts"].values()
                if isinstance(record, dict)
                and "path" in record
                and "sha256" in record
            )
            with Image.open(preview_paths[0]) as preview:
                preview_size = preview.size
                expected_isometric_card = preview.convert("RGB").crop(
                    (0, 0, 450, 325)
                ).resize((300, 227), Image.Resampling.LANCZOS)
                wrong_full_preview_card = preview.convert("RGB").resize(
                    (300, 227),
                    Image.Resampling.LANCZOS,
                )
            with Image.open(board_path) as board:
                board_size = board.size
                actual_first_card = board.convert("RGB").crop(
                    (0, 0, 300, 227)
                )

        self.assertEqual(portfolio["candidate_count"], 3)
        self.assertTrue(portfolio["choice_pool"])
        self.assertEqual(portfolio["pnu"], "1168011800104170004")
        self.assertEqual(portfolio["paid_vlm_request_count"], 0)
        self.assertEqual(portfolio["legal_review_status"], "not_evaluated")
        self.assertEqual(portfolio["board"]["columns"], 10)
        self.assertEqual(preview_size, (900, 680))
        self.assertEqual(board_size[0], 3000)
        self.assertIsNone(
            ImageChops.difference(
                actual_first_card,
                expected_isometric_card,
            ).getbbox()
        )
        self.assertIsNotNone(
            ImageChops.difference(
                actual_first_card,
                wrong_full_preview_card,
            ).getbbox()
        )

        candidate_ids = {
            candidate["candidate_id"] for candidate in candidates
        }
        self.assertEqual(
            candidate_ids,
            {"creative-001", "creative-002", "creative-003"},
        )
        self.assertTrue(all(
            candidate["geometry_program"]["nodes"]
            and candidate["matrix4_trace"]
            and candidate["mesh"]["vertices"]
            and candidate["mesh"]["triangles"]
            for candidate in candidates
        ))
        self.assertTrue(all(
            candidate["legal_review"]["status"] == "not_evaluated"
            and candidate["legal_review"]["hard_pass"] is False
            for candidate in candidates
        ))
        self.assertTrue(all(
            candidate["identity"]["candidate_id"]
            == candidate["candidate_id"]
            and candidate["identity"]["program_hash"]
            == candidate["program_hash"]
            and candidate["identity"]["geometry_hash"]
            == candidate["geometry_hash"]
            for candidate in candidates
        ))
        self.assertEqual(
            mass_manifest["identity"]["geometry_hash"],
            candidates[0]["geometry_hash"],
        )
        self.assertEqual(
            elevation_handoff["status"],
            "prelegal_research_ready",
        )
        self.assertFalse(elevation_handoff["geometry_mutation_allowed"])
        self.assertEqual(
            set(elevation_handoff["views"]),
            {"front", "right", "back", "left", "top", "axon"},
        )
        self.assertTrue(all(
            elevation_handoff["views"][view]["view_matrix4"]
            for view in elevation_handoff["views"]
        ))
        self.assertTrue(view_paths_exist)
        self.assertTrue(required_files_exist)
        self.assertEqual(
            len(vertex_csv_rows) - 1,
            indexed_mesh["vertex_count"],
        )
        self.assertEqual(
            len(triangle_csv_rows) - 1,
            indexed_mesh["triangle_count"],
        )
        self.assertEqual(
            len([row for row in obj_rows if row.startswith("v ")]),
            indexed_mesh["vertex_count"],
        )
        self.assertEqual(
            len([row for row in obj_rows if row.startswith("f ")]),
            indexed_mesh["triangle_count"],
        )
        self.assertEqual(
            len(normal_payload["stable_face_ids"]),
            indexed_mesh["triangle_count"],
        )
        self.assertEqual(
            len(normal_payload["triangle_normals"]),
            indexed_mesh["triangle_count"],
        )
        self.assertTrue(manifest_hashes_match)
        self.assertTrue(all(
            candidate["mass_directory"]
            and candidate["mass_manifest"]
            and candidate["elevation_research_handoff"]
            for candidate in candidates
        ))

        graph = portfolio["frontend_graph"]
        self.assertEqual(
            len([
                node for node in graph["nodes"]
                if node["kind"] == "creative_mass_candidate"
            ]),
            3,
        )
        self.assertEqual(
            len([
                edge for edge in graph["edges"]
                if edge["kind"] == "member_of"
            ]),
            3,
        )
        self.assertEqual(
            set(portfolio["filter_facets"]),
            {"family", "capacity_band", "storeys", "legal_status"},
        )

    def test_count_one_hundred_persists_complete_prelegal_archive_contract(self):
        def tiny_preview(_compilation, output_path, **_kwargs):
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (16, 16), "white").save(output)
            return output

        def tiny_research_views(
            vertices,
            triangles,
            output_directory,
            *,
            execution_id,
        ):
            return render_research_views(
                vertices,
                triangles,
                output_directory,
                execution_id=execution_id,
                size=160,
            )

        with TemporaryDirectory() as temporary, patch(
            "design.management.commands.generate_maas_creative_100."
            "render_compilation_preview",
            side_effect=tiny_preview,
        ), patch(
            "design.maas.creative_research_bundle.render_mesh_views",
            side_effect=tiny_research_views,
        ):
            call_command(
                "generate_maas_creative_100",
                count=100,
                pnu="1168011800104170004",
                capacity_ceiling_m2=332.322,
                output_root=temporary,
                run_id="creative-100-contract",
                author_mode="recipe_fixture",
                verbosity=0,
            )
            run_directory = Path(temporary) / "creative-100-contract"
            portfolio = json.loads((
                run_directory / "maas-creative-portfolio.json"
            ).read_text(encoding="utf-8"))
            candidate_files = sorted(
                (run_directory / "candidates").glob("*.json")
            )
            render_files = sorted(
                (run_directory / "renders").glob("*.png")
            )
            mass_directories = sorted(
                (run_directory / "masses").glob("creative-*")
            )
            first = json.loads(candidate_files[0].read_text(encoding="utf-8"))

        self.assertEqual(len(candidate_files), 100)
        self.assertEqual(len(render_files), 100)
        self.assertEqual(len(mass_directories), 100)
        self.assertEqual(portfolio["candidate_count"], 100)
        self.assertEqual(len(portfolio["filter_facets"]["family"]), 15)
        self.assertEqual(len(portfolio["filter_facets"]["capacity_band"]), 4)
        self.assertEqual(
            portfolio["morphology_evidence"]["accepted_count"],
            100,
        )
        self.assertTrue(first["geometry_program"]["nodes"])
        self.assertTrue(first["matrix4_trace"])
        self.assertTrue(first["mesh"]["vertices"])
        self.assertTrue(first["mesh"]["triangles"])
        self.assertEqual(first["legal_review"]["status"], "not_evaluated")
        self.assertEqual(portfolio["paid_vlm_request_count"], 0)
