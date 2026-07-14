"""Render the cached graph-native author population before search/selection."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from shapely.geometry import box


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "ARR" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))
load_dotenv(BACKEND_ROOT / ".env")

from design.maas.agents.llm_architect_agent import LLMArchitectAgent  # noqa: E402
from design.maas.llm_proposals import build_site_context  # noqa: E402
from design.maas.program_massing.benchmark import _render_archive_sheet  # noqa: E402
from design.maas.program_massing.scoring import attach_program_massing_evidence  # noqa: E402
from design.maas.program_massing.search import _feature  # noqa: E402
from design.maas.program_massing.vlm_a2a import _source_far_utilization  # noqa: E402
from design.maas.source_geometry import compile_sequence_to_source_mass  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v13")
    parser.add_argument("--author-cache-from", type=Path)
    args = parser.parse_args()
    output = REPO_ROOT / "docs" / "playwright" / "design-route-live-verify"
    base = box(0, 0, 60, 40)
    context = build_site_context(
        site_area_m2=float(base.area),
        building_type="neighborhood living",
        limits={"far": 3.0, "bcr": 0.6, "height": 20.0, "max_seed_floors": 5},
        max_variants=20,
        site_polygon=base,
        access_context={"road_edges": ["south"], "primary_access_edge": "south"},
    )
    batch = LLMArchitectAgent().propose_population(
        site_context=context,
        target_count=24,
        model="gpt-5.4-mini",
        cache_path=(
            args.author_cache_from
            if args.author_cache_from is not None
            else output / f"maas-neighborhood-author-{args.version}-graph-cache.json"
        ),
        batch_size=8,
        overgenerate_count=4,
    )
    features = []
    rows = []
    for sequence in batch.sequences:
        source = compile_sequence_to_source_mass(base, sequence)
        if source is None:
            rows.append({"name": sequence.name, "status": "compile_rejected"})
            continue
        feature = _feature(source, sequence, building_type="neighborhood living", height=15.0, floors=5, site_area=float(base.area))
        evidence = attach_program_massing_evidence(feature, building_type="neighborhood living")
        signature = source.signature()
        far = _source_far_utilization(source, site_area=float(base.area), floors=5, far_limit_ratio=3.0)
        feature["properties"]["normalized_far_utilization"] = far
        features.append(feature)
        rows.append({
            "name": sequence.name,
            "status": "compiled",
            "hard_pass": evidence.get("hard_pass"),
            "program_fit": evidence.get("program_fit_score"),
            "coherence": signature.get("coherence_evidence"),
            "spatial": feature.get("properties", {}).get("program_spatial_evidence"),
            "far_utilization": far,
            "volumes": len(source.volumes),
            "surfaces": signature.get("surface_count"),
            "logical_surfaces": signature.get("logical_surface_count"),
            "principle": signature.get("formal_principle"),
            "graph": signature.get("graph_materialization_evidence"),
        })
    png = output / f"maas-graph-author-{args.version}-probe.png"
    _render_archive_sheet(features, png, title=f"MAAS graph-native author probe {args.version}")
    print({"authored": len(batch.sequences), "compiled": len(features), "png": str(png)})
    for row in rows:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
