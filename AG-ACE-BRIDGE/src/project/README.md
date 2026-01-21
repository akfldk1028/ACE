# Project Module

AG-ACE-BRIDGE의 프로젝트 제출 및 관리 모듈. 24/7 AI Factory의 프로젝트 정의, 감시, CLI를 담당.

## 파일 구조

```
src/project/
├── __init__.py    # 모듈 export
├── spec.py        # 프로젝트 스펙 모델 (Pydantic)
├── watcher.py     # 폴더 감시 (watchdog)
├── cli.py         # CLI 명령어
└── README.md      # 이 파일
```

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                        24/7 AI Factory                               │
│                                                                      │
│   projects/                                                          │
│   ├── queue/      ← ProjectWatcher 감시                              │
│   │   └── my-api.yaml  ─┐                                           │
│   ├── completed/        │                                           │
│   └── failed/           │                                           │
│                         ▼                                            │
│   ┌─────────────────────────────────┐                               │
│   │        ProjectFileHandler       │                               │
│   │   - YAML/JSON 파싱              │                               │
│   │   - ProjectSpec 검증            │                               │
│   │   - 마스터 태스크 생성          │                               │
│   └─────────────────────────────────┘                               │
│                         │                                            │
│                         ▼                                            │
│   ┌─────────────────────────────────┐                               │
│   │          TaskQueue              │                               │
│   │   (SQLite)                      │                               │
│   └─────────────────────────────────┘                               │
│                         │                                            │
│                         ▼                                            │
│   ┌─────────────────────────────────┐                               │
│   │        Orchestrator             │                               │
│   │   (24/7 Main Loop)              │                               │
│   └─────────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

## 주요 컴포넌트

### spec.py - 프로젝트 스펙 모델

**핵심 Enum**
```python
class ProjectPhase(str, Enum):
    """프로젝트 라이프사이클 단계"""
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"

class ProjectStatus(str, Enum):
    """프로젝트 실행 상태"""
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
```

**ProjectSpec - 메인 모델**
```python
class ProjectSpec(BaseModel):
    """
    24/7 AI Factory 프로젝트 스펙.

    YAML/JSON 파일로 projects/queue/ 에 드랍하면 자동 실행.
    """

    # Identity
    id: str                    # 고유 ID (자동 생성)
    name: str                  # 프로젝트 이름
    description: str           # 프로젝트 설명

    # Goals & Requirements
    goals: List[str]           # 목표 목록
    requirements: ProjectRequirements  # 요구사항

    # Technical
    tech_stack: List[str]      # 기술 스택
    output_path: str           # 출력 경로

    # Agent Configuration
    agents: AgentConfig        # 에이전트 설정

    # Pipeline Configuration
    pipeline: PipelineConfig   # 파이프라인 설정

    # Execution
    priority: str              # high, medium, low
    auto_start: bool           # 자동 시작 여부

    # State (시스템 관리)
    status: ProjectStatus
    phase: ProjectPhase
    progress_percent: int
    current_task: Optional[str]
    completed_tasks: List[str]
    artifacts: List[str]       # 생성된 산출물
    errors: List[str]          # 에러 메시지
```

**AgentConfig - 에이전트 설정**
```python
class AgentConfig(BaseModel):
    use_auto_claude: bool = True   # Auto-Claude 사용
    use_ag_autogen: bool = True    # AG Autogen 사용
    use_ag_law: bool = False       # AG Law Domain 사용
    preferred_agents: List[str]    # 선호 에이전트
    excluded_agents: List[str]     # 제외 에이전트
```

**PipelineConfig - 파이프라인 설정**
```python
class PipelineConfig(BaseModel):
    pattern: str = "auto"          # auto, sequential, parallel, critic_loop
    max_iterations: int = 5        # 최대 반복
    parallel_limit: int = 3        # 병렬 에이전트 제한
    timeout_minutes: int = 60      # 타임아웃
```

**헬퍼 함수**
```python
def load_project_spec(file_path: Path) -> ProjectSpec:
    """YAML/JSON 파일에서 스펙 로드"""

def save_project_spec(spec: ProjectSpec, file_path: Path) -> None:
    """스펙을 YAML/JSON 파일로 저장"""
```

### watcher.py - 폴더 감시

**ProjectWatcher - 메인 감시 클래스**
```python
class ProjectWatcher:
    """
    projects/queue/ 폴더를 감시하고 새 스펙 파일을 처리.

    동작:
    1. watchdog으로 폴더 감시
    2. 새 YAML/JSON 파일 감지
    3. ProjectSpec 로드 및 검증
    4. 마스터 태스크 생성 후 큐에 추가
    5. 파일을 적절한 폴더로 이동
    """

    async def start(self) -> None:
        """감시 시작 (무한 루프)"""

    async def stop(self) -> None:
        """감시 중지"""

    def set_callback(self, callback: Callable) -> None:
        """새 프로젝트 콜백 설정"""
```

**ProjectFileHandler - 파일 이벤트 핸들러**
```python
class ProjectFileHandler(FileSystemEventHandler):
    """
    파일 시스템 이벤트 처리.

    on_created() 호출 시:
    1. YAML/JSON 파일인지 확인
    2. 스펙 로드 및 검증
    3. 실패 시 failed/ 폴더로 이동
    4. 성공 시 마스터 태스크 생성
    """
```

**폴더 구조**
```
projects/
├── queue/        # 새 프로젝트 드랍 (감시 대상)
├── completed/    # 완료된 프로젝트
├── failed/       # 실패한 프로젝트
└── examples/     # 예시 스펙 파일
```

### cli.py - CLI 명령어

**사용 가능한 명령어**
```bash
# 프로젝트 제출
ace-project submit project.yaml
ace-project submit --name "My API" --description "..." --goal "Goal 1" --goal "Goal 2"

# 프로젝트 목록
ace-project list
ace-project list --status pending
ace-project list --json

# 프로젝트 상태
ace-project status <project_id>
ace-project status <project_id> --json

# 예시 스펙 생성
ace-project example
ace-project example --output ./my-spec.yaml
```

**Python API**
```python
from src.project import submit_project, list_projects, get_project_status

# 프로젝트 제출
project_id = submit_project(spec_path="my-project.yaml")

# 또는 직접 생성
project_id = submit_project(
    name="My API Server",
    description="REST API with FastAPI",
    goals=["Create endpoints", "Add auth"],
    priority="high",
)

# 프로젝트 목록
projects = list_projects(status="pending", limit=10)

# 프로젝트 상태
status = get_project_status(project_id)
```

## 프로젝트 스펙 예시

```yaml
# projects/queue/my-api.yaml

name: "Example REST API"
description: "Build a REST API server with FastAPI and PostgreSQL"

# 프로젝트 목표
goals:
  - "Create user authentication with JWT"
  - "Implement CRUD endpoints for resources"
  - "Add database models and migrations"
  - "Write unit and integration tests"
  - "Generate API documentation"

# 요구사항
requirements:
  functional:
    - "User registration and login"
    - "Token-based authentication"
    - "Resource CRUD operations"
  non_functional:
    - "Response time < 200ms"
    - "Test coverage > 80%"
  constraints:
    - "Python 3.11+"
    - "PostgreSQL 14+"
  dependencies:
    - "FastAPI"
    - "SQLAlchemy"
    - "Pydantic"

# 기술 스택
tech_stack:
  - "Python 3.11"
  - "FastAPI"
  - "SQLAlchemy 2.0"
  - "PostgreSQL"
  - "Docker"

# 출력 경로
output_path: "./output/example-api"

# 에이전트 설정
agents:
  use_auto_claude: true
  use_ag_autogen: true
  use_ag_law: false
  preferred_agents:
    - "auto_claude_coder"
    - "auto_claude_qa_reviewer"

# 파이프라인 설정
pipeline:
  pattern: "auto"
  max_iterations: 5
  parallel_limit: 3
  timeout_minutes: 60

# 실행 설정
priority: "medium"
auto_start: true
```

## 실행 흐름

```
1. 사용자가 YAML 파일을 projects/queue/에 드랍
   │
   └─→ ProjectWatcher (watchdog Observer)
         │
         ├─→ on_created() 이벤트 발생
         │
         ├─→ _load_and_validate()
         │     └─→ load_project_spec()
         │         └─→ ProjectSpec 검증
         │
         ├─→ 검증 실패 시: failed/ 폴더로 이동
         │
         └─→ 검증 성공 시: _create_tasks()
               │
               ├─→ 마스터 PLANNING 태스크 생성
               │     - project_id, goals, requirements
               │     - agent_config, pipeline_config
               │
               ├─→ TaskQueue.enqueue(master_task)
               │
               └─→ 스펙 파일 업데이트 (status: QUEUED)

2. Orchestrator가 큐에서 마스터 태스크 가져오기
   │
   └─→ AUTO_CLAUDE_PLANNER가 goals를 서브태스크로 분해
         │
         └─→ 각 서브태스크 실행 (Sequential/Parallel/CriticLoop)
```

## 사용 예시

### Python API
```python
from src.project import (
    ProjectSpec,
    ProjectWatcher,
    submit_project,
    start_watcher,
)

# 방법 1: 스펙 파일 제출
project_id = submit_project("my-project.yaml")

# 방법 2: 직접 스펙 생성
spec = ProjectSpec(
    name="My App",
    description="Build a web application",
    goals=["Create frontend", "Create backend", "Deploy"],
)
save_project_spec(spec, "projects/queue/my-app.yaml")

# 방법 3: Watcher 시작 (24/7)
await start_watcher()
```

### CLI
```bash
# 예시 스펙 생성
python -m src.project.cli example

# 프로젝트 제출
python -m src.project.cli submit ./my-project.yaml

# 프로젝트 목록 확인
python -m src.project.cli list

# 상태 확인
python -m src.project.cli status abc12345
```

## 설정 (config.py)

```python
# 프로젝트 디렉토리
projects_dir: str = "./projects"

# TaskQueue 데이터베이스
queue_db_path: str = "./data/tasks.db"
```

## 의존성

- `pydantic>=2.0.0` - 스펙 모델 검증
- `pyyaml>=6.0.0` - YAML 파싱
- `watchdog>=3.0.0` - 폴더 감시

## 관련 모듈

- `src/coordinator/task_queue.py` - 태스크 큐
- `src/coordinator/orchestrator.py` - 24/7 오케스트레이터
- `src/utils/models.py` - Task, Priority 모델
- `src/utils/config.py` - projects_dir 설정
