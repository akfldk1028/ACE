"""Is this a building, or is it lawful geometry that nobody could occupy.

Both ceilings can be satisfied by a chimney. Measured on the live Uijeongbu
parcel, carrying a four-block composition down to a 45% ground take produced a
21 m2 footprint under 48 m of height - a slenderness of 10.4, entirely lawful
and not a 근린생활시설 anyone would propose. Eleven of eighty-eight schemes came
out past a slenderness of 4.

Nothing here invents a threshold. Floor viability comes from the project's own
shared rule in `design/maas/floor_viability.py`, which derives a minimum
occupied area from the parcel and holds a room to a 2.4 m clear depth, and the
slenderness bound is the one the existing review gate already applies to
authored candidates in `legal_mesh_optimizer._is_reviewable_architectural_mass`.
Using the rules the project already lives by is the point: a second set of
numbers would be a second opinion about the same question.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from design.maas.floor_viability import (
    evaluate_floor_section_viability,
    minimum_usable_floor_area_m2,
)
from design.maas.source_geometry.ir import SourceMass


# `_is_reviewable_architectural_mass` allows height/min-plan-dimension up to 12
# for an authored candidate carrying real source geometry, which every mass here
# does. Quoted rather than re-decided.
AUTHORED_SLENDERNESS_LIMIT = 12.0
AUTHORED_MINIMUM_PLAN_DIMENSION_M = 1.5


@dataclass(frozen=True)
class Plausibility:
    slenderness: float
    minimum_plan_dimension_m: float
    viable_band_share: float
    occupiable: bool
    reasons: tuple[str, ...]

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_plausibility.v1",
            "slenderness": round(self.slenderness, 3),
            "minimum_plan_dimension_m": round(self.minimum_plan_dimension_m, 3),
            "viable_band_share": round(self.viable_band_share, 3),
            "occupiable": self.occupiable,
            "reasons": list(self.reasons),
            "basis": "design.maas.floor_viability + authored review gate limits",
        }


def _min_dimension(polygon) -> float:
    min_x, min_y, max_x, max_y = polygon.bounds
    return float(min(max_x - min_x, max_y - min_y))


def assess(source: SourceMass, *, parcel_area_m2: float) -> Plausibility:
    """Judge a compiled mass as a building rather than as a solid."""

    bands = tuple(source.volumes)
    if not bands:
        return Plausibility(0.0, 0.0, 0.0, False, ("no_bands",))

    height = float(source.metadata.get("authored_height_m") or 0.0)
    ground = source.footprint
    min_dimension = _min_dimension(ground)
    slenderness = height / min_dimension if min_dimension > 1e-6 else float("inf")

    viable = 0
    for volume in bands:
        verdict = evaluate_floor_section_viability(
            volume.footprint, parcel_area_m2=parcel_area_m2
        )
        if verdict.get("hard_pass"):
            viable += 1
    share = viable / len(bands)

    reasons: list[str] = []
    if slenderness > AUTHORED_SLENDERNESS_LIMIT:
        reasons.append(f"slenderness_{slenderness:.1f}_over_{AUTHORED_SLENDERNESS_LIMIT}")
    if min_dimension < AUTHORED_MINIMUM_PLAN_DIMENSION_M:
        reasons.append(f"plan_dimension_{min_dimension:.1f}m_under_minimum")
    if float(ground.area) < minimum_usable_floor_area_m2(parcel_area_m2):
        reasons.append("ground_floor_below_minimum_usable_area")
    if share <= 0.5:
        reasons.append(f"only_{share:.0%}_of_bands_occupiable")

    return Plausibility(
        slenderness=slenderness,
        minimum_plan_dimension_m=min_dimension,
        viable_band_share=share,
        occupiable=not reasons,
        reasons=tuple(reasons),
    )
