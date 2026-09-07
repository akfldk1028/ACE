"""Exact development may move a raised bridge, but must never resize it."""
from types import SimpleNamespace
from unittest import TestCase

from shapely.geometry import box

from design.maas.book_development import MODE, build_exact_development_portfolio
from design.maas.geometry_language.dsl import parse_geometry_dsl
from design.test_maas_book_delivered_areas import book_import


def exact_bridge_record():
    # Ground: two 6 x 12 supports = 144 m2. Upper bridge: 24 x 12 = 288 m2.
    # Three occupied floors: 144 + 288 + 288 = 720 m2, total height 9 m.
    program = parse_geometry_dsl(
        'result = union(box(6,12,3), translate(box(6,12,3), vector=[18,0,0]), '
        'translate(box(24,12,6), vector=[0,0,3]))')
    context = dict(parent='bridge', parent_shape_id='verified-shape',
        parent_program_hash='verified-program', parent_certificate_id='verified-certificate',
        site_pnu='unregistered-unit-fixture', storey_count=3, storey_height_m=3.,
        height_m=9., target_gfa_m2=720.)
    payload = dict(mode=MODE, inherit_parent_dimensions=True,
        **{key: context[key] for key in ('parent', 'parent_shape_id', 'parent_program_hash')},
        geometry_programs=[program.to_dict()])
    candidate = build_exact_development_portfolio(payload, context, expected_count=1)['candidates'][0]
    return {'trace_sequence_name': 'unchanged-exact-bridge', 'geometry_artifact': {
        'authoredGeometryProgram': candidate['geometry_program'],
        'storeyEvidence': candidate['storey_evidence'],
        'projectedVisualCertificate': {'physical_height_m': 9.},
        'hardGates': {'projectedMetrics': {'footprint_area_m2': 144., 'floor_area_m2': 720.}}}}


class ExactBookImportTests(TestCase):
    def setUp(self):
        self.site = SimpleNamespace(pnu='unregistered-unit-fixture', ground_capacity_m2=1500,
            far_capacity_m2=6000, floor_height_m=3., parcel_area_m2=2500)

    def test_unchanged_raised_bridge_keeps_all_floor_areas_and_metric_dimensions(self):
        source, entry = book_import._compile_record(exact_bridge_record(), box(0, 0, 50, 50), self.site)
        self.assertIsNotNone(source, entry)
        self.assertAlmostEqual(entry['floor_area_m2'], 720., places=3)
        self.assertAlmostEqual(entry['footprint_m2'], 288., places=3)
        self.assertEqual(entry['height_m'], 9.)
        floors = entry['delivered_floor_evidence']
        for actual, expected in zip(floors['actual_floor_areas_m2'], (144., 288., 288.)):
            self.assertAlmostEqual(actual, expected, places=3)
        matrix = floors['normalized_host_fit_matrix4']
        for column in (0, 1):
            self.assertAlmostEqual(sum(matrix[row][column] ** 2 for row in (0, 1)), 1., places=8)
        self.assertAlmostEqual(floors['z_scale'], 1., places=8)

    def test_exact_bridge_that_cannot_fit_is_refused_instead_of_shrunk(self):
        source, reason = book_import._compile_record(exact_bridge_record(), box(0, 0, 18, 18), self.site)
        self.assertTrue(source is None, 'Nonfitting exact development must be refused, not resized')
        self.assertIn('without resizing', reason)

    def test_exact_preservation_does_not_bypass_area_gate(self):
        self.site.far_capacity_m2 = 700.
        source, reason = book_import._compile_record(exact_bridge_record(), box(0, 0, 50, 50), self.site)
        self.assertTrue(source is None, 'Exact delivery must not evade the area gate by shrinking')
        self.assertIn('parcel area gate', reason)
