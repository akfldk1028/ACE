from __future__ import annotations

import csv
import contextlib
import io
import tempfile
import unittest
from pathlib import Path


class ResearchAuditTests(unittest.TestCase):
    def test_resolve_exp01_summary_prefers_complete_pattern_coverage(self) -> None:
        try:
            from iclr2027.audit import resolve_exp01_summary
        except ModuleNotFoundError as exc:
            self.fail(f"audit module is missing: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            exp01 = Path(tmp)
            self._write_summary(exp01 / "summary.csv", ["solo", "rr3"])
            self._write_summary(
                exp01 / "summary_all.csv",
                [
                    "solo",
                    "rr2",
                    "rr3",
                    "rr4",
                    "sel3",
                    "sel4",
                    "swm3",
                    "swm4",
                    "refl2",
                    "refl3",
                    "debate3",
                    "debate4",
                    "pipe",
                    "moa",
                ],
            )

            selected = resolve_exp01_summary(exp01)

        self.assertEqual(selected.name, "summary_all.csv")

    def test_collect_result_inventory_reports_rows_and_pattern_ids(self) -> None:
        try:
            from iclr2027.audit import collect_result_inventory
        except ImportError as exc:
            self.fail(f"inventory function is missing: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp)
            exp01 = results / "exp01"
            exp01.mkdir()
            self._write_summary(exp01 / "summary_all.csv", ["rr2", "rr3", "moa"])

            inventory = collect_result_inventory(results)

        self.assertEqual(inventory["exp01"]["row_count"], 3)
        self.assertEqual(inventory["exp01"]["pattern_ids"], ["moa", "rr2", "rr3"])
        self.assertEqual(inventory["exp01"]["source_file"], "summary_all.csv")

    def test_find_prohibited_claims_flags_a_trained_exp05_estimator(self) -> None:
        try:
            from iclr2027.audit import find_prohibited_claims
        except ImportError as exc:
            self.fail(f"claim audit function is missing: {exc}")

        issues = find_prohibited_claims(
            "Exp05 relies on a quality estimator trained on exp02 data from the same model."
        )

        self.assertEqual(issues, ["exp05_trained_estimator"])

    def test_find_prohibited_claims_flags_unfinished_or_overstated_paper_claims(self) -> None:
        from iclr2027.audit import find_prohibited_claims

        issues = find_prohibited_claims(
            "We conduct a human evaluation. The expert evaluator rates 30 samples. "
            "Experiment 07 uses 3 repeats per model. This is the first systematic study "
            "through 14 topologies."
        )

        self.assertEqual(
            issues,
            [
                "unfinished_human_study_as_completed",
                "uniform_exp07_repeats",
                "unsupported_first_systematic",
                "ambiguous_fourteen_topologies",
            ],
        )

    def test_checked_in_paper_sources_pass_claim_audit_and_share_exp07_counts(self) -> None:
        from iclr2027.audit import find_prohibited_claims

        root = Path(__file__).parents[1]
        sources = {
            "paper_draft.md": root / "paper_draft.md",
            "paper_draft_kr.md": root / "paper_draft_kr.md",
            "latex/main.tex": root / "latex" / "main.tex",
        }
        for name, path in sources.items():
            with self.subTest(source=name):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(find_prohibited_claims(text), [])
                self.assertIn("743", text)
                self.assertNotIn("669", text)

        self.assertIn("6 models", sources["paper_draft.md"].read_text(encoding="utf-8"))
        self.assertIn("6개 모델", sources["paper_draft_kr.md"].read_text(encoding="utf-8"))
        self.assertIn("6 models", sources["latex/main.tex"].read_text(encoding="utf-8"))

    def test_validate_exp01_accepts_complete_multi_agent_export(self) -> None:
        from validate_results import validate_exp01

        multi_agent_patterns = {
            "rr2",
            "rr3",
            "rr4",
            "sel3",
            "sel4",
            "swm3",
            "swm4",
            "refl2",
            "refl3",
            "debate3",
            "debate4",
            "pipe",
            "moa",
        }
        with tempfile.TemporaryDirectory() as tmp:
            exp01 = Path(tmp)
            self._write_summary(exp01 / "summary.csv", ["solo", "rr3"])
            self._write_summary(exp01 / "summary_all.csv", sorted(multi_agent_patterns))

            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    valid = validate_exp01(
                        exp_dir=exp01,
                        expected_patterns=multi_agent_patterns,
                        expected_per_pattern=1,
                    )
                except TypeError as exc:
                    self.fail(f"validator does not support an isolated result directory: {exc}")

        self.assertTrue(valid)

    @staticmethod
    def _write_summary(path: Path, patterns: list[str]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["pattern", "total_tokens", "error"])
            writer.writeheader()
            for pattern in patterns:
                writer.writerow({"pattern": pattern, "total_tokens": 100, "error": ""})


if __name__ == "__main__":
    unittest.main()
