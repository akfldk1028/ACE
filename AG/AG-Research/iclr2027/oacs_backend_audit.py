"""Closed, zero-generation OACS backend readiness audit.

Only a caller-injected three-method metadata probe is permitted.  A READY
result additionally needs a canonical approval trust root and an independently
supplied digest; Tasks 7/8 own and bind that digest outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import re
from typing import Mapping, Protocol


SCHEMA_VERSION = "oacs_backend_audit_v1"
APPROVAL_SCHEMA_VERSION = "oacs_backend_approval_v1"
READY = "ready_for_separate_execution_review"
NOT_ASSESSABLE = "not_assessable"
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_VERSION = re.compile(r"v?[0-9]+(?:\.[0-9]+){1,3}(?:[-+][0-9A-Za-z.-]+)?\Z")
_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{2,127}\Z")
_AUTH_MODES = frozenset({"api_key", "interactive", "none", "service_account"})
_QUOTA_MODES = frozenset({"declared", "enforced", "unmetered"})
_PROVENANCE = frozenset({"injected_metadata"})
_REASON_CODES = frozenset(
    {
        "adapter_hash_mismatch",
        "adapter_unavailable",
        "approval_trust_root_unavailable",
        "auth_mode_mismatch",
        "auth_mode_unknown",
        "cache_accounting_unverifiable",
        "evidence_provenance_mismatch",
        "executable_hash_mismatch",
        "executable_unavailable",
        "failure_accounting_incomplete",
        "marginal_invoice_unapproved",
        "model_identity_mismatch",
        "probe_error",
        "quota_assumptions_mismatch",
        "quota_assumptions_undeclared",
        "quota_mode_mismatch",
        "quota_mode_unknown",
        "retry_unbounded",
        "runtime_version_mismatch",
        "runtime_version_unavailable",
        "timeout_unbounded",
        "usage_accounting_incomplete",
    }
)


class MetadataProbe(Protocol):
    """The entire allowed external surface for this audit."""

    def version(self) -> str: ...

    def auth_mode(self) -> str: ...

    def quota_mode(self) -> str: ...


def _require_exact(value: object, expected: type, name: str) -> None:
    if type(value) is not expected:
        raise TypeError(f"{name} must be exactly {expected.__name__}")


def _require_string(value: object, name: str, *, allow_empty: bool = False) -> str:
    _require_exact(value, str, name)
    if not allow_empty and not value:
        raise ValueError(f"{name} must not be empty")
    return value


def _require_hash(value: object, name: str) -> str:
    value = _require_string(value, name)
    if not _HASH.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")
    return value


def _require_mapping(value: object, name: str) -> Mapping[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{name} must be exactly dict")
    for key in value:
        _require_exact(key, str, f"{name} key")
    return value


def _closed(mapping: Mapping[str, object], fields: frozenset[str], name: str) -> None:
    if set(mapping) != fields:
        raise ValueError(f"{name} has unexpected or missing fields")


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _parse_no_duplicates(payload: bytes) -> Mapping[str, object]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("payload must be UTF-8") from exc

    def no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = item
        return result

    try:
        value = json.loads(text, object_pairs_hook=no_duplicates)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid canonical JSON") from exc
    return _require_mapping(value, "payload")


@dataclass(frozen=True)
class QuotaAssumptionV1:
    scope: str
    statement: str

    def __post_init__(self) -> None:
        _require_string(self.scope, "quota scope")
        _require_string(self.statement, "quota statement")
        if not self.scope.strip() or not self.statement.strip():
            raise ValueError("quota assumptions must not be blank")

    def to_dict(self) -> dict[str, object]:
        return {"scope": self.scope, "statement": self.statement}

    @classmethod
    def from_mapping(cls, value: object) -> "QuotaAssumptionV1":
        mapping = _require_mapping(value, "quota assumption")
        _closed(mapping, frozenset({"scope", "statement"}), "quota assumption")
        return cls(**mapping)  # type: ignore[arg-type]


@dataclass(frozen=True)
class UsageAccountingV1:
    agent_tokens: bool
    selector_tokens: bool
    router_tokens: bool
    verifier_tokens: bool
    synthesis_tokens: bool
    cache_usage: bool
    failure_usage: bool

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _require_exact(getattr(self, field), bool, field)

    @classmethod
    def all_accounted(cls) -> "UsageAccountingV1":
        return cls(True, True, True, True, True, True, True)

    def to_dict(self) -> dict[str, object]:
        return {
            "agent_tokens": self.agent_tokens,
            "cache_usage": self.cache_usage,
            "failure_usage": self.failure_usage,
            "router_tokens": self.router_tokens,
            "selector_tokens": self.selector_tokens,
            "synthesis_tokens": self.synthesis_tokens,
            "verifier_tokens": self.verifier_tokens,
        }

    @classmethod
    def from_mapping(cls, value: object) -> "UsageAccountingV1":
        mapping = _require_mapping(value, "usage_accounting")
        _closed(mapping, frozenset(cls.__dataclass_fields__), "usage_accounting")
        return cls(**mapping)  # type: ignore[arg-type]

    def incomplete_reason_codes(self) -> tuple[str, ...]:
        codes: list[str] = []
        if not all(
            (
                self.agent_tokens,
                self.selector_tokens,
                self.router_tokens,
                self.verifier_tokens,
                self.synthesis_tokens,
            )
        ):
            codes.append("usage_accounting_incomplete")
        if not self.cache_usage:
            codes.append("cache_accounting_unverifiable")
        if not self.failure_usage:
            codes.append("failure_accounting_incomplete")
        return tuple(codes)


def _require_quota_assumptions(
    value: object, name: str
) -> tuple[QuotaAssumptionV1, ...]:
    _require_exact(value, tuple, name)
    for assumption in value:
        if type(assumption) is not QuotaAssumptionV1:
            raise TypeError(f"{name} entries must be exactly QuotaAssumptionV1")
    return value


def _quota_dicts(values: tuple[QuotaAssumptionV1, ...]) -> list[dict[str, object]]:
    return [item.to_dict() for item in values]


@dataclass(frozen=True)
class BackendAuditConfigV1:
    """Untrusted observations.  It deliberately contains no approved identity."""

    executable: str
    executable_sha256: str
    adapter: str
    adapter_sha256: str
    model_id: str
    quota_assumptions: tuple[QuotaAssumptionV1, ...]
    invoice_approval_id: str
    maximum_marginal_cost_microunits: int
    timeout_seconds: int
    retry_count: int
    usage_accounting: UsageAccountingV1
    evidence_provenance: str

    def __post_init__(self) -> None:
        _require_string(self.executable, "executable", allow_empty=True)
        _require_hash(self.executable_sha256, "executable_sha256")
        _require_string(self.adapter, "adapter", allow_empty=True)
        _require_hash(self.adapter_sha256, "adapter_sha256")
        _require_string(self.model_id, "model_id", allow_empty=True)
        _require_quota_assumptions(self.quota_assumptions, "quota_assumptions")
        _require_string(self.invoice_approval_id, "invoice_approval_id")
        _require_exact(
            self.maximum_marginal_cost_microunits,
            int,
            "maximum_marginal_cost_microunits",
        )
        _require_exact(self.timeout_seconds, int, "timeout_seconds")
        _require_exact(self.retry_count, int, "retry_count")
        if type(self.usage_accounting) is not UsageAccountingV1:
            raise TypeError("usage_accounting must be exactly UsageAccountingV1")
        _require_string(self.evidence_provenance, "evidence_provenance")

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter": self.adapter,
            "adapter_sha256": self.adapter_sha256,
            "evidence_provenance": self.evidence_provenance,
            "executable": self.executable,
            "executable_sha256": self.executable_sha256,
            "invoice_approval_id": self.invoice_approval_id,
            "maximum_marginal_cost_microunits": self.maximum_marginal_cost_microunits,
            "model_id": self.model_id,
            "quota_assumptions": _quota_dicts(self.quota_assumptions),
            "retry_count": self.retry_count,
            "timeout_seconds": self.timeout_seconds,
            "usage_accounting": self.usage_accounting.to_dict(),
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_dict())

    @classmethod
    def from_mapping(cls, value: object) -> "BackendAuditConfigV1":
        mapping = dict(_require_mapping(value, "config"))
        _closed(mapping, frozenset(cls.__dataclass_fields__), "config")
        quota_assumptions = mapping["quota_assumptions"]
        if type(quota_assumptions) is not list:
            raise TypeError("quota_assumptions must be exactly a JSON list")
        mapping["quota_assumptions"] = tuple(
            QuotaAssumptionV1.from_mapping(item) for item in quota_assumptions
        )
        mapping["usage_accounting"] = UsageAccountingV1.from_mapping(
            mapping["usage_accounting"]
        )
        return cls(**mapping)  # type: ignore[arg-type]


@dataclass(frozen=True)
class ApprovalTrustRootV1:
    """Trusted approval policy, authenticated by an external expected digest."""

    executable_sha256: str
    runtime_version: str
    adapter_sha256: str
    model_id: str
    auth_mode: str
    quota_mode: str
    quota_assumptions: tuple[QuotaAssumptionV1, ...]
    invoice_approval_id: str
    maximum_marginal_cost_microunits: int
    timeout_seconds: int
    retry_count: int
    usage_accounting: UsageAccountingV1
    required_evidence_provenance: str
    schema_version: str = APPROVAL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_hash(self.executable_sha256, "approval executable_sha256")
        _require_string(self.runtime_version, "approval runtime_version")
        if not _VERSION.fullmatch(self.runtime_version):
            raise ValueError("approval runtime_version must be a semantic version")
        _require_hash(self.adapter_sha256, "approval adapter_sha256")
        _require_string(self.model_id, "approval model_id")
        if not _MODEL.fullmatch(self.model_id) or "//" in self.model_id:
            raise ValueError("approval model_id must be an exact model identifier")
        _require_string(self.auth_mode, "approval auth_mode")
        _require_string(self.quota_mode, "approval quota_mode")
        if self.auth_mode not in _AUTH_MODES or self.quota_mode not in _QUOTA_MODES:
            raise ValueError("approval metadata mode is unsupported")
        _require_quota_assumptions(self.quota_assumptions, "approval quota_assumptions")
        if not self.quota_assumptions:
            raise ValueError("approval quota_assumptions must be declared")
        _require_string(self.invoice_approval_id, "approval invoice_approval_id")
        _require_exact(
            self.maximum_marginal_cost_microunits,
            int,
            "approval maximum_marginal_cost_microunits",
        )
        if self.maximum_marginal_cost_microunits <= 0:
            raise ValueError("approval marginal cost must be positive")
        _require_exact(self.timeout_seconds, int, "approval timeout_seconds")
        _require_exact(self.retry_count, int, "approval retry_count")
        if not 1 <= self.timeout_seconds <= 300 or not 0 <= self.retry_count <= 5:
            raise ValueError("approval timeout/retry policy is unbounded")
        if type(self.usage_accounting) is not UsageAccountingV1:
            raise TypeError(
                "approval usage_accounting must be exactly UsageAccountingV1"
            )
        if self.usage_accounting.incomplete_reason_codes():
            raise ValueError("approval usage accounting must be complete")
        _require_string(
            self.required_evidence_provenance, "approval required_evidence_provenance"
        )
        if self.required_evidence_provenance not in _PROVENANCE:
            raise ValueError("approval provenance is unsupported")
        if self.schema_version != APPROVAL_SCHEMA_VERSION:
            raise ValueError("unsupported approval schema_version")

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter_sha256": self.adapter_sha256,
            "auth_mode": self.auth_mode,
            "executable_sha256": self.executable_sha256,
            "invoice_approval_id": self.invoice_approval_id,
            "maximum_marginal_cost_microunits": self.maximum_marginal_cost_microunits,
            "model_id": self.model_id,
            "quota_assumptions": _quota_dicts(self.quota_assumptions),
            "quota_mode": self.quota_mode,
            "required_evidence_provenance": self.required_evidence_provenance,
            "retry_count": self.retry_count,
            "runtime_version": self.runtime_version,
            "schema_version": self.schema_version,
            "timeout_seconds": self.timeout_seconds,
            "usage_accounting": self.usage_accounting.to_dict(),
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_dict())


def approval_digest(approval: ApprovalTrustRootV1) -> str:
    if type(approval) is not ApprovalTrustRootV1:
        raise TypeError("approval must be exactly ApprovalTrustRootV1")
    return hashlib.sha256(approval.canonical_bytes()).hexdigest()


def parse_canonical_config_bytes(payload: bytes) -> BackendAuditConfigV1:
    config = BackendAuditConfigV1.from_mapping(_parse_no_duplicates(payload))
    if config.canonical_bytes() != payload:
        raise ValueError("config JSON is not canonical")
    return config


@dataclass(frozen=True)
class BackendAuditV1:
    executable: str
    executable_sha256: str
    runtime_version: str
    adapter: str
    adapter_sha256: str
    model_id: str
    auth_mode: str
    quota_mode: str
    quota_assumptions: tuple[QuotaAssumptionV1, ...]
    invoice_approval_id: str
    maximum_marginal_cost_microunits: int
    timeout_seconds: int
    retry_count: int
    usage_accounting: UsageAccountingV1
    evidence_provenance: str
    status: str
    reason_codes: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_string(self.executable, "executable", allow_empty=True)
        _require_hash(self.executable_sha256, "executable_sha256")
        _require_string(self.runtime_version, "runtime_version")
        _require_string(self.adapter, "adapter", allow_empty=True)
        _require_hash(self.adapter_sha256, "adapter_sha256")
        _require_string(self.model_id, "model_id", allow_empty=True)
        _require_string(self.auth_mode, "auth_mode")
        _require_string(self.quota_mode, "quota_mode")
        _require_quota_assumptions(self.quota_assumptions, "quota_assumptions")
        _require_string(self.invoice_approval_id, "invoice_approval_id")
        _require_exact(
            self.maximum_marginal_cost_microunits,
            int,
            "maximum_marginal_cost_microunits",
        )
        _require_exact(self.timeout_seconds, int, "timeout_seconds")
        _require_exact(self.retry_count, int, "retry_count")
        if type(self.usage_accounting) is not UsageAccountingV1:
            raise TypeError("usage_accounting must be exactly UsageAccountingV1")
        _require_string(self.evidence_provenance, "evidence_provenance")
        if self.status not in {READY, NOT_ASSESSABLE}:
            raise ValueError("invalid audit status")
        _require_exact(self.reason_codes, tuple, "reason_codes")
        if any(
            type(code) is not str or code not in _REASON_CODES
            for code in self.reason_codes
        ):
            raise ValueError("invalid audit reason code")
        if tuple(sorted(set(self.reason_codes))) != self.reason_codes:
            raise ValueError("reason_codes must be sorted and unique")
        if (self.status == READY) != (not self.reason_codes):
            raise ValueError("status and reason_codes disagree")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported schema_version")

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter": self.adapter,
            "adapter_sha256": self.adapter_sha256,
            "auth_mode": self.auth_mode,
            "evidence_provenance": self.evidence_provenance,
            "executable": self.executable,
            "executable_sha256": self.executable_sha256,
            "invoice_approval_id": self.invoice_approval_id,
            "maximum_marginal_cost_microunits": self.maximum_marginal_cost_microunits,
            "model_id": self.model_id,
            "quota_assumptions": _quota_dicts(self.quota_assumptions),
            "quota_mode": self.quota_mode,
            "reason_codes": list(self.reason_codes),
            "retry_count": self.retry_count,
            "runtime_version": self.runtime_version,
            "schema_version": self.schema_version,
            "status": self.status,
            "timeout_seconds": self.timeout_seconds,
            "usage_accounting": self.usage_accounting.to_dict(),
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_dict())

    @classmethod
    def from_mapping(cls, value: object) -> "BackendAuditV1":
        mapping = dict(_require_mapping(value, "audit"))
        _closed(mapping, frozenset(cls.__dataclass_fields__), "audit")
        quota_assumptions = mapping["quota_assumptions"]
        if type(quota_assumptions) is not list:
            raise TypeError("quota_assumptions must be exactly a JSON list")
        mapping["quota_assumptions"] = tuple(
            QuotaAssumptionV1.from_mapping(item) for item in quota_assumptions
        )
        reason_codes = mapping["reason_codes"]
        if type(reason_codes) is not list:
            raise TypeError("reason_codes must be exactly a JSON list")
        mapping["reason_codes"] = tuple(reason_codes)
        mapping["usage_accounting"] = UsageAccountingV1.from_mapping(
            mapping["usage_accounting"]
        )
        return cls(**mapping)  # type: ignore[arg-type]


def parse_canonical_audit_bytes(payload: bytes) -> BackendAuditV1:
    audit = BackendAuditV1.from_mapping(_parse_no_duplicates(payload))
    if audit.canonical_bytes() != payload:
        raise ValueError("audit JSON is not canonical")
    return audit


def _safe_version(value: object) -> str:
    return value if type(value) is str and _VERSION.fullmatch(value) else "unknown"


def _safe_mode(value: object, allowed: frozenset[str]) -> str:
    return value if type(value) is str and value in allowed else "unknown"


def _probe_value(probe: MetadataProbe, method: str) -> tuple[object, bool]:
    try:
        return getattr(probe, method)(), False
    except Exception:
        return "unknown", True


def _trusted_approval(
    approval: object, expected_digest: object
) -> ApprovalTrustRootV1 | None:
    if type(approval) is not ApprovalTrustRootV1 or type(expected_digest) is not str:
        return None
    if not _HASH.fullmatch(expected_digest):
        return None
    return (
        approval
        if hmac.compare_digest(approval_digest(approval), expected_digest)
        else None
    )


def audit_backend(
    config: BackendAuditConfigV1,
    probe: MetadataProbe,
    approval: ApprovalTrustRootV1 | None = None,
    expected_approval_digest: str | None = None,
) -> BackendAuditV1:
    """Assess metadata only; READY requires the externally bound trust root."""
    if type(config) is not BackendAuditConfigV1:
        raise TypeError("config must be exactly BackendAuditConfigV1")
    version_raw, version_error = _probe_value(probe, "version")
    auth_raw, auth_error = _probe_value(probe, "auth_mode")
    quota_raw, quota_error = _probe_value(probe, "quota_mode")
    runtime_version = _safe_version(version_raw)
    auth_mode = _safe_mode(auth_raw, _AUTH_MODES)
    quota_mode = _safe_mode(quota_raw, _QUOTA_MODES)
    trusted = _trusted_approval(approval, expected_approval_digest)
    reasons: set[str] = set()
    if trusted is None:
        reasons.add("approval_trust_root_unavailable")
    if not config.executable:
        reasons.add("executable_unavailable")
    if not config.adapter:
        reasons.add("adapter_unavailable")
    if runtime_version == "unknown":
        reasons.add("runtime_version_unavailable")
    if auth_mode == "unknown":
        reasons.add("auth_mode_unknown")
    if quota_mode == "unknown":
        reasons.add("quota_mode_unknown")
    if not config.quota_assumptions:
        reasons.add("quota_assumptions_undeclared")
    if config.maximum_marginal_cost_microunits <= 0:
        reasons.add("marginal_invoice_unapproved")
    if not 1 <= config.timeout_seconds <= 300:
        reasons.add("timeout_unbounded")
    if not 0 <= config.retry_count <= 5:
        reasons.add("retry_unbounded")
    reasons.update(config.usage_accounting.incomplete_reason_codes())
    if version_error or auth_error or quota_error:
        reasons.add("probe_error")
    if trusted is not None:
        if config.executable_sha256 != trusted.executable_sha256:
            reasons.add("executable_hash_mismatch")
        if runtime_version != trusted.runtime_version:
            reasons.add("runtime_version_mismatch")
        if config.adapter_sha256 != trusted.adapter_sha256:
            reasons.add("adapter_hash_mismatch")
        if config.model_id != trusted.model_id:
            reasons.add("model_identity_mismatch")
        if auth_mode != trusted.auth_mode:
            reasons.add("auth_mode_mismatch")
        if quota_mode != trusted.quota_mode:
            reasons.add("quota_mode_mismatch")
        if config.quota_assumptions != trusted.quota_assumptions:
            reasons.add("quota_assumptions_mismatch")
        if (
            config.invoice_approval_id != trusted.invoice_approval_id
            or config.maximum_marginal_cost_microunits
            != trusted.maximum_marginal_cost_microunits
        ):
            reasons.add("marginal_invoice_unapproved")
        if (
            config.timeout_seconds != trusted.timeout_seconds
            or config.retry_count != trusted.retry_count
        ):
            reasons.add("timeout_unbounded")
        if config.usage_accounting != trusted.usage_accounting:
            reasons.add("usage_accounting_incomplete")
        if config.evidence_provenance != trusted.required_evidence_provenance:
            reasons.add("evidence_provenance_mismatch")
    reason_codes = tuple(sorted(reasons))
    return BackendAuditV1(
        executable=config.executable,
        executable_sha256=config.executable_sha256,
        runtime_version=runtime_version,
        adapter=config.adapter,
        adapter_sha256=config.adapter_sha256,
        model_id=config.model_id,
        auth_mode=auth_mode,
        quota_mode=quota_mode,
        quota_assumptions=config.quota_assumptions,
        invoice_approval_id=config.invoice_approval_id,
        maximum_marginal_cost_microunits=config.maximum_marginal_cost_microunits,
        timeout_seconds=config.timeout_seconds,
        retry_count=config.retry_count,
        usage_accounting=config.usage_accounting,
        evidence_provenance=config.evidence_provenance,
        status=READY if not reason_codes else NOT_ASSESSABLE,
        reason_codes=reason_codes,
    )
