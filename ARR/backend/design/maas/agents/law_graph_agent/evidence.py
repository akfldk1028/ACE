"""Existing-source legal evidence adapter owned by ``law_graph_agent``."""

from __future__ import annotations

import sys
import os
import socket
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

import httpx

from design.maas.agents.shared.types import AgentEvidence, ExecutionIdentity
from design.maas.law_provenance import build_law_provenance_projection


GraphLoader = Callable[[], Mapping[str, Any]]
LawSearcher = Callable[[str, int], Mapping[str, Any]]

LAW_SEARCH_TIMEOUT_SECONDS = 6.0
LAW_SEARCH_CONNECT_TIMEOUT_SECONDS = 1.0


def collect_law_agent_evidence(
    identity: ExecutionIdentity,
    context: Mapping[str, Any],
    *,
    graph_loader: GraphLoader | None = None,
    searcher: LawSearcher | None = None,
) -> AgentEvidence:
    """Collect provenance without allowing availability failures to pass."""

    law = context.get("law")
    law = dict(law) if isinstance(law, Mapping) else {}
    resolved_graph_loader = graph_loader or _fast_graph_projection
    graph_projection = dict(resolved_graph_loader() or {})
    graph_status = graph_projection.get("graph_status")
    graph_status = dict(graph_status) if isinstance(graph_status, Mapping) else {}
    graph_status.setdefault("attempted", True)
    graph_status["available"] = bool(graph_status.get("available"))

    resolved_searcher = searcher or _bounded_law_domain_search
    building_type = str(context.get("building_type") or "building mass")
    query = f"{building_type} 용적률 건폐율 높이 주차"
    try:
        law_search = dict(resolved_searcher(query, 3) or {})
    except Exception as exc:  # external boundary: preserve a bounded error only
        law_search = {
            "attempted": True,
            "available": False,
            "error_category": _error_category(exc),
            "results": [],
        }
    law_search.setdefault("attempted", True)
    law_search["available"] = bool(law_search.get("available"))
    law_search["query"] = str(law_search.get("query") or query)
    search_results = [row for row in law_search.get("results") or () if isinstance(row, Mapping)]
    law_search["result_count"] = len(search_results)

    articles = [row for row in graph_projection.get("articles") or () if isinstance(row, Mapping)]
    article_ids = [
        str(row.get("id") or row.get("full_id") or row.get("ref_id") or "")
        for row in articles
    ]
    article_ids = [value for value in article_ids if value]
    search_result_ids = [
        str(row.get("hang_id") or row.get("id") or row.get("source_id") or "")
        for row in search_results
    ]
    search_result_ids = [value for value in search_result_ids if value]

    missing: list[str] = []
    if not graph_status["available"]:
        missing.append("neo4j_unavailable")
    elif not article_ids:
        missing.append("neo4j_articles_unresolved")
    if not law_search["available"]:
        missing.append("law_search_unavailable")
    elif not search_result_ids:
        missing.append("law_search_results_empty")
    if identity.pnu == "PNU_UNRESOLVED":
        missing.append("pnu_unresolved")

    numeric_failed = bool(
        law.get("hard_pass") is False
        and law.get("evaluated") is True
    ) or str(law.get("status") or "") == "failed"
    if numeric_failed:
        status = "failed"
    elif missing:
        status = "needs_evidence"
    else:
        status = "passed"

    return AgentEvidence(
        evidence_id="evidence:law_graph_agent",
        agent="law_graph_agent",
        status=status,
        summary=(
            "legal evidence bound to PNU, law-domain search, and Neo4j"
            if status == "passed"
            else f"legal evidence incomplete: {', '.join(missing) or 'numeric hard gate failed'}"
        ),
        identity=identity,
        evidence={
            "pnu": identity.pnu,
            "numeric_preflight": law,
            "neo4j": graph_status,
            "law_search": {
                key: value
                for key, value in law_search.items()
                if key != "results"
            },
            "articles": [dict(row) for row in articles],
            "search_results": [dict(row) for row in search_results],
            "article_ids": article_ids,
            "search_result_ids": search_result_ids,
            "missing_evidence": missing,
        },
    )


def _bounded_law_domain_search(query: str, limit: int) -> Mapping[str, Any]:
    """Use the existing :8011 law-domain client once; never fan out here."""

    if "test" in sys.argv:
        return {
            "attempted": False,
            "available": False,
            "error_category": "disabled_during_tests",
            "query": query,
            "results": [],
        }
    from land.config import law_client

    try:
        response = law_client.post(
            "/api/search",
            json={"query": query, "limit": max(1, min(3, int(limit)))},
            timeout=httpx.Timeout(
                LAW_SEARCH_TIMEOUT_SECONDS,
                connect=LAW_SEARCH_CONNECT_TIMEOUT_SECONDS,
            ),
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "attempted": True,
            "available": True,
            "source": "law-domain-agents:8011",
            "query": query,
            "results": list(payload.get("results") or ()),
        }
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        return {
            "attempted": True,
            "available": False,
            "source": "law-domain-agents:8011",
            "query": query,
            "error_category": _error_category(exc),
            "results": [],
        }


def _error_category(exc: Exception) -> str:
    if isinstance(exc, httpx.ConnectTimeout):
        return "law_service_connect_timeout"
    if isinstance(exc, httpx.ConnectError):
        return "law_service_unavailable"
    if isinstance(exc, httpx.TimeoutException):
        return "law_service_timeout"
    if isinstance(exc, httpx.HTTPStatusError):
        return "law_service_http_error"
    return "law_service_error"


def _fast_graph_projection() -> Mapping[str, Any]:
    """Avoid paying a driver routing timeout when the configured port is down."""

    if "test" in sys.argv:
        return build_law_provenance_projection()
    uri = str(os.environ.get("NEO4J_URI") or "").strip()
    if not uri:
        return build_law_provenance_projection()
    parsed = urlparse(uri)
    host = parsed.hostname
    port = parsed.port or 7687
    if host:
        try:
            with socket.create_connection((host, port), timeout=0.6):
                pass
        except OSError:
            return {
                "graph_status": {
                    "attempted": True,
                    "available": False,
                    "uri": uri,
                    "error": "neo4j_tcp_preflight_failed",
                },
                "articles": [],
                "refs_by_check": {},
                "provenance_entities": [],
                "provenance_relations": [],
            }
    return build_law_provenance_projection()


__all__ = ["collect_law_agent_evidence"]
