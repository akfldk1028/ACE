from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from PIL import Image

from design.maas.paid_provider_budget import paid_provider_budget_snapshot


class RelationalMassPreviewTests(SimpleTestCase):
    def test_preview_renders_twenty_slots_and_three_free_shortlist_candidates(self):
        from design.maas.geometry_language.relational_mass_preview import (
            render_relational_mass_preview,
        )

        before = paid_provider_budget_snapshot()["request_count"]
        with TemporaryDirectory() as temporary_directory:
            result = render_relational_mass_preview(
                temporary_directory,
                "1168011800104170004",
            )
            board = Path(result["board_png"])
            shortlist = Path(result["shortlist_png"])

            self.assertEqual(result["candidate_count"], 20)
            self.assertEqual(result["shortlist_count"], 3)
            self.assertEqual(
                result["shortlist_candidate_ids"],
                ["mass-19", "mass-17", "mass-15"],
            )
            self.assertEqual(result["paid_provider_request_count"], 0)
            self.assertTrue(board.is_file())
            self.assertTrue(shortlist.is_file())
            with Image.open(board) as image:
                self.assertEqual(image.size, (1920, 1320))
            with Image.open(shortlist) as image:
                self.assertEqual(image.size, (1800, 650))
            for candidate in result["candidates"]:
                program_path = Path(candidate["program_json"])
                self.assertTrue(program_path.is_file())
                if candidate["status"] != "compiled":
                    continue
                self.assertEqual(candidate["component_count"], 1)
                self.assertTrue(candidate["geometry_hash"])

        self.assertEqual(
            paid_provider_budget_snapshot()["request_count"],
            before,
        )
