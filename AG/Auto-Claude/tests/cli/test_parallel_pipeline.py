"""Tests for AG-ACE-BRIDGE parallel pipeline module."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pipeline.parallel import ParallelPipeline
from src.utils.models import Task, TaskType, Stage, StageType, AgentType, Result, ResultStatus


class TestParallelPipeline:
    """Tests for ParallelPipeline class."""

    def test_pipeline_creation(self):
        """Should create ParallelPipeline instance."""
        pipeline = ParallelPipeline()
        assert pipeline is not None

    @pytest.mark.asyncio
    async def test_execute_returns_result(self):
        """execute() should return a Result."""
        pipeline = ParallelPipeline()

        task = Task(type=TaskType.RESEARCH, description="Research topic")
        agents = [AgentType.AG_RESEARCH, AgentType.AG_ANALYST]

        with patch.object(pipeline, 'registry') as mock_registry:
            mock_adapter = AsyncMock()
            mock_adapter.execute = AsyncMock(return_value=Result(
                status=ResultStatus.SUCCESS,
                output={"research": "data"}
            ))
            mock_registry.get_adapter.return_value = mock_adapter

            result = await pipeline.execute(task, agents)

            assert isinstance(result, Result)


class TestParallelPipelineExecution:
    """Tests for parallel execution behavior."""

    @pytest.mark.asyncio
    async def test_multiple_agents_execute(self):
        """Multiple agents should execute."""
        pipeline = ParallelPipeline()

        task = Task(type=TaskType.RESEARCH, description="Research")
        agents = [AgentType.AG_RESEARCH, AgentType.AG_ANALYST]

        call_count = 0

        async def count_calls(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return Result(status=ResultStatus.SUCCESS, output={"done": True})

        with patch.object(pipeline, 'registry') as mock_registry:
            mock_adapter = AsyncMock()
            mock_adapter.execute = count_calls
            mock_registry.get_adapter.return_value = mock_adapter

            await pipeline.execute(task, agents)

            # Should have called execute for each agent
            assert call_count >= 1

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self):
        """Should handle partial failures."""
        pipeline = ParallelPipeline()

        task = Task(type=TaskType.RESEARCH, description="Research")
        agents = [AgentType.AG_RESEARCH, AgentType.AG_ANALYST]

        results_returned = []

        async def mixed_results(*args, **kwargs):
            if len(results_returned) == 0:
                results_returned.append("success")
                return Result(status=ResultStatus.SUCCESS, output={"done": True})
            else:
                results_returned.append("failed")
                return Result(status=ResultStatus.FAILED, error="Failed")

        with patch.object(pipeline, 'registry') as mock_registry:
            mock_adapter = AsyncMock()
            mock_adapter.execute = mixed_results
            mock_registry.get_adapter.return_value = mock_adapter

            result = await pipeline.execute(task, agents)

            # Should have some result (may be partial success)
            assert result is not None


class TestParallelPipelineResultMerging:
    """Tests for result merging."""

    @pytest.mark.asyncio
    async def test_results_merged(self):
        """Results from all agents should be merged."""
        pipeline = ParallelPipeline()

        task = Task(type=TaskType.RESEARCH, description="Research")
        agents = [AgentType.AG_RESEARCH]

        with patch.object(pipeline, 'registry') as mock_registry:
            mock_adapter = AsyncMock()
            mock_adapter.execute = AsyncMock(return_value=Result(
                status=ResultStatus.SUCCESS,
                output={"key1": "value1"}
            ))
            mock_registry.get_adapter.return_value = mock_adapter

            result = await pipeline.execute(task, agents)

            assert result is not None
            assert result.output is not None


class TestParallelPipelineEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_empty_agents_list(self):
        """Should handle empty agents list."""
        pipeline = ParallelPipeline()

        task = Task(type=TaskType.RESEARCH, description="Research")
        agents = []

        result = await pipeline.execute(task, agents)

        # Should return some result
        assert result is not None

    @pytest.mark.asyncio
    async def test_single_agent(self):
        """Should handle single agent."""
        pipeline = ParallelPipeline()

        task = Task(type=TaskType.RESEARCH, description="Research")
        agents = [AgentType.AG_RESEARCH]

        with patch.object(pipeline, 'registry') as mock_registry:
            mock_adapter = AsyncMock()
            mock_adapter.execute = AsyncMock(return_value=Result(
                status=ResultStatus.SUCCESS,
                output={"result": "done"}
            ))
            mock_registry.get_adapter.return_value = mock_adapter

            result = await pipeline.execute(task, agents)

            assert result.status == ResultStatus.SUCCESS
