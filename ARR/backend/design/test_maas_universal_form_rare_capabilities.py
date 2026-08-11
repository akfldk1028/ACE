from django.test import SimpleTestCase

from design.maas.geometry_language import compile_geometry_program
from design.maas.geometry_language.programs import (
    rare_unitbox_capability_programs,
)
from design.maas.geometry_language.universal_form_bank import (
    universal_form_bank_contract,
    universal_form_programs,
)


RARE_FAMILIES = {
    "unitbox_triangular_clip",
    "unitbox_oblique_clip",
    "unitbox_elliptical_volume",
    "unitbox_interlocking_elliptical_volumes",
}


class UniversalFormRareCapabilityTests(SimpleTestCase):
    def test_rare_capabilities_are_bounded_to_about_five_percent_of_page_zero(self):
        programs = universal_form_programs(0)
        rare = tuple(
            program
            for program in programs
            if program.metadata.get("family") in RARE_FAMILIES
        )

        # The page total is the sum of the bank's lanes less whatever the hash
        # dedup drops, so it moves whenever a lane is added and is bounded
        # rather than pinned. What must hold is that these four stay four and
        # stay a low share - they are a capability probe, not a quota.
        contract = universal_form_bank_contract()
        declared = sum((
            contract["synthesis_lane_program_count"],
            contract["executable_core_lane_program_count"],
            contract["rare_unitbox_capability_parent_count"],
            contract["multi_volume_lane_program_count"],
        ))
        self.assertLessEqual(len(programs), declared)
        self.assertGreaterEqual(len(programs), declared - 4)
        self.assertEqual(len(rare), 4)
        self.assertLessEqual(len(rare) / len(programs), 0.05)

    def test_rare_capabilities_descend_from_one_canonical_unitbox(self):
        programs = rare_unitbox_capability_programs()

        self.assertEqual(
            {program.metadata.get("family") for program in programs},
            RARE_FAMILIES,
        )
        for program in programs:
            with self.subTest(family=program.metadata.get("family")):
                primitives = tuple(
                    node for node in program.nodes
                    if node.kind == "primitive"
                )
                self.assertEqual(len(primitives), 1)
                self.assertEqual(primitives[0].operator, "box")
                self.assertEqual(
                    primitives[0].parameters,
                    {"width": 1.0, "depth": 1.0, "height": 1.0},
                )
                self.assertTrue(
                    primitives[0].provenance.get("unitbox_authority")
                )
                self.assertNotIn("reference_basis", program.metadata)

    def test_rare_capabilities_compile_as_connected_manifold_solids(self):
        expected_operators = {
            "unitbox_triangular_clip": {"matrix4", "clip"},
            "unitbox_oblique_clip": {"matrix4", "clip"},
            "unitbox_elliptical_volume": {"matrix4", "circularize"},
            "unitbox_interlocking_elliptical_volumes": {
                "matrix4",
                "circularize",
                "matrix_array",
                "union",
            },
        }

        for program in rare_unitbox_capability_programs():
            family = str(program.metadata.get("family") or "")
            with self.subTest(family=family):
                self.assertTrue(
                    expected_operators[family].issubset({
                        node.operator for node in program.nodes
                    })
                )
                result = compile_geometry_program(program)
                self.assertEqual(result.status, "compiled")
                self.assertEqual(result.metrics["component_count"], 1)
                self.assertTrue(result.metrics["watertight"])
                self.assertTrue(result.metrics["manifold"])

    def test_rare_capability_hashes_are_deterministic_and_distinct(self):
        first = rare_unitbox_capability_programs()
        second = rare_unitbox_capability_programs()

        self.assertEqual(
            [program.program_hash() for program in first],
            [program.program_hash() for program in second],
        )
        self.assertEqual(
            len({program.program_hash() for program in first}),
            4,
        )
