import json
from types import SimpleNamespace

import pytest
from shapely.geometry import box

from design.maas.book_language.portfolio_benchmark import (
    _bounded_replenishment_causal_feedback,
    _deficit_directed_replenishment_inputs,
    _post_selection_family_supply_deficits,
    _next_synthesis_inputs_from_selector_state,
    _select_with_replenishment_state,
    _selector_replenishment_state_boundary,
    _selector_replenishment_stage_outcomes,
    SelectorReplenishmentState,
)


def test_selector_failures_feed_next_synthesis_request_without_geometry_payloads():
    outcomes = _selector_replenishment_stage_outcomes(
        selection_trace={
            "portfolio_contract_deficits": ["missing_descriptor_cells"],
            "coordinates": [[1.0, 2.0, 3.0]],
            "images": ["selector.png"],
        },
        selection_capacity_diagnostics={
            "reason_counts": {
                "silhouette_near_duplicate": 2,
                "book_operation_cap": 1,
                "section_family_cap": 1,
            },
            "exclusive_reason_counts": {
                "silhouette_near_duplicate": 1,
            },
            "minimum_silhouette_distance_summary": {
                "minimum": 0.17,
                "mean": 0.23,
                "maximum": 0.31,
            },
            "caps": {
                "silhouette_distance_minimum": 0.4,
                "book_operation": 3,
                "section_family": 2,
            },
            "vertices": [[0.0, 0.0, 14.0]],
            "surfaces": [{"role": "roof"}],
        },
        family_supply_deficits={
            "missing_descriptor_cells": [
                "body_phenotype:elliptical",
                "roof_archetype:curved",
            ],
            "mesh_payload": {"triangles": [[0, 1, 2]]},
            "image_url": "unsafe.png",
        },
    )
    feedback = _bounded_replenishment_causal_feedback(
        [],
        stage_outcomes=outcomes,
    )
    inputs = _deficit_directed_replenishment_inputs(
        [{"candidate_count": 8, "llm_author_count": 8}],
        legal_fit_repair_feedback=[],
        capacity_authoring_deficits=[],
        family_supply_deficits={},
        authored_visual_authority_replenishment_feedback=feedback,
        progressive_target=5,
        selected_count=1,
        selected_scope_count=1,
        target_count=5,
        required_scope_count=3,
        exact_compile_remaining=8,
        cycle_index=2,
        cycle_budget=3,
    )

    next_feedback = inputs["synthesis_requests"][0][
        "authored_visual_authority_replenishment_feedback"
    ]
    by_reason = {item["reason"]: item for item in next_feedback}
    assert by_reason["silhouette_near_duplicate"]["evidence"][
        "measured_distance"
    ] == 0.17
    assert by_reason["silhouette_near_duplicate"]["evidence"][
        "required_threshold"
    ] == 0.4
    assert by_reason["book_operation_cap"]["evidence"]["cap"] == 3
    assert by_reason["section_family_cap"]["evidence"]["cap"] == 2
    assert by_reason["missing_descriptor_cells"]["evidence"][
        "missing_descriptor_cells"
    ] == ["body_phenotype:elliptical", "roof_archetype:curved"]
    assert len(next_feedback) <= 12

    serialized = json.dumps(next_feedback, sort_keys=True).lower()
    for forbidden in (
        '"coordinate"',
        '"coordinates"',
        '"vertices"',
        '"vertices_m"',
        '"surfaces"',
        '"surface_payload"',
        '"mesh_payload"',
        '"image"',
        '"image_url"',
        '"triangles"',
    ):
        assert forbidden not in serialized


def test_candidate_supply_exhausted_is_independent_of_exclusion_reasons():
    outcomes = _selector_replenishment_stage_outcomes(
        selection_trace={
            "portfolio_contract_deficits": ["selection_count:exact_5"],
        },
        selection_capacity_diagnostics={
            "target_count": 5,
            "selected_count": 1,
            "selection_universe_count": 1,
            "remaining_candidate_count": 0,
            "reason_counts": {},
            "exclusive_reason_counts": {},
        },
        family_supply_deficits={
            "target_count": 5,
            "visible_stepped_count": 1,
        },
    )

    assert outcomes == [{
        "kind": "failed",
        "stage": "portfolio_selection",
        "reason": "candidate_supply_exhausted",
        "target_count": 5,
        "selected_count": 1,
        "selection_universe_count": 1,
        "remaining_candidate_count": 0,
        "candidate_supply_shortfall": 4,
        "portfolio_contract_deficits": ["selection_count:exact_5"],
        "evidence": {
            "target_count": 5,
            "selected_count": 1,
            "selection_universe_count": 1,
            "remaining_candidate_count": 0,
            "candidate_supply_shortfall": 4,
            "portfolio_contract_deficits": ["selection_count:exact_5"],
        },
    }]


def test_candidate_supply_outcome_absent_when_target_reached():
    outcomes = _selector_replenishment_stage_outcomes(
        selection_trace={"portfolio_contract_deficits": []},
        selection_capacity_diagnostics={
            "target_count": 5,
            "selected_count": 5,
            "selection_universe_count": 5,
            "remaining_candidate_count": 0,
            "reason_counts": {},
        },
        family_supply_deficits={},
    )

    assert outcomes == []


def test_remaining_candidate_keeps_existing_selector_exclusion_outcome():
    outcomes = _selector_replenishment_stage_outcomes(
        selection_trace={"portfolio_contract_deficits": []},
        selection_capacity_diagnostics={
            "target_count": 5,
            "selected_count": 1,
            "selection_universe_count": 2,
            "remaining_candidate_count": 1,
            "reason_counts": {"book_operation_cap": 1},
            "exclusive_reason_counts": {"book_operation_cap": 1},
            "caps": {"book_operation": 3},
        },
        family_supply_deficits={},
    )

    assert [item["reason"] for item in outcomes] == ["book_operation_cap"]
    assert outcomes[0]["evidence"]["cap"] == 3


def test_family_supply_is_recomputed_from_selected_then_excluded(monkeypatch):
    from design.maas.book_language import portfolio_benchmark

    selected = object()
    excluded_a = object()
    excluded_b = object()
    seen = {}

    def family_deficits(candidates, **_kwargs):
        seen["candidates"] = list(candidates)
        return {"body_phenotype_shortfall": 2}

    monkeypatch.setattr(
        portfolio_benchmark,
        "family_supply_deficits_for_candidates",
        family_deficits,
    )
    result = _post_selection_family_supply_deficits(
        [excluded_a, selected, excluded_b],
        [selected],
        target_count=5,
        compatibility_analysis=object(),
        selection_trace={"portfolio_contract_deficits": ["missing_cell:a"]},
        selection_capacity_diagnostics={
            "reason_counts": {"book_operation_cap": 2},
        },
    )

    assert seen["candidates"] == [selected, excluded_a, excluded_b]
    assert result["body_phenotype_shortfall"] == 2
    assert result["candidate_supply_count"] == 3
    assert result["candidate_supply_shortfall"] == 2
    assert result["selection_exclusion_evidence"] == {
        "reason_counts": {"book_operation_cap": 2},
        "portfolio_contract_deficits": ["missing_cell:a"],
    }

    inputs = _deficit_directed_replenishment_inputs(
        [{"candidate_count": 4}],
        legal_fit_repair_feedback=[],
        capacity_authoring_deficits=[],
        family_supply_deficits=result,
        progressive_target=5,
        selected_count=1,
        selected_scope_count=1,
        target_count=5,
        required_scope_count=3,
        exact_compile_remaining=4,
    )
    assert inputs["synthesis_requests"][0]["family_supply_deficits"][
        "selection_exclusion_evidence"
    ] == result["selection_exclusion_evidence"]


def test_repeated_selector_feedback_keeps_newest_payload_and_merges_sources():
    stale_outcome = {
        "kind": "failed",
        "stage": "portfolio_selection",
        "reason": "silhouette_near_duplicate",
        "measured_distance": 0.12,
        "required_threshold": 0.35,
        "excluded_candidate_count": 1,
        "missing_descriptor_cells": ["old-cell"],
        "evidence": {},
    }
    stale = _bounded_replenishment_causal_feedback(
        [],
        stage_outcomes=[stale_outcome],
    )
    stale[0]["feedback_source"] = "selector_cycle_1"
    stale[0]["feedback_sources"] = ["selector_cycle_1"]
    newest_outcome = {
        "kind": "failed",
        "stage": "portfolio_selection",
        "reason": "silhouette_near_duplicate",
        "measured_distance": 0.28,
        "required_threshold": 0.4,
        "excluded_candidate_count": 4,
        "missing_descriptor_cells": ["new-cell-a", "new-cell-b"],
        "evidence": {},
    }

    feedback = _bounded_replenishment_causal_feedback(
        stale,
        stage_outcomes=[newest_outcome],
    )

    assert len(feedback) == 1
    record = feedback[0]
    assert record["feedback_sources"] == [
        "selector_cycle_1",
        "stage_outcome",
    ]
    assert record["evidence"]["measured_distance"] == 0.28
    assert record["evidence"]["required_threshold"] == 0.4
    assert record["evidence"]["excluded_candidate_count"] == 4
    assert record["evidence"]["missing_descriptor_cells"] == [
        "new-cell-a",
        "new-cell-b",
    ]


def test_refreshed_selector_feedback_moves_to_tail_before_cap():
    stale_outcome = {
        "kind": "failed",
        "stage": "portfolio_selection",
        "reason": "silhouette_near_duplicate",
        "measured_distance": 0.11,
        "required_threshold": 0.35,
        "excluded_candidate_count": 1,
        "evidence": {},
    }
    existing = _bounded_replenishment_causal_feedback(
        [],
        stage_outcomes=[stale_outcome],
    )
    existing.extend({
        "stage": "final_book_vlm",
        "reason": f"unique-{index}",
        "feedback_source": "test",
    } for index in range(4))
    refreshed = {
        **stale_outcome,
        "measured_distance": 0.29,
        "required_threshold": 0.4,
        "excluded_candidate_count": 5,
    }

    feedback = _bounded_replenishment_causal_feedback(
        existing,
        stage_outcomes=[refreshed],
        limit=4,
    )

    selector = next(
        item
        for item in feedback
        if item["reason"] == "silhouette_near_duplicate"
    )
    assert selector["evidence"]["measured_distance"] == 0.29
    assert selector["evidence"]["required_threshold"] == 0.4
    assert selector["evidence"]["excluded_candidate_count"] == 5


def test_selector_state_boundary_builds_next_cycle_evidence(monkeypatch):
    from design.maas.book_language import portfolio_benchmark

    selected = object()
    excluded = object()
    monkeypatch.setattr(
        portfolio_benchmark,
        "_selection_capacity_diagnostics",
        lambda *_args, **_kwargs: {
            "reason_counts": {"section_family_cap": 2},
            "caps": {"section_family": 1},
        },
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "family_supply_deficits_for_candidates",
        lambda candidates, **_kwargs: {
            "ordered_candidate_ids": [id(item) for item in candidates],
            "missing_descriptor_cells": ["section:open"],
        },
    )

    state = _selector_replenishment_state_boundary(
        phase="initial_selection",
        selection_pool=[excluded, selected],
        selected=[selected],
        target_count=5,
        visual_directive={},
        compatibility_analysis=object(),
        selection_trace={"portfolio_contract_deficits": ["missing_cell:a"]},
        exact_repair_evidence={"failure_records": []},
        stage_outcomes=[{"kind": "passed", "stage": "compile"}],
        final_vlm_gate={"status": "complete"},
    )

    assert state.family_supply_deficits["ordered_candidate_ids"] == [
        id(selected),
        id(excluded),
    ]
    assert state.prior_cycle_causal_evidence["stage_outcomes"][-1][
        "reason"
    ] == "missing_descriptor_cells"
    assert state.phase == "initial_selection"


@pytest.mark.parametrize(
    "phase",
    ["initial_selection", "post_cycle_selection"],
)
def test_select_state_and_next_request_execute_in_order_and_consume_state(
    monkeypatch,
    phase,
):
    from design.maas.book_language import portfolio_benchmark

    events = []
    selected_candidate = object()
    frozen_state = SelectorReplenishmentState(
        phase=phase,
        selection_capacity_diagnostics={"selected_count": 1},
        family_supply_deficits={
            "selection_exclusion_evidence": {
                "reason_counts": {"book_operation_cap": 2},
            },
        },
        selector_stage_outcomes=({
            "kind": "failed",
            "stage": "portfolio_selection",
            "reason": "book_operation_cap",
            "cap": 3,
            "evidence": {},
        },),
        prior_cycle_causal_evidence={
            "exact_post_book_typed_repair": {},
            "stage_outcomes": [{
                "kind": "failed",
                "stage": "portfolio_selection",
                "reason": "book_operation_cap",
                "cap": 3,
                "evidence": {},
            }],
            "final_book_vlm_gate": {},
        },
    )

    def select(*_args, **kwargs):
        events.append("select")
        assert isinstance(kwargs["selection_trace"], dict)
        return [selected_candidate]

    def state_builder(**kwargs):
        events.append("state")
        assert kwargs["selected"] == [selected_candidate]
        assert kwargs["phase"] == phase
        return frozen_state

    def request_builder(*_args, **kwargs):
        events.append("request")
        assert kwargs["family_supply_deficits"] is (
            frozen_state.family_supply_deficits
        )
        assert kwargs[
            "authored_visual_authority_replenishment_feedback"
        ][0]["reason"] == "book_operation_cap"
        return {"synthesis_requests": [{"ok": True}], "exact_compile_limit": 1}

    monkeypatch.setattr(portfolio_benchmark, "_select", select)
    monkeypatch.setattr(
        portfolio_benchmark,
        "_selector_replenishment_state_boundary",
        state_builder,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_deficit_directed_replenishment_inputs",
        request_builder,
    )

    selected, trace, state = _select_with_replenishment_state(
        phase=phase,
        selection_pool=[selected_candidate],
        target_count=5,
        visual_directive={},
        compatibility_analysis=object(),
        allow_diagnostic_fallback=False,
        exact_repair_evidence={},
        stage_outcomes=[],
        final_vlm_gate={},
    )
    inputs, feedback = _next_synthesis_inputs_from_selector_state(
        state,
        synthesis_requests=[{"candidate_count": 4}],
        authored_visual_authority_replenishment_feedback=[],
        legal_fit_repair_feedback=[],
        capacity_authoring_deficits=[],
        progressive_target=5,
        base_book_vlm_replenishment_feedback=[],
        selected_count=len(selected),
        selected_scope_count=1,
        target_count=5,
        required_scope_count=3,
        exact_compile_remaining=4,
        cycle_index=1,
        cycle_budget=2,
        author_replenishment_remaining=2,
    )

    assert trace == {}
    assert inputs["synthesis_requests"] == [{"ok": True}]
    assert feedback[0]["reason"] == "book_operation_cap"
    assert events == ["select", "state", "request"]


def test_top_level_benchmark_consumes_initial_and_refreshed_selector_state(
    monkeypatch,
    tmp_path,
):
    from design.maas.book_language import portfolio_benchmark

    class StopAfterSecondRequest(RuntimeError):
        pass

    class DummyOutcomeGraph:
        def __init__(self, *_args, **_kwargs):
            pass

        @classmethod
        def load(cls, *_args, **_kwargs):
            return cls()

        def __getattr__(self, name):
            if name == "latest_portfolio_directive":
                return lambda *_args, **_kwargs: {}
            if "feedback" in name:
                return lambda *_args, **_kwargs: []
            return lambda *_args, **_kwargs: None

    site = box(0.0, 0.0, 20.0, 20.0)
    candidate = SimpleNamespace(
        principle_id="test-principle",
        principle_kind="subtractive",
        operation="test-book-op",
        score=1.0,
        source=SimpleNamespace(metadata={}),
    )
    selection_number = {"value": 0}
    request_states = []
    cycle_requests = []

    def select(pool, _target, **_kwargs):
        selection_number["value"] += 1
        assert pool == [candidate]
        return [candidate]

    def selection_diagnostics(*_args, **_kwargs):
        return {
            "target_count": 5,
            "selected_count": 1,
            "selection_universe_count": 1,
            "remaining_candidate_count": 0,
            "reason_counts": {},
            "exclusive_reason_counts": {},
        }

    def family_deficits(candidates, **_kwargs):
        assert candidates == [candidate]
        return {"selector_state_marker": f"state-{selection_number['value']}"}

    def request_builder(*_args, **kwargs):
        family = kwargs["family_supply_deficits"]
        feedback = kwargs[
            "authored_visual_authority_replenishment_feedback"
        ]
        request_states.append({
            "marker": family["selector_state_marker"],
            "candidate_supply_shortfall": next(
                item["evidence"]["candidate_supply_shortfall"]
                for item in feedback
                if item["reason"] == "candidate_supply_exhausted"
            ),
        })
        serialized = json.dumps(feedback, sort_keys=True).lower()
        for forbidden in (
            '"coordinates"',
            '"vertices"',
            '"surfaces"',
            '"mesh_payload"',
            '"image_url"',
        ):
            assert forbidden not in serialized
        return {
            "synthesis_requests": [{"marker": family["selector_state_marker"]}],
            "exact_compile_limit": 1,
        }

    def replenishment_cycle(**kwargs):
        cycle_requests.append(kwargs["synthesis_requests"])
        if len(cycle_requests) == 2:
            raise StopAfterSecondRequest
        return SimpleNamespace(
            selection_pool=[candidate],
            generated_pool=[candidate],
            downstream_evaluation_pool=[candidate],
            downstream_report={"rows": [{"combined_hard_pass": True}]},
            reviewed_parent_keys=set(),
            reviewed_parent_fingerprints=set(),
            live_qd_reserve=[],
            reviewed_final_vlm_fingerprints=set(),
            evidence={
                "legal_fit_deficits": [],
                "capacity_authoring_deficits": [],
                "exact_post_book_typed_repair": {},
                "stage_outcomes": [],
                "final_book_vlm_gate": {},
                "exact_compile_invocation_count": 0,
            },
        )

    generation_context = SimpleNamespace(
        generation_site=site,
        envelope=SimpleNamespace(bcr_limit=60.0, far_limit=200.0),
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "GeometryOutcomeGraph",
        DummyOutcomeGraph,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "build_legal_generation_context",
        lambda *_args, **_kwargs: generation_context,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_program_dimensional_context",
        lambda *_args, **_kwargs: {
            "status": "feasible",
            "effective_height_m": 14.0,
            "effective_floors": 4,
        },
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_resolve_authoritative_floor_context",
        lambda *_args, **_kwargs: (
            14.0,
            4,
            {"status": "test_stub", "floor_capacity_plan_hash": "floor"},
        ),
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "build_feasible_capacity_contract",
        lambda *_args, **_kwargs: {"status": "materialized"},
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_load_visual_directive",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "diagnostic_generation_budget",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_program_pool",
        lambda *_args, **_kwargs: ([candidate], {}),
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_shared_floor_hard_pass_candidates",
        lambda pool: list(pool),
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_program_selection_candidates",
        lambda pool: list(pool),
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "evaluate_accepted_sources_downstream",
        lambda candidates, **_kwargs: {
            "rows": [{"combined_hard_pass": True} for _ in candidates],
            "final_vlm_routing": {},
        },
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_final_vlm_input_from_downstream",
        lambda candidates, _report: list(candidates),
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_hard_gate_count_summary",
        lambda _report, candidates: {"candidate_count": len(candidates)},
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "build_gestalt_compatibility_analysis",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_bounded_visual_selection_pool",
        lambda pool: list(pool),
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "qd_archive_evidence",
        lambda _pool: {},
    )
    monkeypatch.setattr(portfolio_benchmark, "_select", select)
    monkeypatch.setattr(
        portfolio_benchmark,
        "_selection_capacity_diagnostics",
        selection_diagnostics,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "family_supply_deficits_for_candidates",
        family_deficits,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_deficit_directed_replenishment_inputs",
        request_builder,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "run_replenishment_cycle",
        replenishment_cycle,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "replenishment_cycle_budget_for_run",
        lambda **_kwargs: 2,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_replenishment_cycle_preflight_stop_reason",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_scope_key",
        lambda _candidate: "scope-a",
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_fingerprint",
        lambda _candidate: ("candidate",),
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_solid_morphology_metrics",
        lambda _candidate: {
            "degenerate_sheet_like": False,
            "phenotype": "compact",
            "wedge_like": False,
            "pyramidal_like": False,
        },
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "_design_concept_descriptor",
        lambda _candidate: {"ground_strategy": "direct"},
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "update_run_progress",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        portfolio_benchmark,
        "persist_diagnostic_generation_progress",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(StopAfterSecondRequest):
        portfolio_benchmark.run_book_program_portfolios(
            site,
            pnu="test-pnu",
            output_dir=tmp_path,
            constraints=[],
            program_slugs=("gymnasium",),
            progressive_target=5,
        )

    assert request_states == [
        {"marker": "state-1", "candidate_supply_shortfall": 4},
        {"marker": "state-2", "candidate_supply_shortfall": 4},
    ]
    assert cycle_requests == [
        [{"marker": "state-1"}],
        [{"marker": "state-2"}],
    ]
