"""An authored development is bound to a scored parent and keeps its variant."""
import copy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
import develop
from vlm_shortlist import shape_id
from design.maas.source_geometry.ir import SourceMass, SourceVolume
from design.maas.massv2.render import render_masses


def source(width):
    plan = box(0, 0, width, 10)
    return SourceMass('fixture', plan, volumes=(SourceVolume('body', plan, 0, 1, 'test'),),
                      metadata={'authored_height_m': 10})


class AuthoredDevelopmentTests(SimpleTestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        run = self.root / 'runs/fixture'
        run.mkdir(parents=True)
        (run / 'massv2-summary.json').write_text(json.dumps({'site': {'parcel_area_m2':2500}}))
        self.parent = {'name': 'parent', 'floor_height_m':3.6,
                       'ops':[{'op':'loop','height':.8,'storeys':3,'bar':.2}]}
        self.variant = 'parent~held_ground^centred'
        self.parent_source = source(10)
        self.expected = shape_id(self.parent_source)
        self.payload = {'parent':self.variant, 'parent_shape_id':self.expected,
                        'schemes':[dict(copy.deepcopy(self.parent), name=f'child{i}') for i in range(4)]}
        for i, child in enumerate(self.payload['schemes']):
            child['ops'][0]['bar'] = .12 + i * .03
        self.path = self.root / 'authored.json'
        self.out = self.root / 'authored-output'
        self.site = SimpleNamespace(floor_height_m=3.8, ground_capacity_m2=1497.877,
                                    far_capacity_m2=6241.962, shared_edges=(),
                                    plan_at=lambda z: box(0,0,50,50))

    def run_payload(self, payload=None, sources=None, expected=None, use_authored=True):
        self.path.write_text(json.dumps(payload or self.payload), encoding='utf8')
        with patch('develop.ROOT',self.root), patch('develop.corpus',return_value={'parent':self.parent}), \
                patch('develop.schedule_of',return_value=None), patch('develop.load_legal_site',return_value=self.site), \
                patch('develop.rebuild',side_effect=sources or [self.parent_source,*[source(i+11) for i in range(4)]]) as rebuild, \
                patch('develop.render_masses', wraps=render_masses) as render, \
                patch('develop.mutants_of',return_value=self.payload['schemes']) as automatic:
            result=develop.main('fixture',self.variant,4,output_dir=self.out,
                                expected_shape_id=expected or self.expected,
                                authored_payload=self.path if use_authored else None)
        return result,rebuild,render,automatic

    def test_exact_four_authored_children_bypass_automatic_mutations_and_keep_suffix(self):
        status,rebuild,render,automatic=self.run_payload()
        self.assertEqual(status,0)
        automatic.assert_not_called()
        self.assertEqual(render.call_count,4)
        self.assertEqual([c.args[0] for c in rebuild.call_args_list[1:]],
                         [f'child{i}~held_ground^centred' for i in range(4)])
        ledger=json.loads((self.out/'mutants.json').read_text())
        self.assertEqual(ledger['author_mode'],'payload')
        self.assertEqual(len(ledger['children']),4)
        self.assertEqual(ledger['children'][0]['scheme']['ops'][0]['bar'],.12)
        drawings = ledger['children'][0]['jury_drawings']['drawings']
        self.assertEqual([drawing['shape_id'] for drawing in drawings],
                         [self.expected, shape_id(source(11))])
        self.assertEqual([drawing['plan_areas_m2'] for drawing in drawings],
                         [[100.0, 100.0], [110.0, 110.0]])
        from PIL import Image
        with Image.open(self.out/'pairs'/ledger['children'][0]['pair']) as pair:
            self.assertGreater(pair.height, render.call_args_list[0].kwargs['tile'][1])

    def test_wrong_count_duplicate_names_unknown_verb_or_wrong_parent_are_rejected_before_output(self):
        bad=[]
        p=copy.deepcopy(self.payload);p['schemes'].pop();bad.append(p)
        p=copy.deepcopy(self.payload);p['schemes'][1]['name']='child0';bad.append(p)
        p=copy.deepcopy(self.payload);p['schemes'][0]['ops'].append({'op':'invented'});bad.append(p)
        p=copy.deepcopy(self.payload);p['parent']='different^centred';bad.append(p)
        p=copy.deepcopy(self.payload);p['parent_shape_id']='old';bad.append(p)
        p=copy.deepcopy(self.payload);p['schemes'][0]['name']='child^off_open';bad.append(p)
        for payload in bad:
            with self.subTest(payload=payload),self.assertRaises(ValueError):self.run_payload(payload)
            self.assertFalse(self.out.exists())

    def test_actual_parent_shape_mismatch_does_not_touch_existing_output(self):
        self.out.mkdir();sentinel=self.out/'untouched.txt';sentinel.write_text('keep')
        status,_,render,_=self.run_payload(sources=[source(99)])
        self.assertEqual(status,1)
        render.assert_not_called()
        self.assertEqual(sentinel.read_text(),'keep')
        self.assertFalse((self.out/'pairs').exists())

    def test_default_mode_still_uses_automatic_mutants(self):
        status,_,render,automatic=self.run_payload(use_authored=False)
        self.assertEqual(status,0)
        automatic.assert_called_once_with(self.parent,4)
        self.assertEqual(render.call_count,4)
        self.assertEqual(json.loads((self.out/'mutants.json').read_text())['author_mode'],'deterministic')

    def test_equal_and_unbuildable_authored_children_still_do_not_get_pairs(self):
        status,_,render,_=self.run_payload(sources=[self.parent_source,self.parent_source,None,source(12),source(12)])
        self.assertEqual(status,0)
        self.assertEqual(render.call_count,1)
        ledger=json.loads((self.out/'mutants.json').read_text())['children']
        self.assertTrue(ledger[0]['erased_by_delivery'])
        self.assertFalse(ledger[1]['delivered'])
        self.assertTrue(ledger[3]['erased_by_delivery'])

    def test_nested_geometry_error_is_not_swallowed_and_preserves_prior_output(self):
        (self.out/'pairs').mkdir(parents=True)
        sentinel=self.out/'pairs/p01.png';sentinel.write_bytes(b'previous stage')
        with self.assertRaisesRegex(ValueError,'bad shape'):
            self.run_payload(sources=[self.parent_source,ValueError('bad shape')])
        self.assertEqual(sentinel.read_bytes(),b'previous stage')

    def test_added_authored_operation_survives_champion_feedback(self):
        child=copy.deepcopy(self.payload['schemes'][0])
        child['ops'].append({'op':'notch','bite':.2,'why':'Authored courtyard threshold.'})
        result=develop._with_developed_why(self.parent,child)
        self.assertEqual(len(result['ops']),2)
        self.assertEqual(result['ops'][1]['op'],'notch')

    def test_physically_unfit_child_is_recorded_without_a_pair_image(self):
        floating = source(13)
        from dataclasses import replace
        floating = replace(floating, volumes=(replace(floating.volumes[0], bottom_fraction=.5),))
        _, _, render, _ = self.run_payload(sources=[self.parent_source, floating, source(12), source(14), source(15)])
        self.assertEqual(render.call_count, 3)
        row = json.loads((self.out/'mutants.json').read_text())['children'][0]
        self.assertNotIn('pair', row)
        self.assertFalse(row['eligibility']['accepted'])
        self.assertTrue(row['eligibility']['reasons'])

    def test_finalist_gap_refusal_survives_into_child_manifest_without_pair(self):
        def delivered(name, *args, diagnostics=None, **kwargs):
            if name.startswith('parent'):
                return self.parent_source
            if name.startswith('child0'):
                diagnostics['gap'] = {'declared_m':7.144,'delivered_m':1.94,'satisfied':False}
                return None
            return source(11+int(name[5]))
        _, _, render, _ = self.run_payload(sources=delivered)
        self.assertEqual(render.call_count,3)
        row=json.loads((self.out/'mutants.json').read_text())['children'][0]
        self.assertNotIn('pair',row)
        self.assertEqual(row['eligibility']['reasons'],['declared_gap_closed'])
        self.assertEqual(row['eligibility']['gap']['delivered_m'],1.94)
