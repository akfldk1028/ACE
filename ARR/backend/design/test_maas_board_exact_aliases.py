"""Presentation aliases require complete, bound evidence, never plan similarity."""
import copy
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
import board_curate
import vlm_shortlist


class BoardExactAliasTests(SimpleTestCase):
    def setUp(self):
        # Actual comp15 O3/O5 public evidence: only name and its bound hash differ.
        self.names = ['book:book-comp11:morph-compact-mid:creative-012',
                      'book:book-comp15:morph-compact-mid:creative-012']
        self.rows = [dict(track='O', name=name, score=4.0, round='vlm-book-comp15',
                          shape_id='dacbb205cef6ed7a1d3e', certificate_id=cid)
                     for name, cid in zip(self.names, ['4589e41b0f45a7cf59bf',
                                                       'ade77bf0d5b994f26c3f'])]
        frozen = Path(__file__).resolve().parent / 'fixtures/comp15_exact_bridge_aliases.json'
        entries = json.loads(frozen.read_text(encoding='utf-8'))
        self.keys = [copy.deepcopy(next(r for r in entries if r['name'] == name))
                     for name in self.names]

    def curate(self, rows=None, keys=None):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'runs/vlm-book-comp15/key.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(self.keys if keys is None else keys), encoding='utf-8')
            return board_curate.exact_presentation_aliases(
                self.rows if rows is None else rows, root=root)

    def test_actual_o3_o5_alias_keeps_first_equal_score_and_full_evidence(self):
        before = copy.deepcopy(self.rows)
        chosen = self.curate()
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0]['name'], self.names[0])
        alias = chosen[0]['exact_geometry_aliases'][0]
        self.assertEqual(alias['row'], self.rows[1])
        self.assertEqual(alias['public_key'], self.keys[1])
        self.assertEqual(self.rows, before)
        self.assertNotIn('exact_geometry_aliases', self.rows[0])

    def test_higher_score_wins_without_rewriting_it(self):
        rows = copy.deepcopy(self.rows)
        rows[1]['score'] = 4.3
        chosen = self.curate(rows=rows)
        self.assertEqual(chosen[0]['name'], self.names[1])
        self.assertEqual(chosen[0]['score'], 4.3)
        self.assertEqual(chosen[0]['exact_geometry_aliases'][0]['row'], rows[0])

    def test_both_certificates_changed_with_stale_ids_remain_separate(self):
        keys = copy.deepcopy(self.keys)
        for key in keys:
            key['certificate']['height_m'] += 1.0
        self.assertEqual(len(self.curate(keys=keys)), 2)

    def test_certificate_owner_preserves_both_known_fixture_ids(self):
        for key in self.keys:
            cert = key['certificate']
            before = copy.deepcopy(cert)
            with self.subTest(name=cert['name']):
                self.assertEqual(vlm_shortlist.certificate_digest(cert), cert['certificate_id'])
                without_id = {k: v for k, v in cert.items() if k != 'certificate_id'}
                self.assertEqual(vlm_shortlist.certificate_digest(without_id), cert['certificate_id'])
                self.assertEqual(cert, before)

    def test_different_roof_shape_and_every_numeric_difference_survive(self):
        for field in ['shape_id', 'gross_m2', 'height_m', 'storey_m']:
            keys, rows = copy.deepcopy(self.keys), copy.deepcopy(self.rows)
            if field == 'shape_id':
                rows[1][field] = keys[1][field] = keys[1]['certificate'][field] = 'other-roof'
            else:
                keys[1]['certificate'][field] += 0.000001
            # Keep changed controls validly hashed: their geometry/evidence
            # difference, rather than a stale digest, must prevent merging.
            cid = vlm_shortlist.certificate_digest(keys[1]['certificate'])
            keys[1]['certificate']['certificate_id'] = rows[1]['certificate_id'] = cid
            if 'certificate_id' in keys[1]:
                keys[1]['certificate_id'] = cid
            with self.subTest(field=field):
                self.assertEqual(len(self.curate(rows, keys)), 2)
        keys = copy.deepcopy(self.keys)
        rows = copy.deepcopy(self.rows)
        keys[1]['certificate']['storey_limit']['max_storeys'] = 4
        cid = vlm_shortlist.certificate_digest(keys[1]['certificate'])
        keys[1]['certificate']['certificate_id'] = rows[1]['certificate_id'] = cid
        if 'certificate_id' in keys[1]:
            keys[1]['certificate_id'] = cid
        self.assertEqual(len(self.curate(rows=rows, keys=keys)), 2)

    def test_missing_wrong_bound_or_malformed_evidence_does_not_merge(self):
        mutations = [lambda k: k.pop('certificate'),
                     lambda k: k['certificate'].pop('height_m'),
                     lambda k: k['certificate'].update(name='wrong'),
                     lambda k: k['certificate'].update(certificate_id='wrong'),
                     lambda k: k.update(shape_id='wrong'),
                     lambda k: k['certificate'].update(height_m=float('nan'))]
        for mutate in mutations:
            keys = copy.deepcopy(self.keys)
            mutate(keys[1])
            with self.subTest(mutation=mutate):
                self.assertEqual(len(self.curate(keys=keys)), 2)
        for field in ['shape_id', 'certificate_id', 'round', 'track']:
            rows = copy.deepcopy(self.rows)
            rows[1].pop(field)
            with self.subTest(missing=field):
                self.assertEqual(len(self.curate(rows=rows)), 2)
        self.assertEqual(len(self.curate(keys=self.keys + [self.keys[1]])), 2)

    def test_track_or_judging_context_difference_does_not_merge(self):
        for field, value in [('track', 'K'), ('round', 'vlm-other')]:
            rows = copy.deepcopy(self.rows)
            rows[1][field] = value
            with self.subTest(field=field):
                self.assertEqual(len(self.curate(rows=rows)), 2)

    def test_main_writes_both_scored_sources_to_ledger_and_alias_to_board(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / 'runs/vlm-book-comp15'
            directory.mkdir(parents=True)
            (directory / 'key.json').write_text(json.dumps(self.keys), encoding='utf-8')
            scored = [dict(row, **{'pass': True, 'jury_detail': {'original': i}})
                      for i, row in enumerate(self.rows)]
            (directory / 'vlm-shortlist.json').write_text(json.dumps(scored), encoding='utf-8')
            with patch.object(board_curate, 'ROOT', root), \
                 patch.object(board_curate, 'rounds', return_value=[
                     ('O', 'runs/vlm-book-comp15/vlm-shortlist.json', 'shortlist')]), \
                 patch.object(board_curate, 'corpus', return_value={}), \
                 patch.object(sys, 'argv', ['board_curate.py']), patch('builtins.print'):
                self.assertEqual(board_curate.main(), 0)
            ledger = json.loads((root / 'runs/board/ledger.json').read_text(encoding='utf-8'))
            board = json.loads((root / 'runs/board/board-key.json').read_text(encoding='utf-8'))
            self.assertEqual(len(ledger), 2)
            self.assertEqual([r['scored_row'] for r in ledger], scored)
            self.assertTrue(all('exact_geometry_aliases' not in r for r in ledger))
            self.assertEqual(len(board), 1)
            self.assertEqual(board[0]['label'], 'O1')
            self.assertEqual(board[0]['certificate_id'], self.rows[0]['certificate_id'])
            self.assertEqual(board[0]['exact_geometry_aliases'][0]['row']['scored_row'], scored[1])
