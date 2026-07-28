import os

from django.test import SimpleTestCase
from dataclasses import replace
from shapely.geometry import LineString, MultiPoint, Point, Polygon, box, mapping
from shapely.geometry.polygon import orient
from types import SimpleNamespace
from unittest.mock import patch

from design.maas.geometry_language.source_bridge import _mesh_section_polygon
from design.maas.geometry_language import GeometryProgramBuilder, compile_geometry_program
from design.maas.geometry_language.gate import compilation_gate
from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume


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
    raw_mesh_triangle_count: int = 1,
    exported_surface_count: int = 1,
) -> SourceMass:
    origin = footprint.centroid
    surface = SourceSurface(
        role="mesh_triangle",
        volume_role="recursive_primary",
        verb="geometry_program",
        surface_type="profiled_recursive_solid_mesh",
        vertices_m=tuple(
            (x - float(origin.x), y - float(origin.y), z)
            for x, y, z in world_vertices
        ),
        operator="loft",
        semantic_patch_id="recursive_primary:profiled_triangle",
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
        surfaces=(surface,),
        metadata={"geometry_program_bridge_evidence": {
            "status": "materialized",
            "program_hash": f"{name}-program",
            "geometry_hash": f"{name}-geometry",
            "authoritative_visual_geometry": "manifold_compilation_mesh",
            "raw_mesh_triangle_count": raw_mesh_triangle_count,
            "exported_surface_count": exported_surface_count,
            "surface_coordinate_frame": "source_footprint_centroid_local",
        }},
    )


class SharedFloorContractTests(SimpleTestCase):
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
        lower_center, upper_center = [
            volume.footprint.centroid for volume in shifted_stack.volumes
        ]
        self.assertAlmostEqual(upper_center.x - lower_center.x, 4.0, delta=0.01)
        self.assertGreater(
            intrinsic_silhouette_distance(centered_stack, shifted_stack),
            DEFAULT_NOVELTY_POLICY.visual_silhouette_repeat,
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
            triangles = tuple(
                triangle
                for index in range(4)
                for next_index in ((index + 1) % 4,)
                for triangle in (
                    (index, next_index, 4 + next_index),
                    (index, 4 + next_index, 4 + index),
                )
            )
            surfaces = tuple(
                SourceSurface(
                    role=f"mesh_{index}",
                    volume_role="recursive_primary",
                    verb="geometry_program",
                    surface_type="profiled_recursive_solid_mesh",
                    vertices_m=tuple(vertices[vertex] for vertex in triangle),
                    operator="loft",
                    semantic_patch_id="recursive_primary:loft_side",
                )
                for index, triangle in enumerate(triangles)
            )
            # Both sources deliberately expose the same conservative proxy.
            # Only the authored mesh records the upper-level shift.
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
                    "program_hash": name,
                    "geometry_hash": name,
                    "authoritative_visual_geometry": "manifold_compilation_mesh",
                    "raw_mesh_triangle_count": len(triangles),
                    "exported_surface_count": len(surfaces),
                }},
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
        shifted_centers = [
            volume.footprint.centroid.x for volume in shifted.volumes
        ]
        self.assertGreater(shifted_centers[1] - shifted_centers[0], 1.5)
        self.assertGreater(
            intrinsic_silhouette_distance(centered, shifted),
            DEFAULT_NOVELTY_POLICY.visual_silhouette_repeat,
        )

    def test_floorwise_visual_projection_preserves_authored_mesh(self):
        """Erasing projected mesh surfaces must not collapse authored shift twins."""
        from design.maas.geometry_language.source_bridge import (
            materialize_floorwise_legal_source,
        )
        from design.maas.program_massing.morphology import (
            intrinsic_silhouette_distance,
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
        self.assertTrue(centered.surfaces)
        self.assertTrue(shifted.surfaces)
        self.assertNotEqual(
            centered_certificate["visual_hash"],
            shifted_certificate["visual_hash"],
        )
        self.assertGreater(
            intrinsic_silhouette_distance(centered, shifted),
            0.10,
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
        self.assertEqual(result.certificate.projected_surface_count, 1)
        self.assertEqual(len(result.surfaces), 1)

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

    def test_smoke_search_stops_only_on_a_floor_valid_base_lineage(self):
        """A descendant without its BOOK base must not terminate smoke search."""
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
            metadata={
                "book_generation_lineage": {
                    "stage": "base",
                    "parent_key": "base-key",
                }
            }
        )
        descendant = SimpleNamespace(
            metadata={
                "book_generation_lineage": {
                    "stage": "combination",
                    "parent_key": "base-key",
                }
            }
        )

        self.assertTrue(
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
        self.assertTrue(
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

    def test_candidate_capacity_retry_measures_the_same_five_floor_contract(self):
        """Plan-fit retries must not use the old three-band volume estimate."""
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
                generation_context=SimpleNamespace(),
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

    def test_capacity_retry_selects_only_a_floor_safe_measured_improvement(self):
        """A tiny shortfall should accept a plain refit without forcing a pack."""
        try:
            from design.maas.book_language.candidate_generation import (
                _capacity_retry_result_is_selectable,
            )
        except ImportError:
            self.fail("capacity retry has no floor-safe selection predicate")

        initial = {"feasible_capacity_utilization": 0.6972}
        improved = {"feasible_capacity_utilization": 0.7010}

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
                {"feasible_capacity_utilization": 0.6960},
                initial,
            )
        )

    def test_downstream_metrics_use_the_same_floor_contract_area_and_hash(self):
        """Removing the contract argument must make FAR fall back to volume sampling."""
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
        self.assertEqual(metrics["floor_area_m2"], 1600.0)
        self.assertEqual(metrics["far_pct"], 25.0)
        self.assertEqual(metrics["height_m"], 15.0)

    def test_paid_review_pool_excludes_candidates_without_shared_floor_hard_pass(self):
        """Removing the pre-VLM floor filter must send a sculpture to paid review."""
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

        self.assertEqual(retained, [building])

    def test_downstream_rejects_failed_floor_contract_and_uses_its_parking_area(self):
        """Removing floor-contract propagation must let the ring pass downstream."""
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

        self.assertFalse(row["combined_hard_pass"])
        self.assertIn(
            "shared_floor_contract_failed",
            row["legal_projection"]["failure_reasons"],
        )
        self.assertEqual(
            row["projected_metrics"]["floor_contract_hash"],
            floor_contract["floor_contract_hash"],
        )
        self.assertEqual(
            row["parking_hard_gate"]["requirement"]["observed_floor_area_m2"],
            floor_contract["totals"]["total_floor_area_m2"],
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
                "law": {"evaluated": True, "hard_pass": True},
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

    def test_vlm_repair_rematerializes_floor_identity_for_the_repaired_geometry(self):
        """A typed VLM repair must not retain its parent's floor/hash evidence."""
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
                generation_context=SimpleNamespace(),
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
