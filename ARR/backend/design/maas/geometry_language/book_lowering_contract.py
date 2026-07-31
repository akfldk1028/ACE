"""Page-reviewed kernel lowering contract for the thirty BOOK operatives."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookOperativeLowering:
    required_operators: frozenset[str]
    forbidden_operators: frozenset[str] = frozenset()


BOOK_OPERATIVE_LOWERING: dict[str, BookOperativeLowering] = {
    "expand": BookOperativeLowering(frozenset({"boundary_expand"})),
    "extrude": BookOperativeLowering(frozenset({"scale"})),
    "inflate": BookOperativeLowering(frozenset({"inflate"})),
    "branch": BookOperativeLowering(frozenset({"book_branch"})),
    "merge": BookOperativeLowering(frozenset({"merge_related"})),
    "nest": BookOperativeLowering(frozenset({"nested_related"}), frozenset({"courtyard"})),
    "offset": BookOperativeLowering(frozenset({"nested_related"}), frozenset({"translate"})),
    "bend": BookOperativeLowering(frozenset({"bend"})),
    "skew": BookOperativeLowering(frozenset({"shear"})),
    "split": BookOperativeLowering(
        frozenset({"book_split"}), frozenset({"split_wing"})
    ),
    "twist": BookOperativeLowering(frozenset({"twist"})),
    "interlock": BookOperativeLowering(frozenset({"interlock_related"})),
    "intersect": BookOperativeLowering(
        frozenset({"intersect_related"}), frozenset({"intersection"})
    ),
    "lift": BookOperativeLowering(
        frozenset({"book_lift"}), frozenset({"lift"})
    ),
    "lodge": BookOperativeLowering(
        frozenset({"book_lodge"}), frozenset({"offset_related"})
    ),
    "overlap": BookOperativeLowering(frozenset({"overlap_related"})),
    "rotate": BookOperativeLowering(
        frozenset({"book_rotate"}), frozenset({"rotate"})
    ),
    "shift": BookOperativeLowering(frozenset({"shift_related"})),
    "carve": BookOperativeLowering(
        frozenset({"book_carve"}), frozenset({"notch"})
    ),
    "compress": BookOperativeLowering(frozenset({"scale"})),
    "fracture": BookOperativeLowering(
        frozenset({"book_fracture"}), frozenset({"split_wing"})
    ),
    "grade": BookOperativeLowering(
        frozenset({"book_grade"}), frozenset({"terrace", "taper"})
    ),
    "notch": BookOperativeLowering(
        frozenset({"book_notch"}), frozenset({"notch"})
    ),
    "pinch": BookOperativeLowering(frozenset({"pinch"})),
    "shear": BookOperativeLowering(frozenset({"slice"}), frozenset({"shear"})),
    "taper": BookOperativeLowering(frozenset({"taper"})),
    "embed": BookOperativeLowering(frozenset({"embed_void"})),
    "extract": BookOperativeLowering(
        frozenset({"book_extract"}), frozenset({"notch"})
    ),
    "inscribe": BookOperativeLowering(frozenset({"courtyard"})),
    "puncture": BookOperativeLowering(frozenset({"puncture"})),
}


__all__ = ["BOOK_OPERATIVE_LOWERING", "BookOperativeLowering"]
