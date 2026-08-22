from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json"
SECRET = bytes(range(32))
PROGRAMS = ("neighborhood", "gymnasium", "cultural")


def _pnu(index: int) -> str:
    return f"10000000001{index:08d}"


class FreezeV2Tests(unittest.TestCase):
    def _registry(self, root: Path) -> Path:
        registry = root / "site_registry.json"
        registry.write_text(
            json.dumps(
                {
                    "schema_version": "ace.iclr2027.site_registry.v1",
                    "version": "selection-20260819-abcdef123456",
                    "frozen": False,
                    "split_manifest_sha256": "",
                    "expected_bundle_counts": {
                        "dev.native": 15,
                        "dev.challenged": 15,
                        "test.native": 15,
                        "test.challenged": 15,
                    },
                    "sites": [
                        {
                            "pnu": _pnu(index),
                            "split": "dev" if index <= 5 else "test",
                            "district_code": _pnu(index)[:5],
                            "parcel_area_m2": 100.0 + index,
                            "area_bin": "small" if index % 2 else "medium",
                            "artifacts": {
                                program: str(FIXTURE.resolve()) for program in PROGRAMS
                            },
                        }
                        for index in range(1, 11)
                    ],
                }
            ),
            encoding="utf-8",
        )
        return registry

    def _build_all(self, root: Path):
        from iclr2027.dataset import (
            CaseBuildResult,
            SourceArtifact,
            registry_core_sha256,
            update_split_manifest,
            write_case_bundle,
        )
        from iclr2027.projection import ProjectionIdentity
        from iclr2027.schema import ArchitectureEvidencePacket, ArchitectureGoldRecord

        registry_path = self._registry(root)
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        core_hash = registry_core_sha256(registry)
        source_hash = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        identity = ProjectionIdentity(SECRET)
        cases = root / "cases"
        split_manifest = root / "split_manifest.json"
        for split in ("dev", "test"):
            sites = [site for site in registry["sites"] if site["split"] == split]
            for condition in ("native", "challenged"):
                packets = []
                gold = []
                for site in sites:
                    for program in PROGRAMS:
                        case_id = f"{split}-{site['pnu']}-{program}-{condition}"
                        packet = ArchitectureEvidencePacket(
                            case_id=case_id,
                            pnu=site["pnu"],
                            program=program,
                            condition=condition,
                            execution_id=f"execution-{split}-{program}",
                            program_hash="a" * 64,
                            geometry_hash="b" * 64,
                            source_artifact_sha256=source_hash,
                            evidence=(
                                {"evidence_id": "evidence:site", "status": "passed"},
                            ),
                        )
                        packets.append(packet)
                        gold.append(
                            ArchitectureGoldRecord(
                                case_id=case_id,
                                expected_decision="STOP_ACCEPT",
                                blocking_issue_codes=(),
                                missing_evidence_codes=(),
                                required_evidence_ids=("evidence:site",),
                                mutation_family="",
                            )
                        )
                result = CaseBuildResult(
                    split=split,
                    condition=condition,
                    registry_version=registry["version"],
                    packets=tuple(packets),
                    gold_records=tuple(gold),
                    source_artifacts=(SourceArtifact(FIXTURE.resolve(), source_hash),),
                    registry_core_sha256=core_hash,
                    expected_bundle_counts=registry["expected_bundle_counts"],
                )
                manifest = write_case_bundle(
                    result,
                    output_dir=cases,
                    projection_identity=identity,
                )
                manifest_path = cases / f"{split}.{condition}.manifest.json"
                update_split_manifest(
                    manifest,
                    bundle_manifest_path=manifest_path,
                    split_manifest_path=split_manifest,
                )
        return registry_path, split_manifest, identity

    def test_freeze_binds_registry_core_public_projection_and_all_triplets(self) -> None:
        try:
            from iclr2027.dataset import freeze_site_registry, verify_frozen_registry
        except ImportError as exc:
            self.fail(f"freeze v2 API is missing: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = self._build_all(root)
            public_registry = root / "site_registry.public.json"
            receipt = root / "freeze_receipt.json"

            freeze_site_registry(
                registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
            )
            verified = verify_frozen_registry(
                registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
            )

            receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
            public_payload = json.loads(public_registry.read_text(encoding="utf-8"))
            registry_payload = json.loads(registry.read_text(encoding="utf-8"))
            self.assertEqual(
                receipt_payload["schema_version"],
                "ace.iclr2027.freeze_receipt.v1",
            )
            self.assertEqual(
                public_payload["schema_version"],
                "ace.iclr2027.public_site_registry.v1",
            )
            self.assertEqual(len(receipt_payload["registry_core_sha256"]), 64)
            self.assertEqual(len(receipt_payload["public_registry_sha256"]), 64)
            self.assertEqual(
                registry_payload["freeze_receipt_sha256"],
                hashlib.sha256(receipt.read_bytes()).hexdigest(),
            )
            self.assertEqual(set(verified["bundles"]), {
                "dev.native",
                "dev.challenged",
                "test.native",
                "test.challenged",
            })
            for site in public_payload["sites"]:
                self.assertEqual(
                    set(site),
                    {"site_ref", "split", "area_bin"},
                )
            public_text = public_registry.read_text(encoding="utf-8")
            for site in registry_payload["sites"]:
                self.assertNotIn(site["pnu"], public_text)

    def test_registry_pnu_substitution_breaks_frozen_core_and_membership(self) -> None:
        from iclr2027.dataset import freeze_site_registry, verify_frozen_registry

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = self._build_all(root)
            public_registry = root / "site_registry.public.json"
            receipt = root / "freeze_receipt.json"
            freeze_site_registry(
                registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
            )
            payload = json.loads(registry.read_text(encoding="utf-8"))
            payload["sites"][0]["pnu"] = _pnu(99)
            registry.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "registry core"):
                verify_frozen_registry(
                    registry,
                    split_manifest_path=split_manifest,
                    projection_identity=identity,
                    public_registry_path=public_registry,
                    freeze_receipt_path=receipt,
                )

    def test_wrong_identity_and_legacy_split_manifest_are_rejected(self) -> None:
        from iclr2027.dataset import freeze_site_registry, verify_frozen_registry
        from iclr2027.projection import ProjectionIdentity

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = self._build_all(root)
            public_registry = root / "site_registry.public.json"
            receipt = root / "freeze_receipt.json"
            freeze_site_registry(
                registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
            )
            with self.assertRaisesRegex(ValueError, "identity commitment"):
                verify_frozen_registry(
                    registry,
                    split_manifest_path=split_manifest,
                    projection_identity=ProjectionIdentity(b"z" * 32),
                    public_registry_path=public_registry,
                    freeze_receipt_path=receipt,
                )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = self._build_all(root)
            payload = json.loads(split_manifest.read_text(encoding="utf-8"))
            payload["schema_version"] = "ace.iclr2027.split_manifest.v1"
            split_manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "split manifest schema"):
                freeze_site_registry(
                    registry,
                    split_manifest_path=split_manifest,
                    projection_identity=identity,
                    public_registry_path=root / "site_registry.public.json",
                    freeze_receipt_path=root / "freeze_receipt.json",
                )

    def test_public_release_is_an_allowlisted_condition_blind_export(self) -> None:
        try:
            from iclr2027.dataset import freeze_site_registry
            from iclr2027.release import write_public_release
        except ImportError as exc:
            self.fail(f"public release exporter is missing: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = self._build_all(root)
            public_registry = root / "site_registry.public.json"
            receipt = root / "freeze_receipt.json"
            freeze_site_registry(
                registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
            )
            release_dir = root / "release"

            manifest = write_public_release(
                registry_path=registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
                output_dir=release_dir,
            )

            self.assertEqual(
                {path.name for path in release_dir.iterdir()},
                {
                    "dev.public.jsonl",
                    "test.public.jsonl",
                    "site_registry.public.json",
                    "release_manifest.json",
                },
            )
            self.assertEqual(
                manifest["schema_version"],
                "ace.iclr2027.public_release_manifest.v1",
            )
            rendered = "\n".join(
                path.read_text(encoding="utf-8") for path in release_dir.iterdir()
            )
            self.assertNotIn('"condition"', rendered)
            self.assertNotIn("internal", rendered)
            self.assertNotIn("gold", rendered)
            registry_payload = json.loads(registry.read_text(encoding="utf-8"))
            for site in registry_payload["sites"]:
                self.assertNotIn(site["pnu"], rendered)

    def test_public_release_refuses_stale_nonallowlisted_output(self) -> None:
        from iclr2027.dataset import freeze_site_registry
        from iclr2027.release import write_public_release

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, split_manifest, identity = self._build_all(root)
            public_registry = root / "site_registry.public.json"
            receipt = root / "freeze_receipt.json"
            freeze_site_registry(
                registry,
                split_manifest_path=split_manifest,
                projection_identity=identity,
                public_registry_path=public_registry,
                freeze_receipt_path=receipt,
            )
            release_dir = root / "release"
            release_dir.mkdir()
            (release_dir / "stale.gold.jsonl").write_text("{}\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "release allowlist"):
                write_public_release(
                    registry_path=registry,
                    split_manifest_path=split_manifest,
                    projection_identity=identity,
                    public_registry_path=public_registry,
                    freeze_receipt_path=receipt,
                    output_dir=release_dir,
                )

    def test_public_registry_rejects_unsafe_area_bin_and_version_lanes(self) -> None:
        from iclr2027.dataset import registry_core_sha256
        from iclr2027.projection import ProjectionIdentity
        from iclr2027.release import build_public_registry_projection

        identity = ProjectionIdentity(SECRET)
        base = {
            "schema_version": "ace.iclr2027.site_registry.v1",
            "version": "selection-20260819-abcdef123456",
            "expected_bundle_counts": {
                "dev.native": 3,
                "dev.challenged": 3,
                "test.native": 3,
                "test.challenged": 3,
            },
            "sites": [
                {
                    "pnu": _pnu(1),
                    "split": "dev",
                    "area_bin": "small",
                    "artifacts": {},
                },
                {
                    "pnu": _pnu(2),
                    "split": "test",
                    "area_bin": "medium",
                    "artifacts": {},
                },
            ],
        }
        for field, value, message in (
            ("area_bin", "1000000000000000001", "area_bin"),
            ("area_bin", "private/source/path", "area_bin"),
        ):
            payload = json.loads(json.dumps(base))
            payload["sites"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaisesRegex(
                ValueError, message
            ):
                build_public_registry_projection(
                    payload,
                    identity,
                    registry_core_hash=registry_core_sha256(payload),
                )
        for version in (
            "selection-20260819-1000000000000000001",
            "../private/registry.json",
            "freeze-v2-fixture",
        ):
            payload = {**base, "version": version}
            with self.subTest(version=version), self.assertRaisesRegex(
                ValueError, "registry version"
            ):
                build_public_registry_projection(
                    payload,
                    identity,
                    registry_core_hash=registry_core_sha256(payload),
                )

    def test_public_metadata_audit_rejects_private_keys_paths_and_raw_ids(self) -> None:
        try:
            from iclr2027.release import audit_public_metadata
        except ImportError as exc:
            self.fail(f"public metadata audit is missing: {exc}")

        unsafe = (
            {"secret_hex": "a" * 64},
            {"internal_case_id": "private-case"},
            {"source_path": "../private/source.json"},
            {"label": "1000000000000000001"},
        )
        for payload in unsafe:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                audit_public_metadata(payload)

    def test_public_metadata_audit_rejects_forbidden_token_variants(self) -> None:
        from iclr2027.release import audit_public_metadata

        unsafe = (
            {"pnu_hint": "redacted"},
            {"condition_label": "redacted"},
            {"review_gold": "redacted"},
            {"release_private": "redacted"},
            {"path_hint": "redacted"},
            {"api_secret": "redacted"},
            {"source_internal": "redacted"},
            {"label": "challenged"},
            {"label": "private:case"},
            {"label": "../registry.json"},
        )
        for payload in unsafe:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                audit_public_metadata(payload)


if __name__ == "__main__":
    unittest.main()
