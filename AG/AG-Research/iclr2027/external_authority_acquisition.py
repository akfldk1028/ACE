"""Synthetic-only negative validator for Task 7 external authority acquisition.

This module validates canonical metadata already present in memory.  It does not
read paths, construct keys, verify signatures, access research sources, or mint
authority.  Its only public result is the frozen current ``no_go`` state.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
import hashlib
import json
import math
import re
from typing import Any, ClassVar


__all__ = (
    "ExternalAuthorityAcquisitionError",
    "NeedsContextError",
    "negative_fixture_registry",
    "validate_synthetic_external_authority_acquisition",
    "require_authenticated_external_authority_acquisition",
)


class ExternalAuthorityAcquisitionError(ValueError):
    """Raised when synthetic acquisition metadata violates the frozen contract."""


class NeedsContextError(ExternalAuthorityAcquisitionError):
    """Raised before inspecting any caller object when external authority is absent."""


_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")
_UTC_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
_LEGACY_SHA = "e774381bbde93a9540821a6375ccbee55ec724d801e91b10efab2bcdc91083b6"
_FORBIDDEN_DOWNSTREAM_SHAS = (
    "a10f565562d83ec2c0e44e43baa13f0b01fa9922e5f72506ad6d824738a463c2",
    "ef42347d74bc3f319036dfc91e84c85934291726d51778d388edbab32736d158",
)
_TASK5_ANALYSIS_SHA = "2809048fa71d0f2458db13f7590c61f0f28674f2195c3d8690a45193df517299"
_TASK5_BRIEF_SHA = "8d2f27d2fb9e6901d7bfed90407a25f8c714d23fe9d2f511a469494e272054ee"
_TASK5_REVIEW_SHA = "8d98a17ee57b1a254d4f651d74b44b696ec022e3822daea1b8a3f25036060cc8"
_TASK5_PINS = tuple(sorted((_TASK5_ANALYSIS_SHA, _TASK5_BRIEF_SHA, _TASK5_REVIEW_SHA)))

_ROLE_DOMAINS = {
    "legacy_search_impossibility_declaration": "ACE-ICLR2027-LEGACY-SEARCH-IMPOSSIBILITY-VNEXT\x00",
    "one_thesis_contract": "ACE-ICLR2027-ONE-THESIS-CONTRACT-VNEXT\x00",
    "new_upstream_scientific_snapshot": "ACE-ICLR2027-NEW-UPSTREAM-SCIENTIFIC-SNAPSHOT-VNEXT\x00",
    "independent_science_migration_review": "ACE-ICLR2027-INDEPENDENT-SCIENCE-MIGRATION-REVIEW-VNEXT\x00",
    "independent_provenance_migration_review": "ACE-ICLR2027-INDEPENDENT-PROVENANCE-MIGRATION-REVIEW-VNEXT\x00",
    "independent_security_migration_review": "ACE-ICLR2027-INDEPENDENT-SECURITY-MIGRATION-REVIEW-VNEXT\x00",
    "provenance_migration_receipt": "ACE-ICLR2027-PROVENANCE-MIGRATION-RECEIPT-VNEXT\x00",
}

_ROLE_SCHEMAS = {
    "legacy_search_impossibility_declaration": "ace.iclr2027.legacy_search_impossibility_declaration.vnext",
    "one_thesis_contract": "ace.iclr2027.one_thesis_contract.vnext",
    "new_upstream_scientific_snapshot": "ace.iclr2027.new_upstream_scientific_snapshot.vnext",
    "independent_science_migration_review": "ace.iclr2027.independent_migration_review.vnext",
    "independent_provenance_migration_review": "ace.iclr2027.independent_migration_review.vnext",
    "independent_security_migration_review": "ace.iclr2027.independent_migration_review.vnext",
    "provenance_migration_receipt": "ace.iclr2027.provenance_migration_receipt.vnext",
}

_POLICY_IDS = (
    "agentprune",
    "agora",
    "always_all_specialists",
    "automix",
    "bicsrouter",
    "conformal_thinking",
    "cost_aware_protocol_routing",
    "difficulty_confidence",
    "fixed_topology",
    "gptswarm",
    "graphplanner",
    "masrouter",
    "matched_compute_self_agent_scaling",
    "random_admissible_action",
    "rirs_talk_to_right_specialists",
    "routellm",
    "self_resource_allocation",
    "separated_router_stopper",
    "solo",
    "verimap",
    "vmao",
    "zooter_adaptation",
)

_ENDPOINT_HIERARCHY = (
    "e2_randomized_executed_bundle_primary",
    "e3_equal_information_oacs_vs_full_parity_raw_router_conditional_on_e2",
    "e4_fresh_downstream_frontier_conditional_on_e1_e2_e3",
    "e1_predictive_support_noncausal_nonprimary",
)

_KILL_CHAIN = (
    "e1_failure_removes_predictive_support_and_blocks_e1_dependent_e4_without_rescuing_e2",
    "architecture_e2_nonpositive_nonestimable_unsupported_or_noncompliant_kills_causal_mechanism_and_iclr_main_oacs_thesis",
    "architecture_e3_null_or_parity_invalid_after_positive_e2_kills_oacs_method_and_iclr_main_claim",
    "architecture_failure_never_reclassified_as_jci_only_main_claim_and_no_cross_ontology_pooling_or_rescue",
    "only_narrower_jci_descriptive_and_randomized_executed_bundle_effect_reporting_may_remain_after_architecture_main_claim_kill",
    "architecture_main_claim_kill_forbids_flagship_replication_cross_domain_mechanism_main_and_oacs_main_survival",
    "jci_e2_nonpositive_nonestimable_unsupported_or_noncompliant_kills_causal_mechanism_and_iclr_main_oacs_thesis",
    "jci_e3_null_or_parity_invalid_after_positive_e2_kills_oacs_method_and_iclr_main_claim",
    "jci_failure_never_reclassified_as_generalization_only_and_no_cross_ontology_pooling_or_rescue",
    "only_narrower_architecture_descriptive_and_executed_bundle_effect_reporting_may_remain",
    "e1_e2_e3_pass_e4_failure_kills_deployable_frontier_claim",
)

_FROZEN_ONE_THESIS_SCALARS = (
    ("thesis_id", "residual_obligation_x_actually_executed_complete_bundle"),
    ("treatment_definition", "residual_obligation_status_x_actually_executed_complete_bundle"),
    ("architecture_domain_role", "flagship_primary_domain"),
    ("jci_domain_role", "independent_e2_e3_replication_no_pooling"),
    (
        "architecture_ontology_clause",
        "architecture_site_cluster_flagship_residual_obligation_x_actually_executed_complete_bundle",
    ),
    (
        "jci_ontology_clause",
        "jci_project_cluster_independent_e2_e3_resource_obligation_replication_no_pooling",
    ),
    ("cross_domain_pooling", "forbidden"),
    ("cats_role", "negative_motivation_and_baseline_only"),
    ("e1_role", "predictive_noncausal_nonprimary_support"),
    ("e2_role", "randomized_executed_complete_bundle_primary_mechanism"),
    (
        "e2_primary_endpoint",
        "blind_terminal_obligation_closure_quality_present_high_minus_low_minus_absent_high_minus_low",
    ),
    ("e3_role", "equal_information_policy_consequence_conditional_on_e2"),
    ("e3_primary_comparator", "full_parity_raw_router"),
    (
        "retrospective_oracle_role",
        "post_outcome_descriptive_upper_bound_separate_not_deployable",
    ),
    ("e4_role", "fresh_downstream_deployable_frontier_after_e1_e2_e3"),
)

# Deliberately not consulted by validators.  It exists only so tests can prove
# that replacing a mutable module binding cannot change the frozen contract.
_ONE_THESIS_SCALARS = dict(_FROZEN_ONE_THESIS_SCALARS)


def _fail(message: str) -> None:
    raise ExternalAuthorityAcquisitionError(message)


def _validate_json_native(value: Any, *, label: str = "value") -> None:
    value_type = type(value)
    if value is None or value_type in (bool, str):
        return
    if value_type is int:
        return
    if value_type is float:
        if not math.isfinite(value) or (value == 0.0 and math.copysign(1.0, value) < 0):
            _fail(f"{label} must be finite canonical JSON")
        return
    if value_type is list:
        for index, item in enumerate(value):
            _validate_json_native(item, label=f"{label}[{index}]")
        return
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                _fail(f"{label} keys must be native strings")
            _validate_json_native(item, label=f"{label}.{key}")
        return
    _fail(f"{label} must use exact JSON-native types")


def _canonical_json(value: Any) -> str:
    _validate_json_native(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise ExternalAuthorityAcquisitionError("value is not canonical JSON") from error


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _strict_json_loads(text: str) -> dict[str, Any]:
    if type(text) is not str or text.startswith("\ufeff"):
        _fail("JSON must be native UTF-8 text without BOM")

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _fail("duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        _fail(f"nonfinite JSON constant: {value}")

    try:
        parsed = json.loads(text, object_pairs_hook=pairs_hook, parse_constant=reject_constant)
    except ExternalAuthorityAcquisitionError:
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ExternalAuthorityAcquisitionError("malformed JSON") from error
    if type(parsed) is not dict:
        _fail("record JSON must be an object")
    _validate_json_native(parsed)
    if text != _canonical_json(parsed):
        _fail("JSON is not canonical")
    return parsed


def _expect_dict(value: Any, names: tuple[str, ...]) -> dict[str, Any]:
    if type(value) is not dict:
        _fail("record must be an exact native dict")
    if tuple(value) != names:
        _fail("record key order or key set mismatch")
    _validate_json_native(value)
    return value


def _expect_str(value: Any, label: str, *, exact: str | None = None) -> str:
    if type(value) is not str or value == "":
        _fail(f"{label} must be a nonempty native string")
    if exact is not None and value != exact:
        _fail(f"{label} mismatch")
    return value


def _expect_ascii(value: Any, label: str) -> str:
    result = _expect_str(value, label)
    if any(ord(character) < 32 or ord(character) > 126 for character in result):
        _fail(f"{label} must be printable ASCII")
    return result


def _expect_digest(value: Any, label: str) -> str:
    result = _expect_str(value, label)
    if _HEX64_RE.fullmatch(result) is None:
        _fail(f"{label} must be a lowercase SHA-256 digest")
    return result


def _expect_int(value: Any, label: str, *, minimum: int = 0, exact: int | None = None) -> int:
    if type(value) is not int or value < minimum:
        _fail(f"{label} must be an exact native integer")
    if exact is not None and value != exact:
        _fail(f"{label} mismatch")
    return value


def _expect_bool(value: Any, label: str, *, exact: bool | None = None) -> bool:
    if type(value) is not bool:
        _fail(f"{label} must be an exact native boolean")
    if exact is not None and value is not exact:
        _fail(f"{label} mismatch")
    return value


def _expect_utc(value: Any, label: str) -> str:
    result = _expect_ascii(value, label)
    if _UTC_RE.fullmatch(result) is None:
        _fail(f"{label} must use exact UTC-Z grammar")
    try:
        datetime.strptime(result, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise ExternalAuthorityAcquisitionError(f"{label} is not a valid UTC time") from error
    return result


def _expect_list(value: Any, label: str) -> list[Any]:
    if type(value) is not list:
        _fail(f"{label} must be an exact native JSON array")
    return value


def _expect_ascii_array(
    value: Any,
    label: str,
    *,
    nonempty: bool = False,
    sorted_unique: bool = True,
) -> tuple[str, ...]:
    items = _expect_list(value, label)
    converted = tuple(_expect_ascii(item, f"{label} item") for item in items)
    if nonempty and not converted:
        _fail(f"{label} must be nonempty")
    if sorted_unique and tuple(sorted(set(converted), key=lambda item: item.encode("utf-8"))) != converted:
        _fail(f"{label} must be byte-sorted and unique")
    return converted


def _expect_digest_array(
    value: Any,
    label: str,
    *,
    nonempty: bool = False,
    sorted_unique: bool = True,
) -> tuple[str, ...]:
    items = _expect_list(value, label)
    converted = tuple(_expect_digest(item, f"{label} item") for item in items)
    if nonempty and not converted:
        _fail(f"{label} must be nonempty")
    if sorted_unique and tuple(sorted(set(converted))) != converted:
        _fail(f"{label} must be sorted and unique")
    return converted


def _verify_self_hash(payload: dict[str, Any], self_field: str) -> None:
    supplied = _expect_digest(payload[self_field], self_field)
    expected = _sha256_json({key: value for key, value in payload.items() if key != self_field})
    if supplied != expected:
        _fail(f"{self_field} mismatch")


def _to_json_value(value: Any) -> Any:
    if isinstance(value, _SealedRecord):
        return value.to_dict()
    if type(value) is tuple:
        return [_to_json_value(item) for item in value]
    return value


def _contains_token(value: Any, token: str) -> bool:
    if type(value) is str:
        return token in value
    if type(value) in (tuple, list):
        return any(_contains_token(item, token) for item in value)
    if type(value) is dict:
        return any(_contains_token(key, token) or _contains_token(item, token) for key, item in value.items())
    return False


def _contains_forbidden_task_namespace(value: Any) -> bool:
    if type(value) is str:
        lowered = value.lower()
        compact = lowered.replace("-", "").replace("_", "").replace(" ", "")
        return "task6" in compact or "task7" in compact
    if type(value) in (tuple, list):
        return any(_contains_forbidden_task_namespace(item) for item in value)
    if type(value) is dict:
        return any(
            _contains_forbidden_task_namespace(key) or _contains_forbidden_task_namespace(item)
            for key, item in value.items()
        )
    return False


def _validate_upstream_forbidden_scope(
    payload: dict[str, Any],
    *,
    legacy_allowed_fields: tuple[str, ...] = (),
    task_namespace_allowed_fields: tuple[str, ...] = (),
) -> None:
    """Reject downstream/legacy tokens with the two frozen field exceptions."""

    for name, value in payload.items():
        for digest in _FORBIDDEN_DOWNSTREAM_SHAS:
            if _contains_token(value, digest):
                _fail(f"{name} contains forbidden downstream dependency")
        if name not in legacy_allowed_fields and _contains_token(value, _LEGACY_SHA):
            _fail(f"{name} contains forbidden legacy dependency")
        if name not in task_namespace_allowed_fields and _contains_forbidden_task_namespace(value):
            _fail(f"{name} contains forbidden Task6/Task7 dependency")


class _SealedRecordMeta(type):
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        del cls, args, kwargs
        raise TypeError("record constructors are disabled; use validated classmethods")


class _SealedRecord(metaclass=_SealedRecordMeta):
    __slots__ = ()
    _SELF_FIELD: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_SealedRecord,):
            raise TypeError("record classes are sealed")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Any:
        names = tuple(field.name for field in fields(cls))
        payload = _expect_dict(value, names)
        normalized = cls._normalize(payload)
        _verify_self_hash(payload, cls._SELF_FIELD)
        instance = object.__new__(cls)
        for name in names:
            object.__setattr__(instance, name, normalized[name])
        return instance

    @classmethod
    def from_json(cls, text: str) -> Any:
        parsed = _strict_json_loads(text)
        names = tuple(field.name for field in fields(cls))
        if set(parsed) != set(names):
            _fail("record JSON key set mismatch")
        ordered = {name: parsed[name] for name in names}
        instance = cls.from_dict(ordered)
        if text != instance.to_json():
            _fail("record JSON is not canonical")
        return instance

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        try:
            payload = {
                field.name: _to_json_value(object.__getattribute__(self, field.name))
                for field in fields(type(self))
            }
        except (AttributeError, TypeError) as error:
            raise ExternalAuthorityAcquisitionError("invalid record construction") from error
        # Revalidate every serialization so object.__new__ and mutation bypasses fail closed.
        type(self).from_dict(payload)
        return payload

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())


@dataclass(frozen=True, slots=True, init=False)
class _ExternalCanonicalSignatureEnvelopeVNext(_SealedRecord):
    schema_version: str
    envelope_version: int
    artifact_role: str
    artifact_schema_version: str
    artifact_logical_id: str
    artifact_file_byte_count: int
    artifact_file_sha256: str
    detached_message_domain: str
    signature_algorithm: str
    signing_key_id: str
    signing_public_key_member_identity: str
    signing_public_key_byte_count: int
    signing_public_key_sha256: str
    detached_signature_member_identity: str
    detached_signature_byte_count: int
    detached_signature_sha256: str
    external_verifier_package_identity: str
    external_verifier_package_version: str
    external_verifier_executable_sha256: str
    rotation_provenance_member_identity: str
    rotation_provenance_sha256: str
    predecessor_envelope_sha256s: tuple[str, ...]
    envelope_sha256: str
    _SELF_FIELD = "envelope_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(payload)
        role = _expect_ascii(payload["artifact_role"], "artifact_role")
        if role not in _ROLE_DOMAINS:
            _fail("artifact_role mismatch")
        _expect_str(
            payload["schema_version"],
            "schema_version",
            exact="ace.iclr2027.external_canonical_signature_envelope.vnext",
        )
        _expect_int(payload["envelope_version"], "envelope_version", minimum=1)
        _expect_str(payload["artifact_schema_version"], "artifact_schema_version", exact=_ROLE_SCHEMAS[role])
        _expect_ascii(payload["artifact_logical_id"], "artifact_logical_id")
        _expect_int(payload["artifact_file_byte_count"], "artifact_file_byte_count", minimum=1)
        _expect_digest(payload["artifact_file_sha256"], "artifact_file_sha256")
        _expect_str(payload["detached_message_domain"], "detached_message_domain", exact=_ROLE_DOMAINS[role])
        _expect_str(payload["signature_algorithm"], "signature_algorithm", exact="ed25519")
        for name in (
            "signing_key_id",
            "signing_public_key_member_identity",
            "detached_signature_member_identity",
            "external_verifier_package_identity",
            "external_verifier_package_version",
            "rotation_provenance_member_identity",
        ):
            _expect_ascii(payload[name], name)
        _expect_int(payload["signing_public_key_byte_count"], "signing_public_key_byte_count", exact=32)
        _expect_int(payload["detached_signature_byte_count"], "detached_signature_byte_count", exact=64)
        for name in (
            "signing_public_key_sha256",
            "detached_signature_sha256",
            "external_verifier_executable_sha256",
            "rotation_provenance_sha256",
            "envelope_sha256",
        ):
            _expect_digest(payload[name], name)
        members = (
            payload["signing_public_key_member_identity"],
            payload["detached_signature_member_identity"],
            payload["rotation_provenance_member_identity"],
        )
        if len(set(members)) != len(members):
            _fail("envelope member identities must be distinct")
        predecessors = _expect_digest_array(payload["predecessor_envelope_sha256s"], "predecessor_envelope_sha256s")
        result = dict(payload)
        result["predecessor_envelope_sha256s"] = predecessors
        return result


@dataclass(frozen=True, slots=True, init=False)
class _ExternalVNextArtifactPinVNext(_SealedRecord):
    schema_version: str
    pin_version: int
    artifact_role: str
    expected_artifact_file_byte_count: int
    expected_artifact_file_sha256: str
    expected_signature_envelope_file_byte_count: int
    expected_signature_envelope_file_sha256: str
    external_verifier_package_identity: str
    external_verifier_package_version: str
    external_verifier_executable_member_identity: str
    external_verifier_executable_sha256: str
    external_platform_signature_member_identity: str
    external_platform_signature_sha256: str
    signing_key_id: str
    signing_public_key_member_identity: str
    signing_public_key_byte_count: int
    signing_public_key_sha256: str
    detached_signature_member_identity: str
    detached_signature_byte_count: int
    detached_signature_sha256: str
    detached_message_domain: str
    rotation_provenance_member_identity: str
    rotation_provenance_sha256: str
    predecessor_artifact_pin_sha256s: tuple[str, ...]
    pin_sha256: str
    _SELF_FIELD = "pin_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(payload)
        role = _expect_ascii(payload["artifact_role"], "artifact_role")
        if role not in _ROLE_DOMAINS:
            _fail("artifact_role mismatch")
        _expect_str(
            payload["schema_version"],
            "schema_version",
            exact="ace.iclr2027.external_vnext_artifact_pin.vnext",
        )
        _expect_int(payload["pin_version"], "pin_version", minimum=1)
        for name in ("expected_artifact_file_byte_count", "expected_signature_envelope_file_byte_count"):
            _expect_int(payload[name], name, minimum=1)
        for name in (
            "expected_artifact_file_sha256",
            "expected_signature_envelope_file_sha256",
            "external_verifier_executable_sha256",
            "external_platform_signature_sha256",
            "signing_public_key_sha256",
            "detached_signature_sha256",
            "rotation_provenance_sha256",
            "pin_sha256",
        ):
            _expect_digest(payload[name], name)
        for name in (
            "external_verifier_package_identity",
            "external_verifier_package_version",
            "external_verifier_executable_member_identity",
            "external_platform_signature_member_identity",
            "signing_key_id",
            "signing_public_key_member_identity",
            "detached_signature_member_identity",
            "rotation_provenance_member_identity",
        ):
            _expect_ascii(payload[name], name)
        _expect_int(payload["signing_public_key_byte_count"], "signing_public_key_byte_count", exact=32)
        _expect_int(payload["detached_signature_byte_count"], "detached_signature_byte_count", exact=64)
        _expect_str(payload["detached_message_domain"], "detached_message_domain", exact=_ROLE_DOMAINS[role])
        members = tuple(
            payload[name]
            for name in (
                "external_verifier_executable_member_identity",
                "external_platform_signature_member_identity",
                "signing_public_key_member_identity",
                "detached_signature_member_identity",
                "rotation_provenance_member_identity",
            )
        )
        if len(set(members)) != len(members):
            _fail("pin member identities must be pairwise distinct")
        predecessors = _expect_digest_array(payload["predecessor_artifact_pin_sha256s"], "predecessor_artifact_pin_sha256s")
        result = dict(payload)
        result["predecessor_artifact_pin_sha256s"] = predecessors
        return result


@dataclass(frozen=True, slots=True, init=False)
class _CustodianSearchRowVNext(_SealedRecord):
    custodian_id: str
    custodian_role: str
    contacted_at_utc: str
    completed_at_utc: str
    searched_store_ids: tuple[str, ...]
    searched_object_version_keys: tuple[str, ...]
    search_method: str
    search_result: str
    approval_member_identity: str
    approval_file_sha256: str
    row_sha256: str
    _SELF_FIELD = "row_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(payload)
        for name in ("custodian_id", "custodian_role", "approval_member_identity"):
            _expect_ascii(payload[name], name)
        contacted = _expect_utc(payload["contacted_at_utc"], "contacted_at_utc")
        completed = _expect_utc(payload["completed_at_utc"], "completed_at_utc")
        if completed < contacted:
            _fail("custodian completion precedes contact")
        stores = _expect_ascii_array(payload["searched_store_ids"], "searched_store_ids", nonempty=True)
        versions = _expect_ascii_array(
            payload["searched_object_version_keys"],
            "searched_object_version_keys",
            nonempty=True,
        )
        _expect_str(payload["search_method"], "search_method", exact="exhaustive_immutable_version_search")
        _expect_str(payload["search_result"], "search_result", exact="exact_raw_bytes_not_found")
        _expect_digest(payload["approval_file_sha256"], "approval_file_sha256")
        _expect_digest(payload["row_sha256"], "row_sha256")
        result = dict(payload)
        result["searched_store_ids"] = stores
        result["searched_object_version_keys"] = versions
        return result


@dataclass(frozen=True, slots=True, init=False)
class _StoreSearchRowVNext(_SealedRecord):
    store_id: str
    owner_custodian_id: str
    store_kind: str
    immutable_store_identity: str
    store_version: str
    searched_at_utc: str
    search_scope: str
    all_known_namespaces_examined: bool
    evidence_member_identities: tuple[str, ...]
    search_result: str
    row_sha256: str
    _SELF_FIELD = "row_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(payload)
        for name in ("store_id", "owner_custodian_id", "immutable_store_identity", "store_version"):
            _expect_ascii(payload[name], name)
        _expect_str(payload["store_kind"], "store_kind", exact="immutable_object_store")
        _expect_utc(payload["searched_at_utc"], "searched_at_utc")
        _expect_str(payload["search_scope"], "search_scope", exact="all_known_namespaces_and_versions")
        _expect_bool(payload["all_known_namespaces_examined"], "all_known_namespaces_examined", exact=True)
        evidence = _expect_ascii_array(payload["evidence_member_identities"], "evidence_member_identities", nonempty=True)
        _expect_str(payload["search_result"], "search_result", exact="exact_raw_bytes_not_found")
        _expect_digest(payload["row_sha256"], "row_sha256")
        result = dict(payload)
        result["evidence_member_identities"] = evidence
        return result


@dataclass(frozen=True, slots=True, init=False)
class _ObjectVersionSearchRowVNext(_SealedRecord):
    object_version_key: str
    store_id: str
    immutable_object_identity: str
    immutable_object_version: str
    examined_at_utc: str
    raw_object_available: bool
    candidate_file_count: int
    candidate_file_sha256s: tuple[str, ...]
    evidence_member_identities: tuple[str, ...]
    search_result: str
    row_sha256: str
    _SELF_FIELD = "row_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(payload)
        for name in ("object_version_key", "store_id", "immutable_object_identity", "immutable_object_version"):
            _expect_ascii(payload[name], name)
        _expect_utc(payload["examined_at_utc"], "examined_at_utc")
        _expect_bool(payload["raw_object_available"], "raw_object_available", exact=False)
        count = _expect_int(payload["candidate_file_count"], "candidate_file_count")
        candidates = _expect_digest_array(payload["candidate_file_sha256s"], "candidate_file_sha256s")
        if count != len(candidates):
            _fail("candidate file count mismatch")
        evidence = _expect_ascii_array(payload["evidence_member_identities"], "evidence_member_identities", nonempty=True)
        _expect_str(payload["search_result"], "search_result", exact="exact_raw_bytes_not_found")
        _expect_digest(payload["row_sha256"], "row_sha256")
        result = dict(payload)
        result["candidate_file_sha256s"] = candidates
        result["evidence_member_identities"] = evidence
        return result


@dataclass(frozen=True, slots=True, init=False)
class _CustodyEvidenceRowVNext(_SealedRecord):
    evidence_index: int
    occurred_at_utc: str
    custodian_identity: str
    immutable_store_identity: str
    immutable_object_identity: str
    immutable_object_version: str
    evidence_member_identity: str
    evidence_file_sha256: str
    evidence_file_byte_count: int
    row_sha256: str
    _SELF_FIELD = "row_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(payload)
        _expect_int(payload["evidence_index"], "evidence_index")
        _expect_utc(payload["occurred_at_utc"], "occurred_at_utc")
        for name in (
            "custodian_identity",
            "immutable_store_identity",
            "immutable_object_identity",
            "immutable_object_version",
            "evidence_member_identity",
        ):
            _expect_ascii(payload[name], name)
        _expect_digest(payload["evidence_file_sha256"], "evidence_file_sha256")
        _expect_int(payload["evidence_file_byte_count"], "evidence_file_byte_count", minimum=1)
        _expect_digest(payload["row_sha256"], "row_sha256")
        return dict(payload)


def _nested_records(
    value: Any,
    label: str,
    record_type: type[_SealedRecord],
    *,
    nonempty: bool = True,
) -> tuple[_SealedRecord, ...]:
    values = _expect_list(value, label)
    if nonempty and not values:
        _fail(f"{label} must be nonempty")
    result = []
    for item in values:
        if type(item) is not dict:
            _fail(f"{label} contains a foreign record")
        names = tuple(field.name for field in fields(record_type))
        if set(item) != set(names):
            _fail(f"{label} nested key set mismatch")
        result.append(record_type.from_dict({name: item[name] for name in names}))
    return tuple(result)


@dataclass(frozen=True, slots=True, init=False)
class _LegacySearchImpossibilityDeclarationVNext(_SealedRecord):
    schema_version: str
    declaration_version: int
    declaration_logical_id: str
    legacy_snapshot_logical_id: str
    expected_legacy_raw_sha256: str
    search_opened_at_utc: str
    search_closed_at_utc: str
    known_custodian_ids: tuple[str, ...]
    known_store_ids: tuple[str, ...]
    known_object_version_keys: tuple[str, ...]
    custodian_search_rows: tuple[_CustodianSearchRowVNext, ...]
    store_search_rows: tuple[_StoreSearchRowVNext, ...]
    object_version_search_rows: tuple[_ObjectVersionSearchRowVNext, ...]
    custody_evidence_rows: tuple[_CustodyEvidenceRowVNext, ...]
    unsearched_custodian_ids: tuple[str, ...]
    unsearched_store_ids: tuple[str, ...]
    unsearched_object_version_keys: tuple[str, ...]
    legacy_recovery_status: str
    legacy_continuity: bool
    legacy_equivalence: bool
    responsible_migration_owner_identity: str
    responsible_owner_approval_member_identity: str
    responsible_owner_approval_sha256: str
    custodian_approval_member_sha256s: tuple[str, ...]
    declaration_sha256: str
    _SELF_FIELD = "declaration_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(
            payload,
            legacy_allowed_fields=("expected_legacy_raw_sha256",),
        )
        _expect_str(
            payload["schema_version"],
            "schema_version",
            exact="ace.iclr2027.legacy_search_impossibility_declaration.vnext",
        )
        _expect_int(payload["declaration_version"], "declaration_version", minimum=1)
        for name in (
            "declaration_logical_id",
            "legacy_snapshot_logical_id",
            "responsible_migration_owner_identity",
            "responsible_owner_approval_member_identity",
        ):
            _expect_ascii(payload[name], name)
        _expect_str(payload["expected_legacy_raw_sha256"], "expected_legacy_raw_sha256", exact=_LEGACY_SHA)
        opened = _expect_utc(payload["search_opened_at_utc"], "search_opened_at_utc")
        closed = _expect_utc(payload["search_closed_at_utc"], "search_closed_at_utc")
        if closed <= opened:
            _fail("search close must follow open")
        known_custodians = _expect_ascii_array(payload["known_custodian_ids"], "known_custodian_ids", nonempty=True)
        known_stores = _expect_ascii_array(payload["known_store_ids"], "known_store_ids", nonempty=True)
        known_versions = _expect_ascii_array(
            payload["known_object_version_keys"],
            "known_object_version_keys",
            nonempty=True,
        )
        custodians = _nested_records(payload["custodian_search_rows"], "custodian_search_rows", _CustodianSearchRowVNext)
        stores = _nested_records(payload["store_search_rows"], "store_search_rows", _StoreSearchRowVNext)
        objects = _nested_records(
            payload["object_version_search_rows"],
            "object_version_search_rows",
            _ObjectVersionSearchRowVNext,
        )
        evidence = _nested_records(payload["custody_evidence_rows"], "custody_evidence_rows", _CustodyEvidenceRowVNext)
        for name in ("unsearched_custodian_ids", "unsearched_store_ids", "unsearched_object_version_keys"):
            if _expect_ascii_array(payload[name], name):
                _fail(f"{name} must be empty")
        _expect_str(
            payload["legacy_recovery_status"],
            "legacy_recovery_status",
            exact="exhaustive_search_completed_exact_raw_bytes_not_recovered",
        )
        _expect_bool(payload["legacy_continuity"], "legacy_continuity", exact=False)
        _expect_bool(payload["legacy_equivalence"], "legacy_equivalence", exact=False)
        _expect_digest(payload["responsible_owner_approval_sha256"], "responsible_owner_approval_sha256")
        approvals = _expect_digest_array(
            payload["custodian_approval_member_sha256s"],
            "custodian_approval_member_sha256s",
            nonempty=True,
        )
        if known_custodians != tuple(row.custodian_id for row in custodians):
            _fail("custodian census mismatch")
        if known_stores != tuple(row.store_id for row in stores):
            _fail("store census mismatch")
        if known_versions != tuple(row.object_version_key for row in objects):
            _fail("object-version census mismatch")
        if approvals != tuple(sorted((row.approval_file_sha256 for row in custodians))):
            _fail("custodian approval census mismatch")
        if tuple(row.evidence_index for row in evidence) != tuple(range(len(evidence))):
            _fail("evidence indices must be contiguous")
        if tuple(row.occurred_at_utc for row in evidence) != tuple(sorted(row.occurred_at_utc for row in evidence)):
            _fail("evidence times must be ordered")
        evidence_members = {row.evidence_member_identity for row in evidence}
        if len(evidence_members) != len(evidence) or any(
            set(row.evidence_member_identities) - evidence_members for row in stores + objects
        ):
            _fail("evidence join mismatch")
        custodian_ids = set(known_custodians)
        store_ids = set(known_stores)
        if any(row.owner_custodian_id not in custodian_ids for row in stores):
            _fail("store owner join mismatch")
        if any(row.store_id not in store_ids for row in objects):
            _fail("object store join mismatch")
        stores_by_id = {row.store_id: row for row in stores}
        physical_evidence_joins = {
            (
                stores_by_id[row.store_id].owner_custodian_id,
                stores_by_id[row.store_id].immutable_store_identity,
                row.immutable_object_identity,
                row.immutable_object_version,
            )
            for row in objects
        }
        for row in evidence:
            physical_join = (
                row.custodian_identity,
                row.immutable_store_identity,
                row.immutable_object_identity,
                row.immutable_object_version,
            )
            if physical_join not in physical_evidence_joins:
                _fail("evidence physical identity join mismatch")
        objects_by_store: dict[str, tuple[_ObjectVersionSearchRowVNext, ...]] = {
            store_id: tuple(row for row in objects if row.store_id == store_id)
            for store_id in known_stores
        }
        for store in stores:
            expected_store_evidence = tuple(
                sorted(
                    (
                        row.evidence_member_identity
                        for row in evidence
                        if row.custodian_identity == store.owner_custodian_id
                        and row.immutable_store_identity == store.immutable_store_identity
                    ),
                    key=lambda item: item.encode("utf-8"),
                )
            )
            if not expected_store_evidence or store.evidence_member_identities != expected_store_evidence:
                _fail("store evidence ownership bijection mismatch")
            for object_row in objects_by_store[store.store_id]:
                expected_object_evidence = tuple(
                    sorted(
                        (
                            row.evidence_member_identity
                            for row in evidence
                            if row.custodian_identity == store.owner_custodian_id
                            and row.immutable_store_identity == store.immutable_store_identity
                            and row.immutable_object_identity == object_row.immutable_object_identity
                            and row.immutable_object_version == object_row.immutable_object_version
                        ),
                        key=lambda item: item.encode("utf-8"),
                    )
                )
                if (
                    not expected_object_evidence
                    or object_row.evidence_member_identities != expected_object_evidence
                ):
                    _fail("object evidence ownership bijection mismatch")
        for row in custodians:
            expected_stores = tuple(store.store_id for store in stores if store.owner_custodian_id == row.custodian_id)
            expected_versions = tuple(
                object_row.object_version_key
                for object_row in objects
                if stores_by_id[object_row.store_id].owner_custodian_id == row.custodian_id
            )
            if row.searched_store_ids != expected_stores or row.searched_object_version_keys != expected_versions:
                _fail("custodian search ownership bijection mismatch")
            if not (opened <= row.contacted_at_utc <= row.completed_at_utc <= closed):
                _fail("custodian time outside search window")
        if any(not (opened <= row.searched_at_utc <= closed) for row in stores):
            _fail("store time outside search window")
        if any(not (opened <= row.examined_at_utc <= closed) for row in objects):
            _fail("object time outside search window")
        if any(not (opened <= row.occurred_at_utc <= closed) for row in evidence):
            _fail("evidence time outside search window")
        payload_without_expected = {
            key: value
            for key, value in payload.items()
            if key not in ("expected_legacy_raw_sha256", "declaration_sha256")
        }
        if _contains_token(payload_without_expected, _LEGACY_SHA):
            _fail("legacy digest is declaration-target only")
        if any(_contains_token(payload, digest) for digest in _FORBIDDEN_DOWNSTREAM_SHAS):
            _fail("downstream memory dependency forbidden")
        if _contains_forbidden_task_namespace(payload_without_expected):
            _fail("Task6/Task7 namespace dependency forbidden")
        _expect_digest(payload["declaration_sha256"], "declaration_sha256")
        result = dict(payload)
        result.update(
            {
                "known_custodian_ids": known_custodians,
                "known_store_ids": known_stores,
                "known_object_version_keys": known_versions,
                "custodian_search_rows": custodians,
                "store_search_rows": stores,
                "object_version_search_rows": objects,
                "custody_evidence_rows": evidence,
                "unsearched_custodian_ids": (),
                "unsearched_store_ids": (),
                "unsearched_object_version_keys": (),
                "custodian_approval_member_sha256s": approvals,
            }
        )
        return result


@dataclass(frozen=True, slots=True, init=False)
class _OneThesisContractVNext(_SealedRecord):
    schema_version: str
    contract_version: int
    contract_logical_id: str
    allowed_upstream_authority_sha256s: tuple[str, ...]
    task5_brief_sha256: str
    task5_analysis_plan_sha256: str
    task5_review_sha256: str
    external_scientist_identity: str
    external_scientist_approval_member_identity: str
    external_scientist_approval_sha256: str
    legacy_continuity: bool
    legacy_equivalence: bool
    thesis_id: str
    treatment_definition: str
    architecture_domain_role: str
    jci_domain_role: str
    architecture_ontology_clause: str
    jci_ontology_clause: str
    cross_domain_pooling: str
    cats_role: str
    e1_role: str
    e2_role: str
    e2_primary_endpoint: str
    e3_role: str
    e3_primary_comparator: str
    e3_mandatory_policy_ids: tuple[str, ...]
    retrospective_oracle_role: str
    e4_role: str
    endpoint_hierarchy: tuple[str, ...]
    kill_chain: tuple[str, ...]
    contract_sha256: str
    _SELF_FIELD = "contract_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any], frozen_scalars: tuple[tuple[str, str], ...] = _FROZEN_ONE_THESIS_SCALARS) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(payload)
        _expect_str(payload["schema_version"], "schema_version", exact="ace.iclr2027.one_thesis_contract.vnext")
        _expect_int(payload["contract_version"], "contract_version", minimum=1)
        for name in (
            "contract_logical_id",
            "external_scientist_identity",
            "external_scientist_approval_member_identity",
        ):
            _expect_ascii(payload[name], name)
        authorities = _expect_digest_array(
            payload["allowed_upstream_authority_sha256s"],
            "allowed_upstream_authority_sha256s",
            nonempty=True,
        )
        if authorities != _TASK5_PINS:
            _fail("Task5 authority set mismatch")
        for name, expected in (
            ("task5_brief_sha256", _TASK5_BRIEF_SHA),
            ("task5_analysis_plan_sha256", _TASK5_ANALYSIS_SHA),
            ("task5_review_sha256", _TASK5_REVIEW_SHA),
        ):
            _expect_str(payload[name], name, exact=expected)
        _expect_digest(payload["external_scientist_approval_sha256"], "external_scientist_approval_sha256")
        _expect_bool(payload["legacy_continuity"], "legacy_continuity", exact=False)
        _expect_bool(payload["legacy_equivalence"], "legacy_equivalence", exact=False)
        for name, expected in frozen_scalars:
            _expect_str(payload[name], name, exact=expected)
        policies = _expect_ascii_array(payload["e3_mandatory_policy_ids"], "e3_mandatory_policy_ids", nonempty=True)
        hierarchy = _expect_ascii_array(
            payload["endpoint_hierarchy"],
            "endpoint_hierarchy",
            nonempty=True,
            sorted_unique=False,
        )
        kill_chain = _expect_ascii_array(
            payload["kill_chain"],
            "kill_chain",
            nonempty=True,
            sorted_unique=False,
        )
        if policies != _POLICY_IDS or hierarchy != _ENDPOINT_HIERARCHY or kill_chain != _KILL_CHAIN:
            _fail("one-thesis roster or hierarchy mismatch")
        forbidden = (_LEGACY_SHA,) + _FORBIDDEN_DOWNSTREAM_SHAS
        if any(_contains_token({key: value for key, value in payload.items() if key != "contract_sha256"}, digest) for digest in forbidden):
            _fail("forbidden legacy or downstream dependency")
        if _contains_forbidden_task_namespace(
            {key: value for key, value in payload.items() if key != "contract_sha256"}
        ):
            _fail("Task6/Task7 namespace dependency forbidden")
        _expect_digest(payload["contract_sha256"], "contract_sha256")
        result = dict(payload)
        result["allowed_upstream_authority_sha256s"] = authorities
        result["e3_mandatory_policy_ids"] = policies
        result["endpoint_hierarchy"] = hierarchy
        result["kill_chain"] = kill_chain
        return result


@dataclass(frozen=True, slots=True, init=False)
class _NewUpstreamScientificSnapshotVNext(_SealedRecord):
    schema_version: str
    snapshot_version: int
    snapshot_logical_id: str
    migration_kind: str
    legacy_search_declaration_file_sha256: str
    legacy_search_declaration_sha256: str
    one_thesis_contract_file_sha256: str
    one_thesis_contract_sha256: str
    allowed_upstream_authority_sha256s: tuple[str, ...]
    external_scientist_approval_sha256: str
    legacy_continuity: bool
    legacy_equivalence: bool
    snapshot_sha256: str
    _SELF_FIELD = "snapshot_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(payload)
        _expect_str(payload["schema_version"], "schema_version", exact="ace.iclr2027.new_upstream_scientific_snapshot.vnext")
        _expect_int(payload["snapshot_version"], "snapshot_version", minimum=1)
        _expect_ascii(payload["snapshot_logical_id"], "snapshot_logical_id")
        _expect_str(payload["migration_kind"], "migration_kind", exact="explicit_non_continuity_migration")
        for name in (
            "legacy_search_declaration_file_sha256",
            "legacy_search_declaration_sha256",
            "one_thesis_contract_file_sha256",
            "one_thesis_contract_sha256",
            "external_scientist_approval_sha256",
            "snapshot_sha256",
        ):
            _expect_digest(payload[name], name)
        authorities = _expect_digest_array(
            payload["allowed_upstream_authority_sha256s"],
            "allowed_upstream_authority_sha256s",
            nonempty=True,
        )
        if authorities != _TASK5_PINS:
            _fail("Task5 authority set mismatch")
        _expect_bool(payload["legacy_continuity"], "legacy_continuity", exact=False)
        _expect_bool(payload["legacy_equivalence"], "legacy_equivalence", exact=False)
        forbidden = (_LEGACY_SHA,) + _FORBIDDEN_DOWNSTREAM_SHAS
        if any(_contains_token({key: value for key, value in payload.items() if key != "snapshot_sha256"}, digest) for digest in forbidden):
            _fail("snapshot contains forbidden legacy/downstream dependency")
        if _contains_forbidden_task_namespace(
            {key: value for key, value in payload.items() if key != "snapshot_sha256"}
        ):
            _fail("snapshot contains Task6/Task7 dependency")
        result = dict(payload)
        result["allowed_upstream_authority_sha256s"] = authorities
        return result


_REVIEW_ROLES = tuple(sorted((
    "independent_science_migration_review",
    "independent_provenance_migration_review",
    "independent_security_migration_review",
)))


@dataclass(frozen=True, slots=True, init=False)
class _IndependentMigrationReviewVNext(_SealedRecord):
    schema_version: str
    review_role: str
    reviewed_declaration_file_sha256: str
    reviewed_declaration_sha256: str
    reviewed_one_thesis_contract_file_sha256: str
    reviewed_one_thesis_contract_sha256: str
    reviewed_snapshot_file_sha256: str
    reviewed_snapshot_sha256: str
    reviewer_identity: str
    reviewer_independent: bool
    reviewed_at_utc: str
    critical_count: int
    important_count: int
    minor_count: int
    verdict: str
    review_sha256: str
    _SELF_FIELD = "review_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(payload)
        _expect_str(payload["schema_version"], "schema_version", exact="ace.iclr2027.independent_migration_review.vnext")
        role = _expect_ascii(payload["review_role"], "review_role")
        if role not in _REVIEW_ROLES:
            _fail("review role mismatch")
        for name in (
            "reviewed_declaration_file_sha256",
            "reviewed_declaration_sha256",
            "reviewed_one_thesis_contract_file_sha256",
            "reviewed_one_thesis_contract_sha256",
            "reviewed_snapshot_file_sha256",
            "reviewed_snapshot_sha256",
            "review_sha256",
        ):
            _expect_digest(payload[name], name)
        _expect_ascii(payload["reviewer_identity"], "reviewer_identity")
        _expect_bool(payload["reviewer_independent"], "reviewer_independent", exact=True)
        _expect_utc(payload["reviewed_at_utc"], "reviewed_at_utc")
        for name in ("critical_count", "important_count", "minor_count"):
            _expect_int(payload[name], name, exact=0)
        _expect_str(payload["verdict"], "verdict", exact="approved")
        if any(_contains_token({key: value for key, value in payload.items() if key != "review_sha256"}, digest) for digest in _FORBIDDEN_DOWNSTREAM_SHAS):
            _fail("review contains forbidden downstream dependency")
        if _contains_forbidden_task_namespace(
            {key: value for key, value in payload.items() if key != "review_sha256"}
        ):
            _fail("review contains Task6/Task7 dependency")
        return dict(payload)


@dataclass(frozen=True, slots=True, init=False)
class _ProvenanceMigrationReceiptVNext(_SealedRecord):
    schema_version: str
    migration_version: int
    migration_logical_id: str
    legacy_search_declaration_file_sha256: str
    legacy_search_declaration_sha256: str
    legacy_search_declaration_signature_envelope_file_sha256: str
    legacy_search_declaration_signature_envelope_sha256: str
    legacy_search_declaration_pin_file_sha256: str
    legacy_search_declaration_pin_sha256: str
    one_thesis_contract_file_sha256: str
    one_thesis_contract_sha256: str
    one_thesis_contract_signature_envelope_file_sha256: str
    one_thesis_contract_signature_envelope_sha256: str
    one_thesis_contract_pin_file_sha256: str
    one_thesis_contract_pin_sha256: str
    new_snapshot_file_sha256: str
    new_snapshot_sha256: str
    new_snapshot_signature_envelope_file_sha256: str
    new_snapshot_signature_envelope_sha256: str
    new_snapshot_pin_file_sha256: str
    new_snapshot_pin_sha256: str
    independent_science_review_file_sha256: str
    independent_science_review_sha256: str
    independent_science_review_signature_envelope_file_sha256: str
    independent_science_review_signature_envelope_sha256: str
    independent_science_review_pin_file_sha256: str
    independent_science_review_pin_sha256: str
    independent_provenance_review_file_sha256: str
    independent_provenance_review_sha256: str
    independent_provenance_review_signature_envelope_file_sha256: str
    independent_provenance_review_signature_envelope_sha256: str
    independent_provenance_review_pin_file_sha256: str
    independent_provenance_review_pin_sha256: str
    independent_security_review_file_sha256: str
    independent_security_review_sha256: str
    independent_security_review_signature_envelope_file_sha256: str
    independent_security_review_signature_envelope_sha256: str
    independent_security_review_pin_file_sha256: str
    independent_security_review_pin_sha256: str
    legacy_continuity: bool
    legacy_equivalence: bool
    migration_status: str
    receipt_sha256: str
    _SELF_FIELD = "receipt_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _validate_upstream_forbidden_scope(
            payload,
            task_namespace_allowed_fields=("migration_status",),
        )
        _expect_str(payload["schema_version"], "schema_version", exact="ace.iclr2027.provenance_migration_receipt.vnext")
        _expect_int(payload["migration_version"], "migration_version", minimum=1)
        _expect_ascii(payload["migration_logical_id"], "migration_logical_id")
        for name, value in payload.items():
            if name.endswith("_sha256"):
                _expect_digest(value, name)
        _expect_bool(payload["legacy_continuity"], "legacy_continuity", exact=False)
        _expect_bool(payload["legacy_equivalence"], "legacy_equivalence", exact=False)
        _expect_str(
            payload["migration_status"],
            "migration_status",
            exact="reviewed_non_continuity_snapshot_ready_for_task6_vnext_authority",
        )
        forbidden = (_LEGACY_SHA,) + _FORBIDDEN_DOWNSTREAM_SHAS
        if any(_contains_token({key: value for key, value in payload.items() if key != "receipt_sha256"}, digest) for digest in forbidden):
            _fail("receipt contains forbidden legacy/downstream dependency")
        if _contains_forbidden_task_namespace(
            {
                key: value
                for key, value in payload.items()
                if key not in ("receipt_sha256", "migration_status")
            }
        ):
            _fail("receipt contains Task6/Task7 dependency")
        return dict(payload)


@dataclass(frozen=True, slots=True, init=False)
class _NegativeFixtureSpec(_SealedRecord):
    schema_version: str
    fixture_id: str
    category: str
    mutation_description: str
    required_outcome: str
    fixture_sha256: str
    _SELF_FIELD = "fixture_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        _expect_str(payload["schema_version"], "schema_version", exact="ace.iclr2027.external_authority_negative_fixture.v1")
        for name in ("fixture_id", "category", "mutation_description", "required_outcome"):
            _expect_ascii(payload[name], name)
        _expect_digest(payload["fixture_sha256"], "fixture_sha256")
        return dict(payload)


_REASON_CODES = (
    "actual_architecture_jci_rosters_missing",
    "external_launcher_root_capability_missing",
    "external_migration_receipt_missing",
    "external_one_thesis_contract_missing",
    "external_path_b_owner_signature_missing",
    "external_reviews_missing",
    "external_signatures_missing",
    "external_snapshot_missing",
    "legacy_search_declaration_missing",
    "operation_rate_manifest_missing",
    "paid_run_authorization_missing",
    "simulation_freeze_missing",
    "task6_vnext_authority_missing",
    "task6_vnext_implementation_missing",
    "task6_vnext_reviews_missing",
)

_COUNTER_FIELDS = (
    "external_artifact_count",
    "external_signature_count",
    "external_review_count",
    "task6_vnext_authority_count",
    "task6_vnext_implementation_count",
    "source_read_count",
    "data_read_count",
    "result_read_count",
    "rate_read_count",
    "simulation_draw_count",
    "model_call_count",
    "tool_call_count",
    "paid_call_count",
)


@dataclass(frozen=True, slots=True, init=False)
class _ExternalAuthorityAcquisitionResult(_SealedRecord):
    schema_version: str
    binding_brief_sha256: str
    science_review_sha256: str
    security_review_sha256: str
    selected_path: str
    authority_mode: str
    status: str
    reason_codes: tuple[str, ...]
    negative_fixture_registry_sha256: str
    external_artifact_count: int
    external_signature_count: int
    external_review_count: int
    task6_vnext_authority_count: int
    task6_vnext_implementation_count: int
    source_read_count: int
    data_read_count: int
    result_read_count: int
    rate_read_count: int
    simulation_draw_count: int
    model_call_count: int
    tool_call_count: int
    paid_call_count: int
    official_result_eligible: bool
    synthetic_only: bool
    result_sha256: str
    _SELF_FIELD = "result_sha256"

    @classmethod
    def _normalize(cls, payload: dict[str, Any]) -> dict[str, Any]:
        expected_scalars = (
            ("schema_version", "ace.iclr2027.external_authority_acquisition_result.v1"),
            ("binding_brief_sha256", "9323c725a7f7a0520fb6ad4f71657fae6808cc7fb6672f91c18f32e27f0b8a54"),
            ("science_review_sha256", "a42811069e45a34ba1cb70ffc90f6e5253e53954042e263356efffa424e67146"),
            ("security_review_sha256", "987c9e316e2c428fe2c0a6effc685ef0f46841ec72e6f462e3fae6194335b571"),
            ("selected_path", "path_b_user_approved_but_not_externally_authenticated"),
            ("authority_mode", "synthetic"),
            ("status", "no_go"),
        )
        for name, expected in expected_scalars:
            _expect_str(payload[name], name, exact=expected)
        reasons = _expect_ascii_array(payload["reason_codes"], "reason_codes", nonempty=True)
        if reasons != _REASON_CODES:
            _fail("reason code closure mismatch")
        _expect_digest(payload["negative_fixture_registry_sha256"], "negative_fixture_registry_sha256")
        if payload["negative_fixture_registry_sha256"] != _fixture_registry_sha256():
            _fail("negative fixture registry binding mismatch")
        for name in _COUNTER_FIELDS:
            _expect_int(payload[name], name, exact=0)
        _expect_bool(payload["official_result_eligible"], "official_result_eligible", exact=False)
        _expect_bool(payload["synthetic_only"], "synthetic_only", exact=True)
        _expect_digest(payload["result_sha256"], "result_sha256")
        result = dict(payload)
        result["reason_codes"] = reasons
        return result


_FIXTURE_ROWS = (
    ("migration_architecture_failure_downgraded_to_domain_local_only", "scientific_kill_chain", "Architecture E2 or E3 failure is downgraded to a domain-local issue", "reject_exact_architecture_main_claim_kill"),
    ("migration_architecture_failure_retains_jci_only_main_claim", "scientific_kill_chain", "Architecture failure retains a JCI-only ICLR-main claim", "reject_no_reclassification_or_rescue"),
    ("migration_architecture_survivor_boundary_swapped_or_omitted", "scientific_kill_chain", "Architecture and JCI survivor boundaries are swapped or omitted", "reject_exact_ordered_kill_chain"),
    ("migration_cats_contribution_upgrade", "scientific_role", "CATS is promoted from baseline-only motivation", "reject_exact_cats_role"),
    ("migration_claims_e774_continuity", "provenance_scope", "Migration asserts e774 continuity or equivalence", "reject_declaration_only_legacy_target"),
    ("migration_contains_task6_or_task7_dependency", "acyclicity", "Upstream migration inserts a Task6 or Task7 dependency", "reject_dependency_insertion_or_reverse_cycle"),
    ("migration_declaration_e774_missing_or_wrong", "provenance_scope", "Declaration omits or changes the searched e774 digest", "reject_legacy_search_declaration"),
    ("migration_derived_from_a10", "provenance_scope", "Migration derives from a downstream current-memory snapshot", "reject_downstream_memory_derivation"),
    ("migration_domain_pooling_or_jci_role_drift", "scientific_role", "JCI is pooled with Architecture or changes role", "reject_exact_domain_contract"),
    ("migration_endpoint_or_kill_chain_drift", "scientific_kill_chain", "Endpoint hierarchy or kill chain changes", "reject_exact_ordered_arrays"),
    ("migration_incomplete_search_or_owner", "search_closure", "Search census or responsible owner approval is incomplete", "reject_incomplete_signed_declaration"),
    ("migration_jci_failure_downgraded_to_generalization_only", "scientific_kill_chain", "JCI failure is downgraded while keeping the main claim", "reject_exact_jci_kill"),
    ("migration_mixed_schema", "schema", "A v1 or v3 object is mixed into a vNext position", "reject_version_mixing"),
    ("migration_ontology_kill_clause_swapped_or_omitted", "scientific_kill_chain", "Ontology-specific kill clauses are swapped or omitted", "reject_ontology_specific_contract"),
    ("migration_oracle_policy_upgrade", "scientific_role", "Retrospective oracle is promoted into the deployable roster", "reject_exact_separate_oracle_role"),
    ("migration_review_independence_caller_authored", "review_independence", "Caller boolean is used as independence evidence", "reject_caller_boolean_as_evidence"),
    ("migration_review_missing_foreign_or_swapped_role_domain", "review_independence", "Review is missing, foreign, or uses a swapped role domain", "reject_before_migration_receipt"),
    ("migration_review_owner_or_producer_signed", "review_independence", "Migration owner or producer signs a review", "reject_role_key_or_package_overlap"),
    ("migration_review_self_file_cycle", "acyclicity", "Review or receipt introduces a self-file reverse cycle", "reject_review_schema_or_reverse_cycle"),
    ("migration_review_shared_key_or_package", "review_independence", "Reviewers share a key or verifier package", "reject_pairwise_distinct_reviewer_authority"),
    ("migration_task6_plan_before_vnext_review", "chronology", "Task6 vNext planning occurs before required reviews", "reject_premature_task6_vnext"),
    ("migration_thesis_role_drift", "scientific_role", "One-thesis treatment or flagship role changes", "reject_exact_one_thesis_contract"),
    ("migration_unreviewed", "review_independence", "One or more migration reviews are absent or nonapproved", "no_go"),
    ("migration_workspace_signing", "trust_boundary", "Workspace key or signature is treated as external authority", "reject_workspace_signing"),
    ("paid_run_from_intake_checklist", "paid_boundary", "An intake checklist is upgraded to paid-run authorization", "no_go"),
    ("synthetic_fixture_upgraded_to_real", "synthetic_boundary", "Synthetic fixture is upgraded to real authority", "reject_synthetic_to_real_upgrade"),
)


def _fixture_record(row: tuple[str, str, str, str]) -> _NegativeFixtureSpec:
    fixture_id, category, description, outcome = row
    payload: dict[str, Any] = {
        "schema_version": "ace.iclr2027.external_authority_negative_fixture.v1",
        "fixture_id": fixture_id,
        "category": category,
        "mutation_description": description,
        "required_outcome": outcome,
    }
    payload["fixture_sha256"] = _sha256_json(payload)
    return _NegativeFixtureSpec.from_dict(payload)


_FIXTURE_REGISTRY = tuple(_fixture_record(row) for row in _FIXTURE_ROWS)


def negative_fixture_registry() -> tuple[_NegativeFixtureSpec, ...]:
    """Return immutable metadata for the exact negative-only fixture registry."""

    return _FIXTURE_REGISTRY


def _fixture_registry_sha256() -> str:
    return _sha256_json([item.to_dict() for item in _FIXTURE_REGISTRY])


def validate_synthetic_external_authority_acquisition() -> _ExternalAuthorityAcquisitionResult:
    """Return the deterministic current synthetic ``no_go`` result."""

    payload: dict[str, Any] = {
        "schema_version": "ace.iclr2027.external_authority_acquisition_result.v1",
        "binding_brief_sha256": "9323c725a7f7a0520fb6ad4f71657fae6808cc7fb6672f91c18f32e27f0b8a54",
        "science_review_sha256": "a42811069e45a34ba1cb70ffc90f6e5253e53954042e263356efffa424e67146",
        "security_review_sha256": "987c9e316e2c428fe2c0a6effc685ef0f46841ec72e6f462e3fae6194335b571",
        "selected_path": "path_b_user_approved_but_not_externally_authenticated",
        "authority_mode": "synthetic",
        "status": "no_go",
        "reason_codes": list(_REASON_CODES),
        "negative_fixture_registry_sha256": _fixture_registry_sha256(),
        "external_artifact_count": 0,
        "external_signature_count": 0,
        "external_review_count": 0,
        "task6_vnext_authority_count": 0,
        "task6_vnext_implementation_count": 0,
        "source_read_count": 0,
        "data_read_count": 0,
        "result_read_count": 0,
        "rate_read_count": 0,
        "simulation_draw_count": 0,
        "model_call_count": 0,
        "tool_call_count": 0,
        "paid_call_count": 0,
        "official_result_eligible": False,
        "synthetic_only": True,
    }
    payload["result_sha256"] = _sha256_json(payload)
    return _ExternalAuthorityAcquisitionResult.from_dict(payload)


def require_authenticated_external_authority_acquisition(view: object, /) -> None:
    """Fail before inspecting a caller object because no external root is present."""

    del view
    raise NeedsContextError("NEEDS_CONTEXT")


_ArtifactTriple = tuple[
    _SealedRecord,
    str,
    _ExternalCanonicalSignatureEnvelopeVNext,
    str,
    _ExternalVNextArtifactPinVNext,
    str,
]


@dataclass(frozen=True, slots=True, init=False)
class _SyntheticPathBDagInput(metaclass=_SealedRecordMeta):
    declaration: _ArtifactTriple
    thesis: _ArtifactTriple
    snapshot: _ArtifactTriple
    reviews: tuple[_ArtifactTriple, ...]
    receipt: _ArtifactTriple

    def __init_subclass__(cls, **kwargs: Any) -> None:
        del cls, kwargs
        raise TypeError("record classes are sealed")

    @classmethod
    def from_components(
        cls,
        *,
        declaration: tuple[Any, ...],
        thesis: tuple[Any, ...],
        snapshot: tuple[Any, ...],
        reviews: tuple[tuple[Any, ...], ...],
        receipt: tuple[Any, ...],
    ) -> _SyntheticPathBDagInput:
        if type(reviews) is not tuple:
            _fail("reviews must be an exact tuple")
        expected = (
            (declaration, _LegacySearchImpossibilityDeclarationVNext),
            (thesis, _OneThesisContractVNext),
            (snapshot, _NewUpstreamScientificSnapshotVNext),
            (receipt, _ProvenanceMigrationReceiptVNext),
        )
        validated: list[_ArtifactTriple] = []
        for triple, record_type in expected:
            validated.append(_validate_triple_shape(triple, record_type))
        review_values = tuple(_validate_triple_shape(triple, _IndependentMigrationReviewVNext) for triple in reviews)
        instance = object.__new__(cls)
        object.__setattr__(instance, "declaration", validated[0])
        object.__setattr__(instance, "thesis", validated[1])
        object.__setattr__(instance, "snapshot", validated[2])
        object.__setattr__(instance, "reviews", review_values)
        object.__setattr__(instance, "receipt", validated[3])
        return instance


def _validate_triple_shape(value: Any, record_type: type[_SealedRecord]) -> _ArtifactTriple:
    if type(value) is not tuple or len(value) != 6:
        _fail("artifact tuple shape mismatch")
    artifact, artifact_file_sha, envelope, envelope_file_sha, pin, pin_file_sha = value
    if type(artifact) is not record_type:
        _fail("foreign artifact record")
    if type(envelope) is not _ExternalCanonicalSignatureEnvelopeVNext:
        _fail("foreign envelope record")
    if type(pin) is not _ExternalVNextArtifactPinVNext:
        _fail("foreign pin record")
    _expect_digest(artifact_file_sha, "artifact_file_sha256")
    _expect_digest(envelope_file_sha, "envelope_file_sha256")
    _expect_digest(pin_file_sha, "pin_file_sha256")
    return artifact, artifact_file_sha, envelope, envelope_file_sha, pin, pin_file_sha


def _artifact_file_sha(record: _SealedRecord) -> str:
    return _sha256_bytes(record.to_json().encode("utf-8"))


def _artifact_file_len(record: _SealedRecord) -> int:
    return len(record.to_json().encode("utf-8"))


def _logical_id(record: _SealedRecord) -> str:
    if type(record) is _LegacySearchImpossibilityDeclarationVNext:
        return record.declaration_logical_id
    if type(record) is _OneThesisContractVNext:
        return record.contract_logical_id
    if type(record) is _NewUpstreamScientificSnapshotVNext:
        return record.snapshot_logical_id
    if type(record) is _IndependentMigrationReviewVNext:
        return f"review:{record.review_role}"
    if type(record) is _ProvenanceMigrationReceiptVNext:
        return record.migration_logical_id
    _fail("unknown artifact record")
    raise AssertionError


def _self_hash(record: _SealedRecord) -> str:
    return object.__getattribute__(record, record._SELF_FIELD)


def _validate_triple_binding(triple: _ArtifactTriple, role: str) -> None:
    artifact, artifact_file_sha, envelope, envelope_file_sha, pin, pin_file_sha = triple
    if artifact_file_sha != _artifact_file_sha(artifact):
        _fail("artifact file digest mismatch")
    if envelope_file_sha != _artifact_file_sha(envelope):
        _fail("envelope file digest mismatch")
    if pin_file_sha != _artifact_file_sha(pin):
        _fail("pin file digest mismatch")
    if envelope.artifact_role != role or pin.artifact_role != role:
        _fail("artifact role mismatch")
    if envelope.artifact_schema_version != _ROLE_SCHEMAS[role]:
        _fail("artifact schema binding mismatch")
    if envelope.artifact_logical_id != _logical_id(artifact):
        _fail("artifact logical ID binding mismatch")
    if envelope.artifact_file_byte_count != _artifact_file_len(artifact):
        _fail("artifact length mismatch")
    if envelope.artifact_file_sha256 != artifact_file_sha:
        _fail("artifact digest not bound by envelope")
    if pin.expected_artifact_file_byte_count != _artifact_file_len(artifact):
        _fail("artifact length not bound by pin")
    if pin.expected_artifact_file_sha256 != artifact_file_sha:
        _fail("artifact digest not bound by pin")
    if pin.expected_signature_envelope_file_byte_count != _artifact_file_len(envelope):
        _fail("envelope length not bound by pin")
    if pin.expected_signature_envelope_file_sha256 != envelope_file_sha:
        _fail("envelope digest not bound by pin")
    equal_fields = (
        "external_verifier_package_identity",
        "external_verifier_package_version",
        "external_verifier_executable_sha256",
        "signing_key_id",
        "signing_public_key_member_identity",
        "signing_public_key_byte_count",
        "signing_public_key_sha256",
        "detached_signature_member_identity",
        "detached_signature_byte_count",
        "detached_signature_sha256",
        "detached_message_domain",
        "rotation_provenance_member_identity",
        "rotation_provenance_sha256",
    )
    for name in equal_fields:
        if getattr(envelope, name) != getattr(pin, name):
            _fail(f"envelope/pin {name} mismatch")


def _receipt_join(receipt: _ProvenanceMigrationReceiptVNext, label: str, triple: _ArtifactTriple) -> None:
    artifact, artifact_file_sha, envelope, envelope_file_sha, pin, pin_file_sha = triple
    self_name = {
        "legacy_search_declaration": "declaration_sha256",
        "one_thesis_contract": "contract_sha256",
        "new_snapshot": "snapshot_sha256",
        "independent_science_review": "review_sha256",
        "independent_provenance_review": "review_sha256",
        "independent_security_review": "review_sha256",
    }[label]
    expected = {
        f"{label}_file_sha256": artifact_file_sha,
        f"{label}_sha256": getattr(artifact, self_name),
        f"{label}_signature_envelope_file_sha256": envelope_file_sha,
        f"{label}_signature_envelope_sha256": envelope.envelope_sha256,
        f"{label}_pin_file_sha256": pin_file_sha,
        f"{label}_pin_sha256": pin.pin_sha256,
    }
    for name, value in expected.items():
        if getattr(receipt, name) != value:
            _fail(f"receipt {name} join mismatch")


def _validate_synthetic_path_b_metadata(value: _SyntheticPathBDagInput) -> None:
    """Validate a complete in-memory synthetic Path-B metadata DAG.

    Success returns ``None`` and deliberately produces no authority object.
    """

    if type(value) is not _SyntheticPathBDagInput:
        _fail("synthetic DAG input type mismatch")
    try:
        raw_declaration = object.__getattribute__(value, "declaration")
        raw_thesis = object.__getattribute__(value, "thesis")
        raw_snapshot = object.__getattribute__(value, "snapshot")
        raw_reviews = object.__getattribute__(value, "reviews")
        raw_receipt = object.__getattribute__(value, "receipt")
    except AttributeError as error:
        raise ExternalAuthorityAcquisitionError("invalid synthetic DAG construction") from error
    declaration = _validate_triple_shape(raw_declaration, _LegacySearchImpossibilityDeclarationVNext)
    thesis = _validate_triple_shape(raw_thesis, _OneThesisContractVNext)
    snapshot = _validate_triple_shape(raw_snapshot, _NewUpstreamScientificSnapshotVNext)
    receipt = _validate_triple_shape(raw_receipt, _ProvenanceMigrationReceiptVNext)
    if type(raw_reviews) is not tuple or len(raw_reviews) != 3:
        _fail("exactly three reviews required")
    reviews = tuple(_validate_triple_shape(item, _IndependentMigrationReviewVNext) for item in raw_reviews)
    role_triples = (
        (declaration, "legacy_search_impossibility_declaration"),
        (thesis, "one_thesis_contract"),
        (snapshot, "new_upstream_scientific_snapshot"),
        *((review, review[0].review_role) for review in reviews),
        (receipt, "provenance_migration_receipt"),
    )
    for triple, role in role_triples:
        _validate_triple_binding(triple, role)
    if thesis[2].predecessor_envelope_sha256s != (declaration[2].envelope_sha256,):
        _fail("thesis envelope predecessor mismatch")
    if thesis[4].predecessor_artifact_pin_sha256s != (declaration[4].pin_sha256,):
        _fail("thesis pin predecessor mismatch")
    if snapshot[2].predecessor_envelope_sha256s != (thesis[2].envelope_sha256,):
        _fail("snapshot envelope predecessor mismatch")
    if snapshot[4].predecessor_artifact_pin_sha256s != (thesis[4].pin_sha256,):
        _fail("snapshot pin predecessor mismatch")
    if declaration[2].predecessor_envelope_sha256s or declaration[4].predecessor_artifact_pin_sha256s:
        _fail("declaration must be DAG genesis")
    expected_review_roles = set(_REVIEW_ROLES)
    if {review[0].review_role for review in reviews} != expected_review_roles:
        _fail("review role census mismatch")
    for review in reviews:
        if review[2].predecessor_envelope_sha256s != (snapshot[2].envelope_sha256,):
            _fail("review envelope predecessor mismatch")
        if review[4].predecessor_artifact_pin_sha256s != (snapshot[4].pin_sha256,):
            _fail("review pin predecessor mismatch")
        if review[2].detached_message_domain != _ROLE_DOMAINS[review[0].review_role]:
            _fail("review signature domain mismatch")
    review_envelopes = tuple(sorted(review[2].envelope_sha256 for review in reviews))
    review_pins = tuple(sorted(review[4].pin_sha256 for review in reviews))
    if receipt[2].predecessor_envelope_sha256s != review_envelopes:
        _fail("receipt envelope predecessor mismatch")
    if receipt[4].predecessor_artifact_pin_sha256s != review_pins:
        _fail("receipt pin predecessor mismatch")
    declaration_record = declaration[0]
    thesis_record = thesis[0]
    snapshot_record = snapshot[0]
    if snapshot_record.legacy_search_declaration_file_sha256 != declaration[1]:
        _fail("snapshot declaration file join mismatch")
    if snapshot_record.legacy_search_declaration_sha256 != declaration_record.declaration_sha256:
        _fail("snapshot declaration self-hash join mismatch")
    if snapshot_record.one_thesis_contract_file_sha256 != thesis[1]:
        _fail("snapshot thesis file join mismatch")
    if snapshot_record.one_thesis_contract_sha256 != thesis_record.contract_sha256:
        _fail("snapshot thesis self-hash join mismatch")
    if snapshot_record.allowed_upstream_authority_sha256s != thesis_record.allowed_upstream_authority_sha256s:
        _fail("snapshot Task5 authority join mismatch")
    if snapshot_record.external_scientist_approval_sha256 != thesis_record.external_scientist_approval_sha256:
        _fail("snapshot scientist approval join mismatch")
    subject_values = (
        declaration[1],
        declaration_record.declaration_sha256,
        thesis[1],
        thesis_record.contract_sha256,
        snapshot[1],
        snapshot_record.snapshot_sha256,
    )
    for review in reviews:
        record = review[0]
        joined = (
            record.reviewed_declaration_file_sha256,
            record.reviewed_declaration_sha256,
            record.reviewed_one_thesis_contract_file_sha256,
            record.reviewed_one_thesis_contract_sha256,
            record.reviewed_snapshot_file_sha256,
            record.reviewed_snapshot_sha256,
        )
        if joined != subject_values:
            _fail("review subject join mismatch")
    reviewer_records = tuple(review[0] for review in reviews)
    reviewer_envelopes = tuple(review[2] for review in reviews)
    reviewer_pins = tuple(review[4] for review in reviews)
    reviewer_identities = tuple(item.reviewer_identity for item in reviewer_records)
    if len(set(reviewer_identities)) != 3:
        _fail("reviewer identities must be pairwise distinct")
    disallowed_reviewer_identities = {
        declaration_record.responsible_migration_owner_identity,
        thesis_record.external_scientist_identity,
    }
    if disallowed_reviewer_identities & set(reviewer_identities):
        _fail("migration owner or producer identity cannot review")
    producer_envelopes = (declaration[2], thesis[2], snapshot[2], receipt[2])
    producer_pins = (declaration[4], thesis[4], snapshot[4], receipt[4])
    envelope_dimensions = (
        "signing_key_id",
        "signing_public_key_member_identity",
        "signing_public_key_sha256",
        "detached_signature_member_identity",
        "detached_signature_sha256",
        "external_verifier_package_identity",
        "external_verifier_package_version",
        "external_verifier_executable_sha256",
        "rotation_provenance_member_identity",
        "rotation_provenance_sha256",
    )
    pin_dimensions = (
        "external_verifier_executable_member_identity",
        "external_platform_signature_member_identity",
        "external_platform_signature_sha256",
    )
    for source_name, names, reviewer_values, producer_values in (
        ("envelope", envelope_dimensions, reviewer_envelopes, producer_envelopes),
        ("pin", pin_dimensions, reviewer_pins, producer_pins),
    ):
        for name in names:
            reviewer_dimension = tuple(getattr(item, name) for item in reviewer_values)
            if len(set(reviewer_dimension)) != 3:
                _fail(f"reviewer {source_name} {name} must be pairwise distinct")
            if set(reviewer_dimension) & {getattr(item, name) for item in producer_values}:
                _fail(f"producer/reviewer {source_name} {name} overlap")
    reviewer_member_identities = {
        *(getattr(item, name) for item in reviewer_envelopes for name in (
            "signing_public_key_member_identity",
            "detached_signature_member_identity",
            "rotation_provenance_member_identity",
        )),
        *(getattr(item, name) for item in reviewer_pins for name in (
            "external_verifier_executable_member_identity",
            "external_platform_signature_member_identity",
        )),
    }
    approval_member_identities = {
        declaration_record.responsible_owner_approval_member_identity,
        thesis_record.external_scientist_approval_member_identity,
        *(row.approval_member_identity for row in declaration_record.custodian_search_rows),
    }
    reviewer_digests = {
        *(getattr(item, name) for item in reviewer_envelopes for name in (
            "signing_public_key_sha256",
            "detached_signature_sha256",
            "external_verifier_executable_sha256",
            "rotation_provenance_sha256",
        )),
        *(item.external_platform_signature_sha256 for item in reviewer_pins),
    }
    approval_digests = {
        declaration_record.responsible_owner_approval_sha256,
        thesis_record.external_scientist_approval_sha256,
        *(row.approval_file_sha256 for row in declaration_record.custodian_search_rows),
    }
    if reviewer_member_identities & approval_member_identities or reviewer_digests & approval_digests:
        _fail("review authority overlaps migration-owner/scientist/custodian approval")
    reviewer_authority_values = (
        *reviewer_identities,
        *(getattr(item, name) for item in reviewer_envelopes for name in envelope_dimensions),
        *(getattr(item, name) for item in reviewer_pins for name in pin_dimensions),
    )
    if len(set(reviewer_authority_values)) != len(reviewer_authority_values):
        _fail("review authority values must be globally pairwise distinct")
    producer_authority_values = {
        declaration_record.responsible_migration_owner_identity,
        thesis_record.external_scientist_identity,
        *approval_member_identities,
        *approval_digests,
        *(getattr(item, name) for item in producer_envelopes for name in envelope_dimensions),
        *(getattr(item, name) for item in producer_pins for name in pin_dimensions),
    }
    if set(reviewer_authority_values) & producer_authority_values:
        _fail("review authority globally overlaps producer/owner/scientist authority")
    receipt_record = receipt[0]
    _receipt_join(receipt_record, "legacy_search_declaration", declaration)
    _receipt_join(receipt_record, "one_thesis_contract", thesis)
    _receipt_join(receipt_record, "new_snapshot", snapshot)
    reviews_by_role = {review[0].review_role: review for review in reviews}
    _receipt_join(receipt_record, "independent_science_review", reviews_by_role["independent_science_migration_review"])
    _receipt_join(
        receipt_record,
        "independent_provenance_review",
        reviews_by_role["independent_provenance_migration_review"],
    )
    _receipt_join(receipt_record, "independent_security_review", reviews_by_role["independent_security_migration_review"])
    all_hashes = []
    for triple, _ in role_triples:
        all_hashes.extend((triple[1], _self_hash(triple[0]), triple[3], triple[2].envelope_sha256, triple[5], triple[4].pin_sha256))
    if len(set(all_hashes)) != len(all_hashes):
        _fail("DAG contains a duplicate or reverse-cycle digest")
    return None
