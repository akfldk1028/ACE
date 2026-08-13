"""Report the delivered ground-take x void grid for one or more runs.

The run writes the joint axis into `selection_pool_ground_takes` (the pool the
solver chose from) and `post_rebalance_ground_takes` (what shipped), keyed as
`ground_take:<band>|void:<band>`. This prints them as the grid so two runs can
be compared.

Usage: python tmp_mass_check/report_grid.py tmp_mass_check/c248-t3 tmp_mass_check/c249-t3
"""

import json
import pathlib
import sys


GROUND = ["dispersed_ground", "held_ground", "worked_ground", "full_ground"]
VOID = ["solid_body", "carved_body", "open_figure", "porous_field"]


def _collect(node, key, found):
    if isinstance(node, dict):
        if key in node:
            found.append(node[key])
        for value in node.values():
            _collect(value, key, found)
    elif isinstance(node, list):
        for value in node:
            _collect(value, key, found)


def _read(run_dir, key):
    found = []
    for path in sorted(pathlib.Path(run_dir).glob("*.json")):
        try:
            _collect(json.loads(path.read_text(encoding="utf-8")), key, found)
        except (ValueError, OSError):
            continue
    return found[0] if found else None


def _split(cell):
    take, _, void = str(cell).partition("|void:")
    return take.replace("ground_take:", ""), void


def report(run_dir):
    pool = _read(run_dir, "selection_pool_ground_takes") or {}
    shipped = _read(run_dir, "post_rebalance_ground_takes") or []

    cells = {}
    for cell, count in pool.items():
        cells[_split(cell)] = count

    print(f"\n=== {run_dir} ===  pool {sum(pool.values())} candidates")
    print(f"{'':<18}" + "".join(f"{name:>14}" for name in VOID))
    for take in GROUND:
        row = "".join(f"{(cells.get((take, void)) or '-'):>14}" for void in VOID)
        print(f"{take:<18}{row}")
    print(f"occupied cells: {len(cells)} / 16")
    print("shipped:", ", ".join(_split(cell)[0] + "|" + _split(cell)[1] for cell in shipped))


def main():
    for run_dir in sys.argv[1:] or ["tmp_mass_check/c249-t3"]:
        report(run_dir)


if __name__ == "__main__":
    main()
