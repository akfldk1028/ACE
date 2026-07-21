import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.test import SimpleTestCase

from design.maas.book_language.book_scan_vlm_audit import audit_page, audit_status
from design.maas.outcome_graph_slice import build_outcome_graph_slice


class MaasExplorationGraphApiTest(SimpleTestCase):
    def test_book_asset_is_allow_listed_registry_evidence(self):
        response = self.client.get("/design/maas/book-assets/3/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertIn("immutable", response["Cache-Control"])
        response.close()
        self.assertEqual(self.client.get("/design/maas/book-assets/70/").status_code, 404)

    def test_book_scan_audit_is_cache_only_without_confirmation(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"MAAS_BOOK_SCAN_VLM_CACHE_DIR": directory},
        ):
            status = audit_status(model="test-vlm")
            result = audit_page(page=3, model="test-vlm")
        self.assertEqual(status["cached_count"], 0)
        self.assertTrue(status["cache_only_default"])
        self.assertEqual(result["status"], "cache_miss")
        self.assertFalse(result["live_request_made"])

    def test_outcome_slice_preserves_directional_portfolio_lineage(self):
        with tempfile.TemporaryDirectory() as directory:
            graph_path = Path(directory) / "pnu-test.json"
            graph_path.write_text(json.dumps({
                "schema_version": "test.v1",
                "nodes": [
                    {"id": "outcome:main", "kind": "outcome", "attributes": {"selected": True}},
                    {"id": "outcome:sibling", "kind": "outcome", "attributes": {"selected": True}},
                    {"id": "compiled:main", "kind": "compiled_geometry", "attributes": {}},
                    {"id": "portfolio:main", "kind": "geometry_portfolio", "attributes": {}},
                    {"id": "critic:main", "kind": "vlm_portfolio_critic", "attributes": {}},
                ],
                "edges": [
                    {"id": "e1", "source": "outcome:main", "target": "compiled:main", "kind": "compiled_as"},
                    {"id": "e2", "source": "compiled:main", "target": "portfolio:main", "kind": "member_of"},
                    {"id": "e3", "source": "portfolio:main", "target": "critic:main", "kind": "reviewed_as_board_by"},
                    {"id": "e4", "source": "compiled:main", "target": "outcome:sibling", "kind": "unrelated_branch"},
                ],
            }), encoding="utf-8")
            with patch.dict(os.environ, {"MAAS_OUTCOME_GRAPH_DIR": directory}):
                result = build_outcome_graph_slice(pnu="test", depth=4, max_nodes=80)
        ids = {node["id"] for node in result["nodes"]}
        self.assertEqual(result["root_node_ids"], ["portfolio:main"])
        self.assertIn("outcome:main", ids)
        self.assertIn("critic:main", ids)
        self.assertNotIn("outcome:sibling", ids)
