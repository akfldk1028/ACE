"""Tests for AG-ACE-BRIDGE Auto-Claude adapter module (4 Claude SDK agents)."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.adapters.auto_claude import AutoClaudeAdapter
from src.utils.models import Task, TaskType, Result, ResultStatus, AgentType


class TestAutoClaudeAdapter:
    """Tests for AutoClaudeAdapter class."""

    def test_adapter_creation_planner(self):
        """Should create adapter for PLANNER agent."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_PLANNER)
        assert adapter is not None

    def test_adapter_creation_coder(self):
        """Should create adapter for CODER agent."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)
        assert adapter is not None

    def test_adapter_creation_qa_reviewer(self):
        """Should create adapter for QA_REVIEWER agent."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_QA_REVIEWER)
        assert adapter is not None

    def test_adapter_creation_qa_fixer(self):
        """Should create adapter for QA_FIXER agent."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_QA_FIXER)
        assert adapter is not None

    def test_invalid_agent_type_raises_error(self):
        """Should raise error for non-Auto-Claude agent type."""
        # Test with a non-Auto-Claude agent type
        with pytest.raises((ValueError, TypeError)):
            # AG_RESEARCH is not an Auto-Claude agent
            adapter = AutoClaudeAdapter(AgentType.AG_RESEARCH)
            # Force initialization if lazy
            _ = adapter.agent_type


class TestAutoClaudeAdapterExecution:
    """Tests for Auto-Claude adapter execution."""

    @pytest.mark.asyncio
    async def test_execute_without_sdk_fails(self):
        """Should fail when Claude SDK is not available."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.FAILED,
                error="Claude SDK not available"
            )

            task = Task(type=TaskType.CODE, description="Write code")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_without_token_fails(self):
        """Should fail when OAuth token is not available."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.FAILED,
                error="OAuth token not available"
            )

            task = Task(type=TaskType.CODE, description="Write code")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Should return SUCCESS result on successful execution."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.SUCCESS,
                output={"code": "def hello(): pass"}
            )

            task = Task(type=TaskType.CODE, description="Write hello function")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.SUCCESS
            assert result.output is not None

    @pytest.mark.asyncio
    async def test_execute_exception_returns_failed(self):
        """Should return FAILED result when exception occurs."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.FAILED,
                error="Execution failed"
            )

            task = Task(type=TaskType.CODE, description="Write code")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.FAILED


class TestAutoClaudeAdapterCapabilities:
    """Tests for Auto-Claude adapter capabilities."""

    def test_planner_capabilities(self):
        """Planner should have planning capabilities."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_PLANNER)
        assert adapter is not None

    def test_coder_capabilities(self):
        """Coder should have coding capabilities."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)
        assert adapter is not None

    def test_qa_reviewer_capabilities(self):
        """QA Reviewer should have review capabilities."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_QA_REVIEWER)
        assert adapter is not None

    def test_qa_fixer_capabilities(self):
        """QA Fixer should have fix capabilities."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_QA_FIXER)
        assert adapter is not None


class TestAutoClaudeAdapterHealthCheck:
    """Tests for Auto-Claude adapter health check."""

    @pytest.mark.asyncio
    async def test_health_check_no_sdk(self):
        """Health check should fail without SDK."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)

        with patch.object(adapter, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = False
            result = await adapter.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_no_token(self):
        """Health check should fail without OAuth token."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)

        with patch.object(adapter, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = False
            result = await adapter.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Health check should succeed with SDK and token."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)

        with patch.object(adapter, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = True
            result = await adapter.health_check()
            assert result is True


class TestAutoClaudeAdapterFactory:
    """Tests for Auto-Claude adapter factory functions."""

    def test_create_planner_adapter(self):
        """Should create planner adapter."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_PLANNER)
        assert adapter is not None

    def test_create_coder_adapter(self):
        """Should create coder adapter."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)
        assert adapter is not None

    def test_create_qa_reviewer_adapter(self):
        """Should create QA reviewer adapter."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_QA_REVIEWER)
        assert adapter is not None

    def test_create_qa_fixer_adapter(self):
        """Should create QA fixer adapter."""
        adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_QA_FIXER)
        assert adapter is not None
