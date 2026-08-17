"""Turn placed volumes into the `SourceMass` the rest of the pipeline expects.

There is no 3D CSG here and that is the point. A `SourceVolume` in this codebase
is already (plan polygon x normalized height band), so a matrix-placed box lands
in it directly: transform the eight corners, take the plan hull and the z span,
cut bands at the z values the volumes themselves declare, and resolve each band
with 2D shapely. For comparison, the eleven BOOK macros spend 23 boolean kernel
calls and 11 `decompose()` traversals to produce one solid, and `exact_compile`
is 96% of a portfolio run's wall clock.

Subtraction is per band, so a court that is roofed over still reads as a court
in the bands below the roof - the flattened-union measurement that hid exactly
that case is what this representation avoids by construction.

What it cannot say, so that the next person does not spend the afternoon again:
a roof that is not flat. Every `SourceVolume` is (plan polygon x height band),
which is a prism with a level top and a level bottom, and there is no plane
term anywhere to tilt one. A pitched roof - 박공, and the vaults Kimbell is
named for - has no representation here at all.

Approximating one by stacking thin tapering slabs was tried and measured, and
it gets worse with resolution rather than better: the same bar at 5 steps came
out at 0.29 articulation over 0.81 ground take, and at 24 steps at 0.09 over
0.94 - a corrugated pad, not a roof, because `taper` scales about the centre so
every added slab sits nearer full size. The stripes are the renderer stroking
each slab, but smoothing only the drawing would be worse than the stripes:
`measure`, `plausibility` and `legal_fit` all read the steps, so the picture
would stop agreeing with every number under it.

A designed roof needs a sloped top on the volume itself - a plane term on
`SourceVolume` and every consumer of it - and until that exists the silhouettes
this package produces are flat tops with whatever the sunlight envelope sliced
off them. Which is what the critics keep saying: `roof-is-envelope-residue`,
22 times across 30 comparisons, their most frequent complaint by a wide margin.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from design.maas.source_geometry.ir import SourceMass, SourceVolume

from design.maas.geometry_language.affine_matrix import transform_point3

from .form import MatrixForm, Placement
from .profiles import unit_plan


# Bands thinner than this are float noise from two volumes meeting at a shared
# level, not a storey; merging them keeps the band list readable.
_MINIMUM_BAND_M = 0.05
# A band whose remaining plan is slighter than this was cut away, not built.
_MINIMUM_BAND_AREA_M2 = 1.0


def _plan(placement: Placement) -> Polygon:
    """Plan outline of a posed box, over its whole height.

    The convex hull of the eight projected corners is exact for any affine image
    of a cube - the projection of a convex solid is convex - so this stays right
    under rotation and shear without needing a mesh. This is the right measure
    for 건축면적, which is the projection of the whole building.
    """

    hull = Polygon([(x, y) for x, y, _z in placement.corners()]).convex_hull
    return hull if isinstance(hull, Polygon) else Polygon()


def _plan_between(placement: Placement, low: float, high: float) -> Polygon:
    """Plan outline of the part of a volume that lies between two heights.

    For an upright box this is the same rectangle at every height, so it agrees
    with `_plan`. For a leaning one it does not, and the difference is the whole
    point: shearing a tower moves its plan sideways as it rises, and taking the
    hull over its full height instead reports one big parallelogram that no
    storey actually has. A leaning tower measured that way came out with a single
    band and zero articulation - the move was in the geometry and invisible to
    every measure downstream.

    The cross-section of an affine cube at a given height is the image of the
    unit square at the corresponding local level, so the two bounding levels are
    enough; anything between them is inside their hull.
    """

    low_z, high_z = placement.z_span()
    span = high_z - low_z
    if span <= 1e-9:
        return _plan(placement)
    lower = max(0.0, min(1.0, (low - low_z) / span))
    upper = max(0.0, min(1.0, (high - low_z) / span))
    ring = unit_plan(placement.plan)
    points = [
        (x, y)
        for level in (lower, upper)
        for x, y, _z in (
            transform_point3(placement.matrix, (corner[0], corner[1], level))
            for corner in ring
        )
    ]
    hull = Polygon(points).convex_hull
    return hull if isinstance(hull, Polygon) else Polygon()


def _band_edges(form: MatrixForm, *, storey_height_m: float | None = None) -> list[float]:
    """Cut heights, taken from the volumes' own tops and bottoms.

    Sampling at a fixed count would put band edges where no volume changes, and
    would miss a setback that happens between two samples.

    A volume that leans is the exception: its plan moves continuously, so its own
    top and bottom are the only edges it declares and the whole tilt collapses
    into one band. Measured that way a tower leaning 35 degrees reported a single
    band and zero articulation. Those are cut at storeys instead, which is the
    interval the building is actually made of.
    """

    additive = form.additive()
    if not additive:
        return []
    edges: set[float] = set()
    for placement in form.placements:
        low, high = placement.z_span()
        edges.add(round(low, 4))
        edges.add(round(high, 4))
        if storey_height_m and storey_height_m > 1e-6 and _leans(placement):
            level = low + storey_height_m
            while level < high - 1e-6:
                edges.add(round(level, 4))
                level += storey_height_m
    ground = min(low for low, _high in (item.z_span() for item in additive))
    roof = max(high for _low, high in (item.z_span() for item in additive))
    ordered = sorted(value for value in edges if ground - 1e-9 <= value <= roof + 1e-9)
    merged: list[float] = []
    for value in ordered:
        if not merged or value - merged[-1] >= _MINIMUM_BAND_M:
            merged.append(value)
    if merged and roof - merged[-1] >= _MINIMUM_BAND_M:
        merged.append(roof)
    elif merged:
        merged[-1] = roof
    return merged


def _spans(placement: Placement, low: float, high: float) -> bool:
    """Does this volume occupy the open interval, rather than just touch it."""

    z_low, z_high = placement.z_span()
    middle = (low + high) / 2.0
    return z_low - 1e-9 <= middle <= z_high + 1e-9


def _band_parts(
    form: MatrixForm, low: float, high: float, allowed_at=None
) -> list[Polygon]:
    """Every plan piece this band occupies, not just the biggest one.

    Two bars with a gap are two pieces at their own storeys, and keeping only
    the larger one would delete half the building - which is exactly what made
    a paired-bar scheme read as 0.05 open instead of a quarter open. The
    existing bridge does the same thing (`source_bridge._polygon_parts`): each
    piece becomes its own volume record and they share the band's fractions,
    because height bands are legal proxies of one component, not separate
    buildings.
    """

    built = [
        _plan_between(item, low, high)
        for item in form.additive()
        if _spans(item, low, high)
    ]
    built = [item for item in built if not item.is_empty and item.area > 0.0]
    if not built:
        return []
    shape = unary_union(built)
    if allowed_at is not None:
        # The legal line cuts the building; it does not shrink it. A volume that
        # runs past the setback is built up to it and stops, which is what an
        # architect draws and what the compiler can represent - a band is an
        # arbitrary polygon here, not a rectangle. Shrinking it instead put the
        # ceiling on ground take at the largest rectangle *inscribed* in the
        # buildable polygon, and on 의정부 4115011300106840001 that polygon is
        # 1922 m2 inside a 3707 m2 bounding box, so the median scheme claimed
        # 0.38 of a 건폐율 it was allowed to fill.
        allowed = allowed_at((low + high) / 2.0)
        if allowed is None or allowed.is_empty:
            return []
        shape = shape.intersection(allowed)
        if shape.is_empty:
            return []
    cutters = [
        _plan_between(item, low, high)
        for item in form.subtractive()
        if _spans(item, low, high)
    ]
    cutters = [item for item in cutters if not item.is_empty and item.area > 0.0]
    if cutters:
        shape = shape.difference(unary_union(cutters))
    if shape.is_empty:
        return []
    parts = list(shape.geoms) if isinstance(shape, MultiPolygon) else [shape]
    return [
        part
        for part in parts
        if isinstance(part, Polygon) and part.area >= _MINIMUM_BAND_AREA_M2
    ]


def _leans(placement: Placement) -> bool:
    """Does this volume's plan move as it rises."""

    low, high = placement.z_span()
    if high - low <= 1e-9:
        return False
    bottom = _plan_between(placement, low, low + (high - low) * 0.02)
    top = _plan_between(placement, high - (high - low) * 0.02, high)
    if bottom.is_empty or top.is_empty:
        return False
    union = bottom.union(top)
    if union.is_empty or float(union.area) <= 1e-9:
        return False
    return float(bottom.symmetric_difference(top).area) / float(union.area) > 0.02


def compile_matrix_form(
    form: MatrixForm,
    *,
    verb: str = "matrix_place",
    storey_height_m: float | None = None,
    allowed_at=None,
) -> SourceMass | None:
    """Compile placements into a `SourceMass`, or `None` if nothing survives.

    `allowed_at(height) -> Polygon | None` is the parcel's legal plan at a
    height, already setback- and sunlight-clipped. Given it, every band is cut
    to the shape of the law rather than the law being used to shrink the
    building until it fits inside a rectangle.
    """

    edges = _band_edges(form, storey_height_m=storey_height_m)
    if len(edges) < 2:
        return None
    ground = edges[0]
    height = form.height_m()
    if height <= 1e-6:
        return None

    volumes: list[SourceVolume] = []
    structural: list[int] = []
    dropped_bands = 0
    for low, high in zip(edges, edges[1:]):
        parts = _band_parts(form, low, high, allowed_at)
        if not parts:
            dropped_bands += 1
            continue
        role = _band_role(form, low, high)
        is_structure = _band_is_structure(form, low, high)
        for part in parts:
            if is_structure:
                structural.append(len(volumes))
            volumes.append(
                SourceVolume(
                    role=role,
                    footprint=part,
                    bottom_fraction=max(0.0, (low - ground) / height),
                    top_fraction=min(1.0, (high - ground) / height),
                    verb=verb,
                )
            )
    if not volumes:
        return None

    grounded = [item for item in volumes if item.bottom_fraction <= 1e-6]
    topmost = [item for item in volumes if item.top_fraction >= 1.0 - 1e-6]
    footprint = unary_union([item.footprint for item in grounded]) if grounded else volumes[0].footprint
    if not isinstance(footprint, Polygon):
        footprint = max(footprint.geoms, key=lambda item: item.area)
    upper = unary_union([item.footprint for item in topmost]) if topmost else None
    if upper is not None and not isinstance(upper, Polygon):
        upper = max(upper.geoms, key=lambda item: item.area)

    notes = list(form.notes)
    if dropped_bands:
        notes.append(f"matrix_form_dropped_empty_bands={dropped_bands}")

    return SourceMass(
        name=form.name,
        footprint=footprint,
        upper_footprint=upper,
        lower_floor_fraction=None,
        volumes=tuple(volumes),
        surfaces=(),
        verb_trace=(),
        notes=tuple(notes),
        status="compiled",
        metadata=_metadata(
            form, height_m=height, band_count=len(volumes),
            structural_bands=tuple(structural),
        ),
    )


def _band_is_structure(form: MatrixForm, low: float, high: float) -> bool:
    """Is everything standing in this band something that holds a room up.

    A band is structure only when nothing occupiable reaches it: four columns
    under a plate make one, the plate above does not, and a band where a column
    passes a floor is a floor. Asked of the volumes rather than of the band's
    outline, because a column and a storey are the same shape in plan and
    differ only in what they are for.
    """

    occupants = [item for item in form.additive() if _spans(item, low, high)]
    return bool(occupants) and not any(item.occupiable for item in occupants)


def _band_role(form: MatrixForm, low: float, high: float) -> str:
    """Name the band after whichever volume actually dominates it.

    Roles carry the hierarchy the selection quotas read, so a band named after
    the wrong volume is a band that votes for the wrong family.
    """

    occupants = [
        (item, _plan(item).area)
        for item in form.additive()
        if _spans(item, low, high)
    ]
    if not occupants:
        return "matrix_band"
    return max(occupants, key=lambda pair: pair[1])[0].role


def _metadata(
    form: MatrixForm,
    *,
    height_m: float,
    band_count: int,
    structural_bands: tuple[int, ...] = (),
) -> dict[str, Any]:
    """The fields `SourceMass.signature()` turns into `source_signature`.

    Leaving these empty is not a cosmetic omission: every diversity quota in
    `design/maas/selection/` reads them, and an unnamed language collapses into
    a single "unknown" family that later balancing culls.
    """

    roles = [item.role for item in form.additive()]
    return {
        "primary_language": form.primary_language,
        "secondary_language": form.secondary_language,
        "formal_principle": form.formal_principle,
        "dominant_gesture": form.dominant_gesture,
        "reference_basis": form.reference_basis,
        "authored_height_m": round(height_m, 3),
        "authored_floor_height_m": form.floor_height_m,
        "matrix_form": form.evidence(),
        "massing_genome": {
            "schema_version": "arr.maas.matrix_form_genome.v1",
            "roles": roles,
            "band_count": band_count,
            "additive_count": len(form.additive()),
            "subtractive_count": len(form.subtractive()),
        },
        "geometry_authority": "matrix_form_analysis",
        # Which bands are what holds the building up rather than part of it.
        # Read by the plausibility gate, which must not ask a column to be as
        # wide as a storey.
        "structural_bands": list(structural_bands),
        **dict(form.extra),
    }
