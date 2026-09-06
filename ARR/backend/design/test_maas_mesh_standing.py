"""The common structure owner must judge the delivered mesh, not its bands."""
import json
from dataclasses import replace
from unittest import TestCase
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
import sys

import manifold3d as m3d
from shapely.geometry import box

from design.maas.massv2 import structure
from design.maas.source_geometry.ir import SourceMass, SourceVolume
from design.test_maas_mesh_support import book018_fixture, source_for_solid


class MeshStandingTests(TestCase):
    def test_book018_fails_actual_gravity_screen_and_does_not_claim_zero_mesh_spans(self):
        source = book018_fixture()
        result = structure.assess_standing(source, height_m=source.metadata['authored_height_m'])
        self.assertFalse(result.stands)
        self.assertAlmostEqual(result.overturning_margin_m, -8.994287199226, places=5)
        evidence = result.evidence()
        self.assertEqual(evidence['measurement_basis'], 'complete_export_mesh')
        self.assertIsNone(evidence['cantilever_ratio'])
        self.assertIsNone(evidence['span_to_depth'])
        self.assertEqual(evidence['member_capacity_status'], 'unverified')
        self.assertIn('moment_transfer_review_required', evidence['requirements'])
        self.assertEqual(evidence['mesh_support']['triangle_count'], 102)
        self.assertIn('gravity', evidence['basis'])
        json.dumps(evidence, allow_nan=False)

    def test_normal_pillar_passes_without_proxy_volumes(self):
        source = source_for_solid(m3d.Manifold.cube((4, 6, 8)))
        result = structure.assess_standing(source, height_m=999)
        self.assertTrue(result.stands)
        self.assertAlmostEqual(result.potential_well_m, -2.)
        self.assertEqual(structure.connectivity(source), (1., 1))
        self.assertEqual(structure.centre_of_mass(source, height_m=999), (2., 3., 4.))
        self.assertAlmostEqual(structure.support_polygon(source).area, 24.)

    def test_no_area_ground_contact_fails_even_when_band_proxy_has_a_floor(self):
        source = source_for_solid(m3d.Manifold.cube((4, 4, 4)).translate((0, 0, .002861843)))
        source = replace(source, volumes=(SourceVolume('fake-ground', box(0, 0, 4, 4), 0, 1, 'proxy'),))
        result = structure.assess_standing(source, height_m=source.metadata['authored_height_m'])
        self.assertFalse(result.stands)
        self.assertIn('mesh_component_0_without_positive_area_ground_contact', result.reasons)
        self.assertIsNone(result.overturning_margin_m)
        self.assertIsNone(structure.support_polygon(source))

    def test_nonzero_datum_uses_com_above_ground_not_absolute_z_for_existing_rule(self):
        source = source_for_solid(m3d.Manifold.cube((4, 6, 8)).translate((0, 0, 12)), datum=12)
        result = structure.assess_standing(source, height_m=20)
        self.assertTrue(result.stands)
        self.assertEqual(result.centre_of_mass_height_m, 4.)
        self.assertEqual(result.potential_well_m, -2.)

    def test_floating_component_refuses_while_two_grounded_bodies_may_pass(self):
        cube = m3d.Manifold.cube((4, 4, 4))
        grounded = structure.assess_standing(source_for_solid(cube+cube.translate((8, 0, 0))), height_m=4)
        floating = structure.assess_standing(source_for_solid(cube+cube.translate((8, 0, 1))), height_m=5)
        self.assertTrue(grounded.stands)
        self.assertEqual(grounded.body_count, 2)
        self.assertFalse(floating.stands)
        self.assertAlmostEqual(floating.grounded_share, .5)

    def test_midheight_negative_margin_is_review_requirement_not_automatic_refusal(self):
        base = m3d.Manifold.cube((10, 10, 1))
        neck = m3d.Manifold.cube((2, 2, 1)).translate((0, 0, 1))
        head = m3d.Manifold.cube((10, 10, 1)).translate((0, 0, 2))
        result = structure.assess_standing(source_for_solid(base+neck+head), height_m=3)
        self.assertTrue(result.stands)
        self.assertIn('moment_transfer_review_required', result.evidence()['requirements'])
        self.assertLess(result.evidence()['mesh_support']['minimum_critical_margin_m'], 0)

    def test_existing_potential_well_policy_is_applied_to_actual_com(self):
        height = 4*(abs(structure.POTENTIAL_WELL_FLOOR_M)+3)
        source = source_for_solid(m3d.Manifold.cube((4, 4, height)))
        result = structure.assess_standing(source, height_m=height)
        self.assertFalse(result.stands)
        self.assertLess(result.potential_well_m, structure.POTENTIAL_WELL_FLOOR_M)
        self.assertTrue(any('potential_well' in r for r in result.reasons))

    def test_component_limit_is_read_from_existing_structure_policy(self):
        cube = m3d.Manifold.cube((4, 4, 4))
        source = source_for_solid(cube+cube.translate((8, 0, 0)))
        with patch.object(structure, 'MAX_SEPARATE_BODIES', 1):
            result = structure.assess_standing(source, height_m=4)
        self.assertFalse(result.stands)
        self.assertIn('2_separate_bodies_not_one_building', result.reasons)

    def test_incomplete_mesh_has_explicit_unknown_measurements_and_refuses(self):
        source = source_for_solid(m3d.Manifold.cube((4, 6, 8)))
        source = replace(source, surfaces=source.surfaces[:-1])
        result = structure.assess_standing(source, height_m=8)
        self.assertFalse(result.stands)
        evidence = result.evidence()
        self.assertEqual(evidence['measurement_status'], 'unknown')
        self.assertIsNone(evidence['overturning_margin_m'])
        self.assertIn('complete', evidence['measurement_error'])
        json.dumps(evidence, allow_nan=False)
        bridge = {**source.metadata['geometry_program_bridge_evidence'],
                  'raw_mesh_triangle_count': len(source.surfaces),
                  'exported_surface_count': len(source.surfaces)}
        open_mesh = replace(source, metadata={**source.metadata, 'geometry_program_bridge_evidence': bridge})
        self.assertIn('closed', structure.assess_standing(open_mesh, height_m=8).measurement_error)

    def test_book_import_and_plausibility_use_the_same_mesh_ground_refusal(self):
        sys.path.insert(0, str(Path(__file__).parent.parent/'tmp_mass_check/_massv2/tools'))
        import book_import
        source = book018_fixture()
        with patch('design.maas.massv2.parcel_policy.storey_limit_evidence', return_value={'satisfied': True}), \
             patch('design.maas.massv2.parcel_policy.area_limit_evidence', return_value={'satisfied': True}), \
             patch('design.maas.massv2.plausibility.assess') as later:
            refusal = book_import._refused(source, SimpleNamespace())
        self.assertIn('mesh gravity screen', refusal)
        later.assert_not_called()
        from design.maas.massv2.plausibility import assess
        selection = assess(source, parcel_area_m2=2500, max_slenderness=10)
        self.assertFalse(selection.occupiable)
        self.assertEqual(selection.standing.evidence(),
            structure.assess_standing(source, height_m=source.metadata['authored_height_m']).evidence())

    def test_ordinary_typed_path_keeps_existing_measurements(self):
        footprint = box(0, 0, 4, 6)
        source = SourceMass('ordinary', footprint,
            volumes=(SourceVolume('room', footprint, 0, 1, 'test'),),
            metadata={'authored_height_m': 8})
        result = structure.assess_standing(source, height_m=8)
        self.assertTrue(result.stands)
        self.assertEqual((result.cantilever_ratio, result.span_to_depth), (0., 0.))
        self.assertEqual(result.potential_well_m, -2.)
        self.assertEqual(result.evidence()['measurement_basis'], 'typed_source_solids')

    def _certificate(self, source):
        sys.path.insert(0, str(Path(__file__).parent.parent/'tmp_mass_check/_massv2/tools'))
        from vlm_shortlist import seat_certificate
        site = SimpleNamespace(parcel_area_m2=1000, floor_height_m=4, pnu='test')
        with patch('design.maas.massv2.parcel_policy.storey_limit_evidence', return_value={'satisfied': True}), \
             patch('design.maas.massv2.parcel_policy.area_limit_evidence', return_value={'satisfied': True, 'ground_m2': 24}), \
             patch('design.maas.massv2.measure.gross_floor_area_m2', return_value=48):
            return seat_certificate('mesh-pillar', source, {}, site)

    def test_certificate_binds_mesh_and_structure_policy_and_refuses_bad_gravity(self):
        source = source_for_solid(m3d.Manifold.cube((4, 6, 8)))
        first = self._certificate(source)
        self.assertEqual(first['structure']['policy_version'], structure.STRUCTURE_POLICY_VERSION)
        self.assertEqual(first['structure']['mesh_support']['mesh_sha256'],
                         structure.assess_standing(source, height_m=8).evidence()['mesh_support']['mesh_sha256'])
        with patch.object(structure, 'STRUCTURE_POLICY_VERSION', 'test-policy-change'):
            second = self._certificate(source)
        self.assertEqual(first['shape_id'], second['shape_id'])
        self.assertNotEqual(first['certificate_id'], second['certificate_id'])
        with self.assertRaisesRegex(ValueError, 'gravity screen'):
            self._certificate(book018_fixture())
