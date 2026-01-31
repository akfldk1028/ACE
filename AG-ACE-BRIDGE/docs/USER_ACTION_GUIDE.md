# AG-ACE-BRIDGE 사용자 액션 가이드

현재 모든 서비스가 실행중입니다. 아래 가이드를 따라 사용하세요.

---

## 전체 시작 순서 (권장)

### 최소 구성 (2개만 실행! ★ 권장)

```powershell
# 1. AutoGen Studio (필수)
autogenstudio ui --port 8081
# → http://localhost:8081

# 2. Auto-Claude UI (필수)
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
# → Electron 앱 자동 실행
```

**이것만으로 AutoGen Studio 결과가 Auto-Claude UI에 실시간 표시됩니다!**

### 전체 구성 (옵션: A2A 에이전트 + Dashboard)

```powershell
# 3. A2A 에이전트 서버 (선택)
cd D:\Data\25_ACE\AG\autogen_a2a_kit
python run_all_agents.py --subset
# → http://localhost:8003-8006, 8120

# 4. AG-ACE-BRIDGE Dashboard (선택)
cd D:\Data\25_ACE\AG-ACE-BRIDGE
python main.py --dashboard
# → http://localhost:8080

# 5. SharedMemory 서버 (선택 - 폴백용)
cd D:\Data\25_ACE\AG\autogen_a2a_kit\AG-cli
python mcp/shared_memory.py
# → http://localhost:8101
```

---

## 아키텍처 (★ 2026-01-24 신규)

### 직접 연결 방식 (권장)

```
AutoGen Studio (8081)
        │
        │ ★ IPC 중앙화 (Main Process에서만 8081 호출!)
        ▼
┌─────────────────────────────────────────────────────┐
│ Main Process (Node.js / Electron)                    │
│  └── a2a-handlers.ts (유일한 8081 호출점)            │
│       ├── getAutogenLatest() → 8081 직접            │
│       └── getAutogenRunsDetailed() → 8081 직접      │
└─────────────────────────────────────────────────────┘
        │
        │ IPC (electronAPI) - 2초마다 폴링
        ▼
┌─────────────────────────────────────────────────────┐
│ Renderer Process (React UI)                          │
│  ├── Sidebar → AutogenStatusBadge (연결 상태)        │
│  ├── KanbanBoard → AutoGen 결과 Kanban 카드          │
│  ├── AutogenResultsWidget → 플로팅 위젯 (미리보기)   │
│  └── ★ Agent Terminals → AutogenCollabPanel          │
│       (터미널 없으면 풀스크린 협업 뷰!)               │
└─────────────────────────────────────────────────────┘
```

**장점:**
| 항목 | 기존 (복잡) | 신규 (단순) |
|------|-------------|-------------|
| 필요 서버 | AutoGen + SharedMemory + Sync 스크립트 | AutoGen만! |
| 설정 | 3개 프로세스 실행 | 2개만 실행 |
| 지연 | 2초 (sync) + 5초 (poll) = 7초 | 2초 (실시간!) |
| CORS | 문제 발생 가능 | 해결 (IPC 중앙화) |

### 폴백 방식 (SharedMemory 경유)

8081 직접 연결 실패 시 자동으로 8101 SharedMemory로 폴백:

```
AutoGen Studio (8081)
       │
       │ run_autogen_sync_simple.py (2초마다)
       ▼
SharedMemory (8101)
       │
       │ Auto-Claude UI 폴백 조회
       ▼
Auto-Claude UI (autogen_latest 키)
```

---

## 1. Auto-Claude UI (Electron 앱)

화면에 떠 있는 **Auto-Claude** 데스크톱 앱입니다.

### 주요 기능
| 버튼/메뉴 | 설명 |
|----------|------|
| **New Spec** | 새 프로젝트 스펙 생성 |
| **Run Build** | 자율 빌드 실행 |
| **Settings** | API 키, 모델 설정 |

### 사용 흐름
```
1. 좌측 사이드바에서 프로젝트 선택 또는 "+" 클릭
2. "Create New Spec" 버튼 클릭
3. 태스크 설명 입력 (예: "Add user authentication")
4. "Generate Spec" 클릭 → AI가 스펙 자동 생성
5. "Start Build" 클릭 → 자율 코딩 시작
```

### AutoGen Studio 연결 상태 (★ 사이드바)

좌측 사이드바에 AutoGen Studio 연결 상태가 표시됩니다:

```
┌─────────────────────────────┐
│ 🤖 AutoGen Studio   [NEW]   │
│                             │
│ AutoGen Studio (8081): Direct │
│ SharedMemory (8101): Offline  │
└─────────────────────────────┘
```

| 상태 | 의미 |
|------|------|
| **Direct** (녹색) | 8081에서 직접 연결됨 |
| **Fallback** (노란색) | 8101 SharedMemory 경유 |
| **Offline** (빨간색) | 연결 없음 |

### AutoGen 결과 Kanban 카드 (★ Kanban 보드)

AutoGen Studio에서 실행한 결과가 Kanban 보드에 자동으로 카드로 표시됩니다:

```
┌─────────────────────────────┐
│ [AutoGen] session_110       │
│ Task: 10*5 please           │
│ Status: complete ✓          │
│ Agents: assistant_agent     │
└─────────────────────────────┘
```

- **2초마다 자동 새로고침 (바로바로!)**
- **source: 'autogen-studio-direct'** → 직접 연결
- **source: 'shared-memory'** → 폴백 연결

### Agent Terminals 탭 (★ 실시간 협업 뷰)

Agent Terminals 탭에서 AutoGen Studio 대화가 실시간으로 스트리밍됩니다:

```
┌─────────────────────────────────────────────────────┐
│ 🤖 Agent Terminals + AutoGen Collaboration          │
├─────────────────────────────────────────────────────┤
│ Session 110 / Run 1                    [complete]   │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 👤 user                                          │ │
│ │ 10*5 please                                      │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 🤖 assistant_agent                              │ │
│ │ The result is 50.                               │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**동작 방식:**
- 터미널 없을 때 → AutoGen 협업 뷰가 풀스크린으로 표시
- 터미널 있을 때 → 툴바의 "AutoGen" 버튼으로 사이드바 토글
- 2초마다 자동 폴링 (IPC 통해 Main Process가 8081 호출)

---

## 2. AutoGen Studio (http://localhost:8081)

브라우저에서 http://localhost:8081 접속

### 주요 탭
| 탭 | 설명 | 버튼 |
|---|------|------|
| **Playground** | 에이전트 테스트 | "New Session" → 대화 시작 |
| **Build** | 에이전트/팀 빌더 | "New Team" → 팀 구성 |
| **Gallery** | 템플릿 갤러리 | 템플릿 클릭 → 가져오기 |
| **Deploy** | 배포 관리 | - |
| **Settings** | API 키 설정 | API 키 입력 |

### 첫 사용 순서
```
1. Settings 탭 → OpenAI API Key 입력
2. Build 탭 → "Teams" 선택 → 기본 팀 확인
3. Playground 탭 → "New Session" 클릭
4. 왼쪽에서 팀 선택 (예: "Round Robin Team")
5. 채팅창에 질문 입력 → Enter
```

### A2A 에이전트 사용 (외부 에이전트 연결)
```
1. Build 탭 → "Agents" → "New Agent"
2. Agent Type: "Remote A2A Agent"
3. URL 입력: http://localhost:8003 (poetry_agent)
4. "Save" → 팀에 추가 가능
```

---

## 3. AutoGen ↔ Auto-Claude 실시간 연동 (★ 핵심!)

AutoGen Studio에서 실행한 결과가 Auto-Claude UI에 자동으로 표시됩니다.

### 직접 연결 (권장 - 추가 설정 불필요!)

```
AutoGen Studio (8081)
       │
       │ /api/sessions/ 조회
       │ /api/sessions/{id}/runs/ 조회
       ▼
Auto-Claude UI (Vite Proxy /api/autogen → :8081)
       │
       ├─→ AutogenStatusBadge (상태)
       ├─→ KanbanBoard (Kanban 카드)
       └─→ AutogenResultsWidget (플로팅 위젯)
```

**핵심 파일:**
| 파일 | 역할 |
|------|------|
| `electron.vite.config.ts` | `/api/autogen` → 8081 프록시 |
| `browser-mock.ts` | AutoGen API 직접 호출 |
| `AutogenStatusBadge.tsx` | 사이드바 연결 상태 |
| `KanbanBoard.tsx` | AutoGen 결과 → Kanban 카드 |

### 폴백 연결 (SharedMemory 경유)

8081 연결 실패 시 자동으로 8101 SharedMemory에서 조회:

```powershell
# 1. SharedMemory 서버 시작
cd D:\Data\25_ACE\AG\autogen_a2a_kit\AG-cli
python mcp/shared_memory.py

# 2. 동기화 스크립트 시작
cd D:\Data\25_ACE\AG-ACE-BRIDGE
python -u run_autogen_sync_simple.py
```

### 저장되는 데이터 (폴백 모드)

| 키 | 설명 |
|---|---|
| `autogen_session_{id}` | 각 세션별 결과 |
| `autogen_latest` | 가장 최근 결과 |

### 데이터 형식

```json
{
  "workflow_name": "session_110",
  "task": "10*5 please",
  "result": "The result is 50.",
  "agents_used": ["assistant_agent"],
  "status": "complete",
  "timestamp": "2026-01-24T12:16:26",
  "source": "autogen-studio-direct"  // 또는 "shared-memory"
}
```

---

## 4. AG-ACE Dashboard (http://localhost:8080)

브라우저에서 http://localhost:8080 접속 (선택)

### 대시보드 화면
| 섹션 | 설명 |
|------|------|
| **Status** | 전체 시스템 상태 (녹색=정상) |
| **Agents** | 연결된 에이전트 목록 |
| **Tasks** | 실행중인 태스크 |
| **Logs** | 실시간 로그 |

### WebSocket 연결
- 자동으로 실시간 업데이트 됨
- 에이전트 실행 상태가 실시간 반영

---

## 5. A2A 에이전트 직접 테스트

### Calculator Agent (http://localhost:8006)
```bash
# Agent Card 확인
curl http://localhost:8006/.well-known/agent.json

# 계산 요청
curl -X POST http://localhost:8006/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"message/send","params":{"message":{"role":"user","parts":[{"text":"Calculate 2 + 3 * 4"}]}},"id":"1"}'
```

### Poetry Agent (http://localhost:8003)
```bash
# 시 요청
curl -X POST http://localhost:8003/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"message/send","params":{"message":{"role":"user","parts":[{"text":"Write a poem about spring"}]}},"id":"1"}'
```

---

## 6. 전체 워크플로우 예시

### 예시 1: AutoGen → Auto-Claude 연동 테스트 (직접 연결)

```
1. AutoGen Studio 실행 (8081)
2. Auto-Claude UI 실행 (npm run dev)

3. [AutoGen Studio] Playground 탭 → New Session
4. 팀 선택 (예: Round Robin Team)
5. 메시지 입력: "100 + 200 + 300 계산해줘"
6. Enter 눌러서 실행

7. [Auto-Claude UI] 5초 후 자동 표시!
   - 사이드바: AutoGen Studio - Direct (녹색)
   - Kanban: [AutoGen] session_xxx 카드
```

### 예시 2: 새 기능 개발

```
1. [Auto-Claude UI] "Create New Spec" 클릭
2. 태스크 입력: "Add login feature with JWT authentication"
3. "Generate Spec" → AI가 요구사항 분석
4. "Start Build" → 자율 코딩 시작
   - Planner Agent: 계획 수립
   - Coder Agent: 코드 작성
   - QA Reviewer: 검토
   - QA Fixer: 수정
5. 완료 시 Auto-Claude UI에서 결과 확인
```

### 예시 3: AutoGen Studio에서 커스텀 팀 만들기

```
1. [AutoGen Studio] Build 탭 → "Teams"
2. "New Team" 클릭
3. Team Type: "Round Robin" 선택
4. Agents 추가:
   - Assistant Agent (기본)
   - Remote A2A Agent (URL: http://localhost:8003)
5. "Save Team"
6. Playground 탭 → 새 세션 → 방금 만든 팀 선택
7. 대화 시작!
8. [Auto-Claude UI] 결과 자동 표시!
```

---

## 포트 요약

| 서비스 | URL | 필수 |
|--------|-----|------|
| Auto-Claude UI | 데스크톱 앱 (5173 내부) | ✅ 필수 |
| AutoGen Studio | http://localhost:8081 | ✅ 필수 |
| AG-ACE Dashboard | http://localhost:8080 | 선택 |
| SharedMemory | http://localhost:8101 | 선택 (폴백) |
| poetry_agent | http://localhost:8003 | 선택 |
| philosophy_agent | http://localhost:8004 | 선택 |
| history_agent | http://localhost:8005 | 선택 |
| calculator_agent | http://localhost:8006 | 선택 |
| gui_test_agent | http://localhost:8120 | 선택 |

---

## 문제 해결

### Auto-Claude UI에 AutoGen 결과 안 뜸

**1. AutoGen Studio 연결 확인:**
```powershell
curl http://localhost:8081/api/version
# 응답 있어야 함
```

**2. Auto-Claude UI 개발 서버 재시작:**
```powershell
cd D:\Data\25_ACE\Auto-Claude\apps\frontend
npm run dev
```

**3. 사이드바에서 AutoGen Studio 상태 확인:**
- "Direct" = 정상
- "Offline" = 8081 서버 미실행

### "연결 실패" 에러
→ 해당 서비스가 실행중인지 확인

### API 키 에러
→ Settings에서 OpenAI/Anthropic API 키 설정

### 에이전트 응답 없음
→ A2A 에이전트 서버가 실행중인지 확인 (포트 8003-8006)

### 폴백 모드로 전환하려면

8081 직접 연결 대신 SharedMemory(8101) 경유를 원하면:

```powershell
# 1. SharedMemory 서버 시작
cd D:\Data\25_ACE\AG\autogen_a2a_kit\AG-cli
python mcp/shared_memory.py

# 2. 동기화 스크립트 시작
cd D:\Data\25_ACE\AG-ACE-BRIDGE
python -u run_autogen_sync_simple.py

# 3. 8081 연결 안 되면 자동으로 8101 사용
```

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|-----------|
| 2026-01-24 | ★ IPC 중앙화 - Main Process(a2a-handlers.ts)에서만 8081 호출, CORS 해결 |
| 2026-01-24 | ★ Agent Terminals 협업 패널 - AutogenCollabPanel 실시간 대화 스트리밍 |
| 2026-01-24 | ★ 폴링 2초로 단축 - 바로바로 실시간 동기화 |
| 2026-01-24 | 직접 연결 구현 - SharedMemory(8101) 없이 AutoGen(8081) 직접 폴링 |
| 2026-01-24 | 최소 구성 (2개만 실행) 가이드 추가 |
| 2026-01-24 | 아키텍처 다이어그램 업데이트 |
