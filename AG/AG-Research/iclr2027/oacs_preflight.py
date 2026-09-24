"""Fail-closed aggregate preflight for the MAS/OACS pre-outcome package.

The aggregate consumes the exact canonical bytes owned by Tasks 1--6.  Its
positive status only permits authoring a separate execution plan; it never
authorizes an experiment, provider call, or scientific claim.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import hmac
import json
import re
from types import MappingProxyType

from iclr2027.oacs_backend_audit import (
    READY,
    ApprovalTrustRootV1,
    BackendAuditV1,
    QuotaAssumptionV1,
    UsageAccountingV1,
    parse_canonical_audit_bytes,
)
from iclr2027.oacs_claim_ledger import verify_claim_ledger_bytes
from iclr2027.oacs_domain_census import (
    DomainCensusError,
    validate_architecture_census,
    validate_jci_census,
    verify_domain_census_bytes,
)
from iclr2027.oacs_power import (
    PowerPlanError,
    validate_plan_census_binding,
    validate_separate_power_plans,
    verify_domain_power_plan_bytes,
)
from iclr2027.oacs_review_harness import (
    ROLES,
    FindingV1,
    ReviewHarnessError,
    adjudicate_review_union,
    verify_locked_review_bytes,
    verify_locked_reviews,
    verify_review_package_bytes,
)
from iclr2027.oacs_study_contract import OacsStudyContractV1


SCHEMA = "oacs-preflight-receipt/v1"
NO_GO = "no_go_needs_context"
GO = "go_for_separate_execution_plan"
STATUSES = (NO_GO, GO)
REASON_CODES = (
    "architecture_census_insufficient",
    "backend_not_ready",
    "jci_census_insufficient",
    "preoutcome_review_unresolved",
    "prospective_power_insufficient",
    "study_parity_invalid",
)
OPERATION_COUNTER_NAMES = (
    "api_calls",
    "experiments_started",
    "generation_calls",
    "model_calls",
    "network_calls",
    "provider_calls",
    "subprocess_generation_calls",
)
_COMPONENT_NAMES = (
    "approval_trust_root",
    "architecture_census",
    "architecture_power_plan",
    "backend_audit",
    "claim_ledger",
    "governing_design",
    "jci_census",
    "jci_power_plan",
    "review_adversarial_falsifier",
    "review_causal_statistics",
    "review_experiment_reproducibility",
    "review_package",
    "review_problem_novelty",
    "study_contract",
)
_ROOT_KEYS = frozenset(
    {
        "approval_trust_root_sha256",
        "component_sha256",
        "expected_approval_trust_root_sha256",
        "governing_design_sha256",
        "operation_counters",
        "reason_codes",
        "receipt_sha256",
        "review_sha256",
        "schema",
        "status",
        "unresolved_critical_important",
    }
)
_FINDING_KEYS = frozenset(
    {
        "claim_id",
        "evidence_sha256",
        "failure_code",
        "falsifier_result",
        "resolved",
        "severity",
    }
)
_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")


class PreflightError(ValueError):
    """Raised when preflight bytes or cross-bindings are not trustworthy."""


def _require_hash(value: object, label: str) -> str:
    if type(value) is not str or _HASH_RE.fullmatch(value) is None:
        raise PreflightError(f"{label} must be a lowercase SHA-256")
    return value


def _canonical_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    except (TypeError, UnicodeError, ValueError) as exc:
        raise PreflightError("value cannot be represented as canonical JSON") from exc


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PreflightError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_canonical_json(raw: bytes, label: str) -> object:
    if type(raw) is not bytes:
        raise PreflightError(f"{label} must be exact bytes")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                PreflightError(f"invalid JSON constant: {constant}")
            ),
        )
    except PreflightError:
        raise
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise PreflightError(f"{label} is not valid UTF-8 JSON") from exc
    if raw != _canonical_bytes(value):
        raise PreflightError(f"{label} bytes are not canonical JSON")
    return value


def _validate_design_bytes(raw: bytes, expected_sha256: str) -> str:
    if type(raw) is not bytes or not raw or not raw.endswith(b"\n"):
        raise PreflightError(
            "governing design must be nonempty bytes with one final LF"
        )
    if b"\r" in raw or raw.startswith(b"\xef\xbb\xbf"):
        raise PreflightError("governing design must use canonical UTF-8/LF bytes")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreflightError("governing design must be canonical UTF-8") from exc
    expected = _require_hash(expected_sha256, "expected governing design digest")
    observed = sha256(raw).hexdigest()
    if not hmac.compare_digest(observed, expected):
        raise PreflightError("governing design digest is stale or mismatched")
    return observed


@dataclass(frozen=True)
class OacsPreflightInputsV1:
    """Exact raw bytes and independently supplied trust pins for preflight."""

    governing_design_bytes: bytes
    expected_governing_design_sha256: str
    claim_ledger_bytes: bytes
    review_package_bytes: bytes
    locked_review_bytes: tuple[bytes, bytes, bytes, bytes]
    architecture_census_bytes: bytes
    jci_census_bytes: bytes
    study_contract_bytes: bytes
    backend_audit_bytes: bytes
    approval_trust_root_bytes: bytes | None
    expected_approval_trust_root_sha256: str | None
    architecture_power_plan_bytes: bytes
    jci_power_plan_bytes: bytes

    def __post_init__(self) -> None:
        for name in (
            "governing_design_bytes",
            "claim_ledger_bytes",
            "review_package_bytes",
            "architecture_census_bytes",
            "jci_census_bytes",
            "study_contract_bytes",
            "backend_audit_bytes",
            "architecture_power_plan_bytes",
            "jci_power_plan_bytes",
        ):
            if type(getattr(self, name)) is not bytes:
                raise TypeError(f"{name} must be exact bytes")
        _require_hash(
            self.expected_governing_design_sha256,
            "expected_governing_design_sha256",
        )
        if (
            type(self.locked_review_bytes) is not tuple
            or len(self.locked_review_bytes) != 4
        ):
            raise TypeError("locked_review_bytes must be an exact four-item tuple")
        if any(type(raw) is not bytes for raw in self.locked_review_bytes):
            raise TypeError("locked_review_bytes entries must be exact bytes")
        if (
            self.approval_trust_root_bytes is not None
            and type(self.approval_trust_root_bytes) is not bytes
        ):
            raise TypeError("approval_trust_root_bytes must be exact bytes or None")
        if self.expected_approval_trust_root_sha256 is not None:
            _require_hash(
                self.expected_approval_trust_root_sha256,
                "expected_approval_trust_root_sha256",
            )


def _hash_map(
    value: object, *, label: str, keys: tuple[str, ...]
) -> Mapping[str, str | None]:
    if type(value) is not dict or tuple(value) != keys:
        raise PreflightError(f"{label} must contain the exact canonical keys")
    normalized: dict[str, str | None] = {}
    for key in keys:
        item = value[key]
        if key == "approval_trust_root" and item is None:
            normalized[key] = None
        else:
            normalized[key] = _require_hash(item, f"{label}.{key}")
    return MappingProxyType(normalized)


def _review_hash_map(value: object) -> Mapping[str, str]:
    if type(value) is not dict or set(value) != set(ROLES):
        raise PreflightError("review_sha256 must contain the exact frozen roles")
    return MappingProxyType(
        {role: _require_hash(value[role], f"review_sha256.{role}") for role in ROLES}
    )


def _operation_map(value: object) -> Mapping[str, int]:
    if type(value) is not dict or tuple(value) != OPERATION_COUNTER_NAMES:
        raise PreflightError("operation counters must contain the exact canonical keys")
    result: dict[str, int] = {}
    for name in OPERATION_COUNTER_NAMES:
        count = value[name]
        if type(count) is not int or count != 0:
            raise PreflightError("operation counters must be native zero integers")
        result[name] = count
    return MappingProxyType(result)


def _finding_payload(finding: FindingV1) -> dict[str, object]:
    return {
        "claim_id": finding.claim_id,
        "evidence_sha256": finding.evidence_sha256,
        "failure_code": finding.failure_code,
        "falsifier_result": finding.falsifier_result,
        "resolved": finding.resolved,
        "severity": finding.severity,
    }


def _unresolved_findings(value: object) -> tuple[Mapping[str, object], ...]:
    if type(value) not in (list, tuple):
        raise PreflightError("unresolved_critical_important must be a sequence")
    normalized: list[Mapping[str, object]] = []
    for item in value:
        if type(item) is not dict or set(item) != _FINDING_KEYS:
            raise PreflightError(
                "unresolved finding keys do not match the closed schema"
            )
        try:
            finding = FindingV1(
                failure_code=item["failure_code"],
                severity=item["severity"],
                claim_id=item["claim_id"],
                evidence_sha256=item["evidence_sha256"],
                falsifier_result=item["falsifier_result"],
                resolved=item["resolved"],
            )
        except (TypeError, ValueError) as exc:
            raise PreflightError("unresolved finding is invalid") from exc
        if finding.resolved or finding.severity not in ("C", "I"):
            raise PreflightError(
                "only unresolved Critical/Important findings may appear"
            )
        normalized.append(MappingProxyType(_finding_payload(finding)))
    encoded = tuple(_canonical_bytes(dict(item)) for item in normalized)
    if encoded != tuple(sorted(set(encoded))):
        raise PreflightError("unresolved findings must be byte-sorted and unique")
    return tuple(normalized)


def _receipt_body(receipt: OacsPreflightReceiptV1) -> dict[str, object]:
    return {
        "approval_trust_root_sha256": receipt.approval_trust_root_sha256,
        "component_sha256": dict(receipt.component_sha256),
        "expected_approval_trust_root_sha256": (
            receipt.expected_approval_trust_root_sha256
        ),
        "governing_design_sha256": receipt.governing_design_sha256,
        "operation_counters": dict(receipt.operation_counters),
        "reason_codes": list(receipt.reason_codes),
        "review_sha256": dict(receipt.review_sha256),
        "schema": receipt.schema,
        "status": receipt.status,
        "unresolved_critical_important": [
            dict(finding) for finding in receipt.unresolved_critical_important
        ],
    }


@dataclass(frozen=True)
class OacsPreflightReceiptV1:
    schema: str
    governing_design_sha256: str
    component_sha256: Mapping[str, str | None]
    review_sha256: Mapping[str, str]
    approval_trust_root_sha256: str | None
    expected_approval_trust_root_sha256: str | None
    status: str
    reason_codes: tuple[str, ...]
    unresolved_critical_important: tuple[Mapping[str, object], ...]
    operation_counters: Mapping[str, int]
    receipt_sha256: str

    def __post_init__(self) -> None:
        if self.schema != SCHEMA:
            raise PreflightError("receipt schema is not supported")
        _require_hash(self.governing_design_sha256, "governing_design_sha256")
        component_hashes = _hash_map(
            self.component_sha256,
            label="component_sha256",
            keys=_COMPONENT_NAMES,
        )
        reviews = _review_hash_map(self.review_sha256)
        operations = _operation_map(self.operation_counters)
        unresolved = _unresolved_findings(self.unresolved_critical_important)
        object.__setattr__(self, "component_sha256", component_hashes)
        object.__setattr__(self, "review_sha256", reviews)
        object.__setattr__(self, "operation_counters", operations)
        object.__setattr__(self, "unresolved_critical_important", unresolved)
        for role in ROLES:
            if reviews[role] != component_hashes[f"review_{role}"]:
                raise PreflightError("review identities disagree with component hashes")
        actual_approval = self.approval_trust_root_sha256
        if actual_approval is not None:
            _require_hash(actual_approval, "approval_trust_root_sha256")
        expected_approval = self.expected_approval_trust_root_sha256
        if expected_approval is not None:
            _require_hash(
                expected_approval,
                "expected_approval_trust_root_sha256",
            )
        if actual_approval != component_hashes["approval_trust_root"]:
            raise PreflightError("approval identity disagrees with component hash")
        if component_hashes["governing_design"] != self.governing_design_sha256:
            raise PreflightError(
                "governing design identity disagrees with component hash"
            )
        if type(self.reason_codes) is not tuple or any(
            type(reason) is not str or reason not in REASON_CODES
            for reason in self.reason_codes
        ):
            raise PreflightError("reason codes are outside the closed vocabulary")
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise PreflightError("reason codes must be byte-sorted and unique")
        expected_status = GO if not self.reason_codes else NO_GO
        if self.status not in STATUSES or self.status != expected_status:
            raise PreflightError("receipt status does not match its reasons")
        approval_is_bound = (
            actual_approval is not None
            and expected_approval is not None
            and hmac.compare_digest(actual_approval, expected_approval)
        )
        if not approval_is_bound and "backend_not_ready" not in self.reason_codes:
            raise PreflightError("approval identity mismatch cannot produce GO")
        if unresolved and "preoutcome_review_unresolved" not in self.reason_codes:
            raise PreflightError("unresolved review findings must block preflight")
        _require_hash(self.receipt_sha256, "receipt_sha256")
        expected_self_hash = sha256(_canonical_bytes(_receipt_body(self))).hexdigest()
        if not hmac.compare_digest(self.receipt_sha256, expected_self_hash):
            raise PreflightError("receipt self-hash does not match")


def _create_receipt(
    *,
    governing_design_sha256: str,
    component_sha256: dict[str, str | None],
    review_sha256: dict[str, str],
    approval_trust_root_sha256: str | None,
    expected_approval_trust_root_sha256: str | None,
    reason_codes: tuple[str, ...],
    unresolved_critical_important: tuple[dict[str, object], ...],
) -> OacsPreflightReceiptV1:
    body = {
        "approval_trust_root_sha256": approval_trust_root_sha256,
        "component_sha256": component_sha256,
        "expected_approval_trust_root_sha256": expected_approval_trust_root_sha256,
        "governing_design_sha256": governing_design_sha256,
        "operation_counters": {name: 0 for name in OPERATION_COUNTER_NAMES},
        "reason_codes": list(reason_codes),
        "review_sha256": review_sha256,
        "schema": SCHEMA,
        "status": GO if not reason_codes else NO_GO,
        "unresolved_critical_important": list(unresolved_critical_important),
    }
    return OacsPreflightReceiptV1(
        schema=SCHEMA,
        governing_design_sha256=governing_design_sha256,
        component_sha256=component_sha256,
        review_sha256=review_sha256,
        approval_trust_root_sha256=approval_trust_root_sha256,
        expected_approval_trust_root_sha256=expected_approval_trust_root_sha256,
        status=body["status"],
        reason_codes=reason_codes,
        unresolved_critical_important=unresolved_critical_important,
        operation_counters=body["operation_counters"],
        receipt_sha256=sha256(_canonical_bytes(body)).hexdigest(),
    )


def _approval_from_bytes(raw: bytes) -> ApprovalTrustRootV1:
    payload = _parse_canonical_json(raw, "approval trust root")
    if type(payload) is not dict:
        raise PreflightError("approval trust root must be a JSON object")
    values = dict(payload)
    expected_keys = frozenset(ApprovalTrustRootV1.__dataclass_fields__)
    if set(values) != expected_keys:
        raise PreflightError("approval trust root keys do not match the closed schema")
    quota = values["quota_assumptions"]
    if type(quota) is not list:
        raise PreflightError("approval quota assumptions must be a JSON array")
    try:
        values["quota_assumptions"] = tuple(
            QuotaAssumptionV1.from_mapping(item) for item in quota
        )
        values["usage_accounting"] = UsageAccountingV1.from_mapping(
            values["usage_accounting"]
        )
        approval = ApprovalTrustRootV1(**values)
    except (TypeError, ValueError) as exc:
        raise PreflightError("approval trust root is invalid") from exc
    if approval.canonical_bytes() != raw:
        raise PreflightError("approval trust root bytes are not canonical")
    return approval


def _backend_matches_approval(
    audit: BackendAuditV1,
    approval: ApprovalTrustRootV1 | None,
    actual_digest: str | None,
    expected_digest: str | None,
) -> bool:
    if (
        audit.status != READY
        or approval is None
        or actual_digest is None
        or expected_digest is None
        or not hmac.compare_digest(actual_digest, expected_digest)
    ):
        return False
    return all(
        (
            audit.executable_sha256 == approval.executable_sha256,
            audit.runtime_version == approval.runtime_version,
            audit.adapter_sha256 == approval.adapter_sha256,
            audit.model_id == approval.model_id,
            audit.auth_mode == approval.auth_mode,
            audit.quota_mode == approval.quota_mode,
            audit.quota_assumptions == approval.quota_assumptions,
            audit.invoice_approval_id == approval.invoice_approval_id,
            audit.maximum_marginal_cost_microunits
            == approval.maximum_marginal_cost_microunits,
            audit.timeout_seconds == approval.timeout_seconds,
            audit.retry_count == approval.retry_count,
            audit.usage_accounting == approval.usage_accounting,
            audit.evidence_provenance == approval.required_evidence_provenance,
        )
    )


def evaluate_preflight(inputs: OacsPreflightInputsV1) -> OacsPreflightReceiptV1:
    """Evaluate every gate from exact component bytes and cross-bindings."""

    if type(inputs) is not OacsPreflightInputsV1:
        raise TypeError("inputs must be an exact OacsPreflightInputsV1")
    design_hash = _validate_design_bytes(
        inputs.governing_design_bytes,
        inputs.expected_governing_design_sha256,
    )
    try:
        ledger = verify_claim_ledger_bytes(inputs.claim_ledger_bytes)
    except (TypeError, ValueError) as exc:
        raise PreflightError("claim ledger is not canonical and valid") from exc
    if ledger.design_sha256 != design_hash:
        raise PreflightError("claim ledger governing-design binding is stale")

    try:
        architecture = verify_domain_census_bytes(inputs.architecture_census_bytes)
        jci = verify_domain_census_bytes(inputs.jci_census_bytes)
        audit = parse_canonical_audit_bytes(inputs.backend_audit_bytes)
        architecture_power = verify_domain_power_plan_bytes(
            inputs.architecture_power_plan_bytes
        )
        jci_power = verify_domain_power_plan_bytes(inputs.jci_power_plan_bytes)
        review_package = verify_review_package_bytes(inputs.review_package_bytes)
        reviews = tuple(
            verify_locked_review_bytes(raw) for raw in inputs.locked_review_bytes
        )
    except (TypeError, ValueError) as exc:
        raise PreflightError(
            "a preflight component is not canonical and valid"
        ) from exc

    _parse_canonical_json(inputs.study_contract_bytes, "study contract")
    study_contract: OacsStudyContractV1 | None
    try:
        study_contract = OacsStudyContractV1.from_bytes(inputs.study_contract_bytes)
    except (TypeError, ValueError):
        study_contract = None

    approval: ApprovalTrustRootV1 | None = None
    approval_digest: str | None = None
    if inputs.approval_trust_root_bytes is not None:
        approval = _approval_from_bytes(inputs.approval_trust_root_bytes)
        approval_digest = sha256(inputs.approval_trust_root_bytes).hexdigest()

    if review_package.claim_ledger_sha256 != sha256(
        inputs.claim_ledger_bytes
    ).hexdigest() or review_package.claim_ids != tuple(
        record.claim_id for record in ledger.records
    ):
        raise PreflightError("review package is not bound to the exact claim ledger")
    required_review_sources = {
        sha256(raw).hexdigest()
        for raw in (
            inputs.governing_design_bytes,
            inputs.architecture_census_bytes,
            inputs.jci_census_bytes,
            inputs.study_contract_bytes,
            inputs.backend_audit_bytes,
            inputs.architecture_power_plan_bytes,
            inputs.jci_power_plan_bytes,
        )
    }
    reviewed_approval_digest = (
        approval_digest
        if approval_digest is not None
        else inputs.expected_approval_trust_root_sha256
    )
    if reviewed_approval_digest is not None:
        required_review_sources.add(reviewed_approval_digest)
    if required_review_sources != set(review_package.source_sha256):
        raise PreflightError(
            "review package must bind the exact preflight component hashes"
        )
    try:
        reviews = verify_locked_reviews(review_package, reviews)
        finding_union = adjudicate_review_union(
            review_package,
            reviews,
            proposed_status="hold",
        )
    except ReviewHarnessError as exc:
        raise PreflightError("locked reviews are not package-bound") from exc

    try:
        validate_plan_census_binding(
            plan=architecture_power,
            census_bytes=inputs.architecture_census_bytes,
        )
        validate_plan_census_binding(
            plan=jci_power,
            census_bytes=inputs.jci_census_bytes,
        )
    except (TypeError, PowerPlanError) as exc:
        raise PreflightError("power plan and exact census binding disagree") from exc
    if (architecture_power.domain, jci_power.domain) != ("architecture", "jci"):
        raise PreflightError("power plans must preserve the two-domain order")

    reasons: set[str] = set()
    try:
        validate_architecture_census(architecture)
    except DomainCensusError:
        reasons.add("architecture_census_insufficient")
    try:
        validate_jci_census(jci)
    except DomainCensusError:
        reasons.add("jci_census_insufficient")
    if study_contract is None:
        reasons.add("study_parity_invalid")
    if not _backend_matches_approval(
        audit,
        approval,
        approval_digest,
        inputs.expected_approval_trust_root_sha256,
    ):
        reasons.add("backend_not_ready")
    try:
        validate_separate_power_plans((architecture_power, jci_power))
    except (TypeError, PowerPlanError):
        reasons.add("prospective_power_insufficient")

    unresolved = tuple(
        _finding_payload(finding)
        for finding in finding_union
        if not finding.resolved and finding.severity in ("C", "I")
    )
    unresolved = tuple(sorted(unresolved, key=_canonical_bytes))
    if unresolved or any(review.verdict != "ACCEPT" for review in reviews):
        reasons.add("preoutcome_review_unresolved")

    review_hashes = {
        role: sha256(raw).hexdigest()
        for role, raw in zip(ROLES, inputs.locked_review_bytes, strict=True)
    }
    component_hashes: dict[str, str | None] = {
        "approval_trust_root": approval_digest,
        "architecture_census": sha256(inputs.architecture_census_bytes).hexdigest(),
        "architecture_power_plan": sha256(
            inputs.architecture_power_plan_bytes
        ).hexdigest(),
        "backend_audit": sha256(inputs.backend_audit_bytes).hexdigest(),
        "claim_ledger": sha256(inputs.claim_ledger_bytes).hexdigest(),
        "governing_design": design_hash,
        "jci_census": sha256(inputs.jci_census_bytes).hexdigest(),
        "jci_power_plan": sha256(inputs.jci_power_plan_bytes).hexdigest(),
        "review_adversarial_falsifier": review_hashes["adversarial_falsifier"],
        "review_causal_statistics": review_hashes["causal_statistics"],
        "review_experiment_reproducibility": review_hashes[
            "experiment_reproducibility"
        ],
        "review_package": sha256(inputs.review_package_bytes).hexdigest(),
        "review_problem_novelty": review_hashes["problem_novelty"],
        "study_contract": sha256(inputs.study_contract_bytes).hexdigest(),
    }
    return _create_receipt(
        governing_design_sha256=design_hash,
        component_sha256=component_hashes,
        review_sha256=review_hashes,
        approval_trust_root_sha256=approval_digest,
        expected_approval_trust_root_sha256=(
            inputs.expected_approval_trust_root_sha256
        ),
        reason_codes=tuple(sorted(reasons)),
        unresolved_critical_important=unresolved,
    )


def preflight_receipt_bytes(receipt: OacsPreflightReceiptV1) -> bytes:
    """Return the sole canonical UTF-8/LF representation of a receipt."""

    if type(receipt) is not OacsPreflightReceiptV1:
        raise TypeError("receipt must be an exact OacsPreflightReceiptV1")
    payload = {**_receipt_body(receipt), "receipt_sha256": receipt.receipt_sha256}
    return _canonical_bytes(payload)


def verify_preflight_receipt_bytes(raw: bytes) -> OacsPreflightReceiptV1:
    """Verify canonical structure, native types, closed values, and self-hash."""

    payload = _parse_canonical_json(raw, "preflight receipt")
    if type(payload) is not dict or set(payload) != _ROOT_KEYS:
        raise PreflightError("preflight receipt keys do not match the closed schema")
    reason_codes = payload["reason_codes"]
    unresolved = payload["unresolved_critical_important"]
    if type(reason_codes) is not list or type(unresolved) is not list:
        raise PreflightError("receipt arrays must use native JSON arrays")
    try:
        receipt = OacsPreflightReceiptV1(
            schema=payload["schema"],
            governing_design_sha256=payload["governing_design_sha256"],
            component_sha256=payload["component_sha256"],
            review_sha256=payload["review_sha256"],
            approval_trust_root_sha256=payload["approval_trust_root_sha256"],
            expected_approval_trust_root_sha256=payload[
                "expected_approval_trust_root_sha256"
            ],
            status=payload["status"],
            reason_codes=tuple(reason_codes),
            unresolved_critical_important=tuple(unresolved),
            operation_counters=payload["operation_counters"],
            receipt_sha256=payload["receipt_sha256"],
        )
    except PreflightError:
        raise
    except (TypeError, ValueError) as exc:
        raise PreflightError("preflight receipt values are invalid") from exc
    if preflight_receipt_bytes(receipt) != raw:
        raise PreflightError("preflight receipt bytes are not canonical")
    return receipt


def validate_preflight_receipt_bytes(
    raw: bytes,
    inputs: OacsPreflightInputsV1,
) -> bytes:
    """Re-evaluate exact inputs and require the receipt to be byte-identical."""

    verify_preflight_receipt_bytes(raw)
    expected = preflight_receipt_bytes(evaluate_preflight(inputs))
    if not hmac.compare_digest(raw, expected):
        raise PreflightError("preflight receipt does not match the exact inputs")
    return raw


__all__ = (
    "GO",
    "NO_GO",
    "OPERATION_COUNTER_NAMES",
    "OacsPreflightInputsV1",
    "OacsPreflightReceiptV1",
    "PreflightError",
    "REASON_CODES",
    "SCHEMA",
    "STATUSES",
    "evaluate_preflight",
    "preflight_receipt_bytes",
    "validate_preflight_receipt_bytes",
    "verify_preflight_receipt_bytes",
)
