"""
AG Law Domain Adapter for AG-ACE-BRIDGE

HTTP adapter for AG law-domain-agents.
Communicates via FastAPI HTTP endpoints.
"""

import asyncio
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.adapters.base import AgentAdapter
from src.utils.models import Task, Result, ResultStatus, AgentType, TaskType, AgentMcpConfig
from src.utils.logger import Loggers
from src.utils.config import get_settings


class AGLawDomainAdapter(AgentAdapter):
    """
    Adapter for AG law-domain-agents.

    Connects to legal domain agents via FastAPI HTTP endpoints.
    Supports 5 specialized legal agents:
    - Case Analyzer: Legal case analysis
    - Legal Researcher: Statute/regulation research
    - Risk Assessor: Legal risk evaluation
    - Compliance Checker: Regulatory compliance
    - Document Drafter: Legal document creation

    Example:
        adapter = AGLawDomainAdapter(AgentType.AG_CASE_ANALYZER)
        await adapter.initialize()

        task = Task(type=TaskType.RESEARCH, description="Analyze case X")
        result = await adapter.execute(task, {})
    """

    # Agent endpoint mappings
    AGENT_ENDPOINTS = {
        AgentType.AG_CASE_ANALYZER: "/legal/case-analyzer",
        AgentType.AG_LEGAL_RESEARCHER: "/legal/researcher",
        AgentType.AG_RISK_ASSESSOR: "/legal/risk-assessor",
        AgentType.AG_COMPLIANCE_CHECKER: "/legal/compliance-checker",
        AgentType.AG_DOCUMENT_DRAFTER: "/legal/document-drafter",
    }

    CAPABILITIES_MAP = {
        AgentType.AG_CASE_ANALYZER: [
            "case-law", "precedent-analysis", "legal-reasoning",
        ],
        AgentType.AG_LEGAL_RESEARCHER: [
            "statute-search", "regulation", "legal-research",
        ],
        AgentType.AG_RISK_ASSESSOR: [
            "risk-evaluation", "liability", "mitigation",
        ],
        AgentType.AG_COMPLIANCE_CHECKER: [
            "compliance", "regulation-check", "audit",
        ],
        AgentType.AG_DOCUMENT_DRAFTER: [
            "legal-docs", "contracts", "templates",
        ],
    }

    def __init__(self, agent_type: AgentType):
        """
        Initialize AG Law Domain adapter.

        Args:
            agent_type: Type of AG law domain agent
        """
        if agent_type not in self.AGENT_ENDPOINTS:
            raise ValueError(f"Invalid AG law domain agent type: {agent_type}")

        self.agent_type = agent_type
        self.endpoint_path = self.AGENT_ENDPOINTS[agent_type]

        settings = get_settings()
        base_url = settings.ag_law_domain_url

        super().__init__(
            name=agent_type.value,
            endpoint_url=f"{base_url}{self.endpoint_path}",
        )

        self.logger = Loggers.adapter()
        self.base_url = base_url
        self.timeout = settings.adapter_timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self) -> None:
        """Initialize HTTP client"""
        await super().initialize()

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        self.logger.info(
            "ag_law_domain_adapter_initialized",
            agent_type=self.agent_type.value,
            endpoint=self.endpoint_url,
        )

    async def shutdown(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
        await super().shutdown()
        self.logger.info("ag_law_domain_adapter_shutdown", agent_type=self.agent_type.value)

    async def execute(self, task: Task, context: Dict[str, Any], mcp_config: Optional[AgentMcpConfig] = None) -> Result:
        """
        Execute a legal task via HTTP.

        Args:
            task: Task to execute
            context: Accumulated context

        Returns:
            Result with output or error
        """
        if not self._client:
            await self.initialize()

        start_time = datetime.now()
        self.logger.info(
            "ag_law_domain_execute_start",
            task_id=task.id,
            agent_type=self.agent_type.value,
            endpoint=self.endpoint_path,
        )

        try:
            # Build request payload
            payload = self._build_request(task, context)

            # Send request
            response = await self._client.post(
                self.endpoint_path,
                json=payload,
            )

            response.raise_for_status()
            response_data = response.json()

            # Process response based on agent type
            output = self._process_response(response_data)

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            result = Result(
                task_id=task.id,
                status=ResultStatus.SUCCESS,
                output=output,
                agent_used=self.agent_type.value,
                execution_time_ms=execution_time,
            )

            self.logger.info(
                "ag_law_domain_execute_success",
                task_id=task.id,
                execution_time_ms=execution_time,
            )

            return result

        except httpx.HTTPStatusError as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.error(
                "ag_law_domain_http_error",
                task_id=task.id,
                status_code=e.response.status_code,
                error=str(e),
            )

            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=f"HTTP {e.response.status_code}: {str(e)}",
                agent_used=self.agent_type.value,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.error(
                "ag_law_domain_execute_failed",
                task_id=task.id,
                error=str(e),
            )

            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=str(e),
                agent_used=self.agent_type.value,
                execution_time_ms=execution_time,
            )

    def _build_request(
        self,
        task: Task,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build HTTP request payload.

        Args:
            task: Task to execute
            context: Context from previous stages

        Returns:
            Request payload
        """
        payload = {
            "task_id": task.id,
            "task_type": task.type if isinstance(task.type, str) else task.type.value,
            "description": task.description,
            "context": context,
            "requirements": task.requirements,
            "domain_validation": task.domain_validation,
        }

        # Add agent-specific parameters
        if self.agent_type == AgentType.AG_CASE_ANALYZER:
            payload["analysis_type"] = context.get("analysis_type", "comprehensive")
            payload["jurisdiction"] = context.get("jurisdiction", "general")

        elif self.agent_type == AgentType.AG_LEGAL_RESEARCHER:
            payload["search_scope"] = context.get("search_scope", "all")
            payload["date_range"] = context.get("date_range", None)

        elif self.agent_type == AgentType.AG_RISK_ASSESSOR:
            payload["risk_categories"] = context.get("risk_categories", [])
            payload["severity_threshold"] = context.get("severity_threshold", "medium")

        elif self.agent_type == AgentType.AG_COMPLIANCE_CHECKER:
            payload["regulations"] = context.get("regulations", [])
            payload["check_depth"] = context.get("check_depth", "standard")

        elif self.agent_type == AgentType.AG_DOCUMENT_DRAFTER:
            payload["document_type"] = context.get("document_type", "general")
            payload["template_id"] = context.get("template_id", None)

        return payload

    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process response based on agent type.

        Args:
            response: Raw response data

        Returns:
            Processed output
        """
        # Extract common fields
        output = {
            "raw_response": response,
            "status": response.get("status", "completed"),
        }

        # Agent-specific processing
        if self.agent_type == AgentType.AG_CASE_ANALYZER:
            output["cases_analyzed"] = response.get("cases", [])
            output["precedents"] = response.get("precedents", [])
            output["summary"] = response.get("summary", "")

        elif self.agent_type == AgentType.AG_LEGAL_RESEARCHER:
            output["statutes"] = response.get("statutes", [])
            output["regulations"] = response.get("regulations", [])
            output["sources"] = response.get("sources", [])

        elif self.agent_type == AgentType.AG_RISK_ASSESSOR:
            output["risks"] = response.get("risks", [])
            output["risk_score"] = response.get("overall_risk_score", 0)
            output["recommendations"] = response.get("recommendations", [])

        elif self.agent_type == AgentType.AG_COMPLIANCE_CHECKER:
            output["compliance_status"] = response.get("status", "unknown")
            output["violations"] = response.get("violations", [])
            output["recommendations"] = response.get("recommendations", [])

        elif self.agent_type == AgentType.AG_DOCUMENT_DRAFTER:
            output["document"] = response.get("document", "")
            output["sections"] = response.get("sections", [])
            output["metadata"] = response.get("metadata", {})

        return output

    async def health_check(self) -> bool:
        """Check if AG law domain endpoint is accessible"""
        if not self._client:
            try:
                await self.initialize()
            except Exception:
                return False

        try:
            # Try health endpoint
            response = await self._client.get("/health")
            return response.status_code == 200
        except Exception as e:
            self.logger.debug("ag_law_domain_health_check_failed", error=str(e))
            return False

    def get_capabilities(self) -> List[str]:
        """Get capabilities for this agent type"""
        return self.CAPABILITIES_MAP.get(self.agent_type, [])


# Factory functions for each agent type
def create_case_analyzer_adapter() -> AGLawDomainAdapter:
    """Create AG Case Analyzer adapter"""
    return AGLawDomainAdapter(AgentType.AG_CASE_ANALYZER)


def create_legal_researcher_adapter() -> AGLawDomainAdapter:
    """Create AG Legal Researcher adapter"""
    return AGLawDomainAdapter(AgentType.AG_LEGAL_RESEARCHER)


def create_risk_assessor_adapter() -> AGLawDomainAdapter:
    """Create AG Risk Assessor adapter"""
    return AGLawDomainAdapter(AgentType.AG_RISK_ASSESSOR)


def create_compliance_checker_adapter() -> AGLawDomainAdapter:
    """Create AG Compliance Checker adapter"""
    return AGLawDomainAdapter(AgentType.AG_COMPLIANCE_CHECKER)


def create_document_drafter_adapter() -> AGLawDomainAdapter:
    """Create AG Document Drafter adapter"""
    return AGLawDomainAdapter(AgentType.AG_DOCUMENT_DRAFTER)
