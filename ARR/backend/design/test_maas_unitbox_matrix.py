"""Contracts for the one-UnitBox homogeneous-matrix MASS authority."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from shapely.affinity import rotate
from shapely.geometry import box

from design.maas.book_exploration_graph import build_book_exploration_graph
from design.maas.geometry_language.affine_matrix import (
    compose_matrix4,
    identity_matrix4,
    inverse_matrix4,
    matrix4_for_transform,
    transform_point3,
    validate_matrix4,
)
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.affine_normalization import (
    normalize_affine_basevolume_program,
)
from design.maas.geometry_language.execution_passport import build_mass_execution_passport
from design.maas.geometry_language.programs import architectural_shape_programs
from design.maas.geometry_language.source_bridge import (
    append_site_placement_matrix,
    derive_host_fit_transform,
)
from design.maas.single_execution import execute_single_mass


def _maximum_vertex_delta(
    actual: tuple[tuple[float, float, float], ...],
    expected: tuple[tuple[float, float, float], ...],
) -> float:
    """Return the largest corresponding-vertex delta."""

    if len(actual) != len(expected):
        return float("inf")
    return max(
        sum((left[index] - right[index]) ** 2 for index in range(3)) ** 0.5
        for left, right in zip(actual, expected)
    )


class UnitBoxMatrixContractTest(SimpleTestCase):
    def test_authored_affine_chain_normalizes_to_explicit_matrix4(self):
        program = GeometryProgram(
            nodes=(
                GeometryNode(
                    "authored_box",
                    "primitive",
                    "box",
                    parameters={
                        "width": 1.0,
                        "depth": 1.0,
                        "height": 1.0,
                        "center": True,
                    },
                    semantic_role="base_authority",
                ),
                GeometryNode(
                    "authored_scale",
                    "transform",
                    "scale",
                    inputs=("authored_box",),
                    parameters={"vector": [2.8, 0.62, 0.48]},
                    semantic_role="base_seed",
                ),
                GeometryNode(
                    "authored_rotate",
                    "transform",
                    "rotate",
                    inputs=("authored_scale",),
                    parameters={"axis": "z", "angle_degrees": 17.0},
                    semantic_role="base_orientation",
                ),
                GeometryNode(
                    "authored_bend",
                    "modifier",
                    "bend",
                    inputs=("authored_rotate",),
                    parameters={
                        "axis": "y",
                        "angle_degrees": 18.0,
                        "subdivisions": 4,
                    },
                    semantic_role="architectural_modifier",
                ),
            ),
            root_id="authored_bend",
            name="authored_affine_chain",
        )

        expected = compile_geometry_program(program)
        normalized = normalize_affine_basevolume_program(program)
        actual = compile_geometry_program(normalized)
        operators = [node.operator for node in normalized.topological_nodes()]

        self.assertEqual(operators.count("box"), 1)
        self.assertFalse(
            {"scale", "rotate", "translate", "mirror", "shear"}
            & set(operators)
        )
        unitbox = next(
            node for node in normalized.nodes
            if node.kind == "primitive" and node.operator == "box"
        )
        basevolume = next(
            node for node in normalized.nodes
            if node.inputs == (unitbox.id,)
        )
        self.assertEqual(basevolume.operator, "matrix4")
        self.assertEqual(
            basevolume.provenance["composed_matrix4_node_ids"],
            ["authored_box_matrix4", "authored_scale", "authored_rotate"],
        )
        self.assertEqual(actual.geometry_hash, expected.geometry_hash)

    def test_affine_inverse_round_trips_and_rejects_singular_matrices(self):
        matrix = compose_matrix4(
            matrix4_for_transform("scale", {"vector": [2.0, 3.0, 4.0]}),
            matrix4_for_transform("rotate", {"angles": [11.0, -7.0, 23.0]}),
            matrix4_for_transform("translate", {"vector": [5.0, 7.0, 11.0]}),
        )
        inverse = inverse_matrix4(matrix)

        self.assertEqual(inverse[3], (0.0, 0.0, 0.0, 1.0))
        self.assertEqual(
            transform_point3(inverse, transform_point3(matrix, (1.0, 2.0, 3.0))),
            (1.0, 2.0, 3.0),
        )
        tiny_scale = matrix4_for_transform(
            "scale",
            {"vector": [1e-5, 1e-5, 1e-5]},
        )
        self.assertEqual(
            transform_point3(
                inverse_matrix4(tiny_scale),
                transform_point3(tiny_scale, (1.0, 2.0, 3.0)),
            ),
            (1.0, 2.0, 3.0),
        )
        with self.assertRaises(ValueError):
            inverse_matrix4((
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            ))

    def test_site_fit_matrix_recompiles_to_the_exact_fitted_vertices(self):
        unit = GeometryNode(
            "unit_box",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        slab = GeometryNode(
            "slab",
            "transform",
            "matrix4",
            inputs=(unit.id,),
            parameters={
                "matrix4": [
                    [18.0, 0.0, 0.0, 0.0],
                    [0.0, 7.0, 0.0, 0.0],
                    [0.0, 0.0, 5.0, 0.0],
                    [0.0, 0.0, 0.0, 1.0],
                ],
            },
        )
        authored_rotation = GeometryNode(
            "authored_rotation",
            "transform",
            "rotate",
            inputs=(slab.id,),
            parameters={"axis": "z", "angle_degrees": 17.0},
        )
        program = GeometryProgram(
            (unit, slab, authored_rotation),
            authored_rotation.id,
            "rotated_unitbox_slab",
        )
        compilation = compile_geometry_program(program)
        host = rotate(
            box(40.0, 70.0, 86.0, 96.0),
            31.0,
            origin=(63.0, 83.0),
        )

        fit = derive_host_fit_transform(compilation, host)
        placed = append_site_placement_matrix(program, fit)
        recompiled = compile_geometry_program(placed)

        self.assertEqual(compilation.status, "compiled", compilation.issues)
        self.assertEqual(recompiled.status, "compiled", recompiled.issues)
        self.assertEqual(fit.matrix4[3], (0.0, 0.0, 0.0, 1.0))
        self.assertEqual(len(recompiled.vertices), len(fit.world_vertices))
        self.assertLess(
            _maximum_vertex_delta(recompiled.vertices, fit.world_vertices),
            1e-7,
        )
        canonical_boxes = [
            node for node in placed.nodes
            if node.kind == "primitive" and node.operator == "box"
        ]
        self.assertEqual(len(canonical_boxes), 1)
        self.assertEqual(
            canonical_boxes[0].parameters,
            {"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        self.assertEqual(placed.root_id, "site_placement_matrix4")
        self.assertEqual(placed.nodes[-1].operator, "matrix4")
        self.assertEqual(placed.nodes[-1].inputs, (program.root_id,))
        self.assertEqual(
            placed.metadata["site_placement"]["upstream_program_hash"],
            program.program_hash(),
        )

    def test_multiple_authored_boxes_share_one_unitbox_authority(self):
        first = GeometryNode(
            "first_box",
            "primitive",
            "box",
            parameters={"width": 8.0, "depth": 5.0, "height": 3.0},
        )
        second = GeometryNode(
            "second_box",
            "primitive",
            "box",
            parameters={"width": 4.0, "depth": 2.0, "height": 6.0, "center": True},
        )
        union = GeometryNode(
            "result",
            "boolean",
            "union",
            inputs=(first.id, second.id),
        )

        result = compile_geometry_program(GeometryProgram((first, second, union), union.id))
        boxes = [
            node for node in result.program.nodes
            if node.kind == "primitive" and node.operator == "box"
        ]
        matrices = [
            node for node in result.program.nodes
            if node.kind == "transform" and node.operator == "matrix4"
        ]

        self.assertEqual(result.status, "compiled", result.issues)
        self.assertEqual(len(boxes), 1)
        self.assertEqual(
            boxes[0].parameters,
            {"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        self.assertEqual(len(matrices), 2)
        self.assertTrue(all(node.inputs == (boxes[0].id,) for node in matrices))

    def test_single_execution_persists_the_normalized_unitbox_program(self):
        program = GeometryProgram((
            GeometryNode(
                "host",
                "primitive",
                "box",
                parameters={"width": 12.0, "depth": 8.0, "height": 5.0},
            ),
            GeometryNode(
                "guest",
                "primitive",
                "box",
                parameters={"width": 4.0, "depth": 8.0, "height": 7.0},
            ),
            GeometryNode(
                "result",
                "boolean",
                "union",
                inputs=("host", "guest"),
            ),
        ), "result", "raw_multi_box")

        with TemporaryDirectory() as directory:
            result = execute_single_mass(
                program,
                output_root=Path(directory),
                execution_id="unitbox-persistence",
            )
            persisted = json.loads(result.program_path.read_text(encoding="utf-8"))

        primitives = [
            node for node in persisted["nodes"]
            if node["kind"] == "primitive" and node["operator"] == "box"
        ]
        matrices = [
            node for node in persisted["nodes"]
            if node["kind"] == "transform" and node["operator"] == "matrix4"
        ]
        self.assertTrue(result.geometry_ready)
        self.assertEqual(len(primitives), 1)
        self.assertEqual(len(matrices), 2)
        self.assertEqual(persisted["metadata"]["box_instance_contract"], "shared_unitbox_matrix4")

    def test_affine_helpers_use_homogeneous_column_vector_contract(self):
        self.assertEqual(identity_matrix4()[3], (0.0, 0.0, 0.0, 1.0))

        scale = matrix4_for_transform("scale", {"vector": [2.0, 3.0, 4.0]})
        move = matrix4_for_transform("translate", {"vector": [5.0, 7.0, 11.0]})
        composed = compose_matrix4(scale, move)

        # Program order is scale, then move: M = T * S.
        self.assertEqual(transform_point3(composed, (1.0, 1.0, 1.0)), (7.0, 10.0, 15.0))

    def test_pivoted_scale_keeps_pivot_fixed(self):
        matrix = matrix4_for_transform(
            "scale",
            {"vector": [2.0, 2.0, 2.0], "pivot": [1.0, 1.0, 1.0]},
        )
        self.assertEqual(transform_point3(matrix, (1.0, 1.0, 1.0)), (1.0, 1.0, 1.0))
        self.assertEqual(transform_point3(matrix, (2.0, 1.0, 1.0)), (3.0, 1.0, 1.0))

    def test_explicit_matrix_rejects_non_affine_last_row(self):
        with self.assertRaises(ValueError):
            validate_matrix4([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 1],
            ])

    def test_compiler_accepts_explicit_matrix4_transform(self):
        unit = GeometryNode(
            "unit_box",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        transformed = GeometryNode(
            "derived_host",
            "transform",
            "matrix4",
            inputs=(unit.id,),
            parameters={
                "matrix4": [
                    [2.0, 0.0, 0.0, 5.0],
                    [0.0, 3.0, 0.0, 7.0],
                    [0.0, 0.0, 4.0, 11.0],
                    [0.0, 0.0, 0.0, 1.0],
                ],
            },
        )
        result = compile_geometry_program(GeometryProgram((unit, transformed), transformed.id))

        self.assertEqual(result.status, "compiled", result.issues)
        self.assertEqual(result.metrics["bounds"], [[5.0, 7.0, 11.0], [7.0, 10.0, 15.0]])
        self.assertEqual(result.trace[-1]["matrix4"][3], [0.0, 0.0, 0.0, 1.0])

    def test_affine_macro_expansion_records_its_matrix4(self):
        unit = GeometryNode(
            "unit_box",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        lean = GeometryNode(
            "lean",
            "macro",
            "leaning_tower",
            inputs=(unit.id,),
            parameters={"direction": "x", "amount": 0.25},
        )
        result = compile_geometry_program(GeometryProgram((unit, lean), lean.id))

        self.assertEqual(result.status, "compiled", result.issues)
        self.assertEqual(result.trace[-1]["matrix4"][0][2], 0.25)
        self.assertEqual(result.trace[-1]["matrix_role"], "macro_affine_expansion")

    def test_exploration_graph_has_one_root_and_derived_book_volumes(self):
        graph = build_book_exploration_graph()
        nodes = {node["id"]: node for node in graph["nodes"]}

        self.assertEqual(graph["counts"]["base_model_count"], 1)
        self.assertEqual(graph["counts"]["derived_volume_count"], 5)
        self.assertEqual(graph["root_node_ids"], ["book:base-model:1-1"])
        self.assertEqual(nodes["book:base-model:1-1"]["attributes"]["matrix4"], [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])
        self.assertTrue(any(
            edge["source"] == "book:base-model:1-1"
            and edge["target"] == "book:derived-volume:3-8"
            and edge["kind"] == "derives_volume"
            for edge in graph["edges"]
        ))

    def test_passport_exposes_honest_pending_elevation_continuation(self):
        unit = GeometryNode(
            "unit_box",
            "primitive",
            "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        )
        compilation = compile_geometry_program(GeometryProgram((unit,), unit.id))
        passport = build_mass_execution_passport(compilation)
        nodes = {node["id"]: node for node in passport["activation_graph"]["nodes"]}

        self.assertEqual(nodes["elevation:mesh_handoff"]["status"], "not_evaluated")
        self.assertEqual(nodes["elevation:condition_pack"]["status"], "not_evaluated")
        self.assertEqual(nodes["elevation:result"]["status"], "not_evaluated")
        self.assertFalse(nodes["elevation:result"]["evidence"]["artifact_exists"])

    def test_reference_shape_boxes_lower_from_unitbox_through_matrix4(self):
        program = architectural_shape_programs()[10]
        primitive = next(node for node in program.nodes if node.kind == "primitive")
        derived = next(node for node in program.nodes if node.operator == "matrix4")

        self.assertEqual(primitive.parameters, {"width": 1.0, "depth": 1.0, "height": 1.0})
        self.assertEqual(derived.inputs, (primitive.id,))
        self.assertEqual(derived.parameters["matrix4"][0][0], 5.0)
        self.assertEqual(derived.parameters["matrix4"][1][1], 5.0)
        self.assertEqual(derived.parameters["matrix4"][2][2], 16.0)
        self.assertEqual(program.node_map[program.root_id].inputs, (derived.id,))

    def test_all_eighteen_reference_shapes_compile_after_unitbox_lowering(self):
        programs = architectural_shape_programs()
        self.assertEqual(len(programs), 18)
        for program in programs:
            with self.subTest(program=program.name):
                boxes = [
                    node for node in program.nodes
                    if node.kind == "primitive" and node.operator == "box"
                ]
                self.assertEqual(len(boxes), 1)
                self.assertEqual(
                    (
                        boxes[0].parameters["width"],
                        boxes[0].parameters["depth"],
                        boxes[0].parameters["height"],
                    ),
                    (1.0, 1.0, 1.0),
                )
                self.assertGreaterEqual(
                    sum(
                        node.kind == "transform" and node.operator == "matrix4"
                        for node in program.nodes
                    ),
                    1,
                )
                compilation = compile_geometry_program(program)
                self.assertEqual(compilation.status, "compiled", compilation.issues)
                self.assertTrue(compilation.metrics["watertight"])
                self.assertEqual(compilation.metrics["component_count"], 1)
