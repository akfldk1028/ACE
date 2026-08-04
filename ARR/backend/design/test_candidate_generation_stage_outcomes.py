from django.test import SimpleTestCase

from design.maas.book_language import candidate_generation
from design.maas.book_language.stage_outcome import (
    StageOutcome,
    record_stage_outcome,
)


class StageOutcomeInvariantTests(SimpleTestCase):
    def test_frozen_outcome_invariants(self):
        passed = StageOutcome.passed("book_projection", evidence={"status": "materialized"})
        diagnostic = StageOutcome.diagnostic(
            "program_review",
            "development_review_only",
            evidence={"development_review_eligible": True},
            value={"candidate": "retained"},
        )
        failed = StageOutcome.failed(
            "site_containment",
            "containment_failed",
            evidence={"contained": False},
        )

        self.assertEqual(passed.kind, "passed")
        self.assertEqual(diagnostic.kind, "diagnostic")
        self.assertEqual(failed.kind, "failed")
        with self.assertRaises(ValueError):
            StageOutcome.failed("clean_mass", "", evidence={"hard_pass": False})
        with self.assertRaises(ValueError):
            StageOutcome.passed("clean_mass", evidence={})
        with self.assertRaises(AttributeError):
            passed.kind = "failed"

    def test_one_recorder_updates_counters_once_and_only_failures_are_terminal(self):
        records = []
        terminals = []
        counters = {"projection_failed": 0, "projection_materialized": 0}

        record_stage_outcome(
            StageOutcome.failed(
                "book_projection",
                "book_projection_failed",
                evidence={"status": "failed"},
            ),
            records=records,
            counter_updates=((counters, "projection_failed"),),
            terminal_recorder=terminals.append,
        )
        record_stage_outcome(
            StageOutcome.passed(
                "book_projection",
                evidence={"status": "materialized"},
            ),
            records=records,
            counter_updates=((counters, "projection_materialized"),),
            terminal_recorder=terminals.append,
        )
        record_stage_outcome(
            StageOutcome.diagnostic(
                "program_review",
                "development_review_only",
                evidence={"development_review_eligible": True},
            ),
            records=records,
            terminal_recorder=terminals.append,
        )

        self.assertEqual(counters, {
            "projection_failed": 1,
            "projection_materialized": 1,
        })
        self.assertEqual([record["kind"] for record in records], [
            "failed", "passed", "diagnostic",
        ])
        self.assertEqual(len(terminals), 1)
        self.assertEqual(terminals[0].reason, "book_projection_failed")

    def test_failed_outcome_cannot_be_recorded_silently(self):
        with self.assertRaises(ValueError):
            record_stage_outcome(
                StageOutcome.failed(
                    "legal_archive",
                    "missing_projection_certificate",
                    evidence={"archive_admitted": False},
                ),
                records=[],
            )

    def test_candidate_recorder_persists_one_failed_terminal_and_counter(self):
        outcomes = []
        terminals = []
        counters = {"containment_failed": 0}

        candidate_generation._record_generation_stage_outcome(
            StageOutcome.failed(
                "site_containment",
                "containment_failed",
                evidence={"contained": False},
            ),
            stage_outcomes=outcomes,
            terminal_records=terminals,
            outcome_graph=None,
            program_slug="neighborhood",
            source_seed="seed",
            program={},
            principle_id="book:operative:test",
            book_scope="1/1",
            legal_floor_field_hash="field",
            counter_updates=((counters, "containment_failed"),),
        )

        self.assertEqual(counters["containment_failed"], 1)
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(len(terminals), 1)
        self.assertEqual(terminals[0]["stage"], "site_containment")
        self.assertEqual(
            terminals[0]["evidence"]["failure_reason"],
            "containment_failed",
        )


class CandidateStageClassificationTests(SimpleTestCase):
    def test_projection_status_and_containment_have_typed_pass_and_failure(self):
        projection_failed = candidate_generation._book_projection_stage_outcome({
            "status": "failed",
            "failure_reason": "projected_compile_or_geometry_gate_failed",
        })
        projection_passed = candidate_generation._book_projection_stage_outcome({
            "status": "materialized",
        })
        containment_failed = candidate_generation._site_containment_stage_outcome(False)

        self.assertEqual(projection_failed.kind, "failed")
        self.assertEqual(
            projection_failed.reason,
            "projected_compile_or_geometry_gate_failed",
        )
        self.assertEqual(projection_passed.kind, "passed")
        self.assertEqual(containment_failed.kind, "failed")

    def test_archive_none_is_failed_and_archive_record_is_passed(self):
        failed = candidate_generation._legal_archive_stage_outcome(
            None,
            reason="projection_certificate_hash_mismatch",
            evidence={"certificate_verified": False},
        )
        passed = candidate_generation._legal_archive_stage_outcome(
            {"geometry_hash": "g"},
            reason="",
            evidence={"certificate_verified": True},
        )

        self.assertEqual(failed.kind, "failed")
        self.assertEqual(failed.reason, "projection_certificate_hash_mismatch")
        self.assertEqual(passed.kind, "passed")

    def test_program_rejection_development_and_pass_are_distinct(self):
        rejected = candidate_generation._program_review_stage_outcome({
            "selection_eligible": False,
            "development_review_eligible": False,
            "failed_design_gates": ["program_fit"],
        })
        development = candidate_generation._program_review_stage_outcome({
            "selection_eligible": False,
            "development_review_eligible": True,
            "failed_design_gates": ["program_fit"],
        })
        passed = candidate_generation._program_review_stage_outcome({
            "selection_eligible": True,
            "development_review_eligible": False,
        })

        self.assertEqual(rejected.kind, "failed")
        self.assertEqual(development.kind, "diagnostic")
        self.assertEqual(passed.kind, "passed")
