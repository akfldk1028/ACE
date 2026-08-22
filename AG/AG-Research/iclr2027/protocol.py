"""Gold-blind protocol checks for three-agent architecture pilot runs."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from .review_state import parse_review_state
from .schema import ArchitectureEvidencePacket


PILOT_THREE_AGENT_PATTERNS = frozenset(
    {"rr3", "sel3", "swm3", "refl3", "debate3"}
)
PILOT_THREE_AGENT_SOURCES = frozenset(
    {"geometry_agent", "compliance_agent", "review_agent"}
)
PILOT_TERMINAL_SIGNALS = {
    "rr3": frozenset({"TERMINATE"}),
    "sel3": frozenset({"TERMINATE"}),
    "swm3": frozenset({"TERMINATE"}),
    "refl3": frozenset({"APPROVED", "TERMINATE"}),
    "debate3": frozenset({"TERMINATE"}),
}


class ProtocolTurn(Protocol):
    source: str
    content: str


def validate_pilot_protocol(
    *,
    pattern: str,
    turns: Sequence[ProtocolTurn],
    packet: ArchitectureEvidencePacket,
    terminated_by: str | None,
) -> tuple[str, ...]:
    """Validate collaboration/format invariants without consulting gold labels."""

    if pattern not in PILOT_THREE_AGENT_PATTERNS:
        return ()
    agent_turns = [turn for turn in turns if str(turn.source).lower() != "user"]
    errors: list[str] = []
    observed_sources = {str(turn.source) for turn in agent_turns}
    if not PILOT_THREE_AGENT_SOURCES.issubset(observed_sources):
        errors.append("protocol.role_coverage_missing")
    if observed_sources - PILOT_THREE_AGENT_SOURCES:
        errors.append("protocol.unexpected_agent_source")
    if any(not str(turn.content).strip() for turn in agent_turns):
        errors.append("protocol.empty_agent_content")
    if not agent_turns:
        errors.append("protocol.no_agent_turn")
        return tuple(dict.fromkeys(errors))
    final_turn = agent_turns[-1]
    if str(final_turn.source) != "review_agent":
        errors.append("protocol.final_source_not_reviewer")
    available_ids = {
        str(item["evidence_id"])
        for item in packet.evidence
        if item.get("evidence_id")
    }
    parsed = parse_review_state(
        str(final_turn.content),
        known_evidence_ids=available_ids,
    )
    final_lines = str(final_turn.content).rstrip().splitlines()
    final_line = final_lines[-1] if final_lines else ""
    has_terminal_signal = final_line in PILOT_TERMINAL_SIGNALS[pattern]
    if not parsed.complete:
        errors.append("protocol.final_state_incomplete")
    elif parsed.state.recommended_decision in {"STOP_ACCEPT", "STOP_REJECT"}:
        if not has_terminal_signal or terminated_by != "structured_state":
            errors.append("protocol.terminal_signal_missing")
    else:
        if has_terminal_signal:
            errors.append("protocol.continue_signal_present")
        if terminated_by != "max_messages":
            errors.append("protocol.continue_terminated_early")
    return tuple(dict.fromkeys(errors))


__all__ = [
    "PILOT_THREE_AGENT_PATTERNS",
    "PILOT_THREE_AGENT_SOURCES",
    "PILOT_TERMINAL_SIGNALS",
    "validate_pilot_protocol",
]
