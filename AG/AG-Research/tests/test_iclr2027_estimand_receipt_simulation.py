from __future__ import annotations

import hashlib
import importlib
import json
import math
import sys
import unittest
from dataclasses import fields, replace
from fractions import Fraction
from unittest import mock

import numpy as np
from numpy.random import Generator, Philox
from scipy.stats import t

from iclr2027.estimand_receipt_evaluators import CONFIGURATIONS
from iclr2027.estimand_receipt_simulation import (
    ESTIMAND_ORDER,
    FAMILY_ORDER,
    STREAM_NAMES,
    BatchSufficientStatisticsV1,
    EstimateSufficientStatisticsV1,
    ReplicateSufficientStatisticsV1,
    apply_fault_transforms,
    bound_witnesses,
    build_evaluator_profile,
    finalize_metrics,
    fixed_covariates,
    generate_potential_outcomes,
    misclassification_witnesses,
    overlap_witnesses,
    philox_seed,
    policy_ipw_site,
    registered_scenarios,
    selection_witnesses,
    simulate_batch,
    t7_interval,
)


_FROZEN_PROFILE = None


def _profile():
    global _FROZEN_PROFILE
    if _FROZEN_PROFILE is None:
        _FROZEN_PROFILE = build_evaluator_profile()
    return _FROZEN_PROFILE


def _manual_seed(scenario_id: str, replicate: int, site: int, stream: str) -> int:
    payload = json.dumps(
        ["estimand-receipt-simulation/v1", scenario_id, replicate, site, stream],
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def _rng(scenario_id: str, replicate: int, site: int, stream: str) -> Generator:
    return Generator(Philox(_manual_seed(scenario_id, replicate, site, stream)))


def _scenario(*, tau: Fraction, families: tuple[str, ...], p: Fraction):
    return next(
        row
        for row in registered_scenarios()
        if row.primary
        and row.tau == tau
        and row.families == families
        and row.fault_rate == p
    )


def _literal_scalar_reference(scenario, replicate: int):
    x1 = tuple(Fraction(value, 7) for value in (-7, -5, -3, -1, 1, 3, 5, 7))
    x2 = tuple(Fraction(value) for value in (-1, 1, -1, 1, -1, 1, -1, 1))
    policy = tuple(int(a + b >= 0) for a, b in zip(x1, x2, strict=True))
    site_estimates = {name: [] for name in ESTIMAND_ORDER}
    itt_truth_terms: list[float] = []
    cb_truth_terms: list[float] = []
    policy_truth_terms: list[float] = []
    any_fault = {family: False for family in FAMILY_ORDER}

    for site in range(8):
        u = float(
            _rng(scenario.scenario_id, replicate, site, "site-effect").standard_normal()
        )
        errors = _rng(
            scenario.scenario_id, replicate, site, "unit-error"
        ).standard_normal(8)
        y0: list[float] = []
        y1: list[float] = []
        for target in range(8):
            eta = (
                math.sqrt(float(scenario.icc)) * u
                + math.sqrt(1.0 - float(scenario.icc)) * float(errors[target])
                + 0.25 * float(x1[target])
                - 0.15 * float(x2[target])
            )
            baseline = 0.5 + 0.18 * math.tanh(eta)
            delta = float(scenario.tau + Fraction(1, 25) * x1[target])
            y0.append(baseline - delta / 2.0)
            y1.append(baseline + delta / 2.0)

        assignment = list(
            map(
                int,
                _rng(scenario.scenario_id, replicate, site, "assignment").permutation(
                    np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=np.int8)
                ),
            )
        )
        masks: dict[str, list[bool]] = {}
        for family in FAMILY_ORDER:
            if family in scenario.families:
                uniforms = _rng(
                    scenario.scenario_id, replicate, site, f"fault-{family}"
                ).random(8)
                masks[family] = [
                    float(value) < float(scenario.fault_rate) for value in uniforms
                ]
            else:
                masks[family] = [False] * 8
            any_fault[family] = any_fault[family] or any(masks[family])

        actual_y1 = [
            y0[index] + (0.8 if masks["E"][index] else 1.0) * (y1[index] - y0[index])
            for index in range(8)
        ]
        endpoint = [
            actual_y1[index] if assignment[index] else y0[index] for index in range(8)
        ]
        measured_policy = list(policy)
        for family in FAMILY_ORDER:
            if family == "E":
                continue
            if family == "B":
                before = list(endpoint)
                for index in range(8):
                    if masks[family][index]:
                        endpoint[index] = before[(index + 1) % 8]
            elif family == "T":
                for index in range(8):
                    if masks[family][index]:
                        endpoint[index] = 1.0 - endpoint[index]
            elif family == "S":
                for index in range(8):
                    if masks[family][index]:
                        endpoint[index] += 0.02 * (2 * assignment[index] - 1)
            elif family == "G":
                for index in range(8):
                    if masks[family][index]:
                        endpoint[index] = float(endpoint[index] >= 0.5)
            elif family == "P":
                for index in range(8):
                    if masks[family][index]:
                        measured_policy[index] = 1 - measured_policy[index]

        treated = [endpoint[index] for index, arm in enumerate(assignment) if arm == 1]
        control = [endpoint[index] for index, arm in enumerate(assignment) if arm == 0]
        contrast = math.fsum(treated) / 4.0 - math.fsum(control) / 4.0
        site_estimates["tau_itt"].append(contrast)
        site_estimates["tau_cb"].append(contrast)
        site_estimates["psi_natural"].append(
            math.fsum(
                2.0 * endpoint[index]
                for index, arm in enumerate(assignment)
                if arm == measured_policy[index]
            )
            / 8.0
        )
        itt_truth_terms.extend(actual_y1[index] - y0[index] for index in range(8))
        cb_truth_terms.extend(y1[index] - y0[index] for index in range(8))
        policy_truth_terms.extend(
            actual_y1[index] if policy[index] else y0[index] for index in range(8)
        )

    truths = {
        "tau_itt": math.fsum(itt_truth_terms) / 64.0,
        "tau_cb": math.fsum(cb_truth_terms) / 64.0,
        "psi_natural": math.fsum(policy_truth_terms) / 64.0,
    }
    blocking = {
        "tau_itt": frozenset(("B", "T", "S", "G")),
        "tau_cb": frozenset(("E", "B", "T", "S", "G")),
        "psi_natural": frozenset(("B", "T", "S", "G", "P")),
    }
    result = {}
    critical = float(t.ppf(0.975, 7))
    for estimand in ESTIMAND_ORDER:
        values = site_estimates[estimand]
        estimate = math.fsum(values) / 8.0
        variance = math.fsum((value - estimate) ** 2 for value in values) / 7.0
        se = math.sqrt(variance / 8.0)
        result[estimand] = {
            "truth": truths[estimand],
            "estimate": estimate,
            "se": se,
            "lower": estimate - critical * se,
            "upper": estimate + critical * se,
            "certified": not any(any_fault[item] for item in blocking[estimand]),
        }
    return result


def _deep_size(value: object, seen: set[int] | None = None) -> int:
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        return size + sum(
            _deep_size(key, seen) + _deep_size(item, seen)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list, set, frozenset)):
        return size + sum(_deep_size(item, seen) for item in value)
    if hasattr(value, "__dataclass_fields__"):
        return size + sum(
            _deep_size(getattr(value, field.name), seen) for field in fields(value)
        )
    return size


class ScenarioAndDgpTests(unittest.TestCase):
    def test_scenario_census_order_and_registered_count_are_exact(self):
        scenarios = registered_scenarios()
        self.assertEqual(len(scenarios), 297)
        self.assertEqual(sum(row.primary for row in scenarios), 255)
        self.assertEqual(sum(not row.primary for row in scenarios), 42)
        self.assertEqual(len({row.scenario_id for row in scenarios}), 297)
        self.assertTrue(all(row.scenario_id.isascii() for row in scenarios))
        self.assertTrue(all(row.registered_replications == 2000 for row in scenarios))

        first = scenarios[0]
        self.assertEqual(
            (first.tau, first.icc, first.families, first.fault_rate),
            (Fraction(-1, 10), Fraction(1, 5), (), Fraction(0)),
        )
        self.assertEqual(
            [(row.families, row.fault_rate) for row in scenarios[1:5]],
            [(("E",), Fraction(value, 100)) for value in (1, 5, 10, 20)],
        )
        self.assertEqual(scenarios[25].families, ("E", "B"))
        self.assertEqual(
            (scenarios[255].icc, scenarios[-1].icc),
            (Fraction(1, 20), Fraction(2, 5)),
        )

    def test_fixed_rational_covariates_policy_and_population_identities(self):
        x1, x2, policy = fixed_covariates()
        self.assertEqual(
            x1, tuple(Fraction(value, 7) for value in (-7, -5, -3, -1, 1, 3, 5, 7))
        )
        self.assertEqual(
            x2, tuple(Fraction(value) for value in (-1, 1, -1, 1, -1, 1, -1, 1))
        )
        self.assertEqual(sum(x1), 0)
        self.assertEqual(sum(x2), 0)
        self.assertEqual(policy, (0, 1, 0, 1, 0, 1, 0, 1))

        scenario = registered_scenarios()[0]
        population = generate_potential_outcomes(scenario, replicate=0)
        self.assertEqual(len(population.y0_complete), 64)
        self.assertEqual(len(population.y1_complete), 64)
        self.assertTrue(all(0.0 <= value <= 1.0 for value in population.y0_complete))
        self.assertTrue(all(0.0 <= value <= 1.0 for value in population.y1_complete))
        manual_effect = (
            math.fsum(
                y1 - y0
                for y0, y1 in zip(
                    population.y0_complete, population.y1_complete, strict=True
                )
            )
            / 64.0
        )
        self.assertAlmostEqual(manual_effect, -0.1, places=14)
        self.assertAlmostEqual(population.complete_bundle_effect, -0.1, places=14)
        for endpoint, scores in zip(
            population.y0_complete, population.domain_scores_y0, strict=True
        ):
            self.assertAlmostEqual(math.fsum(scores) / 5.0, endpoint, places=15)
            self.assertTrue(all(0.0 <= value <= 1.0 for value in scores))
        manual_policy = (
            math.fsum(
                population.y1_complete[index]
                if policy[index % 8]
                else population.y0_complete[index]
                for index in range(64)
            )
            / 64.0
        )
        self.assertAlmostEqual(population.policy_value, manual_policy, places=15)

    def test_sha_to_philox_namespaces_are_closed_and_collision_free(self):
        scenario = registered_scenarios()[0]
        expected = _manual_seed(scenario.scenario_id, 7, 3, "assignment")
        self.assertEqual(philox_seed(scenario, 7, 3, "assignment"), expected)
        seeds = {
            philox_seed(scenario, replicate, site, stream)
            for replicate in (0, 1)
            for site in (0, 7)
            for stream in STREAM_NAMES
        }
        self.assertEqual(len(seeds), 4 * len(STREAM_NAMES))
        with self.assertRaises(ValueError):
            philox_seed(scenario, 0, 0, "fault")
        with self.assertRaises(ValueError):
            philox_seed(scenario, -1, 0, "assignment")

    def test_all_six_transforms_compose_in_frozen_order_and_stay_bounded(self):
        endpoint = np.array(
            [[0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.4]], dtype=np.float64
        )
        y0 = np.array([[0.1] * 8], dtype=np.float64)
        assignment = np.array([[1, 0, 1, 0, 1, 0, 1, 0]], dtype=np.int8)
        policy = np.array([[0, 1, 0, 1, 0, 1, 0, 1]], dtype=np.int8)
        masks = {
            "E": np.array([[1, 0, 0, 0, 0, 0, 0, 0]], dtype=bool),
            "B": np.array([[0, 1, 0, 0, 0, 0, 0, 0]], dtype=bool),
            "T": np.array([[0, 0, 1, 0, 0, 0, 0, 0]], dtype=bool),
            "S": np.array([[0, 0, 0, 1, 0, 0, 0, 0]], dtype=bool),
            "G": np.array([[0, 0, 0, 0, 1, 0, 0, 0]], dtype=bool),
            "P": np.array([[0, 0, 0, 0, 0, 1, 0, 0]], dtype=bool),
        }
        measured, decisions = apply_fault_transforms(
            endpoint, y0, assignment, policy, masks
        )
        self.assertEqual(measured.dtype, np.float64)
        np.testing.assert_allclose(
            measured,
            np.array([[0.18, 0.4, 0.6, 0.48, 1.0, 0.7, 0.8, 0.4]], dtype=np.float64),
            rtol=0.0,
            atol=1e-15,
        )
        np.testing.assert_array_equal(
            decisions, np.array([[0, 1, 0, 1, 0, 0, 0, 1]], dtype=np.int8)
        )
        self.assertTrue(np.all((measured >= 0.0) & (measured <= 1.0)))


class SimulationAndInferenceTests(unittest.TestCase):
    def test_vectorized_replicate_matches_literal_scalar_reference(self):
        scenario = _scenario(tau=Fraction(1, 10), families=("E", "P"), p=Fraction(1, 5))
        expected = _literal_scalar_reference(scenario, replicate=3)
        part = simulate_batch(scenario, start=3, count=1, evaluator_profile=_profile())
        replicate = part.replicates[0]
        self.assertEqual(replicate.replicate, 3)
        for estimand in ESTIMAND_ORDER:
            observed = replicate.cell(estimand)
            literal = expected[estimand]
            self.assertAlmostEqual(observed.realized_truth, literal["truth"], places=14)
            self.assertAlmostEqual(observed.estimate, literal["estimate"], places=14)
            self.assertAlmostEqual(observed.standard_error, literal["se"], places=14)
            self.assertAlmostEqual(observed.lower, literal["lower"], places=14)
            self.assertAlmostEqual(observed.upper, literal["upper"], places=14)
            self.assertEqual(observed.oracle_certified, literal["certified"])
            self.assertEqual(observed.reported, literal["certified"])
        x1, _, policy = fixed_covariates()
        manual_policy_truth = (
            Fraction(1, 2)
            + sum(
                (
                    Fraction(1, 2) - Fraction(1, 25)
                    if policy[target]
                    else Fraction(-1, 2)
                )
                * (Fraction(1, 10) + x1[target] / 25)
                for target in range(8)
            )
            / 8
        )
        self.assertEqual(replicate.cell("tau_itt").truth, 0.096)
        self.assertEqual(replicate.cell("tau_cb").truth, 0.1)
        self.assertEqual(
            replicate.cell("psi_natural").truth, float(manual_policy_truth)
        )

    def test_assignment_is_four_four_and_execution_changes_itt_not_complete_bundle_truth(
        self,
    ):
        scenario = _scenario(tau=Fraction(1, 10), families=("E",), p=Fraction(1, 5))
        literal = _literal_scalar_reference(scenario, replicate=0)
        part = simulate_batch(scenario, start=0, count=1, evaluator_profile=_profile())
        replicate = part.replicates[0]
        self.assertEqual(replicate.site_assignment_counts, ((4, 4),) * 8)
        self.assertAlmostEqual(replicate.cell("tau_cb").truth, 0.1, places=14)
        self.assertAlmostEqual(
            replicate.cell("tau_itt").realized_truth,
            literal["tau_itt"]["truth"],
            places=14,
        )
        self.assertEqual(replicate.cell("tau_itt").truth, 0.096)
        self.assertEqual(
            replicate.cell("tau_cb").oracle_certified, literal["tau_cb"]["certified"]
        )
        self.assertTrue(replicate.cell("tau_itt").oracle_certified)

    def test_t7_interval_and_known_propensity_ipw_use_site_level_units(self):
        values = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7)
        interval = t7_interval(values)
        mean = 0.35
        se = math.sqrt(math.fsum((value - mean) ** 2 for value in values) / 7.0 / 8.0)
        critical = float(t.ppf(0.975, 7))
        self.assertAlmostEqual(interval.estimate, mean, places=15)
        self.assertAlmostEqual(interval.standard_error, se, places=15)
        self.assertAlmostEqual(interval.lower, mean - critical * se, places=15)
        self.assertAlmostEqual(interval.upper, mean + critical * se, places=15)

        assignment = (0, 1, 0, 1, 0, 1, 0, 1)
        endpoint = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
        policy = (0, 1, 1, 0, 0, 1, 1, 0)
        manual = 2.0 * (0.1 + 0.2 + 0.5 + 0.6) / 8.0
        self.assertAlmostEqual(
            policy_ipw_site(assignment, endpoint, policy), manual, places=15
        )

    def test_batch_partition_and_call_order_do_not_change_final_metrics(self):
        scenario = _scenario(tau=Fraction(0), families=("B", "T"), p=Fraction(1, 10))
        whole = simulate_batch(scenario, start=0, count=4, evaluator_profile=_profile())
        split = (
            simulate_batch(scenario, start=2, count=2, evaluator_profile=_profile()),
            simulate_batch(scenario, start=0, count=2, evaluator_profile=_profile()),
        )
        other = registered_scenarios()[1]
        before = simulate_batch(
            scenario, start=0, count=1, evaluator_profile=_profile()
        )
        simulate_batch(other, start=0, count=1, evaluator_profile=_profile())
        after = simulate_batch(scenario, start=0, count=1, evaluator_profile=_profile())
        self.assertEqual(before, after)
        self.assertEqual(finalize_metrics((whole,)), finalize_metrics(split))

    def test_registered_replication_override_and_range_attacks_are_rejected(self):
        scenario = registered_scenarios()[0]
        with self.assertRaises(ValueError):
            simulate_batch(
                replace(scenario, registered_replications=20),
                0,
                1,
                evaluator_profile=_profile(),
            )
        with self.assertRaises(ValueError):
            simulate_batch(
                replace(scenario, scenario_id="forged"),
                0,
                1,
                evaluator_profile=_profile(),
            )
        for start, count in ((-1, 1), (0, 0), (1999, 2), (2000, 1)):
            with self.subTest(start=start, count=count), self.assertRaises(ValueError):
                simulate_batch(scenario, start, count, evaluator_profile=_profile())

    def test_dry_twenty_stores_only_replicate_sufficient_statistics(self):
        scenario = registered_scenarios()[0]
        part = simulate_batch(scenario, start=0, count=20, evaluator_profile=_profile())
        self.assertEqual(part.count, 20)
        self.assertEqual(len(part.replicates), 20)
        self.assertEqual(part.registered_replications, 2000)
        self.assertFalse(
            any(
                isinstance(getattr(part, field.name), np.ndarray)
                for field in fields(part)
            )
        )
        self.assertLess(_deep_size(part), 2_500_000)


class MetricAggregationTests(unittest.TestCase):
    @staticmethod
    def _estimate(
        configuration: str,
        estimand: str,
        *,
        truth: float | None,
        estimate: float | None,
        lower: float | None,
        upper: float | None,
        certified: bool,
        reported: bool,
    ) -> EstimateSufficientStatisticsV1:
        return EstimateSufficientStatisticsV1(
            configuration=configuration,
            estimand=estimand,
            truth=truth,
            realized_truth=truth,
            estimate=estimate,
            standard_error=None if estimate is None else 0.04,
            lower=lower,
            upper=upper,
            oracle_certified=certified,
            reported_status="CERTIFIED" if reported else "NOT_CERTIFIED",
            reported=reported,
        )

    def test_counts_fractions_bias_rmse_coverage_and_type_i_are_literal(self):
        scenario = registered_scenarios()[85]
        literal0 = (
            ("tau_itt", 0.0, 0.1, 0.0, 0.2, True, True),
            ("tau_cb", 0.0, 0.0, -0.1, 0.1, True, True),
            ("psi_natural", 0.5, 0.5, 0.4, 0.6, True, True),
        )
        literal1 = (
            ("tau_itt", None, 0.2, 0.1, 0.3, False, True),
            ("tau_cb", None, None, None, None, False, False),
            ("psi_natural", None, None, None, None, False, False),
        )
        cells0 = tuple(
            self._estimate(
                configuration,
                estimand,
                truth=truth,
                estimate=estimate,
                lower=lower,
                upper=upper,
                certified=certified,
                reported=reported,
            )
            for configuration in CONFIGURATIONS
            for estimand, truth, estimate, lower, upper, certified, reported in literal0
        )
        cells1 = tuple(
            self._estimate(
                configuration,
                estimand,
                truth=truth,
                estimate=estimate,
                lower=lower,
                upper=upper,
                certified=certified,
                reported=reported,
            )
            for configuration in CONFIGURATIONS
            for estimand, truth, estimate, lower, upper, certified, reported in literal1
        )
        reps = (
            ReplicateSufficientStatisticsV1(0, cells0, ((4, 4),) * 8),
            ReplicateSufficientStatisticsV1(1, cells1, ((4, 4),) * 8),
        )
        batch = BatchSufficientStatisticsV1(
            scenario_id=scenario.scenario_id,
            evaluator_profile_sha256=_profile().sha256,
            registered_replications=2000,
            start=0,
            count=2,
            replicates=reps,
        )
        row = next(
            item
            for item in finalize_metrics((batch,))
            if item.configuration == "full_estimand_gate" and item.estimand == "tau_itt"
        )
        self.assertEqual(
            (
                row.total,
                row.oracle_certified,
                row.oracle_not_certified,
                row.reported,
                row.false_reported,
                row.eligible_retained,
                row.abstained,
            ),
            (2, 1, 1, 2, 1, 1, 0),
        )
        self.assertEqual(
            (
                row.false_reportability_rate.numerator,
                row.false_reportability_rate.denominator,
            ),
            (1, 1),
        )
        self.assertEqual(
            (
                row.eligible_retention_rate.numerator,
                row.eligible_retention_rate.denominator,
            ),
            (1, 1),
        )
        self.assertEqual(
            (row.abstention_rate.numerator, row.abstention_rate.denominator),
            (0, 2),
        )
        self.assertAlmostEqual(row.bias, 0.1, places=15)
        self.assertAlmostEqual(row.rmse, 0.1, places=15)
        self.assertEqual((row.coverage.numerator, row.coverage.denominator), (1, 1))
        self.assertEqual(
            (row.type_i_error.numerator, row.type_i_error.denominator), (0, 1)
        )
        self.assertIsNone(row.power)
        self.assertIsNone(row.false_sign_probability)

    def test_continuous_metrics_are_na_without_an_identified_reported_target(self):
        scenario = registered_scenarios()[0]
        cells = tuple(
            self._estimate(
                configuration,
                name,
                truth=None,
                estimate=None,
                lower=None,
                upper=None,
                certified=False,
                reported=False,
            )
            for configuration in CONFIGURATIONS
            for name in ESTIMAND_ORDER
        )
        batch = BatchSufficientStatisticsV1(
            scenario_id=scenario.scenario_id,
            evaluator_profile_sha256=_profile().sha256,
            registered_replications=2000,
            start=0,
            count=1,
            replicates=(ReplicateSufficientStatisticsV1(0, cells, ((4, 4),) * 8),),
        )
        for row in finalize_metrics((batch,)):
            self.assertIsNone(row.bias)
            self.assertIsNone(row.rmse)
            self.assertIsNone(row.coverage.numerator)
            self.assertIsNone(row.coverage.denominator)
            self.assertEqual(
                row.probability_context("coverage").status,
                "ZERO_DENOMINATOR",
            )
            self.assertIsNone(row.type_i_error)
            if row.estimand == "psi_natural":
                self.assertIsNone(row.power)
                self.assertIsNone(row.false_sign_probability)
            else:
                self.assertIsNone(row.power.numerator)
                self.assertIsNone(row.power.denominator)
                self.assertIsNone(row.false_sign_probability.numerator)
                self.assertIsNone(row.false_sign_probability.denominator)


class ExactFiniteWitnessTests(unittest.TestCase):
    def test_corrected_m_q_d_bound_and_99_over_50_attainment_are_exact(self):
        rows = {item.name: item for item in bound_witnesses()}
        self.assertEqual(set(rows), {"m_q_d", "attainment_99_over_50"})
        generic = rows["m_q_d"]
        manual = sum(
            row.analysis_weight
            * (
                row.replacement
                + (1 - row.replacement)
                * min(Fraction(1), row.omitted_mass + row.residual_tv)
            )
            for row in generic.rows
        )
        self.assertEqual(generic.bound, manual)

        sharp = rows["attainment_99_over_50"]
        self.assertEqual(sharp.true_contrast, Fraction(1))
        self.assertEqual(sharp.measured_contrast, Fraction(-49, 50))
        self.assertEqual(
            abs(sharp.measured_contrast - sharp.true_contrast), Fraction(99, 50)
        )
        self.assertEqual(sharp.bound, Fraction(99, 50))
        self.assertEqual(
            sharp.true_arm_laws, (((0, Fraction(1)),), ((1, Fraction(1)),))
        )
        self.assertEqual(
            sharp.measured_arm_laws,
            (
                ((0, Fraction(1, 100)), (1, Fraction(99, 100))),
                ((0, Fraction(99, 100)), (1, Fraction(1, 100))),
            ),
        )

    def test_common_and_differential_misclassification_include_sign_reversal(self):
        rows = {item.name: item for item in misclassification_witnesses()}
        common = rows["common_misclassification"]
        manual_common = (
            1
            - common.sp1
            + (common.se1 + common.sp1 - 1) * common.mu1
            - (1 - common.sp0 + (common.se0 + common.sp0 - 1) * common.mu0)
        )
        self.assertEqual(common.measured_contrast, manual_common)
        self.assertEqual(common.measured_contrast, Fraction(4, 25))
        reversal = rows["differential_sign_reversal"]
        self.assertEqual(reversal.true_contrast, Fraction(1, 5))
        self.assertEqual(reversal.measured_contrast, Fraction(-1, 10))

    def test_mcar_mar_mnar_and_ipw_boundary_use_literal_finite_worlds(self):
        rows = {item.name: item for item in selection_witnesses()}
        self.assertEqual(set(rows), {"mcar", "mar_ipw", "mnar_pair"})
        mcar = rows["mcar"].worlds[0]
        self.assertEqual(mcar.population_mean, Fraction(1, 2))
        self.assertEqual(mcar.complete_case_mean, Fraction(1, 2))
        self.assertEqual(mcar.ipw_mean, Fraction(1, 2))
        mar = rows["mar_ipw"].worlds[0]
        self.assertEqual(mar.population_mean, Fraction(1, 2))
        self.assertEqual(mar.complete_case_mean, Fraction(3, 4))
        self.assertEqual(mar.ipw_mean, Fraction(1, 2))
        p, q = rows["mnar_pair"].worlds
        self.assertEqual(p.observed_law, q.observed_law)
        self.assertNotEqual(p.population_mean, q.population_mean)
        self.assertEqual(rows["mnar_pair"].status, "BOUNDS_OR_SENSITIVITY_ONLY")

    def test_disjoint_nested_and_full_overlap_use_actual_fault_sets(self):
        rows = {item.name: item for item in overlap_witnesses()}
        self.assertEqual(set(rows), {"disjoint", "nested", "full_overlap"})
        self.assertEqual(rows["disjoint"].sum_count, 4)
        self.assertEqual(rows["disjoint"].union_count, 4)
        self.assertEqual(rows["nested"].sum_count, 3)
        self.assertEqual(rows["nested"].union_count, 2)
        self.assertEqual(rows["full_overlap"].sum_count, 4)
        self.assertEqual(rows["full_overlap"].union_count, 2)
        for row in rows.values():
            self.assertEqual(row.union_units, frozenset().union(*row.family_units))

    def test_finite_witnesses_are_not_monte_carlo_scenarios(self):
        scenario_ids = {row.scenario_id for row in registered_scenarios()}
        witness_names = {
            *(row.name for row in bound_witnesses()),
            *(row.name for row in misclassification_witnesses()),
            *(row.name for row in selection_witnesses()),
            *(row.name for row in overlap_witnesses()),
        }
        self.assertTrue(scenario_ids.isdisjoint(witness_names))
        self.assertEqual(len(registered_scenarios()), 297)


class ReviewFixRoundOneTests(unittest.TestCase):
    @staticmethod
    def _module():
        return importlib.import_module("iclr2027.estimand_receipt_simulation")

    def test_profile_uses_live_task6_is_oracle_independent_and_changes_reports(self):
        simulation = self._module()
        if not hasattr(simulation, "build_evaluator_profile"):
            self.fail("no evaluator profile builder")
        evaluators = importlib.import_module("iclr2027.estimand_receipt_evaluators")
        oracle = importlib.import_module("iclr2027.estimand_receipt_oracle")
        profile = simulation.build_evaluator_profile()
        self.assertEqual(len(profile.entries), 64 * 11 * 3)

        with mock.patch.object(
            evaluators,
            "evaluate_configuration",
            side_effect=RuntimeError("raising evaluator sentinel"),
        ):
            with self.assertRaisesRegex(RuntimeError, "raising evaluator sentinel"):
                simulation.build_evaluator_profile()
            frozen_batch = simulation.simulate_batch(
                registered_scenarios()[0], 0, 1, evaluator_profile=profile
            )
        self.assertEqual(frozen_batch.evaluator_profile_sha256, profile.sha256)

        with mock.patch.object(
            oracle,
            "oracle_reportability",
            side_effect=RuntimeError("raising oracle sentinel"),
        ):
            rebuilt = simulation.build_evaluator_profile()
        self.assertEqual(rebuilt.canonical_bytes, profile.canonical_bytes)
        self.assertEqual(rebuilt.sha256, profile.sha256)

        wrong_entries = tuple(
            replace(entry, status="NOT_CERTIFIED") for entry in profile.entries
        )
        wrong = simulation.EvaluatorProfileV1.create(wrong_entries)
        actual_metrics = simulation.finalize_metrics(
            (
                simulation.simulate_batch(
                    registered_scenarios()[0], 0, 2, evaluator_profile=profile
                ),
            )
        )
        wrong_metrics = simulation.finalize_metrics(
            (
                simulation.simulate_batch(
                    registered_scenarios()[0], 0, 2, evaluator_profile=wrong
                ),
            )
        )
        actual = next(
            row
            for row in actual_metrics
            if row.configuration == "full_estimand_gate" and row.estimand == "tau_itt"
        )
        forced = next(
            row
            for row in wrong_metrics
            if row.configuration == "full_estimand_gate" and row.estimand == "tau_itt"
        )
        self.assertEqual(actual.reported, 2)
        self.assertEqual(forced.reported, 0)

    def test_profile_cells_match_independent_direct_task6_evaluation(self):
        simulation = self._module()
        if not hasattr(simulation, "build_evaluator_profile"):
            self.fail("no evaluator profile builder")
        from iclr2027.estimand_receipt_evaluators import (
            CONFIGURATIONS,
            evaluate_configuration,
        )
        from iclr2027.estimand_receipt_faults import apply_fault
        from iclr2027.estimand_receipt_generator import generate_clean_benchmark

        clean = generate_clean_benchmark()
        source = clean.artifacts[0]
        artifacts = {row.unit_id: row for row in clean.artifacts}
        representative = {
            "E": ("execution_omit_geometry", source),
            "B": (
                "target_rebind_same_site_same_assignment",
                artifacts["syn-target-00-04"],
            ),
            "T": ("terminal_stale_owner", source),
            "S": ("scorer_drop_geometry", source),
            "G": ("protocol_stale_incompatible", source),
            "P": ("policy_menu_drift", source),
        }
        mutated = source
        for family in ("E", "B"):
            name, partner = representative[family]
            mutated = apply_fault(mutated, name, partner=partner)
        case_id = hashlib.sha256(b"independent-profile-E+B").hexdigest()
        public = json.dumps(
            {
                "schema_version": "public-artifact-row/v1",
                "case_id": case_id,
                "artifact": mutated.to_dict(),
            },
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        root = json.dumps(
            clean.trust_root.to_dict(),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        profile = simulation.build_evaluator_profile()
        for configuration in CONFIGURATIONS:
            direct = evaluate_configuration(configuration, (public,), root)
            for row in direct:
                self.assertEqual(
                    profile.lookup(("E", "B"), configuration, row.estimand).status,
                    row.status,
                )

    def test_sharp_bound_rejects_empty_and_zero_contrast_law_forgery(self):
        sharp = bound_witnesses()[1]
        with self.assertRaises(ValueError):
            replace(sharp, true_arm_laws=())
        zero_contrast = (((0, Fraction(1)),), ((0, Fraction(1)),))
        with self.assertRaises(ValueError):
            replace(sharp, true_arm_laws=zero_contrast)
        arm_means = tuple(
            tuple(sum(value * mass for value, mass in law) for law in arms)
            for arms in (sharp.true_arm_laws, sharp.measured_arm_laws)
        )
        self.assertEqual(
            arm_means,
            ((Fraction(0), Fraction(1)), (Fraction(99, 100), Fraction(1, 100))),
        )
        self.assertEqual(sharp.true_contrast, Fraction(1))
        self.assertEqual(sharp.measured_contrast, Fraction(-49, 50))
        self.assertEqual(sharp.attained_error, Fraction(99, 50))
        self.assertTrue(sharp.attains_bound)

    def test_configuration_conditional_joint_and_always_abstain_metrics(self):
        simulation = self._module()
        if not hasattr(simulation, "build_evaluator_profile"):
            self.fail("no evaluator profile builder")
        profile = simulation.build_evaluator_profile()
        abstain = simulation.EvaluatorProfileV1.create(
            tuple(replace(entry, status="NOT_CERTIFIED") for entry in profile.entries)
        )
        batch = simulation.simulate_batch(
            registered_scenarios()[0], 0, 2, evaluator_profile=abstain
        )
        rows = simulation.finalize_metrics((batch,))
        self.assertEqual(len(rows), 11 * 3)
        row = next(
            item
            for item in rows
            if item.configuration == "full_estimand_gate" and item.estimand == "tau_itt"
        )
        self.assertEqual(row.exact_decisions, 0)
        self.assertEqual(row.eligible_retention_rate.numerator, 0)
        self.assertEqual(row.eligible_retention_rate.denominator, 2)
        self.assertEqual(row.abstention_rate.numerator, 2)
        self.assertEqual(row.abstention_rate.denominator, 2)
        self.assertIsNone(row.conditional_report_accuracy.numerator)
        self.assertEqual(row.joint_decision_accuracy.numerator, 0)
        self.assertEqual(row.joint_decision_accuracy.denominator, 2)

    def test_bounded_abstention_is_not_an_exact_not_certified_decision(self):
        simulation = self._module()
        profile = simulation.build_evaluator_profile()
        bounded = simulation.EvaluatorProfileV1.create(
            tuple(replace(entry, status="BOUNDED") for entry in profile.entries)
        )
        scenario = _scenario(tau=Fraction(0), families=("B",), p=Fraction(1, 5))
        batch = simulation.simulate_batch(scenario, 0, 1, evaluator_profile=bounded)
        row = next(
            item
            for item in simulation.finalize_metrics((batch,))
            if item.configuration == "full_estimand_gate" and item.estimand == "tau_itt"
        )
        self.assertEqual(row.oracle_not_certified, 1)
        self.assertEqual(row.reported, 0)
        self.assertEqual(row.exact_decisions, 0)

    def test_e_tau_zero_uses_one_exact_marginal_truth_for_all_metrics(self):
        simulation = self._module()
        if not hasattr(simulation, "build_evaluator_profile"):
            self.fail("no evaluator profile builder")
        profile = simulation.build_evaluator_profile()
        scenario = _scenario(tau=Fraction(0), families=("E",), p=Fraction(1, 5))
        batch = simulation.simulate_batch(scenario, 0, 4, evaluator_profile=profile)
        full_cells = tuple(
            replicate.cell("tau_itt", "full_estimand_gate")
            for replicate in batch.replicates
        )
        self.assertTrue(all(cell.truth == 0.0 for cell in full_cells))
        self.assertNotEqual(full_cells[0].realized_truth, 0.0)
        row = next(
            item
            for item in simulation.finalize_metrics((batch,))
            if item.configuration == "full_estimand_gate" and item.estimand == "tau_itt"
        )
        self.assertAlmostEqual(
            row.bias,
            math.fsum(cell.estimate for cell in full_cells) / len(full_cells),
            places=15,
        )
        self.assertEqual(
            row.coverage.numerator,
            sum(cell.lower <= 0.0 <= cell.upper for cell in full_cells),
        )
        self.assertEqual(row.coverage.denominator, len(full_cells))
        self.assertEqual(
            row.type_i_error.numerator,
            sum(not (cell.lower <= 0.0 <= cell.upper) for cell in full_cells),
        )

    def test_clopper_pearson_boundaries_interior_and_na_are_frozen(self):
        simulation = self._module()
        if not hasattr(simulation, "exact_probability"):
            self.fail("no Clopper-Pearson probability constructor")
        from scipy.stats import beta

        zero = simulation.exact_probability(0, 10)
        full = simulation.exact_probability(10, 10)
        interior = simulation.exact_probability(3, 10)
        na = simulation.exact_probability(0, 0)
        self.assertEqual(zero.lower, 0.0)
        self.assertAlmostEqual(zero.upper, float(beta.ppf(0.975, 1, 10)), places=15)
        self.assertAlmostEqual(full.lower, float(beta.ppf(0.025, 10, 1)), places=15)
        self.assertEqual(full.upper, 1.0)
        self.assertAlmostEqual(interior.lower, float(beta.ppf(0.025, 3, 8)), places=15)
        self.assertAlmostEqual(interior.upper, float(beta.ppf(0.975, 4, 7)), places=15)
        self.assertEqual(interior.interval_method, "clopper-pearson-95")
        self.assertEqual(
            (na.numerator, na.denominator, na.lower, na.upper, na.interval_method),
            (None, None, None, None, None),
        )


class ReviewFixRoundTwoTests(unittest.TestCase):
    def test_generic_bound_rejects_zero_forgery_and_derives_each_m_q_d_primitive(self):
        generic = {item.name: item for item in bound_witnesses()}["m_q_d"]
        zero = (((0, Fraction(1)),), ((0, Fraction(1)),))
        with self.assertRaises(ValueError):
            replace(generic, true_arm_laws=zero, measured_arm_laws=zero)
        keyed_zero = ((("a", 0, Fraction(1)),), (("a", 0, Fraction(1)),))
        identity_maps = ((("a", "a"),), (("a", "a"),))
        with self.assertRaises(ValueError):
            replace(
                generic,
                true_arm_laws=keyed_zero,
                measured_arm_laws=keyed_zero,
                declared_maps=identity_maps,
            )
        with self.assertRaises(ValueError):
            replace(generic, declared_maps=((), generic.declared_maps[1]))
        with self.assertRaises(ValueError):
            replace(
                generic,
                true_arm_laws=(
                    generic.true_arm_laws[0] + (("c", 0, Fraction(1, 10)),),
                    generic.true_arm_laws[1],
                ),
            )
        with self.assertRaises(ValueError):
            replace(
                generic,
                true_arm_laws=(
                    (
                        ("a", 0, Fraction(1, 2)),
                        ("b", 0, Fraction(1, 2)),
                        ("c", 0, Fraction(1, 2)),
                    ),
                    generic.true_arm_laws[1],
                ),
            )
        sharp = {item.name: item for item in bound_witnesses()}["attainment_99_over_50"]
        with self.assertRaises(ValueError):
            replace(
                sharp,
                name="m_q_d",
                true_arm_laws=zero,
                measured_arm_laws=zero,
            )
        self.assertEqual(
            tuple(field.name for field in fields(generic)),
            ("name", "true_arm_laws", "measured_arm_laws", "declared_maps"),
        )

        independently_derived = []
        for true_law, measured_law, declared_map in zip(
            generic.true_arm_laws,
            generic.measured_arm_laws,
            generic.declared_maps,
            strict=True,
        ):
            true = {key: (outcome, mass) for key, outcome, mass in true_law}
            measured = {key: (outcome, mass) for key, outcome, mass in measured_law}
            binding = dict(declared_map)
            mapped_targets = set(binding.values())
            replacement = int(any(source != target for source, target in declared_map))
            omitted_mass = sum(
                (mass for key, (_, mass) in true.items() if key not in mapped_targets),
                Fraction(0),
            )
            if replacement:
                residual_tv = Fraction(0)
            else:
                retained_mass = sum(
                    (true[target][1] for target in mapped_targets), Fraction(0)
                )
                true_outcomes = {
                    outcome: sum(
                        (
                            mass / retained_mass
                            for key, (value, mass) in true.items()
                            if key in mapped_targets and value == outcome
                        ),
                        Fraction(0),
                    )
                    for outcome in (0, 1)
                }
                measured_outcomes = {
                    outcome: sum(
                        (mass for value, mass in measured.values() if value == outcome),
                        Fraction(0),
                    )
                    for outcome in (0, 1)
                }
                residual_tv = (
                    sum(
                        (
                            abs(true_outcomes[outcome] - measured_outcomes[outcome])
                            for outcome in (0, 1)
                        ),
                        Fraction(0),
                    )
                    / 2
                )
            independently_derived.append((replacement, omitted_mass, residual_tv))

        self.assertEqual(
            tuple(
                (row.replacement, row.omitted_mass, row.residual_tv)
                for row in generic.rows
            ),
            tuple(independently_derived),
        )
        self.assertTrue(
            any(replacement > 0 for replacement, _, _ in independently_derived)
        )
        self.assertTrue(any(q > 0 for _, q, _ in independently_derived))
        self.assertTrue(any(d > 0 for _, _, d in independently_derived))
        manual_bound = sum(
            Fraction(1) * (replacement + (1 - replacement) * min(Fraction(1), q + d))
            for replacement, q, d in independently_derived
        )
        true_means = tuple(
            sum((Fraction(outcome) * mass for _, outcome, mass in law), Fraction(0))
            for law in generic.true_arm_laws
        )
        measured_means = tuple(
            sum((Fraction(outcome) * mass for _, outcome, mass in law), Fraction(0))
            for law in generic.measured_arm_laws
        )
        manual_error = abs(
            (measured_means[1] - measured_means[0]) - (true_means[1] - true_means[0])
        )
        self.assertEqual(generic.bound, manual_bound)
        self.assertEqual(generic.attained_error, manual_error)
        self.assertEqual(manual_error, manual_bound)

    def test_applicable_zero_report_denominator_is_exact_na_not_inapplicable(self):
        simulation = importlib.import_module("iclr2027.estimand_receipt_simulation")
        profile = simulation.build_evaluator_profile()
        abstain = simulation.EvaluatorProfileV1.create(
            tuple(replace(entry, status="NOT_CERTIFIED") for entry in profile.entries)
        )
        scenario = registered_scenarios()[85]
        batch = simulation.simulate_batch(scenario, 0, 1, evaluator_profile=abstain)
        row = next(
            item
            for item in simulation.finalize_metrics((batch,))
            if item.configuration == "full_estimand_gate" and item.estimand == "tau_itt"
        )
        exact_na = {
            "numerator": None,
            "denominator": None,
            "lower": None,
            "upper": None,
            "interval_method": None,
        }
        self.assertEqual(row.coverage.to_dict(), exact_na)
        self.assertEqual(row.type_i_error.to_dict(), exact_na)
        coverage_context = row.probability_context("coverage")
        type_i_context = row.probability_context("type_i_error")
        self.assertEqual(
            (
                coverage_context.applicability,
                coverage_context.status,
                coverage_context.reason,
                coverage_context.eligible_n,
                coverage_context.reported_n,
            ),
            (
                "APPLICABLE",
                "ZERO_DENOMINATOR",
                "NO_REPORTED_ORACLE_CERTIFIED_ESTIMATES",
                1,
                0,
            ),
        )
        self.assertEqual(type_i_context, coverage_context.for_metric("type_i_error"))

        self.assertIsNone(row.power)
        self.assertIsNone(row.false_sign_probability)
        power_context = row.probability_context("power")
        sign_context = row.probability_context("false_sign_probability")
        self.assertEqual(power_context.applicability, "INAPPLICABLE")
        self.assertEqual(power_context.status, "INAPPLICABLE")
        self.assertEqual(power_context.reason, "NULL_SCENARIO")
        self.assertEqual(sign_context.reason, "NULL_SCENARIO")

        payload = row.to_dict()
        self.assertEqual(payload["coverage"], exact_na)
        self.assertEqual(payload["type_i_error"], exact_na)
        self.assertIsNone(payload["power"])
        self.assertEqual(
            payload["probability_contexts"]["coverage"],
            coverage_context.to_dict(),
        )
        canonical = json.dumps(
            payload,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertEqual(
            canonical,
            json.dumps(
                row.to_dict(),
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    def test_zero_oracle_denominator_and_structural_psi_na_have_distinct_reasons(self):
        simulation = importlib.import_module("iclr2027.estimand_receipt_simulation")
        profile = simulation.build_evaluator_profile()
        scenario = _scenario(tau=Fraction(0), families=("B",), p=Fraction(1, 5))
        batch = simulation.simulate_batch(scenario, 0, 1, evaluator_profile=profile)
        tau_row = next(
            item
            for item in simulation.finalize_metrics((batch,))
            if item.configuration == "full_estimand_gate" and item.estimand == "tau_itt"
        )
        self.assertIsNotNone(tau_row.coverage)
        self.assertIsNone(tau_row.coverage.denominator)
        self.assertIsNotNone(tau_row.joint_coverage)
        self.assertIsNone(tau_row.joint_coverage.denominator)
        self.assertEqual(
            tau_row.probability_context("coverage").reason,
            "NO_ORACLE_CERTIFIED_ESTIMATES",
        )
        self.assertEqual(
            tau_row.probability_context("joint_coverage").reason,
            "NO_ORACLE_CERTIFIED_ESTIMATES",
        )

        psi_row = next(
            item
            for item in simulation.finalize_metrics((batch,))
            if item.configuration == "full_estimand_gate"
            and item.estimand == "psi_natural"
        )
        self.assertIsNone(psi_row.type_i_error)
        psi_context = psi_row.probability_context("type_i_error")
        self.assertEqual(psi_context.applicability, "INAPPLICABLE")
        self.assertEqual(psi_context.reason, "ESTIMAND_NOT_ZERO_EFFECT_TEST")


if __name__ == "__main__":
    unittest.main()
