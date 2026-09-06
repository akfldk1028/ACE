"""A low courtyard can ask to grow in plan without acquiring extra floors."""
import json
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from shapely.geometry import box, Polygon

from design.maas.massv2.grammar import parti_from_record, declared_height_m, declared_stature
from design.maas.massv2.execute import execute
from design.maas.massv2.variations import spread_across_coverage, retarget_ground_take
from design.maas.massv2.fill import fill_to_site
from design.maas.massv2.compile import compile_matrix_form
from design.maas.massv2.legal import LegalSite


def site():
    return LegalSite('growth-fixture', box(0, 0, 50, 50), (0, 0),
        SimpleNamespace(envelope=SimpleNamespace(floor_height=3.6)),
        {'bcr_footprint_capacity_m2': 1499, 'statutory_far_capacity_m2': 6240})


def record(**extra):
    return dict(name='low_court', primary_language='open_figure',
                secondary_language='court', formal_principle='Low court',
                dominant_gesture='court', reference_basis='authored',
                floor_height_m=3.6, ops=[dict(op='loop', storeys=3, height=.52,
                                             bar=.2, why='Three storey court')], **extra)


def built(rec):
    form = execute(parti_from_record(rec), buildable=box(0, 0, 30, 30),
                   axis=(1, 0), height_m=declared_height_m(rec, 3.6), storey_height_m=3.6)
    return replace(form, extra={**form.extra, **declared_stature(rec)})


class AuthoredGrowthTests(SimpleTestCase):
    def test_plan_growth_survives_parser_and_executor(self):
        rec = record(growth='plan')
        self.assertEqual(parti_from_record(rec).evidence().get('growth'), 'plan')
        self.assertEqual(built(rec).extra['growth'], 'plan')

    def test_top_level_enum_refuses_typos_and_non_strings(self):
        for value in ('height', 'PLAN', '', None, 1, []):
            with self.subTest(value=value):
                self.assertIsNone(parti_from_record(record(growth=value)))
        self.assertIsNotNone(parti_from_record(record(growth='both')))

    def test_validator_reports_the_same_invalid_policy(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tmp_mass_check/_massv2/tools'))
        from validate_authored import check
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'payload.json'
            path.write_text(json.dumps({'schemes': [record(growth='height')]}), encoding='utf8')
            faults, _, _ = check(path)
        self.assertTrue(any('growth' in fault for fault in faults), faults)

    def test_all_coverage_matrices_and_delivered_sources_keep_three_storey_height(self):
        form = built(record(growth='plan'))
        controlled = site()
        variants = [form] + spread_across_coverage(form,
            ground_capacity_m2=controlled.ground_capacity_m2,
            far_capacity_m2=controlled.far_capacity_m2, floor_height_m=3.6)
        self.assertGreater(len(variants), 1)
        originals = form.placements
        with patch.object(LegalSite, 'plan_at', return_value=box(0, 0, 50, 50)):
            for variant in variants:
                with self.subTest(variant=variant.name):
                    for placement, original in zip(variant.placements, originals):
                        self.assertEqual(len(placement.matrix), 4)
                        self.assertEqual(placement.matrix[2], original.matrix[2])
                        self.assertAlmostEqual(placement.z_span()[1], 10.8)
                    result = fill_to_site(variant, controlled)
                    self.assertTrue(result.fit.satisfied)
                    self.assertEqual(result.grew_height, 0)
                    source = compile_matrix_form(result.fit.form, storey_height_m=3.6,
                                                 allowed_at=controlled.plan_at)
                    self.assertIsNotNone(source)
                    self.assertLessEqual(source.metadata['authored_height_m'], 10.8 + 1e-6)

    def test_unspecified_and_explicit_both_keep_existing_upward_growth(self):
        for rec in (record(), record(growth='both')):
            form = built(rec)
            self.assertEqual(form.extra['growth'], 'both')
            with patch.object(LegalSite, 'plan_at', return_value=box(0, 0, 50, 50)):
                result = fill_to_site(form, site())
            self.assertGreater(max(p.z_span()[1] for p in result.fit.form.additive()), 10.8)

    def test_smaller_footprint_cannot_buy_extra_height_under_explicit_plan_policy(self):
        for rec, expected in ((record(growth='plan'), 10.8), (record(), 21.6)):
            form = built(rec)
            moved = retarget_ground_take(form, target_area_m2=288,
                                         far_capacity_m2=6240, floor_height_m=3.6)
            self.assertAlmostEqual(max(p.z_span()[1] for p in moved.additive()), expected)

    def test_unspecified_aggregate_keeps_legacy_inferred_growth_and_coverage(self):
        rec = record()
        rec['ops'] = [dict(op='aggregate', n=4, method='pack', height=.52, storeys=3)]
        form = built(rec)
        self.assertEqual(form.extra['growth'], 'plan')
        self.assertNotIn('growth', form.extra['parti'])
        from design.maas.massv2.legal_fit import projected_ground_area
        moved = retarget_ground_take(form, target_area_m2=projected_ground_area(form) / 2,
                                     far_capacity_m2=6240, floor_height_m=3.6)
        self.assertGreater(max(p.z_span()[1] for p in moved.additive()),
                           max(p.z_span()[1] for p in form.additive()))

    def test_plan_policy_still_allows_the_legal_envelope_to_reduce_height(self):
        controlled = site()
        def allowed(z):
            return box(0, 0, 50, 50) if z <= 7.2 else Polygon()
        with patch.object(LegalSite, 'plan_at', side_effect=allowed):
            result = fill_to_site(built(record(growth='plan')), controlled)
            self.assertTrue(result.fit.satisfied)
            source = compile_matrix_form(result.fit.form, storey_height_m=3.6,
                                         allowed_at=controlled.plan_at)
        occupied_top = max(v.top_fraction * source.metadata['authored_height_m']
                           for v in source.volumes)
        self.assertLessEqual(occupied_top, 7.2 + 1e-6)
