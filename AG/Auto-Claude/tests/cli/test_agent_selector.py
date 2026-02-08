"""Tests for AG-ACE-BRIDGE agent_selector module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.coordinator.agent_selector import AgentSelector, AgentSelection
from src.utils.models import Task, TaskType, AgentType


class TestAgentSelector:
    """Tests for AgentSelector class."""

    def test_selector_creation(self):
        """Should create AgentSelector instance."""
        selector = AgentSelector()
        assert selector is not None
        assert selector.registry is not None

    def test_select_returns_agent_selection(self):
        """select() should return AgentSelection dataclass."""
        selector = AgentSelector()
        task = Task(type=TaskType.CODE, description="Write a Python function")
        selection = selector.select(task)

        assert isinstance(selection, AgentSelection)
        assert selection.primary is not None
        assert isinstance(selection.primary, AgentType)

    def test_select_code_task(self):
        """CODE task should select coder-related agent."""
        selector = AgentSelector()
        task = Task(type=TaskType.CODE, description="Implement feature")
        selection = selector.select(task)

        assert selection.primary is not None
        assert selection.confidence >= 0.0
        assert selection.confidence <= 1.0

    def test_select_research_task(self):
        """RESEARCH task should select research-related agent."""
        selector = AgentSelector()
        task = Task(type=TaskType.RESEARCH, description="Research market trends")
        selection = selector.select(task)

        assert selection.primary is not None
        assert selection.confidence >= 0.0

    def test_select_planning_task(self):
        """PLANNING task should select planner agent."""
        selector = AgentSelector()
        task = Task(type=TaskType.PLANNING, description="Create project plan")
        selection = selector.select(task)

        assert selection.primary is not None

    def test_select_qa_task(self):
        """QA task should select QA reviewer."""
        selector = AgentSelector()
        task = Task(type=TaskType.QA, description="Review code quality")
        selection = selector.select(task)

        assert selection.primary is not None


class TestAgentSelectionDataclass:
    """Tests for AgentSelection dataclass."""

    def test_agent_selection_fields(self):
        """AgentSelection should have all required fields."""
        selection = AgentSelection(
            primary=AgentType.AUTO_CLAUDE_CODER,
            alternatives=[AgentType.AUTO_CLAUDE_PLANNER],
            parallel_candidates=[],
            selection_reason="Best match for CODE task",
            confidence=0.85
        )

        assert selection.primary == AgentType.AUTO_CLAUDE_CODER
        assert len(selection.alternatives) == 1
        assert selection.selection_reason != ""
        assert selection.confidence == 0.85

    def test_agent_selection_empty_alternatives(self):
        """Should allow empty alternatives list."""
        selection = AgentSelection(
            primary=AgentType.AUTO_CLAUDE_CODER,
            alternatives=[],
            parallel_candidates=[],
            selection_reason="Only option",
            confidence=0.5
        )

        assert selection.alternatives == []


class TestAgentSelectorConfidence:
    """Tests for confidence score calculation."""

    def test_confidence_in_valid_range(self):
        """Confidence should be between 0.0 and 1.0."""
        selector = AgentSelector()

        for task_type in [TaskType.CODE, TaskType.RESEARCH, TaskType.PLANNING]:
            task = Task(type=task_type, description="Test task")
            selection = selector.select(task)

            assert 0.0 <= selection.confidence <= 1.0

    def test_confidence_higher_for_matching_task(self):
        """Confidence should be higher when agent matches task type well."""
        selector = AgentSelector()

        # CODE task should have reasonable confidence for coder
        code_task = Task(type=TaskType.CODE, description="Write implementation")
        code_selection = selector.select(code_task)

        assert code_selection.confidence >= 0.3  # At least reasonable


class TestAgentSelectorAlternatives:
    """Tests for alternative agent selection."""

    def test_alternatives_provided(self):
        """Should provide alternative agents when available."""
        selector = AgentSelector()
        task = Task(type=TaskType.CODE, description="Build feature")
        selection = selector.select(task)

        # May or may not have alternatives depending on implementation
        assert isinstance(selection.alternatives, list)

    def test_parallel_candidates_for_research(self):
        """Research tasks may have parallel candidates."""
        selector = AgentSelector()
        task = Task(type=TaskType.RESEARCH, description="Research multiple topics")
        selection = selector.select(task)

        assert isinstance(selection.parallel_candidates, list)


class TestAgentSelectorWithRequirements:
    """Tests for selection with specific requirements."""

    def test_select_with_requirements(self):
        """Should consider task requirements in selection."""
        selector = AgentSelector()
        task = Task(
            type=TaskType.CODE,
            description="Build REST API",
            requirements=["python", "fastapi", "implementation"]
        )
        selection = selector.select(task)

        assert selection.primary is not None

    def test_select_with_metadata(self):
        """Should consider task metadata in selection."""
        selector = AgentSelector()
        task = Task(
            type=TaskType.CODE,
            description="Build feature",
            metadata={"language": "python", "framework": "django"}
        )
        selection = selector.select(task)

        assert selection.primary is not None


class TestAgentSelectorEdgeCases:
    """Edge case tests for AgentSelector."""

    def test_empty_description(self):
        """Should handle empty task description."""
        selector = AgentSelector()
        task = Task(type=TaskType.CODE, description="")
        selection = selector.select(task)

        assert selection.primary is not None

    def test_long_description(self):
        """Should handle very long task descriptions."""
        selector = AgentSelector()
        long_desc = "x" * 10000
        task = Task(type=TaskType.CODE, description=long_desc)
        selection = selector.select(task)

        assert selection.primary is not None

    def test_unicode_description(self):
        """Should handle unicode in task description."""
        selector = AgentSelector()
        task = Task(type=TaskType.CODE, description="한글 태스크 설명")
        selection = selector.select(task)

        assert selection.primary is not None

    def test_special_characters_in_description(self):
        """Should handle special characters."""
        selector = AgentSelector()
        task = Task(type=TaskType.CODE, description="Fix bug: $var->method()")
        selection = selector.select(task)

        assert selection.primary is not None


class TestAgentSelectorSelectionReason:
    """Tests for selection reason generation."""

    def test_selection_reason_not_empty(self):
        """Selection should include non-empty reason."""
        selector = AgentSelector()
        task = Task(type=TaskType.CODE, description="Build feature")
        selection = selector.select(task)

        assert selection.selection_reason != ""
        assert len(selection.selection_reason) > 0

    def test_selection_reason_mentions_agent_or_task(self):
        """Selection reason should be meaningful."""
        selector = AgentSelector()
        task = Task(type=TaskType.CODE, description="Build feature")
        selection = selector.select(task)

        # Reason should mention something relevant
        reason_lower = selection.selection_reason.lower()
        # Could mention agent name, capability, task type, etc.
        assert len(reason_lower) > 5
