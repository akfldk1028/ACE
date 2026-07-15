"""Agent-authored sectional monoliths with real through-void geometry.

Unlike a plan polygon loft, this field authors one elevation/section polygon
and optionally subtracts a second polygon before extruding the remaining
section through a bounded parcel depth.  Wedges, diagonal ground undercuts and
large elevated openings are therefore consequences of one generic solid/void
representation rather than named precedent templates.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, degrees, radians, sin
from typing import Any

from shapely.affinity import rotate
from shapely.geometry import MultiPolygon, Polygon


Point2 = tuple[float, float]
Point3 = tuple[float, float, float]


@dataclass(frozen=True)
class SectionalMonolithField:
    section_shape: Polygon
    outer_controls: tuple[Point2, ...]
    void_controls: tuple[Point2, ...]
    proxy_footprint: Polygon
    axis: str
    front_coordinate: float
    back_coordinate: float
    frame_angle_degrees: float
    frame_origin: Point2
    local_bounds: tuple[float, float, float, float]
    evidence: dict[str, Any]


def build_sectional_monolith_field(
    footprint: Polygon,
    params: dict[str, Any],
) -> SectionalMonolithField | None:
    outer = _controls(params.get("section_outer_control_points"), minimum=4)
    if not outer or footprint.is_empty or footprint.area <= 0:
        return None
    outer_polygon = Polygon(outer)
    if not outer_polygon.is_valid or outer_polygon.area < 0.16:
        return None

    void = _controls(params.get("section_void_control_points"), minimum=3)
    void_polygon = Polygon(void) if void else None
    section_shape = outer_polygon
    void_area = 0.0
    if void_polygon is not None:
        if not void_polygon.is_valid or void_polygon.area < 0.025:
            return None
        clipped_void = void_polygon.intersection(outer_polygon)
        if clipped_void.is_empty or clipped_void.area < 0.025:
            return None
        section_shape = outer_polygon.difference(clipped_void)
        void_area = float(clipped_void.area)
    if isinstance(section_shape, MultiPolygon) or not isinstance(section_shape, Polygon):
        return None
    if section_shape.is_empty or not section_shape.is_valid or section_shape.area < 0.10:
        return None

    axis = str(params.get("axis") or "x").strip().lower()
    axis = axis if axis in {"x", "y"} else "x"
    depth_ratio = _number(params.get("section_depth_ratio"), 0.72, 0.28, 0.94)
    depth_shift = _number(params.get("section_depth_shift_ratio"), 0.0, -0.24, 0.24)
    frame_angle = _dominant_axis_degrees(footprint)
    origin = (float(footprint.centroid.x), float(footprint.centroid.y))
    local = rotate(footprint, -frame_angle, origin=origin, use_radians=False)
    minx, miny, maxx, maxy = local.bounds
    width, depth = maxx - minx, maxy - miny
    if width <= 0 or depth <= 0:
        return None

    if axis == "x":
        center = (miny + maxy) / 2.0 + depth * depth_shift
        half_depth = depth * depth_ratio / 2.0
        front, back = max(miny, center - half_depth), min(maxy, center + half_depth)
        section_min = min(point[0] for point in outer)
        section_max = max(point[0] for point in outer)
        local_proxy = Polygon((
            (minx + width * section_min, front),
            (minx + width * section_max, front),
            (minx + width * section_max, back),
            (minx + width * section_min, back),
        ))
    else:
        center = (minx + maxx) / 2.0 + width * depth_shift
        half_depth = width * depth_ratio / 2.0
        front, back = max(minx, center - half_depth), min(maxx, center + half_depth)
        section_min = min(point[0] for point in outer)
        section_max = max(point[0] for point in outer)
        local_proxy = Polygon((
            (front, miny + depth * section_min),
            (back, miny + depth * section_min),
            (back, miny + depth * section_max),
            (front, miny + depth * section_max),
        ))
    world_proxy = rotate(local_proxy, frame_angle, origin=origin, use_radians=False)
    proxy = world_proxy.intersection(footprint)
    if isinstance(proxy, MultiPolygon):
        proxy = max(proxy.geoms, key=lambda item: item.area)
    if not isinstance(proxy, Polygon) or proxy.is_empty or proxy.area <= 0:
        return None

    diagonal_outer = _diagonal_edge_count(outer)
    diagonal_void = _diagonal_edge_count(void)
    void_ratio = void_area / max(float(outer_polygon.area), 1e-9)
    return SectionalMonolithField(
        section_shape=section_shape,
        outer_controls=outer,
        void_controls=void,
        proxy_footprint=proxy,
        axis=axis,
        front_coordinate=front,
        back_coordinate=back,
        frame_angle_degrees=frame_angle,
        frame_origin=origin,
        local_bounds=(minx, miny, maxx, maxy),
        evidence={
            "schema_version": "arr.maas.site_sectional_monolith.v1",
            "field_type": "agent_authored_section_solid_void_extrusion",
            "coordinate_frame": "minimum_rotated_parcel_axis",
            "coordinate_template": False,
            "axis": axis,
            "outer_control_point_count": len(outer),
            "void_control_point_count": len(void),
            "outer_controls": [[round(u, 4), round(z, 4)] for u, z in outer],
            "void_controls": [[round(u, 4), round(z, 4)] for u, z in void],
            "section_depth_ratio": round(depth_ratio, 4),
            "section_depth_shift_ratio": round(depth_shift, 4),
            "section_material_ratio": round(float(section_shape.area) / float(outer_polygon.area), 4),
            "section_void_ratio": round(void_ratio, 4),
            "diagonal_edge_count": diagonal_outer + diagonal_void,
            "has_through_void": bool(void and void_ratio >= 0.04),
            "proxy_area_ratio": round(float(proxy.area) / max(float(footprint.area), 1e-9), 4),
            "dominant_axis_world_degrees": round(frame_angle, 4),
            "source": str(params.get("design_field_source") or "mass_graph_parameters"),
        },
    )


def sectional_vertex_world(field: SectionalMonolithField, point: Point2, *, back: bool) -> Point3:
    """Map normalized section [u,z] to one front/back world vertex."""
    u, z = point
    minx, miny, maxx, maxy = field.local_bounds
    if field.axis == "x":
        local_point = (minx + (maxx - minx) * u, field.back_coordinate if back else field.front_coordinate)
    else:
        local_point = (field.back_coordinate if back else field.front_coordinate, miny + (maxy - miny) * u)
    world_x, world_y = _rotate_point(local_point, field.frame_angle_degrees, field.frame_origin)
    return world_x, world_y, z


def _controls(value: Any, *, minimum: int) -> tuple[Point2, ...]:
    if not isinstance(value, list) or not minimum <= len(value) <= 8:
        return ()
    points: list[Point2] = []
    for item in value:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return ()
        try:
            u, z = float(item[0]), float(item[1])
        except (TypeError, ValueError):
            return ()
        points.append((max(0.02, min(0.98, u)), max(0.0, min(1.0, z))))
    return tuple(points)


def _diagonal_edge_count(points: tuple[Point2, ...]) -> int:
    if len(points) < 2:
        return 0
    return sum(
        1
        for left, right in zip(points, points[1:] + points[:1])
        if abs(left[0] - right[0]) >= 0.04 and abs(left[1] - right[1]) >= 0.04
    )


def _dominant_axis_degrees(footprint: Polygon) -> float:
    coordinates = list(footprint.minimum_rotated_rectangle.exterior.coords)[:4]
    edges = [
        (left, right, (right[0] - left[0]) ** 2 + (right[1] - left[1]) ** 2)
        for left, right in zip(coordinates, coordinates[1:] + coordinates[:1])
    ]
    if not edges:
        return 0.0
    left, right, _ = max(edges, key=lambda item: item[2])
    angle = degrees(atan2(right[1] - left[1], right[0] - left[0]))
    while angle >= 90.0:
        angle -= 180.0
    while angle < -90.0:
        angle += 180.0
    return angle


def _rotate_point(point: Point2, angle_degrees: float, origin: Point2) -> Point2:
    angle = radians(angle_degrees)
    cosine, sine = cos(angle), sin(angle)
    dx, dy = point[0] - origin[0], point[1] - origin[1]
    return origin[0] + dx * cosine - dy * sine, origin[1] + dx * sine + dy * cosine


def _number(value: Any, default: float, low: float, high: float) -> float:
    try:
        return max(low, min(high, float(value)))
    except (TypeError, ValueError):
        return default


__all__ = ["SectionalMonolithField", "build_sectional_monolith_field", "sectional_vertex_world"]
