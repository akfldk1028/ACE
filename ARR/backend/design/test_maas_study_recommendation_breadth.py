"""A short comparison should not spend two seats on a source and its child."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from design.test_maas_study_registered_book import study_sheet
from unittest.mock import patch


class RecommendationBreadthTests(SimpleTestCase):
    def setUp(self):
        self.rows = [dict(name=n, shape_id='shape-' + n, certificate_id='cert-' + n,
                          round='vlm-fixture', score=5 - i / 10)
                     for i, n in enumerate(['child', 'curve', 'parent', 'court'])]
        self.lineages = dict(child='bridge', parent='bridge', curve='curve', court='court')

    def choose(self, lineages, refused=()):
        accepted, chosen = set(), []
        for row in study_sheet._comparison_rows(self.rows, lineages, accepted):
            if row['name'] in refused:
                continue
            chosen.append(row)
            if lineages is not None:
                accepted.add(lineages[row['name']])
            if len(chosen) == 3:
                break
        return [r['name'] for r in chosen]

    def test_source_child_share_comparison_opportunity_not_geometry_identity(self):
        before = json.dumps(self.rows)
        self.assertEqual(self.choose(None), ['child', 'curve', 'parent'])
        self.assertEqual(self.choose(self.lineages), ['child', 'curve', 'court'])
        self.assertEqual(json.dumps(self.rows), before)  # full ranked pool and scores survive
        self.assertNotEqual(self.rows[0]['shape_id'], self.rows[2]['shape_id'])

    def test_backfill_keeps_distinct_sections_when_only_one_lineage_exists(self):
        self.assertEqual(self.choose({r['name']: 'same-source' for r in self.rows}),
                         ['child', 'curve', 'parent'])

    def test_refused_child_does_not_reserve_its_lineage(self):
        self.assertEqual(self.choose(self.lineages, refused={'child'}),
                         ['curve', 'parent', 'court'])

    def test_context_binds_round_board_complete_ranked_candidates_and_identity(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            board = root / 'runs/board/board-key.json'
            board.parent.mkdir(parents=True)
            board.write_text('[]', encoding='utf8')
            context = dict(schema='arr.maas.recommendation_context.v1', run='fixture',
                           board_sha256=hashlib.sha256(board.read_bytes()).hexdigest(),
                           candidates=[dict(identity=study_sheet._recommendation_identity(r),
                                            lineage=self.lineages[r['name']]) for r in self.rows])
            path = root / 'recommendation.json'
            def load(data, rows=None, run='fixture'):
                path.write_text(json.dumps(data), encoding='utf8')
                return study_sheet._recommendation_lineages(run, rows or self.rows, path)
            with patch.object(study_sheet, 'ROOT', root):
                self.assertEqual(load(context), self.lineages)
                for field in ['name', 'shape_id', 'certificate_id', 'score', 'round']:
                    altered = json.loads(json.dumps(context))
                    altered['candidates'][0]['identity'][field] = 'changed'
                    with self.subTest(field=field), self.assertRaises(ValueError):
                        load(altered)
                for altered in [dict(context, run='other'), dict(context, board_sha256='stale'),
                                dict(context, candidates=context['candidates'][:-1]),
                                dict(context, candidates=list(reversed(context['candidates']))),
                                dict(context, schema='unknown'), dict(context, candidates=None)]:
                    with self.assertRaises(ValueError):
                        load(altered)
                malformed = json.loads(json.dumps(context))
                malformed['candidates'][0]['lineage'] = ''
                with self.assertRaises(ValueError):
                    load(malformed)

    def test_context_does_not_rescue_a_stale_actual_book_certificate(self):
        from design.test_maas_study_registered_book import RegisteredBookStudyTests
        from design.test_maas_study_registered_book import book_import, vlm_shortlist
        fixture = RegisteredBookStudyTests()
        fixture.setUp()
        with patch.object(book_import, 'registry', return_value=fixture.registry):
            cert = vlm_shortlist.seat_certificate(fixture.name, fixture.source, {}, fixture.site)
            for stale in (False, True):
                with self.subTest(stale=stale), TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    row = dict(name=fixture.name, shape_id=cert['shape_id'], score=4.5,
                               certificate_id='stale' if stale else cert['certificate_id'],
                               round='vlm-book-fixture')
                    board = root / 'runs/board/board-key.json'
                    board.parent.mkdir(parents=True)
                    board.write_text(json.dumps([row]), encoding='utf8')
                    context = root / 'recommendation-context.json'
                    context.write_text(json.dumps(dict(
                        schema='arr.maas.recommendation_context.v1', run='registered-fixture',
                        board_sha256=hashlib.sha256(board.read_bytes()).hexdigest(),
                        candidates=[dict(identity=study_sheet._recommendation_identity(row),
                                         lineage='verified-source')])) , encoding='utf8')
                    self.assertEqual(fixture.run_study(root, row, context), 1 if stale else 0)
                    result = json.loads((root / 'runs/study-registered-fixture/study.json').read_text(encoding='utf8'))
                    self.assertEqual(len(result['alternatives']), 0 if stale else 1)
                    self.assertEqual(result['comparison_selection']['policy'],
                                     'source-ancestry-first-with-shape-backfill.v1')
