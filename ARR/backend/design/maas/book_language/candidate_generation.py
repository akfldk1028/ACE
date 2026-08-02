"""Staged BOOK candidate authorship, materialization and hard gating."""

from __future__ import annotations

import json
import logging
import os
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from math import cos, isfinite, sin
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
from typing import Any, Callable

from shapely.geometry import Polygon, mapping, shape

from design.maas.geometry_language import (
    GeometryAuthorError,
    GeometryOutcomeGraph,
    GeometryProgram,
    apply_book_projection_to_geometry_program,
    universal_form_program_pages,
    apply_geometry_edits_compiler_safe,
    architectural_shape_programs,
    author_geometry_programs_with_openai,
    build_geometry_graph_notes,
    build_geometry_graph_snapshot,
    compile_geometry_program,
    compile_geometry_program_to_source_mass,
    openai_vlm_geometry_critic,
    project_program_requirements,
    reference_language_programs,
    recursive_book_projection_evidence,
    retrieve_geometry_reference_matches,
    run_geometry_program_a2a_loop,
    synthesize_architectural_programs,
)
from design.maas.geometry_language.floorwise_legal_program import (
    is_intentional_floorwise_stepped_program,
)
from design.maas.geometry_language.gate import GeometryGatePolicy, compilation_gate
from design.maas.geometry_language.legal_field_affine_placement import (
    select_legal_field_affine_projection,
)
from design.maas.geometry_language.source_bridge import (
    compile_site_bound_geometry_program_to_source_mass,
    floorwise_source_to_geometry_program,
    materialize_floorwise_legal_source,
    source_surface_payload_hash,
    source_volume_payload_hash,
)
from design.maas.geometry_language.projected_visual_contract import (
    final_floorwise_visual_geometry_hash,
)
from design.maas.grammar.verb_sequence import VerbSequence
from design.maas.program_massing import (
    ProgramSectionGraphEdit,
    compose_program_with_book_operations,
    mutate_program_section_sequence,
    program_reference_contract,
    program_seed_sequences,
)
from design.maas.program_massing.scoring import attach_program_massing_evidence
from design.maas.program_massing.morphology import (
    intrinsic_silhouette_distance,
)
from design.maas.program_massing.semantic_carriers import (
    bind_source_role_scaffold_to_program,
    build_program_semantic_carrier_evidence,
    rebind_semantic_projection_capacity,
    semantic_capacity_measurement_hash,
    semantic_site_context_hash,
)
from design.maas.program_massing.search import program_seed_variants, source_feature
from design.maas.preference.loop import feature_preview_png
from design.maas.source_geometry import compile_sequence_to_source_mass
from design.maas.shared_floor_contract import (
    bind_shared_floor_contract_capacity,
    materialize_shared_floor_contract,
)

from .candidate_analysis import (
    _Candidate,
    _clean_mass_gate,
    _inside_site,
    _program_form_gate,
    _section_family,
    _seed_family,
    _seed_is_llm_authored,
    _site_access_side_in_principal_frame,
    _solid_morphology_metrics,
)
from .candidate_floor_authority import (
    _capacity_pack_retry_eligible,
    _capacity_retry_required,
    _candidate_floor_context,
    _compact_candidate_capacity_evidence,
    _shared_floor_capacity_measurement as _measure_candidate_floor_capacity,
)
from .capacity_contract import measure_source_capacity, recursive_plan_coverage_floor
from .mass_passport_bridge import resolve_capacity_band_evidence
from .capacity_alternatives import (
    build_capacity_alternative,
    capacity_fit_score,
    capacity_retry_floor_targets,
    capacity_retry_plan_coverage,
    capacity_alternative_for_host,
    capacity_contract_for_alternative,
    evaluate_capacity_alternative,
)


logger = logging.getLogger(__name__)
from .competition_candidate_screen import (
    _capacity_alternative_schedule_index,
    _cheap_ast_bounds,
    _cheap_morphology_preclassification,
    _cheap_typed_ast_candidate_evidence,
    _competition_cheap_candidate_records,
    _competition_pre_exact_shortlist,
    _diagnostic_generation_cap_reached,
    _legal_section_dimensions,
    _recursive_principle_schedule_limit,
    competition_breadth_generation_budget,
    resolve_competition_breadth_generation_budget,
)
from .diagnostic_anchor_scheduler import (
    diagnostic_anchor_capacity_schedule_index,
    diagnostic_anchor_schedule_active,
    diagnostic_anchor_principles,
    diagnostic_anchor_sentence_variants,
    diagnostic_anchor_scope,
    diagnostic_anchor_spec,
    schedule_diagnostic_anchor_parents,
)
from .variation_lattice import book_probe_scope, book_variation_indices
from .downstream_hard_gate import LegalGenerationContext, fit_source_to_sunlight_field, generation_site_at_height
from .gate_diagnostics import _empty_gate_diagnostic, _merge_gate_diagnostics, _record_gate_diagnostic, _summarize_gate_diagnostic
from .lineage import gate_descendants_by_base, lineage_record, staged_principle_schedule
from .program_catalog import PROGRAMS
from .reference_context import _audited_final_book_references, _reference_language_author_context
from .registry import build_book_language_registry
from .semantics import BASE_VOLUME_FRACTIONS
from .legal_floor_field import validate_legal_floor_field


class _PostBookVlmOnly(RuntimeError):
    """Stop pre-BOOK review after authorship; the exact final solid owns VLM."""




















def _mass_stage_design_score(
    *,
    program_fit_score: float,
    architectural_score: float,
    advisory_capacity_score: float | None = None,
) -> float:
    """Score MASS design without letting downstream capacity rank the board."""

    _ = advisory_capacity_score
    return (
        float(program_fit_score) * 0.56
        + float(architectural_score) * 0.44
    )


def _eligible_smoke_floor_candidate(
    source: Any,
    shared_floor_contract: dict[str, Any] | None,
    capacity_measurement: dict[str, Any] | None,
    capacity_projection: dict[str, Any] | None,
    viable_base_keys: set[str],
) -> bool:
    """Never stop generation from a pre-downstream acceptance proxy."""
    _ = (
        source,
        shared_floor_contract,
        capacity_measurement,
        capacity_projection,
        viable_base_keys,
    )
    return False


def _capacity_retry_result_is_selectable(
    floor_contract: dict[str, Any] | None,
    retried_capacity: dict[str, Any] | None,
    baseline_capacity: dict[str, Any] | None,
) -> bool:
    """Capacity evidence cannot select replacement geometry at the MASS stage."""

    return False


def _shared_floor_capacity_measurement(
    source: Any,
    base_capacity_contract: dict[str, Any],
    *,
    generation_context: Any,
    capacity_site: Polygon,
    height: float,
    floors: int,
    pnu: str = "",
    trusted_legal_floor_field: dict[str, Any] | None = None,
    expected_legal_floor_field_hash: str = "",
    trusted_clear_span_floor_plan: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Preserve the legacy sampler patch seam for floor measurement."""

    return _measure_candidate_floor_capacity(
        source,
        base_capacity_contract,
        generation_context=generation_context,
        capacity_site=capacity_site,
        height=height,
        floors=floors,
        pnu=pnu,
        trusted_legal_floor_field=trusted_legal_floor_field,
        expected_legal_floor_field_hash=expected_legal_floor_field_hash,
        trusted_clear_span_floor_plan=trusted_clear_span_floor_plan,
        generation_site_sampler=generation_site_at_height,
    )


def _agent_mutated_seeds(
    building_type: str,
    mutations: list[dict[str, Any]] | None,
    geometry_mutations: list[dict[str, Any]] | None = None,
    synthesis_requests: list[dict[str, Any]] | None = None,
    outcome_graph: GeometryOutcomeGraph | None = None,
    site: Polygon | None = None,
    site_boundary_source: str = "",
    site_access_context: dict[str, Any] | None = None,
    site_access_geometry: dict[str, Any] | None = None,
    program_dimensional_context: dict[str, Any] | None = None,
    height: float = 1.0,
    floors: int = 1,
    live_geometry_vlm_revision: bool = False,
    base_capacity_contract: dict[str, Any] | None = None,
    universal_variation_pages: tuple[int, ...] = (0,),
) -> tuple[VerbSequence, ...]:
    """Apply agent/VLM graph edits to reusable role seeds, never finished forms."""
    seeds = list(program_seed_sequences(building_type))
    originals = {sequence.name: sequence for sequence in seeds}
    for index, record in enumerate(mutations or ()):  # bounded external genotype proposals
        if not isinstance(record, dict):
            continue
        source = originals.get(str(record.get("source_seed") or ""))
        if source is None:
            continue
        edit_records = record.get("edits") if isinstance(record.get("edits"), list) else [record]
        typed_edits: list[ProgramSectionGraphEdit] = []
        replacement = "genotype"
        for edit_record in edit_records:
            if not isinstance(edit_record, dict):
                continue
            operation = str(edit_record.get("operation") or "")
            if operation not in {"replace_roof_operator", "set_parameter", "set_section_control"}:
                continue
            operator_value = str(edit_record.get("operator_value") or "") or None
            if operator_value:
                replacement = operator_value
            try:
                numeric_value = (
                    float(edit_record["numeric_value"])
                    if edit_record.get("numeric_value") is not None
                    else None
                )
                control_index = (
                    int(edit_record["control_index"])
                    if edit_record.get("control_index") is not None
                    else None
                )
            except (TypeError, ValueError):
                continue
            typed_edits.append(ProgramSectionGraphEdit(
                operation=operation,
                target_node_id=str(edit_record.get("target_node_id") or "roof"),
                parameter_name=str(edit_record.get("parameter_name") or "operator"),
                numeric_value=numeric_value,
                control_index=control_index,
                operator_value=operator_value,
                rationale=str(edit_record.get("rationale") or record.get("rationale") or "agent-directed genotype mutation"),
            ))
        if not typed_edits:
            continue
        try:
            mutated = mutate_program_section_sequence(
                source,
                typed_edits,
                director="vlm_portfolio_critic",
                name_suffix=f"genotype_{index}_{replacement}",
            )
        except ValueError:
            continue
        if mutated.name != source.name:
            seeds.append(mutated)
    # A geometry directive creates another typed program seed, not a frozen
    # mesh.  The same program roles and BOOK projection compile first; only
    # then is the dominant role replaced by the recursive solid program.
    for index, record in enumerate(geometry_mutations or ()):
        if not isinstance(record, dict):
            continue
        source = originals.get(str(record.get("source_seed") or ""))
        program_id = str(record.get("geometry_program") or "")
        if source is None or program_id not in _geometry_program_registry():
            continue
        raw_strengths = (
            record.get("legal_fit_strengths")
            if isinstance(record.get("legal_fit_strengths"), list)
            else [record.get("legal_fit_strength") or 0.0]
        )
        try:
            legal_fit_strengths = tuple(dict.fromkeys(
                max(0.0, min(1.0, float(value))) for value in raw_strengths
            ))
        except (TypeError, ValueError):
            continue
        edit_records = record.get("geometry_edits") if isinstance(record.get("geometry_edits"), list) else []
        for strength_index, legal_fit_strength in enumerate(legal_fit_strengths):
            notes = tuple((*source.notes,
                f"geometry_program_directive={program_id}",
                f"geometry_program_source_seed={source.name}",
                f"geometry_program_edits={json.dumps(edit_records, sort_keys=True, separators=(',', ':'))}",
                f"geometry_program_rationale={str(record.get('rationale') or 'agent-authored recursive solid mutation')}",
                f"geometry_program_legal_fit_strength={legal_fit_strength}",
                "geometry_program_source=typed_agent_directive",
            ))
            seeds.append(replace(
                source,
                name=f"{source.name}__geometry_genotype_{index}_{strength_index}_{program_id}",
                notes=notes,
            ))
    # The dominant form control lane is program-independent.  Program role
    # seeds are only carriers here: the shared recursive solid is projected by
    # BOOK first and receives use-specific roles/gates downstream.  The old
    # profile request authored a gym/neighbourhood/cultural body before p.3 and
    # BOOK, which made the supposedly fundamental grammar program-shaped.
    requested_universal_pages = tuple(sorted({
        max(0, min(7, int(page))) for page in universal_variation_pages
    })) or (0,)
    universal_programs = universal_form_program_pages(requested_universal_pages)
    for source_index, source in enumerate(tuple(originals.values())[:2]):
        for program_index, program in enumerate(universal_programs):
            payload = json.dumps(
                program.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            notes = tuple((*source.notes,
                f"geometry_program_payload={payload}",
                f"geometry_program_source_seed={source.name}",
                "geometry_program_edits=[]",
                "geometry_program_rationale=program-independent base seed and chassis bank before BOOK and use projection",
                "geometry_program_legal_fit_strength=0.0",
                "geometry_program_source=universal_form_bank",
                f"geometry_program_form_bank_page={int(program.metadata.get('form_bank_variation_page') or 0)}",
                "geometry_program_synthesis_request_source=universal_form_bank_control",
                "geometry_program_vlm_status=not_requested_pre_program",
                "geometry_program_llm_author_status=not_requested_pre_program",
                "geometry_program_llm_author_active=False",
                "geometry_program_prebook_vlm_quarantined=False",
            ))
            seeds.append(replace(
                source,
                name=(
                    f"{source.name}__universal_{source_index}_{program_index}_"
                    f"{program.program_hash()[:10]}"
                ),
                notes=notes,
            ))

    # Explicit session mutations remain additive. They are feedback requests,
    # not the default control population and cannot replace the universal bank.
    directive_requests = tuple({
        **dict(request),
        "synthesis_request_source": "vlm_or_session_directive",
        "site_access_side": str(
            request.get("site_access_side")
            or (_site_access_side_in_principal_frame(site, site_access_geometry) if site is not None else "closed")
        ),
    } for request in (synthesis_requests or ()) if isinstance(request, dict))
    effective_synthesis_requests = tuple((
        *directive_requests,
    ))

    # A synthesis request describes architectural intent and normalized base
    # seeds.  The agent expands it into recursive ASTs; unlike the legacy
    # geometry_program registry, no named completed-form record is selected.
    for request_index, request in enumerate(effective_synthesis_requests):
        if not isinstance(request, dict):
            continue
        source = originals.get(str(request.get("source_seed") or ""))
        if source is None:
            continue
        programs = synthesize_architectural_programs(request, building_type=building_type)
        vlm_status = "not_requested"
        llm_author_status = "not_requested"
        live_prebook_vlm_requested = bool(request.get("live_vlm_revision"))
        llm_author_requested = bool(request.get("live_llm_author")) or str(
            request.get("synthesis_request_source") or ""
        ) == "openai_vlm_experimental"
        llm_author_only = bool(request.get("llm_author_only")) or (
            llm_author_requested and not live_prebook_vlm_requested
        )
        if live_prebook_vlm_requested or llm_author_requested:
            live_opt_in = os.getenv("MAAS_LIVE_GEOMETRY_VLM", "").strip().lower() in {"1", "true", "yes", "on"}
            rotated_credential_confirmed = os.getenv("MAAS_LIVE_VLM_CREDENTIAL_ROTATED", "").strip().lower() in {"1", "true", "yes", "on"}
            if live_prebook_vlm_requested and not live_opt_in:
                vlm_status = "inactive_requires_explicit_MAAS_LIVE_GEOMETRY_VLM_opt_in"
            elif live_prebook_vlm_requested and not rotated_credential_confirmed:
                vlm_status = "inactive_requires_rotated_credential_confirmation"
            elif (
                not os.getenv("OPENAI_API_KEY")
                and not os.getenv(
                    "MAAS_GEOMETRY_AUTHOR_REPLAY_CACHE_PATH"
                )
            ):
                vlm_status = "inactive_missing_rotated_environment_key"
            else:
                try:
                    reference_contract = {
                        **program_reference_contract(building_type),
                        "program_dimensional_context": dict(program_dimensional_context or {}),
                        "base_capacity_contract": dict(base_capacity_contract or {}),
                        "site_boundary_source": site_boundary_source,
                        "site_access_context": dict(site_access_context or {}),
                        "site_access_side_in_program_frame": str(request.get("site_access_side") or "closed"),
                    }
                    explicit_reference_matches = [
                        item for item in (request.get("reference_matches") or ())
                        if isinstance(item, dict)
                    ]
                    # Reference understanding precedes geometry authorship.
                    # Feed the LLM only VLM-audited, coordinate-free massing
                    # relations; the downstream critic still sees the actual
                    # images and remains the selection authority.
                    reference_matches: list[dict[str, Any]] = []
                    reference_language_context: dict[str, Any] = {
                        "schema_version": "arr.maas.reference_vlm_author_context.v1",
                        "status": "not_available",
                        "selection_authority": "none_author_prior_only",
                        "references": [],
                    }
                    if programs and not llm_author_only:
                        reference_matches, reference_language_audit = _audited_final_book_references(
                            programs[0],
                            building_type=building_type,
                            explicit_matches=explicit_reference_matches,
                        )
                        reference_language_context = _reference_language_author_context(
                            reference_matches,
                            reference_language_audit,
                        )
                    llm_author_context = {
                        "schema_version": "arr.maas.geometry_llm_author_context.v1",
                        "building_type": building_type,
                        "program_context": reference_contract,
                        "base_capacity_contract": dict(base_capacity_contract or {}),
                        "source_program_seed": source.name,
                        "base_seeds": list(request.get("base_seeds") or ()),
                        "intent_tags": list(request.get("intent_tags") or ()),
                        "maximum_operator_depth": max(1, min(3, int(request.get("maximum_operator_depth") or 2))),
                        "downstream_body_rule_reserve": max(
                            0,
                            min(2, int(request.get("downstream_body_rule_reserve") or 0)),
                        ),
                        "site_relation": {
                            "boundary_source": site_boundary_source,
                            "access_side_in_program_frame": str(request.get("site_access_side") or "closed"),
                            "coordinates_available_to_author": False,
                        },
                        "reference_vlm_language": reference_language_context,
                        "outcome_graph_memory": (
                            outcome_graph.author_context(
                                source_seed=source.name,
                                program_slug=building_type,
                                program_aliases=tuple(sorted({
                                    building_type,
                                    next(
                                        (slug for slug, label, _height, _floors in PROGRAMS if label == building_type),
                                        building_type,
                                    ),
                                    str(reference_contract.get("program_id") or ""),
                                })),
                            )
                            if outcome_graph is not None
                            else {
                                "schema_version": "arr.maas.geometry_author_context.v1",
                                "observation_count": 0,
                                "status": "no_prior_observation",
                            }
                        ),
                        "instruction": (
                            "author materially different recursive solid ASTs; references are reviewed "
                            "later by the image-grounded VLM critic; no parcel coordinates or completed form"
                        ),
                    }
                    if llm_author_requested:
                        try:
                            llm_authored = author_geometry_programs_with_openai(
                                llm_author_context,
                                target_count=max(
                                    1,
                                    min(12, int(request.get("llm_author_count") or 8)),
                                ),
                                model=str(request.get("llm_author_model") or "") or None,
                            )
                            llm_authored = tuple(replace(item, metadata={
                                **item.metadata,
                                "reference_vlm_author_context": reference_language_context,
                                "reference_vlm_precedes_author": bool(
                                    reference_language_context.get("status")
                                    not in {"", "not_available"}
                                ),
                                "llm_geometry_author_active": True,
                            }) for item in llm_authored)
                            if llm_author_only:
                                programs = tuple(llm_authored)
                            else:
                                unique_programs = {
                                    program.program_hash(): program
                                    for program in programs
                                }
                                for authored in llm_authored:
                                    unique_programs.setdefault(
                                        authored.program_hash(),
                                        authored,
                                    )
                                programs = tuple(unique_programs.values())
                            llm_author_status = (
                                f"completed:{len(llm_authored)}:"
                                f"cache_hits={sum(bool(item.metadata.get('author_cache_hit')) for item in llm_authored)}"
                            )
                        except GeometryAuthorError as exc:
                            # The deterministic control population remains in the
                            # additive lane; a failed external author is explicit
                            # evidence and never replaced with fabricated DSL.
                            llm_author_status = f"error:{type(exc).__name__}:{str(exc)[:160]}"
                            logger.warning(
                                "LLM geometry author request failed: %s",
                                llm_author_status,
                            )
                    if llm_author_only:
                        raise _PostBookVlmOnly
                    seed_source = (
                        compile_sequence_to_source_mass(site, source)
                        if site is not None
                        else None
                    )
                    capacity_target_plan_area = float(
                        (base_capacity_contract or {}).get("target_base_plan_area_m2") or 0.0
                    )
                    target_plan_area = (
                        capacity_target_plan_area
                        if capacity_target_plan_area > 0.0
                        else (
                            float(seed_source.footprint.area)
                            if seed_source is not None
                            else None
                        )
                    )

                    def render_site_conditioned_preview(
                        program: GeometryProgram,
                        _compilation: Any,
                        output_path: Path,
                    ) -> Path:
                        if site is None:
                            from design.maas.geometry_language import render_compilation_preview
                            return render_compilation_preview(_compilation, output_path, title=program.name)
                        preview_source = compile_geometry_program_to_source_mass(
                            program,
                            site,
                            target_plan_area=target_plan_area,
                            name=f"vlm_preview__{program.name}",
                            max_volume_bands=3,
                        )
                        if preview_source is None:
                            from design.maas.geometry_language import render_compilation_preview
                            return render_compilation_preview(_compilation, output_path, title=program.name)
                        preview_feature = source_feature(
                            preview_source,
                            source,
                            building_type=building_type,
                            height=height,
                            floors=floors,
                            site_area=float(site.area),
                        )
                        props = preview_feature.setdefault("properties", {})
                        props["site_boundary_geometry"] = mapping(site)
                        props["site_boundary_source"] = site_boundary_source
                        props["site_access_context"] = dict(site_access_context or {})
                        props["site_access_geometry"] = site_access_geometry
                        props["program_context"] = reference_contract
                        props["base_capacity_contract"] = dict(base_capacity_contract or {})
                        props["preview_target_plan_area_m2"] = target_plan_area
                        return feature_preview_png(preview_feature, output_path.parent)

                    prebook_parent_programs = tuple(programs)
                    loop = run_geometry_program_a2a_loop(
                        context={
                            "building_type": building_type,
                            "intent_tags": list(request.get("intent_tags") or ()),
                            "base_seeds": list(request.get("base_seeds") or ()),
                            "base_capacity_contract": dict(base_capacity_contract or {}),
                            "instruction": "critic must propose typed node edits, never a completed mesh",
                        },
                        target_count=len(programs),
                        author_programs=lambda _context, authored=programs: authored,
                        critic_program=openai_vlm_geometry_critic(
                            reference_provider=lambda program, explicit=reference_matches: retrieve_geometry_reference_matches(
                                program,
                                building_type=building_type,
                                explicit_matches=explicit,
                                # The image-suitability audit can reject
                                # interiors and close facade shots. Retrieve a
                                # deeper program-specific pool so at least
                                # three whole-building massing views remain.
                                # The reference-image VLM will reject interiors,
                                # detail shots and incompatible building scales.
                                # Search deeply enough that the unchanged
                                # three-image program evidence contract can be
                                # satisfied by whole-building views.
                                limit=max(24, min(32, int(request.get("reference_limit") or 24))),
                            ),
                            memory_provider=(
                                 lambda program: outcome_graph.agent_neighborhood(
                                     source_seed=source.name,
                                     program_hash=program.program_hash(),
                                     program_slug=building_type,
                                     program_aliases=tuple(sorted({
                                         building_type,
                                         str(reference_contract.get("program_id") or ""),
                                     })),
                                 )
                                if outcome_graph is not None
                                else {}
                            ),
                            building_type=building_type,
                            program_context=reference_contract,
                            model=str(request.get("vlm_model") or "") or None,
                        ),
                        max_generations=max(1, min(3, int(request.get("vlm_generations") or 2))),
                        gate_policy=GeometryGatePolicy(maximum_components=1),
                        author_provider=(
                            "bounded_procedural_plus_openai_llm"
                            if any(
                                item.metadata.get("author_provider") == "openai_llm_geometry_author"
                                for item in programs
                            )
                            else "bounded_procedural_geometry_agent"
                        ),
                        critic_provider="openai_vlm",
                        preview_renderer=render_site_conditioned_preview,
                    )
                    if outcome_graph is not None:
                        outcome_graph.observe_vlm_loop(
                            program_slug=building_type,
                            source_seed=source.name,
                            trace=loop.trace,
                        )
                    archive_programs = tuple(replace(
                            candidate.program,
                            metadata={
                                **candidate.program.metadata,
                                "vlm_critic_score": round(float(candidate.critic_score), 4),
                                "vlm_revision_generation": int(candidate.generation),
                                "vlm_geometry_critic_active": True,
                                "vlm_geometry_revision_count": int(loop.trace.get("geometry_revision_count") or 0),
                                "vlm_unique_geometry_count": int(loop.trace.get("unique_geometry_count") or 0),
                                "vlm_model": str(candidate.critic_payload.get("model") or ""),
                                "vlm_response_id": str(candidate.critic_payload.get("response_id") or ""),
                                "vlm_program_fit_hard_pass": bool(
                                    candidate.critic_payload.get("program_fit_hard_pass", True)
                                ),
                                "vlm_program_appropriateness": float(
                                    (candidate.critic_payload.get("concept_scores") or {}).get("program_appropriateness") or 0.0
                                ),
                                "vlm_section_program_fit": float(
                                    (candidate.critic_payload.get("concept_scores") or {}).get("section_program_fit") or 0.0
                                ),
                                "vlm_reference_assessments": list(
                                    candidate.critic_payload.get("reference_assessments") or ()
                                ),
                                "vlm_reference_count": len(
                                    ((candidate.critic_payload.get("maas_causal_context") or {}).get("reference_matches") or ())
                                ),
                                "vlm_memory_observation_count": int(
                                    (((candidate.critic_payload.get("maas_causal_context") or {}).get("outcome_memory") or {}).get("observation_count") or 0)
                                ),
                                "llm_geometry_author_active": bool(
                                    candidate.program.metadata.get("author_provider") == "openai_llm_geometry_author"
                                ),
                                "llm_geometry_author_model": str(
                                    candidate.program.metadata.get("author_model") or ""
                                ),
                                "llm_geometry_author_response_id": str(
                                    candidate.program.metadata.get("author_response_id") or ""
                                ),
                            },
                        ) for candidate in loop.archive)
                    quarantined_programs = _prebook_vlm_quarantined_llm_parents(
                        prebook_parent_programs,
                        loop.trace,
                    )
                    unique_programs = {
                        program.program_hash(): program
                        for program in archive_programs
                    }
                    for program in quarantined_programs:
                        unique_programs.setdefault(program.program_hash(), program)
                    # Quarantine is candidate supply only. Every such parent
                    # must still pass BOOK projection, clean/program/legal
                    # gates and the exact post-BOOK VLM hard gate; it receives
                    # no positive score or final-selection authority here.
                    programs = tuple(unique_programs.values())
                    vlm_status = str(loop.trace.get("status") or "completed")
                except _PostBookVlmOnly:
                    vlm_status = "deferred_to_exact_post_book_final_solid"
                except Exception as exc:
                    # The deterministic graph author and hard gates remain
                    # usable when an external critic is unavailable. Record
                    # the failure; never fabricate a synthetic VLM score.
                    vlm_status = f"error:{type(exc).__name__}"
                    logger.warning(
                        "Geometry author/VLM synthesis stage failed: %s: %s",
                        type(exc).__name__,
                        str(exc)[:300],
                    )
        # Legal compliance must not silently author a second geometry on top
        # of the typed recursive program.  The former 0.25..1.0 frame blend
        # changed every vertex as a function of height and collapsed diverse
        # programs into one tapered/wedge family.  Legal adaptation remains in
        # the downstream hard-gate lane (bounded scale/translate, clipping and
        # measured retention); this synthesis lane always preserves the AST.
        fallback_strengths = (0.0,)
        for program_index, program in enumerate(programs):
            # Do not allow historic outcome-graph observations from the old
            # tapering policy to reintroduce a non-zero frame blend.
            strengths = fallback_strengths
            payload = json.dumps(program.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            family = str(program.metadata.get("family") or "agent_recursive")
            for strength_index, legal_fit_strength in enumerate(strengths):
                notes = tuple((*source.notes,
                    f"geometry_program_payload={payload}",
                    f"geometry_program_source_seed={source.name}",
                    "geometry_program_edits=[]",
                    f"geometry_program_rationale=agent synthesis from normalized base and intent tags: {','.join(program.metadata.get('intent_tags') or ())}",
                    f"geometry_program_legal_fit_strength={legal_fit_strength}",
                    "geometry_program_source=procedural_geometry_synthesis_agent",
                    f"geometry_program_synthesis_request_source={str(request.get('synthesis_request_source') or 'program_profile_control')}",
                    f"geometry_program_vlm_status={vlm_status}",
                    f"geometry_program_vlm_reference_count={int(program.metadata.get('vlm_reference_count') or 0)}",
                    f"geometry_program_vlm_memory_observation_count={int(program.metadata.get('vlm_memory_observation_count') or 0)}",
                    f"geometry_program_vlm_revision_count={int(program.metadata.get('vlm_geometry_revision_count') or 0)}",
                    f"geometry_program_llm_author_status={llm_author_status}",
                    f"geometry_program_llm_author_active={bool(program.metadata.get('llm_geometry_author_active'))}",
                    f"geometry_program_prebook_vlm_quarantined={bool(program.metadata.get('pre_book_vlm_quarantined'))}",
                ))
                seeds.append(replace(
                    source,
                    name=(
                        f"{source.name}__synth_{request_index}_{program_index}_{strength_index}_"
                        f"{family}_{program.program_hash()[:10]}"
                    ),
                    notes=notes,
                ))
    # A cost-bounded smoke run may stop after three floor-valid candidates.
    # Put explicitly requested paid authorship at the front so the large
    # deterministic control bank cannot consume the whole smoke budget before
    # the authored AST is even compiled. This grants review opportunity only;
    # every authored candidate still faces BOOK, legal, FAR, parking and VLM.
    if any(
        bool(request.get("live_llm_author"))
        for request in effective_synthesis_requests
        if isinstance(request, dict)
    ):
        seeds.sort(key=lambda sequence: (
            not any(
                note == "geometry_program_llm_author_active=True"
                for note in sequence.notes
            ),
        ))
    return tuple(seeds)


def _prebook_vlm_quarantined_llm_parents(
    parents: tuple[GeometryProgram, ...],
    trace: dict[str, Any],
) -> tuple[GeometryProgram, ...]:
    """Retain clean LLM parents only as exact-post-BOOK repair supply.

    A pre-BOOK critic sees neither BOOK scope nor the final projected solid.
    Its rejection remains negative evidence, but deleting the genotype here
    prevents the authoritative exact-post-BOOK critic from testing whether a
    typed BOOK mutation resolves that failure. Quarantined parents therefore
    carry zero selection authority until every downstream hard gate passes.
    """
    rejected_records = {
        str(record.get("program_hash") or ""): record
        for generation in trace.get("generations") or ()
        if isinstance(generation, dict)
        for record in generation.get("records") or ()
        if isinstance(record, dict)
        and record.get("status") == "critic_program_fit_rejected"
        and record.get("program_hash")
    }
    quarantined: list[GeometryProgram] = []
    for program in parents:
        if program.metadata.get("author_provider") != "openai_llm_geometry_author":
            continue
        program_hash = program.program_hash()
        record = rejected_records.get(program_hash)
        if record is None:
            continue
        compilation = compile_geometry_program(program)
        if compilation.status != "compiled" or compilation_gate(
            compilation,
            GeometryGatePolicy(maximum_components=1),
        ):
            continue
        quarantined.append(replace(program, metadata={
            **program.metadata,
            "vlm_geometry_critic_active": True,
            "vlm_program_fit_hard_pass": False,
            "pre_book_vlm_quarantined": True,
            "pre_book_vlm_response_id": str(record.get("critic_response_id") or ""),
            "pre_book_vlm_critic_actions": list(record.get("critic_actions") or ()),
            "pre_book_vlm_concept_scores": {
                "program_appropriateness": float(record.get("program_appropriateness") or 0.0),
                "section_program_fit": float(record.get("section_program_fit") or 0.0),
            },
            "pre_book_vlm_quarantine_selection_authority": "none_until_exact_final_vlm_hard_pass",
            "pre_book_vlm_quarantine_reason": "critic_program_fit_rejected_before_book_projection",
            "llm_geometry_author_active": True,
        }))
    return tuple(quarantined)


def _geometry_program_registry() -> dict[str, Any]:
    references = reference_language_programs()
    programs = tuple((*references.values(), *architectural_shape_programs()))
    registry: dict[str, Any] = dict(references)
    for program in programs:
        family = str(program.metadata.get("family") or "")
        for key in (program.name, family):
            if key:
                registry.setdefault(key, program)
    return registry


def _body_program_for_book_projection(
    program: GeometryProgram,
    sequence: VerbSequence,
) -> GeometryProgram:
    if (
        program.metadata.get("author_provider")
        == "openai_llm_geometry_author"
        or program.metadata.get("llm_geometry_author_active") is True
    ):
        return program
    return apply_book_projection_to_geometry_program(program, sequence)


def _program_projection_evidence(
    program: GeometryProgram,
    bridge_evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    evidence = recursive_book_projection_evidence(program, bridge_evidence)
    if evidence:
        return evidence
    if not (
        program.metadata.get("author_provider")
        == "openai_llm_geometry_author"
        or program.metadata.get("llm_geometry_author_active") is True
    ):
        return {}
    bridge = dict(bridge_evidence or {})
    status = (
        "materialized"
        if bridge.get("status") == "materialized"
        and bridge.get("geometry_hash")
        else "compile_failed"
    )
    return {
        "schema_version": "arr.maas.program_book_projection.v2",
        "status": status,
        "projection_kind": "direct_llm_authored_ast",
        "geometry_authority": "llm_authored_recursive_manifold_ast",
        "legacy_source_projection_bypassed": True,
        "operations": [],
        "scope": {
            "node_id": program.root_id,
            "relation": "authored_base_volume_program",
            "base_volume_label": "llm_authored",
            "requested_fraction": None,
            "topology": "authored_ast",
            "orientation": "authored",
        },
        "author_response_id": str(
            program.metadata.get("author_response_id") or ""
        ),
        "authoritative_program_hash": str(
            bridge.get("program_hash") or program.program_hash()
        ),
        "authoritative_geometry_hash": str(
            bridge.get("geometry_hash") or ""
        ),
        "projection_graph": {
            "schema_version": "arr.maas.book_projection_graph.v2",
            "nodes": [],
        },
    }


_AUTHORED_PROJECTION_MAX_SILHOUETTE_DISTANCE = 0.40
def _allow_tiny_geometry_gates() -> bool:
    """Check whether tiny-geometry gate relaxations are allowed."""

    return os.getenv("MAAS_ALLOW_TINY_GEOMETRY_GATES", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
_AUTHORED_STEP_OPERATORS = frozenset({
    "book_grade",
    "setback",
    "stack",
    "stepped_mass",
    "terrace",
})


def _authored_projection_identity_evidence(
    authored_source: Any,
    projected_source: Any,
    *,
    enforce_morphology_preservation: bool = True,
) -> dict[str, Any]:
    """Fail closed when legal fitting invents a different visible body type.

    ``enforce_morphology_preservation`` remains as a compatibility argument for
    older diagnostic callers. It no longer disables the final-MASS identity
    gate; diagnostics may observe a collapsed projection but may not select it.
    """

    del enforce_morphology_preservation

    authored_metrics = _solid_morphology_metrics(
        SimpleNamespace(source=authored_source)
    )
    projected_metrics = _solid_morphology_metrics(
        SimpleNamespace(source=projected_source)
    )
    program = authored_source.metadata.get("geometry_program")
    program = program if isinstance(program, dict) else {}
    authored_operators = {
        str(node.get("operator") or "")
        for node in (program.get("nodes") or ())
        if isinstance(node, dict)
    }
    authored_step_intent = bool(
        authored_operators & _AUTHORED_STEP_OPERATORS
    )
    authored_step_visible = bool(
        authored_metrics.get("visible_stepped")
        or authored_metrics.get("pyramidal_like")
    )
    projected_step_visible = bool(
        projected_metrics.get("visible_stepped")
        or projected_metrics.get("pyramidal_like")
    )
    silhouette_distance = float(
        intrinsic_silhouette_distance(
            authored_source,
            projected_source,
        )
    )
    visual_certificate = projected_source.metadata.get(
        "floorwise_visual_projection"
    )
    visual_certificate = (
        visual_certificate
        if isinstance(visual_certificate, dict)
        else {}
    )
    failures: list[str] = []
    if (
        projected_step_visible
        and not authored_step_visible
        and not authored_step_intent
    ):
        failures.append("unrequested_legal_step_collapse")
    if (
        silhouette_distance > _AUTHORED_PROJECTION_MAX_SILHOUETTE_DISTANCE
        and not authored_step_intent
    ):
        failures.append(
            "authored_projection_silhouette_distance_exceeded"
        )
    if (
        visual_certificate.get("visible_step_fallback") is True
        and not authored_step_intent
    ):
        failures.append("unrequested_visible_step_fallback")
    return {
        "schema_version": "arr.maas.authored_projection_identity.v1",
        "status": "pass" if not failures else "fail",
        "hard_pass": not failures,
        "failure_reasons": failures,
        "authored_program_operators": sorted(authored_operators),
        "authored_step_intent": authored_step_intent,
        "authored_phenotype": str(
            authored_metrics.get("phenotype") or ""
        ),
        "projected_phenotype": str(
            projected_metrics.get("phenotype") or ""
        ),
        "authored_visible_stepped": bool(
            authored_metrics.get("visible_stepped")
        ),
        "projected_visible_stepped": bool(
            projected_metrics.get("visible_stepped")
        ),
        "authored_pyramidal_like": bool(
            authored_metrics.get("pyramidal_like")
        ),
        "projected_pyramidal_like": bool(
            projected_metrics.get("pyramidal_like")
        ),
        "silhouette_distance": round(silhouette_distance, 6),
        "maximum_silhouette_distance": (
            _AUTHORED_PROJECTION_MAX_SILHOUETTE_DISTANCE
        ),
        "visible_step_fallback": bool(
            visual_certificate.get("visible_step_fallback")
        ),
        "identity_policy": (
            "preserve_pose_invariant_top_front_side_figure_and_do_not_"
            "invent_step_or_pyramid_morphology"
        ),
    }


def _materialize_directed_geometry(
    source: Any,
    sequence: VerbSequence,
    *,
    containment_host: Polygon | None = None,
    upper_containment_host: Polygon | None = None,
    floor_containment_hosts: tuple[Polygon | None, ...] = (),
    minimum_host_plan_coverage: float = 0.0,
    capacity_composition_utilizations: tuple[float, float] | None = None,
    floor_capacity_plan_hash: str = "",
    target_floor_areas_m2: tuple[float, ...] = (),
    building_type: str = "",
    site_access_side: str = "closed",
    pnu: str = "",
    capacity_alternative_id: str = "",
    achieved_capacity_band: str = "",
    capacity_measurement_hash: str = "",
    site_context_hash: str = "",
    legal_floor_field_hash: str = "",
) -> Any | None:
    directive = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_directive=")
    ), "")
    raw_payload = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_payload=")
    ), "")
    if not directive and not raw_payload:
        return source
    raw_fit_strength = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_legal_fit_strength=")
    ), "0")
    try:
        fit_strength = max(0.0, min(1.0, float(raw_fit_strength)))
    except (TypeError, ValueError):
        return None
    if raw_payload:
        try:
            program = GeometryProgram.from_dict(json.loads(raw_payload))
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
    else:
        program = _geometry_program_registry().get(directive)
    if program is None:
        return None
    raw_edits = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_edits=")
    ), "[]")
    try:
        edit_records = json.loads(raw_edits)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if edit_records:
        safe_mutation = apply_geometry_edits_compiler_safe(program, edit_records)
        mutation = safe_mutation.mutation
        if mutation.status != "revised" or mutation.program is None:
            return None
        program = mutation.program
    # BOOK p.3 scope and ordered operations must mutate the same recursive
    # manifold later rendered and gated. The old SourceMass projection remains
    # as program/legal evidence, but it is no longer the geometry authority.
    try:
        program = _body_program_for_book_projection(
            program,
            sequence,
        )
        book_geometry_program = program
        semantic_program = project_program_requirements(
            book_geometry_program,
            building_type=building_type,
            access_side=site_access_side,
        )
        bind_source_role_scaffold_to_program(
            semantic_program,
            source,
            program_id=building_type,
        )
        # At MASS, program relations are certified semantic carriers over the
        # legal floor bands. They must not silently replace the authored
        # BaseVolume→BOOK body with a near-complete program template before
        # plan design. The visible authority therefore remains the BOOK AST.
        program = book_geometry_program
    except (TypeError, ValueError):
        return None
    if program is None:
        return None
    legal_sections = tuple(floor_containment_hosts)
    if (
        not isinstance(containment_host, Polygon)
        or not legal_sections
        or len(legal_sections) != len(target_floor_areas_m2)
        or not floor_capacity_plan_hash.strip()
        or any(
            not isinstance(section, Polygon)
            or section.is_empty
            or not section.is_valid
            or float(section.area) <= 1e-9
            for section in legal_sections
        )
    ):
        return None
    authored_program = program
    authored_compilation = compile_geometry_program(authored_program)
    if (
        authored_compilation.status != "compiled"
        or compilation_gate(
            authored_compilation,
            GeometryGatePolicy(maximum_components=1),
        )
    ):
        return None
    if not source.volumes:
        return None
    primary_volume_role = max(
        source.volumes,
        key=lambda volume: (
            float(volume.footprint.area)
            * (
                float(volume.top_fraction)
                - float(volume.bottom_fraction)
            )
        ),
    ).role
    target_areas = tuple(float(value) for value in target_floor_areas_m2)
    legal_field_selection = select_legal_field_affine_projection(
        authored_program,
        legal_sections=legal_sections,
        target_floor_areas_m2=target_floor_areas_m2,
        floor_capacity_plan_hash=floor_capacity_plan_hash,
        aggregate_target_area_m2=sum(target_areas),
        maximum_exact_candidates=4,
        minimum_aggregate_target_ratio=0.35,
    )
    final_projection_book_program = authored_program
    if legal_field_selection is None:
        candidate_floor_context = (
            source.metadata.get("candidate_floor_context")
            if isinstance(
                source.metadata.get("candidate_floor_context"),
                dict,
            )
            else {}
        )
        try:
            candidate_height_m = float(
                candidate_floor_context.get("height_m")
            )
            candidate_floor_count = int(
                candidate_floor_context.get("floors")
            )
        except (TypeError, ValueError):
            return None
        if (
            not isfinite(candidate_height_m)
            or candidate_height_m <= 0.0
            or candidate_floor_count != len(legal_sections)
        ):
            return None
        authored_source = compile_geometry_program_to_source_mass(
            authored_program,
            legal_sections[0],
            upper_host=legal_sections[-1],
            upper_fit_strength=fit_strength,
            target_plan_area=target_areas[0],
            name=f"{source.name}__authored_{authored_program.name}",
            volume_role=primary_volume_role,
            max_volume_bands=max(3, len(legal_sections)),
        )
        if authored_source is None:
            return None
        authored_source = replace(
            authored_source,
            metadata={
                **authored_source.metadata,
                "candidate_floor_context": deepcopy(candidate_floor_context),
            },
        )
        materialized = materialize_floorwise_legal_source(
            authored_source,
            legal_sections=legal_sections,
            target_plan_coverage=minimum_host_plan_coverage,
            floor_capacity_plan_hash=floor_capacity_plan_hash,
            target_floor_areas_m2=target_areas,
        )
        if materialized is None:
            return None
        authored_projection_identity = (
            _authored_projection_identity_evidence(
                authored_source,
                materialized,
            )
        )
        if not authored_projection_identity["hard_pass"]:
            logger.info(
                "Rejecting authored legal projection identity collapse: %s",
                authored_projection_identity,
            )
            return None
        try:
            execution_program = floorwise_source_to_geometry_program(
                materialized,
                height_m=candidate_height_m,
                name=f"{authored_program.name}__final_legal_projection",
                allow_tiny_footprint=_allow_tiny_geometry_gates(),
            )
        except ValueError as exc:
            if str(exc) != "floorwise volume has no replayable footprint":
                raise
            logger.info(
                "Rejecting authored projection replay serialization: %s",
                exc,
            )
            return None
        execution_program = bind_source_role_scaffold_to_program(
            execution_program,
            source,
            program_id=building_type,
        )
        final_compilation = compile_geometry_program(execution_program)
        final_compilation_gate_policy = GeometryGatePolicy(
            maximum_components=8
            if _allow_tiny_geometry_gates()
            else 1,
            minimum_edge_length=1e-8
            if _allow_tiny_geometry_gates()
            else 1e-5,
            minimum_triangle_area=1e-12
            if _allow_tiny_geometry_gates()
            else 1e-10
        )
        final_compilation_gate_issues = compilation_gate(
            final_compilation,
            final_compilation_gate_policy,
        )
        if (
            _allow_tiny_geometry_gates()
            and final_compilation_gate_issues
            and all(
                issue.code in {"tiny_face", "tiny_edge"}
                for issue in final_compilation_gate_issues
            )
        ):
            final_compilation_gate_issues = ()
        if (
            final_compilation.status != "compiled"
            or final_compilation_gate_issues
        ):
            logger.info(
                "Rejecting authored projection replay compilation: "
                "status=%s compile_issues=%s gate_issues=%s transport=%s",
                final_compilation.status,
                [
                    issue.to_dict()
                    for issue in final_compilation.issues
                ][:8],
                [
                    issue.to_dict()
                    for issue in final_compilation_gate_issues
                ][:8],
                deepcopy(
                    (final_compilation.metrics or {}).get(
                        "capacity_replay_numeric_transport"
                    )
                    or {}
                ),
            )
            return None
        final_program_hash = execution_program.program_hash()
        final_geometry_hash = final_floorwise_visual_geometry_hash(
            materialized
        )
        band_areas: dict[tuple[float, float], float] = {}
        for volume in materialized.volumes:
            band = (
                float(volume.bottom_fraction),
                float(volume.top_fraction),
            )
            band_areas[band] = (
                band_areas.get(band, 0.0)
                + float(volume.footprint.area)
            )
        achieved_floor_areas = tuple(
            band_areas[band]
            for band in sorted(band_areas)
        )
        projection_evidence = deepcopy(
            materialized.metadata.get("floorwise_legal_matrix_stack")
            or {}
        )
        projection_evidence.update({
            "projection_mode": (
                "floorwise_matrix_field_authored_mesh_preserved"
            ),
            "hard_pass": True,
            "final_program_hash": final_program_hash,
            "final_geometry_hash": final_geometry_hash,
        })
        fallback_metadata = deepcopy(materialized.metadata)
        fallback_metadata["authored_projection_identity"] = deepcopy(
            authored_projection_identity
        )
        final_surface_payload_hash = source_surface_payload_hash(
            tuple(materialized.surfaces)
        )
        final_proxy_volume_payload_hash = source_volume_payload_hash(
            tuple(materialized.volumes)
        )
        proxy_band_counts = Counter(
            (
                float(volume.bottom_fraction),
                float(volume.top_fraction),
            )
            for volume in materialized.volumes
        )
        proxy_band_part_counts = tuple(
            proxy_band_counts[band]
            for band in sorted(proxy_band_counts)
        )
        fallback_metadata["final_surface_payload_hash"] = (
            final_surface_payload_hash
        )
        fallback_metadata["final_proxy_volume_payload_hash"] = (
            final_proxy_volume_payload_hash
        )
        final_compilation_payload = final_compilation.to_dict(
            include_mesh=False
        )
        final_compilation_payload["geometry_hash"] = final_geometry_hash
        fallback_metadata["geometry_program"] = execution_program.to_dict()
        fallback_metadata["geometry_program_compilation"] = (
            final_compilation_payload
        )
        fallback_metadata["mass_execution_passport"] = deepcopy(
            final_compilation_payload.get("execution_passport") or {}
        )
        fallback_metadata["geometry_graph_notes"] = (
            build_geometry_graph_notes(
                execution_program,
                final_compilation,
            )
        )
        fallback_metadata["geometry_graph_snapshot"] = (
            build_geometry_graph_snapshot(
                execution_program,
                final_compilation,
            )
        )
        fallback_bridge = deepcopy(
            fallback_metadata.get("geometry_program_bridge_evidence")
            or {}
        )
        fallback_bridge.update({
            "program_hash": final_program_hash,
            "geometry_hash": final_geometry_hash,
            "surface_payload_hash": final_surface_payload_hash,
            "raw_mesh_triangle_count": len(materialized.surfaces),
            "exported_surface_count": len(materialized.surfaces),
            "surface_export_complete": bool(materialized.surfaces),
            "proxy_volume_payload_hash": final_proxy_volume_payload_hash,
            "requested_proxy_band_count": len(proxy_band_counts),
            "exported_proxy_band_count": len(proxy_band_counts),
            "exported_proxy_part_count": len(materialized.volumes),
            "proxy_volume_count": len(materialized.volumes),
            "proxy_band_part_counts": list(proxy_band_part_counts),
            "geometry_authority": (
                "final_floorwise_legal_geometry_program"
            ),
            "upstream_authored_program_hash": (
                authored_program.program_hash()
            ),
            "upstream_authored_geometry_hash": (
                authored_compilation.geometry_hash
            ),
        })
        fallback_metadata["geometry_program_bridge_evidence"] = (
            fallback_bridge
        )
        materialized = replace(
            materialized,
            metadata=fallback_metadata,
        )
    else:
        projected = legal_field_selection.projection
        if projected.certificate.get("hard_pass") is not True:
            return None
        materialized = compile_site_bound_geometry_program_to_source_mass(
            projected.program,
            containment_host,
            name=f"{source.name}__geometry_{projected.program.name}",
            volume_role=primary_volume_role,
        )
        if materialized is None:
            return None
        final_projection_book_program = projected.program
        final_program_hash = projected.program.program_hash()
        final_geometry_hash = str(
            projected.certificate.get("final_geometry_hash") or ""
        )
        achieved_floor_areas = tuple(
            float(value)
            for value in (
                projected.certificate.get("achieved_floor_areas_m2")
                or ()
            )
        )
        projection_evidence = deepcopy(legal_field_selection.evidence)
    bridge = (
        materialized.metadata.get("geometry_program_bridge_evidence")
        if isinstance(
            materialized.metadata.get("geometry_program_bridge_evidence"),
            dict,
        )
        else {}
    )
    compilation = (
        materialized.metadata.get("geometry_program_compilation")
        if isinstance(
            materialized.metadata.get("geometry_program_compilation"),
            dict,
        )
        else {}
    )
    if (
        not final_program_hash
        or not final_geometry_hash
        or str(bridge.get("program_hash") or "") != final_program_hash
        or str(bridge.get("geometry_hash") or "") != final_geometry_hash
        or str(compilation.get("geometry_hash") or "") != final_geometry_hash
    ):
        logger.info(
            "Rejecting authored projection identity binding mismatch: %s",
            {
                "final_program_hash": final_program_hash,
                "final_geometry_hash": final_geometry_hash,
                "bridge_program_hash": str(
                    bridge.get("program_hash") or ""
                ),
                "bridge_geometry_hash": str(
                    bridge.get("geometry_hash") or ""
                ),
                "compilation_geometry_hash": str(
                    compilation.get("geometry_hash") or ""
                ),
            },
        )
        return None
    requested_floor_area = sum(float(value) for value in target_floor_areas_m2)
    achieved_floor_area = sum(achieved_floor_areas)
    requested_capacity_satisfied = bool(
        requested_floor_area > 0.0
        and achieved_floor_area + 1e-7 >= requested_floor_area * 0.995
    )
    source_seed = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_source_seed=")
    ), "")
    metadata = {
        **deepcopy(source.metadata),
        **deepcopy(materialized.metadata),
    }
    bridge = deepcopy(metadata.get("geometry_program_bridge_evidence") or {})
    bridge["source_seed"] = source_seed
    bridge["author_provider"] = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_source=")
    ), "unknown")
    bridge["geometry_authority"] = "final_floorwise_legal_geometry_program"
    bridge["upstream_authored_program_hash"] = authored_program.program_hash()
    bridge["upstream_authored_geometry_hash"] = authored_compilation.geometry_hash
    metadata["geometry_program_bridge_evidence"] = bridge
    metadata["geometry_authority"] = "final_floorwise_legal_geometry_program"
    metadata["final_program_hash"] = final_program_hash
    metadata["final_geometry_hash"] = final_geometry_hash
    metadata["legal_field_affine_placement"] = projection_evidence
    metadata["floorwise_legal_projection"] = deepcopy(
        projection_evidence
    )
    metadata["capacity_projection_measurement"] = {
        "schema_version": "arr.maas.capacity_projection_measurement.v1",
        "authority": "diagnostic_only_task4_classification",
        "requested_floor_area_m2": round(requested_floor_area, 6),
        "achieved_floor_area_m2": round(achieved_floor_area, 6),
        "achieved_to_requested_ratio": round(
            achieved_floor_area / max(requested_floor_area, 1e-9),
            8,
        ),
        "requested_capacity_satisfied": requested_capacity_satisfied,
        "candidate_requested_floors": len(legal_sections),
        "legal_floor_field_hash": str(legal_floor_field_hash or ""),
    }
    metadata["authored_geometry_program"] = authored_program.to_dict()
    metadata["authored_geometry_graph_snapshot"] = (
        build_geometry_graph_snapshot(
            authored_program,
            authored_compilation,
        )
    )
    metadata["authored_geometry_provenance"] = {
        "program_hash": authored_program.program_hash(),
        "geometry_hash": authored_compilation.geometry_hash,
        "authority": "upstream_provenance_only",
    }
    site_context_hash = str(site_context_hash or semantic_site_context_hash(
        pnu=pnu,
        building_type=building_type,
        site=containment_host,
    ))
    semantic_projection_context = {
        "floor_capacity_plan_hash": floor_capacity_plan_hash,
        "legal_floor_field_hash": str(legal_floor_field_hash or ""),
        "candidate_requested_floors": len(legal_sections),
        "candidate_target_gfa_m2": round(requested_floor_area, 6),
        "pnu": str(pnu or ""),
        "site_context_hash": site_context_hash,
        "capacity_alternative_id": str(capacity_alternative_id or ""),
        "achieved_capacity_band": str(
            achieved_capacity_band or capacity_alternative_id or ""
        ),
        "capacity_measurement_hash": str(
            capacity_measurement_hash or "pending_capacity_measurement"
        ),
    }
    semantic_projection = build_program_semantic_carrier_evidence(
        source,
        materialized,
        program_id=building_type,
        final_program_hash=final_program_hash,
        final_geometry_hash=final_geometry_hash,
        floor_capacity_plan_hash=str(
            semantic_projection_context["floor_capacity_plan_hash"]
        ),
        pnu=str(semantic_projection_context["pnu"]),
        site_context_hash=str(
            semantic_projection_context["site_context_hash"]
        ),
        capacity_alternative_id=str(
            semantic_projection_context["capacity_alternative_id"]
        ),
        achieved_capacity_band=str(
            semantic_projection_context["achieved_capacity_band"]
        ),
        capacity_measurement_hash=str(
            semantic_projection_context["capacity_measurement_hash"]
        ),
    )
    if semantic_projection.get("hard_pass") is not True:
        return None
    metadata["final_semantic_projection_context"] = semantic_projection_context
    metadata["program_semantic_carrier_evidence"] = semantic_projection
    metadata.pop("floorwise_legal_sibling_evidence", None)
    if legal_field_selection is not None:
        metadata.pop("floorwise_legal_matrix_stack", None)
        metadata.pop("floorwise_visual_projection", None)
    metadata.pop("program_space_zones", None)
    metadata.pop("program_role_integration_evidence", None)
    metadata["program_book_projection_evidence"] = _program_projection_evidence(
        final_projection_book_program,
        bridge,
    )
    return replace(materialized, metadata=metadata)






def _program_pool(
    site: Polygon,
    building_type: str,
    height: float,
    floors: int,
    *,
    generation_context: LegalGenerationContext | None = None,
    parent_variant_indices: tuple[int, ...] = (0,),
    typed_graph_mutations: list[dict[str, Any]] | None = None,
    geometry_program_mutations: list[dict[str, Any]] | None = None,
    synthesis_requests: list[dict[str, Any]] | None = None,
    outcome_graph: GeometryOutcomeGraph | None = None,
    recursive_only: bool = False,
    target_count: int = 0,
    program_dimensional_context: dict[str, Any] | None = None,
    site_boundary_source: str = "",
    site_access_context: dict[str, Any] | None = None,
    site_access_geometry: dict[str, Any] | None = None,
    live_geometry_vlm_revision: bool = False,
    base_capacity_contract: dict[str, Any] | None = None,
    trusted_legal_floor_field: dict[str, Any] | None = None,
    trusted_legal_floor_field_hash: str = "",
    trusted_clear_span_floor_plan: dict[str, Any] | None = None,
    capacity_site: Polygon | None = None,
    pnu: str = "",
    stop_after_shared_floor_hard_passes: int | None = None,
    diagnostic_scope_labels: tuple[str, ...] = (),
    diagnostic_book_probe_count: int | None = None,
    diagnostic_evaluation_cap: int | None = None,
    diagnostic_candidate_cap: int | None = None,
    progress_callback: Callable[[dict[str, int]], None] | None = None,
    diagnostic_evaluation_trace_callback: (
        Callable[[dict[str, Any]], None] | None
    ) = None,
) -> tuple[list[_Candidate], dict[str, Any]]:
    # Local import avoids expanding the ordinary candidate-analysis import
    # surface while allowing online quality-diversity compaction.
    from .quality_diversity_archive import StreamingMapElitesArchive

    if (
        (base_capacity_contract or {}).get("legal_floor_field")
        or (base_capacity_contract or {}).get("legal_floor_field_hash")
    ):
        trusted_field = (
            trusted_legal_floor_field
            if isinstance(trusted_legal_floor_field, dict)
            else None
        )
        trusted_hash = str(trusted_legal_floor_field_hash or "")
        base_field = (base_capacity_contract or {}).get(
            "legal_floor_field"
        )
        if (
            trusted_field is None
            or not trusted_hash
            or not validate_legal_floor_field(trusted_field)
            or str(
                trusted_field.get("legal_floor_field_hash") or ""
            )
            != trusted_hash
            or not validate_legal_floor_field(base_field)
            or str(
                (base_capacity_contract or {}).get(
                    "legal_floor_field_hash"
                )
                or ""
            )
            != trusted_hash
            or base_field != trusted_field
        ):
            raise ValueError(
                "trusted_run_legal_floor_authority_mismatch"
            )
        if (
            (base_capacity_contract or {}).get("floor_planning_mode")
            == "clear_span"
            and (
                not isinstance(trusted_clear_span_floor_plan, dict)
                or str(
                    trusted_clear_span_floor_plan.get(
                        "legal_floor_field_hash"
                    )
                    or ""
                )
                != trusted_hash
                or trusted_clear_span_floor_plan.get(
                    "legal_floor_field"
                )
                != trusted_field
            )
        ):
            raise ValueError(
                "trusted_run_clear_span_floor_authority_mismatch"
            )

    pool_started = perf_counter()
    accepted_archive = StreamingMapElitesArchive()
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
    gate_names = ("role_coverage", "dominant_ratio", "site_coverage", "hierarchy", "coherence", "program_form")
    gate_diagnostics = {label: _empty_gate_diagnostic() for label, _fraction in BASE_VOLUME_FRACTIONS}
    geometry_gate_diagnostics: dict[str, dict[str, Any]] = {}
    geometry_stage_counts: dict[str, dict[str, int]] = {}
    llm_authored_stage_counts: Counter[str] = Counter()
    llm_authored_failure_counts: Counter[str] = Counter()
    capacity_stage_counts: Counter[str] = Counter()
    capacity_target_floor_failure_counts: Counter[str] = Counter()
    floor_hard_capacity_utilizations: list[float] = []
    smoke_floor_pass_candidates = 0
    compiler_clean_base_keys: set[str] = set()
    requested_early_stop_target = max(
        0,
        int(stop_after_shared_floor_hard_passes or 0),
    )
    # Final legal/parking evidence is created downstream of this generator.
    # A pre-downstream floor/capacity proxy cannot authorize stopping a page.
    early_stop_target = 0
    explicit_diagnostic_budget = bool(
        diagnostic_scope_labels
        or diagnostic_book_probe_count is not None
        or diagnostic_evaluation_cap is not None
        or diagnostic_candidate_cap is not None
    )
    competition_breadth_budget = (
        resolve_competition_breadth_generation_budget(
            target_count=int(target_count),
            recursive_only=recursive_only,
            explicit_diagnostic_budget=explicit_diagnostic_budget,
            smoke_mode=requested_early_stop_target > 0,
        )
    )
    scope_schedule_labels = tuple(
        diagnostic_scope_labels
        or competition_breadth_budget.get("scope_labels")
        or ()
    )
    evaluation_cap = max(0, int(
        diagnostic_evaluation_cap
        if diagnostic_evaluation_cap is not None
        else competition_breadth_budget.get("cheap_evaluation_limit")
        or 0
    ))
    candidate_cap = max(0, int(
        diagnostic_candidate_cap
        if diagnostic_candidate_cap is not None
        else competition_breadth_budget.get("exact_shortlist_maximum")
        or 0
    ))
    book_probe_count = (
        max(1, int(diagnostic_book_probe_count))
        if diagnostic_book_probe_count is not None
        else int(competition_breadth_budget.get("book_probe_count") or 3)
    )

    def diagnostic_cap_reached() -> bool:
        return _diagnostic_generation_cap_reached(
            evaluated=evaluated,
            program_passed=program_passed,
            evaluation_cap=evaluation_cap,
            candidate_cap=candidate_cap,
        )

    def emit_progress() -> None:
        if progress_callback is not None:
            progress_callback({
                "evaluated_count": evaluated,
                "compiled_count": compiled,
                "program_passed_count": program_passed,
            })

    requested_parent_indices = tuple(sorted({max(0, int(index)) for index in parent_variant_indices})) or (0,)
    directed_seeds = _agent_mutated_seeds(
        building_type,
        typed_graph_mutations,
        geometry_program_mutations,
        synthesis_requests,
        outcome_graph,
        site=site,
        site_boundary_source=site_boundary_source,
        site_access_context=site_access_context,
        site_access_geometry=site_access_geometry,
        program_dimensional_context=program_dimensional_context,
        height=height,
        floors=floors,
        live_geometry_vlm_revision=live_geometry_vlm_revision,
        base_capacity_contract=base_capacity_contract,
        universal_variation_pages=requested_parent_indices,
    )
    llm_author_only_active = any(
        isinstance(request, dict)
        and bool(request.get("llm_author_only"))
        for request in (synthesis_requests or ())
    )
    if recursive_only:
        directed_seeds = tuple(
            seed for seed in directed_seeds
            if (
                _seed_is_llm_authored(seed)
                if llm_author_only_active
                else any(
                    note.startswith((
                        "geometry_program_directive=",
                        "geometry_program_payload=",
                    ))
                    for note in seed.notes
                )
            )
        )
    parent_seeds = tuple(
        variant
        for seed_index, seed in enumerate(directed_seeds)
        for variant_index, variant in enumerate(program_seed_variants(
            seed,
            count=max(requested_parent_indices) + 1,
            random_seed=417 + seed_index * 97,
        ))
        if variant_index in requested_parent_indices
    )
    diagnostic_anchors_active = diagnostic_anchor_schedule_active(
        recursive_only=recursive_only,
        evaluation_cap=evaluation_cap,
        parent_indices=requested_parent_indices,
        has_capacity_contract=bool(base_capacity_contract),
        target_count=target_count,
    )
    if diagnostic_anchors_active:
        parent_seeds = schedule_diagnostic_anchor_parents(parent_seeds)
    outcome_program_slug = next(
        (slug for slug, label, _height, _floors in PROGRAMS if label == building_type),
        str(building_type),
    )
    llm_authored_stage_counts["directed_seed_count"] = sum(
        _seed_is_llm_authored(seed) for seed in directed_seeds
    )
    llm_authored_stage_counts["parent_seed_count"] = sum(
        _seed_is_llm_authored(seed) for seed in parent_seeds
    )
    principles = tuple(build_book_language_registry()["principles"])
    principle_by_id = {
        str(principle["principle_id"]): (index, principle)
        for index, principle in enumerate(principles)
    }
    breadth_enumeration_duration = perf_counter() - pool_started
    # The legal section field is invariant across every seed/BOOK probe in
    # this program run.  Materializing it inside the 1,968-candidate loop
    # repeated the same intersection/repair work thousands of times.
    run_floor_containment_hosts: tuple[Polygon | None, ...] = ()
    if trusted_legal_floor_field:
        authoritative_sections = (
            trusted_clear_span_floor_plan.get("legal_floor_sections")
            if (
                (base_capacity_contract or {}).get(
                    "floor_planning_mode"
                )
                == "clear_span"
                and isinstance(trusted_clear_span_floor_plan, dict)
            )
            else trusted_legal_floor_field.get(
                "legal_floor_sections"
            )
        )
        run_floor_containment_hosts = tuple(
            shape(section) for section in authoritative_sections or ()
        )
    elif generation_context is not None:
        run_floor_containment_hosts = tuple(
            generation_site_at_height(
                generation_context,
                float(height) * floor_number / max(1, int(floors)),
            )
            for floor_number in range(
                1,
                max(1, int(floors)) + 1,
            )
        )
    run_upper_containment_host = (
        run_floor_containment_hosts[-1]
        if run_floor_containment_hosts
        else None
    )
    competition_exact_keys: frozenset[str] = frozenset()
    competition_cheap_schedule = None
    cheap_screen_duration = 0.0
    if competition_breadth_budget:
        cheap_screen_started = perf_counter()
        cheap_records = _competition_cheap_candidate_records(
            parent_seeds,
            principles,
            book_probe_count=book_probe_count,
            evaluation_limit=evaluation_cap,
            scope_labels=scope_schedule_labels,
            page_index=min(requested_parent_indices),
            legal_sections=run_floor_containment_hosts,
            capacity_contract=base_capacity_contract,
        )
        competition_exact_keys, competition_cheap_schedule = (
            _competition_pre_exact_shortlist(
                cheap_records,
                page_index=min(requested_parent_indices),
                target_count=int(target_count),
            )
        )
        cheap_screen_duration = perf_counter() - cheap_screen_started
    exact_compile_started = perf_counter()
    for seed_index, seed in enumerate(parent_seeds):
        if (
            diagnostic_cap_reached()
            or early_stop_target
            and smoke_floor_pass_candidates >= early_stop_target
        ):
            break
        llm_authored_seed = _seed_is_llm_authored(seed)
        recursive_seed = any(
            note.startswith(("geometry_program_directive=", "geometry_program_payload="))
            for note in seed.notes
        )
        recursive_program: GeometryProgram | None = None
        if recursive_seed:
            payload = next((
                note.split("=", 1)[1]
                for note in seed.notes
                if note.startswith("geometry_program_payload=")
            ), "")
            try:
                recursive_program = GeometryProgram.from_dict(json.loads(payload))
            except (TypeError, ValueError, json.JSONDecodeError):
                recursive_program = None
        source_seed_name = next((
            note.split("=", 1)[1]
            for note in seed.notes
            if note.startswith("geometry_program_source_seed=")
        ), "") if recursive_seed else ""
        anchor_spec = diagnostic_anchor_spec(seed)
        # The exhaustive 69/69 BOOK compiler audit remains a separate hard
        # regression. In portfolio synthesis, multiplying every recursive AST
        # by all 69 sentences and all three probes mostly relabelled the same
        # geometry thousands of times. Give each genotype a deterministic,
        # scope-balanced BOOK neighbourhood so the compute budget explores
        # more actual graph topologies instead.
        scheduled_principles = (
            staged_principle_schedule(principles, seed_index, count=12)
            if recursive_seed
            else tuple(enumerate(principles))
        )
        if (
            recursive_seed
            and outcome_graph is not None
            and not competition_breadth_budget
        ):
            genotype_hash = recursive_program.program_hash() if recursive_program is not None else ""
            if genotype_hash and source_seed_name:
                preferred_ids = outcome_graph.preferred_book_principle_ids(
                    source_seed=source_seed_name,
                    program_hash=genotype_hash,
                    fallback=(str(principle["principle_id"]) for _index, principle in scheduled_principles),
                    limit=12,
                )
                preferred_rank = {
                    principle_id: rank
                    for rank, principle_id in enumerate(preferred_ids)
                }
                scheduled_principles = tuple(sorted(
                    scheduled_principles,
                    key=lambda item: (
                        int(item[1].get("generation_stage_order") or 1),
                        preferred_rank.get(str(item[1]["principle_id"]), len(preferred_rank)),
                    ),
                ))
        principle_schedule_limit = _recursive_principle_schedule_limit(
            evaluation_cap=evaluation_cap,
            explicit_diagnostic_budget=explicit_diagnostic_budget,
        )
        if recursive_seed and principle_schedule_limit is not None:
            scheduled_principles = scheduled_principles[
                :principle_schedule_limit
            ]
        scheduled_principles = diagnostic_anchor_principles(
            seed,
            principle_by_id,
            scheduled_principles,
        )
        if competition_breadth_budget:
            # The cheap screen already chose the exact descriptor keys.
            # Consume those same keys directly instead of spending the exact
            # cap while skipping eleven unselected principles per parent.
            scheduled_principles = tuple(
                item
                for item in scheduled_principles
                if any(
                    key.startswith(
                        f"{seed_index}:{item[1]['principle_id']}:"
                    )
                    for key in competition_exact_keys
                )
            )
        recursive_family = str((recursive_program.metadata if recursive_program else {}).get("family") or "")
        geometry_stages = None
        if recursive_seed:
            geometry_stages = geometry_stage_counts.setdefault(
                recursive_family or "invalid_recursive_program",
                {
                    "evaluated": 0,
                    "sequence_compiled": 0,
                    "sequence_compile_failed": 0,
                    "directed_geometry_materialized": 0,
                    "directed_geometry_materialization_failed": 0,
                    "projection_materialized": 0,
                    "projection_failed": 0,
                    "clean_mass_passed": 0,
                    "containment_failed": 0,
                    "program_hard_passed": 0,
                },
            )
        for schedule_index, (principle_index, principle) in enumerate(scheduled_principles):
            if (
                diagnostic_cap_reached()
                or early_stop_target
                and smoke_floor_pass_candidates >= early_stop_target
            ):
                break
            execution_verbs = tuple(principle["execution_verbs"])
            lineage_base_id = str(
                principle.get("lineage_base_operative_id")
                or principle["principle_id"]
            )
            lineage_base_index = principle_by_id.get(
                lineage_base_id,
                (principle_index, principle),
            )[0]
            # One BOOK sentence is a typed operator family, not one frozen
            # geometry.  Execute three bounded schema-derived parameter probes
            # so selection can compare real alternatives without parcel or
            # finished-form templates.
            variation_indices = book_variation_indices(book_probe_count)
            sentence_variants = diagnostic_anchor_sentence_variants(
                seed,
                execution_verbs,
                default_count=book_probe_count,
            )
            if anchor_spec is not None:
                variation_indices = (anchor_spec.variant_index,)
            indexed_variants = tuple(zip(variation_indices, sentence_variants))
            scheduled_variants = (
                (
                    indexed_variants[
                        (seed_index + lineage_base_index)
                        % len(indexed_variants)
                    ],
                )
                if recursive_seed
                else indexed_variants
            )
            for variant_index, operations in scheduled_variants:
                if (
                    diagnostic_cap_reached()
                    or early_stop_target
                    and smoke_floor_pass_candidates >= early_stop_target
                ):
                    break
                evaluated += 1
                emit_progress()
                if llm_authored_seed:
                    llm_authored_stage_counts["evaluated"] += 1
                if geometry_stages is not None:
                    geometry_stages["evaluated"] += 1
                suffix = str(principle["principle_id"]).split("book:", 1)[-1].replace(":", "_")
                # The page grammar crosses each operation variation with the
                # six base volumes and three shown orientations.  Including
                # the canonical variation state here prevents one seed from
                # receiving three parameter edits on the same frozen host.
                base_volume_label, orientation = book_probe_scope(
                    seed_index,
                    lineage_base_index,
                    variant_index,
                    force_vertical=(
                        recursive_program is not None
                        and lineage_base_id == "book:operative:extrude"
                    ),
                    # A recursive seed evaluates one representative variant
                    # for budget control. Coupling that single variant back
                    # into p.3 scope made 1/1 and 1/4 mathematically
                    # unreachable; scope must rotate independently here.
                    couple_variation=not recursive_seed,
                )
                if scope_schedule_labels:
                    base_volume_label = scope_schedule_labels[
                        (evaluated - 1) % len(scope_schedule_labels)
                    ]
                base_volume_label, orientation = diagnostic_anchor_scope(
                    seed,
                    default_label=base_volume_label,
                    default_orientation=orientation,
                )
                scope_counts = scope_stage_counts[base_volume_label]
                scope_counts["evaluated"] += 1
                generation_lineage = lineage_record(
                    principle,
                    source_seed=seed.name,
                    scope_label=base_volume_label,
                    orientation=orientation,
                    variant_index=variant_index,
                )
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
                competition_candidate_key = (
                    f"{seed_index}:"
                    f"{principle['principle_id']}:"
                    f"{variant_index}"
                )
                if (
                    competition_breadth_budget
                    and competition_candidate_key
                    not in competition_exact_keys
                ):
                    capacity_stage_counts[
                        "competition_cheap_screen_deferred_from_exact"
                    ] += 1
                    continue
                if competition_breadth_budget:
                    capacity_stage_counts[
                        "competition_exact_shortlist_entered"
                    ] += 1
                compile_site = site
                generation_host_mode = "horizontal_buildable_envelope"
                recursive_directed = any(
                    note.startswith(("geometry_program_directive=", "geometry_program_payload="))
                    for note in sequence.notes
                )
                # The third typed parameter probe also explores the vertical
                # legal field.  Its base host is the sunlight-safe section at
                # the requested program height, so the resulting geometry is
                # born inside the envelope instead of repaired after selection.
                use_height_safe_host = variant_index >= 8 or (
                    base_volume_label == "1/16" and variant_index == 0
                )
                if (
                    generation_context is not None
                    and use_height_safe_host
                    and not recursive_directed
                ):
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
                genotype_schedule_index = (
                    seed_index + lineage_base_index + variant_index
                )
                capacity_schedule_index = (
                    diagnostic_anchor_capacity_schedule_index(
                        seed,
                        default_index=_capacity_alternative_schedule_index(
                            evaluation_index=evaluated - 1,
                            diagnostic_evaluation_cap=evaluation_cap,
                            genotype_schedule_index=genotype_schedule_index,
                            competition_target_count=(
                                int(target_count)
                                if competition_breadth_budget
                                else 0
                            ),
                            page_index=min(requested_parent_indices),
                        ),
                    )
                )
                capacity_alternative = build_capacity_alternative(
                    base_capacity_contract,
                    capacity_alternative_for_host(
                        capacity_schedule_index,
                        base_capacity_contract,
                        host_area_m2=float(compile_site.area),
                        floor_count=floors,
                    ),
                )
                if diagnostic_evaluation_trace_callback is not None:
                    diagnostic_evaluation_trace_callback({
                        "evaluation_index": evaluated - 1,
                        "genotype_hash": (
                            recursive_program.program_hash()
                            if recursive_program is not None
                            else ""
                        ),
                        "form_bank_lane": str(
                            (recursive_program.metadata if recursive_program else {}).get(
                                "form_bank_lane"
                            )
                            or ""
                        ),
                        "book_stage": str(
                            generation_lineage.get("stage") or ""
                        ),
                        "book_stage_order": int(
                            generation_lineage.get("stage_order") or 0
                        ),
                        "principle_id": str(
                            generation_lineage.get("principle_id") or ""
                        ),
                        "parent_key": str(
                            generation_lineage.get("parent_key") or ""
                        ),
                        "scope_label": base_volume_label,
                        "orientation": orientation,
                        "variant_index": int(variant_index),
                        "capacity_schedule_index": capacity_schedule_index,
                        "capacity_alternative_id": str(
                            capacity_alternative.get("alternative_id") or ""
                        ),
                        "diagnostic_anchor_body_family": (
                            anchor_spec.body_family
                            if anchor_spec is not None
                            else ""
                        ),
                        "diagnostic_anchor_principle_id": (
                            anchor_spec.principle_id
                            if anchor_spec is not None
                            else ""
                        ),
                    })
                alternative_capacity_contract = capacity_contract_for_alternative(
                    base_capacity_contract,
                    capacity_alternative,
                )
                candidate_floor_context = _candidate_floor_context(
                    alternative_capacity_contract,
                    fallback_height=height,
                    fallback_floors=floors,
                    fallback_legal_sections=run_floor_containment_hosts,
                    trusted_legal_floor_field=trusted_legal_floor_field,
                    expected_legal_floor_field_hash=(
                        trusted_legal_floor_field_hash
                    ),
                    trusted_clear_span_floor_plan=(
                        trusted_clear_span_floor_plan
                    ),
                )
                if candidate_floor_context.get("hard_pass") is not True:
                    capacity_stage_counts[
                        "candidate_floor_context_failed"
                    ] += 1
                    continue
                candidate_height = float(
                    candidate_floor_context["height_m"]
                )
                candidate_floors = int(
                    candidate_floor_context["floors"]
                )
                candidate_legal_sections = tuple(
                    candidate_floor_context["legal_sections"]
                )
                candidate_floor_tops = tuple(
                    candidate_floor_context["floor_top_heights_m"]
                )
                capacity_alternative = {
                    **capacity_alternative,
                    "candidate_requested_floors": candidate_floors,
                    "candidate_requested_height_m": round(
                        candidate_height,
                        3,
                    ),
                    "candidate_floor_count_authority": str(
                        candidate_floor_context.get("authority") or ""
                    ),
                    "legal_floor_field_hash": str(
                        candidate_floor_context.get(
                            "legal_floor_field_hash"
                        )
                        or ""
                    ),
                }
                if use_height_safe_host and recursive_directed:
                    host_floor_index = min(
                        candidate_floors - 1,
                        max(
                            0,
                            (candidate_floors * 2 + 2) // 3 - 1,
                        ),
                    )
                    compile_site = candidate_legal_sections[
                        host_floor_index
                    ]
                    generation_host_mode = (
                        "candidate_legal_floor_prefix_section"
                    )
                    generation_host_section_height = (
                        candidate_floor_tops[host_floor_index]
                    )
                else:
                    generation_host_section_height = 0.0
                # A recursive candidate has one BOOK geometry authority. The
                # source compiler establishes only its program-role scaffold;
                # the exact p.3 selector and ordered operations are applied
                # once, below, to the manifold AST.
                source_sequence = seed if recursive_directed else sequence
                source = compile_sequence_to_source_mass(compile_site, source_sequence)
                if source is None:
                    if outcome_graph is not None and recursive_program is not None and source_seed_name:
                        outcome_graph.observe_geometry_gate_failure(
                            program_slug=outcome_program_slug,
                            source_seed=source_seed_name,
                            program=recursive_program,
                            principle_id=str(principle["principle_id"]),
                            book_scope=base_volume_label,
                            stage="sequence_compile",
                            failure_reasons=("sequence_compile_failed",),
                        )
                    if llm_authored_seed:
                        llm_authored_failure_counts["sequence_compile_failed"] += 1
                    if geometry_stages is not None:
                        geometry_stages["sequence_compile_failed"] += 1
                    continue
                capacity_measurement: dict[str, Any] = {}
                if geometry_stages is not None:
                    geometry_stages["sequence_compiled"] += 1
                if llm_authored_seed:
                    llm_authored_stage_counts["sequence_compiled"] += 1
                materialization_source = replace(
                    source,
                    metadata={
                        **deepcopy(source.metadata),
                        "candidate_floor_context": deepcopy(
                            candidate_floor_context
                        ),
                    },
                )
                upper_containment_host = (
                    candidate_floor_context["upper_legal_section"]
                    if recursive_directed
                    else None
                )
                floor_containment_hosts = (
                    candidate_legal_sections
                    if recursive_directed
                    else ()
                )
                plan_coverage = recursive_plan_coverage_floor(
                    building_type,
                    alternative_capacity_contract,
                    host_area_m2=float(compile_site.area),
                )
                def materialize_capacity_fit(
                    coverage: float,
                    floor_targets: tuple[float, ...],
                ) -> SourceMass | None:
                    return _materialize_directed_geometry(
                        materialization_source,
                        sequence,
                        building_type=building_type,
                        site_access_side=(
                            _site_access_side_in_principal_frame(
                                site,
                                site_access_geometry,
                            )
                        ),
                        containment_host=compile_site,
                        upper_containment_host=upper_containment_host,
                        floor_containment_hosts=floor_containment_hosts,
                        minimum_host_plan_coverage=coverage,
                        floor_capacity_plan_hash=str(
                            alternative_capacity_contract.get(
                                "floor_capacity_plan_hash"
                            )
                            or ""
                        ),
                        legal_floor_field_hash=str(
                            candidate_floor_context.get(
                                "legal_floor_field_hash"
                            )
                            or ""
                        ),
                        target_floor_areas_m2=floor_targets,
                        pnu=pnu,
                        capacity_alternative_id=str(
                            capacity_alternative.get(
                                "alternative_id"
                            )
                            or ""
                        ),
                        site_context_hash=semantic_site_context_hash(
                            pnu=pnu,
                            building_type=building_type,
                            site=(
                                generation_context.generation_site
                                if generation_context is not None
                                else site
                            ),
                        ),
                    )

                source = materialize_capacity_fit(
                    plan_coverage,
                    tuple(
                        float(value)
                        for value in (
                            alternative_capacity_contract.get(
                                "target_floor_areas_m2"
                            )
                            or ()
                        )
                    ),
                )
                if source is None:
                    if outcome_graph is not None and recursive_program is not None and source_seed_name:
                        outcome_graph.observe_geometry_gate_failure(
                            program_slug=outcome_program_slug,
                            source_seed=source_seed_name,
                            program=recursive_program,
                            principle_id=str(principle["principle_id"]),
                            book_scope=base_volume_label,
                            stage="directed_geometry_materialization",
                            failure_reasons=("directed_geometry_materialization_failed",),
                        )
                    if llm_authored_seed:
                        llm_authored_failure_counts["directed_geometry_materialization_failed"] += 1
                    if geometry_stages is not None:
                        geometry_stages["directed_geometry_materialization_failed"] += 1
                    continue
                capacity_plan_fit_evidence: dict[str, Any] = {
                    "schema_version": "arr.maas.capacity_plan_fit.v1",
                    "retry_limit": 2,
                    "retry_attempted": False,
                    "initial_plan_coverage": round(plan_coverage, 6),
                }
                if base_capacity_contract and capacity_site is not None and recursive_directed:
                    initial_floor_contract, initial_capacity = (
                        _shared_floor_capacity_measurement(
                        source,
                        alternative_capacity_contract,
                        generation_context=generation_context,
                        capacity_site=capacity_site,
                        height=candidate_height,
                        floors=candidate_floors,
                        pnu=pnu,
                        trusted_legal_floor_field=(
                            trusted_legal_floor_field
                        ),
                        expected_legal_floor_field_hash=(
                            trusted_legal_floor_field_hash
                        ),
                        trusted_clear_span_floor_plan=(
                            trusted_clear_span_floor_plan
                        ),
                        )
                    )
                    retry_coverage = capacity_retry_plan_coverage(
                        plan_coverage,
                        capacity_alternative,
                        initial_capacity,
                    )
                    retry_floor_targets = capacity_retry_floor_targets(
                        alternative_capacity_contract,
                        capacity_alternative,
                        initial_capacity,
                    )
                    retry_required = _capacity_retry_required(
                        current_plan_coverage=plan_coverage,
                        retry_plan_coverage=retry_coverage,
                        current_floor_targets=alternative_capacity_contract.get(
                            "target_floor_areas_m2"
                        ),
                        retry_floor_targets=retry_floor_targets,
                    )
                    capacity_plan_fit_evidence.update({
                        "initial_achieved_utilization": initial_capacity.get(
                            "feasible_capacity_utilization"
                        ),
                        "derived_retry_plan_coverage": retry_coverage,
                        "derived_retry_floor_targets_m2": list(
                            retry_floor_targets
                        ),
                        "retry_required": retry_required,
                        "retry_attempted": False,
                        "retry_selected": False,
                        "geometry_retry_bypassed": bool(retry_required),
                        "retry_authority": "diagnostic_only",
                        "retry_floor_source_eligible": (
                            _capacity_pack_retry_eligible(initial_floor_contract)
                        ),
                    })
                    if retry_required:
                        capacity_stage_counts[
                            "plan_fit_retry_advisory_opportunity"
                        ] += 1
                    # Capacity evidence is diagnostic at MASS authoring time.
                    # Do not silently replace the authored geometry here: the
                    # attempted refit proved it can reach yield only by
                    # collapsing a bent/prismatic body into an unrequested
                    # stepped/pyramidal legal projection.
                    if (
                        retry_required
                        and not capacity_plan_fit_evidence[
                            "geometry_retry_bypassed"
                        ]
                    ):
                        if not _capacity_pack_retry_eligible(initial_floor_contract):
                            capacity_stage_counts[
                                "plan_fit_retry_skipped_nonviable_floor_source"
                            ] += 1
                        else:
                            capacity_plan_fit_evidence[
                                "retry_attempted"
                            ] = True
                            retry_source = materialize_capacity_fit(
                                retry_coverage,
                                tuple(
                                    float(value)
                                    for value in retry_floor_targets
                                ),
                            )
                            if retry_source is not None:
                                (
                                    retry_floor_contract,
                                    retry_capacity,
                                ) = _shared_floor_capacity_measurement(
                                    retry_source,
                                    alternative_capacity_contract,
                                    generation_context=(
                                        generation_context
                                    ),
                                    capacity_site=capacity_site,
                                    height=candidate_height,
                                    floors=candidate_floors,
                                    pnu=pnu,
                                    trusted_legal_floor_field=(
                                        trusted_legal_floor_field
                                    ),
                                    expected_legal_floor_field_hash=(
                                        trusted_legal_floor_field_hash
                                    ),
                                    trusted_clear_span_floor_plan=(
                                        trusted_clear_span_floor_plan
                                    ),
                                )
                                initial_utilization = float(
                                    initial_capacity.get(
                                        "feasible_capacity_utilization"
                                    )
                                    or 0.0
                                )
                                retry_utilization = float(
                                    retry_capacity.get(
                                        "feasible_capacity_utilization"
                                    )
                                    or 0.0
                                )
                                minimum_floor_area = float(
                                    alternative_capacity_contract.get(
                                        "minimum_floor_area_m2"
                                    )
                                    or 0.0
                                )
                                retry_floor_area = float(
                                    retry_capacity.get(
                                        "floor_area_m2"
                                    )
                                    or 0.0
                                )
                                if (
                                    retry_floor_contract.get(
                                        "hard_pass"
                                    )
                                    is True
                                    and retry_capacity.get(
                                        "hard_pass"
                                    )
                                    is not True
                                    and minimum_floor_area > 0.0
                                    and retry_floor_area > 0.0
                                ):
                                    correction = (
                                        minimum_floor_area
                                        / retry_floor_area
                                    )
                                    corrected_targets = tuple(
                                        float(value) * correction
                                        for value in retry_floor_targets
                                    )
                                    corrected_source = (
                                        materialize_capacity_fit(
                                            retry_coverage,
                                            corrected_targets,
                                        )
                                    )
                                    if corrected_source is not None:
                                        (
                                            corrected_floor_contract,
                                            corrected_capacity,
                                        ) = (
                                            _shared_floor_capacity_measurement(
                                                corrected_source,
                                                alternative_capacity_contract,
                                                generation_context=(
                                                    generation_context
                                                ),
                                                capacity_site=capacity_site,
                                                height=candidate_height,
                                                floors=candidate_floors,
                                                pnu=pnu,
                                                trusted_legal_floor_field=(
                                                    trusted_legal_floor_field
                                                ),
                                                expected_legal_floor_field_hash=(
                                                    trusted_legal_floor_field_hash
                                                ),
                                                trusted_clear_span_floor_plan=(
                                                    trusted_clear_span_floor_plan
                                                ),
                                            )
                                        )
                                        corrected_utilization = float(
                                            corrected_capacity.get(
                                                "feasible_capacity_utilization"
                                            )
                                            or 0.0
                                        )
                                        if (
                                            corrected_floor_contract.get(
                                                "hard_pass"
                                            )
                                            is True
                                            and corrected_utilization
                                            > retry_utilization + 1e-6
                                        ):
                                            retry_source = corrected_source
                                            retry_floor_contract = (
                                                corrected_floor_contract
                                            )
                                            retry_capacity = (
                                                corrected_capacity
                                            )
                                            retry_floor_targets = (
                                                corrected_targets
                                            )
                                            retry_utilization = (
                                                corrected_utilization
                                            )
                                            capacity_plan_fit_evidence[
                                                "correction_retry_attempted"
                                            ] = True
                                for correction_index in range(3):
                                    minimum_floor_area = float(
                                        alternative_capacity_contract.get(
                                            "minimum_floor_area_m2"
                                        )
                                        or 0.0
                                    )
                                    retry_floor_area = sum(
                                        float(volume.footprint.area)
                                        for volume in retry_source.volumes
                                    )
                                    if (
                                        minimum_floor_area <= 0.0
                                        or retry_floor_area <= 0.0
                                    ):
                                        break
                                    if (
                                        abs(
                                            retry_floor_area
                                            - minimum_floor_area
                                        )
                                        <= 5e-7
                                    ):
                                        break
                                    correction = (
                                        minimum_floor_area
                                        / retry_floor_area
                                    )
                                    corrected_targets = tuple(
                                        float(value) * correction
                                        for value in retry_floor_targets
                                    )
                                    corrected_source = (
                                        materialize_capacity_fit(
                                            retry_coverage,
                                            corrected_targets,
                                        )
                                    )
                                    if corrected_source is None:
                                        break
                                    (
                                        corrected_floor_contract,
                                        corrected_capacity,
                                    ) = _shared_floor_capacity_measurement(
                                        corrected_source,
                                        alternative_capacity_contract,
                                        generation_context=(
                                            generation_context
                                        ),
                                        capacity_site=capacity_site,
                                        height=candidate_height,
                                        floors=candidate_floors,
                                        pnu=pnu,
                                        trusted_legal_floor_field=(
                                            trusted_legal_floor_field
                                        ),
                                        expected_legal_floor_field_hash=(
                                            trusted_legal_floor_field_hash
                                        ),
                                        trusted_clear_span_floor_plan=(
                                            trusted_clear_span_floor_plan
                                        ),
                                    )
                                    corrected_utilization = float(
                                        corrected_capacity.get(
                                            "feasible_capacity_utilization"
                                        )
                                        or 0.0
                                    )
                                    corrected_floor_area = sum(
                                        float(volume.footprint.area)
                                        for volume
                                        in corrected_source.volumes
                                    )
                                    if (
                                        corrected_floor_contract.get(
                                            "hard_pass"
                                        )
                                        is not True
                                        or abs(
                                            corrected_floor_area
                                            - minimum_floor_area
                                        )
                                        >= abs(
                                            retry_floor_area
                                            - minimum_floor_area
                                        )
                                    ):
                                        break
                                    retry_source = corrected_source
                                    retry_floor_contract = (
                                        corrected_floor_contract
                                    )
                                    retry_capacity = corrected_capacity
                                    retry_floor_targets = (
                                        corrected_targets
                                    )
                                    retry_utilization = (
                                        corrected_utilization
                                    )
                                    capacity_plan_fit_evidence[
                                        "correction_retry_count"
                                    ] = correction_index + 2
                                capacity_plan_fit_evidence.update({
                                    "retry_achieved_utilization": (
                                        retry_utilization
                                    ),
                                    "retry_floor_hard_pass": bool(
                                        retry_floor_contract.get(
                                            "hard_pass"
                                        )
                                    ),
                                })
                                if (
                                    retry_floor_contract.get(
                                        "hard_pass"
                                    )
                                    is True
                                    and retry_utilization
                                    > initial_utilization + 1e-6
                                ):
                                    retry_metadata = deepcopy(
                                        retry_source.metadata
                                    )
                                    retry_semantic_context = dict(
                                        retry_metadata.get(
                                            "final_semantic_projection_context"
                                        )
                                        or {}
                                    )
                                    retry_semantic_context[
                                        "candidate_target_gfa_m2"
                                    ] = float(
                                        alternative_capacity_contract.get(
                                            "candidate_target_gfa_m2"
                                        )
                                        or alternative_capacity_contract.get(
                                            "target_floor_area_m2"
                                        )
                                        or 0.0
                                    )
                                    retry_metadata[
                                        "final_semantic_projection_context"
                                    ] = retry_semantic_context
                                    retry_source = replace(
                                        retry_source,
                                        metadata=retry_metadata,
                                    )
                                    source = retry_source
                                    initial_floor_contract = (
                                        retry_floor_contract
                                    )
                                    initial_capacity = retry_capacity
                                    plan_coverage = retry_coverage
                                    capacity_plan_fit_evidence.update({
                                        "retry_selected": True,
                                        "geometry_retry_bypassed": False,
                                        "selected_plan_coverage": (
                                            retry_coverage
                                        ),
                                    })
                                    capacity_stage_counts[
                                        "plan_fit_retry_selected"
                                    ] += 1
                if geometry_stages is not None:
                    geometry_stages["directed_geometry_materialized"] += 1
                if llm_authored_seed:
                    llm_authored_stage_counts["directed_geometry_materialized"] += 1
                if program_dimensional_context:
                    source = replace(source, metadata={
                        **deepcopy(source.metadata),
                        "program_dimensional_context": deepcopy(program_dimensional_context),
                    })
                geometry_payload = source.metadata.get("geometry_program")
                if isinstance(geometry_payload, dict) and geometry_payload.get("nodes"):
                    try:
                        geometry_program = GeometryProgram.from_dict(geometry_payload)
                        geometry_compilation = compile_geometry_program(geometry_program)
                        program_context = {
                            **program_reference_contract(building_type),
                            "program_dimensional_context": dict(program_dimensional_context or {}),
                            "base_capacity_contract": dict(base_capacity_contract or {}),
                            "candidate_capacity_contract": (
                                _compact_candidate_capacity_evidence(
                                    alternative_capacity_contract
                                )
                            ),
                            "site_boundary_source": site_boundary_source,
                            "site_access_context": dict(site_access_context or {}),
                            "site_access_side_in_program_frame": _site_access_side_in_principal_frame(
                                site,
                                site_access_geometry,
                            ),
                            "program_space_zones": deepcopy(source.metadata.get("program_space_zones") or []),
                        }
                        metadata = deepcopy(source.metadata)
                        metadata["program_context"] = program_context
                        metadata["geometry_graph_notes"] = build_geometry_graph_notes(
                            geometry_program,
                            geometry_compilation,
                        )
                        metadata["geometry_graph_snapshot"] = build_geometry_graph_snapshot(
                            geometry_program,
                            geometry_compilation,
                            program_context=program_context,
                        )
                        source = replace(source, metadata=metadata)
                    except (TypeError, ValueError):
                        # Invalid ASTs are rejected by the recursive compiler;
                        # context annotation must never fabricate a fallback.
                        pass
                if generation_context is not None:
                    metadata = deepcopy(source.metadata)
                    legal_evidence = deepcopy(generation_context.evidence)
                    legal_evidence.update({
                        "generation_host_mode": generation_host_mode,
                        "candidate_generation_site_area_m2": round(float(compile_site.area), 3),
                        "requested_program_height_m": candidate_height,
                        "requested_program_floors": candidate_floors,
                        "candidate_floor_count_authority": str(
                            candidate_floor_context.get("authority") or ""
                        ),
                        "legal_floor_field_hash": str(
                            candidate_floor_context.get(
                                "legal_floor_field_hash"
                            )
                            or ""
                        ),
                        "generation_host_section_height_m": (
                            round(
                                float(generation_host_section_height),
                                3,
                            )
                        ),
                    })
                    metadata["legal_generation_context_evidence"] = legal_evidence
                    source = replace(source, metadata=metadata)
                    if (
                        not recursive_directed
                        and base_volume_label == "1/16"
                        and generation_host_mode == "horizontal_buildable_envelope"
                    ):
                        source = fit_source_to_sunlight_field(
                            source,
                            generation_context,
                            height_m=candidate_height,
                            floors=candidate_floors,
                        )
                metadata = deepcopy(source.metadata)
                metadata["book_generation_lineage"] = generation_lineage
                metadata["base_capacity_contract"] = deepcopy(base_capacity_contract or {})
                metadata["candidate_capacity_contract"] = (
                    _compact_candidate_capacity_evidence(
                        alternative_capacity_contract
                    )
                )
                metadata["candidate_floor_context"] = {
                    key: deepcopy(value)
                    for key, value in candidate_floor_context.items()
                    if key not in {
                        "legal_sections",
                        "upper_legal_section",
                    }
                }
                metadata["capacity_alternative_projection"] = deepcopy(capacity_alternative)
                metadata["capacity_plan_fit_evidence"] = deepcopy(capacity_plan_fit_evidence)
                source = replace(source, metadata=metadata)
                shared_floor_contract: dict[str, Any] | None = None
                if generation_context is not None and capacity_site is not None:
                    bridge = (
                        source.metadata.get("geometry_program_bridge_evidence")
                        if isinstance(
                            source.metadata.get("geometry_program_bridge_evidence"),
                            dict,
                        )
                        else {}
                    )
                    shared_floor_contract = materialize_shared_floor_contract(
                        source,
                        site_local_utm=capacity_site,
                        legal_sections=candidate_legal_sections,
                        height_m=candidate_height,
                        floors=candidate_floors,
                        pnu=pnu,
                        program_hash=str(bridge.get("program_hash") or ""),
                        geometry_hash=str(bridge.get("geometry_hash") or ""),
                        floor_capacity_plan_hash=str(
                            (alternative_capacity_contract or {}).get(
                                "floor_capacity_plan_hash"
                            )
                            or ""
                        ),
                        feasible_capacity_m2=float(
                            (base_capacity_contract or {}).get(
                                "feasible_maximum_floor_area_m2"
                            )
                            or 0.0
                        ),
                    )
                    metadata = deepcopy(source.metadata)
                    metadata["shared_floor_contract"] = shared_floor_contract
                    source = replace(source, metadata=metadata)
                if base_capacity_contract and capacity_site is not None:
                    capacity_stage_counts["measured"] += 1
                    capacity_measurement = measure_source_capacity(
                        source,
                        alternative_capacity_contract,
                        site_local_utm=capacity_site,
                        height_m=candidate_height,
                        floors=candidate_floors,
                        shared_floor_contract=shared_floor_contract,
                    )
                    metadata = deepcopy(source.metadata)
                    metadata["source_capacity_measurement"] = capacity_measurement
                    metadata["capacity_alternative_projection"] = evaluate_capacity_alternative(
                        capacity_alternative,
                        capacity_measurement,
                    )
                    if shared_floor_contract is not None:
                        shared_floor_contract = bind_shared_floor_contract_capacity(
                            shared_floor_contract,
                            metadata["capacity_alternative_projection"],
                        )
                        metadata["shared_floor_contract"] = shared_floor_contract
                    achieved_capacity_band = str(
                        resolve_capacity_band_evidence(
                            metadata["capacity_alternative_projection"],
                            capacity_measurement=capacity_measurement,
                        ).get("resolved_capacity_alternative_id")
                        or ""
                    )
                    capacity_identity_hash = semantic_capacity_measurement_hash(
                        capacity_measurement,
                        metadata["capacity_alternative_projection"],
                    )
                    semantic_evidence = (
                        metadata.get("program_semantic_carrier_evidence")
                        if isinstance(
                            metadata.get("program_semantic_carrier_evidence"),
                            dict,
                        )
                        else {}
                    )
                    if semantic_evidence.get("status") != "not_required":
                        metadata["program_semantic_carrier_evidence"] = (
                            rebind_semantic_projection_capacity(
                                semantic_evidence,
                                achieved_capacity_band=achieved_capacity_band,
                                capacity_measurement_hash=capacity_identity_hash,
                            )
                        )
                        semantic_context = dict(
                            metadata.get("final_semantic_projection_context")
                            or {}
                        )
                        semantic_context.update({
                            "achieved_capacity_band": achieved_capacity_band,
                            "capacity_measurement_hash": capacity_identity_hash,
                        })
                        metadata["final_semantic_projection_context"] = (
                            semantic_context
                        )
                    source = replace(source, metadata=metadata)
                    capacity_stage_counts[
                        f"alternative:{capacity_alternative['alternative_id']}:measured"
                    ] += 1
                    if metadata["capacity_alternative_projection"]["target_hard_pass"]:
                        capacity_stage_counts[
                            f"alternative:{capacity_alternative['alternative_id']}:target_passed"
                        ] += 1
                    if metadata["capacity_alternative_projection"].get(
                        "selectable_capacity_hard_pass"
                    ):
                        resolved_id = str(
                            metadata["capacity_alternative_projection"].get(
                                "selectable_capacity_alternative_id"
                            )
                            or "unclassified"
                        )
                        capacity_stage_counts[
                            f"realized_band:{resolved_id}:selectable_passed"
                        ] += 1
                    if not capacity_measurement["hard_pass"]:
                        capacity_stage_counts["below_feasible_capacity_floor"] += 1
                        capacity_stage_counts["retained_for_stage_aware_vlm"] += 1
                    else:
                        capacity_stage_counts["hard_passed"] += 1
                compiled += 1
                emit_progress()
                scope_counts["compiled"] += 1
                projection_evidence = source.metadata.get("program_book_projection_evidence") or {}
                if projection_evidence.get("status") != "materialized":
                    if outcome_graph is not None and recursive_program is not None and source_seed_name:
                        outcome_graph.observe_geometry_gate_failure(
                            program_slug=outcome_program_slug,
                            source_seed=source_seed_name,
                            program=recursive_program,
                            principle_id=str(principle["principle_id"]),
                            book_scope=base_volume_label,
                            stage="book_projection",
                            failure_reasons=("book_projection_failed",),
                            source=source,
                        )
                    if llm_authored_seed:
                        llm_authored_failure_counts["book_projection_failed"] += 1
                    scope_counts["projection_failed"] += 1
                    if geometry_stages is not None:
                        geometry_stages["projection_failed"] += 1
                    continue
                scope_counts["projection_materialized"] += 1
                if geometry_stages is not None:
                    geometry_stages["projection_materialized"] += 1
                clean_mass_pass, clean_mass_evidence = _clean_mass_gate(source)
                if not clean_mass_pass:
                    if outcome_graph is not None and recursive_program is not None and source_seed_name:
                        outcome_graph.observe_geometry_gate_failure(
                            program_slug=outcome_program_slug,
                            source_seed=source_seed_name,
                            program=recursive_program,
                            principle_id=str(principle["principle_id"]),
                            book_scope=base_volume_label,
                            stage="clean_mass",
                            failure_reasons=tuple(clean_mass_evidence["failure_reasons"]),
                            source=source,
                        )
                    if llm_authored_seed:
                        for reason in clean_mass_evidence["failure_reasons"]:
                            llm_authored_failure_counts[f"clean_{reason}"] += 1
                    if geometry_stages is not None:
                        for reason in clean_mass_evidence["failure_reasons"]:
                            key = f"clean_failed_{reason}"
                            geometry_stages[key] = geometry_stages.get(key, 0) + 1
                    continue
                if not _inside_site(source, compile_site):
                    if outcome_graph is not None and recursive_program is not None and source_seed_name:
                        outcome_graph.observe_geometry_gate_failure(
                            program_slug=outcome_program_slug,
                            source_seed=source_seed_name,
                            program=recursive_program,
                            principle_id=str(principle["principle_id"]),
                            book_scope=base_volume_label,
                            stage="containment",
                            failure_reasons=("containment_failed",),
                            source=source,
                        )
                    if llm_authored_seed:
                        llm_authored_failure_counts["containment_failed"] += 1
                    if geometry_stages is not None:
                        geometry_stages["containment_failed"] += 1
                    continue
                clean += 1
                scope_counts["clean"] += 1
                # A BOOK descendant is allowed to repair its base parent's
                # program relation.  Its causal parent therefore needs to be
                # compiler-clean and contained, not already a final
                # program-hard-pass design.  Record this before the program
                # gate and carry it across QD compaction.
                if str(generation_lineage.get("stage") or "") == "base":
                    base_key = str(generation_lineage.get("parent_key") or "")
                    if base_key:
                        compiler_clean_base_keys.add(base_key)
                capacity_stage_counts[
                    f"alternative:{capacity_alternative['alternative_id']}:clean_passed"
                ] += 1
                if geometry_stages is not None:
                    geometry_stages["clean_mass_passed"] += 1
                if llm_authored_seed:
                    llm_authored_stage_counts["clean_mass_passed"] += 1
                feature = source_feature(
                    source,
                    sequence,
                    building_type=building_type,
                    height=candidate_height,
                    floors=candidate_floors,
                    site_area=float(compile_site.area),
                    surface_materialization="summary_only",
                )
                props = feature.setdefault("properties", {})
                props["site_boundary_geometry"] = mapping(site)
                props["site_boundary_source"] = site_boundary_source
                props["site_access_context"] = dict(site_access_context or {})
                props["site_access_geometry"] = site_access_geometry
                props["program_context"] = {
                    **program_reference_contract(building_type),
                    "program_dimensional_context": dict(program_dimensional_context or {}),
                    "base_capacity_contract": dict(base_capacity_contract or {}),
                    "candidate_capacity_contract": (
                        _compact_candidate_capacity_evidence(
                            alternative_capacity_contract
                        )
                    ),
                    "site_boundary_source": site_boundary_source,
                    "site_access_context": dict(site_access_context or {}),
                    "site_access_side_in_program_frame": _site_access_side_in_principal_frame(
                        site,
                        site_access_geometry,
                    ),
                    "program_space_zones": deepcopy(source.metadata.get("program_space_zones") or []),
                }
                # These records are immutable evidence already owned by this
                # candidate's SourceMass. Sharing them avoids a second deep
                # object graph per heavy candidate while preserving exact AST
                # identity for render/VLM/selector consumers.
                props["geometry_program"] = source.metadata.get("geometry_program") or {}
                props["geometry_graph_notes"] = source.metadata.get("geometry_graph_notes") or []
                props["geometry_graph_snapshot"] = source.metadata.get("geometry_graph_snapshot") or {}
                props["book_generation_lineage"] = deepcopy(generation_lineage)
                props["base_capacity_contract"] = deepcopy(base_capacity_contract or {})
                props["candidate_capacity_contract"] = (
                    _compact_candidate_capacity_evidence(
                        alternative_capacity_contract
                    )
                )
                props["candidate_floor_context"] = deepcopy(
                    source.metadata.get("candidate_floor_context") or {}
                )
                props["source_capacity_measurement"] = deepcopy(capacity_measurement)
                props["capacity_alternative_projection"] = deepcopy(
                    source.metadata.get("capacity_alternative_projection") or {}
                )
                program = attach_program_massing_evidence(feature, building_type=building_type)
                spatial = feature["properties"]["program_spatial_evidence"]
                program_form_gate = _program_form_gate(source, building_type)
                feature["properties"]["program_form_gate"] = program_form_gate
                gate_pass = {
                    "role_coverage": bool(all(spatial.get("required_role_hits") or ())),
                    "dominant_ratio": float(spatial.get("dominant_ratio_score") or 0.0) >= 0.55,
                    "site_coverage": float(spatial.get("site_coverage_score") or 0.0) >= 0.55,
                    "hierarchy": float(spatial.get("hierarchy_score") or 0.0) >= 0.50,
                    "coherence": bool((feature["properties"].get("source_signature", {}).get("coherence_evidence") or {}).get("hard_pass", False)),
                    "program_form": bool(program_form_gate["hard_pass"]),
                }
                failed_gates = tuple(name for name in gate_names if not gate_pass[name])
                combined_program_hard_pass = bool(program["hard_pass"]) and bool(program_form_gate["hard_pass"])
                coherence_evidence = (
                    feature["properties"].get("source_signature", {}).get("coherence_evidence") or {}
                )
                _record_gate_diagnostic(
                    gate_diagnostics[base_volume_label],
                    spatial=spatial,
                    hard_pass=combined_program_hard_pass,
                    failed_gates=failed_gates,
                    program_form_failures=tuple(program_form_gate.get("failures") or ()),
                    coherence_evidence=coherence_evidence,
                )
                geometry_family = str(source.metadata.get("family") or "") if source.metadata.get("geometry_program_bridge_evidence") else ""
                if geometry_family:
                    _record_gate_diagnostic(
                        geometry_gate_diagnostics.setdefault(geometry_family, _empty_gate_diagnostic()),
                        spatial=spatial,
                        hard_pass=combined_program_hard_pass,
                        failed_gates=failed_gates,
                        program_form_failures=tuple(program_form_gate.get("failures") or ()),
                        coherence_evidence=coherence_evidence,
                    )
                    if outcome_graph is not None:
                        outcome_graph.observe_program_evaluation(
                            program_slug=next(
                                (slug for slug, label, _height, _floors in PROGRAMS if label == building_type),
                                str(building_type),
                            ),
                            source=source,
                            sequence_name=sequence.name,
                            principle_id=str(principle["principle_id"]),
                            spatial=spatial,
                            failed_gates=failed_gates,
                            program_hard_pass=combined_program_hard_pass,
                            program_evidence=program,
                        )
                if not combined_program_hard_pass:
                    if llm_authored_seed:
                        llm_authored_failure_counts.update(f"program_{name}" for name in failed_gates)
                        logger.info(
                            "Rejecting LLM-authored program hard gate: "
                            "failed_gates=%s coherence=%s program_form=%s",
                            failed_gates,
                            deepcopy(coherence_evidence),
                            deepcopy(program_form_gate),
                        )
                    continue
                program_passed += 1
                scope_counts["program_passed"] += 1
                capacity_stage_counts[
                    f"alternative:{capacity_alternative['alternative_id']}:program_passed"
                ] += 1
                if geometry_stages is not None:
                    geometry_stages["program_hard_passed"] += 1
                if llm_authored_seed:
                    llm_authored_stage_counts["program_hard_passed"] += 1
                if capacity_measurement:
                    capacity_projection = (
                        source.metadata.get("capacity_alternative_projection")
                        if isinstance(source.metadata, dict)
                        else {}
                    ) or {}
                    if (
                        isinstance(shared_floor_contract, dict)
                        and shared_floor_contract.get("hard_pass") is True
                    ):
                        floor_hard_capacity_utilizations.append(
                            float(
                                capacity_measurement.get(
                                    "feasible_capacity_utilization"
                                )
                                or 0.0
                            )
                        )
                    if capacity_projection.get("target_hard_pass") is True:
                        if (
                            isinstance(shared_floor_contract, dict)
                            and shared_floor_contract.get("hard_pass") is True
                        ):
                            capacity_stage_counts[
                                "capacity_target_and_floor_contract_passed"
                            ] += 1
                        else:
                            capacity_stage_counts[
                                "capacity_target_passed_floor_contract_failed"
                            ] += 1
                            capacity_target_floor_failure_counts.update(
                                shared_floor_contract.get("failure_reasons") or ()
                                if isinstance(shared_floor_contract, dict)
                                else ("missing_shared_floor_contract",)
                            )
                    if capacity_projection.get(
                        "selectable_capacity_hard_pass"
                    ) is True and (
                        isinstance(shared_floor_contract, dict)
                        and shared_floor_contract.get("hard_pass") is True
                    ):
                        capacity_stage_counts[
                            "capacity_selectable_and_floor_contract_passed"
                        ] += 1
                    capacity_score = capacity_fit_score(
                        capacity_alternative,
                        capacity_measurement,
                    )
                    capacity_plan_fit_evidence[
                        "advisory_capacity_fit_score"
                    ] = capacity_score
                    score = _mass_stage_design_score(
                        program_fit_score=float(program["program_fit_score"]),
                        architectural_score=float(
                            spatial["architectural_score"]
                        ),
                        advisory_capacity_score=capacity_score,
                    )
                else:
                    score = _mass_stage_design_score(
                        program_fit_score=float(program["program_fit_score"]),
                        architectural_score=float(
                            spatial["architectural_score"]
                        ),
                    )
                bridge = source.metadata.get("geometry_program_bridge_evidence") or {}
                fit_strength = float(bridge.get("legal_fit_strength") or 0.0) if isinstance(bridge, dict) else 0.0
                # Selection must not reward a legal interpolation that erases
                # the AST's section language. Hard gates already decide legal
                # validity; this small tie-break preserves design geometry.
                score -= fit_strength * 0.10
                accepted_archive.append(_Candidate(
                    str(principle["principle_id"]),
                    str(principle["kind"]),
                    str(principle["label"]),
                    sequence,
                    source,
                    feature,
                    round(score, 6),
                ))
                emit_progress()
    accepted = accepted_archive.finalize()
    capacity_stage_counts["qd_stream_compaction_count"] += accepted_archive.compaction_count
    capacity_stage_counts["qd_stream_candidates_released"] += accepted_archive.released_count
    capacity_stage_counts["qd_stream_peak_candidate_count"] = accepted_archive.peak_candidate_count
    accepted, lineage_gate = gate_descendants_by_base(
        accepted,
        known_viable_base_keys=compiler_clean_base_keys,
    )
    if candidate_cap:
        accepted = accepted[:candidate_cap]
    active_universal_programs = universal_form_program_pages(requested_parent_indices)
    summarized_gate_diagnostics = {
        label: _summarize_gate_diagnostic(diagnostic)
        for label, diagnostic in gate_diagnostics.items()
    }
    return accepted, {
        "evaluated": evaluated,
        "compiled": compiled,
        "clean": clean,
        "program_passed": program_passed,
        "diagnostic_generation_budget": {
            "active": bool(
                explicit_diagnostic_budget
            ),
            "scope_labels": list(diagnostic_scope_labels),
            "book_probe_count": book_probe_count,
            "evaluation_cap": (
                max(0, int(diagnostic_evaluation_cap or 0))
            ),
            "candidate_cap": (
                max(0, int(diagnostic_candidate_cap or 0))
            ),
        },
        "competition_breadth_generation_budget": {
            "active": bool(competition_breadth_budget),
            "activation_authority": (
                "portfolio_contract_full_target_20_non_smoke"
                if competition_breadth_budget else "inactive"
            ),
            "target_count": 20 if competition_breadth_budget else 0,
            "scope_labels": list(scope_schedule_labels)
            if competition_breadth_budget else [],
            "book_probe_count": book_probe_count
            if competition_breadth_budget else 0,
            "cheap_evaluation_limit": evaluation_cap
            if competition_breadth_budget else 0,
            "exact_shortlist_minimum": int(
                competition_breadth_budget.get(
                    "exact_shortlist_minimum"
                )
                or 0
            ),
            "exact_shortlist_maximum": candidate_cap
            if competition_breadth_budget else 0,
            "historical_36_cap_bypassed": bool(
                competition_breadth_budget and evaluation_cap > 36
            ),
            "cheap_screen": (
                competition_cheap_schedule.evidence()
                if competition_cheap_schedule is not None
                else {}
            ),
            "pre_exact_selected_keys": sorted(
                competition_exact_keys
            ),
        },
        "phase_durations_seconds": {
            "breadth_enumeration": max(
                breadth_enumeration_duration,
                1e-9,
            ),
            "cheap_screen": max(cheap_screen_duration, 1e-9),
            "exact_compile": max(
                perf_counter() - exact_compile_started,
                1e-9,
            ),
        },
        "hard_acceptance_early_stop": {
            "active": False,
            "target": early_stop_target,
            "requested_target": requested_early_stop_target,
            "disabled_reason": (
                "final_legal_and_parking_gates_run_after_candidate_generation"
            ),
            "observed_hard_acceptance_candidates": smoke_floor_pass_candidates,
            "stopped_early": False,
        },
        "capacity_floor_intersection": {
            "target_and_floor_hard_pass_count": int(
                capacity_stage_counts.get(
                    "capacity_target_and_floor_contract_passed",
                    0,
                )
            ),
            "target_pass_floor_failure_reason_counts": dict(
                capacity_target_floor_failure_counts
            ),
            "floor_hard_candidate_count": len(floor_hard_capacity_utilizations),
            "maximum_floor_hard_capacity_utilization": round(
                max(floor_hard_capacity_utilizations, default=0.0),
                6,
            ),
        },
        "base_role_seed_count": len(program_seed_sequences(building_type)),
        "agent_mutated_seed_count": max(0, len(directed_seeds) - len(program_seed_sequences(building_type))),
        "recursive_geometry_seed_count": sum(
            any(
                note.startswith(("geometry_program_directive=", "geometry_program_payload="))
                for note in seed.notes
            )
            for seed in directed_seeds
        ),
        "geometry_synthesis_request_source": (
            "universal_form_bank_control+vlm_or_session_directive"
            if synthesis_requests
            else "universal_form_bank_control"
        ),
        "geometry_synthesis_request_count": (
            1
            + len(tuple(record for record in (synthesis_requests or ()) if isinstance(record, dict)))
        ),
        "geometry_synthesis_request_diagnostics": [
            {
                "source_seed": str(record.get("source_seed") or ""),
                "live_llm_author": bool(record.get("live_llm_author")),
                "llm_author_only": bool(record.get("llm_author_only")),
                "llm_author_count": int(record.get("llm_author_count") or 0),
                "intent_tags": list(record.get("intent_tags") or ()),
            }
            for record in (synthesis_requests or ())
            if isinstance(record, dict)
        ],
        "universal_form_bank": {
            "program_conditioned": False,
            "variation_pages": list(requested_parent_indices),
            "form_program_count": len(active_universal_programs),
            "role_carrier_count": min(2, len(program_seed_sequences(building_type))),
            "dominant_form_seed_count": (
                len(active_universal_programs)
                * min(2, len(program_seed_sequences(building_type)))
            ),
            "prebook_live_vlm_author_active": False,
            "program_projection_and_vlm_are_downstream": True,
        },
        "geometry_program_vlm_status_counts": dict(sorted(Counter(
            note.split("=", 1)[1]
            for seed in directed_seeds
            for note in seed.notes
            if note.startswith("geometry_program_vlm_status=")
        ).items())),
        "geometry_program_llm_author_status_counts": dict(sorted(Counter(
            note.split("=", 1)[1]
            for seed in directed_seeds
            for note in seed.notes
            if note.startswith("geometry_program_llm_author_status=")
        ).items())),
        "geometry_program_llm_author_active_seed_count": sum(
            note == "geometry_program_llm_author_active=True"
            for seed in directed_seeds
            for note in seed.notes
        ),
        "geometry_program_prebook_vlm_quarantined_seed_count": sum(
            note == "geometry_program_prebook_vlm_quarantined=True"
            for seed in directed_seeds
            for note in seed.notes
        ),
        "geometry_program_llm_author_stage_counts": dict(sorted(llm_authored_stage_counts.items())),
        "geometry_program_llm_author_failure_counts": dict(sorted(llm_authored_failure_counts.items())),
        "geometry_program_vlm_causal_trace": {
            "maximum_reference_count": max((
                int(note.split("=", 1)[1])
                for seed in directed_seeds for note in seed.notes
                if note.startswith("geometry_program_vlm_reference_count=")
            ), default=0),
            "maximum_memory_observation_count": max((
                int(note.split("=", 1)[1])
                for seed in directed_seeds for note in seed.notes
                if note.startswith("geometry_program_vlm_memory_observation_count=")
            ), default=0),
            "geometry_revision_count": max((
                int(note.split("=", 1)[1])
                for seed in directed_seeds for note in seed.notes
                if note.startswith("geometry_program_vlm_revision_count=")
            ), default=0),
        },
        "base_capacity_contract": deepcopy(base_capacity_contract or {}),
        "capacity_stage_counts": dict(sorted(capacity_stage_counts.items())),
        "book_lineage_gate": lineage_gate,
        "program_passed_by_seed_family": dict(sorted(Counter(_seed_family(candidate) for candidate in accepted).items())),
        "program_passed_by_section_family": dict(sorted(Counter(_section_family(candidate) for candidate in accepted).items())),
        "scope_stage_counts": scope_stage_counts,
        "program_gate_diagnostics_by_scope": summarized_gate_diagnostics,
        "program_gate_diagnostics_by_recursive_geometry_family": {
            family: _summarize_gate_diagnostic(diagnostic)
            for family, diagnostic in sorted(geometry_gate_diagnostics.items())
        },
        "recursive_geometry_stage_counts": dict(sorted(geometry_stage_counts.items())),
        "program_gate_diagnostics_total": _merge_gate_diagnostics(summarized_gate_diagnostics),
    }



__all__ = ["_agent_mutated_seeds","_prebook_vlm_quarantined_llm_parents","_geometry_program_registry","_materialize_directed_geometry","_program_pool"]
