"""BOOK sentences: what the author writes, and how one becomes a program.

The BOOK's grammar is a base volume, an orientation, one principle (an
operative word, a combination, an aggregation or a case study) and a bounded
variation - the composition lattice in `composition_lattice.py` enumerates
exactly those 13,662 paths, and the page audit builds every one of them
through the same adapter this module calls. The author's job is to choose
sentences from that lattice, size them and face them; the geometry is the
grammar's, not the author's.

The free typed-AST author remains for development, where a parent's exact
nodes are inherited. It is not the creative author any more: comp18's 120
free ASTs were four seeds, four or five nodes each and `notch` sixty-two
times, and not one of the six base volumes.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from ..dimensional_intent import KEY as INTENT_KEY, intent_schema, validate_intent
from ..geometry_language.ast import GeometryProgram
from ..geometry_language.base_seeds import base_seed_program
from ..geometry_language.book_adapter import apply_book_projection_to_geometry_program
from ..geometry_language.compiler import compile_geometry_program
from ..geometry_language.gate import GeometryGatePolicy, compilation_gate
from ..program_massing import (
    book_sentence_variants,
    compose_program_with_book_operations,
    program_seed_sequences,
)
from .composition_lattice import book_composition_path_by_id, iter_book_composition_paths
from .corpus_contract import BOOK_VARIATION_COUNT
from .registry import build_book_language_registry

SIDES = ("east", "west", "north", "south")
SENTENCE_KEY = "sentences"
REPRESENTATION = "book_sentence"
_CONNECTED = GeometryGatePolicy(maximum_components=1)
_PROGRAM_SEED_FALLBACK = "gymnasium"


class BookSentenceError(ValueError):
    """One sentence that the grammar could not build; carries the index."""


def sentence_payload_schema(offered_path_ids: list[str] | tuple[str, ...], *, count: int) -> dict[str, Any]:
    """The strict JSON schema the author's file must satisfy."""

    facing = {
        "type": "object",
        "additionalProperties": False,
        "required": ["access_side", "north_side"],
        "properties": {
            "access_side": {"enum": list(SIDES)},
            "north_side": {"enum": list(SIDES)},
        },
    }
    sentence = {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "book_composition_path_id", INTENT_KEY, "facing", "rationale"],
        "properties": {
            "name": {"type": "string", "minLength": 3, "maxLength": 80, "pattern": "^[a-z0-9_]+$"},
            "book_composition_path_id": {"enum": list(offered_path_ids)},
            INTENT_KEY: intent_schema(),
            "facing": facing,
            "rationale": {"type": "string", "minLength": 10, "maxLength": 600},
        },
    }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "required": [SENTENCE_KEY],
        "properties": {
            SENTENCE_KEY: {"type": "array", "minItems": int(count), "maxItems": int(count), "items": sentence},
        },
    }


def offered_paths(count: int, *, seed: int = 0) -> list[dict[str, Any]]:
    """A stratified offer: every base volume x orientation x principle kind.

    Roughly two to three offers per sentence asked for, spread so that no
    label, orientation or kind is missing from what the author sees.
    """

    paths = [path for path in iter_book_composition_paths() if path.executable]
    buckets: dict[tuple[str, str, str], list] = {}
    for path in paths:
        buckets.setdefault((path.base_volume_label, path.orientation, path.principle_kind), []).append(path)
    target = max(24, int(count) * 5 // 2)
    per_bucket = max(1, -(-target // max(1, len(buckets))))
    chosen = []
    verbs = _principle_verbs()
    for index, key in enumerate(sorted(buckets)):
        pool = sorted(buckets[key], key=lambda item: (item.principle_id, item.variation_index))
        stride = max(1, len(pool) // per_bucket)
        offset = (seed + index) % stride
        # Walk the bucket from its offset and keep the first `per_bucket`
        # paths that build and stand; a path that floats is not offered.
        ordered = pool[offset:] + pool[:offset]
        kept = 0
        for path in ordered:
            if kept >= per_bucket:
                break
            if _path_stands(path, verbs):
                chosen.append(path)
                kept += 1
    return [{
        "path_id": path.path_id,
        "base_volume": path.base_volume_label,
        "orientation": path.orientation,
        "principle": path.principle_id,
        "kind": path.principle_kind,
        "words": list(path.ordered_operations),
        "variation": path.variation_index,
        "page": path.page,
    } for path in chosen]


def _path_stands(path, verbs: dict[str, tuple[str, ...]]) -> bool:
    probe = {"book_composition_path_id": path.path_id,
             "facing": {"access_side": "east", "north_side": "north"},
             INTENT_KEY: {"schema_version": "arr.maas.dimensional_intent.v1", "storey_count": 5,
                          "storey_height_m": 3.8, "target_gfa_m2": 4800.0,
                          "delivery_policy": "preserve_physical_dimensions", "programme_status": "unknown"}}
    try:
        program = realize_book_sentence(probe, principle_verbs=verbs)
        compilation = compile_geometry_program(program)
    except (BookSentenceError, ValueError, TypeError, KeyError):
        return False
    if compilation.status != "compiled" or compilation_gate(compilation, _CONNECTED):
        return False
    return not _stands(standing_evidence(compilation))


def _principle_verbs() -> dict[str, tuple[str, ...]]:
    registry = build_book_language_registry()
    return {
        str(item["principle_id"]): tuple(str(verb) for verb in item["execution_verbs"])
        for item in registry["principles"]
    }


def _program_seed(building_type: str | None):
    for candidate in (building_type, _PROGRAM_SEED_FALLBACK):
        if not candidate:
            continue
        try:
            sequences = program_seed_sequences(str(candidate))
        except Exception:  # noqa: BLE001 - an unregistered building type falls through
            continue
        if sequences:
            return sequences[0]
    raise BookSentenceError("no program seed sequence is registered")


GROUND_CONTACT_RATIO = 0.15  # a lifted block on cores still stands; a block on a stem (0.05) does not


def standing_evidence(compilation) -> dict[str, float | None]:
    """The standing margin and how much of the plan stands on the ground.

    A block on a stem passes the centre-of-mass test and is still not a
    building at this scale (comp24: 108 m2 of stem under 2,215 m2 of body,
    the stem posed outside the parcel and cut away). The ground contact
    must be at least GROUND_CONTACT_RATIO of the plan projection.
    """
    import numpy as np
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    margin = standing_margin(compilation)
    vertices = np.asarray(compilation.vertices, dtype=float)
    triangles = np.asarray(compilation.triangles, dtype=int)
    if margin is None or not len(triangles):
        return {"margin": margin, "ground_ratio": None}
    z_low = float(vertices[:, 2].min())
    eps = max(1e-9, float(vertices[:, 2].max() - z_low) * 1e-6)
    faces = [Polygon(face[:, :2]) for face in (vertices[t] for t in triangles)]
    faces = [(poly, float(abs(vertices[t][:, 2] - z_low).max()) <= eps) for poly, t in zip(faces, triangles) if poly.area > 1e-12]
    plan = unary_union([poly for poly, _ in faces]).area
    ground = unary_union([poly for poly, on_ground in faces if on_ground]).area
    return {"margin": margin, "ground_ratio": (ground / plan) if plan > 0 else None}


def _stands(evidence: dict[str, float | None]) -> str:
    """Empty when the body stands; otherwise why not."""
    margin, ratio = evidence["margin"], evidence["ground_ratio"]
    if margin is None:
        return "no_ground_contact"
    if margin <= 0.0:
        return f"centre_of_mass_{-margin:.3f}_outside_ground"
    if ratio is None or ratio < GROUND_CONTACT_RATIO:
        return f"ground_contact_{(ratio or 0.0):.2f}_of_plan_below_{GROUND_CONTACT_RATIO}"
    return ""


def standing_margin(compilation) -> float | None:
    """How far inside its ground contact the body's centre of mass stands.

    The book draws aggregations as bars floating against each other; a
    building's parts stand on the ground or on each other. comp24 built
    24 sentences that finally looked like the book's pages and the gravity
    screen refused 12 of them for a centre of mass 6-12 m outside the
    ground contact. The same measure at unit scale predicts the screen's
    verdict (axis-aligned scaling keeps the sign), so it is asked here,
    before the author is offered a path and again when a sentence is built.
    Positive: stands. Negative: overhangs by that much. None: no ground.
    """
    import numpy as np
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    vertices = np.asarray(compilation.vertices, dtype=float)
    triangles = np.asarray(compilation.triangles, dtype=int)
    if not len(vertices) or not len(triangles):
        return None
    a, b, c = vertices[triangles[:, 0]], vertices[triangles[:, 1]], vertices[triangles[:, 2]]
    signed = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    volume = float(signed.sum())
    if abs(volume) <= 1e-12:
        return None
    com = (signed[:, None] * (a + b + c) / 4.0).sum(axis=0) / volume
    z_low = float(vertices[:, 2].min())
    eps = max(1e-9, float(vertices[:, 2].max() - z_low) * 1e-6)
    ground = [Polygon(face[:, :2]) for face in (vertices[t] for t in triangles)
              if float(abs(face[:, 2] - z_low).max()) <= eps]
    ground = [poly for poly in ground if poly.area > 1e-12]
    if not ground:
        return None
    hull = unary_union(ground).convex_hull
    point = Point(float(com[0]), float(com[1]))
    distance = float(hull.boundary.distance(point))
    return distance if hull.covers(point) else -distance


def realize_book_sentence(
    sentence: dict[str, Any],
    *,
    site_extent: tuple[float, float, float] | None = None,
    building_type: str | None = None,
    principle_verbs: dict[str, tuple[str, ...]] | None = None,
) -> GeometryProgram:
    """Build the sentence's program the way the page audit builds a page."""

    path_id = str(sentence.get("book_composition_path_id") or "")
    path = book_composition_path_by_id(path_id)
    if path is None:
        raise BookSentenceError(f"unknown_path:{path_id}")
    if not path.executable:
        raise BookSentenceError(f"path_not_executable:{path_id}")
    verbs = (principle_verbs or _principle_verbs()).get(path.principle_id)
    if not verbs:
        raise BookSentenceError(f"principle_without_verbs:{path.principle_id}")
    intent = validate_intent(sentence.get(INTENT_KEY))
    facing = sentence.get("facing") or {}
    for key in ("access_side", "north_side"):
        if facing.get(key) not in SIDES:
            raise BookSentenceError(f"facing_{key}_must_be_one_of_{'/'.join(SIDES)}")
    variants = book_sentence_variants(verbs, count=BOOK_VARIATION_COUNT)
    if not 0 <= int(path.variation_index) < len(variants):
        raise BookSentenceError(f"variation_out_of_range:{path.variation_index}")
    sequence = compose_program_with_book_operations(
        _program_seed(building_type),
        variants[int(path.variation_index)],
        base_volume_label=path.base_volume_label,
        orientation=path.orientation,
    )
    base = base_seed_program("block", site_extent=site_extent)
    # The base volume is the object, not a cell of the block with the rest
    # of the block put back (that is the scope model massv2 edits with).
    program = apply_book_projection_to_geometry_program(base, sequence, recompose_remainder=False)
    name = str(sentence.get("name") or f"sentence_{path_id[-6:]}")
    return replace(program, name=name, metadata={
        **program.metadata,
        "author_representation": REPRESENTATION,
        "base_seed": path.base_volume_label,
        "book_base_volume_label": path.base_volume_label,
        "book_orientation": path.orientation,
        "book_composition_path_id": path.path_id,
        "book_principle_id": path.principle_id,
        "book_principle_kind": path.principle_kind,
        "book_words": list(path.ordered_operations),
        "book_variation_index": int(path.variation_index),
        INTENT_KEY: intent,
        "facing": {"access_side": facing["access_side"], "north_side": facing["north_side"]},
        "rationale": str(sentence.get("rationale") or ""),
    })


def realize_sentence_payload(
    payload: dict[str, Any],
    *,
    expected_count: int,
    site_extent: tuple[float, float, float] | None = None,
    building_type: str | None = None,
) -> tuple[GeometryProgram, ...]:
    """Every sentence becomes a compiled, connected, unique program - or the
    batch is refused with the same 1-based verdict list the free-AST importer
    writes, so the cycle's retry reads it unchanged."""

    sentences = payload.get(SENTENCE_KEY)
    if not isinstance(sentences, list) or not sentences:
        raise ValueError("sentence payload carries no sentences")
    verbs = _principle_verbs()
    programs: list[GeometryProgram] = []
    rejected: list[str] = []
    seen_hashes: set[str] = set()
    seen_paths: set[str] = set()
    for index, sentence in enumerate(sentences):
        label = f"{index + 1}"
        if not isinstance(sentence, dict):
            rejected.append(f"{label}:not_an_object")
            continue
        path_id = str(sentence.get("book_composition_path_id") or "")
        if path_id in seen_paths:
            rejected.append(f"{label}:duplicate_path:{path_id}")
            continue
        try:
            program = realize_book_sentence(
                sentence, site_extent=site_extent, building_type=building_type, principle_verbs=verbs)
        except (BookSentenceError, ValueError, TypeError, KeyError) as exc:
            rejected.append(f"{label}:{path_id or 'no_path'}:{type(exc).__name__}:{str(exc)[:160].replace(';', ',')}")
            continue
        compilation = compile_geometry_program(program)
        issues = compilation_gate(compilation, _CONNECTED)
        if compilation.status != "compiled" or issues:
            reason = (
                compilation.status if compilation.status != "compiled"
                else ",".join(issue.code for issue in issues[:3])
            )
            rejected.append(f"{label}:{path_id}:compile_or_clean_gate:{reason}")
            continue
        why = _stands(standing_evidence(compilation))
        if why:
            rejected.append(f"{label}:{path_id}:does_not_stand:{why}")
            continue
        program_hash = program.program_hash()
        if program_hash in seen_hashes:
            rejected.append(f"{label}:{path_id}:duplicate_program")
            continue
        seen_hashes.add(program_hash)
        seen_paths.add(path_id)
        programs.append(program)
    if len(programs) < max(1, int(expected_count)):
        from ..geometry_language.llm_adapter import GeometryAuthorError
        raise GeometryAuthorError(
            "geometry author batch yielded insufficient valid unique programs"
            + (": " + "; ".join(rejected) if rejected else "")
        )
    return tuple(programs)


__all__ = [
    "SENTENCE_KEY", "SIDES", "BookSentenceError", "offered_paths",
    "realize_book_sentence", "realize_sentence_payload", "sentence_payload_schema",
]


# ----------------------------------------------------------------- site facts
_COMPASS = (("east", (1.0, 0.0)), ("north", (0.0, 1.0)), ("west", (-1.0, 0.0)), ("south", (0.0, -1.0)))


def _compass(dx: float, dy: float) -> str | None:
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return None
    return max(_COMPASS, key=lambda item: item[1][0] * dx + item[1][1] * dy)[0]


def site_facts_for_author(site, *, storey_cap: int | None = None) -> dict[str, Any]:
    """What the author must know about the parcel, from the site's own owners.

    Road/access: `site_open_side_evidence` (registered frontages when the
    plan has them). The sunlight side: the side of the ground plan that the
    top floor's legal plan no longer covers (정북일조 takes it), so no second
    owner of "north" is created. Areas by height: the legal floor field.
    """

    from ..massv2.siting import site_open_side_evidence
    open_side = site_open_side_evidence(site) or {}
    direction = open_side.get("direction_world_xy") or (0.0, 0.0)
    ground = site.plan_at(0.0)
    cap = int(storey_cap or getattr(site, "max_storeys", 0) or 0)
    storey_m = float(getattr(site, "floor_height_m", 0.0) or 0.0)
    top = site.plan_at(max(0.0, cap * storey_m - 0.01)) if cap and storey_m else ground
    cut = ground.difference(top) if (ground is not None and top is not None) else None
    sunlight_side = None
    if cut is not None and not cut.is_empty and cut.area > 1.0:
        sunlight_side = _compass(cut.centroid.x - ground.centroid.x, cut.centroid.y - ground.centroid.y)
    field = getattr(site, "floor_field", {}) or {}
    heights = list(field.get("legal_floor_top_heights_m") or ())
    areas = list(field.get("legal_floor_section_areas_m2") or ())
    by_height = [{"top_m": float(h), "legal_plan_m2": round(float(a), 1)} for h, a in zip(heights, areas)][:max(1, cap or len(heights))]
    return {
        "pnu": str(getattr(site, "pnu", "")),
        "parcel_area_m2": round(float(getattr(site, "parcel_area_m2", 0.0) or 0.0), 1),
        "ground_capacity_m2": round(float(site.ground_capacity_m2), 3),
        "far_capacity_m2": round(float(site.far_capacity_m2), 3),
        "storey_cap": cap,
        "storey_height_m": storey_m,
        "access_side_world": _compass(float(direction[0]), float(direction[1])),
        "access_direction_world_xy": [round(float(direction[0]), 4), round(float(direction[1]), 4)],
        "access_basis": str(open_side.get("basis") or "unavailable"),
        "sunlight_setback_side_world": sunlight_side,
        "ground_legal_plan_m2": round(float(ground.area), 1) if ground is not None else None,
        "top_floor_legal_plan_m2": round(float(top.area), 1) if top is not None else None,
        "legal_plan_by_height": by_height,
        "frame": "program sides east(+x)/west(-x)/north(+y)/south(-y) are the program's own; "
                 "facing maps them onto the world sides named here",
    }


def sentence_prompt(context: dict[str, Any], offer: list[dict[str, Any]], *, count: int, output_path: str, schema_path: str) -> str:
    """The author's instructions - short, because the grammar does the work."""

    facts = context.get("site_facts") or {}
    far = float(facts.get("far_capacity_m2") or context.get("capacity_ceiling_m2") or 0.0)
    ground = float(facts.get("ground_capacity_m2") or 0.0)
    cap = int(facts.get("storey_cap") or 0)
    storey_m = float(facts.get("storey_height_m") or 0.0)
    lines = [
        f"You are the BOOK author. Write exactly {count} BOOK sentences to {output_path}, valid against {schema_path}.",
        "",
        "A sentence is one path of the architect's BOOK: a base volume (1/1, 3/8, 1/2, 1/4, 1/8, 1/16 - cells of the unit cube; 3/8 is an L of three octants), "
        "an orientation (long_axis, short_axis, vertical), one principle (an operative word, a combination of two, an aggregation, or a case study) and a bounded variation. "
        "You choose the path from the OFFER below by its path_id; the grammar builds the geometry. You do not write nodes, operators or parameters.",
        "",
        "For each sentence give: name (snake_case, unique), book_composition_path_id (from the offer, each id at most once), dimensional_intent, facing, rationale.",
        "",
        # Density was "5 storeys, 0.60-0.95 of the FAR capacity" for every
        # sentence, and 6,242 m2 on five floors is a 1,250 m2 plate: every
        # base volume was scaled into the same 19 m block and the book's
        # words became scratches on it (comp26: 30 delivered, most of them
        # a full-site box with a shallow notch). The figure sets the size.
        "DIMENSIONAL INTENT - size to the figure, within the parcel's allowance:",
        f"  storey_count: 2 to {cap}; storey_height_m: {storey_m}. The plan you ask for is target_gfa_m2 / storey_count: "
        f"it may not exceed {ground:,.0f} (coverage capacity), and a 1/16, 1/8 or 1/4 figure, a bar or a tower keeps its proportion "
        f"only if that plan stays well under half of it - give such a figure fewer storeys or less area, never a full-site plate.",
        f"  target_gfa_m2: between {0.35 * far:,.0f} and {0.95 * far:,.0f} (FAR capacity {far:,.0f}). At least a third of the batch must still "
        f"use {cap} storeys and 0.60 or more of the FAR capacity, so the client sees the allowance filled as well as the figures.",
        "  delivery_policy: preserve_physical_dimensions; programme_status: unknown; schema_version: arr.maas.dimensional_intent.v1.",
        "",
        "FACING - the program's own sides are east(+x), west(-x), north(+y), south(-y):",
        f"  access_side: which program side faces the road. The road is on the parcel's {facts.get('access_side_world') or 'unknown'} side ({facts.get('access_basis')}).",
        f"  north_side: which program side takes the sunlight setback. The legal plan shrinks above 9 m on the parcel's {facts.get('sunlight_setback_side_world') or 'unknown'} side: "
        f"{facts.get('ground_legal_plan_m2')} m2 at ground -> {facts.get('top_floor_legal_plan_m2')} m2 at the top floor. Put the lower part of a stepped or split figure there.",
        "",
        "SPREAD - the batch must use every base volume (all six labels) and every orientation; at least a third of the sentences must be combinations, aggregations or case studies; "
        "no two sentences may share a path_id; prefer paths whose words differ.",
        "",
        "SITE FACTS (json):",
        __import__("json").dumps(facts, ensure_ascii=False),
        "",
        f"OFFER ({len(offer)} paths; path_id, base volume, orientation, principle, words, variation):",
    ]
    for item in offer:
        lines.append(f"  {item['path_id']}  {item['base_volume']:>4} {item['orientation']:<10} {item['principle']:<34} {'+'.join(item['words']):<24} v{item['variation']}")
    lines += [
        "",
        "Write the file with a JSON library, validate it against the schema, and write nothing else. Run no pipeline stages.",
    ]
    return chr(10).join(lines)


__all__ += ["site_facts_for_author", "sentence_prompt"]
