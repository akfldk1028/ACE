from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import SimpleTestCase

from design.maas.book_language.legal_mass_archive import (
    _final_surface_payload_hash,
)
from design.maas.book_language.cumulative_candidate_pool import (
    build_cumulative_candidate_pool,
    select_recovery_records,
)


def _surface_payload(offset: float = 0.0) -> list[dict]:
    return [
        {
            "operator": "fixture",
            "role": "primary",
            "semantic_patch_id": "fixture:primary",
            "surface_type": "triangle",
            "verb": "fixture",
            "vertices_m": [
                [offset + 0.0, 0.0, 0.0],
                [offset + 1.0, 0.0, 0.0],
                [offset + 0.0, 1.0, 1.0],
            ],
            "volume_role": "neighborhood_primary_active_bar",
        }
    ]


def _artifact(
    *,
    geometry_hash: str,
    pnu: str = "site",
    legal_floor_field_hash: str = "legal-field",
    floor_capacity_plan_hash: str = "floor-plan",
    scope: str = "1/1",
    family: str = "ribbon",
    principle: str = "book:operative:shear",
    utilization: float = 0.8,
    finalization: bool = False,
    law_graph: bool = False,
    phenotype: str = "",
    visible_stepped: bool = False,
) -> dict:
    surfaces = _surface_payload(float(sum(ord(char) for char in geometry_hash)))
    surface_hash = _final_surface_payload_hash(surfaces)
    artifact = {
        "schemaVersion": "arr.maas.geometry_artifact.v1",
        "bookScope": scope,
        "bookPrincipleId": principle,
        "finalLegalGeometryHash": geometry_hash,
        "finalSurfacePayloadHash": surface_hash,
        "projectedVisualGeometryHash": f"visual-{geometry_hash}",
        "projectedVisualMesh": {"triangles": surfaces},
        "identity": {
            "finalLegalGeometryHash": geometry_hash,
            "geometryHash": f"visual-{geometry_hash}",
            "programHash": f"program-{geometry_hash}",
        },
        "geometryProgram": {"metadata": {"family": family}},
        "capacityAlternative": {
            "achieved_utilization": utilization,
            "legal_floor_field_hash": legal_floor_field_hash,
        },
        "floorwiseLegalMatrixStack": {
            "floor_capacity_plan_hash": floor_capacity_plan_hash,
        },
        "semanticProjectionAudit": {"audited_context": {"pnu": pnu}},
        "hardGates": {
            "cleanMass": {"hard_pass": True},
            "legal": {"hard_pass": True},
            "parking": {"hard_pass": True},
            "program": {"hard_pass": True},
            "candidateFinalization": {"hard_pass": finalization},
            "lawGraph": {"law_graph_evidence_hard_pass": law_graph},
        },
    }
    if phenotype:
        artifact["hardGates"]["program"]["evidence"] = {
            "program_form_gate": {
                "measured_morphology": {
                    "body_phenotype": phenotype,
                    "visible_stepped": visible_stepped,
                    "measurement_authority": "profiled_recursive_solid_mesh",
                }
            }
        }
    return artifact


def _write_archive(directory: Path, *artifacts: dict, pnu: str = "site") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "maas-book-exact-geometry-artifacts.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "arr.maas.geometry_artifact_archive.v1",
                "pnu": pnu,
                "record_count": len(artifacts),
                "records": [
                    {
                        "trace_sequence_name": f"fixture-{index}",
                        "geometry_artifact": artifact,
                    }
                    for index, artifact in enumerate(artifacts, start=1)
                ],
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    return path


class CumulativeCandidatePoolTests(SimpleTestCase):
    def test_pool_deduplicates_geometry_and_excludes_incompatible_context(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _write_archive(
                root / "run-a",
                _artifact(geometry_hash="g1", scope="1/1", family="ribbon"),
            )
            _write_archive(
                root / "run-b",
                _artifact(geometry_hash="g1", scope="1/2", family="bar"),
            )
            _write_archive(
                root / "run-c",
                _artifact(geometry_hash="g2", pnu="other"),
                pnu="other",
            )

            pool = build_cumulative_candidate_pool([root], pnu="site")

        self.assertEqual(pool["mass_eligible_unique_count"], 1)
        self.assertEqual(pool["duplicate_record_count"], 1)
        self.assertEqual(pool["incompatible_record_count"], 1)
        self.assertEqual(pool["context"]["legal_floor_field_hash"], "legal-field")
        self.assertEqual(pool["context"]["floor_capacity_plan_hash"], "floor-plan")

    def test_pool_does_not_promote_missing_publishable_evidence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _write_archive(
                root / "run-a",
                _artifact(
                    geometry_hash="g1",
                    finalization=False,
                    law_graph=False,
                ),
            )

            pool = build_cumulative_candidate_pool([root], pnu="site")

        self.assertEqual(pool["mass_eligible_unique_count"], 1)
        self.assertEqual(pool["publishable_unique_count"], 0)
        self.assertEqual(pool["candidates"][0]["status"], "needs_recertification")
        self.assertEqual(
            pool["candidates"][0]["recertification_reasons"],
            ["candidate_finalization_missing", "law_graph_evidence_missing"],
        )

    def test_pool_quarantines_malformed_archive(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            malformed = root / "broken" / "maas-book-exact-geometry-artifacts.json"
            malformed.parent.mkdir(parents=True)
            malformed.write_text('{"records": [', encoding="utf-8")
            _write_archive(root / "valid", _artifact(geometry_hash="g1"))

            pool = build_cumulative_candidate_pool([root], pnu="site")

        self.assertEqual(pool["archive_file_count"], 2)
        self.assertEqual(pool["malformed_archive_count"], 1)
        self.assertEqual(len(pool["malformed_archives"]), 1)
        self.assertEqual(pool["mass_eligible_unique_count"], 1)

    def test_recovery_selection_prefers_scope_and_family_diversity(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _write_archive(
                root / "run-a",
                _artifact(
                    geometry_hash="g1",
                    scope="1/1",
                    family="family-a",
                    principle="book:operative:shear",
                    utilization=0.95,
                ),
                _artifact(
                    geometry_hash="g2",
                    scope="1/1",
                    family="family-a",
                    principle="book:operative:shift",
                    utilization=0.9,
                ),
                _artifact(
                    geometry_hash="g3",
                    scope="1/2",
                    family="family-b",
                    principle="book:operative:shear",
                    utilization=0.8,
                ),
                _artifact(
                    geometry_hash="g4",
                    scope="2/3",
                    family="family-c",
                    principle="book:operative:carve",
                    utilization=0.7,
                ),
            )
            pool = build_cumulative_candidate_pool([root], pnu="site")

            selected = select_recovery_records(pool, target_count=3)

        self.assertEqual(
            [row["geometry_hash"] for row in selected],
            ["g1", "g3", "g4"],
        )

    def test_recovery_selection_prefers_measured_non_stepped_phenotypes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _write_archive(
                root / "run-a",
                _artifact(geometry_hash="g1", utilization=0.99),
                _artifact(
                    geometry_hash="g2",
                    phenotype="curved",
                    visible_stepped=False,
                    utilization=0.8,
                ),
                _artifact(
                    geometry_hash="g3",
                    phenotype="oblique",
                    visible_stepped=False,
                    scope="1/2",
                    family="wing",
                    utilization=0.7,
                ),
                _artifact(
                    geometry_hash="g4",
                    phenotype="stepped",
                    visible_stepped=True,
                    scope="2/3",
                    family="terrace",
                    utilization=0.95,
                ),
            )
            pool = build_cumulative_candidate_pool([root], pnu="site")

            selected = select_recovery_records(pool, target_count=2)

        self.assertEqual(
            [row["geometry_hash"] for row in selected],
            ["g2", "g3"],
        )


class CumulativeCandidatePoolCommandTests(SimpleTestCase):
    def test_command_writes_ledger_journal_and_exact_board(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive_root = root / "archives"
            output_dir = root / "out"
            _write_archive(
                archive_root / "run-a",
                _artifact(geometry_hash="g1", scope="1/1", family="a"),
                _artifact(geometry_hash="g2", scope="1/2", family="b"),
                _artifact(geometry_hash="g3", scope="2/3", family="c"),
            )

            call_command(
                "rebuild_maas_cumulative_candidate_pool",
                archive_root=[str(archive_root)],
                output_dir=str(output_dir),
                pnu="site",
                target_count=3,
            )

            ledger = json.loads(
                (output_dir / "maas-cumulative-candidate-ledger.json").read_text(
                    encoding="utf-8"
                )
            )
            journal = json.loads(
                (output_dir / "maas-cumulative-flow-journal.json").read_text(
                    encoding="utf-8"
                )
            )
            png_exists = Path(ledger["recovery_board"]["png_path"]).is_file()

        self.assertEqual(ledger["selected_recovery_count"], 3)
        self.assertEqual(journal["stages"][-1]["stage"], "exact_board_rendered")
        self.assertTrue(png_exists)
        self.assertEqual(ledger["recovery_board"]["card_count"], 3)
