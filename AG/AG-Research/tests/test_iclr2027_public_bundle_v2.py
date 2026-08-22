from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "iclr2027" / "native_summary.json"
PNU = str(json.loads(FIXTURE.read_text(encoding="utf-8"))["pnu"])
SECRET = bytes(range(32))


class PublicBundleV2Tests(unittest.TestCase):
    def _registry(self, root: Path) -> Path:
        registry = root / "site_registry.json"
        registry.write_text(
            json.dumps(
                {
                    "schema_version": "ace.iclr2027.site_registry.v1",
                    "version": "public-bundle-fixture-v1",
                    "frozen": False,
                    "split_manifest_sha256": "",
                    "sites": [
                        {
                            "pnu": PNU,
                            "split": "dev",
                            "district_code": PNU[:5],
                            "parcel_area_m2": 250.0,
                            "area_bin": "small",
                            "artifacts": {"neighborhood": str(FIXTURE.resolve())},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return registry

    def test_private_identity_sidecar_is_exact_and_never_serializes_secret(self) -> None:
        try:
            from iclr2027.release import load_projection_identity
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"private release identity loader is missing: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sidecar = root / "projection_identity.private.json"
            sidecar.write_text(
                json.dumps(
                    {
                        "schema_version": "ace.iclr2027.projection_identity.private.v1",
                        "secret_hex": SECRET.hex(),
                    }
                ),
                encoding="utf-8",
            )

            identity = load_projection_identity(sidecar)

            self.assertRegex(identity.commitment, r"^[0-9a-f]{64}$")
            self.assertNotIn(SECRET.hex(), repr(identity))

            invalid = json.loads(sidecar.read_text(encoding="utf-8"))
            invalid["unexpected"] = True
            sidecar.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exact keys"):
                load_projection_identity(sidecar)

    def test_writer_emits_hash_bound_public_internal_gold_triplet_v2(self) -> None:
        try:
            from iclr2027.dataset import build_native_cases, write_case_bundle
            from iclr2027.projection import ProjectionIdentity
            from iclr2027.schema import (
                ArchitectureGoldRecord,
                ArchitecturePublicCase,
                PrivateCaseBinding,
            )
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"public bundle v2 API is missing: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = build_native_cases(self._registry(root), split="dev")
            output = root / "cases"

            manifest = write_case_bundle(
                result,
                output_dir=output,
                projection_identity=ProjectionIdentity(SECRET),
            )

            public_path = output / "dev.native.public.jsonl"
            internal_path = output / "dev.native.internal.jsonl"
            gold_path = output / "dev.native.gold.jsonl"
            public_payload = json.loads(public_path.read_text(encoding="utf-8"))
            internal_payload = json.loads(internal_path.read_text(encoding="utf-8"))
            gold_payload = json.loads(gold_path.read_text(encoding="utf-8"))
            public = ArchitecturePublicCase.from_dict(public_payload)
            binding = PrivateCaseBinding.from_dict(internal_payload)
            gold = ArchitectureGoldRecord.from_dict(gold_payload)

            self.assertEqual(manifest["schema_version"], "ace.iclr2027.case_manifest.v2")
            self.assertEqual(public.case_id, binding.public_case_id)
            self.assertEqual(public.case_id, gold.case_id)
            self.assertNotIn(PNU, public_path.read_text(encoding="utf-8"))
            self.assertNotIn('"condition"', public_path.read_text(encoding="utf-8"))
            self.assertIn(PNU, internal_path.read_text(encoding="utf-8"))
            self.assertEqual(set(manifest["files"]), {"public", "internal", "gold"})
            self.assertEqual(
                manifest["files"]["public"]["schema_version"],
                "ace.iclr2027.public_case.v1",
            )
            self.assertEqual(
                manifest["files"]["internal"]["schema_version"],
                "ace.iclr2027.private_case_binding.v1",
            )
            self.assertEqual(
                manifest["case_ids"],
                [public.case_id],
            )
            self.assertEqual(len(manifest["registry_core_sha256"]), 64)
            self.assertEqual(len(manifest["identity_commitment"]), 64)
            self.assertEqual(
                manifest["sources"],
                [
                    {
                        "source_id": "source:"
                        + hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                        "sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                    }
                ],
            )
            self.assertNotIn("path", json.dumps(manifest["sources"]))

    def test_writer_rejects_public_identity_collision(self) -> None:
        from dataclasses import replace
        from unittest.mock import patch

        from iclr2027.dataset import build_native_cases, write_case_bundle
        from iclr2027.projection import ProjectionIdentity

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = build_native_cases(self._registry(root), split="dev")
            duplicate = replace(
                result.packets[0],
                case_id="different-internal-case-native",
            )
            duplicate_gold = replace(
                result.gold_records[0],
                case_id=duplicate.case_id,
            )
            duplicated_result = replace(
                result,
                packets=(result.packets[0], duplicate),
                gold_records=(result.gold_records[0], duplicate_gold),
            )
            identity = ProjectionIdentity(SECRET)

            with patch.object(
                ProjectionIdentity,
                "case_id",
                return_value="case:" + "0" * 64,
            ):
                with self.assertRaisesRegex(ValueError, "duplicate public case"):
                    write_case_bundle(
                        duplicated_result,
                        output_dir=root / "cases",
                        projection_identity=identity,
                    )


if __name__ == "__main__":
    unittest.main()
