from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import select_iclr2027_sites


class SiteSelectionCliTests(unittest.TestCase):
    def test_repository_scan_decodes_utf8_when_windows_locale_is_not_utf8(self) -> None:
        expected_pnu = "1111010100100000001"
        stdout_bytes = f"{expected_pnu}\n".encode("utf-8")
        stderr_bytes = "D:/자료/À-plan.txt\n".encode("utf-8")

        def run_with_cp949_default(command: list[str], **kwargs: object):
            encoding = kwargs.get("encoding") or "cp949"
            errors = kwargs.get("errors") or "strict"
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=stdout_bytes.decode(str(encoding), str(errors)),
                stderr=stderr_bytes.decode(str(encoding), str(errors)),
            )

        with patch.object(
            select_iclr2027_sites.subprocess,
            "run",
            side_effect=run_with_cp949_default,
        ):
            discovered = select_iclr2027_sites._repository_pnus(
                Path("D:/자료"),
                exclude_paths=(),
            )

        self.assertEqual(discovered, {expected_pnu})

    def test_repository_scan_reports_failure_when_rg_has_no_stderr(self) -> None:
        completed = subprocess.CompletedProcess(
            ["rg"],
            2,
            stdout="",
            stderr=None,
        )
        with patch.object(
            select_iclr2027_sites.subprocess,
            "run",
            return_value=completed,
        ):
            with self.assertRaisesRegex(RuntimeError, "repository PNU scan failed"):
                select_iclr2027_sites._repository_pnus(
                    Path("D:/repository"),
                    exclude_paths=(),
                )

    def test_repository_scan_keeps_pnus_when_rg_diagnostic_is_malformed_utf8(self) -> None:
        expected_pnu = "1114010100100000002"
        stdout_bytes = f"{expected_pnu}\n".encode("utf-8")
        stderr_bytes = b"D:/repository/invalid-\xff-path\n"

        def run_with_raw_output(command: list[str], **kwargs: object):
            encoding = kwargs.get("encoding") or "cp949"
            errors = kwargs.get("errors") or "strict"
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=stdout_bytes.decode(str(encoding), str(errors)),
                stderr=stderr_bytes.decode(str(encoding), str(errors)),
            )

        with patch.object(
            select_iclr2027_sites.subprocess,
            "run",
            side_effect=run_with_raw_output,
        ):
            discovered = select_iclr2027_sites._repository_pnus(
                Path("D:/repository"),
                exclude_paths=(),
            )

        self.assertEqual(discovered, {expected_pnu})

    @unittest.skipUnless(sys.platform == "win32", "Windows reserved device path")
    def test_repository_scan_excludes_nul_device_entry(self) -> None:
        expected_pnu = "1120010100100000003"

        def run_with_root_nul(command: list[str], **kwargs: object):
            excluded_globs = {
                command[index + 1]
                for index, argument in enumerate(command[:-1])
                if argument == "--glob"
            }
            if "!NUL" not in excluded_globs:
                return subprocess.CompletedProcess(
                    command,
                    2,
                    stdout="",
                    stderr="rg: D:/repository/NUL: invalid function (os error 1)",
                )
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=f"{expected_pnu}\n",
                stderr="",
            )

        with patch.object(
            select_iclr2027_sites.subprocess,
            "run",
            side_effect=run_with_root_nul,
        ):
            discovered = select_iclr2027_sites._repository_pnus(
                Path("D:/repository"),
                exclude_paths=(),
            )

        self.assertEqual(discovered, {expected_pnu})

    def test_repository_scan_excludes_exact_nested_candidate_path(self) -> None:
        excluded_only_pnu = "1121510100100000004"
        shared_pnu = "1135010100100000005"
        evidence_only_pnu = "1141010100100000006"
        same_basename_pnu = "1150010100100000007"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            nested_repo = root / "AG" / "AG-Research"
            candidate_source = nested_repo / "data" / "iclr2027" / "candidate_source.json"
            evidence = nested_repo / "results" / "prior_experiment.txt"
            same_basename = nested_repo / "archive" / "candidate_source.json"
            candidate_source.parent.mkdir(parents=True)
            evidence.parent.mkdir(parents=True)
            same_basename.parent.mkdir(parents=True)
            candidate_source.write_text(
                f"{excluded_only_pnu}\n{shared_pnu}\n",
                encoding="utf-8",
            )
            evidence.write_text(
                f"{shared_pnu}\n{evidence_only_pnu}\n",
                encoding="utf-8",
            )
            same_basename.write_text(f"{same_basename_pnu}\n", encoding="utf-8")

            discovered = select_iclr2027_sites._repository_pnus(
                root,
                exclude_paths=(candidate_source,),
            )

        self.assertEqual(
            discovered,
            {shared_pnu, evidence_only_pnu, same_basename_pnu},
        )

    def test_cli_freezes_five_unseen_stratified_test_sites(self) -> None:
        candidates = [
            self._candidate("1111010100100000001", "11110", 120.0),
            self._candidate("1114010100100000002", "11140", 220.0),
            self._candidate("1120010100100000003", "11200", 450.0),
            self._candidate("1121510100100000004", "11215", 850.0),
            self._candidate("1135010100100000005", "11350", 1200.0),
            self._candidate("1141010100100000006", "11410", 2200.0),
            self._candidate("1168011800104170004", "11680", 264.126),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "candidates.json"
            output = root / "site_registry.json"
            selection_archive = root / "site_registry.v1_pre_area_cap.json"
            (root / "prior_experiment.txt").write_text(
                "previous PNU: 1111010100100000001\n",
                encoding="utf-8",
            )
            selection_archive.write_text(
                "archived candidate PNU: 1114010100100000002\n",
                encoding="utf-8",
            )
            source.write_text(json.dumps({"candidates": candidates}), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "select_iclr2027_sites.py",
                    "--candidate-source",
                    str(source),
                    "--count",
                    "5",
                    "--seed",
                    "20260818",
                    "--inventory-commit",
                    "test-commit",
                    "--repository-root",
                    str(root),
                    "--inventory-exclude-path",
                    str(selection_archive),
                    "--output",
                    str(output),
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            registry = json.loads(output.read_text(encoding="utf-8"))
            test_sites = [site for site in registry["sites"] if site["split"] == "test"]
            self.assertEqual(len(test_sites), 5)
            self.assertNotIn(
                "1168011800104170004",
                {site["pnu"] for site in test_sites},
            )
            self.assertNotIn(
                "1111010100100000001",
                {site["pnu"] for site in test_sites},
            )
            self.assertEqual(
                {site["area_bin"] for site in test_sites},
                {"small", "medium", "large"},
            )
            self.assertGreaterEqual(len({site["district_code"] for site in test_sites}), 3)
            self.assertEqual(registry["selection"]["inventory_commit"], "test-commit")
            self.assertTrue(registry["selection"]["repository_inventory_scanned"])
            self.assertEqual(
                registry["selection"]["inventory_exclude_paths"],
                ["site_registry.v1_pre_area_cap.json"],
            )
            self.assertEqual(len(registry["selection"]["candidate_source_sha256"]), 64)
            self.assertFalse(registry["frozen"])

            registry["frozen"] = True
            output.write_text(json.dumps(registry), encoding="utf-8")
            refused = subprocess.run(
                [
                    *completed.args,
                ],
                cwd=Path(__file__).parents[1],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("existing frozen site registry", refused.stderr)

    @staticmethod
    def _candidate(pnu: str, district: str, area: float) -> dict[str, object]:
        return {
            "pnu": pnu,
            "district_code": district,
            "parcel_area_m2": area,
            "boundary_available": True,
            "law_available": True,
            "parking_available": True,
        }


if __name__ == "__main__":
    unittest.main()
