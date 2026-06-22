"""
E2E tests for LLM regulation extraction.

Requires: Neo4j(:7687) + law-domain-agents(:8011) + OPENAI_API_KEY.
Skips gracefully when services unavailable.

Usage:
    cd ARR/backend
    OPENAI_API_KEY=sk-... python manage.py test tests.test_llm_extraction_e2e -v 2
"""

import json
import os
import sys
import unittest

import httpx

# Django setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ARR", "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()


def _services_available():
    """Check if law-domain-agents + OpenAI key are reachable."""
    if not os.getenv("OPENAI_API_KEY"):
        return False
    try:
        r = httpx.get("http://localhost:8011/api/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


SERVICES_UP = _services_available()
SKIP_MSG = "Requires OPENAI_API_KEY + law-domain-agents(:8011)"


@unittest.skipUnless(SERVICES_UP, SKIP_MSG)
class LLMExtractionE2ETest(unittest.TestCase):
    """E2E: law-domain-agents → LLM extraction → structured results."""

    def setUp(self):
        from land.services.law_enricher import clear_extraction_cache
        clear_extraction_cache()
        # Ensure LLM extraction is enabled
        from land import config
        self._orig_enabled = config.LLM_EXTRACTION_ENABLED
        config.LLM_EXTRACTION_ENABLED = True

    def tearDown(self):
        from land import config
        config.LLM_EXTRACTION_ENABLED = self._orig_enabled

    def test_sunlight_extraction(self):
        """주거지역 일조사선 추출: sunlight_applies + sunlight_rules."""
        from land.services.law_enricher import extract_regulation_values

        result = extract_regulation_values(["제1종일반주거지역"], "sunlight")
        self.assertIsNotNone(result, "LLM extraction returned None")
        self.assertIsInstance(result, dict)
        self.assertIn("sunlight_applies", result)
        self.assertIsInstance(result["sunlight_applies"], bool)
        # 제1종일반주거지역은 일조사선 적용
        self.assertTrue(result["sunlight_applies"])
        # Rules should be non-empty list
        rules = result.get("sunlight_rules", [])
        self.assertIsInstance(rules, list)
        self.assertGreater(len(rules), 0, "sunlight_rules should not be empty")

    def test_adjacent_setback_extraction(self):
        """인접대지 이격거리 추출: adjacent_setback_m > 0."""
        from land.services.law_enricher import extract_regulation_values

        result = extract_regulation_values(["제1종일반주거지역"], "adjacent_setback")
        self.assertIsNotNone(result, "LLM extraction returned None")
        self.assertIsInstance(result, dict)
        setback = result.get("adjacent_setback_m")
        self.assertIsNotNone(setback, "adjacent_setback_m should not be None")
        self.assertGreater(setback, 0, "adjacent_setback_m should be positive")


@unittest.skipUnless(SERVICES_UP, SKIP_MSG)
class AnalyzeEndpointE2ETest(unittest.TestCase):
    """E2E: POST /land/analyze/ → sunlight_source field."""

    def setUp(self):
        from land.services.law_enricher import clear_extraction_cache
        clear_extraction_cache()
        from land import config
        self._orig_enabled = config.LLM_EXTRACTION_ENABLED
        config.LLM_EXTRACTION_ENABLED = True

    def tearDown(self):
        from land import config
        config.LLM_EXTRACTION_ENABLED = self._orig_enabled

    def test_residential_sunlight_source_law_text(self):
        """주거지역 analyze → sunlight_source == 'law_text'."""
        from django.test import Client
        client = Client()
        response = client.post(
            "/land/analyze/",
            data=json.dumps({
                "zones": ["제1종일반주거지역"],
                "input_type": "zones",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        reg = data.get("regulation", {})
        self.assertEqual(
            reg.get("sunlight_source"), "law_text",
            f"Expected sunlight_source='law_text', got '{reg.get('sunlight_source')}'"
        )

    def test_non_residential_guard(self):
        """준주거지역 → sunlight_applies=False, source != 'law_text' (가드)."""
        from django.test import Client
        client = Client()
        response = client.post(
            "/land/analyze/",
            data=json.dumps({
                "zones": ["준주거지역"],
                "input_type": "zones",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        reg = data.get("regulation", {})
        self.assertFalse(
            reg.get("sunlight_applies", True),
            "준주거지역 should have sunlight_applies=False"
        )
        self.assertNotEqual(
            reg.get("sunlight_source"), "law_text",
            "Guard should prevent LLM override for 준주거지역"
        )


if __name__ == "__main__":
    unittest.main()
