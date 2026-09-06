"""Parking diagrams reserve actual public voids and never certify access."""
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box, Polygon, mapping, shape
from design.maas.source_geometry.ir import SourceMass, SourceVolume
from design.test_maas_parcel_frontages import PNU, RING
from design.maas import parking_layout

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
from vlm_shortlist import shape_id


def building():
    plan = Polygon([(10, 10), (30, 10), (30, 30), (10, 30)],
                   holes=[[(15, 15), (25, 15), (25, 25), (15, 25)]])
    return SourceMass('courtyard', plan, volumes=(SourceVolume('body', plan, 0, 1, 'test'),),
                      metadata={'authored_height_m': 10.8})


def site():
    return SimpleNamespace(pnu='4115099999999999999', site_local_utm=box(0, 0, 60, 50),
        site_origin_utm=(0, 0), parcel_area_m2=3000, floor_height_m=3.6)


def certificate(source):
    return {'name':source.name, 'shape_id':shape_id(source), 'certificate_id':'fixture-cert',
            'gross_m2':1000, 'floor_area_basis':'fixture conservative mass-area proxy'}


class SitePlanningTests(SimpleTestCase):
    def test_internal_module_checks_its_full_aisle_before_ranking(self):
        envelope = box(0,0,30,18).difference(box(10,6,20,10))
        with patch.object(parking_layout, '_parking_operability_checks',
                          wraps=parking_layout._parking_operability_checks) as checked:
            result = parking_layout._place_internal_90_degree_stalls(envelope,
                required_spaces=10, accessible_spaces=1, strategy='ground_surface')
        self.assertFalse(result['drive_envelope_check']['satisfied'])
        self.assertEqual(result['reason'], 'internal_aisle_outside_envelope')
        self.assertEqual(result['status'], 'fail')
        aisle = Polygon(result['drive_cells'][0])
        self.assertGreater(aisle.difference(envelope).area, 0)
        self.assertAlmostEqual(min(aisle.bounds[2]-aisle.bounds[0], aisle.bounds[3]-aisle.bounds[1]),
                               parking_layout.DEFAULT_AISLE_WIDTH_M)
        self.assertEqual(checked.call_args.kwargs['drive_cells'][0], aisle)
        legal_small = {'required_spaces':10, 'provided_spaces':2,'unmet_spaces':8,'status':'fail'}
        self.assertGreater(parking_layout._layout_rank(legal_small), parking_layout._layout_rank(result))

    def test_existing_internal_module_exposes_its_actual_aisle(self):
        result = parking_layout._place_internal_90_degree_stalls(box(0, 0, 30, 18),
            required_spaces=10, accessible_spaces=1, strategy='ground_surface')
        self.assertTrue(result['drive_cells'])
        aisle = Polygon(result['drive_cells'][0])
        self.assertTrue(box(0, 0, 30, 18).covers(aisle))
        for stall in result['stalls']:
            self.assertAlmostEqual(aisle.intersection(Polygon(stall['polygon'])).area, 0)

    def test_registered_road_context_excludes_prohibited_frontage(self):
        from design.maas.massv2.parcel_policy import registered_vehicle_approach
        result = registered_vehicle_approach(SimpleNamespace(pnu=PNU, site_local_utm=Polygon(RING)))
        allowed, prohibited = shape(result['geometry']), shape(result['prohibited_geometry'])
        self.assertGreater(allowed.length, 0)
        self.assertAlmostEqual(allowed.intersection(prohibited).length, 0)
        self.assertFalse(result['vehicle_access_verified'])
        with self.assertRaises(ValueError):
            registered_vehicle_approach(SimpleNamespace(pnu=PNU, site_local_utm=box(0, 0, 10, 10)))

    def test_court_is_reserved_and_actual_stalls_are_outside_it(self):
        from design.maas.massv2.site_planning import assess_site_parking
        source = building()
        result = assess_site_parking(source, site(), certificate(source), source_shape_id=shape_id(source))
        self.assertEqual(result['requirement']['required_spaces'], 10)
        self.assertEqual(result['requirement']['accessible']['accessible_min'], 1)
        self.assertAlmostEqual(shape(result['geometry']['public_reserve']).area, 100)
        self.assertEqual(result['public_reserve_basis'], 'temporary_convex_hull_void_reservation')
        self.assertFalse(result['legal_approval'])
        self.assertEqual(result['vehicle_access_status'], 'unverified')
        self.assertEqual(result['pedestrian_access_status'], 'unverified')
        self.assertEqual(result['geometry_checks']['stall_public_overlap_m2'], 0)

    def test_all_free_components_are_evaluated_but_counts_are_not_summed(self):
        from design.maas.massv2.site_planning import assess_site_parking
        source = building()
        reserve = {'geometry': mapping(box(0, 20, 60, 25)), 'source_shape_id':shape_id(source),
                   'coordinate_frame':'parcel_local_m', 'confirmed':True}
        called = []
        def solve(envelope, **kw):
            called.append(envelope.area)
            return {'provided_spaces': 0, 'provided_accessible_spaces': 0, 'stalls':[], 'drive_cells':[], 'status':'fail'}
        with patch('design.maas.massv2.site_planning.generate_parking_layout_candidate', side_effect=solve):
            result = assess_site_parking(source, site(), certificate(source), source_shape_id=shape_id(source), public_reserve=reserve)
        self.assertGreaterEqual(len(called), 2)
        self.assertEqual(result['component_count'], len(called))
        self.assertEqual(len(result['component_evaluations']), len(called))
        self.assertEqual(result['public_reserve_basis'], 'confirmed_authored_public_reserve')
        self.assertEqual(result['status'], 'current_layout_capacity_shortfall')
        self.assertFalse(result['site_maximum_proven'])

    def test_supplied_count_does_not_hide_overlap_or_establish_access(self):
        from design.maas.massv2.site_planning import assess_site_parking, parking_status_text
        source = building()
        fake = {'provided_spaces':10, 'provided_accessible_spaces':1, 'status':'pass',
                'stalls':[{'polygon':list(box(16,16,19,21).exterior.coords), 'type':'accessible'}],
                'drive_cells':[list(box(18,18,24,24).exterior.coords)]}
        with patch('design.maas.massv2.site_planning.generate_parking_layout_candidate', return_value=fake):
            result = assess_site_parking(source, site(), certificate(source), source_shape_id=shape_id(source))
        self.assertGreater(result['geometry_checks']['stall_public_overlap_m2'], 0)
        self.assertGreater(result['geometry_checks']['drive_public_overlap_m2'], 0)
        self.assertFalse(result['geometry_checks']['satisfied'])
        self.assertFalse(result['legal_approval'])
        self.assertIn('공간 충돌', parking_status_text(result))
        self.assertIn('차로 침범', parking_status_text(result))

    def test_stale_source_and_public_reserve_binding_are_refused(self):
        from design.maas.massv2.site_planning import assess_site_parking
        source = building()
        with self.assertRaisesRegex(ValueError, 'identity'):
            assess_site_parking(source, site(), certificate(source), source_shape_id='different')
        with self.assertRaisesRegex(ValueError, 'parcel identity'):
            assess_site_parking(source, site(), {**certificate(source), 'site_pnu':'other'},
                source_shape_id=shape_id(source))
        reserve = {'confirmed':True, 'geometry':mapping(box(0,0,5,5)),
                   'source_shape_id':'old', 'coordinate_frame':'parcel_local_m'}
        with self.assertRaisesRegex(ValueError, 'reserve'):
            assess_site_parking(source, site(), certificate(source), source_shape_id=shape_id(source), public_reserve=reserve)

    def test_book_projection_uses_complete_mesh_and_refuses_missing_surface(self):
        from dataclasses import replace
        from design.test_maas_book_presentation_mesh import wedge
        from design.maas.massv2.site_planning import assess_site_parking
        source = wedge()
        source = replace(source, volumes=(SourceVolume('wrong-proxy', box(95,195,115,215),0,1,'book'),))
        parcel = site()
        parcel.site_local_utm = box(90,190,125,225)
        # This test isolates authoritative mesh projection; layout searches
        # have their own geometry tests and need not solve this displaced lot.
        with patch('design.maas.massv2.site_planning.generate_parking_layout_candidate',
                   return_value={'provided_spaces':0,'stalls':[],'drive_cells':[]}):
            result = assess_site_parking(source, parcel, certificate(source), source_shape_id=shape_id(source))
        self.assertAlmostEqual(result['projection_area_m2'],100,places=5)
        self.assertEqual(result['projection_basis'],'complete_export_surface_xy_projection')
        broken = replace(source,surfaces=())
        with self.assertRaises(ValueError):
            assess_site_parking(broken,parcel,certificate(broken),source_shape_id=shape_id(broken))

    def test_plan_png_and_json_bind_actual_layout_and_law_evidence(self):
        import json, hashlib
        from tempfile import TemporaryDirectory
        from design.maas.massv2.site_planning import assess_site_parking, write_site_parking_plan
        source = building()
        result = assess_site_parking(source,site(),certificate(source),source_shape_id=shape_id(source))
        with TemporaryDirectory() as tmp:
            image = write_site_parking_plan(result,tmp,stem='fixture')
            saved = json.loads(image.with_suffix('.json').read_text(encoding='utf8'))
            self.assertEqual(saved['png_sha256'],hashlib.sha256(image.read_bytes()).hexdigest())
            self.assertEqual(saved['source_shape_id'],shape_id(source))
            self.assertEqual(saved['facility_area_assumption_m2'],1000)
            self.assertEqual(saved['floor_area_basis'],certificate(source)['floor_area_basis'])
            self.assertNotIn('actual_gfa_m2',saved)
            self.assertEqual(len(saved['law_source_sha256']),64)
            self.assertEqual(saved['layout']['stalls'],result['layout']['stalls'])
