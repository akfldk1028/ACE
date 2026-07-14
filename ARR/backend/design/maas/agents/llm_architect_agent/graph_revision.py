"""Apply validated VLM/A2A critic edits to the architectural genotype."""

from __future__ import annotations

from dataclasses import replace

from design.maas.agents.orchestrator.generative_loop import CriticDirective
from design.maas.grammar.component_graph import MassComponentGraph, MassComponentNode, graph_with_nodes
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.grammar.vocab import SUPPORTED_VERBS
from design.maas.grammar.parameter_schema import PARAMETER_BOUNDS, bounded_parameter


ALLOWED_ROLES = {"primary", "support", "void", "connector"}


def apply_critic_graph_mutations(
    graph: MassComponentGraph,
    directive: CriticDirective,
) -> tuple[MassComponentGraph, ...]:
    """Apply bounded edits without crossing the lossy flat-sequence boundary."""
    nodes = list(graph.nodes)
    changed = False
    for edit in directive.graph_edits:
        operation = edit.operation
        index = next((i for i, node in enumerate(nodes) if node.node_id == edit.target_node_id), None)
        if operation == "set_parameter":
            if index is None or nodes[index].role == "root" or edit.parameter_name not in PARAMETER_BOUNDS:
                continue
            node = nodes[index]
            params = dict(node.operation.params)
            params[edit.parameter_name] = bounded_parameter(edit.parameter_name, edit.numeric_value)
            nodes[index] = replace(node, operation=VerbCall(node.operation.verb, params))
            changed = True
        elif operation == "replace_operation":
            if index is None or nodes[index].role == "root" or edit.verb not in SUPPORTED_VERBS or edit.verb == "base":
                continue
            node = nodes[index]
            # Replacement changes topology semantics; do not leak parameters
            # that belong to the previous verb.
            nodes[index] = replace(node, operation=VerbCall(edit.verb, {}))
            changed = True
        elif operation == "remove_optional":
            if index is None or not nodes[index].optional or any(node.parent_id == nodes[index].node_id for node in nodes):
                continue
            nodes.pop(index)
            changed = True
        elif operation == "reparent":
            ids = {node.node_id for node in nodes}
            if (
                index is None
                or nodes[index].role == "root"
                or edit.parent_node_id not in ids
                or edit.parent_node_id == nodes[index].node_id
            ):
                continue
            parent_index = next(i for i, node in enumerate(nodes) if node.node_id == edit.parent_node_id)
            if parent_index >= index:
                continue
            nodes[index] = replace(nodes[index], parent_id=edit.parent_node_id)
            changed = True
        elif operation == "add_operation":
            ids = {node.node_id for node in nodes}
            if (
                not edit.node_id or edit.node_id in ids or edit.parent_node_id not in ids
                or edit.role not in ALLOWED_ROLES or edit.verb not in SUPPORTED_VERBS or edit.verb == "base"
                or len(nodes) >= 6
            ):
                continue
            nodes.append(MassComponentNode(
                node_id=edit.node_id,
                role=edit.role,
                parent_id=edit.parent_node_id,
                optional=edit.role in {"support", "connector"},
                operation=VerbCall(edit.verb, {}),
                constraints={"inside_legal_envelope": True, "critic_authored": True},
                relation="subtract" if edit.role == "void" else "connect" if edit.role == "connector" else "attach",
            ))
            changed = True
    if not changed:
        return ()
    revised = graph_with_nodes(graph, nodes, suffix="__a2a_critic_revision")
    if revised.validate():
        return ()
    return (revised,)


def apply_critic_graph_edits(sequence: VerbSequence, directive: CriticDirective) -> tuple[VerbSequence, ...]:
    """Legacy adapter that transports the complete V2 graph envelope."""
    from design.maas.grammar.component_graph import graph_from_sequence

    revised = apply_critic_graph_mutations(graph_from_sequence(sequence), directive)
    return tuple(graph.to_sequence(name=graph.name) for graph in revised)


__all__ = ["apply_critic_graph_edits", "apply_critic_graph_mutations"]
