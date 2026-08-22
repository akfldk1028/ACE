from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from iclr2027.artifact_receipts import verify_artifact_receipt
from iclr2027.pilot_gate import transaction_set_receipt
from iclr2027 import trajectory_ingest as trajectory_ingest_module
from iclr2027.trajectory_ingest import load_development_snapshot


PROJECT_ROOT = Path(__file__).parents[1]
FREEZE_SCRIPT = PROJECT_ROOT / "freeze_iclr2027_development.py"
V12_RESULTS = (
    PROJECT_ROOT
    / "results"
    / "exp08_architecture"
    / "pilot_full_v12_clean_recovery"
)
EXPECTED_TRANSACTION_SET = (
    "3e7e9c0edd5fc8b1f2cc77f69da6dca9e381018d117a2cf3e8e6a4e94459de74"
)
EXPECTED_RUN_PLAN = (
    "7672205a2cdbf8f5b5c929744e58d31c086e7765cb166a80a9a17f59f458b7c9"
)
EXPECTED_CODE_IDENTITY = (
    "179fe49607a33e2eca5337bb099cde78be96055b-dirty-89d4ae988d18b5c7"
    "-deps-48d730d98a916537"
)


class DevelopmentSnapshotTests(unittest.TestCase):
    def test_snapshot_rejects_hardlinked_manifest_before_reading_outside_inode(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="ace-snapshot-hardlink-") as temporary:
            root = Path(temporary)
            results = root / "results"
            results.mkdir()
            outside = root / "outside-run-manifest.json"
            outside.write_bytes((V12_RESULTS / "run_manifest.json").read_bytes())
            linked = results / "run_manifest.json"
            try:
                os.link(outside, linked)
            except OSError as error:
                self.skipTest(f"hard links unavailable: {error}")
            observed: list[Path] = []
            original_read_text = Path.read_text

            def observe_read(path: Path, *args, **kwargs) -> str:
                if path == linked:
                    observed.append(path)
                return original_read_text(path, *args, **kwargs)

            caught: ValueError | None = None
            with mock.patch.object(Path, "read_text", observe_read):
                try:
                    load_development_snapshot(results, expected_count=450)
                except ValueError as error:
                    caught = error
            if observed or caught is None or "link count" not in str(caught):
                self.fail(
                    "snapshot manifest hardlink must fail before the outside inode read; "
                    f"observed={observed!r}, error={caught!r}"
                )

    def _independent_message_hashes(
        self,
        results: Path,
    ) -> dict[str, list[str]]:
        message_hashes: dict[str, list[str]] = {}
        for transaction_path in sorted((results / "run_transactions").glob("*.json")):
            transaction = json.loads(transaction_path.read_text(encoding="utf-8"))
            ordered_hashes = []
            for turn in transaction["raw"]["result"]["turns"]:
                if turn["source"].lower() == "user":
                    continue
                canonical_message = json.dumps(
                    {
                        field: turn[field]
                        for field in (
                            "index",
                            "source",
                            "content",
                            "tokens_in",
                            "tokens_out",
                        )
                    },
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                ordered_hashes.append(hashlib.sha256(canonical_message).hexdigest())
            message_hashes[transaction_path.stem] = ordered_hashes
        return message_hashes

    def _run_freeze(
        self,
        output: Path,
        *,
        results: Path = V12_RESULTS,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(FREEZE_SCRIPT),
                "--results",
                str(results),
                "--pilot-gate",
                str(results / "pilot_gate.json"),
                "--output",
                str(output),
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_snapshot_requires_exact_450_completed_transactions(self) -> None:
        snapshot = load_development_snapshot(V12_RESULTS, expected_count=450)

        self.assertEqual(len(snapshot.transactions), 450)
        self.assertEqual(snapshot.transaction_set_sha256, EXPECTED_TRANSACTION_SET)
        self.assertEqual(snapshot.run_plan_sha256, EXPECTED_RUN_PLAN)
        self.assertEqual(snapshot.code_runtime_identity, EXPECTED_CODE_IDENTITY)
        self.assertEqual(snapshot.completed_checkpoint_count, 450)
        self.assertEqual(snapshot.final_parse_complete_count, 450)
        self.assertEqual(snapshot.terminal_error_count, 0)
        self.assertEqual(len(snapshot.message_hashes), 450)

    def test_snapshot_rejects_message_or_manifest_tamper(self) -> None:
        for target in ("message", "runtime_identity", "model", "execution_census"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                clone = Path(tmp) / "v12"
                shutil.copytree(V12_RESULTS, clone)
                if target == "message":
                    transaction_path = next(
                        iter(sorted((clone / "run_transactions").glob("*.json")))
                    )
                    payload = json.loads(
                        transaction_path.read_text(encoding="utf-8")
                    )
                    agent_turn = next(
                        turn
                        for turn in payload["raw"]["result"]["turns"]
                        if turn["source"].lower() != "user"
                    )
                    agent_turn["content"] += " tampered"
                    transaction_path.write_text(
                        json.dumps(payload), encoding="utf-8"
                    )
                else:
                    manifest_path = clone / "run_manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    if target == "runtime_identity":
                        manifest["code_commit"] = "tampered-runtime-identity"
                    elif target == "model":
                        manifest["model"] = "different-model"
                    else:
                        manifest["execution"]["completed_runs"] = 449
                        manifest["execution"]["skipped_runs"] = 1
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                with self.assertRaises(ValueError):
                    load_development_snapshot(clone, expected_count=450)

    def test_snapshot_requires_the_full_development_case_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "v12"
            shutil.copytree(V12_RESULTS, clone)
            manifest_path = clone / "run_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["expected_case_count"] = manifest["case_count"] + 1
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "full development case set"):
                load_development_snapshot(clone, expected_count=450)

    def test_exp08_validation_rejects_message_tamper_after_rebinding_outer_hash(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "v12"
            shutil.copytree(V12_RESULTS, clone)
            transaction_path = next(
                iter(sorted((clone / "run_transactions").glob("*.json")))
            )
            transaction = json.loads(transaction_path.read_text(encoding="utf-8"))
            agent_turn = next(
                turn
                for turn in transaction["raw"]["result"]["turns"]
                if turn["source"].lower() != "user"
            )
            agent_turn["source"] = "tampered-agent"
            transaction_path.write_text(json.dumps(transaction), encoding="utf-8")
            rebound_hash, rebound_count = transaction_set_receipt(clone)
            self.assertEqual(rebound_count, 450)

            original_hash = trajectory_ingest_module.EXPECTED_TRANSACTION_SET_SHA256
            try:
                trajectory_ingest_module.EXPECTED_TRANSACTION_SET_SHA256 = rebound_hash
                with self.assertRaisesRegex(
                    ValueError, "turn ledgers do not match raw agent turns"
                ):
                    load_development_snapshot(clone, expected_count=450)
            finally:
                trajectory_ingest_module.EXPECTED_TRANSACTION_SET_SHA256 = original_hash

    def test_plan_identity_validation_rejects_tamper_after_rebinding_raw_hash(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "v12"
            shutil.copytree(V12_RESULTS, clone)
            plan_path = clone / "run_plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan[0]["resume_key"] = plan[1]["resume_key"]
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            rebound_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()

            original_hash = trajectory_ingest_module.EXPECTED_RUN_PLAN_SHA256
            try:
                trajectory_ingest_module.EXPECTED_RUN_PLAN_SHA256 = rebound_hash
                with self.assertRaisesRegex(ValueError, "run plan resume identity"):
                    load_development_snapshot(clone, expected_count=450)
            finally:
                trajectory_ingest_module.EXPECTED_RUN_PLAN_SHA256 = original_hash

    def test_cli_freezes_real_receipt_and_identical_bytes_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "snapshot_receipt.json"

            first = self._run_freeze(output)
            self.assertEqual(first.returncode, 0, first.stderr)
            first_bytes = output.read_bytes()
            receipt = json.loads(first_bytes)
            self.assertEqual(
                receipt["schema_version"],
                "ace.iclr2027.development_snapshot_receipt.v1",
            )
            self.assertEqual(receipt["transaction_count"], 450)
            self.assertEqual(receipt["completed_checkpoint_count"], 450)
            self.assertEqual(receipt["terminal_error_count"], 0)
            self.assertEqual(receipt["final_parse_complete_count"], 450)
            self.assertEqual(receipt["parsed_state_count"], 1524)
            self.assertEqual(receipt["parse_complete_count"], 1481)
            self.assertEqual(receipt["transaction_set_sha256"], EXPECTED_TRANSACTION_SET)
            self.assertEqual(receipt["run_plan_sha256"], EXPECTED_RUN_PLAN)
            self.assertEqual(receipt["code_runtime_identity"], EXPECTED_CODE_IDENTITY)
            verify_artifact_receipt(
                receipt["source_artifact_receipt"], root=V12_RESULTS
            )

            self.assertEqual(
                receipt["message_hashes"],
                self._independent_message_hashes(V12_RESULTS),
            )

            second = self._run_freeze(output)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(output.read_bytes(), first_bytes)

    def test_cli_rejects_nonidentical_output_collision_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "snapshot_receipt.json"
            before = b'{"unrelated":true}\n'
            output.write_bytes(before)

            completed = self._run_freeze(output)

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("output collision", completed.stderr)
            self.assertEqual(output.read_bytes(), before)

    def test_cli_refuses_to_write_inside_source_results_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "v12"
            shutil.copytree(V12_RESULTS, clone)
            output = clone / "forbidden_snapshot_receipt.json"

            completed = self._run_freeze(output, results=clone)

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("outside the source results directory", completed.stderr)
            self.assertFalse(output.exists())

    def test_snapshot_rejects_missing_or_forged_plan_identity(self) -> None:
        for target in ("transaction", "plan_identity"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmp:
                clone = Path(tmp) / "v12"
                shutil.copytree(V12_RESULTS, clone)
                if target == "transaction":
                    next(
                        iter(sorted((clone / "run_transactions").glob("*.json")))
                    ).unlink()
                else:
                    plan_path = clone / "run_plan.json"
                    plan = json.loads(plan_path.read_text(encoding="utf-8"))
                    forged = copy.deepcopy(plan[0])
                    forged["resume_key"] = plan[1]["resume_key"]
                    plan[0] = forged
                    plan_path.write_text(json.dumps(plan), encoding="utf-8")

                with self.assertRaises(ValueError):
                    load_development_snapshot(clone, expected_count=450)


if __name__ == "__main__":
    unittest.main()
