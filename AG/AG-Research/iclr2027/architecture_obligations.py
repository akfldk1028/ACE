"""Public, prefix-only architecture obligation adapter."""

from __future__ import annotations

from collections.abc import Mapping
import math
import re
from typing import Any

from .io import sha256_json
from .obligation_contract import ObligationBelief, ObligationSpec, ObligationState
from .review_state import PrefixReviewState
from .schema import ArchitecturePublicCase, ArchitectureReviewState


_PREFIX_SCHEMA_VERSION = "iclr2027.architecture_obligation_prefix.v1"
_SOURCE_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_SITE_OUTER_KEYS = frozenset({"evidence_id", "domain", "status", "evidence"})
_SITE_EVIDENCE_KEYS = frozenset({"site_ref", "inside_site", "geometry_hash"})
_TERMINAL_RECOMMENDATIONS = frozenset({"STOP_ACCEPT", "STOP_REJECT"})
_DOMAINS = frozenset({"site", "law", "parking", "program", "geometry"})

_FAMILY_ROWS = (
    (
        "obligation:architecture:site/evidence",
        "site/evidence",
        "site",
        "evidence:site_agent",
    ),
    (
        "obligation:architecture:law",
        "law",
        "law",
        "evidence:law_graph_agent",
    ),
    (
        "obligation:architecture:parking",
        "parking",
        "parking",
        "evidence:parking_agent",
    ),
    (
        "obligation:architecture:program",
        "program",
        "program",
        "evidence:program_agent",
    ),
    (
        "obligation:architecture:geometry",
        "geometry",
        "geometry",
        "evidence:geometry_agent",
    ),
)
_REQUIRED_EVIDENCE_IDS = frozenset(row[3] for row in _FAMILY_ROWS)
_CODE_PREFIX_TO_FAMILY = {
    "site": "site/evidence",
    "identity": "site/evidence",
    "evidence": "site/evidence",
    "law": "law",
    "parking": "parking",
    "program": "program",
    "geometry": "geometry",
}
_DECLARED_SPECS = tuple(
    ObligationSpec(
        obligation_id=obligation_id,
        family=family,
        weight=1.0,
        hard=True,
        public_basis_ids=("task:architecture_review", evidence_id),
    )
    for obligation_id, family, _domain, evidence_id in _FAMILY_ROWS
)


def _require_execution_case(public_case: Any) -> ArchitecturePublicCase:
    if type(public_case) is not ArchitecturePublicCase:
        raise TypeError("public_case must be an exact ArchitecturePublicCase")
    if public_case.subject_kind != "execution":
        raise ValueError("architecture obligations require subject_kind='execution'")
    return public_case


def _require_exact_keys(
    value: Mapping[str, Any], expected: frozenset[str], label: str
) -> None:
    if any(type(key) is not str for key in value) or set(value) != expected:
        raise ValueError(f"{label} must contain exact keys")


def declared_architecture_obligations(
    public_case: ArchitecturePublicCase,
) -> tuple[ObligationSpec, ...]:
    """Return the stable public declaration for an execution case."""

    _require_execution_case(public_case)
    return _DECLARED_SPECS


def validate_public_architecture_admission(
    public_case: ArchitecturePublicCase,
) -> None:
    """Validate only authenticated source identity and the public site record."""

    case = _require_execution_case(public_case)
    source_hash = case.source_artifact_sha256
    if not isinstance(source_hash, str) or _SOURCE_SHA256.fullmatch(source_hash) is None:
        raise ValueError("source_artifact_sha256 must be a 64-character SHA-256")

    site_agent_records: list[Mapping[str, Any]] = []
    site_domain_records: list[Mapping[str, Any]] = []
    for record in case.evidence:
        if not isinstance(record, Mapping):
            raise TypeError("public evidence records must be mappings")
        if record.get("evidence_id") == "evidence:site_agent":
            site_agent_records.append(record)
        if record.get("domain") == "site":
            site_domain_records.append(record)
    if len(site_agent_records) != 1 or len(site_domain_records) != 1:
        raise ValueError("exactly one site record is required")
    site_record = site_agent_records[0]
    if site_domain_records[0] is not site_record:
        raise ValueError("the site-domain record must be evidence:site_agent")

    _require_exact_keys(site_record, _SITE_OUTER_KEYS, "site record")
    if site_record["evidence_id"] != "evidence:site_agent":
        raise ValueError("site evidence_id must be evidence:site_agent")
    if site_record["domain"] != "site":
        raise ValueError("site record domain must be site")
    if site_record["status"] != "passed":
        raise ValueError("site record status must be passed")

    evidence = site_record["evidence"]
    if not isinstance(evidence, Mapping):
        raise TypeError("site evidence must be a mapping")
    _require_exact_keys(evidence, _SITE_EVIDENCE_KEYS, "site evidence")
    site_ref = evidence["site_ref"]
    if not isinstance(site_ref, str) or site_ref != case.site_ref:
        raise ValueError("site evidence site_ref must match the public case")
    geometry_hash = evidence["geometry_hash"]
    if not isinstance(geometry_hash, str) or geometry_hash != case.geometry_hash:
        raise ValueError("site evidence geometry_hash must match the public case")
    inside_site = evidence["inside_site"]
    if type(inside_site) is not bool:
        raise TypeError("site evidence inside_site must be a native boolean")
    if inside_site is not True:
        raise ValueError("site evidence inside_site must be true")


def _validate_string_tuple(value: Any, field: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be a tuple")
    if any(type(item) is not str for item in value):
        raise TypeError(f"{field} must contain strings")
    if any(not item.strip() for item in value):
        raise ValueError(f"{field} must not contain empty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} must not contain duplicates")
    return value


def _validate_review_prefix(review_prefix: Any) -> PrefixReviewState:
    if type(review_prefix) is not PrefixReviewState:
        raise TypeError("review_prefix must be an exact PrefixReviewState")
    if type(review_prefix.turn_index) is not int:
        raise TypeError("review_prefix.turn_index must be a native integer")
    if review_prefix.turn_index < 0:
        raise ValueError("review_prefix.turn_index must be nonnegative")
    if type(review_prefix.state) is not ArchitectureReviewState:
        raise TypeError("review_prefix.state must be an exact ArchitectureReviewState")
    if type(review_prefix.parse_complete) is not bool:
        raise TypeError("review_prefix.parse_complete must be a native boolean")
    _validate_string_tuple(
        review_prefix.parse_error_codes,
        "review_prefix.parse_error_codes",
    )

    state = review_prefix.state
    checked_domains = _validate_string_tuple(
        state.checked_domains,
        "review_prefix.state.checked_domains",
    )
    if not set(checked_domains).issubset(_DOMAINS):
        raise ValueError("review_prefix.state.checked_domains contains an unknown domain")
    _validate_string_tuple(
        state.blocking_issue_codes,
        "review_prefix.state.blocking_issue_codes",
    )
    _validate_string_tuple(
        state.missing_evidence_codes,
        "review_prefix.state.missing_evidence_codes",
    )
    _validate_string_tuple(
        state.evidence_ids,
        "review_prefix.state.evidence_ids",
    )
    if type(state.recommended_decision) is not str:
        raise TypeError("review_prefix.state.recommended_decision must be a string")
    if state.recommended_decision not in {
        "CONTINUE",
        "STOP_ACCEPT",
        "STOP_REJECT",
    }:
        raise ValueError("review_prefix.state.recommended_decision is unsupported")
    if isinstance(state.confidence, bool) or not isinstance(
        state.confidence, (int, float)
    ):
        raise TypeError("review_prefix.state.confidence must be numeric")
    if not math.isfinite(float(state.confidence)) or not 0.0 <= state.confidence <= 1.0:
        raise ValueError("review_prefix.state.confidence must be within [0, 1]")
    return review_prefix


def _family_for_code(code: str) -> str:
    prefix, separator, suffix = code.partition(".")
    if not separator or not suffix or prefix not in _CODE_PREFIX_TO_FAMILY:
        raise ValueError(f"unknown agent-authored code prefix: {code}")
    return _CODE_PREFIX_TO_FAMILY[prefix]


def _public_evidence_ids(case: ArchitecturePublicCase) -> tuple[set[str], bool]:
    evidence_ids: set[str] = set()
    all_well_formed = True
    for record in case.evidence:
        raw_id = record.get("evidence_id")
        if not isinstance(raw_id, str) or not raw_id:
            all_well_formed = False
            continue
        evidence_ids.add(raw_id)
    return evidence_ids, all_well_formed


def public_obligation_state(
    public_case: ArchitecturePublicCase,
    review_prefix: PrefixReviewState,
    *,
    cumulative_cost: float = 0.0,
) -> ObligationState:
    """Build public controller state without evaluating terminal correctness."""

    validate_public_architecture_admission(public_case)
    prefix = _validate_review_prefix(review_prefix)
    review_state = prefix.state

    coded_families = {
        _family_for_code(code)
        for code in (
            *review_state.blocking_issue_codes,
            *review_state.missing_evidence_codes,
        )
    }
    available_ids, all_evidence_ids_well_formed = _public_evidence_ids(public_case)
    cited_ids = set(review_state.evidence_ids)
    checked_domains = set(review_state.checked_domains)

    beliefs: list[ObligationBelief] = []
    for obligation_id, family, domain, evidence_id in _FAMILY_ROWS:
        cited_available = evidence_id in available_ids and evidence_id in cited_ids
        belief_evidence_ids = (evidence_id,) if cited_available else ()
        if family in coded_families:
            status = "unresolved"
            probability = 1.0
        elif domain in checked_domains and cited_available:
            status = "resolved"
            probability = 0.0
        else:
            status = "unknown"
            probability = 0.5
        beliefs.append(
            ObligationBelief(
                obligation_id=obligation_id,
                status=status,
                unresolved_probability=probability,
                evidence_ids=belief_evidence_ids,
            )
        )

    hard_gate_passed = (
        prefix.parse_complete
        and not prefix.parse_error_codes
        and _REQUIRED_EVIDENCE_IDS.issubset(available_ids)
        and _DOMAINS.issubset(checked_domains)
        and all_evidence_ids_well_formed
        and available_ids == cited_ids
        and not review_state.missing_evidence_codes
        and review_state.recommended_decision in _TERMINAL_RECOMMENDATIONS
    )
    prefix_payload = {
        "schema_version": _PREFIX_SCHEMA_VERSION,
        "public_case": public_case.to_dict(),
        "prefix": {
            "turn_index": prefix.turn_index,
            "state": review_state.to_dict(),
            "parse_complete": prefix.parse_complete,
            "parse_error_codes": list(prefix.parse_error_codes),
        },
    }
    return ObligationState(
        case_id=public_case.case_id,
        prefix_id="prefix:" + sha256_json(prefix_payload),
        beliefs=tuple(beliefs),
        hard_gate_passed=hard_gate_passed,
        cumulative_cost=cumulative_cost,
    )


__all__ = (
    "declared_architecture_obligations",
    "public_obligation_state",
    "validate_public_architecture_admission",
)
