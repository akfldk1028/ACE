"""The parcel's own limits, fetched once and handed to the form language.

This is a thin adapter, deliberately. Every number here is produced by the
existing legal stack - Vworld boundary, zoning limits, setback lines, the north
sunlight envelope, and the per-floor legal field. Nothing is recomputed and
nothing is approximated, because the legal engine is the part of this project
that is already ahead of the published work and must not be forked.

There is no synthetic fallback. A parcel that cannot be resolved raises, rather
than quietly handing back a rectangle that would make every downstream number
meaningless.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from shapely.affinity import translate
from shapely.geometry import LineString, Polygon

from design.maas.book_language.downstream_hard_gate import (
    LegalGenerationContext,
    build_legal_generation_context,
    generation_site_at_height,
)
from design.maas.book_language.legal_floor_field import materialize_legal_floor_field
from design.services.constraint_bridge import regulations_to_constraints
from design.services.site_geometry import (
    fetch_parcel_boundary,
    geojson_to_polygon,
    wgs84_to_utm,
)


logger = logging.getLogger(__name__)


class LegalSiteUnavailable(RuntimeError):
    """The parcel could not be resolved from live data."""


@dataclass(frozen=True)
class LegalSite:
    """Everything the form language needs to know about one parcel."""

    pnu: str
    site_local_utm: Polygon
    site_origin_utm: tuple[float, float]
    context: LegalGenerationContext
    floor_field: dict[str, Any]
    # Boundary segments a neighbouring parcel is built against, in the same
    # site-local frame as everything else. What is left of the boundary is the
    # side the parcel is open on - see `siting.open_side_direction`.
    shared_edges: tuple[tuple[tuple[float, float], ...], ...] = ()

    @property
    def parcel_area_m2(self) -> float:
        return float(self.site_local_utm.area)

    @property
    def ground_capacity_m2(self) -> float:
        """건축면적 ceiling - 건축법 시행령 제119조 제1항 제2호."""

        return float(self.floor_field.get("bcr_footprint_capacity_m2") or 0.0)

    @property
    def far_capacity_m2(self) -> float:
        return float(self.floor_field.get("statutory_far_capacity_m2") or 0.0)

    @property
    def floor_height_m(self) -> float:
        return float(getattr(self.context.envelope, "floor_height", 0.0) or 0.0)

    def plan_at(self, height_m: float) -> Polygon | None:
        """The legal footprint at a height, already sunlight-clipped."""

        return generation_site_at_height(self.context, float(height_m))

    def evidence(self) -> dict[str, Any]:
        return {
            "schema_version": "arr.maas.massv2_legal_site.v1",
            "pnu": self.pnu,
            "parcel_area_m2": round(self.parcel_area_m2, 2),
            "ground_capacity_m2": round(self.ground_capacity_m2, 3),
            "far_capacity_m2": round(self.far_capacity_m2, 3),
            "floor_height_m": self.floor_height_m,
            "legal_floor_section_count": len(
                self.floor_field.get("legal_floor_section_areas_m2") or ()
            ),
        }


def load_legal_site(pnu: str, *, building_type: str = "제1종근린생활시설") -> LegalSite:
    """Resolve one parcel into the limits the form language generates against."""

    boundary = fetch_parcel_boundary(pnu)
    if boundary is None:
        raise LegalSiteUnavailable(
            f"Vworld parcel boundary is required for {pnu}; synthetic fallback is not allowed"
        )

    from land.services import land_api, regulation_calculator, road_frontage, zoning_mapper
    from land.services.setback_geometry import compute_setback_lines

    land_info = land_api.get_land_use_info(pnu)
    zones = land_info.get("zones") or []
    # 국토계획법 제84조: a parcel across two 용도지역 is governed by how much of it
    # is in each, so the split is measured before the limits are asked for. It is
    # only fetched when there is more than one zone to split between, and a
    # failure to measure is not fatal here - `resolve_limits` answers with
    # `needs_zone_areas` and the site refuses itself below, rather than this
    # quietly substituting a guess.
    areas: dict[str, float] = {}
    if len(zones) > 1:
        from land.services import zone_geometry

        try:
            areas = zone_geometry.parcel_zone_split(
                geojson_to_polygon(boundary), to_utm=wgs84_to_utm
            )
        except zone_geometry.ZoneGeometryUnavailable as error:
            logger.warning("zone split unavailable for %s: %s", pnu, error)
    limits = zoning_mapper.resolve_limits(zones, areas) if zones else {}
    zone_names = [
        item["zone_name"] if isinstance(item, dict) else str(item)
        for item in ((limits or {}).get("zones") or zones)
    ]
    if not zone_names:
        raise LegalSiteUnavailable(f"{pnu} zoning lookup returned no executable zone")

    regulation = regulation_calculator.calculate_all(
        zone_names,
        land_info=land_info,
        sigungu_code=pnu[:5],
        zone_areas=areas,
        use_llm_extraction=False,
    )
    constraints = regulations_to_constraints(regulation)
    if not constraints:
        raise LegalSiteUnavailable(f"{pnu} regulation lookup returned no constraints")

    roads = road_frontage.fetch_neighbor_roads(boundary)
    neighbors = road_frontage.fetch_neighbor_parcels(boundary)
    setback_lines = compute_setback_lines(
        boundary,
        regulation,
        compute_datum=False,
        road_frontages=(roads.get("roads") or []) if isinstance(roads, dict) else [],
        neighbor_parcels=(neighbors.get("neighbors") or []) if isinstance(neighbors, dict) else [],
    )

    site_utm = wgs84_to_utm(geojson_to_polygon(boundary))
    min_x, min_y = site_utm.bounds[0], site_utm.bounds[1]
    # Generation happens in a site-local frame. UTM northings are seven digits,
    # and doing form arithmetic against those spends float precision on an
    # offset that means nothing to the design.
    local_site = translate(site_utm, xoff=-min_x, yoff=-min_y)

    context = build_legal_generation_context(
        site_local_utm=local_site,
        site_origin_utm=(min_x, min_y),
        building_type=building_type,
        constraints=constraints,
        sunlight_envelope=setback_lines.get("sunlight_envelope"),
    )
    floor_field = materialize_legal_floor_field(
        context, site_local_utm=local_site, pnu=pnu
    )
    shared = tuple(
        tuple(
            (point[0] - min_x, point[1] - min_y)
            for point in wgs84_to_utm(LineString(edge)).coords
        )
        for edge in (
            item.get("sharedEdge")
            for item in ((neighbors.get("neighbors") or []) if isinstance(neighbors, dict) else [])
        )
        if edge and len(edge) >= 2
    )
    return LegalSite(
        pnu=pnu,
        site_local_utm=local_site,
        site_origin_utm=(min_x, min_y),
        context=context,
        floor_field=floor_field,
        shared_edges=shared,
    )
