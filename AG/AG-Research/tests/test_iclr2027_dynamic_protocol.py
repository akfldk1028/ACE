from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).parents[1]
EXPECTED_COUNTS = {
    "dev.native": 15,
    "dev.challenged": 15,
    "test.native": 15,
    "test.challenged": 15,
}
PATTERNS = ("rr3", "sel3", "swm3", "refl3", "debate3")
STAGE_COUNTS = {
    "execution": 14,
    "selection": 6,
    "materialization": 6,
    "preflight": 4,
}


def _pnu(number: int) -> str:
    return f"11110101001{number:08d}"


def _registry_payload(*, dynamic: bool = True) -> dict:
    payload = {
        "schema_version": "ace.iclr2027.site_registry.v1",
        "version": "dynamic-fixture-v1",
        "frozen": False,
        "split_manifest_sha256": "",
        "sites": [
            {
                "pnu": _pnu(index),
                "split": "dev" if index <= 5 else "test",
                "district_code": "11110",
                "parcel_area_m2": 100.0 + index,
                "area_bin": "small",
                "artifacts": {},
            }
            for index in range(1, 11)
        ],
    }
    if dynamic:
        payload["expected_bundle_counts"] = dict(EXPECTED_COUNTS)
    return payload


class DynamicDatasetProtocolTests(unittest.TestCase):
    def test_registry_counts_are_dynamic_strict_and_site_bound(self) -> None:
        try:
            from iclr2027.dataset import registry_expected_bundle_counts
        except ImportError as exc:
            self.fail(f"dynamic registry count loader is missing: {exc}")

        self.assertEqual(
            registry_expected_bundle_counts(_registry_payload()),
            EXPECTED_COUNTS,
        )
        legacy = _registry_payload(dynamic=False)
        legacy["sites"] = []
        self.assertEqual(
            registry_expected_bundle_counts(legacy),
            {
                "dev.native": 6,
                "dev.challenged": 6,
                "test.native": 15,
                "test.challenged": 15,
            },
        )

        invalid_values = []
        explicit_null = _registry_payload()
        explicit_null["expected_bundle_counts"] = None
        invalid_values.append(("exactly four", explicit_null))
        missing = _registry_payload()
        del missing["expected_bundle_counts"]["dev.native"]
        invalid_values.append(("exactly four", missing))
        extra = _registry_payload()
        extra["expected_bundle_counts"]["extra"] = 1
        invalid_values.append(("exactly four", extra))
        boolean = _registry_payload()
        boolean["expected_bundle_counts"]["dev.native"] = True
        invalid_values.append(("positive integers", boolean))
        floating = _registry_payload()
        floating["expected_bundle_counts"]["dev.native"] = 15.0
        invalid_values.append(("positive integers", floating))
        unequal = _registry_payload()
        unequal["expected_bundle_counts"]["dev.challenged"] = 12
        invalid_values.append(("native and challenged", unequal))
        wrong_site_count = _registry_payload()
        wrong_site_count["expected_bundle_counts"]["dev.native"] = 12
        wrong_site_count["expected_bundle_counts"]["dev.challenged"] = 12
        invalid_values.append(("site count", wrong_site_count))

        for message, payload in invalid_values:
            with self.subTest(message=message), self.assertRaisesRegex(
                ValueError, message
            ):
                registry_expected_bundle_counts(payload)

    def test_dynamic_complete_development_challenge_enforces_seven_execution_bases(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.dataset import CaseBuildResult, _challenge_native_result
        from iclr2027.validators import gold_from_validation

        fixture = (
            Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json"
        )
        execution, _ = packet_from_arr_artifacts(
            fixture,
            pnu="1168011800104170004",
            program="neighborhood",
            case_id="execution-seed-native",
        )
        attempt, _ = packet_from_arr_artifacts(
            PROJECT_ROOT
            / "data"
            / "iclr2027"
            / "arr"
            / "dev-417-law-restored"
            / "maas-book-programs-summary.json",
            pnu="1168011800104170004",
            program="gymnasium",
            case_id="attempt-seed-native",
        )
        packets = []
        for index in range(4):
            payload = execution.to_dict()
            payload["case_id"] = f"execution-{index}-native"
            packets.append(type(execution).from_dict(payload))
        for index in range(11):
            payload = attempt.to_dict()
            payload["case_id"] = f"attempt-{index}-native"
            packets.append(type(attempt).from_dict(payload))
        packet_tuple = tuple(packets)
        native = CaseBuildResult(
            split="dev",
            condition="native",
            registry_version="dynamic-fixture-v1",
            packets=packet_tuple,
            gold_records=tuple(
                gold_from_validation(packet, mutation_family="")
                for packet in packet_tuple
            ),
            expected_bundle_counts=EXPECTED_COUNTS,
        )

        with self.assertRaisesRegex(ValueError, "7 execution packets"):
            _challenge_native_result(native)

        test_result = _challenge_native_result(replace(native, split="test"))
        self.assertEqual(len(test_result.packets), 15)

    def _write_freeze_fixture(self, root: Path, *, dev_count: int):
        from tests.test_iclr2027_freeze_v2 import FreezeV2Tests

        registry, split_manifest, identity = FreezeV2Tests()._build_all(root)
        if dev_count != 15:
            split_payload = json.loads(split_manifest.read_text(encoding="utf-8"))
            for condition in ("native", "challenged"):
                key = f"dev.{condition}"
                entry = split_payload["bundles"][key]
                manifest_path = (split_manifest.parent / entry["manifest_path"]).resolve()
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["case_count"] = dev_count
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                entry["case_count"] = dev_count
                entry["manifest_sha256"] = hashlib.sha256(
                    manifest_path.read_bytes()
                ).hexdigest()
            split_manifest.write_text(json.dumps(split_payload), encoding="utf-8")
        return registry, split_manifest, identity

    def test_amended_freeze_accepts_15_and_rejects_legacy_6_dev_cases(self) -> None:
        from iclr2027.dataset import freeze_site_registry

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = self._write_freeze_fixture(
                root, dev_count=15
            )
            frozen = freeze_site_registry(
                registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=root / "public.json",
                freeze_receipt_path=root / "receipt.json",
            )
            self.assertTrue(frozen["frozen"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = self._write_freeze_fixture(
                root, dev_count=6
            )
            with self.assertRaisesRegex(ValueError, r"case count mismatch: dev\."):
                freeze_site_registry(
                    registry,
                    split_manifest_path=split_manifest,
                    projection_identity=identity,
                    public_registry_path=root / "public.json",
                    freeze_receipt_path=root / "receipt.json",
                )

    def test_freeze_rejects_fractional_manifest_and_split_counts(self) -> None:
        from iclr2027.dataset import freeze_site_registry

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = self._write_freeze_fixture(
                root, dev_count=15
            )
            split_payload = json.loads(split_manifest.read_text(encoding="utf-8"))
            entry = split_payload["bundles"]["dev.native"]
            manifest_path = (
                split_manifest.parent / str(entry["manifest_path"])
            ).resolve()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["case_count"] = 15.9
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            entry["case_count"] = 15.9
            entry["manifest_sha256"] = hashlib.sha256(
                manifest_path.read_bytes()
            ).hexdigest()
            split_manifest.write_text(json.dumps(split_payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "case count must be a positive integer"):
                freeze_site_registry(
                    registry,
                    split_manifest_path=split_manifest,
                    projection_identity=identity,
                    public_registry_path=root / "public.json",
                    freeze_receipt_path=root / "receipt.json",
                )

    def test_build_cli_reads_dynamic_registry_count(self) -> None:
        import build_architecture_cases

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "site_registry.json"
            registry.write_text(json.dumps(_registry_payload()), encoding="utf-8")
            identity = root / "identity.json"
            identity.write_text(
                json.dumps(
                    {
                        "schema_version": "ace.iclr2027.projection_identity.private.v1",
                        "secret_hex": bytes(range(32)).hex(),
                    }
                ),
                encoding="utf-8",
            )
            fake_result = SimpleNamespace(packets=tuple(range(6)))
            with patch.object(
                build_architecture_cases,
                "build_cases",
                return_value=fake_result,
            ), patch.object(
                build_architecture_cases,
                "write_case_bundle",
                side_effect=AssertionError("six cases were incorrectly accepted"),
            ):
                with self.assertRaisesRegex(ValueError, "expected 15 cases"):
                    build_architecture_cases.main(
                        [
                            "--registry",
                            str(registry),
                            "--split",
                            "dev",
                            "--condition",
                            "native",
                            "--output-dir",
                            str(root / "cases"),
                            "--projection-identity",
                            str(identity),
                        ]
                    )


class DynamicPilotProtocolTests(unittest.TestCase):
    @staticmethod
    def _manifest(**changes: object) -> dict:
        manifest = {
            "schema_version": "ace.iclr2027.exp08_run_manifest.v2",
            "input_mode": "frozen_private_binding",
            "split": "dev",
            "patterns": list(PATTERNS),
            "repeats": 3,
            "model": "fixture-model",
            "code_commit": "fixture-commit",
            "expected_case_count": 30,
            "case_count": 30,
            "planned_run_count": 450,
            "stage_case_counts": dict(STAGE_COUNTS),
            "decision_case_counts": {
                "STOP_ACCEPT": 7,
                "STOP_REJECT": 21,
                "CONTINUE": 2,
            },
            "input_hashes": {
                f"input:{index:064x}": f"{index:064x}"
                for index in range(1, 7)
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
        manifest.update(changes)
        return manifest

    @staticmethod
    def _summary():
        from iclr2027.pilot_gate import PilotSummary

        return PilotSummary(
            planned_runs=450,
            completed_runs=450,
            parsed_states=900,
            successful_parses=880,
            final_runs=450,
            successful_final_parses=450,
            correct_final_decisions=450,
            correct_final_verdicts=450,
            correct_final_blocking=450,
            correct_final_missing_evidence=450,
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
            stage_case_counts=dict(STAGE_COUNTS),
        )

    def test_amended_450_plan_passes_without_posthoc_class_rebalancing(self) -> None:
        from iclr2027.pilot_gate import evaluate_pilot

        result = evaluate_pilot(
            self._summary(),
            run_manifest=self._manifest(),
            observed_transaction_set_sha256="d" * 64,
            observed_transaction_count=450,
            deadline=date(2026, 9, 2),
        )

        self.assertTrue(result.passed)
        self.assertTrue(all(result.checks.values()))
        self.assertAlmostEqual(result.safe_share, 7 / 30)
        self.assertAlmostEqual(result.unsafe_share, 21 / 30)
        self.assertAlmostEqual(result.continue_share, 2 / 30)
        self.assertNotIn("safe_share_30_to_70pct", result.checks)
        self.assertNotIn("unsafe_share_30_to_70pct", result.checks)

    def test_legacy_180_or_one_case_smoke_cannot_pass_full_pilot_gate(self) -> None:
        from iclr2027.pilot_gate import evaluate_pilot

        legacy = replace(
            self._summary(),
            planned_runs=180,
            completed_runs=180,
        )
        legacy_result = evaluate_pilot(
            legacy,
            run_manifest=self._manifest(planned_run_count=180),
        )
        self.assertFalse(legacy_result.passed)
        self.assertFalse(legacy_result.checks["pilot_run_composition"])

        smoke_summary = replace(
            self._summary(),
            planned_runs=15,
            completed_runs=15,
            safe_cases=1,
            unsafe_cases=0,
            continue_cases=0,
            stage_case_counts={"execution": 1},
        )
        smoke_result = evaluate_pilot(
            smoke_summary,
            run_manifest=self._manifest(
                case_count=1,
                planned_run_count=15,
                stage_case_counts={"execution": 1},
                decision_case_counts={
                    "STOP_ACCEPT": 1,
                    "STOP_REJECT": 0,
                    "CONTINUE": 0,
                },
            ),
        )
        self.assertFalse(smoke_result.passed)
        self.assertFalse(smoke_result.checks["pilot_full_case_set"])
        self.assertFalse(smoke_result.checks["all_decision_classes_present"])

    def test_missing_stage_report_fails_even_when_run_counts_match(self) -> None:
        from iclr2027.pilot_gate import evaluate_pilot

        result = evaluate_pilot(
            replace(self._summary(), stage_case_counts={}),
            run_manifest=self._manifest(),
        )

        self.assertFalse(result.passed)
        self.assertFalse(result.checks["stage_stratified_reporting"])

    def test_invalid_summary_count_domains_fail_closed(self) -> None:
        from iclr2027.pilot_gate import evaluate_pilot

        invalid = (
            replace(self._summary(), run_errors=-1),
            replace(self._summary(), successful_parses=901),
            replace(self._summary(), completed_runs=450.0),
            replace(self._summary(), run_errors=False),
        )
        for summary in invalid:
            with self.subTest(summary=summary):
                result = evaluate_pilot(summary, run_manifest=self._manifest())
                self.assertFalse(result.passed)
                self.assertFalse(result.checks["pilot_summary_count_domains"])

    def test_summary_loader_does_not_coerce_invalid_domains(self) -> None:
        from iclr2027.pilot_gate import _load_summary, evaluate_pilot

        payload = {
            "planned_runs": 450.0,
            "completed_runs": 450,
            "parsed_states": 900,
            "successful_parses": 880,
            "final_runs": 450,
            "successful_final_parses": 450,
            "correct_final_decisions": 450,
            "correct_final_verdicts": 450,
            "correct_final_blocking": 450,
            "correct_final_missing_evidence": 450,
            "protocol_valid_runs": 450,
            "run_errors": 0,
            "retried_runs": 4,
            "safe_cases": 7,
            "unsafe_cases": 21,
            "continue_cases": 2,
            "fault_families": list(self._summary().fault_families),
            "estimated_completion_date": "2026-09-01",
            "estimated_total_cost_usd": 42.5,
            "schema_version": "ace.iclr2027.pilot_summary.v1",
            "transaction_set_sha256": "d" * 64,
            "stage_case_counts": dict(STAGE_COUNTS),
        }
        invalid = (
            (payload, "pilot_summary_count_domains"),
            (
                {
                    **payload,
                    "planned_runs": 450,
                    "stage_case_counts": list(STAGE_COUNTS.items()),
                },
                "stage_stratified_reporting",
            ),
        )
        for candidate, failed_check in invalid:
            with self.subTest(failed_check=failed_check), tempfile.TemporaryDirectory() as tmp:
                results = Path(tmp)
                (results / "pilot_summary.json").write_text(
                    json.dumps(candidate), encoding="utf-8"
                )
                loaded = _load_summary(results)
                result = evaluate_pilot(loaded, run_manifest=self._manifest())

            self.assertFalse(result.passed)
            self.assertFalse(result.checks[failed_check])

    def test_unknown_stage_names_fail_gate_and_runner_classification(self) -> None:
        from iclr2027.pilot_gate import evaluate_pilot
        from run_exp08_architecture import _stage_case_counts

        result = evaluate_pilot(
            replace(self._summary(), stage_case_counts={"garbage": 30}),
            run_manifest=self._manifest(stage_case_counts={"garbage": 30}),
        )
        self.assertFalse(result.passed)
        self.assertFalse(result.checks["stage_stratified_reporting"])
        with self.assertRaisesRegex(ValueError, "unsupported evidence stage"):
            _stage_case_counts(
                [
                    {
                        "subject_kind": "portfolio_attempt",
                        "attempt_stage": "garbage",
                    }
                ]
            )

    def _write_public_cases(self, cases_dir: Path) -> None:
        from iclr2027.schema import ArchitecturePublicCase

        cases_dir.mkdir()
        cases = [
            ArchitecturePublicCase(
                case_id=f"case:{index + 1:064x}",
                site_ref=f"site:{index + 1:064x}",
                program="neighborhood",
                execution_id=f"execution-{index}",
                program_hash="a" * 64,
                geometry_hash="b" * 64,
                evidence=({"evidence_id": "evidence:geometry_agent"},),
                source_artifact_sha256="c" * 64,
            ).to_dict()
            for index in range(30)
        ]
        for condition, selected in (
            ("native", cases[:15]),
            ("challenged", cases[15:]),
        ):
            (cases_dir / f"dev.{condition}.public.jsonl").write_text(
                "".join(json.dumps(case) + "\n" for case in selected),
                encoding="utf-8",
            )

    def test_runner_manifest_records_full_case_and_stage_composition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases_dir = root / "cases"
            self._write_public_cases(cases_dir)

            def run(output: Path, *extra: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [
                        sys.executable,
                        "run_exp08_architecture.py",
                        "--split",
                        "dev",
                        "--patterns",
                        *PATTERNS,
                        "--repeats",
                        "3",
                        "--model",
                        "test-model",
                        "--code-commit",
                        "abc123",
                        "--cases-dir",
                        str(cases_dir),
                        "--checkpoint-dir",
                        str(output),
                        "--dry-run",
                        "--allow-unfrozen",
                        *extra,
                    ],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )

            full_output = root / "full"
            full = run(full_output)
            self.assertEqual(full.returncode, 0, full.stderr)
            full_manifest = json.loads(
                (full_output / "run_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(full_manifest["expected_case_count"], 30)
            self.assertEqual(full_manifest["case_count"], 30)
            self.assertEqual(full_manifest["planned_run_count"], 450)
            self.assertEqual(full_manifest["stage_case_counts"], {"execution": 30})

            smoke_output = root / "smoke"
            smoke = run(smoke_output, "--limit-cases", "1")
            self.assertEqual(smoke.returncode, 0, smoke.stderr)
            smoke_manifest = json.loads(
                (smoke_output / "run_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(smoke_manifest["expected_case_count"], 30)
            self.assertEqual(smoke_manifest["case_count"], 1)
            self.assertEqual(smoke_manifest["planned_run_count"], 15)


if __name__ == "__main__":
    unittest.main()
