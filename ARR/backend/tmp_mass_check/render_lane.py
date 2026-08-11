"""Contact sheet of a geometry-program supply, so the masses can be looked at.

Axonometric, painter's algorithm, flat shading. Deliberately plain: this is a
look at what the supply actually is, not a presentation render.
"""

import math
import sys

import numpy as np
from PIL import Image, ImageDraw

import os
from pathlib import Path

import django

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from design.maas.geometry_language.compiler import compile_geometry_program  # noqa: E402


TILE = 300
COLUMNS = 6


def project(vertices, size):
    v = np.asarray(vertices, dtype=float)
    # Rotate into a standard architectural axonometric.
    yaw, pitch = math.radians(-35.0), math.radians(28.0)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    x = v[:, 0] * cy - v[:, 1] * sy
    y = v[:, 0] * sy + v[:, 1] * cy
    screen_x = x
    screen_y = y * sp - v[:, 2] * cp
    depth = y * cp + v[:, 2] * sp

    span_x = max(screen_x.max() - screen_x.min(), 1e-9)
    span_y = max(screen_y.max() - screen_y.min(), 1e-9)
    scale = (size * 0.74) / max(span_x, span_y)
    px = (screen_x - screen_x.mean()) * scale + size / 2
    py = (screen_y - screen_y.mean()) * scale + size / 2
    return px, py, depth


def draw_solid(draw, vertices, triangles, offset, size, label):
    px, py, depth = project(vertices, size)
    v = np.asarray(vertices, dtype=float)
    tris = np.asarray(triangles, dtype=int)

    order = np.argsort([depth[t].mean() for t in tris])
    light = np.array([0.45, 0.55, 0.71])
    for index in order:
        a, b, c = tris[index]
        normal = np.cross(v[b] - v[a], v[c] - v[a])
        length = np.linalg.norm(normal)
        if length < 1e-12:
            continue
        shade = abs(float(np.dot(normal / length, light)))
        tone = int(70 + 150 * shade)
        draw.polygon(
            [
                (offset[0] + px[a], offset[1] + py[a]),
                (offset[0] + px[b], offset[1] + py[b]),
                (offset[0] + px[c], offset[1] + py[c]),
            ],
            fill=(tone, tone, min(255, tone + 12)),
            outline=(35, 35, 40),
        )
    draw.text((offset[0] + 8, offset[1] + size - 16), label, fill=(20, 20, 20))


def sheet(programs, path, title):
    rows = (len(programs) + COLUMNS - 1) // COLUMNS
    image = Image.new(
        "RGB", (COLUMNS * TILE, rows * TILE + 30), (247, 247, 245),
    )
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), title, fill=(0, 0, 0))
    for index, program in enumerate(programs):
        result = compile_geometry_program(program)
        if result.status != "compiled" or not result.vertices:
            continue
        column, row = index % COLUMNS, index // COLUMNS
        draw_solid(
            draw,
            result.vertices,
            result.triangles,
            (column * TILE, row * TILE + 30),
            TILE,
            f"{index} {program.metadata.get('family')}",
        )
    image.save(path)
    print(f"wrote {path} ({len(programs)} programs)")


if __name__ == "__main__":
    from design.maas.geometry_language.stacked_volume_bank import (
        stacked_volume_programs,
    )
    from design.maas.geometry_language.universal_form_bank import (
        stratified_form_supply_order,
        universal_form_programs,
    )

    target = sys.argv[1] if len(sys.argv) > 1 else "lane"
    if target == "lane":
        sheet(
            list(stacked_volume_programs(0)),
            "tmp_mass_check/multi-volume-lane.png",
            "multi-volume composition lane (page 0)",
        )
    else:
        ordered = stratified_form_supply_order(universal_form_programs(0))
        sheet(
            list(ordered[:24]),
            "tmp_mass_check/bank-head-24.png",
            "form bank, first 24 in stratified order (what a run actually reaches)",
        )
