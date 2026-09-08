"""Actual occupied-form aliases preserve independent scores and dimension records."""
from copy import deepcopy
from dataclasses import replace
import unittest

from shapely.geometry import box
from design.test_maas_book_delivered_areas import book_import  # exposes tools path
from design.maas.source_geometry.ir import SourceMass, SourceVolume
from presentation_aliases import group_presentations
from vlm_shortlist import certificate_digest, shape_id


def body(role='body', *, height=10):
    plan = box(0, 0, 20, 10)
    return SourceMass(name=role, footprint=plan,
        volumes=(SourceVolume(role, plan, 0, 1, 'occupied'),),
        metadata={'authored_height_m': height})


def judged(name, source, score=4.0, round_name='vlm-test'):
    cert = dict(name=name, shape_id=shape_id(source), height_m=source.metadata['authored_height_m'])
    cert['certificate_id'] = certificate_digest(cert)
    row = dict(track='O', round=round_name, name=name, score=score, pass_=True,
               shape_id=cert['shape_id'], certificate_id=cert['certificate_id'],
               scored_row={'independent_jury': [score, score-0.1, score+0.1]})
    return row, cert


class PresentationAliasGroupTests(unittest.TestCase):
    def test_role_only_alias_and_unselected_alias_share_one_image_without_rewriting_scores(self):
        sources = {'a': body(), 'b': body('other-role'), 'c': body('third-role'), 'd': body(height=12)}
        records = {name: judged(name, source, score=4.5-index/10)
                   for index, (name, source) in enumerate(sources.items())}
        curated = [records[name][0] for name in ('a', 'b', 'd')]
        ledger = [record[0] for record in records.values()]
        before = deepcopy((curated, ledger))
        self.assertNotEqual(records['a'][0]['shape_id'], records['b'][0]['shape_id'])
        shown, audit = group_presentations(curated, ledger,
            lambda row: (sources[row['name']], records[row['name']][1]))
        self.assertEqual([row['name'] for row in shown], ['a', 'd'])
        self.assertEqual([entry['row']['name'] for entry in shown[0]['solid_form_aliases']], ['b', 'c'])
        self.assertEqual((curated, ledger), before)
        self.assertEqual(shown[0]['score'], 4.5)
        groups = {entry['row']['name']: entry['group_id'] for entry in audit['entries']}
        self.assertEqual(groups['a'], groups['b'])
        self.assertEqual(groups['a'], groups['c'])
        self.assertNotEqual(groups['a'], groups['d'])
        self.assertEqual(len(audit['entries']), 4)

    def test_stale_geometry_or_certificate_never_becomes_an_alias(self):
        sources = {'a': body(), 'b': body('other')}
        records = {name: judged(name, source) for name, source in sources.items()}
        for altered in ('shape_id', 'certificate_id'):
            rows = [deepcopy(records[name][0]) for name in sources]
            rows[1][altered] = 'stale'
            with self.subTest(altered=altered):
                shown, audit = group_presentations(rows, rows,
                    lambda row: (sources[row['name']], records[row['name']][1]))
                self.assertEqual(len(shown), 2)
                self.assertEqual(audit['entries'][1]['comparison']['status'], 'unsupported')

    def test_unrebuildable_candidate_is_preserved_and_not_used_as_equivalence_authority(self):
        row, cert = judged('a', body())
        shown, audit = group_presentations([row], [row], lambda _: (None, None))
        self.assertEqual(shown[0]['name'], 'a')
        self.assertEqual(audit['entries'][0]['comparison']['status'], 'unsupported')
