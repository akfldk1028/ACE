"""
Data Models for AG-ACE-BRIDGE

Pydantic models for Task, Result, Pipeline, and related entities.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
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
    PLANNING = "planning"  # Alias for project-level planning
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

    # Claude Code CLI agents
    CLAUDE_CLI_PLAN = "claude_cli.plan"

    # AG A2A Protocol agents (autogen_a2a_kit demo agents)
    AG_A2A_POETRY = "ag.a2a.poetry_agent"
    AG_A2A_PHILOSOPHY = "ag.a2a.philosophy_agent"
    AG_A2A_HISTORY = "ag.a2a.history_agent"
    AG_A2A_CALCULATOR = "ag.a2a.calculator_agent"
    AG_A2A_GUI_TEST = "ag.a2a.gui_test_agent"


class Task(BaseModel):
    """
    Task to be executed by the orchestrator.

    Represents a unit of work that can be assigned to one or more agents.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: TaskType
    description: str = Field(default="")
    priority: Priority = Priority.MEDIUM

    # Task input data
    input: Dict[str, Any] = Field(default_factory=dict)

    # Task context and requirements
    context: Dict[str, Any] = Field(default_factory=dict)
    requirements: List[str] = Field(default_factory=list)

    # Flags for pipeline building
    needs_research: bool = False
    domain_validation: bool = False

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
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

    Accepts either ``status`` (ResultStatus) or ``success`` (bool) at
    construction time.  When ``success`` is given without ``status``,
    it is automatically converted:
        success=True  → status=ResultStatus.SUCCESS
        success=False → status=ResultStatus.FAILED
    """
    task_id: str = ""
    status: ResultStatus = ResultStatus.SUCCESS

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

    @model_validator(mode="before")
    @classmethod
    def _convert_success_to_status(cls, values: Any) -> Any:
        """Allow ``Result(success=True)`` as shorthand."""
        if isinstance(values, dict) and "success" in values:
            success = values.pop("success")
            if "status" not in values:
                values["status"] = (
                    ResultStatus.SUCCESS if success else ResultStatus.FAILED
                )
        return values

    @property
    def success(self) -> bool:
        """Whether the task completed successfully."""
        return self.status == ResultStatus.SUCCESS or self.status == "success"

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

    # Per-agent MCP configuration (injected by PipelineBuilder from project config)
    mcp_config: Optional["AgentMcpConfig"] = None

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


class McpServerConfig(BaseModel):
    """
    MCP server configuration for per-agent MCP integration.

    Maps to AutoGen Studio's McpWorkbenchConfig server_params types:
    - StdioServerParams (command-based)
    - SseServerParams (SSE HTTP)
    - StreamableHttpServerParams (streamable HTTP)

    This is the bridge-level representation; AutoGen agents receive
    these as McpWorkbench components via their workbench field.
    """
    id: str  # Unique server identifier (matches Auto-Claude CustomMcpServer.id)
    name: str  # Display name
    server_type: str  # 'stdio' | 'sse' | 'streamable_http'

    # For stdio (command-based)
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)

    # For sse / streamable_http
    url: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)

    # Behavior
    auto_connect: bool = True
    priority: str = "optional"  # 'required' | 'optional'


class AgentMcpConfig(BaseModel):
    """
    Per-agent MCP configuration passed through pipeline stages.

    Contains the list of MCP servers assigned to a specific agent,
    resolved from Auto-Claude's agentMcpOverrides + customMcpServers.
    """
    servers: List[McpServerConfig] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)  # Additional tool names

    @property
    def has_servers(self) -> bool:
        return len(self.servers) > 0

    def get_required_servers(self) -> List[McpServerConfig]:
        return [s for s in self.servers if s.priority == "required"]


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

    # MCP capabilities (tools available via MCP servers)
    mcp_tools: List[str] = Field(default_factory=list)
    mcp_server_ids: List[str] = Field(default_factory=list)

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
