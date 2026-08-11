"""Read a benchmark run directory and report what actually reached the board.

Reports the two things this session is changing:
  - gates: does the mass clear combined_hard_pass (the regression guard)
  - reach: how much of the form bank the truncated head actually covered
"""

import json
import sys
from collections import Counter
from pathlib import Path


def load(run_dir, name):
    path = Path(run_dir) / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_rows(payload):
    """Find the list of selected candidate records, whatever it is nested in."""

    found = []

    def walk(node):
        if isinstance(node, dict):
            if "projectedVisualGeometryHash" in node or "combined_hard_pass" in node:
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


def main(run_dir):
    print(f"=== {run_dir} ===")
    summary = load(run_dir, "maas-book-programs-summary.json")
    evaluation = load(run_dir, "maas-portfolio-evaluation.json")

    for label, payload in (("summary", summary), ("evaluation", evaluation)):
        if payload is None:
            print(f"  {label}: MISSING")
            continue
        rows = flatten_rows(payload)
        if not rows:
            continue
        gates = Counter(bool(row.get("combined_hard_pass")) for row in rows)
        print(f"  {label}: {len(rows)} rows, combined_hard_pass {dict(gates)}")

        for key in (
            "source_seed",
            "geometry_family",
            "family",
            "base_seed",
            "form_bank_lane",
            "chassis_family",
        ):
            values = [str(row[key]) for row in rows if row.get(key)]
            if values:
                print(f"    {key}: {len(set(values))} distinct -> "
                      f"{Counter(values).most_common(8)}")

        # design_concept is a descriptor dict; its concept_key is the readable
        # summary of base seed / ground / body / roof strategy.
        for field in ("concept_key", "base_seed", "ground_strategy",
                      "body_strategy", "roof_section_strategy"):
            values = []
            for row in rows:
                concept = row.get("design_concept")
                if isinstance(concept, str):
                    try:
                        concept = json.loads(concept.replace("'", '"'))
                    except (ValueError, TypeError):
                        concept = None
                if isinstance(concept, dict) and concept.get(field):
                    values.append(str(concept[field]))
            if values:
                print(f"    concept.{field}: {len(set(values))} distinct -> "
                      f"{Counter(values).most_common(8)}")

        hashes = sorted({
            str(row["projectedVisualGeometryHash"])
            for row in rows
            if row.get("projectedVisualGeometryHash")
        })
        if hashes:
            import hashlib
            digest = hashlib.sha256("".join(hashes).encode()).hexdigest()[:16]
            print(f"    geometry-hash digest: {digest} ({len(hashes)} distinct)")

    for key in ("evaluated_count", "program_passed_count", "selected_count",
                "selected_scope_count", "failure_reason", "status"):
        for payload in (summary, evaluation):
            if isinstance(payload, dict) and key in payload:
                print(f"  {key}: {payload[key]}")
                break


if __name__ == "__main__":
    for target in sys.argv[1:]:
        main(target)
