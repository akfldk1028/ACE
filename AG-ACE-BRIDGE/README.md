# AG-ACE-BRIDGE

24/7 AI Project Factory - Auto-Claude와 AG 멀티에이전트 통합 브릿지

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       AG-ACE-BRIDGE                              │
│                  24/7 AI PROJECT FACTORY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   AUTO-CLAUDE (4)   AG A2A (5)   AG AUTOGEN (5)   AG LAW (5)   │
│   ├── Planner       ├── Poetry   ├── Research     ├── Case Analyzer
│   ├── Coder         ├── Phil     ├── Analyst      ├── Legal Researcher
│   ├── QA Reviewer   ├── History  ├── Writer       ├── Risk Assessor
│   └── QA Fixer      ├── Calc     ├── Reviewer     ├── Compliance Checker
│                     └── GUI      └── Coordinator  └── Document Drafter
│                                                                 │
│   Web Dashboard: http://localhost:8080                          │
│   Hybrid Orchestration: Coordinator + Pipeline + Critic Loop    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Concept: AutoGen Studio에서 설계 → Auto-Claude에서 24/7 실행

```
┌────────────────────┐       ┌────────────────────┐       ┌────────────────────┐
│  AutoGen Studio    │       │   AG-ACE-BRIDGE    │       │    Auto-Claude     │
│  (Design Tool)     │──────▶│  (Execution Bridge)│──────▶│  (24/7 Engine)     │
│                    │       │                    │       │                    │
│  - Workflow Design │       │  - Parse Nodes     │       │  - PLANNER         │
│  - Node + Deps     │       │  - Route to Adapter│       │  - CODER           │
│  - JSON/YAML Save  │       │  - Dependency Order│       │  - QA_REVIEWER     │
└────────────────────┘       └────────────────────┘       │  - QA_FIXER        │
                                                          └────────────────────┘
```

### 실행 흐름

1. **AutoGen Studio에서 설계**: 워크플로우(nodes + dependencies) 생성 → JSON/YAML로 저장
2. **AG-ACE-BRIDGE가 파싱**: PatternRegistry에 등록, 노드별로 어댑터에 라우팅
3. **Auto-Claude에서 24/7 실행**: 각 노드의 agent_type에 따라 순차/병렬 실행

### 예시: 계산기 앱 개발 워크플로우

```json
{
  "name": "calculator_app_workflow",
  "nodes": [
    {"id": "planner", "agent": "AUTO_CLAUDE_PLANNER", "task": "개발 계획"},
    {"id": "coder", "agent": "AUTO_CLAUDE_CODER", "depends_on": ["planner"]},
    {"id": "qa_reviewer", "agent": "AUTO_CLAUDE_QA_REVIEWER", "depends_on": ["coder"]},
    {"id": "qa_fixer", "agent": "AUTO_CLAUDE_QA_FIXER", "depends_on": ["qa_reviewer"]}
  ]
}
```

**실행 순서**: PLANNER → CODER → QA_REVIEWER → QA_FIXER (의존성 그래프 기반)

### 테스트 실행

```bash
# 워크플로우 실행 테스트
python tests/test_workflow_execution.py

# 결과:
# [OK] 의존성 순서 정확!
# 1. AUTO_CLAUDE_PLANNER
# 2. AUTO_CLAUDE_CODER
# 3. AUTO_CLAUDE_QA_REVIEWER
# 4. AUTO_CLAUDE_QA_FIXER
```

---

## Features

- **24/7 자율 운영**: Auto-Claude의 무한 루프 활용
- **19개 에이전트 조율**: Auto-Claude 4 + AG A2A 5 + AG Autogen 5 + AG Law Domain 5
- **Web Dashboard**: 실시간 모니터링 UI (http://localhost:8080)
- **AG A2A Protocol 연동**: Google ADK 기반 A2A 에이전트 직접 연결 (8003-8006)
- **SharedMemory 연동**: AG-CLI SharedMemory(8101)를 통한 상태 공유
- **Hybrid Orchestration**: 5가지 패턴 조합
  - Coordinator/Dispatcher (24/7 Main Loop)
  - Sequential Pipeline (Google ADK)
  - Parallel Fan-Out/Gather (Microsoft)
  - Generator-Critic Loop (Google ADK)
  - Dynamic Agent Selection (Score-based)
- **프로젝트 자동 실행**: YAML 드랍 → 자동 태스크 분해 → 실행
- **동적 파이프라인**: 작업 유형에 따라 자동 구성

## Quick Start

### 1. Clone & Initialize Submodules

```bash
git clone <repository-url> AG-ACE-BRIDGE
cd AG-ACE-BRIDGE

# Initialize Auto-Claude submodule (required for prompts)
git submodule update --init --recursive
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your settings
```

---

## UI 시작 가이드 (★ Triple UI Architecture)

### 포트 요약
| 서비스 | URL | 용도 |
|--------|-----|------|
| **Auto-Claude UI** | Electron 앱 | 자율 코딩 데스크톱 |
| **AutoGen Studio** | http://localhost:8081 | 에이전트 빌더 |
| **AG-ACE Dashboard** | http://localhost:8080 | 모니터링 |
| SharedMemory | http://localhost:8101 | 상태 공유 |
| A2A Agents | http://localhost:8003-8006 | 외부 에이전트 |

### Step 1: A2A 에이전트 시작

```powershell
cd D:\Data\25_ACE\AG\autogen_a2a_kit
python run_all_agents.py --subset
```

### Step 2: SharedMemory 시작

```powershell
cd D:\Data\25_ACE\AG\autogen_a2a_kit\AG-cli
python shared_memory.py
```

### Step 3: AG-ACE Dashboard 시작

```powershell
cd D:\Data\25_ACE\AG-ACE-BRIDGE
python main.py --dashboard
```

### Step 4: AutoGen Studio 시작

```powershell
# autogenstudio 명령이 없으면 Python으로 실행
python -c "from autogenstudio.cli import app; app()" ui --port 8081
```

### Step 5: Auto-Claude UI 시작

```powershell
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
```

### Step 6: AutoGen ↔ SharedMemory 동기화 (★ 핵심!)

```powershell
cd D:\Data\25_ACE\AG-ACE-BRIDGE
python -u run_autogen_sync_simple.py
```

**아키텍처 (★ IPC 중앙화):**
```
AutoGen Studio (8081)
       │
       │ Main Process에서만 호출! (CORS 해결)
       ▼
┌─────────────────────────────────────────────────────┐
│ Main Process (a2a-handlers.ts)                       │
│  ├── getAutogenLatest() → 8081 → 8101 폴백           │
│  └── getAutogenRunsDetailed() → 8081 직접            │
└─────────────────────────────────────────────────────┘
       │
       │ IPC (electronAPI) - 2초 폴링
       ▼
┌─────────────────────────────────────────────────────┐
│ Renderer (React UI)                                  │
│  ├── AutogenStatusBadge (사이드바)                   │
│  ├── KanbanBoard (Kanban 카드)                       │
│  ├── AutogenResultsWidget (플로팅 위젯)              │
│  └── ★ AutogenCollabPanel (Agent Terminals 탭)      │
│       → 터미널 없으면 풀스크린 협업 뷰!              │
└─────────────────────────────────────────────────────┘
```

**Agent Terminals 탭:**
- 터미널 없을 때 → AutoGen 대화가 풀스크린으로 실시간 스트리밍
- 터미널 있을 때 → "AutoGen" 버튼으로 사이드바 토글
- 2초마다 자동 폴링 (바로바로!)

**저장되는 키 (폴백 모드):**
- `autogen_session_{id}` - 각 세션별 결과
- `autogen_latest` - 가장 최근 결과

---

## Backend Quick Start (CLI 전용)

```bash
# SDK 연동 확인
python tests/test_auto_claude_sdk.py

# 24/7 오케스트레이터 직접 시작
python -m src.coordinator.orchestrator

# 프로젝트 watcher 시작
python -m src.project.watcher

# CLI로 프로젝트 제출
python -m src.project.cli submit my-project.yaml
```

## Architecture

4-Layer Hybrid Orchestration:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Coordinator                                             │
│   TaskQueue (SQLite) → AgentSelector → PipelineBuilder          │
│   24/7 Main Loop: dequeue → select → build → execute → handle   │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: Pipeline                                                │
│   Sequential │ Parallel (Fan-Out/Gather) │ CriticLoop (QA)      │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: Adapters                                                │
│   AutoClaudeAdapter (OAuth SDK) │ AGAutogenAdapter (HTTP/A2A)   │
│                                 │ AGLawDomainAdapter (HTTP/REST)│
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Registry + Memory                                       │
│   AgentRegistry (14 agents) │ MemorySync (Graphiti ↔ Neo4j)     │
└─────────────────────────────────────────────────────────────────┘
```

## 14 Agents

| Category | Agent | Role |
|----------|-------|------|
| **Auto-Claude** | Planner | 프로젝트 계획, 태스크 분해 |
| | Coder | 코드 작성, 구현 |
| | QA Reviewer | 코드 리뷰, 품질 검토 |
| | QA Fixer | 이슈 수정, 리팩토링 |
| **AG Autogen** | Research | 정보 수집, 웹 검색 |
| | Analyst | 데이터 분석, 패턴 탐지 |
| | Writer | 문서 작성, 콘텐츠 생성 |
| | Reviewer | 리뷰 피드백, 품질 평가 |
| | Coordinator | 작업 조율, 라우팅 |
| **AG Law Domain** | Case Analyzer | 판례 분석, 법적 선례 |
| | Legal Researcher | 법률 조사, 규정 검색 |
| | Risk Assessor | 리스크 평가, 책임 분석 |
| | Compliance Checker | 컴플라이언스 점검, 감사 |
| | Document Drafter | 법률 문서 초안 작성 |

## Project Structure

```
AG-ACE-BRIDGE/
├── modules/               # Git Submodules
│   └── Auto-Claude/       # AndyMik90/Auto-Claude (prompts, spec_agents)
│
├── src/
│   ├── modules/           # Submodule wrappers
│   │   ├── __init__.py         # Path setup
│   │   └── auto_claude_prompts.py  # Prompt loader
│   │
│   ├── coordinator/       # Layer 1: 24/7 오케스트레이션
│   │   ├── orchestrator.py     # 메인 루프
│   │   ├── task_queue.py       # SQLite 우선순위 큐
│   │   ├── agent_selector.py   # 점수 기반 에이전트 선택
│   │   ├── pipeline_builder.py # 동적 파이프라인 구성
│   │   └── README.md
│   │
│   ├── pipeline/          # Layer 2: 실행 패턴
│   │   ├── sequential.py       # 순차 실행
│   │   ├── parallel.py         # 병렬 Fan-Out/Gather
│   │   ├── critic_loop.py      # Generator-Critic 루프
│   │   └── README.md
│   │
│   ├── adapters/          # Layer 3: 에이전트 연결
│   │   ├── base.py             # 추상 베이스 클래스
│   │   ├── auto_claude.py      # Claude SDK (OAuth)
│   │   ├── ag_autogen.py       # HTTP/A2A Protocol
│   │   ├── ag_law_domain.py    # HTTP/FastAPI
│   │   └── README.md
│   │
│   ├── registry/          # 에이전트 레지스트리
│   │   ├── agent_registry.py   # 런타임 상태 관리
│   │   ├── capabilities.py     # 14개 에이전트 능력 정의
│   │   └── README.md
│   │
│   ├── memory/            # Layer 4: 메모리 동기화 (계획됨)
│   │   ├── __init__.py
│   │   └── README.md
│   │
│   ├── project/           # 프로젝트 제출 시스템
│   │   ├── spec.py             # ProjectSpec 모델
│   │   ├── watcher.py          # 폴더 감시 (watchdog)
│   │   ├── cli.py              # CLI 명령어
│   │   └── README.md
│   │
│   └── utils/             # 유틸리티
│       ├── config.py           # 환경 설정 (pydantic-settings)
│       ├── logger.py           # 구조화 로깅 (structlog)
│       ├── models.py           # 공통 모델 (Task, Result, Pipeline)
│       └── README.md
│
├── tests/
│   └── test_auto_claude_sdk.py  # SDK 연동 테스트
│
├── projects/              # 프로젝트 드랍 폴더
│   ├── queue/                  # 새 프로젝트 (감시 대상)
│   ├── completed/              # 완료된 프로젝트
│   └── failed/                 # 실패한 프로젝트
│
├── data/                  # 런타임 데이터
│   └── tasks.db               # SQLite 태스크 큐
│
├── .env                   # 환경 설정
├── requirements.txt       # 의존성
├── CLAUDE.md              # AI 에이전트용 컨텍스트 (이 파일)
└── README.md              # 이 파일
```

## Documentation Index

### AI 에이전트용 문서 (★ AI가 먼저 읽어야 함)

| 파일 | 설명 | 용도 |
|------|------|------|
| **[CLAUDE.md](CLAUDE.md)** | AI 컨텍스트 파일 | 프로젝트 이해, UI 시작 가이드 |
| **[README_INDEX.md](README_INDEX.md)** | 문서 목록 | 전체 구조 파악 |
| **[docs/USER_ACTION_GUIDE.md](docs/USER_ACTION_GUIDE.md)** | 사용자 액션 가이드 | UI 사용법, 버튼 설명 |

### 모듈별 상세 문서

| 모듈 | 설명 | README |
|------|------|--------|
| **adapters** | 에이전트 연결 (A2A, OAuth) | [src/adapters/README.md](src/adapters/README.md) |
| **coordinator** | 24/7 오케스트레이션 | [src/coordinator/README.md](src/coordinator/README.md) |
| **pipeline** | 실행 패턴 (Sequential, Parallel, Critic) | [src/pipeline/README.md](src/pipeline/README.md) |
| **memory** | SharedMemory 연동 | [src/memory/README.md](src/memory/README.md) |
| **registry** | 에이전트 레지스트리 | [src/registry/README.md](src/registry/README.md) |
| **project** | 프로젝트 제출 시스템 | [src/project/README.md](src/project/README.md) |
| **server** | 웹 대시보드 & API | [src/server/README.md](src/server/README.md) |
| **utils** | 유틸리티 | [src/utils/README.md](src/utils/README.md) |

### 통합 스크립트

| 파일 | 설명 | 용도 |
|------|------|------|
| **[run_autogen_sync_simple.py](run_autogen_sync_simple.py)** | AutoGen ↔ SharedMemory 동기화 | AutoGen 결과 자동 저장 |

### 아키텍처 문서

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - 상세 아키텍처 설계서

## Related Projects

| Project | Description | Path |
|---------|-------------|------|
| Auto-Claude | 24/7 Autonomous Coding Engine | `D:/Data/25_ACE/Auto-Claude` |
| AG | Multi-Agent Framework | `D:/Data/25_ACE/AG` |
| AG-ACE-BRIDGE | Integration Bridge (이 프로젝트) | `D:/Data/25_ACE/AG-ACE-BRIDGE` |

## Development Status

- [x] Phase 1: Foundation (폴더 구조, 모델, 설정)
- [x] Phase 2: Adapters (Auto-Claude SDK OAuth, AG HTTP, AG A2A Protocol)
- [x] Phase 3: Pipeline (Sequential, Parallel, Critic Loop)
- [x] Phase 4: Project System (Spec, Watcher, CLI)
- [x] Phase 5: Web Dashboard (FastAPI + WebSocket 실시간 모니터링)
- [x] Phase 6: AG Integration (A2A Protocol 연동, SharedMemory 클라이언트)
- [x] Phase 7: AutoGen ↔ SharedMemory 동기화 (MCP 없이 직접 연결)
- [x] Phase 8: IPC 중앙화 & Agent Terminals 협업 패널
  - Main Process에서만 8081 호출 (CORS 해결)
  - AutogenCollabPanel 실시간 대화 스트리밍
  - 2초 폴링으로 실시간 동기화
- [ ] Phase 9: E2E Testing & Polish

## License

MIT
