"""
Tests for src/project/spec.py

Validates ProjectSpec creation, default values, enum completeness,
and YAML / JSON round-trip serialization.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest

from src.project.spec import (
    ProjectSpec,
    ProjectPhase,
    ProjectStatus,
    ProjectRequirements,
    AgentConfig,
    PipelineConfig,
    load_project_spec,
    save_project_spec,
)


# ── Minimal creation ──────────────────────────────────────────


class TestProjectSpecCreation:
    """Tests for constructing a ProjectSpec with required fields."""

    def test_project_spec_creation_minimal(self):
        """name, description, and goals are the only required fields."""
        spec = ProjectSpec(
            name="Test Project",
            description="A test project",
            goals=["Goal 1", "Goal 2"],
        )
        assert spec.name == "Test Project"
        assert spec.description == "A test project"
        assert spec.goals == ["Goal 1", "Goal 2"]

    def test_project_spec_id_generated(self):
        """id is auto-generated as an 8-character string."""
        spec = ProjectSpec(
            name="ID Test",
            description="Check auto ID",
            goals=["g"],
        )
        assert isinstance(spec.id, str)
        assert len(spec.id) == 8


# ── Default values ─────────────────────────────────────────────


class TestProjectSpecDefaults:
    """Verify sensible defaults for optional fields."""

    @pytest.fixture()
    def spec(self):
        return ProjectSpec(
            name="Defaults",
            description="Check defaults",
            goals=["g"],
        )

    def test_project_spec_defaults(self, spec):
        """status defaults to PENDING, phase to PLANNING, progress to 0."""
        assert spec.status == ProjectStatus.PENDING
        assert spec.phase == ProjectPhase.PLANNING
        assert spec.progress_percent == 0

    def test_project_requirements_defaults(self, spec):
        """All requirement sub-lists default to empty."""
        reqs = spec.requirements
        assert isinstance(reqs, ProjectRequirements)
        assert reqs.functional == []
        assert reqs.non_functional == []
        assert reqs.constraints == []
        assert reqs.dependencies == []

    def test_agent_config_defaults(self, spec):
        """Agent config defaults: auto_claude=True, ag_autogen=True, ag_law=False."""
        agents = spec.agents
        assert isinstance(agents, AgentConfig)
        assert agents.use_auto_claude is True
        assert agents.use_ag_autogen is True
        assert agents.use_ag_law is False

    def test_pipeline_config_defaults(self, spec):
        """Pipeline config defaults: pattern='auto', max_iterations=5, parallel_limit=3."""
        pipeline = spec.pipeline
        assert isinstance(pipeline, PipelineConfig)
        assert pipeline.pattern == "auto"
        assert pipeline.max_iterations == 5
        assert pipeline.parallel_limit == 3


# ── Enum completeness ──────────────────────────────────────────


class TestEnumCompleteness:
    """Verify all expected enum members exist."""

    def test_project_phase_enum(self):
        """ProjectPhase must contain exactly 6 phases."""
        expected = {
            "PLANNING", "IMPLEMENTATION", "TESTING",
            "REVIEW", "DEPLOYMENT", "COMPLETED",
        }
        actual = {member.name for member in ProjectPhase}
        assert actual == expected

    def test_project_status_enum(self):
        """ProjectStatus must contain exactly 6 statuses."""
        expected = {
            "PENDING", "QUEUED", "IN_PROGRESS",
            "PAUSED", "COMPLETED", "FAILED",
        }
        actual = {member.name for member in ProjectStatus}
        assert actual == expected


# ── Serialization round-trips ──────────────────────────────────


class TestSerialization:
    """Test save/load for YAML and JSON formats."""

    @pytest.fixture()
    def sample_spec(self):
        return ProjectSpec(
            name="Serialize Me",
            description="Round-trip test",
            goals=["Goal A", "Goal B"],
            tech_stack=["Python", "FastAPI"],
            requirements=ProjectRequirements(
                functional=["Login", "Logout"],
                non_functional=["< 200ms response"],
            ),
        )

    def test_save_load_yaml(self, tmp_path, sample_spec):
        """Saving as YAML then loading reproduces the same spec."""
        yaml_file = tmp_path / "spec.yaml"
        save_project_spec(sample_spec, yaml_file)

        loaded = load_project_spec(yaml_file)
        assert loaded.name == sample_spec.name
        assert loaded.description == sample_spec.description
        assert loaded.goals == sample_spec.goals
        assert loaded.tech_stack == sample_spec.tech_stack
        assert loaded.requirements.functional == sample_spec.requirements.functional
        assert loaded.requirements.non_functional == sample_spec.requirements.non_functional
        assert loaded.id == sample_spec.id

    def test_save_load_json(self, tmp_path, sample_spec):
        """Saving as JSON then loading reproduces the same spec."""
        json_file = tmp_path / "spec.json"
        save_project_spec(sample_spec, json_file)

        loaded = load_project_spec(json_file)
        assert loaded.name == sample_spec.name
        assert loaded.description == sample_spec.description
        assert loaded.goals == sample_spec.goals
        assert loaded.tech_stack == sample_spec.tech_stack
        assert loaded.id == sample_spec.id

    def test_load_nonexistent_raises(self, tmp_path):
        """Loading a nonexistent file raises FileNotFoundError."""
        missing = tmp_path / "does_not_exist.yaml"
        with pytest.raises(FileNotFoundError):
            load_project_spec(missing)

    def test_load_unsupported_format(self, tmp_path):
        """Loading a file with an unsupported extension raises ValueError."""
        txt_file = tmp_path / "spec.txt"
        txt_file.write_text("name: test", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_project_spec(txt_file)
