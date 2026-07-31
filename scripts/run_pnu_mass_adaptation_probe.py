"""Compile an accepted MAAS graph archive on a real VWorld PNU parcel."""

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

from design.maas.program_massing.benchmark import _render_archive_sheet  # noqa: E402
from design.maas.program_massing.search import _feature  # noqa: E402
from design.maas.program_massing.vlm_a2a import (  # noqa: E402
    _sequence_from_record,
    _source_far_utilization,
)
from design.maas.source_geometry import compile_sequence_to_source_mass  # noqa: E402
from design.maas.source_geometry.polygon_quality import evaluate_site_containment  # noqa: E402
from run_neighborhood_vlm_a2a import _resolve_metric_site  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pnu", default="1168011800104170004")
    parser.add_argument("--far-limit-ratio", type=float, default=2.5)
    parser.add_argument(
        "--accepted-seed-from",
        type=Path,
        default=REPO_ROOT / "docs" / "playwright" / "design-route-live-verify"
        / "maas-neighborhood-vlm-a2a-v53-full-frontier-repeatability-contract.json",
    )
    parser.add_argument("--site-boundary-from", type=Path)
    parser.add_argument(
        "--output-stem",
        help="Artifact stem; defaults to a PNU-specific latest adaptation name.",
    )
    args = parser.parse_args()

    site, boundary_source, access_context, access_geometry = _resolve_metric_site(
        args.pnu,
        args.site_boundary_from,
    )
    archive = json.loads(args.accepted_seed_from.read_text(encoding="utf-8"))
    sequences = [
        sequence
        for record in archive.get("accepted_sequences") or []
        if (sequence := _sequence_from_record(record)) is not None
    ]
    features = []
    rows = []
    for sequence in sequences:
        source = compile_sequence_to_source_mass(site, sequence)
        if source is None:
            rows.append({"sequence": sequence.name, "status": "compile_failed"})
            continue
        containment = evaluate_site_containment(
            site,
            (volume.footprint for volume in source.volumes),
        )
        within = bool(containment["hard_pass"])
        far_utilization = _source_far_utilization(
            source,
            site_area=float(site.area),
            floors=5,
            far_limit_ratio=float(args.far_limit_ratio),
        )
        feature = _feature(
            source,
            sequence,
            building_type="neighborhood living",
            height=15.0,
            floors=5,
            site_area=float(site.area),
        )
        props = feature["properties"]
        props.update({
            "review_status": "accept" if within else "reject",
            "review_reasons": [] if within else ["outside_real_pnu_boundary"],
            "normalized_far_utilization": far_utilization,
            "pnu": args.pnu,
            "site_boundary_source": boundary_source,
            "site_boundary_geometry": site.__geo_interface__,
            "site_access_context": access_context,
            "site_access_geometry": access_geometry,
        })
        features.append(feature)
        signature = source.signature()
        rows.append({
            "sequence": sequence.name,
            "status": "pass" if within else "outside_site",
            "within_site": within,
            "normalized_far_utilization": far_utilization,
            "volume_count": len(source.volumes),
            "surface_count": len(source.surfaces),
            "site_containment": containment,
            "site_design_field": (
                signature.get("architectural_ambition_evidence") or {}
            ).get("site_design_field"),
        })

    output_root = REPO_ROOT / "docs" / "playwright" / "design-route-live-verify"
    output_stem = args.output_stem or f"maas-pnu-{args.pnu}-site-adaptation-latest"
    output_json = output_root / f"{output_stem}.json"
    output_png = output_root / f"{output_stem}.png"
    result = {
        "schema_version": "arr.maas.pnu_mass_adaptation.v1",
        "status": "pass" if len(features) == 20 and all(row.get("within_site") for row in rows) else "fail",
        "pnu": args.pnu,
        "boundary_source": boundary_source,
        "site_area_m2": round(float(site.area), 2),
        "site_bounds_m": [round(float(value), 3) for value in site.bounds],
        "far_limit_ratio": float(args.far_limit_ratio),
        "site_access_context": access_context,
        "site_access_geometry": access_geometry,
        "source_archive": str(args.accepted_seed_from),
        "compiled_count": len(features),
        "within_site_count": sum(bool(row.get("within_site")) for row in rows),
        "capacity_target_count": sum(
            float(row.get("normalized_far_utilization") or 0.0) >= 0.90 for row in rows
        ),
        "rows": rows,
        "png": str(output_png),
    }
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _render_archive_sheet(
        features,
        output_png,
        title=f"MAAS real PNU {args.pnu} — accepted graph site adaptation",
    )
    print(json.dumps({key: result[key] for key in (
        "status", "pnu", "boundary_source", "site_area_m2", "compiled_count",
        "within_site_count", "capacity_target_count", "png",
    )}, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
