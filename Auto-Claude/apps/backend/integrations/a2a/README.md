# A2A Integration - AG Multi-Agent System

AutoGen Studio의 A2A(Agent-to-Agent) 에이전트와 Auto-Claude를 연동합니다.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Auto-Claude + AG Integration                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐                        ┌─────────────────┐         │
│  │   Auto-Claude   │                        │   AG A2A Agents │         │
│  │   Coder Agent   │                        │                 │         │
│  │                 │  ───► A2A Protocol ───►│  poetry  (8003) │         │
│  │  "시 작성해줘"  │                        │  math    (8007) │         │
│  │                 │  ◄─── Response ◄──────│  gpu     (8009) │         │
│  └─────────────────┘                        │  ...            │         │
│          │                                  └─────────────────┘         │
│          │                                          ↑                   │
│          ▼                                          │                   │
│  ┌─────────────────┐                        ┌───────┴───────┐          │
│  │ A2A Discovery   │────── Registry API ───►│ AutoGen Studio │          │
│  │ (discovery.py)  │                        │    (8081)     │          │
│  └─────────────────┘                        └───────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. `client.py` - A2A Client
A2A 프로토콜로 에이전트와 직접 통신합니다.

```python
from integrations.a2a import A2AClient

client = A2AClient("http://localhost:8003")  # poetry_agent

# 에이전트 호출
result = await client.send_message("봄에 대한 시를 작성해주세요")
print(result["text"])  # 시 출력
```

### 2. `discovery.py` - Agent Discovery
AutoGen Studio 또는 폴더 스캔으로 에이전트를 자동 발견합니다.

```python
from integrations.a2a import A2ADiscovery

discovery = A2ADiscovery(
    autogen_studio_url="http://localhost:8081",
    a2a_demo_path="D:/Data/25_ACE/AG/autogen_a2a_kit/a2a_demo"
)

# 에이전트 발견
agents = await discovery.discover_all()
for agent in agents:
    print(f"{agent.name}: {agent.url} - {agent.description}")

# 상태 확인
await discovery.check_all_status(agents)
online_agents = discovery.get_online_agents()
```

### 3. `tools.py` - MCP Tools
Auto-Claude 에이전트가 사용할 A2A 도구입니다.

```python
from integrations.a2a.tools import list_a2a_agents, call_agent

# 사용 가능한 에이전트 목록
agents = await list_a2a_agents()

# 에이전트 호출
result = await call_agent("math_agent", "피보나치 수열 10번째 값은?")
```

## Available Agents

| Agent | Port | Description |
|-------|------|-------------|
| poetry_agent | 8003 | 시/문학 생성 |
| philosophy_agent | 8004 | 철학적 분석 |
| history_agent | 8005 | 역사 정보 |
| calculator_agent | 8006 | 수학 계산 |
| math_agent | 8007 | 수학 문제 해결 |
| graphics_agent | 8008 | 그래픽 처리 |
| gpu_agent | 8009 | GPU 연산 |
| gui_test_agent | 8120 | GUI 자동화 |

## Usage Flow

1. **Auto-Claude UI 설정**
   - Settings → Integrations → A2A Agent Integration
   - Enable A2A Agents 활성화
   - AutoGen Studio URL 또는 A2A Demo Path 설정

2. **에이전트 서버 시작 (AG)**
   ```bash
   cd D:/Data/25_ACE/AG/autogen_a2a_kit
   start_all_agents.bat
   # 또는 개별 에이전트:
   cd a2a_demo/poetry_agent && python agent.py
   ```

3. **Auto-Claude 코더가 A2A 에이전트 호출**
   - 코더 에이전트가 전문 작업 필요시 자동으로 A2A 에이전트 호출
   - 예: 시 작성 → poetry_agent, GPU 연산 → gpu_agent

## Environment Variables

```bash
# .env
A2A_ENABLED=true
A2A_AUTOGEN_STUDIO_URL=http://localhost:8081
A2A_DEMO_PATH=D:/Data/25_ACE/AG/autogen_a2a_kit/a2a_demo
A2A_AUTO_DISCOVERY=true
```

## A2A Protocol

A2A(Agent-to-Agent)는 Google이 정의한 에이전트 간 통신 프로토콜입니다.

**Agent Card** (/.well-known/agent.json):
```json
{
  "name": "poetry_agent",
  "description": "시/문학 생성 에이전트",
  "skills": [
    {"name": "write_poem", "description": "시 작성"}
  ]
}
```

**Message Send** (JSONRPC 2.0):
```json
{
  "jsonrpc": "2.0",
  "id": "uuid",
  "method": "message/send",
  "params": {
    "message": {
      "messageId": "uuid",
      "role": "user",
      "parts": [{"type": "text", "text": "봄에 대한 시를 작성해주세요"}]
    }
  }
}
```

## Related Projects

- [AG](../../AG/) - Multi-Agent System Hub
- [autogen_a2a_kit](../../AG/autogen_a2a_kit/) - AutoGen + A2A Integration
- [a2a_demo](../../AG/autogen_a2a_kit/a2a_demo/) - A2A Demo Agents
