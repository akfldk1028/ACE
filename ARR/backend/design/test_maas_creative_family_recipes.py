from __future__ import annotations

from math import sqrt
import unittest

from design.maas.creative_family_contract import CreativeRecipeContext
from design.maas.creative_family_registry import registered_creative_recipes
from design.maas.geometry_language.compiler import compile_geometry_program


def _canonical_unitboxes(program):
    return [
        node
        for node in program.nodes
        if (
            node.kind == "primitive"
            and node.operator == "box"
            and node.parameters
            == {"width": 1.0, "depth": 1.0, "height": 1.0}
        )
    ]


def _cross_length(left, right):
    cross = (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )
    return sqrt(sum(value * value for value in cross))


class CreativeFamilyRecipeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = CreativeRecipeContext(
            variation_index=2,
            book_scope_label="1/2",
            capacity_band="balanced_yield",
        )
        cls.specs = registered_creative_recipes()
        cls.results = {
            spec.family_id: spec.builder(cls.context)
            for spec in cls.specs
        }

    def test_all_fifteen_recipes_preserve_strict_unitbox_lineage(self):
        self.assertEqual(len(self.specs), 15)
        for spec in self.specs:
            result = self.results[spec.family_id]
            program = result.program

            self.assertEqual(
                len(_canonical_unitboxes(program)),
                1,
                spec.family_id,
            )
            self.assertTrue(
                all(
                    node.operator == "matrix4"
                    for node in program.nodes
                    if node.kind == "transform"
                ),
                spec.family_id,
            )
            self.assertIn(result.contact_node_id, program.node_map)
            self.assertEqual(result.form_class, spec.form_class)
            self.assertEqual(result.contact_type, spec.contact_type)

    def test_all_fifteen_recipe_witnesses_compile_as_connected_solids(self):
        for spec in self.specs:
            result = self.results[spec.family_id]
            compilation = compile_geometry_program(result.program)
            trace = {
                row["node_id"]: row
                for row in compilation.trace
            }

            self.assertFalse(compilation.issues, spec.family_id)
            self.assertEqual(
                compilation.metrics.get("component_count"),
                1,
                spec.family_id,
            )
            self.assertGreater(
                float(
                    trace[result.contact_node_id].get("volume")
                    or 0.0
                ),
                0.0,
                spec.family_id,
            )

    def test_only_the_stepped_recipe_contains_stepped_topology(self):
        stepped_operators = {"stack", "stepped_mass", "terrace", "setback"}
        for spec in self.specs:
            operators = {
                node.operator
                for node in self.results[spec.family_id].program.nodes
            }
            if spec.family_id == "stepped":
                self.assertIn("stepped_mass", operators)
            else:
                self.assertFalse(
                    operators & stepped_operators,
                    spec.family_id,
                )

    def test_triangular_shard_uses_two_nonparallel_clip_planes(self):
        program = self.results["triangular_shard"].program
        clips = [
            node
            for node in program.nodes
            if node.kind == "modifier" and node.operator == "clip"
        ]

        self.assertGreaterEqual(len(clips), 2)
        normals = [
            tuple(float(value) for value in node.parameters["normal"])
            for node in clips
        ]
        self.assertTrue(any(
            _cross_length(left, right) > 1e-6
            for index, left in enumerate(normals)
            for right in normals[index + 1 :]
        ))

    def test_oblique_crystal_records_clip_shear_and_loft_evidence(self):
        result = self.results["oblique_crystal"]
        nodes = result.program.nodes
        evidence = " ".join(
            " ".join((
                node.operator,
                node.semantic_role,
                str(node.provenance),
            ))
            for node in nodes
        )

        self.assertIn("clip", {node.operator for node in nodes})
        self.assertIn("shear", evidence)
        self.assertIn("loft", evidence)
        self.assertNotIn(
            "stepped_mass",
            {node.operator for node in nodes},
        )

    def test_thin_disc_cluster_has_circularize_and_independent_matrix_branches(self):
        program = self.results["thin_disc_cluster"].program
        circular = next(
            node for node in program.nodes if node.operator == "circularize"
        )
        branches = [
            node
            for node in program.nodes
            if (
                node.kind == "transform"
                and node.operator == "matrix4"
                and node.inputs == (circular.id,)
            )
        ]

        self.assertGreaterEqual(len(branches), 3)
        self.assertEqual(
            len({
                tuple(tuple(row) for row in node.parameters["matrix4"])
                for node in branches
            }),
            len(branches),
        )

    def test_interlocking_discs_use_array_and_occupied_contact_witness(self):
        result = self.results["interlocking_tilted_discs"]
        operators = {node.operator for node in result.program.nodes}
        witness = result.program.node_map[result.contact_node_id]

        self.assertIn("circularize", operators)
        self.assertIn("matrix_array", operators)
        self.assertIn(witness.operator, {"bridge", "intersection", "union"})
        self.assertIn(
            witness.semantic_role,
            {
                "interlocking_disc_contact",
                "interlocking_disc_bridge",
            },
        )

    def test_long_span_has_two_supports_and_occupied_sweep_connector(self):
        result = self.results["long_span_bridge"]
        program = result.program
        supports = [
            node
            for node in program.nodes
            if node.semantic_role == "long_span_support"
        ]
        witness = program.node_map[result.contact_node_id]

        self.assertEqual(len(supports), 2)
        self.assertIn(witness.operator, {"bridge", "profile_sweep_3d"})
        self.assertEqual(
            witness.semantic_role,
            "occupied_long_span_connector",
        )
        self.assertGreater(result.recipe_parameters["span_length"], 1.0)
        self.assertEqual(
            result.recipe_parameters["support_contact_count"],
            2,
        )
        self.assertTrue(
            result.recipe_parameters["occupied_connector"],
        )


if __name__ == "__main__":
    unittest.main()
