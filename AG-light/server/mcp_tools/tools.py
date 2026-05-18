# AG-light MCP Tools — Slim version (~20 tools)
# Wraps Cloudflare Worker APIs + in-process Message Bus / SharedMemory
"""
Slim MCP tool layer for AG-light.

20 tools covering:
- Law Search (4): law_search, law_search_domain, law_domains, law_health
- Land (5): arr_land_analyze, arr_land_agent_analyze, arr_land_resolve, arr_land_zones, arr_land_stats
- Message Bus (5): send_message, broadcast_message, get_conversation_log, get_agent_conversation, get_bus_status
- SharedMemory (4): store_decision, get_all_decisions, publish_event, get_events
- Utility (2): health_check, get_version

Removed from original ACE MCP (57 tools):
- AutoGen Studio execution/CRUD/sessions/gallery
- A2A agent management
- Validation/test/settings/locks/patterns
- API spec & schema publish (still accessible via SharedMemory REST)

Environment variables:
    WORKER_URL          = http://localhost:8787  (Cloudflare Worker)
    MESSAGE_BUS_URL     = http://localhost:8200/bus   (same process)
    SHARED_MEMORY_URL   = http://localhost:8200/memory (same process)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# --------------- Config ---------------

WORKER_URL = os.environ.get("WORKER_URL", "http://localhost:8787")
MESSAGE_BUS_URL = os.environ.get("MESSAGE_BUS_URL", "http://localhost:8200/bus")
SHARED_MEMORY_URL = os.environ.get("SHARED_MEMORY_URL", "http://localhost:8200/memory")

logger = logging.getLogger("ag-light-mcp")

mcp = FastMCP(
    "AG-light",
    instructions=(
        "AG-light MCP server — 20 tools: law article search (Korean legal regulations), "
        "land regulation analysis (건폐율/용적률/건축제한), "
        "Message Bus conversations, SharedMemory events/decisions."
    ),
)

# --------------- Helpers ---------------


def _dumps(obj: Any) -> str:
    """JSON serialize with Korean support."""
    return json.dumps(obj, ensure_ascii=False, indent=2)


async def _worker_client() -> httpx.AsyncClient:
    """Short-lived httpx client for Cloudflare Worker calls."""
    return httpx.AsyncClient(
        base_url=WORKER_URL,
        timeout=httpx.Timeout(30.0, connect=10.0),
        headers={"Content-Type": "application/json"},
    )


async def _bus_client() -> httpx.AsyncClient:
    """Short-lived httpx client for Message Bus calls (same process)."""
    return httpx.AsyncClient(base_url=MESSAGE_BUS_URL, timeout=5.0)


async def _mem_client() -> httpx.AsyncClient:
    """Short-lived httpx client for SharedMemory calls (same process)."""
    return httpx.AsyncClient(base_url=SHARED_MEMORY_URL, timeout=5.0)


# ===============================================================
# 1. Law Search (4)
# ===============================================================


@mcp.tool()
async def law_search(query: str, limit: int = 10) -> str:
    """Search Korean law articles by keyword or article number (e.g. '제17조', '건축법').

    Uses hybrid search: Vectorize semantic + 법제처 keyword, merged via RRF.

    Args:
        query: Search query (Korean law text, article number, or keyword)
        limit: Maximum results to return (default 10)

    Returns:
        JSON with results [{lawName, lawId, mst, lawType, ...}], total count
    """
    try:
        async with await _worker_client() as client:
            resp = await client.post(
                "/search",
                json={"query": query, "limit": limit, "mode": "hybrid"},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Worker not reachable at {WORKER_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def law_search_domain(domain: str, query: str, limit: int = 10) -> str:
    """Search law articles restricted to a specific mode (hybrid/keyword/semantic).

    Args:
        domain: Search mode — "hybrid", "keyword", or "semantic"
        query: Search query (Korean law text, article number, or keyword)
        limit: Maximum results to return (default 10)

    Returns:
        Same format as law_search
    """
    try:
        async with await _worker_client() as client:
            resp = await client.post(
                "/search",
                json={"query": query, "limit": limit, "mode": domain},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Worker not reachable at {WORKER_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def law_domains() -> str:
    """List available search modes for law search.

    Returns:
        JSON with available modes: hybrid, keyword, semantic
    """
    return _dumps({
        "modes": [
            {"id": "hybrid", "name": "Hybrid (semantic + keyword)", "description": "Vectorize + 법제처 API → RRF merge"},
            {"id": "keyword", "name": "Keyword only", "description": "법제처 API keyword search"},
            {"id": "semantic", "name": "Semantic only", "description": "Cloudflare Vectorize semantic search"},
        ]
    })


@mcp.tool()
async def law_health() -> str:
    """Check Worker health (law search + land endpoints).

    Returns:
        JSON with status, timestamp
    """
    try:
        async with await _worker_client() as client:
            resp = await client.get("/health")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Worker not reachable at {WORKER_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# ===============================================================
# 2. Land Regulation (5)
# ===============================================================


@mcp.tool()
async def arr_land_analyze(
    input: str,
    input_type: str = "pnu",
    zones: list[str] | None = None,
    include_law: bool = True,
) -> str:
    """Analyze land parcel for building regulations with legal article references.

    Returns core regulations (BCR, FAR, height, sunlight, corner cutoff,
    building line, adjacent setback, parking, landscaping) plus related law articles.

    Args:
        input: PNU code (19 digits) or address string
        input_type: "pnu" or "address" (default "pnu")
        zones: Optional list of zoning names (e.g. ["제1종일반주거지역"])
        include_law: Whether to search related law articles (default True)

    Returns:
        JSON with pnu, regulations, zone_info, law_articles, restrictions
    """
    try:
        payload: dict[str, Any] = {
            "input": input,
            "input_type": input_type,
            "include_law": include_law,
        }
        if zones:
            payload["zones"] = zones
        async with await _worker_client() as client:
            resp = await client.post("/land/analyze", json=payload)
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Worker not reachable at {WORKER_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def arr_land_agent_analyze(
    input: str,
    input_type: str = "pnu",
    zones: list[str] | None = None,
    timeout: int = 120,
) -> str:
    """Analyze land parcel with extended analysis (deep analysis).

    Runs the standard analysis via Worker, then formats the result as
    a comprehensive report. No AutoGen Studio dependency.

    Args:
        input: PNU code (19 digits) or address string
        input_type: "pnu" or "address" (default "pnu")
        zones: Optional list of zoning names (e.g. ["제1종일반주거지역"])
        timeout: Max execution time in seconds (default 120)

    Returns:
        JSON with quick_result and formatted report
    """
    result: dict[str, Any] = {}

    # Analysis via Worker
    try:
        payload: dict[str, Any] = {
            "input": input,
            "input_type": input_type,
            "include_law": True,
        }
        if zones:
            payload["zones"] = zones
        async with await _worker_client() as client:
            resp = await client.post(
                "/land/analyze",
                json=payload,
                timeout=httpx.Timeout(float(timeout), connect=10.0),
            )
            resp.raise_for_status()
            result["quick_result"] = resp.json()
    except httpx.ConnectError:
        return _dumps({"error": f"Worker not reachable at {WORKER_URL}"})
    except Exception as e:
        return _dumps({"error": f"Analysis failed: {e}"})

    # Build report from quick_result
    qr = result.get("quick_result", {})
    regs = qr.get("regulations") or {}
    bcr = regs.get("bcr", {})
    far = regs.get("far", {})
    zone_info = qr.get("zone_info") or {}
    zone_list = zone_info.get("zones", [])
    restrictions = qr.get("restrictions", [])
    law_count = (qr.get("law_articles") or {}).get("total_count", 0)

    result["report"] = (
        f"토지 규제 분석 결과\n"
        f"용도지역: {', '.join(zone_list) if zone_list else '미확인'}\n"
        f"건폐율: {bcr.get('limit_pct', '?')}%\n"
        f"용적률: {far.get('limit_pct', '?')}%\n"
        f"규제 {len(restrictions)}개, 법조항 {law_count}개\n"
    )

    return _dumps(result)


@mcp.tool()
async def arr_land_resolve(
    input: str,
    input_type: str = "address",
) -> str:
    """Resolve address to PNU code or validate an existing PNU.

    Args:
        input: Address string or PNU code to resolve/validate
        input_type: "address" (geocode to PNU) or "pnu" (validate)

    Returns:
        JSON with resolved PNU info
    """
    try:
        async with await _worker_client() as client:
            resp = await client.post(
                "/land/resolve",
                json={"input": input, "input_type": input_type},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Worker not reachable at {WORKER_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def arr_land_zones() -> str:
    """List all 21 zoning types with their building regulation limits.

    Returns:
        JSON list of zones with bcr_limit (건폐율) and far_limit (용적률)
    """
    try:
        async with await _worker_client() as client:
            resp = await client.get("/land/zones")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Worker not reachable at {WORKER_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def arr_land_stats() -> str:
    """Get land regulation query statistics.

    Returns:
        JSON with service info and uptime
    """
    try:
        async with await _worker_client() as client:
            resp = await client.get("/health")
            resp.raise_for_status()
            data = resp.json()
            data["source"] = "worker"
            return _dumps(data)
    except httpx.ConnectError:
        return _dumps({"error": f"Worker not reachable at {WORKER_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# ===============================================================
# 3. Message Bus (5)
# ===============================================================


@mcp.tool()
async def send_message(
    to_agent: str,
    message: str,
    from_agent: str = "mcp_client",
) -> str:
    """Send a message to an agent via the Message Bus.

    Args:
        to_agent: Target agent name
        message: Message content
        from_agent: Sender name (default: mcp_client)

    Returns:
        JSON status from Message Bus
    """
    try:
        async with await _bus_client() as client:
            resp = await client.post(
                "/send",
                json={"from_agent": from_agent, "to_agent": to_agent, "message": message},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Message Bus not reachable at {MESSAGE_BUS_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def broadcast_message(
    message: str,
    from_agent: str = "mcp_client",
) -> str:
    """Broadcast a message to ALL connected agents via the Message Bus.

    Args:
        message: Message content
        from_agent: Sender name (default: mcp_client)

    Returns:
        JSON status from Message Bus
    """
    try:
        async with await _bus_client() as client:
            resp = await client.post(
                "/broadcast",
                json={"from_agent": from_agent, "message": message},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Message Bus not reachable at {MESSAGE_BUS_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_conversation_log(limit: int = 100) -> str:
    """Get full conversation history from the Message Bus (all agents).

    Args:
        limit: Maximum number of messages to return (default 100)

    Returns:
        JSON array of dialogue events [{timestamp, from_agent, to_agent, message, event_type}]
    """
    try:
        async with await _bus_client() as client:
            resp = await client.get("/log", params={"limit": limit})
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Message Bus not reachable at {MESSAGE_BUS_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_agent_conversation(agent1: str, agent2: str) -> str:
    """Get conversation history between two specific agents.

    Args:
        agent1: First agent name
        agent2: Second agent name

    Returns:
        JSON array of dialogue events between the two agents
    """
    try:
        async with await _bus_client() as client:
            resp = await client.get(f"/conversation/{agent1}/{agent2}")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Message Bus not reachable at {MESSAGE_BUS_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_bus_status() -> str:
    """Get Message Bus status: connected agents list, message count.

    Returns:
        JSON with service name, connected_agents list, log_count
    """
    try:
        async with await _bus_client() as client:
            resp = await client.get("/status")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"Message Bus not reachable at {MESSAGE_BUS_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# ===============================================================
# 4. SharedMemory (4)
# ===============================================================


@mcp.tool()
async def store_decision(
    category: str,
    decision_json: str,
    agent: str = "mcp_client",
) -> str:
    """Store an architectural decision in SharedMemory.

    Args:
        category: Decision category (schema, api_spec, types, etc.)
        decision_json: Decision content as JSON string
        agent: Agent name storing the decision

    Returns:
        Stored decision with version info
    """
    try:
        decision = json.loads(decision_json)
        async with await _mem_client() as client:
            resp = await client.post(
                "/decision",
                json={"category": category, "decision": decision, "agent": agent},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except json.JSONDecodeError as e:
        return _dumps({"error": f"Invalid JSON in decision_json: {e}"})
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_all_decisions() -> str:
    """Get all shared decisions from SharedMemory.

    Returns:
        JSON dict of {category: {value, updated_by, updated_at, version}}
    """
    try:
        async with await _mem_client() as client:
            resp = await client.get("/decisions")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def publish_event(
    event_type: str,
    data_json: str,
    source: str = "mcp_client",
) -> str:
    """Publish an event to SharedMemory (notifies all subscribed agents).

    Common event types: schema_ready, api_ready, file_changed, task_done.

    Args:
        event_type: Event type string
        data_json: Event payload as JSON string
        source: Source agent name

    Returns:
        Published event with event_id and timestamp
    """
    try:
        data = json.loads(data_json)
        async with await _mem_client() as client:
            resp = await client.post(
                "/event",
                json={"event_type": event_type, "data": data, "source": source},
            )
            resp.raise_for_status()
            return _dumps(resp.json())
    except json.JSONDecodeError as e:
        return _dumps({"error": f"Invalid JSON in data_json: {e}"})
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def get_events(event_type: str = "", limit: int = 100) -> str:
    """Get event history from SharedMemory with optional type filter.

    Args:
        event_type: Filter by event type (empty = all events)
        limit: Maximum events to return

    Returns:
        JSON array of events [{event_id, event_type, data, source, timestamp}]
    """
    try:
        params: dict[str, Any] = {"limit": limit}
        if event_type:
            params["event_type"] = event_type
        async with await _mem_client() as client:
            resp = await client.get("/events", params=params)
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.ConnectError:
        return _dumps({"error": f"SharedMemory not reachable at {SHARED_MEMORY_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# ===============================================================
# 5. Utility (2)
# ===============================================================


@mcp.tool()
async def health_check() -> str:
    """Check AG-light server health (Worker + Bus + Memory).

    Returns:
        JSON with status of each component
    """
    result: dict[str, Any] = {"server": "ag-light", "status": True}

    # Check Worker
    try:
        async with await _worker_client() as client:
            resp = await client.get("/health")
            resp.raise_for_status()
            result["worker"] = {"status": True, "url": WORKER_URL, "data": resp.json()}
    except Exception as e:
        result["worker"] = {"status": False, "url": WORKER_URL, "error": str(e)}
        result["status"] = False

    # Check Bus
    try:
        async with await _bus_client() as client:
            resp = await client.get("/status")
            resp.raise_for_status()
            result["bus"] = {"status": True, "url": MESSAGE_BUS_URL}
    except Exception as e:
        result["bus"] = {"status": False, "url": MESSAGE_BUS_URL, "error": str(e)}

    # Check Memory
    try:
        async with await _mem_client() as client:
            resp = await client.get("/status")
            resp.raise_for_status()
            result["memory"] = {"status": True, "url": SHARED_MEMORY_URL}
    except Exception as e:
        result["memory"] = {"status": False, "url": SHARED_MEMORY_URL, "error": str(e)}

    return _dumps(result)


@mcp.tool()
async def get_version() -> str:
    """Get AG-light server version.

    Returns:
        JSON with version string and tool count
    """
    return _dumps({
        "server": "AG-light",
        "version": "1.0.0",
        "tools": 20,
        "worker_url": WORKER_URL,
    })
