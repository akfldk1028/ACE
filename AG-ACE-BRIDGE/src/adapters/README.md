# Adapters Module

AG-ACE-BRIDGE의 에이전트 연결 모듈. 4가지 에이전트 시스템에 대한 통일된 인터페이스 제공.

## 파일 구조

```
src/adapters/
├── __init__.py              # 모듈 export (22개 어댑터/팩토리 함수)
├── base.py                  # AgentAdapter 추상 베이스 클래스
├── auto_claude.py           # Auto-Claude SDK 어댑터 (OAuth 인증)
├── ag_autogen.py            # AG Autogen HTTP 어댑터 (A2A Protocol)
├── ag_a2a_adapter.py        # AG A2A Protocol 어댑터 (Google ADK)
├── ag_law_domain.py         # AG Law Domain HTTP 어댑터 (FastAPI)
├── autogen_studio_adapter.py # AutoGen Studio 워크플로우 어댑터 ★ 신규
└── README.md                # 이 파일
```

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentAdapter (ABC)                      │
│  - execute(task, context) -> Result                          │
│  - health_check() -> bool                                    │
│  - get_capabilities() -> List[str]                           │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ AutoClaudeAdapter│  │ AGAutogenAdapter │  │AGLawDomainAdapter│
│  (Claude SDK)    │  │  (HTTP/A2A)      │  │  (HTTP/FastAPI)  │
│                  │  │                  │  │                  │
│ - OAuth Token    │  │ - JSON-RPC 2.0   │  │ - REST API       │
│ - ClaudeSDKClient│  │ - A2A Protocol   │  │ - Domain-specific│
│ - Graphiti Memory│  │                  │  │   parameters     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   Claude Max           localhost:8000       localhost:8001
   (계정 기반)          (AG Autogen)        (AG Law Domain)
```

## 주요 컴포넌트

### base.py - 추상 베이스 클래스

```python
class AgentAdapter(ABC):
    """모든 어댑터가 구현해야 하는 인터페이스"""

    @abstractmethod
    async def execute(self, task: Task, context: Dict) -> Result:
        """태스크 실행"""

    @abstractmethod
    async def health_check(self) -> bool:
        """에이전트 상태 확인"""

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """에이전트 능력 목록"""
```

### auto_claude.py - Auto-Claude SDK 어댑터

**인증**: Claude Max 계정 기반 OAuth (API 키 X)

```python
# OAuth 토큰 자동 검색 위치:
# Windows: %USERPROFILE%\.claude\.credentials.json
# macOS: ~/Library/Application Support/Claude/.credentials.json
# Linux: ~/.config/claude/.credentials.json

adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)
await adapter.initialize()  # OAuth 토큰 검증

result = await adapter.execute(task, context)
```

**에이전트별 역할 프롬프트**:
| 역할 | 프롬프트 |
|------|----------|
| planner | 프로젝트 구조, 의존성, 구현 계획 생성 |
| coder | 코드 작성, 테스트, 디버깅 |
| qa_reviewer | 코드 리뷰, 버그 탐지, 개선 제안 |
| qa_fixer | QA 이슈 수정, 리팩토링 |

### ag_autogen.py - AG Autogen HTTP 어댑터

**프로토콜**: A2A (JSON-RPC 2.0)

```python
# A2A 요청 포맷
{
    "jsonrpc": "2.0",
    "method": "execute",
    "params": {
        "task_id": "...",
        "task_type": "research",
        "description": "...",
        "context": {...}
    },
    "id": "task-id"
}
```

### ag_law_domain.py - AG Law Domain HTTP 어댑터

**특화 파라미터**:
| 에이전트 | 추가 파라미터 |
|----------|---------------|
| case_analyzer | analysis_type, jurisdiction |
| legal_researcher | search_scope, date_range |
| risk_assessor | risk_categories, severity_threshold |
| compliance_checker | regulations, check_depth |
| document_drafter | document_type, template_id |

## 14개 에이전트 전체 목록

### Auto-Claude (4개) - Claude SDK
| AgentType | 팩토리 함수 | 기능 |
|-----------|-------------|------|
| `AUTO_CLAUDE_PLANNER` | `create_planner_adapter()` | 프로젝트 계획 |
| `AUTO_CLAUDE_CODER` | `create_coder_adapter()` | 코드 작성 |
| `AUTO_CLAUDE_QA_REVIEWER` | `create_qa_reviewer_adapter()` | QA 검토 |
| `AUTO_CLAUDE_QA_FIXER` | `create_qa_fixer_adapter()` | QA 수정 |

### AG Autogen (5개) - HTTP/A2A
| AgentType | 팩토리 함수 | 기능 |
|-----------|-------------|------|
| `AG_RESEARCH` | `create_research_adapter()` | 정보 수집 |
| `AG_ANALYST` | `create_analyst_adapter()` | 데이터 분석 |
| `AG_WRITER` | `create_writer_adapter()` | 문서 작성 |
| `AG_REVIEWER` | `create_reviewer_adapter()` | 리뷰 피드백 |
| `AG_COORDINATOR` | `create_coordinator_adapter()` | 작업 조율 |

### AG Law Domain (5개) - HTTP/FastAPI
| AgentType | 팩토리 함수 | 기능 |
|-----------|-------------|------|
| `AG_CASE_ANALYZER` | `create_case_analyzer_adapter()` | 판례 분석 |
| `AG_LEGAL_RESEARCHER` | `create_legal_researcher_adapter()` | 법률 조사 |
| `AG_RISK_ASSESSOR` | `create_risk_assessor_adapter()` | 리스크 평가 |
| `AG_COMPLIANCE_CHECKER` | `create_compliance_checker_adapter()` | 컴플라이언스 |
| `AG_DOCUMENT_DRAFTER` | `create_document_drafter_adapter()` | 문서 초안 |

### AG A2A Protocol (5개) - Google ADK ★ 신규
| A2AAgentType | Port | 팩토리 함수 | 기능 |
|--------------|------|-------------|------|
| `POETRY` | 8003 | `create_poetry_adapter()` | 시/문학 분석 |
| `PHILOSOPHY` | 8004 | `create_philosophy_adapter()` | 철학적 사고 |
| `HISTORY` | 8005 | `create_history_adapter()` | 역사적 맥락 |
| `CALCULATOR` | 8006 | `create_calculator_adapter()` | 수학 계산 |
| `GUI_TEST` | 8120 | `create_gui_test_adapter()` | GUI 자동화 |

#### A2A 에이전트 서버 시작
```powershell
# 각 터미널에서 실행 (D:\Data\25_ACE\AG\autogen_a2a_kit\a2a_demo\)
cd poetry_agent && python agent.py       # port 8003
cd philosophy_agent && python agent.py   # port 8004
cd history_agent && python agent.py      # port 8005
cd calculator_agent && python agent.py   # port 8006
```

#### A2A 사용 예시
```python
from src.adapters import (
    AGA2AAdapter,
    A2AAgentType,
    A2AAdapterManager,
    create_calculator_adapter,
)

# 단일 에이전트 사용
adapter = create_calculator_adapter(enable_shared_memory=True)
await adapter.initialize()
result = await adapter.execute(task, context)

# 전체 매니저로 관리
manager = A2AAdapterManager(enable_shared_memory=True)
await manager.initialize_all()
status = await manager.health_check_all()
# {A2AAgentType.CALCULATOR: True, A2AAgentType.POETRY: False, ...}
```

### AutoGen Studio (1개) - 워크플로우 실행 ★ 신규

AutoGen Studio에서 설계한 워크플로우를 실행합니다.

| 어댑터 | 모드 | 기능 |
|--------|------|------|
| `AutogenStudioAdapter` | Direct/HTTP | 워크플로우 실행, 팀 조율 |

#### 실행 모드
- **Direct Mode**: autogenstudio 패키지 직접 호출 (권장)
- **HTTP Mode**: AutoGen Studio 서버 API 호출 (포트 8081)

#### AutoGen Studio 서버 시작
```powershell
# autogenstudio CLI로 실행
autogenstudio ui --port 8081

# 또는 Python에서
python -c "from autogenstudio.cli import app; app()" ui --port 8081
```

#### 사용 예시
```python
from src.adapters import AutogenStudioAdapter, execute_pattern_with_autogen

# 어댑터 직접 사용
adapter = AutogenStudioAdapter(
    studio_url="http://localhost:8081",
    use_direct=True,  # Direct mode 사용
    enable_shared_memory=True,
)
await adapter.initialize()

workflow_data = {
    "name": "calculator_workflow",
    "nodes": [
        {"id": "planner", "agent": "AUTO_CLAUDE_PLANNER"},
        {"id": "coder", "agent": "AUTO_CLAUDE_CODER", "depends_on": ["planner"]},
    ],
}
result = await adapter.execute_workflow(workflow_data, "계산기 앱 개발")

# 편의 함수 사용
result = await execute_pattern_with_autogen(
    pattern_data=workflow_data,
    task_description="계산기 앱 개발",
)
```

## 사용 예시

```python
from src.adapters import (
    AutoClaudeAdapter,
    AGAutogenAdapter,
    AGLawDomainAdapter,
    create_coder_adapter,
)
from src.utils import Task, TaskType, AgentType

# 방법 1: 클래스 직접 사용
adapter = AutoClaudeAdapter(AgentType.AUTO_CLAUDE_CODER)
await adapter.initialize()

task = Task(type=TaskType.CODE, description="로그인 기능 구현")
result = await adapter.execute(task, {"project": "my-app"})

await adapter.shutdown()

# 방법 2: 팩토리 함수 사용
coder = create_coder_adapter()
await coder.initialize()
```

## 설정 (config.py)

```python
# AG 연결 설정
ag_autogen_url: str = "http://localhost:8000"
ag_law_domain_url: str = "http://localhost:8001"
adapter_timeout: float = 120.0  # HTTP 타임아웃 (초)
```

## 의존성

- `claude-agent-sdk>=0.1.19` - Auto-Claude SDK
- `httpx>=0.25.0` - HTTP 클라이언트 (AG 어댑터)

## 관련 모듈

- `src/utils/models.py` - AgentType, Task, Result 정의
- `src/registry/` - 에이전트 레지스트리 및 선택
- `src/coordinator/` - 오케스트레이터
