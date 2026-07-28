"""Image-grounded review and typed repair of staged BOOK candidates."""

from __future__ import annotations

import os
import hashlib
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

from shapely.geometry import Polygon, mapping

from design.maas.geometry_language import (
    GeometryOutcomeGraph,
    GeometryProgram,
    apply_geometry_edits_compiler_safe,
    build_geometry_graph_notes,
    build_geometry_graph_snapshot,
    compile_geometry_program,
    materialize_floorwise_legal_source,
    replace_source_dominant_with_geometry_program,
)
from design.maas.program_massing import program_reference_contract
from design.maas.program_massing.scoring import attach_program_massing_evidence
from design.maas.program_massing.search import (
    materialize_source_feature_surfaces,
    source_feature,
)
from design.maas.preference.loop import openai_preview_preference_scorer
from design.maas.preference.vlm_scorer import (
    DEFAULT_VLM_MODEL,
    VLM_PROMPT_CONTRACT_VERSION,
)
from design.maas.shared_floor_contract import (
    bind_shared_floor_contract_capacity,
    materialize_shared_floor_contract,
)
from design.maas.source_geometry import compile_sequence_to_source_mass

from .candidate_analysis import (
    _Candidate,
    _chassis_family,
    _clean_mass_gate,
    _design_concept_descriptor,
    _form_bank_lane,
    _geometry_program_family,
    _inside_site,
    _llm_authored_candidate,
    _program_form_gate,
    _scope_key,
    _site_access_side_in_principal_frame,
    _solid_morphology_metrics,
)
from .base_volume_contract import book_base_volume_spec
from .capacity_alternatives import (
    capacity_fit_score,
    capacity_contract_for_alternative,
    evaluate_capacity_alternative,
)
from .capacity_contract import measure_source_capacity, recursive_plan_coverage_floor
from .capacity_routing import build_capacity_review_context
from .downstream_hard_gate import LegalGenerationContext, generation_site_at_height
from .portfolio_selection import _select
from .reference_context import _audited_final_book_references
from .vlm_stage_policy import book_vlm_stage_policy


def _materialize_repaired_floor_contract(
    source: Any,
    *,
    generation_context: LegalGenerationContext | None,
    capacity_site: Polygon | None,
    height: float,
    floors: int,
    base_capacity_contract: dict[str, Any] | None,
    repaired_program: GeometryProgram,
    repaired_compilation: Any,
) -> dict[str, Any] | None:
    """Recompute floor plates from the exact post-VLM geometry identity."""

    if generation_context is None or capacity_site is None:
        return None
    return materialize_shared_floor_contract(
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
        program_hash=repaired_program.program_hash(),
        geometry_hash=str(repaired_compilation.geometry_hash or ""),
        floor_capacity_plan_hash=str(
            (base_capacity_contract or {}).get("floor_capacity_plan_hash")
            or ""
        ),
        feasible_capacity_m2=float(
            (base_capacity_contract or {}).get("feasible_maximum_floor_area_m2")
            or 0.0
        ),
    )


def _book_stage_capacity_floor(candidate: _Candidate, review_stage: str) -> float:
    """Normalize a developmental base floor by the exact p.3 scope.

    A 1/16 base is intentionally one sixteenth of its host; judging it against
    40% of the completed program before combination/aggregation erases the
    source grammar. Final solids retain the unscaled competition floor.
    """
    policy = book_vlm_stage_policy(review_stage)
    floor = max(0.0, float(policy.minimum_feasible_capacity_utilization))
    if policy.capacity_normalization != "book_scope_fraction":
        return floor
    try:
        fraction = float(book_base_volume_spec(_scope_key(candidate)).fraction)
    except (KeyError, TypeError, ValueError):
        fraction = 1.0
    return floor * max(0.0, min(1.0, fraction))


def _has_exact_geometry_program(candidate: _Candidate) -> bool:
    """Return whether the exact recursive AST required by this critic exists."""
    raw = candidate.source.metadata.get("geometry_program") or {}
    if not isinstance(raw, dict) or not isinstance(raw.get("nodes"), list):
        return False
    try:
        GeometryProgram.from_dict(raw)
    except (TypeError, ValueError):
        return False
    return True


def _final_book_vlm_hard_pass(
    result: dict[str, Any],
    *,
    candidate_morphology: dict[str, Any] | None = None,
    candidate_design_concept: dict[str, Any] | None = None,
    candidate_capacity: dict[str, Any] | None = None,
    minimum_capacity_utilization: float = 0.0,
    review_stage: str = "final_book",
) -> tuple[bool, list[str]]:
    """Gate an image review with an explicit BOOK-stage quality contract."""
    policy = book_vlm_stage_policy(review_stage)
    scores = result.get("concept_scores") if isinstance(result.get("concept_scores"), dict) else {}
    actions = {str(value) for value in result.get("critic_actions") or ()}
    failures: list[str] = []
    reference_gate = (
        result.get("reference_massing_gate")
        if isinstance(result.get("reference_massing_gate"), dict)
        else {}
    )
    if reference_gate and not bool(reference_gate.get("hard_pass")):
        failures.append(f"{policy.stage}_reference_massing_suitability_failed")
    if policy.require_program_fit and not bool(result.get("program_fit_hard_pass")):
        failures.append("final_book_program_fit_failed")
    for action in sorted(actions & policy.blocking_actions):
        failures.append(f"{policy.stage}_vlm_{action}")
    for concept, floor in policy.quality_floors.items():
        if float(scores.get(concept) or 0.0) + 1e-9 < floor:
            failures.append(
                f"{policy.stage}_{concept}_below_{policy.quality_floor_label}"
            )
    capacity = candidate_capacity or {}
    capacity_utilization = float(capacity.get("feasible_capacity_utilization") or 0.0)
    capacity_floor = max(0.0, float(minimum_capacity_utilization))
    if capacity and capacity_utilization + 1e-9 < capacity_floor:
        failures.append("book_stage_feasible_capacity_below_competition_floor")
    if not policy.require_finished_silhouette:
        return not failures, failures
    # The scorer already derives fragmentation actions from hierarchy and
    # repair integrity. This additional explicit field catches arbitrary cake
    # tiers that can retain both scores while repeating one silhouette.
    if (
        float(scores.get("non_stair_silhouette") or 0.0) < 0.55
        and "good_step_mass" not in actions
    ):
        failures.append("final_book_arbitrary_tier_silhouette")
    if bool((candidate_morphology or {}).get("pyramidal_like")):
        # The critic can call a cake-tier silhouette a "good step mass" even
        # when the compiled graph contains no public terrace/threshold or
        # program section relation.  Require the visual judgment and one
        # executable relation to agree. This preserves real stepped courts and
        # gym roof sections without accepting a token alone.
        public_relation = bool((candidate_design_concept or {}).get("frontage_aligned")) and (
            float(scores.get("void_publicness") or 0.0) >= 0.65
        )
        section_relation = (
            str((candidate_morphology or {}).get("section_phenotype") or "none") != "none"
            and float(scores.get("section_program_fit") or 0.0) >= 0.65
        )
        if "good_step_mass" not in actions or not (public_relation or section_relation):
            failures.append("final_book_unresolved_pyramidal_program_relation")
    # A critic request for a carved public void is advisory only when no
    # verified access relation exists.  Once the final AST declares an access
    # side, however, accepting the same sealed mass would contradict both the
    # visual diagnosis and the typed design-concept graph.  Require a revised
    # frontage-bound controller instead of letting a high average score hide
    # the unresolved public threshold.
    target_access_side = str(
        (candidate_design_concept or {}).get("target_access_side_in_program_frame")
        or "closed"
    )
    if (
        target_access_side != "closed"
        and not bool((candidate_design_concept or {}).get("frontage_aligned"))
        and "needs_carved_void" in actions
    ):
        failures.append("final_book_unresolved_public_threshold_relation")
    return not failures, failures


def _final_book_vlm_shortlist(
    pool: list[_Candidate],
    *,
    target: int,
    visual_directive: dict[str, Any],
) -> list[_Candidate]:
    """Stratify exact final solids before the expensive visual critic."""
    if not pool or target <= 0:
        return []
    if target == 1:
        # A one-shot smoke review has no diversity quota to allocate. The
        # former family-round-robin picked the alphabetically first core
        # family (attached_volume) even when the measured selector ranked a
        # cleaner, capacity-target five-floor MASS first. Review the exact
        # candidate that would otherwise be selected.
        selector = _select(
            pool,
            1,
            visual_directive=visual_directive,
        )[:1]
        selector_winner = (
            selector[0]
            if selector
            else max(
                pool,
                key=lambda candidate: float(
                    getattr(candidate, "score", 0.0) or 0.0
                ),
            )
        )
        return [
            _architectural_one_shot_candidate(
                pool,
                selector_winner=selector_winner,
            )
        ]
    # The procedural control archive is much larger than the live authored
    # lane. Without a review reservation, valid LLM ASTs can pass compiler,
    # clean and program gates yet receive only 2/64 final image reviews. This
    # quota grants review bandwidth, never selection or score preference.
    authored = [candidate for candidate in pool if _llm_authored_candidate(candidate)]
    authored_target = min(
        len(authored),
        target,
        max(1, target // 4),
    )
    authored_strata: dict[tuple[str, str, str], list[_Candidate]] = {}
    for candidate in sorted(authored, key=lambda item: item.score, reverse=True):
        key = (
            _geometry_program_family(candidate),
            _scope_key(candidate),
            str(_solid_morphology_metrics(candidate)["phenotype"]),
        )
        authored_strata.setdefault(key, []).append(candidate)
    chosen: list[_Candidate] = []
    authored_depth = 0
    while len(chosen) < authored_target:
        added = False
        for key in sorted(authored_strata):
            bucket = authored_strata[key]
            if authored_depth >= len(bucket):
                continue
            chosen.append(bucket[authored_depth])
            added = True
            if len(chosen) >= authored_target:
                break
        if not added:
            break
        authored_depth += 1
    # The executable core lane is the architectural alphabet (L/U/court,
    # cross, split bridge, sweep, overlap...), while bounded synthesis is the
    # larger combinatorial vocabulary.  A score-only shortlist let the 64
    # synthesis programs consume almost every review slot: in r144, seven
    # core families had 113 program-hard-pass descendants, yet only six exact
    # core candidates were ever shown to the VLM.  Reserve *review bandwidth*
    # across core family/scope strata.  This grants no hard-pass or selection
    # preference; every reserved candidate still faces the identical critic.
    core = [
        candidate for candidate in pool
        if _form_bank_lane(candidate) == "executable_core_language"
    ]
    core_family_count = len({
        _geometry_program_family(candidate) for candidate in core
        if _geometry_program_family(candidate)
    })
    core_target = min(
        len(core),
        # Review two BOOK projections per available core family when budget
        # permits. One projection can distort a good chassis (r145's only
        # split-bridge review used SHIFT and read as toy blocks); a second is
        # still a review quota, not a pass or selection preference.
        max(min(core_family_count * 2, target), target // 3),
    )
    core_strata: dict[str, list[_Candidate]] = {}
    for candidate in sorted(core, key=lambda item: item.score, reverse=True):
        # Family is the first axis on purpose: using family+scope as a key
        # allowed two high-score variants from the first nine alphabetic
        # families to consume all 18 reserved slots.
        key = _geometry_program_family(candidate)
        core_strata.setdefault(key, []).append(candidate)
    chosen_ids = {id(candidate) for candidate in chosen}
    core_depth = 0
    while sum(_form_bank_lane(candidate) == "executable_core_language" for candidate in chosen) < core_target:
        added = False
        for key in sorted(core_strata):
            bucket = core_strata[key]
            if core_depth >= len(bucket):
                continue
            candidate = bucket[core_depth]
            if id(candidate) not in chosen_ids:
                chosen.append(candidate)
                chosen_ids.add(id(candidate))
                added = True
            if sum(_form_bank_lane(item) == "executable_core_language" for item in chosen) >= core_target:
                break
        if not added:
            break
        core_depth += 1

    # Board-level family supply caps belong to final selection. Applying them
    # here prevented the individual critic from ever seeing alternate members
    # of an overrepresented family, even though one could be the single keeper.
    review_directive = dict(visual_directive)
    review_directive.pop("max_geometry_family_counts", None)
    provisional = _select(pool, min(20, target), visual_directive=review_directive)
    chosen.extend(candidate for candidate in provisional if id(candidate) not in chosen_ids)
    chosen_ids = {id(candidate) for candidate in chosen}
    strata: dict[tuple[str, str, str, str], list[_Candidate]] = {}
    for candidate in sorted(pool, key=lambda item: item.score, reverse=True):
        if id(candidate) in chosen_ids:
            continue
        key = (
            _geometry_program_family(candidate),
            str(_solid_morphology_metrics(candidate)["phenotype"]),
            _scope_key(candidate),
            candidate.principle_kind,
        )
        strata.setdefault(key, []).append(candidate)
    depth = 0
    while len(chosen) < target:
        added = False
        for key in sorted(strata):
            bucket = strata[key]
            if depth >= len(bucket):
                continue
            candidate = bucket[depth]
            if id(candidate) not in chosen_ids:
                chosen.append(candidate)
                chosen_ids.add(id(candidate))
                added = True
            if len(chosen) >= target:
                break
        if not added:
            break
        depth += 1
    return chosen[:target]


def _architectural_one_shot_candidate(
    pool: list[_Candidate],
    *,
    selector_winner: _Candidate,
) -> _Candidate:
    """Prefer typed public/program evidence before spending one paid review.

    Every input has already passed the same capacity, legal, parking and
    shared-floor gates.  This function only prevents a one-shot smoke budget
    from repeatedly choosing a generic capacity pack when another hard-pass
    candidate carries executable public-space and program/section relations.
    """

    priorities: dict[int, tuple[float, float]] = {}
    for candidate in pool:
        try:
            concept = _design_concept_descriptor(candidate)
            morphology = _solid_morphology_metrics(candidate)
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
        public_controller = bool(
            concept.get("open_voids")
            or concept.get("frontage_notches")
            or concept.get("frontage_relations")
        )
        phenotype = str(morphology.get("phenotype") or "prismatic")
        score = 0.0
        score += 4.0 if concept.get("frontage_aligned") else 0.0
        score += 3.0 if public_controller else 0.0
        score += 2.0 if concept.get("program_controller_node_ids") else 0.0
        score += 2.0 if concept.get("section_controller_node_ids") else 0.0
        score += 2.0 if phenotype == "voided" else 0.0
        score += 1.0 if phenotype in {"winged", "stepped", "curved", "oblique"} else 0.0
        score -= 3.0 if concept.get("missing_required_concepts") else 0.0
        score -= 2.0 if concept.get("ground_strategy") == "direct_edge" else 0.0
        score -= 2.0 if phenotype == "prismatic" else 0.0
        score -= 2.0 if (
            morphology.get("pyramidal_like")
            or morphology.get("wedge_like")
        ) else 0.0
        priorities[id(candidate)] = (
            score,
            float(getattr(candidate, "score", 0.0) or 0.0),
        )

    winner_priority = priorities.get(id(selector_winner))
    if not priorities or winner_priority is None:
        return selector_winner
    architectural_winner = max(
        (
            candidate for candidate in pool
            if id(candidate) in priorities
        ),
        key=lambda candidate: priorities[id(candidate)],
    )
    if priorities[id(architectural_winner)] <= winner_priority:
        return selector_winner
    return architectural_winner


def _exclude_prior_final_book_vlm_failures(
    pool: list[_Candidate],
    *,
    outcome_graph: GeometryOutcomeGraph | None,
    program_slug: str,
) -> tuple[list[_Candidate], dict[str, Any]]:
    """Avoid paying to review one unchanged exact geometry twice."""

    failed_hashes = (
        outcome_graph.failed_final_book_geometry_hashes(program_slug)
        if outcome_graph is not None
        else set()
    )
    filtered = [
        candidate
        for candidate in pool
        if str(
            (
                candidate.source.metadata.get(
                    "geometry_program_bridge_evidence"
                )
                or {}
            ).get("geometry_hash")
            or ""
        )
        not in failed_hashes
    ]
    return filtered, {
        "schema_version": "arr.maas.prior_final_vlm_failure_filter.v1",
        "program_slug": str(program_slug),
        "known_failed_geometry_count": len(failed_hashes),
        "prior_exact_failure_count": len(pool) - len(filtered),
        "remaining_candidate_count": len(filtered),
        "identity": "exact_geometry_hash",
        "paid_repeat_prevented": len(pool) - len(filtered) > 0,
    }


def _lineage_parent_key(candidate: _Candidate) -> str:
    lineage = candidate.source.metadata.get("book_generation_lineage") or {}
    return str(lineage.get("parent_key") or "")


def _base_review_fingerprint(candidate: _Candidate) -> str:
    """Stable identity for one rendered base, independent of run-local names."""
    compilation = candidate.source.metadata.get("geometry_program_compilation") or {}
    geometry_hash = str(compilation.get("geometry_hash") or "")
    raw_program = candidate.source.metadata.get("geometry_program") or {}
    if geometry_hash:
        payload = {"geometry_hash": geometry_hash}
    elif isinstance(raw_program, dict) and raw_program:
        try:
            payload = {"program_hash": GeometryProgram.from_dict(raw_program).program_hash()}
        except (KeyError, TypeError, ValueError):
            payload = {"program": raw_program}
    else:
        payload = {
            "parent_key": _lineage_parent_key(candidate),
            "principle_id": candidate.principle_id,
            "scope": _scope_key(candidate),
        }
    return hashlib.sha256(json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _book_vlm_review_contract(review_stage: str) -> dict[str, Any]:
    """Return the immutable contract that makes a visual verdict reusable.

    Exact geometry alone is insufficient: a verdict from another model,
    prompt, or stage gate must never silently approve a current base.  The PNU
    and program are graph-level/query-level boundaries; this fingerprint
    covers the remaining visual-review semantics.
    """
    policy = book_vlm_stage_policy(review_stage)
    evidence = {
        "review_stage": str(review_stage),
        "model": str(os.getenv("MAAS_PREFERENCE_VLM_MODEL") or DEFAULT_VLM_MODEL),
        "prompt_contract_version": VLM_PROMPT_CONTRACT_VERSION,
        "gate_policy": policy.to_evidence(),
    }
    evidence["fingerprint"] = hashlib.sha256(json.dumps(
        evidence,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return evidence


def _book_vlm_review_budget(review_stage: str) -> int:
    """Keep base-parent and final-solid review coverage independently bounded."""
    if review_stage == "book_base_operative":
        variable, default, ceiling = "MAAS_BOOK_BASE_VLM_TOP_K", 8, 32
    else:
        variable, default, ceiling = "MAAS_FINAL_BOOK_VLM_TOP_K", 12, 48
    try:
        return max(1, min(ceiling, int(os.getenv(variable, str(default)))))
    except (TypeError, ValueError):
        return default


def _book_base_parent_shortlist(
    pool: list[_Candidate],
    *,
    target: int,
    visual_directive: dict[str, Any],
) -> tuple[list[_Candidate], dict[str, Any]]:
    """Choose base reviews from the descendants the final board may use.

    A generic base-only shortlist can spend the complete VLM budget on
    attractive one-operative masses whose exact lineages have no competitive
    combination or aggregation left in the downstream pool.  Start from a
    structurally stratified descendant shortlist, resolve its exact base
    parents, then use ordinary base strata only to fill unused review slots.
    This preserves the base-before-descendant causal contract without making
    unreviewed parents indistinguishable from visually rejected parents.
    """
    review_target = max(0, min(int(target), len(pool)))
    bases = [
        candidate for candidate in pool
        if str((candidate.source.metadata.get("book_generation_lineage") or {}).get("stage") or "")
        == "base"
    ]
    descendants = [
        candidate for candidate in pool
        if str((candidate.source.metadata.get("book_generation_lineage") or {}).get("stage") or "")
        != "base"
    ]
    bases_by_key: dict[str, _Candidate] = {}
    for candidate in sorted(bases, key=lambda item: item.score, reverse=True):
        parent_key = _lineage_parent_key(candidate)
        if parent_key and parent_key not in bases_by_key:
            bases_by_key[parent_key] = candidate

    # Reserve base-review bandwidth before descendant parent resolution.  In
    # r150, 60 descendant parents consumed a 64-image budget and left only
    # four generic fallback slots. Three valid split_bridge bases therefore
    # existed but were never seen by the VLM. Required families and one
    # representative of every executable core family are review anchors only;
    # they gain no score or hard-pass preference.
    required_families = tuple(dict.fromkeys(
        str(value)
        for value in visual_directive.get("required_geometry_program_families") or ()
        if str(value)
    ))
    geometry_review_caps = {
        str(family): max(1, int(cap))
        for family, cap in (visual_directive.get("max_geometry_family_counts") or {}).items()
        if str(family)
    }
    chassis_review_caps = {
        str(family): max(1, int(cap))
        for family, cap in (visual_directive.get("max_chassis_family_counts") or {}).items()
        if str(family)
    }
    global_chassis_review_cap = max(
        0,
        int(visual_directive.get("max_chassis_family_count") or 0),
    )
    review_geometry_usage: Counter[str] = Counter()
    review_chassis_usage: Counter[str] = Counter()
    review_cap_skip_counts: Counter[str] = Counter()

    def capped_chassis_family(candidate: _Candidate) -> str:
        if not chassis_review_caps and not global_chassis_review_cap:
            return ""
        return _chassis_family(candidate)

    def can_add(candidate: _Candidate) -> bool:
        geometry_family = _geometry_program_family(candidate)
        chassis_family = capped_chassis_family(candidate)
        geometry_cap = geometry_review_caps.get(geometry_family)
        chassis_cap = chassis_review_caps.get(chassis_family, global_chassis_review_cap or None)
        if geometry_cap is not None and review_geometry_usage[geometry_family] >= geometry_cap:
            review_cap_skip_counts[f"geometry:{geometry_family}"] += 1
            return False
        if chassis_cap is not None and review_chassis_usage[chassis_family] >= chassis_cap:
            review_cap_skip_counts[f"chassis:{chassis_family}"] += 1
            return False
        return True

    def add(candidate: _Candidate) -> bool:
        if id(candidate) in chosen_ids or not can_add(candidate):
            return False
        chosen.append(candidate)
        chosen_ids.add(id(candidate))
        review_geometry_usage[_geometry_program_family(candidate)] += 1
        chassis_family = capped_chassis_family(candidate)
        if chassis_family:
            review_chassis_usage[chassis_family] += 1
        return True

    base_strata: dict[str, list[_Candidate]] = {}
    base_chassis_strata: dict[str, list[_Candidate]] = {}
    for candidate in sorted(bases, key=lambda item: item.score, reverse=True):
        base_strata.setdefault(_geometry_program_family(candidate), []).append(candidate)
        chassis_family = _chassis_family(candidate)
        if chassis_family not in {"", "generic_chassis", "recursive_chassis:unclassified"}:
            base_chassis_strata.setdefault(chassis_family, []).append(candidate)
    core_families = sorted({
        _geometry_program_family(candidate)
        for candidate in bases
        if _form_bank_lane(candidate) == "executable_core_language"
        and _geometry_program_family(candidate)
    })
    anchor_target = min(
        review_target,
        max(
            len([family for family in required_families if family in base_strata]),
            len(core_families),
            len(base_chassis_strata),
            review_target // 3,
        ),
    )
    chosen: list[_Candidate] = []
    chosen_ids: set[int] = set()
    for family in required_families:
        if len(chosen) >= review_target:
            break
        match = next((
            candidate for candidate in base_strata.get(family, ())
            if id(candidate) not in chosen_ids and can_add(candidate)
        ), None)
        if match is not None:
            add(match)
    # Geometry-family anchors alone still allowed several author families to
    # collapse onto the same plan chassis (for example many agents producing
    # the same courtyard or bent bar). Reserve one review seat per measured
    # chassis, rarest supply first. This is taxonomy-derived coverage only:
    # each candidate must still pass the unchanged base and final VLM gates.
    chassis_families = sorted(
        base_chassis_strata,
        key=lambda family: (len(base_chassis_strata[family]), family),
    )
    for chassis_family in chassis_families:
        if len(chosen) >= anchor_target:
            break
        match = next((
            candidate for candidate in base_chassis_strata[chassis_family]
            if id(candidate) not in chosen_ids and can_add(candidate)
        ), None)
        if match is not None:
            add(match)
    core_depth = 0
    while len(chosen) < anchor_target:
        added = False
        for family in core_families:
            bucket = base_strata.get(family, [])
            if core_depth >= len(bucket):
                continue
            candidate = bucket[core_depth]
            if add(candidate):
                added = True
            if len(chosen) >= anchor_target:
                break
        if not added:
            break
        core_depth += 1

    descendant_shortlist = _final_book_vlm_shortlist(
        descendants,
        # Inspect the complete bounded descendant pool before applying typed
        # family quotas; taking only the first review_target here could leave
        # every alternate parent hidden behind capped families.
        target=len(descendants),
        visual_directive=visual_directive,
    )
    requested_parent_keys: list[str] = []
    for descendant in descendant_shortlist:
        parent_key = _lineage_parent_key(descendant)
        if (
            parent_key
            and parent_key in bases_by_key
            and parent_key not in requested_parent_keys
        ):
            requested_parent_keys.append(parent_key)

    for parent_key in requested_parent_keys:
        candidate = bases_by_key[parent_key]
        if id(candidate) in chosen_ids or not can_add(candidate):
            continue
        add(candidate)
        if len(chosen) >= review_target:
            break
    fallback = _final_book_vlm_shortlist(
        bases,
        target=len(bases),
        visual_directive=visual_directive,
    )
    for candidate in fallback:
        if id(candidate) in chosen_ids or not can_add(candidate):
            continue
        add(candidate)
        if len(chosen) >= review_target:
            break
    return chosen[:review_target], {
        "schema_version": "arr.maas.book_base_parent_shortlist.v1",
        "review_target": review_target,
        "base_candidate_count": len(bases),
        "descendant_candidate_count": len(descendants),
        "descendant_shortlist_count": len(descendant_shortlist),
        "requested_exact_parent_count": len(requested_parent_keys),
        "resolved_exact_parent_count": sum(
            _lineage_parent_key(candidate) in requested_parent_keys
            for candidate in chosen[:review_target]
        ),
        "required_family_anchor_count": sum(
            _geometry_program_family(candidate) in required_families
            for candidate in chosen[:anchor_target]
        ),
        "executable_core_family_anchor_count": len({
            _geometry_program_family(candidate)
            for candidate in chosen[:anchor_target]
            if _form_bank_lane(candidate) == "executable_core_language"
        }),
        "chassis_family_anchor_count": len({
            _chassis_family(candidate)
            for candidate in chosen[:anchor_target]
        }),
        "base_anchor_target": anchor_target,
        "base_anchor_family_counts": dict(sorted(Counter(
            _geometry_program_family(candidate) or "unclassified"
            for candidate in chosen[:anchor_target]
        ).items())),
        "fallback_base_count": max(
            0,
            min(len(chosen), review_target)
            - anchor_target
            - sum(
                _lineage_parent_key(candidate) in requested_parent_keys
                for candidate in chosen[anchor_target:review_target]
            ),
        ),
        "base_family_supply_counts": dict(sorted(Counter(
            _geometry_program_family(candidate) or "unclassified"
            for candidate in bases
        ).items())),
        "base_chassis_supply_counts": dict(sorted(Counter(
            _chassis_family(candidate) or "unclassified"
            for candidate in bases
        ).items())),
        "descendant_family_supply_counts": dict(sorted(Counter(
            _geometry_program_family(candidate) or "unclassified"
            for candidate in descendants
        ).items())),
        "descendant_shortlist_family_counts": dict(sorted(Counter(
            _geometry_program_family(candidate) or "unclassified"
            for candidate in descendant_shortlist
        ).items())),
        "resolved_parent_family_counts": dict(sorted(Counter(
            _geometry_program_family(candidate) or "unclassified"
            for candidate in chosen[:review_target]
        ).items())),
        "geometry_family_review_caps": dict(sorted(geometry_review_caps.items())),
        "chassis_family_review_caps": dict(sorted(chassis_review_caps.items())),
        "global_chassis_review_cap": global_chassis_review_cap,
        "review_cap_skip_counts": dict(sorted(review_cap_skip_counts.items())),
        "review_caps_are_supply_quotas_not_quality_relaxations": True,
        "review_order": "required_family_then_rare_chassis_then_core_alphabet_then_descendant_parent_then_fallback",
        "descendant_first_parent_resolution": True,
        "review_anchors_grant_no_hard_pass_or_selection_preference": True,
    }


def _attach_base_book_vlm_audit(
    candidate: _Candidate,
    audit: dict[str, Any],
    *,
    reused_from_outcome_graph: bool,
) -> _Candidate:
    """Normalize one base verdict without leaving a false final-stage audit."""
    normalized = deepcopy(audit)
    normalized.update({
        "review_stage": "book_base_operative",
        "reviewed_before_descendant_release": True,
        "reused_from_outcome_graph": bool(reused_from_outcome_graph),
        "base_review_fingerprint": _base_review_fingerprint(candidate),
    })
    metadata = dict(candidate.source.metadata)
    metadata.pop("final_book_vlm_audit", None)
    metadata["base_book_vlm_audit"] = normalized
    feature = deepcopy(candidate.feature)
    properties = feature.setdefault("properties", {})
    properties.pop("final_book_vlm_audit", None)
    properties["base_book_vlm_audit"] = deepcopy(normalized)
    scores = normalized.get("concept_scores")
    if isinstance(scores, dict) and scores:
        visual_score = sum(float(scores.get(key) or 0.0) for key in (
            "gesture_clarity", "hierarchy", "non_stair_silhouette", "void_publicness",
            "repair_integrity", "precedent_resonance", "program_appropriateness",
            "section_program_fit",
        )) / 8.0
        score = candidate.score * 0.72 + visual_score * 0.28
    else:
        score = candidate.score
    return replace(
        candidate,
        source=replace(candidate.source, metadata=metadata),
        feature=feature,
        score=score,
    )


def _audit_final_book_geometry_with_vlm(
    pool: list[_Candidate],
    *,
    building_type: str,
    output_dir: Path,
    visual_directive: dict[str, Any],
    outcome_graph: GeometryOutcomeGraph | None = None,
    program_slug: str = "",
    scorer: Any | None = None,
    reference_provider: Any | None = None,
    review_stage: str = "final_book",
    shortlist_override: list[_Candidate] | None = None,
) -> tuple[list[_Candidate], dict[str, Any]]:
    """Review the post-BOOK solid the user actually sees.

    The earlier recursive-program critic remains the author/reviser. This
    bounded pass closes the causal gap where later BOOK projection could make
    a floating plate or cake-tier silhouette that inherited an obsolete VLM
    score from its pre-BOOK parent.
    """
    maximum = _book_vlm_review_budget(review_stage)
    try:
        workers = max(1, min(6, int(os.getenv("MAAS_FINAL_BOOK_VLM_WORKERS", "4"))))
    except (TypeError, ValueError):
        workers = 4
    input_count = len(pool)
    pool = [candidate for candidate in pool if _has_exact_geometry_program(candidate)]
    invalid_geometry_program_count = input_count - len(pool)
    if review_stage == "final_book":
        pool, prior_failure_filter = _exclude_prior_final_book_vlm_failures(
            pool,
            outcome_graph=outcome_graph,
            program_slug=program_slug or building_type,
        )
    else:
        prior_failure_filter = {
            "schema_version": "arr.maas.prior_final_vlm_failure_filter.v1",
            "status": "not_applicable_to_base_stage",
            "prior_exact_failure_count": 0,
            "remaining_candidate_count": len(pool),
            "paid_repeat_prevented": False,
        }
    if shortlist_override is not None:
        shortlist = [
            candidate for candidate in list(shortlist_override)
            if _has_exact_geometry_program(candidate)
        ][:min(maximum, len(pool))]
        target = min(maximum, len(pool))
        if len(shortlist) < target:
            selected_ids = {id(candidate) for candidate in shortlist}
            fallback = _final_book_vlm_shortlist(
                [candidate for candidate in pool if id(candidate) not in selected_ids],
                target=target - len(shortlist),
                visual_directive=visual_directive,
            )
            shortlist.extend(fallback)
    else:
        shortlist = _final_book_vlm_shortlist(
            pool,
            target=min(maximum, len(pool)),
            visual_directive=visual_directive,
        )
    cache_dir = Path(os.getenv(
        "MAAS_FINAL_BOOK_VLM_CACHE_DIR",
        "docs/ai-session-memory/reference-corpus/final-book-vlm-cache",
    ))
    preview_dir = output_dir / "final-book-vlm-previews"
    scorer = scorer or openai_preview_preference_scorer(
        preview_dir=preview_dir,
        cache_dir=cache_dir,
    )
    def evaluate(candidate: _Candidate) -> tuple[_Candidate, list[dict[str, Any]], dict[str, Any]]:
        raw_program = candidate.source.metadata.get("geometry_program") or {}
        program = GeometryProgram.from_dict(raw_program)
        references, reference_audit = _audited_final_book_references(
            program,
            building_type=building_type,
            reference_provider=reference_provider,
        )
        review_feature = deepcopy(candidate.feature)
        materialize_source_feature_surfaces(
            review_feature,
            candidate.source,
            height=float(
                review_feature.get("properties", {}).get("height")
                or review_feature.get("properties", {}).get("height_m")
                or 1.0
            ),
        )
        # This critic repairs the exact recursive post-BOOK AST.  It must not
        # emit edits against the separate legacy program-role component graph.
        review_feature.setdefault("properties", {})["geometry_only_critic_mode"] = True
        candidate_morphology = _solid_morphology_metrics(candidate)
        review_feature.setdefault("properties", {})["portfolio_diversity_context"] = {
            "schema_version": "arr.maas.final_book_candidate_context.v2",
            "candidate_phenotype": str(candidate_morphology["phenotype"]),
            "candidate_pyramidal_like": bool(candidate_morphology["pyramidal_like"]),
            "maximum_final_pyramidal_like_count": int(
                visual_directive.get("max_pyramidal_like_count", 2)
            ),
            "maximum_final_single_phenotype_count": int(
                visual_directive.get("max_solid_phenotype_count", 5)
            ),
            "critic_is_reviewing_exact_post_book_geometry": True,
            "book_review_stage": review_stage,
            "board_level_sibling_diversity_is_a_separate_vlm_gate": True,
            "volatile_pool_composition_excluded_from_candidate_identity": True,
        }
        review_feature["properties"]["capacity_review_context"] = (
            build_capacity_review_context(candidate.source.metadata)
        )
        result = scorer(
            feature=review_feature,
            reference_matches=list(references or ()),
            model=os.getenv("MAAS_PREFERENCE_VLM_MODEL") or None,
        )
        result["reference_massing_gate"] = {
            key: value
            for key, value in reference_audit.items()
            if key != "accepted"
        }
        return candidate, list(references or ()), result

    evaluated: dict[int, tuple[list[dict[str, Any]], dict[str, Any] | None, str]] = {}
    with ThreadPoolExecutor(max_workers=min(workers, max(1, len(shortlist)))) as executor:
        futures = {executor.submit(evaluate, candidate): candidate for candidate in shortlist}
        for future in as_completed(futures):
            candidate = futures[future]
            try:
                _candidate, references, result = future.result()
                evaluated[id(candidate)] = (references, result, "")
            except Exception as exc:
                evaluated[id(candidate)] = ([], None, str(exc)[:500])

    # A transient provider timeout is not architectural evidence.  The scorer
    # already retries one HTTP request, but a burst of parallel calls can still
    # exhaust those attempts together.  Re-run only failed candidates at low
    # concurrency; completed paid calls are retained in the cache and never
    # repeated here.  Candidates that still fail remain rejected.
    initial_call_failures = {
        id(candidate): evaluated.get(id(candidate), ([], None, "missing_result"))[2]
        for candidate in shortlist
        if (
            evaluated.get(id(candidate), ([], None, "missing_result"))[2]
            or not isinstance(
                evaluated.get(id(candidate), ([], None, "missing_result"))[1],
                dict,
            )
        )
    }
    try:
        recovery_workers = max(1, min(
            2,
            int(os.getenv("MAAS_FINAL_BOOK_VLM_RECOVERY_WORKERS", "1")),
        ))
    except (TypeError, ValueError):
        recovery_workers = 1
    recovery_candidates = [
        candidate for candidate in shortlist
        if id(candidate) in initial_call_failures
    ]
    if recovery_candidates:
        with ThreadPoolExecutor(max_workers=min(recovery_workers, len(recovery_candidates))) as executor:
            futures = {
                executor.submit(evaluate, candidate): candidate
                for candidate in recovery_candidates
            }
            for future in as_completed(futures):
                candidate = futures[future]
                try:
                    _candidate, references, result = future.result()
                    evaluated[id(candidate)] = (references, result, "")
                except Exception as exc:
                    evaluated[id(candidate)] = ([], None, str(exc)[:500])

    review_contract = _book_vlm_review_contract(review_stage)
    accepted: list[_Candidate] = []
    failure_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    llm_failure_counts: Counter[str] = Counter()
    llm_action_counts: Counter[str] = Counter()
    llm_hard_pass_count = 0
    scored_count = cache_hit_count = 0
    audit_records: list[dict[str, Any]] = []
    call_failure_records: list[dict[str, Any]] = []
    for candidate in shortlist:
        references, result, error = evaluated.get(id(candidate), ([], None, "missing_result"))
        if error or not isinstance(result, dict):
            failure_counts["final_book_vlm_call_failed"] += 1
            call_failure_records.append({
                "source_sequence": candidate.sequence.name,
                "parent_key": _lineage_parent_key(candidate),
                "book_principle_id": candidate.principle_id,
                "book_scope": _scope_key(candidate),
                "geometry_family": _geometry_program_family(candidate),
                "error": error or "missing_result",
            })
            continue
        program = GeometryProgram.from_dict(
            candidate.source.metadata.get("geometry_program") or {}
        )
        scored_count += 1
        cache_hit_count += int(bool(result.get("cache_hit")))
        stage_policy = book_vlm_stage_policy(review_stage)
        candidate_morphology = _solid_morphology_metrics(candidate)
        candidate_design_concept = _design_concept_descriptor(candidate)
        candidate_capacity = (
            candidate.source.metadata.get("source_capacity_measurement") or {}
        )
        effective_capacity_floor = _book_stage_capacity_floor(candidate, review_stage)
        hard_pass, failures = _final_book_vlm_hard_pass(
            result,
            candidate_morphology=candidate_morphology,
            candidate_design_concept=candidate_design_concept,
            candidate_capacity=candidate_capacity,
            minimum_capacity_utilization=effective_capacity_floor,
            review_stage=review_stage,
        )
        failure_counts.update(failures)
        action_counts.update(str(value) for value in result.get("critic_actions") or ())
        if _llm_authored_candidate(candidate):
            llm_failure_counts.update(failures)
            llm_action_counts.update(str(value) for value in result.get("critic_actions") or ())
            llm_hard_pass_count += int(hard_pass)
        scores = result.get("concept_scores") if isinstance(result.get("concept_scores"), dict) else {}
        visual_score = sum(float(scores.get(key) or 0.0) for key in (
            "gesture_clarity", "hierarchy", "non_stair_silhouette", "void_publicness",
            "repair_integrity", "precedent_resonance", "program_appropriateness", "section_program_fit",
        )) / 8.0
        audit = {
            "schema_version": "arr.maas.final_book_vlm_audit.v1",
            "status": "pass" if hard_pass else "fail",
            "hard_pass": hard_pass,
            "failures": failures,
            "model": str(result.get("model") or ""),
            "prompt_contract_version": str(
                result.get("prompt_contract_version")
                or review_contract["prompt_contract_version"]
            ),
            "review_contract_fingerprint": str(review_contract["fingerprint"]),
            "response_id": str(result.get("response_id") or ""),
            "cache_hit": bool(result.get("cache_hit")),
            "concept_scores": dict(scores),
            "critic_actions": list(result.get("critic_actions") or ()),
            "geometry_edits": list(result.get("geometry_edits") or ()),
            "rationale": str(result.get("rationale") or "")[:1000],
            "capacity_review_context": build_capacity_review_context(
                candidate.source.metadata
            ),
            "reference_ids": [str(item.get("source_id") or "") for item in references[:5]],
            "reference_records": [
                {
                    "source_id": str(item.get("source_id") or ""),
                    "source": str(item.get("source") or ""),
                    "title": str(item.get("title") or ""),
                    "selection_role": str(item.get("selection_role") or ""),
                    "program_id": str(item.get("program_id") or ""),
                    "program_match_tier": str(item.get("program_match_tier") or ""),
                    "matched_tags": list(item.get("matched_tags") or ()),
                    "source_url": str(item.get("source_url") or item.get("page_url") or ""),
                    "local_path": str(item.get("local_path") or ""),
                    "image_url": str(item.get("image_url") or ""),
                    "massing_image_audit": deepcopy(item.get("massing_image_audit") or {}),
                }
                for item in references[:5]
                if isinstance(item, dict)
            ],
            "reviewed_exact_post_book_geometry": True,
            "review_stage": review_stage,
            "gate_policy": stage_policy.to_evidence(),
            "minimum_feasible_capacity_utilization": stage_policy.minimum_feasible_capacity_utilization,
            "effective_minimum_feasible_capacity_utilization": effective_capacity_floor,
            "capacity_normalization": stage_policy.capacity_normalization,
            "candidate_capacity": deepcopy(candidate_capacity),
            "candidate_morphology": deepcopy(candidate_morphology),
            "candidate_design_concept": deepcopy(candidate_design_concept),
            "legal_or_parking_score": False,
            "reference_massing_gate": deepcopy(result.get("reference_massing_gate") or {}),
        }
        audit_records.append({
            "source_sequence": candidate.sequence.name,
            "parent_key": _lineage_parent_key(candidate),
            "book_principle_id": candidate.principle_id,
            "book_scope": _scope_key(candidate),
            "geometry_family": _geometry_program_family(candidate),
            "form_bank_lane": _form_bank_lane(candidate),
            "llm_authored_lane": _llm_authored_candidate(candidate),
            "hard_pass": hard_pass,
            "failures": failures,
            "response_id": audit["response_id"],
            "concept_scores": dict(scores),
            "critic_actions": list(audit["critic_actions"]),
            "geometry_edits": list(audit["geometry_edits"]),
            "reference_ids": list(audit["reference_ids"]),
            "reference_massing_gate": deepcopy(audit["reference_massing_gate"]),
            "candidate_capacity": deepcopy(candidate_capacity),
            "candidate_morphology": deepcopy(candidate_morphology),
            "candidate_design_concept": deepcopy(candidate_design_concept),
            "program_hash": program.program_hash(),
            "geometry_hash": str(
                candidate.source.metadata.get("geometry_program_compilation", {}).get("geometry_hash")
                if isinstance(candidate.source.metadata.get("geometry_program_compilation"), dict)
                else ""
            ),
            "geometry_program": program.to_dict(),
            "review_image_path": str(result.get("review_image_path") or ""),
            "vlm_audit": deepcopy(audit),
            "chronological_archive_replayable": bool(result.get("review_image_path")),
        })
        if outcome_graph is not None:
            if review_stage == "book_base_operative":
                outcome_graph.observe_base_book_vlm_audit(
                    program_slug=program_slug or building_type,
                    candidate=candidate,
                    base_review_fingerprint=_base_review_fingerprint(candidate),
                    review_contract_fingerprint=str(review_contract["fingerprint"]),
                    audit=audit,
                )
            else:
                outcome_graph.observe_final_book_vlm_audit(
                    program_slug=program_slug or building_type,
                    candidate=candidate,
                    audit=audit,
                )
        source_metadata = dict(candidate.source.metadata)
        source_metadata["final_book_vlm_audit"] = audit
        feature = deepcopy(candidate.feature)
        feature.setdefault("properties", {})["final_book_vlm_audit"] = deepcopy(audit)
        revised = replace(
            candidate,
            source=replace(candidate.source, metadata=source_metadata),
            feature=feature,
            score=candidate.score * 0.72 + visual_score * 0.28,
        )
        if hard_pass:
            accepted.append(revised)
    evidence = {
        "schema_version": "arr.maas.final_book_vlm_portfolio_gate.v1",
        "required": True,
        "input_count": input_count,
        "exact_geometry_program_input_count": len(pool),
        "invalid_geometry_program_rejected_count": invalid_geometry_program_count,
        "prior_final_vlm_failure_filter": prior_failure_filter,
        "shortlist_count": len(shortlist),
        "review_budget": maximum,
        "scored_count": scored_count,
        "cache_hit_count": cache_hit_count,
        "initial_call_failure_count": len(initial_call_failures),
        "recovered_call_failure_count": max(
            0,
            len(initial_call_failures) - len(call_failure_records),
        ),
        "unrecovered_call_failure_count": len(call_failure_records),
        "call_failure_records": call_failure_records,
        "recovery_workers": recovery_workers,
        "hard_pass_count": len(accepted),
        "failure_counts": dict(sorted(failure_counts.items())),
        "critic_action_counts": dict(sorted(action_counts.items())),
        "llm_authored_input_count": sum(_llm_authored_candidate(candidate) for candidate in pool),
        "llm_authored_shortlist_count": sum(_llm_authored_candidate(candidate) for candidate in shortlist),
        "llm_authored_hard_pass_count": llm_hard_pass_count,
        "llm_authored_failure_counts": dict(sorted(llm_failure_counts.items())),
        "llm_authored_critic_action_counts": dict(sorted(llm_action_counts.items())),
        "llm_authored_review_quota_only_not_selection_preference": True,
        "executable_core_input_count": sum(
            _form_bank_lane(candidate) == "executable_core_language"
            for candidate in pool
        ),
        "executable_core_shortlist_count": sum(
            _form_bank_lane(candidate) == "executable_core_language"
            for candidate in shortlist
        ),
        "executable_core_hard_pass_count": sum(
            _form_bank_lane(candidate) == "executable_core_language"
            for candidate in accepted
        ),
        "geometry_family_input_counts": dict(sorted(Counter(
            _geometry_program_family(candidate) or "unclassified"
            for candidate in pool
        ).items())),
        "geometry_family_shortlist_counts": dict(sorted(Counter(
            _geometry_program_family(candidate) or "unclassified"
            for candidate in shortlist
        ).items())),
        "geometry_family_hard_pass_counts": dict(sorted(Counter(
            _geometry_program_family(candidate) or "unclassified"
            for candidate in accepted
        ).items())),
        "executable_core_review_quota_only_not_selection_preference": True,
        "post_book_geometry_reviewed": True,
        "review_stage": review_stage,
        "synthetic_fallback_used": False,
        "selection_input_is_reviewed_hard_pass_only": True,
        "audit_records": audit_records,
    }
    return accepted, evidence


def audit_book_base_stage_with_vlm(
    pool: list[_Candidate],
    *,
    building_type: str,
    output_dir: Path,
    visual_directive: dict[str, Any],
    outcome_graph: GeometryOutcomeGraph | None = None,
    program_slug: str = "",
    scorer: Any | None = None,
    reference_provider: Any | None = None,
    excluded_parent_keys: set[str] | None = None,
    excluded_parent_fingerprints: set[str] | None = None,
) -> tuple[list[_Candidate], dict[str, Any]]:
    """Approve descendants only after their exact BOOK base parent is seen.

    The former pre-BOOK critic reviewed the recursive author body before any
    BOOK language existed.  This gate instead renders the one-operative base
    stage at its capacity-conditioned site scale, records that image audit,
    and releases only combinations/aggregations sharing the approved parent
    key.  Every released descendant is still reviewed again at the final
    post-BOOK stage.
    """
    excluded_parent_keys = {
        str(value) for value in (excluded_parent_keys or set()) if str(value)
    }
    excluded_parent_fingerprints = {
        str(value) for value in (excluded_parent_fingerprints or set()) if str(value)
    }
    all_bases = [
        candidate for candidate in pool
        if str((candidate.source.metadata.get("book_generation_lineage") or {}).get("stage") or "")
        == "base"
    ]
    base_fingerprint_by_parent = {
        _lineage_parent_key(candidate): _base_review_fingerprint(candidate)
        for candidate in all_bases
        if _lineage_parent_key(candidate)
    }
    eligible_pool = [
        candidate for candidate in pool
        if _lineage_parent_key(candidate) not in excluded_parent_keys
        and base_fingerprint_by_parent.get(_lineage_parent_key(candidate), "")
        not in excluded_parent_fingerprints
    ]
    bases = [
        candidate for candidate in eligible_pool
        if str((candidate.source.metadata.get("book_generation_lineage") or {}).get("stage") or "")
        == "base"
    ]
    if not bases:
        return [], {
            "schema_version": "arr.maas.book_base_stage_vlm_gate.v2",
            "required": True,
            "status": "no_viable_base_stage_candidates",
            "input_count": len(pool),
            "eligible_input_count": len(eligible_pool),
            "excluded_parent_count": len(excluded_parent_keys),
            "excluded_parent_fingerprint_count": len(excluded_parent_fingerprints),
            "base_input_count": 0,
            "approved_base_count": 0,
            "released_descendant_count": 0,
            "hard_pass": False,
        }

    review_contract = _book_vlm_review_contract("book_base_operative")
    persisted_audits = (
        outcome_graph.approved_base_book_vlm_audits(
            program_slug=program_slug or building_type,
            base_review_fingerprints=(
                _base_review_fingerprint(candidate) for candidate in bases
            ),
            review_contract_fingerprint=str(review_contract["fingerprint"]),
        )
        if outcome_graph is not None
        else {}
    )
    reused_by_key: dict[str, _Candidate] = {}
    reused_audits: dict[str, dict[str, Any]] = {}
    for candidate in bases:
        parent_key = _lineage_parent_key(candidate)
        audit = persisted_audits.get(_base_review_fingerprint(candidate))
        if not parent_key or not isinstance(audit, dict):
            continue
        reused_by_key[parent_key] = _attach_base_book_vlm_audit(
            candidate,
            audit,
            reused_from_outcome_graph=True,
        )
        reused_audits[parent_key] = deepcopy(audit)

    fresh_pool = [
        candidate for candidate in eligible_pool
        if _lineage_parent_key(candidate) not in reused_by_key
    ]
    fresh_bases = [
        candidate for candidate in bases
        if _lineage_parent_key(candidate) not in reused_by_key
    ]
    review_budget = _book_vlm_review_budget("book_base_operative")
    if fresh_bases:
        parent_shortlist, parent_shortlist_evidence = _book_base_parent_shortlist(
            fresh_pool,
            target=min(review_budget, len(fresh_bases)),
            visual_directive=visual_directive,
        )
        approved, raw_evidence = _audit_final_book_geometry_with_vlm(
            fresh_bases,
            building_type=building_type,
            output_dir=output_dir,
            visual_directive=visual_directive,
            outcome_graph=outcome_graph,
            program_slug=program_slug,
            scorer=scorer,
            reference_provider=reference_provider,
            review_stage="book_base_operative",
            shortlist_override=parent_shortlist,
        )
    else:
        parent_shortlist = []
        parent_shortlist_evidence = {
            "status": "all_exact_bases_resolved_from_outcome_graph",
            "review_target": 0,
        }
        approved = []
        raw_evidence = {
            "schema_version": "arr.maas.final_book_vlm_portfolio_gate.v1",
            "required": True,
            "status": "all_exact_bases_resolved_from_outcome_graph",
            "input_count": 0,
            "shortlist_count": 0,
            "scored_count": 0,
            "hard_pass_count": 0,
            "audit_records": [],
            "review_stage": "book_base_operative",
        }

    approved_by_key: dict[str, _Candidate] = dict(reused_by_key)
    base_audits: dict[str, dict[str, Any]] = dict(reused_audits)
    for candidate in approved:
        parent_key = _lineage_parent_key(candidate)
        if not parent_key:
            continue
        audit = dict(candidate.source.metadata.get("final_book_vlm_audit") or {})
        approved_by_key[parent_key] = _attach_base_book_vlm_audit(
            candidate,
            audit,
            reused_from_outcome_graph=False,
        )
        base_audits[parent_key] = audit

    released: list[_Candidate] = list(approved_by_key.values())
    descendant_count = 0
    for candidate in eligible_pool:
        lineage = candidate.source.metadata.get("book_generation_lineage") or {}
        if str(lineage.get("stage") or "") == "base":
            continue
        parent_key = str(lineage.get("parent_key") or "")
        if parent_key not in approved_by_key:
            continue
        parent_audit = base_audits[parent_key]
        metadata = dict(candidate.source.metadata)
        metadata["base_book_vlm_parent_audit"] = {
            "parent_key": parent_key,
            "hard_pass": True,
            "response_id": str(parent_audit.get("response_id") or ""),
            "review_stage": "book_base_operative",
            "base_review_fingerprint": base_fingerprint_by_parent.get(parent_key, ""),
            "review_contract_fingerprint": str(review_contract["fingerprint"]),
            "reused_from_outcome_graph": parent_key in reused_by_key,
        }
        feature = deepcopy(candidate.feature)
        feature.setdefault("properties", {})["base_book_vlm_parent_audit"] = deepcopy(
            metadata["base_book_vlm_parent_audit"]
        )
        released.append(replace(
            candidate,
            source=replace(candidate.source, metadata=metadata),
            feature=feature,
        ))
        descendant_count += 1

    reviewed_parent_keys = sorted(set(reused_by_key) | {
        str(record.get("parent_key") or "")
        for record in raw_evidence.get("audit_records") or ()
        if str(record.get("parent_key") or "")
    })
    reviewed_parent_fingerprints = sorted(set(persisted_audits) | {
        _base_review_fingerprint(candidate) for candidate in parent_shortlist
    })
    return released, {
        "schema_version": "arr.maas.book_base_stage_vlm_gate.v2",
        "required": True,
        "status": "complete",
        "input_count": len(pool),
        "eligible_input_count": len(eligible_pool),
        "excluded_parent_count": len(excluded_parent_keys),
        "excluded_parent_fingerprint_count": len(excluded_parent_fingerprints),
        "base_input_count": len(bases),
        "fresh_base_input_count": len(fresh_bases),
        "persisted_approved_base_count": len(reused_by_key),
        "newly_approved_base_count": len(approved_by_key) - len(reused_by_key),
        "approved_base_count": len(approved_by_key),
        "released_descendant_count": descendant_count,
        "rejected_descendant_count": max(
            0,
            len(eligible_pool) - len(bases) - descendant_count,
        ),
        "hard_pass": bool(approved_by_key),
        "base_audit": raw_evidence,
        "parent_shortlist": parent_shortlist_evidence,
        "reviewed_parent_keys": reviewed_parent_keys,
        "reviewed_parent_fingerprints": reviewed_parent_fingerprints,
        "review_contract": review_contract,
        "persistent_approval_requires_exact_geometry_program_site_and_contract": True,
        "descendants_require_exact_approved_parent_key": True,
        "final_post_book_vlm_still_required": True,
    }


def _repair_exact_post_book_candidates_from_vlm(
    audited_pool: list[_Candidate],
    audit_gate: dict[str, Any],
    *,
    generation_site: Polygon,
    building_type: str,
    height: float,
    floors: int,
    generation_context: LegalGenerationContext | None,
    program_dimensional_context: dict[str, Any] | None,
    site_boundary_source: str,
    site_access_context: dict[str, Any] | None,
    site_access_geometry: dict[str, Any] | None,
    base_capacity_contract: dict[str, Any] | None = None,
    capacity_site: Polygon | None = None,
    repair_budget: int = 32,
) -> tuple[list[_Candidate], dict[str, Any]]:
    """Apply exact final-image VLM edits to that candidate's final AST.

    Outcome memory and a fresh LLM author remain useful for exploration, but
    they are an indirect repair path.  This function closes the shorter causal
    loop: final render -> typed edit -> same final AST -> compiler -> clean and
    program gates.  BOOK nodes already exist in the audited program, so they
    are not projected a second time.
    """

    records = {
        str(record.get("source_sequence") or ""): record
        for record in audit_gate.get("audit_records") or ()
        if isinstance(record, dict)
        and not record.get("hard_pass")
        and isinstance(record.get("geometry_edits"), list)
        and record.get("geometry_edits")
    }
    eligible = [
        candidate for candidate in audited_pool
        if candidate.sequence.name in records
        and isinstance(candidate.source.metadata.get("geometry_program"), dict)
    ]
    candidates = _exact_post_book_repair_shortlist(
        eligible,
        records,
        repair_budget=max(0, int(repair_budget)),
    )
    repaired: list[_Candidate] = []
    failures: Counter[str] = Counter()
    mutation_issue_counts: Counter[str] = Counter()
    compilation_issue_counts: Counter[str] = Counter()
    compilation_issue_detail_counts: Counter[str] = Counter()
    authored_failure_counts: Counter[str] = Counter()
    failure_records: list[dict[str, Any]] = []
    counts = {
        "schema_version": "arr.maas.exact_post_book_typed_repair.v1",
        "requested_count": len(candidates),
        "requested_llm_authored_count": sum(_llm_authored_candidate(candidate) for candidate in candidates),
        "mutation_revised_count": 0,
        "geometry_changed_count": 0,
        "source_materialized_count": 0,
        "clean_mass_pass_count": 0,
        "program_hard_pass_count": 0,
        "repaired_candidate_count": 0,
        "repair_budget": max(0, int(repair_budget)),
        "same_final_ast_edited": True,
        "book_reprojection_applied": False,
        "synthetic_fallback_used": False,
        "compiler_safe_recovery_count": 0,
        "compiler_safe_rejected_group_count": 0,
        "floorwise_legal_reprojection_count": 0,
    }
    site_access_context = dict(site_access_context or {})
    for candidate in candidates:
        record = records[candidate.sequence.name]
        try:
            parent_program = GeometryProgram.from_dict(candidate.source.metadata["geometry_program"])
        except (TypeError, ValueError):
            failures["invalid_parent_geometry_program"] += 1
            continue
        safe_mutation = apply_geometry_edits_compiler_safe(
            parent_program,
            record["geometry_edits"],
        )
        mutation = safe_mutation.mutation
        if safe_mutation.recovery_mode == "atomic_group_recovery":
            counts["compiler_safe_recovery_count"] += 1
        counts["compiler_safe_rejected_group_count"] += len(safe_mutation.rejected_groups)
        if mutation.status != "revised" or mutation.program is None:
            failures[f"mutation_{mutation.status}"] += 1
            for issue in mutation.issues:
                mutation_issue_counts[str(issue.code or "unknown")] += 1
            if _llm_authored_candidate(candidate):
                authored_failure_counts[f"mutation_{mutation.status}"] += 1
            failure_records.append({
                "source_sequence": candidate.sequence.name,
                "geometry_family": _geometry_program_family(candidate),
                "llm_authored_lane": _llm_authored_candidate(candidate),
                "stage": "typed_mutation",
                "status": mutation.status,
                "issues": [issue.to_dict() for issue in mutation.issues],
                "compiler_safe_recovery_mode": safe_mutation.recovery_mode,
                "compiler_safe_rejected_groups": list(safe_mutation.rejected_groups),
            })
            continue
        counts["mutation_revised_count"] += 1
        parent_compilation = compile_geometry_program(parent_program)
        repaired_program = replace(
            mutation.program,
            name=f"{mutation.program.name}__final_vlm_repair",
            metadata={
                **dict(mutation.program.metadata),
                "final_vlm_repair": {
                    "schema_version": "arr.maas.final_vlm_typed_repair_lineage.v1",
                    "parent_program_hash": parent_program.program_hash(),
                    "parent_geometry_hash": parent_compilation.geometry_hash,
                    "critic_response_id": str(record.get("response_id") or ""),
                    "edit_count": len(record.get("geometry_edits") or ()),
                    "source_sequence": candidate.sequence.name,
                },
            },
        )
        # The safe mutation compiled the same nodes before lineage metadata and
        # name were added. Recompile the exact persisted AST so the evidence
        # always belongs to the artifact sent downstream.
        repaired_compilation = compile_geometry_program(repaired_program)
        if repaired_compilation.status != "compiled":
            failures["repaired_program_compile_failed"] += 1
            for issue in repaired_compilation.issues:
                compilation_issue_counts[str(issue.code or "unknown")] += 1
                compilation_issue_detail_counts[
                    f"{issue.code}:{issue.node_id}:{str(issue.message)[:160]}"
                ] += 1
            if _llm_authored_candidate(candidate):
                authored_failure_counts["repaired_program_compile_failed"] += 1
            failure_records.append({
                "source_sequence": candidate.sequence.name,
                "geometry_family": _geometry_program_family(candidate),
                "llm_authored_lane": _llm_authored_candidate(candidate),
                "stage": "repaired_program_compile",
                "status": repaired_compilation.status,
                "issues": [issue.to_dict() for issue in repaired_compilation.issues],
                "typed_ast": {
                    "name": repaired_program.name,
                    "root_id": repaired_program.root_id,
                    "nodes": [node.to_dict() for node in repaired_program.topological_nodes()],
                    "contains_parcel_coordinates": False,
                    "contains_mesh_payload": False,
                },
            })
            continue
        if repaired_compilation.geometry_hash == parent_compilation.geometry_hash:
            failures["typed_edit_did_not_change_geometry"] += 1
            continue
        counts["geometry_changed_count"] += 1

        legal_generation = candidate.source.metadata.get("legal_generation_context_evidence") or {}
        host_mode = str(legal_generation.get("generation_host_mode") or "horizontal_buildable_envelope")
        compile_site = generation_site
        if host_mode == "height_safe_sunlight_section" and generation_context is not None:
            height_safe = generation_site_at_height(generation_context, height * (2.0 / 3.0))
            if height_safe is not None:
                compile_site = height_safe
        base_source = compile_sequence_to_source_mass(compile_site, candidate.sequence)
        if base_source is None:
            failures["program_sequence_recompile_failed"] += 1
            continue
        bridge = candidate.source.metadata.get("geometry_program_bridge_evidence") or {}
        parent_capacity_alternative = deepcopy(
            candidate.source.metadata.get("capacity_alternative_projection") or {}
        )
        alternative_capacity_contract = capacity_contract_for_alternative(
            base_capacity_contract,
            parent_capacity_alternative,
        )
        try:
            fit_strength = max(0.0, min(1.0, float(bridge.get("legal_fit_strength") or 0.0)))
        except (TypeError, ValueError):
            fit_strength = 0.0
        source = replace_source_dominant_with_geometry_program(
            base_source,
            repaired_program,
            containment_host=compile_site,
            upper_containment_host=(
                generation_site_at_height(generation_context, height)
                if generation_context is not None
                else None
            ),
            upper_fit_strength=fit_strength,
            minimum_host_plan_coverage=recursive_plan_coverage_floor(
                building_type,
                alternative_capacity_contract,
                host_area_m2=float(compile_site.area),
            ),
        )
        if source is None:
            failures["repaired_source_materialization_failed"] += 1
            continue
        counts["source_materialized_count"] += 1
        program_context = {
            **program_reference_contract(building_type),
            "program_dimensional_context": dict(program_dimensional_context or {}),
            "base_capacity_contract": dict(base_capacity_contract or {}),
            "site_boundary_source": site_boundary_source,
            "site_access_context": site_access_context,
            "site_access_side_in_program_frame": _site_access_side_in_principal_frame(
                generation_site,
                site_access_geometry,
            ),
            "program_space_zones": deepcopy(source.metadata.get("program_space_zones") or []),
        }
        metadata = deepcopy(source.metadata)
        metadata["program_dimensional_context"] = deepcopy(program_dimensional_context or {})
        metadata["program_context"] = program_context
        metadata["geometry_graph_notes"] = build_geometry_graph_notes(
            repaired_program,
            repaired_compilation,
        )
        metadata["geometry_graph_snapshot"] = build_geometry_graph_snapshot(
            repaired_program,
            repaired_compilation,
            program_context=program_context,
        )
        metadata["legal_generation_context_evidence"] = deepcopy(legal_generation)
        metadata["base_capacity_contract"] = deepcopy(base_capacity_contract or {})
        metadata["capacity_alternative_projection"] = parent_capacity_alternative
        metadata["final_vlm_repair_parent_audit"] = deepcopy(record)
        repaired_bridge = deepcopy(metadata.get("geometry_program_bridge_evidence") or {})
        repaired_bridge.update({
            "source_seed": str((bridge or {}).get("source_seed") or ""),
            "legal_fit_strength": round(fit_strength, 4),
            "repair_stage": "exact_post_book_vlm_typed_edit",
            "parent_geometry_hash": parent_compilation.geometry_hash,
        })
        metadata["geometry_program_bridge_evidence"] = repaired_bridge
        source = replace(source, metadata=metadata)
        if generation_context is not None:
            legal_sections = tuple(
                generation_site_at_height(
                    generation_context,
                    float(height) * floor_number / max(1, int(floors)),
                )
                for floor_number in range(1, max(1, int(floors)) + 1)
            )
            if any(section is None for section in legal_sections):
                failures["repaired_floorwise_legal_section_missing"] += 1
                continue
            parent_floorwise_stack = candidate.source.metadata.get(
                "floorwise_legal_matrix_stack"
            )
            parent_floorwise_stack = (
                parent_floorwise_stack
                if isinstance(parent_floorwise_stack, dict)
                else {}
            )
            try:
                target_plan_coverage = float(
                    parent_floorwise_stack.get("target_plan_coverage")
                    or parent_capacity_alternative.get("target_base_plan_coverage")
                    or recursive_plan_coverage_floor(
                        building_type,
                        alternative_capacity_contract,
                        host_area_m2=float(compile_site.area),
                    )
                )
            except (TypeError, ValueError):
                failures["repaired_floorwise_target_coverage_invalid"] += 1
                continue
            floorwise_source = materialize_floorwise_legal_source(
                source,
                legal_sections=legal_sections,
                target_plan_coverage=target_plan_coverage,
                floor_capacity_plan_hash=str(
                    parent_floorwise_stack.get("floor_capacity_plan_hash")
                    or (base_capacity_contract or {}).get(
                        "floor_capacity_plan_hash"
                    )
                    or ""
                ),
                target_floor_areas_m2=tuple(
                    float(value)
                    for value in (
                        parent_floorwise_stack.get("target_floor_areas_m2")
                        or (base_capacity_contract or {}).get(
                            "target_floor_areas_m2"
                        )
                        or ()
                    )
                ),
            )
            if floorwise_source is None:
                failures["repaired_floorwise_legal_reprojection_failed"] += 1
                continue
            source = floorwise_source
            counts["floorwise_legal_reprojection_count"] += 1
        shared_floor_contract = _materialize_repaired_floor_contract(
            source,
            generation_context=generation_context,
            capacity_site=capacity_site,
            height=height,
            floors=floors,
            base_capacity_contract=base_capacity_contract,
            repaired_program=repaired_program,
            repaired_compilation=repaired_compilation,
        )
        if shared_floor_contract is not None:
            metadata = deepcopy(source.metadata)
            metadata["shared_floor_contract"] = shared_floor_contract
            source = replace(source, metadata=metadata)
            if not shared_floor_contract.get("hard_pass"):
                failures.update(
                    f"shared_floor_{reason}"
                    for reason in shared_floor_contract.get("failure_reasons") or (
                        "hard_gate_failed",
                    )
                )
                continue
        capacity_measurement: dict[str, Any] = {}
        if base_capacity_contract and capacity_site is not None:
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
                parent_capacity_alternative,
                capacity_measurement,
            )
            if (
                shared_floor_contract is not None
                and shared_floor_contract.get("schema_version")
                == "arr.maas.shared_floor_contract.v1"
            ):
                shared_floor_contract = bind_shared_floor_contract_capacity(
                    shared_floor_contract,
                    metadata["capacity_alternative_projection"],
                )
                metadata["shared_floor_contract"] = shared_floor_contract
            source = replace(source, metadata=metadata)
        clean_pass, clean_evidence = _clean_mass_gate(source)
        if not clean_pass:
            failures.update(f"clean_{reason}" for reason in clean_evidence.get("failure_reasons") or ())
            continue
        if not _inside_site(source, compile_site):
            failures["containment_failed"] += 1
            continue
        counts["clean_mass_pass_count"] += 1
        repair_sequence = replace(
            candidate.sequence,
            name=f"{candidate.sequence.name}__final_vlm_repair",
            label=f"{candidate.sequence.label} · final VLM typed repair",
            notes=tuple((*candidate.sequence.notes,
                f"final_vlm_typed_repair_response={str(record.get('response_id') or '')}",
                f"final_vlm_typed_repair_parent_geometry={parent_compilation.geometry_hash}",
                "final_vlm_typed_repair_book_reprojection=false",
            )),
        )
        feature = source_feature(
            source,
            repair_sequence,
            building_type=building_type,
            height=height,
            floors=floors,
            site_area=float(compile_site.area),
        )
        props = feature.setdefault("properties", {})
        props.update({
            "site_boundary_geometry": mapping(generation_site),
            "site_boundary_source": site_boundary_source,
            "site_access_context": site_access_context,
            "site_access_geometry": site_access_geometry,
            "program_context": program_context,
            "geometry_program": deepcopy(source.metadata.get("geometry_program") or {}),
            "geometry_graph_notes": deepcopy(source.metadata.get("geometry_graph_notes") or []),
            "geometry_graph_snapshot": deepcopy(source.metadata.get("geometry_graph_snapshot") or {}),
            "base_capacity_contract": deepcopy(base_capacity_contract or {}),
            "source_capacity_measurement": deepcopy(capacity_measurement),
            "capacity_alternative_projection": deepcopy(
                source.metadata.get("capacity_alternative_projection") or {}
            ),
        })
        program = attach_program_massing_evidence(feature, building_type=building_type)
        program_form = _program_form_gate(source, building_type)
        feature["properties"]["program_form_gate"] = program_form
        if not (program.get("hard_pass") and program_form.get("hard_pass")):
            failures["program_hard_gate_failed"] += 1
            continue
        counts["program_hard_pass_count"] += 1
        spatial = feature["properties"]["program_spatial_evidence"]
        if capacity_measurement:
            capacity_score = capacity_fit_score(
                source.metadata.get("capacity_alternative_projection") or {},
                capacity_measurement,
            )
            score = (
                float(program["program_fit_score"]) * 0.40
                + float(spatial["architectural_score"]) * 0.30
                + capacity_score * 0.30
            )
        else:
            score = float(program["program_fit_score"]) * 0.56 + float(spatial["architectural_score"]) * 0.44
        repaired.append(_Candidate(
            candidate.principle_id,
            candidate.principle_kind,
            candidate.operation,
            repair_sequence,
            source,
            feature,
            round(score, 6),
        ))
    counts["repaired_candidate_count"] = len(repaired)
    counts["repaired_llm_authored_count"] = sum(_llm_authored_candidate(candidate) for candidate in repaired)
    counts["failure_counts"] = dict(sorted(failures.items()))
    counts["mutation_issue_counts"] = dict(sorted(mutation_issue_counts.items()))
    counts["compilation_issue_counts"] = dict(sorted(compilation_issue_counts.items()))
    counts["compilation_issue_detail_counts"] = dict(sorted(compilation_issue_detail_counts.items()))
    counts["llm_authored_failure_counts"] = dict(sorted(authored_failure_counts.items()))
    counts["failure_records"] = failure_records
    return repaired, counts


def _exact_post_book_repair_shortlist(
    candidates: list[_Candidate],
    records: dict[str, dict[str, Any]],
    *,
    repair_budget: int,
) -> list[_Candidate]:
    """Allocate repair bandwidth from exact VLM evidence, not proxy score.

    The previous implementation sorted only by the pre-VLM procedural score.
    That discarded nearly all typed LLM candidates even when the exact critic
    gave them one localized, executable repair.  This reservation changes only
    which failed ASTs are repaired; it grants no selection preference and all
    repaired solids still repeat every hard gate and exact VLM review.
    """
    budget = max(0, int(repair_budget))
    if not candidates or budget <= 0:
        return []

    def priority(candidate: _Candidate) -> tuple[float, ...]:
        record = records.get(candidate.sequence.name) or {}
        scores = record.get("concept_scores") if isinstance(record.get("concept_scores"), dict) else {}
        failures = list(record.get("failures") or ())
        visual_mean = sum(float(scores.get(key) or 0.0) for key in (
            "gesture_clarity", "hierarchy", "repair_integrity",
            "program_appropriateness", "void_publicness", "section_program_fit",
        )) / 6.0
        program_fit = "final_book_program_fit_failed" not in failures
        return (
            float(program_fit),
            -float(len(failures)),
            float(scores.get("repair_integrity") or 0.0),
            visual_mean,
            float(candidate.score),
        )

    ranked = sorted(candidates, key=priority, reverse=True)
    authored = [candidate for candidate in ranked if _llm_authored_candidate(candidate)]
    authored_quota = min(len(authored), max(4, budget // 3), budget)
    chosen = authored[:authored_quota]
    chosen_ids = {id(candidate) for candidate in chosen}
    for candidate in ranked:
        if len(chosen) >= budget:
            break
        if id(candidate) in chosen_ids:
            continue
        chosen.append(candidate)
        chosen_ids.add(id(candidate))
    return chosen



__all__ = ["_final_book_vlm_hard_pass","_final_book_vlm_shortlist","_audit_final_book_geometry_with_vlm","audit_book_base_stage_with_vlm","_repair_exact_post_book_candidates_from_vlm","_exact_post_book_repair_shortlist"]
