"""Fail-open shadow bridge from ARR's Python mass generator to Mass-Brain/GRL."""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass, replace
from itertools import combinations
from typing import Any, Callable, Iterable

import httpx

from design import config
from design.maas.grammar.component_graph import graph_from_sequence
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.grammar.vocab import SUPPORTED_VERBS
from design.maas.morphology_operators import MorphologyVariant


InterpretSequence = Callable[[Any, VerbSequence], MorphologyVariant | None]


@dataclass(frozen=True)
class MassBrainShadowBatch:
    variants: tuple[MorphologyVariant, ...]
    proposals_by_operator: dict[str, dict[str, Any]]
    artifact: dict[str, Any]


def mass_brain_config(parking_options: dict[str, Any] | None) -> dict[str, Any]:
    options = parking_options or {}
    raw = options.get("mass_brain") if isinstance(options.get("mass_brain"), dict) else {}
    env_enabled = os.getenv("MASS_BRAIN_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
    return {
        "enabled": bool(raw.get("enabled", env_enabled)),
        "count": max(1, min(40, int(raw.get("count") or 12))),
        "seed": int(raw.get("seed") or 20260713),
        "include_experimental": bool(raw.get("include_experimental", True)),
    }


def request_shadow_variants(
    *,
    base_footprint: Any,
    source_variants: Iterable[MorphologyVariant],
    project_key: str,
    interpret: InterpretSequence,
    parking_options: dict[str, Any] | None = None,
) -> MassBrainShadowBatch:
    settings = mass_brain_config(parking_options)
    if not settings["enabled"]:
        return MassBrainShadowBatch((), {}, {"schema_version": "arr.maas.mass_brain_shadow.v1", "status": "disabled"})
    sequences = _unique_sequences(source_variants)
    if len(sequences) < 2:
        return MassBrainShadowBatch((), {}, {"schema_version": "arr.maas.mass_brain_shadow.v1", "status": "insufficient_sources", "source_count": len(sequences)})
    envelope = _build_envelope(project_key, sequences)
    run_id = str(uuid.uuid4())
    try:
        ingest_response = config.mass_brain_client.post("/v1/contracts/ingest", json=envelope)
        ingest_response.raise_for_status()
        proposal_response = config.mass_brain_client.post("/v1/proposals/generate", json={
            "projectKey": project_key,
            "count": settings["count"],
            "seed": settings["seed"],
            "includeExperimental": settings["include_experimental"],
            "registeredVerbs": sorted(SUPPORTED_VERBS),
        })
        proposal_response.raise_for_status()
        payload = proposal_response.json()
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        return MassBrainShadowBatch((), {}, {
            "schema_version": "arr.maas.mass_brain_shadow.v1",
            "status": "unavailable_fail_open",
            "error": str(exc),
        })
    compiled: list[MorphologyVariant] = []
    proposals_by_operator: dict[str, dict[str, Any]] = {}
    experimental_count = 0
    compile_rejected = 0
    for proposal in payload.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        if proposal.get("lane") != "executable":
            experimental_count += int(proposal.get("lane") == "experimental")
            continue
        sequence = _sequence_from_proposal(proposal)
        if sequence is None:
            compile_rejected += 1
            continue
        variant = interpret(base_footprint, sequence)
        if variant is None:
            compile_rejected += 1
            continue
        operator = f"mass_brain_shadow_{_safe_id(str(proposal.get('proposalId') or sequence.name))}"
        variant = replace(
            variant,
            operator=operator,
            notes=variant.notes + (
                "proposal_source=mass_brain_shadow",
                f"mass_brain_proposal_id={proposal.get('proposalId')}",
            ),
        )
        compiled.append(variant)
        proposals_by_operator[operator] = proposal
    return MassBrainShadowBatch(tuple(compiled), proposals_by_operator, {
        "schema_version": "arr.maas.mass_brain_shadow.v1",
        "status": "shadow_generated",
        "project_key": project_key,
        "run_id": run_id,
        "source_count": len(sequences),
        "proposal_count": len(payload.get("proposals") or []),
        "compiled_count": len(compiled),
        "experimental_count": experimental_count,
        "compile_rejected_count": compile_rejected,
        "assistant_status": payload.get("assistantStatus"),
        "rollout": payload.get("rollout") if isinstance(payload.get("rollout"), dict) else {"mode": "shadow", "slots": 0},
        "selection_effect": "none_shadow_only",
    })


def record_shadow_outcomes(
    *,
    project_key: str,
    proposals_by_operator: dict[str, dict[str, Any]],
    features_by_operator: dict[str, dict[str, Any]],
    run_id: str | None = None,
    comparisons_by_operator: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    recorded = 0
    failed = 0
    for operator, proposal in proposals_by_operator.items():
        feature = features_by_operator.get(operator)
        props = feature.get("properties") if isinstance(feature, dict) and isinstance(feature.get("properties"), dict) else {}
        parking = props.get("parking_precheck") if isinstance(props.get("parking_precheck"), dict) else {}
        layout = parking.get("layout") if isinstance(parking.get("layout"), dict) else {}
        design_quality = props.get("design_quality") if isinstance(props.get("design_quality"), dict) else {}
        preference = props.get("preference_distillation") if isinstance(props.get("preference_distillation"), dict) else {}
        payload = {
            "projectKey": project_key,
            "proposalId": proposal.get("proposalId"),
            "runId": f"{run_id}:{proposal.get('proposalId')}" if run_id else None,
            "compilePassed": True,
            "legalPassed": feature is not None,
            "parkingPassed": bool(layout.get("status") == "pass"),
            "geometryPassed": bool(feature and feature.get("geometry")),
            "designQuality": _score01(design_quality.get("score") or design_quality.get("overall")),
            "novelty": _score01((proposal.get("scoreBreakdown") or {}).get("novelty")),
            "vlmScore": _score01(preference.get("distilled_preference_score")),
            "evidenceScore": _score01((proposal.get("scoreBreakdown") or {}).get("evidence")),
            "details": {"operator": operator, "shadow": True},
        }
        comparison = (comparisons_by_operator or {}).get(operator)
        if isinstance(comparison, dict) and comparison.get("comparison_id"):
            payload.update({
                "comparisonId": str(comparison["comparison_id"]),
                "blindVlmWon": bool(comparison.get("blind_vlm_won")),
                "baselineHardPassed": bool(comparison.get("baseline_hard_passed")),
            })
        try:
            response = config.mass_brain_client.post("/v1/outcomes", json=payload)
            response.raise_for_status()
            recorded += 1
        except (httpx.HTTPError, ValueError, TypeError):
            failed += 1
    return {"recorded_count": recorded, "failed_count": failed}


def record_proposal_feedback(
    *,
    project_key: str,
    proposal_id: str,
    feedback_id: str,
    decision: str,
    rating: float | None = None,
    note: str = "",
) -> dict[str, Any]:
    """Forward an ARR decision without making the ARR request depend on the service."""
    payload = {
        "projectKey": project_key,
        "proposalId": proposal_id,
        "feedbackId": feedback_id,
        "decision": decision,
        "note": note,
    }
    if rating is not None:
        payload["rating"] = rating
    try:
        response = config.mass_brain_client.post("/v1/feedback", json=payload)
        response.raise_for_status()
        return {"status": "recorded", "response": response.json()}
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        return {"status": "unavailable_fail_open", "error": str(exc)}


def _build_envelope(project_key: str, sequences: list[VerbSequence]) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    payloads: dict[str, Any] = {}
    feature_ids: list[str] = []
    for index, sequence in enumerate(sequences):
        feature_id = f"feature:arr-seed:{_safe_id(sequence.name)}"
        evidence_id = f"evidence:arr-seed:{_safe_id(sequence.name)}"
        feature_ids.append(feature_id)
        family = _family(sequence)
        features.append({
            "id": feature_id,
            "label": sequence.label or sequence.name,
            "kind": "massdsl_seed",
            "confidence": 0.82,
            "pipelineStage": "seed_generation",
            "evidenceDensity": max(1, len(sequence.notes)),
            "metadata": {"family": family, "operator": sequence.name},
        })
        evidence.append({
            "id": evidence_id,
            "featureId": feature_id,
            "sourcePath": "ARR/design/maas",
            "excerpt": "; ".join(sequence.notes[:4]) or f"ARR executable MassDSL seed {sequence.name}",
            "evidenceType": "generator_trace",
            "confidence": 0.8,
        })
        component = graph_from_sequence(sequence).to_dict()
        payloads[feature_id] = {
            "family": family,
            "componentGraph": {
                "name": component["name"],
                "label": component["label"],
                "nodes": [
                    {
                        "nodeId": node["node_id"],
                        "role": node["role"],
                        "parentId": node["parent_id"],
                        "optional": node["optional"],
                        "operation": node["operation"],
                    }
                    for node in component["nodes"]
                ],
            },
        }
    circuits = []
    relations = []
    for index, (source, target) in enumerate(combinations(feature_ids, 2)):
        source_sequence = sequences[feature_ids.index(source)]
        target_sequence = sequences[feature_ids.index(target)]
        confidence = 0.9 if _family(source_sequence) != _family(target_sequence) else 0.68
        circuits.append({
            "id": f"circuit:arr-seed:{index}",
            "sourceFeatureId": source,
            "targetFeatureId": target,
            "type": "contrasts" if confidence > 0.8 else "same_family",
            "confidence": confidence,
            "evidenceDensity": 2,
            "edgeWeight": 1.2 if confidence > 0.8 else 0.7,
            "evidenceIds": [f"evidence:arr-seed:{_safe_id(source_sequence.name)}", f"evidence:arr-seed:{_safe_id(target_sequence.name)}"],
        })
        relations.append({
            "id": f"relation:arr-seed:{index}",
            "sourceNodeId": source,
            "targetNodeId": target,
            "type": "recombination_candidate",
            "confidence": confidence,
            "evidenceIds": [],
            "metadata": {"source": "arr_massdsl"},
        })
    return {
        "schemaVersion": "mass-brain/v1",
        "projectKey": project_key,
        "contract": {
            "schemaVersion": "grl/v1",
            "dataset": {"id": project_key, "title": f"ARR Mass Brain {project_key}", "source": "ARR/design/maas"},
            "stages": [{"id": "seed_generation", "label": "Seed Generation"}],
            "features": features,
            "evidence": evidence,
            "circuits": circuits,
            "relations": relations,
            "queryHints": ["Find structurally distant executable MassDSL seeds"],
        },
        "domainPayloads": payloads,
    }


def _sequence_from_proposal(proposal: dict[str, Any]) -> VerbSequence | None:
    graph = proposal.get("componentGraph") if isinstance(proposal.get("componentGraph"), dict) else None
    nodes = graph.get("nodes") if isinstance(graph, dict) and isinstance(graph.get("nodes"), list) else []
    calls = tuple(
        VerbCall(str((node.get("operation") or {}).get("verb") or ""), dict((node.get("operation") or {}).get("params") or {}))
        for node in nodes if isinstance(node, dict) and isinstance(node.get("operation"), dict)
    )
    sequence = VerbSequence(
        name=f"mass_brain_{_safe_id(str(proposal.get('proposalId') or 'proposal'))}",
        label=str(graph.get("label") or "Mass-Brain shadow proposal") if isinstance(graph, dict) else "Mass-Brain shadow proposal",
        calls=calls,
        notes=(f"mass_brain_sources={','.join(str(item) for item in proposal.get('sourceNodeIds') or [])}",),
    )
    return None if sequence.validate() else sequence


def _unique_sequences(variants: Iterable[MorphologyVariant]) -> list[VerbSequence]:
    result: list[VerbSequence] = []
    seen: set[tuple[str, ...]] = set()
    for variant in variants:
        raw = variant.verb_sequence or ()
        calls = tuple(VerbCall(str(item.get("verb") or ""), dict(item.get("params") or {})) for item in raw if isinstance(item, dict))
        if not calls:
            continue
        sequence = VerbSequence(variant.operator, variant.operator.replace("_", " "), calls, variant.notes)
        signature = tuple(call.verb for call in calls)
        if signature in seen or sequence.validate():
            continue
        seen.add(signature)
        result.append(sequence)
    return result[:32]


def _family(sequence: VerbSequence) -> str:
    verbs = {call.verb for call in sequence.calls}
    for family, family_verbs in (
        ("court", {"courtyard", "cave", "notch", "pinch"}),
        ("connector", {"bridge", "diagonal_connect", "terrace_link", "interlock", "overlap"}),
        ("section", {"grade", "step_envelope", "sloped_roof_mass", "taper"}),
        ("bar", {"bar", "bend", "shift"}),
        ("cluster", {"branch", "split", "nest", "embed"}),
    ):
        if verbs & family_verbs:
            return family
    return "mass"


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")[:80] or "item"


def _score01(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0.0)))
    except (TypeError, ValueError):
        return 0.0


__all__ = [
    "MassBrainShadowBatch",
    "mass_brain_config",
    "record_shadow_outcomes",
    "record_proposal_feedback",
    "request_shadow_variants",
]
