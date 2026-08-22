from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from design.maas.book_language import candidate_generation
from design.maas.book_language import portfolio_benchmark
from design.maas.book_language import portfolio_replenishment


def _production_replenishment_requests(
    *,
    legal_fit_repair_feedback=None,
    capacity_authoring_deficits=None,
    family_supply_deficits=None,
    base_book_vlm_replenishment_feedback=None,
    authored_visual_authority_replenishment_feedback=None,
    request_updates=None,
    selected_count=1,
    selected_scope_count=1,
    cycle_index=1,
):
    request = {
        "schema_version": "arr.maas.geometry_synthesis_request.v1",
        "program_role": "neighborhood_primary_active_bar",
        "candidate_count": 8,
        "llm_author_count": 8,
        "selector_stage_outcomes": [],
        "candidate_supply_deficits": [],
    }
    request.update(request_updates or {})
    return portfolio_benchmark._deficit_directed_replenishment_inputs(
        [request],
        legal_fit_repair_feedback=legal_fit_repair_feedback or [],
        capacity_authoring_deficits=capacity_authoring_deficits or [],
        family_supply_deficits=family_supply_deficits or {},
        progressive_target=None,
        base_book_vlm_replenishment_feedback=(
            base_book_vlm_replenishment_feedback or []
        ),
        authored_visual_authority_replenishment_feedback=(
            authored_visual_authority_replenishment_feedback or []
        ),
        selected_count=selected_count,
        selected_scope_count=selected_scope_count,
        target_count=5,
        required_scope_count=5,
        exact_compile_remaining=12,
        cycle_index=cycle_index,
        cycle_budget=5,
        author_replenishment_remaining=5,
    )["synthesis_requests"]


def _legal_fit_feedback(target=97.436):
    return [{
        "schema_version": "arr.maas.legal_fit_deficit.v1",
        "stage": "principal_frame_legal_fit",
        "typed_reasons": ["whole_solid_affine_fit_infeasible"],
        "legal_section_indices": [0, 1, 2],
        "measured_values": {
            "target_floor_areas_m2": [target, 97.436, 70.986],
            "legal_section_areas_m2": [102.931, 102.931, 74.989],
            "target_total_m2": target + 168.422,
            "legal_total_m2": 280.851,
            "target_floor_area_decimal_places": 3,
            "target_floor_area_rounding_tolerance_m2": 0.0005,
        },
        "authored_program_hash": "observational-program-hash",
    }]


def _capacity_deficit(**updates):
    payload = {
        "schema_version": "arr.maas.capacity_authoring_deficit.v1",
        "type": "capacity_authoring_deficit",
        "geometry_retry_policy": "measured_typed_ast_capacity_composition",
        "geometry_family": "llm_bend_notch",
        "body_phenotype": "stepped",
        "scope": "3/8",
        "capacity_band": "brief_target",
        "achieved_utilization": 0.84,
        "required_minimum_utilization": 0.9,
        "measured_gfa_m2": 280.0,
        "required_gfa_m2": 299.09,
        "gfa_deficit_m2": 19.09,
        "per_floor_deficit_status": "measured",
        "per_floor_gfa_deficits_m2": [4.0, 5.0, 5.0, 5.09],
        "typed_reasons": ["vertical_support_below_threshold"],
        "vertical_support_ratio": 0.72,
        "minimum_vertical_support_ratio": 0.8,
        "minimum_clear_depth_m": 6.0,
        "measured_clear_depth_m": 4.5,
        "containment_status": "occupied_outside_legal_geometry",
        "outside_distance_m": 0.25,
        "outside_area_m2": 1.5,
        "rejected_parent_program_hash": "observational-parent-hash",
    }
    payload.update(updates)
    return [payload]


def _family_deficits(**updates):
    payload = {
        "schema_version": "arr.maas.family_supply_deficits.v1",
        "target_count": 5,
        "required_body_phenotype_distinct": 3,
        "available_body_phenotype_distinct": 1,
        "body_phenotype_shortfall": 2,
        "required_body_roof_signature_distinct": 3,
        "available_body_roof_signature_distinct": 1,
        "body_roof_signature_shortfall": 2,
        "overrepresented_body_phenotype_counts": {"stepped": 3},
        "overrepresented_geometry_family_counts": {"llm_bend_notch": 3},
        "minimum_pair_distance": 0.2,
        "pair_distance_conflict_count": 2,
        "visible_stepped_count": 3,
        "visible_stepped_maximum": 1,
        "visible_stepped_excess": 2,
        "missing_descriptor_cells": ["body:courtyard"],
    }
    payload.update(updates)
    return payload


def _base_feedback(reason="final_book_vlm_weak_primary_mass"):
    return [{
        "schema_version": "arr.maas.book_base_vlm_replenishment_feedback.v1",
        "stage": "book_base_vlm",
        "reason": reason,
        "failures": [reason],
        "critic_actions": ["needs_carved_void"],
        "required_next_relations": ["public_threshold"],
        "geometry_family": "llm_bend_notch",
        "rationale": "observational prose",
        "response_id": "provider-observation",
    }]


def _authored_feedback(reason="profiled_legal_clip_midplane_topology_mismatch"):
    return [{
        "structural_failure": "authored_visual_authority",
        "structural_subreason": "authored_visual_authority_profiled_clip",
        "repair_reason": "authored_profiled_legal_clip_failed",
        "failure_reason": reason,
        "certificate_causes": [reason],
        "certificate_modes": ["failed", "floorwise_profiled_legal_clip"],
        "geometry_family": "llm_setback_courtyard",
        "book_scope": "1/1",
        "feedback_sources": [{"evidence": "observational"}],
    }]


def _lineage(*, geometry_suffix="a"):
    lineage = candidate_generation.lineage_record(
        {
            "principle_id": "book:operative:bend",
            "generation_stage": "base",
            "generation_stage_order": 1,
        },
        source_seed="reviewed-bend-seed",
        scope_label="1/8",
        orientation="vertical",
        variant_index=5,
    )
    lineage["test_geometry_suffix"] = geometry_suffix
    return lineage


def _principles():
    return (
        {
            "principle_id": "book:operative:bend",
            "lineage_base_operative_id": "book:operative:bend",
            "generation_stage": "base",
            "execution_verbs": ("bend",),
        },
        {
            "principle_id": "book:case:65:bend+shift",
            "lineage_base_operative_id": "book:operative:bend",
            "generation_stage": "case_study",
            "execution_verbs": ("bend", "shift"),
        },
    )


def _authority(lineage, *, geometry="geometry-a", program="program-a", review="review-a"):
    parent_key = candidate_generation.canonical_lineage_parent_key(lineage)
    return {
        parent_key: {
            "parent_key": parent_key,
            "geometry_hash": geometry,
            "program_hash": program,
            "base_review_fingerprint": review,
        }
    }


def _schedule(
    lineage,
    *,
    causal_request_hash,
    authority,
    attempted=(),
    variant_count=1,
    principles=None,
    selected_principle_ids=None,
):
    evidence = {}
    scheduled = candidate_generation._canonical_descendant_tuple_schedule(
        principles or _principles(),
        (lineage,),
        seed=candidate_generation.VerbSequence(
            name="reviewed-bend-seed",
            label="reviewed bend",
            calls=(),
            notes=(),
        ),
        seed_index=0,
        selected_principle_ids=selected_principle_ids,
        descendant_probe_count=2,
        variant_count=variant_count,
        schedule_cap=4,
        rotation_offset=0,
        replenishment_causal_request_hash=causal_request_hash,
        reviewed_parent_authority=authority,
        attempted_work_keys=frozenset(attempted),
        work_disposition_evidence=evidence,
    )
    return scheduled, evidence


def test_identical_zero_author_cycles_schedule_exact_descendant_work_once():
    lineage = _lineage()
    authority = _authority(lineage)
    materialized = []

    first, first_evidence = _schedule(
        lineage,
        causal_request_hash="request-a",
        authority=authority,
    )
    assert first_evidence.get("attempted_work_dispositions", []) == []
    first_identity = candidate_generation._replenishment_descendant_work_identity(
        first[0][4],
        principle_id=first[0][1]["principle_id"],
        variant_index=first[0][2],
        causal_request_hash="request-a",
        reviewed_parent_authority=authority,
    )
    candidate_generation._begin_replenishment_work_disposition(
        first_identity,
        evidence=first_evidence,
    )
    materialized.append(first[0])
    attempted = {
        record["work_key"]
        for record in first_evidence["attempted_work_dispositions"]
    }
    second, second_evidence = _schedule(
        lineage,
        causal_request_hash="request-a",
        authority=authority,
        attempted=attempted,
    )
    materialized.extend(second)

    assert len(first) == 1
    assert second == ()
    assert len(materialized) == 1
    assert second_evidence["skipped_attempted_work_count"] == 1


def test_cap_leaves_scheduled_but_unbegun_work_eligible_next_cycle():
    lineage = _lineage()
    authority = _authority(lineage)
    scheduled, evidence = _schedule(
        lineage,
        causal_request_hash="request-a",
        authority=authority,
        variant_count=2,
    )
    assert len(scheduled) == 2
    assert evidence.get("attempted_work_dispositions", []) == []

    first = scheduled[0]
    first_identity = candidate_generation._replenishment_descendant_work_identity(
        first[4],
        principle_id=first[1]["principle_id"],
        variant_index=first[2],
        causal_request_hash="request-a",
        reviewed_parent_authority=authority,
    )
    candidate_generation._begin_replenishment_work_disposition(
        first_identity,
        evidence=evidence,
    )
    attempted = {
        record["work_key"]
        for record in evidence["attempted_work_dispositions"]
    }

    next_cycle, _ = _schedule(
        lineage,
        causal_request_hash="request-a",
        authority=authority,
        attempted=attempted,
        variant_count=2,
    )

    assert len(next_cycle) == 1
    assert next_cycle[0][2] == scheduled[1][2]


def test_attempted_work_uses_actual_terminal_stage_and_reason():
    evidence = {"attempted_work_dispositions": []}
    record = candidate_generation._begin_replenishment_work_disposition(
        {
            "work_key": "work-a",
            "parent_authority_fingerprint": "parent-a",
            "causal_request_hash": "request-a",
            "child_principle_id": "book:case:65:bend+shift",
            "variant_index": 0,
        },
        evidence=evidence,
    )

    candidate_generation._finalize_replenishment_work_dispositions(
        evidence,
        terminal_records=({
            "stage": "materialization",
            "evidence": {
                "failure_reason": "profiled_legal_clip_mesh_revalidation_failed",
            },
        },),
    )

    assert record["terminal_stage"] == "materialization"
    assert record["terminal_reason"] == (
        "profiled_legal_clip_mesh_revalidation_failed"
    )


def test_changed_deficit_request_or_parent_authority_allows_retry():
    lineage = _lineage()
    authority = _authority(lineage)
    first, evidence = _schedule(
        lineage,
        causal_request_hash="request-a",
        authority=authority,
    )
    first_identity = candidate_generation._replenishment_descendant_work_identity(
        first[0][4],
        principle_id=first[0][1]["principle_id"],
        variant_index=first[0][2],
        causal_request_hash="request-a",
        reviewed_parent_authority=authority,
    )
    candidate_generation._begin_replenishment_work_disposition(
        first_identity,
        evidence=evidence,
    )
    attempted = {
        record["work_key"]
        for record in evidence["attempted_work_dispositions"]
    }

    unchanged, _ = _schedule(
        lineage,
        causal_request_hash="request-a",
        authority=authority,
        attempted=attempted,
    )

    changed_request, _ = _schedule(
        lineage,
        causal_request_hash="request-b",
        authority=authority,
        attempted=attempted,
    )
    repaired_parent, _ = _schedule(
        lineage,
        causal_request_hash="request-a",
        authority=_authority(
            lineage,
            geometry="geometry-repaired",
            program="program-repaired",
            review="review-repaired",
        ),
        attempted=attempted,
    )

    assert len(first) == 1
    assert unchanged == ()
    assert len(changed_request) == 1
    assert len(repaired_parent) == 1


def test_candidate_terminal_disposition_releases_repaired_identity_only():
    original = SimpleNamespace(source=SimpleNamespace(metadata={
        "final_program_hash": "program-a",
        "final_geometry_hash": "geometry-a",
        "final_surface_payload_hash": "surface-a",
    }))
    repaired = deepcopy(original)
    repaired.source.metadata["final_program_hash"] = "program-repaired"
    repaired.source.metadata["final_geometry_hash"] = "geometry-repaired"
    repaired.source.metadata["final_surface_payload_hash"] = "surface-repaired"
    disposition = portfolio_replenishment.ReplenishmentWorkDisposition(
        work_key="generation-work",
        parent_authority_fingerprint="parent-authority",
        causal_request_hash="request-a",
        child_principle_id="book:case:65:bend+shift",
        variant_index=0,
        candidate_identity_hash=(
            portfolio_replenishment.candidate_disposition_identity_hash(original)
        ),
        terminal_stage="downstream",
        terminal_reason="combined_hard_fail",
        cycle_index=1,
    )

    pending, skipped = portfolio_replenishment.filter_terminal_reserve_candidates(
        [original, repaired],
        causal_request_hash="request-a",
        dispositions=(disposition,),
    )

    assert pending == [repaired]
    assert skipped == 1


def test_live_state_retains_hard_passes_separately_and_never_re_reviews_them():
    retained = SimpleNamespace(name="retained-final-hard-pass")
    reviewed_fingerprint = ("program-a", "geometry-a")
    state = portfolio_benchmark._initial_replenishment_live_state(
        [],
        reviewed_final_vlm_fingerprints={reviewed_fingerprint},
        replenishment_work_dispositions=(),
    )
    received = {}

    def boundary(_cycle_function, **kwargs):
        received.update(kwargs)
        return SimpleNamespace(
            selection_pool=[retained],
            live_qd_reserve=[],
            reviewed_final_vlm_fingerprints={reviewed_fingerprint},
            certified_reviewed_base_parents=(),
            replenishment_work_dispositions=(),
        )

    cycle, next_state = portfolio_benchmark._run_replenishment_cycle_with_live_state(
        boundary,
        object(),
        state=state,
        retained_selection_pool=[retained],
    )

    assert cycle.selection_pool == [retained]
    assert received["reviewed_final_vlm_fingerprints"] == {reviewed_fingerprint}
    assert next_state.reviewed_final_vlm_fingerprints == frozenset(
        {reviewed_fingerprint}
    )


def test_work_disposition_state_is_immutable_deterministic_and_bounded():
    records = tuple(
        portfolio_replenishment.ReplenishmentWorkDisposition(
            work_key=f"work-{index:04d}",
            parent_authority_fingerprint=f"parent-{index % 3}",
            causal_request_hash="request-a",
            child_principle_id="book:case:65:bend+shift",
            variant_index=index,
            candidate_identity_hash="",
            terminal_stage="generation",
            terminal_reason="attempted",
            cycle_index=index,
        )
        for index in range(300)
    )

    forward = portfolio_replenishment.bounded_replenishment_work_dispositions(
        records
    )
    reverse = portfolio_replenishment.bounded_replenishment_work_dispositions(
        tuple(reversed(records))
    )

    assert len(forward) == 256
    assert forward == reverse
    assert forward[0].cycle_index == 44
    assert forward[-1].cycle_index == 299


@pytest.mark.parametrize(
    "builder_kwargs",
    [
        {"legal_fit_repair_feedback": _legal_fit_feedback()},
        {"capacity_authoring_deficits": _capacity_deficit()},
        {"family_supply_deficits": _family_deficits()},
        {"base_book_vlm_replenishment_feedback": _base_feedback()},
        {
            "authored_visual_authority_replenishment_feedback": (
                _authored_feedback()
            )
        },
        {
            "request_updates": {
                "selector_stage_outcomes": [{
                    "schema_version": "arr.maas.stage_outcome.v1",
                    "stage": "portfolio_selection",
                    "kind": "failed",
                    "reason": "silhouette_near_duplicate",
                    "missing_descriptor_cells": ["body:courtyard"],
                    "evidence": {"distance": 0.01},
                }],
                "candidate_supply_deficits": [{
                    "schema_version": "arr.maas.candidate_supply_deficit.v1",
                    "type": "candidate_supply_exhausted",
                    "reason": "candidate_supply_exhausted",
                    "required_scope_ids": ["1/8"],
                    "required_principle_ids": ["book:case:65:bend+shift"],
                }],
            }
        },
    ],
    ids=(
        "legal_fit",
        "capacity",
        "family_supply",
        "base_book_vlm",
        "authored_visual_authority",
        "selector_candidate_supply",
    ),
)
def test_production_deficit_categories_change_causal_hash(builder_kwargs):
    baseline = _production_replenishment_requests()
    changed = _production_replenishment_requests(**builder_kwargs)

    assert portfolio_replenishment.replenishment_causal_request_hash(
        changed
    ) != portfolio_replenishment.replenishment_causal_request_hash(baseline)


@pytest.mark.parametrize(
    ("field", "changed_value"),
    [
        ("gfa_deficit_m2", 25.0),
        ("per_floor_gfa_deficits_m2", [8.0, 7.0, 6.0, 4.0]),
        ("vertical_support_ratio", 0.61),
        ("minimum_clear_depth_m", 7.5),
        ("outside_distance_m", 0.75),
        ("outside_area_m2", 4.5),
        ("typed_reasons", ["occupied_outside_legal_geometry"]),
    ],
)
def test_capacity_geometry_targets_change_causal_hash(field, changed_value):
    baseline = _production_replenishment_requests(
        capacity_authoring_deficits=_capacity_deficit()
    )
    changed = _production_replenishment_requests(
        capacity_authoring_deficits=_capacity_deficit(**{field: changed_value})
    )

    assert portfolio_replenishment.replenishment_causal_request_hash(
        changed
    ) != portfolio_replenishment.replenishment_causal_request_hash(baseline)


@pytest.mark.parametrize(
    ("field", "changed_value"),
    [
        ("body_phenotype_shortfall", 1),
        ("overrepresented_body_phenotype_counts", {"stepped": 4}),
        ("overrepresented_geometry_family_counts", {"llm_bend_notch": 4}),
        ("missing_descriptor_cells", ["body:winged"]),
        ("visible_stepped_excess", 1),
    ],
)
def test_family_supply_geometry_deficits_change_causal_hash(field, changed_value):
    baseline = _production_replenishment_requests(
        family_supply_deficits=_family_deficits()
    )
    changed = _production_replenishment_requests(
        family_supply_deficits=_family_deficits(**{field: changed_value})
    )

    assert portfolio_replenishment.replenishment_causal_request_hash(
        changed
    ) != portfolio_replenishment.replenishment_causal_request_hash(baseline)


def test_legal_target_delta_and_typed_feedback_reasons_change_causal_hash():
    legal_a = _production_replenishment_requests(
        legal_fit_repair_feedback=_legal_fit_feedback(97.436)
    )
    legal_b = _production_replenishment_requests(
        legal_fit_repair_feedback=_legal_fit_feedback(99.0)
    )
    base_a = _production_replenishment_requests(
        base_book_vlm_replenishment_feedback=_base_feedback()
    )
    base_b = _production_replenishment_requests(
        base_book_vlm_replenishment_feedback=_base_feedback(
            "final_book_vlm_wrong_program_typology"
        )
    )
    authored_a = _production_replenishment_requests(
        authored_visual_authority_replenishment_feedback=_authored_feedback()
    )
    authored_b = _production_replenishment_requests(
        authored_visual_authority_replenishment_feedback=_authored_feedback(
            "profiled_legal_clip_floor_center_topology_mismatch"
        )
    )

    for left, right in ((legal_a, legal_b), (base_a, base_b), (authored_a, authored_b)):
        assert portfolio_replenishment.replenishment_causal_request_hash(
            left
        ) != portfolio_replenishment.replenishment_causal_request_hash(right)


def test_run_cycle_separates_stable_causal_hash_from_effective_context_hash(
    monkeypatch,
    tmp_path,
):
    supplied = {"principle_id_counts": {"book:operative:bend": 1}, "principle_kind_counts": {}}
    captured = []

    monkeypatch.setattr(
        portfolio_replenishment,
        "book_graph_supply_for_candidates",
        lambda _pool: deepcopy(supplied),
    )

    def program_pool(*_args, **kwargs):
        captured.append(kwargs)
        return [], {"two_phase_base_vlm": {"active": False}}

    monkeypatch.setattr(portfolio_replenishment, "_program_pool", program_pool)

    requests = _production_replenishment_requests(
        legal_fit_repair_feedback=[
            *_legal_fit_feedback(),
            {**_legal_fit_feedback()[0], "typed_reasons": ["target_exceeds_legal_section"]},
        ],
        capacity_authoring_deficits=_capacity_deficit(),
        family_supply_deficits=_family_deficits(),
        base_book_vlm_replenishment_feedback=_base_feedback(),
        authored_visual_authority_replenishment_feedback=_authored_feedback(),
        request_updates={
            "selector_stage_outcomes": [
                {"stage": "portfolio_selection", "reason": "silhouette_near_duplicate"},
                {"stage": "portfolio_selection", "reason": "missing_descriptor_cells"},
            ],
        },
    )

    def run(active_requests):
        return portfolio_replenishment.run_replenishment_cycle(
            cycle_index=len(captured) + 1,
            parent_variant_index=len(captured) + 1,
            retained_selection_pool=[],
            excluded_parent_keys=set(),
            excluded_parent_fingerprints=set(),
            excluded_program_hashes=set(),
            generation_site=SimpleNamespace(),
            building_type="neighborhood_living",
            height=14.0,
            floors=4,
            generation_context=None,
            typed_graph_mutations=[],
            geometry_program_mutations=[],
            synthesis_requests=active_requests,
            outcome_graph=None,
            recursive_only=True,
            program_dimensional_context={},
            site_boundary_source="test",
            site_access_context={},
            site_access_geometry={},
            runtime_live_vlm=False,
            live_vlm_selection_required=False,
            base_capacity_contract={},
            trusted_legal_floor_field={},
            trusted_legal_floor_field_hash="",
            trusted_clear_span_floor_plan={},
            capacity_site=SimpleNamespace(),
            output_dir=tmp_path,
            program_slug="neighborhood",
            visual_directive={},
            downstream_context={},
            hard_gate_summary=lambda _report, pool: {"candidate_count": len(pool)},
        )

    run(requests)
    first_causal_hash = captured[-1]["_replenishment_causal_request_hash"]
    first_context_hash = captured[-1]["_replenishment_effective_context_hash"]
    assert first_causal_hash == (
        portfolio_replenishment.replenishment_causal_request_hash(
            captured[-1]["synthesis_requests"]
        )
    )
    assert first_context_hash == (
        portfolio_replenishment.replenishment_effective_context_hash(
            captured[-1]["synthesis_requests"]
        )
    )
    assert first_context_hash == portfolio_replenishment.replenishment_request_hash(
        captured[-1]["synthesis_requests"]
    )
    supplied["principle_id_counts"]["book:operative:bend"] = 2
    changed_context = _production_replenishment_requests(
        legal_fit_repair_feedback=list(reversed([
            *_legal_fit_feedback(),
            {**_legal_fit_feedback()[0], "typed_reasons": ["target_exceeds_legal_section"]},
        ])),
        capacity_authoring_deficits=_capacity_deficit(),
        family_supply_deficits=_family_deficits(),
        base_book_vlm_replenishment_feedback=_base_feedback(),
        authored_visual_authority_replenishment_feedback=_authored_feedback(),
        request_updates={
            "selector_stage_outcomes": list(reversed([
                {"stage": "portfolio_selection", "reason": "silhouette_near_duplicate"},
                {"stage": "portfolio_selection", "reason": "missing_descriptor_cells"},
            ])),
            "provider_response_id": "provider-second",
            "timestamp": "second",
        },
        selected_count=2,
        selected_scope_count=2,
        cycle_index=2,
    )
    run(changed_context)

    assert captured[-1]["_replenishment_causal_request_hash"] == first_causal_hash
    assert captured[-1]["_replenishment_effective_context_hash"] != first_context_hash


def test_real_deficit_cell_changes_causal_request_hash():
    request = _production_replenishment_requests(
        family_supply_deficits=_family_deficits(
            missing_descriptor_cells=["body:winged"]
        )
    )
    changed = _production_replenishment_requests(
        family_supply_deficits=_family_deficits(
            missing_descriptor_cells=["body:courtyard"]
        )
    )

    assert portfolio_replenishment.replenishment_causal_request_hash(
        request
    ) != portfolio_replenishment.replenishment_causal_request_hash(changed)


def test_supply_growth_does_not_reopen_attempted_parent_child_variant():
    lineage = _lineage()
    authority = _authority(lineage)
    request = _production_replenishment_requests(
        family_supply_deficits=_family_deficits(
            missing_descriptor_cells=["body:winged"]
        )
    )
    request[0]["book_graph_supply"] = {
        "principle_id_counts": {"book:operative:bend": 1}
    }
    causal_hash = portfolio_replenishment.replenishment_causal_request_hash(
        request
    )
    first, evidence = _schedule(
        lineage,
        causal_request_hash=causal_hash,
        authority=authority,
    )
    identity = candidate_generation._replenishment_descendant_work_identity(
        first[0][4],
        principle_id=first[0][1]["principle_id"],
        variant_index=first[0][2],
        causal_request_hash=causal_hash,
        reviewed_parent_authority=authority,
    )
    candidate_generation._begin_replenishment_work_disposition(
        identity,
        evidence=evidence,
    )
    attempted = {record["work_key"] for record in evidence["attempted_work_dispositions"]}
    request[0]["book_graph_supply"]["principle_id_counts"]["book:operative:bend"] = 9
    request[0]["candidate_count"] = 99
    request[0]["llm_author_count"] = 99
    next_causal_hash = portfolio_replenishment.replenishment_causal_request_hash(
        request
    )
    second, second_evidence = _schedule(
        lineage,
        causal_request_hash=next_causal_hash,
        authority=authority,
        attempted=attempted,
    )

    assert next_causal_hash == causal_hash
    assert second == ()
    assert second_evidence["skipped_attempted_work_count"] == 1


def test_new_child_variant_and_repaired_parent_authority_remain_eligible():
    lineage = _lineage()
    authority = _authority(lineage)
    principles = (*_principles(), {
        "principle_id": "book:aggregation:stack:bend",
        "lineage_base_operative_id": "book:operative:bend",
        "generation_stage": "aggregation",
        "execution_verbs": ("bend", "stack"),
    })
    first, evidence = _schedule(
        lineage,
        causal_request_hash="stable-cause",
        authority=authority,
        principles=principles,
        selected_principle_ids=frozenset({"book:case:65:bend+shift"}),
    )
    identity = candidate_generation._replenishment_descendant_work_identity(
        first[0][4],
        principle_id=first[0][1]["principle_id"],
        variant_index=first[0][2],
        causal_request_hash="stable-cause",
        reviewed_parent_authority=authority,
    )
    candidate_generation._begin_replenishment_work_disposition(identity, evidence=evidence)
    attempted = {record["work_key"] for record in evidence["attempted_work_dispositions"]}

    new_child, _ = _schedule(
        lineage,
        causal_request_hash="stable-cause",
        authority=authority,
        attempted=attempted,
        principles=principles,
        selected_principle_ids=frozenset({"book:aggregation:stack:bend"}),
    )
    new_variant, _ = _schedule(
        lineage,
        causal_request_hash="stable-cause",
        authority=authority,
        attempted=attempted,
        variant_count=2,
        principles=principles,
        selected_principle_ids=frozenset({"book:case:65:bend+shift"}),
    )
    repaired_parent, _ = _schedule(
        lineage,
        causal_request_hash="stable-cause",
        authority=_authority(
            lineage,
            geometry="geometry-repaired",
            program="program-repaired",
            review="review-repaired",
        ),
        attempted=attempted,
        principles=principles,
        selected_principle_ids=frozenset({"book:case:65:bend+shift"}),
    )

    assert len(new_child) == 1
    assert new_variant
    assert all(item[2] != first[0][2] for item in new_variant)
    assert len(repaired_parent) == 1


def test_benchmark_two_cycle_result_hands_off_immutable_work_ledger():
    first = portfolio_replenishment.ReplenishmentWorkDisposition(
        work_key="work-first",
        parent_authority_fingerprint="parent-a",
        causal_request_hash="request-a",
        child_principle_id="book:case:65:bend+shift",
        variant_index=0,
        candidate_identity_hash="candidate-a",
        terminal_stage="downstream",
        terminal_reason="combined_hard_fail",
        cycle_index=1,
    )
    second = portfolio_replenishment.ReplenishmentWorkDisposition(
        work_key="work-second",
        parent_authority_fingerprint="parent-a",
        causal_request_hash="request-a",
        child_principle_id="book:aggregation:stack:bend",
        variant_index=1,
        candidate_identity_hash="candidate-b",
        terminal_stage="downstream",
        terminal_reason="combined_hard_fail",
        cycle_index=2,
    )
    state = portfolio_benchmark._initial_replenishment_live_state(
        [],
        reviewed_final_vlm_fingerprints=set(),
        replenishment_work_dispositions=(first,),
    )
    received = []

    def boundary(_cycle_function, **kwargs):
        incoming = tuple(kwargs["replenishment_work_dispositions"])
        received.append(incoming)
        return portfolio_replenishment.ReplenishmentCycleResult(
            selection_pool=[],
            generated_pool=[],
            downstream_evaluation_pool=[],
            downstream_report=None,
            evidence={},
            reviewed_parent_keys=set(),
            reviewed_parent_fingerprints=set(),
            live_qd_reserve=[],
            reviewed_final_vlm_fingerprints=set(),
            replenishment_work_dispositions=(
                *incoming,
                second,
            ),
        )

    _cycle, state = portfolio_benchmark._run_replenishment_cycle_with_live_state(
        boundary,
        object(),
        state=state,
    )
    _cycle, state = portfolio_benchmark._run_replenishment_cycle_with_live_state(
        boundary,
        object(),
        state=state,
    )

    assert received[0] == (first,)
    assert received[1] == (first, second)
    assert state.replenishment_work_dispositions == (first, second)


def _production_base_vlm_feedback(
    tmp_path,
    *,
    failed_gates=("book_scope_legibility", "operation_legibility"),
    geometry_edit_intents=(
        {"operation": "carve", "axis": "x", "target_depth_ratio": 0.18},
        {"operation": "shift", "axis": "y", "target_offset_m": 2.4},
    ),
    rationale="Increase BOOK legibility.",
    response_id="response-a",
):
    from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph

    graph = GeometryOutcomeGraph(tmp_path / "outcome-graph.json", "test-pnu")
    graph.observations.append({
        "stage": "book_base_vlm",
        "program_slug": "gymnasium",
        "base_book_vlm_hard_pass": False,
        "base_review_fingerprint": "base-fingerprint",
        "program_hash": "base-program-hash",
        "failed_base_book_vlm_gates": list(failed_gates),
        "base_book_vlm_audit": {
            "critic_actions": [
                {"action": "clarify_operation", "priority": "required"},
            ],
            "geometry_edits": list(geometry_edit_intents),
            "rationale": rationale,
            "response_id": response_id,
        },
    })
    return graph.base_book_vlm_replenishment_feedback(
        program_slug="gymnasium"
    )


def _production_selector_feedback(
    *,
    required_threshold=0.4,
    cap=3,
    portfolio_contract_deficits=("selection_count:exact_5",),
):
    outcomes = portfolio_benchmark._selector_replenishment_stage_outcomes(
        selection_trace={
            "portfolio_contract_deficits": list(portfolio_contract_deficits),
        },
        selection_capacity_diagnostics={
            "target_count": 5,
            "selected_count": 1,
            "selection_universe_count": 1,
            "remaining_candidate_count": 0,
            "reason_counts": {
                "silhouette_near_duplicate": 1,
                "book_operation_cap": 1,
            },
            "exclusive_reason_counts": {
                "silhouette_near_duplicate": 1,
                "book_operation_cap": 1,
            },
            "minimum_silhouette_distance_summary": {
                "minimum": 0.2,
                "mean": 0.25,
                "maximum": 0.3,
            },
            "caps": {
                "silhouette_distance_minimum": required_threshold,
                "book_operation": cap,
            },
        },
        family_supply_deficits={},
    )
    return portfolio_benchmark._bounded_replenishment_causal_feedback(
        [], stage_outcomes=outcomes
    )


@pytest.mark.parametrize(
    "changed_feedback",
    (
        lambda tmp_path: _production_base_vlm_feedback(
            tmp_path,
            failed_gates=("book_scope_legibility", "mass_coherence"),
        ),
        lambda tmp_path: _production_base_vlm_feedback(
            tmp_path,
            geometry_edit_intents=(
                {"operation": "carve", "axis": "x", "target_depth_ratio": 0.31},
                {"operation": "shift", "axis": "y", "target_offset_m": 2.4},
            ),
        ),
    ),
)
def test_production_base_vlm_control_changes_causal_hash(tmp_path, changed_feedback):
    baseline = _production_replenishment_requests(
        base_book_vlm_replenishment_feedback=_production_base_vlm_feedback(tmp_path)
    )
    changed = _production_replenishment_requests(
        base_book_vlm_replenishment_feedback=changed_feedback(tmp_path)
    )

    assert portfolio_replenishment.replenishment_causal_request_hash(baseline) != (
        portfolio_replenishment.replenishment_causal_request_hash(changed)
    )


@pytest.mark.parametrize(
    "changed_feedback",
    (
        lambda: _production_selector_feedback(required_threshold=0.47),
        lambda: _production_selector_feedback(cap=2),
        lambda: _production_selector_feedback(
            portfolio_contract_deficits=("selection_count:exact_6",)
        ),
    ),
)
def test_production_selector_control_changes_causal_hash(changed_feedback):
    baseline = _production_replenishment_requests(
        authored_visual_authority_replenishment_feedback=_production_selector_feedback()
    )
    changed = _production_replenishment_requests(
        authored_visual_authority_replenishment_feedback=changed_feedback()
    )

    assert portfolio_replenishment.replenishment_causal_request_hash(baseline) != (
        portfolio_replenishment.replenishment_causal_request_hash(changed)
    )


def test_production_control_hash_ignores_response_prose_and_order(tmp_path):
    reordered_base = _production_base_vlm_feedback(
        tmp_path,
        failed_gates=("operation_legibility", "book_scope_legibility"),
        geometry_edit_intents=(
            {"operation": "shift", "axis": "y", "target_offset_m": 2.4},
            {"operation": "carve", "axis": "x", "target_depth_ratio": 0.18},
        ),
        rationale="Different explanatory prose that is not a control.",
        response_id="response-b",
    )
    baseline_selector = _production_selector_feedback()
    reordered_selector = list(reversed(_production_selector_feedback()))
    for record in reordered_selector:
        record["response_id"] = "selector-response-b"
        record["rationale"] = "Different selector prose."
        record.setdefault("evidence", {})["narrative"] = "Ignore this prose."

    baseline = _production_replenishment_requests(
        base_book_vlm_replenishment_feedback=_production_base_vlm_feedback(tmp_path),
        authored_visual_authority_replenishment_feedback=baseline_selector,
    )
    changed_context = _production_replenishment_requests(
        base_book_vlm_replenishment_feedback=reordered_base,
        authored_visual_authority_replenishment_feedback=reordered_selector,
    )

    assert portfolio_replenishment.replenishment_causal_request_hash(baseline) == (
        portfolio_replenishment.replenishment_causal_request_hash(changed_context)
    )


def _all_production_causal_feedback_requests(tmp_path):
    return _production_replenishment_requests(
        legal_fit_repair_feedback=_legal_fit_feedback(),
        capacity_authoring_deficits=_capacity_deficit(),
        family_supply_deficits=_family_deficits(),
        base_book_vlm_replenishment_feedback=(
            _production_base_vlm_feedback(tmp_path)
        ),
        authored_visual_authority_replenishment_feedback=[
            *_authored_feedback(),
            *_production_selector_feedback(),
        ],
    )


def test_identical_production_feedback_multiplicity_and_order_are_not_causal(
    tmp_path,
):
    single = _all_production_causal_feedback_requests(tmp_path)
    duplicate = json.loads(json.dumps(single))
    duplicate.append(json.loads(json.dumps(single[0])))
    for request in duplicate:
        for field in (
            "legal_fit_repair_feedback",
            "capacity_authoring_deficits",
            "base_book_vlm_replenishment_feedback",
            "authored_visual_authority_replenishment_feedback",
        ):
            request[field] = list(reversed(request[field]))

    assert portfolio_replenishment.replenishment_causal_request_hash(single) == (
        portfolio_replenishment.replenishment_causal_request_hash(duplicate)
    )
    assert portfolio_replenishment.replenishment_effective_context_hash(single) != (
        portfolio_replenishment.replenishment_effective_context_hash(duplicate)
    )


def test_distinct_production_typed_targets_and_reasons_remain_causal(tmp_path):
    baseline = _all_production_causal_feedback_requests(tmp_path)

    def changed(mutator):
        payload = json.loads(json.dumps(baseline))
        mutator(payload[0])
        return payload

    variants = (
        changed(lambda request: request["legal_fit_repair_feedback"][0][
            "measured_values"
        ].__setitem__("target_total_m2", 301.25)),
        changed(lambda request: request["capacity_authoring_deficits"][0].__setitem__(
            "gfa_deficit_m2", 31.5
        )),
        changed(lambda request: request["family_supply_deficits"].__setitem__(
            "body_phenotype_shortfall", 3
        )),
        changed(lambda request: request["base_book_vlm_replenishment_feedback"][0].__setitem__(
            "failed_gates", ["mass_coherence"]
        )),
        changed(lambda request: next(
            item
            for item in request[
                "authored_visual_authority_replenishment_feedback"
            ]
            if item.get("reason") == "silhouette_near_duplicate"
        )["evidence"].__setitem__("required_threshold", 0.47)),
    )

    baseline_hash = portfolio_replenishment.replenishment_causal_request_hash(
        baseline
    )
    assert all(
        portfolio_replenishment.replenishment_causal_request_hash(variant)
        != baseline_hash
        for variant in variants
    )


def test_duplicate_production_feedback_keeps_existing_work_suppressed(tmp_path):
    single = _all_production_causal_feedback_requests(tmp_path)
    duplicate = [
        json.loads(json.dumps(single[0])),
        json.loads(json.dumps(single[0])),
    ]
    first_hash = portfolio_replenishment.replenishment_causal_request_hash(single)
    duplicate_hash = portfolio_replenishment.replenishment_causal_request_hash(
        duplicate
    )
    lineage = _lineage()
    authority = _authority(lineage)
    first, evidence = _schedule(
        lineage,
        causal_request_hash=first_hash,
        authority=authority,
    )
    identity = candidate_generation._replenishment_descendant_work_identity(
        first[0][4],
        principle_id=first[0][1]["principle_id"],
        variant_index=first[0][2],
        causal_request_hash=first_hash,
        reviewed_parent_authority=authority,
    )
    candidate_generation._begin_replenishment_work_disposition(
        identity,
        evidence=evidence,
    )
    attempted = {
        record["work_key"]
        for record in evidence["attempted_work_dispositions"]
    }
    repeated, repeated_evidence = _schedule(
        lineage,
        causal_request_hash=duplicate_hash,
        authority=authority,
        attempted=attempted,
    )

    assert duplicate_hash == first_hash
    assert repeated == ()
    assert repeated_evidence["skipped_attempted_work_count"] == 1
