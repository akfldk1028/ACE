"""Hierarchical component graph for MAAS mass generation.

The graph is the architectural genotype.  ``VerbSequence`` remains a wire
format/legacy adapter, but geometry generation and critic mutation reason about
explicit primary, support, void and connector components instead of positions
in a flat list.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Any, Iterable

from .verb_sequence import VerbCall, VerbSequence


GRAPH_SCHEMA_VERSION = "arr.maas.component_graph.v2"
LEGACY_GRAPH_SCHEMA_VERSION = "arr.maas.component_graph.v1"
GRAPH_NOTE_PREFIX = "component_graph_json="

PRIMARY_VERBS = {"base", "bar", "extrude", "taper", "stack", "grade", "inset", "expand"}
VOID_VERBS = {"notch", "cave", "courtyard", "puncture", "pinch", "embed", "nest"}
CONNECTOR_VERBS = {"bridge", "diagonal_connect", "terrace_link", "interlock", "overlap"}


def _role_for(verb: str, index: int) -> str:
    if index == 0 or verb == "base":
        return "root"
    if verb in VOID_VERBS:
        return "void"
    if verb in CONNECTOR_VERBS:
        return "connector"
    if verb in PRIMARY_VERBS and index == 1:
        return "primary"
    return "support"


@dataclass(frozen=True)
class MassComponentNode:
    node_id: str
    role: str
    operation: VerbCall
    parent_id: str | None = None
    optional: bool = False
    constraints: dict[str, Any] = field(default_factory=dict)
    relation: str = "attach"

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "role": self.role,
            "parent_id": self.parent_id,
            "optional": self.optional,
            "operation": self.operation.to_dict(),
            "constraints": dict(self.constraints),
            "relation": self.relation,
        }


@dataclass(frozen=True)
class MassComponentGraph:
    name: str
    label: str
    nodes: tuple[MassComponentNode, ...]
    notes: tuple[str, ...] = ()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.nodes:
            return ["empty component graph"]
        ids = [node.node_id for node in self.nodes]
        if len(ids) != len(set(ids)):
            errors.append("duplicate component node id")
        roots = [node for node in self.nodes if node.role == "root"]
        if len(roots) != 1 or roots[0].operation.verb != "base":
            errors.append("component graph requires exactly one base root")
        known: set[str] = set()
        for node in self.nodes:
            if node.parent_id is not None and node.parent_id not in known:
                errors.append(f"node {node.node_id}: parent must precede child")
            if node.role in {"void", "connector", "support"} and node.parent_id is None:
                errors.append(f"node {node.node_id}: {node.role} requires a parent")
            if node.relation not in {"attach", "input", "connect", "deform", "subtract"}:
                errors.append(f"node {node.node_id}: unsupported relation {node.relation!r}")
            known.add(node.node_id)
        if len(self.nodes) > 6:
            errors.append("component graph exceeds six-node early-massing budget")
        return errors

    def to_sequence(self, *, name: str | None = None) -> VerbSequence:
        # VerbSequence is still used by older service boundaries.  Carry the
        # complete graph as an explicit envelope so a critic-authored branch is
        # not silently flattened on the next compile/search pass.
        graph_note = GRAPH_NOTE_PREFIX + json.dumps(
            self.to_dict(include_validation=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return VerbSequence(
            name or self.name,
            self.label,
            tuple(node.operation for node in self.nodes),
            tuple(note for note in self.notes if not note.startswith(GRAPH_NOTE_PREFIX))
            + (f"component_graph={GRAPH_SCHEMA_VERSION}", graph_note),
        )

    def to_dict(self, *, include_validation: bool = True) -> dict[str, Any]:
        data = {
            "schema_version": GRAPH_SCHEMA_VERSION,
            "name": self.name,
            "label": self.label,
            "notes": list(self.notes),
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [
                {"parent": node.parent_id, "child": node.node_id, "relation": node.relation}
                for node in self.nodes if node.parent_id is not None
            ],
        }
        if include_validation:
            data["validation_errors"] = self.validate()
        return data


def graph_from_dict(data: dict[str, Any]) -> MassComponentGraph:
    """Parse both V1 and V2 graph payloads at one audited boundary."""
    if not isinstance(data, dict) or not isinstance(data.get("nodes"), list):
        raise ValueError("component_graph.nodes is required")
    nodes: list[MassComponentNode] = []
    for item in data["nodes"]:
        operation = item.get("operation") if isinstance(item, dict) else None
        if not isinstance(operation, dict) or not operation.get("verb"):
            raise ValueError("every component node requires operation.verb")
        role = str(item.get("role") or "support")
        relation = str(item.get("relation") or ("subtract" if role == "void" else "connect" if role == "connector" else "attach"))
        nodes.append(MassComponentNode(
            node_id=str(item.get("node_id") or ""),
            role=role,
            parent_id=str(item["parent_id"]) if item.get("parent_id") is not None else None,
            optional=bool(item.get("optional")),
            operation=VerbCall(str(operation["verb"]), dict(operation.get("params") or {})),
            constraints=dict(item.get("constraints") or {}),
            relation=relation,
        ))
    graph = MassComponentGraph(
        name=str(data.get("name") or "component_graph"),
        label=str(data.get("label") or "Component graph"),
        nodes=tuple(nodes),
        notes=tuple(str(note) for note in data.get("notes") or ()),
    )
    errors = graph.validate()
    if errors:
        raise ValueError("invalid component graph: " + "; ".join(errors))
    return graph


def graph_from_sequence(sequence: VerbSequence) -> MassComponentGraph:
    for note in reversed(sequence.notes):
        if not note.startswith(GRAPH_NOTE_PREFIX):
            continue
        try:
            graph = graph_from_dict(json.loads(note[len(GRAPH_NOTE_PREFIX):]))
        except (TypeError, ValueError, json.JSONDecodeError):
            break
        return MassComponentGraph(
            name=sequence.name,
            label=sequence.label,
            nodes=graph.nodes,
            notes=tuple(item for item in sequence.notes if not item.startswith(GRAPH_NOTE_PREFIX) and not item.startswith("component_graph=")),
        )
    nodes: list[MassComponentNode] = []
    previous_id = "root"
    for index, operation in enumerate(sequence.calls):
        role = _role_for(operation.verb, index)
        node_id = "root" if index == 0 else f"{role}_{index}_{operation.verb}"
        if role == "primary":
            parent_id = "root"
        elif role == "root":
            parent_id = None
        else:
            # A flat sequence is an ordered dependency chain.  Explicit graph
            # producers may branch by supplying a different parent_id, but the
            # compatibility adapter must preserve sequential semantics.
            parent_id = previous_id
        nodes.append(MassComponentNode(
            node_id=node_id,
            role=role,
            operation=operation,
            parent_id=parent_id,
            optional=role in {"support", "connector"} and index >= 2,
            constraints={
                "inside_legal_envelope": True,
                "requires_primary_support": role in {"support", "connector"},
                "subtractive": role == "void",
            },
            relation="subtract" if role == "void" else "connect" if role == "connector" else "attach",
        ))
        previous_id = node_id
    return MassComponentGraph(sequence.name, sequence.label, tuple(nodes), sequence.notes)


def graph_with_nodes(graph: MassComponentGraph, nodes: Iterable[MassComponentNode], *, suffix: str) -> MassComponentGraph:
    return MassComponentGraph(
        f"{graph.name}{suffix}",
        graph.label,
        tuple(nodes),
        graph.notes,
    )


def strengthen_node(node: MassComponentNode) -> MassComponentNode:
    params = dict(node.operation.params)
    for key in ("ratio", "factor", "width_ratio", "depth_ratio", "upper_ratio", "top_ratio", "slab_ratio"):
        if isinstance(params.get(key), int | float):
            params[key] = round(min(0.90, max(0.18, float(params[key]) * 1.12)), 3)
    return replace(node, operation=VerbCall(node.operation.verb, params))


__all__ = [
    "GRAPH_SCHEMA_VERSION",
    "GRAPH_NOTE_PREFIX",
    "MassComponentGraph",
    "MassComponentNode",
    "graph_from_sequence",
    "graph_from_dict",
    "graph_with_nodes",
    "strengthen_node",
]
