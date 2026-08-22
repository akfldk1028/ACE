from __future__ import annotations

import ast
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError, fields
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

from iclr2027 import precall_design_lock as lock_module
from iclr2027.precall_design_lock import (
    ArchitectureE1E2E3PreCallDesignLockV3,
    CurrentArchitectureInventoryFactV3,
    GateCheckResultV3,
    NeedsContextError,
    PreCallDesignLockError,
    PreCallDesignLockResultV3,
    require_authenticated_pre_call_authority,
    validate_authenticated_pre_call_design_lock,
    validate_synthetic_pre_call_design_lock,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "validate_iclr2027_precall_design_lock.py"
ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
MEMORY_HASH = "e774381bbde93a9540821a6375ccbee55ec724d801e91b10efab2bcdc91083b6"
DOWNSTREAM_MEMORY_HASH = (
    "836209102b83fc483bad56add0d963b65f32e678b658a947fed2e7111cc64309"
)
SYNTHETIC_IMPLEMENTATION_HASH = (
    "0c0438afe17dd742bba0450eb04f8ebef4e7ffe6e9ac78246a9bfea575660d3e"
)
CURRENT_INVENTORY_FILE_HASH = (
    "064bc6f6dba3d9e44ecb9518646a6ddd5352be8e0d6a53d223f8cecef006d19f"
)
CURRENT_INVENTORY_SELF_HASH = (
    "908972321d6edde49c837a0b0b8f21b7d9284b60cc4b1c5ca74e8af6cc944e75"
)
CURRENT_RECEIPT_FILE_HASH = (
    "9aa8c51b0e9abea0f7dc748fb8ae201e353206c838935b4b00e4083e9c2ac6cc"
)
CURRENT_RECEIPT_SELF_HASH = (
    "beda2758428df3e2ad1bcd153b907e48898a33b665f64b04e8e39a8dd313e669"
)
CURRENT_SOURCE_MAP_HASH = (
    "745c80d835521377723677e47105f0e31854efa7549ab45d7ec824d78228b6b7"
)

EXPECTED_CURRENT_REASONS = {
    "architecture_audit_split_not_met",
    "architecture_branch_coverage_incomplete",
    "architecture_cluster_floor_not_met",
    "architecture_focal_split_not_met",
    "architecture_target_unit_floor_not_met",
    "cost_ceiling_exceeded_or_missing",
    "e1_protocol_incomplete",
    "e2_protocol_incomplete",
    "e3_parity_protocol_incomplete",
    "external_anchor_missing",
    "grid_not_signed_before_simulation",
    "holm_joint_scenario_census_incomplete",
    "holm_strong_fwer_theorem_or_applicability_invalid",
    "jci_floor_missing_or_not_replayable",
    "model_rate_unresolved_or_stale",
    "operation_catalog_incomplete",
    "scenario_grid_incomplete",
    "secondary_contrast_value_missing_or_posthoc",
    "simulation_authorization_or_completion_invalid",
    "substantive_values_missing_or_posthoc",
    "synthetic_authority_cannot_pass",
    "time_ceiling_exceeded_or_missing",
    "tool_rate_unresolved_or_stale",
    "typed_unit_roster_missing",
}


def _fact() -> CurrentArchitectureInventoryFactV3:
    return CurrentArchitectureInventoryFactV3.create(
        gate0_inventory_file_sha256=CURRENT_INVENTORY_FILE_HASH,
        gate0_inventory_self_sha256=CURRENT_INVENTORY_SELF_HASH,
        gate0_publication_receipt_file_sha256=CURRENT_RECEIPT_FILE_HASH,
        gate0_publication_receipt_self_sha256=CURRENT_RECEIPT_SELF_HASH,
        gate0_source_map_sha256=CURRENT_SOURCE_MAP_HASH,
        authenticated_cluster_count=5,
        historical_case_count=30,
        historical_run_count=450,
        prefix_count=1524,
        standardized_action_covered_count=0,
        standardized_action_required_count=6,
        typed_unit_roster_status="absent",
        typed_unit_count=None,
        source_memory_sha256=MEMORY_HASH,
    )


def _lock(
    fact: CurrentArchitectureInventoryFactV3 | None = None,
) -> ArchitectureE1E2E3PreCallDesignLockV3:
    return ArchitectureE1E2E3PreCallDesignLockV3.create(
        authority_mode="synthetic",
        current_inventory_fact=fact or _fact(),
        simulation_freeze_plan=None,
        external_anchor_receipt=None,
        simulation_run_authorization_receipt=None,
        simulation_run_completion_receipt=None,
        architecture_domain_evaluation=None,
        jci_domain_evaluation=None,
        joint_selected_operational_budget=None,
        primary_alpha=0.05,
        primary_interval_level=0.95,
        secondary_holm_fwer=0.05,
        implementation_code_sha256s=(SYNTHETIC_IMPLEMENTATION_HASH,),
    )


def _gate() -> GateCheckResultV3:
    return GateCheckResultV3.create(
        check_id="check",
        domain_id=None,
        candidate_ref=None,
        scenario_ref=None,
        effect_ref=None,
        fold_ref=None,
        predicate_id="predicate",
        comparison_operator="eq",
        expected_value=1,
        observed_value=0,
        passed=False,
        reason_codes=("external_anchor_missing",),
        authority_sha256s=(ZERO_HASH,),
    )


def _load_cli():
    spec = importlib.util.spec_from_file_location("task6_precall_cli", CLI_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("CLI import spec is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rehash_payload(payload: dict[str, object], hash_field: str) -> dict[str, object]:
    result = dict(payload)
    unsigned = {key: value for key, value in result.items() if key != hash_field}
    canonical = json.dumps(
        unsigned,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    result[hash_field] = hashlib.sha256(canonical).hexdigest()
    return result


def _forged_pass_result_payload() -> dict[str, object]:
    result = validate_synthetic_pre_call_design_lock(_lock())
    payload: dict[str, object] = result.to_dict()
    payload.update(
        authority_mode="authenticated",
        status="pass",
        reason_codes=["all_pre_call_checks_passed"],
        official_result_eligible=True,
        synthetic_only=False,
    )
    return _rehash_payload(payload, "result_sha256")


def _forged_passing_failed_gate_payload() -> dict[str, object]:
    payload: dict[str, object] = _gate().to_dict()
    payload.update(
        passed=True,
        reason_codes=["all_pre_call_checks_passed"],
    )
    return _rehash_payload(payload, "check_sha256")


def _fully_rehashed_foreign_current_result_payload() -> dict[str, object]:
    payload: dict[str, object] = validate_synthetic_pre_call_design_lock(
        _lock()
    ).to_dict()
    foreign_fact_sha256 = "e" * 64
    foreign_lock_sha256 = "f" * 64
    authority = [foreign_fact_sha256, foreign_lock_sha256]
    rebound_gates = []
    for gate in payload["gate_checks"]:
        rebound_gate = dict(gate)
        rebound_gate["authority_sha256s"] = authority
        rebound_gates.append(_rehash_payload(rebound_gate, "check_sha256"))
    payload["lock_sha256"] = foreign_lock_sha256
    payload["gate_checks"] = rebound_gates
    return _rehash_payload(payload, "result_sha256")


class TestPublicContract(unittest.TestCase):
    def test_exact_public_api_is_frozen(self) -> None:
        self.assertEqual(
            lock_module.__all__,
            (
                "PreCallDesignLockError",
                "NeedsContextError",
                "validate_synthetic_pre_call_design_lock",
                "validate_authenticated_pre_call_design_lock",
                "require_authenticated_pre_call_authority",
            ),
        )

    def test_public_records_are_frozen_and_slotted(self) -> None:
        fact = _fact()
        lock = _lock(fact)
        result = validate_synthetic_pre_call_design_lock(lock)
        for record in (fact, lock, result, result.gate_checks[0]):
            self.assertFalse(hasattr(record, "__dict__"))
            with self.assertRaises(FrozenInstanceError):
                record.schema_version = "changed"  # type: ignore[misc]

    def test_record_schema_versions_use_exact_v3_prefix(self) -> None:
        self.assertEqual(
            _fact().schema_version,
            "ace.iclr2027.precall_design_lock.v3.current_architecture_inventory_fact_v3",
        )
        self.assertEqual(
            _gate().schema_version,
            "ace.iclr2027.precall_design_lock.v3.gate_check_result_v3",
        )

    def test_gate_canonical_json_and_hash_match_hand_derived_literals(self) -> None:
        gate = _gate()
        expected = (
            '{"authority_sha256s":["0000000000000000000000000000000000000000000000000000000000000000"],'
            '"candidate_ref":null,"check_id":"check",'
            '"check_sha256":"40434ec8d54cbc5b66591bb24252a30b9861fc81cbe491775abc6352d3ae951f",'
            '"comparison_operator":"eq",'
            '"domain_id":null,"effect_ref":null,"expected_value":1,"fold_ref":null,'
            '"observed_value":0,"passed":false,"predicate_id":"predicate",'
            '"reason_codes":["external_anchor_missing"],"scenario_ref":null,'
            '"schema_version":"ace.iclr2027.precall_design_lock.v3.gate_check_result_v3"}'
        )
        self.assertEqual(gate.canonical_json(), expected)
        self.assertEqual(
            gate.check_sha256,
            "40434ec8d54cbc5b66591bb24252a30b9861fc81cbe491775abc6352d3ae951f",
        )


class TestStrictCanonicalRecords(unittest.TestCase):
    def test_from_json_roundtrip_is_exact(self) -> None:
        gate = _gate()
        self.assertEqual(
            GateCheckResultV3.from_json(gate.canonical_json()),
            gate,
        )

    def test_duplicate_json_key_rejects(self) -> None:
        raw = _gate().canonical_json().replace(
            '"check_id":"check"',
            '"check_id":"check","check_id":"check"',
            1,
        )
        with self.assertRaisesRegex(PreCallDesignLockError, "duplicate"):
            GateCheckResultV3.from_json(raw)

    def test_noncanonical_json_whitespace_rejects(self) -> None:
        with self.assertRaisesRegex(PreCallDesignLockError, "canonical"):
            GateCheckResultV3.from_json(" " + _gate().canonical_json())

    def test_nonfinite_json_rejects(self) -> None:
        raw = _gate().canonical_json().replace('"observed_value":0', '"observed_value":NaN')
        with self.assertRaisesRegex(PreCallDesignLockError, "finite"):
            GateCheckResultV3.from_json(raw)

    def test_recursive_raw_negative_zero_rejects(self) -> None:
        raw = _gate().canonical_json().replace('"observed_value":0', '"observed_value":[1,-0.0]')
        with self.assertRaisesRegex(PreCallDesignLockError, "signed zero"):
            GateCheckResultV3.from_json(raw)

    def test_direct_float_negative_zero_normalizes_positive(self) -> None:
        gate = GateCheckResultV3.create(
            check_id="zero",
            domain_id=None,
            candidate_ref=None,
            scenario_ref=None,
            effect_ref=None,
            fold_ref=None,
            predicate_id="zero",
            comparison_operator="eq",
            expected_value=-0.0,
            observed_value={"nested": [-0.0]},
            passed=False,
            reason_codes=("external_anchor_missing",),
            authority_sha256s=(ZERO_HASH,),
        )
        self.assertEqual(gate.expected_value, 0.0)
        self.assertEqual(gate.observed_value, {"nested": [0.0]})
        self.assertNotIn("-0.0", gate.canonical_json())

    def test_gate_arbitrary_json_arrays_roundtrip_without_type_drift(self) -> None:
        gate = GateCheckResultV3.create(
            check_id="array_roundtrip",
            domain_id=None,
            candidate_ref=None,
            scenario_ref=None,
            effect_ref=None,
            fold_ref=None,
            predicate_id="array_roundtrip",
            comparison_operator="eq",
            expected_value=[{"nested": [1, 2]}],
            observed_value=[{"nested": [1, 2]}],
            passed=True,
            reason_codes=("all_pre_call_checks_passed",),
            authority_sha256s=(ZERO_HASH,),
        )
        self.assertEqual(GateCheckResultV3.from_dict(gate.to_dict()), gate)
        self.assertEqual(GateCheckResultV3.from_json(gate.canonical_json()), gate)

    def test_gate_rejects_same_hash_tuple_array_ambiguity(self) -> None:
        with self.assertRaisesRegex(PreCallDesignLockError, "JSON-native"):
            GateCheckResultV3.create(
                check_id="ambiguous_array",
                domain_id=None,
                candidate_ref=None,
                scenario_ref=None,
                effect_ref=None,
                fold_ref=None,
                predicate_id="ambiguous_array",
                comparison_operator="eq",
                expected_value=(1,),
                observed_value=(1,),
                passed=True,
                reason_codes=("all_pre_call_checks_passed",),
                authority_sha256s=(ZERO_HASH,),
            )

    def test_gate_rejects_nested_tuple_inside_arbitrary_json_value(self) -> None:
        with self.assertRaisesRegex(PreCallDesignLockError, "JSON-native"):
            GateCheckResultV3.create(
                check_id="nested_ambiguous_array",
                domain_id=None,
                candidate_ref=None,
                scenario_ref=None,
                effect_ref=None,
                fold_ref=None,
                predicate_id="nested_ambiguous_array",
                comparison_operator="eq",
                expected_value={"nested": (1,)},
                observed_value={"nested": [1]},
                passed=False,
                reason_codes=("external_anchor_missing",),
                authority_sha256s=(ZERO_HASH,),
            )

    def test_gate_declared_tuple_fields_remain_exact_tuples(self) -> None:
        gate = _gate()
        self.assertIs(type(gate.reason_codes), tuple)
        self.assertIs(type(gate.authority_sha256s), tuple)

    def test_bool_as_inventory_count_rejects(self) -> None:
        values = _fact().to_dict()
        values.pop("fact_sha256")
        values.pop("schema_version")
        values.pop("synthetic_only")
        values["authenticated_cluster_count"] = True
        with self.assertRaisesRegex(TypeError, "native int"):
            CurrentArchitectureInventoryFactV3.create(**values)

    def test_missing_extra_and_non_string_dict_keys_reject(self) -> None:
        payload = _gate().to_dict()
        payload.pop("fold_ref")
        with self.assertRaisesRegex(PreCallDesignLockError, "missing or extra"):
            GateCheckResultV3.from_dict(payload)
        payload = _gate().to_dict()
        payload["extra"] = None
        with self.assertRaisesRegex(PreCallDesignLockError, "missing or extra"):
            GateCheckResultV3.from_dict(payload)
        payload = _gate().to_dict()
        payload[1] = None  # type: ignore[index]
        with self.assertRaisesRegex(TypeError, "string keys"):
            GateCheckResultV3.from_dict(payload)

    def test_self_hash_tampering_rejects(self) -> None:
        payload = _gate().to_dict()
        payload["observed_value"] = 1
        with self.assertRaisesRegex(PreCallDesignLockError, "self-hash"):
            GateCheckResultV3.from_dict(payload)

    def test_rehashed_failed_gate_cannot_claim_pass_via_direct_constructor(self) -> None:
        payload = _forged_passing_failed_gate_payload()
        payload["reason_codes"] = tuple(payload["reason_codes"])
        payload["authority_sha256s"] = tuple(payload["authority_sha256s"])
        with self.assertRaisesRegex(PreCallDesignLockError, "recomputed predicate"):
            GateCheckResultV3(**payload)

    def test_rehashed_failed_gate_cannot_claim_pass_via_from_dict(self) -> None:
        with self.assertRaisesRegex(PreCallDesignLockError, "recomputed predicate"):
            GateCheckResultV3.from_dict(_forged_passing_failed_gate_payload())

    def test_rehashed_failed_gate_cannot_claim_pass_via_from_json(self) -> None:
        payload = _forged_passing_failed_gate_payload()
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        with self.assertRaisesRegex(PreCallDesignLockError, "recomputed predicate"):
            GateCheckResultV3.from_json(raw)

    def test_fully_rehashed_result_cannot_rebind_current_lock_via_from_dict(self) -> None:
        with self.assertRaisesRegex(PreCallDesignLockError, "current lock binding"):
            PreCallDesignLockResultV3.from_dict(
                _fully_rehashed_foreign_current_result_payload()
            )

    def test_fully_rehashed_result_cannot_rebind_current_lock_via_from_json(self) -> None:
        raw = json.dumps(
            _fully_rehashed_foreign_current_result_payload(),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        with self.assertRaisesRegex(PreCallDesignLockError, "current lock binding"):
            PreCallDesignLockResultV3.from_json(raw)

    def test_gate_rejects_false_claim_when_typed_predicate_is_true(self) -> None:
        with self.assertRaisesRegex(PreCallDesignLockError, "recomputed predicate"):
            GateCheckResultV3.create(
                check_id="true_predicate",
                domain_id=None,
                candidate_ref=None,
                scenario_ref=None,
                effect_ref=None,
                fold_ref=None,
                predicate_id="true_predicate",
                comparison_operator="eq",
                expected_value=1,
                observed_value=1,
                passed=False,
                reason_codes=("external_anchor_missing",),
                authority_sha256s=(ZERO_HASH,),
            )

    def test_gate_comparison_does_not_treat_bool_as_integer(self) -> None:
        with self.assertRaisesRegex(PreCallDesignLockError, "recomputed predicate"):
            GateCheckResultV3.create(
                check_id="typed_predicate",
                domain_id=None,
                candidate_ref=None,
                scenario_ref=None,
                effect_ref=None,
                fold_ref=None,
                predicate_id="typed_predicate",
                comparison_operator="eq",
                expected_value=1,
                observed_value=True,
                passed=True,
                reason_codes=("all_pre_call_checks_passed",),
                authority_sha256s=(ZERO_HASH,),
            )

    def test_bytes_must_be_utf8_without_bom(self) -> None:
        with self.assertRaisesRegex(PreCallDesignLockError, "UTF-8"):
            GateCheckResultV3.from_json(b"\xff")
        with self.assertRaisesRegex(PreCallDesignLockError, "BOM"):
            GateCheckResultV3.from_json("\ufeff" + _gate().canonical_json())


class TestCurrentSyntheticNoGo(unittest.TestCase):
    def test_current_continuity_values_are_preserved(self) -> None:
        result = validate_synthetic_pre_call_design_lock(_lock())
        self.assertEqual(result.architecture_cluster_count, 5)
        self.assertIsNone(result.architecture_target_unit_count)
        self.assertEqual(_fact().historical_case_count, 30)
        self.assertEqual(_fact().historical_run_count, 450)
        self.assertEqual(_fact().prefix_count, 1524)
        self.assertEqual(_fact().standardized_action_covered_count, 0)
        self.assertEqual(_fact().standardized_action_required_count, 6)
        self.assertEqual(_fact().source_memory_sha256, MEMORY_HASH)

    def test_downstream_memory_cannot_rebind_frozen_upstream_continuity(self) -> None:
        values = _fact().to_dict()
        for field in ("schema_version", "synthetic_only", "fact_sha256"):
            values.pop(field)
        values["source_memory_sha256"] = DOWNSTREAM_MEMORY_HASH
        downstream = CurrentArchitectureInventoryFactV3.create(**values)
        with self.assertRaisesRegex(PreCallDesignLockError, "current continuity"):
            validate_synthetic_pre_call_design_lock(_lock(downstream))

    def test_current_fixture_is_deterministic_no_go(self) -> None:
        first = validate_synthetic_pre_call_design_lock(_lock())
        second = validate_synthetic_pre_call_design_lock(_lock())
        self.assertEqual(first, second)
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertEqual(first.status, "no_go")
        self.assertFalse(first.official_result_eligible)
        self.assertTrue(first.synthetic_only)

    def test_rehashed_pass_result_rejects_via_direct_constructor(self) -> None:
        payload = _forged_pass_result_payload()
        baseline = validate_synthetic_pre_call_design_lock(_lock())
        payload["reason_codes"] = tuple(payload["reason_codes"])
        payload["gate_checks"] = baseline.gate_checks
        with self.assertRaisesRegex(PreCallDesignLockError, "synthetic-only"):
            PreCallDesignLockResultV3(**payload)

    def test_rehashed_pass_result_rejects_via_from_dict(self) -> None:
        with self.assertRaisesRegex(PreCallDesignLockError, "synthetic-only"):
            PreCallDesignLockResultV3.from_dict(_forged_pass_result_payload())

    def test_rehashed_pass_result_rejects_via_from_json(self) -> None:
        payload = _forged_pass_result_payload()
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        with self.assertRaisesRegex(PreCallDesignLockError, "synthetic-only"):
            PreCallDesignLockResultV3.from_json(raw)

    def test_current_failure_reasons_are_complete_sorted_and_unique(self) -> None:
        result = validate_synthetic_pre_call_design_lock(_lock())
        self.assertEqual(set(result.reason_codes), EXPECTED_CURRENT_REASONS)
        self.assertEqual(
            result.reason_codes,
            tuple(sorted(result.reason_codes, key=lambda value: value.encode("utf-8"))),
        )
        self.assertEqual(len(result.reason_codes), len(set(result.reason_codes)))

    def test_each_current_gate_is_failed_and_receipt_bound(self) -> None:
        lock = _lock()
        result = validate_synthetic_pre_call_design_lock(lock)
        self.assertEqual(
            {reason for gate in result.gate_checks for reason in gate.reason_codes},
            EXPECTED_CURRENT_REASONS,
        )
        for gate in result.gate_checks:
            self.assertFalse(gate.passed)
            self.assertTrue(gate.authority_sha256s)
            self.assertIn(lock.lock_sha256, gate.authority_sha256s)

    def test_historical_cases_are_never_substituted_for_target_units(self) -> None:
        result = validate_synthetic_pre_call_design_lock(_lock())
        target_gate = next(
            gate
            for gate in result.gate_checks
            if "architecture_target_unit_floor_not_met" in gate.reason_codes
        )
        self.assertEqual(target_gate.expected_value, 64)
        self.assertIsNone(target_gate.observed_value)
        self.assertNotEqual(target_gate.observed_value, 30)

    def test_missing_numerics_are_none_never_zero(self) -> None:
        result = validate_synthetic_pre_call_design_lock(_lock())
        for field in (
            "architecture_target_unit_count",
            "jci_cluster_count",
            "jci_target_unit_count",
            "architecture_selected_prefix_cell_count",
            "jci_selected_prefix_cell_count",
            "architecture_terminal_count",
            "architecture_branch_generation_call_count",
            "jci_terminal_count",
            "jci_branch_generation_call_count",
            "recomputed_operation_count",
            "recomputed_worst_case_attempts",
            "recomputed_model_cost",
            "recomputed_tool_cost",
            "recomputed_total_cost",
            "recomputed_worst_case_wall_seconds",
        ):
            self.assertIsNone(getattr(result, field), field)

    def test_root_roundtrip_revalidates_nested_exact_types(self) -> None:
        lock = _lock()
        parsed = ArchitectureE1E2E3PreCallDesignLockV3.from_json(lock.canonical_json())
        self.assertEqual(parsed, lock)
        payload = lock.to_dict()
        payload["current_inventory_fact"] = _gate().to_dict()
        with self.assertRaises(PreCallDesignLockError):
            ArchitectureE1E2E3PreCallDesignLockV3.from_dict(payload)

    def test_synthetic_root_rejects_source_authority_fields(self) -> None:
        values = _lock().to_dict()
        for field in ("schema_version", "synthetic_only", "lock_sha256"):
            values.pop(field)
        for field in (
            "simulation_freeze_plan",
            "external_anchor_receipt",
            "simulation_run_authorization_receipt",
            "simulation_run_completion_receipt",
            "architecture_domain_evaluation",
            "jci_domain_evaluation",
            "joint_selected_operational_budget",
        ):
            altered = dict(values)
            altered[field] = {"forged": True}
            with self.subTest(field=field), self.assertRaises(PreCallDesignLockError):
                ArchitectureE1E2E3PreCallDesignLockV3.create(**altered)

    def test_synthetic_root_rejects_authenticated_mode_and_pass_constants(self) -> None:
        values = _lock().to_dict()
        for field in ("schema_version", "synthetic_only", "lock_sha256"):
            values.pop(field)
        for field, value in (
            ("authority_mode", "authenticated"),
            ("primary_alpha", 0.10),
            ("primary_interval_level", 0.90),
            ("secondary_holm_fwer", 0.10),
            ("implementation_code_sha256s", (ZERO_HASH,)),
        ):
            altered = dict(values)
            altered[field] = value
            with self.subTest(field=field), self.assertRaises(PreCallDesignLockError):
                ArchitectureE1E2E3PreCallDesignLockV3.create(**altered)

    def test_synthetic_validator_rejects_foreign_subclass_before_use(self) -> None:
        class ForeignLock(ArchitectureE1E2E3PreCallDesignLockV3):
            pass

        lock = _lock()
        foreign = ForeignLock(
            **{field.name: getattr(lock, field.name) for field in fields(lock)}
        )
        with self.assertRaisesRegex(TypeError, "exact"):
            validate_synthetic_pre_call_design_lock(foreign)

    def test_root_create_rejects_nested_subclass_before_serialization(self) -> None:
        calls = 0

        class ForeignFact(CurrentArchitectureInventoryFactV3):
            def to_dict(self):
                nonlocal calls
                calls += 1
                return super().to_dict()

        fact = _fact()
        foreign = ForeignFact(
            **{field.name: getattr(fact, field.name) for field in fields(fact)}
        )
        values = _lock().to_dict()
        for field in ("schema_version", "synthetic_only", "lock_sha256"):
            values.pop(field)
        values["current_inventory_fact"] = foreign
        with self.assertRaisesRegex(PreCallDesignLockError, "exact record type"):
            ArchitectureE1E2E3PreCallDesignLockV3.create(**values)
        self.assertEqual(calls, 0)

    def test_tampered_current_fact_cannot_upgrade_synthetic_fixture(self) -> None:
        fact_values = _fact().to_dict()
        for field in ("schema_version", "synthetic_only", "fact_sha256"):
            fact_values.pop(field)
        fact_values["authenticated_cluster_count"] = 8
        forged = CurrentArchitectureInventoryFactV3.create(**fact_values)
        with self.assertRaisesRegex(PreCallDesignLockError, "current continuity"):
            validate_synthetic_pre_call_design_lock(_lock(forged))

    def test_rehashed_result_rejects_wrong_current_top_level_closure(self) -> None:
        baseline = validate_synthetic_pre_call_design_lock(_lock())
        cases = (
            ("architecture_cluster_count", 6, "current result closure"),
            ("architecture_target_unit_count", 64, "current result closure"),
            (
                "architecture_selected_candidate_ref",
                "forged_candidate",
                "current result closure",
            ),
            ("recomputed_total_cost", 0.0, "current result closure"),
            ("lock_sha256", "f" * 64, "current lock binding"),
        )
        for field_name, value, error_pattern in cases:
            payload: dict[str, object] = baseline.to_dict()
            payload[field_name] = value
            payload = _rehash_payload(payload, "result_sha256")
            with self.subTest(field=field_name), self.assertRaisesRegex(
                PreCallDesignLockError, error_pattern
            ):
                PreCallDesignLockResultV3.from_dict(payload)

    def test_rehashed_result_rejects_wrong_current_reason_census(self) -> None:
        baseline = validate_synthetic_pre_call_design_lock(_lock())
        payload: dict[str, object] = baseline.to_dict()
        payload["reason_codes"] = list(payload["reason_codes"])[1:]
        payload = _rehash_payload(payload, "result_sha256")
        with self.assertRaisesRegex(PreCallDesignLockError, "current reason"):
            PreCallDesignLockResultV3.from_dict(payload)

    def test_rehashed_result_rejects_nested_gate_identity_or_authority_drift(self) -> None:
        baseline = validate_synthetic_pre_call_design_lock(_lock())
        variants = (
            ("check_id", "current::forged", "current gate closure"),
            ("predicate_id", "forged_predicate", "current gate closure"),
            (
                "reason_codes",
                ["external_anchor_missing"],
                "failed reason does not match",
            ),
            (
                "authority_sha256s",
                [baseline.gate_checks[0].authority_sha256s[0]],
                "current gate closure",
            ),
            ("expected_value", "forged_expected", "current gate closure"),
        )
        for field_name, value, error_pattern in variants:
            payload: dict[str, object] = baseline.to_dict()
            gates = list(payload["gate_checks"])
            gate = dict(gates[0])
            gate[field_name] = value
            gates[0] = _rehash_payload(gate, "check_sha256")
            payload["gate_checks"] = gates
            payload = _rehash_payload(payload, "result_sha256")
            with self.subTest(field=field_name), self.assertRaisesRegex(
                PreCallDesignLockError, error_pattern
            ):
                PreCallDesignLockResultV3.from_dict(payload)


class TestStructuralArithmetic(unittest.TestCase):
    def test_exact_64_one_prefix_compact_census_is_1024_1728(self) -> None:
        census = lock_module._recompute_prefix_complete_structural_census(
            (1,) * 64,
            audit_target_count=24,
            focal_target_count=40,
            plan_kind="compact_actual_packet_reuse",
            synthetic_isolation_reuse_proof=None,
        )
        self.assertEqual(census.target_count, 64)
        self.assertEqual(census.selected_prefix_cell_count, 64)
        self.assertEqual(census.terminal_count, 1024)
        self.assertEqual(census.branch_generation_call_count, 1728)
        self.assertEqual(census.audit_terminal_count, 384)
        self.assertEqual(census.focal_terminal_count, 640)
        self.assertEqual(census.audit_branch_generation_call_count, 648)
        self.assertEqual(census.focal_branch_generation_call_count, 1080)
        self.assertTrue(census.shape_only_reference_counts_match)
        self.assertFalse(census.conditional_synthetic_compact_eligibility)

    def test_extra_prefix_increases_cost_rows_but_not_target_units(self) -> None:
        census = lock_module._recompute_prefix_complete_structural_census(
            (2,) + (1,) * 63,
            audit_target_count=24,
            focal_target_count=40,
            plan_kind="compact_actual_packet_reuse",
            synthetic_isolation_reuse_proof=None,
        )
        self.assertEqual(census.target_count, 64)
        self.assertEqual(census.selected_prefix_cell_count, 65)
        self.assertEqual(census.terminal_count, 1040)
        self.assertEqual(census.branch_generation_call_count, 1755)
        self.assertFalse(census.shape_only_reference_counts_match)
        self.assertFalse(census.conditional_synthetic_compact_eligibility)

    def test_compact_reference_requires_exact_24_40_split(self) -> None:
        census = lock_module._recompute_prefix_complete_structural_census(
            (1,) * 64,
            audit_target_count=25,
            focal_target_count=39,
            plan_kind="compact_actual_packet_reuse",
            synthetic_isolation_reuse_proof=None,
        )
        self.assertFalse(census.shape_only_reference_counts_match)
        self.assertFalse(census.conditional_synthetic_compact_eligibility)

    def test_compact_shape_without_proof_never_claims_conditional_eligibility(self) -> None:
        census = lock_module._recompute_prefix_complete_structural_census(
            (1,) * 64,
            audit_target_count=24,
            focal_target_count=40,
            plan_kind="compact_actual_packet_reuse",
            synthetic_isolation_reuse_proof=None,
        )
        self.assertTrue(census.shape_only_reference_counts_match)
        self.assertFalse(census.conditional_synthetic_compact_eligibility)

    def test_foreign_or_rehashed_incomplete_proof_cannot_upgrade_shape(self) -> None:
        class Trap:
            def __getattribute__(self, name: str):
                raise AssertionError(f"foreign proof property accessed: {name}")

        for proof in (
            Trap(),
            {"proof_sha256": ZERO_HASH, "failure_count": 0, "reviewed": True},
        ):
            with self.subTest(proof_type=type(proof).__name__), self.assertRaisesRegex(
                PreCallDesignLockError, "proof-bearing authority is unavailable"
            ):
                lock_module._recompute_prefix_complete_structural_census(
                    (1,) * 64,
                    audit_target_count=24,
                    focal_target_count=40,
                    plan_kind="compact_actual_packet_reuse",
                    synthetic_isolation_reuse_proof=proof,
                )

    def test_invalid_prefix_and_split_native_types_reject(self) -> None:
        cases = (
            ((1, 0), 1, 1),
            ((1, True), 1, 1),
            ([1, 1], 1, 1),
            ((1, 1), True, 1),
            ((1, 1), 2, 1),
        )
        for prefix_counts, audit_count, focal_count in cases:
            with self.subTest(values=(prefix_counts, audit_count, focal_count)):
                with self.assertRaises((TypeError, PreCallDesignLockError)):
                    lock_module._recompute_prefix_complete_structural_census(
                        prefix_counts,
                        audit_target_count=audit_count,
                        focal_target_count=focal_count,
                        plan_kind="compact_actual_packet_reuse",
                        synthetic_isolation_reuse_proof=None,
                    )

    def test_unbound_conservative_9216_13824_cannot_be_derived(self) -> None:
        with self.assertRaisesRegex(
            PreCallDesignLockError,
            "enumerated rows.*9,216/13,824.*unbound",
        ):
            lock_module._recompute_prefix_complete_structural_census(
                (1,) * 64,
                audit_target_count=24,
                focal_target_count=40,
                plan_kind="enumerated_binding_is_treatment",
                synthetic_isolation_reuse_proof=None,
            )


class TestAuthenticatedBoundary(unittest.TestCase):
    class _Trap:
        def __getattribute__(self, name: str):
            raise AssertionError(f"property access occurred: {name}")

    def test_authenticated_validator_needs_context_before_property_access(self) -> None:
        with self.assertRaisesRegex(NeedsContextError, "NEEDS_CONTEXT"):
            validate_authenticated_pre_call_design_lock(self._Trap())

    def test_required_authority_needs_context_before_any_work(self) -> None:
        with self.assertRaisesRegex(NeedsContextError, "NEEDS_CONTEXT"):
            require_authenticated_pre_call_authority()

    def test_production_module_has_no_io_path_network_or_domain_imports(self) -> None:
        module_path = REPO_ROOT / "iclr2027" / "precall_design_lock.py"
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
        forbidden_roots = {
            "os",
            "pathlib",
            "socket",
            "subprocess",
            "requests",
            "urllib",
            "iclr2027.obligation_outcomes",
            "iclr2027.obligation_oracle",
            "iclr2027.obligation_escalation",
            "iclr2027.capability_binding",
        }
        self.assertTrue(imported.isdisjoint(forbidden_roots), imported)
        self.assertFalse(
            any(
                isinstance(node, ast.Name) and node.id in {"open", "Path"}
                for node in ast.walk(tree)
            )
        )


class TestHelpOnlyCli(unittest.TestCase):
    def test_help_is_available_without_context(self) -> None:
        cli = _load_cli()
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(cli.main([]), 0)
        rendered = stdout.getvalue()
        self.assertIn("synthetic-only", rendered)
        self.assertIn("--current-fixture", rendered)

    def test_current_fixture_output_is_canonical_and_no_go(self) -> None:
        cli = _load_cli()
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(cli.main(["--current-fixture"]), 0)
        raw = stdout.getvalue()
        payload = json.loads(raw)
        self.assertEqual(
            raw,
            json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n",
        )
        lock = ArchitectureE1E2E3PreCallDesignLockV3.from_dict(payload["lock"])
        result = PreCallDesignLockResultV3.from_dict(payload["result"])
        self.assertEqual(result, validate_synthetic_pre_call_design_lock(lock))
        self.assertEqual(result.status, "no_go")
        self.assertFalse(result.official_result_eligible)

    def test_every_source_or_output_flag_needs_context_before_path_io(self) -> None:
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "must_not_exist.json"
            for flag in (
                "--source",
                "--inventory",
                "--data",
                "--rates",
                "--output",
                "--authenticated",
            ):
                argv = [flag] if flag == "--authenticated" else [flag, str(target)]
                with self.subTest(flag=flag):
                    with self.assertRaisesRegex(SystemExit, "NEEDS_CONTEXT"):
                        cli.main(argv)
                    self.assertFalse(target.exists())

    def test_current_fixture_cannot_be_combined_with_source_or_output(self) -> None:
        cli = _load_cli()
        for flag in ("--source", "--output"):
            with self.subTest(flag=flag):
                with self.assertRaisesRegex(SystemExit, "NEEDS_CONTEXT"):
                    cli.main(["--current-fixture", flag, "untrusted"])


if __name__ == "__main__":
    unittest.main()
