from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language.floor_capacity_plan import (
    allocate_floor_targets,
    derive_program_floor_capacity_plan,
)
from design.maas.book_language.capacity_contract import (
    build_feasible_capacity_contract,
)
from design.maas.book_language.portfolio_benchmark import (
    _resolve_authoritative_floor_context,
)


def _context(
    *,
    site=box(0.0, 0.0, 20.0, 20.0),
    generation_site=box(0.0, 0.0, 10.0, 10.0),
    floor_height=3.0,
    height_limit=24.0,
    bcr_limit=60.0,
    far_limit=200.0,
    sunlight_ring=(),
):
    return SimpleNamespace(
        envelope=SimpleNamespace(
            floor_height=floor_height,
            height_limit=height_limit,
            bcr_limit=bcr_limit,
            far_limit=far_limit,
        ),
        generation_site=generation_site,
        sunlight_ring=tuple(sunlight_ring),
        evidence={},
    ), site


class LawDerivedFloorCapacityPlanTests(SimpleTestCase):
    def test_floor_targets_preserve_the_same_design_reserve_on_every_plate(self):
        targets = allocate_floor_targets(
            capacities=(100.0, 10.0),
            target=60.5,
        )

        self.assertAlmostEqual(targets[0], 55.0, places=9)
        self.assertAlmostEqual(targets[1], 5.5, places=9)
        self.assertTrue(
            all(
                target / capacity <= 0.55 + 1e-9
                for target, capacity in zip(targets, (100.0, 10.0))
            )
        )

    def test_law_and_program_range_override_legacy_five_floor_hint(self):
        context, site = _context()

        plan = derive_program_floor_capacity_plan(
            context,
            site_local_utm=site,
            building_type="neighborhood living",
            target_utilization=0.90,
            legacy_floor_hint=5,
        )

        self.assertEqual(plan["status"], "materialized")
        self.assertEqual(plan["selected_floor_count"], 8)
        self.assertEqual(plan["allowed_floor_range"], [2, 8])
        self.assertEqual(plan["legacy_floor_hint"], 5)
        self.assertFalse(plan["legacy_hint_is_authority"])
        self.assertAlmostEqual(plan["target_gfa_m2"], 720.0, places=3)

    def test_legal_height_clamps_floor_range_before_capacity_measurement(self):
        context, site = _context(height_limit=15.0)

        plan = derive_program_floor_capacity_plan(
            context,
            site_local_utm=site,
            building_type="neighborhood living",
            target_utilization=0.90,
        )

        self.assertEqual(plan["allowed_floor_range"], [2, 5])
        self.assertEqual(plan["selected_floor_count"], 5)
        self.assertEqual(plan["selected_height_m"], 15.0)
        self.assertEqual(len(plan["legal_floor_section_areas_m2"]), 5)

    def test_sunlight_sections_drive_bounded_proportional_targets(self):
        context, site = _context(
            height_limit=24.0,
            far_limit=400.0,
            sunlight_ring=(
                (0.0, 0.0, 30.0),
                (10.0, 0.0, 30.0),
                (10.0, 10.0, 0.0),
                (0.0, 10.0, 0.0),
            ),
        )

        plan = derive_program_floor_capacity_plan(
            context,
            site_local_utm=site,
            building_type="neighborhood living",
            target_utilization=0.90,
        )

        legal = plan["legal_floor_section_areas_m2"]
        targets = plan["target_floor_areas_m2"]
        self.assertEqual(plan["selected_floor_count"], 7)
        self.assertGreater(legal[0], legal[-1])
        self.assertEqual(len(targets), 7)
        self.assertAlmostEqual(sum(targets), plan["target_gfa_m2"], places=2)
        self.assertTrue(all(0.0 <= target <= cap + 1e-6 for target, cap in zip(targets, legal)))
        self.assertEqual(
            plan["stack_selection_policy"],
            "preserve_capacity_target_design_reserve",
        )
        self.assertAlmostEqual(plan["design_reserve_ratio"], 0.10, places=3)
        self.assertLessEqual(
            plan["selected_stack_target_utilization"],
            plan["target_utilization"] + 1e-6,
        )
        self.assertLessEqual(
            sum(targets),
            plan["statutory_far_capacity_m2"] + 1e-6,
        )

    def test_far_limited_stack_keeps_reserve_without_selecting_all_floors(self):
        context, site = _context(
            height_limit=24.0,
            far_limit=52.5,
        )

        plan = derive_program_floor_capacity_plan(
            context,
            site_local_utm=site,
            building_type="neighborhood living",
            target_utilization=0.90,
        )

        # Two 100 m2 plates can carry the 189 m2 target, but not the complete
        # 210 m2 feasible capacity. A third floor preserves the 10% design
        # reserve while the FAR cap prevents needless selection of floors 4-8.
        self.assertEqual(plan["selected_floor_count"], 3)
        self.assertAlmostEqual(plan["feasible_maximum_gfa_m2"], 210.0, places=3)
        self.assertAlmostEqual(plan["selected_stack_capacity_m2"], 210.0, places=3)
        self.assertAlmostEqual(plan["target_gfa_m2"], 189.0, places=3)
        self.assertAlmostEqual(
            plan["selected_stack_target_utilization"],
            0.90,
            places=3,
        )

    @patch(
        "design.maas.book_language.floor_capacity_plan."
        "generation_site_at_height"
    )
    def test_terminal_sunlight_sliver_is_not_counted_as_an_occupiable_floor(
        self,
        section_at_height,
    ):
        section_at_height.side_effect = lambda _context, top: (
            box(0.0, 0.0, 10.0, 10.0)
            if top <= 3.0
            else (
                box(0.0, 0.0, 10.0, 8.0)
                if top <= 6.0
                else box(0.0, 0.0, 2.0, 1.0)
            )
        )
        context, site = _context(
            height_limit=24.0,
            far_limit=400.0,
        )

        plan = derive_program_floor_capacity_plan(
            context,
            site_local_utm=site,
            building_type="neighborhood living",
            target_utilization=0.90,
        )

        self.assertEqual(plan["selected_floor_count"], 2)
        self.assertEqual(plan["measured_usable_floor_count"], 2)
        self.assertEqual(plan["minimum_usable_floor_area_m2"], 8.0)
        self.assertEqual(plan["excluded_terminal_floor_count"], 6)
        self.assertAlmostEqual(plan["feasible_maximum_gfa_m2"], 180.0)
        self.assertAlmostEqual(plan["target_gfa_m2"], 162.0)

    @patch(
        "design.maas.book_language.floor_capacity_plan."
        "generation_site_at_height"
    )
    def test_terminal_sunlight_strip_without_clear_depth_is_not_a_floor(
        self,
        section_at_height,
    ):
        section_at_height.side_effect = lambda _context, top: (
            box(0.0, 0.0, 10.0, 10.0)
            if top <= 3.0
            else (
                box(0.0, 0.0, 10.0, 8.0)
                if top <= 6.0
                else box(0.0, 0.0, 20.0, 1.5)
            )
        )
        context, site = _context(
            height_limit=24.0,
            far_limit=400.0,
        )

        plan = derive_program_floor_capacity_plan(
            context,
            site_local_utm=site,
            building_type="neighborhood living",
            target_utilization=0.90,
        )

        self.assertEqual(plan["selected_floor_count"], 2)
        self.assertEqual(plan["minimum_clear_floor_depth_m"], 2.4)
        self.assertIn(
            "insufficient_clear_floor_depth",
            plan["terminal_floor_exclusion_reasons"],
        )

    def test_profile_minimum_above_legal_height_is_explicitly_infeasible(self):
        context, site = _context(height_limit=3.0)

        plan = derive_program_floor_capacity_plan(
            context,
            site_local_utm=site,
            building_type="neighborhood living",
            target_utilization=0.90,
        )

        self.assertEqual(plan["status"], "infeasible")
        self.assertEqual(plan["selected_floor_count"], 0)
        self.assertIn(
            "legal_height_below_program_minimum_floors",
            plan["failure_reasons"],
        )

    def test_clear_span_height_is_not_reinterpreted_as_ordinary_storeys(self):
        context, site = _context(
            floor_height=4.0,
            height_limit=30.0,
            far_limit=300.0,
        )

        plan = derive_program_floor_capacity_plan(
            context,
            site_local_utm=site,
            building_type="gymnasium",
            target_utilization=0.85,
            dimensional_context={
                "status": "feasible",
                "selected_subtype": "community_court",
                "effective_height_m": 18.0,
                "effective_floors": 3,
                "minimum_clear_span_m": 15.0,
            },
        )

        self.assertEqual(plan["planning_mode"], "clear_span")
        self.assertEqual(plan["selected_floor_count"], 3)
        self.assertEqual(plan["selected_height_m"], 18.0)
        self.assertNotEqual(
            plan["selected_height_m"],
            plan["selected_floor_count"] * plan["typical_floor_height_m"],
        )

    def test_portfolio_floor_context_replaces_legacy_catalog_dimensions(self):
        context, site = _context()
        dimensional_context = {
            "status": "not_required",
            "effective_height_m": 15.0,
            "effective_floors": 5,
        }

        height, floors, plan = _resolve_authoritative_floor_context(
            generation_context=context,
            site_local_utm=site,
            building_type="neighborhood living",
            catalog_height_m=15.0,
            catalog_floors=5,
            dimensional_context=dimensional_context,
            target_utilization=0.90,
        )

        self.assertEqual(floors, 8)
        self.assertEqual(height, 24.0)
        self.assertEqual(plan["selected_floor_count"], 8)
        self.assertFalse(plan["legacy_hint_is_authority"])

    def test_capacity_contract_reuses_exact_floor_plan_identity_and_sections(self):
        context, site = _context()
        plan = derive_program_floor_capacity_plan(
            context,
            site_local_utm=site,
            building_type="neighborhood living",
            target_utilization=0.90,
            legacy_floor_hint=5,
        )

        contract = build_feasible_capacity_contract(
            context,
            site_local_utm=site,
            height_m=15.0,
            floors=5,
            target_utilization=0.90,
            minimum_utilization=0.70,
            floor_capacity_plan=plan,
        )

        self.assertEqual(contract["requested_floors"], 8)
        self.assertEqual(contract["requested_height_m"], 24.0)
        self.assertEqual(
            contract["legal_floor_section_areas_m2"],
            plan["legal_floor_section_areas_m2"],
        )
        self.assertEqual(
            contract["floor_capacity_plan_hash"],
            plan["floor_capacity_plan_hash"],
        )
        self.assertEqual(contract["target_floor_areas_m2"], plan["target_floor_areas_m2"])
