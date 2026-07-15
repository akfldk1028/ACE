"""Fast, measured BOOK-operation portfolios on one real parcel.

This benchmark is intentionally bounded: it compiles typed operations over
program assemblies once, filters by clean/program gates, and performs measured
shape-diverse selection.  It is the synchronous diagnostic counterpart to the
slower evolutionary/VLM loop, not a replacement for legal/FAR/parking repair.
"""

from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, replace
from math import pi
from pathlib import Path
from time import perf_counter
from typing import Any

from PIL import Image
from shapely.errors import GEOSException
from shapely.geometry import Polygon

from design.maas.grammar.verb_sequence import VerbSequence
from design.maas.program_massing import (
    book_sentence_variants,
    compose_program_with_book_operations,
    program_seed_sequences,
)
from design.maas.program_massing.benchmark import render_archive_sheet
from design.maas.program_massing.morphology import intrinsic_shape_distance, intrinsic_silhouette_distance
from design.maas.program_massing.scoring import attach_program_massing_evidence
from design.maas.program_massing.search import program_seed_variants, source_feature
from design.maas.source_geometry import compile_sequence_to_source_mass

from .registry import build_book_language_registry
from .semantics import BASE_VOLUME_FRACTIONS
from .downstream_hard_gate import (
    LegalGenerationContext,
    build_legal_generation_context,
    evaluate_accepted_sources_downstream,
    fit_source_to_sunlight_field,
    generation_site_at_height,
)


PROGRAMS = (
    ("neighborhood", "근린생활시설", 15.0, 5),
    ("gymnasium", "체육관", 18.0, 3),
    ("cultural", "미술관", 15.0, 4),
)


@dataclass(frozen=True)
class _Candidate:
    principle_id: str
    principle_kind: str
    operation: str
    sequence: VerbSequence
    source: Any
    feature: dict[str, Any]
    score: float


def _distance(left: _Candidate, right: _Candidate) -> float:
    volume, plan = intrinsic_shape_distance(left.source, right.source)
    return min(1.0, float(volume) * 0.72 + float(plan) * 0.28)


def _silhouette_distance(left: _Candidate, right: _Candidate) -> float:
    return float(intrinsic_silhouette_distance(left.source, right.source))


def _scope_key(candidate: _Candidate) -> str:
    evidence = candidate.source.metadata.get("program_book_projection_evidence") or {}
    scope = evidence.get("scope") if isinstance(evidence, dict) else {}
    return str(scope.get("base_volume_label") or "1/1") if isinstance(scope, dict) else "1/1"


def _seed_family(candidate: _Candidate) -> str:
    return candidate.sequence.name.split("__book_", 1)[0].split("__search_", 1)[0]


def _section_family(candidate: _Candidate) -> str:
    evidence = candidate.source.metadata.get("program_section_graph_evidence") or {}
    nodes = evidence.get("materialized_nodes") if isinstance(evidence, dict) else ()
    operators = tuple(
        str(node.get("operator") or "")
        for node in (nodes or ())
        if isinstance(node, dict) and node.get("operator")
    )
    if operators:
        graph_operators = set(evidence.get("graph_operators") or ())
        modifiers = graph_operators & {"carved_entry", "daylight_monitor"}
        return "+".join(sorted(set(operators) | modifiers))
    signature = candidate.source.signature()
    return str(signature.get("formal_principle") or signature.get("family") or "flat_proxy")


def _oriented_aspect(poly: Polygon) -> float:
    rectangle = poly.minimum_rotated_rectangle
    coordinates = list(rectangle.exterior.coords)
    lengths = sorted(
        (((right[0] - left[0]) ** 2 + (right[1] - left[1]) ** 2) ** 0.5)
        for left, right in zip(coordinates, coordinates[1:])
        if left != right
    )
    return float(lengths[-1] / max(lengths[0], 1e-9)) if lengths else 1.0


def _scope_coverage_anchors(
    candidates: list[_Candidate],
    *,
    seed_family_cap: int,
    section_family_cap: int,
) -> list[_Candidate]:
    """Find one mutually silhouette-distinct candidate for every p.3 scope."""
    by_scope = {
        label: sorted(
            (candidate for candidate in candidates if _scope_key(candidate) == label),
            key=lambda candidate: candidate.score,
            reverse=True,
        )
        for label, _fraction in BASE_VOLUME_FRACTIONS
    }
    if any(not options for options in by_scope.values()):
        return []
    ordered_scopes = sorted(by_scope, key=lambda label: (len(by_scope[label]), label))

    def visit(
        index: int,
        picked: list[_Candidate],
        operation_usage: Counter,
        seed_usage: Counter,
        section_usage: Counter,
    ) -> list[_Candidate] | None:
        if index >= len(ordered_scopes):
            return list(picked)
        scope = ordered_scopes[index]
        options = sorted(
            by_scope[scope],
            key=lambda candidate: (
                seed_usage[_seed_family(candidate)],
                section_usage[_section_family(candidate)],
                -candidate.score,
            ),
        )
        for candidate in options:
            seed = _seed_family(candidate)
            section = _section_family(candidate)
            if operation_usage[candidate.operation] >= 2:
                continue
            if seed_usage[seed] >= seed_family_cap or section_usage[section] >= section_family_cap:
                continue
            if any(_silhouette_distance(candidate, other) < 0.10 for other in picked):
                continue
            operation_usage[candidate.operation] += 1
            seed_usage[seed] += 1
            section_usage[section] += 1
            picked.append(candidate)
            result = visit(index + 1, picked, operation_usage, seed_usage, section_usage)
            if result is not None:
                return result
            picked.pop()
            operation_usage[candidate.operation] -= 1
            seed_usage[seed] -= 1
            section_usage[section] -= 1
        return None

    return visit(0, [], Counter(), Counter(), Counter()) or []


def _fingerprint(candidate: _Candidate) -> tuple[Any, ...]:
    return tuple(sorted((
        tuple(round(value, 3) for value in volume.footprint.bounds),
        round(float(volume.footprint.area), 3),
        round(float(volume.bottom_fraction), 3),
        round(float(volume.top_fraction), 3),
    ) for volume in candidate.source.volumes))


def _inside_site(source: Any, site: Polygon) -> bool:
    try:
        return all(
            volume.footprint.is_valid
            and volume.footprint.difference(site).area <= 1e-6
            for volume in source.volumes
        )
    except (GEOSException, ValueError):
        return False


def _select(pool: list[_Candidate], target: int = 20) -> list[_Candidate]:
    unique: dict[tuple[Any, ...], _Candidate] = {}
    for candidate in pool:
        fingerprint = _fingerprint(candidate)
        current = unique.get(fingerprint)
        if current is None or candidate.score > current.score:
            unique[fingerprint] = candidate
    candidates = list(unique.values())
    selected: list[_Candidate] = []
    operation_usage: dict[str, int] = {}
    scope_usage: dict[str, int] = {}
    seed_usage: dict[str, int] = {}
    section_usage: dict[str, int] = {}
    available_scopes = {_scope_key(candidate) for candidate in candidates}
    seed_families = {_seed_family(candidate) for candidate in candidates}
    seed_family_cap = max(2, (target + max(1, len(seed_families)) - 1) // max(1, len(seed_families)) + 1)
    section_family_cap = max(3, target // 2)
    anchors = _scope_coverage_anchors(
        candidates,
        seed_family_cap=seed_family_cap,
        section_family_cap=section_family_cap,
    )
    anchor_ids = {id(candidate) for candidate in anchors}
    candidates = [candidate for candidate in candidates if id(candidate) not in anchor_ids]
    for winner in anchors:
        selected.append(winner)
        operation_usage[winner.operation] = operation_usage.get(winner.operation, 0) + 1
        scope_usage[_scope_key(winner)] = scope_usage.get(_scope_key(winner), 0) + 1
        seed_usage[_seed_family(winner)] = seed_usage.get(_seed_family(winner), 0) + 1
        section_usage[_section_family(winner)] = section_usage.get(_section_family(winner), 0) + 1
    while candidates and len(selected) < target:
        def eligible_with_operation_cap(operation_cap: int) -> list[_Candidate]:
            return [
                candidate for candidate in candidates
                if operation_usage.get(candidate.operation, 0) < operation_cap
                and seed_usage.get(_seed_family(candidate), 0) < seed_family_cap
                and section_usage.get(_section_family(candidate), 0) < section_family_cap
                and all(_silhouette_distance(candidate, other) >= 0.10 for other in selected)
            ]

        eligible = eligible_with_operation_cap(2)
        if not eligible:
            # Only after the two-use diversity cap is exhausted may the same
            # BOOK sentence appear once more on another program/section
            # family. Silhouette and family caps remain unchanged.
            eligible = eligible_with_operation_cap(3)
        if not eligible:
            break
        uncovered_scopes = available_scopes - set(scope_usage)
        if uncovered_scopes:
            # BOOK p.3 scope coverage is a portfolio constraint. Start with
            # the rarest surviving scope so a high-scoring 1/1 family cannot
            # crowd a valid 1/16 or 1/8 candidate out of the final archive.
            target_scope = min(
                uncovered_scopes,
                key=lambda scope: (
                    sum(_scope_key(candidate) == scope for candidate in eligible),
                    scope,
                ),
            )
            scoped = [candidate for candidate in eligible if _scope_key(candidate) == target_scope]
            if scoped:
                eligible = scoped

        def selection_key(candidate: _Candidate) -> tuple[float, float]:
            novelty = 1.0 if not selected else min(
                _distance(candidate, other) * 0.55 + _silhouette_distance(candidate, other) * 0.45
                for other in selected
            )
            new_language_bonus = 0.08 if operation_usage.get(candidate.operation, 0) == 0 else 0.0
            new_scope_bonus = 0.05 if scope_usage.get(_scope_key(candidate), 0) == 0 else 0.0
            new_seed_bonus = 0.06 if seed_usage.get(_seed_family(candidate), 0) == 0 else 0.0
            new_section_bonus = 0.05 if section_usage.get(_section_family(candidate), 0) == 0 else 0.0
            return (
                candidate.score * 0.44
                + novelty * 0.56
                + new_language_bonus
                + new_scope_bonus
                + new_seed_bonus
                + new_section_bonus,
                candidate.score,
            )

        winner = max(eligible, key=selection_key)
        selected.append(winner)
        operation_usage[winner.operation] = operation_usage.get(winner.operation, 0) + 1
        scope_usage[_scope_key(winner)] = scope_usage.get(_scope_key(winner), 0) + 1
        seed_usage[_seed_family(winner)] = seed_usage.get(_seed_family(winner), 0) + 1
        section_usage[_section_family(winner)] = section_usage.get(_section_family(winner), 0) + 1
        candidates.remove(winner)
    return selected


def _program_pool(
    site: Polygon,
    building_type: str,
    height: float,
    floors: int,
    *,
    generation_context: LegalGenerationContext | None = None,
    parent_variant_indices: tuple[int, ...] = (0,),
) -> tuple[list[_Candidate], dict[str, Any]]:
    accepted: list[_Candidate] = []
    evaluated = compiled = clean = program_passed = 0
    scope_stage_counts = {
        label: {
            "evaluated": 0,
            "compiled": 0,
            "projection_materialized": 0,
            "projection_failed": 0,
            "clean": 0,
            "program_passed": 0,
        }
        for label, _fraction in BASE_VOLUME_FRACTIONS
    }
    gate_names = ("role_coverage", "dominant_ratio", "site_coverage", "hierarchy", "coherence")
    gate_diagnostics = {
        label: {
            "candidate_count": 0,
            "hard_pass_count": 0,
            "failed_candidate_count": 0,
            "gate_failed_counts": {name: 0 for name in gate_names},
            "exclusive_gate_failed_counts": {name: 0 for name in gate_names},
            "failure_signature_counts": {},
            "metric_samples": {
                "role_coverage_score": [],
                "dominant_component_ratio": [],
                "dominant_ratio_score": [],
                "site_coverage_ratio": [],
                "site_coverage_score": [],
                "hierarchy_score": [],
                "coherence_score": [],
            },
        }
        for label, _fraction in BASE_VOLUME_FRACTIONS
    }
    requested_parent_indices = tuple(sorted({max(0, int(index)) for index in parent_variant_indices})) or (0,)
    parent_seeds = tuple(
        variant
        for seed_index, seed in enumerate(program_seed_sequences(building_type))
        for variant_index, variant in enumerate(program_seed_variants(
            seed,
            count=max(requested_parent_indices) + 1,
            random_seed=417 + seed_index * 97,
        ))
        if variant_index in requested_parent_indices
    )
    principles = tuple(build_book_language_registry()["principles"])
    for seed in parent_seeds:
        for principle_index, principle in enumerate(principles):
            execution_verbs = tuple(principle["execution_verbs"])
            # One BOOK sentence is a typed operator family, not one frozen
            # geometry.  Execute three bounded schema-derived parameter probes
            # so selection can compare real alternatives without parcel or
            # finished-form templates.
            for variant_index, operations in enumerate(book_sentence_variants(execution_verbs, count=3)):
                evaluated += 1
                suffix = str(principle["principle_id"]).split("book:", 1)[-1].replace(":", "_")
                base_volume_label = BASE_VOLUME_FRACTIONS[principle_index % len(BASE_VOLUME_FRACTIONS)][0]
                orientation = ("long_axis", "short_axis", "vertical")[(principle_index // len(BASE_VOLUME_FRACTIONS)) % 3]
                scope_counts = scope_stage_counts[base_volume_label]
                scope_counts["evaluated"] += 1
                composed = compose_program_with_book_operations(
                    seed,
                    operations,
                    name_suffix=suffix,
                    base_volume_label=base_volume_label,
                    orientation=orientation,
                )
                sequence = VerbSequence(
                    name=f"{composed.name}__search_v{variant_index}",
                    label=composed.label,
                    calls=composed.calls,
                    notes=composed.notes,
                )
                compile_site = site
                generation_host_mode = "horizontal_buildable_envelope"
                # The third typed parameter probe also explores the vertical
                # legal field.  Its base host is the sunlight-safe section at
                # the requested program height, so the resulting geometry is
                # born inside the envelope instead of repaired after selection.
                use_height_safe_host = variant_index == 2 or (
                    base_volume_label == "1/16" and variant_index == 0
                )
                if generation_context is not None and use_height_safe_host:
                    # Use the section at two thirds of design height.  The
                    # remaining cap is still measured by the exact downstream
                    # retention gate, while the host remains large enough to
                    # carry a coherent long-span/program role graph.
                    generation_section_ratio = 2.0 / 3.0
                    height_safe_site = generation_site_at_height(
                        generation_context,
                        height * generation_section_ratio,
                    )
                    if height_safe_site is not None:
                        compile_site = height_safe_site
                        generation_host_mode = "height_safe_sunlight_section"
                source = compile_sequence_to_source_mass(compile_site, sequence)
                if source is None:
                    continue
                if generation_context is not None:
                    metadata = deepcopy(source.metadata)
                    legal_evidence = deepcopy(generation_context.evidence)
                    legal_evidence.update({
                        "generation_host_mode": generation_host_mode,
                        "candidate_generation_site_area_m2": round(float(compile_site.area), 3),
                        "requested_program_height_m": float(height),
                        "generation_host_section_height_m": (
                            round(float(height) * generation_section_ratio, 3)
                            if generation_host_mode == "height_safe_sunlight_section"
                            else 0.0
                        ),
                    })
                    metadata["legal_generation_context_evidence"] = legal_evidence
                    source = replace(source, metadata=metadata)
                    if base_volume_label == "1/16" and generation_host_mode == "horizontal_buildable_envelope":
                        source = fit_source_to_sunlight_field(
                            source,
                            generation_context,
                            height_m=height,
                            floors=floors,
                        )
                compiled += 1
                scope_counts["compiled"] += 1
                projection_evidence = source.metadata.get("program_book_projection_evidence") or {}
                if projection_evidence.get("status") != "materialized":
                    scope_counts["projection_failed"] += 1
                    continue
                scope_counts["projection_materialized"] += 1
                signature = source.signature()
                raw_surfaces = int(signature.get("surface_count") or 0)
                effective_surfaces = int(signature.get("effective_surface_count") or raw_surfaces)
                profiled = bool((signature.get("continuous_surface_evidence") or {}).get("hard_pass"))
                if len(source.volumes) > 5 or raw_surfaces > (160 if profiled else 48) or effective_surfaces > 28:
                    continue
                if not _inside_site(source, compile_site):
                    continue
                clean += 1
                scope_counts["clean"] += 1
                feature = source_feature(
                    source,
                    sequence,
                    building_type=building_type,
                    height=height,
                    floors=floors,
                    site_area=float(compile_site.area),
                )
                program = attach_program_massing_evidence(feature, building_type=building_type)
                spatial = feature["properties"]["program_spatial_evidence"]
                diagnostic = gate_diagnostics[base_volume_label]
                diagnostic["candidate_count"] += 1
                gate_pass = {
                    "role_coverage": bool(all(spatial.get("required_role_hits") or ())),
                    "dominant_ratio": float(spatial.get("dominant_ratio_score") or 0.0) >= 0.55,
                    "site_coverage": float(spatial.get("site_coverage_score") or 0.0) >= 0.55,
                    "hierarchy": float(spatial.get("hierarchy_score") or 0.0) >= 0.50,
                    "coherence": bool((feature["properties"].get("source_signature", {}).get("coherence_evidence") or {}).get("hard_pass", False)),
                }
                failed_gates = tuple(name for name in gate_names if not gate_pass[name])
                if program["hard_pass"]:
                    diagnostic["hard_pass_count"] += 1
                else:
                    diagnostic["failed_candidate_count"] += 1
                for name in failed_gates:
                    diagnostic["gate_failed_counts"][name] += 1
                if len(failed_gates) == 1:
                    diagnostic["exclusive_gate_failed_counts"][failed_gates[0]] += 1
                signature = "+".join(failed_gates) if failed_gates else "none"
                diagnostic["failure_signature_counts"][signature] = diagnostic["failure_signature_counts"].get(signature, 0) + 1
                for name in diagnostic["metric_samples"]:
                    diagnostic["metric_samples"][name].append(float(spatial.get(name) or 0.0))
                if not program["hard_pass"]:
                    continue
                program_passed += 1
                scope_counts["program_passed"] += 1
                score = float(program["program_fit_score"]) * 0.56 + float(spatial["architectural_score"]) * 0.44
                accepted.append(_Candidate(
                    str(principle["principle_id"]),
                    str(principle["kind"]),
                    str(principle["label"]),
                    sequence,
                    source,
                    feature,
                    round(score, 6),
                ))
    summarized_gate_diagnostics = {
        label: _summarize_gate_diagnostic(diagnostic)
        for label, diagnostic in gate_diagnostics.items()
    }
    return accepted, {
        "evaluated": evaluated,
        "compiled": compiled,
        "clean": clean,
        "program_passed": program_passed,
        "program_passed_by_seed_family": dict(sorted(Counter(_seed_family(candidate) for candidate in accepted).items())),
        "program_passed_by_section_family": dict(sorted(Counter(_section_family(candidate) for candidate in accepted).items())),
        "scope_stage_counts": scope_stage_counts,
        "program_gate_diagnostics_by_scope": summarized_gate_diagnostics,
        "program_gate_diagnostics_total": _merge_gate_diagnostics(summarized_gate_diagnostics),
    }


def _metric_summary(values: list[float]) -> dict[str, float | int]:
    if not values:
        return {"count": 0, "minimum": 0.0, "mean": 0.0, "maximum": 0.0}
    return {
        "count": len(values),
        "minimum": round(min(values), 4),
        "mean": round(sum(values) / len(values), 4),
        "maximum": round(max(values), 4),
    }


def _summarize_gate_diagnostic(diagnostic: dict[str, Any]) -> dict[str, Any]:
    result = {key: deepcopy(value) for key, value in diagnostic.items() if key != "metric_samples"}
    result["metric_summaries"] = {
        name: _metric_summary(values)
        for name, values in diagnostic["metric_samples"].items()
    }
    return result


def _merge_gate_diagnostics(by_scope: dict[str, dict[str, Any]]) -> dict[str, Any]:
    gate_names = ("role_coverage", "dominant_ratio", "site_coverage", "hierarchy", "coherence")
    total = {
        "candidate_count": sum(item["candidate_count"] for item in by_scope.values()),
        "hard_pass_count": sum(item["hard_pass_count"] for item in by_scope.values()),
        "failed_candidate_count": sum(item["failed_candidate_count"] for item in by_scope.values()),
        "gate_failed_counts": {
            name: sum(item["gate_failed_counts"][name] for item in by_scope.values())
            for name in gate_names
        },
        "exclusive_gate_failed_counts": {
            name: sum(item["exclusive_gate_failed_counts"][name] for item in by_scope.values())
            for name in gate_names
        },
        "failure_signature_counts": {},
    }
    for item in by_scope.values():
        for signature, count in item["failure_signature_counts"].items():
            total["failure_signature_counts"][signature] = total["failure_signature_counts"].get(signature, 0) + count
    return total


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
    return {
        "seed_family": _seed_family(candidate),
        "section_family": _section_family(candidate),
        "book_scope": _scope_key(candidate),
        "oriented_plan_aspect_ratio": round(aspect, 4),
        "plan_compactness": round(compactness, 4),
        "plan_family": "bar" if aspect >= 2.2 else ("compact" if aspect <= 1.35 else "intermediate"),
        "dominant_component_ratio": round(float(spatial.get("dominant_component_ratio") or 0.0), 4),
        "site_coverage_ratio": round(float(spatial.get("site_coverage_ratio") or 0.0), 4),
        "hierarchy_score": round(float(spatial.get("hierarchy_score") or 0.0), 4),
        "section_control_signature": controls,
        "semantic_role_tokens": dict(sorted(role_tokens.items())),
    }


def _portfolio_language_metrics(selected: list[_Candidate]) -> dict[str, Any]:
    descriptors = [_candidate_language_descriptor(candidate) for candidate in selected]
    seed_counts = Counter(item["seed_family"] for item in descriptors)
    section_counts = Counter(item["section_family"] for item in descriptors)
    plan_counts = Counter(item["plan_family"] for item in descriptors)
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
        "seed_family_counts": dict(sorted(seed_counts.items())),
        "seed_family_count": len(seed_counts),
        "dominant_seed_family_share": round(max(seed_counts.values(), default=0) / total, 4),
        "roof_section_family_counts": dict(sorted(section_counts.items())),
        "roof_section_family_count": len(section_counts),
        "dominant_roof_section_family_share": round(max(section_counts.values(), default=0) / total, 4),
        "section_control_signature_count": len(control_signatures),
        "plan_family_counts": dict(sorted(plan_counts.items())),
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
        "semantic_role_token_counts": dict(sorted(sum((Counter(item["semantic_role_tokens"]) for item in descriptors), Counter()).items())),
    }


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


def _hard_gate_count_summary(report: dict[str, Any] | None, candidate_count: int) -> dict[str, Any]:
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
    for row in report["rows"]:
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
    summary["by_scope"] = dict(sorted(by_scope.items()))
    summary["candidate_count_by_generation_host"] = dict(sorted(by_host_mode.items()))
    summary["combined_hard_pass_by_generation_host"] = dict(sorted(hard_pass_by_host_mode.items()))
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
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    program_results: list[dict[str, Any]] = []
    selected_by_program: dict[str, list[_Candidate]] = {}
    metrics_by_program: dict[str, dict[str, Any]] = {}
    board_paths: list[Path] = []
    for slug, building_type, height, floors in PROGRAMS:
        started = perf_counter()
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
        pool, counts = _program_pool(
            generation_site,
            building_type,
            height,
            floors,
            generation_context=generation_context,
        )
        preselection_hard_gate = None
        selection_pool = pool
        if generation_context is not None:
            preselection_hard_gate = evaluate_accepted_sources_downstream(
                pool,
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
                for candidate, row in zip(pool, preselection_hard_gate["rows"])
                if row["combined_hard_pass"]
            ]
        counts["preselection_hard_gate"] = _hard_gate_count_summary(preselection_hard_gate, len(pool))
        selected = _select(selection_pool, 20)
        missing_scope = len({_scope_key(candidate) for candidate in selected}) < len(BASE_VOLUME_FRACTIONS)
        if len(selected) < 20 or missing_scope:
            replenishment_pool, replenishment_counts = _program_pool(
                generation_site,
                building_type,
                height,
                floors,
                generation_context=generation_context,
                parent_variant_indices=(1,),
            )
            replenishment_hard_gate = None
            replenishment_selection_pool = replenishment_pool
            if generation_context is not None:
                replenishment_hard_gate = evaluate_accepted_sources_downstream(
                    replenishment_pool,
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
                replenishment_selection_pool = [
                    candidate
                    for candidate, row in zip(replenishment_pool, replenishment_hard_gate["rows"])
                    if row["combined_hard_pass"]
                ]
            counts["bounded_parent_replenishment"] = {
                **replenishment_counts,
                "preselection_hard_gate": _hard_gate_count_summary(
                    replenishment_hard_gate,
                    len(replenishment_pool),
                ),
            }
            selection_pool = [*selection_pool, *replenishment_selection_pool]
            selected = _select(selection_pool, 20)
        counts["final_hard_pass_selection_pool_count"] = len(selection_pool)
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
        for index, candidate in enumerate(selected):
            feature = deepcopy(candidate.feature)
            props = feature["properties"]
            props["archive_variant_id"] = props["variant_id"]
            props["variant_id"] = f"maas_{index + 1:02d}"
            props["mass_shape"] = candidate.operation
            props["review_status"] = "accept"
            props["review_reasons"] = ["program hard pass", "clean mass pass"]
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
                "seed_family": descriptor["seed_family"],
                "roof_section_family": descriptor["section_family"],
                "oriented_plan_aspect_ratio": descriptor["oriented_plan_aspect_ratio"],
                "plan_compactness": descriptor["plan_compactness"],
                "plan_family": descriptor["plan_family"],
                "dominant_component_ratio": descriptor["dominant_component_ratio"],
                "site_coverage_ratio": descriptor["site_coverage_ratio"],
                "hierarchy_score": descriptor["hierarchy_score"],
                "section_control_signature": descriptor["section_control_signature"],
                "semantic_role_tokens": descriptor["semantic_role_tokens"],
            })
        board = output_dir / f"maas-book-{slug}-20.png"
        render_archive_sheet(
            features,
            board,
            title=f"MAAS BOOK × {building_type} · PNU {pnu} · {len(features)}/20 silhouette-distinct masses",
        )
        board_paths.append(board)
        near_duplicates = sum(
            1
            for index, left in enumerate(selected)
            for right in selected[:index]
            if _silhouette_distance(left, right) < 0.10
        )
        failures = []
        if len(selected) != 20:
            failures.append("selected_count_below_20")
        operation_count = len({candidate.principle_id for candidate in selected})
        if operation_count < 10:
            failures.append("book_operation_count_below_10")
        visual_languages: list[_Candidate] = []
        for candidate in selected:
            if all(_silhouette_distance(candidate, representative) >= 0.16 for representative in visual_languages):
                visual_languages.append(candidate)
        if len(visual_languages) < 10:
            failures.append("visual_language_count_below_10")
        scope_count = len({_scope_key(candidate) for candidate in selected})
        if scope_count < len(BASE_VOLUME_FRACTIONS):
            failures.append("book_base_volume_scope_count_below_6")
        if any(not row["inside_site"] or not row["program_hard_pass"] for row in rows):
            failures.append("hard_gate_failure_in_selected_portfolio")
        if language_metrics["dominant_seed_family_share"] > 0.40:
            failures.append("repeated_seed_footprint_family_above_40_percent")
        if language_metrics["dominant_roof_section_family_share"] > 0.50:
            failures.append("repeated_roof_section_family_above_50_percent")
        program_results.append({
            "program": building_type,
            "slug": slug,
            "status": "pass" if not failures else "fail",
            "selected_count": len(selected),
            "book_operation_count": operation_count,
            "book_principle_kind_counts": {
                kind: sum(candidate.principle_kind == kind for candidate in selected)
                for kind in ("base_operative", "combination", "aggregation")
            },
            "visual_language_count": len(visual_languages),
            "book_base_volume_scope_count": scope_count,
            "book_base_volume_scopes": sorted({_scope_key(candidate) for candidate in selected}),
            "near_duplicate_pair_count": near_duplicates,
            "program_language_metrics": language_metrics,
            "downstream_hard_gate": downstream_hard_gate,
            "counts": counts,
            "failures": failures,
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
    visual_review_path = output_dir / "maas-book-programs-visual-review.json"
    if visual_review_path.exists():
        try:
            visual_review = json.loads(visual_review_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            visual_review = {}
        if (
            isinstance(visual_review, dict)
            and str(visual_review.get("pnu") or "") == pnu
        ):
            result["numeric_status"] = book_program_numeric_status
            result["visual_design_review"] = visual_review
            result["visual_design_review_path"] = str(visual_review_path)
            if visual_review.get("status") == "fail":
                result["status"] = "fail"
    (output_dir / "maas-book-programs-summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


__all__ = ["PROGRAMS", "run_book_program_portfolios"]
