from __future__ import annotations

import json

from django.test import SimpleTestCase

from design.maas.creative_author_supply import (
    collect_creative_author_supply,
)
from design.maas.creative_program_author import CreativeAuthoredProgram
from design.maas.geometry_language.ast import GeometryProgram
from design.maas.geometry_language.llm_adapter import GeometryAuthorError
from design.maas.geometry_language.programs import GeometryProgramBuilder


class CreativeAuthorSupplyTests(SimpleTestCase):
    @staticmethod
    def program(index: int) -> GeometryProgram:
        builder = GeometryProgramBuilder(f"authored_supply_{index}")
        body = builder.add(
            "primitive",
            "box",
            parameters={
                "width": 1.0 + index * 0.03,
                "depth": 0.72,
                "height": 1.35,
            },
            semantic_role="llm_authored_body",
        )
        return builder.build(
            body,
            author_provider="test_structured_llm",
            author_model="test-model",
            author_response_id=f"response-{index:03d}",
            author_prompt_contract="typed_ast_test",
        )

    def authored_programs(
        self,
        count: int,
        *,
        cache_hit: bool,
    ) -> tuple[CreativeAuthoredProgram, ...]:
        return tuple(
            CreativeAuthoredProgram(
                program=self.program(index),
                author_evidence={
                    "schema_version": "arr.maas.creative_author_evidence.v1",
                    "source_kind": "llm_authored_geometry_program",
                    "provider": "test_structured_llm",
                    "model": "test-model",
                    "response_id": f"response-{index:03d}",
                    "cache_hit": cache_hit,
                    "prompt_contract": "typed_ast_test",
                },
            )
            for index in range(count)
        )

    @staticmethod
    def fail_if_called(
        requested_count: int,
        attempt_index: int,
    ) -> tuple[GeometryProgram, ...]:
        raise AssertionError(
            f"fresh author called: {requested_count=}, {attempt_index=}"
        )

    @staticmethod
    def raise_geometry_author_429(
        requested_count: int,
        attempt_index: int,
    ) -> tuple[GeometryProgram, ...]:
        raise GeometryAuthorError(
            "provider rate limit",
            diagnostics={
                "provider_error": {
                    "category": "rate_limited",
                    "http_status": 429,
                },
            },
        )

    def fresh_batches_with_one_duplicate(
        self,
        requested_count: int,
        attempt_index: int,
    ) -> tuple[GeometryProgram, ...]:
        if attempt_index == 1:
            return self.program(0), self.program(1)
        return (self.program(2),)

    def test_cache_is_consumed_before_any_fresh_request(self):
        result = collect_creative_author_supply(
            target_count=20,
            cached_programs=self.authored_programs(20, cache_hit=True),
            fresh_author=self.fail_if_called,
            retained_count=lambda programs: len(programs),
            max_fresh_requests=3,
        )

        self.assertEqual(len(result.programs), 20)
        self.assertEqual(result.counts["fresh_transport_attempted"], 0)
        self.assertEqual(result.counts["cache_programs_accepted"], 20)

    def test_first_429_opens_circuit_and_preserves_cached_supply(self):
        result = collect_creative_author_supply(
            target_count=20,
            cached_programs=self.authored_programs(7, cache_hit=True),
            fresh_author=self.raise_geometry_author_429,
            retained_count=lambda programs: len(programs),
            max_fresh_requests=3,
        )

        self.assertEqual(len(result.programs), 7)
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.counts["fresh_transport_attempted"], 1)
        self.assertEqual(result.counts["fresh_transport_deferred"], 2)
        self.assertEqual(result.counts["http_429"], 1)

    def test_fresh_batches_deduplicate_program_hashes_without_fixture_fallback(
        self,
    ):
        result = collect_creative_author_supply(
            target_count=3,
            cached_programs=self.authored_programs(1, cache_hit=True),
            fresh_author=self.fresh_batches_with_one_duplicate,
            retained_count=lambda programs: len(programs),
            max_fresh_requests=3,
        )

        self.assertEqual(len(result.programs), 3)
        self.assertEqual(result.status, "complete")
        self.assertEqual(result.counts["duplicate_program_hash"], 1)
        self.assertNotIn("recipe_fixture", json.dumps(result.evidence()))
