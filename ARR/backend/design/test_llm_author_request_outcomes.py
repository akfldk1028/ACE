from dataclasses import replace
import json
from tempfile import TemporaryDirectory
import urllib.error
from unittest import TestCase
from unittest.mock import patch

from design.maas.book_language import candidate_generation
from design.maas.geometry_language import GeometryAuthorError, base_seed_programs
from design.maas.geometry_language import llm_adapter
from design.maas.paid_provider_budget import (
    configure_paid_provider_budget,
    reserve_paid_provider_request,
    reset_paid_provider_budget_for_tests,
)


def _request(source_name: str) -> dict:
    return {
        "source_seed": source_name,
        "live_llm_author": True,
        "llm_author_only": True,
        "live_vlm_revision": False,
        "llm_author_count": 1,
        "author_stage": "replenishment",
        "author_request_kind": "geometry_author_replenishment",
        "base_book_vlm_replenishment_feedback": [{"reason": "base_rejected"}],
        "authored_visual_authority_replenishment_feedback": [
            {"reason": "silhouette_near_duplicate"},
            {"reason": "missing_descriptor_cells"},
        ],
    }


def _structured_author_item(program, *, name: str, base_seed: str) -> dict:
    def parameter(name, value):
        if isinstance(value, bool):
            return {"name": name, "value_type": "boolean", "boolean_value": value}
        if isinstance(value, (int, float)):
            return {"name": name, "value_type": "number", "numeric_value": value}
        if isinstance(value, str):
            return {"name": name, "value_type": "string", "string_value": value}
        if isinstance(value, (list, tuple)) and all(
            isinstance(component, (int, float)) for component in value
        ):
            return {"name": name, "value_type": "vector", "vector_value": list(value)}
        return {
            "name": name,
            "value_type": "structured_json",
            "structured_json": json.dumps(value, sort_keys=True),
        }
    return {
        "name": name,
        "base_seed": base_seed,
        "intent_tags": [],
        "nodes": [{
            "id": node.id,
            "kind": node.kind,
            "operator": node.operator,
            "inputs": list(node.inputs),
            "parameters": [
                parameter(key, value)
                for key, value in sorted(node.parameters.items())
            ],
            "semantic_role": node.semantic_role,
        } for node in program.nodes],
        "root_id": program.root_id,
        "rationale": "structural test fixture",
    }


class LlmAuthorRequestOutcomeTests(TestCase):
    def setUp(self):
        reset_paid_provider_budget_for_tests()
        configure_paid_provider_budget(8)
        self.source_name = candidate_generation.program_seed_sequences(
            "gymnasium"
        )[0].name

    def tearDown(self):
        reset_paid_provider_budget_for_tests()

    def test_pre_request_exception_is_failed_without_claiming_execution(self):
        outcomes = []
        request = _request(self.source_name)

        with patch.dict(
            "os.environ", {"OPENAI_API_KEY": "test-only"}, clear=False
        ), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            side_effect=GeometryAuthorError(
                "geometry author and compiler repair yielded no valid programs"
            ),
        ):
            seeds = candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[request],
                author_request_outcomes=outcomes,
            )

        self.assertFalse(any(
            "geometry_program_synthesis_request_source=vlm_or_session_directive"
            in seed.notes
            for seed in seeds
        ))
        self.assertEqual(len(outcomes), 1)
        outcome = outcomes[0]
        self.assertIsInstance(
            outcome, candidate_generation.LlmAuthorRequestOutcome
        )
        self.assertFalse(outcome.provider_request_executed)
        self.assertEqual(outcome.author_stage, "replenishment")
        self.assertEqual(
            outcome.request_kind, "geometry_author_replenishment"
        )
        self.assertEqual(outcome.requested_count, 1)
        self.assertEqual(outcome.feedback_count, 2)
        self.assertEqual(outcome.base_feedback_count, 1)
        self.assertEqual(outcome.cache_hit_count, 0)
        self.assertEqual(outcome.valid_authored_program_count, 0)
        self.assertEqual(outcome.terminal_status, "failed")
        self.assertEqual(outcome.failure_reason, "geometry_author_error")

    def test_provider_exception_after_ledger_delta_records_execution(self):
        outcomes = []
        provider_error = urllib.error.HTTPError(
            "https://api.openai.com/v1/responses?secret=query",
            429,
            "secret-error-body",
            {"Retry-After": "12", "X-Request-Id": "secret-id"},
            None,
        )

        def real_adapter(context, **kwargs):
            context = dict(context)
            context.pop("book_graph_vocabulary", None)
            context.pop("program_context", None)
            return llm_adapter.author_geometry_programs_with_openai(
                context, **kwargs
            )

        with TemporaryDirectory() as cache_directory, patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "secret-api-key",
                "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
            },
            clear=False,
        ), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            side_effect=real_adapter,
        ), patch.object(
            llm_adapter.urllib.request,
            "urlopen",
            side_effect=provider_error,
        ):
            candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[_request(self.source_name)],
                author_request_outcomes=outcomes,
            )

        diagnostics = {
            "schema_version": "arr.maas.geometry_author_failure_diagnostics.v1",
            "provider_error": {
                "category": "rate_limited",
                "http_status": 429,
                "retry_after_seconds": 12,
            },
        }

        self.assertTrue(outcomes[0].provider_request_executed)
        self.assertEqual(outcomes[0].valid_authored_program_count, 0)
        self.assertEqual(outcomes[0].terminal_status, "failed")
        self.assertEqual(outcomes[0].failure_reason, "geometry_author_error")
        self.assertEqual(outcomes[0].failure_diagnostics, diagnostics)
        self.assertEqual(outcomes[0].to_dict()["failure_diagnostics"], diagnostics)
        rendered = json.dumps(outcomes[0].to_dict(), sort_keys=True)
        for secret in ("secret-error-body", "secret-api-key", "secret-id", "query"):
            self.assertNotIn(secret, rendered)

    def test_provider_zero_valid_programs_after_ledger_delta_is_executed_failure(self):
        outcomes = []
        payload = {"programs": [
            "not-an-object",
            {"name": "broken", "dsl": "not executable AST"},
        ]}

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "id": "response",
                    "output_text": json.dumps(payload),
                }).encode("utf-8")

        def real_adapter(context, **kwargs):
            context = dict(context)
            context.pop("book_graph_vocabulary", None)
            context.pop("program_context", None)
            return llm_adapter.author_geometry_programs_with_openai(
                context, **kwargs
            )

        request = _request(self.source_name)
        request["llm_author_count"] = 2
        configure_paid_provider_budget(1)
        with TemporaryDirectory() as cache_directory, patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-only",
                "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
            },
            clear=False,
        ), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            side_effect=real_adapter,
        ), patch.object(
            llm_adapter.urllib.request,
            "urlopen",
            return_value=_Response(),
        ):
            candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[request],
                author_request_outcomes=outcomes,
            )

        self.assertTrue(outcomes[0].provider_request_executed)
        self.assertEqual(outcomes[0].valid_authored_program_count, 0)
        self.assertEqual(outcomes[0].terminal_status, "failed")
        self.assertEqual(
            outcomes[0].failure_reason, "geometry_author_error"
        )
        batch = outcomes[0].failure_diagnostics["batches"][0]
        self.assertEqual(
            batch["rejection_category_counts"],
            {"ast_decode": 1, "schema": 1},
        )
        self.assertEqual(
            sum(batch["rejection_category_counts"].values()),
            batch["rejected_program_count"],
        )
        self.assertEqual(
            outcomes[0].failure_diagnostics["secondary_failures"][0]["category"],
            "retry_budget",
        )

    def test_valid_non_cache_program_records_one_valid_authored_program(self):
        outcomes = []
        authored = base_seed_programs()[0]
        inferred_seed = llm_adapter._infer_base_seed(authored)
        wrong_seed = next(
            spec.seed_id for spec in llm_adapter.BASE_SEED_SPECS
            if spec.seed_id != inferred_seed
        )
        payload = {"programs": [
            "not-an-object",
            _structured_author_item(
                authored, name="wrong-seed", base_seed=wrong_seed
            ),
            _structured_author_item(
                authored, name="accepted", base_seed=inferred_seed
            ),
            _structured_author_item(
                authored, name="accepted", base_seed=inferred_seed
            ),
        ]}

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "id": "response",
                    "output_text": json.dumps(payload),
                }).encode("utf-8")

        def real_adapter(context, **kwargs):
            context = dict(context)
            context.pop("book_graph_vocabulary", None)
            context.pop("program_context", None)
            return llm_adapter.author_geometry_programs_with_openai(
                context, **kwargs
            )

        request = _request(self.source_name)
        request["llm_author_count"] = 4
        configure_paid_provider_budget(1)
        with TemporaryDirectory() as cache_directory, patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-only",
                "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
            },
            clear=False,
        ), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            side_effect=real_adapter,
        ), patch.object(
            llm_adapter.urllib.request,
            "urlopen",
            return_value=_Response(),
        ):
            candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[request],
                author_request_outcomes=outcomes,
            )

        self.assertEqual(len(outcomes), 1)
        outcome = outcomes[0]
        self.assertTrue(outcome.provider_request_executed)
        self.assertEqual(outcome.valid_authored_program_count, 1)
        self.assertEqual(outcome.cache_hit_count, 0)
        self.assertEqual(outcome.terminal_status, "completed")
        self.assertEqual(outcome.failure_reason, "")
        self.assertEqual(
            outcome.failure_diagnostics["batches"][0]["valid_program_count"],
            1,
        )
        self.assertEqual(
            outcome.failure_diagnostics["batches"][0]["rejected_program_count"],
            3,
        )
        batch = outcome.failure_diagnostics["batches"][0]
        self.assertEqual(
            batch["rejection_category_counts"],
            {"compiler_or_gate": 1, "duplicate": 1, "schema": 1},
        )
        self.assertEqual(
            sum(batch["rejection_category_counts"].values()),
            batch["rejected_program_count"],
        )
        self.assertEqual(
            batch["rejection_code_counts"],
            {
                "declared_base_seed_mismatch": 1,
                "duplicate_program": 1,
                "non_object_program": 1,
            },
        )
        self.assertEqual(
            outcome.failure_diagnostics["secondary_failures"][0]["category"],
            "retry_budget",
        )

    def test_cache_hit_is_valid_without_claiming_provider_execution(self):
        outcomes = []
        cached = replace(base_seed_programs()[0], metadata={
            **base_seed_programs()[0].metadata,
            "author_provider": "openai_llm_geometry_author",
            "author_cache_hit": True,
        })

        with patch.dict(
            "os.environ", {"OPENAI_API_KEY": "test-only"}, clear=False
        ), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            return_value=(cached,),
        ):
            candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[_request(self.source_name)],
                author_request_outcomes=outcomes,
            )

        outcome = outcomes[0]
        self.assertFalse(outcome.provider_request_executed)
        self.assertEqual(outcome.cache_hit_count, 1)
        self.assertEqual(outcome.valid_authored_program_count, 1)
        self.assertEqual(outcome.terminal_status, "completed")

    def test_generation_evidence_and_two_phase_merge_use_typed_outcomes(self):
        first = candidate_generation.LlmAuthorRequestOutcome(
            provider_request_executed=True,
            author_stage="replenishment",
            request_kind="geometry_author_replenishment",
            requested_count=1,
            feedback_count=2,
            base_feedback_count=1,
            cache_hit_count=0,
            valid_authored_program_count=0,
            terminal_status="failed",
            failure_reason="geometry_author_error",
        )
        second = candidate_generation.LlmAuthorRequestOutcome(
            provider_request_executed=False,
            author_stage="replenishment",
            request_kind="geometry_author_replenishment",
            requested_count=1,
            feedback_count=2,
            base_feedback_count=1,
            cache_hit_count=1,
            valid_authored_program_count=1,
            terminal_status="completed",
            failure_reason="",
        )
        base_counts = {
            "llm_author_request_outcomes": [first.to_dict()],
            "llm_author_request_executed": True,
            "legal_mass_archive": {"records": []},
            "phase_durations_seconds": {},
        }
        descendant_counts = {
            "llm_author_request_outcomes": [second.to_dict()],
            "llm_author_request_executed": False,
            "legal_mass_archive": {"records": []},
            "phase_durations_seconds": {},
        }

        merged = candidate_generation._merge_two_phase_generation_counts(
            base_counts,
            descendant_counts,
            base_vlm_evidence={},
            registry={},
        )

        self.assertEqual(
            merged["llm_author_request_outcomes"],
            [first.to_dict(), second.to_dict()],
        )
        self.assertTrue(merged["llm_author_request_executed"])
        self.assertEqual(merged["llm_author_valid_program_count"], 1)
        self.assertEqual(merged["llm_author_cache_hit_count"], 1)
