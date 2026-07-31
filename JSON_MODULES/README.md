# JSON_MODULES - AutoGen n8n-Style Composable Components

AutoGen Studio 컴포넌트를 JSON 모듈화하여 DRY 방식으로 조합하는 시스템.
`$ref`로 에이전트/모델/종료조건을 참조하고, 컴팩트 템플릿을 full-inline JSON으로 resolve한다.

## Quick Start

```bash
# 1. 모든 컴팩트 템플릿 resolve
python ref_resolver.py --all

# 2. 유효성 검증
python validate_json.py

# 3. AutoGen Studio에 임포트
python ref_resolver.py --import

# 4. A2A 에이전트 관리
python a2a_manager.py --list
python a2a_manager.py --check
```

## Directory Structure

```
JSON_MODULES/
  agents/                       23 standalone agent definitions
    auto_claude_01_...json        Auto-Claude Planner
    auto_claude_02_...json        Auto-Claude Coder
    ...                           (7 auto_claude + 5 debate/reflection + 11 sequential/selector/handoff)
  a2a_agents/                   10 A2A agent definitions (Google ADK)
    calculator_agent.json         port 8006 - 수학 계산
    poetry_agent.json             port 8003 - 시/문학 분석
    philosophy_agent.json         port 8004 - 철학
    history_agent.json            port 8005 - 역사
    math_agent.json               port 8007 - 대수학/정수론
    graphics_agent.json           port 8008 - 컴퓨터 그래픽스
    gpu_agent.json                port 8009 - GPU/병렬 컴퓨팅
    gui_test_agent.json           port 8120 - GUI 자동화
    history_helper_agent.json     port 8001 - 역사 숙제 도우미
    remote_prime_checker.json     port 8002 - 소수 판별
  models/                       7 model configurations
  patterns/                     14 orchestration patterns (docs)
  templates/                    6 full-inline team templates
  templates_compact/            7 compact templates with $ref
  resolved/                     7 auto-resolved output
  teams/                        Legacy teams (AutoGen Studio export)
  e2e_logs/                     E2E test run logs (md + json)
  registry.json                 Central ID -> file mapping
  ref_resolver.py               $ref resolver engine
  validate_json.py              Validation (98 files)
  a2a_manager.py                A2A agent lifecycle CLI
  e2e_playwright_test.py        Comprehensive E2E test suite
```

## $ref Resolver System

컴팩트 템플릿(`templates_compact/`)은 `$ref`와 `_defaults`를 사용하여 40-50% 더 작다.
`ref_resolver.py`가 이를 full-inline JSON으로 변환.

### 컴팩트 템플릿 예시

```json
{
  "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
  "_defaults": {
    "reflect_on_tool_use": false,
    "tool_call_summary_format": "{result}",
    "model_client": {
      "$ref": "models/claude_sonnet",
      "override": { "config.agent_config": {"profile": "text_only"} }
    }
  },
  "config": {
    "participants": [
      {
        "$ref": "agents/auto_claude_planner",
        "override": {
          "model_client.config.agent_config": {"profile": "reader"}
        }
      },
      { "$ref": "a2a_agents/calculator", "override": {"timeout": 60} }
    ],
    "termination_condition": { "$ref": "terminations/default_or" }
  }
}
```

### Resolution Flow

| Category | $ref Flow |
|----------|-----------|
| `agents/` | Load file -> wrap AssistantAgent -> inject `_defaults` -> apply dot-path overrides |
| `a2a_agents/` | Load file -> pass through (self-contained) -> strip `_source` -> flat overrides only |
| `terminations/` | Load from registry inline -> resolve nested conditions recursively |

### Override Types

- **Flat override**: `"description": "new desc"` - 직접 config 키 덮어쓰기
- **Dot-path override**: `"model_client.config.agent_config": {...}` - 깊은 경로 deep-merge

### Model $ref in _defaults

`_defaults.model_client`도 `$ref`를 지원한다. `resolve_defaults()` 함수가 에이전트 주입 전에
_defaults 내부의 `$ref`를 먼저 resolve한다. 모든 7개 컴팩트 템플릿이 model `$ref`를 사용 (100% DRY).

```json
"_defaults": {
  "model_client": {
    "$ref": "models/claude_sonnet",
    "override": { "config.agent_config": {"profile": "text_only"} }
  }
}
```

Resolution order: `resolve_defaults()` -> model `$ref` resolved -> inject into each agent -> agent-level overrides applied.

### CLI

```bash
python ref_resolver.py <file.json>         # Resolve single -> stdout
python ref_resolver.py --all               # Resolve all -> resolved/
python ref_resolver.py --import            # Resolve + POST to AutoGen Studio
python ref_resolver.py --diff <file.json>  # Structural diff vs templates/
```

## A2A Agent Integration

Google ADK 기반 A2A 에이전트를 first-class JSON 모듈로 통합.
Python script를 수동으로 시작/등록하는 대신, JSON 정의 하나로 관리.

### A2A Agent JSON Schema

```json
{
  "provider": "autogenstudio.a2a.A2AAgent",
  "component_type": "agent",
  "config": {
    "name": "calculator_agent",
    "a2a_server_url": "http://localhost:8006",
    "description": "기본 수학 연산, 피보나치 수열, 팩토리얼 계산",
    "timeout": 300,
    "skills": [
      {"name": "calculate", "description": "수학 표현식 계산"},
      {"name": "fibonacci", "description": "피보나치 수 계산"}
    ]
  },
  "_source": {
    "agent_file": "D:/Data/22_AG/.../calculator_agent/agent.py",
    "port": 8006,
    "framework": "google_adk"
  }
}
```

`_source`는 메타데이터. resolve 시 자동 제거됨.

### a2a_manager.py

```bash
python a2a_manager.py --scan              # agent.py 스캔 -> JSON 생성
python a2a_manager.py --list              # 등록된 에이전트 목록
python a2a_manager.py --check             # Health check (port 응답)
python a2a_manager.py --register          # AutoGen Studio에 등록
python a2a_manager.py --start calculator  # 백그라운드 시작
```

### Port Map

| Agent | Port | Domain |
|-------|------|--------|
| history_helper | 8001 | Education |
| prime_checker | 8002 | Math |
| poetry | 8003 | Literature |
| philosophy | 8004 | Humanities |
| history | 8005 | History |
| calculator | 8006 | Math |
| math | 8007 | Algebra |
| graphics | 8008 | Graphics |
| gpu | 8009 | Computing |
| gui_test | 8120 | Automation |

## Registry

`registry.json` - 모든 컴포넌트의 중앙 레지스트리:

```json
{
  "agents":       { "auto_claude_planner": {"file": "agents/...", "name": "planner_agent"} },
  "models":       { "claude_sonnet": {"file": "models/...", "model": "claude-sonnet-4-5"} },
  "terminations": { "default_or": {"provider": "...OrTermination", "conditions": [...]} },
  "a2a_agents":   { "calculator": {"file": "a2a_agents/...", "port": 8006} },
  "teams":        { "sequential": {"file": "templates/..."} }
}
```

## agent_config (Claude SDK Profile)

`model_client.config.agent_config`로 Claude Agent SDK의 역할별 프로필을 설정:

```json
"agent_config": {
  "profile": "coder",
  "max_turns": 5,
  "permission_mode": "acceptEdits",
  "cwd": "D:\\AC247"
}
```

| Profile | Tools | Use Case |
|---------|-------|----------|
| `text_only` | None (`tools=[]`) | 순수 텍스트 응답 |
| `reader` | Read, Glob, Grep, WebSearch | 읽기 전용 분석 |
| `coder` | Read, Write, Edit, Bash, Glob, Grep | 코드 작성/실행 |
| `full_agent` | All (`tools=None`) | 완전 자율 에이전트 |

| Permission Mode | Behavior |
|-----------------|----------|
| `default` | 사용자 확인 필요 |
| `acceptEdits` | 파일 편집 자동 승인 |
| `plan` | 읽기 전용 (Plan Mode) |

## Team Templates

| Template | Pattern | Agents |
|----------|---------|--------|
| sequential_team | RoundRobin | planner -> coder -> qa_reviewer |
| selector_team | Selector | coordinator + history_expert + science_expert + math_expert |
| handoff_team | Swarm | triage -> support + sales + refund |
| debate_team | Selector | advocate -> critic -> judge |
| reflection_team | RoundRobin | generator <-> critic |
| auto_claude_dev_team | RoundRobin | planner -> coder -> qa_reviewer -> qa_fixer |
| hybrid_calculator_team | RoundRobin | claude_planner + a2a_calculator |

## Validation

```bash
python validate_json.py
# 98 PASS, 0 FAIL, 52 warnings
```

Checks: UTF-8 encoding, JSON parse, required fields, provider whitelist, A2A port consistency,
registry file paths, gallery completeness, DRY violations, $ref resolution.

## E2E Test Suite

`e2e_playwright_test.py` - Playwright + WebSocket 종합 테스트.
모든 에이전트 대화를 **turn별로 상세 기록** (글자수, 토큰, 경과시간).

### Test Coverage

| # | Test | Method | Verifies |
|---|------|--------|----------|
| 1 | ref_resolver --all | subprocess | 7 templates resolve |
| 2 | validate_json.py | subprocess | 98 PASS, 0 FAIL |
| 3 | a2a_manager --list | subprocess | 10 agents listed |
| 4 | A2A Calculator Health | HTTP | .well-known/agent.json |
| 5 | Playwright UI | Playwright | UI loads, screenshots |
| 6 | Hybrid Team (Claude+A2A) | WebSocket | planner <-> calculator |
| 7 | Debate Team | WebSocket | advocate -> critic -> judge |
| 8 | Reflection Team | WebSocket | generator -> critic |
| 9 | Code Generation | WebSocket | 4-agent, file created+runs |

### Latest Results (2026-02-07, Run #195-198)

```
9 PASS, 0 FAIL | Total: 598.3s
```

| Test | Duration | Turns | Detail |
|------|----------|-------|--------|
| Hybrid (Claude+A2A) | 212.8s | 10 | planner: 5t/10860chars, calculator: 4t/2178chars |
| Debate | 165.9s | 4 | advocate(1115c)->critic(2258c)->judge(2260c), TERMINATE |
| Reflection | 100.0s | 3 | generator(10237c)->critic(865c), APPROVED |
| Code Generation | 112.5s | 4 | planner->coder->qa_reviewer, file=354B, `2+3=5 10*5=50 100/4=25.0` |

### Run Tests

```bash
# 1. AutoGen Studio 시작 (port 8081)
# 2. Calculator A2A 시작
python a2a_manager.py --start calculator

# 3. E2E 테스트 실행
python e2e_playwright_test.py
```

Logs: `e2e_logs/e2e_run_YYYYMMDD_HHMMSS.md` (conversation transcript) + `.json` (programmatic).

### Conversation Log Format

각 팀 실행의 전체 대화가 기록됨:

```markdown
### Turn 2: `planner_agent` [16.0s]
- Content: 590 chars | Tokens: in=0, out=0

\```
100의 팩토리얼과 피보나치 수열의 10번째 수를 계산해드리겠습니다.
...
\```
```

## Architecture

```
User
  |
  v
[AutoGen Studio :8081]
  |
  +-- AssistantAgent (Claude SDK)
  |     |-- ClaudeCLIChatCompletionClient
  |     `-- Claude API (OAuth: sk-ant-oat01-*)
  |
  +-- A2AAgent (Google A2A Protocol)
        |-- HTTP POST -> localhost:800X
        `-- Google ADK Agent (Python)

[ref_resolver.py]
  templates_compact/*.json  --->  resolved/*.json
  ($ref + _defaults)              (full inline)
                                      |
                                      v
                              POST /api/teams/
                              AutoGen Studio DB
```

## Pattern -> Provider 매핑

| Pattern | AutoGen Provider | Communication |
|---------|------------------|---------------|
| Sequential | RoundRobinGroupChat | turn-based |
| Selector | SelectorGroupChat | AI-routed |
| Handoff | Swarm | event-driven |
| Magentic | MagenticOneGroupChat | broadcast |
| Debate | SelectorGroupChat | structured turn |
| Reflection | RoundRobinGroupChat | generator-critic loop |

## File Count Summary

| Category | Count |
|----------|-------|
| Agents (Claude) | 23 |
| A2A Agents | 10 |
| Models | 7 |
| Patterns | 14 |
| Templates (full) | 6 |
| Templates (compact) | 7 |
| Resolved | 7 |
| Teams (legacy) | 20+ |
| **Total JSON** | **98** |

## Notes

- AutoGen Studio v0.4.3 on port 8081
- `reflect_on_tool_use: false` + `tool_call_summary_format: "{result}"` required for v2 AssistantAgent
- A2A agents use Google ADK `to_a2a()` wrapper
- Windows cp949: always use `encoding='utf-8'` or `errors='replace'` for subprocess
- OAuth token: `~/.claude/.credentials.json` (sk-ant-oat01-*)
