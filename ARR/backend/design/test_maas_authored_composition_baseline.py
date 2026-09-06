"""Authored intent is read before parcel clipping; delivery is still judged."""
import ast
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box, shape

from design.maas.massv2 import MatrixForm, place, compile_matrix_form
from design.maas.massv2 import composition
from design.maas.massv2.delivery_gate import stamp_authored_composition, assess_delivery
from design.maas.massv2.grammar import parti_from_record, declared_height_m
from design.maas.massv2.execute import execute as execute_parti
from design.maas.massv2.legal import LegalSite
from design.maas.massv2.measure import measure_form

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
import finalists
from vlm_shortlist import shape_id


def fixture():
    data = json.loads((Path(__file__).parent / 'fixtures/maas_comp03_authored_composition.json').read_text(encoding='utf8'))
    context = SimpleNamespace(envelope=SimpleNamespace(floor_height=data['floor_height_m']),
        generation_site=shape(data['generation_site_local']), sunlight_ring=data['sunlight_ring_local'])
    site = LegalSite(data['pnu'], shape(data['site_local_utm']), tuple(data['site_origin_utm']),
                     context, data['floor_field'], tuple(data['shared_edges_local_m']))
    return data, site


class AuthoredCompositionBaselineTests(SimpleTestCase):
    def test_actual_c_and_two_gardens_recover_without_changing_delivered_geometry(self):
        data, site = fixture()
        axis, buildable = tuple(data['axis']), site.plan_at(0)
        for row in data['rows']:
            record, expected = row['record'], row['expected']
            with self.subTest(name=record['name']):
                form = execute_parti(parti_from_record(record), buildable=buildable, axis=axis,
                    height_m=max(15.2, declared_height_m(record, 3.6)), storey_height_m=3.6)
                raw = compile_matrix_form(form, storey_height_m=3.6, allowed_at=None)
                clipped = compile_matrix_form(form, storey_height_m=3.6, allowed_at=site.plan_at)
                self.assertEqual(composition.band_id(composition.read(raw)), 'single_body')
                self.assertEqual(composition.band_id(composition.read(clipped)), 'paired_bodies')
                with patch.object(finalists, 'site_open_side_direction', return_value=axis):
                    delivered = finalists.rebuild(record['name'], {record['name']: record}, site, buildable, axis, 15.2)
                self.assertIsNotNone(delivered)
                self.assertEqual(shape_id(delivered), expected['shape_id'])
                self.assertEqual(measure_form(delivered).evidence(), expected['measurement'])
                placements = delivered.metadata['matrix_form']['placements']
                self.assertTrue(all(len(p['matrix4']) == 4 and all(len(r) == 4 for r in p['matrix4']) for p in placements))
                def legacy_clipped_stamp(candidate, *, storey_m):
                    old_source = compile_matrix_form(candidate, storey_height_m=storey_m, allowed_at=site.plan_at)
                    return replace(candidate, extra={**candidate.extra,
                        'authored_composition': composition.band_id(composition.read(old_source))})
                with patch.object(finalists, 'site_open_side_direction', return_value=axis), \
                     patch.object(finalists, 'stamp_authored_composition', side_effect=legacy_clipped_stamp):
                    before = finalists.rebuild(record['name'], {record['name']: record}, site, buildable, axis, 15.2)
                self.assertEqual(placements, before.metadata['matrix_form']['placements'])
                self.assertEqual(before.metadata['authored_composition'], 'paired_bodies')
                self.assertEqual(delivered.metadata['authored_composition'], 'single_body')
                judgment = assess_delivery(delivered, site, storey_m=3.6)
                self.assertTrue(judgment.composition_kept, judgment.evidence())
                self.assertTrue(judgment.legal_area['satisfied'], judgment.legal_area)
                self.assertTrue(judgment.legal_storeys['satisfied'], judgment.legal_storeys)
                self.assertTrue(judgment.gap['satisfied'], judgment.gap)
                self.assertTrue(judgment.plausibility.occupiable, judgment.reasons)
                self.assertTrue(judgment.accepted, judgment.reasons)

    def test_true_paired_authorship_still_refuses_delivered_fusion(self):
        authored = MatrixForm('true-pair', (
            place('one', size=(10, 10, 10.8)),
            place('two', size=(10, 10, 10.8), at=(16, 0, 0))), 'paired')
        stamped = stamp_authored_composition(authored, storey_m=3.6)
        self.assertEqual(stamped.extra['authored_composition'], 'paired_bodies')
        # Keep the pre-fit stamp while a later operation fuses the bodies.
        fused = replace(stamped, placements=(place('fused', size=(26, 10, 10.8)),))
        delivered = compile_matrix_form(fused, storey_height_m=3.6, allowed_at=lambda z: box(-1, -1, 30, 11))
        site = SimpleNamespace(pnu='composition-fixture', parcel_area_m2=2500,
            ground_capacity_m2=1500, far_capacity_m2=6250, floor_height_m=3.6)
        result = assess_delivery(delivered, site)
        self.assertTrue(result.plausibility.occupiable, result.reasons)
        self.assertEqual(result.reasons, ('authored_composition_changed',))
        self.assertFalse(result.accepted)

    def test_unclipped_intent_does_not_bypass_final_legal_clip(self):
        authored = MatrixForm('large-body', (place('one', size=(20, 10, 10.8)),), 'single')
        stamped = stamp_authored_composition(authored, storey_m=3.6)
        delivered = compile_matrix_form(stamped, storey_height_m=3.6, allowed_at=lambda z: box(0, 0, 10, 10))
        self.assertAlmostEqual(measure_form(delivered).footprint_area_m2, 100)
        self.assertEqual(delivered.metadata['authored_composition'], 'single_body')
        site = SimpleNamespace(pnu='composition-fixture', parcel_area_m2=2500,
            ground_capacity_m2=1500, far_capacity_m2=200, floor_height_m=3.6)
        result = assess_delivery(delivered, site)
        self.assertIn('floor_area_exceeds_capacity', result.reasons)

    def test_generator_and_finalist_use_the_common_stamp_before_resizing(self):
        backend = Path(__file__).resolve().parents[1]
        for path in (backend / 'design/management/commands/generate_massv2.py',
                     backend / 'tmp_mass_check/_massv2/tools/finalists.py'):
            tree = ast.parse(path.read_text(encoding='utf8'))
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
            stamp = [n for n in calls if isinstance(n.func, ast.Name) and n.func.id == 'stamp_authored_composition']
            self.assertEqual(len(stamp), 1)
            self.assertNotIn('allowed_at', {k.arg for k in stamp[0].keywords})
            resized = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == 'resized_to']
            self.assertTrue(resized and all(stamp[0].lineno < n.lineno for n in resized))
