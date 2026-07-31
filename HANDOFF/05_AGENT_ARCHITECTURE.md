# 05. 20 에이전트 아키텍처

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    20 Agent Architecture                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [Auto-Claude Agents x4] ─── Claude SDK + OAuth                  │
│   PLANNER, CODER, QA_REVIEWER, QA_FIXER                        │
│   Protocol: Direct Python SDK (no HTTP)                          │
│   Auth: sk-ant-oat01-* (env → credential file)                  │
│                                                                  │
│ [AG Autogen Agents x5] ─── HTTP/A2A → :8000                    │
│   RESEARCH, ANALYST, WRITER, REVIEWER, COORDINATOR              │
│   Protocol: JSON-RPC 2.0 (POST /agents/{name})                  │
│                                                                  │
│ [AG Law Domain Agents x5] ─── HTTP/FastAPI → :8001             │
│   CASE_ANALYZER, LEGAL_RESEARCHER, RISK_ASSESSOR,               │
│   COMPLIANCE_CHECKER, DOCUMENT_DRAFTER                           │
│   Protocol: REST (POST /legal/{role})                            │
│                                                                  │
│ [AG A2A Protocol Agents x5] ─── Individual Ports                │
│   POETRY:8003, PHILOSOPHY:8004, HISTORY:8005,                   │
│   CALCULATOR:8006, GUI_TEST:8120                                │
│   Protocol: A2A JSON-RPC (GET /.well-known/agent.json)          │
│                                                                  │
│ [Claude CLI Agent x1] ─── A2A → :9018                           │
│   CLAUDE_CLI_PLAN                                                │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ Infra: SharedMemory(:8101) + MessageBus(:8100)                  │
│ UI: AutoGen Studio(:8081) + Electron(5173)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 에이전트 카테고리별 상세

### 1. Auto-Claude Agents (4개)

Claude SDK를 직접 사용하는 핵심 개발 에이전트

| 에이전트 | 역할 | 모델 |
|----------|------|------|
| AUTO_CLAUDE_PLANNER | 구현 계획 수립, 서브태스크 분해 | Claude Opus 4.5 |
| AUTO_CLAUDE_CODER | 코드 구현 | Claude Sonnet 4.5 |
| AUTO_CLAUDE_QA_REVIEWER | 코드 품질 검토 | Claude Sonnet 4.5 |
| AUTO_CLAUDE_QA_FIXER | QA 이슈 수정 | Claude Sonnet 4.5 |

**소스 위치**: `AG/Auto-Claude/src/agents/auto_claude/`

**인증**: OAuth 토큰 (`sk-ant-oat01-*`)
- 환경변수: `CLAUDE_CODE_OAUTH_TOKEN`
- 자격증명 파일: `~/.claude/.credentials.json`

---

### 2. AG Autogen Agents (5개)

HTTP/JSON-RPC로 통신하는 연구/분석 에이전트

| 에이전트 | 역할 | 엔드포인트 |
|----------|------|------------|
| AG_RESEARCH | 기술 리서치 | POST /agents/research |
| AG_ANALYST | 데이터 분석 | POST /agents/analyst |
| AG_WRITER | 문서 작성 | POST /agents/writer |
| AG_REVIEWER | 리뷰 | POST /agents/reviewer |
| AG_COORDINATOR | 조율 | POST /agents/coordinator |

**어댑터**: `AG/Auto-Claude/src/adapters/ag_autogen.py`

---

### 3. AG Law Domain Agents (5개)

법률 도메인 특화 에이전트

| 에이전트 | 역할 | 엔드포인트 |
|----------|------|------------|
| AG_CASE_ANALYZER | 사례 분석 | POST /legal/case-analyzer |
| AG_LEGAL_RESEARCHER | 법률 리서치 | POST /legal/legal-researcher |
| AG_RISK_ASSESSOR | 리스크 평가 | POST /legal/risk-assessor |
| AG_COMPLIANCE_CHECKER | 컴플라이언스 확인 | POST /legal/compliance-checker |
| AG_DOCUMENT_DRAFTER | 문서 작성 | POST /legal/document-drafter |

**어댑터**: `AG/Auto-Claude/src/adapters/ag_law_domain.py`

---

### 4. AG A2A Protocol Agents (5개)

A2A 프로토콜을 사용하는 독립 에이전트

| 에이전트 | 역할 | 포트 |
|----------|------|------|
| A2A_POETRY | 시 생성 | 8003 |
| A2A_PHILOSOPHY | 철학적 분석 | 8004 |
| A2A_HISTORY | 역사 연구 | 8005 |
| A2A_CALCULATOR | 계산 | 8006 |
| A2A_GUI_TEST | GUI 테스트 | 8120 |

**어댑터**: `AG/Auto-Claude/src/adapters/ag_a2a_adapter.py`

---

### 5. Claude CLI Agent (1개)

Claude Code CLI를 A2A로 래핑

| 에이전트 | 역할 | 포트 |
|----------|------|------|
| CLAUDE_CLI_PLAN | CLI 기반 계획 수립 | 9018 |

---

## A2A 프로토콜 요약

### Discovery
```http
GET http://agent:port/.well-known/agent.json

Response:
{
  "name": "poetry-agent",
  "description": "시 생성 에이전트",
  "capabilities": ["poetry", "creative-writing"]
}
```

### Execute
```http
POST http://agent:port/

Request:
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "uuid",
      "role": "user",
      "parts": [{"type": "text", "text": "봄에 대한 시를 써줘"}]
    }
  },
  "id": "request-id"
}

Response:
{
  "jsonrpc": "2.0",
  "result": {
    "artifacts": [
      {"parts": [{"text": "봄이 오면 꽃이 피고..."}]}
    ]
  },
  "id": "request-id"
}
```

---

## AutoGen Studio 에이전트

AutoGen Studio UI에서 사용하는 에이전트 (Team 37 기준)

| 에이전트 | 레이블 | 모델 |
|----------|--------|------|
| insights_agent | Pipeline: Insights Analyst | Claude Sonnet 4.5 |
| deep_research_agent | Pipeline: Deep Research | Claude Sonnet 4.5 |
| spec_writer_agent | Pipeline: Spec Writer | Claude Sonnet 4.5 |
| planner_agent | Pipeline: Planner | Claude Sonnet 4.5 |
| coder_agent | Pipeline: Coder | Claude Sonnet 4.5 |
| qa_reviewer_agent | Pipeline: QA Reviewer | Claude Sonnet 4.5 |
| qa_fixer_agent | Pipeline: QA Fixer | GPT-4o-mini |
| planner_agent_1 | Auto-Claude Planner | Claude Opus 4.5 |

---

## Capability 레지스트리

**파일**: `AG/Auto-Claude/src/registry/capabilities.py` (689줄)

에이전트별 처리 가능한 작업 유형:

```python
AgentType.AUTO_CLAUDE_CODER: {
    "task_types": ["CODE", "IMPLEMENTATION", "REFACTORING"],
    "is_autonomous": True,
    "adapter_type": "auto_claude"
}

AgentType.AG_RESEARCH: {
    "task_types": ["RESEARCH", "ANALYSIS"],
    "is_autonomous": False,
    "adapter_type": "ag_http"
}
```
