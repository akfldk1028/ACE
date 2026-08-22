from __future__ import annotations

import json
import re
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from iclr2027.exp08 import build_run_plan, render_case_prompt
from iclr2027.schema import ArchitecturePublicCase


SECRET = bytes(range(32))


def _public_case(index: int) -> ArchitecturePublicCase:
    return ArchitecturePublicCase(
        case_id=f"case:{index:064x}",
        site_ref=f"site:{index:064x}",
        program="neighborhood",
        execution_id=f"execution-public-{index}",
        program_hash="a" * 64,
        geometry_hash="b" * 64,
        evidence=({"evidence_id": "evidence:site", "status": "passed"},),
        source_artifact_sha256="c" * 64,
    )


def _complete_pilot_summary(**kwargs):
    from iclr2027.pilot_gate import PilotSummary

    planned = len(kwargs["plans"])
    records = tuple(kwargs["gold_by_case"].values())
    return PilotSummary(
        planned_runs=planned,
        completed_runs=planned,
        parsed_states=planned,
        successful_parses=planned,
        final_runs=planned,
        successful_final_parses=planned,
        correct_final_decisions=planned,
        correct_final_verdicts=planned,
        correct_final_blocking=planned,
        correct_final_missing_evidence=planned,
        protocol_valid_runs=planned,
        run_errors=0,
        safe_cases=sum(row.expected_decision == "STOP_ACCEPT" for row in records),
        unsafe_cases=sum(row.expected_decision == "STOP_REJECT" for row in records),
        continue_cases=sum(row.expected_decision == "CONTINUE" for row in records),
        fault_families=tuple(
            sorted({row.mutation_family for row in records if row.mutation_family})
        ),
        estimated_completion_date=kwargs["estimated_completion_date"],
        estimated_total_cost_usd=kwargs["estimated_total_cost_usd"],
        stage_case_counts={},
    )


class RunnerV2Tests(unittest.TestCase):
    def _paid_runner_fixture(self, root: Path) -> tuple[list[str], Path]:
        from iclr2027.dataset import freeze_site_registry
        from tests.test_iclr2027_freeze_v2 import FreezeV2Tests

        registry, split_manifest, identity = FreezeV2Tests()._build_all(root)
        public_registry = root / "site_registry.public.json"
        receipt = root / "freeze_receipt.json"
        sidecar = root / "projection.private.json"
        sidecar.write_text(
            json.dumps(
                {
                    "schema_version": "ace.iclr2027.projection_identity.private.v1",
                    "secret_hex": SECRET.hex(),
                }
            ),
            encoding="utf-8",
        )
        freeze_site_registry(
            registry,
            split_manifest_path=split_manifest,
            projection_identity=identity,
            public_registry_path=public_registry,
            freeze_receipt_path=receipt,
        )
        output = root / "run"
        return (
            [
                "--split",
                "dev",
                "--patterns",
                "rr3",
                "--repeats",
                "1",
                "--model",
                "fixture-model",
                "--code-commit",
                "fixture-commit",
                "--registry",
                str(registry),
                "--split-manifest",
                str(split_manifest),
                "--projection-identity",
                str(sidecar),
                "--public-registry",
                str(public_registry),
                "--freeze-receipt",
                str(receipt),
                "--checkpoint-dir",
                str(output),
                "--confirm-paid-run",
                "--estimated-cost-per-run-usd",
                "0.25",
                "--estimated-completion-date",
                "2026-09-01",
            ],
            output,
        )

    def test_exact_all_skip_resume_preserves_executed_manifest_provenance(self) -> None:
        from iclr2027.exp08 import ExecutionSummary
        import run_exp08_architecture as runner

        with tempfile.TemporaryDirectory() as tmp:
            args, output = self._paid_runner_fixture(Path(tmp))

            async def first_execution(**kwargs):
                planned = len(kwargs["plans"])
                return ExecutionSummary(
                    completed_runs=planned,
                    skipped_runs=0,
                    error_runs=0,
                    parsed_states=planned * 2,
                    successful_parses=planned * 2,
                )

            with patch.object(
                runner,
                "_bind_runtime_dependencies",
                return_value="fixture-commit-deps-" + "f" * 16,
            ), patch.object(
                runner,
                "execute_run_plans",
                new=first_execution,
            ), patch.object(
                runner,
                "summarize_pilot",
                new=_complete_pilot_summary,
            ):
                self.assertEqual(runner.main(args), 0)

            manifest_path = output / "run_manifest.json"
            manifest_before = manifest_path.read_bytes()
            payload_before = json.loads(manifest_before)
            summary_before = (output / "pilot_summary.json").read_bytes()

            async def all_skipped(**kwargs):
                return ExecutionSummary(
                    completed_runs=0,
                    skipped_runs=len(kwargs["plans"]),
                    error_runs=0,
                    parsed_states=0,
                    successful_parses=0,
                )

            resumed_args = list(args)
            resumed_args[resumed_args.index("0.25")] = "0.50"
            resumed_args[resumed_args.index("2026-09-01")] = "2026-09-02"
            with patch.object(
                runner,
                "_bind_runtime_dependencies",
                return_value="fixture-commit-deps-" + "f" * 16,
            ), patch.object(
                runner,
                "execute_run_plans",
                new=all_skipped,
            ), patch.object(
                runner,
                "summarize_pilot",
                new=_complete_pilot_summary,
            ), patch.object(
                runner,
                "write_json_atomic",
                wraps=runner.write_json_atomic,
            ) as write_spy:
                self.assertEqual(runner.main(resumed_args), 0)

            protected_writes = {
                Path(call.args[0]).name
                for call in write_spy.call_args_list
                if Path(call.args[0]).name
                in {"run_manifest.json", "pilot_summary.json"}
            }
            self.assertEqual(protected_writes, set())
            self.assertEqual(manifest_path.read_bytes(), manifest_before)
            self.assertEqual((output / "pilot_summary.json").read_bytes(), summary_before)
            payload_after = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload_after["execution"], payload_before["execution"])
            self.assertEqual(
                payload_after["estimated_cost_per_run_usd"],
                payload_before["estimated_cost_per_run_usd"],
            )
            self.assertEqual(
                payload_after["estimated_total_cost_usd"],
                payload_before["estimated_total_cost_usd"],
            )
            self.assertEqual(
                payload_after["estimated_completion_date"],
                payload_before["estimated_completion_date"],
            )

    def test_executed_resume_with_new_completion_or_error_fails_without_writes(self) -> None:
        from iclr2027.exp08 import ExecutionSummary
        import run_exp08_architecture as runner

        with tempfile.TemporaryDirectory() as tmp:
            args, output = self._paid_runner_fixture(Path(tmp))

            async def first_execution(**kwargs):
                planned = len(kwargs["plans"])
                return ExecutionSummary(
                    completed_runs=planned,
                    skipped_runs=0,
                    error_runs=0,
                    parsed_states=planned,
                    successful_parses=planned,
                )

            with patch.object(
                runner,
                "_bind_runtime_dependencies",
                return_value="fixture-commit-deps-" + "f" * 16,
            ), patch.object(
                runner,
                "execute_run_plans",
                new=first_execution,
            ), patch.object(
                runner,
                "summarize_pilot",
                new=_complete_pilot_summary,
            ):
                self.assertEqual(runner.main(args), 0)

            manifest_path = output / "run_manifest.json"
            summary_path = output / "pilot_summary.json"
            manifest_before = manifest_path.read_bytes()
            summary_before = summary_path.read_bytes()

            for error_runs in (0, 1):
                with self.subTest(error_runs=error_runs):

                    async def abnormal_execution(**kwargs):
                        planned = len(kwargs["plans"])
                        return ExecutionSummary(
                            completed_runs=1,
                            skipped_runs=planned - 1,
                            error_runs=error_runs,
                            parsed_states=1,
                            successful_parses=int(error_runs == 0),
                        )

                    with patch.object(
                        runner,
                        "_bind_runtime_dependencies",
                        return_value="fixture-commit-deps-" + "f" * 16,
                    ), patch.object(
                        runner,
                        "execute_run_plans",
                        new=abnormal_execution,
                    ), patch.object(
                        runner,
                        "summarize_pilot",
                        new=_complete_pilot_summary,
                    ), patch.object(
                        runner,
                        "write_json_atomic",
                        wraps=runner.write_json_atomic,
                    ) as write_spy:
                        with self.assertRaisesRegex(ValueError, "executed resume"):
                            runner.main(args)

                    protected_writes = {
                        Path(call.args[0]).name
                        for call in write_spy.call_args_list
                        if Path(call.args[0]).name
                        in {"run_manifest.json", "pilot_summary.json"}
                    }
                    self.assertEqual(protected_writes, set())
                    self.assertEqual(manifest_path.read_bytes(), manifest_before)
                    self.assertEqual(summary_path.read_bytes(), summary_before)

    def test_partial_planned_resume_uses_total_summary_execution_counts(self) -> None:
        from iclr2027.exp08 import ExecutionSummary
        import run_exp08_architecture as runner

        with tempfile.TemporaryDirectory() as tmp:
            args, output = self._paid_runner_fixture(Path(tmp))
            dependency_commit = "fixture-commit-deps-" + "f" * 16
            with patch.object(
                runner,
                "_bind_runtime_dependencies",
                return_value=dependency_commit,
            ):
                self.assertEqual(runner.main([*args, "--dry-run"]), 0)

            planned_manifest = json.loads(
                (output / "run_manifest.json").read_text(encoding="utf-8")
            )
            self.assertFalse(planned_manifest["executed"])
            self.assertEqual(planned_manifest["planned_run_count"], 30)
            transactions = output / "run_transactions"
            transactions.mkdir()
            for index in range(10):
                (transactions / f"partial-{index}.json").write_text(
                    "{}", encoding="utf-8"
                )

            async def partial_resume(**kwargs):
                self.assertEqual(len(list(transactions.glob("*.json"))), 10)
                self.assertEqual(len(kwargs["plans"]), 30)
                return ExecutionSummary(
                    completed_runs=20,
                    skipped_runs=10,
                    error_runs=0,
                    parsed_states=40,
                    successful_parses=40,
                )

            def strict_total_summary(**kwargs):
                self.assertEqual(len(list(transactions.glob("*.json"))), 10)
                return replace(
                    _complete_pilot_summary(**kwargs),
                    completed_runs=30,
                    parsed_states=60,
                    successful_parses=59,
                )

            with patch.object(
                runner,
                "_bind_runtime_dependencies",
                return_value=dependency_commit,
            ), patch.object(
                runner,
                "execute_run_plans",
                new=partial_resume,
            ), patch.object(
                runner,
                "summarize_pilot",
                new=strict_total_summary,
            ):
                self.assertEqual(runner.main(args), 0)

            manifest = json.loads(
                (output / "run_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["execution"],
                {
                    "completed_runs": 30,
                    "skipped_runs": 0,
                    "error_runs": 0,
                    "parsed_states": 60,
                    "successful_parses": 59,
                },
            )

    def test_partial_resume_counts_errors_as_processed_total_runs(self) -> None:
        from iclr2027.exp08 import ExecutionSummary
        import run_exp08_architecture as runner

        with tempfile.TemporaryDirectory() as tmp:
            args, output = self._paid_runner_fixture(Path(tmp))
            dependency_commit = "fixture-commit-deps-" + "f" * 16
            with patch.object(
                runner,
                "_bind_runtime_dependencies",
                return_value=dependency_commit,
            ):
                self.assertEqual(runner.main([*args, "--dry-run"]), 0)

            transactions = output / "run_transactions"
            transactions.mkdir()
            for index in range(10):
                (transactions / f"partial-{index}.json").write_text(
                    "{}", encoding="utf-8"
                )

            async def partial_resume(**_kwargs):
                return ExecutionSummary(
                    completed_runs=20,
                    skipped_runs=10,
                    error_runs=2,
                    parsed_states=36,
                    successful_parses=35,
                )

            def strict_total_summary(**kwargs):
                return replace(
                    _complete_pilot_summary(**kwargs),
                    completed_runs=28,
                    run_errors=2,
                    parsed_states=56,
                    successful_parses=55,
                )

            with patch.object(
                runner,
                "_bind_runtime_dependencies",
                return_value=dependency_commit,
            ), patch.object(
                runner,
                "execute_run_plans",
                new=partial_resume,
            ), patch.object(
                runner,
                "summarize_pilot",
                new=strict_total_summary,
            ):
                self.assertEqual(runner.main(args), 0)

            manifest = json.loads(
                (output / "run_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["execution"],
                {
                    "completed_runs": 30,
                    "skipped_runs": 0,
                    "error_runs": 2,
                    "parsed_states": 56,
                    "successful_parses": 55,
                },
            )

    def test_prompt_and_plan_are_built_from_exact_public_schema(self) -> None:
        case = _public_case(1)

        prompt = render_case_prompt(case)
        plans = build_run_plan(
            [case.to_dict()],
            patterns=("rr3",),
            repeats=1,
            model="fixture-model",
            code_commit="fixture-commit",
        )

        self.assertIn(case.site_ref, prompt)
        self.assertNotIn('"condition"', prompt)
        self.assertNotIn('"pnu"', prompt)
        self.assertEqual(plans[0].case_id, case.case_id)
        self.assertIn("public_case_sha256", plans[0].resume_identity)
        self.assertNotIn("packet_sha256", plans[0].resume_identity)
        with self.assertRaisesRegex(ValueError, "public case"):
            build_run_plan(
                [{**case.to_dict(), "condition": "native"}],
                patterns=("rr3",),
                repeats=1,
                model="fixture-model",
                code_commit="fixture-commit",
            )

    def test_unfrozen_dry_run_reads_public_cases_only_and_writes_manifest_v2(self) -> None:
        from iclr2027.io import write_jsonl_atomic
        from run_exp08_architecture import main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = root / "cases"
            output = root / "output"
            write_jsonl_atomic(cases / "dev.native.public.jsonl", [_public_case(1)])
            write_jsonl_atomic(cases / "dev.challenged.public.jsonl", [_public_case(2)])

            result = main(
                [
                    "--split",
                    "dev",
                    "--patterns",
                    "rr3",
                    "--repeats",
                    "1",
                    "--model",
                    "fixture-model",
                    "--code-commit",
                    "fixture-commit",
                    "--cases-dir",
                    str(cases),
                    "--checkpoint-dir",
                    str(output),
                    "--dry-run",
                    "--allow-unfrozen",
                ]
            )

            self.assertEqual(result, 0)
            manifest = json.loads(
                (output / "run_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["schema_version"],
                "ace.iclr2027.exp08_run_manifest.v2",
            )
            self.assertEqual(manifest["input_mode"], "public_fixture")
            self.assertNotIn("gold_source_hashes", manifest)

    def test_v1_run_manifest_cannot_resume_a_v2_plan(self) -> None:
        from run_exp08_architecture import _existing_compatible_manifest

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            proposed = {
                "schema_version": "ace.iclr2027.exp08_run_manifest.v2",
                "split": "dev",
            }
            (output / "run_manifest.json").write_text(
                json.dumps(
                    {
                        **proposed,
                        "schema_version": "ace.iclr2027.exp08_run_manifest.v1",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "run manifest schema"):
                _existing_compatible_manifest(output, proposed)

    def test_frozen_loader_recomputes_private_binding_under_public_ids(self) -> None:
        from iclr2027.dataset import freeze_site_registry
        from run_exp08_architecture import _load_manifest_bound_cases
        from tests.test_iclr2027_freeze_v2 import FreezeV2Tests

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = FreezeV2Tests()
            registry, split_manifest_path, identity = fixture._build_all(root)
            public_registry = root / "site_registry.public.json"
            receipt = root / "freeze_receipt.json"
            freeze_site_registry(
                registry,
                split_manifest_path=split_manifest_path,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
            )
            split_manifest = json.loads(
                split_manifest_path.read_text(encoding="utf-8")
            )

            public, packets, gold, hashes = _load_manifest_bound_cases(
                split_manifest,
                split_manifest_path=split_manifest_path,
                split="dev",
                projection_identity=identity,
            )

            public_ids = {case.case_id for case in public}
            self.assertEqual(public_ids, set(packets))
            self.assertEqual(public_ids, set(gold))
            self.assertTrue(all(packet.case_id not in public_ids for packet in packets.values()))
            self.assertEqual(len(hashes), 6)
            self.assertTrue(
                all(re.fullmatch(r"input:[0-9a-f]{64}", key) for key in hashes)
            )
            rendered_hashes = json.dumps(hashes, sort_keys=True)
            self.assertIsNone(re.search(r"(?<![A-Za-z])native(?![A-Za-z])", rendered_hashes))
            self.assertIsNone(
                re.search(r"(?<![A-Za-z])challenged(?![A-Za-z])", rendered_hashes)
            )

    def test_build_cli_exposes_all_private_freeze_inputs(self) -> None:
        from build_architecture_cases import build_parser

        args = build_parser().parse_args(
            [
                "--split",
                "dev",
                "--projection-identity",
                "secret.json",
                "--public-registry",
                "public.json",
                "--freeze-receipt",
                "receipt.json",
            ]
        )

        self.assertEqual(args.projection_identity, Path("secret.json"))
        self.assertEqual(args.public_registry, Path("public.json"))
        self.assertEqual(args.freeze_receipt, Path("receipt.json"))

    def test_frozen_loader_rechecks_manifest_file_hash_after_verification(self) -> None:
        from run_exp08_architecture import _load_manifest_bound_cases
        from tests.test_iclr2027_freeze_v2 import FreezeV2Tests

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _registry, split_manifest_path, identity = FreezeV2Tests()._build_all(root)
            split_manifest = json.loads(split_manifest_path.read_text(encoding="utf-8"))
            entry = split_manifest["bundles"]["dev.native"]
            manifest_path = (
                split_manifest_path.parent / entry["manifest_path"]
            ).resolve()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            public_path = manifest_path.parent / manifest["files"]["public"]["path"]
            public_path.write_text(
                public_path.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "public file hash"):
                _load_manifest_bound_cases(
                    split_manifest,
                    split_manifest_path=split_manifest_path,
                    split="dev",
                    projection_identity=identity,
                )

    def test_frozen_run_manifest_is_condition_blind_and_preserves_six_hashes(self) -> None:
        from iclr2027.dataset import freeze_site_registry
        from run_exp08_architecture import main
        from tests.test_iclr2027_freeze_v2 import FreezeV2Tests

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = FreezeV2Tests()._build_all(root)
            public_registry = root / "site_registry.public.json"
            receipt = root / "freeze_receipt.json"
            sidecar = root / "projection.private.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "schema_version": "ace.iclr2027.projection_identity.private.v1",
                        "secret_hex": SECRET.hex(),
                    }
                ),
                encoding="utf-8",
            )
            freeze_site_registry(
                registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
            )
            output = root / "run"

            result = main(
                [
                    "--split",
                    "dev",
                    "--patterns",
                    "rr3",
                    "--repeats",
                    "1",
                    "--model",
                    "fixture-model",
                    "--code-commit",
                    "fixture-commit",
                    "--registry",
                    str(registry),
                    "--split-manifest",
                    str(split_manifest),
                    "--projection-identity",
                    str(sidecar),
                    "--public-registry",
                    str(public_registry),
                    "--freeze-receipt",
                    str(receipt),
                    "--checkpoint-dir",
                    str(output),
                    "--dry-run",
                ]
            )

            self.assertEqual(result, 0)
            manifest = json.loads(
                (output / "run_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(manifest["input_hashes"]), 6)
            self.assertTrue(
                all(
                    re.fullmatch(r"input:[0-9a-f]{64}", key)
                    for key in manifest["input_hashes"]
                )
            )
            rendered = json.dumps(manifest, sort_keys=True)
            self.assertIsNone(re.search(r"(?<![A-Za-z])native(?![A-Za-z])", rendered))
            self.assertIsNone(
                re.search(r"(?<![A-Za-z])challenged(?![A-Za-z])", rendered)
            )

    def test_condition_labeled_v2_checkpoint_is_incompatible(self) -> None:
        from run_exp08_architecture import _existing_compatible_manifest

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            proposed = {
                "schema_version": "ace.iclr2027.exp08_run_manifest.v2",
                "input_hashes": {"input:" + "a" * 64: "b" * 64},
            }
            (output / "run_manifest.json").write_text(
                json.dumps(
                    {
                        **proposed,
                        "input_hashes": {"dev.native:public": "b" * 64},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "input_hashes"):
                _existing_compatible_manifest(output, proposed)


if __name__ == "__main__":
    unittest.main()
