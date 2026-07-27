from django.test import SimpleTestCase

from design.maas.book_language.capacity_alternatives import (
    CAPACITY_ALTERNATIVE_SPECS,
    build_capacity_alternative,
    capacity_fit_score,
    capacity_retry_plan_coverage,
    capacity_alternative_for_host,
    capacity_alternative_for_lattice_index,
    capacity_contract_for_alternative,
    evaluate_capacity_alternative,
)


class MaasCapacityAlternativeTest(SimpleTestCase):
    def setUp(self):
        self.contract = {
            "schema_version": "arr.maas.feasible_base_capacity.v1",
            "minimum_utilization": 0.70,
            "target_utilization": 0.90,
            "feasible_maximum_floor_area_m2": 1000.0,
            "height_field_capacity_m2": 1000.0,
            "generation_site_area_m2": 250.0,
            "requested_floors": 5,
        }

    def test_four_alternatives_are_monotonic_and_site_derived(self):
        alternatives = [
            build_capacity_alternative(self.contract, spec)
            for spec in CAPACITY_ALTERNATIVE_SPECS
        ]

        self.assertEqual(
            [item["alternative_id"] for item in alternatives],
            ["spatial_reserve", "balanced_yield", "brief_target", "maximum_feasible"],
        )
        self.assertEqual(
            [item["target_utilization"] for item in alternatives],
            [0.70, 0.80, 0.90, 0.95],
        )
        self.assertEqual(alternatives[-1]["target_floor_area_m2"], 950.0)
        # A floorwise legal field needs the same 95% yield on every section.
        # Dividing total GFA by five underfills the lower legal sections.
        self.assertEqual(alternatives[-1]["target_base_plan_area_m2"], 237.5)
        self.assertEqual(alternatives[-1]["target_base_plan_coverage"], 0.95)
        self.assertEqual(
            alternatives[-1]["target_rule"],
            "midpoint_of_program_target_and_feasible_ceiling",
        )
        self.assertTrue(all(item["hard_gates_remain_downstream"] for item in alternatives))

    def test_projection_copy_changes_target_without_mutating_base_contract(self):
        contract = {
            **self.contract,
            "bcr_adjusted_floor_areas_m2": [200.0] * 5,
            "target_floor_areas_m2": [180.0] * 5,
        }
        alternative = build_capacity_alternative(contract, "maximum_feasible")
        projected = capacity_contract_for_alternative(contract, alternative)

        self.assertEqual(self.contract["target_utilization"], 0.90)
        self.assertEqual(projected["target_utilization"], 0.95)
        self.assertEqual(projected["capacity_alternative_id"], "maximum_feasible")
        self.assertEqual(projected["target_floor_areas_m2"], [190.0] * 5)
        self.assertEqual(
            sum(projected["target_floor_areas_m2"]),
            projected["target_floor_area_m2"],
        )
        self.assertEqual(contract["target_floor_areas_m2"], [180.0] * 5)

    def test_measured_result_records_target_gap(self):
        alternative = build_capacity_alternative(self.contract, "brief_target")
        evaluated = evaluate_capacity_alternative(
            alternative,
            {
                "schema_version": "arr.maas.source_capacity_measurement.v1",
                "feasible_capacity_utilization": 0.92,
            },
        )

        self.assertTrue(evaluated["target_hard_pass"])
        self.assertEqual(evaluated["target_gap"], 0.02)

    def test_measured_result_resolves_highest_achieved_capacity_band_independently_of_lattice_assignment(self):
        requested = build_capacity_alternative(
            self.contract,
            "maximum_feasible",
        )

        reserve = evaluate_capacity_alternative(
            requested,
            {"feasible_capacity_utilization": 0.79},
        )
        balanced = evaluate_capacity_alternative(
            requested,
            {"feasible_capacity_utilization": 0.81},
        )
        below_minimum = evaluate_capacity_alternative(
            requested,
            {"feasible_capacity_utilization": 0.69},
        )

        self.assertFalse(reserve["target_hard_pass"])
        self.assertTrue(reserve["selectable_capacity_hard_pass"])
        self.assertEqual(
            reserve["selectable_capacity_alternative_id"],
            "spatial_reserve",
        )
        self.assertEqual(
            balanced["selectable_capacity_alternative_id"],
            "balanced_yield",
        )
        self.assertFalse(below_minimum["selectable_capacity_hard_pass"])
        self.assertEqual(
            below_minimum["selectable_capacity_alternative_id"],
            "",
        )

    def test_lattice_sampling_cycles_without_random_state(self):
        sampled = [
            capacity_alternative_for_lattice_index(index).alternative_id
            for index in range(8)
        ]

        self.assertEqual(sampled[:4], sampled[4:])

    def test_host_sampling_never_assigns_a_mathematically_unreachable_target(self):
        # 100 m² × 5 floors / 1000 m² feasible maximum = 0.50 upper bound,
        # below even the 0.70 reserve target, so only the lowest band remains.
        self.assertEqual(
            capacity_alternative_for_host(
                3,
                self.contract,
                host_area_m2=100.0,
                floor_count=5,
            ).alternative_id,
            "spatial_reserve",
        )
        # A full 200 m² × 5-floor host can reach the denominator and keeps the
        # complete deterministic four-band cycle.
        self.assertEqual(
            capacity_alternative_for_host(
                3,
                self.contract,
                host_area_m2=200.0,
                floor_count=5,
            ).alternative_id,
            "maximum_feasible",
        )

    def test_capacity_score_rewards_target_fit_without_hiding_absolute_yield(self):
        alternative = build_capacity_alternative(self.contract, "maximum_feasible")

        self.assertGreater(
            capacity_fit_score(
                alternative,
                {"feasible_capacity_utilization": 0.98},
            ),
            capacity_fit_score(
                alternative,
                {"feasible_capacity_utilization": 0.80},
            ),
        )

    def test_retry_coverage_is_measured_bounded_and_does_not_loop_a_pass(self):
        alternative = build_capacity_alternative(self.contract, "brief_target")
        self.assertEqual(
            capacity_retry_plan_coverage(
                0.60,
                alternative,
                {"feasible_capacity_utilization": 0.60},
            ),
            0.90,
        )
        self.assertEqual(
            capacity_retry_plan_coverage(
                0.90,
                alternative,
                {"feasible_capacity_utilization": 0.90},
            ),
            0.90,
        )
        self.assertEqual(
            capacity_retry_plan_coverage(
                0.90,
                alternative,
                {"feasible_capacity_utilization": 0.10},
            ),
            0.95,
        )
