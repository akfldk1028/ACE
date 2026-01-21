# AG-ACE-BRIDGE

24/7 AI Project Factory - Auto-Claude와 AG 멀티에이전트 통합 브릿지

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       AG-ACE-BRIDGE                              │
│                  24/7 AI PROJECT FACTORY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   AUTO-CLAUDE (24/7 Engine)  ◄──────►  AG (13 Expert Agents)   │
│   ├── Planner                         ├── Research Agent       │
│   ├── Coder (infinite loop)           ├── Analyst Agent        │
│   ├── QA Reviewer                     ├── Legal Researcher     │
│   └── QA Fixer                        ├── Compliance Checker   │
│                                       └── ... 9 more           │
│                                                                 │
│   Hybrid Orchestration: Coordinator + Pipeline + Critic Loop   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **24/7 자율 운영**: Auto-Claude의 무한 루프 활용
- **17개 에이전트 조율**: Auto-Claude 4 + AG 13
- **Hybrid Orchestration**: 5가지 패턴 조합
  - Coordinator/Dispatcher
  - Sequential Pipeline
  - Parallel Fan-Out/Gather
  - Generator-Critic Loop
  - Handoff
- **메모리 동기화**: Graphiti ↔ Neo4j
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
# Edit .env with your API keys
```

### 3. Run

```bash
# Start the 24/7 orchestrator
python -m src.coordinator.orchestrator

# Or run specific pipeline
python -m src.pipeline.sequential --task "Build feature X"
```

## Architecture

4-Layer Hybrid Orchestration:

```
Layer 1: Coordinator   → Task Queue + Agent Selector + Pipeline Builder
Layer 2: Pipeline      → Sequential + Parallel + Critic Loop
Layer 3: Adapters      → Auto-Claude SDK + AG HTTP Clients
Layer 4: Memory Sync   → Graphiti ↔ Neo4j
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Project Structure

```
AG-ACE-BRIDGE/
├── docs/
│   ├── ARCHITECTURE.md    # 아키텍처 설계서
│   ├── PATTERNS.md        # 사용 패턴 설명
│   └── API.md             # API 문서
│
├── src/
│   ├── coordinator/       # Layer 1: 중앙 조율
│   │   ├── orchestrator.py
│   │   ├── task_queue.py
│   │   ├── agent_selector.py
│   │   └── pipeline_builder.py
│   │
│   ├── pipeline/          # Layer 2: 실행 흐름
│   │   ├── sequential.py
│   │   ├── parallel.py
│   │   └── critic_loop.py
│   │
│   ├── adapters/          # Layer 3: 에이전트 연결
│   │   ├── base.py
│   │   ├── auto_claude.py
│   │   ├── ag_autogen.py
│   │   └── ag_law_domain.py
│   │
│   ├── memory/            # Layer 4: 메모리 동기화
│   │   ├── sync_service.py
│   │   ├── graphiti_client.py
│   │   └── neo4j_client.py
│   │
│   ├── registry/          # 에이전트 레지스트리
│   │   ├── agent_registry.py
│   │   └── capabilities.py
│   │
│   └── utils/             # 유틸리티
│       ├── config.py
│       ├── logger.py
│       └── models.py
│
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Related Projects

| Project | Description | Path |
|---------|-------------|------|
| Auto-Claude | 24/7 Autonomous Coding | `D:/Data/25_ACE/Auto-Claude` |
| AG | Multi-Agent Framework | `D:/Data/25_ACE/AG` |
| AG-ACE-BRIDGE | Integration Bridge | `D:/Data/25_ACE/AG-ACE-BRIDGE` |

## Roadmap

- [x] Phase 1: Foundation (폴더 구조, 모델)
- [ ] Phase 2: Adapters (Auto-Claude, AG 연결)
- [ ] Phase 3: Pipeline (Sequential, Parallel, Critic Loop)
- [ ] Phase 4: Memory & Polish (동기화, 테스트)

## License

MIT
