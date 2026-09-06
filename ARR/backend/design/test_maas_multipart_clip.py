"""A legal clip can disconnect an authored C without deleting either arm."""
from dataclasses import replace

from django.test import SimpleTestCase
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from design.maas.massv2 import MatrixForm, compile_matrix_form, place
from design.maas.massv2.compile import _own_figure
from design.maas.source_geometry.solid import ConstantSurface, PolynomialSurface


# Exact normalized region and roof terms authored in gen-comp03's first C.
C_REGION = Polygon([(1, 0), (1, .25), (.28, .25), (.28, .75),
                    (1, .75), (1, 1), (0, 1), (0, 0), (1, 0)])


class MultiPartClipTests(SimpleTestCase):
    def c_form(self, typed=True):
        item = replace(place('C', size=(20, 20, 10)), plan_region=C_REGION)
        if typed:
            item = replace(item, top_surface=PolynomialSurface(((0, 0, 1), (1, 0, -.33))),
                           bottom_surface=ConstantSurface(0))
        return MatrixForm(name='comp03_C', placements=(item,), primary_language='open_figure')

    def test_own_figure_keeps_the_exact_disconnected_clip(self):
        allowed = box(.4, -1, 2, 2)
        clipped = C_REGION.intersection(allowed)
        self.assertEqual(clipped.geom_type, 'MultiPolygon')
        self.assertIs(_own_figure(C_REGION, clipped, allowed), clipped)

    def test_typed_c_keeps_both_arms_and_the_authored_surface_frame(self):
        form = self.c_form()
        full = compile_matrix_form(form)
        allowed = box(8, -1, 21, 21)
        source = compile_matrix_form(form, allowed_at=lambda z: allowed)
        expected = full.volumes[0].footprint.intersection(allowed)
        self.assertEqual(len(source.volumes), 2)
        self.assertTrue(unary_union([v.footprint for v in source.volumes]).equals(expected))
        for part in source.volumes:
            self.assertTrue(part.authored_domain.equals(full.volumes[0].authored_domain))
            for x, y in part.footprint.exterior.coords:
                self.assertEqual(part.top_z(x, y, 0, 10), full.volumes[0].top_z(x, y, 0, 10))
                self.assertEqual(part.bottom_z(x, y, 0, 10), full.volumes[0].bottom_z(x, y, 0, 10))

    def test_flat_c_also_keeps_both_arms(self):
        source = compile_matrix_form(self.c_form(typed=False), allowed_at=lambda z: box(8, -1, 21, 21))
        self.assertEqual(len(source.volumes), 2)
        self.assertAlmostEqual(sum(v.footprint.area for v in source.volumes), 120)

    def test_typed_mixed_polygon_and_line_clip_keeps_the_material_polygon(self):
        # Lower arm overlaps, upper arm only touches the legal boundary.
        allowed = Polygon([(8, -1), (21, -1), (21, 15), (8, 15), (8, -1)])
        full = compile_matrix_form(self.c_form())
        clipped = full.volumes[0].footprint.intersection(allowed)
        self.assertEqual(clipped.geom_type, 'GeometryCollection')
        source = compile_matrix_form(self.c_form(), allowed_at=lambda z: allowed)
        self.assertIsNotNone(source)
        self.assertEqual(len(source.volumes), 1)
        self.assertAlmostEqual(source.volumes[0].footprint.area, clipped.area)

    def test_boundary_contact_without_area_emits_no_volume(self):
        source = compile_matrix_form(self.c_form(), allowed_at=lambda z: box(20, -1, 21, 21))
        self.assertIsNone(source)
