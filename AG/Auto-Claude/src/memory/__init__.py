"""
Memory sync module for AG/Auto-Claude.

AG-CLI의 SharedMemory(8101)에 연결하여 Auto-Claude와 AG 에이전트 간 상태 공유.

Usage:
    from src.memory import SharedMemoryClient, store, get, publish_event

    # 클래스 직접 사용
    client = SharedMemoryClient()
    await client.store("api_spec", {"endpoints": [...]})

    # 편의 함수 사용
    await store("api_spec", {"endpoints": [...]})
    data = await get("api_spec")
    await publish_event("task_completed", {"task_id": "abc"})
"""

from src.memory.shared_memory_client import (
    SharedMemoryClient,
    Decision,
    Event,
    get_client,
    store,
    get,
    publish_event,
)

__all__ = [
    "SharedMemoryClient",
    "Decision",
    "Event",
    "get_client",
    "store",
    "get",
    "publish_event",
]
