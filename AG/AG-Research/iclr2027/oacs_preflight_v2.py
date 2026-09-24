"""Versioned MAS/OACS preflight support for typed unavailable components.

Positive component slots remain exact canonical v1 bytes.  This module adds
only a closed negative envelope and a parallel v2 receipt; it never promotes
missing authority to readiness.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import hmac
import json
import re
from types import MappingProxyType

from iclr2027.oacs_backend_audit import parse_canonical_audit_bytes
from iclr2027.oacs_claim_ledger import verify_claim_ledger_bytes
from iclr2027.oacs_domain_census import (
    DomainCensusError,
    DomainCensusV1,
    validate_architecture_census,
    validate_jci_census,
    verify_domain_census_bytes,
)
from iclr2027.oacs_power import (
    DomainPowerPlanV1,
    PowerPlanError,
    validate_plan_census_binding,
    validate_separate_power_plans,
    verify_domain_power_plan_bytes,
)
from iclr2027 import oacs_preflight as _v1
from iclr2027.oacs_preflight import (
    GO,
    NO_GO,
    OPERATION_COUNTER_NAMES,
    OacsPreflightInputsV1,
    PreflightError,
    REASON_CODES,
    evaluate_preflight,
)
from iclr2027.oacs_review_harness import (
    ROLES,
    ReviewHarnessError,
    adjudicate_review_union,
    verify_locked_review_bytes,
    verify_locked_reviews,
    verify_review_package_bytes,
)
from iclr2027.oacs_study_contract import OacsStudyContractV1


UNAVAILABLE_SCHEMA = "oacs-component-unavailable/v1"
SCHEMA = "oacs-preflight-receipt/v2"
UNAVAILABLE_STATUSES = (NO_GO, "not_assessable")
UNAVAILABLE_COMPONENTS = (
    "architecture_census",
    "architecture_power_plan",
    "jci_census",
    "jci_power_plan",
    "study_contract",
)
ARCHITECTURE_CENSUS_CODES = (
    "accepted_source_rights_absent",
    "blind_overlap_commitment_absent",
    "evaluator_commitment_absent",
    "no_admissible_units",
    "obligation_family_authority_absent",
    "partition_commitment_absent",
    "public_packet_commitment_absent",
    "source_manifest_commitment_absent",
    "unit_declarations_incomplete",
)
JCI_CENSUS_CODES = (
    "explicit_domain_declaration_absent",
    "no_admissible_units",
)
POWER_CODES = (
    "prospective_power_authority_absent",
    "upstream_census_unavailable",
)
STUDY_CONTRACT_CODES = (
    "budget_authority_absent",
    "capability_catalog_absent",
    "capability_crossover_absent",
    "common_synthesizer_absent",
    "e3_readiness_authority_absent",
    "model_binding_absent",
    "public_input_projection_absent",
    "retry_policy_absent",
    "terminal_evaluator_absent",
    "tool_catalog_authority_absent",
    "usage_accounting_absent",
)

_CODES_BY_COMPONENT = {
    "architecture_census": ARCHITECTURE_CENSUS_CODES,
    "jci_census": JCI_CENSUS_CODES,
    "architecture_power_plan": POWER_CODES,
    "jci_power_plan": POWER_CODES,
    "study_contract": STUDY_CONTRACT_CODES,
}
_UNAVAILABLE_KEYS = frozenset(
    {
        "admissible_unit_count",
        "component",
        "missing_authority_codes",
        "schema",
        "status",
        "supplied_authority_sha256",
        "upstream_component_sha256",
    }
)
_PROJECTION_KEYS = frozenset(_UNAVAILABLE_KEYS - {"schema"} | {"component_sha256"})
_ROOT_KEYS = frozenset(_v1._ROOT_KEYS | {"unavailable_components"})
_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_CENSUS_COMPONENTS = frozenset({"architecture_census", "jci_census"})
_POWER_COMPONENTS = frozenset({"architecture_power_plan", "jci_power_plan"})
_REASON_BY_COMPONENT = {
    "architecture_census": "architecture_census_insufficient",
    "jci_census": "jci_census_insufficient",
    "architecture_power_plan": "prospective_power_insufficient",
    "jci_power_plan": "prospective_power_insufficient",
    "study_contract": "study_parity_invalid",
}


class PreflightV2Error(PreflightError):
    """Raised when a v2 envelope, receipt, or cross-binding is invalid."""


def _require_hash(value: object, label: str) -> str:
    if type(value) is not str or _HASH_RE.fullmatch(value) is None:
        raise PreflightV2Error(f"{label} must be a lowercase SHA-256")
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
        raise PreflightV2Error("value cannot be represented as canonical JSON") from exc


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PreflightV2Error(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_canonical_json(raw: bytes, label: str) -> object:
    if type(raw) is not bytes:
        raise PreflightV2Error(f"{label} must be exact bytes")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                PreflightV2Error(f"invalid JSON constant: {constant}")
            ),
        )
    except PreflightV2Error:
        raise
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise PreflightV2Error(f"{label} is not valid UTF-8 JSON") from exc
    if raw != _canonical_bytes(value):
        raise PreflightV2Error(f"{label} bytes are not canonical JSON")
    return value


def _require_sorted_strings(
    value: object,
    *,
    label: str,
    allowed: tuple[str, ...],
    nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise PreflightV2Error(f"{label} must be an exact tuple")
    if nonempty and not value:
        raise PreflightV2Error(f"{label} must be nonempty")
    if any(type(item) is not str or item not in allowed for item in value):
        raise PreflightV2Error(f"{label} contains a code outside its component")
    if value != tuple(sorted(set(value), key=lambda item: item.encode("utf-8"))):
        raise PreflightV2Error(f"{label} must be byte-sorted and unique")
    return value


def _require_sorted_hashes(value: object, label: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise PreflightV2Error(f"{label} must be an exact tuple")
    for item in value:
        _require_hash(item, f"{label} entry")
    if value != tuple(sorted(set(value), key=lambda item: item.encode("utf-8"))):
        raise PreflightV2Error(f"{label} must be byte-sorted and unique")
    return value


@dataclass(frozen=True)
class UnavailableComponentV1:
    """A closed declaration that one exact aggregate slot lacks authority."""

    schema: str
    component: str
    status: str
    missing_authority_codes: tuple[str, ...]
    admissible_unit_count: int | None
    upstream_component_sha256: str | None
    supplied_authority_sha256: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema != UNAVAILABLE_SCHEMA:
            raise PreflightV2Error("unavailable component schema is not supported")
        if self.component not in UNAVAILABLE_COMPONENTS:
            raise PreflightV2Error("unavailable component is not a closed slot")
        if self.status not in UNAVAILABLE_STATUSES:
            raise PreflightV2Error("unavailable status is not a closed negative state")
        codes = _require_sorted_strings(
            self.missing_authority_codes,
            label="missing_authority_codes",
            allowed=_CODES_BY_COMPONENT[self.component],
            nonempty=True,
        )
        supplied = _require_sorted_hashes(
            self.supplied_authority_sha256,
            "supplied_authority_sha256",
        )
        object.__setattr__(self, "missing_authority_codes", codes)
        object.__setattr__(self, "supplied_authority_sha256", supplied)

        if self.component in _CENSUS_COMPONENTS:
            if type(self.admissible_unit_count) is not int:
                raise PreflightV2Error(
                    "census admissible_unit_count must be a native integer"
                )
            if self.admissible_unit_count != 0:
                raise PreflightV2Error(
                    "census admissible_unit_count must be exactly zero"
                )
            if "no_admissible_units" not in codes:
                raise PreflightV2Error(
                    "census unavailable state must include no_admissible_units"
                )
            if self.upstream_component_sha256 is not None:
                raise PreflightV2Error("census upstream component must be null")
        else:
            if self.admissible_unit_count is not None:
                raise PreflightV2Error("non-census admissible_unit_count must be null")
            if self.component == "study_contract":
                if self.upstream_component_sha256 is not None:
                    raise PreflightV2Error("study upstream component must be null")
            else:
                _require_hash(
                    self.upstream_component_sha256,
                    "power upstream_component_sha256",
                )


def _unavailable_body(value: UnavailableComponentV1) -> dict[str, object]:
    return {
        "admissible_unit_count": value.admissible_unit_count,
        "component": value.component,
        "missing_authority_codes": list(value.missing_authority_codes),
        "schema": value.schema,
        "status": value.status,
        "supplied_authority_sha256": list(value.supplied_authority_sha256),
        "upstream_component_sha256": value.upstream_component_sha256,
    }


def unavailable_component_bytes(value: UnavailableComponentV1) -> bytes:
    """Return the sole canonical representation of an unavailable component."""

    if type(value) is not UnavailableComponentV1:
        raise TypeError("value must be an exact UnavailableComponentV1")
    return _canonical_bytes(_unavailable_body(value))


def verify_unavailable_component_bytes(
    raw: bytes,
    *,
    expected_component: str | None = None,
) -> UnavailableComponentV1:
    """Parse a canonical negative envelope and optionally bind its exact slot."""

    payload = _parse_canonical_json(raw, "unavailable component")
    if type(payload) is not dict or set(payload) != _UNAVAILABLE_KEYS:
        raise PreflightV2Error(
            "unavailable component keys do not match the closed schema"
        )
    codes = payload["missing_authority_codes"]
    supplied = payload["supplied_authority_sha256"]
    if type(codes) is not list or type(supplied) is not list:
        raise PreflightV2Error("unavailable component arrays must be JSON arrays")
    try:
        result = UnavailableComponentV1(
            schema=payload["schema"],
            component=payload["component"],
            status=payload["status"],
            missing_authority_codes=tuple(codes),
            admissible_unit_count=payload["admissible_unit_count"],
            upstream_component_sha256=payload["upstream_component_sha256"],
            supplied_authority_sha256=tuple(supplied),
        )
    except PreflightV2Error:
        raise
    except (TypeError, ValueError) as exc:
        raise PreflightV2Error("unavailable component values are invalid") from exc
    if expected_component is not None and result.component != expected_component:
        raise PreflightV2Error("unavailable component does not match its exact slot")
    if unavailable_component_bytes(result) != raw:
        raise PreflightV2Error("unavailable component bytes are not canonical")
    return result


@dataclass(frozen=True)
class OacsPreflightInputsV2:
    """Exact raw v1-positive or v1-unavailable component slot bytes."""

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
        _as_v1_inputs(self)


def _as_v1_inputs(inputs: OacsPreflightInputsV2) -> OacsPreflightInputsV1:
    return OacsPreflightInputsV1(
        governing_design_bytes=inputs.governing_design_bytes,
        expected_governing_design_sha256=inputs.expected_governing_design_sha256,
        claim_ledger_bytes=inputs.claim_ledger_bytes,
        review_package_bytes=inputs.review_package_bytes,
        locked_review_bytes=inputs.locked_review_bytes,
        architecture_census_bytes=inputs.architecture_census_bytes,
        jci_census_bytes=inputs.jci_census_bytes,
        study_contract_bytes=inputs.study_contract_bytes,
        backend_audit_bytes=inputs.backend_audit_bytes,
        approval_trust_root_bytes=inputs.approval_trust_root_bytes,
        expected_approval_trust_root_sha256=(
            inputs.expected_approval_trust_root_sha256
        ),
        architecture_power_plan_bytes=inputs.architecture_power_plan_bytes,
        jci_power_plan_bytes=inputs.jci_power_plan_bytes,
    )


def _parse_census_slot(
    raw: bytes,
    component: str,
) -> DomainCensusV1 | UnavailableComponentV1:
    payload = _parse_canonical_json(raw, component)
    if type(payload) is dict and payload.get("schema") == UNAVAILABLE_SCHEMA:
        return verify_unavailable_component_bytes(raw, expected_component=component)
    try:
        census = verify_domain_census_bytes(raw)
    except (TypeError, ValueError) as exc:
        raise PreflightV2Error(f"{component} is not valid canonical v1 bytes") from exc
    expected_domain = component.removesuffix("_census")
    if any(unit.domain != expected_domain for unit in census.units):
        raise PreflightV2Error(f"{component} contains the wrong domain")
    return census


def _parse_power_slot(
    raw: bytes,
    component: str,
) -> DomainPowerPlanV1 | UnavailableComponentV1:
    payload = _parse_canonical_json(raw, component)
    if type(payload) is dict and payload.get("schema") == UNAVAILABLE_SCHEMA:
        return verify_unavailable_component_bytes(raw, expected_component=component)
    try:
        plan = verify_domain_power_plan_bytes(raw)
    except (TypeError, ValueError) as exc:
        raise PreflightV2Error(f"{component} is not valid canonical v1 bytes") from exc
    expected_domain = component.removesuffix("_power_plan")
    if plan.domain != expected_domain:
        raise PreflightV2Error(f"{component} contains the wrong domain")
    return plan


def _parse_study_slot(
    raw: bytes,
) -> OacsStudyContractV1 | UnavailableComponentV1:
    payload = _parse_canonical_json(raw, "study_contract")
    if type(payload) is dict and payload.get("schema") == UNAVAILABLE_SCHEMA:
        return verify_unavailable_component_bytes(
            raw,
            expected_component="study_contract",
        )
    try:
        return OacsStudyContractV1.from_bytes(raw)
    except (TypeError, ValueError) as exc:
        raise PreflightV2Error(
            "study_contract is not valid canonical v1 bytes"
        ) from exc


def _projection(
    value: UnavailableComponentV1,
    component_sha256: str,
) -> dict[str, object]:
    return {
        "admissible_unit_count": value.admissible_unit_count,
        "component": value.component,
        "component_sha256": component_sha256,
        "missing_authority_codes": value.missing_authority_codes,
        "status": value.status,
        "supplied_authority_sha256": value.supplied_authority_sha256,
        "upstream_component_sha256": value.upstream_component_sha256,
    }


def _normalize_unavailable_components(
    value: object,
    component_sha256: Mapping[str, str | None],
) -> tuple[Mapping[str, object], ...]:
    if type(value) not in (tuple, list):
        raise PreflightV2Error("unavailable_components must be a sequence")
    normalized: list[Mapping[str, object]] = []
    components: set[str] = set()
    for item in value:
        if type(item) is not dict or set(item) != _PROJECTION_KEYS:
            raise PreflightV2Error(
                "unavailable component projection keys do not match the schema"
            )
        codes = item["missing_authority_codes"]
        supplied = item["supplied_authority_sha256"]
        if type(codes) not in (list, tuple) or type(supplied) not in (list, tuple):
            raise PreflightV2Error(
                "unavailable component projection arrays are invalid"
            )
        envelope = UnavailableComponentV1(
            schema=UNAVAILABLE_SCHEMA,
            component=item["component"],
            status=item["status"],
            missing_authority_codes=tuple(codes),
            admissible_unit_count=item["admissible_unit_count"],
            upstream_component_sha256=item["upstream_component_sha256"],
            supplied_authority_sha256=tuple(supplied),
        )
        digest = _require_hash(item["component_sha256"], "component_sha256")
        if not hmac.compare_digest(
            digest,
            sha256(unavailable_component_bytes(envelope)).hexdigest(),
        ):
            raise PreflightV2Error(
                "unavailable projection digest does not match its envelope"
            )
        if envelope.component in components:
            raise PreflightV2Error("unavailable component slots must be unique")
        components.add(envelope.component)
        if component_sha256[envelope.component] != digest:
            raise PreflightV2Error(
                "unavailable projection disagrees with component hashes"
            )
        normalized.append(MappingProxyType(_projection(envelope, digest)))
    encoded = tuple(_canonical_bytes(dict(item)) for item in normalized)
    if encoded != tuple(sorted(set(encoded))):
        raise PreflightV2Error("unavailable_components must be byte-sorted and unique")
    by_component = {item["component"]: item for item in normalized}
    for domain in ("architecture", "jci"):
        census_name = f"{domain}_census"
        power_name = f"{domain}_power_plan"
        census = by_component.get(census_name)
        power = by_component.get(power_name)
        if census is not None and power is None:
            raise PreflightV2Error(
                "unavailable census requires unavailable matching power"
            )
        if power is not None:
            if power["upstream_component_sha256"] != component_sha256[census_name]:
                raise PreflightV2Error(
                    "unavailable power does not bind its exact census slot"
                )
            upstream_missing = (
                "upstream_census_unavailable" in power["missing_authority_codes"]
            )
            if upstream_missing != (census is not None):
                raise PreflightV2Error(
                    "power missing-authority state disagrees with its census slot"
                )
    return tuple(normalized)


def _receipt_body(receipt: OacsPreflightReceiptV2) -> dict[str, object]:
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
        "unavailable_components": [
            dict(item) for item in receipt.unavailable_components
        ],
        "unresolved_critical_important": [
            dict(finding) for finding in receipt.unresolved_critical_important
        ],
    }


@dataclass(frozen=True)
class OacsPreflightReceiptV2:
    schema: str
    governing_design_sha256: str
    component_sha256: Mapping[str, str | None]
    review_sha256: Mapping[str, str]
    approval_trust_root_sha256: str | None
    expected_approval_trust_root_sha256: str | None
    status: str
    reason_codes: tuple[str, ...]
    unavailable_components: tuple[Mapping[str, object], ...]
    unresolved_critical_important: tuple[Mapping[str, object], ...]
    operation_counters: Mapping[str, int]
    receipt_sha256: str

    def __post_init__(self) -> None:
        if self.schema != SCHEMA:
            raise PreflightV2Error("receipt schema is not supported")
        _require_hash(self.governing_design_sha256, "governing_design_sha256")
        try:
            component_hashes = _v1._hash_map(
                self.component_sha256,
                label="component_sha256",
                keys=_v1._COMPONENT_NAMES,
            )
            reviews = _v1._review_hash_map(self.review_sha256)
            operations = _v1._operation_map(self.operation_counters)
            unresolved = _v1._unresolved_findings(self.unresolved_critical_important)
        except (PreflightError, TypeError, ValueError) as exc:
            raise PreflightV2Error(str(exc)) from exc
        unavailable = _normalize_unavailable_components(
            self.unavailable_components,
            component_hashes,
        )
        object.__setattr__(self, "component_sha256", component_hashes)
        object.__setattr__(self, "review_sha256", reviews)
        object.__setattr__(self, "operation_counters", operations)
        object.__setattr__(self, "unresolved_critical_important", unresolved)
        object.__setattr__(self, "unavailable_components", unavailable)
        for role in ROLES:
            if reviews[role] != component_hashes[f"review_{role}"]:
                raise PreflightV2Error(
                    "review identities disagree with component hashes"
                )
        actual_approval = self.approval_trust_root_sha256
        expected_approval = self.expected_approval_trust_root_sha256
        if actual_approval is not None:
            _require_hash(actual_approval, "approval_trust_root_sha256")
        if expected_approval is not None:
            _require_hash(
                expected_approval,
                "expected_approval_trust_root_sha256",
            )
        if actual_approval != component_hashes["approval_trust_root"]:
            raise PreflightV2Error("approval identity disagrees with component hash")
        if component_hashes["governing_design"] != self.governing_design_sha256:
            raise PreflightV2Error(
                "governing design identity disagrees with component hash"
            )
        if type(self.reason_codes) is not tuple or any(
            type(reason) is not str or reason not in REASON_CODES
            for reason in self.reason_codes
        ):
            raise PreflightV2Error("reason codes are outside the closed vocabulary")
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise PreflightV2Error("reason codes must be byte-sorted and unique")
        expected_status = GO if not self.reason_codes else NO_GO
        if self.status != expected_status:
            raise PreflightV2Error("receipt status does not match its reasons")
        if unavailable and self.status != NO_GO:
            raise PreflightV2Error("unavailable components cannot produce GO")
        for row in unavailable:
            if _REASON_BY_COMPONENT[row["component"]] not in self.reason_codes:
                raise PreflightV2Error(
                    "unavailable component aggregate reason is missing"
                )
        approval_is_bound = (
            actual_approval is not None
            and expected_approval is not None
            and hmac.compare_digest(actual_approval, expected_approval)
        )
        if not approval_is_bound and "backend_not_ready" not in self.reason_codes:
            raise PreflightV2Error("approval identity mismatch cannot produce GO")
        if unresolved and "preoutcome_review_unresolved" not in self.reason_codes:
            raise PreflightV2Error("unresolved review findings must block preflight")
        _require_hash(self.receipt_sha256, "receipt_sha256")
        expected_self_hash = sha256(_canonical_bytes(_receipt_body(self))).hexdigest()
        if not hmac.compare_digest(self.receipt_sha256, expected_self_hash):
            raise PreflightV2Error("receipt self-hash does not match")


def _create_receipt(
    *,
    governing_design_sha256: str,
    component_sha256: dict[str, str | None],
    review_sha256: dict[str, str],
    approval_trust_root_sha256: str | None,
    expected_approval_trust_root_sha256: str | None,
    reason_codes: tuple[str, ...],
    unavailable_components: tuple[dict[str, object], ...],
    unresolved_critical_important: tuple[dict[str, object], ...],
) -> OacsPreflightReceiptV2:
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
        "unavailable_components": list(unavailable_components),
        "unresolved_critical_important": list(unresolved_critical_important),
    }
    return OacsPreflightReceiptV2(
        schema=SCHEMA,
        governing_design_sha256=governing_design_sha256,
        component_sha256=component_sha256,
        review_sha256=review_sha256,
        approval_trust_root_sha256=approval_trust_root_sha256,
        expected_approval_trust_root_sha256=expected_approval_trust_root_sha256,
        status=body["status"],
        reason_codes=reason_codes,
        unavailable_components=unavailable_components,
        unresolved_critical_important=unresolved_critical_important,
        operation_counters=body["operation_counters"],
        receipt_sha256=sha256(_canonical_bytes(body)).hexdigest(),
    )


def _receipt_from_v1(receipt: _v1.OacsPreflightReceiptV1) -> OacsPreflightReceiptV2:
    return _create_receipt(
        governing_design_sha256=receipt.governing_design_sha256,
        component_sha256=dict(receipt.component_sha256),
        review_sha256=dict(receipt.review_sha256),
        approval_trust_root_sha256=receipt.approval_trust_root_sha256,
        expected_approval_trust_root_sha256=(
            receipt.expected_approval_trust_root_sha256
        ),
        reason_codes=receipt.reason_codes,
        unavailable_components=(),
        unresolved_critical_important=tuple(
            dict(item) for item in receipt.unresolved_critical_important
        ),
    )


def _validate_domain_pair(
    *,
    domain: str,
    census: DomainCensusV1 | UnavailableComponentV1,
    census_bytes: bytes,
    power: DomainPowerPlanV1 | UnavailableComponentV1,
) -> None:
    census_unavailable = type(census) is UnavailableComponentV1
    power_unavailable = type(power) is UnavailableComponentV1
    if census_unavailable and not power_unavailable:
        raise PreflightV2Error(
            "unavailable census cannot pair with a positive power plan"
        )
    if power_unavailable:
        if power.upstream_component_sha256 != sha256(census_bytes).hexdigest():
            raise PreflightV2Error(
                "unavailable power does not bind its exact census bytes"
            )
        upstream_missing = (
            "upstream_census_unavailable" in power.missing_authority_codes
        )
        if upstream_missing != census_unavailable:
            raise PreflightV2Error(
                "power missing-authority state disagrees with its census slot"
            )
        return
    try:
        validate_plan_census_binding(plan=power, census_bytes=census_bytes)
    except (TypeError, PowerPlanError) as exc:
        raise PreflightV2Error("power plan and exact census binding disagree") from exc
    if power.domain != domain:
        raise PreflightV2Error("power plan is in the wrong domain slot")


def _evaluate_mixed(
    inputs: OacsPreflightInputsV2,
    architecture: DomainCensusV1 | UnavailableComponentV1,
    jci: DomainCensusV1 | UnavailableComponentV1,
    study: OacsStudyContractV1 | UnavailableComponentV1,
    architecture_power: DomainPowerPlanV1 | UnavailableComponentV1,
    jci_power: DomainPowerPlanV1 | UnavailableComponentV1,
) -> OacsPreflightReceiptV2:
    design_hash = _v1._validate_design_bytes(
        inputs.governing_design_bytes,
        inputs.expected_governing_design_sha256,
    )
    ledger = verify_claim_ledger_bytes(inputs.claim_ledger_bytes)
    if ledger.design_sha256 != design_hash:
        raise PreflightV2Error("claim ledger governing-design binding is stale")
    audit = parse_canonical_audit_bytes(inputs.backend_audit_bytes)
    review_package = verify_review_package_bytes(inputs.review_package_bytes)
    reviews = tuple(
        verify_locked_review_bytes(raw) for raw in inputs.locked_review_bytes
    )
    approval = None
    approval_digest = None
    if inputs.approval_trust_root_bytes is not None:
        approval = _v1._approval_from_bytes(inputs.approval_trust_root_bytes)
        approval_digest = sha256(inputs.approval_trust_root_bytes).hexdigest()

    if review_package.claim_ledger_sha256 != sha256(
        inputs.claim_ledger_bytes
    ).hexdigest() or review_package.claim_ids != tuple(
        record.claim_id for record in ledger.records
    ):
        raise PreflightV2Error("review package is not bound to the exact claim ledger")
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
        raise PreflightV2Error(
            "review package must bind the exact preflight component hashes"
        )
    reviews = verify_locked_reviews(review_package, reviews)
    finding_union = adjudicate_review_union(
        review_package,
        reviews,
        proposed_status="hold",
    )

    _validate_domain_pair(
        domain="architecture",
        census=architecture,
        census_bytes=inputs.architecture_census_bytes,
        power=architecture_power,
    )
    _validate_domain_pair(
        domain="jci",
        census=jci,
        census_bytes=inputs.jci_census_bytes,
        power=jci_power,
    )

    unavailable_values = tuple(
        value
        for value in (
            architecture,
            architecture_power,
            jci,
            jci_power,
            study,
        )
        if type(value) is UnavailableComponentV1
    )
    reasons = {_REASON_BY_COMPONENT[value.component] for value in unavailable_values}
    if type(architecture) is DomainCensusV1:
        try:
            validate_architecture_census(architecture)
        except DomainCensusError:
            reasons.add("architecture_census_insufficient")
    if type(jci) is DomainCensusV1:
        try:
            validate_jci_census(jci)
        except DomainCensusError:
            reasons.add("jci_census_insufficient")
    if not _v1._backend_matches_approval(
        audit,
        approval,
        approval_digest,
        inputs.expected_approval_trust_root_sha256,
    ):
        reasons.add("backend_not_ready")
    positive_power = tuple(
        value
        for value in (architecture_power, jci_power)
        if type(value) is DomainPowerPlanV1
    )
    if len(positive_power) == 2:
        try:
            validate_separate_power_plans(positive_power)
        except (TypeError, PowerPlanError):
            reasons.add("prospective_power_insufficient")
    elif any(not plan.structural_floor_powered for plan in positive_power):
        reasons.add("prospective_power_insufficient")

    unresolved = tuple(
        _v1._finding_payload(finding)
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
    unavailable = tuple(
        sorted(
            (
                _projection(
                    value,
                    component_hashes[value.component],
                )
                for value in unavailable_values
            ),
            key=_canonical_bytes,
        )
    )
    return _create_receipt(
        governing_design_sha256=design_hash,
        component_sha256=component_hashes,
        review_sha256=review_hashes,
        approval_trust_root_sha256=approval_digest,
        expected_approval_trust_root_sha256=(
            inputs.expected_approval_trust_root_sha256
        ),
        reason_codes=tuple(sorted(reasons)),
        unavailable_components=unavailable,
        unresolved_critical_important=unresolved,
    )


def evaluate_preflight_v2(inputs: OacsPreflightInputsV2) -> OacsPreflightReceiptV2:
    """Evaluate exact v1-positive or typed-unavailable slots without inference."""

    if type(inputs) is not OacsPreflightInputsV2:
        raise TypeError("inputs must be an exact OacsPreflightInputsV2")
    try:
        architecture = _parse_census_slot(
            inputs.architecture_census_bytes,
            "architecture_census",
        )
        jci = _parse_census_slot(inputs.jci_census_bytes, "jci_census")
        study = _parse_study_slot(inputs.study_contract_bytes)
        architecture_power = _parse_power_slot(
            inputs.architecture_power_plan_bytes,
            "architecture_power_plan",
        )
        jci_power = _parse_power_slot(
            inputs.jci_power_plan_bytes,
            "jci_power_plan",
        )
        slots = (architecture, jci, study, architecture_power, jci_power)
        if all(type(value) is not UnavailableComponentV1 for value in slots):
            return _receipt_from_v1(evaluate_preflight(_as_v1_inputs(inputs)))
        return _evaluate_mixed(
            inputs,
            architecture,
            jci,
            study,
            architecture_power,
            jci_power,
        )
    except PreflightV2Error:
        raise
    except (
        DomainCensusError,
        PowerPlanError,
        PreflightError,
        ReviewHarnessError,
        TypeError,
        ValueError,
    ) as exc:
        raise PreflightV2Error("a v2 preflight component is invalid") from exc


def preflight_receipt_v2_bytes(receipt: OacsPreflightReceiptV2) -> bytes:
    """Return the sole canonical UTF-8/LF representation of a v2 receipt."""

    if type(receipt) is not OacsPreflightReceiptV2:
        raise TypeError("receipt must be an exact OacsPreflightReceiptV2")
    return _canonical_bytes(
        {**_receipt_body(receipt), "receipt_sha256": receipt.receipt_sha256}
    )


def verify_preflight_receipt_v2_bytes(raw: bytes) -> OacsPreflightReceiptV2:
    """Verify canonical v2 receipt structure, projections, and self-hash."""

    payload = _parse_canonical_json(raw, "preflight v2 receipt")
    if type(payload) is not dict or set(payload) != _ROOT_KEYS:
        raise PreflightV2Error(
            "preflight v2 receipt keys do not match the closed schema"
        )
    reason_codes = payload["reason_codes"]
    unavailable = payload["unavailable_components"]
    unresolved = payload["unresolved_critical_important"]
    if (
        type(reason_codes) is not list
        or type(unavailable) is not list
        or type(unresolved) is not list
    ):
        raise PreflightV2Error("receipt arrays must use native JSON arrays")
    try:
        receipt = OacsPreflightReceiptV2(
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
            unavailable_components=tuple(unavailable),
            unresolved_critical_important=tuple(unresolved),
            operation_counters=payload["operation_counters"],
            receipt_sha256=payload["receipt_sha256"],
        )
    except PreflightV2Error:
        raise
    except (TypeError, ValueError) as exc:
        raise PreflightV2Error("preflight v2 receipt values are invalid") from exc
    if preflight_receipt_v2_bytes(receipt) != raw:
        raise PreflightV2Error("preflight v2 receipt bytes are not canonical")
    return receipt


def validate_preflight_receipt_v2_bytes(
    raw: bytes,
    inputs: OacsPreflightInputsV2,
) -> bytes:
    """Re-evaluate exact inputs and require byte-identical v2 receipt bytes."""

    verify_preflight_receipt_v2_bytes(raw)
    expected = preflight_receipt_v2_bytes(evaluate_preflight_v2(inputs))
    if not hmac.compare_digest(raw, expected):
        raise PreflightV2Error("preflight v2 receipt does not match the exact inputs")
    return raw


__all__ = (
    "ARCHITECTURE_CENSUS_CODES",
    "JCI_CENSUS_CODES",
    "OacsPreflightInputsV2",
    "OacsPreflightReceiptV2",
    "POWER_CODES",
    "PreflightV2Error",
    "SCHEMA",
    "STUDY_CONTRACT_CODES",
    "UNAVAILABLE_COMPONENTS",
    "UNAVAILABLE_SCHEMA",
    "UNAVAILABLE_STATUSES",
    "UnavailableComponentV1",
    "evaluate_preflight_v2",
    "preflight_receipt_v2_bytes",
    "unavailable_component_bytes",
    "validate_preflight_receipt_v2_bytes",
    "verify_preflight_receipt_v2_bytes",
    "verify_unavailable_component_bytes",
)
