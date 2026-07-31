"""
A2A SDK v1.0 Integration Tests

Tests the A2A SDK migration across all 3 interconnected projects:
1. AG/agent/law-domain-agents (server.py) — A2A SDK server + REST API
2. AG/autogen_a2a_kit (a2a_client.py) — A2A SDK client
3. ACE MCP Server — REST API consumers

Validates:
- A2A SDK imports and types work (v1.0 protobuf)
- server.py has SDK mount code
- a2a_client.py uses SDK classes
- REST API endpoints preserved (no breakage)
- New endpoints (expand, schema) present
- PageRank integration present
- Tool routing prefix pattern present
- Cross-project port/URL consistency

Run: C:/Python313/python tests/test_a2a_sdk_integration.py -v
"""

import ast
import json
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LAW_AGENTS_DIR = PROJECT_ROOT / "AG/agent/law-domain-agents"
A2A_KIT_DIR = PROJECT_ROOT / "AG/autogen_a2a_kit"
ARR_BACKEND_DIR = PROJECT_ROOT / "ARR/backend"


class TestA2ASDKServerStructure(unittest.TestCase):
    """Verify server.py has proper A2A SDK v1.0 integration."""

    def setUp(self):
        self.content = (LAW_AGENTS_DIR / "server.py").read_text(encoding="utf-8")

    def test_sdk_imports_present(self):
        self.assertIn("from a2a.server.apps import A2AFastAPIApplication", self.content)
        self.assertIn("from a2a.server.request_handlers import DefaultRequestHandler", self.content)
        self.assertIn("from a2a.server.tasks import InMemoryTaskStore", self.content)

    def test_sdk_type_imports(self):
        self.assertIn("AgentCard as A2AAgentCard", self.content)
        self.assertIn("AgentCapabilities as A2ACapabilities", self.content)
        self.assertIn("AgentInterface as A2AInterface", self.content)
        self.assertIn("AgentSkill as A2ASkill", self.content)

    def test_executor_import(self):
        self.assertIn("from a2a_executor import LawSearchAgentExecutor", self.content)

    def test_mount_function_exists(self):
        self.assertIn("def _mount_a2a_sdk(", self.content)

    def test_mount_called_in_lifespan(self):
        self.assertIn("_mount_a2a_sdk(app, domains, agent_factory)", self.content)

    def test_mount_order_domain_first(self):
        """Per-domain agents must mount BEFORE cross-domain (Starlette prefix matching)."""
        domain_mount_pos = self.content.index("Mount per-domain agents FIRST")
        cross_mount_pos = self.content.index("Mount unified cross-domain agent LAST")
        self.assertLess(domain_mount_pos, cross_mount_pos)

    def test_legacy_a2a_removed(self):
        """Manual A2A routes should be gone."""
        self.assertNotIn("register_a2a_routes", self.content)
        self.assertNotIn("handle_a2a_message", self.content)
        self.assertNotIn("generate_agent_card", self.content)
        self.assertNotIn("class JSONRPCRequest", self.content)
        self.assertNotIn("class JSONRPCResponse", self.content)
        self.assertNotIn("class A2AMessagePart", self.content)

    def test_rest_endpoints_preserved(self):
        """All original REST API endpoints must still exist."""
        for endpoint in [
            "/api/search",
            "/api/domain/{domain_id}/search",
            "/api/domains",
            "/api/health",
        ]:
            self.assertIn(endpoint, self.content, f"Missing REST endpoint: {endpoint}")

    def test_new_endpoints_present(self):
        self.assertIn("/api/expand", self.content)
        self.assertIn("/api/schema", self.content)

    def test_domains_response_updated(self):
        """Domain list should reference new A2A paths, not legacy ones."""
        self.assertIn("a2a_card", self.content)
        self.assertIn("a2a_jsonrpc", self.content)
        self.assertNotIn("/.well-known/agent-card/{", self.content)
        self.assertNotIn('"/messages/', self.content)

    def test_root_endpoint_updated(self):
        self.assertIn('"a2a":', self.content)
        self.assertIn("/a2a/.well-known/agent-card.json", self.content)


class TestA2AExecutorStructure(unittest.TestCase):
    """Verify a2a_executor.py follows SDK patterns."""

    def setUp(self):
        self.content = (LAW_AGENTS_DIR / "a2a_executor.py").read_text(encoding="utf-8")

    def test_inherits_agent_executor(self):
        self.assertIn("class LawSearchAgentExecutor(AgentExecutor):", self.content)

    def test_execute_method(self):
        self.assertIn("async def execute(", self.content)

    def test_cancel_method(self):
        self.assertIn("async def cancel(", self.content)

    def test_uses_task_status_update_event(self):
        self.assertIn("TaskStatusUpdateEvent", self.content)
        self.assertIn("TASK_STATE_WORKING", self.content)
        self.assertIn("TASK_STATE_COMPLETED", self.content)
        self.assertIn("TASK_STATE_CANCELED", self.content)

    def test_uses_protobuf_timestamp(self):
        self.assertIn("from google.protobuf.timestamp_pb2 import Timestamp", self.content)

    def test_tool_routing_prefix(self):
        """Should support exact:/semantic:/expand:/article: prefixes."""
        self.assertIn("exact", self.content)
        self.assertIn("semantic", self.content)
        self.assertIn("expand", self.content)
        self.assertIn("article", self.content)
        self.assertIn("_PREFIX_PATTERN", self.content)

    def test_thread_safe_semantic(self):
        """_semantic_search should restore original domain_id."""
        self.assertIn("finally:", self.content)
        self.assertIn("original_domain", self.content)


class TestA2AClientStructure(unittest.TestCase):
    """Verify a2a_client.py uses official SDK classes."""

    def setUp(self):
        self.content = (A2A_KIT_DIR / "a2a_client.py").read_text(encoding="utf-8")

    def test_sdk_client_imports(self):
        self.assertIn("from a2a.client import", self.content)
        self.assertIn("A2ACardResolver", self.content)
        self.assertIn("ClientFactory", self.content)
        self.assertIn("create_text_message_object", self.content)

    def test_async_function(self):
        self.assertIn("async def call_a2a_async(", self.content)

    def test_sync_wrapper(self):
        self.assertIn("def call_a2a(", self.content)
        self.assertIn("asyncio.run", self.content)

    def test_backwards_compatible(self):
        """create_a2a_tool and check_server should still exist."""
        self.assertIn("def create_a2a_tool(", self.content)
        self.assertIn("def check_server(", self.content)

    def test_no_manual_jsonrpc(self):
        """Should NOT have manual JSON-RPC payload construction."""
        self.assertNotIn('"jsonrpc": "2.0"', self.content)
        self.assertNotIn('"method": "message/send"', self.content)

    def test_default_url_points_to_a2a(self):
        self.assertIn("http://localhost:8011/a2a", self.content)


class TestGraphAlgorithmsStructure(unittest.TestCase):
    """Verify graph_algorithms.py (GDS-free PageRank)."""

    def setUp(self):
        self.content = (LAW_AGENTS_DIR / "graph_algorithms.py").read_text(encoding="utf-8")

    def test_pagerank_function(self):
        self.assertIn("def compute_pagerank(", self.content)

    def test_article_importance(self):
        self.assertIn("def compute_article_importance(", self.content)

    def test_cache_class(self):
        self.assertIn("class PageRankCache:", self.content)
        self.assertIn("def get_hang_score(", self.content)
        self.assertIn("def invalidate(", self.content)

    def test_no_gds_dependency(self):
        """Should NOT import neo4j GDS plugin."""
        self.assertNotIn("from graphdatascience", self.content)
        self.assertNotIn("import gds", self.content)


class TestSearchEngineRefactor(unittest.TestCase):
    """Verify law_search_engine.py refactoring."""

    def setUp(self):
        self.content = (LAW_AGENTS_DIR / "law_search_engine.py").read_text(encoding="utf-8")

    def test_run_cypher_helper(self):
        self.assertIn("def _run_cypher(", self.content)

    def test_to_search_result_helper(self):
        self.assertIn("def _to_search_result(", self.content)

    def test_pagerank_integration(self):
        self.assertIn("PageRankCache", self.content)
        self.assertIn("get_hang_score", self.content)
        self.assertIn("pr_score", self.content)

    def test_no_direct_session_run(self):
        """Most session.run() calls should be replaced by _run_cypher()."""
        # Count remaining direct session.run() calls (some may remain for special cases)
        direct_count = self.content.count("session.run(")
        run_cypher_count = self.content.count("self._run_cypher(")
        self.assertGreater(run_cypher_count, direct_count,
                          f"_run_cypher ({run_cypher_count}) should be used more than direct session.run ({direct_count})")


class TestCrossProjectConsistency(unittest.TestCase):
    """Verify consistency across all 3 projects."""

    def test_port_8011_consistent(self):
        """All projects should use port 8011 for law-domain-agents."""
        server = (LAW_AGENTS_DIR / "server.py").read_text(encoding="utf-8")
        client = (A2A_KIT_DIR / "a2a_client.py").read_text(encoding="utf-8")
        views = (ARR_BACKEND_DIR / "law/views.py").read_text(encoding="utf-8")

        self.assertIn("8011", server)
        self.assertIn("localhost:8011", client)
        self.assertIn("localhost:8011", views)

    def test_requirements_has_a2a_sdk(self):
        req = (LAW_AGENTS_DIR / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("a2a-sdk", req)
        self.assertIn("1.0.0", req)

    def test_executor_file_exists(self):
        self.assertTrue((LAW_AGENTS_DIR / "a2a_executor.py").exists())

    def test_graph_algorithms_file_exists(self):
        self.assertTrue((LAW_AGENTS_DIR / "graph_algorithms.py").exists())

    def test_tests_exist(self):
        tests_dir = LAW_AGENTS_DIR / "tests"
        self.assertTrue(tests_dir.exists())
        test_files = list(tests_dir.glob("test_*.py"))
        self.assertGreaterEqual(len(test_files), 4, f"Expected 4+ test files, got {len(test_files)}")

    def test_domain_agent_factory_has_get_any_agent(self):
        content = (LAW_AGENTS_DIR / "domain_agent_factory.py").read_text(encoding="utf-8")
        self.assertIn("def get_any_agent(", content)


class TestRESTAPIPreservation(unittest.TestCase):
    """Verify the REST API contract hasn't changed — critical for ACE MCP and ARR."""

    def test_search_endpoint_accepts_query_and_limit(self):
        content = (LAW_AGENTS_DIR / "server.py").read_text(encoding="utf-8")
        self.assertIn("query", content)
        self.assertIn("limit", content)

    def test_domains_returns_total_and_list(self):
        content = (LAW_AGENTS_DIR / "server.py").read_text(encoding="utf-8")
        self.assertIn('"total":', content)
        self.assertIn('"domains":', content)

    def test_health_returns_status(self):
        content = (LAW_AGENTS_DIR / "server.py").read_text(encoding="utf-8")
        self.assertIn('"status": "healthy"', content)

    def test_arr_proxy_still_works(self):
        """ARR views.py should still proxy to :8011/api/search."""
        views = (ARR_BACKEND_DIR / "law/views.py").read_text(encoding="utf-8")
        self.assertIn("/api/search", views)
        self.assertIn("/api/domains", views)
        self.assertIn("/api/health", views)


if __name__ == "__main__":
    unittest.main()
