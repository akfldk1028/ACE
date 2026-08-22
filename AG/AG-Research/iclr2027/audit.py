"""Result-inventory helpers for the ICLR 2027 research track."""

from __future__ import annotations

import csv
import re
from pathlib import Path


def _summary_coverage(path: Path) -> tuple[int, int]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    patterns = {str(row.get("pattern") or "").strip() for row in rows}
    patterns.discard("")
    return len(patterns), len(rows)


def resolve_exp01_summary(exp01_dir: Path | None = None) -> Path:
    """Return the Exp01 summary with the widest pattern coverage.

    Historical reruns left a smaller ``summary.csv`` beside the complete
    multi-agent export.  Selecting by observed coverage prevents validators
    from silently auditing the stale subset.
    """

    if exp01_dir is None:
        from config import RESULTS_DIR

        exp01_dir = RESULTS_DIR / "exp01"

    candidates = [
        path
        for path in (exp01_dir / "summary_all.csv", exp01_dir / "summary.csv")
        if path.exists()
    ]
    if not candidates:
        raise FileNotFoundError(f"no Exp01 summary CSV found in {exp01_dir}")
    return max(candidates, key=_summary_coverage)


def collect_result_inventory(results_dir: Path) -> dict[str, object]:
    """Collect the source and coverage of result sets used by the paper."""

    exp01_path = resolve_exp01_summary(results_dir / "exp01")
    with exp01_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    pattern_ids = sorted(
        {
            str(row.get("pattern") or "").strip()
            for row in rows
            if str(row.get("pattern") or "").strip()
        }
    )
    return {
        "exp01": {
            "source_file": exp01_path.name,
            "row_count": len(rows),
            "pattern_ids": pattern_ids,
        }
    }


_PROHIBITED_CLAIMS = {
    "exp05_trained_estimator": re.compile(
        r"quality estimator\s+trained on\s+exp0?2",
        flags=re.IGNORECASE,
    ),
    "unfinished_human_study_as_completed": re.compile(
        r"(?:we conduct\s+(?:a\s+)?human evaluation|expert evaluator rates)",
        flags=re.IGNORECASE,
    ),
    "uniform_exp07_repeats": re.compile(
        r"(?:experiment\s*0?7[^.]{0,160})?3 repeats per model",
        flags=re.IGNORECASE,
    ),
    "unsupported_first_systematic": re.compile(
        r"\bfirst systematic (?:comparison|study)\b",
        flags=re.IGNORECASE,
    ),
    "ambiguous_fourteen_topologies": re.compile(
        r"\b14 topolog(?:y|ies)\b",
        flags=re.IGNORECASE,
    ),
    "unfinished_korean_human_study_as_completed": re.compile(
        r"전문 평가자가[^\n]{0,160}(?:평가한다|보고한다)",
    ),
    "unsupported_korean_priority_claim": re.compile(
        r"(?:최초로 체계|최초의 체계|선행 연구에 없|선행 연구는 없다)",
    ),
    "stale_exp07_five_model_result": re.compile(r"\b669\b"),
    "ambiguous_inclusive_pattern_count": re.compile(
        r"13 coordination patterns[^\n]{0,100}including a single-agent baseline",
        flags=re.IGNORECASE,
    ),
}


def find_prohibited_claims(text: str) -> list[str]:
    """Return known factual contradictions found in paper prose."""

    return [
        issue
        for issue, pattern in _PROHIBITED_CLAIMS.items()
        if pattern.search(text)
    ]
