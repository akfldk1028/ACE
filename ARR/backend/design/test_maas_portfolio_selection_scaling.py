from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.book_language.portfolio_constraint_solver import (
    ConstraintCandidateFacts,
)
from design.maas.book_language.portfolio_selection import (
    _solve_cardinality_fallback,
)


class PortfolioSelectionScalingTests(SimpleTestCase):
    def test_large_fallback_pool_uses_bounded_solver(self):
        facts = [
            ConstraintCandidateFacts(score=float(index), cap_keys=())
            for index in range(25)
        ]
        compatibility = [[True] * len(facts) for _ in facts]

        with (
            patch(
                "design.maas.book_language.portfolio_selection."
                "solve_maximum_compatible_subset",
                side_effect=AssertionError("large pool entered exact search"),
            ),
            patch(
                "design.maas.book_language.portfolio_selection."
                "solve_bounded_compatible_subset",
                return_value=tuple(range(20)),
            ) as bounded,
        ):
            selected = _solve_cardinality_fallback(
                facts,
                compatibility,
                target_count=20,
                maximum_key_counts={},
                required_coverage_tags=(),
            )

        self.assertEqual(selected, tuple(range(20)))
        bounded.assert_called_once()

    def test_small_fallback_pool_keeps_exact_solver(self):
        facts = [
            ConstraintCandidateFacts(score=float(index), cap_keys=())
            for index in range(24)
        ]
        compatibility = [[True] * len(facts) for _ in facts]

        with (
            patch(
                "design.maas.book_language.portfolio_selection."
                "solve_maximum_compatible_subset",
                return_value=tuple(range(20)),
            ) as exact,
            patch(
                "design.maas.book_language.portfolio_selection."
                "solve_bounded_compatible_subset",
                side_effect=AssertionError("small pool skipped exact search"),
            ),
        ):
            selected = _solve_cardinality_fallback(
                facts,
                compatibility,
                target_count=20,
                maximum_key_counts={},
                required_coverage_tags=(),
            )

        self.assertEqual(selected, tuple(range(20)))
        exact.assert_called_once()
