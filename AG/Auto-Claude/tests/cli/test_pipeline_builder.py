"""Tests for AG-ACE-BRIDGE pipeline_builder module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import uuid

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.coordinator.pipeline_builder import PipelineBuilder, PipelineTemplate
from src.utils.models import Task, Pipeline, Stage, StageType, AgentType, TaskType


class TestPipelineBuilder:
    """Tests for PipelineBuilder class."""

    def test_builder_creation(self):
        """Should create PipelineBuilder instance."""
        builder = PipelineBuilder()
        assert builder is not None
        assert hasattr(builder, '_templates')

    def test_build_returns_pipeline(self):
        """build() should return a Pipeline."""
        builder = PipelineBuilder()
        task = Task(type=TaskType.CODE, description="Build feature")
        pipeline = builder.build(task)

        assert isinstance(pipeline, Pipeline)
        assert len(pipeline.stages) > 0

    def test_build_code_task(self):
        """CODE task should create appropriate pipeline."""
        builder = PipelineBuilder()
        task = Task(type=TaskType.CODE, description="Implement feature")
        pipeline = builder.build(task)

        assert pipeline is not None
        assert len(pipeline.stages) >= 1

    def test_build_research_task(self):
        """RESEARCH task should create research pipeline."""
        builder = PipelineBuilder()
        task = Task(type=TaskType.RESEARCH, description="Research topic")
        pipeline = builder.build(task)

        assert pipeline is not None
        assert len(pipeline.stages) >= 1

    def test_build_qa_task(self):
        """QA task should create QA pipeline."""
        builder = PipelineBuilder()
        task = Task(type=TaskType.QA, description="Review code")
        pipeline = builder.build(task)

        assert pipeline is not None


class TestPipelineTemplates:
    """Tests for pre-defined pipeline templates."""

    def test_auto_claude_full_template_exists(self):
        """Should have auto_claude_full template."""
        builder = PipelineBuilder()
        assert "auto_claude_full" in builder._templates

    def test_research_template_exists(self):
        """Should have research template."""
        builder = PipelineBuilder()
        assert "research" in builder._templates

    def test_auto_claude_full_has_multiple_stages(self):
        """auto_claude_full should have multiple stages."""
        builder = PipelineBuilder()
        template = builder._templates["auto_claude_full"]

        assert len(template.stages) >= 2

    def test_template_has_required_fields(self):
        """Templates should have all required fields."""
        builder = PipelineBuilder()

        for name, template in builder._templates.items():
            assert isinstance(template, PipelineTemplate)
            assert template.name != ""
            assert template.description != ""
            assert len(template.stages) > 0
            assert isinstance(template.supports_task_types, list)


class TestPipelineStages:
    """Tests for pipeline stage generation."""

    def test_stages_have_unique_ids(self):
        """Each stage should have unique ID."""
        builder = PipelineBuilder()
        task = Task(type=TaskType.CODE, description="Build feature")
        pipeline = builder.build(task)

        stage_ids = [stage.id for stage in pipeline.stages]
        assert len(stage_ids) == len(set(stage_ids))  # All unique

    def test_stages_have_agents(self):
        """Each stage should have an agent assigned."""
        builder = PipelineBuilder()
        task = Task(type=TaskType.CODE, description="Build feature")
        pipeline = builder.build(task)

        for stage in pipeline.stages:
            assert stage.agent is not None

    def test_stages_have_stage_type(self):
        """Each stage should have a stage type."""
        builder = PipelineBuilder()
        task = Task(type=TaskType.CODE, description="Build feature")
        pipeline = builder.build(task)

        for stage in pipeline.stages:
            assert stage.stage_type is not None
            # stage_type can be StageType enum or string value
            if isinstance(stage.stage_type, str):
                valid_types = [st.value for st in StageType]
                assert stage.stage_type in valid_types
            else:
                assert isinstance(stage.stage_type, StageType)


class TestPipelineBuilderWithTemplate:
    """Tests for building from specific template."""

    def test_build_from_template(self):
        """Should build pipeline from specific template."""
        builder = PipelineBuilder()
        task = Task(type=TaskType.CODE, description="Build feature")

        # Build uses task type to select template
        pipeline = builder.build(task)
        assert pipeline is not None

    def test_template_stages_cloned(self):
        """Template stages should be cloned (not shared)."""
        builder = PipelineBuilder()

        task1 = Task(type=TaskType.CODE, description="Task 1")
        task2 = Task(type=TaskType.CODE, description="Task 2")

        pipeline1 = builder.build(task1)
        pipeline2 = builder.build(task2)

        # Stage IDs should be different
        ids1 = {s.id for s in pipeline1.stages}
        ids2 = {s.id for s in pipeline2.stages}

        assert ids1.isdisjoint(ids2)


class TestPipelineBuilderCriticLoop:
    """Tests for critic loop pipeline generation."""

    def test_critic_loop_stage_has_critic_agent(self):
        """Critic loop stages should have critic_agent set."""
        builder = PipelineBuilder()

        # Check the template directly
        if "auto_claude_full" in builder._templates:
            template = builder._templates["auto_claude_full"]
            critic_stages = [
                s for s in template.stages
                if s.stage_type == StageType.CRITIC_LOOP
            ]

            for stage in critic_stages:
                assert stage.critic_agent is not None

    def test_critic_loop_has_max_iterations(self):
        """Critic loop stages should have max_iterations."""
        builder = PipelineBuilder()

        if "auto_claude_full" in builder._templates:
            template = builder._templates["auto_claude_full"]
            critic_stages = [
                s for s in template.stages
                if s.stage_type == StageType.CRITIC_LOOP
            ]

            for stage in critic_stages:
                assert stage.max_iterations is not None
                assert stage.max_iterations > 0


class TestPipelineBuilderParallel:
    """Tests for parallel pipeline generation."""

    def test_parallel_stage_has_agents(self):
        """Parallel stages should have parallel_agents list."""
        builder = PipelineBuilder()

        if "research" in builder._templates:
            template = builder._templates["research"]
            parallel_stages = [
                s for s in template.stages
                if s.stage_type == StageType.PARALLEL
            ]

            for stage in parallel_stages:
                if stage.parallel_agents:
                    assert len(stage.parallel_agents) >= 1


class TestPipelineBuilderCustomization:
    """Tests for pipeline customization."""

    def test_build_with_custom_requirements(self):
        """Should consider task requirements."""
        builder = PipelineBuilder()
        task = Task(
            type=TaskType.CODE,
            description="Build feature",
            requirements=["testing", "documentation"]
        )
        pipeline = builder.build(task)

        assert pipeline is not None

    def test_build_with_metadata(self):
        """Should consider task metadata."""
        builder = PipelineBuilder()
        task = Task(
            type=TaskType.CODE,
            description="Build feature",
            metadata={"priority": "high", "deadline": "2024-12-31"}
        )
        pipeline = builder.build(task)

        assert pipeline is not None


class TestPipelineTemplateDataclass:
    """Tests for PipelineTemplate dataclass."""

    def test_pipeline_template_creation(self):
        """Should create PipelineTemplate."""
        template = PipelineTemplate(
            name="Test Template",
            description="For testing",
            stages=[
                Stage(
                    id=str(uuid.uuid4()),
                    agent=AgentType.AUTO_CLAUDE_CODER,
                    stage_type=StageType.SEQUENTIAL
                )
            ],
            supports_task_types=[TaskType.CODE]
        )

        assert template.name == "Test Template"
        assert len(template.stages) == 1
        assert TaskType.CODE in template.supports_task_types
