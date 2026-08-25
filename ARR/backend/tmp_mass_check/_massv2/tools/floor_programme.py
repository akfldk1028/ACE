"""Which room lands on which floor, and what the mass cannot carry.

A massing sheet answers "how big and what shape". A competition asks the next
question immediately - what is on each floor - and the 실별 소요면적표 already
holds the answer if the brief's own placement rules are read rather than
guessed. 효돈동's brief writes three of them:

    대회의실 천정고 최소 4m 이상
    공용부는 최소 30% 이상 설계
    일시에 다중이 모이는 공간은 피난층과 인접 배치

So the hall goes low, not on top - this brief is on the 피난 side of the split
the survey found (만수6동 puts its 대강당 on the top floor for structure and
noise; 효돈동 and 고전면 put the crowd next to the escape). Rooms marked
`needs_ground` take the ground floor first, the hall takes the lowest floor
that still has room for it, and the rest fill upward largest first.

Service rooms are reported separately rather than placed. The brief builds
지하1/지상3 and every surveyed competition puts plant and stores in that
basement - twelve of twelve, without exception, because a 5.5 m column-free
span underground drags excavation, shoring, smoke control and escape behind
it. This pipeline has no basement, so the honest line is that these 271 m2
are not in the mass rather than a floor invented for them.

    python tools/floor_programme.py <run>
"""

import json
import sys
from pathlib import Path

from finalists import PNU, scheme_of  # noqa: E402  (django setup inside)

from design.maas.massv2 import program as programme  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "inputs" / "programs-korean.json"


def allocate(schedule, *, gfa_m2: float, floors: int, shared_share: float):
    """Rooms per floor, and what did not fit.

    Returns (floors, unplaced, basement) where `floors` is a list of
    {"storey": n, "usable_m2": x, "rooms": [...]} from the ground up.
    """

    usable = max(gfa_m2 * (1.0 - shared_share) / max(floors, 1), 1.0)
    plan = [{"storey": n + 1, "usable_m2": round(usable, 1), "rooms": [],
             "used_m2": 0.0} for n in range(max(floors, 1))]

    def put(level, room, area):
        plan[level]["rooms"].append({"name": room.name, "area_m2": round(area, 1),
                                     "kind": room.kind, "zone": room.zone})
        plan[level]["used_m2"] = round(plan[level]["used_m2"] + area, 1)

    def fits(level, area):
        return plan[level]["used_m2"] + area <= plan[level]["usable_m2"] + 1e-6

    basement, unplaced = [], []
    rooms = sorted(schedule.rooms, key=lambda r: -r.total_m2)

    # 지하: plant and stores, as every surveyed brief builds them.
    for room in list(rooms):
        if room.kind == "service":
            basement.append({"name": room.name, "area_m2": round(room.total_m2, 1)})
            rooms.remove(room)

    # 피난층: the counter and anything the brief marks as reachable without
    # passing through the building, then the crowd space next to it.
    for room in list(rooms):
        if room.needs_ground:
            put(0, room, room.total_m2)
            rooms.remove(room)
    for room in list(rooms):
        if room.kind == "large_span":
            level = next((n for n in range(len(plan)) if fits(n, room.total_m2)), None)
            if level is None:
                unplaced.append({"name": room.name, "area_m2": round(room.total_m2, 1),
                                 "why": "어느 층도 이 대공간을 담지 못함"})
            else:
                put(level, room, room.total_m2)
            rooms.remove(room)

    for room in rooms:
        level = next((n for n in range(len(plan)) if fits(n, room.total_m2)), None)
        if level is None:
            unplaced.append({"name": room.name, "area_m2": round(room.total_m2, 1),
                             "why": "남은 층 면적 부족"})
        else:
            put(level, room, room.total_m2)
    return plan, unplaced, basement


def main(run: str, programme_name: str = "효돈동 주민센터") -> int:
    folder = ROOT / "runs" / run
    summary = json.loads((folder / "massv2-summary.json").read_text(encoding="utf-8"))
    picks = json.loads((folder.parent / f"{run}-pick" / "picks.json")
                       .read_text(encoding="utf-8"))["picks"]
    records = {r["name"]: r for r in summary["records"]}

    book = json.loads(BOOK.read_text(encoding="utf-8"))
    share = book.get("shared_area_share_of_gross") or {}
    share = float(share.get("min") or 0.30) if isinstance(share, dict) else float(share)
    record = next(r for r in book["schedules"] if r.get("name") == programme_name)
    schedule = programme.schedule_from_record(record, shared_share_of_gross=share)

    out = []
    for p in picks:
        rec = records.get(p["name"]) or {}
        storey = float(rec.get("floor_height_m") or 3.0)
        floors = max(1, round(float(p["height_m"] or 0.0) / max(storey, 1.0)))
        plan, unplaced, basement = allocate(
            schedule, gfa_m2=float(rec.get("gfa_m2") or 0.0),
            floors=floors, shared_share=share,
        )
        out.append({"id": p["id"], "family": p["family"], "floors": floors,
                    "plan": plan, "unplaced": unplaced, "basement": basement})

    path = folder.parent / f"{run}-pick" / "programme.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    short = [r for r in out if r["unplaced"]]
    print(f"{len(out)} picks, {len(short)} cannot hold the brief")
    for r in short[:8]:
        names = ", ".join(u["name"] for u in r["unplaced"])
        print(f"  #{r['id']:02d} {r['family'][:32]:<32} {r['floors']}층  못 담음: {names}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], *(sys.argv[2:3] or [])))
