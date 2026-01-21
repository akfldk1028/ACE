"""
SharedMemory Client for AG-ACE-BRIDGE.

AG-CLI의 SharedMemory 서버(8101)에 연결하여 에이전트 간 상태 공유 및 이벤트 통신.
이 클라이언트를 통해 Auto-Claude와 AG 에이전트가 공통 메모리를 공유.

Usage:
    from src.memory import SharedMemoryClient

    client = SharedMemoryClient()

    # 상태 저장
    await client.store("api_spec", {"endpoints": [...]})

    # 상태 조회
    data = await client.get("api_spec")

    # 이벤트 발행
    await client.publish_event("task_completed", {"task_id": "abc"})
"""

import asyncio
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime
import httpx
from pydantic import BaseModel, Field


class Decision(BaseModel):
    """SharedMemory에 저장되는 결정/상태"""
    key: str
    data: Dict[str, Any]
    source: str  # 저장한 에이전트 이름
    timestamp: datetime = Field(default_factory=datetime.now)
    version: int = 1


class Event(BaseModel):
    """SharedMemory 이벤트"""
    id: str
    event_type: str
    data: Dict[str, Any]
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SharedMemoryClient:
    """
    AG-CLI SharedMemory 서버 클라이언트.

    AG-CLI의 SharedMemory(port 8101)에 HTTP로 연결하여:
    - 상태(Decision) 저장/조회
    - 이벤트 발행/구독
    - 파일 락 관리

    이를 통해 Auto-Claude와 AG 에이전트가 컨텍스트를 공유.

    Architecture:
        AG-ACE-BRIDGE                    AG-CLI
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
        source_name: str = "ag-ace-bridge",
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        SharedMemory 클라이언트 초기화.

        Args:
            base_url: SharedMemory 서버 URL (default: http://localhost:8101)
            source_name: 이 클라이언트를 식별하는 이름 (이벤트 source에 사용)
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
            response = await client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    async def get_status(self) -> Dict[str, Any]:
        """
        SharedMemory 서버 상태 조회.

        Returns:
            서버 상태 정보 (decisions count, events count, etc.)
        """
        client = await self._get_client()
        response = await client.get("/status")
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Decision (State) Operations
    # =========================================================================

    async def store(
        self,
        key: str,
        data: Dict[str, Any],
        source: Optional[str] = None,
    ) -> Decision:
        """
        상태를 SharedMemory에 저장.

        Args:
            key: 저장 키 (예: "api_spec", "schema", "task_result")
            data: 저장할 데이터
            source: 저장 주체 (기본값: self.source_name)

        Returns:
            저장된 Decision 객체

        Example:
            await client.store("api_spec", {"endpoints": ["/users", "/items"]})
        """
        client = await self._get_client()

        payload = {
            "key": key,
            "data": data,
            "source": source or self.source_name,
        }

        response = await client.post(f"/decisions/{key}", json=payload)
        response.raise_for_status()

        result = response.json()
        return Decision(**result)

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        SharedMemory에서 상태 조회.

        Args:
            key: 조회할 키

        Returns:
            저장된 데이터 또는 None (키가 없는 경우)

        Example:
            api_spec = await client.get("api_spec")
            if api_spec:
                endpoints = api_spec.get("endpoints", [])
        """
        client = await self._get_client()

        try:
            response = await client.get(f"/decisions/{key}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            result = response.json()
            return result.get("data")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_decision(self, key: str) -> Optional[Decision]:
        """
        SharedMemory에서 Decision 객체 전체 조회 (메타데이터 포함).

        Args:
            key: 조회할 키

        Returns:
            Decision 객체 또는 None
        """
        client = await self._get_client()

        try:
            response = await client.get(f"/decisions/{key}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return Decision(**response.json())
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def delete(self, key: str) -> bool:
        """
        SharedMemory에서 상태 삭제.

        Args:
            key: 삭제할 키

        Returns:
            True if deleted, False if not found
        """
        client = await self._get_client()

        try:
            response = await client.delete(f"/decisions/{key}")
            return response.status_code == 200
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise

    async def list_keys(self) -> List[str]:
        """
        SharedMemory에 저장된 모든 키 목록 조회.

        Returns:
            키 목록
        """
        client = await self._get_client()
        response = await client.get("/decisions")
        response.raise_for_status()
        return response.json().get("keys", [])

    # =========================================================================
    # Event Operations
    # =========================================================================

    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: Optional[str] = None,
    ) -> Event:
        """
        이벤트 발행.

        다른 에이전트들이 구독 중인 이벤트 타입으로 알림 전송.

        Args:
            event_type: 이벤트 타입 (예: "task_completed", "schema_ready")
            data: 이벤트 데이터
            source: 발행 주체 (기본값: self.source_name)

        Returns:
            발행된 Event 객체

        Example:
            await client.publish_event(
                "task_completed",
                {"task_id": "abc", "success": True}
            )
        """
        client = await self._get_client()

        payload = {
            "event_type": event_type,
            "data": data,
            "source": source or self.source_name,
        }

        response = await client.post("/events", json=payload)
        response.raise_for_status()

        result = response.json()
        return Event(**result)

    async def get_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        """
        이벤트 목록 조회.

        Args:
            event_type: 필터할 이벤트 타입 (None이면 전체)
            limit: 최대 조회 개수

        Returns:
            Event 목록
        """
        client = await self._get_client()

        params = {"limit": limit}
        if event_type:
            params["event_type"] = event_type

        response = await client.get("/events", params=params)
        response.raise_for_status()

        events_data = response.json().get("events", [])
        return [Event(**e) for e in events_data]

    # =========================================================================
    # Convenience Methods for AG-ACE-BRIDGE
    # =========================================================================

    async def store_task_result(
        self,
        task_id: str,
        stage: int,
        result: Dict[str, Any],
        agent_type: str,
    ) -> Decision:
        """
        파이프라인 스테이지 결과 저장.

        Args:
            task_id: 태스크 ID
            stage: 스테이지 번호
            result: 실행 결과
            agent_type: 실행한 에이전트 타입

        Returns:
            저장된 Decision
        """
        key = f"task_{task_id}_stage_{stage}"
        data = {
            "task_id": task_id,
            "stage": stage,
            "agent_type": agent_type,
            "result": result,
            "completed_at": datetime.now().isoformat(),
        }
        return await self.store(key, data, source=agent_type)

    async def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """
        태스크의 누적 컨텍스트 조회.

        모든 완료된 스테이지 결과를 수집하여 컨텍스트로 반환.

        Args:
            task_id: 태스크 ID

        Returns:
            누적 컨텍스트 (stage_0_output, stage_1_output, ...)
        """
        context = {}
        keys = await self.list_keys()

        # task_{task_id}_stage_{N} 패턴의 키들 조회
        prefix = f"task_{task_id}_stage_"
        for key in keys:
            if key.startswith(prefix):
                stage_data = await self.get(key)
                if stage_data:
                    stage_num = key.replace(prefix, "")
                    context[f"stage_{stage_num}_output"] = stage_data.get("result", {})

        return context

    async def notify_stage_complete(
        self,
        task_id: str,
        stage: int,
        agent_type: str,
        success: bool,
    ) -> Event:
        """
        스테이지 완료 이벤트 발행.

        Args:
            task_id: 태스크 ID
            stage: 완료된 스테이지 번호
            agent_type: 실행한 에이전트 타입
            success: 성공 여부

        Returns:
            발행된 Event
        """
        return await self.publish_event(
            event_type="stage_completed",
            data={
                "task_id": task_id,
                "stage": stage,
                "agent_type": agent_type,
                "success": success,
            },
        )

    async def notify_task_complete(
        self,
        task_id: str,
        success: bool,
        artifacts: Optional[List[str]] = None,
    ) -> Event:
        """
        태스크 완료 이벤트 발행.

        Args:
            task_id: 태스크 ID
            success: 성공 여부
            artifacts: 생성된 산출물 목록

        Returns:
            발행된 Event
        """
        return await self.publish_event(
            event_type="task_completed",
            data={
                "task_id": task_id,
                "success": success,
                "artifacts": artifacts or [],
            },
        )


# =========================================================================
# Module-level convenience functions
# =========================================================================

_default_client: Optional[SharedMemoryClient] = None


def get_client(
    base_url: str = SharedMemoryClient.DEFAULT_BASE_URL,
    source_name: str = "ag-ace-bridge",
) -> SharedMemoryClient:
    """
    기본 SharedMemoryClient 인스턴스 반환 (싱글톤).

    Args:
        base_url: SharedMemory 서버 URL
        source_name: 클라이언트 식별 이름

    Returns:
        SharedMemoryClient 인스턴스
    """
    global _default_client
    if _default_client is None:
        _default_client = SharedMemoryClient(base_url, source_name)
    return _default_client


async def store(key: str, data: Dict[str, Any]) -> Decision:
    """상태 저장 (편의 함수)."""
    return await get_client().store(key, data)


async def get(key: str) -> Optional[Dict[str, Any]]:
    """상태 조회 (편의 함수)."""
    return await get_client().get(key)


async def publish_event(event_type: str, data: Dict[str, Any]) -> Event:
    """이벤트 발행 (편의 함수)."""
    return await get_client().publish_event(event_type, data)
