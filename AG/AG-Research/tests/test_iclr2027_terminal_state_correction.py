from __future__ import annotations

import json
import hashlib
import asyncio
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

from iclr2027.architecture_metrics import score_prefix, score_prefix_breakdown
from iclr2027.arr_adapter import packet_from_arr_artifacts
from iclr2027.review_state import (
    TurnRecord,
    accumulate_prefix_states,
    parse_review_state,
)
from iclr2027.schema import ArchitectureReviewState


_ALLOWED_BLOCKING_CODES = {
    "identity.attempt_hash_mismatch",
    "evidence.portfolio_attempt_incomplete",
    "selection.no_admitted_candidate",
    "materialization.no_candidate_reached_ledger",
    "preflight.program_site_infeasible",
    "site.boundary_failed",
    "geometry.compilation_failed",
    "identity.hash_mismatch",
    "law.projection_failed",
    "parking.supply_shortage",
    "program.capacity_failed",
}


class TerminalStateBlockingGrammarTests(unittest.TestCase):
    def test_schema_exposes_the_exact_allowed_blocking_code_frozen_set(self) -> None:
        allowed_codes = ArchitectureReviewState.ALLOWED_BLOCKING_ISSUE_CODES

        self.assertIsInstance(allowed_codes, frozenset)
        self.assertEqual(allowed_codes, frozenset(_ALLOWED_BLOCKING_CODES))

    def test_every_exact_allowed_blocker_constructs_successfully(self) -> None:
        for blocker in sorted(_ALLOWED_BLOCKING_CODES):
            with self.subTest(blocker=blocker):
                state = ArchitectureReviewState(
                    checked_domains=("geometry",),
                    blocking_issue_codes=(blocker,),
                    missing_evidence_codes=(),
                    evidence_ids=("evidence:geometry_agent",),
                    recommended_decision="STOP_REJECT",
                    confidence=0.9,
                )

                self.assertEqual(state.blocking_issue_codes, (blocker,))

    def test_invented_blocker_is_rejected_by_the_schema(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown blocking_issue_codes"):
            ArchitectureReviewState(
                checked_domains=("geometry",),
                blocking_issue_codes=("geometry.hard_failure",),
                missing_evidence_codes=(),
                evidence_ids=("evidence:geometry_agent",),
                recommended_decision="STOP_REJECT",
                confidence=0.9,
            )

    def test_invented_blocker_makes_arch_review_state_parse_incomplete(self) -> None:
        payload = {
            "checked_domains": ["geometry"],
            "blocking_issue_codes": ["geometry.hard_failure"],
            "missing_evidence_codes": [],
            "evidence_ids": ["evidence:geometry_agent"],
            "recommended_decision": "STOP_REJECT",
            "confidence": 0.9,
        }

        parsed = parse_review_state(
            "ARCH_REVIEW_STATE\n```json\n" + json.dumps(payload) + "\n```"
        )

        self.assertFalse(parsed.complete)
        self.assertEqual(parsed.error_codes, ("invalid_state",))


class TerminalStateOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.packet, cls.gold = packet_from_arr_artifacts(
            Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json",
            pnu="1168011800104170004",
            program="neighborhood",
            case_id="terminal-state-ownership-native",
        )

    @staticmethod
    def _turn(author: str, payload: dict[str, object]) -> TurnRecord:
        return TurnRecord(
            author=author,
            content="ARCH_REVIEW_STATE\n```json\n" + json.dumps(payload) + "\n```",
        )

    def test_terminal_accept_replaces_an_early_specialist_blocker(self) -> None:
        early = self._turn(
            "parking_agent",
            {
                "checked_domains": ["parking"],
                "blocking_issue_codes": ["parking.supply_shortage"],
                "missing_evidence_codes": [],
                "evidence_ids": ["evidence:parking_agent"],
                "recommended_decision": "STOP_REJECT",
                "confidence": 0.8,
            },
        )
        terminal = self._turn(
            "review_agent",
            {
                "checked_domains": ["site", "geometry", "law", "parking", "program"],
                "blocking_issue_codes": [],
                "missing_evidence_codes": [],
                "evidence_ids": [
                    "evidence:site_agent",
                    "evidence:geometry_agent",
                    "evidence:law_graph_agent",
                    "evidence:parking_agent",
                    "evidence:program_agent",
                    "evidence:review_agent",
                ],
                "recommended_decision": "STOP_ACCEPT",
                "confidence": 0.95,
            },
        )

        final = accumulate_prefix_states((early, terminal), self.packet)[-1]

        self.assertEqual(final.state.blocking_issue_codes, ())
        self.assertEqual(final.state.missing_evidence_codes, ())
        self.assertEqual(final.state.recommended_decision, "STOP_ACCEPT")
        self.assertEqual(
            score_prefix_breakdown(final, self.gold, self.packet)["decision_score"],
            1.0,
        )
        self.assertEqual(
            score_prefix_breakdown(final, self.gold, self.packet)["blocking_issue_f1"],
            1.0,
        )
        self.assertEqual(
            score_prefix(final, self.gold, self.packet).verdict_score,
            1.0,
        )

    def test_later_valid_state_replaces_issues_and_unions_provenance(self) -> None:
        earlier = self._turn(
            "law_agent",
            {
                "checked_domains": ["law"],
                "blocking_issue_codes": ["parking.supply_shortage"],
                "missing_evidence_codes": ["law.required_evidence_missing"],
                "evidence_ids": ["evidence:law_graph_agent"],
                "recommended_decision": "STOP_REJECT",
                "confidence": 0.7,
            },
        )
        later = self._turn(
            "parking_agent",
            {
                "checked_domains": ["parking"],
                "blocking_issue_codes": [],
                "missing_evidence_codes": ["parking.required_evidence_missing"],
                "evidence_ids": ["evidence:parking_agent"],
                "recommended_decision": "CONTINUE",
                "confidence": 0.6,
            },
        )

        final = accumulate_prefix_states((earlier, later), self.packet)[-1]

        self.assertEqual(final.state.checked_domains, ("law", "parking"))
        self.assertEqual(
            final.state.evidence_ids,
            ("evidence:law_graph_agent", "evidence:parking_agent"),
        )
        self.assertEqual(final.state.blocking_issue_codes, ())
        self.assertEqual(
            final.state.missing_evidence_codes,
            ("parking.required_evidence_missing",),
        )
        self.assertEqual(final.state.recommended_decision, "CONTINUE")
        self.assertEqual(final.state.confidence, 0.6)
        self.assertTrue(final.parse_complete)

    def test_invalid_current_turn_keeps_only_prior_valid_provenance(self) -> None:
        prior = self._turn(
            "parking_agent",
            {
                "checked_domains": ["parking"],
                "blocking_issue_codes": ["parking.supply_shortage"],
                "missing_evidence_codes": [],
                "evidence_ids": ["evidence:parking_agent"],
                "recommended_decision": "STOP_REJECT",
                "confidence": 0.8,
            },
        )
        invalid = self._turn(
            "review_agent",
            {
                "checked_domains": ["geometry"],
                "blocking_issue_codes": ["geometry.compilation_failed"],
                "missing_evidence_codes": ["law.required_evidence_missing"],
                "evidence_ids": ["evidence:geometry_agent"],
                "recommended_decision": "STOP_ACCEPT",
                "confidence": 0.99,
            },
        )

        final = accumulate_prefix_states((prior, invalid), self.packet)[-1]

        self.assertFalse(final.parse_complete)
        self.assertEqual(final.state.recommended_decision, "CONTINUE")
        self.assertEqual(final.state.confidence, 0.0)
        self.assertEqual(final.state.checked_domains, ("parking",))
        self.assertEqual(final.state.evidence_ids, ("evidence:parking_agent",))
        self.assertEqual(final.state.blocking_issue_codes, ())
        self.assertEqual(final.state.missing_evidence_codes, ())


class PilotSummaryV2ContractTests(unittest.TestCase):
    _PROVENANCE_CHECKS = {
        "final_run_keys_unique",
        "final_run_keys_complete",
        "reference_join_one_to_one",
        "common_denominator_consistent",
        "scorer_identity",
        "numerator_key_set_bound",
        "correct_final_numerators_bounded_by_successful_parses",
    }

    @staticmethod
    def _sha256_json(value: object) -> str:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @classmethod
    def _provenance(cls) -> dict[str, object]:
        final_key_digest = "a" * 64
        scorer_path = Path(__file__).parents[1] / "iclr2027" / "architecture_metrics.py"
        return {
            "schema_version": "ace.iclr2027.pilot_scoring_provenance.v1",
            "scorer_sha256": hashlib.sha256(scorer_path.read_bytes()).hexdigest(),
            "final_run_key_set_sha256": final_key_digest,
            "final_run_key_count": 450,
            "unique_final_run_key_count": 450,
            "missing_final_run_key_count": 0,
            "duplicate_final_run_key_count": 0,
            "reference_join_count": 450,
            "common_denominator": 450,
            "numerator_key_set_binding_sha256": cls._sha256_json(
                {
                    "blocking": final_key_digest,
                    "decision": final_key_digest,
                    "missing_evidence": final_key_digest,
                    "verdict": final_key_digest,
                }
            ),
        }

    @classmethod
    def _summary_payload(cls, *, version: int = 1) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": f"ace.iclr2027.pilot_summary.v{version}",
            "transaction_set_sha256": "d" * 64,
            "planned_runs": 450,
            "completed_runs": 450,
            "parsed_states": 450,
            "successful_parses": 450,
            "final_runs": 450,
            "successful_final_parses": 450,
            "correct_final_decisions": 450,
            "correct_final_verdicts": 450,
            "correct_final_blocking": 450,
            "correct_final_missing_evidence": 450,
            "protocol_valid_runs": 450,
            "run_errors": 0,
            "retried_runs": 0,
            "safe_cases": 7,
            "unsafe_cases": 21,
            "continue_cases": 2,
            "fault_families": [
                "identity_hash",
                "law_projection",
                "parking_shortage",
                "program_capacity",
                "geometry_compile",
            ],
            "estimated_completion_date": "2026-09-01",
            "estimated_total_cost_usd": 42.5,
            "stage_case_counts": {
                "execution": 14,
                "selection": 6,
                "materialization": 6,
                "preflight": 4,
            },
        }
        if version == 2:
            payload["scoring_provenance"] = cls._provenance()
        return payload

    @staticmethod
    def _manifest() -> dict[str, object]:
        return {
            "schema_version": "ace.iclr2027.exp08_run_manifest.v2",
            "input_mode": "frozen_private_binding",
            "split": "dev",
            "patterns": ["rr3", "sel3", "swm3", "refl3", "debate3"],
            "repeats": 3,
            "model": "fixture-model",
            "code_commit": "fixture-commit",
            "expected_case_count": 30,
            "case_count": 30,
            "planned_run_count": 450,
            "stage_case_counts": {
                "execution": 14,
                "selection": 6,
                "materialization": 6,
                "preflight": 4,
            },
            "decision_case_counts": {
                "STOP_ACCEPT": 7,
                "STOP_REJECT": 21,
                "CONTINUE": 2,
            },
            "input_hashes": {
                f"input:{index:064x}": f"{index:064x}" for index in range(1, 7)
            },
            "identity_commitment": "a" * 64,
            "registry_core_sha256": "b" * 64,
            "split_manifest_sha256": "c" * 64,
            "plan_sha256": "d" * 64,
            "executed": True,
            "execution": {
                "completed_runs": 450,
                "skipped_runs": 0,
                "error_runs": 0,
                "parsed_states": 450,
                "successful_parses": 450,
            },
            "estimated_cost_per_run_usd": 42.5 / 450,
            "estimated_total_cost_usd": 42.5,
            "estimated_completion_date": "2026-09-01",
        }

    def _load(self, payload: dict[str, object]):
        from iclr2027.pilot_gate import _load_summary

        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp)
            (results / "pilot_summary.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            return _load_summary(results)

    def _evaluate(self, payload: dict[str, object]):
        return self._evaluate_summary(self._load(payload))

    def _evaluate_summary(self, summary):
        from iclr2027.pilot_gate import evaluate_pilot

        return evaluate_pilot(
            summary,
            run_manifest=self._manifest(),
            observed_transaction_set_sha256="d" * 64,
            observed_transaction_count=450,
            deadline=date(2026, 9, 2),
        )

    def test_exact_v1_load_and_gate_serialization_remain_historical(self) -> None:
        summary = self._load(self._summary_payload())

        result = self._evaluate(self._summary_payload())
        serialized = result.to_dict()

        self.assertFalse(hasattr(summary, "evaluation_profile"))
        self.assertEqual(summary.to_dict(), self._summary_payload())
        self.assertNotIn("scoring_provenance", summary.to_dict())
        self.assertNotIn("evaluation_profile", serialized)
        self.assertTrue(self._PROVENANCE_CHECKS.isdisjoint(result.checks))

    def test_direct_summary_construction_rejects_mixed_schema_pairings(self) -> None:
        from iclr2027.pilot_gate import (
            PILOT_SUMMARY_V2_SCHEMA,
            PilotScoringProvenance,
        )

        v1 = self._load(self._summary_payload())
        provenance = PilotScoringProvenance.from_dict(self._provenance())
        for label, changes in (
            ("v1 with provenance", {"scoring_provenance": provenance}),
            (
                "v2 without provenance",
                {
                    "schema_version": PILOT_SUMMARY_V2_SCHEMA,
                    "scoring_provenance": None,
                },
            ),
        ):
            with (
                self.subTest(label=label),
                self.assertRaisesRegex(
                    ValueError,
                    "schema/provenance",
                ),
            ):
                replace(v1, **changes)

    def test_direct_provenance_construction_enforces_field_domains(self) -> None:
        from iclr2027.pilot_gate import PilotScoringProvenance

        for label, changes in (
            ("schema", {"schema_version": "not-the-schema"}),
            ("digest", {"final_run_key_set_sha256": "A" * 64}),
            ("negative count", {"final_run_key_count": -1}),
            ("boolean count", {"common_denominator": True}),
        ):
            payload = {**self._provenance(), **changes}
            with self.subTest(label=label), self.assertRaises(ValueError):
                PilotScoringProvenance(**payload)

    def test_evaluate_revalidates_a_mutated_direct_provenance_instance(self) -> None:
        summary = self._load(self._summary_payload(version=2))
        provenance = summary.scoring_provenance
        assert provenance is not None
        object.__setattr__(provenance, "schema_version", "not-the-schema")

        with self.assertRaisesRegex(ValueError, "provenance schema"):
            self._evaluate_summary(summary)

    def test_loader_rejects_missing_or_mixed_v2_root_keys(self) -> None:
        missing_receipt = self._summary_payload(version=2)
        del missing_receipt["scoring_provenance"]
        mixed_v1 = self._summary_payload()
        mixed_v1["scoring_provenance"] = self._provenance()

        for label, payload in (
            ("v2 missing scoring_provenance", missing_receipt),
            ("v1 carrying v2 scoring_provenance", mixed_v1),
        ):
            with (
                self.subTest(label=label),
                self.assertRaisesRegex(
                    ValueError,
                    "pilot summary schema keys",
                ),
            ):
                self._load(payload)

    def test_provenance_payload_enforces_exact_keys_and_field_domains(self) -> None:
        from iclr2027.pilot_gate import PilotScoringProvenance

        expected_keys = {
            "schema_version",
            "scorer_sha256",
            "final_run_key_set_sha256",
            "final_run_key_count",
            "unique_final_run_key_count",
            "missing_final_run_key_count",
            "duplicate_final_run_key_count",
            "reference_join_count",
            "common_denominator",
            "numerator_key_set_binding_sha256",
        }
        receipt = PilotScoringProvenance.from_dict(self._provenance())

        self.assertEqual(set(receipt.to_dict()), expected_keys)
        self.assertEqual(receipt.to_dict(), self._provenance())
        for label, mutation in (
            ("extra", {**self._provenance(), "extra": 1}),
            ("bad schema", {**self._provenance(), "schema_version": "v1"}),
            ("bad hash", {**self._provenance(), "final_run_key_set_sha256": "no"}),
            ("bad count", {**self._provenance(), "final_run_key_count": -1}),
        ):
            with self.subTest(label=label), self.assertRaises(ValueError):
                PilotScoringProvenance.from_dict(mutation)

    def test_v2_gate_names_each_closed_provenance_failure(self) -> None:
        valid = self._summary_payload(version=2)
        result = self._evaluate(valid)

        self.assertEqual(result.evaluation_profile, "terminal_state_v2")
        self.assertEqual(valid, self._load(valid).to_dict())
        self.assertEqual(
            set(result.checks) & self._PROVENANCE_CHECKS, self._PROVENANCE_CHECKS
        )
        self.assertTrue(all(result.checks[name] for name in self._PROVENANCE_CHECKS))
        self.assertTrue(result.passed)

        cases = {
            "duplicate": (
                "final_run_keys_unique",
                {"duplicate_final_run_key_count": 1, "unique_final_run_key_count": 449},
            ),
            "missing": (
                "final_run_keys_complete",
                {"missing_final_run_key_count": 1},
            ),
            "count mismatch": (
                "final_run_keys_complete",
                {"final_run_key_count": 449},
            ),
            "reference join mismatch": (
                "reference_join_one_to_one",
                {"reference_join_count": 449},
            ),
            "denominator mismatch": (
                "common_denominator_consistent",
                {"common_denominator": 449},
            ),
            "invalid binding digest": (
                "numerator_key_set_bound",
                {"numerator_key_set_binding_sha256": "b" * 64},
            ),
            "wrong scorer hash": (
                "scorer_identity",
                {"scorer_sha256": "c" * 64},
            ),
        }
        for label, (failed_check, changes) in cases.items():
            payload = self._summary_payload(version=2)
            payload["scoring_provenance"] = {
                **self._provenance(),
                **changes,
            }
            with self.subTest(label=label):
                failed = self._evaluate(payload)
                self.assertFalse(failed.checks[failed_check])
                self.assertFalse(failed.passed)

    def test_450_final_runs_require_428_successes_for_every_95pct_check(self) -> None:
        threshold_checks = {
            "parse_success_at_least_95pct",
            "final_decision_at_least_95pct",
            "final_verdict_at_least_95pct",
            "final_blocking_at_least_95pct",
            "final_missing_evidence_at_least_95pct",
        }
        payload = self._summary_payload(version=2)
        for field in (
            "successful_parses",
            "correct_final_decisions",
            "correct_final_verdicts",
            "correct_final_blocking",
            "correct_final_missing_evidence",
        ):
            payload[field] = 428

        accepted = self._evaluate(payload)
        self.assertTrue(all(accepted.checks[name] for name in threshold_checks))

        for field, check in (
            ("successful_parses", "parse_success_at_least_95pct"),
            ("correct_final_decisions", "final_decision_at_least_95pct"),
            ("correct_final_verdicts", "final_verdict_at_least_95pct"),
            ("correct_final_blocking", "final_blocking_at_least_95pct"),
            (
                "correct_final_missing_evidence",
                "final_missing_evidence_at_least_95pct",
            ),
        ):
            rejected_payload = dict(payload)
            rejected_payload[field] = 427
            with self.subTest(field=field):
                rejected = self._evaluate(rejected_payload)
                self.assertFalse(rejected.checks[check])

    def test_v1_gate_preserves_historical_numerator_count_semantics(self) -> None:
        payload = self._summary_payload()
        payload["successful_final_parses"] = 449

        result = self._evaluate(payload)

        self.assertTrue(result.checks["pilot_summary_count_domains"])
        self.assertNotIn(
            "correct_final_numerators_bounded_by_successful_parses",
            result.checks,
        )
        self.assertEqual(result.final_decision_accuracy, 1.0)
        self.assertEqual(result.final_verdict_accuracy, 1.0)
        self.assertEqual(result.final_blocking_accuracy, 1.0)
        self.assertEqual(result.final_missing_evidence_accuracy, 1.0)

    def test_v2_gate_requires_numerators_within_successful_final_parses(self) -> None:
        payload = self._summary_payload(version=2)
        payload["successful_final_parses"] = 449

        result = self._evaluate(payload)

        check = "correct_final_numerators_bounded_by_successful_parses"
        self.assertIn(check, result.checks)
        self.assertFalse(result.checks[check])
        self.assertFalse(result.passed)


class ScoringProvenanceTests(unittest.TestCase):
    @staticmethod
    def _case_records():
        from iclr2027.schema import (
            ArchitectureEvidencePacket,
            ArchitectureGoldRecord,
            ArchitecturePublicCase,
        )

        case_id = "case:" + "1" * 64
        packet = ArchitectureEvidencePacket(
            case_id=case_id,
            pnu="1168011800104170004",
            program="neighborhood",
            condition="native",
            execution_id="synthetic-execution",
            program_hash="a" * 64,
            geometry_hash="b" * 64,
            evidence=({"evidence_id": "evidence:site", "domain": "site"},),
        )
        gold = ArchitectureGoldRecord(
            case_id=case_id,
            expected_decision="STOP_ACCEPT",
            blocking_issue_codes=(),
            missing_evidence_codes=(),
            required_evidence_ids=("evidence:site",),
            mutation_family="",
        )
        public = ArchitecturePublicCase(
            case_id=case_id,
            site_ref="site:" + "2" * 64,
            program="neighborhood",
            execution_id="synthetic-execution",
            program_hash="a" * 64,
            geometry_hash="b" * 64,
            evidence=({"evidence_id": "evidence:site", "status": "passed"},),
            source_artifact_sha256="c" * 64,
        )
        return public, packet, gold

    @staticmethod
    def _build_plans(public, *, patterns: tuple[str, ...], model: str):
        from iclr2027.exp08 import build_run_plan

        return build_run_plan(
            (public,),
            patterns=patterns,
            repeats=1,
            model=model,
            code_commit="synthetic-commit",
        )

    @staticmethod
    def _execute(
        output_dir: Path,
        plans,
        packet,
        gold,
        *,
        state: dict[str, object] | None = None,
    ) -> None:
        from experiment_utils import RunResult, TurnRecord as ExperimentTurnRecord
        from iclr2027.exp08 import execute_run_plans

        if state is None:
            state = {
                "checked_domains": ["site"],
                "blocking_issue_codes": [],
                "missing_evidence_codes": [],
                "evidence_ids": ["evidence:site"],
                "recommended_decision": "STOP_ACCEPT",
                "confidence": 0.9,
            }

        async def run_single(**kwargs: object) -> RunResult:
            return RunResult(
                experiment_id="exp08",
                task_id=str(kwargs["task_id"]),
                pattern=str(kwargs["pattern"]),
                repeat_index=int(kwargs["repeat_index"]),
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
                    ExperimentTurnRecord(
                        index=1,
                        source="review_agent",
                        content=(
                            "ARCH_REVIEW_STATE\n```json\n"
                            + json.dumps(state)
                            + "\n```\nTERMINATE"
                        ),
                        timestamp="2026-09-01T00:00:00+00:00",
                        tokens_in=10,
                        tokens_out=20,
                    )
                ],
            )

        asyncio.run(
            execute_run_plans(
                plans=plans,
                packets_by_case={packet.case_id: packet},
                gold_by_case={gold.case_id: gold},
                output_dir=output_dir,
                team_builder=lambda *_args: object(),
                run_single=run_single,
            )
        )

    @staticmethod
    def _summarize(output_dir: Path, plans, packet, gold):
        from iclr2027.exp08 import summarize_pilot

        return summarize_pilot(
            output_dir=output_dir,
            plans=plans,
            packets_by_case={packet.case_id: packet},
            gold_by_case={gold.case_id: gold},
            estimated_completion_date=date(2026, 9, 1),
            estimated_total_cost_usd=1.0,
        )

    def test_summary_emits_closed_v2_scoring_receipt(self) -> None:
        public, packet, gold = self._case_records()
        plans = self._build_plans(
            public,
            patterns=("rr3", "sel3"),
            model="synthetic-model",
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            self._execute(output_dir, plans, packet, gold)

            summary = self._summarize(output_dir, plans, packet, gold)

        receipt = summary.scoring_provenance
        self.assertEqual(summary.schema_version, "ace.iclr2027.pilot_summary.v2")
        self.assertIsNotNone(receipt)
        assert receipt is not None
        self.assertEqual(receipt.common_denominator, summary.final_runs)
        self.assertEqual(receipt.final_run_key_count, summary.final_runs)
        self.assertEqual(
            receipt.unique_final_run_key_count, receipt.final_run_key_count
        )
        self.assertEqual(receipt.missing_final_run_key_count, 0)
        self.assertEqual(receipt.duplicate_final_run_key_count, 0)
        self.assertEqual(receipt.reference_join_count, summary.final_runs)
        scorer_path = Path(__file__).parents[1] / "iclr2027" / "architecture_metrics.py"
        self.assertEqual(
            receipt.scorer_sha256,
            hashlib.sha256(scorer_path.read_bytes()).hexdigest(),
        )
        final_keys = sorted(
            (
                PilotSummaryV2ContractTests._sha256_json(
                    {
                        "case_id": plan.case_id,
                        "pattern": plan.pattern,
                        "repeat": plan.repeat,
                    }
                )
                for plan in plans
            ),
            key=lambda value: value.encode("utf-8"),
        )
        self.assertEqual(
            receipt.final_run_key_set_sha256,
            PilotSummaryV2ContractTests._sha256_json(final_keys),
        )
        serialized = summary.to_dict()
        self.assertEqual(serialized["scoring_provenance"], receipt.to_dict())

    def test_incomplete_final_parse_cannot_increment_correctness_numerators(
        self,
    ) -> None:
        public, packet, gold = self._case_records()
        plans = self._build_plans(
            public,
            patterns=("rr3",),
            model="synthetic-model",
        )
        incomplete_state = {
            "checked_domains": ["site"],
            "blocking_issue_codes": ["geometry.hard_failure"],
            "missing_evidence_codes": [],
            "evidence_ids": ["evidence:site"],
            "recommended_decision": "STOP_ACCEPT",
            "confidence": 0.9,
        }
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            self._execute(
                output_dir,
                plans,
                packet,
                gold,
                state=incomplete_state,
            )

            summary = self._summarize(output_dir, plans, packet, gold)

        self.assertEqual(summary.final_runs, 1)
        self.assertEqual(summary.successful_final_parses, 0)
        self.assertEqual(
            (
                summary.correct_final_decisions,
                summary.correct_final_verdicts,
                summary.correct_final_blocking,
                summary.correct_final_missing_evidence,
            ),
            (0, 0, 0, 0),
        )

    def test_duplicate_synthetic_final_key_fails_before_summary_emission(self) -> None:
        public, packet, gold = self._case_records()
        first = self._build_plans(
            public,
            patterns=("rr3",),
            model="synthetic-model-a",
        )[0]
        duplicate = self._build_plans(
            public,
            patterns=("rr3",),
            model="synthetic-model-b",
        )[0]
        plans = (first, duplicate)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            self._execute(output_dir, plans, packet, gold)

            with self.assertRaisesRegex(ValueError, "duplicate final-run key"):
                self._summarize(output_dir, plans, packet, gold)

    def test_missing_synthetic_final_key_fails_before_summary_emission(self) -> None:
        public, packet, gold = self._case_records()
        observed_plans = self._build_plans(
            public,
            patterns=("rr3", "swm3"),
            model="synthetic-model",
        )
        planned = self._build_plans(
            public,
            patterns=("rr3", "sel3"),
            model="synthetic-model",
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            self._execute(output_dir, observed_plans, packet, gold)

            with self.assertRaisesRegex(ValueError, "missing final-run key"):
                self._summarize(output_dir, planned, packet, gold)


if __name__ == "__main__":
    unittest.main()
