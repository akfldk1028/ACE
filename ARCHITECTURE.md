# 25_ACE Integration Architecture

Auto-Claude (24/7 자율 코딩)와 AG (멀티 에이전트 프레임워크) 통합 아키텍처

## 개요

```
┌─────────────────────────────────────────────────────────────────────┐
│                    25_ACE UNIFIED AGENT ECOSYSTEM                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────┐              ┌────────────────────┐        │
│  │   AUTO-CLAUDE      │    A2A       │        AG          │        │
│  │   24/7 Autonomous  │ ◄─────────►  │   Multi-Agent      │        │
│  │   Coding Framework │   Bridge     │   Framework        │        │
│  │                    │              │                    │        │
│  │   4 Core Agents    │              │   13+ Agents       │        │
│  └─────────┬──────────┘              └─────────┬──────────┘        │
│            │                                   │                    │
│            ▼                                   ▼                    │
│  ┌────────────────────┐              ┌────────────────────┐        │
│  │  Graphiti Memory   │ ◄─────────►  │  Neo4j Knowledge   │        │
│  │  (LadybugDB)       │    Sync      │  Graph             │        │
│  │                    │              │                    │        │
│  │  - Code Patterns   │              │  - Domain Knowledge│        │
│  │  - Session Context │              │  - Legal Rules     │        │
│  │  - Insights        │              │  - Compliance      │        │
│  └────────────────────┘              └────────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 시스템 구성요소

### Auto-Claude (D:\Data\25_ACE\Auto-Claude)

24/7 자율 코딩 프레임워크

| 에이전트 | 역할 | 기능 |
|----------|------|------|
| **Planner** | 구현 계획 | 서브태스크 기반 implementation_plan.json 생성 |
| **Coder** | 24/7 코딩 | `while True:` 무한 루프로 자율 구현 |
| **QA Reviewer** | 품질 검증 | E2E 테스팅 (Electron MCP via CDP) |
| **QA Fixer** | 이슈 수정 | QA 이슈 자동 수정 (최대 5회 반복) |

**파이프라인**: SPEC → PLANNER → CODER → QA LOOP → MERGE

**메모리**: Graphiti (LadybugDB 내장, Docker 불필요)

### AG (D:\Data\25_ACE\AG)

멀티 에이전트 연구/분석 프레임워크

#### autogen_a2a_kit (8 에이전트)

| 에이전트 | 역할 |
|----------|------|
| Research Agent | 정보 수집 및 분석 |
| Analyst Agent | 데이터 분석 |
| Writer Agent | 문서 작성 |
| Reviewer Agent | 검토 및 피드백 |
| Coordinator Agent | 작업 조율 |
| 외 3개 | 특수 목적 에이전트 |

#### law-domain-agents (5 에이전트)

| 에이전트 | 역할 | Neo4j 연동 |
|----------|------|-----------|
| **CaseAnalyzer** | 판례 분석 | 판례 지식 그래프 |
| **LegalResearcher** | 법률 조사 | 법령 DB 검색 |
| **RiskAssessor** | 리스크 평가 | 리스크 패턴 매칭 |
| **ComplianceChecker** | 컴플라이언스 검증 | 규정 준수 확인 |
| **DocumentDrafter** | 문서 초안 | 템플릿 기반 생성 |

---

## 통합 아키텍처

### Layer 1: A2A Protocol Bridge

에이전트 간 통신을 위한 중앙 게이트웨이

```
┌─────────────────────────────────────────────────────────────────┐
│                     A2A PROTOCOL BRIDGE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Protocol: HTTP/WebSocket + JSON-RPC 2.0                       │
│                                                                 │
│  Message Types:                                                 │
│  ├── task_request    → 작업 요청                               │
│  ├── task_response   → 작업 응답                               │
│  ├── context_share   → 컨텍스트 공유                           │
│  ├── memory_sync     → 메모리 동기화                           │
│  └── agent_discover  → 에이전트 탐색                           │
│                                                                 │
│  Components:                                                    │
│  ├── gateway.py      → 메시지 라우팅                           │
│  ├── router.py       → 에이전트 매칭                           │
│  ├── protocol.py     → 프로토콜 정의                           │
│  └── registry.py     → 에이전트 레지스트리                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Layer 2: Memory Synchronization

Graphiti ↔ Neo4j 양방향 메모리 동기화

```
┌─────────────────────────────────────────────────────────────────┐
│                   MEMORY SYNC LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Graphiti (Auto-Claude)          Neo4j (AG)                    │
│  ├── Code Patterns        ─────► Domain Knowledge              │
│  ├── Session Insights     ─────► Implementation Context        │
│  │                                                              │
│  │                        ◄───── Legal Rules                   │
│  │                        ◄───── Compliance Requirements       │
│  └── Project Context      ◄───── Domain Constraints            │
│                                                                 │
│  Sync Strategy:                                                 │
│  ├── Event-driven (실시간 변경 감지)                           │
│  ├── Eventual Consistency (최종 일관성)                        │
│  └── Conflict Resolution (충돌 해결 정책)                      │
│                                                                 │
│  Shared Data:                                                   │
│  ├── Embedding Vectors (시맨틱 유사도)                         │
│  ├── Entity References (엔티티 참조)                           │
│  └── Metadata (메타데이터)                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Layer 3: Task Orchestration

크로스 시스템 작업 조율

```
┌─────────────────────────────────────────────────────────────────┐
│                   TASK ORCHESTRATION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Auto-Claude Tasks:                AG Tasks:                   │
│  ├── SPEC (명세 생성)              ├── RESEARCH (조사)         │
│  ├── PLAN (계획 수립)              ├── ANALYZE (분석)          │
│  ├── CODE (구현)                   ├── REVIEW (검토)           │
│  ├── QA (품질 검증)                └── DOMAIN_VALIDATE (검증)  │
│  └── MERGE (병합)                                              │
│                                                                 │
│  Cross-System Workflows:                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Research-to-Code                                     │   │
│  │    AG Research → Auto-Claude SPEC → CODE → QA          │   │
│  │                                                         │   │
│  │ 2. Domain-Validated Development                        │   │
│  │    Auto-Claude SPEC → AG Domain Validate → CODE        │   │
│  │                                                         │   │
│  │ 3. Compliance-Checked Implementation                   │   │
│  │    Auto-Claude QA → AG ComplianceChecker → MERGE       │   │
│  │                                                         │   │
│  │ 4. Legal Software Development                          │   │
│  │    AG LegalResearcher → Auto-Claude Full Pipeline      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Layer 4: Agent Registry

에이전트 탐색 및 기능 매칭

```
┌─────────────────────────────────────────────────────────────────┐
│                   AGENT REGISTRY                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Total: 17 Coordinated Agents                                   │
│                                                                 │
│  Auto-Claude (4 agents):                                        │
│  ├── planner     [planning, subtask-decomposition]             │
│  ├── coder       [implementation, 24/7-autonomous]             │
│  ├── qa_reviewer [testing, e2e, validation]                    │
│  └── qa_fixer    [debugging, issue-resolution]                 │
│                                                                 │
│  AG autogen_a2a_kit (8 agents):                                │
│  ├── research    [information-gathering, web-search]           │
│  ├── analyst     [data-analysis, pattern-detection]            │
│  ├── writer      [documentation, content-creation]             │
│  ├── reviewer    [feedback, quality-assessment]                │
│  ├── coordinator [orchestration, task-routing]                 │
│  └── ... (3 more specialized agents)                           │
│                                                                 │
│  AG law-domain (5 agents):                                     │
│  ├── case_analyzer    [case-law, precedent-analysis]           │
│  ├── legal_researcher [statute-search, regulation]             │
│  ├── risk_assessor    [risk-evaluation, liability]             │
│  ├── compliance       [compliance-check, regulation]           │
│  └── document_drafter [legal-docs, contracts]                  │
│                                                                 │
│  Capability Matching:                                           │
│  ├── Semantic Search (embedding-based)                         │
│  ├── Tag Matching (explicit capabilities)                      │
│  └── Context Awareness (project/domain specific)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 디렉토리 구조

```
D:\Data\25_ACE\
├── Auto-Claude/                # 24/7 자율 코딩 프레임워크
│   ├── apps/backend/           # Python 백엔드
│   │   ├── agents/             # 에이전트 구현
│   │   ├── core/               # 핵심 인프라
│   │   ├── integrations/       # 외부 연동 (Graphiti)
│   │   └── prompts/            # 시스템 프롬프트
│   └── README_INDEX.md         # 문서 목록
│
├── AG/                         # 멀티 에이전트 프레임워크
│   ├── agent/                  # 에이전트 프로젝트
│   │   ├── autogen_a2a_kit/    # A2A 프로토콜 에이전트
│   │   └── law-domain-agents/  # 법률 도메인 에이전트
│   └── agent/README_INDEX.md   # 문서 목록
│
├── bridge/                     # (NEW) 통합 브릿지
│   ├── gateway.py              # A2A 게이트웨이
│   ├── router.py               # 메시지 라우터
│   ├── protocol.py             # 프로토콜 정의
│   ├── registry.py             # 에이전트 레지스트리
│   └── sync/                   # 메모리 동기화
│       ├── graphiti_neo4j.py   # Graphiti ↔ Neo4j 동기화
│       └── conflict_resolver.py # 충돌 해결
│
├── ARCHITECTURE.md             # 이 파일
└── README.md                   # 프로젝트 개요
```

---

## 구현 로드맵

### Phase 1: Foundation (기초)

1. **A2A Gateway 기초 구현**
   - HTTP 엔드포인트 설정
   - JSON-RPC 2.0 프로토콜
   - 기본 메시지 라우팅

2. **Agent Registry 구현**
   - 에이전트 등록/탐색
   - 기능 태그 시스템
   - 상태 모니터링

### Phase 2: Memory Integration (메모리 통합)

1. **Graphiti → Neo4j 동기화**
   - 코드 패턴 export
   - 세션 인사이트 공유

2. **Neo4j → Graphiti 동기화**
   - 도메인 지식 import
   - 컴플라이언스 규칙 공유

### Phase 3: Workflow Automation (워크플로우 자동화)

1. **Cross-System Tasks**
   - Research-to-Code 파이프라인
   - Domain-Validated Development

2. **Orchestration Rules**
   - 자동 에이전트 매칭
   - 작업 체이닝

### Phase 4: Advanced Features (고급 기능)

1. **Self-Learning**
   - 패턴 학습
   - 최적화 자동화

2. **Scalability**
   - 분산 처리
   - 로드 밸런싱

---

## 사용 예시

### 1. 법률 소프트웨어 개발

```
[User Request: "계약서 자동 생성 기능 구현"]

1. AG LegalResearcher → 계약 법률 조사
2. AG DocumentDrafter → 계약서 템플릿 분석
3. Auto-Claude SPEC → 기능 명세 생성
4. Auto-Claude CODER → 구현 (24/7)
5. AG ComplianceChecker → 법적 검토
6. Auto-Claude QA → E2E 테스트
7. Auto-Claude MERGE → 병합 완료
```

### 2. 연구 기반 개발

```
[User Request: "최신 AI 논문 기반 추천 시스템"]

1. AG Research Agent → 논문 수집 및 분석
2. AG Analyst Agent → 알고리즘 비교
3. Auto-Claude SPEC → 구현 계획
4. Auto-Claude CODER → 코드 구현
5. Auto-Claude QA → 성능 테스트
```

### 3. 컴플라이언스 검증 개발

```
[User Request: "GDPR 준수 데이터 처리 모듈"]

1. Auto-Claude SPEC → 기능 명세
2. AG ComplianceChecker → GDPR 요구사항 확인
3. AG RiskAssessor → 리스크 평가
4. Auto-Claude CODER → 구현 (컴플라이언스 반영)
5. AG ComplianceChecker → 최종 검증
6. Auto-Claude MERGE → 병합
```

---

## 환경 설정

### 필수 환경 변수

```bash
# D:\Data\25_ACE\.env

# Auto-Claude
GRAPHITI_ENABLED=true
ANTHROPIC_API_KEY=sk-ant-...

# AG (law-domain-agents)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
OPENAI_API_KEY=sk-...

# Bridge
BRIDGE_PORT=8080
A2A_PROTOCOL_VERSION=1.0
```

### 서비스 시작

```bash
# Neo4j 시작 (AG용)
neo4j start

# Auto-Claude Backend
cd D:\Data\25_ACE\Auto-Claude\apps\backend
python run.py --list

# AG law-domain-agents
cd D:\Data\25_ACE\AG\agent\law-domain-agents
python -m uvicorn main:app --port 8000

# Bridge (구현 후)
cd D:\Data\25_ACE\bridge
python gateway.py
```

---

## 변경 이력

- 2025-01-21: 초기 아키텍처 설계 문서 작성
