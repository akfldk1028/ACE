# SharedMemory Client for Auto-Claude A2A Integration
"""
Auto-Claude에서 SharedMemory(8101) 서버와 통신하는 클라이언트.

AG-ACE-BRIDGE의 SharedMemoryClient를 기반으로 Auto-Claude에 맞게 단순화.
A2A 에이전트 실행 결과를 SharedMemory에 저장하여 AG와 동기화.

Usage:
    from integrations.a2a.shared_memory import SharedMemoryClient

    client = SharedMemoryClient()

    # A2A 결과 저장
    await client.store_a2a_result("calculator_agent", "2+2", {"result": "4"})

    # 상태 조회
    data = await client.get("a2a_calculator_agent_latest")

    # 이벤트 발행
    await client.publish_event("a2a_call_completed", {"agent": "calculator_agent"})
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx


class SharedMemoryClient:
    """
    SharedMemory 서버 클라이언트 (Auto-Claude용).

    AG-CLI의 SharedMemory(port 8101)에 HTTP로 연결하여:
    - A2A 에이전트 호출 결과 저장
    - 상태 조회 및 이벤트 발행
    - Auto-Claude ↔ AG 동기화

    Architecture:
        Auto-Claude                      AG-CLI
        ┌─────────────────┐              ┌──────────────────┐
        │ SharedMemory    │──HTTP(8101)──│ SharedMemoryServer│
        │ Client          │              │                  │
        └─────────────────┘              └──────────────────┘
    """

    DEFAULT_BASE_URL = "http://localhost:8101"
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        source_name: str = "auto-claude",
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        SharedMemory 클라이언트 초기화.

        Args:
            base_url: SharedMemory 서버 URL (default: http://localhost:8101)
            source_name: 이 클라이언트를 식별하는 이름
            timeout: HTTP 요청 타임아웃 (초)
        """
        self.base_url = base_url.rstrip("/")
        self.source_name = source_name
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """클라이언트 연결 종료."""
        if self._client:
            await self._client.aclose()
            self._client = None

    # =========================================================================
    # Health & Status
    # =========================================================================

    async def health_check(self) -> bool:
        """
        SharedMemory 서버 연결 상태 확인.

        Returns:
            True if connected, False otherwise
        """
        try:
            client = await self._get_client()
            # AG-CLI SharedMemory uses / root endpoint (no /health)
            response = await client.get("/")
            return response.status_code == 200
        except Exception:
            return False

    async def is_available(self) -> bool:
        """SharedMemory 서버 사용 가능 여부 (alias for health_check)."""
        return await self.health_check()

    # =========================================================================
    # Core Operations
    # =========================================================================

    async def store(
        self,
        key: str,
        data: Dict[str, Any],
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        상태를 SharedMemory에 저장.

        Args:
            key: 저장 키 (category로 사용됨)
            data: 저장할 데이터 (decision으로 사용됨)
            source: 저장 주체 (기본값: self.source_name)

        Returns:
            저장 결과

        Example:
            await client.store("my_key", {"value": 123})
        """
        client = await self._get_client()

        # AG-CLI SharedMemory API: POST /decision
        # Body: {"category": str, "decision": Any, "agent": str}
        payload = {
            "category": key,
            "decision": data,
            "agent": source or self.source_name,
        }

        try:
            response = await client.post("/decision", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[SharedMemory] Store failed for key '{key}': {e}")
            return {"error": str(e), "success": False}

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        SharedMemory에서 상태 조회.

        Args:
            key: 조회할 키 (category)

        Returns:
            저장된 데이터 또는 None

        Example:
            data = await client.get("my_key")
        """
        client = await self._get_client()

        try:
            # AG-CLI SharedMemory API: GET /decision/{category}
            response = await client.get(f"/decision/{key}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            # AG-CLI returns the decision value directly
            return response.json()
        except Exception as e:
            print(f"[SharedMemory] Get failed for key '{key}': {e}")
            return None

    async def delete(self, key: str) -> bool:
        """상태 삭제."""
        client = await self._get_client()
        try:
            response = await client.delete(f"/decisions/{key}")
            return response.status_code == 200
        except Exception:
            return False

    async def list_keys(self) -> List[str]:
        """저장된 모든 키(category) 목록 조회."""
        client = await self._get_client()
        try:
            # AG-CLI SharedMemory API: GET /decisions returns dict of decisions
            response = await client.get("/decisions")
            response.raise_for_status()
            # AG-CLI returns {category: decision_dict, ...}
            result = response.json()
            return list(result.keys())
        except Exception:
            return []

    # =========================================================================
    # Event Operations
    # =========================================================================

    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        이벤트 발행.

        Args:
            event_type: 이벤트 타입 (예: "a2a_call_completed")
            data: 이벤트 데이터
            source: 발행 주체

        Returns:
            발행 결과

        Example:
            await client.publish_event("a2a_call_completed", {"agent": "calc"})
        """
        client = await self._get_client()

        # AG-CLI SharedMemory API: POST /event (singular!)
        payload = {
            "event_type": event_type,
            "data": data,
            "source": source or self.source_name,
        }

        try:
            response = await client.post("/event", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[SharedMemory] Publish event failed: {e}")
            return {"error": str(e), "success": False}

    async def get_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """이벤트 목록 조회."""
        client = await self._get_client()

        params = {"limit": limit}
        if event_type:
            params["event_type"] = event_type

        try:
            response = await client.get("/events", params=params)
            response.raise_for_status()
            return response.json().get("events", [])
        except Exception:
            return []

    # =========================================================================
    # A2A-specific Methods (Auto-Claude 전용)
    # =========================================================================

    async def store_a2a_result(
        self,
        agent_name: str,
        message: str,
        result: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        A2A 에이전트 호출 결과 저장.

        Args:
            agent_name: A2A 에이전트 이름 (예: "calculator_agent")
            message: 보낸 메시지
            result: 에이전트 응답 결과
            request_id: 요청 ID (없으면 자동 생성)

        Returns:
            저장 결과

        Example:
            await client.store_a2a_result(
                "calculator_agent",
                "2 + 3",
                {"success": True, "text": "5"}
            )
        """
        req_id = request_id or str(uuid.uuid4())[:8]
        key = f"a2a_{agent_name}_{req_id}"

        data = {
            "agent_name": agent_name,
            "message": message,
            "result": result,
            "request_id": req_id,
            "timestamp": datetime.now().isoformat(),
            "source": "auto-claude",
        }

        # 저장
        store_result = await self.store(key, data)

        # 최신 결과도 업데이트
        latest_key = f"a2a_{agent_name}_latest"
        await self.store(latest_key, data)

        # 이벤트 발행
        await self.publish_event(
            "a2a_call_completed",
            {
                "agent_name": agent_name,
                "request_id": req_id,
                "success": result.get("success", False),
            },
        )

        return store_result

    async def get_a2a_latest(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        A2A 에이전트의 최신 결과 조회.

        Args:
            agent_name: A2A 에이전트 이름

        Returns:
            최신 결과 또는 None
        """
        key = f"a2a_{agent_name}_latest"
        return await self.get(key)

    async def get_a2a_history(
        self,
        agent_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        A2A 호출 히스토리 조회.

        Args:
            agent_name: 특정 에이전트만 필터 (None이면 전체)
            limit: 최대 개수

        Returns:
            호출 히스토리 목록
        """
        keys = await self.list_keys()

        # a2a_ 프리픽스로 시작하는 키들 필터
        a2a_keys = [k for k in keys if k.startswith("a2a_") and not k.endswith("_latest")]

        if agent_name:
            a2a_keys = [k for k in a2a_keys if agent_name in k]

        # 최신순 정렬 (키에 타임스탬프가 없으므로 그냥 역순)
        a2a_keys = a2a_keys[-limit:]

        results = []
        for key in a2a_keys:
            data = await self.get(key)
            if data:
                results.append(data)

        return results


# =========================================================================
# Module-level singleton
# =========================================================================

_default_client: Optional[SharedMemoryClient] = None


def get_shared_memory_client(
    base_url: str = SharedMemoryClient.DEFAULT_BASE_URL,
) -> SharedMemoryClient:
    """
    기본 SharedMemoryClient 인스턴스 반환 (싱글톤).

    Args:
        base_url: SharedMemory 서버 URL

    Returns:
        SharedMemoryClient 인스턴스
    """
    global _default_client
    if _default_client is None:
        _default_client = SharedMemoryClient(base_url)
    return _default_client


async def store_a2a_result(
    agent_name: str,
    message: str,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """A2A 결과 저장 (편의 함수)."""
    return await get_shared_memory_client().store_a2a_result(agent_name, message, result)


async def get_a2a_latest(agent_name: str) -> Optional[Dict[str, Any]]:
    """A2A 최신 결과 조회 (편의 함수)."""
    return await get_shared_memory_client().get_a2a_latest(agent_name)
