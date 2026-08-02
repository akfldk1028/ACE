from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase
from PIL import Image

from design.maas.creative_portfolio_catalog import (
    creative_portfolio_manifest,
    creative_portfolio_render,
)


def _tiny_preview(_compilation, output_path, **_kwargs):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 16), "white").save(output)
    return output


class CreativePortfolioCatalogTests(SimpleTestCase):
    def _create_run(self, root: str, run_id: str = "catalog-run") -> Path:
        with patch(
            "design.management.commands.generate_maas_creative_100."
            "render_compilation_preview",
            side_effect=_tiny_preview,
        ):
            call_command(
                "generate_maas_creative_100",
                count=3,
                pnu="1168011800104170004",
                capacity_ceiling_m2=332.322,
                output_root=root,
                run_id=run_id,
                author_mode="recipe_fixture",
                verbosity=0,
            )
        return Path(root) / run_id

    def test_discovers_every_member_with_exact_identity_and_graph_edges(self):
        with TemporaryDirectory() as temporary:
            self._create_run(temporary)
            manifest = creative_portfolio_manifest(temporary, "catalog-run")

        self.assertEqual(manifest["run_type"], "creative_portfolio")
        self.assertEqual(manifest["candidate_count"], 3)
        self.assertEqual(len(manifest["candidates"]), 3)
        required = {
            "run_id",
            "candidate_id",
            "program_hash",
            "geometry_hash",
            "render_png",
            "candidate_json",
            "family",
            "form_class",
            "capacity_band",
            "mass_directory",
            "mass_manifest",
            "elevation_research_handoff",
            "storeys",
            "legal_status",
        }
        self.assertTrue(all(
            required <= set(candidate)
            and candidate["legal_status"] == "not_evaluated"
            for candidate in manifest["candidates"]
        ))
        self.assertEqual(
            len([
                edge for edge in manifest["graph"]["edges"]
                if edge["kind"] == "member_of"
            ]),
            3,
        )
        self.assertEqual(
            len([
                node for node in manifest["graph"]["nodes"]
                if node["kind"] == "geometry_portfolio"
            ]),
            1,
        )

    def test_rejects_candidate_paths_outside_run_and_tampered_hashes(self):
        with TemporaryDirectory() as temporary:
            run_directory = self._create_run(temporary)
            portfolio_path = run_directory / "maas-creative-portfolio.json"
            portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
            portfolio["candidates"][0]["render_png"] = "../outside.png"
            portfolio_path.write_text(json.dumps(portfolio), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inside run directory"):
                creative_portfolio_manifest(temporary, "catalog-run")

            portfolio["candidates"][0]["render_png"] = "renders/creative-001.png"
            candidate_path = run_directory / "candidates" / "creative-001.json"
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            original_candidate = dict(candidate)
            candidate["program_hash"] = "0" * 64
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            portfolio_path.write_text(json.dumps(portfolio), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "program hash"):
                creative_portfolio_manifest(temporary, "catalog-run")

            original_candidate["mesh"]["vertices"][0][0] += 0.25
            candidate_path.write_text(
                json.dumps(original_candidate),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "stored mesh geometry hash"):
                creative_portfolio_manifest(temporary, "catalog-run")

    def test_render_resolution_is_candidate_bound_and_inside_root(self):
        with TemporaryDirectory() as temporary:
            self._create_run(temporary)
            render = creative_portfolio_render(
                temporary,
                "catalog-run",
                "creative-002",
            )
            self.assertTrue(render.is_file())
            self.assertTrue(render.is_relative_to(Path(temporary).resolve()))
            with self.assertRaises((FileNotFoundError, ValueError)):
                creative_portfolio_render(
                    temporary,
                    "../catalog-run",
                    "creative-002",
                )
