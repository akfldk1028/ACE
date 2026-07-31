# 03. AutoGen 패턴 상세

## 14개 패턴 개요

AutoGen Studio에서 사용 가능한 멀티-에이전트 패턴입니다.

---

## 1. Sequential (순차) ★ 테스트 완료

**Provider**: `RoundRobinGroupChat`

```
user → agent1 → agent2 → agent3 → ... → result
```

- **통신**: turn-based (순서대로)
- **용도**: 파이프라인 처리, 단계별 작업
- **예시**: insights → research → spec → plan → code → QA

**테스트 결과**: ✅ 작동 확인 (Run #146, 4718 tokens)

---

## 2. Concurrent (병렬)

**Provider**: custom (asyncio)

```
         ┌→ agent1 ─┐
user ────┼→ agent2 ─┼───→ aggregator → result
         └→ agent3 ─┘
```

- **통신**: parallel (동시 실행)
- **용도**: 독립적 작업 병렬 처리
- **예시**: 여러 관점에서 동시 분석

---

## 3. Selector (선택)

**Provider**: `SelectorGroupChat`

```
user → selector_model → 적합한 agent → result
```

- **통신**: request-response
- **용도**: 작업 유형에 따라 적합한 에이전트 선택
- **특징**: model_client가 다음 발언자 선택

---

## 4. Group Chat

**Provider**: `SelectorGroupChat`

```
user ←→ agent1 ←→ agent2 ←→ agent3
         ↑____________↓
```

- **통신**: free-form (자유 대화)
- **용도**: 브레인스토밍, 열린 토론

---

## 5. Handoff (핸드오프)

**Provider**: `Swarm`

```
user → agent1 ──handoff──→ agent2 ──handoff──→ agent3
```

- **통신**: event-driven
- **용도**: 상태 전달이 필요한 워크플로우
- **특징**: 에이전트가 명시적으로 다음 에이전트에게 전달

---

## 6. Magentic

**Provider**: `MagenticOneGroupChat`

```
          orchestrator
         ↙    ↓    ↘
    agent1  agent2  agent3
```

- **통신**: broadcast
- **용도**: 오케스트레이터가 전체 조율

---

## 7. Debate (토론) ★ 테스트 필요

**Provider**: `SelectorGroupChat`

```
advocate ←→ critic ←→ judge
   (찬성)     (반대)    (판정)
```

- **통신**: structured (구조화된 토론)
- **용도**: 의사결정, 장단점 분석
- **에이전트**: Advocate, Critic, Judge

---

## 8. Reflection (반성) ★ 테스트 필요

**Provider**: `RoundRobinGroupChat`

```
generator → critic → generator → critic → ... → APPROVED
```

- **통신**: generator-critic 루프
- **용도**: 품질 개선, 반복 정제
- **종료조건**: critic이 "APPROVED" 출력

---

## 9. Hierarchical (계층)

**Provider**: nested teams

```
        supervisor
       ↙    ↓    ↘
   team1  team2  team3
   ↙ ↘    ↙ ↘    ↙ ↘
  a1 a2  a3 a4  a5 a6
```

- **통신**: tree 구조
- **용도**: 대규모 프로젝트, 팀 단위 작업

---

## Provider 상세

### RoundRobinGroupChat
```json
{
  "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
  "layout": "chain",
  "communicationStyle": "turn-based",
  "requiresModelClient": false
}
```

### SelectorGroupChat
```json
{
  "provider": "autogen_agentchat.teams.SelectorGroupChat",
  "layout": "hub-spoke",
  "communicationStyle": "request-response",
  "requiresModelClient": true  // selector_prompt 또는 model_client 필요
}
```

### Swarm
```json
{
  "provider": "autogen_agentchat.teams.Swarm",
  "layout": "mesh",
  "communicationStyle": "event-driven",
  "requiresModelClient": false
}
```

### MagenticOneGroupChat
```json
{
  "provider": "autogen_agentchat.teams.MagenticOneGroupChat",
  "layout": "tree",
  "communicationStyle": "broadcast",
  "requiresModelClient": true
}
```

---

## 테스트 현황

| 패턴 | 상태 | 비고 |
|------|------|------|
| Sequential | ✅ 완료 | Run #146, insights_agent 응답 확인 |
| Concurrent | ❌ 미완료 | |
| Selector | ❌ 미완료 | |
| Group Chat | ❌ 미완료 | |
| Handoff | ❌ 미완료 | |
| Magentic | ❌ 미완료 | |
| Debate | ❌ 미완료 | 다음 테스트 대상 |
| Reflection | ❌ 미완료 | 다음 테스트 대상 |
| Hierarchical | ❌ 미완료 | |

---

## 테스트 방법

### Playwright MCP 사용
```python
# 1. AutoGen Studio 접속
mcp__playwright__browser_navigate(url="http://localhost:8081/")

# 2. New Session 클릭
mcp__playwright__browser_click(ref="new_session_button")

# 3. 팀 선택 (예: Debate Team)
mcp__playwright__browser_click(ref="team_selector")

# 4. 메시지 입력
mcp__playwright__browser_fill_form(fields=[{
  "name": "message",
  "type": "textbox",
  "ref": "message_input",
  "value": "Python 계산기 CLI 앱 만들어줘"
}])

# 5. 전송
mcp__playwright__browser_click(ref="send_button")
```

### API 직접 호출
```bash
# 세션 목록
curl "http://localhost:8081/api/sessions/?user_id=guestuser@gmail.com"

# 팀 정보
curl "http://localhost:8081/api/teams/37?user_id=guestuser@gmail.com"

# 실행 결과
curl "http://localhost:8081/api/sessions/155/runs?user_id=guestuser@gmail.com"
```
