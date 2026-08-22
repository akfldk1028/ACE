from copy import deepcopy
from dataclasses import replace
from math import isfinite
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import manifold3d as m3d
import numpy as np
from shapely.geometry import MultiPolygon, Polygon, box

from design.maas.geometry_language.floorwise_profiled_legal_clip import (
    _legal_band_projection_sample_count,
    _effective_height_m,
    _surfaces_from_manifold,
    clip_profiled_mesh_to_floorwise_legal_solids,
)
from design.maas.geometry_language.profiled_mesh_numeric_repair import (
    MAXIMUM_CLEANUP_DISPLACEMENT_M,
    ProfiledMeshCollapseAttempt,
    ProfiledMeshRevalidationResult,
    SECTION_EXTRACTOR_EPSILON_M,
    SECTION_ROUNDING_BUDGET_M,
    floor_center_numeric_equivalence,
    _collapse_edges,
    _collapse_edges_attempt,
    _COLLAPSE_THRESHOLDS_M,
    indexed_mesh_component_volumes,
    indexed_mesh_hash,
    revalidate_or_repair_profiled_mesh,
)
from design.maas.geometry_language.source_bridge import _append_terminal_failure
from design.maas.geometry_language.floorwise_visual_projection import (
    valid_floor_center_numeric_equivalence,
)
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


def _normalized_semantic_witness(witness):
    def locate(mapping, key):
        if key in mapping:
            return mapping[key]
        for value in mapping.values():
            if isinstance(value, dict):
                found = locate(value, key)
                if found is not None:
                    return found
        return None

    def normalized(value):
        if isinstance(value, float):
            return round(value, 12)
        if isinstance(value, dict):
            return {
                key: normalized(item)
                for key, item in sorted(value.items())
            }
        if isinstance(value, (list, tuple)):
            return sorted(
                (normalized(item) for item in value),
                key=repr,
            )
        return value

    fields = (
        "floor_index",
        "floor_number",
        "midplane_section_index",
        "midplane_z_fraction",
        "actual_polygon_count",
        "expected_polygon_count",
        "actual_ring_count",
        "expected_ring_count",
        "actual_component_count",
        "expected_component_count",
        "actual_hole_count",
        "expected_hole_count",
        "contour_count",
        "measured_component_count",
        "measured_hole_count",
        "actual_area_m2",
        "expected_area_m2",
        "section_numeric_epsilon_m",
        "area_tolerance_m2",
        "area_delta_m2",
        "area_bound_m2",
        "symdiff_m2",
        "hausdorff_m",
        "hausdorff_bound_m",
        "failed_predicates",
        "profiled_mesh_revalidation",
    )
    result = {field: normalized(locate(witness, field)) for field in fields}
    for field in fields:
        if result[field] is None:
            raise AssertionError(f"semantic witness missing {field}")
    return result


def _representative_edge_chain_fixture():
    vertices = (
        (0.0, 0.0, 0.0),       # A
        (2.4e-7, 0.0, 0.0),    # B: B -> A first
        (1e-8, 2.4e-7, 0.0),   # D: A-D appears only after B -> A
        (0.0, 2.0, 0.0),
        (0.0, -2.0, 0.0),
        (2.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    triangles = (
        (0, 1, 3),
        (1, 2, 4),
        (2, 5, 6),
    )
    return vertices, triangles


def _closed_manifold_representative_edge_chain_fixture():
    diagonal = 4e-7 / (2.0 ** 0.5)
    vertices = (
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (diagonal, diagonal, 0.0),
        (diagonal, -diagonal, 0.0),
    )
    a, top, x_axis, y_axis, b, d = range(6)
    triangles = (
        (a, y_axis, x_axis),
        (top, d, x_axis),
        (d, b, x_axis),
        (b, a, x_axis),
        (a, b, y_axis),
        (b, d, y_axis),
        (d, top, y_axis),
        (x_axis, y_axis, top),
    )
    return vertices, triangles


def _authored_profiled_box(*, top_x_offset=0.0, half_extent=30.0):
    footprint = box(-half_extent, -half_extent, half_extent, half_extent)
    corners = (
        (-half_extent, -half_extent, 0.0),
        (half_extent, -half_extent, 0.0),
        (half_extent, half_extent, 0.0),
        (-half_extent, half_extent, 0.0),
        (-half_extent + top_x_offset, -half_extent, 1.0),
        (half_extent + top_x_offset, -half_extent, 1.0),
        (half_extent + top_x_offset, half_extent, 1.0),
        (-half_extent + top_x_offset, half_extent, 1.0),
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


def _projection(
    occupied_sections,
    *,
    legal_sections=None,
    top_x_offset=0.0,
    authored_half_extent=30.0,
):
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
    source = _authored_profiled_box(
        top_x_offset=top_x_offset,
        half_extent=authored_half_extent,
    )
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
    def test_continuous_clip_accepts_narrower_authored_section_above_capacity_minimum(self):
        capacity_section = box(-5.0, -5.0, 5.0, 5.0)

        projection = _projection(
            (capacity_section,),
            legal_sections=(capacity_section,),
            authored_half_extent=4.5,
        )

        certificate = projection.certificate.to_dict()
        self.assertTrue(certificate["hard_pass"], certificate)
        self.assertEqual(certificate["capacity_gfa_m2"], 100.0)
        self.assertEqual(
            certificate["floor_center_numeric_equivalence_schema"],
            "arr.maas.floor_center_visible_section.v1",
        )
        self.assertAlmostEqual(
            certificate["floor_center_topology_metrics"][0]["area_m2"],
            81.0,
        )
        self.assertTrue(valid_floor_center_numeric_equivalence(certificate))

    def test_no_eligible_edge_attempt_measures_unchanged_representative_mesh(self):
        vertices = (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 2.0, 0.5),
        )
        attempt = _collapse_edges_attempt(
            vertices,
            ((0, 1, 2),),
            maximum_length=1e-7,
            effective_height_m=14.0,
        )

        self.assertEqual(attempt.termination_reason, "no_eligible_edge")
        self.assertEqual(attempt.collapse_count, 0)
        self.assertEqual(attempt.minimum_edge_endpoint_indices, (0, 1))
        self.assertEqual(attempt.minimum_edge_delta_xyz, (1.0, 0.0, 0.0))
        self.assertEqual(attempt.minimum_surviving_edge_coordinate, 1.0)
        self.assertEqual(attempt.minimum_surviving_edge_physical_m, 1.0)

    def test_no_eligible_edge_attempt_represents_absent_degenerate_edges(self):
        for triangles in ((), ((0, 0, 0),)):
            with self.subTest(triangles=triangles):
                attempt = _collapse_edges_attempt(
                    ((0.0, 0.0, 0.0),),
                    triangles,
                    maximum_length=1e-7,
                    effective_height_m=14.0,
                )

                self.assertEqual(attempt.termination_reason, "no_eligible_edge")
                self.assertEqual(attempt.collapse_count, 0)
                self.assertEqual(attempt.minimum_edge_endpoint_indices, ())
                self.assertEqual(
                    attempt.minimum_edge_delta_xyz,
                    (0.0, 0.0, 0.0),
                )
                self.assertEqual(attempt.minimum_surviving_edge_coordinate, 0.0)
                self.assertEqual(
                    attempt.minimum_surviving_edge_physical_m,
                    0.0,
                )
                self.assertTrue(all(
                    isfinite(value)
                    for value in (
                        attempt.minimum_surviving_edge_coordinate,
                        attempt.minimum_surviving_edge_physical_m,
                        *attempt.minimum_edge_delta_xyz,
                    )
                ))
                self.assertIsNone(_collapse_edges(
                    ((0.0, 0.0, 0.0),),
                    triangles,
                    maximum_length=1e-7,
                    effective_height_m=14.0,
                ))

    def test_collapse_attempt_records_cover_every_threshold_and_selected_exact(self):
        vertices, triangles = _closed_manifold_representative_edge_chain_fixture()

        result = revalidate_or_repair_profiled_mesh(
            vertices,
            triangles,
            effective_height_m=14.0,
        )

        self.assertTrue(result.hard_pass, result.evidence())
        self.assertEqual(
            tuple(row.threshold_m for row in result.attempt_records),
            _COLLAPSE_THRESHOLDS_M,
        )
        selected = [row for row in result.attempt_records if row.selected_as_final]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].threshold_m, result.collapse_threshold_m)
        self.assertEqual(selected[0].post_gate_codes, ())
        for row in result.attempt_records:
            self.assertIn(row.termination_reason, {
                "no_eligible_edge",
                "chain_displacement_exceeded",
                "invalid_effective_height",
                "completed",
            })
            self.assertGreaterEqual(row.collapse_count, 0)
            self.assertLessEqual(
                row.max_chain_displacement_m,
                MAXIMUM_CLEANUP_DISPLACEMENT_M,
            )
            self.assertTrue(isfinite(row.max_chain_displacement_m))
            self.assertTrue(isfinite(row.threshold_m))
            self.assertTrue(isfinite(row.minimum_surviving_edge_physical_m))
            self.assertTrue(isfinite(row.minimum_surviving_edge_coordinate))
            self.assertLessEqual(len(row.minimum_edge_endpoint_indices), 2)
            self.assertTrue(all(
                0 <= index < len(vertices)
                for index in row.minimum_edge_endpoint_indices
            ))
            self.assertTrue(all(
                isfinite(value)
                for value in row.minimum_edge_delta_xyz
            ))

    def test_chain_displacement_failure_has_typed_bounded_attempt_reason(self):
        vertices = (
            (0.0, 0.0, 0.0),
            (2e-7, 0.0, 0.0),
            (-2e-7, 0.0, 0.0),
            (0.0, 2.0, 0.0),
            (0.0, -2.0, 0.0),
            (2.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
        )
        triangles = ((0, 1, 3), (1, 2, 4), (2, 5, 6))

        attempt = _collapse_edges_attempt(
            vertices,
            triangles,
            maximum_length=3e-7,
            effective_height_m=14.0,
            fixed_point=True,
        )

        self.assertEqual(attempt.termination_reason, "chain_displacement_exceeded")
        self.assertGreater(attempt.max_chain_displacement_m, 3e-7)
        self.assertLessEqual(
            attempt.max_chain_displacement_m,
            MAXIMUM_CLEANUP_DISPLACEMENT_M,
        )
        self.assertIsNone(attempt.vertices)
        self.assertIsNone(attempt.triangles)

    def test_tiny_face_only_repair_preserves_prior_one_pass_chain_behavior(self):
        vertices, triangles = _representative_edge_chain_fixture()
        one_pass = _collapse_edges(
            vertices,
            triangles,
            maximum_length=3e-7,
            effective_height_m=14.0,
            fixed_point=False,
        )
        fixed_point = _collapse_edges(
            vertices,
            triangles,
            maximum_length=3e-7,
            effective_height_m=14.0,
        )
        self.assertIsNotNone(one_pass)
        self.assertIsNotNone(fixed_point)
        self.assertNotEqual(one_pass[:2], fixed_point[:2])

        with patch(
            "design.maas.geometry_language.profiled_mesh_numeric_repair._revalidated_result",
            side_effect=[
                (SimpleNamespace(metrics={"component_count": 1}), ("tiny_face",))
            ]
            + [(SimpleNamespace(metrics={"component_count": 1}), ())]
            * len(_COLLAPSE_THRESHOLDS_M),
        ):
            result = revalidate_or_repair_profiled_mesh(
                vertices,
                triangles,
                effective_height_m=14.0,
            )

        self.assertTrue(result.hard_pass)
        self.assertEqual(result.raw_gate_codes, ("tiny_face",))
        self.assertEqual(result.collapse_threshold_m, 3e-7)
        self.assertEqual(result.certified_vertices, one_pass[0])
        self.assertEqual(result.certified_triangles, one_pass[1])
        self.assertNotEqual(result.certified_vertices, fixed_point[0])

    def test_public_revalidation_repairs_closed_manifold_chain_to_fixed_point(self):
        vertices, triangles = _closed_manifold_representative_edge_chain_fixture()

        result = revalidate_or_repair_profiled_mesh(
            vertices,
            triangles,
            effective_height_m=14.0,
        )

        self.assertTrue(result.hard_pass, result.evidence())
        self.assertIn("tiny_edge", result.raw_gate_codes)
        self.assertTrue(result.repair_attempted)
        self.assertEqual(result.post_repair_gate_codes, ())
        self.assertEqual(result.raw_component_count, 1)
        self.assertEqual(result.post_repair_component_count, 1)
        self.assertGreater(result.max_physical_displacement_m, 0.0)
        self.assertLessEqual(
            result.max_physical_displacement_m,
            MAXIMUM_CLEANUP_DISPLACEMENT_M,
        )
        self.assertIsNotNone(indexed_mesh_component_volumes(
            result.certified_vertices,
            result.certified_triangles,
        ))

    def test_collapse_rebuilds_new_subthreshold_representative_edges(self):
        vertices, triangles = _representative_edge_chain_fixture()

        collapsed = _collapse_edges(
            vertices,
            triangles,
            maximum_length=3e-7,
            effective_height_m=14.0,
        )

        self.assertIsNotNone(collapsed)
        clean_vertices, clean_triangles, displacement = collapsed
        self.assertEqual(clean_vertices, (vertices[0], vertices[6], vertices[5]))
        self.assertEqual(clean_triangles, ((0, 2, 1),))
        self.assertAlmostEqual(displacement, (1e-16 + 5.76e-14) ** 0.5)

    def test_fixed_point_chain_collapse_is_deterministic_and_repeatable(self):
        vertices, triangles = _representative_edge_chain_fixture()

        results = tuple(
            _collapse_edges(
                vertices,
                triangles,
                maximum_length=3e-7,
                effective_height_m=14.0,
            )
            for _ in range(8)
        )

        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(results[0][0], (vertices[0], vertices[6], vertices[5]))
        self.assertEqual(results[0][1], ((0, 2, 1),))

    def test_combined_numeric_gate_codes_repair_to_fully_revalidated_mesh(self):
        vertices = (
            (0.0, 0.0, 0.0),
            (1e-8, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
        triangles = ((0, 1, 2), (0, 2, 3))
        clean_vertices = (vertices[0], vertices[2], vertices[3])
        clean_triangles = ((0, 1, 2),)
        raw_compilation = SimpleNamespace(metrics={"component_count": 1})
        clean_compilation = SimpleNamespace(metrics={"component_count": 1})

        with (
            patch(
                "design.maas.geometry_language.profiled_mesh_numeric_repair._revalidated_result",
                side_effect=[(raw_compilation, ("tiny_edge", "tiny_face"))]
                + [(clean_compilation, ())] * len(_COLLAPSE_THRESHOLDS_M),
            ),
            patch(
                "design.maas.geometry_language.profiled_mesh_numeric_repair._collapse_edges_attempt",
                side_effect=lambda *args, maximum_length, **kwargs: ProfiledMeshCollapseAttempt(
                    threshold_m=maximum_length,
                    collapse_count=1,
                    termination_reason="completed",
                    max_chain_displacement_m=2e-7,
                    minimum_surviving_edge_physical_m=1.0,
                    minimum_surviving_edge_coordinate=1.0,
                    minimum_edge_endpoint_indices=(0, 1),
                    minimum_edge_delta_xyz=(1.0, 0.0, 0.0),
                    vertices=clean_vertices,
                    triangles=clean_triangles,
                ),
            ),
        ):
            result = revalidate_or_repair_profiled_mesh(
                vertices,
                triangles,
                effective_height_m=14.0,
            )

        self.assertIsInstance(result, ProfiledMeshRevalidationResult)
        self.assertTrue(result.hard_pass)
        self.assertTrue(result.repair_attempted)
        self.assertEqual(result.raw_gate_codes, ("tiny_edge", "tiny_face"))
        self.assertEqual(result.post_repair_gate_codes, ())
        self.assertEqual(result.max_physical_displacement_m, 2e-7)
        self.assertEqual(result.certified_vertices, clean_vertices)
        self.assertEqual(result.certified_triangles, clean_triangles)
        self.assertIs(result.compilation, clean_compilation)
        self.assertEqual(
            set(dict(result.numeric_measurements)),
            {
                "vertex_count",
                "triangle_count",
                "minimum_edge_length_coordinate",
                "minimum_triangle_area_coordinate2",
            },
        )

    def test_structural_gate_code_never_attempts_numeric_repair(self):
        vertices = ((0.0, 0.0, 0.0),) * 3
        triangles = ((0, 1, 2),)

        with (
            patch(
                "design.maas.geometry_language.profiled_mesh_numeric_repair._revalidated_result",
                return_value=(
                    SimpleNamespace(metrics={"component_count": 1}),
                    ("mesh_structural_revalidation_failed",),
                ),
            ),
            patch(
                "design.maas.geometry_language.profiled_mesh_numeric_repair._collapse_edges",
            ) as collapse,
        ):
            result = revalidate_or_repair_profiled_mesh(
                vertices,
                triangles,
                effective_height_m=14.0,
            )

        self.assertFalse(result.hard_pass)
        self.assertFalse(result.repair_attempted)
        self.assertEqual(
            result.raw_gate_codes,
            ("mesh_structural_revalidation_failed",),
        )
        collapse.assert_not_called()

    def test_numeric_repair_over_displacement_remains_rejected_with_codes(self):
        vertices = (
            (0.0, 0.0, 0.0),
            (1e-8, 0.0, 0.0),
            (1.0, 0.0, 0.0),
        )
        triangles = ((0, 1, 2),)

        with (
            patch(
                "design.maas.geometry_language.profiled_mesh_numeric_repair._revalidated_result",
                return_value=(
                    SimpleNamespace(metrics={"component_count": 1}),
                    ("tiny_edge",),
                ),
            ),
            patch(
                "design.maas.geometry_language.profiled_mesh_numeric_repair._collapse_edges_attempt",
                side_effect=lambda *args, maximum_length, **kwargs: ProfiledMeshCollapseAttempt(
                    threshold_m=maximum_length,
                    collapse_count=1,
                    termination_reason="chain_displacement_exceeded",
                    max_chain_displacement_m=MAXIMUM_CLEANUP_DISPLACEMENT_M * 2,
                    minimum_surviving_edge_physical_m=maximum_length,
                    minimum_surviving_edge_coordinate=maximum_length,
                    minimum_edge_endpoint_indices=(0, 1),
                    minimum_edge_delta_xyz=(maximum_length, 0.0, 0.0),
                ),
            ),
        ):
            result = revalidate_or_repair_profiled_mesh(
                vertices,
                triangles,
                effective_height_m=14.0,
            )

        self.assertFalse(result.hard_pass)
        self.assertTrue(result.repair_attempted)
        self.assertEqual(result.raw_gate_codes, ("tiny_edge",))
        self.assertEqual(
            result.post_repair_gate_codes,
            ("numeric_repair_displacement_exceeded",),
        )
        self.assertIsNone(result.certified_vertices)

    def test_numeric_repair_rejects_disappearing_raw_component(self):
        vertices = (
            (0.0, 0.0, 0.0),
            (1e-8, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
        triangles = ((0, 1, 2), (0, 2, 3))

        with (
            patch(
                "design.maas.geometry_language.profiled_mesh_numeric_repair._revalidated_result",
                side_effect=[
                    (SimpleNamespace(metrics={"component_count": 2}), ("tiny_edge",))
                ]
                + [(SimpleNamespace(metrics={"component_count": 1}), ())]
                * len(_COLLAPSE_THRESHOLDS_M),
            ),
            patch(
                "design.maas.geometry_language.profiled_mesh_numeric_repair._collapse_edges_attempt",
                side_effect=lambda *args, maximum_length, **kwargs: ProfiledMeshCollapseAttempt(
                    threshold_m=maximum_length,
                    collapse_count=1,
                    termination_reason="completed",
                    max_chain_displacement_m=2e-7,
                    minimum_surviving_edge_physical_m=1.0,
                    minimum_surviving_edge_coordinate=1.0,
                    minimum_edge_endpoint_indices=(0, 1),
                    minimum_edge_delta_xyz=(1.0, 0.0, 0.0),
                    vertices=vertices,
                    triangles=triangles,
                ),
            ),
        ):
            result = revalidate_or_repair_profiled_mesh(
                vertices,
                triangles,
                effective_height_m=14.0,
            )

        self.assertFalse(result.hard_pass)
        self.assertEqual(result.raw_component_count, 2)
        self.assertEqual(result.post_repair_component_count, 1)
        self.assertEqual(
            result.post_repair_gate_codes,
            ("numeric_repair_component_count_mismatch",),
        )
        self.assertIsNone(result.certified_vertices)

    def test_emitted_repaired_mesh_binds_count_and_changed_component_volumes(self):
        effective_height_m = _effective_height_m(_authored_profiled_box())
        self.assertGreater(effective_height_m, 0.0)
        raw_payload = {}

        def tiny_edge_manifold(*args, **kwargs):
            surfaces, vertices, triangles = _surfaces_from_manifold(
                *args,
                **kwargs,
            )
            edge_faces = {}
            for face_index, triangle in enumerate(triangles):
                for left, right in ((0, 1), (1, 2), (2, 0)):
                    edge = tuple(sorted((triangle[left], triangle[right])))
                    edge_faces.setdefault(edge, []).append(face_index)
            face_normals = []
            for triangle in triangles:
                points = tuple(np.asarray(vertices[index]) for index in triangle)
                normal = np.cross(points[1] - points[0], points[2] - points[0])
                face_normals.append(normal / np.linalg.norm(normal))
            shared_edge = next(
                edge
                for edge, faces in sorted(edge_faces.items())
                if len(faces) == 2
                and vertices[edge[0]][0] == vertices[edge[1]][0]
                and vertices[edge[0]][1] == vertices[edge[1]][1]
                and abs(vertices[edge[0]][2] - vertices[edge[1]][2]) > 0.5
                and abs(float(np.dot(
                    face_normals[faces[0]],
                    face_normals[faces[1]],
                ))) < 0.5
            )
            retained, other = sorted(
                shared_edge,
                key=lambda index: (vertices[index], index),
            )
            retained_vertex = vertices[retained]
            adjacent_faces = edge_faces[shared_edge]
            offset_direction = (
                face_normals[adjacent_faces[0]]
                + face_normals[adjacent_faces[1]]
            )
            offset_direction[2] = 0.0
            offset_direction /= np.linalg.norm(offset_direction)
            for axis in range(2):
                if abs(float(offset_direction[axis])) <= 1e-12:
                    continue
                if offset_direction[axis] < 0.0:
                    offset_direction *= -1.0
                break
            offset_m = 4e-7
            inserted_vertex = tuple(
                retained_vertex[axis] + float(offset_direction[axis]) * offset_m
                for axis in range(3)
            )
            inserted = len(vertices)
            raw_vertices = (*vertices, inserted_vertex)
            raw_triangles = []
            for triangle in triangles:
                if retained not in triangle or other not in triangle:
                    raw_triangles.append(triangle)
                    continue
                for offset in range(3):
                    left = triangle[offset]
                    right = triangle[(offset + 1) % 3]
                    third = triangle[(offset + 2) % 3]
                    if {left, right} == {retained, other}:
                        raw_triangles.extend((
                            (left, inserted, third),
                            (inserted, right, third),
                        ))
                        break
            raw_payload["vertices"] = tuple(raw_vertices)
            raw_payload["triangles"] = tuple(raw_triangles)
            return surfaces, raw_payload["vertices"], raw_payload["triangles"]

        with patch(
            "design.maas.geometry_language.floorwise_profiled_legal_clip._surfaces_from_manifold",
            side_effect=tiny_edge_manifold,
        ):
            repaired = _projection((box(-4.0, -4.0, 4.0, 4.0),))

        transition = revalidate_or_repair_profiled_mesh(
            raw_payload["vertices"],
            raw_payload["triangles"],
            effective_height_m=effective_height_m,
        )
        self.assertTrue(transition.hard_pass, transition.evidence())
        self.assertTrue(transition.repair_attempted)
        self.assertTrue(transition.raw_gate_codes)
        self.assertIn("tiny_edge", transition.raw_gate_codes)
        self.assertLessEqual(
            set(transition.raw_gate_codes),
            {"tiny_edge", "tiny_face"},
        )
        self.assertEqual(transition.post_repair_gate_codes, ())
        self.assertGreater(transition.collapse_threshold_m, 0.0)
        self.assertGreater(transition.max_physical_displacement_m, 0.0)
        self.assertLessEqual(
            transition.max_physical_displacement_m,
            MAXIMUM_CLEANUP_DISPLACEMENT_M,
        )
        self.assertEqual(
            transition.raw_component_count,
            transition.post_repair_component_count,
        )
        self.assertEqual(
            transition.raw_indexed_mesh_hash,
            indexed_mesh_hash(raw_payload["vertices"], raw_payload["triangles"]),
        )
        self.assertEqual(
            transition.clean_indexed_mesh_hash,
            indexed_mesh_hash(
                transition.certified_vertices,
                transition.certified_triangles,
            ),
        )
        raw_component_volumes = indexed_mesh_component_volumes(
            raw_payload["vertices"],
            raw_payload["triangles"],
        )
        clean_component_volumes = indexed_mesh_component_volumes(
            transition.certified_vertices,
            transition.certified_triangles,
        )
        self.assertIsNotNone(raw_component_volumes)
        self.assertIsNotNone(clean_component_volumes)
        self.assertNotEqual(raw_component_volumes, clean_component_volumes)
        self.assertTrue(
            repaired.certificate.hard_pass,
            repaired.certificate.to_dict(),
        )
        self.assertEqual(
            repaired.certificate.mesh_cleanup_raw_gate_failure_codes,
            transition.raw_gate_codes,
        )
        self.assertEqual(
            repaired.certificate.mesh_cleanup_collapse_threshold_m,
            transition.collapse_threshold_m,
        )
        self.assertEqual(
            repaired.certificate.mesh_cleanup_max_physical_displacement_m,
            transition.max_physical_displacement_m,
        )
        self.assertEqual(
            repaired.certificate.mesh_cleanup_raw_indexed_mesh_hash,
            transition.raw_indexed_mesh_hash,
        )
        self.assertEqual(
            repaired.certificate.mesh_cleanup_clean_indexed_mesh_hash,
            transition.clean_indexed_mesh_hash,
        )

        emitted_vertices = []
        emitted_triangles = []
        for surface in repaired.surfaces:
            offset = len(emitted_vertices)
            emitted_vertices.extend(surface.vertices_m)
            emitted_triangles.append((offset, offset + 1, offset + 2))
        emitted_volumes = indexed_mesh_component_volumes(
            tuple(emitted_vertices),
            tuple(emitted_triangles),
        )
        self.assertTrue(repaired.certificate.hard_pass)
        self.assertEqual(
            repaired.certificate.final_component_count,
            len(emitted_volumes),
        )
        self.assertEqual(
            repaired.certificate.final_component_volumes_m3,
            emitted_volumes,
        )
        self.assertEqual(
            emitted_volumes,
            indexed_mesh_component_volumes(
                transition.certified_vertices,
                transition.certified_triangles,
            ),
        )

    def test_real_collapse_uses_physical_xy_and_normalized_z_displacement(self):
        within_vertices = (
            (0.0, 0.0, 0.0),
            (3e-7, 0.0, 3e-8),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
        triangles = ((0, 1, 2), (0, 2, 3), (1, 3, 2))
        collapsed = _collapse_edges(
            within_vertices,
            triangles,
            maximum_length=MAXIMUM_CLEANUP_DISPLACEMENT_M,
            effective_height_m=10.0,
        )
        self.assertIsNotNone(collapsed)
        clean_vertices, clean_triangles, displacement = collapsed
        self.assertAlmostEqual(displacement, (18e-14) ** 0.5)

        with patch(
            "design.maas.geometry_language.profiled_mesh_numeric_repair._revalidated_result",
            side_effect=(
                (SimpleNamespace(metrics={"component_count": 1}), ("tiny_edge",)),
                (SimpleNamespace(metrics={"component_count": 1}), ()),
            ),
        ):
            accepted = revalidate_or_repair_profiled_mesh(
                within_vertices,
                triangles,
                effective_height_m=10.0,
            )
        self.assertTrue(accepted.hard_pass)
        self.assertEqual(accepted.certified_vertices, clean_vertices)
        self.assertEqual(accepted.certified_triangles, clean_triangles)

        excess_vertices = (
            (0.0, 0.0, 0.0),
            (8e-6, 0.0, 8e-7),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
        self.assertIsNone(_collapse_edges(
            excess_vertices,
            triangles,
            maximum_length=MAXIMUM_CLEANUP_DISPLACEMENT_M * 2.0,
            effective_height_m=10.0,
        ))
        with patch(
            "design.maas.geometry_language.profiled_mesh_numeric_repair._revalidated_result",
            return_value=(
                SimpleNamespace(metrics={"component_count": 1}),
                ("tiny_edge",),
            ),
        ):
            physically_valid = revalidate_or_repair_profiled_mesh(
                excess_vertices,
                triangles,
                effective_height_m=10.0,
            )
        self.assertTrue(physically_valid.hard_pass)
        self.assertEqual(physically_valid.certified_vertices, excess_vertices)

    def test_revalidation_failure_evidence_reaches_profiled_clip_certificate(self):
        displacement_attempt = ProfiledMeshCollapseAttempt(
            threshold_m=1e-7,
            collapse_count=2,
            termination_reason="chain_displacement_exceeded",
            max_chain_displacement_m=2e-7,
            minimum_surviving_edge_physical_m=0.25,
            minimum_surviving_edge_coordinate=0.25,
            minimum_edge_endpoint_indices=(0, 1),
            minimum_edge_delta_xyz=(0.25, 0.0, 0.0),
            post_gate_codes=(),
            raw_component_count=1,
            post_component_count=0,
            structural_evidence=(),
            selected_as_final=False,
        )
        attempt = ProfiledMeshCollapseAttempt(
            threshold_m=3e-7,
            collapse_count=2,
            termination_reason="completed",
            max_chain_displacement_m=2e-7,
            minimum_surviving_edge_physical_m=0.25,
            minimum_surviving_edge_coordinate=0.25,
            minimum_edge_endpoint_indices=(0, 1),
            minimum_edge_delta_xyz=(0.25, 0.0, 0.0),
            post_gate_codes=("mesh_structural_revalidation_failed",),
            raw_component_count=1,
            post_component_count=0,
            structural_evidence=(("manifold", False),),
            selected_as_final=False,
        )
        typed_failure = ProfiledMeshRevalidationResult(
            hard_pass=False,
            raw_gate_codes=("tiny_edge", "tiny_face"),
            numeric_measurements=(("vertex_count", 8.0),),
            repair_attempted=True,
            max_physical_displacement_m=2e-7,
            post_repair_gate_codes=("mesh_structural_revalidation_failed",),
            attempt_records=(displacement_attempt, attempt),
        )

        with patch(
            "design.maas.geometry_language.floorwise_profiled_legal_clip._revalidated_mesh",
            return_value=typed_failure,
        ):
            projection = _projection((box(-4.0, -4.0, 4.0, 4.0),))

        self.assertFalse(projection.certificate.hard_pass)
        evidence = projection.certificate.failure_witness[
            "profiled_mesh_revalidation"
        ]
        self.assertEqual(evidence["raw_gate_codes"], ["tiny_edge", "tiny_face"])
        self.assertEqual(
            evidence["post_repair_gate_codes"],
            ["mesh_structural_revalidation_failed"],
        )
        self.assertEqual(evidence["numeric_measurements"], {"vertex_count": 8.0})
        self.assertEqual(
            evidence["attempt_records"],
            [displacement_attempt.evidence(), attempt.evidence()],
        )
        self.assertEqual(
            evidence["attempt_records"][0]["termination_reason"],
            "chain_displacement_exceeded",
        )
        self.assertNotIn("message", evidence)

        missing_attempts = dict(typed_failure.evidence())
        missing_attempts.pop("attempt_records")
        self.assertNotIn("attempt_records", missing_attempts)
        missing_sink = []
        _append_terminal_failure(
            missing_sink,
            "authored_visual_authority",
            failure_witness={
                "profiled_mesh_revalidation": missing_attempts,
            },
        )
        sanitized_missing = missing_sink[0]["evidence"]["failure_witness"][
            "profiled_mesh_revalidation"
        ]
        self.assertNotIn("attempt_records", sanitized_missing)

        class Program:
            metadata = {"family": "task8a_missing_attempts"}

            def program_hash(self):
                return "task8a-missing-attempts"

        reports = []
        _propagate_terminal_materialization_failure(
            terminal_record=missing_sink[0],
            report_records=reports,
            outcome_graph=None,
            program_slug="task8a",
            source_seed="task8a_missing_attempts",
            program=Program(),
            principle_id="book:task8a",
            book_scope="1/1",
        )
        propagated_missing = reports[0]["evidence"]["failure_witness"][
            "profiled_mesh_revalidation"
        ]
        self.assertNotIn("attempt_records", propagated_missing)

    def test_five_attempt_records_survive_complete_failure_outcome_path(self):
        attempts = tuple(
            ProfiledMeshCollapseAttempt(
                threshold_m=threshold,
                collapse_count=index,
                termination_reason=(
                    "no_eligible_edge"
                    if index == 0
                    else "chain_displacement_exceeded"
                    if index == 1
                    else "completed"
                ),
                max_chain_displacement_m=index * 1e-8,
                minimum_surviving_edge_physical_m=0.5 + index * 0.1,
                minimum_surviving_edge_coordinate=0.25 + index * 0.1,
                minimum_edge_endpoint_indices=(index, index + 1),
                minimum_edge_delta_xyz=(0.25 + index * 0.1, 0.0, 0.0),
                post_gate_codes=(
                    ("numeric_repair_displacement_exceeded",)
                    if index == 1
                    else ()
                ),
                raw_component_count=1,
                post_component_count=1,
                structural_evidence=(("manifold", True), ("watertight", True)),
                selected_as_final=index == 2,
            )
            for index, threshold in enumerate(_COLLAPSE_THRESHOLDS_M)
        )
        revalidation = ProfiledMeshRevalidationResult(
            hard_pass=True,
            raw_gate_codes=("tiny_edge",),
            numeric_measurements=(("vertex_count", 8.0),),
            repair_attempted=True,
            max_physical_displacement_m=2e-8,
            post_repair_gate_codes=(),
            raw_component_count=1,
            post_repair_component_count=2,
            attempt_records=attempts,
        )

        with patch(
            "design.maas.geometry_language.floorwise_profiled_legal_clip._revalidated_mesh",
            return_value=revalidation,
        ):
            projection = _projection((box(-4.0, -4.0, 4.0, 4.0),))

        self.assertFalse(projection.certificate.hard_pass)
        expected = [attempt.evidence() for attempt in attempts]
        floorwise_records = projection.certificate.failure_witness[
            "profiled_mesh_revalidation"
        ]["attempt_records"]
        self.assertEqual(floorwise_records, expected)

        source_records = []
        _append_terminal_failure(
            source_records,
            "authored_visual_authority",
            failure_reason=projection.certificate.failure_reasons[0],
            failure_witness=projection.certificate.failure_witness,
        )
        source_attempts = source_records[0]["evidence"]["failure_witness"][
            "profiled_mesh_revalidation"
        ]["attempt_records"]
        self.assertEqual(source_attempts, expected)

        class Program:
            metadata = {"family": "task8a_attempt_path"}

            def program_hash(self):
                return "task8a-attempt-path"

        reports = []
        _propagate_terminal_materialization_failure(
            terminal_record=source_records[0],
            report_records=reports,
            outcome_graph=None,
            program_slug="task8a",
            source_seed="task8a_attempt_path",
            program=Program(),
            principle_id="book:task8a",
            book_scope="1/1",
        )
        candidate_attempts = reports[0]["evidence"]["failure_witness"][
            "profiled_mesh_revalidation"
        ]["attempt_records"]
        self.assertEqual(candidate_attempts, expected)
        self.assertEqual(len(candidate_attempts), 5)
        self.assertEqual(
            [row["threshold_m"] for row in candidate_attempts],
            list(_COLLAPSE_THRESHOLDS_M),
        )
        self.assertEqual(
            [row["termination_reason"] for row in candidate_attempts],
            [
                "no_eligible_edge",
                "chain_displacement_exceeded",
                "completed",
                "completed",
                "completed",
            ],
        )
        self.assertEqual(
            sum(row["selected_as_final"] for row in candidate_attempts),
            1,
        )
        for row in candidate_attempts:
            self.assertTrue(all(isfinite(row[key]) for key in (
                "threshold_m",
                "max_chain_displacement_m",
                "minimum_surviving_edge_physical_m",
                "minimum_surviving_edge_coordinate",
            )))
            self.assertEqual(len(row["minimum_edge_endpoint_indices"]), 2)
            self.assertEqual(len(row["minimum_edge_delta_xyz"]), 3)

    def test_floor_center_topology_area_and_containment_remain_hard_invariants(self):
        shell = box(-5.0, -5.0, 5.0, 5.0)
        courtyard = Polygon(
            tuple(shell.exterior.coords),
            holes=(((-1.0, -1.0), (-1.0, 1.0), (1.0, 1.0), (1.0, -1.0)),),
        )
        filled = shell

        topology = floor_center_numeric_equivalence(filled, courtyard)
        self.assertIsNotNone(topology)
        self.assertFalse(topology["hard_pass"])
        self.assertIn("hole_count_mismatch", topology["failed_predicates"])

        escaped = _projection(
            (box(-5.0, -5.0, 5.0, 5.0),),
            legal_sections=(box(-4.0, -4.0, 4.0, 4.0),),
        )
        self.assertFalse(escaped.certificate.hard_pass)
        self.assertIn(
            escaped.certificate.failure_reasons[0],
            {
                "profiled_legal_clip_midplane_topology_mismatch",
                "profiled_legal_clip_legal_revalidation_failed",
            },
        )

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

        for offset_m in (12.0e-6, 369e-6):
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
        self.assertEqual(
            _normalized_semantic_witness(terminal_witness),
            _normalized_semantic_witness(witness),
        )

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
        report_witness = reports[0]["evidence"]["failure_witness"]
        self.assertEqual(
            _normalized_semantic_witness(report_witness),
            _normalized_semantic_witness(certificate["failure_witness"]),
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
