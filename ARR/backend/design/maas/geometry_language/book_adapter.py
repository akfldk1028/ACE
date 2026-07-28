"""Project BOOK p.3 scope and operations into the recursive solid AST.

The legacy program-massing compiler still keeps use-specific roles and legal
evidence.  This adapter makes the BOOK sentence causal in the manifold that is
rendered and gated: select a normalized live-solid scope, mutate that solid,
then compose it back with the unselected remainder.  It contains no parcel
coordinates or completed-building templates.
"""

from __future__ import annotations

from dataclasses import replace
from math import ceil, radians, sqrt, tan
from typing import Any

from design.maas.grammar.verb_sequence import VerbCall, VerbSequence
from design.maas.program_massing.book_projection import book_projection_calls, book_projection_scope
from design.maas.book_language.base_volume_contract import (
    book_base_volume_outward_sign,
    book_base_volume_spec,
)

from .ast import GeometryNode, GeometryProgram
from .book_parameter_projection import (
    book_parameter_projection_evidence,
    book_relation_invariant,
    project_book_parameter,
)
from .book_chassis_compatibility import (
    project_book_split_gap_ratio,
    validate_book_chassis_compatibility,
)


_CANONICAL_OPERATOR_EFFECT = {
    "bent_bar": "bend",
    "bend": "bend",
    "tapered_tower": "taper",
    "taper": "taper",
    "leaning_tower": "shear",
    "shear": "shear",
    "setback": "step",
    "stepped_mass": "step",
    "terrace": "step",
    "stack": "step",
    "book_lift": "book_lift",
    "book_lodge": "book_lodge",
    "book_rotate": "book_rotate",
    "book_carve": "book_carve",
    "book_fracture": "book_fracture",
    "book_grade": "book_grade",
    "book_notch": "book_notch",
    "book_extract": "book_extract",
}

_BOOK_VERB_CANONICAL_EFFECT = {
    "expand": "boundary_expand", "extrude": "scale", "compress": "scale",
    "inflate": "inflate", "pinch": "pinch", "bend": "bend",
    "twist": "twist", "skew": "shear", "shear": "slice",
    "taper": "taper", "grade": "book_grade",
    "carve": "book_carve", "notch": "book_notch", "embed": "embed_void", "extract": "book_extract",
    "nest": "nested_related", "inscribe": "courtyard", "puncture": "puncture",
    "split": "split_wing", "fracture": "book_fracture", "join": "join_related",
    "lift": "book_lift", "branch": "book_branch", "interlock": "interlock_related", "merge": "cross_mass",
    "rotate": "book_rotate", "overlap": "overlap_related", "intersect": "intersect_related",
    "offset": "nested_related", "lodge": "book_lodge", "shift": "shift_related",
    "array": "related_array", "pack": "related_array", "reflect": "mirror_array",
    "stack": "step",
}

_PROGRAM_THRESHOLD_OPERATORS = {
    "courtyard", "carve_void", "notch", "lift", "cantilever", "split_wing",
}


def _is_terminal_program_relation(node: GeometryNode) -> bool:
    if node.operator == "profiled_hall":
        return True
    role = str(node.semantic_role or "").strip().lower()
    role_is_threshold = any(
        token in role for token in (
            "threshold", "entry", "public", "court", "atrium", "ground",
            "void", "terrace", "access",
        )
    )
    return bool(
        node.operator in _PROGRAM_THRESHOLD_OPERATORS
        and (role_is_threshold or bool((node.provenance or {}).get("program_invariant")))
    )


def _program_access_side(program: GeometryProgram) -> str:
    """Return the coordinate-free cardinal access relation in the source AST."""

    for node in reversed(program.topological_nodes()):
        for parameter in ("access_side", "open_side", "side"):
            value = str(node.parameters.get(parameter) or "").strip().lower()
            if value in {"east", "west", "north", "south"}:
                return value
    return "closed"


def apply_capacity_composition_to_geometry_program(
    program: GeometryProgram,
    *,
    achieved_utilization: float,
    target_utilization: float,
) -> GeometryProgram:
    """Recompose a shortfall as a measured typed pack in the same AST.

    The capacity agent is not allowed to swap in a named finished form.  It may
    only aggregate the already-authored BOOK body, with count and unit scale
    derived from the exact shared-floor utilization shortfall.  Program access
    and section relations remain a terminal suffix over the recomposed body.
    """

    achieved = max(0.0, float(achieved_utilization or 0.0))
    target = max(0.0, min(0.98, float(target_utilization or 0.0)))
    if achieved <= 1e-9 or target <= achieved + 1e-9:
        return program

    required_area_ratio = max(1.0, min(3.2, target / achieved))
    # A pack is not four miniature buildings. Account for the useful area of
    # one overlapping unit and prefer the smallest count that can close the
    # measured shortfall. The old ``0.82 ** 2`` divisor turned a 1.5x gap into
    # three narrow wings; legal-host fitting then shrank each wing below the
    # shared-floor clear-depth minimum.
    effective_unit_yield = 0.82
    count = max(
        2,
        min(4, int(ceil(required_area_ratio / effective_unit_yield))),
    )
    # Preserve inhabitable unit depth. The complete composition still receives
    # the same site/floor Matrix4 fit and every legal/capacity gate afterward.
    unit_scale = 0.94

    nodes = list(program.nodes)
    node_map = program.node_map
    terminal_suffix_reversed: list[GeometryNode] = []
    cursor = node_map.get(program.root_id)
    while cursor is not None and _is_terminal_program_relation(cursor) and len(cursor.inputs) == 1:
        terminal_suffix_reversed.append(cursor)
        cursor = node_map.get(cursor.inputs[0])
    terminal_suffix = list(reversed(terminal_suffix_reversed))
    body_root = cursor.id if cursor is not None else program.root_id

    existing_ids = {node.id for node in nodes}
    node_id = "capacity_composition:measured_pack"
    suffix = 2
    while node_id in existing_ids:
        node_id = f"capacity_composition:measured_pack:{suffix}"
        suffix += 1
    capacity_node = GeometryNode(
        id=node_id,
        kind="macro",
        operator="related_array",
        inputs=(body_root,),
        parameters={
            "mode": "pack",
            "axis": "x",
            "count": count,
            "unit_scale": round(unit_scale, 6),
            "spacing_ratio": 0.08,
            "stagger_ratio": 0.04,
        },
        semantic_role="capacity_composed_building_body",
        provenance={
            "source": "capacity_composition_agent",
            "measurement_source": "shared_floor_contract",
            "achieved_utilization": round(achieved, 6),
            "target_utilization": round(target, 6),
            "required_area_ratio": round(required_area_ratio, 6),
            "normalized_parameters_only": True,
            "parcel_coordinates_used": False,
            "completed_building_template": False,
        },
    )
    nodes.append(capacity_node)
    root_id = capacity_node.id
    if terminal_suffix:
        relation_input = capacity_node.id
        relation_rewrites: dict[str, str] = {}
        for relation_node in terminal_suffix:
            relation_rewrites[relation_node.id] = relation_input
            relation_input = relation_node.id
        nodes = [
            replace(node, inputs=(relation_rewrites[node.id],))
            if node.id in relation_rewrites
            else node
            for node in nodes
        ]
        root_id = program.root_id

    return replace(
        program,
        nodes=tuple(nodes),
        root_id=root_id,
        name=f"{program.name}__capacity_pack_{count}",
        metadata={
            **program.metadata,
            "capacity_composition": {
                "schema_version": "arr.maas.capacity_composition.v1",
                "status": "materialized",
                "mode": "measured_typed_pack",
                "measurement_source": "shared_floor_contract",
                "achieved_utilization": round(achieved, 6),
                "target_utilization": round(target, 6),
                "required_area_ratio": round(required_area_ratio, 6),
                "count": count,
                "unit_scale": round(unit_scale, 6),
                "named_shape_selected": False,
                "parcel_coordinates_used": False,
            },
        },
    )


def apply_book_projection_to_geometry_program(
    program: GeometryProgram,
    sequence: VerbSequence,
) -> GeometryProgram:
    """Return a program whose real root embodies BOOK scope and operations."""
    calls = book_projection_calls(sequence)
    if not calls:
        return program
    scope = book_projection_scope(sequence)
    _validate_projection_effect_budget(program, calls, scope_fraction=scope.requested_fraction)
    chassis_compatibility = validate_book_chassis_compatibility(program, calls)
    nodes = list(program.nodes)
    program_root = program.root_id
    active_book_call_index = -1
    # Program threshold/section nodes are a non-negotiable terminal suffix,
    # while BOOK operations mutate the body. Walk the executable root inward
    # through that unary suffix and insert BOOK before it. The suffix is then
    # rewired over the new body in its original order.
    node_map = program.node_map
    terminal_suffix_reversed: list[GeometryNode] = []
    cursor = node_map.get(program_root)
    while cursor is not None and _is_terminal_program_relation(cursor) and len(cursor.inputs) == 1:
        terminal_suffix_reversed.append(cursor)
        cursor = node_map.get(cursor.inputs[0])
    terminal_suffix = list(reversed(terminal_suffix_reversed))
    program_access_side = _program_access_side(program)
    original_root = cursor.id if cursor is not None else program_root
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
                "book_call_index": active_book_call_index,
                "scope_label": scope.label,
                "scope_fraction": scope.requested_fraction,
                "scope_orientation": scope.orientation,
                "normalized_parameters_only": True,
            },
        ))
        return node_id

    selected = add(
        "modifier", "book_base_volume", (original_root,),
        {"label": scope.label, "orientation": scope.orientation},
        verb="select_book_scope",
    )
    remainder = ""
    current = selected
    if scope.requested_fraction < 1.0 - 1e-9:
        remainder = add(
            "boolean", "difference", (original_root, selected), {},
            verb="select_book_scope",
        )

    verb_occurrences: dict[str, int] = {}
    for call_index, call in enumerate(calls, start=1):
        active_book_call_index = call_index
        occurrence_index = verb_occurrences.get(call.verb, 0)
        verb_occurrences[call.verb] = occurrence_index + 1
        current = _append_book_call(
            add,
            current,
            call,
            scope_label=scope.label,
            scope_orientation=scope.orientation,
            program_access_side=program_access_side,
            occurrence_index=occurrence_index,
        )

    if remainder:
        active_book_call_index = -1
        current = add(
            "boolean", "union", (remainder, current), {},
            verb="recompose_book_scope",
        )

    book_result = current
    if terminal_suffix:
        relation_input = book_result
        relation_rewrites: dict[str, str] = {}
        for relation_node in terminal_suffix:
            relation_rewrites[relation_node.id] = relation_input
            relation_input = relation_node.id
        nodes = [
            replace(node, inputs=(relation_rewrites[node.id],))
            if node.id in relation_rewrites
            else node
            for node in nodes
        ]
        current = program_root

    metadata = {
        **program.metadata,
        "book_recursive_projection": {
            "active": True,
            "scope_label": scope.label,
            "scope_fraction": scope.requested_fraction,
            "scope_orientation": scope.orientation,
            "outward_direction_source": "oriented_p3_cell_volume_weighted_center",
            "ordered_verbs": [call.verb for call in calls],
            "geometry_authority": "recursive_manifold_ast",
            "parcel_coordinates_hardcoded": False,
            "application_order": (
                "base_body_then_book_scope_and_operations_then_program_relation_suffix"
                if terminal_suffix
                else "program_solid_then_book_scope_and_operations"
            ),
            "program_relation_suffix_node_ids": [node.id for node in terminal_suffix],
            "program_section_node_id": next((
                node.id for node in terminal_suffix if node.operator == "profiled_hall"
            ), ""),
            "parameter_projection": book_parameter_projection_evidence(
                tuple(call.verb for call in calls)
            ),
            "chassis_compatibility": chassis_compatibility,
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


def recursive_book_projection_evidence(
    program: GeometryProgram,
    bridge_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe the one BOOK projection that owns the final recursive mesh."""

    projection = program.metadata.get("book_recursive_projection")
    if not isinstance(projection, dict) or not projection.get("active"):
        return {}
    bridge = dict(bridge_evidence or {})
    label = str(projection.get("scope_label") or "1/1")
    orientation = str(projection.get("scope_orientation") or "long_axis")
    spec = book_base_volume_spec(label)
    book_nodes = [
        node for node in program.topological_nodes()
        if str((node.provenance or {}).get("source") or "") == "book_recursive_projection"
    ]
    selector = next((
        node for node in book_nodes
        if str((node.provenance or {}).get("book_verb") or "") == "select_book_scope"
        and node.operator == "book_base_volume"
    ), None)
    status = "materialized" if bridge.get("status") == "materialized" and selector is not None else "compile_failed"
    return {
        "schema_version": "arr.maas.program_book_projection.v2",
        "status": status,
        "geometry_authority": "recursive_manifold_ast",
        "legacy_source_projection_bypassed": True,
        "operations": list(projection.get("ordered_verbs") or ()),
        "scope": {
            "node_id": selector.id if selector is not None else "",
            "relation": "select_relative_volume",
            "base_volume_label": label,
            "requested_fraction": spec.fraction,
            "topology": spec.topology,
            "orientation": orientation,
        },
        "authoritative_program_hash": str(bridge.get("program_hash") or program.program_hash()),
        "authoritative_geometry_hash": str(bridge.get("geometry_hash") or ""),
        "projection_graph": {
            "schema_version": "arr.maas.book_projection_graph.v2",
            "nodes": [
                {
                    "node_id": node.id,
                    "inputs": list(node.inputs),
                    "operation": str((node.provenance or {}).get("book_verb") or node.operator),
                    "solid_operator": node.operator,
                    "book_call_index": int((node.provenance or {}).get("book_call_index", -1)),
                }
                for node in book_nodes
            ],
        },
    }


def _validate_projection_effect_budget(
    program: GeometryProgram,
    calls: tuple[VerbCall, ...],
    *,
    scope_fraction: float,
) -> None:
    """Reject a BOOK/body pairing that repeats one dominant effect blindly.

    Every one of the 69 executable BOOK principles remains valid on a neutral base.
    This check is contextual: if the authored body already contains the same
    high-impact controller, a full-volume projection may not stack it again;
    a local p.3 scope may repeat it once, but never create a third identical
    controller.  The rule is typed and transferable, not a completed-form
    blacklist or a parcel-specific recipe.
    """
    existing_counts: dict[str, int] = {}
    for node in program.topological_nodes():
        if (
            node.kind in {"primitive", "boolean", "composition"}
            or node.semantic_role == "base_seed"
            or str((node.provenance or {}).get("source") or "") == "normalized_base_seed_catalog"
        ):
            continue
        effect = _CANONICAL_OPERATOR_EFFECT.get(node.operator, node.operator)
        existing_counts[effect] = existing_counts.get(effect, 0) + 1
    book_counts: dict[str, int] = {}
    for call in calls:
        effect = _BOOK_VERB_CANONICAL_EFFECT.get(call.verb, call.verb)
        book_counts[effect] = book_counts.get(effect, 0) + 1
    existing_relational_field = any(
        node.operator in {"cross_mass", "grid_mass", "radial_array", "split_wing", "related_array"}
        for node in program.topological_nodes()
    )
    if existing_relational_field and any(
        book_counts.get(effect, 0) >= 2 for effect in ("bend", "twist", "shear")
    ):
        raise ValueError(
            "incompatible_book_effect_stack:repeated_nonlinear_deformation_on_relational_field"
        )
    full_scope = float(scope_fraction) >= 1.0 - 1e-9
    for effect, added_count in book_counts.items():
        existing_count = existing_counts.get(effect, 0)
        if existing_count <= 0:
            continue
        maximum = 1 if full_scope else 2
        if existing_count + added_count > maximum:
            raise ValueError(
                "incompatible_book_effect_stack:"
                f"{effect}:existing={existing_count}:book={added_count}:scope={scope_fraction:.4f}"
            )


def _append_book_call(
    add,
    current: str,
    call: VerbCall,
    *,
    scope_label: str,
    scope_orientation: str,
    program_access_side: str = "closed",
    occurrence_index: int = 0,
) -> str:
    verb = call.verb
    p = dict(call.params)
    axis = _axis(p.get("axis"))
    outward_sign = book_base_volume_outward_sign(scope_label, scope_orientation, axis)
    # In the architectural language a vertical p.3 selection followed by
    # EXTRUDE means height growth.  Preserve that semantic relation explicitly
    # instead of forcing every compiler probe into the legacy x/y plan axes.
    # No world coordinate or finished geometry is introduced.
    if verb == "extrude" and scope_orientation == "vertical":
        axis = "z"
    amount = _number(p, "factor", _number(p, "ratio", 0.5))
    angle = _number(p, "angle", 28.0)

    if verb == "expand":
        return add("macro", "boundary_expand", (current,), {
            "axis": axis,
            "amount": amount,
            "shoulder_fraction": 0.38,
        }, verb=verb)
    if verb in {"extrude", "compress"}:
        if verb == "extrude":
            scale = 1.0 + 0.55 * _number(p, "length", 0.5)
            operation_axis = axis
        else:
            scale = max(0.20, min(0.92, amount))
            operation_axis = {
                "long_axis": "x",
                "short_axis": "y",
                "vertical": "z",
            }.get(scope_orientation, axis)
        vector = [1.0, 1.0, 1.0]
        vector[{"x": 0, "y": 1, "z": 2}[operation_axis]] = scale
        return add("transform", "scale", (current,), {"vector": vector, "pivot": "center"}, verb=verb)
    if verb == "inflate":
        return add("modifier", "inflate", (current,), {
            "axis": "z", "middle_scale": 1.08 + 0.32 * amount, "subdivisions": 4,
        }, verb=verb)
    if verb == "pinch":
        pinch_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        return add("modifier", "pinch", (current,), {
            "axis": pinch_axis,
            "waist_scale": _number(p, "waist_ratio", 0.62),
            "profile_power": project_book_parameter(
                verb, "depth_ratio", _number(p, "depth_ratio", 0.50)
            ),
            "subdivisions": 4,
        }, verb=verb)
    if verb == "bend":
        return add("modifier", "bend", (current,), {
            "axis": axis, "angle_degrees": angle, "subdivisions": 4,
        }, verb=verb)
    if verb == "twist":
        twist_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        return add("modifier", "twist", (current,), {
            "axis": twist_axis, "angle_degrees": angle, "subdivisions": 2,
        }, verb=verb)
    if verb == "skew":
        shear_amount = max(-0.38, min(0.38, tan(radians(angle)) * 0.45))
        return add("transform", "shear", (current,), {
            "axis": axis, "direction": "z", "amount": shear_amount, "pivot": "center",
        }, verb=verb)
    if verb == "shear":
        slope = tan(radians(max(-52.0, min(52.0, angle))))
        shear_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        normal = {
            "x": [1.0, 0.0, -slope],
            "y": [0.0, 1.0, -slope],
            "z": [slope, 0.0, 1.0],
        }[shear_axis]
        return add("modifier", "slice", (current,), {
            "normal": normal,
            "offset_ratio": project_book_parameter(verb, "angle", angle),
            "keep_side": "positive",
        }, verb=verb)
    if verb == "grade":
        grade_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        return add("macro", "book_grade", (current,), {
            "axis": grade_axis,
            "outward_sign": book_base_volume_outward_sign(
                scope_label, scope_orientation, grade_axis
            ),
            "face_side": str(p.get("side") or "east").lower(),
            "levels": 4,
            "width_ratio": project_book_parameter(
                verb, "width_ratio", _number(p, "width_ratio", 0.56)
            ),
            "depth_ratio": project_book_parameter(
                verb, "depth_ratio", _number(p, "depth_ratio", 0.40)
            ),
        }, verb=verb)
    if verb == "taper":
        end_x = _number(p, "x_ratio", max(0.38, 0.92 - 0.42 * amount))
        end_y = _number(p, "y_ratio", max(0.38, 0.92 - 0.28 * amount))
        taper_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        return add("modifier", "taper", (current,), {
            "axis": taper_axis, "start_scale": [1.0, 1.0],
            "end_scale": [end_x, end_y], "subdivisions": 3,
        }, verb=verb)
    if verb == "embed":
        embed_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        return add("macro", "embed_void", (current,), {
            "axis": embed_axis,
            "outward_sign": book_base_volume_outward_sign(
                scope_label, scope_orientation, embed_axis
            ),
            "guest_scale": _number(p, "guest_scale", 0.34),
            "position": str(p.get("position") or "center"),
            "embedded_ratio": project_book_parameter(
                verb, "distance_ratio", _number(p, "distance_ratio", 0.12)
            ),
        }, verb=verb)
    if verb == "carve":
        carve_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        side = str(p.get("side") or "").strip().lower()
        carve_sign = book_base_volume_outward_sign(
            scope_label, scope_orientation, carve_axis
        )
        return add("macro", "book_carve", (current,), {
            "axis": carve_axis,
            "outward_sign": carve_sign,
            "face_side": side or "east",
            "width_ratio": project_book_parameter(
                verb, "width_ratio", _number(p, "width_ratio", 0.42)
            ),
            "depth_ratio": project_book_parameter(
                verb, "depth_ratio", _number(p, "depth_ratio", 0.28)
            ),
        }, verb=verb)
    if verb == "notch":
        notch_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        return add("macro", "book_notch", (current,), {
            "axis": notch_axis,
            "outward_sign": book_base_volume_outward_sign(
                scope_label, scope_orientation, notch_axis
            ),
            "corner": str(p.get("corner") or "ne").lower(),
            "ratio": project_book_parameter(
                verb, "ratio", _number(p, "ratio", 0.24)
            ),
        }, verb=verb)
    if verb == "extract":
        extract_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        return add("macro", "book_extract", (current,), {
            "axis": extract_axis,
            "outward_sign": book_base_volume_outward_sign(
                scope_label, scope_orientation, extract_axis
            ),
            "face_side": str(p.get("side") or "east").lower(),
            "guest_scale": project_book_parameter(
                verb, "ratio", _number(p, "ratio", 0.30)
            ),
            "distance_ratio": project_book_parameter(
                verb, "distance_ratio", _number(p, "distance_ratio", 0.12)
            ),
        }, verb=verb)
    if verb == "nest":
        return add("macro", "nested_related", (current,), {
            "axis": axis,
            "distance_ratio": 0.0,
            "unit_scale": _number(p, "inner_scale", 0.50),
        }, verb=verb)
    if verb == "inscribe":
        inner = _number(p, "ratio", 0.5)
        margin = max(0.10, min(0.42, (1.0 - inner) / 2.0))
        return add("macro", "courtyard", (current,), {
            "margin_ratio": margin,
            "open_side": str(p.get("open_side") or "closed"),
        }, verb=verb)
    if verb == "puncture":
        raw_ratio = _number(p, "ratio", 0.35)
        return add("macro", "puncture", (current,), {
            "axis": axis, "count": int(round(_number(p, "n", 2))),
            "ratio": project_book_parameter(verb, "ratio", raw_ratio),
            "spacing_ratio": _number(p, "spacing_ratio", 0.24),
        }, verb=verb)
    if verb == "join":
        return add("macro", "join_related", (current,), {
            "bridge_ratio": _number(p, "bridge_ratio", 0.24),
        }, verb=verb)
    if verb == "split":
        access_bound = program_access_side in {"east", "west", "north", "south"}
        bridge_ratio = _number(p, "bridge_ratio", 0.28)
        split_gap = project_book_split_gap_ratio(
            _number(p, "gap_ratio", 0.16)
        )
        transverse_axis = "y" if axis == "x" else "x"
        return add("macro", "book_split", (current,), {
            "axis": axis,
            "gap_ratio": split_gap,
            # BOOK p.16 keeps one trunk and opens only the terminal portion.
            # Its bridge variation therefore controls the retained trunk,
            # rather than adding a separate connector after a full cut.
            "terminal_ratio": max(0.28, min(0.76, 1.0 - bridge_ratio)),
            # Gap controls the angular displacement of the child volume.  It
            # does not become an empty cosmetic slot.
            "angle_degrees": max(8.0, min(38.0, split_gap * 72.0)),
            "outward_sign": outward_sign,
            "branch_sign": book_base_volume_outward_sign(
                scope_label, scope_orientation, transverse_axis
            ),
            # A repeated Split recursively divides one existing terminal
            # child (p.40).  Generation zero targets the whole end; later
            # generations target successively nested half-width branches.
            "split_generation": occurrence_index,
            "access_side": program_access_side if access_bound else "closed",
        }, verb=verb)
    if verb == "fracture":
        fracture_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        return add("macro", "book_fracture", (current,), {
            "axis": fracture_axis,
            "outward_sign": book_base_volume_outward_sign(
                scope_label, scope_orientation, fracture_axis
            ),
            "gap_ratio": project_book_parameter(
                verb, "gap_ratio", _number(p, "gap_ratio", 0.16)
            ),
            "angle_degrees": max(12.0, min(55.0, abs(angle))),
            "retained_back_ratio": book_relation_invariant(
                verb, "retained_back_ratio"
            ),
        }, verb=verb)
    if verb == "lift":
        lift_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, axis)
        return add("macro", "book_lift", (current,), {
            "axis": lift_axis,
            "outward_sign": book_base_volume_outward_sign(
                scope_label, scope_orientation, lift_axis
            ),
            "guest_scale": project_book_parameter(
                verb, "guest_scale", _number(p, "guest_scale", 0.55)
            ),
            "distance_ratio": project_book_parameter(
                verb, "distance_ratio", _number(p, "distance_ratio", 0.0)
            ),
        }, verb=verb)
    if verb == "branch":
        return add("macro", "book_branch", (current,), {
            "angle_degrees": max(18.0, min(52.0, abs(angle))),
            "trunk_ratio": _number(p, "trunk_ratio", 0.42),
            "arm_ratio": _number(p, "arm_ratio", 0.28),
        }, verb=verb)
    if verb == "merge":
        return add("macro", "merge_related", (current,), {
            "axis": axis,
            "gap_ratio": _number(p, "gap_ratio", 0.22),
            "unit_scale": _number(p, "unit_scale", 0.42),
        }, verb=verb)
    if verb == "interlock":
        return add("macro", "interlock_related", (current,), {
            "axis": axis,
            "outward_sign": outward_sign,
            "angle_degrees": angle,
            "bar_ratio": project_book_parameter(
                verb, "bar_ratio", _number(p, "bar_ratio", 0.28)
            ),
            "distance_ratio": project_book_parameter(
                verb, "distance_ratio", _number(p, "distance_ratio", 0.0)
            ),
        }, verb=verb)
    if verb == "overlap":
        return add("macro", "overlap_related", (current,), {
            "axis": axis,
            "outward_sign": outward_sign,
            "slab_ratio": _number(p, "slab_ratio", 0.56),
            "shift_ratio": _number(p, "shift_ratio", 0.0),
            "vertical_overlap": _number(p, "vertical_overlap", 0.18),
        }, verb=verb)
    if verb == "intersect":
        factor = _number(p, "factor", 0.50)
        return add("macro", "intersect_related", (current,), {
            "axis": axis,
            "angle_degrees": angle,
            "bar_ratio": max(0.18, min(0.52, factor)),
            "unit_scale": project_book_parameter(
                verb, "factor", factor
            ),
        }, verb=verb)
    if verb == "rotate":
        rotation_axis = {
            "long_axis": "x",
            "short_axis": "y",
            "vertical": "z",
        }.get(scope_orientation, "x")
        return add("macro", "book_rotate", (current,), {
            "axis": rotation_axis,
            "angle_degrees": angle,
            "related_ratio": max(0.28, min(0.78, _number(p, "factor", 0.50))),
            "outward_sign": book_base_volume_outward_sign(
                scope_label, scope_orientation, rotation_axis
            ),
        }, verb=verb)
    if verb in {"offset", "shift", "lodge"}:
        distance = _number(p, "distance_ratio", 0.18)
        if verb == "shift":
            return add("macro", "shift_related", (current,), {
                "axis": axis,
                "outward_sign": outward_sign,
                "distance_ratio": project_book_parameter(
                    verb, "distance_ratio", distance
                ),
                "split_ratio": book_relation_invariant(verb, "split_ratio"),
            }, verb=verb)
        if verb == "offset":
            return add("macro", "nested_related", (current,), {
                "axis": axis,
                "distance_ratio": distance,
                "unit_scale": _number(p, "other_scale", 0.42),
            }, verb=verb)
        return add("macro", "book_lodge", (current,), {
            "axis": axis,
            "outward_sign": outward_sign,
            "distance_ratio": distance,
            "guest_scale": _number(p, "guest_scale", 0.42),
        }, verb=verb)
    if verb in {"array", "pack"}:
        count = max(2, min(4, int(round(_number(p, "n", 3)))))
        return add("macro", "related_array", (current,), {
            "mode": verb,
            "axis": axis,
            "count": count,
            "spacing_ratio": max(0.08, min(0.50, _number(p, "spacing_ratio", 0.18))),
            "unit_scale": max(0.60, min(0.82, _number(p, "unit_scale", 0.66))),
            "stagger_ratio": max(0.0, min(0.28, _number(p, "stagger_ratio", 0.08))),
        }, verb=verb)
    if verb == "reflect":
        normal = [1.0, 0.0, 0.0] if axis == "x" else [0.0, 1.0, 0.0]
        return add("pattern", "mirror_array", (current,), {"normal": normal, "pivot": "center"}, verb=verb)
    if verb == "stack":
        levels = max(2, min(4, int(round(_number(p, "levels", 3)))))
        return add("macro", "stepped_mass", (current,), {
            "levels": levels,
            "setback_ratio": _stack_setback_ratio(
                levels=levels,
                upper_ratio=_number(p, "upper_ratio", 1.0),
            ),
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


def _stack_setback_ratio(*, levels: int, upper_ratio: float) -> float:
    """Invert the compiler's linear level scale from the BOOK top ratio."""

    bounded_upper = max(0.18, min(0.95, float(upper_ratio)))
    return max(0.0, min(0.32, (1.0 - bounded_upper) / max(levels - 1, 1)))


def _corner_for_side(value: Any) -> str:
    return {"north": "ne", "south": "sw", "east": "se", "west": "nw"}.get(str(value or "east"), "se")


__all__ = [
    "apply_book_projection_to_geometry_program",
    "apply_capacity_composition_to_geometry_program",
    "recursive_book_projection_evidence",
]
