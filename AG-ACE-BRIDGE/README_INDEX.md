# AG-ACE-BRIDGE README INDEX

> **AI 에이전트용 문서 목록** - 다음 AI가 이 파일을 먼저 읽어야 합니다.

## 프로젝트 한눈에 보기

```
┌─────────────────────────────────────────────────────────────────┐
│                    AG-ACE-BRIDGE                                 │
│               24/7 AI PROJECT FACTORY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│   │ Auto-Claude │   │AutoGen      │   │ AG-ACE      │          │
│   │ UI (Electron)│  │Studio (8081)│   │Dashboard(80)│          │
│   └─────────────┘   └─────────────┘   └─────────────┘          │
│          │                 │                 │                  │
│   ┌──────┴─────────────────┴─────────────────┴──────┐          │
│   │              AG-ACE-BRIDGE Core                  │          │
│   │  Orchestrator → Pipeline → 19 Agents            │          │
│   └─────────────────────────────────────────────────┘          │
│                                                                  │
│   Agents:                                                        │
│   - Auto-Claude (4): Planner, Coder, QA Reviewer, QA Fixer     │
│   - AG A2A (5): Poetry, Philosophy, History, Calculator, GUI   │
│   - AG Autogen (5): Research, Analyst, Writer, Reviewer, Coord │
│   - AG Law (5): Case, Legal, Risk, Compliance, Drafter         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 핵심 문서 (AI가 먼저 읽어야 함)

| 우선순위 | 파일 | 설명 |
|---------|------|------|
| 1 | **[CLAUDE.md](CLAUDE.md)** | AI 컨텍스트, UI 시작 가이드, 아키텍처 |
| 2 | **[README_INDEX.md](README_INDEX.md)** | 이 파일 - 전체 문서 목록 |
| 3 | **[docs/USER_ACTION_GUIDE.md](docs/USER_ACTION_GUIDE.md)** | 사용자 액션 가이드 (버튼 설명) |
| 4 | **[README.md](README.md)** | 프로젝트 메인 README |

---

## Triple UI 아키텍처 (★ 중요)

이 프로젝트는 **3개의 UI**를 가집니다:

| UI | 타입 | URL | 용도 |
|---|---|---|---|
| **Auto-Claude UI** | Electron 데스크톱 | 앱 실행 | 자율 코딩 |
| **AutoGen Studio** | 웹 | http://localhost:8081 | 에이전트 빌더 |
| **AG-ACE Dashboard** | 웹 | http://localhost:8080 | 모니터링 |

### UI 시작 명령어 (순서대로)

```powershell
# 1. A2A 에이전트 (8003-8006)
cd D:\Data\25_ACE\AG\autogen_a2a_kit
python run_all_agents.py --subset

# 2. SharedMemory (8101)
cd D:\Data\25_ACE\AG\autogen_a2a_kit\AG-cli
python shared_memory.py

# 3. AG-ACE Dashboard (8080)
cd D:\Data\25_ACE\AG-ACE-BRIDGE
python main.py --dashboard

# 4. AutoGen Studio (8081)
python -c "from autogenstudio.cli import app; app()" ui --port 8081

# 5. Auto-Claude UI (Electron)
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
```

---

## Auto-Claude ↔ AG 동기화 (★★ 핵심)

### 동기화 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     동기화 데이터 흐름                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐                    ┌─────────────────┐     │
│  │  Auto-Claude    │  ◄── A2A Proto ──► │   A2A Agents    │     │
│  │  UI (Electron)  │                    │  (8003-8120)    │     │
│  │                 │                    │                 │     │
│  │  Settings →     │                    │ poetry, phil,   │     │
│  │  A2A Agents     │                    │ history, calc   │     │
│  └────────┬────────┘                    └────────┬────────┘     │
│           │                                      │              │
│           │         ┌─────────────────┐          │              │
│           └────────►│ SharedMemory    │◄─────────┘              │
│                     │    (8101)       │                         │
│                     │ - 상태 저장      │                         │
│                     │ - 이벤트 발행    │                         │
│                     └────────┬────────┘                         │
│                              │                                  │
│           ┌──────────────────┼──────────────────┐               │
│           ▼                  ▼                  ▼               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │  AutoGen        │ │  AG-ACE         │ │  AG-ACE-BRIDGE  │   │
│  │  Studio (8081)  │ │  Dashboard(8080)│ │  Orchestrator   │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Auto-Claude UI 설정 방법

1. **Settings** 열기 (우상단 톱니바퀴)
2. **Project Settings** → **A2A Agents** 클릭
3. 설정 항목:
   - **Enable A2A Agents**: ✅ 활성화
   - **AutoGen Studio URL**: `http://127.0.0.1`
   - **A2A Demo Path**: `D:/Data/25_ACE/AG/autogen_a2a_kit/a2a_demo`
   - **Auto Discovery**: ✅ 권장

### 동작 방식

1. **Auto-Claude에서 태스크 생성**
   - Kanban Board에서 "New Task" 클릭
   - Coder 에이전트가 구현 시작

2. **A2A 에이전트 자동 호출**
   - Coder가 시 작성 필요 → `poetry_agent` (8003) 호출
   - 계산 필요 → `calculator_agent` (8006) 호출
   - 철학적 분석 → `philosophy_agent` (8004) 호출

3. **결과 동기화**
   - 에이전트 실행 결과 → SharedMemory (8101)에 저장
   - Auto-Claude UI에서 실시간 확인 가능
   - AutoGen Studio에서도 같은 데이터 접근 가능

### 환경 변수 (.env)

```bash
# Auto-Claude 프로젝트 .env 파일
A2A_ENABLED=true
A2A_AUTOGEN_STUDIO_URL=http://127.0.0.1
A2A_DEMO_PATH=D:/Data/25_ACE/AG/autogen_a2a_kit/a2a_demo
A2A_AUTO_DISCOVERY=true
```

---

## 동기화 갭 분석 (★★★ 코드 검토 결과)

### 현재 연동 상태

| 컴포넌트 | SharedMemory (8101) 연동 | 상태 |
|----------|-------------------------|------|
| **AG-ACE-BRIDGE** | ✅ SharedMemoryClient 구현됨 | 완료 |
| **Auto-Claude A2A Client** | ❌ 연동 없음 | **갭** |
| **AutoGen Studio** | △ AG-ACE-BRIDGE 통해 간접 접근 | 부분 |

### 코드 검토 상세

**AG-ACE-BRIDGE (`src/adapters/ag_a2a_adapter.py`):**
```python
# Line 99, 117: SharedMemory 지원
enable_shared_memory: bool = False

# Line 240-241: 결과 저장
if self.enable_shared_memory:
    await self._share_result(task, result)
```

**Auto-Claude (`apps/backend/integrations/a2a/client.py`):**
```python
# SharedMemory 연동 없음 - A2A 프로토콜만 지원
async def send_message(self, message: str) -> Dict[str, Any]:
    # JSON-RPC 2.0으로 A2A 에이전트 호출만 함
    # SharedMemory에 결과 저장 안함 ❌
```

### 필수 구현 사항 (TODO)

| 우선순위 | 작업 | 파일 | 상태 |
|---------|------|------|------|
| 1 | Auto-Claude에 SharedMemoryClient 추가 | `a2a/shared_memory.py` (신규) | ❌ 미구현 |
| 2 | A2AClient에 SharedMemory 연동 | `a2a/client.py` 수정 | ❌ 미구현 |
| 3 | IPC에 SharedMemory 조회 API 추가 | `a2a-handlers.ts` 수정 | ❌ 미구현 |
| 4 | UI에서 SharedMemory 상태 표시 | React 컴포넌트 추가 | ❌ 미구현 |

### 권장 솔루션

```
┌─────────────────────────────────────────────────────────────────┐
│                    권장 동기화 아키텍처                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Auto-Claude A2A Client                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  A2AClient                                               │    │
│  │  ├── send_message() → A2A Agent (8003-8120)            │    │
│  │  └── sync_result() → SharedMemory (8101) ← 추가 필요   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  SharedMemoryClient (AG-ACE-BRIDGE 코드 재사용)          │    │
│  │  ├── store(key, data)                                   │    │
│  │  ├── get(key)                                           │    │
│  │  └── publish_event(type, data)                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 서비스 포트 요약

| 포트 | 서비스 | 설명 |
|------|--------|------|
| 5173 | Auto-Claude Dev Server | Electron 내부용 |
| 8003 | poetry_agent | A2A - 시/문학 |
| 8004 | philosophy_agent | A2A - 철학 |
| 8005 | history_agent | A2A - 역사 |
| 8006 | calculator_agent | A2A - 계산 |
| 8080 | AG-ACE Dashboard | 모니터링 웹 |
| 8081 | AutoGen Studio | 에이전트 빌더 웹 |
| 8101 | SharedMemory | 상태 공유 REST API |
| 8120 | gui_test_agent | A2A - GUI 자동화 |

---

## 문서 구조

### 루트 레벨

| 파일 | 설명 |
|------|------|
| [README.md](README.md) | 프로젝트 메인 README |
| [README_INDEX.md](README_INDEX.md) | 이 파일 - 문서 목록 |
| [CLAUDE.md](CLAUDE.md) | AI 에이전트용 컨텍스트 |
| [.env.example](.env.example) | 환경 변수 템플릿 |
| [requirements.txt](requirements.txt) | Python 의존성 |
| [main.py](main.py) | 메인 엔트리포인트 |

### docs/ 폴더

| 경로 | 설명 |
|------|------|
| [docs/USER_ACTION_GUIDE.md](docs/USER_ACTION_GUIDE.md) | **사용자 액션 가이드** (버튼 뭐 눌러야 하는지) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 상세 아키텍처 설계서 |
| [docs/README.md](docs/README.md) | 문서 폴더 개요 |

### src/ 소스 코드

| 경로 | 모듈 | 역할 |
|------|------|------|
| [src/README.md](src/README.md) | **소스 개요** | 4계층 아키텍처 설명 |
| [src/adapters/README.md](src/adapters/README.md) | **Adapters** | 에이전트 연결 (A2A, OAuth) |
| [src/coordinator/README.md](src/coordinator/README.md) | **Coordinator** | 24/7 오케스트레이터 |
| [src/pipeline/README.md](src/pipeline/README.md) | **Pipeline** | Sequential, Parallel, Critic Loop |
| [src/memory/README.md](src/memory/README.md) | **Memory** | SharedMemory 클라이언트 |
| [src/registry/README.md](src/registry/README.md) | **Registry** | 에이전트 레지스트리 |
| [src/server/README.md](src/server/README.md) | **Server** | Dashboard FastAPI |
| [src/project/README.md](src/project/README.md) | **Project** | 프로젝트 Watcher, CLI |
| [src/utils/README.md](src/utils/README.md) | **Utils** | 설정, 모델, 로깅 |

---

## 19개 에이전트 목록

### Auto-Claude (4개) - Claude Agent SDK + OAuth

| 에이전트 | 역할 | 파일 |
|----------|------|------|
| `planner` | 프로젝트 계획, 태스크 분해 | agents/auto_claude/planner.py |
| `coder` | 코드 작성, 24/7 자율 구현 | agents/auto_claude/coder.py |
| `qa_reviewer` | 코드 리뷰, E2E 테스트 | agents/auto_claude/qa_reviewer.py |
| `qa_fixer` | 이슈 수정, 리팩토링 | agents/auto_claude/qa_fixer.py |

### AG A2A (5개) - Google ADK A2A Protocol

| 에이전트 | 포트 | 역할 |
|----------|------|------|
| `poetry_agent` | 8003 | 시/문학 |
| `philosophy_agent` | 8004 | 철학 |
| `history_agent` | 8005 | 역사 |
| `calculator_agent` | 8006 | 계산 |
| `gui_test_agent` | 8120 | GUI 자동화 (PyAutoGUI) |

### AG Autogen (5개) - HTTP/REST

| 에이전트 | 역할 |
|----------|------|
| `research` | 정보 수집, 웹 검색 |
| `analyst` | 데이터 분석, 패턴 탐지 |
| `writer` | 문서 작성, 콘텐츠 생성 |
| `reviewer` | 리뷰 피드백, 품질 평가 |
| `coordinator` | 작업 조율, 라우팅 |

### AG Law Domain (5개) - HTTP/REST

| 에이전트 | 역할 |
|----------|------|
| `case_analyzer` | 판례 분석, 법적 선례 |
| `legal_researcher` | 법률 조사, 규정 검색 |
| `risk_assessor` | 리스크 평가, 책임 분석 |
| `compliance_checker` | 컴플라이언스 점검, 감사 |
| `document_drafter` | 법률 문서 초안 작성 |

---

## 4계층 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: COORDINATOR (중앙 조율)                                │
│   TaskQueue (SQLite) → AgentSelector → PipelineBuilder         │
│   24/7 Main Loop: dequeue → select → build → execute → handle  │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: PIPELINE (실행 패턴)                                   │
│   Sequential Pipeline │ Parallel Fan-Out │ Critic Loop (QA)   │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: ADAPTERS (에이전트 연결)                               │
│   AutoClaudeAdapter (OAuth) │ AGA2AAdapter │ AGAutogenAdapter  │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: MEMORY (상태 공유)                                     │
│   SharedMemoryClient ← HTTP → AG-CLI SharedMemory (8101)       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 관련 프로젝트

| 프로젝트 | 경로 | 설명 |
|----------|------|------|
| **Auto-Claude** | `D:/Data/25_ACE/Auto-Claude` | 24/7 자율 코딩 (Electron UI) |
| **AG** | `D:/Data/25_ACE/AG` | 멀티에이전트 프레임워크 |
| **AG-ACE-BRIDGE** | `D:/Data/25_ACE/AG-ACE-BRIDGE` | 통합 브릿지 (이 프로젝트) |
| **autogen_a2a_kit** | `D:/Data/25_ACE/AG/autogen_a2a_kit` | A2A 에이전트 + AutoGen Studio |

---

## 구현 현황

| Phase | 상태 | 설명 |
|-------|------|------|
| Phase 1 | ✅ 완료 | Foundation (폴더 구조, 모델, 설정) |
| Phase 2 | ✅ 완료 | Adapters (Auto-Claude OAuth, AG HTTP, A2A Protocol) |
| Phase 3 | ✅ 완료 | Pipeline (Sequential, Parallel, Critic Loop) |
| Phase 4 | ✅ 완료 | Project System (Spec, Watcher, CLI) |
| Phase 5 | ✅ 완료 | Memory Sync (SharedMemoryClient → AG-CLI 8101) |
| Phase 6 | ✅ 완료 | Web Dashboard (FastAPI + WebSocket) |
| Phase 7 | ✅ 완료 | AG Integration (A2A Protocol, 19 에이전트) |
| Phase 8 | ⏳ 진행중 | E2E Testing & Polish |

---

## 변경 이력

- **2026-01-23**: 동기화 갭 분석 추가 - Auto-Claude A2A Client에 SharedMemory 미연동 확인
- **2026-01-23**: 코드 검토: AG-ACE-BRIDGE AGA2AAdapter vs Auto-Claude A2AClient 비교
- **2026-01-23**: Auto-Claude ↔ AG 동기화 문서 추가, A2A 설정 가이드 작성
- **2026-01-23**: Triple UI 시작 가이드 추가, USER_ACTION_GUIDE.md 생성
- **2026-01-23**: 19개 에이전트 통합 확인, A2A 연동 테스트 완료
- **2025-01-21**: 24/7 Project Factory 추가
- **2025-01-21**: 프로젝트 생성, 아키텍처 설계
