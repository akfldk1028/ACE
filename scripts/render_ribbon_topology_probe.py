"""Render editable ribbon-topology variants on one real VWorld parcel.

This is a representation benchmark, not a production seed library.  Every
variant uses the same public MassDSL parameters available to the author and
critic agents, so the sheet detects whether topology/width edits materially
change executable geometry.
"""

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

from design.maas.grammar import VerbCall, VerbSequence  # noqa: E402
from design.maas.program_massing.benchmark import _render_archive_sheet  # noqa: E402
from design.maas.program_massing.search import _feature  # noqa: E402
from design.maas.program_massing.vlm_a2a import _source_far_utilization  # noqa: E402
from design.maas.source_geometry import compile_sequence_to_source_mass  # noqa: E402
from design.maas.source_geometry.polygon_quality import evaluate_site_containment  # noqa: E402
from run_neighborhood_vlm_a2a import _resolve_metric_site  # noqa: E402


VARIANTS: tuple[tuple[str, dict], ...] = (
    ("parallel_calm", {
        "field_topology": "parallel", "curvature": 0.08,
        "width_start_ratio": 0.72, "width_mid_ratio": 1.18, "width_end_ratio": 0.76,
    }),
    ("parallel_tapered", {
        "field_topology": "parallel", "curvature": -0.12,
        "width_start_ratio": 1.24, "width_mid_ratio": 0.82, "width_end_ratio": 0.52,
        "width_wave": -0.14,
    }),
    ("branched_early", {
        "field_topology": "branched", "branch_point_ratio": 0.26, "curvature": 0.12,
        "width_start_ratio": 1.05, "width_mid_ratio": 1.30, "width_end_ratio": 0.64,
        "height_start_ratio": 0.48, "height_mid_ratio": 0.98, "height_end_ratio": 0.62, "height_wave": 0.14,
    }),
    ("branched_late", {
        "field_topology": "branched", "branch_point_ratio": 0.54, "curvature": -0.14,
        "width_start_ratio": 0.82, "width_mid_ratio": 1.34, "width_end_ratio": 0.74,
        "height_start_ratio": 0.76, "height_mid_ratio": 0.94, "height_end_ratio": 0.48, "height_wave": -0.12,
    }),
    ("branched_public_fan", {
        "field_topology": "branched", "branch_point_ratio": 0.38, "curvature": 0.17,
        "width_start_ratio": 1.18, "width_mid_ratio": 1.42, "width_end_ratio": 0.58,
        "width_wave": 0.18,
        "height_start_ratio": 0.44, "height_mid_ratio": 1.00, "height_end_ratio": 0.54, "height_wave": 0.20,
    }),
    ("branched_reverse_fan", {
        "field_topology": "branched", "branch_point_ratio": 0.42, "curvature": -0.17,
        "width_start_ratio": 0.60, "width_mid_ratio": 1.38, "width_end_ratio": 1.16,
        "width_wave": -0.18,
        "height_start_ratio": 0.86, "height_mid_ratio": 0.58, "height_end_ratio": 0.96, "height_wave": -0.18,
    }),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pnu", default="1168011800104170004")
    parser.add_argument("--far-limit-ratio", type=float, default=2.5)
    parser.add_argument("--site-boundary-from", type=Path)
    parser.add_argument("--output-stem", default="maas-ribbon-topology-probe-latest")
    args = parser.parse_args()

    site, boundary_source, access_context, access_geometry = _resolve_metric_site(
        args.pnu, args.site_boundary_from,
    )
    features: list[dict] = []
    rows: list[dict] = []
    for name, authored in VARIANTS:
        params = {
            "lane_count": 3,
            "lane_width_ratio": 0.10,
            "vertical_overlap": 0.24,
            "vertical_mode": "terraced",
            "design_field_source": "agent_editable_probe",
            **authored,
        }
        sequence = VerbSequence(
            name,
            f"editable {params['field_topology']} variable-width ribbon field",
            (VerbCall("base", {}), VerbCall("bend", params)),
        )
        source = compile_sequence_to_source_mass(site, sequence)
        if source is None:
            rows.append({"sequence": name, "status": "compile_failed", "params": params})
            continue
        containment = evaluate_site_containment(site, (volume.footprint for volume in source.volumes))
        signature = source.signature()
        coherence = signature.get("coherence_evidence") or {}
        far = _source_far_utilization(
            source, site_area=float(site.area), floors=5, far_limit_ratio=args.far_limit_ratio,
        )
        feature = _feature(
            source, sequence, building_type="neighborhood living",
            height=15.0, floors=5, site_area=float(site.area),
        )
        feature["properties"].update({
            "review_status": "accept" if containment["hard_pass"] and coherence.get("hard_pass") else "reject",
            "review_reasons": [] if coherence.get("hard_pass") else ["coherence_gate_failed"],
            "normalized_far_utilization": far,
            "pnu": args.pnu,
            "site_boundary_geometry": site.__geo_interface__,
            "site_access_context": access_context,
            "site_access_geometry": access_geometry,
        })
        features.append(feature)
        rows.append({
            "sequence": name,
            "status": feature["properties"]["review_status"],
            "params": params,
            "normalized_far_utilization": far,
            "volume_count": len(source.volumes),
            "effective_surface_count": signature.get("effective_surface_count"),
            "coherence": coherence,
            "site_design_field": (signature.get("architectural_ambition_evidence") or {}).get("site_design_field"),
        })

    output_root = REPO_ROOT / "docs" / "playwright" / "design-route-live-verify"
    output_json = output_root / f"{args.output_stem}.json"
    output_png = output_root / f"{args.output_stem}.png"
    result = {
        "schema_version": "arr.maas.ribbon_topology_probe.v1",
        "status": "pass" if len(features) == len(VARIANTS) and all(row["status"] == "accept" for row in rows) else "fail",
        "purpose": "agent-editable representation comparison; not a production 20-candidate result",
        "pnu": args.pnu,
        "boundary_source": boundary_source,
        "site_area_m2": round(float(site.area), 2),
        "rows": rows,
        "png": str(output_png),
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _render_archive_sheet(features, output_png, title=f"MAAS ribbon topology probe - real PNU {args.pnu}")
    print(json.dumps({
        "status": result["status"], "compiled_count": len(features), "png": str(output_png),
        "rows": [{"sequence": row["sequence"], "status": row["status"], "far": row.get("normalized_far_utilization")} for row in rows],
    }, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
