"""An occupied grid cell must not erase distinct authored organizations before VLM."""
from dataclasses import replace
import unittest

from shapely.geometry import box

from design.maas.massv2.grammar import parti_from_record, declared_height_m
from design.maas.massv2.execute import execute
from design.maas.massv2.compile import compile_matrix_form
from design.maas.massv2.measure import measure_form
from design.maas.massv2.plausibility import Plausibility
from design.maas.massv2.family import family_tag
from design.maas.massv2.select import Candidate, choose, composition_signature


# The four comp07 spatial propositions that competed for a single two-seat
# cell, reduced to their actual operator inputs rather than mocked geometry.
RECORDS = [
    {'name':'four_rotated','ops':[{'op':'aggregate','n':4,'method':'stack','levels':4,
      'storeys':1,'unit':'slab','spread':1.08,'height':1,'tie':0,'turn':24,'reach':.06}]},
    {'name':'paired_levels','ops':[{'op':'aggregate','n':4,'method':'stack','levels':2,
      'storeys':2,'unit':'slab','spread':1.12,'height':1,'tie':0,'turn':0,'reach':.18}]},
    {'name':'inhabited_bridge','ops':[{'op':'extrude','height':1,'storeys':3},
      {'op':'shape','top_surface':{'type':'constant','height':1},'bottom_surface':{
       'type':'profile','points':[[0,0],[.26,0],[.28,.65],[.72,.65],[.74,0],[1,0]],'axis':[1,0],'span':[0,1]}}]},
    {'name':'continuous_court','ops':[{'op':'extrude','height':1,'storeys':4},
      {'op':'shape','plan_region':{'type':'Polygon','coordinates':[
       [[0,0],[1,0],[1,1],[0,1],[0,0]],[[.25,.24],[.25,.76],[.75,.76],[.75,.24],[.25,.24]]]},
       'top_surface':{'type':'profile','points':[[0,.5],[.3,.5],[.7,1],[1,1]],'axis':[1,0],'span':[0,1]},
       'bottom_surface':{'type':'constant','height':0}}]},
]


def actual_candidates():
    result = []
    for index, record in enumerate(RECORDS):
        record = {**record,'primary_language':'solid_body','floor_height_m':3.6,'growth':'plan'}
        form = execute(parti_from_record(record),buildable=box(0,0,40,32),axis=(1.,0.),
                       height_m=declared_height_m(record,3.6),storey_height_m=3.6)
        form = replace(form,extra={**form.extra,'spoken_force':1.-index*.2})
        source = compile_matrix_form(form,storey_height_m=3.6)
        assert source is not None
        result.append(Candidate(form,source,measure_form(source),Plausibility(1.,12.,1.,True,()),
                                'standing_body|single_body',.5,.5))
    return result


class AuthoredFamilyCoverageTests(unittest.TestCase):
    def setUp(self):
        self.candidates = actual_candidates()
        self.tags = {r['name']:family_tag(r) for r in RECORDS}

    def test_configured_family_coverage_exposes_all_four_organizations(self):
        self.assertEqual(len(set(self.tags.values())),4)
        selected = choose(self.candidates,per_cell=2,composition_family=self.tags)
        self.assertEqual({c.form.name for c in selected},set(self.tags))

    def test_unconfigured_cell_budget_is_unchanged(self):
        self.assertEqual(len(choose(self.candidates,per_cell=2)),2)

    def test_alias_tag_and_identical_geometry_do_not_get_extra_seats(self):
        original = self.candidates[0]
        alias = replace(original,form=replace(original.form,name='alias'))
        selected = choose([*self.candidates,alias],per_cell=2,
                          composition_family={**self.tags,'alias':self.tags[original.form.name]})
        self.assertEqual(len(selected),4)
        self.assertEqual(len({composition_signature(c.form) for c in selected}),4)
        # An invented different tag cannot make unchanged geometry distinct.
        selected = choose([*self.candidates,alias],per_cell=2,
                          composition_family={**self.tags,'alias':'different words for the same geometry'})
        self.assertEqual(len(selected),4)

    def test_programme_and_physical_refusals_cannot_be_rescued(self):
        good = [replace(c,form=replace(c.form,extra={**c.form.extra,
                       'programme_target':500.,'far_capacity_m2':1000.})) for c in self.candidates]
        bad = replace(good[-1],far_utilization=.1)
        selected = choose([*good[:-1],bad],per_cell=1,composition_family=self.tags)
        self.assertNotIn(bad.form.name,{c.form.name for c in selected})
        self.assertEqual(len(selected),3)
        unsupported = replace(good[-1],plausibility=Plausibility(1.,12.,1.,False,('unsupported',)))
        selected = choose([*good[:-1],unsupported],per_cell=1,composition_family=self.tags)
        self.assertNotIn(unsupported.form.name,{c.form.name for c in selected})
