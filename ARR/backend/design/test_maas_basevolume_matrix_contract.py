from django.test import SimpleTestCase

from design.maas.geometry_language.base_seeds import base_seed_program
from design.maas.geometry_language.compiler import compile_geometry_program


class BaseVolumeMatrixContractTests(SimpleTestCase):
    def test_affine_seeds_persist_explicit_matrix4(self):
        for seed_id in ("block", "slab", "bar", "tower"):
            with self.subTest(seed_id=seed_id):
                program = base_seed_program(seed_id)
                primitive_nodes = [
                    node for node in program.nodes
                    if node.kind == "primitive"
                ]
                matrix_nodes = [
                    node for node in program.nodes
                    if node.operator == "matrix4"
                ]

                self.assertEqual(len(primitive_nodes), 1)
                self.assertEqual(primitive_nodes[0].operator, "box")
                self.assertEqual(len(matrix_nodes), 1)
                self.assertEqual(
                    matrix_nodes[0].parameters["matrix4"][3],
                    [0.0, 0.0, 0.0, 1.0],
                )
                self.assertEqual(program.root_id, matrix_nodes[0].id)
                self.assertEqual(
                    program.metadata["canonical_root"],
                    "1/1 UnitBox",
                )
                self.assertEqual(
                    program.metadata["basevolume_affine_authority"],
                    "explicit_matrix4",
                )

                compilation = compile_geometry_program(program)
                self.assertEqual(
                    compilation.status,
                    "compiled",
                    compilation.issues,
                )
                self.assertEqual(compilation.metrics["component_count"], 1)
