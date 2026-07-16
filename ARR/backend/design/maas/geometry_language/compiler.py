"""Manifold-backed compiler for recursive architectural geometry programs."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from math import atan2, cos, degrees, hypot, pi, radians, sin
from typing import Any, Callable

import numpy as np

from .ast import GeometryIssue, GeometryNode, GeometryProgram

try:
    import manifold3d as m3d
except ImportError:  # pragma: no cover - exercised as an explicit compile failure
    m3d = None


@dataclass(frozen=True)
class CompilationResult:
    program: GeometryProgram
    status: str
    vertices: tuple[tuple[float, float, float], ...] = ()
    triangles: tuple[tuple[int, int, int], ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)
    trace: tuple[dict[str, Any], ...] = ()
    issues: tuple[GeometryIssue, ...] = ()
    geometry_hash: str = ""
    _solid: Any = field(default=None, repr=False, compare=False)

    def to_dict(self, *, include_mesh: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": "arr.maas.geometry_compilation.v1",
            "status": self.status,
            "program_hash": self.program.program_hash() if not self.issues else "",
            "geometry_hash": self.geometry_hash,
            "metrics": self.metrics,
            "trace": list(self.trace),
            "issues": [issue.to_dict() for issue in self.issues],
        }
        if include_mesh:
            payload["mesh"] = {
                "vertices": [list(vertex) for vertex in self.vertices],
                "triangles": [list(face) for face in self.triangles],
            }
        return payload


class GeometryCompileError(RuntimeError):
    def __init__(self, code: str, message: str, node_id: str = "") -> None:
        super().__init__(message)
        self.issue = GeometryIssue(code, message, node_id)


def compile_geometry_program(program: GeometryProgram) -> CompilationResult:
    issues = tuple(issue for issue in program.validate() if issue.severity == "error")
    if issues:
        return CompilationResult(program, "invalid_program", issues=issues)
    if m3d is None:
        return CompilationResult(
            program,
            "kernel_unavailable",
            issues=(GeometryIssue("kernel_unavailable", "manifold3d>=3.4 is required"),),
        )
    cache: dict[str, Any] = {}
    trace: list[dict[str, Any]] = []
    node_map = program.node_map

    def evaluate(node_id: str):
        if node_id in cache:
            return cache[node_id]
        node = node_map[node_id]
        inputs = [evaluate(input_id) for input_id in node.inputs]
        try:
            solid, expansion = _evaluate_node(node, inputs)
        except GeometryCompileError:
            raise
        except Exception as exc:
            raise GeometryCompileError("operator_exception", f"{type(exc).__name__}: {exc}", node.id) from exc
        if solid is None or solid.is_empty():
            raise GeometryCompileError("empty_operator_result", f"{node.operator} returned an empty solid", node.id)
        status = str(solid.status())
        if "NoError" not in status:
            raise GeometryCompileError("kernel_error", status, node.id)
        cache[node_id] = solid
        trace.append({
            "node_id": node.id,
            "kind": node.kind,
            "operator": node.operator,
            "input_ids": list(node.inputs),
            "triangle_count": int(solid.num_tri()),
            "volume": round(float(solid.volume()), 6),
            "macro_expansion": expansion,
        })
        return solid

    try:
        solid = evaluate(program.root_id)
        mesh = solid.to_mesh64()
        raw_vertices = np.asarray(mesh.vert_properties, dtype=float)[:, :3]
        raw_triangles = np.asarray(mesh.tri_verts, dtype=np.int64)
        vertices = tuple(tuple(round(float(value), 8) for value in row) for row in raw_vertices)
        triangles = tuple(tuple(int(value) for value in row) for row in raw_triangles)
        bounds = tuple(float(value) for value in solid.bounding_box())
        components = tuple(solid.decompose())
        component_volumes = tuple(sorted(
            (max(0.0, float(component.volume())) for component in components),
            reverse=True,
        ))
        total_component_volume = max(sum(component_volumes), 1e-12)
        component_volume_ratios = tuple(
            round(value / total_component_volume, 6)
            for value in component_volumes
        )
        metrics = {
            "kernel": "manifold3d",
            "kernel_status": str(solid.status()),
            "watertight": True,
            "manifold": True,
            "closed_solid": True,
            "self_intersection_checked_by_kernel": True,
            "volume": round(float(solid.volume()), 6),
            "surface_area": round(float(solid.surface_area()), 6),
            "vertex_count": int(solid.num_vert()),
            "triangle_count": int(solid.num_tri()),
            "component_count": len(components),
            "component_volume_ratios": list(component_volume_ratios),
            "minimum_component_volume_ratio": min(component_volume_ratios, default=1.0),
            "genus": int(solid.genus()),
            "bounds": [
                [round(bounds[0], 6), round(bounds[1], 6), round(bounds[2], 6)],
                [round(bounds[3], 6), round(bounds[4], 6), round(bounds[5], 6)],
            ],
        }
        return CompilationResult(
            program=program,
            status="compiled",
            vertices=vertices,
            triangles=triangles,
            metrics=metrics,
            trace=tuple(trace),
            geometry_hash=_mesh_hash(vertices, triangles),
            _solid=solid,
        )
    except GeometryCompileError as exc:
        return CompilationResult(program, "compile_failed", trace=tuple(trace), issues=(exc.issue,))


def _evaluate_node(node: GeometryNode, inputs: list[Any]) -> tuple[Any, list[str]]:
    if node.kind == "primitive":
        return _primitive(node), []
    if node.kind == "transform":
        return _transform(node, inputs[0]), []
    if node.kind == "modifier":
        return _modifier(node, inputs[0]), []
    if node.kind == "boolean":
        return _boolean(node.operator, inputs), []
    if node.kind == "pattern":
        return _pattern(node, inputs[0]), []
    if node.kind == "composition":
        return _composition(node, inputs), []
    if node.kind == "macro":
        solid, expansion = _macro(node, inputs)
        return solid, expansion
    raise GeometryCompileError("unknown_node_kind", node.kind, node.id)


def _primitive(node: GeometryNode):
    p = node.parameters
    if node.operator == "box":
        return m3d.Manifold.cube((_number(p, "width"), _number(p, "depth"), _number(p, "height")), center=bool(p.get("center", False)))
    if node.operator == "cylinder":
        return m3d.Manifold.cylinder(
            _number(p, "height"),
            _number(p, "radius", p.get("radius_low", 1.0)),
            _number(p, "radius_high", p.get("radius", p.get("radius_low", 1.0))),
            circular_segments=max(8, min(96, int(p.get("segments", 24)))),
            center=bool(p.get("center", False)),
        )
    if node.operator == "extruded_polygon":
        points = _points(p.get("points"), dimensions=2, minimum=3, node_id=node.id)
        contours = [points]
        for hole in p.get("holes") or []:
            contours.append(_points(hole, dimensions=2, minimum=3, node_id=node.id))
        section = m3d.CrossSection(contours)
        return section.extrude(_number(p, "height"), n_divisions=max(0, min(16, int(p.get("divisions", 0)))))
    if node.operator == "wedge":
        width, depth = _number(p, "width"), _number(p, "depth")
        h0, h1 = _number(p, "start_height"), _number(p, "end_height")
        points = [(0, 0, 0), (width, 0, 0), (width, depth, 0), (0, depth, 0)]
        points += [(0, 0, h0), (0, depth, h0), (width, 0, h1), (width, depth, h1)]
        return m3d.Manifold.hull_points(points)
    if node.operator == "sweep":
        path = _points(p.get("path"), dimensions=None, minimum=2, node_id=node.id)
        path3 = [(point[0], point[1], point[2] if len(point) > 2 else 0.0) for point in path]
        return _sweep_path(
            path3,
            width=_number(p, "profile_width", p.get("width", 2.0)),
            height=_number(p, "profile_height", p.get("height", 3.0)),
        )
    if node.operator == "loft":
        return _loft_profiles(p.get("profiles"), node_id=node.id)
    raise GeometryCompileError("unsupported_primitive", node.operator, node.id)


def _transform(node: GeometryNode, solid):
    p = node.parameters
    pivot_raw = p.get("pivot", (0.0, 0.0, 0.0))
    pivot = _center(solid) if str(pivot_raw).lower() in {"center", "centroid"} else _vector(pivot_raw, 3, node.id)
    if node.operator == "translate":
        return solid.translate(_vector(p.get("vector", (p.get("x", 0), p.get("y", 0), p.get("z", 0))), 3, node.id))
    if node.operator == "rotate":
        angles = p.get("angles")
        if angles is None:
            axis = str(p.get("axis") or "z").lower()
            value = float(p.get("angle_degrees", p.get("angle", 0.0)))
            angles = (value if axis == "x" else 0.0, value if axis == "y" else 0.0, value if axis == "z" else 0.0)
        return _around_pivot(solid, pivot, lambda item: item.rotate(_vector(angles, 3, node.id)))
    if node.operator == "scale":
        value = p.get("vector", p.get("scale", (1.0, 1.0, 1.0)))
        if isinstance(value, (int, float)):
            value = (float(value),) * 3
        scale = _vector(value, 3, node.id)
        if min(abs(item) for item in scale) <= 1e-6:
            raise GeometryCompileError("degenerate_scale", "scale components must be non-zero", node.id)
        return _around_pivot(solid, pivot, lambda item: item.scale(scale))
    if node.operator == "mirror":
        normal = _vector(p.get("normal", (1.0, 0.0, 0.0)), 3, node.id)
        return _around_pivot(solid, pivot, lambda item: item.mirror(normal))
    if node.operator == "shear":
        amount = float(p.get("amount", 0.0))
        axis = str(p.get("axis") or "x").lower()
        direction = str(p.get("direction") or "z").lower()
        matrix = np.eye(3, 4, dtype=float)
        row = {"x": 0, "y": 1, "z": 2}.get(axis)
        column = {"x": 0, "y": 1, "z": 2}.get(direction)
        if row is None or column is None or row == column:
            raise GeometryCompileError("invalid_shear_axes", "shear axis and direction must differ", node.id)
        matrix[row, column] = amount
        return _around_pivot(solid, pivot, lambda item: item.transform(matrix.tolist()))
    raise GeometryCompileError("unsupported_transform", node.operator, node.id)


def _modifier(node: GeometryNode, solid):
    p = node.parameters
    if node.operator == "taper":
        return _warp_taper(solid, p, node.id)
    if node.operator == "twist":
        return _warp_twist(solid, p, node.id)
    if node.operator == "bend":
        return _warp_bend(solid, p, node.id)
    if node.operator == "pinch":
        return _warp_mid_profile(solid, p, node.id, mode="pinch")
    if node.operator == "inflate":
        return _warp_mid_profile(solid, p, node.id, mode="inflate")
    if node.operator in {"slice", "clip"}:
        normal = np.asarray(_vector(p.get("normal"), 3, node.id), dtype=float)
        normal /= max(float(np.linalg.norm(normal)), 1e-12)
        keep_negative = str(p.get("keep_side") or "positive").lower() in {"negative", "below", "back"}
        offset = float(p.get("offset", 0.0))
        if keep_negative:
            normal = -normal
            offset = -offset
        if p.get("offset_ratio") is not None:
            # Agent-authored cuts operate in normalized live-solid space. An
            # absolute plane offset made the same graph erase most of a slab
            # while barely touching a block.  After orienting the kept side,
            # trim a bounded fraction from the negative projection extreme.
            cut_ratio = max(0.02, min(0.45, float(p.get("offset_ratio"))))
            minx, miny, minz, maxx, maxy, maxz = _bounds(solid)
            projections = [
                float(np.dot(normal, np.asarray((x, y, z), dtype=float)))
                for x in (minx, maxx)
                for y in (miny, maxy)
                for z in (minz, maxz)
            ]
            offset = min(projections) + (max(projections) - min(projections)) * cut_ratio
        return solid.trim_by_plane(tuple(normal.tolist()), offset)
    if node.operator == "clip_fraction":
        return _clip_fraction(solid, p, node.id)
    if node.operator == "cut_corner":
        return _cut_corner(solid, p, node.id)
    raise GeometryCompileError("unsupported_modifier", node.operator, node.id)


def _boolean(operator: str, inputs: list[Any]):
    op = {
        "union": m3d.OpType.Add,
        "difference": m3d.OpType.Subtract,
        "intersection": m3d.OpType.Intersect,
    }[operator]
    return m3d.Manifold.batch_boolean(inputs, op)


def _pattern(node: GeometryNode, solid):
    p = node.parameters
    count = max(1, min(24, int(p.get("count", 2))))
    copies: list[Any] = []
    if node.operator in {"duplicate", "linear_array"}:
        vector = _vector(p.get("vector", (p.get("spacing", 2.0), 0.0, 0.0)), 3, node.id)
        copies = [solid.translate(tuple(value * index for value in vector)) for index in range(count)]
    elif node.operator == "stack":
        spacing = float(p.get("spacing", _bounds(solid)[5] - _bounds(solid)[2]))
        shift = _vector(p.get("shift_per_level", (0.0, 0.0, 0.0)), 3, node.id)
        copies = [solid.translate((shift[0] * index, shift[1] * index, spacing * index + shift[2] * index)) for index in range(count)]
    elif node.operator == "radial_array":
        total = float(p.get("total_angle_degrees", p.get("angle_degrees", 180.0)))
        pivot_raw = p.get("pivot", (0.0, 0.0, 0.0))
        pivot = _center(solid) if str(pivot_raw).lower() in {"center", "centroid"} else _vector(pivot_raw, 3, node.id)
        step = total / max(count - 1, 1)
        copies = [_around_pivot(solid, pivot, lambda item, angle=step * index: item.rotate((0.0, 0.0, angle))) for index in range(count)]
    elif node.operator == "mirror_array":
        normal = _vector(p.get("normal", (1.0, 0.0, 0.0)), 3, node.id)
        pivot_raw = p.get("pivot", (0.0, 0.0, 0.0))
        pivot = _center(solid) if str(pivot_raw).lower() in {"center", "centroid"} else _vector(pivot_raw, 3, node.id)
        copies = [solid, _around_pivot(solid, pivot, lambda item: item.mirror(normal))]
    else:
        raise GeometryCompileError("unsupported_pattern", node.operator, node.id)
    return m3d.Manifold.batch_boolean(copies, m3d.OpType.Add)


def _composition(node: GeometryNode, inputs: list[Any]):
    if node.operator == "attach":
        return m3d.Manifold.batch_boolean(inputs, m3d.OpType.Add)
    if node.operator == "bridge":
        bridge = _bridge_between(inputs[0], inputs[1], node.parameters, node.id)
        return m3d.Manifold.batch_boolean([*inputs, bridge], m3d.OpType.Add)
    raise GeometryCompileError("unsupported_composition", node.operator, node.id)


def _macro(node: GeometryNode, inputs: list[Any]) -> tuple[Any, list[str]]:
    p = node.parameters
    base = inputs[0]
    operator = node.operator
    if operator in {"courtyard", "carve_void"}:
        if len(inputs) >= 2:
            cutter = inputs[1]
        else:
            minx, miny, minz, maxx, maxy, maxz = _bounds(base)
            margin = max(0.08, min(0.45, float(p.get("margin_ratio", p.get("margin", 0.22)))))
            cutter = m3d.Manifold.cube(((maxx - minx) * (1 - margin * 2), (maxy - miny) * (1 - margin * 2), maxz - minz + 2.0)).translate((minx + (maxx - minx) * margin, miny + (maxy - miny) * margin, minz - 1.0))
        return base - cutter, ["difference", "box_cutter"]
    if operator == "notch":
        minx, miny, minz, maxx, maxy, maxz = _bounds(base)
        ratio = max(0.08, min(0.48, float(p.get("ratio", 0.25))))
        corner = str(p.get("corner") or "ne").lower()
        width, depth, height = (maxx - minx) * ratio, (maxy - miny) * ratio, (maxz - minz) * max(0.1, min(1.2, float(p.get("height_ratio", 1.0))))
        x = maxx - width if "e" in corner else minx
        y = maxy - depth if "n" in corner else miny
        cutter = m3d.Manifold.cube((width, depth, height + 1.0)).translate((x, y, minz - 0.5))
        return base - cutter, ["difference", "corner_box_cutter"]
    if operator in {"setback", "stepped_mass", "terrace"}:
        return _stepped_macro(base, p, terrace=operator == "terrace"), ["slice", "scale", "translate", "union"]
    if operator == "cantilever":
        minx, miny, minz, maxx, maxy, maxz = _bounds(base)
        cut = minz + (maxz - minz) * max(0.1, min(0.9, float(p.get("start_ratio", 0.55))))
        upper = base.trim_by_plane((0.0, 0.0, 1.0), cut).translate(_vector(p.get("vector", (2.0, 0.0, 0.0)), 3, node.id))
        lower = base.trim_by_plane((0.0, 0.0, -1.0), -cut)
        return lower + upper, ["split_by_plane", "translate", "union"]
    if operator == "bridge":
        if len(inputs) < 2:
            raise GeometryCompileError("macro_requires_two_inputs", "bridge macro needs two wings", node.id)
        bridge = _bridge_between(inputs[0], inputs[1], p, node.id)
        return m3d.Manifold.batch_boolean([inputs[0], inputs[1], bridge], m3d.OpType.Add), ["beam_between", "union"]
    if operator == "cross_mass":
        pivot = _center(base)
        other = _around_pivot(base, pivot, lambda item: item.rotate((0.0, 0.0, float(p.get("angle_degrees", 90.0)))))
        return base + other, ["rotate", "union"]
    if operator == "bent_bar":
        return _warp_bend(base, p, node.id), ["refine", "bend_warp"]
    if operator == "split_wing":
        minx, miny, minz, maxx, maxy, maxz = _bounds(base)
        axis = str(p.get("axis") or "x").lower()
        gap = max(0.05, min(0.5, float(p.get("gap_ratio", 0.18))))
        if axis == "y":
            size = (maxx - minx + 2, (maxy - miny) * gap, maxz - minz + 2)
            origin = (minx - 1, (miny + maxy - size[1]) / 2, minz - 1)
        else:
            size = ((maxx - minx) * gap, maxy - miny + 2, maxz - minz + 2)
            origin = ((minx + maxx - size[0]) / 2, miny - 1, minz - 1)
        split = base - m3d.Manifold.cube(size).translate(origin)
        parts = split.decompose()
        additions = []
        expansion = ["difference", "decompose"]
        if bool(p.get("ground_spine", False)) and len(parts) >= 2:
            # A long-span wing pair needs an occupiable service/entry spine,
            # not two almost-disconnected bars held together only by a small
            # roof bridge.  The relation stays normalized to the live solid
            # bounds and is therefore transferable across parcels.  Upper
            # wings remain visually split while the low spine improves role
            # coverage, coherence and downstream geometry retention.
            left, right = parts[0], parts[1]
            left_center, right_center = _center(left), _center(right)
            short_span = (maxy - miny) if axis == "x" else (maxx - minx)
            height_span = max(maxz - minz, 1e-7)
            spine_width = short_span * max(0.18, min(0.72, float(p.get("ground_spine_width_ratio", 0.38))))
            spine_height = height_span * max(0.10, min(0.42, float(p.get("ground_spine_height_ratio", 0.22))))
            additions.append(_beam_between(
                (left_center[0], left_center[1], minz),
                (right_center[0], right_center[1], minz),
                width=spine_width,
                height=spine_height,
                node_id=node.id,
            ))
            expansion.append("ground_service_spine")
        if bool(p.get("bridge", False)) and len(parts) >= 2:
            additions.append(_bridge_between(parts[0], parts[1], p, node.id))
            expansion.append("upper_bridge")
        if additions:
            split = m3d.Manifold.batch_boolean([split, *additions], m3d.OpType.Add)
            return split, [*expansion, "union"]
        return split, ["difference", "gap_cutter"]
    if operator == "attach_volume":
        return m3d.Manifold.batch_boolean(inputs, m3d.OpType.Add), ["union"]
    if operator == "tapered_tower":
        return _warp_taper(base, p, node.id), ["taper_warp"]
    if operator == "leaning_tower":
        amount = float(p.get("amount", 0.18))
        direction = str(p.get("direction") or "x").lower()
        matrix = [[1.0, 0.0, amount if direction == "x" else 0.0, 0.0], [0.0, 1.0, amount if direction == "y" else 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]]
        return base.transform(matrix), ["shear"]
    if operator == "lift":
        minx, miny, minz, maxx, maxy, maxz = _bounds(base)
        height = max(maxz - minz, 1e-7)
        rise = height * max(0.08, min(0.45, float(p.get("rise_ratio", 0.22))))
        lifted = base.translate((0.0, 0.0, rise))
        support_ratio = max(0.04, min(0.18, float(p.get("support_ratio", 0.08))))
        support_width = max((maxx - minx) * support_ratio, 1e-5)
        support_depth = max((maxy - miny) * support_ratio, 1e-5)
        inset_x = (maxx - minx) * 0.16
        inset_y = (maxy - miny) * 0.16
        supports = [
            m3d.Manifold.cube((support_width, support_depth, rise + height * 0.08)).translate((x, y, minz))
            for x in (minx + inset_x, maxx - inset_x - support_width)
            for y in (miny + inset_y, maxy - inset_y - support_depth)
        ]
        return m3d.Manifold.batch_boolean([lifted, *supports], m3d.OpType.Add), ["translate", "support_array", "union"]
    if operator == "puncture":
        minx, miny, minz, maxx, maxy, maxz = _bounds(base)
        axis = str(p.get("axis") or "x").lower()
        count = max(1, min(3, int(p.get("count", p.get("n", 2)))))
        ratio = max(0.06, min(0.26, float(p.get("ratio", 0.14))))
        cutters = []
        if axis == "y":
            width = (maxx - minx) * ratio
            height = (maxz - minz) * ratio
            for index in range(count):
                t = (index + 1) / (count + 1)
                cutters.append(m3d.Manifold.cube((width, maxy - miny + 2.0, height)).translate((
                    minx + (maxx - minx) * t - width / 2.0, miny - 1.0,
                    minz + (maxz - minz) * 0.5 - height / 2.0,
                )))
        else:
            depth = (maxy - miny) * ratio
            height = (maxz - minz) * ratio
            for index in range(count):
                t = (index + 1) / (count + 1)
                cutters.append(m3d.Manifold.cube((maxx - minx + 2.0, depth, height)).translate((
                    minx - 1.0, miny + (maxy - miny) * t - depth / 2.0,
                    minz + (maxz - minz) * 0.5 - height / 2.0,
                )))
        cutter = m3d.Manifold.batch_boolean(cutters, m3d.OpType.Add)
        return base - cutter, ["cutter_array", "difference"]
    if operator == "cut_corner":
        return _cut_corner(base, p, node.id), ["half_space_intersection"]
    raise GeometryCompileError("unsupported_macro", operator, node.id)


def _warp_taper(solid, params: dict[str, Any], node_id: str):
    axis = str(params.get("axis") or "z").lower()
    axis_index = {"x": 0, "y": 1, "z": 2}.get(axis)
    if axis_index is None:
        raise GeometryCompileError("invalid_axis", axis, node_id)
    bounds = _bounds(solid)
    low, high = bounds[axis_index], bounds[axis_index + 3]
    length = max(high - low, 1e-9)
    start = params.get("start_scale", (1.0, 1.0))
    end = params.get("end_scale", params.get("scale_top", (0.6, 0.6)))
    start2 = _scale_pair(start)
    end2 = _scale_pair(end)
    center = _center(solid)
    pivot_raw = params.get("pivot")
    pivot = _vector(pivot_raw, 3, node_id) if pivot_raw is not None else center
    other = [index for index in range(3) if index != axis_index]
    refined = solid.refine(max(2, min(6, int(params.get("subdivisions", 3)))))

    def warp(points):
        result = np.asarray(points, dtype=float).copy()
        t = np.clip((result[:, axis_index] - low) / length, 0.0, 1.0)
        for pair_index, coordinate_index in enumerate(other):
            scale = start2[pair_index] + (end2[pair_index] - start2[pair_index]) * t
            result[:, coordinate_index] = pivot[coordinate_index] + (result[:, coordinate_index] - pivot[coordinate_index]) * scale
        return result

    return refined.warp_batch(warp)


def _warp_mid_profile(solid, params: dict[str, Any], node_id: str, *, mode: str):
    """Contract or swell the middle of one solid without changing topology."""
    axis = str(params.get("axis") or "x").lower()
    axis_index = {"x": 0, "y": 1, "z": 2}.get(axis)
    if axis_index is None:
        raise GeometryCompileError("invalid_axis", axis, node_id)
    bounds = _bounds(solid)
    low, high = bounds[axis_index], bounds[axis_index + 3]
    length = max(high - low, 1e-9)
    center = _center(solid)
    refined = solid.refine(max(2, min(6, int(params.get("subdivisions", 4)))))
    if mode == "pinch":
        middle_scale = max(0.28, min(0.92, float(params.get("waist_scale", params.get("waist_ratio", 0.62)))))
    else:
        middle_scale = max(1.04, min(1.45, float(params.get("middle_scale", params.get("factor", 1.18)))))
    power = max(1.0, min(4.0, float(params.get("profile_power", 2.0))))
    other = [index for index in range(3) if index != axis_index]

    def warp(points):
        result = np.asarray(points, dtype=float).copy()
        t = np.clip((result[:, axis_index] - low) / length, 0.0, 1.0)
        weight = np.sin(np.pi * t) ** power
        scale = 1.0 + (middle_scale - 1.0) * weight
        for coordinate_index in other:
            result[:, coordinate_index] = center[coordinate_index] + (
                result[:, coordinate_index] - center[coordinate_index]
            ) * scale
        return result

    return refined.warp_batch(warp)


def _warp_twist(solid, params: dict[str, Any], node_id: str):
    axis = str(params.get("axis") or "z").lower()
    if axis != "z":
        raise GeometryCompileError("unsupported_twist_axis", "twist currently uses the architectural vertical z axis", node_id)
    minx, miny, minz, maxx, maxy, maxz = _bounds(solid)
    height = max(maxz - minz, 1e-9)
    pivot = params.get("pivot")
    center = _vector(pivot, 3, node_id) if pivot is not None else ((minx + maxx) / 2, (miny + maxy) / 2, minz)
    angle = radians(float(params.get("angle_degrees", params.get("angle", 25.0))))
    refined = solid.refine(max(2, min(6, int(params.get("subdivisions", 3)))))

    def warp(points):
        result = np.asarray(points, dtype=float).copy()
        t = np.clip((result[:, 2] - minz) / height, 0.0, 1.0)
        theta = angle * t
        x, y = result[:, 0] - center[0], result[:, 1] - center[1]
        result[:, 0] = center[0] + x * np.cos(theta) - y * np.sin(theta)
        result[:, 1] = center[1] + x * np.sin(theta) + y * np.cos(theta)
        return result

    return refined.warp_batch(warp)


def _warp_bend(solid, params: dict[str, Any], node_id: str):
    axis = str(params.get("axis") or "x").lower()
    angle = radians(float(params.get("angle_degrees", params.get("angle", 35.0))))
    if abs(angle) < 1e-5:
        return solid
    minx, miny, minz, maxx, maxy, maxz = _bounds(solid)
    refined = solid.refine(max(2, min(7, int(params.get("subdivisions", 4)))))
    center = _center(solid)

    def warp(points):
        result = np.asarray(points, dtype=float).copy()
        if axis == "x":
            length = max(maxx - minx, 1e-9)
            theta = angle * np.clip((result[:, 0] - minx) / length, 0.0, 1.0)
            radius = length / angle
            local = result[:, 1] - center[1]
            result[:, 0] = minx + radius * np.sin(theta) - local * np.sin(theta)
            result[:, 1] = center[1] + radius * (1.0 - np.cos(theta)) + local * np.cos(theta)
        elif axis == "y":
            length = max(maxy - miny, 1e-9)
            theta = angle * np.clip((result[:, 1] - miny) / length, 0.0, 1.0)
            radius = length / angle
            local = result[:, 0] - center[0]
            result[:, 1] = miny + radius * np.sin(theta) - local * np.sin(theta)
            result[:, 0] = center[0] + radius * (1.0 - np.cos(theta)) + local * np.cos(theta)
        elif axis == "z":
            length = max(maxz - minz, 1e-9)
            theta = angle * np.clip((result[:, 2] - minz) / length, 0.0, 1.0)
            radius = length / angle
            local = result[:, 0] - center[0]
            result[:, 2] = minz + radius * np.sin(theta) - local * np.sin(theta)
            result[:, 0] = center[0] + radius * (1.0 - np.cos(theta)) + local * np.cos(theta)
        else:
            raise GeometryCompileError("invalid_axis", axis, node_id)
        return result

    return refined.warp_batch(warp)


def _cut_corner(solid, params: dict[str, Any], node_id: str):
    minx, miny, _minz, maxx, maxy, _maxz = _bounds(solid)
    distance = max(1e-4, float(params.get("distance", min(maxx - minx, maxy - miny) * float(params.get("ratio", 0.2)))))
    corner = str(params.get("corner") or "ne").lower()
    normals = {"ne": (-1.0, -1.0, 0.0), "nw": (1.0, -1.0, 0.0), "se": (-1.0, 1.0, 0.0), "sw": (1.0, 1.0, 0.0)}
    normal = np.asarray(normals.get(corner), dtype=float) if corner in normals else None
    if normal is None:
        raise GeometryCompileError("invalid_corner", corner, node_id)
    normal /= np.linalg.norm(normal)
    point = {
        "ne": (maxx - distance, maxy - distance, 0.0),
        "nw": (minx + distance, maxy - distance, 0.0),
        "se": (maxx - distance, miny + distance, 0.0),
        "sw": (minx + distance, miny + distance, 0.0),
    }[corner]
    offset = float(np.dot(normal, np.asarray(point)))
    return solid.trim_by_plane(tuple(normal.tolist()), offset)


def _clip_fraction(solid, params: dict[str, Any], node_id: str):
    """Select a normalized occupied-solid fraction along its live bounds."""
    fraction = max(0.01, min(1.0, float(params.get("fraction", 1.0))))
    if fraction >= 1.0 - 1e-9:
        return solid
    minx, miny, minz, maxx, maxy, maxz = _bounds(solid)
    lengths = [maxx - minx, maxy - miny, maxz - minz]
    raw_axis = str(params.get("axis") or "long").lower()
    if raw_axis == "long":
        axis = 0 if lengths[0] >= lengths[1] else 1
    elif raw_axis == "short":
        axis = 1 if lengths[0] >= lengths[1] else 0
    else:
        axis = {"x": 0, "y": 1, "z": 2, "vertical": 2}.get(raw_axis, -1)
    if axis < 0 or lengths[axis] <= 1e-9:
        raise GeometryCompileError("invalid_scope_axis", raw_axis, node_id)
    anchor = str(params.get("anchor") or "end").lower()
    selected_length = lengths[axis] * fraction
    lower = [minx, miny, minz]
    upper = [maxx, maxy, maxz]
    if anchor in {"start", "low", "negative"}:
        upper[axis] = lower[axis] + selected_length
    elif anchor in {"center", "middle"}:
        center = (lower[axis] + upper[axis]) / 2.0
        lower[axis] = center - selected_length / 2.0
        upper[axis] = center + selected_length / 2.0
    else:
        lower[axis] = upper[axis] - selected_length
    epsilon = max(max(lengths), 1.0) * 1e-5
    for index in range(3):
        if index != axis:
            lower[index] -= epsilon
            upper[index] += epsilon
    size = tuple(max(1e-7, upper[index] - lower[index]) for index in range(3))
    cutter = m3d.Manifold.cube(size).translate(tuple(lower))
    return m3d.Manifold.batch_boolean([solid, cutter], m3d.OpType.Intersect)


def _stepped_macro(base, params: dict[str, Any], *, terrace: bool):
    minx, miny, minz, maxx, maxy, maxz = _bounds(base)
    levels = max(2, min(10, int(params.get("levels", 4))))
    level_height = (maxz - minz) / levels
    setback = max(0.0, min(0.32, float(params.get("setback_ratio", 0.08))))
    direction = str(params.get("direction") or "x").lower()
    solids = []
    for index in range(levels):
        ratio = max(0.18, 1.0 - setback * index)
        width = (maxx - minx) * (ratio if not terrace or direction == "y" else 1.0)
        depth = (maxy - miny) * (ratio if not terrace or direction == "x" else 1.0)
        x = minx + ((maxx - minx - width) / 2 if not terrace or direction == "y" else (maxx - minx - width) * index / max(levels - 1, 1))
        y = miny + ((maxy - miny - depth) / 2 if not terrace or direction == "x" else (maxy - miny - depth) * index / max(levels - 1, 1))
        solids.append(m3d.Manifold.cube((width, depth, level_height)).translate((x, y, minz + index * level_height)))
    return m3d.Manifold.batch_boolean(solids, m3d.OpType.Add)


def _bridge_between(left, right, params: dict[str, Any], node_id: str):
    lc, rc = _center(left), _center(right)
    lb, rb = _bounds(left), _bounds(right)
    z = float(params.get("z", min(lb[5], rb[5]) * float(params.get("height_ratio", 0.65))))
    height = max(0.2, float(params.get("height", min(lb[5] - lb[2], rb[5] - rb[2]) * 0.14)))
    width = max(0.2, float(params.get("width", min(lb[4] - lb[1], rb[4] - rb[1]) * 0.24)))
    return _beam_between((lc[0], lc[1], z), (rc[0], rc[1], z), width=width, height=height, node_id=node_id)


def _sweep_path(path: list[tuple[float, float, float]], *, width: float, height: float):
    solids = [
        _beam_between(start, end, width=width, height=height, node_id="sweep")
        for start, end in zip(path, path[1:])
        if hypot(end[0] - start[0], end[1] - start[1]) > 1e-7
    ]
    if not solids:
        raise GeometryCompileError("degenerate_sweep_path", "sweep path has no measurable segments")
    return m3d.Manifold.batch_boolean(solids, m3d.OpType.Add)


def _beam_between(start, end, *, width: float, height: float, node_id: str):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = hypot(dx, dy)
    if length <= 1e-7:
        raise GeometryCompileError("degenerate_bridge", "bridge endpoints coincide", node_id)
    angle = degrees(atan2(dy, dx))
    overlap = min(width * 0.35, length * 0.08)
    beam = m3d.Manifold.cube((length + overlap * 2, width, height), center=True)
    beam = beam.rotate((0.0, 0.0, angle))
    return beam.translate(((start[0] + end[0]) / 2, (start[1] + end[1]) / 2, min(start[2], end[2]) + height / 2))


def _loft_profiles(raw_profiles: Any, *, node_id: str):
    if not isinstance(raw_profiles, list) or len(raw_profiles) < 2:
        raise GeometryCompileError("missing_profile", "loft needs at least two profiles", node_id)
    profiles: list[tuple[float, list[tuple[float, float]]]] = []
    for index, raw in enumerate(raw_profiles):
        if isinstance(raw, dict):
            z = float(raw.get("z", index))
            points = _points(raw.get("points"), dimensions=2, minimum=3, node_id=node_id)
        else:
            z = float(index)
            points = _points(raw, dimensions=2, minimum=3, node_id=node_id)
        profiles.append((z, [(point[0], point[1]) for point in points]))
    profiles.sort(key=lambda item: item[0])
    solids = []
    for (z0, lower), (z1, upper) in zip(profiles, profiles[1:]):
        if z1 <= z0:
            raise GeometryCompileError("non_monotonic_loft", "loft profile z values must increase", node_id)
        points3 = [(x, y, z0) for x, y in lower] + [(x, y, z1) for x, y in upper]
        segment = m3d.Manifold.hull_points(points3)
        if segment.is_empty():
            raise GeometryCompileError("invalid_loft_segment", "loft profiles are degenerate", node_id)
        solids.append(segment)
    return m3d.Manifold.batch_boolean(solids, m3d.OpType.Add)


def _around_pivot(solid, pivot: tuple[float, float, float], operation: Callable[[Any], Any]):
    return operation(solid.translate(tuple(-value for value in pivot))).translate(pivot)


def _bounds(solid) -> tuple[float, float, float, float, float, float]:
    return tuple(float(value) for value in solid.bounding_box())


def _center(solid) -> tuple[float, float, float]:
    minx, miny, minz, maxx, maxy, maxz = _bounds(solid)
    return ((minx + maxx) / 2, (miny + maxy) / 2, (minz + maxz) / 2)


def _number(params: dict[str, Any], key: str, default: Any = None) -> float:
    value = params.get(key, default)
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise GeometryCompileError("invalid_parameter_type", f"{key} must be numeric") from exc
    if result <= 0:
        raise GeometryCompileError("non_positive_dimension", f"{key} must be positive")
    return result


def _vector(value: Any, length: int, node_id: str) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise GeometryCompileError("invalid_vector", f"expected vector length {length}", node_id)
    try:
        return tuple(float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise GeometryCompileError("invalid_vector", "vector values must be numeric", node_id) from exc


def _points(value: Any, *, dimensions: int | None, minimum: int, node_id: str) -> list[tuple[float, ...]]:
    if not isinstance(value, list) or len(value) < minimum:
        raise GeometryCompileError("invalid_points", f"at least {minimum} points are required", node_id)
    result: list[tuple[float, ...]] = []
    for raw in value:
        if not isinstance(raw, (list, tuple)) or (dimensions is not None and len(raw) != dimensions) or len(raw) not in {2, 3}:
            raise GeometryCompileError("invalid_points", "point dimensions are invalid", node_id)
        result.append(tuple(float(item) for item in raw))
    return result


def _scale_pair(value: Any) -> tuple[float, float]:
    if isinstance(value, (int, float)):
        result = (float(value), float(value))
    elif isinstance(value, (list, tuple)) and len(value) >= 2:
        result = (float(value[0]), float(value[1]))
    else:
        raise GeometryCompileError("invalid_scale", "taper scale must be scalar or a two-vector")
    if min(result) <= 0.02 or max(result) > 4.0:
        raise GeometryCompileError("taper_scale_out_of_bounds", "taper scale must remain in 0.02..4")
    return result


def _mesh_hash(vertices: tuple[tuple[float, float, float], ...], triangles: tuple[tuple[int, int, int], ...]) -> str:
    canonical = []
    for face in triangles:
        points = sorted(tuple(round(value, 5) for value in vertices[index]) for index in face)
        canonical.append(points)
    canonical.sort()
    return hashlib.sha256(json.dumps(canonical, separators=(",", ":")).encode("utf-8")).hexdigest()


__all__ = ["CompilationResult", "GeometryCompileError", "compile_geometry_program"]
