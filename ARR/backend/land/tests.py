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


# ──────────────────────────────────────────────────────
# Land API Tests (Phase 3)
# ──────────────────────────────────────────────────────
import httpx
from unittest.mock import patch, MagicMock


class LandApiStubTest(TestCase):
    """Test land_api returns stub when no API key."""

    def test_stub_when_no_key(self):
        from land.services import land_api
        with patch.object(land_api, 'VWORLD_API_KEY', ''):
            result = land_api.get_land_use_info('1168010100106770000')
        self.assertTrue(result["success"])
        self.assertEqual(result["source"], "stub")
        self.assertEqual(result["zones"], [])

    def test_stub_has_message(self):
        from land.services import land_api
        with patch.object(land_api, 'VWORLD_API_KEY', ''):
            result = land_api.get_land_use_info('1168010100106770000')
        self.assertIn("message", result)


class LandApiParseTest(TestCase):
    """Test Vworld API response parsing (mocked HTTP)."""

    def _mock_land_use_response(self):
        return {
            "landUses": {
                "totalCount": "3",
                "field": [
                    {"prposAreaDstrcCodeNm": "일반상업지역", "prposAreaDstrcCode": "UQA220", "cnflcAtNm": "포함"},
                    {"prposAreaDstrcCodeNm": "도시지역", "prposAreaDstrcCode": "UQA01X", "cnflcAtNm": "포함"},
                    {"prposAreaDstrcCodeNm": "제2종일반주거지역", "prposAreaDstrcCode": "UQA122", "cnflcAtNm": "접함"},
                ],
            }
        }

    def _mock_ladfrl_response(self):
        return {
            "ladfrlVOList": {
                "totalCount": "1",
                "ladfrlVOList": [
                    {"lndpclAr": "497.2", "lndcgrCodeNm": "대", "pnu": "1168010100106770000"},
                ],
            }
        }

    def _mock_price_response(self, price="28620000", year="2025"):
        return {
            "indvdLandPrices": {
                "totalCount": "1",
                "field": [
                    {"pblntfPclnd": price, "stdrYear": year, "pnu": "1168010100106770000"},
                ],
            }
        }

    def _mock_empty_response(self):
        return {"response": {"totalCount": "0"}}

    @patch('land.services.land_api.VWORLD_API_KEY', 'test-key')
    @patch('land.services.land_api.httpx.Client')
    def test_parse_land_use_zones(self, mock_client_cls):
        """Parses zone names from getLandUseAttr, filters cnflcAtNm=포함 only."""
        from land.services import land_api
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._mock_land_use_response()
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = land_api._fetch_land_use_attr('1168010100106770000')
        self.assertTrue(result["success"])
        # 일반상업지역(포함) + 도시지역(포함). 제2종일반주거지역 excluded (접함)
        self.assertIn("일반상업지역", result["zones"])
        self.assertNotIn("제2종일반주거지역", result["zones"])

    @patch('land.services.land_api.VWORLD_API_KEY', 'test-key')
    @patch('land.services.land_api.httpx.Client')
    def test_parse_ladfrl(self, mock_client_cls):
        """Parses area and jimok from ladfrlList."""
        from land.services import land_api
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._mock_ladfrl_response()
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = land_api._fetch_ladfrl('1168010100106770000')
        self.assertTrue(result["success"])
        self.assertEqual(result["land_area_m2"], 497.2)
        self.assertEqual(result["land_use_situation"], "대")

    @patch('land.services.land_api.VWORLD_API_KEY', 'test-key')
    @patch('land.services.land_api.httpx.Client')
    def test_parse_land_price(self, mock_client_cls):
        """Parses price from getIndvdLandPriceAttr."""
        from land.services import land_api
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._mock_price_response()
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = land_api._fetch_land_price_for_year('1168010100106770000', '2025')
        self.assertTrue(result["success"])
        self.assertEqual(result["official_land_price"], 28620000)

    @patch('land.services.land_api.VWORLD_API_KEY', 'test-key')
    @patch('land.services.land_api.httpx.Client')
    def test_connection_error_graceful(self, mock_client_cls):
        """ConnectError returns success=False, not exception."""
        from land.services import land_api
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.ConnectError("unreachable")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = land_api._fetch_land_use_attr('1168010100106770000')
        self.assertFalse(result["success"])
        self.assertIn("connection failed", result["error"])

    @patch('land.services.land_api.VWORLD_API_KEY', 'test-key')
    @patch('land.services.land_api.httpx.Client')
    def test_empty_response_graceful(self, mock_client_cls):
        """Empty API response (totalCount=0) returns success=False."""
        from land.services import land_api
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._mock_empty_response()
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = land_api._fetch_land_use_attr('0000000000000000000')
        self.assertFalse(result["success"])
        self.assertEqual(result["zones"], [])

    @patch('land.services.land_api.VWORLD_API_KEY', 'test-key')
    @patch('land.services.land_api.httpx.Client')
    def test_partial_failure_still_success(self, mock_client_cls):
        """If 2 of 3 APIs fail, overall success=True if 1 succeeds."""
        from land.services import land_api

        def mock_get(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            # Only price API succeeds (3rd and 4th calls: year fallback)
            if 'getIndvdLandPriceAttr' in url:
                mock_resp.json.return_value = self._mock_price_response()
            elif 'getLandUseAttr' in url:
                mock_resp.json.return_value = self._mock_empty_response()
            else:
                mock_resp.json.return_value = {"response": {"totalCount": "0"}}
            return mock_resp

        mock_client = MagicMock()
        mock_client.get.side_effect = mock_get
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = land_api.get_land_use_info('1168010100106770000')
        self.assertTrue(result["success"])
        self.assertEqual(result["source"], "vworld")
        self.assertEqual(result["official_land_price"], 28620000)
        self.assertEqual(result["zones"], [])
        self.assertIn("errors", result)

    @patch('land.services.land_api.VWORLD_API_KEY', 'test-key')
    @patch('land.services.land_api.httpx.Client')
    def test_all_fail_returns_failure(self, mock_client_cls):
        """If all 3 APIs fail, overall success=False."""
        from land.services import land_api

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"response": {"totalCount": "0"}}
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = land_api.get_land_use_info('0000000000000000000')
        self.assertFalse(result["success"])
        self.assertIn("message", result)

    @patch('land.services.land_api.VWORLD_API_KEY', 'test-key')
    @patch('land.services.land_api.httpx.Client')
    def test_zone_name_dedup(self, mock_client_cls):
        """Duplicate zone names are removed."""
        from land.services import land_api
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "landUses": {
                "totalCount": "3",
                "field": [
                    {"prposAreaDstrcCodeNm": "일반상업지역", "cnflcAtNm": "포함"},
                    {"prposAreaDstrcCodeNm": "일반상업지역", "cnflcAtNm": "포함"},
                    {"prposAreaDstrcCodeNm": "제1종일반주거지역", "cnflcAtNm": "포함"},
                ],
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = land_api._fetch_land_use_attr('1168010100106770000')
        self.assertEqual(len(result["zones"]), 2)


class LandApiNormalizationTest(TestCase):
    """Test zone name normalization."""

    def test_full_name_unchanged(self):
        from land.services.land_api import _normalize_zone_name
        self.assertEqual(_normalize_zone_name("제1종일반주거지역"), "제1종일반주거지역")

    def test_suffix_appended_if_matches(self):
        from land.services.land_api import _normalize_zone_name
        # "일반상업" + "지역" = "일반상업지역" which exists in zoning_mapper
        result = _normalize_zone_name("일반상업")
        self.assertEqual(result, "일반상업지역")

    def test_unknown_name_unchanged(self):
        from land.services.land_api import _normalize_zone_name
        self.assertEqual(_normalize_zone_name("과밀억제"), "과밀억제")


class AnalyzeWithLandApiTest(TestCase):
    """Test analyze view integration with land_api."""

    @patch('land.services.land_api.VWORLD_API_KEY', '')
    def test_manual_zones_override_api_zones(self):
        """Manual zones in request override API-returned zones (stub mode)."""
        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "1168010100106770000",
                "input_type": "pnu",
                "zones": ["제1종일반주거지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Manual zones should be used regardless of API response
        self.assertEqual(data["regulations"]["bcr"]["limit_pct"], 60)

    def test_data_source_recorded(self):
        """data_source reflects land_api source."""
        from land.models import LandAnalysisResult
        client = Client()
        client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "test",
                "input_type": "raw",
                "zones": ["일반상업지역"],
                "include_law": False,
            }),
            content_type="application/json",
        )
        result = LandAnalysisResult.objects.first()
        # With raw input, land_api is not called, so source stays "static"
        self.assertEqual(result.data_source, "static")

    @patch('land.services.land_api.VWORLD_API_KEY', 'test-key')
    @patch('land.services.land_api.httpx.Client')
    def test_api_zones_used_when_no_manual(self, mock_client_cls):
        """API zones used when no manual zones provided."""
        from land.models import LandAnalysisResult

        def mock_get(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            if 'getLandUseAttr' in url:
                mock_resp.json.return_value = {
                    "landUses": {
                        "totalCount": "1",
                        "field": [
                            {"prposAreaDstrcCodeNm": "일반상업지역", "cnflcAtNm": "포함"},
                        ],
                    }
                }
            elif 'ladfrlList' in url:
                mock_resp.json.return_value = {
                    "ladfrlVOList": {
                        "totalCount": "1",
                        "ladfrlVOList": [
                            {"lndpclAr": "500.0", "lndcgrCodeNm": "대"},
                        ],
                    }
                }
            elif 'getIndvdLandPriceAttr' in url:
                mock_resp.json.return_value = {
                    "indvdLandPrices": {
                        "totalCount": "1",
                        "field": [
                            {"pblntfPclnd": "10000000", "stdrYear": "2025"},
                        ],
                    }
                }
            return mock_resp

        mock_client = MagicMock()
        mock_client.get.side_effect = mock_get
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        client = Client()
        resp = client.post(
            "/land/analyze/",
            data=json.dumps({
                "input": "1168010100106770000",
                "input_type": "pnu",
                "include_law": False,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # API-returned zone "일반상업지역" should be used
        self.assertEqual(data["regulations"]["bcr"]["limit_pct"], 80)
        self.assertIsNotNone(data["land_info"])
        self.assertEqual(data["land_info"]["land_area_m2"], 500.0)
        self.assertEqual(data["land_info"]["official_land_price"], 10000000)
        self.assertEqual(data["land_info"]["source"], "vworld")

        # Check saved result
        result = LandAnalysisResult.objects.first()
        self.assertEqual(result.data_source, "vworld")
        self.assertEqual(result.land_use_situation, "대")


# ──────────────────────────────────────────────────────
# Extended Regulation Calculator Tests (items 11-41)
# ──────────────────────────────────────────────────────
class ExtendedCalculatorTest(TestCase):
    """Test regulation_calculator_ext for 31 extended items."""

    def test_returns_31_keys(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["제1종일반주거지역"])
        self.assertEqual(len(result), 31)

    def test_group_a_keys_present(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["제1종일반주거지역"])
        for key in ("building_use_restriction", "site_road_requirement",
                     "site_subdivision_limit", "daylighting_spacing", "split_zoning_rule"):
            self.assertIn(key, result, f"Missing Group A key: {key}")

    def test_group_b_keys_present(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["제1종일반주거지역"])
        for key in ("site_safety", "public_open_space", "on_site_open_space",
                     "structural_safety", "fire_resistant", "fire_compartment",
                     "fire_district", "elevator", "development_permit",
                     "infrastructure_fee"):
            self.assertIn(key, result, f"Missing Group B key: {key}")

    def test_group_c_keys_present(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["제1종일반주거지역"])
        for key in ("fire_protection", "accessibility", "energy_saving", "evacuation",
                     "finishing_materials", "room_daylighting", "sewage_treatment",
                     "school_buffer_zone", "cultural_heritage_zone", "military_zone",
                     "use_district_restriction", "party_wall", "cpted",
                     "combined_development", "basement_restriction", "building_systems"):
            self.assertIn(key, result, f"Missing Group C key: {key}")

    def test_every_item_has_name_and_article(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["제1종일반주거지역"])
        for key, item in result.items():
            self.assertIn("name", item, f"{key} missing 'name'")
            self.assertIn("article", item, f"{key} missing 'article'")
            self.assertTrue(item["article"], f"{key} has empty article")

    def test_residential_daylighting_applies(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["제1종일반주거지역"])
        self.assertTrue(result["daylighting_spacing"]["applies"])

    def test_commercial_daylighting_not_applies(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["중심상업지역"])
        self.assertFalse(result["daylighting_spacing"]["applies"])

    def test_residential_subdivision_limit(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["제1종일반주거지역"])
        self.assertEqual(result["site_subdivision_limit"]["min_area_m2"], 60)

    def test_commercial_subdivision_limit(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["중심상업지역"])
        self.assertEqual(result["site_subdivision_limit"]["min_area_m2"], 150)

    def test_multiple_zones_strictest_subdivision(self):
        """Multiple zones → largest min_area (strictest)."""
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(
            ["제1종일반주거지역", "보전녹지지역"]
        )
        # 주거 60 vs 녹지 200 → strictest = 200
        self.assertEqual(result["site_subdivision_limit"]["min_area_m2"], 200)

    def test_multiple_zones_daylighting_any(self):
        """Daylighting applies if ANY zone requires it."""
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(
            ["제1종일반주거지역", "중심상업지역"]
        )
        self.assertTrue(result["daylighting_spacing"]["applies"])

    def test_multiple_zones_building_use_note(self):
        """Multiple zones adds note about cross-checking."""
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(
            ["제1종일반주거지역", "중심상업지역"]
        )
        self.assertIn("note", result["building_use_restriction"])

    def test_unmatched_zones_still_return_31(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["없는지역"])
        self.assertEqual(len(result), 31)

    def test_development_permit_zone_enrichment(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["보전녹지지역"])
        # 보전녹지 has max_area_m2=5000 in extended JSON
        self.assertEqual(result["development_permit"]["max_area_m2"], 5000)

    def test_development_permit_strictest_multi(self):
        """Multiple zones → smallest max_area for development_permit."""
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(
            ["보전녹지지역", "제1종일반주거지역"]
        )
        # 보전녹지 5000 vs 주거 10000 → strictest = 5000
        self.assertEqual(result["development_permit"]["max_area_m2"], 5000)

    def test_site_road_requirement_common(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["제1종일반주거지역"])
        self.assertEqual(result["site_road_requirement"]["min_frontage_m"], 2)

    def test_group_c_static_content(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["제1종일반주거지역"])
        self.assertIn("소방시설", result["fire_protection"]["name"])
        self.assertIn("소방시설법", result["fire_protection"]["article"])

    def test_building_use_restriction_populated(self):
        from land.services import regulation_calculator_ext
        result = regulation_calculator_ext.calculate_extended(["제1종일반주거지역"])
        bur = result["building_use_restriction"]
        self.assertTrue(bur["allowed_summary"])
        self.assertTrue(bur["prohibited_summary"])


# ──────────────────────────────────────────────────────
# Extended View Integration Tests
# ──────────────────────────────────────────────────────
class ExtendedViewTest(TestCase):
    """Test that extended regulations appear in analyze response."""

    def test_extended_key_in_response(self):
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
        self.assertIn("extended", data["regulations"])
        self.assertEqual(len(data["regulations"]["extended"]), 31)

    def test_existing_10_unchanged(self):
        """Original 10 regulations still present and correct."""
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
            self.assertIn(key, regs, f"Missing original regulation: {key}")
        self.assertEqual(regs["bcr"]["limit_pct"], 60)
        self.assertEqual(regs["far"]["limit_pct"], 200)

    def test_extended_saved_to_db(self):
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
        result = LandAnalysisResult.objects.first()
        self.assertIsInstance(result.regulations_extended, dict)
        self.assertEqual(len(result.regulations_extended), 31)

    def test_extended_has_fire_protection(self):
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
        ext = data["regulations"]["extended"]
        self.assertIn("fire_protection", ext)
        self.assertIn("소방시설", ext["fire_protection"]["name"])

    def test_extended_commercial_no_daylighting(self):
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
        ext = data["regulations"]["extended"]
        self.assertFalse(ext["daylighting_spacing"]["applies"])


# ──────────────────────────────────────────────────────
# Extended Law Enricher Tests
# ──────────────────────────────────────────────────────
class ExtendedLawEnricherTest(TestCase):
    """Test law_enricher extended queries toggle."""

    def test_base_query_count(self):
        from land.services.law_enricher import _BASE_QUERIES
        self.assertEqual(len(_BASE_QUERIES), 11)

    def test_extended_query_count(self):
        from land.services.law_enricher import _EXTENDED_QUERIES
        self.assertEqual(len(_EXTENDED_QUERIES), 9)

    @patch('land.services.law_enricher.httpx.Client')
    def test_extended_false_uses_base_only(self, mock_client_cls):
        """include_extended=False uses only base queries + zone queries."""
        from land.services import law_enricher
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_resp.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        law_enricher.search_for_zones(["제1종일반주거지역"], include_extended=False)
        # 11 base + 2 zone-specific ("제1종일반주거지역 건폐율", "제1종일반주거지역 건축제한")
        self.assertEqual(mock_client.post.call_count, 13)

    @patch('land.services.law_enricher.httpx.Client')
    def test_extended_true_adds_queries(self, mock_client_cls):
        """include_extended=True adds 9 more queries."""
        from land.services import law_enricher
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_resp.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        law_enricher.search_for_zones(["제1종일반주거지역"], include_extended=True)
        # 11 base + 9 extended + 2 zone-specific = 22
        self.assertEqual(mock_client.post.call_count, 22)
