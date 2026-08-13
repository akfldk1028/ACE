"""A verb the author left bare must still reach more than one magnitude.

`_parameter_mutations` built its mutable set as `if i > 0 and call.params`, so a
call carrying no numeric parameter was skipped by every variant and compiled at
the single value the adapter falls back to. Measured on the live Uijeongbu run,
every `carve` in the pool was the identical carve - while the operative's own
range runs from a convex-hull departure of 0.004 to 0.200, and 0.200 is what
`branch` reaches. That is the shape of the supply ceiling: 39 candidates, 10
distinct silhouettes, many names over few forms.

The seed values come from the bounds the grammar already declares for the verb,
so no constant is introduced and nothing is fitted to a parcel.
"""

from django.test import SimpleTestCase

from design.maas.evolution.island_loop import _parameter_mutations, _seeded_for_mutation
from design.maas.grammar.parameter_schema import PARAMETER_BOUNDS, PARAMETERS_BY_VERB
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence


def _sequence(*calls):
    return VerbSequence(
        name="test", label="test", calls=(VerbCall("base", {}), *calls), notes=()
    )


class ParamlessCallsReachSeveralMagnitudesTests(SimpleTestCase):
    def test_a_bare_carve_produces_two_different_carves(self):
        variants = _parameter_mutations(_sequence(VerbCall("carve", {})))

        carves = [
            call.params
            for variant in variants
            for call in variant.calls
            if call.verb == "carve"
        ]

        self.assertEqual(2, len(carves))
        self.assertNotEqual(carves[0], carves[1])

    def test_the_widths_land_either_side_of_the_declared_middle(self):
        """0.72x and 1.28x of the middle, not two points in the same corner."""

        low, high = PARAMETER_BOUNDS["width_ratio"]
        middle = (low + high) / 2.0
        variants = _parameter_mutations(_sequence(VerbCall("carve", {})))
        widths = sorted(
            call.params["width_ratio"]
            for variant in variants
            for call in variant.calls
            if call.verb == "carve"
        )

        self.assertLess(widths[0], middle)
        self.assertGreater(widths[1], middle)

    def test_every_seeded_value_is_inside_its_own_declared_bounds(self):
        for verb in ("carve", "grade", "notch", "extract", "fracture", "lodge"):
            with self.subTest(verb=verb):
                for name, value in _seeded_for_mutation(VerbCall(verb, {})).params.items():
                    low, high = PARAMETER_BOUNDS[name]
                    self.assertGreaterEqual(value, low)
                    self.assertLessEqual(value, high)

    def test_a_signed_range_is_not_seeded_to_its_midpoint(self):
        """The middle of (-55, 55) is no rotation at all, not a middle angle."""

        seeded = _seeded_for_mutation(VerbCall("fracture", {})).params

        self.assertNotIn("angle", seeded)
        self.assertIn("gap_ratio", seeded)

    def test_a_call_the_author_did_fill_in_is_left_alone(self):
        """Seeding over an authored value would overwrite a design decision."""

        authored = VerbCall("carve", {"width_ratio": 0.31})

        self.assertEqual(authored.params, _seeded_for_mutation(authored).params)

    def test_a_verb_with_no_declared_numbers_is_returned_unchanged(self):
        bare = VerbCall("base", {})

        self.assertIs(bare, _seeded_for_mutation(bare))

    def test_the_parent_sequence_still_compiles_as_it_did(self):
        """Only the variants are seeded; the original is not rewritten."""

        parent = _sequence(VerbCall("carve", {}))
        _parameter_mutations(parent)

        self.assertEqual({}, parent.calls[1].params)

    def test_it_reaches_the_operatives_that_were_pinned(self):
        """Each of these was measured stuck at one magnitude in the live run."""

        for verb in ("carve", "grade", "notch", "extract", "fracture"):
            with self.subTest(verb=verb):
                variants = _parameter_mutations(_sequence(VerbCall(verb, {})))
                params = [
                    call.params
                    for variant in variants
                    for call in variant.calls
                    if call.verb == verb
                ]

                self.assertNotEqual(params[0], params[1])

    def test_the_seeds_are_the_grammar_and_not_a_table_here(self):
        """If the grammar's bounds move, the seed moves with them."""

        seeded = _seeded_for_mutation(VerbCall("notch", {})).params
        low, high = PARAMETER_BOUNDS["ratio"]

        self.assertIn("ratio", PARAMETERS_BY_VERB["notch"])
        self.assertAlmostEqual(round((low + high) / 2.0, 3), seeded["ratio"])
