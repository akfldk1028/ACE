from __future__ import annotations

import importlib
import importlib.util
import unittest

from design.maas.book_language import candidate_generation


SCREEN_SYMBOLS = (
    "competition_breadth_generation_budget",
    "resolve_competition_breadth_generation_budget",
    "_competition_pre_exact_shortlist",
    "_cheap_morphology_preclassification",
    "_cheap_ast_bounds",
    "_legal_section_dimensions",
    "_cheap_typed_ast_candidate_evidence",
    "_competition_cheap_candidate_records",
    "_recursive_principle_schedule_limit",
    "_diagnostic_generation_cap_reached",
    "_capacity_alternative_schedule_index",
)


class CompetitionCandidateScreenExtractionTests(unittest.TestCase):
    def test_candidate_generation_reexports_owner_symbols_without_wrappers(self):
        module_name = (
            "design.maas.book_language.competition_candidate_screen"
        )
        self.assertIsNotNone(
            importlib.util.find_spec(module_name),
            "competition breadth helpers need a focused owner module",
        )
        owner = importlib.import_module(module_name)

        for symbol in SCREEN_SYMBOLS:
            with self.subTest(symbol=symbol):
                self.assertIs(
                    getattr(candidate_generation, symbol),
                    getattr(owner, symbol),
                )


if __name__ == "__main__":
    unittest.main()
