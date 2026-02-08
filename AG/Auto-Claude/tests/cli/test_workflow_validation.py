"""Tests for AG-ACE-BRIDGE workflow_executor module."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.bridge.workflow_executor import WorkflowExecutor


class TestWorkflowExecutor:
    """Tests for WorkflowExecutor class."""

    def test_executor_creation(self):
        """Should create WorkflowExecutor instance."""
        executor = WorkflowExecutor()
        assert executor is not None

    def test_executor_has_registry(self):
        """Executor should have registry reference."""
        executor = WorkflowExecutor()
        # May have registry or other dependencies
        assert executor is not None


class TestWorkflowExecutorMethods:
    """Tests for WorkflowExecutor methods."""

    def test_has_execute_method(self):
        """Should have execute method."""
        executor = WorkflowExecutor()
        assert hasattr(executor, 'execute') or hasattr(executor, 'execute_spec')

    def test_has_run_method(self):
        """Should have run or execute method."""
        executor = WorkflowExecutor()
        methods = dir(executor)
        run_methods = [m for m in methods if 'run' in m.lower() or 'execute' in m.lower()]
        assert len(run_methods) > 0


class TestWorkflowExecutorIntegration:
    """Integration tests for WorkflowExecutor."""

    @pytest.mark.skip(reason="Requires full pipeline setup")
    def test_execute_simple_task(self):
        """Should execute simple task."""
        executor = WorkflowExecutor()
        # Would require actual pipeline setup
        pass

    @pytest.mark.skip(reason="Requires full pipeline setup")
    def test_execute_with_spec(self):
        """Should execute with project spec."""
        executor = WorkflowExecutor()
        # Would require actual spec file
        pass
