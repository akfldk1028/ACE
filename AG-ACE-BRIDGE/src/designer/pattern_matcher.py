"""
Pattern Matcher - Task to Pattern Matching

Matches project tasks to existing patterns in the registry.
If no suitable pattern exists, recommends creating a new one.

Usage:
    matcher = PatternMatcher(pattern_registry)

    # Match a single task
    pattern = await matcher.match_task(task)

    # Match all tasks in a project
    matches = await matcher.match_project(project)
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from src.registry.pattern_registry import PatternRegistry, RegisteredPattern, PatternType
from src.designer.project_designer import ProjectTask, ProjectSpec
from src.utils.logger import Loggers


@dataclass
class PatternMatch:
    """Result of pattern matching"""
    task_id: str
    pattern_id: Optional[str]
    pattern_name: Optional[str]
    confidence: float  # 0.0 - 1.0
    reason: str
    create_new: bool  # True if no match found, recommend creating new


class PatternMatcher:
    """
    Matches project tasks to existing patterns.

    Matching Strategy:
    1. Keyword matching (task description vs pattern tags/name)
    2. Agent type matching (task agent vs pattern agents)
    3. Pattern type matching (task type vs pattern type)
    4. Historical success rate consideration

    If no suitable pattern found (confidence < threshold),
    recommends creating a new pattern.
    """

    # Keywords for different pattern types
    PATTERN_KEYWORDS = {
        PatternType.WORKFLOW: [
            "workflow", "pipeline", "process", "sequence", "flow",
            "automate", "orchestrate", "coordinate"
        ],
        PatternType.AGENT: [
            "agent", "assistant", "helper", "worker", "executor"
        ],
        PatternType.SKILL: [
            "skill", "capability", "function", "tool", "utility"
        ],
        PatternType.TEMPLATE: [
            "template", "boilerplate", "scaffold", "starter"
        ],
    }

    # Agent to capability mapping
    AGENT_CAPABILITIES = {
        "AUTO_CLAUDE_PLANNER": ["plan", "design", "analyze", "architect", "strategy"],
        "AUTO_CLAUDE_CODER": ["code", "implement", "write", "develop", "program"],
        "AUTO_CLAUDE_QA_REVIEWER": ["review", "check", "verify", "validate", "audit"],
        "AUTO_CLAUDE_QA_FIXER": ["fix", "debug", "test", "repair", "correct"],
        "AG_RESEARCH": ["research", "search", "find", "gather", "investigate"],
        "AG_A2A_CALCULATOR": ["calculate", "compute", "math", "arithmetic"],
        "AG_A2A_POETRY": ["poem", "poetry", "creative", "literary"],
    }

    def __init__(
        self,
        registry: PatternRegistry,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize PatternMatcher.

        Args:
            registry: Pattern registry to search
            confidence_threshold: Minimum confidence to consider a match
        """
        self.registry = registry
        self.confidence_threshold = confidence_threshold
        self.logger = Loggers.orchestrator()

    async def match_task(self, task: ProjectTask) -> PatternMatch:
        """
        Match a single task to a pattern.

        Args:
            task: Project task to match

        Returns:
            PatternMatch with best match or create recommendation
        """
        patterns = self.registry.list_active()

        if not patterns:
            return PatternMatch(
                task_id=task.id,
                pattern_id=None,
                pattern_name=None,
                confidence=0.0,
                reason="No patterns available in registry",
                create_new=True,
            )

        # Score each pattern
        scored_patterns: List[Tuple[RegisteredPattern, float, str]] = []

        for pattern in patterns:
            score, reason = self._score_pattern(task, pattern)
            scored_patterns.append((pattern, score, reason))

        # Sort by score descending
        scored_patterns.sort(key=lambda x: x[1], reverse=True)

        best_pattern, best_score, best_reason = scored_patterns[0]

        if best_score >= self.confidence_threshold:
            return PatternMatch(
                task_id=task.id,
                pattern_id=best_pattern.id,
                pattern_name=best_pattern.name,
                confidence=best_score,
                reason=best_reason,
                create_new=False,
            )
        else:
            return PatternMatch(
                task_id=task.id,
                pattern_id=None,
                pattern_name=None,
                confidence=best_score,
                reason=f"Best match ({best_pattern.name}) below threshold: {best_score:.2f} < {self.confidence_threshold}",
                create_new=True,
            )

    def _score_pattern(
        self,
        task: ProjectTask,
        pattern: RegisteredPattern,
    ) -> Tuple[float, str]:
        """
        Score how well a pattern matches a task.

        Returns:
            (score, reason) tuple
        """
        score = 0.0
        reasons = []

        task_desc_lower = task.description.lower()
        pattern_name_lower = pattern.name.lower()

        # 1. Name/tag keyword matching (40% weight)
        keyword_score = 0.0
        matched_keywords = []

        # Check pattern name
        name_words = pattern_name_lower.replace("_", " ").replace("-", " ").split()
        for word in name_words:
            if word in task_desc_lower:
                keyword_score += 0.2
                matched_keywords.append(word)

        # Check pattern tags
        for tag in pattern.tags:
            if tag.lower() in task_desc_lower:
                keyword_score += 0.15
                matched_keywords.append(tag)

        keyword_score = min(keyword_score, 0.4)
        score += keyword_score

        if matched_keywords:
            reasons.append(f"Keywords: {', '.join(matched_keywords[:3])}")

        # 2. Agent type matching (30% weight)
        if task.agent_type:
            # Check if pattern data references the same agent
            pattern_agents = self._extract_agents_from_pattern(pattern)

            if task.agent_type in pattern_agents:
                score += 0.3
                reasons.append(f"Agent match: {task.agent_type}")
            elif pattern_agents:
                # Partial match - same family
                if self._same_agent_family(task.agent_type, pattern_agents):
                    score += 0.15
                    reasons.append("Agent family match")

        # 3. Pattern type inference (20% weight)
        inferred_type = self._infer_pattern_type(task.description)
        if inferred_type == pattern.pattern_type:
            score += 0.2
            reasons.append(f"Type match: {inferred_type.value}")

        # 4. Historical success (10% weight)
        if pattern.execution_count > 0:
            # Assume patterns with more executions are better
            success_bonus = min(pattern.execution_count / 100, 0.1)
            score += success_bonus
            if success_bonus > 0.05:
                reasons.append(f"Well-tested ({pattern.execution_count} runs)")

        reason = "; ".join(reasons) if reasons else "Low relevance"
        return min(score, 1.0), reason

    def _extract_agents_from_pattern(self, pattern: RegisteredPattern) -> List[str]:
        """Extract agent types referenced in pattern data"""
        agents = []
        data = pattern.data

        # Check nodes for agent references
        for node in data.get("nodes", []):
            if "agent" in node:
                agents.append(node["agent"])

        # Check direct agent field
        if "agent_type" in data:
            agents.append(data["agent_type"])

        # Check config
        config = data.get("config", {})
        if "agents" in config:
            agents.extend(config["agents"])

        return agents

    def _same_agent_family(self, agent: str, pattern_agents: List[str]) -> bool:
        """Check if agent is in same family as pattern agents"""
        agent_families = {
            "AUTO_CLAUDE": ["AUTO_CLAUDE_PLANNER", "AUTO_CLAUDE_CODER",
                          "AUTO_CLAUDE_QA_REVIEWER", "AUTO_CLAUDE_QA_FIXER"],
            "AG_A2A": ["AG_A2A_CALCULATOR", "AG_A2A_POETRY", "AG_A2A_PHILOSOPHY",
                      "AG_A2A_HISTORY", "AG_A2A_GUI_TEST"],
            "AG": ["AG_RESEARCH", "AG_ANALYST", "AG_WRITER", "AG_REVIEWER"],
        }

        agent_family = None
        for family, members in agent_families.items():
            if agent in members:
                agent_family = family
                break

        if not agent_family:
            return False

        for pattern_agent in pattern_agents:
            if pattern_agent in agent_families.get(agent_family, []):
                return True

        return False

    def _infer_pattern_type(self, description: str) -> PatternType:
        """Infer pattern type from task description"""
        desc_lower = description.lower()

        for pattern_type, keywords in self.PATTERN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return pattern_type

        return PatternType.WORKFLOW  # Default

    async def match_project(
        self,
        project: ProjectSpec,
    ) -> Dict[str, PatternMatch]:
        """
        Match all tasks in a project to patterns.

        Args:
            project: Project specification

        Returns:
            Dict mapping task_id to PatternMatch
        """
        matches = {}

        for phase in project.phases:
            for task_dict in phase.get("tasks", []):
                task = ProjectTask(
                    id=task_dict["id"],
                    description=task_dict["description"],
                    agent_type=task_dict.get("agent_type"),
                )

                match = await self.match_task(task)
                matches[task.id] = match

        # Log summary
        matched_count = sum(1 for m in matches.values() if not m.create_new)
        total_count = len(matches)

        self.logger.info(
            "project_pattern_matching_complete",
            project_id=project.id,
            matched=matched_count,
            total=total_count,
            match_rate=f"{matched_count/total_count*100:.1f}%" if total_count > 0 else "0%",
        )

        return matches

    async def suggest_patterns_to_create(
        self,
        project: ProjectSpec,
    ) -> List[Dict[str, Any]]:
        """
        Suggest new patterns to create based on unmatched tasks.

        Args:
            project: Project specification

        Returns:
            List of pattern creation suggestions
        """
        matches = await self.match_project(project)
        suggestions = []

        # Group unmatched tasks by agent type
        unmatched_by_agent: Dict[str, List[ProjectTask]] = {}

        for phase in project.phases:
            for task_dict in phase.get("tasks", []):
                task_id = task_dict["id"]
                match = matches.get(task_id)

                if match and match.create_new:
                    agent = task_dict.get("agent_type", "AUTO_CLAUDE_CODER")
                    if agent not in unmatched_by_agent:
                        unmatched_by_agent[agent] = []
                    unmatched_by_agent[agent].append(
                        ProjectTask(
                            id=task_id,
                            description=task_dict["description"],
                            agent_type=agent,
                        )
                    )

        # Create suggestions
        for agent, tasks in unmatched_by_agent.items():
            if len(tasks) >= 2:
                # Suggest workflow pattern
                suggestions.append({
                    "type": "workflow",
                    "name": f"{agent.lower()}_workflow",
                    "description": f"Workflow for {len(tasks)} {agent} tasks",
                    "agent": agent,
                    "tasks": [t.description for t in tasks],
                })
            else:
                # Suggest single-task pattern
                for task in tasks:
                    suggestions.append({
                        "type": "agent",
                        "name": f"{task.id}_pattern",
                        "description": task.description,
                        "agent": agent,
                    })

        return suggestions
