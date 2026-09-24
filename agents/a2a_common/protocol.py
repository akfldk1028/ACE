"""Generic A2A tool adapter (a2a-sdk 1.0): one JSON-RPC message -> one tool call.

ONE OWNER: agents/a2a_common/protocol.py. Every agent's a2a_service/protocol.py is a
byte-for-byte copy of it (each agent is its own repository, so the copy is how it
ships) and each agent's tests assert the copy still matches. Change it here, then copy.

It knows nothing about any agent: tool bodies, message prefixes and argument policies
are injected by that agent's tools.py. Wire format, task states and card layout are the
same for every agent, so one client (the Orchestrator's A2AAdapter) talks to all.
"""
from __future__ import annotations

import inspect
import json
import logging
from datetime import datetime, timezone
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
from google.protobuf.timestamp_pb2 import Timestamp

ToolFn = Callable[..., Awaitable[str]]
Parser = Callable[[str], tuple[str, dict[str, Any]]]
Binder = Callable[[ToolFn, dict[str, Any]], dict[str, Any]]


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


class ToolExecutor(AgentExecutor):
    """Routes one A2A message to one tool; the tool's JSON text is the reply verbatim.

    Unknown tool or bad arguments -> TASK_STATE_FAILED with a JSON error. A tool
    that answers `{"error": ...}` is still a completed task: the consumer decides
    (needs_evidence), the adapter never turns it into a pass or a failure.
    """

    def __init__(self, tools: dict[str, ToolFn], parser: Parser, binder: Binder, logger_name: str = "a2a.tools"):
        self.tools = tools
        self.parser = parser
        self.binder = binder
        self.logger = logging.getLogger(logger_name)

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = context.task_id
        context_id = context.context_id or str(uuid4())
        text = context.get_user_input()
        try:
            tool, args = self.parser(text)
            fn = self.tools.get(tool)
            if fn is None:
                raise ValueError(f"unknown tool {tool!r}; exposed: {', '.join(self.tools)}")
            kwargs = self.binder(fn, args)
        except Exception as exc:
            await self._emit(event_queue, task_id, context_id, TaskState.TASK_STATE_FAILED,
                             json.dumps({"error": str(exc)}, ensure_ascii=False))
            return
        self.logger.info("A2A %s %s", tool, json.dumps(kwargs, ensure_ascii=False, default=str)[:120])
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
            return
        await self._emit(event_queue, task_id, context_id, TaskState.TASK_STATE_COMPLETED, result,
                         metadata={"tool": tool, "args": kwargs})

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(TaskStatusUpdateEvent(
            task_id=context.task_id, context_id=context.context_id or str(uuid4()),
            status=TaskStatus(state=TaskState.TASK_STATE_CANCELED, timestamp=_now()),
        ))

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
                   cors: bool = False):
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
        return {"agent": agent_id, "version": version, "port": port, "tools": tools,
                "card": "/.well-known/agent-card.json", "jsonrpc": "/"}

    return app


__all__ = ["Binder", "Parser", "ToolExecutor", "ToolFn", "build_agent_card", "build_tool_app", "parse_json_message"]
