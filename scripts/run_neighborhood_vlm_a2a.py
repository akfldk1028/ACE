"""Reproducible CLI for the graph-native neighborhood VLM/A2A benchmark."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "ARR" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

from design.maas.program_massing.vlm_a2a import (  # noqa: E402
    generation_feedback_from_result,
    run_neighborhood_vlm_a2a_loop,
)
from design.services.site_geometry import (  # noqa: E402
    fetch_parcel_boundary,
    geojson_to_polygon,
    wgs84_to_utm,
)
from land.services import road_frontage  # noqa: E402
from shapely.affinity import translate  # noqa: E402
from shapely.geometry import LineString, mapping  # noqa: E402


def _site_access_context(parcel_geometry: dict, metric_site) -> tuple[dict, object | None]:
    """Derive coarse author-facing access facts from actual VWorld roads."""

    try:
        result = road_frontage.fetch_neighbor_roads(parcel_geometry)
        roads = result.get("roads") if isinstance(result, dict) else None
    except Exception:
        roads = None
    if not isinstance(roads, list) or not roads:
        return {"status": "road_frontage_unresolved", "road_edges": []}, None
    frontages = []
    site_center = metric_site.centroid
    for road in roads:
        shared_edge = road.get("sharedEdge") if isinstance(road, dict) else None
        if not isinstance(shared_edge, list) or len(shared_edge) < 2:
            continue
        try:
            edge = wgs84_to_utm(LineString(shared_edge))
            midpoint = edge.centroid
            dx = float(midpoint.x - site_center.x)
            dy = float(midpoint.y - site_center.y)
            side = ("east" if dx >= 0 else "west") if abs(dx) >= abs(dy) else ("north" if dy >= 0 else "south")
            frontages.append({
                "side": side,
                "shared_length_m": round(float(edge.length), 2),
                "road_width_m": round(float(road.get("roadWidthM") or 0.0), 2),
                "_metric_edge": edge,
            })
        except Exception:
            continue
    if not frontages:
        return {"status": "road_frontage_unresolved", "road_edges": []}, None
    primary = max(frontages, key=lambda item: item["shared_length_m"])
    context = {
        "status": "vworld_neighbor_road",
        "road_edges": list(dict.fromkeys(item["side"] for item in frontages)),
        "primary_access_edge": primary["side"],
        "road_width_m": max(item["road_width_m"] for item in frontages),
        "frontages": [
            {key: value for key, value in item.items() if not key.startswith("_")}
            for item in frontages
        ],
    }
    return context, primary["_metric_edge"]


def _resolve_metric_site(pnu: str, cached_boundary_path: Path | None):
    geometry = fetch_parcel_boundary(pnu)
    source = "vworld_live_pnu"
    if geometry is None:
        fallback = cached_boundary_path or (
            REPO_ROOT / "docs" / "playwright" / "design-route-live-verify" / "maas-20-alt-latest.json"
        )
        payload = json.loads(fallback.read_text(encoding="utf-8"))
        boundary = payload.get("boundary") if isinstance(payload, dict) else None
        if str(payload.get("pnu") or "") != pnu or not isinstance(boundary, dict):
            raise RuntimeError(f"no live or matching cached VWorld boundary for PNU {pnu}")
        geometry = boundary.get("geometry")
        source = f"cached_vworld_pnu:{fallback.as_posix()}"
    polygon = wgs84_to_utm(geojson_to_polygon(geometry))
    access_context, access_edge = _site_access_context(geometry, polygon)
    minx, miny, _, _ = polygon.bounds
    local_access_edge = (
        mapping(translate(access_edge, xoff=-minx, yoff=-miny))
        if access_edge is not None
        else None
    )
    return (
        translate(polygon, xoff=-minx, yoff=-miny),
        source,
        access_context,
        local_access_edge,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v10")
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--target-count", type=int, default=20)
    parser.add_argument("--review-pool-count", type=int, default=30)
    parser.add_argument("--critic-generations", type=int, default=3)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--pnu", help="Load the real parcel boundary from VWorld before generation.")
    parser.add_argument(
        "--site-boundary-from",
        type=Path,
        help="Matching cached VWorld response used only when live PNU lookup is unavailable.",
    )
    parser.add_argument("--far-limit-ratio", type=float, default=3.0)
    parser.add_argument("--feedback-from", type=Path)
    parser.add_argument(
        "--author-cache-from",
        type=Path,
        help="Reuse a previously verified live-author batch while re-evaluating changed geometry/VLM logic.",
    )
    parser.add_argument(
        "--supplemental-author-cache-from",
        type=Path,
        action="append",
        default=[],
        help="Add another verified author population to the cumulative replenishment search pool.",
    )
    parser.add_argument(
        "--accepted-seed-from",
        type=Path,
        action="append",
        default=[],
        help="Persist accepted executable graphs from a previous result while replenishing missing languages.",
    )
    parser.add_argument(
        "--supplemental-vlm-cache-from",
        type=Path,
        action="append",
        default=[],
        help="Merge surface-aware score caches from prior replenishment rounds.",
    )
    args = parser.parse_args()

    output = REPO_ROOT / "docs" / "playwright" / "design-route-live-verify"
    version = str(args.version).strip().replace("/", "_").replace("\\", "_")
    feedback = None
    if args.feedback_from:
        feedback = generation_feedback_from_result(
            __import__("json").loads(args.feedback_from.read_text(encoding="utf-8"))
        )
    site_polygon = None
    site_boundary_source = "synthetic_benchmark"
    site_access_context = None
    site_access_geometry = None
    if args.pnu:
        site_polygon, site_boundary_source, site_access_context, site_access_geometry = _resolve_metric_site(
            args.pnu,
            args.site_boundary_from,
        )
    result = run_neighborhood_vlm_a2a_loop(
        output_json=output / f"maas-neighborhood-vlm-a2a-{version}.json",
        output_png=output / f"maas-neighborhood-vlm-a2a-{version}.png",
        model=args.model,
        author_model=args.model,
        author_target_count=24,
        author_cache_path=(
            args.author_cache_from
            if args.author_cache_from is not None
            else output / f"maas-neighborhood-author-{version}-graph-cache.json"
        ),
        supplemental_author_cache_paths=tuple(args.supplemental_author_cache_from),
        accepted_seed_result_paths=tuple(args.accepted_seed_from),
        supplemental_vlm_cache_paths=tuple(args.supplemental_vlm_cache_from),
        reference_language_cache_path=output / "maas-reference-language-neighborhood-v4.json",
        target_count=max(1, args.target_count),
        review_pool_count=max(1, args.review_pool_count),
        critic_generations=max(1, args.critic_generations),
        workers=max(1, args.workers),
        generation_feedback=feedback,
        site_polygon=site_polygon,
        site_pnu=args.pnu,
        site_boundary_source=site_boundary_source,
        site_access_context=site_access_context,
        site_access_geometry=site_access_geometry,
        far_limit_ratio=args.far_limit_ratio,
    )
    keys = (
        "status", "visual_status", "raw_evaluated_count", "clean_pool_count",
        "capacity_pool_count", "vlm_parent_count", "vlm_child_count",
        "selected_count", "capacity_target_met_count", "final_language_group_counts",
        "near_duplicate_pairs",
    )
    print({key: result.get(key) for key in keys})
    author = result.get("author_artifact") or {}
    print({
        "author_cache": author.get("cache"),
        "author_elapsed_ms": author.get("elapsed_ms"),
        "author_openai_batch_errors": author.get("openai_batch_errors"),
        "author_timeout_coverage_repair_count": author.get("timeout_coverage_repair_count"),
        "author_deterministic_coverage_repair_count": author.get("deterministic_coverage_repair_count"),
        "author_rejected_sequence_samples": author.get("rejected_sequence_samples"),
    })
    return 0 if result.get("status") == "technical_pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
