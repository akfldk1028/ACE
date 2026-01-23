# CLAUDE.md - AI Agent Context File

AG-ACE-BRIDGE 프로젝트의 AI 에이전트용 컨텍스트 파일.

---

## 필수 규칙 (MUST DO)

> **코드 변경 시 반드시 문서도 동기화!**

### 1. 문서 동기화
- 코드 변경 → 관련 README 업데이트
- 새 기능 추가 → 해당 모듈 README에 반영
- API 변경 → CLAUDE.md 업데이트

### 2. README 필수
- **모든 폴더에 README.md 필수**
- 새 폴더 생성 시 README.md 함께 생성
- 내용: 개요, 파일 설명, 사용법, 예제

### 3. Documentation Index 유지
- 메인 `README.md`에 Documentation Index 섹션 유지
- 새 README 추가 시 인덱스에 링크 추가

```markdown
## Documentation Index
| 모듈 | 설명 | README |
|------|------|--------|
| new_module | 설명 | [링크](src/new_module/README.md) |
```

---

## 개발 환경

### Python 버전
- **Python 3.13+** 권장
- 현재: Python 3.13.7

### 가상환경 설정

```bash
# 1. 가상환경 생성
python -m venv .venv

# 2. 활성화
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Windows (CMD)
.\.venv\Scripts\activate.bat

# Linux/macOS
source .venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. Submodule 초기화
git submodule update --init --recursive
```

### 환경 변수 (.env)

```bash
cp .env.example .env
# .env 파일 편집
```

주요 설정:
| 변수 | 설명 | 기본값 |
|------|------|--------|
| `BRIDGE_PORT` | 브릿지 서버 포트 | 8080 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | - |
| `NEO4J_URI` | Neo4j 연결 URI | bolt://localhost:7687 |
| `MAX_QA_ITERATIONS` | QA 루프 최대 반복 | 5 |

### Claude Code OAuth

```bash
# Claude Code 로그인 (필수)
claude
/login
# 브라우저에서 OAuth 인증
```

---

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
│   │   ├── ag_a2a_adapter.py   # A2A Protocol (Google ADK)
│   │   └── ag_law_domain.py    # HTTP/REST
│   │
│   ├── registry/          # 에이전트 레지스트리
│   │   ├── agent_registry.py   # 런타임 상태
│   │   ├── capabilities.py     # 14개 능력 정의
│   │   └── pattern_registry.py # 패턴 등록/관리 (★ NEW)
│   │
│   ├── watcher/           # 패턴 감시 (★ NEW)
│   │   ├── __init__.py
│   │   └── pattern_watcher.py  # AutoGen Studio 출력 감시
│   │
│   ├── scheduler/         # 스케줄러 (★ NEW)
│   │   ├── __init__.py
│   │   └── trigger.py          # Cron/이벤트 트리거
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
│   ├── server/            # 웹 서버 (대시보드)
│   │   ├── __init__.py         # 모듈 export
│   │   ├── dashboard.py        # FastAPI + WebSocket
│   │   └── pattern_routes.py   # 패턴 REST API (★ NEW)
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
├── patterns/              # 패턴 폴더 (★ NEW - AutoGen Studio 연동)
│   └── *.json/yaml            # 워크플로우/에이전트 패턴
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

## UI 시작 가이드 (★ 중요!)

### Triple UI 아키텍처

| UI | 설명 | URL/위치 |
|---|---|---|
| **Auto-Claude UI** | Electron 데스크톱 앱 | 데스크톱 앱 |
| **AutoGen Studio** | 웹 기반 에이전트 빌더 | http://localhost:8081 |
| **AG-ACE Dashboard** | 브릿지 모니터링 대시보드 | http://localhost:8080 |

### 1. Auto-Claude UI 시작 (Electron)

```powershell
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
```

- Electron 데스크톱 앱이 자동으로 열림
- Dev 서버: http://localhost:5173 (내부용)

### 2. AutoGen Studio 시작

```powershell
# 방법 1: Python에서 직접 실행 (권장)
python -c "from autogenstudio.cli import app; app()" ui --port 8081

# 방법 2: autogenstudio 명령어가 PATH에 있는 경우
autogenstudio ui --port 8081
```

- 웹 브라우저에서 http://localhost:8081 접속

### 3. A2A 에이전트 서버 시작 (AG)

```powershell
cd D:\Data\25_ACE\AG\autogen_a2a_kit
python run_all_agents.py --subset
```

| Agent | Port | 설명 |
|-------|------|------|
| poetry_agent | 8003 | 시/문학 |
| philosophy_agent | 8004 | 철학 |
| history_agent | 8005 | 역사 |
| calculator_agent | 8006 | 계산 |
| gui_test_agent | 8120 | GUI 자동화 |

### 4. AG-ACE-BRIDGE Dashboard 시작

```powershell
cd D:\Data\25_ACE\AG-ACE-BRIDGE
python main.py --dashboard
```

- 웹 브라우저에서 http://localhost:8080 접속

### 5. SharedMemory 서버 시작

```powershell
cd D:\Data\25_ACE\AG\autogen_a2a_kit\AG-cli
python shared_memory.py
```

- REST API: http://localhost:8101

### 전체 시작 순서 (권장)

```
1. A2A 에이전트 서버 (ports 8003-8006, 8120)
2. SharedMemory 서버 (port 8101)
3. AG-ACE Dashboard (port 8080)
4. AutoGen Studio (port 8081)
5. Auto-Claude UI (Electron)
```

---

## Pattern Automation (★ AutoGen Studio → 24/7 자동 실행)

AutoGen Studio에서 설계한 패턴이 자동으로 24/7 실행되는 시스템입니다.

### 아키텍처

```
[AutoGen Studio]
      │
      │ (1) 패턴 저장 (JSON/YAML)
      ▼
[patterns/ 폴더] ─────────────────────────────────┐
      │                                           │
      │ (2) PatternWatcher 감지                   │
      ▼                                           │
[PatternRegistry]                                 │
      │                                           │
      │ (3) SharedMemory에 등록                   │
      ▼                                           │
[SharedMemory:8101]                               │
      │                                           │
      ├─→ (4a) ScheduleTrigger (Cron/이벤트)      │
      │                                           │
      ├─→ (4b) Auto-Claude UI 알림               │
      ▼                                           │
[Orchestrator 실행]                               │
      │                                           │
      │ (5) A2A 에이전트 호출                     │
      ▼                                           │
[실행 결과] ──────────────────────────────────────┘
```

### 핵심 컴포넌트

| 컴포넌트 | 위치 | 역할 |
|---------|------|------|
| PatternWatcher | `src/watcher/` | AutoGen Studio 출력 폴더 감시 |
| PatternRegistry | `src/registry/` | 패턴 등록, 버전 관리, SharedMemory 동기화 |
| ScheduleTrigger | `src/scheduler/` | Cron/이벤트 기반 자동 실행 |
| Pattern REST API | `src/server/pattern_routes.py` | HTTP 관리 인터페이스 |

### 감시 폴더

```
./patterns/                      # 로컬 패턴 폴더
~/.autogenstudio/patterns/       # AutoGen Studio 패턴
~/.autogenstudio/workflows/      # AutoGen Studio 워크플로우
```

### Pattern REST API

```bash
# 패턴 목록
GET /patterns/

# 패턴 상세
GET /patterns/{pattern_id}

# 패턴 등록 (수동)
POST /patterns/
{
  "name": "my_workflow",
  "pattern_type": "workflow",
  "data": { "nodes": [...] }
}

# 패턴 스케줄 설정
POST /patterns/{pattern_id}/schedule
{
  "cron": "0 9 * * *"  # 매일 오전 9시
}

# 패턴 즉시 실행
POST /patterns/{pattern_id}/trigger

# 이벤트 트리거 추가
POST /patterns/{pattern_id}/event-trigger
{
  "event_type": "task_completed"
}
```

### 패턴 파일 형식

```json
{
  "name": "calculator_workflow",
  "description": "Calculator development workflow",
  "type": "workflow",
  "tags": ["calculator", "demo"],
  "nodes": [
    {
      "id": "planner",
      "agent": "AUTO_CLAUDE_PLANNER",
      "task": "Create development plan"
    },
    {
      "id": "coder",
      "agent": "AUTO_CLAUDE_CODER",
      "depends_on": ["planner"]
    }
  ],
  "config": {
    "max_iterations": 3,
    "enable_shared_memory": true
  }
}
```

### 사용 흐름

1. **AutoGen Studio에서 설계**
   - 워크플로우/에이전트 패턴 생성
   - JSON/YAML로 저장

2. **자동 감지**
   - PatternWatcher가 파일 변경 감지
   - PatternRegistry에 자동 등록
   - SharedMemory에 메타데이터 동기화

3. **스케줄 설정** (선택)
   - REST API로 Cron 스케줄 설정
   - 또는 이벤트 트리거 설정

4. **자동 실행**
   - ScheduleTrigger가 정해진 시간에 실행
   - Orchestrator를 통해 에이전트 호출
   - 결과 SharedMemory에 저장

5. **모니터링**
   - Auto-Claude UI에서 실행 상태 확인
   - AG-ACE Dashboard에서 통계 확인

---

## 빠른 시작 (백엔드 전용)

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
- [x] Phase 2: Adapters (Auto-Claude SDK OAuth, AG HTTP, AG A2A Protocol)
- [x] Phase 3: Pipeline (Sequential, Parallel, Critic Loop)
- [x] Phase 4: Project System (Spec, Watcher, CLI)
- [x] Phase 5: Memory Sync (SharedMemoryClient → AG-CLI 8101 연동)
- [x] Phase 6: Web Dashboard (FastAPI + WebSocket 실시간 모니터링)
- [x] Phase 7: AG Integration (A2A Protocol 연동, 19개 에이전트 조율)
- [ ] Phase 8: E2E Testing & Polish
