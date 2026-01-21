"""
Base Agent Adapter Interface

All adapters must implement this interface for consistent agent interaction.

SharedMemory Integration:
    모든 어댑터는 선택적으로 SharedMemory에 연결하여:
    - 실행 결과를 중앙 저장소에 공유
    - 다른 에이전트의 컨텍스트 조회
    - 이벤트 발행/구독
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from ..utils.models import Task, Result, AgentCapability


class AgentAdapter(ABC):
    """
    Base class for all agent adapters.

    Provides a consistent interface for executing tasks on different agent systems:
    - Auto-Claude (Claude Agent SDK)
    - AG autogen_a2a_kit (HTTP/A2A Protocol)
    - AG law-domain-agents (HTTP/FastAPI)

    SharedMemory Integration:
        어댑터가 execute() 완료 후 결과를 SharedMemory에 자동 저장 가능.
        enable_shared_memory=True로 설정 시 활성화.
    """

    def __init__(
        self,
        name: str,
        endpoint_url: str = None,
        enable_shared_memory: bool = False,
        shared_memory_url: str = "http://localhost:8101",
    ):
        """
        Initialize the adapter.

        Args:
            name: Unique identifier for this adapter
            endpoint_url: URL for HTTP-based agents (optional)
            enable_shared_memory: SharedMemory 연동 활성화 여부
            shared_memory_url: SharedMemory 서버 URL
        """
        self.name = name
        self.endpoint_url = endpoint_url
        self._is_initialized = False

        # SharedMemory integration
        self.enable_shared_memory = enable_shared_memory
        self.shared_memory_url = shared_memory_url
        self._shared_memory_client = None

    async def initialize(self) -> None:
        """
        Initialize the adapter (e.g., establish connections).
        Called once before first use.
        """
        self._is_initialized = True

        # SharedMemory 클라이언트 초기화
        if self.enable_shared_memory:
            from ..memory import SharedMemoryClient
            self._shared_memory_client = SharedMemoryClient(
                base_url=self.shared_memory_url,
                source_name=self.name,
            )

    async def shutdown(self) -> None:
        """
        Clean up resources when shutting down.
        """
        self._is_initialized = False

        # SharedMemory 클라이언트 정리
        if self._shared_memory_client:
            await self._shared_memory_client.close()
            self._shared_memory_client = None

    async def _share_result(self, task: Task, result: Result) -> None:
        """
        실행 결과를 SharedMemory에 저장.

        Args:
            task: 실행한 태스크
            result: 실행 결과
        """
        if not self._shared_memory_client:
            return

        try:
            # 결과 저장
            await self._shared_memory_client.store(
                key=f"result_{task.id}_{self.name}",
                data={
                    "task_id": task.id,
                    "agent": self.name,
                    "success": result.success,
                    "output": result.output,
                    "execution_time_ms": result.execution_time_ms,
                    "insights": result.insights,
                },
            )

            # 완료 이벤트 발행
            await self._shared_memory_client.publish_event(
                event_type="agent_task_completed",
                data={
                    "task_id": task.id,
                    "agent": self.name,
                    "success": result.success,
                },
            )
        except Exception:
            # SharedMemory 오류는 무시 (핵심 로직에 영향 없도록)
            pass

    async def _get_shared_context(self, task: Task) -> Dict[str, Any]:
        """
        SharedMemory에서 관련 컨텍스트 조회.

        Args:
            task: 현재 태스크

        Returns:
            SharedMemory에서 조회한 컨텍스트
        """
        if not self._shared_memory_client:
            return {}

        try:
            return await self._shared_memory_client.get_task_context(task.id)
        except Exception:
            return {}

    @abstractmethod
    async def execute(self, task: Task, context: Dict[str, Any]) -> Result:
        """
        Execute a task using this agent.

        Args:
            task: The task to execute
            context: Accumulated context from previous pipeline stages

        Returns:
            Result containing output, status, and any follow-up tasks
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the agent is available and healthy.

        Returns:
            True if agent is available, False otherwise
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get the list of capabilities this agent provides.

        Returns:
            List of capability strings (e.g., ["research", "analysis"])
        """
        pass

    def get_agent_info(self) -> AgentCapability:
        """
        Get full agent capability information.

        Returns:
            AgentCapability model with all metadata
        """
        from ..utils.models import AgentType

        return AgentCapability(
            agent=AgentType(self.name) if self.name in [e.value for e in AgentType] else AgentType.AUTO_CLAUDE_CODER,
            capabilities=self.get_capabilities(),
            description=self.__class__.__doc__ or f"Adapter for {self.name}",
            endpoint_url=self.endpoint_url,
            is_available=self._is_initialized,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, initialized={self._is_initialized})"
