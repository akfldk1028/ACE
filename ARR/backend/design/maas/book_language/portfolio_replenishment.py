"""Bounded causal replenishment for a BOOK portfolio.

Each call owns one parent-variant generation cycle.  The benchmark decides
whether another cycle is needed from the accumulated exact hard-pass pool;
this module guarantees every new candidate follows the same base VLM,
program, legal/parking, final VLM and typed-repair path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from .candidate_analysis import (
    _Candidate,
    _capacity_alternative_key,
    _chassis_family,
    _geometry_program_family,
    _plan_family,
    _roof_archetype,
    _scope_key,
    _solid_morphology_metrics,
    _vlm_reviewed_program_candidate,
)
from .candidate_generation import _program_pool
from .competition_breadth_scheduler import (
    BreadthScheduleResult,
    CompetitionBreadthScheduler,
    STAGE_FAILURE_NAMES,
)
from .competition_portfolio_contract import competition_family_supply_deficits
from .downstream_hard_gate import evaluate_accepted_sources_downstream
from .final_vlm_cycle import run_final_vlm_cycle
from .portfolio_selection import _bounded_visual_selection_pool
from .vlm_review import audit_book_base_stage_with_vlm


@dataclass(frozen=True)
class ReplenishmentCycleResult:
    selection_pool: list[_Candidate]
    generated_pool: list[_Candidate]
    downstream_evaluation_pool: list[_Candidate]
    downstream_report: dict[str, Any] | None
    evidence: dict[str, Any]
    reviewed_parent_keys: set[str]
    reviewed_parent_fingerprints: set[str]


def _candidate_program_hashes(candidate: _Candidate) -> set[str]:
    metadata = getattr(getattr(candidate, "source", None), "metadata", {}) or {}
    bridge = metadata.get("geometry_program_bridge_evidence") or {}
    semantic = metadata.get("final_semantic_projection_context") or {}
    snapshot = metadata.get("geometry_graph_snapshot") or {}
    program = metadata.get("geometry_program") or {}
    return {
        str(value)
        for value in (
            bridge.get("program_hash"),
            semantic.get("program_hash"),
            snapshot.get("program_hash"),
            program.get("program_hash"),
        )
        if str(value or "")
    }


def _exclude_duplicate_program_hashes(
    candidates: list[_Candidate],
    excluded_program_hashes: set[str],
) -> tuple[list[_Candidate], int]:
    excluded = {str(value) for value in excluded_program_hashes if str(value)}
    retained = [
        candidate for candidate in candidates
        if not (_candidate_program_hashes(candidate) & excluded)
    ]
    return retained, len(candidates) - len(retained)


def family_supply_deficits_for_candidates(
    candidates: list[_Candidate],
    *,
    target_count: int,
    compatibility_analysis: Any | None = None,
) -> dict[str, Any]:
    facts = []
    for candidate in candidates:
        morphology = _solid_morphology_metrics(candidate)
        body = str(
            morphology.get("body_phenotype")
            or morphology.get("phenotype")
            or "unclassified"
        )
        roof = _roof_archetype(candidate)
        facts.append({
            "body_phenotype": body,
            "roof_archetype": roof,
            "body_roof_signature": f"{body}|{roof}",
            "geometry_family": _geometry_program_family(candidate),
            "visible_stepped": bool(morphology.get("visible_stepped")),
        })
    pair_distances = []
    if compatibility_analysis is not None:
        for left_index, left in enumerate(candidates):
            for right in candidates[left_index + 1:]:
                pair_distances.append(
                    compatibility_analysis.distance(left, right)
                )
    return competition_family_supply_deficits(
        facts,
        target_count=target_count,
        pair_distances=pair_distances,
    )


def book_graph_supply_for_candidates(
    candidates: list[_Candidate],
) -> dict[str, Any]:
    """Describe retained BOOK principle supply without creating a hard gate."""

    principle_id_counts: dict[str, int] = {}
    principle_kind_counts: dict[str, int] = {}
    for candidate in candidates:
        principle_id = str(
            getattr(candidate, "principle_id", "") or ""
        )
        principle_kind = str(
            getattr(candidate, "principle_kind", "") or ""
        )
        if principle_id:
            principle_id_counts[principle_id] = (
                principle_id_counts.get(principle_id, 0) + 1
            )
        if principle_kind:
            principle_kind_counts[principle_kind] = (
                principle_kind_counts.get(principle_kind, 0) + 1
            )
    return {
        "schema_version": "arr.maas.book_graph_supply.v1",
        "hard_gate_effect": "none_diagnostic_only",
        "principle_id_counts": dict(sorted(principle_id_counts.items())),
        "principle_kind_counts": dict(
            sorted(principle_kind_counts.items())
        ),
    }


def competition_breadth_replenishment_state(
    schedule: BreadthScheduleResult,
    *,
    exact_hard_pass_count: int,
    feasible_portfolio: bool | None,
    downstream_stage_failure_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Persist the typed reason to stop or advance exactly one form-bank page."""

    state = competition_exact_reserve_transition(
        page_index=int(schedule.page_index),
        exact_hard_pass_count=exact_hard_pass_count,
        feasible_portfolio=feasible_portfolio,
    )
    stage_failure_counts = dict(schedule.stage_failure_counts)
    for stage, count in (downstream_stage_failure_counts or {}).items():
        if stage not in STAGE_FAILURE_NAMES:
            raise ValueError(f"unknown breadth failure stage: {stage}")
        stage_failure_counts[stage] = (
            int(stage_failure_counts.get(stage, 0))
            + max(0, int(count))
        )
    return {
        **state,
        "exact_shortlist_count": len(schedule.exact_shortlist),
        "breadth_deficits": [
            deficit.to_dict() for deficit in schedule.deficits
            if not (
                deficit.axis == "exact_shortlist"
                and deficit.cell == "total"
            )
        ],
        "stage_failure_counts": stage_failure_counts,
    }


def competition_exact_reserve_transition(
    *,
    page_index: int,
    exact_hard_pass_count: int,
    feasible_portfolio: bool | None,
) -> dict[str, Any]:
    """Return the operational stop/advance state consumed by the page loop."""

    stop = CompetitionBreadthScheduler.exact_pool_ready(
        exact_hard_pass_count=exact_hard_pass_count,
        feasible_portfolio=feasible_portfolio is True,
    )
    return {
        "schema_version": "arr.maas.competition_breadth_replenishment.v1",
        "stop": stop,
        "page_index": int(page_index),
        "next_page_index": (
            None if stop else int(page_index) + 1
        ),
        "exact_hard_pass_count": max(0, int(exact_hard_pass_count)),
        "feasible_portfolio": feasible_portfolio,
    }


def _downstream_breadth_failure_counts(
    report: dict[str, Any] | None,
) -> dict[str, int]:
    counts = {stage: 0 for stage in STAGE_FAILURE_NAMES}
    for row in (report or {}).get("rows") or ():
        legal = row.get("legal_projection") or {}
        parking = row.get("parking_hard_gate") or {}
        semantic = row.get("semantic_projection_hard_gate") or {}
        capacity = (
            row.get("capacity_hard_gate")
            or row.get("source_capacity_measurement")
            or {}
        )
        if legal.get("evaluated") is True and legal.get("hard_pass") is not True:
            counts["exact_csg"] += 1
        if (
            parking.get("evaluated") is True
            and parking.get("hard_pass") is not True
        ):
            counts["parking"] += 1
        if (
            semantic.get("evaluated") is True
            and semantic.get("hard_pass") is not True
        ):
            counts["hash_bridge"] += 1
        if (
            capacity.get("evaluated") is True
            and capacity.get("hard_pass") is not True
        ):
            counts["capacity"] += 1
    return counts


def competition_breadth_shortlist_candidates(
    candidates: list[_Candidate],
    *,
    page_index: int,
    target_count: int,
) -> tuple[list[_Candidate], BreadthScheduleResult]:
    """Adapt compiled candidates into the shared quota-aware exact shortlist."""

    wrapped = []
    for index, candidate in enumerate(candidates):
        morphology = _solid_morphology_metrics(candidate)
        wrapped.append(SimpleNamespace(
            key=f"breadth-{int(page_index):02d}-{index:04d}",
            original_candidate=candidate,
            page_index=int(page_index),
            base_scope=_scope_key(candidate),
            genotype_family=_geometry_program_family(candidate),
            book_principle_kind=str(candidate.principle_kind),
            book_principle_id=str(
                getattr(candidate, "principle_id", "unclassified")
            ),
            body_family=str(
                morphology.get("body_phenotype")
                or morphology.get("phenotype")
                or "unclassified"
            ),
            roof_family=_roof_archetype(candidate),
            chassis_family=_chassis_family(candidate),
            plan_family=_plan_family(candidate),
            capacity_band=_capacity_alternative_key(candidate),
            score=float(candidate.score),
            book_bind_pass=True,
            authored_compile_pass=True,
            legal_section_screen_pass=True,
            affine_screen_pass=True,
            approximate_capacity_pass=True,
        ))
    schedule = CompetitionBreadthScheduler(
        target_count=int(target_count),
    ).schedule_page(
        wrapped,
        page_index=int(page_index),
    )
    return [
        item.original_candidate for item in schedule.exact_shortlist
    ], schedule


def competition_exact_hard_pass_deficits(
    candidates: list[_Candidate],
    *,
    page_index: int,
    target_count: int,
) -> list[dict[str, Any]]:
    """Recompute typed quota deficits over the actual exact hard-pass pool."""

    _retained, schedule = competition_breadth_shortlist_candidates(
        candidates,
        page_index=page_index,
        target_count=target_count,
    )
    deficits = [
        deficit.to_dict() for deficit in schedule.deficits
        if not (
            deficit.axis == "exact_shortlist"
            and deficit.cell == "total"
        )
    ]
    if int(target_count) == 20 and len(candidates) < 24:
        deficits.append({
            "axis": "exact_hard_pass_reserve",
            "cell": "total",
            "required_count": 24,
            "available_count": len(candidates),
            "shortfall": 24 - len(candidates),
            "stage": "exact_hard_pass",
            "page_index": int(page_index),
        })
    return deficits


def replenishment_cycle_budget() -> int:
    """Return the bounded number of fresh parent variants to explore.

    Parent indices are an actual deterministic variation-lattice axis.  The
    One cycle is the safe default because every fresh parent can trigger both
    base and final image review. Larger experiments must opt in explicitly and
    remain protected by the process-wide live-request budget.
    """
    try:
        return max(1, min(8, int(os.getenv("MAAS_BOOK_REPLENISHMENT_CYCLES", "1"))))
    except (TypeError, ValueError):
        return 1


def replenishment_cycle_budget_for_run(
    *,
    live_vlm: bool,
    smoke_mode: bool = False,
) -> int:
    """Keep paid review bounded while letting local geometry pages close."""

    configured = replenishment_cycle_budget()
    if smoke_mode:
        smoke_diagnostic = os.getenv(
            "MAAS_BOOK_SMOKE_REPLENISHMENT_CYCLES"
        )
        if smoke_diagnostic is not None:
            try:
                # Zero is an explicit diagnostic-only request. It never makes
                # an undersized portfolio pass; it only persists the initial
                # selection diagnostics without compiling another page.
                return max(0, min(8, int(smoke_diagnostic)))
            except (TypeError, ValueError):
                pass
    if live_vlm or smoke_mode:
        return configured
    # Production/local closure still defaults to seven geometry pages. A
    # deliberately named diagnostic override can stop after an early page so
    # solver supply is inspected before another hour-long run. It never changes
    # any geometry, legal, parking, capacity or silhouette threshold.
    diagnostic = os.getenv("MAAS_BOOK_NONLIVE_REPLENISHMENT_CYCLES")
    if diagnostic is not None:
        try:
            return max(1, min(8, int(diagnostic)))
        except (TypeError, ValueError):
            pass
    return max(7, configured)


def replenishment_stop_reason(
    *,
    selected_count: int,
    selected_scope_count: int,
    target_count: int,
    required_scope_count: int,
    cycles_run: int,
    cycle_budget: int,
    exact_hard_pass_count: int | None = None,
    feasible_portfolio: bool | None = None,
    author_budget_failure: dict[str, Any] | None = None,
) -> str:
    """Return a terminal reason only for success or an exhausted budget.

    A cycle can approve new base parents without immediately increasing the
    final hard-pass pool: their descendants may fail the current BOOK or
    program projection while the next parent variant succeeds.  Treating two
    zero-growth final pools as stagnation skipped that next bounded variant
    and contradicted the three-cycle exploration contract.
    """
    failure = author_budget_failure or {}
    if (
        failure.get("code") == "request_quota_exhausted"
        and failure.get("quota") == "author_replenishment"
        and failure.get("author_stage") == "replenishment"
    ):
        return "replenishment_author_quota_exhausted"
    if int(target_count) == 20:
        if CompetitionBreadthScheduler.exact_pool_ready(
            exact_hard_pass_count=int(exact_hard_pass_count or 0),
            feasible_portfolio=feasible_portfolio is True,
        ):
            return "competition_exact_reserve_feasible"
    elif selected_count >= target_count and selected_scope_count >= required_scope_count:
        return "target_and_scope_coverage_reached"
    if cycles_run >= cycle_budget:
        return "cycle_budget_exhausted"
    return ""


def critic_feedback_consumption_evidence(
    *,
    feedback_count: int,
    included_in_author_context: bool,
    author_request_executed: bool,
) -> dict[str, Any]:
    count = max(0, int(feedback_count))
    consumed = bool(
        count > 0
        and included_in_author_context
        and author_request_executed
    )
    if consumed:
        reason = "consumed"
    elif count == 0:
        reason = "no_feedback"
    elif not included_in_author_context:
        reason = "not_included_in_author_context"
    else:
        reason = "author_request_not_executed"
    return {
        "critic_feedback_consumed_same_run": consumed,
        "feedback_count": count,
        "included_in_author_context": bool(included_in_author_context),
        "author_request_executed": bool(author_request_executed),
        "reason": reason,
    }


def competition_exact_hard_pass_reserve(
    pool: list[_Candidate],
    *,
    selected: list[_Candidate],
) -> list[_Candidate]:
    """Keep a feasible 20-set plus at most eight deterministic reserve cards."""

    if len(selected) != 20:
        return list(pool)
    retained: list[_Candidate] = []
    seen: set[int] = set()
    for candidate in (*selected, *pool):
        identity = id(candidate)
        if identity in seen:
            continue
        seen.add(identity)
        retained.append(candidate)
        if len(retained) >= 28:
            break
    return retained


def run_replenishment_cycle(
    *,
    cycle_index: int,
    parent_variant_index: int,
    retained_selection_pool: list[_Candidate],
    excluded_parent_keys: set[str],
    excluded_parent_fingerprints: set[str],
    excluded_program_hashes: set[str],
    generation_site: Any,
    building_type: str,
    height: float,
    floors: int,
    generation_context: Any,
    typed_graph_mutations: list[Any],
    geometry_program_mutations: list[Any],
    synthesis_requests: list[Any],
    outcome_graph: Any,
    recursive_only: bool,
    target_count: int = 0,
    exact_compile_limit: int | None = None,
    program_dimensional_context: dict[str, Any] | None,
    site_boundary_source: str,
    site_access_context: dict[str, Any] | None,
    site_access_geometry: dict[str, Any] | None,
    runtime_live_vlm: bool,
    live_vlm_selection_required: bool,
    base_capacity_contract: dict[str, Any] | None,
    trusted_legal_floor_field: dict[str, Any] | None,
    trusted_legal_floor_field_hash: str,
    trusted_clear_span_floor_plan: dict[str, Any] | None,
    capacity_site: Any,
    output_dir: Path,
    program_slug: str,
    visual_directive: dict[str, Any],
    downstream_context: dict[str, Any],
    hard_gate_summary: Callable[[dict[str, Any] | None, list[_Candidate]], dict[str, Any]],
    stop_after_shared_floor_hard_passes: int | None = None,
    diagnostic_generation_budget: dict[str, Any] | None = None,
    progress_callback: Callable[[dict[str, int]], None] | None = None,
) -> ReplenishmentCycleResult:
    diagnostic_budget = dict(diagnostic_generation_budget or {})
    book_graph_supply = book_graph_supply_for_candidates(
        retained_selection_pool
    )
    effective_synthesis_requests = [
        {
            **dict(request),
            "book_graph_supply": {
                **book_graph_supply,
                "principle_id_counts": dict(
                    book_graph_supply["principle_id_counts"]
                ),
                "principle_kind_counts": dict(
                    book_graph_supply["principle_kind_counts"]
                ),
            },
        }
        for request in synthesis_requests
        if isinstance(request, dict)
    ]
    generated_pool, generation_counts = _program_pool(
        generation_site,
        building_type,
        height,
        floors,
        generation_context=generation_context,
        parent_variant_indices=(parent_variant_index,),
        typed_graph_mutations=typed_graph_mutations,
        geometry_program_mutations=geometry_program_mutations,
        synthesis_requests=effective_synthesis_requests,
        outcome_graph=outcome_graph,
        recursive_only=recursive_only,
        target_count=int(target_count),
        exact_compile_limit=exact_compile_limit,
        program_dimensional_context=program_dimensional_context,
        site_boundary_source=site_boundary_source,
        site_access_context=site_access_context,
        site_access_geometry=site_access_geometry,
        live_geometry_vlm_revision=runtime_live_vlm,
        base_capacity_contract=base_capacity_contract,
        trusted_legal_floor_field=trusted_legal_floor_field,
        trusted_legal_floor_field_hash=(
            trusted_legal_floor_field_hash
        ),
        trusted_clear_span_floor_plan=(
            trusted_clear_span_floor_plan
        ),
        capacity_site=capacity_site,
        pnu=str(downstream_context.get("pnu") or ""),
        stop_after_shared_floor_hard_passes=stop_after_shared_floor_hard_passes,
        diagnostic_scope_labels=tuple(
            diagnostic_budget.get("scope_labels") or ()
        ),
        diagnostic_book_probe_count=diagnostic_budget.get(
            "book_probe_count"
        ),
        diagnostic_evaluation_cap=diagnostic_budget.get("evaluation_cap"),
        diagnostic_candidate_cap=diagnostic_budget.get("candidate_cap"),
        progress_callback=progress_callback,
    )
    generated_pool, duplicate_program_hash_count = (
        _exclude_duplicate_program_hashes(
            generated_pool,
            set(excluded_program_hashes or ()),
        )
    )
    generated_pool = [
        candidate
        for candidate in generated_pool
        if (
            isinstance(
                candidate.source.metadata.get("shared_floor_contract"),
                dict,
            )
            and candidate.source.metadata["shared_floor_contract"].get("hard_pass")
            is True
        )
    ]
    breadth_schedule = None
    if (
        int(target_count) == 20
        and not diagnostic_budget
        and stop_after_shared_floor_hard_passes is None
    ):
        generated_pool, breadth_schedule = (
            competition_breadth_shortlist_candidates(
                generated_pool,
                page_index=parent_variant_index,
                target_count=int(target_count),
            )
        )
    if runtime_live_vlm:
        downstream_evaluation_pool, base_gate = audit_book_base_stage_with_vlm(
            generated_pool,
            building_type=building_type,
            output_dir=output_dir / f"replenishment-cycle-{cycle_index}" / "book-base-stage",
            visual_directive=visual_directive,
            outcome_graph=outcome_graph,
            program_slug=program_slug,
            excluded_parent_keys=excluded_parent_keys,
            excluded_parent_fingerprints=excluded_parent_fingerprints,
        )
    else:
        downstream_evaluation_pool = generated_pool
        base_gate = {
            "required": False,
            "status": "not_requested",
            "input_count": len(generated_pool),
            "reviewed_parent_keys": [],
            "reviewed_parent_fingerprints": [],
        }
    downstream_report = None
    downstream_passes = list(downstream_evaluation_pool)
    if generation_context is not None:
        downstream_report = evaluate_accepted_sources_downstream(
            downstream_evaluation_pool,
            **downstream_context,
        )
        downstream_passes = [
            candidate
            for candidate, row in zip(downstream_evaluation_pool, downstream_report["rows"])
            if row["combined_hard_pass"]
        ]
    if live_vlm_selection_required:
        downstream_passes = [
            candidate for candidate in downstream_passes
            if _vlm_reviewed_program_candidate(candidate)
        ]
    degenerate_count = sum(
        bool(_solid_morphology_metrics(candidate)["degenerate_sheet_like"])
        for candidate in downstream_passes
    )
    downstream_passes = [
        candidate for candidate in downstream_passes
        if not _solid_morphology_metrics(candidate)["degenerate_sheet_like"]
    ]
    evidence = {
        **generation_counts,
        "schema_version": "arr.maas.bounded_parent_replenishment_cycle.v2",
        "cycle_index": cycle_index,
        "parent_variant_index": parent_variant_index,
        "causal_trigger": "exact_post_book_vlm_and_portfolio_capacity",
        **critic_feedback_consumption_evidence(
            feedback_count=int(
                generation_counts.get("base_book_vlm_feedback_count") or 0
            ),
            included_in_author_context=bool(
                generation_counts.get(
                    "base_book_vlm_feedback_in_author_context"
                )
            ),
            author_request_executed=bool(
                generation_counts.get("llm_author_request_executed")
            ),
        ),
        "authored_visual_authority_feedback_consumption": {
            "feedback_count": int(
                generation_counts.get(
                    "authored_visual_authority_feedback_count"
                ) or 0
            ),
            "included_in_author_context": bool(
                generation_counts.get(
                    "authored_visual_authority_feedback_in_author_context"
                )
            ),
            "author_request_executed": bool(
                generation_counts.get("llm_author_request_executed")
            ),
            "revision_target": "typed_geometry_program_ast_mechanism",
            "legal_floor_loft_or_prism_replay_allowed": False,
        },
        "recursive_geometry_lane_enabled": bool(recursive_only),
        "preselection_hard_gate": hard_gate_summary(
            downstream_report,
            downstream_evaluation_pool,
        ),
        "degenerate_sheet_like_rejected_count": degenerate_count,
        "book_base_stage_vlm_gate": base_gate,
        "duplicate_parent_program_hash_excluded_count": (
            duplicate_program_hash_count
        ),
    }
    if breadth_schedule is not None:
        exact_hard_pass_deficits = competition_exact_hard_pass_deficits(
            downstream_passes,
            page_index=parent_variant_index,
            target_count=int(target_count),
        )
        evidence["competition_breadth_schedule"] = (
            breadth_schedule.evidence()
        )
        evidence["competition_breadth_replenishment"] = (
            competition_breadth_replenishment_state(
                breadth_schedule,
                exact_hard_pass_count=len(downstream_passes),
                # Solver feasibility remains authoritative downstream.  This
                # cycle records supply and requests the next page until that
                # exact solver result is available.
                feasible_portfolio=None,
                downstream_stage_failure_counts=(
                    _downstream_breadth_failure_counts(
                        downstream_report
                    )
                ),
            )
        )
        evidence["competition_breadth_replenishment"][
            "breadth_deficits"
        ] = exact_hard_pass_deficits
    if runtime_live_vlm:
        cycle = run_final_vlm_cycle(
            downstream_passes,
            retained_hard_passes=list(retained_selection_pool),
            building_type=building_type,
            output_dir=output_dir / f"replenishment-cycle-{cycle_index}" / "final",
            visual_directive=visual_directive,
            outcome_graph=outcome_graph,
            program_slug=program_slug,
            generation_site=generation_site,
            height=height,
            floors=floors,
            generation_context=generation_context,
            program_dimensional_context=program_dimensional_context,
            site_boundary_source=site_boundary_source,
            site_access_context=site_access_context,
            site_access_geometry=site_access_geometry,
            base_capacity_contract=base_capacity_contract,
            downstream_context=downstream_context,
            hard_gate_summary=hard_gate_summary,
            completion_status="replenishment_exact_typed_repair_cycle_complete",
            no_repair_status="no_downstream_hard_pass_replenishment_repair_candidates",
        )
        selection_pool = cycle.selection_pool
        evidence["exact_post_book_typed_repair"] = cycle.repair_evidence
        evidence["final_book_vlm_gate"] = cycle.final_vlm_gate
    else:
        selection_pool = _bounded_visual_selection_pool([
            *retained_selection_pool,
            *downstream_passes,
        ])
    return ReplenishmentCycleResult(
        selection_pool=selection_pool,
        generated_pool=generated_pool,
        downstream_evaluation_pool=downstream_evaluation_pool,
        downstream_report=downstream_report,
        evidence=evidence,
        reviewed_parent_keys=set(str(value) for value in base_gate.get("reviewed_parent_keys") or ()),
        reviewed_parent_fingerprints=set(
            str(value) for value in base_gate.get("reviewed_parent_fingerprints") or ()
        ),
    )


__all__ = [
    "ReplenishmentCycleResult",
    "competition_breadth_replenishment_state",
    "competition_breadth_shortlist_candidates",
    "competition_exact_hard_pass_reserve",
    "competition_exact_hard_pass_deficits",
    "competition_exact_reserve_transition",
    "family_supply_deficits_for_candidates",
    "replenishment_cycle_budget",
    "replenishment_cycle_budget_for_run",
    "replenishment_stop_reason",
    "run_replenishment_cycle",
]
