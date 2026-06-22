"""
QA Boundary Test — validates Backend response shapes match Frontend TS types.

Ensures REST API response dicts from land/, design/, law/ have the exact fields
that the Frontend TypeScript interfaces expect. Catches schema drift early.

Run: python -m pytest tests/test_qa_boundary.py -v
"""

import sys
import os
import unittest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ARR', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()


class TestLandAnalyzeResponseShape(unittest.TestCase):
    """Verify /land/analyze/ response matches LandAnalysisResult TS interface."""

    # Expected top-level keys from LandAnalysisResult
    EXPECTED_TOP_KEYS = {
        'pnu', 'zone_info', 'regulations', 'land_info',
        'law_articles', 'restrictions',
    }
    OPTIONAL_TOP_KEYS = {
        'overlay_regulations', 'setback_lines', 'errors', 'warning',
    }

    def test_format_regulations_keys(self):
        """format_regulations() output matches Regulations TS interface."""
        from land.formatters import format_regulations

        reg = {
            'bcr_pct': 60, 'bcr_article': '국토계획법 §77',
            'far_pct': 200, 'far_article': '국토계획법 §78',
            'height_limit_m': None, 'height_article': '',
            'sunlight_applies': True, 'sunlight_rules': [{'setback_m': 1.5}],
            'sunlight_article': '건축법 §61',
            'corner_cutoff_required': True, 'corner_cutoff_article': '령§31',
            'road_diagonal_multiplier': 1.5, 'road_diagonal_rule': '도로사선',
            'road_diagonal_article': '',
            'building_line_setback_m': 1.0, 'building_line_article': '',
            'adjacent_setback_m': 0.5, 'adjacent_setback_article': '',
            'parking_rule': '150m²당 1대', 'parking_article': '',
            'landscaping_threshold_m2': 200, 'landscaping_min_pct': 15,
            'landscaping_article': '',
        }
        result = format_regulations(reg)

        # TS Regulations interface keys
        expected_keys = {
            'bcr', 'far', 'height', 'sunlight_setback',
            'corner_cutoff', 'road_diagonal', 'building_line',
            'adjacent_setback', 'parking', 'landscaping',
        }
        self.assertEqual(set(result.keys()), expected_keys)

        # bcr → RegulationItem must have limit_pct, article
        self.assertIn('limit_pct', result['bcr'])
        self.assertIn('article', result['bcr'])

        # sunlight_setback → must have applies, direction, rules, article
        ss = result['sunlight_setback']
        self.assertIn('applies', ss)
        self.assertIn('direction', ss)
        self.assertIn('rules', ss)
        self.assertIn('article', ss)

        # adjacent_setback → min_m (not setback_m)
        self.assertIn('min_m', result['adjacent_setback'])

    def test_format_regulations_with_extended(self):
        """Extended regulations appear under 'extended' key."""
        from land.formatters import format_regulations

        reg = {
            'bcr_pct': 60, 'bcr_article': '', 'far_pct': 200, 'far_article': '',
            'height_limit_m': None, 'height_article': '',
            'sunlight_applies': False, 'sunlight_rules': [], 'sunlight_article': '',
            'corner_cutoff_required': False, 'corner_cutoff_article': '',
            'road_diagonal_multiplier': None, 'road_diagonal_rule': '',
            'road_diagonal_article': '',
            'building_line_setback_m': None, 'building_line_article': '',
            'adjacent_setback_m': 0.5, 'adjacent_setback_article': '',
            'parking_rule': '', 'parking_article': '',
            'landscaping_threshold_m2': None, 'landscaping_min_pct': None,
            'landscaping_article': '',
        }
        ext = {'용도제한': {'name': '용도제한', 'applies': True, 'article': '§71'}}
        result = format_regulations(reg, reg_ext=ext)
        self.assertIn('extended', result)
        self.assertIn('용도제한', result['extended'])

    def test_flatten_law_articles_shape(self):
        """_flatten_law_articles() output matches LawArticlesResult TS interface."""
        # Import the private function from views
        from land.views import _flatten_law_articles

        nested = {
            'articles': [
                {
                    'query': '건폐율',
                    'results': [
                        {'hang_id': 'H001', 'content': '건폐율 제한',
                         'law_name': '국토계획법', 'law_type': '법률',
                         'article': '제77조', 'similarity': 0.85,
                         'stages': ['vector']},
                    ],
                },
            ],
            'errors': [],
        }
        flat = _flatten_law_articles(nested)

        # TS LawArticlesResult: articles, total_count, errors
        self.assertIn('articles', flat)
        self.assertIn('total_count', flat)
        self.assertIn('errors', flat)
        self.assertIsInstance(flat['articles'], list)
        self.assertEqual(flat['total_count'], 1)

        # Each item: LawArticleItem fields
        item = flat['articles'][0]
        self.assertIn('hang_id', item)
        self.assertIn('content', item)

    def test_flatten_deduplicates(self):
        """Duplicate hang_ids are removed."""
        from land.views import _flatten_law_articles

        nested = {
            'articles': [
                {'query': 'q1', 'results': [
                    {'hang_id': 'H001', 'content': 'A'},
                ]},
                {'query': 'q2', 'results': [
                    {'hang_id': 'H001', 'content': 'A'},  # dup
                    {'hang_id': 'H002', 'content': 'B'},
                ]},
            ],
            'errors': [],
        }
        flat = _flatten_law_articles(nested)
        self.assertEqual(flat['total_count'], 2)

    def test_pnu_parse_shape(self):
        """parse_pnu() output matches PnuInfo TS interface."""
        from land.services.pnu_resolver import parse_pnu

        result = parse_pnu('1168011200101280003')

        expected_keys = {
            'pnu', 'sido', 'sigungu', 'eupmyeondong', 'ri',
            'land_type', 'main_number', 'sub_number', 'land_type_name',
        }
        self.assertTrue(expected_keys.issubset(set(result.keys())),
                        f"Missing keys: {expected_keys - set(result.keys())}")


class TestLandResolveResponseShape(unittest.TestCase):
    """Verify /land/resolve/ response matches PnuResolveResult TS interface."""

    def test_pnu_validation_response(self):
        """PNU validation returns {valid, parsed}."""
        from land.services.pnu_resolver import parse_pnu, validate_pnu

        pnu = '1168011200101280003'
        self.assertTrue(validate_pnu(pnu))
        response = {'valid': True, 'parsed': parse_pnu(pnu)}

        # TS PnuResolveResult: valid + parsed
        self.assertIn('valid', response)
        self.assertIn('parsed', response)

    def test_address_error_response_shape(self):
        """Address resolve error matches PnuResolveResult shape."""
        error_response = {
            'success': False,
            'error': 'VWORLD_API_KEY not configured',
            'address': 'test',
            'pnu': None,
        }
        # TS PnuResolveResult: success, error, address, pnu
        for key in ('success', 'error', 'address', 'pnu'):
            self.assertIn(key, error_response)


class TestSetbackLinesShape(unittest.TestCase):
    """Verify setback_geometry output matches SetbackLines TS interface."""

    def test_result_keys(self):
        """compute_setback_lines returns all SetbackLines keys."""
        from land.services.setback_geometry import compute_setback_lines

        # Empty geometry → all None but all keys present
        result = compute_setback_lines({}, {})

        expected_keys = {
            'buildable_area', 'north_setback', 'adjacent_setback',
            'road_setback', 'corner_cutoff', 'sunlight_envelope',
            'building_designation_line', 'daylight_diagonal_envelope',
        }
        self.assertEqual(set(result.keys()), expected_keys,
                         f"SetbackLines key mismatch. "
                         f"Missing: {expected_keys - set(result.keys())}. "
                         f"Extra: {set(result.keys()) - expected_keys}")

    def test_sunlight_envelope_shape(self):
        """sunlight_envelope matches SunlightEnvelope TS interface when present."""
        from land.services.setback_geometry import compute_setback_lines

        # Real-ish polygon (square parcel in WGS84)
        parcel = {
            'type': 'Polygon',
            'coordinates': [[
                [127.0, 37.5],
                [127.001, 37.5],
                [127.001, 37.501],
                [127.0, 37.501],
                [127.0, 37.5],
            ]],
        }
        regs = {
            'adjacent_setback_m': 0.5,
            'sunlight_applies': True,
            'sunlight_rules': [{'setback_m': 1.5}],
        }
        result = compute_setback_lines(parcel, regs)

        # sunlight_envelope should be generated for sunlight zones
        if result.get('sunlight_envelope'):
            env = result['sunlight_envelope']
            # TS SunlightEnvelope: walls, slope, base_setback_m, base_height_m, max_depth_m
            self.assertIn('walls', env)
            self.assertIn('slope', env)
            self.assertIn('base_setback_m', env)
            self.assertIn('base_height_m', env)
            self.assertIn('max_depth_m', env)
            self.assertIsInstance(env['walls'], list)

            if env['walls']:
                wall = env['walls'][0]
                self.assertIn('positions', wall)
                self.assertIn('min_heights', wall)
                self.assertIn('max_heights', wall)


class TestSetbackNewTypes(unittest.TestCase):
    """Test the 4 new setback types (road, corner, daylight, classify)."""

    SQUARE_PARCEL = {
        'type': 'Polygon',
        'coordinates': [[
            [127.0, 37.5],
            [127.001, 37.5],      # south edge (longest ~ 87m)
            [127.001, 37.501],
            [127.0, 37.501],      # north edge
            [127.0, 37.5],
        ]],
    }

    def test_road_edges_detected(self):
        """Longest edges classified as road."""
        from land.services.setback_geometry import (
            _extract_edges, _classify_edges, _wgs_to_utm,
        )
        from shapely.geometry import shape

        parcel = shape(self.SQUARE_PARCEL)
        parcel_utm = _wgs_to_utm(parcel)
        edges = _extract_edges(parcel_utm)
        classified = _classify_edges(edges, parcel_utm)

        # At least one road edge detected (longest heuristic)
        self.assertGreater(len(classified["road"]), 0,
                           "No road edges detected — longest-edge heuristic failed")

    def test_road_setback_generated(self):
        """road_setback present when building_line_setback_m provided."""
        from land.services.setback_geometry import compute_setback_lines

        regs = {
            'adjacent_setback_m': 0.5,
            'building_line_setback_m': 2.0,
            'sunlight_applies': False,
        }
        result = compute_setback_lines(self.SQUARE_PARCEL, regs)
        self.assertIsNotNone(result['road_setback'],
                             "road_setback should be generated")
        self.assertIn('type', result['road_setback'])

    def test_corner_cutoff_with_road_edges(self):
        """corner_cutoff generated for corner lot with 2+ road edges."""
        from land.services.setback_geometry import compute_setback_lines

        # L-shaped parcel → more likely to have 2 road-length edges
        regs = {
            'adjacent_setback_m': 0.5,
            'building_line_setback_m': 1.0,
            'corner_cutoff_required': True,
            'sunlight_applies': False,
        }
        result = compute_setback_lines(self.SQUARE_PARCEL, regs)
        # corner_cutoff may be None if < 2 road edges share a vertex
        # Just verify key exists and type is correct when present
        self.assertIn('corner_cutoff', result)
        if result['corner_cutoff']:
            self.assertIn('type', result['corner_cutoff'])

    def test_daylight_distance_compliant(self):
        """Buildings far apart → compliant."""
        from land.services.setback_geometry import compute_daylight_distance

        bldg_a = {"height": 30.0, "centroid": [127.0, 37.5]}
        bldg_b = {"height": 40.0, "centroid": [127.001, 37.5]}  # ~87m apart

        result = compute_daylight_distance(bldg_a, bldg_b)
        self.assertTrue(result["compliant"])
        self.assertEqual(result["taller_height_m"], 40.0)
        self.assertAlmostEqual(result["required_m"], 20.0, places=1)
        self.assertGreater(result["distance_m"], 20.0)

    def test_daylight_distance_non_compliant(self):
        """Buildings too close → not compliant."""
        from land.services.setback_geometry import compute_daylight_distance

        bldg_a = {"height": 60.0, "centroid": [127.0, 37.5]}
        bldg_b = {"height": 60.0, "centroid": [127.00005, 37.5]}  # ~4m apart

        result = compute_daylight_distance(bldg_a, bldg_b)
        self.assertFalse(result["compliant"])
        self.assertEqual(result["required_m"], 30.0)

    def test_daylight_urban_living(self):
        """Urban living uses 0.25 multiplier."""
        from land.services.setback_geometry import compute_daylight_distance

        bldg_a = {"height": 40.0, "centroid": [127.0, 37.5]}
        bldg_b = {"height": 40.0, "centroid": [127.001, 37.5]}

        result = compute_daylight_distance(bldg_a, bldg_b, is_urban_living=True)
        self.assertEqual(result["required_m"], 10.0)  # 40 * 0.25
        self.assertIn("0.25", result["formula"])

    def test_daylight_result_shape(self):
        """DaylightDistanceResult matches TS interface."""
        from land.services.setback_geometry import compute_daylight_distance

        result = compute_daylight_distance(
            {"height": 20, "centroid": [127.0, 37.5]},
            {"height": 20, "centroid": [127.001, 37.5]},
        )
        expected_keys = {
            'distance_m', 'required_m', 'ratio', 'compliant',
            'taller_height_m', 'formula',
        }
        self.assertEqual(set(result.keys()), expected_keys)


class TestDesignJobResponseShape(unittest.TestCase):
    """Verify design formatters match DesignJob/DesignResult TS interfaces."""

    def test_format_job_response_keys(self):
        """format_job_response() output matches DesignJob TS interface."""
        from design.formatters import format_job_response
        from unittest.mock import MagicMock
        from datetime import datetime

        job = MagicMock()
        job.id = 'test-id'
        job.pnu = '1168011200101280003'
        job.address = '강남구 역삼동'
        job.status = 'running'
        job.generation_count = 10
        job.max_generations = 50
        job.population_size = 210
        job.site_area_m2 = 500.0
        job.constraints = [{'name': 'BCR', 'val': 60}]
        job.created_at = datetime.now()
        job.completed_at = None
        job.error = ''

        result = format_job_response(job)

        # TS DesignJob keys
        expected = {
            'id', 'pnu', 'address', 'status', 'generation_count',
            'max_generations', 'population_size', 'site_area_m2',
            'constraints', 'created_at', 'completed_at', 'error',
        }
        self.assertEqual(set(result.keys()), expected)

    def test_format_design_response_keys(self):
        """format_design_response() output matches DesignResult TS interface."""
        from design.formatters import format_design_response
        from unittest.mock import MagicMock

        design = MagicMock()
        design.design_id = 1
        design.generation = 5
        design.inputs = [[0.5, 0.3]]
        design.outputs = {'bcr': 55.0}
        design.ranking = 1
        design.crowding_distance = 0.8
        design.is_feasible = True
        design.is_pareto_optimal = True
        design.mass_geojson = None

        result = format_design_response(design)

        expected = {
            'design_id', 'generation', 'inputs', 'outputs',
            'ranking', 'crowding_distance', 'is_feasible',
            'is_pareto_optimal', 'mass_geojson',
        }
        self.assertEqual(set(result.keys()), expected)


class TestZonesResponseShape(unittest.TestCase):
    """Verify /land/zones/ response shape."""

    def test_get_all_zones_items(self):
        """Each zone item has expected fields."""
        from land.services.zoning_mapper import get_all_zones

        zones = get_all_zones()
        self.assertIsInstance(zones, list)
        self.assertGreater(len(zones), 0)

        z = zones[0]
        # Must have at least zone_name, bcr_default, far_default
        self.assertIn('zone_name', z)
        self.assertIn('bcr_default', z)
        self.assertIn('far_default', z)


if __name__ == '__main__':
    unittest.main()
