"""Presentation duplicates are occupied solids, independent of author labels."""
from dataclasses import replace
from pathlib import Path
import sys

from django.test import SimpleTestCase
import manifold3d as m3d
from shapely.affinity import translate, scale
from shapely.geometry import box

from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume
from design.maas.source_geometry.solid import AffineSurface, ConstantSurface, PolynomialSurface

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
from solid_presentation import SolidPresentationRegistry


def body(height=10):
    footprint = box(0, 0, 20, 10)
    volume = SourceVolume('body', footprint, 0, 1, 'extrude')
    return SourceMass('source', footprint, volumes=(volume,), metadata={'authored_height_m': height})


def book_body(missing_face=False):
    source = body()
    mesh = m3d.Manifold.cube((20, 10, 10)).to_mesh64()
    faces = list(mesh.tri_verts)[:-1] if missing_face else mesh.tri_verts
    surfaces = tuple(SourceSurface('body', 'body', 'compose', 'mesh', tuple(
        (float(mesh.vert_properties[i][0]) - 10, float(mesh.vert_properties[i][1]) - 5,
         float(mesh.vert_properties[i][2]) / 10) for i in face)) for face in faces)
    return replace(source, surfaces=surfaces, metadata={**source.metadata,
        'geometry_program_bridge_evidence': {
            'surface_coordinate_frame': 'source_footprint_centroid_local',
            'surface_export_complete': True, 'raw_mesh_triangle_count': len(surfaces),
            'exported_surface_count': len(surfaces),
            'authoritative_visual_geometry': 'manifold_compilation_mesh'}})


class SolidPresentationTests(SimpleTestCase):
    def match(self, a, b):
        registry = SolidPresentationRegistry()
        first = registry.find_or_add('first', a)
        self.assertEqual(first['status'], 'verified', first)
        return registry.find_or_add('second', b)

    def test_role_and_part_decomposition_are_duplicates(self):
        source = body()
        v = source.volumes[0]
        for volumes in ((replace(v, role='different', verb='assemble'),),
                        (replace(v, top_fraction=.4), replace(v, bottom_fraction=.4))):
            with self.subTest(volumes=volumes):
                result = self.match(source, replace(source, volumes=volumes))
                self.assertEqual(result['duplicate_of'], 'first', result)
                self.assertTrue(result['proof']['a_minus_b_empty'])
                self.assertTrue(result['proof']['b_minus_a_empty'])

    def test_translation_and_uniform_xyz_scale_preserve_form(self):
        source = body()
        footprint = translate(scale(source.footprint, xfact=3, yfact=3, origin=(0, 0)), 73, -42)
        moved = replace(source, footprint=footprint,
            volumes=(replace(source.volumes[0], footprint=footprint),), metadata={'authored_height_m': 30})
        result = self.match(source, moved)
        self.assertEqual(result['duplicate_of'], 'first', result)
        self.assertEqual(result['proof']['normalization']['policy'], 'translation_uniform_xyz')
        sunken = replace(source, metadata={**source.metadata, 'datum_m': 2})
        scaled_sunken = replace(moved, metadata={**moved.metadata, 'datum_m': 6})
        self.assertEqual(self.match(sunken, scaled_sunken)['duplicate_of'], 'first')

    def test_same_plan_different_roof_stays_distinct(self):
        source = body()
        sloped = replace(source, volumes=(replace(source.volumes[0], top_drop=.4, drop_toward=(1, 0)),))
        self.assertIsNone(self.match(source, sloped)['duplicate_of'])

    def test_same_roof_different_underside_stays_distinct(self):
        source = body()
        # A central raised underside leaves ground at the sides and full roof.
        v = source.volumes[0]
        raised = replace(source, volumes=(replace(v, bottom_fraction=.4),
            replace(v, footprint=box(0, 0, 2, 10)), replace(v, footprint=box(18, 0, 20, 10))))
        self.assertIsNone(self.match(source, raised)['duplicate_of'])

    def test_same_roof_and_lowest_bottom_finite_height_void_stays_distinct(self):
        source = body()
        v = source.volumes[0]
        undercut = replace(source, volumes=(replace(v, top_fraction=.3),
            replace(v, bottom_fraction=.5), replace(v, footprint=box(0, 0, 2, 10))))
        self.assertIsNone(self.match(source, undercut)['duplicate_of'])

    def test_changed_height_proportion_stays_distinct(self):
        self.assertIsNone(self.match(body(10), body(12))['duplicate_of'])

    def test_changed_ground_datum_is_not_normalized_away(self):
        source = body()
        for datum in (2, 1e-10):
            with self.subTest(datum=datum):
                sunken = replace(source, metadata={**source.metadata, 'datum_m': datum})
                self.assertIsNone(self.match(source, sunken)['duplicate_of'])

    def test_raised_body_keeps_its_ground_clearance(self):
        source = body()
        raised = replace(source, volumes=(replace(source.volumes[0], bottom_fraction=.2),))
        self.assertIsNone(self.match(body(8), raised)['duplicate_of'])

    def test_no_rotation_or_independent_axis_normalization(self):
        source = body()
        rotated_plan = box(0, 0, 10, 20)
        rotated = replace(source, footprint=rotated_plan,
                          volumes=(replace(source.volumes[0], footprint=rotated_plan),))
        self.assertIsNone(self.match(source, rotated)['duplicate_of'])

    def test_authoritative_book_mesh_matches_typed_volume(self):
        result = self.match(body(), book_body())
        self.assertEqual(result['duplicate_of'], 'first', result)

    def test_authoritative_book_ignores_conservative_volume_proxy(self):
        source = book_body()
        # The BOOK triangle mesh is authoritative, even if its proxy differs.
        other = replace(source, volumes=(replace(source.volumes[0], top_fraction=.1),))
        self.assertEqual(self.match(source, other)['duplicate_of'], 'first')

    def test_open_mesh_is_unsupported_and_never_an_alias(self):
        result = self.match(body(), book_body(missing_face=True))
        self.assertEqual(result['status'], 'unsupported', result)
        self.assertIsNone(result['duplicate_of'])
        self.assertTrue(result['proof']['reason'])

    def test_record_and_certificate_fields_are_not_mutated(self):
        source = body()
        original = repr(source)
        self.match(source, replace(source, name='new_name'))
        self.assertEqual(repr(source), original)

    def test_curved_hole_body_is_watertight_and_role_independent(self):
        source = body()
        footprint = source.footprint.difference(box(8, 3, 12, 7))
        dome = AffineSurface(PolynomialSurface(((0, 0, .6), (1, 0, .8), (2, 0, -.8),
            (0, 1, .8), (0, 2, -.8))), (1/20, 0, 0, 1/10, 0, 0))
        volume = replace(source.volumes[0], footprint=footprint, top_surface=dome,
                         bottom_surface=ConstantSurface(0), authored_domain=source.footprint)
        curved = replace(source, footprint=footprint, volumes=(volume,))
        renamed = replace(curved, volumes=(replace(volume, role='other_curve'),))
        result = self.match(curved, renamed)
        self.assertEqual(result['duplicate_of'], 'first', result)
        self.assertTrue(result['proof']['closed_kernel_solid'])

    def test_mirrored_roof_is_not_normalized_away(self):
        source = body()
        a = replace(source, volumes=(replace(source.volumes[0], top_drop=.4, drop_toward=(1, 0)),))
        b = replace(source, volumes=(replace(source.volumes[0], top_drop=.4, drop_toward=(-1, 0)),))
        self.assertIsNone(self.match(a, b)['duplicate_of'])
