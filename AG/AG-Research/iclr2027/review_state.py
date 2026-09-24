"""Fail-closed parsing and prefix accumulation for architecture agent reviews."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Sequence

from .schema import ArchitectureEvidencePacket, ArchitectureReviewState


_LABELED_BLOCK = re.compile(
    r"ARCH_REVIEW_STATE\s*```(?:json)?\s*(.*?)\s*```",
    flags=re.IGNORECASE | re.DOTALL,
)
_LEADING_FENCE = re.compile(
    r"\A\s*```(?:json)?\s*(.*?)\s*```",
    flags=re.IGNORECASE | re.DOTALL,
)
_STATE_SCHEMA_FIELD = "state_schema"
_STATE_SCHEMA_VALUE = "ARCH_REVIEW_STATE"
_STATE_FIELDS = {
    "checked_domains",
    "blocking_issue_codes",
    "missing_evidence_codes",
    "evidence_ids",
    "recommended_decision",
    "confidence",
}
_KNOWN_EVIDENCE_IDS = {
    "evidence:site_agent",
    "evidence:geometry_agent",
    "evidence:law_graph_agent",
    "evidence:parking_agent",
    "evidence:program_agent",
    "evidence:review_agent",
    "evidence:portfolio_attempt",
}


@dataclass(frozen=True)
class ParseResult:
    state: ArchitectureReviewState
    complete: bool
    error_codes: tuple[str, ...]
    block_count: int


@dataclass(frozen=True)
class TurnRecord:
    author: str
    content: str


@dataclass(frozen=True)
class PrefixReviewState:
    turn_index: int
    state: ArchitectureReviewState
    parse_complete: bool
    parse_error_codes: tuple[str, ...]


def _incomplete_state(
    candidate: ArchitectureReviewState | None = None,
) -> ArchitectureReviewState:
    return ArchitectureReviewState(
        checked_domains=candidate.checked_domains if candidate else (),
        blocking_issue_codes=candidate.blocking_issue_codes if candidate else (),
        missing_evidence_codes=candidate.missing_evidence_codes if candidate else (),
        evidence_ids=candidate.evidence_ids if candidate else (),
        recommended_decision="CONTINUE",
        confidence=0.0,
    )


def _decision_is_consistent(candidate: ArchitectureReviewState) -> bool:
    if candidate.recommended_decision == "STOP_ACCEPT":
        return (
            not candidate.blocking_issue_codes and not candidate.missing_evidence_codes
        )
    if candidate.recommended_decision == "STOP_REJECT":
        return bool(candidate.blocking_issue_codes)
    return bool(candidate.missing_evidence_codes) and not candidate.blocking_issue_codes


def parse_review_state(
    text: str,
    *,
    known_evidence_ids: Sequence[str] | set[str] | None = None,
) -> ParseResult:
    """Return the last valid ARCH_REVIEW_STATE block or an incomplete state."""

    allowed_evidence_ids = (
        _KNOWN_EVIDENCE_IDS if known_evidence_ids is None else set(known_evidence_ids)
    )

    candidates: list[tuple[str, bool]] = [
        (match.group(1), False) for match in _LABELED_BLOCK.finditer(text)
    ]
    leading = _LEADING_FENCE.match(text)
    if leading is not None:
        try:
            leading_payload = json.loads(leading.group(1))
        except json.JSONDecodeError:
            leading_payload = None
        if (
            isinstance(leading_payload, dict)
            and leading_payload.get(_STATE_SCHEMA_FIELD) == _STATE_SCHEMA_VALUE
        ):
            candidates.insert(0, (leading.group(1), True))
    if not candidates:
        return ParseResult(
            state=_incomplete_state(),
            complete=False,
            error_codes=("missing_state_block",),
            block_count=0,
        )

    last_valid: ArchitectureReviewState | None = None
    last_candidate: ArchitectureReviewState | None = None
    observed_errors: list[str] = []
    for raw_payload, self_tagged in candidates:
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            observed_errors.append("malformed_json")
            continue
        if not isinstance(payload, dict):
            observed_errors.append("state_not_object")
            continue
        expected_fields = _STATE_FIELDS | (
            {_STATE_SCHEMA_FIELD}
            if self_tagged or _STATE_SCHEMA_FIELD in payload
            else set()
        )
        if set(payload) != expected_fields:
            observed_errors.append("unexpected_field")
            continue
        if _STATE_SCHEMA_FIELD in payload:
            if payload.get(_STATE_SCHEMA_FIELD) != _STATE_SCHEMA_VALUE:
                observed_errors.append("invalid_state_schema")
                continue
            payload = {
                key: value
                for key, value in payload.items()
                if key != _STATE_SCHEMA_FIELD
            }
        try:
            candidate = ArchitectureReviewState.from_dict(payload)
        except (TypeError, ValueError):
            observed_errors.append("invalid_state")
            continue
        last_candidate = candidate
        if not _decision_is_consistent(candidate):
            observed_errors.append("invalid_state")
            continue
        if set(candidate.evidence_ids) - allowed_evidence_ids:
            observed_errors.append("unknown_evidence_id")
            continue
        last_valid = candidate

    if last_valid is not None:
        return ParseResult(
            state=last_valid,
            complete=True,
            error_codes=(),
            block_count=len(candidates),
        )
    return ParseResult(
        state=_incomplete_state(last_candidate),
        complete=False,
        error_codes=tuple(dict.fromkeys(observed_errors)) or ("invalid_state",),
        block_count=len(candidates),
    )


def accumulate_prefix_states(
    turns: Sequence[TurnRecord],
    packet: ArchitectureEvidencePacket,
) -> list[PrefixReviewState]:
    """Accumulate cited review evidence while preserving fail-closed turns."""

    available_ids = {str(item["evidence_id"]) for item in packet.evidence}
    domains: set[str] = set()
    evidence_ids: set[str] = set()
    prefixes: list[PrefixReviewState] = []
    for index, turn in enumerate(turns):
        parsed = parse_review_state(
            turn.content,
            known_evidence_ids=available_ids,
        )
        errors = list(parsed.error_codes)
        if not set(parsed.state.evidence_ids).issubset(available_ids):
            errors.append("unknown_evidence_id")
        complete = parsed.complete and not errors
        if complete:
            domains.update(parsed.state.checked_domains)
            evidence_ids.update(parsed.state.evidence_ids)
        state = ArchitectureReviewState(
            checked_domains=tuple(sorted(domains)),
            blocking_issue_codes=(
                parsed.state.blocking_issue_codes if complete else ()
            ),
            missing_evidence_codes=(
                parsed.state.missing_evidence_codes if complete else ()
            ),
            evidence_ids=tuple(sorted(evidence_ids)),
            recommended_decision=(
                parsed.state.recommended_decision if complete else "CONTINUE"
            ),
            confidence=parsed.state.confidence if complete else 0.0,
        )
        prefixes.append(
            PrefixReviewState(
                turn_index=index,
                state=state,
                parse_complete=complete,
                parse_error_codes=tuple(dict.fromkeys(errors)),
            )
        )
    return prefixes
