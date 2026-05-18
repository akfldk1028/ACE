# AG-CLI SharedMemory MCP Server
# 에이전트 간 정보 공유 및 이벤트 발행
"""
SharedMemory는 에이전트 간 정보를 공유하는 중앙 저장소입니다.

주요 기능:
1. 아키텍처 결정 저장 (DB 스키마, API 스펙 등)
2. 이벤트 발행/구독 (schema_ready, api_ready 등)
3. 파일 락 관리 (동시 수정 방지)
4. 타입 정의 공유

사용법:
    # MCP 서버로 실행
    python shared_memory.py

    # 에이전트에서 사용
    await mcp("shared-memory", "store_decision", {"category": "schema", "decision": {...}})
    schema = await mcp("shared-memory", "get_decision", {"category": "schema"})
"""
import asyncio
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
from pathlib import Path
import sys

# FastAPI (REST API 엔드포인트)
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("[WARN] 'fastapi' library not installed. Install with: pip install fastapi uvicorn")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """아키텍처 결정 (스키마, API 스펙 등)"""
    category: str
    value: Any
    updated_by: str
    updated_at: str
    version: int = 1

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Event:
    """이벤트 (schema_ready, api_ready 등)"""
    event_type: str
    data: Dict[str, Any]
    source: str
    timestamp: str
    event_id: str = ""
    delivered_to: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileLock:
    """파일 락"""
    file_path: str
    locked_by: str
    locked_at: str
    expires_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class SharedMemoryServer:
    """에이전트 간 정보 공유 서버"""

    def __init__(self, storage_path: Optional[str] = None):
        # 아키텍처 결정 저장소
        self.decisions: Dict[str, Decision] = {}
        # 이벤트 저장소
        self.events: List[Event] = []
        # 파일 락 저장소
        self.locks: Dict[str, FileLock] = {}
        # 구독자 큐 (이벤트 스트리밍용)
        self.subscribers: Dict[str, asyncio.Queue] = {}
        # 영구 저장 경로
        self.storage_path = Path(storage_path) if storage_path else None
        # 이벤트 카운터
        self._event_counter = 0

        # 저장된 데이터 로드
        if self.storage_path and self.storage_path.exists():
            self._load()

    # === 아키텍처 결정 ===

    def store_decision(self, category: str, decision: Any, agent: str = "unknown") -> dict:
        """아키텍처 결정 저장

        Args:
            category: 결정 카테고리 (schema, api_spec, types 등)
            decision: 결정 내용 (dict 또는 any)
            agent: 저장하는 에이전트 이름

        Returns:
            저장된 결정 정보
        """
        version = 1
        if category in self.decisions:
            version = self.decisions[category].version + 1

        self.decisions[category] = Decision(
            category=category,
            value=decision,
            updated_by=agent,
            updated_at=datetime.now().isoformat(),
            version=version
        )

        self._save()
        logger.info(f"Decision stored: {category} v{version} by {agent}")

        # 변경 이벤트 발행
        self.publish_event(
            event_type=f"{category}_updated",
            data={"category": category, "version": version},
            source=agent
        )

        return self.decisions[category].to_dict()

    def get_decision(self, category: str) -> Optional[Any]:
        """저장된 결정 조회"""
        if category in self.decisions:
            return self.decisions[category].value
        return None

    def get_all_decisions(self) -> Dict[str, dict]:
        """모든 결정 조회"""
        return {k: v.to_dict() for k, v in self.decisions.items()}

    # === API 스펙 공유 ===

    def publish_api_spec(self, endpoints: List[dict], agent: str = "backend") -> bool:
        """API 스펙 게시

        Args:
            endpoints: API 엔드포인트 목록
                [{"path": "/users", "methods": ["GET", "POST"], "description": "..."}]
            agent: 게시하는 에이전트

        Returns:
            성공 여부
        """
        self.store_decision(
            category="api_spec",
            decision={"endpoints": endpoints},
            agent=agent
        )

        # api_ready 이벤트 발행
        self.publish_event(
            event_type="api_ready",
            data={"endpoint_count": len(endpoints)},
            source=agent
        )

        return True

    def get_api_spec(self) -> List[dict]:
        """API 스펙 조회"""
        spec = self.get_decision("api_spec")
        if spec:
            return spec.get("endpoints", [])
        return []

    # === DB 스키마 공유 ===

    def publish_schema(self, tables: Dict[str, dict], agent: str = "db") -> bool:
        """DB 스키마 게시

        Args:
            tables: 테이블 정의
                {"users": {"id": "uuid", "email": "varchar(255)", ...}}
            agent: 게시하는 에이전트

        Returns:
            성공 여부
        """
        self.store_decision(
            category="schema",
            decision={"tables": tables},
            agent=agent
        )

        # schema_ready 이벤트 발행
        self.publish_event(
            event_type="schema_ready",
            data={"table_count": len(tables)},
            source=agent
        )

        return True

    def get_schema(self) -> Dict[str, dict]:
        """DB 스키마 조회"""
        schema = self.get_decision("schema")
        if schema:
            return schema.get("tables", {})
        return {}

    # === 이벤트 발행/구독 ===

    def publish_event(self, event_type: str, data: dict, source: str) -> Event:
        """이벤트 발행

        Args:
            event_type: 이벤트 유형 (schema_ready, api_ready, file_changed 등)
            data: 이벤트 데이터
            source: 발행 에이전트

        Returns:
            생성된 이벤트
        """
        self._event_counter += 1
        event = Event(
            event_id=f"evt_{self._event_counter}",
            event_type=event_type,
            data=data,
            source=source,
            timestamp=datetime.now().isoformat()
        )

        self.events.append(event)
        logger.info(f"Event published: {event_type} from {source}")

        # 모든 구독자에게 전달
        for agent_name, queue in self.subscribers.items():
            if agent_name != source:  # 자기 자신에게는 안 보냄
                asyncio.create_task(queue.put(event))

        return event

    async def subscribe(self, agent_name: str, event_types: List[str] = None) -> AsyncGenerator[Event, None]:
        """이벤트 구독 (async generator)

        Args:
            agent_name: 구독하는 에이전트 이름
            event_types: 구독할 이벤트 유형 (None이면 전체)

        Yields:
            Event: 이벤트
        """
        if agent_name not in self.subscribers:
            self.subscribers[agent_name] = asyncio.Queue()

        logger.info(f"Agent subscribed: {agent_name} for {event_types or 'all'}")

        while True:
            event = await self.subscribers[agent_name].get()
            if event_types is None or event.event_type in event_types:
                yield event

    def get_events(self, event_type: str = None, limit: int = 100) -> List[dict]:
        """이벤트 이력 조회"""
        events = self.events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return [e.to_dict() for e in events[-limit:]]

    # === 파일 락 ===

    def acquire_lock(self, file_path: str, agent: str, timeout_seconds: int = 300) -> bool:
        """파일 락 획득

        Args:
            file_path: 락을 걸 파일 경로
            agent: 락을 요청하는 에이전트
            timeout_seconds: 락 만료 시간 (기본 5분)

        Returns:
            성공 여부
        """
        # 이미 같은 에이전트가 락을 가지고 있으면 갱신
        if file_path in self.locks:
            existing = self.locks[file_path]
            if existing.locked_by == agent:
                # 갱신
                self.locks[file_path] = FileLock(
                    file_path=file_path,
                    locked_by=agent,
                    locked_at=datetime.now().isoformat(),
                    expires_at=(datetime.now().isoformat() if timeout_seconds else None)
                )
                return True

            # 만료 확인
            if existing.expires_at:
                expires = datetime.fromisoformat(existing.expires_at)
                if datetime.now() > expires:
                    # 만료됨, 새 락 획득 가능
                    del self.locks[file_path]
                else:
                    logger.warning(f"Lock denied: {file_path} held by {existing.locked_by}")
                    return False
            else:
                logger.warning(f"Lock denied: {file_path} held by {existing.locked_by}")
                return False

        # 새 락 획득
        expires_at = None
        if timeout_seconds:
            from datetime import timedelta
            expires_at = (datetime.now() + timedelta(seconds=timeout_seconds)).isoformat()

        self.locks[file_path] = FileLock(
            file_path=file_path,
            locked_by=agent,
            locked_at=datetime.now().isoformat(),
            expires_at=expires_at
        )

        logger.info(f"Lock acquired: {file_path} by {agent}")
        return True

    def release_lock(self, file_path: str, agent: str) -> bool:
        """파일 락 해제

        Args:
            file_path: 락을 해제할 파일 경로
            agent: 락을 해제하는 에이전트

        Returns:
            성공 여부
        """
        if file_path in self.locks:
            if self.locks[file_path].locked_by == agent:
                del self.locks[file_path]
                logger.info(f"Lock released: {file_path} by {agent}")
                return True
            else:
                logger.warning(f"Lock release denied: {file_path} not held by {agent}")
                return False
        return True  # 락이 없으면 성공

    def get_locks(self) -> Dict[str, dict]:
        """모든 락 조회"""
        return {k: v.to_dict() for k, v in self.locks.items()}

    def is_locked(self, file_path: str, by_agent: str = None) -> bool:
        """파일이 락 걸려있는지 확인"""
        if file_path not in self.locks:
            return False
        if by_agent:
            return self.locks[file_path].locked_by != by_agent
        return True

    # === 영구 저장 ===

    def _save(self):
        """데이터 저장"""
        if not self.storage_path:
            return

        data = {
            "decisions": {k: v.to_dict() for k, v in self.decisions.items()},
            "events": [e.to_dict() for e in self.events[-1000:]],  # 최근 1000개만
            "locks": {k: v.to_dict() for k, v in self.locks.items()},
            "saved_at": datetime.now().isoformat()
        }

        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self):
        """데이터 로드"""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Decisions 복원
            for k, v in data.get("decisions", {}).items():
                self.decisions[k] = Decision(**v)

            # Events 복원
            for e in data.get("events", []):
                self.events.append(Event(**e))

            # Locks는 복원하지 않음 (재시작 시 초기화)

            logger.info(f"Loaded {len(self.decisions)} decisions, {len(self.events)} events")

        except Exception as e:
            logger.error(f"Failed to load data: {e}")


# === FastAPI REST API ===

def create_fastapi_app(memory: SharedMemoryServer) -> FastAPI:
    """FastAPI 앱 생성"""
    app = FastAPI(title="AG-CLI SharedMemory")

    # CORS 설정 (Auto-Claude UI 브라우저 모드 지원)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발용: 모든 origin 허용
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # === Pydantic Models ===
    class StoreDecisionRequest(BaseModel):
        category: str
        decision: Any
        agent: str = "unknown"

    class PublishApiSpecRequest(BaseModel):
        endpoints: List[dict]
        agent: str = "backend"

    class PublishSchemaRequest(BaseModel):
        tables: Dict[str, dict]
        agent: str = "db"

    class PublishEventRequest(BaseModel):
        event_type: str
        data: dict
        source: str

    class LockRequest(BaseModel):
        file_path: str
        agent: str
        timeout_seconds: int = 300

    # === 상태 ===

    @app.get("/")
    async def root():
        return {
            "service": "AG-CLI SharedMemory",
            "decisions": list(memory.decisions.keys()),
            "events_count": len(memory.events),
            "locks_count": len(memory.locks)
        }

    # === 결정 ===

    @app.post("/decision")
    async def store_decision(req: StoreDecisionRequest):
        result = memory.store_decision(req.category, req.decision, req.agent)
        return result

    @app.get("/decision/{category}")
    async def get_decision(category: str):
        result = memory.get_decision(category)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Decision not found: {category}")
        return result

    @app.get("/decisions")
    async def get_all_decisions():
        return memory.get_all_decisions()

    # === API 스펙 ===

    @app.post("/api-spec")
    async def publish_api_spec(req: PublishApiSpecRequest):
        memory.publish_api_spec(req.endpoints, req.agent)
        return {"status": "published", "endpoint_count": len(req.endpoints)}

    @app.get("/api-spec")
    async def get_api_spec():
        return memory.get_api_spec()

    # === DB 스키마 ===

    @app.post("/schema")
    async def publish_schema(req: PublishSchemaRequest):
        memory.publish_schema(req.tables, req.agent)
        return {"status": "published", "table_count": len(req.tables)}

    @app.get("/schema")
    async def get_schema():
        return memory.get_schema()

    # === 이벤트 ===

    @app.post("/event")
    async def publish_event(req: PublishEventRequest):
        event = memory.publish_event(req.event_type, req.data, req.source)
        return event.to_dict()

    @app.get("/events")
    async def get_events(event_type: str = None, limit: int = 100):
        return memory.get_events(event_type, limit)

    # === 락 ===

    @app.post("/lock/acquire")
    async def acquire_lock(req: LockRequest):
        success = memory.acquire_lock(req.file_path, req.agent, req.timeout_seconds)
        if not success:
            raise HTTPException(status_code=409, detail="Lock held by another agent")
        return {"status": "acquired", "file_path": req.file_path}

    @app.post("/lock/release")
    async def release_lock(req: LockRequest):
        success = memory.release_lock(req.file_path, req.agent)
        return {"status": "released" if success else "not_held", "file_path": req.file_path}

    @app.get("/locks")
    async def get_locks():
        return memory.get_locks()

    @app.get("/lock/{file_path:path}")
    async def check_lock(file_path: str):
        is_locked = memory.is_locked(file_path)
        lock_info = memory.locks.get(file_path)
        return {
            "file_path": file_path,
            "is_locked": is_locked,
            "lock_info": lock_info.to_dict() if lock_info else None
        }

    return app


# === 메인 ===

async def main():
    """SharedMemory 서버 시작"""
    print("=" * 60)
    print("AG-CLI SharedMemory Server")
    print("=" * 60)

    storage_dir = Path(__file__).parent.parent / "data"
    storage_dir.mkdir(exist_ok=True)
    storage_file = storage_dir / "shared_memory.json"

    memory = SharedMemoryServer(storage_path=str(storage_file))

    if FASTAPI_AVAILABLE:
        app = create_fastapi_app(memory)
        config = uvicorn.Config(app, host="127.0.0.1", port=8101, log_level="info")
        server = uvicorn.Server(config)

        print(f"REST API: http://127.0.0.1:8101")
        print(f"Storage: {storage_file}")
        print("=" * 60)
        print("\nEndpoints:")
        print("  POST /decision - 결정 저장")
        print("  GET  /decision/{category} - 결정 조회")
        print("  POST /api-spec - API 스펙 게시")
        print("  GET  /api-spec - API 스펙 조회")
        print("  POST /schema - DB 스키마 게시")
        print("  GET  /schema - DB 스키마 조회")
        print("  POST /event - 이벤트 발행")
        print("  GET  /events - 이벤트 조회")
        print("  POST /lock/acquire - 파일 락 획득")
        print("  POST /lock/release - 파일 락 해제")
        print("=" * 60)

        await server.serve()
    else:
        print("ERROR: 'fastapi' library is required")
        print("Install with: pip install fastapi uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
