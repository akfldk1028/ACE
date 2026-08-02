"""Contracts for constant-per-floor legal CSG projection."""

from copy import deepcopy
from math import hypot

from django.test import SimpleTestCase
from shapely.affinity import rotate, scale
from shapely.geometry import LineString, Polygon, box
from shapely.ops import polygonize, unary_union

from design.maas.geometry_language import (
    FloorwiseLegalProgramResult,
    append_floorwise_legal_projection,
    base_seed_programs,
    compilation_gate,
    compile_geometry_program,
)
from design.maas.geometry_language.authored_legal_preservation import (
    AuthoredLegalPreservationResult,
    certify_authored_affine_program,
)
from design.maas.geometry_language.affine_matrix import identity_matrix4
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.legal_field_affine_placement import (
    is_intentional_floorwise_stepped_program,
    select_legal_field_affine_projection,
)
from design.maas.geometry_language.source_bridge import (
    HostFitTransform,
    append_site_placement_matrix,
    compile_site_bound_geometry_program_to_source_mass,
    derive_host_fit_transform,
)


def _section_polygon(compilation, z: float):
    contours = tuple(compilation._solid.slice(float(z)).to_polygons())
    section = None
    for contour in contours:
        polygon = Polygon(tuple(
            (float(point[0]), float(point[1]))
            for point in contour
        ))
        if polygon.is_empty or not polygon.is_valid or polygon.area <= 1e-10:
            continue
        section = (
            polygon
            if section is None
            else section.symmetric_difference(polygon)
        )
    if section is not None and not section.is_empty:
        return section

    segments = []
    epsilon = 1e-7
    for triangle in compilation.triangles:
        points = [compilation.vertices[index] for index in triangle]
        intersections = []
        for left, right in zip(points, (*points[1:], points[0])):
            left_z, right_z = left[2] - z, right[2] - z
            if abs(left_z) <= epsilon:
                intersections.append((left[0], left[1]))
            if left_z * right_z < -(epsilon * epsilon):
                amount = (z - left[2]) / (right[2] - left[2])
                intersections.append((
                    left[0] + (right[0] - left[0]) * amount,
                    left[1] + (right[1] - left[1]) * amount,
                ))
        unique = []
        for point in intersections:
            if not any(
                hypot(point[0] - other[0], point[1] - other[1]) <= 1e-6
                for other in unique
            ):
                unique.append(point)
        if len(unique) >= 2:
            segment = tuple(
                (round(float(point[0]), 8), round(float(point[1]), 8))
                for point in unique[:2]
            )
            if segment[0] != segment[1]:
                segments.append(LineString(segment))
    polygons = tuple(polygonize(unary_union(segments)))
    if not polygons:
        return None
    hole_regions = tuple(
        Polygon(interior)
        for polygon in polygons
        for interior in polygon.interiors
    )
    retained = tuple(
        polygon
        for polygon in polygons
        if not any(
            hole.covers(polygon.representative_point())
            for hole in hole_regions
        )
    )
    return unary_union(retained or polygons)


def _placed_u_program():
    unit = GeometryNode(
        "unit_box",
        "primitive",
        "box",
        parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
    )
    four_floor_slab = GeometryNode(
        "four_floor_slab",
        "transform",
        "matrix4",
        inputs=(unit.id,),
        parameters={
            "matrix4": [
                [14.0, 0.0, 0.0, 0.0],
                [0.0, 10.0, 0.0, 0.0],
                [0.0, 0.0, 12.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        },
    )
    u_root = GeometryNode(
        "authored_u",
        "macro",
        "courtyard",
        inputs=(four_floor_slab.id,),
        parameters={"margin_ratio": 0.24, "open_side": "east"},
        semantic_role="authored_basevolume",
    )
    authored = GeometryProgram(
        (unit, four_floor_slab, u_root),
        u_root.id,
        "four_floor_authored_u",
        metadata={"base_volume_scope": "1/1", "family": "open_courtyard"},
    )
    host = rotate(
        box(30.0, 50.0, 50.0, 65.0),
        17.0,
        origin=(40.0, 57.5),
    )
    compilation = compile_geometry_program(authored)
    fit = derive_host_fit_transform(
        compilation,
        host,
        target_plan_area=97.784,
    )
    return append_site_placement_matrix(authored, fit), host


def _placed_bent_offset_program():
    unit = GeometryNode(
        "unit_box",
        "primitive",
        "box",
        parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
    )
    horizontal = GeometryNode(
        "bent_horizontal",
        "transform",
        "matrix4",
        inputs=(unit.id,),
        parameters={
            "matrix4": [
                [8.0, 0.0, 0.0, 0.0],
                [0.0, 4.0, 0.0, 0.0],
                [0.0, 0.0, 8.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        },
        semantic_role="authored_horizontal_bar",
    )
    offset = GeometryNode(
        "bent_offset",
        "transform",
        "matrix4",
        inputs=(unit.id,),
        parameters={
            "matrix4": [
                [4.0, 0.0, 0.0, 4.0],
                [0.0, 8.0, 0.0, 2.0],
                [0.0, 0.0, 8.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        },
        semantic_role="authored_offset_bar",
    )
    bent_root = GeometryNode(
        "authored_bent_offset",
        "boolean",
        "union",
        inputs=(horizontal.id, offset.id),
        semantic_role="authored_bent_offset_relation",
    )
    authored = GeometryProgram(
        (unit, horizontal, offset, bent_root),
        bent_root.id,
        "authored_bent_offset",
        metadata={"base_volume_scope": "1/1", "family": "bent_offset"},
    )
    legal = box(-10.0, -10.0, 30.0, 30.0)
    fit = derive_host_fit_transform(
        compile_geometry_program(authored),
        legal,
        target_plan_area=72.0,
    )
    return append_site_placement_matrix(authored, fit), legal


def _with_live_step(
    placed_program: GeometryProgram,
    *,
    setback_ratio: float = 0.08,
) -> GeometryProgram:
    step = GeometryNode(
        "authored_intentional_step",
        "macro",
        "stepped_mass",
        inputs=(placed_program.root_id,),
        parameters={
            "levels": 4,
            "setback_ratio": setback_ratio,
            "direction": "x",
        },
        semantic_role="authored_intentional_stepped_body",
    )
    return GeometryProgram(
        (*placed_program.nodes, step),
        step.id,
        f"{placed_program.name}_intentional_step",
        metadata=deepcopy(placed_program.metadata),
    )


class AuthoredLegalPreservationTests(SimpleTestCase):
    def test_affine_selector_prefers_unchanged_preservation(self):
        block = next(
            program
            for program in base_seed_programs()
            if str(
                (program.metadata.get("base_seed") or {}).get("seed_id")
                or ""
            )
            == "block"
        )

        selected = select_legal_field_affine_projection(
            block,
            legal_sections=(box(0.0, 0.0, 20.0, 20.0),),
            target_floor_areas_m2=(100.0,),
            floor_capacity_plan_hash="capacity-plan:selector-preserves",
        )

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(
            selected.projection.certificate["projection_mode"],
            "authored_affine_preserved",
        )
        self.assertFalse(any(
            node.semantic_role == "final_floorwise_legal_solid"
            for node in selected.projection.program.nodes
        ))
        self.assertEqual(
            selected.evidence["projection_mode"],
            "authored_affine_preserved",
        )

    def test_only_explicit_stepped_ast_is_floorwise_csg_eligible(self):
        nonstepped, _legal = _placed_bent_offset_program()
        unit = GeometryNode(
            "unit_box",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        stepped = GeometryNode(
            "authored_setback",
            "macro",
            "setback",
            inputs=(unit.id,),
            parameters={"levels": 3, "setback_ratio": 0.1},
        )
        stepped_program = GeometryProgram(
            (unit, stepped),
            stepped.id,
            "authored_setback",
        )

        self.assertFalse(
            is_intentional_floorwise_stepped_program(nonstepped)
        )
        self.assertTrue(
            is_intentional_floorwise_stepped_program(stepped_program)
        )

    def test_preserves_nonstepped_authored_program_inside_constant_sections(self):
        placed, legal = _placed_bent_offset_program()

        result = certify_authored_affine_program(
            placed,
            legal_sections=(legal, legal),
            target_floor_areas_m2=(60.0, 60.0),
            floor_capacity_plan_hash="capacity-plan:authored-bent",
        )

        self.assertIsInstance(result, AuthoredLegalPreservationResult)
        assert result is not None
        self.assertIs(result.program, placed)
        self.assertEqual(result.program.program_hash(), placed.program_hash())
        self.assertEqual(
            result.certificate["projection_mode"],
            "authored_affine_preserved",
        )
        self.assertTrue(result.certificate["all_sections_contained"])
        self.assertGreaterEqual(
            sum(result.achieved_floor_areas_m2),
            120.0 * 0.995,
        )
        self.assertEqual(
            len(result.certificate["floor_evidence"]),
            2,
        )
        self.assertTrue(all(
            evidence["containment_margin_m"] >= 0.0
            for evidence in result.certificate["floor_evidence"]
        ))

    def test_preserves_courtyard_mesh_inside_shrinking_legal_sections(self):
        placed, host = _placed_u_program()
        before = compile_geometry_program(placed)
        shrinking_sections = tuple(
            scale(host, xfact=factor, yfact=factor)
            for factor in (1.0, 0.98, 0.96, 0.94)
        )

        result = certify_authored_affine_program(
            placed,
            legal_sections=shrinking_sections,
            target_floor_areas_m2=(90.0, 90.0, 90.0, 90.0),
            floor_capacity_plan_hash="capacity-plan:authored-courtyard",
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.final_compilation.geometry_hash, before.geometry_hash)
        self.assertEqual(result.final_compilation.vertices, before.vertices)
        self.assertEqual(result.final_compilation.triangles, before.triangles)
        self.assertEqual(
            result.certificate["final_geometry_hash"],
            before.geometry_hash,
        )

    def test_rejects_authored_program_outside_exact_legal_section(self):
        placed, _legal = _placed_bent_offset_program()
        outside = box(1000.0, 1000.0, 1010.0, 1010.0)

        result = certify_authored_affine_program(
            placed,
            legal_sections=(outside, outside),
            target_floor_areas_m2=(1.0, 1.0),
            floor_capacity_plan_hash="capacity-plan:outside",
        )

        self.assertIsNone(result)

    def test_rejects_authored_program_below_capacity_threshold(self):
        placed, legal = _placed_bent_offset_program()

        result = certify_authored_affine_program(
            placed,
            legal_sections=(legal, legal),
            target_floor_areas_m2=(80.0, 80.0),
            floor_capacity_plan_hash="capacity-plan:short",
        )

        self.assertIsNone(result)

    def test_rejects_twisted_prism_that_exits_legal_section_between_samples(self):
        unit = GeometryNode(
            "unit_box",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        prism = GeometryNode(
            "four_by_one_prism",
            "transform",
            "matrix4",
            inputs=(unit.id,),
            parameters={
                "matrix4": [
                    [4.0, 0.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0, 0.0],
                    [0.0, 0.0, 4.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ],
            },
        )
        twist = GeometryNode(
            "authored_half_turn",
            "modifier",
            "twist",
            inputs=(prism.id,),
            parameters={
                "axis": "z",
                "angle_degrees": 180.0,
                "subdivisions": 6,
            },
        )
        authored = GeometryProgram(
            (unit, prism, twist),
            twist.id,
            "twisted_prism_counterexample",
        )
        compilation = compile_geometry_program(authored)
        identity = identity_matrix4()
        placed = append_site_placement_matrix(
            authored,
            HostFitTransform(
                matrix4=identity,
                inverse_matrix4=identity,
                world_vertices=compilation.vertices,
                achieved_plan_area_m2=4.0,
            ),
        )
        placed_compilation = compile_geometry_program(placed)
        sampled_sections = tuple(
            _section_polygon(placed_compilation, z)
            for z in (0.0001, 2.0, 3.9999)
        )
        self.assertTrue(all(section is not None for section in sampled_sections))
        legal = unary_union(sampled_sections).buffer(0.01, join_style=2)
        self.assertIsInstance(legal, Polygon)
        between_samples = _section_polygon(placed_compilation, 1.0)
        self.assertIsNotNone(between_samples)
        self.assertFalse(legal.covers(between_samples))
        self.assertGreater(
            between_samples.difference(legal).area,
            2.0,
        )

        result = certify_authored_affine_program(
            placed,
            legal_sections=(legal,),
            target_floor_areas_m2=(3.9,),
            floor_capacity_plan_hash="capacity-plan:twist-counterexample",
        )

        self.assertIsNone(result)

    def test_rejects_vertical_box_occupying_a_middle_floor_legal_hole(self):
        unit = GeometryNode(
            "unit_box",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        box_2x2x3 = GeometryNode(
            "box_2x2x3",
            "transform",
            "matrix4",
            inputs=(unit.id,),
            parameters={
                "matrix4": [
                    [2.0, 0.0, 0.0, 0.0],
                    [0.0, 2.0, 0.0, 0.0],
                    [0.0, 0.0, 3.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ],
            },
        )
        authored = GeometryProgram(
            (unit, box_2x2x3),
            box_2x2x3.id,
            "three_floor_vertical_box",
        )
        compilation = compile_geometry_program(authored)
        identity = identity_matrix4()
        placed = append_site_placement_matrix(
            authored,
            HostFitTransform(
                matrix4=identity,
                inverse_matrix4=identity,
                world_vertices=compilation.vertices,
                achieved_plan_area_m2=4.0,
            ),
        )
        full_legal = box(-0.1, -0.1, 2.1, 2.1)
        excluded_center = box(0.75, 0.75, 1.25, 1.25)
        middle_legal = Polygon(
            full_legal.exterior.coords,
            holes=(excluded_center.exterior.coords,),
        )
        actual_middle = _section_polygon(
            compile_geometry_program(placed),
            1.5,
        )
        self.assertIsNotNone(actual_middle)
        self.assertFalse(middle_legal.covers(actual_middle))
        self.assertAlmostEqual(
            actual_middle.difference(middle_legal).area,
            0.25,
            places=6,
        )

        result = certify_authored_affine_program(
            placed,
            legal_sections=(full_legal, middle_legal, full_legal),
            target_floor_areas_m2=(3.9, 3.9, 3.9),
            floor_capacity_plan_hash="capacity-plan:middle-legal-hole",
        )

        self.assertIsNone(result)


class FloorwiseLegalProgramTest(SimpleTestCase):
    def test_public_floorwise_csg_rejects_nonstepped_authored_program(self):
        placed_program, host = _placed_u_program()

        self.assertIsNone(append_floorwise_legal_projection(
            placed_program,
            legal_sections=(host, host, host, host),
            target_floor_areas_m2=(10.0, 10.0, 10.0, 10.0),
            floor_capacity_plan_hash="capacity-plan:nonstepped-direct",
        ))

    def test_public_floorwise_csg_rejects_dead_unused_step_node(self):
        placed_program, host = _placed_u_program()
        dead_step = GeometryNode(
            "dead_unused_step",
            "macro",
            "terrace",
            inputs=(placed_program.nodes[0].id,),
            parameters={
                "levels": 3,
                "setback_ratio": 0.12,
                "direction": "x",
            },
        )
        program_with_dead_step = GeometryProgram(
            (*placed_program.nodes, dead_step),
            placed_program.root_id,
            placed_program.name,
            metadata=deepcopy(placed_program.metadata),
        )

        self.assertFalse(
            is_intentional_floorwise_stepped_program(
                program_with_dead_step
            )
        )
        self.assertIsNone(append_floorwise_legal_projection(
            program_with_dead_step,
            legal_sections=(host, host, host, host),
            target_floor_areas_m2=(10.0, 10.0, 10.0, 10.0),
            floor_capacity_plan_hash="capacity-plan:dead-step-direct",
        ))

    def test_floorwise_csg_certificate_marks_intentional_stepped_lane(self):
        placed_program, host = _placed_u_program()
        placed_program = _with_live_step(
            placed_program,
            setback_ratio=0.12,
        )

        result = append_floorwise_legal_projection(
            placed_program,
            legal_sections=(host, host, host, host),
            target_floor_areas_m2=(20.0, 20.0, 20.0, 20.0),
            floor_capacity_plan_hash="capacity-plan:intentional-stepped",
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(
            result.certificate["projection_mode"],
            "intentional_floorwise_stepped",
        )
        self.assertEqual(result.certificate["capacity_threshold_ratio"], 0.995)
        self.assertGreaterEqual(
            result.certificate["achieved_aggregate_area_m2"],
            result.certificate["aggregate_target_area_m2"] * 0.995,
        )

    def test_public_floorwise_csg_rejects_unattainable_capacity_target(self):
        placed_program, host = _placed_u_program()
        placed_program = _with_live_step(placed_program)

        self.assertIsNone(append_floorwise_legal_projection(
            placed_program,
            legal_sections=(host, host, host, host),
            target_floor_areas_m2=(1000.0, 1000.0, 1000.0, 1000.0),
            floor_capacity_plan_hash="capacity-plan:floorwise-short",
        ))

    def test_advisory_floor_targets_do_not_rescale_authored_final_geometry(self):
        placed_program, host = _placed_u_program()
        placed_program = _with_live_step(placed_program)
        sections = (
            host,
            scale(host, xfact=0.92, yfact=0.92),
            scale(host, xfact=0.82, yfact=0.82),
            scale(host, xfact=0.76, yfact=0.76),
        )
        first_targets = (20.0, 20.0, 20.0, 20.0)
        second_targets = (10.0, 10.0, 10.0, 10.0)

        first = append_floorwise_legal_projection(
            placed_program,
            legal_sections=sections,
            target_floor_areas_m2=first_targets,
            floor_capacity_plan_hash="capacity-plan:advisory-a",
        )
        second = append_floorwise_legal_projection(
            placed_program,
            legal_sections=sections,
            target_floor_areas_m2=second_targets,
            floor_capacity_plan_hash="capacity-plan:advisory-b",
        )

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        assert first is not None and second is not None
        first_compilation = compile_geometry_program(first.program)
        second_compilation = compile_geometry_program(second.program)
        self.assertEqual(
            first_compilation.geometry_hash,
            second_compilation.geometry_hash,
            "advisory capacity targets must not author different solids",
        )
        self.assertEqual(
            first.program.program_hash(),
            second.program.program_hash(),
            "advisory capacity provenance must not change executable identity",
        )
        self.assertEqual(
            first.achieved_floor_areas_m2,
            second.achieved_floor_areas_m2,
        )
        self.assertNotEqual(
            tuple(round(value, 3) for value in first.achieved_floor_areas_m2),
            first_targets,
        )
        self.assertEqual(
            first.certificate["target_floor_areas_m2"],
            list(first_targets),
        )
        self.assertEqual(
            second.certificate["target_floor_areas_m2"],
            list(second_targets),
        )
        self.assertEqual(
            first.certificate["floor_capacity_plan_hash"],
            "capacity-plan:advisory-a",
        )
        self.assertFalse(any(
            node.semantic_role == "floorwise_legal_area_transform"
            for node in first.program.nodes
        ))
        authored_bands = tuple(
            node
            for node in first.program.nodes
            if node.semantic_role == "floorwise_authored_band"
        )
        legal_clips = tuple(
            node
            for node in first.program.nodes
            if node.operator == "legal_section_clip"
        )
        self.assertEqual(len(authored_bands), len(sections))
        self.assertEqual(len(legal_clips), len(sections))
        self.assertEqual(
            tuple(node.inputs for node in legal_clips),
            tuple((node.id,) for node in authored_bands),
        )

    def test_bent_offset_relation_survives_floorwise_legal_intersections(self):
        placed_program, legal = _placed_bent_offset_program()
        placed_program = _with_live_step(placed_program)
        authored = compile_geometry_program(placed_program)
        bounds = authored.metrics["bounds"]
        lower_z = float(bounds[0][2])
        upper_z = float(bounds[1][2])
        floor_height = (upper_z - lower_z) / 2.0
        authored_sections = tuple(
            _section_polygon(
                authored,
                lower_z + floor_height * (index + 0.5),
            )
            for index in range(2)
        )

        result = append_floorwise_legal_projection(
            placed_program,
            legal_sections=(legal, legal),
            target_floor_areas_m2=(20.0, 20.0),
            floor_capacity_plan_hash="capacity-plan:bent-offset-advisory",
        )

        self.assertIsNotNone(result)
        assert result is not None
        final = compile_geometry_program(result.program)
        final_sections = tuple(
            _section_polygon(
                final,
                evidence["sample_z_m"][1],
            )
            for evidence in result.certificate["floor_evidence"]
        )
        self.assertTrue(all(section is not None for section in authored_sections))
        self.assertTrue(all(section is not None for section in final_sections))
        self.assertTrue(all(
            authored_section.symmetric_difference(final_section).area < 1e-5
            for authored_section, final_section in zip(
                authored_sections,
                final_sections,
            )
        ))
        self.assertTrue(all(
            section.area / section.convex_hull.area < 0.90
            for section in final_sections
        ))
        self.assertEqual(final.metrics["component_count"], 1)
        self.assertTrue(result.certificate["all_sections_contained"])
        self.assertNotIn("surfaces", result.program.metadata)
        self.assertNotIn("projected_surfaces", result.program.metadata)

    def test_connected_inputs_cannot_certify_two_component_unexportable_result(self):
        block = next(
            program
            for program in base_seed_programs()
            if str(
                (program.metadata.get("base_seed") or {}).get("seed_id")
                or ""
            )
            == "block"
        )
        authored = compile_geometry_program(block)
        self.assertEqual(authored.metrics["component_count"], 1)
        fit = derive_host_fit_transform(
            authored,
            box(0.0, 4.0, 10.0, 6.0),
            target_plan_area=20.0,
        )
        self.assertIsNotNone(fit)
        assert fit is not None
        placed = append_site_placement_matrix(block, fit)
        placed = _with_live_step(placed)
        self.assertEqual(
            compile_geometry_program(placed).metrics["component_count"],
            1,
        )
        legal = Polygon((
            (0.0, 0.0),
            (10.0, 0.0),
            (10.0, 10.0),
            (7.0, 10.0),
            (7.0, 1.0),
            (3.0, 1.0),
            (3.0, 10.0),
            (0.0, 10.0),
        ))
        self.assertTrue(legal.is_valid)
        self.assertIsInstance(legal, Polygon)

        result = append_floorwise_legal_projection(
            placed,
            legal_sections=(legal,),
            target_floor_areas_m2=(20.0,),
            floor_capacity_plan_hash="connected-input-split-output",
        )

        if result is not None:
            final = compile_geometry_program(result.program)
            self.assertTrue(result.certificate["hard_pass"])
            self.assertEqual(final.metrics["component_count"], 2)
            self.assertFalse(compilation_gate(final), compilation_gate(final))
            self.assertIsNotNone(
                compile_site_bound_geometry_program_to_source_mass(
                    result.program,
                    legal,
                ),
                "a hard-pass floorwise certificate must satisfy mandatory export",
            )
        self.assertIsNone(result)

    def test_shrinking_floor_stack_certificate_is_exportable_without_tiny_edges(self):
        block = next(
            program
            for program in base_seed_programs()
            if str(
                (program.metadata.get("base_seed") or {}).get("seed_id")
                or ""
            )
            == "block"
        )
        lower = box(-15.0, -10.0, 15.0, 10.0)
        middle = box(-11.5, -8.0, 11.5, 8.0)
        upper = box(-8.0, -6.0, 8.0, 6.0)
        fit = derive_host_fit_transform(
            compile_geometry_program(block),
            lower,
            target_plan_area=180.0,
            minimum_plan_area=180.0,
        )
        self.assertIsNotNone(fit)
        placed = _with_live_step(
            append_site_placement_matrix(block, fit),
        )
        result = append_floorwise_legal_projection(
            placed,
            legal_sections=(lower, lower, middle, upper),
            target_floor_areas_m2=(60.0, 60.0, 60.0, 60.0),
            floor_capacity_plan_hash="shrinking-stack-export",
        )

        self.assertIsNotNone(result)
        assert result is not None
        compilation = compile_geometry_program(result.program)
        self.assertFalse(
            compilation_gate(compilation),
            compilation_gate(compilation),
        )
        self.assertIsNotNone(
            compile_site_bound_geometry_program_to_source_mass(
                result.program,
                lower,
            )
        )

    def test_equal_area_floor_matrix_does_not_create_tiny_step_edges(self):
        placed_program, host = _placed_u_program()
        placed_program = _with_live_step(placed_program)
        sections = (
            host,
            scale(host, xfact=0.92, yfact=0.92),
            scale(host, xfact=0.82, yfact=0.82),
            scale(host, xfact=0.76, yfact=0.76),
        )
        result = append_floorwise_legal_projection(
            placed_program,
            legal_sections=sections,
            target_floor_areas_m2=(20.0, 20.0, 20.0, 20.0),
            floor_capacity_plan_hash="capacity-plan:exact-identity",
        )

        self.assertIsNotNone(result)
        compilation = compile_geometry_program(result.program)
        self.assertFalse(
            compilation_gate(compilation),
            compilation_gate(compilation),
        )
        self.assertIsNotNone(
            compile_site_bound_geometry_program_to_source_mass(
                result.program,
                host,
            )
        )

    def test_four_floor_projection_is_one_authored_identity_csg_program(self):
        placed_program, host = _placed_u_program()
        placed_program = _with_live_step(placed_program)
        sections = (
            host,
            scale(host, xfact=0.92, yfact=0.92),
            scale(host, xfact=0.82, yfact=0.82),
            scale(host, xfact=0.76, yfact=0.76),
        )
        targets = (20.0, 20.0, 20.0, 20.0)

        result = append_floorwise_legal_projection(
            placed_program,
            legal_sections=sections,
            target_floor_areas_m2=targets,
            floor_capacity_plan_hash="capacity-plan:test",
        )

        self.assertIsInstance(result, FloorwiseLegalProgramResult)
        self.assertEqual(len(result.floor_matrices), 4)
        self.assertEqual(
            [node.operator for node in result.program.nodes[-1:]],
            ["union"],
        )
        self.assertFalse(result.certificate["matrix_interpolation"])
        self.assertFalse(result.certificate["projected_surface_only"])
        self.assertTrue(result.certificate["hard_pass"])
        self.assertEqual(
            result.certificate["floor_capacity_plan_hash"],
            "capacity-plan:test",
        )
        self.assertEqual(
            result.certificate["final_program_hash"],
            result.program.program_hash(),
        )

        compilation = compile_geometry_program(result.program)
        self.assertEqual(compilation.status, "compiled", compilation.issues)
        self.assertEqual(
            result.certificate["final_geometry_hash"],
            compilation.geometry_hash,
        )
        self.assertTrue(compilation.metrics["manifold"])
        self.assertTrue(compilation.metrics["watertight"])
        self.assertNotEqual(
            tuple(round(value, 3) for value in result.achieved_floor_areas_m2),
            targets,
        )
        self.assertEqual(
            result.certificate["target_floor_areas_m2"],
            list(targets),
        )

        primitives = tuple(
            node for node in result.program.nodes if node.kind == "primitive"
        )
        self.assertEqual(len(primitives), 1)
        self.assertEqual(primitives[0].operator, "box")
        self.assertEqual(
            primitives[0].parameters,
            {"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        band_nodes = tuple(
            node
            for node in result.program.nodes
            if node.semantic_role == "floorwise_horizontal_band"
        )
        self.assertEqual(len(band_nodes), 4)
        self.assertTrue(all(
            node.kind == "transform"
            and node.operator == "matrix4"
            and node.inputs == (primitives[0].id,)
            for node in band_nodes
        ))
        legal_clips = tuple(
            node
            for node in result.program.nodes
            if node.operator == "legal_section_clip"
        )
        self.assertEqual(len(legal_clips), 4)
        self.assertTrue(all(node.kind == "modifier" for node in legal_clips))

        area_transform_nodes = tuple(
            node
            for node in result.program.nodes
            if node.semantic_role == "floorwise_legal_area_transform"
        )
        self.assertEqual(area_transform_nodes, ())
        self.assertTrue(all(
            matrix == (
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            )
            for matrix in result.floor_matrices
        ))

        self.assertFalse(any(
            "interpolat" in node.operator
            for node in result.program.nodes
        ))
        self.assertFalse(any(
            node.parameters.get("matrix_interpolation") is True
            for node in result.program.nodes
        ))
        self.assertNotIn("surfaces", result.program.metadata)
        self.assertNotIn("projected_surfaces", result.program.metadata)

        floor_sections = []
        for floor_index, evidence in enumerate(
            result.certificate["floor_evidence"]
        ):
            sampled = tuple(
                _section_polygon(compilation, z)
                for z in evidence["sample_z_m"]
            )
            self.assertTrue(all(section is not None for section in sampled))
            self.assertTrue(all(
                sections[floor_index].buffer(1e-7).covers(section)
                for section in sampled
            ))
            self.assertEqual(
                evidence["containment_authority"],
                "closed_z_band_projected_mesh",
            )
            self.assertTrue(evidence["sample_sections_contained"])
            self.assertEqual(
                evidence["matrix_mode"],
                "authored_identity_legal_csg",
            )
            self.assertTrue(evidence["contained"])
            floor_sections.append(sampled[1])

        # The open court remains a real U-shaped concavity at every level.
        self.assertTrue(all(
            section.area / section.convex_hull.area < 0.82
            for section in floor_sections
        ))
        # Advisory targets do not create steps; the live authored step macro
        # does, and the accepted final mesh retains those authored transitions.
        self.assertTrue(all(
            left.symmetric_difference(right).area > 5.0
            for left, right in zip(floor_sections, floor_sections[1:])
        ))

    def test_three_eighths_l_lineage_stays_connected_after_projection(self):
        unit = GeometryNode(
            "unit_box",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        cells = tuple(
            GeometryNode(
                f"cell_{index}",
                "transform",
                "matrix4",
                inputs=(unit.id,),
                parameters={
                    "matrix4": [
                        [4.0, 0.0, 0.0, x],
                        [0.0, 4.0, 0.0, y],
                        [0.0, 0.0, 4.0, 0.0],
                        [0.0, 0.0, 0.0, 1.0],
                    ],
                },
            )
            for index, (x, y) in enumerate(((0.0, 0.0), (4.0, 0.0), (0.0, 4.0)))
        )
        l_root = GeometryNode(
            "three_eighths_l",
            "boolean",
            "union",
            inputs=tuple(cell.id for cell in cells),
            semantic_role="book_basevolume_3_8",
        )
        authored = GeometryProgram(
            (unit, *cells, l_root),
            l_root.id,
            "three_eighths_l",
            metadata={"base_volume_scope": "3/8"},
        )
        compilation = compile_geometry_program(authored)
        self.assertEqual(compilation.status, "compiled", compilation.issues)
        legal = box(20.0, 30.0, 50.0, 60.0)
        fit = derive_host_fit_transform(
            compilation,
            legal,
            target_plan_area=120.0,
        )
        placed = append_site_placement_matrix(authored, fit)
        placed = _with_live_step(placed)

        result = append_floorwise_legal_projection(
            placed,
            legal_sections=(legal,),
            target_floor_areas_m2=(60.0,),
            floor_capacity_plan_hash="capacity-plan:three-eighths",
        )

        self.assertIsNotNone(result)
        final = compile_geometry_program(result.program)
        self.assertEqual(final.status, "compiled", final.issues)
        evidence = result.certificate["floor_evidence"][0]
        middle = _section_polygon(final, evidence["sample_z_m"][1])
        self.assertIsInstance(middle, Polygon)
        self.assertEqual(final.metrics["component_count"], 1)
        self.assertLess(middle.area / middle.convex_hull.area, 0.90)
        self.assertEqual(result.program.metadata["base_volume_scope"], "3/8")
        self.assertEqual(
            result.certificate["authored_program_hash"],
            placed.program_hash(),
        )

    def test_projection_rejects_incomplete_or_nonfinite_contracts(self):
        placed_program, host = _placed_u_program()

        self.assertIsNone(append_floorwise_legal_projection(
            placed_program,
            legal_sections=(host,),
            target_floor_areas_m2=(10.0, 9.0),
            floor_capacity_plan_hash="capacity-plan:mismatch",
        ))
        self.assertIsNone(append_floorwise_legal_projection(
            placed_program,
            legal_sections=(Polygon(),),
            target_floor_areas_m2=(10.0,),
            floor_capacity_plan_hash="capacity-plan:empty",
        ))
        self.assertIsNone(append_floorwise_legal_projection(
            placed_program,
            legal_sections=(host,),
            target_floor_areas_m2=(float("nan"),),
            floor_capacity_plan_hash="capacity-plan:nan",
        ))
        self.assertIsNone(append_floorwise_legal_projection(
            placed_program,
            legal_sections=(host,),
            target_floor_areas_m2=(10.0,),
            floor_capacity_plan_hash="",
        ))
