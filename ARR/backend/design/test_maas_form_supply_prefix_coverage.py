"""The form supply is truncated downstream, so its prefix has to be the bank.

An exact-compile cap evaluates only a head of the supply. In construction
order that head was one program seed crossed with a contiguous run of forms,
which left the rare capability lane (indices 82-85 of 86) and most of the
composition families unreachable no matter what the gates decided.

These tests assert the *property* - a prefix spans the bank, and the bank
itself is unchanged - rather than any family name or index, so the bank can
grow without editing them.
"""

from collections import Counter

from django.test import SimpleTestCase

from design.maas.book_language.candidate_generation import _agent_mutated_seeds
from design.maas.geometry_language.universal_form_bank import (
    stratified_form_supply_order,
    universal_form_programs,
)


def _families(programs):
    return [str(program.metadata.get("family") or "") for program in programs]


def _lanes(programs):
    return [str(program.metadata.get("form_bank_lane") or "") for program in programs]


def _source_seed(sequence):
    for note in sequence.notes:
        if note.startswith("geometry_program_source_seed="):
            return note.split("=", 1)[1]
    return ""


def _carries_universal_form(sequence):
    return any(
        note.startswith("geometry_program_payload=")
        for note in sequence.notes
    )


class StratifiedFormSupplyOrderTests(SimpleTestCase):
    def test_order_is_a_permutation_of_the_bank(self):
        for page in (0, 1, 2):
            with self.subTest(page=page):
                bank = universal_form_programs(page)
                ordered = stratified_form_supply_order(bank)

                self.assertEqual(
                    sorted(program.program_hash() for program in ordered),
                    sorted(program.program_hash() for program in bank),
                )

    def test_no_family_repeats_before_every_family_has_appeared(self):
        ordered = stratified_form_supply_order(universal_form_programs(0))
        families = _families(ordered)
        distinct = len(set(families))

        # The first round has to be one program per family, in some order.
        self.assertEqual(len(set(families[:distinct])), distinct)

    def test_a_prefix_the_size_of_the_bank_families_reaches_every_lane(self):
        ordered = stratified_form_supply_order(universal_form_programs(0))
        families = _families(ordered)
        lanes = _lanes(ordered)
        head = len(set(families))

        self.assertEqual(set(lanes[:head]), set(lanes))

    def test_the_rarest_lane_is_reachable_far_earlier_than_in_bank_order(self):
        bank = universal_form_programs(0)
        ordered = stratified_form_supply_order(bank)
        rarest = Counter(_lanes(bank)).most_common()[-1][0]

        def first_index(programs):
            return next(
                index
                for index, lane in enumerate(_lanes(programs))
                if lane == rarest
            )

        self.assertLess(first_index(ordered), first_index(bank))

    def test_empty_supply_is_handled(self):
        self.assertEqual(stratified_form_supply_order(()), ())


class UniversalSeedCrossProductTests(SimpleTestCase):
    """The cross product is where the diversity budget is actually spent."""

    programs = ("cultural", "neighborhood_living", "gymnasium")

    def test_every_program_seed_reaches_the_cross_product(self):
        from design.maas.program_massing.sequences import program_seed_sequences

        for program in self.programs:
            with self.subTest(program=program):
                expected = {
                    sequence.name
                    for sequence in program_seed_sequences(program)
                }
                seeds = _agent_mutated_seeds(
                    program, None, None, None, None,
                    universal_variation_pages=(0,),
                )
                reached = {
                    _source_seed(sequence)
                    for sequence in seeds
                    if _carries_universal_form(sequence)
                }

                self.assertEqual(reached, expected)

    def test_a_short_head_spans_both_seeds_and_forms(self):
        for program in self.programs:
            with self.subTest(program=program):
                seeds = [
                    sequence
                    for sequence in _agent_mutated_seeds(
                        program, None, None, None, None,
                        universal_variation_pages=(0,),
                    )
                    if _carries_universal_form(sequence)
                ]
                seed_names = {
                    _source_seed(sequence)
                    for sequence in seeds
                }
                head = seeds[:len(universal_form_programs(0))]

                # One pass over the bank is one distinct form each...
                self.assertEqual(len(head), len({
                    sequence.name.rsplit("_", 1)[-1] for sequence in head
                }))
                # ...and it still rotates through every program seed.
                self.assertEqual(
                    {_source_seed(sequence) for sequence in head},
                    seed_names,
                )

    def test_every_seed_and_form_pairing_is_still_produced(self):
        seeds = [
            sequence
            for sequence in _agent_mutated_seeds(
                "cultural", None, None, None, None,
                universal_variation_pages=(0,),
            )
            if _carries_universal_form(sequence)
        ]
        pairings = {
            (_source_seed(sequence), sequence.name.rsplit("_", 1)[-1])
            for sequence in seeds
        }
        seed_count = len({_source_seed(sequence) for sequence in seeds})

        self.assertEqual(
            len(pairings),
            seed_count * len(universal_form_programs(0)),
        )
