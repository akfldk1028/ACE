"""Behavioral tests for anonymous estimand-receipt evaluators."""

from __future__ import annotations

import hashlib
import importlib
import json
import unittest

from iclr2027.estimand_receipt_faults import apply_fault
from iclr2027.estimand_receipt_generator import generate_clean_benchmark
from iclr2027.estimand_receipts import (
    ObservedArtifactV1,
    ObservedReceiptV1,
    ScoreWeightV1,
    TrustRootV1,
    evaluate_reportability,
)


CONFIGURATIONS = (
    "completion_only",
    "hash_only",
    "trace_schema_closure",
    "field_complete_no_semantics",
    "ablate_E",
    "ablate_B",
    "ablate_T",
    "ablate_S",
    "ablate_G",
    "ablate_P",
    "full_estimand_gate",
)
ESTIMANDS = ("tau_itt", "tau_cb", "psi_natural")


def _module():
    try:
        return importlib.import_module("iclr2027.estimand_receipt_evaluators")
    except ModuleNotFoundError as exc:
        raise AssertionError("estimand receipt evaluators must be implemented") from exc


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _case_id(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _public_row(case_id: str, artifact: ObservedArtifactV1) -> bytes:
    return _canonical_bytes(
        {
            "schema_version": "public-artifact-row/v1",
            "case_id": case_id,
            "artifact": artifact.to_dict(),
        }
    )


def _reseal(artifact: ObservedArtifactV1, **changes: object) -> ObservedArtifactV1:
    payload = artifact.to_dict()
    payload.pop("payload_sha256")
    payload.update(changes)
    return ObservedArtifactV1.from_dict(
        {**payload, "payload_sha256": _sha256_json(payload)}
    )


def _status_map(rows: tuple[object, ...], configuration: str) -> dict[str, str]:
    return {
        row.estimand: row.status for row in rows if row.configuration == configuration
    }


def _decision(rows: tuple[object, ...], configuration: str, estimand: str):
    return next(
        row
        for row in rows
        if row.configuration == configuration and row.estimand == estimand
    )


class EstimandReceiptEvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = generate_clean_benchmark()
        cls.root_bytes = _canonical_bytes(cls.clean.trust_root.to_dict())
        cls.artifact_by_id = {
            artifact.unit_id: artifact for artifact in cls.clean.artifacts
        }

    def _evaluate(self, artifact: ObservedArtifactV1, label: str = "case"):
        return _module().evaluate_frozen_artifacts(
            (_public_row(_case_id(label), artifact),), self.root_bytes
        )

    def test_exact_configuration_order_public_schema_digest_and_sort(self) -> None:
        # Catches renamed/reordered configurations, gold leakage, and unstable rows.
        module = _module()
        self.assertEqual(module.CONFIGURATIONS, CONFIGURATIONS)
        rows = self._evaluate(self.clean.artifacts[0])
        self.assertEqual(len(rows), 11 * 3)
        self.assertEqual(
            tuple((row.configuration, row.estimand) for row in rows),
            tuple(
                (config, estimand)
                for config in CONFIGURATIONS
                for estimand in ESTIMANDS
            ),
        )
        expected_keys = {
            "public_case_id",
            "configuration",
            "estimand",
            "status",
            "reason_codes",
            "failed_bindings",
            "bounds",
            "canonical_decision_digest",
        }
        forbidden = {"mutation", "order", "family", "expected_status"}
        for row in rows:
            value = row.to_dict()
            self.assertEqual(set(value), expected_keys)
            self.assertTrue(forbidden.isdisjoint(value))
            digest = value.pop("canonical_decision_digest")
            self.assertEqual(digest, _sha256_json(value))

    def test_each_baseline_runs_when_the_semantic_gate_is_unavailable(self) -> None:
        # Catches baseline labels implemented as postprocessing of the full gate.
        module = _module()
        public = _public_row(_case_id("baseline-isolation"), self.clean.artifacts[0])
        original = module.evaluate_reportability

        def forbidden_semantic_gate(*_args: object, **_kwargs: object):
            raise AssertionError("baseline called semantic gate")

        module.evaluate_reportability = forbidden_semantic_gate
        try:
            for configuration in CONFIGURATIONS[:4]:
                with self.subTest(configuration=configuration):
                    rows = module.evaluate_configuration(
                        configuration, (public,), self.root_bytes
                    )
                    self.assertEqual(len(rows), 3)
                    self.assertEqual(
                        tuple(row.status for row in rows), ("CERTIFIED",) * 3
                    )
            with self.assertRaisesRegex(AssertionError, "semantic gate"):
                module.evaluate_configuration(
                    "full_estimand_gate", (public,), self.root_bytes
                )
        finally:
            module.evaluate_reportability = original

    def test_baseline_information_paths_are_differentially_closed(self) -> None:
        # Catches four aliases hidden behind one fully semantic parser.
        module = _module()
        source = self.clean.artifacts[0].to_dict()

        stale_hash = dict(source)
        stale_hash["payload_sha256"] = "0" * 64
        stale_row = _canonical_bytes(
            {
                "schema_version": "public-artifact-row/v1",
                "case_id": _case_id("stale-hash"),
                "artifact": stale_hash,
            }
        )
        self.assertEqual(
            len(
                module.evaluate_configuration(
                    "completion_only", (stale_row,), self.root_bytes
                )
            ),
            3,
        )
        with self.assertRaises(ValueError):
            module.evaluate_configuration("hash_only", (stale_row,), self.root_bytes)

        opaque_payload = {"opaque": "canonical-but-not-a-receipt"}
        opaque_artifact = {
            **opaque_payload,
            "payload_sha256": _sha256_json(opaque_payload),
        }
        opaque_row = _canonical_bytes(
            {
                "schema_version": "public-artifact-row/v1",
                "case_id": _case_id("opaque"),
                "artifact": opaque_artifact,
            }
        )
        self.assertEqual(
            len(
                module.evaluate_configuration(
                    "hash_only", (opaque_row,), self.root_bytes
                )
            ),
            3,
        )
        with self.assertRaises(ValueError):
            module.evaluate_configuration(
                "trace_schema_closure", (opaque_row,), self.root_bytes
            )

        wrong_nested_schema = dict(source)
        wrong_nested_schema.pop("payload_sha256")
        wrong_nested_schema["policy_record"] = {
            **wrong_nested_schema["policy_record"],
            "schema_version": "policy-record/not-v1",
        }
        wrong_nested_schema["payload_sha256"] = _sha256_json(wrong_nested_schema)
        wrong_nested_row = _canonical_bytes(
            {
                "schema_version": "public-artifact-row/v1",
                "case_id": _case_id("wrong-nested-schema"),
                "artifact": wrong_nested_schema,
            }
        )
        self.assertEqual(
            len(
                module.evaluate_configuration(
                    "hash_only", (wrong_nested_row,), self.root_bytes
                )
            ),
            3,
        )
        with self.assertRaises(ValueError):
            module.evaluate_configuration(
                "trace_schema_closure", (wrong_nested_row,), self.root_bytes
            )

        invalid_domain = dict(source)
        invalid_domain.pop("payload_sha256")
        invalid_domain["assignment"] = 2
        invalid_domain["payload_sha256"] = _sha256_json(invalid_domain)
        invalid_domain_row = _canonical_bytes(
            {
                "schema_version": "public-artifact-row/v1",
                "case_id": _case_id("invalid-domain"),
                "artifact": invalid_domain,
            }
        )
        self.assertEqual(
            len(
                module.evaluate_configuration(
                    "trace_schema_closure", (invalid_domain_row,), self.root_bytes
                )
            ),
            3,
        )
        with self.assertRaises(ValueError):
            module.evaluate_configuration(
                "field_complete_no_semantics",
                (invalid_domain_row,),
                self.root_bytes,
            )

    def test_full_gate_is_decision_equivalent_to_task2_one_commitment_receipt(
        self,
    ) -> None:
        # Catches a lookalike gate that does not actually delegate Task-2 semantics.
        artifact = apply_fault(
            self.clean.artifacts[0],
            "terminal_stale_owner",
            partner=self.clean.artifacts[0],
        )
        observed = self._evaluate(artifact, "terminal")
        commitment = self.clean.trust_root.commitments[0]
        one_root_dict = {
            "schema_version": "trust-root/v1",
            "study_id": self.clean.trust_root.study_id,
            "commitments": [commitment.to_dict()],
            "commitments_sha256": _sha256_json([commitment.to_dict()]),
        }
        one_root = TrustRootV1.from_dict(one_root_dict)
        receipt_payload = {
            "schema_version": "observed-receipt/v1",
            "study_id": one_root.study_id,
            "trust_root_sha256": _sha256_json(one_root.to_dict()),
            "artifacts": [artifact.to_dict()],
        }
        receipt = ObservedReceiptV1.from_dict(
            {**receipt_payload, "payload_sha256": _sha256_json(receipt_payload)}
        )
        expected = evaluate_reportability(receipt, one_root)
        self.assertEqual(
            tuple(
                (
                    row.status,
                    row.reason_codes,
                    row.failed_bindings,
                    row.bound_lower,
                    row.bound_upper,
                )
                for row in expected
            ),
            tuple(
                (
                    row.status,
                    row.reason_codes,
                    row.failed_bindings,
                    None if row.bounds is None else row.bounds.lower,
                    None if row.bounds is None else row.bounds.upper,
                )
                for row in observed
                if row.configuration == "full_estimand_gate"
            ),
        )

    def test_selective_faults_and_single_binding_ablations_are_exact(self) -> None:
        # Catches all-estimand blocking and ablations that remove the wrong binding.
        source = self.clean.artifacts[0]
        cases = {
            "E": (
                apply_fault(source, "execution_omit_geometry", partner=source),
                ("CERTIFIED", "NOT_CERTIFIED", "CERTIFIED"),
            ),
            "B": (
                apply_fault(
                    source,
                    "target_rebind_same_site_same_assignment",
                    partner=self.artifact_by_id["syn-target-00-04"],
                ),
                ("NOT_CERTIFIED", "NOT_CERTIFIED", "NOT_CERTIFIED"),
            ),
            "P": (
                apply_fault(source, "policy_menu_drift", partner=source),
                ("CERTIFIED", "CERTIFIED", "NOT_CERTIFIED"),
            ),
        }
        for family, (artifact, expected) in cases.items():
            with self.subTest(family=family):
                rows = self._evaluate(artifact, family)
                self.assertEqual(
                    tuple(_status_map(rows, "full_estimand_gate").values()), expected
                )
                self.assertEqual(
                    tuple(_status_map(rows, f"ablate_{family}").values()),
                    ("CERTIFIED", "CERTIFIED", "CERTIFIED"),
                )

    def test_compound_ablations_retain_every_nonablated_failure(self) -> None:
        # Catches an ablation that clears the whole failure closure for compounds.
        source = self.clean.artifacts[0]
        execution = apply_fault(source, "execution_omit_geometry", partner=source)
        compound = apply_fault(
            execution,
            "target_rebind_same_site_same_assignment",
            partner=self.artifact_by_id["syn-target-00-04"],
        )
        rows = self._evaluate(compound, "compound")
        self.assertEqual(
            tuple(_status_map(rows, "full_estimand_gate").values()),
            ("NOT_CERTIFIED", "NOT_CERTIFIED", "NOT_CERTIFIED"),
        )
        self.assertEqual(
            tuple(_status_map(rows, "ablate_E").values()),
            ("NOT_CERTIFIED", "NOT_CERTIFIED", "NOT_CERTIFIED"),
        )
        self.assertEqual(
            tuple(_status_map(rows, "ablate_B").values()),
            ("CERTIFIED", "NOT_CERTIFIED", "CERTIFIED"),
        )
        residual = _decision(rows, "ablate_B", "tau_cb")
        self.assertEqual(residual.failed_bindings, ("E",))
        self.assertEqual(residual.reason_codes, ("execution_noncompliance",))

    def test_all_three_registered_invariances_remain_certified(self) -> None:
        # Catches semantic comparisons that reject registered equivalence classes.
        source = self.clean.artifacts[0]
        commitment = self.clean.trust_root.commitments[0]
        controls = (
            _reseal(
                source,
                target_binding_sha256=commitment.allowed_target_binding_sha256[0],
            ),
            _reseal(
                source,
                scorer_weights=[
                    *[item.to_dict() for item in source.scorer_weights],
                    ScoreWeightV1(
                        schema_version="score-weight/v1",
                        key="zero_mass_shadow",
                        weight=0.0,
                    ).to_dict(),
                ],
            ),
            _reseal(
                source,
                protocol_version=commitment.allowed_protocol_versions[0],
            ),
        )
        for index, artifact in enumerate(controls):
            with self.subTest(control=index):
                rows = self._evaluate(artifact, f"control-{index}")
                self.assertEqual(
                    tuple(_status_map(rows, "full_estimand_gate").values()),
                    ("CERTIFIED", "CERTIFIED", "CERTIFIED"),
                )

    def test_input_order_is_irrelevant_and_duplicate_or_invalid_ids_fail_closed(
        self,
    ) -> None:
        # Catches positional output identity and ambiguous/missing public IDs.
        module = _module()
        left = _public_row(_case_id("left"), self.clean.artifacts[0])
        right = _public_row(_case_id("right"), self.clean.artifacts[1])
        self.assertEqual(
            module.evaluate_frozen_artifacts((left, right), self.root_bytes),
            module.evaluate_frozen_artifacts((right, left), self.root_bytes),
        )
        for rows in ((), (left, left)):
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                module.evaluate_frozen_artifacts(rows, self.root_bytes)
        with self.assertRaises(ValueError):
            module.evaluate_frozen_artifacts(
                (_public_row("not-a-digest", self.clean.artifacts[0]),),
                self.root_bytes,
            )
        missing_id = json.loads(left)
        del missing_id["case_id"]
        with self.assertRaises(ValueError):
            module.evaluate_frozen_artifacts(
                (_canonical_bytes(missing_id),), self.root_bytes
            )

    def test_malformed_or_noncanonical_bytes_and_unknown_units_are_rejected(
        self,
    ) -> None:
        # Catches permissive parsing and receipt evaluation without a commitment.
        module = _module()
        valid = _public_row(_case_id("valid"), self.clean.artifacts[0])
        for malformed in (b"{", b"[]", valid + b"\n", b"\xff"):
            with self.subTest(payload=malformed[:8]), self.assertRaises(ValueError):
                module.evaluate_frozen_artifacts((malformed,), self.root_bytes)
        unknown = _reseal(self.clean.artifacts[0], unit_id="syn-target-99-99")
        with self.assertRaises(ValueError):
            module.evaluate_frozen_artifacts(
                (_public_row(_case_id("unknown"), unknown),), self.root_bytes
            )


if __name__ == "__main__":
    unittest.main()
