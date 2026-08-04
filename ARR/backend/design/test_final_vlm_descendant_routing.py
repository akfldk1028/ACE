from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.book_language import final_vlm_cycle, lineage, portfolio_benchmark


def _candidate(
    *,
    principle_id: str = "book:combination:18:expand+shift",
    principle_kind: str = "combination",
    stage: str | None = "combination",
    operation: str = "",
    include_lineage: bool = True,
    lineage_principle_id: str | None = None,
    lineage_principle_kind: str | None = None,
    projection_status: str | None = "materialized",
):
    base_operative_ids = {
        "book:operative:expand": "book:operative:expand",
        "book:combination:18:expand+shift": "book:operative:expand",
        "book:aggregation:array+stack:rotate": "book:operative:rotate",
        "book:case:65:bend+shift": "book:operative:bend",
    }
    lineage_id = lineage_principle_id or principle_id
    base_operative_id = base_operative_ids.get(lineage_id, lineage_id)
    source_seed = "test-seed"
    scope_label = "1/1"
    orientation = "long_axis"
    variant_index = 0
    parent_key = "|".join((
        source_seed,
        base_operative_id,
        scope_label,
        orientation,
        f"v{variant_index}",
    ))
    metadata = {}
    if include_lineage:
        metadata["book_generation_lineage"] = {
            "schema_version": "arr.maas.book_generation_lineage.v1",
            "stage": stage,
            "principle_id": lineage_id,
            "principle_kind": (
                lineage_principle_kind or principle_kind
            ),
            "base_operative_id": base_operative_id,
            "parent_key": parent_key,
            "source_seed": source_seed,
            "scope_label": scope_label,
            "orientation": orientation,
            "variant_index": variant_index,
        }
    if projection_status is not None:
        metadata["program_book_projection_evidence"] = {
            "status": projection_status,
        }
    return SimpleNamespace(
        principle_id=principle_id,
        principle_kind=principle_kind,
        operation=operation,
        sequence=SimpleNamespace(name=f"candidate-{stage}"),
        source=SimpleNamespace(metadata=metadata),
        feature={"properties": {}},
        score=0.8,
    )


class FinalVlmDescendantRoutingTest(SimpleTestCase):
    def test_canonical_applied_book_kinds_route_regardless_of_operation_label(self):
        candidates = [
            _candidate(
                principle_id="book:operative:expand",
                principle_kind="base_operative",
                stage="base",
                operation="",
            ),
            _candidate(operation="arbitrary combination label"),
            _candidate(
                principle_id="book:aggregation:array+stack:rotate",
                principle_kind="aggregation",
                stage="aggregation",
                operation="",
            ),
            _candidate(
                principle_id="book:case:65:bend+shift",
                principle_kind="case_study",
                stage="case_study",
                operation="case label without prefix",
            ),
        ]
        report = {"rows": [
            {
                "combined_hard_pass": True,
                "semantic_projection_hard_gate": {"hard_pass": True},
            }
            for _candidate_item in candidates
        ]}

        with patch.object(
            portfolio_benchmark,
            "_bind_final_visual_authority_for_review",
        ):
            routed = portfolio_benchmark._final_vlm_input_from_downstream(
                candidates,
                report,
            )

        self.assertEqual(routed, candidates)
        self.assertEqual(
            report["final_vlm_routing"]["schema_version"],
            "arr.maas.final_vlm_applied_book_routing.v2",
        )
        self.assertEqual(
            report["final_vlm_routing"][
                "routed_applied_book_candidate_count"
            ],
            4,
        )

    def test_live_valid_book_descendant_calls_critic_and_approval_is_eligible(self):
        descendant = _candidate(
            stage="combination",
            operation="book:combination:split+shift",
        )
        report = {"rows": [{
            "combined_hard_pass": True,
            "semantic_projection_hard_gate": {"hard_pass": True},
        }]}

        def bind_exact(candidate, _audit):
            candidate.feature["properties"]["geometry_artifact"] = {
                "authority": "certified_projected_visual_mesh",
                "exactSurface": "archived-descendant-surface",
            }

        with patch.object(
            portfolio_benchmark,
            "_bind_final_visual_authority_for_review",
            side_effect=bind_exact,
        ):
            routed = portfolio_benchmark._final_vlm_input_from_downstream(
                [descendant],
                report,
            )

        approved = SimpleNamespace(
            **{
                **descendant.__dict__,
                "source": SimpleNamespace(metadata={
                    **descendant.source.metadata,
                    "final_book_vlm_audit": {
                        "status": "pass",
                        "hard_pass": True,
                        "response_id": "resp-final-1",
                        "critic_actions": ["retain_void"],
                    },
                }),
            }
        )
        gate = {
            "audit_records": [{
                "status": "pass",
                "hard_pass": True,
                "response_id": "resp-final-1",
                "critic_actions": ["retain_void"],
            }],
        }
        with (
            patch.object(
                final_vlm_cycle,
                "route_capacity_target_hard_passes",
                side_effect=lambda items, **_: (list(items), {"status": "pass"}),
            ),
            patch.object(
                final_vlm_cycle,
                "_bounded_visual_selection_pool",
                side_effect=lambda items: list(items),
            ),
            patch.object(
                final_vlm_cycle,
                "_audit_final_book_geometry_with_vlm",
                return_value=([approved], gate),
            ) as critic,
            patch.object(
                final_vlm_cycle,
                "_repair_exact_post_book_candidates_from_vlm",
                return_value=([], {}),
            ),
        ):
            result = final_vlm_cycle.run_final_vlm_cycle(
                routed,
                retained_hard_passes=[],
                building_type="neighborhood_living",
                output_dir=Path("unused"),
                visual_directive={},
                outcome_graph=object(),
                program_slug="neighborhood",
                generation_site=object(),
                height=15.0,
                floors=5,
                generation_context=None,
                program_dimensional_context={},
                site_boundary_source="test",
                site_access_context={},
                site_access_geometry={},
                base_capacity_contract={},
                downstream_context={},
                hard_gate_summary=lambda report, pool: {
                    "candidate_count": len(pool)
                },
                completion_status="complete",
                no_repair_status="no_repair",
                target_count=5,
            )

        critic.assert_called_once()
        reviewed = critic.call_args.args[0]
        self.assertEqual(len(reviewed), 1)
        self.assertEqual(
            reviewed[0].feature["properties"]["geometry_artifact"]["exactSurface"],
            "archived-descendant-surface",
        )
        self.assertEqual(result.selection_pool, [approved])
        self.assertEqual(
            result.final_vlm_gate["audit_records"][0]["response_id"],
            "resp-final-1",
        )

    def test_applied_base_stage_book_operation_routes_to_final_vlm(self):
        base = _candidate(
            principle_id="book:operative:expand",
            principle_kind="base_operative",
            stage="base",
            operation="book:operative:bend",
        )
        report = {"rows": [{
            "combined_hard_pass": True,
            "semantic_projection_hard_gate": {"hard_pass": True},
        }]}

        with patch.object(
            portfolio_benchmark,
            "_bind_final_visual_authority_for_review",
        ):
            routed = portfolio_benchmark._final_vlm_input_from_downstream(
                [base],
                report,
            )

        self.assertEqual(routed, [base])
        self.assertEqual(
            report["final_vlm_routing"]["base_only_excluded_count"],
            0,
        )
        self.assertEqual(
            report["final_vlm_routing"]["routed_book_descendant_count"],
            1,
        )

    def test_raw_base_without_operation_remains_base_only(self):
        raw_base = _candidate(
            principle_id="",
            principle_kind="",
            stage=None,
            operation="",
            include_lineage=False,
            projection_status=None,
        )
        report = {"rows": [{
            "combined_hard_pass": True,
            "semantic_projection_hard_gate": {"hard_pass": True},
        }]}

        routed = portfolio_benchmark._final_vlm_input_from_downstream(
            [raw_base],
            report,
        )

        self.assertEqual(routed, [])
        self.assertEqual(
            report["final_vlm_routing"]["base_only_excluded_count"],
            1,
        )
        self.assertEqual(
            report["final_vlm_routing"]["non_book_excluded_count"],
            0,
        )

    def test_invalid_applied_book_contracts_emit_typed_reasons(self):
        cases = [
            (
                "raw_base",
                _candidate(
                    principle_id="",
                    principle_kind="",
                    include_lineage=False,
                    projection_status=None,
                ),
            ),
            (
                "missing_lineage",
                _candidate(include_lineage=False),
            ),
            (
                "unknown_principle",
                _candidate(
                    principle_id="unknown-principle",
                    principle_kind="combination",
                ),
            ),
            (
                "principle_id_mismatch",
                _candidate(
                    lineage_principle_id="book:operative:expand",
                    lineage_principle_kind="base_operative",
                ),
            ),
            (
                "principle_kind_mismatch",
                _candidate(principle_kind="base_operative"),
            ),
            (
                "projection_not_materialized",
                _candidate(projection_status="failed"),
            ),
        ]
        candidates = [candidate for _reason, candidate in cases]
        report = {"rows": [{
            "combined_hard_pass": True,
            "semantic_projection_hard_gate": {"hard_pass": True},
        } for _candidate_item in candidates]}

        for expected_reason, candidate in cases:
            with self.subTest(reason=expected_reason):
                classification = lineage.classify_applied_book_candidate(
                    candidate
                )
                self.assertIsInstance(
                    classification,
                    lineage.AppliedBookCandidateClassification,
                )
                self.assertFalse(classification.eligible)
                self.assertEqual(
                    classification.reason.value,
                    expected_reason,
                )

        routed = portfolio_benchmark._final_vlm_input_from_downstream(
            candidates,
            report,
        )

        self.assertEqual(routed, [])
        self.assertEqual(
            report["final_vlm_routing"]["base_only_excluded_count"],
            1,
        )
        self.assertEqual(
            report["final_vlm_routing"]["non_book_excluded_count"],
            5,
        )
        self.assertEqual(
            report["final_vlm_routing"]["exclusion_reason_counts"],
            {reason: 1 for reason, _candidate_item in cases},
        )

    def test_critic_rejection_with_response_remains_unselected(self):
        descendant = _candidate(
            stage="combination",
            operation="book:combination:split+shift",
        )
        rejection_gate = {
            "audit_records": [{
                "status": "fail",
                "hard_pass": False,
                "response_id": "resp-final-reject",
                "critic_actions": ["repair_entry"],
                "failures": ["final_book_gesture_clarity_failed"],
            }],
        }
        with (
            patch.object(
                final_vlm_cycle,
                "route_capacity_target_hard_passes",
                side_effect=lambda items, **_: (list(items), {"status": "pass"}),
            ),
            patch.object(
                final_vlm_cycle,
                "_bounded_visual_selection_pool",
                side_effect=lambda items: list(items),
            ),
            patch.object(
                final_vlm_cycle,
                "_audit_final_book_geometry_with_vlm",
                return_value=([], rejection_gate),
            ) as critic,
            patch.object(
                final_vlm_cycle,
                "_repair_exact_post_book_candidates_from_vlm",
                return_value=([], {}),
            ),
        ):
            result = final_vlm_cycle.run_final_vlm_cycle(
                [descendant], retained_hard_passes=[],
                building_type="neighborhood_living", output_dir=Path("unused"),
                visual_directive={}, outcome_graph=object(),
                program_slug="neighborhood", generation_site=object(),
                height=15.0, floors=5, generation_context=None,
                program_dimensional_context={}, site_boundary_source="test",
                site_access_context={}, site_access_geometry={},
                base_capacity_contract={}, downstream_context={},
                hard_gate_summary=lambda report, pool: {"candidate_count": len(pool)},
                completion_status="complete", no_repair_status="no_repair",
                target_count=5,
            )

        critic.assert_called_once()
        self.assertEqual(result.selection_pool, [])
        record = result.final_vlm_gate["audit_records"][0]
        self.assertEqual(record["response_id"], "resp-final-reject")
        self.assertEqual(record["critic_actions"], ["repair_entry"])
        self.assertFalse(record["hard_pass"])
