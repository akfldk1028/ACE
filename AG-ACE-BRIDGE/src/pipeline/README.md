# Pipeline Module

실행 흐름 모듈. Sequential, Parallel, Critic Loop 패턴을 구현합니다.

## 구조

```
pipeline/
├── __init__.py
├── sequential.py     # Sequential 패턴
├── parallel.py       # Fan-Out/Gather 패턴
├── critic_loop.py    # Generator-Critic 루프
└── stages.py         # 스테이지 정의
```

## 핵심 컴포넌트

### sequential.py - Sequential Pipeline

```
[Stage1] → [Stage2] → [Stage3] → [Stage4] → Result
```

```python
class SequentialPipeline:
    """
    선형 파이프라인 실행
    - 각 스테이지의 출력이 다음 스테이지의 입력
    - 컨텍스트 누적
    """

    async def execute(self, stages: List[Stage], context: dict) -> Result:
        for stage in stages:
            adapter = self.get_adapter(stage.agent)
            result = await adapter.execute(task, context)
            context.update(result.output)
        return result
```

### parallel.py - Parallel Fan-Out/Gather

```
        ┌→ [Agent A] ─┐
Input → ├→ [Agent B] ─┼→ [Gather] → Result
        └→ [Agent C] ─┘
```

```python
class ParallelPipeline:
    """
    병렬 실행 후 결과 집계
    - 동시 실행으로 시간 단축
    - 결과 병합 전략 지원
    """

    async def execute(self, agents: List[AgentType], task: Task) -> Result:
        tasks = [adapter.execute(task, context) for adapter in adapters]
        results = await asyncio.gather(*tasks)
        return self.merge_results(results)
```

### critic_loop.py - Generator-Critic Loop

```
[Generator] → [Critic] → Approved? → Done
     ↑            │          │
     │            └── No ────┘
     │                 │
     └─── [Fixer] ◄────┘
         (max 5 iterations)
```

```python
class CriticLoop:
    """
    Generator-Critic 패턴 (Google ADK)
    - Auto-Claude QA Loop의 핵심
    - 최대 반복 횟수 제한
    """

    async def execute(
        self,
        generator: AgentAdapter,
        critic: AgentAdapter,
        fixer: AgentAdapter,
        max_iterations: int = 5
    ) -> Result:
        result = await generator.execute(task, context)

        for i in range(max_iterations):
            critique = await critic.review(result)
            if critique.approved:
                return result
            result = await fixer.fix(critique.issues)

        return result  # Max iterations reached
```

## 파이프라인 조합

실제 사용에서는 여러 패턴을 조합합니다:

```
[Parallel Research] → [Sequential Spec→Plan→Code] → [Critic QA Loop]
      (AG)                    (Auto-Claude)              (Auto-Claude)
```

## 사용법

```python
from src.pipeline import SequentialPipeline, ParallelPipeline, CriticLoop

# Sequential
seq = SequentialPipeline()
result = await seq.execute(stages, context)

# Parallel
par = ParallelPipeline()
result = await par.execute(agents, task)

# Critic Loop
loop = CriticLoop()
result = await loop.execute(coder, qa_reviewer, qa_fixer)
```

## 설계 패턴

- **Sequential Pipeline Pattern** (Microsoft/Google)
- **Parallel Fan-Out/Gather Pattern** (Microsoft)
- **Generator-Critic Loop Pattern** (Google ADK)

## 관련 파일

- `src/utils/models.py`: Stage, Pipeline 모델
- `src/adapters/`: 에이전트 어댑터
- `src/coordinator/pipeline_builder.py`: 파이프라인 구성
