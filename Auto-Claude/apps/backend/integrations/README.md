# Integrations Module

외부 서비스 연동 모듈. Graphiti 메모리 시스템과 Linear 작업 추적을 담당합니다.

## 구조

```
integrations/
├── graphiti/           # Graphiti 메모리 시스템
│   ├── memory.py       # GraphitiMemory 메인 클래스
│   ├── config.py       # 설정
│   ├── providers.py    # 멀티 프로바이더 팩토리
│   ├── providers_pkg/  # 프로바이더 구현
│   └── queries_pkg/    # 쿼리 및 스키마
│       ├── graphiti.py # 메인 쿼리 클래스
│       ├── client.py   # LadybugDB 클라이언트
│       ├── queries.py  # 그래프 쿼리
│       ├── search.py   # 시맨틱 검색
│       └── schema.py   # 스키마 정의
│
└── linear/             # Linear 작업 추적
    └── (작업 진행 상태 동기화)
```

## Graphiti 메모리 시스템

**Docker 불필요!** LadybugDB가 내장되어 있습니다.

### 기능

- **그래프 데이터베이스**: 세션 간 지식 그래프
- **시맨틱 검색**: 관련 컨텍스트 자동 검색
- **인사이트 추출**: 패턴, 고찰 자동 저장
- **멀티 프로바이더**: OpenAI, Anthropic, Azure, Ollama, Google AI

### 설정

`apps/backend/.env`:
```bash
GRAPHITI_ENABLED=true
ANTHROPIC_API_KEY=sk-ant-...
# 또는 다른 프로바이더 키
```

### 사용법

```python
from integrations.graphiti.memory import get_graphiti_memory

# 메모리 인스턴스 가져오기
memory = get_graphiti_memory(spec_dir, project_dir)

# 세션 컨텍스트 검색
context = memory.get_context_for_session("Implementing feature X")

# 인사이트 저장
memory.add_session_insight("Pattern: use React hooks for state")
```

### 데이터 저장 위치

```
.auto-claude/specs/XXX-feature/
└── graphiti/           # 메모리 데이터
```

### 지원 프로바이더

| 프로바이더 | LLM | Embedder |
|-----------|-----|----------|
| OpenAI | O | O |
| Anthropic | O | X |
| Azure OpenAI | O | O |
| Ollama | O | O |
| Google AI (Gemini) | O | O |
| Voyage AI | X | O |

## Linear 연동

작업 진행 상태를 Linear와 자동 동기화합니다.

### 설정

```bash
LINEAR_API_KEY=lin_...
LINEAR_TEAM_ID=...
```

### 기능

- 작업 상태 자동 업데이트
- "In Progress", "Done" 동기화
- spec별 이슈 연결

## 관련 파일

- `integrations/graphiti/memory.py`: 메인 메모리 클래스
- `integrations/graphiti/providers.py`: 프로바이더 팩토리
- `integrations/linear/`: Linear 연동
- `linear_config.py`, `linear_updater.py`: Linear 설정 및 업데이트
