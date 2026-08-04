import json
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.book_language import candidate_generation
from design.maas.book_language.candidate_analysis import _Candidate
from design.maas.book_language.portfolio_benchmark import (
    _bounded_replenishment_causal_feedback,
    _deficit_directed_replenishment_inputs,
)
from design.maas.book_language import portfolio_replenishment
from design.maas.book_language.run_budget import progressive_mass_run_budget
from design.maas.geometry_language import base_seed_programs
from design.maas.geometry_language.llm_adapter import (
    author_geometry_programs_with_openai,
)
from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph
from design.maas.paid_provider_budget import (
    PaidProviderBudgetError,
    configure_paid_provider_budget,
    paid_provider_budget_snapshot,
    reserve_paid_provider_request,
    reset_paid_provider_budget_for_tests,
)


class Task6CAuthorPartitionTest(SimpleTestCase):
    def tearDown(self):
        reset_paid_provider_budget_for_tests()
        super().tearDown()

    def test_target_contracts_partition_initial_and_replenishment_author(self):
        expected = {
            3: (2, 1, 3, 9, 1, 16, 13),
            10: (4, 1, 8, 30, 1, 44, 39),
            20: (7, 1, 8, 60, 1, 77, 69),
        }
        for target, contract in expected.items():
            budget = progressive_mass_run_budget(target)
            self.assertEqual(
                (
                    budget.initial_author_request_limit,
                    budget.replenishment_author_request_limit,
                    budget.base_parent_review_budget,
                    budget.exact_acceptance_opportunities,
                    budget.portfolio_board_reserve,
                    budget.total_provider_request_limit,
                    budget.live_vlm_request_limit,
                ),
                contract,
            )

    def test_author_partitions_do_not_cross_borrow(self):
        configure_paid_provider_budget(3, quotas={
            "author_initial": 2,
            "author_replenishment": 1,
            "base_candidate": 0,
            "exact_candidate": 0,
            "portfolio_board": 0,
            "reference_audit": 0,
            "retry": 0,
        })
        reserve_paid_provider_request("geometry_author_initial")
        reserve_paid_provider_request("geometry_author_initial")
        reserve_paid_provider_request("geometry_author_replenishment")
        with self.assertRaises(PaidProviderBudgetError) as initial:
            reserve_paid_provider_request("geometry_author_initial")
        with self.assertRaises(PaidProviderBudgetError) as replenishment:
            reserve_paid_provider_request("geometry_author_replenishment")
        self.assertEqual(initial.exception.quota, "author_initial")
        self.assertEqual(replenishment.exception.quota, "author_replenishment")

    def test_candidate_context_passes_explicit_replenishment_author_stage(self):
        source_name = candidate_generation.program_seed_sequences("gymnasium")[0].name
        authored = base_seed_programs()[0]
        request = {
            "source_seed": source_name,
            "live_llm_author": True,
            "live_vlm_revision": False,
            "llm_author_count": 1,
            "author_stage": "replenishment",
            "author_request_kind": "geometry_author_replenishment",
            "base_book_vlm_replenishment_feedback": [{
                "parent_fingerprint": "fp-exact",
                "program_hash": "program-exact",
                "critic_actions": [{"operation": "add_void", "semantic_role": "courtyard"}],
            }],
        }
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-only"}, clear=False), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            return_value=(authored,),
        ) as author:
            candidate_generation._agent_mutated_seeds(
                "gymnasium", mutations=None, synthesis_requests=[request]
            )
        context = author.call_args.args[0]
        self.assertEqual(context["author_stage"], "replenishment")
        self.assertEqual(context["author_request_kind"], "geometry_author_replenishment")
        self.assertEqual(
            context["base_book_vlm_replenishment_feedback"],
            request["base_book_vlm_replenishment_feedback"],
        )

    def test_recursive_compiler_repair_inherits_replenishment_partition(self):
        configure_paid_provider_budget(1, quotas={
            "author_initial": 0,
            "author_replenishment": 1,
            "base_candidate": 0,
            "exact_candidate": 0,
            "portfolio_board": 0,
            "reference_audit": 0,
            "retry": 0,
        })
        partial = base_seed_programs()[0]

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "id": "task6c-partial",
                    "output_text": json.dumps({"programs": []}),
                }).encode("utf-8")

        with TemporaryDirectory() as cache_directory, patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-key",
                "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
            },
            clear=False,
        ), patch(
            "design.maas.geometry_language.llm_adapter.urllib.request.urlopen",
            return_value=Response(),
        ), patch(
            "design.maas.geometry_language.llm_adapter.geometry_programs_from_author_payload",
            return_value=(partial,),
        ), patch(
            "design.maas.geometry_language.llm_adapter._author_payload_compiler_diagnostics",
            return_value=[],
        ):
            programs = author_geometry_programs_with_openai(
                {
                    "building_type": "library",
                    "author_stage": "replenishment",
                    "author_request_kind": "geometry_author_replenishment",
                },
                target_count=2,
                model="task6c-model",
            )

        self.assertEqual(len(programs), 1)
        failure = programs[0].metadata[
            "author_compiler_repair_budget_failure"
        ]
        self.assertEqual(failure["quota"], "author_replenishment")
        self.assertEqual(failure["author_stage"], "replenishment")
        snapshot = paid_provider_budget_snapshot()
        self.assertEqual(snapshot["quota_request_counts"]["author_initial"], 0)
        self.assertEqual(
            snapshot["quota_request_counts"]["author_replenishment"], 1
        )

    def test_author_cache_hit_consumes_neither_partition(self):
        configure_paid_provider_budget(1, quotas={
            "author_initial": 0,
            "author_replenishment": 1,
            "base_candidate": 0,
            "exact_candidate": 0,
            "portfolio_board": 0,
            "reference_audit": 0,
            "retry": 0,
        })
        cached = base_seed_programs()[0]
        with patch(
            "design.maas.geometry_language.llm_adapter._load_author_cache",
            return_value={
                "compiled_programs": [cached.to_dict()],
                "model": "cached-model",
                "response_id": "cached-response",
            },
        ):
            programs = author_geometry_programs_with_openai(
                {
                    "author_stage": "initial",
                    "author_request_kind": "geometry_author_initial",
                },
                target_count=1,
            )
        self.assertEqual(len(programs), 1)
        self.assertEqual(paid_provider_budget_snapshot()["request_count"], 0)

    def test_cached_repair_budget_history_is_not_current_run_failure(self):
        source_name = candidate_generation.program_seed_sequences(
            "gymnasium"
        )[0].name
        historical_failure = {
            "author_stage": "replenishment",
            "code": "request_quota_exhausted",
            "limit": 1,
            "quota": "author_replenishment",
            "remaining": 0,
            "request_kind": "geometry_author_replenishment",
            "used": 1,
        }
        authored = replace(base_seed_programs()[0], metadata={
            **base_seed_programs()[0].metadata,
            "author_cache_hit": True,
            "author_compiler_repair_budget_failure": historical_failure,
        })
        request = {
            "source_seed": source_name,
            "live_llm_author": True,
            "live_vlm_revision": False,
            "llm_author_count": 1,
            "author_stage": "replenishment",
            "author_request_kind": "geometry_author_replenishment",
        }

        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "test-only"},
            clear=False,
        ), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            return_value=(authored,),
        ):
            seeds = candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[request],
            )

        authored_notes = [
            note
            for seed in seeds
            for note in seed.notes
            if note.startswith("geometry_program_llm_author_")
        ]
        self.assertIn(
            "geometry_program_llm_author_request_executed=False",
            authored_notes,
        )
        geometry_program_llm_author_budget_failures = [
            json.loads(note.split("=", 1)[1])
            for note in authored_notes
            if note.startswith(
                "geometry_program_llm_author_budget_failure="
            ) and note.split("=", 1)[1]
        ]
        self.assertEqual(
            geometry_program_llm_author_budget_failures,
            [],
        )

    def test_live_repair_budget_failure_remains_current_run_failure(self):
        source_name = candidate_generation.program_seed_sequences(
            "gymnasium"
        )[0].name
        current_failure = {
            "author_stage": "replenishment",
            "code": "request_quota_exhausted",
            "limit": 5,
            "quota": "author_replenishment",
            "remaining": 0,
            "request_kind": "geometry_author_replenishment",
            "used": 5,
        }
        authored = replace(base_seed_programs()[0], metadata={
            **base_seed_programs()[0].metadata,
            "author_cache_hit": False,
            "author_compiler_repair_budget_failure": current_failure,
        })
        request = {
            "source_seed": source_name,
            "live_llm_author": True,
            "live_vlm_revision": False,
            "llm_author_count": 1,
            "author_stage": "replenishment",
            "author_request_kind": "geometry_author_replenishment",
        }

        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "test-only"},
            clear=False,
        ), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            return_value=(authored,),
        ):
            seeds = candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[request],
            )

        authored_notes = [
            note
            for seed in seeds
            for note in seed.notes
            if note.startswith("geometry_program_llm_author_")
        ]
        self.assertIn(
            "geometry_program_llm_author_request_executed=True",
            authored_notes,
        )
        geometry_program_llm_author_budget_failures = [
            json.loads(note.split("=", 1)[1])
            for note in authored_notes
            if note.startswith(
                "geometry_program_llm_author_budget_failure="
            ) and note.split("=", 1)[1]
        ]
        self.assertEqual(
            geometry_program_llm_author_budget_failures,
            [current_failure],
        )

    def test_target3_replenishment_uses_its_partition_after_initial_exhaustion(self):
        """Benchmark replenishment must generate from its isolated author quota."""
        budget = progressive_mass_run_budget(3)
        configure_paid_provider_budget(
            budget.total_provider_request_limit,
            quotas=budget.provider_request_quotas,
        )

        def parameter(
            name, value_type, *, number=0.0, string="", vector=()
        ):
            return {
                "name": name,
                "value_type": value_type,
                "numeric_value": number,
                "string_value": string,
                "boolean_value": False,
                "vector_value": list(vector),
                "structured_json": "null",
            }

        response_payload = {
            "id": "task6c-live-author",
            "output_text": json.dumps({
                "programs": [{
                    "name": "task6c_profiled_hall",
                    "base_seed": "bar",
                    "intent_tags": ["long_span"],
                    "root_id": "result",
                    "rationale": "A profiled hall retains one access-bound mass.",
                    "nodes": [
                        {
                            "id": "base",
                            "kind": "primitive",
                            "operator": "box",
                            "inputs": [],
                            "parameters": [
                                parameter("width", "number", number=1.0),
                                parameter("depth", "number", number=1.0),
                                parameter("height", "number", number=1.0),
                            ],
                            "semantic_role": "base_seed",
                        },
                        {
                            "id": "seed",
                            "kind": "transform",
                            "operator": "scale",
                            "inputs": ["base"],
                            "parameters": [
                                parameter(
                                    "vector",
                                    "vector",
                                    vector=(2.8, 0.62, 0.48),
                                ),
                            ],
                            "semantic_role": "base_seed",
                        },
                        {
                            "id": "entry",
                            "kind": "macro",
                            "operator": "notch",
                            "inputs": ["seed"],
                            "parameters": [
                                parameter("ratio", "number", number=0.28),
                                parameter("corner", "string", string="sw"),
                                parameter("side", "string", string="west"),
                            ],
                            "semantic_role": "public_threshold",
                        },
                        {
                            "id": "result",
                            "kind": "macro",
                            "operator": "profiled_hall",
                            "inputs": ["entry"],
                            "parameters": [
                                parameter(
                                    "section_family", "string", string="ridge"
                                ),
                                parameter("span_axis", "string", string="x"),
                            ],
                            "semantic_role": "roof_section",
                        },
                    ],
                }],
            }),
        }
        http_calls = []

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps(response_payload).encode("utf-8")

        def openai_response(*_args, **_kwargs):
            http_calls.append(1)
            return Response()

        generation_site = box(0.0, 0.0, 30.0, 30.0)
        floor_context = {
            "hard_pass": True,
            "height_m": 16.0,
            "floors": 4,
            "legal_sections": (generation_site,) * 4,
            "floor_top_heights_m": (4.0, 8.0, 12.0, 16.0),
            "upper_legal_section": generation_site,
            "authority": "task6c_focused_pipeline_test",
            "legal_floor_field_hash": "task6c-focused-field",
        }

        def isolate_heavy_materialization(source, _sequence, **_kwargs):
            return replace(source, metadata={
                **source.metadata,
                "program_book_projection_evidence": {
                    "status": "materialized",
                    "authority": "task6c_isolated_heavy_materialization",
                },
                "shared_floor_contract": {
                    "schema_version": "arr.maas.shared_floor_contract.v1",
                    "hard_pass": True,
                    "plates": [],
                    "authority": "task6c_isolated_heavy_materialization",
                },
            })

        with TemporaryDirectory() as cache_directory, patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-key",
                "MAAS_GEOMETRY_AUTHOR_CACHE_DIR": cache_directory,
            },
            clear=False,
        ), patch(
            "design.maas.geometry_language.llm_adapter.urllib.request.urlopen",
            side_effect=openai_response,
        ), patch.object(
            candidate_generation,
            "_candidate_floor_context",
            return_value=floor_context,
        ), patch.object(
            candidate_generation,
            "_materialize_directed_geometry",
            side_effect=isolate_heavy_materialization,
        ) as materialize:
            for variation_offset in range(budget.initial_author_request_limit):
                author_geometry_programs_with_openai(
                    {
                        "building_type": "gymnasium",
                        "author_stage": "initial",
                        "author_request_kind": "geometry_author_initial",
                        "author_variation_offset": variation_offset,
                    },
                    target_count=1,
                    model="task6c-integration-model",
                )

            with self.assertRaises(PaidProviderBudgetError) as initial:
                author_geometry_programs_with_openai(
                    {
                        "building_type": "gymnasium",
                        "author_stage": "initial",
                        "author_request_kind": "geometry_author_initial",
                        "author_variation_offset": 99,
                    },
                    target_count=1,
                    model="task6c-integration-model",
                )

            feedback = [{
                "parent_fingerprint": "task6c-parent",
                "program_hash": "task6c-program",
                "critic_actions": [{"operation": "add_courtyard"}],
            }]
            source_name = candidate_generation.program_seed_sequences(
                "gymnasium"
            )[0].name
            cycle = portfolio_replenishment.run_replenishment_cycle(
                cycle_index=1,
                parent_variant_index=0,
                retained_selection_pool=[],
                excluded_parent_keys=set(),
                excluded_parent_fingerprints=set(),
                excluded_program_hashes=set(),
                generation_site=generation_site,
                building_type="gymnasium",
                height=16.0,
                floors=4,
                generation_context=None,
                typed_graph_mutations=[],
                geometry_program_mutations=[],
                synthesis_requests=[{
                    "source_seed": source_name,
                    "live_llm_author": True,
                    "llm_author_only": True,
                    "llm_author_count": 2,
                    "author_stage": "replenishment",
                    "author_request_kind": "geometry_author_replenishment",
                    "base_book_vlm_replenishment_feedback": feedback,
                    "llm_author_model": "task6c-integration-model",
                }],
                outcome_graph=None,
                recursive_only=True,
                target_count=3,
                exact_compile_limit=1,
                program_dimensional_context=None,
                site_boundary_source="task6c-test",
                site_access_context=None,
                site_access_geometry=None,
                runtime_live_vlm=False,
                live_vlm_selection_required=False,
                base_capacity_contract=None,
                trusted_legal_floor_field=None,
                trusted_legal_floor_field_hash="",
                trusted_clear_span_floor_plan=None,
                capacity_site=None,
                output_dir=Path(cache_directory),
                program_slug="gymnasium",
                visual_directive={},
                downstream_context={},
                hard_gate_summary=lambda _report, candidates: {
                    "candidate_count": len(candidates)
                },
                diagnostic_generation_budget={
                    "scope_labels": ["1/1"],
                    "book_probe_count": 1,
                    "evaluation_cap": 1,
                    "candidate_cap": 1,
                },
            )

        self.assertEqual(initial.exception.quota, "author_initial")
        self.assertEqual(len(cycle.generated_pool), 1)
        self.assertIsInstance(cycle.generated_pool[0], _Candidate)
        self.assertIs(
            cycle.generated_pool[0],
            cycle.downstream_evaluation_pool[0],
        )
        self.assertEqual(cycle.evidence["evaluated"], 1)
        self.assertEqual(cycle.evidence["compiled"], 1)
        self.assertEqual(cycle.evidence["clean"], 1)
        self.assertEqual(cycle.evidence["program_passed"], 1)
        self.assertEqual(materialize.call_count, 1)
        self.assertEqual(cycle.evidence["exact_compile_invocation_count"], 1)
        self.assertEqual(cycle.evidence["exact_compile_remaining"], 0)
        self.assertEqual(
            cycle.evidence["exact_compile_stop_reason"],
            "cumulative_exact_compile_budget_exhausted",
        )
        self.assertGreater(
            cycle.evidence["geometry_program_llm_author_active_seed_count"],
            0,
        )
        self.assertTrue(cycle.evidence["llm_author_request_executed"])
        self.assertTrue(cycle.evidence["critic_feedback_consumed_same_run"])
        self.assertTrue(cycle.evidence["included_in_author_context"])
        self.assertTrue(cycle.evidence["author_request_executed"])
        self.assertEqual(cycle.evidence["feedback_count"], len(feedback))
        failures = cycle.evidence[
            "geometry_program_llm_author_budget_failures"
        ]
        self.assertEqual(len(failures), 1)
        failure = failures[0]
        self.assertEqual(failure["quota"], "author_replenishment")
        self.assertEqual(failure["request_kind"], "geometry_author_replenishment")
        self.assertEqual(failure["author_stage"], "replenishment")
        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                selected_count=0,
                selected_scope_count=0,
                target_count=3,
                required_scope_count=3,
                cycles_run=1,
                cycle_budget=1,
                author_budget_failure=failure,
            ),
            "replenishment_author_quota_exhausted",
        )
        snapshot = paid_provider_budget_snapshot()
        self.assertEqual(snapshot["quota_request_counts"]["author_initial"], 2)
        self.assertEqual(snapshot["quota_request_counts"]["author_replenishment"], 1)
        self.assertEqual(snapshot["quota_request_counts"]["base_candidate"], 0)
        self.assertEqual(snapshot["quota_request_counts"]["exact_candidate"], 0)
        self.assertEqual(snapshot["quota_request_counts"]["portfolio_board"], 0)
        self.assertEqual(snapshot["request_count"], 3)
        self.assertEqual(len(http_calls), 3)


class Task6CBaseCritiqueTest(SimpleTestCase):
    def test_rejected_exact_base_audits_become_transferable_intents(self):
        graph = GeometryOutcomeGraph(path=Path("unused.json"), pnu="pnu")
        graph.observations.extend([
            {
                "stage": "book_base_vlm",
                "program_slug": "library",
                "base_review_fingerprint": "fp-a",
                "program_hash": "program-a",
                "base_book_vlm_hard_pass": False,
                "failed_base_book_vlm_gates": ["courtyard_legibility"],
                "base_book_vlm_audit": {
                    "critic_actions": [{
                        "operation": "add_courtyard",
                        "target_node_id": "stale-node-a",
                        "semantic_role": "central_void",
                        "parameters": {"margin_ratio": 0.18},
                        "rationale": "Open the center for daylight.",
                    }],
                    "geometry_edits": [{
                        "operator": "courtyard",
                        "target_id": "stale-node-b",
                        "parameters": {"open_side": "west"},
                    }],
                    "rationale": "Improve void hierarchy.",
                },
            },
            {
                "stage": "book_base_vlm",
                "program_slug": "library",
                "base_review_fingerprint": "fp-b",
                "program_hash": "program-b",
                "base_book_vlm_hard_pass": False,
                "failed_base_book_vlm_gates": ["silhouette"],
                "base_book_vlm_audit": {"critic_actions": []},
            },
        ])

        feedback = graph.base_book_vlm_replenishment_feedback(
            program_slug="library"
        )

        self.assertEqual(
            [(row["parent_fingerprint"], row["program_hash"]) for row in feedback],
            [("fp-a", "program-a"), ("fp-b", "program-b")],
        )
        serialized = json.dumps(feedback, sort_keys=True)
        self.assertNotIn("stale-node-a", serialized)
        self.assertNotIn("stale-node-b", serialized)
        self.assertNotIn("target_node_id", serialized)
        self.assertNotIn("target_id", serialized)
        self.assertIn("add_courtyard", serialized)
        self.assertIn("margin_ratio", serialized)
        self.assertIn("central_void", serialized)

    def test_deficit_request_carries_feedback_and_replenishment_stage(self):
        feedback = [{"parent_fingerprint": "fp", "program_hash": "hash"}]
        result = _deficit_directed_replenishment_inputs(
            [{"source_seed": "seed"}],
            legal_fit_repair_feedback=[],
            capacity_authoring_deficits=[],
            family_supply_deficits={},
            base_book_vlm_replenishment_feedback=feedback,
            progressive_target=3,
        )
        request = result["synthesis_requests"][0]
        self.assertEqual(request["author_stage"], "replenishment")
        self.assertEqual(
            request["author_request_kind"], "geometry_author_replenishment"
        )
        self.assertEqual(
            request["base_book_vlm_replenishment_feedback"], feedback
        )

    def test_cycle_failure_becomes_next_cycle_coordinate_free_author_feedback(self):
        cycle_n_feedback = _bounded_replenishment_causal_feedback(
            [],
            exact_repair_evidence={"failure_records": [{
                "stage": "repaired_program_compile",
                "status": "compile_failed",
                "source_sequence": "cycle-n-source",
                "geometry_family": "llm_twist_carve_void",
                "issues": [{"code": "unsupported_edit", "coordinates": [1, 2]}],
            }]},
            stage_outcomes=[
                {
                    "stage": "program_review",
                    "kind": "failed",
                    "reason": "program_fit",
                    "evidence": {
                        "program_hash": "cycle-n-program",
                        "site_boundary_geometry": {
                            "type": "Polygon",
                            "coordinates": [[[0, 0], [1, 0], [0, 0]]],
                        },
                    },
                },
                {
                    "stage": "clean_mass",
                    "kind": "passed",
                    "reason": "",
                    "evidence": {"hard_pass": True},
                },
            ],
            final_vlm_gate={"audit_records": [{
                "hard_pass": False,
                "failures": ["final_book_weak_primary_mass"],
                "source_sequence": "cycle-n-source",
                "critic_actions": ["strengthen_primary_mass"],
                "geometry_edits": [{"operation": "scale", "factor": 1.1}],
                "vlm_image_inputs": {"image_url": "forbidden"},
            }]},
        )

        cycle_n_plus_1 = _deficit_directed_replenishment_inputs(
            [{"source_seed": "seed", "candidate_count": 2}],
            legal_fit_repair_feedback=[],
            capacity_authoring_deficits=[],
            family_supply_deficits={},
            progressive_target=3,
            authored_visual_authority_replenishment_feedback=cycle_n_feedback,
            selected_count=0,
            selected_scope_count=0,
            target_count=3,
            required_scope_count=3,
            exact_compile_remaining=3,
            cycle_index=2,
            cycle_budget=2,
        )
        feedback = cycle_n_plus_1["synthesis_requests"][0][
            "authored_visual_authority_replenishment_feedback"
        ]
        serialized = json.dumps(feedback, sort_keys=True)

        self.assertIn("cycle-n-source", serialized)
        self.assertIn("program_fit", serialized)
        self.assertIn("strengthen_primary_mass", serialized)
        self.assertIn('"operation": "scale"', serialized)
        self.assertNotIn("coordinates", serialized)
        self.assertNotIn("site_boundary_geometry", serialized)
        self.assertNotIn("vlm_image_inputs", serialized)
        self.assertNotIn('"kind": "passed"', serialized)


class Task6CTruthfulEvidenceTest(SimpleTestCase):
    def test_quota_exhaustion_has_typed_replenishment_stop_priority(self):
        failure = {
            "code": "request_quota_exhausted",
            "request_kind": "geometry_author_replenishment",
            "quota": "author_replenishment",
            "used": 1,
            "limit": 1,
            "remaining": 0,
            "author_stage": "replenishment",
        }
        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                selected_count=1,
                selected_scope_count=1,
                target_count=3,
                required_scope_count=3,
                cycles_run=1,
                cycle_budget=1,
                author_budget_failure=failure,
            ),
            "replenishment_author_quota_exhausted",
        )

    def test_critic_consumption_requires_feedback_context_and_executed_request(self):
        critic_feedback_consumption_evidence = getattr(
            portfolio_replenishment,
            "critic_feedback_consumption_evidence",
            None,
        )
        self.assertIsNotNone(critic_feedback_consumption_evidence)
        self.assertEqual(
            critic_feedback_consumption_evidence(
                feedback_count=2,
                included_in_author_context=True,
                author_request_executed=True,
            )["critic_feedback_consumed_same_run"],
            True,
        )
        for kwargs, reason in (
            ({"feedback_count": 0, "included_in_author_context": True, "author_request_executed": True}, "no_feedback"),
            ({"feedback_count": 2, "included_in_author_context": False, "author_request_executed": True}, "not_included_in_author_context"),
            ({"feedback_count": 2, "included_in_author_context": True, "author_request_executed": False}, "author_request_not_executed"),
        ):
            evidence = critic_feedback_consumption_evidence(**kwargs)
            self.assertFalse(evidence["critic_feedback_consumed_same_run"])
            self.assertEqual(evidence["reason"], reason)
