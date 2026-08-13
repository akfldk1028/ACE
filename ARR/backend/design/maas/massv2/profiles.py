"""The base shape a matrix carries, when a square is not what the plan is.

A 4x4 affine can pose anything, but it can only pose what it was given: with a
unit square as the only primitive the vocabulary can say tower, bar and slab and
nothing else. Qatar National Library is a folded plate, the Kunsthal a wedge,
Kanazawa a circle - those are different base shapes, not different transforms.

So a placement carries a normalized unit plan and the matrix does the rest. The
profiles are the repo's own `PROFILED_PRISM_FAMILIES`, normalized into the unit
square so `scale_matrix4((w, d, h))` means the same thing for every one of them.
Nine shapes already agreed on inside this project beats nine invented here.
"""

from __future__ import annotations

from design.maas.geometry_language.base_seeds import PROFILED_PRISM_FAMILIES


UnitPlan = tuple[tuple[float, float], ...]

# The square every other profile is measured against, and the default.
_SQUARE: UnitPlan = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))


def _normalized(ring) -> UnitPlan:
    """Fit a ring into the unit square, keeping its shape.

    Each family is authored at its own size, so scaling by `(w, d, h)` would
    otherwise mean a different footprint per profile and a bar authored as
    `triangular` would come out a different size from the same bar as a box.
    """

    xs = [float(x) for x, _y in ring]
    ys = [float(y) for _x, y in ring]
    span_x = max(max(xs) - min(xs), 1e-9)
    span_y = max(max(ys) - min(ys), 1e-9)
    return tuple(
        ((float(x) - min(xs)) / span_x, (float(y) - min(ys)) / span_y) for x, y in ring
    )


UNIT_PLANS: dict[str, UnitPlan] = {
    "square": _SQUARE,
    **{name: _normalized(ring) for name, ring in PROFILED_PRISM_FAMILIES},
}


def unit_plan(name: str) -> UnitPlan:
    """The named plan, or the square - an unknown name is not worth a crash."""

    return UNIT_PLANS.get(str(name).lower(), _SQUARE)


def plan_names() -> tuple[str, ...]:
    return tuple(sorted(UNIT_PLANS))
