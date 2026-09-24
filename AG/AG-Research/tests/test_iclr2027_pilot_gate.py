from __future__ import annotations

import json
import asyncio
import inspect
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from iclr2027.projection import (
    ProjectionIdentity,
    project_gold_record,
    project_public_case,
)
from iclr2027.schema import ArchitecturePublicCase


def _public_case(index: int) -> ArchitecturePublicCase:
    return ArchitecturePublicCase(
        case_id=f"case:{index + 1:064x}",
        site_ref=f"site:{index + 1:064x}",
        program="neighborhood",
        execution_id=f"execution-{index}",
        program_hash="a" * 64,
        geometry_hash="b" * 64,
        evidence=({"evidence_id": "evidence:geometry_agent"},),
        source_artifact_sha256="c" * 64,
    )


class Exp08PlanningTests(unittest.TestCase):
    def test_frozen_loader_reads_only_manifest_bound_case_files(self) -> None:
        try:
            from run_exp08_architecture import _load_manifest_bound_cases
        except ImportError as exc:
            self.fail(f"manifest-bound loader is missing: {exc}")

        from tests.test_iclr2027_freeze_v2 import FreezeV2Tests

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _registry, split_manifest_path, identity = FreezeV2Tests()._build_all(root)
            split_manifest = json.loads(split_manifest_path.read_text(encoding="utf-8"))
            public, packets, gold, _hashes = _load_manifest_bound_cases(
                split_manifest,
                split_manifest_path=split_manifest_path,
                split="dev",
                projection_identity=identity,
            )
            public_ids = {case.case_id for case in public}
            self.assertEqual(public_ids, set(packets))
            self.assertEqual(public_ids, set(gold))
        return

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases_dir = root / "bound"
            cases_dir.mkdir()
            bundles: dict[str, dict[str, object]] = {}
            for condition in ("native", "challenged"):
                stem = f"dev.{condition}"
                public_path = cases_dir / f"{stem}.public.jsonl"
                gold_path = cases_dir / f"{stem}.gold.jsonl"
                public_path.write_text(
                    json.dumps({"case_id": f"bound-{condition}"}) + "\n",
                    encoding="utf-8",
                )
                gold_path.write_text(
                    json.dumps({"case_id": f"bound-{condition}"}) + "\n",
                    encoding="utf-8",
                )
                manifest_path = cases_dir / f"{stem}.manifest.json"
                manifest_path.write_text(
                    json.dumps(
                        {
                            "files": {
                                "public": {"path": public_path.name},
                                "gold": {"path": gold_path.name},
                            }
                        }
                    ),
                    encoding="utf-8",
                )
                bundles[stem] = {
                    "manifest_path": str(manifest_path.relative_to(root)),
                }
            split_manifest_path = root / "split_manifest.json"
            split_manifest = {"bundles": bundles}

            public, gold, _, _ = _load_manifest_bound_cases(
                split_manifest,
                split_manifest_path=split_manifest_path,
                split="dev",
            )

        self.assertEqual(
            {row["case_id"] for row in public},
            {"bound-native", "bound-challenged"},
        )
        self.assertEqual(
            {row["case_id"] for row in gold},
            {"bound-native", "bound-challenged"},
        )

    def test_default_code_identity_changes_for_uncommitted_source(self) -> None:
        from run_exp08_architecture import _git_code_identity

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=root,
                check=True,
            )
            source = root / "module.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "module.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)

            clean = _git_code_identity(root, root)
            (root / "results").mkdir()
            (root / "results" / "pilot.json").write_text("{}\n", encoding="utf-8")
            after_output = _git_code_identity(root, root)
            source.write_text("VALUE = 2\n", encoding="utf-8")
            dirty = _git_code_identity(root, root)

            self.assertEqual(clean, after_output)
            self.assertNotEqual(clean, dirty)
            self.assertIn("-dirty-", dirty)

    def test_code_identity_binds_external_model_transport_dependencies(self) -> None:
        from run_exp08_architecture import _git_code_identity

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = root / "repository"
            dependency = root / "transport"
            repository.mkdir()
            dependency.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=repository,
                check=True,
            )
            (repository / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "module.py"], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial"], cwd=repository, check=True
            )
            transport = dependency / "client.py"
            transport.write_text("TRANSPORT = 1\n", encoding="utf-8")
            before = _git_code_identity(
                repository,
                repository,
                dependency_roots=(dependency,),
            )
            transport.write_text("TRANSPORT = 2\n", encoding="utf-8")
            after = _git_code_identity(
                repository,
                repository,
                dependency_roots=(dependency,),
            )

        self.assertNotEqual(before, after)

    def test_code_identity_fails_closed_when_dependency_cannot_be_hashed(self) -> None:
        from run_exp08_architecture import _git_code_identity

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            (root / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "module.py"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)

            with self.assertRaisesRegex(RuntimeError, "code identity"):
                _git_code_identity(
                    root,
                    root,
                    dependency_roots=(root / "missing-dependency",),
                )

    def test_dry_run_matrix_has_180_unique_complete_resume_identities(self) -> None:
        try:
            from iclr2027.exp08 import build_run_plan
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"Exp08 planning module is missing: {exc}")

        cases = [_public_case(index).to_dict() for index in range(12)]
        plans = build_run_plan(
            cases,
            patterns=("rr3", "sel3", "swm3", "refl3", "debate3"),
            repeats=3,
            model="test-model",
            code_commit="abc123",
        )

        self.assertEqual(len(plans), 180)
        self.assertEqual(len({plan.resume_key for plan in plans}), 180)
        for plan in plans:
            identity = plan.resume_identity
            self.assertEqual(
                set(identity),
                {
                    "case_id",
                    "pattern",
                    "repeat",
                    "model",
                    "public_case_sha256",
                    "prompt_sha256",
                    "code_commit",
                },
            )
            self.assertNotIn("expected_decision", plan.prompt)
            self.assertNotIn("mutation_family", plan.prompt)
            self.assertNotIn("gold_", plan.prompt.lower())
            self.assertNotIn('"condition":', plan.prompt)
            self.assertNotIn(plan.case_id, plan.prompt)

    def test_runner_cli_dry_run_writes_exact_plan_without_calling_models(self) -> None:
        cases = [_public_case(index).to_dict() for index in range(12)]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases_dir = root / "cases"
            output_dir = root / "pilot"
            cases_dir.mkdir()
            registry = root / "site_registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "ace.iclr2027.site_registry.v1",
                        "version": "unfrozen-test",
                        "frozen": False,
                        "split_manifest_sha256": "",
                        "sites": [],
                    }
                ),
                encoding="utf-8",
            )
            identity_path = root / "identity.json"
            identity_path.write_text(
                json.dumps(
                    {
                        "schema_version": "ace.iclr2027.projection_identity.private.v1",
                        "secret_hex": bytes(range(32)).hex(),
                    }
                ),
                encoding="utf-8",
            )
            for condition, selected in (
                ("native", cases[:6]),
                ("challenged", cases[6:]),
            ):
                (cases_dir / f"dev.{condition}.public.jsonl").write_text(
                    "".join(json.dumps(case) + "\n" for case in selected),
                    encoding="utf-8",
                )
                gold_rows = [
                    {
                        "case_id": case["case_id"],
                        "expected_decision": (
                            "STOP_ACCEPT" if condition == "native" else "STOP_REJECT"
                        ),
                        "blocking_issue_codes": (
                            []
                            if condition == "native"
                            else ["geometry.compilation_failed"]
                        ),
                        "required_evidence_ids": ["evidence:geometry_agent"],
                        "mutation_family": (
                            "" if condition == "native" else "geometry_compile"
                        ),
                    }
                    for case in selected
                ]
                (cases_dir / f"dev.{condition}.gold.jsonl").write_text(
                    "".join(json.dumps(row) + "\n" for row in gold_rows),
                    encoding="utf-8",
                )
            completed = subprocess.run(
                [
                    sys.executable,
                    "run_exp08_architecture.py",
                    "--split",
                    "dev",
                    "--patterns",
                    "rr3",
                    "sel3",
                    "swm3",
                    "refl3",
                    "debate3",
                    "--repeats",
                    "3",
                    "--model",
                    "test-model",
                    "--code-commit",
                    "abc123",
                    "--cases-dir",
                    str(cases_dir),
                    "--checkpoint-dir",
                    str(output_dir),
                    "--dry-run",
                    "--allow-unfrozen",
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("planned_runs=180", completed.stdout)
            manifest = json.loads(
                (output_dir / "run_manifest.json").read_text(encoding="utf-8")
            )
            plans = json.loads(
                (output_dir / "run_plan.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["planned_run_count"], 180)
            self.assertEqual(len(plans), 180)
            self.assertFalse(manifest["executed"])
            self.assertRegex(manifest["code_commit"], r"^abc123-deps-[0-9a-f]{16}$")

            (output_dir / "run_manifest.json").write_text(
                json.dumps({**manifest, "unexpected": 0}),
                encoding="utf-8",
            )
            polluted = subprocess.run(
                [
                    sys.executable,
                    "run_exp08_architecture.py",
                    "--split",
                    "dev",
                    "--patterns",
                    "rr3",
                    "sel3",
                    "swm3",
                    "refl3",
                    "debate3",
                    "--repeats",
                    "3",
                    "--model",
                    "test-model",
                    "--code-commit",
                    "abc123",
                    "--cases-dir",
                    str(cases_dir),
                    "--checkpoint-dir",
                    str(output_dir),
                    "--dry-run",
                    "--allow-unfrozen",
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(polluted.returncode, 0)
            self.assertIn("keys are not exact", polluted.stderr)
            (output_dir / "run_manifest.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )

            incompatible = subprocess.run(
                [
                    sys.executable,
                    "run_exp08_architecture.py",
                    "--split",
                    "dev",
                    "--patterns",
                    "rr3",
                    "sel3",
                    "swm3",
                    "refl3",
                    "debate3",
                    "--repeats",
                    "3",
                    "--model",
                    "different-model",
                    "--code-commit",
                    "abc123",
                    "--cases-dir",
                    str(cases_dir),
                    "--checkpoint-dir",
                    str(output_dir),
                    "--dry-run",
                    "--allow-unfrozen",
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(incompatible.returncode, 0)
            self.assertIn("incompatible run directory", incompatible.stderr)

            blocked = subprocess.run(
                [
                    sys.executable,
                    "run_exp08_architecture.py",
                    "--split",
                    "dev",
                    "--patterns",
                    "rr3",
                    "--repeats",
                    "1",
                    "--model",
                    "test-model",
                    "--code-commit",
                    "abc123",
                    "--cases-dir",
                    str(cases_dir),
                    "--registry",
                    str(registry),
                    "--split-manifest",
                    str(root / "split_manifest.json"),
                    "--projection-identity",
                    str(identity_path),
                    "--checkpoint-dir",
                    str(root / "blocked-pilot"),
                    "--dry-run",
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("site registry is not frozen", blocked.stderr)

    def test_executor_writes_artifacts_once_and_resumes_by_full_key(self) -> None:
        from experiment_utils import RunResult, TurnRecord as LegacyTurnRecord
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.exp08 import (
            build_run_plan,
            execute_run_plans,
            summarize_pilot,
        )
        from iclr2027.validators import gold_from_validation

        fixture = (
            Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json"
        )
        packet, _ = packet_from_arr_artifacts(
            fixture,
            pnu="1168011800104170004",
            program="neighborhood",
            case_id="dev-417-neighborhood-native",
        )
        gold = gold_from_validation(packet, mutation_family="")
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
            "checked_domains": ["site", "geometry", "law", "parking", "program"],
            "blocking_issue_codes": [],
            "missing_evidence_codes": [],
            "evidence_ids": list(gold.required_evidence_ids),
            "recommended_decision": "STOP_ACCEPT",
            "confidence": 0.9,
        }
        fake_result = RunResult(
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
                LegacyTurnRecord(
                    index=0,
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
        calls: list[str] = []

        async def run_single(**kwargs: object) -> RunResult:
            calls.append(str(kwargs["task_id"]))
            return fake_result

        def team_builder(
            pattern: str,
            model: str,
            allowed_evidence_ids: tuple[str, ...],
        ) -> object:
            self.assertTrue(allowed_evidence_ids)
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
            for name, torn_tail in (
                ("raw_trajectories.jsonl", "{torn"),
                ("parsed_turn_states.jsonl", "{torn"),
                ("checkpoint.jsonl", "{torn"),
                ("turn_scores.csv", "torn"),
            ):
                with (output_dir / name).open("a", encoding="utf-8") as handle:
                    handle.write(torn_tail)
            second = asyncio.run(execute_run_plans(**kwargs))
            (output_dir / "checkpoint.jsonl").unlink()
            third = asyncio.run(execute_run_plans(**kwargs))
            fourth = asyncio.run(execute_run_plans(**kwargs))

            self.assertEqual(first.completed_runs, 1)
            self.assertEqual(second.completed_runs, 0)
            self.assertEqual(second.skipped_runs, 1)
            self.assertEqual(third.completed_runs, 0)
            self.assertEqual(third.skipped_runs, 1)
            self.assertEqual(fourth.completed_runs, 0)
            self.assertEqual(fourth.skipped_runs, 1)
            self.assertEqual(calls, [public_case.case_id])
            self.assertEqual(
                len((output_dir / "raw_trajectories.jsonl").read_text().splitlines()),
                1,
            )
            self.assertEqual(
                len((output_dir / "parsed_turn_states.jsonl").read_text().splitlines()),
                1,
            )
            self.assertEqual(
                len((output_dir / "checkpoint.jsonl").read_text().splitlines()),
                1,
            )
            self.assertEqual(
                len((output_dir / "turn_scores.csv").read_text().splitlines()),
                2,
            )
            summary = summarize_pilot(
                output_dir=output_dir,
                plans=plans,
                packets_by_case={public_case.case_id: packet},
                gold_by_case={public_case.case_id: public_gold},
                estimated_completion_date=date(2026, 8, 20),
                estimated_total_cost_usd=2.5,
            )
            self.assertEqual(summary.planned_runs, 1)
            self.assertEqual(summary.completed_runs, 1)
            self.assertEqual(summary.parsed_states, 1)
            self.assertEqual(summary.successful_parses, 1)
            self.assertEqual(summary.final_runs, 1)
            self.assertEqual(summary.successful_final_parses, 1)
            self.assertEqual(summary.correct_final_decisions, 1)
            self.assertEqual(summary.correct_final_verdicts, 1)
            self.assertEqual(summary.correct_final_blocking, 1)
            self.assertEqual(summary.correct_final_missing_evidence, 1)
            self.assertEqual(summary.protocol_valid_runs, 0)
            self.assertEqual(summary.safe_cases, 1)
            self.assertEqual(summary.unsafe_cases, 0)
            self.assertEqual(summary.estimated_total_cost_usd, 2.5)

            transaction_path = next((output_dir / "run_transactions").glob("*.json"))
            original_transaction = transaction_path.read_bytes()
            transaction_path.unlink()
            with self.assertRaisesRegex(ValueError, "missing final-run key"):
                summarize_pilot(
                    output_dir=output_dir,
                    plans=plans,
                    packets_by_case={public_case.case_id: packet},
                    gold_by_case={public_case.case_id: public_gold},
                    estimated_completion_date=date(2026, 8, 20),
                    estimated_total_cost_usd=2.5,
                )
            transaction_path.write_bytes(original_transaction)
            transaction = json.loads(transaction_path.read_text(encoding="utf-8"))
            transaction["raw"]["result"]["turns"][-1]["content"] = transaction["raw"][
                "result"
            ]["turns"][-1]["content"].replace(
                '"recommended_decision": "STOP_ACCEPT"',
                '"recommended_decision": "STOP_REJECT"',
            )
            transaction_path.write_text(json.dumps(transaction), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "semantic mismatch"):
                summarize_pilot(
                    output_dir=output_dir,
                    plans=plans,
                    packets_by_case={public_case.case_id: packet},
                    gold_by_case={public_case.case_id: public_gold},
                    estimated_completion_date=date(2026, 8, 20),
                    estimated_total_cost_usd=2.5,
                )

    def test_executor_retries_a_transient_model_error(self) -> None:
        from dataclasses import replace

        from experiment_utils import RunResult
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.exp08 import build_run_plan, execute_run_plans
        from iclr2027.validators import gold_from_validation

        fixture = (
            Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json"
        )
        packet, _ = packet_from_arr_artifacts(
            fixture,
            pnu="1168011800104170004",
            program="neighborhood",
            case_id="dev-417-neighborhood-native",
        )
        gold = gold_from_validation(packet, mutation_family="")
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
        success = RunResult(
            experiment_id="exp08",
            task_id=packet.case_id,
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
        results = [replace(success, error="temporary failure"), success]
        calls = 0

        async def run_single(**_: object) -> RunResult:
            nonlocal calls
            calls += 1
            return results.pop(0)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            execution = asyncio.run(
                execute_run_plans(
                    plans=plans,
                    packets_by_case={public_case.case_id: packet},
                    gold_by_case={public_case.case_id: public_gold},
                    output_dir=output_dir,
                    team_builder=lambda _pattern, _model, _evidence_ids: object(),
                    run_single=run_single,
                    max_attempts=2,
                )
            )

            errors = [
                json.loads(line)
                for line in (output_dir / "errors_retries.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]

        self.assertEqual(calls, 2)
        self.assertEqual(execution.completed_runs, 1)
        self.assertEqual(execution.error_runs, 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["attempt"], 1)


class PilotGateSecureInputTests(unittest.TestCase):
    @staticmethod
    def _create_directory_link(link: Path, target: Path) -> None:
        if os.name == "nt":
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                check=False,
                capture_output=True,
                text=True,
            )
            if created.returncode != 0:
                raise unittest.SkipTest(
                    f"junction creation unavailable: {created.stdout}{created.stderr}"
                )
        else:
            link.symlink_to(target, target_is_directory=True)

    @staticmethod
    def _remove_directory_link(link: Path) -> None:
        if not os.path.lexists(link):
            return
        if os.name == "nt":
            link.rmdir()
        else:
            link.unlink()

    def test_summary_and_run_manifest_hardlinks_reject_before_observer_or_parser(
        self,
    ) -> None:
        from iclr2027 import pilot_gate

        for filename, loader in (
            ("pilot_summary.json", pilot_gate._load_summary),
            ("run_manifest.json", pilot_gate._load_run_manifest),
        ):
            with (
                self.subTest(filename=filename),
                tempfile.TemporaryDirectory(
                    prefix="ace-pilot-input-hardlink-"
                ) as temporary,
            ):
                root = Path(temporary)
                outside = root / f"outside-{filename}"
                outside.write_bytes(
                    f"outside-{filename}-bytes-must-not-be-parsed".encode("utf-8")
                )
                linked = root / filename
                try:
                    os.link(outside, linked)
                except OSError as error:
                    self.skipTest(f"hard links unavailable: {error}")
                observed_reads: list[Path] = []
                observed_parses: list[object] = []
                original_read_text = Path.read_text
                original_loads = json.loads

                def observe_read(path: Path, *args, **kwargs) -> str:
                    if path == linked:
                        observed_reads.append(path)
                    return original_read_text(path, *args, **kwargs)

                def observe_parse(value: object, *args, **kwargs):
                    observed_parses.append(value)
                    return original_loads(value, *args, **kwargs)

                caught: ValueError | None = None
                with (
                    mock.patch.object(Path, "read_text", observe_read),
                    mock.patch(
                        "iclr2027.pilot_gate.json.loads",
                        side_effect=observe_parse,
                    ),
                ):
                    try:
                        loader(root)
                    except ValueError as error:
                        caught = error
                if (
                    observed_reads
                    or observed_parses
                    or caught is None
                    or "link count" not in str(caught)
                ):
                    self.fail(
                        f"{filename} hardlink must reject before observer/parser; "
                        f"reads={observed_reads!r}, parses={observed_parses!r}, "
                        f"error={caught!r}"
                    )

    def test_transaction_enumeration_authenticates_root_before_outside_names(
        self,
    ) -> None:
        from iclr2027 import exp08, pilot_gate

        for label, module, loader in (
            ("exp08", exp08, exp08.load_validated_transactions),
            ("pilot", pilot_gate, pilot_gate.transaction_set_receipt),
        ):
            with (
                self.subTest(label=label),
                tempfile.TemporaryDirectory(
                    prefix="ace-transaction-junction-"
                ) as temporary,
            ):
                base = Path(temporary)
                results = base / "results"
                results.mkdir()
                outside = base / "outside-transactions"
                outside.mkdir()
                outside_name = "outside-name-must-not-be-observed.json"
                (outside / outside_name).write_bytes(b"outside transaction bytes")
                transaction_link = results / "run_transactions"
                self._create_directory_link(transaction_link, outside)
                observed_names: list[str] = []
                original_glob = Path.glob
                real_tree = module.AuthenticatedTree
                supports_name_observer = (
                    "name_observer" in inspect.signature(real_tree).parameters
                )

                def observe_glob(path: Path, pattern: str):
                    values = tuple(original_glob(path, pattern))
                    if path == transaction_link:
                        observed_names.extend(value.name for value in values)
                    return iter(values)

                def observed_tree(*args, **kwargs):
                    if supports_name_observer:
                        kwargs["name_observer"] = (
                            lambda _directory, name: observed_names.append(name)
                        )
                    return real_tree(*args, **kwargs)

                caught: ValueError | None = None
                try:
                    with (
                        mock.patch.object(Path, "glob", observe_glob),
                        mock.patch.object(
                            module,
                            "AuthenticatedTree",
                            side_effect=observed_tree,
                        ),
                    ):
                        try:
                            loader(results)
                        except ValueError as error:
                            caught = error
                finally:
                    self._remove_directory_link(transaction_link)
                if (
                    observed_names
                    or caught is None
                    or not any(
                        marker in str(caught)
                        for marker in ("reparse", "symlink", "authenticated")
                    )
                ):
                    self.fail(
                        f"{label} must authenticate before transaction names; "
                        f"observed_names={observed_names!r}, error={caught!r}"
                    )


class PilotGateTests(unittest.TestCase):
    def test_gate_passes_only_when_all_spending_preconditions_hold(self) -> None:
        try:
            from iclr2027.pilot_gate import PilotSummary, evaluate_pilot
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"pilot gate module is missing: {exc}")

        summary = PilotSummary(
            planned_runs=450,
            completed_runs=450,
            parsed_states=900,
            successful_parses=880,
            final_runs=450,
            successful_final_parses=450,
            correct_final_decisions=440,
            correct_final_verdicts=435,
            correct_final_blocking=440,
            correct_final_missing_evidence=440,
            protocol_valid_runs=450,
            run_errors=0,
            retried_runs=4,
            safe_cases=7,
            unsafe_cases=21,
            continue_cases=2,
            fault_families=(
                "identity_hash",
                "law_projection",
                "parking_shortage",
                "program_capacity",
                "geometry_compile",
            ),
            estimated_completion_date=date(2026, 9, 1),
            estimated_total_cost_usd=42.5,
            transaction_set_sha256="d" * 64,
            stage_case_counts={
                "execution": 14,
                "selection": 6,
                "materialization": 6,
                "preflight": 4,
            },
        )
        run_manifest = {
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
            "stage_case_counts": dict(summary.stage_case_counts),
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
                "parsed_states": 900,
                "successful_parses": 880,
            },
            "estimated_cost_per_run_usd": 42.5 / 450,
            "estimated_total_cost_usd": 42.5,
            "estimated_completion_date": "2026-09-01",
        }

        result = evaluate_pilot(
            summary,
            run_manifest=run_manifest,
            observed_transaction_set_sha256="d" * 64,
            observed_transaction_count=450,
            deadline=date(2026, 9, 2),
        )

        self.assertTrue(result.passed)
        self.assertTrue(all(result.checks.values()))
        self.assertAlmostEqual(result.parse_success_rate, 880 / 900)
        self.assertAlmostEqual(result.final_decision_accuracy, 440 / 450)
        self.assertAlmostEqual(result.final_verdict_accuracy, 435 / 450)
        self.assertEqual(result.run_error_rate, 0.0)
        self.assertAlmostEqual(result.retry_rate, 4 / 450)
        self.assertEqual(result.estimated_total_cost_usd, 42.5)

        failed = evaluate_pilot(
            PilotSummary(
                **{
                    **summary.__dict__,
                    "successful_parses": 854,
                    "estimated_total_cost_usd": None,
                }
            ),
            run_manifest=run_manifest,
            observed_transaction_set_sha256="d" * 64,
            observed_transaction_count=450,
            deadline=date(2026, 9, 2),
        )
        self.assertFalse(failed.passed)
        self.assertFalse(failed.checks["parse_success_at_least_95pct"])
        self.assertFalse(failed.checks["cost_estimate_present"])

        final_failure = evaluate_pilot(
            PilotSummary(
                **{
                    **summary.__dict__,
                    "successful_final_parses": 449,
                    "correct_final_decisions": 426,
                    "correct_final_verdicts": 426,
                    "correct_final_blocking": 426,
                    "correct_final_missing_evidence": 426,
                    "protocol_valid_runs": 449,
                }
            ),
            run_manifest=run_manifest,
            observed_transaction_set_sha256="d" * 64,
            observed_transaction_count=450,
            deadline=date(2026, 9, 2),
        )
        self.assertFalse(final_failure.passed)
        self.assertFalse(final_failure.checks["all_final_states_parse_complete"])
        self.assertFalse(final_failure.checks["all_runs_protocol_valid"])
        self.assertFalse(final_failure.checks["final_decision_at_least_95pct"])
        self.assertFalse(final_failure.checks["final_verdict_at_least_95pct"])
        self.assertFalse(final_failure.checks["final_blocking_at_least_95pct"])
        self.assertFalse(final_failure.checks["final_missing_evidence_at_least_95pct"])

        seven_case_summary = PilotSummary(
            **{
                **summary.__dict__,
                "planned_runs": 105,
                "completed_runs": 105,
                "parsed_states": 210,
                "successful_parses": 210,
                "final_runs": 105,
                "successful_final_parses": 105,
                "correct_final_decisions": 105,
                "correct_final_verdicts": 105,
                "correct_final_blocking": 105,
                "correct_final_missing_evidence": 105,
                "protocol_valid_runs": 105,
                "run_errors": 0,
                "safe_cases": 2,
                "unsafe_cases": 4,
                "continue_cases": 1,
                "stage_case_counts": {"execution": 7},
            }
        )
        seven_case_manifest = {
            **run_manifest,
            "expected_case_count": 7,
            "case_count": 7,
            "planned_run_count": 105,
            "stage_case_counts": {"execution": 7},
            "decision_case_counts": {
                "STOP_ACCEPT": 2,
                "STOP_REJECT": 4,
                "CONTINUE": 1,
            },
        }
        seven_case_result = evaluate_pilot(
            seven_case_summary,
            run_manifest=seven_case_manifest,
            observed_transaction_set_sha256="d" * 64,
            observed_transaction_count=105,
            deadline=date(2026, 9, 2),
        )
        self.assertFalse(seven_case_result.passed)
        self.assertFalse(seven_case_result.checks["pilot_full_case_set"])

        stale_summary = evaluate_pilot(
            summary,
            run_manifest=run_manifest,
            observed_transaction_set_sha256="e" * 64,
            observed_transaction_count=450,
            deadline=date(2026, 9, 2),
        )
        self.assertFalse(stale_summary.passed)
        self.assertFalse(stale_summary.checks["transaction_set_bound"])


if __name__ == "__main__":
    unittest.main()
