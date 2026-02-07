# Auto-Claude Agents

Claude Agent SDK 기반 AI 에이전트 구현.

## 개요

Auto-Claude 에이전트는 Claude Code의 OAuth 인증과 SDK를 사용하여 자율적으로 코딩 작업을 수행합니다.

```
src/agents/auto_claude/
├── __init__.py      # 모듈 exports
├── base.py          # BaseAutoClaudeAgent (OAuth, SDK 클라이언트)
├── planner.py       # 계획 수립 에이전트
├── coder.py         # 코드 구현 에이전트
├── qa_reviewer.py   # QA 리뷰 에이전트
└── qa_fixer.py      # 버그 수정 에이전트
```

## 에이전트 목록

| 에이전트 | 클래스 | 역할 |
|---------|--------|------|
| Planner | `AutoClaudePlanner` | 요구사항 분석, 태스크 분해, 구현 계획 |
| Coder | `AutoClaudeCoder` | 코드 작성, 기능 구현, 리팩토링 |
| QA Reviewer | `AutoClaudeQAReviewer` | 코드 리뷰, 테스트 실행, 품질 검증 |
| QA Fixer | `AutoClaudeQAFixer` | 버그 수정, 이슈 해결, 디버깅 |

## 사용법

### 기본 사용

```python
from src.agents.auto_claude import (
    AutoClaudePlanner,
    AutoClaudeCoder,
    AutoClaudeQAReviewer,
    AutoClaudeQAFixer,
)

# 에이전트 생성
planner = AutoClaudePlanner()

# 초기화 (OAuth 토큰 확인)
await planner.initialize()

# 태스크 실행
result = await planner.execute(
    task_description="사용자 인증 API 구현",
    context={"requirements": {"auth_method": "JWT"}},
    project_dir=Path("./my-project"),
)

# 종료
await planner.shutdown()
```

### 어댑터를 통한 사용 (권장)

```python
from src.adapters.auto_claude import create_planner_adapter

adapter = create_planner_adapter()
await adapter.initialize()

result = await adapter.execute(task, context)
```

## 시스템 프롬프트

에이전트는 Auto-Claude submodule의 프롬프트를 동적으로 로드합니다:

```python
# src/modules/auto_claude_prompts.py에서 로드
system_prompt = get_planner_prompt() or self.DEFAULT_SYSTEM_PROMPT
```

프롬프트 위치: `modules/Auto-Claude/apps/backend/prompts/`

| 에이전트 | 프롬프트 파일 | 크기 |
|---------|--------------|------|
| Planner | planner.md | ~28KB |
| Coder | coder.md | ~31KB |
| QA Reviewer | qa_reviewer.md | ~13KB |
| QA Fixer | qa_fixer.md | ~9KB |

## OAuth 인증

Claude Code OAuth 토큰이 필요합니다:

```bash
# 1. Claude Code 실행
claude

# 2. 로그인
/login

# 3. 브라우저에서 인증 완료
```

토큰 확인 위치:
- Windows: `%USERPROFILE%\.claude\.credentials.json`
- macOS: Keychain (`Claude Code-credentials`)
- Linux: Secret Service

### 환경 변수

```bash
# 직접 토큰 설정 (선택)
export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...
```

## 핵심 클래스

### BaseAutoClaudeAgent

모든 Auto-Claude 에이전트의 베이스 클래스:

```python
class BaseAutoClaudeAgent(ABC):
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", ...]

    async def initialize(self) -> None
    async def shutdown(self) -> None
    async def run_session(self, prompt: str, project_dir: Path) -> str
    async def health_check(self) -> bool

    @abstractmethod
    async def execute(self, task_description, context, project_dir) -> Dict
```

### OAuth 헬퍼 함수

```python
from src.agents.auto_claude import (
    get_oauth_token,      # 토큰 조회 (None 가능)
    require_oauth_token,  # 토큰 필수 (없으면 예외)
    CLAUDE_SDK_AVAILABLE, # SDK 설치 여부
)
```

## 관련 파일

- `/src/adapters/auto_claude.py` - 어댑터 레이어
- `/src/modules/auto_claude_prompts.py` - 프롬프트 로더
- `/modules/Auto-Claude/` - 원본 submodule
