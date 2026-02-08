"""
Tests for src/registry/capabilities.py

Validates the 20-agent capability registry: agent definitions,
keyword matching, adapter grouping, task-type filtering,
and best-agent selection logic.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest

from src.utils.models import AgentType, TaskType
from src.registry.capabilities import (
    ALL_AGENT_CAPABILITIES,
    get_capabilities,
    get_agents_by_task_type,
    get_agents_by_adapter,
    find_best_agents,
    AgentCapabilities,
    Capability,
)


# ── Registry size and completeness ──────────────────────────────


class TestRegistryCompleteness:
    """Verify the registry contains all expected agents."""

    def test_all_agent_capabilities_count(self):
        """ALL_AGENT_CAPABILITIES must contain exactly 20 entries."""
        assert len(ALL_AGENT_CAPABILITIES) == 20

    def test_all_agent_types_present(self):
        """Every AgentType enum member must be a key in ALL_AGENT_CAPABILITIES."""
        for agent_type in AgentType:
            assert agent_type in ALL_AGENT_CAPABILITIES, (
                f"{agent_type} missing from ALL_AGENT_CAPABILITIES"
            )


# ── get_capabilities ────────────────────────────────────────────


class TestGetCapabilities:
    """Tests for the get_capabilities lookup function."""

    def test_get_capabilities_valid(self):
        """Returns an AgentCapabilities instance for a known AgentType."""
        caps = get_capabilities(AgentType.AUTO_CLAUDE_CODER)
        assert caps is not None
        assert isinstance(caps, AgentCapabilities)
        assert caps.agent_type == AgentType.AUTO_CLAUDE_CODER

    def test_get_capabilities_invalid(self):
        """Returns None for an unknown / fabricated key."""
        result = get_capabilities("nonexistent_agent_type")
        assert result is None


# ── Adapter type grouping ──────────────────────────────────────


class TestAdapterGrouping:
    """Verify agents are assigned the correct adapter_type string."""

    def test_auto_claude_agents_adapter_type(self):
        """Exactly 4 agents use adapter_type='auto_claude'."""
        auto_claude = [
            c for c in ALL_AGENT_CAPABILITIES.values()
            if c.adapter_type == "auto_claude"
        ]
        assert len(auto_claude) == 4

    def test_ag_agents_adapter_type(self):
        """Exactly 5 AG autogen agents use adapter_type='ag_http'."""
        ag = [
            c for c in ALL_AGENT_CAPABILITIES.values()
            if c.adapter_type == "ag_http"
        ]
        assert len(ag) == 5

    def test_law_agents_adapter_type(self):
        """Exactly 5 law-domain agents use adapter_type='ag_law'."""
        law = [
            c for c in ALL_AGENT_CAPABILITIES.values()
            if c.adapter_type == "ag_law"
        ]
        assert len(law) == 5

    def test_a2a_agents_adapter_type(self):
        """5 A2A demo agents + 1 Claude CLI Plan = 6 with adapter_type='a2a'."""
        a2a = [
            c for c in ALL_AGENT_CAPABILITIES.values()
            if c.adapter_type == "a2a"
        ]
        assert len(a2a) == 6


# ── get_agents_by_task_type ────────────────────────────────────


class TestGetAgentsByTaskType:
    """Tests for filtering agents by the tasks they support."""

    def test_get_agents_by_task_type_code(self):
        """CODE task returns agents that list CODE in supported_task_types."""
        agents = get_agents_by_task_type(TaskType.CODE)
        assert len(agents) > 0
        for agent in agents:
            assert TaskType.CODE in agent.supported_task_types

    def test_get_agents_by_task_type_research(self):
        """RESEARCH task returns the expected research-capable agents."""
        agents = get_agents_by_task_type(TaskType.RESEARCH)
        assert len(agents) > 0
        agent_types = {a.agent_type for a in agents}
        assert AgentType.AG_RESEARCH in agent_types


# ── get_agents_by_adapter ─────────────────────────────────────


class TestGetAgentsByAdapter:
    """Tests for filtering agents by adapter type."""

    def test_get_agents_by_adapter_auto_claude(self):
        """Adapter filter 'auto_claude' returns exactly 4 agents."""
        agents = get_agents_by_adapter("auto_claude")
        assert len(agents) == 4
        for agent in agents:
            assert agent.adapter_type == "auto_claude"


# ── find_best_agents ──────────────────────────────────────────


class TestFindBestAgents:
    """Tests for the scored agent selection logic."""

    def test_find_best_agents_code(self):
        """CODE task with code/implement requirements ranks AUTO_CLAUDE_CODER highly."""
        best = find_best_agents(TaskType.CODE, ["code", "implement"])
        assert len(best) > 0
        # AUTO_CLAUDE_CODER should appear in the top results
        best_types = [a.agent_type for a in best]
        assert AgentType.AUTO_CLAUDE_CODER in best_types

    def test_find_best_agents_research(self):
        """RESEARCH task with 'research' requirement ranks AG_RESEARCH highly."""
        best = find_best_agents(TaskType.RESEARCH, ["research"])
        assert len(best) > 0
        best_types = [a.agent_type for a in best]
        assert AgentType.AG_RESEARCH in best_types


# ── AgentCapabilities methods ──────────────────────────────────


class TestAgentCapabilitiesMethods:
    """Tests for methods on the AgentCapabilities dataclass."""

    def test_matches_requirements_empty(self):
        """Empty requirements list returns the neutral score 0.5."""
        caps = get_capabilities(AgentType.AUTO_CLAUDE_CODER)
        score = caps.matches_requirements([])
        assert score == 0.5

    def test_matches_requirements_partial(self):
        """Partial keyword overlap yields a score strictly between 0 and 1."""
        caps = get_capabilities(AgentType.AUTO_CLAUDE_CODER)
        # "code" should match, "quantum_teleportation" should not
        score = caps.matches_requirements(["code", "quantum_teleportation"])
        assert 0.0 < score < 1.0

    def test_get_all_keywords(self):
        """get_all_keywords returns a deduplicated list (set semantics)."""
        caps = get_capabilities(AgentType.AUTO_CLAUDE_CODER)
        keywords = caps.get_all_keywords()
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Verify deduplication
        assert len(keywords) == len(set(keywords))


# ── Agent flags and invariants ─────────────────────────────────


class TestAgentFlags:
    """Tests for per-agent boolean flags and structural invariants."""

    def test_is_autonomous_flag(self):
        """AUTO_CLAUDE_CODER must be marked as autonomous."""
        caps = get_capabilities(AgentType.AUTO_CLAUDE_CODER)
        assert caps.is_autonomous is True

    def test_supported_task_types(self):
        """Every agent must support at least one TaskType."""
        for agent_type, caps in ALL_AGENT_CAPABILITIES.items():
            assert len(caps.supported_task_types) >= 1, (
                f"{agent_type} has no supported_task_types"
            )
