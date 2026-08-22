"""Hard spending gate for the Exp08 architecture pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Sequence

from .io import sha256_json, write_json_atomic
from .secure_files import AuthenticatedTree, read_authenticated_file


REQUIRED_FAULT_FAMILIES = {
    "identity_hash",
    "law_projection",
    "parking_shortage",
    "program_capacity",
    "geometry_compile",
}
PILOT_PATTERNS = ("rr3", "sel3", "swm3", "refl3", "debate3")
PILOT_EXPECTED_DEV_CASES = 30
PILOT_SUMMARY_SCHEMA = "ace.iclr2027.pilot_summary.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_CASE_STAGES = frozenset(
    {
        "execution",
        "selection",
        "materialization",
        "preflight",
        "candidate_floor_context",
    }
)


@dataclass(frozen=True)
class PilotSummary:
    planned_runs: int
    completed_runs: int
    parsed_states: int
    successful_parses: int
    final_runs: int
    successful_final_parses: int
    correct_final_decisions: int
    correct_final_verdicts: int
    correct_final_blocking: int
    correct_final_missing_evidence: int
    protocol_valid_runs: int
    run_errors: int
    safe_cases: int
    unsafe_cases: int
    continue_cases: int
    fault_families: tuple[str, ...]
    estimated_completion_date: date
    estimated_total_cost_usd: float | None
    stage_case_counts: dict[str, int] = field(default_factory=dict)
    schema_version: str = PILOT_SUMMARY_SCHEMA
    transaction_set_sha256: str = ""
    retried_runs: int = 0


@dataclass(frozen=True)
class PilotGateResult:
    passed: bool
    checks: dict[str, bool]
    parse_success_rate: float
    final_parse_success_rate: float
    final_decision_accuracy: float
    final_verdict_accuracy: float
    final_blocking_accuracy: float
    final_missing_evidence_accuracy: float
    protocol_valid_rate: float
    run_error_rate: float
    retry_rate: float
    safe_share: float
    unsafe_share: float
    continue_share: float
    estimated_total_cost_usd: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_pilot(
    summary: PilotSummary,
    *,
    run_manifest: Any,
    observed_transaction_set_sha256: str | None = None,
    observed_transaction_count: int | None = None,
    deadline: date = date(2026, 9, 2),
) -> PilotGateResult:
    summary_counts = (
        summary.planned_runs,
        summary.completed_runs,
        summary.parsed_states,
        summary.successful_parses,
        summary.final_runs,
        summary.successful_final_parses,
        summary.correct_final_decisions,
        summary.correct_final_verdicts,
        summary.correct_final_blocking,
        summary.correct_final_missing_evidence,
        summary.protocol_valid_runs,
        summary.run_errors,
        summary.retried_runs,
        summary.safe_cases,
        summary.unsafe_cases,
        summary.continue_cases,
    )
    summary_count_domains = (
        all(type(value) is int and value >= 0 for value in summary_counts)
        and summary.planned_runs > 0
        and summary.completed_runs <= summary.planned_runs
        and summary.successful_parses <= summary.parsed_states
        and summary.final_runs <= summary.completed_runs
        and summary.successful_final_parses <= summary.final_runs
        and summary.correct_final_decisions <= summary.final_runs
        and summary.correct_final_verdicts <= summary.final_runs
        and summary.correct_final_blocking <= summary.final_runs
        and summary.correct_final_missing_evidence <= summary.final_runs
        and summary.protocol_valid_runs <= summary.final_runs
        and summary.run_errors <= summary.completed_runs
        and summary.retried_runs <= summary.completed_runs
    )
    parse_rate = (
        summary.successful_parses / summary.parsed_states
        if summary_count_domains and summary.parsed_states
        else 0.0
    )
    error_rate = (
        summary.run_errors / summary.completed_runs
        if summary_count_domains and summary.completed_runs
        else 1.0
    )
    retry_rate = (
        summary.retried_runs / summary.completed_runs
        if summary_count_domains and summary.completed_runs
        else 1.0
    )
    final_parse_rate = (
        summary.successful_final_parses / summary.final_runs
        if summary_count_domains and summary.final_runs
        else 0.0
    )
    final_decision_accuracy = (
        summary.correct_final_decisions / summary.final_runs
        if summary_count_domains and summary.final_runs
        else 0.0
    )
    final_verdict_accuracy = (
        summary.correct_final_verdicts / summary.final_runs
        if summary_count_domains and summary.final_runs
        else 0.0
    )
    final_blocking_accuracy = (
        summary.correct_final_blocking / summary.final_runs
        if summary_count_domains and summary.final_runs
        else 0.0
    )
    final_missing_evidence_accuracy = (
        summary.correct_final_missing_evidence / summary.final_runs
        if summary_count_domains and summary.final_runs
        else 0.0
    )
    protocol_valid_rate = (
        summary.protocol_valid_runs / summary.final_runs
        if summary_count_domains and summary.final_runs
        else 0.0
    )
    labeled_cases = (
        summary.safe_cases + summary.unsafe_cases + summary.continue_cases
        if summary_count_domains
        else 0
    )
    safe_share = summary.safe_cases / labeled_cases if labeled_cases else 0.0
    unsafe_share = summary.unsafe_cases / labeled_cases if labeled_cases else 0.0
    continue_share = summary.continue_cases / labeled_cases if labeled_cases else 0.0
    try:
        from .run_manifest import validate_run_manifest

        manifest = validate_run_manifest(run_manifest)
        manifest_exact = True
    except (TypeError, ValueError):
        manifest = run_manifest if isinstance(run_manifest, dict) else {}
        manifest_exact = False
    patterns = manifest.get("patterns")
    exact_patterns = (
        isinstance(patterns, list) and tuple(patterns) == PILOT_PATTERNS
    )
    repeats = manifest.get("repeats")
    exact_repeats = type(repeats) is int and repeats == 3
    expected_case_count = manifest.get("expected_case_count")
    case_count = manifest.get("case_count")
    planned_run_count = manifest.get("planned_run_count")
    valid_case_counts = (
        type(expected_case_count) is int
        and expected_case_count > 0
        and type(case_count) is int
        and case_count > 0
    )
    expected_runs = (
        case_count * len(PILOT_PATTERNS) * 3 if valid_case_counts else -1
    )
    manifest_stage_counts = manifest.get("stage_case_counts")
    manifest_decision_counts = manifest.get("decision_case_counts")
    summary_decision_counts = {
        "STOP_ACCEPT": summary.safe_cases,
        "STOP_REJECT": summary.unsafe_cases,
        "CONTINUE": summary.continue_cases,
    }
    valid_decision_census = (
        isinstance(manifest_decision_counts, dict)
        and set(manifest_decision_counts) == set(summary_decision_counts)
        and all(
            type(value) is int and value >= 0
            for value in manifest_decision_counts.values()
        )
        and (
            not valid_case_counts
            or sum(manifest_decision_counts.values()) == case_count
        )
    )

    def valid_stage_counts(value: Any) -> bool:
        return (
            isinstance(value, dict)
            and bool(value)
            and all(
                isinstance(stage, str)
                and bool(stage.strip())
                and stage in ALLOWED_CASE_STAGES
                and type(count) is int
                and count > 0
                for stage, count in value.items()
            )
        )

    manifest_stages_valid = valid_stage_counts(manifest_stage_counts)
    summary_stages_valid = valid_stage_counts(summary.stage_case_counts)
    checks = {
        "run_manifest_exact": manifest_exact,
        "pilot_summary_schema": (
            summary.schema_version == PILOT_SUMMARY_SCHEMA
        ),
        "transaction_set_bound": (
            isinstance(observed_transaction_set_sha256, str)
            and _SHA256.fullmatch(observed_transaction_set_sha256) is not None
            and summary.transaction_set_sha256
            == observed_transaction_set_sha256
            and type(observed_transaction_count) is int
            and observed_transaction_count == summary.planned_runs
        ),
        "run_manifest_schema": (
            manifest.get("schema_version")
            == "ace.iclr2027.exp08_run_manifest.v2"
        ),
        "pilot_summary_count_domains": summary_count_domains,
        "pilot_split_dev": manifest.get("split") == "dev",
        "pilot_exact_five_patterns": exact_patterns,
        "pilot_repeats_3": exact_repeats,
        "pilot_full_case_set": (
            valid_case_counts
            and expected_case_count == PILOT_EXPECTED_DEV_CASES
            and case_count == PILOT_EXPECTED_DEV_CASES
        ),
        "pilot_run_composition": (
            exact_patterns
            and exact_repeats
            and type(planned_run_count) is int
            and planned_run_count == expected_runs
            and summary.planned_runs == expected_runs
        ),
        "pilot_manifest_executed": manifest.get("executed") is True,
        "pilot_complete": (
            summary_count_domains
            and summary.planned_runs > 0
            and summary.completed_runs == summary.planned_runs
        ),
        "parse_success_at_least_95pct": parse_rate >= 0.95,
        "all_completed_runs_have_final_state": (
            summary_count_domains
            and summary.final_runs == summary.completed_runs
        ),
        "all_final_states_parse_complete": final_parse_rate == 1.0,
        "all_runs_protocol_valid": protocol_valid_rate == 1.0,
        "final_decision_at_least_95pct": final_decision_accuracy >= 0.95,
        "final_verdict_at_least_95pct": final_verdict_accuracy >= 0.95,
        "final_blocking_at_least_95pct": final_blocking_accuracy >= 0.95,
        "final_missing_evidence_at_least_95pct": (
            final_missing_evidence_accuracy >= 0.95
        ),
        "no_terminal_run_errors": error_rate == 0.0,
        "retry_rate_below_5pct": retry_rate < 0.05,
        "all_cases_labeled": (
            valid_case_counts
            and summary_count_domains
            and summary.safe_cases >= 0
            and summary.unsafe_cases >= 0
            and summary.continue_cases >= 0
            and labeled_cases == case_count
        ),
        "all_decision_classes_present": (
            summary_count_domains
            and summary.safe_cases > 0
            and summary.unsafe_cases > 0
            and summary.continue_cases > 0
        ),
        "decision_census_consistent": (
            valid_decision_census
            and manifest_decision_counts == summary_decision_counts
        ),
        "stage_stratified_reporting": (
            valid_case_counts
            and manifest_stages_valid
            and summary_stages_valid
            and manifest_stage_counts == summary.stage_case_counts
            and sum(manifest_stage_counts.values()) == case_count
        ),
        "all_fault_families": REQUIRED_FAULT_FAMILIES.issubset(
            set(summary.fault_families)
        ),
        "completion_by_deadline": summary.estimated_completion_date <= deadline,
        "cost_estimate_present": (
            type(summary.estimated_total_cost_usd) in {int, float}
            and summary.estimated_total_cost_usd >= 0.0
        ),
    }
    return PilotGateResult(
        passed=all(checks.values()),
        checks=checks,
        parse_success_rate=parse_rate,
        final_parse_success_rate=final_parse_rate,
        final_decision_accuracy=final_decision_accuracy,
        final_verdict_accuracy=final_verdict_accuracy,
        final_blocking_accuracy=final_blocking_accuracy,
        final_missing_evidence_accuracy=final_missing_evidence_accuracy,
        protocol_valid_rate=protocol_valid_rate,
        run_error_rate=error_rate,
        retry_rate=retry_rate,
        safe_share=safe_share,
        unsafe_share=unsafe_share,
        continue_share=continue_share,
        estimated_total_cost_usd=summary.estimated_total_cost_usd,
    )


def _load_summary(results: Path) -> PilotSummary:
    payload = json.loads(
        read_authenticated_file(
            results / "pilot_summary.json",
            label="pilot summary",
        ).decode("utf-8")
    )
    expected_keys = {
        "schema_version",
        "transaction_set_sha256",
        "planned_runs",
        "completed_runs",
        "parsed_states",
        "successful_parses",
        "final_runs",
        "successful_final_parses",
        "correct_final_decisions",
        "correct_final_verdicts",
        "correct_final_blocking",
        "correct_final_missing_evidence",
        "protocol_valid_runs",
        "run_errors",
        "retried_runs",
        "safe_cases",
        "unsafe_cases",
        "continue_cases",
        "fault_families",
        "estimated_completion_date",
        "estimated_total_cost_usd",
        "stage_case_counts",
    }
    if not isinstance(payload, dict) or set(payload) != expected_keys:
        raise ValueError("pilot summary schema keys are invalid")
    return PilotSummary(
        planned_runs=payload["planned_runs"],
        completed_runs=payload["completed_runs"],
        parsed_states=payload["parsed_states"],
        successful_parses=payload["successful_parses"],
        final_runs=payload["final_runs"],
        successful_final_parses=payload["successful_final_parses"],
        correct_final_decisions=payload["correct_final_decisions"],
        correct_final_verdicts=payload["correct_final_verdicts"],
        correct_final_blocking=payload["correct_final_blocking"],
        correct_final_missing_evidence=payload[
            "correct_final_missing_evidence"
        ],
        protocol_valid_runs=payload["protocol_valid_runs"],
        run_errors=payload["run_errors"],
        retried_runs=payload["retried_runs"],
        safe_cases=payload["safe_cases"],
        unsafe_cases=payload["unsafe_cases"],
        continue_cases=payload["continue_cases"],
        fault_families=tuple(payload["fault_families"]),
        estimated_completion_date=date.fromisoformat(
            payload["estimated_completion_date"]
        ),
        estimated_total_cost_usd=payload.get("estimated_total_cost_usd"),
        stage_case_counts=payload.get("stage_case_counts"),
        schema_version=payload["schema_version"],
        transaction_set_sha256=payload["transaction_set_sha256"],
    )


def transaction_set_receipt(results: Path) -> tuple[str, int]:
    """Return a content-addressed receipt for the exact transaction file set."""

    entries: list[dict[str, str]] = []
    with AuthenticatedTree(results, label="transaction results root") as tree:
        result_entries = tree.list_directory(None, label="transaction results root")
        transaction_entry = next(
            (entry for entry in result_entries if entry.name == "run_transactions"),
            None,
        )
        if transaction_entry is None or not transaction_entry.is_directory:
            return sha256_json(entries), 0
        paths = tuple(
            entry
            for entry in tree.list_directory(
                "run_transactions",
                label="transaction receipt directory",
            )
            if not entry.is_directory and entry.name.endswith(".json")
        )
        for path in paths:
            stem = Path(path.name).stem
            if _SHA256.fullmatch(stem) is None:
                raise ValueError("transaction filename is not a resume-key hash")
            artifact = tree.read_bytes(
                Path("run_transactions") / path.name,
                label=f"transaction receipt {path.name}",
            )
            entries.append(
                {
                    "resume_key": stem,
                    "file_sha256": hashlib.sha256(artifact).hexdigest(),
                }
            )
    return sha256_json(entries), len(entries)


def _load_run_manifest(results: Path) -> dict[str, Any]:
    payload = json.loads(
        read_authenticated_file(
            results / "run_manifest.json",
            label="pilot run manifest",
        ).decode("utf-8")
    )
    from .run_manifest import validate_run_manifest

    return validate_run_manifest(payload)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    transaction_hash, transaction_count = transaction_set_receipt(args.results)
    result = evaluate_pilot(
        _load_summary(args.results),
        run_manifest=_load_run_manifest(args.results),
        observed_transaction_set_sha256=transaction_hash,
        observed_transaction_count=transaction_count,
    )
    write_json_atomic(args.output, result.to_dict())
    cost = result.estimated_total_cost_usd
    print(f"pilot_gate={'PASS' if result.passed else 'FAIL'}")
    print(f"estimated_total_cost_usd={cost if cost is not None else 'MISSING'}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
