from types import SimpleNamespace

from django.test import SimpleTestCase

from design.maas.book_language.portfolio_benchmark import (
    _capacity_hard_pass_selection_pool,
)


def candidate(*, resolved_hard_pass: bool, utilization: float):
    return SimpleNamespace(source=SimpleNamespace(metadata={
        "capacity_alternative_projection": {
            "alternative_id": "spatial_reserve",
            "target_utilization": 0.75,
            "target_hard_pass": resolved_hard_pass,
            "feasible_minimum_utilization": 0.70,
            "selectable_capacity_hard_pass": resolved_hard_pass,
            "selectable_capacity_alternative_id": (
                "spatial_reserve" if resolved_hard_pass else "below_feasible_minimum"
            ),
            "selectable_capacity_target_utilization": (
                0.70 if resolved_hard_pass else 0.0
            ),
        },
        "source_capacity_measurement": {
            "feasible_capacity_utilization": utilization,
            "hard_pass": resolved_hard_pass,
        },
    }))


class CapacitySelectionAdmissionTests(SimpleTestCase):
    def test_final_selection_excludes_below_minimum_capacity(self):
        passing = candidate(resolved_hard_pass=True, utilization=0.707)
        underfilled = candidate(resolved_hard_pass=False, utilization=0.529)

        retained, exclusions = _capacity_hard_pass_selection_pool(
            [underfilled, passing],
            required=True,
        )

        self.assertEqual(retained, [passing])
        self.assertEqual(exclusions[0]["reason"], "capacity_hard_pass_required")
        self.assertEqual(exclusions[0]["achieved_capacity_utilization"], 0.529)

    def test_non_capacity_workflow_is_unchanged(self):
        item = candidate(resolved_hard_pass=False, utilization=0.0)

        retained, exclusions = _capacity_hard_pass_selection_pool(
            [item],
            required=False,
        )

        self.assertEqual(retained, [item])
        self.assertEqual(exclusions, [])
