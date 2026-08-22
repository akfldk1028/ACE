from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path


def _packet():
    from iclr2027.schema import ArchitectureEvidencePacket

    evidence_ids = (
        "evidence:site_agent",
        "evidence:geometry_agent",
        "evidence:law_graph_agent",
        "evidence:parking_agent",
        "evidence:program_agent",
        "evidence:review_agent",
    )
    return ArchitectureEvidencePacket(
        case_id="protocol-case",
        pnu="1168011800104170004",
        program="neighborhood",
        condition="native",
        execution_id="execution-1",
        program_hash="a" * 64,
        geometry_hash="b" * 64,
        evidence=tuple({"evidence_id": item} for item in evidence_ids),
    )


def _block(decision: str = "STOP_REJECT") -> str:
    payload = {
        "state_schema": "ARCH_REVIEW_STATE",
        "checked_domains": ["site", "geometry", "law", "parking", "program"],
        "blocking_issue_codes": (
            ["program.capacity_failed"] if decision == "STOP_REJECT" else []
        ),
        "missing_evidence_codes": (
            ["parking.required_evidence_missing"] if decision == "CONTINUE" else []
        ),
        "evidence_ids": [
            "evidence:site_agent",
            "evidence:geometry_agent",
            "evidence:law_graph_agent",
            "evidence:parking_agent",
            "evidence:program_agent",
            "evidence:review_agent",
        ],
        "recommended_decision": decision,
        "confidence": 0.9,
    }
    return "ARCH_REVIEW_STATE\n```json\n" + json.dumps(payload) + "\n```"


def _turn(source: str, content: str | None = None):
    return SimpleNamespace(source=source, content=_block() if content is None else content)


class PilotProtocolTests(unittest.TestCase):
    def test_complete_three_role_terminal_run_is_valid(self) -> None:
        from iclr2027.protocol import validate_pilot_protocol

        errors = validate_pilot_protocol(
            pattern="swm3",
            turns=(
                _turn("geometry_agent"),
                _turn("compliance_agent"),
                _turn("review_agent", _block() + "\nTERMINATE"),
            ),
            packet=_packet(),
            terminated_by="structured_state",
        )

        self.assertEqual(errors, ())

    def test_terminal_provenance_cannot_replace_the_exact_signal(self) -> None:
        from iclr2027.protocol import validate_pilot_protocol

        turns = (
            _turn("geometry_agent"),
            _turn("compliance_agent"),
            _turn("review_agent"),
        )
        missing_signal = validate_pilot_protocol(
            pattern="swm3",
            turns=turns,
            packet=_packet(),
            terminated_by="structured_state",
        )
        continue_with_signal = validate_pilot_protocol(
            pattern="debate3",
            turns=(*turns[:-1], _turn("review_agent", _block("CONTINUE") + "\nTERMINATE")),
            packet=_packet(),
            terminated_by="max_messages",
        )
        whitespace_signal = validate_pilot_protocol(
            pattern="swm3",
            turns=(*turns[:-1], _turn("review_agent", _block() + "\n TERMINATE ")),
            packet=_packet(),
            terminated_by="structured_state",
        )

        self.assertIn("protocol.terminal_signal_missing", missing_signal)
        self.assertIn("protocol.continue_signal_present", continue_with_signal)
        self.assertIn("protocol.terminal_signal_missing", whitespace_signal)

    def test_missing_roles_empty_or_malformed_final_and_missing_signal_fail(self) -> None:
        from iclr2027.protocol import validate_pilot_protocol

        cases = (
            (
                (_turn("geometry_agent"),) * 3,
                "max_messages",
                {"protocol.role_coverage_missing", "protocol.final_source_not_reviewer"},
            ),
            (
                (
                    _turn("geometry_agent"),
                    _turn("compliance_agent"),
                    _turn("review_agent", ""),
                ),
                "max_messages",
                {"protocol.empty_agent_content", "protocol.final_state_incomplete"},
            ),
            (
                (
                    _turn("geometry_agent"),
                    _turn("compliance_agent"),
                    _turn("review_agent", "analysis before a fence"),
                ),
                "max_messages",
                {"protocol.final_state_incomplete"},
            ),
            (
                (
                    _turn("geometry_agent"),
                    _turn("compliance_agent"),
                    _turn("review_agent"),
                ),
                "max_messages",
                {"protocol.terminal_signal_missing"},
            ),
        )
        for turns, terminated_by, expected in cases:
            with self.subTest(expected=expected):
                errors = set(
                    validate_pilot_protocol(
                        pattern="swm3",
                        turns=turns,
                        packet=_packet(),
                        terminated_by=terminated_by,
                    )
                )
                self.assertTrue(expected.issubset(errors))

    def test_continue_may_end_at_max_after_complete_reviewer_state(self) -> None:
        from iclr2027.protocol import validate_pilot_protocol

        errors = validate_pilot_protocol(
            pattern="debate3",
            turns=(
                _turn("geometry_agent"),
                _turn("compliance_agent"),
                _turn("review_agent", _block("CONTINUE")),
            ),
            packet=_packet(),
            terminated_by="max_messages",
        )

        self.assertEqual(errors, ())

    def test_executor_retries_gold_blind_protocol_failure_before_persisting(self) -> None:
        from experiment_utils import RunResult, TurnRecord
        from iclr2027.exp08 import build_run_plan, execute_run_plans
        from iclr2027.projection import (
            ProjectionIdentity,
            project_gold_record,
            project_public_case,
        )
        from iclr2027.schema import ArchitectureGoldRecord

        packet = _packet()
        gold = ArchitectureGoldRecord(
            case_id=packet.case_id,
            expected_decision="STOP_REJECT",
            blocking_issue_codes=("program.capacity_failed",),
            missing_evidence_codes=(),
            required_evidence_ids=tuple(
                str(item["evidence_id"]) for item in packet.evidence
            ),
            mutation_family="program_failure",
        )
        identity = ProjectionIdentity(bytes(range(32)))
        public_case = project_public_case(packet, identity)
        public_gold = project_gold_record(gold, packet, identity)
        plans = build_run_plan(
            (public_case,),
            patterns=("swm3",),
            repeats=1,
            model="test-model",
            code_commit="abc123",
        )

        def result(sources: tuple[str, ...], terminated_by: str) -> RunResult:
            turns = [
                TurnRecord(
                    index=0,
                    source="user",
                    content="public task",
                    timestamp="2026-08-19T00:00:00+00:00",
                )
            ] + [
                TurnRecord(
                    index=index + 1,
                    source=source,
                    content=(
                        _block() + "\nTERMINATE"
                        if source == "review_agent"
                        else _block()
                    ),
                    timestamp="2026-08-19T00:00:00+00:00",
                )
                for index, source in enumerate(sources)
            ]
            return RunResult(
                experiment_id="exp08",
                task_id=packet.case_id,
                pattern="swm3",
                repeat_index=0,
                pattern_category="swarm",
                agent_count=3,
                stop_reason=terminated_by,
                duration_sec=0.1,
                total_tokens_in=0,
                total_tokens_out=0,
                total_tokens=0,
                turn_count=len(turns),
                agent_turn_count=len(sources),
                terminated_by=terminated_by,
                turns=turns,
            )

        results = [
            result(("geometry_agent",) * 3, "max_messages"),
            result(
                ("geometry_agent", "compliance_agent", "review_agent"),
                "structured_state",
            ),
        ]
        calls = 0

        async def run_single(**_: object) -> RunResult:
            nonlocal calls
            calls += 1
            return results.pop(0)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            summary = asyncio.run(
                execute_run_plans(
                    plans=plans,
                    packets_by_case={public_case.case_id: packet},
                    gold_by_case={public_case.case_id: public_gold},
                    output_dir=output_dir,
                    team_builder=lambda *_args: object(),
                    run_single=run_single,
                    max_attempts=2,
                    enforce_pilot_protocol=True,
                )
            )
            error_rows = [
                json.loads(line)
                for line in (output_dir / "errors_retries.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]

        self.assertEqual(calls, 2)
        self.assertEqual(summary.error_runs, 0)
        self.assertEqual(len(error_rows), 1)
        self.assertIn("protocol.role_coverage_missing", error_rows[0]["error"])


if __name__ == "__main__":
    unittest.main()
