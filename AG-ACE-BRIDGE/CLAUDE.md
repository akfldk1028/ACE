# CLAUDE.md - AI Agent Context File

AG-ACE-BRIDGE 프로젝트의 AI 에이전트용 컨텍스트 파일.

## 프로젝트 개요

**AG-ACE-BRIDGE**는 24/7 AI Project Factory로, Auto-Claude와 AG 멀티에이전트 시스템을 통합하는 브릿지입니다.

```
핵심 목표: 14개 AI 에이전트를 조율하여 24/7 자율 프로젝트 실행
```

## 핵심 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                       AG-ACE-BRIDGE                              │
│                    (4-Layer Architecture)                        │
├─────────────────────────────────────────────────────────────────┤
│ Layer 1: Coordinator (24/7 Main Loop)                           │
│   TaskQueue → AgentSelector → PipelineBuilder → Execute         │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: Pipeline (Execution Patterns)                          │
│   Sequential │ Parallel (Fan-Out) │ CriticLoop (QA)             │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: Adapters (Agent Connections)                           │
│   AutoClaudeAdapter (OAuth) │ AGAutogenAdapter │ AGLawAdapter   │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Registry + Memory                                      │
│   AgentRegistry (14 agents) │ SharedMemoryClient (AG-CLI 연동)   │
└─────────────────────────────────────────────────────────────────┘
```

## 14개 에이전트 매핑

### Auto-Claude (4개) - Claude Agent SDK + OAuth
| AgentType | 역할 | 시스템 프롬프트 키 |
|-----------|------|-------------------|
| `AUTO_CLAUDE_PLANNER` | 프로젝트 계획, 태스크 분해 | planner |
| `AUTO_CLAUDE_CODER` | 코드 작성, 구현 | coder |
| `AUTO_CLAUDE_QA_REVIEWER` | 코드 리뷰, 품질 검토 | qa_reviewer |
| `AUTO_CLAUDE_QA_FIXER` | 이슈 수정, 리팩토링 | qa_fixer |

### AG Autogen (5개) - HTTP/A2A Protocol
| AgentType | 역할 | 엔드포인트 |
|-----------|------|----------|
| `AG_RESEARCH` | 정보 수집, 웹 검색 | /agents/research |
| `AG_ANALYST` | 데이터 분석, 패턴 탐지 | /agents/analyst |
| `AG_WRITER` | 문서 작성, 콘텐츠 생성 | /agents/writer |
| `AG_REVIEWER` | 리뷰 피드백, 품질 평가 | /agents/reviewer |
| `AG_COORDINATOR` | 작업 조율, 라우팅 | /agents/coordinator |

### AG Law Domain (5개) - HTTP/FastAPI
| AgentType | 역할 | 엔드포인트 |
|-----------|------|----------|
| `AG_CASE_ANALYZER` | 판례 분석, 법적 선례 | /law/case-analyzer |
| `AG_LEGAL_RESEARCHER` | 법률 조사, 규정 검색 | /law/researcher |
| `AG_RISK_ASSESSOR` | 리스크 평가, 책임 분석 | /law/risk-assessor |
| `AG_COMPLIANCE_CHECKER` | 컴플라이언스 점검, 감사 | /law/compliance |
| `AG_DOCUMENT_DRAFTER` | 법률 문서 초안 작성 | /law/drafter |

## 핵심 모델 (src/utils/models.py)

### Task
```python
class Task(BaseModel):
    id: str                      # UUID
    type: TaskType               # CODE, PLAN, REVIEW, RESEARCH, LEGAL_*
    description: str             # 태스크 설명
    priority: Priority           # HIGH, MEDIUM, LOW
    status: TaskStatus           # PENDING, RUNNING, COMPLETED, FAILED
    input_data: Dict[str, Any]   # 입력 데이터
    context: Dict[str, Any]      # 컨텍스트 (누적)
```

### Result
```python
class Result(BaseModel):
    success: bool                # 성공 여부
    output: Dict[str, Any]       # 출력 데이터
    error: Optional[str]         # 에러 메시지
    execution_time_ms: int       # 실행 시간
    insights: List[str]          # 인사이트 (메모리 동기화용)
```

### Stage & Pipeline
```python
class Stage(BaseModel):
    agent_type: AgentType        # 실행할 에이전트
    stage_type: StageType        # SEQUENTIAL, PARALLEL, CRITIC_LOOP
    max_iterations: int = 1      # CRITIC_LOOP용

class Pipeline(BaseModel):
    task_id: str
    stages: List[Stage]
    current_stage: int = 0
```

## 파이프라인 패턴

### 1. Sequential (순차 실행)
```python
# 각 스테이지 출력이 다음 스테이지 컨텍스트로 누적
await run_sequential(task, stages=[
    Stage(AUTO_CLAUDE_PLANNER, SEQUENTIAL),
    Stage(AUTO_CLAUDE_CODER, SEQUENTIAL),
])
# context["stage_0_output"], context["stage_1_output"] 누적
```

### 2. Parallel (병렬 Fan-Out/Gather)
```python
# 여러 에이전트 동시 실행 후 결과 집계
await run_parallel(task, agents=[AG_RESEARCH, AG_ANALYST],
                   gather_strategy="merge")  # merge, list, first_success, majority
```

### 3. CriticLoop (Generator-Critic 반복)
```python
# Generator → Critic → Pass? → Done (또는 Fixer로 재시도)
await run_auto_claude_qa_loop(task, max_iterations=5)
# CriticFeedback: passed, score (0.0~1.0), issues, suggestions
```

## 어댑터 인터페이스

모든 어댑터는 `BaseAdapter` 상속:
```python
class BaseAdapter(ABC):
    @abstractmethod
    async def execute(self, task: Task, context: Dict) -> Result:
        """태스크 실행"""

    @abstractmethod
    async def health_check(self) -> bool:
        """연결 상태 확인"""
```

### Auto-Claude 어댑터 특징
- Claude Agent SDK + OAuth 2.0 (PKCE)
- 토큰 자동 갱신 (expire 5분 전)
- 시스템 프롬프트 프리셋 (planner, coder, qa_reviewer, qa_fixer)

### AG 어댑터 특징
- HTTP/REST 또는 A2A Protocol
- 비동기 aiohttp 클라이언트
- 재시도 로직 (최대 3회)

## 에이전트 선택 알고리즘 (AgentSelector)

```python
score = 0.0
score += 0.3 if available else 0.0           # 가용성 보너스
score += success_rate * 0.2                   # 성공률 보너스
score += keyword_match_score                   # 태스크 키워드 매칭
score -= consecutive_failures * 0.1            # 연속 실패 패널티
```

## 프로젝트 제출 흐름

```
1. YAML 파일을 projects/queue/에 드랍
2. ProjectWatcher가 감지 (watchdog)
3. ProjectSpec 로드 및 검증
4. 마스터 PLANNING 태스크 생성
5. TaskQueue에 enqueue
6. Orchestrator가 dequeue하여 실행
```

### ProjectSpec 필수 필드
```yaml
name: "프로젝트 이름"
description: "프로젝트 설명"
goals:
  - "목표 1"
  - "목표 2"
agents:
  use_auto_claude: true
  use_ag_autogen: true
  use_ag_law: false
pipeline:
  pattern: "auto"  # auto, sequential, parallel, critic_loop
  max_iterations: 5
priority: "medium"  # high, medium, low
auto_start: true
```

## SharedMemory 연동 (★ Auto-Claude ↔ AG 연결점)

AG-CLI의 SharedMemory(8101)를 통해 Auto-Claude와 AG 에이전트가 상태를 공유합니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                     AG-ACE-BRIDGE                                │
│  ┌───────────────┐              ┌───────────────┐               │
│  │ Auto-Claude   │              │  AG Agents    │               │
│  │   Adapter     │              │   Adapter     │               │
│  └───────┬───────┘              └───────┬───────┘               │
│          │                              │                       │
│          └──────────────┬───────────────┘                       │
│                         ▼                                        │
│              ┌─────────────────────┐                            │
│              │ SharedMemoryClient  │                            │
│              └──────────┬──────────┘                            │
└─────────────────────────┼───────────────────────────────────────┘
                          │ HTTP (8101)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AG-CLI                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │            SharedMemoryServer (8101)                     │    │
│  │  - Decisions (상태 저장)                                 │    │
│  │  - Events (이벤트 발행/구독)                             │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 사용법

```python
from src.memory import SharedMemoryClient, store, get, publish_event

# 상태 저장/조회
await store("api_spec", {"endpoints": ["/users"]})
data = await get("api_spec")

# 이벤트 발행
await publish_event("task_completed", {"task_id": "abc"})

# 어댑터에서 자동 연동
adapter = MyAdapter(enable_shared_memory=True)
```

### 필수 서버

```powershell
# AG-CLI SharedMemory 서버 시작
cd D:\Data\22_AG\autogen_a2a_kit\AG-cli
python mcp/shared_memory.py
# → http://localhost:8101
```

## 디렉토리 구조

```
AG-ACE-BRIDGE/
├── src/
│   ├── coordinator/       # Layer 1: 24/7 오케스트레이션
│   │   ├── orchestrator.py     # 메인 루프
│   │   ├── task_queue.py       # SQLite 우선순위 큐
│   │   ├── agent_selector.py   # 점수 기반 선택
│   │   └── pipeline_builder.py # 동적 파이프라인
│   │
│   ├── pipeline/          # Layer 2: 실행 패턴
│   │   ├── sequential.py       # 순차 실행
│   │   ├── parallel.py         # 병렬 Fan-Out/Gather
│   │   └── critic_loop.py      # Generator-Critic
│   │
│   ├── adapters/          # Layer 3: 에이전트 연결
│   │   ├── base.py             # 추상 베이스
│   │   ├── auto_claude.py      # Claude SDK OAuth
│   │   ├── ag_autogen.py       # HTTP/A2A
│   │   └── ag_law_domain.py    # HTTP/REST
│   │
│   ├── registry/          # 에이전트 레지스트리
│   │   ├── agent_registry.py   # 런타임 상태
│   │   └── capabilities.py     # 14개 능력 정의
│   │
│   ├── memory/            # Layer 4: SharedMemory 연동
│   │   ├── __init__.py            # 모듈 export
│   │   └── shared_memory_client.py # AG-CLI SharedMemory 클라이언트
│   │
│   ├── project/           # 프로젝트 제출
│   │   ├── spec.py             # ProjectSpec 모델
│   │   ├── watcher.py          # 폴더 감시
│   │   └── cli.py              # CLI 명령어
│   │
│   └── utils/             # 유틸리티
│       ├── config.py           # 환경 설정
│       ├── models.py           # 공통 모델
│       └── logger.py           # 구조화 로깅
│
├── projects/              # 프로젝트 드랍 폴더
│   ├── queue/                  # 새 프로젝트
│   ├── completed/              # 완료
│   └── failed/                 # 실패
│
└── data/
    └── tasks.db               # SQLite 태스크 큐
```

## 설정 파일 (.env)

```bash
# Auto-Claude OAuth
AUTO_CLAUDE_CLIENT_ID=your_client_id
AUTO_CLAUDE_CLIENT_SECRET=your_client_secret

# AG Autogen
AG_AUTOGEN_BASE_URL=http://localhost:8000
AG_AUTOGEN_API_KEY=your_api_key

# AG Law Domain
AG_LAW_BASE_URL=http://localhost:8001

# SharedMemory (AG-CLI 연동)
SHARED_MEMORY_URL=http://localhost:8101

# Neo4j (옵션 - 추가 메모리 동기화)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# 실행 설정
ORCHESTRATOR_POLL_INTERVAL=1.0
MAX_QA_ITERATIONS=5
STAGE_TIMEOUT_SECONDS=300
```

## 빠른 시작

```bash
# 1. 설치
pip install -r requirements.txt

# 2. 설정
cp .env.example .env
# .env 편집

# 3. SDK 연동 확인
python tests/test_auto_claude_sdk.py

# 4. 오케스트레이터 시작 (24/7)
python -m src.coordinator.orchestrator

# 5. 프로젝트 제출
python -m src.project.cli submit my-project.yaml
```

## 관련 프로젝트

| 프로젝트 | 설명 | 경로 |
|---------|------|------|
| Auto-Claude | 24/7 자율 코딩 엔진 | `D:/Data/25_ACE/Auto-Claude` |
| AG | 멀티에이전트 프레임워크 | `D:/Data/25_ACE/AG` |
| AG-ACE-BRIDGE | 통합 브릿지 (이 프로젝트) | `D:/Data/25_ACE/AG-ACE-BRIDGE` |

## 개발 상태

- [x] Phase 1: Foundation (폴더 구조, 모델, 설정)
- [x] Phase 2: Adapters (Auto-Claude SDK OAuth, AG HTTP)
- [x] Phase 3: Pipeline (Sequential, Parallel, Critic Loop)
- [x] Phase 4: Project System (Spec, Watcher, CLI)
- [x] Phase 5: Memory Sync (SharedMemoryClient → AG-CLI 8101 연동)
- [ ] Phase 6: E2E Testing & Polish
