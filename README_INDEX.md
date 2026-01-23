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

## 변경 이력

| 날짜 | 변경 내용 |
|------|-----------|
| 2025-01-23 | README_INDEX.md 생성 (AI 네비게이션용) |
