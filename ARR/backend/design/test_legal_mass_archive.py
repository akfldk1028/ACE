from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.test import SimpleTestCase

from design.maas.book_language.legal_mass_archive import LegalMassArchive


class LegalMassArchiveTests(SimpleTestCase):
    _FINAL_SURFACE_PAYLOAD_HASH = (
        "6a36d2fb2e3d71c681b9d7cb77f3c901fb49068ba4755dbde397230978082257"
    )

    def _candidate(self, **overrides):
        candidate = {
            "geometry_hash": "geometry-parent",
            "program_hash": "program-parent",
            "final_authored_surface_payload": [{
                "operator": "extrude",
                "role": "final_roof",
                "semantic_patch_id": "patch-1",
                "surface_type": "triangle",
                "verb": "geometry_program",
                "vertices_m": [
                    [0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                ],
                "volume_role": "mass",
            }],
            "final_surface_payload_hash": self._FINAL_SURFACE_PAYLOAD_HASH,
            "candidate_floor_context": {
                "floor_count": 4,
                "height_m": 14.0,
            },
            "policy_evidence": {
                "compiler_clean": True,
                "contained": True,
                "authored_surface_certified": True,
                "legal_hard_pass": True,
            },
            "capacity_evidence": {
                "capacity_objective_status": "below",
                "feasible_capacity_utilization": 0.668,
                "revision_recommended": True,
            },
            "scope": {"base_volume_label": "mid-rise"},
            "family": "stepped_courtyard",
            "lineage": {
                "stage": "base",
                "fingerprint": "parent-fingerprint",
            },
        }
        candidate.update(overrides)
        return candidate

    def _generation_source(self, **metadata_overrides):
        surface = SimpleNamespace(
            operator="extrude",
            role="final_roof",
            semantic_patch_id="patch-1",
            surface_type="triangle",
            verb="geometry_program",
            vertices_m=[
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
            ],
            volume_role="mass",
        )
        metadata = {
            "final_geometry_hash": "geometry-final",
            "final_program_hash": "program-final",
            "final_surface_payload_hash": self._FINAL_SURFACE_PAYLOAD_HASH,
            "authored_legal_projection_certificate": {
                "schema_version": (
                    "arr.maas.authored_legal_projection_certificate.v1"
                ),
                "status": "verified",
                "hard_pass": True,
                "input_authored_program_hash": "program-final",
                "projected_surface_hash": "geometry-final",
                "projected_surface_payload_hash": (
                    self._FINAL_SURFACE_PAYLOAD_HASH
                ),
            },
            "legal_capacity_authority": {
                "legal_hard_pass": True,
                "capacity_objective_status": "below",
                "feasible_capacity_utilization": 0.668,
                "revision_recommended": True,
            },
            "source_capacity_measurement": {
                "feasible_capacity_utilization": 0.668,
            },
            "capacity_alternative_projection": {
                "target_hard_pass": False,
            },
            "book_scope": {"base_volume_label": "mid-rise"},
            "family": "stepped_courtyard",
            "generation_lineage": {
                "stage": "base",
                "fingerprint": "generation-parent",
            },
        }
        metadata.update(metadata_overrides)
        return SimpleNamespace(metadata=metadata, surfaces=(surface,))

    def test_legal_capacity_miss_enters_the_archive(self):
        archive = LegalMassArchive()

        record = archive.admit(self._candidate())

        self.assertIsNotNone(record)
        self.assertEqual(record["geometry_hash"], "geometry-parent")
        self.assertEqual(record["capacity_evidence"]["capacity_objective_status"], "below")
        self.assertEqual(archive.evidence()["record_count"], 1)

    def test_illegal_or_unbound_candidates_do_not_enter_the_archive(self):
        archive = LegalMassArchive()
        illegal = self._candidate(policy_evidence={
            "compiler_clean": True,
            "contained": True,
            "authored_surface_certified": True,
            "legal_hard_pass": False,
        })
        unbound = self._candidate(
            geometry_hash="geometry-unbound",
            policy_evidence={
                "compiler_clean": False,
                "contained": True,
                "authored_surface_certified": True,
                "legal_hard_pass": True,
            },
        )

        self.assertIsNone(archive.admit(illegal))
        self.assertIsNone(archive.admit(unbound))
        self.assertEqual(archive.evidence()["records"], [])

    def test_descendant_creates_a_new_record_without_overwriting_its_parent(self):
        archive = LegalMassArchive()
        parent = self._candidate()
        descendant = self._candidate(
            geometry_hash="geometry-descendant",
            program_hash="program-descendant",
            lineage={
                "stage": "combination",
                "parent_geometry_hash": "geometry-parent",
                "fingerprint": "descendant-fingerprint",
            },
        )

        archive.admit(parent)
        archive.admit(descendant)
        archive.admit({**deepcopy(parent), "family": "replacement-attempt"})

        records = archive.evidence()["records"]
        self.assertEqual([record["geometry_hash"] for record in records], [
            "geometry-parent", "geometry-descendant",
        ])
        self.assertEqual(records[0]["family"], "stepped_courtyard")
        self.assertEqual(records[1]["lineage"]["parent_geometry_hash"], "geometry-parent")

    def test_records_retain_hashes_policy_capacity_scope_family_and_lineage(self):
        archive = LegalMassArchive()
        candidate = self._candidate()

        record = archive.admit(candidate)
        candidate["scope"]["base_volume_label"] = "mutated"
        candidate["lineage"]["fingerprint"] = "mutated"
        candidate["final_authored_surface_payload"][0]["vertices_m"][0][0] = 99.0

        self.assertEqual(record["program_hash"], "program-parent")
        self.assertEqual(record["policy_evidence"]["legal_hard_pass"], True)
        self.assertEqual(record["capacity_evidence"]["feasible_capacity_utilization"], 0.668)
        self.assertEqual(record["scope"]["base_volume_label"], "mid-rise")
        self.assertEqual(record["family"], "stepped_courtyard")
        self.assertEqual(record["lineage"]["fingerprint"], "parent-fingerprint")
        self.assertEqual(
            record["final_surface_payload_hash"],
            self._FINAL_SURFACE_PAYLOAD_HASH,
        )
        self.assertEqual(
            record["final_authored_surface_payload"][0]["vertices_m"][0],
            [0.0, 0.0, 0.0],
        )

    def test_generation_boundary_archives_legal_capacity_miss_after_real_gates(self):
        from design.maas.book_language.candidate_generation import (
            _admit_legal_mass_candidate,
        )

        archive = LegalMassArchive()
        source = self._generation_source()
        record = _admit_legal_mass_candidate(
            archive,
            source,
            compiler_clean_passed=True,
            site_containment_passed=True,
        )
        source.surfaces[0].vertices_m[0][0] = 99.0

        self.assertIsNotNone(record)
        self.assertEqual(record["geometry_hash"], "geometry-final")
        self.assertEqual(
            record["capacity_evidence"]["legal_capacity_authority"][
                "capacity_objective_status"
            ],
            "below",
        )
        self.assertEqual(
            record["final_surface_payload_hash"],
            self._FINAL_SURFACE_PAYLOAD_HASH,
        )
        self.assertEqual(
            record["final_authored_surface_payload"][0]["vertices_m"][0],
            [0.0, 0.0, 0.0],
        )
        self.assertEqual(
            archive.evidence()["records"][0][
                "final_authored_surface_payload"
            ][0]["vertices_m"][0],
            [0.0, 0.0, 0.0],
        )

    def test_generation_archive_uses_physical_metric_surface_payload(self):
        from design.maas.book_language.candidate_generation import (
            _admit_legal_mass_candidate,
        )
        from design.maas.geometry_language.source_bridge import (
            source_surface_payload_hash,
        )

        source = self._generation_source()
        source.surfaces[0].surface_type = "profiled_recursive_solid_mesh"
        source.surfaces[0].vertices_m[2][2] = 1.0
        normalized_hash = source_surface_payload_hash(source.surfaces)
        source.metadata["candidate_floor_context"] = {
            "floor_count": 4,
            "height_m": 14.0,
        }
        source.metadata["final_surface_payload_hash"] = normalized_hash
        source.metadata["authored_legal_projection_certificate"][
            "projected_surface_payload_hash"
        ] = normalized_hash
        record = _admit_legal_mass_candidate(
            LegalMassArchive(),
            source,
            compiler_clean_passed=True,
            site_containment_passed=True,
        )

        self.assertIsNotNone(record)
        z_values = [
            float(vertex[2])
            for triangle in record["final_authored_surface_payload"]
            for vertex in triangle["vertices_m"]
        ]
        self.assertEqual(max(z_values) - min(z_values), 14.0)
        self.assertNotEqual(
            record["final_surface_payload_hash"],
            normalized_hash,
        )
        self.assertEqual(
            record["normalized_source_surface_payload_hash"],
            normalized_hash,
        )

    def test_missing_legacy_target_hard_pass_remains_diagnostic_after_archive(self):
        from collections import Counter

        from design.maas.book_language.candidate_generation import (
            _admit_legal_mass_candidate,
            _record_capacity_projection_diagnostics,
        )

        source = self._generation_source(capacity_alternative_projection={
            "capacity_objective_status": "below",
            "revision_recommended": True,
        })
        archive = LegalMassArchive()
        record = _admit_legal_mass_candidate(
            archive,
            source,
            compiler_clean_passed=True,
            site_containment_passed=True,
        )
        counts = Counter()

        diagnostic = _record_capacity_projection_diagnostics(
            counts,
            alternative_id="measured-current-schema",
            metadata=source.metadata,
        )

        self.assertIsNotNone(record)
        self.assertEqual(archive.evidence()["record_count"], 1)
        self.assertEqual(diagnostic["capacity_objective_status"], "below")
        self.assertTrue(diagnostic["revision_recommended"])
        self.assertFalse(diagnostic["hard_gate"])
        self.assertEqual(
            counts[
                "alternative:measured-current-schema:capacity_revision_recommended"
            ],
            1,
        )

    def test_generation_boundary_rejects_failed_gate_or_stale_surface_authority(self):
        from design.maas.book_language.candidate_generation import (
            _admit_legal_mass_candidate,
        )

        stale_certificate = deepcopy(
            self._generation_source().metadata[
                "authored_legal_projection_certificate"
            ]
        )
        stale_certificate["projected_surface_payload_hash"] = "stale-surface"
        mismatched_surface_source = self._generation_source()
        mismatched_surface_source.surfaces[0].vertices_m[0][0] = 2.0
        cases = (
            (self._generation_source(), False, True),
            (self._generation_source(), True, False),
            (
                self._generation_source(
                    authored_legal_projection_certificate=stale_certificate,
                    geometry_program_bridge_evidence={
                        "geometry_authority": "authored_projected_surface_payload",
                    },
                ),
                True,
                True,
            ),
            (mismatched_surface_source, True, True),
        )

        for source, compiler_clean_passed, site_containment_passed in cases:
            with self.subTest(
                compiler_clean_passed=compiler_clean_passed,
                site_containment_passed=site_containment_passed,
            ):
                archive = LegalMassArchive()
                self.assertIsNone(_admit_legal_mass_candidate(
                    archive,
                    source,
                    compiler_clean_passed=compiler_clean_passed,
                    site_containment_passed=site_containment_passed,
                ))
                self.assertEqual(archive.evidence()["record_count"], 0)

    def test_top_level_summary_publishes_generation_archive_evidence(self):
        from design.maas.book_language.portfolio_benchmark import (
            _legal_mass_archive_portfolio_summary,
            persist_book_program_summary,
        )

        archive = LegalMassArchive()
        archive.admit(self._candidate())
        summary = _legal_mass_archive_portfolio_summary([{
            "slug": "housing",
            "counts": {"legal_mass_archive": archive.evidence()},
        }])

        with TemporaryDirectory() as temporary_directory:
            path = persist_book_program_summary(
                Path(temporary_directory),
                {"legal_mass_archive": summary},
            )
            payload = json.loads(path.read_text(encoding="utf-8"))

        published = payload["legal_mass_archive"]
        self.assertEqual(published["record_count"], 1)
        self.assertEqual(
            published["programs"]["housing"]["records"][0][
                "geometry_hash"
            ],
            "geometry-parent",
        )
