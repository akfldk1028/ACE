"""A sentence can choose what it acts on, which is the BOOK's first move.

`book_language.semantics` says it in its first paragraph: a base operative is a
three-part grammar - choose a relative base volume and an orientation, perform
one spatial action, then explore that action's bounded variations. massv2 only
ever had the middle part. Every sentence started from `seed_rectangle`, the
parcel's own extent, so every mass began as the plot, and six blind jurors kept
writing the same sentence about it: an object placed on the parcel rather than
a building that has reckoned with its edges.
"""

from __future__ import annotations

from django.test import SimpleTestCase
from shapely.geometry import Polygon

from design.maas.massv2.execute import _base_volume_extent, execute
from design.maas.massv2.grammar import (
    BASE_ORIENTATIONS,
    BASE_VOLUME_LABELS,
    parti_from_record,
)

SENTENCE = {
    "name": "base_volume_test",
    "primary_language": "solid_body",
    "secondary_language": "a test",
    "formal_principle": "a test",
    "dominant_gesture": "a test",
    "reference_basis": "a test",
    "floor_height_m": 4.0,
    "ops": [{"op": "extrude", "height": 1.0, "storeys": 4, "profile": "square",
             "why": "seed"}],
}
PLOT = Polygon([(0.0, 0.0), (60.0, 0.0), (60.0, 40.0), (0.0, 40.0)])


class BaseVolumeTests(SimpleTestCase):
    def test_the_book_six_fractions_and_three_orientations_are_sayable(self):
        self.assertEqual(BASE_VOLUME_LABELS,
                         {"1/1", "3/8", "1/2", "1/4", "1/8", "1/16"})
        self.assertEqual(BASE_ORIENTATIONS,
                         {"long_axis", "short_axis", "vertical"})

    def test_a_fraction_falls_on_the_axis_the_orientation_names(self):
        # A quarter taken vertically is a tower and a quarter taken along is a
        # bar; a fraction is not a scalar on every axis at once.
        self.assertEqual(_base_volume_extent(60.0, 40.0, "1/4", "long_axis"),
                         (15.0, 40.0, 1.0))
        self.assertEqual(_base_volume_extent(60.0, 40.0, "1/4", "short_axis"),
                         (60.0, 10.0, 1.0))
        self.assertEqual(_base_volume_extent(60.0, 40.0, "1/4", "vertical"),
                         (60.0, 40.0, 0.25))

    def test_silence_is_the_whole_plot_so_the_corpus_does_not_move(self):
        self.assertEqual(_base_volume_extent(60.0, 40.0, None, None),
                         (60.0, 40.0, 1.0))
        self.assertEqual(_base_volume_extent(60.0, 40.0, "1/1", "vertical"),
                         (60.0, 40.0, 1.0))

    def test_a_label_nobody_can_name_is_silence_not_a_guess(self):
        parti = parti_from_record(dict(SENTENCE, base_volume="2/3",
                                       base_orientation="sideways"))
        self.assertIsNone(parti.base_volume)
        self.assertIsNone(parti.base_orientation)

    def test_the_sentence_carries_its_choice_into_the_delivered_mass(self):
        whole = execute(parti_from_record(SENTENCE), buildable=PLOT,
                        axis=(1.0, 0.0), height_m=16.0, storey_height_m=4.0)
        quarter = execute(
            parti_from_record(dict(SENTENCE, base_volume="1/4",
                                   base_orientation="long_axis")),
            buildable=PLOT, axis=(1.0, 0.0), height_m=16.0, storey_height_m=4.0)
        self.assertIsNotNone(whole)
        self.assertIsNotNone(quarter)
        def widest(form):
            corners = [corner for item in form.additive() for corner in item.corners()]
            xs = [corner[0] for corner in corners]
            return max(xs) - min(xs)

        # `plan` on a Placement is the figure's NAME, not its polygon; the
        # extent has to come off the posed corners.
        self.assertLess(widest(quarter), widest(whole) * 0.5,
                        "a quarter of the plot should not span half of it")
