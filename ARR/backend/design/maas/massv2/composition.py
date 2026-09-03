"""Is this mass composed, or is it parts that happen to be legal?

Every gate in this package answers a question about a single body: can it
stand, does it hold a room, is it inside the envelope. None of them asks the
question an architect asks first - do these parts belong to one another - and
so a field of six equal boxes, each of them lawful and standing, comes back
through the funnel as six good answers and reads on the sheet as rubble.

The literature has one operational answer. Akin and Moustapha watched six
architects massing for two hours each and found the mechanism that structured
every session was the REGULATING ELEMENT: an alignment axis, a symmetry line,
a shared face, a datum. Volumes were freely added and removed, and what
survived the additions - what made the result read as one thing - was that a
small set of these elements explained where every part sat. Their words: the
architects "preserved and even reinforced the underlying structure through
regulating elements".

That is measurable, and this module measures it:

    parts explained by the FEWEST elements that explain them all.

A composition of eight bodies whose faces land on three lines is composed. The
same eight bodies on eight lines of their own are a pile. The second half of
the reading is hierarchy - one body large enough to be the building and the
rest subordinate to it - which is the oldest rule in composition and the one a
random grammar breaks first, because equal parts have no primary.

Neither number is a gate. A gate answers yes or no about physics or law; this
answers "how strongly is this composed", which is the selector's question and
the jury's, and it belongs where they can read it.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, degrees, sin

from design.maas.source_geometry.ir import SourceMass

# How close two faces must be to count as landing on the same line. A wall is
# drawn to the metre in a massing study and read by eye at the scale of a
# parcel; half a metre is under the line weight of the drawing this is judged
# from, and it is the tolerance the alignment verbs already work to.
ALIGNMENT_TOLERANCE_M = 0.5

# How close two directions must be to count as the same direction. Parallel by
# eye, not by construction: a body turned two degrees off its neighbour reads
# as aligned and shares its regulating line.
PARALLEL_TOLERANCE_DEG = 4.0

# How far apart two bodies must be to be two bodies. Half a metre is a
# construction joint; what separates one building from another is space a
# person can occupy or pass through, which is the room-width standard the
# plausibility gate already erodes by. Measured at the joint tolerance, a
# ring whose four bars sat 0.4 m apart read as two bodies before the growth
# loop and one after - and the difference was reported as a lost parti.
SEPARATION_M = 1.5

# A face shorter than this is not a face a line can regulate - it is a corner
# cut or a clip fragment, and letting them vote turned every chamfered plan
# into its own family of axes.
MINIMUM_FACE_M = 4.0

# The share of the whole a body must hold to be the building rather than one
# of several. Below it, no part is primary and the eye has nothing to rest on:
# four bodies of a quarter each is the field that reads as blocks on a tray.
PRIMARY_SHARE = 0.4


@dataclass(frozen=True)
class Composition:
    """What holds the parts together, and what leads them."""

    parts: int
    elements: int
    explained: int
    dominance: float
    datums: int
    # The section relation the plan reading cannot see: the leading body
    # stands off the ground on structure. Pilotis is the oldest of these and
    # the one this project is asked for most often, and to a part-to-whole
    # reading a lifted house and a house on the ground are the same single
    # body - the legs are structure and structure is not a part. Recorded
    # here so the axis is at least honest about what it does not measure.
    lifted: bool = False

    @property
    def explained_share(self) -> float:
        return self.explained / self.parts if self.parts else 0.0

    @property
    def economy(self) -> float:
        """Parts per regulating element - the composition's own efficiency.

        Three lines holding eight bodies is 2.67; eight lines holding eight
        bodies is 1.0, which is the arithmetic of a pile. One part is not a
        composition either way, so it scores neutral.
        """

        if self.parts <= 1:
            return 1.0
        return self.explained / self.elements if self.elements else 0.0

    @property
    def is_composed(self) -> bool:
        """A reading, not a verdict: most parts on few lines, one part leading."""

        if self.parts <= 1:
            return True
        return (self.explained_share >= 0.75
                and self.economy >= 1.75
                and self.dominance >= PRIMARY_SHARE)

    def to_dict(self) -> dict:
        return {
            "schema_version": "arr.maas.massv2_composition.v1",
            "parts": self.parts,
            "regulating_elements": self.elements,
            "explained_parts": self.explained,
            "explained_share": round(self.explained_share, 3),
            "economy": round(self.economy, 2),
            "dominance": round(self.dominance, 3),
            "datums": self.datums,
            "lifted": self.lifted,
            "composed": self.is_composed,
        }


# The four positions a massing can hold in part-to-whole terms. Named the way
# an architect names them, and ordered by how much the whole depends on one
# part. A grid axis wants positions somebody would ask for by name, not a
# continuous score: "give me the one with a base and two wings" is a request;
# "give me the one at 0.62 dominance" is not.
COMPOSITION_BANDS: tuple[tuple[str, str], ...] = (
    ("single_body", "one body: the building is one figure"),
    ("body_and_parts", "one body leads, the rest are subordinate to it"),
    ("paired_bodies", "two bodies of comparable weight, in relation"),
    ("field_of_parts", "many parts, none of them the building on its own"),
)


def band_id(reading: "Composition") -> str:
    """Which of the four part-to-whole positions this mass holds.

    Read off the delivered geometry rather than the sentence: a `split` that
    the growth loop fused back together is one body whatever the words said,
    and the axis exists to spread the SHEET, which is made of what was built.
    """

    if reading.parts <= 1:
        return "single_body"
    if reading.dominance >= PRIMARY_SHARE + 0.2:
        return "body_and_parts"
    if reading.parts == 2:
        return "paired_bodies"
    return "field_of_parts"


def _bodies(source: SourceMass) -> list[tuple[float, list]]:
    """The mass as bodies: bands that overlap in plan and touch are one body.

    The same reading `SourceMass.body_height_m` takes for stature, kept here
    rather than imported back so this module stays readable on its own: a
    compiled band is a slice, and a slice is not a part anybody drew.
    """

    structural = set(source.metadata.get("structural_bands") or ())
    rooms = [volume for index, volume in enumerate(source.volumes)
             if index not in structural]
    rooms.sort(key=lambda volume: float(volume.bottom_fraction))
    columns: list[list] = []
    for volume in rooms:
        for column in columns:
            top = column[-1]
            if float(volume.bottom_fraction) > float(top.top_fraction) + 1e-3:
                continue
            shared = volume.footprint.intersection(top.footprint).area
            if shared > 0.5 * min(volume.footprint.area, top.footprint.area):
                column.append(volume)
                break
        else:
            columns.append([volume])
    # Bodies that TOUCH are one body. Two bays of a gable, the two halves of
    # a split with no gap declared, a bar and the wing built against it: they
    # share a wall, and a wall is not a gap. Counting them apart made the
    # reading unstable - the same house read as two parts before the growth
    # loop and one part after, because a plan scale moved the overlap across
    # the fifty-per-cent line - and that instability was being reported as
    # the pipeline destroying a parti. What separates two bodies is space
    # between them, which is what the declared-gap rule already polices.
    merged = True
    while merged and len(columns) > 1:
        merged = False
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                a_low = min(float(v.bottom_fraction) for v in columns[i])
                a_high = max(float(v.top_fraction) for v in columns[i])
                b_low = min(float(v.bottom_fraction) for v in columns[j])
                b_high = max(float(v.top_fraction) for v in columns[j])
                if min(a_high, b_high) < max(a_low, b_low) - 1e-3:
                    continue  # one is above the other, with nothing shared
                touching = any(
                    va.footprint.distance(vb.footprint) <= SEPARATION_M
                    for va in columns[i] for vb in columns[j]
                )
                if not touching:
                    continue
                columns[i] = columns[i] + columns[j]
                del columns[j]
                merged = True
                break
            if merged:
                break
    out = []
    for column in columns:
        mass = sum(float(v.footprint.area)
                   * max(0.0, float(v.top_fraction) - float(v.bottom_fraction))
                   for v in column)
        out.append((mass, column))
    return out


def _faces(column: list) -> list[tuple[float, float]]:
    """The body's own faces as (direction in degrees, signed offset).

    A face is a line: its bearing folded into [0, 180) because a wall and the
    same wall seen from the other side are one line, and its perpendicular
    distance from the origin, which is what two aligned bodies share.
    """

    faces: list[tuple[float, float]] = []
    for volume in column:
        ring = list(volume.footprint.exterior.coords)
        for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
            dx, dy = x1 - x0, y1 - y0
            length = (dx * dx + dy * dy) ** 0.5
            if length < MINIMUM_FACE_M:
                continue
            bearing = degrees(atan2(dy, dx)) % 180.0
            # Perpendicular offset of the line through (x0, y0) at `bearing`.
            normal = bearing + 90.0
            offset = x0 * cos(normal * 3.141592653589793 / 180.0) + \
                y0 * sin(normal * 3.141592653589793 / 180.0)
            faces.append((bearing, offset))
    return faces


def _same_line(a: tuple[float, float], b: tuple[float, float]) -> bool:
    turn = abs(a[0] - b[0])
    turn = min(turn, 180.0 - turn)
    return turn <= PARALLEL_TOLERANCE_DEG and abs(a[1] - b[1]) <= ALIGNMENT_TOLERANCE_M


def read(source: SourceMass) -> Composition:
    """Read the composition: parts, the lines that explain them, and the lead."""

    bodies = _bodies(source)
    if not bodies:
        return Composition(parts=0, elements=0, explained=0, dominance=0.0, datums=0)
    total = sum(mass for mass, _column in bodies) or 1.0
    dominance = max(mass for mass, _column in bodies) / total

    # Candidate lines: every face of every body. A line is REGULATING when it
    # is shared - two bodies landing on it - which is the whole content of the
    # idea. Lines are then chosen greedily, most bodies first, until every
    # body that can be explained is: the fewest lines that explain them all.
    per_body = [_faces(column) for _mass, column in bodies]
    candidates: list[tuple[tuple[float, float], set[int]]] = []
    for index, faces in enumerate(per_body):
        for face in faces:
            for line, members in candidates:
                if _same_line(line, face):
                    members.add(index)
                    break
            else:
                candidates.append((face, {index}))
    shared = [(line, members) for line, members in candidates if len(members) >= 2]

    covered: set[int] = set()
    elements = 0
    while True:
        best = None
        for line, members in shared:
            gain = len(members - covered)
            if gain >= 1 and (best is None or gain > best[0]):
                best = (gain, line, members)
        # A line that adds one body to a set already covered adds nothing to
        # the reading; the loop stops when nothing new is explained.
        if best is None or best[0] == 0:
            break
        covered |= best[2]
        elements += 1
        shared = [(line, members) for line, members in shared if members - covered]

    # Datums: heights where two or more bodies begin or end together. The
    # horizontal half of the same idea - a shared base, a shared eaves line -
    # and what makes a stepped composition read as one building.
    height = float(source.metadata.get("authored_height_m") or 0.0)
    levels: list[list[float]] = []
    for _mass, column in bodies:
        for value in (float(column[0].bottom_fraction) * height,
                      float(column[-1].top_fraction) * height):
            for group in levels:
                if abs(group[0] - value) <= ALIGNMENT_TOLERANCE_M:
                    group.append(value)
                    break
            else:
                levels.append([value])
    datums = sum(1 for group in levels if len(group) >= 2)

    # Off the ground: the leading body starts above grade and something
    # structural stands under it. A body floating with nothing below is a
    # different fault and the standing gate owns it.
    lead = max(bodies, key=lambda item: item[0])[1]
    lead_base = min(float(volume.bottom_fraction) for volume in lead)
    structural = set(source.metadata.get("structural_bands") or ())
    lifted = bool(
        lead_base > 1e-3
        and any(float(source.volumes[index].bottom_fraction) <= 1e-6
                for index in structural
                if index < len(source.volumes))
    )

    return Composition(
        parts=len(bodies),
        elements=elements,
        explained=len(covered),
        dominance=dominance,
        datums=datums,
        lifted=lifted,
    )
