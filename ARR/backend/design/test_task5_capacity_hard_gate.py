from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from shapely.geometry import box

from design.maas.book_language import portfolio_benchmark
from design.maas.book_language.downstream_hard_gate import (
    _evaluate_candidate,
    evaluate_accepted_sources_downstream,
)
from design.maas.source_geometry.ir import SourceMass, SourceVolume
from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph


class Task5CapacityHardGateTest(TestCase):
    def _candidate(self):
        footprint = box(0.0, 0.0, 10.0, 10.0)
        source = SourceMass(
            name="stale-selectable-capacity",
            footprint=footprint,
            volumes=(
                SourceVolume(
                    "main",
                    footprint,
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            metadata={
                "capacity_alternative_projection": {
                    "alternative_id": "balanced_yield",
                    "target_utilization": 0.80,
                    "target_hard_pass": True,
                    "selectable_capacity_alternative_id": "balanced_yield",
                    "selectable_capacity_target_utilization": 0.80,
                    "selectable_capacity_hard_pass": True,
                    "feasible_minimum_utilization": 0.70,
                },
                "source_capacity_measurement": {
                    "utilization_ratio": 0.40,
                    "hard_pass": False,
                },
            },
        )
        return SimpleNamespace(
            source=source,
            feature={"properties": {"variant_id": "stale-capacity"}},
            sequence=SimpleNamespace(name="stale-capacity-sequence"),
            principle_id="book:test",
        )

    def test_capacity_and_shared_floor_miss_remain_diagnostic_for_final_vlm(self):
        candidate = self._candidate()
        envelope = SimpleNamespace(
            buildable_footprint=box(-1.0, -1.0, 11.0, 11.0),
            bcr_limit=100.0,
            far_limit=1000.0,
            height_limit=30.0,
            outputs_def=[],
        )
        payload_hash = candidate.source.signature()[
            "actual_surface_payload_hash"
        ]
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate._final_source_geometry_identity",
                return_value=("g" * 64, [], "g" * 64, payload_hash, True),
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_shared_floor_contract_hard_gate",
                return_value={
                    "hard_pass": False,
                    "failure_reasons": ["shared_floor_target_miss"],
                },
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.audit_source_semantic_projection",
                return_value={"hard_pass": True, "failures": []},
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                return_value={
                    "status": "computed",
                    "required_spaces": 0,
                    "accessible": {"accessible_min": 0},
                },
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {
                        "status": "pass",
                        "provided_spaces": 0,
                    },
                },
            ),
        ):
            row = _evaluate_candidate(
                candidate,
                site_local_utm=envelope.buildable_footprint,
                envelope=envelope,
                sunlight_ring=[],
                pnu="1168011800104170004",
                building_type="gymnasium",
                height_m=10.0,
                floors=2,
                rules={},
                parking_options={},
            )

        self.assertTrue(row["legal_projection"]["hard_pass"], row)
        self.assertTrue(row["legal_projection"]["geometry_retention_pass"], row)
        self.assertTrue(row["parking_hard_gate"]["hard_pass"], row)
        self.assertTrue(row["semantic_projection_hard_gate"]["hard_pass"], row)
        self.assertFalse(row["capacity_hard_gate"]["hard_pass"], row)
        self.assertTrue(row["combined_hard_pass"], row)
        self.assertTrue(
            row["legal_projection"]["component_evidence"][
                "statutory_law_graph"
            ]["hard_pass"]
        )
        self.assertFalse(
            row["legal_projection"]["diagnostic_evidence"][
                "shared_floor"
            ]["hard_pass"]
        )

        candidate.feature["properties"]["program_form_gate"] = {
            "hard_pass": False,
            "failures": ["over_tortuous_mass_outline"],
        }
        with patch.object(
            portfolio_benchmark,
            "_bind_final_visual_authority_for_review",
        ) as bind:
            final_vlm_input = portfolio_benchmark._final_vlm_input_from_downstream(
                [candidate],
                {"rows": [row]},
            )
        self.assertEqual(final_vlm_input, [candidate])
        bind.assert_called_once()

    def test_actual_containment_bcr_or_far_failure_remains_blocked(self):
        candidate = self._candidate()
        payload_hash = candidate.source.signature()["actual_surface_payload_hash"]
        for label, site, bcr_limit, far_limit in (
            ("containment", box(0.0, 0.0, 5.0, 5.0), 100.0, 1000.0),
            ("bcr", box(0.0, 0.0, 10.0, 10.0), 50.0, 1000.0),
            ("far", box(0.0, 0.0, 10.0, 10.0), 100.0, 50.0),
        ):
            envelope = SimpleNamespace(
                buildable_footprint=site,
                bcr_limit=bcr_limit,
                far_limit=far_limit,
                height_limit=30.0,
                outputs_def=[],
            )
            with self.subTest(label=label), patch(
                "design.maas.book_language.downstream_hard_gate._final_source_geometry_identity",
                return_value=("g" * 64, [], "g" * 64, payload_hash, True),
            ), patch(
                "design.maas.book_language.downstream_hard_gate.resolve_shared_floor_contract_hard_gate",
                return_value={"hard_pass": False, "failure_reasons": ["diagnostic"]},
            ), patch(
                "design.maas.book_language.downstream_hard_gate.audit_source_semantic_projection",
                return_value={"hard_pass": False, "failures": ["program_form"]},
            ), patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                return_value={"status": "computed", "required_spaces": 0, "accessible": {"accessible_min": 0}},
            ), patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={"layout_candidate": {"status": "pass", "provided_spaces": 0}},
            ):
                row = _evaluate_candidate(
                    candidate,
                    site_local_utm=site,
                    envelope=envelope,
                    sunlight_ring=[],
                    pnu="test",
                    building_type="gymnasium",
                    height_m=10.0,
                    floors=2,
                    rules={},
                    parking_options={},
                )
            self.assertFalse(row["legal_projection"]["hard_pass"], row)
            self.assertFalse(row["combined_hard_pass"], row)
            self.assertEqual(
                portfolio_benchmark._final_vlm_input_from_downstream(
                    [candidate], {"rows": [row]}
                ),
                [],
            )

    def test_downstream_summary_reports_capacity_passes_and_bounded_failures(self):
        failed_row = {
            "legal_projection": {
                "hard_pass": True,
                "failure_reasons": [],
                "geometry_retention_pass": True,
                "geometry_failure_reasons": [],
                "volume_retention": 1.0,
            },
            "parking_hard_gate": {"hard_pass": True, "failure_reasons": []},
            "capacity_hard_gate": {
                "hard_pass": False,
                "failure_reasons": ["resolved_capacity_hard_pass_failed"],
            },
            "semantic_projection_hard_gate": {"hard_pass": True, "failures": []},
            "combined_hard_pass": False,
        }
        site = box(0.0, 0.0, 10.0, 10.0)
        context = SimpleNamespace(
            envelope=SimpleNamespace(
                bcr_limit=100.0,
                far_limit=1000.0,
                height_limit=30.0,
                buildable_footprint=site,
            ),
            generation_site=site,
            sunlight_ring=(),
            evidence={},
        )
        dimensions = SimpleNamespace(
            height_m=10.0,
            floors=2,
            publishable=True,
            authority="test",
        )
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.build_legal_generation_context",
                return_value=context,
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.load_parking_requirement_rules",
                return_value={"status": "loaded", "rules": {}},
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate._candidate_downstream_dimensions",
                return_value=dimensions,
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate._evaluate_candidate",
                return_value=failed_row,
            ),
        ):
            report = evaluate_accepted_sources_downstream(
                [object()],
                site_local_utm=site,
                site_origin_utm=(0.0, 0.0),
                pnu="1168011800104170004",
                building_type="gymnasium",
                height_m=10.0,
                floors=2,
                constraints=[],
                regulation_evidence={},
                sunlight_envelope=None,
            )

        self.assertEqual(report["capacity_hard_pass_count"], 0)
        self.assertEqual(
            report["capacity_failure_reason_counts"],
            {"resolved_capacity_hard_pass_failed": 1},
        )

    def test_release_observation_records_typed_legal_component_causality(self):
        candidate = self._candidate()
        candidate.source.metadata["geometry_program_bridge_evidence"] = {
            "geometry_hash": "release-geometry",
            "source_seed": "release-seed",
        }
        row = {
            "legal_projection": {
                "hard_pass": True,
                "geometry_retention_pass": True,
                "volume_retention": 1.0,
                "geometry_failure_reasons": [],
                "component_evidence": {
                    "containment": {"hard_pass": True, "failure_reasons": []},
                    "structural_surface_validity": {"hard_pass": True, "failure_reasons": []},
                    "height": {"hard_pass": True, "failure_reasons": []},
                    "bcr": {"hard_pass": True, "failure_reasons": []},
                    "far": {"hard_pass": True, "failure_reasons": []},
                    "statutory_law_graph": {"hard_pass": True, "failure_reasons": []},
                },
                "diagnostic_evidence": {
                    "shared_floor": {
                        "hard_pass": False,
                        "failure_reasons": ["shared_floor_target_miss"],
                        "hard_gate": False,
                    },
                },
            },
            "parking_hard_gate": {"hard_pass": True, "failure_reasons": []},
            "capacity_hard_gate": {
                "hard_pass": False,
                "failure_reasons": ["resolved_capacity_hard_pass_failed"],
            },
            "semantic_projection_hard_gate": {
                "hard_pass": False,
                "failures": ["program_form"],
            },
            "combined_hard_pass": True,
            "release_component_evidence": {
                "program_and_capacity_are_not_release_hard_gates": True,
            },
        }
        graph = GeometryOutcomeGraph(Path("unused.json"), pnu="test")
        with patch(
            "design.maas.geometry_language.outcome_graph._source_program_identities",
            return_value=(
                {"name": "authored", "metadata": {}},
                {"name": "projected", "metadata": {}},
                {},
                {},
                "program-hash",
                "authored-hash",
                "projected-hash",
            ),
        ):
            graph.observe_candidates(
                program_slug="neighborhood",
                candidates=[candidate],
                downstream_report={"rows": [row]},
            )

        observation = graph.observations[0]
        self.assertTrue(observation["legal_hard_pass"])
        self.assertTrue(observation["combined_hard_pass"])
        self.assertEqual(
            observation["legal_component_failure_reasons"]["containment"],
            [],
        )
        self.assertEqual(
            observation["capacity_diagnostic"]["failure_reasons"],
            ["resolved_capacity_hard_pass_failed"],
        )
        self.assertEqual(
            observation["shared_floor_diagnostic"]["failure_reasons"],
            ["shared_floor_target_miss"],
        )

    def test_publish_validator_accepts_exact_all_pass_rows(self):
        validator = getattr(
            portfolio_benchmark,
            "_final_downstream_publish_failures",
            lambda rows, selected_count: ["validator_missing"],
        )
        self.assertEqual(
            validator([{"combined_hard_pass": True}], selected_count=1),
            [],
        )

    def test_publish_validator_fails_closed_on_failure_or_missing_row(self):
        validator = getattr(
            portfolio_benchmark,
            "_final_downstream_publish_failures",
            lambda rows, selected_count: ["validator_missing"],
        )
        self.assertEqual(
            validator([{"combined_hard_pass": False}], selected_count=1),
            ["final_downstream_hard_gate_failed"],
        )
        self.assertEqual(
            validator([], selected_count=1),
            ["final_downstream_cardinality_mismatch"],
        )

    def test_final_archive_row_persists_exact_downstream_authorities(self):
        persist = getattr(
            portfolio_benchmark,
            "_persist_final_downstream_authority",
            lambda row, downstream_row: None,
        )
        archive_row = {
            "capacity_alternative": {
                "selectable_capacity_hard_pass": True,
            },
        }
        downstream_row = {
            "capacity_hard_gate": {
                "hard_pass": False,
                "failure_reasons": ["resolved_capacity_hard_pass_failed"],
                "resolved_capacity_hard_pass": False,
            },
            "semantic_projection_hard_gate": {
                "hard_pass": True,
                "failures": [],
            },
            "combined_hard_pass": False,
        }

        persist(archive_row, downstream_row)

        self.assertEqual(
            archive_row["capacity_hard_gate"],
            downstream_row["capacity_hard_gate"],
        )
        self.assertIsNot(
            archive_row["capacity_hard_gate"],
            downstream_row["capacity_hard_gate"],
        )
        self.assertEqual(
            archive_row["semantic_projection_hard_gate"],
            downstream_row["semantic_projection_hard_gate"],
        )
        self.assertFalse(archive_row["combined_hard_pass"])
        self.assertFalse(
            archive_row["capacity_hard_gate"]["hard_pass"],
            "stale selectable projection must not become final authority",
        )

    def test_non_smoke_publish_seam_applies_final_downstream_failure_to_status(self):
        apply_gate = getattr(
            portfolio_benchmark,
            "_apply_final_downstream_publish_gate",
            lambda **kwargs: {
                "status": "pass",
                "failures": list(kwargs["failures"]),
            },
        )

        failed = apply_gate(
            failures=[],
            downstream_rows=[{"combined_hard_pass": False}],
            selected_count=1,
            smoke_mode=False,
        )
        missing = apply_gate(
            failures=[],
            downstream_rows=[],
            selected_count=1,
            smoke_mode=False,
        )

        self.assertEqual(failed["status"], "fail")
        self.assertIn("final_downstream_hard_gate_failed", failed["failures"])
        self.assertEqual(missing["status"], "fail")
        self.assertIn(
            "final_downstream_cardinality_mismatch",
            missing["failures"],
        )
