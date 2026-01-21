# AG-ACE-BRIDGE Architecture

24/7 AI Project Factory - Auto-Claude와 AG 멀티에이전트 통합 브릿지

## Overview

AG-ACE-BRIDGE는 **Hybrid Orchestration Pattern**을 사용하여 두 AI 시스템을 연결합니다:
- **Auto-Claude**: 24/7 자율 코딩 프레임워크 (SPEC→PLAN→CODE→QA→MERGE)
- **AG**: 멀티에이전트 연구/분석 프레임워크 (13개 전문 에이전트)

```
┌─────────────────────────────────────────────────────────────────────┐
│                       AG-ACE-BRIDGE                                  │
│                  24/7 AI PROJECT FACTORY                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Task Queue ──→ Orchestrator ──→ Pipeline ──→ Result              │
│        ↑              │               │            │                │
│        │              ▼               ▼            │                │
│        │    ┌─────────────┐   ┌─────────────┐    │                │
│        │    │ Auto-Claude │ ↔ │     AG      │    │                │
│        │    │  (24/7)     │   │ (13 agents) │    │                │
│        │    └─────────────┘   └─────────────┘    │                │
│        │                                          │                │
│        └────────── New Tasks ◄────────────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Design Patterns Used

### 1. Coordinator/Dispatcher Pattern (Microsoft)
중앙 오케스트레이터가 작업을 적절한 에이전트에게 라우팅

```
Input → Coordinator → Select Agent → Execute → Result
              │
              └→ Capability Matching
              └→ Load Balancing
              └→ Priority Scheduling
```

### 2. Sequential Pipeline Pattern
Auto-Claude의 기본 흐름: SPEC → PLAN → CODE → QA → MERGE

```
[Research] → [SPEC] → [PLAN] → [CODE] → [QA] → [MERGE]
   (AG)      (Auto)   (Auto)   (Auto)   (Auto)  (Auto)
```

### 3. Parallel Fan-Out/Gather Pattern
AG 에이전트들의 병렬 실행 후 결과 통합

```
           ┌→ Research Agent ─┐
Task ──→   ├→ Analyst Agent  ─┼→ Aggregate → Result
           └→ Domain Agent   ─┘
```

### 4. Generator-Critic Loop Pattern (Google ADK)
Auto-Claude QA Loop의 핵심 패턴

```
[Coder] ──→ [QA Reviewer] ──→ Approved? ──→ Done
   ↑              │              │
   │              └── Rejected ──┘
   │                    │
   └──── [QA Fixer] ◄───┘
         (max 5 iterations)
```

### 5. Handoff Pattern
AG ↔ Auto-Claude 간 컨텍스트 전달

```
AG Research ──→ Context Handoff ──→ Auto-Claude SPEC
                     │
                     └→ Full context transfer
                     └→ Memory sync
```

---

## 4-Layer Architecture

### Layer 1: Coordinator (중앙 조율)

```
┌─────────────────────────────────────────────────────────────────┐
│                         COORDINATOR                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Task Queue  │  │   Agent      │  │  Pipeline    │         │
│  │  (SQLite)    │  │   Selector   │  │  Builder     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                     │
│                  ┌──────────────┐                               │
│                  │ Orchestrator │                               │
│                  │  (24/7 Loop) │                               │
│                  └──────────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**
- **TaskQueue**: SQLite 기반 우선순위 작업 큐
- **AgentSelector**: 작업 요구사항 기반 에이전트 선택
- **PipelineBuilder**: 동적 파이프라인 구성
- **Orchestrator**: 24/7 메인 루프

### Layer 2: Pipeline (실행 흐름)

```
┌─────────────────────────────────────────────────────────────────┐
│                          PIPELINE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Sequential:                                                    │
│  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐        │
│  │Stage1│ → │Stage2│ → │Stage3│ → │Stage4│ → │Stage5│        │
│  └──────┘   └──────┘   └──────┘   └──────┘   └──────┘        │
│                                                                 │
│  Parallel:                                                      │
│  ┌──────┐   ┌──────┐                                           │
│  │AgentA│ ↘       ↗ │Merge │                                   │
│  │AgentB│ → Gather → │Result│                                   │
│  │AgentC│ ↗       ↘ │      │                                   │
│  └──────┘   └──────┘                                           │
│                                                                 │
│  Critic Loop:                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                   │
│  │Generator │ → │  Critic  │ → │  Fixer   │ ─┐                │
│  └──────────┘   └──────────┘   └──────────┘  │                │
│       ↑                                       │                │
│       └───────────────────────────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**
- **Sequential**: 선형 스테이지 실행
- **Parallel**: 병렬 실행 + 결과 집계
- **CriticLoop**: Generator-Critic 반복

### Layer 3: Adapters (에이전트 연결)

```
┌─────────────────────────────────────────────────────────────────┐
│                          ADAPTERS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                   AgentAdapter (Base)                   │    │
│  │  + execute(task, context) → Result                     │    │
│  │  + health_check() → bool                               │    │
│  │  + get_capabilities() → List[str]                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                            │                                    │
│          ┌─────────────────┼─────────────────┐                 │
│          ▼                 ▼                 ▼                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ AutoClaude   │  │ AGAutogen    │  │ AGLawDomain  │        │
│  │ Adapter      │  │ Adapter      │  │ Adapter      │        │
│  │              │  │              │  │              │        │
│  │ - SDK Session│  │ - HTTP Client│  │ - HTTP Client│        │
│  │ - Graphiti   │  │ - A2A Proto  │  │ - Neo4j      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Adapters:**
- **AutoClaudeAdapter**: Claude Agent SDK 세션 관리
- **AGAutogenAdapter**: autogen_a2a_kit HTTP 클라이언트
- **AGLawDomainAdapter**: law-domain-agents HTTP 클라이언트

### Layer 4: Memory Sync (컨텍스트 공유)

```
┌─────────────────────────────────────────────────────────────────┐
│                        MEMORY SYNC                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────┐         │
│  │    Graphiti          │    │      Neo4j           │         │
│  │    (LadybugDB)       │    │    (Knowledge)       │         │
│  │                      │    │                      │         │
│  │  - Code Patterns     │ ←→ │  - Domain Knowledge  │         │
│  │  - Session Insights  │    │  - Legal Rules       │         │
│  │  - Implementation    │    │  - Compliance        │         │
│  └──────────────────────┘    └──────────────────────┘         │
│              │                        │                        │
│              └────────────┬───────────┘                        │
│                           ▼                                     │
│                  ┌──────────────┐                               │
│                  │  Sync        │                               │
│                  │  Service     │                               │
│                  │              │                               │
│                  │  - Event     │                               │
│                  │    Driven    │                               │
│                  │  - Conflict  │                               │
│                  │    Resolver  │                               │
│                  └──────────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**
- **GraphitiClient**: Auto-Claude 메모리 연동
- **Neo4jClient**: AG 지식 그래프 연동
- **SyncService**: 양방향 동기화

---

## Data Flow

### Complete Pipeline Flow

```
1. TASK INPUT
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ TaskQueue.push(task)                                            │
│ - priority: HIGH/MEDIUM/LOW                                     │
│ - type: RESEARCH/SPEC/CODE/VALIDATE                            │
│ - context: {...}                                                │
└─────────────────────────────────────────────────────────────────┘
   │
   ▼
2. ORCHESTRATOR PROCESSING
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ task = queue.pop()                                              │
│ agents = registry.select(task.requirements)                     │
│ pipeline = builder.build(task, agents)                         │
└─────────────────────────────────────────────────────────────────┘
   │
   ▼
3. PIPELINE EXECUTION
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ for stage in pipeline:                                          │
│     adapter = get_adapter(stage.agent)                         │
│     result = adapter.execute(task, context)                    │
│     context.update(result)                                      │
│                                                                 │
│     if stage.critic_loop:                                      │
│         while not approved and iterations < 5:                  │
│             critic_result = critic.review(result)              │
│             if critic_result.approved: break                   │
│             result = fixer.fix(critic_result.issues)           │
│             iterations += 1                                    │
└─────────────────────────────────────────────────────────────────┘
   │
   ▼
4. RESULT HANDLING
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ memory_sync.save_insights(result.insights)                     │
│ for next_task in result.next_tasks:                            │
│     queue.push(next_task)                                      │
│ # Loop continues → 24/7 operation                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Registry

### Registered Agents (17 Total)

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT REGISTRY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  AUTO-CLAUDE (4 agents)                                         │
│  ├── planner                                                    │
│  │   └── capabilities: [planning, subtask-decomposition]       │
│  ├── coder                                                      │
│  │   └── capabilities: [implementation, 24/7-autonomous]       │
│  ├── qa_reviewer                                                │
│  │   └── capabilities: [testing, e2e, validation]              │
│  └── qa_fixer                                                   │
│      └── capabilities: [debugging, issue-resolution]           │
│                                                                 │
│  AG AUTOGEN_A2A_KIT (8 agents)                                 │
│  ├── research_agent                                             │
│  │   └── capabilities: [information-gathering, web-search]     │
│  ├── analyst_agent                                              │
│  │   └── capabilities: [data-analysis, pattern-detection]      │
│  ├── writer_agent                                               │
│  │   └── capabilities: [documentation, content-creation]       │
│  ├── reviewer_agent                                             │
│  │   └── capabilities: [feedback, quality-assessment]          │
│  ├── coordinator_agent                                          │
│  │   └── capabilities: [orchestration, task-routing]           │
│  └── ... (3 more specialized)                                  │
│                                                                 │
│  AG LAW-DOMAIN (5 agents)                                      │
│  ├── case_analyzer                                              │
│  │   └── capabilities: [case-law, precedent-analysis]          │
│  ├── legal_researcher                                           │
│  │   └── capabilities: [statute-search, regulation]            │
│  ├── risk_assessor                                              │
│  │   └── capabilities: [risk-evaluation, liability]            │
│  ├── compliance_checker                                         │
│  │   └── capabilities: [compliance, regulation-check]          │
│  └── document_drafter                                           │
│      └── capabilities: [legal-docs, contracts]                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Capability Matching

```python
# Example: Task requires legal research and code implementation
task.requirements = ["legal-research", "implementation"]

# Agent Selector finds:
# 1. AG legal_researcher (legal-research)
# 2. Auto-Claude coder (implementation)

# Pipeline Builder creates:
# [legal_researcher] → [auto_claude.spec] → [auto_claude.coder]
```

---

## Use Cases

### 1. Legal Software Development

```
User Request: "계약서 자동 생성 기능 구현"

Pipeline:
┌──────────────────┐
│ AG               │
│ legal_researcher │ → 계약 법률 조사
└────────┬─────────┘
         ▼
┌──────────────────┐
│ AG               │
│ document_drafter │ → 템플릿 분석
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Auto-Claude      │
│ SPEC → PLAN      │ → 기능 명세 & 계획
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Auto-Claude      │
│ CODER (24/7)     │ → 구현
└────────┬─────────┘
         ▼
┌──────────────────┐
│ AG               │
│ compliance       │ → 법적 검토
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Auto-Claude      │
│ QA Loop          │ → 테스트 & 수정
└────────┬─────────┘
         ▼
       완료!
```

### 2. Research-Driven Development

```
User Request: "최신 AI 논문 기반 추천 시스템"

Pipeline:
[AG research] → [AG analyst] → [Auto-Claude full pipeline]
      │              │
      └──────────────┴→ Context shared to Auto-Claude
```

### 3. Continuous Improvement

```
자동 실행 (24/7):

Orchestrator detects:
- Completed task → Generate improvement suggestions
- AG Analyst → Analyze code quality
- Queue new tasks → Auto-Claude implements

Result: Self-improving codebase!
```

---

## Configuration

### Environment Variables (.env)

```bash
# AG-ACE-BRIDGE Configuration
BRIDGE_PORT=8080
BRIDGE_LOG_LEVEL=INFO

# Auto-Claude Connection
AUTO_CLAUDE_PATH=D:/Data/25_ACE/Auto-Claude/apps/backend
GRAPHITI_ENABLED=true
ANTHROPIC_API_KEY=sk-ant-...

# AG Connection
AG_AUTOGEN_URL=http://localhost:8000
AG_LAW_DOMAIN_URL=http://localhost:8001

# Neo4j (AG Memory)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# Task Queue
QUEUE_DB_PATH=./data/tasks.db
QUEUE_MAX_RETRIES=3

# Pipeline Settings
MAX_QA_ITERATIONS=5
DEFAULT_PRIORITY=MEDIUM
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [x] Folder structure
- [ ] Data models (Task, Result, Pipeline)
- [ ] TaskQueue (SQLite)
- [ ] Basic Orchestrator loop

### Phase 2: Adapters (Week 2)
- [ ] Base Adapter interface
- [ ] Auto-Claude Adapter
- [ ] AG Autogen Adapter
- [ ] AG Law-Domain Adapter

### Phase 3: Pipeline (Week 3)
- [ ] Sequential execution
- [ ] Parallel Fan-Out/Gather
- [ ] Generator-Critic Loop
- [ ] Pipeline Builder

### Phase 4: Memory & Polish (Week 4)
- [ ] Graphiti client
- [ ] Neo4j client
- [ ] Sync service
- [ ] Tests & Documentation

---

## Related Documents

- [PATTERNS.md](./PATTERNS.md) - Detailed pattern explanations
- [API.md](./API.md) - API documentation
- [../README.md](../README.md) - Project overview

---

## References

- [Microsoft AI Agent Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [Google ADK Multi-Agent Patterns](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
- [Auto-Claude CLAUDE.md](../../Auto-Claude/CLAUDE.md)
- [AG README_INDEX.md](../../AG/agent/README_INDEX.md)
