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


def _compile_record(rec: dict, buildable, site):
    """One book record -> SourceMass at the book's own size and height.

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
    source = replace(source, metadata={**dict(source.metadata),
                                       "authored_height_m": round(height_m, 3),
                                       "book_height_certificate": certificate})
    verbs = list(((payload.get("metadata") or {}).get("book_recursive_projection") or {})
                 .get("ordered_verbs") or [])
    entry = {
        "trace": rec.get("trace_sequence_name"),
        "thesis": str(art.get("bookPrincipleId") or art.get("bookScope") or "book principle"),
        "verbs": verbs,
        "height_m": round(height_m, 2),
        "footprint_m2": round(footprint_m2, 2),
        "floor_area_m2": round(float(metrics.get("floor_area_m2") or 0.0), 2),
        "program": art.get("programType"),
    }
    return source, entry


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
    artifacts = json.loads((Path(entry["book_dir"]) / "maas-book-exact-geometry-artifacts.json")
                           .read_text(encoding="utf-8"))
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
    from finalists import PNU  # noqa: E402
    from vlm_shortlist import certified_caption, ride_anchors  # noqa: E402
    from design.maas.massv2.legal import load_legal_site  # noqa: E402
    from design.maas.massv2.render import render_masses  # noqa: E402

    artifacts = json.loads(
        (book_dir / "maas-book-exact-geometry-artifacts.json").read_text(encoding="utf-8"))
    records = artifacts.get("records") or []
    if not records:
        print("FAIL: no records in book artifacts")
        return 1

    site = load_legal_site(PNU, building_type="제1종근린생활시설")
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
        key_rows.append({"tile": tile, "name": name, "height_m": entry["height_m"]})
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

    # The overseas rubric, verbatim from its owner - never retyped here.
    prompts = json.loads((ROOT / "inputs" / "judge-prompts.json").read_text(encoding="utf-8"))
    (out / "prompts.json").write_text(json.dumps(prompts, ensure_ascii=False), encoding="utf-8")
    (out / "PROMPT.txt").write_text(
        "아래 타일 전부를 Read 도구로 실제로 보고 채점하십시오. key.json은 열지 마십시오.\n\n"
        + (prompts.get("rubric_overseas") or prompts["rubric"]), encoding="utf-8")

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
