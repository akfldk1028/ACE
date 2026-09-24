from __future__ import annotations

import math
import unittest
from dataclasses import FrozenInstanceError, fields, replace
from fractions import Fraction

from iclr2027.estimand_receipt_theory import (
    BoundRow,
    PairedWorldWitness,
    contrast_error_bound,
    contrast_error_bound_exact,
    invariance_certificates,
    paired_world_witnesses,
    selection_estimand_status,
    terminal_measured_contrast,
    terminal_measured_contrast_exact,
)


F = Fraction


TEST_A_COMPLETE = (("bundle", "complete"), ("members", ("m1", "m2")))
TEST_A_PARTIAL = (("bundle", "partial"), ("members", ("m1",)))
TEST_E_IDENTITY = (
    ("order", ("m1", "m2")),
    (
        "regime_map",
        (("complete", "slot-complete"), ("partial", "slot-partial")),
    ),
    ("version", "exec-v1"),
)
TEST_E_SWAPPED = (
    ("order", ("m1", "m2")),
    (
        "regime_map",
        (("complete", "slot-partial"), ("partial", "slot-complete")),
    ),
    ("version", "exec-v2"),
)
TEST_SLOTS_0 = (("slot-complete", F(0)), ("slot-partial", F(0)))
TEST_SLOTS_1 = (("slot-complete", F(1)), ("slot-partial", F(0)))
TEST_T_IDENTITY = (
    ("owner", "canonical"),
    ("value_map", (("high", F(1)), ("low", F(0)))),
)
TEST_T_REVERSED = (
    ("owner", "reversed"),
    ("value_map", (("high", F(0)), ("low", F(1)))),
)
TEST_S_A = (("key-a", F(1)), ("key-b", F(0)))
TEST_S_B = (("key-a", F(0)), ("key-b", F(1)))
TEST_G_IDENTITY = (
    ("protocol_id", "success-v1"),
    ("truth_map", (("fail", F(0)), ("pass", F(1)))),
)
TEST_G_REVERSED = (
    ("protocol_id", "reversed-v2"),
    ("truth_map", (("fail", F(1)), ("pass", F(0)))),
)
TEST_POLICY_A = (
    ("action_menu", ("a", "b")),
    ("decision_rule", (("x0", "a"), ("x1", "a"))),
    ("information_snapshot", "x"),
    ("policy_id", "policy-a"),
    ("propensity", F(1, 2)),
)
TEST_POLICY_B = (
    ("action_menu", ("a", "b")),
    ("decision_rule", (("x0", "a"), ("x1", "b"))),
    ("information_snapshot", "x"),
    ("policy_id", "policy-b"),
    ("propensity", F(1, 2)),
)
TEST_POTENTIAL_0 = (("a", F(1)), ("b", F(0)))
TEST_POTENTIAL_1 = (("a", F(0)), ("b", F(1)))


EXPECTED_WORLDS = {
    "Z": {
        "estimand": "tau_ITT",
        "p": (
            ((("Y", F(0)), ("Z", 0)), F(1, 2)),
            ((("Y", F(1)), ("Z", 1)), F(1, 2)),
        ),
        "q": (
            ((("Y", F(0)), ("Z", 1)), F(1, 2)),
            ((("Y", F(1)), ("Z", 0)), F(1, 2)),
        ),
        "projected": (
            ((("Y", F(0)),), F(1, 2)),
            ((("Y", F(1)),), F(1, 2)),
        ),
        "estimands": (F(1), F(-1)),
        "manifest": (
            ("assignment_design", "balanced-half"),
            ("manifest_scope", "design-only"),
        ),
    },
    "A": {
        "estimand": "tau_CB",
        "p": (
            (
                (
                    ("A", TEST_A_COMPLETE),
                    ("E", TEST_E_IDENTITY),
                    ("Z", 0),
                    ("outcome_slots", TEST_SLOTS_0),
                ),
                F(1, 2),
            ),
            (
                (
                    ("A", TEST_A_COMPLETE),
                    ("E", TEST_E_IDENTITY),
                    ("Z", 1),
                    ("outcome_slots", TEST_SLOTS_1),
                ),
                F(1, 2),
            ),
        ),
        "q": (
            (
                (
                    ("A", TEST_A_PARTIAL),
                    ("E", TEST_E_IDENTITY),
                    ("Z", 0),
                    ("outcome_slots", TEST_SLOTS_0),
                ),
                F(1, 2),
            ),
            (
                (
                    ("A", TEST_A_PARTIAL),
                    ("E", TEST_E_IDENTITY),
                    ("Z", 1),
                    ("outcome_slots", TEST_SLOTS_1),
                ),
                F(1, 2),
            ),
        ),
        "projected": (
            (
                (
                    ("E", TEST_E_IDENTITY),
                    ("Z", 0),
                    ("outcome_slots", TEST_SLOTS_0),
                ),
                F(1, 2),
            ),
            (
                (
                    ("E", TEST_E_IDENTITY),
                    ("Z", 1),
                    ("outcome_slots", TEST_SLOTS_1),
                ),
                F(1, 2),
            ),
        ),
        "estimands": (F(1), F(0)),
        "manifest": (("manifest_scope", "retained-records-only"),),
    },
    "E": {
        "estimand": "tau_CB",
        "p": (
            (
                (
                    ("A", TEST_A_COMPLETE),
                    ("E", TEST_E_IDENTITY),
                    ("Z", 0),
                    ("outcome_slots", TEST_SLOTS_0),
                ),
                F(1, 2),
            ),
            (
                (
                    ("A", TEST_A_COMPLETE),
                    ("E", TEST_E_IDENTITY),
                    ("Z", 1),
                    ("outcome_slots", TEST_SLOTS_1),
                ),
                F(1, 2),
            ),
        ),
        "q": (
            (
                (
                    ("A", TEST_A_COMPLETE),
                    ("E", TEST_E_SWAPPED),
                    ("Z", 0),
                    ("outcome_slots", TEST_SLOTS_0),
                ),
                F(1, 2),
            ),
            (
                (
                    ("A", TEST_A_COMPLETE),
                    ("E", TEST_E_SWAPPED),
                    ("Z", 1),
                    ("outcome_slots", TEST_SLOTS_1),
                ),
                F(1, 2),
            ),
        ),
        "projected": (
            (
                (
                    ("A", TEST_A_COMPLETE),
                    ("Z", 0),
                    ("outcome_slots", TEST_SLOTS_0),
                ),
                F(1, 2),
            ),
            (
                (
                    ("A", TEST_A_COMPLETE),
                    ("Z", 1),
                    ("outcome_slots", TEST_SLOTS_1),
                ),
                F(1, 2),
            ),
        ),
        "estimands": (F(1), F(0)),
        "manifest": (("manifest_scope", "retained-records-only"),),
    },
    "B": {
        "estimand": "tau_ITT",
        "p": (
            (
                (
                    (
                        "B",
                        (
                            ("assignment-0", "outcome-0"),
                            ("assignment-1", "outcome-1"),
                        ),
                    ),
                    (
                        "assignment_objects",
                        (("assignment-0", 0), ("assignment-1", 1)),
                    ),
                    (
                        "outcome_objects",
                        (("outcome-0", F(0)), ("outcome-1", F(1))),
                    ),
                ),
                F(1),
            ),
        ),
        "q": (
            (
                (
                    (
                        "B",
                        (
                            ("assignment-0", "outcome-1"),
                            ("assignment-1", "outcome-0"),
                        ),
                    ),
                    (
                        "assignment_objects",
                        (("assignment-0", 0), ("assignment-1", 1)),
                    ),
                    (
                        "outcome_objects",
                        (("outcome-0", F(0)), ("outcome-1", F(1))),
                    ),
                ),
                F(1),
            ),
        ),
        "projected": (
            (
                (
                    (
                        "assignment_objects",
                        (("assignment-0", 0), ("assignment-1", 1)),
                    ),
                    (
                        "outcome_objects",
                        (("outcome-0", F(0)), ("outcome-1", F(1))),
                    ),
                ),
                F(1),
            ),
        ),
        "estimands": (F(1), F(-1)),
        "manifest": (("manifest_scope", "unjoined-object-multisets"),),
    },
    "T": {
        "estimand": "tau_ITT",
        "p": (
            ((("T", TEST_T_IDENTITY), ("Z", 0), ("terminal_token", "low")), F(1, 2)),
            ((("T", TEST_T_IDENTITY), ("Z", 1), ("terminal_token", "high")), F(1, 2)),
        ),
        "q": (
            ((("T", TEST_T_REVERSED), ("Z", 0), ("terminal_token", "low")), F(1, 2)),
            ((("T", TEST_T_REVERSED), ("Z", 1), ("terminal_token", "high")), F(1, 2)),
        ),
        "projected": (
            ((("Z", 0), ("terminal_token", "low")), F(1, 2)),
            ((("Z", 1), ("terminal_token", "high")), F(1, 2)),
        ),
        "estimands": (F(1), F(-1)),
        "manifest": (("manifest_scope", "scalar-without-owner-semantics"),),
    },
    "S": {
        "estimand": "tau_ITT",
        "p": (
            (
                (
                    ("S", TEST_S_A),
                    ("Z", 0),
                    ("key_scores", (("key-a", F(0)), ("key-b", F(1)))),
                ),
                F(1, 2),
            ),
            (
                (
                    ("S", TEST_S_A),
                    ("Z", 1),
                    ("key_scores", (("key-a", F(1)), ("key-b", F(0)))),
                ),
                F(1, 2),
            ),
        ),
        "q": (
            (
                (
                    ("S", TEST_S_B),
                    ("Z", 0),
                    ("key_scores", (("key-a", F(0)), ("key-b", F(1)))),
                ),
                F(1, 2),
            ),
            (
                (
                    ("S", TEST_S_B),
                    ("Z", 1),
                    ("key_scores", (("key-a", F(1)), ("key-b", F(0)))),
                ),
                F(1, 2),
            ),
        ),
        "projected": (
            ((("Z", 0), ("key_scores", (("key-a", F(0)), ("key-b", F(1))))), F(1, 2)),
            ((("Z", 1), ("key_scores", (("key-a", F(1)), ("key-b", F(0))))), F(1, 2)),
        ),
        "estimands": (F(1), F(-1)),
        "manifest": (("manifest_scope", "scalar-without-key-map"),),
    },
    "G": {
        "estimand": "tau_ITT",
        "p": (
            ((("G", TEST_G_IDENTITY), ("Z", 0), ("protocol_token", "fail")), F(1, 2)),
            ((("G", TEST_G_IDENTITY), ("Z", 1), ("protocol_token", "pass")), F(1, 2)),
        ),
        "q": (
            ((("G", TEST_G_REVERSED), ("Z", 0), ("protocol_token", "fail")), F(1, 2)),
            ((("G", TEST_G_REVERSED), ("Z", 1), ("protocol_token", "pass")), F(1, 2)),
        ),
        "projected": (
            ((("Z", 0), ("protocol_token", "fail")), F(1, 2)),
            ((("Z", 1), ("protocol_token", "pass")), F(1, 2)),
        ),
        "estimands": (F(1), F(-1)),
        "manifest": (("manifest_scope", "scalar-without-protocol-map"),),
    },
    "P": {
        "estimand": "Psi_N",
        "p": (
            (
                (
                    ("P", TEST_POLICY_A),
                    ("action", "a"),
                    ("context", "x0"),
                    ("potential_outcomes", TEST_POTENTIAL_0),
                ),
                F(1, 2),
            ),
            (
                (
                    ("P", TEST_POLICY_A),
                    ("action", "a"),
                    ("context", "x1"),
                    ("potential_outcomes", TEST_POTENTIAL_1),
                ),
                F(1, 2),
            ),
        ),
        "q": (
            (
                (
                    ("P", TEST_POLICY_B),
                    ("action", "a"),
                    ("context", "x0"),
                    ("potential_outcomes", TEST_POTENTIAL_0),
                ),
                F(1, 2),
            ),
            (
                (
                    ("P", TEST_POLICY_B),
                    ("action", "a"),
                    ("context", "x1"),
                    ("potential_outcomes", TEST_POTENTIAL_1),
                ),
                F(1, 2),
            ),
        ),
        "projected": (
            (
                (
                    ("action", "a"),
                    ("context", "x0"),
                    ("potential_outcomes", TEST_POTENTIAL_0),
                ),
                F(1, 2),
            ),
            (
                (
                    ("action", "a"),
                    ("context", "x1"),
                    ("potential_outcomes", TEST_POTENTIAL_1),
                ),
                F(1, 2),
            ),
        ),
        "estimands": (F(1, 2), F(1)),
        "manifest": (("manifest_scope", "actions-without-policy-provenance"),),
    },
}


def bound_row(
    arm: int,
    weight: Fraction | int,
    replacement: int,
    omitted: Fraction | int,
    residual: Fraction | int,
) -> BoundRow:
    return BoundRow(
        arm=arm,
        analysis_weight=weight,
        replacement=replacement,
        omitted_mass=omitted,
        residual_tv=residual,
    )


def independent_registered_estimand(witness, law) -> Fraction:
    arm_mass = {0: F(0), 1: F(0)}
    arm_total = {0: F(0), 1: F(0)}
    if witness.component == "B":
        for atom, mass in law:
            row = dict(atom)
            assignments = dict(row["assignment_objects"])
            outcomes = dict(row["outcome_objects"])
            for assignment_id, outcome_id in row["B"]:
                arm = assignments[assignment_id]
                arm_mass[arm] += mass
                arm_total[arm] += mass * outcomes[outcome_id]
        return arm_total[1] / arm_mass[1] - arm_total[0] / arm_mass[0]
    if witness.estimand == "Psi_N":
        value = F(0)
        for atom, mass in law:
            row = dict(atom)
            policy = dict(row["P"])
            action = dict(policy["decision_rule"])[row["context"]]
            value += mass * dict(row["potential_outcomes"])[action]
        return value
    for atom, mass in law:
        row = dict(atom)
        arm = row["Z"]
        if witness.estimand == "tau_CB":
            requested_bundle = dict(row["A"])["bundle"]
            execution = dict(row["E"])
            slot = dict(execution["regime_map"])[requested_bundle]
            outcome = dict(row["outcome_slots"])[slot]
        elif witness.component == "Z":
            outcome = row["Y"]
        elif witness.component == "T":
            outcome = dict(dict(row["T"])["value_map"])[row["terminal_token"]]
        elif witness.component == "S":
            scores = dict(row["key_scores"])
            outcome = sum(weight * scores[key] for key, weight in row["S"])
        elif witness.component == "G":
            outcome = dict(dict(row["G"])["truth_map"])[row["protocol_token"]]
        else:
            raise AssertionError(witness.component)
        arm_mass[arm] += mass
        arm_total[arm] += mass * outcome
    return arm_total[1] / arm_mass[1] - arm_total[0] / arm_mass[0]


def independent_invariance_image(component: str, physical_object):
    physical = dict(physical_object)
    if component == "B":
        return tuple(
            (
                ("analysis_weight", dict(row)["analysis_weight"]),
                ("outcome", dict(row)["outcome"]),
                ("stratum", dict(row)["stratum"]),
            )
            for row in physical["rows"]
        )
    if component == "S":
        scores = dict(physical["scores"])
        return tuple(
            (("key", key), ("score", scores[key]), ("weight", weight))
            for key, weight in physical["weights"]
            if weight > 0
        )
    if component == "G":
        truth = dict(physical["truth_map"])
        return tuple(
            (("mass", mass), ("terminal", terminal), ("value", truth[terminal]))
            for terminal, mass in physical["evaluation_mass"]
        )
    raise AssertionError(component)


def independent_invariance_estimand(component: str, image) -> Fraction:
    if component == "B":
        return sum(dict(row)["analysis_weight"] * dict(row)["outcome"] for row in image)
    if component == "S":
        return sum(dict(row)["weight"] * dict(row)["score"] for row in image)
    if component == "G":
        return sum(dict(row)["mass"] * dict(row)["value"] for row in image)
    raise AssertionError(component)


def bernoulli_mean(law: tuple[tuple[int, Fraction], ...]) -> Fraction:
    return sum(value * mass for value, mass in law)


def bernoulli_total_variation(
    law_p: tuple[tuple[int, Fraction], ...],
    law_q: tuple[tuple[int, Fraction], ...],
) -> Fraction:
    masses_p = dict(law_p)
    masses_q = dict(law_q)
    return F(1, 2) * sum(
        abs(masses_p.get(value, F(0)) - masses_q.get(value, F(0))) for value in (0, 1)
    )


class PairedWorldWitnessTests(unittest.TestCase):
    def test_every_omitted_component_has_literal_equal_projection_and_unequal_target(
        self,
    ) -> None:
        witnesses = paired_world_witnesses()

        self.assertEqual(
            tuple(witness.component for witness in witnesses),
            ("Z", "A", "E", "B", "T", "S", "G", "P"),
        )
        self.assertEqual(len(witnesses), 8)
        for witness in witnesses:
            with self.subTest(component=witness.component):
                self.assertIs(type(witness), PairedWorldWitness)
                expected = EXPECTED_WORLDS[witness.component]
                self.assertEqual(witness.estimand, expected["estimand"])
                self.assertEqual(witness.full_law_p, expected["p"])
                self.assertEqual(witness.full_law_q, expected["q"])
                self.assertEqual(witness.projected_law_p, expected["projected"])
                self.assertEqual(witness.projected_law_q, expected["projected"])
                self.assertEqual(
                    (witness.estimand_p, witness.estimand_q),
                    expected["estimands"],
                )
                self.assertEqual(
                    witness.authenticated_manifest,
                    expected["manifest"],
                )
                self.assertNotEqual(witness.estimand_p, witness.estimand_q)

    def test_projection_removes_only_the_named_component_and_preserves_mass(
        self,
    ) -> None:
        for witness in paired_world_witnesses():
            with self.subTest(component=witness.component):
                for full_law, projected_law in (
                    (witness.full_law_p, witness.projected_law_p),
                    (witness.full_law_q, witness.projected_law_q),
                ):
                    self.assertEqual(sum(mass for _, mass in full_law), F(1))
                    self.assertEqual(sum(mass for _, mass in projected_law), F(1))
                    literal_projection = {}
                    for atom, mass in full_law:
                        keys = tuple(key for key, _ in atom)
                        self.assertEqual(keys.count(witness.component), 1)
                        retained = tuple(
                            field for field in atom if field[0] != witness.component
                        )
                        literal_projection[retained] = (
                            literal_projection.get(retained, F(0)) + mass
                        )
                    self.assertEqual(
                        tuple(sorted(literal_projection.items())),
                        projected_law,
                    )

    def test_retained_records_and_manifest_cannot_recover_omitted_component(
        self,
    ) -> None:
        for witness in paired_world_witnesses():
            with self.subTest(component=witness.component):
                retained_to_omitted = {}
                for law in (witness.full_law_p, witness.full_law_q):
                    for atom, mass in law:
                        if mass == 0:
                            continue
                        retained = tuple(
                            field for field in atom if field[0] != witness.component
                        )
                        omitted = next(
                            value for key, value in atom if key == witness.component
                        )
                        retained_to_omitted.setdefault(retained, set()).add(omitted)
                self.assertTrue(
                    any(len(values) > 1 for values in retained_to_omitted.values())
                )
                self.assertNotIn(
                    witness.component,
                    tuple(key for key, _ in witness.authenticated_manifest),
                )
                self.assertIs(witness.recoverable_from_retained, False)

    def test_witnesses_are_frozen_and_reject_false_nonidentification_claims(
        self,
    ) -> None:
        witness = paired_world_witnesses()[0]
        with self.assertRaises(FrozenInstanceError):
            witness.estimand_p = F(0)  # type: ignore[misc]
        with self.assertRaises(TypeError):
            replace(witness, estimand_q=witness.estimand_p)
        with self.assertRaises(ValueError):
            replace(
                witness,
                authenticated_manifest=((witness.component, "recovering-value"),),
            )

    def test_physical_changes_can_preserve_the_estimand_under_exact_certificates(
        self,
    ) -> None:
        certificates = invariance_certificates()

        self.assertEqual(
            tuple(certificate.component for certificate in certificates),
            ("B", "S", "G"),
        )
        b_row_0 = (
            ("analysis_weight", F(1, 2)),
            ("outcome", F(0)),
            ("stratum", "s0"),
            ("target_id", "target-0"),
            ("unit_id", "u0"),
        )
        b_row_1 = (
            ("analysis_weight", F(1, 2)),
            ("outcome", F(1)),
            ("stratum", "s0"),
            ("target_id", "target-1"),
            ("unit_id", "u1"),
        )
        expected = (
            (
                (("rows", (b_row_0, b_row_1)),),
                (
                    (
                        "rows",
                        (
                            (
                                *b_row_0[:3],
                                ("target_id", "target-1"),
                                b_row_0[4],
                            ),
                            (
                                *b_row_1[:3],
                                ("target_id", "target-0"),
                                b_row_1[4],
                            ),
                        ),
                    ),
                ),
                F(1, 2),
            ),
            (
                (
                    (
                        "scores",
                        (("key-a", F(3, 4)), ("unused", F(1, 4))),
                    ),
                    (
                        "weights",
                        (("key-a", F(1)), ("unused", F(0))),
                    ),
                ),
                (
                    ("scores", (("key-a", F(3, 4)),)),
                    ("weights", (("key-a", F(1)),)),
                ),
                F(3, 4),
            ),
            (
                (
                    (
                        "evaluation_mass",
                        (("terminal-0", F(3, 4)), ("terminal-1", F(1, 4))),
                    ),
                    ("protocol_id", "protocol-v1"),
                    (
                        "truth_map",
                        (("terminal-0", F(0)), ("terminal-1", F(1))),
                    ),
                ),
                (
                    (
                        "evaluation_mass",
                        (("terminal-0", F(3, 4)), ("terminal-1", F(1, 4))),
                    ),
                    ("protocol_id", "protocol-v2-compatible"),
                    (
                        "truth_map",
                        (("terminal-0", F(0)), ("terminal-1", F(1))),
                    ),
                ),
                F(1, 4),
            ),
        )
        for certificate, literal in zip(certificates, expected, strict=True):
            with self.subTest(component=certificate.component):
                physical_p, physical_q, estimand = literal
                self.assertEqual(certificate.physical_object_p, physical_p)
                self.assertEqual(certificate.physical_object_q, physical_q)
                self.assertNotEqual(physical_p, physical_q)
                functional_image = independent_invariance_image(
                    certificate.component, physical_p
                )
                self.assertEqual(certificate.functional_image_p, functional_image)
                self.assertEqual(
                    certificate.functional_image_q,
                    independent_invariance_image(certificate.component, physical_q),
                )
                self.assertEqual(certificate.estimand_p, estimand)
                self.assertEqual(certificate.estimand_q, estimand)
                self.assertIs(certificate.preserves_estimand, True)


class ContrastErrorBoundTests(unittest.TestCase):
    def test_disjoint_nested_and_fully_overlapping_faults_are_not_double_counted(
        self,
    ) -> None:
        disjoint = (
            bound_row(1, F(1, 2), 1, 0, 0),
            bound_row(1, F(1, 2), 0, F(1, 4), F(1, 4)),
            bound_row(0, 1, 0, 0, 0),
        )
        nested = (
            bound_row(1, 1, 1, F(3, 4), F(1, 4)),
            bound_row(0, 1, 0, 0, 0),
        )
        full_overlap = (
            bound_row(1, 1, 1, 1, 1),
            bound_row(0, 1, 0, 0, 0),
        )

        self.assertEqual(contrast_error_bound_exact(disjoint), F(3, 4))
        self.assertEqual(contrast_error_bound_exact(nested), F(1))
        self.assertEqual(contrast_error_bound_exact(full_overlap), F(1))

    def test_finite_examples_attain_equality_and_a_near_cap_value(self) -> None:
        equality_rows = (
            bound_row(1, 1, 1, 0, 0),
            bound_row(0, 1, 0, 0, 0),
        )
        true_contrast = F(1) - F(0)
        measured_contrast = F(0) - F(0)
        self.assertEqual(
            abs(measured_contrast - true_contrast),
            contrast_error_bound_exact(equality_rows),
        )

        true_one = ((1, F(1)),)
        measured_one = ((0, F(99, 100)), (1, F(1, 100)))
        true_zero = ((0, F(1)),)
        measured_zero = ((0, F(1, 100)), (1, F(99, 100)))
        near_cap_rows = (
            bound_row(
                1,
                1,
                0,
                0,
                bernoulli_total_variation(true_one, measured_one),
            ),
            bound_row(
                0,
                1,
                0,
                0,
                bernoulli_total_variation(true_zero, measured_zero),
            ),
        )
        true_contrast = bernoulli_mean(true_one) - bernoulli_mean(true_zero)
        measured_contrast = bernoulli_mean(measured_one) - bernoulli_mean(measured_zero)
        self.assertEqual(contrast_error_bound_exact(near_cap_rows), F(99, 50))
        self.assertEqual(
            abs(measured_contrast - true_contrast),
            F(99, 50),
        )

    def test_two_arm_bound_is_capped_at_two_and_float_conversion_is_at_boundary(
        self,
    ) -> None:
        true_one = ((1, F(1)),)
        measured_one = ((0, F(1)),)
        true_zero = ((0, F(1)),)
        measured_zero = ((1, F(1)),)
        rows = (
            bound_row(
                1,
                1,
                0,
                0,
                bernoulli_total_variation(true_one, measured_one),
            ),
            bound_row(
                0,
                1,
                0,
                0,
                bernoulli_total_variation(true_zero, measured_zero),
            ),
        )
        true_contrast = bernoulli_mean(true_one) - bernoulli_mean(true_zero)
        measured_contrast = bernoulli_mean(measured_one) - bernoulli_mean(measured_zero)

        self.assertEqual(abs(measured_contrast - true_contrast), F(2))
        self.assertEqual(contrast_error_bound_exact(rows), F(2))
        self.assertEqual(contrast_error_bound(rows), 2.0)
        self.assertIs(type(contrast_error_bound(rows)), float)

    def test_bound_row_normalizes_exact_numeric_fields(self) -> None:
        row = bound_row(0, 1, 0, F(1, 3), F(1, 6))

        self.assertEqual(row.analysis_weight, F(1))
        self.assertEqual(row.omitted_mass, F(1, 3))
        self.assertEqual(row.residual_tv, F(1, 6))
        self.assertIs(type(row.analysis_weight), Fraction)
        self.assertIs(type(row.omitted_mass), Fraction)
        self.assertIs(type(row.residual_tv), Fraction)

    def test_bound_row_rejects_every_registered_out_of_domain_condition(self) -> None:
        valid = bound_row(0, 1, 0, 0, 0)
        invalid = (
            lambda: replace(valid, arm=-1),
            lambda: replace(valid, arm=2),
            lambda: replace(valid, arm=True),
            lambda: replace(valid, arm=1.0),
            lambda: replace(valid, analysis_weight=F(-1, 2)),
            lambda: replace(valid, analysis_weight=F(3, 2)),
            lambda: replace(valid, analysis_weight=True),
            lambda: replace(valid, analysis_weight=0.5),
            lambda: replace(valid, analysis_weight=math.nan),
            lambda: replace(valid, analysis_weight=math.inf),
            lambda: replace(valid, replacement=-1),
            lambda: replace(valid, replacement=2),
            lambda: replace(valid, replacement=True),
            lambda: replace(valid, replacement=F(1)),
            lambda: replace(valid, omitted_mass=F(-1, 10)),
            lambda: replace(valid, omitted_mass=F(11, 10)),
            lambda: replace(valid, omitted_mass=True),
            lambda: replace(valid, omitted_mass=math.nan),
            lambda: replace(valid, residual_tv=F(-1, 10)),
            lambda: replace(valid, residual_tv=F(11, 10)),
            lambda: replace(valid, residual_tv=True),
            lambda: replace(valid, residual_tv=math.inf),
            lambda: replace(valid, unit_deleted=True),
            lambda: replace(valid, denominator_changed=True),
            lambda: replace(valid, cross_arm_movement=True),
            lambda: replace(valid, unit_deleted=0),
            lambda: replace(valid, denominator_changed=0),
            lambda: replace(valid, cross_arm_movement=0),
            lambda: replace(valid, score_lower=F(-1, 10)),
            lambda: replace(valid, score_upper=F(11, 10)),
            lambda: replace(valid, score_lower=F(3, 4), score_upper=F(1, 4)),
            lambda: replace(valid, score_lower=True),
            lambda: replace(valid, score_upper=math.inf),
        )

        for index, constructor in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(ValueError):
                constructor()

    def test_bound_requires_both_arms_and_exact_per_arm_normalization(self) -> None:
        cases = (
            (),
            (bound_row(0, 1, 0, 0, 0),),
            (
                bound_row(0, F(1, 2), 0, 0, 0),
                bound_row(1, 1, 0, 0, 0),
            ),
            (
                bound_row(0, F(3, 4), 0, 0, 0),
                bound_row(0, F(1, 2), 0, 0, 0),
                bound_row(1, 1, 0, 0, 0),
            ),
            (bound_row(0, 1, 0, 0, 0), object()),
        )

        for index, rows in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                contrast_error_bound_exact(rows)  # type: ignore[arg-type]


class TerminalMeasurementTests(unittest.TestCase):
    def test_common_nondifferential_rates_scale_the_true_contrast(self) -> None:
        exact = terminal_measured_contrast_exact(
            F(1, 4), F(3, 4), F(4, 5), F(9, 10), F(4, 5), F(9, 10)
        )

        self.assertEqual(exact, F(7, 20))
        self.assertEqual(exact, (F(4, 5) + F(9, 10) - 1) * F(1, 2))
        self.assertEqual(
            terminal_measured_contrast(
                F(1, 4), F(3, 4), F(4, 5), F(9, 10), F(4, 5), F(9, 10)
            ),
            0.35,
        )

    def test_arm_specific_equation_matches_hand_derived_fraction(self) -> None:
        measured = terminal_measured_contrast_exact(
            F(1, 4), F(3, 4), F(3, 4), F(4, 5), F(9, 10), F(7, 10)
        )

        self.assertEqual(measured, F(33, 80))

    def test_fixed_true_point_two_contrast_reverses_to_negative_point_one(self) -> None:
        mu0 = F(2, 5)
        mu1 = F(3, 5)

        self.assertEqual(mu1 - mu0, F(1, 5))
        self.assertEqual(
            terminal_measured_contrast_exact(mu0, mu1, 1, 1, F(1, 2), 1),
            F(-1, 10),
        )
        self.assertEqual(
            terminal_measured_contrast(0.4, 0.6, 1.0, 1.0, 0.5, 1.0),
            -0.1,
        )

    def test_terminal_formula_rejects_bool_nonfinite_and_out_of_unit_interval(
        self,
    ) -> None:
        valid = [F(2, 5), F(3, 5), F(1), F(1), F(1, 2), F(1)]
        invalid_values = (True, -0.01, 1.01, math.nan, math.inf, -math.inf, "0.5")

        for position in range(6):
            for invalid in invalid_values:
                values = valid.copy()
                values[position] = invalid  # type: ignore[list-item]
                with self.subTest(position=position, invalid=invalid):
                    with self.assertRaises(ValueError):
                        terminal_measured_contrast(*values)


class SelectionBoundaryTests(unittest.TestCase):
    def test_full_sample_mcar_mar_mnar_and_compliance_statuses_are_distinct(
        self,
    ) -> None:
        expected = {
            "full_sample": "FULL_SAMPLE_RANDOMIZED_ESTIMAND",
            "mcar": "IDENTIFIED_WITHOUT_RECEIPT_CONDITIONING",
            "mar+positivity": "IDENTIFIED_BY_STANDARDIZATION_OR_IPW",
            "mnar": "BOUNDS_OR_SENSITIVITY_ONLY",
            "post-treatment_compliance": (
                "KEEP_RANDOMIZED_ESTIMAND_DO_NOT_CONDITION_ON_POST_TREATMENT_COMPLIANCE"
            ),
        }

        actual = {
            mechanism: selection_estimand_status(mechanism) for mechanism in expected
        }
        self.assertEqual(actual, expected)
        self.assertEqual(len(set(actual.values())), 5)

    def test_selection_status_rejects_unregistered_or_ambiguous_mechanisms(
        self,
    ) -> None:
        for mechanism in ("mar", "MAR+positivity", "", "compliance", None, True):
            with self.subTest(mechanism=mechanism), self.assertRaises(ValueError):
                selection_estimand_status(mechanism)  # type: ignore[arg-type]


class ReviewFixRoundOneTests(unittest.TestCase):
    def test_paired_world_targets_are_derived_from_physical_laws(self) -> None:
        self.assertEqual(
            tuple(field.name for field in fields(PairedWorldWitness)),
            (
                "component",
                "estimand",
                "full_law_p",
                "full_law_q",
                "authenticated_manifest",
            ),
        )
        for witness in paired_world_witnesses():
            with self.subTest(component=witness.component):
                self.assertEqual(
                    witness.estimand_p,
                    independent_registered_estimand(witness, witness.full_law_p),
                )
                self.assertEqual(
                    witness.estimand_q,
                    independent_registered_estimand(witness, witness.full_law_q),
                )
        with self.assertRaises(TypeError):
            replace(paired_world_witnesses()[0], estimand_p=F(17))

    def test_invariance_images_and_estimands_are_derived_from_physical_objects(
        self,
    ) -> None:
        certificates = invariance_certificates()
        self.assertEqual(
            tuple(field.name for field in fields(type(certificates[0]))),
            ("component", "physical_object_p", "physical_object_q"),
        )
        for certificate in certificates:
            with self.subTest(component=certificate.component):
                image_p = independent_invariance_image(
                    certificate.component, certificate.physical_object_p
                )
                image_q = independent_invariance_image(
                    certificate.component, certificate.physical_object_q
                )
                self.assertEqual(certificate.functional_image_p, image_p)
                self.assertEqual(certificate.functional_image_q, image_q)
                self.assertEqual(
                    certificate.estimand_p,
                    independent_invariance_estimand(certificate.component, image_p),
                )
                self.assertEqual(
                    certificate.estimand_q,
                    independent_invariance_estimand(certificate.component, image_q),
                )
        with self.assertRaises(TypeError):
            replace(certificates[0], functional_image_p=())
        with self.assertRaises(ValueError):
            type(certificates[0])(
                component="B",
                physical_object_p=(),
                physical_object_q=(),
            )

    def test_near_cap_bound_is_attained_by_explicit_bernoulli_tv_laws(self) -> None:
        true_arm_one = ((1, F(1)),)
        measured_arm_one = ((0, F(99, 100)), (1, F(1, 100)))
        true_arm_zero = ((0, F(1)),)
        measured_arm_zero = ((0, F(1, 100)), (1, F(99, 100)))
        tv_one = bernoulli_total_variation(true_arm_one, measured_arm_one)
        tv_zero = bernoulli_total_variation(true_arm_zero, measured_arm_zero)
        rows = (
            bound_row(1, 1, 0, 0, tv_one),
            bound_row(0, 1, 0, 0, tv_zero),
        )
        true_contrast = bernoulli_mean(true_arm_one) - bernoulli_mean(true_arm_zero)
        measured_contrast = bernoulli_mean(measured_arm_one) - bernoulli_mean(
            measured_arm_zero
        )

        self.assertEqual((tv_one, tv_zero), (F(99, 100), F(99, 100)))
        self.assertEqual(true_contrast, F(1))
        self.assertEqual(measured_contrast, F(-49, 50))
        self.assertEqual(abs(measured_contrast - true_contrast), F(99, 50))
        self.assertEqual(contrast_error_bound_exact(rows), F(99, 50))

    def test_disjoint_nested_and_full_overlap_are_verified_as_fault_sets(self) -> None:
        disjoint_replacements = frozenset(("u0",))
        disjoint_key_faults = frozenset(("u1",))
        nested_replacements = frozenset(("u0", "u1"))
        nested_key_faults = frozenset(("u0",))
        full_replacements = frozenset(("u0", "u1"))
        full_key_faults = frozenset(("u0", "u1"))

        self.assertTrue(disjoint_replacements.isdisjoint(disjoint_key_faults))
        self.assertLess(nested_key_faults, nested_replacements)
        self.assertEqual(full_key_faults, full_replacements)
        disjoint_rows = (
            bound_row(1, F(1, 2), 1, 0, 0),
            bound_row(1, F(1, 2), 0, F(1, 4), F(1, 4)),
            bound_row(0, 1, 0, 0, 0),
        )
        nested_rows = (
            bound_row(1, F(1, 2), 1, 1, 0),
            bound_row(1, F(1, 2), 1, 0, 0),
            bound_row(0, 1, 0, 0, 0),
        )
        full_rows = (
            bound_row(1, F(1, 2), 1, 1, 0),
            bound_row(1, F(1, 2), 1, 1, 0),
            bound_row(0, 1, 0, 0, 0),
        )

        self.assertEqual(contrast_error_bound_exact(disjoint_rows), F(3, 4))
        self.assertEqual(contrast_error_bound_exact(nested_rows), F(1))
        self.assertEqual(contrast_error_bound_exact(full_rows), F(1))

    def test_compliance_keeps_itt_and_cace_late_is_a_distinct_optional_target(
        self,
    ) -> None:
        compliance_types = (
            (("never-taker", F(1, 2)), 0, 0),
            (("complier", F(1, 2)), 0, 1),
        )
        randomized_itt = sum(
            label_and_mass[1] * (outcome_z1 - outcome_z0)
            for label_and_mass, outcome_z0, outcome_z1 in compliance_types
        )
        complier_late = F(1)

        self.assertEqual(randomized_itt, F(1, 2))
        self.assertEqual(complier_late, F(1))
        self.assertNotEqual(randomized_itt, complier_late)
        self.assertEqual(
            selection_estimand_status("post-treatment_compliance"),
            ("KEEP_RANDOMIZED_ESTIMAND_DO_NOT_CONDITION_ON_POST_TREATMENT_COMPLIANCE"),
        )


if __name__ == "__main__":
    unittest.main()
