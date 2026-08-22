from django.test import SimpleTestCase

from design.maas.geometry_language.chassis_taxonomy import (
    classify_geometry_program,
)


class ChassisTaxonomyTests(SimpleTestCase):
    def test_terminal_access_notch_does_not_mask_twisted_tower_body(self):
        classification = classify_geometry_program(
            family="",
            source_operators=("box", "scale", "matrix4", "twist", "notch"),
            declared_base_seed="tower",
        )

        self.assertEqual(classification["chassis"], "twisted_tower")
        self.assertEqual(classification["base_seed"], "tower")

    def test_terminal_access_notch_does_not_mask_structural_body_chassis(self):
        cases = (
            ("grid_mass", "bar", "distributed_grid"),
            ("cantilever", "bar", "cantilevered_bar"),
            ("puncture", "block", "perforated_monolith"),
            ("taper", "tower", "tapered_tower"),
            ("shear", "tower", "sheared_tower"),
        )

        for operator, seed, expected_chassis in cases:
            with self.subTest(operator=operator):
                classification = classify_geometry_program(
                    family="",
                    source_operators=(
                        "box",
                        "scale",
                        "matrix4",
                        operator,
                        "notch",
                    ),
                    declared_base_seed=seed,
                )

                self.assertEqual(
                    classification["chassis"],
                    expected_chassis,
                )
                self.assertEqual(classification["base_seed"], seed)
