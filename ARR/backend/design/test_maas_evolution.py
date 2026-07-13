from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.evolution.island_loop import _island_for, _parameter_mutations, _program_complexity, _simplification_mutations, evolve_massdsl_islands
from design.maas.grammar import SEQUENCES, interpret_sequence
from design.maas.grammar.verb_sequence import VerbCall, VerbSequence


class MaasEvolutionGrammarTest(SimpleTestCase):
    def test_child_budget_is_round_robin_across_islands(self):
        result = evolve_massdsl_islands(
            base_footprint=box(0, 0, 42, 30),
            seed_sequences=SEQUENCES,
            interpret=interpret_sequence,
            max_children=16,
        )
        budget = result.trace["island_child_budget"]
        self.assertTrue(all(budget.get(name, 0) > 0 for name in ("additive", "hybrid", "sectional", "subtractive")))

    def test_parameter_mutations_explore_symmetric_visible_range(self):
        sequence = VerbSequence(
            "bend",
            "bend",
            (
                VerbCall("base", {"proportion": "site"}),
                VerbCall("bend", {"angle": 30.0, "factor": 0.5}),
            ),
        )
        low, high = _parameter_mutations(sequence)
        self.assertEqual(low.calls[1].params["angle"], 22.5)
        self.assertEqual(high.calls[1].params["angle"], 37.5)
        self.assertEqual(low.calls[1].params["factor"], 0.36)
        self.assertEqual(high.calls[1].params["factor"], 0.64)

    def test_island_uses_dominant_topology_not_vertical_modifier(self):
        sequence = VerbSequence(
            "fin",
            "fin",
            (
                VerbCall("base", {"proportion": "site"}),
                VerbCall("extrude", {"axis": "x", "length": 0.3}),
                VerbCall("lift", {"upper_ratio": 0.7}),
                VerbCall("taper", {"top_ratio": 0.8}),
            ),
        )
        self.assertEqual(_island_for(sequence), "additive")

    def test_simplification_rewrite_strictly_reduces_complexity(self):
        sequence = VerbSequence(
            "over_composed",
            "over composed",
            (
                VerbCall("base", {"proportion": "site"}),
                VerbCall("branch", {"angle": 32.0}),
                VerbCall("pinch", {"waist_ratio": 0.62}),
                VerbCall("taper", {"top_ratio": 0.78}),
            ),
        )
        children = _simplification_mutations(sequence)
        self.assertTrue(children)
        self.assertTrue(all(len(child.calls) < len(sequence.calls) for child in children))
        self.assertTrue(all(
            _program_complexity(child.calls) < _program_complexity(sequence.calls)
            for child in children
        ))
        self.assertTrue(all(child.calls[1].verb == "branch" for child in children))
