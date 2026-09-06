"""Authoring direction follows documented frontage, not an inset plan's asymmetry."""
from types import SimpleNamespace

from django.test import SimpleTestCase
from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, box

from design.maas.massv2 import siting, parcel_policy
from design.test_maas_parcel_frontages import RING, PNU


class SiteFrontageAxisTests(SimpleTestCase):
    def direction(self, site):
        owner = getattr(siting, 'site_open_side_direction', None)
        self.assertTrue(callable(owner), 'site-aware frontage owner is required')
        return owner(site)

    def public_site(self):
        return SimpleNamespace(pnu=PNU, site_local_utm=Polygon(RING),
            shared_edges=tuple((RING[i], RING[(i + 1) % len(RING)])
                               for i in (3, 0, 4, 7, 6)))

    def test_public_one_points_east_even_when_neighbor_list_contains_road(self):
        axis = self.direction(self.public_site())
        self.assertGreater(axis[0], .98)
        self.assertGreater(axis[1], .1)
        self.assertLess(axis[1], .2)

    def test_inset_legal_plan_cannot_decide_the_frontage(self):
        site = self.public_site()
        axis = self.direction(site)
        site.plan_at = lambda height: box(-100, 50, -80, 55)
        self.assertEqual(self.direction(site), axis)

    def test_geometry_identity_is_required_for_registered_frontage(self):
        site = self.public_site()
        site.site_local_utm = translate(site.site_local_utm, xoff=1)
        with self.assertRaisesRegex(ValueError, 'registration.*frame'):
            self.direction(site)

    def test_ring_winding_does_not_reverse_the_registered_axis(self):
        site = self.public_site()
        expected = self.direction(site)
        site.site_local_utm = Polygon(list(reversed(RING)))
        self.assertEqual(self.direction(site), expected)

    def test_unknown_parcel_compares_original_boundary_with_shared_edges(self):
        site = SimpleNamespace(pnu='unregistered', site_local_utm=box(0, 0, 20, 10),
            shared_edges=(((0, 0), (20, 0)), ((0, 10), (0, 0)), ((20, 10), (0, 10))),
            plan_at=lambda height: box(4, 2, 10, 8))
        self.assertEqual(self.direction(site), (1., 0.))

    def test_no_frontage_evidence_does_not_turn_an_asymmetric_outline_into_a_road(self):
        site = SimpleNamespace(pnu='unregistered',
            site_local_utm=Polygon([(0, 0), (20, 0), (12, 10), (0, 7)]), shared_edges=())
        self.assertIsNone(self.direction(site))

    def test_frontage_axis_keeps_pedestrian_orientation_separate_from_vehicle_prohibition(self):
        site = self.public_site()
        self.direction(site)
        point = LineString([RING[3], RING[4]]).interpolate(.5, normalized=True)
        self.assertFalse(parcel_policy.vehicle_access_evidence(
            site, boundary_crossings=[point])['satisfied'])
        owner = getattr(siting, 'site_open_side_evidence', None)
        self.assertTrue(callable(owner))
        evidence = owner(site)
        self.assertEqual(evidence['basis'], 'official_plan_road_frontages')
        self.assertEqual(evidence['source_pdf_sha256'],
            '0225c991a7c2c8ca7dc497c8576eaa1d29668f57b5d78ebd43727e22349bb3cd')
        self.assertIsNone(evidence['vehicle_access_permission'])
        self.assertEqual(evidence['vehicle_access_status'],
                         'not_assessed_by_pedestrian_orientation')
