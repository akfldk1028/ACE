# Memory Module

AG-ACE-BRIDGE의 메모리 동기화 모듈. AG-CLI의 SharedMemory(8101)에 연결하여 Auto-Claude와 AG 에이전트 간 상태 공유.

## 핵심 개념

```
┌──────────────────────────────────────────────────────────────────┐
│                     AG-ACE-BRIDGE                                 │
│  ┌─────────────────┐    ┌─────────────────┐                      │
│  │ Auto-Claude     │    │   AG Agents     │                      │
│  │ Adapter         │    │   Adapter       │                      │
│  └────────┬────────┘    └────────┬────────┘                      │
│           │                      │                               │
│           └──────────┬───────────┘                               │
│                      ▼                                           │
│           ┌──────────────────────┐                               │
│           │ SharedMemoryClient   │  ← 이 모듈                    │
│           └──────────┬───────────┘                               │
└──────────────────────┼───────────────────────────────────────────┘
                       │ HTTP (8101)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     AG-CLI                                        │
│  ┌────────────────────────────────────────────────────────┐      │
│  │            SharedMemoryServer (8101)                   │      │
│  │  - Decisions (상태 저장)                               │      │
│  │  - Events (이벤트 발행/구독)                           │      │
│  │  - File Locks (파일 락)                                │      │
│  └────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────┘
```

## 파일 구조

```
src/memory/
├── __init__.py              # 모듈 export
├── shared_memory_client.py  # SharedMemory HTTP 클라이언트
└── README.md                # 이 파일
```

## 주요 클래스

### SharedMemoryClient

AG-CLI SharedMemory 서버에 HTTP로 연결하는 클라이언트.

```python
from src.memory import SharedMemoryClient

client = SharedMemoryClient(
    base_url="http://localhost:8101",  # AG-CLI SharedMemory 서버
    source_name="ag-ace-bridge",       # 클라이언트 식별 이름
)
```

**핵심 메서드**

| 메서드 | 설명 |
|--------|------|
| `store(key, data)` | 상태 저장 |
| `get(key)` | 상태 조회 |
| `delete(key)` | 상태 삭제 |
| `list_keys()` | 모든 키 목록 |
| `publish_event(type, data)` | 이벤트 발행 |
| `get_events(type, limit)` | 이벤트 조회 |
| `health_check()` | 서버 연결 확인 |

**편의 메서드 (파이프라인용)**

| 메서드 | 설명 |
|--------|------|
| `store_task_result(task_id, stage, result, agent)` | 스테이지 결과 저장 |
| `get_task_context(task_id)` | 태스크 누적 컨텍스트 조회 |
| `notify_stage_complete(task_id, stage, agent, success)` | 스테이지 완료 이벤트 |
| `notify_task_complete(task_id, success, artifacts)` | 태스크 완료 이벤트 |

### Decision

SharedMemory에 저장되는 상태 모델.

```python
class Decision(BaseModel):
    key: str               # 저장 키
    data: Dict[str, Any]   # 데이터
    source: str            # 저장 주체
    timestamp: datetime    # 저장 시간
    version: int           # 버전
```

### Event

SharedMemory 이벤트 모델.

```python
class Event(BaseModel):
    id: str                # 이벤트 ID
    event_type: str        # 이벤트 타입
    data: Dict[str, Any]   # 이벤트 데이터
    source: str            # 발행 주체
    timestamp: datetime    # 발행 시간
```

## 사용 예시

### 기본 사용

```python
from src.memory import SharedMemoryClient

async def main():
    client = SharedMemoryClient()

    # 상태 저장
    await client.store("api_spec", {
        "endpoints": ["/users", "/items"],
        "version": "1.0.0"
    })

    # 상태 조회
    api_spec = await client.get("api_spec")
    print(api_spec["endpoints"])  # ["/users", "/items"]

    # 이벤트 발행
    await client.publish_event(
        "api_ready",
        {"endpoints_count": 2}
    )

    await client.close()
```

### 편의 함수 사용

```python
from src.memory import store, get, publish_event

# 모듈 레벨 편의 함수 (싱글톤 클라이언트 사용)
await store("schema", {"tables": ["users", "orders"]})
schema = await get("schema")
await publish_event("schema_ready", {"tables_count": 2})
```

### 어댑터에서 사용

```python
from src.adapters.base import AgentAdapter

# SharedMemory 연동 활성화
adapter = MyAdapter(
    name="my_agent",
    enable_shared_memory=True,  # 활성화
    shared_memory_url="http://localhost:8101"
)

# execute() 완료 후 자동으로 결과 공유됨
result = await adapter.execute(task, context)
# → SharedMemory에 result_{task_id}_{agent_name} 저장
# → agent_task_completed 이벤트 발행
```

### 파이프라인에서 사용

```python
from src.memory import SharedMemoryClient

client = SharedMemoryClient()

# 스테이지 결과 저장
await client.store_task_result(
    task_id="task_123",
    stage=0,
    result={"code": "..."},
    agent_type="auto_claude_coder"
)

# 다음 스테이지에서 컨텍스트 조회
context = await client.get_task_context("task_123")
# context = {"stage_0_output": {"code": "..."}}
```

## 이벤트 타입

### 표준 이벤트

| 이벤트 타입 | 설명 | 데이터 |
|------------|------|--------|
| `agent_task_completed` | 에이전트 태스크 완료 | `{task_id, agent, success}` |
| `stage_completed` | 파이프라인 스테이지 완료 | `{task_id, stage, agent_type, success}` |
| `task_completed` | 전체 태스크 완료 | `{task_id, success, artifacts}` |

### 커스텀 이벤트

```python
# 스키마 준비 완료
await client.publish_event("schema_ready", {
    "tables": ["users", "orders", "items"],
    "source": "db_agent"
})

# API 준비 완료
await client.publish_event("api_ready", {
    "endpoints": ["/users", "/orders"],
    "version": "1.0.0"
})
```

## AG-CLI 서버 실행

SharedMemory 클라이언트를 사용하려면 AG-CLI SharedMemory 서버가 실행 중이어야 합니다.

```powershell
# AG-CLI SharedMemory 서버 시작
cd D:\Data\22_AG\autogen_a2a_kit\AG-cli
python mcp/shared_memory.py
# → Running on http://localhost:8101
```

## 설정

환경변수 또는 직접 설정:

```python
# 환경변수
SHARED_MEMORY_URL=http://localhost:8101

# 또는 직접 설정
client = SharedMemoryClient(
    base_url="http://localhost:8101"
)
```

## 에러 처리

SharedMemory 연결 오류는 핵심 로직에 영향을 주지 않도록 처리됩니다.

```python
# 어댑터에서 SharedMemory 오류 시
async def _share_result(self, task, result):
    try:
        await self._shared_memory_client.store(...)
    except Exception:
        pass  # 무시 - 핵심 로직 계속 진행
```

## 의존성

- `httpx>=0.24.0` - 비동기 HTTP 클라이언트
- `pydantic>=2.0.0` - 데이터 모델

## 관련 모듈

- `AG-CLI/mcp/shared_memory.py` - SharedMemory 서버 구현
- `src/adapters/base.py` - AgentAdapter SharedMemory 통합
- `src/pipeline/` - 파이프라인 컨텍스트 공유
