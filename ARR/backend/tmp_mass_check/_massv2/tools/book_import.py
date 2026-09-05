"""Bring BOOK-stack masses to the massv2 jury.

Two pipelines, one shared IR: book_language compiles its 70-principle
vocabulary into the same SourceMass that massv2's post-compile funnel
consumes. This tool replays a book run's exact geometry artifacts
(GeometryProgram AST -> SourceMass on this parcel's legal host) and
stages them as anonymous jury tiles - PROMPT.txt, tNN.png, key.json,
with three current board seats riding as anchors - exactly the stage
layout judge.sh/score.sh already speak. Book masses then face the same
blind eyes as every massv2 family, which is what "use the book" means.

    python tools/book_import.py <book-run-dir> <stage-name>
    # e.g. python tools/book_import.py ../c250-t3 book01
    # then: judge with skills/mass-judge (stage name book01)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[1]


BOOKS = ROOT / "runs" / "books"


def records_of(book_dir: Path) -> list[dict]:
    """Every BOOK record in a run directory, whichever era wrote it.

    The exploration command has two output shapes. The older run wrote one
    `maas-book-exact-geometry-artifacts.json` holding records with a
    `geometry_artifact`; the current one writes a portfolio plus one JSON per
    candidate, each with its `geometry_program` directly. Both are BOOK masses
    and the board judges both, so the reader takes either.
    """

    old = book_dir / "maas-book-exact-geometry-artifacts.json"
    if old.exists():
        return list(json.loads(old.read_text(encoding="utf-8")).get("records") or [])
    portfolio = book_dir / "maas-creative-portfolio.json"
    if not portfolio.exists():
        return []
    entries = json.loads(portfolio.read_text(encoding="utf-8")).get("candidates") or []
    records = []
    for entry in entries:
        path = book_dir / str(entry.get("candidate_json") or "")
        if not path.exists():
            continue
        candidate = json.loads(path.read_text(encoding="utf-8"))
        program = candidate.get("geometry_program")
        if not program:
            continue
        floors = (candidate.get("storey_evidence") or {}).get("actual_floor_areas_m2")
        if not floors:
            # Without the book's own plan size the shared compile fits the
            # plan to the legal host, which is how a 209 m2 book was once
            # staged at 705 m2. Skipped loudly rather than judged at a size
            # nobody authored.
            import sys as _sys
            print(f"  skip {entry.get('candidate_id')}: no floor areas",
                  file=_sys.stderr)
            continue
        # The portfolio's own words for what this candidate is: the family it
        # came from and the BOOK principle it was assigned. That is the thesis
        # a juror reads, and without it the tile carries a hash.
        assignment = (program.get("metadata") or {}).get(
            "creative_book_assignment") or {}
        principle = str(assignment.get("principle_id") or "")
        verbs = ", ".join(str(v) for v in (assignment.get("execution_verbs") or ()))
        family = str(candidate.get("family") or entry.get("family") or "")
        records.append({
            # The run id is part of the identity. Candidate ids restart at
            # creative-001 every exploration, so without it two runs mint the
            # same sixty keys and the registry - a flat merge of every
            # runs/books/*.json - hands the baker whichever sorted last.
            "trace_sequence_name":
                f"{book_dir.name}:{family}:{entry.get('candidate_id')}",
            "thesis": (
                f"{family.replace('_', ' ')} - "
                f"{verbs or 'base'}"
                + (f" ({principle.split(':')[-1]})" if principle else "")
            ),
            "geometry_artifact": {
                "authoredGeometryProgram": program,
                # The portfolio states the physical height as the top of the
                # mesh bounds and the storeys it was cut into; the older
                # artifact carried a certificate instead. Both are the book's
                # own account of how tall it is, which is what the height
                # dialect below needs - without one every book mass measured
                # 0.0 m and drew flat.
                "projectedVisualCertificate": {
                    "physical_height_m": float(
                        ((candidate.get("mesh_evidence") or {}).get("bounds")
                         or [[0, 0, 0], [0, 0, 0]])[1][2] or 0.0),
                },
                "hardGates": {"projectedMetrics": {
                    "footprint_area_m2": float(
                        ((candidate.get("storey_evidence") or {}).get(
                            "actual_floor_areas_m2") or [0.0])[0] or 0.0),
                    # The book's own gross, summed over its own floors at its
                    # own storey height. Left unset, the caption fell back to
                    # measuring the delivered bands at the parcel's storey -
                    # the very reading the height dialect below exists to
                    # avoid - and all sixty tiles went to the jury with a
                    # 용적률 taken on the wrong ruler.
                    "floor_area_m2": float(sum(
                        (candidate.get("storey_evidence") or {}).get(
                            "actual_floor_areas_m2") or ())),
                }},
            },
        })
    return records


# What share of the parcel's 용적률 capacity a book mass is brought to. Not the
# whole of it: an authored scheme that fills the cap is making a claim about
# density, and a book figure makes no such claim - it states a proportion. Four
# fifths puts it in the same conversation as the schemes it is judged against
# without pretending it was designed for this brief.
BOOK_FAR_SHARE = 0.8

# And the ceiling on its footprint, as a share of the 건폐율 capacity. A book
# figure taken to the full coverage ceiling would be a different figure - the
# whole parcel wearing a cross - so it stops here and takes the rest in height.
BOOK_GROUND_SHARE = 0.75


def _to_parcel_size(footprint_m2: float, gross_m2: float, height_m: float,
                    site) -> tuple[float, float]:
    """The book's figure at this parcel's size: (plan area, height).

    One uniform factor, so every proportion the book states survives it. Gross
    floor area goes as plan area times floor count, and a uniform scale s
    multiplies plan by s squared and height (so floors) by s, which is why the
    factor is the cube root of the ratio wanted.
    """

    if site is None or footprint_m2 <= 1e-6 or gross_m2 <= 1e-6 or height_m <= 1e-6:
        return footprint_m2, height_m
    target = float(site.far_capacity_m2) * BOOK_FAR_SHARE
    scale = (target / gross_m2) ** (1.0 / 3.0)
    ground_cap = float(site.ground_capacity_m2) * BOOK_GROUND_SHARE
    if footprint_m2 * scale * scale > ground_cap:
        scale = (ground_cap / footprint_m2) ** 0.5
    # A book taller than the parcel's own legal section is not this parcel's
    # building; the envelope would cut it to one anyway, and cutting is what
    # made these read as fragments in the first place.
    ceiling = float(site.floor_height_m) * max(
        1.0, float(site.far_capacity_m2) / max(float(site.ground_capacity_m2), 1.0)) * 2.0
    if height_m * scale > ceiling:
        scale = ceiling / height_m
    return footprint_m2 * scale * scale, height_m * scale


def _compile_record(rec: dict, buildable, site=None):
    """One book record -> SourceMass, the book's figure at this parcel's size.

    The single path the stage and the board's baker share, so a seated
    book mass is rebuilt exactly as it was judged. Returns (source, entry)
    or (None, reason); `entry` is what the registry records about it.
    """

    from dataclasses import replace  # noqa: E402
    from design.maas.geometry_language.ast import GeometryProgram  # noqa: E402
    from design.maas.geometry_language.source_bridge import (  # noqa: E402
        compile_geometry_program_to_source_mass,
    )

    art = rec.get("geometry_artifact") or {}
    payload = art.get("authoredGeometryProgram") or art.get("geometryProgram")
    if not payload:
        return None, "no geometry program"
    metrics = ((art.get("hardGates") or {}).get("projectedMetrics") or {})
    footprint_m2 = float(metrics.get("footprint_area_m2") or 0.0)
    book_gross_m2 = float(metrics.get("floor_area_m2") or 0.0)
    book_height_m = float(
        (art.get("projectedVisualCertificate") or {}).get("physical_height_m")
        or metrics.get("height_m") or 0.0)
    # The figure is the book's, the size is the parcel's.
    footprint_m2, scaled_height_m = _to_parcel_size(
        footprint_m2, book_gross_m2, book_height_m, site)
    try:
        program = GeometryProgram.from_dict(payload)
        # At the book's own plan size. Left to its default the shared
        # compile fits the plan to the legal host, and the book's 209 m2
        # footprint was staged at 705 m2 under the book's 35 m - a tower
        # 3.4x the certificate's, captioned 270% on a 250% parcel.
        source = compile_geometry_program_to_source_mass(
            program, buildable, name=rec.get("trace_sequence_name"),
            target_plan_area=footprint_m2 or None,
            minimum_plan_area=footprint_m2 or None)
    except Exception as exc:  # a book record that no longer compiles is news, not a crash
        return None, f"{type(exc).__name__}: {exc}"
    if source is None:
        return None, "compiled to None"
    # The height dialect. massv2's measure, gates and renderer read
    # `metadata["authored_height_m"]`; the book stamps its physical height
    # as a certificate on the artifact instead, and the shared compile
    # leaves the volumes as fractions of an unstated whole - so every book
    # mass measured 0.0 m and drew flat. Translated once, from the book's
    # own certificate, never from a guess.
    height_m, certificate = 0.0, ""
    for label, value in (
            ("projectedVisualCertificate.physical_height_m",
             (art.get("projectedVisualCertificate") or {}).get("physical_height_m")),
            ("hardGates.projectedMetrics.height_m", metrics.get("height_m")),
            ("capacityAlternative.candidate_requested_height_m",
             (art.get("capacityAlternative") or {}).get("candidate_requested_height_m"))):
        if value:
            height_m, certificate = float(value), label
            break
    if height_m <= 0.0:
        return None, "no physical height certificate"
    # Scaled with the plan, so the book's proportion survives.
    if scaled_height_m > 0.0:
        height_m = scaled_height_m
    source = replace(source, metadata={**dict(source.metadata),
                                       "authored_height_m": round(height_m, 3),
                                       "book_height_certificate": certificate})
    verbs = list(((payload.get("metadata") or {}).get("book_recursive_projection") or {})
                 .get("ordered_verbs") or [])
    entry = {
        "trace": rec.get("trace_sequence_name"),
        # What the tile says about itself. The portfolio reader writes a
        # sentence ("courtyard - inscribe (11)"); the older artifact carries a
        # principle id. Either beats the literal words "book principle", which
        # is what every one of sixty tiles was captioned with.
        "thesis": str(rec.get("thesis")
                      or art.get("bookPrincipleId")
                      or art.get("bookScope") or "book principle"),
        "verbs": verbs,
        "height_m": round(height_m, 2),
        "footprint_m2": round(footprint_m2, 2),
        # The book's gross at the size it was actually staged. Recorded
        # unscaled, the caption printed the toy's 용적률 beside the scaled
        # mass - 40% coverage next to 42% floor area ratio, which is
        # arithmetically impossible on any parcel. Gross goes as the cube of
        # a uniform scale, and the height ratio is that scale.
        "floor_area_m2": round(
            float(metrics.get("floor_area_m2") or 0.0)
            * ((height_m / book_height_m) ** 3 if book_height_m > 1e-6 else 1.0), 2),
        "program": art.get("programType"),
    }
    return source, entry


def _refused(source, site) -> str:
    """Why this mass cannot be judged, or an empty string.

    Standing first - a body with nothing under it is not a proposal - then the
    room rule, which is what separates a building from a sculpture at this
    scale.
    """

    from design.maas.massv2.plausibility import assess as plausibility_of  # noqa: E402
    from design.maas.massv2.structure import assess_standing  # noqa: E402

    from design.maas.massv2.plausibility import slenderness_limit  # noqa: E402

    height_m = float(source.metadata.get("authored_height_m") or 0.0)
    try:
        standing = assess_standing(source, height_m=height_m)
    except Exception as exc:  # noqa: BLE001 - a gate that crashes is news
        return f"standing check failed ({type(exc).__name__}: {exc})"
    if not getattr(standing, "stands", True):
        reasons = list(getattr(standing, "reasons", ()) or ())
        return f"does not stand ({'; '.join(str(r) for r in reasons[:2]) or 'no reason'})"
    try:
        plausible = plausibility_of(
            source,
            parcel_area_m2=float(site.parcel_area_m2),
            max_slenderness=slenderness_limit(
                far_capacity_m2=float(site.far_capacity_m2),
                ground_capacity_m2=float(site.ground_capacity_m2)),
            floor_height_m=float(site.floor_height_m))
    except Exception as exc:  # noqa: BLE001
        return f"room check failed ({type(exc).__name__}: {exc})"
    if not plausible.occupiable:
        reasons = list(getattr(plausible, "reasons", ()) or ())
        return f"no room in it ({'; '.join(str(r) for r in reasons[:2])})"
    return ""


def registry() -> dict:
    """Every staged book mass, by its `book:` name -> {book_dir, ...entry}."""

    found: dict = {}
    if BOOKS.exists():
        for path in sorted(BOOKS.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for name, entry in (data.get("entries") or {}).items():
                found[name] = {**entry, "book_dir": data["book_dir"]}
    return found


def book_rebuild(name: str, site, buildable):
    """A seated book mass, rebuilt exactly as it was judged (for the baker)."""

    entry = registry().get(name)
    if entry is None:
        return None
    # `records_of` reads whichever shape the run wrote; the old artifact file
    # was being opened unconditionally beside it, so a seat imported from a
    # portfolio run could be judged and then not baked.
    artifacts = {"records": records_of(Path(entry["book_dir"]))}
    rec = next((r for r in artifacts.get("records") or []
                if r.get("trace_sequence_name") == entry["trace"]), None)
    if rec is None:
        return None
    source, _entry = _compile_record(rec, buildable, site)
    return source


def main() -> int:
    book_dir = Path(sys.argv[1])
    if not book_dir.is_absolute():
        book_dir = (ROOT / book_dir).resolve()
    stage_name = sys.argv[2]

    from band_probe import corpus  # noqa: E402,F401  (django setup side effect)
    from finalists import PNU, BUILDING_TYPE  # noqa: E402
    from vlm_shortlist import certified_caption, ride_anchors, shape_id  # noqa: E402
    from design.maas.massv2.legal import load_legal_site  # noqa: E402
    from design.maas.massv2.render import render_masses  # noqa: E402

    records = records_of(book_dir)
    if not records:
        print("FAIL: no records in book artifacts")
        return 1

    site = load_legal_site(PNU, building_type=BUILDING_TYPE)
    buildable = site.plan_at(0.0)

    out = ROOT / "runs" / f"vlm-{stage_name}"
    out.mkdir(parents=True, exist_ok=True)
    for stale in list(out.glob("t*.png")) + [out / r for r in ("r1.txt", "r2.txt", "r3.txt")]:
        Path(stale).unlink(missing_ok=True)

    key_rows: list[dict] = []
    entries: dict = {}
    index = 0
    for rec in records:
        source, entry = _compile_record(rec, buildable, site)
        if source is None:
            print(f"  skip {rec.get('trace_sequence_name')}: {entry}")
            continue
        # The same questions every authored mass answers before it is drawn.
        # A book mass skipped all of them and went straight to the jury, so a
        # `lift` whose supports the compile dropped arrived as a slab floating
        # over an empty parcel - 14% coverage, nothing under it - and a juror
        # was asked to score it as architecture. One ruler for everything.
        refusal = _refused(source, site)
        if refusal:
            print(f"  skip {rec.get('trace_sequence_name')}: {refusal}")
            continue
        index += 1
        tile = f"t{index:02d}"
        name = f"book:{rec.get('trace_sequence_name') or tile}"
        # 건폐율/용적률 from the book's own certificate: it counts floors at
        # its own storey height (35 m / 10 floors), which massv2's per-band
        # rounding at the parcel storey cannot reproduce on three fat bands.
        render_masses([(tile, source, certified_caption(
                           source, site, entry["thesis"],
                           ground_m2=entry["footprint_m2"] or None,
                           gross_m2=entry["floor_area_m2"] or None))],
                      out / f"{tile}.png", site_ring=list(buildable.exterior.coords),
                      columns=1, tile=(900, 820), style="massing")
        key_rows.append({"tile": tile, "name": name, "height_m": entry["height_m"],
                         "shape_id": shape_id(source)})
        entries[name] = entry
    # The registry: how the curator keys a book mass and how the baker
    # rebuilds it once seated. Written per stage, read as a whole.
    BOOKS.mkdir(parents=True, exist_ok=True)
    (BOOKS / f"{stage_name}.json").write_text(
        json.dumps({"book_dir": str(book_dir), "entries": entries},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    if not key_rows:
        print("FAIL: no book record compiled")
        return 1

    # The overseas rubric, from its owner (vlm_shortlist.rubric_for) - never retyped here.
    from vlm_shortlist import BLIND_PREAMBLE, rubric_for  # noqa: E402
    (out / "PROMPT.txt").write_text(BLIND_PREAMBLE + rubric_for("overseas"), encoding="utf-8")

    # Three board seats ride as anchors - the same ride, rebuild and caption
    # every massv2 round uses (vlm_shortlist.ride_anchors owns it).
    ride_anchors(out, key_rows, site=site)

    (out / "key.json").write_text(json.dumps(key_rows, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
    candidates = sum(1 for r in key_rows if "anchor" not in r)
    print(f"{len(key_rows)} tiles staged ({candidates} book + "
          f"{len(key_rows) - candidates} anchors) -> {out}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
