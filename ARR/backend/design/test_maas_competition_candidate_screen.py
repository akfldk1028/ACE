from __future__ import annotations

import importlib
import importlib.util
import json
import unittest

from design.maas.book_language import candidate_generation
from design.maas.book_language.competition_candidate_screen import (
    _competition_cheap_candidate_records,
)
from design.maas.book_language.composition_lattice import (
    iter_book_composition_paths,
)
from design.maas.book_language.registry import build_book_language_registry
from design.maas.geometry_language import GeometryNode, GeometryProgram
from design.maas.grammar.verb_sequence import VerbSequence, call


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

    def test_causal_oauth_path_is_the_exact_cheap_screen_descriptor(self):
        path = next(
            item for item in iter_book_composition_paths()
            if item.principle_id == "book:operative:notch"
            and item.base_volume_label == "1/8"
            and item.orientation == "short_axis"
            and item.variation_index == 7
        )
        program = GeometryProgram(
            nodes=(GeometryNode(
                id="base",
                kind="primitive",
                operator="box",
                parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                semantic_role="base_volume",
            ),),
            root_id="base",
            name="causal_screen_probe",
            execution_contract={
                "schema_version": (
                    "arr.maas.codex_book_path_execution_binding.v1"
                ),
                "book_composition_path_id": path.path_id,
                "author_response_sha256": "a" * 64,
            },
        )
        seed = VerbSequence(
            name="causal_seed",
            label="causal seed",
            calls=(call("base", width=1.0, depth=1.0, height=1.0),),
            notes=(
                "geometry_program_payload="
                + json.dumps(program.to_dict(), separators=(",", ":")),
            ),
        )
        principles = tuple(build_book_language_registry()["principles"])

        records = _competition_cheap_candidate_records(
            (seed,),
            principles,
            book_probe_count=3,
            evaluation_limit=192,
            scope_labels=("1/1", "1/2", "1/8"),
            page_index=0,
            legal_sections=(),
            capacity_contract=None,
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0].key,
            "0:book:operative:notch:7",
        )
        self.assertEqual(records[0].base_scope, "1/8")


if __name__ == "__main__":
    unittest.main()
