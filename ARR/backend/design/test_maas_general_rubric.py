"""Juror rulers retain their score contracts and bind only supplied site data."""
import ast
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

from django.test import SimpleTestCase
from shapely.geometry import box
from design.maas.massv2.legal import LegalSite

TOOLS=Path(__file__).resolve().parents[1]/'tmp_mass_check/_massv2/tools'
sys.path.insert(0,str(TOOLS))
import vlm_shortlist as jury


class GeneralRubricTests(SimpleTestCase):
    def test_missing_site_has_no_sample_programme_or_parcel(self):
        for track in ('overseas','korea'):
            text=jury.rubric_for(track)
            for forbidden in ('2,500','2500','1,546','1,500-6,000','효돈','산곡','civic budget','community centre'):
                self.assertNotIn(forbidden,text)
            self.assertIn('not supplied',text)
            self.assertFalse(re.search('[가-힣]',text))

    def test_two_actual_sites_supply_distinct_data_and_unknowns(self):
        def site(pnu,width,use):
            return LegalSite(pnu,box(0,0,width,20),(0,0),
                SimpleNamespace(envelope=SimpleNamespace(floor_height=4.1)),
                {'bcr_footprint_capacity_m2':width*8,'statutory_far_capacity_m2':width*30},
                building_type=use)
        a,b=site('1111111111111111111',30,'library'),site('2222222222222222222',70,'housing')
        for s,area,ground in ((a,600,240),(b,1400,560)):
            text=jury.rubric_for('overseas',site=s)
            data=json.loads(text.split('SITE INPUT DATA\n```json\n',1)[1].split('\n```',1)[0])
            self.assertEqual(data['parcel_area_m2'],area)
            self.assertEqual(data['ground_capacity_m2'],ground)
            self.assertEqual(data['building_use_input'],s.building_type)
            self.assertEqual(data['statutory_max_height_m'],'unknown_or_not_established')
            self.assertEqual(data['max_storeys'],'unknown_or_not_established')
            self.assertEqual(data['terrain_datum_measured'],False)
            self.assertNotIn(s.pnu,text)
        self.assertNotEqual(jury.rubric_for('korea',site=a),jury.rubric_for('korea',site=b))

    def test_site_data_whitelist_excludes_private_fields(self):
        supplied=SimpleNamespace(evidence=lambda:{'parcel_area_m2':900,'candidate_name':'SECRET_CANDIDATE',
            'score':4.99,'private_ballot':'SECRET_BALLOT','parcel_policy':{'previous_scores':[5]}})
        text=jury.rubric_for('korea',site=supplied)
        self.assertNotIn('SECRET',text)
        self.assertNotIn('previous_scores',text)
        self.assertIn('900',text)

    def test_track_weights_and_parser_tokens_remain_exact(self):
        from tempfile import TemporaryDirectory
        contracts={'overseas':{'CONCEPT':.35,'FEASIBILITY':.25,'SITE':.20,'EDITABILITY':.20},
                   'korea':{'AESTHETICS':.15,'FEASIBILITY':.35,'COMPLIANCE':.25,'EDITABILITY':.25}}
        for track,expected in contracts.items():
            text=jury.rubric_for(track)
            weights={k:float(v) for k,v in re.findall(r'\*\*([A-Z]+) \(weight (0\.\d+)\)\*\*',text)}
            self.assertEqual(weights,expected)
            for field in expected:
                self.assertIn('\n'+field+' <score> | <one line>',text)
            for token in ('TILE <id>','WEIGHTED <weighted mean, two decimals>','RANKING:','VERDICT:'):
                self.assertIn(token,text)
            with TemporaryDirectory() as tmp:
                ballot=Path(tmp)/'synthetic.txt'
                ballot.write_text('TILE t01\n'+'\n'.join(k+' 4 | observed' for k in expected)+
                    '\nWEIGHTED 4.00\nRANKING: t01\nVERDICT: Advance for development.',encoding='utf8')
                self.assertEqual(jury.read_verdict(ballot,{'t01'}),{'t01':4.0})

    def test_active_stage_callers_pass_their_site(self):
        for filename in ('vlm_shortlist.py','book_import.py','board_rejudge.py'):
            tree=ast.parse((TOOLS/filename).read_text(encoding='utf8'))
            calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)
                   and isinstance(n.func,ast.Name) and n.func.id=='rubric_for']
            self.assertTrue(calls,filename)
            for call in calls:
                self.assertTrue(any(k.arg=='site' and isinstance(k.value,ast.Name)
                                    and k.value.id=='site' for k in call.keywords),filename)
