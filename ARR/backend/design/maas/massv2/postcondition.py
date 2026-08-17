"""Did the building do what the sentence said it did.

Everything else in this package checks the mass against the world - the law,
daylight, gravity, the parcel. Nothing checked it against its own sentence, and
that gap is why work on this language had become a sequence of patches: a
`split` whose halves stood flush drew a picture identical to the box it cut, a
two-metre `lift` under a twelve-metre plate read as a plinth recess, a `carve`
at the low end of its range came out as a skylight. Each was found by a person
looking at a PNG, forming a hypothesis and changing code.

The first version of this module asked the question per verb: what does a
`carve` leave behind, what does a `lift` look like. That was the same mistake
one level up. Four checks, and measurement corrected three of them in a single
afternoon - reading only for interior rings called every edge-notch silent,
demanding the raised plate be less than half held collided with the four
supports `lift` puts there itself, and requiring the sheared volumes to overlap
refused the strongest version of the move. Worse, `_shows_shear` passed
whenever a `split` had moved two parts apart, so it reported on a move that had
not happened and its numbers were never trustworthy.

There is only one question, and it does not need to know what any verb means:

    is the mass after this word measurably different from the mass before it?

`execute_steps` already stops the sentence after each word. Comparing those
frames answers it for every verb at once, including verbs added later, and it
cannot be fooled by a neighbouring move because the only thing that changed
between the two frames is the word being judged.

The check runs once per sentence, at the size it was authored. A verb that does
nothing here does nothing in every coverage and siting variant derived from it,
so judging the sentence is both cheaper and the right unit: silence is a
property of what was written, not of how large it was later drawn.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shapely.ops import unary_union

from design.maas.source_geometry.ir import SourceMass

from .compile import _plan, compile_matrix_form
from .execute import execute_steps


# How much of the mass a word has to change to count as having been said. Below
# this the drawing is the same drawing: measured against the corpus offset
# floor, which holds that a move under 0.15 of a volume's own dimension reads as
# a setting-out error rather than as a decision, a word that redraws less than
# a twentieth of the building is in the same class.
MIN_CHANGED_SHARE = 0.05

# Where the two masses are compared. Storey by storey, because that is how the
# compiler bands them and how a person reads a section.
_SAMPLES = 16

# How far outside its own plan a scoped word may push its volumes and still be
# measured. A `shift` moves the thing it is aimed at, and judging it only where
# the volume used to be would score the move as a disappearance.
_SCOPE_MARGIN_M = 12.0


@dataclass(frozen=True)
class Verdict:
    declared: tuple[str, ...]
    silent: tuple[str, ...]
    changed: tuple[float, ...]

    @property
    def honest(self) -> bool:
        return not self.silent

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_postcondition.v2",
            "declared": list(self.declared),
            "silent": list(self.silent),
            "changed_share": [round(value, 4) for value in self.changed],
            "honest": self.honest,
        }


def _plan_at(source: SourceMass | None, z: float):
    """The mass's plan at a height, as one polygon."""

    if source is None:
        return None
    height = float(source.metadata.get("authored_height_m") or 0.0)
    if height <= 0.0:
        return None
    parts = [
        volume.footprint
        for volume in source.volumes
        if volume.bottom_fraction * height - 1e-6 <= z < volume.top_fraction * height + 1e-6
    ]
    return unary_union(parts) if parts else None


def _height_of(source: SourceMass | None) -> float:
    if source is None:
        return 0.0
    return float(source.metadata.get("authored_height_m") or 0.0)


def _scope_region(form, prefix: str):
    """The plan the volumes a scoped word aims at were occupying.

    A word aimed at one part of a composition is judged against that part. The
    check compares whole masses, and a share of the whole is the wrong
    denominator for `on: "bar_n"`: MMCA rings a court with four bars and then
    splits one of them into a wing and a gate with a 6.1 m gap between - real
    work, exactly what the sentence says - and it scored 0.029 because the other
    three bars did not move. Below the 0.05 floor, so the sentence was refused
    for a word that did its job.
    """

    if form is None or not prefix:
        return None
    picked = [
        item for item in form.placements
        if item.kind == "additive" and item.role.startswith(prefix)
    ]
    if not picked:
        return None
    shapes = [_plan(item) for item in picked]
    shapes = [shape for shape in shapes if not shape.is_empty]
    if not shapes:
        return None
    # Generously: the word may move its volumes as well as reshape them, and a
    # displaced piece has to stay inside the region it is measured in.
    return unary_union(shapes).buffer(_SCOPE_MARGIN_M)


def changed_share(
    before: SourceMass | None, after: SourceMass | None, region=None
) -> float:
    """How much of the building this word redrew, as a share of the whole.

    Sampled storey by storey and summed, so a word that changes one band of a
    six-band mass reports about a sixth rather than being averaged away. The
    ladder spans whichever mass is taller: a word that only made the building
    higher has changed everything above the old top, and that has to count.
    """

    if after is None:
        return 0.0
    top = max(_height_of(before), _height_of(after))
    if top <= 0.0:
        return 0.0

    differing = 0.0
    total = 0.0
    for index in range(_SAMPLES):
        z = top * (index + 0.5) / _SAMPLES
        one, two = _plan_at(before, z), _plan_at(after, z)
        if one is None and two is None:
            continue
        if one is None:
            two = two.intersection(region) if region is not None else two
            differing += float(two.area)
            total += float(two.area)
            continue
        if two is None:
            one = one.intersection(region) if region is not None else one
            differing += float(one.area)
            total += float(one.area)
            continue
        if region is not None:
            one, two = one.intersection(region), two.intersection(region)
            if one.is_empty and two.is_empty:
                continue
        try:
            differing += float(one.symmetric_difference(two).area)
            total += float(one.union(two).area)
        except Exception:  # pragma: no cover - GEOS refusing a degenerate pair
            continue
    return (differing / total) if total > 1e-9 else 0.0


def check_sentence(parti, *, buildable, axis, height_m, allowed_at=None, storey_height_m=None) -> Verdict:
    """Run the sentence one word at a time and find the words that did nothing."""

    steps = execute_steps(
        parti, buildable=buildable, axis=axis, height_m=height_m,
        storey_height_m=storey_height_m or 0.0,
    )
    declared = tuple(op.verb for op in parti.ops)
    if not steps:
        return Verdict(declared, declared, ())

    def compiled(form):
        return compile_matrix_form(
            form, storey_height_m=storey_height_m, allowed_at=allowed_at
        )

    silent: list[str] = []
    shares: list[float] = []
    previous = None
    previous_form = None
    for op, form in steps:
        current = compiled(form)
        # A scoped word is judged inside its scope, an unscoped one against the
        # whole building - which is what each of them is claiming.
        region = _scope_region(previous_form, str(op.params.get("on") or "").strip())
        share = changed_share(previous, current, region)
        shares.append(share)
        if share < MIN_CHANGED_SHARE:
            silent.append(op.verb)
        previous = current
        previous_form = form
    return Verdict(declared, tuple(silent), tuple(shares))


__all__ = ["Verdict", "changed_share", "check_sentence", "MIN_CHANGED_SHARE"]
