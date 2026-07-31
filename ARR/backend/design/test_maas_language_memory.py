from django.test import SimpleTestCase

from design.maas.language_memory import build_language_visual_memory


class MaasLanguageVisualMemoryTest(SimpleTestCase):
    def test_snapshot_binds_typed_language_to_mass_png_evidence(self):
        payload = build_language_visual_memory()

        self.assertEqual(payload["schema_version"], "arr.maas.language_visual_memory.v1")
        self.assertEqual(payload["language_system"]["counts"]["programs"], 7)
        self.assertEqual(payload["language_system"]["counts"]["capacity_alternatives"], 4)
        self.assertEqual(
            payload["language_system"]["counts"]["theoretical_language_paths"],
            21039480,
        )
        self.assertEqual(
            payload["mass_png_memory_contract"]["geometry_authority"],
            "typed_ast_plus_program_hash_plus_geometry_hash",
        )
        self.assertIn("crop_box", payload["mass_png_memory_contract"]["binding_fields"])
        self.assertIn(
            "capacity_alternative_id",
            payload["mass_png_memory_contract"]["binding_fields"],
        )
        evidence = payload["latest_mass_visual_evidence"]
        self.assertTrue(evidence["available"])
        self.assertTrue(evidence["board_png_available"])
        self.assertEqual(evidence["latest_completed_run"]["selected_count"], 16)
        self.assertEqual(evidence["latest_completed_run"]["target_count"], 20)
        self.assertEqual(evidence["latest_completed_run"]["direct_png_review"]["verdict"], "fail")
        self.assertEqual(evidence["latest_interrupted_run"]["program_board_count"], 0)
        self.assertFalse(payload["live_vlm_launched_by_export"])
