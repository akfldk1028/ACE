"""
Data Models for AG-ACE-BRIDGE

Pydantic models for Task, Result, Pipeline, and related entities.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class Priority(str, Enum):
    """Task priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskType(str, Enum):
    """Types of tasks that can be executed"""
    RESEARCH = "research"
    SPEC = "spec"
    PLAN = "plan"
    CODE = "code"
    QA = "qa"
    FIX = "fix"
    VALIDATE = "validate"
    MERGE = "merge"
    CUSTOM = "custom"


class ResultStatus(str, Enum):
    """Status of task execution result"""
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_RETRY = "needs_retry"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Types of agents available"""
    # Auto-Claude agents
    AUTO_CLAUDE_PLANNER = "auto_claude.planner"
    AUTO_CLAUDE_CODER = "auto_claude.coder"
    AUTO_CLAUDE_QA_REVIEWER = "auto_claude.qa_reviewer"
    AUTO_CLAUDE_QA_FIXER = "auto_claude.qa_fixer"

    # AG autogen_a2a_kit agents
    AG_RESEARCH = "ag.research"
    AG_ANALYST = "ag.analyst"
    AG_WRITER = "ag.writer"
    AG_REVIEWER = "ag.reviewer"
    AG_COORDINATOR = "ag.coordinator"

    # AG law-domain-agents
    AG_CASE_ANALYZER = "ag.case_analyzer"
    AG_LEGAL_RESEARCHER = "ag.legal_researcher"
    AG_RISK_ASSESSOR = "ag.risk_assessor"
    AG_COMPLIANCE_CHECKER = "ag.compliance_checker"
    AG_DOCUMENT_DRAFTER = "ag.document_drafter"


class Task(BaseModel):
    """
    Task to be executed by the orchestrator.

    Represents a unit of work that can be assigned to one or more agents.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: TaskType
    description: str
    priority: Priority = Priority.MEDIUM

    # Task context and requirements
    context: Dict[str, Any] = Field(default_factory=dict)
    requirements: List[str] = Field(default_factory=list)

    # Flags for pipeline building
    needs_research: bool = False
    domain_validation: bool = False

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    parent_task_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    class Config:
        use_enum_values = True


class Result(BaseModel):
    """
    Result of task execution.

    Contains the output, status, and any follow-up tasks.
    """
    task_id: str
    status: ResultStatus

    # Output data
    output: Any = None
    error: Optional[str] = None

    # Follow-up
    next_tasks: List[Task] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)

    # Metadata
    completed_at: datetime = Field(default_factory=datetime.now)
    execution_time_ms: Optional[int] = None
    agent_used: Optional[str] = None

    class Config:
        use_enum_values = True


class StageType(str, Enum):
    """Types of pipeline stages"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CRITIC_LOOP = "critic_loop"


class Stage(BaseModel):
    """
    A single stage in a pipeline.

    Can be sequential, parallel, or a critic loop.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: AgentType
    stage_type: StageType = StageType.SEQUENTIAL

    # Configuration
    timeout_seconds: int = 300
    retry_on_failure: bool = True

    # For parallel stages
    parallel_agents: List[AgentType] = Field(default_factory=list)

    # For critic loop
    critic_loop: bool = False
    max_iterations: int = 5
    critic_agent: Optional[AgentType] = None
    fixer_agent: Optional[AgentType] = None

    class Config:
        use_enum_values = True


class Pipeline(BaseModel):
    """
    A complete pipeline of stages to execute.

    Represents the execution plan for a task.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    stages: List[Stage] = Field(default_factory=list)

    # State
    current_stage_index: int = 0
    is_complete: bool = False

    # Context accumulation
    accumulated_context: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)


class AgentCapability(BaseModel):
    """
    Capability definition for an agent.

    Used for agent selection and matching.
    """
    agent: AgentType
    capabilities: List[str]
    description: str

    # Performance characteristics
    avg_execution_time_ms: Optional[int] = None
    success_rate: Optional[float] = None

    # Availability
    is_available: bool = True
    endpoint_url: Optional[str] = None

    class Config:
        use_enum_values = True


class MemorySyncEvent(BaseModel):
    """
    Event for memory synchronization between Graphiti and Neo4j.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str  # "graphiti" or "neo4j"
    event_type: str  # "insert", "update", "delete"

    # Data
    entity_type: str
    entity_id: str
    data: Dict[str, Any]

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    synced: bool = False
