"""Offer breadth without changing historical frozen author contracts."""

from dataclasses import replace
import hashlib
import json
from unittest import TestCase
from unittest.mock import patch

from design.maas.book_language.composition_lattice import iter_book_composition_paths
from design.maas.geometry_language.llm_adapter import _book_composition_path_slice


class BookPathSamplingTests(TestCase):
    def context(self, **overrides):
        return {
            "book_graph_vocabulary": {},
            "creative_portfolio_run_id": "book-reference39",
            **overrides,
        }

    def test_legacy_frozen_offer_retains_exact_24_path_six_principle_baseline(self):
        offer = _book_composition_path_slice(self.context(), 6)
        self.assertEqual(len(offer), 24)
        self.assertEqual(len({row["principle_id"] for row in offer}), 6)
        identity = json.dumps([row["path_id"] for row in offer], separators=(",", ":"))
        self.assertEqual(hashlib.sha256(identity.encode()).hexdigest(),
                         "c242da27eafd7dabc7de0bc997cae8feb5aa7cb948858aafdca1818dd8ba737d")
        self.assertEqual(offer, _book_composition_path_slice(
            self.context(book_path_sampling_version=1), 6))
        self.assertEqual(offer, _book_composition_path_slice(
            self.context(creative_portfolio_run_id="book-language41"), 6))

    def test_v2_covers_every_executable_principle_with_valid_unique_paths(self):
        executable = {path.path_id: path for path in iter_book_composition_paths()
                      if path.executable}
        offer = _book_composition_path_slice(self.context(book_path_sampling_version=2), 6)
        self.assertEqual({row["principle_id"] for row in offer},
                         {path.principle_id for path in executable.values()})
        self.assertLessEqual(len(offer), 96)
        self.assertEqual(len(offer), len({row["path_id"] for row in offer}))
        self.assertTrue(all(row["path_id"] in executable for row in offer))
        for row in offer:
            original = executable[row["path_id"]].to_dict()
            self.assertEqual(row, {key: original[key] for key in row})

    def test_v2_is_deterministic_and_round_identity_changes_variants(self):
        context = self.context(book_path_sampling_version=2)
        first = _book_composition_path_slice(context, 6)
        self.assertEqual(first, _book_composition_path_slice(dict(context), 6))
        second = _book_composition_path_slice(
            {**context, "creative_portfolio_run_id": "book-language41"}, 6)
        self.assertNotEqual({row["path_id"] for row in first},
                            {row["path_id"] for row in second})
        self.assertEqual({row["principle_id"] for row in first},
                         {row["principle_id"] for row in second})

    def test_v2_fills_larger_budget_with_distinct_variants_up_to_cap(self):
        offer = _book_composition_path_slice(self.context(book_path_sampling_version=2), 100)
        self.assertEqual(len(offer), 96)
        self.assertEqual(len({row["path_id"] for row in offer}), 96)
        self.assertGreater(len(offer), len({row["principle_id"] for row in offer}))

    def test_v2_rotates_principle_groups_when_vocabulary_exceeds_cap(self):
        base = next(path for path in iter_book_composition_paths() if path.executable)
        paths = tuple(replace(base, principle_id=f"test:principle:{index}")
                      for index in range(120))
        with patch("design.maas.book_language.composition_lattice.iter_book_composition_paths",
                   return_value=iter(paths)):
            first = _book_composition_path_slice(self.context(book_path_sampling_version=2), 6)
        with patch("design.maas.book_language.composition_lattice.iter_book_composition_paths",
                   return_value=iter(paths)):
            second = _book_composition_path_slice(self.context(
                book_path_sampling_version=2, creative_portfolio_run_id="book-language41"), 6)
        self.assertEqual(len(first), 96)
        self.assertEqual(len({row["principle_id"] for row in first}), 96)
        self.assertNotEqual({row["principle_id"] for row in first},
                            {row["principle_id"] for row in second})

    def test_no_vocabulary_still_means_no_offer(self):
        for context in ({}, {"book_path_sampling_version": 2}):
            self.assertEqual(_book_composition_path_slice(context, 6), [])
