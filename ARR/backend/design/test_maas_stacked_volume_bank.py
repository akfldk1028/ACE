"""The multi-volume lane is the only supply that can compose several volumes.

The rest of the bank is a one-body language, so these programs are the whole
basis for the composition the reference competition massing is made of:
several clean volumes stacked and shifted, a lifted ground, setback terraces.
They are worth nothing unless they survive compilation and the BOOK layer, so
that is what is asserted here.
"""

from collections import Counter

from django.test import SimpleTestCase

from design.maas.geometry_language.book_adapter import (
    apply_book_projection_to_geometry_program,
)
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.stacked_volume_bank import (
    stacked_volume_programs,
)
from design.maas.geometry_language.universal_form_bank import (
    universal_form_programs,
)
from design.maas.program_massing.sequences import program_seed_sequences


def _volume_instances(program):
    """Volumes are Matrix4 placements of the one canonical UnitBox."""

    return sum(node.operator == "matrix4" for node in program.nodes)


class StackedVolumeProgramTests(SimpleTestCase):
    def test_every_program_compiles_to_one_closed_component(self):
        for page in (0, 1, 2):
            for program in stacked_volume_programs(page):
                with self.subTest(page=page, name=program.name):
                    result = compile_geometry_program(program)

                    self.assertEqual(result.status, "compiled")
                    self.assertEqual(
                        (result.metrics or {}).get("component_count"), 1,
                    )
                    self.assertEqual([
                        issue.code for issue in (result.issues or ())
                    ], [])

    def test_every_program_actually_places_more_than_one_volume(self):
        for program in stacked_volume_programs(0):
            with self.subTest(name=program.name):
                self.assertGreaterEqual(_volume_instances(program), 2)

    def test_all_volumes_descend_from_the_one_canonical_unitbox(self):
        for program in stacked_volume_programs(0):
            with self.subTest(name=program.name):
                primitives = [
                    node for node in program.nodes if node.kind == "primitive"
                ]

                self.assertEqual(len(primitives), 1)
                self.assertEqual(primitives[0].operator, "box")
                self.assertEqual(
                    dict(primitives[0].parameters),
                    {"width": 1.0, "depth": 1.0, "height": 1.0},
                )

    def test_the_lane_survives_book_projection(self):
        sequences = program_seed_sequences("cultural")

        for program in stacked_volume_programs(0):
            for sequence in sequences:
                with self.subTest(name=program.name, seed=sequence.name):
                    projected = apply_book_projection_to_geometry_program(
                        program, sequence,
                    )
                    result = compile_geometry_program(projected)

                    self.assertEqual(result.status, "compiled")
                    self.assertEqual(
                        (result.metrics or {}).get("component_count"), 1,
                    )

    def test_pages_do_not_replay_each_other(self):
        first = {program.program_hash() for program in stacked_volume_programs(0)}
        second = {program.program_hash() for program in stacked_volume_programs(1)}

        self.assertFalse(first & second)

    def test_no_parcel_coordinate_or_program_label_leaks_into_the_lane(self):
        for program in stacked_volume_programs(0):
            with self.subTest(name=program.name):
                self.assertNotIn("pnu", program.name.lower())
                for key in ("parcel_coordinates_in_program", "program_conditioned"):
                    self.assertFalse(program.metadata.get(key, False))


class MultiVolumeLaneInBankTests(SimpleTestCase):
    def test_the_bank_now_carries_a_multi_volume_lane(self):
        lanes = Counter(
            str(program.metadata.get("form_bank_lane"))
            for program in universal_form_programs(0)
        )

        self.assertGreater(lanes["multi_volume_composition"], 0)

    def test_the_lane_is_what_lifts_the_bank_off_one_body(self):
        bank = universal_form_programs(0)
        combining = {"union", "attach", "matrix_array"}

        def combines(program):
            return sum(
                node.operator in combining for node in program.nodes
            ) >= 2

        multi = [program for program in bank if combines(program)]

        # Before this lane exactly one program in the whole page combined
        # volumes more than once.
        self.assertGreater(len(multi), 1)
