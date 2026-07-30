"""Strict one-UnitBox lineage contracts for typed geometry operators."""

from __future__ import annotations

from copy import deepcopy

from django.test import SimpleTestCase

from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.compiler import compile_geometry_program


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


def _unitbox_input(
    *,
    width: float,
    depth: float,
    height: float,
    translation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> tuple[GeometryNode, GeometryNode]:
    unitbox = GeometryNode(
        "unitbox",
        "primitive",
        "box",
        parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        semantic_role="base_authority",
    )
    x, y, z = translation
    derived = GeometryNode(
        "derived",
        "transform",
        "matrix4",
        inputs=(unitbox.id,),
        parameters={
            "matrix4": [
                [width, 0.0, 0.0, x],
                [0.0, depth, 0.0, y],
                [0.0, 0.0, height, z],
                [0.0, 0.0, 0.0, 1.0],
            ]
        },
        semantic_role="unitbox_derived_profile",
    )
    return unitbox, derived


def unitbox_circularize_program(
    *,
    radius_x: float,
    radius_y: float,
    height: float,
    segments: int = 24,
) -> GeometryProgram:
    unitbox, derived = _unitbox_input(
        width=radius_x * 2.0,
        depth=radius_y * 2.0,
        height=height,
        translation=(4.0, -3.0, 2.0),
    )
    circular = GeometryNode(
        "result",
        "modifier",
        "circularize",
        inputs=(derived.id,),
        parameters={"segments": segments},
    )
    return GeometryProgram((unitbox, derived, circular), circular.id, "circular")


_OVERLAPPING_ROTATION_MATRICES = [
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.9659258263, -0.2588190451, 0.1464466094],
        [0.0, 0.2588190451, 0.9659258263, -0.1123724357],
        [0.0, 0.0, 0.0, 1.0],
    ],
    [
        [0.9396926208, 0.0, 0.3420201433, -0.1408563821],
        [0.0, 1.0, 0.0, 0.0],
        [-0.3420201433, 0.0, 0.9396926208, 0.2011637612],
        [0.0, 0.0, 0.0, 1.0],
    ],
    [
        [0.9396926208, 0.3420201433, 0.0, -0.1408563821],
        [-0.3420201433, 0.9396926208, 0.0, 0.2011637612],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ],
]


def unitbox_matrix_array_program(
    matrices: object = _OVERLAPPING_ROTATION_MATRICES,
    *,
    require_connected: bool = True,
) -> GeometryProgram:
    unitbox, derived = _unitbox_input(width=4.0, depth=3.0, height=2.0)
    array = GeometryNode(
        "result",
        "pattern",
        "matrix_array",
        inputs=(derived.id,),
        parameters={
            "matrices": deepcopy(matrices),
            "require_connected": require_connected,
        },
    )
    return GeometryProgram((unitbox, derived, array), array.id, "matrix_array")


def unitbox_profile_sweep_program(path: object) -> GeometryProgram:
    unitbox, derived = _unitbox_input(width=1.2, depth=0.8, height=0.6)
    sweep = GeometryNode(
        "result",
        "modifier",
        "profile_sweep_3d",
        inputs=(derived.id,),
        parameters={"path": deepcopy(path), "require_connected": True},
    )
    return GeometryProgram((unitbox, derived, sweep), sweep.id, "profile_sweep")


class StrictUnitBoxOperatorsTest(SimpleTestCase):
    def test_typed_surface_evaluator_preserves_existing_solid_geometry_hashes(self):
        programs = {
            "circularize": unitbox_circularize_program(
                radius_x=2.0,
                radius_y=1.0,
                height=0.4,
            ),
            "matrix_array": unitbox_matrix_array_program(),
            "profile_sweep_3d": unitbox_profile_sweep_program(
                [[0.0, 0.0, 1.0], [2.0, 1.0, 2.5], [4.0, 1.5, 5.0]]
            ),
        }
        expected_hashes = {
            "circularize": (
                "0c8437f125b96b0c38493397ec3ddfc2a"
                "e0f674ff496f62a089223d8fdb54aff"
            ),
            "matrix_array": (
                "9c2f84f85946f704654ad98f401b0e2c"
                "2838e17f744a72f6f183c94bb1fe0e85"
            ),
            "profile_sweep_3d": (
                "dc571a223ffe96bfc7e911248073e497e"
                "34aef7484b2e143a5548f8e0602dfe4"
            ),
        }

        for operator, program in programs.items():
            with self.subTest(operator=operator):
                result = compile_geometry_program(program)

                self.assertEqual(result.status, "compiled", result.issues)
                self.assertEqual(
                    result.geometry_hash,
                    expected_hashes[operator],
                )

    def test_circularize_consumes_unitbox_derived_input_deterministically(self):
        program = unitbox_circularize_program(
            radius_x=2.0,
            radius_y=1.0,
            height=0.4,
        )

        first = compile_geometry_program(program)
        second = compile_geometry_program(program)

        self.assertEqual(first.status, "compiled", first.issues)
        self.assertEqual(first.metrics["component_count"], 1)
        self.assertTrue(first.metrics["watertight"])
        self.assertTrue(first.metrics["manifold"])
        self.assertTrue(exactly_one_canonical_unitbox(first.program))
        self.assertEqual(first.program.program_hash(), second.program.program_hash())
        self.assertEqual(first.geometry_hash, second.geometry_hash)
        self.assertEqual(
            first.metrics["bounds"],
            [[4.0, -3.0, 2.0], [8.0, -1.0, 2.4]],
        )
        row = next(row for row in first.trace if row["operator"] == "circularize")
        self.assertEqual(
            row["macro_expansion"],
            [
                "live_bounds",
                "bounded_circular_section",
                "extrude",
                "unitbox_consumed",
            ],
        )

    def test_circularize_segments_change_geometry_hash(self):
        coarse = compile_geometry_program(
            unitbox_circularize_program(
                radius_x=2.0, radius_y=1.0, height=0.4, segments=8
            )
        )
        fine = compile_geometry_program(
            unitbox_circularize_program(
                radius_x=2.0, radius_y=1.0, height=0.4, segments=48
            )
        )

        self.assertEqual(coarse.status, "compiled", coarse.issues)
        self.assertEqual(fine.status, "compiled", fine.issues)
        self.assertNotEqual(coarse.geometry_hash, fine.geometry_hash)

    def test_matrix_array_applies_each_explicit_rotation_and_unions_connected(self):
        program = unitbox_matrix_array_program()

        result = compile_geometry_program(program)

        self.assertEqual(result.status, "compiled", result.issues)
        self.assertEqual(result.metrics["component_count"], 1)
        self.assertTrue(result.metrics["watertight"])
        self.assertTrue(result.metrics["manifold"])
        self.assertTrue(exactly_one_canonical_unitbox(result.program))
        row = next(row for row in result.trace if row["operator"] == "matrix_array")
        self.assertEqual(len(row["matrix_entries"]), 3)
        self.assertEqual(
            [entry["matrix_index"] for entry in row["matrix_entries"]],
            [0, 1, 2],
        )
        self.assertEqual(
            [entry["matrix4"] for entry in row["matrix_entries"]],
            _OVERLAPPING_ROTATION_MATRICES,
        )

    def test_matrix_array_rejects_malformed_nonfinite_and_nonaffine_matrices(self):
        malformed = deepcopy(_OVERLAPPING_ROTATION_MATRICES)
        malformed[0] = [[1.0, 0.0], [0.0, 1.0]]
        nonfinite = deepcopy(_OVERLAPPING_ROTATION_MATRICES)
        nonfinite[1][0][0] = float("inf")
        nonaffine = deepcopy(_OVERLAPPING_ROTATION_MATRICES)
        nonaffine[2][3] = [0.0, 0.0, 0.25, 1.0]

        for matrices in (malformed, nonfinite, nonaffine):
            with self.subTest(matrices=matrices):
                result = compile_geometry_program(
                    unitbox_matrix_array_program(matrices)
                )
                self.assertEqual(result.status, "invalid_program")
                self.assertIn(
                    "invalid_matrix_array_matrix",
                    {issue.code for issue in result.issues},
                )

    def test_matrix_array_requires_two_to_twenty_four_explicit_matrices(self):
        for matrices in ([], [_OVERLAPPING_ROTATION_MATRICES[0]], [*_OVERLAPPING_ROTATION_MATRICES] * 9):
            with self.subTest(count=len(matrices)):
                result = compile_geometry_program(
                    unitbox_matrix_array_program(matrices)
                )
                self.assertEqual(result.status, "invalid_program")
                self.assertIn(
                    "matrix_array_count_out_of_bounds",
                    {issue.code for issue in result.issues},
                )

    def test_matrix_array_rejects_disconnected_union_when_required(self):
        separated = deepcopy(_OVERLAPPING_ROTATION_MATRICES[:2])
        separated[1][0][3] += 20.0

        result = compile_geometry_program(unitbox_matrix_array_program(separated))

        self.assertEqual(result.status, "compile_failed")
        self.assertEqual(result.issues[0].code, "disconnected_matrix_array")

    def test_profile_sweep_3d_reaches_endpoint_elevations_and_stays_connected(self):
        path = [[0.0, 0.0, 1.0], [2.0, 1.0, 2.5], [4.0, 1.5, 5.0]]
        program = unitbox_profile_sweep_program(path)

        result = compile_geometry_program(program)

        self.assertEqual(result.status, "compiled", result.issues)
        self.assertEqual(result.metrics["component_count"], 1)
        self.assertTrue(result.metrics["bounds"][0][2] <= path[0][2])
        self.assertTrue(result.metrics["bounds"][1][2] >= path[-1][2])
        self.assertTrue(result.metrics["watertight"])
        self.assertTrue(result.metrics["manifold"])
        self.assertTrue(exactly_one_canonical_unitbox(result.program))
        row = next(
            row for row in result.trace if row["operator"] == "profile_sweep_3d"
        )
        self.assertEqual(row["operator_metrics"]["frame_count"], 3)
        self.assertAlmostEqual(row["operator_metrics"]["path_length"], 5.932953, places=6)
        self.assertEqual(
            row["macro_expansion"],
            [
                "live_bounds",
                "parallel_transport_frames",
                "section_hulls",
                "union",
                "unitbox_consumed",
            ],
        )

    def test_profile_sweep_3d_rejects_repeated_and_zero_length_paths(self):
        cases = (
            (
                [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [0.0, 0.0, 0.0]],
                "repeated_profile_sweep_point",
            ),
            (
                [[2.0, 3.0, 4.0], [2.0, 3.0, 4.0]],
                "zero_length_profile_sweep_path",
            ),
        )
        for path, issue_code in cases:
            with self.subTest(issue_code=issue_code):
                result = compile_geometry_program(
                    unitbox_profile_sweep_program(path)
                )
                self.assertEqual(result.status, "invalid_program")
                self.assertIn(issue_code, {issue.code for issue in result.issues})
