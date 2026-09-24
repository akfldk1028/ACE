"""Synthetic-only Task 6 pre-call design-lock contract.

This module intentionally has no source adapter.  It validates only the frozen
current synthetic continuity fixture and therefore can return only ``no_go``.
Authenticated authority requires an out-of-workspace launcher capability and
is unavailable in Phase A.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
import math
from typing import Any, ClassVar, NoReturn

from iclr2027.architecture_target_roster import verify_frozen_target_roster


__all__ = (
    "PreCallDesignLockError",
    "NeedsContextError",
    "validate_synthetic_pre_call_design_lock",
    "validate_authenticated_pre_call_design_lock",
    "require_authenticated_pre_call_authority",
)


_SCHEMA_PREFIX = "ace.iclr2027.precall_design_lock.v3."
_MEMORY_SHA256 = "e774381bbde93a9540821a6375ccbee55ec724d801e91b10efab2bcdc91083b6"
_SYNTHETIC_IMPLEMENTATION_SHA256 = hashlib.sha256(
    b"ace.iclr2027.precall_design_lock.v3.synthetic-validator"
).hexdigest()

_FAILURE_REASONS = frozenset(
    {
        "external_anchor_missing",
        "external_signature_invalid",
        "external_payload_nested_mismatch",
        "source_closure_incomplete",
        "method_source_version_untrusted",
        "synthetic_authority_cannot_pass",
        "domain_pooling_detected",
        "physical_cluster_alias_or_join_invalid",
        "physical_case_family_alias_or_join_invalid",
        "target_unit_alias_or_join_invalid",
        "typed_unit_roster_missing",
        "architecture_cluster_floor_not_met",
        "architecture_target_unit_floor_not_met",
        "architecture_audit_split_not_met",
        "architecture_focal_split_not_met",
        "architecture_branch_coverage_incomplete",
        "jci_floor_missing_or_not_replayable",
        "action_menu_incomplete",
        "shared_menu_incomplete",
        "evaluator_invariance_failed",
        "assignment_bijection_incomplete",
        "planned_control_closure_incomplete",
        "planned_terminal_or_call_closure_incomplete",
        "postrun_conformance_plan_missing",
        "branch_isolation_invalid",
        "reuse_equivalence_invalid",
        "conservative_expansion_unbound",
        "e1_protocol_incomplete",
        "e2_protocol_incomplete",
        "e3_parity_protocol_incomplete",
        "jci_determinism_protocol_incomplete",
        "mandatory_policy_plan_incomplete",
        "substantive_values_missing_or_posthoc",
        "grid_not_signed_before_simulation",
        "simulation_authorization_or_completion_invalid",
        "scenario_grid_incomplete",
        "variance_or_correlation_infeasible",
        "simulation_draw_count_below_10000",
        "simulation_power_lower_bound_failed",
        "mde_exceeds_substantive_delta",
        "precision_above_ceiling",
        "loso_failed",
        "randomization_computational_readiness_failed",
        "randomization_null_transformation_invalid",
        "weak_null_randomization_exactness_overclaim",
        "future_randomization_result_used_pre_call",
        "randomization_mc_exchangeability_or_add_one_rule_invalid",
        "randomization_mode_none_rule_invalid",
        "worst_case_missingness_failed",
        "support_attrition_or_noncompliance_failed",
        "holm_family_failed",
        "holm_family_plan_missing_or_posthoc",
        "holm_contrast_membership_mismatch",
        "secondary_contrast_value_missing_or_posthoc",
        "holm_joint_draw_or_dependence_invalid",
        "holm_joint_scenario_census_incomplete",
        "holm_global_null_effect_nonzero",
        "holm_strong_fwer_theorem_or_applicability_invalid",
        "holm_global_null_only_strong_fwer_claim",
        "holm_validity_mode_or_conclusion_invalid",
        "holm_finite_remainder_adjustment_invalid",
        "holm_asymptotic_to_finite_upgrade",
        "holm_subset_stress_failed",
        "holm_simulation_fwer_power_or_precision_failed",
        "future_actual_holm_used_pre_call",
        "model_rate_unresolved_or_stale",
        "tool_rate_unresolved_or_stale",
        "retry_or_tool_undercounted",
        "cost_ceiling_exceeded_or_missing",
        "time_ceiling_exceeded_or_missing",
        "caller_total_mismatch",
        "canonical_schema_hash_or_native_type_invalid",
        "hash_dependency_cycle",
        "plan_certification_cycle",
        "candidate_set_or_order_unanchored",
        "prefix_selection_or_closure_invalid",
        "prefix_cost_undercounted",
        "operation_catalog_incomplete",
        "mandatory_policy_operation_incomplete",
        "task5_roster_or_oracle_contract_mismatch",
        "joint_retry_expansion_incomplete",
        "null_type_i_bound_failed",
        "null_coverage_bound_failed",
        "simulation_simultaneous_bound_failed",
        "effect_lattice_or_sign_invalid",
        "mde_missing_for_required_nuisance",
        "e2_four_cell_missingness_incomplete",
        "e3_resource_utility_bound_invalid",
        "two_sided_resolution_invalid",
        "neyman_or_wild_plan_or_result_invalid",
        "scenario_candidate_protocol_mismatch",
        "population_estimand_closure_failed",
        "simulation_certification_plan_missing_or_posthoc",
        "simulation_bound_component_missing_duplicate_or_reused",
        "resampling_or_missingness_plan_missing_or_posthoc",
        "substantive_delta_gate_missing",
        "weighted_randomization_law_invalid",
        "scheduler_overhead_unbound_or_invalid",
        "sensitivity_predicate_invalid",
    }
)

_CURRENT_REASONS = (
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
)

_CURRENT_FACT_SHA256 = (
    "f3d40b5e11a5714d1553291ebb250ffd4f92cb1de1fe5ee3b230f4d24c8933ca"
)
_CURRENT_LOCK_SHA256 = (
    "409257e4dec111e1c0fc04054a016e2ab162ef6554eb11fbe9575eb448a9c468"
)
_CURRENT_GATE_AUTHORITY_SHA256S = tuple(
    sorted((_CURRENT_FACT_SHA256, _CURRENT_LOCK_SHA256), key=str.encode)
)


class PreCallDesignLockError(ValueError):
    """Raised when a pre-call design-lock value violates the frozen contract."""


class NeedsContextError(RuntimeError):
    """Raised before any I/O when authenticated launcher authority is absent."""


def _require_exact_bool(value: Any, name: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"{name} must be a native bool")


def _require_exact_int(value: Any, name: str, *, minimum: int = 0) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be a native int")
    if value < minimum:
        raise PreCallDesignLockError(f"{name} is below its minimum")


def _require_exact_float(value: Any, name: str) -> None:
    if type(value) is not float:
        raise TypeError(f"{name} must be a native float")
    if not math.isfinite(value):
        raise PreCallDesignLockError(f"{name} must be finite")


def _require_text(value: Any, name: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if type(value) is not str:
        raise TypeError(f"{name} must be a native string")
    if not value or value != value.strip():
        raise PreCallDesignLockError(f"{name} must be exact nonempty text")


def _require_sha256(value: Any, name: str) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise PreCallDesignLockError(f"{name} must be a lowercase SHA-256 digest")


def _normal_zero(value: Any) -> Any:
    if type(value) is float:
        if not math.isfinite(value):
            raise PreCallDesignLockError("all numeric values must be finite")
        return 0.0 if value == 0.0 else value
    if type(value) in (str, int, bool) or value is None:
        return value
    if type(value) is tuple:
        return tuple(_normal_zero(item) for item in value)
    if type(value) is list:
        return [_normal_zero(item) for item in value]
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise TypeError("canonical objects require native string keys")
        return {key: _normal_zero(item) for key, item in value.items()}
    raise TypeError(f"unsupported non-native canonical value: {type(value).__name__}")


def _require_json_native_value(value: Any, name: str) -> None:
    if type(value) in (str, int, bool) or value is None:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise PreCallDesignLockError(f"{name} must contain finite JSON numerics")
        return
    if type(value) is list:
        for item in value:
            _require_json_native_value(item, name)
        return
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise TypeError(f"{name} requires native string object keys")
        for item in value.values():
            _require_json_native_value(item, name)
        return
    raise PreCallDesignLockError(
        f"{name} must contain only canonical JSON-native values"
    )


def _reject_raw_negative_zero(value: Any) -> None:
    if type(value) is float:
        if not math.isfinite(value):
            raise PreCallDesignLockError("all JSON numerics must be finite")
        if value == 0.0 and math.copysign(1.0, value) < 0:
            raise PreCallDesignLockError("raw JSON signed zero is forbidden")
        return
    if type(value) is list:
        for item in value:
            _reject_raw_negative_zero(item)
        return
    if type(value) is dict:
        for item in value.values():
            _reject_raw_negative_zero(item)


def _plain(value: Any) -> Any:
    if isinstance(value, _Record):
        return value.to_dict()
    if type(value) is tuple:
        return [_plain(item) for item in value]
    if type(value) is list:
        return [_plain(item) for item in value]
    if type(value) is dict:
        return {key: _plain(item) for key, item in value.items()}
    return value


def _canonical(value: Any) -> str:
    try:
        return json.dumps(
            _plain(value),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise PreCallDesignLockError("value is not canonical JSON") from error


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _byte_sorted_unique(values: tuple[str, ...], name: str) -> None:
    if type(values) is not tuple or any(type(value) is not str for value in values):
        raise TypeError(f"{name} must be an exact tuple of native strings")
    expected = tuple(sorted(set(values), key=lambda item: item.encode("utf-8")))
    if values != expected:
        raise PreCallDesignLockError(f"{name} must be UTF-8 byte-sorted and unique")


def _typed_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        if set(left) != set(right):
            return False
        return all(_typed_equal(left[key], right[key]) for key in left)
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(
            _typed_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return bool(left == right)


def _recompute_comparison(operator: str, expected: Any, observed: Any) -> bool:
    if operator == "eq":
        return _typed_equal(expected, observed)
    if operator == "is_none":
        return observed is None
    if operator == "is_not_none":
        return observed is not None
    if type(expected) is not type(observed) or type(expected) not in (int, float):
        return False
    if operator == "ge":
        return observed >= expected
    if operator == "le":
        return observed <= expected
    if operator == "gt":
        return observed > expected
    if operator == "lt":
        return observed < expected
    raise PreCallDesignLockError("comparison_operator is invalid")


def _duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PreCallDesignLockError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_json(raw: str | bytes) -> tuple[Any, str]:
    if type(raw) is bytes:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise PreCallDesignLockError("input must be valid UTF-8") from error
    elif type(raw) is str:
        text = raw
    else:
        raise TypeError("JSON input must be exact str or bytes")
    if text.startswith("\ufeff"):
        raise PreCallDesignLockError("UTF-8 BOM is forbidden")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_guard,
            parse_constant=lambda token: (_ for _ in ()).throw(
                PreCallDesignLockError(f"non-finite JSON constant: {token}")
            ),
        )
    except PreCallDesignLockError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise PreCallDesignLockError("invalid canonical JSON") from error
    _reject_raw_negative_zero(value)
    if _canonical(value) != text:
        raise PreCallDesignLockError("input is not canonical JSON")
    return value, text


class _Record:
    __slots__ = ()
    SCHEMA: ClassVar[str]
    HASH_FIELD: ClassVar[str]
    RECORD_FIELDS: ClassVar[dict[str, type[_Record]]] = {}
    TUPLE_FIELDS: ClassVar[frozenset[str]] = frozenset()
    RECORD_TUPLE_FIELDS: ClassVar[dict[str, type[_Record]]] = {}

    @classmethod
    def create(cls, **values: Any):
        field_names = tuple(field.name for field in fields(cls))
        supplied_names = set(values)
        generated_names = {"schema_version", cls.HASH_FIELD}
        if "synthetic_only" in field_names:
            generated_names.add("synthetic_only")
        expected_names = set(field_names) - generated_names
        if supplied_names != expected_names:
            raise PreCallDesignLockError("record keys are missing or extra")
        payload = {
            name: cls._normalize_declared_field(name, value)
            for name, value in values.items()
        }
        payload["schema_version"] = cls.SCHEMA
        if "synthetic_only" in field_names:
            payload["synthetic_only"] = True
        unsigned = {
            name: _plain(payload[name])
            for name in field_names
            if name != cls.HASH_FIELD
        }
        payload[cls.HASH_FIELD] = _sha256(unsigned)
        return cls(**payload)

    @classmethod
    def _normalize_declared_field(cls, name: str, value: Any) -> Any:
        if name in cls.RECORD_FIELDS:
            if type(value) is not cls.RECORD_FIELDS[name]:
                raise PreCallDesignLockError(f"{name} must have its exact record type")
            return value
        if name in cls.RECORD_TUPLE_FIELDS:
            if type(value) is not tuple:
                raise TypeError(f"{name} must be an exact tuple")
            record_type = cls.RECORD_TUPLE_FIELDS[name]
            if any(type(item) is not record_type for item in value):
                raise PreCallDesignLockError(
                    f"{name} must contain only its exact record type"
                )
            return value
        return _normal_zero(value)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]):
        if type(payload) is not dict:
            raise TypeError("record payload must be an exact native dict")
        if any(type(key) is not str for key in payload):
            raise TypeError("record payload requires native string keys")
        expected = {field.name for field in fields(cls)}
        if set(payload) != expected:
            raise PreCallDesignLockError("record keys are missing or extra")
        converted: dict[str, Any] = {}
        for name, value in payload.items():
            if name in cls.RECORD_FIELDS:
                if type(value) is not dict:
                    raise PreCallDesignLockError(
                        f"{name} must be a nested record object"
                    )
                value = cls.RECORD_FIELDS[name].from_dict(value)
            elif name in cls.RECORD_TUPLE_FIELDS:
                if type(value) is not list:
                    raise PreCallDesignLockError(f"{name} must be a canonical array")
                record_type = cls.RECORD_TUPLE_FIELDS[name]
                if any(type(item) is not dict for item in value):
                    raise PreCallDesignLockError(f"{name} contains a non-record")
                value = tuple(record_type.from_dict(item) for item in value)
            elif name in cls.TUPLE_FIELDS:
                if type(value) is not list:
                    raise PreCallDesignLockError(f"{name} must be a canonical array")
                value = tuple(value)
            converted[name] = cls._normalize_declared_field(name, value)
        try:
            return cls(**converted)
        except PreCallDesignLockError:
            raise
        except (TypeError, ValueError) as error:
            raise PreCallDesignLockError("record payload is invalid") from error

    @classmethod
    def from_json(cls, raw: str | bytes):
        payload, _ = _parse_json(raw)
        if type(payload) is not dict:
            raise PreCallDesignLockError("record JSON must contain an object")
        return cls.from_dict(payload)

    def __post_init__(self) -> None:
        for field in fields(self):
            object.__setattr__(
                self,
                field.name,
                type(self)._normalize_declared_field(
                    field.name, getattr(self, field.name)
                ),
            )
        if self.schema_version != self.SCHEMA:
            raise PreCallDesignLockError("schema_version is not exact")
        supplied_hash = getattr(self, self.HASH_FIELD)
        _require_sha256(supplied_hash, self.HASH_FIELD)
        unsigned = {
            field.name: _plain(getattr(self, field.name))
            for field in fields(self)
            if field.name != self.HASH_FIELD
        }
        if supplied_hash != _sha256(unsigned):
            raise PreCallDesignLockError("record self-hash mismatch")
        self._validate()

    def _validate(self) -> None:
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        return {field.name: _plain(getattr(self, field.name)) for field in fields(self)}

    def canonical_json(self) -> str:
        return _canonical(self.to_dict())


@dataclass(frozen=True, slots=True)
class VerifiedArchitectureInventoryV2(_Record):
    """Verified public inventory facts; this view confers no call authority."""

    schema_version: str
    site_count: int
    target_unit_count: int
    target_roster_sha256: str
    freeze_receipt_sha256: str
    projection_identity_commitment: str
    view_sha256: str

    SCHEMA: ClassVar[str] = "ace.iclr2027.verified_architecture_inventory.v2"
    HASH_FIELD: ClassVar[str] = "view_sha256"

    def _validate(self) -> None:
        _require_exact_int(self.site_count, "site_count")
        _require_exact_int(self.target_unit_count, "target_unit_count")
        if self.site_count != 8:
            raise PreCallDesignLockError("site_count must be exactly 8")
        if self.target_unit_count != 64:
            raise PreCallDesignLockError("target_unit_count must be exactly 64")
        for name in (
            "target_roster_sha256",
            "freeze_receipt_sha256",
            "projection_identity_commitment",
        ):
            _require_sha256(getattr(self, name), name)


def verify_architecture_inventory_receipt(
    roster_path: Any,
    receipt_path: Any,
    *,
    projection_identity_commitment: str,
) -> VerifiedArchitectureInventoryV2:
    """Derive a non-authorizing inventory view from verified public sidecars."""

    receipt = verify_frozen_target_roster(
        roster_path,
        receipt_path,
        projection_identity_commitment=projection_identity_commitment,
    )
    return VerifiedArchitectureInventoryV2.create(
        site_count=receipt.combined_dev_site_count,
        target_unit_count=receipt.combined_dev_target_count,
        target_roster_sha256=receipt.target_roster_sha256,
        freeze_receipt_sha256=receipt.receipt_sha256,
        projection_identity_commitment=projection_identity_commitment,
    )


@dataclass(frozen=True, slots=True)
class CurrentArchitectureInventoryFactV3(_Record):
    schema_version: str
    gate0_inventory_file_sha256: str
    gate0_inventory_self_sha256: str
    gate0_publication_receipt_file_sha256: str
    gate0_publication_receipt_self_sha256: str
    gate0_source_map_sha256: str
    authenticated_cluster_count: int
    historical_case_count: int
    historical_run_count: int
    prefix_count: int
    standardized_action_covered_count: int
    standardized_action_required_count: int
    typed_unit_roster_status: str
    typed_unit_count: int | None
    source_memory_sha256: str
    synthetic_only: bool
    fact_sha256: str

    SCHEMA: ClassVar[str] = _SCHEMA_PREFIX + "current_architecture_inventory_fact_v3"
    HASH_FIELD: ClassVar[str] = "fact_sha256"

    def _validate(self) -> None:
        for name in (
            "gate0_inventory_file_sha256",
            "gate0_inventory_self_sha256",
            "gate0_publication_receipt_file_sha256",
            "gate0_publication_receipt_self_sha256",
            "gate0_source_map_sha256",
            "source_memory_sha256",
        ):
            _require_sha256(getattr(self, name), name)
        for name in (
            "authenticated_cluster_count",
            "historical_case_count",
            "historical_run_count",
            "prefix_count",
            "standardized_action_covered_count",
            "standardized_action_required_count",
        ):
            _require_exact_int(getattr(self, name), name)
        if (
            self.standardized_action_covered_count
            > self.standardized_action_required_count
        ):
            raise PreCallDesignLockError("covered actions exceed required actions")
        if self.typed_unit_roster_status not in {"absent", "present"}:
            raise PreCallDesignLockError("typed_unit_roster_status is invalid")
        if self.typed_unit_roster_status == "absent":
            if self.typed_unit_count is not None:
                raise PreCallDesignLockError(
                    "absent typed roster requires a null count"
                )
        else:
            _require_exact_int(self.typed_unit_count, "typed_unit_count", minimum=1)
        _require_exact_bool(self.synthetic_only, "synthetic_only")
        if not self.synthetic_only:
            raise PreCallDesignLockError("this record is synthetic-only")


@dataclass(frozen=True, slots=True)
class GateCheckResultV3(_Record):
    schema_version: str
    check_id: str
    domain_id: str | None
    candidate_ref: str | None
    scenario_ref: str | None
    effect_ref: str | None
    fold_ref: str | None
    predicate_id: str
    comparison_operator: str
    expected_value: Any
    observed_value: Any
    passed: bool
    reason_codes: tuple[str, ...]
    authority_sha256s: tuple[str, ...]
    check_sha256: str

    SCHEMA: ClassVar[str] = _SCHEMA_PREFIX + "gate_check_result_v3"
    HASH_FIELD: ClassVar[str] = "check_sha256"
    TUPLE_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"reason_codes", "authority_sha256s"}
    )

    def _validate(self) -> None:
        _require_text(self.check_id, "check_id")
        for name in (
            "domain_id",
            "candidate_ref",
            "scenario_ref",
            "effect_ref",
            "fold_ref",
        ):
            _require_text(getattr(self, name), name, optional=True)
        _require_text(self.predicate_id, "predicate_id")
        if self.comparison_operator not in {
            "eq",
            "ge",
            "le",
            "gt",
            "lt",
            "is_none",
            "is_not_none",
        }:
            raise PreCallDesignLockError("comparison_operator is invalid")
        _require_json_native_value(self.expected_value, "expected_value")
        _require_json_native_value(self.observed_value, "observed_value")
        _require_exact_bool(self.passed, "passed")
        recomputed = _recompute_comparison(
            self.comparison_operator, self.expected_value, self.observed_value
        )
        if self.passed is not recomputed:
            raise PreCallDesignLockError(
                "passed disagrees with the recomputed predicate"
            )
        _byte_sorted_unique(self.reason_codes, "reason_codes")
        if self.passed:
            if self.reason_codes != ("all_pre_call_checks_passed",):
                raise PreCallDesignLockError("passing reason vocabulary is invalid")
        elif not self.reason_codes or not set(self.reason_codes) <= _FAILURE_REASONS:
            raise PreCallDesignLockError("failure reason vocabulary is invalid")
        elif self.predicate_id in _FAILURE_REASONS and self.reason_codes != (
            self.predicate_id,
        ):
            raise PreCallDesignLockError("failed reason does not match its predicate")
        _byte_sorted_unique(self.authority_sha256s, "authority_sha256s")
        if not self.authority_sha256s:
            raise PreCallDesignLockError("authority_sha256s cannot be empty")
        for digest in self.authority_sha256s:
            _require_sha256(digest, "authority_sha256s item")


@dataclass(frozen=True, slots=True)
class ArchitectureE1E2E3PreCallDesignLockV3(_Record):
    schema_version: str
    authority_mode: str
    current_inventory_fact: CurrentArchitectureInventoryFactV3
    simulation_freeze_plan: None
    external_anchor_receipt: None
    simulation_run_authorization_receipt: None
    simulation_run_completion_receipt: None
    architecture_domain_evaluation: None
    jci_domain_evaluation: None
    joint_selected_operational_budget: None
    primary_alpha: float
    primary_interval_level: float
    secondary_holm_fwer: float
    implementation_code_sha256s: tuple[str, ...]
    synthetic_only: bool
    lock_sha256: str

    SCHEMA: ClassVar[str] = (
        _SCHEMA_PREFIX + "architecture_e1_e2_e3_pre_call_design_lock_v3"
    )
    HASH_FIELD: ClassVar[str] = "lock_sha256"
    RECORD_FIELDS: ClassVar[dict[str, type[_Record]]] = {
        "current_inventory_fact": CurrentArchitectureInventoryFactV3
    }
    TUPLE_FIELDS: ClassVar[frozenset[str]] = frozenset({"implementation_code_sha256s"})

    def _validate(self) -> None:
        if self.authority_mode != "synthetic":
            raise PreCallDesignLockError("synthetic authority_mode must be exact")
        if type(self.current_inventory_fact) is not CurrentArchitectureInventoryFactV3:
            raise PreCallDesignLockError(
                "current_inventory_fact must have its exact record type"
            )
        for name in (
            "simulation_freeze_plan",
            "external_anchor_receipt",
            "simulation_run_authorization_receipt",
            "simulation_run_completion_receipt",
            "architecture_domain_evaluation",
            "jci_domain_evaluation",
            "joint_selected_operational_budget",
        ):
            if getattr(self, name) is not None:
                raise PreCallDesignLockError(f"synthetic {name} must be None")
        for name, expected in (
            ("primary_alpha", 0.05),
            ("primary_interval_level", 0.95),
            ("secondary_holm_fwer", 0.05),
        ):
            value = getattr(self, name)
            _require_exact_float(value, name)
            if value != expected:
                raise PreCallDesignLockError(f"{name} is not frozen")
        _byte_sorted_unique(
            self.implementation_code_sha256s, "implementation_code_sha256s"
        )
        if self.implementation_code_sha256s != (_SYNTHETIC_IMPLEMENTATION_SHA256,):
            raise PreCallDesignLockError(
                "implementation closure is not the frozen synthetic closure"
            )
        _require_exact_bool(self.synthetic_only, "synthetic_only")
        if not self.synthetic_only:
            raise PreCallDesignLockError("synthetic lock cannot be upgraded")


@dataclass(frozen=True, slots=True)
class PreCallDesignLockResultV3(_Record):
    schema_version: str
    lock_sha256: str
    authority_mode: str
    status: str
    reason_codes: tuple[str, ...]
    gate_checks: tuple[GateCheckResultV3, ...]
    architecture_selected_candidate_ref: str | None
    jci_selected_candidate_ref: str | None
    architecture_cluster_count: int | None
    architecture_target_unit_count: int | None
    jci_cluster_count: int | None
    jci_target_unit_count: int | None
    architecture_selected_prefix_cell_count: int | None
    jci_selected_prefix_cell_count: int | None
    architecture_terminal_count: int | None
    architecture_branch_generation_call_count: int | None
    jci_terminal_count: int | None
    jci_branch_generation_call_count: int | None
    recomputed_operation_count: int | None
    recomputed_worst_case_attempts: int | None
    recomputed_model_cost: float | None
    recomputed_tool_cost: float | None
    recomputed_total_cost: float | None
    recomputed_worst_case_wall_seconds: float | None
    official_result_eligible: bool
    synthetic_only: bool
    result_sha256: str

    SCHEMA: ClassVar[str] = _SCHEMA_PREFIX + "pre_call_design_lock_result_v3"
    HASH_FIELD: ClassVar[str] = "result_sha256"
    TUPLE_FIELDS: ClassVar[frozenset[str]] = frozenset({"reason_codes"})
    RECORD_TUPLE_FIELDS: ClassVar[dict[str, type[_Record]]] = {
        "gate_checks": GateCheckResultV3
    }

    def _validate(self) -> None:
        _require_sha256(self.lock_sha256, "lock_sha256")
        if self.lock_sha256 != _CURRENT_LOCK_SHA256:
            raise PreCallDesignLockError("current lock binding is not exact")
        _require_exact_bool(self.synthetic_only, "synthetic_only")
        if not self.synthetic_only:
            raise PreCallDesignLockError("Phase-A result is synthetic-only")
        if (
            self.authority_mode != "synthetic"
            or self.status != "no_go"
            or self.official_result_eligible is not False
        ):
            raise PreCallDesignLockError(
                "Phase-A synthetic-only result must be no_go and unofficial"
            )
        _byte_sorted_unique(self.reason_codes, "reason_codes")
        if self.reason_codes != _CURRENT_REASONS:
            raise PreCallDesignLockError("current reason census is not exact")
        if type(self.gate_checks) is not tuple or not self.gate_checks:
            raise PreCallDesignLockError("gate_checks must be a nonempty exact tuple")
        if any(type(gate) is not GateCheckResultV3 for gate in self.gate_checks):
            raise PreCallDesignLockError("gate_checks contain a foreign record type")
        for name in (
            "architecture_selected_candidate_ref",
            "jci_selected_candidate_ref",
        ):
            _require_text(getattr(self, name), name, optional=True)
        count_fields = (
            "architecture_cluster_count",
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
        )
        for name in count_fields:
            value = getattr(self, name)
            if value is not None:
                _require_exact_int(value, name)
        for name in (
            "recomputed_model_cost",
            "recomputed_tool_cost",
            "recomputed_total_cost",
            "recomputed_worst_case_wall_seconds",
        ):
            value = getattr(self, name)
            if value is not None:
                _require_exact_float(value, name)
                if value < 0.0:
                    raise PreCallDesignLockError(f"{name} cannot be negative")
        _require_exact_bool(self.official_result_eligible, "official_result_eligible")
        exact_top_level = {
            "architecture_selected_candidate_ref": None,
            "jci_selected_candidate_ref": None,
            "architecture_cluster_count": 5,
            "architecture_target_unit_count": None,
            "jci_cluster_count": None,
            "jci_target_unit_count": None,
            "architecture_selected_prefix_cell_count": None,
            "jci_selected_prefix_cell_count": None,
            "architecture_terminal_count": None,
            "architecture_branch_generation_call_count": None,
            "jci_terminal_count": None,
            "jci_branch_generation_call_count": None,
            "recomputed_operation_count": None,
            "recomputed_worst_case_attempts": None,
            "recomputed_model_cost": None,
            "recomputed_tool_cost": None,
            "recomputed_total_cost": None,
            "recomputed_worst_case_wall_seconds": None,
        }
        if any(
            not _typed_equal(getattr(self, name), expected)
            for name, expected in exact_top_level.items()
        ):
            raise PreCallDesignLockError("current result closure is not exact")
        if len(self.gate_checks) != len(_CURRENT_REASONS):
            raise PreCallDesignLockError("current gate closure is not exact")
        common_authority = self.gate_checks[0].authority_sha256s
        if common_authority != _CURRENT_GATE_AUTHORITY_SHA256S:
            raise PreCallDesignLockError("current gate closure authority is not exact")
        if self.lock_sha256 not in common_authority:
            raise PreCallDesignLockError(
                "current result closure lock binding is not exact"
            )
        for reason, gate in zip(_CURRENT_REASONS, self.gate_checks, strict=True):
            operator, expected, observed = _current_gate_values(reason)
            expected_domain = (
                "architecture" if reason.startswith("architecture_") else None
            )
            exact_gate = (
                gate.check_id == f"current::{reason}"
                and gate.domain_id == expected_domain
                and gate.candidate_ref is None
                and gate.scenario_ref is None
                and gate.effect_ref is None
                and gate.fold_ref is None
                and gate.predicate_id == reason
                and gate.comparison_operator == operator
                and _typed_equal(gate.expected_value, expected)
                and _typed_equal(gate.observed_value, observed)
                and gate.passed is False
                and gate.reason_codes == (reason,)
                and gate.authority_sha256s == common_authority
                and self.lock_sha256 in gate.authority_sha256s
            )
            if not exact_gate:
                raise PreCallDesignLockError("current gate closure is not exact")


@dataclass(frozen=True, slots=True)
class _StructuralCensus:
    target_count: int
    selected_prefix_cell_count: int
    terminal_count: int
    branch_generation_call_count: int
    audit_terminal_count: int
    focal_terminal_count: int
    audit_branch_generation_call_count: int
    focal_branch_generation_call_count: int
    shape_only_reference_counts_match: bool
    conditional_synthetic_compact_eligibility: bool


def _recompute_prefix_complete_structural_census(
    selected_prefix_counts: tuple[int, ...],
    *,
    audit_target_count: int,
    focal_target_count: int,
    plan_kind: str,
    synthetic_isolation_reuse_proof: object | None = None,
) -> _StructuralCensus:
    """Recompute shape-only 16/27 arithmetic without certifying reuse."""

    if synthetic_isolation_reuse_proof is not None:
        raise PreCallDesignLockError(
            "synthetic proof-bearing authority is unavailable in Phase A"
        )

    if type(selected_prefix_counts) is not tuple:
        raise TypeError("selected_prefix_counts must be an exact tuple")
    if not selected_prefix_counts:
        raise PreCallDesignLockError("at least one target is required")
    for count in selected_prefix_counts:
        _require_exact_int(count, "selected prefix count", minimum=1)
    _require_exact_int(audit_target_count, "audit_target_count")
    _require_exact_int(focal_target_count, "focal_target_count")
    if audit_target_count + focal_target_count != len(selected_prefix_counts):
        raise PreCallDesignLockError("audit/focal targets must close the target roster")
    if plan_kind == "enumerated_binding_is_treatment":
        raise PreCallDesignLockError(
            "conservative expansion requires complete enumerated rows; "
            "9,216/13,824 remain scientifically unbound"
        )
    if plan_kind != "compact_actual_packet_reuse":
        raise PreCallDesignLockError("plan_kind is invalid")
    selected_cells = sum(selected_prefix_counts)
    audit_cells = sum(selected_prefix_counts[:audit_target_count])
    focal_cells = sum(selected_prefix_counts[audit_target_count:])
    return _StructuralCensus(
        target_count=len(selected_prefix_counts),
        selected_prefix_cell_count=selected_cells,
        terminal_count=16 * selected_cells,
        branch_generation_call_count=27 * selected_cells,
        audit_terminal_count=16 * audit_cells,
        focal_terminal_count=16 * focal_cells,
        audit_branch_generation_call_count=27 * audit_cells,
        focal_branch_generation_call_count=27 * focal_cells,
        shape_only_reference_counts_match=(
            len(selected_prefix_counts) == 64
            and audit_target_count == 24
            and focal_target_count == 40
            and selected_prefix_counts == (1,) * 64
        ),
        conditional_synthetic_compact_eligibility=False,
    )


def _current_gate_values(reason: str) -> tuple[str, Any, Any]:
    if reason == "architecture_cluster_floor_not_met":
        return "ge", 8, 5
    if reason == "architecture_target_unit_floor_not_met":
        return "ge", 64, None
    if reason == "architecture_audit_split_not_met":
        return "ge", {"clusters": 3, "targets": 24}, None
    if reason == "architecture_focal_split_not_met":
        return "ge", {"clusters": 5, "targets": 40}, None
    if reason == "architecture_branch_coverage_incomplete":
        return "eq", 6, 0
    if reason == "synthetic_authority_cannot_pass":
        return "eq", False, True
    return "is_not_none", "bound", None


def _assert_current_continuity(fact: CurrentArchitectureInventoryFactV3) -> None:
    exact = (
        fact.authenticated_cluster_count == 5
        and fact.historical_case_count == 30
        and fact.historical_run_count == 450
        and fact.prefix_count == 1524
        and fact.standardized_action_covered_count == 0
        and fact.standardized_action_required_count == 6
        and fact.typed_unit_roster_status == "absent"
        and fact.typed_unit_count is None
        and fact.source_memory_sha256 == _MEMORY_SHA256
        and fact.synthetic_only
    )
    if not exact:
        raise PreCallDesignLockError(
            "current continuity fixture does not match frozen facts"
        )


def validate_synthetic_pre_call_design_lock(
    lock: ArchitectureE1E2E3PreCallDesignLockV3,
) -> PreCallDesignLockResultV3:
    """Validate the frozen no-I/O current fixture and return deterministic NO-GO."""

    if type(lock) is not ArchitectureE1E2E3PreCallDesignLockV3:
        raise TypeError("lock must have the exact synthetic design-lock type")
    _assert_current_continuity(lock.current_inventory_fact)
    authority = tuple(
        sorted(
            (lock.current_inventory_fact.fact_sha256, lock.lock_sha256),
            key=lambda value: value.encode("utf-8"),
        )
    )
    gates = []
    for reason in _CURRENT_REASONS:
        operator, expected, observed = _current_gate_values(reason)
        gates.append(
            GateCheckResultV3.create(
                check_id=f"current::{reason}",
                domain_id="architecture"
                if reason.startswith("architecture_")
                else None,
                candidate_ref=None,
                scenario_ref=None,
                effect_ref=None,
                fold_ref=None,
                predicate_id=reason,
                comparison_operator=operator,
                expected_value=expected,
                observed_value=observed,
                passed=False,
                reason_codes=(reason,),
                authority_sha256s=authority,
            )
        )
    return PreCallDesignLockResultV3.create(
        lock_sha256=lock.lock_sha256,
        authority_mode="synthetic",
        status="no_go",
        reason_codes=_CURRENT_REASONS,
        gate_checks=tuple(gates),
        architecture_selected_candidate_ref=None,
        jci_selected_candidate_ref=None,
        architecture_cluster_count=5,
        architecture_target_unit_count=None,
        jci_cluster_count=None,
        jci_target_unit_count=None,
        architecture_selected_prefix_cell_count=None,
        jci_selected_prefix_cell_count=None,
        architecture_terminal_count=None,
        architecture_branch_generation_call_count=None,
        jci_terminal_count=None,
        jci_branch_generation_call_count=None,
        recomputed_operation_count=None,
        recomputed_worst_case_attempts=None,
        recomputed_model_cost=None,
        recomputed_tool_cost=None,
        recomputed_total_cost=None,
        recomputed_worst_case_wall_seconds=None,
        official_result_eligible=False,
    )


def validate_authenticated_pre_call_design_lock(
    view: object,
) -> PreCallDesignLockResultV3:
    """Fail before inspecting ``view`` because the external trust root is absent."""

    del view
    raise NeedsContextError(
        "NEEDS_CONTEXT: authenticated launcher capability is absent"
    )


def require_authenticated_pre_call_authority() -> NoReturn:
    """Require the externally delivered authority unavailable in synthetic Phase A."""

    raise NeedsContextError(
        "NEEDS_CONTEXT: authenticated launcher capability is absent"
    )


def _fixture_digest(label: str) -> str:
    return hashlib.sha256(f"synthetic-current::{label}".encode("utf-8")).hexdigest()


def _current_synthetic_pre_call_design_lock() -> ArchitectureE1E2E3PreCallDesignLockV3:
    fact = CurrentArchitectureInventoryFactV3.create(
        gate0_inventory_file_sha256=_fixture_digest("inventory-file"),
        gate0_inventory_self_sha256=_fixture_digest("inventory-self"),
        gate0_publication_receipt_file_sha256=_fixture_digest("receipt-file"),
        gate0_publication_receipt_self_sha256=_fixture_digest("receipt-self"),
        gate0_source_map_sha256=_fixture_digest("source-map"),
        authenticated_cluster_count=5,
        historical_case_count=30,
        historical_run_count=450,
        prefix_count=1524,
        standardized_action_covered_count=0,
        standardized_action_required_count=6,
        typed_unit_roster_status="absent",
        typed_unit_count=None,
        source_memory_sha256=_MEMORY_SHA256,
    )
    return ArchitectureE1E2E3PreCallDesignLockV3.create(
        authority_mode="synthetic",
        current_inventory_fact=fact,
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
        implementation_code_sha256s=(_SYNTHETIC_IMPLEMENTATION_SHA256,),
    )


def _current_synthetic_fixture() -> dict[str, Any]:
    lock = _current_synthetic_pre_call_design_lock()
    result = validate_synthetic_pre_call_design_lock(lock)
    return {"lock": lock.to_dict(), "result": result.to_dict()}


def _canonical_fixture_json() -> str:
    return _canonical(_current_synthetic_fixture())
