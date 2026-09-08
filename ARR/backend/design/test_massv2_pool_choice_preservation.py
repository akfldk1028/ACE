"""The browsing output preserves different 3D choices, even on identical plans."""
import importlib.util
import json
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from shapely.geometry import box
from design.test_maas_book_delivered_areas import book_import

spec = importlib.util.spec_from_file_location('pool_choice_tool',
    Path(book_import.__file__).with_name('pool_sheets.py'))
pool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pool)


class PoolChoiceTests(TestCase):
    def test_same_plan_different_roof_and_siting_survive_but_exact_alias_is_logged(self):
        names = ['roof~band^one', 'roof~band^two', 'alias~band']
        sources = {name: SimpleNamespace(identity=identity, volumes=[SimpleNamespace(
            footprint=box(0, 0, 20, 10), bottom_fraction=0)])
            for name, identity in zip(names, ['flat', 'dome', 'flat'])}
        site = SimpleNamespace(floor_height_m=3, far_capacity_m2=3000,
            ground_capacity_m2=1000, plan_at=lambda _: box(0, 0, 50, 50))
        with TemporaryDirectory() as tmp, ExitStack() as stack:
            root = Path(tmp)
            (root / 'runs/test').mkdir(parents=True)
            records = [dict(name=n, plausibility={'occupiable': True},
                legal_fit={'ground_area_m2': 200, 'gross_floor_area_m2': 600}) for n in names]
            (root / 'runs/test/massv2-summary.json').write_text(json.dumps(
                {'site': {'parcel_area_m2': 2500}, 'records': records}))
            for attr, value in [('ROOT', root), ('corpus', lambda: {'roof': {'ops': []}, 'alias': {'ops': []}}),
                    ('schedule_of', lambda _: None), ('load_legal_site', lambda *a, **k: site),
                    ('site_open_side_direction', lambda _: (1, 0)),
                    ('rebuild', lambda name, *a, **k: sources[name]), ('render_masses', lambda *a, **k: None)]:
                stack.enter_context(patch.object(pool, attr, value))
            stack.enter_context(patch('vlm_shortlist.shape_id', lambda source: source.identity))
            pool.main('test')
            rows = json.loads((root / 'runs/pool-test/pool-index.json').read_text())
            self.assertEqual({r['shape_id'] for r in rows}, {'flat', 'dome'})
            self.assertEqual(len(rows), 2)
            self.assertTrue(any(r['similar_plan_to'] for r in rows))
            removed = json.loads((root / 'runs/pool-test/pool-suppressed.json').read_text())
            self.assertEqual(len(removed), 1)
            self.assertEqual(removed[0]['shape_id'], 'flat')
