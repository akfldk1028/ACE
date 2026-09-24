from __future__ import annotations

import copy
import hashlib
import json
import math
import unittest
from dataclasses import replace

from iclr2027.estimand_receipts import (
    BoundCertificateV1,
    GateDecisionV1,
    ObservedArtifactV1,
    ObservedReceiptV1,
    PolicyRecordV1,
    ScoreWeightV1,
    TrustRootV1,
    UnitCommitmentV1,
    evaluate_reportability,
)


def _sha256_json(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _policy_dict(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "policy-record/v1",
        "policy_id": "policy-a",
        "action_menu": ["act-a", "act-b"],
        "information_snapshot_sha256": "4" * 64,
        "chosen_action": "act-a",
        "propensity": 0.5,
        "budget_limit": 10,
        "realized_cost": 3.5,
        "retry_limit": 2,
        "decision_event_sha256": "5" * 64,
    }
    value.update(changes)
    return value


def _weights_dict(first: float = 0.75, second: float = 0.25) -> list[dict[str, object]]:
    return [
        {"schema_version": "score-weight/v1", "key": "quality", "weight": first},
        {"schema_version": "score-weight/v1", "key": "safety", "weight": second},
    ]


def _certificate_dict(
    certificate_id: str,
    estimand: str,
    binding: str,
    observed_binding_sha256: str,
    lower: float,
    upper: float,
) -> dict[str, object]:
    return {
        "schema_version": "bound-certificate/v1",
        "certificate_id": certificate_id,
        "estimand": estimand,
        "binding": binding,
        "observed_binding_sha256": observed_binding_sha256,
        "lower": lower,
        "upper": upper,
    }


ALT_WEIGHTS = _weights_dict(0.5, 0.5)
ALT_SCORER_SHA256 = "42c1a30878e3a783b1b7b1b5ad4002950e509b5ec6b6cac48b7d74fbcfe4f91a"


def _commitment_dict(
    *,
    unit_id: str = "unit-a",
    certificates: list[dict[str, object]] | None = None,
    **changes: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "unit-commitment/v1",
        "unit_id": unit_id,
        "site_id": "site-a",
        "stratum_id": "stratum-a",
        "assignment": 1,
        "requested_action_id": "act-a",
        "requested_members": ["member-a", "member-b"],
        "target_binding_sha256": "1" * 64,
        "terminal_owner_id": "owner-a",
        "terminal_value_sha256": "2" * 64,
        "scorer_weights": _weights_dict(),
        "protocol_version": "proto-v1",
        "policy_record": _policy_dict(),
        "allowed_target_binding_sha256": ["3" * 64],
        "allowed_scorer_binding_sha256": [ALT_SCORER_SHA256],
        "allowed_protocol_versions": ["proto-v2"],
        "bound_certificates": certificates or [],
    }
    value.update(changes)
    return value


def _artifact_dict(
    *,
    unit_id: str = "unit-a",
    certificate_ids: list[str] | None = None,
    **changes: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "observed-artifact/v1",
        "study_id": "study-a",
        "unit_id": unit_id,
        "site_id": "site-a",
        "stratum_id": "stratum-a",
        "assignment": 1,
        "requested_action_id": "act-a",
        "requested_members": ["member-a", "member-b"],
        "executed_action_id": "act-a",
        "executed_members": ["member-a", "member-b"],
        "target_binding_sha256": "1" * 64,
        "terminal_owner_id": "owner-a",
        "terminal_value_sha256": "2" * 64,
        "scorer_weights": _weights_dict(),
        "protocol_version": "proto-v1",
        "policy_record": _policy_dict(),
        "bound_certificate_ids": certificate_ids or [],
    }
    value.update(changes)
    value["payload_sha256"] = _sha256_json(value)
    return value


def _contracts(
    *,
    commitments: list[dict[str, object]] | None = None,
    artifacts: list[dict[str, object]] | None = None,
    root_study: str = "study-a",
    receipt_study: str = "study-a",
) -> tuple[TrustRootV1, ObservedReceiptV1]:
    commitment_values = commitments or [_commitment_dict()]
    root_dict: dict[str, object] = {
        "schema_version": "trust-root/v1",
        "study_id": root_study,
        "commitments": commitment_values,
        "commitments_sha256": _sha256_json(commitment_values),
    }
    artifact_values = artifacts or [_artifact_dict()]
    receipt_dict: dict[str, object] = {
        "schema_version": "observed-receipt/v1",
        "study_id": receipt_study,
        "trust_root_sha256": _sha256_json(root_dict),
        "artifacts": artifact_values,
    }
    receipt_dict["payload_sha256"] = _sha256_json(receipt_dict)
    return TrustRootV1.from_dict(root_dict), ObservedReceiptV1.from_dict(receipt_dict)


def _decision_map(receipt: ObservedReceiptV1, root: TrustRootV1):
    return {row.estimand: row for row in evaluate_reportability(receipt, root)}


def _statuses(receipt: ObservedReceiptV1, root: TrustRootV1) -> tuple[str, ...]:
    return tuple(row.status for row in evaluate_reportability(receipt, root))


class ClosedSchemaTests(unittest.TestCase):
    def test_exact_round_trip_and_independent_literal_digests(self) -> None:
        root, receipt = _contracts()

        self.assertEqual(
            root.commitments_sha256,
            "dda4d08f9b61f8d760a40764c168bbb37e94ac1caaed0101ecfd88003613cc81",
        )
        self.assertEqual(
            receipt.trust_root_sha256,
            "fc4fd0a164a9eb9d94e0df8be0856b5880a736aae250b77c19890203f1f08412",
        )
        self.assertEqual(
            receipt.artifacts[0].payload_sha256,
            "c212992af042238225ee44668d96e4f86192f22cb44f7dca703fa1ec6571cd9a",
        )
        self.assertEqual(
            receipt.payload_sha256,
            "d891b1351dfd095d0129566ee3e183d5ab169550e497cff3e1f61963e260ee09",
        )
        expected_policy = _policy_dict()
        expected_commitment = _commitment_dict()
        expected_artifact = _artifact_dict()
        expected_root = {
            "schema_version": "trust-root/v1",
            "study_id": "study-a",
            "commitments": [expected_commitment],
            "commitments_sha256": (
                "dda4d08f9b61f8d760a40764c168bbb37e94ac1caaed0101ecfd88003613cc81"
            ),
        }
        expected_receipt = {
            "schema_version": "observed-receipt/v1",
            "study_id": "study-a",
            "trust_root_sha256": (
                "fc4fd0a164a9eb9d94e0df8be0856b5880a736aae250b77c19890203f1f08412"
            ),
            "artifacts": [expected_artifact],
            "payload_sha256": (
                "d891b1351dfd095d0129566ee3e183d5ab169550e497cff3e1f61963e260ee09"
            ),
        }

        self.assertEqual(root.to_dict(), expected_root)
        self.assertEqual(receipt.to_dict(), expected_receipt)
        self.assertEqual(root.commitments[0].policy_record.to_dict(), expected_policy)
        self.assertIsInstance(root.commitments, tuple)
        self.assertIsInstance(receipt.artifacts, tuple)
        self.assertIsInstance(root.commitments[0].scorer_weights, tuple)
        self.assertEqual(TrustRootV1.from_dict(expected_root), root)
        self.assertEqual(ObservedReceiptV1.from_dict(expected_receipt), receipt)

    def test_every_from_dict_is_exact_key_closed(self) -> None:
        root, receipt = _contracts()
        values_and_types = (
            (_weights_dict()[0], ScoreWeightV1),
            (_policy_dict(), PolicyRecordV1),
            (
                _certificate_dict("cert-a", "tau_itt", "B", "6" * 64, -0.2, 0.3),
                BoundCertificateV1,
            ),
            (_commitment_dict(), UnitCommitmentV1),
            (root.to_dict(), TrustRootV1),
            (receipt.artifacts[0].to_dict(), ObservedArtifactV1),
            (receipt.to_dict(), ObservedReceiptV1),
            (
                {
                    "schema_version": "gate-decision/v1",
                    "estimand": "tau_itt",
                    "status": "CERTIFIED",
                    "reason_codes": [],
                    "failed_bindings": [],
                    "bound_lower": None,
                    "bound_upper": None,
                },
                GateDecisionV1,
            ),
        )
        for base, row_type in values_and_types:
            with self.subTest(row_type=row_type.__name__, mutation="extra"):
                extra = copy.deepcopy(base)
                extra["unknown"] = "closed"
                with self.assertRaises(ValueError):
                    row_type.from_dict(extra)
            with self.subTest(row_type=row_type.__name__, mutation="missing"):
                missing = copy.deepcopy(base)
                del missing["schema_version"]
                with self.assertRaises(ValueError):
                    row_type.from_dict(missing)

    def test_direct_construction_rejects_mutable_nested_values(self) -> None:
        root, receipt = _contracts()
        commitment = root.commitments[0]
        artifact = receipt.artifacts[0]
        cases = (
            lambda: replace(commitment, requested_members=["member-a"]),
            lambda: replace(commitment, scorer_weights=list(commitment.scorer_weights)),
            lambda: replace(commitment, policy_record=_policy_dict()),
            lambda: replace(artifact, executed_members=["member-a"]),
            lambda: replace(receipt, artifacts=list(receipt.artifacts)),
            lambda: replace(root, commitments=list(root.commitments)),
        )
        for index, constructor in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                constructor()

    def test_direct_construction_revalidates_mutated_frozen_nested_records(
        self,
    ) -> None:
        root, receipt = _contracts()
        commitment = root.commitments[0]
        artifact = receipt.artifacts[0]
        bad_weight = copy.deepcopy(commitment.scorer_weights[0])
        object.__setattr__(bad_weight, "schema_version", "score-weight/bad")
        bad_policy = copy.deepcopy(commitment.policy_record)
        object.__setattr__(bad_policy, "propensity", math.nan)
        bad_commitment = copy.deepcopy(commitment)
        object.__setattr__(bad_commitment, "schema_version", "unit-commitment/bad")
        bad_artifact = copy.deepcopy(artifact)
        object.__setattr__(bad_artifact, "schema_version", "observed-artifact/bad")

        root_with_bad_commitment = {
            "schema_version": root.schema_version,
            "study_id": root.study_id,
            "commitments": (bad_commitment,),
            "commitments_sha256": _sha256_json([bad_commitment.to_dict()]),
        }
        receipt_payload = {
            "schema_version": receipt.schema_version,
            "study_id": receipt.study_id,
            "trust_root_sha256": receipt.trust_root_sha256,
            "artifacts": [bad_artifact.to_dict()],
        }
        cases = (
            lambda: replace(
                commitment, scorer_weights=(bad_weight, commitment.scorer_weights[1])
            ),
            lambda: replace(commitment, policy_record=bad_policy),
            lambda: TrustRootV1(**root_with_bad_commitment),
            lambda: replace(
                receipt,
                artifacts=(bad_artifact,),
                payload_sha256=_sha256_json(receipt_payload),
            ),
        )
        for index, constructor in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                constructor()

    def test_bool_integer_confusion_and_nonfinite_numbers_are_rejected(self) -> None:
        root, receipt = _contracts()
        policy = root.commitments[0].policy_record
        weight = root.commitments[0].scorer_weights[0]
        certificate = BoundCertificateV1.from_dict(
            _certificate_dict("cert-a", "tau_itt", "B", "6" * 64, -0.2, 0.3)
        )
        cases = (
            lambda: replace(root.commitments[0], assignment=True),
            lambda: replace(receipt.artifacts[0], assignment=False),
            lambda: replace(policy, budget_limit=True),
            lambda: replace(policy, retry_limit=False),
            lambda: replace(policy, propensity=True),
            lambda: replace(weight, weight=True),
            lambda: replace(certificate, lower=True),
            lambda: replace(policy, propensity=math.inf),
            lambda: replace(policy, realized_cost=math.nan),
            lambda: replace(weight, weight=-math.inf),
            lambda: replace(certificate, upper=math.nan),
        )
        for index, constructor in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                constructor()

    def test_tuple_uniqueness_sorting_and_weight_sum_are_closed(self) -> None:
        root, receipt = _contracts()
        commitment = root.commitments[0]
        artifact = receipt.artifacts[0]
        policy = commitment.policy_record
        duplicate_weight = commitment.scorer_weights[0]
        cases = (
            lambda: replace(policy, action_menu=("act-b", "act-a")),
            lambda: replace(policy, action_menu=("act-a", "act-a")),
            lambda: replace(commitment, requested_members=("member-b", "member-a")),
            lambda: replace(
                commitment, scorer_weights=(duplicate_weight, duplicate_weight)
            ),
            lambda: replace(
                commitment, allowed_target_binding_sha256=("3" * 64, "3" * 64)
            ),
            lambda: replace(
                commitment, allowed_protocol_versions=("proto-z", "proto-a")
            ),
            lambda: replace(artifact, executed_members=("member-b", "member-a")),
            lambda: replace(artifact, bound_certificate_ids=("cert-b", "cert-a")),
            lambda: replace(root, commitments=(commitment, commitment)),
            lambda: replace(receipt, artifacts=(artifact, artifact)),
            lambda: replace(
                commitment,
                scorer_weights=(
                    replace(commitment.scorer_weights[0], weight=0.5),
                    replace(commitment.scorer_weights[1], weight=0.4),
                ),
            ),
        )
        for index, constructor in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                constructor()

    def test_domains_bounds_and_stale_digests_are_rejected(self) -> None:
        bad_policies = (
            _policy_dict(chosen_action="not-listed"),
            _policy_dict(propensity=0.0),
            _policy_dict(propensity=1.1),
            _policy_dict(budget_limit=-1),
            _policy_dict(realized_cost=10.1),
        )
        for value in bad_policies:
            with self.subTest(value=value), self.assertRaises(ValueError):
                PolicyRecordV1.from_dict(value)

        certificates = (
            _certificate_dict("c", "bad", "B", "6" * 64, 0.0, 0.1),
            _certificate_dict("c", "tau_itt", "A", "6" * 64, 0.0, 0.1),
            _certificate_dict("c", "tau_cb", "T", "6" * 64, 0.2, 0.1),
            _certificate_dict("c", "tau_cb", "S", "6" * 64, -1.1, 0.0),
            _certificate_dict("c", "psi_natural", "B", "6" * 64, 0.0, 1.1),
        )
        for value in certificates:
            with self.subTest(value=value), self.assertRaises(ValueError):
                BoundCertificateV1.from_dict(value)

        root, receipt = _contracts()
        malformed = copy.deepcopy(root.to_dict())
        malformed["commitments_sha256"] = "A" * 64
        stale_root = copy.deepcopy(root.to_dict())
        stale_root["commitments_sha256"] = "0" * 64
        stale_artifact = copy.deepcopy(receipt.artifacts[0].to_dict())
        stale_artifact["payload_sha256"] = "0" * 64
        stale_receipt = copy.deepcopy(receipt.to_dict())
        stale_receipt["payload_sha256"] = "0" * 64
        for row_type, value in (
            (TrustRootV1, malformed),
            (TrustRootV1, stale_root),
            (ObservedArtifactV1, stale_artifact),
            (ObservedReceiptV1, stale_receipt),
        ):
            with (
                self.subTest(row_type=row_type.__name__),
                self.assertRaises(ValueError),
            ):
                row_type.from_dict(value)

    def test_direct_schema_and_allowed_primary_repetition_are_rejected(self) -> None:
        root, receipt = _contracts()
        commitment = root.commitments[0]
        primary_scorer = (
            "54be4747d28670736375a5839514c161cd9b3b300b59d17df5bbfcc6b15663b6"
        )
        cases = (
            lambda: replace(
                commitment.scorer_weights[0], schema_version="score-weight/v2"
            ),
            lambda: replace(
                commitment.policy_record, schema_version="policy-record/v2"
            ),
            lambda: replace(commitment, schema_version="unit-commitment/v2"),
            lambda: replace(root, schema_version="trust-root/v2"),
            lambda: replace(
                receipt.artifacts[0], schema_version="observed-artifact/v2"
            ),
            lambda: replace(receipt, schema_version="observed-receipt/v2"),
            lambda: replace(commitment, allowed_target_binding_sha256=("1" * 64,)),
            lambda: replace(
                commitment, allowed_scorer_binding_sha256=(primary_scorer,)
            ),
            lambda: replace(commitment, allowed_protocol_versions=("proto-v1",)),
        )
        for index, constructor in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                constructor()


class ReportabilityLatticeTests(unittest.TestCase):
    def test_clean_contract_is_certified_in_fixed_estimand_order(self) -> None:
        root, receipt = _contracts()

        decisions = evaluate_reportability(receipt, root)

        self.assertEqual(
            tuple(row.estimand for row in decisions),
            ("tau_itt", "tau_cb", "psi_natural"),
        )
        self.assertEqual(tuple(row.status for row in decisions), ("CERTIFIED",) * 3)
        self.assertTrue(all(row.reason_codes == () for row in decisions))
        self.assertTrue(all(row.failed_bindings == () for row in decisions))

    def test_v2_unrecoverable_lattice_rows(self) -> None:
        cases = (
            (
                "Z identity",
                _artifact_dict(stratum_id="stratum-wrong"),
                ("NOT_CERTIFIED", "NOT_CERTIFIED", "NOT_CERTIFIED"),
                (("Z_binding_unverified",),) * 3,
            ),
            (
                "Z assignment",
                _artifact_dict(assignment=0),
                ("NOT_CERTIFIED", "NOT_CERTIFIED", "CERTIFIED"),
                (("Z_binding_unverified",), ("Z_binding_unverified",), ()),
            ),
            (
                "A requested action",
                _artifact_dict(requested_action_id="act-b"),
                ("CERTIFIED", "NOT_CERTIFIED", "CERTIFIED"),
                ((), ("A_binding_unverified",), ()),
            ),
            (
                "E execution",
                _artifact_dict(executed_action_id="act-b"),
                ("CERTIFIED", "NOT_CERTIFIED", "CERTIFIED"),
                ((), ("execution_noncompliance",), ()),
            ),
            (
                "B target",
                _artifact_dict(target_binding_sha256="6" * 64),
                ("NOT_CERTIFIED",) * 3,
                (("B_binding_unverified",),) * 3,
            ),
            (
                "T owner",
                _artifact_dict(terminal_owner_id="owner-wrong"),
                ("NOT_CERTIFIED",) * 3,
                (("T_binding_unverified",),) * 3,
            ),
            (
                "S scorer",
                _artifact_dict(scorer_weights=_weights_dict(0.6, 0.4)),
                ("NOT_CERTIFIED",) * 3,
                (("S_binding_unverified",),) * 3,
            ),
            (
                "G protocol",
                _artifact_dict(protocol_version="proto-v3"),
                ("NOT_CERTIFIED",) * 3,
                (("G_binding_unverified",),) * 3,
            ),
            (
                "P policy",
                _artifact_dict(policy_record=_policy_dict(policy_id="policy-b")),
                ("CERTIFIED", "CERTIFIED", "NOT_CERTIFIED"),
                ((), (), ("P_binding_unverified",)),
            ),
        )
        for label, artifact, statuses, reasons in cases:
            with self.subTest(label=label):
                root, receipt = _contracts(artifacts=[artifact])
                decisions = evaluate_reportability(receipt, root)
                self.assertEqual(tuple(row.status for row in decisions), statuses)
                self.assertEqual(tuple(row.reason_codes for row in decisions), reasons)

    def test_execution_noncompliance_preserves_itt_and_natural_policy_only(
        self,
    ) -> None:
        root, receipt = _contracts(
            artifacts=[_artifact_dict(executed_members=["member-a"])]
        )

        decisions = _decision_map(receipt, root)

        self.assertEqual(decisions["tau_itt"].status, "CERTIFIED")
        self.assertEqual(decisions["tau_cb"].status, "NOT_CERTIFIED")
        self.assertEqual(decisions["psi_natural"].status, "CERTIFIED")

    def test_allowed_target_scorer_protocol_and_zero_mass_changes_are_certified(
        self,
    ) -> None:
        zero_mass = _weights_dict() + [
            {"schema_version": "score-weight/v1", "key": "unused", "weight": 0.0}
        ]
        cases = (
            _artifact_dict(target_binding_sha256="3" * 64),
            _artifact_dict(scorer_weights=ALT_WEIGHTS),
            _artifact_dict(protocol_version="proto-v2"),
            _artifact_dict(scorer_weights=zero_mass),
        )
        for artifact in cases:
            with self.subTest(artifact=artifact):
                root, receipt = _contracts(artifacts=[artifact])
                self.assertEqual(_statuses(receipt, root), ("CERTIFIED",) * 3)

    def test_terminal_has_no_equivalence_and_requires_authenticated_certificate(
        self,
    ) -> None:
        observed = "6" * 64
        certificate = _certificate_dict(
            "cert-t",
            "tau_itt",
            "T",
            "20403e9987a5ed413921b923a5bc908f7b54750c3909fc9065477cb23dea48e7",
            -0.4,
            0.5,
        )
        root, receipt = _contracts(
            commitments=[_commitment_dict(certificates=[certificate])],
            artifacts=[
                _artifact_dict(
                    terminal_value_sha256=observed,
                    certificate_ids=["cert-t"],
                )
            ],
        )

        decisions = _decision_map(receipt, root)

        self.assertEqual(decisions["tau_itt"].status, "BOUNDED")
        self.assertEqual(
            (decisions["tau_itt"].bound_lower, decisions["tau_itt"].bound_upper),
            (-0.4, 0.5),
        )
        self.assertEqual(decisions["tau_cb"].status, "NOT_CERTIFIED")
        self.assertEqual(decisions["psi_natural"].status, "NOT_CERTIFIED")

    def test_terminal_owner_drift_rejects_value_only_certificate_digest(self) -> None:
        certificate = _certificate_dict(
            "cert-t-value-only", "tau_itt", "T", "2" * 64, -0.4, 0.5
        )
        root, receipt = _contracts(
            commitments=[_commitment_dict(certificates=[certificate])],
            artifacts=[
                _artifact_dict(
                    terminal_owner_id="owner-wrong",
                    certificate_ids=["cert-t-value-only"],
                )
            ],
        )

        decision = _decision_map(receipt, root)["tau_itt"]

        self.assertEqual(decision.status, "NOT_CERTIFIED")
        self.assertIsNone(decision.bound_lower)
        self.assertIsNone(decision.bound_upper)

    def test_terminal_owner_and_value_drift_accepts_canonical_pair_digest(self) -> None:
        canonical_pair_sha256 = (
            "11106a8bc09497a27d4d2a863d2b2d0fea7e8d32078a622682c099ce23578b9c"
        )
        certificate = _certificate_dict(
            "cert-t-pair", "tau_itt", "T", canonical_pair_sha256, -0.7, 0.4
        )
        root, receipt = _contracts(
            commitments=[_commitment_dict(certificates=[certificate])],
            artifacts=[
                _artifact_dict(
                    terminal_owner_id="owner-b",
                    terminal_value_sha256="6" * 64,
                    certificate_ids=["cert-t-pair"],
                )
            ],
        )

        decision = _decision_map(receipt, root)["tau_itt"]

        self.assertEqual(decision.status, "BOUNDED")
        self.assertEqual((decision.bound_lower, decision.bound_upper), (-0.7, 0.4))

    def test_each_recoverable_binding_is_bounded_per_estimand(self) -> None:
        cases = (
            ("B", {"target_binding_sha256": "6" * 64}, "6" * 64),
            (
                "T",
                {"terminal_value_sha256": "7" * 64},
                "fb99b7182a92358b58b6d66b1e0d324a869321d9f1e7231f723588a2954c2ca8",
            ),
            ("S", {"scorer_weights": _weights_dict(0.6, 0.4)}, None),
        )
        for binding, changes, explicit_digest in cases:
            observed_artifact = _artifact_dict(**changes)
            observed_digest = explicit_digest or _sha256_json(
                observed_artifact["scorer_weights"]
            )
            certificates = [
                _certificate_dict(
                    f"cert-{binding.lower()}-{index}",
                    estimand,
                    binding,
                    observed_digest,
                    lower,
                    upper,
                )
                for index, (estimand, lower, upper) in enumerate(
                    (
                        ("tau_itt", -0.8, 0.7),
                        ("tau_cb", -0.6, 0.5),
                        ("psi_natural", 0.2, 0.9),
                    )
                )
            ]
            ids = sorted(row["certificate_id"] for row in certificates)
            certificates.sort(
                key=lambda row: str(row["certificate_id"]).encode("utf-8")
            )
            observed_artifact = _artifact_dict(certificate_ids=ids, **changes)
            with self.subTest(binding=binding):
                root, receipt = _contracts(
                    commitments=[_commitment_dict(certificates=certificates)],
                    artifacts=[observed_artifact],
                )
                decisions = evaluate_reportability(receipt, root)
                self.assertEqual(
                    tuple(row.status for row in decisions), ("BOUNDED",) * 3
                )
                self.assertEqual(
                    tuple((row.bound_lower, row.bound_upper) for row in decisions),
                    ((-0.8, 0.7), (-0.6, 0.5), (0.2, 0.9)),
                )

    def test_certificate_authentication_requires_id_estimand_binding_and_digest(
        self,
    ) -> None:
        observed = "6" * 64
        base = _certificate_dict("cert-a", "tau_itt", "B", observed, -0.2, 0.3)
        cases = (
            (base, []),
            ({**base, "estimand": "tau_cb"}, ["cert-a"]),
            ({**base, "binding": "T"}, ["cert-a"]),
            ({**base, "observed_binding_sha256": "7" * 64}, ["cert-a"]),
        )
        for certificate, cited_ids in cases:
            with self.subTest(certificate=certificate, cited_ids=cited_ids):
                root, receipt = _contracts(
                    commitments=[_commitment_dict(certificates=[certificate])],
                    artifacts=[
                        _artifact_dict(
                            target_binding_sha256=observed,
                            certificate_ids=cited_ids,
                        )
                    ],
                )
                self.assertEqual(
                    _decision_map(receipt, root)["tau_itt"].status,
                    "NOT_CERTIFIED",
                )

    def test_multiple_certificates_and_units_use_conservative_hull(self) -> None:
        observed = "6" * 64
        certs_a = [
            _certificate_dict("cert-a1", "tau_itt", "B", observed, -0.2, 0.3),
            _certificate_dict("cert-a2", "tau_itt", "B", observed, -0.6, 0.1),
        ]
        certs_b = [_certificate_dict("cert-b1", "tau_itt", "B", observed, -0.1, 0.8)]
        commitments = [
            _commitment_dict(unit_id="unit-a", certificates=certs_a),
            _commitment_dict(unit_id="unit-b", certificates=certs_b),
        ]
        artifacts = [
            _artifact_dict(
                unit_id="unit-a",
                target_binding_sha256=observed,
                certificate_ids=["cert-a1", "cert-a2"],
            ),
            _artifact_dict(
                unit_id="unit-b",
                target_binding_sha256=observed,
                certificate_ids=["cert-b1"],
            ),
        ]

        root, receipt = _contracts(commitments=commitments, artifacts=artifacts)
        decision = _decision_map(receipt, root)["tau_itt"]

        self.assertEqual(decision.status, "BOUNDED")
        self.assertEqual((decision.bound_lower, decision.bound_upper), (-0.6, 0.8))

    def test_all_mismatching_units_need_certificate_coverage(self) -> None:
        observed = "6" * 64
        certificate = _certificate_dict("cert-a", "tau_itt", "B", observed, -0.2, 0.3)
        commitments = [
            _commitment_dict(unit_id="unit-a", certificates=[certificate]),
            _commitment_dict(unit_id="unit-b"),
        ]
        artifacts = [
            _artifact_dict(
                unit_id="unit-a",
                target_binding_sha256=observed,
                certificate_ids=["cert-a"],
            ),
            _artifact_dict(unit_id="unit-b", target_binding_sha256=observed),
        ]
        root, receipt = _contracts(commitments=commitments, artifacts=artifacts)

        self.assertEqual(
            _decision_map(receipt, root)["tau_itt"].status,
            "NOT_CERTIFIED",
        )

    def test_multistratum_multiunit_clean_receipt_preserves_certification(self) -> None:
        commitments = [
            _commitment_dict(unit_id="unit-a"),
            _commitment_dict(
                unit_id="unit-b",
                site_id="site-b",
                stratum_id="stratum-b",
                requested_members=["member-c", "member-d"],
            ),
        ]
        artifacts = [
            _artifact_dict(unit_id="unit-a"),
            _artifact_dict(
                unit_id="unit-b",
                site_id="site-b",
                stratum_id="stratum-b",
                requested_members=["member-c", "member-d"],
                executed_members=["member-c", "member-d"],
            ),
        ]
        root, receipt = _contracts(commitments=commitments, artifacts=artifacts)

        self.assertEqual(_statuses(receipt, root), ("CERTIFIED",) * 3)

    def test_mixed_multiunit_failures_follow_binding_and_state_precedence(self) -> None:
        observed = "6" * 64
        certificate = _certificate_dict("cert-b", "tau_itt", "B", observed, -0.2, 0.3)
        commitments = [
            _commitment_dict(unit_id="unit-a"),
            _commitment_dict(unit_id="unit-b", certificates=[certificate]),
        ]
        artifacts = [
            _artifact_dict(unit_id="unit-a", executed_action_id="act-b"),
            _artifact_dict(
                unit_id="unit-b",
                target_binding_sha256=observed,
                policy_record=_policy_dict(policy_id="policy-b"),
                certificate_ids=["cert-b"],
            ),
        ]
        root, receipt = _contracts(commitments=commitments, artifacts=artifacts)

        decisions = _decision_map(receipt, root)

        self.assertEqual(decisions["tau_itt"].status, "BOUNDED")
        self.assertEqual(decisions["tau_itt"].reason_codes, ("B_binding_unverified",))
        self.assertEqual(decisions["tau_cb"].status, "NOT_CERTIFIED")
        self.assertEqual(
            decisions["tau_cb"].reason_codes,
            ("execution_noncompliance", "B_binding_unverified"),
        )
        self.assertEqual(decisions["tau_cb"].failed_bindings, ("E", "B"))
        self.assertEqual(decisions["psi_natural"].status, "NOT_CERTIFIED")
        self.assertEqual(
            decisions["psi_natural"].reason_codes,
            ("B_binding_unverified", "P_binding_unverified"),
        )


class GlobalFailureAndDecisionSchemaTests(unittest.TestCase):
    def test_global_failures_return_all_not_certified_with_stable_precedence(
        self,
    ) -> None:
        root, receipt = _contracts()

        wrong_root = TrustRootV1.from_dict(
            {
                **root.to_dict(),
                "study_id": "study-b",
                "commitments_sha256": root.commitments_sha256,
            }
        )
        different_study_root, different_study_receipt = _contracts(
            root_study="study-a",
            receipt_study="study-b",
            artifacts=[_artifact_dict(study_id="study-b")],
        )
        missing_dict = receipt.to_dict()
        missing_dict["artifacts"] = [_artifact_dict(unit_id="unit-b")]
        missing_dict["payload_sha256"] = _sha256_json(
            {
                key: value
                for key, value in missing_dict.items()
                if key != "payload_sha256"
            }
        )
        coverage_receipt = ObservedReceiptV1.from_dict(missing_dict)
        invalid_receipt = copy.deepcopy(receipt)
        object.__setattr__(invalid_receipt.artifacts[0], "schema_version", "bad")

        cases = (
            (wrong_root, receipt, "trust_root_mismatch"),
            (different_study_root, different_study_receipt, "study_binding_mismatch"),
            (root, coverage_receipt, "unit_coverage_mismatch"),
            (root, invalid_receipt, "artifact_identity_invalid"),
        )
        for case_root, case_receipt, reason in cases:
            with self.subTest(reason=reason):
                decisions = evaluate_reportability(case_receipt, case_root)
                self.assertEqual(
                    tuple(row.status for row in decisions), ("NOT_CERTIFIED",) * 3
                )
                self.assertEqual(
                    tuple(row.reason_codes for row in decisions), ((reason,),) * 3
                )
                self.assertTrue(all(row.failed_bindings == () for row in decisions))

    def test_mutated_stale_digests_and_duplicate_artifacts_are_closed_at_evaluation(
        self,
    ) -> None:
        root, receipt = _contracts()
        stale_root = copy.deepcopy(root)
        object.__setattr__(stale_root, "commitments_sha256", "0" * 64)
        stale_receipt = copy.deepcopy(receipt)
        object.__setattr__(stale_receipt, "payload_sha256", "0" * 64)
        duplicate_receipt = copy.deepcopy(receipt)
        object.__setattr__(
            duplicate_receipt,
            "artifacts",
            (duplicate_receipt.artifacts[0], duplicate_receipt.artifacts[0]),
        )

        cases = (
            (stale_root, receipt, "trust_root_mismatch"),
            (root, stale_receipt, "artifact_identity_invalid"),
            (root, duplicate_receipt, "unit_coverage_mismatch"),
        )
        for case_root, case_receipt, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(
                    tuple(
                        row.reason_codes
                        for row in evaluate_reportability(case_receipt, case_root)
                    ),
                    ((reason,),) * 3,
                )

    def test_missing_and_extra_units_are_coverage_failures(self) -> None:
        root, receipt = _contracts()
        extra = copy.deepcopy(receipt)
        extra_artifact = ObservedArtifactV1.from_dict(_artifact_dict(unit_id="unit-b"))
        object.__setattr__(extra, "artifacts", (*extra.artifacts, extra_artifact))
        missing = copy.deepcopy(receipt)
        object.__setattr__(missing, "artifacts", ())
        for mutated in (extra, missing):
            with self.subTest(count=len(mutated.artifacts)):
                self.assertEqual(
                    evaluate_reportability(mutated, root)[0].reason_codes,
                    ("unit_coverage_mismatch",),
                )

    def test_gate_decision_schema_enforces_registered_order_and_bound_shape(
        self,
    ) -> None:
        valid = GateDecisionV1(
            schema_version="gate-decision/v1",
            estimand="tau_cb",
            status="BOUNDED",
            reason_codes=("execution_noncompliance", "B_binding_unverified"),
            failed_bindings=("E", "B"),
            bound_lower=-0.5,
            bound_upper=0.6,
        )
        self.assertEqual(
            valid.to_dict(),
            {
                "schema_version": "gate-decision/v1",
                "estimand": "tau_cb",
                "status": "BOUNDED",
                "reason_codes": ["execution_noncompliance", "B_binding_unverified"],
                "failed_bindings": ["E", "B"],
                "bound_lower": -0.5,
                "bound_upper": 0.6,
            },
        )
        cases = (
            lambda: replace(valid, estimand="unknown"),
            lambda: replace(valid, status="MAYBE"),
            lambda: replace(valid, failed_bindings=("B", "E")),
            lambda: replace(valid, failed_bindings=("E", "E")),
            lambda: replace(
                valid, reason_codes=("B_binding_unverified", "execution_noncompliance")
            ),
            lambda: replace(valid, reason_codes=("made_up",)),
            lambda: replace(valid, bound_lower=None),
            lambda: replace(valid, bound_upper=math.inf),
            lambda: replace(valid, status="CERTIFIED"),
        )
        for index, constructor in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                constructor()


if __name__ == "__main__":
    unittest.main()
