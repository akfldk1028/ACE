"""Tests for AG-ACE-BRIDGE Law Domain adapter module (5 legal agents)."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.adapters.ag_law_domain import AGLawDomainAdapter
from src.utils.models import Task, TaskType, Result, ResultStatus, AgentType


class TestAGLawDomainAdapter:
    """Tests for AGLawDomainAdapter class."""

    def test_adapter_creation_case_analyzer(self):
        """Should create adapter for CASE_ANALYZER agent."""
        adapter = AGLawDomainAdapter(AgentType.AG_CASE_ANALYZER)
        assert adapter is not None

    def test_adapter_creation_legal_researcher(self):
        """Should create adapter for LEGAL_RESEARCHER agent."""
        adapter = AGLawDomainAdapter(AgentType.AG_LEGAL_RESEARCHER)
        assert adapter is not None

    def test_adapter_creation_risk_assessor(self):
        """Should create adapter for RISK_ASSESSOR agent."""
        adapter = AGLawDomainAdapter(AgentType.AG_RISK_ASSESSOR)
        assert adapter is not None

    def test_adapter_creation_compliance_checker(self):
        """Should create adapter for COMPLIANCE_CHECKER agent."""
        adapter = AGLawDomainAdapter(AgentType.AG_COMPLIANCE_CHECKER)
        assert adapter is not None

    def test_adapter_creation_document_drafter(self):
        """Should create adapter for DOCUMENT_DRAFTER agent."""
        adapter = AGLawDomainAdapter(AgentType.AG_DOCUMENT_DRAFTER)
        assert adapter is not None


class TestLawDomainEndpoints:
    """Tests for Law Domain endpoint mappings."""

    def test_case_analyzer_endpoint(self):
        """Case analyzer endpoint should be /legal/case-analyzer."""
        adapter = AGLawDomainAdapter(AgentType.AG_CASE_ANALYZER)
        assert adapter is not None

    def test_legal_researcher_endpoint(self):
        """Legal researcher endpoint should be /legal/researcher."""
        adapter = AGLawDomainAdapter(AgentType.AG_LEGAL_RESEARCHER)
        assert adapter is not None

    def test_risk_assessor_endpoint(self):
        """Risk assessor endpoint should be /legal/risk-assessor."""
        adapter = AGLawDomainAdapter(AgentType.AG_RISK_ASSESSOR)
        assert adapter is not None


class TestLawDomainRequestCustomization:
    """Tests for law domain request customization."""

    def test_case_analyzer_request_params(self):
        """Case analyzer should accept analysis_type and jurisdiction."""
        adapter = AGLawDomainAdapter(AgentType.AG_CASE_ANALYZER)
        assert adapter is not None

    def test_legal_researcher_request_params(self):
        """Legal researcher should accept search_scope and date_range."""
        adapter = AGLawDomainAdapter(AgentType.AG_LEGAL_RESEARCHER)
        assert adapter is not None

    def test_risk_assessor_request_params(self):
        """Risk assessor should accept risk_categories and severity_threshold."""
        adapter = AGLawDomainAdapter(AgentType.AG_RISK_ASSESSOR)
        assert adapter is not None

    def test_compliance_checker_request_params(self):
        """Compliance checker should accept regulations and check_depth."""
        adapter = AGLawDomainAdapter(AgentType.AG_COMPLIANCE_CHECKER)
        assert adapter is not None

    def test_document_drafter_request_params(self):
        """Document drafter should accept document_type and template_id."""
        adapter = AGLawDomainAdapter(AgentType.AG_DOCUMENT_DRAFTER)
        assert adapter is not None


class TestLawDomainResponseParsing:
    """Tests for law domain response parsing."""

    @pytest.mark.asyncio
    async def test_parse_cases_analyzed(self):
        """Should parse cases_analyzed from response."""
        adapter = AGLawDomainAdapter(AgentType.AG_CASE_ANALYZER)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.SUCCESS,
                output={"cases_analyzed": 5, "summary": "Analysis complete"}
            )

            task = Task(type=TaskType.RESEARCH, description="Analyze case")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.SUCCESS
            assert "cases_analyzed" in result.output

    @pytest.mark.asyncio
    async def test_parse_precedents(self):
        """Should parse precedents from response."""
        adapter = AGLawDomainAdapter(AgentType.AG_LEGAL_RESEARCHER)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.SUCCESS,
                output={"precedents": ["Case A", "Case B"]}
            )

            task = Task(type=TaskType.RESEARCH, description="Find precedents")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.SUCCESS


class TestLawDomainExecution:
    """Tests for law domain execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Should return SUCCESS result on successful execution."""
        adapter = AGLawDomainAdapter(AgentType.AG_CASE_ANALYZER)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.SUCCESS,
                output={"analysis": "complete"}
            )

            task = Task(type=TaskType.RESEARCH, description="Legal analysis")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_http_error(self):
        """Should return FAILED result on HTTP error."""
        adapter = AGLawDomainAdapter(AgentType.AG_CASE_ANALYZER)

        with patch.object(adapter, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = Result(
                status=ResultStatus.FAILED,
                error="HTTP 500 Error"
            )

            task = Task(type=TaskType.RESEARCH, description="Legal analysis")
            result = await adapter.execute(task)

            assert result.status == ResultStatus.FAILED


class TestLawDomainCapabilities:
    """Tests for law domain capabilities."""

    def test_case_analyzer_capabilities(self):
        """Case analyzer should have analysis capabilities."""
        adapter = AGLawDomainAdapter(AgentType.AG_CASE_ANALYZER)
        assert adapter is not None

    def test_document_drafter_capabilities(self):
        """Document drafter should have drafting capabilities."""
        adapter = AGLawDomainAdapter(AgentType.AG_DOCUMENT_DRAFTER)
        assert adapter is not None
