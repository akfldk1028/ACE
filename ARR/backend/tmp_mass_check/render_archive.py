"""Draw the masses a run actually produced, straight from its legal archive.

The archive holds every mass that cleared generation, whether or not the
portfolio contract later selected it. Selection taking zero does not mean no
mass was built, and this is how to see that.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TILE = 300
COLUMNS = 7


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


def main(run_dir, limit=28):
    payload = json.loads(
        (Path(run_dir) / "maas-book-programs-summary.json").read_text(encoding="utf-8"),
    )
    records = []
    for program in payload.get("programs", []):
        archive = (program.get("counts") or {}).get("legal_mass_archive") or {}
        records.extend(archive.get("records") or [])
    records = [record for record in records if surfaces_of(record)][:limit]
    if not records:
        print("no archived masses with surfaces")
        return

    rows = (len(records) + COLUMNS - 1) // COLUMNS
    image = Image.new("RGB", (COLUMNS * TILE, rows * TILE + 30), (247, 247, 245))
    context = ImageDraw.Draw(image)
    context.text((10, 10), f"{Path(run_dir).name}: {len(records)} archived masses",
                 fill=(0, 0, 0))
    for index, record in enumerate(records):
        column, row = index % COLUMNS, index // COLUMNS
        label = str(record.get("geometry_hash") or "")[:8]
        draw(context, surfaces_of(record), (column * TILE, row * TILE + 30),
             TILE, f"{index} {label}")
    out = Path(run_dir).parent / f"{Path(run_dir).name}-archive.png"
    image.save(out)
    print(f"wrote {out} ({len(records)} masses)")


if __name__ == "__main__":
    main(sys.argv[1])
