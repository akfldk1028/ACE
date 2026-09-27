"""BOOK-only delivery excludes legacy contestants and unjudged canon seats."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from design.test_maas_evaluation_contract import board_curate, study_sheet, rubric_id


class BookOnlySelectionTests(TestCase):
    def test_curator_limits_book_only_seats_and_preserves_mixed_mode(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'inputs').mkdir()
            rubric = 'You are a juror. Evaluate massing.'
            identity = rubric_id(rubric)
            (root / 'inputs/judge-prompts-overseas.json').write_text(json.dumps({'rubric': rubric}))
            (root / 'inputs/gen-canon.json').write_text(json.dumps({'schemes': [
                {'name': 'legacy-canon', 'layer': 'canon'}]}))
            stage = root / 'runs/vlm-current'
            stage.mkdir(parents=True)
            (stage / 'round.json').write_text(json.dumps(
                {'track': 'O', 'kind': 'shortlist', 'rubric_id': identity}))
            (stage / 'vlm-shortlist.json').write_text(json.dumps([
                {'name': name, 'score': 4.2, 'pass': True, 'rubric_id': identity}
                for name in ['book:current:one', 'legacy-massv2']]))
            for mode, expected in [('1', {'book:current:one'}),
                                   ('0', {'book:current:one', 'legacy-massv2', 'legacy-canon'})]:
                with self.subTest(mode=mode), patch.dict(os.environ, {'BOOK_ONLY': mode}), \
                     patch.object(board_curate, 'ROOT', root), \
                     patch.object(board_curate, 'corpus', return_value={}), \
                     patch('presentation_aliases.current_source_loader', return_value=lambda row: (None, None)), \
                     patch('sys.argv', ['board_curate.py']):
                    self.assertEqual(board_curate.main(), 0)
                    board = json.loads((root / 'runs/board/board-key.json').read_text())
                    self.assertEqual({row['name'] for row in board}, expected)

    def test_study_excludes_non_book_board_and_fresh_scores_in_book_only(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            board = root / 'runs/board'
            board.mkdir(parents=True)
            (board / 'board-key.json').write_text(json.dumps([
                {'label': 'O1', 'name': 'legacy-board', 'score': 4.9},
                {'label': 'O2', 'name': 'book:board:one', 'score': 4.2}]))
            stage = root / 'runs/vlm-current'
            stage.mkdir()
            (stage / 'vlm-shortlist.json').write_text(json.dumps([
                {'name': 'legacy-fresh', 'score': 4.8, 'pass': True},
                {'name': 'book:current:one', 'score': 4.1, 'pass': True}]))
            with patch.dict(os.environ, {'BOOK_ONLY': '1'}), patch.object(study_sheet, 'ROOT', root):
                self.assertEqual({row['name'] for row in study_sheet._candidate_rows('current')},
                                 {'book:board:one', 'book:current:one'})
