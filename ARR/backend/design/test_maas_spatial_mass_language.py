"""Direct-authorship contracts for the generic spatial MASS language."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.creative_program_author import authored_programs_from_payload
from design.maas.geometry_language import BoundedSurface, build_geometry_graph_notes
from design.maas.geometry_language import compiler as geometry_compiler
from design.maas.geometry_language.ast import (
    GeometryNode,
    GeometryProgram,
    geometry_node_input_kinds,
    geometry_node_output_kind,
)
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.llm_adapter import GeometryAuthorError
from design.maas.geometry_language.surface_geometry import (
    host_face_surface_from_bounds,
    loft_surface_from_bounds,
    section_surface_from_bounds,
)


def exactly_one_canonical_unitbox(program: GeometryProgram) -> bool:
    boxes = [
        node
        for node in program.nodes
        if node.kind == "primitive" and node.operator == "box"
    ]
    return (
        len(boxes) == 1
        and boxes[0].parameters
        == {"width": 1.0, "depth": 1.0, "height": 1.0}
    )


def direct_interlocking_plate_program() -> GeometryProgram:
    thin_plate_matrix4 = [
        [4.0, 0.0, 0.0, -2.0],
        [0.0, 1.6, 0.0, -0.8],
        [0.0, 0.0, 0.25, -0.125],
        [0.0, 0.0, 0.0, 1.0],
    ]
    overlapping_arbitrary_xyz_matrices = [
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.573576, -0.819152, 0.0],
            [0.0, 0.819152, 0.573576, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        [
            [0.707107, 0.0, -0.707107, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.707107, 0.0, 0.707107, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
    ]
    unitbox = GeometryNode(
        "unitbox",
        "primitive",
        "box",
        parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        semantic_role="base_seed",
    )
    plate = GeometryNode(
        "plate",
        "transform",
        "matrix4",
        inputs=("unitbox",),
        parameters={"matrix4": thin_plate_matrix4},
        semantic_role="occupied_slab",
    )
    disc = GeometryNode(
        "disc",
        "modifier",
        "circularize",
        inputs=("plate",),
        parameters={"segments": 32},
        semantic_role="envelope",
    )
    assembly = GeometryNode(
        "assembly",
        "pattern",
        "matrix_array",
        inputs=("disc",),
        parameters={
            "matrices": overlapping_arbitrary_xyz_matrices,
            "require_connected": True,
        },
        semantic_role="envelope",
    )
    return GeometryProgram(
        nodes=(unitbox, plate, disc, assembly),
        root_id="assembly",
        name="direct_interlocking_plate",
    )


def valid_legacy_author_payload() -> dict[str, object]:
    return {
        "programs": [{
            "name": "legacy_would_succeed",
            "base_seed": "slab",
            "dsl": (
                "mass base = scale(box(1, 1, 1), "
                "vector=[2.2, 1.45, 0.28])\n"
                "mass result = courtyard("
                "base, margin_ratio=0.22, open_side='west')"
            ),
            "intent_tags": ["public_court"],
        }],
    }


def surface_program(
    *,
    surface_operator: str = "section_surface",
    surface_parameters: dict[str, object] | None = None,
    shell_parameters: dict[str, object] | None = None,
) -> GeometryProgram:
    base = GeometryNode(
        "base",
        "primitive",
        "box",
        parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
    )
    surface = GeometryNode(
        "surface",
        "surface",
        surface_operator,
        inputs=("base",),
        parameters=surface_parameters or {
            "span_axis": "x",
            "section_controls": [[0.0, 0.15], [0.5, 0.85], [1.0, 0.2]],
        },
    )
    shell = GeometryNode(
        "shell",
        "conversion",
        "shell_thicken",
        inputs=("surface",),
        parameters=shell_parameters or {
            "thickness_ratio": 0.04,
            "side": "center",
            "close_edges": True,
        },
    )
    return GeometryProgram(
        nodes=(base, surface, shell),
        root_id="shell",
        name="typed_surface_program",
    )


def site_scale_section_shell_program(
    *,
    surface_operator: str = "section_surface",
    surface_parameters: dict[str, object] | None = None,
    shell_parameters: dict[str, object] | None = None,
) -> GeometryProgram:
    unitbox = GeometryNode(
        "unitbox",
        "primitive",
        "box",
        parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
    )
    host = GeometryNode(
        "host",
        "transform",
        "matrix4",
        inputs=("unitbox",),
        parameters={
            "matrix4": [
                [20.0, 0.0, 0.0, 0.0],
                [0.0, 12.0, 0.0, 0.0],
                [0.0, 0.0, 8.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
        },
    )
    surface = GeometryNode(
        "surface",
        "surface",
        surface_operator,
        inputs=("host",),
        parameters=surface_parameters or {
            "span_axis": "x",
            "section_controls": [[0.0, 0.15], [0.5, 0.85], [1.0, 0.2]],
        },
    )
    shell = GeometryNode(
        "shell",
        "conversion",
        "shell_thicken",
        inputs=("surface",),
        parameters=shell_parameters or {
            "thickness_ratio": 0.04,
            "side": "center",
            "close_edges": True,
        },
    )
    return GeometryProgram(
        nodes=(unitbox, host, surface, shell),
        root_id="shell",
        name="site_scale_section_shell",
    )


class SurfaceShellCompileTest(SimpleTestCase):
    def assert_shell_invariants(self, result):
        self.assertEqual(result.status, "compiled", result.issues)
        self.assertTrue(exactly_one_canonical_unitbox(result.program))
        self.assertEqual(result.metrics["component_count"], 1)
        self.assertTrue(result.metrics["closed_solid"])
        self.assertTrue(result.metrics["watertight"])
        self.assertTrue(result.metrics["manifold"])
        self.assertGreater(result.metrics["volume"], 0.0)

    def test_section_surface_thickens_to_closed_mass(self):
        result = compile_geometry_program(site_scale_section_shell_program())

        self.assert_shell_invariants(result)

        surface_row = next(
            row for row in result.trace if row["operator"] == "section_surface"
        )
        self.assertEqual(surface_row["output_value_kind"], "surface")
        self.assertNotIn("volume", surface_row)
        self.assertEqual(surface_row["section_count"], 3)
        self.assertEqual(surface_row["point_count"], 6)

        shell_row = next(
            row for row in result.trace if row["operator"] == "shell_thicken"
        )
        self.assertEqual(shell_row["output_value_kind"], "solid")
        self.assertAlmostEqual(shell_row["thickness_m"], 0.32, places=6)
        self.assertEqual(shell_row["side"], "center")
        self.assertEqual(shell_row["segment_count"], 2)
        self.assertEqual(shell_row["fold_joint_count"], 1)
        self.assertFalse(shell_row["closed_seam"])

    @patch(
        "design.maas.geometry_language.vlm_adapter.score_candidate_with_openai_vlm",
        side_effect=AssertionError("VLM graph notes must not call provider"),
    )
    def test_surface_shell_graph_notes_expose_typed_conversion_evidence(
        self,
        _urlopen,
    ):
        program = site_scale_section_shell_program()
        result = compile_geometry_program(program)

        notes = {
            note["operator"]: note
            for note in build_geometry_graph_notes(program, result)
        }
        surface_note = notes["section_surface"]
        shell_note = notes["shell_thicken"]

        self.assertEqual(surface_note["output_value_kind"], "surface")
        self.assertEqual(shell_note["output_value_kind"], "solid")
        self.assertAlmostEqual(shell_note["thickness_m"], 0.32, places=6)
        self.assertEqual(shell_note["side"], "center")
        self.assertTrue(shell_note["close_edges"])
        self.assertNotIn(
            "occupiable",
            json.dumps(shell_note, ensure_ascii=False).lower(),
        )

    def test_all_surface_constructors_and_side_modes_compile_end_to_end(self):
        surfaces = (
            (
                "section_surface",
                {
                    "span_axis": "x",
                    "section_controls": [
                        [0.0, 0.2],
                        [0.5, 0.8],
                        [1.0, 0.3],
                    ],
                },
            ),
            (
                "loft_surface",
                {
                    "profiles": [
                        [[0.0, 0.0, 0.2], [0.0, 1.0, 0.2]],
                        [[0.5, 0.0, 0.8], [0.5, 1.0, 0.8]],
                        [[1.0, 0.0, 0.3], [1.0, 1.0, 0.3]],
                    ],
                },
            ),
            (
                "host_face_surface",
                {"host_face": "top", "inset_ratio": 0.1},
            ),
        )
        for operator, surface_parameters in surfaces:
            for side in ("center", "inward", "outward"):
                with self.subTest(operator=operator, side=side):
                    result = compile_geometry_program(
                        site_scale_section_shell_program(
                            surface_operator=operator,
                            surface_parameters=surface_parameters,
                            shell_parameters={
                                "thickness_ratio": 0.04,
                                "side": side,
                                "close_edges": True,
                            },
                        )
                    )

                    self.assert_shell_invariants(result)
                    shell_row = next(
                        row
                        for row in result.trace
                        if row["operator"] == "shell_thicken"
                    )
                    self.assertEqual(shell_row["side"], side)
                    self.assertAlmostEqual(
                        shell_row["thickness_m"],
                        0.32,
                        places=6,
                    )
                    normals = shell_row["oriented_normals"]
                    self.assertTrue(all(
                        sum(
                            left_value * right_value
                            for left_value, right_value in zip(left, right)
                        )
                        >= -1e-8
                        for left, right in zip(normals, normals[1:])
                    ))

    def test_host_face_outward_and_inward_follow_all_six_host_directions(self):
        expected_axis_bounds = {
            "west": (
                0, (-0.32, 0.0), (0.0, 0.32), [-1.0, 0.0, 0.0]
            ),
            "east": (
                0, (20.0, 20.32), (19.68, 20.0), [1.0, 0.0, 0.0]
            ),
            "south": (
                1, (-0.32, 0.0), (0.0, 0.32), [0.0, -1.0, 0.0]
            ),
            "north": (
                1, (12.0, 12.32), (11.68, 12.0), [0.0, 1.0, 0.0]
            ),
            "bottom": (
                2, (-0.32, 0.0), (0.0, 0.32), [0.0, 0.0, -1.0]
            ),
            "top": (
                2, (8.0, 8.32), (7.68, 8.0), [0.0, 0.0, 1.0]
            ),
        }
        for host_face, (
            axis,
            expected_outward,
            expected_inward,
            expected_normal,
        ) in expected_axis_bounds.items():
            for side, expected in (
                ("outward", expected_outward),
                ("inward", expected_inward),
            ):
                with self.subTest(host_face=host_face, side=side):
                    result = compile_geometry_program(
                        site_scale_section_shell_program(
                            surface_operator="host_face_surface",
                            surface_parameters={
                                "host_face": host_face,
                                "inset_ratio": 0.0,
                            },
                            shell_parameters={
                                "thickness_ratio": 0.04,
                                "side": side,
                                "close_edges": True,
                            },
                        )
                    )

                    self.assert_shell_invariants(result)
                    actual = (
                        result.metrics["bounds"][0][axis],
                        result.metrics["bounds"][1][axis],
                    )
                    self.assertAlmostEqual(actual[0], expected[0], places=6)
                    self.assertAlmostEqual(actual[1], expected[1], places=6)
                    shell_row = next(
                        row
                        for row in result.trace
                        if row["operator"] == "shell_thicken"
                    )
                    self.assertEqual(
                        shell_row["oriented_normals"],
                        [expected_normal],
                    )

    def test_closed_rectangular_loft_loop_compiles_without_false_crossing(self):
        profiles = [
            [[0.2, 0.0, 0.2], [0.2, 1.0, 0.2]],
            [[0.8, 0.0, 0.2], [0.8, 1.0, 0.2]],
            [[0.8, 0.0, 0.8], [0.8, 1.0, 0.8]],
            [[0.2, 0.0, 0.8], [0.2, 1.0, 0.8]],
            [[0.2, 0.0, 0.2], [0.2, 1.0, 0.2]],
        ]
        for side in ("center", "inward", "outward"):
            with self.subTest(side=side):
                result = compile_geometry_program(
                    site_scale_section_shell_program(
                        surface_operator="loft_surface",
                        surface_parameters={"profiles": profiles},
                        shell_parameters={
                            "thickness_ratio": 0.04,
                            "side": side,
                            "close_edges": True,
                        },
                    )
                )

                self.assert_shell_invariants(result)
                shell_row = next(
                    row
                    for row in result.trace
                    if row["operator"] == "shell_thicken"
                )
                self.assertTrue(shell_row["closed_seam"])
                self.assertEqual(shell_row["segment_count"], 4)
                self.assertEqual(shell_row["fold_joint_count"], 4)

    def test_ast_rejects_zero_thickness_and_open_edges_before_kernel(self):
        cases = (
            (
                {
                    "thickness_ratio": 0.0,
                    "side": "center",
                    "close_edges": True,
                },
                "shell_thickness_out_of_bounds",
            ),
            (
                {
                    "thickness_ratio": 0.04,
                    "side": "center",
                    "close_edges": False,
                },
                "open_shell_edges",
            ),
        )

        for parameters, issue_code in cases:
            with self.subTest(issue_code=issue_code):
                result = compile_geometry_program(
                    site_scale_section_shell_program(
                        shell_parameters=parameters,
                    )
                )

                self.assertEqual(result.status, "invalid_program")
                self.assertIn(
                    issue_code,
                    {issue.code for issue in result.issues},
                )

    def test_collapsed_surface_section_fails_closed_at_compile_boundary(self):
        result = compile_geometry_program(
            site_scale_section_shell_program(
                surface_operator="loft_surface",
                surface_parameters={
                    "profiles": [
                        [[0.0, 0.0, 0.2], [0.0, 1.0, 0.2]],
                        [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5]],
                        [[1.0, 0.0, 0.8], [1.0, 1.0, 0.8]],
                    ],
                },
            )
        )

        self.assertEqual(result.status, "compile_failed")
        self.assertEqual(result.issues[0].code, "invalid_surface_geometry")

    def test_true_nonadjacent_crossing_fails_before_shell_union(self):
        result = compile_geometry_program(
            site_scale_section_shell_program(
                surface_operator="loft_surface",
                surface_parameters={
                    "profiles": [
                        [[0.0, 0.0, 0.2], [0.0, 1.0, 0.2]],
                        [[1.0, 0.0, 0.8], [1.0, 1.0, 0.8]],
                        [[0.0, 0.0, 0.8], [0.0, 1.0, 0.8]],
                        [[1.0, 0.0, 0.2], [1.0, 1.0, 0.2]],
                    ],
                },
            )
        )

        self.assertEqual(result.status, "compile_failed")
        self.assertEqual(result.issues[0].code, "self_intersecting_shell")

    def test_partial_and_full_surface_retraces_fail_for_every_side(self):
        centerlines = {
            "partial": (
                (0.1, 0.2),
                (0.9, 0.8),
                (0.2, 0.275),
            ),
            "full": (
                (0.1, 0.2),
                (0.9, 0.8),
                (0.1, 0.2),
            ),
        }
        for retrace_kind, centerline in centerlines.items():
            profiles = [
                [[x, 0.0, z], [x, 1.0, z]]
                for x, z in centerline
            ]
            for side in ("center", "inward", "outward"):
                with self.subTest(
                    retrace_kind=retrace_kind,
                    side=side,
                ):
                    result = compile_geometry_program(
                        site_scale_section_shell_program(
                            surface_operator="loft_surface",
                            surface_parameters={"profiles": profiles},
                            shell_parameters={
                                "thickness_ratio": 0.04,
                                "side": side,
                                "close_edges": True,
                            },
                        )
                    )

                    self.assertEqual(result.status, "compile_failed")
                    self.assertEqual(
                        result.issues[0].code,
                        "self_intersecting_shell",
                    )
                    self.assertEqual(
                        result.issues[0].message,
                        "surface centerline retraces the previous segment",
                    )

    def test_closed_seam_triplet_cannot_retrace_first_segment(self):
        profiles = [
            [[0.2, 0.0, 0.2], [0.2, 1.0, 0.2]],
            [[0.8, 0.0, 0.2], [0.8, 1.0, 0.2]],
            [[0.8, 0.0, 0.8], [0.8, 1.0, 0.8]],
            [[0.5, 0.0, 0.2], [0.5, 1.0, 0.2]],
            [[0.2, 0.0, 0.2], [0.2, 1.0, 0.2]],
        ]

        result = compile_geometry_program(
            site_scale_section_shell_program(
                surface_operator="loft_surface",
                surface_parameters={"profiles": profiles},
            )
        )

        self.assertEqual(result.status, "compile_failed")
        self.assertEqual(result.issues[0].code, "self_intersecting_shell")
        self.assertEqual(
            result.issues[0].message,
            "surface centerline retraces the previous segment",
        )

    def test_fold_joint_cannot_cross_a_nonincident_segment(self):
        centerline = (
            (0.8514422403522063, 0.7582473359297199),
            (0.7121736535540322, 0.3080880368672024),
            (0.7484019761981957, 0.15014077878288984),
            (0.5128414338424889, 0.8227140118828640),
            (0.1951909705426227, 0.6708298998937252),
            (0.0845895855070813, 0.2545692735969854),
        )
        profiles = [
            [[x, 0.0, z], [x, 1.0, z]]
            for x, z in centerline
        ]

        result = compile_geometry_program(
            site_scale_section_shell_program(
                surface_operator="loft_surface",
                surface_parameters={"profiles": profiles},
                shell_parameters={
                    "thickness_ratio": 0.04,
                    "side": "center",
                    "close_edges": True,
                },
            )
        )

        self.assertEqual(result.status, "compile_failed")
        self.assertEqual(result.issues[0].code, "self_intersecting_shell")
        self.assertEqual(
            result.issues[0].message,
            "fold joint intersects a nonincident surface segment",
        )

    def test_disjoint_joint_incidence_activates_joint_crossing_gate(self):
        profiles = [
            [[0.0, 0.0, 0.2], [0.0, 1.0, 0.2]],
            [[0.25, 0.0, 0.6], [0.25, 1.0, 0.6]],
            [[0.5, 0.0, 0.2], [0.5, 1.0, 0.2]],
            [[0.75, 0.0, 0.6], [0.75, 1.0, 0.6]],
            [[1.0, 0.0, 0.2], [1.0, 1.0, 0.2]],
        ]
        checked_labels: list[str] = []

        def simulated_overlap(*_args, **kwargs):
            label = str(kwargs["label"])
            checked_labels.append(label)
            return label.startswith("joints ")

        with patch.object(
            geometry_compiler,
            "_shell_has_positive_overlap",
            side_effect=simulated_overlap,
        ):
            result = compile_geometry_program(
                site_scale_section_shell_program(
                    surface_operator="loft_surface",
                    surface_parameters={"profiles": profiles},
                )
            )

        self.assertEqual(result.status, "compile_failed")
        self.assertEqual(result.issues[0].code, "self_intersecting_shell")
        self.assertIn("joints 0:2", checked_labels)

    def test_outward_fold_uses_joint_hull_to_remain_connected(self):
        result = compile_geometry_program(
            site_scale_section_shell_program(
                surface_operator="loft_surface",
                surface_parameters={
                    "profiles": [
                        [[0.0, 0.0, 0.1], [0.0, 1.0, 0.1]],
                        [[0.0, 0.0, 0.9], [0.0, 1.0, 0.9]],
                        [[0.5, 0.0, 0.1], [0.5, 1.0, 0.1]],
                    ],
                },
                shell_parameters={
                    "thickness_ratio": 0.04,
                    "side": "outward",
                    "close_edges": True,
                },
            )
        )

        self.assert_shell_invariants(result)
        shell_row = next(
            row for row in result.trace if row["operator"] == "shell_thicken"
        )
        self.assertEqual(shell_row["fold_joint_count"], 1)

    def test_shell_kernel_exceptions_keep_shell_specific_error_code(self):
        intersection_program = site_scale_section_shell_program(
            surface_operator="loft_surface",
            surface_parameters={
                "profiles": [
                    [[0.0, 0.0, 0.1], [0.0, 1.0, 0.1]],
                    [[0.2, 0.0, 0.3], [0.2, 1.0, 0.3]],
                    [[0.0, 0.0, 0.3], [0.0, 1.0, 0.3]],
                    [[1.0, 0.0, 0.1], [1.0, 1.0, 0.1]],
                ],
            },
        )
        cases = (
            (
                "hull",
                "_shell_hull_points",
                site_scale_section_shell_program(),
            ),
            (
                "intersection",
                "_shell_batch_boolean",
                intersection_program,
            ),
            (
                "union",
                "_shell_batch_boolean",
                site_scale_section_shell_program(),
            ),
            (
                "status",
                "_shell_status",
                site_scale_section_shell_program(),
            ),
            (
                "decompose",
                "_shell_decompose",
                site_scale_section_shell_program(),
            ),
        )
        for kernel_path, helper_name, program in cases:
            with self.subTest(
                kernel_path=kernel_path,
                helper_name=helper_name,
            ):
                with patch.object(
                    geometry_compiler,
                    helper_name,
                    side_effect=RuntimeError(f"{helper_name} failed"),
                    create=True,
                ):
                    result = compile_geometry_program(program)

                self.assertEqual(result.status, "compile_failed")
                self.assertEqual(result.issues[0].code, "shell_kernel_error")
                self.assertEqual(result.issues[0].node_id, "shell")

    def test_compiler_defense_rejects_non_solid_root_after_ast_boundary(self):
        source = site_scale_section_shell_program()
        program = GeometryProgram(
            nodes=source.nodes[:-1],
            root_id="surface",
        )

        with patch.object(GeometryProgram, "validate", return_value=()):
            result = compile_geometry_program(program)

        self.assertEqual(result.status, "compile_failed")
        self.assertEqual(result.issues[0].code, "non_solid_root")

    def test_surface_cannot_reach_solid_only_union_compiler_path(self):
        source = site_scale_section_shell_program()
        other = GeometryNode(
            "other",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        union = GeometryNode(
            "result",
            "boolean",
            "union",
            inputs=("surface", "other"),
        )
        program = GeometryProgram(
            nodes=(*source.nodes[:-1], other, union),
            root_id="result",
        )

        result = compile_geometry_program(program)

        self.assertEqual(result.status, "invalid_program")
        self.assertIn(
            "geometry_value_kind_mismatch",
            {issue.code for issue in result.issues},
        )


class SurfaceAstTypeTest(SimpleTestCase):
    def test_geometry_value_kind_contracts_are_explicit(self):
        source = surface_program()

        self.assertEqual(
            geometry_node_output_kind(source.node_map["base"]),
            "solid",
        )
        self.assertEqual(
            geometry_node_output_kind(source.node_map["surface"]),
            "surface",
        )
        self.assertEqual(
            geometry_node_input_kinds(source.node_map["surface"]),
            ("solid",),
        )
        self.assertEqual(
            geometry_node_input_kinds(source.node_map["shell"]),
            ("surface",),
        )

    def test_surface_node_cannot_be_program_root(self):
        source = surface_program()
        program = source.with_nodes(source.nodes[:-1], root_id="surface")

        self.assertIn(
            "surface_root_not_allowed",
            {issue.code for issue in program.validate()},
        )

    def test_surface_cannot_enter_solid_boolean(self):
        source = surface_program()
        other = GeometryNode(
            "other",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        union = GeometryNode(
            "result",
            "boolean",
            "union",
            inputs=("surface", "other"),
        )
        program = GeometryProgram(
            nodes=(source.node_map["base"], source.node_map["surface"], other, union),
            root_id="result",
        )

        self.assertIn(
            "geometry_value_kind_mismatch",
            {issue.code for issue in program.validate()},
        )

    def test_shell_thicken_converts_surface_to_solid(self):
        self.assertEqual(surface_program().validate(), ())

    def test_unknown_surface_operator_rejects(self):
        program = surface_program(surface_operator="unknown_surface")

        self.assertIn(
            "unknown_operator",
            {issue.code for issue in program.validate()},
        )

    def test_shell_thicken_rejects_solid_input(self):
        source = surface_program()
        shell = replace(source.node_map["shell"], inputs=("base",))
        program = GeometryProgram(
            nodes=(source.node_map["base"], shell),
            root_id="shell",
        )

        self.assertIn(
            "geometry_value_kind_mismatch",
            {issue.code for issue in program.validate()},
        )

    def test_surface_and_conversion_require_exactly_one_input(self):
        source = surface_program()
        cases = (
            replace(source.node_map["surface"], inputs=()),
            replace(source.node_map["surface"], inputs=("base", "base")),
            replace(source.node_map["shell"], inputs=()),
            replace(source.node_map["shell"], inputs=("surface", "surface")),
        )

        for node in cases:
            with self.subTest(kind=node.kind, inputs=node.inputs):
                self.assertIn(
                    "invalid_arity",
                    {issue.code for issue in _program_ending_at(source, node).validate()},
                )

    def test_section_surface_rejects_invalid_controls(self):
        invalid_controls = (
            [],
            [[0.0, 0.2]],
            [[0.0, 0.2]] * 13,
            [[0.0, 0.2], [0.0, 0.4], [1.0, 0.2]],
            [[0.1, 0.2], [1.0, 0.2]],
            [[0.0, 0.2], [0.9, 0.2]],
            [[0.0, 0.2], [1.0, float("inf")]],
            [[0.0, 0.2, 0.3], [1.0, 0.2]],
        )

        for controls in invalid_controls:
            with self.subTest(controls=controls):
                program = surface_program(
                    surface_parameters={
                        "span_axis": "x",
                        "section_controls": controls,
                    },
                )
                self.assertIn(
                    "invalid_surface_controls",
                    {issue.code for issue in program.validate()},
                )

    def test_loft_surface_rejects_invalid_profiles(self):
        valid_profile = [[0.0, 0.0, 0.2], [0.0, 1.0, 0.2]]
        invalid_profiles = (
            [],
            [valid_profile],
            [valid_profile] * 13,
            [valid_profile, [[0.0, 0.0, float("nan")], [1.0, 1.0, 0.2]]],
            [valid_profile, [[0.0, 0.2], [1.0, 0.2]]],
            [valid_profile, [[0.0, 0.0, 0.2]]],
            [valid_profile, [[0.0, 0.0, 0.2], [1.1, 1.0, 0.2]]],
        )

        for profiles in invalid_profiles:
            with self.subTest(profiles=profiles):
                program = surface_program(
                    surface_operator="loft_surface",
                    surface_parameters={"profiles": profiles},
                )
                self.assertIn(
                    "invalid_surface_profile",
                    {issue.code for issue in program.validate()},
                )

    def test_host_face_surface_rejects_unsupported_face(self):
        for host_face in ("", "front", None):
            with self.subTest(host_face=host_face):
                program = surface_program(
                    surface_operator="host_face_surface",
                    surface_parameters={"host_face": host_face},
                )
                self.assertIn(
                    "unsupported_host_face",
                    {issue.code for issue in program.validate()},
                )

    def test_shell_thicken_rejects_invalid_parameters(self):
        cases = (
            (
                {"thickness_ratio": 0.004, "side": "center", "close_edges": True},
                "shell_thickness_out_of_bounds",
            ),
            (
                {"thickness_ratio": 0.251, "side": "center", "close_edges": True},
                "shell_thickness_out_of_bounds",
            ),
            (
                {"thickness_ratio": float("nan"), "side": "center", "close_edges": True},
                "shell_thickness_out_of_bounds",
            ),
            (
                {"thickness_ratio": 0.04, "side": "both", "close_edges": True},
                "unsupported_shell_side",
            ),
            (
                {"thickness_ratio": 0.04, "side": "center", "close_edges": False},
                "open_shell_edges",
            ),
        )

        for parameters, expected_code in cases:
            with self.subTest(parameters=parameters):
                program = surface_program(shell_parameters=parameters)
                self.assertIn(
                    expected_code,
                    {issue.code for issue in program.validate()},
                )

    def test_surface_parameter_contract_accepts_all_documented_boundaries(self):
        valid_profiles = [
            [[0.0, 0.0, 0.15], [0.0, 1.0, 0.15]],
            [[1.0, 0.0, 0.85], [1.0, 1.0, 0.85]],
        ]
        programs = [
            surface_program(
                surface_operator="loft_surface",
                surface_parameters={"profiles": valid_profiles},
            ),
            *[
                surface_program(
                    surface_operator="host_face_surface",
                    surface_parameters={"host_face": host_face},
                )
                for host_face in ("east", "west", "north", "south", "top", "bottom")
            ],
            *[
                surface_program(
                    shell_parameters={
                        "thickness_ratio": thickness_ratio,
                        "side": side,
                        "close_edges": True,
                    },
                )
                for thickness_ratio in (0.005, 0.25)
                for side in ("center", "inward", "outward")
            ],
        ]

        for program in programs:
            with self.subTest(program=program.to_dict()):
                self.assertEqual(program.validate(), ())


class BoundedSurfaceTest(SimpleTestCase):
    bounds = (0.0, 0.0, 0.0, 20.0, 12.0, 8.0)

    def test_section_surface_maps_controls_through_live_bounds(self):
        surface = section_surface_from_bounds(
            self.bounds,
            {
                "span_axis": "x",
                "section_controls": [[0.0, 0.15], [0.5, 0.85], [1.0, 0.2]],
            },
        )

        self.assertEqual(surface.operator, "section_surface")
        self.assertEqual(len(surface.sections), 3)
        self.assertEqual(surface.sections[0][0], (0.0, 0.0, 1.2))
        self.assertEqual(surface.sections[0][1], (0.0, 12.0, 1.2))
        self.assertEqual(surface.sections[-1][0], (20.0, 0.0, 1.6))
        self.assertEqual(surface.validate(), ())

    def test_loft_surface_preserves_ordered_normalized_profiles(self):
        surface = loft_surface_from_bounds(
            self.bounds,
            {
                "profiles": [
                    [[0.0, 0.0, 0.25], [0.0, 1.0, 0.5]],
                    [[0.5, 0.0, 0.75], [0.5, 1.0, 1.0]],
                    [[1.0, 0.0, 0.5], [1.0, 1.0, 0.25]],
                ],
            },
        )

        self.assertEqual(
            surface.sections,
            (
                ((0.0, 0.0, 2.0), (0.0, 12.0, 4.0)),
                ((10.0, 0.0, 6.0), (10.0, 12.0, 8.0)),
                ((20.0, 0.0, 4.0), (20.0, 12.0, 2.0)),
            ),
        )
        self.assertEqual(surface.validate(), ())

    def test_host_face_surface_returns_four_inset_live_face_corners(self):
        surface = host_face_surface_from_bounds(
            self.bounds,
            {"host_face": "top", "inset_ratio": 0.25},
        )

        self.assertEqual(
            surface.sections,
            (
                ((5.0, 3.0, 8.0), (5.0, 9.0, 8.0)),
                ((15.0, 3.0, 8.0), (15.0, 9.0, 8.0)),
            ),
        )
        self.assertEqual(
            sum(len(section) for section in surface.sections),
            4,
        )
        self.assertEqual(surface.validate(), ())

    def test_surface_is_immutable_and_serializes_without_kernel_objects(self):
        surface = section_surface_from_bounds(
            self.bounds,
            {
                "span_axis": "x",
                "section_controls": [[0.0, 0.2], [1.0, 0.8]],
            },
        )

        with self.assertRaises(FrozenInstanceError):
            surface.operator = "changed"
        payload = surface.to_dict()

        self.assertEqual(
            json.loads(json.dumps(payload, sort_keys=True)),
            payload,
        )
        self.assertEqual(
            payload,
            {
                "operator": "section_surface",
                "sections": [
                    [[0.0, 0.0, 1.6], [0.0, 12.0, 1.6]],
                    [[20.0, 0.0, 6.4], [20.0, 12.0, 6.4]],
                ],
                "source_bounds": [0.0, 0.0, 0.0, 20.0, 12.0, 8.0],
            },
        )

    def test_validate_rejects_each_invalid_surface_geometry(self):
        valid_sections = (
            ((0.0, 0.0, 1.0), (0.0, 12.0, 1.0)),
            ((20.0, 0.0, 2.0), (20.0, 12.0, 2.0)),
        )
        cases = (
            (
                (
                    ((0.0, 0.0, float("nan")), (0.0, 12.0, 1.0)),
                    valid_sections[1],
                ),
                "nonfinite_point",
            ),
            ((valid_sections[0],), "too_few_sections"),
            (
                (
                    valid_sections[0],
                    ((20.0, 0.0, 2.0), (20.0, 6.0, 2.0), (20.0, 12.0, 2.0)),
                ),
                "inconsistent_section_vertex_count",
            ),
            (
                (
                    ((0.0, 0.0, 1.0), (0.0, 0.0, 1.0)),
                    valid_sections[1],
                ),
                "zero_length_section_edge",
            ),
            (
                (valid_sections[0], valid_sections[0]),
                "repeated_consecutive_sections",
            ),
            (
                (
                    valid_sections[0],
                    ((20.000001, 0.0, 2.0), (20.0, 12.0, 2.0)),
                ),
                "point_outside_source_bounds",
            ),
        )

        for sections, expected_error in cases:
            with self.subTest(expected_error=expected_error):
                surface = BoundedSurface(
                    operator="test_surface",
                    sections=sections,
                    source_bounds=self.bounds,
                )
                self.assertIn(expected_error, surface.validate())

    def test_validate_allows_bounds_tolerance(self):
        surface = BoundedSurface(
            operator="test_surface",
            sections=(
                ((-0.00000005, 0.0, 1.0), (0.0, 12.0, 1.0)),
                ((20.00000005, 0.0, 2.0), (20.0, 12.0, 2.0)),
            ),
            source_bounds=self.bounds,
        )

        self.assertEqual(surface.validate(), ())

    def test_constructors_reject_parameters_outside_normalized_domain(self):
        invalid_calls = (
            (
                section_surface_from_bounds,
                {
                    "span_axis": "z",
                    "section_controls": [[0.0, 0.2], [1.0, 0.8]],
                },
            ),
            (
                section_surface_from_bounds,
                {
                    "span_axis": "x",
                    "section_controls": [[0.0, 0.2], [1.0, 1.01]],
                },
            ),
            (
                loft_surface_from_bounds,
                {
                    "profiles": [
                        [[0.0, 0.0, 0.2], [0.0, 1.0, 0.2]],
                        [[1.0, 0.0, 0.2], [1.0, -0.01, 0.2]],
                    ],
                },
            ),
            (
                host_face_surface_from_bounds,
                {"host_face": "front", "inset_ratio": 0.1},
            ),
            (
                host_face_surface_from_bounds,
                {"host_face": "top", "inset_ratio": 0.5},
            ),
        )

        for constructor, parameters in invalid_calls:
            with self.subTest(
                constructor=constructor.__name__,
                parameters=parameters,
            ):
                with self.assertRaises(ValueError):
                    constructor(self.bounds, parameters)


def _program_ending_at(source: GeometryProgram, node: GeometryNode) -> GeometryProgram:
    nodes_by_id = {
        item.id: item
        for item in source.nodes
        if item.id != node.id
    }
    nodes_by_id[node.id] = node
    reachable_ids = set(node.inputs)
    if node.kind == "conversion":
        reachable_ids.add("surface")
        reachable_ids.add("base")
    elif node.kind == "surface":
        reachable_ids.add("base")
    nodes = tuple(
        nodes_by_id[node_id]
        for node_id in ("base", "surface", "shell")
        if node_id in nodes_by_id and (node_id == node.id or node_id in reachable_ids)
    )
    return GeometryProgram(nodes=nodes, root_id=node.id)


class DirectPlateAuthorshipTest(SimpleTestCase):
    def test_payload_authorship_accepts_unnamed_interlocking_plate_program(self):
        source = direct_interlocking_plate_program()
        payload = {
            "schema_version": "arr.maas.geometry_llm_author_cache.v3",
            "compiled_programs": [source.to_dict()],
            "response_id": "fixture-no-provider",
        }

        authored = authored_programs_from_payload(
            payload,
            expected_count=1,
            program_context={"pnu": "fixture"},
        )
        result = compile_geometry_program(authored[0].program)

        self.assertEqual(result.status, "compiled", result.issues)
        self.assertTrue(exactly_one_canonical_unitbox(result.program))
        self.assertEqual(result.metrics["component_count"], 1)
        self.assertTrue(result.metrics["watertight"])
        self.assertTrue(result.metrics["manifold"])
        self.assertEqual(
            [node.operator for node in result.program.topological_nodes()],
            ["box", "matrix4", "circularize", "matrix_array"],
        )

    def test_interlocking_plate_authorship_rejects_disconnected_placement(self):
        source = direct_interlocking_plate_program()
        assembly = source.node_map["assembly"]
        matrices = [
            [list(row) for row in matrix]
            for matrix in assembly.parameters["matrices"]
        ]
        matrices[2][0][3] = 20.0
        disconnected_assembly = replace(
            assembly,
            parameters={
                **assembly.parameters,
                "matrices": matrices,
            },
        )
        disconnected = source.with_nodes(
            disconnected_assembly if node.id == "assembly" else node
            for node in source.nodes
        )
        payload = {
            "schema_version": "arr.maas.geometry_llm_author_cache.v3",
            "compiled_programs": [disconnected.to_dict()],
            "response_id": "fixture-no-provider",
        }

        authored = authored_programs_from_payload(
            payload,
            expected_count=1,
            program_context={"pnu": "fixture"},
        )
        result = compile_geometry_program(authored[0].program)

        self.assertEqual(result.status, "compile_failed")
        self.assertEqual(result.issues[0].code, "disconnected_matrix_array")

    def test_geometry_programs_wins_when_both_exact_keys_are_present(self):
        source = direct_interlocking_plate_program()
        alternate_nodes = tuple(
            replace(node, parameters={**node.parameters, "segments": 8})
            if node.id == "disc"
            else node
            for node in source.nodes
        )
        alternate = source.with_nodes(alternate_nodes)

        authored = authored_programs_from_payload(
            {
                "geometry_programs": [source.to_dict()],
                "compiled_programs": [alternate.to_dict()],
            },
            expected_count=1,
        )

        self.assertEqual(
            authored[0].program.node_map["disc"].parameters["segments"],
            32,
        )

    def test_malformed_geometry_programs_cannot_fall_back(self):
        source = direct_interlocking_plate_program()
        for malformed in (None, [], {"unexpected": True}, [None]):
            with self.subTest(malformed=malformed):
                with self.assertRaises(GeometryAuthorError):
                    authored_programs_from_payload(
                        {
                            **valid_legacy_author_payload(),
                            "geometry_programs": malformed,
                            "compiled_programs": [source.to_dict()],
                        },
                        expected_count=1,
                    )

    def test_malformed_compiled_programs_cannot_fall_through_to_legacy(self):
        for malformed in (None, [], {"unexpected": True}, [None]):
            with self.subTest(malformed=malformed):
                with self.assertRaises(GeometryAuthorError):
                    authored_programs_from_payload(
                        {
                            **valid_legacy_author_payload(),
                            "compiled_programs": malformed,
                        },
                        expected_count=1,
                    )
