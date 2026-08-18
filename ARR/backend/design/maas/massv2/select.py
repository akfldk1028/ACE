"""Choose the sheet an architect would actually look at.

Eighty-eight masses of which forty were distinct compositions is not a portfolio,
it is a contact sheet with the same building printed four times. Filling a grid
cell is a label; the architect chooses between buildings.

Three rules, in order:

  A mass that is lawful but not occupiable is not an option. That judgement is
  `plausibility`, which uses the project's own floor-viability rule.

  A composition seen twice *in one cell* is one composition, and the signature
  is scale-free so that two drawings of the same idea collapse. It is not
  applied across cells: ground take is one of the grid's two axes, so a scheme
  carried along that axis has moved, not repeated. Deduping globally deleted
  the move before the cells were ever looked at - measured on the Uijeongbu
  parcel, raked_bar stood lawful and occupiable in four different cells at an
  articulation of 0.309 and only one copy survived, which handed
  dispersed|solid_body to a scheme scoring 0.280.

  One per grid cell, and the one kept is the most articulate. Cells are filled
  scarcest-first, and a cell prefers a composition no other cell has taken, so
  an abundant cell cannot spend the only occupant a thin cell had.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from design.maas.source_geometry.ir import SourceMass

from .form import MatrixForm
from .measure import FormMeasurement
from .plausibility import Plausibility


@dataclass(frozen=True)
class Candidate:
    form: MatrixForm
    source: SourceMass
    measurement: FormMeasurement
    plausibility: Plausibility
    cell: str
    ground_take: float
    far_utilization: float


def composition_signature(form: MatrixForm) -> tuple:
    """What this composition is, independent of how big it was drawn.

    Every volume is expressed as a fraction of the whole form's bounding box, so
    a scheme and the same scheme at 45% ground take collapse to one signature.
    Rounding is coarse on purpose: two volumes a few centimetres apart in a
    sixty-metre composition are the same design decision.
    """

    additive = form.additive()
    if not additive:
        return ()
    corners = [corner for item in additive for corner in item.corners()]
    min_x = min(x for x, _y, _z in corners)
    max_x = max(x for x, _y, _z in corners)
    min_y = min(y for _x, y, _z in corners)
    max_y = max(y for _x, y, _z in corners)
    min_z = min(z for _x, _y, z in corners)
    max_z = max(z for _x, _y, z in corners)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    span_z = max(max_z - min_z, 1e-6)

    entries = []
    for item in form.placements:
        item_corners = item.corners()
        xs = [x for x, _y, _z in item_corners]
        ys = [y for _x, y, _z in item_corners]
        zs = [z for _x, _y, z in item_corners]
        entries.append((
            item.kind,
            round((min(xs) - min_x) / span_x, 2),
            round((min(ys) - min_y) / span_y, 2),
            round((min(zs) - min_z) / span_z, 2),
            round((max(xs) - min(xs)) / span_x, 2),
            round((max(ys) - min(ys)) / span_y, 2),
            round((max(zs) - min(zs)) / span_z, 2),
        ))
    return tuple(sorted(entries))


# How many volumes a winning Korean entry is made of. Measured across 2014-2024
# competition winners by small practices: 3.4 masses, 1.3 external vertical
# circulations, 2.5 three-dimensional exterior spaces, 2 principal cladding
# materials (김경율, 서울대 석사, 2026).
#
# A preference and not a gate. Six volumes is not unlawful, it is simply not
# what wins there, and the number is a distribution rather than a rule - which
# is the mistake `MIN_TIER_CONTRAST` made in the other direction, legislating
# a property that should have emerged. It applies only where the evidence
# does: a brief in hand means this sheet is being judged as a Korean entry.
CORPUS_PIECES = 3.4

# 연면적 ±5% is close to universal across the 설계공모지침서 examined; the same
# documents make exceeding it a deduction and then a disqualification.
BRIEF_TOLERANCE = 0.05

# How little of the parcel's 용적률 an unbriefed scheme may deliver and still be
# an alternative. Half of `fill._TARGET_FLOOR`: the growth loop aims at 0.75 and
# a scheme that lands under half of that did not choose a low coverage, it ran
# out of moves. Kept loose on purpose - the point is to refuse the house on the
# 2,499 m2 parcel, not to push every scheme toward the ceiling, which is the
# objective the critics scored worst (rho -0.73 against their own ranking).
MINIMUM_DELIVERED_SHARE = 0.375

# How many tiles one composition may occupy. See `family_of`: two cells apart is
# the same scheme moved along an axis and is worth showing twice; three is the
# same drawing printed three times.
MAX_TILES_PER_FAMILY = 2


def _brief_tolerance(item) -> float | None:
    """How far off the brief this scheme is, or None if it has no brief."""

    target = item.form.extra.get("programme_target")
    capacity = float(item.form.extra.get("far_capacity_m2") or 0.0)
    if not target or capacity <= 0.0:
        return None
    delivered = item.far_utilization * capacity
    return abs(delivered - float(target)) / float(target)


def piece_count(form: MatrixForm) -> int:
    """Volumes as placed, not as the compiler sliced them.

    The compiler cuts every volume at each storey, so counting bands reports a
    single deformed mass - which is BIG's own signature in seven of ten - at
    six and a half pieces.
    """

    return sum(1 for _item in form.additive())


def _piece_distance(item: Candidate) -> float:
    """How far this scheme sits from the corpus, in whole volumes.

    Rounded, so it separates a three-piece scheme from a seven-piece one and
    stays silent between three and four.
    """

    if item.form.extra.get("programme_target") is None:
        return 0.0
    return round(abs(piece_count(item.form) - CORPUS_PIECES))


def _shape_work(item: Candidate) -> float:
    """How much shaping this scheme did, by whichever means it chose.

    Carving in plan and changing in section are not two things a building owes;
    they are two ways of doing the same one. A courtyard block is carved and
    never steps. A stepped tower steps and is convex in every plan. Listing
    them as separate objectives asks each to be both, and balance then punishes
    whichever it is not - measured on the live parcel, that handed
    full_ground|solid_body to a scheme at 0.05 articulation over `stacked_45`
    at 0.55, purely because the stepped one was flat in plan.

    So they are one objective, taken by the larger. Balance belongs between
    things a scheme genuinely owes at the same time - floor area and form -
    and a maximum belongs between substitutes. Using the same rule for both is
    what went wrong, in each direction: a maximum over everything let a scheme
    win on plan void alone, and a leximin over everything let a scheme win by
    being mediocre evenly.
    """

    return max(item.measurement.convexity_drop, item.measurement.section_change)


def _spoken_force(item: Candidate) -> float:
    """How much of the building each word of its sentence actually redrew.

    Both objectives that used to be here score negatively against the only
    judgement of these sheets that comes from outside the geometry. Three
    subagents compared thirty pairs of the ten Uijeongbu alternatives without
    seeing each other's verdicts, and against that ranking:

        far_utilization   rho -0.26     shape_work    rho -0.23
        articulation      rho -0.31     plan_void     rho -0.48

    The selector was rewarding, one for one, what the critics were marking
    down - `kahn_kimbell` came last on every pairing while leading the field on
    both objectives. 용적률 had already measured rho -0.73 against an earlier
    critique round, so this is the third independent look saying the same thing.

    What does predict is whether the words did any work: mean redraw per word
    scores rho +0.62, and the critics' own language for the schemes that won is
    that the operation is visible - "one operation you name in three seconds",
    "the verb is legible in every edge". A mass whose sentence is invisible is
    the failure they tagged seventeen times.

    It is one objective on purpose, and that is a reversal of the note in
    `_balance_keys`. Simulated over the same ten, the balanced pairs are all
    worse than this alone: with far +0.43, with plan compactness +0.50, with a
    word count +0.62 and no better. The warning that note carries was earned by
    articulation, which is a property of a shape; this is a property of a
    sentence, and the sheet is a sheet of sentences.

    A seed family has no sentence, so it reads 0.0 and cannot win a cell it is
    sharing with an authored one. That is the intended reading rather than a
    fallback: this sheet is for options somebody wrote.
    """

    return float(item.form.extra.get("spoken_force") or 0.0)


# What a scheme is asked to be good at, once its cell has already said where it
# sits. Neither grid coordinate is here and that is deliberate: ground take and
# plan void are the axes, so scoring them scores the thing every occupant of a
# cell has in common.
OBJECTIVES: tuple[tuple[str, Any], ...] = (
    ("spoken_force", _spoken_force),
)

# ⚠️ One objective, so `_balance_keys` degenerates for the overseas edition: a
# one-tuple sorts to itself, and comparing one-tuples is comparing one number.
# The balance criterion below is live only on the briefed path, which has two.
#
# That is not an oversight to quietly patch. `far` and `shape_work` were here
# and were removed on measurement - their correlation with the critics' ranking
# flipped sign between rounds, -0.23 then +0.33, while `spoken_force` held at
# +0.67 and +0.48. Putting a second axis back means finding one that survives a
# judged comparison, not one that makes this tuple longer. Until then the
# overseas sheet is chosen by a single number and this comment says so.


def _brief_fit(item: Candidate) -> float:
    """How near the delivered floor area is to what the brief asked for.

    Under a brief, 용적률 utilisation stops being an objective - every scheme
    is supposed to arrive at the same number, and the sheet is judged on
    hitting it. A 설계공모지침서 gives 연면적 with a ±5% tolerance and treats
    exceeding it as a deduction and then a disqualification, so nearer is
    simply better and there is no credit for more.
    """

    target = item.form.extra.get("programme_target")
    if not target:
        return item.far_utilization
    delivered = item.far_utilization * _far_capacity(item)
    return 1.0 - min(1.0, abs(delivered - float(target)) / float(target))


def _far_capacity(item: Candidate) -> float:
    """Recover the parcel's capacity from the share the candidate carries."""

    return float(item.form.extra.get("far_capacity_m2") or 0.0)


def _ground_released(item: Candidate) -> float:
    """How much of the ground the building gave back.

    The Korean reading of a good mass is the opposite of the one this module
    started with. Its praise vocabulary is about a building imposing less -
    "규모에 비해 가볍고 경쾌", "매스가 덜 느껴져서 좋음", "볼륨을 줄이는 효과",
    "1층의 비워놓기 공간 계획" - and winners include a 청년문화센터 at 7.88%
    건폐율 and a 커뮤니티센터 at 6.94%. Articulation is not what they are
    scoring; how little ground the building takes is closer to it.
    """

    return 1.0 - min(1.0, max(0.0, item.ground_take))


# What a scheme is asked to be good at once a brief says how large it is. The
# pair above stops meaning anything there: every scheme targets the same floor
# area, and the mass a Korean jury rewards is the plain one with a good yard,
# which `shape_work` scores down by construction. Measured across the mixed
# corpus, the Korean sentences average 0.317 articulation against 0.407 for the
# international ones and were selected once in ten deliveries despite a 100%
# survival rate - the selector was refusing what the research says wins.
BRIEFED_OBJECTIVES: tuple[tuple[str, Any], ...] = (
    ("brief_fit", _brief_fit),
    ("ground_released", _ground_released),
)


def _balance_keys(pool: list[Candidate]) -> dict[int, tuple[float, ...]]:
    """Score every candidate on how balanced it is, with no weights.

    ⚠️ Live on the briefed path only. `OBJECTIVES` is one entry long, so for the
    overseas edition everything below reduces to maximising `spoken_force` -
    see the note there for why a second axis has not simply been added back.

    A single number decided cells until now and it picked the worse building.
    `splayed_fan` topped its cell at an articulation of 0.79 while measuring
    almost nothing in section or in carving, because a maximum only has to be
    large once - and all five schemes rewritten against the critic's notes lost
    to the versions they were meant to replace.

    So: normalise each objective across the pool, then compare candidates by
    their objectives sorted worst-first. A scheme wins by having no weak side,
    not by having one strong one. This is the criterion behind T-DominO (Gaier,
    Stoddart, Villaggi, Bentley, PPSN 2022), which reports that a quarter of
    NSGA-II's solutions clear the lower quartile on all five of its objectives
    against 99% of its own - the same "nothing passes on every count" symptom
    this sheet has had all along. Sorting is monotone in Pareto dominance, so a
    scheme better on every objective still wins outright; balance only decides
    the cases dominance leaves open, which is most of them.
    """

    # A brief changes what the sheet is being judged on, so it changes the axes.
    objectives = (
        BRIEFED_OBJECTIVES
        if pool and pool[0].form.extra.get("programme_target") is not None
        else OBJECTIVES
    )

    spans: list[tuple[float, float]] = []
    for _name, read in objectives:
        values = [float(read(item)) for item in pool]
        low, high = (min(values), max(values)) if values else (0.0, 0.0)
        spans.append((low, high))

    keys: dict[int, tuple[float, ...]] = {}
    for item in pool:
        scaled = []
        for (_name, read), (low, high) in zip(objectives, spans):
            width = high - low
            scaled.append((float(read(item)) - low) / width if width > 1e-9 else 1.0)
        # Worst-first, so comparing two keys compares their weakest sides first.
        keys[id(item)] = tuple(sorted(scaled))
    return keys


def choose(
    candidates: Iterable[Candidate],
    *,
    require_occupiable: bool = True,
    per_cell: int = 1,
) -> list[Candidate]:
    """Drop what cannot be occupied, then fill each cell with its best occupant."""

    pool = [
        candidate
        for candidate in candidates
        if not (require_occupiable and not candidate.plausibility.occupiable)
    ]
    # A brief is checked before the drawing is looked at. Korean 설계공모지침서
    # give 연면적 with a ±5% tolerance, deduct for missing it and disqualify for
    # missing it badly, and the check happens at 기술검토위원회 ahead of the jury.
    # So it is a gate, not an objective: scoring it against ground released let
    # a scheme buy its way past the brief by giving back more ground, and brief
    # conformance fell from 8 of 10 to 5.
    briefed = [item for item in pool if _brief_tolerance(item) is not None]
    if briefed:
        inside = [item for item in briefed if _brief_tolerance(item) <= BRIEF_TOLERANCE]
        if inside:
            pool = inside
    else:
        # With no brief, the parcel is the brief. A scheme that delivers a
        # fraction of what the site affords is not a low-coverage proposition,
        # it is a scheme that could not grow: Villa dall'Ava came out at 5.5%
        # 건폐율 and 578 m2 on a 2,499 m2 parcel - a house - and went onto the
        # sheet as an alternative.
        #
        # Low coverage IS how some Korean winners work (7.88%, 6.94%), but they
        # get there against a 소요면적표 that asks for little, which is the
        # briefed branch above. Unbriefed, the floor is `fill`'s own growth
        # target: a scheme that cannot reach it has failed at the thing the
        # growth loop exists to do, and saying so here keeps the judgement in
        # one place rather than adding a second opinion about the same number.
        standing = [item for item in pool if item.far_utilization >= MINIMUM_DELIVERED_SHARE]
        if standing:
            pool = standing
    keys = _balance_keys(pool)

    def rank(item: Candidate) -> tuple:
        return (keys[id(item)], item.far_utilization)

    by_cell: dict[str, dict[tuple, Candidate]] = {}
    for candidate in pool:
        signature = composition_signature(candidate.form)
        cell = by_cell.setdefault(candidate.cell, {})
        held = cell.get(signature)
        if held is None or rank(candidate) > rank(held):
            cell[signature] = candidate

    # Scarcest cell first. A cell with one lawful occupant has no second choice,
    # so it picks before a cell holding a dozen - otherwise the abundant cell
    # takes the composition and the thin one is left empty or with junk.
    order = sorted(by_cell, key=lambda cell: (len(by_cell[cell]), cell))

    taken: set[str] = set()
    times: dict[str, int] = {}
    chosen: list[Candidate] = []
    for cell in order:
        # A family that has already had its two outings is out of the running,
        # not merely sorted below. Preferring the unseen is what `taken` does,
        # and it is enough only while some other family is available in the
        # cell - `lab_city` took four of thirteen tiles the moment a change in
        # the geometry made it rank first in cells where nothing else did.
        #
        # Two is the number `family_of` argues for directly: two cells apart is
        # a move along an axis and belongs on the sheet twice, three cells apart
        # is the same drawing printed three times.
        available = [
            item for item in by_cell[cell].values()
            if times.get(family_of(item), 0) < MAX_TILES_PER_FAMILY
        ]
        if not available:
            # The cell goes empty rather than take a third copy. Measured on the
            # 의정부 sheet, four cells had exactly one sentence able to occupy
            # them - the high ground-take column, which only a handful of
            # compositions can reach at all - and `lab_city` printed four times
            # out of thirteen tiles. An empty cell says the supply does not
            # reach here, which is true and useful; a repeated tile says it does,
            # which is neither. This module opens by refusing exactly that trade.
            continue
        ranked = sorted(
            available,
            # An unseen composition first: the sheet is a set of options, and an
            # option the architect has already been shown is worth less than one
            # they have not, even when it measures a little better.
            #
            # Then, where a brief says this is being judged as a Korean entry,
            # the scheme whose volume count is nearer the winners'. Negated so
            # that nearer sorts higher under the reverse below, and rounded so
            # it only speaks when the difference is whole volumes.
            key=lambda item: (
                family_of(item) not in taken,
                -_piece_distance(item),
                rank(item),
            ),
            reverse=True,
        )
        for candidate in ranked[:max(1, per_cell)]:
            family = family_of(candidate)
            taken.add(family)
            times[family] = times.get(family, 0) + 1
            chosen.append(candidate)
    return chosen


def family_of(candidate: Candidate) -> str:
    """Which composition this is, before the coverage axis restated it.

    Two cells apart, the same scheme is a move along an axis and belongs on the
    sheet twice - that is what deduping globally got wrong. Three cells apart it
    is the same drawing printed three times, which is what happened the moment
    the ranking changed: `hollow_market_arch` took the arch cell, then took two
    more, and the sixteen tiles read as nine buildings.

    Both suffixes have to be cut, not just the coverage one. A siting copy is
    the same composition standing somewhere else, and keeping `^off_open` in
    the key made it a new family - so `plate_on_four_supports` printed twice on
    one sheet, and `lifted_back_court` twice more.

    The geometry signature cannot police that either, because it is what the
    coverage variants legitimately differ in - growing a scheme wider and growing it
    taller both change its proportions, so its own copies stop matching it. The
    name the variants were derived from does not move, so that is what is
    remembered across cells. Within a cell the signature still rules, since
    there the question really is whether two drawings are one design.
    """

    name = candidate.form.name
    for mark in ("~", "^"):
        name = name.split(mark, 1)[0]
    return name


def summary(chosen: list[Candidate], *, considered: int) -> dict[str, Any]:
    return {
        "schema_version": "arr.maas.massv2_selection.v1",
        "considered": considered,
        "distinct_compositions": len({composition_signature(item.form) for item in chosen}),
        "chosen": len(chosen),
        "cells": sorted({item.cell for item in chosen}),
    }
