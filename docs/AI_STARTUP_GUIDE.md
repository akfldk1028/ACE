# AI Startup Guide - 25_ACE Ecosystem

AI 에이전트가 시스템을 시작하고 운영하기 위한 가이드.

---

## 시스템 개요

```
┌─────────────────────────────────────────────────────────────────────┐
│                          25_ACE ECOSYSTEM                            │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │  AG-ACE     │    │   AutoGen   │    │      A2A Agents         │ │
│  │  Dashboard  │    │   Studio    │    │  (8개 전문 에이전트)      │ │
│  │   :8080     │    │    :8081    │    │  :8003-8009, :8120      │ │
│  └──────┬──────┘    └──────┬──────┘    └───────────┬─────────────┘ │
│         │                  │                       │               │
│         └──────────────────┼───────────────────────┘               │
│                            │                                        │
│                  ┌─────────┴─────────┐                             │
│                  │   SharedMemory    │                             │
│                  │      :8101        │                             │
│                  └───────────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 서버 시작 순서 (필수!)

> **순서를 지켜야 함!** 의존성: A2A → SharedMemory → Dashboard → Studio

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

### Step 2: SharedMemory 서버 시작

```powershell
# 터미널 2
cd D:\Data\25_ACE\AG\autogen_a2a_kit\AG-cli
python mcp/shared_memory.py
```

| 항목 | 값 |
|------|-----|
| Port | 8101 |
| 상태 확인 | http://127.0.0.1:8101 |
| API 목록 | http://127.0.0.1:8101/docs |

**대기:** "REST API: http://127.0.0.1:8101" 출력할 때까지

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

### Step 4: AutoGen Studio 시작 (UI 2) - 선택적

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
# A2A 에이전트 확인
@(8003,8004,8005,8006,8007,8008,8009,8120) | ForEach-Object {
    $port = $_
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$port/.well-known/agent.json" -TimeoutSec 2
        Write-Host "[OK] Port $port" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] Port $port" -ForegroundColor Red
    }
}

# SharedMemory 확인
Invoke-WebRequest http://127.0.0.1:8101

# Dashboard 확인
Invoke-WebRequest http://localhost:8080/api/status
```

### curl로 확인

```bash
# SharedMemory
curl http://127.0.0.1:8101

# Dashboard 상태
curl http://localhost:8080/api/status

# A2A 에이전트 (예: calculator)
curl http://127.0.0.1:8006/.well-known/agent.json
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

```
1. start_all_agents.bat  → 2. shared_memory.py  → 3. main.py  → 4. autogenstudio ui
```

**포트 기억:**
- A2A: 8003-8009, 8120
- SharedMemory: 8101
- Dashboard: 8080
- Studio: 8081
