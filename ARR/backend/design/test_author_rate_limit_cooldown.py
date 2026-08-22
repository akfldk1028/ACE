import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from design.maas.book_language import candidate_generation
from design.maas.book_language import portfolio_benchmark
from design.maas.book_language import portfolio_replenishment
from design.maas.geometry_language import GeometryAuthorError, base_seed_programs
from design.maas.geometry_language import llm_adapter
from design.maas.paid_provider_budget import (
    configure_paid_provider_budget,
    reserve_paid_provider_request,
    reset_paid_provider_budget_for_tests,
)


def _request(source_name):
    return {
        "source_seed": source_name,
        "live_llm_author": True,
        "llm_author_only": True,
        "live_vlm_revision": False,
        "llm_author_count": 1,
        "author_stage": "replenishment",
        "author_request_kind": "geometry_author_replenishment",
    }


def _rate_limited_outcome(*, retry_after_seconds=None):
    provider_error = {"category": "rate_limited", "http_status": 429}
    if retry_after_seconds is not None:
        provider_error["retry_after_seconds"] = retry_after_seconds
    return {
        "schema_version": "arr.maas.llm_author_request_outcome.v1",
        "provider_request_executed": True,
        "valid_authored_program_count": 0,
        "terminal_status": "failed",
        "failure_reason": "geometry_author_error",
        "failure_diagnostics": {
            "schema_version": (
                "arr.maas.geometry_author_failure_diagnostics.v1"
            ),
            "provider_error": provider_error,
        },
    }


class AuthorRateLimitCooldownTests(TestCase):
    def setUp(self):
        reset_paid_provider_budget_for_tests()
        configure_paid_provider_budget(16)
        self.source_name = candidate_generation.program_seed_sequences(
            "gymnasium"
        )[0].name

    def tearDown(self):
        reset_paid_provider_budget_for_tests()

    def test_no_retry_after_defers_remaining_cycles_with_one_transport_call(self):
        carried = SimpleNamespace(source=SimpleNamespace(metadata={
            "test_identity": "carried-1",
            "final_program_hash": "program-1",
            "final_geometry_hash": "geometry-1",
            "final_surface_payload_hash": "surface-1",
            "shared_floor_contract": {"hard_pass": True},
        }))
        unseen_carried = SimpleNamespace(source=SimpleNamespace(metadata={
            "test_identity": "carried-2",
            "final_program_hash": "program-2",
            "final_geometry_hash": "geometry-2",
            "final_surface_payload_hash": "surface-2",
            "shared_floor_contract": {"hard_pass": True},
        }))
        state = portfolio_benchmark._ReplenishmentLiveState(
            live_qd_reserve=(carried,),
            reviewed_final_vlm_fingerprints=frozenset(),
        )
        transport_calls = []
        cycle_outcomes = []
        downstream_cycles = []
        wall_clock = [100.0]

        def paid_rate_limited_author(*args, **kwargs):
            transport_calls.append((args, kwargs))
            reserve_paid_provider_request("geometry_author_replenishment")
            raise GeometryAuthorError(
                "redacted",
                diagnostics=_rate_limited_outcome()["failure_diagnostics"],
            )

        def program_pool(*args, **kwargs):
            outcomes = []
            candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=kwargs["synthesis_requests"],
                author_request_outcomes=outcomes,
            )
            serialized = [outcome.to_dict() for outcome in outcomes]
            cycle_outcomes.extend(serialized)
            return [], {
                "llm_author_request_outcomes": serialized,
                "llm_author_request_executed": any(
                    outcome.provider_request_executed for outcome in outcomes
                ),
            }

        def downstream(candidates, **kwargs):
            downstream_cycles.append(list(candidates))
            return {"rows": [{"combined_hard_pass": True} for _ in candidates]}

        cycle_kwargs = {
            "parent_variant_index": 0,
            "retained_selection_pool": [],
            "excluded_parent_keys": set(),
            "excluded_parent_fingerprints": set(),
            "excluded_program_hashes": set(),
            "generation_site": object(),
            "building_type": "gymnasium",
            "height": 14.0,
            "floors": 4,
            "generation_context": object(),
            "typed_graph_mutations": [],
            "geometry_program_mutations": [],
            "synthesis_requests": [_request(self.source_name)],
            "outcome_graph": None,
            "recursive_only": True,
            "target_count": 5,
            "exact_compile_limit": 12,
            "program_dimensional_context": {},
            "site_boundary_source": "test",
            "site_access_context": {},
            "site_access_geometry": {},
            "runtime_live_vlm": False,
            "live_vlm_selection_required": False,
            "base_capacity_contract": {},
            "trusted_legal_floor_field": {},
            "trusted_legal_floor_field_hash": "legal-field-hash",
            "trusted_clear_span_floor_plan": {},
            "capacity_site": object(),
            "output_dir": Path("test-output"),
            "program_slug": "gymnasium",
            "visual_directive": {},
            "downstream_context": {},
            "hard_gate_summary": lambda report, candidates: {
                "candidate_count": len(candidates),
            },
        }

        with patch.dict(
            "os.environ", {"OPENAI_API_KEY": "test-only"}, clear=False
        ), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            side_effect=paid_rate_limited_author,
        ), patch.object(
            portfolio_replenishment, "_program_pool", side_effect=program_pool
        ), patch.object(
            portfolio_replenishment,
            "_merge_live_qd_reserve",
            side_effect=lambda carried_pool, generated: list(carried_pool) + [
                candidate for candidate in generated if candidate not in carried_pool
            ],
        ), patch.object(
            portfolio_replenishment,
            "_exclude_duplicate_program_hashes",
            side_effect=lambda pool, excluded: (list(pool), 0),
        ), patch.object(
            portfolio_replenishment,
            "_live_qd_reserve_eligible",
            return_value=True,
        ), patch.object(
            portfolio_replenishment,
            "evaluate_accepted_sources_downstream",
            side_effect=downstream,
        ), patch.object(
            portfolio_replenishment,
            "_fingerprint",
            side_effect=lambda candidate: (
                candidate.source.metadata["test_identity"],
            ),
        ), patch.object(
            portfolio_replenishment,
            "_solid_morphology_metrics",
            return_value={"degenerate_sheet_like": False},
        ), patch.object(
            portfolio_replenishment,
            "_bounded_visual_selection_pool",
            side_effect=lambda pool: list(pool),
        ):
            _, _, invocation_cooldown = (
                portfolio_benchmark
                ._run_initial_generation_with_author_cooldown(
                    program_pool,
                    cooldown_state=state.author_rate_limit_cooldown,
                    clock=lambda: wall_clock[0],
                    synthesis_requests=[_request(self.source_name)],
                )
            )
            state = portfolio_benchmark._ReplenishmentLiveState(
                live_qd_reserve=state.live_qd_reserve,
                reviewed_final_vlm_fingerprints=(
                    state.reviewed_final_vlm_fingerprints
                ),
                author_rate_limit_cooldown=invocation_cooldown,
            )
            for cycle_index in range(1, 6):
                wall_clock[0] = 100.0 + (cycle_index * 300.0)
                _, state = (
                    portfolio_benchmark
                    ._run_replenishment_cycle_with_live_state(
                        lambda cycle_function, **kwargs: cycle_function(**kwargs),
                        portfolio_replenishment.run_replenishment_cycle,
                        state=state,
                        cycle_index=cycle_index,
                        clock=lambda: wall_clock[0],
                        **cycle_kwargs,
                    )
                )
                if cycle_index == 1:
                    state = portfolio_benchmark._ReplenishmentLiveState(
                        live_qd_reserve=(
                            *state.live_qd_reserve,
                            unseen_carried,
                        ),
                        reviewed_final_vlm_fingerprints=(
                            state.reviewed_final_vlm_fingerprints
                        ),
                        certified_reviewed_base_parents=(
                            state.certified_reviewed_base_parents
                        ),
                        replenishment_work_dispositions=(
                            state.replenishment_work_dispositions
                        ),
                        author_rate_limit_cooldown=(
                            state.author_rate_limit_cooldown
                        ),
                    )

            self.assertEqual(len(transport_calls), 1)
            wall_clock[0] += 300.0
            portfolio_benchmark._run_initial_generation_with_author_cooldown(
                program_pool,
                cooldown_state=(
                    portfolio_benchmark._AuthorRateLimitCooldownState()
                ),
                clock=lambda: wall_clock[0],
                synthesis_requests=[_request(self.source_name)],
            )

        self.assertEqual(len(transport_calls), 2)
        self.assertEqual(
            [outcome["terminal_status"] for outcome in cycle_outcomes[:6]],
            ["failed", "deferred", "deferred", "deferred", "deferred", "deferred"],
        )
        for outcome in cycle_outcomes[1:6]:
            self.assertFalse(outcome["provider_request_executed"])
            self.assertEqual(outcome["failure_reason"], "rate_limited_cooldown")
            self.assertEqual(
                outcome["failure_diagnostics"]["provider_error"],
                {"category": "rate_limited_cooldown", "http_status": 429},
            )
            self.assertEqual(
                outcome["failure_diagnostics"]["cooldown"]["scope"],
                "benchmark_run",
            )
        self.assertTrue(state.author_rate_limit_cooldown.circuit_open)
        self.assertIsNone(state.author_rate_limit_cooldown.deadline_epoch_seconds)
        self.assertEqual(downstream_cycles[0], [carried])
        self.assertIn(unseen_carried, downstream_cycles[1])

    def test_partial_success_with_nested_repair_429_activates_cooldown(self):
        sanitized_diagnostics = GeometryAuthorError(
            "redacted",
            diagnostics={
                "secondary_failures": [{
                    "category": "repair_author_failure",
                    "diagnostics": {
                        "provider_error": {
                            "category": "rate_limited",
                            "http_status": 429,
                            "retry_after_seconds": 9,
                        }
                    }
                }],
            },
        ).diagnostics
        partial = {
            "provider_request_executed": True,
            "valid_authored_program_count": 1,
            "terminal_status": "completed",
            "failure_reason": "",
            "failure_diagnostics": sanitized_diagnostics,
        }

        state = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            portfolio_benchmark._AuthorRateLimitCooldownState(),
            [partial],
            now=20.0,
        )

        self.assertEqual(state.attempt_count, 1)
        self.assertEqual(state.deadline_epoch_seconds, 29.0)

    def test_two_program_slugs_share_nested_429_run_circuit(self):
        nested = {
            "provider_request_executed": True,
            "valid_authored_program_count": 1,
            "terminal_status": "completed",
            "failure_reason": "",
            "failure_diagnostics": GeometryAuthorError(
                "redacted",
                diagnostics={
                    "secondary_failures": [{
                        "category": "repair_author_failure",
                        "diagnostics": _rate_limited_outcome()[
                            "failure_diagnostics"
                        ],
                    }],
                },
            ).diagnostics,
        }

        def first_program(**kwargs):
            self.assertNotIn(
                "author_rate_limit_cooldown",
                kwargs["synthesis_requests"][0],
            )
            return [], {"llm_author_request_outcomes": [nested]}

        state = portfolio_benchmark._AuthorRateLimitCooldownState()
        _, _, state = portfolio_benchmark._run_initial_generation_with_author_cooldown(
            first_program,
            cooldown_state=state,
            clock=lambda: 10.0,
            synthesis_requests=[_request(self.source_name)],
        )
        second_outcomes = []

        def second_program(**kwargs):
            candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=kwargs["synthesis_requests"],
                author_request_outcomes=second_outcomes,
            )
            return [], {
                "llm_author_request_outcomes": [
                    outcome.to_dict() for outcome in second_outcomes
                ]
            }

        with patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            side_effect=AssertionError("second slug called provider"),
        ):
            _, _, state = (
                portfolio_benchmark
                ._run_initial_generation_with_author_cooldown(
                    second_program,
                    cooldown_state=state,
                    clock=lambda: 10000.0,
                    synthesis_requests=[_request(self.source_name)],
                )
            )

        self.assertTrue(state.circuit_open)
        self.assertEqual(second_outcomes[0].terminal_status, "deferred")

    def test_valid_retry_after_expiry_allows_next_program_call(self):
        calls = []

        def first_program(**kwargs):
            calls.append("first")
            return [], {
                "llm_author_request_outcomes": [
                    _rate_limited_outcome(retry_after_seconds=1)
                ]
            }

        _, _, state = portfolio_benchmark._run_initial_generation_with_author_cooldown(
            first_program,
            cooldown_state=portfolio_benchmark._AuthorRateLimitCooldownState(),
            clock=lambda: 10.0,
            synthesis_requests=[_request(self.source_name)],
        )

        def second_program(**kwargs):
            calls.append("second")
            self.assertNotIn(
                "author_rate_limit_cooldown",
                kwargs["synthesis_requests"][0],
            )
            return [], {
                "llm_author_request_outcomes": [{
                    "provider_request_executed": True,
                    "valid_authored_program_count": 1,
                    "terminal_status": "completed",
                    "failure_reason": "",
                    "failure_diagnostics": {},
                }]
            }

        _, _, state = portfolio_benchmark._run_initial_generation_with_author_cooldown(
            second_program,
            cooldown_state=state,
            clock=lambda: 12.0,
            synthesis_requests=[_request(self.source_name)],
        )

        self.assertEqual(calls, ["first", "second"])
        self.assertEqual(state, portfolio_benchmark._AuthorRateLimitCooldownState())

    def test_only_clean_success_resets_existing_cooldown(self):
        limited = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            portfolio_benchmark._AuthorRateLimitCooldownState(),
            [_rate_limited_outcome()],
            now=10.0,
        )
        sanitized_diagnostics = GeometryAuthorError(
            "redacted",
            diagnostics={
                "secondary_failures": [{
                    "category": "repair_author_failure",
                    "diagnostics": {
                        "provider_error": {
                            "category": "rate_limited",
                            "http_status": 429,
                        }
                    }
                }]
            },
        ).diagnostics
        nested_429_success = {
            "provider_request_executed": True,
            "valid_authored_program_count": 1,
            "terminal_status": "completed",
            "failure_reason": "",
            "failure_diagnostics": sanitized_diagnostics,
        }

        retained = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            limited,
            [nested_429_success],
            now=20.0,
        )
        reset = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            retained,
            [{
                "provider_request_executed": True,
                "valid_authored_program_count": 1,
                "terminal_status": "completed",
                "failure_reason": "",
                "failure_diagnostics": {},
            }],
            now=21.0,
        )

        self.assertEqual(retained.attempt_count, 2)
        self.assertEqual(reset, portfolio_benchmark._AuthorRateLimitCooldownState())

    def test_http_date_retry_after_uses_injected_wall_clock(self):
        now = datetime(2026, 8, 5, 6, 21, 0, tzinfo=timezone.utc).timestamp()
        diagnostics = llm_adapter._provider_failure_diagnostics(
            category="rate_limited",
            http_status=429,
            retry_after="Wed, 05 Aug 2026 06:21:30 GMT",
        )
        outcome = {
            **_rate_limited_outcome(),
            "failure_diagnostics": diagnostics,
        }

        state = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            portfolio_benchmark._AuthorRateLimitCooldownState(),
            [outcome],
            now=now,
        )

        self.assertEqual(state.source, "retry_after_http_date")
        self.assertEqual(state.backoff_seconds, 30.0)
        self.assertEqual(state.deadline_epoch_seconds, now + 30.0)

    def test_malformed_retry_after_opens_benchmark_run_circuit(self):
        diagnostics = llm_adapter._provider_failure_diagnostics(
            category="rate_limited",
            http_status=429,
            retry_after="not-a-valid-http-date",
        )
        outcome = {
            **_rate_limited_outcome(),
            "failure_diagnostics": diagnostics,
        }

        state = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            portfolio_benchmark._AuthorRateLimitCooldownState(),
            [outcome],
            now=50.0,
        )

        self.assertEqual(state.source, "benchmark_run_circuit")
        self.assertEqual(state.scope, "benchmark_run")
        self.assertTrue(state.circuit_open)
        self.assertEqual(state.backoff_seconds, 0.0)

    def test_delta_seconds_expiry_allows_retry_and_retains_attempt_history(self):
        initial = portfolio_benchmark._AuthorRateLimitCooldownState()
        first = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            initial,
            [_rate_limited_outcome(retry_after_seconds=1)],
            now=10.0,
        )

        expired, defer = portfolio_benchmark._author_rate_limit_cooldown_before_cycle(
            first,
            now=11.0,
        )
        second = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            expired,
            [_rate_limited_outcome()],
            now=11.0,
        )

        self.assertIsNone(defer)
        self.assertIsNone(expired.deadline_epoch_seconds)
        self.assertEqual(expired.attempt_count, 1)
        self.assertEqual(expired.backoff_seconds, 1.0)
        self.assertEqual(expired.source, "retry_after")
        self.assertEqual(expired.http_status, 429)
        self.assertEqual(expired.retry_after_seconds, 1.0)
        self.assertFalse(expired.circuit_open)
        self.assertEqual(second.attempt_count, 2)
        self.assertTrue(second.circuit_open)
        self.assertEqual(second.scope, "benchmark_run")
        self.assertIsNone(second.deadline_epoch_seconds)

    def test_missing_retry_after_circuit_ignores_wall_clock_advance(self):
        state = portfolio_benchmark._AuthorRateLimitCooldownState()
        state = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            state,
            [_rate_limited_outcome()],
            now=100.0,
        )
        retained, defer = portfolio_benchmark._author_rate_limit_cooldown_before_cycle(
            state,
            now=100000.0,
        )

        self.assertTrue(retained.circuit_open)
        self.assertEqual(retained.scope, "benchmark_run")
        self.assertEqual(retained.attempt_count, 1)
        self.assertIsNone(retained.deadline_epoch_seconds)
        self.assertEqual(defer["scope"], "benchmark_run")

    def test_successful_paid_author_call_fully_resets_history(self):
        limited = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            portfolio_benchmark._AuthorRateLimitCooldownState(),
            [_rate_limited_outcome()],
            now=10.0,
        )
        success = {
            "provider_request_executed": True,
            "valid_authored_program_count": 1,
            "terminal_status": "completed",
            "failure_reason": "",
            "failure_diagnostics": {},
        }

        reset = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            limited,
            [success],
            now=20.0,
        )

        self.assertEqual(
            reset,
            portfolio_benchmark._AuthorRateLimitCooldownState(),
        )

    def test_non_429_failure_does_not_change_state_and_serialization_is_redacted(self):
        state = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            portfolio_benchmark._AuthorRateLimitCooldownState(),
            [_rate_limited_outcome(retry_after_seconds=5)],
            now=10.0,
        )
        non_429 = {
            **_rate_limited_outcome(),
            "failure_diagnostics": {
                "provider_error": {
                    "category": "http_error",
                    "http_status": 503,
                }
            },
        }

        unchanged = portfolio_benchmark._author_rate_limit_cooldown_after_cycle(
            state,
            [non_429],
            now=11.0,
        )
        payload = unchanged.to_dict()
        serialized = json.dumps(payload, sort_keys=True)

        self.assertEqual(unchanged, state)
        self.assertNotIn("body", serialized.lower())
        self.assertNotIn("url", serialized.lower())
        self.assertNotIn("secret", serialized.lower())
        self.assertEqual(payload["http_status"], 429)
