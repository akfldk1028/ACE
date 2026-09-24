from __future__ import annotations

import hashlib
import importlib
import json
import re
import unittest
from collections import Counter
from dataclasses import replace

from iclr2027.estimand_receipts import (
    ObservedArtifactV1,
    ObservedReceiptV1,
    evaluate_reportability,
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _generate_clean_benchmark():
    try:
        module = importlib.import_module("iclr2027.estimand_receipt_generator")
    except ModuleNotFoundError as exc:
        raise AssertionError("Task 4 generator module is missing") from exc
    return module.generate_clean_benchmark()


def _target_object(
    *, unit_id: str, site_id: str, target_index: int
) -> dict[str, object]:
    return {
        "schema_version": "synthetic-target/v1",
        "unit_id": unit_id,
        "site_id": site_id,
        "target_index": target_index,
    }


def _score_rows(
    *, unit_id: str, assignment: int, keys: tuple[str, ...]
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key in sorted(keys, key=lambda item: item.encode("utf-8")):
        source = f"score/v1\0{unit_id}\0{key}\0{assignment}".encode()
        rows.append(
            {
                "schema_version": "rational-obligation-score/v1",
                "key": key,
                "numerator": int(hashlib.sha256(source).hexdigest()[:8], 16),
                "denominator": 4_294_967_295,
            }
        )
    return rows


def _information_snapshot(
    *,
    study_id: str,
    site_id: str,
    unit_id: str,
    stratum_id: str,
    target_binding_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": "policy-information-snapshot/v1",
        "study_id": study_id,
        "site_id": site_id,
        "unit_id": unit_id,
        "stratum_id": stratum_id,
        "target_binding_sha256": target_binding_sha256,
        "action_menu": ["action-baseline-v1", "action-receipt-v1"],
        "budget_limit": 5,
        "retry_limit": 0,
    }


def _decision_event(
    *,
    information_snapshot_sha256: str,
    chosen_action: str,
    realized_cost: float,
) -> dict[str, object]:
    return {
        "schema_version": "policy-decision-event/v1",
        "policy_id": "policy-balanced-v1",
        "information_snapshot_sha256": information_snapshot_sha256,
        "chosen_action": chosen_action,
        "propensity": 0.5,
        "budget_limit": 5,
        "realized_cost": realized_cost,
        "retry_limit": 0,
    }


def _reseal_artifact(
    artifact: ObservedArtifactV1, **changes: object
) -> ObservedArtifactV1:
    value = artifact.to_dict()
    value.update(changes)
    payload = dict(value)
    del payload["payload_sha256"]
    value["payload_sha256"] = _sha256_json(payload)
    return ObservedArtifactV1.from_dict(value)


def _receipt(benchmark, artifacts: tuple[ObservedArtifactV1, ...]) -> ObservedReceiptV1:
    payload: dict[str, object] = {
        "schema_version": "observed-receipt/v1",
        "study_id": "estimand-receipt-synthetic-v1",
        "trust_root_sha256": _sha256_json(benchmark.trust_root.to_dict()),
        "artifacts": [item.to_dict() for item in artifacts],
    }
    return ObservedReceiptV1.from_dict(
        {**payload, "payload_sha256": _sha256_json(payload)}
    )


class EstimandReceiptGeneratorTests(unittest.TestCase):
    maxDiff = None

    def test_clean_generator_has_exact_balanced_anonymous_census(self) -> None:
        benchmark = _generate_clean_benchmark()

        self.assertEqual(benchmark.schema_version, "clean-benchmark/v1")
        self.assertEqual(benchmark.study_id, "estimand-receipt-synthetic-v1")
        self.assertEqual(len(benchmark.ledger), 64)
        self.assertEqual(len(benchmark.trust_root.commitments), 64)
        self.assertEqual(len(benchmark.artifacts), 64)

        expected_sites = {f"syn-site-{index:02d}" for index in range(8)}
        self.assertEqual({row.site_id for row in benchmark.ledger}, expected_sites)
        expected_units = {
            f"syn-target-{site_index:02d}-{target_index:02d}"
            for site_index in range(8)
            for target_index in range(8)
        }
        self.assertEqual({row.unit_id for row in benchmark.ledger}, expected_units)

        by_site: dict[str, list[object]] = {site: [] for site in expected_sites}
        for row in benchmark.ledger:
            by_site[row.site_id].append(row)
        for site_id, rows in by_site.items():
            self.assertEqual(len(rows), 8, site_id)
            self.assertEqual(Counter(row.assignment for row in rows), {0: 4, 1: 4})
            self.assertEqual({row.target_index for row in rows}, set(range(8)))

        identity_text = "\n".join(
            (
                benchmark.study_id,
                *(
                    value
                    for artifact in benchmark.artifacts
                    for value in (
                        artifact.site_id,
                        artifact.unit_id,
                        artifact.requested_action_id,
                        *artifact.requested_members,
                        artifact.executed_action_id,
                        *artifact.executed_members,
                        artifact.terminal_owner_id,
                        artifact.protocol_version,
                        artifact.policy_record.policy_id,
                    )
                ),
            )
        ).lower()
        self.assertIsNone(re.search(r"(?<!\d)\d{19}(?!\d)", identity_text))
        text = _canonical_json(benchmark.to_dict()).lower()
        for forbidden in ("pnu", "mutation", "fault", "gold", "oracle"):
            self.assertNotIn(forbidden, text)

    def test_every_clean_binding_is_independently_derived_from_exact_inputs(
        self,
    ) -> None:
        benchmark = _generate_clean_benchmark()
        expected_keys = (
            "geometry",
            "law",
            "parking",
            "program",
            "site_evidence",
        )
        commitments = {
            commitment.unit_id: commitment
            for commitment in benchmark.trust_root.commitments
        }
        artifacts = {artifact.unit_id: artifact for artifact in benchmark.artifacts}

        for row in benchmark.ledger:
            commitment = commitments[row.unit_id]
            artifact = artifacts[row.unit_id]
            assignment = row.target_index % 2
            action = "action-baseline-v1" if assignment == 0 else "action-receipt-v1"
            members = (
                ("agent-builder",)
                if assignment == 0
                else ("agent-builder", "agent-reviewer", "agent-router")
            )
            realized_cost = 1.0 if assignment == 0 else 3.0
            stratum_id = _sha256_json(
                {
                    "schema_version": "synthetic-stratum/v1",
                    "site_id": row.site_id,
                }
            )
            target = _target_object(
                unit_id=row.unit_id,
                site_id=row.site_id,
                target_index=row.target_index,
            )
            target_binding = _sha256_json(target)
            partner_index = row.target_index ^ 2
            partner_binding = _sha256_json(
                _target_object(
                    unit_id=(f"syn-target-{row.site_id[-2:]}-{partner_index:02d}"),
                    site_id=row.site_id,
                    target_index=partner_index,
                )
            )
            scores = _score_rows(
                unit_id=row.unit_id,
                assignment=assignment,
                keys=expected_keys,
            )
            terminal_value = _sha256_json(scores)
            snapshot = _information_snapshot(
                study_id="estimand-receipt-synthetic-v1",
                site_id=row.site_id,
                unit_id=row.unit_id,
                stratum_id=stratum_id,
                target_binding_sha256=target_binding,
            )
            snapshot_digest = _sha256_json(snapshot)
            decision = _decision_event(
                information_snapshot_sha256=snapshot_digest,
                chosen_action=action,
                realized_cost=realized_cost,
            )
            decision_digest = _sha256_json(decision)
            expected_policy = {
                "schema_version": "policy-record/v1",
                "policy_id": "policy-balanced-v1",
                "action_menu": ["action-baseline-v1", "action-receipt-v1"],
                "information_snapshot_sha256": snapshot_digest,
                "chosen_action": action,
                "propensity": 0.5,
                "budget_limit": 5,
                "realized_cost": realized_cost,
                "retry_limit": 0,
                "decision_event_sha256": decision_digest,
            }
            expected_weights = [
                {"schema_version": "score-weight/v1", "key": key, "weight": 0.2}
                for key in expected_keys
            ]

            self.assertEqual(row.schema_version, "clean-construction-row/v1")
            self.assertEqual(row.assignment, assignment)
            self.assertEqual(row.stratum_id, stratum_id)
            self.assertEqual(row.target.to_dict(), target)
            self.assertEqual(
                [score.to_dict() for score in row.obligation_scores], scores
            )
            self.assertEqual(row.information_snapshot.to_dict(), snapshot)
            self.assertEqual(row.decision_event.to_dict(), decision)

            self.assertEqual(commitment.site_id, row.site_id)
            self.assertEqual(commitment.stratum_id, stratum_id)
            self.assertEqual(commitment.assignment, assignment)
            self.assertEqual(commitment.requested_action_id, action)
            self.assertEqual(commitment.requested_members, members)
            self.assertEqual(commitment.target_binding_sha256, target_binding)
            self.assertEqual(
                commitment.terminal_owner_id, f"terminal-owner-{row.unit_id}"
            )
            self.assertEqual(commitment.terminal_value_sha256, terminal_value)
            self.assertEqual(
                [weight.to_dict() for weight in commitment.scorer_weights],
                expected_weights,
            )
            self.assertEqual(
                commitment.protocol_version, "estimand-receipt-protocol-v1"
            )
            self.assertEqual(commitment.policy_record.to_dict(), expected_policy)
            self.assertEqual(
                commitment.allowed_target_binding_sha256, (partner_binding,)
            )
            self.assertEqual(commitment.allowed_scorer_binding_sha256, ())
            self.assertEqual(
                commitment.allowed_protocol_versions,
                ("estimand-receipt-protocol-v1-compatible",),
            )
            self.assertEqual(commitment.bound_certificates, ())

            self.assertEqual(artifact.requested_action_id, action)
            self.assertEqual(artifact.executed_action_id, action)
            self.assertEqual(artifact.requested_members, members)
            self.assertEqual(artifact.executed_members, members)
            self.assertEqual(artifact.schema_version, "observed-artifact/v1")
            self.assertEqual(artifact.study_id, "estimand-receipt-synthetic-v1")
            self.assertEqual(artifact.unit_id, row.unit_id)
            self.assertEqual(artifact.site_id, row.site_id)
            self.assertEqual(artifact.stratum_id, stratum_id)
            self.assertEqual(artifact.assignment, assignment)
            self.assertEqual(artifact.target_binding_sha256, target_binding)
            self.assertEqual(
                artifact.terminal_owner_id, f"terminal-owner-{row.unit_id}"
            )
            self.assertEqual(artifact.terminal_value_sha256, terminal_value)
            self.assertEqual(
                [weight.to_dict() for weight in artifact.scorer_weights],
                expected_weights,
            )
            self.assertEqual(artifact.protocol_version, "estimand-receipt-protocol-v1")
            self.assertEqual(artifact.policy_record.to_dict(), expected_policy)
            self.assertEqual(artifact.bound_certificate_ids, ())
            artifact_payload = artifact.to_dict()
            del artifact_payload["payload_sha256"]
            self.assertEqual(artifact.payload_sha256, _sha256_json(artifact_payload))

            self.assertEqual(row.commitment_sha256, _sha256_json(commitment.to_dict()))
            self.assertEqual(row.artifact_sha256, _sha256_json(artifact.to_dict()))

        commitment_rows = [
            commitment.to_dict() for commitment in benchmark.trust_root.commitments
        ]
        self.assertEqual(
            benchmark.trust_root.commitments_sha256,
            _sha256_json(commitment_rows),
        )

    def test_fully_resealed_cross_bound_artifact_is_rejected(self) -> None:
        benchmark = _generate_clean_benchmark()
        artifact_value = benchmark.artifacts[0].to_dict()
        artifact_value.update(
            {
                "site_id": "syn-site-99",
                "assignment": 1,
                "terminal_owner_id": "terminal-owner-corrupt",
                "protocol_version": "estimand-receipt-protocol-v999",
            }
        )
        artifact_payload = dict(artifact_value)
        del artifact_payload["payload_sha256"]
        artifact_value["payload_sha256"] = _sha256_json(artifact_payload)
        resealed_artifact = ObservedArtifactV1.from_dict(artifact_value)
        resealed_row = replace(
            benchmark.ledger[0],
            artifact_sha256=_sha256_json(resealed_artifact.to_dict()),
        )
        resealed_ledger = (resealed_row, *benchmark.ledger[1:])
        resealed_artifacts = (resealed_artifact, *benchmark.artifacts[1:])

        with self.assertRaises(ValueError):
            type(benchmark)(
                schema_version=benchmark.schema_version,
                study_id=benchmark.study_id,
                ledger=resealed_ledger,
                trust_root=benchmark.trust_root,
                artifacts=resealed_artifacts,
            )

    def test_clean_boundary_rejects_order_and_coverage_drift(self) -> None:
        benchmark = _generate_clean_benchmark()

        with self.assertRaises(ValueError):
            replace(benchmark, artifacts=benchmark.artifacts[:-1])
        with self.assertRaises(ValueError):
            replace(benchmark, artifacts=tuple(reversed(benchmark.artifacts)))
        with self.assertRaises(ValueError):
            replace(benchmark, ledger=tuple(reversed(benchmark.ledger)))

    def test_registered_target_partners_are_exact_symmetric_and_assignment_safe(
        self,
    ) -> None:
        benchmark = _generate_clean_benchmark()
        commitments = {item.unit_id: item for item in benchmark.trust_root.commitments}

        for site_index in range(8):
            for target_index in range(8):
                unit_id = f"syn-target-{site_index:02d}-{target_index:02d}"
                partner_index = target_index ^ 2
                partner_id = f"syn-target-{site_index:02d}-{partner_index:02d}"
                expected_partner_digest = _sha256_json(
                    _target_object(
                        unit_id=partner_id,
                        site_id=f"syn-site-{site_index:02d}",
                        target_index=partner_index,
                    )
                )
                commitment = commitments[unit_id]
                partner = commitments[partner_id]

                self.assertEqual(
                    commitment.allowed_target_binding_sha256,
                    (expected_partner_digest,),
                )
                self.assertEqual(
                    commitment.allowed_target_binding_sha256,
                    (partner.target_binding_sha256,),
                )
                self.assertEqual(
                    partner.allowed_target_binding_sha256,
                    (commitment.target_binding_sha256,),
                )
                self.assertEqual(commitment.site_id, partner.site_id)
                self.assertEqual(commitment.assignment, partner.assignment)
                self.assertNotEqual(commitment.unit_id, partner.unit_id)
                self.assertEqual(commitment.allowed_scorer_binding_sha256, ())
                self.assertEqual(
                    commitment.allowed_protocol_versions,
                    ("estimand-receipt-protocol-v1-compatible",),
                )
                self.assertEqual(commitment.bound_certificates, ())

    def test_registered_invariance_receipts_are_certified_but_not_clean(self) -> None:
        benchmark = _generate_clean_benchmark()
        rows = {item.unit_id: item for item in benchmark.ledger}

        target_swaps = tuple(
            _reseal_artifact(
                artifact,
                target_binding_sha256=_sha256_json(
                    _target_object(
                        unit_id=(
                            f"syn-target-{rows[artifact.unit_id].site_id[-2:]}-"
                            f"{rows[artifact.unit_id].target_index ^ 2:02d}"
                        ),
                        site_id=rows[artifact.unit_id].site_id,
                        target_index=rows[artifact.unit_id].target_index ^ 2,
                    )
                ),
            )
            for artifact in benchmark.artifacts
        )
        zero_weight_scorers = tuple(
            _reseal_artifact(
                artifact,
                scorer_weights=[
                    *[item.to_dict() for item in artifact.scorer_weights],
                    {
                        "schema_version": "score-weight/v1",
                        "key": "zero_mass_control",
                        "weight": 0.0,
                    },
                ],
            )
            for artifact in benchmark.artifacts
        )
        compatible_protocols = tuple(
            _reseal_artifact(
                artifact,
                protocol_version="estimand-receipt-protocol-v1-compatible",
            )
            for artifact in benchmark.artifacts
        )

        for artifacts in (
            target_swaps,
            zero_weight_scorers,
            compatible_protocols,
        ):
            decisions = evaluate_reportability(
                _receipt(benchmark, artifacts), benchmark.trust_root
            )
            self.assertEqual(
                tuple(item.status for item in decisions),
                ("CERTIFIED", "CERTIFIED", "CERTIFIED"),
            )
            self.assertEqual(
                tuple(item.reason_codes for item in decisions), ((), (), ())
            )
            with self.assertRaises(ValueError):
                replace(benchmark, artifacts=artifacts)

    def test_clean_rows_are_byte_sorted_and_input_object_hashes_ignore_key_order(
        self,
    ) -> None:
        benchmark = _generate_clean_benchmark()
        unit_ids = tuple(row.unit_id for row in benchmark.ledger)
        self.assertEqual(unit_ids, tuple(sorted(unit_ids, key=lambda x: x.encode())))
        self.assertEqual(
            tuple(item.unit_id for item in benchmark.trust_root.commitments), unit_ids
        )
        self.assertEqual(tuple(item.unit_id for item in benchmark.artifacts), unit_ids)

        row = benchmark.ledger[0]
        commitment = benchmark.trust_root.commitments[0]
        target = row.target.to_dict()
        snapshot = row.information_snapshot.to_dict()
        decision = row.decision_event.to_dict()
        self.assertEqual(
            _sha256_json(dict(reversed(tuple(target.items())))),
            commitment.target_binding_sha256,
        )
        self.assertEqual(
            _sha256_json(dict(reversed(tuple(snapshot.items())))),
            commitment.policy_record.information_snapshot_sha256,
        )
        self.assertEqual(
            _sha256_json(dict(reversed(tuple(decision.items())))),
            commitment.policy_record.decision_event_sha256,
        )

        reverse_source_keys = (
            "site_evidence",
            "program",
            "parking",
            "law",
            "geometry",
        )
        independently_sorted_scores = _score_rows(
            unit_id=row.unit_id,
            assignment=row.assignment,
            keys=reverse_source_keys,
        )
        self.assertEqual(
            _sha256_json(independently_sorted_scores),
            commitment.terminal_value_sha256,
        )

    def test_requested_and_executed_clean_fields_are_identical(self) -> None:
        benchmark = _generate_clean_benchmark()

        for artifact in benchmark.artifacts:
            self.assertEqual(artifact.requested_action_id, artifact.executed_action_id)
            self.assertEqual(artifact.requested_members, artifact.executed_members)
            self.assertEqual(
                artifact.scorer_weights,
                next(
                    item.scorer_weights
                    for item in benchmark.trust_root.commitments
                    if item.unit_id == artifact.unit_id
                ),
            )

    def test_generation_has_deterministic_canonical_bytes(self) -> None:
        first = _generate_clean_benchmark()
        second = _generate_clean_benchmark()

        first_bytes = _canonical_json(first.to_dict()).encode("utf-8")
        second_bytes = _canonical_json(second.to_dict()).encode("utf-8")
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(
            hashlib.sha256(first_bytes).digest(),
            hashlib.sha256(second_bytes).digest(),
        )


if __name__ == "__main__":
    unittest.main()
