"""Contracts for the architect-supplied BOOK language registry."""

import gc
import hashlib
import json
import os
import weakref
from collections import Counter
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from math import cos, sin, tau
from pathlib import Path
from threading import Barrier, Lock
from time import sleep
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase
from shapely.affinity import rotate
from shapely.geometry import Polygon
from shapely.ops import triangulate

from design.maas.book_language import audited_book_language_registry, book_base_verbs, build_book_language_registry
from design.maas.book_language import candidate_analysis, candidate_generation, portfolio_benchmark, portfolio_feedback
from design.maas.book_language import portfolio_selection, vlm_review
from design.maas.book_language import final_vlm_cycle, portfolio_replenishment
from design.maas.book_language import lineage as book_lineage
from design.maas.book_language import quality_diversity_archive
from design.maas.book_language.corpus_audit import audit_book_corpus
from design.maas.book_language.competition_portfolio_contract import (
    competition_portfolio_contract,
)
from design.maas.book_language.competition_breadth_scheduler import (
    CompetitionBreadthScheduler,
    cheap_screen_records,
)
from design.maas.geometry_language import (
    GeometryNode,
    GeometryProgram,
    architectural_shape_programs,
    base_seed_program,
    compile_geometry_program,
    compile_geometry_program_to_source_mass,
)
from design.maas.geometry_language.projected_visual_contract import (
    validate_projected_visual_artifact,
)
from design.maas.grammar.vocab import BOOK_BASE_VERBS, SUPPORTED_VERBS
from design.maas.preference.vlm_scorer import _normalize_vlm_result
from design.maas.preference import vlm_scorer
from design.maas.preference.loop import _vlm_cache_key
from design.maas.program_massing import program_seed_sequences
from design.maas.program_massing.visual_silhouette import (
    visual_silhouette_distance,
)
from design.maas.source_geometry import compile_sequence_to_source_mass
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume


class MaasBookLanguageRegistryTest(SimpleTestCase):
    @staticmethod
    def _publishable_phase_timings():
        return {
            "pnu_context": 1.0,
            "breadth_enumeration": 1.1,
            "cheap_screen": 1.2,
            "exact_compile": 2.0,
            "law": 0.8,
            "parking": 0.7,
            "solver": 0.5,
            "render": 0.4,
            "total": 7.7,
        }

    def test_publishable_command_requires_twenty_card_contract(self):
        with self.assertRaisesRegex(
            CommandError,
            "--publishable-20 cannot be combined with --diagnostic-target",
        ):
            call_command(
                "benchmark_maas_book_program_portfolios",
                publishable_20=True,
                diagnostic_target=3,
            )

    @staticmethod
    def _publishable_authoritative_programs():
        from design.maas.geometry_language.section_profiles import (
            SECTION_PROFILES,
        )

        architectural = list(architectural_shape_programs())

        def profiled(program, family, suffix):
            base = base_seed_program("bar")
            roof = GeometryNode(
                id=f"fixture_roof_{family}_{suffix}",
                kind="macro",
                operator="profiled_hall",
                inputs=(program.root_id,),
                parameters={
                    "section_family": family,
                    "section_controls": SECTION_PROFILES[family],
                    "span_axis": "x",
                },
                provenance={"source": "publishable_test_fixture"},
            )
            return program.with_nodes(
                (*program.nodes, roof),
                root_id=roof.id,
                name_suffix=f"_{family}_{suffix}",
            )

        def translated(program, index, suffix):
            shift = GeometryNode(
                id=f"fixture_shift_{suffix}_{index}",
                kind="transform",
                operator="translate",
                inputs=(program.root_id,),
                parameters={
                    "vector": [index * 0.25, index * 0.13, 0.0],
                },
                provenance={"source": "publishable_test_fixture"},
            )
            return program.with_nodes(
                (*program.nodes, shift),
                root_id=shift.id,
                name_suffix=f"_fixture_{index}",
            )

        courtyard = architectural[4]
        attached = architectural[5]
        setback = architectural[7]
        bar = base_seed_program("bar")
        return (
            # Four voided courtyard plans, but four independently measured
            # roof genotypes.
            courtyard,
            profiled(courtyard, "ridge", "court"),
            profiled(courtyard, "shed", "court"),
            profiled(courtyard, "barrel", "court"),
            # Four winged plans; the fourth has an authored folded section.
            architectural[1],
            architectural[8],
            architectural[16],
            profiled(architectural[1], "folded", "wing"),
            # Four stepped bodies across two distinct chassis families.
            attached,
            translated(attached, 1, "attached"),
            profiled(setback, "stepped", "terrace"),
            profiled(
                translated(setback, 1, "terrace"),
                "sawtooth",
                "terrace",
            ),
            # Four oblique bodies, one tower plus three roofed bars.
            architectural[9],
            profiled(bar, "ridge", "oblique"),
            profiled(bar, "folded", "oblique"),
            profiled(bar, "barrel", "oblique"),
            # Four prismatic bodies with bounded plan/chassis repetition.
            architectural[11],
            architectural[13],
            architectural[17],
            profiled(bar, "shed", "prismatic"),
        )

    @staticmethod
    def _publishable_authoritative_artifact(program):
        from design.maas.geometry_language.projected_visual_contract import (
            AUTHORED_COORDINATE_SPACE,
            CAPACITY_PROGRAM_ROLE,
            CERTIFICATE_SCHEMA,
            MESH_SCHEMA,
            PROJECTED_AUTHORITY,
            _task1_visual_hash,
            exact_triangle_payload_hash,
        )

        compilation = compile_geometry_program(program)
        if compilation.status != "compiled":
            raise AssertionError(compilation.issues)
        triangles = [{
            "role": f"fixture_triangle_{index}",
            "volume_role": "certified_visual_mesh",
            "verb": "geometry_program",
            "surface_type": "profiled_recursive_solid_mesh",
            "vertices_m": [
                [
                    float(value)
                    for value in compilation.vertices[vertex_index]
                ]
                for vertex_index in triangle
            ],
            "operator": program.node_map[program.root_id].operator,
            "semantic_patch_id": f"fixture:triangle:{index}",
        } for index, triangle in enumerate(compilation.triangles)]
        visual_hash = _task1_visual_hash(triangles)
        payload_hash = exact_triangle_payload_hash(triangles)
        certificate = {
            "schema_version": CERTIFICATE_SCHEMA,
            "status": "certified",
            "hard_pass": True,
            "certification_mode": "authored_visual_legal_validation",
            "visual_hash": visual_hash,
            "projected_surface_count": len(triangles),
            "projected_surface_coordinate_frame": (
                AUTHORED_COORDINATE_SPACE
            ),
            "exact_surface_payload_hash": payload_hash,
        }
        return {
            "schemaVersion": "arr.maas.geometry_artifact.v1",
            "authority": PROJECTED_AUTHORITY,
            "geometryProgramRole": CAPACITY_PROGRAM_ROLE,
            "geometryProgram": program.to_dict(),
            "identity": {
                "programHash": program.program_hash(),
                "geometryHash": visual_hash,
                "finalLegalGeometryHash": compilation.geometry_hash,
            },
            "finalLegalGeometryHash": compilation.geometry_hash,
            "projectedVisualMesh": {
                "schemaVersion": MESH_SCHEMA,
                "coordinateSpace": AUTHORED_COORDINATE_SPACE,
                "triangles": triangles,
                "vertexCount": len(triangles) * 3,
                "triangleCount": len(triangles),
            },
            "projectedVisualCertificate": certificate,
            "projectedVisualGeometryHash": visual_hash,
            "projectedVisualPayloadHash": payload_hash,
        }

    @staticmethod
    def _publishable_twenty_fixture():
        from design.maas.agents.law_graph_agent.evidence import (
            canonical_agent_evidence_hash,
        )
        from design.maas.program_massing.competition_gestalt import (
            competition_gestalt_distance,
        )
        from design.maas.program_massing.certified_artifact_measurement import (
            measure_authoritative_geometry_artifact,
        )

        pnu = "1168011800104170004"
        shared_floor_plan_hash = "floor-plan-shared"
        scopes = (
            ("1/1", 4),
            ("1/2", 4),
            ("3/8", 3),
            ("1/4", 3),
            ("1/8", 3),
            ("1/16", 3),
        )
        scope_values = [
            scope
            for scope, count in scopes
            for _ in range(count)
        ]
        capacity_bands = (
            ["spatial_reserve"] * 5
            + ["balanced_yield"] * 5
            + ["brief_target"] * 5
            + ["maximum_feasible"] * 5
        )
        rows = []
        gestalt_keys = []
        authoritative_programs = (
            MaasBookLanguageRegistryTest
            ._publishable_authoritative_programs()
        )
        for index in range(20):
            execution_id = f"book:neighborhood:maas_{index + 1:02d}"
            authoritative_artifact = (
                MaasBookLanguageRegistryTest
                ._publishable_authoritative_artifact(
                    authoritative_programs[index]
                )
            )
            authoritative_identity = authoritative_artifact["identity"]
            program_hash = str(authoritative_identity["programHash"])
            geometry_hash = str(
                authoritative_identity["finalLegalGeometryHash"]
            )
            visual_hash = str(authoritative_identity["geometryHash"])
            authoritative_measurement = (
                measure_authoritative_geometry_artifact(
                    authoritative_artifact,
                    expected_program_hash=program_hash,
                    expected_final_geometry_hash=geometry_hash,
                    expected_visual_hash=visual_hash,
                )
            )
            law_payload = {
                "evidence_id": "evidence:law_graph_agent",
                "agent": "law_graph_agent",
                "status": "passed",
                "summary": "law graph evidence",
                "identity": {
                    "execution_id": execution_id,
                    "program_hash": program_hash,
                    "geometry_hash": geometry_hash,
                    "floor_capacity_plan_hash": shared_floor_plan_hash,
                    "pnu": pnu,
                },
                "evidence": {
                    "pnu": pnu,
                    "numeric_preflight": {
                        "evaluated": True,
                        "hard_pass": True,
                        "status": "pass",
                    },
                    "neo4j": {"attempted": True, "available": True},
                    "law_search": {"attempted": True, "available": True},
                    "article_ids": ["article-1"],
                    "search_result_ids": ["search-1"],
                    "missing_evidence": [],
                },
            }
            gestalt_key = authoritative_measurement.gestalt_key
            gestalt_keys.append(gestalt_key)
            gestalt_payload = gestalt_key.to_payload()
            morphology = authoritative_measurement.morphology
            gestalt_payload_hash = hashlib.sha256(
                json.dumps(
                    gestalt_payload,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            morphology_payload_hash = hashlib.sha256(
                json.dumps(
                    morphology,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            certified_mesh_evidence = {
                "schema_version": "arr.maas.certified_mesh_gestalt.v1",
                "measurement_authority": (
                    "certified_projected_visual_mesh"
                ),
                "visual_hash": visual_hash,
                "exact_mesh_payload_hash": (
                    authoritative_measurement.exact_mesh_payload_hash
                ),
                "gestalt_payload_hash": gestalt_payload_hash,
                "morphology_payload_hash": morphology_payload_hash,
                "morphology": morphology,
            }
            certified_mesh_evidence["evidence_hash"] = hashlib.sha256(
                json.dumps(
                    certified_mesh_evidence,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            rows.append({
                "variant_id": f"maas_{index + 1:02d}",
                "book_operation": (
                    "winged" if index in (0, 2)
                    else "curved" if index == 1
                    else f"operation-{index % 12}"
                ),
                "book_principle_id": f"principle-{index % 12}",
                "book_scope": {
                    "base_volume_label": scope_values[index],
                },
                "resolved_capacity_alternative_id": capacity_bands[index],
                **deepcopy(morphology),
                "visible_stepped": gestalt_key.visible_stepped,
                "certified_gestalt_key": gestalt_payload,
                "certified_mesh_evidence": certified_mesh_evidence,
                "authoritative_geometry_artifact": (
                    authoritative_artifact
                ),
                "inside_site": True,
                "program_hard_pass": True,
                "resolved_capacity_hard_pass": True,
                "combined_hard_pass": True,
                "law_graph_evidence_hard_pass": True,
                "selected_execution_id": execution_id,
                "final_legal_program_hash": program_hash,
                "final_legal_geometry_hash": geometry_hash,
                "floor_capacity_plan_hash": shared_floor_plan_hash,
                "parking_hard_gate": {
                    "evaluated": True,
                    "hard_pass": True,
                    "rule_repository_source": "neo4j:test",
                    "graph_status": "available",
                },
                "parking_rule_source": "neo4j:test",
                "parking_graph_status": "available",
                "law_graph_agent_evidence": law_payload,
                "law_graph_evidence_hash": (
                    canonical_agent_evidence_hash(law_payload)
                ),
                "archive_render_evidence": {
                    "projected_visual_geometry_hash": visual_hash,
                    "final_legal_geometry_hash": geometry_hash,
                    "exact_mesh_payload_hash": (
                        authoritative_measurement
                        .exact_mesh_payload_hash
                    ),
                    "morphology_payload_hash": morphology_payload_hash,
                },
                "legal_projection": {
                    "evaluated": True,
                    "hard_pass": True,
                    "status": "pass",
                },
                "mass_execution_passport": {
                    "program_hash": program_hash,
                    "geometry_hash": visual_hash,
                    "visual_hash": visual_hash,
                    "final_legal_geometry_hash": geometry_hash,
                    "floor_capacity_plan_hash": shared_floor_plan_hash,
                },
            })
        pair_rows = []
        for right_index, right_key in enumerate(gestalt_keys):
            for left_index in range(right_index):
                same_body = (
                    rows[left_index]["body_phenotype"]
                    == rows[right_index]["body_phenotype"]
                )
                same_roof = (
                    rows[left_index]["roof_archetype"]
                    == rows[right_index]["roof_archetype"]
                )
                required = 0.22 if same_body or same_roof else 0.14
                distance = competition_gestalt_distance(
                    gestalt_keys[left_index],
                    right_key,
                )
                pair_rows.append({
                    "left_variant_id": rows[left_index]["variant_id"],
                    "right_variant_id": rows[right_index]["variant_id"],
                    "distance": distance,
                    "required_distance": required,
                    "same_body_phenotype": same_body,
                    "same_roof_archetype": same_roof,
                    "hard_pass": distance >= required,
                })
        return {
            "pnu": pnu,
            "status": "pass",
            "programs": [{
                "slug": "neighborhood",
                "status": "pass",
                "selected_count": 20,
                "book_operation_count": 12,
                "portfolio_completion": {
                    "hard_pass": True,
                    "failures": [],
                },
                "downstream_hard_gate": {"status": "pass"},
                "selected_pair_certificate": {
                    "schema_version": (
                        "arr.maas.competition_gestalt_pair_certificate.v1"
                    ),
                    "measurement_authority": "certified_final_mesh",
                    "expected_pair_count": 190,
                    "pair_count": len(pair_rows),
                    "hard_pass": True,
                    "pairs": pair_rows,
                },
                "program_language_metrics": {
                    "stepped_count": 2,
                    "solid_phenotype_count": 5,
                    "roof_archetype_count": 10,
                    "chassis_family_count": 10,
                    "plan_family_counts": {
                        f"plan-{index}": 4 for index in range(5)
                    },
                },
                "counts": {
                    "selection_trace": {
                        "portfolio_contract_target_count": 20,
                        "portfolio_contract_solver_count": 20,
                        "portfolio_contract_solver_target_reached": True,
                        "portfolio_contract_deficits": [],
                        "compatibility_analysis": {
                            "compatibility_threshold": 0.14,
                        },
                    },
                },
                "rows": rows,
                "failures": [],
            }],
        }

    def test_publishable_manifest_rejects_old_synthetic_twenty_after_exact_remeasurement(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        evidence = build_publishable_20_manifest_evidence(
            self._publishable_twenty_fixture(),
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertEqual(evidence["target_count"], 20)
        self.assertEqual(
            evidence["phase_durations_seconds"]["exact_compile"],
            2.0,
        )
        program = evidence["programs"][0]
        self.assertEqual(
            program["quota_evidence"]["capacity_band_counts"],
            {
                "balanced_yield": 5,
                "brief_target": 5,
                "maximum_feasible": 5,
                "spatial_reserve": 5,
            },
        )
        self.assertEqual(program["contract_metrics"]["selected_count"], 20)
        self.assertEqual(
            program["contract_metrics"]["solver_evidence"],
            {
                "target_count": 20,
                "selected_count": 20,
                "target_reached": True,
                "compatibility_threshold": 0.14,
                "minimum_pair_distance": 0.14,
                "shared_language_minimum_composite_distance": 0.22,
                "deficits": [],
            },
        )
        self.assertEqual(len(program["identity_hashes"]), 20)
        self.assertEqual(
            set(program["identity_hashes"][0]),
            {
                "variant_id",
                "program_hash",
                "geometry_hash",
                "visual_hash",
                "floor_capacity_plan_hash",
                "legal_floor_field_hash",
                "candidate_actual_gfa_stop_hash",
            },
        )
        deficit_codes = {
            deficit["code"]
            for deficit in evidence["typed_failure_deficits"]
        }
        self.assertIn("gestalt.pair_distance_below_contract", deficit_codes)
        self.assertIn("quota.visible_stepped_outside_range", deficit_codes)
        self.assertIn("quota.wedge_above_2", deficit_codes)
        self.assertIn("quota.pyramid_above_2", deficit_codes)

    def test_authoritative_artifact_recompiles_once_and_remeasures_exact_mesh(self):
        from design.maas.program_massing import (
            certified_artifact_measurement,
        )

        program = architectural_shape_programs()[4]
        artifact = self._publishable_authoritative_artifact(program)
        identity = artifact["identity"]

        with patch.object(
            certified_artifact_measurement,
            "compile_geometry_program",
            wraps=compile_geometry_program,
        ) as compile_spy:
            measurement = (
                certified_artifact_measurement
                .measure_authoritative_geometry_artifact(
                    artifact,
                    expected_program_hash=identity["programHash"],
                    expected_final_geometry_hash=(
                        identity["finalLegalGeometryHash"]
                    ),
                    expected_visual_hash=identity["geometryHash"],
                )
            )

        self.assertEqual(compile_spy.call_count, 1)
        self.assertEqual(
            measurement.program_hash,
            identity["programHash"],
        )
        self.assertEqual(
            measurement.final_geometry_hash,
            identity["finalLegalGeometryHash"],
        )
        self.assertEqual(
            measurement.visual_hash,
            identity["geometryHash"],
        )
        self.assertEqual(
            measurement.gestalt_key.measurement_authority,
            "certified_final_mesh",
        )
        self.assertEqual(
            len(measurement.gestalt_key.projection_variants),
            8,
        )
        self.assertEqual(
            measurement.morphology["body_phenotype"],
            "voided",
        )
        self.assertEqual(
            measurement.morphology["plan_family"],
            "courtyard",
        )

    def test_publishable_manifest_fails_closed_on_missing_visual_identity(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        summary["programs"][0]["rows"][0]["mass_execution_passport"][
            "visual_hash"
        ] = ""
        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds={},
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "identity.visual_hash_missing",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_visual_hash_not_bound_to_render(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        summary["programs"][0]["rows"][0]["mass_execution_passport"][
            "visual_hash"
        ] = "visual-not-rendered"
        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds={},
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "identity.visual_hash_mismatch",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_twenty_copies_but_not_split_candidate_floor_plans(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        rows = summary["programs"][0]["rows"]
        first = rows[0]
        for index, row in enumerate(rows):
            row["final_legal_program_hash"] = first["final_legal_program_hash"]
            row["final_legal_geometry_hash"] = first["final_legal_geometry_hash"]
            row["archive_render_evidence"] = dict(first["archive_render_evidence"])
            row["mass_execution_passport"] = dict(first["mass_execution_passport"])
            row["floor_capacity_plan_hash"] = f"split-floor-{index:02d}"
            row["mass_execution_passport"]["floor_capacity_plan_hash"] = (
                row["floor_capacity_plan_hash"]
            )

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )
        codes = {
            deficit["code"]
            for deficit in evidence["typed_failure_deficits"]
        }
        self.assertEqual(evidence["status"], "fail")
        self.assertIn("identity.duplicate_program_hash", codes)
        self.assertIn("identity.duplicate_geometry_hash", codes)
        self.assertIn("identity.duplicate_visual_hash", codes)
        self.assertNotIn("identity.floor_capacity_plan_not_shared", codes)
        self.assertIn(
            "identity.legal_floor_field_not_shared_or_trusted",
            codes,
        )
        self.assertIn("identity.actual_gfa_stop_invalid", codes)

    def test_publishable_manifest_accepts_split_candidate_plans_with_shared_legal_and_valid_stops(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )
        from design.test_maas_actual_gfa_stop_certificate import (
            _certify,
            _field,
        )

        summary = self._publishable_twenty_fixture()
        program = summary["programs"][0]
        field = _field(pnu=summary["pnu"])
        program["floor_capacity_plan"] = {
            "legal_floor_field": deepcopy(field),
            "legal_floor_field_hash": field["legal_floor_field_hash"],
        }
        for index, row in enumerate(program["rows"]):
            identity = {
                "program_hash": row["final_legal_program_hash"],
                "final_geometry_hash": row[
                    "final_legal_geometry_hash"
                ],
                "visual_hash": row["mass_execution_passport"][
                    "visual_hash"
                ],
            }
            certificate = _certify(
                field,
                identity=identity,
                areas=(100.0,) + (0.0,) * 24,
                target=100.0,
            )
            plan_hash = f"candidate-plan-{index:02d}"
            row.update({
                "floor_capacity_plan_hash": plan_hash,
                "legal_floor_field_hash": field[
                    "legal_floor_field_hash"
                ],
                "candidate_actual_gfa_stop_hash": certificate[
                    "candidate_actual_gfa_stop_hash"
                ],
                "candidate_actual_gfa_stop_certificate": deepcopy(
                    certificate
                ),
                "candidate_floor_count": 1,
                "candidate_target_gfa_m2": 100.0,
                "achieved_gfa_m2": 100.0,
            })
            row["mass_execution_passport"].update({
                "floor_capacity_plan_hash": plan_hash,
                "legal_floor_field_hash": field[
                    "legal_floor_field_hash"
                ],
                "candidate_actual_gfa_stop_hash": certificate[
                    "candidate_actual_gfa_stop_hash"
                ],
                "candidate_actual_gfa_stop_certificate": deepcopy(
                    certificate
                ),
            })

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )
        codes = {
            deficit["code"]
            for deficit in evidence["typed_failure_deficits"]
        }

        self.assertNotIn("identity.floor_capacity_plan_not_shared", codes)
        self.assertNotIn(
            "identity.legal_floor_field_not_shared_or_trusted",
            codes,
        )
        self.assertNotIn("identity.actual_gfa_stop_invalid", codes)
        self.assertEqual(
            evidence["programs"][0]["contract_metrics"][
                "candidate_actual_gfa_stop_valid_count"
            ],
            20,
        )

        stale = deepcopy(summary)
        stale["programs"][0]["rows"][0][
            "mass_execution_passport"
        ]["candidate_actual_gfa_stop_certificate"] = deepcopy(
            stale["programs"][0]["rows"][1][
                "candidate_actual_gfa_stop_certificate"
            ]
        )
        stale_evidence = build_publishable_20_manifest_evidence(
            stale,
            phase_durations_seconds=self._publishable_phase_timings(),
        )
        self.assertIn(
            "identity.actual_gfa_stop_invalid",
            {
                deficit["code"]
                for deficit in stale_evidence[
                    "typed_failure_deficits"
                ]
            },
        )

    def test_publishable_manifest_validates_law_payload_not_boolean_label(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        summary["programs"][0]["rows"][0][
            "law_graph_evidence_hash"
        ] = "tampered"

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds={},
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "hard_gate.law_graph_payload_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_failed_numeric_law_preflight(self):
        from design.maas.agents.law_graph_agent.evidence import (
            canonical_agent_evidence_hash,
        )
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        row = summary["programs"][0]["rows"][0]
        row["law_graph_agent_evidence"]["evidence"][
            "numeric_preflight"
        ] = {
            "evaluated": True,
            "hard_pass": False,
            "status": "failed",
        }
        row["law_graph_evidence_hash"] = canonical_agent_evidence_hash(
            row["law_graph_agent_evidence"]
        )

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "hard_gate.law_graph_payload_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_missing_law_search_evidence(self):
        from design.maas.agents.law_graph_agent.evidence import (
            canonical_agent_evidence_hash,
        )
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        row = summary["programs"][0]["rows"][0]
        law = row["law_graph_agent_evidence"]
        law["evidence"]["law_search"] = {
            "attempted": True,
            "available": False,
        }
        law["evidence"]["article_ids"] = []
        law["evidence"]["search_result_ids"] = []
        law["evidence"]["missing_evidence"] = [
            "law_search_unavailable",
        ]
        row["law_graph_evidence_hash"] = canonical_agent_evidence_hash(law)

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "hard_gate.law_graph_payload_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_failed_legal_projection(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        summary["programs"][0]["rows"][0]["legal_projection"] = {
            "evaluated": True,
            "hard_pass": False,
            "status": "failed",
        }

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "hard_gate.legal_projection_not_pass",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_uses_hash_bound_mesh_morphology_not_row_labels(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        for row in summary["programs"][0]["rows"]:
            row.update({
                "body_phenotype": "forged-row-body",
                "roof_archetype": "forged-row-roof",
                "chassis_family": "forged-row-chassis",
                "plan_family": "forged-row-plan",
                "solid_genus": 0,
                "wedge_like": True,
                "pyramidal_like": True,
            })

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["typed_failure_deficits"], [])

    def test_publishable_manifest_rejects_mesh_evidence_not_bound_to_visual_hash(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        summary["programs"][0]["rows"][0]["certified_mesh_evidence"][
            "visual_hash"
        ] = "forged-visual"

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "gestalt.certified_mesh_evidence_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_mesh_payload_hash_not_bound_to_render(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        mesh_evidence = summary["programs"][0]["rows"][0][
            "certified_mesh_evidence"
        ]
        mesh_evidence["exact_mesh_payload_hash"] = "forged-mesh-payload"
        hash_payload = {
            key: value
            for key, value in mesh_evidence.items()
            if key != "evidence_hash"
        }
        mesh_evidence["evidence_hash"] = hashlib.sha256(
            json.dumps(
                hash_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "gestalt.certified_mesh_evidence_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_rehashed_morphology_not_bound_to_mesh(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        mesh_evidence = summary["programs"][0]["rows"][0][
            "certified_mesh_evidence"
        ]
        mesh_evidence["morphology"]["body_phenotype"] = "forged-body"
        mesh_evidence["morphology_payload_hash"] = hashlib.sha256(
            json.dumps(
                mesh_evidence["morphology"],
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        hash_payload = {
            key: value
            for key, value in mesh_evidence.items()
            if key != "evidence_hash"
        }
        mesh_evidence["evidence_hash"] = hashlib.sha256(
            json.dumps(
                hash_payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "gestalt.certified_mesh_evidence_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_missing_authoritative_geometry_artifact(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        summary["programs"][0]["rows"][0].pop(
            "authoritative_geometry_artifact"
        )

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "gestalt.authoritative_geometry_artifact_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_coordinated_mesh_and_render_hash_reseal(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        row = summary["programs"][0]["rows"][0]
        mesh_evidence = row["certified_mesh_evidence"]
        mesh_evidence["exact_mesh_payload_hash"] = "coordinated-forged-mesh"
        row["archive_render_evidence"][
            "exact_mesh_payload_hash"
        ] = "coordinated-forged-mesh"
        mesh_evidence["evidence_hash"] = hashlib.sha256(
            json.dumps(
                {
                    key: value
                    for key, value in mesh_evidence.items()
                    if key != "evidence_hash"
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "gestalt.authoritative_geometry_artifact_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_coordinated_morphology_render_and_pair_reseal(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        rows = summary["programs"][0]["rows"]
        mesh_evidence = rows[0]["certified_mesh_evidence"]
        mesh_evidence["morphology"]["body_phenotype"] = (
            "coordinated-forged-body"
        )
        mesh_evidence["morphology_payload_hash"] = hashlib.sha256(
            json.dumps(
                mesh_evidence["morphology"],
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        rows[0]["archive_render_evidence"][
            "morphology_payload_hash"
        ] = mesh_evidence["morphology_payload_hash"]
        mesh_evidence["evidence_hash"] = hashlib.sha256(
            json.dumps(
                {
                    key: value
                    for key, value in mesh_evidence.items()
                    if key != "evidence_hash"
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        for pair in summary["programs"][0][
            "selected_pair_certificate"
        ]["pairs"]:
            left_index = int(
                str(pair["left_variant_id"]).split("_", 1)[1]
            ) - 1
            right_index = int(
                str(pair["right_variant_id"]).split("_", 1)[1]
            ) - 1
            left = rows[left_index]["certified_mesh_evidence"][
                "morphology"
            ]
            right = rows[right_index]["certified_mesh_evidence"][
                "morphology"
            ]
            same_body = (
                left["body_phenotype"] == right["body_phenotype"]
            )
            same_roof = (
                left["roof_archetype"] == right["roof_archetype"]
            )
            pair.update({
                "same_body_phenotype": same_body,
                "same_roof_archetype": same_roof,
                "required_distance": (
                    0.22 if same_body or same_roof else 0.14
                ),
                "hard_pass": float(pair["distance"]) >= (
                    0.22 if same_body or same_roof else 0.14
                ),
            })

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "gestalt.authoritative_geometry_artifact_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_requires_explicit_numeric_law_pass_status(self):
        from design.maas.agents.law_graph_agent.evidence import (
            canonical_agent_evidence_hash,
        )
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        row = summary["programs"][0]["rows"][0]
        row["law_graph_agent_evidence"]["evidence"][
            "numeric_preflight"
        ].pop("status")
        row["law_graph_evidence_hash"] = canonical_agent_evidence_hash(
            row["law_graph_agent_evidence"]
        )

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "hard_gate.law_graph_payload_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_requires_explicit_legal_projection_pass_status(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        summary["programs"][0]["rows"][0][
            "legal_projection"
        ].pop("status")

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "hard_gate.legal_projection_not_pass",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_rejects_nonfinite_pair_certificate(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        certificate = summary["programs"][0]["selected_pair_certificate"]
        certificate["hard_pass"] = False
        certificate["pairs"][0].update({
            "distance": "NaN",
            "required_distance": 999,
            "hard_pass": False,
        })

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "gestalt.pair_certificate_invalid",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_requires_complete_passport_hash_chain(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        passport = summary["programs"][0]["rows"][0][
            "mass_execution_passport"
        ]
        passport["program_hash"] = ""
        passport["floor_capacity_plan_hash"] = ""
        passport["final_legal_geometry_hash"] = ""
        passport["geometry_hash"] = "stale-passport-geometry"

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds=self._publishable_phase_timings(),
        )
        codes = {
            deficit["code"]
            for deficit in evidence["typed_failure_deficits"]
        }

        self.assertEqual(evidence["status"], "fail")
        self.assertIn("identity.passport_program_hash_missing", codes)
        self.assertIn(
            "identity.passport_floor_capacity_plan_hash_missing",
            codes,
        )
        self.assertIn(
            "identity.passport_final_legal_geometry_hash_missing",
            codes,
        )
        self.assertIn("identity.passport_geometry_hash_mismatch", codes)

    def test_publishable_manifest_recomputes_all_190_final_mesh_distances(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        rows = summary["programs"][0]["rows"]
        rows[1]["certified_gestalt_key"] = deepcopy(
            rows[0]["certified_gestalt_key"]
        )
        # Stale certificate labels still claim every pair passed.
        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds={},
        )
        codes = {
            deficit["code"]
            for deficit in evidence["typed_failure_deficits"]
        }

        self.assertEqual(evidence["status"], "fail")
        self.assertIn("gestalt.pair_distance_below_contract", codes)
        self.assertIn("gestalt.pair_certificate_distance_mismatch", codes)

    def test_publishable_manifest_uses_final_mesh_step_fact_not_stale_summary(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        summary = self._publishable_twenty_fixture()
        summary["programs"][0]["program_language_metrics"][
            "stepped_count"
        ] = 2
        for row in summary["programs"][0]["rows"]:
            row["visible_stepped"] = True
            row["certified_gestalt_key"]["visible_stepped"] = False

        evidence = build_publishable_20_manifest_evidence(
            summary,
            phase_durations_seconds={},
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "quota.visible_stepped_outside_range",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_requires_all_phase_timings(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        evidence = build_publishable_20_manifest_evidence(
            self._publishable_twenty_fixture(),
            phase_durations_seconds={
                "pnu_context": 1.0,
                "breadth_enumeration": 1.0,
                "cheap_screen": 1.0,
                "exact_compile": 2.0,
                "law": 1.0,
                "parking": 1.0,
                "solver": 1.0,
                "total": 3.0,
            },
        )

        self.assertEqual(evidence["status"], "fail")
        self.assertIn(
            "timing.render_missing",
            {
                deficit["code"]
                for deficit in evidence["typed_failure_deficits"]
            },
        )

    def test_publishable_manifest_preserves_positive_submillisecond_timing(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            build_publishable_20_manifest_evidence,
        )

        timings = self._publishable_phase_timings()
        timings["solver"] = 0.0001
        evidence = build_publishable_20_manifest_evidence(
            self._publishable_twenty_fixture(),
            phase_durations_seconds=timings,
        )

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(
            evidence["phase_durations_seconds"]["solver"],
            0.0001,
        )

    def test_publishable_command_persists_manifest_evidence_before_acceptance(self):
        from design.management.commands.benchmark_maas_book_program_portfolios import (
            persist_publishable_20_result,
        )

        with TemporaryDirectory() as temporary_dir:
            output_dir = Path(temporary_dir)
            result = self._publishable_twenty_fixture()
            evidence = persist_publishable_20_result(
                output_dir,
                result,
                phase_durations_seconds=self._publishable_phase_timings(),
            )
            persisted = json.loads(
                (
                    output_dir / "maas-book-programs-summary.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(
            persisted["publishable_20_manifest"]["status"],
            "pass",
        )
        self.assertEqual(
            persisted["publishable_20_manifest"][
                "phase_durations_seconds"
            ]["total"],
            7.7,
        )

    def test_certified_visual_hash_flows_from_passport_to_archive_record(self):
        from design.maas.geometry_language.executed_archive import (
            _manifest_row,
        )
        from design.maas.geometry_language.execution_passport import (
            build_mass_execution_passport,
        )

        program = base_seed_program("block")
        compilation = compile_geometry_program(program)
        certified = replace(
            compilation,
            metrics={
                **compilation.metrics,
                "geometry_authority": (
                    "certified_projected_visual_mesh"
                ),
            },
        )
        passport = build_mass_execution_passport(certified)
        visual_hash = compilation.geometry_hash
        artifact = {
            "geometryProgram": program.to_dict(),
            "identity": {
                "programHash": program.program_hash(),
                "geometryHash": visual_hash,
            },
            "projectedVisualGeometryHash": visual_hash,
            "projectedVisualCertificate": {
                "visual_hash": visual_hash,
            },
            "compilation": compilation.to_dict(include_mesh=False),
            "capacityAlternative": {},
            "hardGates": {"combinedHardPass": True},
            "executionPassport": passport,
        }
        row = _manifest_row(
            1,
            {
                "trace_sequence_name": "certified-visual",
                "geometry_artifact": artifact,
            },
            {"variant_id": "maas_01"},
            Path(
                "book-program-portfolios-pnu20"
            ) / "maas-book-exact-geometry-artifacts.json",
        )

        self.assertEqual(passport["visual_hash"], visual_hash)
        self.assertEqual(row["visual_hash"], visual_hash)

    def test_archive_visual_hash_fails_closed_without_matching_certificate(self):
        from design.maas.geometry_language.executed_archive import (
            _manifest_row,
        )

        program = base_seed_program("block")
        compilation = compile_geometry_program(program)
        visual_hash = compilation.geometry_hash
        artifact = {
            "geometryProgram": program.to_dict(),
            "identity": {
                "programHash": program.program_hash(),
                "geometryHash": visual_hash,
            },
            "projectedVisualGeometryHash": visual_hash,
            "projectedVisualCertificate": {
                "visual_hash": "different-certificate",
            },
            "compilation": compilation.to_dict(include_mesh=False),
            "capacityAlternative": {},
            "hardGates": {"combinedHardPass": True},
            "executionPassport": {},
        }
        row = _manifest_row(
            1,
            {
                "trace_sequence_name": "uncertified-visual",
                "geometry_artifact": artifact,
            },
            {"variant_id": "maas_01"},
            Path(
                "book-program-portfolios-pnu20"
            ) / "maas-book-exact-geometry-artifacts.json",
        )

        self.assertEqual(row["visual_hash"], "")

    def test_archive_visual_hash_fails_closed_on_passport_mismatch(self):
        from design.maas.geometry_language.executed_archive import (
            _manifest_row,
        )

        program = base_seed_program("block")
        compilation = compile_geometry_program(program)
        visual_hash = compilation.geometry_hash
        artifact = {
            "geometryProgram": program.to_dict(),
            "identity": {
                "programHash": program.program_hash(),
                "geometryHash": visual_hash,
            },
            "projectedVisualGeometryHash": visual_hash,
            "projectedVisualCertificate": {
                "visual_hash": visual_hash,
            },
            "compilation": compilation.to_dict(include_mesh=False),
            "capacityAlternative": {},
            "hardGates": {"combinedHardPass": True},
            "executionPassport": {
                "program_hash": program.program_hash(),
                "geometry_hash": "stale-passport-geometry",
                "visual_hash": "stale-passport-visual",
            },
        }
        row = _manifest_row(
            1,
            {
                "trace_sequence_name": "passport-mismatch",
                "geometry_artifact": artifact,
            },
            {"variant_id": "maas_01"},
            Path("book-program-portfolios-pnu20")
            / "maas-book-exact-geometry-artifacts.json",
        )

        self.assertEqual(row["visual_hash"], "")

    def test_archive_floor_capacity_hash_flows_from_exact_passport(self):
        from design.maas.geometry_language.executed_archive import (
            _manifest_row,
        )

        program = base_seed_program("block")
        compilation = compile_geometry_program(program)
        visual_hash = compilation.geometry_hash
        passport = {
            "program_hash": program.program_hash(),
            "geometry_hash": visual_hash,
            "visual_hash": visual_hash,
            "final_legal_geometry_hash": visual_hash,
            "floor_capacity_plan_hash": "shared-floor-hash",
        }
        artifact = {
            "geometryProgram": program.to_dict(),
            "identity": {
                "programHash": program.program_hash(),
                "geometryHash": visual_hash,
            },
            "finalLegalGeometryHash": visual_hash,
            "projectedVisualGeometryHash": visual_hash,
            "projectedVisualCertificate": {
                "visual_hash": visual_hash,
            },
            "compilation": compilation.to_dict(include_mesh=False),
            "capacityAlternative": {},
            "hardGates": {"combinedHardPass": True},
            "executionPassport": passport,
        }

        row = _manifest_row(
            1,
            {
                "trace_sequence_name": "floor-hash-passport",
                "geometry_artifact": artifact,
            },
            {"variant_id": "maas_01"},
            Path("book-program-portfolios-pnu20")
            / "maas-book-exact-geometry-artifacts.json",
        )

        self.assertEqual(
            row["floor_capacity_plan_hash"],
            "shared-floor-hash",
        )

    def test_archive_program_hash_fails_closed_on_passport_mismatch(self):
        from design.maas.geometry_language.executed_archive import (
            _manifest_row,
        )

        program = base_seed_program("block")
        compilation = compile_geometry_program(program)
        visual_hash = compilation.geometry_hash
        artifact = {
            "geometryProgram": program.to_dict(),
            "identity": {
                "programHash": program.program_hash(),
                "geometryHash": visual_hash,
            },
            "projectedVisualGeometryHash": visual_hash,
            "projectedVisualCertificate": {
                "visual_hash": visual_hash,
            },
            "compilation": compilation.to_dict(include_mesh=False),
            "capacityAlternative": {},
            "hardGates": {"combinedHardPass": True},
            "executionPassport": {
                "program_hash": "stale-passport-program",
                "geometry_hash": visual_hash,
                "visual_hash": visual_hash,
            },
        }

        row = _manifest_row(
            1,
            {
                "trace_sequence_name": "program-hash-mismatch",
                "geometry_artifact": artifact,
            },
            {"variant_id": "maas_01"},
            Path("book-program-portfolios-pnu20")
            / "maas-book-exact-geometry-artifacts.json",
        )

        self.assertEqual(row["program_hash"], "")

    @staticmethod
    def _breadth_record(
        index,
        *,
        scope,
        body,
        roof,
        chassis,
        plan,
        capacity_band,
        score=0.5,
    ):
        return SimpleNamespace(
            key=f"breadth-{index:03d}",
            page_index=index // 64,
            base_scope=scope,
            genotype_family=f"genotype-{index % 9}",
            book_principle_kind=(
                "base_operative",
                "combination",
                "aggregation",
                "case_study",
            )[index % 4],
            book_principle_id=f"book-principle-{index % 12}",
            body_family=body,
            roof_family=roof,
            chassis_family=chassis,
            plan_family=plan,
            capacity_band=capacity_band,
            score=score,
            book_bind_pass=True,
            authored_compile_pass=True,
            legal_section_screen_pass=True,
            affine_screen_pass=True,
            approximate_capacity_pass=True,
        )

    def test_competition_breadth_visits_all_six_scopes(self):
        scheduler = CompetitionBreadthScheduler(target_count=20)
        cycle = scheduler.first_breadth_cycle()

        self.assertEqual(
            [record.base_scope for record in cycle],
            ["1/1", "1/2", "3/8", "1/4", "1/8", "1/16"],
        )
        self.assertGreater(scheduler.cheap_evaluation_limit, 36)

    def test_competition_breadth_real_records_visit_six_scopes_before_repeat(self):
        scopes = ("1/1", "1/2", "3/8", "1/4", "1/8", "1/16")
        records = [
            self._breadth_record(
                scope_index * 2 + cell_index,
                scope=scope,
                body=f"body-{scope_index}-{cell_index}",
                roof=f"roof-{scope_index}-{cell_index}",
                chassis=f"chassis-{scope_index}-{cell_index}",
                plan=f"plan-{scope_index}-{cell_index}",
                capacity_band=(
                    "spatial_reserve",
                    "balanced_yield",
                )[cell_index],
            )
            for scope_index, scope in enumerate(scopes)
            for cell_index in range(2)
        ]

        result = CompetitionBreadthScheduler(target_count=20).schedule_page(
            records,
            page_index=0,
        )

        self.assertEqual(
            [record.base_scope for record in result.exact_shortlist[:6]],
            list(scopes),
        )
        self.assertEqual(
            [record.base_scope for record in result.exact_shortlist[6:12]],
            list(scopes),
        )

    def test_competition_cheap_capacity_bands_rotate_by_page(self):
        carrier = program_seed_sequences("neighborhood_living")[0]
        program = base_seed_program("bar")
        seed = replace(
            carrier,
            notes=tuple((
                *carrier.notes,
                "geometry_program_payload="
                + json.dumps(
                    program.to_dict(),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )),
        )
        principles = tuple(
            build_book_language_registry()["principles"]
        )
        scopes = ("1/1", "1/2", "3/8", "1/4", "1/8", "1/16")

        first_page = candidate_generation._competition_cheap_candidate_records(
            (seed,) * 4,
            principles,
            book_probe_count=3,
            evaluation_limit=4,
            scope_labels=scopes,
            page_index=0,
            legal_sections=(),
            capacity_contract=None,
        )
        second_page = candidate_generation._competition_cheap_candidate_records(
            (seed,) * 4,
            principles,
            book_probe_count=3,
            evaluation_limit=4,
            scope_labels=scopes,
            page_index=1,
            legal_sections=(),
            capacity_contract=None,
        )

        self.assertEqual(
            [record.capacity_band for record in first_page],
            [
                "spatial_reserve",
                "balanced_yield",
                "brief_target",
                "maximum_feasible",
            ],
        )
        self.assertEqual(
            [record.capacity_band for record in second_page],
            [
                "balanced_yield",
                "brief_target",
                "maximum_feasible",
                "spatial_reserve",
            ],
        )

    def test_competition_cheap_geometry_uses_its_scheduled_capacity_target(self):
        carrier = program_seed_sequences("neighborhood_living")[0]
        program = base_seed_program("bar")
        seed = replace(
            carrier,
            notes=tuple((
                *carrier.notes,
                "geometry_program_payload="
                + json.dumps(
                    program.to_dict(),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "geometry_program_preservation_control=bar",
            )),
        )
        legal_sections = (
            Polygon(((0, 0), (10, 0), (10, 10), (0, 10))),
        ) * 4
        capacity_contract = {
            "requested_floors": 4,
            "requested_height_m": 12.0,
            "generation_site_area_m2": 100.0,
            "feasible_maximum_floor_area_m2": 400.0,
            "height_field_capacity_m2": 400.0,
            "minimum_utilization": 0.70,
            "target_utilization": 0.90,
            "bcr_adjusted_floor_areas_m2": [100.0] * 4,
            "target_floor_areas_m2": [90.0] * 4,
        }

        spatial = candidate_generation._competition_cheap_candidate_records(
            (seed,),
            tuple(build_book_language_registry()["principles"]),
            book_probe_count=3,
            evaluation_limit=12,
            scope_labels=("1/1", "1/2", "3/8", "1/4", "1/8", "1/16"),
            page_index=0,
            legal_sections=legal_sections,
            capacity_contract=capacity_contract,
        )[0]
        balanced = candidate_generation._competition_cheap_candidate_records(
            (seed,),
            tuple(build_book_language_registry()["principles"]),
            book_probe_count=3,
            evaluation_limit=12,
            scope_labels=("1/1", "1/2", "3/8", "1/4", "1/8", "1/16"),
            page_index=1,
            legal_sections=legal_sections,
            capacity_contract=capacity_contract,
        )[0]

        self.assertEqual(spatial.capacity_band, "spatial_reserve")
        self.assertEqual(spatial.cheap_target_utilization, 0.70)
        self.assertEqual(
            sum(spatial.cheap_target_floor_areas_m2),
            280.0,
        )
        self.assertEqual(balanced.capacity_band, "balanced_yield")
        self.assertEqual(balanced.cheap_target_utilization, 0.80)
        self.assertEqual(
            sum(balanced.cheap_target_floor_areas_m2),
            320.0,
        )

    def test_competition_cheap_screen_round_robins_parent_forms_before_repeats(self):
        carrier = program_seed_sequences("neighborhood_living")[0]
        seeds = []
        for index in range(20):
            program = replace(
                base_seed_program("bar"),
                metadata={
                    **base_seed_program("bar").metadata,
                    "family": f"round_robin_family_{index:02d}",
                },
            )
            seeds.append(replace(
                carrier,
                name=f"{carrier.name}_round_robin_{index:02d}",
                notes=tuple((
                    *carrier.notes,
                    "geometry_program_payload="
                    + json.dumps(
                        program.to_dict(),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )),
            ))

        records = candidate_generation._competition_cheap_candidate_records(
            tuple(seeds),
            tuple(build_book_language_registry()["principles"]),
            book_probe_count=3,
            evaluation_limit=20,
            scope_labels=("1/1", "1/2", "3/8", "1/4", "1/8", "1/16"),
            page_index=0,
            legal_sections=(),
            capacity_contract=None,
        )

        self.assertEqual(len(records), 20)
        self.assertEqual(
            {record.genotype_family for record in records},
            {f"round_robin_family_{index:02d}" for index in range(20)},
        )

        two_per_parent = (
            candidate_generation._competition_cheap_candidate_records(
                tuple(seeds),
                tuple(build_book_language_registry()["principles"]),
                book_probe_count=3,
                evaluation_limit=40,
                scope_labels=(
                    "1/1", "1/2", "3/8", "1/4", "1/8", "1/16",
                ),
                page_index=0,
                legal_sections=(),
                capacity_contract=None,
            )
        )
        self.assertEqual(len(two_per_parent), 40)
        self.assertEqual(
            Counter(
                record.genotype_family
                for record in two_per_parent
            ),
            Counter({
                f"round_robin_family_{index:02d}": 2
                for index in range(20)
            }),
        )

    def test_competition_exact_capacity_schedule_rotates_by_page(self):
        self.assertEqual(
            [
                candidate_generation._capacity_alternative_schedule_index(
                    evaluation_index=4,
                    diagnostic_evaluation_cap=0,
                    genotype_schedule_index=17,
                    competition_target_count=20,
                    page_index=page_index,
                )
                for page_index in range(4)
            ],
            [4, 5, 6, 7],
        )

    def test_competition_cheap_probe_matches_preservation_exact_probe(self):
        carrier = program_seed_sequences("neighborhood_living")[0]
        program = base_seed_program("bar")
        seed = replace(
            carrier,
            notes=tuple((
                *carrier.notes,
                "geometry_program_payload="
                + json.dumps(
                    program.to_dict(),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "geometry_program_preservation_control=bar",
            )),
        )

        records = candidate_generation._competition_cheap_candidate_records(
            (seed,),
            tuple(build_book_language_registry()["principles"]),
            book_probe_count=3,
            evaluation_limit=12,
            scope_labels=("1/1", "1/2", "3/8", "1/4", "1/8", "1/16"),
            page_index=0,
            legal_sections=(),
            capacity_contract=None,
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0].key,
            "0:book:operative:skew:5",
        )
        self.assertEqual(records[0].base_scope, "1/1")

    def test_competition_breadth_shortlist_is_bounded(self):
        scopes = ("1/1", "1/2", "3/8", "1/4", "1/8", "1/16")
        bodies = tuple(f"body-{index}" for index in range(5))
        roofs = tuple(f"roof-{index}" for index in range(7))
        chassis = tuple(f"chassis-{index}" for index in range(6))
        plans = tuple(f"plan-{index}" for index in range(5))
        capacity_bands = (
            "spatial_reserve",
            "balanced_yield",
            "brief_target",
            "maximum_feasible",
        )
        records = [
            self._breadth_record(
                index,
                scope=scopes[index % len(scopes)],
                body=bodies[index % len(bodies)],
                roof=roofs[index % len(roofs)],
                chassis=chassis[index % len(chassis)],
                plan=plans[index % len(plans)],
                capacity_band=capacity_bands[index % len(capacity_bands)],
                score=10.0 if index < 64 else 0.01,
            )
            for index in range(160)
        ]
        # Put the only copy of four required cells below every ordinary score.
        records.extend((
            self._breadth_record(
                900,
                scope="1/1",
                body="body-rare",
                roof="roof-0",
                chassis="chassis-0",
                plan="plan-0",
                capacity_band="spatial_reserve",
                score=-100.0,
            ),
            self._breadth_record(
                901,
                scope="1/2",
                body="body-0",
                roof="roof-rare",
                chassis="chassis-0",
                plan="plan-0",
                capacity_band="balanced_yield",
                score=-100.0,
            ),
            self._breadth_record(
                902,
                scope="3/8",
                body="body-0",
                roof="roof-0",
                chassis="chassis-rare",
                plan="plan-0",
                capacity_band="brief_target",
                score=-100.0,
            ),
            self._breadth_record(
                903,
                scope="1/4",
                body="body-0",
                roof="roof-0",
                chassis="chassis-0",
                plan="plan-rare",
                capacity_band="maximum_feasible",
                score=-100.0,
            ),
        ))

        result = CompetitionBreadthScheduler(target_count=20).schedule_page(
            records,
            page_index=0,
        )

        self.assertGreaterEqual(len(result.exact_shortlist), 48)
        self.assertLessEqual(len(result.exact_shortlist), 64)
        self.assertIn(
            "body-rare",
            {record.body_family for record in result.exact_shortlist},
        )
        self.assertIn(
            "roof-rare",
            {record.roof_family for record in result.exact_shortlist},
        )
        self.assertIn(
            "chassis-rare",
            {record.chassis_family for record in result.exact_shortlist},
        )
        self.assertIn(
            "plan-rare",
            {record.plan_family for record in result.exact_shortlist},
        )

    def test_competition_exact_required_keeps_valid_rare_unknown_and_drops_invalid_ast(self):
        valid_unknown = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="unit",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
                GeometryNode(
                    id="radial",
                    kind="pattern",
                    operator="radial_array",
                    inputs=("unit",),
                    parameters={
                        "count": 3,
                        "pivot": [0.0, 0.0, 0.0],
                    },
                ),
            ),
            root_id="radial",
            name="valid-exact-required",
        )
        exact_invalid = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="unit",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
                GeometryNode(
                    id="radial",
                    kind="pattern",
                    operator="radial_array",
                    inputs=("unit",),
                    parameters={"count": 3, "pivot": "invalid-pivot"},
                ),
            ),
            root_id="radial",
            name="exact-required-that-exact-compiler-rejects",
        )
        invalid_ast = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="unit",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
            ),
            root_id="missing-root",
            name="invalid-exact-required",
        )
        records = [
            self._breadth_record(
                index,
                scope=("1/1", "1/2", "3/8", "1/4", "1/8", "1/16")[
                    index % 6
                ],
                body=f"body-{index % 5}",
                roof=f"roof-{index % 7}",
                chassis=f"chassis-{index % 6}",
                plan=f"plan-{index % 5}",
                capacity_band=(
                    "spatial_reserve",
                    "balanced_yield",
                    "brief_target",
                    "maximum_feasible",
                )[index % 4],
            )
            for index in range(60)
        ]

        def exact_required_record(
            index,
            *,
            key,
            program,
            body,
            roof,
            chassis,
            plan,
        ):
            base = self._breadth_record(
                index,
                scope=("1/1", "1/2", "3/8", "1/4", "1/8", "1/16")[
                    index % 6
                ],
                body=body,
                roof=roof,
                chassis=chassis,
                plan=plan,
                capacity_band="spatial_reserve",
                score=-100.0,
            )
            return SimpleNamespace(**{
                **base.__dict__,
                "key": key,
                "typed_ast": program,
                "authored_compile_pass": False,
                "cheap_bounds_status": "unknown_bounds",
                "authored_validation_issue_codes": (
                    "cheap_bounds_unknown_operator",
                ),
                "exact_required": True,
                "legal_section_screen_pass": False,
                "affine_screen_pass": False,
                "approximate_capacity_pass": False,
            })

        valid_rare = exact_required_record(
            900,
            key="exact-required-valid-rare",
            program=valid_unknown,
            body="body-curved-rare",
            roof="roof-curved-rare",
            chassis="chassis-rare",
            plan="plan-radial-rare",
        )
        invalid_ast_record = exact_required_record(
            901,
            key="exact-required-invalid-ast",
            program=invalid_ast,
            body="body-invalid-rare",
            roof="roof-invalid-rare",
            chassis="chassis-invalid-rare",
            plan="plan-invalid-rare",
        )
        exact_invalid_record = exact_required_record(
            902,
            key="exact-required-exact-invalid",
            program=exact_invalid,
            body="body-exact-invalid-rare",
            roof="roof-exact-invalid-rare",
            chassis="chassis-exact-invalid-rare",
            plan="plan-exact-invalid-rare",
        )
        result = CompetitionBreadthScheduler(target_count=20).schedule_page(
            [*records, valid_rare, invalid_ast_record, exact_invalid_record],
            page_index=0,
        )
        screened = {
            record.key: record
            for record in result.cheap_screen_records
        }
        shortlist_keys = {
            record.key for record in result.exact_shortlist
        }

        self.assertFalse(
            screened["exact-required-valid-rare"].cheap_hard_pass
        )
        self.assertEqual(
            screened["exact-required-valid-rare"].failure_stage,
            "exact_required",
        )
        self.assertIn("exact-required-valid-rare", shortlist_keys)
        self.assertNotIn("exact-required-invalid-ast", shortlist_keys)
        self.assertEqual(
            screened["exact-required-invalid-ast"].failure_stage,
            "authored_compile",
        )
        self.assertIn("exact-required-exact-invalid", shortlist_keys)
        self.assertNotEqual(
            compile_geometry_program(exact_invalid).status,
            "compiled",
        )
        exact_hard_pass_keys = {
            record.key
            for record in result.exact_shortlist
            if (
                getattr(record, "typed_ast", None) is None
                or compile_geometry_program(record.typed_ast).status
                == "compiled"
            )
        }
        self.assertNotIn(
            "exact-required-exact-invalid",
            exact_hard_pass_keys,
        )

    def test_competition_exact_required_fills_bounded_192_record_shortlist_deterministically(self):
        valid_unknown = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="unit",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
                GeometryNode(
                    id="radial",
                    kind="pattern",
                    operator="radial_array",
                    inputs=("unit",),
                    parameters={
                        "count": 3,
                        "pivot": [0.0, 0.0, 0.0],
                    },
                ),
            ),
            root_id="radial",
            name="valid-192-exact-required",
        )
        scopes = ("1/1", "1/2", "3/8", "1/4", "1/8", "1/16")
        capacity_bands = (
            "spatial_reserve",
            "balanced_yield",
            "brief_target",
            "maximum_feasible",
        )
        records = []
        for index in range(192):
            base = self._breadth_record(
                index,
                scope=scopes[index % len(scopes)],
                body=(
                    "body-curved-rare"
                    if index == 191
                    else "body-profiled-rare"
                    if index == 190
                    else f"body-{index % 5}"
                ),
                roof=(
                    "roof-curved-rare"
                    if index == 191
                    else "roof-profiled-rare"
                    if index == 190
                    else f"roof-{index % 7}"
                ),
                chassis=(
                    "chassis-rare"
                    if index == 191
                    else f"chassis-{index % 6}"
                ),
                plan=(
                    "plan-winged-rare"
                    if index == 191
                    else f"plan-{index % 5}"
                ),
                capacity_band=capacity_bands[index % len(capacity_bands)],
                score=-100.0 if index == 191 else 1.0,
            )
            if index < 7:
                records.append(base)
                continue
            records.append(SimpleNamespace(**{
                **base.__dict__,
                "typed_ast": valid_unknown,
                "authored_compile_pass": False,
                "cheap_bounds_status": "unknown_bounds",
                "authored_validation_issue_codes": (
                    "cheap_bounds_unknown_operator",
                ),
                "exact_required": True,
                "legal_section_screen_pass": False,
                "affine_screen_pass": False,
                "approximate_capacity_pass": False,
            }))

        first = CompetitionBreadthScheduler(target_count=20).schedule_page(
            records,
            page_index=0,
        )
        second = CompetitionBreadthScheduler(target_count=20).schedule_page(
            records,
            page_index=0,
        )
        first_keys = [record.key for record in first.exact_shortlist]
        second_keys = [record.key for record in second.exact_shortlist]

        self.assertEqual(len(first.exact_shortlist), 64)
        self.assertEqual(first_keys, second_keys)
        self.assertEqual(
            sum(
                record.exact_required
                for record in first.cheap_screen_records
            ),
            185,
        )
        self.assertGreaterEqual(
            sum(
                bool(getattr(record, "exact_required", False))
                for record in first.exact_shortlist
            ),
            48,
        )
        self.assertIn("breadth-191", first_keys)
        self.assertIn("breadth-190", first_keys)
        self.assertEqual(
            set(scopes),
            {record.base_scope for record in first.exact_shortlist},
        )
        self.assertEqual(
            first.evidence()["exact_required_count"],
            185,
        )
        self.assertLessEqual(
            first.evidence()["exact_required_shortlist_count"],
            64,
        )

    def test_competition_breadth_reports_cell_deficits(self):
        records = [
            self._breadth_record(
                index,
                scope="1/1",
                body="body-only",
                roof="roof-only",
                chassis="chassis-only",
                plan="plan-only",
                capacity_band="spatial_reserve",
            )
            for index in range(12)
        ]

        result = CompetitionBreadthScheduler(target_count=20).schedule_page(
            records,
            page_index=0,
            required_cells={
                "body_family": {"body-only": 1, "body-missing": 1},
                "roof_family": {"roof-only": 1, "roof-missing": 1},
                "chassis_family": {
                    "chassis-only": 1,
                    "chassis-missing": 1,
                },
                "plan_family": {"plan-only": 1, "plan-missing": 1},
            },
        )
        deficits = {
            (deficit.axis, deficit.cell): deficit.shortfall
            for deficit in result.deficits
        }

        self.assertEqual(deficits[("body_family", "body-missing")], 1)
        self.assertEqual(deficits[("roof_family", "roof-missing")], 1)
        self.assertEqual(
            deficits[("chassis_family", "chassis-missing")],
            1,
        )
        self.assertEqual(deficits[("plan_family", "plan-missing")], 1)
        self.assertEqual(result.next_page_index, 1)

    def test_competition_breadth_reports_missing_distinct_family_cardinality(self):
        scopes = ("1/1", "1/2", "3/8", "1/4", "1/8", "1/16")
        capacity_bands = (
            "spatial_reserve",
            "balanced_yield",
            "brief_target",
            "maximum_feasible",
        )
        records = [
            self._breadth_record(
                index,
                scope=scopes[index % 6],
                body="one-body",
                roof="one-roof",
                chassis="one-chassis",
                plan="one-plan",
                capacity_band=capacity_bands[index % 4],
            )
            for index in range(60)
        ]

        result = CompetitionBreadthScheduler(target_count=20).schedule_page(
            records,
            page_index=0,
        )
        deficits = {
            (deficit.axis, deficit.cell): deficit.shortfall
            for deficit in result.deficits
        }

        self.assertEqual(deficits[("body_family", "__distinct__")], 4)
        self.assertEqual(deficits[("roof_family", "__distinct__")], 6)
        self.assertEqual(deficits[("chassis_family", "__distinct__")], 5)
        self.assertEqual(deficits[("plan_family", "__distinct__")], 4)

    def test_competition_breadth_compiles_each_typed_ast_once_in_cheap_screen(self):
        typed_ast = SimpleNamespace(program_hash=lambda: "shared-program")
        records = [
            SimpleNamespace(
                **{
                    **self._breadth_record(
                        index,
                        scope="1/1",
                        body="body",
                        roof="roof",
                        chassis="chassis",
                        plan="plan",
                        capacity_band="balanced_yield",
                    ).__dict__,
                    "typed_ast": typed_ast,
                },
            )
            for index in range(4)
        ]
        compile_count = 0

        def compile_ast(_record):
            nonlocal compile_count
            compile_count += 1
            return SimpleNamespace(status="compiled")

        screened = cheap_screen_records(
            records,
            compile_typed_ast=compile_ast,
        )

        self.assertEqual(compile_count, 1)
        self.assertTrue(all(record.cheap_hard_pass for record in screened))

    def test_competition_candidate_specific_cheap_geometry_filters_only_protruding_ast(self):
        good_program = base_seed_program("block")
        bad_program = replace(
            good_program,
            name="bad-slender-program",
            nodes=tuple(
                replace(
                    node,
                    parameters={"vector": [40.0, 1.0, 1.0]},
                )
                if node.kind == "transform" and node.operator == "scale"
                else node
                for node in good_program.nodes
            ),
        )
        legal_sections = (
            Polygon(((0, 0), (10, 0), (10, 10), (0, 10))),
            Polygon(((0, 0), (10, 0), (10, 10), (0, 10))),
        )
        good = candidate_generation._cheap_typed_ast_candidate_evidence(
            good_program,
            legal_sections=legal_sections,
            target_floor_areas_m2=(80.0, 80.0),
        )
        bad = candidate_generation._cheap_typed_ast_candidate_evidence(
            bad_program,
            legal_sections=legal_sections,
            target_floor_areas_m2=(80.0, 80.0),
        )

        self.assertTrue(good["authored_compile_pass"])
        self.assertTrue(good["legal_section_screen_pass"])
        self.assertTrue(good["affine_screen_pass"])
        self.assertTrue(good["approximate_capacity_pass"])
        self.assertGreater(good["approximate_capacity_ratio"], 1.0)
        self.assertTrue(bad["authored_compile_pass"])
        self.assertFalse(bad["legal_section_screen_pass"])
        self.assertFalse(bad["affine_screen_pass"])
        self.assertFalse(bad["approximate_capacity_pass"])
        self.assertLess(bad["approximate_capacity_ratio"], 0.1)
        self.assertNotEqual(
            good["conservative_footprint_bounds"],
            bad["conservative_footprint_bounds"],
        )
        records = [
            SimpleNamespace(
                **{
                    **self._breadth_record(
                        index,
                        scope=("1/1", "1/2")[index],
                        body=f"body-{index}",
                        roof=f"roof-{index}",
                        chassis=f"chassis-{index}",
                        plan=f"plan-{index}",
                        capacity_band="brief_target",
                    ).__dict__,
                    **evidence,
                },
            )
            for index, evidence in enumerate((good, bad))
        ]
        screened = cheap_screen_records(records)

        self.assertTrue(screened[0].cheap_hard_pass)
        self.assertFalse(screened[1].cheap_hard_pass)
        self.assertEqual(
            screened[1].failure_stage,
            "legal_section_screen",
        )

    def test_competition_cheap_bounds_enclose_real_swept_bar_and_reject_shallow_site(self):
        program = next(
            item for item in architectural_shape_programs()
            if item.name == "shape_16_swept_curved_bar"
        )
        compilation = compile_geometry_program(program)
        exact_width = (
            max(vertex[0] for vertex in compilation.vertices)
            - min(vertex[0] for vertex in compilation.vertices)
        )
        exact_depth = (
            max(vertex[1] for vertex in compilation.vertices)
            - min(vertex[1] for vertex in compilation.vertices)
        )

        bounds = candidate_generation._cheap_ast_bounds(program)
        self.assertIsNotNone(bounds)
        cheap_width = bounds[2] - bounds[0]
        cheap_depth = bounds[3] - bounds[1]
        self.assertGreaterEqual(cheap_width + 1e-9, exact_width)
        self.assertGreaterEqual(cheap_depth + 1e-9, exact_depth)

        evidence = candidate_generation._cheap_typed_ast_candidate_evidence(
            program,
            legal_sections=(
                Polygon(((0, 0), (12, 0), (12, 2.4), (0, 2.4))),
            ),
            target_floor_areas_m2=(28.0,),
        )
        self.assertTrue(evidence["authored_compile_pass"])
        self.assertFalse(evidence["legal_section_screen_pass"])
        self.assertFalse(evidence["affine_screen_pass"])
        self.assertFalse(evidence["approximate_capacity_pass"])

    def test_competition_cheap_bounds_include_matrix4_z_to_xy_mixing(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="unit",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
                GeometryNode(
                    id="mixed",
                    kind="transform",
                    operator="matrix4",
                    inputs=("unit",),
                    parameters={
                        "matrix4": (
                            (1.0, 0.0, 10.0, 0.0),
                            (0.0, 1.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0, 0.0),
                            (0.0, 0.0, 0.0, 1.0),
                        ),
                    },
                ),
            ),
            root_id="mixed",
            name="z-to-x-adversary",
        )

        bounds = candidate_generation._cheap_ast_bounds(program)
        self.assertIsNotNone(bounds)
        self.assertGreaterEqual(bounds[2] - bounds[0], 11.0)
        evidence = candidate_generation._cheap_typed_ast_candidate_evidence(
            program,
            legal_sections=(
                Polygon(((0, 0), (2, 0), (2, 1), (0, 1))),
            ),
            target_floor_areas_m2=(1.0,),
        )
        self.assertFalse(evidence["legal_section_screen_pass"])

    def test_competition_cheap_bounds_enclose_sweep_path_and_loft_profiles(self):
        programs = (
            GeometryProgram(
                nodes=(GeometryNode(
                    id="sweep",
                    kind="primitive",
                    operator="sweep",
                    parameters={
                        "path": [[0, 0, 0], [5, 7, 1], [9, -2, 2]],
                        "profile_width": 2.0,
                        "profile_height": 3.0,
                    },
                ),),
                root_id="sweep",
                name="adversarial-sweep-path",
            ),
            GeometryProgram(
                nodes=(GeometryNode(
                    id="loft",
                    kind="primitive",
                    operator="loft",
                    parameters={"profiles": [
                        {"z": 0, "points": [[-3, -2], [3, -2], [3, 2], [-3, 2]]},
                        {"z": 8, "points": [[-7, -1], [6, -1], [6, 4], [-7, 4]]},
                    ]},
                ),),
                root_id="loft",
                name="adversarial-loft-profiles",
            ),
        )

        for program in programs:
            with self.subTest(program=program.name):
                compilation = compile_geometry_program(program)
                bounds = candidate_generation._cheap_ast_bounds(program)
                self.assertEqual(compilation.status, "compiled")
                self.assertIsNotNone(bounds)
                self.assertLessEqual(
                    bounds[0],
                    min(vertex[0] for vertex in compilation.vertices) + 1e-9,
                )
                self.assertLessEqual(
                    bounds[1],
                    min(vertex[1] for vertex in compilation.vertices) + 1e-9,
                )
                self.assertGreaterEqual(
                    bounds[2] + 1e-9,
                    max(vertex[0] for vertex in compilation.vertices),
                )
                self.assertGreaterEqual(
                    bounds[3] + 1e-9,
                    max(vertex[1] for vertex in compilation.vertices),
                )

    def test_competition_cheap_bounds_fail_closed_for_unproved_macro(self):
        base = base_seed_program("block")
        program = replace(
            base,
            name="unknown-bounds-macro",
            root_id="unknown_macro",
            nodes=base.nodes + (
                GeometryNode(
                    id="unknown_macro",
                    kind="macro",
                    operator="boundary_expand",
                    inputs=(base.root_id,),
                    parameters={"distance_ratio": 25.0},
                ),
            ),
        )

        evidence = candidate_generation._cheap_typed_ast_candidate_evidence(
            program,
            legal_sections=(
                Polygon(((0, 0), (10, 0), (10, 10), (0, 10))),
            ),
            target_floor_areas_m2=(10.0,),
        )
        self.assertFalse(evidence["authored_compile_pass"])
        self.assertEqual(evidence["cheap_bounds_status"], "unknown_bounds")
        self.assertTrue(evidence["typed_ast_valid"])
        self.assertTrue(evidence["exact_required"])
        self.assertIn(
            "cheap_bounds_unknown_operator",
            evidence["authored_validation_issue_codes"],
        )

    def test_competition_cheap_bounds_enclose_intersect_related_macro(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="unit",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
                GeometryNode(
                    id="scaled",
                    kind="transform",
                    operator="scale",
                    inputs=("unit",),
                    parameters={"vector": [10.0, 2.0, 3.0]},
                ),
                GeometryNode(
                    id="cross",
                    kind="macro",
                    operator="intersect_related",
                    inputs=("scaled",),
                    parameters={},
                ),
            ),
            root_id="cross",
            name="intersect-related-envelope-adversary",
        )

        compilation = compile_geometry_program(program)
        bounds = candidate_generation._cheap_ast_bounds(program)

        self.assertEqual(compilation.status, "compiled")
        self.assertIsNotNone(bounds)
        self.assertLessEqual(
            bounds[0], min(vertex[0] for vertex in compilation.vertices) + 1e-9
        )
        self.assertLessEqual(
            bounds[1], min(vertex[1] for vertex in compilation.vertices) + 1e-9
        )
        self.assertGreaterEqual(
            bounds[2] + 1e-9, max(vertex[0] for vertex in compilation.vertices)
        )
        self.assertGreaterEqual(
            bounds[3] + 1e-9, max(vertex[1] for vertex in compilation.vertices)
        )

    def test_competition_cheap_bounds_match_inflate_minimum_clamp(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="unit",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
                GeometryNode(
                    id="inflated",
                    kind="modifier",
                    operator="inflate",
                    inputs=("unit",),
                    parameters={"axis": "z", "middle_scale": 0.5},
                ),
            ),
            root_id="inflated",
            name="inflate-minimum-clamp-adversary",
        )

        compilation = compile_geometry_program(program)
        bounds = candidate_generation._cheap_ast_bounds(program)

        self.assertEqual(compilation.status, "compiled")
        self.assertIsNotNone(bounds)
        self.assertLessEqual(
            bounds[0], min(vertex[0] for vertex in compilation.vertices) + 1e-9
        )
        self.assertLessEqual(
            bounds[1], min(vertex[1] for vertex in compilation.vertices) + 1e-9
        )
        self.assertGreaterEqual(
            bounds[2] + 1e-9, max(vertex[0] for vertex in compilation.vertices)
        )
        self.assertGreaterEqual(
            bounds[3] + 1e-9, max(vertex[1] for vertex in compilation.vertices)
        )

    def test_competition_cheap_bounds_enclose_taper_about_external_pivot(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="unit",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
                GeometryNode(
                    id="tapered",
                    kind="modifier",
                    operator="taper",
                    inputs=("unit",),
                    parameters={
                        "axis": "z",
                        "start_scale": [0.5, 0.5],
                        "end_scale": [0.5, 0.5],
                        "pivot": [100.0, 100.0, 0.0],
                    },
                ),
            ),
            root_id="tapered",
            name="taper-external-pivot-adversary",
        )

        compilation = compile_geometry_program(program)
        bounds = candidate_generation._cheap_ast_bounds(program)

        self.assertEqual(compilation.status, "compiled")
        self.assertIsNotNone(bounds)
        self.assertLessEqual(
            bounds[0], min(vertex[0] for vertex in compilation.vertices) + 1e-9
        )
        self.assertLessEqual(
            bounds[1], min(vertex[1] for vertex in compilation.vertices) + 1e-9
        )
        self.assertGreaterEqual(
            bounds[2] + 1e-9, max(vertex[0] for vertex in compilation.vertices)
        )
        self.assertGreaterEqual(
            bounds[3] + 1e-9, max(vertex[1] for vertex in compilation.vertices)
        )

    def test_competition_cheap_bounds_enclose_twist_about_external_pivot(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="unit",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
                GeometryNode(
                    id="twisted",
                    kind="modifier",
                    operator="twist",
                    inputs=("unit",),
                    parameters={
                        "axis": "z",
                        "angle_degrees": 90.0,
                        "pivot": [100.0, 100.0, 0.0],
                    },
                ),
            ),
            root_id="twisted",
            name="twist-external-pivot-adversary",
        )

        compilation = compile_geometry_program(program)
        bounds = candidate_generation._cheap_ast_bounds(program)

        self.assertEqual(compilation.status, "compiled")
        self.assertIsNotNone(bounds)
        self.assertLessEqual(
            bounds[0], min(vertex[0] for vertex in compilation.vertices) + 1e-9
        )
        self.assertLessEqual(
            bounds[1], min(vertex[1] for vertex in compilation.vertices) + 1e-9
        )
        self.assertGreaterEqual(
            bounds[2] + 1e-9, max(vertex[0] for vertex in compilation.vertices)
        )
        self.assertGreaterEqual(
            bounds[3] + 1e-9, max(vertex[1] for vertex in compilation.vertices)
        )

    def test_competition_cheap_bounds_fail_closed_for_recomposition_connector(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="left",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
                GeometryNode(
                    id="right_seed",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
                ),
                GeometryNode(
                    id="right",
                    kind="transform",
                    operator="translate",
                    inputs=("right_seed",),
                    parameters={"vector": [5.0, 0.0, 0.0]},
                ),
                GeometryNode(
                    id="joined",
                    kind="boolean",
                    operator="union",
                    inputs=("left", "right"),
                    provenance={"book_verb": "recompose_book_scope"},
                ),
            ),
            root_id="joined",
            name="recomposition-connector-envelope-adversary",
        )

        compilation = compile_geometry_program(program)
        bounds = candidate_generation._cheap_ast_bounds(program)
        exact = (
            min(vertex[0] for vertex in compilation.vertices),
            min(vertex[1] for vertex in compilation.vertices),
            max(vertex[0] for vertex in compilation.vertices),
            max(vertex[1] for vertex in compilation.vertices),
        )

        self.assertEqual(compilation.status, "compiled")
        self.assertTrue(
            bounds is None
            or (
                bounds[0] <= exact[0] + 1e-9
                and bounds[1] <= exact[1] + 1e-9
                and bounds[2] + 1e-9 >= exact[2]
                and bounds[3] + 1e-9 >= exact[3]
            ),
            (bounds, exact),
        )

    def test_competition_cheap_bounds_fail_closed_for_loose_center_pivot_chain(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="box",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 10.0, "depth": 2.0, "height": 2.0},
                ),
                GeometryNode(
                    id="subset",
                    kind="modifier",
                    operator="clip_fraction",
                    inputs=("box",),
                    parameters={"fraction": 0.2, "axis": "x"},
                ),
                GeometryNode(
                    id="scaled",
                    kind="transform",
                    operator="scale",
                    inputs=("subset",),
                    parameters={
                        "vector": [0.5, 0.5, 0.5],
                        "pivot": "center",
                    },
                ),
            ),
            root_id="scaled",
            name="loose-center-pivot-envelope-adversary",
        )

        compilation = compile_geometry_program(program)
        bounds = candidate_generation._cheap_ast_bounds(program)
        evidence = candidate_generation._cheap_typed_ast_candidate_evidence(
            program,
            legal_sections=(
                Polygon(((0, 0), (12, 0), (12, 3), (0, 3))),
            ),
            target_floor_areas_m2=(1.0,),
        )

        self.assertEqual(compilation.status, "compiled")
        self.assertIsNone(bounds)
        self.assertEqual(evidence["cheap_bounds_status"], "unknown_bounds")

    def test_competition_cheap_bounds_fail_closed_for_bend_after_loose_selection(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="box",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 10.0, "depth": 4.0, "height": 6.0},
                ),
                GeometryNode(
                    id="subset",
                    kind="modifier",
                    operator="book_base_volume",
                    inputs=("box",),
                    parameters={
                        "label": "1/2",
                        "orientation": "vertical",
                    },
                ),
                GeometryNode(
                    id="bent",
                    kind="modifier",
                    operator="bend",
                    inputs=("subset",),
                    parameters={"axis": "x", "angle_degrees": 90.0},
                ),
            ),
            root_id="bent",
            name="bend-after-loose-selection-envelope-adversary",
        )

        compilation = compile_geometry_program(program)
        bounds = candidate_generation._cheap_ast_bounds(program)

        self.assertEqual(compilation.status, "compiled")
        self.assertIsNone(bounds)

    def test_competition_cheap_bounds_fail_closed_for_derived_stack_spacing_after_loose_selection(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="box",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 10.0},
                ),
                GeometryNode(
                    id="subset",
                    kind="modifier",
                    operator="book_base_volume",
                    inputs=("box",),
                    parameters={
                        "label": "1/16",
                        "orientation": "long_axis",
                    },
                ),
                GeometryNode(
                    id="stacked",
                    kind="pattern",
                    operator="stack",
                    inputs=("subset",),
                    parameters={
                        "count": 5,
                        "shift_per_level": [0.0, 0.0, -15.0],
                    },
                ),
                GeometryNode(
                    id="mixed",
                    kind="transform",
                    operator="matrix4",
                    inputs=("stacked",),
                    parameters={
                        "matrix4": (
                            (1.0, 0.0, 1.0, 0.0),
                            (0.0, 1.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0, 0.0),
                            (0.0, 0.0, 0.0, 1.0),
                        ),
                    },
                ),
            ),
            root_id="mixed",
            name="derived-stack-spacing-envelope-adversary",
        )

        compilation = compile_geometry_program(program)
        bounds = candidate_generation._cheap_ast_bounds(program)
        evidence = candidate_generation._cheap_typed_ast_candidate_evidence(
            program,
            legal_sections=(
                Polygon(((0, 0), (40, 0), (40, 2), (0, 2))),
            ),
            target_floor_areas_m2=(20.0,),
        )
        exact_width = (
            max(vertex[0] for vertex in compilation.vertices)
            - min(vertex[0] for vertex in compilation.vertices)
        )

        self.assertEqual(compilation.status, "compiled")
        self.assertAlmostEqual(exact_width, 53.5, places=6)
        self.assertIsNone(bounds)
        self.assertEqual(evidence["cheap_bounds_status"], "unknown_bounds")
        self.assertFalse(evidence["authored_compile_pass"])

    def test_competition_cheap_bounds_keep_explicit_stack_spacing_after_loose_selection(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    id="box",
                    kind="primitive",
                    operator="box",
                    parameters={"width": 1.0, "depth": 1.0, "height": 10.0},
                ),
                GeometryNode(
                    id="subset",
                    kind="modifier",
                    operator="book_base_volume",
                    inputs=("box",),
                    parameters={
                        "label": "1/16",
                        "orientation": "long_axis",
                    },
                ),
                GeometryNode(
                    id="stacked",
                    kind="pattern",
                    operator="stack",
                    inputs=("subset",),
                    parameters={
                        "count": 5,
                        "spacing": 2.0,
                        "shift_per_level": [0.0, 0.0, -15.0],
                    },
                ),
                GeometryNode(
                    id="mixed",
                    kind="transform",
                    operator="matrix4",
                    inputs=("stacked",),
                    parameters={
                        "matrix4": (
                            (1.0, 0.0, 1.0, 0.0),
                            (0.0, 1.0, 0.0, 0.0),
                            (0.0, 0.0, 1.0, 0.0),
                            (0.0, 0.0, 0.0, 1.0),
                        ),
                    },
                ),
            ),
            root_id="mixed",
            name="explicit-stack-spacing-envelope-control",
        )

        compilation = compile_geometry_program(program)
        bounds = candidate_generation._cheap_ast_bounds(program)
        exact = (
            min(vertex[0] for vertex in compilation.vertices),
            min(vertex[1] for vertex in compilation.vertices),
            max(vertex[0] for vertex in compilation.vertices),
            max(vertex[1] for vertex in compilation.vertices),
        )

        self.assertEqual(compilation.status, "compiled")
        self.assertIsNotNone(bounds)
        assert bounds is not None
        self.assertLessEqual(bounds[0], exact[0] + 1e-9)
        self.assertLessEqual(bounds[1], exact[1] + 1e-9)
        self.assertGreaterEqual(bounds[2] + 1e-9, exact[2])
        self.assertGreaterEqual(bounds[3] + 1e-9, exact[3])

    def test_competition_generation_budget_uses_six_scopes_and_bounded_exact_page(self):
        budget = candidate_generation.competition_breadth_generation_budget(
            20,
        )

        self.assertEqual(
            budget["scope_labels"],
            ("1/1", "1/2", "3/8", "1/4", "1/8", "1/16"),
        )
        self.assertGreater(budget["cheap_evaluation_limit"], 36)
        self.assertEqual(budget["exact_shortlist_minimum"], 48)
        self.assertEqual(budget["exact_shortlist_maximum"], 64)
        self.assertEqual(
            candidate_generation.competition_breadth_generation_budget(10),
            {},
        )
        self.assertEqual(
            candidate_generation.resolve_competition_breadth_generation_budget(
                target_count=20,
                recursive_only=True,
                explicit_diagnostic_budget=False,
                smoke_mode=True,
            ),
            {},
        )
        self.assertEqual(
            candidate_generation.resolve_competition_breadth_generation_budget(
                target_count=20,
                recursive_only=True,
                explicit_diagnostic_budget=True,
                smoke_mode=False,
            ),
            {},
        )
        self.assertEqual(
            candidate_generation.resolve_competition_breadth_generation_budget(
                target_count=20,
                recursive_only=False,
                explicit_diagnostic_budget=False,
                smoke_mode=False,
            ),
            {},
        )
        self.assertEqual(
            candidate_generation.resolve_competition_breadth_generation_budget(
                target_count=10,
                recursive_only=True,
                explicit_diagnostic_budget=False,
                smoke_mode=False,
            ),
            {},
        )
        self.assertIsNone(
            candidate_generation._recursive_principle_schedule_limit(
                evaluation_cap=192,
                explicit_diagnostic_budget=False,
            ),
        )
        self.assertEqual(
            candidate_generation._recursive_principle_schedule_limit(
                evaluation_cap=36,
                explicit_diagnostic_budget=True,
            ),
            1,
        )

    def test_competition_pre_exact_shortlist_protects_rare_late_quota_witness(self):
        records = [
            self._breadth_record(
                index,
                scope=("1/1", "1/2", "3/8", "1/4", "1/8", "1/16")[
                    index % 6
                ],
                body=f"body-{index % 5}",
                roof=f"roof-{index % 7}",
                chassis=f"chassis-{index % 6}",
                plan=f"plan-{index % 5}",
                capacity_band=(
                    "spatial_reserve",
                    "balanced_yield",
                    "brief_target",
                    "maximum_feasible",
                )[index % 4],
                score=1.0,
            )
            for index in range(192)
        ]
        records[-1] = SimpleNamespace(
            **{
                **records[-1].__dict__,
                "key": "late-rare-book-body",
                "body_family": "body-rare",
                "book_principle_kind": "rare-book-kind",
                "book_principle_id": "book-principle-rare",
                "score": -100.0,
            },
        )

        selected_keys, schedule = (
            candidate_generation._competition_pre_exact_shortlist(
                records,
                page_index=0,
                target_count=20,
            )
        )

        self.assertEqual(len(selected_keys), 64)
        self.assertIn("late-rare-book-body", selected_keys)
        self.assertIn(
            "body-rare",
            {
                record.body_family
                for record in schedule.exact_shortlist
            },
        )
        self.assertIn(
            "book-principle-rare",
            {
                record.book_principle_id
                for record in schedule.exact_shortlist
            },
        )

    def test_competition_replenishment_advances_page_until_exact_reserve_is_feasible(self):
        records = [
            self._breadth_record(
                index,
                scope="1/1",
                body="body-only",
                roof="roof-only",
                chassis="chassis-only",
                plan="plan-only",
                capacity_band="spatial_reserve",
            )
            for index in range(12)
        ]
        scheduled = CompetitionBreadthScheduler(
            target_count=20,
        ).schedule_page(records, page_index=2)

        pending = (
            portfolio_replenishment.competition_breadth_replenishment_state(
                scheduled,
                exact_hard_pass_count=23,
                feasible_portfolio=False,
            )
        )
        complete = (
            portfolio_replenishment.competition_breadth_replenishment_state(
                scheduled,
                exact_hard_pass_count=24,
                feasible_portfolio=True,
            )
        )
        failed_exact = (
            portfolio_replenishment.competition_breadth_replenishment_state(
                scheduled,
                exact_hard_pass_count=23,
                feasible_portfolio=False,
                downstream_stage_failure_counts={
                    "exact_csg": 2,
                    "parking": 1,
                    "hash_bridge": 3,
                },
            )
        )

        self.assertFalse(pending["stop"])
        self.assertEqual(pending["next_page_index"], 3)
        self.assertTrue(pending["breadth_deficits"])
        self.assertEqual(
            pending["stage_failure_counts"],
            {
                "affine_screen": 0,
                "authored_compile": 0,
                "book_bind": 0,
                "capacity": 0,
                "exact_csg": 0,
                "hash_bridge": 0,
                "legal_section_screen": 0,
                "parking": 0,
            },
        )
        self.assertTrue(complete["stop"])
        self.assertIsNone(complete["next_page_index"])
        self.assertEqual(
            failed_exact["stage_failure_counts"]["exact_csg"],
            2,
        )
        self.assertEqual(
            failed_exact["stage_failure_counts"]["parking"],
            1,
        )
        self.assertEqual(
            failed_exact["stage_failure_counts"]["hash_bridge"],
            3,
        )
        self.assertFalse(
            CompetitionBreadthScheduler.exact_pool_ready(
                exact_hard_pass_count=23,
                feasible_portfolio=True,
            ),
        )
        self.assertTrue(
            CompetitionBreadthScheduler.exact_pool_ready(
                exact_hard_pass_count=24,
                feasible_portfolio=True,
            ),
        )
        self.assertTrue(
            CompetitionBreadthScheduler.exact_pool_ready(
                exact_hard_pass_count=28,
                feasible_portfolio=True,
            ),
        )
        self.assertFalse(
            CompetitionBreadthScheduler.exact_pool_ready(
                exact_hard_pass_count=29,
                feasible_portfolio=True,
            ),
        )

    def test_competition_exact_reserve_compacts_above_28_and_drives_stop(self):
        pool = [
            SimpleNamespace(key=f"candidate-{index}", score=40 - index)
            for index in range(40)
        ]
        selected = pool[:20]

        reserve = portfolio_replenishment.competition_exact_hard_pass_reserve(
            pool,
            selected=selected,
        )

        self.assertEqual(len(reserve), 28)
        self.assertTrue(all(candidate in reserve for candidate in selected))
        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                selected_count=20,
                selected_scope_count=6,
                target_count=20,
                required_scope_count=6,
                cycles_run=1,
                cycle_budget=3,
                exact_hard_pass_count=28,
                feasible_portfolio=True,
            ),
            "competition_exact_reserve_feasible",
        )
        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                selected_count=20,
                selected_scope_count=6,
                target_count=20,
                required_scope_count=6,
                cycles_run=1,
                cycle_budget=3,
                exact_hard_pass_count=23,
                feasible_portfolio=True,
            ),
            "",
        )

    def test_competition_exact_reserve_does_not_slice_infeasible_pool(self):
        pool = [
            SimpleNamespace(key=f"candidate-{index}", score=40 - index)
            for index in range(40)
        ]

        reserve = portfolio_replenishment.competition_exact_hard_pass_reserve(
            pool,
            selected=[],
        )

        self.assertEqual(reserve, pool)

    def test_competition_replenishment_sends_at_most_64_candidates_to_exact_gates(self):
        candidates = [
            SimpleNamespace(
                key=f"candidate-{index:03d}",
                score=1.0 - index * 0.001,
                scope=(
                    "1/1",
                    "1/2",
                    "3/8",
                    "1/4",
                    "1/8",
                    "1/16",
                )[index % 6],
                genotype=f"genotype-{index % 9}",
                principle_kind=(
                    "base_operative",
                    "combination",
                    "aggregation",
                    "case_study",
                )[index % 4],
                body=f"body-{index % 5}",
                roof=f"roof-{index % 7}",
                chassis=f"chassis-{index % 6}",
                plan=f"plan-{index % 5}",
                capacity_band=(
                    "spatial_reserve",
                    "balanced_yield",
                    "brief_target",
                    "maximum_feasible",
                )[index % 4],
            )
            for index in range(140)
        ]
        with (
            patch.object(
                portfolio_replenishment,
                "_scope_key",
                side_effect=lambda item: item.scope,
            ),
            patch.object(
                portfolio_replenishment,
                "_geometry_program_family",
                side_effect=lambda item: item.genotype,
            ),
            patch.object(
                portfolio_replenishment,
                "_solid_morphology_metrics",
                side_effect=lambda item: {
                    "body_phenotype": item.body,
                    "phenotype": item.body,
                },
            ),
            patch.object(
                portfolio_replenishment,
                "_roof_archetype",
                side_effect=lambda item: item.roof,
            ),
            patch.object(
                portfolio_replenishment,
                "_chassis_family",
                side_effect=lambda item: item.chassis,
            ),
            patch.object(
                portfolio_replenishment,
                "_plan_family",
                side_effect=lambda item: item.plan,
            ),
            patch.object(
                portfolio_replenishment,
                "_capacity_alternative_key",
                side_effect=lambda item: item.capacity_band,
            ),
        ):
            shortlist, schedule = (
                portfolio_replenishment.competition_breadth_shortlist_candidates(
                    candidates,
                    page_index=4,
                    target_count=20,
                )
            )

        self.assertEqual(len(shortlist), 64)
        self.assertEqual(len(schedule.exact_shortlist), 64)
        self.assertTrue(all(candidate in candidates for candidate in shortlist))

    def test_qd_archive_protects_each_solver_quota_cell(self):
        candidates = [
            SimpleNamespace(
                key=f"candidate-{index}",
                score=100.0 - index,
                scope="1/1",
                phenotype="common-body",
                body="common-body",
                roof="common-roof",
                chassis="common-chassis",
                plan="common-plan",
                family="common-genotype",
                principle_id="book:common",
            )
            for index in range(40)
        ]
        candidates.extend((
            SimpleNamespace(
                **{
                    **candidates[0].__dict__,
                    "key": "rare-body",
                    "score": -100.0,
                    "body": "rare-body",
                },
            ),
            SimpleNamespace(
                **{
                    **candidates[0].__dict__,
                    "key": "rare-roof",
                    "score": -100.0,
                    "roof": "rare-roof",
                },
            ),
            SimpleNamespace(
                **{
                    **candidates[0].__dict__,
                    "key": "rare-chassis",
                    "score": -100.0,
                    "chassis": "rare-chassis",
                },
            ),
            SimpleNamespace(
                **{
                    **candidates[0].__dict__,
                    "key": "rare-plan",
                    "score": -100.0,
                    "plan": "rare-plan",
                },
            ),
        ))
        with (
            patch.object(
                quality_diversity_archive,
                "_fingerprint",
                side_effect=lambda item: (item.key,),
            ),
            patch.object(
                quality_diversity_archive,
                "_scope_key",
                side_effect=lambda item: item.scope,
            ),
            patch.object(
                quality_diversity_archive,
                "_solid_morphology_metrics",
                side_effect=lambda item: {
                    "phenotype": item.phenotype,
                    "body_phenotype": item.body,
                },
            ),
            patch.object(
                quality_diversity_archive,
                "_roof_archetype",
                side_effect=lambda item: item.roof,
            ),
            patch.object(
                quality_diversity_archive,
                "_chassis_family",
                side_effect=lambda item: item.chassis,
            ),
            patch.object(
                quality_diversity_archive,
                "_plan_family",
                side_effect=lambda item: item.plan,
            ),
            patch.object(
                quality_diversity_archive,
                "_geometry_program_family",
                side_effect=lambda item: item.family,
            ),
            patch.object(
                quality_diversity_archive,
                "_capacity_alternative_key",
                return_value="balanced_yield",
            ),
            patch.object(
                quality_diversity_archive,
                "_capacity_target_gate",
                return_value=True,
            ),
            patch.object(
                quality_diversity_archive,
                "_capacity_minimum_gate",
                return_value=True,
            ),
            patch.dict(
                os.environ,
                {
                    "MAAS_QD_ELITES_PER_CELL": "1",
                    "MAAS_QD_ARCHIVE_MAX_SIZE": "32",
                },
            ),
        ):
            retained = quality_diversity_archive.map_elites_archive(
                candidates,
            )

        self.assertIn("rare-body", {item.body for item in retained})
        self.assertIn("rare-roof", {item.roof for item in retained})
        self.assertIn("rare-chassis", {item.chassis for item in retained})
        self.assertIn("rare-plan", {item.plan for item in retained})

    @staticmethod
    def _certified_prism_mesh_source(
        name,
        layers,
        *,
        geometry_program_nodes=(),
        projection_mode="authored_affine_preserved",
        proxy_layers=None,
        proxy_footprint=None,
    ):
        surfaces = []
        maximum_height = max(top for _footprint, _bottom, top in layers)
        for layer_index, (footprint, bottom, top) in enumerate(layers):
            role = f"certified_layer_{layer_index:02d}"
            triangles = [
                triangle
                for triangle in triangulate(footprint)
                if footprint.covers(triangle.representative_point())
            ]
            for triangle in triangles:
                coordinates = tuple(triangle.exterior.coords)[:3]
                for face_z, reverse in ((bottom, True), (top, False)):
                    vertices = tuple(
                        (float(x), float(y), float(face_z))
                        for x, y in coordinates
                    )
                    if reverse:
                        vertices = tuple(reversed(vertices))
                    surfaces.append(SourceSurface(
                        role=f"{role}:skin:{len(surfaces):04d}",
                        volume_role=role,
                        verb="certified_final_mesh",
                        surface_type="profiled_recursive_solid_mesh",
                        vertices_m=vertices,
                        operator="mesh",
                        semantic_patch_id=f"{role}:skin:{len(surfaces):04d}",
                    ))
            rings = [footprint.exterior, *footprint.interiors]
            for ring in rings:
                coordinates = list(ring.coords)
                for (x1, y1), (x2, y2) in zip(
                    coordinates,
                    coordinates[1:],
                ):
                    for vertices in (
                        (
                            (float(x1), float(y1), float(bottom)),
                            (float(x2), float(y2), float(bottom)),
                            (float(x2), float(y2), float(top)),
                        ),
                        (
                            (float(x1), float(y1), float(bottom)),
                            (float(x2), float(y2), float(top)),
                            (float(x1), float(y1), float(top)),
                        ),
                    ):
                        surfaces.append(SourceSurface(
                            role=f"{role}:skin:{len(surfaces):04d}",
                            volume_role=role,
                            verb="certified_final_mesh",
                            surface_type="profiled_recursive_solid_mesh",
                            vertices_m=vertices,
                            operator="mesh",
                            semantic_patch_id=(
                                f"{role}:skin:{len(surfaces):04d}"
                            ),
                        ))
        proxy_layers = tuple(proxy_layers or layers)
        volumes = tuple(
            SourceVolume(
                role=f"proxy_layer_{layer_index:02d}",
                footprint=footprint,
                bottom_fraction=bottom / maximum_height,
                top_fraction=top / maximum_height,
                verb="certified_final_mesh_proxy",
            )
            for layer_index, (footprint, bottom, top) in enumerate(
                proxy_layers
            )
        )
        geometry_program = {
            "nodes": [
                {"id": f"node_{index}", **node}
                for index, node in enumerate(geometry_program_nodes)
            ],
        }
        projection = {
            "schema_version": "arr.maas.authored_legal_preservation.v1",
            "status": "certified",
            "hard_pass": True,
            "projection_mode": projection_mode,
            "floor_count": len(layers),
        }
        footprint = proxy_footprint or proxy_layers[0][0]
        return SourceMass(
            name=name,
            footprint=footprint,
            upper_footprint=layers[-1][0],
            volumes=tuple(volumes),
            surfaces=tuple(surfaces),
            metadata={
                "geometry_program": geometry_program,
                "geometry_program_compilation": {
                    "status": "compiled",
                    "geometry_hash": f"{name}-geometry-hash",
                    "metrics": {
                        "component_count": 1,
                        "genus": len(footprint.interiors),
                        "manifold": True,
                        "watertight": True,
                    },
                },
                "authored_legal_preservation": projection,
            },
        )

    @staticmethod
    def _certified_triangle_mesh_source(
        name,
        *,
        vertices,
        triangles,
        proxy_footprint,
        proxy_volumes,
        geometry_program_nodes=(),
    ):
        surfaces = tuple(
            SourceSurface(
                role=f"certified_mesh:skin:{index:04d}",
                volume_role="certified_mesh",
                verb="certified_final_mesh",
                surface_type="profiled_recursive_solid_mesh",
                vertices_m=tuple(vertices[vertex] for vertex in triangle),
                operator="mesh",
                semantic_patch_id=f"certified_mesh:skin:{index:04d}",
            )
            for index, triangle in enumerate(triangles)
        )
        return SourceMass(
            name=name,
            footprint=proxy_footprint,
            upper_footprint=proxy_footprint,
            volumes=tuple(proxy_volumes),
            surfaces=surfaces,
            metadata={
                "geometry_program": {
                    "nodes": [
                        {"id": f"node_{index}", **node}
                        for index, node in enumerate(geometry_program_nodes)
                    ],
                },
                "geometry_program_compilation": {
                    "status": "compiled",
                    "geometry_hash": f"{name}-geometry-hash",
                    "metrics": {
                        "component_count": 1,
                        "genus": 0,
                        "manifold": True,
                        "watertight": True,
                    },
                },
                "authored_legal_preservation": {
                    "schema_version": (
                        "arr.maas.authored_legal_preservation.v1"
                    ),
                    "status": "certified",
                    "hard_pass": True,
                    "projection_mode": "authored_affine_preserved",
                },
            },
        )

    def test_competition_gestalt_marks_one_large_mesh_setback_visible(self):
        lower = Polygon(((-5, -4), (5, -4), (5, 4), (-5, 4)))
        upper = Polygon(((-2.5, -3), (4.5, -3), (4.5, 3), (-2.5, 3)))
        stepped = self._certified_prism_mesh_source(
            "two-tier-visible-step",
            ((lower, 0.0, 1.0), (upper, 1.0, 2.0)),
            geometry_program_nodes=({"operator": "setback"},),
        )
        vertices = (
            (-5.0, -4.0, 0.0),
            (5.0, -4.0, 0.0),
            (5.0, 4.0, 0.0),
            (-5.0, 4.0, 0.0),
            (-5.0, -4.0, 2.0),
            (5.0, -4.0, 2.0),
            (5.0, 4.0, 2.0),
            (-5.0, 4.0, 2.0),
            (-5.0, 0.0, 3.0),
            (5.0, 0.0, 3.0),
        )
        triangles = (
            (0, 2, 1), (0, 3, 2),
            (0, 1, 5), (0, 5, 4),
            (3, 7, 6), (3, 6, 2),
            (0, 4, 7), (0, 7, 3), (4, 8, 7),
            (1, 2, 6), (1, 6, 5), (5, 6, 9),
            (4, 5, 9), (4, 9, 8),
            (8, 9, 6), (8, 6, 7),
        )
        roof_only = self._certified_triangle_mesh_source(
            "gable-roof-only",
            vertices=vertices,
            triangles=triangles,
            proxy_footprint=lower,
            proxy_volumes=(
                SourceVolume(
                    role="gable_proxy",
                    footprint=lower,
                    bottom_fraction=0.0,
                    top_fraction=1.0,
                    verb="certified_final_mesh_proxy",
                ),
            ),
        )

        stepped_key = candidate_analysis.competition_gestalt_key(stepped)
        roof_key = candidate_analysis.competition_gestalt_key(roof_only)

        self.assertEqual(len(stepped_key.setback_transition_sequence), 1)
        self.assertTrue(stepped_key.visible_stepped)
        self.assertFalse(roof_key.visible_stepped)

    def test_visible_mesh_step_takes_body_precedence_over_sloped_faces(self):
        lower = Polygon(((-5, -4), (5, -4), (5, 4), (-5, 4)))
        upper = Polygon(((-2.5, -3), (4.5, -3), (4.5, 3), (-2.5, 3)))
        stepped = self._certified_prism_mesh_source(
            "visible-step-with-sloped-faces",
            ((lower, 0.0, 1.0), (upper, 1.0, 2.0)),
            geometry_program_nodes=({"operator": "setback"},),
        )
        sloped = SourceSurface(
            role="sloped-body-proof",
            volume_role="certified_layer_01",
            verb="certified_final_mesh",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=(
                (-20.0, -20.0, 0.0),
                (20.0, -20.0, 0.0),
                (0.0, 20.0, 20.0),
            ),
            operator="mesh",
            semantic_patch_id="sloped-body-proof",
        )
        source = replace(
            stepped,
            surfaces=(*stepped.surfaces, sloped),
            metadata=deepcopy(stepped.metadata),
        )
        with (
            patch.object(
                candidate_analysis,
                "_step_origin_evidence",
                return_value={
                    "visible_stepped": True,
                    "authored_stepped": True,
                    "legal_seam_stepped": False,
                    "step_projection_mode": "authored_affine_preserved",
                    "competition_gestalt": {},
                },
            ),
            patch.object(
                candidate_analysis,
                "_verified_exact_profiled_sloped_mesh",
                return_value=True,
            ),
        ):
            morphology = candidate_analysis._solid_morphology_metrics(source)

        self.assertGreater(morphology["sloped_surface_ratio"], 0.24)
        self.assertTrue(morphology["visible_stepped"])
        self.assertEqual(morphology["body_phenotype"], "stepped")

    def test_competition_gestalt_morphology_ignores_mismatched_proxies(self):
        lower = Polygon(((-5, -4), (5, -4), (5, 4), (-5, 4)))
        upper = Polygon(((-2.5, -3), (4.5, -3), (4.5, 3), (-2.5, 3)))
        proxy = Polygon(((-8, -7), (8, -7), (8, 7), (-8, 7)))
        stepped = self._certified_prism_mesh_source(
            "mesh-step-proxy-prism",
            ((lower, 0.0, 1.0), (upper, 1.0, 2.0)),
            geometry_program_nodes=({"operator": "setback"},),
            proxy_layers=((proxy, 0.0, 2.0),),
            proxy_footprint=proxy,
        )
        courtyard_mesh = Polygon(
            ((-5, -4), (5, -4), (5, 4), (-5, 4)),
            holes=(((-2, -1.5), (2, -1.5), (2, 1.5), (-2, 1.5)),),
        )
        courtyard = self._certified_prism_mesh_source(
            "mesh-courtyard-proxy-solid",
            ((courtyard_mesh, 0.0, 2.0),),
            geometry_program_nodes=({"operator": "courtyard"},),
            proxy_layers=((proxy, 0.0, 2.0),),
            proxy_footprint=proxy,
        )

        stepped_key = candidate_analysis.competition_gestalt_key(stepped)
        courtyard_key = candidate_analysis.competition_gestalt_key(courtyard)

        self.assertTrue(stepped_key.visible_stepped)
        self.assertEqual(len(stepped_key.setback_transition_sequence), 1)
        self.assertLess(min(stepped_key.floor_area_by_height), 0.60)
        self.assertEqual(courtyard_key.plan_profile[1], 1.0)
        self.assertGreater(courtyard_key.plan_profile[2], 0.10)

    def test_competition_gestalt_is_invariant_to_rigid_mesh_rotation(self):
        layers = (
            (Polygon(((-5, -4), (5, -4), (5, 4), (-5, 4))), 0.0, 1.0),
            (Polygon(((-3, -3), (4, -3), (4, 3), (-3, 3))), 1.0, 2.0),
            (Polygon(((-2, -2), (3, -2), (3, 2), (-2, 2))), 2.0, 3.0),
        )
        source = self._certified_prism_mesh_source(
            "asymmetric-three-tier",
            layers,
            geometry_program_nodes=({"operator": "setback"},),
        )
        angle = 37.0 * tau / 360.0

        def rotate_vertex(vertex):
            x, y, z = vertex
            return (
                x * cos(angle) - y * sin(angle),
                x * sin(angle) + y * cos(angle),
                z,
            )

        rotated = replace(
            source,
            name="asymmetric-three-tier-rotated-37",
            footprint=rotate(source.footprint, 37.0, origin=(0.0, 0.0)),
            upper_footprint=rotate(
                source.upper_footprint,
                37.0,
                origin=(0.0, 0.0),
            ),
            volumes=tuple(
                replace(
                    volume,
                    footprint=rotate(
                        volume.footprint,
                        37.0,
                        origin=(0.0, 0.0),
                    ),
                )
                for volume in source.volumes
            ),
            surfaces=tuple(
                replace(
                    surface,
                    vertices_m=tuple(
                        rotate_vertex(vertex)
                        for vertex in surface.vertices_m
                    ),
                )
                for surface in source.surfaces
            ),
            metadata={
                **source.metadata,
                "geometry_program_compilation": {
                    **source.metadata["geometry_program_compilation"],
                    "geometry_hash": "asymmetric-three-tier-rotated-hash",
                },
            },
        )

        distance = candidate_analysis.competition_gestalt_distance(
            source,
            rotated,
        )

        self.assertLessEqual(distance, 0.001)

    def test_competition_gestalt_rejects_same_stair_language(self):
        rectangle_layers = (
            (Polygon(((-5, -4), (5, -4), (5, 4), (-5, 4))), 0.0, 1.0),
            (Polygon(((-4, -3), (4, -3), (4, 3), (-4, 3))), 1.0, 2.0),
            (Polygon(((-3, -2), (3, -2), (3, 2), (-3, 2))), 2.0, 3.0),
        )

        def cross(width, depth):
            shoulder_x = width * 0.24
            shoulder_y = depth * 0.24
            half_x = width / 2.0
            half_y = depth / 2.0
            return Polygon((
                (-shoulder_x, -half_y),
                (shoulder_x, -half_y),
                (shoulder_x, -shoulder_y),
                (half_x, -shoulder_y),
                (half_x, shoulder_y),
                (shoulder_x, shoulder_y),
                (shoulder_x, half_y),
                (-shoulder_x, half_y),
                (-shoulder_x, shoulder_y),
                (-half_x, shoulder_y),
                (-half_x, -shoulder_y),
                (-shoulder_x, -shoulder_y),
            ))

        cross_layers = (
            (rotate(cross(10.0, 8.0), 27.0), 0.0, 1.0),
            (rotate(cross(8.0, 6.0), 27.0), 1.0, 2.0),
            (rotate(cross(6.0, 4.0), 27.0), 2.0, 3.0),
        )
        left = self._certified_prism_mesh_source(
            "same-stair-rectangle",
            rectangle_layers,
            geometry_program_nodes=({"operator": "setback"},),
        )
        right = self._certified_prism_mesh_source(
            "same-stair-cross",
            cross_layers,
            projection_mode="intentional_floorwise_stepped",
        )

        self.assertNotEqual(
            left.signature()["actual_surface_payload_hash"],
            right.signature()["actual_surface_payload_hash"],
        )
        self.assertGreater(visual_silhouette_distance(left, right), 0.10)
        self.assertTrue(
            hasattr(candidate_analysis, "competition_gestalt_distance"),
            "certified-mesh competition gestalt API is missing",
        )
        self.assertLess(
            candidate_analysis.competition_gestalt_distance(left, right),
            0.22,
        )
        self.assertLess(
            candidate_analysis._distance(
                SimpleNamespace(source=left),
                SimpleNamespace(source=right),
            ),
            0.22,
        )
        left_morphology = candidate_analysis._solid_morphology_metrics(left)
        right_morphology = candidate_analysis._solid_morphology_metrics(right)
        self.assertTrue(left_morphology["visible_stepped"])
        self.assertTrue(left_morphology["authored_stepped"])
        self.assertFalse(left_morphology["legal_seam_stepped"])
        self.assertTrue(right_morphology["visible_stepped"])
        self.assertFalse(right_morphology["authored_stepped"])
        self.assertTrue(right_morphology["legal_seam_stepped"])

    def test_competition_gestalt_keeps_courtyard_and_curve(self):
        courtyard = self._certified_prism_mesh_source(
            "courtyard",
            ((
                Polygon(
                    ((-5, -4), (5, -4), (5, 4), (-5, 4)),
                    holes=((( -2, -1.5), (2, -1.5), (2, 1.5), (-2, 1.5)),),
                ),
                0.0,
                3.0,
            ),),
            geometry_program_nodes=({"operator": "courtyard"},),
        )
        curved_outline = Polygon(tuple(
            (
                5.0 * cos(index * tau / 24),
                4.0 * sin(index * tau / 24),
            )
            for index in range(24)
        ))
        curved = self._certified_prism_mesh_source(
            "curved-body",
            ((curved_outline, 0.0, 3.0),),
            geometry_program_nodes=({"operator": "bend"},),
        )

        self.assertGreaterEqual(
            visual_silhouette_distance(courtyard, curved),
            0.14,
        )
        self.assertTrue(
            hasattr(candidate_analysis, "competition_gestalt_distance"),
            "certified-mesh competition gestalt API is missing",
        )
        self.assertGreaterEqual(
            candidate_analysis.competition_gestalt_distance(
                courtyard,
                curved,
            ),
            0.14,
        )

    def test_competition_target_20_contract(self):
        contract = competition_portfolio_contract(20)

        self.assertEqual(contract.target_count, 20)
        self.assertEqual(contract.capacity_band_exact_counts, {
            "spatial_reserve": 5,
            "balanced_yield": 5,
            "brief_target": 5,
            "maximum_feasible": 5,
        })
        self.assertEqual(contract.visible_stepped_minimum, 1)
        self.assertEqual(contract.visible_stepped_maximum, 3)
        self.assertEqual(contract.body_phenotype_minimum_distinct, 5)
        self.assertEqual(contract.body_phenotype_maximum_each, 4)
        self.assertEqual(contract.roof_archetype_minimum_distinct, 7)
        self.assertEqual(contract.roof_archetype_maximum_each, 3)

    def test_target_3_rejects_two_visible_stepped_cards(self):
        facts = [
            portfolio_selection.ConstraintCandidateFacts(
                score=1.0 - index * 0.01,
                cap_keys=(),
                visible_stepped=index < 2,
                body_phenotype=f"body_{index}",
                roof_archetype=f"roof_{index}",
                body_roof_signature=f"body_{index}:roof_{index}",
            )
            for index in range(3)
        ]
        certificate = {}

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            self._fully_compatible(3),
            target_count=3,
            maximum_key_counts={},
            portfolio_contract=competition_portfolio_contract(3),
            infeasibility_certificate=certificate,
        )

        self.assertEqual(selected, ())
        self.assertIn(
            "visible_stepped:max_1",
            certificate["unsatisfied_constraints"],
        )

    def test_selector_uses_visible_mesh_steps_when_body_language_is_not_stepped(self):
        phenotypes = ("voided", "winged", "curved")
        candidates = [
            SimpleNamespace(
                key=f"visible-step-{index}",
                score=1.0 - index * 0.01,
                scope="1/1",
                principle_kind="base_operative",
                operation=f"operation_{index}",
                seed=f"seed_{index}",
                section=f"section_{index}",
                roof=f"roof_{index}",
                chassis=f"chassis_{index}",
                family=f"family_{index}",
                plan=f"plan_{index}",
                morphology={
                    "phenotype": phenotype,
                    "body_phenotype": phenotype,
                    "section_phenotype": "none",
                    "visible_stepped": index < 2,
                    "wedge_like": False,
                    "pyramidal_like": False,
                },
                source=SimpleNamespace(metadata={}),
            )
            for index, phenotype in enumerate(phenotypes)
        ]
        trace = {}
        with (
            patch.object(
                portfolio_selection,
                "_fingerprint",
                side_effect=lambda item: (item.key,),
            ),
            patch.object(
                portfolio_selection,
                "_scope_key",
                side_effect=lambda item: item.scope,
            ),
            patch.object(
                portfolio_selection,
                "_capacity_alternative_key",
                return_value="",
            ),
            patch.object(
                portfolio_selection,
                "_seed_family",
                side_effect=lambda item: item.seed,
            ),
            patch.object(
                portfolio_selection,
                "_section_family",
                side_effect=lambda item: item.section,
            ),
            patch.object(
                portfolio_selection,
                "_roof_archetype",
                side_effect=lambda item: item.roof,
            ),
            patch.object(
                portfolio_selection,
                "_chassis_family",
                side_effect=lambda item: item.chassis,
            ),
            patch.object(
                portfolio_selection,
                "_geometry_program_family",
                side_effect=lambda item: item.family,
            ),
            patch.object(
                portfolio_selection,
                "_plan_family",
                side_effect=lambda item: item.plan,
            ),
            patch.object(
                portfolio_selection,
                "_solid_morphology_metrics",
                side_effect=lambda item: item.morphology,
            ),
            patch.object(
                portfolio_selection,
                "_silhouette_distance",
                return_value=1.0,
            ),
            patch.object(
                portfolio_selection,
                "_distance",
                return_value=1.0,
            ),
            patch.object(
                portfolio_selection,
                "_design_concept_descriptor",
                side_effect=lambda item: {
                    "ground_strategy": f"ground_{item.key}",
                    "concept_key": item.key,
                    "frontage_aligned": False,
                },
            ),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=3,
                selection_trace=trace,
            )

        self.assertEqual(selected, [])
        self.assertIn(
            "visible_stepped:max_1",
            trace["portfolio_contract_deficits"],
        )

    def test_target_20_requires_five_cards_per_capacity_band(self):
        bands = (
            ["spatial_reserve"] * 5
            + ["balanced_yield"] * 5
            + ["brief_target"] * 5
            + ["maximum_feasible"] * 5
        )
        scopes = (
            ["1/1"] * 4
            + ["1/2"] * 4
            + ["3/8"] * 3
            + ["1/4"] * 3
            + ["1/8"] * 3
            + ["1/16"] * 3
        )

        def facts_for(capacity_bands):
            return [
                portfolio_selection.ConstraintCandidateFacts(
                    score=1.0 - index * 0.01,
                    cap_keys=(),
                    visible_stepped=index < 2,
                    body_phenotype=f"body_{index % 5}",
                    roof_archetype=f"roof_{index % 7}",
                    chassis_family=f"chassis_{index % 6}",
                    plan_family=f"plan_{index % 5}",
                    base_scope=scopes[index],
                    capacity_band=band,
                    body_roof_signature=(
                        f"body_{index % 5}:roof_{index % 7}"
                    ),
                )
                for index, band in enumerate(capacity_bands)
            ]

        contract = competition_portfolio_contract(20)
        balanced = portfolio_selection.solve_milp_compatible_subset(
            facts_for(bands),
            self._fully_compatible(20),
            target_count=20,
            maximum_key_counts={},
            portfolio_contract=contract,
        )
        mutated_bands = list(bands)
        mutated_bands[5] = "spatial_reserve"
        certificate = {}
        unbalanced = portfolio_selection.solve_milp_compatible_subset(
            facts_for(mutated_bands),
            self._fully_compatible(20),
            target_count=20,
            maximum_key_counts={},
            portfolio_contract=contract,
            infeasibility_certificate=certificate,
        )

        self.assertEqual(balanced, tuple(range(20)))
        self.assertEqual(unbalanced, ())
        self.assertTrue(any(
            deficit.startswith("capacity_band:")
            and deficit.endswith(":exact_5")
            for deficit in certificate["unsatisfied_constraints"]
        ))

    def test_benchmark_morphology_audit_uses_target_contract(self):
        target_three_failures = (
            portfolio_benchmark._portfolio_contract_morphology_failures(
                {
                    "stepped_count": 0,
                    "upper_band_stepped_count": 0,
                    "solid_phenotype_counts": {
                        "body_a": 1,
                        "body_b": 1,
                        "body_c": 1,
                    },
                },
                target_count=3,
            )
        )
        target_twenty_failures = (
            portfolio_benchmark._portfolio_contract_morphology_failures(
                {
                    "stepped_count": 1,
                    "upper_band_stepped_count": 0,
                    "solid_phenotype_counts": {
                        f"body_{index}": 4 for index in range(5)
                    },
                },
                target_count=20,
            )
        )

        self.assertEqual(target_three_failures, [])
        self.assertEqual(target_twenty_failures, [])

    def test_shared_compatibility_analysis_measures_each_unordered_pair_once(self):
        if not hasattr(portfolio_selection, "build_compatibility_analysis"):
            self.fail("shared compatibility analysis is not implemented")

        class CandidateProbe:
            def __init__(self, name):
                self.name = name

        candidates = [CandidateProbe(f"candidate-{index}") for index in range(54)]
        calls = Counter()

        def measured_distance(left, right):
            key = tuple(sorted((left.name, right.name)))
            calls[key] += 1
            return 0.25 if left is not right else 0.0

        analysis = portfolio_selection.build_compatibility_analysis(
            candidates,
            threshold=0.10,
            distance_evaluator=measured_distance,
        )
        first = analysis.compatibility_matrix(candidates)
        second = analysis.compatibility_matrix(list(reversed(candidates)))
        for left in candidates:
            for right in candidates:
                analysis.distance(left, right)

        self.assertEqual(len(first), 54)
        self.assertEqual(len(second), 54)
        self.assertEqual(sum(calls.values()), 54 * 53 // 2)
        self.assertTrue(all(value == 1 for value in calls.values()))
        self.assertEqual(
            analysis.evidence()["exact_pair_evaluation_count"],
            54 * 53 // 2,
        )
        self.assertEqual(
            analysis.evidence()["compatibility_threshold"],
            0.10,
        )
        self.assertTrue(
            analysis.evidence()["distance_evaluator"].endswith(
                ".measured_distance"
            )
        )

    def test_target_twenty_compatibility_uses_competition_contract_threshold(self):
        analysis = portfolio_selection.build_compatibility_analysis(
            [],
            target_count=20,
        )

        self.assertEqual(
            analysis.evidence()["compatibility_threshold"],
            competition_portfolio_contract(20).minimum_pair_distance,
        )

    def test_portfolio_selection_uses_competition_gestalt_distance(self):
        analysis = (
            portfolio_selection.build_gestalt_compatibility_analysis(
                [],
                target_count=3,
            )
        )

        evidence = analysis.evidence()
        self.assertEqual(
            evidence["compatibility_threshold"],
            competition_portfolio_contract(3).minimum_pair_distance,
        )
        self.assertTrue(
            evidence["distance_evaluator"].endswith(
                ".candidate_analysis._distance"
            )
        )

    def test_shared_compatibility_analysis_does_not_retain_dropped_candidates(self):
        sequence = program_seed_sequences("neighborhood_living")[0]
        left = portfolio_benchmark._Candidate(
            "book:test:left",
            "base_operative",
            "left",
            sequence,
            SimpleNamespace(),
            {"type": "Feature", "properties": {}},
            1.0,
        )
        right = portfolio_benchmark._Candidate(
            "book:test:right",
            "base_operative",
            "right",
            sequence,
            SimpleNamespace(),
            {"type": "Feature", "properties": {}},
            0.9,
        )
        left_ref = weakref.ref(left)
        right_ref = weakref.ref(right)
        analysis = portfolio_selection.build_compatibility_analysis(
            [left, right],
            distance_evaluator=lambda _left, _right: 1.0,
        )
        self.assertEqual(analysis.distance(left, right), 1.0)
        self.assertEqual(analysis.evidence()["cached_pair_count"], 1)

        del left
        del right
        gc.collect()

        self.assertIsNone(left_ref())
        self.assertIsNone(right_ref())
        self.assertEqual(analysis.evidence()["cached_pair_count"], 0)

    def test_shared_compatibility_analysis_single_flights_same_pair(self):
        class CandidateProbe:
            pass

        left = CandidateProbe()
        right = CandidateProbe()
        call_count = 0
        count_lock = Lock()
        start = Barrier(8)

        def measured_distance(_left, _right):
            nonlocal call_count
            with count_lock:
                call_count += 1
            sleep(0.04)
            return 0.25

        analysis = portfolio_selection.build_compatibility_analysis(
            [left, right],
            distance_evaluator=measured_distance,
        )

        def worker(_index):
            start.wait()
            return analysis.distance(left, right)

        with ThreadPoolExecutor(max_workers=8) as executor:
            distances = list(executor.map(worker, range(8)))

        self.assertEqual(distances, [0.25] * 8)
        self.assertEqual(call_count, 1)
        evidence = analysis.evidence()
        self.assertEqual(evidence["exact_pair_evaluation_count"], 1)
        self.assertEqual(evidence["pair_cache_hit_count"], 7)

    def test_portfolio_duplicate_threshold_uses_shared_visual_novelty_policy(self):
        """Selection and replenishment must agree on what counts as a repeat."""
        from design.maas.program_massing.morphology import DEFAULT_NOVELTY_POLICY

        self.assertEqual(
            portfolio_selection.PORTFOLIO_SILHOUETTE_DISTANCE,
            DEFAULT_NOVELTY_POLICY.visual_silhouette_repeat,
        )
        self.assertEqual(
            portfolio_benchmark.PORTFOLIO_SILHOUETTE_DISTANCE,
            DEFAULT_NOVELTY_POLICY.visual_silhouette_repeat,
        )

    def test_lineage_gate_keeps_descendant_when_viable_base_was_evicted_by_qd(self):
        def candidate(parent_key: str, stage: str, target_pass: bool):
            return SimpleNamespace(source=SimpleNamespace(metadata={
                "book_generation_lineage": {
                    "parent_key": parent_key,
                    "stage": stage,
                },
                "geometry_program": {
                    "metadata": {"family": "agent_notch"},
                },
                "capacity_alternative_projection": {
                    "target_hard_pass": target_pass,
                },
            }))

        retained_descendant = candidate(
            "base-evicted-after-program-pass",
            "combination",
            True,
        )
        rejected_descendant = candidate(
            "base-never-program-valid",
            "combination",
            True,
        )

        retained, evidence = book_lineage.gate_descendants_by_base(
            [retained_descendant, rejected_descendant],
            known_viable_base_keys={"base-evicted-after-program-pass"},
        )

        self.assertEqual(retained, [retained_descendant])
        self.assertEqual(evidence["retained_via_known_base_count"], 1)
        self.assertEqual(evidence["capacity_target_pass_input_count"], 2)
        self.assertEqual(evidence["capacity_target_pass_retained_count"], 1)

    def test_capacity_portfolio_quotas_balance_four_bands_and_absorb_rare_supply(self):
        def candidate(alternative_id: str):
            return SimpleNamespace(source=SimpleNamespace(metadata={
                "capacity_alternative_projection": {
                    "requested_capacity_alternative_id": alternative_id,
                    "selectable_capacity_alternative_id": alternative_id,
                    "selectable_capacity_target_utilization": 0.70,
                    "selectable_capacity_hard_pass": True,
                    "feasible_minimum_utilization": 0.70,
                },
                "source_capacity_measurement": {
                    "feasible_capacity_utilization": 0.80,
                },
            }))

        balanced_supply = [
            candidate(alternative_id)
            for alternative_id in (
                "spatial_reserve", "balanced_yield", "brief_target", "maximum_feasible",
            )
            for _index in range(20)
        ]
        self.assertEqual(
            portfolio_selection._capacity_portfolio_quotas(
                balanced_supply,
                target=20,
            ),
            {
                "maximum_feasible": 5,
                "brief_target": 5,
                "balanced_yield": 5,
                "spatial_reserve": 5,
            },
        )

        rare_maximum_supply = [
            *[candidate("maximum_feasible") for _index in range(3)],
            *[candidate("brief_target") for _index in range(9)],
            *[candidate("balanced_yield") for _index in range(20)],
            *[candidate("spatial_reserve") for _index in range(20)],
        ]
        self.assertEqual(
            portfolio_selection._capacity_portfolio_quotas(
                rare_maximum_supply,
                target=20,
            ),
            {
                "maximum_feasible": 3,
                "brief_target": 6,
                "balanced_yield": 6,
                "spatial_reserve": 5,
            },
        )

    def test_exact_solver_prefers_cardinality_when_full_coverage_is_infeasible(self):
        """A small coverage set must not hide a larger legal compatible set."""
        facts = [
            portfolio_selection.ConstraintCandidateFacts(
                score=1.0,
                cap_keys=("slot:1", "slot:2", "slot:3"),
                coverage_tags=("required:scope",),
            ),
            *[
                portfolio_selection.ConstraintCandidateFacts(
                    score=0.9 - index * 0.1,
                    cap_keys=(f"slot:{index + 1}",),
                )
                for index in range(3)
            ],
        ]
        compatibility = [[True for _right in range(4)] for _left in range(4)]

        selected = portfolio_selection.solve_maximum_compatible_subset(
            facts,
            compatibility,
            target_count=3,
            maximum_key_counts={
                "slot:1": 1,
                "slot:2": 1,
                "slot:3": 1,
            },
            required_coverage_tags=("required:scope",),
        )

        self.assertEqual(selected, (1, 2, 3))

    def test_bounded_solver_recovers_twenty_set_from_large_greedy_trap(self):
        count = 31
        facts = [
            portfolio_selection.ConstraintCandidateFacts(
                score=2.0 if index == 0 else 1.0 - index * 0.001,
                cap_keys=(f"candidate:{index}",),
                coverage_tags=(("required:maximum",) if index == 20 else ()),
            )
            for index in range(count)
        ]
        compatibility = [[True for _right in range(count)] for _left in range(count)]
        for index in range(1, 21):
            compatibility[0][index] = False
            compatibility[index][0] = False

        selected = portfolio_selection.solve_bounded_compatible_subset(
            facts,
            compatibility,
            target_count=20,
            maximum_key_counts={f"candidate:{index}": 1 for index in range(count)},
            required_coverage_tags=("required:maximum",),
            beam_width=128,
        )

        self.assertEqual(len(selected), 20)
        self.assertNotIn(0, selected)
        self.assertIn(20, selected)

    def test_bounded_fallback_prefers_cardinality_before_isolated_required_coverage(self):
        """A rare coverage witness cannot replace a compatible ten-card set."""
        count = 11
        facts = [
            portfolio_selection.ConstraintCandidateFacts(
                score=2.0 if index == 0 else 1.0 - index * 0.001,
                cap_keys=(f"candidate:{index}",),
                coverage_tags=(("required:isolated",) if index == 0 else ()),
            )
            for index in range(count)
        ]
        compatibility = [
            [True for _right in range(count)]
            for _left in range(count)
        ]
        for index in range(1, count):
            compatibility[0][index] = False
            compatibility[index][0] = False

        selected = portfolio_selection.solve_bounded_compatible_subset(
            facts,
            compatibility,
            target_count=10,
            maximum_key_counts={
                f"candidate:{index}": 1
                for index in range(count)
            },
            required_coverage_tags=("required:isolated",),
            beam_width=32,
        )

        self.assertEqual(selected, tuple(range(1, 11)))

    def test_milp_solver_proves_maximum_set_under_caps_and_coverage(self):
        count = 31
        facts = [
            portfolio_selection.ConstraintCandidateFacts(
                score=2.0 if index == 0 else 1.0 - index * 0.001,
                cap_keys=(f"candidate:{index}", f"band:{index % 4}"),
                coverage_tags=(("required:maximum",) if index == 20 else ()),
            )
            for index in range(count)
        ]
        compatibility = [[True for _right in range(count)] for _left in range(count)]
        for index in range(1, 21):
            compatibility[0][index] = False
            compatibility[index][0] = False
        maximum_counts = {
            **{f"candidate:{index}": 1 for index in range(count)},
            **{f"band:{index}": 6 for index in range(4)},
        }

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            compatibility,
            target_count=20,
            maximum_key_counts=maximum_counts,
            required_coverage_tags=("required:maximum",),
        )

        self.assertEqual(len(selected), 20)
        self.assertNotIn(0, selected)
        self.assertIn(20, selected)

    def test_milp_solver_returns_certificate_when_joint_coverage_is_infeasible(self):
        """A completed portfolio must never hide a missing requirement."""
        facts = [
            portfolio_selection.ConstraintCandidateFacts(
                score=2.0,
                cap_keys=("candidate:0",),
                coverage_tags=("scope:rare",),
            ),
            portfolio_selection.ConstraintCandidateFacts(
                score=1.0,
                cap_keys=("candidate:1",),
                coverage_tags=("capacity:brief",),
            ),
            portfolio_selection.ConstraintCandidateFacts(
                score=0.9,
                cap_keys=("candidate:2",),
            ),
        ]
        compatibility = [
            [True, False, False],
            [False, True, True],
            [False, True, True],
        ]

        certificate = {}
        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            compatibility,
            target_count=2,
            maximum_key_counts={
                "candidate:0": 1,
                "candidate:1": 1,
                "candidate:2": 1,
            },
            required_coverage_tags=("scope:rare", "capacity:brief"),
            infeasibility_certificate=certificate,
        )

        self.assertEqual(selected, ())
        self.assertEqual(certificate["maximum_achievable_cardinality"], 2)
        self.assertTrue(certificate["unsatisfied_constraints"])

    def test_capacity_descriptor_uses_only_realized_selectable_band(self):
        candidate = SimpleNamespace(source=SimpleNamespace(metadata={
            "capacity_alternative_projection": {
                "alternative_id": "maximum_feasible",
                "requested_capacity_alternative_id": "maximum_feasible",
                "requested_target_utilization": 0.95,
                "achieved_utilization": 0.72,
                "target_hard_pass": False,
                "selectable_capacity_alternative_id": "",
                "selectable_capacity_target_utilization": 0.0,
                "selectable_capacity_hard_pass": False,
            },
        }))

        self.assertEqual(candidate_analysis._capacity_alternative_key(candidate), "")
        self.assertFalse(candidate_analysis._capacity_target_gate(candidate))

    def test_capacity_descriptor_re_resolves_raw_true_against_final_measurement(self):
        candidate = SimpleNamespace(source=SimpleNamespace(metadata={
            "capacity_alternative_projection": {
                "requested_capacity_alternative_id": "brief_target",
                "selectable_capacity_alternative_id": "brief_target",
                "selectable_capacity_target_utilization": 0.80,
                "selectable_capacity_hard_pass": True,
                "feasible_minimum_utilization": 0.70,
            },
            "source_capacity_measurement": {
                "feasible_capacity_utilization": 0.72,
            },
        }))

        self.assertEqual(
            candidate_analysis._capacity_alternative_key(candidate),
            "",
        )

    def test_joint_ten_card_solver_rejects_four_two_two_two_capacity_counts(self):
        facts = self._joint_portfolio_facts(
            ["spatial_reserve"] * 4
            + ["balanced_yield"] * 2
            + ["brief_target"] * 2
            + ["maximum_feasible"] * 2
        )
        certificate = {}

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            self._fully_compatible(10),
            target_count=10,
            maximum_key_counts={},
            **self._joint_portfolio_constraints(certificate),
        )

        self.assertEqual(selected, ())
        self.assertIn(
            "capacity_band:spatial_reserve:max_3",
            certificate["unsatisfied_constraints"],
        )

    def test_joint_ten_card_solver_accepts_three_three_two_two_and_six_scopes(self):
        facts = self._joint_portfolio_facts(self._balanced_capacity_bands())
        certificate = {}

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            self._fully_compatible(10),
            target_count=10,
            maximum_key_counts={},
            **self._joint_portfolio_constraints(certificate),
        )

        self.assertEqual(selected, tuple(range(10)))
        self.assertEqual(certificate, {})

    def test_joint_ten_card_solver_rejects_two_unclassified_capacity_cards(self):
        facts = self._joint_portfolio_facts(
            ["spatial_reserve"] * 2
            + ["balanced_yield"] * 2
            + ["brief_target"] * 2
            + ["maximum_feasible"] * 2
            + ["", ""]
        )
        certificate = {}

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            self._fully_compatible(10),
            target_count=10,
            maximum_key_counts={},
            **self._joint_portfolio_constraints(certificate),
        )

        self.assertEqual(selected, ())
        self.assertIn(
            "capacity_band:classified_exact_10",
            certificate["unsatisfied_constraints"],
        )

    def test_final_audit_rejects_two_unclassified_capacity_cards(self):
        keys = (
            ["spatial_reserve"] * 2
            + ["balanced_yield"] * 2
            + ["brief_target"] * 2
            + ["maximum_feasible"] * 2
            + ["", ""]
        )

        self.assertFalse(
            portfolio_benchmark._achieved_capacity_balance_pass(
                keys,
                target_count=10,
            )
        )

    def test_milp_timeout_is_not_reported_as_proven_infeasible(self):
        timeout = SimpleNamespace(
            x=None,
            success=False,
            status=1,
            message="Time limit reached.",
        )
        certificate = {}
        with patch("scipy.optimize.milp", return_value=timeout):
            selected = portfolio_selection.solve_milp_compatible_subset(
                [
                    portfolio_selection.ConstraintCandidateFacts(
                        score=1.0,
                        cap_keys=(),
                    ),
                ],
                [[True]],
                target_count=1,
                maximum_key_counts={},
                infeasibility_certificate=certificate,
            )

        self.assertEqual(selected, ())
        self.assertEqual(certificate["status"], "solver_not_proven")
        self.assertEqual(certificate["solver_status"], "limit_reached")
        self.assertNotIn("maximum_achievable_cardinality", certificate)

    def test_milp_returns_feasible_target_incumbent_at_time_limit(self):
        timeout_with_incumbent = SimpleNamespace(
            x=[1.0, 1.0],
            success=False,
            status=1,
            message="Time limit reached.",
        )
        certificate = {}
        with patch(
            "scipy.optimize.milp",
            return_value=timeout_with_incumbent,
        ):
            selected = portfolio_selection.solve_milp_compatible_subset(
                [
                    portfolio_selection.ConstraintCandidateFacts(
                        score=1.0,
                        cap_keys=(),
                    ),
                    portfolio_selection.ConstraintCandidateFacts(
                        score=0.9,
                        cap_keys=(),
                    ),
                ],
                [[True, True], [True, True]],
                target_count=2,
                maximum_key_counts={},
                infeasibility_certificate=certificate,
            )

        self.assertEqual(selected, (0, 1))
        self.assertEqual(certificate, {})

    def test_diagnostic_timeout_does_not_claim_maximum_cardinality(self):
        exact_infeasible = SimpleNamespace(
            x=None,
            success=False,
            status=2,
            message="The problem is infeasible.",
        )
        diagnostic_timeout = SimpleNamespace(
            x=[1.0, 0.0],
            success=False,
            status=1,
            message="Time limit reached.",
        )
        certificate = {}
        with patch(
            "scipy.optimize.milp",
            side_effect=(exact_infeasible, diagnostic_timeout),
        ):
            selected = portfolio_selection.solve_milp_compatible_subset(
                [
                    portfolio_selection.ConstraintCandidateFacts(
                        score=1.0,
                        cap_keys=(),
                        coverage_tags=("only:left",),
                    ),
                    portfolio_selection.ConstraintCandidateFacts(
                        score=0.9,
                        cap_keys=(),
                        coverage_tags=("only:right",),
                    ),
                ],
                [[True, False], [False, True]],
                target_count=2,
                maximum_key_counts={},
                required_coverage_tags=("only:left", "only:right"),
                infeasibility_certificate=certificate,
            )

        self.assertEqual(selected, ())
        self.assertEqual(certificate["status"], "infeasible")
        self.assertEqual(
            certificate["diagnostic_solver_status"],
            "limit_reached",
        )
        self.assertNotIn("maximum_achievable_cardinality", certificate)

    def test_joint_ten_card_solver_keeps_sole_one_sixteenth_witness(self):
        facts = self._joint_portfolio_facts(
            [
                "spatial_reserve",
                "spatial_reserve",
                "balanced_yield",
                "balanced_yield",
                "balanced_yield",
                "brief_target",
                "brief_target",
                "maximum_feasible",
                "maximum_feasible",
                "spatial_reserve",
                "maximum_feasible",
            ],
            scopes=(
                "1/1", "3/8", "1/2", "1/4", "1/8",
                "1/1", "3/8", "1/2", "1/4", "1/8", "1/16",
            ),
            stepped_indices={5},
        )
        compatibility = self._fully_compatible(len(facts))
        compatibility[0][10] = False
        compatibility[10][0] = False

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            compatibility,
            target_count=10,
            maximum_key_counts={},
            **self._joint_portfolio_constraints({}),
        )

        self.assertEqual(len(selected), 10)
        self.assertIn(10, selected)
        self.assertNotIn(0, selected)

    def test_joint_ten_card_solver_rejects_four_stepped_candidates(self):
        facts = self._joint_portfolio_facts(
            self._balanced_capacity_bands(),
            stepped_indices={0, 1, 6, 7},
        )
        certificate = {}

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            self._fully_compatible(10),
            target_count=10,
            maximum_key_counts={},
            **self._joint_portfolio_constraints(certificate),
        )

        self.assertEqual(selected, ())
        self.assertIn("stepped:max_3", certificate["unsatisfied_constraints"])

    def test_joint_ten_card_solver_rejects_zero_stepped_candidates(self):
        facts = self._joint_portfolio_facts(
            self._balanced_capacity_bands(),
            stepped_indices=set(),
        )
        certificate = {}

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            self._fully_compatible(10),
            target_count=10,
            maximum_key_counts={},
            **self._joint_portfolio_constraints(certificate),
        )

        self.assertEqual(selected, ())
        self.assertIn("stepped:min_1", certificate["unsatisfied_constraints"])

    def test_joint_ten_card_solver_requires_an_upper_band_stepped_candidate(self):
        facts = self._joint_portfolio_facts(
            self._balanced_capacity_bands(),
            stepped_indices={0},
        )
        certificate = {}

        selected = portfolio_selection.solve_milp_compatible_subset(
            facts,
            self._fully_compatible(10),
            target_count=10,
            maximum_key_counts={},
            **self._joint_portfolio_constraints(certificate),
        )

        self.assertEqual(selected, ())
        self.assertIn(
            "upper_band_stepped:min_1",
            certificate["unsatisfied_constraints"],
        )

    def test_joint_ten_card_solver_caps_roof_and_solid_phenotype_at_three(self):
        roof_facts = self._joint_portfolio_facts(
            self._balanced_capacity_bands(),
            roof_override={
                0: "roof_repeat", 1: "roof_repeat",
                2: "roof_repeat", 3: "roof_repeat",
            },
        )
        roof_certificate = {}
        roof_selected = portfolio_selection.solve_milp_compatible_subset(
            roof_facts,
            self._fully_compatible(10),
            target_count=10,
            maximum_key_counts={},
            **self._joint_portfolio_constraints(roof_certificate),
        )
        phenotype_facts = self._joint_portfolio_facts(
            self._balanced_capacity_bands(),
            phenotype_override={
                0: "solid_repeat", 1: "solid_repeat",
                2: "solid_repeat", 3: "solid_repeat",
            },
        )
        phenotype_certificate = {}
        phenotype_selected = portfolio_selection.solve_milp_compatible_subset(
            phenotype_facts,
            self._fully_compatible(10),
            target_count=10,
            maximum_key_counts={},
            **self._joint_portfolio_constraints(phenotype_certificate),
        )

        self.assertEqual(roof_selected, ())
        self.assertIn(
            "roof:roof_repeat:max_3",
            roof_certificate["unsatisfied_constraints"],
        )
        self.assertEqual(phenotype_selected, ())
        self.assertIn(
            "solid_phenotype:solid_repeat:max_3",
            phenotype_certificate["unsatisfied_constraints"],
        )

    def test_selector_returns_no_board_and_joint_infeasibility_certificate(self):
        candidates = [
            SimpleNamespace(
                key=f"candidate_{index}",
                score=1.0 - index * 0.01,
                scope="1/1",
                band=self._balanced_capacity_bands()[index],
                stepped=index == 6,
                roof=f"roof_{index % 4}",
                phenotype=f"phenotype_{index % 4}",
                principle_kind="base_operative",
                principle_id=f"book:{index}",
                operation=f"operation_{index}",
                seed=f"seed_{index}",
                section=f"section_{index}",
                chassis=f"chassis_{index}",
                family=f"family_{index}",
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "selectable_capacity_alternative_id": (
                            self._balanced_capacity_bands()[index]
                        ),
                        "selectable_capacity_hard_pass": True,
                    },
                }),
            )
            for index in range(10)
        ]
        trace = {}
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_capacity_alternative_key", side_effect=lambda item: item.band),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": "stepped" if item.stepped else item.phenotype,
                "section_phenotype": "stepped" if item.stepped else "prismatic",
                "wedge_like": False,
                "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": f"ground_{int(item.key.rsplit('_', 1)[1]) % 3}",
                "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(portfolio_selection, "_plan_family", return_value="quadrilateral"),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=10,
                selection_trace=trace,
            )

        self.assertEqual(selected, [])
        self.assertFalse(trace["joint_ten_card_solver_target_reached"])
        certificate = trace["joint_ten_card_infeasibility_certificate"]
        self.assertEqual(certificate["maximum_achievable_cardinality"], 10)
        self.assertIn(
            "scope:1/16:min_1",
            certificate["unsatisfied_constraints"],
        )

    @staticmethod
    def _balanced_capacity_bands():
        return (
            ["spatial_reserve"] * 3
            + ["balanced_yield"] * 3
            + ["brief_target"] * 2
            + ["maximum_feasible"] * 2
        )

    @staticmethod
    def _fully_compatible(count):
        return [[True for _right in range(count)] for _left in range(count)]

    @staticmethod
    def _joint_portfolio_constraints(certificate):
        return {
            "required_scopes": (
                "1/1", "3/8", "1/2", "1/4", "1/8", "1/16",
            ),
            "capacity_band_minimum_counts": {
                "spatial_reserve": 2,
                "balanced_yield": 2,
                "brief_target": 2,
                "maximum_feasible": 2,
            },
            "capacity_band_maximum_counts": {
                "spatial_reserve": 3,
                "balanced_yield": 3,
                "brief_target": 3,
                "maximum_feasible": 3,
            },
            "required_classified_capacity_count": 10,
            "minimum_stepped_count": 1,
            "maximum_stepped_count": 3,
            "upper_band_stepped_bands": (
                "brief_target", "maximum_feasible",
            ),
            "minimum_upper_band_stepped_count": 1,
            "maximum_roof_archetype_count": 3,
            "maximum_solid_phenotype_count": 3,
            "infeasibility_certificate": certificate,
        }

    @staticmethod
    def _joint_portfolio_facts(
        bands,
        *,
        scopes=None,
        stepped_indices=frozenset({6}),
        roof_override=None,
        phenotype_override=None,
    ):
        scopes = scopes or (
            "1/1", "3/8", "1/2", "1/4", "1/8",
            "1/16", "1/1", "3/8", "1/2", "1/4",
        )
        roof_override = roof_override or {}
        phenotype_override = phenotype_override or {}
        return [
            portfolio_selection.ConstraintCandidateFacts(
                score=1.0 - index * 0.01,
                cap_keys=(),
                scope=scopes[index],
                capacity_band=band,
                stepped=index in stepped_indices,
                roof_archetype=roof_override.get(
                    index, f"roof_{index % 4}",
                ),
                solid_phenotype=phenotype_override.get(
                    index, f"phenotype_{index % 4}",
                ),
            )
            for index, band in enumerate(bands)
        ]

    def test_joint_scope_anchors_include_rare_capacity_band_before_greedy_selection(self):
        scopes = ("1/1", "1/2", "1/4", "1/8", "1/16", "3/8")
        alternatives = (
            "spatial_reserve", "balanced_yield", "brief_target",
            "maximum_feasible", "spatial_reserve", "balanced_yield",
        )
        principle_kinds = (
            "base_operative", "combination", "aggregation",
            "base_operative", "combination", "aggregation",
        )
        candidates = [
            SimpleNamespace(
                key=f"candidate_{index}",
                scope=scope,
                alternative=alternatives[index],
                principle_kind=principle_kinds[index],
                operation=f"operation_{index}",
                score=1.0 - index * 0.01,
                seed=f"seed_{index}",
                section=f"section_{index}",
                roof=f"roof_{index}",
                chassis=f"chassis_{index}",
                phenotype=f"phenotype_{index}",
            )
            for index, scope in enumerate(scopes)
        ]
        with (
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_capacity_alternative_key", side_effect=lambda item: item.alternative),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype,
                "wedge_like": False,
                "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
        ):
            anchors = portfolio_selection._scope_coverage_anchors(
                candidates,
                seed_family_cap=2,
                section_family_cap=6,
                roof_archetype_caps={candidate.roof: 2 for candidate in candidates},
                chassis_family_caps={candidate.chassis: 2 for candidate in candidates},
                phenotype_cap=6,
                wedge_like_cap=2,
                pyramidal_like_cap=2,
                required_principle_kinds=("base_operative", "combination", "aggregation"),
                required_capacity_alternatives=(
                    "spatial_reserve", "balanced_yield", "brief_target", "maximum_feasible",
                ),
            )

        self.assertEqual({candidate.scope for candidate in anchors}, set(scopes))
        self.assertIn("maximum_feasible", {candidate.alternative for candidate in anchors})

    def test_final_ast_controller_resolves_stale_snapshot_missing_concept(self):
        source = SimpleNamespace(metadata={
            "geometry_program": {
                "metadata": {"base_seed": "bar"},
                "nodes": [
                    {
                        "id": "program_projection:public_threshold",
                        "operator": "notch",
                        "parameters": {"side": "west"},
                        "semantic_role": "public_threshold",
                        "provenance": {
                            "source": "post_book_program_projection",
                            "program_invariant": True,
                        },
                    },
                ],
            },
            "program_context": {"site_access_side_in_program_frame": "west"},
            "geometry_graph_snapshot": {
                "design_concept_graph": {
                    "concept_nodes": [
                        {
                            "concept_id": "concept:public_threshold",
                            "missing_controller": True,
                        },
                    ],
                },
            },
        })
        candidate = SimpleNamespace(source=source)
        with (
            patch.object(candidate_analysis, "_architectural_articulation_metrics", return_value={"rules": []}),
            patch.object(candidate_analysis, "_roof_archetype", return_value="recursive:winged"),
        ):
            descriptor = candidate_analysis._design_concept_descriptor(candidate)

        self.assertEqual(descriptor["missing_required_concepts"], [])
        self.assertEqual(
            descriptor["resolved_snapshot_concepts_from_final_ast"],
            ["concept:public_threshold"],
        )
        self.assertEqual(
            descriptor["threshold_controller_node_ids"],
            ["program_projection:public_threshold"],
        )
        self.assertTrue(descriptor["frontage_aligned"])

    def test_replenishment_cycle_budget_is_bounded(self):
        with patch.dict(os.environ, {"MAAS_BOOK_REPLENISHMENT_CYCLES": ""}):
            self.assertEqual(portfolio_replenishment.replenishment_cycle_budget(), 1)
            self.assertEqual(
                portfolio_replenishment.replenishment_cycle_budget_for_run(live_vlm=True),
                1,
            )
            self.assertEqual(
                portfolio_replenishment.replenishment_cycle_budget_for_run(live_vlm=False),
                7,
            )
            self.assertEqual(
                portfolio_replenishment.replenishment_cycle_budget_for_run(
                    live_vlm=False,
                    smoke_mode=True,
                ),
                1,
            )
        with patch.dict(os.environ, {"MAAS_BOOK_REPLENISHMENT_CYCLES": "0"}):
            self.assertEqual(portfolio_replenishment.replenishment_cycle_budget(), 1)
        with patch.dict(os.environ, {"MAAS_BOOK_REPLENISHMENT_CYCLES": "9"}):
            self.assertEqual(portfolio_replenishment.replenishment_cycle_budget(), 8)

    def test_live_vlm_http_request_budget_is_a_process_wide_hard_cap(self):
        with (
            patch.dict(os.environ, {"MAAS_LIVE_VLM_MAX_REQUESTS": "2"}),
            patch.object(vlm_scorer, "_LIVE_VLM_REQUEST_COUNT", 0),
        ):
            self.assertEqual(vlm_scorer._consume_live_vlm_request_budget(), 1)
            self.assertEqual(vlm_scorer._consume_live_vlm_request_budget(), 2)
            with self.assertRaisesRegex(
                vlm_scorer.VlmScoringError,
                "live_vlm_request_budget_exhausted:2/2",
            ):
                vlm_scorer._consume_live_vlm_request_budget()

    def test_replenishment_does_not_stop_on_intermediate_zero_pool_growth(self):
        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                selected_count=9,
                selected_scope_count=6,
                target_count=20,
                required_scope_count=6,
                cycles_run=2,
                cycle_budget=3,
            ),
            "",
        )
        self.assertEqual(
            portfolio_replenishment.replenishment_stop_reason(
                selected_count=9,
                selected_scope_count=6,
                target_count=20,
                required_scope_count=6,
                cycles_run=3,
                cycle_budget=3,
            ),
            "cycle_budget_exhausted",
        )

    def test_final_vlm_cycle_accumulates_only_exact_hard_passes(self):
        retained = SimpleNamespace(key="retained")
        candidate = SimpleNamespace(key="new")
        repaired = SimpleNamespace(key="repaired")
        with (
            patch.object(final_vlm_cycle, "_bounded_visual_selection_pool", side_effect=lambda items: list(items)),
            patch.object(
                final_vlm_cycle,
                "_audit_final_book_geometry_with_vlm",
                side_effect=[
                    ([candidate], {"hard_pass_count": 1, "audit_records": []}),
                    ([repaired], {"hard_pass_count": 1, "audit_records": []}),
                ],
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
                [candidate],
                retained_hard_passes=[retained],
                building_type="program",
                output_dir=Path("unused"),
                visual_directive={},
                outcome_graph=object(),
                program_slug="test",
                generation_site=object(),
                height=12.0,
                floors=4,
                generation_context=object(),
                program_dimensional_context={},
                site_boundary_source="test",
                site_access_context={},
                site_access_geometry={},
                base_capacity_contract={},
                downstream_context={},
                hard_gate_summary=lambda report, pool: {"candidate_count": len(pool)},
                completion_status="complete",
                no_repair_status="no_repair",
            )

        self.assertEqual(result.selection_pool, [retained, candidate, repaired])
        self.assertEqual(result.final_vlm_gate["hard_pass_count"], 3)
        self.assertTrue(result.repair_evidence["same_run_causal_loop_closed"])

    def test_final_vlm_cycle_routes_capacity_target_labels_as_advisory(self):
        target_pass = SimpleNamespace(
            key="target-pass",
            source=SimpleNamespace(metadata={
                "capacity_alternative_projection": {"target_hard_pass": True},
            }),
        )
        target_miss = SimpleNamespace(
            key="target-miss",
            source=SimpleNamespace(metadata={
                "capacity_alternative_projection": {"target_hard_pass": False},
            }),
        )
        reviewed_inputs = []

        def audit(items, **_kwargs):
            reviewed_inputs.append(list(items))
            return list(items), {"hard_pass_count": len(items), "audit_records": []}

        with (
            patch.object(
                final_vlm_cycle,
                "_bounded_visual_selection_pool",
                side_effect=lambda items: list(items),
            ),
            patch.object(
                final_vlm_cycle,
                "_audit_final_book_geometry_with_vlm",
                side_effect=audit,
            ),
            patch.object(
                final_vlm_cycle,
                "_repair_exact_post_book_candidates_from_vlm",
                return_value=([], {"repaired_candidate_count": 0}),
            ),
        ):
            result = final_vlm_cycle.run_final_vlm_cycle(
                [target_miss, target_pass],
                retained_hard_passes=[],
                building_type="program",
                output_dir=Path("unused"),
                visual_directive={},
                outcome_graph=object(),
                program_slug="test",
                generation_site=object(),
                height=12.0,
                floors=4,
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
            )

        self.assertEqual(reviewed_inputs, [[target_miss, target_pass]])
        self.assertEqual(result.selection_pool, [target_miss, target_pass])
        self.assertEqual(
            result.initial_vlm_gate["capacity_target_routing"][
                "rejected_before_paid_vlm_count"
            ],
            0,
        )
        self.assertEqual(
            result.initial_vlm_gate["capacity_target_routing"][
                "advisory_miss_count"
            ],
            1,
        )

    def test_final_vlm_cycle_reviews_measured_target_miss_as_advisory(self):
        target_miss = SimpleNamespace(
            key="target-miss",
            source=SimpleNamespace(metadata={
                "capacity_alternative_projection": {"target_hard_pass": False},
            }),
        )

        with (
            patch.object(
                final_vlm_cycle,
                "_bounded_visual_selection_pool",
                side_effect=lambda items: list(items),
            ),
            patch.object(
                final_vlm_cycle,
                "_audit_final_book_geometry_with_vlm",
                return_value=(
                    [target_miss],
                    {"hard_pass_count": 1, "audit_records": []},
                ),
            ) as paid_review,
            patch.object(
                final_vlm_cycle,
                "_repair_exact_post_book_candidates_from_vlm",
                return_value=([], {"repaired_candidate_count": 0}),
            ) as repair,
        ):
            result = final_vlm_cycle.run_final_vlm_cycle(
                [target_miss],
                retained_hard_passes=[],
                building_type="program",
                output_dir=Path("unused"),
                visual_directive={},
                outcome_graph=object(),
                program_slug="test",
                generation_site=object(),
                height=12.0,
                floors=4,
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
            )

        paid_review.assert_called_once()
        repair.assert_called_once()
        self.assertEqual(result.selection_pool, [target_miss])
        self.assertEqual(
            result.initial_vlm_gate["capacity_target_routing"]["status"],
            "capacity_target_diagnostic_passthrough",
        )
        self.assertEqual(
            result.final_vlm_gate["status"],
            "complete",
        )

    def test_replenishment_vlm_reviews_only_new_candidates(self):
        retained = [SimpleNamespace(key="prior-pass")]
        new = [SimpleNamespace(key="new-candidate")]
        with patch.object(
            portfolio_benchmark,
            "_bounded_visual_selection_pool",
            side_effect=lambda items: list(items),
        ):
            kept, review_pool = portfolio_benchmark._partition_replenishment_vlm_candidates(
                retained,
                new,
            )

        self.assertEqual([item.key for item in kept], ["prior-pass"])
        self.assertEqual([item.key for item in review_pool], ["new-candidate"])
        self.assertNotIn(retained[0], review_pool)

    def test_individual_vlm_cache_key_is_program_and_review_stage_scoped(self):
        geometry = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]]],
        }
        neighborhood = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "program_context": {"program_id": "neighborhood_living"},
                "site_access_context": {"side": "west"},
                "portfolio_diversity_context": {"book_review_stage": "final_book"},
            },
        }
        gymnasium = {
            **neighborhood,
            "properties": {
                **neighborhood["properties"],
                "program_context": {"program_id": "gymnasium"},
            },
        }
        base_review = {
            **neighborhood,
            "properties": {
                **neighborhood["properties"],
                "portfolio_diversity_context": {
                    "book_review_stage": "book_base_operative",
                },
            },
        }

        neighborhood_key = _vlm_cache_key(neighborhood, [], "test-model")
        self.assertNotEqual(neighborhood_key, _vlm_cache_key(gymnasium, [], "test-model"))
        self.assertNotEqual(neighborhood_key, _vlm_cache_key(base_review, [], "test-model"))

    def test_base_vlm_reviews_exact_parents_of_diverse_descendants_first(self):
        def candidate(name, stage, parent_key, score):
            return SimpleNamespace(
                key=name,
                score=score,
                sequence=SimpleNamespace(name=name),
                source=SimpleNamespace(metadata={
                    "book_generation_lineage": {
                        "stage": stage,
                        "parent_key": parent_key,
                    },
                }),
            )

        base_1 = candidate("base-1", "base", "parent-1", 0.99)
        base_2 = candidate("base-2", "base", "parent-2", 0.80)
        base_3 = candidate("base-3", "base", "parent-3", 0.70)
        descendant_2 = candidate("descendant-2", "combination", "parent-2", 0.95)
        descendant_3 = candidate("descendant-3", "aggregation", "parent-3", 0.90)
        with patch.object(
            vlm_review,
            "_final_book_vlm_shortlist",
            side_effect=lambda items, target, **_kwargs: list(items)[:target],
        ):
            shortlist, evidence = vlm_review._book_base_parent_shortlist(
                [base_1, base_2, base_3, descendant_2, descendant_3],
                target=3,
                visual_directive={},
            )

        self.assertEqual([item.key for item in shortlist], ["base-2", "base-3", "base-1"])
        self.assertEqual(evidence["requested_exact_parent_count"], 2)
        self.assertTrue(evidence["descendant_first_parent_resolution"])

    def test_base_vlm_replenishment_quota_does_not_oversample_capped_family(self):
        def candidate(name, family, score):
            return SimpleNamespace(
                key=name,
                family=family,
                chassis=f"chassis-{family}",
                score=score,
                source=SimpleNamespace(metadata={
                    "book_generation_lineage": {
                        "stage": "base",
                        "parent_key": f"parent-{name}",
                    },
                }),
            )

        candidates = [
            *[candidate(f"repeat-{index}", "repeated", 1.0 - index * 0.01) for index in range(5)],
            candidate("lift", "lift", 0.80),
            candidate("notch", "notch", 0.79),
            candidate("split", "split_bridge", 0.78),
        ]
        with (
            patch.object(vlm_review, "_final_book_vlm_shortlist", side_effect=lambda items, target, **_kwargs: list(items)[:target]),
            patch.object(vlm_review, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(vlm_review, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(vlm_review, "_form_bank_lane", return_value="bounded_synthesis"),
        ):
            shortlist, evidence = vlm_review._book_base_parent_shortlist(
                candidates,
                target=4,
                visual_directive={"max_geometry_family_counts": {"repeated": 1}},
            )

        self.assertEqual(sum(item.family == "repeated" for item in shortlist), 1)
        self.assertEqual({item.family for item in shortlist}, {
            "repeated", "lift", "notch", "split_bridge",
        })
        self.assertGreater(evidence["review_cap_skip_counts"]["geometry:repeated"], 0)
        self.assertTrue(evidence["review_caps_are_supply_quotas_not_quality_relaxations"])

    def test_base_vlm_shortlist_reserves_one_review_per_chassis_before_score_fill(self):
        def candidate(name, chassis, score):
            return SimpleNamespace(
                key=name,
                family="shared-agent-family",
                chassis=chassis,
                score=score,
                source=SimpleNamespace(metadata={
                    "book_generation_lineage": {
                        "stage": "base",
                        "parent_key": f"parent-{name}",
                    },
                }),
            )

        candidates = [
            *[candidate(f"repeat-{index}", "repeated", 1.0 - index * 0.01) for index in range(5)],
            candidate("court", "courtyard", 0.70),
            candidate("split", "split-wing", 0.69),
            candidate("cross", "distributed-cross", 0.68),
        ]
        with (
            patch.object(vlm_review, "_final_book_vlm_shortlist", side_effect=lambda items, target, **_kwargs: list(items)[:target]),
            patch.object(vlm_review, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(vlm_review, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(vlm_review, "_form_bank_lane", return_value="bounded_synthesis"),
        ):
            shortlist, evidence = vlm_review._book_base_parent_shortlist(
                candidates,
                target=4,
                visual_directive={},
            )

        self.assertEqual({item.chassis for item in shortlist}, {
            "repeated", "courtyard", "split-wing", "distributed-cross",
        })
        self.assertEqual(evidence["chassis_family_anchor_count"], 4)

    def test_default_outcome_graph_is_run_scoped_and_ignores_pnu_cache_env(self):
        with TemporaryDirectory() as temporary_dir, patch.dict(
            os.environ,
            {"MAAS_OUTCOME_GRAPH_DIR": str(Path(temporary_dir) / "pnu-cache")},
        ):
            output_dir = Path(temporary_dir) / "run-r268"
            graph_path = portfolio_benchmark.default_outcome_graph_path(output_dir)

        self.assertEqual(
            graph_path,
            output_dir.resolve() / "maas-geometry-mutation-outcome-graph.json",
        )

    def test_final_vlm_shortlist_reserves_review_bandwidth_for_typed_llm_author_lane(self):
        procedural = [
            SimpleNamespace(
                key=f"procedural-{index}",
                score=1.0 - index * 0.001,
                authored=False,
                family=f"agent_family_{index % 8}",
                scope=("1/1", "1/2", "1/4", "1/8")[index % 4],
                phenotype=("prismatic", "stepped", "voided")[index % 3],
                principle_kind="base_operative",
            )
            for index in range(100)
        ]
        authored = [
            SimpleNamespace(
                key=f"authored-{index}",
                score=0.7 - index * 0.001,
                authored=True,
                family=f"llm_family_{index % 5}",
                scope=("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")[index % 6],
                phenotype=("curved", "oblique", "winged", "voided")[index % 4],
                principle_kind="combination",
            )
            for index in range(20)
        ]
        pool = [*procedural, *authored]
        with (
            patch.object(vlm_review, "_llm_authored_candidate", side_effect=lambda item: item.authored),
            patch.object(vlm_review, "_form_bank_lane", return_value=""),
            patch.object(vlm_review, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(vlm_review, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(vlm_review, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype,
            }),
            patch.object(vlm_review, "_select", side_effect=lambda items, target, **_kwargs: list(items)[:target]),
        ):
            shortlist = portfolio_benchmark._final_book_vlm_shortlist(
                pool,
                target=64,
                visual_directive={},
            )

        self.assertEqual(len(shortlist), 64)
        self.assertGreaterEqual(sum(item.authored for item in shortlist), 16)

    def test_final_vlm_shortlist_reviews_each_available_executable_core_family(self):
        synthesized = [
            SimpleNamespace(
                key=f"synthesized-{index}",
                score=1.0 - index * 0.001,
                lane="bounded_synthesis",
                family=f"agent_family_{index % 12}",
                scope=("1/1", "1/2", "1/4", "1/8")[index % 4],
                phenotype=("prismatic", "stepped", "voided")[index % 3],
                principle_kind="base_operative",
            )
            for index in range(120)
        ]
        core = [
            SimpleNamespace(
                key=f"core-{family}-{variant}",
                score=0.65 - family * 0.002 - variant * 0.001,
                lane="executable_core_language",
                family=f"core_family_{family}",
                scope=("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")[variant % 6],
                phenotype=("winged", "voided", "curved")[variant % 3],
                principle_kind="combination",
            )
            for family in range(18)
            for variant in range(2)
        ]
        pool = [*synthesized, *core]
        with (
            patch.object(vlm_review, "_llm_authored_candidate", return_value=False),
            patch.object(vlm_review, "_form_bank_lane", side_effect=lambda item: item.lane),
            patch.object(vlm_review, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(vlm_review, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(vlm_review, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype,
            }),
            patch.object(vlm_review, "_select", side_effect=lambda items, target, **_kwargs: list(items)[:target]),
        ):
            shortlist = vlm_review._final_book_vlm_shortlist(
                pool,
                target=64,
                visual_directive={},
            )

        reviewed_core_families = {
            item.family for item in shortlist
            if item.lane == "executable_core_language"
        }
        self.assertEqual(len(shortlist), 64)
        self.assertEqual(reviewed_core_families, {f"core_family_{index}" for index in range(18)})
        self.assertGreaterEqual(
            sum(item.lane == "executable_core_language" for item in shortlist),
            36,
        )

    def test_portfolio_capacity_descriptor_separates_requested_and_resolved_band(self):
        site = Polygon(((0, 0), (20, 0), (20, 16), (0, 16)))
        sequence = program_seed_sequences("neighborhood_living")[0]
        source = compile_sequence_to_source_mass(site, sequence)
        self.assertIsNotNone(source)
        assert source is not None
        source = replace(source, metadata={
            **source.metadata,
            "capacity_alternative_projection": {
                "alternative_id": "maximum_feasible",
                "target_utilization": 0.95,
                "target_hard_pass": False,
                "feasible_minimum_utilization": 0.70,
                "requested_capacity_alternative_id": "maximum_feasible",
                "requested_target_utilization": 0.95,
                "selectable_capacity_alternative_id": "balanced_yield",
                "selectable_capacity_target_utilization": 0.80,
                "selectable_capacity_hard_pass": True,
            },
            "source_capacity_measurement": {
                "feasible_capacity_utilization": 0.8241,
                "far_pct": 103.689,
            },
        })
        candidate = portfolio_benchmark._Candidate(
            "book:operative:test",
            "base_operative",
            "test",
            sequence,
            source,
            {"type": "Feature", "geometry": None, "properties": {}},
            0.8,
        )

        descriptor = portfolio_benchmark._candidate_language_descriptor(candidate)

        self.assertEqual(
            descriptor.get("requested_capacity_alternative_id"),
            "maximum_feasible",
        )
        self.assertEqual(descriptor.get("requested_capacity_target_utilization"), 0.95)
        self.assertFalse(descriptor.get("requested_capacity_target_hard_pass"))
        self.assertEqual(
            descriptor.get("resolved_capacity_alternative_id"),
            "balanced_yield",
        )
        self.assertEqual(descriptor.get("resolved_capacity_target_utilization"), 0.80)
        self.assertTrue(descriptor.get("resolved_capacity_hard_pass"))
        self.assertEqual(descriptor["capacity_alternative_id"], "balanced_yield")
        self.assertEqual(descriptor["capacity_target_utilization"], 0.80)
        self.assertTrue(descriptor["capacity_target_hard_pass"])

    def test_final_vlm_recovers_transient_call_failure_and_reports_it(self):
        site = Polygon(((0, 0), (20, 0), (20, 16), (0, 16)))
        sequence = program_seed_sequences("neighborhood_living")[0]
        source = compile_sequence_to_source_mass(site, sequence)
        self.assertIsNotNone(source)
        assert source is not None
        program = base_seed_program("slab")
        source = replace(source, metadata={
            **source.metadata,
            "geometry_program": program.to_dict(),
            "source_capacity_measurement": {
                "utilization_ratio": 0.8,
                "total_floor_area_m2": 240.0,
            },
            "capacity_alternative_projection": {
                "requested_capacity_alternative_id": "brief_target",
                "requested_target_utilization": 0.90,
                "selectable_capacity_alternative_id": "balanced",
                "selectable_capacity_target_utilization": 0.80,
                "selectable_capacity_hard_pass": True,
            },
            "shared_floor_contract": {
                "schema_version": "arr.maas.shared_floor_contract.v1",
                "floor_contract_hash": "floor-contract-test",
                "floor_capacity_plan_hash": "floor-plan-test",
                "target_floor_areas_m2": [80.0, 80.0, 80.0],
                "totals": {"requested_floors": 3, "total_floor_area_m2": 240.0},
                "hard_pass": True,
            },
        })
        candidate = portfolio_benchmark._Candidate(
            "book:operative:test",
            "base_operative",
            "test",
            sequence,
            source,
            {"type": "Feature", "geometry": None, "properties": {}},
            0.8,
        )
        attempts = 0
        reviewed_features = []

        def flaky_scorer(**kwargs):
            nonlocal attempts
            attempts += 1
            reviewed_features.append(kwargs["feature"])
            if attempts == 1:
                raise TimeoutError("transient unit-test timeout")
            return {
                "concept_scores": {},
                "critic_actions": [],
                "geometry_edits": [],
                "response_id": "recovered-response",
                "model": "test-vlm",
                "vlm_image_inputs": {
                    "schema_version": "arr.maas.vlm_image_inputs.v1",
                    "candidate": {
                        "sha256": "candidate-image-sha",
                        "program_hash": "program-hash",
                        "geometry_hash": "geometry-hash",
                        "used_by_vlm": True,
                    },
                    "references": [
                        {
                            "source_id": "archdaily_test",
                            "sha256": "reference-image-sha",
                            "used_by_vlm": True,
                        }
                    ],
                },
            }

        with (
            TemporaryDirectory() as temporary_dir,
            patch.object(vlm_review, "_audited_final_book_references", return_value=([], {
                "hard_pass": True,
                "accepted": [],
            })),
            patch.object(vlm_review, "_solid_morphology_metrics", return_value={
                "phenotype": "prismatic",
                "pyramidal_like": False,
            }),
            patch.object(vlm_review, "_final_book_vlm_hard_pass", return_value=(True, [])),
            patch.dict(os.environ, {"MAAS_FINAL_BOOK_VLM_RECOVERY_WORKERS": "1"}),
        ):
            accepted, evidence = vlm_review._audit_final_book_geometry_with_vlm(
                [candidate],
                building_type="neighborhood_living",
                output_dir=Path(temporary_dir),
                visual_directive={},
                scorer=flaky_scorer,
                shortlist_override=[candidate],
            )

        self.assertEqual(attempts, 2)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(evidence["initial_call_failure_count"], 1)
        self.assertEqual(evidence["recovered_call_failure_count"], 1)
        self.assertEqual(evidence["unrecovered_call_failure_count"], 0)
        self.assertEqual(evidence["call_failure_records"], [])
        self.assertNotIn("source_surfaces", candidate.feature["properties"])
        self.assertGreater(
            len(reviewed_features[-1]["properties"]["source_surfaces"]),
            0,
        )
        capacity_context = reviewed_features[-1]["properties"]["capacity_review_context"]
        self.assertEqual(
            capacity_context["capacity_alternative"][
                "selectable_capacity_alternative_id"
            ],
            "balanced",
        )
        self.assertEqual(
            capacity_context["target_floor_areas_m2"],
            [80.0, 80.0, 80.0],
        )
        self.assertEqual(
            accepted[0].source.metadata["final_book_vlm_audit"][
                "capacity_review_context"
            ]["floor_contract_hash"],
            "floor-contract-test",
        )
        image_inputs = accepted[0].source.metadata["final_book_vlm_audit"][
            "vlm_image_inputs"
        ]
        self.assertEqual(
            image_inputs["candidate"]["sha256"],
            "candidate-image-sha",
        )
        self.assertEqual(
            image_inputs["references"][0]["source_id"],
            "archdaily_test",
        )

    def test_final_vlm_rejects_legacy_candidate_before_provider_call(self):
        legacy = SimpleNamespace(
            source=SimpleNamespace(metadata={}),
            feature={"type": "Feature", "properties": {}},
            sequence=SimpleNamespace(name="legacy-program-sequence"),
            score=0.9,
        )

        def scorer_must_not_run(**_kwargs):
            raise AssertionError("legacy geometry must not reach the exact-AST VLM")

        with TemporaryDirectory() as temporary_dir:
            accepted, evidence = vlm_review._audit_final_book_geometry_with_vlm(
                [legacy],
                building_type="neighborhood_living",
                output_dir=Path(temporary_dir),
                visual_directive={},
                scorer=scorer_must_not_run,
                shortlist_override=[legacy],
            )

        self.assertEqual(accepted, [])
        self.assertEqual(evidence["input_count"], 1)
        self.assertEqual(evidence["exact_geometry_program_input_count"], 0)
        self.assertEqual(evidence["invalid_geometry_program_rejected_count"], 1)
        self.assertEqual(evidence["initial_call_failure_count"], 0)

    def test_final_vlm_typed_edit_keeps_authored_mass_and_only_records_floor_sibling(self):
        site = Polygon(((0, 0), (42, 0), (42, 30), (0, 30)))
        sequence = program_seed_sequences("gymnasium")[0]
        source = compile_sequence_to_source_mass(site, sequence)
        self.assertIsNotNone(source)
        assert source is not None
        parent_program = base_seed_program("slab")
        parent_capacity_alternative = {
            "schema_version": "arr.maas.capacity_alternative_projection.v1",
            "alternative_id": "maximum_feasible",
            "target_utilization": 0.98,
            "target_floor_area_m2": 3704.4,
        }
        base_capacity_contract = {
            "schema_version": "arr.maas.feasible_base_capacity.v1",
            "minimum_utilization": 0.70,
            "target_utilization": 0.90,
            "feasible_maximum_floor_area_m2": 3780.0,
            "generation_site_area_m2": float(site.area),
            "requested_floors": 3,
        }
        source = replace(source, metadata={
            **source.metadata,
            "geometry_program": parent_program.to_dict(),
            "geometry_program_bridge_evidence": {"legal_fit_strength": 0.0},
            "legal_generation_context_evidence": {},
            "capacity_alternative_projection": parent_capacity_alternative,
            "floorwise_legal_matrix_stack": {
                "status": "materialized",
                "target_plan_coverage": 0.74,
            },
        })
        candidate = portfolio_benchmark._Candidate(
            "test-principle",
            "base_operative",
            "expand",
            sequence,
            source,
            {"type": "Feature", "properties": {}},
            0.8,
        )
        audit_gate = {"audit_records": [{
            "source_sequence": sequence.name,
            "hard_pass": False,
            "response_id": "critic-exact-1",
            "geometry_edits": [{
                "operation": "set_parameter",
                "target_node_id": "seed_slab",
                "parameter_name": "vector",
                "vector_value": [2.65, 1.25, 0.34],
            }],
        }]}

        materialize_calls = []
        materialized_sources = []

        def materialize(_base_source, repaired_program, **kwargs):
            materialize_calls.append(kwargs)
            repaired_source = compile_geometry_program_to_source_mass(
                repaired_program,
                site,
            )
            self.assertIsNotNone(repaired_source)
            assert repaired_source is not None
            repaired_source = replace(repaired_source, metadata={
                **source.metadata,
                **repaired_source.metadata,
                "geometry_program": repaired_program.to_dict(),
            })
            materialized_sources.append(repaired_source)
            return repaired_source

        def attach_evidence(feature, **_kwargs):
            feature.setdefault("properties", {})["program_spatial_evidence"] = {
                "architectural_score": 0.82,
            }
            return {"hard_pass": True, "program_fit_score": 0.84}

        with (
            patch.object(vlm_review, "compile_sequence_to_source_mass", return_value=source),
            patch.object(vlm_review, "replace_source_dominant_with_geometry_program", side_effect=materialize),
            patch.object(vlm_review, "_clean_mass_gate", return_value=(True, {"failure_reasons": []})),
            patch.object(vlm_review, "_inside_site", return_value=True),
            patch.object(vlm_review, "source_feature", return_value={"type": "Feature", "properties": {}}),
            patch.object(vlm_review, "attach_program_massing_evidence", side_effect=attach_evidence),
            patch.object(vlm_review, "_program_form_gate", return_value={"hard_pass": True}),
            patch.object(vlm_review, "measure_source_capacity", return_value={
                "schema_version": "arr.maas.source_capacity_measurement.v1",
                "feasible_capacity_utilization": 0.99,
            }),
            patch.object(
                vlm_review,
                "materialize_floorwise_legal_source",
                side_effect=lambda repaired_source, **_kwargs: replace(
                    repaired_source,
                    name="capacity-floorwise-sibling",
                    footprint=Polygon(((0, 0), (6, 0), (6, 6), (0, 6))),
                    metadata={
                        **repaired_source.metadata,
                        "floorwise_legal_matrix_stack": {
                            "status": "materialized",
                            "visual_hash": "capacity-sibling-hash",
                        },
                    },
                ),
            ) as floorwise_reprojection,
            patch.object(
                vlm_review,
                "_materialize_repaired_floor_contract",
                return_value={
                    "schema_version": "arr.maas.shared_floor_contract.v1",
                    "hard_pass": False,
                    "failure_reasons": ["insufficient_clear_floor_depth"],
                },
            ),
            patch.object(vlm_review, "generation_site_at_height", return_value=site),
        ):
            repaired, counts = portfolio_benchmark._repair_exact_post_book_candidates_from_vlm(
                [candidate],
                audit_gate,
                generation_site=site,
                building_type="gymnasium",
                height=18.0,
                floors=3,
                generation_context=SimpleNamespace(),
                program_dimensional_context={},
                site_boundary_source="unit_test",
                site_access_context={},
                site_access_geometry=None,
                base_capacity_contract=base_capacity_contract,
                capacity_site=site,
            )

        self.assertEqual(len(repaired), 1)
        self.assertEqual(counts["geometry_changed_count"], 1)
        self.assertEqual(counts["repaired_candidate_count"], 1)
        self.assertEqual(counts["floorwise_legal_reprojection_count"], 0)
        self.assertEqual(floorwise_reprojection.call_count, 1)
        self.assertEqual(
            floorwise_reprojection.call_args.kwargs["target_plan_coverage"],
            0.74,
        )
        self.assertEqual(
            materialize_calls[0]["minimum_host_plan_coverage"],
            0.0,
        )
        self.assertNotEqual(
            repaired[0].source.name,
            "capacity-floorwise-sibling",
        )
        self.assertEqual(
            repaired[0].source.footprint,
            materialized_sources[0].footprint,
        )
        self.assertTrue(
            repaired[0].source.metadata["floorwise_legal_sibling_evidence"][
                "visible_authored_geometry_preserved"
            ]
        )
        self.assertFalse(
            repaired[0].source.metadata["shared_floor_contract"]["hard_pass"]
        )
        self.assertFalse(counts["book_reprojection_applied"])
        repaired_program = repaired[0].source.metadata["geometry_program"]
        self.assertEqual(
            repaired_program["metadata"]["final_vlm_repair"]["parent_program_hash"],
            parent_program.program_hash(),
        )
        self.assertNotEqual(
            compile_geometry_program(parent_program).geometry_hash,
            compile_geometry_program(type(parent_program).from_dict(repaired_program)).geometry_hash,
        )
        repaired_capacity = repaired[0].source.metadata["capacity_alternative_projection"]
        self.assertEqual(repaired_capacity["alternative_id"], "maximum_feasible")
        self.assertEqual(repaired_capacity["target_utilization"], 0.98)
        self.assertTrue(repaired_capacity["target_hard_pass"])
        repaired_source = repaired[0].source
        self.assertTrue(repaired_source.surfaces)
        self.assertEqual(
            repaired_source.metadata["floorwise_visual_projection"][
                "certification_mode"
            ],
            "authored_visual_legal_validation",
        )
        artifact = portfolio_benchmark._certified_projected_visual_artifact(
            repaired_source
        )
        artifact["identity"] = {
            "geometryHash": artifact["projectedVisualGeometryHash"],
        }
        rebound = validate_projected_visual_artifact(artifact)
        self.assertIsNotNone(rebound)
        self.assertEqual(
            rebound.visual_hash,
            repaired_source.metadata["floorwise_visual_projection"][
                "visual_hash"
            ],
        )

    def test_exact_post_book_repair_reserves_bandwidth_for_typed_llm_ast(self):
        candidates = []
        records = {}
        for index in range(12):
            authored = index >= 8
            name = f"candidate-{index}"
            program_metadata = {
                "family": f"{'llm' if authored else 'agent'}_{index}",
                **({"author_provider": "openai_llm_geometry_author"} if authored else {}),
            }
            candidates.append(SimpleNamespace(
                sequence=SimpleNamespace(name=name),
                source=SimpleNamespace(metadata={
                    "geometry_program": {"metadata": program_metadata},
                }),
                score=1.0 - index * 0.01,
            ))
            records[name] = {
                "failures": ["final_book_unresolved_public_threshold_relation"],
                "concept_scores": {
                    "gesture_clarity": 0.78,
                    "hierarchy": 0.76,
                    "repair_integrity": 0.82,
                    "program_appropriateness": 0.7,
                    "void_publicness": 0.62,
                    "section_program_fit": 0.66,
                },
            }

        selected = portfolio_benchmark._exact_post_book_repair_shortlist(
            candidates,
            records,
            repair_budget=6,
        )

        self.assertEqual(len(selected), 6)
        self.assertEqual(
            sum(portfolio_benchmark._llm_authored_candidate(candidate) for candidate in selected),
            4,
        )

    def test_vlm_normalization_rejects_arbitrary_tier_before_archive(self):
        scores = {
            "gesture_clarity": 0.82,
            "hierarchy": 0.84,
            "non_stair_silhouette": 0.22,
            "void_publicness": 0.76,
            "repair_integrity": 0.86,
            "precedent_resonance": 0.72,
            "program_appropriateness": 0.80,
            "section_program_fit": 0.66,
        }
        unresolved = _normalize_vlm_result({
            "concept_scores": scores,
            "program_fit_hard_pass": True,
            "critic_actions": ["preserve_dominant_gesture"],
        }, model="test-vlm", response_id="unresolved")
        intentional = _normalize_vlm_result({
            "concept_scores": scores,
            "program_fit_hard_pass": True,
            "critic_actions": ["good_step_mass"],
        }, model="test-vlm", response_id="intentional")

        self.assertFalse(unresolved["program_fit_hard_pass"])
        self.assertIn("weak_form_continuity", unresolved["critic_actions"])
        self.assertTrue(intentional["program_fit_hard_pass"])

    def test_final_book_vlm_gate_rejects_fragmentation_and_arbitrary_tiers(self):
        accepted, accepted_failures = portfolio_benchmark._final_book_vlm_hard_pass({
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.82,
                "hierarchy": 0.80,
                "repair_integrity": 0.78,
                "program_appropriateness": 0.76,
                "non_stair_silhouette": 0.82,
            },
            "critic_actions": ["good_step_mass", "preserve_dominant_gesture"],
        })
        fragmented, fragmented_failures = portfolio_benchmark._final_book_vlm_hard_pass({
            "program_fit_hard_pass": True,
            "concept_scores": {"non_stair_silhouette": 0.71},
            "critic_actions": ["too_fragmented", "weak_form_continuity"],
        })
        tiered, tiered_failures = portfolio_benchmark._final_book_vlm_hard_pass({
            "program_fit_hard_pass": True,
            "concept_scores": {"non_stair_silhouette": 0.41},
            "critic_actions": [],
        })

        self.assertTrue(accepted)
        self.assertEqual(accepted_failures, [])
        self.assertFalse(fragmented)
        self.assertIn("final_book_vlm_too_fragmented", fragmented_failures)
        self.assertIn("final_book_vlm_weak_form_continuity", fragmented_failures)
        self.assertFalse(tiered)
        self.assertIn("final_book_arbitrary_tier_silhouette", tiered_failures)

    def test_base_book_vlm_gate_preserves_developable_parent_for_descendants(self):
        result = {
            "program_fit_hard_pass": False,
            "concept_scores": {
                "gesture_clarity": 0.66,
                "hierarchy": 0.64,
                "repair_integrity": 0.74,
                "program_appropriateness": 0.55,
                "non_stair_silhouette": 0.44,
            },
            "critic_actions": [
                "too_box_like", "weak_form_continuity", "wrong_program_typology",
            ],
        }

        base_pass, base_failures = portfolio_benchmark._final_book_vlm_hard_pass(
            result,
            review_stage="book_base_operative",
        )
        final_pass, final_failures = portfolio_benchmark._final_book_vlm_hard_pass(result)

        self.assertTrue(base_pass)
        self.assertEqual(base_failures, [])
        self.assertFalse(final_pass)
        self.assertIn("final_book_program_fit_failed", final_failures)
        self.assertIn("final_book_vlm_too_box_like", final_failures)
        self.assertIn("final_book_vlm_wrong_program_typology", final_failures)

    def test_book_vlm_capacity_floor_is_advisory_to_visual_hard_gate(self):
        base_policy = vlm_review.book_vlm_stage_policy("book_base_operative")
        final_policy = vlm_review.book_vlm_stage_policy("final_book")

        self.assertEqual(base_policy.minimum_feasible_capacity_utilization, 0.40)
        self.assertEqual(final_policy.minimum_feasible_capacity_utilization, 0.40)
        self.assertEqual(base_policy.capacity_normalization, "book_scope_fraction")
        self.assertEqual(final_policy.capacity_normalization, "none")

        candidate = SimpleNamespace(source=SimpleNamespace(metadata={
            "program_book_projection_evidence": {
                "scope": {"base_volume_label": "1/16"},
            },
        }))
        self.assertAlmostEqual(
            vlm_review._book_stage_capacity_floor(candidate, "book_base_operative"),
            0.025,
        )
        self.assertAlmostEqual(
            vlm_review._book_stage_capacity_floor(candidate, "final_book"),
            0.40,
        )

        result = {
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.82,
                "hierarchy": 0.80,
                "repair_integrity": 0.78,
                "program_appropriateness": 0.76,
                "non_stair_silhouette": 0.82,
            },
            "critic_actions": ["preserve_dominant_gesture"],
        }
        viable, viable_failures = vlm_review._final_book_vlm_hard_pass(
            result,
            candidate_capacity={"feasible_capacity_utilization": 0.45},
            minimum_capacity_utilization=final_policy.minimum_feasible_capacity_utilization,
        )
        undersized, undersized_failures = vlm_review._final_book_vlm_hard_pass(
            result,
            candidate_capacity={"feasible_capacity_utilization": 0.39},
            minimum_capacity_utilization=final_policy.minimum_feasible_capacity_utilization,
        )

        self.assertTrue(viable)
        self.assertEqual(viable_failures, [])
        self.assertTrue(undersized)
        self.assertNotIn(
            "book_stage_feasible_capacity_below_competition_floor",
            undersized_failures,
        )

    def test_program_site_infeasible_stops_before_mass_generation_and_persists_evidence(self):
        site = Polygon(((0, 0), (40, 0), (40, 30), (0, 30)))
        generation_context = SimpleNamespace(
            generation_site=site,
            envelope=SimpleNamespace(bcr_limit=60.0, far_limit=200.0),
        )
        infeasible_dimensions = {
            "schema_version": "arr.maas.program_dimensional_context.v1",
            "program_id": "gymnasium",
            "status": "infeasible",
            "selected_subtype": "none",
            "effective_height_m": 0.0,
            "effective_floors": 0,
            "generation_host_area_m2": 429.7,
            "generation_host_short_axis_m": 6.215,
            "generation_host_long_axis_m": 85.423,
            "estimated_clear_span_capacity_m": 5.718,
            "available_subtypes": [
                "long_span_sports_hall",
                "compact_training_hall",
            ],
            "failure_reasons": [
                "legal_generation_site_cannot_fit_minimum_program_span",
            ],
        }
        materialized_plan = {
            "schema_version": "arr.maas.floor_capacity_plan.v1",
            "status": "materialized",
            "selected_height_m": 9.0,
            "selected_floor_count": 3,
            "floor_capacity_plan_hash": "pnu2-floor-plan",
            "failure_reasons": [],
        }

        with (
            TemporaryDirectory() as temporary_dir,
            patch.object(
                portfolio_benchmark,
                "build_legal_generation_context",
                return_value=generation_context,
            ),
            patch.object(
                portfolio_benchmark,
                "_program_dimensional_context",
                return_value=infeasible_dimensions,
            ),
            patch.object(
                portfolio_benchmark,
                "_resolve_authoritative_floor_context",
                return_value=(9.0, 3, materialized_plan),
            ),
            patch.object(
                portfolio_benchmark,
                "build_feasible_capacity_contract",
                return_value={"status": "materialized"},
            ),
            patch.object(
                portfolio_benchmark,
                "_program_pool",
                side_effect=AssertionError("MASS generation must not run"),
            ),
            patch.object(
                portfolio_benchmark.GeometryOutcomeGraph,
                "mirror_to_neo4j",
                return_value={"status": "not_requested"},
            ),
            patch.object(
                portfolio_benchmark,
                "publish_geometry_portfolio_shadow",
                return_value={"status": "not_requested"},
            ),
        ):
            output_dir = Path(temporary_dir)
            result = portfolio_benchmark.run_book_program_portfolios(
                site,
                pnu="1168011800104670003",
                output_dir=output_dir,
                constraints=[],
                program_slugs=("gymnasium",),
                smoke_mode=True,
                diagnostic_target=3,
            )
            persisted = json.loads(
                (output_dir / "maas-book-programs-summary.json").read_text(
                    encoding="utf-8",
                )
            )

        program = result["programs"][0]
        persisted_program = persisted["programs"][0]
        self.assertEqual(result["status"], "diagnostic_only")
        self.assertEqual(program["status"], "diagnostic_only")
        self.assertEqual(
            program["generation_status"],
            "program_site_infeasible",
        )
        self.assertEqual(program["selected_count"], 0)
        self.assertEqual(program["downstream_hard_gate"]["status"], "fail")
        self.assertIn("program_site_infeasible", program["failures"])
        self.assertIn("selected_count_below_target_3", program["failures"])
        self.assertIn(
            "selected_count_below_minimum_10",
            program["portfolio_completion"]["failures"],
        )
        self.assertEqual(
            program["counts"]["early_stop"]["status"],
            "program_site_infeasible",
        )
        self.assertEqual(
            program["counts"]["early_stop"]["dimensional_evidence"][
                "generation_host_short_axis_m"
            ],
            6.215,
        )
        self.assertEqual(
            program["counts"]["early_stop"]["dimensional_evidence"][
                "effective_height_m"
            ],
            0.0,
        )
        self.assertEqual(
            persisted_program["generation_status"],
            "program_site_infeasible",
        )
        self.assertEqual(
            persisted_program["counts"]["early_stop"][
                "floor_capacity_plan_evidence"
            ]["status"],
            "materialized",
        )

    def test_program_site_compatible_still_reaches_mass_generation(self):
        class GenerationReached(RuntimeError):
            pass

        site = Polygon(((0, 0), (40, 0), (40, 30), (0, 30)))
        generation_context = SimpleNamespace(
            generation_site=site,
            envelope=SimpleNamespace(bcr_limit=60.0, far_limit=200.0),
        )
        compatible_dimensions = {
            "status": "feasible",
            "selected_subtype": "compact_training_hall",
            "effective_height_m": 9.0,
            "effective_floors": 3,
            "failure_reasons": [],
        }
        materialized_plan = {
            "schema_version": "arr.maas.floor_capacity_plan.v1",
            "status": "materialized",
            "selected_height_m": 9.0,
            "selected_floor_count": 3,
            "floor_capacity_plan_hash": "compatible-floor-plan",
            "failure_reasons": [],
        }

        with (
            TemporaryDirectory() as temporary_dir,
            patch.object(
                portfolio_benchmark,
                "build_legal_generation_context",
                return_value=generation_context,
            ),
            patch.object(
                portfolio_benchmark,
                "_program_dimensional_context",
                return_value=compatible_dimensions,
            ),
            patch.object(
                portfolio_benchmark,
                "_resolve_authoritative_floor_context",
                return_value=(9.0, 3, materialized_plan),
            ),
            patch.object(
                portfolio_benchmark,
                "build_feasible_capacity_contract",
                return_value={"status": "materialized"},
            ),
            patch.object(
                portfolio_benchmark,
                "_program_pool",
                side_effect=GenerationReached("MASS generation reached"),
            ),
        ):
            with self.assertRaisesRegex(GenerationReached, "MASS generation reached"):
                portfolio_benchmark.run_book_program_portfolios(
                    site,
                    pnu="1168011800104170004",
                    output_dir=Path(temporary_dir),
                    constraints=[],
                    program_slugs=("gymnasium",),
                )

    def test_final_book_vlm_gate_requires_massing_legible_reference_images(self):
        hard_pass, failures = portfolio_benchmark._final_book_vlm_hard_pass({
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.82,
                "hierarchy": 0.80,
                "repair_integrity": 0.78,
                "program_appropriateness": 0.76,
                "non_stair_silhouette": 0.82,
            },
            "critic_actions": ["preserve_dominant_gesture"],
            "reference_massing_gate": {
                "hard_pass": False,
                "minimum_program_specific_images": 3,
                "massing_suitable_program_image_count": 2,
            },
        })

        self.assertFalse(hard_pass)
        self.assertIn("final_book_reference_massing_suitability_failed", failures)

    def test_final_book_vlm_gate_requires_program_relation_for_pyramidal_mass(self):
        base_result = {
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.82,
                "hierarchy": 0.80,
                "repair_integrity": 0.78,
                "program_appropriateness": 0.76,
                "non_stair_silhouette": 0.72,
                "void_publicness": 0.40,
                "section_program_fit": 0.48,
            },
            "critic_actions": ["good_step_mass"],
        }

        hard_pass, failures = portfolio_benchmark._final_book_vlm_hard_pass(
            base_result,
            candidate_morphology={"pyramidal_like": True, "section_phenotype": "none"},
            candidate_design_concept={"frontage_aligned": False},
        )
        resolved_result = {
            **base_result,
            "concept_scores": {
                **base_result["concept_scores"],
                "section_program_fit": 0.78,
            },
        }
        resolved, resolved_failures = portfolio_benchmark._final_book_vlm_hard_pass(
            resolved_result,
            candidate_morphology={"pyramidal_like": True, "section_phenotype": "stepped"},
            candidate_design_concept={"frontage_aligned": False},
        )

        self.assertFalse(hard_pass)
        self.assertIn("final_book_unresolved_pyramidal_program_relation", failures)
        self.assertTrue(resolved)
        self.assertEqual(resolved_failures, [])

    def test_final_book_vlm_gate_does_not_accept_unresolved_access_side_void_request(self):
        result = {
            "program_fit_hard_pass": True,
            "concept_scores": {
                "gesture_clarity": 0.84,
                "hierarchy": 0.78,
                "repair_integrity": 0.82,
                "program_appropriateness": 0.72,
                "non_stair_silhouette": 0.70,
                "void_publicness": 0.34,
            },
            "critic_actions": ["needs_carved_void", "preserve_dominant_gesture"],
        }

        hard_pass, failures = portfolio_benchmark._final_book_vlm_hard_pass(
            result,
            candidate_morphology={"pyramidal_like": False, "section_phenotype": "none"},
            candidate_design_concept={
                "target_access_side_in_program_frame": "west",
                "frontage_aligned": False,
            },
        )

        self.assertFalse(hard_pass)
        self.assertIn("final_book_unresolved_public_threshold_relation", failures)

    def test_portfolio_joint_anchor_preserves_all_available_book_language_depths(self):
        scopes = ("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")
        kinds = ("base_operative", "base_operative", "combination", "base_operative", "aggregation", "base_operative")
        candidates = [
            SimpleNamespace(
                scope=scope,
                principle_kind=kind,
                operation=f"op_{index}",
                score=1.0 - index * 0.01,
                seed=f"seed_{index}",
                section=f"section_{index % 2}",
                roof=f"roof_{index % 3}",
                chassis=f"chassis_{index % 2}",
                phenotype="oblique" if index else "curved",
            )
            for index, (scope, kind) in enumerate(zip(scopes, kinds))
        ]
        with (
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {"phenotype": item.phenotype}),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
        ):
            anchors = portfolio_benchmark._scope_coverage_anchors(
                candidates,
                seed_family_cap=2,
                section_family_cap=4,
                roof_archetype_caps={f"roof_{index}": 4 for index in range(3)},
                chassis_family_caps={f"chassis_{index}": 4 for index in range(2)},
                phenotype_cap=5,
                wedge_like_cap=2,
                pyramidal_like_cap=2,
                required_phenotypes=("curved", "oblique"),
                required_principle_kinds=("base_operative", "combination", "aggregation"),
            )

        self.assertEqual({item.scope for item in anchors}, set(scopes))
        self.assertEqual(
            {item.principle_kind for item in anchors},
            {"base_operative", "combination", "aggregation"},
        )

    def test_selector_does_not_complete_board_without_achieved_capacity_bands(self):
        scopes = ["1/1", "3/8", "1/2", "1/4", "1/8", "1/16"]
        candidates = []
        for index, scope in enumerate(scopes):
            for pyramidal in (True, False):
                candidates.append(SimpleNamespace(
                    key=f"{scope}:{pyramidal}",
                    scope=scope,
                    principle_kind="base_operative",
                    operation=f"operation_{index}_{int(pyramidal)}",
                    score=1.0 if pyramidal else 0.8,
                    seed=f"seed_{index}_{int(pyramidal)}",
                    section=f"section_{index}_{int(pyramidal)}",
                    roof=f"roof_{index}_{int(pyramidal)}",
                    chassis=f"chassis_{index}_{int(pyramidal)}",
                    phenotype="stepped" if pyramidal else f"non_step_{index}",
                    pyramidal=pyramidal,
                ))
        trace = {}
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype,
                "wedge_like": False,
                "pyramidal_like": item.pyramidal,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge",
                "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(portfolio_selection, "_geometry_program_family", return_value=""),
            patch.object(portfolio_selection, "_rebalance_measured_morphologies", side_effect=lambda selected, *_args, **_kwargs: selected),
        ):
            selected = portfolio_benchmark._select(
                candidates,
                target=10,
                visual_directive={"max_pyramidal_like_count": 2},
                selection_trace=trace,
            )

        self.assertEqual(selected, [])
        self.assertIn(
            "capacity_band:brief_target:min_2",
            trace["joint_ten_card_infeasibility_certificate"][
                "unsatisfied_constraints"
            ],
        )

    def test_selector_consumes_next_run_geometry_family_supply_cap(self):
        scopes = ("1/1", "3/8", "1/2", "1/4", "1/8", "1/16")

        class CandidateProbe:
            def __init__(self, **values):
                self.__dict__.update(values)

        candidates = []
        for index, scope in enumerate(scopes):
            for family, score in (("repeated_family", 1.0), (f"alternate_{index}", 0.8)):
                candidates.append(CandidateProbe(
                    key=f"{scope}:{family}", scope=scope,
                    principle_kind="base_operative", operation=f"op_{index}_{family}",
                    score=score, seed=f"seed_{index}_{family}",
                    section=f"section_{index}_{family}", roof=f"roof_{index}_{family}",
                    chassis=f"chassis_{index}_{family}",
                    phenotype=f"phenotype_{index}_{family}",
                    family=family,
                ))
        trace = {}
        measured_pairs = Counter()

        def measured_silhouette(left, right):
            key = tuple(sorted((left.key, right.key)))
            measured_pairs[key] += 1
            return 1.0

        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype, "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(
                portfolio_selection,
                "_silhouette_distance",
                side_effect=measured_silhouette,
            ),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_plan_family", return_value="quadrilateral"),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge", "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(portfolio_selection, "_rebalance_measured_morphologies", side_effect=lambda selected, *_args, **_kwargs: selected),
        ):
            analysis = portfolio_selection.build_compatibility_analysis(candidates)
            analysis.compatibility_matrix(candidates)
            selected = portfolio_selection._select(
                candidates,
                target=6,
                visual_directive={"max_geometry_family_counts": {"repeated_family": 1}},
                selection_trace=trace,
                compatibility_analysis=analysis,
            )
            evaluated_after_selection = sum(measured_pairs.values())
            diagnostics = portfolio_selection._selection_capacity_diagnostics(
                candidates,
                selected,
                target=6,
                visual_directive={"max_geometry_family_counts": {"repeated_family": 1}},
                compatibility_analysis=analysis,
            )

        self.assertEqual(sum(item.family == "repeated_family" for item in selected), 1)
        self.assertEqual(trace["memory_geometry_family_caps"], {"repeated_family": 1})
        self.assertEqual(len(measured_pairs), len(candidates) * (len(candidates) - 1) // 2)
        self.assertTrue(all(count == 1 for count in measured_pairs.values()))
        self.assertEqual(sum(measured_pairs.values()), evaluated_after_selection)
        self.assertEqual(
            diagnostics["compatibility_analysis"]["exact_pair_evaluation_count"],
            trace["compatibility_analysis"]["exact_pair_evaluation_count"],
        )

    def test_selector_reserves_a_slot_for_missing_chassis_only_after_hard_pass_pool(self):
        candidates = [
            SimpleNamespace(
                key=name, scope="1/1", principle_kind="base_operative",
                operation=f"op_{name}", score=score, seed=f"seed_{name}",
                section=f"section_{name}", roof=f"roof_{name}",
                chassis=chassis, phenotype="prismatic", family=f"family_{name}",
            )
            for name, score, chassis in (
                ("common_a", 1.0, "recursive_chassis:courtyard"),
                ("common_b", 0.9, "recursive_chassis:courtyard"),
                ("radial", 0.2, "recursive_chassis:radial_wings"),
            )
        ]
        trace = {}
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype, "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge", "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(portfolio_selection, "_rebalance_measured_morphologies", side_effect=lambda selected, *_args, **_kwargs: selected),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=2,
                visual_directive={
                    "required_chassis_families": ["recursive_chassis:radial_wings"],
                },
                selection_trace=trace,
            )

        self.assertIn("recursive_chassis:radial_wings", {item.chassis for item in selected})
        self.assertEqual(trace["after_chassis_anchor_count"], 2)

    def test_selector_fails_closed_when_chassis_cap_blocks_target(self):
        candidates = [
            SimpleNamespace(
                key=f"candidate_{index}", scope="1/1",
                principle_kind="base_operative", operation=f"op_{index}",
                score=1.0 - index * 0.1, seed=f"seed_{index}",
                section=f"section_{index}", roof=f"roof_{index}",
                chassis="recursive_chassis:courtyard",
                phenotype=f"phenotype_{index}", family=f"family_{index}",
            )
            for index in range(3)
        ]
        trace = {}
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype, "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": f"ground_{item.key}", "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(portfolio_selection, "_rebalance_measured_morphologies", side_effect=lambda selected, *_args, **_kwargs: selected),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=3,
                visual_directive={
                    "max_chassis_family_counts": {"recursive_chassis:courtyard": 1},
                },
                selection_trace=trace,
            )

        self.assertEqual(selected, [])
        self.assertEqual(trace["memory_cap_primary_selection_count"], 1)
        self.assertEqual(trace["memory_cap_fallback_added_count"], 0)
        self.assertIn(
            "typed_cap:chassis:recursive_chassis:courtyard:max_1",
            trace["portfolio_contract_deficits"],
        )

    def test_selector_keeps_measured_capacity_target_miss_for_design_scoring(self):
        candidates = [
            SimpleNamespace(
                key=name,
                scope="1/1",
                principle_kind="base_operative",
                operation=f"op_{name}",
                score=score,
                seed=f"seed_{name}",
                section=f"section_{name}",
                roof=f"roof_{name}",
                chassis=f"chassis_{name}",
                phenotype="prismatic",
                family=f"family_{name}",
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "alternative_id": "maximum_feasible",
                        "target_hard_pass": capacity_pass,
                    },
                }),
            )
            for name, score, capacity_pass in (
                ("high_score_miss", 1.0, False),
                ("measured_pass", 0.6, True),
            )
        ]
        trace = {}
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype, "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge", "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(
                portfolio_selection,
                "_rebalance_measured_morphologies",
                side_effect=lambda selected, *_args, **_kwargs: selected,
            ),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=1,
                selection_trace=trace,
            )

        self.assertEqual([candidate.key for candidate in selected], ["high_score_miss"])
        self.assertEqual(trace["capacity_target_gate_measured_count"], 2)
        self.assertEqual(trace["capacity_target_gate_pass_count"], 1)
        self.assertEqual(trace["capacity_target_gate_advisory_miss_count"], 1)
        self.assertEqual(trace["capacity_target_gate_rejected_count"], 0)

    def test_target_20_contract_rejects_capacity_band_shortage(self):
        alternatives = (
            ["spatial_reserve"] * 5
            + ["balanced_yield"] * 5
            + ["brief_target"] * 6
            + ["maximum_feasible"] * 4
        )
        scopes = (
            ["1/1"] * 4
            + ["1/2"] * 4
            + ["3/8"] * 3
            + ["1/4"] * 3
            + ["1/8"] * 3
            + ["1/16"] * 3
        )
        candidates = [
            SimpleNamespace(
                key=f"candidate_{index}",
                scope=scopes[index],
                principle_kind=("combination" if index == 1 else "base_operative"),
                operation=f"operation_{index % 12}",
                score=1.0 - index * 0.001,
                seed=f"seed_{index}",
                section=f"section_{index}",
                roof=f"roof_{index % 7}",
                chassis=f"chassis_{index % 6}",
                plan=f"plan_{index % 5}",
                phenotype=f"phenotype_{index % 5}",
                section_stepped=index < 2,
                family=f"family_{index}",
                alternative=alternative,
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "requested_capacity_alternative_id": alternative,
                        "alternative_id": alternative,
                        "requested_target_utilization": 0.70,
                        "target_hard_pass": True,
                        "selectable_capacity_alternative_id": alternative,
                        "selectable_capacity_target_utilization": 0.70,
                        "selectable_capacity_hard_pass": True,
                        "feasible_minimum_utilization": 0.60,
                    },
                    "source_capacity_measurement": {
                        "feasible_capacity_utilization": 0.80,
                        "hard_pass": True,
                    },
                }),
            )
            for index, alternative in enumerate(alternatives)
        ]
        trace = {}

        def silhouette(left, right):
            return 1.0

        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda item: item.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda item: item.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda item: item.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_selection, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_selection, "_solid_morphology_metrics", side_effect=lambda item: {
                "phenotype": item.phenotype,
                "body_phenotype": item.phenotype,
                "section_phenotype": (
                    "stepped" if item.section_stepped else "prismatic"
                ),
                "wedge_like": False,
                "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", side_effect=silhouette),
            patch.object(portfolio_selection, "_distance", return_value=1.0),
            patch.object(
                portfolio_selection,
                "_plan_family",
                side_effect=lambda item: item.plan,
            ),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge", "concept_key": item.key,
                "frontage_aligned": False,
            }),
            patch.object(
                portfolio_selection,
                "_rebalance_measured_morphologies",
                side_effect=lambda selected, *_args, **_kwargs: selected,
            ),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=20,
                selection_trace=trace,
            )

        self.assertEqual(selected, [])
        self.assertEqual(trace["capacity_alternative_quotas"], {})
        self.assertEqual(
            trace["capacity_alternative_quota_authority"],
            "diagnostic_only",
        )
        self.assertEqual(
            trace["capacity_alternative_supply_counts"],
            {
                "balanced_yield": 5,
                "brief_target": 6,
                "maximum_feasible": 4,
                "spatial_reserve": 5,
            },
        )
        self.assertEqual(
            set(trace["portfolio_contract_deficits"])
            & {
                "capacity_band:balanced_yield:exact_5",
                "capacity_band:brief_target:exact_5",
                "capacity_band:maximum_feasible:exact_5",
                "capacity_band:spatial_reserve:exact_5",
            },
            {
                "capacity_band:brief_target:exact_5",
                "capacity_band:maximum_feasible:exact_5",
            },
        )
        self.assertIn(
            "capacity_band:maximum_feasible:exact_5",
            trace["portfolio_contract_deficits"],
        )

    def test_target_20_diagnostic_preview_contract_retrieves_maximum_cardinality(self):
        candidates = [
            SimpleNamespace(
                key=f"candidate_{index}",
                scope="1/1",
                principle_kind="base_operative",
                operation=f"operation_{index % 4}",
                score=1.0,
                seed=f"seed_{index % 5}",
                section=f"section_{index % 6}",
                roof=f"roof_{index % 7}",
                chassis=f"chassis_{index % 5}",
                plan=f"plan_{index % 4}",
                family=f"family_{index % 3}",
                alternative="spatial_reserve",
                source=SimpleNamespace(
                    metadata={
                        "capacity_alternative_projection": {
                            "alternative_id": "spatial_reserve",
                            "target_hard_pass": True,
                        },
                    },
                ),
            )
            for index in range(20)
        ]
        trace: dict[str, object] = {}

        with (
            patch.object(
                portfolio_selection,
                "_target_hard_pass_universe",
                return_value=(candidates, candidates),
            ),
            patch.object(
                portfolio_selection,
                "_scope_coverage_anchors",
                return_value=[],
            ),
            patch.object(
                portfolio_selection,
                "_fingerprint",
                side_effect=lambda item: (item.key,),
            ),
            patch.object(
                portfolio_selection,
                "_scope_key",
                side_effect=lambda item: item.scope,
            ),
            patch.object(
                portfolio_selection,
                "_seed_family",
                side_effect=lambda item: item.seed,
            ),
            patch.object(
                portfolio_selection,
                "_section_family",
                side_effect=lambda item: item.section,
            ),
            patch.object(
                portfolio_selection,
                "_roof_archetype",
                side_effect=lambda item: item.roof,
            ),
            patch.object(
                portfolio_selection,
                "_chassis_family",
                side_effect=lambda item: item.chassis,
            ),
            patch.object(
                portfolio_selection,
                "_geometry_program_family",
                side_effect=lambda item: item.family,
            ),
            patch.object(
                portfolio_selection,
                "_plan_family",
                side_effect=lambda item: item.plan,
            ),
            patch.object(
                portfolio_selection,
                "_capacity_alternative_key",
                side_effect=lambda item: item.alternative,
            ),
            patch.object(
                portfolio_selection,
                "_solid_morphology_metrics",
                side_effect=lambda item: {
                    "phenotype": "prismatic",
                    "body_phenotype": "prismatic",
                    "section_phenotype": "prismatic",
                    "wedge_like": False,
                    "pyramidal_like": False,
                },
            ),
            patch.object(
                portfolio_selection,
                "_silhouette_distance",
                return_value=1.0,
            ),
            patch.object(
                portfolio_selection,
                "_distance",
                return_value=1.0,
            ),
            patch.object(
                portfolio_selection,
                "_design_concept_descriptor",
                side_effect=lambda item: {
                    "ground_strategy": "direct_edge",
                    "concept_key": item.key,
                    "frontage_aligned": False,
                },
            ),
            patch.object(
                portfolio_selection,
                "_rebalance_measured_morphologies",
                side_effect=lambda selected, *_args, **_kwargs: selected,
            ),
            patch.object(
                portfolio_selection,
                "solve_milp_compatible_subset",
                side_effect=[[], []],
            ),
            patch.object(
                portfolio_selection,
                "solve_maximum_compatible_subset",
                return_value=list(range(20)),
            ),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=20,
                selection_trace=trace,
                allow_diagnostic_fallback=True,
            )

        self.assertEqual(len(selected), 20)
        self.assertEqual(
            trace["portfolio_contract_infeasibility_certificate"]["fallback_contract"],
            "diagnostic_preview_contract",
        )
        self.assertEqual(
            trace["portfolio_contract_infeasibility_certificate"]["status"],
            "preview_target_reached",
        )
        self.assertEqual(trace["portfolio_contract_preview_recovered_count"], 20)
        self.assertEqual(trace["portfolio_contract_solver_count"], 20)

    def test_target_20_diagnostic_preview_contract_replaces_partial_legacy_solution(self):
        candidates = [
            SimpleNamespace(
                key=f"candidate_{index}",
                scope="1/1",
                principle_kind="base_operative",
                operation=f"operation_{index % 4}",
                score=1.0,
                seed=f"seed_{index % 5}",
                section=f"section_{index % 6}",
                roof=f"roof_{index % 7}",
                chassis=f"chassis_{index % 5}",
                plan=f"plan_{index % 4}",
                family=f"family_{index % 3}",
                alternative="spatial_reserve",
                source=SimpleNamespace(
                    metadata={
                        "capacity_alternative_projection": {
                            "alternative_id": "spatial_reserve",
                            "target_hard_pass": True,
                        },
                    },
                ),
            )
            for index in range(20)
        ]
        trace: dict[str, object] = {}

        with (
            patch.object(
                portfolio_selection,
                "_target_hard_pass_universe",
                return_value=(candidates, candidates),
            ),
            patch.object(
                portfolio_selection,
                "_scope_coverage_anchors",
                return_value=[],
            ),
            patch.object(
                portfolio_selection,
                "_fingerprint",
                side_effect=lambda item: (item.key,),
            ),
            patch.object(
                portfolio_selection,
                "_scope_key",
                side_effect=lambda item: item.scope,
            ),
            patch.object(
                portfolio_selection,
                "_seed_family",
                side_effect=lambda item: item.seed,
            ),
            patch.object(
                portfolio_selection,
                "_section_family",
                side_effect=lambda item: item.section,
            ),
            patch.object(
                portfolio_selection,
                "_roof_archetype",
                side_effect=lambda item: item.roof,
            ),
            patch.object(
                portfolio_selection,
                "_chassis_family",
                side_effect=lambda item: item.chassis,
            ),
            patch.object(
                portfolio_selection,
                "_geometry_program_family",
                side_effect=lambda item: item.family,
            ),
            patch.object(
                portfolio_selection,
                "_plan_family",
                side_effect=lambda item: item.plan,
            ),
            patch.object(
                portfolio_selection,
                "_capacity_alternative_key",
                side_effect=lambda item: item.alternative,
            ),
            patch.object(
                portfolio_selection,
                "_solid_morphology_metrics",
                side_effect=lambda item: {
                    "phenotype": "prismatic",
                    "body_phenotype": "prismatic",
                    "section_phenotype": "prismatic",
                    "wedge_like": False,
                    "pyramidal_like": False,
                },
            ),
            patch.object(
                portfolio_selection,
                "_silhouette_distance",
                return_value=1.0,
            ),
            patch.object(
                portfolio_selection,
                "_distance",
                return_value=1.0,
            ),
            patch.object(
                portfolio_selection,
                "_design_concept_descriptor",
                side_effect=lambda item: {
                    "ground_strategy": "direct_edge",
                    "concept_key": item.key,
                    "frontage_aligned": False,
                },
            ),
            patch.object(
                portfolio_selection,
                "_rebalance_measured_morphologies",
                side_effect=lambda selected, *_args, **_kwargs: selected,
            ),
            patch.object(
                portfolio_selection,
                "solve_milp_compatible_subset",
                return_value=list(range(10)),
            ),
            patch.object(
                portfolio_selection,
                "solve_maximum_compatible_subset",
                return_value=list(range(20)),
            ),
        ):
            selected = portfolio_selection._select(
                candidates,
                target=20,
                selection_trace=trace,
                allow_diagnostic_fallback=True,
            )

        self.assertEqual(len(selected), 20)
        self.assertEqual(
            trace["portfolio_contract_infeasibility_certificate"]["fallback_contract"],
            "diagnostic_preview_contract",
        )
        self.assertEqual(
            trace["portfolio_contract_infeasibility_certificate"]["status"],
            "preview_target_reached",
        )
        self.assertEqual(trace["portfolio_contract_preview_recovered_count"], 20)

    def test_bounded_visual_pool_preserves_rare_capacity_pass_despite_common_higher_score(self):
        candidates = [
            SimpleNamespace(
                key=name,
                score=score,
                scope="1/1",
                phenotype="prismatic",
                family="shared_family",
                plan="quadrilateral",
                principle_id="book:shared",
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "alternative_id": alternative_id,
                        "target_hard_pass": True,
                    },
                }),
            )
            for name, score, alternative_id in (
                ("common_reserve", 1.0, "spatial_reserve"),
                ("rare_maximum", 0.7, "maximum_feasible"),
            )
        ]
        with (
            patch.object(
                portfolio_selection,
                "_fingerprint",
                side_effect=lambda item: (item.key,),
            ),
            patch.object(
                quality_diversity_archive,
                "_fingerprint",
                side_effect=lambda item: (item.key,),
            ),
            patch.object(
                quality_diversity_archive,
                "_scope_key",
                side_effect=lambda item: item.scope,
            ),
            patch.object(
                quality_diversity_archive,
                "_solid_morphology_metrics",
                side_effect=lambda item: {"phenotype": item.phenotype},
            ),
            patch.object(
                quality_diversity_archive,
                "_capacity_alternative_key",
                side_effect=lambda item: item.source.metadata[
                    "capacity_alternative_projection"
                ]["alternative_id"],
            ),
            patch.object(
                quality_diversity_archive,
                "_capacity_target_gate",
                return_value=True,
            ),
            patch.object(
                quality_diversity_archive,
                "_capacity_minimum_gate",
                return_value=True,
            ),
            patch.object(
                quality_diversity_archive,
                "_plan_family",
                side_effect=lambda item: item.plan,
            ),
            patch.object(
                quality_diversity_archive,
                "_geometry_program_family",
                side_effect=lambda item: item.family,
            ),
            patch.dict(
                os.environ,
                {
                    "MAAS_QD_ELITES_PER_CELL": "1",
                    "MAAS_QD_ARCHIVE_MAX_SIZE": "32",
                },
            ),
        ):
            retained = portfolio_selection._bounded_visual_selection_pool(
                candidates,
                per_family_scope=1,
                per_seed_scope=1,
            )

        self.assertEqual(
            {candidate.key for candidate in retained},
            {"common_reserve", "rare_maximum"},
        )

    def test_bounded_visual_pool_keeps_unique_solver_witnesses_below_memory_cap(self):
        """QD cell quotas must not shrink an already bounded exact-solver pool."""
        candidates = [
            SimpleNamespace(
                key=f"witness_{index}",
                score=1.0 - index * 0.01,
                scope="1/1",
                phenotype="prismatic",
                family="shared_family",
                plan="quadrilateral",
                principle_id="book:shared",
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "alternative_id": "balanced_yield",
                        "target_hard_pass": True,
                    },
                }),
            )
            for index in range(3)
        ]
        with (
            patch.object(
                portfolio_selection,
                "_fingerprint",
                side_effect=lambda item: (item.key,),
            ),
            patch.object(
                quality_diversity_archive,
                "_fingerprint",
                side_effect=lambda item: (item.key,),
            ),
            patch.object(
                quality_diversity_archive,
                "_scope_key",
                side_effect=lambda item: item.scope,
            ),
            patch.object(
                quality_diversity_archive,
                "_solid_morphology_metrics",
                side_effect=lambda item: {"phenotype": item.phenotype},
            ),
            patch.object(
                quality_diversity_archive,
                "_capacity_alternative_key",
                return_value="balanced_yield",
            ),
            patch.object(
                quality_diversity_archive,
                "_capacity_target_gate",
                return_value=True,
            ),
            patch.object(
                quality_diversity_archive,
                "_capacity_minimum_gate",
                return_value=True,
            ),
            patch.object(
                quality_diversity_archive,
                "_plan_family",
                side_effect=lambda item: item.plan,
            ),
            patch.object(
                quality_diversity_archive,
                "_geometry_program_family",
                side_effect=lambda item: item.family,
            ),
            patch.dict(
                os.environ,
                {
                    "MAAS_QD_ELITES_PER_CELL": "1",
                    "MAAS_QD_ARCHIVE_MAX_SIZE": "32",
                },
            ),
        ):
            retained = portfolio_selection._bounded_visual_selection_pool(
                candidates,
            )

        self.assertEqual(
            {candidate.key for candidate in retained},
            {candidate.key for candidate in candidates},
        )

    def test_selection_diagnostics_retains_capacity_target_misses_as_advisory(self):
        def candidate(key: str, hard_pass: bool):
            return SimpleNamespace(
                key=key,
                score=1.0,
                operation=key,
                principle_kind="base_operative",
                source=SimpleNamespace(metadata={
                    "capacity_alternative_projection": {
                        "alternative_id": "balanced_yield",
                        "target_hard_pass": hard_pass,
                    },
                }),
            )

        selected = candidate("selected", True)
        valid_remaining = candidate("valid_remaining", True)
        target_miss = candidate("target_miss", False)
        with (
            patch.object(portfolio_selection, "_fingerprint", side_effect=lambda item: (item.key,)),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda item: item.key),
            patch.object(portfolio_selection, "_section_family", return_value="section"),
            patch.object(portfolio_selection, "_roof_archetype", return_value="roof"),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda item: item.key),
            patch.object(portfolio_selection, "_plan_family", side_effect=lambda item: (
                "triangular" if item.key == "valid_remaining" else "quadrilateral"
            )),
            patch.object(portfolio_selection, "_silhouette_distance", return_value=1.0),
            patch.object(portfolio_selection, "_solid_morphology_metrics", return_value={
                "phenotype": "prismatic", "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda item: {
                "ground_strategy": "direct_edge",
                "concept_key": item.key,
                "frontage_aligned": True,
            }),
        ):
            diagnostics = portfolio_selection._selection_capacity_diagnostics(
                [selected, valid_remaining, target_miss],
                [selected],
                target=20,
            )

        self.assertEqual(diagnostics["capacity_target_measured_count"], 3)
        self.assertEqual(diagnostics["capacity_target_pass_count"], 2)
        self.assertEqual(diagnostics["capacity_target_advisory_miss_count"], 1)
        self.assertEqual(diagnostics["capacity_target_rejected_count"], 0)
        self.assertEqual(diagnostics["selection_universe_count"], 3)
        self.assertEqual(diagnostics["remaining_candidate_count"], 2)
        self.assertEqual(
            diagnostics["plan_family_supply_counts"],
            {"quadrilateral": 2, "triangular": 1},
        )

    def test_portfolio_feedback_resolves_replace_votes_to_exact_ast_family(self):
        rows = [{"variant_id": f"maas_{index:02}"} for index in range(1, 5)]
        candidates = [SimpleNamespace(family="profiled", chassis="courtyard") for _ in rows]
        audit = {
            "candidate_actions": [
                {"candidate_id": "maas_01", "decision": "keep"},
                {"candidate_id": "maas_02", "decision": "replace"},
                {"candidate_id": "maas_03", "decision": "replace"},
                {"candidate_id": "maas_04", "decision": "replace"},
            ],
        }
        with (
            patch.object(
                portfolio_feedback,
                "_geometry_program_family",
                side_effect=lambda item: item.family,
            ),
            patch.object(
                portfolio_feedback,
                "_chassis_family",
                side_effect=lambda item: item.chassis,
            ),
        ):
            enriched = portfolio_feedback.enrich_portfolio_vlm_feedback(
                audit, rows=rows, candidates=candidates,
            )

        self.assertEqual(
            enriched["geometry_family_action_counts"]["profiled"],
            {"keep": 1, "replace": 3},
        )
        self.assertEqual(enriched["overrepresented_geometry_families"], ["profiled"])
        self.assertEqual(
            enriched["chassis_family_action_counts"]["courtyard"],
            {"keep": 1, "replace": 3},
        )
        self.assertEqual(enriched["overrepresented_chassis_families"], ["courtyard"])

    def test_portfolio_feedback_marks_two_replaced_chassis_as_repeated(self):
        rows = [{"variant_id": "maas_01"}, {"variant_id": "maas_02"}]
        candidates = [SimpleNamespace(family="curve", chassis="curved_bar") for _ in rows]
        audit = {"candidate_actions": [
            {"candidate_id": "maas_01", "decision": "replace"},
            {"candidate_id": "maas_02", "decision": "replace"},
        ]}
        with (
            patch.object(portfolio_feedback, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_feedback, "_chassis_family", side_effect=lambda item: item.chassis),
        ):
            enriched = portfolio_feedback.enrich_portfolio_vlm_feedback(
                audit, rows=rows, candidates=candidates,
            )

        self.assertEqual(enriched["overrepresented_chassis_families"], ["curved_bar"])

    def test_post_run_descriptor_feedback_matches_live_candidate_feedback(self):
        enriched = portfolio_feedback.enrich_portfolio_vlm_feedback_from_descriptors(
            {"hard_pass": False, "candidate_actions": [
                {"candidate_id": "maas_01", "decision": "replace"},
                {"candidate_id": "maas_02", "decision": "replace"},
            ]},
            candidate_descriptors=[
                {"candidate_id": "maas_01", "geometry_family": "agent_notch", "chassis_family": "carved_monolith"},
                {"candidate_id": "maas_02", "geometry_family": "agent_notch", "chassis_family": "carved_monolith"},
            ],
        )

        self.assertEqual(enriched["overrepresented_geometry_families"], ["agent_notch"])
        self.assertEqual(enriched["overrepresented_chassis_families"], ["carved_monolith"])

    def test_portfolio_feedback_marks_missing_core_chassis_as_review_anchors(self):
        rows = [{"variant_id": "maas_01"}]
        candidates = [SimpleNamespace(family="curve", chassis="recursive_chassis:curved_bar")]
        with (
            patch.object(portfolio_feedback, "_geometry_program_family", side_effect=lambda item: item.family),
            patch.object(portfolio_feedback, "_chassis_family", side_effect=lambda item: item.chassis),
            patch.object(portfolio_feedback, "core_chassis_families", return_value=("curved_bar", "radial_wings")),
        ):
            failed = portfolio_feedback.enrich_portfolio_vlm_feedback(
                {"hard_pass": False, "candidate_actions": []},
                rows=rows,
                candidates=candidates,
            )
            passed = portfolio_feedback.enrich_portfolio_vlm_feedback(
                {"hard_pass": True, "candidate_actions": []},
                rows=rows,
                candidates=candidates,
            )

        self.assertEqual(
            failed["underrepresented_chassis_families"],
            ["recursive_chassis:radial_wings"],
        )
        self.assertEqual(passed["underrepresented_chassis_families"], [])

    def test_chassis_caps_apply_only_to_the_named_family(self):
        caps = portfolio_selection._chassis_caps(
            {"courtyard", "split_wing"},
            target=20,
            directive={"max_chassis_family_counts": {"courtyard": 1}},
        )

        self.assertEqual(caps["courtyard"], 1)
        self.assertEqual(caps["split_wing"], 12)

    def test_rebalance_one_for_two_recovers_valid_portfolio_without_relaxing_caps(self):
        def item(name, scope, score):
            return SimpleNamespace(
                name=name,
                scope=scope,
                principle_kind="base_operative",
                operation=f"op_{name}",
                score=score,
                seed=f"seed_{name}",
                section=f"section_{name}",
                roof=f"roof_{name}",
                chassis=f"chassis_{name}",
            )

        a = item("a", "1/1", 0.90)
        b = item("b", "1/2", 0.80)
        c = item("c", "1/1", 0.88)
        d = item("d", "1/1", 0.86)

        def silhouette(left, right):
            return 0.05 if {left.name, right.name} in ({"a", "c"}, {"a", "d"}) else 1.0

        with (
            patch.object(portfolio_selection, "_scope_key", side_effect=lambda value: value.scope),
            patch.object(portfolio_selection, "_seed_family", side_effect=lambda value: value.seed),
            patch.object(portfolio_selection, "_section_family", side_effect=lambda value: value.section),
            patch.object(portfolio_selection, "_roof_archetype", side_effect=lambda value: value.roof),
            patch.object(portfolio_selection, "_chassis_family", side_effect=lambda value: value.chassis),
            patch.object(portfolio_selection, "_solid_morphology_metrics", return_value={
                "phenotype": "prismatic", "wedge_like": False, "pyramidal_like": False,
            }),
            patch.object(portfolio_selection, "_silhouette_distance", side_effect=silhouette),
            patch.object(portfolio_selection, "_design_concept_descriptor", side_effect=lambda value: {
                "ground_strategy": "direct_edge",
                "concept_key": value.name,
                "frontage_aligned": False,
            }),
        ):
            result = portfolio_benchmark._rebalance_measured_morphologies(
                [a, b],
                [a, b, c, d],
                target=3,
                visual_directive={},
            )

        self.assertEqual({value.name for value in result}, {"b", "c", "d"})

    def test_clean_mass_gate_rejects_two_large_disconnected_mesh_components(self):
        source = SimpleNamespace(
            volumes=(object(),),
            metadata={
                "geometry_program_bridge_evidence": {"program_hash": "recursive"},
                "geometry_program_compilation": {"metrics": {
                    "component_count": 2,
                    "minimum_component_volume_ratio": 0.5,
                }},
            },
            signature=lambda: {
                "surface_count": 20,
                "effective_surface_count": 12,
                "continuous_surface_evidence": {"hard_pass": True},
            },
        )

        hard_pass, evidence = portfolio_benchmark._clean_mass_gate(source)

        self.assertFalse(hard_pass)
        self.assertIn("disconnected_mesh_component_count", evidence["failure_reasons"])
        self.assertEqual(evidence["mesh_component_count"], 2)

    def test_clean_mass_gate_treats_law_derived_floor_bands_as_one_building(self):
        source = SimpleNamespace(
            volumes=tuple(object() for _ in range(6)),
            metadata={
                "geometry_program_bridge_evidence": {"program_hash": "recursive"},
                "geometry_program_compilation": {"metrics": {
                    "component_count": 1,
                    "minimum_component_volume_ratio": 1.0,
                }},
                "floorwise_legal_matrix_stack": {
                    "status": "materialized",
                    "floor_count": 6,
                },
            },
            signature=lambda: {
                "surface_count": 24,
                "effective_surface_count": 12,
                "continuous_surface_evidence": {"hard_pass": False},
            },
        )

        hard_pass, evidence = portfolio_benchmark._clean_mass_gate(source)

        self.assertTrue(hard_pass, evidence)
        self.assertNotIn("visible_volume_count", evidence["failure_reasons"])
        self.assertEqual(evidence["floor_band_count"], 6)
        self.assertEqual(evidence["visible_component_count"], 1)

    def test_registry_reconciles_all_pages_and_principle_groups(self):
        registry = build_book_language_registry()

        self.assertEqual(registry["page_count"], 69)
        self.assertEqual(registry["base_volume_count"], 6)
        self.assertEqual([item["label"] for item in registry["base_volumes"]], [
            "1/1 Base Volume", "3/8 Base Volume", "1/2 Base Volume",
            "1/4 Base Volume", "1/8 Base Volume", "1/16 Base Volume",
        ])
        self.assertEqual(len(registry["pages"]), 69)
        self.assertEqual(registry["base_operative_count"], 30)
        self.assertEqual(registry["combination_count"], 20)
        self.assertEqual(registry["aggregation_recipe_count"], 9)
        self.assertEqual(registry["case_study_count"], 10)
        self.assertEqual(registry["executable_principle_count"], 69)
        self.assertEqual(registry["operative_page_variation_count"], 11)
        self.assertEqual(registry["operative_orientation_count"], 3)
        self.assertEqual([page["page"] for page in registry["pages"]], list(range(1, 70)))
        self.assertTrue(all(page["sha256"] for page in registry["pages"]))
        self.assertEqual(len(registry["taxonomy"]["operations"]["add"]["single"]), 3)
        self.assertEqual(len(registry["taxonomy"]["operations"]["add"]["multiple"]), 4)
        self.assertEqual(len(registry["taxonomy"]["operations"]["displace"]["single"]), 4)
        self.assertEqual(len(registry["taxonomy"]["operations"]["displace"]["multiple"]), 7)
        self.assertEqual(len(registry["taxonomy"]["operations"]["subtract"]["single"]), 8)
        self.assertEqual(len(registry["taxonomy"]["operations"]["subtract"]["multiple"]), 4)
        self.assertEqual(len(registry["pages"][2]["principle_ids"]), 6)

    def test_disk_corpus_matches_typed_registry_and_ocr_provenance(self):
        audit = audit_book_corpus()

        self.assertTrue(audit["hard_pass"], audit["issues"])
        self.assertEqual(audit["scan_page_count"], 69)
        self.assertEqual(audit["ocr_page_count"], 69)
        self.assertEqual(audit["registry_page_count"], 69)
        self.assertEqual(audit["principle_count"], 69)
        self.assertEqual(
            audit["unreferenced_source_pages"],
            [1, 2, 4, 5, 13, 25, 38, 49, 59],
        )

    def test_taxonomy_continuation_pages_are_not_mislabeled_as_operatives(self):
        pages = {item["page"]: item for item in build_book_language_registry()["pages"]}

        self.assertEqual(pages[13]["section"], "operative_index")
        self.assertEqual(pages[25]["section"], "operative_index")
        self.assertEqual(pages[12]["section"], "base_operative")
        self.assertEqual(pages[14]["section"], "base_operative")
        self.assertEqual(pages[26]["section"], "base_operative")

    def test_every_base_operative_preserves_book_procedure_and_variation_semantics(self):
        base = [item for item in build_book_language_registry()["principles"] if item["kind"] == "base_operative"]

        self.assertEqual(len(base), 30)
        self.assertTrue(all(len(item["semantics"]["procedure"]) == 3 for item in base))
        self.assertTrue(all(item["semantics"]["variation_parameters"] for item in base))
        self.assertTrue(all(item["semantics"]["base_volume_fractions"] == ["1/1", "3/8", "1/2", "1/4", "1/8", "1/16"] for item in base))
        self.assertTrue(all(item["source_diagram_contract"]["procedure_step_count"] == 3 for item in base))
        self.assertTrue(all(item["source_diagram_contract"]["variation_count"] == 11 for item in base))
        self.assertTrue(all(item["source_diagram_contract"]["orientations"] == ["long_axis", "short_axis", "vertical"] for item in base))
        self.assertEqual(next(item for item in base if item["label"] == "bend")["semantics"]["output_topology"], "single_bent_volume")
        self.assertEqual(next(item for item in base if item["label"] == "merge")["semantics"]["output_topology"], "single_fused_volume")

    def test_case_studies_preserve_the_books_combined_operations(self):
        cases = {item["page_refs"][0]: item for item in build_book_language_registry()["case_studies"]}

        self.assertEqual(cases[60]["verbs"], ["carve", "offset"])
        self.assertEqual(cases[61]["verbs"], ["embed", "branch"])
        self.assertEqual(cases[63]["verbs"], ["expand", "nest"])
        self.assertEqual(cases[69]["verbs"], ["overlap", "rotate"])
        self.assertEqual(cases[60]["implementation_elements"], [
            "Offset Program", "Perimeter Services", "Punctured Openings",
        ])
        self.assertEqual(cases[69]["implementation_elements"], [
            "Rotated Volumes", "Stacked Utility and Circulation Cores", "Plinth and Street Facade",
        ])
        self.assertTrue(all(item["generation_stage"] == "case_study" for item in cases.values()))

    def test_book_aggregation_display_and_execution_orders_are_both_preserved(self):
        aggregations = [item for item in build_book_language_registry()["principles"] if item["kind"] == "aggregation"]
        reflect_expand = next(item for item in aggregations if item["label"].startswith("reflect"))

        self.assertEqual(reflect_expand["verbs"], ["reflect", "expand"])
        self.assertEqual(reflect_expand["execution_verbs"], ["expand", "reflect"])

    def test_page_count_and_executable_taxonomy_are_independently_accounted(self):
        registry = build_book_language_registry()
        principles = registry["principles"]

        self.assertEqual(len([item for item in principles if item["kind"] == "base_operative"]), 30)
        self.assertEqual(len([item for item in principles if item["kind"] == "combination"]), 20)
        self.assertEqual(len([item for item in principles if item["kind"] == "aggregation"]), 9)
        self.assertEqual(len([item for item in principles if item["kind"] == "case_study"]), 10)
        self.assertEqual(len(registry["case_studies"]), 10)
        self.assertEqual(registry["executable_principle_count"], len(principles))

    def test_compile_evidence_is_required_for_active_status(self):
        principle_id = "book:operative:expand"
        typed = build_book_language_registry()["principles"]
        active = build_book_language_registry({
            principle_id: {"compile_passed": True, "hard_pass": True, "geometry_delta": 0.12},
        })["principles"]

        self.assertEqual(next(item for item in typed if item["principle_id"] == principle_id)["status"], "typed")
        self.assertEqual(next(item for item in active if item["principle_id"] == principle_id)["status"], "active")

    def test_base_operative_vocabulary_is_exact(self):
        self.assertEqual(len(book_base_verbs()), 30)
        self.assertIn("inflate", book_base_verbs())
        self.assertIn("rotate", book_base_verbs())
        self.assertIn("puncture", book_base_verbs())
        self.assertEqual(BOOK_BASE_VERBS, set(book_base_verbs()))
        self.assertTrue(BOOK_BASE_VERBS.issubset(SUPPORTED_VERBS))

    def test_every_base_operative_has_multi_site_compile_evidence(self):
        registry = audited_book_language_registry()
        base = [item for item in registry["principles"] if item["kind"] == "base_operative"]

        self.assertEqual(len(base), 30)
        self.assertTrue(all(item["compile_evidence"]["compile_pass_count"] == 4 for item in base))
        self.assertTrue(all(item["status"] == "active" for item in base))
        self.assertTrue(all(item["compile_evidence"]["clean_pass_count"] == 4 for item in base))

    def test_all_book_operations_combinations_aggregations_and_cases_have_clean_execution_evidence(self):
        registry = audited_book_language_registry()

        self.assertEqual(len(registry["principles"]), 69)
        self.assertTrue(all(item["status"] == "active" for item in registry["principles"]))
        self.assertTrue(all(item["compile_evidence"]["clean_pass_count"] == 4 for item in registry["principles"]))
