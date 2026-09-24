"""Generation-0 orchestration for the Path-B positive-intake contract.

This module validates only already-constructed synthetic in-memory views.  It
does not locate, open, read, authenticate, or promote an external package.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import NoReturn

from iclr2027.path_b_positive_intake_contract import IntakeContractError
from iclr2027.path_b_positive_intake_crypto import IntakeCryptoError
from iclr2027.path_b_positive_intake_science import (
    SyntheticPackageView,
    validate_frozen_scientific_contract,
    validate_global_role_separation,
)


__all__ = (
    "IntakeContractError",
    "NeedsContextError",
    "current_status",
    "negative_fixture_registry",
    "validate_synthetic_path_b_contract",
    "validate_authenticated_path_b_intake",
)


class NeedsContextError(IntakeContractError):
    """Raised because the externally pinned launcher capability is absent."""


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


@dataclass(frozen=True, slots=True)
class _NegativeFixture:
    schema_version: str
    fixture_id: str
    reason_code: str
    required_outcome: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "fixture_id": self.fixture_id,
            "reason_code": self.reason_code,
            "required_outcome": self.required_outcome,
        }


@dataclass(frozen=True, slots=True)
class _GenerationZeroStatus:
    schema_version: str
    authority_mode: str
    status: str
    reason_codes: tuple[str, ...]
    empirical_status: str
    synthetic_only: bool
    external_artifact_count: int
    external_signature_count: int
    external_review_count: int
    authenticated_locator_count: int
    authenticated_package_count: int
    task6_vnext_authority_count: int
    task6_vnext_implementation_count: int
    candidate_path_construction_count: int
    locator_open_count: int
    candidate_root_open_count: int
    package_index_read_count: int
    member_read_count: int
    source_read_count: int
    data_read_count: int
    result_read_count: int
    rate_read_count: int
    simulation_draw_count: int
    model_call_count: int
    tool_call_count: int
    paid_call_count: int
    output_write_count: int
    operation_count: int
    automatic_retry_count: int
    fallback_count: int
    task6_vnext_commission_eligible: bool
    source_access_authorized: bool
    simulation_authorized: bool
    paid_run_authorized: bool
    official_result_eligible: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "authority_mode": self.authority_mode,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "empirical_status": self.empirical_status,
            "synthetic_only": self.synthetic_only,
            "external_artifact_count": self.external_artifact_count,
            "external_signature_count": self.external_signature_count,
            "external_review_count": self.external_review_count,
            "authenticated_locator_count": self.authenticated_locator_count,
            "authenticated_package_count": self.authenticated_package_count,
            "task6_vnext_authority_count": self.task6_vnext_authority_count,
            "task6_vnext_implementation_count": self.task6_vnext_implementation_count,
            "candidate_path_construction_count": self.candidate_path_construction_count,
            "locator_open_count": self.locator_open_count,
            "candidate_root_open_count": self.candidate_root_open_count,
            "package_index_read_count": self.package_index_read_count,
            "member_read_count": self.member_read_count,
            "source_read_count": self.source_read_count,
            "data_read_count": self.data_read_count,
            "result_read_count": self.result_read_count,
            "rate_read_count": self.rate_read_count,
            "simulation_draw_count": self.simulation_draw_count,
            "model_call_count": self.model_call_count,
            "tool_call_count": self.tool_call_count,
            "paid_call_count": self.paid_call_count,
            "output_write_count": self.output_write_count,
            "operation_count": self.operation_count,
            "automatic_retry_count": self.automatic_retry_count,
            "fallback_count": self.fallback_count,
            "task6_vnext_commission_eligible": (self.task6_vnext_commission_eligible),
            "source_access_authorized": self.source_access_authorized,
            "simulation_authorized": self.simulation_authorized,
            "paid_run_authorized": self.paid_run_authorized,
            "official_result_eligible": self.official_result_eligible,
        }

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())


_REASON_CODES = (
    "approval_authentication_failed",
    "canonical_file_encoding_failed",
    "core_record_census_mismatch",
    "cryptographic_signature_failed",
    "external_root_missing",
    "filesystem_identity_failed",
    "immutable_member_census_mismatch",
    "locator_authentication_failed",
    "package_index_binding_failed",
    "process_spec_custody_failed",
    "producer_reviewer_authority_overlap",
    "replay_or_freshness_failed",
    "scientific_contract_drift",
    "task5_parent_custody_failed",
    "verifier_package_or_rotation_failed",
)

_FIXTURES = tuple(
    _NegativeFixture(
        schema_version=("ace.iclr2027.path_b_positive_intake_negative_fixture.v1"),
        fixture_id=reason_code,
        reason_code=reason_code,
        required_outcome="reject_without_authority",
    )
    for reason_code in _REASON_CODES
)

_CURRENT_STATUS = _GenerationZeroStatus(
    schema_version="ace.iclr2027.path_b_positive_intake_generation0_status.v1",
    authority_mode="external_bootstrap_absent",
    status="no_go",
    reason_codes=("external_root_missing",),
    empirical_status="no_go_needs_context",
    synthetic_only=True,
    external_artifact_count=0,
    external_signature_count=0,
    external_review_count=0,
    authenticated_locator_count=0,
    authenticated_package_count=0,
    task6_vnext_authority_count=0,
    task6_vnext_implementation_count=0,
    candidate_path_construction_count=0,
    locator_open_count=0,
    candidate_root_open_count=0,
    package_index_read_count=0,
    member_read_count=0,
    source_read_count=0,
    data_read_count=0,
    result_read_count=0,
    rate_read_count=0,
    simulation_draw_count=0,
    model_call_count=0,
    tool_call_count=0,
    paid_call_count=0,
    output_write_count=0,
    operation_count=0,
    automatic_retry_count=0,
    fallback_count=0,
    task6_vnext_commission_eligible=False,
    source_access_authorized=False,
    simulation_authorized=False,
    paid_run_authorized=False,
    official_result_eligible=False,
)


def current_status() -> _GenerationZeroStatus:
    """Return the deterministic current Generation-0 no-authority status."""

    return _CURRENT_STATUS


def negative_fixture_registry() -> tuple[_NegativeFixture, ...]:
    """Return the closed failure-family registry without performing I/O."""

    return _FIXTURES


def validate_synthetic_path_b_contract(package: SyntheticPackageView) -> None:
    """Validate a complete in-memory scientific view without minting authority."""

    try:
        validate_frozen_scientific_contract(package)
        validate_global_role_separation(package)
    except (IntakeContractError, IntakeCryptoError):
        raise
    return None


def validate_authenticated_path_b_intake(capability: object) -> NoReturn:
    """Reject before observing a caller because the external root is absent."""

    del capability
    raise NeedsContextError("external_root_missing")
