# Tests

Auto-Claude 테스트 스위트. 백엔드 Python 코드의 단위 테스트와 통합 테스트를 포함합니다.

## 빠른 시작

```bash
# 테스트 의존성 설치
cd apps/backend && uv pip install -r ../../tests/requirements-test.txt

# 전체 테스트 실행
apps/backend/.venv/bin/pytest tests/ -v

# 특정 테스트 파일 실행
apps/backend/.venv/bin/pytest tests/test_security.py -v

# 특정 테스트 함수 실행
apps/backend/.venv/bin/pytest tests/test_security.py::test_bash_command_validation -v

# 느린 테스트 제외
apps/backend/.venv/bin/pytest tests/ -m "not slow"
```

## 테스트 구조

### 핵심 테스트

| 파일 | 테스트 대상 |
|------|------------|
| `test_client.py` | Claude SDK 클라이언트 |
| `test_auth.py` | OAuth 인증 |
| `test_security.py` | 보안 모듈 |
| `test_security_cache.py` | 보안 캐시 |
| `test_security_scanner.py` | 보안 스캐너 |

### 에이전트 테스트

| 파일 | 테스트 대상 |
|------|------------|
| `test_agent_architecture.py` | 에이전트 아키텍처 |
| `test_agent_configs.py` | 에이전트 설정 |
| `test_implementation_plan.py` | 구현 계획 |
| `test_recovery.py` | 복구 로직 |

### QA 테스트

| 파일 | 테스트 대상 |
|------|------------|
| `test_qa_loop.py` | QA 루프 |
| `test_qa_loop_enhancements.py` | QA 루프 개선 |
| `test_qa_criteria.py` | QA 기준 |
| `test_qa_report_*.py` | QA 리포트 생성 |

### Merge 테스트

| 파일 | 테스트 대상 |
|------|------------|
| `test_merge_orchestrator.py` | Merge 오케스트레이터 |
| `test_merge_conflict_detector.py` | 충돌 감지 |
| `test_merge_ai_resolver.py` | AI 충돌 해결 |
| `test_merge_auto_merger.py` | 자동 머지 |
| `test_merge_semantic_analyzer.py` | 시맨틱 분석 |
| `test_merge_parallel.py` | 병렬 머지 |

### GitHub 통합 테스트

| 파일 | 테스트 대상 |
|------|------------|
| `test_github_pr_review.py` | PR 리뷰 |
| `test_github_pr_e2e.py` | PR E2E 테스트 |
| `test_github_bot_detection.py` | 봇 감지 |
| `test_pr_worktree_manager.py` | PR Worktree 관리 |

### Workspace 테스트

| 파일 | 테스트 대상 |
|------|------------|
| `test_workspace.py` | 워크스페이스 |
| `test_worktree.py` | Git Worktree |
| `test_project_analyzer.py` | 프로젝트 분석 |

### Spec 테스트

| 파일 | 테스트 대상 |
|------|------------|
| `test_spec_pipeline.py` | Spec 파이프라인 |
| `test_spec_phases.py` | Spec 단계 |
| `test_spec_complexity.py` | 복잡도 평가 |

### 유틸리티 테스트

| 파일 | 테스트 대상 |
|------|------------|
| `test_platform.py` | 크로스 플랫폼 |
| `test_git_executable.py` | Git 실행 파일 |
| `test_check_encoding.py` | 인코딩 검사 |
| `test_discovery.py` | 발견 로직 |
| `test_ci_discovery.py` | CI 발견 |

### Graphiti 테스트

| 파일 | 테스트 대상 |
|------|------------|
| `test_graphiti.py` | Graphiti 메모리 |
| `test_graphiti_search.py` | Graphiti 검색 |

## 테스트 픽스처

### conftest.py

공통 픽스처 정의:
- 임시 디렉토리
- Mock 클라이언트
- 테스트 프로젝트 설정

### test_fixtures.py

테스트용 데이터 픽스처

### review_fixtures.py

리뷰 관련 픽스처

### merge_fixtures.py

머지 테스트용 픽스처

### qa_report_helpers.py

QA 리포트 테스트 헬퍼

## 테스트 마커

```python
@pytest.mark.slow       # 느린 테스트
@pytest.mark.integration # 통합 테스트
@pytest.mark.e2e        # E2E 테스트
```

### 마커별 실행

```bash
# 느린 테스트 제외
pytest -m "not slow"

# 통합 테스트만
pytest -m integration

# E2E 테스트 제외
pytest -m "not e2e"
```

## 커버리지

```bash
# 커버리지 측정
pytest --cov=apps/backend --cov-report=html tests/

# HTML 리포트 확인
open htmlcov/index.html
```

## CI/CD

GitHub Actions에서 자동 실행:
- 모든 PR에서 테스트 실행
- 3개 플랫폼 (Windows, macOS, Linux)
- 커버리지 리포트 생성

## 새 테스트 추가

1. `test_*.py` 파일 생성
2. `test_` 접두사로 함수 정의
3. 픽스처는 `conftest.py`에 추가

```python
# tests/test_new_feature.py
import pytest

def test_new_feature():
    """새 기능 테스트."""
    result = new_feature()
    assert result == expected
```

## 관련 파일

- `requirements-test.txt` - 테스트 의존성
- `pytest.ini` - pytest 설정
- `conftest.py` - 공통 픽스처
