import json
import os
import urllib.error
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from shapely.geometry import box

from design.maas.book_language.candidate_generation import (
    _materialize_directed_geometry,
    _propagate_terminal_materialization_failure,
)
from design.maas.book_language.downstream_hard_gate import (
    _final_source_geometry_identity,
)
from design.maas.book_language.portfolio_benchmark import (
    _deficit_directed_replenishment_inputs,
)
from design.maas.book_language.legal_floor_field import (
    materialize_legal_floor_field,
)
from design.maas.geometry_language.llm_adapter import (
    GeometryAuthorError,
    author_geometry_programs_with_openai,
)
from design.maas.geometry_language import (
    base_seed_programs,
    compile_geometry_program_to_source_mass,
)
from design.maas.geometry_language.outcome_graph import GeometryOutcomeGraph
from design.maas.geometry_language.source_bridge import (
    _internal_horizontal_tread_area_ratio,
    materialize_floorwise_legal_source,
)
from design.maas.paid_provider_budget import (
    configure_paid_provider_budget,
    reset_paid_provider_budget_for_tests,
)
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume
from design.maas.program_massing import program_seed_sequences
from design.maas.program_massing.semantic_carriers import (
    audit_source_semantic_projection,
)


_LEGAL_SITE = box(0.0, 0.0, 20.0, 20.0)
_LEGAL_FIELD = materialize_legal_floor_field(
    SimpleNamespace(
        envelope=SimpleNamespace(
            floor_height=3.0,
            height_limit=30.0,
            bcr_limit=100.0,
            far_limit=1000.0,
        ),
        generation_site=_LEGAL_SITE,
        sunlight_ring=(),
        evidence={},
    ),
    site_local_utm=_LEGAL_SITE,
    pnu="1168011800104170004",
)
LEGAL_FLOOR_FIELD_HASH = _LEGAL_FIELD["legal_floor_field_hash"]


class _Program:
    def program_hash(self):
        return "task7c-program-hash"

    def to_dict(self):
        return {
            "name": "task7c-program",
            "metadata": {"family": "recursive_solid"},
        }


def _authored_box_source():
    footprint = box(-5.0, -3.0, 5.0, 3.0)
    corners = (
        (-5.0, -3.0, 0.0), (5.0, -3.0, 0.0),
        (5.0, 3.0, 0.0), (-5.0, 3.0, 0.0),
        (-5.0, -3.0, 1.0), (5.0, -3.0, 1.0),
        (5.0, 3.0, 1.0), (-5.0, 3.0, 1.0),
    )
    triangles = (
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
    )
    surfaces = tuple(
        SourceSurface(
            role=f"surface_{index}",
            volume_role="mass",
            verb="extrude",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=tuple(corners[item] for item in triangle),
        )
        for index, triangle in enumerate(triangles)
    )
    return SourceMass(
        name="task7c-authored",
        footprint=footprint,
        volumes=(SourceVolume("mass", footprint, 0.0, 1.0, "extrude"),),
        surfaces=surfaces,
        metadata={},
    )


def _projection(*, hard_pass, surfaces, reasons=(), mode="matrix4_projection"):
    return SimpleNamespace(
        surfaces=tuple(surfaces),
        certificate=SimpleNamespace(
            hard_pass=hard_pass,
            status="certified" if hard_pass else "failed",
            certification_mode=mode,
            failure_reasons=tuple(reasons),
            section_numeric_epsilon_m=None,
            to_dict=lambda: {
                "status": "certified" if hard_pass else "failed",
                "hard_pass": hard_pass,
                "certification_mode": mode,
                "failure_reasons": list(reasons),
            },
        ),
    )


class Task7CAuthoredVisualAuthorityTest(TestCase):
    def tearDown(self):
        reset_paid_provider_budget_for_tests()
        super().tearDown()

    def _graph(self):
        return GeometryOutcomeGraph(Path("unused-task7c.json"), "task7c-pnu")

    def _propagate(self, terminal_record, graph, report_records, source_seed):
        _propagate_terminal_materialization_failure(
            terminal_record=terminal_record,
            report_records=report_records,
            outcome_graph=graph,
            program_slug="task7c",
            source_seed=source_seed,
            program=_Program(),
            principle_id="stack",
            book_scope="whole_building",
        )

    def test_profiled_csg_clip_precedes_floorwise_loft_for_authored_mesh(self):
        source = _authored_box_source()
        primary = _projection(
            hard_pass=False,
            surfaces=(),
            reasons=("projected_visual_mesh_outside_legal_section",),
        )
        clipped = _projection(
            hard_pass=True,
            surfaces=source.surfaces,
            mode="floorwise_profiled_legal_clip",
        )
        lofted = _projection(
            hard_pass=True,
            surfaces=source.surfaces,
            mode="floorwise_csg_section_loft",
        )
        with (
            patch(
                "design.maas.geometry_language.floorwise_visual_projection."
                "project_floorwise_visual_mesh",
                return_value=primary,
            ),
            patch(
                "design.maas.geometry_language.floorwise_profiled_legal_clip."
                "clip_profiled_mesh_to_floorwise_legal_solids",
                return_value=clipped,
            ) as clip_mock,
            patch(
                "design.maas.geometry_language.floorwise_section_loft."
                "loft_floorwise_legal_sections",
                return_value=lofted,
            ) as loft_mock,
        ):
            result = materialize_floorwise_legal_source(
                source,
                legal_sections=(box(-10.0, -10.0, 10.0, 10.0),),
                target_plan_coverage=0.15,
                legal_floor_field_hash=LEGAL_FLOOR_FIELD_HASH,
            )

        self.assertIsNotNone(result)
        clip_mock.assert_called_once()
        loft_mock.assert_not_called()
        certificate = result.metadata["floorwise_visual_projection"]
        self.assertEqual(
            certificate["certification_mode"],
            "floorwise_profiled_legal_clip",
        )
        self.assertEqual(
            certificate["visible_surface_producer"],
            "authored_continuous_envelope_clip",
        )
        self.assertEqual(
            certificate["visible_internal_tread_area_ratio"],
            0.0,
        )

    def test_dominant_clip_terrace_is_replaced_by_certified_loft(self):
        source = _authored_box_source()
        # The authored box skin is 152 m2.  Two 10x6 treads at mid-height are
        # 60 m2, i.e. ~28% of the visible skin, so the clip has collapsed into
        # a step and the exact-section loft is the better visible authority.
        terraces = tuple(
            SourceSurface(
                role=f"generated_floor_terrace_{index}",
                volume_role="mass",
                verb="floorwise_legal_clip",
                surface_type="profiled_recursive_solid_mesh",
                vertices_m=vertices,
            )
            for index, vertices in enumerate((
                (
                    (-5.0, -3.0, 0.5),
                    (5.0, -3.0, 0.5),
                    (5.0, 3.0, 0.5),
                ),
                (
                    (-5.0, -3.0, 0.5),
                    (5.0, 3.0, 0.5),
                    (-5.0, 3.0, 0.5),
                ),
            ))
        )
        primary = _projection(
            hard_pass=False,
            surfaces=(),
            reasons=("projected_visual_mesh_outside_legal_section",),
        )
        clipped = _projection(
            hard_pass=True,
            surfaces=(*source.surfaces, *terraces),
            mode="floorwise_profiled_legal_clip",
        )
        lofted = _projection(
            hard_pass=True,
            surfaces=source.surfaces,
            mode="floorwise_csg_section_loft",
        )
        with (
            patch(
                "design.maas.geometry_language.floorwise_visual_projection."
                "project_floorwise_visual_mesh",
                return_value=primary,
            ),
            patch(
                "design.maas.geometry_language.floorwise_profiled_legal_clip."
                "clip_profiled_mesh_to_floorwise_legal_solids",
                return_value=clipped,
            ),
            patch(
                "design.maas.geometry_language.floorwise_section_loft."
                "loft_floorwise_legal_sections",
                return_value=lofted,
            ) as loft_mock,
        ):
            result = materialize_floorwise_legal_source(
                source,
                legal_sections=(box(-10.0, -10.0, 10.0, 10.0),),
                target_plan_coverage=0.15,
                legal_floor_field_hash=LEGAL_FLOOR_FIELD_HASH,
            )

        self.assertIsNotNone(result)
        loft_mock.assert_called_once()
        self.assertEqual(
            result.metadata["floorwise_visual_projection"]
            ["certification_mode"],
            "floorwise_csg_section_loft",
        )
        self.assertEqual(
            result.metadata["floorwise_visual_projection"]
            ["visible_surface_producer"],
            "legal_section_loft",
        )

    def test_minor_clip_terrace_keeps_authored_skin_instead_of_loft(self):
        source = _authored_box_source()
        # One 4 m2 tread against a 152 m2 authored skin is ~2.6%.  Rebuilding
        # the body from legal sections would trade that tread for a fully
        # terraced legal mass, so the authored clip must stay the authority.
        terrace = SourceSurface(
            role="generated_floor_terrace",
            volume_role="mass",
            verb="floorwise_legal_clip",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=(
                (-2.0, -1.0, 0.5),
                (2.0, -1.0, 0.5),
                (2.0, 1.0, 0.5),
            ),
        )
        primary = _projection(
            hard_pass=False,
            surfaces=(),
            reasons=("projected_visual_mesh_outside_legal_section",),
        )
        clipped = _projection(
            hard_pass=True,
            surfaces=(*source.surfaces, terrace),
            mode="floorwise_profiled_legal_clip",
        )
        lofted = _projection(
            hard_pass=True,
            surfaces=source.surfaces,
            mode="floorwise_csg_section_loft",
        )
        with (
            patch(
                "design.maas.geometry_language.floorwise_visual_projection."
                "project_floorwise_visual_mesh",
                return_value=primary,
            ),
            patch(
                "design.maas.geometry_language.floorwise_profiled_legal_clip."
                "clip_profiled_mesh_to_floorwise_legal_solids",
                return_value=clipped,
            ),
            patch(
                "design.maas.geometry_language.floorwise_section_loft."
                "loft_floorwise_legal_sections",
                return_value=lofted,
            ) as loft_mock,
        ):
            result = materialize_floorwise_legal_source(
                source,
                legal_sections=(box(-10.0, -10.0, 10.0, 10.0),),
                target_plan_coverage=0.15,
                legal_floor_field_hash=LEGAL_FLOOR_FIELD_HASH,
            )

        loft_mock.assert_not_called()

    def test_internal_tread_area_ratio_measures_share_not_presence(self):
        source = _authored_box_source()
        minor = SourceSurface(
            role="minor_tread",
            volume_role="mass",
            verb="floorwise_legal_clip",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=(
                (-2.0, -1.0, 0.5),
                (2.0, -1.0, 0.5),
                (2.0, 1.0, 0.5),
            ),
        )
        dominant = tuple(
            SourceSurface(
                role=f"dominant_tread_{index}",
                volume_role="mass",
                verb="floorwise_legal_clip",
                surface_type="profiled_recursive_solid_mesh",
                vertices_m=vertices,
            )
            for index, vertices in enumerate((
                (
                    (-5.0, -3.0, 0.5),
                    (5.0, -3.0, 0.5),
                    (5.0, 3.0, 0.5),
                ),
                (
                    (-5.0, -3.0, 0.5),
                    (5.0, 3.0, 0.5),
                    (-5.0, 3.0, 0.5),
                ),
            ))
        )

        self.assertEqual(
            _internal_horizontal_tread_area_ratio(source.surfaces),
            0.0,
        )
        self.assertAlmostEqual(
            _internal_horizontal_tread_area_ratio(
                (*source.surfaces, minor)
            ),
            4.0 / 156.0,
            places=6,
        )
        self.assertAlmostEqual(
            _internal_horizontal_tread_area_ratio(
                (*source.surfaces, *dominant)
            ),
            60.0 / 212.0,
            places=6,
        )

    def test_source_profiled_no_valid_surface_flows_to_replenishment_with_safe_evidence(self):
        source = _authored_box_source()
        primary = _projection(
            hard_pass=False,
            surfaces=(),
            reasons=("projected_visual_mesh_outside_legal_section",),
        )
        clipped = _projection(
            hard_pass=False,
            surfaces=(),
            reasons=(
                "profiled_clip_no_valid_surface",
                "csg_midplane_certificate_failed",
            ),
            mode="floorwise_profiled_legal_clip",
        )
        terminal_records = []
        with patch(
            "design.maas.geometry_language.floorwise_visual_projection.project_floorwise_visual_mesh",
            return_value=primary,
        ), patch(
            "design.maas.geometry_language.floorwise_profiled_legal_clip.clip_profiled_mesh_to_floorwise_legal_solids",
            return_value=clipped,
        ):
            result = materialize_floorwise_legal_source(
                source,
                legal_sections=(box(-10.0, -10.0, 10.0, 10.0),),
                target_plan_coverage=0.5,
                legal_floor_field_hash=LEGAL_FLOOR_FIELD_HASH,
                terminal_failure_sink=terminal_records,
            )

        self.assertIsNone(result)
        self.assertEqual(terminal_records[0]["stage"], "authored_visual_authority")
        self.assertEqual(
            terminal_records[0]["evidence"]["failure_reasons"],
            [
                "profiled_clip_no_valid_surface",
                "csg_midplane_certificate_failed",
            ],
        )
        self.assertEqual(
            terminal_records[0]["evidence"]["legal_floor_field_hash"],
            LEGAL_FLOOR_FIELD_HASH,
        )

        terminal_records[0]["evidence"].update({
            "node_id": "stale-node",
            "vertices": [[1.0, 2.0, 3.0]] * 1000,
            "mesh_payload": {"triangles": [[0, 1, 2]] * 1000},
        })
        graph = self._graph()
        report_records = []
        self._propagate(terminal_records[0], graph, report_records, "profiled-seed")
        feedback = graph.authored_visual_authority_replenishment_feedback(
            program_slug="task7c"
        )

        self.assertEqual(
            feedback[0]["structural_subreason"],
            "authored_visual_authority_empty_or_no_valid_surface",
        )
        self.assertEqual(
            feedback[0]["certificate_causes"],
            [
                "profiled_clip_no_valid_surface",
                "csg_midplane_certificate_failed",
            ],
        )
        self.assertEqual(feedback[0]["legal_floor_field_hash"], LEGAL_FLOOR_FIELD_HASH)
        self.assertTrue(feedback[0]["hard_fail_closed"])
        self.assertFalse(feedback[0]["legal_floor_loft_or_prism_replay_allowed"])
        serialized = json.dumps(report_records + feedback, sort_keys=True)
        for forbidden in ("stale-node", "vertices", "triangles", "mesh_payload"):
            self.assertNotIn(forbidden, serialized)

    def test_source_revalidation_emits_authored_stage_and_old_records_remain_readable(self):
        source = _authored_box_source()
        projected = _projection(hard_pass=True, surfaces=source.surfaces)
        terminal_records = []
        with patch(
            "design.maas.geometry_language.floorwise_visual_projection.project_floorwise_visual_mesh",
            return_value=projected,
        ):
            result = materialize_floorwise_legal_source(
                source,
                legal_sections=(box(-10.0, -10.0, 10.0, 10.0),),
                target_plan_coverage=0.5,
                legal_floor_field_hash=LEGAL_FLOOR_FIELD_HASH,
                terminal_failure_sink=terminal_records,
            )

        self.assertIsNone(result)
        self.assertEqual(terminal_records[0]["stage"], "authored_visual_authority")
        graph = self._graph()
        report_records = []
        self._propagate(terminal_records[0], graph, report_records, "revalidation-seed")
        feedback = graph.authored_visual_authority_replenishment_feedback(
            program_slug="task7c"
        )
        self.assertEqual(
            feedback[0]["structural_subreason"],
            "authored_visual_authority_revalidation",
        )
        self.assertEqual(feedback[0]["legal_floor_field_hash"], LEGAL_FLOOR_FIELD_HASH)

        legacy_graph = self._graph()
        legacy_graph.observations.append({
            "stage": "geometry_gate",
            "geometry_gate_stage": "visual_projection_or_replay",
            "program_slug": "task7c",
            "program_hash": "legacy-program-hash",
            "geometry_family": "recursive_solid",
            "book_scope": "whole_building",
            "terminal_materialization_evidence": {
                "failure_reason": "revalidation_floor_section_mismatch",
                "legal_floor_field_hash": "legacy-legal-hash",
            },
        })
        legacy_feedback = legacy_graph.authored_visual_authority_replenishment_feedback(
            program_slug="task7c"
        )
        self.assertEqual(
            legacy_feedback[0]["structural_subreason"],
            "authored_visual_authority_revalidation",
        )
        self.assertEqual(legacy_feedback[0]["book_scope"], "whole_building")

    def test_successful_candidate_keeps_authored_surfaces_as_final_visual_authority(self):
        authored_program = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        sequence = replace(
            seed,
            notes=tuple(seed.notes) + (
                "geometry_program_payload="
                + json.dumps(authored_program.to_dict(), sort_keys=True),
                "geometry_program_source_seed=task7c-authored-seed",
            ),
        )
        source = replace(
            _authored_box_source(),
            metadata={
                "candidate_floor_context": {
                    "height_m": 10.0,
                    "floors": 1,
                },
            },
        )
        terminal_records = []
        with patch(
            "design.maas.book_language.candidate_generation.select_legal_field_affine_projection",
            return_value=None,
        ):
            materialized = _materialize_directed_geometry(
                source,
                sequence,
                containment_host=box(-10.0, -10.0, 10.0, 10.0),
                floor_containment_hosts=(box(-10.0, -10.0, 10.0, 10.0),),
                minimum_host_plan_coverage=0.5,
                floor_capacity_plan_hash="task7c-floor-capacity-plan",
                target_floor_areas_m2=(180.0,),
                building_type="",
                legal_floor_field_hash=LEGAL_FLOOR_FIELD_HASH,
                terminal_failure_sink=terminal_records,
            )

        self.assertIsNotNone(materialized, terminal_records)
        self.assertTrue(materialized.surfaces)
        self.assertTrue(materialized.volumes)
        self.assertTrue(all(
            volume.verb == "floorwise_legal_matrix4"
            for volume in materialized.volumes
        ))
        metadata = materialized.metadata
        bridge = metadata["geometry_program_bridge_evidence"]
        self.assertEqual(
            metadata["geometry_authority"],
            "authored_projected_surface_payload",
        )
        self.assertEqual(
            bridge["geometry_authority"],
            "authored_projected_surface_payload",
        )
        self.assertEqual(
            metadata["geometry_program"],
            metadata["authored_geometry_program"],
        )
        operators = {
            str(node.get("operator") or "")
            for node in metadata["geometry_program"].get("nodes") or ()
        }
        self.assertNotIn("extruded_polygon", operators)
        self.assertNotEqual(
            metadata["geometry_program"].get("metadata", {}).get("family"),
            "materialized_floorwise_legal_projection",
        )
        self.assertEqual(
            metadata["final_surface_payload_hash"],
            bridge["surface_payload_hash"],
        )
        self.assertEqual(
            metadata["capacity_projection_measurement"]["legal_floor_field_hash"],
            LEGAL_FLOOR_FIELD_HASH,
        )
        projection_certificate = metadata["authored_legal_projection_certificate"]
        self.assertEqual(
            projection_certificate["schema_version"],
            "arr.maas.authored_legal_projection_certificate.v1",
        )
        self.assertEqual(
            projection_certificate["input_authored_program_hash"],
            bridge["post_book_authored_program_hash"],
        )
        self.assertEqual(
            projection_certificate["input_authored_geometry_hash"],
            bridge["post_book_authored_geometry_hash"],
        )
        self.assertEqual(
            projection_certificate["legal_floor_field_hash"],
            LEGAL_FLOOR_FIELD_HASH,
        )
        self.assertEqual(
            projection_certificate["projected_surface_hash"],
            metadata["final_geometry_hash"],
        )
        self.assertNotEqual(
            projection_certificate["input_authored_geometry_hash"],
            projection_certificate["projected_surface_hash"],
        )
        self.assertEqual(
            metadata["authored_geometry_provenance"]["authority"],
            "post_book_authored_ast",
        )
        self.assertNotIn("upstream_authored_program_hash", bridge)
        self.assertNotIn("upstream_authored_geometry_hash", bridge)
        _, downstream_failures, _, _, _ = _final_source_geometry_identity(
            materialized
        )
        self.assertNotIn(
            "authored_legal_projection_chain_mismatch",
            downstream_failures,
        )
        self.assertFalse(
            bridge["legal_floor_loft_or_prism_replay_allowed"]
        )
        self.assertFalse(bridge["llm_geometry_author_active"])
        self.assertNotEqual(
            bridge["author_provider"],
            "openai_llm_geometry_author",
        )
        self.assertNotIn(
            "initial_llm_authored_pre_book_program_hash",
            bridge,
        )
        self.assertNotIn(
            "initial_llm_authored_pre_book_geometry_hash",
            bridge,
        )

    def test_procedural_candidate_bridge_omits_all_llm_provenance(self):
        authored_program = base_seed_programs()[0]
        authored_program = replace(authored_program, metadata={
            **authored_program.metadata,
            "author_provider": "bounded_procedural_geometry_agent",
            "language_layer": "agent_synthesized_recursive_geometry",
        })
        seed = program_seed_sequences("gymnasium")[0]
        sequence = replace(
            seed,
            notes=tuple(seed.notes) + (
                "geometry_program_payload="
                + json.dumps(authored_program.to_dict(), sort_keys=True),
                "geometry_program_source=bounded_procedural_geometry_agent",
                "geometry_program_source_seed=task7d-procedural-seed",
            ),
        )
        source = replace(
            _authored_box_source(),
            metadata={
                "candidate_floor_context": {
                    "height_m": 10.0,
                    "floors": 1,
                },
            },
        )
        terminal_records = []

        def compile_with_stale_llm_bridge(*args, **kwargs):
            compiled = compile_geometry_program_to_source_mass(*args, **kwargs)
            self.assertIsNotNone(compiled)
            stale_metadata = dict(compiled.metadata)
            stale_metadata["geometry_program_bridge_evidence"] = {
                **stale_metadata["geometry_program_bridge_evidence"],
                "author_provider": "openai_llm_geometry_author",
                "author_source": "openai_llm_geometry_author",
                "author_model": "stale-gpt-model",
                "author_response_id": "stale-author-response",
                "llm_geometry_author_model": "stale-llm-model",
                "llm_geometry_author_response_id": "stale-llm-response",
                "initial_llm_authored_pre_book_program_hash": "stale-program",
                "initial_llm_authored_pre_book_geometry_hash": "stale-geometry",
            }
            return replace(compiled, metadata=stale_metadata)

        with patch(
            "design.maas.book_language.candidate_generation.select_legal_field_affine_projection",
            return_value=None,
        ), patch(
            "design.maas.book_language.candidate_generation.compile_geometry_program_to_source_mass",
            side_effect=compile_with_stale_llm_bridge,
        ):
            materialized = _materialize_directed_geometry(
                source,
                sequence,
                containment_host=box(-10.0, -10.0, 10.0, 10.0),
                floor_containment_hosts=(box(-10.0, -10.0, 10.0, 10.0),),
                minimum_host_plan_coverage=0.5,
                floor_capacity_plan_hash="task7d-procedural-floor-plan",
                target_floor_areas_m2=(180.0,),
                building_type="",
                legal_floor_field_hash=LEGAL_FLOOR_FIELD_HASH,
                terminal_failure_sink=terminal_records,
            )

        self.assertIsNotNone(materialized, terminal_records)
        metadata = materialized.metadata
        bridge = metadata["geometry_program_bridge_evidence"]
        self.assertFalse(bridge["llm_geometry_author_active"])
        self.assertEqual(
            bridge["author_provider"],
            "bounded_procedural_geometry_agent",
        )
        self.assertEqual(
            bridge["author_source"],
            "bounded_procedural_geometry_agent",
        )
        self.assertEqual(bridge["source_seed"], "task7d-procedural-seed")
        self.assertFalse(any(
            key.startswith("initial_llm_")
            for key in bridge
        ))
        for key in (
            "author_response_id",
            "author_model",
            "llm_geometry_author_response_id",
            "llm_geometry_author_model",
        ):
            self.assertNotIn(key, bridge)
        self.assertEqual(
            metadata["final_program_hash"],
            authored_program.program_hash(),
        )
        self.assertEqual(
            metadata["geometry_program"],
            authored_program.to_dict(),
        )
        self.assertEqual(
            metadata["authored_geometry_provenance"]["authority"],
            "post_book_authored_ast",
        )
        self.assertFalse(
            bridge["legal_floor_loft_or_prism_replay_allowed"]
        )

    def test_semantic_hard_gate_accepts_authored_surface_authority_but_still_fails_closed(self):
        source = replace(
            _authored_box_source(),
            metadata={
                "geometry_authority": "authored_projected_surface_payload",
                "geometry_program_bridge_evidence": {
                    "program_hash": "task7c-program-hash",
                    "geometry_hash": "task7c-visual-hash",
                    "surface_payload_hash": "missing-binding",
                },
            },
        )
        audit = audit_source_semantic_projection(
            source,
            building_type="gymnasium",
            expected_context={},
        )

        self.assertFalse(audit["hard_pass"])
        self.assertNotIn(
            "authored_surface_geometry_authority_required",
            audit["failures"],
        )

    def test_non_bridge_candidate_failure_propagates_production_legal_hash(self):
        authored_program = base_seed_programs()[0]
        seed = program_seed_sequences("gymnasium")[0]
        sequence = replace(
            seed,
            notes=tuple(seed.notes) + (
                "geometry_program_payload="
                + json.dumps(authored_program.to_dict(), sort_keys=True),
            ),
        )
        source = replace(
            _authored_box_source(),
            metadata={
                "candidate_floor_context": {"height_m": 10.0, "floors": 1},
            },
        )
        terminal_records = []
        with patch(
            "design.maas.book_language.candidate_generation.select_legal_field_affine_projection",
            return_value=None,
        ):
            materialized = _materialize_directed_geometry(
                source,
                sequence,
                containment_host=box(-10.0, -10.0, 10.0, 10.0),
                floor_containment_hosts=(box(-10.0, -10.0, 10.0, 10.0),),
                minimum_host_plan_coverage=0.5,
                floor_capacity_plan_hash="task7c-floor-capacity-plan",
                target_floor_areas_m2=(180.0,),
                building_type="gymnasium",
                legal_floor_field_hash=LEGAL_FLOOR_FIELD_HASH,
                terminal_failure_sink=terminal_records,
            )

        self.assertIsNone(materialized)
        self.assertEqual(terminal_records[0]["stage"], "semantic_carrier")
        self.assertEqual(
            terminal_records[0]["evidence"]["legal_floor_field_hash"],
            LEGAL_FLOOR_FIELD_HASH,
        )
        graph = self._graph()
        report_records = []
        self._propagate(
            terminal_records[0],
            graph,
            report_records,
            "non-bridge-semantic-seed",
        )
        self.assertEqual(
            graph.observations[-1]["legal_floor_field_hash"],
            LEGAL_FLOOR_FIELD_HASH,
        )

    def test_source_bridge_early_failure_carries_legal_floor_field_hash(self):
        source = replace(_authored_box_source(), volumes=())
        terminal_records = []
        result = materialize_floorwise_legal_source(
            source,
            legal_sections=(box(0.0, 0.0, 20.0, 20.0),),
            target_plan_coverage=0.5,
            legal_floor_field_hash=LEGAL_FLOOR_FIELD_HASH,
            terminal_failure_sink=terminal_records,
        )
        self.assertIsNone(result)
        self.assertEqual(
            terminal_records[0]["evidence"]["legal_floor_field_hash"],
            LEGAL_FLOOR_FIELD_HASH,
        )

    def test_actual_llm_author_prompt_serializes_bounded_structural_feedback(self):
        graph = self._graph()
        report_records = []
        self._propagate({
            "stage": "authored_visual_authority",
            "evidence": {
                "repair_reason": "authored_matrix4_projection_failed",
                "failure_reasons": ["matrix4_certificate_failed"],
                "legal_floor_field_hash": LEGAL_FLOOR_FIELD_HASH,
            },
        }, graph, report_records, "matrix4-seed")
        feedback = graph.authored_visual_authority_replenishment_feedback(
            program_slug="task7c"
        )
        replenishment = _deficit_directed_replenishment_inputs(
            [{"instruction": "revise the failed AST mechanism"}],
            legal_fit_repair_feedback=[],
            capacity_authoring_deficits=[],
            family_supply_deficits={},
            progressive_target=None,
            authored_visual_authority_replenishment_feedback=feedback,
        )
        context = replenishment["synthesis_requests"][0]
        captured = {}

        def reject_external_request(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            raise urllib.error.URLError("task7c offline provider")

        configure_paid_provider_budget(3, quotas={
            "author_initial": 2,
            "author_replenishment": 1,
            "base_candidate": 0,
            "exact_candidate": 0,
            "portfolio_board": 0,
            "reference_audit": 0,
            "retry": 0,
        })
        with TemporaryDirectory() as temporary, patch.dict(os.environ, {
            "OPENAI_API_KEY": "task7c-test-key",
            "MAAS_GEOMETRY_AUTHOR_REPLAY_CACHE_PATH": str(
                Path(temporary) / "missing-cache.json"
            ),
        }), patch(
            "design.maas.geometry_language.llm_adapter.urllib.request.urlopen",
            side_effect=reject_external_request,
        ):
            with self.assertRaises(GeometryAuthorError):
                author_geometry_programs_with_openai(context, target_count=1)

        prompt = captured["body"]["input"][1]["content"][0]["text"]
        self.assertIn("authored_visual_authority_replenishment_feedback", prompt)
        self.assertIn("authored_visual_authority_matrix4_projection", prompt)
        self.assertIn(LEGAL_FLOOR_FIELD_HASH, prompt)
        self.assertNotIn("legal_floor_loft_or_prism_replay_allowed\": true", prompt)
