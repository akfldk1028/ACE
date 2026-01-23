# A2A Client - AutoGen Studio A2A Agent Registry Client
"""
AutoGen Studio A2A 에이전트와 통신하는 클라이언트.

SharedMemory 연동 지원:
- enable_shared_memory=True로 설정하면 결과가 SharedMemory(8101)에 저장됨
- Auto-Claude ↔ AG 동기화 가능
"""
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

# SharedMemory 연동 (옵션)
try:
    from integrations.a2a.shared_memory import get_shared_memory_client, SharedMemoryClient
    SHARED_MEMORY_AVAILABLE = True
except ImportError:
    SHARED_MEMORY_AVAILABLE = False
    SharedMemoryClient = None


@dataclass
class A2AAgent:
    """A2A 에이전트 정보"""
    name: str
    display_name: str
    url: str
    description: str = ""
    skills: List[dict] = field(default_factory=list)
    is_online: bool = False
    timeout: int = 300  # CLI 에이전트용 5분

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "url": self.url,
            "description": self.description,
            "skills": self.skills,
            "is_online": self.is_online,
            "timeout": self.timeout,
        }


class A2AClient:
    """
    A2A 에이전트 호출 클라이언트.

    AutoGen Studio 없이도 직접 A2A 프로토콜로 에이전트를 호출할 수 있습니다.

    SharedMemory 연동:
        enable_shared_memory=True로 설정하면 A2A 호출 결과가
        SharedMemory(8101)에 자동 저장되어 AG와 동기화됩니다.

    Example:
        client = A2AClient("http://localhost:8006", enable_shared_memory=True)
        result = await client.send_message("2 + 3")
        # 결과가 SharedMemory에도 저장됨
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 300,
        enable_shared_memory: bool = True,  # ★ 항상 True (Auto-Claude ↔ AG 동기화)
        agent_name: Optional[str] = None,
    ):
        """
        Args:
            base_url: A2A 서버 URL (예: http://localhost:8003)
            timeout: 요청 타임아웃 (초)
            enable_shared_memory: SharedMemory 연동 활성화
            agent_name: 에이전트 이름 (SharedMemory 저장용, 없으면 URL에서 추출)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.enable_shared_memory = enable_shared_memory and SHARED_MEMORY_AVAILABLE
        self.agent_name = agent_name or self._extract_agent_name(base_url)
        self._shared_memory: Optional[SharedMemoryClient] = None

    def _extract_agent_name(self, url: str) -> str:
        """URL에서 에이전트 이름 추출 (포트 기반)."""
        port_to_agent = {
            "8003": "poetry_agent",
            "8004": "philosophy_agent",
            "8005": "history_agent",
            "8006": "calculator_agent",
            "8120": "gui_test_agent",
        }
        for port, name in port_to_agent.items():
            if f":{port}" in url:
                return name
        return "unknown_agent"

    async def _get_shared_memory(self) -> Optional[SharedMemoryClient]:
        """SharedMemory 클라이언트 가져오기 (lazy init)."""
        if not self.enable_shared_memory:
            return None
        if self._shared_memory is None and SHARED_MEMORY_AVAILABLE:
            self._shared_memory = get_shared_memory_client()
        return self._shared_memory

    async def get_agent_card(self) -> Optional[Dict[str, Any]]:
        """에이전트 카드(.well-known/agent.json) 가져오기"""
        try:
            url = f"{self.base_url}/.well-known/agent.json"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Failed to get agent card from {self.base_url}: {e}")
            return None

    async def is_online(self) -> bool:
        """에이전트 온라인 상태 확인"""
        card = await self.get_agent_card()
        return card is not None

    async def send_message(self, message: str) -> Dict[str, Any]:
        """
        A2A 프로토콜로 메시지 전송

        Args:
            message: 보낼 메시지

        Returns:
            에이전트 응답

        Note:
            enable_shared_memory=True인 경우 결과가 SharedMemory(8101)에도 저장됩니다.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": str(uuid.uuid4()),
                    "role": "user",
                    "parts": [{"type": "text", "text": message}]
                }
            }
        }

        result_data: Dict[str, Any] = {}

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                result = response.json()

                # 응답 파싱
                if "result" in result and "artifacts" in result["result"]:
                    for artifact in result["result"]["artifacts"]:
                        for part in artifact.get("parts", []):
                            if "text" in part:
                                result_data = {
                                    "success": True,
                                    "text": part["text"],
                                    "raw": result
                                }
                                break
                        if result_data:
                            break

                if not result_data:
                    if "error" in result:
                        result_data = {
                            "success": False,
                            "error": result["error"],
                            "raw": result
                        }
                    else:
                        result_data = {
                            "success": True,
                            "text": str(result),
                            "raw": result
                        }

        except Exception as e:
            result_data = {
                "success": False,
                "error": f"A2A 호출 실패: {str(e)}",
                "raw": None
            }

        # SharedMemory에 결과 저장 (활성화된 경우)
        await self._sync_to_shared_memory(message, result_data)

        return result_data

    async def _sync_to_shared_memory(
        self,
        message: str,
        result: Dict[str, Any],
    ) -> None:
        """SharedMemory에 A2A 결과 동기화."""
        if not self.enable_shared_memory:
            return

        try:
            shared_memory = await self._get_shared_memory()
            if shared_memory:
                await shared_memory.store_a2a_result(
                    agent_name=self.agent_name,
                    message=message,
                    result=result,
                )
                print(f"[A2AClient] Synced to SharedMemory: {self.agent_name}")
        except Exception as e:
            # SharedMemory 연동 실패해도 A2A 결과는 반환
            print(f"[A2AClient] SharedMemory sync failed: {e}")

    def send_message_sync(self, message: str) -> Dict[str, Any]:
        """동기 버전의 메시지 전송"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_message(message))


def call_a2a_agent(
    agent_url: str,
    message: str,
    timeout: int = 300,
    enable_shared_memory: bool = True,  # ★ 항상 True (Auto-Claude ↔ AG 동기화)
) -> str:
    """
    A2A 에이전트 간편 호출 함수

    Args:
        agent_url: A2A 서버 URL
        message: 보낼 메시지
        timeout: 타임아웃 (초)
        enable_shared_memory: SharedMemory 동기화 활성화

    Returns:
        에이전트 응답 텍스트

    Example:
        # SharedMemory 동기화 활성화
        result = call_a2a_agent(
            "http://localhost:8006",
            "2 + 3",
            enable_shared_memory=True
        )
    """
    client = A2AClient(agent_url, timeout, enable_shared_memory=enable_shared_memory)
    result = client.send_message_sync(message)

    if result["success"]:
        return result["text"]
    else:
        return f"에러: {result.get('error', 'Unknown error')}"
