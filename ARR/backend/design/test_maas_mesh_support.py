"""Independent physical-mesh support measurements, deliberately not a gate."""
import json
from dataclasses import replace
from pathlib import Path
from unittest import TestCase

import manifold3d as m3d
import numpy as np
from shapely.geometry import box, shape

from design.maas.source_geometry.ir import SourceMass, SourceSurface, SourceVolume
from design.maas.massv2.mesh_support import measure_mesh_support


def source_for_solid(solid, *, datum=0.):
    mesh = solid.to_mesh64()
    vertices = np.asarray(mesh.vert_properties)[:, :3]
    height = max(float(vertices[:, 2].max()), 1.)
    footprint = box(100, 200, 120, 220)
    origin = footprint.centroid
    surfaces = tuple(SourceSurface('mesh', 'mesh', 'test', 'triangle',
        tuple((float(vertices[i, 0])-origin.x, float(vertices[i, 1])-origin.y,
               float(vertices[i, 2])/height) for i in face)) for face in mesh.tri_verts)
    return SourceMass('test', footprint, surfaces=surfaces, metadata={
        'authored_height_m': height, 'datum_m': datum,
        'geometry_program_bridge_evidence': {
            'surface_coordinate_frame': 'source_footprint_centroid_local',
            'surface_export_complete': True, 'raw_mesh_triangle_count': len(surfaces),
            'exported_surface_count': len(surfaces)}})


def book018_fixture():
    data = json.loads((Path(__file__).parent/'test_fixtures/book018-support.json').read_text(encoding='utf8'))
    surfaces = tuple(SourceSurface(**{k: v for k, v in s.items() if k != 'vertex_count'})
                     for s in data['surfaces'])
    volumes = tuple(SourceVolume(**{**v, 'footprint': shape(v['footprint'])}) for v in data['volumes'])
    return SourceMass(data['provenance']['name'], shape(data['footprint']),
                      surfaces=surfaces, volumes=volumes, metadata=data['metadata'])


class MeshSupportTests(TestCase):
    def test_book018_band_pass_has_actual_negative_ground_and_transfer_margin(self):
        source = book018_fixture()
        evidence = measure_mesh_support(source)
        self.assertEqual(evidence['component_count'], 1)
        self.assertAlmostEqual(evidence['volume_m3'], 4315.215627060073, places=6)
        self.assertAlmostEqual(evidence['ground_contact_area_m2'], 125.29589781852, places=5)
        self.assertAlmostEqual(evidence['minimum_ground_margin_m'], -8.994287199226, places=5)
        self.assertLess(evidence['minimum_critical_margin_m'], -9.7)
        self.assertEqual(evidence['uniform_density_com_xyz_m'], evidence['components'][0]['uniform_density_com_xyz_m'])

    def test_grounded_pillar_has_closed_topology_analytic_volume_com_and_margin(self):
        e = measure_mesh_support(source_for_solid(m3d.Manifold.cube((4, 6, 8))))
        self.assertTrue(e['closed_oriented_mesh'])
        self.assertEqual(e['volume_m3'], 192.)
        self.assertEqual(e['uniform_density_com_xyz_m'], [2., 3., 4.])
        self.assertAlmostEqual(e['minimum_ground_margin_m'], 2.)
        self.assertEqual(e['grounded_volume_share'], 1.)
        json.dumps(e, allow_nan=False)

    def test_two_pier_bridge_uses_hull_of_its_own_disjoint_contacts(self):
        pier = m3d.Manifold.cube((2, 4, 4))
        slab = m3d.Manifold.cube((10, 4, 2)).translate((0, 0, 4))
        e = measure_mesh_support(source_for_solid(pier + pier.translate((8, 0, 0)) + slab))
        self.assertEqual(e['component_count'], 1)
        self.assertEqual(e['components'][0]['ground_contact']['patch_count'], 2)
        self.assertAlmostEqual(e['ground_contact_area_m2'], 16.)
        self.assertGreater(e['minimum_ground_margin_m'], 0)
        self.assertGreater(e['minimum_critical_margin_m'], 0)

    def test_floating_body_cannot_borrow_another_component_ground_hull(self):
        grounded = m3d.Manifold.cube((4, 4, 1))
        floating = m3d.Manifold.cube((2, 2, 2)).translate((1, 1, 2))
        e = measure_mesh_support(source_for_solid(grounded + floating))
        self.assertEqual(e['component_count'], 2)
        self.assertAlmostEqual(e['grounded_volume_share'], 16/24)
        self.assertEqual(sum(c['has_ground_contact'] for c in e['components']), 1)
        self.assertIn('component_without_ground_contact', e['observations'])

    def test_internal_transfer_can_fail_while_whole_body_ground_com_is_inside(self):
        base = m3d.Manifold.cube((10, 10, 1))
        neck = m3d.Manifold.cube((2, 2, 1)).translate((0, 0, 1))
        head = m3d.Manifold.cube((10, 10, 1)).translate((0, 0, 2))
        e = measure_mesh_support(source_for_solid(base + neck + head))
        self.assertGreater(e['minimum_ground_margin_m'], 0)
        self.assertLess(e['minimum_critical_margin_m'], -3)

    def test_through_hole_is_subtracted_from_volume_and_contact(self):
        outer = m3d.Manifold.cube((10, 10, 10))
        hole = m3d.Manifold.cube((4, 4, 12)).translate((3, 3, -1))
        e = measure_mesh_support(source_for_solid(outer-hole))
        self.assertAlmostEqual(e['volume_m3'], 840.)
        self.assertAlmostEqual(e['ground_contact_area_m2'], 84.)
        self.assertEqual(e['components'][0]['ground_contact']['hole_count'], 1)
        self.assertEqual(e['uniform_density_com_xyz_m'], [5., 5., 5.])

    def test_enclosed_cavity_shell_is_void_not_a_floating_material_body(self):
        outer = m3d.Manifold.cube((10, 10, 10))
        void = m3d.Manifold.cube((2, 2, 2)).translate((4, 4, 4))
        e = measure_mesh_support(source_for_solid(outer-void))
        self.assertEqual(e['component_count'], 1)
        self.assertAlmostEqual(e['volume_m3'], 992.)
        self.assertEqual(e['uniform_density_com_xyz_m'], [5., 5., 5.])
        self.assertFalse(e['observations'])

    def test_actual_small_air_gap_is_not_welded_by_band_contact_tolerance(self):
        lower = m3d.Manifold.cube((4, 4, 2))
        upper = m3d.Manifold.cube((4, 4, 2)).translate((0, 0, 2.001))
        e = measure_mesh_support(source_for_solid(lower+upper))
        self.assertEqual(e['component_count'], 2)
        self.assertAlmostEqual(e['grounded_volume_share'], .5)
        self.assertIn('upper_component_without_bearing_at_sample', e['observations'])

    def test_nonzero_datum_does_not_translate_mesh_vertices_again(self):
        source = source_for_solid(m3d.Manifold.cube((4, 6, 8)).translate((0, 0, 12)), datum=12)
        e = measure_mesh_support(source)
        self.assertEqual(e['uniform_density_com_xyz_m'], [2., 3., 16.])
        self.assertEqual(e['components'][0]['com_height_above_ground_m'], 4.)
        self.assertEqual(e['ground_contact_area_m2'], 24.)
        self.assertEqual(measure_mesh_support(source, datum_m=0)['ground_contact_area_m2'], 0.)

    def test_triangle_order_and_cyclic_vertex_start_do_not_change_evidence(self):
        source = book018_fixture()
        reordered = replace(source, surfaces=tuple(replace(s, vertices_m=tuple(s.vertices_m[1:])+tuple(s.vertices_m[:1]))
                                                   for s in reversed(source.surfaces)))
        self.assertEqual(measure_mesh_support(source), measure_mesh_support(reordered))

    def test_missing_export_and_open_mesh_refuse_without_proxy_fallback(self):
        source = source_for_solid(m3d.Manifold.cube((4, 6, 8)))
        with self.assertRaisesRegex(ValueError, 'complete'):
            measure_mesh_support(replace(source, surfaces=source.surfaces[:-1]))
        bridge = {**source.metadata['geometry_program_bridge_evidence'],
                  'raw_mesh_triangle_count': len(source.surfaces)-1,
                  'exported_surface_count': len(source.surfaces)-1}
        with self.assertRaisesRegex(ValueError, 'closed|oriented'):
            measure_mesh_support(replace(source, surfaces=source.surfaces[:-1],
                metadata={**source.metadata, 'geometry_program_bridge_evidence': bridge}))

    def test_no_critical_checks_is_explicit_and_no_standing_claim_is_created(self):
        e = measure_mesh_support(source_for_solid(m3d.Manifold.cube((4, 6, 8))), critical_heights=False)
        self.assertFalse(e['critical_heights_evaluated'])
        self.assertEqual(e['critical_sections'], [])
        self.assertIsNone(e['minimum_critical_margin_m'])
        self.assertNotIn('stands', e)
        json.dumps(e, allow_nan=False)
