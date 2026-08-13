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
from math import radians, tan
from typing import Any, Iterable, Literal

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


@dataclass(frozen=True)
class Placement:
    """One unit cube, posed by its own matrix.

    `role` is architectural rather than geometric - plinth, slab, tower, court -
    because the downstream selection quotas read roles, not shapes.
    """

    role: str
    matrix: Matrix4
    kind: PlacementKind = "additive"

    def corners(self) -> tuple[tuple[float, float, float], ...]:
        return tuple(transform_point3(self.matrix, corner) for corner in UNIT_BOX_CORNERS)

    def z_span(self) -> tuple[float, float]:
        zs = [corner[2] for corner in self.corners()]
        return min(zs), max(zs)

    def evidence(self) -> dict[str, Any]:
        low, high = self.z_span()
        return {
            "role": self.role,
            "kind": self.kind,
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
    kind: PlacementKind = "additive",
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
    return Placement(role=str(role), matrix=validate_matrix4(matrix), kind=kind)
