# Documentation

AG-ACE-BRIDGE 프로젝트 문서 모음

## 문서 목록

| 문서 | 설명 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 상세 아키텍처 설계서 |
| [PATTERNS.md](PATTERNS.md) | 사용된 오케스트레이션 패턴 설명 |
| [API.md](API.md) | API 문서 |

## ARCHITECTURE.md

4계층 Hybrid Orchestration 아키텍처:

1. **Coordinator Layer**: 중앙 조율 (TaskQueue, AgentSelector, PipelineBuilder)
2. **Pipeline Layer**: 실행 흐름 (Sequential, Parallel, CriticLoop)
3. **Adapter Layer**: 에이전트 연결 (Auto-Claude SDK, AG HTTP)
4. **Memory Layer**: 메모리 동기화 (Graphiti ↔ Neo4j)

## 참조 문서

### 외부 참조
- [Microsoft AI Agent Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [Google ADK Multi-Agent Patterns](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)

### 관련 프로젝트 문서
- [Auto-Claude CLAUDE.md](../../Auto-Claude/CLAUDE.md)
- [Auto-Claude README_INDEX.md](../../Auto-Claude/README_INDEX.md)
- [AG README_INDEX.md](../../AG/agent/README_INDEX.md)
