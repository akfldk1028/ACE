"""Placed volumes have to reach shapes the face-operation language cannot.

The existing language is face operations on one solid. Measured on a 40x24x18
reference box with every operative pushed to its strongest accepted setting,
departure from the mass's own convex hull tops out at 0.29 - and five of the ten
operatives could not be seen at all by the void axis, because a flattened plan
projection closes any opening that has something above it.

These tests hold three things about the replacement:

  * a plain box measures as a plain box (the measure is not simply generous),
  * a stepped stack is not called plain (plan measures alone said 0.000),
  * the language reaches `porous_field`, which four consecutive live runs of the
    old language never produced once.
"""

from django.test import SimpleTestCase

from design.maas.massv2 import MatrixForm, compile_matrix_form, measure_form, place


def _form(name, placements, **kwargs):
    kwargs.setdefault("primary_language", "test_language")
    return MatrixForm(name=name, placements=tuple(placements), **kwargs)


def _measured(form):
    source = compile_matrix_form(form)
    assert source is not None, f"{form.name} failed to compile"
    return source, measure_form(source)


class PlainThingsMeasurePlainTests(SimpleTestCase):
    def test_a_single_extrusion_is_flat_on_every_axis(self):
        _source, measurement = _measured(_form("box", [place("box", size=(30, 20, 16))]))

        self.assertAlmostEqual(0.0, measurement.convexity_drop, places=3)
        self.assertAlmostEqual(0.0, measurement.plan_void_ratio, places=3)
        self.assertAlmostEqual(0.0, measurement.section_change, places=3)
        self.assertAlmostEqual(0.0, measurement.articulation(), places=3)

    def test_a_rotated_box_is_still_flat(self):
        """Void measured against an axis-aligned box reads 0.52 at 45 degrees.

        That is orientation, not void, and it contaminated the void axis until
        it was re-based on the tightest rectangle. Hold that here too.
        """

        _source, measurement = _measured(
            _form("turned", [place("box", size=(30, 20, 16), rotation_degrees=37.0)])
        )

        self.assertAlmostEqual(0.0, measurement.plan_void_ratio, places=3)


class SectionIsArticulationTooTests(SimpleTestCase):
    def test_a_stepped_stack_is_not_reported_plain(self):
        """Every storey of a setback tower is a convex closed rectangle.

        Plan convexity and plan void both read 0.000 for it. Reporting only
        those would file a whole family of massing as a plain box.
        """

        _source, measurement = _measured(
            _form(
                "stack",
                [
                    place("plinth", size=(34, 22, 5)),
                    place("mid", size=(24, 18, 7), at=(6, 2, 4.9)),
                    place("tower", size=(14, 14, 9), at=(2, 6, 11.8)),
                ],
            )
        )

        self.assertAlmostEqual(0.0, measurement.convexity_drop, places=2)
        self.assertGreater(measurement.section_change, 0.2)
        self.assertGreater(measurement.articulation(), 0.2)


class SeparatedPiecesSurviveTests(SimpleTestCase):
    def test_two_bars_with_a_gap_keep_both_bars(self):
        """Keeping only the largest piece of a band deletes half the building.

        Measured before the fix, a paired-bar scheme read 0.05 open because one
        bar was dropped; both present it is a quarter open.
        """

        source, measurement = _measured(
            _form(
                "bars",
                [
                    place("bar_a", size=(36, 9, 18)),
                    place("bar_b", size=(36, 9, 18), at=(0, 15, 0)),
                ],
            )
        )
        ground = [item for item in source.volumes if item.bottom_fraction <= 1e-6]

        self.assertEqual(2, len(ground))
        self.assertGreater(measurement.plan_void_ratio, 0.2)

    def test_the_pieces_of_one_band_share_that_band(self):
        """They are one storey of one building, not two buildings."""

        source, _measurement = _measured(
            _form(
                "bars",
                [
                    place("bar_a", size=(36, 9, 18)),
                    place("bar_b", size=(36, 9, 18), at=(0, 15, 0)),
                ],
            )
        )
        spans = {(item.bottom_fraction, item.top_fraction) for item in source.volumes}

        self.assertEqual(1, len(spans))


class ReachesWhatTheOldLanguageCouldNotTests(SimpleTestCase):
    OLD_LANGUAGE_CEILING = 0.29

    def test_porous_field_is_reachable(self):
        """Four consecutive live runs of the old language produced none."""

        _source, measurement = _measured(
            _form(
                "splayed",
                [
                    place("a", size=(30, 8, 17)),
                    place("b", size=(30, 8, 17), at=(0, 14, 0), rotation_degrees=18.0),
                    place("core", size=(8, 8, 17), at=(0, 7, 0)),
                ],
            )
        )

        self.assertEqual("porous_field", measurement.void_band_id)

    def test_articulation_clears_the_face_operation_ceiling(self):
        _source, measurement = _measured(
            _form(
                "cross",
                [
                    place("base", size=(16, 16, 9)),
                    place("arm", size=(38, 10, 6), at=(-11, 3, 8.9)),
                    place("cap", size=(12, 30, 5), at=(2, -7, 14.5)),
                ],
            )
        )

        self.assertGreater(measurement.articulation(), self.OLD_LANGUAGE_CEILING)


class SubtractionIsPerBandTests(SimpleTestCase):
    def test_a_roofed_court_still_reads_as_a_court_below_the_roof(self):
        """This is the case a flattened union closes and the axis then misses."""

        _source, measurement = _measured(
            _form(
                "roofed_court",
                [
                    place("body", size=(30, 24, 12)),
                    place("court", size=(12, 10, 14), at=(9, 7, -1), kind="subtractive"),
                    place("roof", size=(30, 24, 3), at=(0, 0, 11.9)),
                ],
            )
        )

        self.assertGreater(measurement.plan_void_ratio, 0.0)

    def test_a_cutter_does_not_set_the_building_height(self):
        """A cutter is pushed past the face so its cut lands cleanly.

        Letting it define the height would inflate the building by however far
        it was pushed out.
        """

        form = _form(
            "cut",
            [
                place("body", size=(30, 24, 12)),
                place("court", size=(12, 10, 40), at=(9, 7, -14), kind="subtractive"),
            ],
        )

        self.assertAlmostEqual(12.0, form.height_m(), places=6)
