"""Actual solids and support regressions for explicit relative base anchoring."""
from unittest import TestCase
import manifold3d as m3d
from design.maas.geometry_language import compiler as c
from design.maas.geometry_language.ast import GeometryNode, _parameter_issues
from design.maas.massv2.structure import assess_standing
from design.test_maas_mesh_support import source_for_solid


class MacroVerticalAnchorTests(TestCase):
    def stands(self, solid):
        source = source_for_solid(solid)
        return assess_standing(source, height_m=source.metadata['authored_height_m']).stands

    def test_grounded_branch_gains_real_support_without_changing_xy_outline(self):
        base = m3d.Manifold.cube((30, 8, 9))
        old = c._book_branch_macro(base, {}, 'branch')
        anchored = c._book_branch_macro(base, {'vertical_anchor': 'input_base'}, 'branch')
        self.assertFalse(self.stands(old))
        self.assertTrue(self.stands(anchored))
        self.assertEqual(tuple(old.bounding_box())[:2], tuple(anchored.bounding_box())[:2])

    def test_parallel_wings_and_connectors_preserve_input_base(self):
        for mode in ('array', 'pack'):
            with self.subTest(mode=mode):
                result = c._related_array_macro(m3d.Manifold.cube((30, 8, 9)),
                    {'vertical_anchor': 'input_base', 'mode': mode}, 'wings')
                self.assertAlmostEqual(result.bounding_box()[2], 0.)
                self.assertTrue(self.stands(result))
                self.assertEqual(len(result.decompose()), 1)

    def test_lifted_input_is_not_implicitly_grounded(self):
        for macro in (c._book_branch_macro, c._related_array_macro):
            with self.subTest(macro=macro.__name__):
                result = macro(m3d.Manifold.cube((30, 8, 9)).translate((0, 0, 4)),
                    {'vertical_anchor': 'input_base'}, 'lifted')
                self.assertAlmostEqual(result.bounding_box()[2], 4.)
                self.assertFalse(self.stands(result))

    def test_explicit_center_matches_omitted_legacy_mesh(self):
        for macro in (c._book_branch_macro, c._related_array_macro):
            base = m3d.Manifold.cube((30, 8, 9)).translate((0, 0, 8))
            a, b = macro(base, {}, 'a'), macro(base, {'vertical_anchor': 'center'}, 'b')
            self.assertEqual((a-b).volume(), 0.)
            self.assertEqual((b-a).volume(), 0.)

    def test_invalid_anchor_is_rejected_by_ast_and_direct_macro(self):
        for op, macro in [('book_branch', c._book_branch_macro), ('related_array', c._related_array_macro)]:
            for value in ('ground', None, [], 1):
                node = GeometryNode(id='bad', kind='macro', operator=op,
                    inputs=('base',), parameters={'vertical_anchor': value})
                self.assertIn('invalid_vertical_anchor', [x.code for x in _parameter_issues(node)])
                with self.assertRaises(c.GeometryCompileError):
                    macro(m3d.Manifold.cube((30, 8, 9)), node.parameters, 'bad')

    def test_connector_requires_common_height_and_real_contact(self):
        left = m3d.Manifold.cube((8, 8, 2))
        right = left.translate((12, 0, 4))
        with self.assertRaises(c.GeometryCompileError):
            c._input_base_array_connector(left, right, {'height': 1., 'width': 1.}, 'bad')
        slab = m3d.Manifold.cube((8, 8, 1))
        alternating_left = slab + slab.translate((0, 0, 6))
        alternating_right = slab.translate((12, 0, 2)) + slab.translate((12, 0, 8))
        with self.assertRaises(c.GeometryCompileError) as error:
            c._input_base_array_connector(alternating_left, alternating_right,
                {'height': 8., 'width': 2.}, 'alternating')
        self.assertEqual(error.exception.issue.code, 'array_connector_no_common_material')
        # A concave input's bbox centre is void. Surface embedding is required.
        u = m3d.Manifold.cube((10, 10, 6)) - m3d.Manifold.cube((6, 8, 8)).translate((2, 2, 0))
        other = u.translate((15, 0, 0))
        link = c._input_base_array_connector(u, other, {'height': 4., 'width': 2.}, 'u')
        self.assertGreater((link ^ u).volume(), 0.)
        self.assertGreater((link ^ other).volume(), 0.)
        self.assertGreaterEqual(link.bounding_box()[2], 0.)

    def test_concave_ground_control_keeps_existing_hull_rule(self):
        u = m3d.Manifold.cube((30, 30, 9)) - m3d.Manifold.cube((20, 25, 12)).translate((5, 5, 0))
        self.assertTrue(self.stands(u))

    def test_new_physical_floor_schedule_uses_new_compiled_geometry(self):
        from design.maas.geometry_language.programs import GeometryProgramBuilder
        from design.maas.creative_floor_portfolio import _with_occupied_floor_plates
        for operator in ('book_branch', 'related_array'):
            with self.subTest(operator=operator):
                builder = GeometryProgramBuilder('new_grounded_assembly')
                base = builder.add('primitive', 'box', parameters={'width': 30., 'depth': 8., 'height': 9.})
                root = builder.add('macro', operator, inputs=(base,), parameters={'vertical_anchor': 'input_base'})
                program = builder.build(root)
                compiled = c.compile_geometry_program(program)
                self.assertIsNotNone(compiled._solid, compiled.issues)
                bounds = compiled._solid.bounding_box()
                physical, _, plate_ids = _with_occupied_floor_plates(program,
                    bounds=(bounds[:3], bounds[3:]), storey_count=3, storey_height_m=3.)
                result = c.compile_geometry_program(physical)
                self.assertIsNotNone(result._solid, result.issues)
                self.assertEqual(len(plate_ids), 3)
                self.assertTrue(self.stands(result._solid))
