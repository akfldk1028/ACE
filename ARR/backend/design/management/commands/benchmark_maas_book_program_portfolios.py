"""Run bounded BOOK × program 20-mass boards on a live PNU parcel."""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from shapely.affinity import translate

from design.maas.book_language.portfolio_benchmark import run_book_program_portfolios
from design.services.constraint_bridge import regulations_to_constraints
from design.services.site_geometry import fetch_parcel_boundary, geojson_to_polygon, wgs84_to_utm


class Command(BaseCommand):
    help = "Compile BOOK-operation portfolios for neighborhood, gym and cultural programs"

    def add_arguments(self, parser):
        parser.add_argument("--pnu", default="1168011800104170004")
        parser.add_argument(
            "--output-dir",
            default="../../docs/playwright/design-route-live-verify/book-program-portfolios",
        )

    def handle(self, *args, **options):
        pnu = str(options["pnu"])
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
            for road in road_frontages or []:
                try:
                    width = float(road.get("roadWidthM") or road.get("road_width_m") or 0.0)
                except (TypeError, ValueError):
                    width = 0.0
                if width > 0:
                    widths.append(width)
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
        result = run_book_program_portfolios(
            local_site,
            pnu=pnu,
            output_dir=Path(options["output_dir"]).resolve(),
            site_origin_utm=(float(minx), float(miny)),
            constraints=constraints,
            regulation_evidence=regulation_evidence,
            sunlight_envelope=sunlight_envelope,
            parking_options=parking_options,
        )
        self.stdout.write(self.style.SUCCESS(
            f"BOOK program portfolios: {result['status']} · "
            + ", ".join(
                f"{item['program']} {item['selected_count']}/20 ({item['book_operation_count']} ops)"
                for item in result["programs"]
            )
        ))
