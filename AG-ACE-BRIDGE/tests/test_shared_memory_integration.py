"""
SharedMemory Integration Test for AG-ACE-BRIDGE

Verifies orchestrator properly integrates with SharedMemory (AG-CLI 8101).
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.coordinator.orchestrator import Orchestrator, OrchestratorState
from src.utils.models import Task, TaskType, Priority, Result, ResultStatus, AgentType
from src.memory import SharedMemoryClient


class TestSharedMemoryIntegration:
    """Test SharedMemory integration in Orchestrator"""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator with temp db"""
        db_path = str(tmp_path / "test_tasks.db")
        return Orchestrator(db_path=db_path)

    @pytest.fixture
    def sample_task(self):
        """Create sample task"""
        return Task(
            id="test-task-001",
            type=TaskType.CODE,
            description="Test task for SharedMemory integration",
            priority=Priority.MEDIUM,
        )

    @pytest.mark.asyncio
    async def test_shared_memory_initialization(self, orchestrator):
        """Test SharedMemory client initialization"""
        # Mock SharedMemoryClient
        with patch.object(
            SharedMemoryClient, 'health_check',
            new_callable=AsyncMock, return_value=True
        ):
            await orchestrator._initialize_shared_memory()

            # Should have created client if enabled
            if orchestrator._enable_shared_memory:
                assert orchestrator._shared_memory is not None

    @pytest.mark.asyncio
    async def test_shared_memory_disabled(self, orchestrator):
        """Test SharedMemory skipped when disabled"""
        orchestrator._enable_shared_memory = False
        await orchestrator._initialize_shared_memory()

        assert orchestrator._shared_memory is None

    @pytest.mark.asyncio
    async def test_shared_memory_connection_failure(self, orchestrator):
        """Test graceful handling when SharedMemory unavailable"""
        orchestrator._enable_shared_memory = True

        with patch.object(
            SharedMemoryClient, 'health_check',
            new_callable=AsyncMock, return_value=False
        ):
            await orchestrator._initialize_shared_memory()

            # Should be None if health check fails
            assert orchestrator._shared_memory is None

    @pytest.mark.asyncio
    async def test_share_stage_result(self, orchestrator, sample_task):
        """Test stage result sharing to SharedMemory"""
        # Setup mock SharedMemoryClient
        mock_client = AsyncMock(spec=SharedMemoryClient)
        orchestrator._shared_memory = mock_client

        # Create mock stage and result
        mock_stage = MagicMock()
        mock_stage.agent = AgentType.AUTO_CLAUDE_CODER

        result = Result(
            task_id=sample_task.id,
            status=ResultStatus.SUCCESS,
            output={"code": "print('hello')"},
        )

        # Call share method
        await orchestrator._share_stage_result(
            task=sample_task,
            stage_index=0,
            stage=mock_stage,
            result=result,
        )

        # Verify calls
        mock_client.store_task_result.assert_called_once()
        mock_client.notify_stage_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_task_complete_success(self, orchestrator, sample_task):
        """Test task completion sharing for success"""
        mock_client = AsyncMock(spec=SharedMemoryClient)
        orchestrator._shared_memory = mock_client

        output = {"final": "result"}

        await orchestrator._share_task_complete(
            task=sample_task,
            success=True,
            output=output,
        )

        mock_client.notify_task_complete.assert_called_once_with(
            task_id=sample_task.id,
            success=True,
            artifacts=output,
        )

    @pytest.mark.asyncio
    async def test_share_task_complete_failure(self, orchestrator, sample_task):
        """Test task completion sharing for failure"""
        mock_client = AsyncMock(spec=SharedMemoryClient)
        orchestrator._shared_memory = mock_client

        await orchestrator._share_task_complete(
            task=sample_task,
            success=False,
        )

        mock_client.notify_task_complete.assert_called_once_with(
            task_id=sample_task.id,
            success=False,
            artifacts={},
        )

    @pytest.mark.asyncio
    async def test_share_failure_does_not_affect_task(self, orchestrator, sample_task):
        """Test that SharedMemory errors don't fail the task"""
        mock_client = AsyncMock(spec=SharedMemoryClient)
        mock_client.store_task_result.side_effect = Exception("Network error")
        orchestrator._shared_memory = mock_client

        mock_stage = MagicMock()
        mock_stage.agent = AgentType.AUTO_CLAUDE_CODER

        result = Result(
            task_id=sample_task.id,
            status=ResultStatus.SUCCESS,
            output={"code": "test"},
        )

        # Should not raise exception
        await orchestrator._share_stage_result(
            task=sample_task,
            stage_index=0,
            stage=mock_stage,
            result=result,
        )
        # Test passes if no exception raised

    @pytest.mark.asyncio
    async def test_shutdown_closes_shared_memory(self, orchestrator):
        """Test SharedMemory closed on shutdown"""
        mock_client = AsyncMock(spec=SharedMemoryClient)
        orchestrator._shared_memory = mock_client

        await orchestrator._shutdown()

        mock_client.close.assert_called_once()


class TestSharedMemoryClientMethods:
    """Test SharedMemoryClient convenience methods"""

    @pytest.fixture
    def client(self):
        """Create mock SharedMemoryClient"""
        return SharedMemoryClient(
            base_url="http://localhost:8101",
            source_name="test-client",
        )

    @pytest.mark.asyncio
    async def test_store_task_result(self, client):
        """Test store_task_result method"""
        with patch.object(client, 'store', new_callable=AsyncMock) as mock_store:
            await client.store_task_result(
                task_id="task-001",
                stage=0,
                result={"data": "value"},
                agent_type="auto_claude_coder",
            )

            mock_store.assert_called_once()
            call_args = mock_store.call_args
            assert "task-001" in call_args[0][0]  # key contains task_id
            assert call_args[0][1]["data"] == "value"  # result stored

    @pytest.mark.asyncio
    async def test_notify_stage_complete(self, client):
        """Test notify_stage_complete method"""
        with patch.object(client, 'publish_event', new_callable=AsyncMock) as mock_publish:
            await client.notify_stage_complete(
                task_id="task-001",
                stage=0,
                agent_type="auto_claude_coder",
                success=True,
            )

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert call_args[0][0] == "stage_completed"

    @pytest.mark.asyncio
    async def test_notify_task_complete(self, client):
        """Test notify_task_complete method"""
        with patch.object(client, 'publish_event', new_callable=AsyncMock) as mock_publish:
            await client.notify_task_complete(
                task_id="task-001",
                success=True,
                artifacts={"output": "result"},
            )

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert call_args[0][0] == "task_completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
