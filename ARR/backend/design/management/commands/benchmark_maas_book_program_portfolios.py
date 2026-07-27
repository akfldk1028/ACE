"""Run bounded BOOK × program 20-mass boards on a live PNU parcel."""

import os
from copy import deepcopy
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from shapely.affinity import translate
from shapely.geometry import LineString, mapping

from design.maas.book_language.portfolio_benchmark import run_book_program_portfolios
from design.maas.geometry_language.run_state import tracked_mass_command
from design.services.constraint_bridge import regulations_to_constraints
from design.services.site_geometry import fetch_parcel_boundary, geojson_to_polygon, wgs84_to_utm


def _with_site_local_parking_frontage(
    parking_options: dict,
    site_access_geometry: dict | None,
) -> dict:
    """Put the road edge in the same local UTM frame as MASS/parking geometry."""

    result = deepcopy(parking_options or {})
    if not isinstance(site_access_geometry, dict):
        return result
    road_context = dict(result.get("road_context") or {})
    road_context["frontage_geometry"] = deepcopy(site_access_geometry)
    road_context["coordinate_frame"] = "site_local_utm"
    result["road_context"] = road_context
    return result


class Command(BaseCommand):
    help = "Compile BOOK-operation portfolios for neighborhood, gym and cultural programs"

    def add_arguments(self, parser):
        parser.add_argument("--pnu", default="1168011800104170004")
        parser.add_argument(
            "--output-dir",
            default="../../docs/playwright/design-route-live-verify/book-program-portfolios",
        )
        parser.add_argument("--program", action="append", choices=("neighborhood", "gymnasium", "cultural"))
        parser.add_argument("--recursive-only", action="store_true")
        parser.add_argument(
            "--smoke",
            action="store_true",
            help=(
                "Stop after one shared-floor/program candidate, select one MASS, "
                "and skip 20-member replenishment/diversity requirements."
            ),
        )
        parser.add_argument(
            "--live-vlm",
            action="store_true",
            help=(
                "Run the image-grounded critic and typed repair after the shared "
                "universal form bank, BOOK projection and program projection; "
                "requires MAAS_LIVE_GEOMETRY_VLM=1, "
                "MAAS_LIVE_VLM_CREDENTIAL_ROTATED=1 and OPENAI_API_KEY"
            ),
        )
        parser.add_argument("--visual-directive", default=None)
        parser.add_argument(
            "--outcome-graph",
            default=None,
            help=(
                "Explicitly opt into a controlled cross-run typed outcome graph. "
                "By default every output directory owns one isolated causal graph."
            ),
        )

    @tracked_mass_command
    def handle(self, *args, **options):
        pnu = str(options["pnu"])
        if options.get("live_vlm"):
            missing = [
                name for name in (
                    "MAAS_LIVE_GEOMETRY_VLM",
                    "MAAS_LIVE_VLM_CREDENTIAL_ROTATED",
                    "OPENAI_API_KEY",
                )
                if not os.getenv(name)
            ]
            if missing:
                raise CommandError(
                    "--live-vlm requires explicit runtime credentials/opt-in: "
                    + ", ".join(missing)
                )
        boundary = fetch_parcel_boundary(pnu)
        if boundary is None:
            raise CommandError("VWorld parcel boundary is required; no synthetic fallback is allowed")
        try:
            from land.services import land_api, regulation_calculator, road_frontage, zoning_mapper
            from land.services.setback_geometry import compute_setback_lines

            land_info = land_api.get_land_use_info(pnu)
            zones = land_info.get("zones", []) or []
            limits = zoning_mapper.resolve_limits(zones) if zones else {}
            zone_names = [
                item["zone_name"] if isinstance(item, dict) else str(item)
                for item in ((limits or {}).get("zones") or zones)
            ]
            if not zone_names:
                raise ValueError("PNU zoning lookup returned no executable zone")
            regulation = regulation_calculator.calculate_all(
                zone_names,
                land_info=land_info,
                sigungu_code=pnu[:5],
                use_llm_extraction=False,
            )
            constraints = regulations_to_constraints(regulation)
            if not constraints:
                raise ValueError("PNU regulation lookup returned no constraints")
            roads_result = road_frontage.fetch_neighbor_roads(boundary)
            road_frontages = roads_result.get("roads") if isinstance(roads_result, dict) and roads_result.get("success") else []
            neighbors_result = road_frontage.fetch_neighbor_parcels(boundary)
            neighbor_parcels = neighbors_result.get("neighbors") if isinstance(neighbors_result, dict) and neighbors_result.get("success") else []
            setback_lines = compute_setback_lines(
                boundary,
                regulation,
                compute_datum=False,
                road_frontages=road_frontages or [],
                neighbor_parcels=neighbor_parcels or [],
            )
            sunlight_envelope = setback_lines.get("sunlight_envelope")
            widths = []
            frontage_records = []
            metric_site = wgs84_to_utm(geojson_to_polygon(boundary))
            site_center = metric_site.centroid
            for road in road_frontages or []:
                try:
                    width = float(road.get("roadWidthM") or road.get("road_width_m") or 0.0)
                except (TypeError, ValueError):
                    width = 0.0
                if width > 0:
                    widths.append(width)
                shared_edge = road.get("sharedEdge") if isinstance(road, dict) else None
                if not isinstance(shared_edge, list) or len(shared_edge) < 2:
                    continue
                try:
                    metric_edge = wgs84_to_utm(LineString(shared_edge))
                except Exception:
                    continue
                midpoint = metric_edge.centroid
                dx = float(midpoint.x - site_center.x)
                dy = float(midpoint.y - site_center.y)
                frontage_records.append({
                    "side": (
                        ("east" if dx >= 0 else "west")
                        if abs(dx) >= abs(dy)
                        else ("north" if dy >= 0 else "south")
                    ),
                    "shared_length_m": round(float(metric_edge.length), 3),
                    "road_width_m": round(width, 3),
                    "metric_edge": metric_edge,
                })
            primary_frontage = (
                max(frontage_records, key=lambda item: item["shared_length_m"])
                if frontage_records
                else None
            )
            site_access_context = {
                "status": "vworld_neighbor_road" if primary_frontage else "road_frontage_unresolved",
                "primary_access_edge": str((primary_frontage or {}).get("side") or ""),
                "road_width_m": max(widths) if widths else None,
                "frontages": [
                    {key: value for key, value in item.items() if key != "metric_edge"}
                    for item in frontage_records
                ],
            }
            parking_options = {
                "road_context": {
                    "road_width_m": max(widths) if widths else None,
                    "road_frontages": road_frontages or [],
                },
            }
            regulation_evidence = {
                "zones": zone_names,
                "bcr_pct": regulation.get("bcr_pct"),
                "far_pct": regulation.get("far_pct"),
                "height_limit_m": regulation.get("height_limit_m"),
                "adjacent_setback_m": regulation.get("adjacent_setback_m"),
                "building_line_setback_m": regulation.get("building_line_setback_m"),
                "landscaping_min_pct": regulation.get("landscaping_min_pct"),
                "sunlight_applies": regulation.get("sunlight_applies"),
                "road_frontage_count": len(road_frontages or []),
                "neighbor_parcel_count": len(neighbor_parcels or []),
            }
        except Exception as exc:
            raise CommandError(f"live PNU regulation/parking context is required; no synthetic fallback: {exc}") from exc
        site = wgs84_to_utm(geojson_to_polygon(boundary))
        minx, miny, _maxx, _maxy = site.bounds
        local_site = translate(site, xoff=-minx, yoff=-miny)
        site_access_geometry = (
            mapping(translate(primary_frontage["metric_edge"], xoff=-minx, yoff=-miny))
            if primary_frontage is not None
            else None
        )
        parking_options = _with_site_local_parking_frontage(
            parking_options,
            site_access_geometry,
        )
        result = run_book_program_portfolios(
            local_site,
            pnu=pnu,
            output_dir=Path(options["output_dir"]).resolve(),
            site_origin_utm=(float(minx), float(miny)),
            constraints=constraints,
            regulation_evidence=regulation_evidence,
            sunlight_envelope=sunlight_envelope,
            parking_options=parking_options,
            site_boundary_source="vworld_live_pnu",
            site_access_context=site_access_context,
            site_access_geometry=site_access_geometry,
            program_slugs=tuple(options.get("program") or ()),
            recursive_only=bool(options.get("recursive_only")),
            live_geometry_vlm_revision=bool(options.get("live_vlm")),
            smoke_mode=bool(options.get("smoke")),
            visual_directive_path=(
                Path(str(options["visual_directive"])).resolve()
                if options.get("visual_directive")
                else None
            ),
            outcome_graph_path=(
                Path(str(options["outcome_graph"])).resolve()
                if options.get("outcome_graph")
                else None
            ),
        )
        self.stdout.write(self.style.SUCCESS(
            f"BOOK program portfolios: {result['status']} · "
            + ", ".join(
                (
                    f"{item['program']} {item['selected_count']}/"
                    f"{1 if options.get('smoke') else 20} "
                    f"({item['book_operation_count']} ops)"
                )
                for item in result["programs"]
            )
        ))
        # Django writes a non-None ``handle`` return value as command output,
        # so returning the structured result here makes ``BaseCommand`` call
        # ``dict.endswith`` after every otherwise-complete benchmark run.
        # The canonical structured result is already persisted in the output
        # directory; the management command must return text or ``None``.
        return None
