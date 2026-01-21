# 25_ACE

AI Agent Coordination Ecosystem - 24/7 AI 프로젝트 팩토리

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         25_ACE ECOSYSTEM                             │
│                    AI Agent Coordination Ecosystem                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐                      ┌─────────────────┐      │
│  │   Auto-Claude   │                      │       AG        │      │
│  │   24/7 Engine   │                      │  Multi-Agent    │      │
│  │                 │                      │                 │      │
│  │  • Planner      │    AG-ACE-BRIDGE    │  • autogen_a2a  │      │
│  │  • Coder (24/7) │◄────────────────────►│    (8 agents)   │      │
│  │  • QA Reviewer  │                      │  • law-domain   │      │
│  │  • QA Fixer     │                      │    (5 agents)   │      │
│  └─────────────────┘                      └─────────────────┘      │
│          │                                        │                 │
│          ▼                                        ▼                 │
│  ┌─────────────────┐                      ┌─────────────────┐      │
│  │    Graphiti     │        Sync          │     Neo4j       │      │
│  │   (LadybugDB)   │◄────────────────────►│  Knowledge      │      │
│  └─────────────────┘                      └─────────────────┘      │
│                                                                     │
│  Total: 17 Coordinated Agents                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Projects

| 프로젝트 | 설명 | 문서 |
|----------|------|------|
| [Auto-Claude](Auto-Claude/) | 24/7 자율 코딩 프레임워크 | [README_INDEX](Auto-Claude/README_INDEX.md) |
| [AG](AG/) | 멀티에이전트 프레임워크 (18개 프로젝트) | [README_INDEX](AG/agent/README_INDEX.md) |
| [AG-ACE-BRIDGE](AG-ACE-BRIDGE/) | Auto-Claude + AG 통합 브릿지 | [README_INDEX](AG-ACE-BRIDGE/README_INDEX.md) |

## Architecture

상세 아키텍처: [ARCHITECTURE.md](ARCHITECTURE.md)

### 핵심 개념

1. **Auto-Claude**: 24/7 자율 코딩 엔진
   - SPEC → PLAN → CODE → QA → MERGE 파이프라인
   - `while True:` 무한 루프로 자율 운영
   - Claude Agent SDK 기반

2. **AG**: 멀티에이전트 전문가 팀
   - autogen_a2a_kit: 8개 A2A 프로토콜 에이전트
   - law-domain-agents: 5개 법률 도메인 에이전트
   - FastAPI HTTP 엔드포인트

3. **AG-ACE-BRIDGE**: 통합 브릿지
   - 4계층 Hybrid Orchestration
   - 17개 에이전트 조율
   - Graphiti ↔ Neo4j 메모리 동기화

## Quick Start

### Auto-Claude 실행

```bash
cd Auto-Claude/apps/backend
python run.py --list
python run.py --spec 001
```

### AG Law-Domain 실행

```bash
cd AG/agent/law-domain-agents
python -m uvicorn main:app --port 8000
```

### AG-ACE-BRIDGE 실행 (구현 예정)

```bash
cd AG-ACE-BRIDGE
pip install -r requirements.txt
python -m src.coordinator.orchestrator
```

## Directory Structure

```
D:/Data/25_ACE/
│
├── Auto-Claude/              # 24/7 자율 코딩
│   ├── apps/backend/         # Python 백엔드
│   ├── apps/frontend/        # Electron 프론트엔드
│   ├── CLAUDE.md             # Claude Code 가이드
│   └── README_INDEX.md       # 문서 목록
│
├── AG/                       # 멀티에이전트 프레임워크
│   └── agent/                # 에이전트 프로젝트들
│       ├── autogen_a2a_kit/  # A2A 프로토콜 에이전트
│       ├── law-domain-agents/# 법률 도메인 에이전트
│       └── README_INDEX.md   # 문서 목록
│
├── AG-ACE-BRIDGE/            # 통합 브릿지
│   ├── src/                  # 소스 코드
│   │   ├── coordinator/      # 24/7 오케스트레이터
│   │   ├── pipeline/         # 실행 흐름
│   │   ├── adapters/         # 에이전트 어댑터
│   │   ├── memory/           # 메모리 동기화
│   │   └── registry/         # 에이전트 레지스트리
│   ├── docs/ARCHITECTURE.md  # 상세 아키텍처
│   └── README_INDEX.md       # 문서 목록
│
├── ARCHITECTURE.md           # 전체 아키텍처 문서
└── README.md                 # 이 파일
```

## Agent Registry (17개)

### Auto-Claude (4개)
| 에이전트 | 기능 |
|----------|------|
| Planner | 구현 계획, 서브태스크 분해 |
| Coder | 24/7 자율 코딩 |
| QA Reviewer | E2E 테스트, 품질 검증 |
| QA Fixer | 이슈 수정, 디버깅 |

### AG autogen_a2a_kit (8개)
| 에이전트 | 기능 |
|----------|------|
| Research | 정보 수집, 웹 검색 |
| Analyst | 데이터 분석, 패턴 탐지 |
| Writer | 문서 작성 |
| Reviewer | 검토, 피드백 |
| Coordinator | 작업 조율 |
| ... | (3개 더) |

### AG law-domain (5개)
| 에이전트 | 기능 |
|----------|------|
| Case Analyzer | 판례 분석 |
| Legal Researcher | 법률 조사 |
| Risk Assessor | 리스크 평가 |
| Compliance Checker | 컴플라이언스 검증 |
| Document Drafter | 법률 문서 초안 |

## Use Cases

### 1. 법률 소프트웨어 개발
```
AG Legal Research → Auto-Claude SPEC → CODE → AG Compliance → QA → MERGE
```

### 2. 연구 기반 개발
```
AG Research → AG Analyst → Auto-Claude Full Pipeline
```

### 3. 24/7 자동 개선
```
Orchestrator detects → AG Analyst → Queue new tasks → Auto-Claude implements
```

## Requirements

- Python 3.10+
- Node.js (Auto-Claude frontend)
- Neo4j (AG law-domain)
- Claude API Key (ANTHROPIC_API_KEY)
- OpenAI API Key (AG)

## Documentation

- [Auto-Claude CLAUDE.md](Auto-Claude/CLAUDE.md) - Auto-Claude 핵심 가이드
- [ARCHITECTURE.md](ARCHITECTURE.md) - 전체 아키텍처
- [AG-ACE-BRIDGE Architecture](AG-ACE-BRIDGE/docs/ARCHITECTURE.md) - 브릿지 상세 설계

## License

- Auto-Claude: AGPL-3.0
- AG: Various
- AG-ACE-BRIDGE: MIT
