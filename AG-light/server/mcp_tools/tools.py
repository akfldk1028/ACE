# AG-light MCP Tools — Slim version (26 tools)
# Wraps Cloudflare Worker APIs + in-process Message Bus / SharedMemory
"""
Slim MCP tool layer for AG-light.

26 tools covering:
- Law Search (4): law_search, law_search_domain, law_domains, law_health
- Land (5): arr_land_analyze, arr_land_agent_analyze, arr_land_resolve, arr_land_zones, arr_land_stats
- MAAS Evidence (2): arr_maas_evidence, arr_maas_review
- Parking/MAAS Legal Design (4): arr_parking_graph_verify, arr_parking_count_check,
  arr_parking_to_maas_layout_check, arr_maas_parking_layout_candidate
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
    ARR_BACKEND_URL     = http://127.0.0.1:18000 (ARR Django backend)
    MESSAGE_BUS_URL     = http://localhost:8200/bus   (same process)
    SHARED_MEMORY_URL   = http://localhost:8200/memory (same process)
"""
from __future__ import annotations

import json
import logging
import os
import sys
import asyncio
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# --------------- Config ---------------

WORKER_URL = os.environ.get("WORKER_URL", "http://localhost:8787")
ARR_BACKEND_URL = os.environ.get("ARR_BACKEND_URL", "http://127.0.0.1:18000").rstrip("/")
MESSAGE_BUS_URL = os.environ.get("MESSAGE_BUS_URL", "http://localhost:8200/bus")
SHARED_MEMORY_URL = os.environ.get("SHARED_MEMORY_URL", "http://localhost:8200/memory")
ARR_BACKEND_DIR = os.environ.get("ARR_BACKEND_DIR", "/mnt/d/Data/25_ACE/ARR/backend")
ARR_PYTHON = os.environ.get("ARR_PYTHON", os.path.join(ARR_BACKEND_DIR, ".venv", "bin", "python"))
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://172.27.80.1:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")

logger = logging.getLogger("ag-light-mcp")

mcp = FastMCP(
    "AG-light",
    instructions=(
        "AG-light MCP server — 26 tools: law article search (Korean legal regulations), "
        "land regulation analysis (건폐율/용적률/건축제한), MAAS evidence review, "
        "parking/legal-design checks, Message Bus conversations, SharedMemory events/decisions."
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


async def _arr_client() -> httpx.AsyncClient:
    """Short-lived httpx client for ARR Django backend calls."""
    return httpx.AsyncClient(
        base_url=ARR_BACKEND_URL,
        timeout=httpx.Timeout(60.0, connect=10.0),
        headers={"Content-Type": "application/json"},
    )


async def _bus_client() -> httpx.AsyncClient:
    """Short-lived httpx client for Message Bus calls (same process)."""
    return httpx.AsyncClient(base_url=MESSAGE_BUS_URL, timeout=5.0)


async def _mem_client() -> httpx.AsyncClient:
    """Short-lived httpx client for SharedMemory calls (same process)."""
    return httpx.AsyncClient(base_url=SHARED_MEMORY_URL, timeout=5.0)


async def _run_arr_python(args: list[str], timeout: int = 120) -> dict[str, Any]:
    """Run an ARR backend Python command and return captured output."""
    python_exe = ARR_PYTHON if os.path.exists(ARR_PYTHON) else sys.executable
    proc: asyncio.subprocess.Process | None = None
    try:
        proc = await asyncio.create_subprocess_exec(
            python_exe,
            *args,
            cwd=ARR_BACKEND_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "command": [python_exe, *args],
            "stdout": stdout_b.decode("utf-8", errors="replace"),
            "stderr": stderr_b.decode("utf-8", errors="replace"),
        }
    except asyncio.TimeoutError:
        if proc and proc.returncode is None:
            proc.kill()
            await proc.wait()
        return {"ok": False, "error": f"ARR command timed out after {timeout}s", "args": args}
    except FileNotFoundError as e:
        return {"ok": False, "error": str(e), "python": python_exe, "arr_backend_dir": ARR_BACKEND_DIR}
    except Exception as e:
        return {"ok": False, "error": str(e), "args": args}


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
# 3. MAAS Evidence (2)
# ===============================================================


@mcp.tool()
async def arr_maas_evidence(job_id: str, design_id: int) -> str:
    """Fetch the canonical ARR MAAS evidence bundle for one saved design candidate.

    This calls ARR Django:
    GET /design/jobs/{job_id}/results/{design_id}/evidence/

    Args:
        job_id: ARR design OptimizationJob UUID
        design_id: Saved DesignResult design_id, e.g. 900000

    Returns:
        JSON evidence bundle following schema_version arr.maas.evidence.v0.
        Missing legal/program/parking/VWorld evidence remains needs_evidence.
    """
    try:
        async with await _arr_client() as client:
            resp = await client.get(f"/design/jobs/{job_id}/results/{int(design_id)}/evidence/")
            resp.raise_for_status()
            return _dumps(resp.json())
    except httpx.HTTPStatusError as e:
        return _dumps({
            "error": f"ARR Backend HTTP {e.response.status_code}",
            "url": f"{ARR_BACKEND_URL}/design/jobs/{job_id}/results/{design_id}/evidence/",
            "body": e.response.text[:500],
        })
    except httpx.ConnectError:
        return _dumps({"error": f"ARR Backend not reachable at {ARR_BACKEND_URL}"})
    except Exception as e:
        return _dumps({"error": str(e)})


@mcp.tool()
async def arr_maas_review(job_id: str, design_id: int) -> str:
    """Summarize the ARR MAAS evidence bundle for agent review.

    This tool does not invent new legal pass/fail results. It reads the bundle's
    checks, issues, and final_decision, then returns a compact review summary.

    Args:
        job_id: ARR design OptimizationJob UUID
        design_id: Saved DesignResult design_id

    Returns:
        JSON summary with final_status, hard_failures, missing_evidence,
        open_issues, and domain status counts.
    """
    try:
        raw = await arr_maas_evidence(job_id, design_id)
        bundle = json.loads(raw)
        if bundle.get("error"):
            return _dumps(bundle)

        checks = bundle.get("checks") or []
        issues = bundle.get("issues") or []
        final_decision = bundle.get("final_decision") or {}
        counts: dict[str, dict[str, int]] = {}
        hard_failures = []
        missing_evidence = []
        for check in checks:
            domain = str(check.get("domain") or "unknown")
            status = str(check.get("status") or "unknown")
            counts.setdefault(domain, {})
            counts[domain][status] = counts[domain].get(status, 0) + 1
            key = str(check.get("key") or check.get("id") or "")
            if status == "fail" and check.get("severity") == "hard":
                hard_failures.append(key)
            if status in {"needs_evidence", "unknown"}:
                missing_evidence.append(key)

        return _dumps({
            "schema_version": bundle.get("schema_version"),
            "bundle_id": bundle.get("bundle_id"),
            "candidate": bundle.get("candidate", {}),
            "final_status": final_decision.get("status"),
            "hard_failures": final_decision.get("blocking_failures") or hard_failures,
            "missing_evidence": final_decision.get("missing_evidence") or missing_evidence,
            "open_issues": [
                {
                    "id": issue.get("id"),
                    "title": issue.get("title"),
                    "severity": issue.get("severity"),
                    "assignee": issue.get("assignee"),
                }
                for issue in issues
                if issue.get("status") == "open"
            ],
            "domain_status_counts": counts,
            "non_negotiable": "Do not mark final pass while hard failures or needs_evidence checks remain.",
        })
    except json.JSONDecodeError as e:
        return _dumps({"error": f"ARR evidence response was not JSON: {e}"})
    except Exception as e:
        return _dumps({"error": str(e)})


# ===============================================================
# 4. Parking / MAAS Legal Design (4)
# ===============================================================


@mcp.tool()
async def arr_parking_graph_verify(timeout: int = 120) -> str:
    """Verify ARR parking law Graph DB coverage.

    Runs:
    law/scripts/verify_parking_law_graph.py

    Returns stdout/stderr and pass/fail status. This checks law roots,
    parking requirement rules, Seoul ordinance overrides, accessibility rules,
    and small attached-parking layout rules.
    """
    result = await _run_arr_python(
        [
            "law/scripts/verify_parking_law_graph.py",
            "--uri", NEO4J_URI,
            "--user", NEO4J_USER,
            "--password", NEO4J_PASSWORD,
        ],
        timeout=timeout,
    )
    return _dumps(result)


@mcp.tool()
async def arr_parking_count_check(timeout: int = 120) -> str:
    """Run deterministic parking-count scenarios against the ARR law Graph DB.

    Covers Seoul ordinance overrides, national fallback, note-6 rounding,
    delegated housing rules, and accessible parking count status.
    """
    result = await _run_arr_python(
        [
            "law/scripts/check_parking_counts.py",
            "--uri", NEO4J_URI,
            "--user", NEO4J_USER,
            "--password", NEO4J_PASSWORD,
        ],
        timeout=timeout,
    )
    return _dumps(result)


@mcp.tool()
async def arr_parking_to_maas_layout_check(timeout: int = 120) -> str:
    """Run Graph DB -> parking count -> MAAS layout candidate integration checks.

    This proves that selected parking rules can produce required counts and
    deterministic stall polygon candidates for MAAS review.
    """
    result = await _run_arr_python(
        [
            "law/scripts/check_parking_to_maas_layout.py",
            "--uri", NEO4J_URI,
            "--user", NEO4J_USER,
            "--password", NEO4J_PASSWORD,
        ],
        timeout=timeout,
    )
    return _dumps(result)


@mcp.tool()
async def arr_maas_parking_layout_candidate(
    required_spaces: int,
    envelope_width_m: float,
    envelope_depth_m: float,
    accessible_spaces: int = 0,
    strategy: str = "ground_surface",
    road_width_m: float | None = None,
    has_sidewalk_separation: bool | None = None,
    is_dead_end_road: bool = False,
    timeout: int = 30,
) -> str:
    """Generate a deterministic MAAS parking layout candidate with stall coordinates.

    This does not claim final legal compliance. It creates a first coordinate
    candidate for agents to review before a future grid/MIP solver.
    """
    road_context = {
        "road_width_m": road_width_m,
        "has_sidewalk_separation": has_sidewalk_separation,
        "is_dead_end_road": is_dead_end_road,
    }
    snippet = (
        "import json\n"
        "from shapely.geometry import box\n"
        "from design.maas.parking_layout import generate_parking_layout_candidate\n"
        f"road_context = {json.dumps(road_context, ensure_ascii=False)!r}\n"
        "road_context = json.loads(road_context)\n"
        "road_context = {k: v for k, v in road_context.items() if v is not None}\n"
        "layout = generate_parking_layout_candidate(\n"
        f"    box(0, 0, {float(envelope_width_m)}, {float(envelope_depth_m)}),\n"
        f"    required_spaces={int(required_spaces)},\n"
        f"    accessible_spaces={int(accessible_spaces)},\n"
        f"    strategy={json.dumps(strategy)},\n"
        "    road_context=road_context,\n"
        ")\n"
        "print(json.dumps(layout, ensure_ascii=False, indent=2))\n"
    )
    result = await _run_arr_python(["-c", snippet], timeout=timeout)
    if result.get("ok"):
        try:
            result["layout"] = json.loads(result.get("stdout") or "{}")
        except json.JSONDecodeError:
            pass
    return _dumps(result)


# ===============================================================
# 5. Message Bus (5)
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
# 5. SharedMemory (4)
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
# 7. Utility (2)
# ===============================================================


@mcp.tool()
async def health_check() -> str:
    """Check AG-light server health (Worker + ARR Backend + Bus + Memory).

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

    # Check ARR Backend
    try:
        async with await _arr_client() as client:
            resp = await client.get("/design/jobs/")
            # 405/404 still proves the backend is reachable; connection failure is what matters here.
            result["arr_backend"] = {
                "status": resp.status_code < 500,
                "url": ARR_BACKEND_URL,
                "http_status": resp.status_code,
            }
            if resp.status_code >= 500:
                result["status"] = False
    except Exception as e:
        result["arr_backend"] = {"status": False, "url": ARR_BACKEND_URL, "error": str(e)}
        result["status"] = False

    # Check Bus
    try:
        async with await _bus_client() as client:
            resp = await client.get("/status")
            resp.raise_for_status()
            result["bus"] = {"status": True, "url": MESSAGE_BUS_URL}
    except Exception as e:
        result["bus"] = {"status": False, "url": MESSAGE_BUS_URL, "error": str(e)}
        result["status"] = False

    # Check Memory
    try:
        async with await _mem_client() as client:
            resp = await client.get("/status")
            resp.raise_for_status()
            result["memory"] = {"status": True, "url": SHARED_MEMORY_URL}
    except Exception as e:
        result["memory"] = {"status": False, "url": SHARED_MEMORY_URL, "error": str(e)}
        result["status"] = False

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
        "tools": 26,
        "worker_url": WORKER_URL,
        "arr_backend_url": ARR_BACKEND_URL,
        "arr_backend_dir": ARR_BACKEND_DIR,
    })
