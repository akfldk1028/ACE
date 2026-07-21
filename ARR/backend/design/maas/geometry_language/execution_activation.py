"""Build the observable causal graph for one MASS execution passport."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any, Mapping

from .execution_evidence import status_activation


def build_activation_graph(
    *,
    program: Any,
    ordered_nodes: tuple[Any, ...],
    trace_by_id: Mapping[str, Any],
    stages: list[dict[str, Any]],
    preview: Mapping[str, Any],
    vlm: Mapping[str, Any],
    gate_issues: tuple[Any, ...],
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    stage_by_id = {row["id"]: row for row in stages}
    for node in ordered_nodes:
        source = str((node.provenance or {}).get("source") or "")
        column = (
            "book" if source == "book_recursive_projection"
            else "program" if source in {"post_book_program_projection", "program_projection_connectivity_guard"}
            else "base" if node.kind == "primitive" or node.semantic_role == "base_seed"
            else "geometry"
        )
        evaluated = node.id in trace_by_id
        nodes.append({
            "id": f"ast:{node.id}",
            "source_id": node.id,
            "column": column,
            "label": str((node.provenance or {}).get("book_verb") or node.operator),
            "kind": node.kind,
            "operator": node.operator,
            "semantic_role": str(node.semantic_role or ""),
            "status": "evaluated" if evaluated else "failed",
            "activation": 1.0 if evaluated else 0.0,
            "evidence": deepcopy(trace_by_id.get(node.id) or {}),
        })
        for input_id in node.inputs:
            edges.append(edge(f"ast:{input_id}", f"ast:{node.id}", "solid_input", 1.0 if evaluated else 0.0))

    program_stage = stage_by_id["program"]
    nodes.append(flow_node("flow:program", "program", program_stage["label"], program_stage["status"], evidence=program_stage["evidence"]))
    if ordered_nodes:
        edges.append(edge(f"ast:{program.root_id}", "flow:program", "program_projection_result", status_activation(program_stage["status"])))
    compiler_status = stage_by_id["compiler"]["status"]
    nodes.append(flow_node("flow:compiler", "compiler", "Geometry Compiler", compiler_status))
    edges.append(edge("flow:program", "flow:compiler", "compile", 1.0 if compiler_status == "passed" else 0.0))
    gate_status = stage_by_id["geometry_gate"]["status"]
    nodes.append(flow_node("flow:geometry_gate", "gate", "Geometry GATE", gate_status, evidence={"issues": [issue.to_dict() for issue in gate_issues]}))
    edges.append(edge("flow:compiler", "flow:geometry_gate", "validate", 1.0 if gate_status == "passed" else 0.0))

    prior = "flow:geometry_gate"
    for stage_id in ("site", "capacity", "law", "parking", "program_fit"):
        row = stage_by_id[stage_id]
        node_id = f"flow:{stage_id}"
        nodes.append(flow_node(node_id, stage_id, row["label"], row["status"], evidence=row["evidence"]))
        edges.append(edge(prior, node_id, "downstream_gate", status_activation(row["status"])))
        prior = node_id

    render_status = stage_by_id["render"]["status"]
    nodes.append(flow_node("flow:render", "render", "4-view render", render_status, evidence=preview))
    edges.append(edge("flow:compiler", "flow:render", "render", status_activation(render_status)))
    for view in preview.get("views") or ("isometric", "opposite", "front", "top"):
        view_id = f"render:{view}"
        nodes.append(flow_node(view_id, "render", str(view), render_status))
        edges.append(edge("flow:render", view_id, "view", status_activation(render_status)))
    nodes.append({
        "id": "render:mass_png",
        "column": "render",
        "label": "Generated MASS PNG",
        "kind": "mass_render_result",
        "status": render_status,
        "activation": status_activation(render_status),
        "evidence": deepcopy(dict(preview)),
    })
    edges.append(edge("flow:render", "render:mass_png", "materialized_png", status_activation(render_status)))

    vlm_status = str(vlm.get("status") or "not_evaluated")
    nodes.append(flow_node("flow:vlm", "vlm", "VLM critic", vlm_status, evidence=vlm))
    for view in preview.get("views") or ("isometric", "opposite", "front", "top"):
        edges.append(edge(f"render:{view}", "flow:vlm", "visual_input", status_activation(vlm_status)))
    edges.append(edge("render:mass_png", "flow:vlm", "candidate_image_input", status_activation(vlm_status)))
    append_vlm_nodes(nodes, edges, vlm)

    selector = stage_by_id["selector"]
    nodes.append(flow_node("flow:selector", "selector", selector["label"], selector["status"], evidence=selector["evidence"]))
    edges.append(edge(prior, "flow:selector", "hard_gate_input", status_activation(selector["status"])))
    edges.append(edge("flow:vlm", "flow:selector", "critic_input", status_activation(vlm_status)))
    nodes.append({
        "id": "result:mass",
        "column": "result",
        "label": str(getattr(program, "name", "") or "Generated MASS"),
        "kind": "mass_result",
        "status": render_status,
        "activation": status_activation(render_status),
        "evidence": deepcopy(dict(preview)),
    })
    edges.append(edge("render:mass_png", "result:mass", "generated_result", status_activation(render_status)))
    edges.append(edge("flow:selector", "result:mass", "selection_status", status_activation(selector["status"])))
    ast_node_ids = [f"ast:{node.id}" for node in ordered_nodes]
    incoming_ast_targets = {
        str(item.get("target") or "")
        for item in edges
        if str(item.get("target") or "").startswith("ast:")
    }
    root_node_ids = [node_id for node_id in ast_node_ids if node_id not in incoming_ast_targets]
    try:
        program_hash = str(program.program_hash())
    except (AttributeError, TypeError, ValueError):
        program_hash = ""
    return {
        "schema_version": "arr.maas.mass_activation_graph.v1",
        "graph_id": f"mass-execution:{program_hash or program.root_id}",
        "internal_neuron_claim": False,
        "causal_program_trace": True,
        "root_node_ids": root_node_ids,
        "result_node_ids": ["result:mass"],
        "query_contract": {
            "selection_unit": "one_executed_mass",
            "default_query": "active_ancestors_of_result:mass",
            "node_identity": "stable node.id within program_hash",
            "edge_direction": "cause_to_effect",
            "active_edge_predicate": "activation > 0",
            "inactive_evidence_policy": "retain node and edge with activation=0; never infer pass",
            "visualization_policy": "render one selected MASS induced subgraph; never create parallel authority graphs",
            "book_image_policy": "BOOK is typed language provenance, not raster image evidence",
            "vlm_image_policy": "materialize only images actually submitted to a recorded VLM evaluation",
        },
        "nodes": nodes,
        "edges": edges,
    }


def append_vlm_nodes(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], vlm: Mapping[str, Any]) -> None:
    existing = {str(node.get("id") or "") for node in nodes}
    image_inputs = vlm.get("image_inputs") if isinstance(vlm.get("image_inputs"), dict) else {}
    assessments = {
        str(item.get("source_id") or ""): item
        for item in vlm.get("reference_assessments") or ()
        if isinstance(item, dict) and item.get("source_id")
    }
    for index, reference in enumerate(image_inputs.get("references") or (), start=1):
        if not isinstance(reference, dict) or reference.get("used_by_vlm") is not True:
            continue
        source_id = str(reference.get("source_id") or index)
        digest = hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:12]
        node_id = f"vlm:reference:{digest}"
        if node_id in existing:
            continue
        evidence = deepcopy(reference)
        if source_id in assessments:
            evidence["vlm_assessment"] = deepcopy(assessments[source_id])
        nodes.append({
            "id": node_id,
            "source_id": source_id,
            "column": "reference",
            "label": str(reference.get("title") or source_id or f"Reference {index}"),
            "kind": "vlm_reference_image",
            "status": "evaluated",
            "activation": 1.0,
            "evidence": evidence,
        })
        edges.append(edge(node_id, "flow:vlm", "visual_reference_input", 1.0))
        existing.add(node_id)
    for key, value in sorted((vlm.get("concept_scores") or {}).items()):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        score = max(0.0, min(1.0, float(value)))
        node_id = f"vlm:concept:{key}"
        if node_id in existing:
            continue
        nodes.append({"id": node_id, "column": "vlm", "label": str(key), "kind": "vlm_concept_score", "status": "evaluated", "activation": score, "evidence": {"score": float(value)}})
        edges.append(edge("flow:vlm", node_id, "concept_score", score))
        existing.add(node_id)
    for index, edit in enumerate(vlm.get("geometry_edits") or (), start=1):
        if not isinstance(edit, dict):
            continue
        node_id = f"vlm:edit:{index}"
        if node_id in existing:
            continue
        nodes.append({"id": node_id, "column": "repair", "label": str(edit.get("operation") or edit.get("op") or "typed edit"), "kind": "typed_geometry_edit", "status": "evaluated", "activation": 1.0, "evidence": deepcopy(edit)})
        edges.append(edge("flow:vlm", node_id, "requests_edit", 1.0))
        existing.add(node_id)


def flow_node(node_id: str, column: str, label: str, status: str, *, evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {"id": node_id, "column": column, "label": label, "kind": "pipeline_stage", "status": status, "activation": status_activation(status), "evidence": deepcopy(dict(evidence or {}))}


def edge(source: str, target: str, relation: str, activation: float) -> dict[str, Any]:
    digest = hashlib.sha256(f"{source}|{relation}|{target}".encode("utf-8")).hexdigest()[:16]
    return {"id": f"edge:{digest}", "source": source, "target": target, "relation": relation, "activation": round(float(activation), 6)}


__all__ = ["append_vlm_nodes", "build_activation_graph", "edge"]
