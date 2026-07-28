"""Staged BOOK candidate authorship, materialization and hard gating."""

from __future__ import annotations

import json
import os
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

from shapely.geometry import Polygon, mapping

from design.maas.geometry_language import (
    GeometryAuthorError,
    GeometryOutcomeGraph,
    GeometryProgram,
    apply_book_projection_to_geometry_program,
    apply_capacity_composition_to_geometry_program,
    universal_form_program_pages,
    apply_geometry_edits_compiler_safe,
    architectural_shape_programs,
    author_geometry_programs_with_openai,
    build_geometry_graph_notes,
    build_geometry_graph_snapshot,
    compile_geometry_program,
    compile_geometry_program_to_source_mass,
    materialize_floorwise_legal_source,
    openai_vlm_geometry_critic,
    project_program_requirements,
    reference_language_programs,
    recursive_book_projection_evidence,
    replace_source_dominant_with_geometry_program,
    retrieve_geometry_reference_matches,
    run_geometry_program_a2a_loop,
    synthesize_architectural_programs,
)
from design.maas.geometry_language.gate import GeometryGatePolicy, compilation_gate
from design.maas.grammar.verb_sequence import VerbSequence
from design.maas.program_massing import (
    ProgramSectionGraphEdit,
    book_sentence_variants,
    compose_program_with_book_operations,
    mutate_program_section_sequence,
    program_reference_contract,
    program_seed_sequences,
)
from design.maas.program_massing.scoring import attach_program_massing_evidence
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
)
from .capacity_contract import measure_source_capacity, recursive_plan_coverage_floor
from .capacity_alternatives import (
    build_capacity_alternative,
    capacity_fit_score,
    capacity_retry_plan_coverage,
    capacity_alternative_for_host,
    capacity_contract_for_alternative,
    evaluate_capacity_alternative,
)
from .variation_lattice import book_probe_scope, book_variation_indices
from .downstream_hard_gate import LegalGenerationContext, fit_source_to_sunlight_field, generation_site_at_height
from .gate_diagnostics import _empty_gate_diagnostic, _merge_gate_diagnostics, _record_gate_diagnostic, _summarize_gate_diagnostic
from .lineage import gate_descendants_by_base, lineage_record, staged_principle_schedule
from .program_catalog import PROGRAMS
from .reference_context import _audited_final_book_references, _reference_language_author_context
from .registry import build_book_language_registry
from .semantics import BASE_VOLUME_FRACTIONS


class _PostBookVlmOnly(RuntimeError):
    """Stop pre-BOOK review after authorship; the exact final solid owns VLM."""


def _eligible_smoke_floor_candidate(
    source: Any,
    shared_floor_contract: dict[str, Any] | None,
    capacity_measurement: dict[str, Any] | None,
    capacity_projection: dict[str, Any] | None,
    viable_base_keys: set[str],
) -> bool:
    """Stop only on a floor/capacity-valid BOOK candidate with viable lineage."""

    lineage = (
        source.metadata.get("book_generation_lineage")
        if isinstance(getattr(source, "metadata", None), dict)
        else {}
    ) or {}
    stage = str(lineage.get("stage") or "")
    parent_key = str(lineage.get("parent_key") or "")
    return bool(
        isinstance(shared_floor_contract, dict)
        and shared_floor_contract.get("hard_pass") is True
        and isinstance(capacity_measurement, dict)
        and capacity_measurement.get("hard_pass") is True
        and isinstance(capacity_projection, dict)
        and (
            capacity_projection.get("selectable_capacity_hard_pass") is True
            or (
                "selectable_capacity_hard_pass" not in capacity_projection
                and capacity_projection.get("target_hard_pass") is True
            )
        )
        and (
            stage == "base"
            or (parent_key and parent_key in viable_base_keys)
        )
    )


def _capacity_pack_retry_eligible(
    shared_floor_contract: dict[str, Any] | None,
) -> bool:
    """Return whether plan packing can repair the measured floor shortfall."""

    if not isinstance(shared_floor_contract, dict):
        return False
    if shared_floor_contract.get("hard_pass") is True:
        return True
    failures = set(shared_floor_contract.get("failure_reasons") or ())
    if failures - {"insufficient_clear_floor_depth", "insufficient_floor_area"}:
        return False
    plates = shared_floor_contract.get("plates")
    if not isinstance(plates, list) or not plates:
        return False
    return bool(
        all(float(plate.get("gross_area_m2") or 0.0) > 1e-6 for plate in plates)
        and all(
            index == 0 or float(plate.get("support_ratio") or 0.0) >= 0.20
            for index, plate in enumerate(plates)
        )
    )


def _capacity_retry_result_is_selectable(
    floor_contract: dict[str, Any] | None,
    retried_capacity: dict[str, Any] | None,
    baseline_capacity: dict[str, Any] | None,
) -> bool:
    """Require both an inhabitable floor contract and a measured improvement."""

    if not isinstance(floor_contract, dict) or floor_contract.get("hard_pass") is not True:
        return False
    retried = float((retried_capacity or {}).get("feasible_capacity_utilization") or 0.0)
    baseline = float((baseline_capacity or {}).get("feasible_capacity_utilization") or 0.0)
    return retried > baseline + 1e-9


def _shared_floor_capacity_measurement(
    source: Any,
    base_capacity_contract: dict[str, Any],
    *,
    generation_context: Any,
    capacity_site: Polygon,
    height: float,
    floors: int,
    pnu: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Measure candidate/retry capacity from the exact legal floor plates."""

    bridge = (
        source.metadata.get("geometry_program_bridge_evidence")
        if isinstance(source.metadata.get("geometry_program_bridge_evidence"), dict)
        else {}
    )
    shared_floor_contract = materialize_shared_floor_contract(
        source,
        site_local_utm=capacity_site,
        legal_sections=tuple(
            generation_site_at_height(
                generation_context,
                float(height) * floor_number / max(1, int(floors)),
            )
            for floor_number in range(1, max(1, int(floors)) + 1)
        ),
        height_m=height,
        floors=floors,
        pnu=pnu,
        program_hash=str(bridge.get("program_hash") or ""),
        geometry_hash=str(bridge.get("geometry_hash") or ""),
        floor_capacity_plan_hash=str(
            base_capacity_contract.get("floor_capacity_plan_hash") or ""
        ),
        feasible_capacity_m2=float(
            base_capacity_contract.get("feasible_maximum_floor_area_m2")
            or 0.0
        ),
    )
    measurement = measure_source_capacity(
        source,
        base_capacity_contract,
        site_local_utm=capacity_site,
        height_m=height,
        floors=floors,
        shared_floor_contract=shared_floor_contract,
    )
    return shared_floor_contract, measurement


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
            elif not os.getenv("OPENAI_API_KEY"):
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
                            unique_programs = {program.program_hash(): program for program in programs}
                            for authored in llm_authored:
                                unique_programs.setdefault(authored.program_hash(), authored)
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


def _materialize_directed_geometry(
    source: Any,
    sequence: VerbSequence,
    *,
    containment_host: Polygon | None = None,
    upper_containment_host: Polygon | None = None,
    floor_containment_hosts: tuple[Polygon, ...] = (),
    minimum_host_plan_coverage: float = 0.0,
    capacity_composition_utilizations: tuple[float, float] | None = None,
    floor_capacity_plan_hash: str = "",
    target_floor_areas_m2: tuple[float, ...] = (),
    building_type: str = "",
    site_access_side: str = "closed",
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
        program = apply_book_projection_to_geometry_program(program, sequence)
        if capacity_composition_utilizations is not None:
            achieved_utilization, target_utilization = capacity_composition_utilizations
            program = apply_capacity_composition_to_geometry_program(
                program,
                achieved_utilization=achieved_utilization,
                target_utilization=target_utilization,
            )
        program = project_program_requirements(
            program,
            building_type=building_type,
            access_side=site_access_side,
        )
    except (TypeError, ValueError):
        return None
    materialized = replace_source_dominant_with_geometry_program(
        source,
        program,
        containment_host=containment_host,
        upper_containment_host=upper_containment_host,
        upper_fit_strength=fit_strength,
        minimum_host_plan_coverage=minimum_host_plan_coverage,
    )
    if materialized is None:
        return None
    if floor_containment_hosts:
        materialized = materialize_floorwise_legal_source(
            materialized,
            legal_sections=floor_containment_hosts,
            target_plan_coverage=minimum_host_plan_coverage,
            floor_capacity_plan_hash=floor_capacity_plan_hash,
            target_floor_areas_m2=target_floor_areas_m2,
        )
        if materialized is None:
            return None
    source_seed = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_source_seed=")
    ), "")
    metadata = deepcopy(materialized.metadata)
    bridge = deepcopy(metadata.get("geometry_program_bridge_evidence") or {})
    bridge["source_seed"] = source_seed
    bridge["author_provider"] = next((
        note.split("=", 1)[1]
        for note in sequence.notes
        if note.startswith("geometry_program_source=")
    ), "unknown")
    metadata["geometry_program_bridge_evidence"] = bridge
    metadata["program_book_projection_evidence"] = recursive_book_projection_evidence(
        program,
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
    program_dimensional_context: dict[str, Any] | None = None,
    site_boundary_source: str = "",
    site_access_context: dict[str, Any] | None = None,
    site_access_geometry: dict[str, Any] | None = None,
    live_geometry_vlm_revision: bool = False,
    base_capacity_contract: dict[str, Any] | None = None,
    capacity_site: Polygon | None = None,
    pnu: str = "",
    stop_after_shared_floor_hard_passes: int | None = None,
) -> tuple[list[_Candidate], dict[str, Any]]:
    # Local import avoids expanding the ordinary candidate-analysis import
    # surface while allowing online quality-diversity compaction.
    from .quality_diversity_archive import StreamingMapElitesArchive

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
    early_stop_target = max(0, int(stop_after_shared_floor_hard_passes or 0))
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
    if recursive_only:
        directed_seeds = tuple(
            seed for seed in directed_seeds
            if any(
                note.startswith(("geometry_program_directive=", "geometry_program_payload="))
                for note in seed.notes
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
    for seed_index, seed in enumerate(parent_seeds):
        if early_stop_target and smoke_floor_pass_candidates >= early_stop_target:
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
        if recursive_seed and outcome_graph is not None:
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
            if early_stop_target and smoke_floor_pass_candidates >= early_stop_target:
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
            variation_indices = book_variation_indices(3)
            sentence_variants = tuple(book_sentence_variants(execution_verbs, count=3))
            indexed_variants = tuple(zip(variation_indices, sentence_variants))
            scheduled_variants = (
                (
                    indexed_variants[2],
                )
                if recursive_seed and (seed_index + lineage_base_index) % 3 == 0
                else (
                    indexed_variants[0],
                )
                if recursive_seed
                else indexed_variants
            )
            for variant_index, operations in scheduled_variants:
                if early_stop_target and smoke_floor_pass_candidates >= early_stop_target:
                    break
                evaluated += 1
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
                capacity_alternative = build_capacity_alternative(
                    base_capacity_contract,
                    capacity_alternative_for_host(
                        seed_index + lineage_base_index + variant_index,
                        base_capacity_contract,
                        host_area_m2=float(compile_site.area),
                        floor_count=floors,
                    ),
                )
                alternative_capacity_contract = capacity_contract_for_alternative(
                    base_capacity_contract,
                    capacity_alternative,
                )
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
                materialization_source = source
                upper_containment_host = (
                    generation_site_at_height(generation_context, height)
                    if recursive_directed and generation_context is not None
                    else None
                )
                floor_containment_hosts: tuple[Polygon, ...] = ()
                if recursive_directed and generation_context is not None:
                    floor_containment_hosts = tuple(
                        section
                        for floor_number in range(1, max(1, int(floors)) + 1)
                        for section in (
                            generation_site_at_height(
                                generation_context,
                                float(height) * floor_number / max(1, int(floors)),
                            ),
                        )
                        if section is not None
                    )
                plan_coverage = recursive_plan_coverage_floor(
                    building_type,
                    alternative_capacity_contract,
                    host_area_m2=float(compile_site.area),
                )
                source = _materialize_directed_geometry(
                    materialization_source,
                    sequence,
                    building_type=building_type,
                    site_access_side=_site_access_side_in_principal_frame(
                        site,
                        site_access_geometry,
                    ),
                    containment_host=compile_site,
                    upper_containment_host=upper_containment_host,
                    floor_containment_hosts=floor_containment_hosts,
                    minimum_host_plan_coverage=plan_coverage,
                    floor_capacity_plan_hash=str(
                        alternative_capacity_contract.get(
                            "floor_capacity_plan_hash"
                        )
                        or ""
                    ),
                    target_floor_areas_m2=tuple(
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
                        base_capacity_contract,
                        generation_context=generation_context,
                        capacity_site=capacity_site,
                        height=height,
                        floors=floors,
                        pnu=pnu,
                        )
                    )
                    retry_coverage = capacity_retry_plan_coverage(
                        plan_coverage,
                        capacity_alternative,
                        initial_capacity,
                    )
                    capacity_plan_fit_evidence.update({
                        "initial_achieved_utilization": initial_capacity.get(
                            "feasible_capacity_utilization"
                        ),
                        "derived_retry_plan_coverage": retry_coverage,
                    })
                    if (
                        retry_coverage > plan_coverage + 1e-6
                        and _capacity_pack_retry_eligible(initial_floor_contract)
                    ):
                        capacity_stage_counts["plan_fit_retry_attempted"] += 1
                        capacity_plan_fit_evidence["retry_attempted"] = True
                        # First preserve the exact authored AST and only refit
                        # its measured plan coverage. A tiny capacity shortfall
                        # must not force an unnecessary aggregation macro.
                        retried_source = _materialize_directed_geometry(
                            materialization_source,
                            sequence,
                            building_type=building_type,
                            site_access_side=_site_access_side_in_principal_frame(
                                site,
                                site_access_geometry,
                            ),
                            containment_host=compile_site,
                            upper_containment_host=upper_containment_host,
                            floor_containment_hosts=floor_containment_hosts,
                            minimum_host_plan_coverage=retry_coverage,
                            floor_capacity_plan_hash=str(
                                alternative_capacity_contract.get(
                                    "floor_capacity_plan_hash"
                                )
                                or ""
                            ),
                            target_floor_areas_m2=tuple(
                                float(value)
                                for value in (
                                    alternative_capacity_contract.get(
                                        "target_floor_areas_m2"
                                    )
                                    or ()
                                )
                            ),
                        )
                        baseline_capacity = initial_capacity
                        if retried_source is not None:
                            retried_floor_contract, retried_capacity = (
                                _shared_floor_capacity_measurement(
                                retried_source,
                                base_capacity_contract,
                                generation_context=generation_context,
                                capacity_site=capacity_site,
                                height=height,
                                floors=floors,
                                pnu=pnu,
                                )
                            )
                            capacity_plan_fit_evidence["retry_achieved_utilization"] = (
                                retried_capacity.get("feasible_capacity_utilization")
                            )
                            if _capacity_retry_result_is_selectable(
                                retried_floor_contract,
                                retried_capacity,
                                baseline_capacity,
                            ):
                                source = retried_source
                                baseline_capacity = retried_capacity
                                capacity_stage_counts["plan_fit_retry_improved"] += 1
                                capacity_plan_fit_evidence["retry_selected"] = True
                                capacity_plan_fit_evidence["retry_mode"] = "plain_plan_refit"
                            else:
                                capacity_plan_fit_evidence["retry_selected"] = False
                                if retried_floor_contract.get("hard_pass") is not True:
                                    capacity_stage_counts[
                                        "plan_fit_retry_rejected_floor_contract"
                                    ] += 1
                        target_after_plain = evaluate_capacity_alternative(
                            capacity_alternative,
                            baseline_capacity,
                        )
                        if target_after_plain.get("target_hard_pass") is not True:
                            capacity_stage_counts["capacity_pack_fallback_attempted"] += 1
                            capacity_plan_fit_evidence["capacity_pack_fallback_attempted"] = True
                            packed_source = _materialize_directed_geometry(
                                materialization_source,
                                sequence,
                                building_type=building_type,
                                site_access_side=_site_access_side_in_principal_frame(
                                    site,
                                    site_access_geometry,
                                ),
                                containment_host=compile_site,
                                upper_containment_host=upper_containment_host,
                                floor_containment_hosts=floor_containment_hosts,
                                minimum_host_plan_coverage=retry_coverage,
                                capacity_composition_utilizations=(
                                    float(
                                        baseline_capacity.get(
                                            "feasible_capacity_utilization"
                                        )
                                        or 0.0
                                    ),
                                    float(
                                        capacity_alternative.get(
                                            "target_utilization"
                                        )
                                        or 0.0
                                    ),
                                ),
                                floor_capacity_plan_hash=str(
                                    alternative_capacity_contract.get(
                                        "floor_capacity_plan_hash"
                                    )
                                    or ""
                                ),
                                target_floor_areas_m2=tuple(
                                    float(value)
                                    for value in (
                                        alternative_capacity_contract.get(
                                            "target_floor_areas_m2"
                                        )
                                        or ()
                                    )
                                ),
                            )
                            if packed_source is not None:
                                packed_floor_contract, packed_capacity = (
                                    _shared_floor_capacity_measurement(
                                        packed_source,
                                        base_capacity_contract,
                                        generation_context=generation_context,
                                        capacity_site=capacity_site,
                                        height=height,
                                        floors=floors,
                                        pnu=pnu,
                                    )
                                )
                                capacity_plan_fit_evidence[
                                    "capacity_pack_achieved_utilization"
                                ] = packed_capacity.get("feasible_capacity_utilization")
                                if _capacity_retry_result_is_selectable(
                                    packed_floor_contract,
                                    packed_capacity,
                                    baseline_capacity,
                                ):
                                    source = packed_source
                                    capacity_stage_counts[
                                        "capacity_pack_fallback_improved"
                                    ] += 1
                                    capacity_plan_fit_evidence["retry_selected"] = True
                                    capacity_plan_fit_evidence["retry_mode"] = (
                                        "typed_capacity_pack"
                                    )
                                elif packed_floor_contract.get("hard_pass") is not True:
                                    capacity_stage_counts[
                                        "capacity_pack_rejected_floor_contract"
                                    ] += 1
                    elif retry_coverage > plan_coverage + 1e-6:
                        capacity_stage_counts[
                            "plan_fit_retry_skipped_nonviable_floor_source"
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
                        "requested_program_height_m": float(height),
                        "generation_host_section_height_m": (
                            round(float(height) * generation_section_ratio, 3)
                            if generation_host_mode == "height_safe_sunlight_section"
                            else 0.0
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
                            height_m=height,
                            floors=floors,
                        )
                metadata = deepcopy(source.metadata)
                metadata["book_generation_lineage"] = generation_lineage
                metadata["base_capacity_contract"] = deepcopy(base_capacity_contract or {})
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
                        legal_sections=tuple(
                            generation_site_at_height(
                                generation_context,
                                float(height) * floor_number / max(1, int(floors)),
                            )
                            for floor_number in range(1, max(1, int(floors)) + 1)
                        ),
                        height_m=height,
                        floors=floors,
                        pnu=pnu,
                        program_hash=str(bridge.get("program_hash") or ""),
                        geometry_hash=str(bridge.get("geometry_hash") or ""),
                        floor_capacity_plan_hash=str(
                            (base_capacity_contract or {}).get(
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
                        base_capacity_contract,
                        site_local_utm=capacity_site,
                        height_m=height,
                        floors=floors,
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
                    height=height,
                    floors=floors,
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
                    score = (
                        float(program["program_fit_score"]) * 0.40
                        + float(spatial["architectural_score"]) * 0.30
                        + capacity_score * 0.30
                    )
                else:
                    score = float(program["program_fit_score"]) * 0.56 + float(spatial["architectural_score"]) * 0.44
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
                if _eligible_smoke_floor_candidate(
                    source,
                    shared_floor_contract,
                    capacity_measurement,
                    source.metadata.get("capacity_alternative_projection"),
                    compiler_clean_base_keys,
                ):
                    smoke_floor_pass_candidates += 1
    accepted = accepted_archive.finalize()
    capacity_stage_counts["qd_stream_compaction_count"] += accepted_archive.compaction_count
    capacity_stage_counts["qd_stream_candidates_released"] += accepted_archive.released_count
    capacity_stage_counts["qd_stream_peak_candidate_count"] = accepted_archive.peak_candidate_count
    accepted, lineage_gate = gate_descendants_by_base(
        accepted,
        known_viable_base_keys=compiler_clean_base_keys,
    )
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
        "shared_floor_early_stop": {
            "active": bool(early_stop_target),
            "target": early_stop_target,
            "observed_program_pass_candidates": smoke_floor_pass_candidates,
            "stopped_early": bool(
                early_stop_target
                and smoke_floor_pass_candidates >= early_stop_target
            ),
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
