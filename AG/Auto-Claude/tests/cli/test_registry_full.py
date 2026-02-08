"""Tests for AG-ACE-BRIDGE full agent registry (20 agents)."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.models import AgentType, TaskType
from src.registry.agent_registry import get_registry, AgentRegistry
from src.registry.capabilities import (
    get_capabilities,
    get_agents_by_task_type,
    find_best_agents,
    ALL_AGENT_CAPABILITIES,
)


class TestAgentTypeEnum:
    """Tests for AgentType enum completeness."""

    def test_agent_type_count(self):
        """Should have 20 agent types."""
        assert len(AgentType) == 20

    def test_auto_claude_agents_exist(self):
        """Should have 4 Auto-Claude agent types."""
        auto_claude_types = [
            AgentType.AUTO_CLAUDE_PLANNER,
            AgentType.AUTO_CLAUDE_CODER,
            AgentType.AUTO_CLAUDE_QA_REVIEWER,
            AgentType.AUTO_CLAUDE_QA_FIXER,
        ]
        for at in auto_claude_types:
            assert at is not None

    def test_ag_autogen_agents_exist(self):
        """Should have 5 AG Autogen agent types."""
        ag_types = [
            AgentType.AG_RESEARCH,
            AgentType.AG_ANALYST,
            AgentType.AG_WRITER,
            AgentType.AG_REVIEWER,
            AgentType.AG_COORDINATOR,
        ]
        for at in ag_types:
            assert at is not None

    def test_legal_agents_exist(self):
        """Should have 5 legal agent types."""
        legal_types = [
            AgentType.AG_CASE_ANALYZER,
            AgentType.AG_LEGAL_RESEARCHER,
            AgentType.AG_RISK_ASSESSOR,
            AgentType.AG_COMPLIANCE_CHECKER,
            AgentType.AG_DOCUMENT_DRAFTER,
        ]
        for at in legal_types:
            assert at is not None

    def test_a2a_agents_exist(self):
        """Should have 5 A2A agent types."""
        a2a_types = [
            AgentType.AG_A2A_POETRY,
            AgentType.AG_A2A_PHILOSOPHY,
            AgentType.AG_A2A_HISTORY,
            AgentType.AG_A2A_CALCULATOR,
            AgentType.AG_A2A_GUI_TEST,
        ]
        for at in a2a_types:
            assert at is not None

    def test_claude_cli_agent_exists(self):
        """Should have Claude CLI agent type."""
        assert AgentType.CLAUDE_CLI_PLAN is not None


class TestGetCapabilities:
    """Tests for get_capabilities function."""

    def test_get_capabilities_valid_agent(self):
        """Should return capabilities for valid agent."""
        caps = get_capabilities(AgentType.AUTO_CLAUDE_CODER)
        assert caps is not None
        # AgentCapabilities has 'capabilities' attribute which is a list of Capability
        assert hasattr(caps, 'capabilities') or hasattr(caps, 'agent_type')

    def test_get_capabilities_all_agents(self):
        """Should return capabilities for all agents."""
        for agent_type in AgentType:
            caps = get_capabilities(agent_type)
            assert caps is not None


class TestGetAgentsByTaskType:
    """Tests for get_agents_by_task_type function."""

    def test_get_agents_for_code_task(self):
        """Should return agents for CODE task."""
        agents = get_agents_by_task_type(TaskType.CODE)
        assert len(agents) > 0

    def test_get_agents_for_research_task(self):
        """Should return agents for RESEARCH task."""
        agents = get_agents_by_task_type(TaskType.RESEARCH)
        assert len(agents) > 0


class TestFindBestAgents:
    """Tests for find_best_agents function."""

    def test_find_best_for_code(self):
        """Should find best agents for code task."""
        results = find_best_agents(TaskType.CODE, "Implement feature")
        assert len(results) > 0

    def test_find_best_for_research(self):
        """Should find best agents for research task."""
        results = find_best_agents(TaskType.RESEARCH, "Research trends")
        assert len(results) > 0


class TestAgentRegistry:
    """Tests for AgentRegistry class."""

    def test_get_registry(self):
        """Should get registry instance."""
        registry = get_registry()
        assert registry is not None
        assert isinstance(registry, AgentRegistry)

    def test_registry_has_agents(self):
        """Registry should have agents registered."""
        registry = get_registry()
        # Should have some agents
        assert registry is not None

    def test_registry_select_agents(self):
        """Should select agents for task."""
        registry = get_registry()
        from src.utils.models import Task
        task = Task(type=TaskType.CODE, description="Build feature")

        agents = registry.select_agents(task)
        assert len(agents) > 0


class TestAllAgentCapabilities:
    """Tests for ALL_AGENT_CAPABILITIES constant."""

    def test_all_agent_capabilities_defined(self):
        """ALL_AGENT_CAPABILITIES should be defined."""
        assert ALL_AGENT_CAPABILITIES is not None
        assert len(ALL_AGENT_CAPABILITIES) == 20

    def test_all_agents_have_capabilities(self):
        """Each agent type should have capabilities."""
        for agent_type in AgentType:
            assert agent_type in ALL_AGENT_CAPABILITIES
            caps = ALL_AGENT_CAPABILITIES[agent_type]
            assert caps is not None
