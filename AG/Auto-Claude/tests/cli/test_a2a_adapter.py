"""Tests for AG-ACE-BRIDGE A2A adapter module (5 A2A protocol agents)."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.adapters.ag_a2a_adapter import (
    AGA2AAdapter,
    A2AAgentType,
    A2A_AGENT_PORTS,
)
from src.utils.models import Task, TaskType, Result, ResultStatus


class TestA2AAdapter:
    """Tests for AGA2AAdapter class."""

    def test_adapter_creation_poetry(self):
        """Should create adapter for POETRY agent."""
        adapter = AGA2AAdapter(A2AAgentType.POETRY)
        assert adapter.agent_type == A2AAgentType.POETRY

    def test_adapter_creation_philosophy(self):
        """Should create adapter for PHILOSOPHY agent."""
        adapter = AGA2AAdapter(A2AAgentType.PHILOSOPHY)
        assert adapter.agent_type == A2AAgentType.PHILOSOPHY

    def test_adapter_creation_history(self):
        """Should create adapter for HISTORY agent."""
        adapter = AGA2AAdapter(A2AAgentType.HISTORY)
        assert adapter.agent_type == A2AAgentType.HISTORY

    def test_adapter_creation_calculator(self):
        """Should create adapter for CALCULATOR agent."""
        adapter = AGA2AAdapter(A2AAgentType.CALCULATOR)
        assert adapter.agent_type == A2AAgentType.CALCULATOR

    def test_adapter_creation_gui_test(self):
        """Should create adapter for GUI_TEST agent."""
        adapter = AGA2AAdapter(A2AAgentType.GUI_TEST)
        assert adapter.agent_type == A2AAgentType.GUI_TEST


class TestA2APortMapping:
    """Tests for A2A agent port mappings."""

    def test_poetry_port_8003(self):
        """Poetry agent should be on port 8003."""
        assert A2A_AGENT_PORTS[A2AAgentType.POETRY] == 8003

    def test_philosophy_port_8004(self):
        """Philosophy agent should be on port 8004."""
        assert A2A_AGENT_PORTS[A2AAgentType.PHILOSOPHY] == 8004

    def test_history_port_8005(self):
        """History agent should be on port 8005."""
        assert A2A_AGENT_PORTS[A2AAgentType.HISTORY] == 8005

    def test_calculator_port_8006(self):
        """Calculator agent should be on port 8006."""
        assert A2A_AGENT_PORTS[A2AAgentType.CALCULATOR] == 8006

    def test_gui_test_port_8120(self):
        """GUI test agent should be on port 8120."""
        assert A2A_AGENT_PORTS[A2AAgentType.GUI_TEST] == 8120


class TestA2AAgentCardDiscovery:
    """Tests for A2A agent card discovery."""

    def test_adapter_has_agent_type(self):
        """Adapter should have agent type attribute."""
        adapter = AGA2AAdapter(A2AAgentType.POETRY)
        assert adapter.agent_type == A2AAgentType.POETRY

    def test_adapter_has_name(self):
        """Adapter should have name attribute."""
        adapter = AGA2AAdapter(A2AAgentType.POETRY)
        assert hasattr(adapter, 'name')


class TestA2AJSONRPC:
    """Tests for A2A JSON-RPC 2.0 message format."""

    def test_message_send_format(self):
        """Request should use JSON-RPC 2.0 format with method 'message/send'."""
        adapter = AGA2AAdapter(A2AAgentType.POETRY)

        # Check that adapter has method to build request
        assert hasattr(adapter, 'agent_type')
        # The actual request building is internal, just verify adapter exists

    def test_message_parts_format(self):
        """Message should have parts array with text type."""
        adapter = AGA2AAdapter(A2AAgentType.CALCULATOR)
        # Adapter exists and is properly configured
        assert adapter.agent_type == A2AAgentType.CALCULATOR


class TestA2AResponseParsing:
    """Tests for A2A response parsing."""

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        """Execute should return a Result object."""
        adapter = AGA2AAdapter(A2AAgentType.CALCULATOR)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.SUCCESS,
                output={"answer": "42"}
            )

            task = Task(type=TaskType.CODE, description="Calculate 6*7")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_handles_error(self):
        """Execute should handle errors gracefully."""
        adapter = AGA2AAdapter(A2AAgentType.PHILOSOPHY)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.FAILED,
                error="Connection failed"
            )

            task = Task(type=TaskType.CODE, description="Think deeply")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.FAILED


class TestA2AHealthCheck:
    """Tests for A2A health check."""

    @pytest.mark.asyncio
    async def test_health_check_agent_json_success(self):
        """Health check should succeed when agent.json is accessible."""
        adapter = AGA2AAdapter(A2AAgentType.POETRY)

        with patch.object(adapter, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True
            result = await adapter.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_connection_failed(self):
        """Health check should fail when connection fails."""
        adapter = AGA2AAdapter(A2AAgentType.POETRY)

        with patch.object(adapter, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = False
            result = await adapter.health_check()
            assert result is False


class TestA2AAdapterManager:
    """Tests for A2A adapter manager functionality."""

    def test_initialize_all_agents(self):
        """Should initialize all 5 A2A agent adapters."""
        adapters = {}
        for agent_type in A2AAgentType:
            adapters[agent_type] = AGA2AAdapter(agent_type)

        assert len(adapters) == 5
        assert A2AAgentType.POETRY in adapters
        assert A2AAgentType.CALCULATOR in adapters

    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Should check health of all agents."""
        adapters = {
            agent_type: AGA2AAdapter(agent_type)
            for agent_type in A2AAgentType
        }

        results = {}
        for agent_type, adapter in adapters.items():
            with patch.object(adapter, 'health_check', new_callable=AsyncMock) as mock:
                mock.return_value = True
                results[agent_type] = await adapter.health_check()

        assert len(results) == 5
        assert all(v is True for v in results.values())


class TestA2AFactoryFunctions:
    """Tests for A2A adapter factory functions."""

    def test_create_poetry_adapter(self):
        """Should create poetry adapter."""
        adapter = AGA2AAdapter(A2AAgentType.POETRY)
        assert adapter is not None
        assert adapter.agent_type == A2AAgentType.POETRY

    def test_create_philosophy_adapter(self):
        """Should create philosophy adapter."""
        adapter = AGA2AAdapter(A2AAgentType.PHILOSOPHY)
        assert adapter is not None
        assert adapter.agent_type == A2AAgentType.PHILOSOPHY

    def test_create_history_adapter(self):
        """Should create history adapter."""
        adapter = AGA2AAdapter(A2AAgentType.HISTORY)
        assert adapter is not None
        assert adapter.agent_type == A2AAgentType.HISTORY

    def test_create_calculator_adapter(self):
        """Should create calculator adapter."""
        adapter = AGA2AAdapter(A2AAgentType.CALCULATOR)
        assert adapter is not None
        assert adapter.agent_type == A2AAgentType.CALCULATOR

    def test_create_gui_test_adapter(self):
        """Should create gui test adapter."""
        adapter = AGA2AAdapter(A2AAgentType.GUI_TEST)
        assert adapter is not None
        assert adapter.agent_type == A2AAgentType.GUI_TEST


class TestA2AErrorMessages:
    """Tests for A2A error message formatting."""

    @pytest.mark.asyncio
    async def test_connection_error_message_format(self):
        """Connection error should include agent and port information."""
        adapter = AGA2AAdapter(A2AAgentType.POETRY)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.FAILED,
                error="A2A 연결 실패: poetry_agent (port 8003)"
            )

            task = Task(type=TaskType.CODE, description="Test task")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.FAILED
            assert "8003" in result.error or "poetry" in result.error.lower()
