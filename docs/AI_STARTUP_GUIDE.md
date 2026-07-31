# AI Startup Guide - 25_ACE Ecosystem

AI 에이전트가 시스템을 이해하고 운영하기 위한 가이드.
마지막 검증: 2026-01-31

---

## 한줄 요약

AutoGen Studio(8081)에서 multi-agent 팀이 설계/분석/코딩하면, Auto-Claude(5173)가 3초 폴링으로 자동 감지해서 AG-ACE-BRIDGE(8080) 빌드 파이프라인을 24/7 실행하는 AI 코딩 공장.

---

## 시스템 구조

```
AutoGen Studio (8081)          Auto-Claude (5173)           AG-ACE-BRIDGE (8080)
+-----------------------+     +------------------------+   +---------------------+
| Team Builder          |     | Kanban Board           |   | Orchestrator        |
| Playground            | --> | 3s polling             | ->| Pipeline            |
| Gallery (12 patterns) |     | Agent 카드 분해         |   | Planner->Coder->QA  |
| MCP (experimental)    |     | 24/7 auto-trigger      |   | Critic Loop (x5)    |
+-----------------------+     +------------------------+   +---------------------+
         |                              |                            |
    SQLite DB                     Electron + Vite           FastAPI + WebSocket
  ~/.autogenstudio/              IPC (Electron mode)        Priority Task Queue
  autogen04203.db               Proxy (Browser mode)        19 Agent Registry
```

---

## 시작 방법

### 최소 구성 (2개만 - 권장)

```powershell
# 터미널 1: AutoGen Studio
autogenstudio ui --port 8081

# 터미널 2: Auto-Claude
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
```

이것만으로 동작:
- AutoGen Studio에서 팀 설계 + 세션 실행
- Auto-Claude Kanban에 agent별 카드가 자동 표시
- 세션 완료 시 자동 trigger (AG-ACE-BRIDGE 8080이 떠있으면)

### 파이프라인 포함 (3개)

```powershell
# 터미널 1: AutoGen Studio
autogenstudio ui --port 8081

# 터미널 2: AG-ACE-BRIDGE (파이프라인 서버)
cd D:\Data\25_ACE\AG-ACE-BRIDGE
python main.py --dashboard

# 터미널 3: Auto-Claude
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
```

추가 기능:
- AutoGen 완료 -> 자동으로 빌드 파이프라인 실행
- Dashboard(8080)에서 실시간 모니터링
- Planner -> Coder -> QA Reviewer -> QA Fixer 자동 파이프라인

### 전체 구성 (Optional 포함)

```powershell
# 터미널 1: A2A Agents (선택)
cd D:\Data\25_ACE\AG\autogen_a2a_kit\a2a_demo
python run_all_agents.py

# 터미널 2: AutoGen Studio
autogenstudio ui --port 8081

# 터미널 3: AG-ACE-BRIDGE
cd D:\Data\25_ACE\AG-ACE-BRIDGE
python main.py --dashboard

# 터미널 4: Auto-Claude
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
```

---

## 포트 요약

| Service | Port | Required | Description |
|---------|------|----------|-------------|
| **AutoGen Studio** | **8081** | **Yes** | 에이전트 팀 설계, 세션 실행 |
| **Auto-Claude** | **5173** | **Yes** | Electron Kanban, 24/7 auto-trigger |
| AG-ACE-BRIDGE | 8080 | Pipeline용 | 빌드 파이프라인, 24/7 오케스트레이터 |
| A2A Agents | 8003-8120 | Optional | 전문 에이전트 (calculator, poetry 등) |
| SharedMemory | 8101 | Optional | AG-CLI state sync (fallback) |

---

## 검증 명령어

```bash
# 필수 서비스 확인
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/    # 200 = AutoGen OK
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/    # 200 = Auto-Claude OK

# 파이프라인 확인 (선택)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health  # 200 = Bridge OK

# AutoGen API 직접 확인
curl http://localhost:8081/api/version
curl http://localhost:8081/api/sessions/

# Vite Proxy 확인 (브라우저 모드)
curl http://localhost:5173/api/autogen/version
```

```powershell
# PowerShell: A2A 에이전트 일괄 헬스체크 (선택)
@(8003,8004,8005,8006,8007,8008,8009,8120) | ForEach-Object {
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:$_/.well-known/agent.json" -TimeoutSec 2
        Write-Host "[OK] Port $_" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] Port $_" -ForegroundColor Red
    }
}
```

---

## 24/7 운영 시 주의사항

### Auto-Claude 폴링 안전장치
- `initialLoadDoneRef`: 앱 시작 시 기존 세션은 auto-trigger 안 함
- `processedSessionsRef`: 이미 trigger한 세션 중복 방지
- `isProcessingQueueRef`: 동시 파이프라인 실행 방지 (mutex)
- 1시간마다 메모리 정리 (triggerLog max 100 entries)

### Electron 프로세스
- Electron 창 닫으면 dev server도 종료됨 (exit code 1)
- 재시작: `npm run dev`

### AutoGen Studio Windows
- **`npm run build` 실행 금지!** -> `web/ui/` 폴더가 삭제됨
- 복구: `git checkout HEAD -- autogenstudio/web/ui/`
- 소스 수정은 minified JS 직접 패치 방식

---

## 데이터 저장 경로

| Data | Location | Format |
|------|----------|--------|
| AutoGen Teams | `~/.autogenstudio/autogen04203.db` (team 테이블) | SQLite, JSON column |
| AutoGen Sessions | `~/.autogenstudio/autogen04203.db` (session 테이블) | SQLite |
| AutoGen Messages | `~/.autogenstudio/autogen04203.db` (message 테이블) | SQLite |
| AG-ACE-BRIDGE Queue | `AG-ACE-BRIDGE/data/tasks.db` | SQLite |
| Auto-Claude Config | `Auto-Claude/apps/frontend/` | TypeScript files |

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| Kanban에 카드 안 보임 | AutoGen Studio 미실행 | `autogenstudio ui --port 8081` |
| Setup Wizard 가림 | 첫 실행 시 자동 표시 | "Skip Setup" 클릭 |
| auto-trigger 안 됨 | AG-ACE-BRIDGE 미실행 | `python main.py --dashboard` |
| `/build/` 페이지 빈 화면 | Team Builder SSR 누락 | `build/index.html` + `page-data/build/` 확인 |
| Electron 창 닫힘 | dev server 종료 | `npm run dev` 재실행 |
| CORS 에러 (8080) | 브라우저 모드 제한 | Electron 모드 사용 (IPC 우회) |
| `autogenstudio: not found` | 미설치 | `pip install autogenstudio` |

---

## 핵심 파일 경로

```
D:\Data\25_ACE\
├── Auto-Claude/apps/frontend/
│   ├── src/renderer/components/
│   │   ├── KanbanBoard.tsx          # 핵심: agent 분해, auto-trigger, 폴링
│   │   └── TaskCard.tsx             # 카드 렌더링, memo, stuck detection
│   ├── src/renderer/lib/
│   │   └── browser-mock.ts          # AutoGen/Bridge API 호출 (browser mode)
│   ├── src/main/ipc-handlers/
│   │   └── a2a-handlers.ts          # IPC 핸들러 (Electron mode)
│   ├── src/preload/api/modules/
│   │   └── a2a-api.ts               # Preload bridge
│   ├── src/shared/constants/ipc.ts  # IPC 채널 상수
│   ├── src/shared/types/ipc.ts      # IPC 타입 정의
│   └── electron.vite.config.ts      # Vite proxy 설정
│
├── AG-ACE-BRIDGE/
│   ├── main.py                      # 진입점 (--dashboard, --orchestrator)
│   ├── src/server/__init__.py       # FastAPI 앱
│   ├── src/server/dashboard.py      # 대시보드 + WebSocket
│   ├── src/server/pipeline_routes.py # Pipeline API
│   ├── src/coordinator/orchestrator.py # 24/7 메인 루프
│   ├── src/coordinator/task_queue.py   # SQLite 우선순위 큐
│   ├── src/coordinator/agent_selector.py # 에이전트 스코어링
│   ├── src/coordinator/pipeline_builder.py # 동적 파이프라인
│   ├── src/pipeline/                # Sequential, Parallel, CriticLoop
│   ├── src/adapters/               # 5종 어댑터
│   └── src/memory/shared_memory_client.py # SharedMemory 연동
│
├── AG/autogen_a2a_kit/
│   ├── autogen_source/.../autogen-studio/ # AutoGen Studio 소스
│   ├── a2a_demo/                    # 10개 A2A 에이전트
│   └── AG-cli/mcp/shared_memory.py  # SharedMemory 서버
│
├── README.md                        # 메인 문서
├── README_INDEX.md                  # AI 네비게이션 인덱스
├── ARCHITECTURE.md                  # 시스템 아키텍처 상세
└── docs/
    ├── AI_STARTUP_GUIDE.md          # 이 파일
    ├── PROJECT_START_GUIDE.md       # 3 UI 조정 가이드
    └── WORKFLOW_EXAMPLE.md          # GitHub Issue -> PR 예시
```

---

## 다음 AI에게

이 프로젝트는 **24/7 무중단 AI 코딩 공장**입니다. 순차적으로 이해하세요:

1. **README_INDEX.md** 먼저 읽기 (전체 구조 파악)
2. **ARCHITECTURE.md** 읽기 (데이터 흐름, 4-Layer, 19 agents)
3. **KanbanBoard.tsx** 읽기 (핵심 로직: 폴링, 분해, auto-trigger)
4. 수정 전 반드시 **`npm run build`** 가능한지 확인
5. useEffect 무한루프, memo comparator 깨짐 조심 (2026-01-31에 8개 버그 수정함)

핵심 원칙:
- AutoGen 세션 1개 = Kanban 카드 N개 (agent-level decomposition)
- 완료된 세션은 자동으로 빌드 파이프라인 trigger (24/7)
- Electron IPC / Vite Proxy 이중 모드 지원
- 향후 agent별 MCP 라우팅 예정 (metadata.agent 필드 활용)

---

*상세 아키텍처: [ARCHITECTURE.md](../ARCHITECTURE.md)*
*문서 인덱스: [README_INDEX.md](../README_INDEX.md)*
