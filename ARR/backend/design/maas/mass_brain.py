"""Fail-open shadow bridge from ARR's Python mass generator to Mass-Brain/GRL."""

from __future__ import annotations

import os
import re
import uuid
import json
from dataclasses import dataclass, replace
from itertools import combinations
from typing import Any, Callable, Iterable

import httpx

from design import config
from design.maas.grammar.component_graph import graph_from_sequence
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.grammar.vocab import SUPPORTED_VERBS
from design.maas.morphology_operators import MorphologyVariant
from design.maas.mass_brain_relation_profile import (
    relation_profile_from_feature,
    relation_profile_from_sequence,
    site_aspect_bucket,
)


InterpretSequence = Callable[[Any, VerbSequence], MorphologyVariant | None]


@dataclass(frozen=True)
class MassBrainShadowBatch:
    variants: tuple[MorphologyVariant, ...]
    proposals_by_operator: dict[str, dict[str, Any]]
    artifact: dict[str, Any]


@dataclass(frozen=True)
class MassBrainSequenceBatch:
    sequences: tuple[VerbSequence, ...]
    proposals_by_sequence: dict[str, dict[str, Any]]
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
    program_type: str | None = None,
) -> MassBrainShadowBatch:
    settings = mass_brain_config(parking_options)
    if not settings["enabled"]:
        return MassBrainShadowBatch((), {}, {"schema_version": "arr.maas.mass_brain_shadow.v1", "status": "disabled"})
    source_variants = list(source_variants)
    sequences = _unique_sequences(source_variants)
    if len(sequences) < 2:
        return MassBrainShadowBatch((), {}, {"schema_version": "arr.maas.mass_brain_shadow.v1", "status": "insufficient_sources", "source_count": len(sequences)})
    signatures = {
        variant.operator: dict(variant.source_signature)
        for variant in source_variants
        if isinstance(variant.source_signature, dict)
    }
    context = {
        "programType": str(program_type or "unknown"),
        "siteAspectBucket": site_aspect_bucket(base_footprint),
    }
    envelope = _build_envelope(project_key, sequences, source_signatures=signatures, context=context)
    run_id = str(uuid.uuid4())
    payload, error = _request_proposals(envelope, project_key=project_key, settings=settings)
    if error:
        return MassBrainShadowBatch((), {}, {
            "schema_version": "arr.maas.mass_brain_shadow.v1",
            "status": "unavailable_fail_open",
            "error": error,
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


def request_shadow_sequences(
    *,
    source_sequences: Iterable[VerbSequence],
    project_key: str,
    program_type: str,
    site_aspect: str,
    parking_options: dict[str, Any] | None = None,
) -> MassBrainSequenceBatch:
    """Request graph-memory variants without coupling to legal geometry.

    Program-massing/VLM loops use this lane to score Mass-Brain proposals as
    shadow evidence. They are not admitted to the final archive unless the
    service's separate promotion contract is active.
    """
    settings = mass_brain_config(parking_options)
    if not settings["enabled"]:
        return MassBrainSequenceBatch((), {}, {"schema_version": "arr.maas.mass_brain_shadow.v1", "status": "disabled"})
    sequences = _unique_verb_sequences(source_sequences)
    if len(sequences) < 2:
        return MassBrainSequenceBatch((), {}, {
            "schema_version": "arr.maas.mass_brain_shadow.v1",
            "status": "insufficient_sources",
            "source_count": len(sequences),
        })
    envelope = _build_envelope(
        project_key,
        sequences,
        context={"programType": program_type, "siteAspectBucket": site_aspect},
    )
    payload, error = _request_proposals(envelope, project_key=project_key, settings=settings)
    if error:
        return MassBrainSequenceBatch((), {}, {
            "schema_version": "arr.maas.mass_brain_shadow.v1",
            "status": "unavailable_fail_open",
            "error": error,
        })
    compiled: list[VerbSequence] = []
    proposals: dict[str, dict[str, Any]] = {}
    for proposal in payload.get("proposals") or []:
        if not isinstance(proposal, dict) or proposal.get("lane") != "executable":
            continue
        sequence = _sequence_from_proposal(proposal)
        if sequence is None:
            continue
        sequence = VerbSequence(
            name=sequence.name,
            label=sequence.label,
            calls=sequence.calls,
            notes=sequence.notes + (
                "proposal_source=mass_brain_shadow",
                f"mass_brain_proposal_id={proposal.get('proposalId')}",
            ),
        )
        compiled.append(sequence)
        proposals[sequence.name] = proposal
    return MassBrainSequenceBatch(tuple(compiled), proposals, {
        "schema_version": "arr.maas.mass_brain_shadow.v1",
        "status": "shadow_sequences_generated",
        "project_key": project_key,
        "source_count": len(sequences),
        "proposal_count": len(payload.get("proposals") or []),
        "compiled_count": len(compiled),
        "assistant_status": payload.get("assistantStatus"),
        "rollout": payload.get("rollout") if isinstance(payload.get("rollout"), dict) else {"mode": "shadow", "slots": 0},
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
        relation_profile = relation_profile_from_feature(feature)
        clean_mass_passed = _clean_mass_pass(relation_profile)
        payload = {
            "projectKey": project_key,
            "proposalId": proposal.get("proposalId"),
            "runId": f"{run_id}:{proposal.get('proposalId')}" if run_id else None,
            "compilePassed": True,
            "legalPassed": feature is not None,
            "parkingPassed": bool(layout.get("status") == "pass"),
            "geometryPassed": bool(feature and feature.get("geometry") and clean_mass_passed),
            "designQuality": _score01(design_quality.get("score") or design_quality.get("overall")),
            "novelty": _score01((proposal.get("scoreBreakdown") or {}).get("novelty")),
            "vlmScore": _score01(preference.get("distilled_preference_score")),
            "evidenceScore": _score01((proposal.get("scoreBreakdown") or {}).get("evidence")),
            "details": {
                "operator": operator,
                "shadow": True,
                "relationProfile": relation_profile,
                "cleanMassPassed": clean_mass_passed,
                "farUtilization": _score01(props.get("far_utilization")),
                "bcrUtilization": _score01(props.get("bcr_utilization")),
            },
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


def _build_envelope(
    project_key: str,
    sequences: list[VerbSequence],
    *,
    source_signatures: dict[str, dict[str, Any]] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
        relation_profile = relation_profile_from_sequence(
            sequence.calls,
            source_signature=(source_signatures or {}).get(sequence.name),
        )
        payloads[feature_id] = {
            "family": family,
            "relationProfile": relation_profile,
            "context": dict(context or {}),
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
    seen: set[tuple[tuple[str, str], ...]] = set()
    for variant in variants:
        raw = variant.verb_sequence or ()
        calls = tuple(VerbCall(str(item.get("verb") or ""), dict(item.get("params") or {})) for item in raw if isinstance(item, dict))
        if not calls:
            continue
        sequence = VerbSequence(variant.operator, variant.operator.replace("_", " "), calls, variant.notes)
        signature = _sequence_signature(calls)
        if signature in seen or sequence.validate():
            continue
        seen.add(signature)
        result.append(sequence)
    return result[:32]


def _unique_verb_sequences(sequences: Iterable[VerbSequence]) -> list[VerbSequence]:
    result: list[VerbSequence] = []
    seen: set[tuple[tuple[str, str], ...]] = set()
    for sequence in sequences:
        signature = _sequence_signature(sequence.calls)
        if not sequence.calls or signature in seen or sequence.validate():
            continue
        seen.add(signature)
        result.append(sequence)
    return result[:64]


def _sequence_signature(calls: Iterable[VerbCall]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (call.verb, json.dumps(call.params, ensure_ascii=False, sort_keys=True, default=str))
        for call in calls
    )


def _request_proposals(
    envelope: dict[str, Any],
    *,
    project_key: str,
    settings: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
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
        return (payload if isinstance(payload, dict) else {}), None
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        return {}, str(exc)


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


def _clean_mass_pass(profile: dict[str, Any]) -> bool:
    """Keep weak learning behind the same clean-mass limits as visual review."""
    surface_count = int(profile.get("surfaceCount") or 0)
    return bool(
        surface_count > 0
        and surface_count <= 48
        and int(profile.get("componentCount") or 0) <= 5
        and int(profile.get("smallFragmentCount") or 0) <= 1
        and float(profile.get("primaryEnvelopeRetention") or 0.0) >= 0.55
        and int(profile.get("dominantOperationCount") or 0) <= 3
    )


__all__ = [
    "MassBrainSequenceBatch",
    "MassBrainShadowBatch",
    "mass_brain_config",
    "record_shadow_outcomes",
    "record_proposal_feedback",
    "request_shadow_sequences",
    "request_shadow_variants",
]
