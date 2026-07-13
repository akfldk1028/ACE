"""Hierarchical component graph for MAAS mass generation.

The graph is the architectural genotype.  ``VerbSequence`` remains a wire
format/legacy adapter, but geometry generation and critic mutation reason about
explicit primary, support, void and connector components instead of positions
in a flat list.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Iterable

from .verb_sequence import VerbCall, VerbSequence


GRAPH_SCHEMA_VERSION = "arr.maas.component_graph.v1"

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "role": self.role,
            "parent_id": self.parent_id,
            "optional": self.optional,
            "operation": self.operation.to_dict(),
            "constraints": dict(self.constraints),
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
            known.add(node.node_id)
        if len(self.nodes) > 6:
            errors.append("component graph exceeds six-node early-massing budget")
        return errors

    def to_sequence(self, *, name: str | None = None) -> VerbSequence:
        return VerbSequence(
            name or self.name,
            self.label,
            tuple(node.operation for node in self.nodes),
            self.notes + ("component_graph=arr.maas.component_graph.v1",),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": GRAPH_SCHEMA_VERSION,
            "name": self.name,
            "label": self.label,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [
                {"parent": node.parent_id, "child": node.node_id, "relation": node.role}
                for node in self.nodes if node.parent_id is not None
            ],
            "validation_errors": self.validate(),
        }


def graph_from_sequence(sequence: VerbSequence) -> MassComponentGraph:
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
    "MassComponentGraph",
    "MassComponentNode",
    "graph_from_sequence",
    "graph_with_nodes",
    "strengthen_node",
]
