"""Counterfactual dependency loss is not a malformed authored shape."""
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box

from design.maas.massv2.ablation import _delivered, ablate
from design.maas.massv2.execute import execute
from design.maas.massv2.grammar import parti_from_record


class AblationDependencyTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        path = Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/inputs/gen-comp01.json'
        cls.records = json.loads(path.read_text(encoding='utf8'))['schemes']

    def setUp(self):
        self.kw = dict(buildable=box(0, 0, 50, 50), axis=(1, 0), height_m=18,
                       storey_height_m=3.6)
        self.site = SimpleNamespace(plan_at=lambda z: box(-100, -100, 100, 100))
        # This contract is about executor dependencies. Avoid external legal
        # services and growth; keep actual execution, source compile and delta.
        self.fill = patch('design.maas.massv2.ablation.fill_to_site',
                          side_effect=lambda form, site: SimpleNamespace(fit=SimpleNamespace(form=form)))
        self.fill.start()
        self.addCleanup(self.fill.stop)

    def test_actual_ten_inputs_opener_ablation_does_not_abort(self):
        self.assertEqual(len(self.records), 10)
        for record in self.records:
            with self.subTest(record=record['name']):
                parti = parti_from_record(record)
                shorter = replace(parti, ops=parti.ops[1:])
                without = _delivered(shorter, site=self.site,
                                     allow_missing_dependency=True, **self.kw)
                self.assertIsNone(without)

    def test_actual_body_and_tier_shape_dependencies_get_full_contribution(self):
        records = [r for r in self.records if any(o['op'] == 'shape' for o in r['ops'])]
        self.assertEqual({r['ops'][1]['on'] for r in records}, {'body', 'tier_1'})
        for record in records:
            with self.subTest(record=record['name']):
                result = ablate(parti_from_record(record), site=self.site, **self.kw)
                self.assertEqual(result.removed_share[0], 1)
                self.assertNotIn(result.declared[0], result.idle)

    def test_missing_dependency_is_still_an_error_outside_counterfactual(self):
        from design.maas.massv2.execute import MissingOperationDependency
        parti = parti_from_record(self.records[-1])
        shorter = replace(parti, ops=parti.ops[1:])
        with self.assertRaises(MissingOperationDependency):
            execute(shorter, **self.kw)
        with self.assertRaises(MissingOperationDependency):
            ablate(shorter, site=self.site, **self.kw)

    def test_malformed_shape_payload_is_not_swallowed(self):
        parti = parti_from_record(self.records[-1])
        bad = replace(parti.ops[-1], params={'on': 'tier_1',
                                            'top_surface': {'type': 'not-a-surface'}})
        malformed = replace(parti, ops=(*parti.ops[:-1], bad))
        with self.assertRaises(ValueError):
            _delivered(malformed, site=self.site, allow_missing_dependency=True, **self.kw)
        with self.assertRaises(ValueError):
            ablate(malformed, site=self.site, **self.kw)
