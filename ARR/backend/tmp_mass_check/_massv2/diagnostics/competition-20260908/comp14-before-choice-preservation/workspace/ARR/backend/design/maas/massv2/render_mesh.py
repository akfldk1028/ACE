"""Exact BOOK mesh transport shared by rendering, plans and sections.

SourceSurface XY is relative to SourceMass.footprint.centroid; Z is a fraction
of authored_height_m. Datum is the ground plane, not another vertex offset.
"""
from math import cos, isfinite, sin

import numpy as np
from PIL import Image
from shapely.geometry import Polygon


def is_mesh_authoritative(source):
    meta = source.metadata or {}
    bridge = meta.get('geometry_program_bridge_evidence') or {}
    return bool(meta.get('book_height_certificate') or
                bridge.get('authoritative_visual_geometry') == 'manifold_compilation_mesh' or
                bridge.get('surface_coordinate_frame') == 'source_footprint_centroid_local')


def physical_triangles(source):
    """Complete world XYZ triangles; refuse missing authority/frame/vertices."""
    bridge = (source.metadata or {}).get('geometry_program_bridge_evidence') or {}
    surfaces = tuple(source.surfaces or ())
    if (bridge.get('surface_coordinate_frame') != 'source_footprint_centroid_local'
            or not bridge.get('surface_export_complete')
            or not surfaces or bridge.get('raw_mesh_triangle_count') != len(surfaces)
            or bridge.get('exported_surface_count') != len(surfaces)):
        raise ValueError('complete authoritative mesh surface export required')
    height = float(source.metadata.get('authored_height_m') or 0)
    if not isfinite(height) or height <= 0:
        raise ValueError('authoritative mesh requires positive physical height')
    origin = source.footprint.centroid
    result = []
    for surface in surfaces:
        points = surface.vertices_m
        if len(points) != 3 or any(len(p) != 3 or not all(isfinite(float(n)) for n in p) for p in points):
            raise ValueError('finite XYZ mesh triangles required')
        result.append(tuple((float(x)+origin.x, float(y)+origin.y, float(z)*height) for x, y, z in points))
    return tuple(result)


def actual_xy_projection(source):
    # The legal owner already checks and measures the complete exported mesh.
    physical_triangles(source)
    from .parcel_policy import _projection_for_gate
    return _projection_for_gate(source)[0]


def mesh_section_at(source, *, axis='z', coordinate=0.0):
    """Exact kernel section: XY for z, XZ for y, YZ for x, all metres."""
    from design.maas.geometry_language.source_bridge import mesh_section_solid, solid_section_polygon
    triangles = physical_triangles(source)
    vertices = [p for triangle in triangles for p in triangle]
    if axis == 'y':
        vertices = [(x, z, -y) for x, y, z in vertices]
        coordinate = -coordinate
    elif axis == 'x':
        vertices = [(y, z, x) for x, y, z in vertices]
    elif axis != 'z':
        raise ValueError('mesh section axis must be x, y or z')
    faces = [(i, i+1, i+2) for i in range(0, len(vertices), 3)]
    result = solid_section_polygon(mesh_section_solid(vertices, faces), coordinate)
    return result if result is not None else Polygon()


def mesh_plan_at(source, z):
    return mesh_section_at(source, axis='z', coordinate=z)


def paint_mesh(panel, triangles, *, project, to_screen, yaw, pitch, palette, smooth_turn_cos):
    """Orthographic triangle rasterization with depth-tested fills and edges.

    No band reconstruction, convex hull, coordinate snapping or face dropping.
    Triangle interiors stay seamless; silhouettes and actual sharp folds show.
    """
    width, height = panel.size
    pixels = np.array(panel, dtype=np.uint8)
    depth = np.full((height, width), -np.inf)
    normals = np.zeros((height, width, 3))
    camera = np.array((sin(yaw)*cos(pitch), cos(yaw)*cos(pitch), sin(pitch)))
    light = np.array((-.25, -.35, 1.0)); light /= np.linalg.norm(light)
    for triangle in triangles:
        world = np.asarray(triangle, dtype=float)
        normal = np.cross(world[1]-world[0], world[2]-world[0])
        length = np.linalg.norm(normal)
        if length == 0:
            continue
        normal /= length
        projected = np.asarray([to_screen(project(*point)) for point in triangle])
        xs, ys = projected[:, 0], projected[:, 1]
        left, right = max(0, int(np.floor(xs.min()))), min(width-1, int(np.ceil(xs.max())))
        top, bottom = max(0, int(np.floor(ys.min()))), min(height-1, int(np.ceil(ys.max())))
        if right < left or bottom < top:
            continue
        denominator = (ys[1]-ys[2])*(xs[0]-xs[2]) + (xs[2]-xs[1])*(ys[0]-ys[2])
        if denominator == 0:
            continue
        xx, yy = np.meshgrid(np.arange(left, right+1)+.5, np.arange(top, bottom+1)+.5)
        a = ((ys[1]-ys[2])*(xx-xs[2]) + (xs[2]-xs[1])*(yy-ys[2])) / denominator
        b = ((ys[2]-ys[0])*(xx-xs[2]) + (xs[0]-xs[2])*(yy-ys[2])) / denominator
        c = 1-a-b
        z = world @ camera
        interpolated = a*z[0]+b*z[1]+c*z[2]
        target = depth[top:bottom+1, left:right+1]
        visible = (a >= 0) & (b >= 0) & (c >= 0) & (interpolated > target)
        target[visible] = interpolated[visible]
        normals[top:bottom+1, left:right+1][visible] = normal
        base = np.asarray(palette.roof if normal[2] > .5 else palette.wall)
        shade = .88 + .12 * max(0, float(normal @ light))
        pixels[top:bottom+1, left:right+1][visible] = np.clip(base*shade, 0, 255).astype(np.uint8)
    occupied = np.isfinite(depth)
    edges = np.zeros_like(occupied)
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        adjacent = np.roll(occupied, (dy, dx), axis=(0, 1))
        adjacent_normals = np.roll(normals, (dy, dx), axis=(0, 1))
        sharp = np.sum(normals*adjacent_normals, axis=2) < smooth_turn_cos
        edges |= occupied & (~adjacent | sharp)
    pixels[edges] = palette.edge
    panel.paste(Image.fromarray(pixels))
