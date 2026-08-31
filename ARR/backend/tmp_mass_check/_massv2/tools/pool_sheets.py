"""Every physics-passing mass of a run, drawn - so a person can actually look.

The selection showed 12 of 3,482 and the user rightly asked to see the rest:
the pool had eleven hundred masses of five storeys and more that no sheet
ever surfaced. This renders the WHOLE plausible pool as numbered contact
sheets (48 tiles each), ordered tall-first within family order, with storeys
and FAR on every tile - the browsing surface for a human sweep and for
auditor subagents.

    python tools/pool_sheets.py <run> [out-dir-name]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from band_probe import corpus, schedule_of  # noqa: E402
from finalists import PNU, rebuild  # noqa: E402

from design.maas.massv2.legal import load_legal_site  # noqa: E402
from design.maas.massv2.render import render_masses  # noqa: E402
from design.maas.massv2.siting import open_side_direction  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# The sheet's geometry in one place: anyone cropping a tile back out of a
# rendered sheet (probe_pair) reads these, so they may never drift apart.
PER_SHEET = 48
COLUMNS = 8
TILE = (300, 270)


def main(run: str, out_name: str = "", mode: str = "") -> int:
    heroes = mode == "--heroes"
    summary = json.loads((ROOT / "runs" / run / "massv2-summary.json")
                         .read_text(encoding="utf-8"))
    book = corpus()
    schedule = schedule_of(run)
    site = load_legal_site(PNU, building_type="제1종근린생활시설")
    buildable = site.plan_at(0.0)
    axis = open_side_direction(buildable, site.shared_edges) or (1.0, 0.0)
    base = site.floor_height_m * max(
        1, int(site.far_capacity_m2 // max(1.0, site.ground_capacity_m2)))
    parcel = float(summary["site"]["parcel_area_m2"])

    rows = []
    for record in summary["records"]:
        if not (record.get("plausibility") or {}).get("occupiable"):
            continue
        fit = record.get("legal_fit") or {}
        ground = float(fit.get("ground_area_m2") or 0.0)
        gross = float(fit.get("gross_floor_area_m2") or 0.0)
        storeys = gross / ground if ground > 1e-6 else 0.0
        rows.append((storeys, gross, record["name"]))
    rows.sort(reverse=True)  # tall first - the under-served end leads

    variants: dict[str, int] = {}
    family_tag: dict[str, str] = {}
    if heroes:
        # One tile per sentence, its tallest variant standing for the rest.
        # 94% of the pool is coverage/siting re-tags, and rank order lays a
        # sentence's ~21 near-identical tags side by side - a browsing surface
        # that looks like duplication whatever the corpus holds. Grouping by
        # composition family also makes authoring convergence visible: same
        # family, adjacent tiles, no caption reading needed.
        from family_key import family_key  # noqa: E402
        best: dict[str, tuple[float, float, str]] = {}
        for storeys, gross, name in rows:
            sentence = name.split("~")[0].split("^")[0]
            variants[sentence] = variants.get(sentence, 0) + 1
            if sentence not in best:
                best[sentence] = (storeys, gross, name)
        for sentence in best:
            if sentence in book:
                opener, moves, stature = family_key(book[sentence])
                family_tag[sentence] = (
                    f"{opener}/{next(iter(moves), '-')}/{stature}")
        rows = sorted(
            (best[s] for s in best if s in book),
            key=lambda item: (
                family_tag[item[2].split("~")[0].split("^")[0]], -item[0]))

    out = ROOT / "runs" / (out_name or f"pool-{run}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "pool-index.json").write_text(json.dumps(
        [{"rank": i + 1, "storeys": round(s, 1), "name": n}
         for i, (s, _g, n) in enumerate(rows)],
        ensure_ascii=False, indent=1), encoding="utf-8")

    batch, sheet, drawn, failed = [], 0, 0, 0
    for index, (storeys, gross, name) in enumerate(rows, start=1):
        family = name.split("~")[0].split("^")[0]
        parti = book.get(family)
        if parti is None:
            failed += 1
            continue
        asked = max((float(op.get("storeys") or 0) for op in parti["ops"]),
                    default=0.0)
        source = rebuild(name, book, site, buildable, axis,
                         max(base, asked * site.floor_height_m),
                         schedule=schedule)
        if source is None:
            failed += 1
            continue
        drawn += 1
        meta = {
            "층": f"{storeys:.1f}", "용적": f"{gross / parcel * 100:.0f}%",
            "": family[:24],
        }
        if heroes:
            meta["안"] = str(variants.get(family, 1))
            meta[""] = f"{family_tag.get(family, '?')[:20]} {family[:16]}"
        batch.append((f"#{index}", source, meta))
        if len(batch) == PER_SHEET:
            sheet += 1
            render_masses(batch, out / f"pool{sheet:03d}.png",
                          site_ring=list(buildable.exterior.coords),
                          columns=COLUMNS, tile=TILE, style="massing")
            print(f"pool{sheet:03d}.png  ({drawn}/{len(rows)})", flush=True)
            batch = []
    if batch:
        sheet += 1
        render_masses(batch, out / f"pool{sheet:03d}.png",
                      site_ring=list(buildable.exterior.coords),
                      columns=COLUMNS, tile=TILE, style="massing")
    print(f"done: {drawn} drawn, {failed} rebuild-failed, {sheet} sheets -> {out}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(*sys.argv[1:4]))
