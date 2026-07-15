"""Deterministic four-view mesh renderer used by the VLM critic loop."""

from __future__ import annotations

from math import cos, radians, sin
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .compiler import CompilationResult


def render_compilation_preview(result: CompilationResult, output_path: str | Path, *, title: str = "") -> Path:
    if result.status != "compiled" or not result.vertices or not result.triangles:
        raise ValueError("only compiled geometry can be rendered")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    vertices = np.asarray(result.vertices, dtype=float)
    faces = np.asarray(result.triangles, dtype=int)
    width, height = 900, 680
    image = Image.new("RGB", (width, height), "#f4f7fb")
    draw = ImageDraw.Draw(image, "RGBA")
    views = (
        ("isometric", 35.0, 28.0, 0, 0),
        ("opposite", 215.0, 28.0, 450, 0),
        ("front", 0.0, 0.0, 0, 325),
        ("top", 0.0, 90.0, 450, 325),
    )
    light = np.asarray((0.35, -0.45, 0.82), dtype=float)
    light /= np.linalg.norm(light)
    for label, yaw, pitch, ox, oy in views:
        panel_w, panel_h = 450, 325
        projected, depth, rotated = _project(vertices, yaw=yaw, pitch=pitch)
        span = np.ptp(projected, axis=0)
        scale = min((panel_w - 70) / max(span[0], 1e-9), (panel_h - 70) / max(span[1], 1e-9))
        center = (projected.min(axis=0) + projected.max(axis=0)) / 2
        screen = np.empty_like(projected)
        screen[:, 0] = ox + panel_w / 2 + (projected[:, 0] - center[0]) * scale
        screen[:, 1] = oy + panel_h / 2 - (projected[:, 1] - center[1]) * scale
        draw.rectangle((ox + 6, oy + 6, ox + panel_w - 6, oy + panel_h - 6), fill=(255, 255, 255, 255), outline=(198, 210, 224, 255), width=1)
        draw.text((ox + 16, oy + 14), label, fill=(51, 65, 85, 255))
        ordered = sorted(range(len(faces)), key=lambda index: float(depth[faces[index]].mean()))
        for face_index in ordered:
            face = faces[face_index]
            a, b, c = rotated[face]
            normal = np.cross(b - a, c - a)
            norm = float(np.linalg.norm(normal))
            if norm <= 1e-12:
                continue
            normal /= norm
            intensity = 0.38 + 0.58 * abs(float(np.dot(normal, light)))
            color = (
                int(225 * intensity),
                int(148 * intensity),
                int(56 * intensity),
                235,
            )
            points = [tuple(float(value) for value in screen[index]) for index in face]
            draw.polygon(points, fill=color, outline=(126, 69, 28, 115))
    caption = title or result.program.name
    draw.rectangle((8, height - 30, width - 8, height - 5), fill=(244, 247, 251, 245))
    draw.text((16, height - 25), f"{caption[:90]} | {result.metrics.get('triangle_count')} tri | {result.geometry_hash[:12]}", fill=(15, 23, 42, 255))
    temporary = output.with_suffix(".tmp.png")
    image.save(temporary)
    temporary.replace(output)
    return output


def _project(vertices: np.ndarray, *, yaw: float, pitch: float):
    center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2
    points = vertices - center
    y = radians(yaw)
    p = radians(pitch)
    rz = np.asarray(((cos(y), -sin(y), 0), (sin(y), cos(y), 0), (0, 0, 1)), dtype=float)
    rx = np.asarray(((1, 0, 0), (0, cos(p), -sin(p)), (0, sin(p), cos(p))), dtype=float)
    rotated = points @ rz.T @ rx.T
    return rotated[:, :2], rotated[:, 2], rotated


__all__ = ["render_compilation_preview"]
