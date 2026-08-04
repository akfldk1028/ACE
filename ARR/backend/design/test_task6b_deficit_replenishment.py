import os
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.book_language import candidate_generation
from design.maas.book_language import competition_portfolio_contract
from design.maas.book_language import portfolio_benchmark
from design.maas.book_language import portfolio_replenishment
from design.maas.book_language.final_vlm_cycle import FinalVlmCycleResult
from design.maas.geometry_language import base_seed_programs
from design.test_maas_floorwise_candidate_rejection import _slab_fallback_case


class Task6BDeficitDirectedReplenishmentTest(SimpleTestCase):
    def test_replenishment_final_vlm_selection_preserves_certified_binding(self):
        artifact = {"canonical": "artifact"}
        anchor = {"expected_semantic_projection_hash": "semantic-hash"}
        candidate = SimpleNamespace(
            source=SimpleNamespace(metadata={
                "shared_floor_contract": {"hard_pass": True},
            }),
            feature={"type": "Feature", "properties": {}},
        )

        def bind(review_candidate, audit):
            self.assertEqual(audit["semantic_projection_hash"], "semantic-hash")
            review_candidate.feature["properties"].update({
                "geometry_artifact": artifact,
                "final_semantic_anchor": anchor,
                "certified_mass_artifact_core_hash": "core-hash",
            })

        def final_cycle(review_pool, **_kwargs):
            props = review_pool[0].feature["properties"]
            self.assertIs(props["geometry_artifact"], artifact)
            self.assertEqual(
                props["certified_mass_artifact_core_hash"], "core-hash"
            )
            return FinalVlmCycleResult(
                selection_pool=list(review_pool),
                initial_vlm_passes=list(review_pool),
                initial_vlm_gate={},
                repair_pool=[],
                repair_vlm_passes=[],
                repair_evidence={},
                final_vlm_gate={},
            )

        with patch.object(
            portfolio_replenishment,
            "_program_pool",
            return_value=([candidate], {}),
        ), patch.object(
            portfolio_replenishment,
            "audit_book_base_stage_with_vlm",
            return_value=([candidate], {}),
        ), patch.object(
            portfolio_replenishment,
            "evaluate_accepted_sources_downstream",
            return_value={"rows": [{
                "combined_hard_pass": True,
                "semantic_projection_hard_gate": {
                    "semantic_projection_hash": "semantic-hash",
                },
            }]},
        ), patch.object(
            portfolio_replenishment,
            "_solid_morphology_metrics",
            return_value={"degenerate_sheet_like": False},
        ), patch.object(
            portfolio_replenishment,
            "_bind_final_visual_authority_for_review",
            side_effect=bind,
            create=True,
        ) as binder, patch.object(
            portfolio_replenishment,
            "run_final_vlm_cycle",
            side_effect=final_cycle,
        ):
            result = portfolio_replenishment.run_replenishment_cycle(
                cycle_index=1,
                parent_variant_index=1,
                retained_selection_pool=[],
                excluded_parent_keys=set(),
                excluded_parent_fingerprints=set(),
                excluded_program_hashes=set(),
                generation_site=object(),
                building_type="library",
                height=20.0,
                floors=5,
                generation_context=object(),
                typed_graph_mutations=[],
                geometry_program_mutations=[],
                synthesis_requests=[],
                outcome_graph=None,
                recursive_only=True,
                target_count=1,
                exact_compile_limit=1,
                program_dimensional_context=None,
                site_boundary_source="test",
                site_access_context=None,
                site_access_geometry=None,
                runtime_live_vlm=True,
                live_vlm_selection_required=False,
                base_capacity_contract=None,
                trusted_legal_floor_field=None,
                trusted_legal_floor_field_hash="",
                trusted_clear_span_floor_plan=None,
                capacity_site=None,
                output_dir=portfolio_replenishment.Path("."),
                program_slug="library",
                visual_directive={},
                downstream_context={},
                hard_gate_summary=lambda _report, _pool: {},
            )

        binder.assert_called_once()
        self.assertIs(
            result.selection_pool[0].feature["properties"][
                "geometry_artifact"
            ],
            artifact,
        )

    def test_capacity_retry_opportunity_materializes_authored_geometry_once(self):
        materialize_once = getattr(
            candidate_generation,
            "_materialize_once_for_capacity_policy",
            None,
        )
        self.assertIsNotNone(materialize_once)
        calls = []

        result = materialize_once(
            lambda coverage, targets: calls.append((coverage, targets)) or "source",
            0.72,
            (100.0, 90.0),
        )

        self.assertEqual(result, "source")
        self.assertEqual(calls, [(0.72, (100.0, 90.0))])
        self.assertEqual(
            candidate_generation.GEOMETRY_RETRY_POLICY,
            "diagnostic_only_no_geometry_replacement",
        )

    def test_capacity_authoring_deficit_is_typed_and_bounded(self):
        build_deficit = getattr(
            candidate_generation,
            "_capacity_authoring_deficit",
            None,
        )
        self.assertIsNotNone(build_deficit)

        deficit = build_deficit(
            resolved_capacity_hard_pass=False,
            parent_fingerprint="parent-fp",
            parent_program_hash="program-hash",
            geometry_family="recursive_family",
            body_phenotype="body-family",
            scope="1/2",
            capacity_band="brief_target",
            achieved_utilization=0.61,
            required_utilization=0.70,
            measured_gfa_m2=61.0,
            feasible_gfa_m2=100.0,
            achieved_floor_areas_m2=None,
            target_floor_areas_m2=(35.0, 35.0),
            terminal_materialization_reason="",
        )

        self.assertEqual(deficit["type"], "capacity_authoring_deficit")
        self.assertEqual(deficit["geometry_retry_policy"], candidate_generation.GEOMETRY_RETRY_POLICY)
        self.assertEqual(deficit["gfa_deficit_m2"], 9.0)
        self.assertNotIn("floor_target_deficit_m2", deficit)
        self.assertEqual(deficit["per_floor_deficit_status"], "unavailable")
        self.assertEqual(deficit["required_minimum_utilization"], 0.70)
        self.assertNotIn("desired_shape", deficit)

        self.assertIsNone(build_deficit(
            resolved_capacity_hard_pass=True,
            parent_fingerprint="passing",
            parent_program_hash="passing-hash",
            geometry_family="family",
            body_phenotype="body",
            scope="1/1",
            capacity_band="band",
            achieved_utilization=0.8,
            required_utilization=0.7,
            measured_gfa_m2=80.0,
            feasible_gfa_m2=100.0,
            achieved_floor_areas_m2=(40.0, 40.0),
            target_floor_areas_m2=(35.0, 35.0),
        ))

    def test_target3_family_supply_deficits_derive_from_contract(self):
        derive = getattr(
            competition_portfolio_contract,
            "competition_family_supply_deficits",
            None,
        )
        self.assertIsNotNone(derive)
        facts = [
            {
                "body_phenotype": "same-body",
                "body_roof_signature": "same-body|same-roof",
                "geometry_family": "same-family",
                "visible_stepped": True,
            }
            for _ in range(3)
        ]

        deficits = derive(
            facts,
            target_count=3,
            pair_distances=(0.10, 0.18, 0.12),
        )

        self.assertEqual(deficits["required_body_phenotype_distinct"], 3)
        self.assertEqual(deficits["available_body_phenotype_distinct"], 1)
        self.assertEqual(deficits["required_body_roof_signature_distinct"], 3)
        self.assertEqual(deficits["available_body_roof_signature_distinct"], 1)
        self.assertEqual(deficits["overrepresented_geometry_family_counts"], {"same-family": 3})
        self.assertEqual(deficits["pair_distance_conflict_count"], 2)
        self.assertEqual(deficits["visible_stepped_count"], 3)
        self.assertEqual(deficits["visible_stepped_maximum"], 1)

    def test_unknown_family_values_do_not_satisfy_distinct_supply(self):
        derive = competition_portfolio_contract.competition_family_supply_deficits
        deficits = derive([
            {"body_phenotype": "unclassified", "roof_archetype": "roof-a", "geometry_family": "unknown"},
            {"body_phenotype": "unknown", "roof_archetype": "roof-b", "geometry_family": "unclassified"},
        ], target_count=3)
        self.assertEqual(deficits["available_body_phenotype_distinct"], 0)
        self.assertEqual(deficits["available_body_roof_signature_distinct"], 0)
        self.assertEqual(deficits["unknown_body_phenotype_count"], 2)
        self.assertEqual(deficits["unknown_body_roof_signature_count"], 2)

    def test_signature_supply_requires_known_body_and_known_roof_components(self):
        derive = competition_portfolio_contract.competition_family_supply_deficits
        deficits = derive([
            {
                "body_phenotype": "known-body",
                "roof_archetype": "unclassified",
                "body_roof_signature": "known-body|unclassified",
            },
            {
                "body_phenotype": "unknown",
                "roof_archetype": "known-roof",
                "body_roof_signature": "unknown|known-roof",
            },
            {
                "body_phenotype": "known-body",
                "roof_archetype": "known-roof",
                "body_roof_signature": "known-body|known-roof",
            },
        ], target_count=3)
        self.assertEqual(deficits["available_body_phenotype_distinct"], 1)
        self.assertEqual(deficits["available_body_roof_signature_distinct"], 1)
        self.assertEqual(deficits["unknown_body_roof_signature_count"], 2)

    def test_actual_author_call_receives_structured_deficit_context(self):
        source_name = candidate_generation.program_seed_sequences("gymnasium")[0].name
        authored = replace(base_seed_programs()[0], metadata={
            **base_seed_programs()[0].metadata,
            "author_provider": "test",
        })
        request = {
            "source_seed": source_name,
            "live_llm_author": True,
            "live_vlm_revision": False,
            "llm_author_count": 1,
            "legal_fit_repair_feedback": [{"typed_reasons": ["affine_fit_failed"]}],
            "capacity_authoring_deficits": [{"type": "capacity_authoring_deficit", "gfa_deficit_m2": 9.0}],
            "family_supply_deficits": {"body_phenotype_shortfall": 2},
            "require_new_geometry_program_ast": True,
        }
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}, clear=False), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            return_value=(authored,),
        ) as author:
            candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[request],
            )
        context = author.call_args.args[0]
        self.assertEqual(context["legal_fit_repair_feedback"], request["legal_fit_repair_feedback"])
        self.assertEqual(context["capacity_authoring_deficits"], request["capacity_authoring_deficits"])
        self.assertEqual(context["family_supply_deficits"], request["family_supply_deficits"])
        self.assertIs(context["require_new_geometry_program_ast"], True)

    def test_actual_author_call_receives_full_book_graph_author_vocabulary(self):
        source_name = candidate_generation.program_seed_sequences("gymnasium")[0].name
        authored = replace(base_seed_programs()[0], metadata={
            **base_seed_programs()[0].metadata,
            "author_provider": "test",
        })
        request = {
            "source_seed": source_name,
            "live_llm_author": True,
            "live_vlm_revision": False,
            "llm_author_count": 1,
        }
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}, clear=False), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            return_value=(authored,),
        ) as author:
            candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[request],
            )

        context = author.call_args.args[0]
        self.assertIn("book_graph_vocabulary", context)
        vocabulary = context["book_graph_vocabulary"]
        registry = candidate_generation.build_book_language_registry()
        expected_ids = [
            principle["principle_id"]
            for principle in registry["principles"]
        ]

        self.assertEqual(
            vocabulary["schema_version"],
            "arr.maas.book_graph_author_vocabulary.v1",
        )
        self.assertEqual(vocabulary["corpus_id"], registry["corpus_id"])
        self.assertEqual(vocabulary["principle_count"], len(expected_ids))
        self.assertEqual(
            [principle["principle_id"] for principle in vocabulary["principles"]],
            expected_ids,
        )
        self.assertEqual(
            {principle["kind"] for principle in vocabulary["principles"]},
            {"base_operative", "combination", "aggregation", "case_study"},
        )
        self.assertNotIn("pages", vocabulary)

    def test_replenishment_forwards_retained_pool_principle_supply_as_diagnostic(self):
        retained = [
            SimpleNamespace(
                principle_id="book:operative:add",
                principle_kind="base_operative",
            ),
            SimpleNamespace(
                principle_id="book:operative:add",
                principle_kind="base_operative",
            ),
            SimpleNamespace(
                principle_id="book:combination:01:add+displace",
                principle_kind="combination",
            ),
        ]
        request = {"source_seed": "seed", "live_llm_author": True}

        with patch.object(
            portfolio_replenishment,
            "_program_pool",
            return_value=([], {}),
        ) as program_pool, patch.object(
            portfolio_replenishment,
            "_bounded_visual_selection_pool",
            side_effect=lambda candidates: list(candidates),
        ):
            portfolio_replenishment.run_replenishment_cycle(
                cycle_index=1,
                parent_variant_index=1,
                retained_selection_pool=retained,
                excluded_parent_keys=set(),
                excluded_parent_fingerprints=set(),
                excluded_program_hashes=set(),
                generation_site=object(),
                building_type="library",
                height=20.0,
                floors=5,
                generation_context=None,
                typed_graph_mutations=[],
                geometry_program_mutations=[],
                synthesis_requests=[request],
                outcome_graph=None,
                recursive_only=True,
                target_count=3,
                exact_compile_limit=24,
                program_dimensional_context=None,
                site_boundary_source="test",
                site_access_context=None,
                site_access_geometry=None,
                runtime_live_vlm=False,
                live_vlm_selection_required=False,
                base_capacity_contract=None,
                trusted_legal_floor_field=None,
                trusted_legal_floor_field_hash="",
                trusted_clear_span_floor_plan=None,
                capacity_site=None,
                output_dir=portfolio_replenishment.Path("."),
                program_slug="library",
                visual_directive={},
                downstream_context={},
                hard_gate_summary=lambda _report, _pool: {},
            )

        forwarded = program_pool.call_args.kwargs["synthesis_requests"][0]
        self.assertEqual(forwarded["source_seed"], "seed")
        self.assertIn("book_graph_supply", forwarded)
        self.assertEqual(
            forwarded["book_graph_supply"],
            {
                "schema_version": "arr.maas.book_graph_supply.v1",
                "hard_gate_effect": "none_diagnostic_only",
                "principle_id_counts": {
                    "book:combination:01:add+displace": 1,
                    "book:operative:add": 2,
                },
                "principle_kind_counts": {
                    "base_operative": 2,
                    "combination": 1,
                },
            },
        )
        self.assertNotIn("book_graph_supply", request)

    def test_replenishment_context_propagates_all_feedback_and_target3_compile_limit(self):
        build_inputs = getattr(
            portfolio_benchmark,
            "_deficit_directed_replenishment_inputs",
            None,
        )
        self.assertIsNotNone(build_inputs)

        result = build_inputs(
            [{"prompt": "author recursive AST"}],
            legal_fit_repair_feedback=[{"typed_reasons": ["affine_fit_failed"]}],
            capacity_authoring_deficits=[{"type": "capacity_authoring_deficit"}],
            family_supply_deficits={"body_phenotype_shortfall": 2},
            progressive_target=3,
        )

        request = result["synthesis_requests"][0]
        self.assertEqual(len(request["legal_fit_repair_feedback"]), 1)
        self.assertEqual(len(request["capacity_authoring_deficits"]), 1)
        self.assertEqual(request["family_supply_deficits"]["body_phenotype_shortfall"], 2)
        self.assertTrue(request["require_new_geometry_program_ast"])
        self.assertEqual(result["exact_compile_limit"], 24)

    def test_replenishment_provider_request_requires_measured_capacity_response(self):
        source_name = candidate_generation.program_seed_sequences("gymnasium")[0].name
        authored = replace(base_seed_programs()[0], metadata={
            **base_seed_programs()[0].metadata,
            "author_provider": "test",
        })
        deficits = [{
            "type": "capacity_authoring_deficit",
            "rejected_parent_program_hash": "capacity-parent-hash",
            "scope": "1/2",
            "required_minimum_utilization": 0.70,
            "achieved_utilization": 0.61,
            "gfa_deficit_m2": 90.0,
            "per_floor_deficit_status": "measured",
            "per_floor_gfa_deficit_m2": [30.0, 25.0, 20.0, 15.0],
        }]
        replenishment = portfolio_benchmark._deficit_directed_replenishment_inputs(
            [{
                "source_seed": source_name,
                "live_llm_author": True,
                "live_vlm_revision": False,
                "llm_author_count": 1,
            }],
            legal_fit_repair_feedback=[],
            capacity_authoring_deficits=deficits,
            family_supply_deficits={"body_phenotype_shortfall": 2},
            progressive_target=3,
        )
        request = replenishment["synthesis_requests"][0]

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}, clear=False), patch.object(
            candidate_generation,
            "author_geometry_programs_with_openai",
            return_value=(authored,),
        ) as author:
            candidate_generation._agent_mutated_seeds(
                "gymnasium",
                mutations=None,
                synthesis_requests=[request],
            )

        provider_context = author.call_args.args[0]
        provider_deficits = provider_context["capacity_authoring_deficits"]
        self.assertEqual(len(provider_deficits), 1)
        self.assertEqual(
            provider_deficits[0]["per_floor_gfa_deficit_m2"],
            deficits[0]["per_floor_gfa_deficit_m2"],
        )
        self.assertEqual(
            provider_deficits[0]["required_minimum_utilization"],
            deficits[0]["required_minimum_utilization"],
        )
        contract = provider_deficits[0]["replenishment_response_contract"]
        self.assertEqual(
            contract["schema_version"],
            "arr.maas.capacity_replenishment_contract.v1",
        )
        self.assertTrue(contract["require_new_geometry_program_ast"])
        self.assertTrue(contract["preserve_legal_floor_sections"])
        self.assertTrue(contract["preserve_typed_book_operations"])
        self.assertTrue(contract["preserve_authored_identity"])
        self.assertTrue(contract["require_family_diversity_response"])
        instruction = provider_deficits[0]["authoring_instruction"]
        self.assertIn("per-floor GFA deficits", instruction)
        self.assertIn("required utilization", instruction)
        self.assertIn("preserve legal floor sections", instruction)
        self.assertIn("typed BOOK operations", instruction)
        self.assertIn("family diversity", instruction)

    def test_replenishment_cycle_excludes_rejected_parent_program_hash(self):
        duplicate_metadata = [
            {"geometry_program_bridge_evidence": {"program_hash": "same-hash"}},
            {"final_semantic_projection_context": {"program_hash": "same-hash"}},
            {"geometry_graph_snapshot": {"program_hash": "same-hash"}},
            {"geometry_program": {"program_hash": "same-hash"}},
        ]
        duplicates = [
            SimpleNamespace(source=SimpleNamespace(metadata={
                "shared_floor_contract": {"hard_pass": True},
                **metadata,
            }))
            for metadata in duplicate_metadata
        ]
        fresh = SimpleNamespace(
            source=SimpleNamespace(
                metadata={
                    "shared_floor_contract": {"hard_pass": True},
                    "geometry_program_bridge_evidence": {"program_hash": "fresh-hash"},
                }
            )
        )
        with patch.object(
            portfolio_replenishment,
            "_program_pool",
            return_value=([*duplicates, fresh], {}),
        ), patch.object(
            portfolio_replenishment,
            "_solid_morphology_metrics",
            return_value={"degenerate_sheet_like": False},
        ), patch.object(
            portfolio_replenishment,
            "_bounded_visual_selection_pool",
            side_effect=lambda candidates: list(candidates),
        ):
            result = portfolio_replenishment.run_replenishment_cycle(
                cycle_index=1,
                parent_variant_index=1,
                retained_selection_pool=[],
                excluded_parent_keys=set(),
                excluded_parent_fingerprints=set(),
                excluded_program_hashes={"same-hash"},
                generation_site=object(),
                building_type="library",
                height=20.0,
                floors=5,
                generation_context=None,
                typed_graph_mutations=[],
                geometry_program_mutations=[],
                synthesis_requests=[],
                outcome_graph=None,
                recursive_only=True,
                target_count=3,
                exact_compile_limit=24,
                program_dimensional_context=None,
                site_boundary_source="test",
                site_access_context=None,
                site_access_geometry=None,
                runtime_live_vlm=False,
                live_vlm_selection_required=False,
                base_capacity_contract=None,
                trusted_legal_floor_field=None,
                trusted_legal_floor_field_hash="",
                trusted_clear_span_floor_plan=None,
                capacity_site=None,
                output_dir=portfolio_replenishment.Path("."),
                program_slug="library",
                visual_directive={},
                downstream_context={},
                hard_gate_summary=lambda report, pool: {},
            )

        self.assertEqual(result.generated_pool, [fresh])
        self.assertEqual(result.evidence["duplicate_parent_program_hash_excluded_count"], 4)

    def test_actual_program_pool_materializes_once_for_retry_opportunity(self):
        source, _program, legal_section, _sequence, _context = _slab_fallback_case()
        generation_context = SimpleNamespace(
            evidence={},
            generation_site=legal_section,
        )
        floor_context = {
            "hard_pass": True,
            "height_m": 16.0,
            "floors": 4,
            "legal_sections": (legal_section,) * 4,
            "floor_top_heights_m": (4.0, 8.0, 12.0, 16.0),
            "upper_legal_section": legal_section,
            "authority": "task6b_retry_probe",
            "legal_floor_field_hash": "",
        }
        contract = {
            "target_floor_areas_m2": [50.0] * 4,
            "feasible_maximum_floor_area_m2": 400.0,
            "minimum_utilization": 0.7,
        }
        alternative = {
            "alternative_id": "brief_target",
            "target_utilization": 0.7,
            "feasible_minimum_utilization": 0.7,
        }
        projection = {
            **alternative,
            "target_hard_pass": False,
            "selectable_capacity_hard_pass": False,
        }
        measurement = {
            "hard_pass": False,
            "floor_area_m2": 240.0,
            "feasible_maximum_floor_area_m2": 400.0,
            "feasible_capacity_utilization": 0.6,
        }
        with (
            patch.object(candidate_generation, "compile_sequence_to_source_mass", return_value=source),
            patch.object(candidate_generation, "_candidate_floor_context", return_value=floor_context),
            patch.object(candidate_generation, "generation_site_at_height", return_value=legal_section),
            patch.object(candidate_generation, "_materialize_directed_geometry", return_value=source) as materialize,
            patch.object(candidate_generation, "build_capacity_alternative", return_value=alternative),
            patch.object(candidate_generation, "capacity_alternative_for_host", return_value=alternative),
            patch.object(candidate_generation, "capacity_contract_for_alternative", return_value=contract),
            patch.object(candidate_generation, "_shared_floor_capacity_measurement", return_value=({"hard_pass": True}, measurement)),
            patch.object(candidate_generation, "capacity_retry_plan_coverage", return_value=0.9),
            patch.object(candidate_generation, "capacity_retry_floor_targets", return_value=(70.0,) * 4),
            patch.object(candidate_generation, "_capacity_retry_required", return_value=True) as retry_required,
            patch.object(candidate_generation, "materialize_shared_floor_contract", return_value={"schema_version": "arr.maas.shared_floor_contract.v1", "hard_pass": True, "plates": []}),
            patch.object(candidate_generation, "measure_source_capacity", return_value=measurement),
            patch.object(candidate_generation, "evaluate_capacity_alternative", return_value=projection),
            patch.object(candidate_generation, "resolve_capacity_band_evidence", return_value={
                "resolved_capacity_alternative_id": "brief_target",
                "resolved_capacity_target_utilization": 0.7,
                "resolved_capacity_minimum_utilization": 0.7,
                "achieved_capacity_utilization": 0.6,
                "resolved_capacity_hard_pass": False,
            }),
        ):
            candidate_generation._program_pool(
                legal_section,
                "gymnasium",
                16.0,
                4,
                generation_context=generation_context,
                recursive_only=True,
                base_capacity_contract=contract,
                capacity_site=legal_section,
                exact_compile_limit=1,
                diagnostic_evaluation_cap=1,
                diagnostic_candidate_cap=1,
            )
        retry_required.assert_called()
        self.assertEqual(materialize.call_count, 1)

    def test_actual_program_pool_zero_exact_budget_prevents_materialization(self):
        source, _program, legal_section, _sequence, _context = _slab_fallback_case()
        with patch.object(candidate_generation, "compile_sequence_to_source_mass", return_value=source), patch.object(
            candidate_generation,
            "_materialize_directed_geometry",
            side_effect=AssertionError("zero remaining budget compiled geometry"),
        ) as materialize:
            _pool, report = candidate_generation._program_pool(
                legal_section,
                "gymnasium",
                16.0,
                4,
                recursive_only=True,
                exact_compile_limit=0,
                diagnostic_evaluation_cap=2,
                diagnostic_candidate_cap=2,
            )
        materialize.assert_not_called()
        self.assertEqual(report["exact_compile_invocation_count"], 0)
        self.assertEqual(report["exact_compile_stop_reason"], "cumulative_exact_compile_budget_exhausted")

    def test_cumulative_compile_budget_subtracts_actual_initial_and_cycle_usage(self):
        remaining = getattr(portfolio_benchmark, "_remaining_exact_compile_budget", None)
        self.assertIsNotNone(remaining)
        self.assertEqual(remaining(24, 17), 7)
        self.assertEqual(remaining(24, 17, 7), 0)
        self.assertEqual(remaining(24, 17, 9), 0)
        self.assertLessEqual(17 + min(7, remaining(24, 17)), 24)

    def test_production_cycle_seam_passes_remaining_and_stops_at_zero(self):
        invoke = getattr(
            portfolio_benchmark,
            "_run_replenishment_cycle_with_compile_authority",
            None,
        )
        self.assertIsNotNone(invoke)
        received_limits = []

        def fake_cycle(**kwargs):
            received_limits.append(kwargs["exact_compile_limit"])
            return SimpleNamespace(
                evidence={"exact_compile_invocation_count": 7}
            )

        stop = {}
        first = invoke(
            fake_cycle,
            exact_compile_remaining=7,
            compile_stop_sink=stop,
            cycle_index=1,
            exact_compile_limit=24,
        )
        used = 17 + first.evidence["exact_compile_invocation_count"]
        next_remaining = portfolio_benchmark._remaining_exact_compile_budget(
            24,
            used,
        )
        second = invoke(
            fake_cycle,
            exact_compile_remaining=next_remaining,
            compile_stop_sink=stop,
            cycle_index=2,
            exact_compile_limit=24,
        )

        self.assertEqual(received_limits, [7])
        self.assertIsNone(second)
        self.assertEqual(
            stop["progressive_exact_compile_stop"]["status"],
            "cumulative_exact_compile_budget_exhausted",
        )
        self.assertEqual(
            stop["progressive_exact_compile_stop"]["cycle_not_started"],
            2,
        )

    def test_capacity_advisory_never_grants_downstream_capacity_pass(self):
        self.assertFalse(candidate_generation._capacity_retry_result_is_selectable(
            {"hard_pass": True},
            {"feasible_capacity_utilization": 0.9},
            {"feasible_capacity_utilization": 0.6},
        ))
