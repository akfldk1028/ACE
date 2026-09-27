"""BOOK sentences: the grammar builds what the author chose."""
from __future__ import annotations

import unittest

import jsonschema

from design.maas.book_language.composition_lattice import iter_book_composition_paths
from design.maas.book_language.sentence_author import (
    SIDES,
    offered_paths,
    realize_book_sentence,
    realize_sentence_payload,
    sentence_payload_schema,
)
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.llm_adapter import GeometryAuthorError

INTENT = {
    "schema_version": "arr.maas.dimensional_intent.v1",
    "storey_count": 5,
    "storey_height_m": 3.8,
    "target_gfa_m2": 4800.0,
    "delivery_policy": "preserve_physical_dimensions",
    "programme_status": "unknown",
}
FACING = {"access_side": "east", "north_side": "north"}


def _sentence(path_id: str, index: int = 0) -> dict:
    return {
        "name": f"sentence_{index:03d}",
        "book_composition_path_id": path_id,
        "dimensional_intent": dict(INTENT),
        "facing": dict(FACING),
        "site_fit": "impose" if index % 2 else "inherit",
        "rationale": "a test sentence chosen from the lattice for the grammar to build",
    }


class BookSentenceAuthorTests(unittest.TestCase):
    def test_every_label_orientation_and_kind_realizes_one_connected_solid(self):
        # The offer is what the author chooses from, and every offered path
        # has already been built and found to stand; one per bucket.
        picked = {}
        for item in offered_paths(120):
            key = (item["base_volume"], item["orientation"], item["kind"])
            picked.setdefault(key, item["path_id"])
        self.assertEqual(len(picked), 6 * 3 * 4)
        payload = {"sentences": [_sentence(path_id, i) for i, path_id in enumerate(picked.values())]}
        programs = realize_sentence_payload(payload, expected_count=len(picked))
        self.assertEqual(len(programs), len(picked))
        labels = {program.metadata["base_seed"] for program in programs}
        self.assertEqual(labels, {"1/1", "3/8", "1/2", "1/4", "1/8", "1/16"})
        for program in programs[:12]:
            compilation = compile_geometry_program(program)
            self.assertEqual(compilation.status, "compiled")
            self.assertEqual(int(compilation.metrics.get("component_count", 0)), 1)
            operators = [node.operator for node in program.topological_nodes()]
            self.assertIn("book_base_volume", operators)
            self.assertEqual(program.metadata["author_representation"], "book_sentence")
            self.assertEqual(program.metadata["facing"], FACING)
        # The base volume is the object: a 1/16 sentence is a small body,
        # not the whole block with a sixteenth of it operated on.
        small = next(p for p in programs if p.metadata["base_seed"] == "1/16")
        self.assertLess(float(compile_geometry_program(small).metrics["volume"]), 0.25)

    def test_a_refused_sentence_is_named_by_index_and_path(self):
        good = next(p for p in iter_book_composition_paths() if p.executable)
        payload = {"sentences": [_sentence(good.path_id, 0), _sentence("book:path:nope", 1)]}
        with self.assertRaises(GeometryAuthorError) as caught:
            realize_sentence_payload(payload, expected_count=2)
        self.assertIn("2:book:path:nope:", str(caught.exception))
        # one valid of two asked is still a batch when one is enough
        self.assertEqual(len(realize_sentence_payload(payload, expected_count=1)), 1)

    def test_the_same_path_twice_is_a_duplicate(self):
        good = next(p for p in iter_book_composition_paths() if p.executable)
        payload = {"sentences": [_sentence(good.path_id, 0), _sentence(good.path_id, 1)]}
        with self.assertRaises(GeometryAuthorError) as caught:
            realize_sentence_payload(payload, expected_count=2)
        self.assertIn("duplicate_path", str(caught.exception))

    def test_facing_must_name_a_side(self):
        good = next(p for p in iter_book_composition_paths() if p.executable)
        sentence = _sentence(good.path_id)
        sentence["facing"] = {"access_side": "road", "north_side": "north"}
        with self.assertRaises(ValueError):
            realize_book_sentence(sentence)

    def test_offer_and_schema_cover_the_lattice_evenly(self):
        offer = offered_paths(120)
        self.assertGreaterEqual(len(offer), 240)
        self.assertEqual({item["base_volume"] for item in offer}, {"1/1", "3/8", "1/2", "1/4", "1/8", "1/16"})
        self.assertEqual({item["orientation"] for item in offer}, {"long_axis", "short_axis", "vertical"})
        self.assertEqual({item["kind"] for item in offer}, {"base_operative", "combination", "aggregation", "case_study"})
        schema = sentence_payload_schema([item["path_id"] for item in offer], count=2)
        payload = {"sentences": [_sentence(offer[0]["path_id"], 0), _sentence(offer[1]["path_id"], 1)]}
        jsonschema.validate(payload, schema)
        payload["sentences"][0]["facing"]["access_side"] = "up"
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(payload, schema)
        self.assertEqual(set(SIDES), {"east", "west", "north", "south"})


if __name__ == "__main__":
    unittest.main()
