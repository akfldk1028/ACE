# AI Startup Guide - 25_ACE Ecosystem

AI 에이전트가 시스템을 시작하고 운영하기 위한 가이드.

---

## 시스템 개요

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           25_ACE ECOSYSTEM (3-Layer)                         │
│                                                                              │
│  STEP 1: 에이전트 설계                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  AutoGen Studio (8081) - 드래그 앤 드롭 에이전트 팀 설계                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│                                      ▼ Workflow JSON                         │
│  STEP 2: 브릿지 (변환 + 실행)                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  AG-ACE-BRIDGE (8080)                                                    │ │
│  │    WorkflowExecutor.execute_full_pipeline()                              │ │
│  │      Phase 1: spec_runner.py (AI Spec 생성)                              │ │
│  │      Phase 2: run.py (빌드 실행)                                         │ │
│  │      Phase 3: Git Worktree 관리                                          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                       │
│                                      ▼ subprocess                            │
│  STEP 3: 24/7 자율 실행                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Auto-Claude (5173) - Electron UI                                        │ │
│  │    Planner → Coder → QA Reviewer → QA Fixer                              │ │
│  │    + Git Worktree 격리 빌드                                              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  [선택] A2A Agents (8003-8009, 8120) - 전문 에이전트                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 서버 시작 순서 (권장)

> **최소 필수:** AutoGen Studio(8081) + Auto-Claude UI만으로 작동!
> ★ SharedMemory(8101)는 완전히 제거됨 (2026-01-25)

### 최소 구성 (2개만!)

```powershell
# 터미널 1: AutoGen Studio (에이전트 설계)
cd D:\Data\25_ACE\AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio
autogenstudio ui --port 8081

# 터미널 2: Auto-Claude UI (24/7 실행)
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
```

| 서비스 | 포트 | 설명 |
|--------|------|------|
| AutoGen Studio | 8081 | 에이전트 팀 설계, 패턴 갤러리 |
| Auto-Claude UI | 5173 | Electron 데스크톱 앱 |

---

### 확장 구성 (추가 기능)

```powershell
# 터미널 3: A2A 에이전트 (선택)
cd D:\Data\25_ACE\AG\autogen_a2a_kit
.\start_all_agents.bat
```

| 서비스 | 포트 | 설명 |
|--------|------|------|
| A2A Agents | 8003-8009, 8120 | 전문 에이전트 (calculator, gui_test 등) |

> **Note (2026-01-25)**: SharedMemory(8101), AG-ACE Dashboard(8080) 모두 제거됨

---

### Legacy 구성 (전체) - ⚠️ 더 이상 권장하지 않음

> **Note**: 아래 Legacy 구성은 참고용입니다. SharedMemory(8101)는 완전히 제거되었습니다.

### Step 1: A2A 에이전트 시작 (8개)

```powershell
# 터미널 1
cd D:\Data\25_ACE\AG\autogen_a2a_kit
.\start_all_agents.bat
```

| Agent | Port | 상태 확인 URL |
|-------|------|---------------|
| poetry_agent | 8003 | http://127.0.0.1:8003/.well-known/agent.json |
| philosophy_agent | 8004 | http://127.0.0.1:8004/.well-known/agent.json |
| history_agent | 8005 | http://127.0.0.1:8005/.well-known/agent.json |
| calculator_agent | 8006 | http://127.0.0.1:8006/.well-known/agent.json |
| math_agent | 8007 | http://127.0.0.1:8007/.well-known/agent.json |
| graphics_agent | 8008 | http://127.0.0.1:8008/.well-known/agent.json |
| gpu_agent | 8009 | http://127.0.0.1:8009/.well-known/agent.json |
| gui_test_agent | 8120 | http://127.0.0.1:8120/.well-known/agent.json |

**대기:** 모든 에이전트가 "Running on http://127.0.0.1:PORT" 출력할 때까지

---

### Step 2: SharedMemory 서버 시작 - ❌ 제거됨

> **⚠️ SharedMemory(8101)는 2026-01-25에 완전히 제거되었습니다.**
> Auto-Claude는 이제 AutoGen Studio(8081)에 직접 연결합니다.

---

### Step 3: AG-ACE-BRIDGE Dashboard 시작 (UI 1)

```powershell
# 터미널 3
cd D:\Data\25_ACE\AG-ACE-BRIDGE
python main.py
```

| 항목 | 값 |
|------|-----|
| Port | 8080 |
| Dashboard URL | http://localhost:8080 |
| API Docs | http://localhost:8080/docs |

**대기:** 배너 출력 후 "Uvicorn running on http://0.0.0.0:8080" 나올 때까지

---

### Step 4: AutoGen Studio 시작 (UI 2)

```powershell
# 터미널 4
cd D:\Data\25_ACE\AG\autogen_a2a_kit\autogen_source\python\packages\autogen-studio
autogenstudio ui --port 8081
```

| 항목 | 값 |
|------|-----|
| Port | 8081 |
| Studio URL | http://localhost:8081 |

---

### Step 5: Auto-Claude UI 시작 (Electron)

```powershell
# 터미널 5
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
```

| 항목 | 값 |
|------|-----|
| Port | 5173 (dev) |
| 앱 | Electron 데스크톱 |

---

## 2 UI 접속 정보

### UI 1: AG-ACE-BRIDGE Dashboard (운영용)
- **URL:** http://localhost:8080
- **용도:** 24/7 오케스트레이션, 태스크 모니터링, 프로젝트 제출
- **기능:**
  - 실시간 태스크 큐 상태
  - 에이전트 상태 모니터링
  - 프로젝트 SPEC 제출
  - 실행 로그 확인

### UI 2: AutoGen Studio (개발용)
- **URL:** http://localhost:8081
- **용도:** MAS 패턴 개발, 팀 구성, A2A 테스트
- **기능:**
  - 패턴 갤러리 (11개 패턴)
  - 드래그 앤 드롭 팀 구성
  - 에이전트 테스트 실행

---

## 검증 명령어

### 전체 헬스체크 (PowerShell)

```powershell
# AutoGen Studio 확인 (★ 필수!)
Invoke-WebRequest http://localhost:8081/api/version

# A2A 에이전트 확인 (선택)
@(8003,8004,8005,8006,8007,8008,8009,8120) | ForEach-Object {
    $port = $_
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$port/.well-known/agent.json" -TimeoutSec 2
        Write-Host "[OK] Port $port" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] Port $port" -ForegroundColor Red
    }
}
```

### curl로 확인

```bash
# AutoGen Studio (★ 필수!)
curl http://localhost:8081/api/version

# A2A 에이전트 (예: calculator) (선택)
curl http://127.0.0.1:8006/.well-known/agent.json

# Vite 프록시 확인 (브라우저 모드용)
curl http://localhost:5173/api/autogen/version
```

---

## 파일 경로 요약

```
D:\Data\25_ACE\
├── AG-ACE-BRIDGE\
│   ├── main.py                    # Dashboard + Orchestrator 진입점
│   └── src\
│       ├── server\dashboard.py    # FastAPI 대시보드 (8080)
│       ├── coordinator\orchestrator.py  # 24/7 오케스트레이터
│       └── adapters\              # 에이전트 어댑터
│
├── AG\autogen_a2a_kit\
│   ├── start_all_agents.bat       # A2A 에이전트 일괄 시작
│   ├── a2a_demo\                  # 8개 A2A 에이전트
│   ├── AG-cli\mcp\
│   │   ├── shared_memory.py       # SharedMemory 서버 (8101)
│   │   └── message_bus.py         # 메시지 버스 (8100)
│   └── autogen_source\python\packages\autogen-studio\
│                                  # AutoGen Studio UI
```

---

## 트러블슈팅

| 에러 | 원인 | 해결 |
|------|------|------|
| `ConnectionRefused :8003` | A2A 에이전트 미실행 | Step 1 실행 |
| `ConnectionRefused :8101` | SharedMemory 미실행 | Step 2 실행 |
| `OPENAI_API_KEY not found` | 환경변수 미설정 | `.env` 파일 생성 |
| `autogenstudio: command not found` | 미설치 | `pip install autogenstudio` |

---

## 빠른 시작 (한 줄 요약)

### 최소 구성 (권장)
```
1. autogenstudio ui --port 8081  → 2. npm run dev (Auto-Claude)
```

### 전체 구성
```
1. start_all_agents.bat  → 2. shared_memory.py  → 3. main.py  → 4. autogenstudio ui → 5. npm run dev
```

**포트 기억:**
- AutoGen Studio: 8081 (에이전트 설계) - ★ 필수
- Auto-Claude UI: 5173 (Electron 앱) - ★ 필수
- A2A: 8003-8009, 8120 (전문 에이전트) - 선택
- ~~AG-ACE Dashboard: 8080~~ - ❌ 제거됨
- ~~SharedMemory: 8101~~ - ❌ 제거됨

---

## AG-ACE-BRIDGE 사용법 (프로그래밍 방식)

```python
from src.bridge import WorkflowExecutor

executor = WorkflowExecutor()

# AI 모드: Auto-Claude의 모든 기능 활용
result = executor.execute_full_pipeline_sync(
    task_description="계산기 앱 만들어줘",
    complexity="standard",  # simple, standard, complex
    auto_merge=False        # True면 완료 후 자동 병합
)

# 파이프라인:
# 1. spec_runner.py → AI가 Spec 생성
# 2. run.py → Planner → Coder → QA 파이프라인
# 3. Git Worktree에서 안전하게 빌드
```

---

*자세한 아키텍처는 [ARCHITECTURE.md](ARCHITECTURE.md)를 참조하세요.*
