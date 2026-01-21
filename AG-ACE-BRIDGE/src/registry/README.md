# Registry Module

에이전트 레지스트리 모듈. 14개 에이전트의 등록, 상태 추적, 기능 기반 선택을 담당.

## 파일 구조

```
src/registry/
├── __init__.py          # 모듈 export
├── agent_registry.py    # AgentRegistry, AgentStatus
├── capabilities.py      # 14개 에이전트 능력 정의
└── README.md            # 이 파일
```

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AgentRegistry                                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │
│  │ _capabilities │  │  _statuses    │  │  _adapters    │           │
│  │ (정적 능력)   │  │ (런타임상태) │  │ (어댑터참조) │           │
│  └───────────────┘  └───────────────┘  └───────────────┘           │
│                            │                                        │
│         ┌──────────────────┼──────────────────┐                    │
│         ▼                  ▼                  ▼                    │
│   select_agents()    health_check()    record_success()           │
│   (태스크→에이전트)  (상태 모니터링)   (성능 기록)                 │
└─────────────────────────────────────────────────────────────────────┘
```

## 주요 컴포넌트

### capabilities.py - 에이전트 능력 정의

**14개 에이전트의 능력을 정적으로 정의**

```python
@dataclass
class AgentCapabilities:
    agent_type: AgentType           # 에이전트 타입
    name: str                       # 표시 이름
    capabilities: List[Capability]  # 능력 목록
    supported_task_types: List[TaskType]  # 지원 태스크
    is_autonomous: bool             # 24/7 자율 실행 가능
    adapter_type: str               # "auto_claude", "ag_http", "ag_law"
    priority_boost: int             # 우선순위 가산점

@dataclass
class Capability:
    name: str                # 능력 이름 (e.g., "implementation")
    description: str         # 설명
    keywords: List[str]      # 매칭 키워드 (e.g., ["code", "implement"])
```

**전역 레지스트리**
```python
ALL_AGENT_CAPABILITIES: Dict[AgentType, AgentCapabilities] = {
    # 14개 에이전트 능력 정의
}
```

### agent_registry.py - 런타임 레지스트리

**AgentStatus - 런타임 상태**
```python
@dataclass
class AgentStatus:
    agent_type: AgentType
    is_available: bool = True       # 사용 가능 여부
    is_healthy: bool = True         # 건강 상태
    current_task_id: Optional[str]  # 현재 실행 중인 태스크
    consecutive_failures: int = 0   # 연속 실패 횟수
    total_tasks_completed: int = 0  # 총 완료 태스크
    avg_response_time_ms: float     # 평균 응답 시간
```

**AgentRegistry - 메인 클래스**
```python
class AgentRegistry:
    def initialize(self):
        """14개 에이전트 초기화"""

    def select_agents(self, task, limit=3) -> List[AgentType]:
        """태스크에 맞는 에이전트 선택 (점수 기반)"""

    def record_success(self, agent_type, response_time_ms):
        """성공 기록 (EMA로 평균 응답시간 갱신)"""

    def record_failure(self, agent_type):
        """실패 기록 (3회 연속 실패 시 unhealthy)"""

    async def health_check_all(self) -> Dict[AgentType, bool]:
        """전체 에이전트 상태 확인"""
```

## 에이전트 선택 알고리즘

```python
def select_agents(task, limit=3) -> List[AgentType]:
    # 1. TaskType으로 후보 필터링
    candidates = find_best_agents(task.type, task.requirements)

    # 2. 각 후보 점수 계산
    for candidate in candidates:
        score = capability_match_score      # 요구사항 매칭 (0.0~1.0)
        score += availability_bonus         # 가용성 보너스 (+0.3)
        score += success_rate * 0.2         # 성공률 보너스
        score -= failures * 0.1             # 연속 실패 패널티

    # 3. 점수순 정렬 후 상위 N개 반환
    return sorted(scored)[:limit]
```

## 14개 에이전트 전체 목록

### Auto-Claude (4개) - 자율 코딩
| AgentType | 이름 | 주요 능력 | TaskType |
|-----------|------|-----------|----------|
| `AUTO_CLAUDE_PLANNER` | Planner | planning, task-decomposition | SPEC, PLAN |
| `AUTO_CLAUDE_CODER` | Coder | implementation, refactoring | CODE, FIX |
| `AUTO_CLAUDE_QA_REVIEWER` | QA Reviewer | code-review, testing | QA, VALIDATE |
| `AUTO_CLAUDE_QA_FIXER` | QA Fixer | debugging, issue-resolution | FIX |

### AG Autogen (5개) - 범용
| AgentType | 이름 | 주요 능력 | TaskType |
|-----------|------|-----------|----------|
| `AG_RESEARCH` | Research | web-search, info-gathering | RESEARCH |
| `AG_ANALYST` | Analyst | data-analysis, pattern-detection | RESEARCH, VALIDATE |
| `AG_WRITER` | Writer | documentation, content | SPEC, CUSTOM |
| `AG_REVIEWER` | Reviewer | feedback, quality-assessment | QA, VALIDATE |
| `AG_COORDINATOR` | Coordinator | orchestration, task-routing | PLAN, CUSTOM |

### AG Law Domain (5개) - 법률 특화
| AgentType | 이름 | 주요 능력 | TaskType |
|-----------|------|-----------|----------|
| `AG_CASE_ANALYZER` | Case Analyzer | case-law, precedent | RESEARCH, VALIDATE |
| `AG_LEGAL_RESEARCHER` | Legal Researcher | statute-search, regulation | RESEARCH |
| `AG_RISK_ASSESSOR` | Risk Assessor | risk-evaluation, liability | VALIDATE, RESEARCH |
| `AG_COMPLIANCE_CHECKER` | Compliance Checker | compliance, audit | VALIDATE, QA |
| `AG_DOCUMENT_DRAFTER` | Document Drafter | legal-docs, contracts | SPEC, CUSTOM |

## 사용 예시

```python
from src.registry import get_registry, AgentRegistry
from src.utils import Task, TaskType

# 싱글톤 레지스트리 가져오기
registry = get_registry()

# 태스크에 맞는 에이전트 선택
task = Task(
    type=TaskType.CODE,
    description="로그인 기능 구현",
    requirements=["implementation", "authentication"]
)
agents = registry.select_agents(task, limit=2)
# → [AUTO_CLAUDE_CODER, ...]

# 단일 최적 에이전트
best = registry.select_single_agent(task)
# → AUTO_CLAUDE_CODER

# 특정 능력으로 검색
coders = registry.get_agents_by_capability("implementation")
# → [AUTO_CLAUDE_CODER, AUTO_CLAUDE_QA_FIXER]

# 실행 결과 기록
registry.record_success(AgentType.AUTO_CLAUDE_CODER, response_time_ms=1500)
registry.record_failure(AgentType.AG_RESEARCH)

# 통계 조회
stats = registry.get_stats()
# → {"total_agents": 14, "available_agents": 12, ...}
```

## 헬퍼 함수

```python
from src.registry import (
    get_capabilities,       # AgentType → AgentCapabilities
    get_agents_by_task_type, # TaskType → List[AgentCapabilities]
    get_agents_by_adapter,   # adapter_type → List[AgentCapabilities]
    find_best_agents,        # (TaskType, requirements) → scored agents
)

# TaskType으로 후보 찾기
candidates = get_agents_by_task_type(TaskType.CODE)
# → [AUTO_CLAUDE_CODER, AUTO_CLAUDE_QA_FIXER]

# 어댑터 타입으로 그룹
auto_claude_agents = get_agents_by_adapter("auto_claude")
# → [PLANNER, CODER, QA_REVIEWER, QA_FIXER]
```

## 관련 모듈

- `src/utils/models.py` - AgentType, TaskType 정의
- `src/adapters/` - 실제 에이전트 연결
- `src/coordinator/agent_selector.py` - 고급 선택 로직
