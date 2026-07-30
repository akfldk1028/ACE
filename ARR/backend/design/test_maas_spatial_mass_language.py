"""Direct-authorship contracts for the generic spatial MASS language."""

from __future__ import annotations

from dataclasses import replace

from django.test import SimpleTestCase

from design.maas.creative_program_author import authored_programs_from_payload
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
