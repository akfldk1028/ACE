"""Deterministic cross-program MAAS benchmark with a clean PNG artifact."""

from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from pathlib import Path
from statistics import mean
from typing import Any

from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import box, mapping, shape

from design.maas.preference.loop import feature_preview_png
from .profiles import resolve_program_profile
from .search import search_creative_elites, search_program_elites


PROGRAM_CASES = (
    ("공동주택", "housing", 18.0, 6),
    ("카페", "cafe", 6.0, 2),
    ("체육관", "gymnasium", 12.0, 2),
)


def run_program_massing_benchmark(*, output_json: Path, output_png: Path) -> dict[str, Any]:
    base = box(0, 0, 60, 40)
    rows: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []
    search_reports: dict[str, Any] = {}
    for building_type, expected_profile, height, floors in PROGRAM_CASES:
        profile = resolve_program_profile(building_type)
        elites, search_report = search_program_elites(base, building_type=building_type, height=height, floors=floors)
        search_reports[profile["id"]] = search_report
        for elite in elites:
            sequence, source, feature = elite.sequence, elite.source, elite.feature
            evidence = feature["properties"]["program_massing_evidence"]
            rows.append({
                "building_type": building_type,
                "profile_id": profile["id"],
                "expected_profile": expected_profile,
                "sequence": sequence.name,
                "verbs": [item.verb for item in sequence.calls],
                "family": source.signature().get("family"),
                "volume_count": len(source.volumes),
                "surface_count": len(source.surfaces),
                "footprint_area_ratio": round(source.footprint.area / base.area, 3),
                "program_fit_score": evidence["program_fit_score"],
                "program_hard_pass": evidence["hard_pass"],
                "architectural_score": feature["properties"]["program_spatial_evidence"]["architectural_score"],
            })
            features.append(feature)
    profile_groups = {
        profile_id: [row for row in rows if row["profile_id"] == profile_id]
        for profile_id in ("housing", "cafe", "gymnasium")
    }
    fingerprints = {
        profile_id: sorted({(tuple(row["verbs"]), row["family"], row["volume_count"]) for row in group}, key=str)
        for profile_id, group in profile_groups.items()
    }
    failures: list[str] = []
    for profile_id, group in profile_groups.items():
        if len(group) < 2:
            failures.append(f"{profile_id}_seed_count_below_2")
        if group and mean(row["program_fit_score"] for row in group) < 0.75:
            failures.append(f"{profile_id}_mean_program_fit_below_0.75")
        if group and min(row["architectural_score"] for row in group) < 0.88:
            failures.append(f"{profile_id}_architectural_floor_below_0.88")
        if not all(row["program_hard_pass"] for row in group):
            failures.append(f"{profile_id}_program_hard_gate_failure")
    if len({json.dumps(value, sort_keys=True) for value in fingerprints.values()}) < 3:
        failures.append("program_geometry_fingerprints_not_distinct")
    if sum(int(report.get("evaluated_count") or 0) for report in search_reports.values()) < 300:
        failures.append("program_search_did_not_evaluate_300_candidates")
    if sum(int(report.get("rejected_count") or 0) for report in search_reports.values()) < 1:
        failures.append("program_search_rejected_no_invalid_candidates")
    result = {
        "schema_version": "arr.maas.program_massing_benchmark.v1",
        "status": "pass" if not failures else "fail",
        "case_count": len(rows),
        "profile_count": len(profile_groups),
        "mean_program_fit": round(mean(row["program_fit_score"] for row in rows), 4) if rows else 0.0,
        "profile_mean_scores": {
            key: round(mean(row["program_fit_score"] for row in group), 4) if group else 0.0
            for key, group in profile_groups.items()
        },
        "distinct_profile_fingerprint_count": len({json.dumps(value, sort_keys=True) for value in fingerprints.values()}),
        "search_reports": search_reports,
        "rows": rows,
        "failures": failures,
        "png": str(output_png),
    }
    _render_contact_sheet(features, output_png)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _render_contact_sheet(features: list[dict[str, Any]], output: Path) -> None:
    card_w, card_h, columns = 720, 570, 2
    rows = (len(features) + columns - 1) // columns
    canvas = Image.new("RGB", (card_w * columns, 72 + card_h * rows), "#07111f")
    draw = ImageDraw.Draw(canvas)
    try:
        title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
        label_font = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 15)
    except OSError:
        title_font = label_font = ImageFont.load_default()
    draw.text((24, 20), "MAAS program-conditioned mass benchmark", fill="#f8fafc", font=title_font)
    with tempfile.TemporaryDirectory(prefix="maas-program-benchmark-") as temporary:
        for index, feature in enumerate(features):
            raw_preview = Image.open(feature_preview_png(feature, Path(temporary))).convert("RGBA")
            preview = Image.new("RGBA", raw_preview.size, "white")
            preview.alpha_composite(raw_preview)
            preview = preview.convert("RGB")
            x = index % columns * card_w
            y = 72 + index // columns * card_h
            canvas.paste(preview, (x, y))
            props = feature["properties"]
            evidence = props["program_massing_evidence"]
            draw.rectangle((x, y + 520, x + card_w, y + card_h), fill="#101d32")
            label = f"{props['building_type']} · {evidence['profile_id']} · fit {evidence['program_fit_score']:.3f} · {props['variant_id']}"
            draw.text((x + 14, y + 534), label, fill="#f8fafc", font=label_font)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def run_creative_20_archive_benchmark(*, output_json: Path, output_png: Path) -> dict[str, Any]:
    base = box(0, 0, 60, 40)
    elites, search_report = search_creative_elites(
        base,
        height=18.0,
        floors=6,
        generations=5,
        offspring_per_seed=16,
        random_seed=417,
        target_count=20,
    )
    rows = []
    for elite in elites:
        props = elite.feature["properties"]
        evidence = props["creative_mass_evidence"]
        rows.append({
            "variant_id": props["variant_id"],
            "topology": props["variant_id"].split("__search_", 1)[0],
            "score": elite.score,
            "creative_score": evidence["creative_score"],
            "coherence_score": evidence["coherence_score"],
            "dominant_component_ratio": evidence["dominant_component_ratio"],
            "site_coverage_ratio": evidence["site_coverage_ratio"],
            "volume_count": len(props["mass_volumes"]),
            "surface_count": props["source_signature"]["surface_count"],
            "sculptural_geometry": bool(evidence.get("sculptural_geometry")),
            "non_rectilinear_volume_count": int(evidence.get("non_rectilinear_volume_count") or 0),
            "hard_pass": bool(evidence["hard_pass"]),
        })
    topology_count = len({row["topology"] for row in rows})
    geometric_language_count = int(search_report.get("geometric_language_count") or 0)
    failures = []
    if len(rows) != 20:
        failures.append("archive_did_not_select_20")
    if topology_count < 12:
        failures.append("formal_operation_graph_count_below_12")
    if geometric_language_count < 14:
        failures.append("geometric_language_count_below_14")
    if rows and min(row["creative_score"] for row in rows) < 0.75:
        failures.append("creative_quality_floor_below_0.75")
    if not all(row["hard_pass"] for row in rows):
        failures.append("creative_archive_contains_clean_mass_gate_failure")
    sculptural_count = sum(1 for row in rows if row["sculptural_geometry"])
    if sculptural_count < 8:
        failures.append("sculptural_geometry_count_below_8_box_bias")
    result = {
        "schema_version": "arr.maas.creative_archive_benchmark.v1",
        "stage": "creative_form_exploration",
        "program_conditioned": False,
        "legal_parking_checked": False,
        "status": "pass" if not failures else "fail",
        "selected_count": len(rows),
        "topology_count": topology_count,
        "geometric_language_count": geometric_language_count,
        "mean_creative_score": round(mean(row["creative_score"] for row in rows), 4) if rows else 0.0,
        "minimum_creative_score": min((row["creative_score"] for row in rows), default=0.0),
        "sculptural_geometry_count": sculptural_count,
        "rectilinear_extrusion_count": len(rows) - sculptural_count,
        "search_report": search_report,
        "rows": rows,
        "failures": failures,
        "png": str(output_png),
    }
    board_features = []
    for index, elite in enumerate(elites):
        feature = deepcopy(elite.feature)
        props = feature["properties"]
        source_name = str(props["variant_id"])
        topology = source_name.split("__search_", 1)[0]
        props["archive_variant_id"] = source_name
        props["variant_id"] = f"maas_{index + 1:02d}"
        props["mass_shape"] = topology.replace("creative_", "")
        props["maas_concept"] = "creative source archive; program/legal projection pending"
        props["typology_family"] = props["source_signature"].get("family")
        props["operator_family"] = props["source_signature"].get("family")
        props["maas_sequence_verbs"] = list(props["source_signature"].get("verb_profile") or [])
        props["far"] = 0.0
        props["bcr"] = round(shape(feature["geometry"]).area / float(base.area) * 100.0, 1)
        props["parking_precheck"] = {
            "required_count": {},
            "layout_candidate": {"status": "source archive; legal/parking not run", "provided_spaces": "-", "required_spaces": "-", "stalls": []},
        }
        board_features.append(feature)
    result.update({
        "pnu": "normalized-creative-archive",
        "building_type": "creative mass exploration",
        "elapsed_ms": 0,
        "boundary": {"type": "Feature", "geometry": mapping(base), "properties": {}},
        "response": {"feature_collection": {"type": "FeatureCollection", "features": board_features}},
    })
    _render_archive_sheet([elite.feature for elite in elites], output_png)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def run_housing_20_archive_benchmark(*, output_json: Path, output_png: Path) -> dict[str, Any]:
    """Backward-compatible entry point; the source archive is now program-neutral."""
    return run_creative_20_archive_benchmark(output_json=output_json, output_png=output_png)


def _render_archive_sheet(features: list[dict[str, Any]], output: Path) -> None:
    # Human review uses one large isometric image per candidate in the same 5x4
    # arrangement as the established legal board. The VLM still receives the
    # full four-view preview; front/top/opposite are diagnostic evidence and
    # must not visually multiply candidates on the primary review sheet.
    card_w, card_h, columns = 384, 300, 5
    row_count = (len(features) + columns - 1) // columns
    canvas = Image.new("RGB", (card_w * columns, 72 + card_h * row_count), "#07111f")
    draw = ImageDraw.Draw(canvas)
    try:
        title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 25)
        label_font = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 13)
    except OSError:
        title_font = label_font = ImageFont.load_default()
    draw.text((24, 20), "MAAS — 20 program-neutral creative mass elites", fill="#f8fafc", font=title_font)
    with tempfile.TemporaryDirectory(prefix="maas-creative-archive-") as temporary:
        for index, feature in enumerate(features):
            raw = Image.open(feature_preview_png(feature, Path(temporary))).convert("RGBA")
            raw = raw.crop((0, 0, 360, 250))
            flattened = Image.new("RGBA", raw.size, "white")
            flattened.alpha_composite(raw)
            preview = flattened.convert("RGB").resize((card_w, 260), Image.Resampling.LANCZOS)
            x, y = index % columns * card_w, 72 + index // columns * card_h
            canvas.paste(preview, (x, y))
            props = feature["properties"]
            evidence = props["creative_mass_evidence"]
            draw.rectangle((x, y + 260, x + card_w, y + card_h), fill="#101d32")
            source_id = str(props.get("archive_variant_id") or props["variant_id"])
            topology = source_id.split("__search_", 1)[0].replace("creative_", "")
            label = f"{index + 1:02d} {topology} · creative {evidence['creative_score']:.3f}"
            draw.text((x + 12, y + 274), label, fill="#f8fafc", font=label_font)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


__all__ = ["run_creative_20_archive_benchmark", "run_housing_20_archive_benchmark", "run_program_massing_benchmark"]
