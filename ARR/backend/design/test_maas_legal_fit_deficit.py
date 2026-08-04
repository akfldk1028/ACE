from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language.legal_fit_deficit import (
    build_legal_fit_deficit,
)


class LegalFitDeficitTests(SimpleTestCase):
    def test_three_decimal_target_rounding_does_not_exceed_legal_section(self):
        cases = (
            (102.931, 102.930961),
            (51.471, 51.470715),
        )

        for target_area, legal_area in cases:
            with self.subTest(
                target_area=target_area,
                legal_area=legal_area,
            ):
                deficit = build_legal_fit_deficit(
                    authored_program_hash="authored-hash",
                    legal_sections=(box(0, 0, 1, legal_area),),
                    target_floor_areas_m2=(target_area,),
                    floor_capacity_plan_hash="floor-plan-hash",
                )

                self.assertNotIn(
                    "target_exceeds_legal_section",
                    deficit.typed_reasons,
                )
                self.assertEqual(deficit.legal_section_indices, ())

    def test_exceed_beyond_three_decimal_rounding_tolerance_still_fails(self):
        deficit = build_legal_fit_deficit(
            authored_program_hash="authored-hash",
            legal_sections=(box(0, 0, 1, 51.4704),),
            target_floor_areas_m2=(51.471,),
            floor_capacity_plan_hash="floor-plan-hash",
        )

        self.assertIn(
            "target_exceeds_legal_section",
            deficit.typed_reasons,
        )
        self.assertEqual(deficit.legal_section_indices, (0,))

    def test_reports_floor_targets_beyond_legal_sections(self):
        deficit = build_legal_fit_deficit(
            authored_program_hash="authored-hash",
            legal_sections=(box(0, 0, 10, 10), box(0, 0, 8, 8)),
            target_floor_areas_m2=(90.0, 80.0),
            floor_capacity_plan_hash="floor-plan-hash",
        )

        self.assertEqual(deficit.stage, "principal_frame_legal_fit")
        self.assertIn("target_exceeds_legal_section", deficit.typed_reasons)
        self.assertEqual(deficit.legal_section_indices, (1,))
        self.assertEqual(deficit.authored_program_hash, "authored-hash")

    def test_feasible_sections_report_whole_solid_fit_not_a_form_recipe(self):
        deficit = build_legal_fit_deficit(
            authored_program_hash="authored-hash",
            legal_sections=(box(0, 0, 10, 10),),
            target_floor_areas_m2=(60.0,),
            floor_capacity_plan_hash="floor-plan-hash",
        )

        self.assertEqual(
            deficit.typed_reasons,
            ("whole_solid_affine_fit_infeasible",),
        )
        self.assertNotIn("stepped", str(deficit.to_dict()).lower())
