"""Courtyard wall visibility must respect the projected roof opening."""
import hashlib
import json

from django.test import SimpleTestCase
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from design.maas.massv2 import render
from design.maas.massv2.measure import gross_floor_area_m2
from design.maas.source_geometry.ir import SourceMass, SourceVolume
from design.maas.source_geometry.solid import PolynomialSurface


def ring():
    return Polygon(box(0, 0, 30, 24).exterior.coords,
                   [box(10, 8, 20, 16).exterior.coords])


class CourtyardVisibilityTests(SimpleTestCase):
    def check_aperture_walls(self, height, volume=None):
        poly = ring()
        slope = render._slope_of(volume, 0, height) if volume else None
        faces = list(render._faces(poly, 0, height, slope))
        court_index = next(i for i, (_, color, _) in enumerate(faces) if color == render._PAL.court)
        aperture = Polygon(faces[court_index][0])
        visible = faces[court_index + 1:]
        walls = [Polygon(points) for points, color, _ in visible
                 if color == render._PAL.wall and len(points) >= 3]
        self.assertTrue(walls, 'Real inner wall depth must remain visible after the court background')
        self.assertGreater(unary_union(walls).area, .1)
        for points, color, _ in visible:
            geometry = LineString(points) if len(points) == 2 else Polygon(points)
            self.assertLess(geometry.difference(aperture.buffer(1e-8)).length, 1e-6,
                            'An inner wall or edge must never leak onto the outside facade')
        if volume is None:
            outer = [(float(x), float(y)) for x, y in poly.exterior.coords[:-1]]
            expected = list(render._walls(outer, 0, height))
            first_roof = next(i for i, (_, color, _) in enumerate(faces) if color == render._PAL.roof)
            self.assertEqual(faces[:first_roof], expected,
                             'No inner wall may be painted over the exterior before the roof')

    def test_shallow_and_tall_flat_courts_show_depth_without_facade_ghosts(self):
        for height in (4., 10., 18.):
            with self.subTest(height=height):
                self.check_aperture_walls(height)

    def test_typed_curved_court_preserves_visible_walls_inside_its_aperture(self):
        volume = SourceVolume('curve', ring(), 0, 1, 'test',
                    top_surface=PolynomialSurface(((0, 0, .8), (1, 0, .2/30),
                                                   (0, 1, .2/24), (1, 1, -.4/720))))
        source = SourceMass('curve', ring(), volumes=(volume,), metadata={'authored_height_m':12})
        before = (volume.signature(), source.solid_volume_m3(), source.plan_at(6).wkb,
                  gross_floor_area_m2(source, floor_height_m=3))
        self.check_aperture_walls(12, volume)
        self.assertEqual(before, (volume.signature(), source.solid_volume_m3(), source.plan_at(6).wkb,
                                 gross_floor_area_m2(source, floor_height_m=3)))

    def test_curved_aperture_uses_surface_heights_between_corners(self):
        volume = SourceVolume('vault', ring(), 0, 1, 'test',
                    top_surface=PolynomialSurface(((0, 0, .7), (1, 0, .04), (2, 0, -.04/30))))
        self.check_aperture_walls(12, volume)
        slope = render._slope_of(volume, 0, 12)
        points = next(points for points, color, _ in render._faces(ring(), 0, 12, slope)
                      if color == render._PAL.court)
        self.assertGreater(len(points), 4)
        corner_only = Polygon([render._project(x, y, volume.top_z(x, y, 0, 12))
                               for x, y in ring().interiors[0].coords[:-1]])
        self.assertGreater(Polygon(points).symmetric_difference(corner_only).area, .01)

    def test_solid_without_hole_keeps_its_exterior_faces(self):
        polygon = box(0, 0, 30, 24)
        outer = [(float(x), float(y)) for x, y in polygon.exterior.coords[:-1]]
        expected = list(render._walls(outer, 0, 10))
        expected.append(([render._project(x, y, 10) for x, y in outer], render._PAL.roof, True))
        self.assertEqual(list(render._faces(polygon, 0, 10)), expected)

    def test_sunken_pit_keeps_existing_face_contract(self):
        actual = list(render._faces(ring(), 0, 4, pit_walls=True))
        # Recorded from the existing sunken-earth path before the courtyard fix.
        digest = hashlib.sha256(json.dumps(actual).encode()).hexdigest()
        self.assertEqual(digest, 'e4ef1b48cc0e8ebd29c88a7a3c709749f1629fa81d0d85198384cb4472b57793')
