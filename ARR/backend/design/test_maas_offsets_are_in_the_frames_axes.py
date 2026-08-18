"""A move written "along" has to go along, on a parcel at any bearing.

`_Frame` is the parcel's own rectangle and it is almost never square to north:
Uijeongbu's bearing is -168.3 degrees, Gangnam's 35.5, Jongno's 165.0. Two
conventions met inside `frame.box` and neither was stated at the call sites.
`_direction` returns its vectors in the frame's axes - its own docstring says
so, and its named-line branch rotates a world direction back into them - while
`box` added those vectors straight onto a world centre. At -168 degrees the
cosine is -0.979, so a move meant to run along the frame ran very nearly
backwards along it.

A top-level `split` survived that, which is why it went unseen: its two halves
are symmetric about one centre, so reversing the sides only swaps their names.
A second `split` aimed at one of those halves did not, because the parent's
offset was a world quantity and the child's shift a frame one, and adding them
put the child across the gap the first cut had opened.

Measured before the fix, on all three parcels: `kr_hansol_gym_is_its_own_body`
declares 2.58 m between `civic` and `gym` and 1.82 m inside `civic`, and stood
`library` 0.00 m from `gym`.
"""

import math

from django.test import SimpleTestCase
from shapely.geometry import Polygon

from design.maas.massv2.compile import _plan
from design.maas.massv2.execute import _Frame, execute
from design.maas.massv2.grammar import JOINT_CLEARANCE_M, parti_from_record


# ⚠️ Away from the origin, and it has to be. A parcel centred on (0, 0) makes
# the frame's own axes and the world's numerically identical, so a verb that
# reads a frame offset as a world point is indistinguishable from a correct one
# and the file passes with the conversion deliberately removed. That happened
# here, on the second falsification pass. Real parcels are in a projected
# system: the Uijeongbu plot sits near (208000, 553000) in EPSG:5186.
PLOT_AT = (208_400.0, 553_100.0)


def _square(side: float) -> Polygon:
    half = side / 2.0
    ox, oy = PLOT_AT
    return Polygon([(ox - half, oy - half), (ox + half, oy - half),
                    (ox + half, oy + half), (ox - half, oy + half)])


def _axis(degrees: float) -> tuple[float, float]:
    """The frame's bearing comes from the open side, not from the plot.

    ⚠️ The first version of this file rotated the parcel and left the axis at
    (1, 0), and `seed_rectangle` reads its rotation off the axis whenever one
    is given - so every case ran at `frame.rotation == 0.0` and the file passed
    with the fix deliberately removed. Vary the axis.
    """

    bearing = math.radians(degrees)
    return (math.cos(bearing), math.sin(bearing))


# The three live bearings - Uijeongbu, Gangnam, Jongno - plus two plain ones.
BEARINGS = (0.0, -168.3, 35.54, 164.96, 90.0)


class OffsetsAreInTheFramesAxesTests(SimpleTestCase):
    def test_a_frame_offset_turns_with_the_frame(self):
        for degrees in BEARINGS:
            frame = _Frame(_square(60.0), _axis(degrees), height_m=12.0)
            along = frame.out(1.0, 0.0)
            bearing = math.radians(frame.rotation)
            self.assertAlmostEqual(along[0], math.cos(bearing), places=9, msg=str(degrees))
            self.assertAlmostEqual(along[1], math.sin(bearing), places=9, msg=str(degrees))

    def test_a_world_point_and_back_is_the_same_point(self):
        for degrees in BEARINGS:
            frame = _Frame(_square(60.0), _axis(degrees), height_m=12.0)
            for point in ((frame.cx + 7.0, frame.cy - 3.0), (frame.cx, frame.cy + 11.0)):
                local = frame.local(*point)
                back = frame.out(*local)
                self.assertAlmostEqual(frame.cx + back[0], point[0], places=6)
                self.assertAlmostEqual(frame.cy + back[1], point[1], places=6)


class ASecondCutKeepsTheFirstCutsGapTests(SimpleTestCase):
    """The sentence that found this, reduced to its two splits."""

    SENTENCE = parti_from_record({
        "name": "two_cuts",
        "primary_language": "two_bodies",
        "ops": [
            {"op": "extrude", "height": 0.72},
            {"op": "split", "ratio": 0.56, "along": "cross", "first": "civic",
             "second": "gym", "gap": 3.4, "contrast": 1.5},
            {"op": "split", "ratio": 0.64, "along": "long", "on": "civic",
             "first": "office", "second": "library", "gap": 2.4, "contrast": 1.55},
        ],
    })

    def _parts(self, degrees: float) -> dict[str, Polygon]:
        form = execute(
            self.SENTENCE,
            buildable=_square(60.0),
            axis=_axis(degrees),
            height_m=16.8,
            storey_height_m=4.2,
        )
        return {item.role.split("|")[0]: _plan(item) for item in form.additive()}

    def test_the_child_of_a_cut_does_not_cross_into_its_parents_sibling(self):
        owed = 2.4 * JOINT_CLEARANCE_M
        for degrees in BEARINGS:
            parts = self._parts(degrees)
            self.assertEqual(set(parts), {"office", "library", "gym"}, msg=str(degrees))
            for child in ("office", "library"):
                distance = parts[child].distance(parts["gym"])
                self.assertGreaterEqual(
                    distance, owed - 0.01,
                    msg=f"{child} stands {distance:.2f} m from gym at {degrees} deg",
                )

    def test_the_second_gap_is_the_one_that_was_written(self):
        owed = 2.4 * JOINT_CLEARANCE_M
        for degrees in BEARINGS:
            parts = self._parts(degrees)
            distance = parts["office"].distance(parts["library"])
            self.assertAlmostEqual(distance, owed, delta=0.05, msg=str(degrees))


class VerbsThatPlaceAbsolutelyStayOnTheParcelTests(SimpleTestCase):
    """`taper` and `twist` hand a world corner straight to `stack`.

    Every other verb offsets through `frame.box`, which converts. These two do
    not, and when `_bounds_of` began returning its centre in the frame's axes
    they kept reading it as a world point - so the slabs were built near the
    origin instead of on the parcel, and the legal clip then removed the whole
    building. `nishizawa_teshima` compiled to 2 bands and 2,754 m² raw and to
    `None` clipped, which the silence gate read as two words that did nothing.
    """

    def _form(self, verb: str, degrees: float):
        sentence = parti_from_record({
            "name": f"one_{verb}",
            "primary_language": "solid_body",
            "ops": [{"op": "extrude", "height": 0.9},
                    {"op": verb, "ratio": 0.45, "degrees": 30.0}],
        })
        return execute(
            sentence, buildable=_square(60.0), axis=_axis(degrees),
            height_m=16.8, storey_height_m=4.2,
        )

    def test_the_slabs_stand_where_the_parcel_is(self):
        plot = _square(60.0)
        for verb in ("taper", "twist"):
            for degrees in BEARINGS:
                form = self._form(verb, degrees)
                for item in form.additive():
                    plan = _plan(item)
                    self.assertGreater(
                        plan.intersection(plot).area, 0.5 * plan.area,
                        msg=f"{verb} at {degrees} deg put {item.role} off the plot",
                    )
