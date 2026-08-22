import os
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from unittest.mock import patch

from django.test import SimpleTestCase
from PIL import Image
from shapely.geometry import Polygon

from design.management.commands.benchmark_maas_book_program_portfolios import (
    _progressive_provider_budget_lifecycle,
)
from design.maas.book_language import final_vlm_cycle
from design.maas.book_language import vlm_review
from design.maas.book_language.candidate_analysis import _Candidate, VerbSequence
from design.maas.geometry_language import base_seed_programs
from design.maas.paid_provider_budget import (
    configure_paid_provider_budget,
    paid_provider_budget_snapshot,
    reset_paid_provider_budget_for_tests,
    reserve_paid_provider_request,
)
from design.maas.preference import vlm_scorer
from design.maas.preference.vlm_scorer import (
    VlmBudgetExhaustedError,
    audit_reference_image_for_massing,
    score_candidate_with_openai_vlm,
)


def _quotas(**overrides):
    quotas = {
        "author": 0,
        "base_candidate": 0,
        "exact_candidate": 0,
        "portfolio_board": 0,
        "reference_audit": 0,
        "retry": 0,
    }
    quotas.update(overrides)
    return quotas


class Task6A2VlmBudgetWiringTests(SimpleTestCase):
    def tearDown(self):
        reset_paid_provider_budget_for_tests()
        super().tearDown()

    def _image(self, directory: str, name: str = "candidate.png") -> Path:
        path = Path(directory) / name
        Image.new("RGB", (16, 16), "white").save(path)
        return path

    def _candidate(self, *, stage="base"):
        program = base_seed_programs()[0]

        @dataclass(frozen=True)
        class Source:
            metadata: dict
            volumes: tuple = ()
            surfaces: tuple = ()
            upper_footprint: object = None

            def signature(self):
                return {"formal_principle": "fixture", "family": "fixture"}

            @property
            def footprint(self):
                return Polygon(((0, 0), (1, 0), (1, 1), (0, 1)))

        return _Candidate(
            principle_id=f"{stage}-candidate",
            principle_kind="base_operative",
            operation="matrix4",
            sequence=VerbSequence(f"{stage}-candidate", "candidate", ()),
            source=Source(metadata={
                "geometry_program": program.to_dict(),
                "geometry_program_compilation": {"geometry_hash": "geometry-hash"},
                "book_generation_lineage": {"stage": stage, "parent_key": "parent"},
            }),
            feature={
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                "properties": {"height": 3.0, "source_surfaces": [], "mass_volumes": []},
            },
            score=0.5,
        )

    def _passing_score(self):
        return {
            "concept_scores": {
                "gesture_clarity": 1.0, "hierarchy": 1.0,
                "non_stair_silhouette": 1.0, "void_publicness": 1.0,
                "repair_integrity": 1.0, "precedent_resonance": 1.0,
                "program_appropriateness": 1.0, "section_program_fit": 1.0,
            },
            "program_fit_hard_pass": True,
            "critic_actions": [], "geometry_edits": [],
            "reference_assessments": [], "response_id": "test", "model": "test",
        }

    def _audit_patches(self):
        return (
            patch.object(vlm_review, "materialize_source_feature_surfaces"),
            patch.object(vlm_review, "_audited_final_book_references", return_value=([], {"hard_pass": True, "accepted": []})),
            patch.object(vlm_review, "_solid_morphology_metrics", return_value={"phenotype": "compact", "pyramidal_like": False, "section_phenotype": "none"}),
            patch.object(vlm_review, "_design_concept_descriptor", return_value={"target_access_side_in_program_frame": "closed", "frontage_aligned": False}),
            patch.object(vlm_review, "_select", side_effect=lambda pool, limit, **_kwargs: list(pool)[:limit]),
        )

    def test_actual_base_and_final_audits_route_explicit_request_kinds(self):
        configure_paid_provider_budget(
            3,
            quotas=_quotas(base_candidate=1, exact_candidate=1, portfolio_board=1),
            run_metadata={"target_count": 3},
        )
        observed = []

        def scorer(**_kwargs):
            observed.append(vlm_scorer._VLM_REQUEST_KIND.get())
            return self._passing_score()

        patches = self._audit_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            vlm_review.audit_book_base_stage_with_vlm(
                [self._candidate(stage="base")], building_type="program",
                output_dir=Path("unused"), visual_directive={}, scorer=scorer,
            )
            vlm_review._audit_final_book_geometry_with_vlm(
                [self._candidate(stage="combination")], building_type="program",
                output_dir=Path("unused"), visual_directive={}, scorer=scorer,
                paid_opportunity_limit=1,
            )

        self.assertEqual(observed, ["base_candidate_vlm", "exact_candidate_vlm"])

    def test_full_default_scorer_wiring_consumes_base_then_exact_partition(self):
        configure_paid_provider_budget(
            3,
            quotas=_quotas(base_candidate=1, exact_candidate=1, portfolio_board=1),
            run_metadata={"target_count": 3},
        )

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({
                    "id": "response",
                    "output_text": json.dumps(self_payload),
                }).encode("utf-8")

        self_payload = self._passing_score()
        with TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "MAAS_FINAL_BOOK_VLM_CACHE_DIR": str(Path(directory) / "cache"),
                "MAAS_PREFERENCE_VLM_RETRIES": "0",
            },
            clear=False,
        ), patch.object(
            vlm_scorer.urllib.request,
            "urlopen",
            return_value=Response(),
        ):
            vlm_review.audit_book_base_stage_with_vlm(
                [self._candidate(stage="base")], building_type="program",
                output_dir=Path(directory) / "base", visual_directive={},
                reference_provider=lambda _program: [],
            )
            vlm_review._audit_final_book_geometry_with_vlm(
                [self._candidate(stage="combination")], building_type="program",
                output_dir=Path(directory) / "final", visual_directive={},
                reference_provider=lambda _program: [], paid_opportunity_limit=1,
            )

        snapshot = paid_provider_budget_snapshot()
        self.assertEqual(snapshot["quota_request_counts"]["base_candidate"], 1)
        self.assertEqual(snapshot["quota_request_counts"]["exact_candidate"], 1)

    def test_typed_budget_fields_survive_parallel_final_audit_evidence(self):
        candidate = self._candidate(stage="combination")

        def scorer(**_kwargs):
            raise VlmBudgetExhaustedError(
                "bounded", request_kind="exact_candidate_vlm", quota="exact_candidate"
            )

        patches = self._audit_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            accepted, gate = vlm_review._audit_final_book_geometry_with_vlm(
                [candidate], building_type="program", output_dir=Path("unused"),
                visual_directive={}, scorer=scorer, paid_opportunity_limit=1,
            )

        self.assertEqual(accepted, [])
        record = gate["call_failure_records"][0]
        self.assertEqual(record["failure_code"], "vlm_provider_budget_exhausted")
        self.assertEqual(record["budget_code"], "provider_quota_exhausted")
        self.assertEqual(record["request_kind"], "exact_candidate_vlm")
        self.assertEqual(record["quota"], "exact_candidate")
        self.assertLessEqual(len(record["error"]), 500)

    def test_parallel_partition_consumption_never_exceeds_quota(self):
        configure_paid_provider_budget(2, quotas=_quotas(exact_candidate=2))
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(reserve_paid_provider_request, "exact_candidate_vlm")
                for _ in range(12)
            ]
            outcomes = []
            for future in futures:
                try:
                    future.result()
                    outcomes.append("reserved")
                except Exception:
                    outcomes.append("exhausted")

        self.assertEqual(outcomes.count("reserved"), 2)
        self.assertEqual(
            paid_provider_budget_snapshot()["quota_request_counts"]["exact_candidate"],
            2,
        )

    def test_explicit_base_and_exact_request_kinds_route_to_separate_quotas(self):
        configure_paid_provider_budget(
            2,
            quotas=_quotas(base_candidate=1, exact_candidate=1),
        )
        with TemporaryDirectory() as directory, patch.dict(
            os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False
        ), patch.object(
            vlm_scorer.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("offline"),
        ):
            for kind in ("base_candidate_vlm", "exact_candidate_vlm"):
                with self.assertRaises(vlm_scorer.VlmScoringError):
                    score_candidate_with_openai_vlm(
                        feature={"properties": {}},
                        image_path=self._image(directory, f"{kind}.png"),
                        request_kind=kind,
                        max_retries=0,
                    )

        snapshot = paid_provider_budget_snapshot()
        self.assertEqual(snapshot["quota_request_counts"]["base_candidate"], 1)
        self.assertEqual(snapshot["quota_request_counts"]["exact_candidate"], 1)

    def test_retry_uses_retry_quota_and_cannot_steal_exact_acceptance(self):
        configure_paid_provider_budget(
            1,
            quotas=_quotas(exact_candidate=1),
        )
        with TemporaryDirectory() as directory, patch.dict(
            os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False
        ), patch.object(
            vlm_scorer.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("offline"),
        ):
            with self.assertRaises(VlmBudgetExhaustedError) as raised:
                score_candidate_with_openai_vlm(
                    feature={"properties": {}},
                    image_path=self._image(directory),
                    request_kind="exact_candidate_vlm",
                    max_retries=1,
                )

        self.assertEqual(raised.exception.code, "provider_quota_exhausted")
        self.assertEqual(raised.exception.quota, "retry")
        snapshot = paid_provider_budget_snapshot()
        self.assertEqual(snapshot["quota_request_counts"]["exact_candidate"], 1)
        self.assertEqual(snapshot["quota_request_counts"]["retry"], 0)

    def test_reference_cache_miss_has_typed_reference_budget_failure(self):
        configure_paid_provider_budget(1, quotas=_quotas(portfolio_board=1))
        with TemporaryDirectory() as directory, patch.dict(
            os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False
        ):
            with self.assertRaises(VlmBudgetExhaustedError) as raised:
                audit_reference_image_for_massing(
                    self._image(directory, "reference.png"),
                    max_retries=0,
                )

        self.assertEqual(raised.exception.code, "provider_quota_exhausted")
        self.assertEqual(raised.exception.quota, "reference_audit")
        self.assertEqual(paid_provider_budget_snapshot()["request_count"], 0)

    def test_initial_exact_cap_is_six_and_repair_uses_remaining_exact_quota(self):
        candidate = object()
        repaired = object()
        configure_paid_provider_budget(
            10,
            quotas=_quotas(exact_candidate=9, portfolio_board=1),
            run_metadata={"target_count": 3},
        )
        with (
            patch.object(final_vlm_cycle, "_bounded_visual_selection_pool", side_effect=lambda items: list(items)),
            patch.object(final_vlm_cycle, "route_capacity_target_hard_passes", side_effect=lambda items, **_: (list(items), {"status": "pass"})),
            patch.object(
                final_vlm_cycle,
                "_audit_final_book_geometry_with_vlm",
                side_effect=[([candidate], {"audit_records": []}), ([repaired], {"audit_records": []})],
            ) as audit,
            patch.object(final_vlm_cycle, "_repair_exact_post_book_candidates_from_vlm", return_value=([repaired], {})),
            patch.object(final_vlm_cycle, "evaluate_accepted_sources_downstream", return_value={"rows": [{"combined_hard_pass": True}]}),
        ):
            final_vlm_cycle.run_final_vlm_cycle(
                [candidate], retained_hard_passes=[], building_type="program",
                output_dir=Path("unused"), visual_directive={}, outcome_graph=object(),
                program_slug="test", generation_site=object(), height=12.0, floors=4,
                generation_context=object(), program_dimensional_context={},
                site_boundary_source="test", site_access_context={}, site_access_geometry={},
                base_capacity_contract={}, downstream_context={},
                hard_gate_summary=lambda report, pool: {"candidate_count": len(pool)},
                completion_status="complete", no_repair_status="no_repair",
            )

        self.assertEqual(audit.call_args_list[0].kwargs["request_kind"], "exact_candidate_vlm")
        self.assertEqual(audit.call_args_list[0].kwargs["paid_opportunity_limit"], 6)
        self.assertEqual(audit.call_args_list[1].kwargs["request_kind"], "exact_candidate_vlm")
        self.assertEqual(audit.call_args_list[1].kwargs["paid_opportunity_limit"], 9)

    def test_retained_replenishment_initial_lane_remains_two_target(self):
        candidate = object()
        retained = object()
        configure_paid_provider_budget(
            10, quotas=_quotas(exact_candidate=9, portfolio_board=1),
            run_metadata={"target_count": 3},
        )
        with (
            patch.object(final_vlm_cycle, "_bounded_visual_selection_pool", side_effect=lambda items: list(items)),
            patch.object(final_vlm_cycle, "route_capacity_target_hard_passes", side_effect=lambda items, **_: (list(items), {"status": "pass"})),
            patch.object(final_vlm_cycle, "_audit_final_book_geometry_with_vlm", return_value=([], {"audit_records": []})) as audit,
            patch.object(final_vlm_cycle, "_repair_exact_post_book_candidates_from_vlm", return_value=([], {})),
        ):
            result = final_vlm_cycle.run_final_vlm_cycle(
                [candidate], retained_hard_passes=[retained], building_type="program",
                output_dir=Path("unused"), visual_directive={}, outcome_graph=object(),
                program_slug="test", generation_site=object(), height=12.0, floors=4,
                generation_context=None, program_dimensional_context={},
                site_boundary_source="test", site_access_context={}, site_access_geometry={},
                base_capacity_contract={}, downstream_context={},
                hard_gate_summary=lambda report, pool: {"candidate_count": len(pool)},
                completion_status="complete", no_repair_status="no_repair",
            )

        self.assertEqual(audit.call_args.kwargs["paid_opportunity_limit"], 6)
        self.assertEqual(result.selection_pool, [retained])

    def test_final_cycle_excludes_failed_initial_and_failed_second_vlm_repair(self):
        passed = object()
        failed = object()
        repaired = object()
        initial_gate = {
            "audit_records": [{
                "source_sequence": "failed",
                "hard_pass": False,
                "geometry_edits": [{"operation": "set_parameter"}],
            }],
        }
        with (
            patch.object(final_vlm_cycle, "_bounded_visual_selection_pool", side_effect=lambda items: list(items)),
            patch.object(final_vlm_cycle, "route_capacity_target_hard_passes", side_effect=lambda items, **_: (list(items), {"status": "pass"})),
            patch.object(
                final_vlm_cycle,
                "_audit_final_book_geometry_with_vlm",
                side_effect=[([passed], initial_gate), ([], {"audit_records": []})],
            ),
            patch.object(
                final_vlm_cycle,
                "_repair_exact_post_book_candidates_from_vlm",
                return_value=([repaired], {"repaired_candidate_count": 1}),
            ),
            patch.object(
                final_vlm_cycle,
                "evaluate_accepted_sources_downstream",
                return_value={"rows": [{"combined_hard_pass": True}]},
            ),
        ):
            result = final_vlm_cycle.run_final_vlm_cycle(
                [passed, failed], retained_hard_passes=[], building_type="program",
                output_dir=Path("unused"), visual_directive={}, outcome_graph=object(),
                program_slug="test", generation_site=object(), height=12.0, floors=4,
                generation_context=object(), program_dimensional_context={},
                site_boundary_source="test", site_access_context={}, site_access_geometry={},
                base_capacity_contract={}, downstream_context={}, target_count=3,
                hard_gate_summary=lambda report, pool: {"candidate_count": len(pool)},
                completion_status="complete", no_repair_status="no_repair",
            )

        self.assertEqual(result.initial_vlm_passes, [passed])
        self.assertEqual(result.repair_pool, [repaired])
        self.assertEqual(result.repair_vlm_passes, [])
        self.assertEqual(result.selection_pool, [passed])

    def test_progressive_lifecycle_restores_ledger_and_environment_on_success_and_error(self):
        original_limit = os.environ.get("MAAS_PAID_PROVIDER_MAX_REQUESTS")
        original_timeout = os.environ.get("MAAS_MASS_RUN_TIMEOUT_SECONDS")
        original_live_limit = os.environ.get("MAAS_LIVE_VLM_MAX_REQUESTS")

        class Owner:
            pass

        with patch.object(vlm_scorer, "_LIVE_VLM_REQUEST_COUNT", 7):
            self._assert_lifecycle_restoration(
                original_limit,
                original_timeout,
                original_live_limit,
            )

    def _assert_lifecycle_restoration(self, original_limit, original_timeout, original_live_limit):
        class Owner:
            pass

        for target, provider_limit, live_limit in ((3, 15, 13), (10, 43, 39), (20, 76, 69)):
            for failure in (None, RuntimeError("boom")):
                @_progressive_provider_budget_lifecycle
                def operation(_self, **_options):
                    snapshot = paid_provider_budget_snapshot()
                    self.assertEqual(snapshot["limit"], provider_limit)
                    self.assertEqual(snapshot["quota_limits"]["portfolio_board"], 1)
                    self.assertEqual(os.environ["MAAS_PAID_PROVIDER_MAX_REQUESTS"], str(provider_limit))
                    self.assertEqual(os.environ["MAAS_LIVE_VLM_MAX_REQUESTS"], str(live_limit))
                    self.assertEqual(vlm_scorer._LIVE_VLM_REQUEST_COUNT, 0)
                    if failure:
                        raise failure
                    return "ok"

                if failure:
                    with self.assertRaises(RuntimeError):
                        operation(Owner(), progressive_target=target)
                else:
                    self.assertEqual(operation(Owner(), progressive_target=target), "ok")
                self.assertNotIn("quota_limits", paid_provider_budget_snapshot())
                self.assertEqual(os.environ.get("MAAS_PAID_PROVIDER_MAX_REQUESTS"), original_limit)
                self.assertEqual(os.environ.get("MAAS_MASS_RUN_TIMEOUT_SECONDS"), original_timeout)
                self.assertEqual(os.environ.get("MAAS_LIVE_VLM_MAX_REQUESTS"), original_live_limit)
                self.assertEqual(vlm_scorer._LIVE_VLM_REQUEST_COUNT, 7)
