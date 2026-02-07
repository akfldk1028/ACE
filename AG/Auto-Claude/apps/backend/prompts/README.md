# Prompts Module

에이전트 시스템 프롬프트 모음. 각 에이전트의 역할과 행동을 정의합니다.

## 프롬프트 목록

### 핵심 에이전트

| 파일 | 에이전트 | 역할 |
|------|---------|------|
| `planner.md` | Planner | 서브태스크 기반 구현 계획 생성 |
| `coder.md` | Coder | 개별 서브태스크 구현 |
| `coder_recovery.md` | Coder Recovery | STUCK 태스크 복구 |
| `qa_reviewer.md` | QA Reviewer | 인수 조건 검증 |
| `qa_fixer.md` | QA Fixer | QA 이슈 수정 |

### Spec 생성 에이전트

| 파일 | 에이전트 | 역할 |
|------|---------|------|
| `spec_gatherer.md` | Spec Gatherer | 사용자 요구사항 수집 |
| `spec_researcher.md` | Spec Researcher | 외부 연동 검증 |
| `spec_writer.md` | Spec Writer | spec.md 문서 생성 |
| `spec_critic.md` | Spec Critic | ultrathink로 셀프 비평 |
| `spec_quick.md` | Quick Spec | 간단한 spec 빠른 생성 |

### 분석 에이전트

| 파일 | 에이전트 | 역할 |
|------|---------|------|
| `complexity_assessor.md` | Complexity Assessor | AI 기반 복잡도 평가 |
| `insight_extractor.md` | Insight Extractor | 세션에서 인사이트 추출 |
| `competitor_analysis.md` | Competitor Analyzer | 경쟁사 분석 |

### Ideation 에이전트

| 파일 | 역할 |
|------|------|
| `ideation_code_improvements.md` | 코드 개선 아이디어 |
| `ideation_code_quality.md` | 코드 품질 분석 |
| `ideation_documentation.md` | 문서화 제안 |
| `ideation_performance.md` | 성능 최적화 |
| `ideation_security.md` | 보안 분석 |
| `ideation_ui_ux.md` | UI/UX 개선 |

### 기타 에이전트

| 파일 | 역할 |
|------|------|
| `followup_planner.md` | 후속 작업 계획 |
| `roadmap_discovery.md` | 로드맵 발견 |
| `roadmap_features.md` | 기능 로드맵 |
| `validation_fixer.md` | 검증 이슈 수정 |

### 하위 폴더

| 폴더 | 내용 |
|------|------|
| `github/` | GitHub 관련 프롬프트 |
| `mcp_tools/` | MCP 도구 프롬프트 |

## 프롬프트 구조

각 프롬프트는 다음 구조를 따릅니다:

```markdown
# Role
에이전트의 역할 정의

# Context
주어진 컨텍스트 설명

# Instructions
수행할 작업 지시

# Output Format
출력 형식 정의

# Examples
예시 (선택적)
```

## 복잡도별 프롬프트 선택

| 복잡도 | 사용 프롬프트 |
|--------|-------------|
| SIMPLE | spec_quick.md → planner.md → coder.md |
| STANDARD | spec_gatherer.md → spec_writer.md → planner.md → coder.md |
| COMPLEX | 전체 + spec_critic.md (ultrathink) |

## 커스터마이징

프롬프트를 수정하여 에이전트 행동을 조정할 수 있습니다:

1. 역할 명확화
2. 출력 형식 변경
3. 제약 조건 추가
4. 예시 추가

## 관련 파일

- `prompts.py`: 프롬프트 로딩 유틸리티
- `prompt_generator.py`: 동적 프롬프트 생성
- `prompts_pkg/`: 프롬프트 관리 패키지
