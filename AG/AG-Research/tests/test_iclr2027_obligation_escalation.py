"""Granular synthetic-only tests for the Task 5A E1 contracts."""

from __future__ import annotations

from dataclasses import asdict, fields, FrozenInstanceError
import hashlib
import importlib
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SCHEMA = "ace.iclr2027.synthetic_task5_phase_a.v2.EscalationContract.v1"
IDENTITY_DOMAIN = "ace.iclr2027.synthetic_task5_phase_a.v2"
IDENTITY_SEED = hashlib.sha256(b"task-5-v2-e1-test-seed").hexdigest()


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _opaque_id(kind: str, ordinal: int) -> str:
    return "o5_" + hashlib.sha256(
        _canonical([IDENTITY_DOMAIN, IDENTITY_SEED, kind, ordinal])
    ).hexdigest()


def _ordered(records: list[object], hash_name: str) -> tuple[object, ...]:
    return tuple(sorted(records, key=lambda row: getattr(row, hash_name).encode("ascii")))


def _rebuild(record: object, /, **changes: object) -> object:
    values = {field.name: getattr(record, field.name) for field in fields(record)}
    values.pop("synthetic_only")
    values.pop(tuple(record.__dataclass_fields__)[-1])  # type: ignore[attr-defined]
    values.update(changes)
    return type(record).create(**values)


def _escalation_contract(subject: object) -> object:
    return subject.EscalationContract.create(
        schema_version=SCHEMA,
        base_adjustment_schema_sha256=_digest("base"),
        difficulty_feature_schema_sha256=_digest("difficulty"),
        site_fold_manifest_sha256=_digest("site-fold"),
        calibration_spec_sha256=_digest("calibration"),
        learner_class_sha256=_digest("learner-class"),
        learner_capacity_sha256=_digest("learner-capacity"),
        tie_rule_sha256=_digest("tie"),
        branch_outcome_schema_sha256=_digest("outcome"),
        analysis_code_sha256=_digest("analysis"),
    )


def _e1_e2_contract(
    oracle: object,
    *,
    packet_qualities: tuple[tuple[float, float], tuple[float, float]] = (
        (0.8, 0.6), (0.4, 0.5)
    ),
    solo_qualities: tuple[float, float] = (0.5, 0.5),
) -> object:
    """A complete hand-written pre-outcome roster with two fixed cells."""
    target = ("site-a", "case-a", "prefix-a")
    cells = ((0, 100), (1, 101))
    packet_ids = tuple(_opaque_id("packet", ordinal) for ordinal in (10, 11, 12))
    slot_ids = tuple(_opaque_id("slot", ordinal) for ordinal in (20, 21, 22))
    assignment_ids = tuple(_opaque_id("assignment", ordinal) for ordinal in range(30, 35))
    manifests = tuple(_digest(f"manifest:{index}") for index in range(3))
    entries = tuple(
        sorted(
            [
                *( ("assignment", ordinal, identifier) for ordinal, identifier in zip(range(30, 35), assignment_ids, strict=True) ),
                *( ("packet", ordinal, identifier) for ordinal, identifier in zip((10, 11, 12), packet_ids, strict=True) ),
                *( ("slot", ordinal, identifier) for ordinal, identifier in zip((20, 21, 22), slot_ids, strict=True) ),
            ],
            key=lambda row: (row[0].encode("ascii"), row[1]),
        )
    )
    registry = oracle.SyntheticOpaqueIdentityRegistryV2.create(
        derivation_seed_sha256=IDENTITY_SEED,
        entries=entries,
        packet_manifest_bindings=tuple(
            sorted(zip(packet_ids, manifests, strict=True), key=lambda row: row[0].encode("ascii"))
        ),
    )
    declared_packets = tuple(sorted(packet_ids[:2], key=lambda item: item.encode("ascii")))
    common_spec = _digest("common-synthesis")
    roster = oracle.SyntheticE1ActionRosterV2.create(
        site_ref=target[0], case_ref=target[1], prefix_ref=target[2],
        packet_ids=declared_packets, repeat_seed_cells=cells,
        common_synthesis_spec_sha256=common_spec,
        opaque_identity_registry_sha256=registry.registry_sha256,
    )
    assignments: list[object] = []
    executions: list[object] = []
    branches: list[object] = []
    solo_records: list[object] = []
    for packet_index, packet_id in enumerate(packet_ids[:2]):
        for cell_index, (repeat, seed) in enumerate(cells):
            assignment_ref = assignment_ids[packet_index * len(cells) + cell_index]
            assignment = oracle.SyntheticAssignmentCrossoverRecord.create(
                assignment_ref=assignment_ref, site_ref=target[0], case_ref=target[1], prefix_ref=target[2],
                repeat_index=repeat, seed=seed, assigned_opaque_slot_id=slot_ids[packet_index],
                assigned_actual_packet_id=packet_id, assigned_complete_bundle_manifest_sha256=manifests[packet_index],
                assignment_probability=0.5, assignment_probability_spec_sha256=_digest("assignment-probability"),
                randomization_nonce_sha256=_digest(f"nonce:{packet_index}:{cell_index}"),
                cyclic_crossover_plan_sha256=_digest("crossover"),
                complete_packet_roster_sha256=_digest("packet-roster"),
                immutable_target_roster_sha256=roster.roster_sha256,
            )
            execution = oracle.SyntheticExecutionConformanceRecord.create(
                assignment_ref=assignment_ref, site_ref=target[0], case_ref=target[1], prefix_ref=target[2],
                repeat_index=repeat, seed=seed, assigned_opaque_slot_id=slot_ids[packet_index],
                assigned_actual_packet_id=packet_id, actual_opaque_slot_id=slot_ids[packet_index],
                actual_packet_id=packet_id, actual_complete_bundle_manifest_sha256=manifests[packet_index],
                pre_call_execution_isolation_receipt_sha256=_digest(f"packet-isolation:{packet_index}:{cell_index}"),
                post_run_execution_usage_conformance_receipt_sha256=_digest(f"packet-conformance:{packet_index}:{cell_index}"),
                usage_ledger_sha256=_digest(f"packet-ledger:{packet_index}:{cell_index}"),
                compliance_status="verified",
            )
            branch = oracle.SyntheticTerminalBranch.create(
                site_ref=target[0], case_ref=target[1], prefix_ref=target[2],
                treatment_kind="capability_packet", opaque_slot_id=slot_ids[packet_index], actual_packet_id=packet_id,
                repeat_index=repeat, seed=seed, blind_terminal_quality=packet_qualities[packet_index][cell_index],
                complete_processed_tokens=10, latency_seconds=0.1, list_price_cost=0.0,
                execution_conformance_sha256=execution.post_run_execution_usage_conformance_receipt_sha256,
                direct_terminal_sha256=_digest(f"packet-terminal:{packet_index}:{cell_index}"),
            )
            assignments.append(assignment)
            executions.append(execution)
            branches.append(branch)
    for cell_index, (repeat, seed) in enumerate(cells):
        solo = oracle.SyntheticSoloExecutionConformanceV2.create(
            site_ref=target[0], case_ref=target[1], prefix_ref=target[2], repeat_index=repeat, seed=seed,
            common_synthesis_spec_sha256=common_spec,
            pre_call_execution_isolation_receipt_sha256=_digest(f"solo-isolation:{cell_index}"),
            post_run_execution_usage_conformance_receipt_sha256=_digest(f"solo-conformance:{cell_index}"),
            usage_ledger_sha256=_digest(f"solo-ledger:{cell_index}"), compliance_status="verified",
        )
        branch = oracle.SyntheticTerminalBranch.create(
            site_ref=target[0], case_ref=target[1], prefix_ref=target[2], treatment_kind="solo_synthesis",
            opaque_slot_id=None, actual_packet_id=None, repeat_index=repeat, seed=seed,
            blind_terminal_quality=solo_qualities[cell_index], complete_processed_tokens=5,
            latency_seconds=0.1, list_price_cost=0.0, execution_conformance_sha256=solo.record_sha256,
            direct_terminal_sha256=_digest(f"solo-terminal:{cell_index}"),
        )
        solo_records.append(solo)
        branches.append(branch)
    return oracle.E2MechanismContract.create(
        opaque_identity_registry=registry, e1_action_rosters=(roster,),
        solo_execution_records=_ordered(solo_records, "record_sha256"),
        auxiliary_control_plans=(), auxiliary_control_conformances=(), bindings=(),
        assignments=_ordered(assignments, "record_sha256"), pair_assignment_closures=(),
        support_balance_records=(), execution_records=_ordered(executions, "record_sha256"),
        terminal_branches=_ordered(branches, "record_sha256"), pairs=(),
        residual_absent_control_pairs=(), residual_absent_control_rosters=(),
        blind_outcome_schema_sha256=_digest("blind"), common_synthesis_spec_sha256=common_spec,
        analysis_code_sha256=_digest("e1-analysis"),
    )


class EscalationSchemaTests(unittest.TestCase):
    def test_exports_are_exact(self) -> None:
        from iclr2027 import obligation_escalation as subject

        self.assertEqual(subject.__all__, (
            "EscalationContract", "SyntheticEscalationLabel", "SyntheticCalibrationSummary",
            "build_synthetic_escalation_labels", "validate_synthetic_calibration",
        ))

    def test_records_are_explicit_frozen_slotted_and_exactly_typed(self) -> None:
        from iclr2027 import obligation_escalation as subject

        expected = {
            "EscalationContract": ("schema_version", "base_adjustment_schema_sha256", "difficulty_feature_schema_sha256", "site_fold_manifest_sha256", "calibration_spec_sha256", "learner_class_sha256", "learner_capacity_sha256", "tie_rule_sha256", "branch_outcome_schema_sha256", "analysis_code_sha256", "synthetic_only", "contract_sha256"),
            "SyntheticEscalationLabel": ("site_ref", "case_ref", "prefix_ref", "declared_packet_roster_sha256", "repeat_census_sha256", "escalation_contract_sha256", "label", "synthetic_only", "label_sha256"),
            "SyntheticCalibrationSummary": ("status", "site_fold_census_sha256", "label_census_sha256", "prediction_census_sha256", "escalation_contract_sha256", "calibration_value", "synthetic_only", "summary_sha256"),
        }
        for name, names in expected.items():
            cls = getattr(subject, name)
            self.assertEqual(tuple(field.name for field in fields(cls)), names)
            self.assertNotIn("__dict__", cls.__dict__)
            self.assertFalse(hasattr(object.__new__(cls), "__dict__"))
            self.assertFalse(any(field.type is object for field in fields(cls)))

    def test_escalation_records_validate_direct_constructor_json_hash_and_zero(self) -> None:
        from iclr2027 import obligation_escalation as subject

        contract = _escalation_contract(subject)
        self.assertEqual(type(contract).from_json(contract.canonical_json()), contract)
        with self.assertRaises(ValueError):
            type(contract)(**{**asdict(contract), "contract_sha256": "0" * 64})
        with self.assertRaises(ValueError):
            type(contract).from_json(contract.canonical_json()[:-1] + ',"schema_version":"duplicate"}')
        with self.assertRaises(FrozenInstanceError):
            contract.synthetic_only = False  # type: ignore[misc]
        summary = subject.SyntheticCalibrationSummary.create(
            status="synthetic_complete", site_fold_census_sha256=_digest("sites"),
            label_census_sha256=_digest("labels"), prediction_census_sha256=_digest("predictions"),
            escalation_contract_sha256=contract.contract_sha256,
            calibration_value=-0.0,
        )
        self.assertEqual(math.copysign(1.0, summary.calibration_value), 1.0)


class EscalationLabelClosureTests(unittest.TestCase):
    def _reject(self, subject: object, contract: object) -> None:
        with self.assertRaises(ValueError):
            subject.build_synthetic_escalation_labels(contract, _escalation_contract(subject))

    def test_complete_hand_written_roster_builds_fixed_label(self) -> None:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle

        contract = _e1_e2_contract(oracle)
        labels = subject.build_synthetic_escalation_labels(contract, _escalation_contract(subject))
        roster = contract.e1_action_rosters[0]
        self.assertEqual(len(labels), 1)
        self.assertTrue(labels[0].label)
        self.assertEqual(labels[0].declared_packet_roster_sha256, hashlib.sha256(_canonical(list(roster.packet_ids))).hexdigest())
        self.assertEqual(labels[0].repeat_census_sha256, hashlib.sha256(_canonical([[0, 100], [1, 101]])).hexdigest())
        self.assertEqual(labels[0].escalation_contract_sha256, _escalation_contract(subject).contract_sha256)

    def test_validated_task2_plan_only_auxiliary_legs_are_not_e1_extras(self) -> None:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle
        from tests import test_iclr2027_obligation_oracle as oracle_tests

        contract = oracle_tests._e1_owned_contract(oracle, shared_uniform_leg=False)
        self.assertEqual(oracle.evaluate_synthetic_e2(contract).status, "synthetic_complete")
        labels = subject.build_synthetic_escalation_labels(contract, _escalation_contract(subject))
        self.assertEqual(tuple(row.label for row in labels), (True,))

    def test_predeclared_shared_e1_auxiliary_leg_builds_one_label(self) -> None:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle
        from tests import test_iclr2027_obligation_oracle as oracle_tests

        contract = oracle_tests._e1_owned_contract(oracle, shared_uniform_leg=True)
        self.assertEqual(oracle.evaluate_synthetic_e2(contract).status, "synthetic_complete")
        self.assertEqual(len(subject.build_synthetic_escalation_labels(contract, _escalation_contract(subject))), 1)

    def test_removed_declared_packet_is_not_reconstructed_from_survivors(self) -> None:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle

        contract = _e1_e2_contract(oracle)
        removed = contract.e1_action_rosters[0].packet_ids[1]
        altered = _rebuild(
            contract,
            assignments=_ordered([row for row in contract.assignments if row.assigned_actual_packet_id != removed], "record_sha256"),
            execution_records=_ordered([row for row in contract.execution_records if row.actual_packet_id != removed], "record_sha256"),
            terminal_branches=_ordered([row for row in contract.terminal_branches if row.actual_packet_id != removed], "record_sha256"),
        )
        self._reject(subject, altered)

    def test_missing_or_extra_declared_packet_cell_rejects_before_label(self) -> None:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle

        contract = _e1_e2_contract(oracle)
        roster = contract.e1_action_rosters[0]
        declared_extra_cell = _rebuild(roster, repeat_seed_cells=((0, 100), (1, 101), (2, 102)))
        missing = _rebuild(contract, e1_action_rosters=(declared_extra_cell,))
        extra_cell = (2, 102)
        assignments = list(contract.assignments)
        executions = list(contract.execution_records)
        branches = list(contract.terminal_branches)
        for packet_id in roster.packet_ids:
            assignment = next(row for row in contract.assignments if row.assigned_actual_packet_id == packet_id)
            execution = next(row for row in contract.execution_records if row.actual_packet_id == packet_id)
            branch = next(row for row in contract.terminal_branches if row.actual_packet_id == packet_id)
            extra_assignment = _rebuild(
                assignment, repeat_index=extra_cell[0], seed=extra_cell[1],
                randomization_nonce_sha256=_digest(f"extra-assignment:{packet_id}"),
            )
            extra_execution = _rebuild(
                execution, repeat_index=extra_cell[0], seed=extra_cell[1],
                pre_call_execution_isolation_receipt_sha256=_digest(f"extra-isolation:{packet_id}"),
                post_run_execution_usage_conformance_receipt_sha256=_digest(f"extra-conformance:{packet_id}"),
                usage_ledger_sha256=_digest(f"extra-ledger:{packet_id}"),
            )
            assignments.append(extra_assignment)
            executions.append(extra_execution)
            branches.append(_rebuild(
                branch, repeat_index=extra_cell[0], seed=extra_cell[1],
                execution_conformance_sha256=extra_execution.post_run_execution_usage_conformance_receipt_sha256,
                direct_terminal_sha256=_digest(f"extra-terminal:{packet_id}"),
            ))
        solo = contract.solo_execution_records[0]
        extra_solo = _rebuild(
            solo, repeat_index=extra_cell[0], seed=extra_cell[1],
            pre_call_execution_isolation_receipt_sha256=_digest("extra-solo-isolation"),
            post_run_execution_usage_conformance_receipt_sha256=_digest("extra-solo-conformance"),
            usage_ledger_sha256=_digest("extra-solo-ledger"),
        )
        solo_terminal = next(row for row in contract.terminal_branches if row.treatment_kind == "solo_synthesis")
        branches.append(_rebuild(
            solo_terminal, repeat_index=extra_cell[0], seed=extra_cell[1],
            execution_conformance_sha256=extra_solo.record_sha256,
            direct_terminal_sha256=_digest("extra-solo-terminal"),
        ))
        added = _rebuild(
            contract, assignments=_ordered(assignments, "record_sha256"),
            execution_records=_ordered(executions, "record_sha256"),
            solo_execution_records=_ordered([*contract.solo_execution_records, extra_solo], "record_sha256"),
            terminal_branches=_ordered(branches, "record_sha256"),
        )
        for altered in (missing, added):
            with self.subTest(contract=altered.contract_sha256):
                self._reject(subject, altered)

    def test_solo_terminal_requires_matching_verified_conformance(self) -> None:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle

        contract = _e1_e2_contract(oracle)
        first = contract.solo_execution_records[0]
        mismatched = _rebuild(first, post_run_execution_usage_conformance_receipt_sha256=_digest("wrong-solo-receipt"))
        nonverified = _rebuild(first, compliance_status="noncompliant")
        for replacement in (mismatched, nonverified):
            altered = _rebuild(contract, solo_execution_records=_ordered([
                replacement if row.record_sha256 == first.record_sha256 else row
                for row in contract.solo_execution_records
            ], "record_sha256"))
            with self.subTest(replacement=replacement.record_sha256):
                self._reject(subject, altered)

    def test_solo_and_declared_packet_cell_sets_must_be_identical(self) -> None:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle

        contract = _e1_e2_contract(oracle)
        altered = _rebuild(contract, terminal_branches=_ordered([
            row for row in contract.terminal_branches
            if not (row.treatment_kind == "solo_synthesis" and (row.repeat_index, row.seed) == (1, 101))
        ], "record_sha256"))
        self._reject(subject, altered)

    def test_observed_undeclared_packet_cannot_change_survivor_label(self) -> None:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle

        contract = _e1_e2_contract(
            oracle, packet_qualities=((0.4, 0.4), (0.5, 0.5)), solo_qualities=(0.5, 0.5)
        )
        packet_id = _opaque_id("packet", 12)
        slot_id = _opaque_id("slot", 22)
        roster = contract.e1_action_rosters[0]
        assignments = list(contract.assignments)
        branches = list(contract.terminal_branches)
        executions = list(contract.execution_records)
        for cell_index, (repeat, seed) in enumerate(((0, 100),)):
            assignment = oracle.SyntheticAssignmentCrossoverRecord.create(
                assignment_ref=_opaque_id("assignment", 34), site_ref="site-a", case_ref="case-a", prefix_ref="prefix-a",
                repeat_index=repeat, seed=seed, assigned_opaque_slot_id=slot_id,
                assigned_actual_packet_id=packet_id, assigned_complete_bundle_manifest_sha256=_digest("manifest:2"),
                assignment_probability=0.5, assignment_probability_spec_sha256=_digest("undeclared-probability"),
                randomization_nonce_sha256=_digest("undeclared-nonce"),
                cyclic_crossover_plan_sha256=_digest("undeclared-crossover"),
                complete_packet_roster_sha256=_digest("undeclared-roster"),
                immutable_target_roster_sha256=roster.roster_sha256,
            )
            execution = oracle.SyntheticExecutionConformanceRecord.create(
                assignment_ref=_opaque_id("assignment", 34), site_ref="site-a", case_ref="case-a", prefix_ref="prefix-a",
                repeat_index=repeat, seed=seed, assigned_opaque_slot_id=slot_id, assigned_actual_packet_id=packet_id,
                actual_opaque_slot_id=slot_id, actual_packet_id=packet_id,
                actual_complete_bundle_manifest_sha256=_digest("manifest:2"),
                pre_call_execution_isolation_receipt_sha256=_digest(f"undeclared-isolation:{cell_index}"),
                post_run_execution_usage_conformance_receipt_sha256=_digest(f"undeclared-conformance:{cell_index}"),
                usage_ledger_sha256=_digest(f"undeclared-ledger:{cell_index}"), compliance_status="verified",
            )
            assignments.append(assignment)
            executions.append(execution)
            branches.append(oracle.SyntheticTerminalBranch.create(
                site_ref="site-a", case_ref="case-a", prefix_ref="prefix-a", treatment_kind="capability_packet",
                opaque_slot_id=slot_id, actual_packet_id=packet_id, repeat_index=repeat, seed=seed,
                blind_terminal_quality=0.9, complete_processed_tokens=10, latency_seconds=0.1, list_price_cost=0.0,
                execution_conformance_sha256=execution.post_run_execution_usage_conformance_receipt_sha256,
                direct_terminal_sha256=_digest(f"undeclared-terminal:{cell_index}"),
            ))
        altered = _rebuild(contract, assignments=_ordered(assignments, "record_sha256"), execution_records=_ordered(executions, "record_sha256"), terminal_branches=_ordered(branches, "record_sha256"))
        self._reject(subject, altered)

    def test_foreign_target_packet_or_terminal_rejects(self) -> None:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle

        contract = _e1_e2_contract(oracle)
        foreign_case = "case-foreign"
        solo_records = [
            _rebuild(row, case_ref=foreign_case)
            for row in contract.solo_execution_records
        ]
        solo_by_cell = {(row.repeat_index, row.seed): row for row in solo_records}
        altered = _rebuild(
            contract,
            assignments=_ordered([_rebuild(row, case_ref=foreign_case) for row in contract.assignments], "record_sha256"),
            execution_records=_ordered([_rebuild(row, case_ref=foreign_case) for row in contract.execution_records], "record_sha256"),
            solo_execution_records=_ordered(solo_records, "record_sha256"),
            terminal_branches=_ordered([
                _rebuild(
                    row, case_ref=foreign_case,
                    execution_conformance_sha256=(
                        solo_by_cell[(row.repeat_index, row.seed)].record_sha256
                        if row.treatment_kind == "solo_synthesis" else row.execution_conformance_sha256
                    ),
                )
                for row in contract.terminal_branches
            ], "record_sha256"),
        )
        self._reject(subject, altered)

    def test_nonverified_packet_execution_rejects_label(self) -> None:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle

        contract = _e1_e2_contract(oracle)
        first = contract.execution_records[0]
        bad = _rebuild(first, compliance_status="noncompliant")
        altered = _rebuild(contract, execution_records=_ordered([
            bad if row.record_sha256 == first.record_sha256 else row
            for row in contract.execution_records
        ], "record_sha256"))
        self._reject(subject, altered)


class CalibrationTests(unittest.TestCase):
    def _labels(self) -> tuple[object, object, tuple[object, ...]]:
        from iclr2027 import obligation_escalation as subject
        from iclr2027 import obligation_oracle as oracle

        contract = _escalation_contract(subject)
        label = subject.build_synthetic_escalation_labels(_e1_e2_contract(oracle), contract)[0]
        companion = subject.SyntheticEscalationLabel.create(
            site_ref="site-b", case_ref="case-b", prefix_ref="prefix-b",
            declared_packet_roster_sha256=_digest("companion-roster"), repeat_census_sha256=_digest("companion-cells"),
            escalation_contract_sha256=contract.contract_sha256,
            label=False,
        )
        return subject, contract, (label, companion)

    def test_toy_calibration_is_hand_derived(self) -> None:
        subject, contract, labels = self._labels()
        predictions = tuple((row.label_sha256, row.site_ref, 0.8 if row.label else 0.2) for row in labels)
        summary = subject.validate_synthetic_calibration(labels, predictions, contract)
        self.assertEqual(summary.status, "synthetic_complete")
        self.assertAlmostEqual(summary.calibration_value, 0.04)
        self.assertEqual(summary.escalation_contract_sha256, contract.contract_sha256)
        self.assertEqual(
            summary.site_fold_census_sha256,
            hashlib.sha256(_canonical([["site-a", 1], ["site-b", 1]])).hexdigest(),
        )

    def test_calibration_requires_exact_prediction_closure_and_site_identity(self) -> None:
        subject, contract, labels = self._labels()
        valid = tuple((row.label_sha256, row.site_ref, 0.5) for row in labels)
        cases = (valid[:-1], valid + (valid[0],), ((valid[0][0], "site-foreign", 0.5), valid[1]), ((valid[0][0], valid[0][1], 1.1), valid[1]))
        for predictions in cases:
            with self.subTest(predictions=predictions), self.assertRaises(ValueError):
                subject.validate_synthetic_calibration(labels, predictions, contract)

    def test_calibration_rejects_mixed_or_swapped_escalation_contract_binding(self) -> None:
        subject, contract, labels = self._labels()
        swapped_contract = subject.EscalationContract.create(
            schema_version=SCHEMA,
            base_adjustment_schema_sha256=_digest("base-swapped"),
            difficulty_feature_schema_sha256=_digest("difficulty-swapped"),
            site_fold_manifest_sha256=_digest("site-fold-swapped"),
            calibration_spec_sha256=_digest("calibration-swapped"),
            learner_class_sha256=_digest("learner-class-swapped"),
            learner_capacity_sha256=_digest("learner-capacity-swapped"),
            tie_rule_sha256=_digest("tie-swapped"),
            branch_outcome_schema_sha256=_digest("outcome-swapped"),
            analysis_code_sha256=_digest("analysis-swapped"),
        )
        predictions = tuple((row.label_sha256, row.site_ref, 0.5) for row in labels)
        forged = _rebuild(labels[0], escalation_contract_sha256=swapped_contract.contract_sha256)
        with self.assertRaises(ValueError):
            subject.validate_synthetic_calibration((forged, labels[1]), predictions, contract)
        with self.assertRaises(ValueError):
            subject.validate_synthetic_calibration(labels, predictions, swapped_contract)

    def test_single_site_or_single_class_is_non_estimable_with_none(self) -> None:
        subject, contract, labels = self._labels()
        one_site = labels[:1]
        summary = subject.validate_synthetic_calibration(one_site, ((one_site[0].label_sha256, one_site[0].site_ref, 0.5),), contract)
        self.assertEqual(summary.status, "non_estimable_support")
        self.assertIsNone(summary.calibration_value)

    def test_summary_status_dependent_none_rules_validate_directly(self) -> None:
        from iclr2027 import obligation_escalation as subject

        contract = _escalation_contract(subject)
        common = dict(site_fold_census_sha256=_digest("sites"), label_census_sha256=_digest("labels"), prediction_census_sha256=_digest("predictions"), escalation_contract_sha256=contract.contract_sha256)
        with self.assertRaises(ValueError):
            subject.SyntheticCalibrationSummary.create(status="non_estimable_support", calibration_value=0.0, **common)
        with self.assertRaises((TypeError, ValueError)):
            subject.SyntheticCalibrationSummary.create(status="synthetic_complete", calibration_value=None, **common)


class EscalationPhaseBoundaryTests(unittest.TestCase):
    def test_escalation_cli_help_and_all_source_flags_stop_before_io(self) -> None:
        cli = importlib.import_module("analyze_iclr2027_obligation_escalation")
        self.assertEqual(cli.main([]), 0)
        for flag in ("--inventory", "--source", "--data", "--output"):
            with self.subTest(flag=flag), mock.patch.object(Path, "exists", side_effect=AssertionError("I/O")):
                with self.assertRaisesRegex(SystemExit, "^NEEDS_CONTEXT$"):
                    cli.main([flag, str(Path(tempfile.gettempdir()) / "must-not-open")])


if __name__ == "__main__":
    unittest.main()
