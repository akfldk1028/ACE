"""The composition generator's guarantee is connectivity, so prove it.

A CSG solid is an r-set and a CSG tree combines primitive instances with rigid
motions and regularized booleans. The union of a scope set is one r-set
component exactly when the scopes' intersection graph is connected, which is
decidable in closed form for boxes. The generator grows a spanning tree, so
connectivity is an invariant rather than something to sample-and-reject - and
these tests check the invariant against both the predicate and manifold3d
itself, because a predicate that disagrees with the kernel is worthless.
"""

from django.test import SimpleTestCase

from design.maas.geometry_language.affine_matrix import (
    compose_matrix4,
    matrix4_to_lists,
    scale_matrix4,
    translation_matrix4,
)
from design.maas.geometry_language.ast import GeometryNode, GeometryProgram
from design.maas.geometry_language.compiler import compile_geometry_program
from design.maas.geometry_language.scope_composition import (
    ScopePlacement,
    sample_connected_scope_set,
    scope_set_is_connected,
    scopes_share_volume,
)


def _halton(index, base):
    result, factor, value = 0.0, 1.0, max(1, int(index))
    while value:
        factor /= base
        value, remainder = divmod(value, base)
        result += remainder * factor
    return result


def _sampler(offset):
    bases = (2, 3, 5, 7, 11, 13)
    return lambda index: _halton(offset * 31 + index + 1, bases[index % len(bases)])


def _program_from_scopes(placements, name):
    nodes = [GeometryNode(
        "unit_box", "primitive", "box",
        parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
        semantic_role="base_seed",
    )]
    placed = []
    for index, placement in enumerate(placements):
        node_id = f"scope_{index:02d}"
        nodes.append(GeometryNode(
            node_id, "transform", "matrix4", inputs=("unit_box",),
            parameters={"matrix4": matrix4_to_lists(compose_matrix4(
                scale_matrix4(placement.scale),
                translation_matrix4(placement.offset),
            ))},
            semantic_role="main" if index == 0 else "composed_scope",
        ))
        placed.append(node_id)
    root = placed[0]
    for index, node_id in enumerate(placed[1:], start=1):
        union_id = f"scope_union_{index:02d}"
        nodes.append(GeometryNode(
            union_id, "boolean", "union", inputs=(root, node_id),
            semantic_role="main",
        ))
        root = union_id
    return GeometryProgram(tuple(nodes), root, name, metadata={"family": "probe"})


class ScopeConnectivityPredicateTests(SimpleTestCase):
    def test_boxes_that_only_touch_do_not_share_volume(self):
        left = ScopePlacement(scale=(1.0, 1.0, 1.0), offset=(0.0, 0.0, 0.0))
        flush = ScopePlacement(scale=(1.0, 1.0, 1.0), offset=(1.0, 0.0, 0.0))
        overlapping = ScopePlacement(scale=(1.0, 1.0, 1.0), offset=(0.5, 0.0, 0.0))

        self.assertFalse(scopes_share_volume(left, flush))
        self.assertTrue(scopes_share_volume(left, overlapping))

    def test_a_disconnected_set_is_reported_as_disconnected(self):
        placements = (
            ScopePlacement(scale=(1.0, 1.0, 1.0), offset=(0.0, 0.0, 0.0)),
            ScopePlacement(scale=(1.0, 1.0, 1.0), offset=(9.0, 0.0, 0.0)),
        )

        self.assertFalse(scope_set_is_connected(placements))

    def test_a_chain_connected_only_through_a_middle_scope_is_connected(self):
        placements = (
            ScopePlacement(scale=(1.0, 1.0, 1.0), offset=(0.0, 0.0, 0.0)),
            ScopePlacement(scale=(1.0, 1.0, 1.0), offset=(1.6, 0.0, 0.0)),
            ScopePlacement(scale=(1.0, 1.0, 1.0), offset=(0.8, 0.0, 0.0)),
        )

        self.assertFalse(scopes_share_volume(placements[0], placements[1]))
        self.assertTrue(scope_set_is_connected(placements))


class ScopeSamplerInvariantTests(SimpleTestCase):
    def test_every_sampled_set_is_connected(self):
        for count in (1, 2, 3, 4, 5):
            for offset in range(120):
                with self.subTest(count=count, offset=offset):
                    placements = sample_connected_scope_set(
                        count, (12.0, 9.0, 4.0), _sampler(offset),
                    )

                    self.assertEqual(len(placements), max(1, count))
                    self.assertTrue(scope_set_is_connected(placements))

    def test_the_predicate_agrees_with_the_csg_kernel(self):
        for count in (2, 3, 4):
            for offset in range(25):
                with self.subTest(count=count, offset=offset):
                    placements = sample_connected_scope_set(
                        count, (12.0, 9.0, 4.0), _sampler(offset),
                    )
                    result = compile_geometry_program(
                        _program_from_scopes(placements, f"probe_{count}_{offset}"),
                    )

                    self.assertEqual(result.status, "compiled")
                    self.assertEqual(
                        (result.metrics or {}).get("component_count"), 1,
                    )

    def test_the_first_placement_is_always_the_untranslated_base(self):
        placements = sample_connected_scope_set(
            4, (12.0, 9.0, 4.0), _sampler(3),
        )

        self.assertEqual(placements[0].offset, (0.0, 0.0, 0.0))
        self.assertEqual(placements[0].scale, (12.0, 9.0, 4.0))

    def test_sampling_is_deterministic(self):
        first = sample_connected_scope_set(4, (12.0, 9.0, 4.0), _sampler(11))
        second = sample_connected_scope_set(4, (12.0, 9.0, 4.0), _sampler(11))

        self.assertEqual(first, second)


class SynthesisComposesVolumesTests(SimpleTestCase):
    def test_the_synthesis_lane_now_composes_and_stays_one_component(self):
        from design.maas.geometry_language.universal_form_bank import (
            universal_form_programs,
        )

        bank = universal_form_programs(0)
        synthesized = [
            program for program in bank
            if str(program.metadata.get("form_bank_lane")) == "bounded_synthesis"
        ]
        composed = [
            program for program in synthesized
            if any(node.operator == "union" for node in program.nodes)
        ]

        # The generator emitted no boolean operator at all before this.
        self.assertGreater(len(composed), 0)
        for program in composed:
            with self.subTest(name=program.name):
                result = compile_geometry_program(program)

                self.assertEqual(result.status, "compiled")
                self.assertEqual(
                    (result.metrics or {}).get("component_count"), 1,
                )
                self.assertEqual(
                    sum(node.kind == "primitive" for node in program.nodes), 1,
                )

    def test_a_composed_program_never_also_carves_a_void(self):
        from design.maas.geometry_language.synthesis import _VOID_MACROS
        from design.maas.geometry_language.universal_form_bank import (
            universal_form_programs,
        )

        for program in universal_form_programs(0):
            if str(program.metadata.get("form_bank_lane")) != "bounded_synthesis":
                continue
            operators = {node.operator for node in program.nodes}
            if "union" not in operators:
                continue
            with self.subTest(name=program.name):
                self.assertFalse(operators & _VOID_MACROS)
