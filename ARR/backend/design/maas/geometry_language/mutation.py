"""Bounded typed mutation of recursive geometry programs.

VLM/LLM agents never write kernel objects.  They emit these small edits; this
module validates references, operator compatibility and parameter bounds before
the compiler is allowed to see the revised program.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from typing import Any, Iterable

from .ast import GeometryIssue, GeometryNode, GeometryProgram, OPERATORS_BY_KIND


@dataclass(frozen=True)
class GeometryEdit:
    operation: str
    target_node_id: str = ""
    node_id: str = ""
    node_kind: str = ""
    operator: str = ""
    input_ids: tuple[str, ...] = ()
    input_index: int = 0
    input_node_id: str = ""
    parameter_name: str = ""
    numeric_value: float = 0.0
    string_value: str = ""
    vector_value: tuple[float, ...] = ()
    semantic_role: str = ""
    rationale: str = ""

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "GeometryEdit":
        return cls(
            operation=str(value.get("operation") or ""),
            target_node_id=str(value.get("target_node_id") or ""),
            node_id=str(value.get("node_id") or ""),
            node_kind=str(value.get("node_kind") or ""),
            operator=str(value.get("operator") or ""),
            input_ids=tuple(str(item) for item in value.get("input_ids") or ()),
            input_index=int(value.get("input_index") or 0),
            input_node_id=str(value.get("input_node_id") or ""),
            parameter_name=str(value.get("parameter_name") or ""),
            numeric_value=float(value.get("numeric_value") or 0.0),
            string_value=str(value.get("string_value") or ""),
            vector_value=tuple(float(item) for item in value.get("vector_value") or ()),
            semantic_role=str(value.get("semantic_role") or ""),
            rationale=str(value.get("rationale") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "target_node_id": self.target_node_id,
            "node_id": self.node_id,
            "node_kind": self.node_kind,
            "operator": self.operator,
            "input_ids": list(self.input_ids),
            "input_index": self.input_index,
            "input_node_id": self.input_node_id,
            "parameter_name": self.parameter_name,
            "numeric_value": self.numeric_value,
            "string_value": self.string_value,
            "vector_value": list(self.vector_value),
            "semantic_role": self.semantic_role,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class MutationResult:
    status: str
    program: GeometryProgram | None
    applied_edits: tuple[GeometryEdit, ...] = ()
    issues: tuple[GeometryIssue, ...] = ()


ALLOWED_EDIT_OPERATIONS = frozenset({
    "set_parameter",
    "replace_operator",
    "add_node",
    "remove_node",
    "rewire_input",
    "set_root",
})

NUMERIC_BOUNDS: dict[str, tuple[float, float]] = {
    "angle": (-180.0, 180.0),
    "angle_degrees": (-180.0, 180.0),
    "amount": (-0.85, 0.85),
    "ratio": (0.03, 0.75),
    "margin": (0.03, 0.45),
    "margin_ratio": (0.03, 0.45),
    "setback_ratio": (0.0, 0.32),
    "gap_ratio": (0.04, 0.5),
    "height_ratio": (0.05, 1.4),
    "offset": (-1000.0, 1000.0),
    "offset_ratio": (0.02, 0.45),
    "distance": (0.001, 1000.0),
    "count": (1.0, 24.0),
    "levels": (2.0, 10.0),
    "subdivisions": (2.0, 7.0),
    "width": (0.01, 1000.0),
    "depth": (0.01, 1000.0),
    "height": (0.01, 1000.0),
    "profile_width": (0.01, 1000.0),
    "profile_height": (0.01, 1000.0),
}

VECTOR_LENGTHS: dict[str, tuple[int, ...]] = {
    "vector": (3,),
    "pivot": (3,),
    "normal": (3,),
    "angles": (3,),
    "scale": (2, 3),
    "start_scale": (2,),
    "end_scale": (2,),
    "shift_per_level": (3,),
}


def apply_geometry_edits(program: GeometryProgram, edits: Iterable[GeometryEdit | dict[str, Any]]) -> MutationResult:
    normalized = tuple(edit if isinstance(edit, GeometryEdit) else GeometryEdit.from_dict(edit) for edit in edits)
    if not normalized:
        return MutationResult("no_edits", None)
    nodes = list(program.nodes)
    root_id = program.root_id
    applied: list[GeometryEdit] = []
    issues: list[GeometryIssue] = []

    for edit in normalized:
        if edit.operation not in ALLOWED_EDIT_OPERATIONS:
            issues.append(GeometryIssue("unsupported_edit", edit.operation, edit.target_node_id))
            continue
        node_map = {node.id: node for node in nodes}
        target = node_map.get(edit.target_node_id)
        if edit.operation == "set_parameter":
            if target is None:
                issues.append(GeometryIssue("edit_target_missing", "parameter target does not exist", edit.target_node_id))
                continue
            value, issue = _parameter_value(edit)
            if issue is not None:
                issues.append(issue)
                continue
            params = json.loads(json.dumps(target.parameters))
            params[edit.parameter_name] = value
            nodes[nodes.index(target)] = replace(target, parameters=params)
            applied.append(edit)
        elif edit.operation == "replace_operator":
            if target is None or edit.operator not in OPERATORS_BY_KIND.get(target.kind, ()):
                issues.append(GeometryIssue("incompatible_operator", f"{target.kind if target else '?'}:{edit.operator}", edit.target_node_id))
                continue
            nodes[nodes.index(target)] = replace(target, operator=edit.operator)
            applied.append(edit)
        elif edit.operation == "add_node":
            if not edit.node_id or edit.node_id in node_map:
                issues.append(GeometryIssue("duplicate_or_missing_new_node_id", "new node id is invalid", edit.node_id))
                continue
            if edit.node_kind not in OPERATORS_BY_KIND or edit.operator not in OPERATORS_BY_KIND[edit.node_kind]:
                issues.append(GeometryIssue("invalid_new_operator", f"{edit.node_kind}:{edit.operator}", edit.node_id))
                continue
            if any(input_id not in node_map for input_id in edit.input_ids):
                issues.append(GeometryIssue("missing_input", "new node references a missing input", edit.node_id))
                continue
            nodes.append(GeometryNode(
                id=edit.node_id,
                kind=edit.node_kind,
                operator=edit.operator,
                inputs=edit.input_ids,
                parameters={},
                semantic_role=edit.semantic_role,
                provenance={"source": "critic_geometry_edit", "rationale": edit.rationale},
            ))
            applied.append(edit)
        elif edit.operation == "rewire_input":
            if target is None or edit.input_node_id not in node_map or not 0 <= edit.input_index < len(target.inputs):
                issues.append(GeometryIssue("invalid_rewire", "rewire target/input/index is invalid", edit.target_node_id))
                continue
            inputs = list(target.inputs)
            inputs[edit.input_index] = edit.input_node_id
            nodes[nodes.index(target)] = replace(target, inputs=tuple(inputs))
            applied.append(edit)
        elif edit.operation == "set_root":
            candidate = edit.target_node_id or edit.node_id
            if candidate not in node_map:
                issues.append(GeometryIssue("missing_root", "requested root does not exist", candidate))
                continue
            root_id = candidate
            applied.append(edit)
        elif edit.operation == "remove_node":
            if target is None or target.id == root_id or any(target.id in node.inputs for node in nodes):
                issues.append(GeometryIssue("node_not_removable", "node is root or still referenced", edit.target_node_id))
                continue
            nodes.remove(target)
            applied.append(edit)

    if not applied:
        return MutationResult("no_valid_edit_applied", None, issues=tuple(issues))
    revised = program.with_nodes(nodes, root_id=root_id, name_suffix="__critic_revision")
    validation = tuple(issue for issue in revised.validate() if issue.severity == "error")
    if validation:
        return MutationResult("invalid_revision", None, tuple(applied), tuple((*issues, *validation)))
    if revised.program_hash() == program.program_hash():
        return MutationResult("no_program_change", None, tuple(applied), tuple(issues))
    return MutationResult("revised", revised, tuple(applied), tuple(issues))


def _parameter_value(edit: GeometryEdit) -> tuple[Any, GeometryIssue | None]:
    name = edit.parameter_name.strip()
    if not name:
        return None, GeometryIssue("missing_parameter_name", "parameter edit has no name", edit.target_node_id)
    if edit.vector_value:
        allowed_lengths = VECTOR_LENGTHS.get(name)
        if allowed_lengths is not None and len(edit.vector_value) not in allowed_lengths:
            return None, GeometryIssue("invalid_vector_length", f"{name} expects {allowed_lengths}", edit.target_node_id)
        values = [round(float(value), 6) for value in edit.vector_value]
        if name in {"scale", "start_scale", "end_scale"} and min(values) <= 0.02:
            return None, GeometryIssue("degenerate_scale", f"{name} values must exceed 0.02", edit.target_node_id)
        return values, None
    if edit.string_value:
        return edit.string_value.strip().lower()[:80], None
    value = float(edit.numeric_value)
    lower, upper = NUMERIC_BOUNDS.get(name, (-1000.0, 1000.0))
    if not lower <= value <= upper:
        return None, GeometryIssue("parameter_out_of_bounds", f"{name} must be in {lower}..{upper}", edit.target_node_id)
    if name in {"count", "levels", "subdivisions"}:
        return int(round(value)), None
    return round(value, 6), None


__all__ = [
    "ALLOWED_EDIT_OPERATIONS",
    "GeometryEdit",
    "MutationResult",
    "apply_geometry_edits",
]
