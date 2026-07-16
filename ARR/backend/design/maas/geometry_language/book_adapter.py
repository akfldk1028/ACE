"""Project BOOK p.3 scope and operations into the recursive solid AST.

The legacy program-massing compiler still keeps use-specific roles and legal
evidence.  This adapter makes the BOOK sentence causal in the manifold that is
rendered and gated: select a normalized live-solid scope, mutate that solid,
then compose it back with the unselected remainder.  It contains no parcel
coordinates or completed-building templates.
"""

from __future__ import annotations

from dataclasses import replace
from math import tan, radians
from typing import Any

from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.program_massing.book_projection import book_projection_calls, book_projection_scope

from .ast import GeometryNode, GeometryProgram


def apply_book_projection_to_geometry_program(
    program: GeometryProgram,
    sequence: VerbSequence,
) -> GeometryProgram:
    """Return a program whose real root embodies BOOK scope and operations."""
    calls = book_projection_calls(sequence)
    if not calls:
        return program
    scope = book_projection_scope(sequence)
    nodes = list(program.nodes)
    original_root = program.root_id
    current = original_root
    serial = 0

    def add(
        kind: str,
        operator: str,
        inputs: tuple[str, ...],
        parameters: dict[str, Any] | None = None,
        *,
        verb: str,
    ) -> str:
        nonlocal serial
        serial += 1
        node_id = f"book{serial:02d}_{operator}"
        existing = {node.id for node in nodes}
        while node_id in existing:
            serial += 1
            node_id = f"book{serial:02d}_{operator}"
        nodes.append(GeometryNode(
            id=node_id,
            kind=kind,
            operator=operator,
            inputs=inputs,
            parameters=parameters or {},
            semantic_role="book_mutated_dominant",
            provenance={
                "source": "book_recursive_projection",
                "book_verb": verb,
                "scope_label": scope.label,
                "scope_fraction": scope.requested_fraction,
                "scope_orientation": scope.orientation,
                "normalized_parameters_only": True,
            },
        ))
        return node_id

    remainder = ""
    if scope.requested_fraction < 1.0 - 1e-9:
        axis = {"long_axis": "long", "short_axis": "short", "vertical": "z"}[scope.orientation]
        selected = add(
            "modifier", "clip_fraction", (original_root,),
            {"axis": axis, "fraction": scope.requested_fraction, "anchor": "end"},
            verb="select_book_scope",
        )
        remainder = add(
            "boolean", "difference", (original_root, selected), {},
            verb="select_book_scope",
        )
        current = selected

    for call in calls:
        current = _append_book_call(
            add,
            current,
            call,
            scope_orientation=scope.orientation,
        )

    if remainder:
        current = add(
            "boolean", "union", (remainder, current), {},
            verb="recompose_book_scope",
        )

    metadata = {
        **program.metadata,
        "book_recursive_projection": {
            "active": True,
            "scope_label": scope.label,
            "scope_fraction": scope.requested_fraction,
            "scope_orientation": scope.orientation,
            "ordered_verbs": [call.verb for call in calls],
            "geometry_authority": "recursive_manifold_ast",
            "parcel_coordinates_hardcoded": False,
        },
        "pre_book_program_hash": program.program_hash(),
    }
    return replace(
        program,
        nodes=tuple(nodes),
        root_id=current,
        name=f"{program.name}__book_{scope.label.replace('/', '_')}_{'_'.join(call.verb for call in calls)}",
        metadata=metadata,
    )


def _append_book_call(
    add,
    current: str,
    call: VerbCall,
    *,
    scope_orientation: str,
) -> str:
    verb = call.verb
    p = dict(call.params)
    axis = _axis(p.get("axis"))
    # In the architectural language a vertical p.3 selection followed by
    # EXTRUDE means height growth.  Preserve that semantic relation explicitly
    # instead of forcing every compiler probe into the legacy x/y plan axes.
    # No world coordinate or finished geometry is introduced.
    if verb == "extrude" and scope_orientation == "vertical":
        axis = "z"
    amount = _number(p, "factor", _number(p, "ratio", 0.5))
    angle = _number(p, "angle", 28.0)

    if verb in {"expand", "extrude", "compress"}:
        if verb == "expand":
            scale = 1.0 + 0.45 * amount
        elif verb == "extrude":
            scale = 1.0 + 0.55 * _number(p, "length", 0.5)
        else:
            scale = max(0.42, min(0.92, amount))
        vector = [1.0, 1.0, 1.0]
        vector[{"x": 0, "y": 1, "z": 2}[axis]] = scale
        return add("transform", "scale", (current,), {"vector": vector, "pivot": "center"}, verb=verb)
    if verb == "inflate":
        return add("modifier", "inflate", (current,), {
            "axis": "z", "middle_scale": 1.08 + 0.32 * amount, "subdivisions": 4,
        }, verb=verb)
    if verb == "pinch":
        return add("modifier", "pinch", (current,), {
            "axis": axis, "waist_scale": _number(p, "waist_ratio", 0.62), "subdivisions": 4,
        }, verb=verb)
    if verb == "bend":
        return add("modifier", "bend", (current,), {
            "axis": axis, "angle_degrees": angle, "subdivisions": 4,
        }, verb=verb)
    if verb == "twist":
        return add("modifier", "twist", (current,), {
            "axis": "z", "angle_degrees": angle, "subdivisions": 4,
        }, verb=verb)
    if verb in {"skew", "shear"}:
        shear_amount = max(-0.38, min(0.38, tan(radians(angle)) * 0.45))
        return add("transform", "shear", (current,), {
            "axis": axis, "direction": "z", "amount": shear_amount, "pivot": "center",
        }, verb=verb)
    if verb in {"taper", "grade"}:
        end_x = _number(p, "x_ratio", max(0.38, 0.92 - 0.42 * amount))
        end_y = _number(p, "y_ratio", max(0.38, 0.92 - 0.28 * amount))
        taper_axis = "z" if verb == "taper" else axis
        return add("modifier", "taper", (current,), {
            "axis": taper_axis, "start_scale": [1.0, 1.0],
            "end_scale": [end_x, end_y], "subdivisions": 3,
        }, verb=verb)
    if verb in {"carve", "notch", "embed", "extract"}:
        corner = str(p.get("corner") or _corner_for_side(p.get("side")))
        return add("macro", "notch", (current,), {
            "corner": corner, "ratio": _number(p, "ratio", _number(p, "width_ratio", 0.24)),
            "height_ratio": 0.72 if verb in {"carve", "extract"} else 1.0,
        }, verb=verb)
    if verb in {"nest", "inscribe"}:
        inner = _number(p, "inner_scale", _number(p, "ratio", 0.5))
        margin = max(0.10, min(0.42, (1.0 - inner) / 2.0))
        return add("macro", "courtyard", (current,), {"margin_ratio": margin}, verb=verb)
    if verb == "puncture":
        return add("macro", "puncture", (current,), {
            "axis": axis, "count": int(round(_number(p, "n", 2))),
            "ratio": _number(p, "ratio", 0.14),
        }, verb=verb)
    if verb in {"split", "fracture", "join"}:
        return add("macro", "split_wing", (current,), {
            "axis": axis, "gap_ratio": _number(p, "gap_ratio", 0.16),
            "bridge": verb == "join" or _number(p, "bridge_ratio", 0.0) > 0.25,
            "height_ratio": 0.64, "height": 0.18,
        }, verb=verb)
    if verb == "lift":
        return add("macro", "lift", (current,), {
            "rise_ratio": max(0.10, min(0.38, _number(p, "upper_ratio", 0.55) * 0.42)),
            "support_ratio": 0.08,
        }, verb=verb)
    if verb in {"branch", "interlock", "merge"}:
        base_angle = angle if verb != "merge" else 34.0
        if verb == "branch":
            return add("pattern", "radial_array", (current,), {
                "count": 3, "total_angle_degrees": max(24.0, min(105.0, abs(base_angle) * 1.6)),
                "pivot": "center",
            }, verb=verb)
        return add("macro", "cross_mass", (current,), {
            "angle_degrees": max(22.0, min(90.0, abs(base_angle))),
        }, verb=verb)
    if verb in {"rotate", "overlap", "intersect"}:
        rotated = add("transform", "rotate", (current,), {
            "axis": "z", "angle_degrees": angle or 28.0, "pivot": "center",
        }, verb=verb)
        operator = "intersection" if verb == "intersect" else "union"
        return add("boolean", operator, (current, rotated), {}, verb=verb)
    if verb in {"offset", "shift", "lodge"}:
        distance = _number(p, "distance_ratio", 0.18)
        vector = [0.0, 0.0, 0.0]
        vector[0 if axis == "x" else 1] = distance
        moved = add("transform", "translate", (current,), {"vector": vector}, verb=verb)
        if verb == "shift":
            return moved
        return add("boolean", "union", (current, moved), {}, verb=verb)
    if verb in {"array", "pack"}:
        count = max(2, min(4, int(round(_number(p, "n", 3)))))
        spacing = max(0.08, min(0.38, _number(p, "spacing_ratio", 0.18)))
        vector = [spacing if axis == "x" else 0.0, spacing if axis == "y" else 0.0, 0.0]
        return add("pattern", "linear_array", (current,), {"count": count, "vector": vector}, verb=verb)
    if verb == "reflect":
        normal = [1.0, 0.0, 0.0] if axis == "x" else [0.0, 1.0, 0.0]
        return add("pattern", "mirror_array", (current,), {"normal": normal, "pivot": "center"}, verb=verb)
    if verb == "stack":
        return add("macro", "stepped_mass", (current,), {
            "levels": max(2, min(4, int(round(_number(p, "levels", 3))))),
            "setback_ratio": 0.10 + 0.12 * amount,
        }, verb=verb)
    # Every BOOK verb is expected to be covered explicitly. Raising here makes
    # omissions a compiler diagnostic instead of silently returning a box.
    raise ValueError(f"BOOK recursive geometry mapping missing for {verb!r}")


def _axis(value: Any) -> str:
    raw = str(value or "x").lower()
    return raw if raw in {"x", "y", "z"} else "x"


def _number(params: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(params.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _corner_for_side(value: Any) -> str:
    return {"north": "ne", "south": "sw", "east": "se", "west": "nw"}.get(str(value or "east"), "se")


__all__ = ["apply_book_projection_to_geometry_program"]
