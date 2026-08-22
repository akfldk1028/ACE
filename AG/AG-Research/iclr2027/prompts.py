"""Architecture role banks and structured review prompt contract."""

from __future__ import annotations

from dataclasses import dataclass


ARCH_REVIEW_STATE_BLOCK = """ARCH_REVIEW_STATE
```json
{
  "state_schema": "ARCH_REVIEW_STATE",
  "checked_domains": ["site", "geometry", "law", "parking", "program"],
  "blocking_issue_codes": [],
  "missing_evidence_codes": ["parking.required_evidence_missing"],
  "evidence_ids": [],
  "recommended_decision": "CONTINUE",
  "confidence": 0.0
}
```"""

ARCH_REVIEW_DECISION_RULES = """Decision consistency rules:
- STOP_ACCEPT requires both issue lists to be empty.
- CONTINUE requires missing evidence and no blocking issue.
- STOP_REJECT requires at least one blocking issue."""

ARCH_REVIEW_EVIDENCE_POLICY = """Typed evidence decision policy:
- For subject_kind=execution, consider site, geometry, law, parking, and program. Cite every supplied evidence ID. evidence:review_agent never substitutes for a missing domain record.
- Missing evidence:law_graph_agent means law.required_evidence_missing; missing evidence:parking_agent means parking.required_evidence_missing. Missing required evidence with no blocker means CONTINUE.
- missing_evidence_codes contains issue codes, not evidence IDs. Never place an evidence: identifier in either issue-code list; evidence: identifiers belong only in evidence_ids.
- Report site.boundary_failed when site status is not passed or inside_site is not true.
- Report geometry.compilation_failed when geometry status is not certified, hard_pass is not true, candidate_floor_count is not positive, or achieved_gfa_m2 is not positive.
- Report identity.hash_mismatch when corresponding site_ref, execution_id, program_hash, or geometry_hash values disagree across the execution packet.
- Report law.projection_failed when the supplied law record or either legal projection is not evaluated/hard-pass, or volume_retention is below 0.98.
- Report parking.supply_shortage when the supplied parking record is not evaluated/hard-pass, counts are invalid, or provided_spaces is below required_spaces.
- Report program.capacity_failed when semantic_projection is not hard-pass, accepted_carrier_count is not positive, or achieved_gfa_m2 / candidate_target_gfa_m2 is below 0.70.
- For subject_kind=portfolio_attempt, do not require execution law or parking records. Check program, cite only evidence:portfolio_attempt, and use the supplied DECISION_FACTS integrity predicate.
- If portfolio_attempt_hash_matches is false, report identity.attempt_hash_mismatch.
- A complete selection attempt with no admitted candidate reports selection.no_admitted_candidate.
- A complete materialization attempt with no ledger candidate reports materialization.no_candidate_reached_ledger.
- A complete preflight attempt with program/site infeasibility reports preflight.program_site_infeasible.
- A candidate_floor_context attempt missing its typed ledger reports candidate_floor_context.typed_ledger_missing and CONTINUE.
- An invalid or incomplete portfolio-attempt record reports evidence.portfolio_attempt_incomplete.
- Do not invent alternative issue-code names."""

ARCH_REVIEW_RESPONSE_ORDER = """The ARCH_REVIEW_STATE block must be the first content in your response. Its first line must be the literal text ARCH_REVIEW_STATE, before the opening JSON fence.
Put any explanation in at most three short bullets after the block."""


@dataclass(frozen=True)
class ArchitectureRole:
    name: str
    description: str
    focus: str


ROLE_BANKS: dict[int, tuple[ArchitectureRole, ...]] = {
    1: (
        ArchitectureRole(
            "architect_review_agent",
            "Integrated architect and evidence reviewer",
            "Check geometry, legal, parking, program, and evidence identity together.",
        ),
    ),
    2: (
        ArchitectureRole(
            "design_agent",
            "Geometry and program evidence reviewer",
            "Check final geometry compilation, site fit, and program capacity.",
        ),
        ArchitectureRole(
            "review_agent",
            "Compliance and terminal decision reviewer",
            "Check legal, parking, identity, and whether a terminal decision is supported.",
        ),
    ),
    3: (
        ArchitectureRole(
            "geometry_agent",
            "Geometry and program evidence reviewer",
            "Check final geometry compilation, site fit, and program measurements.",
        ),
        ArchitectureRole(
            "compliance_agent",
            "Law and parking evidence reviewer",
            "Check PNU-bound law projection, parking supply, and all identity hashes.",
        ),
        ArchitectureRole(
            "review_agent",
            "Architecture terminal decision reviewer",
            "Synthesize cited evidence and reject unsupported or unsafe stopping.",
        ),
    ),
    4: (
        ArchitectureRole(
            "geometry_agent",
            "Geometry evidence reviewer",
            "Check final geometry compilation, floor count, site fit, and geometry identity.",
        ),
        ArchitectureRole(
            "law_agent",
            "Statutory law evidence reviewer",
            "Check PNU-bound law projection and legal evidence identity.",
        ),
        ArchitectureRole(
            "program_parking_agent",
            "Program and parking evidence reviewer",
            "Check usable program capacity and required versus provided parking.",
        ),
        ArchitectureRole(
            "review_agent",
            "Architecture terminal decision reviewer",
            "Synthesize cited evidence and reject unsupported or unsafe stopping.",
        ),
    ),
}


def architecture_system_prompt(
    role: ArchitectureRole,
    *,
    terminal_signal: str | None,
    handoff_targets: tuple[str, ...] = (),
) -> str:
    signal_instruction = (
        f"After the block, append {terminal_signal} only when reporting a supported "
        "terminal recommendation. You MUST append it as the standalone final line "
        "for STOP_ACCEPT or STOP_REJECT. Do not append it for CONTINUE. "
        "The signal is not evidence or ground truth."
        if terminal_signal
        else "Do not append a termination keyword; the topology controls the message budget."
    )
    if handoff_targets:
        target_names = ", ".join(handoff_targets)
        handoff_instruction = f"""SWARM HANDOFF PROTOCOL:
- On your first activation, emit one complete ARCH_REVIEW_STATE response.
- On your next activation, the coverage controller will emit a sanitized handoff control event to: {target_names}.
- Do not call a handoff tool yourself. The deterministic control event is not a substantive review response."""
    else:
        handoff_instruction = ""
    return f"""You are {role.name}, an architecture-domain evidence reviewer.
{role.focus}
Use only evidence IDs and measurements present in the supplied packet. Never infer a gold label.
Every substantive response must contain exactly one ARCH_REVIEW_STATE fenced JSON block with exactly these fields:
{ARCH_REVIEW_RESPONSE_ORDER}
{ARCH_REVIEW_STATE_BLOCK}
Allowed decisions are CONTINUE, STOP_ACCEPT, and STOP_REJECT. Cite only packet evidence IDs.
{ARCH_REVIEW_DECISION_RULES}
{ARCH_REVIEW_EVIDENCE_POLICY}
{signal_instruction}
{handoff_instruction}
"""
