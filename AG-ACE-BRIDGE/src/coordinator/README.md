# Coordinator Module

중앙 조율 모듈. 24/7 오케스트레이터, 작업 큐, 에이전트 선택, 파이프라인 구성을 담당합니다.

## 구조

```
coordinator/
├── __init__.py
├── orchestrator.py      # 24/7 메인 루프 (핵심)
├── task_queue.py        # SQLite 기반 작업 큐
├── agent_selector.py    # 에이전트 선택 로직
└── pipeline_builder.py  # 파이프라인 동적 구성
```

## 핵심 컴포넌트

### orchestrator.py - 24/7 메인 루프

```python
class Orchestrator:
    """
    24/7 메인 오케스트레이터
    Coordinator/Dispatcher 패턴 구현
    """

    async def run_forever(self):
        """무한 루프 - 작업 큐에서 작업을 가져와 실행"""
        while True:
            task = await self.queue.pop()
            if task:
                pipeline = self.pipeline_builder.build(task)
                result = await self.execute_pipeline(pipeline, task)
                await self.handle_result(result)
            await asyncio.sleep(self.poll_interval)
```

### task_queue.py - 작업 큐

```python
class TaskQueue:
    """
    SQLite 기반 우선순위 작업 큐
    - Priority: HIGH > MEDIUM > LOW
    - FIFO within same priority
    - Retry support
    """

    async def push(self, task: Task) -> None: ...
    async def pop(self) -> Optional[Task]: ...
    async def peek(self) -> Optional[Task]: ...
    async def retry(self, task_id: str) -> None: ...
```

### agent_selector.py - 에이전트 선택

```python
class AgentSelector:
    """
    작업 요구사항 기반 에이전트 선택
    - Capability matching
    - Load balancing
    - Availability check
    """

    def select(self, requirements: List[str]) -> List[AgentType]: ...
```

### pipeline_builder.py - 파이프라인 구성

```python
class PipelineBuilder:
    """
    작업 유형에 따라 동적으로 파이프라인 구성
    - Sequential stages
    - Parallel stages
    - Critic loop stages
    """

    def build(self, task: Task) -> Pipeline: ...
```

## 사용법

```python
from src.coordinator import Orchestrator

# 오케스트레이터 생성 및 실행
orchestrator = Orchestrator()
await orchestrator.run_forever()
```

## 설계 패턴

- **Coordinator/Dispatcher Pattern** (Microsoft)
- 중앙 집중식 작업 라우팅
- 동적 에이전트 선택

## 관련 파일

- `src/utils/models.py`: Task, Result, Pipeline 모델
- `src/utils/config.py`: 설정 (poll_interval 등)
- `src/registry/`: 에이전트 레지스트리
