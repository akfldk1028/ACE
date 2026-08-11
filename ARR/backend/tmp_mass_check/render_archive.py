"""Draw the masses a run actually produced, straight from its legal archive.

The archive holds every mass that cleared generation, whether or not the
portfolio contract later selected it. Selection taking zero does not mean no
mass was built, and this is how to see that.

Each tile carries its measured 건축면적 - the union of the mass projected onto
XY, per 건축법 시행령 제119조 제1항 제2호 - against the capacity the run itself
declared. A sheet of pictures alone invites "looks fine to me"; every defect
this session found was visible only once a number sat next to the shape.

Usage: render_archive.py RUN_DIR [LIMIT]   (no LIMIT renders every mass)
"""

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TILE = 300
COLUMNS = 7


def declared_capacity(run_dir):
    text = (Path(run_dir) / "maas-book-programs-summary.json").read_text(
        encoding="utf-8",
    )
    found = re.search(r'"bcr_footprint_capacity_m2"\s*:\s*([0-9.]+)', text)
    return float(found.group(1)) if found else None


def projected_area(polygons):
    faces = [
        flat
        for polygon in polygons
        for flat in (Polygon([(row[0], row[1]) for row in polygon]),)
        if flat.is_valid and flat.area > 0.0
    ]
    return float(unary_union(faces).area) if faces else 0.0


def surfaces_of(record):
    payload = record.get("final_authored_surface_payload") or []
    polygons = []
    for surface in payload:
        vertices = surface.get("vertices_m") or []
        if len(vertices) >= 3:
            polygons.append(np.asarray(vertices, dtype=float))
    return polygons


def draw(draw_ctx, polygons, offset, size, label):
    points = np.vstack(polygons)
    yaw, pitch = math.radians(-35.0), math.radians(28.0)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    def project(v):
        x = v[:, 0] * cy - v[:, 1] * sy
        y = v[:, 0] * sy + v[:, 1] * cy
        return x, y * sp - v[:, 2] * cp, y * cp + v[:, 2] * sp

    ax, ay, _ = project(points)
    span = max(ax.max() - ax.min(), ay.max() - ay.min(), 1e-9)
    scale = (size * 0.74) / span
    cx, cyy = ax.mean(), ay.mean()

    faces = []
    for polygon in polygons:
        px, py, depth = project(polygon)
        normal = np.cross(polygon[1] - polygon[0], polygon[2] - polygon[0])
        length = np.linalg.norm(normal)
        shade = abs(float(np.dot(normal / length, [0.45, 0.55, 0.71]))) if length > 1e-12 else 0.5
        faces.append((depth.mean(), [
            (offset[0] + (x - cx) * scale + size / 2,
             offset[1] + (y - cyy) * scale + size / 2)
            for x, y in zip(px, py)
        ], shade))

    for _depth, screen, shade in sorted(faces, key=lambda item: item[0]):
        tone = int(70 + 150 * shade)
        draw_ctx.polygon(screen, fill=(tone, tone, min(255, tone + 12)),
                         outline=(35, 35, 40))
    draw_ctx.text((offset[0] + 8, offset[1] + size - 16), label, fill=(20, 20, 20))


def main(run_dir, limit=None):
    payload = json.loads(
        (Path(run_dir) / "maas-book-programs-summary.json").read_text(encoding="utf-8"),
    )
    records = []
    for program in payload.get("programs", []):
        archive = (program.get("counts") or {}).get("legal_mass_archive") or {}
        records.extend(archive.get("records") or [])
    records = [record for record in records if surfaces_of(record)]
    if limit is not None:
        records = records[:limit]
    if not records:
        print("no archived masses with surfaces")
        return

    capacity = declared_capacity(run_dir)
    measured = [projected_area(surfaces_of(record)) for record in records]
    over = (
        sum(1 for area in measured if area > capacity)
        if capacity is not None
        else 0
    )

    rows = (len(records) + COLUMNS - 1) // COLUMNS
    image = Image.new("RGB", (COLUMNS * TILE, rows * TILE + 30), (247, 247, 245))
    context = ImageDraw.Draw(image)
    heading = f"{Path(run_dir).name}: {len(records)} archived masses"
    if capacity is not None:
        # ASCII only: the default PIL font has no CJK glyphs and renders the
        # heading as tofu boxes, which is worse than the English name.
        heading += (
            f"   building coverage cap {capacity:.1f} m2"
            f"   over cap {over}/{len(records)}"
        )
    context.text((10, 10), heading, fill=(0, 0, 0))
    for index, record in enumerate(records):
        column, row = index % COLUMNS, index // COLUMNS
        offset = (column * TILE, row * TILE + 30)
        area = measured[index]
        breached = capacity is not None and area > capacity
        if breached:
            context.rectangle(
                [offset[0] + 2, offset[1] + 2,
                 offset[0] + TILE - 3, offset[1] + TILE - 3],
                outline=(200, 60, 60), width=3,
            )
        label = str(record.get("geometry_hash") or "")[:8]
        principle = str((record.get("lineage") or {}).get("principle_label") or "")
        draw(context, surfaces_of(record), offset, TILE, f"{index} {label}")
        context.text(
            (offset[0] + 8, offset[1] + 8),
            f"{area:.0f} m2{'  OVER' if breached else ''}",
            fill=(200, 60, 60) if breached else (40, 90, 40),
        )
        if principle:
            context.text(
                (offset[0] + 8, offset[1] + 22), principle, fill=(90, 90, 95),
            )
    out = Path(run_dir).parent / f"{Path(run_dir).name}-archive.png"
    image.save(out)
    print(f"wrote {out} ({len(records)} masses, {over} over cap)")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
