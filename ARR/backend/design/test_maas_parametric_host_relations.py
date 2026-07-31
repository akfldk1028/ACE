from __future__ import annotations

import unittest

from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.base_seeds import base_seed_program, profiled_prism_parameters
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.host_face_relations import (
    ATTACH_PARAMETER_SPACE,
    sample_face_attachment_parameters,
)
from design.maas.geometry_language.universal_form_bank import universal_form_programs


class ParametricHostRelationTests(unittest.TestCase):
    def test_triangular_profile_is_a_real_watertight_plan_primitive(self):
        program = base_seed_program("profiled_prism", variation_index=1)
        primitive = program.nodes[0]
        result = compile_geometry_program(program)

        self.assertEqual(primitive.parameters["profile_family"], "triangular")
        self.assertEqual(len(primitive.parameters["points"]), 3)
        self.assertEqual(result.status, "compiled")
        self.assertTrue(result.metrics["watertight"])
        self.assertEqual(result.metrics["component_count"], 1)

    def test_attach_resolves_from_live_host_bounds_not_absolute_coordinates(self):
        parameters = sample_face_attachment_parameters(0, 0.5, 0.5)
        small = self._attach_program((10.0, 8.0, 6.0), parameters)
        large = self._attach_program((20.0, 16.0, 12.0), parameters)
        small_result = compile_geometry_program(small)
        large_result = compile_geometry_program(large)
        small_trace = next(row for row in small_result.trace if row["operator"] == "attach")
        large_trace = next(row for row in large_result.trace if row["operator"] == "attach")
        small_resolution = small_trace["host_relation_resolution"]
        large_resolution = large_trace["host_relation_resolution"]

        self.assertEqual(parameters["parameter_space"], ATTACH_PARAMETER_SPACE)
        self.assertEqual(small_result.status, "compiled")
        self.assertEqual(large_result.status, "compiled")
        self.assertEqual(small_result.metrics["component_count"], 1)
        self.assertEqual(large_result.metrics["component_count"], 1)
        for small_value, large_value in zip(
            small_resolution["target_span"], large_resolution["target_span"]
        ):
            self.assertAlmostEqual(large_value, small_value * 2.0, places=6)

    def test_universal_form_bank_supplies_triangle_and_face_attach_graphs(self):
        programs = universal_form_programs(0)
        triangular = [
            program for program in programs
            if any(
                node.operator == "extruded_polygon"
                and node.parameters.get("profile_family") == "triangular"
                for node in program.nodes
            )
        ]
        attached = [
            program for program in programs
            if any(node.operator == "attach" for node in program.nodes)
        ]

        self.assertTrue(triangular)
        self.assertTrue(attached)
        self.assertTrue(all(
            compile_geometry_program(program).status == "compiled"
            for program in (*triangular, *attached)
        ))

    @staticmethod
    def _attach_program(
        host_size: tuple[float, float, float],
        parameters: dict[str, object],
    ) -> GeometryProgram:
        host = GeometryNode(
            "host", "primitive", "box",
            parameters={
                "width": host_size[0],
                "depth": host_size[1],
                "height": host_size[2],
            },
            semantic_role="base_seed",
        )
        guest = GeometryNode(
            "guest", "primitive", "extruded_polygon",
            parameters=profiled_prism_parameters(1),
            semantic_role="attached_guest_volume",
        )
        attach = GeometryNode(
            "attached", "composition", "attach",
            inputs=(host.id, guest.id),
            parameters=dict(parameters),
            semantic_role="dominant_mass",
        )
        return GeometryProgram((host, guest, attach), attach.id, name="attach_probe")


if __name__ == "__main__":
    unittest.main()
