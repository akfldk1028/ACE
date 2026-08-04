from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.book_language import final_vlm_cycle, portfolio_benchmark


def _candidate(
    *,
    stage: str,
    operation: str,
    principle_kind: str | None = None,
):
    return SimpleNamespace(
        principle_id="principle",
        principle_kind=(
            principle_kind
            if principle_kind is not None
            else ("base_operative" if stage == "base" else "combination")
        ),
        operation=operation,
        sequence=SimpleNamespace(name=f"candidate-{stage}"),
        source=SimpleNamespace(metadata={
            "book_generation_lineage": {
                "stage": stage,
                "parent_key": "parent-1",
            },
        }),
        feature={"properties": {}},
        score=0.8,
    )


class FinalVlmDescendantRoutingTest(SimpleTestCase):
    def test_applied_descendant_lineage_routes_despite_base_principle_kind(self):
        descendant = _candidate(
            stage="combination",
            operation="book:combination:expand+shift",
            principle_kind="base_operative",
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
                [descendant],
                report,
            )

        self.assertEqual(routed, [descendant])
        self.assertEqual(
            report["final_vlm_routing"]["base_only_excluded_count"],
            0,
        )
        self.assertEqual(
            report["final_vlm_routing"]["routed_book_descendant_count"],
            1,
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

    def test_base_only_is_not_routed_and_records_no_call_reason(self):
        base = _candidate(stage="base", operation="book:operative:bend")
        report = {"rows": [{
            "combined_hard_pass": True,
            "semantic_projection_hard_gate": {"hard_pass": True},
        }]}

        routed = portfolio_benchmark._final_vlm_input_from_downstream(
            [base],
            report,
        )

        self.assertEqual(routed, [])
        self.assertEqual(
            report["final_vlm_routing"]["no_call_reason"],
            "no_law_parking_structural_valid_book_descendants",
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
