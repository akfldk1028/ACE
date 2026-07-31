"""Contracts for the one-UnitBox homogeneous-matrix MASS authority."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from design.maas.book_exploration_graph import build_book_exploration_graph
from design.maas.geometry_language.affine_matrix import (
    compose_matrix4,
    identity_matrix4,
    matrix4_for_transform,
    transform_point3,
    validate_matrix4,
)
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.execution_passport import build_mass_execution_passport
from design.maas.geometry_language.programs import architectural_shape_programs
from design.maas.single_execution import execute_single_mass


class UnitBoxMatrixContractTest(SimpleTestCase):
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
