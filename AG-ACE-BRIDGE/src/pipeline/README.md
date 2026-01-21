# Pipeline Module

AG-ACE-BRIDGE의 실행 흐름 모듈. Sequential, Parallel, Critic Loop 패턴을 구현.

## 파일 구조

```
src/pipeline/
├── __init__.py       # 모듈 export
├── sequential.py     # 순차 파이프라인 (Google ADK 기반)
├── parallel.py       # 병렬 Fan-Out/Gather (Microsoft 기반)
├── critic_loop.py    # Generator-Critic 루프 (Google ADK 기반)
└── README.md         # 이 파일
```

## 아키텍처

```
┌────────────────────────────────────────────────────────────────────┐
│                      Pipeline Execution Patterns                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Sequential                2. Parallel                          │
│  ┌──────┐   ┌──────┐         ┌──────┐                             │
│  │Stage1│ → │Stage2│ → ...   │Agent1│ ─┐                          │
│  └──────┘   └──────┘         ├──────┤  ├→ Gather → Result         │
│                              │Agent2│ ─┤                           │
│                              ├──────┤  │                           │
│                              │Agent3│ ─┘                           │
│                              └──────┘                              │
│                                                                     │
│  3. Critic Loop                                                     │
│  ┌───────────┐    ┌────────┐    Pass?                             │
│  │ Generator │ →  │ Critic │ ──Yes──→ Done                        │
│  └───────────┘    └────────┘                                       │
│       ↑               │                                            │
│       └── Fixer ◄─────┘ (No, with feedback)                       │
│          (max N iterations)                                        │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

## 주요 컴포넌트

### sequential.py - 순차 파이프라인

**클래스 설명**
```python
class SequentialPipeline:
    """
    순차 파이프라인 실행기.

    각 스테이지의 출력이 다음 스테이지의 컨텍스트로 누적됨.
    Google ADK Sequential Pipeline 패턴 기반.

    Flow:
    Stage 1 → Stage 2 → Stage 3 → ... → Final Result
    """
```

**핵심 메서드**
```python
async def execute(
    self,
    task: Task,
    stages: List[Stage],
    initial_context: Optional[Dict[str, Any]] = None,
) -> Result:
    """
    스테이지를 순차적으로 실행.

    동작:
    1. 각 스테이지의 어댑터 가져오기
    2. 레지스트리에 에이전트 busy 마킹
    3. 타임아웃과 함께 실행
    4. 성공/실패 기록 (레지스트리)
    5. 컨텍스트 누적 (stage_N_output)
    6. 최종 결과 반환
    """
```

**컨텍스트 누적**
```python
# 각 스테이지 결과가 컨텍스트에 누적됨
context["stage_0_output"] = result.output
context["stage_1_output"] = result.output
# ...
context["insights"] = [...]  # 모든 인사이트 수집
```

### parallel.py - 병렬 파이프라인

**클래스 설명**
```python
class ParallelPipeline:
    """
    병렬 파이프라인 실행기 (Fan-Out/Gather 패턴).

    여러 에이전트를 동시에 실행하고 결과를 집계.
    Microsoft Parallel Fan-Out/Gather 패턴 기반.

    Flow:
              ┌─→ Agent 1 ─┐
    Task ──→  ├─→ Agent 2 ─┼──→ Gather → Combined Result
              └─→ Agent 3 ─┘
    """
```

**Gather 전략**
| 전략 | 설명 |
|------|------|
| `merge` | 모든 출력을 하나의 dict로 병합 (기본값) |
| `list` | 결과를 리스트로 유지 |
| `first_success` | 첫 번째 성공 결과만 반환 |
| `majority` | 과반수 성공 시 병합, 아니면 실패 |

**핵심 메서드**
```python
async def execute(
    self,
    task: Task,
    agents: List[AgentType],
    context: Optional[Dict[str, Any]] = None,
    timeout: int = 300,
) -> Result:
    """
    에이전트들을 병렬 실행.

    동작:
    1. 각 에이전트의 어댑터 가져오기
    2. asyncio.gather()로 동시 실행
    3. 예외 포함하여 결과 수집
    4. gather_strategy에 따라 결과 병합
    """
```

**ParallelFanOut 헬퍼**
```python
class ParallelFanOut:
    """서브태스크 생성 헬퍼"""

    def fan_out(
        self,
        task: Task,
        agents: List[AgentType],
        task_modifier: Optional[Callable] = None,
    ) -> List[Task]:
        """
        하나의 태스크를 여러 서브태스크로 분할.

        각 서브태스크는:
        - 고유 ID
        - parent_task_id로 원본 참조
        - assigned_agent 필드
        """
```

### critic_loop.py - Generator-Critic 루프

**클래스 설명**
```python
class CriticLoopPipeline:
    """
    Generator-Critic 루프 실행기.

    Generator가 출력을 생성하고, Critic이 검토하여
    합격할 때까지 (또는 최대 반복 횟수까지) 반복.

    Google ADK Generator-Critic Loop 패턴 기반.

    Flow:
    ┌─────────────────────────────────────────┐
    │  Generator → Critic → Pass? ──Yes──→ Done
    │      ↑          │
    │      └──No──────┘ (with feedback)
    └─────────────────────────────────────────┘
    """
```

**CriticFeedback 데이터 클래스**
```python
@dataclass
class CriticFeedback:
    passed: bool          # 합격 여부
    score: float          # 점수 (0.0 ~ 1.0)
    issues: List[str]     # 발견된 문제점
    suggestions: List[str] # 개선 제안
    details: Dict[str, Any] # 상세 정보
```

**핵심 메서드**
```python
async def execute(
    self,
    task: Task,
    context: Optional[Dict[str, Any]] = None,
    feedback_parser: Optional[Callable] = None,
) -> Result:
    """
    Generator-Critic 루프 실행.

    동작:
    1. 첫 반복: Generator 실행
    2. 이후 반복: Fixer 실행 (피드백 포함)
    3. Critic 실행하여 피드백 수집
    4. 합격 또는 최대 반복까지 반복
    5. 반복 히스토리 포함하여 결과 반환
    """
```

**Auto-Claude 전용 QA 루프**
```python
async def run_auto_claude_qa_loop(
    task: Task,
    context: Optional[Dict] = None,
    max_iterations: Optional[int] = None,
) -> Result:
    """
    Auto-Claude 전용 QA 루프.

    에이전트 구성:
    - Generator: AUTO_CLAUDE_CODER
    - Critic: AUTO_CLAUDE_QA_REVIEWER
    - Fixer: AUTO_CLAUDE_QA_FIXER

    max_iterations: settings.max_qa_iterations (기본 5)
    """
```

## 실행 흐름 상세

### Sequential Pipeline 흐름
```
1. execute(task, stages) 호출
   │
   └─→ for stage in stages:
         │
         ├─→ registry.get_adapter(agent_type)
         │
         ├─→ registry.mark_busy(agent_type, task_id)
         │
         ├─→ adapter.execute(task, context) [with timeout]
         │
         ├─→ SUCCESS: registry.record_success(agent_type, ms)
         │   FAILED:  registry.record_failure(agent_type)
         │
         └─→ context[f"stage_{i}_output"] = result.output
             context.update(result.output)  # 병합

2. return final_result (all stage_results + accumulated_context)
```

### Critic Loop 흐름
```
1. execute(task, context) 호출
   │
   └─→ while iteration < max_iterations:
         │
         ├─→ iteration == 1?
         │     YES → _run_generator(task, context)
         │     NO  → _run_fixer(task, context_with_feedback)
         │
         ├─→ _run_critic(task, {generated_output, iteration})
         │
         ├─→ parse feedback (score, issues, suggestions)
         │
         ├─→ passed OR score >= pass_threshold?
         │     YES → return SUCCESS
         │     NO  → context["critic_feedback"] = feedback
         │           continue loop

2. max_iterations 도달 → return PARTIAL
```

## 편의 함수

```python
from src.pipeline import (
    # Sequential
    run_sequential,

    # Parallel
    run_parallel,

    # Critic Loop
    run_critic_loop,
    run_auto_claude_qa_loop,  # Auto-Claude 전용
)

# Sequential 실행
result = await run_sequential(task, stages, context)

# Parallel 실행
result = await run_parallel(task, agents, context, gather_strategy="merge")

# Generic Critic Loop
result = await run_critic_loop(
    task,
    generator=AgentType.AUTO_CLAUDE_CODER,
    critic=AgentType.AUTO_CLAUDE_QA_REVIEWER,
    fixer=AgentType.AUTO_CLAUDE_QA_FIXER,
    max_iterations=5,
    context=context,
)

# Auto-Claude QA Loop (단축)
result = await run_auto_claude_qa_loop(task, context)
```

## 파이프라인 조합 패턴

실제 사용에서는 여러 패턴을 조합:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Full Project Pipeline                     │
│                                                                  │
│  [Parallel Research] → [Sequential Spec→Plan→Code] → [QA Loop]  │
│        (AG)                  (Auto-Claude)           (Auto-Claude)│
│                                                                  │
│  ┌───────────┐                                                   │
│  │AG_RESEARCH│─┐     ┌─────────┐   ┌──────┐   ┌──────┐          │
│  ├───────────┤ ├─→   │ PLANNER │ → │CODER │ → │ QA   │          │
│  │AG_ANALYST │─┘     └─────────┘   └──────┘   │ LOOP │          │
│  └───────────┘                                 └──────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## 설정 (config.py)

```python
# Critic Loop 설정
max_qa_iterations: int = 5        # QA 루프 최대 반복
stage_timeout_seconds: int = 300  # 스테이지 타임아웃

# CriticLoopPipeline 기본값
pass_threshold: float = 0.8       # 합격 기준 점수
```

## 설계 패턴 참조

- **Sequential Pipeline Pattern** (Microsoft/Google ADK)
- **Parallel Fan-Out/Gather Pattern** (Microsoft Orchestration)
- **Generator-Critic Loop Pattern** (Google ADK)

## 관련 모듈

- `src/utils/models.py` - Stage, Pipeline, Result 모델
- `src/adapters/` - 14개 에이전트 어댑터
- `src/registry/` - 에이전트 레지스트리 (busy 마킹, 성공/실패 기록)
- `src/coordinator/pipeline_builder.py` - 파이프라인 동적 구성
