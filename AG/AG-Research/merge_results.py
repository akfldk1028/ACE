"""Merge category-level exp01 results into combined files."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from config import RESULTS_DIR


def merge_exp01():
    exp_dir = RESULTS_DIR / "exp01"
    csv_files = sorted(exp_dir.glob("summary_*.csv"))
    json_files = sorted(exp_dir.glob("raw_*.json"))

    if not csv_files:
        print("No category files to merge.")
        return

    # Merge CSVs
    dfs = [pd.read_csv(f) for f in csv_files]
    combined = pd.concat(dfs, ignore_index=True)
    combined.to_csv(exp_dir / "summary.csv", index=False)
    print(f"Merged {len(csv_files)} CSV files -> {len(combined)} rows -> summary.csv")

    # Merge JSONs
    all_data = []
    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            all_data.extend(json.load(f))
    with open(exp_dir / "raw.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"Merged {len(json_files)} JSON files -> {len(all_data)} runs -> raw.json")


if __name__ == "__main__":
    merge_exp01()
