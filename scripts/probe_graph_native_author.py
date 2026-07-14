"""Small, bounded diagnostic for the graph-native MAAS author contract."""

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

from design.maas.llm_proposals import build_site_context, generate_llm_massdsl_batch  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--target-count", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()
    site = box(0, 0, 60, 40)
    context = build_site_context(
        site_area_m2=float(site.area),
        building_type="neighborhood living",
        limits={"far": 3.0, "bcr": 0.6, "height": 20.0, "max_seed_floors": 5},
        max_variants=args.target_count,
        site_polygon=site,
        access_context={"road_edges": ["south"], "primary_access_edge": "south"},
    )
    batch = generate_llm_massdsl_batch(
        site_context=context,
        target_count=max(3, args.target_count),
        model=args.model,
        timeout=args.timeout,
        batch_size=max(3, args.target_count),
        batch_retries=1,
        batch_workers=1,
        max_openai_batches=1,
        overgenerate_count=0,
        max_output_tokens=6000,
        allow_subbatch_recovery=False,
    )
    artifact = batch.artifact
    print({
        "model": artifact.get("model"),
        "elapsed_ms": artifact.get("elapsed_ms"),
        "compiled_sequence_count": artifact.get("compiled_sequence_count"),
        "timeout_coverage_repair_count": artifact.get("timeout_coverage_repair_count"),
        "openai_batch_errors": artifact.get("openai_batch_errors"),
        "rejected_sequence_samples": artifact.get("rejected_sequence_samples"),
    })
    for sequence in batch.sequences:
        graph_note = next((note for note in sequence.notes if note.startswith("component_graph_json=")), "")
        print(sequence.name, "graph_native=", bool(graph_note), "verbs=", [call.verb for call in sequence.calls])
    return 0 if not artifact.get("timeout_coverage_repair_count") else 2


if __name__ == "__main__":
    raise SystemExit(main())
