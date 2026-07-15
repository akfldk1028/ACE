"""Reproducible real-PNU MAAS section-loft/VLM board run."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import django
from shapely.affinity import translate


ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
os.environ.setdefault("PYTHONPATH", str(ROOT / "ARR" / "backend"))
sys.path.insert(0, str(ROOT / "ARR" / "backend"))
django.setup()
logging.getLogger("httpx").setLevel(logging.WARNING)

from design.maas.program_massing.adaptive_loop import run_adaptive_neighborhood_vlm_a2a_loop
from design.services.site_geometry import fetch_parcel_boundary, geojson_to_polygon, wgs84_to_utm


def main() -> None:
    output_root = ROOT / "docs" / "playwright" / "design-route-live-verify"
    pnu = "1168011800104170004"
    boundary = fetch_parcel_boundary(pnu)
    if not boundary:
        raise RuntimeError(f"No live VWorld parcel boundary for {pnu}")
    utm = wgs84_to_utm(geojson_to_polygon(boundary))
    minx, miny, _, _ = utm.bounds
    local_site = translate(utm, xoff=-minx, yoff=-miny)
    stem = "maas-neighborhood-vlm-a2a-v94-visible-section-mutation"
    result = run_adaptive_neighborhood_vlm_a2a_loop(
        output_json=output_root / f"{stem}.json",
        output_png=output_root / f"{stem}.png",
        max_rounds=1,
        model="gpt-5.4-mini",
        author_model="gpt-5.4-mini",
        author_target_count=32,
        author_cache_path=output_root / "maas-neighborhood-vlm-a2a-v91-agent-section-loft-author-graph-cache.json",
        # The fresh cache plus exact accepted seeds are the replenishment
        # frontier. Historical author populations are audit evidence, not
        # candidates to re-search on every service request.
        supplemental_author_cache_paths=(),
        accepted_seed_result_paths=(
            output_root / "maas-neighborhood-vlm-a2a-v93-section-genotype-search.json",
        ),
        vlm_cache_path=output_root / f"{stem}-vlm-score-cache.json",
        supplemental_vlm_cache_paths=(
            output_root / "maas-neighborhood-vlm-a2a-v93-section-genotype-search-vlm-score-cache.json",
        ),
        target_count=20,
        review_pool_count=40,
        minimum_vlm_score=0.55,
        workers=4,
        critic_generations=2,
        search_generations=1,
        offspring_per_seed=2,
        author_timeout=240.0,
        require_live_graph_author=True,
        site_polygon=local_site,
        site_pnu=pnu,
        site_boundary_source="vworld_live_pnu",
        site_access_context={
            "status": "vworld_neighbor_road",
            "road_edges": ["east"],
            "primary_access_edge": "east",
            "road_width_m": 37.48,
        },
        far_limit_ratio=3.0,
    )
    scores = [float(row.get("vlm_design_score") or 0.0) for row in result.get("rows") or []]
    print({
        "status": result.get("status"),
        "visual_status": result.get("visual_status"),
        "selected_count": result.get("selected_count"),
        "language_groups": result.get("final_language_group_counts"),
        "capacity_target_met_count": result.get("capacity_target_met_count"),
        "mean_vlm": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "png": result.get("accepted_only_png") or result.get("png"),
    })


if __name__ == "__main__":
    main()
