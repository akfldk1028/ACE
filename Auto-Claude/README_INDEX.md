# Auto-Claude README INDEX

프로젝트 문서 목록. 24/7 자율 코딩 프레임워크의 전체 구조와 문서를 안내합니다.

## 프로젝트 개요

Auto-Claude는 Claude Agent SDK 기반의 다중 에이전트 자율 코딩 프레임워크입니다.

```
SPEC → PLANNER → CODER → QA LOOP → FIXER → MERGE
```

**핵심 특징:**
- 24/7 자율 실행 (`while True:` 무한 루프)
- Git Worktree 격리 환경
- Graphiti 메모리 시스템 (LadybugDB 내장, Docker 불필요)
- 크로스 플랫폼 (Windows, macOS, Linux)
- E2E 테스팅 (Electron MCP via Chrome DevTools Protocol)

---

## 문서 구조

### 루트 레벨

| 파일 | 설명 |
|------|------|
| [CLAUDE.md](CLAUDE.md) | Claude Code 가이드 (핵심 레퍼런스) |
| [README.md](README.md) | 프로젝트 메인 README |
| [README_INDEX.md](README_INDEX.md) | 이 파일 - 문서 목록 |
| [RELEASE.md](RELEASE.md) | 릴리스 프로세스 |

---

## Backend 문서 (`apps/backend/`)

### 메인 문서

| 경로 | 설명 |
|------|------|
| [apps/backend/README.md](apps/backend/README.md) | Backend 메인 가이드 |

### 핵심 모듈

| 경로 | 모듈 | 역할 |
|------|------|------|
| [apps/backend/agents/README.md](apps/backend/agents/README.md) | **Agents** | 에이전트 실행 시스템 |
| [apps/backend/core/README.md](apps/backend/core/README.md) | **Core** | SDK 클라이언트, 인증, 플랫폼 추상화 |
| [apps/backend/integrations/README.md](apps/backend/integrations/README.md) | **Integrations** | Graphiti 메모리, Linear 연동 |
| [apps/backend/prompts/README.md](apps/backend/prompts/README.md) | **Prompts** | 에이전트 시스템 프롬프트 |
| [apps/backend/qa/README.md](apps/backend/qa/README.md) | **QA** | 품질 검증 (Reviewer → Fixer 루프) |

### 서브 모듈

| 경로 | 모듈 | 역할 |
|------|------|------|
| [apps/backend/core/workspace/README.md](apps/backend/core/workspace/README.md) | Workspace | Git Worktree 격리 |
| [apps/backend/merge/ai_resolver/README.md](apps/backend/merge/ai_resolver/README.md) | AI Resolver | AI 기반 병합 충돌 해결 |
| [apps/backend/project/command_registry/README.md](apps/backend/project/command_registry/README.md) | Command Registry | 명령어 등록 |
| [apps/backend/runners/ai_analyzer/README.md](apps/backend/runners/ai_analyzer/README.md) | AI Analyzer | 코드 분석 |
| [apps/backend/spec/phases/README.md](apps/backend/spec/phases/README.md) | Spec Phases | Spec 생성 단계 |
| [apps/backend/spec/validate_pkg/README.md](apps/backend/spec/validate_pkg/README.md) | Validation | Spec 검증 |
| [apps/backend/task_logger/README.md](apps/backend/task_logger/README.md) | Task Logger | 작업 로깅 |

---

## 아키텍처 다이어그램

### 파이프라인 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                     AUTO-CLAUDE PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [User Request]                                                 │
│        │                                                        │
│        ▼                                                        │
│  ┌──────────┐    Spec 생성 (3-8 단계)                          │
│  │ SPEC     │    - SIMPLE: Discovery → Quick → Validate        │
│  │ RUNNER   │    - STANDARD: Full 6-7 phases                   │
│  │          │    - COMPLEX: + Research + Critic               │
│  └────┬─────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐    서브태스크 기반 구현 계획                      │
│  │ PLANNER  │    implementation_plan.json 생성                  │
│  └────┬─────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐    while True: 무한 루프                         │
│  │ CODER    │    서브태스크별 구현                              │
│  │ (24/7)   │    에러 시 자동 재시도                            │
│  └────┬─────┘                                                   │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────────────────────┐              │
│  │           QA VALIDATION LOOP                  │              │
│  │                                               │              │
│  │  [QA Reviewer] ──→ 테스트 실행 & 검증        │              │
│  │        │           (E2E via Electron MCP)    │              │
│  │        │                                      │              │
│  │        ├─→ APPROVED? ──→ 완료!               │              │
│  │        │                                      │              │
│  │        └─→ REJECTED? ──→ [QA Fixer] ──→ 루프 │              │
│  │                              (최대 5회)       │              │
│  └────────────────────────────────────────────────┘              │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐    Git Worktree에서 메인으로                     │
│  │ MERGE    │    사용자 승인 후 병합                            │
│  └──────────┘                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 에이전트 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     AGENT ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  agents/                                                    │
│  ├── base.py ─────────────── 기본 클래스 & 인터페이스      │
│  ├── utils.py ────────────── 공용 유틸리티                 │
│  ├── memory.py ───────────── Graphiti 메모리 관리          │
│  ├── session.py ──────────── SDK 세션 실행                 │
│  │                                                          │
│  ├── planner.py ──────────── 구현 계획 에이전트            │
│  │                           └→ implementation_plan.json    │
│  │                                                          │
│  ├── coder.py ────────────── 코더 에이전트 (24/7)          │
│  │                           └→ while True 무한 루프       │
│  │                                                          │
│  └── coder_recovery.py ───── STUCK 태스크 복구             │
│                                                             │
│  Claude Agent SDK Client (core/client.py)                   │
│  ├── Security Hooks                                         │
│  ├── Tool Permissions (agent_type별)                       │
│  ├── MCP Integration                                        │
│  └── Extended Thinking                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 메모리 시스템

```
┌─────────────────────────────────────────────────────────────┐
│                  GRAPHITI MEMORY SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  integrations/graphiti/                                     │
│  ├── memory.py ────────────── GraphitiMemory 메인 클래스   │
│  ├── config.py ────────────── 설정                         │
│  ├── providers.py ─────────── 멀티 프로바이더 팩토리       │
│  │                                                          │
│  └── queries_pkg/                                           │
│      ├── graphiti.py ──────── 메인 쿼리 클래스             │
│      ├── client.py ────────── LadybugDB 클라이언트        │
│      ├── queries.py ───────── 그래프 쿼리                  │
│      ├── search.py ────────── 시맨틱 검색                  │
│      └── schema.py ────────── 스키마 정의                  │
│                                                             │
│  지원 프로바이더:                                           │
│  ├── LLM: OpenAI, Anthropic, Azure, Ollama, Google AI      │
│  └── Embedder: OpenAI, Voyage AI, Azure, Ollama, Google AI │
│                                                             │
│  Docker 불필요 - LadybugDB 내장                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 주요 파일 레퍼런스

### 핵심 엔트리포인트

| 파일 | 역할 |
|------|------|
| `apps/backend/run.py` | 메인 CLI 엔트리포인트 |
| `apps/backend/spec_runner.py` | Spec 생성 CLI |
| `apps/backend/agents/coder.py` | 24/7 코더 에이전트 (핵심) |
| `apps/backend/core/client.py` | Claude Agent SDK 클라이언트 |

### 설정 파일

| 파일 | 역할 |
|------|------|
| `apps/backend/.env` | 환경 변수 |
| `apps/backend/.env.example` | 환경 변수 템플릿 |
| `.auto-claude-security.json` | 보안 프로필 캐시 |

### Spec 디렉토리 구조

```
.auto-claude/specs/XXX-feature/
├── spec.md                  # 기능 명세
├── requirements.json        # 구조화된 요구사항
├── context.json             # 발견된 코드베이스 컨텍스트
├── implementation_plan.json # 서브태스크 기반 계획
├── qa_report.md             # QA 검증 결과
├── QA_FIX_REQUEST.md        # 수정 요청 (rejected 시)
└── graphiti/                # 메모리 데이터
```

---

## 빠른 시작

### 설치

```bash
cd apps/backend
python -m pip install -r requirements.txt

# 인증
claude
# /login 입력 후 브라우저 OAuth 완료
```

### 기본 사용

```bash
# Spec 목록
python run.py --list

# Spec 실행
python run.py --spec 001

# QA 검증
python run.py --spec 001 --qa

# 병합
python run.py --spec 001 --merge
```

---

## 관련 프로젝트

| 프로젝트 | 설명 | 연동 |
|----------|------|------|
| AG (Multi-Agent) | 18개 AI 에이전트 프로젝트 | A2A 프로토콜 |
| law-domain-agents | 법률 도메인 5개 에이전트 | Graphiti 메모리 |
| autogen_a2a_kit | A2A 프로토콜 8개 에이전트 | HTTP/WS 브릿지 |

---

## 변경 이력

- 2025-01-21: README INDEX 생성
- 2025-01-21: core, integrations, prompts, qa README 추가
