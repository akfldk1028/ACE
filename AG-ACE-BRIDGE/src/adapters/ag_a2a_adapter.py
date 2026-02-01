"""
AG A2A Protocol Adapter for AG-ACE-BRIDGE

Connects to AG's autogen_a2a_kit agents via A2A Protocol (Google ADK).
Supports direct communication with A2A agents running on ports 8003-8009.

A2A Agents:
- poetry_agent (8003): 시/문학 분석
- philosophy_agent (8004): 철학적 사고
- history_agent (8005): 역사적 맥락
- calculator_agent (8006): 수학 계산
- gui_test_agent (8120): GUI 자동화

Protocol:
- Agent Card: GET /.well-known/agent.json
- Send Message: POST / (JSON-RPC 2.0 style)
"""

import asyncio
import httpx
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from src.adapters.base import AgentAdapter
from src.utils.models import Task, Result, ResultStatus, AgentMcpConfig
from src.utils.logger import Loggers


class A2AAgentType(str, Enum):
    """Available A2A Agents in AG autogen_a2a_kit"""
    POETRY = "poetry_agent"
    PHILOSOPHY = "philosophy_agent"
    HISTORY = "history_agent"
    CALCULATOR = "calculator_agent"
    GUI_TEST = "gui_test_agent"


# Agent port mappings
A2A_AGENT_PORTS = {
    A2AAgentType.POETRY: 8003,
    A2AAgentType.PHILOSOPHY: 8004,
    A2AAgentType.HISTORY: 8005,
    A2AAgentType.CALCULATOR: 8006,
    A2AAgentType.GUI_TEST: 8120,
}


# Agent capabilities
A2A_AGENT_CAPABILITIES = {
    A2AAgentType.POETRY: [
        "poem-analysis", "literary-devices", "poet-information",
        "structure-analysis", "korean-poetry", "english-poetry"
    ],
    A2AAgentType.PHILOSOPHY: [
        "philosophical-analysis", "ethical-reasoning", "critical-thinking",
        "concept-explanation", "thought-experiments"
    ],
    A2AAgentType.HISTORY: [
        "historical-context", "timeline-analysis", "event-research",
        "period-comparison", "cultural-history"
    ],
    A2AAgentType.CALCULATOR: [
        "math-calculation", "expression-eval", "fibonacci",
        "factorial", "basic-arithmetic"
    ],
    A2AAgentType.GUI_TEST: [
        "gui-automation", "screen-capture", "click-actions",
        "keyboard-input", "pyautogui"
    ],
}


class AGA2AAdapter(AgentAdapter):
    """
    Adapter for AG A2A Protocol agents.

    Connects to Google ADK-based A2A agents running in autogen_a2a_kit.
    Uses JSON-RPC 2.0 style messaging over HTTP.

    Example:
        adapter = AGA2AAdapter(A2AAgentType.CALCULATOR)
        await adapter.initialize()

        task = Task(description="Calculate 2 + 3 * 4")
        result = await adapter.execute(task, {})

    Protocol Flow:
        1. GET /.well-known/agent.json - Get agent card (capabilities)
        2. POST / - Send message/task to agent
        3. Receive JSON-RPC response
    """

    def __init__(
        self,
        agent_type: A2AAgentType,
        host: str = "127.0.0.1",
        enable_shared_memory: bool = False,
    ):
        """
        Initialize A2A adapter.

        Args:
            agent_type: Type of A2A agent to connect to
            host: Host where A2A agents are running
            enable_shared_memory: Enable SharedMemory integration
        """
        self.agent_type = agent_type
        self.port = A2A_AGENT_PORTS[agent_type]
        self.host = host
        self.base_url = f"http://{host}:{self.port}"

        super().__init__(
            name=agent_type.value,
            endpoint_url=self.base_url,
            enable_shared_memory=enable_shared_memory,
        )

        self.logger = Loggers.adapter()
        self._client: Optional[httpx.AsyncClient] = None
        self._agent_card: Optional[Dict] = None
        self._session_id: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize HTTP client and fetch agent card"""
        await super().initialize()

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=60.0,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        # Generate session ID for this adapter instance
        self._session_id = str(uuid.uuid4())

        # Try to fetch agent card
        try:
            self._agent_card = await self._fetch_agent_card()
            self.logger.info(
                "a2a_adapter_initialized",
                agent=self.agent_type.value,
                port=self.port,
                agent_name=self._agent_card.get("name", "unknown"),
            )
        except Exception as e:
            self.logger.warning(
                "a2a_agent_card_fetch_failed",
                agent=self.agent_type.value,
                error=str(e),
            )
            # Continue without agent card - might be available later

    async def shutdown(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
        await super().shutdown()
        self.logger.info("a2a_adapter_shutdown", agent=self.agent_type.value)

    async def _fetch_agent_card(self) -> Dict:
        """
        Fetch agent card from A2A endpoint.

        Returns:
            Agent card JSON with name, description, capabilities
        """
        # Try different agent card endpoints
        endpoints = [
            "/.well-known/agent.json",
            "/.well-known/agent-card.json",
        ]

        for endpoint in endpoints:
            try:
                response = await self._client.get(endpoint)
                if response.status_code == 200:
                    return response.json()
            except Exception:
                continue

        raise Exception("Failed to fetch agent card from any endpoint")

    async def execute(self, task: Task, context: Dict[str, Any], mcp_config: Optional[AgentMcpConfig] = None) -> Result:
        """
        Execute a task via A2A Protocol.

        Args:
            task: Task to execute
            context: Accumulated context from previous stages

        Returns:
            Result with output or error
        """
        if not self._client:
            await self.initialize()

        start_time = datetime.now()
        self.logger.info(
            "a2a_execute_start",
            task_id=task.id,
            agent=self.agent_type.value,
            description=task.description[:100],
        )

        try:
            # Build A2A request
            payload = self._build_a2a_message(task, context)

            # Send to A2A agent
            response = await self._client.post("/", json=payload)
            response.raise_for_status()
            response_data = response.json()

            # Parse response
            output = self._parse_a2a_response(response_data)

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            result = Result(
                task_id=task.id,
                status=ResultStatus.SUCCESS,
                output=output,
                agent_used=self.agent_type.value,
                execution_time_ms=execution_time,
            )

            self.logger.info(
                "a2a_execute_success",
                task_id=task.id,
                execution_time_ms=execution_time,
            )

            # Share result to SharedMemory if enabled
            if self.enable_shared_memory:
                await self._share_result(task, result)

            return result

        except httpx.ConnectError as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            error_msg = f"A2A 연결 실패: {self.agent_type.value} (port {self.port}) 서버가 실행 중인지 확인하세요."

            self.logger.error(
                "a2a_connect_error",
                task_id=task.id,
                agent=self.agent_type.value,
                port=self.port,
                error=str(e),
            )

            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=error_msg,
                agent_used=self.agent_type.value,
                execution_time_ms=execution_time,
            )

        except httpx.HTTPStatusError as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            self.logger.error(
                "a2a_http_error",
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
                "a2a_execute_failed",
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

    def _build_a2a_message(
        self,
        task: Task,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build A2A Protocol message.

        A2A uses JSON-RPC 2.0 style with specific message format.

        Args:
            task: Task to execute
            context: Context from previous stages

        Returns:
            A2A message payload
        """
        # Build message content
        message_content = task.description

        # Add context if available
        if context:
            context_str = "\n\n[Context from previous stages]:\n"
            for key, value in context.items():
                if isinstance(value, dict) and "output" in value:
                    context_str += f"- {key}: {value.get('output', {}).get('summary', str(value)[:200])}\n"
                else:
                    context_str += f"- {key}: {str(value)[:200]}\n"
            message_content += context_str

        return {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": task.id,
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": message_content,
                        }
                    ],
                },
            },
            "id": task.id,
        }

    def _parse_a2a_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse A2A Protocol response.

        Args:
            response: Raw A2A response

        Returns:
            Parsed output dictionary
        """
        # Handle JSON-RPC response
        if "result" in response:
            result = response["result"]

            # Handle artifacts format (Google ADK style)
            if isinstance(result, dict) and "artifacts" in result:
                for artifact in result["artifacts"]:
                    for part in artifact.get("parts", []):
                        if "text" in part:
                            return {
                                "text": part["text"],
                                "raw_response": result,
                            }

            # Extract text from message parts
            if isinstance(result, dict):
                if "message" in result:
                    message = result["message"]
                    if "parts" in message:
                        text_parts = [
                            p.get("text", "")
                            for p in message["parts"]
                            if p.get("type") == "text"
                        ]
                        return {
                            "text": "\n".join(text_parts),
                            "raw_response": result,
                        }
                return result
            return {"text": str(result)}

        elif "error" in response:
            error = response["error"]
            raise Exception(error.get("message", str(error)))

        else:
            return {"raw": response}

    async def health_check(self) -> bool:
        """Check if A2A agent is accessible"""
        if not self._client:
            try:
                await self.initialize()
            except Exception:
                return False

        try:
            # Try to fetch agent card as health check
            response = await self._client.get("/.well-known/agent.json")
            return response.status_code == 200
        except Exception:
            try:
                # Fallback: try root endpoint
                response = await self._client.get("/")
                return response.status_code in [200, 404, 405]  # Server is responding
            except Exception:
                return False

    def get_capabilities(self) -> List[str]:
        """Get capabilities for this A2A agent"""
        return A2A_AGENT_CAPABILITIES.get(self.agent_type, [])

    def get_agent_card(self) -> Optional[Dict]:
        """Get cached agent card"""
        return self._agent_card


# Factory functions for each A2A agent
# ★ 기본값 True: SharedMemory 동기화 항상 활성화 (Auto-Claude ↔ AG 통합)
def create_poetry_adapter(enable_shared_memory: bool = True) -> AGA2AAdapter:
    """Create Poetry A2A adapter (port 8003)"""
    return AGA2AAdapter(A2AAgentType.POETRY, enable_shared_memory=enable_shared_memory)


def create_philosophy_adapter(enable_shared_memory: bool = True) -> AGA2AAdapter:
    """Create Philosophy A2A adapter (port 8004)"""
    return AGA2AAdapter(A2AAgentType.PHILOSOPHY, enable_shared_memory=enable_shared_memory)


def create_history_adapter(enable_shared_memory: bool = True) -> AGA2AAdapter:
    """Create History A2A adapter (port 8005)"""
    return AGA2AAdapter(A2AAgentType.HISTORY, enable_shared_memory=enable_shared_memory)


def create_calculator_adapter(enable_shared_memory: bool = True) -> AGA2AAdapter:
    """Create Calculator A2A adapter (port 8006)"""
    return AGA2AAdapter(A2AAgentType.CALCULATOR, enable_shared_memory=enable_shared_memory)


def create_gui_test_adapter(enable_shared_memory: bool = True) -> AGA2AAdapter:
    """Create GUI Test A2A adapter (port 8120)"""
    return AGA2AAdapter(A2AAgentType.GUI_TEST, enable_shared_memory=enable_shared_memory)


class A2AAdapterManager:
    """
    Manager for multiple A2A adapters.

    Provides centralized control over all A2A agent connections.

    Example:
        manager = A2AAdapterManager()
        await manager.initialize_all()

        # Check all agents
        status = await manager.health_check_all()

        # Execute on specific agent
        result = await manager.execute(A2AAgentType.CALCULATOR, task, context)
    """

    def __init__(self, enable_shared_memory: bool = True):
        """Initialize manager with all A2A adapters (SharedMemory 기본 활성화)"""
        self.enable_shared_memory = enable_shared_memory
        self.adapters: Dict[A2AAgentType, AGA2AAdapter] = {}
        self.logger = Loggers.adapter()

    async def initialize_all(self, timeout_per_agent: float = 10.0) -> Dict[A2AAgentType, bool]:
        """
        Initialize all A2A adapters with per-agent timeout.

        Args:
            timeout_per_agent: Max seconds to wait per agent initialization

        Returns:
            Dict mapping agent type to initialization success
        """
        results = {}

        for agent_type in A2AAgentType:
            try:
                adapter = AGA2AAdapter(
                    agent_type,
                    enable_shared_memory=self.enable_shared_memory,
                )
                await asyncio.wait_for(
                    adapter.initialize(),
                    timeout=timeout_per_agent,
                )
                self.adapters[agent_type] = adapter
                results[agent_type] = True

            except asyncio.TimeoutError:
                self.logger.warning(
                    "a2a_adapter_init_timeout",
                    agent=agent_type.value,
                    timeout=timeout_per_agent,
                )
                # Cleanup partially initialized adapter
                try:
                    await adapter.shutdown()
                except Exception:
                    pass
                results[agent_type] = False

            except Exception as e:
                self.logger.warning(
                    "a2a_adapter_init_failed",
                    agent=agent_type.value,
                    error=str(e),
                )
                # Cleanup partially initialized adapter
                try:
                    await adapter.shutdown()
                except Exception:
                    pass
                results[agent_type] = False

        return results

    async def shutdown_all(self) -> None:
        """Shutdown all adapters"""
        for adapter in self.adapters.values():
            await adapter.shutdown()
        self.adapters.clear()

    async def health_check_all(self) -> Dict[A2AAgentType, bool]:
        """
        Check health of all A2A agents.

        Returns:
            Dict mapping agent type to health status
        """
        results = {}

        for agent_type, adapter in self.adapters.items():
            results[agent_type] = await adapter.health_check()

        return results

    async def execute(
        self,
        agent_type: A2AAgentType,
        task: Task,
        context: Dict[str, Any],
    ) -> Result:
        """
        Execute task on specific A2A agent.

        Args:
            agent_type: Which A2A agent to use
            task: Task to execute
            context: Context from previous stages

        Returns:
            Execution result
        """
        if agent_type not in self.adapters:
            return Result(
                task_id=task.id,
                status=ResultStatus.FAILED,
                error=f"A2A agent {agent_type.value} not initialized",
                agent_used=agent_type.value,
                execution_time_ms=0,
            )

        return await self.adapters[agent_type].execute(task, context)

    def get_available_agents(self) -> List[A2AAgentType]:
        """Get list of initialized agents"""
        return list(self.adapters.keys())
