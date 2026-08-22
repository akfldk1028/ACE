from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import importlib
import math
import unittest


def _module():
    try:
        return importlib.import_module("iclr2027.obligation_contract")
    except ModuleNotFoundError as error:
        raise AssertionError("obligation contract is not implemented") from error


def _belief_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "obligation_id": "law.use",
        "status": "unresolved",
        "unresolved_probability": 0.25,
        "evidence_ids": ["evidence:law"],
    }
    payload.update(overrides)
    return payload


def _state_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "case_id": "case:1",
        "prefix_id": "prefix:2",
        "beliefs": [_belief_payload()],
        "hard_gate_passed": True,
        "cumulative_cost": 12.5,
    }
    payload.update(overrides)
    return payload


class ObligationContractTests(unittest.TestCase):
    def test_spec_is_frozen_and_round_trips_exact_public_basis(self) -> None:
        contract = _module()
        payload = {
            "obligation_id": "parking.supply",
            "family": "parking",
            "weight": 2.5,
            "hard": True,
            "public_basis_ids": ["public:parking-code", "public:site-plan"],
        }
        spec = contract.ObligationSpec.from_dict(payload)
        self.assertEqual(spec.to_dict(), payload)
        self.assertEqual(
            spec.public_basis_ids,
            ("public:parking-code", "public:site-plan"),
        )
        with self.assertRaises(FrozenInstanceError):
            spec.weight = 3.0

    def test_all_and_only_declared_obligation_families_are_accepted(self) -> None:
        contract = _module()
        accepted = {"law", "parking", "program", "geometry", "site/evidence"}
        self.assertEqual(contract.OBLIGATION_FAMILIES, frozenset(accepted))
        observed: set[str] = set()
        for family in accepted:
            with self.subTest(family=family):
                spec = contract.ObligationSpec(
                    obligation_id=f"{family}.required",
                    family=family,
                    weight=1.0,
                    hard=False,
                    public_basis_ids=(f"public:{family}",),
                )
                observed.add(spec.family)
        self.assertEqual(observed, accepted)
        with self.assertRaises(ValueError):
            contract.ObligationSpec(
                obligation_id="finance.required",
                family="finance",
                weight=1.0,
                hard=False,
                public_basis_ids=("public:finance",),
            )

    def test_belief_status_probability_and_evidence_are_exact(self) -> None:
        contract = _module()
        self.assertEqual(
            contract.OBLIGATION_STATUSES,
            frozenset({"resolved", "unresolved", "unknown"}),
        )
        for status, probability in (
            ("resolved", 0.0),
            ("unresolved", 1.0),
            ("unknown", 0.5),
        ):
            with self.subTest(status=status):
                belief = contract.ObligationBelief.from_dict(
                    _belief_payload(
                        status=status,
                        unresolved_probability=probability,
                    )
                )
                self.assertEqual(
                    contract.ObligationBelief.from_dict(belief.to_dict()), belief
                )
                self.assertIsInstance(belief.evidence_ids, tuple)
        with self.assertRaises(ValueError):
            contract.ObligationBelief.from_dict(_belief_payload(status="pending"))
        with self.assertRaises(ValueError):
            contract.ObligationBelief.from_dict(
                _belief_payload(evidence_ids=["evidence:law", "evidence:law"])
            )

    def test_state_rejects_duplicate_obligation_ids_and_is_deeply_immutable(self) -> None:
        contract = _module()
        duplicate = _belief_payload()
        with self.assertRaises(ValueError):
            contract.ObligationState.from_dict(
                _state_payload(beliefs=[_belief_payload(), duplicate])
            )

        state = contract.ObligationState.from_dict(_state_payload())
        self.assertIsInstance(state.beliefs, tuple)
        with self.assertRaises(FrozenInstanceError):
            state.cumulative_cost = 0.0
        with self.assertRaises(AttributeError):
            state.beliefs.append(state.beliefs[0])

    def test_numeric_fields_reject_nonfinite_and_out_of_contract_values(self) -> None:
        contract = _module()
        for invalid in (math.nan, math.inf, -math.inf, -0.1, True):
            with self.subTest(field="weight", invalid=invalid), self.assertRaises(
                (TypeError, ValueError)
            ):
                contract.ObligationSpec(
                    obligation_id="law.use",
                    family="law",
                    weight=invalid,
                    hard=True,
                    public_basis_ids=("public:law",),
                )
        for invalid in (math.nan, math.inf, -math.inf, -0.01, 1.01, True):
            with self.subTest(
                field="unresolved_probability", invalid=invalid
            ), self.assertRaises((TypeError, ValueError)):
                contract.ObligationBelief.from_dict(
                    _belief_payload(unresolved_probability=invalid)
                )
        for invalid in (math.nan, math.inf, -math.inf, -0.01, True):
            with self.subTest(
                field="cumulative_cost", invalid=invalid
            ), self.assertRaises((TypeError, ValueError)):
                contract.ObligationState.from_dict(
                    _state_payload(cumulative_cost=invalid)
                )

    def test_exact_keys_text_booleans_and_public_basis_fail_closed(self) -> None:
        contract = _module()
        with self.assertRaises(ValueError):
            contract.ObligationSpec.from_dict(
                {
                    "obligation_id": "law.use",
                    "family": "law",
                    "weight": 1.0,
                    "hard": True,
                    "public_basis_ids": [],
                }
            )
        with self.assertRaises(ValueError):
            contract.ObligationState.from_dict(
                {**_state_payload(), "unexpected": "value"}
            )
        with self.assertRaises((TypeError, ValueError)):
            contract.ObligationState.from_dict(
                _state_payload(hard_gate_passed=1)
            )
        with self.assertRaises((TypeError, ValueError)):
            contract.ObligationBelief.from_dict(
                _belief_payload(obligation_id="  ")
            )

    def test_coordination_action_has_the_exact_closed_vocabulary(self) -> None:
        contract = _module()
        expected = {
            "STOP",
            "SOLO_SYNTHESIS",
            "ASK_LAW",
            "ASK_PARKING",
            "ASK_PROGRAM",
            "ASK_GEOMETRY",
        }
        self.assertEqual({action.value for action in contract.CoordinationAction}, expected)
        for value in expected:
            self.assertEqual(contract.CoordinationAction(value).value, value)
        with self.assertRaises(ValueError):
            contract.CoordinationAction("ASK_GENERALIST")

    def test_canonical_json_and_sha256_are_stable_and_hand_derived(self) -> None:
        contract = _module()
        state = contract.ObligationState.from_dict(_state_payload())
        expected_json = (
            '{"beliefs":[{"evidence_ids":["evidence:law"],'
            '"obligation_id":"law.use","status":"unresolved",'
            '"unresolved_probability":0.25}],"case_id":"case:1",'
            '"cumulative_cost":12.5,"hard_gate_passed":true,'
            '"prefix_id":"prefix:2"}'
        )
        expected_sha256 = hashlib.sha256(expected_json.encode("utf-8")).hexdigest()
        self.assertEqual(state.canonical_json(), expected_json)
        self.assertEqual(state.sha256(), expected_sha256)
        self.assertEqual(
            contract.ObligationState.from_dict(state.to_dict()).sha256(),
            expected_sha256,
        )

    def test_signed_zero_has_one_canonical_dict_json_and_hash(self) -> None:
        contract = _module()
        pairs = (
            (
                "weight",
                contract.ObligationSpec(
                    "o", "law", 0.0, False, ("public:x",)
                ),
                contract.ObligationSpec(
                    "o", "law", -0.0, False, ("public:x",)
                ),
            ),
            (
                "unresolved_probability",
                contract.ObligationBelief("o", "unknown", 0.0, ()),
                contract.ObligationBelief("o", "unknown", -0.0, ()),
            ),
            (
                "cumulative_cost",
                contract.ObligationState("c", "p", (), True, 0.0),
                contract.ObligationState("c", "p", (), True, -0.0),
            ),
        )
        observed: dict[str, dict[str, bool]] = {}
        for field, positive, negative in pairs:
            positive_dict = positive.to_dict()
            negative_dict = negative.to_dict()
            observed[field] = {
                "objects_equal": positive == negative,
                "dictionaries_equal": positive_dict == negative_dict,
                "dictionary_zero_is_positive": (
                    math.copysign(1.0, float(negative_dict[field])) == 1.0
                ),
                "canonical_json_equal": (
                    positive.canonical_json() == negative.canonical_json()
                ),
                "sha256_equal": positive.sha256() == negative.sha256(),
            }
        all_equal = {
            "objects_equal": True,
            "dictionaries_equal": True,
            "dictionary_zero_is_positive": True,
            "canonical_json_equal": True,
            "sha256_equal": True,
        }
        self.assertEqual(
            observed,
            {
                "weight": all_equal,
                "unresolved_probability": all_equal,
                "cumulative_cost": all_equal,
            },
        )

    def test_forbidden_controller_keys_are_rejected_at_any_depth(self) -> None:
        contract = _module()
        for forbidden in (
            "mutation_family",
            "gold",
            "expected_decision",
            "blocking_issue_codes_gold",
        ):
            with self.subTest(forbidden=forbidden):
                payload = _state_payload()
                payload["beliefs"][0]["evidence_ids"] = [
                    "evidence:law",
                    {"nested": [{forbidden: "secret"}]},
                ]
                with self.assertRaisesRegex(ValueError, "forbidden controller key"):
                    contract.ObligationState.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
