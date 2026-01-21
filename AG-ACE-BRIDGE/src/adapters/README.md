# Adapters Module

에이전트 연결 모듈. Auto-Claude와 AG 에이전트들에 대한 통일된 인터페이스를 제공합니다.

## 구조

```
adapters/
├── __init__.py
├── base.py            # 기본 어댑터 인터페이스 (ABC)
├── auto_claude.py     # Auto-Claude SDK 어댑터
├── ag_autogen.py      # AG autogen_a2a_kit HTTP 어댑터
└── ag_law_domain.py   # AG law-domain-agents HTTP 어댑터
```

## 핵심 컴포넌트

### base.py - 기본 인터페이스

```python
class AgentAdapter(ABC):
    """
    모든 어댑터의 기본 인터페이스
    일관된 에이전트 상호작용 제공
    """

    @abstractmethod
    async def execute(self, task: Task, context: dict) -> Result:
        """작업 실행"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """에이전트 상태 확인"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """에이전트 기능 목록"""
        pass
```

### auto_claude.py - Auto-Claude 어댑터

```python
class AutoClaudeAdapter(AgentAdapter):
    """
    Auto-Claude SDK 세션 관리
    - Claude Agent SDK 연동
    - Graphiti 메모리 접근
    - 4개 에이전트 지원: planner, coder, qa_reviewer, qa_fixer
    """

    async def execute(self, task: Task, context: dict) -> Result:
        # SDK 세션 생성 및 실행
        client = create_client(
            project_dir=self.project_dir,
            spec_dir=self.spec_dir,
            agent_type=self.agent_type
        )
        response = await client.create_agent_session(
            name=f"{self.agent_type}-session",
            starting_message=task.description
        )
        return Result(task_id=task.id, status="success", output=response)
```

### ag_autogen.py - AG Autogen 어댑터

```python
class AGAutogenAdapter(AgentAdapter):
    """
    AG autogen_a2a_kit HTTP 클라이언트
    - A2A 프로토콜 지원
    - 8개 에이전트 지원
    """

    async def execute(self, task: Task, context: dict) -> Result:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint_url}/agents/{self.agent_name}/run",
                json={"task": task.dict(), "context": context}
            )
            return Result(**response.json())
```

### ag_law_domain.py - AG Law Domain 어댑터

```python
class AGLawDomainAdapter(AgentAdapter):
    """
    AG law-domain-agents HTTP 클라이언트
    - FastAPI 엔드포인트 호출
    - Neo4j 연동 에이전트
    - 5개 법률 도메인 에이전트 지원
    """

    async def execute(self, task: Task, context: dict) -> Result:
        # 법률 도메인 특화 에이전트 호출
        ...
```

## 지원 에이전트

### Auto-Claude (4개)
| 에이전트 | 기능 |
|----------|------|
| `auto_claude.planner` | 구현 계획 생성 |
| `auto_claude.coder` | 코드 구현 (24/7) |
| `auto_claude.qa_reviewer` | 품질 검증 |
| `auto_claude.qa_fixer` | 이슈 수정 |

### AG autogen_a2a_kit (8개)
| 에이전트 | 기능 |
|----------|------|
| `ag.research` | 정보 수집 |
| `ag.analyst` | 데이터 분석 |
| `ag.writer` | 문서 작성 |
| `ag.reviewer` | 검토 피드백 |
| `ag.coordinator` | 작업 조율 |
| ... | 3개 더 |

### AG law-domain (5개)
| 에이전트 | 기능 |
|----------|------|
| `ag.case_analyzer` | 판례 분석 |
| `ag.legal_researcher` | 법률 조사 |
| `ag.risk_assessor` | 리스크 평가 |
| `ag.compliance_checker` | 컴플라이언스 검증 |
| `ag.document_drafter` | 법률 문서 초안 |

## 사용법

```python
from src.adapters import AutoClaudeAdapter, AGAutogenAdapter

# Auto-Claude
auto = AutoClaudeAdapter(agent_type="coder")
result = await auto.execute(task, context)

# AG
ag = AGAutogenAdapter(agent_name="research")
result = await ag.execute(task, context)
```

## 설계 패턴

- **Adapter Pattern** - 통일된 인터페이스
- **Handoff Pattern** (Microsoft) - 에이전트 간 컨텍스트 전달

## 관련 파일

- `src/utils/models.py`: AgentType, AgentCapability 모델
- `src/registry/`: 에이전트 레지스트리
- `Auto-Claude/apps/backend/core/client.py`: SDK 클라이언트
