"""Canonical, traceable registry for the architect-supplied 69-page BOOK.

The scanned pages are evidence.  Operative principles are typed concepts that
may cite one or more pages.  Keeping those identities separate prevents the
debug UI from presenting a page count or a coarse strategy bucket as if it
were an executable architectural language.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from .semantics import BASE_VOLUME_FRACTIONS, semantics_for


SCHEMA_VERSION = "arr.maas.book_language_registry.v1"
CORPUS_ID = "architect-book-69"
_OCR_PATH = Path(__file__).resolve().parents[1] / "grammar" / "data" / "book_operative_languages.v1.ocr.json"


@dataclass(frozen=True)
class BaseOperative:
    verb: str
    page: int
    transformation: str
    cardinality: str

    @property
    def principle_id(self) -> str:
        return f"book:operative:{self.verb}"


BASE_OPERATIVES: tuple[BaseOperative, ...] = (
    BaseOperative("expand", 6, "add", "single"),
    BaseOperative("extrude", 7, "add", "single"),
    BaseOperative("inflate", 8, "add", "single"),
    BaseOperative("branch", 9, "add", "multiple"),
    BaseOperative("merge", 10, "add", "multiple"),
    BaseOperative("nest", 11, "add", "multiple"),
    BaseOperative("offset", 12, "add", "multiple"),
    BaseOperative("bend", 14, "displace", "single"),
    BaseOperative("skew", 15, "displace", "single"),
    BaseOperative("split", 16, "displace", "single"),
    BaseOperative("twist", 17, "displace", "single"),
    BaseOperative("interlock", 18, "displace", "multiple"),
    BaseOperative("intersect", 19, "displace", "multiple"),
    BaseOperative("lift", 20, "displace", "multiple"),
    BaseOperative("lodge", 21, "displace", "multiple"),
    BaseOperative("overlap", 22, "displace", "multiple"),
    BaseOperative("rotate", 23, "displace", "multiple"),
    BaseOperative("shift", 24, "displace", "multiple"),
    BaseOperative("carve", 26, "subtract", "single"),
    BaseOperative("compress", 27, "subtract", "single"),
    BaseOperative("fracture", 28, "subtract", "single"),
    BaseOperative("grade", 29, "subtract", "single"),
    BaseOperative("notch", 30, "subtract", "single"),
    BaseOperative("pinch", 31, "subtract", "single"),
    BaseOperative("shear", 32, "subtract", "single"),
    BaseOperative("taper", 33, "subtract", "single"),
    BaseOperative("embed", 34, "subtract", "multiple"),
    BaseOperative("extract", 35, "subtract", "multiple"),
    BaseOperative("inscribe", 36, "subtract", "multiple"),
    BaseOperative("puncture", 37, "subtract", "multiple"),
)


# Page, first operation, second operation.  The order is evidence: BOOK treats
# repeated and mixed operations as different generative sentences.
COMBINATIONS: tuple[tuple[int, str, str], ...] = (
    (39, "inscribe", "inscribe"), (39, "intersect", "intersect"),
    (40, "split", "split"), (40, "embed", "embed"),
    (41, "taper", "taper"), (41, "bend", "bend"),
    (42, "branch", "branch"), (42, "expand", "expand"),
    (43, "shift", "shift"), (43, "notch", "notch"),
    (44, "inscribe", "intersect"), (44, "intersect", "split"),
    (45, "split", "embed"), (45, "embed", "taper"),
    (46, "taper", "bend"), (46, "bend", "branch"),
    (47, "branch", "expand"), (47, "expand", "shift"),
    (48, "shift", "notch"), (48, "notch", "twist"),
)


# Page, aggregation method, operative input.  Page 51 explicitly combines two
# aggregation methods and therefore retains both in the method tuple.
AGGREGATIONS: tuple[tuple[int, tuple[str, ...], str], ...] = (
    (50, ("reflect",), "expand"),
    (51, ("reflect", "pack"), "skew"),
    (52, ("pack",), "inflate"),
    (53, ("pack", "stack"), "branch"),
    (54, ("stack",), "bend"),
    (55, ("array", "stack"), "rotate"),
    (56, ("array",), "taper"),
    (57, ("join", "array"), "pinch"),
    (58, ("join",), "split"),
)


CASE_STUDIES: tuple[tuple[int, str, tuple[str, ...]], ...] = (
    (60, "Poli House · Carve + Offset", ("carve", "offset")),
    (61, "Villa 1 · Embed + Branch", ("embed", "branch")),
    (62, "Casa para un Carpintero · Embed + Overlap", ("embed", "overlap")),
    (63, "House N · Expand + Nest", ("expand", "nest")),
    (64, "House in Minamimachi 2 · Overlap + Expand", ("overlap", "expand")),
    (65, "Nursing Home · Bend + Shift", ("bend", "shift")),
    (66, "Leimondo Nursery School · Embed + Taper", ("embed", "taper")),
    (67, "Gouveia Law Courts · Lift + Carve", ("lift", "carve")),
    (68, "Carabanchel Housing · Lift + Extrude", ("lift", "extrude")),
    (69, "Ironbank · Overlap + Rotate", ("overlap", "rotate")),
)


PAGE_SECTIONS: tuple[tuple[range, str], ...] = (
    (range(1, 3), "introduction"),
    (range(3, 6), "operative_index"),
    (range(6, 13), "base_operative"),
    (range(13, 25), "base_operative"),
    (range(25, 38), "base_operative"),
    (range(38, 49), "combination"),
    (range(49, 59), "aggregation"),
    (range(59, 70), "case_study"),
)


def _page_section(page: int) -> str:
    return next(section for pages, section in PAGE_SECTIONS if page in pages)


@lru_cache(maxsize=1)
def _ocr_document() -> dict[str, Any]:
    data = json.loads(_OCR_PATH.read_text(encoding="utf-8"))
    if data.get("page_count") != 69 or len(data.get("pages") or ()) != 69:
        raise ValueError("BOOK OCR contract requires exactly 69 pages")
    return data


def _principle_refs_by_page() -> dict[int, list[str]]:
    refs: dict[int, list[str]] = {page: [] for page in range(1, 70)}
    refs[3].extend(f"book:base-volume:{label.replace('/', '-') }" for label, _fraction in BASE_VOLUME_FRACTIONS)
    for item in BASE_OPERATIVES:
        refs[item.page].append(item.principle_id)
    for index, (page, left, right) in enumerate(COMBINATIONS, start=1):
        refs[page].append(f"book:combination:{index:02d}:{left}+{right}")
    for page, methods, verb in AGGREGATIONS:
        refs[page].append(f"book:aggregation:{'+'.join(methods)}:{verb}")
    for page, _label, verbs in CASE_STUDIES:
        refs[page].append(f"book:case:{page}:{'+'.join(verbs)}")
    return refs


def _status(principle_id: str, compile_evidence: dict[str, dict[str, Any]]) -> str:
    evidence = compile_evidence.get(principle_id) or {}
    if evidence.get("hard_pass") and evidence.get("geometry_delta", 0) > 0:
        return "active"
    if evidence.get("compile_passed"):
        return "compile_tested"
    return "typed"


def build_book_language_registry(
    compile_evidence: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return one reconciled manifest for provenance, typing and execution."""
    evidence = compile_evidence or {}
    ocr = _ocr_document()
    refs = _principle_refs_by_page()
    pages = []
    for page in ocr["pages"]:
        number = int(page["page"])
        pages.append({
            "page": number,
            "source_path": page.get("source_path"),
            "sha256": page.get("sha256"),
            "section": _page_section(number),
            "ocr_status": "extracted",
            "ocr_lines": page.get("ocr_lines") or [],
            "principle_ids": refs[number],
        })

    principles: list[dict[str, Any]] = []
    for item in BASE_OPERATIVES:
        semantics = semantics_for(item.verb)
        principles.append({
            "principle_id": item.principle_id,
            "kind": "base_operative",
            "label": item.verb,
            "verbs": [item.verb],
            "execution_verbs": [item.verb],
            "page_refs": [item.page],
            "transformation": item.transformation,
            "cardinality": item.cardinality,
            "semantics": semantics.to_dict(),
            "status": _status(item.principle_id, evidence),
            "compile_evidence": evidence.get(item.principle_id),
        })
    for index, (page, left, right) in enumerate(COMBINATIONS, start=1):
        principle_id = f"book:combination:{index:02d}:{left}+{right}"
        principles.append({
            "principle_id": principle_id,
            "kind": "combination",
            "label": f"{left} + {right}",
            "verbs": [left, right],
            "execution_verbs": [left, right],
            "page_refs": [page],
            "status": _status(principle_id, evidence),
            "compile_evidence": evidence.get(principle_id),
        })
    for page, methods, verb in AGGREGATIONS:
        principle_id = f"book:aggregation:{'+'.join(methods)}:{verb}"
        principles.append({
            "principle_id": principle_id,
            "kind": "aggregation",
            "label": f"{' + '.join(methods)} · {verb}",
            "verbs": [*methods, verb],
            # The BOOK title presents aggregation method first (Reflect |
            # Expand), while its procedure applies the operation before the
            # aggregation method (Base -> Expand -> Reflect).
            "execution_verbs": [verb, *methods],
            "aggregation_methods": list(methods),
            "page_refs": [page],
            "status": _status(principle_id, evidence),
            "compile_evidence": evidence.get(principle_id),
        })
    case_studies: list[dict[str, Any]] = []
    for page, label, verbs in CASE_STUDIES:
        principle_id = f"book:case:{page}:{'+'.join(verbs)}"
        case_studies.append({
            "principle_id": principle_id,
            "kind": "case_study",
            "label": label,
            "verbs": list(verbs),
            "execution_verbs": list(verbs),
            "page_refs": [page],
            "status": "evidence_only",
            "compile_evidence": evidence.get(principle_id),
        })

    status_counts: dict[str, int] = {}
    for principle in principles:
        status_counts[principle["status"]] = status_counts.get(principle["status"], 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "corpus_id": CORPUS_ID,
        "source": ocr.get("source"),
        "page_count": len(pages),
        "base_volume_count": len(BASE_VOLUME_FRACTIONS),
        "base_volumes": [
            {
                "base_volume_id": f"book:base-volume:{label.replace('/', '-')}",
                "label": f"{label} Base Volume",
                "fraction": fraction,
                "page_refs": [3],
                "status": "typed",
            }
            for label, fraction in BASE_VOLUME_FRACTIONS
        ],
        "base_operative_count": len(BASE_OPERATIVES),
        "combination_count": len(COMBINATIONS),
        "aggregation_recipe_count": len(AGGREGATIONS),
        "case_study_count": len(CASE_STUDIES),
        "aggregation_methods": sorted({method for _, methods, _ in AGGREGATIONS for method in methods}),
        "taxonomy": {
            "base_volumes": [f"book:base-volume:{label.replace('/', '-')}" for label, _fraction in BASE_VOLUME_FRACTIONS],
            "operations": {
                transformation: {
                    cardinality: [
                        item.principle_id for item in BASE_OPERATIVES
                        if item.transformation == transformation and item.cardinality == cardinality
                    ]
                    for cardinality in ("single", "multiple")
                }
                for transformation in ("add", "displace", "subtract")
            },
            "combinations": [
                f"book:combination:{index:02d}:{left}+{right}"
                for index, (_page, left, right) in enumerate(COMBINATIONS, start=1)
            ],
            "aggregations": [
                f"book:aggregation:{'+'.join(methods)}:{verb}"
                for _page, methods, verb in AGGREGATIONS
            ],
            "case_studies": [
                f"book:case:{page}:{'+'.join(verbs)}"
                for page, _label, verbs in CASE_STUDIES
            ],
        },
        "status_counts": status_counts,
        "pages": pages,
        "principles": principles,
        "case_studies": case_studies,
    }


def book_base_verbs() -> frozenset[str]:
    return frozenset(item.verb for item in BASE_OPERATIVES)


def principles_for_verbs(verbs: Iterable[str]) -> tuple[str, ...]:
    requested = tuple(str(verb) for verb in verbs)
    manifest = build_book_language_registry()
    return tuple(
        item["principle_id"] for item in manifest["principles"]
        if item["kind"] != "case_study" and tuple(item["verbs"]) == requested
    )


__all__ = [
    "AGGREGATIONS",
    "BASE_OPERATIVES",
    "CASE_STUDIES",
    "COMBINATIONS",
    "CORPUS_ID",
    "SCHEMA_VERSION",
    "book_base_verbs",
    "build_book_language_registry",
    "principles_for_verbs",
]
