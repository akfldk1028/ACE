from math import log

from django.test import SimpleTestCase
from shapely.geometry import box, mapping

from design.maas.geometry_language.legal_envelope import (
    normalized_legal_field_design_context,
)
from design.maas.geometry_language.legal_envelope.seed_conditioning import (
    envelope_seed_conditioning,
)
from design.maas.geometry_language.legal_envelope.supply_ranking import (
    rank_programs_by_lawful_fit,
    seed_plan_aspect,
)
from design.maas.geometry_language.universal_form_bank import (
    universal_form_programs,
)


def _conditioning(sections):
    return envelope_seed_conditioning(
        normalized_legal_field_design_context({
            "candidate_legal_floor_sections": [mapping(s) for s in sections]
        })
    )


class LawfulFitRankingTests(SimpleTestCase):
    """Ranking may reorder the supply; it may never change or lose it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.programs = universal_form_programs(0)

    def test_absent_conditioning_leaves_the_supply_untouched(self):
        for conditioning in ({}, None):
            with self.subTest(conditioning=conditioning):
                ranked = rank_programs_by_lawful_fit(
                    self.programs, conditioning
                )
                self.assertEqual(
                    [program.program_hash() for program in ranked],
                    [program.program_hash() for program in self.programs],
                )

    def test_ranking_is_a_permutation_of_the_supply(self):
        conditioning = _conditioning([box(0, 0, 16, 10), box(0, 0, 16, 5)])

        ranked = rank_programs_by_lawful_fit(self.programs, conditioning)

        self.assertEqual(len(ranked), len(self.programs))
        self.assertEqual(
            sorted(program.program_hash() for program in ranked),
            sorted(program.program_hash() for program in self.programs),
        )

    def test_the_lawful_proportion_leads_the_supply(self):
        # Throughput: the first thing evaluated should be the seed that fits the
        # lawful ground best.
        conditioning = _conditioning([box(0, 0, 16, 10), box(0, 0, 16, 5)])
        self.assertAlmostEqual(conditioning["plan_aspect"], 1.6, places=6)

        ranked = rank_programs_by_lawful_fit(self.programs, conditioning)

        measured = [
            aspect
            for aspect in (seed_plan_aspect(p) for p in self.programs)
            if aspect is not None
        ]
        best = min(measured, key=lambda value: abs(log(value / 1.6)))
        self.assertAlmostEqual(seed_plan_aspect(ranked[0]), best, places=9)

    def test_the_leading_block_covers_the_range_instead_of_clustering(self):
        # Diversity: sorting by distance alone front-loads near-identical
        # proportions, which is what collapsed the portfolio's aspect spread.
        # The leading block must span more of the range than the nearest block.
        conditioning = _conditioning([box(0, 0, 16, 10), box(0, 0, 16, 5)])

        ranked = rank_programs_by_lawful_fit(self.programs, conditioning)

        leading = [
            aspect
            for aspect in (seed_plan_aspect(p) for p in ranked[:12])
            if aspect is not None
        ]
        nearest = sorted(
            (
                aspect
                for aspect in (seed_plan_aspect(p) for p in self.programs)
                if aspect is not None
            ),
            key=lambda value: abs(log(value / 1.6)),
        )[:12]

        self.assertGreater(
            max(leading) - min(leading),
            max(nearest) - min(nearest),
        )

    def test_ranking_is_deterministic(self):
        conditioning = _conditioning([box(0, 0, 16, 10), box(0, 0, 16, 5)])

        first = rank_programs_by_lawful_fit(self.programs, conditioning)
        second = rank_programs_by_lawful_fit(self.programs, conditioning)

        self.assertEqual(
            [program.program_hash() for program in first],
            [program.program_hash() for program in second],
        )

    def test_a_different_lawful_ground_produces_a_different_order(self):
        wide = _conditioning([box(0, 0, 24, 6), box(0, 0, 24, 3)])
        square = _conditioning([box(0, 0, 12, 12), box(0, 0, 12, 6)])

        self.assertNotEqual(
            [
                program.program_hash()
                for program in rank_programs_by_lawful_fit(self.programs, wide)
            ],
            [
                program.program_hash()
                for program in rank_programs_by_lawful_fit(
                    self.programs, square
                )
            ],
        )

    def test_uncompilable_programs_do_not_break_ranking(self):
        class _Broken:
            nodes = ()

            def program_hash(self):
                return "broken"

        conditioning = _conditioning([box(0, 0, 16, 10), box(0, 0, 16, 5)])
        supply = (*self.programs[:5], _Broken())

        ranked = rank_programs_by_lawful_fit(supply, conditioning)

        self.assertEqual(len(ranked), 6)
        self.assertEqual(ranked[-1].program_hash(), "broken")


class FormBankWiringTests(SimpleTestCase):
    """The form bank pages themselves must not change; only their order may."""

    def test_pages_without_conditioning_are_byte_identical(self):
        from design.maas.geometry_language.universal_form_bank import (
            universal_form_program_pages,
        )

        baseline = universal_form_program_pages((0, 1))

        for conditioning in (None, {}):
            with self.subTest(conditioning=conditioning):
                self.assertEqual(
                    [
                        program.program_hash()
                        for program in universal_form_program_pages(
                            (0, 1), envelope_conditioning=conditioning
                        )
                    ],
                    [program.program_hash() for program in baseline],
                )

    def test_conditioned_pages_reorder_without_changing_membership(self):
        from design.maas.geometry_language.universal_form_bank import (
            universal_form_program_pages,
        )

        baseline = universal_form_program_pages((0, 1))
        conditioned = universal_form_program_pages(
            (0, 1),
            envelope_conditioning=_conditioning(
                [box(0, 0, 24, 6), box(0, 0, 24, 3)]
            ),
        )

        self.assertEqual(
            sorted(program.program_hash() for program in conditioned),
            sorted(program.program_hash() for program in baseline),
        )
        self.assertNotEqual(
            [program.program_hash() for program in conditioned],
            [program.program_hash() for program in baseline],
        )
