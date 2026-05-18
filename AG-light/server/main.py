# AG-light Server — FastAPI entry point
# Single process: MCP tools + Message Bus + SharedMemory + Health
"""
Integrates:
- MCP tools via streamable-http at /mcp (20 tools)
- Message Bus API at /bus/*
- SharedMemory API at /memory/*
- Health at /health

Run:
    uvicorn main:app --host 0.0.0.0 --port 8200
"""
from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import data store classes (reuse, don't rewrite)
from agents.message_bus import AgentMessageBus
from agents.shared_memory import SharedMemoryServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("ag-light")

# --------------- Shared instances ---------------

_DATA_DIR = Path(__file__).parent / "data"

bus = AgentMessageBus()
memory = SharedMemoryServer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize data stores on startup."""
    _DATA_DIR.mkdir(exist_ok=True)

    # Optionally load persisted memory
    storage_file = _DATA_DIR / "shared_memory.json"
    if storage_file.exists():
        memory.storage_path = storage_file
        memory._load()
    else:
        memory.storage_path = storage_file

    # Log path for bus
    log_file = _DATA_DIR / f"dialogue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    bus.log_path = log_file

    logger.info(f"AG-light server starting (bus log: {log_file})")
    yield
    logger.info("AG-light server shutting down")


app = FastAPI(
    title="AG-light Server",
    description="MCP tools + Message Bus + SharedMemory",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===============================================================
# Health
# ===============================================================


@app.get("/health")
async def health():
    return {
        "service": "AG-light",
        "status": True,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "bus": {"connected_agents": list(bus.connected_agents), "log_count": len(bus.log)},
            "memory": {"decisions": list(memory.decisions.keys()), "events_count": len(memory.events)},
        },
    }


# ===============================================================
# Message Bus Router (/bus/*)
# ===============================================================


class SendRequest(BaseModel):
    from_agent: str
    to_agent: str
    message: str
    metadata: Optional[dict] = None


class BroadcastRequest(BaseModel):
    from_agent: str
    message: str
    metadata: Optional[dict] = None


@app.get("/bus/status")
async def bus_status():
    return {
        "service": "AG-light Message Bus",
        "connected_agents": list(bus.connected_agents),
        "log_count": len(bus.log),
    }


@app.get("/bus/log")
async def bus_log(limit: int = 100):
    return bus.get_log(limit)


@app.get("/bus/conversation/{agent1}/{agent2}")
async def bus_conversation(agent1: str, agent2: str):
    return bus.get_conversation(agent1, agent2)


@app.post("/bus/send")
async def bus_send(req: SendRequest):
    await bus.send(req.from_agent, req.to_agent, req.message, req.metadata)
    return {"status": "sent"}


@app.post("/bus/broadcast")
async def bus_broadcast(req: BroadcastRequest):
    await bus.broadcast(req.from_agent, req.message, req.metadata)
    return {"status": "broadcast"}


# ===============================================================
# SharedMemory Router (/memory/*)
# ===============================================================


class StoreDecisionRequest(BaseModel):
    category: str
    decision: Any
    agent: str = "unknown"


class PublishEventRequest(BaseModel):
    event_type: str
    data: dict
    source: str


@app.get("/memory/status")
async def memory_status():
    return {
        "service": "AG-light SharedMemory",
        "decisions": list(memory.decisions.keys()),
        "events_count": len(memory.events),
        "locks_count": len(memory.locks),
    }


@app.post("/memory/decision")
async def memory_store_decision(req: StoreDecisionRequest):
    result = memory.store_decision(req.category, req.decision, req.agent)
    return result


@app.get("/memory/decision/{category}")
async def memory_get_decision(category: str):
    result = memory.get_decision(category)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Decision not found: {category}")
    return result


@app.get("/memory/decisions")
async def memory_get_all_decisions():
    return memory.get_all_decisions()


@app.post("/memory/event")
async def memory_publish_event(req: PublishEventRequest):
    event = memory.publish_event(req.event_type, req.data, req.source)
    return event.to_dict()


@app.get("/memory/events")
async def memory_get_events(event_type: str = None, limit: int = 100):
    return memory.get_events(event_type, limit)


# ===============================================================
# MCP mount (streamable-http at /mcp)
# ===============================================================

# Import the MCP server instance
try:
    from mcp_tools.tools import mcp as mcp_server  # noqa: E402

    try:
        mcp_app = mcp_server.streamable_http_app()
        app.mount("/mcp", mcp_app)
        logger.info("MCP tools mounted at /mcp (streamable-http)")
    except AttributeError:
        logger.warning(
            "FastMCP.streamable_http_app() not available. "
            "MCP tools available via stdio only."
        )
except ImportError as e:
    logger.warning(f"MCP tools not loaded (missing dependency: {e})")


# ===============================================================
# Main
# ===============================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8200"))
    logger.info(f"Starting AG-light server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
