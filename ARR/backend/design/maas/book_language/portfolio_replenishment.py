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
from typing import Any, Callable

from .candidate_analysis import (
    _Candidate,
    _solid_morphology_metrics,
    _vlm_reviewed_program_candidate,
)
from .candidate_generation import _program_pool
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
) -> str:
    """Return a terminal reason only for success or an exhausted budget.

    A cycle can approve new base parents without immediately increasing the
    final hard-pass pool: their descendants may fail the current BOOK or
    program projection while the next parent variant succeeds.  Treating two
    zero-growth final pools as stagnation skipped that next bounded variant
    and contradicted the three-cycle exploration contract.
    """
    if selected_count >= target_count and selected_scope_count >= required_scope_count:
        return "target_and_scope_coverage_reached"
    if cycles_run >= cycle_budget:
        return "cycle_budget_exhausted"
    return ""


def run_replenishment_cycle(
    *,
    cycle_index: int,
    parent_variant_index: int,
    retained_selection_pool: list[_Candidate],
    excluded_parent_keys: set[str],
    excluded_parent_fingerprints: set[str],
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
    program_dimensional_context: dict[str, Any] | None,
    site_boundary_source: str,
    site_access_context: dict[str, Any] | None,
    site_access_geometry: dict[str, Any] | None,
    runtime_live_vlm: bool,
    live_vlm_selection_required: bool,
    base_capacity_contract: dict[str, Any] | None,
    capacity_site: Any,
    output_dir: Path,
    program_slug: str,
    visual_directive: dict[str, Any],
    downstream_context: dict[str, Any],
    hard_gate_summary: Callable[[dict[str, Any] | None, list[_Candidate]], dict[str, Any]],
    stop_after_shared_floor_hard_passes: int | None = None,
) -> ReplenishmentCycleResult:
    generated_pool, generation_counts = _program_pool(
        generation_site,
        building_type,
        height,
        floors,
        generation_context=generation_context,
        parent_variant_indices=(parent_variant_index,),
        typed_graph_mutations=typed_graph_mutations,
        geometry_program_mutations=geometry_program_mutations,
        synthesis_requests=synthesis_requests,
        outcome_graph=outcome_graph,
        recursive_only=recursive_only,
        program_dimensional_context=program_dimensional_context,
        site_boundary_source=site_boundary_source,
        site_access_context=site_access_context,
        site_access_geometry=site_access_geometry,
        live_geometry_vlm_revision=runtime_live_vlm,
        base_capacity_contract=base_capacity_contract,
        capacity_site=capacity_site,
        pnu=str(downstream_context.get("pnu") or ""),
        stop_after_shared_floor_hard_passes=stop_after_shared_floor_hard_passes,
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
        "critic_feedback_consumed_same_run": bool(runtime_live_vlm),
        "recursive_geometry_lane_enabled": bool(recursive_only),
        "preselection_hard_gate": hard_gate_summary(
            downstream_report,
            downstream_evaluation_pool,
        ),
        "degenerate_sheet_like_rejected_count": degenerate_count,
        "book_base_stage_vlm_gate": base_gate,
    }
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
    "replenishment_cycle_budget",
    "replenishment_cycle_budget_for_run",
    "replenishment_stop_reason",
    "run_replenishment_cycle",
]
