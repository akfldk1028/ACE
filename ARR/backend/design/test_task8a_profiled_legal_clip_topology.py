from copy import deepcopy
from dataclasses import replace
from unittest import TestCase

import manifold3d as m3d
import numpy as np
from shapely.geometry import MultiPolygon, Polygon, box

from design.maas.geometry_language.floorwise_profiled_legal_clip import (
    _legal_band_projection_sample_count,
    clip_profiled_mesh_to_floorwise_legal_solids,
)
from design.maas.geometry_language.profiled_mesh_numeric_repair import (
    MAXIMUM_CLEANUP_DISPLACEMENT_M,
    SECTION_EXTRACTOR_EPSILON_M,
    SECTION_ROUNDING_BUDGET_M,
    floor_center_numeric_equivalence,
)
from design.maas.geometry_language.source_bridge import _append_terminal_failure
from design.maas.book_language.candidate_generation import (
    _propagate_terminal_materialization_failure,
)
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume


IDENTITY_MATRIX4 = (
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 1.0),
)


def _authored_profiled_box(*, top_x_offset=0.0):
    footprint = box(-30.0, -30.0, 30.0, 30.0)
    corners = (
        (-30.0, -30.0, 0.0), (30.0, -30.0, 0.0),
        (30.0, 30.0, 0.0), (-30.0, 30.0, 0.0),
        (-30.0 + top_x_offset, -30.0, 1.0),
        (30.0 + top_x_offset, -30.0, 1.0),
        (30.0 + top_x_offset, 30.0, 1.0),
        (-30.0 + top_x_offset, 30.0, 1.0),
    )
    triangles = (
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7),
    )
    surfaces = tuple(
        SourceSurface(
            role=f"task8a_authored_{index:02d}",
            volume_role="mass",
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=tuple(corners[item] for item in triangle),
        )
        for index, triangle in enumerate(triangles)
    )
    return SourceMass(
        name="task8a-authored-profiled-box",
        footprint=footprint,
        volumes=(SourceVolume("mass", footprint, 0.0, 1.0, "extrude"),),
        surfaces=surfaces,
        metadata={
            "candidate_floor_context": {"height_m": 12.0},
            "geometry_program_bridge_evidence": {
                "raw_mesh_triangle_count": len(triangles),
                "exported_surface_count": len(surfaces),
            },
        },
    )


def _polygon_components(section):
    if isinstance(section, Polygon):
        return (section,)
    return tuple(section.geoms)


def _projection(occupied_sections, *, legal_sections=None, top_x_offset=0.0):
    occupied_sections = tuple(occupied_sections)
    legal_sections = tuple(legal_sections or occupied_sections)
    floor_count = len(occupied_sections)
    capacity_plates = tuple(
        SourceVolume(
            "mass",
            component,
            floor_index / floor_count,
            (floor_index + 1) / floor_count,
            "floorwise_legal_matrix4",
        )
        for floor_index, section in enumerate(occupied_sections)
        for component in _polygon_components(section)
    )
    source = _authored_profiled_box(top_x_offset=top_x_offset)
    source = SourceMass(
        name=source.name,
        footprint=source.footprint,
        upper_footprint=source.upper_footprint,
        volumes=source.volumes,
        surfaces=source.surfaces,
        metadata={
            **source.metadata,
            "floorwise_legal_matrix_stack": {
                "status": "materialized",
                "floor_capacity_plan_hash": "task8a-floor-capacity-plan",
                "floors": [
                    {"floor": index + 1, "matrix4": IDENTITY_MATRIX4}
                    for index in range(floor_count)
                ],
            },
        },
    )
    return clip_profiled_mesh_to_floorwise_legal_solids(
        source,
        occupied_sections=occupied_sections,
        legal_sections=legal_sections,
        floor_matrices=(IDENTITY_MATRIX4,) * floor_count,
        capacity_plates=capacity_plates,
        output_origin=(0.0, 0.0),
    )


def _surface_manifold(surfaces):
    vertices = []
    triangles = []
    for surface in surfaces:
        offset = len(vertices)
        vertices.extend(surface.vertices_m)
        triangles.append((offset, offset + 1, offset + 2))
    mesh = m3d.Mesh(
        np.asarray(vertices, dtype=np.float64),
        np.asarray(triangles, dtype=np.uint32),
    )
    mesh.merge()
    return m3d.Manifold(mesh)


class Task8AProfiledLegalClipTopologyTest(TestCase):
    def assertClosedComponents(self, projection, expected_count):
        self.assertTrue(projection.certificate.hard_pass)
        self.assertTrue(projection.surfaces)
        solid = _surface_manifold(projection.surfaces)
        self.assertIn("NoError", str(solid.status()))
        components = tuple(solid.decompose())
        self.assertEqual(len(components), expected_count)
        self.assertTrue(all(
            "NoError" in str(component.status()) and component.volume() > 1e-8
            for component in components
        ))

    def test_split_wing_two_components_preserves_both_closed_solids(self):
        split_wings = MultiPolygon((
            box(-12.0, -5.0, -2.0, 5.0),
            box(2.0, -5.0, 12.0, 5.0),
        ))

        projection = _projection((split_wings,))

        self.assertClosedComponents(projection, 2)
        certificate = projection.certificate.to_dict()
        self.assertEqual(certificate["final_component_count"], 2)
        self.assertEqual(
            certificate["occupied_section_topology"][0]["component_count"],
            2,
        )
        self.assertEqual(
            certificate["floor_center_topology_metrics"][0]["component_count"],
            2,
        )

    def test_courtyard_hole_is_subtracted_and_certified(self):
        courtyard = Polygon(
            ((-12.0, -10.0), (12.0, -10.0), (12.0, 10.0), (-12.0, 10.0)),
            holes=(((-3.0, -3.0), (-3.0, 3.0), (3.0, 3.0), (3.0, -3.0)),),
        )

        projection = _projection((courtyard,))

        self.assertClosedComponents(projection, 1)
        certificate = projection.certificate.to_dict()
        self.assertEqual(certificate["occupied_section_topology"][0]["hole_count"], 1)
        self.assertEqual(certificate["legal_section_topology"][0]["hole_count"], 1)
        self.assertEqual(
            certificate["floor_center_topology_metrics"][0]["hole_count"],
            1,
        )
        self.assertEqual(
            certificate["floor_center_topology_metrics"][0]["contour_count"],
            2,
        )

    def test_mixed_floors_allow_component_count_to_change(self):
        lower = MultiPolygon((
            box(-12.0, -5.0, -2.0, 5.0),
            box(2.0, -5.0, 12.0, 5.0),
        ))
        upper = box(-12.0, -5.0, 12.0, 5.0)

        projection = _projection((lower, upper))

        self.assertClosedComponents(projection, 1)
        certificate = projection.certificate.to_dict()
        self.assertEqual(
            [row["component_count"] for row in certificate["occupied_section_topology"]],
            [2, 1],
        )
        self.assertEqual(
            [row["component_count"] for row in certificate["floor_center_topology_metrics"]],
            [2, 1],
        )
        boundary_assignments = certificate["legal_revalidation_witness"][
            "boundary_assignments"
        ]
        self.assertTrue(any(
            row["adjacent_band_indices"] == [0, 1]
            and row["selected_band_index"] == 1
            for row in boundary_assignments
        ))

    def test_invalid_self_intersection_is_rejected_with_floor_witness(self):
        bow_tie = Polygon(((0.0, 0.0), (8.0, 8.0), (0.0, 8.0), (8.0, 0.0)))

        projection = _projection((bow_tie,), legal_sections=(box(-1.0, -1.0, 9.0, 9.0),))

        self.assertFalse(projection.certificate.hard_pass)
        certificate = projection.certificate.to_dict()
        self.assertEqual(
            certificate["failure_reasons"],
            ["profiled_legal_clip_occupied_section_invalid"],
        )
        self.assertEqual(certificate["failure_witness"]["floor_index"], 0)

    def test_overlapping_components_are_rejected_with_component_witness(self):
        overlapping = MultiPolygon((
            box(-8.0, -4.0, 2.0, 4.0),
            box(-2.0, -4.0, 8.0, 4.0),
        ))

        projection = _projection(
            (overlapping,),
            legal_sections=(box(-10.0, -6.0, 10.0, 6.0),),
        )

        self.assertFalse(projection.certificate.hard_pass)
        certificate = projection.certificate.to_dict()
        self.assertEqual(
            certificate["failure_reasons"],
            ["profiled_legal_clip_occupied_components_overlap"],
        )
        self.assertEqual(certificate["failure_witness"]["floor_index"], 0)
        self.assertEqual(certificate["failure_witness"]["component_index"], 0)
        self.assertEqual(certificate["failure_witness"]["other_component_index"], 1)

    def test_midplane_full_topology_mismatch_records_metrics_and_contours(self):
        expected_courtyard = Polygon(
            ((-5.0, -5.0), (5.0, -5.0), (5.0, 5.0), (-5.0, 5.0)),
            holes=(((-1.0, -1.0), (-1.0, 1.0), (1.0, 1.0), (1.0, -1.0)),),
        )
        equal_area_without_hole = box(-6.0, -4.0, 6.0, 4.0)

        projection = _projection(
            (expected_courtyard,),
            legal_sections=(equal_area_without_hole,),
        )

        self.assertFalse(projection.certificate.hard_pass)
        certificate = projection.certificate.to_dict()
        self.assertEqual(
            certificate["failure_reasons"],
            ["profiled_legal_clip_midplane_topology_mismatch"],
        )
        witness = certificate["failure_witness"]
        self.assertEqual(witness["floor_index"], 0)
        self.assertIn("floor_number", witness)
        self.assertEqual(witness["floor_number"], 1)
        self.assertEqual(witness["midplane_section_index"], 0)
        self.assertEqual(witness["midplane_z_fraction"], 0.5)
        self.assertEqual(witness["expected_component_count"], 1)
        self.assertEqual(witness["actual_component_count"], 1)
        self.assertEqual(witness["expected_polygon_count"], 1)
        self.assertEqual(witness["actual_polygon_count"], 1)
        self.assertEqual(witness["expected_ring_count"], 2)
        self.assertEqual(witness["actual_ring_count"], 1)
        self.assertEqual(witness["expected_hole_count"], 1)
        self.assertEqual(witness["actual_hole_count"], 0)
        self.assertEqual(witness["measured_hole_count"], 0)
        self.assertEqual(witness["contour_count"], 1)
        self.assertAlmostEqual(witness["expected_area_m2"], 96.0)
        self.assertAlmostEqual(witness["actual_area_m2"], 96.0)
        self.assertAlmostEqual(witness["area_delta_m2"], 0.0)
        self.assertGreater(witness["section_numeric_epsilon_m"], 0.0)
        self.assertGreaterEqual(witness["area_tolerance_m2"], 0.0)
        self.assertIn("hausdorff_bound_m", witness)
        self.assertEqual(
            witness["hausdorff_bound_m"],
            max(
                witness["section_numeric_epsilon_m"],
                SECTION_EXTRACTOR_EPSILON_M
                + MAXIMUM_CLEANUP_DISPLACEMENT_M
                + SECTION_ROUNDING_BUDGET_M,
            ),
        )
        self.assertEqual(
            witness["failed_predicates"],
            [
                "hole_count_mismatch",
                "symmetric_difference_exceeds_bound",
                "hausdorff_distance_exceeds_bound",
            ],
        )
        self.assertGreater(witness["symdiff_m2"], 0.0)
        self.assertGreater(witness["hausdorff_m"], 0.0)

    def test_hausdorff_uses_existing_bounded_numeric_envelope(self):
        expected = box(0.0, 0.0, 1000.0, 0.1)
        envelope = (
            SECTION_EXTRACTOR_EPSILON_M
            + MAXIMUM_CLEANUP_DISPLACEMENT_M
            + SECTION_ROUNDING_BUDGET_M
        )

        for offset_m in (1.23e-6, 1.33e-6):
            with self.subTest(offset_m=offset_m, expected="pass"):
                measured = box(offset_m, 0.0, 1000.0 + offset_m, 0.1)
                metrics = floor_center_numeric_equivalence(
                    measured,
                    expected,
                    epsilon_m=SECTION_EXTRACTOR_EPSILON_M,
                )
                self.assertIsNotNone(metrics)
                self.assertTrue(metrics["hard_pass"], metrics)
                self.assertAlmostEqual(metrics["hausdorff_bound_m"], envelope)
                self.assertEqual(metrics["failed_predicates"], [])
                self.assertLessEqual(metrics["area_delta_m2"], metrics["area_bound_m2"])
                self.assertLessEqual(metrics["symdiff_m2"], metrics["area_bound_m2"])

        for offset_m in (4.26e-6, 369e-6):
            with self.subTest(offset_m=offset_m, expected="fail"):
                measured = box(offset_m, 0.0, 1000.0 + offset_m, 0.1)
                metrics = floor_center_numeric_equivalence(
                    measured,
                    expected,
                    epsilon_m=SECTION_EXTRACTOR_EPSILON_M,
                )
                self.assertIsNotNone(metrics)
                self.assertFalse(metrics["hard_pass"], metrics)
                self.assertIn("hausdorff_bound_m", metrics)
                self.assertAlmostEqual(metrics["hausdorff_bound_m"], envelope)
                self.assertEqual(
                    metrics["failed_predicates"],
                    ["hausdorff_distance_exceeds_bound"],
                )
                self.assertLessEqual(metrics["area_delta_m2"], metrics["area_bound_m2"])
                self.assertLessEqual(metrics["symdiff_m2"], metrics["area_bound_m2"])

    def test_midplane_mismatch_witness_survives_source_bridge_failure_evidence(self):
        expected_courtyard = Polygon(
            ((-5.0, -5.0), (5.0, -5.0), (5.0, 5.0), (-5.0, 5.0)),
            holes=(((-1.0, -1.0), (-1.0, 1.0), (1.0, 1.0), (1.0, -1.0)),),
        )
        projection = _projection(
            (expected_courtyard,),
            legal_sections=(box(-6.0, -4.0, 6.0, 4.0),),
        )
        witness = projection.certificate.to_dict()["failure_witness"]
        sink = []

        _append_terminal_failure(
            sink,
            "authored_visual_authority",
            failure_reason="profiled_legal_clip_midplane_topology_mismatch",
            failure_witness=witness,
        )

        self.assertEqual(len(sink), 1)
        self.assertIn("failure_witness", sink[0]["evidence"])
        terminal_witness = sink[0]["evidence"]["failure_witness"]
        self.assertEqual(terminal_witness, witness)

    def test_real_midplane_mismatch_witness_survives_production_propagation(self):
        class Program:
            metadata = {"family": "task8a_profiled_mismatch"}

            def program_hash(self):
                return "task8a-profiled-mismatch-program"

        expected_courtyard = Polygon(
            ((-5.0, -5.0), (5.0, -5.0), (5.0, 5.0), (-5.0, 5.0)),
            holes=(((-1.0, -1.0), (-1.0, 1.0), (1.0, 1.0), (1.0, -1.0)),),
        )
        projection = _projection(
            (expected_courtyard,),
            legal_sections=(box(-6.0, -4.0, 6.0, 4.0),),
        )
        certificate = projection.certificate.to_dict()
        self.assertEqual(
            certificate["failure_reasons"],
            ["profiled_legal_clip_midplane_topology_mismatch"],
        )
        source_bridge_records = []
        _append_terminal_failure(
            source_bridge_records,
            "authored_visual_authority",
            repair_reason="authored_profiled_legal_clip_failed",
            failure_reason=certificate["failure_reasons"][0],
            failure_reasons=certificate["failure_reasons"],
            certificate_causes=certificate["failure_reasons"],
            certificate_modes=(certificate["status"], certificate["certification_mode"]),
            failure_witness=certificate["failure_witness"],
        )
        reports = []

        _propagate_terminal_materialization_failure(
            terminal_record=source_bridge_records[0],
            report_records=reports,
            outcome_graph=None,
            program_slug="task8a",
            source_seed="task8a_profiled_source",
            program=Program(),
            principle_id="book:task8a",
            book_scope="1/1",
        )

        self.assertEqual(len(reports), 1)
        self.assertIn("failure_witness", reports[0]["evidence"])
        self.assertEqual(
            reports[0]["evidence"]["failure_witness"],
            certificate["failure_witness"],
        )

    def test_r336_shaped_irregular_profiled_clip_succeeds_without_replay(self):
        irregular = Polygon((
            (19.209301786660244, 10.303196462622152),
            (7.952368958284199, 4.076129022809751),
            (4.463835566056591, 10.370785636863394),
            (4.0776683608121385, 11.067550186502613),
            (15.327914636438544, 17.308309178434918),
        ))

        projection = _projection((irregular,), top_x_offset=12.0)

        self.assertClosedComponents(projection, 1)
        certificate = projection.certificate.to_dict()
        self.assertEqual(certificate["certification_mode"], "floorwise_profiled_legal_clip")
        self.assertEqual(
            certificate["visible_geometry_operation"],
            "authored_profiled_mesh_legal_solid_intersection",
        )
        self.assertFalse(certificate["visible_step_fallback"])
        self.assertEqual(certificate["capacity_authority"], "floorwise_legal_volumes")
        self.assertNotEqual(certificate["exact_surface_payload_hash"], "")

    def test_floor_count_mismatch_is_typed(self):
        projection = _projection(
            (box(-4.0, -4.0, 4.0, 4.0),),
            legal_sections=(box(-5.0, -5.0, 5.0, 5.0),) * 2,
        )

        self.assertFalse(projection.certificate.hard_pass)
        self.assertEqual(
            projection.certificate.failure_reasons,
            ("profiled_legal_clip_floor_count_mismatch",),
        )

    def test_xy_escape_inside_old_buffer_is_strictly_rejected(self):
        vertices = (
            (-5e-8, 0.2, 0.25),
            (0.8, 0.2, 0.25),
            (0.2, 0.8, 0.25),
        )

        count, witness = _legal_band_projection_sample_count(
            vertices,
            ((0, 1, 2),),
            (box(0.0, 0.0, 1.0, 1.0),),
        )

        self.assertIsNone(count)
        self.assertEqual(witness["failures"][0]["face_index"], 0)
        self.assertEqual(witness["failures"][0]["adjacent_band_indices"], [0])

    def test_component_and_hole_reordering_is_certificate_and_mesh_stable(self):
        left = box(-12.0, -5.0, -4.0, 5.0)
        right = box(2.0, -3.0, 12.0, 3.0)
        first_multi = MultiPolygon((left, right))
        reordered_multi = MultiPolygon((
            Polygon(tuple(right.exterior.coords)[::-1]),
            Polygon(tuple(left.exterior.coords)[::-1]),
        ))
        shell = ((-12.0, -10.0), (12.0, -10.0), (12.0, 10.0), (-12.0, 10.0))
        small_hole = ((-8.0, -2.0), (-8.0, 2.0), (-5.0, 2.0), (-5.0, -2.0))
        large_hole = ((2.0, -3.0), (2.0, 3.0), (8.0, 3.0), (8.0, -3.0))
        first_holes = Polygon(shell, holes=(small_hole, large_hole))
        reordered_holes = Polygon(
            shell[::-1],
            holes=(large_hole[::-1], small_hole[::-1]),
        )

        first = _projection((first_multi, first_holes))
        reordered = _projection((reordered_multi, reordered_holes))

        self.assertTrue(first.certificate.hard_pass)
        self.assertTrue(reordered.certificate.hard_pass)
        first_certificate = first.certificate.to_dict()
        reordered_certificate = reordered.certificate.to_dict()
        self.assertEqual(
            first_certificate["occupied_section_topology"],
            reordered_certificate["occupied_section_topology"],
        )
        self.assertEqual(
            first_certificate["legal_section_topology"],
            reordered_certificate["legal_section_topology"],
        )
        self.assertEqual(
            first_certificate["exact_surface_payload_hash"],
            reordered_certificate["exact_surface_payload_hash"],
        )
        self.assertEqual(first.surfaces, reordered.surfaces)

    def test_legal_revalidation_witness_is_bounded_deterministically(self):
        vertices = (
            (0.1, 0.1, 0.5),
            (0.9, 0.1, 0.5),
            (0.1, 0.9, 0.5),
        )
        triangles = ((0, 1, 2),) * 100

        count, witness = _legal_band_projection_sample_count(
            vertices,
            triangles,
            (box(0.0, 0.0, 1.0, 1.0),) * 2,
        )

        self.assertEqual(count, 100)
        self.assertEqual(witness["total_count"], 100)
        self.assertEqual(witness["retained_count"], 64)
        self.assertEqual(witness["maximum_retained_count"], 64)
        self.assertTrue(witness["truncated"])
        self.assertEqual(len(witness["records"]), 64)
        self.assertTrue(all(row["status"] == "covered" for row in witness["records"]))

    def test_degenerate_and_nonmanifold_authored_inputs_fail_typed(self):
        source = _authored_profiled_box()
        degenerate_surface = replace(
            source.surfaces[0],
            vertices_m=((0.0, 0.0, 0.0),) * 3,
        )
        open_source = replace(
            source,
            surfaces=source.surfaces[:-1],
            metadata={
                **source.metadata,
                "geometry_program_bridge_evidence": {
                    "raw_mesh_triangle_count": 11,
                    "exported_surface_count": 11,
                },
            },
        )
        degenerate_source = replace(
            source,
            surfaces=(degenerate_surface, *source.surfaces[1:]),
        )
        legal = box(-5.0, -5.0, 5.0, 5.0)

        for malformed in (degenerate_source, open_source):
            with self.subTest(surface_count=len(malformed.surfaces)):
                projection = clip_profiled_mesh_to_floorwise_legal_solids(
                    replace(
                        malformed,
                        metadata={
                            **malformed.metadata,
                            "floorwise_legal_matrix_stack": {
                                "floor_capacity_plan_hash": "task8a-malformed",
                                "floors": [{"matrix4": IDENTITY_MATRIX4}],
                            },
                        },
                    ),
                    occupied_sections=(legal,),
                    legal_sections=(legal,),
                    floor_matrices=(IDENTITY_MATRIX4,),
                    capacity_plates=(SourceVolume(
                        "mass", legal, 0.0, 1.0, "floorwise_legal_matrix4"
                    ),),
                    output_origin=(0.0, 0.0),
                )
                self.assertFalse(projection.certificate.hard_pass)
                self.assertEqual(
                    projection.certificate.failure_reasons,
                    ("profiled_legal_clip_invalid_authored_manifold",),
                )

    def test_split_solid_authoritative_archive_roundtrip_and_topology_tamper_rejection(self):
        from design.maas.geometry_language.projected_visual_contract import (
            _recomputed_floorwise_authority_binding_hash,
            _task1_visual_hash,
            exact_triangle_payload_hash,
            serialize_certified_projected_visual,
            validate_projected_visual_artifact,
        )
        from design.maas.geometry_language.floorwise_profiled_legal_clip import (
            profiled_legal_section_authority_binding_hash,
        )

        split = MultiPolygon((
            box(-12.0, -5.0, -2.0, 5.0),
            box(2.0, -5.0, 12.0, 5.0),
        ))
        projection = _projection((split,))
        source = _authored_profiled_box()
        certified = replace(
            source,
            surfaces=projection.surfaces,
            metadata={
                **source.metadata,
                "floorwise_visual_projection": projection.certificate.to_dict(),
                "profiled_legal_section_authority_binding_hash": (
                    profiled_legal_section_authority_binding_hash(
                        (split,),
                        (split,),
                        (0.0, 0.0),
                    )
                ),
            },
        )

        missing_external_source_anchor = replace(
            certified,
            metadata={
                key: value
                for key, value in certified.metadata.items()
                if key != "profiled_legal_section_authority_binding_hash"
            },
        )
        with self.assertRaisesRegex(ValueError, "external lawful section binding"):
            serialize_certified_projected_visual(missing_external_source_anchor)

        artifact = serialize_certified_projected_visual(certified)
        artifact["identity"] = {
            "geometryHash": artifact["projectedVisualGeometryHash"],
        }
        expected_binding_hash = artifact["projectedVisualCertificate"][
            "section_geometry_binding_hash"
        ]
        validated = validate_projected_visual_artifact(
            artifact,
            expected_section_geometry_binding_hash=expected_binding_hash,
        )
        self.assertIsNotNone(validated)
        self.assertEqual(
            artifact["projectedVisualCertificate"]["final_component_count"],
            2,
        )

        oversized_floor_payload = deepcopy(artifact)
        oversized_floor_payload["projectedVisualCertificate"]["floor_count"] = 257
        with self.assertRaisesRegex(ValueError, "resource bound"):
            validate_projected_visual_artifact(
                oversized_floor_payload,
                expected_section_geometry_binding_hash=expected_binding_hash,
            )

        oversized_failure_codes = deepcopy(artifact)
        oversized_failure_codes["projectedVisualCertificate"][
            "mesh_cleanup_raw_gate_failure_codes"
        ] = ["gate"] * 257
        with self.assertRaisesRegex(ValueError, "resource bound"):
            validate_projected_visual_artifact(
                oversized_failure_codes,
                expected_section_geometry_binding_hash=expected_binding_hash,
            )

        oversized_failure_code_string = deepcopy(artifact)
        oversized_failure_code_string["projectedVisualCertificate"][
            "mesh_cleanup_raw_gate_failure_codes"
        ] = ["x" * 4097]
        with self.assertRaisesRegex(ValueError, "resource bound"):
            validate_projected_visual_artifact(
                oversized_failure_code_string,
                expected_section_geometry_binding_hash=expected_binding_hash,
            )

        tampered = deepcopy(artifact)
        tampered["projectedVisualCertificate"][
            "floor_center_topology_metrics"
        ][0]["component_count"] = 1
        with self.assertRaisesRegex(ValueError, "numeric equivalence mismatch"):
            validate_projected_visual_artifact(
                tampered,
                expected_section_geometry_binding_hash=expected_binding_hash,
            )

        occupied_tamper = deepcopy(artifact)
        occupied_tamper["projectedVisualCertificate"][
            "occupied_section_topology"
        ][0]["component_count"] = 1
        with self.assertRaisesRegex(ValueError, "numeric equivalence mismatch"):
            validate_projected_visual_artifact(
                occupied_tamper,
                expected_section_geometry_binding_hash=expected_binding_hash,
            )

        coordinated_tamper = deepcopy(artifact)
        moved_triangles = coordinated_tamper["projectedVisualMesh"]["triangles"]
        for triangle in moved_triangles:
            triangle["vertices_m"] = [
                [vertex[0] + 100.0, vertex[1], vertex[2]]
                for vertex in triangle["vertices_m"]
            ]
        moved_payload_hash = exact_triangle_payload_hash(
            moved_triangles
        )
        moved_visual_hash = _task1_visual_hash(moved_triangles)
        moved_certificate = coordinated_tamper["projectedVisualCertificate"]
        moved_certificate["exact_surface_payload_hash"] = moved_payload_hash
        moved_certificate["visual_hash"] = moved_visual_hash
        moved_certificate["authority_binding_hash"] = (
            _recomputed_floorwise_authority_binding_hash(
                moved_certificate,
                exact_payload_hash=moved_payload_hash,
            )
        )
        coordinated_tamper["projectedVisualPayloadHash"] = moved_payload_hash
        coordinated_tamper["projectedVisualGeometryHash"] = moved_visual_hash
        coordinated_tamper["identity"]["geometryHash"] = moved_visual_hash
        original_binding_hash = artifact["projectedVisualCertificate"][
            "section_geometry_binding_hash"
        ]
        with self.assertRaisesRegex(ValueError, "lawful section|legal containment"):
            validate_projected_visual_artifact(
                coordinated_tamper,
                expected_section_geometry_binding_hash=original_binding_hash,
            )

        from hashlib import sha256
        import json
        from shapely import from_wkb
        from shapely.affinity import translate

        fully_coordinated = deepcopy(coordinated_tamper)
        fully_coordinated_certificate = fully_coordinated[
            "projectedVisualCertificate"
        ]
        for field in ("occupied_section_wkb_hex", "legal_section_wkb_hex"):
            fully_coordinated_certificate[field] = [
                translate(from_wkb(bytes.fromhex(value)), xoff=100.0)
                .normalize()
                .wkb_hex
                for value in fully_coordinated_certificate[field]
            ]
        binding_payload = {
            "schema": fully_coordinated_certificate[
                "section_geometry_binding_schema"
            ],
            "occupied_section_wkb_hex": fully_coordinated_certificate[
                "occupied_section_wkb_hex"
            ],
            "legal_section_wkb_hex": fully_coordinated_certificate[
                "legal_section_wkb_hex"
            ],
        }
        fully_coordinated_certificate["section_geometry_binding_hash"] = sha256(
            json.dumps(
                binding_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        fully_coordinated_certificate["authority_binding_hash"] = (
            _recomputed_floorwise_authority_binding_hash(
                fully_coordinated_certificate,
                exact_payload_hash=moved_payload_hash,
            )
        )
        with self.assertRaisesRegex(ValueError, "external lawful section binding"):
            validate_projected_visual_artifact(
                fully_coordinated,
                expected_section_geometry_binding_hash=original_binding_hash,
            )
        with self.assertRaisesRegex(ValueError, "external lawful section binding"):
            validate_projected_visual_artifact(
                fully_coordinated,
                expected_semantic_context={
                    "section_geometry_binding_hash": (
                        fully_coordinated_certificate[
                            "section_geometry_binding_hash"
                        ]
                    ),
                },
            )
        with self.assertRaisesRegex(ValueError, "external lawful section binding"):
            validate_projected_visual_artifact(artifact)

        reordered_split = MultiPolygon((
            Polygon(tuple(split.geoms[1].exterior.coords)[::-1]),
            Polygon(tuple(split.geoms[0].exterior.coords)[::-1]),
        ))
        reordered_projection = _projection((reordered_split,))
        reordered_certified = replace(
            source,
            surfaces=reordered_projection.surfaces,
            metadata={
                **certified.metadata,
                "floorwise_visual_projection": reordered_projection.certificate.to_dict(),
            },
        )
        reordered_artifact = serialize_certified_projected_visual(reordered_certified)
        reordered_artifact["identity"] = {
            "geometryHash": reordered_artifact["projectedVisualGeometryHash"],
        }
        reordered_validated = validate_projected_visual_artifact(
            reordered_artifact,
            expected_section_geometry_binding_hash=original_binding_hash,
        )
        self.assertIsNotNone(reordered_validated)
        self.assertEqual(
            artifact["projectedVisualCertificate"]["section_geometry_binding_hash"],
            reordered_artifact["projectedVisualCertificate"]["section_geometry_binding_hash"],
        )
        self.assertEqual(
            artifact["projectedVisualGeometryHash"],
            reordered_artifact["projectedVisualGeometryHash"],
        )
