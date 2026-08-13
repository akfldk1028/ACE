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
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from design.maas.source_geometry.ir import SourceMass, SourceVolume

from .form import MatrixForm, Placement


# Bands thinner than this are float noise from two volumes meeting at a shared
# level, not a storey; merging them keeps the band list readable.
_MINIMUM_BAND_M = 0.05
# A band whose remaining plan is slighter than this was cut away, not built.
_MINIMUM_BAND_AREA_M2 = 1.0


def _plan(placement: Placement) -> Polygon:
    """Plan outline of a posed box.

    The convex hull of the eight projected corners is exact for any affine image
    of a cube - the projection of a convex solid is convex - so this stays right
    under rotation and shear without needing a mesh.
    """

    hull = Polygon([(x, y) for x, y, _z in placement.corners()]).convex_hull
    return hull if isinstance(hull, Polygon) else Polygon()


def _band_edges(form: MatrixForm) -> list[float]:
    """Cut heights, taken from the volumes' own tops and bottoms.

    Sampling at a fixed count would put band edges where no volume changes, and
    would miss a setback that happens between two samples.
    """

    additive = form.additive()
    if not additive:
        return []
    edges: set[float] = set()
    for placement in form.placements:
        low, high = placement.z_span()
        edges.add(round(low, 4))
        edges.add(round(high, 4))
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


def _band_parts(form: MatrixForm, low: float, high: float) -> list[Polygon]:
    """Every plan piece this band occupies, not just the biggest one.

    Two bars with a gap are two pieces at their own storeys, and keeping only
    the larger one would delete half the building - which is exactly what made
    a paired-bar scheme read as 0.05 open instead of a quarter open. The
    existing bridge does the same thing (`source_bridge._polygon_parts`): each
    piece becomes its own volume record and they share the band's fractions,
    because height bands are legal proxies of one component, not separate
    buildings.
    """

    built = [_plan(item) for item in form.additive() if _spans(item, low, high)]
    built = [item for item in built if not item.is_empty and item.area > 0.0]
    if not built:
        return []
    shape = unary_union(built)
    cutters = [_plan(item) for item in form.subtractive() if _spans(item, low, high)]
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


def compile_matrix_form(form: MatrixForm, *, verb: str = "matrix_place") -> SourceMass | None:
    """Compile placements into a `SourceMass`, or `None` if nothing survives."""

    edges = _band_edges(form)
    if len(edges) < 2:
        return None
    ground = edges[0]
    height = form.height_m()
    if height <= 1e-6:
        return None

    volumes: list[SourceVolume] = []
    dropped_bands = 0
    for low, high in zip(edges, edges[1:]):
        parts = _band_parts(form, low, high)
        if not parts:
            dropped_bands += 1
            continue
        role = _band_role(form, low, high)
        for part in parts:
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
        metadata=_metadata(form, height_m=height, band_count=len(volumes)),
    )


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


def _metadata(form: MatrixForm, *, height_m: float, band_count: int) -> dict[str, Any]:
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
        **dict(form.extra),
    }
