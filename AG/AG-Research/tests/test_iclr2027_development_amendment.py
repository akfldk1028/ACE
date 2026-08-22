from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]
SCRIPT = PROJECT_ROOT / "amend_iclr2027_development.py"
REGISTRY_SCHEMA = "ace.iclr2027.site_registry.v1"
EXPECTED_COUNTS = {
    "dev.native": 15,
    "dev.challenged": 15,
    "test.native": 15,
    "test.challenged": 15,
}


def _pnu(number: int) -> str:
    return f"11110101001{number:08d}"


BASE_DEV = (_pnu(1), _pnu(2))
FINAL_TEST = tuple(_pnu(number) for number in range(11, 16))
OLD_TEST = tuple(_pnu(number) for number in range(21, 26))
OLD_AREAS = (200.0, 600.0, 700_000.0, 900_000.0, 140.0)
PROMOTED = (OLD_TEST[0], OLD_TEST[1], OLD_TEST[4])


class DevelopmentAmendmentTests(unittest.TestCase):
    def _subject(self):
        try:
            from iclr2027.development_amendment import (
                amend_development_registry,
                derive_development_amendment,
            )
        except (ImportError, ModuleNotFoundError) as exc:
            self.fail(f"development amendment module is missing: {exc}")
        return amend_development_registry, derive_development_amendment

    @staticmethod
    def _site(pnu: str, split: str, area: float, *, artifacts=None) -> dict:
        return {
            "pnu": pnu,
            "split": split,
            "district_code": pnu[:5],
            "parcel_area_m2": area,
            "area_bin": (
                "small" if area < 300.0 else "medium" if area < 1000.0 else "large"
            ),
            "artifacts": artifacts or {},
        }

    def _payloads(self) -> tuple[dict, dict, dict]:
        candidates = []
        areas = {
            **{pnu: 250.0 + index * 100 for index, pnu in enumerate(BASE_DEV)},
            **{pnu: 150.0 + index * 300 for index, pnu in enumerate(FINAL_TEST)},
            **dict(zip(OLD_TEST, OLD_AREAS)),
        }
        for index, (pnu, area) in enumerate(areas.items()):
            candidates.append(
                {
                    "pnu": pnu,
                    "district_code": f"{11110 + index:05d}",
                    "parcel_area_m2": area,
                    "boundary_available": True,
                    "law_available": True,
                    "parking_available": True,
                }
            )
        candidate_source = {
            "schema_version": "ace.iclr2027.candidate_source.v1",
            "provenance": {"fixture": True},
            "candidates": candidates,
            "exclusions": [],
        }
        candidate_sha = "c" * 64
        current = {
            "schema_version": REGISTRY_SCHEMA,
            "version": "selection-20260818-currentv2",
            "frozen": False,
            "split_manifest_sha256": "",
            "selection": {
                "seed": 20260818,
                "max_parcel_area_m2": 30_000.0,
                "candidate_source_sha256": candidate_sha,
                "selected_pnus": list(FINAL_TEST),
                "excluded": {},
            },
            "sites": [
                *(
                    self._site(pnu, "dev", areas[pnu])
                    for pnu in BASE_DEV
                ),
                *(
                    self._site(
                        pnu,
                        "test",
                        areas[pnu],
                        artifacts={"neighborhood": f"kept/{index}.json"},
                    )
                    for index, pnu in enumerate(FINAL_TEST, start=1)
                ),
            ],
        }
        archived = {
            "schema_version": REGISTRY_SCHEMA,
            "version": "selection-20260818-archivedv1",
            "frozen": False,
            "split_manifest_sha256": "",
            "selection": {
                "seed": 20260818,
                "candidate_source_sha256": candidate_sha,
                "selected_pnus": list(OLD_TEST),
                "excluded": {},
            },
            "sites": [
                self._site(pnu, "dev", areas[pnu]) for pnu in BASE_DEV
            ]
            + [
                self._site(pnu, "test", area, artifacts={"legacy": "ignored.json"})
                for pnu, area in zip(OLD_TEST, OLD_AREAS)
            ],
        }
        return current, archived, candidate_source

    def _write_fixture(self, root: Path) -> tuple[Path, Path, Path, str, str]:
        current, archived, candidate_source = self._payloads()
        candidate_path = root / "candidate_source.json"
        candidate_path.write_text(
            json.dumps(candidate_source, sort_keys=True), encoding="utf-8"
        )
        candidate_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
        current["selection"]["candidate_source_sha256"] = candidate_sha
        archived["selection"]["candidate_source_sha256"] = candidate_sha

        registry_path = root / "site_registry.json"
        archive_path = root / "site_registry.v1_pre_area_cap.json"
        registry_path.write_text(json.dumps(current, sort_keys=True), encoding="utf-8")
        archive_path.write_text(json.dumps(archived, sort_keys=True), encoding="utf-8")
        archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        return registry_path, archive_path, candidate_path, archive_sha, candidate_sha

    def test_promotes_all_and_only_eligible_archived_test_sites(self) -> None:
        amend_files, _ = self._subject()
        with tempfile.TemporaryDirectory() as tmp:
            registry, archive, candidates, archive_sha, candidate_sha = self._write_fixture(
                Path(tmp)
            )
            original = json.loads(registry.read_text(encoding="utf-8"))
            original_tests = {
                site["pnu"]: site
                for site in original["sites"]
                if site["split"] == "test"
            }

            amended = amend_files(
                registry,
                archive,
                candidates,
                expected_archived_registry_sha256=archive_sha,
                expected_candidate_source_sha256=candidate_sha,
            )

            dev_sites = [site for site in amended["sites"] if site["split"] == "dev"]
            test_sites = [site for site in amended["sites"] if site["split"] == "test"]
            self.assertEqual(len(dev_sites), 5)
            self.assertEqual(len(test_sites), 5)
            promoted = {
                site["pnu"]: site
                for site in dev_sites
                if site["pnu"] not in BASE_DEV
            }
            self.assertEqual(set(promoted), set(PROMOTED))
            self.assertEqual([promoted[pnu]["artifacts"] for pnu in PROMOTED], [{}, {}, {}])
            self.assertEqual({site["pnu"]: site for site in test_sites}, original_tests)
            self.assertEqual(amended["schema_version"], REGISTRY_SCHEMA)
            self.assertEqual(amended["protocol_revision"], 2)
            self.assertEqual(amended["expected_bundle_counts"], EXPECTED_COUNTS)
            self.assertRegex(amended["version"], r"^selection-20260819-[0-9a-f]{12}$")
            self.assertNotEqual(amended["version"], original["version"])

            amendment = amended["selection"]["development_amendment"]
            self.assertEqual(amendment["promoted_source_ranks"], [1, 2, 5])
            self.assertEqual(amendment["excluded_source_ranks"], [3, 4])
            self.assertEqual(
                amendment["excluded_reason_counts"],
                {"parcel_area_out_of_scope": 2},
            )
            self.assertEqual(amendment["promoted_pnus"], list(PROMOTED))
            self.assertEqual(amendment["source_registry_sha256"], archive_sha)
            self.assertEqual(amendment["candidate_source_sha256"], candidate_sha)
            self.assertEqual(amendment["max_parcel_area_m2"], 30_000.0)
            self.assertTrue(amendment["include_all_matches"])

    def test_derivation_is_stable_under_nonsemantic_input_order(self) -> None:
        _, derive = self._subject()
        current, archived, candidates = self._payloads()
        kwargs = {
            "source_registry_path": "site_registry.v1_pre_area_cap.json",
            "source_registry_sha256": "a" * 64,
            "candidate_source_sha256": "c" * 64,
        }
        first = derive(current, archived, candidates, **kwargs)
        current["sites"].reverse()
        archived["sites"].reverse()
        candidates["candidates"].reverse()

        second = derive(current, archived, candidates, **kwargs)

        self.assertEqual(second, first)

    def test_selection_fields_name_their_actual_source_documents(self) -> None:
        _, derive = self._subject()
        current, archived, candidates = self._payloads()

        amended = derive(
            current,
            archived,
            candidates,
            source_registry_path="archive.json",
            source_registry_sha256="a" * 64,
            candidate_source_sha256="c" * 64,
        )

        amendment = amended["selection"]["development_amendment"]
        self.assertEqual(
            amendment["selection_fields"],
            [
                "archived_registry.sites[].split",
                "candidate_source.candidates[].parcel_area_m2",
                "candidate_source.candidates[].boundary_available",
                "candidate_source.candidates[].law_available",
                "candidate_source.candidates[].parking_available",
            ],
        )

    def test_provenance_is_relative_to_final_output_and_remains_idempotent(self) -> None:
        amend_files, _ = self._subject()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs = root / "inputs"
            inputs.mkdir()
            registry, archive, candidates, archive_sha, candidate_sha = (
                self._write_fixture(inputs)
            )
            output = root / "release" / "site_registry.json"
            output.parent.mkdir()

            amended = amend_files(
                registry,
                archive,
                candidates,
                expected_archived_registry_sha256=archive_sha,
                expected_candidate_source_sha256=candidate_sha,
                output_registry_path=output,
            )

            provenance = amended["selection"]["development_amendment"]
            self.assertEqual(
                provenance["source_registry_path"],
                "../inputs/site_registry.v1_pre_area_cap.json",
            )
            output.write_text(json.dumps(amended), encoding="utf-8")
            repeated = amend_files(
                output,
                archive,
                candidates,
                expected_archived_registry_sha256=archive_sha,
                expected_candidate_source_sha256=candidate_sha,
                output_registry_path=output,
            )
            self.assertEqual(repeated, amended)

    def test_rejects_wrong_expected_input_hash_without_mutating_registry(self) -> None:
        amend_files, _ = self._subject()
        with tempfile.TemporaryDirectory() as tmp:
            registry, archive, candidates, archive_sha, candidate_sha = self._write_fixture(
                Path(tmp)
            )
            before = registry.read_bytes()
            for label, expected_archive, expected_candidate in (
                ("archive", "0" * 64, candidate_sha),
                ("candidate", archive_sha, "0" * 64),
            ):
                with self.subTest(label=label), self.assertRaisesRegex(
                    ValueError, "SHA-256 mismatch"
                ):
                    amend_files(
                        registry,
                        archive,
                        candidates,
                        expected_archived_registry_sha256=expected_archive,
                        expected_candidate_source_sha256=expected_candidate,
                    )
                self.assertEqual(registry.read_bytes(), before)

    def test_rejects_candidate_hash_not_bound_by_both_registries(self) -> None:
        _, derive = self._subject()
        current, archived, candidates = self._payloads()
        for label, target in (("current", current), ("archive", archived)):
            broken = copy.deepcopy(target)
            broken["selection"]["candidate_source_sha256"] = "f" * 64
            args = (
                (broken, archived, candidates)
                if label == "current"
                else (current, broken, candidates)
            )
            with self.subTest(label=label), self.assertRaisesRegex(
                ValueError, "candidate source hash is not bound"
            ):
                derive(
                    *args,
                    source_registry_path="archive.json",
                    source_registry_sha256="a" * 64,
                    candidate_source_sha256="c" * 64,
                )

    def test_rejects_duplicate_site_or_candidate_identity(self) -> None:
        _, derive = self._subject()
        current, archived, candidates = self._payloads()
        mutations = []
        duplicate_current = copy.deepcopy(current)
        duplicate_current["sites"].append(copy.deepcopy(duplicate_current["sites"][0]))
        mutations.append(("current", duplicate_current, archived, candidates))
        duplicate_archive = copy.deepcopy(archived)
        duplicate_archive["sites"].append(copy.deepcopy(duplicate_archive["sites"][-1]))
        mutations.append(("archive", current, duplicate_archive, candidates))
        duplicate_candidate = copy.deepcopy(candidates)
        duplicate_candidate["candidates"].append(
            copy.deepcopy(duplicate_candidate["candidates"][0])
        )
        mutations.append(("candidate", current, archived, duplicate_candidate))

        for label, current_value, archive_value, candidate_value in mutations:
            with self.subTest(label=label), self.assertRaisesRegex(
                ValueError, "duplicate"
            ):
                derive(
                    current_value,
                    archive_value,
                    candidate_value,
                    source_registry_path="archive.json",
                    source_registry_sha256="a" * 64,
                    candidate_source_sha256="c" * 64,
                )

    def test_rejects_overlap_with_final_v2_test(self) -> None:
        _, derive = self._subject()
        current, archived, candidates = self._payloads()
        replaced = current["selection"]["selected_pnus"][0]
        current["selection"]["selected_pnus"][0] = PROMOTED[0]
        for site in current["sites"]:
            if site["pnu"] == replaced:
                site["pnu"] = PROMOTED[0]
                break

        with self.assertRaisesRegex(ValueError, "overlaps final v2 test"):
            derive(
                current,
                archived,
                candidates,
                source_registry_path="archive.json",
                source_registry_sha256="a" * 64,
                candidate_source_sha256="c" * 64,
            )

    def test_rejects_unexpected_eligible_promotion_count(self) -> None:
        _, derive = self._subject()
        current, archived, candidates = self._payloads()
        for candidate in candidates["candidates"]:
            if candidate["pnu"] == PROMOTED[1]:
                candidate["law_available"] = False

        with self.assertRaisesRegex(ValueError, "expected 3 eligible promotions"):
            derive(
                current,
                archived,
                candidates,
                source_registry_path="archive.json",
                source_registry_sha256="a" * 64,
                candidate_source_sha256="c" * 64,
            )

    def test_protocol_area_cap_cannot_be_redefined(self) -> None:
        _, derive = self._subject()
        current, archived, candidates = self._payloads()

        for cap in (29_999.0, 30_001.0, True):
            with self.subTest(cap=cap), self.assertRaisesRegex(
                ValueError, "protocol max_parcel_area_m2 must equal 30000.0"
            ):
                derive(
                    current,
                    archived,
                    candidates,
                    source_registry_path="archive.json",
                    source_registry_sha256="a" * 64,
                    candidate_source_sha256="c" * 64,
                    max_parcel_area_m2=cap,
                )

    def test_cli_is_atomic_idempotent_and_never_prints_site_identifiers(self) -> None:
        self._subject()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry, archive, candidates, archive_sha, candidate_sha = self._write_fixture(
                root
            )
            command = [
                sys.executable,
                str(SCRIPT),
                "--registry",
                str(registry),
                "--archived-registry",
                str(archive),
                "--candidate-source",
                str(candidates),
                "--expected-archived-registry-sha256",
                archive_sha,
                "--expected-candidate-source-sha256",
                candidate_sha,
                "--output",
                str(registry),
            ]

            first = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            first_bytes = registry.read_bytes()
            second = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(registry.read_bytes(), first_bytes)
            self.assertIn("promoted_sites=3", first.stdout)
            self.assertIn("development_sites=5", first.stdout)
            self.assertIn("test_sites=5", first.stdout)
            for pnu in (*BASE_DEV, *FINAL_TEST, *OLD_TEST):
                self.assertNotIn(pnu, first.stdout)
                self.assertNotIn(pnu, second.stdout)

    def test_cli_rejects_output_collision_with_immutable_sources(self) -> None:
        self._subject()
        for source_name in ("archive", "candidate"):
            with self.subTest(source_name=source_name), tempfile.TemporaryDirectory() as tmp:
                registry, archive, candidates, archive_sha, candidate_sha = (
                    self._write_fixture(Path(tmp))
                )
                output = archive if source_name == "archive" else candidates
                before = output.read_bytes()
                result = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "--registry",
                        str(registry),
                        "--archived-registry",
                        str(archive),
                        "--candidate-source",
                        str(candidates),
                        "--expected-archived-registry-sha256",
                        archive_sha,
                        "--expected-candidate-source-sha256",
                        candidate_sha,
                        "--output",
                        str(output),
                    ],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("output registry collides", result.stderr)
                self.assertEqual(output.read_bytes(), before)

    def test_existing_amendment_must_match_before_idempotent_noop(self) -> None:
        amend_files, _ = self._subject()
        with tempfile.TemporaryDirectory() as tmp:
            registry, archive, candidates, archive_sha, candidate_sha = self._write_fixture(
                Path(tmp)
            )
            amended = amend_files(
                registry,
                archive,
                candidates,
                expected_archived_registry_sha256=archive_sha,
                expected_candidate_source_sha256=candidate_sha,
            )
            amended["selection"]["development_amendment"]["promoted_source_ranks"] = [
                1,
                2,
                4,
            ]
            registry.write_text(json.dumps(amended), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "existing development amendment"):
                amend_files(
                    registry,
                    archive,
                    candidates,
                    expected_archived_registry_sha256=archive_sha,
                    expected_candidate_source_sha256=candidate_sha,
                )


if __name__ == "__main__":
    unittest.main()
