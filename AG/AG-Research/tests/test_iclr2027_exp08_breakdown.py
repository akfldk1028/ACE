from __future__ import annotations

import asyncio
import csv
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from experiment_utils import RunResult, TurnRecord
from iclr2027.exp08 import build_run_plan, execute_run_plans
from iclr2027.projection import ProjectionIdentity, project_gold_record, project_public_case
from iclr2027.schema import ArchitectureEvidencePacket, ArchitectureGoldRecord


class Exp08BreakdownPersistenceTests(unittest.TestCase):
    def test_breakdown_rows_match_scores_and_rebuild_deterministically_after_retry(self) -> None:
        packet = ArchitectureEvidencePacket(
            case_id="dev-case-breakdown-01",
            pnu="1168011800104170004",
            program="neighborhood",
            condition="native",
            execution_id="execution-1",
            program_hash="a" * 64,
            geometry_hash="b" * 64,
            evidence=(
                {"evidence_id": "evidence:site_agent", "domain": "site"},
            ),
        )
        gold = ArchitectureGoldRecord(
            case_id=packet.case_id,
            expected_decision="STOP_ACCEPT",
            blocking_issue_codes=(),
            missing_evidence_codes=(),
            required_evidence_ids=("evidence:site_agent",),
            mutation_family="",
        )
        identity = ProjectionIdentity(bytes(range(32)))
        public_case = project_public_case(packet, identity)
        public_gold = project_gold_record(gold, packet, identity)
        plans = build_run_plan(
            (public_case,),
            patterns=("rr3",),
            repeats=1,
            model="test-model",
            code_commit="abc123",
        )
        state = {
            "checked_domains": ["site"],
            "blocking_issue_codes": [],
            "missing_evidence_codes": [],
            "evidence_ids": ["evidence:site_agent"],
            "recommended_decision": "STOP_ACCEPT",
            "confidence": 0.9,
        }
        successful_result = RunResult(
            experiment_id="exp08",
            task_id=packet.case_id,
            pattern="rr3",
            repeat_index=0,
            pattern_category="flat",
            agent_count=3,
            stop_reason="TERMINATE",
            duration_sec=0.1,
            total_tokens_in=10,
            total_tokens_out=20,
            total_tokens=30,
            turn_count=1,
            agent_turn_count=1,
            terminated_by="keyword",
            turns=[
                TurnRecord(
                    index=7,
                    source="review_agent",
                    content=(
                        "ARCH_REVIEW_STATE\n```json\n"
                        + json.dumps(state)
                        + "\n```\nTERMINATE"
                    ),
                    timestamp="2026-08-18T00:00:00+00:00",
                    tokens_in=10,
                    tokens_out=20,
                )
            ],
        )
        results = [
            replace(successful_result, error="temporary model error"),
            successful_result,
        ]

        async def run_single(**_kwargs: object) -> RunResult:
            return results.pop(0)

        def team_builder(
            _pattern: str,
            _model: str,
            _allowed_evidence_ids: tuple[str, ...],
        ) -> object:
            return object()

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            kwargs = {
                "plans": plans,
                "packets_by_case": {public_case.case_id: packet},
                "gold_by_case": {public_case.case_id: public_gold},
                "output_dir": output_dir,
                "team_builder": team_builder,
                "run_single": run_single,
            }

            first = asyncio.run(execute_run_plans(**kwargs))
            score_path = output_dir / "turn_scores.csv"
            breakdown_path = output_dir / "turn_score_breakdown.csv"
            score_text = score_path.read_text(encoding="utf-8")
            breakdown_text = breakdown_path.read_text(encoding="utf-8")
            with score_path.open(encoding="utf-8", newline="") as handle:
                score_reader = csv.DictReader(handle)
                self.assertEqual(
                    score_reader.fieldnames,
                    [
                        "resume_key",
                        "case_id",
                        "pattern",
                        "repeat",
                        "turn_index",
                        "issue_f1",
                        "evidence_f1",
                        "domain_coverage",
                        "verdict_score",
                        "quality",
                    ],
                )
                score_rows = list(score_reader)
            with breakdown_path.open(encoding="utf-8", newline="") as handle:
                breakdown_rows = list(csv.DictReader(handle))

            identity_fields = (
                "resume_key",
                "case_id",
                "pattern",
                "repeat",
                "turn_index",
            )
            self.assertEqual(first.completed_runs, 1)
            self.assertEqual(len(score_rows), 1)
            self.assertEqual(len(breakdown_rows), 1)
            self.assertEqual(
                {tuple(row[field] for field in identity_fields) for row in score_rows},
                {
                    tuple(row[field] for field in identity_fields)
                    for row in breakdown_rows
                },
            )
            self.assertEqual(
                {key: breakdown_rows[0][key] for key in (
                    "subject_stage",
                    "decision_score",
                    "blocking_issue_f1",
                    "missing_evidence_f1",
                )},
                {
                    "subject_stage": "execution",
                    "decision_score": "1.0",
                    "blocking_issue_f1": "1.0",
                    "missing_evidence_f1": "1.0",
                },
            )

            with breakdown_path.open("a", encoding="utf-8") as handle:
                handle.write("torn")
            resumed = asyncio.run(execute_run_plans(**kwargs))
            self.assertEqual(resumed.skipped_runs, 1)
            self.assertEqual(score_path.read_text(encoding="utf-8"), score_text)
            self.assertEqual(
                breakdown_path.read_text(encoding="utf-8"),
                breakdown_text,
            )

            breakdown_path.unlink()
            rebuilt = asyncio.run(execute_run_plans(**kwargs))
            self.assertEqual(rebuilt.skipped_runs, 1)
            self.assertEqual(
                breakdown_path.read_text(encoding="utf-8"),
                breakdown_text,
            )


if __name__ == "__main__":
    unittest.main()
