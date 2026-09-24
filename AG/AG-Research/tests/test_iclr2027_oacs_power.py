from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import math
import unittest

from scipy.optimize import brentq
from scipy.stats import nct, t

from iclr2027.oacs_domain_census import (
    DomainCensusV1,
    DomainUnitV1,
    domain_census_bytes,
)
from iclr2027.oacs_power import (
    DomainPowerPlanV1,
    PowerPlanError,
    domain_power_plan_bytes,
    minimum_detectable_effect,
    paired_cluster_power,
    validate_plan_census_binding,
    validate_separate_power_plans,
    verify_domain_power_plan_bytes,
)


class OacsPowerTests(unittest.TestCase):
    def _plan(self, **changes: object) -> DomainPowerPlanV1:
        values: dict[str, object] = {
            "schema": "oacs-domain-power-plan/v1",
            "domain": "architecture",
            "census_sha256": "a" * 64,
            "direction": "one_sided_greater",
            "alpha": 0.05,
            "target_power": 0.80,
            "cluster_count": 12,
            "target_standardized_effect": 0.20,
            "achieved_prospective_power": 0.16011365665870958,
            "minimum_detectable_effect": 0.7664045742339854,
            "multiplicity_family": "architecture_primary",
            "structural_floor_powered": False,
        }
        values.update(changes)
        return DomainPowerPlanV1(**values)  # type: ignore[arg-type]

    def _census_bytes(
        self,
        domain: str,
        *,
        commitment_character: str = "b",
        cluster_count: int = 12,
    ) -> bytes:
        rows = tuple(
            DomainUnitV1(
                domain=domain,
                cluster_id=f"cluster-{position:02d}",
                unit_id=f"unit-{position:02d}",
                partition="focal",
                obligation_families=("compatibility",),
                public_packet_sha256="1" * 64,
                evaluator_commitment_sha256=commitment_character * 64,
                source_rights_status="unrestricted",
                blind_overlap_sha256="2" * 64,
            )
            for position in range(cluster_count)
        )
        return domain_census_bytes(
            DomainCensusV1(
                schema="oacs-domain-census/v1",
                units=rows,
                source_manifest_sha256="3" * 64,
            )
        )

    def test_power_is_monotone_in_clusters_and_effect(self) -> None:
        cluster_powers = tuple(
            paired_cluster_power(cluster_count=count, effect=0.2, alpha=0.05)
            for count in range(3, 101)
        )
        self.assertTrue(
            all(left < right for left, right in zip(cluster_powers, cluster_powers[1:]))
        )
        effect_powers = tuple(
            paired_cluster_power(cluster_count=12, effect=effect, alpha=0.05)
            for effect in (0.0, 0.1, 0.2, 0.5, 1.0)
        )
        self.assertTrue(
            all(left < right for left, right in zip(effect_powers, effect_powers[1:]))
        )

    def test_power_matches_direct_scipy_one_sided_noncentral_t(self) -> None:
        for cluster_count, effect, alpha in (
            (3, 0.0, 0.01),
            (8, 0.2, 0.05),
            (24, 0.5, 0.025),
            (100, 1.0, 0.10),
        ):
            with self.subTest(cluster_count=cluster_count, effect=effect, alpha=alpha):
                degrees_of_freedom = cluster_count - 1
                critical = t.ppf(1.0 - alpha, degrees_of_freedom)
                expected = 1.0 - nct.cdf(
                    critical,
                    degrees_of_freedom,
                    effect * math.sqrt(cluster_count),
                )
                self.assertAlmostEqual(
                    paired_cluster_power(
                        cluster_count=cluster_count,
                        effect=effect,
                        alpha=alpha,
                    ),
                    float(expected),
                    places=14,
                )

    def test_numeric_power_fixtures_are_independently_recomputable(self) -> None:
        expected = {
            8: 0.1287974008989745,
            12: 0.16011365665870958,
            24: 0.24390761181941156,
            40: 0.3438820542078692,
        }
        for cluster_count, fixture in expected.items():
            with self.subTest(cluster_count=cluster_count):
                self.assertAlmostEqual(
                    paired_cluster_power(
                        cluster_count=cluster_count,
                        effect=0.2,
                        alpha=0.05,
                    ),
                    fixture,
                    places=14,
                )

    def test_zero_effect_has_alpha_power_for_the_greater_tail(self) -> None:
        for cluster_count in (3, 8, 40, 100):
            with self.subTest(cluster_count=cluster_count):
                self.assertAlmostEqual(
                    paired_cluster_power(
                        cluster_count=cluster_count,
                        effect=0.0,
                        alpha=0.05,
                    ),
                    0.05,
                    places=14,
                )

    def test_mde_inverts_power(self) -> None:
        effect = minimum_detectable_effect(
            cluster_count=12,
            alpha=0.05,
            target_power=0.80,
        )
        self.assertAlmostEqual(
            paired_cluster_power(cluster_count=12, effect=effect, alpha=0.05),
            0.80,
            places=10,
        )

    def test_numeric_mde_fixtures_and_cluster_monotonicity(self) -> None:
        expected = {
            8: 0.978156085535595,
            12: 0.7664045742339857,
            24: 0.5231756242614581,
            40: 0.40015071418255127,
        }
        observed = []
        for cluster_count, fixture in expected.items():
            with self.subTest(cluster_count=cluster_count):
                value = minimum_detectable_effect(
                    cluster_count=cluster_count,
                    alpha=0.05,
                    target_power=0.80,
                )
                observed.append(value)
                self.assertAlmostEqual(value, fixture, places=11)
        self.assertTrue(
            all(left > right for left, right in zip(observed, observed[1:]))
        )

    def test_scalar_functions_reject_non_native_and_out_of_range_inputs(self) -> None:
        for cluster_count in (True, 3.0, 2, 0, -1):
            with (
                self.subTest(cluster_count=cluster_count),
                self.assertRaises((TypeError, PowerPlanError)),
            ):
                paired_cluster_power(
                    cluster_count=cluster_count,  # type: ignore[arg-type]
                    effect=0.2,
                    alpha=0.05,
                )
        for effect in (True, 1, -0.1, math.inf, -math.inf, math.nan):
            with (
                self.subTest(effect=effect),
                self.assertRaises((TypeError, PowerPlanError)),
            ):
                paired_cluster_power(
                    cluster_count=8,
                    effect=effect,  # type: ignore[arg-type]
                    alpha=0.05,
                )
        for alpha in (True, 0, 0.0, 1.0, -0.1, math.inf, math.nan):
            with (
                self.subTest(alpha=alpha),
                self.assertRaises((TypeError, PowerPlanError)),
            ):
                paired_cluster_power(
                    cluster_count=8,
                    effect=0.2,
                    alpha=alpha,  # type: ignore[arg-type]
                )

    def test_negative_zero_effect_fails_closed(self) -> None:
        with self.assertRaisesRegex(PowerPlanError, "nonnegative"):
            paired_cluster_power(cluster_count=8, effect=-0.0, alpha=0.05)

    def test_mde_rejects_invalid_target_power_and_infeasible_nonnegative_root(
        self,
    ) -> None:
        for target_power in (True, 1, 0.0, 1.0, -0.1, math.inf, math.nan, 0.05, 0.04):
            with (
                self.subTest(target_power=target_power),
                self.assertRaises((TypeError, PowerPlanError)),
            ):
                minimum_detectable_effect(
                    cluster_count=8,
                    alpha=0.05,
                    target_power=target_power,  # type: ignore[arg-type]
                )

    def test_plan_create_records_only_prospective_derived_values(self) -> None:
        plan = DomainPowerPlanV1.create(
            domain="architecture",
            census_sha256="a" * 64,
            direction="one_sided_greater",
            alpha=0.05,
            target_power=0.80,
            cluster_count=12,
            target_standardized_effect=0.20,
            multiplicity_family="architecture_primary",
        )
        self.assertEqual(plan.achieved_prospective_power, 0.16011365665870958)
        self.assertAlmostEqual(plan.minimum_detectable_effect, 0.7664045742339857, 11)
        self.assertIs(plan.structural_floor_powered, False)
        self.assertNotIn("empirical", domain_power_plan_bytes(plan).decode("utf-8"))

    def test_plan_requires_exact_derived_values_and_powered_status(self) -> None:
        for field, value, message in (
            ("achieved_prospective_power", 0.17, "achieved prospective power"),
            ("minimum_detectable_effect", 0.70, "minimum detectable effect"),
            ("structural_floor_powered", True, "structural floor powered"),
        ):
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(PowerPlanError, message),
            ):
                self._plan(**{field: value})

    def test_near_threshold_forged_power_and_status_are_rejected(self) -> None:
        cluster_count = 12
        alpha = 0.05
        target_power = 0.80
        degrees_of_freedom = cluster_count - 1
        critical = t.ppf(1.0 - alpha, degrees_of_freedom)

        def direct_power(effect: float) -> float:
            return float(
                1.0
                - nct.cdf(
                    critical,
                    degrees_of_freedom,
                    effect * math.sqrt(cluster_count),
                )
            )

        mde = float(
            brentq(
                lambda effect: direct_power(effect) - target_power,
                0.0,
                1.0,
                xtol=1e-13,
                rtol=1e-14,
                maxiter=200,
            )
        )
        near_threshold_effect = mde - 1e-13
        self.assertLess(direct_power(near_threshold_effect), target_power)
        forged = {
            "schema": "oacs-domain-power-plan/v1",
            "domain": "architecture",
            "census_sha256": "a" * 64,
            "direction": "one_sided_greater",
            "alpha": alpha,
            "target_power": target_power,
            "cluster_count": cluster_count,
            "target_standardized_effect": near_threshold_effect,
            "achieved_prospective_power": target_power,
            "minimum_detectable_effect": mde,
            "multiplicity_family": "architecture_primary",
            "structural_floor_powered": True,
        }
        raw = (
            json.dumps(forged, sort_keys=True, separators=(",", ":")).encode("utf-8")
            + b"\n"
        )
        with self.assertRaisesRegex(PowerPlanError, "achieved prospective power"):
            verify_domain_power_plan_bytes(raw)

    def test_plan_schema_enums_hashes_and_native_types_are_closed(self) -> None:
        attacks = (
            ("schema", "oacs-domain-power-plan/v2"),
            ("domain", "pooled"),
            ("census_sha256", "A" * 64),
            ("direction", "two_sided"),
            ("multiplicity_family", ""),
            ("cluster_count", True),
            ("alpha", 1),
            ("target_power", 1),
            ("target_standardized_effect", 1),
            ("achieved_prospective_power", math.nan),
            ("minimum_detectable_effect", math.inf),
            ("structural_floor_powered", 0),
        )
        for field, value in attacks:
            with (
                self.subTest(field=field),
                self.assertRaises((TypeError, PowerPlanError)),
            ):
                self._plan(**{field: value})

    def test_plan_bytes_are_canonical_and_round_trip_exactly(self) -> None:
        plan = self._plan()
        raw = domain_power_plan_bytes(plan)
        expected = (
            b'{"achieved_prospective_power":0.16011365665870958,"alpha":0.05,'
            b'"census_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
            b'"cluster_count":12,"direction":"one_sided_greater","domain":"architecture",'
            b'"minimum_detectable_effect":0.7664045742339854,'
            b'"multiplicity_family":"architecture_primary","schema":"oacs-domain-power-plan/v1",'
            b'"structural_floor_powered":false,"target_power":0.8,'
            b'"target_standardized_effect":0.2}\n'
        )
        self.assertEqual(raw, expected)
        self.assertEqual(verify_domain_power_plan_bytes(raw), plan)

    def test_parser_rejects_duplicates_noncanonical_bytes_and_closed_schema_attacks(
        self,
    ) -> None:
        raw = domain_power_plan_bytes(self._plan())
        duplicate = raw.replace(b'"domain":', b'"domain":"jci","domain":', 1)
        with self.assertRaisesRegex(PowerPlanError, "duplicate JSON key"):
            verify_domain_power_plan_bytes(duplicate)
        with self.assertRaisesRegex(PowerPlanError, "canonical"):
            verify_domain_power_plan_bytes(b" " + raw)
        payload = json.loads(raw)
        payload["extra"] = "rejected"
        extra = (
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            + b"\n"
        )
        with self.assertRaisesRegex(PowerPlanError, "closed schema"):
            verify_domain_power_plan_bytes(extra)
        payload.pop("extra")
        payload["census_sha256"] = "g" * 64
        malformed_hash = (
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            + b"\n"
        )
        with self.assertRaisesRegex(PowerPlanError, "lowercase SHA-256"):
            verify_domain_power_plan_bytes(malformed_hash)

    def test_exact_census_hash_binding_rejects_a_valid_resealed_substitution(
        self,
    ) -> None:
        original = self._census_bytes("architecture", commitment_character="b")
        alternate = self._census_bytes("architecture", commitment_character="c")
        self.assertNotEqual(sha256(original).digest(), sha256(alternate).digest())
        plan = self._plan(census_sha256=sha256(original).hexdigest())
        bound = validate_plan_census_binding(plan=plan, census_bytes=original)
        self.assertEqual(bound.cluster_count, 12)
        with self.assertRaisesRegex(PowerPlanError, "census SHA-256 binding"):
            validate_plan_census_binding(plan=plan, census_bytes=alternate)

    def test_census_binding_rejects_cross_domain_and_cluster_count_pooling(
        self,
    ) -> None:
        architecture = self._census_bytes("architecture")
        plan = self._plan(census_sha256=sha256(architecture).hexdigest())
        wrong_count = DomainPowerPlanV1.create(
            domain="architecture",
            census_sha256=sha256(architecture).hexdigest(),
            direction="one_sided_greater",
            alpha=0.05,
            target_power=0.80,
            cluster_count=11,
            target_standardized_effect=0.20,
            multiplicity_family="architecture_primary",
        )
        with self.assertRaisesRegex(PowerPlanError, "cluster count binding"):
            validate_plan_census_binding(plan=wrong_count, census_bytes=architecture)

        jci = self._census_bytes("jci")
        cross_domain = replace(plan, census_sha256=sha256(jci).hexdigest())
        with self.assertRaisesRegex(PowerPlanError, "must not pool domains"):
            validate_plan_census_binding(plan=cross_domain, census_bytes=jci)

    def test_both_separate_domains_must_meet_the_frozen_power_target(self) -> None:
        architecture = DomainPowerPlanV1.create(
            domain="architecture",
            census_sha256="a" * 64,
            direction="one_sided_greater",
            alpha=0.05,
            target_power=0.80,
            cluster_count=12,
            target_standardized_effect=1.0,
            multiplicity_family="architecture_primary",
        )
        jci = DomainPowerPlanV1.create(
            domain="jci",
            census_sha256="b" * 64,
            direction="one_sided_greater",
            alpha=0.05,
            target_power=0.80,
            cluster_count=12,
            target_standardized_effect=1.0,
            multiplicity_family="jci_replication",
        )
        self.assertEqual(
            validate_separate_power_plans((architecture, jci)),
            (architecture, jci),
        )
        underpowered_jci = DomainPowerPlanV1.create(
            domain="jci",
            census_sha256="b" * 64,
            direction="one_sided_greater",
            alpha=0.05,
            target_power=0.80,
            cluster_count=12,
            target_standardized_effect=0.2,
            multiplicity_family="jci_replication",
        )
        with self.assertRaisesRegex(
            PowerPlanError, "jci prospective power insufficient"
        ):
            validate_separate_power_plans((architecture, underpowered_jci))

    def test_separate_domain_gate_rejects_wrong_containers_duplicates_and_order(
        self,
    ) -> None:
        architecture = DomainPowerPlanV1.create(
            domain="architecture",
            census_sha256="a" * 64,
            direction="one_sided_greater",
            alpha=0.05,
            target_power=0.80,
            cluster_count=12,
            target_standardized_effect=1.0,
            multiplicity_family="architecture_primary",
        )
        jci = replace(
            architecture,
            domain="jci",
            census_sha256="b" * 64,
            multiplicity_family="jci_replication",
        )
        for plans in (
            [architecture, jci],
            (architecture,),
            (architecture, architecture),
            (jci, architecture),
        ):
            with (
                self.subTest(plans=plans),
                self.assertRaises((TypeError, PowerPlanError)),
            ):
                validate_separate_power_plans(plans)  # type: ignore[arg-type]

    def test_separate_domain_gate_recomputes_power_instead_of_trusting_status(
        self,
    ) -> None:
        architecture = DomainPowerPlanV1.create(
            domain="architecture",
            census_sha256="a" * 64,
            direction="one_sided_greater",
            alpha=0.05,
            target_power=0.80,
            cluster_count=12,
            target_standardized_effect=1.0,
            multiplicity_family="architecture_primary",
        )
        jci = DomainPowerPlanV1.create(
            domain="jci",
            census_sha256="b" * 64,
            direction="one_sided_greater",
            alpha=0.05,
            target_power=0.80,
            cluster_count=12,
            target_standardized_effect=0.2,
            multiplicity_family="jci_replication",
        )
        object.__setattr__(jci, "structural_floor_powered", True)
        with self.assertRaisesRegex(
            PowerPlanError, "jci prospective power insufficient"
        ):
            validate_separate_power_plans((architecture, jci))


if __name__ == "__main__":
    unittest.main()
