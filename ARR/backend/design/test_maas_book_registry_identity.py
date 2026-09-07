"""Delivery must select the judged BOOK snapshot, never lexical name winners."""
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
import book_import


class BookRegistryIdentityTests(SimpleTestCase):
    def test_missing_unseated_book_still_returns_no_rebuild(self):
        import vlm_shortlist
        with patch.object(book_import, 'registry', return_value={}):
            self.assertEqual(vlm_shortlist.rebuild_seat(
                'book:missing', {}, None, None, None, None), (None, None))

    def test_judged_round_wins_over_later_lexical_snapshot(self):
        name = 'book:inherited:creative-001'
        with TemporaryDirectory() as tmp, patch.object(book_import, 'BOOKS', Path(tmp)):
            for stage, shape, cert in [('book-comp12', 'fresh', 'new-cert'),
                                       ('book-develop-comp03', 'stale', 'old-cert')]:
                entry = {'trace': 'creative-001', 'delivered_shape_id': shape,
                         'numeric_certificate': {'name': name, 'shape_id': shape,
                                                 'certificate_id': cert}}
                (Path(tmp) / f'{stage}.json').write_text(json.dumps(
                    {'book_dir': stage, 'entries': {name: entry}}), encoding='utf8')
            row = {'name': name, 'round': 'vlm-book-comp12', 'shape_id': 'fresh',
                   'certificate_id': 'new-cert'}
            self.assertEqual(book_import.registry()[name]['book_dir'], 'book-develop-comp03')
            selected = book_import.entry_for_judged_row(row)
            self.assertEqual(selected['book_dir'], 'book-comp12')
            for field in ('shape_id', 'certificate_id'):
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'identity'):
                    book_import.entry_for_judged_row({**row, field: 'wrong'})
            with self.assertRaisesRegex(ValueError, 'snapshot'):
                book_import.entry_for_judged_row({**row, 'round': 'vlm-book-missing'})

    def test_rebuild_uses_explicit_snapshot_record(self):
        entry = {'book_dir': 'judged', 'trace': 'right'}
        record = {'trace_sequence_name': 'right'}
        source = object()
        with patch.object(book_import, 'registry', side_effect=AssertionError('global lookup')), \
             patch.object(book_import, 'records_of', return_value=[record]) as records, \
             patch.object(book_import, '_compile_record', return_value=(source, {})) as compile_record:
            self.assertIs(book_import.book_rebuild('book:x', 'site', 'host', book_entry=entry), source)
        records.assert_called_once_with(Path('judged'))
        compile_record.assert_called_once_with(record, 'host', 'site')
