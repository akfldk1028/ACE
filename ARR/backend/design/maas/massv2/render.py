"""Draw a compiled mass so a person can judge it.

Deliberately self-contained: no MAAS renderer import, no certificate, no
`profiled_` surfaces. The existing preview path raises unless an authored mesh
carries a projected-visual certificate, and arming that layer is exactly what
this package is avoiding while the form language is being proven.

Bands are drawn back to front as extruded prisms under a fixed axonometric.
That is enough to tell a stacked tower from a courtyard block, which is the only
question being asked here.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable, Sequence

from PIL import Image, ImageDraw

from design.maas.source_geometry.ir import SourceMass


_YAW = math.radians(-35.0)
_PITCH = math.radians(28.0)
_BACKGROUND = (250, 250, 248)
_SITE = (196, 214, 200)
_WALL = (214, 132, 66)
_ROOF = (238, 168, 92)
_EDGE = (120, 68, 26)
# A court is a hole in the roof, painted back to the ground it opens onto.
_COURT = (206, 218, 208)


def _project(x: float, y: float, z: float) -> tuple[float, float]:
    sx = x * math.cos(_YAW) - y * math.sin(_YAW)
    sy = x * math.sin(_YAW) + y * math.cos(_YAW)
    return sx, sy * math.sin(_PITCH) - z * math.cos(_PITCH)


def _walls(ring: Sequence[tuple[float, float]], low: float, high: float):
    for (x0, y0), (x1, y1) in zip(ring, list(ring[1:]) + [ring[0]]):
        yield [
            _project(x0, y0, low), _project(x1, y1, low),
            _project(x1, y1, high), _project(x0, y0, high),
        ], _WALL


def _faces(polygon, low: float, high: float):
    """Walls for every ring, then the roof drawn as a ring with its holes.

    Drawing only the exterior ring made every courtyard scheme render as a solid
    block - the court was in the geometry and in the measurement, and missing
    only from the picture, which is the worst place for it to be missing. A
    court has walls too, and they face inward.
    """

    outer = [(float(x), float(y)) for x, y in polygon.exterior.coords[:-1]]
    if len(outer) < 3:
        return
    yield from _walls(outer, low, high)
    for interior in polygon.interiors:
        court = [(float(x), float(y)) for x, y in interior.coords[:-1]]
        if len(court) >= 3:
            yield from _walls(court, low, high)
    # The roof is the ring minus its holes. Painting the hole in the background
    # colour is the cheapest correct answer for a filled polygon renderer.
    yield [_project(x, y, high) for x, y in outer], _ROOF
    for interior in polygon.interiors:
        court = [(float(x), float(y)) for x, y in interior.coords[:-1]]
        if len(court) >= 3:
            yield [_project(x, y, high) for x, y in court], _COURT


def render_masses(
    items: Iterable[tuple[str, SourceMass, dict[str, Any]]],
    output: Path,
    *,
    site_ring: Sequence[tuple[float, float]] | None = None,
    columns: int = 4,
    tile: tuple[int, int] = (330, 300),
) -> Path:
    """Contact sheet, one compiled mass per tile, captioned with its numbers."""

    entries = list(items)
    if not entries:
        raise ValueError("nothing to render")
    rows = math.ceil(len(entries) / columns)
    sheet = Image.new("RGB", (columns * tile[0], rows * tile[1]), _BACKGROUND)

    for index, (title, source, caption) in enumerate(entries):
        panel = _render_one(source, tile, site_ring=site_ring, title=title, caption=caption)
        sheet.paste(panel, ((index % columns) * tile[0], (index // columns) * tile[1]))

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return output


def _render_one(
    source: SourceMass,
    tile: tuple[int, int],
    *,
    site_ring: Sequence[tuple[float, float]] | None,
    title: str,
    caption: dict[str, Any],
) -> Image.Image:
    panel = Image.new("RGB", tile, _BACKGROUND)
    draw = ImageDraw.Draw(panel)

    height = float(source.metadata.get("authored_height_m") or 0.0)
    polygons: list[tuple[list[tuple[float, float]], tuple[int, int, int]]] = []

    if site_ring:
        polygons.append(([_project(x, y, 0.0) for x, y in site_ring], _SITE))

    # Painter's algorithm on the band's own depth: farther bands first, and
    # within a band the lower one first, so an upper volume overlaps the one
    # holding it up rather than the other way round.
    ordered = sorted(source.volumes, key=lambda item: (item.bottom_fraction, -item.footprint.centroid.y))
    for volume in ordered:
        low = float(volume.bottom_fraction) * height
        high = float(volume.top_fraction) * height
        polygons.extend(_faces(volume.footprint, low, high))

    flat = [point for shape, _colour in polygons for point in shape]
    if not flat:
        return panel
    min_x = min(px for px, _py in flat)
    max_x = max(px for px, _py in flat)
    min_y = min(py for _px, py in flat)
    max_y = max(py for _px, py in flat)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    scale = min((tile[0] - 30) / span_x, (tile[1] - 78) / span_y)
    off_x = (tile[0] - span_x * scale) / 2.0
    off_y = 22.0 + (tile[1] - 78 - span_y * scale) / 2.0

    def to_screen(point: tuple[float, float]) -> tuple[float, float]:
        return (off_x + (point[0] - min_x) * scale, off_y + (point[1] - min_y) * scale)

    for shape, colour in polygons:
        draw.polygon([to_screen(point) for point in shape], fill=colour, outline=_EDGE)

    draw.text((10, 6), title[:40], fill=(40, 40, 44))
    line = "  ".join(f"{key} {value}" for key, value in caption.items())
    draw.text((10, tile[1] - 46), line[:58], fill=(70, 70, 76))
    return panel
