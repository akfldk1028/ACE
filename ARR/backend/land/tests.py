"""Tests for land regulation analysis app v2."""

import json

from django.test import TestCase, Client


# ──────────────────────────────────────────────────────
# Zoning Mapper Tests (unchanged)
# ──────────────────────────────────────────────────────
class ZoningMapperTest(TestCase):
    """Test static zoning data loading and lookup."""

    def test_load_all_zones(self):
        from land.services import zoning_mapper
        zones = zoning_mapper.get_all_zones()
        self.assertEqual(len(zones), 21)

    def test_lookup_exact(self):
        from land.services import zoning_mapper
        zone = zoning_mapper.lookup("제1종일반주거지역")
        self.assertIsNotNone(zone)
        self.assertEqual(zone["bcr_default"], 60)
        self.assertEqual(zone["far_default"], 200)

    def test_lookup_exact_only(self):
        from land.services import zoning_mapper
        zone = zoning_mapper.lookup("일반상업")
        self.assertIsNone(zone)

    def test_lookup_missing(self):
        from land.services import zoning_mapper
        zone = zoning_mapper.lookup("존재하지않는지역")
        self.assertIsNone(zone)

    def test_resolve_limits_single(self):
        from land.services import zoning_mapper
        result = zoning_mapper.resolve_limits(["제1종일반주거지역"])
        self.assertEqual(result["bcr_limit"], 60)
        self.assertEqual(result["far_limit"], 200)
        self.assertEqual(result["matched"], 1)

    def test_resolve_limits_multiple_strictest(self):
        from land.services import zoning_mapper
        result = zoning_mapper.resolve_limits(["제1종일반주거지역", "보전녹지지역"])
        self.assertEqual(result["bcr_limit"], 20)
        self.assertEqual(result["far_limit"], 80)
        self.assertEqual(result["matched"], 2)

    def test_resolve_limits_unmatched(self):
        from land.services import zoning_mapper
        result = zoning_mapper.resolve_limits(["없는지역"])
        self.assertIsNone(result["bcr_limit"])
        self.assertEqual(result["unmatched"], ["없는지역"])

    def test_new_zones_exist(self):
        from land.services import zoning_mapper
        for name in ["농림지역", "자연환경보전지역", "보전관리지역", "생산관리지역", "계획관리지역"]:
            self.assertIsNotNone(zoning_mapper.lookup(name), f"Missing zone: {name}")

    def test_zone_has_extended_fields(self):
        """All zones have new regulation fields."""
        from land.services import zoning_mapper
        zone = zoning_mapper.lookup("제1종일반주거지역")
        for field in ("sunlight_setback", "road_diagonal", "corner_cutoff",
                      "adjacent_setback_m", "landscaping", "parking_article",
                      "height_limit_article", "building_line_article"):
            self.assertIn(field, zone, f"Missing field: {field}")


# ──────────────────────────────────────────────────────
# PNU Resolver Tests (unchanged)
# ──────────────────────────────────────────────────────
class PnuResolverTest(TestCase):

    def test_valid_pnu(self):
        from land.services import pnu_resolver
        self.assertTrue(pnu_resolver.validate_pnu("1168011200101280003"))

    def test_invalid_pnu_short(self):
        from land.services import pnu_resolver
        self.assertFalse(pnu_resolver.validate_pnu("123"))

    def test_invalid_pnu_letters(self):
        from land.services import pnu_resolver
        self.assertFalse(pnu_resolver.validate_pnu("116801120010128000a"))

    def test_parse_pnu(self):
        from land.services import pnu_resolver
        result = pnu_resolver.parse_pnu("1168011200101280003")
        self.assertIsNotNone(result)
        self.assertEqual(result["sido"], "11")
        self.assertEqual(result["sigungu"], "680")
        self.assertEqual(result["land_type"], "1")


# ──────────────────────────────────────────────────────
# Regulation Calculator Tests (NEW)
# ──────────────────────────────────────────────────────
class RegulationCalculatorTest(TestCase):
    """Test all 10 regulation calculations."""

    def test_single_residential_zone(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역"])
        self.assertEqual(reg["bcr_pct"], 60)
        self.assertEqual(reg["far_pct"], 200)
        self.assertTrue(reg["sunlight_applies"])
        self.assertEqual(reg["road_diagonal_multiplier"], 1.0)
        self.assertTrue(reg["corner_cutoff_required"])
        self.assertEqual(reg["adjacent_setback_m"], 0.5)
        self.assertEqual(reg["landscaping_min_pct"], 15)
        self.assertEqual(reg["zone_category"], "주거지역")

    def test_single_commercial_zone(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["중심상업지역"])
        self.assertEqual(reg["bcr_pct"], 90)
        self.assertEqual(reg["far_pct"], 1500)
        self.assertFalse(reg["sunlight_applies"])
        self.assertEqual(reg["road_diagonal_multiplier"], 1.5)
        self.assertEqual(reg["landscaping_min_pct"], 10)

    def test_single_green_zone(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["보전녹지지역"])
        self.assertEqual(reg["bcr_pct"], 20)
        self.assertEqual(reg["far_pct"], 80)
        self.assertFalse(reg["sunlight_applies"])
        self.assertEqual(reg["landscaping_min_pct"], 20)

    def test_multiple_zones_strictest_bcr_far(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역", "보전녹지지역"])
        self.assertEqual(reg["bcr_pct"], 20)
        self.assertEqual(reg["far_pct"], 80)

    def test_multiple_zones_sunlight_applies_if_any(self):
        """Sunlight applies if any zone requires it."""
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역", "중심상업지역"])
        self.assertTrue(reg["sunlight_applies"])

    def test_multiple_zones_strictest_road_diagonal(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역", "중심상업지역"])
        self.assertEqual(reg["road_diagonal_multiplier"], 1.0)

    def test_multiple_zones_strictest_landscaping(self):
        """Use highest landscaping percentage."""
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["중심상업지역", "보전녹지지역"])
        self.assertEqual(reg["landscaping_min_pct"], 20)

    def test_multiple_zones_strictest_adjacent_setback(self):
        """Use largest adjacent setback."""
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역", "중심상업지역"])
        self.assertEqual(reg["adjacent_setback_m"], 0.5)

    def test_unmatched_zones(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역", "존재하지않는지역"])
        self.assertEqual(reg["bcr_pct"], 60)
        self.assertIn("존재하지않는지역", reg["unmatched_zones"])

    def test_all_unmatched_returns_empty(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["없는지역"])
        self.assertIsNone(reg["bcr_pct"])
        self.assertFalse(reg["sunlight_applies"])
        self.assertEqual(reg["matched_zones"], [])

    def test_sunlight_rules_structure(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역"])
        self.assertIsInstance(reg["sunlight_rules"], list)
        self.assertGreater(len(reg["sunlight_rules"]), 0)
        self.assertIn("condition", reg["sunlight_rules"][0])

    def test_articles_populated(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역"])
        self.assertIn("국토계획법", reg["bcr_article"])
        self.assertIn("국토계획법", reg["far_article"])
        self.assertIn("건축법", reg["sunlight_article"])
        self.assertIn("건축법", reg["corner_cutoff_article"])
        self.assertIn("건축법", reg["road_diagonal_article"])
        self.assertIn("건축법", reg["adjacent_setback_article"])
        self.assertIn("건축법", reg["building_line_article"])
        self.assertIn("주차장법", reg["parking_article"])
        self.assertIn("건축법", reg["landscaping_article"])

    def test_height_limit_null_default(self):
        """Height limit is null (zone-agnostic, requires site-specific data)."""
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역"])
        self.assertIsNone(reg["height_limit_m"])
        self.assertIn("건축법", reg["height_article"])

    def test_parking_rule_text(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역"])
        self.assertIn("주차장법", reg["parking_rule"])

    def test_building_line_null_default(self):
        from land.services import regulation_calculator
        reg = regulation_calculator.calculate_all(["제1종일반주거지역"])
        self.assertIsNone(reg["building_line_setback_m"])


# ──────────────────────────────────────────────────────
# View Tests (updated for v2 response format)
# ──────────────────────────────────────────────────────
class ZonesViewTest(TestCase):

    def test_zones_list(self):
        client = Client()
        resp = client.get("/land/zones/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["count"], 21)
        self.assertEqual(len(data["zones"]), 21)

    def test_zones_has_required_fields(self):
        client = Client()
        resp = client.get("/land/zones/")
        data = resp.json()
        zone = data["zones"][0]
        for field in ("zone_name", "bcr_default", "far_default", "category"):
            self.assertIn(field, zone, f"Missing field: {field}")


class AnalyzeViewTest(TestCase):

    def test_analyze_with_zones(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "test",
                "input_type": "raw",
                "zones": ["제1종일반주거지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNotNone(data["regulations"])
        self.assertEqual(data["regulations"]["bcr"]["limit_pct"], 60)
        self.assertEqual(data["regulations"]["far"]["limit_pct"], 200)

    def test_analyze_has_all_10_regulations(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "test",
                "input_type": "raw",
                "zones": ["제1종일반주거지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        data = resp.json()
        regs = data["regulations"]
        for key in ("bcr", "far", "height", "sunlight_setback", "corner_cutoff",
                     "road_diagonal", "building_line", "adjacent_setback",
                     "parking", "landscaping"):
            self.assertIn(key, regs, f"Missing regulation: {key}")

    def test_analyze_sunlight_for_residential(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "test",
                "input_type": "raw",
                "zones": ["제1종일반주거지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data["regulations"]["sunlight_setback"]["applies"])
        self.assertEqual(data["regulations"]["sunlight_setback"]["direction"], "정북방향")

    def test_analyze_sunlight_false_for_commercial(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "test",
                "input_type": "raw",
                "zones": ["중심상업지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        data = resp.json()
        self.assertFalse(data["regulations"]["sunlight_setback"]["applies"])

    def test_analyze_with_pnu(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "1168011200101280003",
                "input_type": "pnu",
                "zones": ["준주거지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNotNone(data["pnu"])
        self.assertEqual(data["pnu"]["sido"], "11")

    def test_analyze_invalid_pnu(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({"input": "123", "input_type": "pnu"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_analyze_no_input(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_analyze_invalid_json(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data="not json",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_analyze_zones_must_be_list(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({"input": "x", "input_type": "raw", "zones": "not a list"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_analyze_input_too_long(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({"input": "x" * 501, "input_type": "raw", "zones": ["준주거지역"]}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_analyze_creates_audit_log(self):
        from land.models import LandQuery
        client = Client()
        client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "test",
                "input_type": "raw",
                "zones": ["중심상업지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(LandQuery.objects.count(), 1)
        log = LandQuery.objects.first()
        self.assertEqual(log.building_coverage_limit, 90)
        self.assertEqual(log.floor_area_limit, 1500)

    def test_analyze_creates_analysis_result(self):
        from land.models import LandAnalysisResult
        client = Client()
        client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "test",
                "input_type": "raw",
                "zones": ["제1종일반주거지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(LandAnalysisResult.objects.count(), 1)
        result = LandAnalysisResult.objects.first()
        self.assertEqual(result.bcr_pct, 60)
        self.assertEqual(result.far_pct, 200)
        self.assertTrue(result.sunlight_applies)
        self.assertEqual(result.road_diagonal_multiplier, 1.0)

    def test_analyze_links_query_to_result(self):
        from land.models import LandQuery
        client = Client()
        client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "test",
                "input_type": "raw",
                "zones": ["제1종일반주거지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        log = LandQuery.objects.first()
        self.assertIsNotNone(log.analysis_result)

    def test_analyze_restrictions_list(self):
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "test",
                "input_type": "raw",
                "zones": ["제1종일반주거지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        data = resp.json()
        restrictions = data["restrictions"]
        self.assertIsInstance(restrictions, list)
        self.assertTrue(any("건폐율" in r for r in restrictions))
        self.assertTrue(any("용적률" in r for r in restrictions))
        self.assertTrue(any("일조사선" in r for r in restrictions))

    def test_analyze_zone_info_backward_compat(self):
        """zone_info field still present for backward compatibility."""
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "test",
                "input_type": "raw",
                "zones": ["제1종일반주거지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        data = resp.json()
        self.assertIn("zone_info", data)
        self.assertEqual(data["zone_info"]["bcr_limit"], 60)


class ResolveViewTest(TestCase):

    def test_resolve_valid_pnu(self):
        client = Client()
        resp = client.post(
            "/land/resolve/",
            data=json.dumps({"input": "1168011200101280003", "input_type": "pnu"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["valid"])

    def test_resolve_invalid_pnu_returns_400(self):
        client = Client()
        resp = client.post(
            "/land/resolve/",
            data=json.dumps({"input": "123", "input_type": "pnu"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_resolve_address(self):
        """Address resolution via Vworld (returns success if API key configured)."""
        client = Client()
        resp = client.post(
            "/land/resolve/",
            data=json.dumps({"input": "서울시 강남구", "input_type": "address"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        # Vworld API is live (Phase 2.5), so this may succeed or fail
        # depending on network. Just check structure.
        data = resp.json()
        self.assertIn("success", data)

    def test_resolve_missing_input(self):
        client = Client()
        resp = client.post(
            "/land/resolve/",
            data=json.dumps({"input_type": "pnu"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


class StatsViewTest(TestCase):

    def test_stats_empty(self):
        client = Client()
        resp = client.get("/land/stats/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_queries"], 0)
