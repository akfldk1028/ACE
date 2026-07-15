"""Reproducible real-PNU MAAS mixed-language run with oblique envelopes."""

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
from design.maas.program_massing.vlm_a2a import generation_feedback_from_result
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
    stem = os.getenv("MAAS_RUN_STEM", "maas-neighborhood-vlm-a2a-v95-oblique-envelope")
    feedback_stem = os.getenv("MAAS_FEEDBACK_STEM", "").strip()
    if feedback_stem:
        feedback_json = output_root / f"{feedback_stem}.json"
        feedback_payload = __import__("json").loads(feedback_json.read_text(encoding="utf-8"))
        generation_feedback = generation_feedback_from_result(feedback_payload)
        supplemental_author_caches = (
            output_root / f"{feedback_stem}-author-graph-cache.json",
        )
        supplemental_vlm_caches = (
            output_root / f"{feedback_stem}-vlm-score-cache.json",
        )
        accepted_seed_paths = (feedback_json,)
    else:
        generation_feedback = None
        supplemental_author_caches = ()
        supplemental_vlm_caches = (
            output_root / "maas-neighborhood-vlm-a2a-v94-visible-section-mutation-vlm-score-cache.json",
        )
        accepted_seed_paths = (
            output_root / "maas-neighborhood-vlm-a2a-v94-visible-section-mutation.json",
        )
    result = run_adaptive_neighborhood_vlm_a2a_loop(
        output_json=output_root / f"{stem}.json",
        output_png=output_root / f"{stem}.png",
        max_rounds=1,
        model="gpt-5.4-mini",
        author_model="gpt-5.4-mini",
        author_target_count=int(os.getenv("MAAS_AUTHOR_TARGET_COUNT", "32")),
        # A new contract needs a fresh author population. Reusing v91 would
        # prove only that old section graphs still run, not that the LLM can
        # author the new polygon-ring genotype.
        author_cache_path=output_root / f"{stem}-author-graph-cache.json",
        supplemental_author_cache_paths=supplemental_author_caches,
        accepted_seed_result_paths=accepted_seed_paths,
        vlm_cache_path=output_root / f"{stem}-vlm-score-cache.json",
        supplemental_vlm_cache_paths=supplemental_vlm_caches,
        generation_feedback=generation_feedback,
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
