"""Recursive, serializable geometry-program AST for architectural massing.

The legacy MAAS source IR is intentionally optimized for parcel-derived 2.5D
volumes.  This AST is the solid-program layer above a real geometry kernel:
every node consumes and returns a solid, so Boolean, deformation, cutting,
pattern and composition results can be nested without a lossy flat verb list.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
import re
from typing import Any, Iterable


NODE_KINDS = frozenset({
    "primitive",
    "transform",
    "modifier",
    "boolean",
    "pattern",
    "composition",
    "macro",
})

OPERATORS_BY_KIND: dict[str, frozenset[str]] = {
    "primitive": frozenset({"box", "cylinder", "extruded_polygon", "wedge", "sweep", "loft"}),
    "transform": frozenset({"translate", "rotate", "scale", "mirror", "shear"}),
    "modifier": frozenset({
        "bend", "taper", "twist", "pinch", "inflate",
        "slice", "clip", "clip_fraction", "cut_corner",
    }),
    "boolean": frozenset({"union", "difference", "intersection"}),
    "pattern": frozenset({"duplicate", "linear_array", "radial_array", "mirror_array", "stack"}),
    "composition": frozenset({"attach", "bridge"}),
    "macro": frozenset({
        "courtyard",
        "carve_void",
        "notch",
        "setback",
        "terrace",
        "cantilever",
        "bridge",
        "cross_mass",
        "bent_bar",
        "split_wing",
        "attach_volume",
        "tapered_tower",
        "leaning_tower",
        "lift",
        "puncture",
        "cut_corner",
        "stepped_mass",
        "profiled_hall",
    }),
}

UNARY_KINDS = frozenset({"transform", "modifier", "pattern"})
IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,79}$")


@dataclass(frozen=True)
class GeometryIssue:
    code: str
    message: str
    node_id: str = ""
    severity: str = "error"

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "node_id": self.node_id,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class GeometryNode:
    id: str
    kind: str
    operator: str
    inputs: tuple[str, ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)
    semantic_role: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "GeometryNode":
        if not isinstance(value, dict):
            raise TypeError("geometry node must be an object")
        raw_inputs = value.get("inputs") or ()
        if not isinstance(raw_inputs, (list, tuple)):
            raise TypeError("geometry node inputs must be an array")
        parameters = value.get("parameters") or {}
        provenance = value.get("provenance") or {}
        if not isinstance(parameters, dict) or not isinstance(provenance, dict):
            raise TypeError("geometry node parameters/provenance must be objects")
        return cls(
            id=str(value.get("id") or ""),
            kind=str(value.get("kind") or value.get("type") or "").lower(),
            operator=str(value.get("operator") or "").lower(),
            inputs=tuple(str(item) for item in raw_inputs),
            parameters=_json_copy(parameters),
            semantic_role=str(value.get("semantic_role") or ""),
            provenance=_json_copy(provenance),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "operator": self.operator,
            "inputs": list(self.inputs),
            "parameters": _json_copy(self.parameters),
            "semantic_role": self.semantic_role,
            "provenance": _json_copy(self.provenance),
        }


@dataclass(frozen=True)
class GeometryProgram:
    nodes: tuple[GeometryNode, ...]
    root_id: str
    name: str = "geometry_program"
    schema_version: str = "arr.maas.geometry_program.v1"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "GeometryProgram":
        if not isinstance(value, dict):
            raise TypeError("geometry program must be an object")
        nodes = value.get("nodes") or ()
        if not isinstance(nodes, list):
            raise TypeError("geometry program nodes must be an array")
        metadata = value.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise TypeError("geometry program metadata must be an object")
        return cls(
            nodes=tuple(GeometryNode.from_dict(item) for item in nodes),
            root_id=str(value.get("root_id") or ""),
            name=str(value.get("name") or "geometry_program"),
            schema_version=str(value.get("schema_version") or "arr.maas.geometry_program.v1"),
            metadata=_json_copy(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "root_id": self.root_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "metadata": _json_copy(self.metadata),
        }

    @property
    def node_map(self) -> dict[str, GeometryNode]:
        return {node.id: node for node in self.nodes}

    def with_nodes(
        self,
        nodes: Iterable[GeometryNode],
        *,
        root_id: str | None = None,
        name_suffix: str = "",
    ) -> "GeometryProgram":
        return replace(
            self,
            nodes=tuple(nodes),
            root_id=root_id or self.root_id,
            name=f"{self.name}{name_suffix}",
        )

    def validate(self, *, maximum_nodes: int = 96, maximum_depth: int = 32) -> tuple[GeometryIssue, ...]:
        issues: list[GeometryIssue] = []
        if not self.nodes:
            return (GeometryIssue("empty_program", "program has no nodes"),)
        if len(self.nodes) > maximum_nodes:
            issues.append(GeometryIssue("node_budget_exceeded", f"{len(self.nodes)} > {maximum_nodes}"))
        seen: set[str] = set()
        for node in self.nodes:
            if not IDENTIFIER_RE.match(node.id):
                issues.append(GeometryIssue("invalid_node_id", "node id is not a stable identifier", node.id))
            if node.id in seen:
                issues.append(GeometryIssue("duplicate_node_id", "node id appears more than once", node.id))
            seen.add(node.id)
            if node.kind not in NODE_KINDS:
                issues.append(GeometryIssue("unknown_node_kind", node.kind, node.id))
                continue
            if node.operator not in OPERATORS_BY_KIND[node.kind]:
                issues.append(GeometryIssue("unknown_operator", f"{node.kind}:{node.operator}", node.id))
            issues.extend(_arity_issues(node))
            issues.extend(_parameter_issues(node))
        if self.root_id not in seen:
            issues.append(GeometryIssue("missing_root", "root_id does not reference a node", self.root_id))
        for node in self.nodes:
            for input_id in node.inputs:
                if input_id not in seen:
                    issues.append(GeometryIssue("missing_input", f"missing input {input_id}", node.id))

        node_map = self.node_map
        state: dict[str, int] = {}

        def visit(node_id: str, depth: int) -> None:
            if depth > maximum_depth:
                issues.append(GeometryIssue("tree_depth_exceeded", f"depth > {maximum_depth}", node_id))
                return
            if state.get(node_id) == 1:
                issues.append(GeometryIssue("cyclic_reference", "geometry program contains a cycle", node_id))
                return
            if state.get(node_id) == 2 or node_id not in node_map:
                return
            state[node_id] = 1
            for input_id in node_map[node_id].inputs:
                visit(input_id, depth + 1)
            state[node_id] = 2

        if self.root_id in node_map:
            visit(self.root_id, 1)
        reachable = {node_id for node_id, value in state.items() if value == 2}
        for node in self.nodes:
            if node.id not in reachable:
                issues.append(GeometryIssue("unreachable_node", "node is not reachable from root", node.id, "warning"))
        return tuple(_deduplicate_issues(issues))

    def topological_nodes(self) -> tuple[GeometryNode, ...]:
        issues = [issue for issue in self.validate() if issue.severity == "error"]
        if issues:
            raise ValueError("invalid geometry program: " + ", ".join(issue.code for issue in issues))
        node_map = self.node_map
        ordered: list[GeometryNode] = []
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            node = node_map[node_id]
            for input_id in node.inputs:
                visit(input_id)
            visited.add(node_id)
            ordered.append(node)

        visit(self.root_id)
        return tuple(ordered)

    def canonical_dict(self) -> dict[str, Any]:
        ordered = self.topological_nodes()
        return {
            "schema_version": self.schema_version,
            "root_id": self.root_id,
            "nodes": [
                {
                    "id": node.id,
                    "kind": node.kind,
                    "operator": node.operator,
                    "inputs": sorted(node.inputs) if node.operator in {"union", "intersection", "attach"} else list(node.inputs),
                    "parameters": _canonical_value(node.parameters),
                    "semantic_role": node.semantic_role,
                }
                for node in ordered
            ],
        }

    def program_hash(self) -> str:
        payload = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _arity_issues(node: GeometryNode) -> list[GeometryIssue]:
    count = len(node.inputs)
    if node.kind == "primitive" and count != 0:
        return [GeometryIssue("invalid_arity", "primitive accepts no solid inputs", node.id)]
    if node.kind in UNARY_KINDS and count != 1:
        return [GeometryIssue("invalid_arity", f"{node.kind} requires one input", node.id)]
    if node.kind == "boolean":
        if node.operator == "difference" and count != 2:
            return [GeometryIssue("invalid_arity", "difference requires exactly two inputs", node.id)]
        if node.operator in {"union", "intersection"} and count < 2:
            return [GeometryIssue("invalid_arity", f"{node.operator} requires at least two inputs", node.id)]
    if node.kind == "composition" and count < 2:
        return [GeometryIssue("invalid_arity", "composition requires at least two inputs", node.id)]
    if node.kind == "macro" and count < 1:
        return [GeometryIssue("invalid_arity", "architectural macro requires a base input", node.id)]
    return []


def _parameter_issues(node: GeometryNode) -> list[GeometryIssue]:
    issues: list[GeometryIssue] = []
    params = node.parameters
    positive_fields = {
        "width", "depth", "height", "radius", "radius_low", "radius_high",
        "start_height", "end_height", "profile_width", "profile_height", "level_height",
    }
    for key in positive_fields:
        if key not in params:
            continue
        try:
            if float(params[key]) <= 0:
                issues.append(GeometryIssue("non_positive_dimension", f"{key} must be positive", node.id))
        except (TypeError, ValueError):
            issues.append(GeometryIssue("invalid_parameter_type", f"{key} must be numeric", node.id))
    if node.operator in {"linear_array", "radial_array", "stack", "duplicate"}:
        try:
            count = int(params.get("count", 2))
            if not 1 <= count <= 24:
                issues.append(GeometryIssue("pattern_count_out_of_bounds", "count must be 1..24", node.id))
        except (TypeError, ValueError):
            issues.append(GeometryIssue("invalid_parameter_type", "count must be integer", node.id))
    if node.operator in {"extruded_polygon", "loft"}:
        key = "points" if node.operator == "extruded_polygon" else "profiles"
        minimum = 3 if node.operator == "extruded_polygon" else 2
        if not isinstance(params.get(key), list) or len(params[key]) < minimum:
            issues.append(GeometryIssue("missing_profile", f"{node.operator} requires at least {minimum} {key}", node.id))
    if node.operator == "sweep":
        path = params.get("path")
        if not isinstance(path, list) or len(path) < 2:
            issues.append(GeometryIssue("missing_path", "sweep requires at least two path points", node.id))
    if node.operator in {"slice", "clip"}:
        normal = params.get("normal")
        if not _vector(normal, 3) or sum(float(value) ** 2 for value in normal) <= 1e-12:
            issues.append(GeometryIssue("invalid_plane", "cutting plane needs a non-zero normal", node.id))
    if node.operator == "clip_fraction":
        try:
            fraction = float(params.get("fraction", 1.0))
            if not 0.01 <= fraction <= 1.0:
                issues.append(GeometryIssue("scope_fraction_out_of_bounds", "fraction must be 0.01..1.0", node.id))
        except (TypeError, ValueError):
            issues.append(GeometryIssue("invalid_parameter_type", "fraction must be numeric", node.id))
    return issues


def _vector(value: Any, length: int) -> bool:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        return False
    try:
        return all(float(item) == float(item) for item in value)
    except (TypeError, ValueError):
        return False


def _deduplicate_issues(issues: Iterable[GeometryIssue]) -> list[GeometryIssue]:
    result: list[GeometryIssue] = []
    seen: set[tuple[str, str, str]] = set()
    for issue in issues:
        key = (issue.code, issue.node_id, issue.message)
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result


def _json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _canonical_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _canonical_value(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, float):
        return round(value, 8)
    return value


GEOMETRY_PROGRAM_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://arr.local/schema/maas-geometry-program-v1.json",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "name", "root_id", "nodes", "metadata"],
    "properties": {
        "schema_version": {"const": "arr.maas.geometry_program.v1"},
        "name": {"type": "string", "minLength": 1, "maxLength": 120},
        "root_id": {"type": "string", "pattern": IDENTIFIER_RE.pattern},
        "metadata": {"type": "object"},
        "nodes": {
            "type": "array",
            "minItems": 1,
            "maxItems": 96,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "kind", "operator", "inputs", "parameters", "semantic_role", "provenance"],
                "properties": {
                    "id": {"type": "string", "pattern": IDENTIFIER_RE.pattern},
                    "kind": {"enum": sorted(NODE_KINDS)},
                    "operator": {"type": "string"},
                    "inputs": {"type": "array", "items": {"type": "string"}, "maxItems": 24},
                    "parameters": {"type": "object"},
                    "semantic_role": {"type": "string", "maxLength": 80},
                    "provenance": {"type": "object"},
                },
            },
        },
    },
}


__all__ = [
    "GEOMETRY_PROGRAM_JSON_SCHEMA",
    "GeometryIssue",
    "GeometryNode",
    "GeometryProgram",
    "NODE_KINDS",
    "OPERATORS_BY_KIND",
]
