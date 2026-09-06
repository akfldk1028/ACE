"""Prompt expectations derived from the real author admission context."""
import unittest

from design.maas.geometry_language import llm_adapter as owner


class AuthorDensityPromptTests(unittest.TestCase):
    def test_missing_programme_does_not_invent_capacity_floor(self):
        prompt = owner._author_prompt({}, 2)
        self.assertNotIn("capacity utilization must remain at least 0.60", prompt)
        self.assertNotIn("0.70 is the preferred design target", prompt)
        self.assertIn("Missing programme or target area remains unknown", prompt)
        self.assertIn("legal ceilings are not automatic design targets", prompt)

    def test_explicit_capacity_budget_survives_without_another_numeric_owner(self):
        contract = {"minimum_utilization": 0.37, "target_utilization": 0.52,
                    "target_floor_areas_m2": [240.0, 310.0]}
        for context in ({"base_capacity_contract": contract},
                        {"program_context": {"base_capacity_contract": contract}}):
            with self.subTest(context=context):
                prompt = owner._author_prompt(context, 2)
                self.assertIn('"minimum_utilization": 0.37', prompt)
                self.assertIn('"target_utilization": 0.52', prompt)
                self.assertIn('"target_floor_areas_m2": [240.0, 310.0]', prompt)
                self.assertIn("supplied capacity_design_budget", prompt)
                self.assertNotIn("capacity utilization must remain at least 0.60", prompt)

    def test_body_allowance_matches_actual_gate_for_each_reserve(self):
        for depth, reserve in ((1, 0), (2, 0), (3, 0), (3, 1), (2, 1)):
            context = {"maximum_operator_depth": depth,
                       "downstream_body_rule_reserve": reserve}
            with self.subTest(context=context):
                expected = owner.geometry_author_validation_context(context)["author_maximum_body_rule_count"]
                prompt = owner._author_prompt(context, 2)
                self.assertIn(f"BODY RULE BUDGET = {expected}", prompt)
                self.assertNotIn("Do not add a second bend", prompt)
                self.assertIn("Do not exceed the declared BODY RULE BUDGET", prompt)
                self.assertIn("from distinct", prompt)


if __name__ == "__main__":
    unittest.main()
