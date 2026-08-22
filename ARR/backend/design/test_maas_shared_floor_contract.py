import os

from copy import deepcopy
from django.test import SimpleTestCase
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image
from shapely.affinity import translate
from shapely.geometry import (
    LineString,
    MultiPoint,
    Point,
    Polygon,
    box,
    mapping,
)
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from types import SimpleNamespace
from unittest.mock import patch

from design.maas.geometry_language.source_bridge import _mesh_section_polygon
from design.maas.geometry_language import GeometryProgramBuilder, compile_geometry_program
from design.maas.geometry_language.gate import compilation_gate
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume


def _real_final_projected_source() -> SourceMass:
    from design.maas.geometry_language import (
        base_seed_programs,
    )
    from design.maas.geometry_language.legal_field_affine_placement import (
        select_legal_field_affine_projection,
    )
    from design.maas.geometry_language.source_bridge import (
        compile_site_bound_geometry_program_to_source_mass,
    )

    program = next(
        item
        for item in base_seed_programs()
        if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
        == "slab"
    )
    legal_sections = (
        box(-6.0, -6.0, 6.0, 6.0),
        box(-6.0, -6.0, 6.0, 6.0),
    )
    selected = select_legal_field_affine_projection(
        program,
        legal_sections=legal_sections,
        target_floor_areas_m2=(100.0, 100.0),
        floor_capacity_plan_hash="shared-floor-final-source",
        maximum_exact_candidates=4,
    )
    projection = selected.projection if selected is not None else None
    assert projection is not None
    source = compile_site_bound_geometry_program_to_source_mass(
        projection.program,
        box(-10.0, -10.0, 10.0, 10.0),
        name="real-final-projected-source",
    )
    assert source is not None
    assert source.surfaces
    metadata = dict(source.metadata)
    bridge = dict(metadata["geometry_program_bridge_evidence"])
    metadata.update({
        "geometry_authority": "final_floorwise_legal_geometry_program",
        "final_program_hash": projection.certificate["final_program_hash"],
        "final_geometry_hash": projection.certificate["final_geometry_hash"],
        "final_surface_payload_hash": bridge["surface_payload_hash"],
        "final_proxy_volume_payload_hash": bridge[
            "proxy_volume_payload_hash"
        ],
        "floorwise_legal_projection": dict(projection.certificate),
    })
    bridge["geometry_authority"] = (
        "final_floorwise_legal_geometry_program"
    )
    metadata["geometry_program_bridge_evidence"] = bridge
    return replace(source, metadata=metadata)


class LegalFieldAffineUnderfillTest(SimpleTestCase):
    def test_single_affine_authored_form_can_pass_advisory_underfill(self):
        from design.maas.geometry_language import base_seed_programs
        from design.maas.geometry_language.legal_field_affine_placement import (
            select_legal_field_affine_projection,
        )

        program = next(
            item
            for item in base_seed_programs()
            if str(
                (item.metadata.get("base_seed") or {}).get("seed_id") or ""
            ) == "slab"
        )
        selection = select_legal_field_affine_projection(
            program,
            legal_sections=(
                box(-6.0, -6.0, 6.0, 6.0),
                box(-3.0, -3.0, 3.0, 3.0),
            ),
            target_floor_areas_m2=(100.0, 100.0),
            floor_capacity_plan_hash="nonuniform-underfill",
            aggregate_target_area_m2=200.0,
            minimum_aggregate_target_ratio=0.30,
        )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertTrue(selection.projection.certificate["hard_pass"])
        self.assertGreaterEqual(
            selection.evidence["achieved_aggregate_area_m2"],
            60.0,
        )
        self.assertEqual(
            selection.evidence["minimum_aggregate_target_ratio"],
            0.30,
        )
        self.assertEqual(
            selection.projection.certificate["projection_mode"],
            "authored_affine_preserved",
        )


def _hollow_square_prism_mesh():
    outer = ((-5.0, -5.0), (5.0, -5.0), (5.0, 5.0), (-5.0, 5.0))
    inner = ((-2.0, -2.0), (-2.0, 2.0), (2.0, 2.0), (2.0, -2.0))
    vertices = tuple(
        (x, y, z)
        for ring in (outer, inner)
        for z in (0.0, 1.0)
        for x, y in ring
    )

    triangles = []
    for offset in (0, 8):
        bottom = tuple(offset + index for index in range(4))
        top = tuple(offset + 4 + index for index in range(4))
        for index in range(4):
            next_index = (index + 1) % 4
            triangles.extend((
                (bottom[index], bottom[next_index], top[next_index]),
                (bottom[index], top[next_index], top[index]),
            ))
    return vertices, tuple(triangles)


def _authored_profiled_box_source(
    name: str,
    *,
    top_x_offset: float = 0.0,
) -> SourceMass:
    lower = (
        (-5.0, -5.0, 0.0),
        (5.0, -5.0, 0.0),
        (5.0, 5.0, 0.0),
        (-5.0, 5.0, 0.0),
    )
    upper = tuple(
        (x + top_x_offset, y, 1.0)
        for x, y, _z in lower
    )
    vertices = (*lower, *upper)
    triangles = (
        (0, 2, 1),
        (0, 3, 2),
        (4, 5, 6),
        (4, 6, 7),
        (0, 1, 5),
        (0, 5, 4),
        (1, 2, 6),
        (1, 6, 5),
        (2, 3, 7),
        (2, 7, 6),
        (3, 0, 4),
        (3, 4, 7),
    )
    surfaces = tuple(
        SourceSurface(
            role=f"mesh_{index}",
            volume_role="recursive_primary",
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=tuple(vertices[vertex] for vertex in triangle),
            operator="loft",
            semantic_patch_id="recursive_primary:profiled_box",
        )
        for index, triangle in enumerate(triangles)
    )
    proxy = box(-5.0, -5.0, 5.0, 5.0)
    return SourceMass(
        name=name,
        footprint=proxy,
        volumes=(
            SourceVolume(
                "recursive_primary",
                proxy,
                0.0,
                1.0,
                "geometry_program",
            ),
        ),
        surfaces=surfaces,
        metadata={"geometry_program_bridge_evidence": {
            "status": "materialized",
            "program_hash": f"{name}-program",
            "geometry_hash": f"{name}-geometry",
            "authoritative_visual_geometry": "manifold_compilation_mesh",
            "raw_mesh_triangle_count": len(triangles),
            "exported_surface_count": len(surfaces),
            "surface_coordinate_frame": "source_footprint_centroid_local",
        }},
    )


def _authored_profiled_triangle_source(
    name: str,
    *,
    world_vertices: tuple[tuple[float, float, float], ...],
    footprint: Polygon,
    closure_world_vertex: tuple[float, float, float] | None = None,
    raw_mesh_triangle_count: int | None = None,
    exported_surface_count: int | None = None,
) -> SourceMass:
    origin = footprint.centroid
    vertices = (
        *world_vertices,
        *((closure_world_vertex,) if closure_world_vertex is not None else ()),
    )
    triangles = (
        ((0, 1, 2),)
        if closure_world_vertex is None
        else (
            (0, 1, 2),
            (1, 0, 3),
            (2, 1, 3),
            (0, 2, 3),
        )
    )
    surfaces = tuple(
        SourceSurface(
            role=(
                "mesh_triangle"
                if index == 0
                else f"mesh_closure_{index}"
            ),
            volume_role="recursive_primary",
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=tuple(
                (
                    vertices[vertex][0] - float(origin.x),
                    vertices[vertex][1] - float(origin.y),
                    vertices[vertex][2],
                )
                for vertex in triangle
            ),
            operator="loft",
            semantic_patch_id=(
                "recursive_primary:profiled_triangle"
                if index == 0
                else f"recursive_primary:closure:{index}"
            ),
        )
        for index, triangle in enumerate(triangles)
    )
    return SourceMass(
        name=name,
        footprint=footprint,
        volumes=(
            SourceVolume(
                "recursive_primary",
                footprint,
                0.0,
                1.0,
                "geometry_program",
            ),
        ),
        surfaces=surfaces,
        metadata={"geometry_program_bridge_evidence": {
            "status": "materialized",
            "program_hash": f"{name}-program",
            "geometry_hash": f"{name}-geometry",
            "authoritative_visual_geometry": "manifold_compilation_mesh",
            "raw_mesh_triangle_count": (
                len(surfaces)
                if raw_mesh_triangle_count is None
                else raw_mesh_triangle_count
            ),
            "exported_surface_count": (
                len(surfaces)
                if exported_surface_count is None
                else exported_surface_count
            ),
            "surface_coordinate_frame": "source_footprint_centroid_local",
        }},
    )


class SharedFloorContractTests(SimpleTestCase):
    def test_continuous_legal_envelope_has_no_internal_horizontal_terraces(self):
        from design.maas.geometry_language import floorwise_section_loft

        builder = getattr(
            floorwise_section_loft,
            "build_continuous_legal_envelope_mesh",
            None,
        )
        self.assertIsNotNone(builder)
        sections = (
            box(-5.0, -4.0, 5.0, 4.0),
            box(-4.6, -3.6, 4.8, 3.6),
            box(-3.8, -3.0, 4.4, 3.0),
            box(-3.0, -2.4, 4.0, 2.4),
        )

        envelope = builder(
            legal_sections=sections,
            output_origin=(0.0, 0.0),
        )

        self.assertTrue(envelope.hard_pass, envelope.failure_reasons)
        self.assertTrue(envelope.vertices)
        self.assertTrue(envelope.triangles)
        self.assertEqual(
            sorted({
                round(float(vertex[2]), 10)
                for vertex in envelope.vertices
            }),
            [0.0, 0.25, 0.5, 0.75, 1.0],
        )
        internal_horizontal = []
        for triangle in envelope.triangles:
            levels = {
                round(float(envelope.vertices[index][2]), 10)
                for index in triangle
            }
            if len(levels) == 1 and next(iter(levels)) not in {0.0, 1.0}:
                internal_horizontal.append(triangle)
        self.assertEqual(internal_horizontal, [])

    def test_continuous_legal_envelope_conservatively_normalizes_numeric_reflex(self):
        from shapely.geometry import Polygon

        from design.maas.geometry_language.floorwise_section_loft import (
            build_continuous_legal_envelope_mesh,
        )

        near_convex = Polygon((
            (19.209301786660244, 10.303196462622152),
            (7.952368958284199, 4.076129022809751),
            (4.463835566056591, 10.370785636863394),
            (4.0776683608121385, 11.067550186502613),
            (15.327914636438544, 17.308309178434918),
        ))
        upper = Polygon((
            (19.209301786660244, 10.303196462622152),
            (7.952368958284199, 4.076129022809751),
            (5.099797816884418, 9.223265020497559),
            (16.41123368811874, 15.353139088336144),
        ))

        envelope = build_continuous_legal_envelope_mesh(
            legal_sections=(near_convex, near_convex, upper),
            output_origin=(0.0, 0.0),
        )

        self.assertTrue(envelope.hard_pass, envelope.failure_witness)
        self.assertEqual(envelope.failure_reasons, ())

    def test_mesh_export_execution_contract_is_hash_bound_without_changing_legacy_hash(self):
        from design.maas.geometry_language.ast import (
            FLOORWISE_CAPACITY_REPLAY_TRANSPORT_CONTRACT,
            GeometryProgram,
        )

        builder = GeometryProgramBuilder("execution-contract-hash")
        root_id = builder.add(
            "primitive",
            "box",
            parameters={"width": 2.0, "depth": 3.0, "height": 4.0},
        )
        legacy = builder.build(root_id, note="legacy")
        metadata_only = replace(legacy, metadata={"note": "changed"})
        contracted = replace(
            legacy,
            execution_contract=deepcopy(
                FLOORWISE_CAPACITY_REPLAY_TRANSPORT_CONTRACT
            ),
        )

        self.assertEqual(legacy.program_hash(), metadata_only.program_hash())
        self.assertNotEqual(legacy.program_hash(), contracted.program_hash())
        self.assertEqual(
            GeometryProgram.from_dict(contracted.to_dict()).program_hash(),
            contracted.program_hash(),
        )
        invalid = replace(
            legacy,
            execution_contract={
                "capacity_replay_numeric_transport": {"threshold": 6}
            },
        )
        self.assertIn(
            "invalid_execution_contract",
            {issue.code for issue in invalid.validate()},
        )

    def test_profiled_floor_allocation_preserves_law_derived_floor_vector(self):
        from design.maas.geometry_language.source_bridge import (
            _allocate_profiled_floor_targets,
        )

        planned = (85.256, 85.256, 62.113)
        legal_caps = (102.931, 102.931, 74.989)
        profile = (1.0, 0.7673, 0.6525)

        ordinary = _allocate_profiled_floor_targets(
            planned_floor_areas_m2=planned,
            legal_floor_caps_m2=legal_caps,
            authored_profile_ratios=profile,
        )
        bounded = _allocate_profiled_floor_targets(
            planned_floor_areas_m2=planned,
            legal_floor_caps_m2=legal_caps,
            authored_profile_ratios=profile,
            ground_design_cap_m2=85.256,
        )
        infeasible = _allocate_profiled_floor_targets(
            planned_floor_areas_m2=(60.0, 60.0),
            legal_floor_caps_m2=(50.0, 50.0),
            authored_profile_ratios=(1.0, 0.8),
            ground_design_cap_m2=50.0,
        )

        self.assertEqual(ordinary, planned)
        self.assertEqual(bounded, planned)
        self.assertEqual(infeasible, ())

    def test_global_capacity_scale_uses_total_budget_not_smallest_floor_ratio(self):
        from design.maas.geometry_language.source_bridge import (
            _global_capacity_area_scale_product,
        )

        planned = (77.198, 77.198, 56.242, 38.604)
        authored = (71.6658, 70.8058, 59.3358, 52.5929)

        scale = _global_capacity_area_scale_product(
            planned_floor_areas_m2=planned,
            source_floor_areas_m2=authored,
        )

        self.assertAlmostEqual(scale, sum(planned) / sum(authored), places=9)
        self.assertGreater(scale, min(
            planned[index] / authored[index]
            for index in range(4)
        ))

    def test_floor_fit_may_exceed_design_distribution_but_not_legal_plate(self):
        from design.maas.geometry_language.source_bridge import (
            _floor_target_fit_is_legal,
        )

        self.assertTrue(_floor_target_fit_is_legal(
            achieved_area_m2=62.0,
            maximum_legal_area_m2=75.0,
        ))
        self.assertFalse(_floor_target_fit_is_legal(
            achieved_area_m2=76.0,
            maximum_legal_area_m2=75.0,
        ))

    def test_global_target_compensates_only_for_measured_legal_clip_loss(self):
        from design.maas.geometry_language.source_bridge import (
            _capacity_compensated_global_target_area,
        )

        compensated = _capacity_compensated_global_target_area(
            current_ground_target_area_m2=70.2127,
            requested_total_area_m2=249.242,
            achieved_total_area_m2=232.8336,
        )

        self.assertAlmostEqual(compensated, 75.1608, delta=0.001)
        self.assertEqual(
            _capacity_compensated_global_target_area(
                current_ground_target_area_m2=70.2127,
                requested_total_area_m2=249.242,
                achieved_total_area_m2=232.8336,
                maximum_ground_target_area_m2=72.0,
            ),
            72.0,
        )
        self.assertEqual(
            _capacity_compensated_global_target_area(
                current_ground_target_area_m2=70.0,
                requested_total_area_m2=249.0,
                achieved_total_area_m2=250.0,
            ),
            70.0,
        )

    def test_floorwise_materializer_applies_live_ground_design_cap(self):
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        source_sections = (
            box(0.0, 0.0, 10.0, 10.0),
            box(0.0, 0.0, 7.673, 10.0),
            box(0.0, 0.0, 6.525, 10.0),
        )
        source = SourceMass(
            name="live-ground-reserve-vector",
            footprint=source_sections[0],
            volumes=tuple(
                SourceVolume(
                    "main",
                    section,
                    index / 3.0,
                    (index + 1) / 3.0,
                    "geometry_program",
                )
                for index, section in enumerate(source_sections)
            ),
            metadata={"geometry_program_bridge_evidence": {
                "program_hash": "ground-reserve-program",
                "geometry_hash": "ground-reserve-geometry",
            }},
        )
        legal = (
            box(0.0, 0.0, 10.2931, 10.0),
            box(0.0, 0.0, 10.2931, 10.0),
            box(0.0, 0.0, 7.4989, 10.0),
        )

        result = materialize_floorwise_legal_source(
            source,
            legal_sections=legal,
            target_plan_coverage=0.7,
            floor_capacity_plan_hash="live-ground-reserve-plan",
            target_floor_areas_m2=(85.256, 85.256, 62.113),
        )

        self.assertIsNotNone(result)
        assert result is not None
        allocated = result.metadata["floorwise_legal_matrix_stack"][
            "allocated_floor_areas_m2"
        ]
        self.assertEqual(
            [round(float(area), 3) for area in allocated],
            [85.256, 85.256, 62.113],
        )

    def test_floorwise_section_loft_preserves_exact_shifted_mid_sections(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            loft_floorwise_legal_sections,
        )

        occupied = (
            box(-4.0, -3.0, 4.0, 3.0),
            box(-3.0, -2.0, 5.0, 2.0),
            box(-1.5, -1.0, 4.5, 1.0),
        )
        legal = (
            box(-5.0, -4.0, 5.0, 4.0),
            box(-4.0, -3.0, 6.0, 3.0),
            box(-2.5, -2.0, 5.5, 2.0),
        )
        plates = tuple(
            SourceVolume(
                "recursive_primary",
                section,
                index / 3.0,
                (index + 1) / 3.0,
                "floorwise_legal_matrix4",
            )
            for index, section in enumerate(occupied)
        )
        source = SourceMass(
            name="nested-shifted-section-loft",
            footprint=occupied[0],
            volumes=plates,
            metadata={"floorwise_legal_matrix_stack": {
                "floor_capacity_plan_hash": "loft-plan-hash",
                "floors": [
                    {"matrix4": [
                        [1.0, 0.0, 0.0, float(index)],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ]}
                    for index in range(3)
                ],
            }},
        )

        result = loft_floorwise_legal_sections(
            source,
            occupied,
            legal,
            plates,
            (0.0, 0.0),
        )

        self.assertTrue(result.certificate.hard_pass, result.certificate)
        self.assertEqual(
            result.certificate.certification_mode,
            "floorwise_csg_section_loft",
        )
        self.assertEqual(
            result.certificate.visible_geometry_operation,
            "exact_legal_section_profile_loft",
        )
        self.assertFalse(result.certificate.visible_step_fallback)
        self.assertEqual(
            result.certificate.section_numeric_epsilon_m,
            1e-5,
        )
        vertices = tuple(
            vertex
            for surface in result.surfaces
            for vertex in surface.vertices_m
        )
        triangles = tuple(
            (index, index + 1, index + 2)
            for index in range(0, len(vertices), 3)
        )
        for index, expected in enumerate(occupied):
            measured = _mesh_section_polygon(
                vertices,
                triangles,
                (index + 0.5) / 3.0,
            )
            self.assertIsNotNone(measured)
            assert measured is not None
            self.assertAlmostEqual(measured.area, expected.area, delta=1e-6)
            self.assertAlmostEqual(
                measured.symmetric_difference(expected).area,
                0.0,
                delta=1e-6,
            )
            self.assertTrue(legal[index].buffer(1e-7).covers(measured))
        from design.maas.geometry_language.floorwise_visual_projection import (
            _has_closed_directed_edge_topology,
        )
        self.assertTrue(_has_closed_directed_edge_topology(result.surfaces))
        for field in (
            "section_profile_hash",
            "capacity_volume_hash",
            "floor_capacity_plan_hash",
            "matrix4_stack_hash",
            "exact_surface_payload_hash",
            "authority_binding_hash",
        ):
            self.assertTrue(getattr(result.certificate, field), field)
        self.assertTrue(any(
            abs(left[2] - right[2]) > 1e-8
            and (
                abs(left[0] - right[0]) > 1e-8
                or abs(left[1] - right[1]) > 1e-8
            )
            for surface in result.surfaces
            for left, right in zip(
                surface.vertices_m,
                (*surface.vertices_m[1:], surface.vertices_m[0]),
            )
        ))

    def test_floorwise_section_loft_cap_preserves_collinear_boundary_segments(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            _ear_clip,
        )

        profile = (
            (0.0, 0.0, 0.0),
            (2.66425, 0.0, 0.0),
            (5.3285, 0.0, 0.0),
            (7.99275, 0.0, 0.0),
            (10.657, 0.0, 0.0),
            (10.657, 2.0, 0.0),
            (10.657, 4.0, 0.0),
            (10.657, 6.0, 0.0),
            (10.657, 8.0, 0.0),
            (7.99275, 8.0, 0.0),
            (5.3285, 8.0, 0.0),
            (2.66425, 8.0, 0.0),
            (0.0, 8.0, 0.0),
            (0.0, 6.0, 0.0),
            (0.0, 4.0, 0.0),
            (0.0, 2.0, 0.0),
        )
        expected = Polygon([(x, y) for x, y, _z in profile])
        self.assertTrue(expected.is_valid)
        self.assertTrue(expected.exterior.is_ccw)
        self.assertAlmostEqual(expected.area, 85.256, delta=1e-9)

        triangles = _ear_clip(profile)

        self.assertIsNotNone(triangles)
        assert triangles is not None
        self.assertEqual(len(triangles), len(profile) - 2)
        triangle_polygons = tuple(
            Polygon([
                profile[left][:2],
                profile[middle][:2],
                profile[right][:2],
            ])
            for left, middle, right in triangles
        )
        self.assertTrue(all(triangle.area > 1e-12 for triangle in triangle_polygons))
        self.assertAlmostEqual(
            sum(triangle.area for triangle in triangle_polygons),
            expected.area,
            delta=1e-9,
        )
        self.assertAlmostEqual(
            unary_union(triangle_polygons).symmetric_difference(expected).area,
            0.0,
            delta=1e-9,
        )
        directed_edges = tuple(
            edge
            for triangle in triangles
            for edge in (
                (triangle[0], triangle[1]),
                (triangle[1], triangle[2]),
                (triangle[2], triangle[0]),
            )
        )
        for index in range(len(profile)):
            self.assertEqual(
                directed_edges.count((index, (index + 1) % len(profile))),
                1,
            )
        undirected_edges = tuple(
            tuple(sorted(edge))
            for edge in directed_edges
        )
        boundary_edges = {
            tuple(sorted((index, (index + 1) % len(profile))))
            for index in range(len(profile))
        }
        for edge in set(undirected_edges):
            self.assertEqual(
                undirected_edges.count(edge),
                1 if edge in boundary_edges else 2,
            )

    def test_floorwise_section_loft_cap_is_invariant_to_cyclic_ring_start(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            _ear_clip,
        )

        base_profile = (
            (0.0, 0.0, 0.0),
            (2.66425, 0.0, 0.0),
            (5.3285, 0.0, 0.0),
            (7.99275, 0.0, 0.0),
            (10.657, 0.0, 0.0),
            (10.657, 2.0, 0.0),
            (10.657, 4.0, 0.0),
            (10.657, 6.0, 0.0),
            (10.657, 8.0, 0.0),
            (7.99275, 8.0, 0.0),
            (5.3285, 8.0, 0.0),
            (2.66425, 8.0, 0.0),
            (0.0, 8.0, 0.0),
            (0.0, 6.0, 0.0),
            (0.0, 4.0, 0.0),
            (0.0, 2.0, 0.0),
        )
        for start in range(len(base_profile)):
            with self.subTest(start=start):
                profile = (
                    *base_profile[start:],
                    *base_profile[:start],
                )
                expected = Polygon([(x, y) for x, y, _z in profile])

                triangles = _ear_clip(profile)

                self.assertIsNotNone(triangles)
                assert triangles is not None
                self.assertEqual(_ear_clip(profile), triangles)
                self.assertEqual(len(triangles), len(profile) - 2)
                triangle_polygons = tuple(
                    Polygon([
                        profile[left][:2],
                        profile[middle][:2],
                        profile[right][:2],
                    ])
                    for left, middle, right in triangles
                )
                self.assertTrue(all(
                    triangle.area > 1e-12
                    for triangle in triangle_polygons
                ))
                self.assertAlmostEqual(
                    sum(triangle.area for triangle in triangle_polygons),
                    expected.area,
                    delta=1e-9,
                )
                self.assertAlmostEqual(
                    unary_union(triangle_polygons)
                    .symmetric_difference(expected)
                    .area,
                    0.0,
                    delta=1e-9,
                )
                directed_edges = tuple(
                    edge
                    for triangle in triangles
                    for edge in (
                        (triangle[0], triangle[1]),
                        (triangle[1], triangle[2]),
                        (triangle[2], triangle[0]),
                    )
                )
                boundary_edges = {
                    tuple(sorted((index, (index + 1) % len(profile))))
                    for index in range(len(profile))
                }
                for index in range(len(profile)):
                    self.assertEqual(
                        directed_edges.count((
                            index,
                            (index + 1) % len(profile),
                        )),
                        1,
                    )
                undirected_edges = tuple(
                    tuple(sorted(edge))
                    for edge in directed_edges
                )
                for edge in set(undirected_edges):
                    self.assertEqual(
                        undirected_edges.count(edge),
                        1 if edge in boundary_edges else 2,
                    )

    def test_floorwise_section_loft_cap_concavity_is_positive_or_fails_closed(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            _ear_clip,
        )

        profile = (
            (0.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
            (4.0, 4.0, 0.0),
            (2.0, 2.0, 0.0),
            (0.0, 4.0, 0.0),
        )
        expected = Polygon([(x, y) for x, y, _z in profile])
        self.assertTrue(expected.is_valid)
        self.assertTrue(expected.exterior.is_ccw)

        triangles = _ear_clip(profile)

        if triangles is None:
            return
        self.assertEqual(len(triangles), len(profile) - 2)
        triangle_polygons = tuple(
            Polygon([
                profile[left][:2],
                profile[middle][:2],
                profile[right][:2],
            ])
            for left, middle, right in triangles
        )
        self.assertTrue(all(
            triangle.area > 1e-12
            for triangle in triangle_polygons
        ))
        self.assertAlmostEqual(
            sum(triangle.area for triangle in triangle_polygons),
            expected.area,
            delta=1e-9,
        )
        self.assertAlmostEqual(
            unary_union(triangle_polygons).symmetric_difference(expected).area,
            0.0,
            delta=1e-9,
        )
        directed_edges = tuple(
            edge
            for triangle in triangles
            for edge in (
                (triangle[0], triangle[1]),
                (triangle[1], triangle[2]),
                (triangle[2], triangle[0]),
            )
        )
        boundary_edges = {
            tuple(sorted((index, (index + 1) % len(profile))))
            for index in range(len(profile))
        }
        for index in range(len(profile)):
            self.assertEqual(
                directed_edges.count((index, (index + 1) % len(profile))),
                1,
            )
        undirected_edges = tuple(
            tuple(sorted(edge))
            for edge in directed_edges
        )
        for edge in set(undirected_edges):
            self.assertEqual(
                undirected_edges.count(edge),
                1 if edge in boundary_edges else 2,
            )

    def test_floorwise_section_loft_failure_preserves_coordinate_witness(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            _failure,
        )

        result = _failure(
            "section_loft_outside_legal_envelope",
            capacity_gfa=120.0,
            source_surface_count=24,
            legal_sample_count=7,
            failure_witness={
                "stage": "triangle_coverage",
                "triangle_index": 11,
                "legal_indices": [1, 2],
            },
        )

        self.assertEqual(
            result.certificate.failure_witness,
            {
                "stage": "triangle_coverage",
                "triangle_index": 11,
                "legal_indices": [1, 2],
            },
        )

    def test_section_loft_numeric_buffer_accepts_micron_sliver_only(self):
        from design.maas.geometry_language.floorwise_visual_projection import (
            _BufferedLegalSections,
            _legal_sections_cover_triangle,
        )

        legal = box(0.0, 0.0, 10.0, 10.0)
        micron_sliver = (
            (0.0, 4.0, 0.25),
            (10.000009, 5.0, 0.25),
            (0.0, 6.0, 0.25),
        )
        material_drift = (
            (0.0, 4.0, 0.25),
            (10.00002, 5.0, 0.25),
            (0.0, 6.0, 0.25),
        )
        legal_sections = _BufferedLegalSections(
            (legal,),
            buffer_distance_m=1e-5,
        )

        self.assertTrue(_legal_sections_cover_triangle(
            micron_sliver,
            legal_sections=legal_sections,
            legal_indices=(0,),
        ))
        self.assertFalse(_legal_sections_cover_triangle(
            material_drift,
            legal_sections=legal_sections,
            legal_indices=(0,),
        ))

    def test_floorwise_section_loft_compacts_exact_collinear_breakpoints(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            _ring,
            loft_floorwise_legal_sections,
        )

        corners = ((0.0, 0.0), (12.0, 0.0), (12.0, 8.0), (0.0, 8.0))
        dense_coordinates = []
        for left, right in zip(corners, (*corners[1:], corners[0])):
            dense_coordinates.extend(
                (
                    left[0] + (right[0] - left[0]) * step / 41.0,
                    left[1] + (right[1] - left[1]) * step / 41.0,
                )
                for step in range(41)
            )
        dense = Polygon(dense_coordinates)
        self.assertEqual(len(tuple(dense.exterior.coords)) - 1, 164)
        self.assertEqual(len(_ring(dense)), 4)
        occupied = (dense, dense, dense)
        legal = (box(-1.0, -1.0, 13.0, 9.0),) * 3
        plates = tuple(
            SourceVolume(
                "main",
                section,
                index / 3.0,
                (index + 1) / 3.0,
                "floorwise_legal_matrix4",
            )
            for index, section in enumerate(occupied)
        )
        source = SourceMass(
            name="dense-collinear-live-ring",
            footprint=dense,
            volumes=plates,
            metadata={"floorwise_legal_matrix_stack": {
                "floor_capacity_plan_hash": "dense-ring-plan",
                "floors": [
                    {"matrix4": [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ]}
                    for _index in range(3)
                ],
            }},
        )

        result = loft_floorwise_legal_sections(
            source,
            occupied,
            legal,
            plates,
            (6.0, 4.0),
        )

        self.assertTrue(result.certificate.hard_pass, result.certificate)
        self.assertEqual(len(result.surfaces), 52)
        self.assertLess(len(result.surfaces), 2048)
        vertices = tuple(
            vertex
            for surface in result.surfaces
            for vertex in surface.vertices_m
        )
        triangles = tuple(
            (index, index + 1, index + 2)
            for index in range(0, len(vertices), 3)
        )
        for floor_index in range(3):
            measured = _mesh_section_polygon(
                vertices,
                triangles,
                (floor_index + 0.5) / 3.0,
            )
            self.assertIsNotNone(measured)
            assert measured is not None
            expected_local = translate(dense, xoff=-6.0, yoff=-4.0)
            self.assertAlmostEqual(
                measured.symmetric_difference(expected_local).area,
                0.0,
                delta=1e-6,
            )
            self.assertAlmostEqual(
                measured.area,
                dense.area,
                delta=1e-6,
            )

    def test_floorwise_section_loft_keeps_true_near_collinear_corner(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            loft_floorwise_legal_sections,
        )

        near_collinear = Polygon((
            (0.0, 0.0),
            (2.0, 1e-5),
            (4.0, 0.0),
            (4.0, 4.0),
            (0.0, 4.0),
        ))
        plate = SourceVolume(
            "main",
            near_collinear,
            0.0,
            1.0,
            "floorwise_legal_matrix4",
        )
        source = SourceMass(
            name="true-near-collinear-corner",
            footprint=near_collinear,
            volumes=(plate,),
            metadata={"floorwise_legal_matrix_stack": {
                "floor_capacity_plan_hash": "near-collinear-plan",
                "floors": [{"matrix4": [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ]}],
            }},
        )

        result = loft_floorwise_legal_sections(
            source,
            (near_collinear,),
            (box(-1.0, -1.0, 5.0, 5.0),),
            (plate,),
            (2.0, 2.0),
        )

        self.assertTrue(result.certificate.hard_pass, result.certificate)
        self.assertEqual(len(result.surfaces), 26)

    def test_floorwise_section_loft_compacts_live_like_noisy_straight_edges(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            _ring,
            loft_floorwise_legal_sections,
        )

        corners = (
            (0.0, 0.0),
            (10.657, 0.0),
            (10.657, 8.0),
            (0.0, 8.0),
        )
        noisy_coordinates = []
        noise_m = 2e-9
        for left, right in zip(corners, (*corners[1:], corners[0])):
            dx = right[0] - left[0]
            dy = right[1] - left[1]
            length = (dx * dx + dy * dy) ** 0.5
            normal = (-dy / length, dx / length)
            for step in range(8):
                amount = step / 8.0
                noise = (
                    0.0
                    if step == 0
                    else noise_m * (1.0 if step % 2 else -1.0)
                )
                noisy_coordinates.append((
                    left[0] + dx * amount + normal[0] * noise,
                    left[1] + dy * amount + normal[1] * noise,
                ))
        noisy = Polygon(noisy_coordinates)
        self.assertTrue(noisy.is_valid)
        self.assertEqual(len(tuple(noisy.exterior.coords)) - 1, 32)
        self.assertAlmostEqual(noisy.area, 85.256, delta=1e-6)
        self.assertEqual(len(_ring(noisy)), 4)
        plate = SourceVolume(
            "main",
            noisy,
            0.0,
            1.0,
            "floorwise_legal_matrix4",
        )
        source = SourceMass(
            name="live-like-noisy-ring",
            footprint=noisy,
            volumes=(plate,),
            metadata={"floorwise_legal_matrix_stack": {
                "floor_capacity_plan_hash": "noisy-ring-plan",
                "floors": [{"matrix4": [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ]}],
            }},
        )

        result = loft_floorwise_legal_sections(
            source,
            (noisy,),
            (box(-1.0, -1.0, 12.0, 9.0),),
            (plate,),
            tuple(noisy.centroid.coords)[0],
        )

        self.assertTrue(result.certificate.hard_pass, result.certificate)
        self.assertEqual(len(result.surfaces), 20)
        vertices = tuple(
            vertex
            for surface in result.surfaces
            for vertex in surface.vertices_m
        )
        triangles = tuple(
            (index, index + 1, index + 2)
            for index in range(0, len(vertices), 3)
        )
        measured = _mesh_section_polygon(vertices, triangles, 0.5)
        self.assertIsNotNone(measured)
        assert measured is not None
        expected_local = translate(
            noisy,
            xoff=-float(noisy.centroid.x),
            yoff=-float(noisy.centroid.y),
        )
        self.assertLessEqual(
            measured.symmetric_difference(expected_local).area,
            1e-6,
        )
        self.assertAlmostEqual(measured.area, noisy.area, delta=1e-6)

    def test_floorwise_section_loft_fails_closed_on_hole_topology(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            loft_floorwise_legal_sections,
        )

        solid = box(-4.0, -4.0, 4.0, 4.0)
        hollow = Polygon(
            solid.exterior.coords,
            holes=[box(-1.0, -1.0, 1.0, 1.0).exterior.coords],
        )
        stale = SourceSurface(
            role="stale-pre-csg",
            volume_role="main",
            verb="geometry_program",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=((50.0, 50.0, 0.0), (51.0, 50.0, 0.0), (50.0, 51.0, 1.0)),
        )
        source = SourceMass(
            name="hole-topology-mismatch",
            footprint=solid,
            volumes=(SourceVolume("main", solid, 0.0, 1.0, "base"),),
            surfaces=(stale,),
        )

        multipart = unary_union((
            box(-4.0, -4.0, -1.0, 4.0),
            box(1.0, -4.0, 4.0, 4.0),
        ))
        for invalid in (hollow, multipart):
            with self.subTest(geometry_type=invalid.geom_type):
                result = loft_floorwise_legal_sections(
                    source,
                    (solid, invalid),
                    (solid, solid),
                    source.volumes,
                    (0.0, 0.0),
                )

                self.assertFalse(result.certificate.hard_pass)
                self.assertEqual(
                    result.certificate.failure_reasons,
                    ("section_loft_topology_incompatible",),
                )
                self.assertEqual(result.surfaces, ())

    def test_floorwise_section_loft_requires_matching_plan_matrix_and_capacity(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            loft_floorwise_legal_sections,
        )

        occupied = (
            box(-4.0, -3.0, 4.0, 3.0),
            box(-3.0, -2.0, 5.0, 2.0),
        )
        legal = (box(-6.0, -5.0, 6.0, 5.0),) * 2
        plates = tuple(
            SourceVolume(
                "main",
                section,
                index / 2.0,
                (index + 1) / 2.0,
                "floorwise_legal_matrix4",
            )
            for index, section in enumerate(occupied)
        )
        floors = [
            {"matrix4": [
                [1.0, 0.0, 0.0, float(index)],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]}
            for index in range(2)
        ]
        source = SourceMass(
            name="authority-evidence-required",
            footprint=occupied[0],
            volumes=plates,
            metadata={"floorwise_legal_matrix_stack": {
                "floor_capacity_plan_hash": "required-plan",
                "floors": floors,
            }},
        )
        missing_plan = replace(source, metadata={
            "floorwise_legal_matrix_stack": {"floors": floors},
        })
        short_matrix_stack = replace(source, metadata={
            "floorwise_legal_matrix_stack": {
                "floor_capacity_plan_hash": "required-plan",
                "floors": floors[:1],
            },
        })
        mismatched_plates = (
            replace(plates[0], footprint=box(-1.0, -1.0, 1.0, 1.0)),
            plates[1],
        )

        for candidate, candidate_plates, reason in (
            (
                missing_plan,
                plates,
                "section_loft_missing_authority_evidence",
            ),
            (
                short_matrix_stack,
                plates,
                "section_loft_missing_authority_evidence",
            ),
            (
                source,
                mismatched_plates,
                "section_loft_capacity_section_mismatch",
            ),
        ):
            with self.subTest(reason=reason):
                result = loft_floorwise_legal_sections(
                    candidate,
                    occupied,
                    legal,
                    candidate_plates,
                    (0.0, 0.0),
                )
                self.assertFalse(result.certificate.hard_pass)
                self.assertEqual(result.certificate.failure_reasons, (reason,))
                self.assertEqual(result.surfaces, ())

    def test_floorwise_section_loft_rejects_overlapping_capacity_plate_gfa(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            loft_floorwise_legal_sections,
        )

        occupied = box(0.0, 0.0, 4.0, 4.0)
        duplicate_plates = (
            SourceVolume(
                "main-a",
                occupied,
                0.0,
                1.0,
                "floorwise_legal_matrix4",
            ),
            SourceVolume(
                "main-b",
                occupied,
                0.0,
                1.0,
                "floorwise_legal_matrix4",
            ),
        )
        source = SourceMass(
            name="overlapping-capacity-inflation",
            footprint=occupied,
            volumes=duplicate_plates,
            metadata={"floorwise_legal_matrix_stack": {
                "floor_capacity_plan_hash": "overlap-plan",
                "floors": [{"matrix4": [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ]}],
            }},
        )

        result = loft_floorwise_legal_sections(
            source,
            (occupied,),
            (box(-1.0, -1.0, 5.0, 5.0),),
            duplicate_plates,
            (2.0, 2.0),
        )

        self.assertEqual(occupied.area, 16.0)
        self.assertEqual(
            sum(plate.footprint.area for plate in duplicate_plates),
            32.0,
        )
        self.assertFalse(result.certificate.hard_pass)
        self.assertEqual(
            result.certificate.failure_reasons,
            ("section_loft_capacity_section_mismatch",),
        )
        self.assertEqual(result.surfaces, ())

    def test_floorwise_section_loft_transport_and_archive_reject_exact_tamper(self):
        from design.maas.geometry_language.floorwise_section_loft import (
            loft_floorwise_legal_sections,
        )
        from design.maas.geometry_language.projected_visual_contract import (
            exact_triangle_payload_hash,
            serialize_certified_projected_visual,
            validate_projected_visual_artifact,
        )

        occupied = (
            box(-4.0, -3.0, 4.0, 3.0),
            box(-3.0, -2.0, 5.0, 2.0),
        )
        legal = (box(-6.0, -5.0, 6.0, 5.0),) * 2
        plates = tuple(
            SourceVolume(
                "main",
                section,
                index / 2.0,
                (index + 1) / 2.0,
                "floorwise_legal_matrix4",
            )
            for index, section in enumerate(occupied)
        )
        source = SourceMass(
            name="exact-loft-transport",
            footprint=occupied[0],
            volumes=plates,
            metadata={"floorwise_legal_matrix_stack": {
                "floor_capacity_plan_hash": "transport-plan",
                "floors": [
                    {"matrix4": [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ]},
                    {"matrix4": [
                        [1.0, 0.0, 0.0, 1.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ]},
                ],
            }},
        )
        projection = loft_floorwise_legal_sections(
            source,
            occupied,
            legal,
            plates,
            (0.0, 0.0),
        )
        self.assertTrue(projection.certificate.hard_pass)
        certified = replace(
            source,
            surfaces=projection.surfaces,
            metadata={
                **source.metadata,
                "floorwise_visual_projection": (
                    projection.certificate.to_dict()
                ),
            },
        )
        artifact = serialize_certified_projected_visual(certified)
        artifact["identity"] = {
            "geometryHash": artifact["projectedVisualGeometryHash"],
        }
        self.assertIsNotNone(validate_projected_visual_artifact(artifact))

        first = certified.surfaces[0]
        vertices = list(first.vertices_m)
        vertices[0] = (
            vertices[0][0] + 1e-9,
            vertices[0][1],
            vertices[0][2],
        )
        source_tamper = replace(
            certified,
            surfaces=(
                replace(first, vertices_m=tuple(vertices)),
                *certified.surfaces[1:],
            ),
        )
        with self.assertRaisesRegex(ValueError, "exact payload hash mismatch"):
            serialize_certified_projected_visual(source_tamper)

        binding_tamper = deepcopy(certified.metadata)
        binding_tamper["floorwise_visual_projection"][
            "section_profile_hash"
        ] = "a" * 64
        with self.assertRaisesRegex(ValueError, "authority binding mismatch"):
            serialize_certified_projected_visual(
                replace(certified, metadata=binding_tamper)
            )

        archive_tamper = deepcopy(artifact)
        archive_tamper["projectedVisualMesh"]["triangles"][0][
            "vertices_m"
        ][0][0] += 1e-9
        tampered_payload = exact_triangle_payload_hash(
            archive_tamper["projectedVisualMesh"]["triangles"]
        )
        archive_tamper["projectedVisualPayloadHash"] = tampered_payload
        archive_tamper["projectedVisualCertificate"][
            "exact_surface_payload_hash"
        ] = tampered_payload
        with self.assertRaisesRegex(ValueError, "authority binding mismatch"):
            validate_projected_visual_artifact(archive_tamper)

        archive_component_tamper = deepcopy(artifact)
        archive_component_tamper["projectedVisualCertificate"][
            "matrix4_stack_hash"
        ] = "b" * 64
        with self.assertRaisesRegex(ValueError, "authority binding mismatch"):
            validate_projected_visual_artifact(archive_component_tamper)

        mode_mutations = (
            (
                "certification_mode",
                "floorwise_matrix_prism_exact_containment",
            ),
            (
                "certification_mode",
                "unknown_floorwise_authority_mode",
            ),
            (
                "visible_geometry_operation",
                "floorwise_matrix_prism_recomposition",
            ),
            ("visible_step_fallback", True),
        )
        for field, value in mode_mutations:
            with self.subTest(source_mode_field=field):
                source_mode_tamper = deepcopy(certified.metadata)
                source_mode_tamper["floorwise_visual_projection"][
                    field
                ] = value
                with self.assertRaisesRegex(
                    ValueError,
                    "(?:authority binding mismatch|authority mode mismatch)",
                ):
                    serialize_certified_projected_visual(
                        replace(certified, metadata=source_mode_tamper)
                    )
            with self.subTest(archive_mode_field=field):
                archive_mode_tamper = deepcopy(artifact)
                archive_mode_tamper["projectedVisualCertificate"][
                    field
                ] = value
                with self.assertRaisesRegex(
                    ValueError,
                    "(?:authority binding mismatch|authority mode mismatch)",
                ):
                    validate_projected_visual_artifact(archive_mode_tamper)

        unknown_source_tamper = deepcopy(source_tamper.metadata)
        unknown_source_tamper["floorwise_visual_projection"][
            "certification_mode"
        ] = "unknown_floorwise_authority_mode"
        with self.assertRaisesRegex(ValueError, "authority mode mismatch"):
            serialize_certified_projected_visual(
                replace(source_tamper, metadata=unknown_source_tamper)
            )

        unknown_archive_tamper = deepcopy(artifact)
        unknown_archive_tamper["projectedVisualCertificate"][
            "certification_mode"
        ] = "unknown_floorwise_authority_mode"
        unknown_archive_tamper["projectedVisualMesh"]["triangles"][0][
            "vertices_m"
        ][0][0] += 1e-9
        unknown_archive_tamper["projectedVisualPayloadHash"] = (
            exact_triangle_payload_hash(
                unknown_archive_tamper["projectedVisualMesh"]["triangles"]
            )
        )
        with self.assertRaisesRegex(ValueError, "authority mode mismatch"):
            validate_projected_visual_artifact(unknown_archive_tamper)

    def test_unrelated_authored_exact_visual_mode_remains_transportable(self):
        from design.maas.geometry_language.floorwise_visual_projection import (
            certify_authored_visual_mesh,
        )
        from design.maas.geometry_language.projected_visual_contract import (
            serialize_certified_projected_visual,
        )

        source = _authored_profiled_box_source("legacy-authored-exact")
        projection = certify_authored_visual_mesh(
            source,
            (box(-20.0, -20.0, 20.0, 20.0),) * 2,
        )
        self.assertTrue(projection.certificate.hard_pass)
        certified = replace(
            source,
            metadata={
                **source.metadata,
                "floorwise_visual_projection": (
                    projection.certificate.to_dict()
                ),
            },
        )

        artifact = serialize_certified_projected_visual(certified)

        self.assertEqual(
            artifact["projectedVisualCertificate"]["certification_mode"],
            "authored_visual_legal_validation",
        )

    def test_shared_floor_contract_repairs_non_noded_candidate_topology(self):
        from design.maas.shared_floor_contract import materialize_shared_floor_contract

        self_intersecting = Polygon(
            [(0.0, 0.0), (10.0, 10.0), (10.0, 0.0), (0.0, 10.0), (0.0, 0.0)]
        )
        source = SourceMass(
            name="invalid_intermediate_candidate",
            footprint=box(0.0, 0.0, 10.0, 10.0),
            volumes=(
                SourceVolume(
                    "main",
                    self_intersecting,
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
        )

        contract = materialize_shared_floor_contract(
            source,
            site_local_utm=box(0.0, 0.0, 10.0, 10.0),
            legal_sections=(box(0.0, 0.0, 10.0, 10.0),) * 5,
            height_m=15.0,
            floors=5,
        )

        self.assertEqual(contract["schema_version"], "arr.maas.shared_floor_contract.v1")
        self.assertEqual(len(contract["plates"]), 5)
        self.assertNotIn("invalid_floor_topology", contract["failure_reasons"])

    def test_shared_floor_contract_discards_line_residue_from_mixed_overlay(self):
        from design.maas.shared_floor_contract import materialize_shared_floor_contract

        inside = box(1.0, 1.0, 6.0, 6.0)
        boundary_touch_only = box(10.0, 2.0, 12.0, 4.0)
        source = SourceMass(
            name="mixed_dimension_overlay_candidate",
            footprint=inside,
            volumes=(
                SourceVolume("main", inside, 0.0, 1.0, "geometry_program"),
                SourceVolume(
                    "annex",
                    boundary_touch_only,
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
        )

        contract = materialize_shared_floor_contract(
            source,
            site_local_utm=box(0.0, 0.0, 10.0, 10.0),
            legal_sections=(box(0.0, 0.0, 10.0, 10.0),) * 5,
            height_m=15.0,
            floors=5,
        )

        self.assertEqual(len(contract["plates"]), 5)
        self.assertNotIn("invalid_floor_topology", contract["failure_reasons"])
        self.assertTrue(all(plate["gross_area_m2"] == 25.0 for plate in contract["plates"]))

    def test_shared_floor_contract_preserves_disjoint_wing_components(self):
        from design.maas.shared_floor_contract import materialize_shared_floor_contract

        west_wing = box(0.0, 0.0, 10.0, 10.0)
        east_wing = box(20.0, 0.0, 30.0, 10.0)
        source = SourceMass(
            name="disjoint_wing_candidate",
            footprint=unary_union((west_wing, east_wing)),
            volumes=(
                SourceVolume("west", west_wing, 0.0, 1.0, "geometry_program"),
                SourceVolume("east", east_wing, 0.0, 1.0, "geometry_program"),
            ),
        )

        contract = materialize_shared_floor_contract(
            source,
            site_local_utm=box(0.0, 0.0, 40.0, 20.0),
            legal_sections=(box(0.0, 0.0, 40.0, 20.0),) * 2,
            height_m=6.0,
            floors=2,
        )

        self.assertTrue(contract["hard_pass"], contract["failure_reasons"])
        self.assertTrue(all(
            plate["occupied_geometry_utm"]["type"] == "MultiPolygon"
            for plate in contract["plates"]
        ))
        self.assertTrue(all(
            plate["gross_area_m2"] == 200.0
            for plate in contract["plates"]
        ))
        self.assertEqual(contract["plates"][1]["support_ratio"], 1.0)

    def test_shared_floor_contract_preserves_courtyard_hole_and_support(self):
        from design.maas.shared_floor_contract import materialize_shared_floor_contract

        courtyard = Polygon(
            box(0.0, 0.0, 20.0, 20.0).exterior.coords,
            (box(6.0, 6.0, 14.0, 14.0).exterior.coords,),
        )
        source = SourceMass(
            name="courtyard_candidate",
            footprint=courtyard,
            volumes=(
                SourceVolume("court", courtyard, 0.0, 1.0, "geometry_program"),
            ),
        )

        contract = materialize_shared_floor_contract(
            source,
            site_local_utm=box(-5.0, -5.0, 25.0, 25.0),
            legal_sections=(box(-5.0, -5.0, 25.0, 25.0),) * 2,
            height_m=6.0,
            floors=2,
        )

        self.assertTrue(contract["hard_pass"], contract["failure_reasons"])
        for plate in contract["plates"]:
            self.assertEqual(plate["occupied_geometry_utm"]["type"], "Polygon")
            self.assertEqual(len(plate["occupied_geometry_utm"]["coordinates"]), 2)
            self.assertEqual(plate["gross_area_m2"], 336.0)
        self.assertEqual(contract["plates"][1]["support_ratio"], 1.0)

    def test_smoke_keeps_downstream_reserve_after_first_floor_capacity_pass(self):
        try:
            from design.maas.book_language.portfolio_benchmark import (
                _smoke_floor_pass_reserve,
            )
        except ImportError:
            self.fail("smoke benchmark has no downstream survival reserve")

        self.assertEqual(_smoke_floor_pass_reserve(1), 3)
        self.assertEqual(_smoke_floor_pass_reserve(2), 6)
        self.assertEqual(_smoke_floor_pass_reserve(1, live_vlm=True), 12)
        with patch.dict(os.environ, {"MAAS_FINAL_BOOK_VLM_TOP_K": "1"}):
            self.assertEqual(_smoke_floor_pass_reserve(1, live_vlm=True), 3)

    def test_floorwise_legal_stack_uses_five_matrix_fitted_ast_bands(self):
        """One authored body becomes five legal plates without a finished-form template."""
        try:
            from design.maas.geometry_language.source_bridge import (
                materialize_floorwise_legal_source,
            )
        except ImportError:
            self.fail("source bridge has no floorwise legal matrix-stack modifier")
        from design.maas.shared_floor_contract import materialize_shared_floor_contract

        source = SourceMass(
            name="authored_ast_mass",
            footprint=box(0.0, 0.0, 10.0, 10.0),
            volumes=(
                SourceVolume(
                    "recursive_primary",
                    box(0.0, 0.0, 10.0, 10.0),
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            metadata={
                "geometry_program_bridge_evidence": {
                    "program_hash": "program-hash",
                    "geometry_hash": "geometry-hash",
                },
                "program_space_zones": [
                    {"role": "service", "plan_area_ratio": 0.20},
                    {"role": "entry", "plan_area_ratio": 0.15},
                ],
                "capacity_alternative_projection": {
                    "schema_version": "arr.maas.capacity_alternative.v1",
                    "alternative_id": "brief_target",
                    "target_utilization": 0.90,
                    "requested_capacity_alternative_id": "brief_target",
                    "requested_target_utilization": 0.90,
                    "selectable_capacity_alternative_id": "spatial_reserve",
                    "selectable_capacity_target_utilization": 0.70,
                    "selectable_capacity_hard_pass": True,
                },
            },
        )
        legal_sections = (
            box(0.0, 0.0, 10.0, 10.0),
            box(0.0, 0.0, 10.0, 10.0),
            box(0.0, 0.0, 10.0, 10.0),
            box(1.0, 1.0, 9.0, 9.0),
            box(1.65, 1.65, 8.35, 8.35),
        )

        stacked = materialize_floorwise_legal_source(
            source,
            legal_sections=legal_sections,
            target_plan_coverage=0.90,
            floor_capacity_plan_hash="capacity-plan-123",
            target_floor_areas_m2=(90.0, 90.0, 90.0, 57.6, 40.4),
        )

        self.assertIsNotNone(stacked)
        assert stacked is not None
        self.assertEqual(len(stacked.volumes), 5)
        self.assertEqual(
            {volume.role for volume in stacked.volumes},
            {"recursive_primary"},
        )
        self.assertEqual(stacked.surfaces, ())
        evidence = stacked.metadata["floorwise_legal_matrix_stack"]
        self.assertEqual(evidence["floor_count"], 5)
        self.assertEqual(evidence["floor_capacity_plan_hash"], "capacity-plan-123")
        coherence = stacked.metadata["coherence_evidence"]
        self.assertTrue(coherence["hard_pass"], coherence)
        self.assertTrue(coherence["floorwise_quality_uses_occupied_plates"])
        self.assertEqual(coherence["floorwise_quality_plate_count"], 5)
        self.assertFalse(evidence["completed_building_template"])
        self.assertTrue(all(
            row["floor_capacity_plan_hash"] == "capacity-plan-123"
            for row in evidence["floors"]
        ))
        self.assertEqual(
            [len(row["matrix4"]) for row in evidence["floors"]],
            [4, 4, 4, 4, 4],
        )
        self.assertTrue(all(
            row["matrix4"][3] == [0.0, 0.0, 0.0, 1.0]
            for row in evidence["floors"]
        ))
        for volume, legal in zip(stacked.volumes, legal_sections):
            self.assertTrue(legal.buffer(1e-7).covers(volume.footprint))
            self.assertAlmostEqual(
                volume.footprint.area,
                legal.area * 0.90,
                delta=0.05,
            )

        try:
            from design.maas.geometry_language.source_bridge import (
                floorwise_source_to_geometry_program,
            )
        except ImportError:
            self.fail("source bridge cannot serialize the final five-floor mass for exact replay")
        clockwise_stacked = replace(
            stacked,
            volumes=tuple(
                replace(volume, footprint=orient(volume.footprint, sign=-1.0))
                for volume in stacked.volumes
            ),
        )
        replay_program = floorwise_source_to_geometry_program(
            clockwise_stacked,
            height_m=15.0,
            name="authored_ast_mass_final_projection",
        )
        replay_compilation = compile_geometry_program(replay_program)
        self.assertEqual(replay_compilation.status, "compiled", replay_compilation.issues)
        self.assertEqual(compilation_gate(replay_compilation), ())
        self.assertEqual(
            replay_program.metadata["floorwise_projection"]["floor_count"],
            5,
        )
        self.assertEqual(
            replay_program.metadata["floorwise_projection"]["upstream_program_hash"],
            "program-hash",
        )
        self.assertEqual(
            replay_program.metadata["floorwise_projection"]["floor_capacity_plan_hash"],
            "capacity-plan-123",
        )
        self.assertEqual(
            replay_program.metadata["floorwise_projection"]["target_floor_areas_m2"],
            [90.0, 90.0, 90.0, 57.6, 40.4],
        )
        self.assertEqual(
            replay_program.metadata["floorwise_projection"][
                "selectable_capacity_alternative_id"
            ],
            "spatial_reserve",
        )
        self.assertFalse(
            replay_program.metadata["floorwise_projection"]["completed_building_template"]
        )
        self.assertEqual(
            len([
                node
                for node in replay_program.nodes
                if node.kind == "transform" and node.operator == "translate"
            ]),
            5,
        )

        for volume in stacked.volumes:
            z_m = 15.0 * (
                float(volume.bottom_fraction) + float(volume.top_fraction)
            ) / 2.0
            section = _mesh_section_polygon(
                replay_compilation.vertices,
                replay_compilation.triangles,
                z_m,
            )
            self.assertIsNotNone(section)
            assert section is not None
            self.assertAlmostEqual(section.area, volume.footprint.area, delta=0.1)

        contract = materialize_shared_floor_contract(
            stacked,
            site_local_utm=box(0.0, 0.0, 10.0, 10.0),
            legal_sections=legal_sections,
            height_m=15.0,
            floors=5,
            program_hash="program-hash",
            geometry_hash="geometry-hash",
            feasible_capacity_m2=sum(section.area for section in legal_sections),
            floor_capacity_plan_hash="capacity-plan-123",
        )
        self.assertTrue(contract["hard_pass"], contract["failure_reasons"])
        self.assertEqual(contract["floor_capacity_plan_hash"], "capacity-plan-123")
        self.assertEqual(
            contract["identity"]["floor_capacity_plan_hash"],
            "capacity-plan-123",
        )
        self.assertEqual(
            contract["target_floor_areas_m2"],
            [90.0, 90.0, 90.0, 57.6, 40.4],
        )
        self.assertEqual(
            contract["capacity_alternative"]["requested_capacity_alternative_id"],
            "brief_target",
        )
        self.assertEqual(
            contract["capacity_alternative"]["selectable_capacity_alternative_id"],
            "spatial_reserve",
        )
        self.assertEqual(contract["totals"]["num_floors"], 5)
        self.assertAlmostEqual(contract["totals"]["capacity_utilization"], 0.90, places=3)

        from design.maas.program_massing.spatial_evaluation import (
            attach_program_spatial_evidence,
        )
        feature = {
            "type": "Feature",
            "geometry": mapping(stacked.footprint),
            "properties": {
                "benchmark_site_area_m2": 100.0,
                "source_signature": stacked.signature(),
                "mass_volumes": [
                    {
                        "geometry": mapping(volume.footprint),
                        "bottom_height": 15.0 * volume.bottom_fraction,
                        "top_height": 15.0 * volume.top_fraction,
                        "role": volume.role,
                    }
                    for volume in stacked.volumes
                ],
            },
        }
        spatial = attach_program_spatial_evidence(
            feature,
            building_type="neighborhood",
            site_area_m2=100.0,
        )
        self.assertGreaterEqual(spatial["dominant_ratio_score"], 0.55)

    def test_floorwise_matrix_fit_uses_one_global_affine_to_reach_target_area(self):
        """Site adaptation may use one shared 4x4 plan transform, not per-floor warps."""
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        source = SourceMass(
            name="long_authored_bar",
            footprint=box(0.0, 0.0, 10.0, 5.0),
            volumes=(
                SourceVolume(
                    "recursive_primary",
                    box(0.0, 0.0, 10.0, 5.0),
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            metadata={
                "geometry_program_bridge_evidence": {
                    "program_hash": "long-bar-program",
                    "geometry_hash": "long-bar-geometry",
                },
            },
        )

        stacked = materialize_floorwise_legal_source(
            source,
            legal_sections=(box(0.0, 0.0, 10.0, 10.0),),
            target_plan_coverage=0.80,
            floor_capacity_plan_hash="capacity-plan-nonuniform",
            target_floor_areas_m2=(80.0,),
        )

        self.assertIsNotNone(stacked)
        assert stacked is not None
        floor = stacked.metadata["floorwise_legal_matrix_stack"]["floors"][0]
        self.assertAlmostEqual(floor["achieved_plan_area_m2"], 80.0, delta=0.1)
        volume = stacked.volumes[0]
        self.assertAlmostEqual(volume.footprint.centroid.y, 5.0, delta=0.01)
        matrix = floor["matrix4"]
        self.assertNotAlmostEqual(abs(matrix[0][0]), abs(matrix[1][1]), delta=0.05)
        stack = stacked.metadata["floorwise_legal_matrix_stack"]
        self.assertEqual(
            stack["pose_fit"],
            "single_global_rotation_translation_with_floor_relative_pose_preserved",
        )
        self.assertEqual(len(stack["global_plan_axis_scales"]), 2)

    def test_floorwise_matrix_fit_search_reaches_feasible_target_in_irregular_host(self):
        """A bounded fit must shrink in place, never substitute another pose."""
        from math import hypot
        from design.maas.geometry_language import source_bridge
        from design.maas.geometry_language.source_bridge import (
            _matrix_fit_polygon_to_host,
            _principal_frame,
            _requested_plan_axis_scales,
        )

        legal_host = Polygon((
            (19.2093017867, 10.3031964626),
            (7.9523689583, 4.0761290228),
            (4.4638355661, 10.3707856369),
            (4.0776683608, 11.0675501865),
            (15.3279146364, 17.3083091784),
        ))
        authored_notch = Polygon((
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (6.0, 10.0),
            (6.0, 4.0),
            (4.0, 4.0),
            (4.0, 10.0),
            (0.0, 10.0),
        ))
        target_area = float(legal_host.area) * 0.70
        source_angle, _source_width, _source_depth = _principal_frame(
            authored_notch.convex_hull
        )
        legal_angle, _legal_width, _legal_depth = _principal_frame(legal_host)
        scales = _requested_plan_axis_scales(
            authored_notch,
            legal_host,
            target_area=target_area,
            target_angle_offset_degrees=legal_angle - source_angle,
        )
        self.assertIsNotNone(scales)
        assert scales is not None
        authored_ratio = scales[0] / scales[1]
        with patch.object(
            source_bridge,
            "affine_transform",
            wraps=source_bridge.affine_transform,
        ) as fit_transform:
            fitted = _matrix_fit_polygon_to_host(
                authored_notch,
                legal_host,
                target_area=target_area,
                target_center=(
                    float(legal_host.centroid.x),
                    float(legal_host.centroid.y),
                ),
                target_angle_offset_degrees=legal_angle - source_angle,
                anisotropy_ratio=authored_ratio,
            )

        self.assertIsNotNone(fitted)
        assert fitted is not None
        occupied, matrix = fitted
        self.assertTrue(legal_host.buffer(1e-7).covers(occupied))
        fitted_ratio = (
            hypot(matrix[0][0], matrix[1][0])
            / hypot(matrix[0][1], matrix[1][1])
        )
        self.assertAlmostEqual(fitted_ratio, authored_ratio, delta=1e-9)
        self.assertAlmostEqual(float(occupied.area), 65.221, delta=0.02)
        self.assertLessEqual(fit_transform.call_count, 13)

    def test_floorwise_materializer_can_use_bounded_legal_csg_projection(self):
        """A near-fit authored notch may be clipped, but never underfill GFA."""
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        legal_host = Polygon((
            (19.2093017867, 10.3031964626),
            (7.9523689583, 4.0761290228),
            (4.4638355661, 10.3707856369),
            (4.0776683608, 11.0675501865),
            (15.3279146364, 17.3083091784),
        ))
        authored_notch = Polygon((
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (6.0, 10.0),
            (6.0, 4.0),
            (4.0, 4.0),
            (4.0, 10.0),
            (0.0, 10.0),
        ))
        target_area = round(float(legal_host.area) * 0.70, 3)
        source = SourceMass(
            name="authored_notch_legal_csg",
            footprint=authored_notch,
            volumes=(
                SourceVolume(
                    "recursive_primary",
                    authored_notch,
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            metadata={"geometry_program_bridge_evidence": {
                "program_hash": "notch-program",
                "geometry_hash": "notch-geometry",
            }},
        )

        stacked = materialize_floorwise_legal_source(
            source,
            legal_sections=(legal_host,),
            target_plan_coverage=0.70,
            floor_capacity_plan_hash="irregular-csg-plan",
            target_floor_areas_m2=(target_area,),
        )

        self.assertIsNotNone(stacked)
        assert stacked is not None
        occupied = unary_union([
            volume.footprint for volume in stacked.volumes
        ])
        self.assertTrue(legal_host.buffer(1e-7).covers(occupied))
        self.assertAlmostEqual(occupied.area, target_area, delta=1e-5)
        floor = stacked.metadata["floorwise_legal_matrix_stack"]["floors"][0]
        self.assertGreater(floor["legal_csg_clip_area_m2"], 0.0)
        self.assertEqual(len(floor["matrix4"]), 4)

    def test_replay_ring_transport_preserves_true_short_non_collinear_corner(self):
        from design.maas.geometry_language.replay_ring_transport import (
            normalize_replay_polygon,
        )

        true_short_corner = Polygon((
            (0.0, 0.0),
            (4.0, 0.0),
            (4.0, 4.0),
            (3.999995, 4.000005),
            (0.0, 4.0),
        ))

        normalized = normalize_replay_polygon(true_short_corner)

        self.assertEqual(
            tuple(normalized.exterior.coords)[:-1],
            tuple(true_short_corner.exterior.coords)[:-1],
        )
        self.assertEqual(
            normalized.symmetric_difference(true_short_corner).area,
            0.0,
        )

    def test_replay_ring_transport_is_subset_safe_and_cyclic_deterministic(self):
        from design.maas.geometry_language.replay_ring_transport import (
            normalize_replay_polygon,
        )

        shallow_inward_notch = (
            (2.0, 3.9999995),
            (0.0, 4.0),
            (0.0, 0.0),
            (4.0, 0.0),
            (4.0, 4.0),
            (2.000006, 4.0),
        )
        normalized_payloads = []
        for shift in range(len(shallow_inward_notch)):
            rotated = (
                shallow_inward_notch[shift:]
                + shallow_inward_notch[:shift]
            )
            canonical = orient(Polygon(rotated), sign=1.0)

            normalized = normalize_replay_polygon(canonical)

            self.assertTrue(
                canonical.covers(normalized),
                canonical.difference(normalized).wkt,
            )
            self.assertLessEqual(
                normalized.symmetric_difference(canonical).area,
                1e-6,
            )
            normalized_payloads.append(normalized.wkb_hex)
        self.assertEqual(len(set(normalized_payloads)), 1)
        self.assertEqual(
            len(tuple(normalized.exterior.coords)) - 1,
            5,
        )

    def test_floorwise_replay_proves_serialized_payload_without_expansion(self):
        from design.maas.geometry_language.replay_ring_transport import (
            replay_polygon_origin,
        )
        from design.maas.geometry_language.source_bridge import (
            floorwise_source_to_geometry_program,
        )

        exterior = (
            (2.0, 3.9999995),
            (0.0, 4.0),
            (0.0, 0.0),
            (4.0, 0.0),
            (4.0, 4.0),
            (2.000006, 4.0),
        )
        hole = (
            (1.0, 1.0),
            (1.0, 3.0),
            (3.0, 3.0),
            (3.0, 1.0),
        )
        serialized_payloads = []
        precision_modes = set()
        for shift in range(len(exterior)):
            rotated = exterior[shift:] + exterior[:shift]
            footprint = Polygon(rotated, holes=[hole])
            source = SourceMass(
                name=f"rounded-replay-proof-{shift}",
                footprint=footprint,
                volumes=(
                    SourceVolume(
                        "main",
                        footprint,
                        0.0,
                        1.0,
                        "floorwise_legal_matrix4",
                    ),
                ),
                metadata={"floorwise_legal_matrix_stack": {
                    "status": "materialized",
                    "floor_capacity_plan_hash": "rounded-proof",
                    "floors": [{"matrix4": [
                        [1.0, 0.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0, 0.0],
                        [0.0, 0.0, 1.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ]}],
                }},
            )

            program = floorwise_source_to_geometry_program(
                source,
                height_m=3.0,
            )

            primitive = next(
                node
                for node in program.nodes
                if node.operator == "extruded_polygon"
            )
            local_payload = Polygon(
                primitive.parameters["points"],
                holes=primitive.parameters["holes"],
            )
            canonical = orient(footprint, sign=1.0)
            replay_origin = replay_polygon_origin(footprint)
            local_reference = translate(
                canonical,
                xoff=-replay_origin[0],
                yoff=-replay_origin[1],
            )
            self.assertTrue(local_payload.is_valid)
            self.assertEqual(len(local_payload.interiors), 1)
            self.assertTrue(local_payload.exterior.is_ccw)
            self.assertTrue(all(
                not interior.is_ccw
                for interior in local_payload.interiors
            ))
            self.assertTrue(local_reference.covers(local_payload))
            self.assertLessEqual(
                abs(float(local_payload.area) - float(local_reference.area)),
                1e-6,
            )
            self.assertLessEqual(
                local_payload.symmetric_difference(local_reference).area,
                1e-6,
            )
            serialized_payloads.append((
                tuple(tuple(point) for point in primitive.parameters["points"]),
                tuple(
                    tuple(tuple(point) for point in ring)
                    for ring in primitive.parameters["holes"]
                ),
            ))
            precision_modes.add(
                primitive.provenance["ring_transport_precision"]
            )
        self.assertEqual(len(set(serialized_payloads)), 1)
        self.assertEqual(precision_modes, {"full_precision_fallback"})

    def test_replay_ring_transport_proves_two_hole_fallback_in_local_frame(self):
        from design.maas.geometry_language.replay_ring_transport import (
            replay_polygon_origin,
            replay_polygon_point_payload,
        )

        exterior = (
            (2.0, 3.9999995),
            (0.0, 4.0),
            (0.0, 0.0),
            (4.0, 0.0),
            (4.0, 4.0),
            (2.000006, 4.0),
        )
        holes = (
            (
                (1.0, 1.0),
                (1.0, 3.0),
                (3.0, 3.0),
                (3.0, 1.0),
            ),
            (
                (0.2, 0.2),
                (0.2, 0.4),
                (0.4, 0.4),
                (0.4, 0.2),
            ),
        )
        serialized_payloads = []
        for shift in range(len(exterior)):
            polygon = orient(
                Polygon(
                    exterior[shift:] + exterior[:shift],
                    holes=holes,
                ),
                sign=1.0,
            )
            self.assertTrue(polygon.is_valid)
            origin = replay_polygon_origin(polygon)

            points, transported_holes, precision_mode = (
                replay_polygon_point_payload(
                    polygon,
                    xoff=origin[0],
                    yoff=origin[1],
                )
            )

            local_payload = Polygon(points, holes=transported_holes)
            local_reference = translate(
                polygon,
                xoff=-origin[0],
                yoff=-origin[1],
            )
            self.assertTrue(local_payload.is_valid)
            self.assertEqual(len(local_payload.interiors), 2)
            self.assertTrue(local_payload.exterior.is_ccw)
            self.assertTrue(all(
                not interior.is_ccw
                for interior in local_payload.interiors
            ))
            self.assertTrue(local_reference.covers(local_payload))
            self.assertLessEqual(
                local_reference.symmetric_difference(local_payload).area,
                1e-6,
            )
            self.assertEqual(
                precision_mode,
                "full_precision_fallback",
            )
            serialized_payloads.append((
                tuple(tuple(point) for point in points),
                tuple(
                    tuple(tuple(point) for point in ring)
                    for ring in transported_holes
                ),
            ))
        self.assertEqual(len(set(serialized_payloads)), 1)

    def test_floorwise_replay_compacts_only_proven_noisy_breakpoints_without_rekeying_authorities(self):
        from design.maas.geometry_language.replay_ring_transport import (
            replay_polygon_origin,
        )
        from design.maas.geometry_language.source_bridge import (
            floorwise_source_to_geometry_program,
            source_surface_payload_hash,
            source_volume_payload_hash,
        )

        noisy_clockwise = orient(
            Polygon(
                (
                    (0.0, 0.0),
                    (2.0, 0.0),
                    (2.0, 0.0),
                    (2.000001, 0.0),
                    (4.0, 0.0),
                    (4.0, 3.99998),
                    (3.99998, 4.0),
                    (2.5, 4.0),
                    (2.5, 3.995),
                    (1.5, 3.995),
                    (1.5, 4.0),
                    (0.0, 4.0),
                ),
                holes=[(
                    (1.0, 1.0),
                    (1.0, 3.0),
                    (3.0, 3.0),
                    (3.0, 1.0),
                )],
            ),
            sign=-1.0,
        )
        visual_surface = SourceSurface(
            role="certified_visual",
            volume_role="main",
            verb="exact_loft",
            surface_type="profiled_recursive_solid_mesh",
            vertices_m=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            semantic_patch_id="main:certified-visual",
        )
        source = SourceMass(
            name="replay-noisy-breakpoint",
            footprint=noisy_clockwise,
            volumes=(
                SourceVolume(
                    "main",
                    noisy_clockwise,
                    0.0,
                    1.0,
                    "floorwise_legal_matrix4",
                ),
            ),
            surfaces=(visual_surface,),
            metadata={"floorwise_legal_matrix_stack": {
                "status": "materialized",
                "floor_capacity_plan_hash": "c" * 64,
                "legal_floor_field_hash": "l" * 64,
                "visual_hash": "v" * 64,
                "geometry_hash": "g" * 64,
                "floors": [{"matrix4": [
                    [1.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 1.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ]}],
            }},
        )
        volume_hash = source_volume_payload_hash(source.volumes)
        visual_hash = source_surface_payload_hash(source.surfaces)

        replay_program = floorwise_source_to_geometry_program(
            source,
            height_m=3.0,
        )
        replay_compilation = compile_geometry_program(replay_program)

        self.assertEqual(
            compilation_gate(replay_compilation),
            (),
            compilation_gate(replay_compilation),
        )
        primitive = next(
            node
            for node in replay_program.nodes
            if node.operator == "extruded_polygon"
        )
        replayed_local_plan = Polygon(
            primitive.parameters["points"],
            holes=primitive.parameters["holes"],
        )
        replay_origin = replay_polygon_origin(noisy_clockwise)
        source_local_plan = translate(
            noisy_clockwise,
            xoff=-replay_origin[0],
            yoff=-replay_origin[1],
        )
        self.assertTrue(replayed_local_plan.exterior.is_ccw)
        self.assertTrue(all(
            not interior.is_ccw
            for interior in replayed_local_plan.interiors
        ))
        replayed_world_points = {
            (
                round(float(point[0]) + replay_origin[0], 8),
                round(float(point[1]) + replay_origin[1], 8),
            )
            for point in primitive.parameters["points"]
        }
        self.assertIn((4.0, 3.99998), replayed_world_points)
        self.assertIn((3.99998, 4.0), replayed_world_points)
        self.assertIn(
            primitive.provenance["ring_transport_precision"],
            {"decimal_7", "full_precision_fallback"},
        )
        self.assertLessEqual(
            abs(float(replayed_local_plan.area) - float(source_local_plan.area)),
            1e-6,
        )
        self.assertLessEqual(
            replayed_local_plan.symmetric_difference(source_local_plan).area,
            1e-6,
        )
        self.assertTrue(source_local_plan.covers(replayed_local_plan))
        legal_host = box(-1.0, -1.0, 5.0, 5.0)
        replayed_world_plan = translate(
            replayed_local_plan,
            xoff=replay_origin[0],
            yoff=replay_origin[1],
        )
        self.assertTrue(legal_host.covers(replayed_world_plan))
        self.assertEqual(
            replay_program.metadata["floorwise_projection"][
                "floor_capacity_plan_hash"
            ],
            "c" * 64,
        )
        self.assertEqual(
            source.metadata["floorwise_legal_matrix_stack"][
                "legal_floor_field_hash"
            ],
            "l" * 64,
        )
        self.assertEqual(
            source.metadata["floorwise_legal_matrix_stack"]["visual_hash"],
            "v" * 64,
        )
        self.assertEqual(source_volume_payload_hash(source.volumes), volume_hash)
        self.assertEqual(source_surface_payload_hash(source.surfaces), visual_hash)

    def test_real_pnu_grid_replay_normalizes_only_sub_tolerance_sliver_vertices(self):
        import json

        from shapely.geometry import shape

        from design.maas.book_language.candidate_generation import (
            _agent_mutated_seeds,
        )
        from design.maas.book_language.program_catalog import PROGRAMS
        from design.maas.book_language.registry import (
            build_book_language_registry,
        )
        from design.maas.geometry_language import (
            GeometryProgram,
            apply_book_projection_to_geometry_program,
            compile_geometry_program_to_source_mass,
        )
        from design.maas.geometry_language.source_bridge import (
            floorwise_source_to_geometry_program,
            materialize_floorwise_legal_source,
        )
        from design.maas.program_massing import (
            book_sentence_variants,
            compose_program_with_book_operations,
        )

        legal_sections = tuple(shape({
            "type": "Polygon",
            "coordinates": coordinates,
        }) for coordinates in (
            [[
                [19.209301786660244, 10.303196462622152],
                [7.952368958284199, 4.076129022809751],
                [4.463835566056591, 10.370785636863394],
                [4.0776683608121385, 11.067550186502613],
                [15.327914636438544, 17.308309178434918],
                [19.209301786660244, 10.303196462622152],
            ]],
            [[
                [19.209301786660244, 10.303196462622152],
                [7.952368958284199, 4.076129022809751],
                [4.463835566056591, 10.370785636863394],
                [4.0776683608121385, 11.067550186502613],
                [15.327914636438544, 17.308309178434918],
                [19.209301786660244, 10.303196462622152],
            ]],
            [[
                [19.209301786660244, 10.303196462622152],
                [7.952368958284199, 4.076129022809751],
                [5.099797816884418, 9.223265020497559],
                [16.41123368811874, 15.353139088336144],
                [19.209301786660244, 10.303196462622152],
            ]],
            [[
                [19.209301786660244, 10.303196462622152],
                [7.952368958284199, 4.076129022809751],
                [6.016642466400299, 7.568924474412199],
                [17.26653809635558, 13.809488956529954],
                [19.209301786660244, 10.303196462622152],
            ]],
        ))
        source_seed = _agent_mutated_seeds(
            PROGRAMS[0][1],
            None,
            universal_variation_pages=(0,),
        )[6]
        payload = next(
            note.split("=", 1)[1]
            for note in source_seed.notes
            if note.startswith("geometry_program_payload=")
        )
        grid_program = GeometryProgram.from_dict(json.loads(payload))
        bend = next(
            principle
            for principle in build_book_language_registry()["principles"]
            if principle["principle_id"] == "book:operative:bend"
        )
        operations = book_sentence_variants(
            bend["execution_verbs"],
            count=3,
        )[1]
        sequence = compose_program_with_book_operations(
            source_seed,
            operations,
            base_volume_label="3/8",
            orientation="vertical",
        )
        projected = apply_book_projection_to_geometry_program(
            grid_program,
            sequence,
        )
        source = compile_geometry_program_to_source_mass(
            projected,
            legal_sections[0],
            upper_host=legal_sections[-1],
            upper_fit_strength=0.0,
            target_plan_area=92.638,
            name=projected.name,
            volume_role="recursive-primary",
            max_volume_bands=4,
        )
        self.assertIsNotNone(source)

        materialized = materialize_floorwise_legal_source(
            source,
            legal_sections=legal_sections,
            target_plan_coverage=0.9,
            floor_capacity_plan_hash="real-pnu-grid-sliver-regression",
            target_floor_areas_m2=(92.638, 92.638, 67.49, 46.324),
        )

        self.assertIsNotNone(materialized)
        assert materialized is not None
        replay = compile_geometry_program(
            floorwise_source_to_geometry_program(
                materialized,
                height_m=14.0,
            )
        )
        self.assertFalse(compilation_gate(replay), compilation_gate(replay))
        for floor_index, (legal, target) in enumerate(zip(
            legal_sections,
            (92.638, 92.638, 67.49, 46.324),
        )):
            band = unary_union(tuple(
                volume.footprint
                for volume in materialized.volumes
                if round(float(volume.bottom_fraction) * 4) == floor_index
            ))
            self.assertTrue(legal.buffer(1e-7).covers(band))
            self.assertAlmostEqual(float(band.area), target, places=6)
        stack = materialized.metadata["floorwise_legal_matrix_stack"]
        self.assertTrue(all(len(floor["matrix4"]) == 4 for floor in stack["floors"]))
        self.assertGreater(
            max(
                len(part.exterior.coords)
                for volume in materialized.volumes
                for part in (
                    tuple(volume.footprint.geoms)
                    if hasattr(volume.footprint, "geoms")
                    else (volume.footprint,)
                )
            ),
            8,
        )
        self.assertEqual(len(floor["matrix4"]), 4)

    def test_v18_legal_field_materializes_three_current_codex_families(self):
        """Current authored families must survive the real four-floor field."""
        import json

        from shapely.geometry import shape

        from design.maas.geometry_language import GeometryProgram
        from design.maas.geometry_language.source_bridge import (
            compile_geometry_program_to_source_mass,
            materialize_floorwise_legal_source,
        )

        manifest_path = (
            Path(__file__).resolve().parents[2]
            / ".superpowers"
            / "sdd"
            / "2026-08-05-llm-authored-diverse-legal-mass"
            / "codex-mass-manifest-v1.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        programs = {
            row["name"]: GeometryProgram.from_dict(row)
            for row in manifest["programs"]
        }
        family_names = (
            "codex_split_wings_sky_bridge",
            "codex_tapered_oblique_prism",
            "codex_faceted_cut_corner_prism",
        )
        legal_sections = tuple(shape({
            "type": "Polygon",
            "coordinates": coordinates,
        }) for coordinates in (
            [[[19.209301786660244, 10.303196462622152], [7.952368958284199, 4.076129022809751], [4.463835566056591, 10.370785636863394], [4.0776683608121385, 11.067550186502613], [15.327914636438544, 17.308309178434918], [19.209301786660244, 10.303196462622152]]],
            [[[19.209301786660244, 10.303196462622152], [7.952368958284199, 4.076129022809751], [4.463835566056591, 10.370785636863394], [4.0776683608121385, 11.067550186502613], [15.327914636438544, 17.308309178434918], [19.209301786660244, 10.303196462622152]]],
            [[[19.209301786660244, 10.303196462622152], [7.952368958284199, 4.076129022809751], [5.099797816884418, 9.223265020497559], [16.41123368811874, 15.353139088336144], [19.209301786660244, 10.303196462622152]]],
            [[[19.209301786660244, 10.303196462622152], [7.952368958284199, 4.076129022809751], [6.016642466400299, 7.568924474412199], [17.26653809635558, 13.809488956529954], [19.209301786660244, 10.303196462622152]]],
        ))
        targets = (92.638, 92.638, 67.49, 46.324)

        for family_name in family_names:
            with self.subTest(family=family_name):
                source = compile_geometry_program_to_source_mass(
                    programs[family_name],
                    legal_sections[0],
                    upper_host=legal_sections[-1],
                    upper_fit_strength=0.0,
                    target_plan_area=targets[0],
                    name=family_name,
                    volume_role="recursive-primary",
                    max_volume_bands=4,
                )
                self.assertIsNotNone(source)
                assert source is not None
                source = replace(source, metadata={
                    **source.metadata,
                    "candidate_floor_context": {
                        "height_m": 14.0,
                        "effective_height_m": 14.0,
                        "floors": 4,
                        "floor_top_heights_m": [3.5, 7.0, 10.5, 14.0],
                    },
                })
                terminal_failures = []
                materialized = materialize_floorwise_legal_source(
                    source,
                    legal_sections=legal_sections,
                    target_plan_coverage=0.9,
                    floor_capacity_plan_hash="v18-three-family-regression",
                    target_floor_areas_m2=targets,
                    terminal_failure_sink=terminal_failures,
                )
                self.assertIsNotNone(materialized, terminal_failures)

    def test_floorwise_capacity_budget_preserves_distinct_authored_vertical_profiles(self):
        """A capacity target must not rewrite different AST profiles as one step stack."""
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )
        from design.maas.program_massing.morphology import (
            intrinsic_silhouette_distance,
        )

        flat = SourceMass(
            name="flat_authored_profile",
            footprint=box(0.0, 0.0, 10.0, 10.0),
            volumes=(
                SourceVolume(
                    "recursive_primary",
                    box(0.0, 0.0, 10.0, 10.0),
                    0.0,
                    1.0,
                    "geometry_program",
                ),
            ),
            metadata={"geometry_program_bridge_evidence": {
                "program_hash": "flat-program",
                "geometry_hash": "flat-geometry",
            }},
        )
        tapered = SourceMass(
            name="tapered_authored_profile",
            footprint=box(0.0, 0.0, 10.0, 10.0),
            volumes=(
                SourceVolume(
                    "recursive_primary",
                    box(0.0, 0.0, 10.0, 10.0),
                    0.0,
                    0.5,
                    "geometry_program",
                ),
                SourceVolume(
                    "recursive_primary",
                    box(2.5, 2.5, 7.5, 7.5),
                    0.5,
                    1.0,
                    "geometry_program",
                ),
            ),
            metadata={"geometry_program_bridge_evidence": {
                "program_hash": "tapered-program",
                "geometry_hash": "tapered-geometry",
            }},
        )
        legal_sections = (box(0.0, 0.0, 10.0, 10.0),) * 4
        target_areas = (90.0, 90.0, 60.0, 40.0)

        flat_stack = materialize_floorwise_legal_source(
            flat,
            legal_sections=legal_sections,
            target_plan_coverage=0.90,
            target_floor_areas_m2=target_areas,
        )
        tapered_stack = materialize_floorwise_legal_source(
            tapered,
            legal_sections=legal_sections,
            target_plan_coverage=0.90,
            target_floor_areas_m2=target_areas,
        )

        self.assertIsNotNone(flat_stack)
        self.assertIsNotNone(tapered_stack)
        assert flat_stack is not None and tapered_stack is not None
        self.assertAlmostEqual(
            sum(volume.footprint.area for volume in flat_stack.volumes),
            sum(target_areas),
            delta=0.1,
        )
        self.assertAlmostEqual(
            sum(volume.footprint.area for volume in tapered_stack.volumes),
            sum(target_areas),
            delta=0.1,
        )
        self.assertNotEqual(
            [round(volume.footprint.area, 2) for volume in flat_stack.volumes],
            [round(volume.footprint.area, 2) for volume in tapered_stack.volumes],
        )
        self.assertGreater(
            intrinsic_silhouette_distance(flat_stack, tapered_stack),
            0.0,
        )

    def test_floorwise_legal_stack_preserves_relative_upper_floor_offset(self):
        """Floor Matrix4 fitting must not recenter authored shift into a twin."""
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )
        from design.maas.program_massing.morphology import (
            DEFAULT_NOVELTY_POLICY,
            intrinsic_silhouette_distance,
        )

        lower = box(0.0, 0.0, 10.0, 6.0)

        def source(name, upper):
            return SourceMass(
                name=name,
                footprint=lower,
                upper_footprint=upper,
                volumes=(
                    SourceVolume("main", lower, 0.0, 0.5, "base"),
                    SourceVolume("main", upper, 0.5, 1.0, "shift"),
                ),
                metadata={"geometry_program_bridge_evidence": {
                    "status": "materialized",
                    "program_hash": name,
                    "geometry_hash": name,
                }},
            )

        centered = source("centered", lower)
        shifted = source("shifted", box(4.0, 0.0, 14.0, 6.0))
        legal_sections = (box(-10.0, -10.0, 20.0, 20.0),) * 2
        centered_stack = materialize_floorwise_legal_source(
            centered,
            legal_sections=legal_sections,
            target_plan_coverage=0.5,
            target_floor_areas_m2=(60.0, 60.0),
        )
        shifted_stack = materialize_floorwise_legal_source(
            shifted,
            legal_sections=legal_sections,
            target_plan_coverage=0.5,
            target_floor_areas_m2=(60.0, 60.0),
        )

        self.assertIsNotNone(centered_stack)
        self.assertIsNotNone(shifted_stack)
        assert centered_stack is not None and shifted_stack is not None
        strict_stack = shifted_stack.metadata["floorwise_legal_matrix_stack"]
        self.assertFalse(strict_stack["pose_fallback_used"])
        self.assertEqual(
            strict_stack["pose_fit"],
            "single_global_rotation_translation_with_floor_relative_pose_preserved",
        )
        floor_matrices = [
            floor["matrix4"]
            for floor in strict_stack["floors"]
        ]
        self.assertEqual(
            [
                [round(float(floor_matrices[0][row][column]), 9) for column in range(2)]
                for row in range(2)
            ],
            [
                [round(float(floor_matrices[1][row][column]), 9) for column in range(2)]
                for row in range(2)
            ],
        )
        lower_center, upper_center = [
            volume.footprint.centroid for volume in shifted_stack.volumes
        ]
        self.assertAlmostEqual(upper_center.x - lower_center.x, 4.0, delta=0.01)
        self.assertGreater(
            intrinsic_silhouette_distance(centered_stack, shifted_stack),
            DEFAULT_NOVELTY_POLICY.visual_silhouette_repeat,
        )

    def test_floorwise_legal_stack_uses_one_plan_linear_block_for_shrinking_sections(self):
        """A v16-like upper legal contraction must not rewrite floor pose."""
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        source = _authored_profiled_box_source(
            "v16_shrinking_legal_sections",
        )

        stacked = materialize_floorwise_legal_source(
            source,
            legal_sections=(
                box(-10.0, -10.0, 10.0, 10.0),
                box(-8.0, -8.0, 8.0, 8.0),
                box(-6.0, -6.0, 6.0, 6.0),
                box(-5.0, -5.0, 5.0, 5.0),
            ),
            target_plan_coverage=0.90,
            target_floor_areas_m2=(90.0, 80.0, 70.0, 60.0),
        )

        self.assertIsNotNone(stacked)
        assert stacked is not None
        stack = stacked.metadata["floorwise_legal_matrix_stack"]
        self.assertFalse(stack["pose_fallback_used"])
        linear_blocks = [
            tuple(
                round(float(matrix[row][column]), 9)
                for row in range(2)
                for column in range(2)
            )
            for matrix in (
                floor["matrix4"] for floor in stack["floors"]
            )
        ]
        self.assertEqual(len(set(linear_blocks)), 1)
        self.assertTrue(all(
            floor["achieved_plan_area_m2"]
            <= floor["legal_plan_area_m2"] + 1e-6
            for floor in stack["floors"]
        ))
        self.assertGreaterEqual(
            sum(
                floor["achieved_plan_area_m2"]
                for floor in stack["floors"]
            ),
            sum((90.0, 80.0, 70.0, 60.0)) * 0.90,
        )

    def test_floorwise_legal_stack_never_reflows_authored_upper_pose(self):
        """A tight upper host may reduce area, but cannot recenter the AST floor."""
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        lower = box(0.0, 0.0, 10.0, 6.0)
        upper = box(12.0, 0.0, 22.0, 6.0)
        source = SourceMass(
            name="fixed_pose_tight_upper",
            footprint=lower,
            upper_footprint=upper,
            volumes=(
                SourceVolume("main", lower, 0.0, 0.5, "base"),
                SourceVolume("main", upper, 0.5, 1.0, "shift"),
            ),
            metadata={"geometry_program_bridge_evidence": {
                "status": "materialized",
                "program_hash": "fixed-pose-program",
                "geometry_hash": "fixed-pose-geometry",
            }},
        )
        legal_sections = (box(-10.0, -10.0, 20.0, 20.0),) * 2

        stacked = materialize_floorwise_legal_source(
            source,
            legal_sections=legal_sections,
            target_plan_coverage=0.5,
            target_floor_areas_m2=(60.0, 60.0),
        )

        self.assertIsNotNone(stacked)
        assert stacked is not None
        stack = stacked.metadata["floorwise_legal_matrix_stack"]
        self.assertFalse(stack["pose_fallback_used"])
        self.assertEqual(
            stack["pose_fit"],
            "single_global_rotation_translation_with_floor_relative_pose_preserved",
        )
        lower_center, upper_center = [
            volume.footprint.centroid for volume in stacked.volumes
        ]
        self.assertAlmostEqual(upper_center.x - lower_center.x, 12.0, delta=0.01)
        self.assertLess(
            stack["floors"][1]["achieved_plan_area_m2"],
            stack["floors"][1]["target_plan_area_m2"],
        )

    def test_floorwise_legal_stack_samples_exact_authored_mesh_sections(self):
        """Floor plates must not substitute a coarse volume proxy for the AST mesh."""
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )
        from design.maas.program_massing.morphology import (
            DEFAULT_NOVELTY_POLICY,
            intrinsic_silhouette_distance,
        )

        def authored_source(name: str, top_x_offset: float) -> SourceMass:
            # Both sources expose the same conservative proxy. Only the
            # closed authored mesh records the upper-level shift.
            return _authored_profiled_box_source(
                name,
                top_x_offset=top_x_offset,
            )

        centered = materialize_floorwise_legal_source(
            authored_source("centered_mesh", 0.0),
            legal_sections=(box(-20.0, -20.0, 20.0, 20.0),) * 2,
            target_plan_coverage=0.5,
            target_floor_areas_m2=(100.0, 100.0),
        )
        shifted = materialize_floorwise_legal_source(
            authored_source("shifted_mesh", 4.0),
            legal_sections=(box(-20.0, -20.0, 20.0, 20.0),) * 2,
            target_plan_coverage=0.5,
            target_floor_areas_m2=(100.0, 100.0),
        )

        self.assertIsNotNone(centered)
        self.assertIsNotNone(shifted)
        assert centered is not None and shifted is not None
        shifted_stack = shifted.metadata["floorwise_legal_matrix_stack"]
        self.assertEqual(
            shifted_stack["pose_fit"],
            "single_global_rotation_translation_with_floor_relative_pose_preserved",
        )
        self.assertFalse(shifted_stack["pose_fallback_used"])
        shifted_centers = [
            volume.footprint.centroid.x for volume in shifted.volumes
        ]
        self.assertGreater(shifted_centers[1] - shifted_centers[0], 1.5)
        self.assertGreater(
            intrinsic_silhouette_distance(centered, shifted),
            DEFAULT_NOVELTY_POLICY.visual_silhouette_repeat,
        )

    def test_exact_authored_section_uses_closed_solid_terrace_convention(self):
        """A coplanar terrace must not union the footprints on both sides."""
        import manifold3d as m3d

        from design.maas.geometry_language.source_bridge import (
            _exact_authored_mesh_section,
        )

        lower = m3d.Manifold.cube((10.0, 10.0, 0.625), center=True).translate(
            (0.0, 0.0, 0.3125)
        )
        upper = m3d.Manifold.cube((6.0, 6.0, 0.375), center=True).translate(
            (0.0, 0.0, 0.8125)
        )
        mesh = (lower + upper).to_mesh64()
        vertices = tuple(
            tuple(float(value) for value in row[:3])
            for row in mesh.vert_properties
        )
        triangles = tuple(
            tuple(int(index) for index in row)
            for row in mesh.tri_verts
        )
        surfaces = tuple(
            SourceSurface(
                role=f"terrace-{index}",
                volume_role="recursive-primary",
                verb="geometry_program",
                surface_type="profiled_recursive_solid_mesh",
                vertices_m=tuple(vertices[vertex] for vertex in triangle),
            )
            for index, triangle in enumerate(triangles)
        )
        source = SourceMass(
            name="coplanar-terrace",
            footprint=box(-5.0, -5.0, 5.0, 5.0),
            upper_footprint=box(-3.0, -3.0, 3.0, 3.0),
            volumes=(SourceVolume(
                "recursive-primary",
                box(-5.0, -5.0, 5.0, 5.0),
                0.0,
                1.0,
                "geometry_program",
            ),),
            surfaces=surfaces,
            metadata={"geometry_program_bridge_evidence": {
                "raw_mesh_triangle_count": len(triangles),
                "exported_surface_count": len(triangles),
            }},
        )

        closed_solid_section = _exact_authored_mesh_section(
            source,
            height_fraction=0.625,
        )
        ambiguous_segment_section = _mesh_section_polygon(
            vertices,
            triangles,
            0.625,
        )

        self.assertIsNotNone(closed_solid_section)
        self.assertIsNotNone(ambiguous_segment_section)
        assert closed_solid_section is not None
        assert ambiguous_segment_section is not None
        self.assertAlmostEqual(float(closed_solid_section.area), 36.0, places=6)
        self.assertAlmostEqual(float(ambiguous_segment_section.area), 100.0, places=6)

    def test_floorwise_visual_projection_preserves_authored_mesh(self):
        """Erasing projected mesh surfaces must not collapse authored shift twins."""
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )
        legal_sections = (box(-20.0, -20.0, 20.0, 20.0),) * 2
        centered = materialize_floorwise_legal_source(
            _authored_profiled_box_source("centered_visual_mesh"),
            legal_sections=legal_sections,
            target_plan_coverage=0.5,
            floor_capacity_plan_hash="capacity-visual-mesh",
            target_floor_areas_m2=(100.0, 100.0),
        )
        shifted = materialize_floorwise_legal_source(
            _authored_profiled_box_source(
                "shifted_visual_mesh",
                top_x_offset=4.0,
            ),
            legal_sections=legal_sections,
            target_plan_coverage=0.5,
            floor_capacity_plan_hash="capacity-visual-mesh",
            target_floor_areas_m2=(100.0, 100.0),
        )

        self.assertIsNotNone(centered)
        self.assertIsNotNone(shifted)
        assert centered is not None and shifted is not None
        centered_certificate = centered.metadata["floorwise_visual_projection"]
        shifted_certificate = shifted.metadata["floorwise_visual_projection"]
        self.assertTrue(centered_certificate["hard_pass"], centered_certificate)
        self.assertTrue(shifted_certificate["hard_pass"], shifted_certificate)
        self.assertEqual(centered_certificate["status"], "certified")
        self.assertEqual(shifted_certificate["status"], "certified")
        self.assertFalse(centered_certificate["visible_step_fallback"])
        self.assertFalse(shifted_certificate["visible_step_fallback"])
        self.assertTrue(centered.surfaces)
        self.assertTrue(shifted.surfaces)
        self.assertNotEqual(
            centered_certificate["visual_hash"],
            shifted_certificate["visual_hash"],
        )
        self.assertAlmostEqual(
            sum(volume.footprint.area for volume in centered.volumes),
            200.0,
            delta=0.1,
        )
        self.assertAlmostEqual(
            sum(volume.footprint.area for volume in shifted.volumes),
            200.0,
            delta=0.1,
        )

    def test_profiled_clip_accepts_submicron_normalized_z_transport_noise(self):
        from design.maas.geometry_language.affine_matrix import identity_matrix4
        from design.maas.geometry_language.floorwise_profiled_legal_clip import (
            _source_world_matrix_field_manifold,
        )

        authored = _authored_profiled_box_source("submicron-z-transport")
        surfaces = tuple(
            replace(
                surface,
                vertices_m=tuple(
                    (
                        x,
                        y,
                        -4e-7 if z == 0.0 else 1.0 + 4e-7,
                    )
                    for x, y, z in surface.vertices_m
                ),
            )
            for surface in authored.surfaces
        )
        source = replace(authored, surfaces=surfaces)

        solid = _source_world_matrix_field_manifold(
            source,
            surfaces,
            (identity_matrix4(),),
        )

        self.assertIn("NoError", str(solid.status()))
        self.assertFalse(solid.is_empty())

    def test_floorwise_profiled_legal_clip_preserves_real_oblique_skin(self):
        """The legal clip must preserve measured slope, not relabel a prism."""
        from math import sqrt

        from design.maas.geometry_language.compiler import (
            CompilationResult,
            revalidate_compilation_mesh,
        )
        from design.maas.geometry_language.ast import GeometryProgram
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        legal = box(-5.0, -5.0, 5.0, 5.0)
        authored = _authored_profiled_box_source(
            "profiled_legal_clip_oblique",
            top_x_offset=12.0,
        )
        stacked = materialize_floorwise_legal_source(
            authored,
            legal_sections=(legal, legal),
            target_plan_coverage=0.95,
            floor_capacity_plan_hash="profiled-legal-clip-capacity",
            target_floor_areas_m2=(100.0, 100.0),
        )

        self.assertIsNotNone(stacked)
        assert stacked is not None
        certificate = stacked.metadata["floorwise_visual_projection"]
        self.assertEqual(
            certificate["certification_mode"],
            "floorwise_csg_section_loft",
        )
        self.assertEqual(
            certificate["visible_geometry_operation"],
            "exact_legal_section_profile_loft",
        )
        self.assertFalse(certificate["visible_step_fallback"])
        self.assertEqual(
            certificate["floor_capacity_plan_hash"],
            "profiled-legal-clip-capacity",
        )
        self.assertTrue(certificate["authority_binding_hash"])

        vertex_index = {}
        vertices = []
        triangles = []
        sloped_area = total_area = 0.0
        for surface in stacked.surfaces:
            triangle = []
            scaled = []
            for x, y, z in surface.vertices_m:
                key = (float(x), float(y), float(z))
                if key not in vertex_index:
                    vertex_index[key] = len(vertices)
                    vertices.append(key)
                triangle.append(vertex_index[key])
                scaled.append((float(x), float(y), float(z) * 10.5))
            triangles.append(tuple(triangle))
            left = tuple(
                scaled[1][axis] - scaled[0][axis] for axis in range(3)
            )
            right = tuple(
                scaled[2][axis] - scaled[0][axis] for axis in range(3)
            )
            normal = (
                left[1] * right[2] - left[2] * right[1],
                left[2] * right[0] - left[0] * right[2],
                left[0] * right[1] - left[1] * right[0],
            )
            magnitude = sqrt(sum(value * value for value in normal))
            if magnitude <= 1e-12:
                continue
            area = magnitude / 2.0
            total_area += area
            absolute_z = abs(normal[2]) / magnitude
            if 0.12 < absolute_z < 0.90:
                sloped_area += area
        revalidated = revalidate_compilation_mesh(CompilationResult(
            program=GeometryProgram(
                nodes=(),
                root_id="",
                name="profiled-clip-test",
            ),
            status="compiled",
            vertices=tuple(vertices),
            triangles=tuple(triangles),
        ))
        self.assertEqual(revalidated.status, "compiled")
        self.assertTrue(revalidated.metrics["closed_solid"])
        self.assertTrue(revalidated.metrics["manifold"])
        self.assertEqual(revalidated.metrics["component_count"], 1)
        from design.maas.book_language.final_mesh_floor_evidence import (
            _mesh_section_segments,
        )

        origin = stacked.footprint.centroid
        for normalized_z in (0.25, 0.75):
            segments = _mesh_section_segments(
                tuple(vertices),
                tuple(triangles),
                normalized_z,
            )
            self.assertTrue(segments)
            self.assertTrue(all(
                legal.covers(translate(
                    segment,
                    xoff=float(origin.x),
                    yoff=float(origin.y),
                ))
                for segment in segments
            ))
        # The exact legal-section loft remains a continuous sloped skin. Its
        # role is lawful contraction, so it need not retain the much steeper
        # authored oblique ratio after the legal field removes that pose.
        self.assertGreaterEqual(sloped_area / total_area, 0.01)

        occupied_by_floor = tuple(
            volume.footprint
            for volume in sorted(
                stacked.volumes,
                key=lambda volume: float(volume.bottom_fraction),
            )
        )
        for floor_index in range(2):
            measured = _mesh_section_polygon(
                tuple(vertices),
                tuple(triangles),
                (floor_index + 0.5) / 2.0,
            )
            self.assertIsNotNone(measured)
            assert measured is not None
            measured = translate(
                measured,
                xoff=float(origin.x),
                yoff=float(origin.y),
            )
            self.assertLess(
                measured.symmetric_difference(
                    occupied_by_floor[floor_index],
                ).area,
                1e-6,
            )
        below_seam = _mesh_section_polygon(
            tuple(vertices),
            tuple(triangles),
            0.5 - 1e-6,
        )
        above_seam = _mesh_section_polygon(
            tuple(vertices),
            tuple(triangles),
            0.5 + 1e-6,
        )
        self.assertIsNotNone(below_seam)
        self.assertIsNotNone(above_seam)
        assert below_seam is not None and above_seam is not None
        self.assertLess(
            below_seam.symmetric_difference(above_seam).area,
            1e-3,
        )
        achieved_gfa = sum(
            volume.footprint.area for volume in stacked.volumes
        )
        self.assertGreater(achieved_gfa, 0.0)
        self.assertLessEqual(achieved_gfa, 200.0 + 1e-6)
        repeated = materialize_floorwise_legal_source(
            _authored_profiled_box_source(
                "profiled_legal_clip_oblique",
                top_x_offset=12.0,
            ),
            legal_sections=(legal, legal),
            target_plan_coverage=0.95,
            floor_capacity_plan_hash="profiled-legal-clip-capacity",
            target_floor_areas_m2=(100.0, 100.0),
        )
        self.assertIsNotNone(repeated)
        assert repeated is not None
        repeated_certificate = repeated.metadata["floorwise_visual_projection"]
        self.assertEqual(
            repeated_certificate["exact_surface_payload_hash"],
            certificate["exact_surface_payload_hash"],
        )
        self.assertEqual(
            repeated_certificate["authority_binding_hash"],
            certificate["authority_binding_hash"],
        )
        self.assertEqual(repeated.surfaces, stacked.surfaces)

        from design.maas.geometry_language.floorwise_visual_projection import (
            clip_and_certify_projected_piloti_visual,
        )

        piloti = clip_and_certify_projected_piloti_visual(
            stacked.surfaces,
            certificate,
            void_height_fraction=0.10,
        )
        self.assertIsNotNone(piloti)
        assert piloti is not None
        self.assertNotEqual(
            piloti[1]["exact_surface_payload_hash"],
            certificate["exact_surface_payload_hash"],
        )
        self.assertNotEqual(
            piloti[1]["authority_binding_hash"],
            certificate["authority_binding_hash"],
        )
        self.assertIsNone(
            clip_and_certify_projected_piloti_visual(
                stacked.surfaces,
                certificate,
                void_height_fraction=0.30,
            )
        )

    def test_shrinking_legal_field_uses_continuous_exact_section_loft(self):
        """Legal contraction must not render the capacity bands as steps."""
        from design.maas.geometry_language.ast import GeometryProgram
        from design.maas.geometry_language.compiler import (
            CompilationResult,
            revalidate_compilation_mesh,
        )
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )
        from design.maas.program_massing.competition_gestalt import (
            competition_gestalt_key,
        )

        legal_sections = (
            box(-6.0, -6.0, 6.0, 6.0),
            box(-5.5, -5.5, 5.5, 5.5),
            box(-4.5, -4.5, 4.5, 4.5),
            box(-3.5, -3.5, 3.5, 3.5),
        )
        targets = (90.0, 80.0, 60.0, 40.0)
        base = _authored_profiled_box_source(
            "v19-shrinking-legal-field",
            top_x_offset=12.0,
        )
        authored = replace(base, metadata={
            **base.metadata,
            "candidate_floor_context": {
                "height_m": 14.0,
                "effective_height_m": 14.0,
                "floors": 4,
            },
        })

        materialized = materialize_floorwise_legal_source(
            authored,
            legal_sections=legal_sections,
            target_plan_coverage=0.9,
            floor_capacity_plan_hash="v19-continuous-loft",
            target_floor_areas_m2=targets,
        )

        self.assertIsNotNone(materialized)
        assert materialized is not None
        certificate = materialized.metadata["floorwise_visual_projection"]
        self.assertTrue(certificate["hard_pass"], certificate)
        self.assertEqual(
            certificate["certification_mode"],
            "floorwise_csg_section_loft",
        )
        self.assertFalse(certificate["visible_step_fallback"])
        matrices = tuple(
            tuple(tuple(row) for row in floor["matrix4"])
            for floor in materialized.metadata[
                "floorwise_legal_matrix_stack"
            ]["floors"]
        )
        self.assertEqual(len(set(matrices)), 1)
        vertex_indices = {}
        vertices = []
        triangles = []
        for surface in materialized.surfaces:
            triangle = []
            for vertex in surface.vertices_m:
                point = tuple(float(value) for value in vertex)
                if point not in vertex_indices:
                    vertex_indices[point] = len(vertices)
                    vertices.append(point)
                triangle.append(vertex_indices[point])
            triangles.append(tuple(triangle))
        revalidated = revalidate_compilation_mesh(CompilationResult(
            program=GeometryProgram(nodes=(), root_id="", name="v19-loft"),
            status="compiled",
            vertices=tuple(vertices),
            triangles=tuple(triangles),
        ))
        self.assertEqual(revalidated.status, "compiled")
        self.assertTrue(revalidated.metrics["closed_solid"])
        self.assertTrue(revalidated.metrics["manifold"])
        origin = materialized.footprint.centroid
        for floor_index, legal in enumerate(legal_sections):
            occupied = unary_union(tuple(
                volume.footprint
                for volume in materialized.volumes
                if round(float(volume.bottom_fraction) * 4) == floor_index
            ))
            self.assertTrue(legal.buffer(1e-7).covers(occupied))
            measured = _mesh_section_polygon(
                tuple(vertices),
                tuple(triangles),
                (floor_index + 0.5) / 4.0,
            )
            self.assertIsNotNone(measured)
            assert measured is not None
            measured = translate(
                measured,
                xoff=float(origin.x),
                yoff=float(origin.y),
            )
            self.assertLess(
                measured.symmetric_difference(occupied).area,
                1e-6,
            )
        self.assertFalse(
            competition_gestalt_key(materialized).visible_stepped
        )

    def test_floor_center_numeric_equivalence_preserves_holes_and_islands(self):
        from shapely.geometry import MultiPolygon

        from design.maas.geometry_language.floorwise_profiled_legal_clip import (
            _floor_center_numeric_equivalence,
        )

        expected = box(0.0, 0.0, 10.0, 10.0)
        microscopic_hole = Polygon(
            expected.exterior.coords,
            holes=[box(4.9999999, 4.9999999, 5.0000001, 5.0000001).exterior.coords],
        )
        microscopic_island = MultiPolygon((
            expected,
            box(10.0000001, 0.0, 10.0000002, 0.0000001),
        ))
        hole_match = _floor_center_numeric_equivalence(
            microscopic_hole,
            microscopic_hole,
        )
        island_match = _floor_center_numeric_equivalence(
            microscopic_island,
            microscopic_island,
        )
        self.assertIsNotNone(hole_match)
        self.assertIsNotNone(island_match)
        self.assertTrue(hole_match["hard_pass"])
        self.assertTrue(island_match["hard_pass"])
        self.assertEqual(hole_match["hole_count"], 1)
        self.assertEqual(island_match["component_count"], 2)

        hole_mismatch = _floor_center_numeric_equivalence(
            microscopic_hole,
            expected,
        )
        island_mismatch = _floor_center_numeric_equivalence(
            microscopic_island,
            expected,
        )
        self.assertIsNotNone(hole_mismatch)
        self.assertIsNotNone(island_mismatch)
        self.assertFalse(hole_mismatch["hard_pass"])
        self.assertFalse(island_mismatch["hard_pass"])

    def test_floor_center_numeric_equivalence_rejects_boundary_drift(self):
        from design.maas.geometry_language.floorwise_profiled_legal_clip import (
            _floor_center_numeric_equivalence,
        )

        expected = box(0.0, 0.0, 10.0, 10.0)
        within = _floor_center_numeric_equivalence(
            translate(expected, xoff=0.5e-6),
            expected,
        )
        outside = _floor_center_numeric_equivalence(
            translate(expected, xoff=1.1e-6),
            expected,
        )
        self.assertIsNotNone(within)
        self.assertIsNotNone(outside)
        self.assertTrue(within["hard_pass"])
        self.assertFalse(outside["hard_pass"])
        self.assertGreater(outside["hausdorff_m"], 1e-6)

    def test_floorwise_profiled_legal_clip_accepts_valid_topology_and_rejects_invalid_authority(self):
        """Valid holes/multipart survive; malformed equivalents fail typed."""
        from dataclasses import replace

        from shapely.geometry import MultiPolygon

        from design.maas.geometry_language.floorwise_profiled_legal_clip import (
            clip_profiled_mesh_to_floorwise_legal_solids,
        )
        from design.maas.geometry_language.floorwise_visual_projection import (
            floorwise_authority_binding_hash,
        )
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        legal = box(-5.0, -5.0, 5.0, 5.0)
        legacy_binding_fields = {
            "section_profile_hash": "section",
            "capacity_volume_hash": "capacity",
            "floor_capacity_plan_hash": "plan",
            "matrix4_stack_hash": "matrix",
            "exact_surface_payload_hash": "surface",
            "certification_mode": "floorwise_csg_section_loft",
            "visible_geometry_operation": "exact_legal_section_profile_loft",
            "visible_step_fallback": False,
        }
        self.assertEqual(
            floorwise_authority_binding_hash(**legacy_binding_fields),
            floorwise_authority_binding_hash(
                **legacy_binding_fields,
                authored_program_hash="",
                effective_height_m=0.0,
                verified_profiled_sloped_surface_area=0.0,
                verified_profiled_sloped_surface_ratio=0.0,
                verified_profiled_sloped_surface_hash="",
            ),
        )
        authored = _authored_profiled_box_source(
            "profiled_legal_clip_fail_closed",
            top_x_offset=12.0,
        )
        baseline = materialize_floorwise_legal_source(
            authored,
            legal_sections=(legal, legal),
            target_plan_coverage=0.95,
            floor_capacity_plan_hash="profiled-legal-clip-fail-closed",
            target_floor_areas_m2=(100.0, 100.0),
        )
        self.assertIsNotNone(baseline)
        assert baseline is not None
        stack = baseline.metadata["floorwise_legal_matrix_stack"]
        authority_source = replace(
            authored,
            metadata={
                **authored.metadata,
                "floorwise_legal_matrix_stack": stack,
            },
        )
        matrices = tuple(
            floor["matrix4"]
            for floor in stack["floors"]
        )
        occupied = tuple(
            unary_union([
                volume.footprint
                for volume in baseline.volumes
                if (
                    abs(volume.bottom_fraction - floor_index / 2.0)
                    <= 1e-8
                )
            ])
            for floor_index in range(2)
        )
        direct_baseline = clip_profiled_mesh_to_floorwise_legal_solids(
            authority_source,
            occupied_sections=occupied,
            legal_sections=(legal, legal),
            floor_matrices=matrices,
            capacity_plates=baseline.volumes,
            output_origin=(0.0, 0.0),
        )
        self.assertTrue(
            direct_baseline.certificate.hard_pass,
            direct_baseline.certificate.to_dict(),
        )
        reversed_legal = Polygon(tuple(reversed(legal.exterior.coords)))
        reversed_result = clip_profiled_mesh_to_floorwise_legal_solids(
            replace(
                authority_source,
                surfaces=tuple(reversed(authority_source.surfaces)),
            ),
            occupied_sections=occupied,
            legal_sections=(reversed_legal, reversed_legal),
            floor_matrices=matrices,
            capacity_plates=tuple(reversed(baseline.volumes)),
            output_origin=(0.0, 0.0),
        )
        self.assertTrue(
            reversed_result.certificate.hard_pass,
            reversed_result.certificate.to_dict(),
        )
        self.assertEqual(
            reversed_result.certificate.exact_surface_payload_hash,
            direct_baseline.certificate.exact_surface_payload_hash,
        )
        self.assertEqual(
            reversed_result.certificate.authority_binding_hash,
            direct_baseline.certificate.authority_binding_hash,
        )
        incomplete_authored_export = clip_profiled_mesh_to_floorwise_legal_solids(
            replace(
                authority_source,
                surfaces=(
                    *authority_source.surfaces,
                    SourceSurface(
                        role="unexported_authored_surface",
                        volume_role="recursive_primary",
                        verb="geometry_program",
                        surface_type="authored_non_profiled_surface",
                        vertices_m=(
                            (0.0, 0.0, 0.0),
                            (1.0, 0.0, 0.0),
                            (0.0, 1.0, 0.0),
                        ),
                    ),
                ),
            ),
            occupied_sections=occupied,
            legal_sections=(legal, legal),
            floor_matrices=matrices,
            capacity_plates=baseline.volumes,
            output_origin=(0.0, 0.0),
        )
        self.assertFalse(incomplete_authored_export.certificate.hard_pass)
        self.assertEqual(incomplete_authored_export.surfaces, ())
        self.assertEqual(
            incomplete_authored_export.certificate.failure_reasons,
            ("profiled_legal_clip_incomplete_authored_mesh",),
        )
        holed = Polygon(
            tuple(legal.exterior.coords),
            holes=(
                ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)),
            ),
        )
        multipart = unary_union((
            box(-5.0, -5.0, -1.0, 5.0),
            box(1.0, -5.0, 5.0, 5.0),
        ))
        for lawful in (holed, multipart):
            with self.subTest(geometry_type=lawful.geom_type):
                lawful_components = (
                    tuple(lawful.geoms)
                    if isinstance(lawful, MultiPolygon)
                    else (lawful,)
                )
                lawful_capacity = tuple(
                    SourceVolume(
                        baseline.volumes[0].role,
                        component,
                        floor_index / 2.0,
                        (floor_index + 1) / 2.0,
                        "floorwise_legal_matrix4",
                    )
                    for floor_index in range(2)
                    for component in lawful_components
                )
                result = clip_profiled_mesh_to_floorwise_legal_solids(
                    authority_source,
                    occupied_sections=(lawful, lawful),
                    legal_sections=(lawful, lawful),
                    floor_matrices=matrices,
                    capacity_plates=lawful_capacity,
                    output_origin=(0.0, 0.0),
                )
                self.assertTrue(
                    result.certificate.hard_pass,
                    result.certificate.to_dict(),
                )
                topology = result.certificate.to_dict()[
                    "floor_center_topology_metrics"
                ]
                expected_components = len(lawful_components)
                expected_holes = sum(
                    len(component.interiors)
                    for component in lawful_components
                )
                self.assertEqual(
                    [row["component_count"] for row in topology],
                    [expected_components, expected_components],
                )
                self.assertEqual(
                    [row["hole_count"] for row in topology],
                    [expected_holes, expected_holes],
                )

        self_intersection = Polygon(
            ((-4.0, -4.0), (4.0, 4.0), (-4.0, 4.0), (4.0, -4.0))
        )
        overlapping = MultiPolygon((
            box(-5.0, -5.0, 1.0, 5.0),
            box(-1.0, -5.0, 5.0, 5.0),
        ))
        for invalid, reason in (
            (
                self_intersection,
                "profiled_legal_clip_legal_section_invalid",
            ),
            (
                overlapping,
                "profiled_legal_clip_legal_components_overlap",
            ),
        ):
            with self.subTest(invalid_geometry=invalid.geom_type):
                result = clip_profiled_mesh_to_floorwise_legal_solids(
                    authority_source,
                    occupied_sections=occupied,
                    legal_sections=(invalid, invalid),
                    floor_matrices=matrices,
                    capacity_plates=baseline.volumes,
                    output_origin=(0.0, 0.0),
                )
                self.assertFalse(result.certificate.hard_pass)
                self.assertEqual(result.surfaces, ())
                self.assertEqual(result.certificate.failure_reasons, (reason,))

        drifted = clip_profiled_mesh_to_floorwise_legal_solids(
            authority_source,
            occupied_sections=(
                legal,
                box(-4.9, -4.9, 4.9, 4.9),
            ),
            legal_sections=(legal, legal),
            floor_matrices=matrices,
            capacity_plates=baseline.volumes,
            output_origin=(0.0, 0.0),
        )
        self.assertFalse(drifted.certificate.hard_pass)
        self.assertEqual(drifted.surfaces, ())
        self.assertEqual(
            drifted.certificate.failure_reasons,
            ("profiled_legal_clip_capacity_section_mismatch",),
        )
        mismatched_matrices = list(matrices)
        mismatched_matrices[0] = (
            (0.0, -1.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
        matrix_mismatch = clip_profiled_mesh_to_floorwise_legal_solids(
            authority_source,
            occupied_sections=occupied,
            legal_sections=(legal, legal),
            floor_matrices=tuple(mismatched_matrices),
            capacity_plates=baseline.volumes,
            output_origin=(0.0, 0.0),
        )
        self.assertFalse(matrix_mismatch.certificate.hard_pass)
        self.assertEqual(matrix_mismatch.surfaces, ())
        self.assertEqual(
            matrix_mismatch.certificate.failure_reasons,
            ("profiled_legal_clip_matrix_authority_mismatch",),
        )

    def test_floorwise_profiled_legal_clip_retains_terminal_slice_plane(self):
        """A real compiled slice plane survives Matrix4 placement and legal CSG."""
        from math import sqrt

        from design.maas.book_language.candidate_analysis import (
            _solid_morphology_metrics,
            _verified_exact_profiled_sloped_mesh,
        )
        from design.maas.geometry_language.floorwise_visual_projection import (
            _split_triangle_at_z_breakpoints,
            _transform_with_matrix_field,
            floorwise_authority_binding_hash,
        )
        from design.maas.geometry_language.floorwise_profiled_legal_clip import (
            clip_profiled_mesh_to_floorwise_legal_solids,
        )
        from design.maas.geometry_language.programs import (
            architectural_shape_programs,
        )
        from design.maas.geometry_language.projected_visual_contract import (
            serialize_certified_projected_visual,
            validate_projected_visual_artifact,
        )
        from design.maas.geometry_language.source_bridge import (
            compile_geometry_program_to_source_mass,
            floorwise_source_to_geometry_program,
            materialize_floorwise_legal_source,
        )

        def plane(
            triangle: tuple[tuple[float, float, float], ...],
        ) -> tuple[tuple[float, float, float], float, float]:
            left = tuple(
                triangle[1][axis] - triangle[0][axis]
                for axis in range(3)
            )
            right = tuple(
                triangle[2][axis] - triangle[0][axis]
                for axis in range(3)
            )
            normal = (
                left[1] * right[2] - left[2] * right[1],
                left[2] * right[0] - left[0] * right[2],
                left[0] * right[1] - left[1] * right[0],
            )
            magnitude = sqrt(sum(value * value for value in normal))
            unit = tuple(value / magnitude for value in normal)
            offset = -sum(
                unit[axis] * triangle[0][axis]
                for axis in range(3)
            )
            return unit, offset, magnitude / 2.0

        physical_height_m = 10.5
        identity = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
        program = next(
            item
            for item in architectural_shape_programs()
            if item.name == "shape_13_diagonal_slice"
        )
        source = compile_geometry_program_to_source_mass(
            program,
            box(-5.0, -5.0, 5.0, 5.0),
            target_plan_area=80.0,
            max_volume_bands=2,
            name="terminal-diagonal-slice-lineage",
        )
        self.assertIsNotNone(source)
        assert source is not None
        source = replace(
            source,
            metadata={
                **source.metadata,
                "program_dimensional_context": {
                    "effective_height_m": physical_height_m,
                },
            },
        )
        self.assertEqual(
            next(
                node.operator
                for node in program.nodes
                if node.id == program.root_id
            ),
            "slice",
        )

        authored_slice_triangles = []
        for surface in source.surfaces:
            physical = tuple(
                (float(x), float(y), float(z) * physical_height_m)
                for x, y, z in surface.vertices_m
            )
            normal, _offset, _area = plane(physical)
            if 0.12 < abs(normal[2]) < 0.90:
                authored_slice_triangles.append(surface.vertices_m)
        self.assertEqual(len(authored_slice_triangles), 2)
        authored_plane = plane(tuple(
            (
                float(x),
                float(y),
                float(z) * physical_height_m,
            )
            for x, y, z in authored_slice_triangles[0]
        ))
        self.assertGreater(abs(authored_plane[0][0]), 0.75)
        self.assertGreater(authored_plane[2], 1.0)
        for triangle in authored_slice_triangles:
            for x, y, z in triangle:
                point = (float(x), float(y), float(z) * physical_height_m)
                self.assertAlmostEqual(
                    sum(
                        authored_plane[0][axis] * point[axis]
                        for axis in range(3)
                    ) + authored_plane[1],
                    0.0,
                    delta=1e-7,
                )

        legal = Polygon((
            (-5.0, -5.0),
            (5.0, -5.0),
            (3.0, 5.0),
            (-3.0, 5.0),
        ))
        final = materialize_floorwise_legal_source(
            source,
            legal_sections=(legal, legal),
            target_plan_coverage=0.8,
            floor_capacity_plan_hash="terminal-diagonal-slice-capacity",
            target_floor_areas_m2=(40.0, 40.0),
        )
        self.assertIsNotNone(final)
        assert final is not None
        certificate = final.metadata["floorwise_visual_projection"]
        self.assertEqual(
            certificate["certification_mode"],
            "floorwise_profiled_legal_clip",
        )
        self.assertTrue(certificate["hard_pass"], certificate)
        artifact = serialize_certified_projected_visual(final)
        artifact["identity"] = {
            "geometryHash": artifact["projectedVisualGeometryHash"],
        }
        self.assertIsNotNone(validate_projected_visual_artifact(
            artifact,
            expected_section_geometry_binding_hash=str(
                certificate["section_geometry_binding_hash"]
            ),
        ))
        transport_tamper = deepcopy(final.metadata)
        transport_tamper["floorwise_visual_projection"][
            "verified_profiled_sloped_surface_hash"
        ] = "tampered"
        with self.assertRaisesRegex(
            ValueError,
            "authority binding mismatch",
        ):
            serialize_certified_projected_visual(
                replace(final, metadata=transport_tamper)
            )

        stack = final.metadata["floorwise_legal_matrix_stack"]
        matrices = tuple(floor["matrix4"] for floor in stack["floors"])
        centers = (0.25, 0.75)
        split_levels = (0.25, 0.5, 0.75)
        source_origin = source.footprint.centroid
        projected_slice_planes = []
        for triangle in authored_slice_triangles:
            world = tuple(
                (
                    float(x) + float(source_origin.x),
                    float(y) + float(source_origin.y),
                    float(z),
                )
                for x, y, z in triangle
            )
            for piece in _split_triangle_at_z_breakpoints(
                world,
                breakpoints=split_levels,
            ):
                transformed = tuple(
                    _transform_with_matrix_field(
                        matrices,
                        point,
                        breakpoints=centers,
                    )
                    for point in piece
                )
                physical = tuple(
                    (x, y, z * physical_height_m)
                    for x, y, z in transformed
                )
                projected_slice_planes.append(plane(physical))

        retained_slice_area = 0.0
        total_area = 0.0
        sloped_area = 0.0
        for surface in final.surfaces:
            triangle = tuple(
                (float(x), float(y), float(z) * physical_height_m)
                for x, y, z in surface.vertices_m
            )
            normal, _offset, area = plane(triangle)
            total_area += area
            if 0.12 < abs(normal[2]) < 0.90:
                sloped_area += area
            for expected_normal, expected_offset, _expected_area in (
                projected_slice_planes
            ):
                parallel = abs(sum(
                    normal[axis] * expected_normal[axis]
                    for axis in range(3)
                ))
                maximum_distance = max(
                    abs(sum(
                        expected_normal[axis] * vertex[axis]
                        for axis in range(3)
                    ) + expected_offset)
                    for vertex in triangle
                )
                if parallel >= 1.0 - 1e-6 and maximum_distance <= 1e-5:
                    retained_slice_area += area
                    break
        self.assertGreater(retained_slice_area, 1.0)
        self.assertGreaterEqual(sloped_area / total_area, 0.055)
        final.metadata.setdefault(
            "program_dimensional_context",
            {},
        )["effective_height_m"] = physical_height_m
        morphology = _solid_morphology_metrics(final)
        self.assertEqual(morphology["measurement_authority"], (
            "profiled_recursive_solid_mesh"
        ))
        self.assertEqual(morphology["body_phenotype"], "oblique")
        self.assertAlmostEqual(
            morphology["sloped_surface_ratio"],
            sloped_area / total_area,
            delta=1e-4,
        )
        self.assertEqual(
            final.metadata["authored_geometry_program"],
            program.to_dict(),
        )
        self.assertEqual(
            final.metadata["geometry_program_bridge_evidence"][
                "upstream_authored_program_hash"
            ],
            program.program_hash(),
        )
        replay_program = floorwise_source_to_geometry_program(
            final,
            height_m=physical_height_m,
            name="candidate-equivalent-capacity-replay",
        )
        self.assertEqual(
            replay_program.execution_contract[
                "capacity_replay_numeric_transport"
            ][
                "retry_on_issue_codes"
            ],
            ["tiny_edge"],
        )
        replay_compilation = compile_geometry_program(replay_program)
        self.assertEqual(
            replay_compilation.status,
            "compiled",
            replay_compilation.issues,
        )
        self.assertIn(
            "capacity_replay_numeric_transport",
            replay_compilation.metrics,
        )
        replay_metadata = deepcopy(final.metadata)
        replay_metadata["geometry_program"] = replay_program.to_dict()
        replay_metadata.pop("measured_solid_morphology", None)
        candidate_equivalent = replace(final, metadata=replay_metadata)
        candidate_morphology = _solid_morphology_metrics(
            candidate_equivalent
        )
        self.assertEqual(candidate_morphology["body_phenotype"], "oblique")
        self.assertAlmostEqual(
            candidate_morphology["sloped_surface_ratio"],
            sloped_area / total_area,
            delta=1e-4,
        )

        tampered_payload = deepcopy(replay_metadata)
        tampered_payload["authored_geometry_program"]["nodes"][-1][
            "parameters"
        ]["offset"] = -2.5
        tampered_payload.pop("measured_solid_morphology", None)
        self.assertEqual(
            _solid_morphology_metrics(
                replace(final, metadata=tampered_payload)
            )["body_phenotype"],
            "prismatic",
        )
        tampered_hash = deepcopy(replay_metadata)
        tampered_hash["geometry_program_bridge_evidence"][
            "upstream_authored_program_hash"
        ] = "tampered"
        tampered_hash.pop("measured_solid_morphology", None)
        self.assertEqual(
            _solid_morphology_metrics(
                replace(final, metadata=tampered_hash)
            )["body_phenotype"],
            "prismatic",
        )
        tampered_certificate = deepcopy(replay_metadata)
        tampered_certificate["floorwise_visual_projection"][
            "verified_profiled_sloped_surface_hash"
        ] = "tampered"
        tampered_certificate.pop("measured_solid_morphology", None)
        self.assertEqual(
            _solid_morphology_metrics(
                replace(final, metadata=tampered_certificate)
            )["body_phenotype"],
            "prismatic",
        )
        for field, value in (
            ("schema_version", "tampered"),
            ("verified_profiled_sloped_surface_area", float("nan")),
        ):
            malformed_certificate = deepcopy(replay_metadata)
            malformed_certificate["floorwise_visual_projection"][
                field
            ] = value
            malformed_certificate.pop("measured_solid_morphology", None)
            self.assertEqual(
                _verified_exact_profiled_sloped_mesh(
                    replace(final, metadata=malformed_certificate)
                ),
                False,
            )
        first_surface = final.surfaces[0]
        first_vertices = list(first_surface.vertices_m)
        first_vertices[0] = (
            first_vertices[0][0] + 1e-3,
            first_vertices[0][1],
            first_vertices[0][2],
        )
        surface_tampered = replace(
            final,
            surfaces=(
                replace(
                    first_surface,
                    vertices_m=tuple(first_vertices),
                ),
                *final.surfaces[1:],
            ),
            metadata=deepcopy(replay_metadata),
        )
        surface_tampered.metadata.pop(
            "measured_solid_morphology",
            None,
        )
        self.assertEqual(
            _solid_morphology_metrics(surface_tampered)["body_phenotype"],
            "prismatic",
        )

        slice_free_legal = box(2.0, -3.0, 4.0, 3.0)
        slice_free_volumes = tuple(
            SourceVolume(
                "recursive_solid_primary",
                slice_free_legal,
                index / 2.0,
                (index + 1) / 2.0,
                "floorwise_legal_matrix4",
            )
            for index in range(2)
        )
        slice_free_stack = {
            "status": "materialized",
            "matrix_convention": "row_major_column_vector",
            "floor_capacity_plan_hash": "slice-plane-fully-clipped",
            "floors": [
                {"matrix4": [list(row) for row in identity]}
                for _index in range(2)
            ],
        }
        slice_free_projection = (
            clip_profiled_mesh_to_floorwise_legal_solids(
                replace(
                    source,
                    metadata={
                        **deepcopy(source.metadata),
                        "floorwise_legal_matrix_stack": slice_free_stack,
                    },
                ),
                occupied_sections=(slice_free_legal, slice_free_legal),
                legal_sections=(slice_free_legal, slice_free_legal),
                floor_matrices=(identity, identity),
                capacity_plates=slice_free_volumes,
                output_origin=tuple(
                    slice_free_legal.centroid.coords
                )[0],
            )
        )
        self.assertTrue(
            slice_free_projection.certificate.hard_pass,
            slice_free_projection.certificate.to_dict(),
        )
        self.assertEqual(
            slice_free_projection.certificate.authored_program_hash,
            program.program_hash(),
        )
        self.assertEqual(
            slice_free_projection.certificate.
            verified_profiled_sloped_surface_area,
            0.0,
        )
        slice_free_metadata = deepcopy(source.metadata)
        slice_free_metadata.update({
            "geometry_program": floorwise_source_to_geometry_program(
                replace(
                    source,
                    footprint=slice_free_legal,
                    upper_footprint=slice_free_legal,
                    volumes=slice_free_volumes,
                    metadata={
                        **deepcopy(source.metadata),
                        "floorwise_legal_matrix_stack": slice_free_stack,
                    },
                ),
                height_m=physical_height_m,
            ).to_dict(),
            "authored_geometry_program": program.to_dict(),
            "floorwise_legal_matrix_stack": slice_free_stack,
            "floorwise_visual_projection": (
                slice_free_projection.certificate.to_dict()
            ),
        })
        slice_free_bridge = deepcopy(
            slice_free_metadata["geometry_program_bridge_evidence"]
        )
        slice_free_bridge["upstream_authored_program_hash"] = (
            program.program_hash()
        )
        slice_free_metadata["geometry_program_bridge_evidence"] = (
            slice_free_bridge
        )
        slice_free_metadata["program_dimensional_context"] = {
            "effective_height_m": physical_height_m,
        }
        slice_free_candidate = replace(
            source,
            footprint=slice_free_legal,
            upper_footprint=slice_free_legal,
            volumes=slice_free_volumes,
            surfaces=slice_free_projection.surfaces,
            metadata=slice_free_metadata,
        )
        self.assertEqual(
            _solid_morphology_metrics(
                slice_free_candidate
            )["body_phenotype"],
            "prismatic",
        )

        vertices = tuple(
            vertex
            for surface in final.surfaces
            for vertex in surface.vertices_m
        )
        triangles = tuple(
            (index, index + 1, index + 2)
            for index in range(0, len(vertices), 3)
        )
        for floor_index in range(2):
            measured = _mesh_section_polygon(
                vertices,
                triangles,
                (floor_index + 0.5) / 2.0,
            )
            expected = unary_union(tuple(
                volume.footprint
                for volume in final.volumes
                if abs(
                    float(volume.bottom_fraction) - floor_index / 2.0
                    ) <= 1e-8
            ))
            expected = translate(
                expected,
                xoff=-float(final.footprint.centroid.x),
                yoff=-float(final.footprint.centroid.y),
            )
            self.assertIsNotNone(measured)
            assert measured is not None
            self.assertLess(
                measured.symmetric_difference(expected).area,
                1e-6,
            )

    def test_floorwise_profiled_legal_clip_owns_lower_setback_terrace(self):
        """A lower-band terrace need not fit the smaller upper legal field."""
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        lower = box(-5.0, -5.0, 5.0, 5.0)
        upper = box(-4.0, -4.0, 4.0, 4.0)
        stacked = materialize_floorwise_legal_source(
            _authored_profiled_box_source(
                "profiled_legal_clip_setback",
                top_x_offset=12.0,
            ),
            legal_sections=(lower, upper),
            target_plan_coverage=0.95,
            floor_capacity_plan_hash="profiled-legal-clip-setback",
            target_floor_areas_m2=(100.0, 64.0),
        )

        self.assertIsNotNone(stacked)
        assert stacked is not None
        certificate = stacked.metadata["floorwise_visual_projection"]
        self.assertEqual(
            certificate["certification_mode"],
            "floorwise_profiled_legal_clip",
        )
        self.assertTrue(certificate["hard_pass"])
        self.assertFalse(certificate["visible_step_fallback"])

    def test_irregular_profiled_clip_is_strictly_final_mesh_contained(self):
        from design.maas.book_language.final_mesh_floor_evidence import (
            _mesh_section_segments,
        )
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        legal = Polygon((
            (19.209301786660244, 10.303196462622152),
            (7.952368958284199, 4.076129022809751),
            (4.463835566056591, 10.370785636863394),
            (4.0776683608121385, 11.067550186502613),
            (15.327914636438544, 17.308309178434918),
        ))
        stacked = materialize_floorwise_legal_source(
            _authored_profiled_box_source(
                "strict_irregular_profiled_clip",
                top_x_offset=12.0,
            ),
            legal_sections=(legal, legal),
            target_plan_coverage=0.9,
            floor_capacity_plan_hash="strict-irregular-profiled-clip",
            target_floor_areas_m2=(92.638, 92.638),
        )

        self.assertIsNotNone(stacked)
        assert stacked is not None
        vertices = tuple(
            vertex
            for surface in stacked.surfaces
            for vertex in surface.vertices_m
        )
        triangles = tuple(
            (index, index + 1, index + 2)
            for index in range(0, len(vertices), 3)
        )
        origin = stacked.footprint.centroid
        for normalized_z in (0.25, 0.75):
            segments = _mesh_section_segments(
                vertices,
                triangles,
                normalized_z,
            )
            self.assertTrue(segments)
            self.assertTrue(all(
                legal.covers(translate(
                    segment,
                    xoff=float(origin.x),
                    yoff=float(origin.y),
                ))
                for segment in segments
            ))

    def test_floorwise_visual_projection_rejects_legal_escape(self):
        """An authored mesh outside its legal host must fail, never empty-pass."""
        from design.maas.geometry_language.affine_matrix import identity_matrix4
        from design.maas.geometry_language.floorwise_visual_projection import (
            project_floorwise_visual_mesh,
        )

        legal = box(-4.0, -4.0, 4.0, 4.0)
        result = project_floorwise_visual_mesh(
            _authored_profiled_box_source("escaped_visual_mesh"),
            legal_sections=(legal,),
            floor_matrices=(identity_matrix4(),),
            capacity_plates=(
                SourceVolume(
                    "recursive_primary",
                    legal,
                    0.0,
                    1.0,
                    "floorwise_legal_matrix4",
                ),
            ),
        )

        self.assertFalse(result.certificate.hard_pass)
        self.assertEqual(result.certificate.status, "failed")
        self.assertIn(
            "projected_visual_mesh_outside_legal_section",
            result.certificate.failure_reasons,
        )
        self.assertEqual(result.surfaces, ())

    def test_floorwise_visual_projection_rejects_normalized_z_out_of_range(self):
        """Authored normalized Z outside [0, 1] must fail before projection."""
        from design.maas.geometry_language.affine_matrix import identity_matrix4
        from design.maas.geometry_language.floorwise_visual_projection import (
            project_floorwise_visual_mesh,
        )

        legal = box(-5.0, -5.0, 5.0, 5.0)
        source = _authored_profiled_triangle_source(
            "out_of_range_normalized_z",
            world_vertices=(
                (-2.0, -2.0, -0.1),
                (2.0, -2.0, 0.5),
                (-2.0, 2.0, 0.5),
            ),
            closure_world_vertex=(0.0, 0.0, 0.0),
            footprint=legal,
        )

        result = project_floorwise_visual_mesh(
            source,
            legal_sections=(legal,),
            floor_matrices=(identity_matrix4(),),
            capacity_plates=source.volumes,
        )

        self.assertFalse(result.certificate.hard_pass)
        self.assertEqual(result.certificate.status, "failed")
        self.assertIn(
            "authored_visual_normalized_z_out_of_range",
            result.certificate.failure_reasons,
        )
        self.assertEqual(result.surfaces, ())

    def test_floorwise_visual_projection_tessellates_matrix_field_breakpoints(self):
        """Projected triangles must follow the piecewise floor Matrix4 field."""
        from design.maas.geometry_language.affine_matrix import (
            identity_matrix4,
            translation_matrix4,
        )
        from design.maas.geometry_language.floorwise_visual_projection import (
            project_floorwise_visual_mesh,
        )

        legal = box(-30.0, -30.0, 30.0, 30.0)
        result = project_floorwise_visual_mesh(
            _authored_profiled_box_source("piecewise_visual_mesh"),
            legal_sections=(legal, legal),
            floor_matrices=(
                identity_matrix4(),
                translation_matrix4((10.0, 0.0, 0.0)),
            ),
            capacity_plates=(
                SourceVolume(
                    "recursive_primary",
                    box(-5.0, -5.0, 5.0, 5.0),
                    0.0,
                    0.5,
                    "floorwise_legal_matrix4",
                ),
                SourceVolume(
                    "recursive_primary",
                    box(5.0, -5.0, 15.0, 5.0),
                    0.5,
                    1.0,
                    "floorwise_legal_matrix4",
                ),
            ),
        )

        self.assertTrue(result.certificate.hard_pass, result.certificate)
        vertices = [
            vertex
            for surface in result.surfaces
            for vertex in surface.vertices_m
        ]
        quarter_x = [x for x, _y, z in vertices if abs(z - 0.25) <= 1e-8]
        three_quarter_x = [
            x for x, _y, z in vertices if abs(z - 0.75) <= 1e-8
        ]
        self.assertTrue(quarter_x)
        self.assertTrue(three_quarter_x)
        self.assertAlmostEqual(max(quarter_x), 5.0, delta=1e-8)
        self.assertAlmostEqual(max(three_quarter_x), 15.0, delta=1e-8)

    def test_floorwise_visual_projection_rejects_capped_profiled_export(self):
        """A capped profiled export is a failed mesh, never proxy-only success."""
        from design.maas.geometry_language.affine_matrix import identity_matrix4
        from design.maas.geometry_language.floorwise_visual_projection import (
            project_floorwise_visual_mesh,
        )

        source = _authored_profiled_box_source("capped_visual_mesh")
        bridge = dict(source.metadata["geometry_program_bridge_evidence"])
        bridge["raw_mesh_triangle_count"] = len(source.surfaces) + 1
        metadata = dict(source.metadata)
        metadata["geometry_program_bridge_evidence"] = bridge
        source = replace(source, metadata=metadata)
        legal = box(-20.0, -20.0, 20.0, 20.0)

        result = project_floorwise_visual_mesh(
            source,
            legal_sections=(legal,),
            floor_matrices=(identity_matrix4(),),
            capacity_plates=source.volumes,
        )

        self.assertFalse(result.certificate.hard_pass)
        self.assertEqual(result.certificate.status, "failed")
        self.assertIn(
            "incomplete_authored_mesh_export",
            result.certificate.failure_reasons,
        )
        self.assertEqual(result.surfaces, ())

    def test_floorwise_visual_projection_rejects_malformed_export_counters(self):
        """Malformed completeness counters must fail closed without raising."""
        from design.maas.geometry_language.affine_matrix import identity_matrix4
        from design.maas.geometry_language.floorwise_visual_projection import (
            project_floorwise_visual_mesh,
        )

        legal = box(-20.0, -20.0, 20.0, 20.0)
        for field in ("raw_mesh_triangle_count", "exported_surface_count"):
            with self.subTest(field=field):
                source = _authored_profiled_box_source(
                    f"malformed_{field}",
                )
                bridge = dict(
                    source.metadata["geometry_program_bridge_evidence"],
                )
                bridge[field] = "not-an-integer"
                metadata = dict(source.metadata)
                metadata["geometry_program_bridge_evidence"] = bridge
                source = replace(source, metadata=metadata)

                result = project_floorwise_visual_mesh(
                    source,
                    legal_sections=(legal,),
                    floor_matrices=(identity_matrix4(),),
                    capacity_plates=source.volumes,
                )

                self.assertFalse(result.certificate.hard_pass)
                self.assertEqual(result.certificate.status, "failed")
                self.assertIn(
                    "incomplete_authored_mesh_export",
                    result.certificate.failure_reasons,
                )
                self.assertEqual(result.surfaces, ())

    def test_floorwise_visual_projection_rejects_triangle_crossing_legal_hole(self):
        """Point-safe vertices must not hide a triangle crossing a legal void."""
        from design.maas.geometry_language.affine_matrix import identity_matrix4
        from design.maas.geometry_language.floorwise_visual_projection import (
            project_floorwise_visual_mesh,
        )

        footprint = box(-1.0, -1.0, 11.0, 11.0)
        source = _authored_profiled_triangle_source(
            "hole_crossing_visual_mesh",
            world_vertices=(
                (0.0, 0.0, 0.5),
                (10.0, 0.0, 0.5),
                (0.0, 10.0, 0.5),
            ),
            closure_world_vertex=(0.0, 0.0, 0.0),
            footprint=footprint,
        )
        legal = footprint.difference(box(1.5, 1.5, 2.5, 2.5))

        result = project_floorwise_visual_mesh(
            source,
            legal_sections=(legal,),
            floor_matrices=(identity_matrix4(),),
            capacity_plates=(
                SourceVolume(
                    "recursive_primary",
                    legal,
                    0.0,
                    1.0,
                    "floorwise_legal_matrix4",
                ),
            ),
        )

        self.assertFalse(result.certificate.hard_pass)
        self.assertIn(
            "projected_visual_mesh_outside_legal_section",
            result.certificate.failure_reasons,
        )
        self.assertEqual(result.surfaces, ())

    def test_floorwise_visual_projection_uses_explicit_final_footprint_origin(self):
        """Disconnected capacity evidence must not move final SourceMass-local mesh."""
        from design.maas.geometry_language.affine_matrix import identity_matrix4
        from design.maas.geometry_language.floorwise_visual_projection import (
            project_floorwise_visual_mesh,
        )

        source = _authored_profiled_box_source("explicit_visual_origin")
        legal = box(-30.0, -30.0, 30.0, 30.0)
        capacity_plates = (
            SourceVolume(
                "recursive_primary",
                box(-5.0, -5.0, 5.0, 5.0),
                0.0,
                1.0,
                "floorwise_legal_matrix4",
            ),
            SourceVolume(
                "recursive_primary",
                box(20.0, 0.0, 22.0, 2.0),
                0.0,
                1.0,
                "floorwise_legal_matrix4",
            ),
        )

        result = project_floorwise_visual_mesh(
            source,
            legal_sections=(legal,),
            floor_matrices=(identity_matrix4(),),
            capacity_plates=capacity_plates,
            output_origin=(0.0, 0.0),
        )

        self.assertTrue(result.certificate.hard_pass, result.certificate)
        all_x = [
            x
            for surface in result.surfaces
            for x, _y, _z in surface.vertices_m
        ]
        self.assertAlmostEqual(min(all_x), -5.0, delta=1e-8)
        self.assertAlmostEqual(max(all_x), 5.0, delta=1e-8)

    def test_floorwise_visual_projection_deduplicates_coplanar_breakpoint_pieces(self):
        """A triangle on a Matrix4 breakpoint must be emitted exactly once."""
        from design.maas.geometry_language.affine_matrix import identity_matrix4
        from design.maas.geometry_language.floorwise_visual_projection import (
            project_floorwise_visual_mesh,
        )

        footprint = box(-5.0, -5.0, 5.0, 5.0)
        source = _authored_profiled_triangle_source(
            "coplanar_breakpoint_visual_mesh",
            world_vertices=(
                (-4.0, -4.0, 0.25),
                (4.0, -4.0, 0.25),
                (-4.0, 4.0, 0.25),
            ),
            closure_world_vertex=(0.0, 0.0, 0.0),
            footprint=footprint,
        )
        legal = box(-20.0, -20.0, 20.0, 20.0)

        result = project_floorwise_visual_mesh(
            source,
            legal_sections=(legal, legal),
            floor_matrices=(identity_matrix4(), identity_matrix4()),
            capacity_plates=(
                SourceVolume(
                    "recursive_primary",
                    footprint,
                    0.0,
                    0.5,
                    "floorwise_legal_matrix4",
                ),
                SourceVolume(
                    "recursive_primary",
                    footprint,
                    0.5,
                    1.0,
                    "floorwise_legal_matrix4",
                ),
            ),
        )

        self.assertTrue(result.certificate.hard_pass, result.certificate)
        target_surfaces = tuple(
            surface
            for surface in result.surfaces
            if surface.semantic_patch_id
            == "recursive_primary:profiled_triangle"
        )
        self.assertEqual(len(target_surfaces), 1)
        self.assertEqual(
            result.certificate.projected_surface_count,
            len(result.surfaces),
        )

    def test_floorwise_visual_projection_allows_lower_piece_at_upper_setback(self):
        """A lower-floor face may widen below a legal upper setback boundary."""
        from design.maas.geometry_language.affine_matrix import identity_matrix4
        from design.maas.geometry_language.floorwise_visual_projection import (
            project_floorwise_visual_mesh,
        )

        lower_legal = box(-5.0, -5.0, 5.0, 5.0)
        upper_legal = box(-2.0, -2.0, 2.0, 2.0)
        source = _authored_profiled_triangle_source(
            "legal_lower_wider_than_upper",
            world_vertices=(
                (-4.0, -4.0, 0.0),
                (-1.0, 0.0, 0.5),
                (1.0, 0.0, 0.5),
            ),
            closure_world_vertex=(0.0, 0.0, 0.0),
            footprint=lower_legal,
        )

        result = project_floorwise_visual_mesh(
            source,
            legal_sections=(lower_legal, upper_legal),
            floor_matrices=(identity_matrix4(), identity_matrix4()),
            capacity_plates=(
                SourceVolume(
                    "recursive_primary",
                    lower_legal,
                    0.0,
                    0.5,
                    "floorwise_legal_matrix4",
                ),
                SourceVolume(
                    "recursive_primary",
                    upper_legal,
                    0.5,
                    1.0,
                    "floorwise_legal_matrix4",
                ),
            ),
            output_origin=(0.0, 0.0),
        )

        self.assertTrue(result.certificate.hard_pass, result.certificate)
        self.assertTrue(result.surfaces)

    def test_floorwise_visual_projection_rejects_unproven_legacy_open_mesh(self):
        """Missing export counts cannot certify an open legacy triangle as complete."""
        from design.maas.geometry_language.affine_matrix import identity_matrix4
        from design.maas.geometry_language.floorwise_visual_projection import (
            project_floorwise_visual_mesh,
        )

        legal = box(-5.0, -5.0, 5.0, 5.0)
        source = _authored_profiled_triangle_source(
            "unproven_open_legacy_mesh",
            world_vertices=(
                (-2.0, -2.0, 0.5),
                (2.0, -2.0, 0.5),
                (-2.0, 2.0, 0.5),
            ),
            footprint=legal,
        )
        bridge = dict(source.metadata["geometry_program_bridge_evidence"])
        bridge.pop("raw_mesh_triangle_count")
        bridge.pop("exported_surface_count")
        metadata = dict(source.metadata)
        metadata["geometry_program_bridge_evidence"] = bridge
        source = replace(source, metadata=metadata)

        result = project_floorwise_visual_mesh(
            source,
            legal_sections=(legal,),
            floor_matrices=(identity_matrix4(),),
            capacity_plates=source.volumes,
        )

        self.assertFalse(result.certificate.hard_pass)
        self.assertEqual(result.certificate.status, "failed")
        self.assertIn(
            "unproven_authored_mesh_completeness",
            result.certificate.failure_reasons,
        )
        self.assertEqual(result.surfaces, ())

    def test_mesh_fit_containment_uses_occupied_triangles_not_convex_hull_void(self):
        """A legal U/wing plan must not fail because its empty hull crosses a court."""
        try:
            from design.maas.geometry_language.source_bridge import (
                _mesh_plan_projection_inside_host,
            )
        except ImportError:
            self.fail("source fit has no exact mesh-plan containment predicate")

        host = box(0.0, 0.0, 10.0, 10.0).difference(box(3.0, 3.0, 7.0, 10.0))
        vertices = (
            (0.5, 0.5, 0.0),
            (2.5, 0.5, 0.0),
            (2.5, 9.5, 0.0),
            (0.5, 9.5, 0.0),
            (7.5, 0.5, 0.0),
            (9.5, 0.5, 0.0),
            (9.5, 9.5, 0.0),
            (7.5, 9.5, 0.0),
        )
        triangles = ((0, 1, 2), (0, 2, 3), (4, 5, 6), (4, 6, 7))

        self.assertFalse(
            host.covers(MultiPoint([(x, y) for x, y, _z in vertices]).convex_hull)
        )
        self.assertTrue(
            _mesh_plan_projection_inside_host(vertices, triangles, host)
        )

    def test_live_pnu_parking_uses_site_local_frontage_geometry(self):
        """Absolute UTM/WGS frontage must not be compared to a local 0-based site."""
        try:
            from design.management.commands.benchmark_maas_book_program_portfolios import (
                _with_site_local_parking_frontage,
            )
        except ImportError:
            self.fail("live PNU command does not localize parking frontage")
        from design.maas.parking_strategy import infer_parking_strategy

        site = box(0.0, 0.0, 20.0, 20.0)
        footprint = box(5.0, 5.0, 15.0, 15.0)
        local_frontage = mapping(LineString([(0.0, 0.0), (20.0, 0.0)]))
        parking_options = _with_site_local_parking_frontage(
            {
                "road_context": {
                    "frontage_geometry": mapping(
                        LineString(
                            [(500000.0, 4100000.0), (500020.0, 4100000.0)]
                        )
                    )
                }
            },
            local_frontage,
        )

        strategy = infer_parking_strategy(
            {
                "footprint_area": 100.0,
                "floor_area": 400.0,
                "num_floors": 5,
                "height": 15.0,
                "bcr": 25.0,
                "required_parking_spaces": 1,
                "required_accessible_parking_spaces": 0,
            },
            site_area_m2=400.0,
            building_type="neighborhood",
            footprint_utm=footprint,
            site_utm=site,
            road_context=parking_options["road_context"],
        )

        self.assertEqual(strategy["layout_candidate"]["status"], "pass")
        self.assertTrue(
            strategy["layout_candidate"]["grid_solver"]["entrance_verified"]
        )

    def test_smoke_search_never_stops_before_downstream_hard_gates(self):
        """Generation cannot prove legal or parking acceptance at this stage."""
        try:
            from design.maas.book_language.candidate_generation import (
                _eligible_smoke_floor_candidate,
            )
        except ImportError:
            self.fail("smoke search has no lineage-aware floor predicate")

        floor_contract = {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "hard_pass": True,
        }
        capacity_measurement = {"hard_pass": True}
        capacity_target = {"target_hard_pass": True}
        base = SimpleNamespace(
            status="compiled",
            volumes=(object(),),
            surfaces=(object(),),
            metadata={
                "book_generation_lineage": {
                    "stage": "base",
                    "parent_key": "base-key",
                },
            }
        )
        descendant = SimpleNamespace(
            status="compiled",
            volumes=(object(),),
            surfaces=(object(),),
            metadata={
                "book_generation_lineage": {
                    "stage": "combination",
                    "parent_key": "base-key",
                },
            }
        )

        self.assertFalse(
            _eligible_smoke_floor_candidate(
                base,
                floor_contract,
                capacity_measurement,
                capacity_target,
                set(),
            )
        )
        self.assertFalse(
            _eligible_smoke_floor_candidate(
                descendant,
                floor_contract,
                capacity_measurement,
                capacity_target,
                set(),
            )
        )
        self.assertFalse(
            _eligible_smoke_floor_candidate(
                descendant,
                floor_contract,
                capacity_measurement,
                capacity_target,
                {"base-key"},
            )
        )
        self.assertFalse(
            _eligible_smoke_floor_candidate(
                base,
                floor_contract,
                {"hard_pass": False},
                capacity_target,
                set(),
            )
        )
        self.assertFalse(
            _eligible_smoke_floor_candidate(
                base,
                floor_contract,
                capacity_measurement,
                {"target_hard_pass": False},
                set(),
            )
        )

    def test_mesh_section_preserves_nested_void_area_instead_of_filling_hole(self):
        """Removing nested-face filtering must make the courtyard center solid."""
        vertices, triangles = _hollow_square_prism_mesh()

        section = _mesh_section_polygon(vertices, triangles, 0.5)

        self.assertIsNotNone(section)
        self.assertAlmostEqual(section.area, 84.0, places=6)
        self.assertEqual(len(section.interiors), 1)
        self.assertFalse(section.covers(Point(0.0, 0.0)))

    def test_inhabitable_floor_gate_rejects_thin_annular_sculpture_and_accepts_five_storey_stack(self):
        """Removing the clear-depth gate must let the 1 m ring pass as a building."""
        try:
            from design.maas.shared_floor_contract import materialize_shared_floor_contract
        except ImportError:
            self.fail("shared-floor contract is not implemented")

        site = box(-40.0, -40.0, 40.0, 40.0)
        legal_sections = (site,) * 5
        building_plate = box(-10.0, -8.0, 10.0, 8.0)
        annular_plate = Point(0.0, 0.0).buffer(30.0, resolution=64).difference(
            Point(0.0, 0.0).buffer(29.0, resolution=64)
        )
        building = SourceMass(
            name="five_storey_building",
            footprint=building_plate,
            volumes=(
                SourceVolume("main", building_plate, 0.0, 1.0, "geometry_program"),
            ),
        )
        sculpture = SourceMass(
            name="thin_annular_sculpture",
            footprint=annular_plate,
            volumes=(
                SourceVolume("ring", annular_plate, 0.0, 1.0, "geometry_program"),
            ),
        )

        building_contract = materialize_shared_floor_contract(
            building,
            site_local_utm=site,
            legal_sections=legal_sections,
            height_m=15.0,
            floors=5,
            pnu="1168011800104170004",
            program_hash="program-building",
            geometry_hash="geometry-building",
        )
        sculpture_contract = materialize_shared_floor_contract(
            sculpture,
            site_local_utm=site,
            legal_sections=legal_sections,
            height_m=15.0,
            floors=5,
            pnu="1168011800104170004",
            program_hash="program-sculpture",
            geometry_hash="geometry-sculpture",
        )

        self.assertTrue(building_contract["hard_pass"])
        self.assertEqual(building_contract["totals"]["num_floors"], 5)
        self.assertAlmostEqual(
            building_contract["totals"]["total_floor_area_m2"],
            1600.0,
            places=3,
        )
        self.assertEqual(
            len({plate["floor_contract_hash"] for plate in building_contract["plates"]}),
            1,
        )
        self.assertFalse(sculpture_contract["hard_pass"])
        self.assertIn(
            "insufficient_clear_floor_depth",
            sculpture_contract["failure_reasons"],
        )

    def test_capacity_measurement_uses_shared_floor_contract_totals(self):
        """Removing shared-floor consumption must restore the false midpoint result."""
        from design.maas.book_language.capacity_contract import measure_source_capacity
        from design.maas.shared_floor_contract import materialize_shared_floor_contract

        site = box(0.0, 0.0, 80.0, 80.0)
        building_plate = box(0.0, 0.0, 20.0, 16.0)
        source = SourceMass(
            name="five_storey_building",
            footprint=building_plate,
            volumes=(
                SourceVolume("main", building_plate, 0.0, 1.0, "geometry_program"),
            ),
        )
        floor_contract = materialize_shared_floor_contract(
            source,
            site_local_utm=site,
            legal_sections=(site,) * 5,
            height_m=15.0,
            floors=5,
            feasible_capacity_m2=2000.0,
        )

        try:
            measurement = measure_source_capacity(
                source,
                {
                    "feasible_maximum_floor_area_m2": 2000.0,
                    "minimum_utilization": 0.70,
                },
                site_local_utm=site,
                height_m=15.0,
                floors=1,
                shared_floor_contract=floor_contract,
            )
        except TypeError:
            self.fail("capacity measurement does not consume shared-floor evidence")

        self.assertEqual(
            measurement["floor_contract_hash"],
            floor_contract["floor_contract_hash"],
        )
        self.assertEqual(measurement["floor_area_m2"], 1600.0)
        self.assertEqual(measurement["far_pct"], 25.0)
        self.assertEqual(measurement["feasible_capacity_utilization"], 0.8)
        self.assertTrue(measurement["hard_pass"])

    def test_capacity_measurement_honors_rounded_minimum_floor_area(self):
        """A 0.001 m2 contract must not fail on its unrounded ratio."""
        from design.maas.book_language.capacity_contract import measure_source_capacity

        site = box(0.0, 0.0, 20.0, 20.0)
        source = SourceMass(
            name="rounded_capacity_target",
            footprint=box(0.0, 0.0, 1.0, 1.0),
            volumes=(),
        )
        measurement = measure_source_capacity(
            source,
            {
                "feasible_maximum_floor_area_m2": 332.322,
                "minimum_utilization": 0.70,
                "minimum_floor_area_m2": 232.625,
            },
            site_local_utm=site,
            height_m=10.5,
            floors=3,
            shared_floor_contract={
                "schema_version": "arr.maas.shared_floor_contract.v1",
                "hard_pass": True,
                "floor_contract_hash": "rounded-minimum",
                "totals": {"total_floor_area_m2": 232.625001},
            },
        )

        self.assertEqual(measurement["floor_area_m2"], 232.625)
        self.assertEqual(measurement["feasible_capacity_utilization"], 0.7)
        self.assertTrue(measurement["hard_pass"])

    def test_candidate_capacity_retry_measures_the_same_five_floor_contract(self):
        """Plan-fit retries must not use the old three-band volume estimate."""
        from design.test_task5_regression_fixtures import (
            legal_generation_context_for_site,
        )

        try:
            from design.maas.book_language.candidate_generation import (
                _shared_floor_capacity_measurement,
            )
        except ImportError:
            self.fail("candidate retry has no shared-floor capacity measurement")

        site = box(0.0, 0.0, 80.0, 80.0)
        plate = box(0.0, 0.0, 20.0, 16.0)
        source = SourceMass(
            name="five_storey_retry",
            footprint=plate,
            volumes=(SourceVolume("main", plate, 0.0, 1.0, "geometry_program"),),
            metadata={
                "geometry_program_bridge_evidence": {
                    "program_hash": "retry-program",
                    "geometry_hash": "retry-geometry",
                }
            },
        )
        with patch(
            "design.maas.book_language.candidate_generation.generation_site_at_height",
            return_value=site,
        ):
            floor_contract, measurement = _shared_floor_capacity_measurement(
                source,
                {
                    "feasible_maximum_floor_area_m2": 2000.0,
                    "minimum_utilization": 0.70,
                },
                generation_context=legal_generation_context_for_site(site),
                capacity_site=site,
                height=15.0,
                floors=5,
                pnu="1168011800104170004",
            )

        self.assertEqual(floor_contract["totals"]["num_floors"], 5)
        self.assertEqual(measurement["floor_area_m2"], 1600.0)
        self.assertEqual(measurement["floor_contract_hash"], floor_contract["floor_contract_hash"])
        self.assertTrue(measurement["hard_pass"])

    def test_capacity_retry_adds_a_measured_typed_pack_instead_of_a_named_shape(self):
        """A shortfall must recompose the AST without selecting a shape template."""
        try:
            from design.maas.geometry_language.book_adapter import (
                apply_capacity_composition_to_geometry_program,
            )
        except ImportError:
            self.fail("capacity retry has no typed GeometryProgram composition")

        builder = GeometryProgramBuilder("capacity-bar")
        bar = builder.add(
            "primitive",
            "box",
            parameters={"width": 4.0, "depth": 1.0, "height": 1.0},
            semantic_role="base_volume",
        )
        program = builder.build(bar, family="bar")

        recomposed = apply_capacity_composition_to_geometry_program(
            program,
            achieved_utilization=0.52,
            target_utilization=0.78,
        )
        original_compilation = compile_geometry_program(program)
        recomposed_compilation = compile_geometry_program(recomposed)
        capacity_nodes = [
            node
            for node in recomposed.nodes
            if node.provenance.get("source") == "capacity_composition_agent"
        ]

        self.assertEqual(original_compilation.status, "compiled")
        self.assertEqual(recomposed_compilation.status, "compiled")
        self.assertGreater(
            recomposed_compilation.metrics["volume"],
            original_compilation.metrics["volume"],
        )
        self.assertEqual(len(capacity_nodes), 1)
        self.assertEqual(capacity_nodes[0].operator, "related_array")
        self.assertEqual(capacity_nodes[0].parameters["mode"], "pack")
        self.assertEqual(capacity_nodes[0].parameters["count"], 2)
        self.assertEqual(capacity_nodes[0].parameters["unit_scale"], 0.94)
        self.assertEqual(
            capacity_nodes[0].provenance["measurement_source"],
            "shared_floor_contract",
        )
        self.assertFalse(capacity_nodes[0].provenance["completed_building_template"])
        self.assertNotEqual(recomposed.program_hash(), program.program_hash())

        unchanged = apply_capacity_composition_to_geometry_program(
            program,
            achieved_utilization=0.80,
            target_utilization=0.78,
        )
        self.assertEqual(unchanged.program_hash(), program.program_hash())

    def test_mass_materialization_keeps_one_final_geometry_across_capacity_advice(self):
        """Advisory utilization cannot replace the final projected program."""
        from design.maas.book_language import candidate_generation
        from design.maas.geometry_language import (
            base_seed_programs,
        )
        from design.maas.geometry_language.floorwise_visual_projection import (
            projected_surface_visual_hash,
        )
        from design.maas.program_massing.semantic_carriers import (
            semantic_site_context_hash,
        )
        from design.test_task5_regression_fixtures import (
            canonical_gym_materialization_context,
            canonical_gym_semantic_source,
        )

        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "slab"
        )
        host = box(0.0, 0.0, 40.0, 30.0)
        source = canonical_gym_semantic_source("authored-capacity-invariant")
        sequence = SimpleNamespace(
            notes=("geometry_program_directive=authored-capacity-invariant",)
        )
        semantic_context = canonical_gym_materialization_context(
            capacity_alternative_id="brief_target",
            site=host,
        )
        expected_site_context_hash = semantic_site_context_hash(
            pnu=semantic_context["pnu"],
            building_type=semantic_context["building_type"],
            site=host,
        )

        with patch.object(
            candidate_generation,
            "_geometry_program_registry",
            return_value={"authored-capacity-invariant": program},
        ):
            baseline = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                containment_host=host,
                floor_containment_hosts=(host,),
                minimum_host_plan_coverage=0.15,
                floor_capacity_plan_hash="capacity-invariant-plan",
                target_floor_areas_m2=(600.0,),
                **semantic_context,
            )
            capacity_advised = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                containment_host=host,
                floor_containment_hosts=(host,),
                minimum_host_plan_coverage=0.95,
                capacity_composition_utilizations=(0.40, 0.90),
                floor_capacity_plan_hash="capacity-invariant-plan",
                target_floor_areas_m2=(600.0,),
                **semantic_context,
            )

        self.assertIsNotNone(baseline)
        self.assertIsNotNone(capacity_advised)
        assert baseline is not None and capacity_advised is not None
        for materialized in (baseline, capacity_advised):
            persisted_context = materialized.metadata[
                "final_semantic_projection_context"
            ]
            self.assertEqual(
                persisted_context["site_context_hash"],
                expected_site_context_hash,
            )
            self.assertEqual(
                persisted_context["capacity_measurement_hash"],
                "pending_capacity_measurement",
            )
            self.assertEqual(
                persisted_context["achieved_capacity_band"],
                persisted_context["capacity_alternative_id"],
            )
        self.assertEqual(
            baseline.metadata["geometry_program"],
            capacity_advised.metadata["geometry_program"],
        )
        self.assertEqual(baseline.volumes, capacity_advised.volumes)
        self.assertEqual(baseline.surfaces, capacity_advised.surfaces)
        self.assertEqual(
            projected_surface_visual_hash(baseline.surfaces),
            projected_surface_visual_hash(capacity_advised.surfaces),
        )
        self.assertEqual(
            baseline.metadata["geometry_authority"],
            "final_floorwise_legal_geometry_program",
        )
        self.assertEqual(
            baseline.metadata["final_geometry_hash"],
            capacity_advised.metadata["final_geometry_hash"],
        )
        self.assertNotIn(
            "floorwise_legal_sibling_evidence",
            baseline.metadata,
        )

    def test_materialization_uses_aggregate_target_not_largest_floor_target(self):
        from design.maas.book_language import candidate_generation
        from design.maas.geometry_language import base_seed_programs
        from design.test_task5_regression_fixtures import (
            canonical_gym_materialization_context,
            canonical_gym_semantic_source,
        )

        program = next(
            item
            for item in base_seed_programs()
            if str((item.metadata.get("base_seed") or {}).get("seed_id") or "")
            == "slab"
        )
        host = box(0.0, 0.0, 40.0, 30.0)
        source = canonical_gym_semantic_source("aggregate-capacity-invariant")
        sequence = SimpleNamespace(
            notes=("geometry_program_directive=aggregate-capacity-invariant",)
        )
        semantic_context = canonical_gym_materialization_context(
            capacity_alternative_id="brief_target",
            site=host,
        )

        with patch.object(
            candidate_generation,
            "_geometry_program_registry",
            return_value={"aggregate-capacity-invariant": program},
        ):
            front_loaded = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                containment_host=host,
                floor_containment_hosts=(host, host),
                minimum_host_plan_coverage=0.15,
                floor_capacity_plan_hash="capacity-plan:front-loaded",
                target_floor_areas_m2=(600.0, 200.0),
                **semantic_context,
            )
            balanced = candidate_generation._materialize_directed_geometry(
                source,
                sequence,
                containment_host=host,
                floor_containment_hosts=(host, host),
                minimum_host_plan_coverage=0.15,
                floor_capacity_plan_hash="capacity-plan:balanced",
                target_floor_areas_m2=(400.0, 400.0),
                **semantic_context,
            )

        self.assertIsNotNone(front_loaded)
        self.assertIsNotNone(balanced)
        assert front_loaded is not None and balanced is not None
        self.assertEqual(
            front_loaded.metadata["final_program_hash"],
            balanced.metadata["final_program_hash"],
        )
        self.assertEqual(
            front_loaded.metadata["final_geometry_hash"],
            balanced.metadata["final_geometry_hash"],
        )
        self.assertEqual(front_loaded.volumes, balanced.volumes)
        self.assertEqual(front_loaded.surfaces, balanced.surfaces)
        self.assertEqual(
            front_loaded.metadata["capacity_projection_measurement"][
                "requested_floor_area_m2"
            ],
            800.0,
        )
        self.assertEqual(
            balanced.metadata["capacity_projection_measurement"][
                "requested_floor_area_m2"
            ],
            800.0,
        )

    def test_capacity_pack_retry_requires_a_vertically_viable_floor_source(self):
        """Plan packing must not spend a retry on missing/unsupported storeys."""
        try:
            from design.maas.book_language.candidate_generation import (
                _capacity_pack_retry_eligible,
            )
        except ImportError:
            self.fail("capacity retry has no shared-floor viability predicate")

        clear_depth_only = {
            "hard_pass": False,
            "failure_reasons": ["insufficient_clear_floor_depth"],
            "plates": [
                {"gross_area_m2": 20.0, "support_ratio": 1.0},
                {"gross_area_m2": 18.0, "support_ratio": 0.8},
            ],
        }
        missing_storey = {
            "hard_pass": False,
            "failure_reasons": ["insufficient_floor_area"],
            "plates": [
                {"gross_area_m2": 20.0, "support_ratio": 1.0},
                {"gross_area_m2": 0.0, "support_ratio": 0.0},
            ],
        }
        unsupported = {
            "hard_pass": False,
            "failure_reasons": ["insufficient_vertical_support"],
            "plates": [
                {"gross_area_m2": 20.0, "support_ratio": 1.0},
                {"gross_area_m2": 18.0, "support_ratio": 0.0},
            ],
        }

        self.assertTrue(_capacity_pack_retry_eligible(clear_depth_only))
        self.assertFalse(_capacity_pack_retry_eligible(missing_storey))
        self.assertFalse(_capacity_pack_retry_eligible(unsupported))
        self.assertTrue(
            _capacity_pack_retry_eligible(
                {"hard_pass": True, "failure_reasons": [], "plates": []}
            )
        )

    def test_capacity_retry_selects_only_a_fully_recertified_typed_composition(self):
        """Only a legal, capacity-passing AST improvement may replace its parent."""
        try:
            from design.maas.book_language.candidate_generation import (
                _capacity_retry_result_is_selectable,
            )
        except ImportError:
            self.fail("capacity retry has no floor-safe selection predicate")

        initial = {
            "hard_pass": False,
            "feasible_capacity_utilization": 0.6972,
        }
        improved = {
            "hard_pass": True,
            "feasible_capacity_utilization": 0.7010,
        }

        self.assertTrue(
            _capacity_retry_result_is_selectable(
                {"hard_pass": True},
                improved,
                initial,
            )
        )
        self.assertFalse(
            _capacity_retry_result_is_selectable(
                {"hard_pass": False},
                improved,
                initial,
            )
        )
        self.assertFalse(
            _capacity_retry_result_is_selectable(
                {"hard_pass": True},
                {
                    "hard_pass": False,
                    "feasible_capacity_utilization": 0.7010,
                },
                initial,
            )
        )
        self.assertFalse(
            _capacity_retry_result_is_selectable(
                {"hard_pass": True},
                {
                    "hard_pass": True,
                    "feasible_capacity_utilization": 0.6960,
                },
                initial,
            )
        )

    def test_capacity_retry_is_noop_when_initial_floor_target_is_met(self):
        """A capacity pass must not be enlarged by a redundant retry."""
        from design.maas.book_language import capacity_alternatives
        from design.maas.book_language.capacity_contract import (
            measure_source_capacity,
        )
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )
        from design.maas.shared_floor_contract import (
            materialize_shared_floor_contract,
        )

        legal_sections = tuple(
            box(5.0, 5.0, 15.0, 15.0)
            for _floor_index in range(4)
        )
        legal_floor_caps = [round(section.area, 3) for section in legal_sections]
        feasible_capacity = sum(legal_floor_caps)
        alternative = {
            "target_utilization": 0.70,
            "feasible_minimum_utilization": 0.70,
        }
        alternative_contract = {
            "minimum_utilization": 0.70,
            "feasible_maximum_floor_area_m2": feasible_capacity,
            "bcr_adjusted_floor_areas_m2": legal_floor_caps,
            "target_floor_areas_m2": [
                capacity * 0.70 for capacity in legal_floor_caps
            ],
        }
        source = _authored_profiled_box_source("r287_capacity_retry_probe")
        site = box(0.0, 0.0, 20.0, 20.0)

        def materialize_and_measure(
            plan_coverage: float,
            floor_targets: tuple[float, ...],
        ):
            stacked = materialize_floorwise_legal_source(
                source,
                legal_sections=legal_sections,
                target_plan_coverage=plan_coverage,
                target_floor_areas_m2=floor_targets,
            )
            self.assertIsNotNone(stacked)
            assert stacked is not None
            floor_contract = materialize_shared_floor_contract(
                stacked,
                site_local_utm=site,
                legal_sections=legal_sections,
                height_m=14.0,
                floors=4,
                feasible_capacity_m2=feasible_capacity,
            )
            measurement = measure_source_capacity(
                stacked,
                alternative_contract,
                site_local_utm=site,
                height_m=14.0,
                floors=4,
                shared_floor_contract=floor_contract,
            )
            return stacked, floor_contract, measurement

        initial_targets = tuple(alternative_contract["target_floor_areas_m2"])
        _initial_stack, initial_floor_contract, initial_measurement = (
            materialize_and_measure(0.70, initial_targets)
        )
        self.assertTrue(initial_floor_contract["hard_pass"])
        self.assertAlmostEqual(
            initial_measurement["feasible_capacity_utilization"],
            0.70,
            delta=0.0001,
        )
        self.assertTrue(initial_measurement["hard_pass"])

        capacity_retry_floor_targets = getattr(
            capacity_alternatives,
            "capacity_retry_floor_targets",
            None,
        )
        self.assertIsNotNone(
            capacity_retry_floor_targets,
            "capacity retry does not refit the authoritative floor targets",
        )
        retry_targets = capacity_retry_floor_targets(
            alternative_contract,
            alternative,
            initial_measurement,
        )
        self.assertEqual(
            retry_targets,
            tuple(round(value, 3) for value in initial_targets),
        )

    def test_capacity_retry_dispatch_closes_a_measured_floor_target_miss(self):
        """Compensated targets must reach a real remeasurement hard pass."""
        from design.maas.book_language.candidate_generation import (
            _capacity_retry_required,
        )
        from design.maas.book_language.capacity_alternatives import (
            capacity_retry_floor_targets,
            capacity_retry_plan_coverage,
        )
        from design.maas.book_language.capacity_contract import (
            measure_source_capacity,
        )
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )
        from design.maas.shared_floor_contract import (
            materialize_shared_floor_contract,
        )

        legal_sections = tuple(box(5.0, 5.0, 15.0, 15.0) for _ in range(4))
        floor_caps = [float(section.area) for section in legal_sections]
        feasible_capacity = sum(floor_caps)
        alternative = {
            "target_utilization": 0.70,
            "feasible_minimum_utilization": 0.70,
        }
        contract = {
            "minimum_utilization": 0.70,
            "feasible_maximum_floor_area_m2": feasible_capacity,
            "bcr_adjusted_floor_areas_m2": floor_caps,
            "target_floor_areas_m2": [70.0] * 4,
        }
        source = _authored_profiled_box_source("r287_capacity_dispatch_probe")
        site = box(0.0, 0.0, 20.0, 20.0)

        def materialize_and_measure(
            plan_coverage: float,
            floor_targets: tuple[float, ...],
        ):
            stacked = materialize_floorwise_legal_source(
                source,
                legal_sections=legal_sections,
                target_plan_coverage=plan_coverage,
                target_floor_areas_m2=floor_targets,
            )
            self.assertIsNotNone(stacked)
            assert stacked is not None
            floor_contract = materialize_shared_floor_contract(
                stacked,
                site_local_utm=site,
                legal_sections=legal_sections,
                height_m=14.0,
                floors=4,
                feasible_capacity_m2=feasible_capacity,
            )
            measurement = measure_source_capacity(
                stacked,
                contract,
                site_local_utm=site,
                height_m=14.0,
                floors=4,
                shared_floor_contract=floor_contract,
            )
            return floor_contract, measurement

        _initial_floor_contract, initial_measurement = materialize_and_measure(
            0.68,
            (68.0, 68.0, 68.0, 68.0),
        )
        self.assertFalse(initial_measurement["hard_pass"])
        self.assertAlmostEqual(
            initial_measurement["feasible_capacity_utilization"],
            0.68,
            delta=0.0001,
        )

        retry_coverage = capacity_retry_plan_coverage(
            0.68,
            alternative,
            initial_measurement,
        )
        retry_targets = capacity_retry_floor_targets(
            contract,
            alternative,
            initial_measurement,
        )
        self.assertTrue(_capacity_retry_required(
            current_plan_coverage=0.68,
            retry_plan_coverage=retry_coverage,
            current_floor_targets=contract["target_floor_areas_m2"],
            retry_floor_targets=retry_targets,
        ))

        retried_floor_contract, retried_measurement = materialize_and_measure(
            retry_coverage,
            retry_targets,
        )
        self.assertTrue(retried_floor_contract["hard_pass"])
        self.assertTrue(retried_measurement["hard_pass"])
        self.assertGreaterEqual(
            retried_measurement["feasible_capacity_utilization"],
            0.70,
        )

    def test_capacity_retry_floor_targets_compensate_shortfall_within_legal_caps(self):
        """A measured miss may raise floor targets, but never beyond legal plates."""
        from design.maas.book_language import capacity_alternatives

        contract = {
            "bcr_adjusted_floor_areas_m2": [
                102.931,
                102.931,
                74.989,
                51.471,
            ],
            "target_floor_areas_m2": [
                72.052,
                72.052,
                52.492,
                36.030,
            ],
        }
        capacity_retry_floor_targets = getattr(
            capacity_alternatives,
            "capacity_retry_floor_targets",
            None,
        )
        self.assertIsNotNone(
            capacity_retry_floor_targets,
            "capacity retry does not refit the authoritative floor targets",
        )
        retry_targets = capacity_retry_floor_targets(
            contract,
            {
                "target_utilization": 0.70,
                "feasible_minimum_utilization": 0.70,
            },
            {"feasible_capacity_utilization": 0.65},
        )

        self.assertAlmostEqual(sum(retry_targets), 250.520, delta=0.002)
        self.assertTrue(all(
            target <= cap + 1e-9
            for target, cap in zip(
                retry_targets,
                contract["bcr_adjusted_floor_areas_m2"],
            )
        ))

    def test_capacity_retry_enters_when_floor_targets_change_at_maximum_coverage(self):
        """A 0.95 plan ceiling must not suppress a measured floor-target repair."""
        from design.maas.book_language import (
            candidate_generation,
            capacity_alternatives,
        )

        contract = {
            "bcr_adjusted_floor_areas_m2": [
                102.931,
                102.931,
                74.989,
                51.471,
            ],
            "target_floor_areas_m2": [
                97.784,
                97.784,
                71.240,
                48.898,
            ],
        }
        alternative = {
            "target_utilization": 0.95,
            "feasible_minimum_utilization": 0.70,
        }
        retry_targets = capacity_alternatives.capacity_retry_floor_targets(
            contract,
            alternative,
            {"feasible_capacity_utilization": 0.90},
        )
        retry_required = getattr(
            candidate_generation,
            "_capacity_retry_required",
            None,
        )

        self.assertIsNotNone(
            retry_required,
            "capacity retry is still gated only by plan-coverage growth",
        )
        assert retry_required is not None
        self.assertAlmostEqual(sum(retry_targets), 332.322, delta=0.002)
        self.assertTrue(retry_required(
            current_plan_coverage=0.95,
            retry_plan_coverage=0.95,
            current_floor_targets=contract["target_floor_areas_m2"],
            retry_floor_targets=retry_targets,
        ))
        self.assertFalse(retry_required(
            current_plan_coverage=0.95,
            retry_plan_coverage=0.95,
            current_floor_targets=retry_targets,
            retry_floor_targets=retry_targets,
        ))

    def test_maximum_coverage_retry_targets_increase_legal_allocation(self):
        """Measured shortfall targets must survive the consumer's legal cap."""
        from design.maas.book_language.capacity_alternatives import (
            capacity_retry_floor_targets,
        )
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )

        legal_sections = tuple(
            box(5.0, 5.0, 15.0, 15.0)
            for _floor_index in range(4)
        )
        contract = {
            "bcr_adjusted_floor_areas_m2": [100.0] * 4,
            "target_floor_areas_m2": [95.0] * 4,
        }
        retry_targets = capacity_retry_floor_targets(
            contract,
            {
                "target_utilization": 0.95,
                "feasible_minimum_utilization": 0.70,
            },
            {"feasible_capacity_utilization": 0.90},
        )
        source_plan = box(0.0, 0.0, 10.0, 10.0)
        source = SourceMass(
            name="maximum_coverage_consumer_probe",
            footprint=source_plan,
            volumes=(
                SourceVolume("main", source_plan, 0.0, 1.0, "geometry_program"),
            ),
            metadata={"geometry_program_bridge_evidence": {
                "program_hash": "maximum-coverage-program",
                "geometry_hash": "maximum-coverage-geometry",
            }},
        )

        initial = materialize_floorwise_legal_source(
            source,
            legal_sections=legal_sections,
            target_plan_coverage=0.95,
            target_floor_areas_m2=(95.0,) * 4,
        )
        retried = materialize_floorwise_legal_source(
            source,
            legal_sections=legal_sections,
            target_plan_coverage=0.95,
            target_floor_areas_m2=retry_targets,
        )

        self.assertEqual(retry_targets, (100.0, 100.0, 100.0, 100.0))
        self.assertIsNotNone(initial)
        self.assertIsNotNone(retried)
        assert initial is not None and retried is not None
        initial_stack = initial.metadata["floorwise_legal_matrix_stack"]
        retried_stack = retried.metadata["floorwise_legal_matrix_stack"]
        initial_total = sum(initial_stack["allocated_floor_areas_m2"])
        retried_total = sum(retried_stack["allocated_floor_areas_m2"])
        self.assertAlmostEqual(initial_total, 380.0, delta=0.01)
        self.assertAlmostEqual(retried_total, 400.0, delta=0.01)
        self.assertLessEqual(retried_total, sum(retry_targets) + 1e-6)
        self.assertGreater(retried_total, initial_total)
        self.assertEqual(retried_stack["target_plan_coverage"], 0.95)
        self.assertTrue(
            retried.metadata["floorwise_visual_projection"]["hard_pass"]
        )
        self.assertTrue(all(
            legal_sections[index].buffer(1e-7).covers(volume.footprint)
            for index, volume in enumerate(retried.volumes)
        ))
        self.assertTrue(all(
            floor["legal_csg_clip_area_m2"] == 0.0
            for floor in retried_stack["floors"]
        ))

    def test_downstream_metrics_keep_floor_contract_hash_advisory(self):
        """The floor hash remains traceable while authored volumes own legal metrics."""
        from design.maas.book_language.downstream_hard_gate import _metrics
        from design.maas.shared_floor_contract import materialize_shared_floor_contract

        site = box(0.0, 0.0, 80.0, 80.0)
        building_plate = box(0.0, 0.0, 20.0, 16.0)
        source = SourceMass(
            name="five_storey_building",
            footprint=building_plate,
            volumes=(
                SourceVolume("main", building_plate, 0.0, 1.0, "geometry_program"),
            ),
        )
        floor_contract = materialize_shared_floor_contract(
            source,
            site_local_utm=site,
            legal_sections=(site,) * 5,
            height_m=15.0,
            floors=5,
        )

        try:
            metrics = _metrics(
                source.volumes,
                site,
                height_m=15.0,
                floors=1,
                shared_floor_contract=floor_contract,
            )
        except TypeError:
            self.fail("downstream metrics do not consume shared-floor evidence")

        self.assertEqual(metrics["floor_contract_hash"], floor_contract["floor_contract_hash"])
        self.assertEqual(metrics["floor_area_m2"], 320.0)
        self.assertEqual(metrics["far_pct"], 5.0)
        self.assertEqual(metrics["height_m"], 15.0)
        self.assertEqual(
            metrics["metric_authority"],
            "visible_authored_source_volume_horizontal_slices",
        )

    def test_paid_review_pool_keeps_shared_floor_misses_for_later_legal_review(self):
        """A shared-floor miss is advisory before paid VLM and downstream gates."""
        try:
            from design.maas.book_language.portfolio_benchmark import (
                _shared_floor_hard_pass_candidates,
            )
        except ImportError:
            self.fail("portfolio has no shared-floor pre-VLM filter")

        building = SimpleNamespace(
            source=SimpleNamespace(
                metadata={
                    "shared_floor_contract": {
                        "schema_version": "arr.maas.shared_floor_contract.v1",
                        "hard_pass": True,
                        "floor_contract_hash": "building-floor-hash",
                    }
                }
            )
        )
        sculpture = SimpleNamespace(
            source=SimpleNamespace(
                metadata={
                    "shared_floor_contract": {
                        "schema_version": "arr.maas.shared_floor_contract.v1",
                        "hard_pass": False,
                        "floor_contract_hash": "sculpture-floor-hash",
                    }
                }
            )
        )
        missing = SimpleNamespace(source=SimpleNamespace(metadata={}))

        retained = _shared_floor_hard_pass_candidates((sculpture, building, missing))

        self.assertEqual(retained, [sculpture, building, missing])

    def test_smoke_pre_downstream_gate_ignores_shared_floor_advice(self):
        """Smoke MASS gating owns geometry/program validity, not capacity advice."""
        from design.maas.book_language import portfolio_benchmark

        helper = getattr(
            portfolio_benchmark,
            "_smoke_pre_downstream_candidate_pass",
            None,
        )
        self.assertIsNotNone(helper)
        assert helper is not None
        candidate = SimpleNamespace(
            source=SimpleNamespace(
                metadata={"shared_floor_contract": {"hard_pass": False}}
            )
        )

        self.assertTrue(helper(
            candidate,
            {"inside_site": True, "program_hard_pass": True},
        ))
        self.assertFalse(helper(
            candidate,
            {"inside_site": False, "program_hard_pass": True},
        ))
        self.assertFalse(helper(
            candidate,
            {"inside_site": True, "program_hard_pass": False},
        ))

    def test_downstream_uses_authored_metrics_even_when_shared_floor_gate_fails(self):
        """A floor-contract miss fails closed without replacing authored metrics."""
        from design.maas.book_language.downstream_hard_gate import _evaluate_candidate
        from design.maas.shared_floor_contract import materialize_shared_floor_contract

        site = box(-40.0, -40.0, 40.0, 40.0)
        ring = Point(0.0, 0.0).buffer(30.0, resolution=64).difference(
            Point(0.0, 0.0).buffer(29.0, resolution=64)
        )
        source = SourceMass(
            name="thin_annular_sculpture",
            footprint=ring,
            volumes=(SourceVolume("ring", ring, 0.0, 1.0, "geometry_program"),),
        )
        floor_contract = materialize_shared_floor_contract(
            source,
            site_local_utm=site,
            legal_sections=(site,) * 5,
            height_m=15.0,
            floors=5,
        )
        source.metadata["shared_floor_contract"] = floor_contract
        candidate = SimpleNamespace(
            source=source,
            feature={"properties": {"variant_id": "thin-ring"}},
            sequence=SimpleNamespace(name="thin-ring-sequence"),
            principle_id="book:test",
        )
        envelope = SimpleNamespace(
            buildable_footprint=site,
            bcr_limit=60.0,
            far_limit=250.0,
            height_limit=30.0,
            outputs_def=[],
        )

        def parking_requirement(**kwargs):
            return {
                "status": "computed",
                "required_spaces": 1,
                "accessible": {"accessible_min": 0},
                "observed_floor_area_m2": kwargs["facility_area_m2"],
            }

        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                side_effect=parking_requirement,
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {"status": "pass", "provided_spaces": 1},
                },
            ),
        ):
            row = _evaluate_candidate(
                candidate,
                site_local_utm=site,
                envelope=envelope,
                sunlight_ring=[],
                pnu="1168011800104170004",
                building_type="neighborhood",
                height_m=15.0,
                floors=5,
                rules={},
                parking_options={},
            )

        self.assertFalse(row["legal_projection"]["hard_pass"])
        self.assertTrue(row["parking_hard_gate"]["hard_pass"])
        self.assertFalse(row["semantic_projection_hard_gate"]["hard_pass"])
        self.assertFalse(row["combined_hard_pass"])
        self.assertIn(
            "shared_floor_contract_failed",
            row["legal_projection"]["failure_reasons"],
        )
        self.assertFalse(
            row["legal_projection"]["shared_floor_contract_hard_pass"],
        )
        self.assertEqual(
            row["projected_metrics"]["floor_contract_hash"],
            floor_contract["floor_contract_hash"],
        )
        self.assertEqual(
            row["parking_hard_gate"]["requirement"]["observed_floor_area_m2"],
            row["original_metrics"]["floor_area_m2"],
        )

    def test_downstream_evidence_binds_one_final_geometry_hash(self):
        from design.maas.book_language.downstream_hard_gate import (
            _evaluate_candidate,
        )

        source = _real_final_projected_source()
        geometry_hash = source.metadata["final_geometry_hash"]
        measured_gfa = round(sum(
            source.metadata["floorwise_legal_projection"][
                "achieved_floor_areas_m2"
            ]
        ), 3)
        source.metadata["shared_floor_contract"] = {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "floor_capacity_plan_hash": "shared-floor-final-source",
            "floor_contract_hash": "measured-final-floor-contract",
            "hard_pass": True,
            "failure_reasons": [],
            "identity": {"geometry_hash": geometry_hash},
            "totals": {"total_floor_area_m2": measured_gfa},
        }
        footprint = source.footprint
        candidate = SimpleNamespace(
            source=source,
            feature={"properties": {"variant_id": "final-projected"}},
            sequence=SimpleNamespace(name="final-projected-sequence"),
            principle_id="book:final",
        )
        envelope = SimpleNamespace(
            buildable_footprint=box(-20.0, -20.0, 20.0, 20.0),
            bcr_limit=60.0,
            far_limit=250.0,
            height_limit=30.0,
            outputs_def=[],
        )
        parking_calls = []

        def parking_requirement(**kwargs):
            parking_calls.append(dict(kwargs))
            return {
                "status": "computed",
                "required_spaces": 0,
                "accessible": {"accessible_min": 0},
                "observed_floor_area_m2": kwargs["facility_area_m2"],
            }

        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                side_effect=parking_requirement,
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {
                        "status": "pass",
                        "provided_spaces": 0,
                    },
                },
            ),
        ):
            row = _evaluate_candidate(
                candidate,
                site_local_utm=envelope.buildable_footprint,
                envelope=envelope,
                sunlight_ring=[],
                pnu="1168011800104170004",
                building_type="neighborhood",
                height_m=6.0,
                floors=2,
                rules={},
                parking_options={},
            )

        self.assertFalse(
            row["combined_hard_pass"],
            "final authority now also requires verified semantic projection",
        )
        self.assertFalse(
            row["semantic_projection_hard_gate"]["hard_pass"],
        )
        self.assertEqual(row["original_metrics"]["floor_area_m2"], measured_gfa)
        self.assertEqual(row["projected_metrics"]["floor_area_m2"], measured_gfa)
        self.assertEqual(len(parking_calls), 1)
        self.assertEqual(
            parking_calls[0]["facility_area_m2"],
            measured_gfa,
        )
        self.assertEqual(
            row["parking_hard_gate"]["requirement"][
                "observed_floor_area_m2"
            ],
            measured_gfa,
        )
        for bundle in (
            row["original_metrics"],
            row["projected_metrics"],
            row["legal_projection"],
            row["parking_hard_gate"],
            row["render_evidence"],
        ):
            self.assertEqual(bundle["geometry_hash"], geometry_hash)
        bridge = source.metadata["geometry_program_bridge_evidence"]
        self.assertEqual(
            bridge["raw_mesh_triangle_count"],
            len(source.surfaces),
        )
        self.assertEqual(
            bridge["exported_surface_count"],
            len(source.surfaces),
        )
        self.assertTrue(bridge["surface_export_complete"])
        self.assertEqual(
            row["render_evidence"]["surface_payload_hash"],
            bridge["surface_payload_hash"],
        )
        self.assertTrue(
            row["render_evidence"]["surface_payload_matches"],
        )

    def test_downstream_fails_closed_on_surface_payload_tamper(self):
        from design.maas.book_language.downstream_hard_gate import (
            _evaluate_candidate,
        )

        source = _real_final_projected_source()
        first_surface = source.surfaces[0]
        tampered_vertices = (
            (
                first_surface.vertices_m[0][0] + 0.25,
                first_surface.vertices_m[0][1],
                first_surface.vertices_m[0][2],
            ),
            *first_surface.vertices_m[1:],
        )
        source = replace(
            source,
            surfaces=(
                replace(first_surface, vertices_m=tampered_vertices),
                *source.surfaces[1:],
            ),
        )
        candidate = SimpleNamespace(
            source=source,
            feature={"properties": {"variant_id": "mismatched-final"}},
            sequence=SimpleNamespace(name="mismatched-final-sequence"),
            principle_id="book:final",
        )
        envelope = SimpleNamespace(
            buildable_footprint=box(-20.0, -20.0, 20.0, 20.0),
            bcr_limit=60.0,
            far_limit=250.0,
            height_limit=30.0,
            outputs_def=[],
        )
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                return_value={
                    "status": "computed",
                    "required_spaces": 0,
                    "accessible": {"accessible_min": 0},
                },
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {
                        "status": "pass",
                        "provided_spaces": 0,
                    },
                },
            ),
        ):
            row = _evaluate_candidate(
                candidate,
                site_local_utm=envelope.buildable_footprint,
                envelope=envelope,
                sunlight_ring=[],
                pnu="1168011800104170004",
                building_type="neighborhood",
                height_m=6.0,
                floors=1,
                rules={},
                parking_options={},
            )

        self.assertFalse(row["combined_hard_pass"])
        self.assertIn(
            "final_source_surface_payload_mismatch",
            row["legal_projection"]["geometry_failure_reasons"],
        )

    def test_downstream_identity_fails_closed_on_proxy_volume_tamper(self):
        from shapely.affinity import translate
        from design.maas.book_language.downstream_hard_gate import (
            _final_source_geometry_identity,
        )

        source = _real_final_projected_source()
        first = source.volumes[0]
        tampered = replace(
            source,
            volumes=(
                replace(
                    first,
                    footprint=translate(first.footprint, xoff=0.25),
                ),
                *source.volumes[1:],
            ),
        )

        _hash, failures, _render_hash, _surface_hash, _surface_match = (
            _final_source_geometry_identity(tampered)
        )

        self.assertIn(
            "final_source_proxy_volume_payload_mismatch",
            failures,
        )

    def test_downstream_identity_requires_final_proxy_volume_hash(self):
        from design.maas.book_language.downstream_hard_gate import (
            _final_source_geometry_identity,
        )

        source = _real_final_projected_source()
        metadata = dict(source.metadata)
        metadata.pop("final_proxy_volume_payload_hash")
        missing_final_hash = replace(source, metadata=metadata)

        _hash, failures, _render_hash, _surface_hash, _surface_match = (
            _final_source_geometry_identity(missing_final_hash)
        )

        self.assertIn(
            "final_source_proxy_volume_payload_incomplete",
            failures,
        )

    def test_downstream_identity_recomputes_actual_proxy_band_counts(self):
        from design.maas.book_language.downstream_hard_gate import (
            _final_source_geometry_identity,
        )

        source = _real_final_projected_source()
        self.assertEqual(
            len({
                (volume.bottom_fraction, volume.top_fraction)
                for volume in source.volumes
            }),
            3,
        )
        metadata = dict(source.metadata)
        bridge = dict(metadata["geometry_program_bridge_evidence"])
        bridge.update({
            "requested_proxy_band_count": 1,
            "exported_proxy_band_count": 1,
            "exported_proxy_part_count": 3,
            "proxy_volume_count": 3,
            "proxy_band_part_counts": [3],
        })
        metadata["geometry_program_bridge_evidence"] = bridge
        forged = replace(source, metadata=metadata)

        _hash, failures, _render_hash, _surface_hash, _surface_match = (
            _final_source_geometry_identity(forged)
        )

        self.assertIn(
            "final_source_proxy_volume_payload_incomplete",
            failures,
        )

    def test_downstream_fails_closed_on_empty_final_surface_payload(self):
        from design.maas.book_language.downstream_hard_gate import (
            _evaluate_candidate,
        )

        source = replace(_real_final_projected_source(), surfaces=())
        candidate = SimpleNamespace(
            source=source,
            feature={"properties": {"variant_id": "empty-final-surfaces"}},
            sequence=SimpleNamespace(name="empty-final-surfaces-sequence"),
            principle_id="book:final",
        )
        envelope = SimpleNamespace(
            buildable_footprint=box(-20.0, -20.0, 20.0, 20.0),
            bcr_limit=60.0,
            far_limit=250.0,
            height_limit=30.0,
            outputs_def=[],
        )
        with (
            patch(
                "design.maas.book_language.downstream_hard_gate.resolve_candidate_parking_requirement",
                return_value={
                    "status": "computed",
                    "required_spaces": 0,
                    "accessible": {"accessible_min": 0},
                },
            ),
            patch(
                "design.maas.book_language.downstream_hard_gate.infer_parking_strategy",
                return_value={
                    "selected_strategy": "surface",
                    "layout_candidate": {
                        "status": "pass",
                        "provided_spaces": 0,
                    },
                },
            ),
        ):
            row = _evaluate_candidate(
                candidate,
                site_local_utm=envelope.buildable_footprint,
                envelope=envelope,
                sunlight_ring=[],
                pnu="1168011800104170004",
                building_type="neighborhood",
                height_m=6.0,
                floors=2,
                rules={},
                parking_options={},
            )

        self.assertFalse(row["combined_hard_pass"])
        self.assertIn(
            "final_source_surface_payload_incomplete",
            row["legal_projection"]["geometry_failure_reasons"],
        )

    def test_elevation_uses_exact_shared_floor_guides(self):
        """Removing the contract must restore invented 3.3 m elevation guides."""
        from tempfile import TemporaryDirectory
        from pathlib import Path

        from design.maas.agents.elevation_agent.runtime import generate_elevation_bundle

        builder = GeometryProgramBuilder("five_storey_elevation")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 20.0, "depth": 16.0, "height": 15.0},
            semantic_role="main",
        )
        compilation = compile_geometry_program(builder.build(root))
        floor_hash = "floor-contract-123"
        floor_contract = {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "floor_contract_hash": floor_hash,
            "floor_capacity_plan_hash": "capacity-plan-123",
            "target_floor_areas_m2": [64.0, 64.0, 64.0, 48.0, 32.0],
            "capacity_alternative": {
                "requested_capacity_alternative_id": "brief_target",
                "requested_target_utilization": 0.90,
                "selectable_capacity_alternative_id": "spatial_reserve",
                "selectable_capacity_target_utilization": 0.70,
                "selectable_capacity_hard_pass": True,
            },
            "hard_pass": True,
            "plates": [
                {
                    "floor": floor,
                    "bottom_height_m": float((floor - 1) * 3),
                    "top_height_m": float(floor * 3),
                    "hard_pass": True,
                }
                for floor in range(1, 6)
            ],
        }

        try:
            with TemporaryDirectory() as directory:
                bundle = generate_elevation_bundle(
                    compilation,
                    Path(directory),
                    execution_id="five-storey-elevation",
                    shared_floor_contract=floor_contract,
                )
        except TypeError:
            self.fail("elevation runtime does not accept shared-floor evidence")

        condition = bundle["condition_pack"]
        self.assertEqual(condition["floor_contract_hash"], floor_hash)
        self.assertEqual(
            condition["floor_capacity_plan_hash"],
            "capacity-plan-123",
        )
        self.assertEqual(
            condition["identity"]["floor_capacity_plan_hash"],
            "capacity-plan-123",
        )
        self.assertEqual(
            condition["target_floor_areas_m2"],
            [64.0, 64.0, 64.0, 48.0, 32.0],
        )
        self.assertEqual(
            condition["capacity_alternative"][
                "selectable_capacity_alternative_id"
            ],
            "spatial_reserve",
        )
        self.assertEqual(condition["floor_guides_m"], [0.0, 3.0, 6.0, 9.0, 12.0, 15.0])

    def test_measured_capacity_band_reseals_shared_floor_contract(self):
        from design.maas.shared_floor_contract import (
            bind_shared_floor_contract_capacity,
        )

        original = {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "floor_contract_hash": "pre-measurement",
            "plates": [
                {"floor": 1, "hard_pass": True, "floor_contract_hash": "pre-measurement"}
            ],
            "hard_pass": True,
        }
        bound = bind_shared_floor_contract_capacity(
            original,
            {
                "requested_capacity_alternative_id": "brief_target",
                "requested_target_utilization": 0.90,
                "selectable_capacity_alternative_id": "spatial_reserve",
                "selectable_capacity_target_utilization": 0.70,
                "selectable_capacity_hard_pass": True,
            },
        )

        self.assertEqual(original["floor_contract_hash"], "pre-measurement")
        self.assertNotEqual(bound["floor_contract_hash"], "pre-measurement")
        self.assertEqual(
            bound["plates"][0]["floor_contract_hash"],
            bound["floor_contract_hash"],
        )
        self.assertEqual(
            bound["capacity_alternative"]["selectable_capacity_alternative_id"],
            "spatial_reserve",
        )

    def test_single_execution_blocks_elevation_until_floor_and_downstream_accepted(self):
        """Removing the acceptance predicate must generate elevation for a failed MASS."""
        from tempfile import TemporaryDirectory
        from pathlib import Path

        from design.maas.single_execution import execute_single_mass

        builder = GeometryProgramBuilder("five_storey_single_execution")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 20.0, "depth": 16.0, "height": 15.0},
            semantic_role="main",
        )
        program = builder.build(root)
        plates = [
            {
                "floor": floor,
                "bottom_height_m": float((floor - 1) * 3),
                "top_height_m": float(floor * 3),
                "hard_pass": True,
            }
            for floor in range(1, 6)
        ]

        def downstream(floor_pass):
            return {
                "pnu": "1168011800104170004",
                "shared_floor_contract": {
                    "schema_version": "arr.maas.shared_floor_contract.v1",
                    "floor_contract_hash": (
                        "accepted-floor-contract"
                        if floor_pass
                        else "failed-floor-contract"
                    ),
                    "hard_pass": floor_pass,
                    "failure_reasons": [] if floor_pass else ["insufficient_clear_floor_depth"],
                    "plates": plates,
                },
                "site": {"status": "passed", "pnu": "1168011800104170004"},
                "capacity": {"evaluated": True, "hard_pass": True},
                "law": {
                    "evaluated": True,
                    "hard_pass": True,
                    "status": "pass",
                },
                "parking": {"evaluated": True, "hard_pass": True},
                "program_fit": {"evaluated": True, "hard_pass": True},
                "selector": {"evaluated": True, "hard_pass": True},
            }

        with TemporaryDirectory() as directory:
            failed = execute_single_mass(
                program,
                output_root=Path(directory),
                execution_id="floor-failed",
                downstream_evidence=downstream(False),
            )
            accepted = execute_single_mass(
                program,
                output_root=Path(directory),
                execution_id="floor-accepted",
                downstream_evidence=downstream(True),
            )

        self.assertEqual(failed.passport["elevation_evidence"]["status"], "blocked")
        self.assertEqual(accepted.passport["elevation_evidence"]["status"], "generated")
        self.assertEqual(
            accepted.passport["elevation_evidence"]["condition_pack"]["floor_guides_m"],
            [0.0, 3.0, 6.0, 9.0, 12.0, 15.0],
        )

    def test_selected_passport_and_replay_preserve_the_shared_floor_contract(self):
        """Dropping the contract during archive replay must not revive invented floors."""
        from design.maas.book_language.mass_passport_bridge import (
            selected_candidate_execution_passport,
        )
        from design.maas.single_execution.replay import (
            downstream_evidence_from_passport,
        )

        floor_contract = {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "floor_contract_hash": "floor-contract-replay",
            "hard_pass": True,
            "failure_reasons": [],
            "plates": [
                {
                    "floor": floor,
                    "bottom_height_m": float((floor - 1) * 3),
                    "top_height_m": float(floor * 3),
                    "hard_pass": True,
                }
                for floor in range(1, 6)
            ],
        }
        initial_passport = {
            "schema_version": "arr.maas.mass_execution_passport.v1",
            "stages": [
                {
                    "id": stage_id,
                    "status": "not_evaluated",
                    "evidence": {},
                }
                for stage_id in (
                    "site",
                    "capacity",
                    "law",
                    "parking",
                    "program_fit",
                    "selector",
                    "vlm",
                )
            ],
            "activation_graph": {"nodes": [], "edges": []},
        }
        archived = selected_candidate_execution_passport(
            compilation={"execution_passport": initial_passport},
            downstream_row={},
            source_metadata={
                "shared_floor_contract": floor_contract,
                "capacity_alternative_projection": {"minimum_utilization": 0.7},
                "source_capacity_measurement": {"hard_pass": True},
            },
            program_evidence={"evaluated": True, "hard_pass": True},
            descriptor={"capacity_target_hard_pass": True},
            pnu="1168011800104170004",
        )

        replay = downstream_evidence_from_passport(archived)

        self.assertEqual(
            replay["shared_floor_contract"]["floor_contract_hash"],
            floor_contract["floor_contract_hash"],
        )
        self.assertEqual(
            replay["capacity"]["floor_contract_hash"],
            floor_contract["floor_contract_hash"],
        )

    def test_selected_passport_rejects_false_or_missing_required_floor_contract(self):
        """A selected MASS cannot revive after its required floor contract fails."""
        from design.maas.book_language.mass_passport_bridge import (
            selected_candidate_execution_passport,
        )

        initial_passport = {
            "schema_version": "arr.maas.mass_execution_passport.v1",
            "stages": [
                {
                    "id": stage_id,
                    "status": "passed",
                    "required_for_final": True,
                    "evidence": {"evaluated": True, "hard_pass": True},
                }
                for stage_id in (
                    "site",
                    "capacity",
                    "law",
                    "parking",
                    "program_fit",
                    "selector",
                )
            ],
            "activation_graph": {"nodes": [], "edges": []},
        }
        failed_contract = {
            "schema_version": "arr.maas.shared_floor_contract.v1",
            "floor_contract_hash": "failed-floor-contract",
            "floor_capacity_plan_hash": "floor-plan-1",
            "hard_pass": False,
            "failure_reasons": ["insufficient_clear_floor_depth"],
        }

        for label, contract in (
            ("false", failed_contract),
            ("missing", None),
        ):
            with self.subTest(shared_floor_contract=label):
                metadata = {
                    "capacity_alternative_projection": {
                        "alternative_id": "spatial_reserve",
                        "target_utilization": 0.8,
                        "target_hard_pass": True,
                    },
                    "source_capacity_measurement": {
                        "utilization_ratio": 0.8,
                        "hard_pass": True,
                    },
                }
                if contract is not None:
                    metadata["shared_floor_contract"] = contract
                passport = selected_candidate_execution_passport(
                    compilation={"execution_passport": initial_passport},
                    downstream_row={
                        "legal_projection": {
                            "evaluated": True,
                            "hard_pass": True,
                        },
                        "parking_hard_gate": {
                            "evaluated": True,
                            "hard_pass": True,
                        },
                    },
                    source_metadata=metadata,
                    program_evidence={"evaluated": True, "hard_pass": True},
                    descriptor={"capacity_target_hard_pass": True},
                    pnu="1168011800104170004",
                )
                capacity = next(
                    stage
                    for stage in passport["stages"]
                    if stage["id"] == "capacity"
                )
                self.assertEqual(capacity["status"], "failed")
                self.assertFalse(capacity["evidence"]["hard_pass"])
                self.assertFalse(
                    capacity["evidence"][
                        "shared_floor_contract_hard_pass"
                    ]
                )

    def test_selected_passport_capacity_uses_resolved_selectable_band(self):
        from design.maas.book_language.mass_passport_bridge import (
            selected_candidate_execution_passport,
        )

        initial_passport = {
            "schema_version": "arr.maas.mass_execution_passport.v1",
            "stages": [
                {
                    "id": stage_id,
                    "status": "not_evaluated",
                    "evidence": {},
                }
                for stage_id in (
                    "site",
                    "capacity",
                    "law",
                    "parking",
                    "program_fit",
                    "selector",
                    "vlm",
                )
            ],
            "activation_graph": {"nodes": [], "edges": []},
        }
        archived = selected_candidate_execution_passport(
            compilation={"execution_passport": initial_passport},
            downstream_row={},
            source_metadata={
                "shared_floor_contract": {
                    "schema_version": "arr.maas.shared_floor_contract.v1",
                    "floor_contract_hash": "selectable-floor-contract",
                    "hard_pass": True,
                    "failure_reasons": [],
                },
                "capacity_alternative_projection": {
                    "alternative_id": "maximum_feasible",
                    "target_hard_pass": False,
                    "feasible_minimum_utilization": 0.70,
                    "requested_capacity_alternative_id": "maximum_feasible",
                    "requested_target_utilization": 0.95,
                    "selectable_capacity_alternative_id": "balanced_yield",
                    "selectable_capacity_target_utilization": 0.80,
                    "selectable_capacity_hard_pass": True,
                },
                "source_capacity_measurement": {
                    "schema_version": "arr.maas.source_capacity_measurement.v1",
                    "feasible_capacity_utilization": 0.8241,
                },
            },
            program_evidence={"evaluated": True, "hard_pass": True},
            descriptor={"capacity_target_hard_pass": False},
            pnu="1168011800104170004",
        )

        capacity = next(
            stage for stage in archived["stages"] if stage["id"] == "capacity"
        )
        self.assertEqual(capacity["status"], "passed")
        self.assertFalse(capacity["evidence"]["requested_target_hard_pass"])
        self.assertEqual(
            capacity["evidence"]["resolved_capacity_alternative_id"],
            "balanced_yield",
        )
        self.assertEqual(
            capacity["evidence"]["resolved_capacity_target_utilization"],
            0.80,
        )
        self.assertTrue(capacity["evidence"]["resolved_capacity_hard_pass"])
        self.assertTrue(capacity["evidence"]["hard_pass"])

    def test_resolved_selectable_capacity_requires_achieving_its_exact_target(self):
        from design.maas.book_language.mass_passport_bridge import (
            resolve_capacity_band_evidence,
        )

        cases = (
            ("spatial_reserve", 0.70, 0.70, True),
            ("balanced_yield", 0.80, 0.75, False),
            ("balanced_yield", 0.80, 0.8241, True),
            ("tampered_zero_target", 0.0, 0.70, False),
        )
        for alternative_id, target, achieved, expected in cases:
            with self.subTest(
                alternative_id=alternative_id,
                target=target,
                achieved=achieved,
            ):
                resolved = resolve_capacity_band_evidence(
                    {
                        "selectable_capacity_alternative_id": alternative_id,
                        "selectable_capacity_target_utilization": target,
                        "selectable_capacity_hard_pass": True,
                        "feasible_minimum_utilization": 0.70,
                    },
                    capacity_measurement={
                        "feasible_capacity_utilization": achieved,
                    },
                )

                self.assertEqual(
                    resolved["resolved_capacity_hard_pass"],
                    expected,
                )

    def test_requested_capacity_band_requires_measured_aggregate_utilization(self):
        from design.maas.book_language.mass_passport_bridge import (
            resolve_capacity_band_evidence,
        )

        projection = {
            "requested_capacity_alternative_id": "brief_target",
            "requested_target_utilization": 0.80,
            "target_hard_pass": True,
            "feasible_minimum_utilization": 0.70,
        }
        cases = (
            ("below_minimum", {}, False),
            (
                "below_minimum",
                {"feasible_capacity_utilization": 0.69},
                False,
            ),
            (
                "missed_requested_band",
                {"feasible_capacity_utilization": 0.75},
                False,
            ),
            (
                "measured_requested_band",
                {"feasible_capacity_utilization": 0.8241},
                True,
            ),
        )
        for label, measurement, expected in cases:
            with self.subTest(label=label):
                resolved = resolve_capacity_band_evidence(
                    projection,
                    capacity_measurement=measurement,
                )

                self.assertEqual(
                    resolved["resolved_capacity_hard_pass"],
                    expected,
                )
                self.assertEqual(
                    resolved["achieved_capacity_utilization"],
                    float(
                        measurement.get("feasible_capacity_utilization")
                        or 0.0
                    ),
                )

    def test_capacity_minimum_comes_from_program_specific_authority(self):
        from design.maas.book_language.mass_passport_bridge import (
            resolve_capacity_band_evidence,
        )

        cases = (
            ("neighborhood", 0.70, 0.70, True),
            ("cultural", 0.40, 0.40, True),
            ("missing", None, 0.80, False),
            ("nonfinite", float("nan"), 0.80, False),
        )
        for label, minimum, achieved, expected in cases:
            projection = {
                "requested_capacity_alternative_id": f"{label}-band",
                "requested_target_utilization": (
                    float(minimum)
                    if minimum is not None
                    else 0.40
                ),
                "target_hard_pass": True,
            }
            if minimum is not None:
                projection["feasible_minimum_utilization"] = minimum
            with self.subTest(label=label):
                resolved = resolve_capacity_band_evidence(
                    projection,
                    capacity_measurement={
                        "feasible_capacity_utilization": achieved,
                    },
                )

                self.assertEqual(
                    resolved["resolved_capacity_hard_pass"],
                    expected,
                )

    def test_certified_passport_does_not_fabricate_missing_vlm_image_binding(self):
        from design.maas.book_language.mass_passport_bridge import (
            selected_candidate_execution_passport,
        )

        builder = GeometryProgramBuilder("certified_vlm_passport")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 10.0, "depth": 8.0, "height": 12.0},
            semantic_role="main",
        )
        program = builder.build(root)
        compilation = compile_geometry_program(program)
        certified_hash = "a" * 64
        certified = replace(compilation, geometry_hash=certified_hash)

        archived = selected_candidate_execution_passport(
            compilation={
                "certified_compilation": certified,
                "combined_hard_pass": True,
            },
            downstream_row={},
            source_metadata={
                "final_book_vlm_audit": {
                    "schema_version": "arr.maas.final_book_vlm_audit.v1",
                    "status": "pass",
                    "hard_pass": True,
                    "model": "review-model",
                    "response_id": "review-response",
                    "concept_scores": {"gesture_clarity": 0.81},
                    "vlm_image_inputs": {
                        "candidate": {
                            "sha256": "d" * 64,
                            "used_by_vlm": True,
                        },
                    },
                    "evidence_binding": {
                        "geometry_hash": "stale-capacity-hash",
                    },
                },
            },
            program_evidence={"evaluated": True, "hard_pass": True},
            descriptor={},
            pnu="1168011800104170004",
        )

        vlm = next(stage for stage in archived["stages"] if stage["id"] == "vlm")
        self.assertEqual(vlm["status"], "not_evaluated")
        self.assertFalse(vlm["evidence"]["hard_pass"])
        self.assertEqual(vlm["evidence"].get("model"), "review-model")
        self.assertEqual(vlm["evidence"].get("response_id"), "review-response")
        self.assertEqual(
            vlm["evidence"].get("concept_scores"),
            {"gesture_clarity": 0.81},
        )
        self.assertEqual(
            (vlm["evidence"].get("image_inputs") or {}).get("candidate", {}).get(
                "sha256"
            ),
            "d" * 64,
        )
        self.assertEqual(vlm["evidence"].get("binding_status"), "unbound")
        self.assertEqual(
            (vlm["evidence"].get("source_audit") or {}).get("response_id"),
            "review-response",
        )
        self.assertNotIn(
            "program_hash",
            vlm["evidence"]["evidence_binding"],
        )
        self.assertEqual(
            vlm["evidence"]["evidence_binding"]["geometry_hash"],
            "stale-capacity-hash",
        )

    def test_certified_passport_rejects_mismatched_vlm_input_image_digest(self):
        from design.maas.book_language.mass_passport_bridge import (
            selected_candidate_execution_passport,
        )

        builder = GeometryProgramBuilder("certified_vlm_digest_mismatch")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 10.0, "depth": 8.0, "height": 12.0},
            semantic_role="main",
        )
        program = builder.build(root)
        compilation = compile_geometry_program(program)
        certified_hash = "b" * 64
        certified = replace(
            compilation,
            geometry_hash=certified_hash,
            metrics={
                **compilation.metrics,
                "geometry_authority": "certified_projected_visual_mesh",
            },
        )

        with TemporaryDirectory() as temporary:
            board = Path(temporary) / "board.png"
            Image.new("RGB", (32, 24), (220, 120, 50)).save(board)
            archived = selected_candidate_execution_passport(
                compilation={
                    "certified_compilation": certified,
                    "combined_hard_pass": True,
                    "archive_render_evidence": {
                        "board_png": str(board),
                        "hard_pass": True,
                        "crop_box": [0, 0, 32, 24],
                        "projected_visual_geometry_hash": certified_hash,
                    },
                },
                downstream_row={},
                source_metadata={
                    "final_book_vlm_audit": {
                        "schema_version": "arr.maas.final_book_vlm_audit.v1",
                        "status": "pass",
                        "hard_pass": True,
                        "model": "review-model",
                        "response_id": "review-response",
                        "concept_scores": {"gesture_clarity": 0.73},
                        "vlm_image_inputs": {
                            "candidate": {
                                "sha256": "c" * 64,
                                "used_by_vlm": True,
                            },
                        },
                        "evidence_binding": {
                            "schema_version": "arr.maas.vlm_evidence_binding.v1",
                            "program_hash": program.program_hash(),
                            "geometry_hash": certified_hash,
                            "geometry_authority": (
                                "certified_projected_visual_mesh"
                            ),
                            "candidate_sha256": "c" * 64,
                        },
                    },
                },
                program_evidence={"evaluated": True, "hard_pass": True},
                descriptor={},
                pnu="1168011800104170004",
            )

        vlm = next(stage for stage in archived["stages"] if stage["id"] == "vlm")
        self.assertEqual(vlm["status"], "not_evaluated")
        self.assertFalse(vlm["evidence"]["hard_pass"])
        self.assertEqual(
            vlm["evidence"]["reason"],
            "certified_vlm_input_image_digest_mismatch",
        )
        self.assertEqual(vlm["evidence"].get("model"), "review-model")
        self.assertEqual(vlm["evidence"].get("response_id"), "review-response")
        self.assertEqual(
            vlm["evidence"].get("concept_scores"),
            {"gesture_clarity": 0.73},
        )
        self.assertEqual(
            (vlm["evidence"].get("image_inputs") or {}).get("candidate", {}).get(
                "sha256"
            ),
            "c" * 64,
        )
        self.assertEqual(vlm["evidence"].get("binding_status"), "unbound")
        self.assertEqual(
            (vlm["evidence"].get("source_audit") or {}).get("response_id"),
            "review-response",
        )

    def test_vlm_repair_rematerializes_floor_identity_for_the_repaired_geometry(self):
        """A typed VLM repair must not retain its parent's floor/hash evidence."""
        from design.test_task5_regression_fixtures import (
            legal_generation_context_for_site,
        )

        try:
            from design.maas.book_language.vlm_review import (
                _materialize_repaired_floor_contract,
            )
        except ImportError:
            self.fail("VLM repair has no shared-floor rematerialization")

        builder = GeometryProgramBuilder("vlm_repaired_building")
        root = builder.add(
            "primitive",
            "box",
            parameters={"width": 20.0, "depth": 16.0, "height": 15.0},
            semantic_role="main",
        )
        program = builder.build(root)
        compilation = compile_geometry_program(program)
        site = box(-40.0, -40.0, 40.0, 40.0)
        plate = box(-10.0, -8.0, 10.0, 8.0)
        source = SourceMass(
            name="vlm_repaired_building",
            footprint=plate,
            volumes=(SourceVolume("main", plate, 0.0, 1.0, "geometry_program"),),
        )

        with patch(
            "design.maas.book_language.vlm_review.generation_site_at_height",
            return_value=site,
        ):
            floor_contract = _materialize_repaired_floor_contract(
                source,
                generation_context=legal_generation_context_for_site(site),
                capacity_site=site,
                height=15.0,
                floors=5,
                base_capacity_contract={"feasible_maximum_floor_area_m2": 2000.0},
                repaired_program=program,
                repaired_compilation=compilation,
            )

        self.assertTrue(floor_contract["hard_pass"])
        self.assertEqual(
            floor_contract["identity"]["program_hash"],
            program.program_hash(),
        )
        self.assertEqual(
            floor_contract["identity"]["geometry_hash"],
            compilation.geometry_hash,
        )
