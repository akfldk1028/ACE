"""Bake the board's tiles and track sheets from board-key.json.

The board was re-baked by hand once (rule 0: after an executor change the
tiles are re-rendered before anyone looks). Republishing is a routine now,
so the baking is a tool: every overseas entry is rebuilt with the code as it
stands and drawn as a single tile plus its place in the track sheet. Korean
entries are rebuilt the same way when their brief is available; otherwise an
existing tile is kept and reported, never silently redrawn from the wrong
schedule.

    python tools/board_render.py            # rebake O tiles + both sheets
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from band_probe import corpus  # noqa: E402
from finalists import PNU, rebuild  # noqa: E402

from design.maas.massv2.legal import load_legal_site  # noqa: E402
from design.maas.massv2.render import render_masses  # noqa: E402
from design.maas.massv2.siting import open_side_direction  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "runs" / "board"
TILE = (880, 740)
SHEET_TILE = (440, 370)
SHEET_COLUMNS = 4
# The board's parcel is 효돈동 and its Korean track is sized to this brief -
# the same 과업 the Korean rubric names. Loaded from programs-korean.json,
# never typed as numbers here.
KOREA_BRIEF = "효돈동 주민센터"


def _korea_schedule():
    from design.maas.massv2 import program as programme
    book = json.loads((ROOT / "inputs" / "programs-korean.json")
                      .read_text(encoding="utf-8"))
    record = next((r for r in book["schedules"]
                   if r.get("name") == KOREA_BRIEF), None)
    if record is None:
        return None
    return programme.schedule_from_record(
        record, shared_share_of_gross=book.get("shared_area_share_of_gross"))


def main() -> int:
    board = json.loads((BOARD / "board-key.json").read_text(encoding="utf-8"))
    book = corpus()
    site = load_legal_site(PNU, building_type="제1종근린생활시설")
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    base = site.floor_height_m * max(
        1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))

    korea_schedule = _korea_schedule()
    per_track: dict[str, list] = {"K": [], "O": [], "C": []}
    kept, baked = 0, 0
    for row in board:
        track = row["label"][0]
        family = row["name"].split("~")[0].split("^")[0]
        parti = book.get(family)
        source = None
        if parti is not None and (track in ("O", "C") or korea_schedule is not None):
            asked = max((float(op.get("storeys") or 0)
                         for op in parti["ops"]), default=0.0)
            source = rebuild(row["name"], book, site, buildable, axis,
                             max(base, asked * site.floor_height_m),
                             schedule=korea_schedule if track == "K" else None)
        if source is None:
            existing = BOARD / f"{row['label']}.png"
            if existing.exists():
                kept += 1
                per_track[track].append((row["label"], None, existing))
                continue
            print(f"missing and unbakeable: {row['label']} {row['name']}")
            continue
        baked += 1
        meta = {"": f"{row['score']:.2f}" if row.get("score") is not None else "전형"}
        render_masses([(row["label"], source, meta)],
                      BOARD / f"{row['label']}.png",
                      site_ring=list(buildable.exterior.coords),
                      columns=1, tile=TILE, style="massing")
        per_track[track].append((row["label"], source, None))

    from PIL import Image
    for track in ("K", "O", "C"):
        entries = per_track[track]
        if not entries:
            continue
        columns = SHEET_COLUMNS
        rows = (len(entries) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * SHEET_TILE[0],
                                  rows * SHEET_TILE[1]), "white")
        for i, (label, _source, existing) in enumerate(entries):
            tile_path = existing or (BOARD / f"{label}.png")
            tile = Image.open(tile_path).resize(SHEET_TILE)
            sheet.paste(tile, ((i % columns) * SHEET_TILE[0],
                               (i // columns) * SHEET_TILE[1]))
        sheet.save(BOARD / f"sheet_{track}.png")
    print(f"baked {baked}, kept {kept} -> {BOARD}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
