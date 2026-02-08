"""
Pytest Configuration and Shared Fixtures for AG/Auto-Claude CLI Unit Tests
==========================================================================

Provides fixtures for testing the 4-layer CLI architecture:
  - Coordinator: TaskQueue, Orchestrator
  - Pipeline: Sequential, Parallel, CriticLoop
  - Adapters: AutoClaude, AGAutogen, A2A, LawDomain, AutogenStudio
  - Registry + Memory: AgentRegistry, SharedMemory

Fixtures:
  - temp_db_path / task_queue: SQLite-backed TaskQueue for tests
  - sample_task: Factory for Task objects with configurable params
  - mock_registry: AgentRegistry pre-loaded with mock adapters
  - mock_settings: Patches get_settings() with safe test defaults
  - MockAdapter: Configurable mock adapter class
  - mock_oauth_token: Patches get_oauth_token() to return a fake token
  - mock_claude_sdk / mock_no_sdk: SDK availability patches
  - HTTP mock fixtures for all external services
"""

import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path manipulation: ensure AG/Auto-Claude/src is importable
# ---------------------------------------------------------------------------
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# ---------------------------------------------------------------------------
# Pre-mock external SDK modules that may not be installed
# ---------------------------------------------------------------------------
if "claude_agent_sdk" not in sys.modules:
    _sdk_mock = MagicMock()
    _sdk_mock.ClaudeAgentOptions = MagicMock
    _sdk_mock.ClaudeSDKClient = MagicMock
    sys.modules["claude_agent_sdk"] = _sdk_mock

# ---------------------------------------------------------------------------
# Project imports (after path setup)
# ---------------------------------------------------------------------------
from src.utils.models import (  # noqa: E402
    AgentMcpConfig,
    AgentType,
    McpServerConfig,
    Pipeline,
    Priority,
    Result,
    ResultStatus,
    Stage,
    StageType,
    Task,
    TaskType,
)
from src.coordinator.task_queue import TaskQueue, TaskStatus  # noqa: E402
from src.registry.agent_registry import (  # noqa: E402
    AgentRegistry,
    AgentStatus,
    get_registry,
    reset_registry,
)
from src.utils.config import Settings, get_settings  # noqa: E402
from src.agents.auto_claude.base import (  # noqa: E402
    get_oauth_token,
    CLAUDE_SDK_AVAILABLE,
)


# ===========================================================================
# MockAdapter -- a configurable mock that satisfies the AgentAdapter protocol
# ===========================================================================

class MockAdapter:
    """
    A lightweight mock adapter for unit tests.

    Satisfies the AgentAdapter interface without inheriting from it so that
    tests do not trigger real HTTP clients or SharedMemory connections.

    Args:
        name: Adapter identifier (should match an AgentType value).
        capabilities: List of capability strings this adapter advertises.
        health: Whether health_check() returns True.
        result_status: Default ResultStatus returned by execute().
        result_output: Default output payload returned by execute().
        result_error: Default error message (used when result_status != SUCCESS).
        execute_side_effect: Optional callable/exception to raise on execute().
    """

    def __init__(
        self,
        name: str = "mock_adapter",
        capabilities: Optional[List[str]] = None,
        health: bool = True,
        result_status: ResultStatus = ResultStatus.SUCCESS,
        result_output: Any = None,
        result_error: Optional[str] = None,
        execute_side_effect: Any = None,
    ):
        self.name = name
        self.endpoint_url = f"http://localhost:9999/{name}"
        self._capabilities = capabilities or ["mock-capability"]
        self._health = health
        self._result_status = result_status
        self._result_output = result_output if result_output is not None else {
            "summary": f"Mock output from {name}",
        }
        self._result_error = result_error
        self._execute_side_effect = execute_side_effect
        self._is_initialized = False

        # Tracking
        self.execute_call_count = 0
        self.last_task: Optional[Task] = None
        self.last_context: Optional[Dict[str, Any]] = None

    async def initialize(self) -> None:
        self._is_initialized = True

    async def shutdown(self) -> None:
        self._is_initialized = False

    async def execute(
        self,
        task: Task,
        context: Dict[str, Any],
        mcp_config: Optional[AgentMcpConfig] = None,
    ) -> Result:
        self.execute_call_count += 1
        self.last_task = task
        self.last_context = context

        if self._execute_side_effect is not None:
            if callable(self._execute_side_effect):
                return self._execute_side_effect(task, context)
            raise self._execute_side_effect

        return Result(
            task_id=task.id,
            status=self._result_status,
            output=self._result_output,
            error=self._result_error,
            agent_used=self.name,
            execution_time_ms=42,
        )

    async def health_check(self) -> bool:
        return self._health

    def get_capabilities(self) -> List[str]:
        return list(self._capabilities)


# ===========================================================================
# Fixture: temp_db_path
# ===========================================================================

@pytest.fixture()
def temp_db_path(tmp_path: Path) -> Path:
    """
    Provide a temporary SQLite database path for TaskQueue.

    Uses pytest's built-in ``tmp_path`` so cleanup is automatic.
    """
    return tmp_path / "test_tasks.db"


# ===========================================================================
# Fixture: task_queue
# ===========================================================================

@pytest.fixture()
def task_queue(temp_db_path: Path) -> TaskQueue:
    """
    Return an initialized TaskQueue backed by a temporary SQLite DB.
    """
    queue = TaskQueue(db_path=str(temp_db_path))
    queue.initialize()
    return queue


# ===========================================================================
# Fixture: sample_task (factory)
# ===========================================================================

@pytest.fixture()
def sample_task():
    """
    Factory fixture that creates Task objects with configurable parameters.

    Usage::

        def test_something(sample_task):
            task = sample_task()                            # defaults
            task = sample_task(task_type=TaskType.QA, priority=Priority.HIGH)
            task = sample_task(description="Custom desc")
    """

    def _make_task(
        task_type: TaskType = TaskType.CODE,
        priority: Priority = Priority.MEDIUM,
        description: str = "Test task for CLI unit tests",
        **kwargs: Any,
    ) -> Task:
        return Task(
            type=task_type,
            priority=priority,
            description=description,
            **kwargs,
        )

    return _make_task


# ===========================================================================
# Fixture: mock_registry
# ===========================================================================

@pytest.fixture()
def mock_registry() -> AgentRegistry:
    """
    Return an AgentRegistry pre-populated with MockAdapters for every
    Auto-Claude and AG-Autogen agent type.

    The registry is freshly created each test (does NOT modify the global
    singleton).  Call ``reset_registry()`` in teardown if needed.
    """
    registry = AgentRegistry()
    registry.initialize()

    # Register mock adapters for Auto-Claude agents
    auto_claude_agents = [
        AgentType.AUTO_CLAUDE_PLANNER,
        AgentType.AUTO_CLAUDE_CODER,
        AgentType.AUTO_CLAUDE_QA_REVIEWER,
        AgentType.AUTO_CLAUDE_QA_FIXER,
    ]
    for agent_type in auto_claude_agents:
        adapter = MockAdapter(
            name=agent_type.value,
            capabilities=["planning", "coding", "review", "fixing"],
        )
        registry.register_adapter(agent_type, adapter)

    # Register mock adapters for AG-Autogen agents
    ag_autogen_agents = [
        AgentType.AG_RESEARCH,
        AgentType.AG_ANALYST,
        AgentType.AG_WRITER,
        AgentType.AG_REVIEWER,
        AgentType.AG_COORDINATOR,
    ]
    for agent_type in ag_autogen_agents:
        adapter = MockAdapter(
            name=agent_type.value,
            capabilities=["research", "analysis", "writing"],
        )
        registry.register_adapter(agent_type, adapter)

    return registry


# ===========================================================================
# Fixture: mock_settings
# ===========================================================================

@pytest.fixture()
def mock_settings():
    """
    Patch ``get_settings()`` to return safe defaults suitable for testing.

    Disables SharedMemory, uses short timeouts, and points queue DB to a
    temp file so tests never touch production data.

    Yields the patched Settings instance for further customisation.
    """
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()

    settings = Settings(
        enable_shared_memory=False,
        adapter_timeout=5.0,
        bridge_port=18080,
        bridge_log_level="WARNING",
        ag_autogen_url="http://localhost:19000",
        ag_law_domain_url="http://localhost:19001",
        shared_memory_url="http://localhost:19101",
        queue_db_path=temp_db.name,
        queue_max_retries=1,
        max_qa_iterations=2,
        orchestrator_poll_interval=0.1,
        stage_timeout_seconds=10,
        graphiti_enabled=False,
        anthropic_api_key="sk-ant-test-key-not-real",
    )

    with patch("src.utils.config.get_settings", return_value=settings):
        yield settings

    # Cleanup temp DB
    try:
        Path(temp_db.name).unlink(missing_ok=True)
    except Exception:
        pass


# ===========================================================================
# Fixture: mock_oauth_token
# ===========================================================================

_FAKE_OAUTH_TOKEN = "sk-ant-oat01-test-token-12345"


@pytest.fixture()
def mock_oauth_token():
    """
    Patch ``get_oauth_token()`` in ``src.agents.auto_claude.base`` to
    return a fake token.  Also patches ``require_oauth_token`` for
    consistency.

    Yields the fake token string.
    """
    with patch(
        "src.agents.auto_claude.base.get_oauth_token",
        return_value=_FAKE_OAUTH_TOKEN,
    ), patch(
        "src.agents.auto_claude.base.require_oauth_token",
        return_value=_FAKE_OAUTH_TOKEN,
    ):
        yield _FAKE_OAUTH_TOKEN


# ===========================================================================
# Fixture: mock_claude_sdk
# ===========================================================================

@pytest.fixture()
def mock_claude_sdk():
    """
    Patch ``CLAUDE_SDK_AVAILABLE = True`` and provide mock
    ``ClaudeSDKClient`` / ``ClaudeAgentOptions`` in the base agent module.

    Yields a dict with keys ``client_cls`` and ``options_cls`` pointing to
    the mocked classes so tests can configure return values.
    """
    mock_client_cls = MagicMock(name="MockClaudeSDKClient")
    mock_options_cls = MagicMock(name="MockClaudeAgentOptions")

    # Make the mock client support async context manager
    mock_instance = MagicMock()
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)
    mock_instance.query = AsyncMock()

    # receive_response returns an async iterator
    async def _receive_response():
        msg = MagicMock()
        msg.__class__.__name__ = "AssistantMessage"
        msg.content = [MagicMock(text="Mock SDK response")]
        yield msg

    mock_instance.receive_response = _receive_response
    mock_client_cls.return_value = mock_instance

    with patch(
        "src.agents.auto_claude.base.CLAUDE_SDK_AVAILABLE", True
    ), patch(
        "src.agents.auto_claude.base.ClaudeSDKClient", mock_client_cls
    ), patch(
        "src.agents.auto_claude.base.ClaudeAgentOptions", mock_options_cls
    ):
        yield {
            "client_cls": mock_client_cls,
            "client_instance": mock_instance,
            "options_cls": mock_options_cls,
        }


# ===========================================================================
# Fixture: mock_no_sdk
# ===========================================================================

@pytest.fixture()
def mock_no_sdk():
    """
    Patch ``CLAUDE_SDK_AVAILABLE = False`` so that code paths handling
    missing SDK are exercised.
    """
    with patch(
        "src.agents.auto_claude.base.CLAUDE_SDK_AVAILABLE", False
    ), patch(
        "src.agents.auto_claude.base.ClaudeSDKClient", None
    ), patch(
        "src.agents.auto_claude.base.ClaudeAgentOptions", None
    ):
        yield


# ===========================================================================
# HTTP Mock Helpers
# ===========================================================================

def _make_json_response(
    data: Any,
    status_code: int = 200,
) -> MagicMock:
    """
    Create a mock httpx.Response with JSON payload.

    Args:
        data: JSON-serializable data for ``response.json()``.
        status_code: HTTP status code.

    Returns:
        MagicMock that behaves like ``httpx.Response``.
    """
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = data
    response.text = str(data)
    response.is_success = 200 <= status_code < 300
    response.raise_for_status = MagicMock()
    if status_code >= 400:
        import httpx as _httpx

        response.raise_for_status.side_effect = _httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=response,
        )
    return response


# ===========================================================================
# Fixture: mock_a2a_server
# ===========================================================================

@pytest.fixture()
def mock_a2a_server():
    """
    Patch ``httpx.AsyncClient`` so that A2A adapter calls receive
    canned responses instead of hitting real A2A agent servers
    (ports 8003-8120).

    Yields a dict of ``AsyncMock`` objects keyed by HTTP method
    (``post``, ``get``) for assertion and customisation.
    """
    mock_post = AsyncMock(
        return_value=_make_json_response({
            "jsonrpc": "2.0",
            "result": {
                "artifacts": [
                    {
                        "parts": [
                            {"type": "text", "text": "Mock A2A response text"}
                        ]
                    }
                ]
            },
            "id": "mock-id",
        })
    )

    mock_get = AsyncMock(
        return_value=_make_json_response({
            "name": "mock_a2a_agent",
            "description": "A mock A2A agent for testing",
            "capabilities": ["mock"],
        })
    )

    mock_client_instance = MagicMock()
    mock_client_instance.post = mock_post
    mock_client_instance.get = mock_get
    mock_client_instance.aclose = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        yield {
            "post": mock_post,
            "get": mock_get,
            "client": mock_client_instance,
        }


# ===========================================================================
# Fixture: mock_ag_autogen_server
# ===========================================================================

@pytest.fixture()
def mock_ag_autogen_server():
    """
    Patch ``httpx.AsyncClient`` to mock the AG Autogen HTTP server
    (default port 8000).

    Yields a dict of mocks for post/get requests.
    """
    mock_post = AsyncMock(
        return_value=_make_json_response({
            "jsonrpc": "2.0",
            "result": {
                "output": "Mock AG Autogen analysis result",
                "agent": "ag.research",
                "confidence": 0.95,
            },
            "id": "mock-ag-autogen-id",
        })
    )

    mock_get = AsyncMock(
        return_value=_make_json_response({"status": "healthy"})
    )

    mock_client_instance = MagicMock()
    mock_client_instance.post = mock_post
    mock_client_instance.get = mock_get
    mock_client_instance.aclose = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        yield {
            "post": mock_post,
            "get": mock_get,
            "client": mock_client_instance,
        }


# ===========================================================================
# Fixture: mock_law_domain_server
# ===========================================================================

@pytest.fixture()
def mock_law_domain_server():
    """
    Patch ``httpx.AsyncClient`` to mock the AG Law Domain HTTP server
    (default port 8001).

    Yields a dict of mocks for post/get requests.
    """
    mock_post = AsyncMock(
        return_value=_make_json_response({
            "status": "completed",
            "summary": "Mock legal analysis complete",
            "cases": [{"id": "case-001", "title": "Mock v. Test"}],
            "risks": [],
            "recommendations": ["No action required"],
        })
    )

    mock_get = AsyncMock(
        return_value=_make_json_response({"status": "healthy"})
    )

    mock_client_instance = MagicMock()
    mock_client_instance.post = mock_post
    mock_client_instance.get = mock_get
    mock_client_instance.aclose = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        yield {
            "post": mock_post,
            "get": mock_get,
            "client": mock_client_instance,
        }


# ===========================================================================
# Fixture: mock_shared_memory_server
# ===========================================================================

@pytest.fixture()
def mock_shared_memory_server():
    """
    Patch ``httpx.AsyncClient`` to mock the SharedMemory HTTP server
    (default port 8101).

    Provides canned responses for decisions, events, health, and status
    endpoints.

    Yields a dict of mocks.
    """
    _decisions: Dict[str, Any] = {}

    async def _mock_post(url: str, **kwargs: Any) -> MagicMock:
        json_data = kwargs.get("json", {})

        if "/decisions/" in url:
            key = json_data.get("key", url.split("/decisions/")[-1])
            _decisions[key] = json_data
            return _make_json_response({
                "key": key,
                "data": json_data.get("data", {}),
                "source": json_data.get("source", "test"),
                "timestamp": "2026-01-01T00:00:00",
                "version": 1,
            })

        if "/events" in url:
            return _make_json_response({
                "id": "evt-mock-001",
                "event_type": json_data.get("event_type", "test"),
                "data": json_data.get("data", {}),
                "source": json_data.get("source", "test"),
                "timestamp": "2026-01-01T00:00:00",
            })

        return _make_json_response({"ok": True})

    async def _mock_get(url: str, **kwargs: Any) -> MagicMock:
        if "/health" in url:
            return _make_json_response({"status": "healthy"})

        if "/status" in url:
            return _make_json_response({
                "decisions_count": len(_decisions),
                "events_count": 0,
                "uptime_seconds": 3600,
            })

        if "/decisions" in url and "/" == url[-1:]:
            return _make_json_response({"keys": list(_decisions.keys())})

        # Individual decision lookup
        for key, value in _decisions.items():
            if key in url:
                return _make_json_response(value)

        return _make_json_response({"keys": list(_decisions.keys())})

    mock_post = AsyncMock(side_effect=_mock_post)
    mock_get = AsyncMock(side_effect=_mock_get)

    mock_client_instance = MagicMock()
    mock_client_instance.post = mock_post
    mock_client_instance.get = mock_get
    mock_client_instance.delete = AsyncMock(return_value=_make_json_response({"ok": True}))
    mock_client_instance.aclose = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        yield {
            "post": mock_post,
            "get": mock_get,
            "client": mock_client_instance,
            "decisions": _decisions,
        }


# ===========================================================================
# Fixture: mock_autogen_studio_server
# ===========================================================================

@pytest.fixture()
def mock_autogen_studio_server():
    """
    Patch ``httpx.AsyncClient`` to mock the AutoGen Studio HTTP server
    (default port 8081).

    Provides canned responses for workflow execution, session listing,
    and health endpoints.

    Yields a dict of mocks.
    """
    mock_post = AsyncMock(
        return_value=_make_json_response({
            "status": "completed",
            "workflow_name": "mock_workflow",
            "output": {
                "messages": [
                    {"role": "assistant", "content": "Mock AutoGen Studio response"}
                ],
                "summary": "Workflow executed successfully in mock mode",
            },
            "duration_seconds": 1.5,
        })
    )

    mock_get = AsyncMock(
        return_value=_make_json_response({
            "status": "healthy",
            "version": "0.4.0",
            "sessions": [],
        })
    )

    mock_client_instance = MagicMock()
    mock_client_instance.post = mock_post
    mock_client_instance.get = mock_get
    mock_client_instance.aclose = AsyncMock()
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        yield {
            "post": mock_post,
            "get": mock_get,
            "client": mock_client_instance,
        }
