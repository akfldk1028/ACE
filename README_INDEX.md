# 25_ACE README INDEX

AI 에이전트를 위한 전체 문서 인덱스. 24/7 AI Project Factory 생태계의 모든 문서와 경로를 안내합니다.

---

## 전체 구조

```
25_ACE/
├── README.md                    # 메인 README
├── README_INDEX.md              # 이 파일 (전체 문서 인덱스)
│
├── docs/                        # 통합 문서
│   ├── AI_STARTUP_GUIDE.md      # AI용 시작 가이드 ⭐
│   ├── PROJECT_START_GUIDE.md   # 3 UI 조정 가이드
│   └── WORKFLOW_EXAMPLE.md      # 완전한 워크플로우 예시
│
├── Auto-Claude/                 # 24/7 자율 코딩 엔진
│   ├── README_INDEX.md          # Auto-Claude 문서 인덱스
│   └── CLAUDE.md                # AI 컨텍스트 ⭐
│
├── AG/                          # 멀티 에이전트 시스템
│   ├── README_INDEX.md          # AG 문서 인덱스
│   └── .claude/CLAUDE.md        # AI 컨텍스트 ⭐
│
├── AG-ACE-BRIDGE/               # 통합 브릿지 (24/7 오케스트레이터)
│   ├── README_INDEX.md          # Bridge 문서 인덱스
│   └── CLAUDE.md                # AI 컨텍스트 ⭐
│
└── Calculator/                  # 예제 프로젝트
    └── README.md
```

---

## AI가 먼저 읽어야 할 파일 (우선순위)

### 1. 시스템 시작하기

| 순서 | 파일 | 설명 |
|:----:|------|------|
| 1 | **[docs/AI_STARTUP_GUIDE.md](docs/AI_STARTUP_GUIDE.md)** | 서버 시작 순서, 2 UI 운영 방법 |
| 2 | [README.md](README.md) | 전체 개요, Triple UI Architecture |

### 2. 프로젝트별 AI 컨텍스트 (CLAUDE.md)

| 프로젝트 | CLAUDE.md | 내용 |
|----------|-----------|------|
| AG-ACE-BRIDGE | **[AG-ACE-BRIDGE/CLAUDE.md](AG-ACE-BRIDGE/CLAUDE.md)** | 오케스트레이터, 어댑터, 파이프라인 |
| Auto-Claude | [Auto-Claude/CLAUDE.md](Auto-Claude/CLAUDE.md) | SDK 사용법, 에이전트 구조 |
| AG | [AG/.claude/CLAUDE.md](AG/.claude/CLAUDE.md) | A2A 에이전트, MAS 패턴 |

### 3. 프로젝트별 문서 인덱스 (README_INDEX.md)

| 프로젝트 | README_INDEX | 문서 수 |
|----------|--------------|---------|
| AG-ACE-BRIDGE | [AG-ACE-BRIDGE/README_INDEX.md](AG-ACE-BRIDGE/README_INDEX.md) | ~15 |
| Auto-Claude | [Auto-Claude/README_INDEX.md](Auto-Claude/README_INDEX.md) | ~25 |
| AG | [AG/README_INDEX.md](AG/README_INDEX.md) | ~30 |

---

## 문서 분류

### 운영 가이드 (How-To)

| 문서 | 경로 | 용도 |
|------|------|------|
| AI 시작 가이드 | [docs/AI_STARTUP_GUIDE.md](docs/AI_STARTUP_GUIDE.md) | 서버 시작, UI 접속 |
| 프로젝트 시작 가이드 | [docs/PROJECT_START_GUIDE.md](docs/PROJECT_START_GUIDE.md) | 3 UI 조정, 단계별 안내 |
| 워크플로우 예시 | [docs/WORKFLOW_EXAMPLE.md](docs/WORKFLOW_EXAMPLE.md) | GitHub Issue → PR 전체 흐름 |

### 아키텍처 문서

| 문서 | 경로 | 내용 |
|------|------|------|
| 전체 아키텍처 | [ARCHITECTURE.md](ARCHITECTURE.md) | 19 에이전트, 4계층 구조 |
| Bridge 아키텍처 | [AG-ACE-BRIDGE/docs/ARCHITECTURE.md](AG-ACE-BRIDGE/docs/ARCHITECTURE.md) | 오케스트레이터 상세 |

### AI 컨텍스트 (CLAUDE.md)

| 파일 | 내용 |
|------|------|
| [AG-ACE-BRIDGE/CLAUDE.md](AG-ACE-BRIDGE/CLAUDE.md) | 14개 에이전트, 파이프라인, SharedMemory |
| [Auto-Claude/CLAUDE.md](Auto-Claude/CLAUDE.md) | SDK 사용법, 명령어, 보안 모델 |
| [AG/.claude/CLAUDE.md](AG/.claude/CLAUDE.md) | A2A 프로토콜, AG-CLI, 패턴 |

---

## 서비스 포트 요약

| 서비스 | 포트 | 시작 명령 |
|--------|------|-----------|
| A2A Agents | 8003-8009, 8120 | `start_all_agents.bat` |
| SharedMemory | 8101 | `python mcp/shared_memory.py` |
| AG-ACE-BRIDGE | 8080 | `python main.py` |
| AutoGen Studio | 8081 | `autogenstudio ui --port 8081` |

---

## 에이전트 목록 (19개)

### Auto-Claude (4)
| 에이전트 | 역할 |
|----------|------|
| Planner | 태스크 분해, 계획 |
| Coder | 24/7 자율 코딩 |
| QA Reviewer | 품질 검증 |
| QA Fixer | 이슈 수정 |

### AG A2A (10)
| 에이전트 | 포트 | 역할 |
|----------|------|------|
| poetry_agent | 8003 | 시/문학 |
| philosophy_agent | 8004 | 철학 |
| history_agent | 8005 | 역사 |
| calculator_agent | 8006 | 계산 |
| math_agent | 8007 | 수학 |
| graphics_agent | 8008 | 그래픽 |
| gpu_agent | 8009 | GPU |
| gui_test_agent | 8120 | GUI 자동화 |
| research_agent | - | 리서치 |
| code_agent | - | 코드 분석 |

### AG Law Domain (5)
| 에이전트 | 역할 |
|----------|------|
| Case Analyzer | 판례 분석 |
| Legal Researcher | 법률 조사 |
| Risk Assessor | 리스크 평가 |
| Compliance Checker | 컴플라이언스 |
| Document Drafter | 문서 작성 |

---

## 핵심 파일 경로

### 엔트리포인트

| 파일 | 경로 | 용도 |
|------|------|------|
| Bridge 메인 | `AG-ACE-BRIDGE/main.py` | Dashboard + Orchestrator |
| A2A 시작 | `AG/autogen_a2a_kit/start_all_agents.bat` | 8개 A2A 에이전트 |
| SharedMemory | `AG/autogen_a2a_kit/AG-cli/mcp/shared_memory.py` | 8101 포트 |

### 핵심 코드

| 파일 | 경로 | 역할 |
|------|------|------|
| Orchestrator | `AG-ACE-BRIDGE/src/coordinator/orchestrator.py` | 24/7 메인 루프 |
| Dashboard | `AG-ACE-BRIDGE/src/server/dashboard.py` | FastAPI (8080) |
| A2A Adapter | `AG-ACE-BRIDGE/src/adapters/ag_a2a_adapter.py` | A2A 프로토콜 |
| Auto-Claude Adapter | `AG-ACE-BRIDGE/src/adapters/auto_claude.py` | Claude SDK |

---

## Quick Reference

```
시작하기:
  1. docs/AI_STARTUP_GUIDE.md 읽기
  2. start_all_agents.bat 실행
  3. shared_memory.py 실행
  4. main.py 실행

문서 찾기:
  - 전체 구조: README.md
  - AI 컨텍스트: */CLAUDE.md
  - 상세 문서: */README_INDEX.md

포트:
  - 8003-8009, 8120: A2A
  - 8080: Dashboard
  - 8081: Studio
  - 8101: SharedMemory
```

---

## 핵심 연동 (★ 직접 연결 - 8101 불필요!)

**AutoGen Studio(8081) → Auto-Claude UI 직접 연결:**

| 단계 | 설명 | 방식 |
|------|------|------|
| 1 | AutoGen Studio에서 워크플로우 실행 | Web UI (8081) |
| 2 | Auto-Claude UI가 5초마다 직접 조회 | Vite Proxy `/api/autogen` |
| 3 | Kanban 보드에 카드로 표시 | [AutoGen] workflow_name |

**장점 (vs 기존 방식):**
| 항목 | 기존 (복잡) | 신규 (단순) |
|------|-------------|-------------|
| 필요 서버 | AutoGen + SharedMemory + Sync 스크립트 | AutoGen만! |
| 설정 | 3개 프로세스 실행 | 2개만 실행 |
| 지연 | 2초 (sync) + 5초 (poll) = 7초 | 5초 (직접 poll) |

**핵심 파일:**

| 파일 | 역할 |
|------|------|
| `Auto-Claude/.../electron.vite.config.ts` | `/api/autogen` → 8081 프록시 |
| `Auto-Claude/.../browser-mock.ts` | AutoGen API 직접 호출 (8081 우선) |
| `Auto-Claude/.../KanbanBoard.tsx` | AutoGen 결과 Kanban 표시 |
| `Auto-Claude/.../AutogenStatusBadge.tsx` | 연결 상태 뱃지 |
| `AG-ACE-BRIDGE/run_autogen_sync_simple.py` | (선택) SharedMemory 동기화 |

## AutoGen Studio Windows 빌드/패치 가이드

> **경고**: Windows에서 Gatsby 풀빌드(`npm run build`)는 SSR 에러로 실패한다.
> 소스 수정 후 **minified JS 직접 패치** 방식으로 적용해야 한다.

**상세 가이드**: [AG/autogen_a2a_kit/autogen_source/.../frontend/README.md](../22_AG/autogen_a2a_kit/autogen_source/python/packages/autogen-studio/frontend/README.md) → "Windows 빌드 가이드" 섹션

### 핵심 경로

| 경로 | 설명 |
|------|------|
| `autogen_source/.../frontend/src/` | TypeScript 소스 (수정하는 곳) |
| `autogen_source/.../autogenstudio/web/ui/` | 실제 서빙되는 minified 파일 |
| `autogen_source/.../frontend/gatsby-node.js` | SSR null-loader 설정 |

### 소스 수정 → 적용 절차 (빌드 없이)

```
1. frontend/src/ 에서 TypeScript 소스 수정
2. autogenstudio/web/ui/ 에서 minified JS 패턴 찾기 (grep)
3. Python 스크립트로 패턴 치환
4. index.html에 cache-bust 추가 (필수!)
5. AutoGen Studio 재시작
6. 브라우저 Ctrl+Shift+R (하드 리프레시)
```

### 절대 하지 말 것

- `npm run build` 실행 금지 → `web/ui/` 폴더 삭제됨
- 삭제되면 복구: `git checkout HEAD -- autogenstudio/web/ui/`

### 알려진 이슈 (해결됨)

| 이슈 | 증상 | 해결 |
|------|------|------|
| `msg.config` undefined | `runview.tsx:162` TypeError | `e.config&&` null guard 패치 |
| SSR `/lite/` 에러 | gatsby build 실패 | `gatsby-node.js` null-loader |
| SSR `/settings/` 에러 | `@monaco-editor` SSR 접근 | 미해결 (빌드 우회) |
| Windows 빌드 문법 | `PREFIX_PATH_VALUE=''` 실패 | `npx gatsby build --prefix-paths` 직접 실행 |
| 브라우저 캐시 | 패치 후에도 에러 지속 | index.html cache-bust 추가 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|-----------|
| 2026-01-31 | AutoGen Studio Windows 빌드/패치 가이드 추가 (runview.tsx 크래시 해결) |
| 2026-01-24 | ★ 직접 연결 구현 - SharedMemory(8101) 없이 AutoGen(8081) 직접 폴링 |
| 2026-01-24 | Agent Collaboration & Data Flow 섹션 추가 |
| 2025-01-23 | README_INDEX.md 생성 (AI 네비게이션용) |
