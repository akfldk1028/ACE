# Source Code

AG-ACE-BRIDGE 소스 코드 구조

## 모듈 구조

```
src/
├── __init__.py
│
├── coordinator/        # Layer 1: 중앙 조율
│   ├── orchestrator.py     # 24/7 메인 루프
│   ├── task_queue.py       # 작업 큐
│   ├── agent_selector.py   # 에이전트 선택
│   └── pipeline_builder.py # 파이프라인 구성
│
├── pipeline/           # Layer 2: 실행 흐름
│   ├── sequential.py       # Sequential 패턴
│   ├── parallel.py         # Parallel 패턴
│   └── critic_loop.py      # Critic Loop 패턴
│
├── adapters/           # Layer 3: 에이전트 연결
│   ├── base.py             # 기본 인터페이스
│   ├── auto_claude.py      # Auto-Claude SDK
│   ├── ag_autogen.py       # AG HTTP
│   └── ag_law_domain.py    # AG Law Domain
│
├── memory/             # Layer 4: 메모리 동기화
│   ├── sync_service.py     # 동기화 서비스
│   ├── graphiti_client.py  # Graphiti
│   └── neo4j_client.py     # Neo4j
│
├── registry/           # 에이전트 레지스트리
│   ├── agent_registry.py   # 등록/탐색
│   └── capabilities.py     # 기능 정의
│
└── utils/              # 유틸리티
    ├── config.py           # 설정
    ├── models.py           # 데이터 모델
    └── logger.py           # 로깅
```

## 4계층 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: COORDINATOR                                            │
│ - TaskQueue: 작업 대기열 관리                                   │
│ - AgentSelector: 요구사항 기반 에이전트 선택                    │
│ - PipelineBuilder: 동적 파이프라인 구성                         │
│ - Orchestrator: 24/7 메인 루프                                  │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: PIPELINE                                               │
│ - Sequential: 선형 실행                                         │
│ - Parallel: 병렬 실행 + 결과 집계                               │
│ - CriticLoop: Generator-Critic 반복                             │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: ADAPTERS                                               │
│ - AutoClaudeAdapter: Claude Agent SDK 연동                      │
│ - AGAutogenAdapter: autogen_a2a_kit HTTP                        │
│ - AGLawDomainAdapter: law-domain-agents HTTP                    │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: MEMORY                                                 │
│ - GraphitiClient: Auto-Claude 메모리                            │
│ - Neo4jClient: AG 지식 그래프                                   │
│ - SyncService: 양방향 동기화                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Import Convention

```python
# 모델
from src.utils import Task, Result, Pipeline, AgentType

# 설정
from src.utils.config import get_settings

# 어댑터
from src.adapters import AgentAdapter
from src.adapters.auto_claude import AutoClaudeAdapter

# 파이프라인
from src.pipeline import SequentialPipeline, ParallelPipeline

# 레지스트리
from src.registry import AgentRegistry
```

## 각 모듈 README

- [coordinator/README.md](coordinator/README.md)
- [pipeline/README.md](pipeline/README.md)
- [adapters/README.md](adapters/README.md)
- [memory/README.md](memory/README.md)
- [registry/README.md](registry/README.md)
- [utils/README.md](utils/README.md)
