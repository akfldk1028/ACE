"""
Tests for src/utils/models.py

Validates Pydantic data models used throughout the AG/Auto-Claude CLI:
enums (Priority, TaskType, ResultStatus, AgentType), Task, Result,
Stage, Pipeline, McpServerConfig, AgentMcpConfig, and MemorySyncEvent.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import uuid
from datetime import datetime

from src.utils.models import (
    AgentMcpConfig,
    AgentType,
    McpServerConfig,
    MemorySyncEvent,
    Pipeline,
    Priority,
    Result,
    ResultStatus,
    Stage,
    StageType,
    Task,
    TaskType,
)


# ---------------------------------------------------------------------------
# Enum value tests
# ---------------------------------------------------------------------------

class TestPriorityEnum:
    def test_priority_enum_values(self):
        """HIGH, MEDIUM, LOW map to the expected lowercase strings."""
        assert Priority.HIGH == "high"
        assert Priority.MEDIUM == "medium"
        assert Priority.LOW == "low"


class TestTaskTypeEnum:
    def test_task_type_enum_values(self):
        """All 10 TaskType members exist with correct string values."""
        expected = {
            "RESEARCH": "research",
            "SPEC": "spec",
            "PLAN": "plan",
            "PLANNING": "planning",
            "CODE": "code",
            "QA": "qa",
            "FIX": "fix",
            "VALIDATE": "validate",
            "MERGE": "merge",
            "CUSTOM": "custom",
        }
        assert len(TaskType) == 10
        for name, value in expected.items():
            member = TaskType[name]
            assert member.value == value, f"TaskType.{name} should be '{value}'"


class TestResultStatusEnum:
    def test_result_status_enum_values(self):
        """ResultStatus contains SUCCESS, FAILED, NEEDS_RETRY, PARTIAL, CANCELLED."""
        assert ResultStatus.SUCCESS == "success"
        assert ResultStatus.FAILED == "failed"
        assert ResultStatus.NEEDS_RETRY == "needs_retry"
        assert ResultStatus.PARTIAL == "partial"
        assert ResultStatus.CANCELLED == "cancelled"
        assert len(ResultStatus) == 5


class TestAgentTypeEnum:
    def test_agent_type_enum_count(self):
        """There are exactly 20 agent types registered."""
        # 4 auto_claude + 5 ag + 5 law + 5 a2a + 1 claude_cli = 20
        assert len(AgentType) == 20

    def test_agent_type_auto_claude_agents(self):
        """4 auto_claude.* agents are defined."""
        auto_claude = [m for m in AgentType if m.value.startswith("auto_claude.")]
        assert len(auto_claude) == 4
        values = {m.value for m in auto_claude}
        assert values == {
            "auto_claude.planner",
            "auto_claude.coder",
            "auto_claude.qa_reviewer",
            "auto_claude.qa_fixer",
        }

    def test_agent_type_ag_agents(self):
        """5 ag.* (non-law, non-a2a) agents are defined."""
        ag_core = [
            m for m in AgentType
            if m.value.startswith("ag.")
            and not m.value.startswith("ag.a2a.")
            and m.value not in {
                "ag.case_analyzer",
                "ag.legal_researcher",
                "ag.risk_assessor",
                "ag.compliance_checker",
                "ag.document_drafter",
            }
        ]
        assert len(ag_core) == 5
        values = {m.value for m in ag_core}
        assert values == {
            "ag.research",
            "ag.analyst",
            "ag.writer",
            "ag.reviewer",
            "ag.coordinator",
        }

    def test_agent_type_law_agents(self):
        """5 law-domain agents (case_analyzer, legal_researcher, etc.) are defined."""
        law_values = {
            "ag.case_analyzer",
            "ag.legal_researcher",
            "ag.risk_assessor",
            "ag.compliance_checker",
            "ag.document_drafter",
        }
        law_agents = [m for m in AgentType if m.value in law_values]
        assert len(law_agents) == 5

    def test_agent_type_a2a_agents(self):
        """5 ag.a2a.* protocol agents are defined."""
        a2a = [m for m in AgentType if m.value.startswith("ag.a2a.")]
        assert len(a2a) == 5
        values = {m.value for m in a2a}
        assert values == {
            "ag.a2a.poetry_agent",
            "ag.a2a.philosophy_agent",
            "ag.a2a.history_agent",
            "ag.a2a.calculator_agent",
            "ag.a2a.gui_test_agent",
        }


# ---------------------------------------------------------------------------
# Task model tests
# ---------------------------------------------------------------------------

class TestTaskModel:
    def test_task_creation_defaults(self):
        """Task(type=CODE) fills in a UUID id, MEDIUM priority, and empty dicts."""
        task = Task(type=TaskType.CODE)

        # id should be a valid UUID-4 string
        parsed = uuid.UUID(task.id)
        assert parsed.version == 4

        # use_enum_values means the stored value is the raw string
        assert task.priority == "medium"
        assert task.description == ""
        assert task.input == {}
        assert task.context == {}
        assert task.requirements == []
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert task.parent_task_id is None
        assert isinstance(task.created_at, datetime)

    def test_task_creation_custom(self):
        """All custom fields are stored correctly."""
        task = Task(
            id="custom-id-123",
            type=TaskType.RESEARCH,
            description="Investigate OAuth providers",
            priority=Priority.HIGH,
            input={"query": "oauth2"},
            context={"project": "test"},
            requirements=["must support Google"],
            needs_research=True,
            domain_validation=True,
            parent_task_id="parent-000",
            retry_count=1,
            max_retries=5,
            metadata={"source": "cli"},
        )

        assert task.id == "custom-id-123"
        assert task.type == "research"
        assert task.description == "Investigate OAuth providers"
        assert task.priority == "high"
        assert task.input == {"query": "oauth2"}
        assert task.context == {"project": "test"}
        assert task.requirements == ["must support Google"]
        assert task.needs_research is True
        assert task.domain_validation is True
        assert task.parent_task_id == "parent-000"
        assert task.retry_count == 1
        assert task.max_retries == 5
        assert task.metadata == {"source": "cli"}


# ---------------------------------------------------------------------------
# Result model tests
# ---------------------------------------------------------------------------

class TestResultModel:
    def test_result_success_shorthand(self):
        """Result(success=True) converts to status=SUCCESS via model_validator."""
        result = Result(success=True)
        assert result.status == "success"

    def test_result_failure_shorthand(self):
        """Result(success=False) converts to status=FAILED via model_validator."""
        result = Result(success=False)
        assert result.status == "failed"

    def test_result_success_property(self):
        """result.success returns True when status is SUCCESS."""
        result_ok = Result(status=ResultStatus.SUCCESS)
        assert result_ok.success is True

        result_fail = Result(status=ResultStatus.FAILED)
        assert result_fail.success is False

        result_partial = Result(status=ResultStatus.PARTIAL)
        assert result_partial.success is False


# ---------------------------------------------------------------------------
# Stage & Pipeline tests
# ---------------------------------------------------------------------------

class TestStageModel:
    def test_stage_creation(self):
        """Stage with agent and stage_type gets sensible defaults."""
        stage = Stage(
            agent=AgentType.AUTO_CLAUDE_CODER,
            stage_type=StageType.SEQUENTIAL,
        )

        parsed = uuid.UUID(stage.id)
        assert parsed.version == 4
        assert stage.agent == "auto_claude.coder"
        assert stage.stage_type == "sequential"
        assert stage.timeout_seconds == 300
        assert stage.retry_on_failure is True
        assert stage.parallel_agents == []
        assert stage.critic_loop is False
        assert stage.max_iterations == 5
        assert stage.mcp_config is None


class TestPipelineModel:
    def test_pipeline_creation(self):
        """Pipeline with a task_id and stages list is constructed correctly."""
        stage = Stage(
            agent=AgentType.AUTO_CLAUDE_PLANNER,
            stage_type=StageType.SEQUENTIAL,
        )
        pipeline = Pipeline(task_id="task-999", stages=[stage])

        parsed = uuid.UUID(pipeline.id)
        assert parsed.version == 4
        assert pipeline.task_id == "task-999"
        assert len(pipeline.stages) == 1
        assert pipeline.current_stage_index == 0
        assert pipeline.is_complete is False
        assert pipeline.accumulated_context == {}
        assert isinstance(pipeline.created_at, datetime)


# ---------------------------------------------------------------------------
# MCP configuration tests
# ---------------------------------------------------------------------------

class TestMcpServerConfig:
    def test_mcp_server_config(self):
        """McpServerConfig stores both stdio and SSE fields."""
        cfg = McpServerConfig(
            id="server-1",
            name="Test MCP",
            server_type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            env={"HOME": "/tmp"},
            auto_connect=False,
            priority="required",
        )
        assert cfg.id == "server-1"
        assert cfg.name == "Test MCP"
        assert cfg.server_type == "stdio"
        assert cfg.command == "npx"
        assert cfg.args == ["-y", "@modelcontextprotocol/server-filesystem"]
        assert cfg.env == {"HOME": "/tmp"}
        assert cfg.url is None
        assert cfg.headers == {}
        assert cfg.auto_connect is False
        assert cfg.priority == "required"

        # SSE variant
        sse_cfg = McpServerConfig(
            id="server-2",
            name="Remote SSE",
            server_type="sse",
            url="https://mcp.example.com/sse",
            headers={"Authorization": "Bearer tok"},
        )
        assert sse_cfg.url == "https://mcp.example.com/sse"
        assert sse_cfg.command is None


class TestAgentMcpConfig:
    def test_agent_mcp_config_has_servers(self):
        """has_servers property and get_required_servers() filter correctly."""
        # Empty config
        empty = AgentMcpConfig()
        assert empty.has_servers is False
        assert empty.get_required_servers() == []

        # With servers
        required_srv = McpServerConfig(
            id="r1", name="Required", server_type="stdio",
            command="node", priority="required",
        )
        optional_srv = McpServerConfig(
            id="o1", name="Optional", server_type="sse",
            url="http://localhost:3000", priority="optional",
        )
        config = AgentMcpConfig(
            servers=[required_srv, optional_srv],
            tools=["read", "write"],
        )
        assert config.has_servers is True
        required = config.get_required_servers()
        assert len(required) == 1
        assert required[0].id == "r1"


# ---------------------------------------------------------------------------
# MemorySyncEvent test
# ---------------------------------------------------------------------------

class TestMemorySyncEvent:
    def test_memory_sync_event(self):
        """MemorySyncEvent is created with correct fields and defaults."""
        event = MemorySyncEvent(
            source="graphiti",
            event_type="insert",
            entity_type="task",
            entity_id="ent-42",
            data={"name": "test entity"},
        )

        parsed = uuid.UUID(event.id)
        assert parsed.version == 4
        assert event.source == "graphiti"
        assert event.event_type == "insert"
        assert event.entity_type == "task"
        assert event.entity_id == "ent-42"
        assert event.data == {"name": "test entity"}
        assert isinstance(event.timestamp, datetime)
        assert event.synced is False
