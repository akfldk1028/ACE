"""Generic A2A tool adapter (a2a-sdk 1.0): one JSON-RPC message -> one tool call.

ONE OWNER: agents/a2a_common/protocol.py. Every agent's a2a_service/protocol.py is a
byte-for-byte copy of it (each agent is its own repository, so the copy is how it
ships) and each agent's tests assert the copy still matches. Change it here, then copy.

It knows nothing about any agent: tool bodies, message prefixes and argument policies
are injected by that agent's tools.py. Wire format, task states and card layout are the
same for every agent, so one client (the Orchestrator's A2AAdapter) talks to all.

One transport-level fact lives here as well, because every agent needs it and none
should state it differently - **which call this is**. The caller puts a trace record on
`Message.metadata` (see the Orchestrator's `adapters/a2a.py`). `execute` reads it, logs
it, writes one full record per hop to a JSONL file, echoes it on the reply, and holds it
in `CURRENT_TRACE` for the duration of the tool so a tool that calls another agent can
forward it. Tools receive only their own `**kwargs`; the contextvar is how the record
reaches them without a signature change.

Which *code* is answering is the sibling identity.py (standard library only, so tools.py
can import it without pulling this module's SDK); this module does not import it. The
server passes the version string in as `ToolExecutor(version=...)`.
"""
from __future__ import annotations

import inspect
import json
import logging
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from google.protobuf.json_format import MessageToDict
from google.protobuf.timestamp_pb2 import Timestamp

ToolFn = Callable[..., Awaitable[str]]
Parser = Callable[[str], tuple[str, dict[str, Any]]]
Binder = Callable[[ToolFn, dict[str, Any]], dict[str, Any]]

# The inbound trace record for the call in progress, plus the A2A ids the server minted
# or accepted for it. Set by ToolExecutor.execute, visible to the tool and to anything
# the tool awaits or runs in a thread.
CURRENT_TRACE: ContextVar[dict[str, Any] | None] = ContextVar("a2a_trace", default=None)


def parse_json_message(text: str) -> tuple[str, dict[str, Any]] | None:
    """`{"tool": str, "args": object}` -> (tool, args); None when the text is not JSON."""
    raw = text.strip()
    if not raw.startswith("{"):
        return None
    body = json.loads(raw)
    tool = body.get("tool")
    args = body.get("args") or {}
    if not isinstance(tool, str) or not isinstance(args, dict):
        raise ValueError('JSON message needs {"tool": str, "args": object}')
    return tool, args


def _now() -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(datetime.now(timezone.utc))
    return ts


def _trace_of(context: RequestContext) -> dict[str, Any]:
    """The caller's trace record, or {} when the message carries none."""
    message = context.message
    if message is None:
        return {}
    try:
        trace = MessageToDict(message.metadata).get("trace")
    except Exception:
        return {}
    return trace if isinstance(trace, dict) else {}


class ToolExecutor(AgentExecutor):
    """Routes one A2A message to one tool; the tool's JSON text is the reply verbatim.

    Unknown tool or bad arguments -> TASK_STATE_FAILED with a JSON error. A tool
    that answers `{"error": ...}` is still a completed task: the consumer decides
    (needs_evidence), the adapter never turns it into a pass or a failure.
    """

    def __init__(self, tools: dict[str, ToolFn], parser: Parser, binder: Binder, logger_name: str = "a2a.tools",
                 *, version: str = "", hop_log: Path | None = None):
        self.tools = tools
        self.parser = parser
        self.binder = binder
        self.logger = logging.getLogger(logger_name)
        self.version = version
        self.hop_log = hop_log

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        context_id = context.context_id or str(uuid4())
        text = context.get_user_input()
        trace = _trace_of(context)
        token = CURRENT_TRACE.set({**trace, "a2a_task_id": task_id, "a2a_context_id": context_id})
        started = time.perf_counter()
        tool, kwargs = "", {}
        try:
            try:
                tool, args = self.parser(text)
                fn = self.tools.get(tool)
                if fn is None:
                    raise ValueError(f"unknown tool {tool!r}; exposed: {', '.join(self.tools)}")
                kwargs = self.binder(fn, args)
            except Exception as exc:
                await self._emit(event_queue, task_id, context_id, TaskState.TASK_STATE_FAILED,
                                 json.dumps({"error": str(exc)}, ensure_ascii=False))
                self._record(tool, kwargs, trace, task_id, context_id, "rejected", started, 0)
                return
            self.logger.info("A2A %s run=%s req=%s task=%s hop=%s ctx=%s args=%s", tool,
                             trace.get("run_id", ""), trace.get("request_id", ""), trace.get("task_id", ""),
                             trace.get("hop", ""), context_id,
                             json.dumps(kwargs, ensure_ascii=False, default=str)[:120])
            await event_queue.enqueue_event(TaskStatusUpdateEvent(
                task_id=task_id, context_id=context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING, timestamp=_now()),
            ))
            try:
                result = await fn(**kwargs)
            except Exception as exc:
                self.logger.exception("tool %s raised", tool)
                await self._emit(event_queue, task_id, context_id, TaskState.TASK_STATE_FAILED,
                                 json.dumps({"error": f"{type(exc).__name__}: {exc}", "tool": tool}, ensure_ascii=False))
                self._record(tool, kwargs, trace, task_id, context_id, "failed", started, 0)
                return
            await self._emit(event_queue, task_id, context_id, TaskState.TASK_STATE_COMPLETED, result,
                             metadata={"tool": tool, "args": kwargs, "trace": trace, "version": self.version})
            self._record(tool, kwargs, trace, task_id, context_id, "completed", started, len(result))
        finally:
            CURRENT_TRACE.reset(token)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(TaskStatusUpdateEvent(
            task_id=context.task_id, context_id=context.context_id or str(uuid4()),
            status=TaskStatus(state=TaskState.TASK_STATE_CANCELED, timestamp=_now()),
        ))

    def _record(self, tool: str, kwargs: dict[str, Any], trace: dict[str, Any], task_id: str,
                context_id: str, state: str, started: float, reply_bytes: int) -> None:
        """One JSON line per hop, with the full arguments the console line truncates.

        The console keeps 120 characters so a tail stays readable; this file is where a
        failed run is reconstructed. A record that cannot be written is reported and
        dropped - it never fails the call it describes.
        """
        if self.hop_log is None:
            return
        try:
            self.hop_log.parent.mkdir(parents=True, exist_ok=True)
            with self.hop_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                    "agent": self.logger.name, "version": self.version, "tool": tool, "trace": trace,
                    "a2a_task_id": task_id, "a2a_context_id": context_id, "args": kwargs,
                    "state": state, "elapsed_ms": round((time.perf_counter() - started) * 1000),
                    "reply_bytes": reply_bytes,
                }, ensure_ascii=False, default=str) + "\n")
        except Exception:
            self.logger.warning("hop log unavailable at %s", self.hop_log)

    @staticmethod
    async def _emit(event_queue: EventQueue, task_id: str, context_id: str, state: int, text: str,
                    metadata: dict[str, Any] | None = None) -> None:
        message = Message(role="ROLE_AGENT", message_id=str(uuid4()), parts=[Part(text=text)],
                          task_id=task_id, context_id=context_id)
        if metadata:
            message.metadata.update(metadata)
        await event_queue.enqueue_event(TaskStatusUpdateEvent(
            task_id=task_id, context_id=context_id,
            status=TaskStatus(state=state, message=message, timestamp=_now()),
        ))


def build_agent_card(*, name: str, description: str, tools: dict[str, ToolFn], endpoint_url: str,
                     version: str, tags: list[str], skill_prefix: str = "") -> AgentCard:
    """One skill per tool; the skill description is the tool docstring's first line."""
    skills = [AgentSkill(id=tool_name,
                         name=tool_name.replace(skill_prefix, "", 1).replace("_", " ") if skill_prefix else tool_name.replace("_", " "),
                         description=(inspect.getdoc(fn) or tool_name).splitlines()[0],
                         tags=list(tags))
              for tool_name, fn in tools.items()]
    card = AgentCard(name=name, description=description, version=version,
                     capabilities=AgentCapabilities(streaming=True, push_notifications=False),
                     default_input_modes=["text/plain", "application/json"],
                     default_output_modes=["application/json"], skills=skills)
    card.supported_interfaces.append(AgentInterface(url=endpoint_url, protocol_binding="JSONRPC"))
    return card


def build_tool_app(*, card: AgentCard, executor: ToolExecutor, agent_id: str, version: str, port: int,
                   cors: bool = False, build: dict[str, Any] | None = None):
    """FastAPI app: JSON-RPC at `/`, card at `/.well-known/agent-card.json`, `/health` listing the tools."""
    handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore())
    app = A2AFastAPIApplication(agent_card=card, http_handler=handler).build()
    if cors:
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                           allow_methods=["*"], allow_headers=["*"])
    tools = list(executor.tools)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"agent": agent_id, "version": version, "build": build or {}, "port": port, "tools": tools,
                "card": "/.well-known/agent-card.json", "jsonrpc": "/"}

    return app


__all__ = ["Binder", "CURRENT_TRACE", "Parser", "ToolExecutor", "ToolFn", "build_agent_card",
           "build_tool_app", "parse_json_message"]
