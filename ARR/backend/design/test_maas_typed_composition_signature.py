"""Different plan/section geometry must not collapse to one bounding box."""
import unittest
from dataclasses import replace

from shapely.geometry import Polygon, box

from design.maas.massv2.form import MatrixForm, place
from design.maas.massv2.select import composition_signature, choose, Candidate
from design.maas.massv2.compile import compile_matrix_form
from design.maas.massv2.measure import measure_form
from design.maas.massv2.plausibility import Plausibility
from design.maas.source_geometry.solid import ConstantSurface, PolynomialSurface


def form(name, region, *, top=None, bottom=None, size=(30., 30., 12.)):
    body = replace(place('body', size=size), plan_region=region,
                   top_surface=top, bottom_surface=bottom)
    return MatrixForm(name=name, placements=(body,), primary_language='carved_body', floor_height_m=3.)


class TypedCompositionSignatureTests(unittest.TestCase):
    def test_ring_and_folded_plan_survive_same_cell_dedup(self):
        ring = box(0, 0, 1, 1).difference(box(.25, .25, .75, .75))
        comb = Polygon([(0, 0), (1, 0), (1, 1), (.7, 1), (.7, .4),
                        (.3, .4), (.3, 1), (0, 1)])
        forms = [form('ring', ring), form('comb', comb)]
        self.assertNotEqual(*(composition_signature(f) for f in forms))
        candidates = []
        for f in forms:
            source = compile_matrix_form(f, storey_height_m=3.)
            self.assertIsNotNone(source)
            candidates.append(Candidate(f, source, measure_form(source),
                Plausibility(1., 12., 1., True, ()), 'standing|single', .5, .5))
        self.assertEqual({c.form.name for c in choose(candidates, per_cell=2)}, {'ring', 'comb'})

    def test_same_bounds_different_top_or_underside_are_distinct(self):
        flat = form('flat', box(0, 0, 1, 1))
        slope = replace(flat, placements=(replace(flat.placements[0],
            top_surface=PolynomialSurface(((0, 0, .5), (1, 0, .5)))),))
        underside = replace(flat, placements=(replace(flat.placements[0],
            bottom_surface=PolynomialSurface(((1, 0, .2),))),))
        self.assertEqual(len({composition_signature(f) for f in (flat, slope, underside)}), 3)

    def test_geometry_identity_ignores_ring_start_winding_name_and_physical_scale(self):
        region = box(0, 0, 1, 1).difference(box(.25, .25, .75, .75))
        a = form('first', region, top=PolynomialSurface(((0, 0, .5), (1, 0, .5))))
        ext = list(region.exterior.coords)[:-1]
        hole = list(region.interiors[0].coords)[:-1]
        reordered = Polygon(list(reversed(ext[1:] + ext[:1])), [list(reversed(hole[2:] + hole[:2]))])
        b = form('renamed', reordered, size=(60., 60., 24.),
                 top=PolynomialSurface(((1, 0, .5), (0, 0, .5))))
        p = b.placements[0]
        matrix = tuple(tuple(v + (100. if r == 0 else 200. if r == 1 else 30.)
                             if c == 3 and r < 3 else v for c, v in enumerate(row))
                       for r, row in enumerate(p.matrix))
        b = replace(b, placements=(replace(p, matrix=matrix),))
        self.assertEqual(composition_signature(a), composition_signature(b))

    def test_explicit_constant_surfaces_equal_default_flat_solid(self):
        a = form('implicit', box(0, 0, 1, 1))
        b = form('explicit', box(0, 0, 1, 1), top=ConstantSurface(1.), bottom=ConstantSurface(0.))
        self.assertEqual(composition_signature(a), composition_signature(b))
