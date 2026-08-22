from __future__ import annotations

import asyncio
import copy
import json
import tempfile
import unittest
from pathlib import Path

from experiment_utils import RunResult
from iclr2027.exp08 import (
    RunPlan,
    _materialize_transactions,
    execute_run_plans,
)
from iclr2027.io import sha256_json
from iclr2027.schema import ArchitectureEvidencePacket, ArchitectureGoldRecord


def _valid_transaction(
    *,
    turn_indices: tuple[int, ...] = (7,),
    status: str = "completed",
    final_error: str | None = None,
    error_attempts: tuple[int, ...] = (),
) -> tuple[str, dict]:
    identity = {
        "case_id": "case:" + "1" * 64,
        "pattern": "rr3",
        "repeat": 0,
        "model": "fixture-model",
        "public_case_sha256": "b" * 64,
        "prompt_sha256": "c" * 64,
        "code_commit": "fixture-commit",
    }
    resume_key = sha256_json(identity)
    state = {
        "checked_domains": ["site"],
        "blocking_issue_codes": [],
        "missing_evidence_codes": [],
        "evidence_ids": ["evidence:site"],
        "recommended_decision": "STOP_ACCEPT",
        "confidence": 0.9,
    }
    score_rows = []
    parsed_rows = []
    breakdown_rows = []
    turns = []
    for turn_index in turn_indices:
        row_identity = {
            "resume_key": resume_key,
            "case_id": identity["case_id"],
            "pattern": identity["pattern"],
            "repeat": identity["repeat"],
            "turn_index": turn_index,
        }
        parsed_rows.append(
            {
                **row_identity,
                "source": "review_agent",
                "parse_complete": True,
                "parse_error_codes": [],
                "state": copy.deepcopy(state),
            }
        )
        score_rows.append(
            {
                **row_identity,
                "issue_f1": 1.0,
                "evidence_f1": 1.0,
                "domain_coverage": 1.0,
                "verdict_score": 1.0,
                "quality": 1.0,
            }
        )
        breakdown_rows.append(
            {
                **row_identity,
                "subject_stage": "execution",
                "decision_score": 1.0,
                "blocking_issue_f1": 1.0,
                "missing_evidence_f1": 1.0,
            }
        )
        turns.append(
            {
                "index": turn_index,
                "source": "review_agent",
                "content": "fixture",
                "timestamp": "2026-08-19T00:00:00+00:00",
                "tokens_in": 1,
                "tokens_out": 1,
            }
        )
    errors = [
        {
            **identity,
            "resume_key": resume_key,
            "attempt": attempt,
            "error": final_error or "temporary error",
        }
        for attempt in error_attempts
    ]
    result = {
        "experiment_id": "exp08_architecture",
        "task_id": identity["case_id"],
        "pattern": identity["pattern"],
        "repeat_index": identity["repeat"],
        "pattern_category": "flat",
        "agent_count": 3,
        "stop_reason": "TERMINATE" if final_error is None else None,
        "duration_sec": 0.1,
        "total_tokens_in": len(turns),
        "total_tokens_out": len(turns),
        "total_tokens": len(turns) * 2,
        "turn_count": len(turns),
        "agent_turn_count": len(turns),
        "terminated_by": "keyword" if final_error is None else None,
        "turns": turns,
        "error": final_error,
        "quality_score": None,
        "converged_at": None,
        "stage_results": None,
    }
    return resume_key, {
        "schema_version": "ace.iclr2027.run_transaction.v1",
        "resume_identity_sha256": resume_key,
        "raw": {**identity, "resume_key": resume_key, "result": result},
        "parsed": parsed_rows,
        "scores": score_rows,
        "score_breakdowns": breakdown_rows,
        "errors": errors,
        "checkpoint": {"resume_key": resume_key, "status": status},
    }


def _materialize_payload(payload: dict, resume_key: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp)
        transactions = output / "run_transactions"
        transactions.mkdir()
        (transactions / f"{resume_key}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        _materialize_transactions(output)


class TransactionV1Tests(unittest.TestCase):
    def test_executor_persists_only_outer_public_task_identity(self) -> None:
        public_case_id = "case:" + "1" * 64
        internal_case_id = "private-internal-case"
        identity = {
            "case_id": public_case_id,
            "pattern": "rr3",
            "repeat": 0,
            "model": "fixture-model",
            "public_case_sha256": "b" * 64,
            "prompt_sha256": "c" * 64,
            "code_commit": "fixture-commit",
        }
        plan = RunPlan(
            **identity,
            prompt="public prompt",
            resume_key=sha256_json(identity),
        )
        packet = ArchitectureEvidencePacket(
            case_id=internal_case_id,
            pnu="1168011800104170004",
            program="neighborhood",
            condition="native",
            execution_id="execution-1",
            program_hash="a" * 64,
            geometry_hash="b" * 64,
            evidence=({"evidence_id": "evidence:site", "domain": "site"},),
        )
        gold = ArchitectureGoldRecord(
            case_id=public_case_id,
            expected_decision="STOP_ACCEPT",
            blocking_issue_codes=(),
            missing_evidence_codes=(),
            required_evidence_ids=("evidence:site",),
            mutation_family="",
        )
        result = RunResult(
            experiment_id="exp08_architecture",
            task_id=internal_case_id,
            pattern="rr3",
            repeat_index=0,
            pattern_category="flat",
            agent_count=3,
            stop_reason="TERMINATE",
            duration_sec=0.1,
            total_tokens_in=0,
            total_tokens_out=0,
            total_tokens=0,
            turn_count=0,
            agent_turn_count=0,
            terminated_by="keyword",
        )

        async def run_single(**_kwargs: object) -> RunResult:
            return result

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            asyncio.run(
                execute_run_plans(
                    plans=(plan,),
                    packets_by_case={public_case_id: packet},
                    gold_by_case={public_case_id: gold},
                    output_dir=output,
                    team_builder=lambda _pattern, _model, _evidence_ids: object(),
                    run_single=run_single,
                )
            )
            transaction_text = (
                output / "run_transactions" / f"{plan.resume_key}.json"
            ).read_text(encoding="utf-8")
            transaction = json.loads(transaction_text)

        self.assertEqual(transaction["raw"]["result"]["task_id"], public_case_id)
        self.assertNotIn(internal_case_id, transaction_text)

    def test_legacy_unversioned_transaction_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            transactions = output / "run_transactions"
            transactions.mkdir()
            (transactions / ("a" * 64 + ".json")).write_text(
                json.dumps(
                    {
                        "raw": {},
                        "parsed": [],
                        "scores": [],
                        "score_breakdowns": [],
                        "errors": [],
                        "checkpoint": {},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "transaction schema"):
                _materialize_transactions(output)

    def test_v1_transaction_identity_must_match_raw_and_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            transactions = output / "run_transactions"
            transactions.mkdir()
            resume_key = "a" * 64
            payload = {
                "schema_version": "ace.iclr2027.run_transaction.v1",
                "resume_identity_sha256": "b" * 64,
                "raw": {"resume_key": resume_key},
                "parsed": [],
                "scores": [],
                "score_breakdowns": [],
                "errors": [],
                "checkpoint": {"resume_key": resume_key, "status": "completed"},
            }
            (transactions / f"{resume_key}.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "transaction identity"):
                _materialize_transactions(output)

    def test_transaction_identity_is_recomputed_from_raw_plan_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            transactions = output / "run_transactions"
            transactions.mkdir()
            resume_key = "a" * 64
            payload = {
                "schema_version": "ace.iclr2027.run_transaction.v1",
                "resume_identity_sha256": resume_key,
                "raw": {
                    "resume_key": resume_key,
                    "case_id": "case:" + "1" * 64,
                    "pattern": "rr3",
                    "repeat": 0,
                    "model": "fixture",
                    "public_case_sha256": "b" * 64,
                    "prompt_sha256": "c" * 64,
                    "code_commit": "fixture",
                },
                "parsed": [],
                "scores": [],
                "score_breakdowns": [],
                "errors": [],
                "checkpoint": {"resume_key": resume_key, "status": "completed"},
            }
            (transactions / f"{resume_key}.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "canonical transaction identity"):
                _materialize_transactions(output)

    def test_forged_nested_ledger_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            transactions = output / "run_transactions"
            transactions.mkdir()
            identity = {
                "case_id": "case:" + "1" * 64,
                "pattern": "rr3",
                "repeat": 0,
                "model": "fixture-model",
                "public_case_sha256": "b" * 64,
                "prompt_sha256": "c" * 64,
                "code_commit": "fixture-commit",
            }
            resume_key = sha256_json(identity)
            forged = {
                "resume_key": resume_key,
                "case_id": "case:" + "2" * 64,
                "pattern": "rr3",
                "repeat": 0,
                "turn_index": 1,
            }
            payload = {
                "schema_version": "ace.iclr2027.run_transaction.v1",
                "resume_identity_sha256": resume_key,
                "raw": {
                    **identity,
                    "resume_key": resume_key,
                    "result": {
                        "task_id": identity["case_id"],
                        "pattern": "rr3",
                        "repeat_index": 0,
                        "agent_turn_count": 1,
                        "error": None,
                    },
                },
                "parsed": [
                    {
                        **forged,
                        "source": "review_agent",
                        "parse_complete": True,
                        "parse_error_codes": [],
                        "state": {
                            "checked_domains": ["site"],
                            "blocking_issue_codes": [],
                            "missing_evidence_codes": [],
                            "evidence_ids": ["evidence:site"],
                            "recommended_decision": "STOP_ACCEPT",
                            "confidence": 0.9,
                        },
                    }
                ],
                "scores": [
                    {
                        **forged,
                        "issue_f1": 1.0,
                        "evidence_f1": 1.0,
                        "domain_coverage": 1.0,
                        "verdict_score": 1.0,
                        "quality": 1.0,
                    }
                ],
                "score_breakdowns": [
                    {
                        **forged,
                        "subject_stage": "execution",
                        "decision_score": 1.0,
                        "blocking_issue_f1": 1.0,
                        "missing_evidence_f1": 1.0,
                    }
                ],
                "errors": [],
                "checkpoint": {"resume_key": resume_key, "status": "completed"},
            }
            (transactions / f"{resume_key}.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "nested transaction identity"):
                _materialize_transactions(output)

    def test_turn_ledgers_bind_exactly_to_raw_agent_turns(self) -> None:
        resume_key, payload = _valid_transaction(turn_indices=(3, 7))
        mutations = []
        wrong_index = copy.deepcopy(payload)
        for ledger in ("parsed", "scores", "score_breakdowns"):
            wrong_index[ledger][0]["turn_index"] = 4
        mutations.append(wrong_index)
        wrong_order = copy.deepcopy(payload)
        for ledger in ("parsed", "scores", "score_breakdowns"):
            wrong_order[ledger].reverse()
        mutations.append(wrong_order)
        wrong_source = copy.deepcopy(payload)
        wrong_source["parsed"][0]["source"] = "forged_agent"
        mutations.append(wrong_source)

        for forged in mutations:
            with self.subTest(forged=forged["parsed"]), self.assertRaisesRegex(
                ValueError, "raw agent turns"
            ):
                _materialize_payload(forged, resume_key)

    def test_error_attempts_must_be_contiguous_from_one(self) -> None:
        resume_key, payload = _valid_transaction(
            turn_indices=(),
            status="error",
            final_error="terminal failure",
            error_attempts=(2,),
        )

        with self.assertRaisesRegex(ValueError, "contiguous from one"):
            _materialize_payload(payload, resume_key)

    def test_nested_and_raw_repeat_indices_require_native_integers(self) -> None:
        resume_key, payload = _valid_transaction()
        mutations = []
        for ledger in ("parsed", "scores", "score_breakdowns"):
            forged = copy.deepcopy(payload)
            forged[ledger][0]["repeat"] = False
            mutations.append(forged)
        raw_repeat = copy.deepcopy(payload)
        raw_repeat["raw"]["result"]["repeat_index"] = False
        mutations.append(raw_repeat)
        error_key, error_payload = _valid_transaction(
            turn_indices=(),
            status="error",
            final_error="terminal failure",
            error_attempts=(1,),
        )
        error_payload["errors"][0]["repeat"] = False
        mutations.append(error_payload)

        for forged in mutations:
            key = error_key if forged is error_payload else resume_key
            with self.subTest(forged=forged), self.assertRaisesRegex(
                ValueError, "repeat"
            ):
                _materialize_payload(forged, key)

    def test_all_nested_ledgers_bind_to_outer_resume_identity(self) -> None:
        resume_key, payload = _valid_transaction()
        forged_values = {
            "resume_key": "0" * 64,
            "case_id": "case:" + "2" * 64,
            "pattern": "sel3",
            "repeat": 1,
        }
        mutations: list[tuple[str, dict, str]] = []
        for ledger in ("parsed", "scores", "score_breakdowns"):
            for field, forged_value in forged_values.items():
                forged = copy.deepcopy(payload)
                forged[ledger][0][field] = forged_value
                mutations.append((f"{ledger}.{field}", forged, resume_key))
        error_key, error_payload = _valid_transaction(
            turn_indices=(),
            status="error",
            final_error="terminal failure",
            error_attempts=(1,),
        )
        for field, forged_value in forged_values.items():
            forged = copy.deepcopy(error_payload)
            forged["errors"][0][field] = forged_value
            mutations.append((f"errors.{field}", forged, error_key))

        for label, forged, key in mutations:
            with self.subTest(label=label), self.assertRaisesRegex(
                ValueError, "nested transaction identity"
            ):
                _materialize_payload(forged, key)

    def test_persisted_rows_require_exact_schemas_and_strict_types(self) -> None:
        resume_key, payload = _valid_transaction()
        mutations: list[tuple[str, dict, str, str]] = []

        def add(label: str, forged: dict, message: str, key: str = resume_key) -> None:
            mutations.append((label, forged, message, key))

        parsed_extra = copy.deepcopy(payload)
        parsed_extra["parsed"][0]["extra"] = "forged"
        add("parsed exact keys", parsed_extra, "parsed row must contain exact keys")
        parsed_bool = copy.deepcopy(payload)
        parsed_bool["parsed"][0]["parse_complete"] = 1
        add("parsed bool", parsed_bool, "parse_complete must be boolean")
        score_extra = copy.deepcopy(payload)
        score_extra["scores"][0]["extra"] = "forged"
        add("score exact keys", score_extra, "score row must contain exact keys")
        score_bool = copy.deepcopy(payload)
        score_bool["scores"][0]["quality"] = True
        add("score metric", score_bool, "finite within")
        breakdown_extra = copy.deepcopy(payload)
        breakdown_extra["score_breakdowns"][0]["extra"] = "forged"
        add("breakdown exact keys", breakdown_extra, "must contain exact keys")
        breakdown_stage = copy.deepcopy(payload)
        breakdown_stage["score_breakdowns"][0]["subject_stage"] = "forged"
        add("breakdown stage", breakdown_stage, "subject_stage is invalid")
        raw_extra = copy.deepcopy(payload)
        raw_extra["raw"]["extra"] = "forged"
        add("raw exact keys", raw_extra, "raw transaction must contain exact keys")
        checkpoint_extra = copy.deepcopy(payload)
        checkpoint_extra["checkpoint"]["extra"] = "forged"
        add("checkpoint exact keys", checkpoint_extra, "checkpoint must contain exact keys")
        result_extra = copy.deepcopy(payload)
        result_extra["raw"]["result"]["extra"] = "forged"
        add("result exact keys", result_extra, "raw result must contain exact keys")
        turn_extra = copy.deepcopy(payload)
        turn_extra["raw"]["result"]["turns"][0]["extra"] = "forged"
        add("turn exact keys", turn_extra, "raw result turn must contain exact keys")
        error_key, error_payload = _valid_transaction(
            turn_indices=(),
            status="error",
            final_error="terminal failure",
            error_attempts=(1,),
        )
        error_extra = copy.deepcopy(error_payload)
        error_extra["errors"][0]["extra"] = "forged"
        add("error exact keys", error_extra, "error row must contain exact keys", error_key)
        error_bool = copy.deepcopy(error_payload)
        error_bool["errors"][0]["attempt"] = True
        add("error attempt", error_bool, "error attempt is invalid", error_key)

        for label, forged, message, key in mutations:
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, message):
                _materialize_payload(forged, key)

    def test_checkpoint_status_binds_completed_and_error_invariants(self) -> None:
        retry_key, retry_success = _valid_transaction(
            status="completed",
            final_error=None,
            error_attempts=(1,),
        )
        _materialize_payload(retry_success, retry_key)

        mutations: list[tuple[str, dict, str]] = []
        completed_error = copy.deepcopy(retry_success)
        completed_error["raw"]["result"]["error"] = "terminal failure"
        mutations.append(
            ("completed final error", completed_error, "completed transaction")
        )
        error_key, error_payload = _valid_transaction(
            turn_indices=(),
            status="error",
            final_error="terminal failure",
            error_attempts=(1,),
        )
        missing_final = copy.deepcopy(error_payload)
        missing_final["raw"]["result"]["error"] = None
        mutations.append(("missing final error", missing_final, "requires a final error"))
        missing_error_row = copy.deepcopy(error_payload)
        missing_error_row["errors"] = []
        mutations.append(("missing error row", missing_error_row, "bind its final error"))
        mismatched_error = copy.deepcopy(error_payload)
        mismatched_error["errors"][-1]["error"] = "different failure"
        mutations.append(("mismatched final error", mismatched_error, "bind its final error"))

        for label, forged, message in mutations:
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, message):
                _materialize_payload(forged, error_key if label != "completed final error" else retry_key)


if __name__ == "__main__":
    unittest.main()
