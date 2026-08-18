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


def _elide(text: str, font, width: float) -> str:
    """Cut to the space there is, not to a character count. A fixed `[:44]`
    fits a sheet tile and truncates nothing on a drawing three times as wide,
    which is where the name matters most."""

    if font.getlength(text) <= width:
        return text
    while text and font.getlength(text + "…") > width:
        text = text[:-1]
    return text + "…"


def _project(x: float, y: float, z: float) -> tuple[float, float]:
    sx = x * math.cos(_YAW) - y * math.sin(_YAW)
    sy = x * math.sin(_YAW) + y * math.cos(_YAW)
    return sx, sy * math.sin(_PITCH) - z * math.cos(_PITCH)


def _top_at(x: float, y: float, high: float, slope) -> float:
    """The top face's height at a plan point - flat unless the band tilts."""

    if slope is None:
        return high
    drop_m, ux, uy, lo_p, hi_p = slope
    span = max(hi_p - lo_p, 1e-9)
    t = (x * ux + y * uy - lo_p) / span
    return high - drop_m * min(1.0, max(0.0, t))


def _walls(ring: Sequence[tuple[float, float]], low: float, high: float, slope=None):
    for (x0, y0), (x1, y1) in zip(ring, list(ring[1:]) + [ring[0]]):
        yield [
            _project(x0, y0, low), _project(x1, y1, low),
            _project(x1, y1, _top_at(x1, y1, high, slope)),
            _project(x0, y0, _top_at(x0, y0, high, slope)),
        ], _WALL


def _slope_of(volume, low: float, high: float):
    """The renderer's reading of a tilted band: metres of drop and its axis.

    The projection range comes from the volume's own footprint, so the top
    meets `high` at the rear edge and `high - drop` at the front edge exactly.
    """

    drop = float(getattr(volume, "top_drop", 0.0) or 0.0)
    if drop <= 0.0 or volume.drop_toward is None:
        return None
    ux, uy = volume.drop_toward
    values = [x * ux + y * uy for x, y in volume.footprint.exterior.coords]
    return (drop * (high - low), ux, uy, min(values), max(values))


def _faces(polygon, low: float, high: float, slope=None):
    """Walls for every ring, then the roof drawn as a ring with its holes.

    Drawing only the exterior ring made every courtyard scheme render as a solid
    block - the court was in the geometry and in the measurement, and missing
    only from the picture, which is the worst place for it to be missing. A
    court has walls too, and they face inward.
    """

    outer = [(float(x), float(y)) for x, y in polygon.exterior.coords[:-1]]
    if len(outer) < 3:
        return
    yield from _walls(outer, low, high, slope)
    for interior in polygon.interiors:
        court = [(float(x), float(y)) for x, y in interior.coords[:-1]]
        if len(court) >= 3:
            yield from _walls(court, low, high, slope)
    # The roof is the ring minus its holes. Painting the hole in the background
    # colour is the cheapest correct answer for a filled polygon renderer.
    yield [_project(x, y, _top_at(x, y, high, slope)) for x, y in outer], _ROOF
    for interior in polygon.interiors:
        court = [(float(x), float(y)) for x, y in interior.coords[:-1]]
        if len(court) >= 3:
            yield [_project(x, y, _top_at(x, y, high, slope)) for x, y in court], _COURT


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
            for shape, _colour in _faces(volume.footprint, low, high, _slope_of(volume, low, high)):
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
            for shape, colour in _faces(volume.footprint, low, high, _slope_of(volume, low, high)):
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


def _plan_key(polygon) -> tuple:
    """What makes two bands the same plan, coarsely enough to survive floats."""

    bounds = tuple(round(value, 2) for value in polygon.bounds)
    return (bounds, round(float(polygon.area), 2), len(polygon.interiors))


def _merged_runs(volumes) -> list[tuple[float, float, Any]]:
    """Consecutive bands with the same plan, drawn as one prism.

    The compiler cuts a mass at every height where any volume starts or stops,
    which is right - it is how a setback is measured and how a court that is
    roofed over still reads as a court below the roof. It is not how a building
    is drawn. A tower crossing thirteen band edges was being drawn as thirteen
    stacked prisms, each with its own outline, so the sheet showed twelve lines
    that are not in the building and the mass read as a pile of slabs.

    Where the plan does not change from one band to the next there is no edge,
    so the run is one volume and gets one outline. Where it does change the line
    stays, because that line is the setback.
    """

    runs: list[tuple[float, float, Any]] = []
    by_plan: dict[tuple, list] = {}
    for volume in volumes:
        by_plan.setdefault(_plan_key(volume.footprint), []).append(volume)
    for group in by_plan.values():
        group.sort(key=lambda item: item.bottom_fraction)
        low = float(group[0].bottom_fraction)
        high = float(group[0].top_fraction)
        for volume in group[1:]:
            # Contiguous, allowing for the rounding the compiler's fractions
            # carry. A gap means two separate pieces of the same plan - a court
            # roofed over, say - and those are two prisms, not one.
            if float(volume.bottom_fraction) <= high + 1e-4:
                high = max(high, float(volume.top_fraction))
                continue
            runs.append((low, high, group[0].footprint))
            low, high = float(volume.bottom_fraction), float(volume.top_fraction)
        runs.append((low, high, group[0].footprint))
    return runs


def _draw_plan(draw, source, box, site_ring) -> None:
    """A roof plan beside the axonometric.

    The axonometric hides the one thing a settlement scheme is about. Central
    Beheer came out of the executor as four blocks standing apart - measured,
    four disjoint pieces in plan, and the streets between them are 4.6 m wide -
    and from a single viewpoint the near blocks simply cover them. The gaps are
    in the building and not in the drawing.

    Which is the practice answer as well: SANAA require every option to carry a
    plan, a drawing and a model, and a Korean 배치도 is what a jury reads first.
    One viewpoint is not a massing study.
    """

    left, top, width, height = box
    shapes = [footprint for _low, _high, footprint in _merged_runs(source.volumes)]
    if not shapes:
        return
    rings = [list(site_ring)] if site_ring else []
    points = [point for shape in shapes for point in shape.exterior.coords]
    points += [point for ring in rings for point in ring]
    xs = [x for x, _y in points]
    ys = [y for _x, y in points]
    span_x = max(max(xs) - min(xs), 1e-6)
    span_y = max(max(ys) - min(ys), 1e-6)
    scale = min(width / span_x, height / span_y)
    off_x = left + (width - span_x * scale) / 2.0
    off_y = top + (height - span_y * scale) / 2.0

    def to_screen(point):
        # North up: screen y grows downward, so the site's y is flipped.
        return (off_x + (point[0] - min(xs)) * scale,
                off_y + (max(ys) - point[1]) * scale)

    for ring in rings:
        draw.polygon([to_screen(point) for point in ring], fill=_SITE, outline=None)
    for shape in shapes:
        draw.polygon(
            [to_screen(point) for point in shape.exterior.coords],
            fill=_ROOF, outline=_EDGE,
        )
        for hole in shape.interiors:
            draw.polygon([to_screen(point) for point in hole.coords], fill=_SITE, outline=_EDGE)


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

    # Read the caption without consuming it. `pop` on the caller's dict meant
    # the sheet ate the thesis and the star, and the per-alternative drawings -
    # rendered afterwards from the same list - came out with the numbers only.
    # The large drawing is the one that gets looked at, so it lost exactly the
    # line it existed to carry.
    body = _font(11)
    mark = "★ " if caption.get("recommended") else ""
    numbers = "  ".join(
        f"{key} {value}"
        for key, value in caption.items()
        if key not in ("thesis", "recommended")
    )
    thesis = str(caption.get("thesis") or "").strip()
    # However many lines the sentence needs. Two was a guess that cut every
    # thesis mid-clause, and a thesis that stops at "so the route through the
    # block is the thing that" argues nothing.
    thesis_lines = _wrap(thesis, body, tile[0] - 20) if thesis else []
    reserve = 46 + 13 * len(thesis_lines)

    height = float(source.metadata.get("authored_height_m") or 0.0)
    polygons: list[tuple[list[tuple[float, float]], tuple[int, int, int]]] = []

    if site_ring:
        polygons.append(([_project(x, y, 0.0) for x, y in site_ring], _SITE))

    # Painter's algorithm on the band's own depth: farther bands first, and
    # within a band the lower one first, so an upper volume overlaps the one
    # holding it up rather than the other way round.
    ordered = sorted(_merged_runs(source.volumes),
                     key=lambda item: (item[0], -item[2].centroid.y))
    for low_fraction, high_fraction, footprint in ordered:
        low = low_fraction * height
        high = high_fraction * height
        polygons.extend(_faces(footprint, low, high))

    flat = [point for shape, _colour in polygons for point in shape]
    if not flat:
        return panel
    min_x = min(px for px, _py in flat)
    max_x = max(px for px, _py in flat)
    min_y = min(py for _px, py in flat)
    max_y = max(py for _px, py in flat)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    # The plan needs its own column, not a corner: dropped on top of the
    # axonometric it lands on the roof, which is the one place a reader is
    # already looking.
    inset = int(tile[0] * 0.26) if tile[0] >= 700 else 0
    gutter = inset + 32 if inset else 0
    scale = min((tile[0] - 30 - gutter) / span_x, (tile[1] - 22 - reserve) / span_y)
    off_x = (tile[0] - gutter - span_x * scale) / 2.0
    off_y = 22.0 + (tile[1] - 22 - reserve - span_y * scale) / 2.0

    def to_screen(point: tuple[float, float]) -> tuple[float, float]:
        return (off_x + (point[0] - min_x) * scale, off_y + (point[1] - min_y) * scale)

    for shape, colour in polygons:
        draw.polygon([to_screen(point) for point in shape], fill=colour, outline=_EDGE)

    # Room for a plan only where there is room: the contact sheet's tile is a
    # thumbnail and an inset in it would be a smudge. The large drawing per
    # alternative is where the gaps have to be readable.
    if inset:
        draw.text((tile[0] - inset - 16, 38), "배치", font=_font(10), fill=_MUTED)
        _draw_plan(draw, source, (tile[0] - inset - 16, 54, inset, inset), site_ring)

    # A recommended option is named as one. RAIC and every feasibility scope say
    # a massing study ends with a recommendation, and a sheet without one is an
    # inventory rather than a proposal.
    heading = _font(12, bold=True)
    draw.text((10, 6), _elide(mark + title, heading, tile[0] - 20), font=heading, fill=_INK)

    # The thesis, then the numbers. It was the numbers alone, and the numbers
    # are the part a jury does not read: what an option is for is a sentence,
    # and OMA gives every option a name for exactly this reason. The sentence
    # was already being carried on the form as `formal_principle` and thrown
    # away at the tile.
    y = tile[1] - reserve + 8
    for text in thesis_lines:
        draw.text((10, y), text, font=body, fill=(52, 52, 58))
        y += 13
    draw.text((10, y + 1), _elide(numbers, body, tile[0] - 20), font=body, fill=(120, 120, 128))
    return panel
