"""Fast, measured BOOK-operation portfolios on one real parcel.

This benchmark is intentionally bounded: it compiles typed operations over
program assemblies once, filters by clean/program gates, and performs measured
shape-diverse selection.  It is the synchronous diagnostic counterpart to the
slower evolutionary/VLM loop, not a replacement for legal/FAR/parking repair.
"""

from __future__ import annotations

import json
import hashlib
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import dataclass, replace
from math import atan2, cos, degrees, hypot, pi, sin, sqrt
from pathlib import Path
from time import perf_counter
from typing import Any

from PIL import Image
from shapely.errors import GEOSException
from shapely.geometry import Polygon, mapping, shape

from design.maas.geometry_language import (
    GeometryOutcomeGraph,
    GeometryProgram,
    GeometryAuthorError,
    audit_reference_matches_for_massing,
    author_geometry_programs_with_openai,
    build_geometry_graph_notes,
    build_geometry_graph_snapshot,
    apply_book_projection_to_geometry_program,
    apply_geometry_edits,
    apply_geometry_edits_compiler_safe,
    architectural_shape_programs,
    reference_language_programs,
    replace_source_dominant_with_geometry_program,
    openai_vlm_geometry_critic,
    retrieve_geometry_reference_matches,
    run_geometry_program_a2a_loop,
    synthesize_architectural_programs,
    synthesis_requests_from_program_profile,
    compile_geometry_program_to_source_mass,
    compile_geometry_program,
)
from design.maas.geometry_language.gate import GeometryGatePolicy, compilation_gate
from design.maas.capacity_policy import resolve_massing_capacity_policy
from design.maas.grammar.verb_sequence import VerbSequence
from design.maas.mass_brain import publish_geometry_portfolio_shadow
from design.maas.program_massing import (
    ProgramSectionGraphEdit,
    book_sentence_variants,
    compose_program_with_book_operations,
    mutate_program_section_sequence,
    program_reference_contract,
    program_seed_sequences,
    resolve_program_profile,
)
from design.maas.program_massing.assembly import program_component_chassis
from design.maas.program_massing.benchmark import render_archive_sheet
from design.maas.program_massing.morphology import (
    intrinsic_section_profile_distance,
    intrinsic_shape_distance,
    intrinsic_silhouette_distance,
)
from design.maas.program_massing.scoring import attach_program_massing_evidence
from design.maas.program_massing.search import program_seed_variants, source_feature
from design.maas.preference.loop import feature_preview_png, openai_preview_preference_scorer
from design.maas.preference.vlm_scorer import score_portfolio_board_with_openai_vlm
from design.maas.source_geometry import compile_sequence_to_source_mass
from design.maas.book_language.mass_passport_bridge import selected_candidate_execution_passport


def default_outcome_graph_path(pnu: str) -> Path:
    """Return the cross-run portable memory for one parcel.

    Diagnostic output directories are intentionally disposable.  Keeping the
    causal graph below one of those directories made every new benchmark start
    without the previous VLM failures and typed repairs.  The default is now a
    PNU-keyed cache at repository scope; callers may still supply an explicit
    path (for isolated ablations or controlled experiments).
    """
    configured_dir = os.getenv("MAAS_OUTCOME_GRAPH_DIR", "").strip()
    base_dir = (
        Path(configured_dir).resolve()
        if configured_dir
        else Path(__file__).resolve().parents[5]
        / "docs"
        / "ai-session-memory"
        / "maas-cache"
        / "outcome-graphs"
    )
    safe_pnu = "".join(character for character in str(pnu) if character.isalnum() or character in "-_")
    if not safe_pnu:
        safe_pnu = hashlib.sha256(str(pnu).encode("utf-8")).hexdigest()[:20]
    return base_dir / f"pnu-{safe_pnu}.json"

from .registry import build_book_language_registry
from .semantics import BASE_VOLUME_FRACTIONS
from .downstream_hard_gate import (
    LegalGenerationContext,
    build_legal_generation_context,
    evaluate_accepted_sources_downstream,
    fit_source_to_sunlight_field,
    generation_site_at_height,
)
from .capacity_contract import (
    build_feasible_capacity_contract,
    measure_source_capacity,
    recursive_plan_coverage_floor,
)
from .lineage import gate_descendants_by_base, lineage_record, staged_principle_schedule


from .candidate_analysis import (
    _Candidate,
    _distance,
    _silhouette_distance,
    _scope_key,
    _capacity_alternative_key,
    _seed_family,
    _section_family,
    _roof_archetype,
    _chassis_family,
    _geometry_program_family,
    _geometry_program_metadata,
    _plan_family,
    _vlm_reviewed_program_candidate,
    _llm_authored_candidate,
    _seed_is_llm_authored,
    _solid_morphology_metrics,
    _section_silhouette_flags,
    _program_form_gate,
    _architectural_articulation_metrics,
    _design_concept_descriptor,
    _program_section_phenotype,
    _oriented_aspect,
    _oriented_plan_dimensions,
    _program_dimensional_context,
    _fingerprint,
    _inside_site,
    _clean_mass_gate,
    _site_access_side_in_principal_frame,
)

from .portfolio_selection import (
    _scope_coverage_anchors,
    _select,
    _selection_capacity_diagnostics,
    _rebalance_measured_morphologies,
    _bounded_visual_selection_pool,
    _target_hard_pass_universe,
)
from .quality_diversity_archive import qd_archive_evidence

from .gate_diagnostics import (
    _empty_gate_diagnostic,
    _record_gate_diagnostic,
    _metric_summary,
    _summarize_gate_diagnostic,
    _merge_gate_diagnostics,
)

from .program_catalog import PROGRAMS
from .portfolio_feedback import enrich_portfolio_vlm_feedback
from .final_vlm_cycle import run_final_vlm_cycle
from .portfolio_replenishment import (
    replenishment_cycle_budget_for_run,
    replenishment_stop_reason,
    run_replenishment_cycle,
)
from .reference_context import (
    _audited_final_book_references,
    _reference_language_author_context,
)

from .candidate_generation import (
    _agent_mutated_seeds,
    _prebook_vlm_quarantined_llm_parents,
    _geometry_program_registry,
    _materialize_directed_geometry,
    _program_pool,
)

from .vlm_review import (
    _final_book_vlm_hard_pass,
    _final_book_vlm_shortlist,
    _audit_final_book_geometry_with_vlm,
    audit_book_base_stage_with_vlm,
    _repair_exact_post_book_candidates_from_vlm,
    _exact_post_book_repair_shortlist,
)


def _partition_replenishment_vlm_candidates(
    retained_hard_passes: list[_Candidate],
    new_candidates: list[_Candidate],
) -> tuple[list[_Candidate], list[_Candidate]]:
    """Keep prior exact passes out of the new-candidate VLM review pool."""
    return (
        list(retained_hard_passes),
        _bounded_visual_selection_pool(list(new_candidates)),
    )


def _load_visual_directive(output_dir: Path, pnu: str) -> dict[str, Any]:
    path = output_dir / "maas-book-programs-vlm-directive.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != "arr.maas.portfolio_vlm_directive.v1"
        or str(payload.get("pnu") or "") != pnu
        or payload.get("status") != "active"
    ):
        return {}
    return payload


def _archive_render_evidence(board: Path, candidate_count: int) -> list[dict[str, Any]]:
    """Measure whether each accepted card visibly contains rendered mass.

    Geometry validity alone cannot catch a camera/transport regression that
    produces an apparently empty review card.  The archive renderer uses one
    stable orange material, so record a conservative material-pixel ratio as
    post-render evidence.  This is not a design-quality score and does not
    replace direct PNG review.
    """
    try:
        image = Image.open(board).convert("RGB")
    except (OSError, ValueError):
        return []
    card_w, card_h, columns, header_h, preview_h = 384, 322, 5, 72, 260
    evidence: list[dict[str, Any]] = []
    for index in range(max(0, int(candidate_count))):
        x = (index % columns) * card_w
        y = header_h + (index // columns) * card_h
        pixels = image.crop((x, y, x + card_w, y + preview_h)).getdata()
        material_pixels = sum(
            1 for red, green, blue in pixels
            if red > 90 and red >= green + 18 and green >= blue + 8
        )
        ratio = material_pixels / float(card_w * preview_h)
        evidence.append({
            "card_index": index + 1,
            "board_png": str(board),
            "crop_box": [x, y, x + card_w, y + preview_h],
            "rendered_mass_pixel_count": material_pixels,
            "rendered_mass_pixel_ratio": round(ratio, 5),
            "hard_pass": ratio >= 0.005,
            "evidence_role": "human_and_vlm_visual_observation_not_geometry_authority",
        })
    return evidence


def _candidate_language_descriptor(candidate: _Candidate) -> dict[str, Any]:
    source = candidate.source
    poly = source.footprint
    aspect = _oriented_aspect(poly)
    compactness = 4.0 * pi * float(poly.area) / max(float(poly.length) ** 2, 1e-9)
    spatial = candidate.feature.get("properties", {}).get("program_spatial_evidence", {})
    section = source.metadata.get("program_section_graph_evidence") or {}
    materialized = section.get("materialized_nodes") if isinstance(section, dict) else ()
    controls = tuple(
        tuple(tuple(float(value) for value in item) for item in (node.get("section_controls") or ()))
        for node in (materialized or ())
        if isinstance(node, dict) and node.get("section_controls")
    )
    role_tokens = Counter()
    for volume in source.volumes:
        role = str(volume.role).lower()
        for token in (
            "hall", "service", "entry", "monitor", "canopy", "gallery",
            "public", "bridge", "ramp", "court", "street", "terrace", "ribbon",
        ):
            if token in role:
                role_tokens[token] += 1
    for zone in source.metadata.get("program_space_zones") or ():
        role = str(zone.get("role") or "").lower() if isinstance(zone, dict) else ""
        for token in (
            "hall", "service", "entry", "monitor", "canopy", "gallery",
            "public", "bridge", "ramp", "court", "street", "terrace", "ribbon",
        ):
            if token in role:
                role_tokens[token] += 1
    morphology = _solid_morphology_metrics(candidate)
    articulation = _architectural_articulation_metrics(source)
    design_concept = _design_concept_descriptor(candidate)
    program_form = candidate.feature.get("properties", {}).get("program_form_gate", {})
    capacity_alternative = source.metadata.get("capacity_alternative_projection") or {}
    capacity_measurement = source.metadata.get("source_capacity_measurement") or {}
    return {
        "seed_family": _seed_family(candidate),
        "section_family": _section_family(candidate),
        "roof_archetype": _roof_archetype(candidate),
        "chassis_family": _chassis_family(candidate),
        "geometry_program_family": _geometry_program_family(candidate) or "none",
        "solid_phenotype": morphology["phenotype"],
        "body_phenotype": morphology.get("body_phenotype") or morphology["phenotype"],
        "section_phenotype": morphology.get("section_phenotype") or "none",
        "wedge_like": morphology["wedge_like"],
        "pyramidal_like": morphology["pyramidal_like"],
        "collapsed_profiled_tent_like": bool(morphology.get("collapsed_profiled_tent_like")),
        "degenerate_sheet_like": morphology["degenerate_sheet_like"],
        "horizontal_surface_ratio": morphology["horizontal_surface_ratio"],
        "vertical_surface_ratio": morphology["vertical_surface_ratio"],
        "sloped_surface_ratio": morphology["sloped_surface_ratio"],
        "normal_direction_bin_count": morphology["normal_direction_bin_count"],
        "horizontal_level_count": morphology["horizontal_level_count"],
        "plan_convexity": morphology["plan_convexity"],
        "upper_area_ratio": morphology["upper_area_ratio"],
        "solid_genus": morphology["genus"],
        "solid_component_count": morphology["component_count"],
        "book_scope": _scope_key(candidate),
        "capacity_alternative_id": _capacity_alternative_key(candidate),
        "capacity_target_utilization": float(
            capacity_alternative.get("target_utilization") or 0.0
        ),
        "capacity_achieved_utilization": float(
            capacity_measurement.get("feasible_capacity_utilization") or 0.0
        ),
        "capacity_target_hard_pass": bool(
            capacity_alternative.get("target_hard_pass")
        ),
        "far_pct": float(capacity_measurement.get("far_pct") or 0.0),
        "oriented_plan_aspect_ratio": round(aspect, 4),
        "plan_compactness": round(compactness, 4),
        "plan_family": _plan_family(candidate),
        "dominant_component_ratio": round(float(spatial.get("dominant_component_ratio") or 0.0), 4),
        "site_coverage_ratio": round(float(spatial.get("site_coverage_ratio") or 0.0), 4),
        "hierarchy_score": round(float(spatial.get("hierarchy_score") or 0.0), 4),
        "section_control_signature": controls,
        "semantic_role_tokens": dict(sorted(role_tokens.items())),
        "body_rule_count": articulation["body_rule_count"],
        "program_body_rule_count": articulation["program_rule_count"],
        "public_threshold_rule_count": articulation["public_threshold_rule_count"],
        "book_body_rule_count": articulation["book_rule_count"],
        "body_rule_family_counts": articulation["family_counts"],
        "body_rules": articulation["rules"],
        "design_concept": design_concept,
        "design_concept_key": design_concept["concept_key"],
        "ground_strategy": design_concept["ground_strategy"],
        "frontage_aligned_public_threshold": design_concept["frontage_aligned"],
        "missing_required_design_concepts": design_concept["missing_required_concepts"],
        "measured_clear_span_m": float(program_form.get("measured_clear_span_m") or 0.0),
        "measured_solid_height_m": float(program_form.get("measured_solid_height_m") or 0.0),
        "height_to_clear_span_ratio": float(program_form.get("height_to_clear_span_ratio") or 0.0),
    }


def _portfolio_language_metrics(selected: list[_Candidate]) -> dict[str, Any]:
    descriptors = [_candidate_language_descriptor(candidate) for candidate in selected]
    seed_counts = Counter(item["seed_family"] for item in descriptors)
    section_counts = Counter(item["section_family"] for item in descriptors)
    roof_archetype_counts = Counter(item["roof_archetype"] for item in descriptors)
    chassis_counts = Counter(item["chassis_family"] for item in descriptors)
    geometry_program_counts = Counter(
        item["geometry_program_family"]
        for item in descriptors
        if item["geometry_program_family"] != "none"
    )
    phenotype_counts = Counter(item["solid_phenotype"] for item in descriptors)
    section_phenotype_counts = Counter(item["section_phenotype"] for item in descriptors)
    wedge_like_count = sum(bool(item["wedge_like"]) for item in descriptors)
    pyramidal_like_count = sum(bool(item["pyramidal_like"]) for item in descriptors)
    plan_counts = Counter(item["plan_family"] for item in descriptors)
    ground_strategy_counts = Counter(item["ground_strategy"] for item in descriptors)
    concept_key_counts = Counter(item["design_concept_key"] for item in descriptors)
    capacity_alternative_counts = Counter(
        item["capacity_alternative_id"] for item in descriptors
        if item["capacity_alternative_id"] != "unclassified"
    )
    control_signatures = {
        json.dumps(item["section_control_signature"], sort_keys=True)
        for item in descriptors
        if item["section_control_signature"]
    }

    def mean(name: str) -> float:
        values = [float(item[name]) for item in descriptors]
        return round(sum(values) / len(values), 4) if values else 0.0

    total = max(1, len(descriptors))
    return {
        "schema_version": "arr.maas.program_language_metrics.v1",
        "candidate_count": len(descriptors),
        "capacity_alternative_counts": dict(sorted(capacity_alternative_counts.items())),
        "capacity_alternative_count": len(capacity_alternative_counts),
        "capacity_target_pass_count": sum(
            bool(item["capacity_target_hard_pass"]) for item in descriptors
        ),
        "mean_capacity_target_utilization": mean("capacity_target_utilization"),
        "mean_capacity_achieved_utilization": mean("capacity_achieved_utilization"),
        "mean_far_pct": mean("far_pct"),
        "seed_family_counts": dict(sorted(seed_counts.items())),
        "seed_family_count": len(seed_counts),
        "dominant_seed_family_share": round(max(seed_counts.values(), default=0) / total, 4),
        "roof_section_family_counts": dict(sorted(section_counts.items())),
        "roof_section_family_count": len(section_counts),
        "dominant_roof_section_family_share": round(max(section_counts.values(), default=0) / total, 4),
        "roof_archetype_counts": dict(sorted(roof_archetype_counts.items())),
        "roof_archetype_count": len(roof_archetype_counts),
        "dominant_roof_archetype_share": round(max(roof_archetype_counts.values(), default=0) / total, 4),
        "chassis_family_counts": dict(sorted(chassis_counts.items())),
        "chassis_family_count": len(chassis_counts),
        "dominant_chassis_family_share": round(max(chassis_counts.values(), default=0) / total, 4),
        "recursive_geometry_program_counts": dict(sorted(geometry_program_counts.items())),
        "recursive_geometry_program_count": sum(geometry_program_counts.values()),
        "recursive_geometry_family_count": len(geometry_program_counts),
        "solid_phenotype_counts": dict(sorted(phenotype_counts.items())),
        "solid_phenotype_count": len(phenotype_counts),
        "dominant_solid_phenotype_share": round(max(phenotype_counts.values(), default=0) / total, 4),
        "section_phenotype_counts": dict(sorted(section_phenotype_counts.items())),
        "section_phenotype_count": len(section_phenotype_counts),
        "collapsed_profiled_tent_like_count": sum(
            bool(item["collapsed_profiled_tent_like"]) for item in descriptors
        ),
        "wedge_like_count": wedge_like_count,
        "wedge_like_share": round(wedge_like_count / total, 4),
        "pyramidal_like_count": pyramidal_like_count,
        "pyramidal_like_share": round(pyramidal_like_count / total, 4),
        "mean_horizontal_surface_ratio": mean("horizontal_surface_ratio"),
        "mean_vertical_surface_ratio": mean("vertical_surface_ratio"),
        "mean_sloped_surface_ratio": mean("sloped_surface_ratio"),
        "section_control_signature_count": len(control_signatures),
        "plan_family_counts": dict(sorted(plan_counts.items())),
        "ground_strategy_counts": dict(sorted(ground_strategy_counts.items())),
        "ground_strategy_count": len(ground_strategy_counts),
        "frontage_aligned_public_threshold_count": sum(
            bool(item["frontage_aligned_public_threshold"]) for item in descriptors
        ),
        "design_concept_key_count": len(concept_key_counts),
        "maximum_design_concept_key_repeat": max(concept_key_counts.values(), default=0),
        "missing_required_design_concept_count": sum(
            len(item["missing_required_design_concepts"]) for item in descriptors
        ),
        "mean_oriented_plan_aspect_ratio": mean("oriented_plan_aspect_ratio"),
        "mean_plan_compactness": mean("plan_compactness"),
        "mean_dominant_component_ratio": mean("dominant_component_ratio"),
        "mean_site_coverage_ratio": mean("site_coverage_ratio"),
        "mean_hierarchy_score": mean("hierarchy_score"),
        "mean_volume_count": round(sum(len(candidate.source.volumes) for candidate in selected) / total, 4),
        "mean_effective_surface_count": round(
            sum(int(candidate.source.signature().get("effective_surface_count") or 0) for candidate in selected) / total,
            4,
        ),
        "mean_body_rule_count": mean("body_rule_count"),
        "maximum_body_rule_count": max((int(item["body_rule_count"]) for item in descriptors), default=0),
        "mean_public_threshold_rule_count": mean("public_threshold_rule_count"),
        "body_rule_family_counts": dict(sorted(sum((Counter(item["body_rule_family_counts"]) for item in descriptors), Counter()).items())),
        "semantic_role_token_counts": dict(sorted(sum((Counter(item["semantic_role_tokens"]) for item in descriptors), Counter()).items())),
    }


def _order_portfolio_for_capacity_review(
    selected: list[_Candidate],
) -> list[_Candidate]:
    """Group the 5-column review board by yield band, then visual family."""
    capacity_rank = {
        "spatial_reserve": 0,
        "balanced_yield": 1,
        "brief_target": 2,
        "maximum_feasible": 3,
        "unclassified": 4,
    }
    return sorted(
        selected,
        key=lambda candidate: (
            capacity_rank.get(_capacity_alternative_key(candidate), 4),
            _solid_morphology_metrics(candidate)["phenotype"],
            _geometry_program_family(candidate),
            -float(candidate.score),
        ),
    )


def _cross_program_language_comparison(
    selected_by_program: dict[str, list[_Candidate]],
    metrics_by_program: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    slugs = tuple(selected_by_program)
    pairs: list[dict[str, Any]] = []
    for index, left_slug in enumerate(slugs):
        for right_slug in slugs[:index]:
            left = selected_by_program[left_slug]
            right = selected_by_program[right_slug]
            distances = [
                _silhouette_distance(left_candidate, right_candidate)
                for left_candidate in left
                for right_candidate in right
            ]
            left_sections = set(metrics_by_program[left_slug]["roof_section_family_counts"])
            right_sections = set(metrics_by_program[right_slug]["roof_section_family_counts"])
            union = left_sections | right_sections
            jaccard_distance = 1.0 - len(left_sections & right_sections) / max(1, len(union))
            pairs.append({
                "programs": [right_slug, left_slug],
                "mean_cross_program_silhouette_distance": round(sum(distances) / len(distances), 4) if distances else 0.0,
                "minimum_cross_program_silhouette_distance": round(min(distances), 4) if distances else 0.0,
                "roof_section_family_jaccard_distance": round(jaccard_distance, 4),
                "mean_plan_aspect_ratio_delta": round(abs(
                    metrics_by_program[left_slug]["mean_oriented_plan_aspect_ratio"]
                    - metrics_by_program[right_slug]["mean_oriented_plan_aspect_ratio"]
                ), 4),
                "mean_plan_compactness_delta": round(abs(
                    metrics_by_program[left_slug]["mean_plan_compactness"]
                    - metrics_by_program[right_slug]["mean_plan_compactness"]
                ), 4),
                "mean_dominant_ratio_delta": round(abs(
                    metrics_by_program[left_slug]["mean_dominant_component_ratio"]
                    - metrics_by_program[right_slug]["mean_dominant_component_ratio"]
                ), 4),
            })
    return {
        "schema_version": "arr.maas.cross_program_language_comparison.v1",
        "program_metrics": metrics_by_program,
        "pairwise_comparisons": pairs,
        "interpretation": "Measured geometry descriptors; visual review remains required.",
    }


def _hard_gate_count_summary(
    report: dict[str, Any] | None,
    candidates: list[_Candidate],
) -> dict[str, Any]:
    candidate_count = len(candidates)
    if report is None:
        return {"status": "not_run", "candidate_count": candidate_count}
    summary = {
        key: report[key]
        for key in (
            "candidate_count",
            "legal_hard_pass_count",
            "geometry_retention_pass_count",
            "parking_hard_pass_count",
            "combined_hard_pass_count",
            "mean_volume_retention",
            "minimum_volume_retention",
            "legal_failure_reason_counts",
            "geometry_failure_reason_counts",
            "parking_failure_reason_counts",
        )
    }
    by_scope: dict[str, dict[str, int]] = {}
    by_host_mode: Counter[str] = Counter()
    hard_pass_by_host_mode: Counter[str] = Counter()
    by_geometry_family: dict[str, dict[str, Any]] = {}
    by_geometry_genotype: dict[str, dict[str, Any]] = {}
    for candidate, row in zip(candidates, report["rows"]):
        scope = str(row.get("book_scope") or "1/1")
        bucket = by_scope.setdefault(scope, {
            "candidate_count": 0,
            "legal_hard_pass_count": 0,
            "geometry_retention_pass_count": 0,
            "parking_hard_pass_count": 0,
            "combined_hard_pass_count": 0,
        })
        bucket["candidate_count"] += 1
        bucket["legal_hard_pass_count"] += int(bool(row["legal_projection"]["hard_pass"]))
        bucket["geometry_retention_pass_count"] += int(bool(row["legal_projection"]["geometry_retention_pass"]))
        bucket["parking_hard_pass_count"] += int(bool(row["parking_hard_gate"]["hard_pass"]))
        bucket["combined_hard_pass_count"] += int(bool(row["combined_hard_pass"]))
        host_mode = str(row.get("generation_host_mode") or "horizontal_buildable_envelope")
        by_host_mode[host_mode] += 1
        if row["combined_hard_pass"]:
            hard_pass_by_host_mode[host_mode] += 1
        geometry_family = _geometry_program_family(candidate)
        if geometry_family:
            empty_bucket = lambda: {
                "candidate_count": 0,
                "geometry_retention_pass_count": 0,
                "combined_hard_pass_count": 0,
                "volume_retentions": [],
                "failure_reason_counts": Counter(),
            }
            for bucket in (
                by_geometry_family.setdefault(geometry_family, empty_bucket()),
                by_geometry_genotype.setdefault(_seed_family(candidate), empty_bucket()),
            ):
                bucket["candidate_count"] += 1
                bucket["geometry_retention_pass_count"] += int(bool(row["legal_projection"]["geometry_retention_pass"]))
                bucket["combined_hard_pass_count"] += int(bool(row["combined_hard_pass"]))
                bucket["volume_retentions"].append(float(row["legal_projection"].get("volume_retention") or 0.0))
                bucket["failure_reason_counts"].update(row["legal_projection"].get("geometry_failure_reasons") or ())
    summary["by_scope"] = dict(sorted(by_scope.items()))
    summary["candidate_count_by_generation_host"] = dict(sorted(by_host_mode.items()))
    summary["combined_hard_pass_by_generation_host"] = dict(sorted(hard_pass_by_host_mode.items()))
    def serialize_geometry_buckets(buckets: dict[str, dict[str, Any]]) -> dict[str, Any]:
        return {
        family: {
            "candidate_count": bucket["candidate_count"],
            "geometry_retention_pass_count": bucket["geometry_retention_pass_count"],
            "combined_hard_pass_count": bucket["combined_hard_pass_count"],
            "mean_volume_retention": round(sum(bucket["volume_retentions"]) / len(bucket["volume_retentions"]), 4),
            "minimum_volume_retention": round(min(bucket["volume_retentions"]), 4),
            "failure_reason_counts": dict(sorted(bucket["failure_reason_counts"].items())),
        }
        for family, bucket in sorted(buckets.items())
        }

    summary["by_recursive_geometry_family"] = serialize_geometry_buckets(by_geometry_family)
    summary["by_recursive_geometry_genotype"] = serialize_geometry_buckets(by_geometry_genotype)
    return summary


def run_book_program_portfolios(
    site: Polygon,
    *,
    pnu: str,
    output_dir: Path,
    site_origin_utm: tuple[float, float] = (0.0, 0.0),
    constraints: list[dict[str, Any]] | None = None,
    regulation_evidence: dict[str, Any] | None = None,
    sunlight_envelope: dict[str, Any] | None = None,
    parking_options: dict[str, Any] | None = None,
    program_slugs: tuple[str, ...] | None = None,
    recursive_only: bool = False,
    visual_directive_path: Path | None = None,
    outcome_graph_path: Path | None = None,
    site_boundary_source: str = "",
    site_access_context: dict[str, Any] | None = None,
    site_access_geometry: dict[str, Any] | None = None,
    live_geometry_vlm_revision: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    directive_dir = visual_directive_path.parent if visual_directive_path is not None else output_dir
    visual_directive_payload = _load_visual_directive(directive_dir, pnu)
    outcome_graph_path_was_explicit = outcome_graph_path is not None
    outcome_graph_path = outcome_graph_path or default_outcome_graph_path(pnu)
    outcome_graph_snapshot_path = output_dir / "maas-geometry-mutation-outcome-graph.json"
    outcome_graph = GeometryOutcomeGraph.load(outcome_graph_path, pnu=pnu)
    program_results: list[dict[str, Any]] = []
    selected_by_program: dict[str, list[_Candidate]] = {}
    metrics_by_program: dict[str, dict[str, Any]] = {}
    board_paths: list[Path] = []
    mass_brain_trace_sequences: list[VerbSequence] = []
    mass_brain_trace_features: dict[str, dict[str, Any]] = {}
    requested_slugs = set(program_slugs or ())
    for slug, building_type, height, floors in PROGRAMS:
        if requested_slugs and slug not in requested_slugs:
            continue
        started = perf_counter()
        outcome_graph.begin_program_run(slug)
        memory_visual_directive = outcome_graph.latest_portfolio_directive(slug)
        program_visual_directive = dict(
            (visual_directive_payload.get("programs") or {}).get(slug) or {}
        )
        # Plan topology is measured from the final footprint. Requesting a
        # triangular member has no effect when no valid triangular candidate
        # survives; when one does survive, the portfolio must not silently
        # discard the entire non-orthogonal plan language.
        program_visual_directive.setdefault("required_plan_families", ["triangular"])
        remembered_families = list(
            memory_visual_directive.get("required_geometry_program_families") or ()
        )
        if remembered_families:
            program_visual_directive["required_geometry_program_families"] = list(dict.fromkeys((
                *remembered_families,
                *(program_visual_directive.get("required_geometry_program_families") or ()),
            )))
        remembered_chassis = list(
            memory_visual_directive.get("required_chassis_families") or ()
        )
        if remembered_chassis:
            program_visual_directive["required_chassis_families"] = list(dict.fromkeys((
                *remembered_chassis,
                *(program_visual_directive.get("required_chassis_families") or ()),
            )))
        program_visual_directive["portfolio_memory_directive"] = memory_visual_directive
        remembered_family_caps = dict(
            memory_visual_directive.get("max_geometry_family_counts") or {}
        )
        if remembered_family_caps:
            program_visual_directive["max_geometry_family_counts"] = {
                **remembered_family_caps,
                **dict(program_visual_directive.get("max_geometry_family_counts") or {}),
            }
        remembered_chassis_caps = dict(
            memory_visual_directive.get("max_chassis_family_counts") or {}
        )
        if remembered_chassis_caps:
            program_visual_directive["max_chassis_family_counts"] = {
                **remembered_chassis_caps,
                **dict(program_visual_directive.get("max_chassis_family_counts") or {}),
            }
        remembered_chassis_cap = int(
            memory_visual_directive.get("max_chassis_family_count") or 0
        )
        if remembered_chassis_cap and not remembered_chassis_caps and not program_visual_directive.get(
            "max_chassis_family_count"
        ):
            program_visual_directive["max_chassis_family_count"] = remembered_chassis_cap
        runtime_live_vlm = bool(
            live_geometry_vlm_revision
            or program_visual_directive.get("live_geometry_vlm_revision")
        )
        typed_graph_mutations = program_visual_directive.get("typed_graph_mutations") or []
        geometry_program_mutations = program_visual_directive.get("geometry_program_mutations") or []
        synthesis_requests = program_visual_directive.get("geometry_synthesis_requests") or []
        if synthesis_requests:
            live_requested = runtime_live_vlm
            reference_matches = [
                {
                    "local_path": str(path),
                    "title": Path(str(path)).stem,
                    "selection_role": "operation_language_reference_not_shape_template",
                    "source": "portfolio_vlm_directive",
                }
                for path in visual_directive_payload.get("reference_images") or ()
            ]
            synthesis_requests = [
                {
                    **dict(request),
                    "live_vlm_revision": bool(request.get("live_vlm_revision", live_requested)),
                    "reference_matches": reference_matches,
                    "required_body_phenotypes": list(
                        program_visual_directive.get("required_solid_phenotypes") or ()
                    ),
                }
                for request in synthesis_requests
                if isinstance(request, dict)
            ]
        # The universal recursive form bank is the default dominant-form
        # authority.  Legacy program sequences are role/context carriers, not
        # selectable finished geometry.  Previously this flag became false
        # without an explicit session mutation even though _program_pool still
        # injected the universal bank; legacy candidates could then enter the
        # exact-AST VLM shortlist with no geometry_program nodes at all.
        geometry_program_authority = True
        generation_context = (
            build_legal_generation_context(
                site_local_utm=site,
                site_origin_utm=site_origin_utm,
                building_type=building_type,
                constraints=constraints,
                sunlight_envelope=sunlight_envelope,
            )
            if constraints is not None
            else None
        )
        generation_site = generation_context.generation_site if generation_context is not None else site
        dimensional_context = _program_dimensional_context(
            generation_site,
            building_type,
            height,
            floors,
        )
        if dimensional_context["status"] == "infeasible":
            empty_metrics = _portfolio_language_metrics([])
            board = output_dir / f"maas-book-{slug}-20.png"
            render_archive_sheet(
                [],
                board,
                title=f"MAAS BOOK × {building_type} · PNU {pnu} · PROGRAM INFEASIBLE",
            )
            board_paths.append(board)
            selected_by_program[slug] = []
            metrics_by_program[slug] = empty_metrics
            program_results.append({
                "program": building_type,
                "slug": slug,
                "status": "fail",
                "selected_count": 0,
                "book_operation_count": 0,
                "book_principle_kind_counts": {},
                "visual_language_count": 0,
                "book_base_volume_scope_count": 0,
                "book_base_volume_scopes": [],
                "near_duplicate_pair_count": 0,
                "program_language_metrics": empty_metrics,
                "program_dimensional_context": dimensional_context,
                "vlm_portfolio_directive": {
                    "active": bool(runtime_live_vlm or program_visual_directive),
                    "runtime_live_vlm_requested": runtime_live_vlm,
                },
                "downstream_hard_gate": {"status": "not_run", "candidate_count": 0},
                "counts": {},
                "failures": list(dimensional_context.get("failure_reasons") or ("program_dimensional_infeasible",)),
                "missing_vlm_required_roof_archetypes": [],
                "missing_required_solid_phenotypes": [],
                "duration_seconds": round(perf_counter() - started, 3),
                "rows": [],
                "png": str(board),
            })
            continue
        height = float(dimensional_context["effective_height_m"])
        floors = int(dimensional_context["effective_floors"])
        capacity_policy = resolve_massing_capacity_policy(
            building_type=building_type,
            site_area_m2=float(site.area),
            parking_options=parking_options,
        )
        base_capacity_contract = (
            build_feasible_capacity_contract(
                generation_context,
                site_local_utm=site,
                height_m=height,
                floors=floors,
                target_utilization=float(capacity_policy["target_far_utilization"]),
                minimum_utilization=float(capacity_policy["min_far_utilization"]),
            )
            if generation_context is not None
            else None
        )
        pool, counts = _program_pool(
            generation_site,
            building_type,
            height,
            floors,
            generation_context=generation_context,
            typed_graph_mutations=typed_graph_mutations,
            geometry_program_mutations=geometry_program_mutations,
            synthesis_requests=synthesis_requests,
            outcome_graph=outcome_graph,
            recursive_only=geometry_program_authority,
            program_dimensional_context=dimensional_context,
            site_boundary_source=site_boundary_source,
            site_access_context=site_access_context,
            site_access_geometry=site_access_geometry,
            live_geometry_vlm_revision=runtime_live_vlm,
            base_capacity_contract=base_capacity_contract,
            capacity_site=site,
        )
        counts["program_dimensional_context"] = deepcopy(dimensional_context)
        counts["capacity_policy"] = deepcopy(capacity_policy)
        counts["base_capacity_contract"] = deepcopy(base_capacity_contract or {})
        # The base is a causal visual parent, not necessarily a final legal or
        # parking solution. Review that parent after program/clean gates, then
        # release its exact descendants and apply downstream hard gates to
        # each released candidate. Reversing this order deleted a legal,
        # parking-valid split+shift descendant merely because its unshifted
        # visual parent could not itself lay out parking.
        if runtime_live_vlm:
            downstream_evaluation_pool, base_stage_vlm_gate = audit_book_base_stage_with_vlm(
                pool,
                building_type=building_type,
                output_dir=output_dir / slug / "book-base-stage",
                visual_directive=program_visual_directive,
                outcome_graph=outcome_graph,
                program_slug=slug,
            )
        else:
            downstream_evaluation_pool = pool
            base_stage_vlm_gate = {
                "schema_version": "arr.maas.book_base_stage_vlm_gate.v1",
                "required": False,
                "status": "not_requested",
                "input_count": len(pool),
            }
        preselection_hard_gate = None
        selection_pool = downstream_evaluation_pool
        if generation_context is not None:
            preselection_hard_gate = evaluate_accepted_sources_downstream(
                downstream_evaluation_pool,
                site_local_utm=site,
                site_origin_utm=site_origin_utm,
                pnu=pnu,
                building_type=building_type,
                height_m=height,
                floors=floors,
                constraints=constraints,
                regulation_evidence=regulation_evidence or {},
                sunlight_envelope=sunlight_envelope,
                parking_options=parking_options,
                generation_context=generation_context,
            )
            selection_pool = [
                candidate
                for candidate, row in zip(downstream_evaluation_pool, preselection_hard_gate["rows"])
                if row["combined_hard_pass"]
            ]
        counts["preselection_hard_gate"] = _hard_gate_count_summary(
            preselection_hard_gate,
            downstream_evaluation_pool,
        )
        counts["geometry_program_authority"] = {
            "required": geometry_program_authority,
            "reason": (
                "recursive_only_flag"
                if recursive_only
                else (
                    "geometry_synthesis_request"
                    if synthesis_requests
                    else (
                        "geometry_program_mutation"
                        if geometry_program_mutations
                        else "universal_form_bank_default"
                    )
                )
            ),
            "legacy_geometry_final_selection_allowed": False,
        }
        # The default dominant-form supply is now the universal bank. Program
        # evidence and BOOK projection exist before the live critic sees a
        # candidate; no program-conditioned VLM authors the base/chassis lane.
        # Explicit session directives remain additive feedback only.
        live_vlm_selection_required = False
        pre_vlm_selection_count = len(selection_pool)
        pre_book_reviewed_count = sum(
            _vlm_reviewed_program_candidate(candidate)
            for candidate in selection_pool
        )
        counts["vlm_final_selection_gate"] = {
            "required": False,
            "role": "post_program_exact_book_critic",
            "universal_form_bank_precedes_program_and_vlm": True,
            "input_count": pre_vlm_selection_count,
            "legacy_prebook_reviewed_program_fit_pass_count": pre_book_reviewed_count,
            "universal_control_count": pre_vlm_selection_count - pre_book_reviewed_count,
            "universal_control_retained_for_exact_post_book_review": True,
            "exact_post_book_vlm_is_final_selection_authority": bool(runtime_live_vlm),
        }
        counts["book_base_stage_vlm_gate"] = base_stage_vlm_gate
        degenerate_sheet_count = sum(
            bool(_solid_morphology_metrics(candidate)["degenerate_sheet_like"])
            for candidate in selection_pool
        )
        selection_pool = [
            candidate for candidate in selection_pool
            if not _solid_morphology_metrics(candidate)["degenerate_sheet_like"]
        ]
        raw_selection_pool_count = len(selection_pool)
        selection_pool = _bounded_visual_selection_pool(selection_pool)
        counts["visual_selection_pool"] = {
            "input_count": raw_selection_pool_count,
            "bounded_count": len(selection_pool),
            "quality_diversity_archive": qd_archive_evidence(selection_pool),
            "degenerate_sheet_like_rejected_count": degenerate_sheet_count,
            "measured_solid_phenotype_counts": dict(sorted(Counter(
                _solid_morphology_metrics(candidate)["phenotype"]
                for candidate in selection_pool
            ).items())),
            "measured_wedge_like_count": sum(
                bool(_solid_morphology_metrics(candidate)["wedge_like"])
                for candidate in selection_pool
            ),
            "measured_pyramidal_like_count": sum(
                bool(_solid_morphology_metrics(candidate)["pyramidal_like"])
                for candidate in selection_pool
            ),
        }
        pre_final_book_vlm_pool = list(selection_pool)
        if runtime_live_vlm:
            initial_cycle = run_final_vlm_cycle(
                pre_final_book_vlm_pool,
                retained_hard_passes=[],
                building_type=building_type,
                output_dir=output_dir / slug,
                visual_directive=program_visual_directive,
                outcome_graph=outcome_graph,
                program_slug=slug,
                generation_site=generation_site,
                height=height,
                floors=floors,
                generation_context=generation_context,
                program_dimensional_context=dimensional_context,
                site_boundary_source=site_boundary_source,
                site_access_context=site_access_context,
                site_access_geometry=site_access_geometry,
                base_capacity_contract=base_capacity_contract,
                downstream_context={
                    "site_local_utm": site,
                    "site_origin_utm": site_origin_utm,
                    "pnu": pnu,
                    "building_type": building_type,
                    "height_m": height,
                    "floors": floors,
                    "constraints": constraints,
                    "regulation_evidence": regulation_evidence or {},
                    "sunlight_envelope": sunlight_envelope,
                    "parking_options": parking_options,
                    "generation_context": generation_context,
                },
                hard_gate_summary=_hard_gate_count_summary,
                completion_status="exact_typed_repair_cycle_complete",
                no_repair_status="no_downstream_hard_pass_repair_candidates",
            )
            selection_pool = initial_cycle.selection_pool
            counts["initial_final_book_vlm_gate"] = initial_cycle.initial_vlm_gate
            counts["exact_post_book_typed_repair"] = initial_cycle.repair_evidence
            final_book_vlm_gate = initial_cycle.final_vlm_gate
        else:
            final_book_vlm_gate = {
                "schema_version": "arr.maas.final_book_vlm_portfolio_gate.v1",
                "required": False,
                "status": "not_requested",
                "input_count": len(selection_pool),
                "post_book_geometry_reviewed": False,
            }
        counts["final_book_vlm_gate"] = final_book_vlm_gate
        selection_trace: dict[str, Any] = {}
        selected = _select(
            selection_pool,
            20,
            visual_directive=program_visual_directive,
            selection_trace=selection_trace,
        )
        outcome_graph.observe_candidates(
            program_slug=slug,
            candidates=downstream_evaluation_pool,
            downstream_report=preselection_hard_gate,
            selected=selected,
        )
        initial_selected_snapshot = list(selected)
        initial_selected_fingerprints = {
            _fingerprint(candidate) for candidate in initial_selected_snapshot
        }
        missing_scope = len({_scope_key(candidate) for candidate in selected}) < len(BASE_VOLUME_FRACTIONS)
        replenishment_cycles: list[dict[str, Any]] = []
        if len(selected) < 20 or missing_scope:
            excluded_parent_keys = set(base_stage_vlm_gate.get("reviewed_parent_keys") or ())
            excluded_parent_fingerprints = set(
                base_stage_vlm_gate.get("reviewed_parent_fingerprints") or ()
            )
            stop_reason = "cycle_budget_exhausted"
            cycle_budget = replenishment_cycle_budget_for_run(
                live_vlm=runtime_live_vlm,
            )
            downstream_context = {
                "site_local_utm": site,
                "site_origin_utm": site_origin_utm,
                "pnu": pnu,
                "building_type": building_type,
                "height_m": height,
                "floors": floors,
                "constraints": constraints,
                "regulation_evidence": regulation_evidence or {},
                "sunlight_envelope": sunlight_envelope,
                "parking_options": parking_options,
                "generation_context": generation_context,
            }
            # The exact initial observations are already persisted in the
            # run-local outcome graph. Retaining the full compiled pool here
            # kept hundreds of heavyweight meshes alive across all later
            # cycles. Only the bounded QD archive and the at-most-20 initial
            # selected candidates are needed to refresh final selection flags.
            pool = []
            downstream_evaluation_pool = []
            for cycle_index in range(1, cycle_budget + 1):
                previous_pool_count = len(selection_pool)
                cycle = run_replenishment_cycle(
                    cycle_index=cycle_index,
                    parent_variant_index=cycle_index,
                    retained_selection_pool=selection_pool,
                    excluded_parent_keys=excluded_parent_keys,
                    excluded_parent_fingerprints=excluded_parent_fingerprints,
                    generation_site=generation_site,
                    building_type=building_type,
                    height=height,
                    floors=floors,
                    generation_context=generation_context,
                    typed_graph_mutations=typed_graph_mutations,
                    geometry_program_mutations=geometry_program_mutations,
                    synthesis_requests=synthesis_requests,
                    outcome_graph=outcome_graph,
                    recursive_only=geometry_program_authority,
                    program_dimensional_context=dimensional_context,
                    site_boundary_source=site_boundary_source,
                    site_access_context=site_access_context,
                    site_access_geometry=site_access_geometry,
                    runtime_live_vlm=runtime_live_vlm,
                    live_vlm_selection_required=live_vlm_selection_required,
                    base_capacity_contract=base_capacity_contract,
                    capacity_site=site,
                    output_dir=output_dir / slug,
                    program_slug=slug,
                    visual_directive=program_visual_directive,
                    downstream_context=downstream_context,
                    hard_gate_summary=_hard_gate_count_summary,
                )
                selection_pool = cycle.selection_pool
                excluded_parent_keys.update(cycle.reviewed_parent_keys)
                excluded_parent_fingerprints.update(cycle.reviewed_parent_fingerprints)
                selection_trace = {}
                selected = _select(
                    selection_pool,
                    20,
                    visual_directive=program_visual_directive,
                    selection_trace=selection_trace,
                )
                pool_growth = len(selection_pool) - previous_pool_count
                cycle_evidence = {
                    **cycle.evidence,
                    "selection_pool_count_before": previous_pool_count,
                    "selection_pool_count_after": len(selection_pool),
                    "selection_pool_growth": pool_growth,
                    "selected_count_after": len(selected),
                    "selection_capacity_diagnostics": _selection_capacity_diagnostics(
                        selection_pool,
                        selected,
                        target=20,
                        visual_directive=program_visual_directive,
                    ),
                }
                replenishment_cycles.append(cycle_evidence)
                if runtime_live_vlm and cycle.evidence.get("final_book_vlm_gate"):
                    counts["final_book_vlm_gate"] = cycle.evidence["final_book_vlm_gate"]
                outcome_graph.observe_candidates(
                    program_slug=slug,
                    candidates=cycle.downstream_evaluation_pool,
                    downstream_report=cycle.downstream_report,
                    selected=selected,
                )
                missing_scope = (
                    len({_scope_key(candidate) for candidate in selected})
                    < len(BASE_VOLUME_FRACTIONS)
                )
                terminal_reason = replenishment_stop_reason(
                    selected_count=len(selected),
                    selected_scope_count=len({_scope_key(candidate) for candidate in selected}),
                    target_count=20,
                    required_scope_count=len(BASE_VOLUME_FRACTIONS),
                    cycles_run=cycle_index,
                    cycle_budget=cycle_budget,
                )
                del cycle
                if terminal_reason:
                    stop_reason = terminal_reason
                    break
            if replenishment_cycles:
                counts["bounded_parent_replenishment"] = {
                    **replenishment_cycles[-1],
                    "schema_version": "arr.maas.bounded_parent_replenishment.v2",
                    "cycle_budget": cycle_budget,
                    "cycle_count": len(replenishment_cycles),
                    "cycles": replenishment_cycles,
                    "stop_reason": stop_reason,
                }
            # The final selection can displace a first-pass incumbent. Update
            # observation flags instead of leaving stale selected=true memory.
            outcome_graph.observe_candidates(
                program_slug=slug,
                candidates=[
                    *initial_selected_snapshot,
                    *(
                        candidate for candidate in selected
                        if _fingerprint(candidate) not in initial_selected_fingerprints
                    ),
                ],
                downstream_report=None,
                selected=selected,
            )
        counts["final_hard_pass_selection_pool_count"] = len(selection_pool)
        counts["selection_trace"] = selection_trace
        counts["selection_capacity_diagnostics"] = _selection_capacity_diagnostics(
            selection_pool,
            selected,
            target=20,
            visual_directive=program_visual_directive,
        )
        selected = _order_portfolio_for_capacity_review(selected)
        selected_by_program[slug] = selected
        language_metrics = _portfolio_language_metrics(selected)
        metrics_by_program[slug] = language_metrics
        downstream_hard_gate = (
            evaluate_accepted_sources_downstream(
                selected,
                site_local_utm=site,
                site_origin_utm=site_origin_utm,
                pnu=pnu,
                building_type=building_type,
                height_m=height,
                floors=floors,
                constraints=constraints,
                regulation_evidence=regulation_evidence or {},
                sunlight_envelope=sunlight_envelope,
                parking_options=parking_options,
                generation_context=generation_context,
            )
            if constraints is not None
            else {
                "schema_version": "arr.maas.book_downstream_hard_gate.v1",
                "status": "not_run",
                "same_accepted_source": True,
                "candidate_count": len(selected),
            }
        )
        features: list[dict[str, Any]] = []
        rows: list[dict[str, Any]] = []
        downstream_rows = (
            list(downstream_hard_gate.get("rows") or ())
            if isinstance(downstream_hard_gate, dict)
            else []
        )
        for index, candidate in enumerate(selected):
            feature = deepcopy(candidate.feature)
            props = feature["properties"]
            props["archive_variant_id"] = props["variant_id"]
            props["variant_id"] = f"maas_{index + 1:02d}"
            props["mass_shape"] = candidate.operation
            props["review_status"] = "accept"
            props["review_reasons"] = ["program hard pass", "clean mass pass"]
            if runtime_live_vlm:
                props["review_reasons"].append("exact post-BOOK VLM hard pass")
            features.append(feature)
            signature = candidate.source.signature()
            descriptor = _candidate_language_descriptor(candidate)
            rows.append({
                "variant_id": props["variant_id"],
                "source_sequence": candidate.sequence.name,
                "book_operation": candidate.operation,
                "book_principle_id": candidate.principle_id,
                "book_principle_kind": candidate.principle_kind,
                "book_scope": candidate.source.metadata.get("program_book_projection_evidence", {}).get("scope", {}),
                "capacity_alternative": deepcopy(
                    candidate.source.metadata.get("capacity_alternative_projection") or {}
                ),
                "score": candidate.score,
                "volume_count": len(candidate.source.volumes),
                "surface_count": int(signature.get("effective_surface_count") or signature.get("surface_count") or 0),
                "inside_site": _inside_site(candidate.source, generation_site),
                "generation_host_mode": str((
                    candidate.source.metadata.get("legal_generation_context_evidence") or {}
                ).get("generation_host_mode") or "unconstrained_site"),
                "legal_generation_context_evidence": deepcopy(
                    candidate.source.metadata.get("legal_generation_context_evidence") or {}
                ),
                "program_hard_pass": bool(props["program_massing_evidence"]["hard_pass"]),
                "vlm_geometry_critic_active": bool(
                    _geometry_program_metadata(candidate).get("vlm_geometry_critic_active")
                ),
                "vlm_program_fit_hard_pass": bool(
                    _geometry_program_metadata(candidate).get("vlm_program_fit_hard_pass")
                ),
                "vlm_critic_score": _geometry_program_metadata(candidate).get("vlm_critic_score"),
                "vlm_program_appropriateness": _geometry_program_metadata(candidate).get("vlm_program_appropriateness"),
                "vlm_section_program_fit": _geometry_program_metadata(candidate).get("vlm_section_program_fit"),
                "final_book_vlm_audit": deepcopy(
                    candidate.source.metadata.get("final_book_vlm_audit") or {}
                ),
                "seed_family": descriptor["seed_family"],
                "roof_section_family": descriptor["section_family"],
                "roof_archetype": descriptor["roof_archetype"],
                "chassis_family": descriptor["chassis_family"],
                "solid_phenotype": descriptor["solid_phenotype"],
                "body_phenotype": descriptor["body_phenotype"],
                "section_phenotype": descriptor["section_phenotype"],
                "wedge_like": descriptor["wedge_like"],
                "pyramidal_like": descriptor["pyramidal_like"],
                "collapsed_profiled_tent_like": descriptor["collapsed_profiled_tent_like"],
                "degenerate_sheet_like": descriptor["degenerate_sheet_like"],
                "horizontal_surface_ratio": descriptor["horizontal_surface_ratio"],
                "vertical_surface_ratio": descriptor["vertical_surface_ratio"],
                "sloped_surface_ratio": descriptor["sloped_surface_ratio"],
                "normal_direction_bin_count": descriptor["normal_direction_bin_count"],
                "horizontal_level_count": descriptor["horizontal_level_count"],
                "plan_convexity": descriptor["plan_convexity"],
                "upper_area_ratio": descriptor["upper_area_ratio"],
                "solid_genus": descriptor["solid_genus"],
                "solid_component_count": descriptor["solid_component_count"],
                "oriented_plan_aspect_ratio": descriptor["oriented_plan_aspect_ratio"],
                "plan_compactness": descriptor["plan_compactness"],
                "plan_family": descriptor["plan_family"],
                "dominant_component_ratio": descriptor["dominant_component_ratio"],
                "site_coverage_ratio": descriptor["site_coverage_ratio"],
                "hierarchy_score": descriptor["hierarchy_score"],
                "section_control_signature": descriptor["section_control_signature"],
                "semantic_role_tokens": descriptor["semantic_role_tokens"],
                "body_rule_count": descriptor["body_rule_count"],
                "program_body_rule_count": descriptor["program_body_rule_count"],
                "public_threshold_rule_count": descriptor["public_threshold_rule_count"],
                "book_body_rule_count": descriptor["book_body_rule_count"],
                "body_rule_family_counts": descriptor["body_rule_family_counts"],
                "body_rules": descriptor["body_rules"],
                "design_concept": descriptor["design_concept"],
                "design_concept_key": descriptor["design_concept_key"],
                "ground_strategy": descriptor["ground_strategy"],
                "frontage_aligned_public_threshold": descriptor["frontage_aligned_public_threshold"],
                "missing_required_design_concepts": descriptor["missing_required_design_concepts"],
                "measured_clear_span_m": descriptor["measured_clear_span_m"],
                "measured_solid_height_m": descriptor["measured_solid_height_m"],
                "height_to_clear_span_ratio": descriptor["height_to_clear_span_ratio"],
                "capacity_alternative_id": descriptor["capacity_alternative_id"],
                "capacity_target_utilization": descriptor["capacity_target_utilization"],
                "capacity_achieved_utilization": descriptor["capacity_achieved_utilization"],
                "capacity_target_hard_pass": descriptor["capacity_target_hard_pass"],
                "far_pct": descriptor["far_pct"],
            })
            downstream_row = (
                downstream_rows[index]
                if index < len(downstream_rows) and isinstance(downstream_rows[index], dict)
                else {}
            )
            compilation = deepcopy(
                candidate.source.metadata.get("geometry_program_compilation") or {}
            )
            bridge = deepcopy(
                candidate.source.metadata.get("geometry_program_bridge_evidence") or {}
            )
            program_payload = deepcopy(
                candidate.source.metadata.get("geometry_program") or {}
            )
            graph_snapshot = deepcopy(
                candidate.source.metadata.get("geometry_graph_snapshot") or {}
            )
            props["geometry_program_compilation"] = compilation
            trace_name = f"{slug}__{index + 1:02d}__{candidate.sequence.name}"
            trace_sequence = VerbSequence(
                name=trace_name,
                label=f"{slug} {index + 1:02d} {candidate.sequence.label or candidate.sequence.name}",
                calls=candidate.sequence.calls,
                notes=tuple(candidate.sequence.notes) + (
                    "trace_source=exact_final_selected_geometry",
                    "selection_effect=none_shadow_only",
                ),
            )
            hard_gates = {
                "program": {
                    "hard_pass": bool(props.get("program_massing_evidence", {}).get("hard_pass")),
                    "evidence": deepcopy(props.get("program_massing_evidence") or {}),
                },
                "cleanMass": {
                    "hard_pass": True,
                    "visibleVolumeCount": len(candidate.source.volumes),
                    "effectiveSurfaceCount": int(
                        candidate.source.signature().get("effective_surface_count")
                        or candidate.source.signature().get("surface_count")
                        or 0
                    ),
                    "coherence": deepcopy(
                        (props.get("source_signature") or {}).get("coherence_evidence") or {}
                    ),
                },
                "legal": deepcopy(downstream_row.get("legal_projection") or {}),
                "parking": deepcopy(downstream_row.get("parking_hard_gate") or {}),
                "originalMetrics": deepcopy(downstream_row.get("original_metrics") or {}),
                "projectedMetrics": deepcopy(downstream_row.get("projected_metrics") or {}),
                "combinedHardPass": bool(downstream_row.get("combined_hard_pass")),
            }
            mass_execution_passport = selected_candidate_execution_passport(
                compilation=compilation,
                downstream_row=downstream_row,
                source_metadata=candidate.source.metadata,
                program_evidence=props.get("program_massing_evidence") or {},
                descriptor=descriptor,
                pnu=pnu,
            )
            props["mass_execution_passport"] = mass_execution_passport
            props["geometry_artifact"] = {
                "schemaVersion": "arr.maas.geometry_artifact.v1",
                "authority": "arr_recursive_geometry_program",
                "programType": slug,
                "programLabel": building_type,
                "sourceSequence": candidate.sequence.name,
                "bookPrincipleId": candidate.principle_id,
                "bookScope": _scope_key(candidate),
                "capacityAlternative": deepcopy(
                    candidate.source.metadata.get("capacity_alternative_projection") or {}
                ),
                "geometryProgram": program_payload,
                "geometryGraphSnapshot": graph_snapshot,
                "programRelationEvidence": deepcopy(
                    candidate.source.metadata.get("program_component_relation_evidence") or {}
                ),
                "compilation": compilation,
                "identity": {
                    "programHash": str(
                        compilation.get("program_hash")
                        or bridge.get("program_hash")
                        or ""
                    ),
                    "geometryHash": str(
                        compilation.get("geometry_hash")
                        or bridge.get("geometry_hash")
                        or ""
                    ),
                },
                "vlmAudit": deepcopy(
                    candidate.source.metadata.get("final_book_vlm_audit") or {}
                ),
                "hardGates": hard_gates,
                "executionPassport": mass_execution_passport,
                "selectionEffect": "none_shadow_only",
            }
            mass_brain_trace_sequences.append(trace_sequence)
            mass_brain_trace_features[trace_name] = feature
        board = output_dir / f"maas-book-{slug}-20.png"
        render_archive_sheet(
            features,
            board,
            title=f"MAAS BOOK × {building_type} · PNU {pnu} · {len(features)}/20 silhouette-distinct masses",
        )
        render_evidence = _archive_render_evidence(board, len(features))
        for row, evidence in zip(rows, render_evidence):
            row["archive_render_evidence"] = evidence
        outcome_graph.observe_portfolio_render(
            program_slug=slug,
            candidates=selected,
            board_path=board,
            render_evidence=render_evidence,
        )
        board_paths.append(board)
        if runtime_live_vlm and selected:
            try:
                portfolio_vlm_audit = score_portfolio_board_with_openai_vlm(
                    image_path=board,
                    program_context={
                        **program_reference_contract(building_type),
                        "site_access_side_in_program_frame": _site_access_side_in_principal_frame(
                            generation_site,
                            site_access_geometry,
                        ),
                    },
                    candidate_summaries=[{
                        "candidate_id": row["variant_id"],
                        "book_scope": str((row.get("book_scope") or {}).get("base_volume_label") or ""),
                        "capacity_alternative_id": row.get("capacity_alternative_id"),
                        "capacity_target_utilization": row.get("capacity_target_utilization"),
                        "capacity_achieved_utilization": row.get("capacity_achieved_utilization"),
                        "base_seed": str((row.get("design_concept") or {}).get("base_seed") or ""),
                        "body_phenotype": row.get("body_phenotype"),
                        "roof_archetype": row.get("roof_archetype"),
                        "ground_strategy": row.get("ground_strategy"),
                        "design_concept_key": row.get("design_concept_key"),
                        "geometry_family": _geometry_program_family(candidate),
                        "form_bank_lane": _geometry_program_metadata(candidate).get("form_bank_lane"),
                        "chassis_family": row.get("chassis_family"),
                    } for row, candidate in zip(rows, selected)],
                )
                portfolio_vlm_audit = enrich_portfolio_vlm_feedback(
                    portfolio_vlm_audit,
                    rows=rows,
                    candidates=selected,
                )
            except Exception as exc:
                portfolio_vlm_audit = {
                    "schema_version": "arr.maas.portfolio_visual_audit.v1",
                    "status": "call_failed",
                    "hard_pass": False,
                    "candidate_count": len(selected),
                    "failure_reasons": ["portfolio_vlm_call_failed"],
                    "error": f"{type(exc).__name__}:{str(exc)[:240]}",
                    "legal_or_parking_score": False,
                }
            outcome_graph.observe_portfolio_vlm_audit(
                program_slug=slug,
                candidate_geometry_hashes=[
                    str((candidate.source.metadata.get("geometry_program_bridge_evidence") or {}).get("geometry_hash") or "")
                    for candidate in selected
                ],
                audit=portfolio_vlm_audit,
            )
        else:
            portfolio_vlm_audit = {
                "schema_version": "arr.maas.portfolio_visual_audit.v1",
                "status": "not_requested" if not runtime_live_vlm else "no_selected_candidates",
                # Not evaluated is not a visual approval.  Overall non-live
                # diagnostics remain governed by their numeric gates, while
                # this field now reports the VLM state truthfully.
                "hard_pass": False,
                "evaluated": False,
                "candidate_count": len(selected),
                "legal_or_parking_score": False,
            }
        counts["portfolio_vlm_audit"] = deepcopy(portfolio_vlm_audit)
        near_duplicates = sum(
            1
            for index, left in enumerate(selected)
            for right in selected[:index]
            if _silhouette_distance(left, right) < 0.10
        )
        failures = []
        if runtime_live_vlm and not portfolio_vlm_audit.get("hard_pass"):
            failures.append("portfolio_vlm_visual_diversity_hard_gate_failed")
        if len(selected) != 20:
            failures.append("selected_count_below_20")
        operation_count = len({candidate.principle_id for candidate in selected})
        if operation_count < 10:
            failures.append("book_operation_count_below_10")
        selectable_universe, _measured_capacity_universe = (
            _target_hard_pass_universe(selection_pool)
        )
        available_principle_kinds = {
            candidate.principle_kind for candidate in selectable_universe
        }
        selected_principle_kinds = {
            candidate.principle_kind for candidate in selected
        }
        if not available_principle_kinds.issubset(selected_principle_kinds):
            failures.append("available_book_principle_kind_missing_from_portfolio")
        visual_languages: list[_Candidate] = []
        for candidate in selected:
            if all(_silhouette_distance(candidate, representative) >= 0.16 for representative in visual_languages):
                visual_languages.append(candidate)
        if len(visual_languages) < 10:
            failures.append("visual_language_count_below_10")
        scope_count = len({_scope_key(candidate) for candidate in selected})
        if scope_count < len(BASE_VOLUME_FRACTIONS):
            failures.append("book_base_volume_scope_count_below_6")
        available_capacity_alternatives = {
            _capacity_alternative_key(candidate)
            for candidate in selectable_universe
            if _capacity_alternative_key(candidate) != "unclassified"
        }
        selected_capacity_alternatives = {
            _capacity_alternative_key(candidate)
            for candidate in selected
            if _capacity_alternative_key(candidate) != "unclassified"
        }
        if not available_capacity_alternatives.issubset(selected_capacity_alternatives):
            failures.append("available_capacity_alternative_missing_from_portfolio")
        if any(
            not bool((candidate.source.metadata.get("capacity_alternative_projection") or {}).get("target_hard_pass"))
            for candidate in selected
            if _capacity_alternative_key(candidate) != "unclassified"
        ):
            failures.append("capacity_alternative_target_miss_in_selected_portfolio")
        if any(not row["inside_site"] or not row["program_hard_pass"] for row in rows):
            failures.append("hard_gate_failure_in_selected_portfolio")
        if len(render_evidence) != len(features) or any(
            not item.get("hard_pass") for item in render_evidence
        ):
            failures.append("accepted_mass_not_visible_in_archive_render")
        if language_metrics["dominant_seed_family_share"] > 0.40:
            failures.append("repeated_seed_footprint_family_above_40_percent")
        if language_metrics["dominant_roof_section_family_share"] > 0.50:
            failures.append("repeated_roof_section_family_above_50_percent")
        if (
            language_metrics["roof_archetype_count"] > 1
            and language_metrics["dominant_roof_archetype_share"] > 0.30
        ):
            failures.append("repeated_roof_archetype_above_30_percent")
        missing_required_roofs = sorted(
            set(program_visual_directive.get("required_roof_archetypes") or ())
            - set(language_metrics["roof_archetype_counts"])
        )
        if missing_required_roofs:
            failures.append("vlm_required_roof_archetype_missing")
        required_phenotypes = set(program_visual_directive.get("required_solid_phenotypes") or ())
        missing_required_phenotypes = sorted(
            required_phenotypes - set(language_metrics["solid_phenotype_counts"])
        )
        if missing_required_phenotypes:
            failures.append("required_solid_phenotype_missing")
        wedge_cap = int(program_visual_directive.get("max_wedge_like_count", max(3, len(selected) // 5)))
        if language_metrics["wedge_like_count"] > wedge_cap:
            failures.append("wedge_like_count_above_measured_cap")
        pyramidal_cap = int(program_visual_directive.get("max_pyramidal_like_count", 2))
        if language_metrics["pyramidal_like_count"] > pyramidal_cap:
            failures.append("pyramidal_like_count_above_measured_cap")
        selection_caps = (
            (counts.get("selection_capacity_diagnostics") or {}).get("caps")
            if isinstance(counts.get("selection_capacity_diagnostics"), dict)
            else {}
        ) or {}
        # The final assertion must use the same measured cap as the selector.
        # Previously selection intentionally admitted five examples of one
        # broad phenotype, then the summary silently defaulted to four and
        # marked that identical portfolio failed. This aligns two hard gates;
        # it does not admit a candidate the selector rejected.
        phenotype_cap = int(program_visual_directive.get(
            "max_solid_phenotype_count",
            int(selection_caps.get("solid_phenotype") or max(4, len(selected) // 4)),
        ))
        if max(language_metrics["solid_phenotype_counts"].values(), default=0) > phenotype_cap:
            failures.append("solid_phenotype_count_above_measured_cap")
        if language_metrics["ground_strategy_count"] < 3:
            failures.append("ground_strategy_count_below_3")
        if (
            site_access_geometry
            and language_metrics["frontage_aligned_public_threshold_count"] < 1
        ):
            failures.append("frontage_aligned_public_threshold_missing")
        if language_metrics["maximum_design_concept_key_repeat"] > 2:
            failures.append("design_concept_key_repeated_above_2")
        if language_metrics["missing_required_design_concept_count"]:
            failures.append("required_design_concept_controller_missing")
        program_results.append({
            "program": building_type,
            "slug": slug,
            "status": "pass" if not failures else "fail",
            "selected_count": len(selected),
            "book_operation_count": operation_count,
            "book_principle_kind_counts": {
                kind: sum(candidate.principle_kind == kind for candidate in selected)
                for kind in ("base_operative", "combination", "aggregation", "case_study")
            },
            "visual_language_count": len(visual_languages),
            "book_base_volume_scope_count": scope_count,
            "book_base_volume_scopes": sorted({_scope_key(candidate) for candidate in selected}),
            "capacity_alternative_count": len(selected_capacity_alternatives),
            "capacity_alternatives": sorted(selected_capacity_alternatives),
            "near_duplicate_pair_count": near_duplicates,
            "portfolio_vlm_audit": deepcopy(portfolio_vlm_audit),
            "archive_render_evidence": {
                "card_count": len(render_evidence),
                "visible_mass_card_count": sum(bool(item.get("hard_pass")) for item in render_evidence),
                "minimum_rendered_mass_pixel_ratio": round(min(
                    (float(item.get("rendered_mass_pixel_ratio") or 0.0) for item in render_evidence),
                    default=0.0,
                ), 5),
                "direct_png_review_required": True,
            },
            "program_language_metrics": language_metrics,
            "program_dimensional_context": dimensional_context,
            "vlm_portfolio_directive": {
                "active": bool(runtime_live_vlm or program_visual_directive),
                "provider": (
                    visual_directive_payload.get("provider")
                    if program_visual_directive
                    else ("openai_program_conditioned_vlm" if runtime_live_vlm else None)
                ),
                "runtime_live_vlm_requested": runtime_live_vlm,
                "typed_graph_mutation_count": len(typed_graph_mutations),
                "geometry_synthesis_request_count": int(counts.get("geometry_synthesis_request_count") or 0),
                "geometry_synthesis_request_source": counts.get("geometry_synthesis_request_source"),
                "geometry_program_llm_author_status_counts": counts.get("geometry_program_llm_author_status_counts") or {},
                "geometry_program_llm_author_active_seed_count": int(
                    counts.get("geometry_program_llm_author_active_seed_count") or 0
                ),
                "geometry_program_prebook_vlm_quarantined_seed_count": int(
                    counts.get("geometry_program_prebook_vlm_quarantined_seed_count") or 0
                ),
                "geometry_program_vlm_status_counts": counts.get("geometry_program_vlm_status_counts") or {},
                "geometry_program_vlm_causal_trace": counts.get("geometry_program_vlm_causal_trace") or {},
                "required_roof_archetypes": list(program_visual_directive.get("required_roof_archetypes") or ()),
                "required_solid_phenotypes": list(program_visual_directive.get("required_solid_phenotypes") or ()),
                "required_geometry_program_families": list(
                    program_visual_directive.get("required_geometry_program_families") or ()
                ),
                "required_chassis_families": list(
                    program_visual_directive.get("required_chassis_families") or ()
                ),
                "portfolio_memory_directive": deepcopy(memory_visual_directive),
                "max_geometry_family_counts": dict(
                    program_visual_directive.get("max_geometry_family_counts") or {}
                ),
                "max_chassis_family_counts": dict(
                    program_visual_directive.get("max_chassis_family_counts") or {}
                ),
                "max_wedge_like_count": wedge_cap,
                "max_pyramidal_like_count": pyramidal_cap,
            },
            "downstream_hard_gate": downstream_hard_gate,
            "counts": counts,
            "failures": failures,
            "missing_vlm_required_roof_archetypes": missing_required_roofs,
            "missing_required_solid_phenotypes": missing_required_phenotypes,
            "duration_seconds": round(perf_counter() - started, 3),
            "rows": rows,
            "png": str(board),
        })
    summary_board = output_dir / "maas-book-programs-60-summary.png"
    images = [Image.open(path).convert("RGB") for path in board_paths]
    combined = Image.new("RGB", (max(image.width for image in images), sum(image.height for image in images)), "#07111f")
    y = 0
    for image in images:
        combined.paste(image, (0, y))
        y += image.height
    combined.save(summary_board)
    book_program_numeric_status = "pass" if all(item["status"] == "pass" for item in program_results) else "fail"
    downstream_status = (
        "pass"
        if program_results and all(item["downstream_hard_gate"]["status"] == "pass" for item in program_results)
        else ("not_run" if all(item["downstream_hard_gate"]["status"] == "not_run" for item in program_results) else "fail")
    )
    result = {
        "schema_version": "arr.maas.book_program_portfolios.v1",
        "status": "pass" if book_program_numeric_status == "pass" and downstream_status in {"pass", "not_run"} else "fail",
        "book_program_numeric_status": book_program_numeric_status,
        "downstream_hard_gate_status": downstream_status,
        "pnu": pnu,
        "site_area_m2": round(float(site.area), 3),
        "program_count": len(program_results),
        "programs": program_results,
        "cross_program_language_comparison": _cross_program_language_comparison(
            selected_by_program,
            metrics_by_program,
        ),
        "legal_parking_checked": downstream_status != "not_run",
        "visual_duplicate_metric": "pose-invariant top/front/side silhouette distance",
        "summary_png": str(summary_board),
    }
    review_fingerprint_payload = [
        {
            "slug": item["slug"],
            "status": item["status"],
            "selected": [
                (
                    row.get("source_sequence"), row.get("book_principle_id"),
                    (row.get("book_scope") or {}).get("base_volume_label"),
                    row.get("solid_phenotype"), row.get("roof_archetype"),
                )
                for row in item.get("rows") or ()
            ],
        }
        for item in program_results
    ]
    result["visual_review_fingerprint"] = hashlib.sha256(
        json.dumps(review_fingerprint_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    outcome_graph_payload = outcome_graph.save()
    # Preserve a self-contained evidence snapshot beside every PNG/summary,
    # while the next run reads the stable PNU-scoped graph above.
    if outcome_graph_snapshot_path.resolve() != outcome_graph_path.resolve():
        snapshot_temporary = outcome_graph_snapshot_path.with_suffix(
            outcome_graph_snapshot_path.suffix + ".tmp"
        )
        snapshot_temporary.write_text(
            json.dumps(outcome_graph_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        snapshot_temporary.replace(outcome_graph_snapshot_path)
    result["geometry_mutation_outcome_graph"] = {
        "status": "materialized",
        "path": str(outcome_graph_path),
        "snapshot_path": str(outcome_graph_snapshot_path),
        "path_policy": (
            "explicit_cross_run_memory"
            if outcome_graph_path_was_explicit
            else "default_pnu_cross_run_memory"
        ),
        "persistent_across_output_directories": True,
        "node_count": outcome_graph_payload["node_count"],
        "edge_count": outcome_graph_payload["edge_count"],
        "observation_count": outcome_graph_payload["observation_count"],
        "neo4j_mirror": outcome_graph.mirror_to_neo4j(),
    }
    geometry_artifact_records = []
    for sequence in mass_brain_trace_sequences:
        feature = mass_brain_trace_features.get(sequence.name) or {}
        props = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        artifact = props.get("geometry_artifact") if isinstance(props.get("geometry_artifact"), dict) else None
        if artifact is None:
            continue
        geometry_artifact_records.append({
            "trace_sequence_name": sequence.name,
            "trace_sequence_label": sequence.label,
            "legacy_verb_calls": sequence.to_list(),
            "geometry_artifact": artifact,
        })
    geometry_artifact_path = output_dir / "maas-book-exact-geometry-artifacts.json"
    geometry_artifact_path.write_text(
        json.dumps({
            "schema_version": "arr.maas.geometry_artifact_archive.v1",
            "pnu": pnu,
            "selection_effect": "none_shadow_only",
            "record_count": len(geometry_artifact_records),
            "records": geometry_artifact_records,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    result["geometry_artifact_archive"] = {
        "status": "materialized",
        "path": str(geometry_artifact_path),
        "record_count": len(geometry_artifact_records),
        "program_count": len({
            str((record["geometry_artifact"] or {}).get("programType") or "")
            for record in geometry_artifact_records
        }),
    }
    result["mass_brain_geometry_trace"] = publish_geometry_portfolio_shadow(
        project_key=pnu,
        source_sequences=mass_brain_trace_sequences,
        source_features_by_sequence=mass_brain_trace_features,
        context={
            "programType": "verified_multi_program_portfolio",
            "programSlugs": [item["slug"] for item in program_results],
            "pnu": pnu,
            "outcomeGraphPath": str(outcome_graph_path),
            "selectionEffect": "none_shadow_only",
        },
    )
    visual_review_path = output_dir / "maas-book-programs-visual-review.json"
    if visual_review_path.exists():
        try:
            visual_review = json.loads(visual_review_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            visual_review = {}
        if (
            isinstance(visual_review, dict)
            and str(visual_review.get("pnu") or "") == pnu
            and str(visual_review.get("source_summary_fingerprint") or "") == result["visual_review_fingerprint"]
        ):
            result["numeric_status"] = book_program_numeric_status
            result["visual_design_review"] = visual_review
            result["visual_design_review_path"] = str(visual_review_path)
            if visual_review.get("status") == "fail":
                result["status"] = "fail"
        elif isinstance(visual_review, dict) and str(visual_review.get("pnu") or "") == pnu:
            result["visual_design_review"] = {
                "status": "not_run_for_current_fingerprint",
                "stale_review_ignored": True,
            }
    (output_dir / "maas-book-programs-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


__all__ = ["PROGRAMS", "run_book_program_portfolios"]
