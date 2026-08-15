"""A vocabulary drawn from the parcel says the parcel's own numbers.

Seventy-six hand-written sentences filled sixteen of sixteen cells on the plot
they were written against and ten of sixteen on a commercial site, and their
stated reasons still described a four-storey building on a sixteen-storey plot.
The masses adapted; the reasoning did not. These tests hold the two things that
have to be true of a generated vocabulary for that to stop happening:

  * a sentence quotes the site it was drawn on, so the same draw on a different
    parcel is a different sentence and not the same one resized,
  * a truncated draw still covers the void axis, because a run that stops at N
    must not be all stacks.
"""

from django.test import SimpleTestCase

from design.maas.massv2.grammar import (
    MAX_OFFSET_RATIO,
    MIN_OFFSET_RATIO,
    MIN_TIER_CONTRAST,
    parti_from_record,
)
from design.maas.massv2.sampler import SiteFacts, sample_sentences


def _facts(**overrides) -> SiteFacts:
    base = dict(
        storeys_allowed=4.17,
        bcr_limit_pct=59.9,
        far_limit_pct=249.7,
        parcel_area_m2=2499.7,
        buildable_m2=1497.9,
        skew=0.795,
        party_edges=5,
        open_side="한 면",
    )
    base.update(overrides)
    return SiteFacts(**base)


class SentencesQuoteTheirParcelTests(SimpleTestCase):
    def test_the_storey_count_in_the_reason_is_this_parcel_s(self):
        low = sample_sentences(_facts(storeys_allowed=4.17), limit=40)
        high = sample_sentences(_facts(storeys_allowed=16.3), limit=40)

        low_reasons = " ".join(op["why"] for item in low for op in item["ops"])
        high_reasons = " ".join(op["why"] for item in high for op in item["ops"])

        self.assertIn("4.2층", low_reasons)
        self.assertNotIn("16.3층", low_reasons)
        self.assertIn("16.3층", high_reasons)
        self.assertNotIn("4.2층", high_reasons)

    def test_a_parcel_that_affords_more_storeys_offers_more_tiers(self):
        def tiers(storeys):
            drawn = sample_sentences(_facts(storeys_allowed=storeys), limit=400)
            return {
                op["n"]
                for item in drawn
                for op in item["ops"]
                if op["op"] == "stack"
            }

        self.assertLess(max(tiers(4.17)), max(tiers(16.3)))

    def test_a_short_draw_reaches_every_way_the_mass_can_arrive(self):
        """`product` varies its first iterable slowest, so bucketing on void
        alone drew every sentence from `extrude` and never reached the rest."""

        drawn = sample_sentences(_facts(), limit=40)
        bases = {op["op"] for item in drawn for op in item["ops"]}
        self.assertTrue({"extrude", "stack", "loop", "aggregate"} <= bases, bases)

    def test_a_draw_holds_both_divided_and_undivided_masses(self):
        """Leaving the cut out of the bucket key drew 94% undivided, because a
        bucket's own order runs every whole-mass combination first."""

        drawn = sample_sentences(_facts(), limit=120)
        split = sum(1 for item in drawn if any(op["op"] == "split" for op in item["ops"]))
        self.assertGreater(split, 0)
        self.assertLess(split, len(drawn))
        self.assertGreater(split / len(drawn), 0.2)

    def test_a_small_plot_does_not_offer_a_six_object_field(self):
        small = sample_sentences(_facts(buildable_m2=300.0), limit=400)
        counts = {
            op["n"] for item in small for op in item["ops"] if op["op"] == "aggregate"
        }
        self.assertTrue(counts)
        self.assertLessEqual(max(counts), 3)


class ATruncatedDrawStillCoversTheAxisTests(SimpleTestCase):
    def test_every_void_family_appears_in_a_short_draw(self):
        drawn = sample_sentences(_facts(), limit=16)
        families = {item["primary_language"] for item in drawn}
        self.assertEqual(
            families,
            {"solid_body", "carved_body", "open_figure", "porous_field"},
        )

    def test_the_draw_is_the_same_twice(self):
        first = [item["name"] for item in sample_sentences(_facts(), limit=60)]
        second = [item["name"] for item in sample_sentences(_facts(), limit=60)]
        self.assertEqual(first, second)


class EverySentenceIsWellFormedTests(SimpleTestCase):
    def setUp(self):
        self.drawn = sample_sentences(_facts(), limit=240)

    def test_every_sentence_parses_into_a_parti(self):
        for item in self.drawn:
            self.assertIsNotNone(parti_from_record(item), item["name"])

    def test_no_move_is_aimed_at_a_part_the_sentence_never_cut(self):
        """A verb scoped to a wing that was never grown is silent by design, and
        a silent verb leaves the base mass wearing a name it did not earn."""

        for item in self.drawn:
            names = {
                op.get("first") for op in item["ops"] if op["op"] == "split"
            } | {op.get("second") for op in item["ops"] if op["op"] == "split"}
            for op in item["ops"]:
                scope = op.get("on")
                if scope:
                    self.assertIn(scope, names, item["name"])

    def test_magnitudes_stay_inside_the_corpus_bands(self):
        for item in self.drawn:
            for op in item["ops"]:
                if op["op"] == "shear":
                    self.assertGreaterEqual(op["ratio"], MIN_OFFSET_RATIO)
                    self.assertLessEqual(op["ratio"], MAX_OFFSET_RATIO)
                if op["op"] == "stack":
                    self.assertGreaterEqual(op["contrast"], MIN_TIER_CONTRAST)

    def test_every_move_carries_a_reason(self):
        for item in self.drawn:
            for op in item["ops"]:
                self.assertTrue(op.get("why"), f"{item['name']} / {op['op']}")
