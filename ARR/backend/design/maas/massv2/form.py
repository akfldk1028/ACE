"""A mass as placed volumes, not a box with dents cut into it.

Measured on the live Uijeongbu parcel, every operative in the existing language
tops out around 0.2-0.29 departure from its own convex hull, because all of them
are face operations on one solid. `source_geometry/stacked_volume_bank.py` had
already written the diagnosis: 80 of 86 programs were a single box with a single
modifier, while the reference competition massing is three or four clean
orthogonal volumes stacked and shifted - and nothing in the geometry layer ever
prevented that. What was missing was a way to author it.

A `Placement` is one unit cube carried by a 4x4 affine. That is the same
representation the repo already normalizes every box into
(`geometry_language/programs.py` rewrites `box(w,d,h)` into the canonical
1x1x1 UnitBox plus a `scale_matrix4`), and the same one the current
building-massing state of the art uses - BuildingBlock (SIGGRAPH 2025)
generates massing as an unordered set of boxes, and PrimitiveAnything
(SIGGRAPH 2025) parameterizes every primitive as (class, translation, rotation,
scale). Neither uses CSG at massing scale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from math import radians, tan
from typing import Any, Iterable, Literal

from .profiles import unit_plan

from design.maas.geometry_language.affine_matrix import (
    Matrix4,
    compose_matrix4,
    rotation_matrix4,
    scale_matrix4,
    shear_matrix4,
    transform_point3,
    translation_matrix4,
    validate_matrix4,
)


PlacementKind = Literal["additive", "subtractive"]

# The unit cube this language places, corners in the order the affine sees them.
UNIT_BOX_CORNERS: tuple[tuple[float, float, float], ...] = (
    (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0),
)


@lru_cache(maxsize=None)
def _unit_corners(plan: str) -> tuple[tuple[float, float, float], ...]:
    """The unposed solid for a plan name. There are nine of these in the language."""

    ring = unit_plan(plan)
    return tuple((x, y, level) for level in (0.0, 1.0) for x, y in ring)


@dataclass(frozen=True)
class Placement:
    """One unit cube, posed by its own matrix.

    `role` is architectural rather than geometric - plinth, slab, tower, court -
    because the downstream selection quotas read roles, not shapes.
    """

    role: str
    matrix: Matrix4
    kind: PlacementKind = "additive"
    # The unit plan this matrix carries. A square is a tower, a bar and a slab;
    # a wedge, a folded plate and a circle are different base shapes, not
    # different transforms, and no matrix can turn one into another.
    plan: str = "square"
    # A tilted top, in the volume's own terms: the top face drops by this
    # share of the volume's height along `drop_toward` (world unit vector).
    # Compile carries it onto the band that holds this volume's top.
    top_drop: float = 0.0
    drop_toward: tuple[float, float] | None = None
    # The house section as ONE volume: when `ridge_along` (world unit vector,
    # the ridge line's direction through the plan centroid) is set instead of
    # `drop_toward`, the top drops by `top_drop` of the height on BOTH sides
    # of that line, full drop at the farthest eave. It exists because the
    # pentagon was first said as two independent half-wedges, and any later
    # word that scaled plans - a coverage retarget scales each volume about
    # its own centre - pulled the ridge apart into a slot. A section is a
    # base shape, not an assembly; one volume survives every transform whole.
    ridge_along: tuple[float, float] | None = None
    # Is this volume a room, or is it what holds a room up. A column is meant
    # to be thin and a storey is not, so every rule about how wide or how deep
    # a plate must be has to know which of the two it is looking at. The
    # executor already made the distinction - it lets a support under a lifted
    # plate be shorter than a storey - and then threw it away at placement, so
    # the gates downstream had no way to tell a column from a sliver of floor.
    occupiable: bool = True

    def unit_corners(self) -> tuple[tuple[float, float, float], ...]:
        """The unit solid before posing: this placement's plan, at z 0 and 1."""

        return _unit_corners(self.plan)

    def corners(self) -> tuple[tuple[float, float, float], ...]:
        """Pose the unit solid, once per placement.

        A placement is frozen, so its corners are a property of it rather than
        a question to be re-answered. They were being recomputed on every call:
        profiled over the seventy-six authored sentences, `corners` ran 681,531
        times and drove 6.3 million matrix transforms - 103 of 180 seconds -
        because the growth loop refits a scheme up to twenty-four times, every
        fit compiles it, and every compile walks the same eight points again.
        `z_span` asked for them a second time on top of that.

        The cached value is the tuple the transform produced, so the numbers
        are bit-identical and the exactness oracle in
        `design/test_maas_affine_matrix_exactness.py` still reads the same
        matrices. Frozen dataclasses compare on their declared fields, so a
        cache in the instance dict changes neither equality nor hashing.
        """

        cached = self.__dict__.get("_corners_cache")
        if cached is None:
            cached = tuple(
                transform_point3(self.matrix, corner) for corner in self.unit_corners()
            )
            object.__setattr__(self, "_corners_cache", cached)
        return cached

    def z_span(self) -> tuple[float, float]:
        cached = self.__dict__.get("_z_span_cache")
        if cached is None:
            zs = [corner[2] for corner in self.corners()]
            cached = (min(zs), max(zs))
            object.__setattr__(self, "_z_span_cache", cached)
        return cached

    def evidence(self) -> dict[str, Any]:
        low, high = self.z_span()
        return {
            "role": self.role,
            "kind": self.kind,
            "plan": self.plan,
            "z_low": round(low, 4),
            "z_high": round(high, 4),
            "matrix4": [list(row) for row in self.matrix],
        }


@dataclass(frozen=True)
class MatrixForm:
    """An authored mass: placements plus the language that explains them.

    The `language` fields are not decoration. `SourceMass.signature()` reads
    them into `props["source_signature"]`, and every diversity quota in
    `design/maas/selection/` keys off that. A form that leaves them empty
    collapses into one "unknown" family and is culled before it is ever seen.
    """

    name: str
    placements: tuple[Placement, ...]
    primary_language: str
    secondary_language: str = ""
    formal_principle: str = ""
    dominant_gesture: str = ""
    reference_basis: str = ""
    # A gallery is not a shop and neither is a gym. Fixing every scheme at the
    # zoning storey height makes floor count a function of the parcel alone,
    # when it is a decision about the programme - and it is the decision that
    # moves 용적률, because floor area is plan times storeys. Left unset the
    # parcel's own value is used.
    floor_height_m: float | None = None
    notes: tuple[str, ...] = ()
    extra: dict[str, Any] = field(default_factory=dict)

    def additive(self) -> tuple[Placement, ...]:
        return tuple(item for item in self.placements if item.kind == "additive")

    def subtractive(self) -> tuple[Placement, ...]:
        return tuple(item for item in self.placements if item.kind == "subtractive")

    def height_m(self) -> float:
        """Total height, measured from the additive volumes only.

        A subtractive volume is allowed to overshoot so its cut reaches cleanly
        through the top or bottom face; letting it set the height would inflate
        the building by however far the cutter was pushed out.
        """

        spans = [item.z_span() for item in self.additive()]
        if not spans:
            return 0.0
        return max(high for _low, high in spans) - min(low for low, _high in spans)

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.matrix_form.v1",
            "name": self.name,
            "placement_count": len(self.placements),
            "additive_count": len(self.additive()),
            "subtractive_count": len(self.subtractive()),
            "height_m": round(self.height_m(), 3),
            "floor_height_m": self.floor_height_m,
            "primary_language": self.primary_language,
            "secondary_language": self.secondary_language,
            "formal_principle": self.formal_principle,
            "dominant_gesture": self.dominant_gesture,
            "placements": [item.evidence() for item in self.placements],
        }


def place(
    role: str,
    *,
    size: Iterable[float],
    at: Iterable[float] = (0.0, 0.0, 0.0),
    rotation_degrees: float = 0.0,
    lean_degrees: float = 0.0,
    lean_axis: str = "x",
    plan: str = "square",
    kind: PlacementKind = "additive",
    occupiable: bool = True,
) -> Placement:
    """Build a placement from the terms an architect actually says.

    Size and position are metres in the site-local frame; `at` is the volume's
    own lower corner, not its centre, so a stack reads as a list of heights
    rather than a list of half-heights.

    Rotation is applied about the volume's own centre in plan. Rotating about
    the origin instead would couple orientation to position, so nudging a
    volume sideways would also swing it.

    `lean_degrees` shears the volume off vertical about its own base, which is
    the move that separates a stack of boxes from the massing those offices are
    known for - a leaning tower, a bar that rakes as it rises. It costs nothing
    that an upright volume does not: shear is one more term in the same matrix,
    and `affine_matrix.shear_matrix4` was already here, unused.

    Leaning about the base rather than the centre keeps the volume standing on
    the ground it was placed on; shearing about the centre would push its
    footprint half a lean off the plan the author drew.
    """

    width, depth, height = (float(value) for value in size)
    x, y, z = (float(value) for value in at)
    matrix = compose_matrix4(scale_matrix4((width, depth, height)), translation_matrix4((x, y, z)))
    if abs(lean_degrees) > 1e-9:
        axis = "y" if str(lean_axis).lower() == "y" else "x"
        amount = tan(radians(max(-60.0, min(60.0, float(lean_degrees)))))
        matrix = compose_matrix4(
            matrix,
            translation_matrix4((0.0, 0.0, -z)),
            shear_matrix4(axis, "z", amount),
            translation_matrix4((0.0, 0.0, z)),
        )
    if abs(rotation_degrees) > 1e-9:
        centre = (x + width / 2.0, y + depth / 2.0, 0.0)
        matrix = compose_matrix4(
            matrix,
            translation_matrix4((-centre[0], -centre[1], 0.0)),
            rotation_matrix4((0.0, 0.0, float(rotation_degrees))),
            translation_matrix4(centre),
        )
    return Placement(
        role=str(role),
        matrix=validate_matrix4(matrix),
        kind=kind,
        plan=str(plan),
        occupiable=bool(occupiable) and kind == "additive",
    )


def stack(
    role: str,
    *,
    size: Iterable[float],
    at: Iterable[float] = (0.0, 0.0, 0.0),
    storeys: int = 8,
    twist_degrees: float = 0.0,
    taper: float = 1.0,
    drift: Iterable[float] = (0.0, 0.0),
    plan: str = "square",
    kind: PlacementKind = "additive",
    rotation_degrees: float = 0.0,
    occupiable: bool = True,
) -> tuple[Placement, ...]:
    """A volume whose section changes as it rises, cut into storeys.

    One affine matrix can translate, scale, rotate, shear and mirror, and any
    composition of those - but it cannot twist, taper or bend, because those are
    transforms that *vary* with height and a single matrix is linear. The
    graphics answer is to subdivide: a twisted tower is a stack of thin slabs,
    each with its own matrix, turned a little further than the one below.

    That is what this returns. `twist_degrees` is the total turn from base to
    top, `taper` the ratio of the top plan to the base plan, and `drift` how far
    the top slides in plan - the three moves behind a twisted tower, a tapering
    one, and a leaning one respectively.

    `storeys` is the resolution, and a storey is the right one: the building is
    made of floors, so a slab per floor is exactly as fine as the thing being
    described.

    `rotation_degrees` is the frame's own bearing, which every volume on a site
    carries; `twist_degrees` turns on top of it. Separating them matters because
    a stack that inherited only the twist would come out square to the north on
    a parcel that is not.
    """

    width, depth, height = (float(value) for value in size)
    x, y, z = (float(value) for value in at)
    drift_x, drift_y = (float(value) for value in drift)
    count = max(1, int(storeys))
    slab = height / count

    out: list[Placement] = []
    for index in range(count):
        # Sampled at the middle of each slab rather than its base, so the stack
        # approximates the continuous form symmetrically instead of lagging it.
        t = (index + 0.5) / count
        scale = 1.0 + (float(taper) - 1.0) * t
        slab_w, slab_d = width * scale, depth * scale
        out.append(
            place(
                role,
                # Slabs meet on a shared face. Overlapping them is what you do
                # to keep a boolean kernel out of a degenerate case, and this
                # pipeline has none - `compile` cuts bands at the z values the
                # volumes declare, so an overlap declares one extra band per
                # joint carrying the plan of the slab below (ff22aa8).
                size=(slab_w, slab_d, slab),
                at=(
                    x + (width - slab_w) / 2.0 + drift_x * t,
                    y + (depth - slab_d) / 2.0 + drift_y * t,
                    z + index * slab,
                ),
                rotation_degrees=float(rotation_degrees) + float(twist_degrees) * t,
                plan=plan,
                kind=kind,
                occupiable=occupiable,
            )
        )
    return tuple(out)
