"""Delivery must use each actual authored scheme's own storey ruler."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.massv2.grammar import declared_height_m

TOOLS = Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'
sys.path.insert(0, str(TOOLS))
from vlm_shortlist import rebuild_seat

# The relevant declarations from the three comp01 selections. No run artifacts
# are needed by unit tests; the full real-site replay lives in the report.
DECLARATIONS = (
    ('sangok_saddle_garden_room', 2, .4),
    ('sangok_boundary_hinge', 3, .56),
    ('sangok_vaulted_civic_street', 3, .6),
)


class DeliveryStoreyBudgetTests(SimpleTestCase):
    def test_actual_three_selected_schemes_reach_executor_at_generator_budget(self):
        book = {name: {'name': name, 'floor_height_m': 3.6,
                      'ops': [{'op': 'extrude', 'storeys': floors, 'height': share}]}
                for name, floors, share in DECLARATIONS}
        site = SimpleNamespace(floor_height_m=3.8)
        base = 3.8 * 4
        for name in book:
            with self.subTest(name=name):
                record = book[name]
                expected = max(base, declared_height_m(record, record['floor_height_m']))
                with patch('finalists.execute_parti', return_value=None) as execute:
                    rebuild_seat(name, book, site, box(0, 0, 50, 50), (1, 0), base)
                self.assertAlmostEqual(execute.call_args.kwargs['height_m'], expected)
                self.assertEqual(execute.call_args.kwargs['storey_height_m'], 3.6)

    def test_missing_own_storey_uses_site_default_and_preserves_explicit_base(self):
        record = {'name': 'fallback', 'ops': [{'op': 'extrude', 'storeys': 2, 'height': .4}]}
        site = SimpleNamespace(floor_height_m=3.8)
        for base in (15.2, 24.):
            with self.subTest(base=base), patch('finalists.execute_parti', return_value=None) as execute:
                rebuild_seat('fallback', {'fallback': record}, site, box(0, 0, 50, 50), (1, 0), base)
                self.assertAlmostEqual(execute.call_args.kwargs['height_m'], max(base, 19.))

    def test_rebuilt_siting_is_preserved_when_the_legal_fitter_receives_it(self):
        from finalists import rebuild
        record = {'name': 'held', 'floor_height_m': 3.6,
                  'ops': [{'op': 'extrude', 'storeys': 2, 'height': .4}]}
        site = SimpleNamespace(floor_height_m=3.8, ground_capacity_m2=1497.877,
                               far_capacity_m2=6241.962, shared_edges=(),
                               plan_at=lambda z: box(0, 0, 50, 50))
        with patch('finalists.fill_to_site', return_value=SimpleNamespace(
                fit=SimpleNamespace(satisfied=False))) as fill:
            rebuild('held^centred', {'held': record}, site, box(0, 0, 50, 50), (1, 0), 15.2)
        self.assertEqual(fill.call_args.args[0].extra.get('siting'), 'centred',
                         'Without this marker the fitter seats the already-sited candidate again')

    def test_development_does_not_reinflate_own_storeys_before_rebuild(self):
        import develop
        record = {'name': 'five', 'floor_height_m': 3.6,
                  'ops': [{'op': 'extrude', 'storeys': 5, 'height': 1.0}]}
        site = SimpleNamespace(floor_height_m=3.8, ground_capacity_m2=1497.877,
                               far_capacity_m2=6241.962, shared_edges=(),
                               plan_at=lambda z: box(0, 0, 50, 50))
        with TemporaryDirectory() as folder, patch('develop.corpus', return_value={'five': record}), \
                patch('develop.schedule_of', return_value=None), \
                patch('develop.load_legal_site', return_value=site), \
                patch('finalists.execute_parti', return_value=None) as execute, \
                patch('develop.ROOT', Path(folder)):
            run = Path(folder) / 'runs' / 'fixture'
            run.mkdir(parents=True)
            (run / 'massv2-summary.json').write_text(json.dumps({'site': {'parcel_area_m2':2500}}), encoding='utf8')
            # Stop at execution, before any mutations or pair images are made.
            self.assertEqual(develop.main('fixture', 'five', output_dir=Path(folder) / 'develop'), 1)
            self.assertEqual(execute.call_args.kwargs['height_m'], 18.)
