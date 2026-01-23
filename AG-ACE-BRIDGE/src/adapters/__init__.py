"""
Adapters module for AG-ACE-BRIDGE

Provides adapters for connecting to different agent systems:
- Auto-Claude: Claude Agent SDK
- AG Autogen: HTTP/A2A Protocol
- AG A2A: Google ADK A2A Protocol (ports 8003-8009)
- AG Law Domain: HTTP/FastAPI
"""

from .base import AgentAdapter

from .auto_claude import (
    AutoClaudeAdapter,
    create_planner_adapter,
    create_coder_adapter,
    create_qa_reviewer_adapter,
    create_qa_fixer_adapter,
)

from .ag_autogen import (
    AGAutogenAdapter,
    create_research_adapter,
    create_analyst_adapter,
    create_writer_adapter,
    create_reviewer_adapter,
    create_coordinator_adapter,
)

from .ag_a2a_adapter import (
    AGA2AAdapter,
    A2AAgentType,
    A2AAdapterManager,
    create_poetry_adapter,
    create_philosophy_adapter,
    create_history_adapter,
    create_calculator_adapter,
    create_gui_test_adapter,
)

from .ag_law_domain import (
    AGLawDomainAdapter,
    create_case_analyzer_adapter,
    create_legal_researcher_adapter,
    create_risk_assessor_adapter,
    create_compliance_checker_adapter,
    create_document_drafter_adapter,
)

__all__ = [
    # Base
    "AgentAdapter",
    # Auto-Claude
    "AutoClaudeAdapter",
    "create_planner_adapter",
    "create_coder_adapter",
    "create_qa_reviewer_adapter",
    "create_qa_fixer_adapter",
    # AG Autogen
    "AGAutogenAdapter",
    "create_research_adapter",
    "create_analyst_adapter",
    "create_writer_adapter",
    "create_reviewer_adapter",
    "create_coordinator_adapter",
    # AG A2A Protocol (Google ADK)
    "AGA2AAdapter",
    "A2AAgentType",
    "A2AAdapterManager",
    "create_poetry_adapter",
    "create_philosophy_adapter",
    "create_history_adapter",
    "create_calculator_adapter",
    "create_gui_test_adapter",
    # AG Law Domain
    "AGLawDomainAdapter",
    "create_case_analyzer_adapter",
    "create_legal_researcher_adapter",
    "create_risk_assessor_adapter",
    "create_compliance_checker_adapter",
    "create_document_drafter_adapter",
]
