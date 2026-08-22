from django.test import SimpleTestCase
from unittest.mock import patch

from design.maas.book_language import candidate_generation
from design.maas.book_language.candidate_generation import (
    _MaterializationAttemptDiagnostics,
)
from design.test_maas_floorwise_candidate_rejection import _slab_fallback_case


class MaterializationCountMetadataTest(SimpleTestCase):
    def test_program_pool_reports_failure_then_success_across_evaluations(self):
        source, _program, legal_section, _sequence, _context = (
            _slab_fallback_case()
        )
        floor_context = {
            "hard_pass": True,
            "height_m": 16.0,
            "floors": 4,
            "legal_sections": (legal_section,) * 4,
            "floor_top_heights_m": (4.0, 8.0, 12.0, 16.0),
            "upper_legal_section": legal_section,
            "authority": "focused_count_integration_test",
            "legal_floor_field_hash": "focused-count-field",
        }
        attempts = 0

        def fail_then_succeed(*_args, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                kwargs["legal_fit_failure_sink"].extend([
                    {"typed_reasons": ["floor_affine_miss", "area_shortfall"]},
                    {"typed_reasons": ["area_shortfall"]},
                ])
                kwargs["terminal_failure_sink"].append({
                    "stage": "floor_affine_fit",
                    "evidence": {"hard_pass": False},
                })
                return None
            return source

        with (
            patch.object(
                candidate_generation,
                "compile_sequence_to_source_mass",
                return_value=source,
            ),
            patch.object(
                candidate_generation,
                "_candidate_floor_context",
                return_value=floor_context,
            ),
            patch.object(
                candidate_generation,
                "_materialize_directed_geometry",
                side_effect=fail_then_succeed,
            ),
        ):
            _candidates, report = candidate_generation._program_pool(
                legal_section,
                "gymnasium",
                16.0,
                4,
                recursive_only=True,
                parent_variant_indices=(0,),
                diagnostic_evaluation_cap=2,
                diagnostic_candidate_cap=2,
            )

        self.assertEqual(report["materialization_invocation_count"], 2)
        self.assertEqual(report["terminal_materialization_failure_count"], 1)
        self.assertEqual(
            sum(
                report[
                    "terminal_materialization_failure_reason_counts"
                ].values()
            ),
            1,
        )
        self.assertEqual(
            report["terminal_materialization_failure_reason_counts"],
            {"floor_affine_fit": 1},
        )
        self.assertEqual(
            report["legal_fit_failure_reason_counts"],
            {"area_shortfall": 2, "floor_affine_miss": 1},
        )
        self.assertEqual(
            report["legal_fit_failure_count_unit"],
            "deficit_reason_event",
        )
        self.assertEqual(
            report["terminal_materialization_failure_count_unit"],
            "failed_materialization_invocation",
        )
        self.assertNotIn(
            "floor_affine_miss",
            report["terminal_materialization_failure_reason_counts"],
        )

    def test_multiple_legal_deficits_remain_reason_events_for_one_invocation(self):
        diagnostics = _MaterializationAttemptDiagnostics()

        diagnostics.record_invocation(
            materialized=object(),
            terminal_failures=(),
        )
        metadata = diagnostics.metadata([
            {"typed_reasons": ["floor_area_shortfall", "floor_area_shortfall"]},
            {"typed_reasons": ["legal_section_miss"]},
        ])

        self.assertEqual(metadata["materialization_invocation_count"], 1)
        self.assertEqual(metadata["terminal_materialization_failure_count"], 0)
        self.assertEqual(
            metadata["legal_fit_failure_reason_counts"],
            {"floor_area_shortfall": 2, "legal_section_miss": 1},
        )
        self.assertEqual(
            metadata["legal_fit_failure_count_unit"],
            "deficit_reason_event",
        )

    def test_separate_failure_and_success_attempts_are_counted_once_each(self):
        diagnostics = _MaterializationAttemptDiagnostics()

        diagnostics.record_invocation(
            materialized=None,
            terminal_failures=({"stage": "floor_affine_fit"},),
        )
        diagnostics.record_invocation(
            materialized=object(),
            terminal_failures=(),
        )
        metadata = diagnostics.metadata([])

        self.assertEqual(metadata["materialization_invocation_count"], 2)
        self.assertEqual(metadata["terminal_materialization_failure_count"], 1)
        self.assertEqual(
            metadata["terminal_materialization_failure_reason_counts"],
            {"floor_affine_fit": 1},
        )
        self.assertEqual(
            metadata["terminal_materialization_failure_count_unit"],
            "failed_materialization_invocation",
        )

    def test_terminal_failure_and_summary_invariants_are_consistent(self):
        diagnostics = _MaterializationAttemptDiagnostics()

        diagnostics.record_invocation(
            materialized=None,
            terminal_failures=({"stage": "book_projection"},),
        )
        diagnostics.record_invocation(
            materialized=None,
            terminal_failures=(),
        )
        metadata = diagnostics.metadata([])

        terminal_reasons = metadata[
            "terminal_materialization_failure_reason_counts"
        ]
        self.assertEqual(
            metadata["terminal_materialization_failure_count"],
            sum(terminal_reasons.values()),
        )
        self.assertLessEqual(
            metadata["terminal_materialization_failure_count"],
            metadata["materialization_invocation_count"],
        )
        self.assertEqual(
            terminal_reasons,
            {
                "book_projection": 1,
                "unclassified_terminal_materialization_failure": 1,
            },
        )
