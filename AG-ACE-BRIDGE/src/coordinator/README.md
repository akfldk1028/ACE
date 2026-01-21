# Coordinator Module

AG-ACE-BRIDGE의 핵심 오케스트레이션 모듈. 24/7 자율 태스크 처리를 담당.

## 파일 구조

```
src/coordinator/
├── __init__.py          # 모듈 export
├── orchestrator.py      # 24/7 메인 루프 오케스트레이터
├── agent_selector.py    # 지능형 에이전트 선택기
├── pipeline_builder.py  # 동적 파이프라인 빌더
├── task_queue.py        # SQLite 기반 우선순위 큐
└── README.md            # 이 파일
```

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Orchestrator                                 │
│                       (24/7 Main Loop)                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  while running:                                              │   │
│  │    task = queue.dequeue()          ← TaskQueue (SQLite)      │   │
│  │    selection = selector.select()   ← AgentSelector           │   │
│  │    pipeline = builder.build()      ← PipelineBuilder         │   │
│  │    result = execute(pipeline)      → Adapters (14개)         │   │
│  │    handle_result(result)           → queue.complete/fail     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
         │                │                │                │
         ▼                ▼                ▼                ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
   │TaskQueue │    │AgentSel. │    │Pipeline  │    │ Adapters │
   │(SQLite)  │    │(Scoring) │    │Builder   │    │(14 types)│
   └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## 주요 컴포넌트

### orchestrator.py - 24/7 메인 루프

**핵심 클래스**
```python
class Orchestrator:
    """24/7 자율 실행 오케스트레이터"""

    async def start(self):
        """메인 루프 시작 (무한 루프)"""
        await self._initialize_adapters()  # 14개 어댑터 초기화
        await self._main_loop()

    async def _main_loop(self):
        """while self._running: dequeue → build → execute → handle"""

    async def _process_task(self, task: Task) -> Result:
        """단일 태스크 처리: 선택 → 빌드 → 실행"""

    async def _execute_pipeline(self, pipeline: Pipeline) -> Result:
        """파이프라인 실행 (Sequential/Parallel/CriticLoop)"""
```

**어댑터 초기화**
```python
# 14개 에이전트 어댑터 매핑
self._adapters = {
    # Auto-Claude (4)
    AgentType.AUTO_CLAUDE_PLANNER: AutoClaudeAdapter(...),
    AgentType.AUTO_CLAUDE_CODER: AutoClaudeAdapter(...),
    AgentType.AUTO_CLAUDE_QA_REVIEWER: AutoClaudeAdapter(...),
    AgentType.AUTO_CLAUDE_QA_FIXER: AutoClaudeAdapter(...),

    # AG Autogen (5)
    AgentType.AG_RESEARCH: AGAutogenAdapter(...),
    # ...

    # AG Law Domain (5)
    AgentType.AG_CASE_ANALYZER: AGLawDomainAdapter(...),
    # ...
}
```

### task_queue.py - SQLite 우선순위 큐

**테이블 스키마**
```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending',
    input_data TEXT,           -- JSON
    context TEXT,              -- JSON
    result TEXT,               -- JSON
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
)
```

**우선순위 가중치**
```python
PRIORITY_WEIGHTS = {
    Priority.HIGH: 3,
    Priority.MEDIUM: 2,
    Priority.LOW: 1
}
# dequeue 시 (priority_weight, -created_at) 순으로 정렬
```

**핵심 메서드**
```python
class TaskQueue:
    async def enqueue(self, task: Task) -> str:
        """태스크 추가, task_id 반환"""

    async def dequeue(self) -> Optional[Task]:
        """우선순위 높은 순으로 태스크 가져오기"""

    async def complete(self, task_id: str, result: Result):
        """태스크 완료 처리"""

    async def fail(self, task_id: str, error: str) -> bool:
        """실패 처리, retry_count < max_retries면 pending으로 복귀"""

    async def get_stats(self) -> Dict:
        """통계: pending, running, completed, failed 개수"""
```

### agent_selector.py - 지능형 에이전트 선택기

**선택 결과**
```python
@dataclass
class AgentSelection:
    primary: AgentType              # 주 에이전트
    alternatives: List[AgentType]   # 대안 (fallback용)
    parallel_candidates: List[AgentType]  # 병렬 실행 후보
    confidence: float               # 선택 신뢰도 (0.0~1.0)
    pipeline_type: str              # "auto", "full_auto_claude", etc.
```

**선택 알고리즘**
```python
def select(self, task: Task) -> AgentSelection:
    # 1. TaskType으로 후보 필터링
    candidates = registry.get_agents_by_task_type(task.type)

    # 2. 각 후보 점수 계산
    scores = {}
    for agent in candidates:
        score = 0.0
        score += availability_bonus(agent)      # +0.3 if available
        score += success_rate_bonus(agent)      # success_rate * 0.2
        score += requirement_match(agent, task) # 키워드 매칭 점수
        score -= failure_penalty(agent)         # consecutive_failures * 0.1
        scores[agent] = score

    # 3. 최고 점수 에이전트 선택
    primary = max(scores, key=scores.get)

    # 4. 파이프라인 타입 결정
    pipeline_type = determine_pipeline_type(task, primary)

    return AgentSelection(primary, alternatives, [], confidence, pipeline_type)
```

**파이프라인 타입**
| Type | 설명 | 사용 케이스 |
|------|------|-------------|
| `auto` | 자동 결정 | 기본값 |
| `full_auto_claude` | Auto-Claude 4단계 | CODE, PLAN 태스크 |
| `research_first` | 리서치 → 코딩 | 정보 수집 필요 시 |
| `legal` | 법률 도메인 특화 | 법률 관련 태스크 |

### pipeline_builder.py - 동적 파이프라인 빌더

**스테이지 타입**
```python
class StageType(Enum):
    SEQUENTIAL = "sequential"   # 순차 실행
    PARALLEL = "parallel"       # 병렬 실행 (Fan-Out)
    CRITIC_LOOP = "critic_loop" # QA 반복 (최대 N회)
```

**사전 정의 템플릿**
```python
TEMPLATES = {
    "auto_claude_full": [
        Stage(AgentType.AUTO_CLAUDE_PLANNER, StageType.SEQUENTIAL),
        Stage(AgentType.AUTO_CLAUDE_CODER, StageType.SEQUENTIAL),
        Stage(AgentType.AUTO_CLAUDE_QA_REVIEWER, StageType.CRITIC_LOOP, max_iterations=5),
    ],

    "research": [
        Stage(AgentType.AG_RESEARCH, StageType.SEQUENTIAL),
        Stage(AgentType.AG_ANALYST, StageType.SEQUENTIAL),
    ],

    "legal_validation": [
        Stage(AgentType.AG_LEGAL_RESEARCHER, StageType.SEQUENTIAL),
        Stage(AgentType.AG_CASE_ANALYZER, StageType.PARALLEL),
        Stage(AgentType.AG_RISK_ASSESSOR, StageType.PARALLEL),
        Stage(AgentType.AG_COMPLIANCE_CHECKER, StageType.SEQUENTIAL),
    ],

    "qa_loop": [
        Stage(AgentType.AUTO_CLAUDE_QA_REVIEWER, StageType.SEQUENTIAL),
        Stage(AgentType.AUTO_CLAUDE_QA_FIXER, StageType.CRITIC_LOOP, max_iterations=3),
    ],
}
```

**자동 빌드 로직**
```python
def build(self, task: Task, selection: AgentSelection) -> Pipeline:
    # 1. 템플릿 사용 가능하면 템플릿 사용
    if selection.pipeline_type in TEMPLATES:
        stages = TEMPLATES[selection.pipeline_type]

    # 2. 아니면 TaskType 기반 자동 생성
    else:
        stages = self._auto_build_stages(task, selection)

    return Pipeline(task_id=task.id, stages=stages)
```

## 실행 흐름 상세

```
1. Orchestrator.start()
   │
   ├─→ _initialize_adapters()
   │     └─→ 14개 어댑터 생성 및 초기화
   │
   └─→ _main_loop()
         │
         ├─→ queue.dequeue()
         │     └─→ SQLite에서 우선순위 높은 태스크 가져오기
         │
         ├─→ _process_task(task)
         │     │
         │     ├─→ selector.select(task)
         │     │     └─→ 점수 기반 에이전트 선택
         │     │
         │     ├─→ builder.build(task, selection)
         │     │     └─→ 파이프라인 구성
         │     │
         │     └─→ _execute_pipeline(pipeline)
         │           │
         │           ├─→ SEQUENTIAL: 순차 실행
         │           ├─→ PARALLEL: asyncio.gather()
         │           └─→ CRITIC_LOOP: while not approved
         │
         └─→ _handle_result(result)
               │
               ├─→ SUCCESS: queue.complete()
               ├─→ FAILED: queue.fail() → 재시도 or 실패
               └─→ NEEDS_RETRY: 자동 재큐
```

## 사용 예시

```python
from src.coordinator import Orchestrator, TaskQueue, AgentSelector, PipelineBuilder
from src.utils import Task, TaskType, Priority

# 오케스트레이터 시작 (24/7)
orchestrator = Orchestrator()
await orchestrator.start()  # 무한 루프

# 또는 개별 컴포넌트 사용
queue = TaskQueue()
await queue.initialize()

# 태스크 추가
task = Task(
    type=TaskType.CODE,
    description="로그인 기능 구현",
    priority=Priority.HIGH
)
task_id = await queue.enqueue(task)

# 에이전트 선택
selector = AgentSelector()
selection = selector.select(task)
# → AgentSelection(primary=AUTO_CLAUDE_CODER, confidence=0.85, ...)

# 파이프라인 빌드
builder = PipelineBuilder()
pipeline = builder.build(task, selection)
# → Pipeline(stages=[Planner, Coder, QA_Reviewer])

# 통계 조회
stats = await queue.get_stats()
# → {"pending": 5, "running": 1, "completed": 100, "failed": 2}
```

## 설정 (config.py)

```python
# Orchestrator 설정
orchestrator_poll_interval: float = 1.0  # 큐 폴링 간격 (초)
orchestrator_batch_size: int = 1         # 배치 크기

# TaskQueue 설정
queue_db_path: str = "./data/tasks.db"   # SQLite DB 경로
queue_max_retries: int = 3               # 최대 재시도 횟수

# Pipeline 설정
max_qa_iterations: int = 5               # QA 크리틱 루프 최대 반복
stage_timeout_seconds: int = 300         # 스테이지 타임아웃
```

## 관련 모듈

- `src/adapters/` - 14개 에이전트 어댑터
- `src/registry/` - 에이전트 레지스트리 및 능력 정의
- `src/pipeline/` - 파이프라인 실행 엔진
- `src/utils/models.py` - Task, Result, Pipeline 모델
