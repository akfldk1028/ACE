"""A gap declared in the sentence must survive its actual delivered variant."""
import sys
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
from unittest.mock import patch
from django.test import SimpleTestCase
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from design.maas.source_geometry.ir import SourceMass, SourceVolume
from design.maas.massv2 import MatrixForm, place, compile_matrix_form
from design.maas.massv2.legal_fit import _scaled_composition
from design.test_maas_parcel_frontages import RING, PNU

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))

BUILDABLE = Polygon([(31.194935128030696,47.87194639689766),(31.273782840332473,47.92141831313834),
    (46.53302300174088,57.82882668374121),(73.59177227027043,42.34164997042827),
    (75.01539573853002,37.0167996450559),(56.18570193385851,4.096338148124966),
    (34.6230312406169,16.45968195987992),(6.031885501329932,32.85574870422635),
    (13.085447583724187,36.89826365137419),(13.148550120585927,36.93545947096788)])
AXIS = (-.9792161796320089,-.20281931255897057)
RECORD = {'name':'sangok_c02_hall_and_daily_street','floor_height_m':3.6,
    'primary_language':'open_figure','growth':'plan','ops':[
        {'op':'extrude','height':.6,'storeys':3},
        {'op':'split','ratio':.62,'along':'cross','first':'civic','second':'community','gap':9.4,'contrast':1.4},
        {'op':'vault','on':'community','rise':.25,'bays':1,'along':'long'}]}


def site():
    return SimpleNamespace(pnu=PNU,site_local_utm=Polygon(RING),floor_height_m=3.8,
        parcel_area_m2=Polygon(RING).area,ground_capacity_m2=1497.877,far_capacity_m2=6241.962,
        max_storeys=5,shared_edges=tuple((RING[i],RING[(i+1)%8]) for i in (3,0,4,7,6)),
        plan_at=lambda z:BUILDABLE)


def separated(gap, claim=9.4):
    one,two=box(0,0,10,10),box(10+gap,0,20+gap,10)
    return SourceMass('gap',one,volumes=(SourceVolume('one',one,0,1,'split'),
        SourceVolume('two',two,0,1,'split')),metadata={'authored_height_m':10.8,
        'authored_floor_height_m':3.6,'parti':{'operations':[{'verb':'split','params':{'gap':claim}}]}})


class DeliveredGapTests(SimpleTestCase):
    def test_actual_comp02_variant_retains_space_after_coverage_and_final_delivery(self):
        from finalists import rebuild
        from design.maas.massv2.ablation import gap_evidence
        # This is the captured comp02 axis, independent of later parcel-axis fixes.
        with patch('finalists.site_open_side_direction',return_value=AXIS,create=True):
            source=rebuild(RECORD['name']+'~full_ground^to_open',{RECORD['name']:RECORD},
                           site(),BUILDABLE,AXIS,15.2)
        self.assertIsNotNone(source)
        gap=gap_evidence(source)
        self.assertTrue(gap['satisfied'],gap)
        self.assertAlmostEqual(gap['delivered_m'],4.7811587161,places=5)
        matrices=source.metadata['matrix_form']['placements']
        self.assertEqual(len(matrices),2)
        self.assertTrue(all(len(item['matrix4'])==4 for item in matrices))
        self.assertAlmostEqual(matrices[1]['matrix4'][2][2],5.16282536138,places=6)

    def test_existing_gap_threshold_and_small_reveal_semantics(self):
        from design.maas.massv2.ablation import gap_evidence
        for width, claim, passed in ((1.9423889229,9.4,False),(2.3500001,9.4,True),
                                      (.2,.28,True),(0.,9.4,False),(0.,0.,True)):
            with self.subTest(width=width,claim=claim):
                self.assertEqual(gap_evidence(separated(width,claim))['satisfied'],passed)

    def test_shared_gate_rejects_narrow_actual_gap_even_when_physical_and_legal_pass(self):
        from design.maas.massv2.delivery_gate import assess_delivery
        controlled=SimpleNamespace(pnu='gap-fixture',floor_height_m=3.6,parcel_area_m2=2500,
                                    ground_capacity_m2=1499,far_capacity_m2=6240)
        result=assess_delivery(separated(1.9423889229),controlled)
        self.assertTrue(result.plausibility.occupiable)
        self.assertFalse(result.accepted)
        self.assertIn('declared_gap_closed',result.reasons)

    def test_original_sentence_gap_probe_and_finalist_refusal_share_actual_source_measurement(self):
        from design.maas.massv2 import ablation
        from design.maas.massv2.grammar import parti_from_record
        from finalists import rebuild
        source=separated(1.9423889229)
        with patch.object(ablation,'_delivered',return_value=source):
            declared,measured=ablation.gap_survived(parti_from_record(RECORD),
                buildable=BUILDABLE,axis=AXIS,height_m=18,site=site(),storey_height_m=3.6)
        self.assertEqual(declared,7.144)
        self.assertAlmostEqual(measured,1.9423889229)
        diagnostics={}
        with patch('finalists.compile_matrix_form',return_value=source), \
             patch('finalists.site_open_side_direction',return_value=AXIS,create=True):
            result=rebuild(RECORD['name']+'~full_ground^to_open',{RECORD['name']:RECORD},
                           site(),BUILDABLE,AXIS,15.2,diagnostics=diagnostics)
        self.assertIsNone(result)
        self.assertFalse(diagnostics['gap']['satisfied'])

    def test_declared_gap_fallback_preserves_real_carrier_height_and_landing(self):
        carrier=replace(place('carrier',size=(10,10,6)),top_profile=((0,0),(.5,1),(1,0)),
                        profile_across=(1,0),top_drop=.3)
        upper=place('upper',size=(4,4,3),at=(0,0,6))
        other=replace(place('other',size=(10,10,6),at=(16,0,0)),
                      top_profile=((0,0),(.5,1),(1,0)),profile_across=(1,0),top_drop=.3)
        form=MatrixForm('supported-gap',(carrier,upper,other),primary_language='open_figure',
            floor_height_m=3.6,extra={'parti':{'operations':[{'verb':'split','params':{'gap':9.4}}]}})
        changed=_scaled_composition(form,.65,(0,0))
        self.assertEqual(changed.placements[0].z_span()[1],6)
        self.assertAlmostEqual(changed.placements[1].z_span()[0],6)
        self.assertLess(changed.placements[2].z_span()[1],6)
        for item in changed.placements:
            self.assertEqual(len(item.matrix),4)
            self.assertTrue(all(len(row)==4 for row in item.matrix))
