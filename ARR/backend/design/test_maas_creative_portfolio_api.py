from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from PIL import Image


def _tiny_preview(_compilation, output_path, **_kwargs):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 16), "white").save(output)
    return output


class CreativePortfolioApiTests(SimpleTestCase):
    def test_read_only_manifest_and_candidate_render_endpoints(self):
        with TemporaryDirectory() as temporary, patch(
            "design.management.commands.generate_maas_creative_100."
            "render_compilation_preview",
            side_effect=_tiny_preview,
        ):
            call_command(
                "generate_maas_creative_100",
                count=2,
                pnu="1168011800104170004",
                capacity_ceiling_m2=332.322,
                output_root=temporary,
                run_id="api-run",
                author_mode="recipe_fixture",
                verbosity=0,
            )
            with override_settings(MAAS_CREATIVE_PORTFOLIO_ROOT=temporary):
                response = self.client.get(
                    "/design/maas/creative-portfolios/",
                    {"run_id": "api-run"},
                )
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["run_type"], "creative_portfolio")
                self.assertEqual(payload["candidate_count"], 2)
                self.assertNotIn("law_evidence", payload["candidates"][0])
                self.assertNotIn("parking_evidence", payload["candidates"][0])
                render_response = self.client.get(
                    payload["candidates"][0]["render_url"]
                )
                self.assertEqual(render_response.status_code, 200)
                self.assertEqual(
                    render_response["Content-Type"],
                    "image/png",
                )
                b"".join(render_response.streaming_content)
                render_response.close()
                self.assertEqual(
                    self.client.post(
                        "/design/maas/creative-portfolios/",
                        data={},
                    ).status_code,
                    405,
                )

    def test_rejects_opaque_run_traversal_and_unknown_candidate(self):
        with TemporaryDirectory() as temporary, override_settings(
            MAAS_CREATIVE_PORTFOLIO_ROOT=temporary,
        ):
            traversal = self.client.get(
                "/design/maas/creative-portfolios/",
                {"run_id": "../outside"},
            )
            missing = self.client.get(
                "/design/maas/creative-portfolios/safe-run/"
                "candidates/unknown/render/",
            )

        self.assertIn(traversal.status_code, {400, 404})
        self.assertEqual(missing.status_code, 404)
