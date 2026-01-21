# AG-ACE-BRIDGE

24/7 AI Project Factory - Auto-Claude와 AG 멀티에이전트 통합 브릿지

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       AG-ACE-BRIDGE                              │
│                  24/7 AI PROJECT FACTORY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   AUTO-CLAUDE (4)              AG AUTOGEN (5)   AG LAW (5)     │
│   ├── Planner                  ├── Research     ├── Case Analyzer
│   ├── Coder                    ├── Analyst      ├── Legal Researcher
│   ├── QA Reviewer              ├── Writer       ├── Risk Assessor
│   └── QA Fixer                 ├── Reviewer     ├── Compliance Checker
│                                └── Coordinator  └── Document Drafter
│                                                                 │
│   Hybrid Orchestration: Coordinator + Pipeline + Critic Loop   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **24/7 자율 운영**: Auto-Claude의 무한 루프 활용
- **14개 에이전트 조율**: Auto-Claude 4 + AG Autogen 5 + AG Law Domain 5
- **Hybrid Orchestration**: 5가지 패턴 조합
  - Coordinator/Dispatcher (24/7 Main Loop)
  - Sequential Pipeline (Google ADK)
  - Parallel Fan-Out/Gather (Microsoft)
  - Generator-Critic Loop (Google ADK)
  - Dynamic Agent Selection (Score-based)
- **프로젝트 자동 실행**: YAML 드랍 → 자동 태스크 분해 → 실행
- **동적 파이프라인**: 작업 유형에 따라 자동 구성

## Quick Start

### 1. Install

```bash
cd D:/Data/25_ACE/AG-ACE-BRIDGE
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Verify SDK Integration

```bash
# Claude SDK 및 OAuth 연동 확인
python tests/test_auto_claude_sdk.py
```

### 4. Run

```bash
# 24/7 오케스트레이터 시작
python -m src.coordinator.orchestrator

# 또는 프로젝트 watcher 시작
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
├── src/
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

## Related Projects

| Project | Description | Path |
|---------|-------------|------|
| Auto-Claude | 24/7 Autonomous Coding Engine | `D:/Data/25_ACE/Auto-Claude` |
| AG | Multi-Agent Framework | `D:/Data/25_ACE/AG` |
| AG-ACE-BRIDGE | Integration Bridge (이 프로젝트) | `D:/Data/25_ACE/AG-ACE-BRIDGE` |

## Development Status

- [x] Phase 1: Foundation (폴더 구조, 모델, 설정)
- [x] Phase 2: Adapters (Auto-Claude SDK OAuth, AG HTTP)
- [x] Phase 3: Pipeline (Sequential, Parallel, Critic Loop)
- [x] Phase 4: Project System (Spec, Watcher, CLI)
- [ ] Phase 5: Memory Sync (Graphiti ↔ Neo4j)
- [ ] Phase 6: E2E Testing & Polish

## License

MIT
