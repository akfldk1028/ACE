"""
Agent Selector for AG/Auto-Claude

Selects appropriate agents based on task requirements.
Uses capability matching and load balancing.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.utils.models import Task, TaskType, AgentType, AgentMcpConfig
from src.utils.logger import Loggers
from src.registry.agent_registry import get_registry
from src.registry.capabilities import (
    get_agents_by_task_type,
    find_best_agents,
    AgentCapabilities,
)


@dataclass
class AgentSelection:
    """Result of agent selection"""
    primary: AgentType
    alternatives: List[AgentType]
    parallel_candidates: List[AgentType]
    selection_reason: str
    confidence: float  # 0.0 to 1.0


class AgentSelector:
    """
    Intelligent agent selection.

    Selects agents based on:
    - Task type compatibility
    - Required capabilities
    - Agent availability
    - Historical performance

    Example:
        selector = AgentSelector()

        task = Task(type=TaskType.CODE, requirements=["implementation"])
        selection = selector.select(task)

        print(selection.primary)  # AgentType.AUTO_CLAUDE_CODER
    """

    def __init__(self):
        self.logger = Loggers.orchestrator()
        self.registry = get_registry()

    def select(self, task: Task) -> AgentSelection:
        """
        Select best agent(s) for a task.

        Args:
            task: Task to find agents for

        Returns:
            AgentSelection with primary and alternative agents
        """
        task_type = TaskType(task.type) if isinstance(task.type, str) else task.type

        self.logger.debug(
            "agent_selection_start",
            task_id=task.id,
            task_type=task_type.value,
            requirements=task.requirements,
        )

        # Get candidates based on capabilities
        candidates = self.registry.select_agents(task, limit=5)

        if not candidates:
            # Fallback: get any agent that supports the task type
            fallback = self._get_fallback_agent(task_type)
            return AgentSelection(
                primary=fallback,
                alternatives=[],
                parallel_candidates=[],
                selection_reason="Fallback selection (no capability matches)",
                confidence=0.3,
            )

        primary = candidates[0]
        alternatives = candidates[1:3] if len(candidates) > 1 else []

        # Determine parallel candidates if task supports it
        parallel_candidates = self._get_parallel_candidates(task, primary)

        # Calculate confidence (with MCP tools if specified in task metadata)
        required_mcp_tools = task.metadata.get("required_mcp_tools") if task.metadata else None
        confidence = self._calculate_confidence(task, primary, required_mcp_tools=required_mcp_tools)

        # Build selection reason
        reason = self._build_selection_reason(task, primary)

        selection = AgentSelection(
            primary=primary,
            alternatives=alternatives,
            parallel_candidates=parallel_candidates,
            selection_reason=reason,
            confidence=confidence,
        )

        self.logger.info(
            "agent_selected",
            task_id=task.id,
            primary=primary.value,
            alternatives=[a.value for a in alternatives],
            confidence=confidence,
        )

        return selection

    def select_for_pipeline(
        self,
        task: Task,
        pipeline_type: str = "auto",
    ) -> List[AgentType]:
        """
        Select agents for a full pipeline.

        Args:
            task: Task to build pipeline for
            pipeline_type: Type of pipeline
                - "auto": Automatically determine
                - "full_auto_claude": Complete Auto-Claude pipeline
                - "research_first": Start with research
                - "legal": Legal domain pipeline

        Returns:
            Ordered list of agents for pipeline
        """
        task_type = TaskType(task.type) if isinstance(task.type, str) else task.type

        if pipeline_type == "auto":
            pipeline_type = self._determine_pipeline_type(task)

        if pipeline_type == "full_auto_claude":
            return self._select_auto_claude_pipeline(task)
        elif pipeline_type == "research_first":
            return self._select_research_pipeline(task)
        elif pipeline_type == "legal":
            return self._select_legal_pipeline(task)
        else:
            # Default: single agent
            selection = self.select(task)
            return [selection.primary]

    def _determine_pipeline_type(self, task: Task) -> str:
        """Determine best pipeline type based on task"""
        task_type = TaskType(task.type) if isinstance(task.type, str) else task.type

        # Research tasks
        if task.needs_research or task_type == TaskType.RESEARCH:
            return "research_first"

        # Legal domain tasks
        if task.domain_validation or any(
            kw in task.description.lower()
            for kw in ["legal", "compliance", "contract", "law"]
        ):
            return "legal"

        # Code tasks go to full Auto-Claude pipeline
        if task_type in [TaskType.CODE, TaskType.PLAN, TaskType.SPEC]:
            return "full_auto_claude"

        return "single"

    def _select_auto_claude_pipeline(self, task: Task) -> List[AgentType]:
        """Select full Auto-Claude pipeline"""
        return [
            AgentType.AUTO_CLAUDE_PLANNER,
            AgentType.AUTO_CLAUDE_CODER,
            AgentType.AUTO_CLAUDE_QA_REVIEWER,
            # QA Fixer handled in critic loop, not sequential
        ]

    def _select_research_pipeline(self, task: Task) -> List[AgentType]:
        """Select research-first pipeline"""
        pipeline = [AgentType.AG_RESEARCH]

        task_type = TaskType(task.type) if isinstance(task.type, str) else task.type

        # Add analysis if needed
        if "analysis" in task.requirements or "analyze" in task.description.lower():
            pipeline.append(AgentType.AG_ANALYST)

        # Continue to Auto-Claude for implementation
        if task_type in [TaskType.CODE, TaskType.PLAN]:
            pipeline.extend([
                AgentType.AUTO_CLAUDE_PLANNER,
                AgentType.AUTO_CLAUDE_CODER,
            ])

        return pipeline

    def _select_legal_pipeline(self, task: Task) -> List[AgentType]:
        """Select legal domain pipeline"""
        pipeline = []

        # Start with legal research
        pipeline.append(AgentType.AG_LEGAL_RESEARCHER)

        # Add case analysis if needed
        if "case" in task.description.lower() or "precedent" in task.description.lower():
            pipeline.append(AgentType.AG_CASE_ANALYZER)

        # Add compliance check if needed
        if "compliance" in task.description.lower() or task.domain_validation:
            pipeline.append(AgentType.AG_COMPLIANCE_CHECKER)

        # Risk assessment
        if "risk" in task.description.lower():
            pipeline.append(AgentType.AG_RISK_ASSESSOR)

        # Document drafting
        if "draft" in task.description.lower() or "document" in task.description.lower():
            pipeline.append(AgentType.AG_DOCUMENT_DRAFTER)

        return pipeline if pipeline else [AgentType.AG_LEGAL_RESEARCHER]

    def _get_fallback_agent(self, task_type: TaskType) -> AgentType:
        """Get fallback agent for task type"""
        fallbacks = {
            TaskType.RESEARCH: AgentType.AG_RESEARCH,
            TaskType.SPEC: AgentType.AUTO_CLAUDE_PLANNER,
            TaskType.PLAN: AgentType.AUTO_CLAUDE_PLANNER,
            TaskType.CODE: AgentType.AUTO_CLAUDE_CODER,
            TaskType.QA: AgentType.AUTO_CLAUDE_QA_REVIEWER,
            TaskType.FIX: AgentType.AUTO_CLAUDE_QA_FIXER,
            TaskType.VALIDATE: AgentType.AG_REVIEWER,
            TaskType.MERGE: AgentType.AUTO_CLAUDE_CODER,
            TaskType.CUSTOM: AgentType.AG_COORDINATOR,
        }
        return fallbacks.get(task_type, AgentType.AUTO_CLAUDE_CODER)

    def _get_parallel_candidates(
        self,
        task: Task,
        primary: AgentType,
    ) -> List[AgentType]:
        """Get candidates for parallel execution"""
        task_type = TaskType(task.type) if isinstance(task.type, str) else task.type

        # Research tasks can use multiple research agents
        if task_type == TaskType.RESEARCH:
            return [
                AgentType.AG_RESEARCH,
                AgentType.AG_ANALYST,
            ]

        # Validation can use multiple reviewers
        if task_type == TaskType.VALIDATE:
            return [
                AgentType.AG_REVIEWER,
                AgentType.AUTO_CLAUDE_QA_REVIEWER,
            ]

        return []

    def _calculate_confidence(
        self,
        task: Task,
        agent: AgentType,
        required_mcp_tools: Optional[List[str]] = None,
    ) -> float:
        """
        Calculate selection confidence.

        Args:
            task: Task being evaluated
            agent: Candidate agent
            required_mcp_tools: MCP tools required by the task (optional)

        Returns:
            Confidence score 0.0 to 1.0
        """
        status = self.registry.get_status(agent)
        capabilities = self.registry.get_capabilities(agent)

        if not status or not capabilities:
            return 0.5

        confidence = 0.5

        # Boost for availability
        if status.is_available and status.is_healthy:
            confidence += 0.2

        # Boost for success rate
        confidence += status.success_rate * 0.2

        # Boost for requirement match
        if task.requirements:
            match_score = capabilities.matches_requirements(task.requirements)
            confidence += match_score * 0.1

        # MCP tool availability scoring
        if required_mcp_tools:
            mcp_score = self._calculate_mcp_score(agent, required_mcp_tools)
            confidence += mcp_score * 0.15

        return min(confidence, 1.0)

    def _calculate_mcp_score(
        self,
        agent: AgentType,
        required_tools: List[str],
    ) -> float:
        """
        Calculate MCP tool availability score for an agent.

        Checks if the agent has access to the required MCP tools
        via its assigned MCP servers.

        Args:
            agent: Agent to check
            required_tools: List of required MCP tool names

        Returns:
            Score 0.0 to 1.0 based on tool coverage
        """
        if not required_tools:
            return 0.0

        agent_info = self.registry.get_agent_info(agent)
        if not agent_info:
            return 0.0

        available_tools = set(getattr(agent_info, 'mcp_tools', []))
        if not available_tools:
            return 0.0

        matched = sum(1 for t in required_tools if t in available_tools)
        return matched / len(required_tools)

    def _build_selection_reason(self, task: Task, agent: AgentType) -> str:
        """Build human-readable selection reason"""
        capabilities = self.registry.get_capabilities(agent)

        if not capabilities:
            return "Selected as best available"

        task_type = TaskType(task.type) if isinstance(task.type, str) else task.type

        reasons = [f"Supports task type: {task_type.value}"]

        if task.requirements:
            matched = []
            for cap in capabilities.capabilities:
                for req in task.requirements:
                    if req.lower() in cap.name.lower() or any(
                        req.lower() in kw for kw in cap.keywords
                    ):
                        matched.append(cap.name)
                        break
            if matched:
                reasons.append(f"Matches requirements: {', '.join(matched)}")

        status = self.registry.get_status(agent)
        if status and status.is_available:
            reasons.append("Currently available")

        return "; ".join(reasons)


# Global selector instance
_selector: Optional[AgentSelector] = None


def get_selector() -> AgentSelector:
    """Get or create global selector"""
    global _selector
    if _selector is None:
        _selector = AgentSelector()
    return _selector
