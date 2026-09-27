"""BOOK-only presentation must never rebuild deferred massv2 alternatives."""
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'
sys.path.insert(0, str(TOOLS))
import board_curate
import study_sheet


class BookOnlyBoardTests(TestCase):
    def test_mixed_ledger_keeps_only_book_seats_before_rebuilding(self):
        for mode in ('1', '0'):
            with self.subTest(mode=mode), TemporaryDirectory() as tmp:
                root = Path(tmp)
                stage = root / 'runs/vlm-mixed'
                stage.mkdir(parents=True)
                inputs = root / 'inputs'
                inputs.mkdir()
                (inputs / 'gen-canon.json').write_text(json.dumps({'schemes':[
                    {'name':'canon-cylinder', 'layer':'canon'}]}), encoding='utf8')
                rows = [{'name':name, 'score':score, 'pass':True}
                        for name, score in [('book:authored', 4.2), ('legacy-mass', 4.9)]]
                (stage / 'vlm-shortlist.json').write_text(json.dumps(rows), encoding='utf8')
                loaded = []

                def load(row):
                    loaded.append(row['name'])
                    return None, None

                with patch.dict(os.environ, {'BOOK_ONLY':mode}), \
                     patch.object(board_curate, 'ROOT', root), \
                     patch.object(board_curate, 'rounds', return_value=[('O', 'runs/vlm-mixed/vlm-shortlist.json', 'shortlist')]), \
                     patch.object(board_curate, 'corpus', return_value={}), \
                     patch('presentation_aliases.current_source_loader', return_value=load), \
                     patch.object(sys, 'argv', ['board_curate.py']):
                    self.assertEqual(board_curate.main(), 0)
                board = json.loads((root / 'runs/board/board-key.json').read_text())
                names = {row['name'] for row in board}
                if mode == '1':
                    self.assertEqual(names, {'book:authored'})
                    self.assertNotIn('legacy-mass', loaded)
                else:
                    self.assertEqual(names, {'book:authored', 'legacy-mass', 'canon-cylinder'})
                ledger = json.loads((root / 'runs/board/ledger.json').read_text())
                self.assertEqual({row['name'] for row in ledger}, {'book:authored', 'legacy-mass'})

    def test_sheet_filters_mixed_board_and_fresh_shortlist(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            board = root / 'runs/board'
            board.mkdir(parents=True)
            stage = root / 'runs/vlm-mixed'
            stage.mkdir()
            (board / 'board-key.json').write_text(json.dumps([
                {'label':'O1', 'name':'legacy-board', 'score':4.9},
                {'label':'O2', 'name':'book:board', 'score':4.2},
            ]), encoding='utf8')
            (stage / 'vlm-shortlist.json').write_text(json.dumps([
                {'name':'legacy-fresh', 'score':4.8, 'pass':True},
                {'name':'book:fresh', 'score':4.3, 'pass':True},
            ]), encoding='utf8')
            for mode in ('1', '0'):
                with self.subTest(mode=mode), patch.dict(os.environ, {'BOOK_ONLY':mode}), \
                     patch.object(study_sheet, 'ROOT', root):
                    names = [row['name'] for row in study_sheet._candidate_rows('mixed')]
                    self.assertEqual(names, ['book:fresh', 'book:board'] if mode == '1' else
                                     ['legacy-board', 'legacy-fresh', 'book:fresh', 'book:board'])
