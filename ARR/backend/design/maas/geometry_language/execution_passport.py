"""Facade and orchestration for auditable per-MASS execution passports."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from .execution_activation import append_vlm_nodes, build_activation_graph
from .execution_evidence import (
    DOWNSTREAM_ALIASES,
    DOWNSTREAM_STAGE_KEYS,
    normalize_downstream_evidence,
    passport_state,
    preview_evidence,
    stage,
    stage_from_downstream,
    status_activation,
    vlm_evidence,
)
from .execution_persistence import passport_path_for_preview, write_mass_execution_passport
from .gate import compilation_gate


MASS_EXECUTION_PASSPORT_SCHEMA = "arr.maas.mass_execution_passport.v1"


def build_mass_execution_passport(
    compilation: Any,
    *,
    preview_path: str | Path | None = None,
    vlm_result: Mapping[str, Any] | None = None,
    downstream_evidence: Mapping[str, Any] | None = None,
    geometry_gate_evidence: Mapping[str, Any] | None = None,
    agent_collaboration: Mapping[str, Any] | None = None,
    elevation_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one truthful passport from evidence materialized for this MASS."""

    program = compilation.program
    metadata = deepcopy(program.metadata or {})
    trace_by_id = {
        str(row.get("node_id") or ""): row
        for row in compilation.trace or ()
        if isinstance(row, dict)
    }
    measured_gate_issues = compilation_gate(compilation)
    gate_override = deepcopy(dict(geometry_gate_evidence or {}))
    gate_issues = () if gate_override.get("hard_pass") is True else measured_gate_issues
    program_issues = tuple(program.validate())
    preview = preview_evidence(preview_path)
    vlm = vlm_evidence(vlm_result)
    downstream = normalize_downstream_evidence(metadata, downstream_evidence)
    book_projection = metadata.get("book_recursive_projection")
    book_projection = book_projection if isinstance(book_projection, dict) else {}
    program_projection = metadata.get("program_projection")
    program_projection = program_projection if isinstance(program_projection, dict) else {}
    ordered_nodes = _safe_topological_nodes(program)
    base_nodes = [node for node in ordered_nodes if node.kind == "primitive" or node.semantic_role == "base_seed"]
    book_nodes = [node for node in ordered_nodes if str((node.provenance or {}).get("source") or "") == "book_recursive_projection"]
    program_nodes = [
        node for node in ordered_nodes
        if str((node.provenance or {}).get("source") or "")
        in {"post_book_program_projection", "program_projection_connectivity_guard"}
    ]
    stages: list[dict[str, Any]] = [
        stage("base_model", "Base Model", "passed" if base_nodes else "failed", node_ids=[node.id for node in base_nodes], evidence={"operators": [node.operator for node in base_nodes], "seed_family": str(metadata.get("base_seed_family") or "")}),
        stage("book_language", "BOOK geometry language", "evaluated" if book_projection.get("active") else "not_evaluated", node_ids=[node.id for node in book_nodes], evidence={"scope_label": str(book_projection.get("scope_label") or ""), "scope_fraction": book_projection.get("scope_fraction"), "ordered_verbs": list(book_projection.get("ordered_verbs") or ()), "application_order": str(book_projection.get("application_order") or "")}),
        stage("recursive_geometry", "Recursive Geometry AST", "passed" if not program_issues else "failed", node_ids=[node.id for node in ordered_nodes], evidence={
            "root_id": program.root_id,
            "node_count": len(program.nodes),
            "issues": [issue.to_dict() for issue in program_issues],
            "form_bank_lane": str(metadata.get("form_bank_lane") or ""),
            "form_bank_variation_page": int(metadata.get("form_bank_variation_page") or 0),
            "program_conditioned": bool(metadata.get("program_conditioned")),
        }),
        stage("program", "Use / program projection", "passed" if metadata.get("program_projection_applied") else "not_evaluated", node_ids=[node.id for node in program_nodes], evidence=program_projection),
    ]
    stages.extend(stage_from_downstream(key, downstream[key]) for key in ("site", "capacity", "law", "parking", "program_fit"))
    stages.extend((
        stage("compiler", "Geometry Compiler", "passed" if compilation.status == "compiled" else "failed", node_ids=list(trace_by_id), evidence={"status": compilation.status, "trace_count": len(compilation.trace or ()), "issues": [issue.to_dict() for issue in compilation.issues or ()]}),
        stage("geometry_gate", "Geometry GATE", "passed" if not gate_issues else "failed", evidence={
            "hard_pass": not gate_issues,
            "issues": [issue.to_dict() for issue in gate_issues],
            "metrics": deepcopy(compilation.metrics or {}),
            **gate_override,
        }),
        stage("render", "Four-view PNG", preview["status"], evidence=preview),
        stage("vlm", "VLM critic", vlm["status"], evidence=vlm),
        stage_from_downstream("selector", downstream["selector"]),
    ))
    collaboration = deepcopy(dict(agent_collaboration or {}))
    collaboration_status = str(collaboration.get("final_status") or "")
    stages.append(stage(
        "agent_collaboration",
        "Specialist agent collaboration",
        "passed" if collaboration_status == "accepted" else collaboration_status or "not_evaluated",
        evidence=collaboration,
    ))
    activation_graph = build_activation_graph(
        program=program,
        ordered_nodes=ordered_nodes,
        trace_by_id=trace_by_id,
        stages=stages,
        preview=preview,
        vlm=vlm,
        gate_issues=gate_issues,
        agent_collaboration=collaboration,
        geometry_hash=str(compilation.geometry_hash or ""),
        elevation_evidence=deepcopy(dict(elevation_evidence or {})),
    )
    state = passport_state(stages)
    return {
        "schema_version": MASS_EXECUTION_PASSPORT_SCHEMA,
        "mass_id": f"mass:{compilation.geometry_hash or _safe_program_hash(program)}",
        "program_name": program.name,
        "program_hash": _safe_program_hash(program),
        "structural_hash": _safe_structural_hash(program),
        "geometry_hash": str(compilation.geometry_hash or ""),
        **state,
        "truth_policy": {
            "unevaluated_is_never_pass": True,
            "execution_complete_is_not_acceptance": True,
            "internal_neuron_claim": False,
            "causal_program_trace": True,
            "visual_activation_uses_materialized_evidence_only": True,
        },
        "stages": stages,
        "activation_graph": activation_graph,
        "agent_collaboration": collaboration,
        "elevation_evidence": deepcopy(dict(elevation_evidence or {})),
    }


def enrich_mass_execution_passport(
    passport: Mapping[str, Any],
    *,
    downstream_evidence: Mapping[str, Any] | None = None,
    vlm_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach later site/capacity/law/parking/VLM facts without recompiling."""

    result = deepcopy(dict(passport))
    stages = result.get("stages")
    graph = result.get("activation_graph")
    if not isinstance(stages, list) or not isinstance(graph, dict):
        raise ValueError("invalid MASS execution passport")
    supplied = dict(downstream_evidence or {})
    updates = normalize_downstream_evidence({}, supplied)
    stage_map = {str(row.get("id") or ""): row for row in stages if isinstance(row, dict)}
    for stage_id in DOWNSTREAM_STAGE_KEYS:
        if stage_id in stage_map and any(key in supplied for key in DOWNSTREAM_ALIASES[stage_id]):
            stage_map[stage_id].update(stage_from_downstream(stage_id, updates[stage_id]))
    if vlm_result is not None and "vlm" in stage_map:
        vlm = vlm_evidence(vlm_result)
        stage_map["vlm"].update(stage("vlm", "VLM critic", vlm["status"], evidence=vlm))

    graph_nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
    graph_edges = graph.get("edges") if isinstance(graph.get("edges"), list) else []
    node_map = {str(node.get("id") or ""): node for node in graph_nodes if isinstance(node, dict)}
    for stage_id in (*DOWNSTREAM_STAGE_KEYS, "vlm"):
        row = stage_map.get(stage_id)
        node = node_map.get(f"flow:{stage_id}")
        if not row or not node:
            continue
        node["status"] = row["status"]
        node["activation"] = status_activation(row["status"])
        node["evidence"] = deepcopy(row.get("evidence") or {})
        for graph_edge in graph_edges:
            if isinstance(graph_edge, dict) and graph_edge.get("target") == node["id"]:
                graph_edge["activation"] = node["activation"]
    if vlm_result is not None:
        append_vlm_nodes(graph_nodes, graph_edges, vlm_evidence(vlm_result))
    result.update(passport_state(stages))
    return result


def _safe_topological_nodes(program: Any) -> tuple[Any, ...]:
    try:
        return tuple(program.topological_nodes())
    except ValueError:
        return tuple(program.nodes or ())


def _safe_program_hash(program: Any) -> str:
    try:
        return str(program.program_hash())
    except ValueError:
        return ""


def _safe_structural_hash(program: Any) -> str:
    try:
        return str(program.canonical_structure_hash())
    except ValueError:
        return ""


__all__ = [
    "MASS_EXECUTION_PASSPORT_SCHEMA",
    "build_mass_execution_passport",
    "enrich_mass_execution_passport",
    "passport_path_for_preview",
    "write_mass_execution_passport",
]
