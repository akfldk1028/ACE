# Registry Module

에이전트 레지스트리 모듈. 17개 에이전트의 등록, 탐색, 기능 매칭을 담당합니다.

## 구조

```
registry/
├── __init__.py
├── agent_registry.py   # 에이전트 등록/탐색
└── capabilities.py     # 기능 정의
```

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT REGISTRY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  AUTO-CLAUDE (4 agents)                                         │
│  ├── planner     [planning, subtask-decomposition]             │
│  ├── coder       [implementation, 24/7-autonomous]             │
│  ├── qa_reviewer [testing, e2e, validation]                    │
│  └── qa_fixer    [debugging, issue-resolution]                 │
│                                                                 │
│  AG AUTOGEN (8 agents)                                         │
│  ├── research    [information-gathering, web-search]           │
│  ├── analyst     [data-analysis, pattern-detection]            │
│  ├── writer      [documentation, content-creation]             │
│  └── ...                                                       │
│                                                                 │
│  AG LAW-DOMAIN (5 agents)                                      │
│  ├── case_analyzer    [case-law, precedent]                    │
│  ├── legal_researcher [statute, regulation]                    │
│  └── ...                                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 핵심 컴포넌트

### agent_registry.py - 에이전트 레지스트리

```python
class AgentRegistry:
    """
    에이전트 등록 및 탐색
    - Capability-based matching
    - Availability tracking
    - Load balancing
    """

    def __init__(self):
        self._agents: Dict[AgentType, AgentCapability] = {}
        self._register_default_agents()

    def register(self, capability: AgentCapability) -> None:
        """에이전트 등록"""
        self._agents[capability.agent] = capability

    def find_by_capabilities(self, required: List[str]) -> List[AgentType]:
        """
        요구 기능에 맞는 에이전트 찾기

        Example:
            required = ["legal-research", "implementation"]
            returns = [AG_LEGAL_RESEARCHER, AUTO_CLAUDE_CODER]
        """
        matched = []
        for agent, cap in self._agents.items():
            if any(req in cap.capabilities for req in required):
                matched.append(agent)
        return matched

    def get_available(self) -> List[AgentType]:
        """사용 가능한 에이전트 목록"""
        return [a for a, c in self._agents.items() if c.is_available]
```

### capabilities.py - 기능 정의

```python
# 기본 기능 정의
CAPABILITIES = {
    # Auto-Claude
    AgentType.AUTO_CLAUDE_PLANNER: [
        "planning", "subtask-decomposition", "implementation-plan"
    ],
    AgentType.AUTO_CLAUDE_CODER: [
        "implementation", "coding", "24/7-autonomous", "bug-fix"
    ],
    AgentType.AUTO_CLAUDE_QA_REVIEWER: [
        "testing", "e2e", "validation", "quality-assurance"
    ],
    AgentType.AUTO_CLAUDE_QA_FIXER: [
        "debugging", "issue-resolution", "fix"
    ],

    # AG autogen_a2a_kit
    AgentType.AG_RESEARCH: [
        "information-gathering", "web-search", "research"
    ],
    AgentType.AG_ANALYST: [
        "data-analysis", "pattern-detection", "analytics"
    ],
    # ...

    # AG law-domain
    AgentType.AG_LEGAL_RESEARCHER: [
        "legal-research", "statute-search", "regulation"
    ],
    AgentType.AG_COMPLIANCE_CHECKER: [
        "compliance", "regulation-check", "legal-validation"
    ],
    # ...
}
```

## 에이전트 선택 로직

### Capability Matching

```python
# Task: "법률 조사 후 계약서 생성 기능 구현"
task.requirements = ["legal-research", "implementation"]

# Registry finds:
# 1. AG_LEGAL_RESEARCHER (legal-research)
# 2. AUTO_CLAUDE_CODER (implementation)

agents = registry.find_by_capabilities(task.requirements)
# → [AG_LEGAL_RESEARCHER, AUTO_CLAUDE_CODER]
```

### Pipeline Building with Registry

```python
def build_pipeline(task: Task) -> Pipeline:
    agents = registry.find_by_capabilities(task.requirements)

    stages = []
    for agent in agents:
        stages.append(Stage(agent=agent))

    return Pipeline(stages=stages)
```

## 사용법

```python
from src.registry import AgentRegistry

registry = AgentRegistry()

# 기능으로 에이전트 찾기
agents = registry.find_by_capabilities(["research", "implementation"])

# 특정 에이전트 정보
info = registry.get(AgentType.AUTO_CLAUDE_CODER)
print(info.capabilities)  # ["implementation", "coding", ...]

# 사용 가능한 에이전트
available = registry.get_available()
```

## 전체 에이전트 목록 (17개)

| 시스템 | 에이전트 | 주요 기능 |
|--------|----------|-----------|
| Auto-Claude | planner | planning, subtask-decomposition |
| Auto-Claude | coder | implementation, 24/7-autonomous |
| Auto-Claude | qa_reviewer | testing, e2e, validation |
| Auto-Claude | qa_fixer | debugging, issue-resolution |
| AG Autogen | research | information-gathering, web-search |
| AG Autogen | analyst | data-analysis, pattern-detection |
| AG Autogen | writer | documentation, content-creation |
| AG Autogen | reviewer | feedback, quality-assessment |
| AG Autogen | coordinator | orchestration, task-routing |
| AG Autogen | ... | (3개 더) |
| AG Law | case_analyzer | case-law, precedent-analysis |
| AG Law | legal_researcher | statute-search, regulation |
| AG Law | risk_assessor | risk-evaluation, liability |
| AG Law | compliance_checker | compliance, regulation-check |
| AG Law | document_drafter | legal-docs, contracts |

## 관련 파일

- `src/utils/models.py`: AgentType, AgentCapability 모델
- `src/adapters/`: 에이전트 어댑터
- `src/coordinator/agent_selector.py`: 선택 로직
