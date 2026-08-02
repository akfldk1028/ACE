from types import SimpleNamespace

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language.floor_capacity_plan import (
    derive_program_floor_capacity_plan,
)


def _law_context(*, legal_floor_count: int, far_limit_pct: float):
    site = box(0.0, 0.0, 20.0, 20.0)
    return (
        SimpleNamespace(
            envelope=SimpleNamespace(
                floor_height=3.0,
                height_limit=legal_floor_count * 3.0,
                bcr_limit=60.0,
                far_limit=far_limit_pct,
            ),
            generation_site=box(0.0, 0.0, 10.0, 10.0),
            sunlight_ring=(),
            evidence={},
        ),
        site,
    )


class LawDerivedFloorCapacityStopTests(SimpleTestCase):
    def test_ordinary_floors_stop_at_first_lawful_far_saturating_floor(self):
        cases = (
            # A 400 m2 parcel with 100 m2 legal plates needs these exact
            # counts to reach each independently hand-calculated FAR cap.
            (1, 25.0, 10, 100.0),
            (3, 52.5, 10, 210.0),
            (7, 162.5, 10, 650.0),
            (23, 562.5, 25, 2250.0),
        )

        for expected_floors, far_limit, legal_floors, expected_gfa in cases:
            with self.subTest(expected_floors=expected_floors):
                context, site = _law_context(
                    legal_floor_count=legal_floors,
                    far_limit_pct=far_limit,
                )

                plan = derive_program_floor_capacity_plan(
                    context,
                    site_local_utm=site,
                    building_type="neighborhood living",
                    target_utilization=0.90,
                    legacy_floor_hint=5,
                )

                self.assertEqual(plan["status"], "materialized")
                self.assertEqual(
                    plan["selected_floor_count"],
                    expected_floors,
                )
                self.assertEqual(
                    plan["allowed_floor_range"],
                    [1, legal_floors],
                )
                self.assertAlmostEqual(
                    plan["feasible_maximum_gfa_m2"],
                    expected_gfa,
                    places=3,
                )
                self.assertAlmostEqual(
                    plan["selected_stack_capacity_m2"],
                    expected_gfa,
                    places=3,
                )
                self.assertFalse(plan["legacy_hint_is_authority"])
