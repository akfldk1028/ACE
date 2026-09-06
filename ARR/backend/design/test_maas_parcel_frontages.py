"""Registered public-office frontages constrain geometry without claiming a survey."""
from dataclasses import dataclass
from types import SimpleNamespace

from django.test import SimpleTestCase
from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box

from design.maas.massv2 import parcel_policy
from design.maas.massv2.legal import LegalSite
from design.maas.book_language.downstream_hard_gate import LegalGenerationContext

PNU = '4115011300106840001'
# Independent captured parcel, not a policy-return-value fixture.
RING = [(0.,32.85654268087819),(11.59371943201404,39.50109809124842),
        (29.64010443945881,50.43758501717821),(46.434598230640404,61.34179168846458),
        (76.16706880752463,44.32430054806173),(78.23247281974182,36.59896623622626),
        (57.298764832085,0.),(33.13071452913573,13.857184919528663)]


def site():
    return SimpleNamespace(pnu=PNU, site_local_utm=Polygon(RING),
                           ground_capacity_m2=1497.877, far_capacity_m2=6241.962)


def inside_edge(index, distance):
    a,b=RING[index],RING[(index+1)%len(RING)]
    dx,dy=b[0]-a[0],b[1]-a[1];length=(dx*dx+dy*dy)**.5
    return Point((a[0]+b[0])/2+dy/length*distance,
                 (a[1]+b[1])/2-dx/length*distance)


class PublicOneFrontageTests(SimpleTestCase):
    def test_three_registered_frontages_enforce_two_metres_only_there(self):
        allowed=parcel_policy.registered_buildable(site())
        for edge in (3,4,5):
            self.assertFalse(allowed.covers(inside_edge(edge,1.9)))
            self.assertTrue(allowed.covers(inside_edge(edge,2.1)))
        # No invented uniform buffer on the opposite two sides.
        for edge in (1,7):
            self.assertTrue(allowed.covers(inside_edge(edge,.1)))

    def test_unknown_or_changed_coordinate_frame_cannot_reuse_registration(self):
        controlled=site();controlled.site_local_utm=translate(controlled.site_local_utm,xoff=1)
        with self.assertRaisesRegex(ValueError,'registration.*frame'):
            parcel_policy.registered_buildable(controlled)
        self.assertIsNone(parcel_policy.registered_buildable(SimpleNamespace(pnu='another')))

    def test_final_area_gate_rejects_a_small_source_inside_bcr_but_across_building_line(self):
        source=SimpleNamespace(volumes=[SimpleNamespace(footprint=inside_edge(3,1).buffer(.1))])
        evidence=parcel_policy.area_limit_evidence(source,site(),1)
        self.assertFalse(evidence['satisfied'])
        self.assertIn('registered_building_line_exceeded',evidence['reasons'])
        self.assertGreater(evidence['building_line']['outside_area_m2'],0)

    def test_projection_inside_line_passes_with_registered_not_surveyed_grade(self):
        source=SimpleNamespace(volumes=[SimpleNamespace(footprint=box(35,25,40,30))])
        evidence=parcel_policy.area_limit_evidence(source,site(),25)
        self.assertTrue(evidence['satisfied'])
        self.assertEqual(evidence['building_line']['evidence_grade'],'official_plan_registered')
        self.assertFalse(evidence['building_line']['survey_verified'])

    def test_book_export_triangle_outside_line_is_not_hidden_by_inside_proxy(self):
        proxy=box(35,25,40,30);origin=proxy.centroid
        point=inside_edge(3,1)
        vertices=[(point.x-origin.x,point.y-origin.y,.5),
                  (point.x-origin.x+.1,point.y-origin.y,.5),
                  (point.x-origin.x,point.y-origin.y+.1,.5)]
        source=SimpleNamespace(footprint=proxy,volumes=[SimpleNamespace(footprint=proxy)],
            surfaces=[SimpleNamespace(vertices_m=vertices)],
            metadata={'authored_height_m':10, 'geometry_program_bridge_evidence':{
                'surface_coordinate_frame':'source_footprint_centroid_local',
                'surface_export_complete':True,
                'raw_mesh_triangle_count':1,'exported_surface_count':1}})
        evidence=parcel_policy.area_limit_evidence(source,site(),1)
        self.assertFalse(evidence['satisfied'])
        self.assertIn('registered_building_line_exceeded',evidence['reasons'])
        self.assertEqual(evidence['projection_basis'],'complete_export_surface_xy_projection')

    def test_missing_book_export_mesh_does_not_fall_back_to_proxy(self):
        proxy=box(35,25,40,30)
        source=SimpleNamespace(footprint=proxy,volumes=[SimpleNamespace(footprint=proxy)],surfaces=[],
            metadata={'geometry_program_bridge_evidence':{
                'surface_coordinate_frame':'source_footprint_centroid_local',
                'raw_mesh_triangle_count':4,'exported_surface_count':4}})
        evidence=parcel_policy.area_limit_evidence(source,site(),1)
        self.assertFalse(evidence['satisfied'])
        self.assertIn('source_projection_unavailable',evidence['reasons'])

    def test_vehicle_missing_plan_is_unverified_and_crossing_prohibited_interval_fails(self):
        missing=parcel_policy.vehicle_access_evidence(site())
        self.assertIsNone(missing['satisfied'])
        self.assertFalse(missing['access_and_egress_verified'])
        for point in (LineString([RING[3],RING[4]]).interpolate(.5,normalized=True),
                      LineString([RING[4],RING[5]]).interpolate(.5,normalized=True),
                      LineString([RING[5],RING[6]]).interpolate(9)):
            evidence=parcel_policy.vehicle_access_evidence(site(),boundary_crossings=[point])
            self.assertFalse(evidence['satisfied'])
        outside=parcel_policy.vehicle_access_evidence(site(),boundary_crossings=[Point(0,0)])
        self.assertFalse(outside['satisfied'])

    def test_unmarked_segment_only_passes_prohibition_check_not_complete_access(self):
        point=LineString([RING[5],RING[6]]).interpolate(15)
        evidence=parcel_policy.vehicle_access_evidence(site(),boundary_crossings=[point])
        self.assertTrue(evidence['satisfied'])
        self.assertFalse(evidence['access_and_egress_verified'])

    def test_context_and_all_height_sections_keep_existing_tighter_geometry(self):
        from design.maas.massv2.legal import apply_registered_parcel_plan
        @dataclass(frozen=True)
        class Envelope:
            buildable_footprint: object
            floor_height: float=3.6
        parcel=Polygon(RING);existing=parcel.intersection(box(10,-10,90,90))
        context=LegalGenerationContext(Envelope(existing),existing,(),{})
        changed=apply_registered_parcel_plan(PNU,parcel,context)
        self.assertLess(changed.generation_site.area,existing.area)
        self.assertLess(changed.generation_site.difference(existing).area,1e-9)
        self.assertTrue(changed.envelope.buildable_footprint.equals(changed.generation_site))
        legal=LegalSite(PNU,parcel,(0,0),changed,{'bcr_footprint_capacity_m2':1497.877,'statutory_far_capacity_m2':6241.962})
        self.assertTrue(legal.plan_at(0).equals(legal.plan_at(18)))
        evidence=legal.evidence()
        self.assertTrue(evidence['building_line_geometry_registered'])
        self.assertFalse(evidence['exact_building_line_geometry_verified'])
        self.assertEqual(evidence['frontage_constraints']['evidence_grade'],'official_plan_registered')

    def test_policy_preserves_official_hash_and_reproducible_registration_source(self):
        reg=parcel_policy.policy_for(PNU)['frontage_registration']
        self.assertEqual(reg['source_pdf_sha256'],'0225c991a7c2c8ca7dc497c8576eaa1d29668f57b5d78ebd43727e22349bb3cd')
        self.assertEqual(reg['source_pdf_page_1_based'],6)
        self.assertEqual(len(reg['diagnostic_sha256']),64)
        self.assertFalse(reg['survey_verified'])
