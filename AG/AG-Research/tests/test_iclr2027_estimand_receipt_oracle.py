"""Independent oracle and exact benchmark-score tests."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
import unittest

from iclr2027.estimand_receipt_faults import (
    PublicMutationOracleV1,
    PublicMutationRowV1,
    apply_fault,
    materialize_public_census,
)
from iclr2027.estimand_receipt_generator import generate_clean_benchmark
from iclr2027.io import sha256_json


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


def _oracle_module():
    try:
        return importlib.import_module("iclr2027.estimand_receipt_oracle")
    except ModuleNotFoundError as exc:
        raise AssertionError("estimand receipt oracle must be implemented") from exc


def _evaluator_module():
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


def _case_id(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _mutation_row(clean, name: str, family: str, case_kind: str = "single"):
    source = clean.artifacts[0]
    partner = clean.artifacts[4] if family == "B" else source
    artifact = apply_fault(source, name, partner=partner)
    case_id = _case_id(f"{family}-{name}")
    oracle = PublicMutationOracleV1(
        schema_version="public-mutation-oracle/v1",
        case_id=case_id,
        case_kind=case_kind,
        mutation_names=(name,),
        families=(family,),
        partner_unit_ids=(partner.unit_id,) if family == "B" else (),
        expected_statuses=("NOT_CERTIFIED",) * 3,
    )
    return PublicMutationRowV1(
        schema_version="public-mutation-row/v1",
        case_id=case_id,
        artifact=artifact,
        artifact_sha256=sha256_json(artifact.to_dict()),
        oracle=oracle,
    )


def _output_row(module, case_id: str, config: str, estimand: str, status: str):
    return module.PublicEvaluatorDecisionV1.create(
        public_case_id=case_id,
        configuration=config,
        estimand=estimand,
        status=status,
        reason_codes=() if status == "CERTIFIED" else ("synthetic_abstention",),
        failed_bindings=(),
        bounds=None,
    )


class OracleTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = generate_clean_benchmark()

    def test_family_effects_are_derived_not_copied_from_expected_statuses(self) -> None:
        # Catches oracle truth copied from a caller-supplied expected-status vector.
        module = _oracle_module()
        row = _mutation_row(self.clean, "execution_omit_geometry", "E")
        decisions = module.oracle_reportability(
            self.clean.trust_root, self.clean.ledger[0], row
        )
        self.assertEqual(
            tuple(item.status for item in decisions),
            ("CERTIFIED", "NOT_CERTIFIED", "CERTIFIED"),
        )
        self.assertEqual(
            tuple(item.blocking_families for item in decisions),
            ((), ("E",), ()),
        )

    def test_clean_controls_and_selective_policy_truth_are_exact(self) -> None:
        # Catches applying E/P to every estimand or treating controls as harmful.
        module = _oracle_module()
        source = self.clean.artifacts[0]
        clean_id = _case_id("clean")
        clean_oracle = PublicMutationOracleV1(
            schema_version="public-mutation-oracle/v1",
            case_id=clean_id,
            case_kind="clean",
            mutation_names=(),
            families=(),
            partner_unit_ids=(),
            expected_statuses=("NOT_CERTIFIED",) * 3,
        )
        clean_row = PublicMutationRowV1(
            schema_version="public-mutation-row/v1",
            case_id=clean_id,
            artifact=source,
            artifact_sha256=sha256_json(source.to_dict()),
            oracle=clean_oracle,
        )
        self.assertEqual(
            tuple(
                item.status
                for item in module.oracle_reportability(
                    self.clean.trust_root, self.clean.ledger[0], clean_row
                )
            ),
            ("CERTIFIED", "CERTIFIED", "CERTIFIED"),
        )
        policy = _mutation_row(self.clean, "policy_menu_drift", "P")
        self.assertEqual(
            tuple(
                item.status
                for item in module.oracle_reportability(
                    self.clean.trust_root, self.clean.ledger[0], policy
                )
            ),
            ("CERTIFIED", "CERTIFIED", "NOT_CERTIFIED"),
        )

    def test_compound_truth_is_the_union_of_family_effects(self) -> None:
        # Catches last-family-wins or first-family-wins compound truth.
        module = _oracle_module()
        source = self.clean.artifacts[0]
        execution = apply_fault(source, "execution_omit_geometry", partner=source)
        compound = apply_fault(execution, "policy_menu_drift", partner=source)
        case_id = _case_id("E-P")
        oracle = PublicMutationOracleV1(
            schema_version="public-mutation-oracle/v1",
            case_id=case_id,
            case_kind="ordered_compound",
            mutation_names=("execution_omit_geometry", "policy_menu_drift"),
            families=("E", "P"),
            partner_unit_ids=(),
            expected_statuses=("CERTIFIED",) * 3,
        )
        row = PublicMutationRowV1(
            schema_version="public-mutation-row/v1",
            case_id=case_id,
            artifact=compound,
            artifact_sha256=sha256_json(compound.to_dict()),
            oracle=oracle,
        )
        decisions = module.oracle_reportability(
            self.clean.trust_root, self.clean.ledger[0], row
        )
        self.assertEqual(
            tuple(item.status for item in decisions),
            ("CERTIFIED", "NOT_CERTIFIED", "NOT_CERTIFIED"),
        )

    def test_oracle_rejects_a_construction_row_from_the_wrong_unit(self) -> None:
        # Catches positional joining of public mutations to the construction ledger.
        row = _mutation_row(self.clean, "execution_omit_geometry", "E")
        with self.assertRaises(ValueError):
            _oracle_module().oracle_reportability(
                self.clean.trust_root, self.clean.ledger[1], row
            )


class BenchmarkScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.oracle = _oracle_module()
        cls.evaluator = _evaluator_module()
        cls.case_ids = (_case_id("eligible"), _case_id("ineligible"))
        cls.oracle_rows = tuple(
            cls.oracle.OracleDecisionV1(
                schema_version="oracle-decision/v1",
                public_case_id=case_id,
                estimand=estimand,
                status="CERTIFIED" if case_index == 0 else "NOT_CERTIFIED",
                blocking_families=() if case_index == 0 else ("B",),
            )
            for case_index, case_id in enumerate(cls.case_ids)
            for estimand in ESTIMANDS
        )
        cls.oracle_bytes = cls.oracle.freeze_oracle_decisions(cls.oracle_rows)

    def _outputs(self):
        rows = []
        for config_index, config in enumerate(CONFIGURATIONS):
            for case_id in self.case_ids:
                for estimand in ESTIMANDS:
                    status = "CERTIFIED" if config_index == 0 else "NOT_CERTIFIED"
                    rows.append(
                        _output_row(self.evaluator, case_id, config, estimand, status)
                    )
        return tuple(rows)

    def test_integer_counts_and_exact_unsimplified_denominators_are_correct(
        self,
    ) -> None:
        # Catches float rates, denominator substitution, and misdefined counts.
        score = self.oracle.score_frozen_outputs(
            self.evaluator.freeze_evaluator_outputs(self._outputs()),
            self.oracle_bytes,
        )
        report_all = score.cell("completion_only", "tau_itt")
        self.assertEqual(
            (
                report_all.total,
                report_all.truth_certified,
                report_all.truth_not_certified,
                report_all.reported,
                report_all.false_reported,
                report_all.eligible_retained,
                report_all.abstained,
                report_all.exact_decisions,
            ),
            (2, 1, 1, 2, 1, 1, 0, 1),
        )
        self.assertEqual(
            report_all.false_reportability_rate.to_dict(),
            {"numerator": 1, "denominator": 1},
        )
        self.assertEqual(
            report_all.eligible_retention_rate.to_dict(),
            {"numerator": 1, "denominator": 1},
        )
        self.assertEqual(
            report_all.abstention_rate.to_dict(), {"numerator": 0, "denominator": 2}
        )
        self.assertEqual(
            report_all.conditional_report_accuracy.to_dict(),
            {"numerator": 1, "denominator": 2},
        )
        self.assertEqual(
            report_all.joint_decision_accuracy.to_dict(),
            {"numerator": 1, "denominator": 2},
        )

    def test_always_abstain_has_zero_retention_one_abstention_and_na_conditional(
        self,
    ) -> None:
        # Catches treating abstention as correct reporting or replacing zero denominators.
        score = self.oracle.score_frozen_outputs(
            self.evaluator.freeze_evaluator_outputs(self._outputs()),
            self.oracle_bytes,
        )
        cell = score.cell("hash_only", "tau_cb")
        self.assertEqual(
            (
                cell.reported,
                cell.false_reported,
                cell.eligible_retained,
                cell.abstained,
                cell.exact_decisions,
            ),
            (0, 0, 0, 2, 1),
        )
        self.assertEqual(
            cell.false_reportability_rate.to_dict(), {"numerator": 0, "denominator": 1}
        )
        self.assertEqual(
            cell.eligible_retention_rate.to_dict(), {"numerator": 0, "denominator": 1}
        )
        self.assertEqual(
            cell.abstention_rate.to_dict(), {"numerator": 2, "denominator": 2}
        )
        self.assertEqual(
            cell.conditional_report_accuracy.to_dict(),
            {"numerator": None, "denominator": None},
        )
        self.assertEqual(
            cell.joint_decision_accuracy.to_dict(), {"numerator": 1, "denominator": 2}
        )

    def test_scoring_joins_by_anonymous_id_not_output_order(self) -> None:
        # Catches positional joining of evaluator rows to private truth.
        outputs = self._outputs()
        standard = self.evaluator.freeze_evaluator_outputs(outputs)
        wrapper = json.loads(standard)
        wrapper["rows"].reverse()
        reversed_bytes = _canonical_bytes(wrapper)
        self.assertEqual(
            self.oracle.score_frozen_outputs(standard, self.oracle_bytes),
            self.oracle.score_frozen_outputs(reversed_bytes, self.oracle_bytes),
        )

    def test_missing_duplicate_extra_and_corrupt_output_ids_fail_closed(self) -> None:
        # Catches incomplete or ambiguous joins and unauthenticated decisions.
        outputs = self._outputs()
        valid = [item.to_dict() for item in outputs]
        first = outputs[0]
        extra = self.evaluator.PublicEvaluatorDecisionV1.create(
            public_case_id=_case_id("extra"),
            configuration=first.configuration,
            estimand=first.estimand,
            status=first.status,
            reason_codes=first.reason_codes,
            failed_bindings=first.failed_bindings,
            bounds=first.bounds,
        ).to_dict()
        corrupt = dict(valid[0])
        corrupt["canonical_decision_digest"] = "0" * 64
        bad_sets = (
            valid[:-1],
            [*valid, valid[0]],
            [extra, *valid[1:]],
            [corrupt, *valid[1:]],
        )
        for index, rows in enumerate(bad_sets):
            with self.subTest(index=index), self.assertRaises(ValueError):
                raw = _canonical_bytes(
                    {
                        "schema_version": "estimand-evaluator-outputs/v1",
                        "rows": rows,
                    }
                )
                self.oracle.score_frozen_outputs(raw, self.oracle_bytes)


class PublicCensusGateTests(unittest.TestCase):
    def test_exact_public_census_gate(self) -> None:
        oracle_module_name = "iclr2027.estimand_receipt_oracle"
        self.assertNotIn(oracle_module_name, sys.modules)

        clean = generate_clean_benchmark()
        census = materialize_public_census(clean)
        public_bytes = _canonical_bytes(census.public_to_dict())
        trust_root_bytes = _canonical_bytes(clean.trust_root.to_dict())
        public_artifact_bytes = tuple(
            _canonical_bytes(row.public_to_dict()) for row in census.rows
        )

        self.assertEqual(len(census.rows), 3_584)
        self.assertEqual(
            census.counts,
            {
                "clean": 64,
                "single": 1_408,
                "ordered_compound": 1_920,
                "invariance": 192,
            },
        )
        self.assertEqual(len(public_bytes), 6_352_742)
        self.assertEqual(
            hashlib.sha256(public_bytes).hexdigest(),
            "0ac7b9dfe4f724035d8cf52a95fa149806980983004e11a56cbff5e52129d81f",
        )
        self.assertEqual(len(trust_root_bytes), 102_133)
        self.assertEqual(
            hashlib.sha256(trust_root_bytes).hexdigest(),
            "6adfb9dc5398cfe58ce76fcc50c2c22894ace2d2e88843891253581fb7e847d8",
        )

        evaluator = _evaluator_module()
        self.assertNotIn(oracle_module_name, sys.modules)
        evaluator_rows = evaluator.evaluate_frozen_artifacts(
            public_artifact_bytes, trust_root_bytes
        )
        frozen_evaluator_bytes = evaluator.freeze_evaluator_outputs(evaluator_rows)
        self.assertNotIn(oracle_module_name, sys.modules)
        self.assertEqual(len(evaluator_rows), 3_584 * 11 * 3)

        oracle = _oracle_module()
        construction_by_unit = {row.unit_id: row for row in clean.ledger}
        oracle_rows = tuple(
            decision
            for mutation in census.rows
            for decision in oracle.oracle_reportability(
                clean.trust_root,
                construction_by_unit[mutation.artifact.unit_id],
                mutation,
            )
        )
        frozen_oracle_bytes = oracle.freeze_oracle_decisions(oracle_rows)
        score = oracle.score_frozen_outputs(
            frozen_evaluator_bytes, frozen_oracle_bytes
        )
        score_bytes = _canonical_bytes(score.to_dict())

        census_bytes = _canonical_bytes(census.to_dict())
        oracle_sidecar_bytes = _canonical_bytes(census.oracle_to_dict())
        self.assertEqual(len(census_bytes), 7_521_706)
        self.assertEqual(
            hashlib.sha256(census_bytes).hexdigest(),
            "750adf56b38853cbf76e56bff66577eb074924ca3d435ec3f2be65f198941b5f",
        )
        self.assertEqual(len(oracle_sidecar_bytes), 1_168_898)
        self.assertEqual(
            hashlib.sha256(oracle_sidecar_bytes).hexdigest(),
            "86b3c6d706020716c80fd767516bad3d716ee716ac0a93b5244f946350f1b0d0",
        )

        output_by_coordinate = {
            (row.public_case_id, row.configuration, row.estimand): row.status
            for row in evaluator_rows
        }
        truth_by_coordinate = {
            (row.public_case_id, row.estimand): row.status for row in oracle_rows
        }
        kind_by_case = {row.case_id: row.oracle.case_kind for row in census.rows}
        harmful_false_reportability = sum(
            output_by_coordinate[(case_id, "full_estimand_gate", estimand)]
            == "CERTIFIED"
            and status == "NOT_CERTIFIED"
            for (case_id, estimand), status in truth_by_coordinate.items()
            if kind_by_case[case_id] in ("single", "ordered_compound")
        )
        clean_invariance_false_nonreportability = sum(
            output_by_coordinate[(case_id, "full_estimand_gate", estimand)]
            != "CERTIFIED"
            for (case_id, estimand), status in truth_by_coordinate.items()
            if kind_by_case[case_id] in ("clean", "invariance")
            and status == "CERTIFIED"
        )
        self.assertEqual(harmful_false_reportability, 0)
        self.assertEqual(clean_invariance_false_nonreportability, 0)

        for estimand in ESTIMANDS:
            full = score.cell("full_estimand_gate", estimand)
            self.assertEqual(full.total, 3_584)
            self.assertEqual(full.exact_decisions, 3_584)
            self.assertEqual(full.false_reported, 0)
            self.assertEqual(full.eligible_retained, full.truth_certified)

        for configuration in CONFIGURATIONS[:4]:
            for estimand in ESTIMANDS:
                baseline = score.cell(configuration, estimand)
                self.assertEqual(baseline.total, 3_584)
                self.assertEqual(baseline.reported, 3_584)
                self.assertEqual(baseline.abstained, 0)
                self.assertEqual(
                    baseline.false_reported, baseline.truth_not_certified
                )
                self.assertEqual(
                    baseline.eligible_retained, baseline.truth_certified
                )
                self.assertEqual(baseline.exact_decisions, baseline.truth_certified)

        receipt = {
            "schema_version": "public-census-gate-receipt/v1",
            "cases": len(census.rows),
            "counts": census.counts,
            "census_sha256": hashlib.sha256(census_bytes).hexdigest(),
            "public_sha256": hashlib.sha256(public_bytes).hexdigest(),
            "trust_root_sha256": hashlib.sha256(trust_root_bytes).hexdigest(),
            "evaluator_rows": len(evaluator_rows),
            "evaluator_output_bytes": len(frozen_evaluator_bytes),
            "evaluator_output_sha256": hashlib.sha256(
                frozen_evaluator_bytes
            ).hexdigest(),
            "oracle_rows": len(oracle_rows),
            "oracle_decision_bytes": len(frozen_oracle_bytes),
            "oracle_decision_sha256": hashlib.sha256(
                frozen_oracle_bytes
            ).hexdigest(),
            "score_sha256": hashlib.sha256(score_bytes).hexdigest(),
            "harmful_false_reportability": harmful_false_reportability,
            "clean_invariance_false_nonreportability": (
                clean_invariance_false_nonreportability
            ),
            "cells": [cell.to_dict() for cell in score.cells],
        }
        print("PUBLIC_CENSUS_GATE_RECEIPT=" + _canonical_bytes(receipt).decode())


if __name__ == "__main__":
    unittest.main()
