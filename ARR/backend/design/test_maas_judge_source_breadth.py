"""Jury membership preserves selected fresh sources without promoting rejected work."""
import random
import sys
from pathlib import Path

from django.test import SimpleTestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
import judge_tiles


def summary(names, cells=None):
    return {'selection': {'chosen_names': names},
            'records': [{'name': name, 'cell': (cells or {}).get(name, 'shared')}
                        for name in names]}


class JudgeSourceBreadthTests(SimpleTestCase):
    def allocate(self, data, count, fresh, refused=()):
        calls = []
        def rebuild(name):
            calls.append(name)
            return (None, 'existing rebuild refused') if name in refused else (object(), None)
        seats, evidence = judge_tiles.allocate_stage(data, count, fresh, rebuild)
        self.assertEqual(len(calls), len(set(calls)), 'one cached rebuild per attempted candidate')
        return [name for name, _source in seats], evidence

    def test_selected_fresh_sources_survive_shared_cell_and_unselected_source_does_not(self):
        names = [f'old-{i}' for i in range(15)] + ['curved~fit', 'folded^open']
        admitted, evidence = self.allocate(summary(names), 3, ['curved', 'folded', 'unselected'])
        self.assertIn('curved~fit', admitted)
        self.assertIn('folded^open', admitted)
        self.assertNotIn('unselected', admitted)
        self.assertEqual(evidence['fresh_sources_without_selected_variant'], ['unselected'])

    def test_union_keeps_existing_cell_representatives_and_records_overflow(self):
        names = ['old-single', 'old-pair', 'fresh~one', 'fresh-two']
        data = summary(names, {'old-single': 'single', 'old-pair': 'pair',
                               'fresh~one': 'single', 'fresh-two': 'single'})
        admitted, evidence = self.allocate(data, 1, ['fresh', 'fresh-two'])
        self.assertIn('old-pair', admitted)
        self.assertIn('fresh~one', admitted)
        self.assertIn('fresh-two', admitted)
        self.assertGreaterEqual(len(admitted), 3)
        self.assertEqual(evidence['overflow_count'], len(admitted) - 1)
        self.assertEqual({r['cell'] for r in evidence['cell_representatives']}, {'single', 'pair'})

    def test_source_uses_selector_variant_order_and_falls_back_after_refusal(self):
        data = summary(['fresh~first', 'fresh^second', 'old'])
        admitted, evidence = self.allocate(data, 1, ['fresh'], refused=['fresh~first'])
        self.assertNotIn('fresh~first', admitted)
        self.assertIn('fresh^second', admitted)
        self.assertEqual(evidence['source_reservations'], [{'source': 'fresh', 'name': 'fresh^second'}])
        self.assertEqual(evidence['refused'][0]['name'], 'fresh~first')
        self.assertEqual(evidence['refused'][0]['reason'], 'existing rebuild refused')

    def test_all_fresh_variants_refused_are_not_admitted_or_called_success(self):
        admitted, evidence = self.allocate(summary(['fresh', 'old']), 1, ['fresh'], refused=['fresh'])
        self.assertEqual(admitted, ['old'])
        self.assertEqual(evidence['fresh_sources_without_rebuildable_variant'], ['fresh'])
        self.assertEqual(evidence['source_reservations'], [])

    def test_missing_historical_source_input_preserves_legacy_order_and_budget(self):
        names = ['a', 'b', 'c', 'd']
        data = summary(names, {'a': 'one', 'b': 'one', 'c': 'two', 'd': 'three'})
        shuffled = names[:]
        random.Random(20260831).shuffle(shuffled)
        first, rest, seen = [], [], set()
        for name in shuffled:
            cell = next(r['cell'] for r in data['records'] if r['name'] == name)
            (rest if cell in seen else first).append(name)
            seen.add(cell)
        admitted, evidence = self.allocate(data, 2, None)
        self.assertEqual(admitted, (first + rest)[:2])
        self.assertEqual(evidence['policy'], 'legacy_cell_order')
        self.assertEqual(evidence['overflow_count'], 0)
