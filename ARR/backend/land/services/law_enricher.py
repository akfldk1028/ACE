"""
Law Enricher - searches law-domain-agents for relevant building/zoning law articles.

Queries :8011/api/search with zone-specific keywords.
Designed for extension: future phases will add multi-law corpus search.
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

LAW_AGENTS_URL = os.getenv("LAW_BACKEND_URL", "http://localhost:8011")
_TIMEOUT = httpx.Timeout(30.0, connect=5.0)

# Base queries applied to every analysis (10 regulation categories)
_BASE_QUERIES = [
    "건폐율",
    "용적률",
    "건축제한",
    "높이제한",
    "일조권",
    "가각전제",
    "도로사선",
    "건축선",
    "인접대지",
    "주차장",
    "조경",
]

# Extended queries for items 11-41 (optional, activated via include_extended)
_EXTENDED_QUERIES = [
    "용도제한",
    "접도의무",
    "대지분할",
    "인동간격",
    "공개공지",
    "내화구조",
    "개발행위허가",
    "소방시설",
    "에너지절약",
]


def search_for_zones(zone_names: list[str], limit_per_query: int = 5,
                     include_extended: bool = False) -> dict:
    """
    Search law articles relevant to the given zoning zones.

    For each zone, searches base queries + zone-specific keywords.
    Fails fast if law-domain-agents is unreachable.

    Returns:
        {
            "articles": [{"query": str, "results": list}],
            "total_count": int,
            "errors": [str]
        }
    """
    all_articles = []
    errors = []

    # Build query list: base + extended(optional) + zone-specific
    queries = list(_BASE_QUERIES)
    if include_extended:
        queries.extend(_EXTENDED_QUERIES)
    for zone in zone_names:
        queries.append(f"{zone} 건폐율")
        queries.append(f"{zone} 건축제한")

    # Deduplicate while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)

    try:
        with httpx.Client(base_url=LAW_AGENTS_URL, timeout=_TIMEOUT) as client:
            consecutive_failures = 0
            for query in unique_queries:
                try:
                    resp = client.post(
                        "/api/search",
                        json={"query": query, "limit": limit_per_query},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    results = data.get("results", [])
                    if results:
                        all_articles.append({
                            "query": query,
                            "results": results,
                        })
                    consecutive_failures = 0
                except httpx.ConnectError:
                    remaining = len(unique_queries) - unique_queries.index(query) - 1
                    errors.append(
                        f"law-domain-agents unreachable, skipping {remaining} remaining queries"
                    )
                    break
                except Exception as e:
                    consecutive_failures += 1
                    errors.append(f"Query '{query}' failed: {e}")
                    if consecutive_failures >= 3:
                        errors.append("3 consecutive failures, stopping law search")
                        break
    except httpx.ConnectError:
        errors.append(f"law-domain-agents not reachable at {LAW_AGENTS_URL}")

    total = sum(len(a["results"]) for a in all_articles)

    return {
        "articles": all_articles,
        "total_count": total,
        "errors": errors,
    }
