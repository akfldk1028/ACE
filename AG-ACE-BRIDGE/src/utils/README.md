# Utils Module

유틸리티 모듈. 설정 관리, 데이터 모델, 로깅을 담당합니다.

## 구조

```
utils/
├── __init__.py
├── config.py      # 설정 관리 (Pydantic Settings)
├── models.py      # 데이터 모델 (Pydantic)
└── logger.py      # 구조화된 로깅
```

## 핵심 컴포넌트

### config.py - 설정 관리

```python
class Settings(BaseSettings):
    """
    환경 변수 기반 설정
    .env 파일 자동 로드
    """

    # Bridge Settings
    bridge_port: int = 8080
    bridge_log_level: str = "INFO"

    # Auto-Claude
    auto_claude_path: str = "D:/Data/25_ACE/Auto-Claude/apps/backend"
    graphiti_enabled: bool = True
    anthropic_api_key: Optional[str] = None

    # AG Connection
    ag_autogen_url: str = "http://localhost:8000"
    ag_law_domain_url: str = "http://localhost:8001"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: Optional[str] = None

    # Task Queue
    queue_db_path: str = "./data/tasks.db"
    queue_max_retries: int = 3

    # Pipeline
    max_qa_iterations: int = 5
    default_priority: str = "medium"

    class Config:
        env_file = ".env"
```

### models.py - 데이터 모델

주요 모델들:

```python
# Task - 작업 정의
class Task(BaseModel):
    id: str
    type: TaskType  # RESEARCH, SPEC, CODE, QA, etc.
    description: str
    priority: Priority  # HIGH, MEDIUM, LOW
    context: dict
    requirements: List[str]
    needs_research: bool = False
    domain_validation: bool = False

# Result - 실행 결과
class Result(BaseModel):
    task_id: str
    status: ResultStatus  # SUCCESS, FAILED, NEEDS_RETRY
    output: Any
    next_tasks: List[Task] = []
    insights: List[str] = []

# Pipeline - 실행 계획
class Pipeline(BaseModel):
    id: str
    task_id: str
    stages: List[Stage]
    current_stage_index: int = 0
    accumulated_context: dict = {}

# Stage - 파이프라인 스테이지
class Stage(BaseModel):
    id: str
    agent: AgentType
    stage_type: StageType  # SEQUENTIAL, PARALLEL, CRITIC_LOOP
    timeout_seconds: int = 300
    critic_loop: bool = False
    max_iterations: int = 5

# AgentCapability - 에이전트 기능
class AgentCapability(BaseModel):
    agent: AgentType
    capabilities: List[str]
    description: str
    is_available: bool = True
```

### Enum 정의

```python
class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskType(str, Enum):
    RESEARCH = "research"
    SPEC = "spec"
    PLAN = "plan"
    CODE = "code"
    QA = "qa"
    FIX = "fix"
    VALIDATE = "validate"
    MERGE = "merge"

class ResultStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_RETRY = "needs_retry"

class AgentType(str, Enum):
    # Auto-Claude
    AUTO_CLAUDE_PLANNER = "auto_claude.planner"
    AUTO_CLAUDE_CODER = "auto_claude.coder"
    AUTO_CLAUDE_QA_REVIEWER = "auto_claude.qa_reviewer"
    AUTO_CLAUDE_QA_FIXER = "auto_claude.qa_fixer"
    # AG autogen
    AG_RESEARCH = "ag.research"
    AG_ANALYST = "ag.analyst"
    # ... etc.
```

### logger.py - 구조화된 로깅

```python
import structlog

def get_logger(name: str):
    """구조화된 로거 생성"""
    return structlog.get_logger(name)

# 사용
logger = get_logger("orchestrator")
logger.info("task_started", task_id=task.id, type=task.type)
```

## 사용법

```python
from src.utils import (
    get_settings,
    Task, Result, Pipeline, Stage,
    Priority, TaskType, AgentType
)

# 설정
settings = get_settings()
print(settings.auto_claude_path)

# Task 생성
task = Task(
    type=TaskType.CODE,
    description="Implement user auth",
    priority=Priority.HIGH,
    requirements=["implementation", "security"]
)

# Result 생성
result = Result(
    task_id=task.id,
    status=ResultStatus.SUCCESS,
    output={"files_changed": 5}
)
```

## 관련 파일

- `.env.example`: 환경 변수 템플릿
- `pyproject.toml`: 프로젝트 설정
