"""Deterministic architecture review quality metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .review_state import PrefixReviewState
from .schema import ArchitectureEvidencePacket, ArchitectureGoldRecord
from .validators import validate_terminal_admissibility


@dataclass(frozen=True)
class ArchitectureTurnScore:
    issue_f1: float
    evidence_f1: float
    domain_coverage: float
    verdict_score: float
    quality: float


def _f1(predicted: Iterable[str], expected: Iterable[str]) -> float:
    predicted_set = set(predicted)
    expected_set = set(expected)
    if not predicted_set and not expected_set:
        return 1.0
    if not predicted_set or not expected_set:
        return 0.0
    true_positive = len(predicted_set & expected_set)
    precision = true_positive / len(predicted_set)
    recall = true_positive / len(expected_set)
    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def _required_domains(packet: ArchitectureEvidencePacket) -> set[str]:
    allowed = {"site", "law", "parking", "program", "geometry"}
    return {
        str(item.get("domain"))
        for item in packet.evidence
        if item.get("domain") in allowed
    }


def score_prefix(
    state: PrefixReviewState,
    gold: ArchitectureGoldRecord,
    packet: ArchitectureEvidencePacket,
) -> ArchitectureTurnScore:
    issue_f1 = _f1(
        state.state.blocking_issue_codes,
        gold.blocking_issue_codes,
    )
    evidence_f1 = _f1(
        state.state.evidence_ids,
        gold.required_evidence_ids,
    )
    required_domains = _required_domains(packet)
    domain_coverage = (
        len(set(state.state.checked_domains) & required_domains) / len(required_domains)
        if required_domains
        else 1.0
    )
    admissibility = validate_terminal_admissibility(packet, state.state)
    verdict_score = float(
        state.parse_complete
        and state.state.recommended_decision == gold.expected_decision
        and admissibility.admissible
    )
    quality = (
        0.30 * issue_f1
        + 0.25 * evidence_f1
        + 0.20 * domain_coverage
        + 0.25 * verdict_score
    )
    return ArchitectureTurnScore(
        issue_f1=issue_f1,
        evidence_f1=evidence_f1,
        domain_coverage=domain_coverage,
        verdict_score=verdict_score,
        quality=quality,
    )


def score_prefix_breakdown(
    state: PrefixReviewState,
    gold: ArchitectureGoldRecord,
    packet: ArchitectureEvidencePacket,
) -> dict[str, str | float]:
    """Report stage, decision, blocker, and missing-evidence scores separately.

    The existing ``ArchitectureTurnScore`` fields remain stable for experiment CSV
    compatibility; this explicit breakdown prevents a correct CONTINUE report from
    being counted as a false-positive blocker.
    """

    score = score_prefix(state, gold, packet)
    return {
        "subject_stage": packet.attempt_stage or "execution",
        "decision_score": float(
            state.parse_complete
            and state.state.recommended_decision == gold.expected_decision
        ),
        "blocking_issue_f1": score.issue_f1,
        "missing_evidence_f1": _f1(
            state.state.missing_evidence_codes,
            gold.missing_evidence_codes,
        ),
    }
