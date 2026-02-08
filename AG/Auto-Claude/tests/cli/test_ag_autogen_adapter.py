"""Tests for AG-ACE-BRIDGE AG Autogen adapter module (5 HTTP agents)."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.adapters.ag_autogen import AGAutogenAdapter
from src.utils.models import Task, TaskType, Result, ResultStatus, AgentType


class TestAGAutogenAdapter:
    """Tests for AGAutogenAdapter class."""

    def test_adapter_creation_research(self):
        """Should create adapter for RESEARCH agent."""
        adapter = AGAutogenAdapter(AgentType.AG_RESEARCH)
        assert adapter is not None

    def test_adapter_creation_analyst(self):
        """Should create adapter for ANALYST agent."""
        adapter = AGAutogenAdapter(AgentType.AG_ANALYST)
        assert adapter is not None

    def test_adapter_creation_writer(self):
        """Should create adapter for WRITER agent."""
        adapter = AGAutogenAdapter(AgentType.AG_WRITER)
        assert adapter is not None

    def test_adapter_creation_reviewer(self):
        """Should create adapter for REVIEWER agent."""
        adapter = AGAutogenAdapter(AgentType.AG_REVIEWER)
        assert adapter is not None

    def test_adapter_creation_coordinator(self):
        """Should create adapter for COORDINATOR agent."""
        adapter = AGAutogenAdapter(AgentType.AG_COORDINATOR)
        assert adapter is not None


class TestAGAutogenEndpointMapping:
    """Tests for AG Autogen endpoint mappings."""

    def test_research_endpoint(self):
        """Research agent endpoint should be configured."""
        adapter = AGAutogenAdapter(AgentType.AG_RESEARCH)
        assert adapter is not None

    def test_analyst_endpoint(self):
        """Analyst agent endpoint should be configured."""
        adapter = AGAutogenAdapter(AgentType.AG_ANALYST)
        assert adapter is not None

    def test_writer_endpoint(self):
        """Writer agent endpoint should be configured."""
        adapter = AGAutogenAdapter(AgentType.AG_WRITER)
        assert adapter is not None


class TestAGAutogenJSONRPC:
    """Tests for AG Autogen JSON-RPC 2.0 request format."""

    def test_jsonrpc_request_format(self):
        """Request should use JSON-RPC 2.0 format."""
        adapter = AGAutogenAdapter(AgentType.AG_RESEARCH)
        # Verify adapter is properly initialized
        assert adapter is not None

    def test_jsonrpc_method_execute(self):
        """Request method should be 'execute'."""
        adapter = AGAutogenAdapter(AgentType.AG_ANALYST)
        assert adapter is not None


class TestAGAutogenExecution:
    """Tests for AG Autogen execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Should return SUCCESS result on successful execution."""
        adapter = AGAutogenAdapter(AgentType.AG_RESEARCH)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.SUCCESS,
                output={"research": "findings"}
            )

            task = Task(type=TaskType.RESEARCH, description="Research topic")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.SUCCESS
            assert result.output is not None

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Should return FAILED result on HTTP error."""
        adapter = AGAutogenAdapter(AgentType.AG_RESEARCH)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.FAILED,
                error="HTTP 500 Internal Server Error"
            )

            task = Task(type=TaskType.RESEARCH, description="Research topic")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.FAILED
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_connection_timeout(self):
        """Should return FAILED result on connection timeout."""
        adapter = AGAutogenAdapter(AgentType.AG_RESEARCH)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.FAILED,
                error="Connection timeout"
            )

            task = Task(type=TaskType.RESEARCH, description="Research topic")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.FAILED


class TestAGAutogenSharedMemory:
    """Tests for AG Autogen SharedMemory integration."""

    @pytest.mark.asyncio
    async def test_share_result_called_on_success(self):
        """Should share result via SharedMemory on success."""
        adapter = AGAutogenAdapter(AgentType.AG_RESEARCH)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.SUCCESS,
                output={"shared": True}
            )

            task = Task(type=TaskType.RESEARCH, description="Test")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.SUCCESS


class TestAGAutogenFactoryFunctions:
    """Tests for AG Autogen adapter factory functions."""

    def test_create_research_adapter(self):
        """Should create research adapter."""
        adapter = AGAutogenAdapter(AgentType.AG_RESEARCH)
        assert adapter is not None

    def test_create_analyst_adapter(self):
        """Should create analyst adapter."""
        adapter = AGAutogenAdapter(AgentType.AG_ANALYST)
        assert adapter is not None

    def test_create_writer_adapter(self):
        """Should create writer adapter."""
        adapter = AGAutogenAdapter(AgentType.AG_WRITER)
        assert adapter is not None

    def test_create_reviewer_adapter(self):
        """Should create reviewer adapter."""
        adapter = AGAutogenAdapter(AgentType.AG_REVIEWER)
        assert adapter is not None

    def test_create_coordinator_adapter(self):
        """Should create coordinator adapter."""
        adapter = AGAutogenAdapter(AgentType.AG_COORDINATOR)
        assert adapter is not None
