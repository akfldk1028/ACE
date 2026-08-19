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

from dataclasses import replace
from design.maas.geometry_language.affine_matrix import transform_point3

from .form import MatrixForm, Placement
from .profiles import unit_plan


# Bands thinner than this are a seam between two volumes that end near each
# other, not a layer of the building. The number is the package's own floor on
# how thin anything it builds may be - `_Frame.box` holds every volume to at
# least 0.5 m, and a storey to a storey - so a band under it corresponds to no
# building element at all.
#
# It was 0.05, chosen against float noise, and 5 cm is far below the scale of
# the mistake: measured over the sixteen delivered alternatives, seven of the
# seventy-four prisms drawn were under a metre. In an axonometric each of those
# is a line across a facade that no wall makes, which is what "정갈하지 않다"
# turned out to mean in about a tenth of the cases. The rest of the layering is
# not noise - forty-nine of the seventy-four are 3 m or thicker, and those are
# storeys.
_MINIMUM_BAND_M = 0.5
# A band whose remaining plan is slighter than this was cut away, not built.
_MINIMUM_BAND_AREA_M2 = 1.0


def _ring_at(placement: Placement, level: float) -> list[tuple[float, float]]:
    """The volume's plan outline at one normalized height, in order."""

    return [
        (x, y)
        for x, y, _z in (
            transform_point3(placement.matrix, (corner[0], corner[1], level))
            for corner in unit_plan(placement.plan)
        )
    ]


def _stands_upright(placement: Placement) -> bool:
    """Is this volume's plan the same at every height.

    Cheap and non-recursive, so the plan functions can ask it. Compares the
    posed ring at the bottom and the top point for point, which is exactly what
    a lean or a twist changes.
    """

    bottom, top = _ring_at(placement, 0.0), _ring_at(placement, 1.0)
    return all(
        abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9
        for a, b in zip(bottom, top)
    )


def _ordered(points) -> Polygon:
    polygon = Polygon(points)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    return polygon if isinstance(polygon, Polygon) else Polygon()


def _plan(placement: Placement) -> Polygon:
    """Plan outline of a posed volume, over its whole height.

    A volume that stands upright has the same plan at every height, so the
    posed ring in order is exact. A convex hull is not: `concave_l` is one of
    the ten profiles this grammar can name, and its hull is 32% larger than the
    shape - the notch that makes it an L was being filled in, in the measure of
    건축면적, in every downstream metric, and in the drawing. Two sentences in
    the corpus ask for that plan and none of them has ever been drawn with it.

    A leaning or twisting volume is the case the hull was written for: its
    projection over height is the union of every level's ring, and the hull of
    the eight corners is exact for the affine image of a *cube* - which is what
    every leaning volume here is, because the profiles that lean are square.
    """

    if _stands_upright(placement):
        return _ordered(_ring_at(placement, 0.0))
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
    if _stands_upright(placement):
        # Same plan at every height, so the slice is the whole plan and the
        # ring in order is exact - hulling it would fill a concave profile in.
        return _ordered(_ring_at(placement, 0.0))
    lower = max(0.0, min(1.0, (low - low_z) / span))
    upper = max(0.0, min(1.0, (high - low_z) / span))
    points = _ring_at(placement, lower) + _ring_at(placement, upper)
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
    if _stands_upright(placement):
        return False
    bottom = _ordered(_ring_at(placement, 0.0))
    top = _ordered(_ring_at(placement, 1.0))
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

    # A tilted volume never merges. `_band_parts` unions every footprint in a
    # band into one polygon, and a union can carry only one roof plane - a
    # gable's two halves came through as a single band with a single tilt, so
    # half of every pitched roof compiled flat. Tilted placements are set
    # aside here and emitted per placement, clipped by the same envelope,
    # with their own tilt carried directly.
    tilted = [
        item for item in form.additive()
        if float(getattr(item, "top_drop", 0.0) or 0.0) > 0.0
        and (item.drop_toward is not None
             or getattr(item, "ridge_along", None) is not None
             or getattr(item, "top_profile", None) is not None)
    ]
    flat_form = replace(
        form,
        placements=tuple(
            item for item in form.placements if item not in tilted
        ),
    ) if tilted else form

    volumes: list[SourceVolume] = []
    structural: list[int] = []
    dropped_bands = 0
    for low, high in zip(edges, edges[1:]):
        parts = _band_parts(flat_form, low, high, allowed_at)
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
        emitted = bool(parts)

        def _tilted_piece(item, lo: float, hi: float, *, drop: float, toward,
                          ridge=None, profile=None, across=None) -> bool:
            plan = _plan_between(item, lo, hi)
            if allowed_at is not None:
                allowed = allowed_at((lo + hi) / 2.0)
                if allowed is None or allowed.is_empty:
                    return False
                plan = plan.intersection(allowed)
            cutters = [
                _plan_between(cutter, lo, hi)
                for cutter in form.subtractive()
                if _spans(cutter, lo, hi)
            ]
            cutters = [c for c in cutters if not c.is_empty]
            if cutters:
                plan = plan.difference(unary_union(cutters))
            if plan.is_empty:
                return False
            made = False
            pieces = list(plan.geoms) if isinstance(plan, MultiPolygon) else [plan]
            for piece in pieces:
                if not isinstance(piece, Polygon) or piece.area < _MINIMUM_BAND_AREA_M2:
                    continue
                made = True
                volumes.append(SourceVolume(
                    role=item.role,
                    footprint=piece,
                    bottom_fraction=max(0.0, (lo - ground) / height),
                    top_fraction=min(1.0, (hi - ground) / height),
                    verb=verb,
                    top_drop=drop,
                    drop_toward=toward,
                    ridge_along=ridge,
                    top_profile=profile,
                    profile_across=across,
                ))
            return made

        for item in tilted:
            if not _spans(item, low, high):
                continue
            # `top_drop` is declared as a share of the volume's own height
            # (form.py) and the renderer reads a volume's drop as a share of
            # the band it arrived in (`_slope_of`) - so carrying the declared
            # number onto a storey-thick top band drew every roof one storey
            # deep at most: a 0.8 pitch on a nine-metre bar rendered as a
            # 2.4 m bevel, and the fifth frame-of-reference mismatch in this
            # package was a house profile that could not be drawn. The roof
            # zone - the declared drop's own depth - is emitted as a single
            # volume whose drop is its full height, and the storeys under it
            # stay flat bands; the declared metres and the drawn metres are
            # the same number for the first time.
            z0, z1 = item.z_span()
            share = min(max(float(item.top_drop), 0.0), 1.0)
            drop_m = max(share * (z1 - z0), _MINIMUM_BAND_M)
            roof_lo = max(z0, z1 - drop_m)
            body_hi = min(high, roof_lo)
            if body_hi - max(low, z0) > 1e-6:
                emitted |= _tilted_piece(
                    item, max(low, z0), body_hi, drop=0.0, toward=None,
                )
            if low - 1e-6 <= roof_lo < high - 1e-6 or (
                roof_lo <= z0 + 1e-9 and low - 1e-6 <= z0 < high - 1e-6
            ):
                # A profile's heights are shares of the whole volume; the roof
                # band is only its top `share`, so the profile is re-read in
                # the band's own terms - the eaves at 0, the crest at 1.
                profile = getattr(item, "top_profile", None)
                if profile is not None and share > 1e-9:
                    profile = tuple(
                        (u, min(1.0, max(0.0, (h - (1.0 - share)) / share)))
                        for u, h in profile
                    )
                emitted |= _tilted_piece(
                    item, roof_lo, z1, drop=1.0, toward=item.drop_toward,
                    ridge=getattr(item, "ridge_along", None),
                    profile=profile,
                    across=getattr(item, "profile_across", None),
                )
        if not emitted:
            dropped_bands += 1
    if not volumes:
        return None
    grounded = [item for item in volumes if item.bottom_fraction <= 1e-6]
    topmost = [item for item in volumes if item.top_fraction >= 1.0 - 1e-6]
    footprint = unary_union([item.footprint for item in grounded]) if grounded else volumes[0].footprint
    if not isinstance(footprint, Polygon):
        # ⚠️ `SourceMass.footprint` is typed as one Polygon, so a mass standing
        # on several bodies loses all but its largest here. This is ground
        # contact and not 건축면적 either - a lifted wing touches nothing - so
        # nothing that has to agree with the law may read it. 건폐율 comes from
        # `legal_fit.ground_area_m2`, which is what the gate checks.
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
