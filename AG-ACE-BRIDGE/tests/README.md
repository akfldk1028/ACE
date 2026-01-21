# Tests

AG-ACE-BRIDGE 테스트 모음

## 구조

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_orchestrator.py     # Orchestrator 테스트
├── test_pipeline.py         # Pipeline 테스트
├── test_adapters.py         # Adapter 테스트
├── test_memory.py           # Memory sync 테스트
└── test_registry.py         # Registry 테스트
```

## 실행 방법

```bash
# 전체 테스트
pytest tests/ -v

# 특정 파일
pytest tests/test_orchestrator.py -v

# 커버리지
pytest tests/ --cov=src --cov-report=html
```

## Fixtures (conftest.py)

```python
import pytest
from src.utils.models import Task, TaskType, Priority

@pytest.fixture
def sample_task():
    return Task(
        type=TaskType.CODE,
        description="Implement feature X",
        priority=Priority.MEDIUM,
        requirements=["implementation"]
    )

@pytest.fixture
def mock_adapter():
    """Mock adapter for testing"""
    ...
```

## 테스트 카테고리

### Unit Tests
- `test_models.py`: 데이터 모델
- `test_config.py`: 설정 로드
- `test_capabilities.py`: 기능 정의

### Integration Tests
- `test_orchestrator.py`: 전체 오케스트레이션 흐름
- `test_pipeline.py`: 파이프라인 실행
- `test_adapters.py`: 에이전트 연결

### E2E Tests
- `test_e2e_auto_claude.py`: Auto-Claude 연동
- `test_e2e_ag.py`: AG 연동
- `test_e2e_full_pipeline.py`: 전체 플로우

## 설정

```bash
# 테스트 의존성 설치
pip install -e ".[dev]"

# 또는
pip install pytest pytest-asyncio pytest-cov
```
