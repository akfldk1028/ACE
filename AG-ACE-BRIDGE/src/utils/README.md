# Utils Module

AG-ACE-BRIDGE의 핵심 유틸리티 모듈.

## 파일 구조

```
src/utils/
├── __init__.py      # 모듈 export
├── models.py        # Pydantic 데이터 모델
├── config.py        # 환경 설정 관리
├── logger.py        # 구조화된 로깅
└── README.md        # 이 파일
```

## 주요 컴포넌트

### models.py - 데이터 모델

모든 데이터 구조를 Pydantic으로 정의.

#### Enums (열거형)
| Enum | 용도 | 값 |
|------|------|-----|
| `Priority` | 태스크 우선순위 | HIGH, MEDIUM, LOW |
| `TaskType` | 태스크 유형 | RESEARCH, SPEC, PLAN, CODE, QA, FIX, VALIDATE, MERGE, CUSTOM |
| `ResultStatus` | 실행 결과 | SUCCESS, FAILED, NEEDS_RETRY, PARTIAL, CANCELLED |
| `StageType` | 파이프라인 스테이지 | SEQUENTIAL, PARALLEL, CRITIC_LOOP |
| `AgentType` | 17개 AI 에이전트 | 아래 참조 |

#### AgentType - 17개 에이전트
```
Auto-Claude (4):
├── auto_claude.planner      # 프로젝트 계획
├── auto_claude.coder        # 코드 작성
├── auto_claude.qa_reviewer  # QA 검토
└── auto_claude.qa_fixer     # QA 수정

AG Autogen (5):
├── ag.research              # 리서치
├── ag.analyst               # 분석
├── ag.writer                # 작성
├── ag.reviewer              # 리뷰
└── ag.coordinator           # 조율

AG Law Domain (5):
├── ag.case_analyzer         # 케이스 분석
├── ag.legal_researcher      # 법률 리서치
├── ag.risk_assessor         # 리스크 평가
├── ag.compliance_checker    # 컴플라이언스 체크
└── ag.document_drafter      # 문서 초안
```

#### Models (데이터 클래스)
| Model | 용도 | 주요 필드 |
|-------|------|-----------|
| `Task` | 실행할 태스크 | id, type, description, priority, input, context |
| `Result` | 실행 결과 | task_id, status, output, error, next_tasks |
| `Stage` | 파이프라인 스테이지 | agent, stage_type, timeout_seconds |
| `Pipeline` | 실행 계획 | task_id, stages, current_stage_index |
| `AgentCapability` | 에이전트 능력 | agent, capabilities, is_available |
| `MemorySyncEvent` | 메모리 동기화 | source, event_type, entity_id, data |

### config.py - 설정 관리

환경 변수 및 `.env` 파일에서 설정 로드.

```python
from src.utils.config import get_settings

settings = get_settings()
print(settings.bridge_port)  # 8080
print(settings.auto_claude_path)  # D:/Data/25_ACE/Auto-Claude/apps/backend
```

#### 주요 설정값
| 설정 | 기본값 | 설명 |
|------|--------|------|
| `bridge_port` | 8080 | 브릿지 서버 포트 |
| `auto_claude_path` | D:/Data/25_ACE/Auto-Claude/apps/backend | Auto-Claude 경로 |
| `ag_autogen_url` | http://localhost:8000 | AG Autogen 서버 |
| `ag_law_domain_url` | http://localhost:8001 | AG Law Domain 서버 |
| `neo4j_uri` | bolt://localhost:7687 | Neo4j 연결 |
| `queue_db_path` | ./data/tasks.db | SQLite 태스크 큐 |
| `max_qa_iterations` | 5 | QA 크리틱 루프 최대 반복 |

### logger.py - 구조화 로깅

structlog 기반 JSON 로깅.

```python
from src.utils.logger import Loggers, bind_context

# 모듈별 로거 사용
logger = Loggers.orchestrator()
logger.info("task_started", task_id="123", type="code")

# 컨텍스트 바인딩 (이후 모든 로그에 포함)
bind_context(pipeline_id="456")
logger.info("stage_complete")  # pipeline_id 자동 포함
```

#### 로거 종류
- `Loggers.orchestrator()` - 오케스트레이터
- `Loggers.pipeline()` - 파이프라인
- `Loggers.adapter()` - 어댑터
- `Loggers.memory()` - 메모리
- `Loggers.registry()` - 레지스트리
- `Loggers.queue()` - 태스크 큐

## 사용 예시

```python
from src.utils import Task, TaskType, Priority, Result, ResultStatus

# 태스크 생성
task = Task(
    type=TaskType.CODE,
    description="사용자 인증 기능 구현",
    priority=Priority.HIGH,
    input={"feature": "login"},
    context={"project": "my-app"}
)

# 결과 생성
result = Result(
    task_id=task.id,
    status=ResultStatus.SUCCESS,
    output={"files_created": ["auth.py", "test_auth.py"]},
    agent_used="auto_claude.coder"
)
```

## 의존성

- `pydantic>=2.0.0` - 데이터 검증
- `pydantic-settings>=2.0.0` - 설정 관리
- `structlog>=23.0.0` - 구조화 로깅
