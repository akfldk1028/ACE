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

from PIL import Image, ImageDraw, ImageFont

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
# The boundary a neighbour is already built against. The parcel's open side is
# whatever is left of the outline, and it is the reason the siting axis points
# where it does - so the drawing should say which is which.
_PARTY_WALL = (128, 122, 116)
_INK = (40, 40, 44)
_MUTED = (108, 110, 104)
_ACCENT = (170, 82, 20)

_FONT_FACES = ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/gulim.ttc")


def _font(size: int, bold: bool = False):
    """A face that can set Hangul. The authors' reasons are written in Korean."""

    faces = ("C:/Windows/Fonts/malgunbd.ttf",) + _FONT_FACES if bold else _FONT_FACES
    for path in faces:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(text: str, font, width: float) -> list[str]:
    """Break to fit. Korean wraps per character; the space-split alone leaves
    long unbroken runs that overflow the caption block."""

    lines: list[str] = []
    line = ""
    for char in text:
        if char == "\n":
            lines.append(line)
            line = ""
            continue
        trial = line + char
        if font.getlength(trial) > width and line:
            lines.append(line)
            line = char.lstrip()
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


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


def render_sequence(
    frames: Sequence[dict[str, Any]],
    output: Path,
    *,
    site_ring: Sequence[tuple[float, float]] | None = None,
    party_edges: Sequence[Sequence[tuple[float, float]]] = (),
    heading: str = "",
    subheading: str = "",
    tile: tuple[int, int] = (400, 480),
) -> Path:
    """One drawing per word of the sentence, all on one scale.

    The shared scale is the whole point. Fitting each panel to its own contents
    makes the mass appear to change size between moves, which is the one thing
    a parti diagram must not say - the reader is being shown what changed, so
    everything that did not change has to sit still.
    """

    if not frames:
        raise ValueError("nothing to render")

    # One bound for every frame, so a move reads as a move.
    world: list[tuple[float, float]] = []
    if site_ring:
        world.extend(_project(x, y, 0.0) for x, y in site_ring)
    for frame in frames:
        source = frame.get("source")
        if source is None:
            continue
        height = float(source.metadata.get("authored_height_m") or 0.0)
        for volume in source.volumes:
            low = float(volume.bottom_fraction) * height
            high = float(volume.top_fraction) * height
            for shape, _colour in _faces(volume.footprint, low, high):
                world.extend(shape)
    if not world:
        raise ValueError("nothing to draw")

    min_x = min(px for px, _py in world)
    max_x = max(px for px, _py in world)
    min_y = min(py for _px, py in world)
    max_y = max(py for _px, py in world)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)

    draw_h = tile[1] - 170
    scale = min((tile[0] - 44) / span_x, (draw_h - 24) / span_y)
    off_x = (tile[0] - span_x * scale) / 2.0
    off_y = 46.0 + (draw_h - span_y * scale) / 2.0

    def to_screen(point: tuple[float, float]) -> tuple[float, float]:
        return (off_x + (point[0] - min_x) * scale, off_y + (point[1] - min_y) * scale)

    head = 78 if heading else 0
    sheet = Image.new("RGB", (len(frames) * tile[0], tile[1] + head), _BACKGROUND)
    board = ImageDraw.Draw(sheet)

    if heading:
        board.text((26, 22), heading, font=_font(25, bold=True), fill=_INK)
        if subheading:
            board.text((26, 52), subheading, font=_font(14), fill=_MUTED)

    for index, frame in enumerate(frames):
        panel = _render_frame(frame, tile, to_screen, site_ring, party_edges, index + 1)
        sheet.paste(panel, (index * tile[0], head))

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return output


def _render_frame(
    frame: dict[str, Any],
    tile: tuple[int, int],
    to_screen,
    site_ring: Sequence[tuple[float, float]] | None,
    party_edges: Sequence[Sequence[tuple[float, float]]],
    number: int,
) -> Image.Image:
    panel = Image.new("RGB", tile, _BACKGROUND)
    draw = ImageDraw.Draw(panel)

    draw.text((22, 18), f"{number:02d}", font=_font(13, bold=True), fill=_ACCENT)
    draw.text((48, 17), str(frame.get("verb") or ""), font=_font(15, bold=True), fill=_INK)

    if site_ring:
        draw.polygon([to_screen(_project(x, y, 0.0)) for x, y in site_ring], fill=_SITE)
    for edge in party_edges:
        points = [to_screen(_project(x, y, 0.0)) for x, y in edge]
        if len(points) >= 2:
            draw.line(points, fill=_PARTY_WALL, width=4)

    source = frame.get("source")
    if source is not None:
        height = float(source.metadata.get("authored_height_m") or 0.0)
        ordered = sorted(
            source.volumes,
            key=lambda item: (item.bottom_fraction, -item.footprint.centroid.y),
        )
        for volume in ordered:
            low = float(volume.bottom_fraction) * height
            high = float(volume.top_fraction) * height
            for shape, colour in _faces(volume.footprint, low, high):
                draw.polygon([to_screen(point) for point in shape], fill=colour, outline=_EDGE)

    y = tile[1] - 150
    draw.line([(22, y), (tile[0] - 22, y)], fill=(220, 220, 214), width=1)
    y += 12

    aim = str(frame.get("aim") or "")
    if aim:
        draw.text((22, y), aim, font=_font(12, bold=True), fill=_ACCENT)
        y += 20

    body = _font(13)
    for line in _wrap(str(frame.get("why") or ""), body, tile[0] - 46)[:5]:
        draw.text((22, y), line, font=body, fill=_MUTED)
        y += 19

    numbers = frame.get("numbers")
    if numbers:
        draw.text((22, tile[1] - 30), str(numbers), font=_font(12, bold=True), fill=_INK)
    return panel


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

    draw.text((10, 6), title[:40], fill=_INK)
    line = "  ".join(f"{key} {value}" for key, value in caption.items())
    draw.text((10, tile[1] - 46), line[:58], fill=(70, 70, 76))
    return panel
