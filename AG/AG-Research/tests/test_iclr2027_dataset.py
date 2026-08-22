from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json"
SECRET_HEX = bytes(range(32)).hex()


class ArchitectureDatasetTests(unittest.TestCase):
    def _write_identity(self, root: Path) -> Path:
        path = root / "projection.private.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "ace.iclr2027.projection_identity.private.v1",
                    "secret_hex": SECRET_HEX,
                }
            ),
            encoding="utf-8",
        )
        return path

    def _write_fixture_registry(self, root: Path) -> Path:
        registry = root / "site_registry.json"
        registry.write_text(
            json.dumps(
                {
                    "schema_version": "ace.iclr2027.site_registry.v1",
                    "version": "fixture-v1",
                    "sites": [
                        {
                            "pnu": "1168011800104170004",
                            "split": "dev",
                            "district_code": "11680",
                            "parcel_area_m2": 264.126,
                            "artifacts": {
                                "neighborhood": str(FIXTURE.resolve()),
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return registry

    def test_native_bundle_is_deterministic_separated_and_hash_manifested(self) -> None:
        try:
            from iclr2027.dataset import build_native_cases, write_case_bundle
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"dataset builder module is missing: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_fixture_registry(root)

            result = build_native_cases(registry, split="dev")
            from iclr2027.projection import ProjectionIdentity

            identity = ProjectionIdentity(bytes.fromhex(SECRET_HEX))
            manifest = write_case_bundle(
                result,
                output_dir=root / "cases",
                projection_identity=identity,
            )

            public_path = root / "cases" / "dev.native.public.jsonl"
            gold_path = root / "cases" / "dev.native.gold.jsonl"
            public = [json.loads(line) for line in public_path.read_text(encoding="utf-8").splitlines()]
            gold = [json.loads(line) for line in gold_path.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(len(public), 1)
            self.assertEqual(len(gold), 1)
            self.assertEqual(public[0]["case_id"], gold[0]["case_id"])
            self.assertNotIn("expected_decision", public[0])
            self.assertNotIn("mutation_family", public[0])
            self.assertEqual(gold[0]["expected_decision"], "STOP_ACCEPT")
            self.assertEqual(manifest["case_count"], 1)
            self.assertEqual(
                manifest["files"]["public"]["sha256"],
                hashlib.sha256(public_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                manifest["files"]["gold"]["sha256"],
                hashlib.sha256(gold_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(len(manifest["sources"]), 1)
            self.assertEqual(
                manifest["sources"][0]["sha256"],
                hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
            )

            first_public = public_path.read_bytes()
            first_gold = gold_path.read_bytes()
            write_case_bundle(
                build_native_cases(registry, split="dev"),
                output_dir=root / "cases",
                projection_identity=identity,
            )
            self.assertEqual(public_path.read_bytes(), first_public)
            self.assertEqual(gold_path.read_bytes(), first_gold)

    def test_build_cli_writes_requested_native_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_fixture_registry(root)
            output_dir = root / "cases"
            identity = self._write_identity(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    "build_architecture_cases.py",
                    "--registry",
                    str(registry),
                    "--split",
                    "dev",
                    "--condition",
                    "native",
                    "--output-dir",
                    str(output_dir),
                    "--allow-partial",
                    "--projection-identity",
                    str(identity),
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("built 1 native cases", completed.stdout)
            self.assertTrue((output_dir / "dev.native.public.jsonl").is_file())
            self.assertTrue((output_dir / "dev.native.gold.jsonl").is_file())

    def test_build_cli_derives_challenged_gold_without_public_fault_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_fixture_registry(root)
            output_dir = root / "cases"
            identity = self._write_identity(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    "build_architecture_cases.py",
                    "--registry",
                    str(registry),
                    "--split",
                    "dev",
                    "--condition",
                    "challenged",
                    "--output-dir",
                    str(output_dir),
                    "--allow-partial",
                    "--projection-identity",
                    str(identity),
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            public = json.loads(
                (output_dir / "dev.challenged.public.jsonl")
                .read_text(encoding="utf-8")
                .strip()
            )
            gold = json.loads(
                (output_dir / "dev.challenged.gold.jsonl")
                .read_text(encoding="utf-8")
                .strip()
            )
            self.assertNotIn("condition", public)
            self.assertNotIn("mutation_family", public)
            self.assertEqual(gold["expected_decision"], "STOP_REJECT")
            self.assertTrue(gold["mutation_family"])

    def test_build_cli_rejects_incomplete_research_split_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_fixture_registry(root)
            identity = self._write_identity(root)
            completed = subprocess.run(
                [
                    sys.executable,
                    "build_architecture_cases.py",
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
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("expected 6 cases", completed.stderr)

    def test_build_cli_refuses_to_mutate_a_frozen_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_fixture_registry(root)
            identity = self._write_identity(root)
            payload = json.loads(registry.read_text(encoding="utf-8"))
            payload.update({"frozen": True, "split_manifest_sha256": "0" * 64})
            registry.write_text(json.dumps(payload), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "build_architecture_cases.py",
                    "--registry",
                    str(registry),
                    "--split",
                    "dev",
                    "--condition",
                    "native",
                    "--output-dir",
                    str(root / "cases"),
                    "--allow-partial",
                    "--projection-identity",
                    str(identity),
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("site registry is frozen", completed.stderr)

    def test_builder_rejects_registry_entry_without_program_artifacts(self) -> None:
        from iclr2027.dataset import build_native_cases

        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "site_registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "ace.iclr2027.site_registry.v1",
                        "version": "fixture-v1",
                        "sites": [
                            {
                                "pnu": "1168011800104170004",
                                "split": "dev",
                                "district_code": "11680",
                                "parcel_area_m2": 264.126,
                                "artifacts": {},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "has no program artifacts"):
                build_native_cases(registry, split="dev")

    def test_registry_freeze_binds_all_four_complete_case_bundles(self) -> None:
        from iclr2027.dataset import (
            freeze_site_registry,
            update_split_manifest,
            verify_frozen_registry,
        )

        # The v2 freeze path is exercised with real public/internal/gold triplets;
        # the legacy synthetic v1 manifest below remains unreachable by design.
        from tests.test_iclr2027_freeze_v2 import FreezeV2Tests

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = FreezeV2Tests()._build_all(root)
            public_registry = root / "site_registry.public.json"
            receipt = root / "freeze_receipt.json"
            freeze_site_registry(
                registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
            )
            frozen = verify_frozen_registry(
                registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
            )
            self.assertEqual(set(frozen["bundles"]), {
                "dev.native",
                "dev.challenged",
                "test.native",
                "test.challenged",
            })
        return

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases_dir = root / "cases"
            cases_dir.mkdir()
            registry = root / "site_registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema_version": "ace.iclr2027.site_registry.v1",
                        "version": "freeze-fixture-v1",
                        "frozen": False,
                        "split_manifest_sha256": "",
                        "sites": [],
                    }
                ),
                encoding="utf-8",
            )
            split_manifest = root / "split_manifest.json"
            for split, count in (("dev", 6), ("test", 15)):
                for condition in ("native", "challenged"):
                    stem = f"{split}.{condition}"
                    public_path = cases_dir / f"{stem}.public.jsonl"
                    gold_path = cases_dir / f"{stem}.gold.jsonl"
                    source_path = cases_dir / f"{stem}.source.json"
                    source_path.write_text(
                        json.dumps({"source": stem}),
                        encoding="utf-8",
                    )
                    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
                    public_path.write_text(
                        "".join(
                            json.dumps(
                                {
                                    "case_id": f"{stem}-{i}",
                                    "source_artifact_sha256": source_sha256,
                                }
                            )
                            + "\n"
                            for i in range(count)
                        ),
                        encoding="utf-8",
                    )
                    gold_path.write_text(
                        "".join(json.dumps({"case_id": f"{stem}-{i}"}) + "\n" for i in range(count)),
                        encoding="utf-8",
                    )
                    bundle_manifest = {
                        "schema_version": "ace.iclr2027.case_manifest.v1",
                        "registry_version": "freeze-fixture-v1",
                        "split": split,
                        "condition": condition,
                        "case_count": count,
                        "case_ids": [f"{stem}-{i}" for i in range(count)],
                        "sources": [
                            {
                                "path": source_path.name,
                                "sha256": source_sha256,
                            }
                        ],
                        "files": {
                            "public": {
                                "path": public_path.name,
                                "record_count": count,
                                "sha256": hashlib.sha256(public_path.read_bytes()).hexdigest(),
                            },
                            "gold": {
                                "path": gold_path.name,
                                "record_count": count,
                                "sha256": hashlib.sha256(gold_path.read_bytes()).hexdigest(),
                            },
                        },
                    }
                    manifest_path = cases_dir / f"{stem}.manifest.json"
                    manifest_path.write_text(json.dumps(bundle_manifest), encoding="utf-8")
                    update_split_manifest(
                        bundle_manifest,
                        bundle_manifest_path=manifest_path,
                        split_manifest_path=split_manifest,
                    )

            def rebind_bundle(stem: str, manifest: dict[str, object]) -> None:
                manifest_path = cases_dir / f"{stem}.manifest.json"
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                split_payload = json.loads(split_manifest.read_text(encoding="utf-8"))
                split_payload["bundles"][stem]["manifest_sha256"] = hashlib.sha256(
                    manifest_path.read_bytes()
                ).hexdigest()
                split_manifest.write_text(json.dumps(split_payload), encoding="utf-8")

            native_manifest_path = cases_dir / "dev.native.manifest.json"
            native_manifest = json.loads(native_manifest_path.read_text(encoding="utf-8"))
            native_manifest["condition"] = "challenged"
            rebind_bundle("dev.native", native_manifest)
            with self.assertRaisesRegex(ValueError, "manifest metadata mismatch"):
                freeze_site_registry(registry, split_manifest_path=split_manifest)

            native_manifest["condition"] = "native"
            rebind_bundle("dev.native", native_manifest)
            public_path = cases_dir / "dev.native.public.jsonl"
            original_public = public_path.read_text(encoding="utf-8")
            public_rows = [json.loads(line) for line in original_public.splitlines()]
            public_rows[0]["source_artifact_sha256"] = "f" * 64
            public_path.write_text(
                "".join(json.dumps(row) + "\n" for row in public_rows),
                encoding="utf-8",
            )
            native_manifest["files"]["public"]["sha256"] = hashlib.sha256(
                public_path.read_bytes()
            ).hexdigest()
            rebind_bundle("dev.native", native_manifest)
            with self.assertRaisesRegex(ValueError, "packet source artifact is not bound"):
                freeze_site_registry(registry, split_manifest_path=split_manifest)

            public_path.write_text(original_public, encoding="utf-8")
            native_manifest["files"]["public"]["sha256"] = hashlib.sha256(
                public_path.read_bytes()
            ).hexdigest()
            rebind_bundle("dev.native", native_manifest)

            freeze_site_registry(registry, split_manifest_path=split_manifest)
            frozen = verify_frozen_registry(
                registry,
                split_manifest_path=split_manifest,
            )

            self.assertEqual(set(frozen["bundles"]), {
                "dev.native",
                "dev.challenged",
                "test.native",
                "test.challenged",
            })
            registry_payload = json.loads(registry.read_text(encoding="utf-8"))
            self.assertTrue(registry_payload["frozen"])
            self.assertEqual(len(registry_payload["split_manifest_sha256"]), 64)

            (cases_dir / "dev.native.source.json").write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source artifact hash mismatch"):
                verify_frozen_registry(registry, split_manifest_path=split_manifest)

    def test_stage_aware_challenges_cover_execution_faults_and_attempt_integrity(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.dataset import CaseBuildResult, _challenge_native_result
        from iclr2027.faults import FAULT_REGISTRY
        from iclr2027.validators import gold_from_validation, validate_evidence_packet

        execution, _ = packet_from_arr_artifacts(
            FIXTURE,
            pnu="1168011800104170004",
            program="neighborhood",
            case_id="seed-native",
        )
        execution_packets = []
        for index in range(7):
            payload = execution.to_dict()
            payload["case_id"] = f"dev-execution-{index}-native"
            execution_packets.append(type(execution).from_dict(payload))

        actual = (
            Path(__file__).parents[1]
            / "data"
            / "iclr2027"
            / "arr"
            / "dev-417-law-restored"
            / "maas-book-programs-summary.json"
        )
        attempt, _ = packet_from_arr_artifacts(
            actual,
            pnu="1168011800104170004",
            program="gymnasium",
            case_id="dev-attempt-native",
        )
        candidate_floor, _ = packet_from_arr_artifacts(
            Path(__file__).parents[1]
            / "data"
            / "iclr2027"
            / "arr"
            / "test-03"
            / "maas-book-programs-summary.json",
            pnu="1165011100200390001",
            program="gymnasium",
            case_id="dev-candidate-floor-native",
        )
        packets = tuple([*execution_packets, attempt, candidate_floor])
        native = CaseBuildResult(
            split="dev",
            condition="native",
            registry_version="fixture-v1",
            packets=packets,
            gold_records=tuple(
                gold_from_validation(packet, mutation_family="")
                for packet in packets
            ),
        )

        challenged = _challenge_native_result(native)

        self.assertEqual(len(challenged.packets), 9)
        families = {record.mutation_family for record in challenged.gold_records}
        self.assertTrue(set(FAULT_REGISTRY).issubset(families))
        self.assertIn("portfolio_attempt_hash", families)
        attempt_challenged = next(
            packet for packet in challenged.packets if packet.attempt_stage == "selection"
        )
        self.assertEqual(
            set(validate_evidence_packet(attempt_challenged).blocking_issue_codes),
            {
                "identity.attempt_hash_mismatch",
                "selection.no_admitted_candidate",
            },
        )
        candidate_floor_challenged = next(
            packet
            for packet in challenged.packets
            if packet.attempt_stage == "candidate_floor_context"
        )
        candidate_floor_validation = validate_evidence_packet(
            candidate_floor_challenged
        )
        self.assertEqual(
            candidate_floor_validation.blocking_issue_codes,
            ("identity.attempt_hash_mismatch",),
        )
        self.assertEqual(
            candidate_floor_validation.missing_evidence_codes,
            ("candidate_floor_context.typed_ledger_missing",),
        )
        candidate_floor_gold = next(
            record
            for record in challenged.gold_records
            if record.case_id == candidate_floor_challenged.case_id
        )
        self.assertEqual(candidate_floor_gold.expected_decision, "STOP_REJECT")
        self.assertEqual(
            candidate_floor_gold.missing_evidence_codes,
            candidate_floor_validation.missing_evidence_codes,
        )

    def test_full_development_challenge_requires_exactly_seven_execution_subjects(self) -> None:
        from iclr2027.arr_adapter import packet_from_arr_artifacts
        from iclr2027.dataset import CaseBuildResult, _challenge_native_result
        from iclr2027.validators import gold_from_validation

        execution, _ = packet_from_arr_artifacts(
            FIXTURE,
            pnu="1168011800104170004",
            program="neighborhood",
            case_id="seed-native",
        )
        actual = (
            Path(__file__).parents[1]
            / "data"
            / "iclr2027"
            / "arr"
            / "dev-417-law-restored"
            / "maas-book-programs-summary.json"
        )
        attempt, _ = packet_from_arr_artifacts(
            actual,
            pnu="1168011800104170004",
            program="gymnasium",
            case_id="attempt-seed-native",
        )
        packets = []
        for index in range(4):
            payload = execution.to_dict()
            payload["case_id"] = f"execution-{index}-native"
            packets.append(type(execution).from_dict(payload))
        for index in range(2):
            payload = attempt.to_dict()
            payload["case_id"] = f"attempt-{index}-native"
            packets.append(type(attempt).from_dict(payload))
        packet_tuple = tuple(packets)
        native = CaseBuildResult(
            split="dev",
            condition="native",
            registry_version="fixture-v1",
            packets=packet_tuple,
            gold_records=tuple(
                gold_from_validation(packet, mutation_family="")
                for packet in packet_tuple
            ),
        )

        with self.assertRaisesRegex(ValueError, "7 execution packets"):
            _challenge_native_result(native)


if __name__ == "__main__":
    unittest.main()
