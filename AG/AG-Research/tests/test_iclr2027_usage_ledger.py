from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest


class UsageLedgerTests(unittest.TestCase):
    def test_non_null_duration_and_cost_must_be_finite_and_nonnegative(self) -> None:
        from dataclasses import replace

        from iclr2027.usage_ledger import UsageEvent, build_usage_ledger

        event = build_usage_ledger(
            (self._transaction(),),
            trajectory_ids={"a" * 64: "trajectory:" + "b" * 64},
        ).events[0]
        self.assertIsInstance(event, UsageEvent)
        for field, value in (
            ("duration_sec", -0.1),
            ("duration_sec", math.inf),
            ("duration_sec", math.nan),
            ("cost_usd", -0.01),
            ("cost_usd", math.inf),
            ("cost_usd", math.nan),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaisesRegex(ValueError, field.replace("_", " ")):
                    replace(event, **{field: value})

    def test_usage_events_are_canonically_sorted_and_duplicate_rejected(self) -> None:
        from copy import deepcopy

        from iclr2027.usage_ledger import build_usage_ledger

        first = self._transaction()
        second = deepcopy(first)
        second["resume_identity_sha256"] = "b" * 64
        ledger = build_usage_ledger(
            (second, first),
            trajectory_ids={
                "a" * 64: "trajectory:" + "a" * 64,
                "b" * 64: "trajectory:" + "b" * 64,
            },
        )
        self.assertEqual(
            [event.trajectory_id for event in ledger.events[:5]],
            ["trajectory:" + "a" * 64] * 5,
        )
        with self.assertRaisesRegex(ValueError, "duplicate usage event"):
            build_usage_ledger(
                (first, deepcopy(first)),
                trajectory_ids={"a" * 64: "trajectory:" + "a" * 64},
            )
    @staticmethod
    def _transaction() -> dict[str, object]:
        return {
            "resume_identity_sha256": "a" * 64,
            "raw": {
                "model": "visible-agent-model",
                "result": {
                    "turns": [
                        {
                            "index": 1,
                            "source": "site_agent",
                            "tokens_in": 11,
                            "tokens_out": 7,
                        },
                        {
                            "index": 2,
                            "source": "law_agent",
                            "tokens_in": 13,
                            "tokens_out": 5,
                        },
                    ]
                },
            },
            "errors": [{"attempt": 1, "error": "temporary provider failure"}],
        }

    def test_emits_successful_failed_and_unavailable_event_kinds(self) -> None:
        from iclr2027.usage_ledger import build_usage_ledger

        ledger = build_usage_ledger(
            (self._transaction(),),
            trajectory_ids={"a" * 64: "trajectory:" + "b" * 64},
        )

        self.assertEqual(
            [(event.event_kind, event.attempt_status) for event in ledger.events],
            [
                ("agent_inference", "successful"),
                ("agent_inference", "successful"),
                ("retry_attempt", "failed"),
                ("selector_inference", "unavailable"),
                ("deterministic_control", "unavailable"),
            ],
        )
        self.assertIsNone(ledger.events[0].cached_tokens)
        self.assertIsNone(ledger.events[0].cost_usd)
        self.assertEqual(
            ledger.events[3].unavailable_reason, "selector_usage_unavailable"
        )

    def test_retry_events_preserve_attempt_lineage(self) -> None:
        from iclr2027.usage_ledger import build_usage_ledger

        ledger = build_usage_ledger(
            (self._transaction(),),
            trajectory_ids={"a" * 64: "trajectory:" + "b" * 64},
        )

        retry = next(event for event in ledger.events if event.event_kind == "retry_attempt")
        self.assertEqual(retry.trajectory_id, "trajectory:" + "b" * 64)
        self.assertEqual(retry.control_index, 1)
        self.assertEqual(retry.retry_attempt, 1)
        self.assertEqual(retry.attempt_status, "failed")
        self.assertEqual(retry.unavailable_reason, "retry_usage_unavailable")

    def test_indexes_cumulative_visible_agent_tokens_by_trajectory_and_turn(self) -> None:
        from iclr2027.usage_ledger import build_usage_ledger

        ledger = build_usage_ledger(
            (self._transaction(),),
            trajectory_ids={"a" * 64: "trajectory:" + "b" * 64},
        )

        self.assertEqual(
            ledger.cumulative_visible_agent_tokens,
            {
                ("trajectory:" + "b" * 64, 1): 18,
                ("trajectory:" + "b" * 64, 2): 36,
            },
        )
        agent_events = [event for event in ledger.events if event.event_kind == "agent_inference"]
        self.assertEqual(
            [event.cumulative_visible_agent_tokens for event in agent_events], [18, 36]
        )

    def test_missing_selector_and_control_usage_blocks_cost_claims(self) -> None:
        from iclr2027.usage_ledger import summarize_usage

        availability = summarize_usage((self._transaction(),))

        self.assertTrue(availability.visible_agent_tokens)
        self.assertFalse(availability.invoice_grade_cost)
        self.assertFalse(availability.total_compute)
        self.assertIn("selector_usage_unavailable", availability.reasons)
        self.assertIn("deterministic_control_usage_unavailable", availability.reasons)
        self.assertIn("provider_usage_unavailable", availability.reasons)
        self.assertIn("cached_token_usage_unavailable", availability.reasons)
        self.assertIn("cost_usage_unavailable", availability.reasons)
        self.assertIn("duration_usage_unavailable", availability.reasons)
        self.assertIn("retry_usage_unavailable", availability.reasons)

    def test_dataset_builder_receipts_usage_without_changing_claim_boundary(self) -> None:
        from build_exp09_dataset import build_dataset
        from iclr2027.study_contract import StudyContract

        root = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "dataset"
            build_dataset(
                snapshot=root
                / "results"
                / "exp09_cats"
                / "development_snapshot"
                / "snapshot_receipt.json",
                results=root
                / "results"
                / "exp08_architecture"
                / "pilot_full_v12_clean_recovery",
                split_manifest=root / "data" / "iclr2027" / "split_manifest.json",
                projection_identity=root
                / "data"
                / "iclr2027"
                / "projection_identity.private.json",
                epsilon=0.02,
                output=output,
                method_lock=StudyContract.primary(),
            )

            events_path = output / "usage" / "usage_events.jsonl"
            availability_path = output / "usage" / "claim_availability.json"
            events = [
                json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()
            ]
            availability = json.loads(availability_path.read_text(encoding="utf-8"))

            self.assertEqual(
                availability["usage_events_sha256"],
                hashlib.sha256(events_path.read_bytes()).hexdigest(),
            )
            self.assertTrue(availability["visible_agent_tokens"])
            self.assertFalse(availability["invoice_grade_cost"])
            self.assertFalse(availability["total_compute"])
            self.assertEqual(availability["event_counts"]["agent_inference.successful"], 1524)
            self.assertEqual(availability["event_counts"]["retry_attempt.failed"], 138)
            self.assertEqual(availability["event_counts"]["selector_inference.unavailable"], 450)
            self.assertEqual(
                availability["event_counts"]["deterministic_control.unavailable"], 450
            )
            self.assertEqual(
                sum(
                    event["cumulative_visible_agent_tokens"] is not None
                    for event in events
                ),
                1524,
            )


if __name__ == "__main__":
    unittest.main()
