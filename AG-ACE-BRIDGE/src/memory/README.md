# Memory Module

메모리 동기화 모듈. Graphiti (Auto-Claude)와 Neo4j (AG) 간의 양방향 메모리 동기화를 담당합니다.

## 구조

```
memory/
├── __init__.py
├── sync_service.py      # 동기화 서비스 (핵심)
├── graphiti_client.py   # Graphiti 클라이언트
└── neo4j_client.py      # Neo4j 클라이언트
```

## 아키텍처

```
┌──────────────────────┐    ┌──────────────────────┐
│    Graphiti          │    │      Neo4j           │
│    (LadybugDB)       │    │    (Knowledge)       │
│                      │    │                      │
│  - Code Patterns     │ ←→ │  - Domain Knowledge  │
│  - Session Insights  │    │  - Legal Rules       │
│  - Implementation    │    │  - Compliance        │
└──────────────────────┘    └──────────────────────┘
            │                        │
            └────────────┬───────────┘
                         ▼
                ┌──────────────┐
                │  Sync        │
                │  Service     │
                └──────────────┘
```

## 핵심 컴포넌트

### sync_service.py - 동기화 서비스

```python
class MemorySyncService:
    """
    Graphiti ↔ Neo4j 양방향 동기화
    - Event-driven sync
    - Conflict resolution
    - Eventual consistency
    """

    async def sync_to_neo4j(self, insights: List[str]) -> None:
        """Auto-Claude 인사이트 → Neo4j"""
        for insight in insights:
            embedding = await self.graphiti.get_embedding(insight)
            await self.neo4j.store_insight(insight, embedding)

    async def sync_from_neo4j(self, query: str) -> List[str]:
        """Neo4j 도메인 지식 → Graphiti 컨텍스트"""
        knowledge = await self.neo4j.search(query)
        return knowledge
```

### graphiti_client.py - Graphiti 클라이언트

```python
class GraphitiClient:
    """
    Auto-Claude Graphiti 메모리 연동
    - LadybugDB 접근 (Docker 불필요)
    - Semantic search
    - Session insights
    """

    async def get_context(self, query: str) -> dict:
        """세션 컨텍스트 검색"""
        ...

    async def add_insight(self, insight: str) -> None:
        """인사이트 저장"""
        ...

    async def get_embedding(self, text: str) -> List[float]:
        """임베딩 벡터 생성"""
        ...
```

### neo4j_client.py - Neo4j 클라이언트

```python
class Neo4jClient:
    """
    AG Neo4j 지식 그래프 연동
    - 도메인 지식 쿼리
    - 법률 규칙 검색
    - 컴플라이언스 요구사항
    """

    async def search(self, query: str) -> List[dict]:
        """지식 그래프 검색"""
        cypher = """
        MATCH (n)-[r]->(m)
        WHERE n.content CONTAINS $query
        RETURN n, r, m
        """
        return await self.run(cypher, {"query": query})

    async def store_insight(self, insight: str, embedding: List[float]) -> None:
        """인사이트 저장"""
        ...
```

## 동기화 전략

### 1. Event-Driven Sync
작업 완료 시 자동 동기화

```python
# Pipeline 완료 후
result = await pipeline.execute(task)
await memory_sync.sync_to_neo4j(result.insights)
```

### 2. On-Demand Sync
필요 시 수동 동기화

```python
# 도메인 지식 필요 시
context = await memory_sync.sync_from_neo4j("contract law")
```

### 3. Conflict Resolution
충돌 해결 정책

```python
class ConflictResolver:
    """
    충돌 해결 전략
    - Last-write-wins
    - Merge
    - Manual resolution
    """
```

## 동기화 데이터

### Graphiti → Neo4j
| 데이터 | 설명 |
|--------|------|
| Code Patterns | 코드 패턴, 베스트 프랙티스 |
| Session Insights | 세션 중 발견된 인사이트 |
| Implementation Context | 구현 컨텍스트 |

### Neo4j → Graphiti
| 데이터 | 설명 |
|--------|------|
| Domain Knowledge | 도메인 지식 |
| Legal Rules | 법률 규칙 (law-domain) |
| Compliance Requirements | 컴플라이언스 요구사항 |

## 사용법

```python
from src.memory import MemorySyncService

sync = MemorySyncService()

# Auto-Claude 인사이트 → Neo4j
await sync.sync_to_neo4j(["Pattern: use async/await for I/O"])

# Neo4j 도메인 지식 → Graphiti
knowledge = await sync.sync_from_neo4j("계약법 요구사항")
```

## 설정

```bash
# .env
GRAPHITI_ENABLED=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
```

## 관련 파일

- `Auto-Claude/apps/backend/integrations/graphiti/`: Graphiti 구현
- `AG/agent/law-domain-agents/`: Neo4j 연동 에이전트
- `src/utils/models.py`: MemorySyncEvent 모델
