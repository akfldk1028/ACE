# 02. JSON 모듈화 구조

## 개요

모든 AutoGen 컴포넌트(패턴, 모델, 에이전트, 팀)가 JSON으로 완전 모듈화되어 있습니다.

**총 61개 JSON 파일** → `D:\Data\25_ACE\JSON_MODULES\`

---

## 폴더 구조

```
JSON_MODULES/
├── index.json              # 마스터 인덱스 (패턴 선택 플로우차트)
├── cohub_gallery.json      # 갤러리 정의 (5개 팀 완전체)
│
├── patterns/               # 14개 패턴 정의
│   ├── 01_sequential.json      → RoundRobinGroupChat
│   ├── 02_concurrent.json      → asyncio (병렬)
│   ├── 03_selector.json        → SelectorGroupChat
│   ├── 04_group_chat.json      → SelectorGroupChat
│   ├── 05_handoff.json         → Swarm
│   ├── 06_magentic.json        → MagenticOneGroupChat
│   ├── 07_debate.json          → SelectorGroupChat
│   ├── 08_reflection.json      → RoundRobinGroupChat
│   ├── 09_hierarchical.json    → nested teams
│   ├── 10_mixture_of_agents.json
│   ├── 11_cli_collaboration.json
│   ├── 11_code_execution.json
│   ├── 11_gui_test_team.json
│   └── 12_pseudo_hierarchical.json
│
├── templates/              # 5개 팀 템플릿 (간소화)
│   ├── sequential_team.json
│   ├── selector_team.json
│   ├── handoff_team.json
│   ├── debate_team.json
│   └── reflection_team.json
│
├── models/                 # 7개 모델 정의
│   ├── claude_01_Claude_Opus_4.5_Max_OAuth.json
│   ├── claude_02_Claude_Sonnet_4.5_Max_OAuth.json
│   ├── claude_03_Claude_Haiku_4.5_Max_OAuth.json
│   ├── default_01_OpenAI_GPT_4o_Mini.json
│   ├── default_02_Mistral_7B_Local.json
│   ├── default_03_Anthropic_Claude_3_7.json
│   └── default_04_AzureOpenAI_GPT_4o_mini.json
│
├── agents/                 # 12개 에이전트 정의
│   ├── auto_claude_01_Planner.json
│   ├── auto_claude_02_Coder.json
│   ├── auto_claude_03_QA_Reviewer.json
│   ├── auto_claude_04_QA_Fixer.json
│   ├── auto_claude_05_Insights_Analyst.json
│   ├── auto_claude_06_Deep_Research_Agent.json
│   ├── auto_claude_07_Spec_Writer_Agent.json
│   ├── pattern_01_Advocate_Debate.json
│   ├── pattern_02_Critic_Debate.json
│   ├── pattern_03_Judge_Debate.json
│   ├── pattern_04_Generator_Reflection.json
│   └── pattern_05_Critic_Reflection.json
│
├── teams/                  # 20개 팀 정의
│   ├── cohub_01_Sequential_Team.json
│   ├── cohub_02_Selector_Team.json
│   ├── cohub_03_Handoff_Team.json
│   ├── cohub_04_Debate_Team.json
│   ├── cohub_05_Reflection_Team.json
│   ├── 037_Auto-Claude_Sequential_Pipeline.json  # ★ 메인 파이프라인
│   └── ... (기타)
│
└── providers/              # AutoGen Provider 설정
    └── providers.json      # RoundRobin, Selector, Swarm, Magentic
```

---

## 패턴 ↔ Provider 매핑

| 패턴 | AutoGen Provider | 통신 방식 |
|------|------------------|----------|
| Sequential | RoundRobinGroupChat | turn-based |
| Concurrent | custom (asyncio) | parallel |
| Selector | SelectorGroupChat | request-response |
| Group Chat | SelectorGroupChat | free-form |
| Handoff | Swarm | event-driven |
| Magentic | MagenticOneGroupChat | broadcast |
| Debate | SelectorGroupChat | structured |
| Reflection | RoundRobinGroupChat | generator-critic |
| Hierarchical | nested teams | tree |

---

## 모델 종류

### Claude (Max OAuth) - ClaudeCLIChatCompletionClient
| 모델 | 용도 |
|------|------|
| Opus 4.5 | Complex/Auto 프로필 |
| Sonnet 4.5 | Balanced 프로필 (기본) |
| Haiku 4.5 | Quick Edits 프로필 |

### OpenAI / 기타 - 표준 클라이언트
| 모델 | Provider |
|------|----------|
| GPT-4o Mini | OpenAIChatCompletionClient |
| GPT-4o-mini | AzureOpenAIChatCompletionClient |
| Mistral-7B | Ollama (로컬) |
| Claude-3-7 | AnthropicChatCompletionClient |

---

## JSON 파일 예시

### 에이전트 정의 (pattern_05_Critic_Reflection.json)
```json
{
  "provider": "autogen_agentchat.agents.AssistantAgent",
  "component_type": "agent",
  "version": 1,
  "label": "Critic (Reflection)",
  "description": "품질 검토 및 피드백 에이전트",
  "config": {
    "name": "critic",
    "system_message": "생성된 결과를 검토하고 구체적인 개선점을 제시하세요. 문제가 없으면 APPROVED라고 말하세요."
  }
}
```

### 패턴 정의 구조
```json
{
  "id": "sequential",
  "name": "Sequential Pattern",
  "autogen_implementation": {
    "provider": "autogen_agentchat.teams.RoundRobinGroupChat",
    "team_type": "RoundRobinGroupChat"
  }
}
```

---

## 사용법

1. **패턴 선택**: `patterns/` 폴더에서 적합한 패턴 JSON 선택
2. **에이전트 조합**: `agents/` 폴더에서 필요한 에이전트 선택
3. **모델 지정**: `models/` 폴더에서 사용할 모델 선택
4. **팀 구성**: 위 컴포넌트를 조합하여 팀 JSON 생성
