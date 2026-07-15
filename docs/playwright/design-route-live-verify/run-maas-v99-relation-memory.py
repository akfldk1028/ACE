"""Real-PNU mixed-language regression with GRL/Mass-Brain shadow scoring."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import django
from shapely.affinity import translate


ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
sys.path.insert(0, str(ROOT / "ARR" / "backend"))
django.setup()
logging.getLogger("httpx").setLevel(logging.WARNING)

from design.maas.program_massing.adaptive_loop import run_adaptive_neighborhood_vlm_a2a_loop
from design.maas.program_massing.vlm_a2a import generation_feedback_from_result
from design.services.site_geometry import fetch_parcel_boundary, geojson_to_polygon, wgs84_to_utm


def main() -> None:
    output_root = ROOT / "docs" / "playwright" / "design-route-live-verify"
    pnu = "1168011800104170004"
    previous_stem = "maas-neighborhood-vlm-a2a-v98-stepped-replenish"
    stem = os.getenv("MAAS_RUN_STEM", "maas-neighborhood-vlm-a2a-v99-relation-memory")
    previous_json = output_root / f"{previous_stem}.json"
    previous = __import__("json").loads(previous_json.read_text(encoding="utf-8"))
    boundary = fetch_parcel_boundary(pnu)
    if not boundary:
        raise RuntimeError(f"No live VWorld parcel boundary for {pnu}")
    utm = wgs84_to_utm(geojson_to_polygon(boundary))
    minx, miny, _, _ = utm.bounds
    site = translate(utm, xoff=-minx, yoff=-miny)
    result = run_adaptive_neighborhood_vlm_a2a_loop(
        output_json=output_root / f"{stem}.json",
        output_png=output_root / f"{stem}.png",
        max_rounds=1,
        model="gpt-5.4-mini",
        author_model="gpt-5.4-mini",
        author_target_count=20,
        author_cache_path=output_root / f"{previous_stem}-author-graph-cache.json",
        accepted_seed_result_paths=(previous_json,),
        vlm_cache_path=output_root / f"{stem}-vlm-score-cache.json",
        supplemental_vlm_cache_paths=tuple(
            path
            for path in (
                output_root / "maas-neighborhood-vlm-a2a-v99-relation-memory-vlm-score-cache.json",
                output_root / f"{previous_stem}-vlm-score-cache.json",
            )
            if path != output_root / f"{stem}-vlm-score-cache.json" and path.exists()
        ),
        generation_feedback=generation_feedback_from_result(previous),
        target_count=20,
        review_pool_count=40,
        minimum_vlm_score=0.55,
        workers=4,
        critic_generations=1,
        search_generations=1,
        offspring_per_seed=2,
        author_timeout=180.0,
        require_live_graph_author=True,
        site_polygon=site,
        site_pnu=pnu,
        site_boundary_source="vworld_live_pnu",
        site_access_context={
            "status": "vworld_neighbor_road",
            "road_edges": ["east"],
            "primary_access_edge": "east",
            "road_width_m": 37.48,
        },
        far_limit_ratio=3.0,
        mass_brain_enabled=True,
    )
    brain = result.get("mass_brain_shadow") or {}
    print({
        "status": result.get("status"),
        "visual_status": result.get("visual_status"),
        "selected_count": result.get("selected_count"),
        "language_groups": result.get("final_language_group_counts"),
        "mass_brain_status": brain.get("status"),
        "mass_brain_compiled": brain.get("compiled_count"),
        "mass_brain_vlm_evaluated": brain.get("vlm_evaluated_count"),
        "mass_brain_rollout": brain.get("rollout"),
        "png": result.get("png"),
    })


if __name__ == "__main__":
    main()
