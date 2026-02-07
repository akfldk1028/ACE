"""
Agent Capabilities for AG/Auto-Claude

Defines capabilities, skills, and metadata for all 20 agents.
Used by AgentRegistry for matching tasks to appropriate agents.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from src.utils.models import AgentType, TaskType


@dataclass
class Capability:
    """Single capability definition"""
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)


@dataclass
class AgentCapabilities:
    """Complete capability profile for an agent"""
    agent_type: AgentType
    name: str
    description: str
    capabilities: List[Capability]
    supported_task_types: List[TaskType]

    # Agent characteristics
    is_autonomous: bool = False  # Can work 24/7 without supervision
    supports_streaming: bool = False
    max_context_length: Optional[int] = None

    # Performance hints
    avg_execution_time_seconds: Optional[int] = None
    priority_boost: int = 0  # Higher = prefer this agent

    # Connection info
    adapter_type: str = ""  # "auto_claude", "ag_http", "ag_law"
    endpoint: Optional[str] = None

    def get_all_keywords(self) -> List[str]:
        """Get all keywords from all capabilities"""
        keywords = []
        for cap in self.capabilities:
            keywords.extend(cap.keywords)
        return list(set(keywords))

    def matches_requirements(self, requirements: List[str]) -> float:
        """
        Calculate match score for given requirements.

        Args:
            requirements: List of required capabilities/keywords

        Returns:
            Match score (0.0 to 1.0)
        """
        if not requirements:
            return 0.5  # Neutral score if no requirements

        all_keywords = self.get_all_keywords()
        cap_names = [c.name.lower() for c in self.capabilities]
        all_terms = set(all_keywords + cap_names)

        matched = 0
        for req in requirements:
            req_lower = req.lower()
            if any(req_lower in term or term in req_lower for term in all_terms):
                matched += 1

        return matched / len(requirements) if requirements else 0.0


# =============================================================================
# Auto-Claude Agents (4)
# =============================================================================

AUTO_CLAUDE_PLANNER = AgentCapabilities(
    agent_type=AgentType.AUTO_CLAUDE_PLANNER,
    name="Auto-Claude Planner",
    description="Plans implementation strategy, decomposes tasks into subtasks",
    capabilities=[
        Capability(
            name="planning",
            description="Create implementation plans",
            keywords=["plan", "strategy", "roadmap", "architecture"],
        ),
        Capability(
            name="task-decomposition",
            description="Break down complex tasks",
            keywords=["decompose", "subtask", "breakdown", "split"],
        ),
        Capability(
            name="spec-analysis",
            description="Analyze specifications",
            keywords=["spec", "requirement", "analyze", "specification"],
        ),
    ],
    supported_task_types=[TaskType.SPEC, TaskType.PLAN],
    is_autonomous=True,
    adapter_type="auto_claude",
    avg_execution_time_seconds=30,
    priority_boost=1,
)

AUTO_CLAUDE_CODER = AgentCapabilities(
    agent_type=AgentType.AUTO_CLAUDE_CODER,
    name="Auto-Claude Coder",
    description="24/7 autonomous coding agent",
    capabilities=[
        Capability(
            name="implementation",
            description="Write production code",
            keywords=["code", "implement", "develop", "program", "write"],
        ),
        Capability(
            name="refactoring",
            description="Improve existing code",
            keywords=["refactor", "improve", "optimize", "clean"],
        ),
        Capability(
            name="24/7-autonomous",
            description="Operates continuously",
            keywords=["autonomous", "continuous", "24/7", "automated"],
        ),
    ],
    supported_task_types=[TaskType.CODE, TaskType.FIX],
    is_autonomous=True,
    supports_streaming=True,
    adapter_type="auto_claude",
    avg_execution_time_seconds=120,
    priority_boost=2,  # Primary coding agent
)

AUTO_CLAUDE_QA_REVIEWER = AgentCapabilities(
    agent_type=AgentType.AUTO_CLAUDE_QA_REVIEWER,
    name="Auto-Claude QA Reviewer",
    description="Reviews code quality, runs E2E tests",
    capabilities=[
        Capability(
            name="code-review",
            description="Review code quality",
            keywords=["review", "quality", "check", "inspect"],
        ),
        Capability(
            name="testing",
            description="Run and analyze tests",
            keywords=["test", "e2e", "unit", "integration", "qa"],
        ),
        Capability(
            name="validation",
            description="Validate implementations",
            keywords=["validate", "verify", "confirm", "ensure"],
        ),
    ],
    supported_task_types=[TaskType.QA, TaskType.VALIDATE],
    is_autonomous=True,
    adapter_type="auto_claude",
    avg_execution_time_seconds=60,
)

AUTO_CLAUDE_QA_FIXER = AgentCapabilities(
    agent_type=AgentType.AUTO_CLAUDE_QA_FIXER,
    name="Auto-Claude QA Fixer",
    description="Fixes issues found during QA",
    capabilities=[
        Capability(
            name="debugging",
            description="Debug and fix issues",
            keywords=["debug", "fix", "resolve", "troubleshoot"],
        ),
        Capability(
            name="issue-resolution",
            description="Resolve identified problems",
            keywords=["issue", "problem", "bug", "error", "resolve"],
        ),
    ],
    supported_task_types=[TaskType.FIX],
    is_autonomous=True,
    adapter_type="auto_claude",
    avg_execution_time_seconds=90,
)


# =============================================================================
# AG autogen_a2a_kit Agents (8)
# =============================================================================

AG_RESEARCH = AgentCapabilities(
    agent_type=AgentType.AG_RESEARCH,
    name="AG Research Agent",
    description="Gathers information, performs web searches",
    capabilities=[
        Capability(
            name="information-gathering",
            description="Collect relevant information",
            keywords=["research", "gather", "collect", "find", "search"],
        ),
        Capability(
            name="web-search",
            description="Search the web for information",
            keywords=["web", "internet", "online", "search", "google"],
        ),
        Capability(
            name="source-validation",
            description="Validate information sources",
            keywords=["source", "validate", "verify", "credibility"],
        ),
    ],
    supported_task_types=[TaskType.RESEARCH],
    adapter_type="ag_http",
    endpoint="/agents/research",
    avg_execution_time_seconds=45,
)

AG_ANALYST = AgentCapabilities(
    agent_type=AgentType.AG_ANALYST,
    name="AG Analyst Agent",
    description="Analyzes data, detects patterns",
    capabilities=[
        Capability(
            name="data-analysis",
            description="Analyze data sets",
            keywords=["analyze", "data", "statistics", "metrics"],
        ),
        Capability(
            name="pattern-detection",
            description="Find patterns in data",
            keywords=["pattern", "trend", "insight", "correlation"],
        ),
        Capability(
            name="reporting",
            description="Generate analysis reports",
            keywords=["report", "summary", "findings"],
        ),
    ],
    supported_task_types=[TaskType.RESEARCH, TaskType.VALIDATE],
    adapter_type="ag_http",
    endpoint="/agents/analyst",
    avg_execution_time_seconds=60,
)

AG_WRITER = AgentCapabilities(
    agent_type=AgentType.AG_WRITER,
    name="AG Writer Agent",
    description="Creates documentation and content",
    capabilities=[
        Capability(
            name="documentation",
            description="Write technical documentation",
            keywords=["document", "docs", "readme", "guide"],
        ),
        Capability(
            name="content-creation",
            description="Create various content",
            keywords=["write", "content", "article", "blog"],
        ),
        Capability(
            name="technical-writing",
            description="Technical writing expertise",
            keywords=["technical", "spec", "api", "reference"],
        ),
    ],
    supported_task_types=[TaskType.SPEC, TaskType.CUSTOM],
    adapter_type="ag_http",
    endpoint="/agents/writer",
    avg_execution_time_seconds=40,
)

AG_REVIEWER = AgentCapabilities(
    agent_type=AgentType.AG_REVIEWER,
    name="AG Reviewer Agent",
    description="Reviews and provides feedback",
    capabilities=[
        Capability(
            name="feedback",
            description="Provide constructive feedback",
            keywords=["feedback", "review", "critique", "evaluate"],
        ),
        Capability(
            name="quality-assessment",
            description="Assess quality of work",
            keywords=["quality", "assess", "grade", "score"],
        ),
    ],
    supported_task_types=[TaskType.QA, TaskType.VALIDATE],
    adapter_type="ag_http",
    endpoint="/agents/reviewer",
    avg_execution_time_seconds=30,
)

AG_COORDINATOR = AgentCapabilities(
    agent_type=AgentType.AG_COORDINATOR,
    name="AG Coordinator Agent",
    description="Coordinates multi-agent tasks",
    capabilities=[
        Capability(
            name="orchestration",
            description="Orchestrate agent collaboration",
            keywords=["coordinate", "orchestrate", "manage", "direct"],
        ),
        Capability(
            name="task-routing",
            description="Route tasks to appropriate agents",
            keywords=["route", "assign", "delegate", "dispatch"],
        ),
    ],
    supported_task_types=[TaskType.PLAN, TaskType.CUSTOM],
    adapter_type="ag_http",
    endpoint="/agents/coordinator",
    avg_execution_time_seconds=20,
)


# =============================================================================
# AG law-domain-agents (5)
# =============================================================================

AG_CASE_ANALYZER = AgentCapabilities(
    agent_type=AgentType.AG_CASE_ANALYZER,
    name="AG Case Analyzer",
    description="Analyzes legal cases and precedents",
    capabilities=[
        Capability(
            name="case-law",
            description="Analyze case law",
            keywords=["case", "precedent", "ruling", "judgment", "verdict"],
        ),
        Capability(
            name="precedent-analysis",
            description="Find and analyze precedents",
            keywords=["precedent", "previous", "similar", "historical"],
        ),
        Capability(
            name="legal-reasoning",
            description="Apply legal reasoning",
            keywords=["legal", "reason", "argument", "logic"],
        ),
    ],
    supported_task_types=[TaskType.RESEARCH, TaskType.VALIDATE],
    adapter_type="ag_law",
    endpoint="/legal/case-analyzer",
    avg_execution_time_seconds=90,
)

AG_LEGAL_RESEARCHER = AgentCapabilities(
    agent_type=AgentType.AG_LEGAL_RESEARCHER,
    name="AG Legal Researcher",
    description="Researches statutes and regulations",
    capabilities=[
        Capability(
            name="statute-search",
            description="Search legal statutes",
            keywords=["statute", "law", "act", "legislation"],
        ),
        Capability(
            name="regulation",
            description="Research regulations",
            keywords=["regulation", "rule", "requirement", "standard"],
        ),
        Capability(
            name="legal-research",
            description="Comprehensive legal research",
            keywords=["legal", "research", "jurisprudence"],
        ),
    ],
    supported_task_types=[TaskType.RESEARCH],
    adapter_type="ag_law",
    endpoint="/legal/researcher",
    avg_execution_time_seconds=75,
)

AG_RISK_ASSESSOR = AgentCapabilities(
    agent_type=AgentType.AG_RISK_ASSESSOR,
    name="AG Risk Assessor",
    description="Evaluates legal risks and liabilities",
    capabilities=[
        Capability(
            name="risk-evaluation",
            description="Evaluate legal risks",
            keywords=["risk", "danger", "threat", "exposure"],
        ),
        Capability(
            name="liability",
            description="Assess liability",
            keywords=["liability", "responsibility", "obligation"],
        ),
        Capability(
            name="mitigation",
            description="Suggest risk mitigation",
            keywords=["mitigate", "reduce", "prevent", "minimize"],
        ),
    ],
    supported_task_types=[TaskType.VALIDATE, TaskType.RESEARCH],
    adapter_type="ag_law",
    endpoint="/legal/risk-assessor",
    avg_execution_time_seconds=60,
)

AG_COMPLIANCE_CHECKER = AgentCapabilities(
    agent_type=AgentType.AG_COMPLIANCE_CHECKER,
    name="AG Compliance Checker",
    description="Checks regulatory compliance",
    capabilities=[
        Capability(
            name="compliance",
            description="Verify compliance",
            keywords=["compliance", "compliant", "conform", "adhere"],
        ),
        Capability(
            name="regulation-check",
            description="Check against regulations",
            keywords=["regulation", "check", "verify", "validate"],
        ),
        Capability(
            name="audit",
            description="Conduct compliance audits",
            keywords=["audit", "review", "examine", "inspect"],
        ),
    ],
    supported_task_types=[TaskType.VALIDATE, TaskType.QA],
    adapter_type="ag_law",
    endpoint="/legal/compliance-checker",
    avg_execution_time_seconds=45,
)

AG_DOCUMENT_DRAFTER = AgentCapabilities(
    agent_type=AgentType.AG_DOCUMENT_DRAFTER,
    name="AG Document Drafter",
    description="Drafts legal documents and contracts",
    capabilities=[
        Capability(
            name="legal-docs",
            description="Draft legal documents",
            keywords=["document", "draft", "legal", "official"],
        ),
        Capability(
            name="contracts",
            description="Create contracts",
            keywords=["contract", "agreement", "terms", "conditions"],
        ),
        Capability(
            name="templates",
            description="Use legal templates",
            keywords=["template", "form", "standard", "boilerplate"],
        ),
    ],
    supported_task_types=[TaskType.SPEC, TaskType.CUSTOM],
    adapter_type="ag_law",
    endpoint="/legal/document-drafter",
    avg_execution_time_seconds=90,
)


# =============================================================================
# AG A2A Protocol Agents (5)
# =============================================================================

AG_A2A_POETRY = AgentCapabilities(
    agent_type=AgentType.AG_A2A_POETRY,
    name="AG A2A Poetry Agent",
    description="Poetry and literary analysis via A2A Protocol",
    capabilities=[
        Capability(
            name="poem-analysis",
            description="Analyze poems and literary works",
            keywords=["poem", "poetry", "literary", "verse", "stanza"],
        ),
        Capability(
            name="literary-devices",
            description="Identify literary devices and techniques",
            keywords=["metaphor", "simile", "alliteration", "rhyme"],
        ),
    ],
    supported_task_types=[TaskType.RESEARCH, TaskType.CUSTOM],
    adapter_type="a2a",
    endpoint="http://localhost:8003/",
    avg_execution_time_seconds=30,
)

AG_A2A_PHILOSOPHY = AgentCapabilities(
    agent_type=AgentType.AG_A2A_PHILOSOPHY,
    name="AG A2A Philosophy Agent",
    description="Philosophical reasoning and analysis via A2A Protocol",
    capabilities=[
        Capability(
            name="philosophical-analysis",
            description="Analyze philosophical concepts",
            keywords=["philosophy", "ethics", "logic", "reasoning"],
        ),
        Capability(
            name="critical-thinking",
            description="Apply critical thinking frameworks",
            keywords=["critical", "thinking", "argument", "dialectic"],
        ),
    ],
    supported_task_types=[TaskType.RESEARCH, TaskType.CUSTOM],
    adapter_type="a2a",
    endpoint="http://localhost:8004/",
    avg_execution_time_seconds=30,
)

AG_A2A_HISTORY = AgentCapabilities(
    agent_type=AgentType.AG_A2A_HISTORY,
    name="AG A2A History Agent",
    description="Historical context and analysis via A2A Protocol",
    capabilities=[
        Capability(
            name="historical-context",
            description="Provide historical context and analysis",
            keywords=["history", "historical", "timeline", "era", "period"],
        ),
        Capability(
            name="event-research",
            description="Research historical events",
            keywords=["event", "war", "revolution", "culture"],
        ),
    ],
    supported_task_types=[TaskType.RESEARCH, TaskType.CUSTOM],
    adapter_type="a2a",
    endpoint="http://localhost:8005/",
    avg_execution_time_seconds=30,
)

AG_A2A_CALCULATOR = AgentCapabilities(
    agent_type=AgentType.AG_A2A_CALCULATOR,
    name="AG A2A Calculator Agent",
    description="Mathematical calculations via A2A Protocol",
    capabilities=[
        Capability(
            name="math-calculation",
            description="Perform mathematical calculations",
            keywords=["math", "calculate", "arithmetic", "expression"],
        ),
        Capability(
            name="number-theory",
            description="Number theory operations",
            keywords=["fibonacci", "factorial", "prime", "number"],
        ),
    ],
    supported_task_types=[TaskType.CUSTOM],
    adapter_type="a2a",
    endpoint="http://localhost:8006/",
    avg_execution_time_seconds=10,
)

AG_A2A_GUI_TEST = AgentCapabilities(
    agent_type=AgentType.AG_A2A_GUI_TEST,
    name="AG A2A GUI Test Agent",
    description="GUI automation testing via A2A Protocol",
    capabilities=[
        Capability(
            name="gui-automation",
            description="Automate GUI interactions",
            keywords=["gui", "automation", "screen", "click", "keyboard"],
        ),
        Capability(
            name="screen-capture",
            description="Capture and analyze screen content",
            keywords=["screenshot", "capture", "visual", "pyautogui"],
        ),
    ],
    supported_task_types=[TaskType.QA, TaskType.VALIDATE],
    adapter_type="a2a",
    endpoint="http://localhost:8120/",
    avg_execution_time_seconds=45,
)


# =============================================================================
# Claude Code CLI Agents (1)
# =============================================================================

CLAUDE_CLI_PLAN = AgentCapabilities(
    agent_type=AgentType.CLAUDE_CLI_PLAN,
    name="Claude CLI Plan Agent",
    description="Analyzes codebases and generates implementation plans using Claude Code CLI in plan mode (read-only)",
    capabilities=[
        Capability(
            name="code-analysis",
            description="Analyze codebase structure and architecture",
            keywords=["analyze", "codebase", "architecture", "structure", "read"],
        ),
        Capability(
            name="implementation-planning",
            description="Generate implementation plans for features and changes",
            keywords=["plan", "implement", "design", "strategy", "approach"],
        ),
        Capability(
            name="code-review",
            description="Review code and provide feedback (read-only)",
            keywords=["review", "feedback", "quality", "inspect", "assess"],
        ),
    ],
    supported_task_types=[TaskType.PLAN, TaskType.SPEC, TaskType.RESEARCH],
    is_autonomous=True,
    adapter_type="a2a",
    endpoint="http://localhost:9018/",
    avg_execution_time_seconds=60,
    priority_boost=1,
)


# =============================================================================
# Capability Registry
# =============================================================================

# All agent capabilities
ALL_AGENT_CAPABILITIES: Dict[AgentType, AgentCapabilities] = {
    # Auto-Claude
    AgentType.AUTO_CLAUDE_PLANNER: AUTO_CLAUDE_PLANNER,
    AgentType.AUTO_CLAUDE_CODER: AUTO_CLAUDE_CODER,
    AgentType.AUTO_CLAUDE_QA_REVIEWER: AUTO_CLAUDE_QA_REVIEWER,
    AgentType.AUTO_CLAUDE_QA_FIXER: AUTO_CLAUDE_QA_FIXER,
    # AG autogen
    AgentType.AG_RESEARCH: AG_RESEARCH,
    AgentType.AG_ANALYST: AG_ANALYST,
    AgentType.AG_WRITER: AG_WRITER,
    AgentType.AG_REVIEWER: AG_REVIEWER,
    AgentType.AG_COORDINATOR: AG_COORDINATOR,
    # Claude Code CLI
    AgentType.CLAUDE_CLI_PLAN: CLAUDE_CLI_PLAN,
    # AG law-domain
    AgentType.AG_CASE_ANALYZER: AG_CASE_ANALYZER,
    AgentType.AG_LEGAL_RESEARCHER: AG_LEGAL_RESEARCHER,
    AgentType.AG_RISK_ASSESSOR: AG_RISK_ASSESSOR,
    AgentType.AG_COMPLIANCE_CHECKER: AG_COMPLIANCE_CHECKER,
    AgentType.AG_DOCUMENT_DRAFTER: AG_DOCUMENT_DRAFTER,
    # AG A2A Protocol
    AgentType.AG_A2A_POETRY: AG_A2A_POETRY,
    AgentType.AG_A2A_PHILOSOPHY: AG_A2A_PHILOSOPHY,
    AgentType.AG_A2A_HISTORY: AG_A2A_HISTORY,
    AgentType.AG_A2A_CALCULATOR: AG_A2A_CALCULATOR,
    AgentType.AG_A2A_GUI_TEST: AG_A2A_GUI_TEST,
}


def get_capabilities(agent_type: AgentType) -> Optional[AgentCapabilities]:
    """Get capabilities for an agent type"""
    return ALL_AGENT_CAPABILITIES.get(agent_type)


def get_agents_by_task_type(task_type: TaskType) -> List[AgentCapabilities]:
    """Get all agents that support a task type"""
    return [
        cap for cap in ALL_AGENT_CAPABILITIES.values()
        if task_type in cap.supported_task_types
    ]


def get_agents_by_adapter(adapter_type: str) -> List[AgentCapabilities]:
    """Get all agents using a specific adapter type"""
    return [
        cap for cap in ALL_AGENT_CAPABILITIES.values()
        if cap.adapter_type == adapter_type
    ]


def find_best_agents(
    task_type: TaskType,
    requirements: List[str],
    limit: int = 3,
) -> List[AgentCapabilities]:
    """
    Find best matching agents for a task.

    Args:
        task_type: Type of task
        requirements: Required capabilities
        limit: Maximum number of agents to return

    Returns:
        List of matching agents, sorted by score
    """
    candidates = get_agents_by_task_type(task_type)

    scored = []
    for agent in candidates:
        score = agent.matches_requirements(requirements)
        score += agent.priority_boost * 0.1  # Apply priority boost
        scored.append((score, agent))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [agent for _, agent in scored[:limit]]
