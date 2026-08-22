"""r339 regressions for proven LLM pre-BOOK lineage release."""

from types import SimpleNamespace
from unittest import TestCase

from design.maas.book_language.candidate_generation import (
    _proven_llm_pre_book_parent_key,
)
from design.maas.book_language.lineage import (
    gate_descendants_by_base,
    lineage_record,
)


class R339LlmBookLineageReleaseTests(TestCase):
    @staticmethod
    def _lineage():
        return lineage_record(
            {
                "principle_id": "book:combination:setback_notch",
                "lineage_base_operative_id": "book:operative:subtract",
                "generation_stage": "combination",
            },
            source_seed="llm-r339",
            scope_label="1/2",
            orientation="long_axis",
            variant_index=1,
        )

    @staticmethod
    def _candidate(lineage, proof):
        return SimpleNamespace(source=SimpleNamespace(metadata={
            "book_generation_lineage": lineage,
            "geometry_program": {"metadata": {"family": "setback_notch"}},
            "capacity_alternative_projection": {"target_hard_pass": True},
            "geometry_program_bridge_evidence": {
                "llm_geometry_author_active": True,
                "initial_llm_authored_pre_book_program_hash": "pre-program",
                "initial_llm_authored_pre_book_geometry_hash": "pre-geometry",
                "pre_book_lineage_parent_proof": proof,
            },
        }))

    def test_matching_proven_pre_book_parent_releases_llm_descendant(self):
        lineage = self._lineage()
        proof = {
            "parent_key": lineage["parent_key"],
            "program_hash": "pre-program",
            "geometry_hash": "pre-geometry",
            "compiler_clean": True,
            "contained": True,
        }
        candidate = self._candidate(lineage, proof)

        proven_key = _proven_llm_pre_book_parent_key(candidate.source, lineage)
        retained, evidence = gate_descendants_by_base(
            [candidate],
            known_viable_base_keys={proven_key} if proven_key else set(),
        )

        self.assertEqual(retained, [candidate])
        self.assertEqual(evidence["retained_via_known_base_count"], 1)

    def test_mismatched_or_unproven_parent_still_rejects(self):
        lineage = self._lineage()
        cases = (
            {
                "parent_key": lineage["parent_key"] + "-other",
                "program_hash": "pre-program",
                "geometry_hash": "pre-geometry",
                "compiler_clean": True,
                "contained": True,
            },
            {
                "parent_key": lineage["parent_key"],
                "program_hash": "pre-program",
                "geometry_hash": "pre-geometry",
                "compiler_clean": False,
                "contained": True,
            },
            {},
        )
        for proof in cases:
            with self.subTest(proof=proof):
                candidate = self._candidate(lineage, proof)
                proven_key = _proven_llm_pre_book_parent_key(
                    candidate.source,
                    lineage,
                )
                retained, evidence = gate_descendants_by_base(
                    [candidate],
                    known_viable_base_keys=(
                        {proven_key} if proven_key else set()
                    ),
                )
                self.assertEqual(proven_key, "")
                self.assertEqual(retained, [])
                self.assertEqual(
                    evidence["descendant_without_viable_base_count"],
                    1,
                )
