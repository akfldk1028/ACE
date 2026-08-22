from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]
SCRIPT = PROJECT_ROOT / "bind_iclr2027_artifacts.py"
PROGRAMS = ("neighborhood", "gymnasium", "cultural")
PNU_A = "1168011800104170004"
PNU_B = "1168011800104670003"
PNU_EXTRA = "1111010100100000001"


class ArtifactBindingCliTests(unittest.TestCase):
    def _write_registry(
        self,
        root: Path,
        pnus: tuple[str, ...] = (PNU_A, PNU_B),
        *,
        frozen: bool = False,
        artifacts_by_pnu: dict[str, dict[str, str]] | None = None,
        schema_version: str = "ace.iclr2027.site_registry.v1",
    ) -> Path:
        artifacts_by_pnu = artifacts_by_pnu or {}
        registry = root / "site_registry.json"
        registry.write_text(
            json.dumps(
                {
                    "schema_version": schema_version,
                    "version": "binding-fixture-v1",
                    "frozen": frozen,
                    "split_manifest_sha256": "",
                    "sites": [
                        {
                            "pnu": pnu,
                            "split": "dev" if index == 0 else "test",
                            "district_code": pnu[:5],
                            "parcel_area_m2": 300.0 + index,
                            "artifacts": artifacts_by_pnu.get(pnu, {}),
                        }
                        for index, pnu in enumerate(pnus)
                    ],
                }
            ),
            encoding="utf-8",
        )
        return registry

    def _write_summary(
        self,
        root: Path,
        name: str,
        pnu: str,
        *,
        schema_version: str = "arr.maas.book_program_portfolios.v1",
        slugs: tuple[str, ...] = PROGRAMS,
    ) -> Path:
        summary = root / "summaries" / name
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(
            json.dumps(
                {
                    "schema_version": schema_version,
                    "pnu": pnu,
                    "programs": [
                        {"slug": slug, "program": f"fixture-{slug}", "rows": []}
                        for slug in slugs
                    ],
                }
            ),
            encoding="utf-8",
        )
        return summary

    def _run(self, registry: Path, summaries: list[Path]) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(SCRIPT), "--registry", str(registry)]
        for summary in summaries:
            command.extend(("--summary", str(summary)))
        return subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def _assert_rejected(
        self,
        registry: Path,
        summaries: list[Path],
        message: str,
    ) -> None:
        before = registry.read_bytes()
        completed = self._run(registry, summaries)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(message, completed.stderr)
        self.assertEqual(registry.read_bytes(), before)

    def test_swapped_summary_order_binds_by_internal_pnu_and_uses_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_registry(root)
            summary_a = self._write_summary(root, "first.json", PNU_A)
            summary_b = self._write_summary(root, "second.json", PNU_B)

            completed = self._run(registry, [summary_b, summary_a])

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(registry.read_text(encoding="utf-8"))
            sites = {site["pnu"]: site for site in payload["sites"]}
            self.assertEqual(
                sites[PNU_A]["artifacts"],
                {program: "summaries/first.json" for program in PROGRAMS},
            )
            self.assertEqual(
                sites[PNU_B]["artifacts"],
                {program: "summaries/second.json" for program in PROGRAMS},
            )
            self.assertEqual(
                completed.stdout.strip(),
                "bound_sites=2 summaries=2 artifact_entries=6",
            )
            self.assertNotIn(PNU_A, completed.stdout)
            self.assertNotIn(PNU_B, completed.stdout)

    def test_duplicate_summary_pnu_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_registry(root, (PNU_A,))
            first = self._write_summary(root, "first.json", PNU_A)
            second = self._write_summary(root, "second.json", PNU_A)

            self._assert_rejected(
                registry,
                [first, second],
                "duplicate summary PNU",
            )

    def test_missing_registry_site_summary_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_registry(root)
            summary = self._write_summary(root, "only.json", PNU_A)

            self._assert_rejected(
                registry,
                [summary],
                "missing summaries for 1 registry site",
            )

    def test_extra_summary_pnu_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_registry(root, (PNU_A,))
            expected = self._write_summary(root, "expected.json", PNU_A)
            extra = self._write_summary(root, "extra.json", PNU_EXTRA)

            self._assert_rejected(
                registry,
                [expected, extra],
                "summary PNU is not present in registry",
            )

    def test_wrong_registry_or_summary_schema_is_rejected(self) -> None:
        for wrong_target in ("registry", "summary"):
            with self.subTest(wrong_target=wrong_target), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                registry = self._write_registry(
                    root,
                    (PNU_A,),
                    schema_version=(
                        "ace.iclr2027.site_registry.v0"
                        if wrong_target == "registry"
                        else "ace.iclr2027.site_registry.v1"
                    ),
                )
                summary = self._write_summary(
                    root,
                    "summary.json",
                    PNU_A,
                    schema_version=(
                        "arr.maas.book_program_portfolios.v0"
                        if wrong_target == "summary"
                        else "arr.maas.book_program_portfolios.v1"
                    ),
                )

                self._assert_rejected(
                    registry,
                    [summary],
                    (
                        "unsupported site registry schema"
                        if wrong_target == "registry"
                        else "unsupported ARR summary schema"
                    ),
                )

    def test_missing_duplicate_or_extra_program_slug_is_rejected(self) -> None:
        invalid_programs = {
            "missing": ("neighborhood", "gymnasium"),
            "duplicate": ("neighborhood", "gymnasium", "gymnasium"),
            "extra": (*PROGRAMS, "office"),
        }
        for label, slugs in invalid_programs.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                registry = self._write_registry(root, (PNU_A,))
                summary = self._write_summary(
                    root,
                    "summary.json",
                    PNU_A,
                    slugs=slugs,
                )

                self._assert_rejected(
                    registry,
                    [summary],
                    "ARR summary program slugs",
                )

    def test_invalid_summary_pnu_and_nonfile_summary_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_registry(root, (PNU_A,))
            invalid_pnu = self._write_summary(root, "invalid.json", "not-a-pnu")
            self._assert_rejected(
                registry,
                [invalid_pnu],
                "summary PNU must contain exactly 19 digits",
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_registry(root, (PNU_A,))
            directory = root / "summary-directory"
            directory.mkdir()
            self._assert_rejected(
                registry,
                [directory],
                "summary must be a file",
            )

    def test_frozen_registry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_registry(root, (PNU_A,), frozen=True)
            summary = self._write_summary(root, "summary.json", PNU_A)

            self._assert_rejected(registry, [summary], "site registry is frozen")

    def test_existing_nonidentical_artifacts_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = self._write_registry(
                root,
                (PNU_A,),
                artifacts_by_pnu={PNU_A: {"neighborhood": "old.json"}},
            )
            summary = self._write_summary(root, "summary.json", PNU_A)

            self._assert_rejected(
                registry,
                [summary],
                "site artifacts already bound differently",
            )

    def test_identical_existing_binding_is_an_idempotent_noop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = self._write_summary(root, "summary.json", PNU_A)
            identical = {program: "summaries/summary.json" for program in PROGRAMS}
            registry = self._write_registry(
                root,
                (PNU_A,),
                artifacts_by_pnu={PNU_A: identical},
            )
            before = registry.read_bytes()

            completed = self._run(registry, [summary])

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(registry.read_bytes(), before)
            self.assertEqual(
                completed.stdout.strip(),
                "bound_sites=1 summaries=1 artifact_entries=3",
            )


if __name__ == "__main__":
    unittest.main()
