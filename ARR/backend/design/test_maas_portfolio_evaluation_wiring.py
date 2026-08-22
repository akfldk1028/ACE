from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from design.maas.book_language.portfolio_evaluation_bridge import (
    PortfolioEvaluationInput,
    book_candidate_evaluation_input,
    build_portfolio_evaluation_ledger,
)
from design.maas.book_language.portfolio_replenishment import (
    competition_exact_hard_pass_deficits,
)
from design.maas.book_language.portfolio_benchmark import (
    optional_book_base_review_callback,
    partition_finalizable_candidates,
    persist_book_program_summary,
    portfolio_candidate_id,
    downstream_rows_indexed_by_program_hash,
)
from design.maas.book_language.final_mesh_floor_evidence import (
    FinalMeshFloorEvidenceError,
)


def deterministic_pass_gates() -> dict[str, dict]:
    return {
        "geometry": {"hard_pass": True, "triangle_count": 48},
        "law": {"hard_pass": True, "contained": True},
        "capacity": {"hard_pass": True, "far_pct": 118.0},
        "parking": {"hard_pass": True, "provided_spaces": 3},
        "program": {"hard_pass": True, "program_id": "neighborhood"},
        "vlm": {"status": "not_requested", "evaluated": False},
        "selection": {"status": "selected"},
    }


class PortfolioEvaluationWiringTests(SimpleTestCase):
    def test_downstream_rows_use_their_own_program_hash_identity(self):
        rows = [{"final_legal_program_hash": "a" * 64, "combined_hard_pass": True}]

        indexed = downstream_rows_indexed_by_program_hash(rows)

        self.assertIs(indexed["a" * 64], rows[0])

    def test_downstream_rows_bind_ordered_candidate_identity_before_passport(self):
        rows = [{"combined_hard_pass": True}, {"combined_hard_pass": False}]

        indexed = downstream_rows_indexed_by_program_hash(
            rows,
            fallback_program_hashes=("a" * 64, "b" * 64),
        )

        self.assertIs(indexed["a" * 64], rows[0])
        self.assertIs(indexed["b" * 64], rows[1])
        self.assertNotIn("final_legal_program_hash", rows[0])

    def test_candidate_id_keeps_book_lineage_but_is_unique_per_program(self):
        first = portfolio_candidate_id("book:operative:shift", "a" * 64)
        second = portfolio_candidate_id("book:operative:shift", "b" * 64)

        self.assertEqual(first, "book:operative:shift:aaaaaaaaaaaa")
        self.assertNotEqual(first, second)

    def test_invalid_finalization_candidate_is_retained_as_rejection(self):
        def resolve(candidate):
            if candidate == "invalid":
                raise FinalMeshFloorEvidenceError(
                    "candidate_finalization_context_mismatch",
                    mismatch_fields=["pnu"],
                )
            return object()

        accepted, rejected = partition_finalizable_candidates(
            ["valid", "invalid"],
            resolver=resolve,
        )

        self.assertEqual(accepted, ["valid"])
        self.assertEqual(rejected[0][0], "invalid")
        self.assertEqual(
            rejected[0][1]["failure_code"],
            "candidate_finalization_context_mismatch",
        )

    def test_initial_breadth_deficits_accept_progressive_compile_budget(self):
        deficits = competition_exact_hard_pass_deficits(
            [],
            page_index=0,
            target_count=20,
            exact_compile_limit=None,
        )

        self.assertTrue(any(
            item["axis"] == "exact_hard_pass_reserve"
            for item in deficits
        ))

    def test_disabled_book_base_review_is_none_not_a_none_returning_lambda(self):
        callback = lambda values: (values, {"status": "reviewed"})

        self.assertIsNone(optional_book_base_review_callback(False, callback))
        self.assertEqual(
            optional_book_base_review_callback(True, callback)(["base"]),
            (["base"], {"status": "reviewed"}),
        )

    def test_summary_persistence_writes_separate_evaluation_manifest(self):
        evaluation = {
            "schema_version": "arr.maas.portfolio_evaluation_ledger.v1",
            "run_id": "book-run",
            "pnu": "1168011800104170004",
            "target_count": 1,
            "record_count": 1,
            "records": [{"candidate_id": "maas_01"}],
            "records_truncated": False,
        }
        result = {
            "schema_version": "arr.maas.book_program_portfolios.v1",
            "programs": [{
                "slug": "neighborhood",
                "portfolio_evaluation": evaluation,
            }],
        }
        with TemporaryDirectory() as temporary:
            root = Path(temporary)

            persist_book_program_summary(root, result)

            persisted = json.loads(
                (root / "maas-portfolio-evaluation.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(
            persisted["schema_version"],
            "arr.maas.portfolio_evaluation_manifest.v1",
        )
        self.assertEqual(
            persisted["programs"][0],
            {**evaluation, "program_slug": "neighborhood"},
        )

    def test_book_candidate_adapter_reads_existing_gate_authorities(self):
        metadata = {
            "program_gate_result": {
                "hard_pass": True,
                "program_id": "neighborhood",
            },
            "final_book_vlm_audit": {
                "status": "not_requested",
                "evaluated": False,
                "vlm_image_inputs": {
                    "candidate": {
                        "local_path": "renders/book-bend.png",
                    },
                },
            },
        }
        downstream_row = {
            "legal_projection": {
                "hard_pass": True,
                "geometry_retention_pass": True,
                "contained": True,
            },
            "capacity_hard_gate": {"hard_pass": True, "far_pct": 118.0},
            "parking_hard_gate": {
                "hard_pass": False,
                "failure_reasons": ["parking_count_shortfall"],
            },
            "semantic_projection_hard_gate": {"hard_pass": True},
        }

        item = book_candidate_evaluation_input(
            candidate_id="book:bend",
            program_hash="program-book",
            geometry_hash="geometry-book",
            metadata=metadata,
            downstream_row=downstream_row,
            selected=False,
            selection_reasons=("downstream_hard_gate_failed",),
            lineage={"scope_label": "3/8"},
        )

        self.assertTrue(item.gate_evidence["geometry"]["hard_pass"])
        self.assertTrue(item.gate_evidence["law"]["hard_pass"])
        self.assertFalse(item.gate_evidence["parking"]["hard_pass"])
        self.assertEqual(
            item.gate_evidence["selection"]["failure_reasons"],
            ["downstream_hard_gate_failed"],
        )
        self.assertEqual(item.preview_path, "renders/book-bend.png")

    def test_book_candidate_adapter_uses_clean_compile_before_downstream(self):
        item = book_candidate_evaluation_input(
            candidate_id="book:pre-downstream",
            program_hash="program-clean",
            geometry_hash="geometry-clean",
            metadata={
                "geometry_program_compilation": {
                    "geometry_hash": "geometry-clean",
                    "issues": [],
                },
                "program_gate_result": {
                    "hard_pass": False,
                    "failure_reasons": ["program_fit_failed"],
                },
            },
            downstream_row=None,
            selected=False,
        )

        self.assertTrue(item.gate_evidence["geometry"]["hard_pass"])
        self.assertEqual(item.gate_evidence["law"], {})
        self.assertFalse(item.gate_evidence["program"]["hard_pass"])

    def test_bridge_preserves_selected_legal_pass_and_raw_gate_evidence(self):
        gates = deterministic_pass_gates()
        original = deepcopy(gates)

        ledger = build_portfolio_evaluation_ledger(
            run_id="book-run",
            pnu="1168011800104170004",
            target_count=2,
            candidates=(PortfolioEvaluationInput(
                candidate_id="maas_01",
                program_hash="program-01",
                geometry_hash="geometry-01",
                preview_path="renders/maas_01.png",
                lineage={"book_principle_id": "book:operative:bend"},
                gate_evidence=gates,
                selected=True,
            ),),
        )

        record = ledger.evidence()["records"][0]

        self.assertEqual(record["overall_status"], "selected")
        self.assertEqual(record["stages"]["capacity"]["status"], "pass")
        self.assertEqual(
            record["stages"]["capacity"]["evidence"]["far_pct"],
            118.0,
        )
        self.assertEqual(gates, original)

    def test_bridge_retains_parking_failure_and_ordered_terminal_reasons(self):
        gates = deterministic_pass_gates()
        gates["parking"] = {
            "hard_pass": False,
            "failure_reasons": [
                "parking_count_shortfall",
                "turning_path_unverified",
            ],
        }
        gates["selection"] = {
            "status": "rejected",
            "failure_reasons": ["strict_portfolio_not_selected"],
        }

        ledger = build_portfolio_evaluation_ledger(
            run_id="book-run",
            pnu="1168011800104170004",
            target_count=2,
            candidates=(PortfolioEvaluationInput(
                candidate_id="maas_02",
                program_hash="program-02",
                geometry_hash="geometry-02",
                gate_evidence=gates,
            ),),
        )

        record = ledger.evidence()["records"][0]

        self.assertEqual(record["overall_status"], "failed")
        self.assertEqual(
            record["terminal_reasons"],
            [
                "parking_count_shortfall",
                "turning_path_unverified",
                "strict_portfolio_not_selected",
            ],
        )

    def test_absent_gate_evidence_is_not_evaluated_not_pass(self):
        ledger = build_portfolio_evaluation_ledger(
            run_id="partial-run",
            pnu="1168011800104170004",
            target_count=1,
            candidates=(PortfolioEvaluationInput(
                candidate_id="maas_partial",
                program_hash="program-partial",
                geometry_hash="geometry-partial",
                gate_evidence={
                    "geometry": {"hard_pass": True},
                    "program": {"hard_pass": True},
                },
            ),),
        )

        record = ledger.evidence()["records"][0]

        self.assertEqual(record["overall_status"], "not_evaluated")
        self.assertEqual(record["stages"]["law"]["status"], "not_evaluated")
        self.assertEqual(record["stages"]["parking"]["status"], "not_evaluated")
