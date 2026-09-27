"""Production score/selection boundaries must not mix different judging rulers."""
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'
sys.path.insert(0, str(TOOLS))
import vlm_shortlist
import study_sheet
import board_curate
from evaluation_contract import rubric_id, stage_contract


class EvaluationContractTests(TestCase):
    def test_identity_excludes_site_data_but_changes_with_box_penalty(self):
        neutral = 'You are a juror. Assess a legible spatial principle.'
        penalty = 'You are a juror. SEVERELY PENALIZE simple boxes.'
        self.assertEqual(rubric_id('SITE INPUT DATA\nparcel 100\n\n' + neutral),
                         rubric_id('SITE INPUT DATA\nparcel 200\n\n' + neutral))
        self.assertNotEqual(rubric_id(neutral), rubric_id(penalty))

    def test_changed_frozen_prompt_is_refused(self):
        with TemporaryDirectory() as tmp:
            stage = Path(tmp)
            prompt = stage / 'PROMPT.txt'
            prompt.write_text('You are a juror. Neutral.', encoding='utf8')
            original = stage_contract(stage, freeze=True)
            self.assertEqual(original, stage_contract(stage, freeze=True))
            prompt.write_text('You are a juror. Penalize boxes.', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'prompt changed'):
                stage_contract(stage, freeze=True)
            self.assertEqual(original, stage_contract(stage))

    def test_new_board_reads_only_manifest_with_active_rubric(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'inputs').mkdir()
            rubric = 'You are a juror. SEVERELY PENALIZE boxes.'
            (root / 'inputs/judge-prompts-overseas.json').write_text(json.dumps({'rubric':rubric}), encoding='utf8')
            for name, identity in [('comp34', rubric_id('You are a juror. Neutral.')),
                                   ('comp35', rubric_id(rubric)), ('unknown', None)]:
                stage = root / f'runs/vlm-{name}'
                stage.mkdir(parents=True)
                (stage / 'round.json').write_text(json.dumps({'track':'O', 'kind':'shortlist', 'rubric_id':identity}), encoding='utf8')
                (stage / 'vlm-shortlist.json').write_text('[]', encoding='utf8')
            with patch.object(board_curate, 'ROOT', root):
                self.assertEqual(board_curate.rounds(), [('O', 'runs/vlm-comp35/vlm-shortlist.json', 'shortlist')])

    def test_curator_writes_only_compatible_scores_and_keeps_tracks_separate(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'inputs').mkdir()
            for track, filename in [('O','judge-prompts-overseas.json'), ('K','judge-prompts.json')]:
                rubric = f'You are a juror. Track {track}.'
                identity = rubric_id(rubric)
                (root / 'inputs' / filename).write_text(json.dumps({'rubric':rubric}), encoding='utf8')
                stage = root / f'runs/vlm-{track}'
                stage.mkdir(parents=True)
                (stage / 'round.json').write_text(json.dumps({'track':track, 'kind':'shortlist', 'rubric_id':identity}), encoding='utf8')
                (stage / 'vlm-shortlist.json').write_text(json.dumps([
                    {'name':'same-sentence', 'score':4.31 if track == 'O' else 4.59,
                     'pass':True, 'rubric_id':identity},
                    {'name':'missing', 'score':5, 'pass':True},
                    {'name':'old', 'score':4.9, 'pass':True, 'rubric_id':'old'},
                ]), encoding='utf8')
            # Only the unrelated geometric presentation loader is stubbed;
            # real round discovery, ledger admission and curator all execute.
            with patch.object(board_curate, 'ROOT', root), patch.object(board_curate, 'corpus', return_value={}), \
                 patch('presentation_aliases.current_source_loader', return_value=lambda row:(None, None)), \
                 patch.object(sys, 'argv', ['board_curate.py']):
                self.assertEqual(board_curate.main(), 0)
            ledger = json.loads((root / 'runs/board/ledger.json').read_text())
            board = json.loads((root / 'runs/board/board-key.json').read_text())
            self.assertEqual(len(ledger), 2)
            self.assertEqual({row['label'] for row in board}, {'K1', 'O1'})
            self.assertEqual(len({row['rubric_id'] for row in board}), 2)

    def test_new_stage_does_not_rebuild_incompatible_or_unknown_anchors(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / 'runs/vlm-new'
            stage.mkdir(parents=True)
            (stage / 'PROMPT.txt').write_text('You are a juror. Penalize boxes.', encoding='utf8')
            board = root / 'runs/board'
            board.mkdir()
            (board / 'board-key.json').write_text(json.dumps([
                {'label':'O1', 'name':'book:old', 'score':4.59, 'rubric_id':'old'},
                {'label':'O2', 'name':'book:unknown', 'score':4.7},
            ]), encoding='utf8')
            with patch.object(vlm_shortlist, 'ROOT', root), patch.object(vlm_shortlist, 'seat_context') as rebuild:
                self.assertEqual(vlm_shortlist.ride_anchors(stage, []), 0)
                rebuild.assert_not_called()
            self.assertTrue(stage_contract(stage)['rubric_id'])

    def test_historical_sheet_without_contract_retains_replay(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            board = root / 'runs/board'
            board.mkdir(parents=True)
            (board / 'board-key.json').write_text(json.dumps([
                {'label':'O1', 'name':'book:historical', 'score':4.59},
            ]), encoding='utf8')
            with patch.object(study_sheet, 'ROOT', root):
                self.assertEqual(study_sheet._candidate_rows('historical')[0]['name'], 'book:historical')

    def test_historical_run_cannot_inject_scores_into_new_active_board(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'inputs').mkdir()
            rubric = 'You are a juror. Penalize boxes.'
            active = rubric_id(rubric)
            (root / 'inputs/judge-prompts-overseas.json').write_text(json.dumps({'rubric':rubric}), encoding='utf8')
            board = root / 'runs/board'
            board.mkdir(parents=True)
            (board / 'board-key.json').write_text(json.dumps([
                {'label':'O1', 'name':'book:new', 'score':4.31, 'rubric_id':active},
            ]), encoding='utf8')
            stage = root / 'runs/vlm-historical'
            stage.mkdir()
            (stage / 'vlm-shortlist.json').write_text(json.dumps([
                {'name':'book:old', 'score':4.59, 'pass':True},
            ]), encoding='utf8')
            with patch.object(study_sheet, 'ROOT', root):
                self.assertEqual([row['name'] for row in study_sheet._candidate_rows('historical')], ['book:new'])

    def test_neutral_comp34_cannot_outscore_explicit_box_penalty_comp35(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            board = root / 'runs/board'
            board.mkdir(parents=True)
            stage = root / 'runs/vlm-book-comp35'
            stage.mkdir()
            (stage / 'PROMPT.txt').write_text('SITE INPUT DATA\nunknown\n\nYou are a juror. SEVERELY PENALIZE boxes.', encoding='utf8')
            (stage / 'evaluation-contract.json').write_text(json.dumps({'rubric_id':'new'}), encoding='utf8')
            (stage / 'round.json').write_text(json.dumps({'rubric_id':'new'}), encoding='utf8')
            (board / 'board-key.json').write_text(json.dumps([
                {'label':'O1', 'name':'book:comp34', 'score':4.59, 'rubric_id':'old'},
                {'label':'O2', 'name':'book:unknown', 'score':4.9},
                {'label':'O3', 'name':'book:compatible', 'score':4.2, 'rubric_id':'new'},
            ]), encoding='utf8')
            (stage / 'vlm-shortlist.json').write_text(json.dumps([
                {'name':'book:comp35', 'score':4.31, 'pass':True, 'rubric_id':'new'},
                {'name':'book:missing', 'score':5, 'pass':True},
            ]), encoding='utf8')
            before = (board / 'board-key.json').read_bytes()
            with patch.object(study_sheet, 'ROOT', root):
                self.assertEqual([r['name'] for r in study_sheet._candidate_rows('book-comp35')],
                                 ['book:comp35', 'book:compatible'])
            self.assertEqual(before, (board / 'board-key.json').read_bytes())

    def test_score_records_frozen_rubric_and_ignores_incompatible_anchor(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / 'runs/vlm-book-new'
            stage.mkdir(parents=True)
            (stage / 'PROMPT.txt').write_text('SITE INPUT DATA\nunknown\n\nYou are a juror. Penalize boxes.', encoding='utf8')
            (stage / 'key.json').write_text(json.dumps([
                {'tile':'t01', 'name':'book:new'},
                {'tile':'t02', 'name':'book:old', 'anchor':5, 'rubric_id':'old'},
            ]), encoding='utf8')
            verdict = stage / 'r1.txt'
            (stage / 'jury-provenance.json').write_text(json.dumps({'mode':'external', 'model':None, 'jurors':[{'id':'r1'}]}), encoding='utf8')
            verdict.write_text('TILE t01\nWEIGHTED 3.50\nTILE t02\nWEIGHTED 2.00\n', encoding='utf8')
            with patch.object(vlm_shortlist, 'ROOT', root):
                vlm_shortlist.score('book-new', [str(verdict)])
            rows = json.loads((stage / 'vlm-shortlist.json').read_text())
            self.assertEqual(rows[0]['corrected'], 3.5)
            self.assertTrue(rows[0].get('rubric_id'))
            self.assertEqual(rows[0]['rubric_id'], json.loads((stage / 'round.json').read_text())['rubric_id'])
            self.assertEqual(rows[0]['jury_provenance']['mode'], 'external')
            self.assertIsNone(rows[0]['jury_provenance']['model'])
