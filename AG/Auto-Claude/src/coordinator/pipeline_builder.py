"""
Pipeline Builder for AG/Auto-Claude

Dynamically builds execution pipelines based on task requirements.
Uses orchestration patterns from Microsoft and Google ADK.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import uuid

from src.utils.models import (
    Task, Pipeline, Stage, StageType, AgentType, TaskType, AgentMcpConfig
)
from src.utils.logger import Loggers
from src.utils.config import get_settings
from src.coordinator.agent_selector import get_selector


@dataclass
class PipelineTemplate:
    """Pre-defined pipeline template"""
    name: str
    description: str
    stages: List[Stage]
    supports_task_types: List[TaskType]


class PipelineBuilder:
    """
    Dynamic pipeline builder.

    Creates execution pipelines based on:
    - Task type and requirements
    - Pre-defined templates
    - Custom configurations

    Patterns supported:
    - Sequential: Linear stage execution
    - Parallel Fan-Out: Multiple agents simultaneously
    - Critic Loop: Generator-Critic iteration
    - Hybrid: Combination of patterns

    Example:
        builder = PipelineBuilder()

        task = Task(type=TaskType.CODE, description="Implement feature")
        pipeline = builder.build(task)

        print(pipeline.stages)
    """

    def __init__(self):
        self.logger = Loggers.pipeline()
        self.settings = get_settings()
        self.selector = get_selector()
        self._templates: Dict[str, PipelineTemplate] = {}
        self._initialize_templates()

    def _initialize_templates(self) -> None:
        """Initialize pre-defined pipeline templates"""

        # Full Auto-Claude pipeline
        self._templates["auto_claude_full"] = PipelineTemplate(
            name="Auto-Claude Full Pipeline",
            description="Complete SPEC → PLAN → CODE → QA → FIX cycle",
            stages=[
                Stage(
                    id=str(uuid.uuid4()),
                    agent=AgentType.AUTO_CLAUDE_PLANNER,
                    stage_type=StageType.SEQUENTIAL,
                ),
                Stage(
                    id=str(uuid.uuid4()),
                    agent=AgentType.AUTO_CLAUDE_CODER,
                    stage_type=StageType.SEQUENTIAL,
                ),
                Stage(
                    id=str(uuid.uuid4()),
                    agent=AgentType.AUTO_CLAUDE_QA_REVIEWER,
                    stage_type=StageType.CRITIC_LOOP,
                    critic_loop=True,
                    max_iterations=5,
                    critic_agent=AgentType.AUTO_CLAUDE_QA_REVIEWER,
                    fixer_agent=AgentType.AUTO_CLAUDE_QA_FIXER,
                ),
            ],
            supports_task_types=[TaskType.SPEC, TaskType.PLAN, TaskType.CODE],
        )

        # Research pipeline
        self._templates["research"] = PipelineTemplate(
            name="Research Pipeline",
            description="Multi-agent research and analysis",
            stages=[
                Stage(
                    id=str(uuid.uuid4()),
                    agent=AgentType.AG_RESEARCH,
                    stage_type=StageType.PARALLEL,
                    parallel_agents=[AgentType.AG_RESEARCH, AgentType.AG_ANALYST],
                ),
                Stage(
                    id=str(uuid.uuid4()),
                    agent=AgentType.AG_WRITER,
                    stage_type=StageType.SEQUENTIAL,
                ),
            ],
            supports_task_types=[TaskType.RESEARCH],
        )

        # Legal validation pipeline
        self._templates["legal_validation"] = PipelineTemplate(
            name="Legal Validation Pipeline",
            description="Legal research, compliance check, risk assessment",
            stages=[
                Stage(
                    id=str(uuid.uuid4()),
                    agent=AgentType.AG_LEGAL_RESEARCHER,
                    stage_type=StageType.SEQUENTIAL,
                ),
                Stage(
                    id=str(uuid.uuid4()),
                    agent=AgentType.AG_CASE_ANALYZER,
                    stage_type=StageType.PARALLEL,
                    parallel_agents=[
                        AgentType.AG_CASE_ANALYZER,
                        AgentType.AG_COMPLIANCE_CHECKER,
                    ],
                ),
                Stage(
                    id=str(uuid.uuid4()),
                    agent=AgentType.AG_RISK_ASSESSOR,
                    stage_type=StageType.SEQUENTIAL,
                ),
            ],
            supports_task_types=[TaskType.VALIDATE],
        )

        # QA loop only
        self._templates["qa_loop"] = PipelineTemplate(
            name="QA Loop",
            description="Generator-Critic QA cycle",
            stages=[
                Stage(
                    id=str(uuid.uuid4()),
                    agent=AgentType.AUTO_CLAUDE_CODER,
                    stage_type=StageType.CRITIC_LOOP,
                    critic_loop=True,
                    max_iterations=5,
                    critic_agent=AgentType.AUTO_CLAUDE_QA_REVIEWER,
                    fixer_agent=AgentType.AUTO_CLAUDE_QA_FIXER,
                ),
            ],
            supports_task_types=[TaskType.QA, TaskType.FIX],
        )

    def build(
        self,
        task: Task,
        template_name: Optional[str] = None,
        custom_stages: Optional[List[Stage]] = None,
        agent_mcp_overrides: Optional[Dict[str, AgentMcpConfig]] = None,
    ) -> Pipeline:
        """
        Build a pipeline for a task.

        Args:
            task: Task to build pipeline for
            template_name: Optional template to use
            custom_stages: Optional custom stages override
            agent_mcp_overrides: Per-agent MCP configurations keyed by AgentType value.
                                 Resolved from Auto-Claude's project config (agentMcpOverrides
                                 + customMcpServers). Each agent's MCP config is injected into
                                 the corresponding pipeline stage.

        Returns:
            Configured Pipeline
        """
        self.logger.info(
            "pipeline_build_start",
            task_id=task.id,
            template=template_name,
        )

        # Use custom stages if provided
        if custom_stages:
            stages = custom_stages
        elif template_name and template_name in self._templates:
            stages = self._clone_stages(self._templates[template_name].stages)
        else:
            # Auto-build based on task
            stages = self._auto_build_stages(task)

        # Inject per-agent MCP configs into stages
        if agent_mcp_overrides:
            stages = self._inject_mcp_configs(stages, agent_mcp_overrides)

        pipeline = Pipeline(
            id=str(uuid.uuid4()),
            task_id=task.id,
            stages=stages,
            accumulated_context={
                "task_description": task.description,
                "requirements": task.requirements,
            },
        )

        self.logger.info(
            "pipeline_built",
            task_id=task.id,
            pipeline_id=pipeline.id,
            stage_count=len(stages),
        )

        return pipeline

    def _inject_mcp_configs(
        self,
        stages: List[Stage],
        agent_mcp_overrides: Dict[str, AgentMcpConfig],
    ) -> List[Stage]:
        """
        Inject per-agent MCP configurations into pipeline stages.

        Each stage's primary agent is looked up in the overrides map.
        Note: Stage.mcp_config is per-stage, not per-agent within a stage.
        For parallel/critic stages, the primary agent's config is used.

        Args:
            stages: Pipeline stages to inject into
            agent_mcp_overrides: Map of agent type string -> AgentMcpConfig

        Returns:
            Stages with MCP configs injected
        """
        for stage in stages:
            agent_key = stage.agent if isinstance(stage.agent, str) else stage.agent.value if hasattr(stage.agent, 'value') else str(stage.agent)

            if agent_key in agent_mcp_overrides:
                stage.mcp_config = agent_mcp_overrides[agent_key]
                self.logger.debug(
                    "mcp_config_injected",
                    stage_id=stage.id,
                    agent=agent_key,
                    server_count=len(agent_mcp_overrides[agent_key].servers),
                )

        return stages

    def _auto_build_stages(self, task: Task) -> List[Stage]:
        """Automatically build stages based on task"""
        task_type = TaskType(task.type) if isinstance(task.type, str) else task.type
        stages = []

        # Determine if research is needed
        if task.needs_research:
            stages.append(Stage(
                id=str(uuid.uuid4()),
                agent=AgentType.AG_RESEARCH,
                stage_type=StageType.SEQUENTIAL,
            ))

        # Add main execution stages based on task type
        if task_type == TaskType.RESEARCH:
            stages.extend(self._build_research_stages(task))

        elif task_type in [TaskType.SPEC, TaskType.PLAN]:
            stages.append(Stage(
                id=str(uuid.uuid4()),
                agent=AgentType.AUTO_CLAUDE_PLANNER,
                stage_type=StageType.SEQUENTIAL,
            ))

        elif task_type == TaskType.CODE:
            stages.extend(self._build_code_stages(task))

        elif task_type in [TaskType.QA, TaskType.VALIDATE]:
            stages.extend(self._build_qa_stages(task))

        elif task_type == TaskType.FIX:
            stages.append(Stage(
                id=str(uuid.uuid4()),
                agent=AgentType.AUTO_CLAUDE_QA_FIXER,
                stage_type=StageType.SEQUENTIAL,
            ))

        else:
            # Fallback: use agent selector
            agents = self.selector.select_for_pipeline(task)
            for agent in agents:
                stages.append(Stage(
                    id=str(uuid.uuid4()),
                    agent=agent,
                    stage_type=StageType.SEQUENTIAL,
                ))

        # Add legal validation if needed
        if task.domain_validation:
            stages.extend(self._build_legal_validation_stages())

        return stages if stages else [self._build_default_stage(task)]

    def _build_research_stages(self, task: Task) -> List[Stage]:
        """Build stages for research task"""
        return [
            Stage(
                id=str(uuid.uuid4()),
                agent=AgentType.AG_RESEARCH,
                stage_type=StageType.PARALLEL,
                parallel_agents=[AgentType.AG_RESEARCH, AgentType.AG_ANALYST],
            ),
            Stage(
                id=str(uuid.uuid4()),
                agent=AgentType.AG_WRITER,
                stage_type=StageType.SEQUENTIAL,
            ),
        ]

    def _build_code_stages(self, task: Task) -> List[Stage]:
        """Build stages for code task"""
        stages = [
            Stage(
                id=str(uuid.uuid4()),
                agent=AgentType.AUTO_CLAUDE_PLANNER,
                stage_type=StageType.SEQUENTIAL,
            ),
            Stage(
                id=str(uuid.uuid4()),
                agent=AgentType.AUTO_CLAUDE_CODER,
                stage_type=StageType.SEQUENTIAL,
            ),
        ]

        # Add QA loop
        stages.append(Stage(
            id=str(uuid.uuid4()),
            agent=AgentType.AUTO_CLAUDE_QA_REVIEWER,
            stage_type=StageType.CRITIC_LOOP,
            critic_loop=True,
            max_iterations=self.settings.max_qa_iterations,
            critic_agent=AgentType.AUTO_CLAUDE_QA_REVIEWER,
            fixer_agent=AgentType.AUTO_CLAUDE_QA_FIXER,
        ))

        return stages

    def _build_qa_stages(self, task: Task) -> List[Stage]:
        """Build stages for QA task"""
        return [
            Stage(
                id=str(uuid.uuid4()),
                agent=AgentType.AUTO_CLAUDE_QA_REVIEWER,
                stage_type=StageType.CRITIC_LOOP,
                critic_loop=True,
                max_iterations=self.settings.max_qa_iterations,
                critic_agent=AgentType.AUTO_CLAUDE_QA_REVIEWER,
                fixer_agent=AgentType.AUTO_CLAUDE_QA_FIXER,
            ),
        ]

    def _build_legal_validation_stages(self) -> List[Stage]:
        """Build stages for legal validation"""
        return [
            Stage(
                id=str(uuid.uuid4()),
                agent=AgentType.AG_COMPLIANCE_CHECKER,
                stage_type=StageType.PARALLEL,
                parallel_agents=[
                    AgentType.AG_COMPLIANCE_CHECKER,
                    AgentType.AG_RISK_ASSESSOR,
                ],
            ),
        ]

    def _build_default_stage(self, task: Task) -> Stage:
        """Build default fallback stage"""
        selection = self.selector.select(task)
        return Stage(
            id=str(uuid.uuid4()),
            agent=selection.primary,
            stage_type=StageType.SEQUENTIAL,
        )

    def _clone_stages(self, stages: List[Stage]) -> List[Stage]:
        """Clone stages with new IDs"""
        return [
            Stage(
                id=str(uuid.uuid4()),
                agent=s.agent,
                stage_type=s.stage_type,
                timeout_seconds=s.timeout_seconds,
                retry_on_failure=s.retry_on_failure,
                parallel_agents=s.parallel_agents.copy() if s.parallel_agents else [],
                critic_loop=s.critic_loop,
                max_iterations=s.max_iterations,
                critic_agent=s.critic_agent,
                fixer_agent=s.fixer_agent,
            )
            for s in stages
        ]

    def get_template(self, name: str) -> Optional[PipelineTemplate]:
        """Get a pipeline template by name"""
        return self._templates.get(name)

    def list_templates(self) -> List[str]:
        """List all available template names"""
        return list(self._templates.keys())

    def register_template(self, template: PipelineTemplate) -> None:
        """Register a custom pipeline template"""
        self._templates[template.name] = template
        self.logger.info("template_registered", name=template.name)


# Global builder instance
_builder: Optional[PipelineBuilder] = None


def get_builder() -> PipelineBuilder:
    """Get or create global pipeline builder"""
    global _builder
    if _builder is None:
        _builder = PipelineBuilder()
    return _builder


def build_pipeline(
    task: Task,
    template: Optional[str] = None,
    agent_mcp_overrides: Optional[Dict[str, AgentMcpConfig]] = None,
) -> Pipeline:
    """
    Convenience function to build a pipeline.

    Args:
        task: Task to build pipeline for
        template: Optional template name
        agent_mcp_overrides: Per-agent MCP configurations

    Returns:
        Configured pipeline
    """
    builder = get_builder()
    return builder.build(task, template_name=template, agent_mcp_overrides=agent_mcp_overrides)
