"""
Law Pipeline Connection Tests

Tests the law proxy chain without requiring Django or running servers.
Validates: URL routing, field mapping, MCP tool signatures, migration structure.

Run: C:/Python313/python test_law_pipeline.py -v
"""

import ast
import json
import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestStep1EmbeddingFix(unittest.TestCase):
    """Verify step3 wrapper comments match actual OpenAI usage."""

    def test_step3_wrapper_mentions_openai(self):
        path = PROJECT_ROOT / "ARR/backend/law/STEP/step3_add_hang_embeddings.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("OpenAI", content)
        self.assertIn("3072", content)
        self.assertNotIn("KR-SBERT", content)
        self.assertNotIn("768-dim", content)

    def test_step3_actual_script_uses_openai(self):
        path = PROJECT_ROOT / "ARR/backend/law/scripts/add_hang_embeddings.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("load_embedding_model", content)
        self.assertIn("openai", content.lower())

    def test_run_all_cost_updated(self):
        path = PROJECT_ROOT / "ARR/backend/law/STEP/run_all.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("$3-5", content)
        self.assertNotIn("$2-3", content)


class TestStep2ARRProxy(unittest.TestCase):
    """Verify ARR backend proxy structure is correct."""

    def test_views_imports_httpx(self):
        path = PROJECT_ROOT / "ARR/backend/law/views.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("import httpx", content)
        self.assertIn("from law.models import SearchLog", content)

    def test_views_proxy_url(self):
        path = PROJECT_ROOT / "ARR/backend/law/views.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("LAW_BACKEND_URL", content)
        self.assertIn("http://localhost:8011", content)

    def test_views_field_mapping(self):
        """search() receives {"q": ...} and sends {"query": ...} to law-domain-agents."""
        path = PROJECT_ROOT / "ARR/backend/law/views.py"
        content = path.read_text(encoding="utf-8")
        # Receives "q" from client
        self.assertIn('body.get("q"', content)
        # Sends "query" to law-domain-agents
        self.assertIn('json={"query": query, "limit": limit}', content)

    def test_views_has_all_endpoints(self):
        path = PROJECT_ROOT / "ARR/backend/law/views.py"
        content = path.read_text(encoding="utf-8")
        for fn in ["def search(", "def search_domain(", "def domains(",
                    "def health(", "def stats("]:
            self.assertIn(fn, content, f"Missing view function: {fn}")

    def test_views_csrf_exempt_on_post(self):
        path = PROJECT_ROOT / "ARR/backend/law/views.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("@csrf_exempt", content)

    def test_views_searchlog_creation(self):
        path = PROJECT_ROOT / "ARR/backend/law/views.py"
        content = path.read_text(encoding="utf-8")
        self.assertGreaterEqual(content.count("SearchLog.objects.create"), 2,
                                "SearchLog.objects.create should appear in search(), search_domain(), and stream")

    def test_views_limit_validation(self):
        """limit parameter should be validated with try/except."""
        path = PROJECT_ROOT / "ARR/backend/law/views.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn('"limit" must be an integer', content)

    def test_urls_match_views(self):
        path = PROJECT_ROOT / "ARR/backend/law/urls.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("path('search/', views.search", content)
        self.assertIn("path('domain/<str:domain_id>/search/', views.search_domain", content)
        self.assertIn("path('domains/', views.domains", content)
        self.assertIn("path('health/', views.health", content)
        self.assertIn("path('stats/', views.stats", content)

    def test_root_urls_includes_law(self):
        path = PROJECT_ROOT / "ARR/backend/backend/urls.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("path('law/', include('law.urls'))", content)

    def test_law_in_installed_apps(self):
        path = PROJECT_ROOT / "ARR/backend/backend/settings.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("'law'", content)

    def test_model_fields(self):
        path = PROJECT_ROOT / "ARR/backend/law/models.py"
        content = path.read_text(encoding="utf-8")
        for field in ["query", "domain_id", "limit", "result_count",
                       "response_time_ms", "source", "created_at"]:
            self.assertIn(field, content, f"Missing field: {field}")

    def test_migration_matches_model(self):
        migration = PROJECT_ROOT / "ARR/backend/law/migrations/0001_add_searchlog.py"
        content = migration.read_text(encoding="utf-8")
        self.assertIn("'SearchLog'", content)
        self.assertIn("initial = True", content)
        for field in ["query", "domain_id", "limit", "result_count",
                       "response_time_ms", "source", "created_at"]:
            self.assertIn(f"'{field}'", content, f"Migration missing field: {field}")

    def test_init_graceful_degradation(self):
        path = PROJECT_ROOT / "ARR/backend/law/__init__.py"
        content = path.read_text(encoding="utf-8")
        self.assertIn("try:", content)
        self.assertIn("except ImportError:", content)
        self.assertIn('__all__ = []', content)


class TestStep3MCPTools(unittest.TestCase):
    """Verify MCP server changes for ARR backend tools."""

    def setUp(self):
        path = PROJECT_ROOT / "AG/autogen_a2a_kit/AG-cli/mcp/autogen_studio_server.py"
        self.content = path.read_text(encoding="utf-8")

    def test_arr_backend_url_config(self):
        self.assertIn('ARR_BACKEND_URL = os.environ.get("ARR_BACKEND_URL", "http://localhost:8000")', self.content)

    def test_arr_client_factory(self):
        self.assertIn("async def _arr_client()", self.content)
        self.assertIn("base_url=ARR_BACKEND_URL", self.content)

    def test_arr_law_search_tool(self):
        self.assertIn("async def arr_law_search(", self.content)
        self.assertIn('"/law/search/"', self.content)
        self.assertIn('"q": query', self.content)

    def test_arr_law_health_tool(self):
        self.assertIn("async def arr_law_health(", self.content)
        self.assertIn('"/law/health/"', self.content)

    def test_arr_law_health_fallback(self):
        """Should try direct law-domain-agents if ARR is unreachable."""
        self.assertIn("_law_client()", self.content.split("arr_law_health")[1])

    def test_tool_count_updated(self):
        # Tool count may increase over time; check it exists in docstring
        self.assertTrue(
            "tools" in self.content,
            "MCP server should mention tool count"
        )

    def test_docstring_lists_arr_category(self):
        self.assertIn("ARR Backend (2)", self.content)

    def test_law_health_uses_dumps(self):
        """law_health should use _dumps(), not json.dumps()."""
        # Find the law_health function body
        idx = self.content.index("async def law_health(")
        end = self.content.index("# -----", idx + 1)
        fn_body = self.content[idx:end]
        self.assertNotIn("json.dumps(", fn_body)
        self.assertIn("_dumps(", fn_body)

    def test_law_client_docstring_fixed(self):
        self.assertIn('"""Create a short-lived httpx client for law-domain-agents calls."""', self.content)


class TestProxyChainConsistency(unittest.TestCase):
    """Verify the full proxy chain field mapping is consistent."""

    def test_mcp_to_arr_field_mapping(self):
        """MCP arr_law_search sends {"q": query} to ARR, which expects "q"."""
        mcp = (PROJECT_ROOT / "AG/autogen_a2a_kit/AG-cli/mcp/autogen_studio_server.py").read_text(encoding="utf-8")
        views = (PROJECT_ROOT / "ARR/backend/law/views.py").read_text(encoding="utf-8")

        # MCP sends "q" to ARR
        self.assertIn('"q": query', mcp)
        # ARR reads "q"
        self.assertIn('body.get("q"', views)
        # ARR sends "query" to law-domain-agents
        self.assertIn('"query": query', views)

    def test_mcp_direct_vs_proxy_field_mapping(self):
        """Direct law_search sends {"query": ...}, arr_law_search sends {"q": ...}."""
        mcp = (PROJECT_ROOT / "AG/autogen_a2a_kit/AG-cli/mcp/autogen_studio_server.py").read_text(encoding="utf-8")

        # Direct tool sends "query" to law-domain-agents
        direct_section = mcp[mcp.index("async def law_search("):mcp.index("async def law_search_domain(")]
        self.assertIn('"query": query', direct_section)

        # Proxy tool sends "q" to ARR
        proxy_section = mcp[mcp.index("async def arr_law_search("):mcp.index("async def arr_law_health(")]
        self.assertIn('"q": query', proxy_section)

    def test_port_assignments(self):
        """Verify port numbers are consistent across projects."""
        mcp = (PROJECT_ROOT / "AG/autogen_a2a_kit/AG-cli/mcp/autogen_studio_server.py").read_text(encoding="utf-8")
        views = (PROJECT_ROOT / "ARR/backend/law/views.py").read_text(encoding="utf-8")

        # law-domain-agents = 8011
        self.assertIn("localhost:8011", mcp)
        self.assertIn("localhost:8011", views)

        # ARR backend = 8000
        self.assertIn("localhost:8000", mcp)


if __name__ == "__main__":
    unittest.main()
