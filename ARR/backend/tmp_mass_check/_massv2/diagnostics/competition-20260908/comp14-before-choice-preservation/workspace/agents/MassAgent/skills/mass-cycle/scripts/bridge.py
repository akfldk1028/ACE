"""Thin integration with ARR's geometry owners; no duplicated geometry policy."""
import json
import logging
import os
from pathlib import Path
import sys

from cycle import CycleError, pair_votes, read, write

WS = Path(os.environ["MASSV2_WS"])
# Sibling modules (lineage) must import whether this file runs as a script
# or is loaded from its path by the tests.
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
BACKEND = Path(os.environ["ARR_BACKEND"])
sys.path[:0] = [str(WS / "tools"), str(BACKEND)]
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def verify_baseline(directory):
    import hashlib
    directory = Path(directory).resolve()
    manifest = read(directory / "manifest.json")
    for relative, sha in manifest.items():
        path = (directory / relative).resolve()
        if not path.is_relative_to(directory) or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise CycleError(f"baseline artifact missing or changed: {relative}")
    return directory


def new_era(note, baseline):
    verify_baseline(baseline)
    era = WS / "runs/board/era.json"
    # A crash after clearing the board but before the coordinator receipt must
    # not clear it again. The backend's persisted unique note is the receipt.
    if era.exists() and read(era).get("note") == note:
        return
    from board_curate import new_era as begin
    begin(note)


def pixel_diff(baseline, output):
    from PIL import Image, ImageChops
    baseline = verify_baseline(baseline)
    before_dir = baseline / "runs/board"
    current_dir = WS / "runs/board"
    before_key = {r["label"]: r for r in read(before_dir / "board-key.json")}
    current_key = {r["label"]: r for r in read(current_dir / "board-key.json")}
    result = []
    for path in sorted(current_dir.glob("*.png")):
        previous = before_dir / path.name
        row = {"file": path.name, "baseline_exists": previous.exists(),
               "before_identity": before_key.get(path.stem), "after_identity": current_key.get(path.stem)}
        if previous.exists():
            with Image.open(previous) as old, Image.open(path) as new:
                a, b = old.convert("RGB"), new.convert("RGB")
                row["same_dimensions"] = a.size == b.size
                if a.size == b.size:
                    diff = ImageChops.difference(a, b)
                    row["identical_pixels"] = diff.getbbox() is None
                    row["changed_pixel_fraction"] = sum(any(pixel) for pixel in diff.getdata()) / (a.width * a.height)
                    diff_path = Path(output).parent / "pixel-diff" / path.name
                    diff_path.parent.mkdir(exist_ok=True)
                    diff.save(diff_path)
                    row["difference_image"] = str(diff_path)
        result.append(row)
    write(output, {"baseline": str(baseline), "comparisons": result,
                   "interpretation": "Pixel change evidence only; a changed selection is not a same-geometry quality comparison."})


def validate_book(path, count):
    from design.maas.creative_program_author import authored_programs_from_payload
    programs = authored_programs_from_payload(read(path), expected_count=int(count))
    if len(programs) < int(count):
        raise CycleError(f"BOOK payload contains {len(programs)} programs; {count} required")
    print(f"validated {len(programs)} authored BOOK programs")


def book_author_contract(output, count, run_id):
    """Materialize current ARR author owners; never maintain a second grammar."""
    from design.maas.geometry_language import llm_adapter as owner
    from design.maas.book_language.candidate_generation import _book_graph_author_vocabulary
    output = Path(output)
    count = int(count)
    from lineage import recent_lineages
    developed = recent_lineages(WS, str(run_id).replace('book-', '', 1))
    context = {
        'pnu': os.environ['PNU'],
        'capacity_ceiling_m2': float(os.environ['GROUND_CAPACITY_M2']),
        'creative_portfolio_run_id': run_id,
        'book_graph_vocabulary': _book_graph_author_vocabulary(),
        'instruction': 'Author materially different executable typed MASS ASTs. '
                       'Do not select or imitate a named family recipe.'
                       + (' Figures developed in the last three cycles - '
                          + ', '.join(developed)
                          + ' - have had their turn; propose other figures.' if developed else ''),
        'recently_developed_lineages': developed,
        'author_prompt_contract': owner.GEOMETRY_AUTHOR_PROMPT_CONTRACT,
    }
    schema = owner._author_schema(
        count, allowed_base_seeds=owner._allowed_author_base_seeds(context),
        allowed_operators=owner._allowed_author_operators(context),
        book_principle_vocabulary=owner._book_graph_principle_vocabulary(context),
        book_composition_path_ids=tuple(item['path_id'] for item in owner._book_composition_path_slice(context, count)))
    output.mkdir(parents=True, exist_ok=True)
    write(output / 'context.json', context)
    write(output / 'schema.json', schema)
    (output / 'PROMPT.txt').write_text(owner._author_prompt(context, count), encoding='utf-8')


def book_record(name):
    from book_import import registry, records_of
    entry = registry().get(name)
    if not entry:
        raise CycleError(f"BOOK source unavailable: {name}")
    rec = next((r for r in records_of(Path(entry["book_dir"]))
                if r.get("trace_sequence_name") == entry["trace"]), None)
    if rec is None:
        raise CycleError(f"BOOK source record unavailable: {name}")
    return rec


def _development_site_feedback(source, site, certificate, expected_shape):
    """Adapt the existing site owner into an identity-bound author handoff."""
    from copy import deepcopy
    from design.maas.massv2.site_planning import assess_site_parking
    if (not expected_shape or certificate.get('shape_id') != expected_shape
            or not certificate.get('certificate_id')
            or str(certificate.get('site_pnu')) != str(site.pnu)):
        raise CycleError('development parking parent identity mismatch')
    evidence = assess_site_parking(source, site, certificate, source_shape_id=expected_shape)
    for key, expected in (('source_shape_id', expected_shape),
                          ('certificate_id', certificate['certificate_id']),
                          ('site_pnu', str(site.pnu))):
        if evidence.get(key) != expected:
            raise CycleError(f'development parking measurement {key} mismatch')
    requests = (evidence.get('layout') or {}).get('repair_requests') or []
    if not isinstance(requests, list) or any(not isinstance(item, dict) for item in requests):
        raise CycleError('development parking owner returned invalid repair requests')
    return {
        'schema': 'massagent.development_site_feedback.v1',
        'source_shape_id': expected_shape,
        'certificate_id': certificate['certificate_id'],
        'site_pnu': str(site.pnu),
        'measurement_owner': 'design.maas.massv2.site_planning.assess_site_parking',
        'law_source_sha256': evidence.get('law_source_sha256'),
        'law_requirement_evidence_sha256': evidence.get('law_requirement_evidence_sha256'),
        'site_parking': deepcopy(evidence),
        'repair_requests': deepcopy(requests),
        'parking_solved': False,
        'legal_approval': False,
        'author_instruction': (
            'Address the measured parking repair_requests in the authored development, '
            'preserving the parent spatial principle and verified dimensional contract. '
            'Explain which request each child addresses and any unresolved conflict. '
            'Use the attached conditional legal evidence and actual available-area geometry; '
            'do not infer a site maximum or reduce programme without authorization. '
            'After delivery, remeasure each child with the same site-planning owner and '
            'its new shape_id and certificate. Counts alone do not verify vehicle access, '
            'pedestrian access, swept paths, or permit compliance.'),
    }


def _judged_book_entry(parent, expected_shape):
    """The registry entry of the stage the parent was judged in.

    A parent's name can recur across stages (a champion is carried into every
    later BOOK run), and the merged registry then answers with whichever stage
    sorts last. The board row that made it a parent carries its judged round
    and certificate, so that row resolves the entry; by name alone only when
    every stage agrees.
    """
    from book_import import entry_for_judged_row, resolve_entry
    board = WS / "runs/board/board-key.json"
    if board.exists():
        for row in read(board):
            if row.get("name") == parent and (not expected_shape or row.get("shape_id") == expected_shape)                     and row.get("certificate_id"):
                return entry_for_judged_row(row)
    return resolve_entry(parent)


def book_development_contract(parent, expected_shape, output):
    """Resolve inherited numbers from the scored parent's current exact source."""
    from finalists import PNU, BUILDING_TYPE
    from book_import import book_rebuild, _refused
    from vlm_shortlist import shape_id, seat_certificate
    from design.maas.massv2.legal import load_legal_site
    from design.maas.geometry_language.ast import GeometryProgram
    from design.maas.book_development import validate_parent_contract
    site = load_legal_site(PNU, building_type=BUILDING_TYPE)
    entry = _judged_book_entry(parent, expected_shape)
    source = book_rebuild(parent, site, site.plan_at(0), book_entry=entry)
    if source is None or _refused(source, site):
        raise CycleError('BOOK development parent no longer passes delivery gates')
    if not expected_shape or shape_id(source) != expected_shape:
        raise CycleError('BOOK development parent differs from scored shape')
    cert = seat_certificate(parent, source, {}, site, book_entry=entry)
    stored = entry.get('numeric_certificate') or {}
    if stored.get('certificate_id') != cert['certificate_id']:
        raise CycleError('BOOK development parent certificate differs from staged evidence')
    art = book_record(parent)['geometry_artifact']
    program = GeometryProgram.from_dict(art.get('authoredGeometryProgram') or art['geometryProgram'])
    context = {'parent': parent, 'parent_shape_id': expected_shape,
               'parent_program_hash': program.program_hash(),
               'parent_certificate_id': cert['certificate_id'], 'site_pnu': str(site.pnu),
               'storey_count': int(source.metadata['book_floor_count']),
               'storey_height_m': float(source.metadata['book_storey_height_m']),
               'target_gfa_m2': float(cert['gross_m2']), 'height_m': float(cert['height_m'])}
    context['site_feedback'] = _development_site_feedback(source, site, cert, expected_shape)
    validate_parent_contract(context)
    write(output, context)


def validate_book_development(payload, count, contract):
    from design.maas.book_development import validate_development_payload
    validate_development_payload(read(payload), read(contract), expected_count=int(count))


def carry_book(directory):
    from book_import import records_of
    directory = Path(directory)
    records = records_of(directory)
    feedback = WS / "inputs/book-develop-feedback.json"
    seen = {r["trace_sequence_name"] for r in records}
    if feedback.exists():
        for entry in read(feedback).get("champions", []):
            record = entry["record"]
            if record["trace_sequence_name"] not in seen:
                records.append(record)
                seen.add(record["trace_sequence_name"])
    if not records:
        raise CycleError("BOOK generation produced no usable source records")
    write(directory / "maas-book-exact-geometry-artifacts.json", {"records": records})


def authored_pairs(parent, run, count, output, shape="", authored_payload=""):
    import develop
    status = develop.main(run, parent, count, output_dir=output, expected_shape_id=shape or None,
                          authored_payload=authored_payload or None)
    if status:
        raise CycleError("authored development failed")


def book_pairs(parent, run, output, expected_shape=""):
    from finalists import PNU, BUILDING_TYPE
    from book_import import book_rebuild, _refused
    from vlm_shortlist import shape_id, seat_certificate
    from design.maas.massv2.legal import load_legal_site
    from design.maas.massv2.render import render_masses
    site = load_legal_site(PNU, building_type=BUILDING_TYPE)
    buildable = site.plan_at(0)
    source = book_rebuild(parent, site, buildable, book_entry=_judged_book_entry(parent, expected_shape))
    if source is None or _refused(source, site):
        raise CycleError("BOOK parent no longer passes delivery gates")
    parent_shape = shape_id(source)
    if expected_shape and parent_shape != expected_shape:
        raise CycleError("BOOK parent differs from scored board geometry; rejudge first")
    output = Path(output)
    (output / "pairs").mkdir(parents=True, exist_ok=True)
    registry = read(WS / "runs/books" / f"{run}.json")
    seen = {parent_shape}
    children = []
    for name in registry["entries"]:
        # The children are this run's own entries; no merged lookup.
        child = book_rebuild(name, site, buildable,
                             book_entry={**registry["entries"][name], "book_dir": registry.get("book_dir")})
        if child is None or _refused(child, site):
            children.append({"name": name, "delivered": False})
            continue
        shape = shape_id(child)
        if registry['entries'][name].get('delivered_shape_id') != shape:
            raise CycleError('BOOK child differs from staged geometry; re-stage before pairs')
        certificate = seat_certificate(name, child, {}, site, book_entry=registry['entries'][name])
        if (registry['entries'][name].get('numeric_certificate') or {}).get('certificate_id') != certificate['certificate_id']:
            raise CycleError('BOOK child differs from staged certificate; re-stage before pairs')
        if shape in seen:
            children.append({"name": name, "delivered": True, "erased_by_delivery": True})
            continue
        site_feedback = _development_site_feedback(child, site, certificate, shape)
        seen.add(shape)
        pair = f"p{sum(bool(c.get('pair')) for c in children) + 1:02d}.png"
        render_masses([("A", source, {}), ("B", child, {})], output / "pairs" / pair,
                      site_ring=list(buildable.exterior.coords), columns=2, tile=(620, 560), style="massing")
        from presentation import append_jury_drawings
        drawings = append_jury_drawings(output / 'pairs' / pair, [
            (parent, source, source.metadata.get('book_storey_height_m')),
            (name, child, certificate['storey_m'])], buildable)
        import hashlib
        children.append({"name": name, "delivered": True, "pair": pair,
                         "shape_id": shape, "record": book_record(name),
                         'site_feedback': site_feedback,
                         'certificate': certificate, 'certificate_id': certificate['certificate_id'], 'jury_drawings': drawings,
                         'pair_sha256': hashlib.sha256((output / 'pairs' / pair).read_bytes()).hexdigest()})
    write(output / "mutants.json", {"parent": parent, "parent_shape_id": parent_shape,
          "parent_record": book_record(parent), "source": "book", "children": children})


def score_book(output, *ballots):
    output = Path(output)
    record = read(output / "mutants.json")
    votes = pair_votes(ballots, {Path(c["pair"]).stem for c in record["children"] if c.get("pair")})
    winners = []
    for child in record["children"]:
        if child.get("pair"):
            child["votes"] = "".join(votes[Path(child["pair"]).stem])
            if child["votes"] == "BBB":
                winners.append(child)
    # Stable first-local-change tie break matches the authored development rule.
    winner = winners[0] if winners else None
    record.update(champion=winner["name"] if winner else None,
                  unanimous_children=[c["name"] for c in winners], jurors=3)
    feedback = WS / "inputs/book-develop-feedback.json"
    data = read(feedback) if feedback.exists() else {"champions": []}
    name = winner["name"] if winner else record["parent"]
    row = {"name": name, "parent": record["parent"],
           "record": winner["record"] if winner else record["parent_record"],
           "development": str(output / "champion.json")}
    data["champions"] = [r for r in data["champions"] if r["name"] != name] + [row]
    write(feedback, data)
    record["feedback_written"] = True
    write(output / "champion.json", record)


if __name__ == "__main__":
    commands = {"validate-book": validate_book, "carry-book": carry_book,
                "book-author-contract": book_author_contract,
                "book-development-contract": book_development_contract,
                "validate-book-development": validate_book_development,
                "authored-pairs": authored_pairs, "book-pairs": book_pairs, "score-book": score_book,
                "new-era": new_era, "pixel-diff": pixel_diff}
    try:
        commands[sys.argv[1]](*sys.argv[2:])
    except (CycleError, ValueError, KeyError, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        sys.exit(1)
