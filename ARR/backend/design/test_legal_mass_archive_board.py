from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy

from django.test import SimpleTestCase

from design.maas.book_language.legal_mass_archive_board import (
    render_legal_mass_archive_board,
)
from design.maas.book_language.legal_mass_archive import (
    _final_surface_payload_hash,
)


class LegalMassArchiveBoardTests(SimpleTestCase):
    def _record(self, index: int) -> dict:
        offset = float(index * 4)
        surfaces = [
            {
                "role": "certified_final_mesh",
                "volume_role": "certified_final_mesh",
                "verb": "geometry_program",
                "surface_type": "profiled_final_mesh",
                "operator": "extrude",
                "semantic_patch_id": f"archive-{index}-{face}",
                "vertices_m": vertices,
            }
            for face, vertices in enumerate((
                [[offset, 0.0, 0.0], [offset + 3.0, 0.0, 0.0], [offset, 2.0, 0.0]],
                [[offset, 0.0, 0.0], [offset + 3.0, 0.0, 0.0], [offset + 1.0, 0.7, 6.0]],
                [[offset + 3.0, 0.0, 0.0], [offset, 2.0, 0.0], [offset + 1.0, 0.7, 6.0]],
                [[offset, 2.0, 0.0], [offset, 0.0, 0.0], [offset + 1.0, 0.7, 6.0]],
            ))
        ]
        return {
            "geometry_hash": f"geometry-{index}",
            "program_hash": f"program-{index}",
            "final_surface_payload_hash": _final_surface_payload_hash(surfaces),
            "final_authored_surface_payload": surfaces,
            "policy_evidence": {"legal_hard_pass": True},
            "capacity_evidence": {
                "feasible_capacity_utilization": 0.68 + index * 0.01,
                "capacity_objective_status": "below",
                "parking_status": "pass",
                "vlm_status": "reviewed",
            },
            "scope": {"base_volume_label": "mid-rise"},
            "family": "stepped-courtyard",
            "lineage": {"stage": "base"},
            "selection_evidence": {
                "non_selection_reason": "not selected by final VLM diversity ranking",
            },
        }

    def test_zero_selected_result_renders_every_legal_archive_record(self):
        records = [self._record(index) for index in range(1, 4)]

        with TemporaryDirectory() as temporary_directory:
            evidence = render_legal_mass_archive_board(
                output_dir=Path(temporary_directory),
                program_slug="housing",
                target_count=5,
                selected_count=0,
                archive_records=records,
            )

            self.assertEqual(evidence["card_count"], 3)
            self.assertTrue(
                Path(evidence["png_path"]).is_file(),
            )
            self.assertEqual(
                Path(evidence["png_path"]).name,
                "maas-book-housing-5-legal-archive.png",
            )
            self.assertRegex(evidence["png_sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(evidence["visible_mass_pixel_ratio"], 0.0)
            self.assertEqual(
                [card["geometry_hash"] for card in evidence["cards"]],
                ["geometry-1", "geometry-2", "geometry-3"],
            )
            for card in evidence["cards"]:
                self.assertGreater(card["visible_mass_pixel_ratio"], 0.0)
                self.assertGreater(card["visible_mass_pixels"], 0)
                self.assertEqual(card["capacity_status"], "below")
                self.assertEqual(card["parking_status"], "pass")
                self.assertEqual(card["vlm_status"], "reviewed")
                self.assertEqual(
                    card["non_selection_reason"],
                    "not selected by final VLM diversity ranking",
                )

    def test_summary_and_attach_render_nonempty_archive_for_normal_zero_of_five(self):
        from design.maas.book_language.portfolio_benchmark import (
            _legal_mass_archive_portfolio_summary,
            attach_legal_mass_archive_boards,
        )

        records = [self._record(index) for index in range(1, 4)]
        program_results = [{
            "slug": "housing",
            "selected_count": 0,
            "portfolio_requirement": {"target_count": 5},
            "counts": {
                "legal_mass_archive": {
                    "record_count": 3,
                    "records": records,
                },
            },
        }]
        summary = _legal_mass_archive_portfolio_summary(program_results)
        result = {"programs": program_results, "legal_mass_archive": summary}

        with TemporaryDirectory() as temporary_directory:
            attached = attach_legal_mass_archive_boards(
                result,
                output_dir=Path(temporary_directory),
            )

        self.assertEqual(summary["record_count"], 3)
        self.assertEqual(attached["legal_mass_archive"]["boards"]["housing"]["card_count"], 3)
        self.assertEqual(attached["legal_mass_archive"]["boards"]["housing"]["selected_count"], 0)
        self.assertEqual(attached["legal_mass_archive"]["boards"]["housing"]["target_count"], 5)

    def test_hash_mismatch_fails_before_writing_board(self):
        record = self._record(1)
        record["final_surface_payload_hash"] = "0" * 64

        with TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            with self.assertRaisesRegex(ValueError, "payload hash mismatch"):
                render_legal_mass_archive_board(
                    output_dir=output_dir,
                    program_slug="housing",
                    target_count=5,
                    selected_count=0,
                    archive_records=[record],
                )
            self.assertEqual(list(output_dir.glob("*.png")), [])

    def test_vertical_exact_surface_renders_without_synthetic_footprint(self):
        record = self._record(1)
        record["final_authored_surface_payload"] = [{
            **deepcopy(record["final_authored_surface_payload"][0]),
            "vertices_m": [
                [0.0, 0.0, 0.0],
                [0.0, 2.0, 0.0],
                [0.0, 1.0, 6.0],
            ],
        }]
        record["final_surface_payload_hash"] = _final_surface_payload_hash(
            record["final_authored_surface_payload"]
        )

        with TemporaryDirectory() as temporary_directory:
            evidence = render_legal_mass_archive_board(
                output_dir=Path(temporary_directory),
                program_slug="housing",
                target_count=5,
                selected_count=0,
                archive_records=[record],
            )

        self.assertEqual(evidence["cards"][0]["source_surface_count"], 1)
        self.assertGreater(evidence["cards"][0]["visible_mass_pixels"], 0)

    def test_publishable_benchmark_keeps_capacity_objectives_diagnostic(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )
        from design.test_maas_book_language import MaasBookLanguageRegistryTest

        summary = MaasBookLanguageRegistryTest._publishable_twenty_fixture()
        rows = summary["programs"][0]["rows"]
        for row in rows:
            row["resolved_capacity_hard_pass"] = False
            row["resolved_capacity_alternative_id"] = "spatial_reserve"
        rows[0]["parking_hard_gate"]["hard_pass"] = False
        rows[0]["law_graph_evidence_hard_pass"] = False

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=(
                MaasBookLanguageRegistryTest._publishable_phase_timings()
            ),
        )
        codes = {
            deficit["code"]
            for deficit in evidence["typed_failure_deficits"]
        }
        objective = evidence["programs"][0]["quota_evidence"][
            "capacity_band_objective"
        ]

        self.assertNotIn("quota.capacity_band_exact_counts", codes)
        self.assertNotIn("hard_gate.resolved_capacity_hard_pass_not_pass", codes)
        self.assertFalse(objective["objective_met"])
        self.assertEqual(objective["hard_gate_effect"], "none_diagnostic_only")
        self.assertIn("hard_gate.parking_graph_rule_not_pass", codes)
        self.assertIn("hard_gate.law_graph_not_pass", codes)

    def test_capacity_only_combined_failure_has_no_hard_deficit_and_board_attaches(self):
        from design.maas.book_language.portfolio_benchmark import (
            _legal_mass_archive_portfolio_summary,
            attach_legal_mass_archive_boards,
        )
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )
        from design.test_maas_book_language import MaasBookLanguageRegistryTest

        summary = MaasBookLanguageRegistryTest._publishable_twenty_fixture()
        baseline_evidence = build_publishable_20_manifest_evidence(
            deepcopy(summary),
            phase_durations_seconds=(
                MaasBookLanguageRegistryTest._publishable_phase_timings()
            ),
        )
        program = summary["programs"][0]
        program["status"] = "fail"
        program["portfolio_completion"] = {
            "hard_pass": False,
            "failures": ["resolved_capacity_hard_pass_false"],
        }
        program["downstream_hard_gate"] = {
            "status": "fail",
            "failures": ["capacity_hard_gate_failed"],
        }
        for row in program["rows"]:
            row["resolved_capacity_hard_pass"] = False
            row["combined_hard_pass"] = False
            row["law_graph_evidence_hard_pass"] = True
            row["legal_projection"] = {
                "evaluated": True,
                "hard_pass": True,
                "status": "pass",
            }
            row["parking_hard_gate"]["evaluated"] = True
            row["parking_hard_gate"]["hard_pass"] = True
            row["parking_hard_gate"]["graph_status"] = "available"
        archive_records = [self._record(index) for index in range(1, 4)]
        program["portfolio_requirement"] = {"target_count": 20}
        program["counts"]["legal_mass_archive"] = {
            "record_count": len(archive_records),
            "records": archive_records,
        }
        summary["legal_mass_archive"] = _legal_mass_archive_portfolio_summary(
            summary["programs"]
        )

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=(
                MaasBookLanguageRegistryTest._publishable_phase_timings()
            ),
        )
        hard_deficits = [
            deficit
            for deficit in evidence["typed_failure_deficits"]
            if str(deficit["code"]).startswith("hard_gate.")
        ]
        with TemporaryDirectory() as temporary_directory:
            attached = attach_legal_mass_archive_boards(
                summary,
                output_dir=Path(temporary_directory),
            )

        self.assertEqual(hard_deficits, [])
        self.assertEqual(
            evidence["typed_failure_deficits"],
            baseline_evidence["typed_failure_deficits"],
        )
        self.assertEqual(
            attached["legal_mass_archive"]["boards"]["neighborhood"]["card_count"],
            3,
        )
