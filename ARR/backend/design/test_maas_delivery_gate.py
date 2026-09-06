"""Development cannot offer a child the generator would retire."""
from types import SimpleNamespace
from django.test import SimpleTestCase
from shapely.geometry import box
from design.maas.source_geometry.ir import SourceMass, SourceVolume


def source(height=10.8, bottom=0., **metadata):
    plan = box(0, 0, 12, 12)
    return SourceMass('gate-fixture', plan,
        volumes=(SourceVolume('body', plan, bottom, 1., 'test'),),
        metadata={'authored_height_m':height, 'authored_floor_height_m':3.6,
                  'declared_storeys':3., 'stature_is_building':True, **metadata})


class DeliveryGateTests(SimpleTestCase):
    def test_existing_generator_stature_boundaries_remain_exact(self):
        from design.maas.massv2.delivery_gate import stature_evidence, stature_ceiling_m
        self.assertEqual(stature_ceiling_m(3, 3.6), 18.)
        for height, refused in ((7.199, True), (7.2, False), (18.01, False), (18.011, True)):
            with self.subTest(height=height):
                result = stature_evidence(source(height), storey_m=3.6)
                self.assertEqual(result['crushed'], refused)
        # A count on a stacked unit is not a ceiling on the composition.
        self.assertFalse(stature_evidence(source(24, stature_is_building=False), storey_m=3.6)['over'])

    def test_physical_standing_and_declared_composition_both_gate_children(self):
        from design.maas.massv2.delivery_gate import assess_delivery
        site = SimpleNamespace(parcel_area_m2=2500, ground_capacity_m2=1499,
                               far_capacity_m2=6240, floor_height_m=3.6)
        good = assess_delivery(source(), site)
        self.assertTrue(good.accepted, good.reasons)
        floating = assess_delivery(source(bottom=.4), site)
        self.assertFalse(floating.accepted)
        self.assertFalse(floating.plausibility.occupiable)
        self.assertTrue(floating.plausibility.standing.reasons)
        changed = assess_delivery(source(authored_composition='different'), site)
        self.assertFalse(changed.accepted)
        self.assertIn('authored_composition_changed', changed.reasons)

    def test_assessment_is_exactly_the_existing_plausibility_and_composition_owners(self):
        from design.maas.massv2.delivery_gate import assess_delivery
        from design.maas.massv2 import plausibility, composition
        site = SimpleNamespace(parcel_area_m2=2500, ground_capacity_m2=1499,
                               far_capacity_m2=6240, floor_height_m=3.8)
        actual = source()
        result = assess_delivery(actual, site)
        old = plausibility.assess(actual, parcel_area_m2=2500,
            max_slenderness=plausibility.slenderness_limit(far_capacity_m2=6240,
                ground_capacity_m2=1499), floor_height_m=3.6)
        self.assertEqual(result.plausibility.evidence(), old.evidence())
        self.assertEqual(result.composition.to_dict(), composition.read(actual).to_dict())

    def test_final_source_area_and_parcel_storey_owners_are_rechecked(self):
        from design.maas.massv2.delivery_gate import assess_delivery
        site = SimpleNamespace(pnu='unregistered-fixture', parcel_area_m2=2500,
            ground_capacity_m2=1499, far_capacity_m2=400, floor_height_m=3.6)
        area = assess_delivery(source(), site)
        self.assertFalse(area.accepted)
        self.assertIn('floor_area_exceeds_capacity', area.reasons)
        site.far_capacity_m2 = 6240
        six = source(21.6, declared_storeys=6)
        self.assertIsNone(assess_delivery(six, site).legal_storeys['max_storeys'])
        site.pnu = '4115011300106840001'
        public = assess_delivery(six, site)
        self.assertFalse(public.accepted)
        self.assertIn('declared_storeys_exceed_limit', public.reasons)
