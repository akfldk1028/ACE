# Core Module

Auto-Claude의 핵심 인프라 모듈. Claude Agent SDK 클라이언트, 인증, 플랫폼 추상화, 워크스페이스 관리를 담당합니다.

## 구조

```
core/
├── client.py              # Claude Agent SDK 클라이언트 팩토리
├── simple_client.py       # 간단한 클라이언트 래퍼
├── auth.py                # OAuth 토큰 관리
├── model_config.py        # 모델 설정
│
├── platform/              # 크로스 플랫폼 추상화
│   └── (Windows, macOS, Linux 지원)
│
├── workspace/             # 워크스페이스 관리
│   └── (Git Worktree 격리)
│
├── worktree.py            # Git Worktree 유틸리티
├── workspace.py           # 워크스페이스 유틸리티
│
├── file_utils.py          # 파일 작업 유틸리티
├── io_utils.py            # I/O 유틸리티
├── git_executable.py      # Git 실행 파일 찾기
├── gh_executable.py       # GitHub CLI 찾기
│
├── dependency_validator.py # 의존성 검증
├── plan_normalization.py  # 계획 정규화
├── phase_event.py         # 페이즈 이벤트
├── progress.py            # 진행 상태
├── sentry.py              # 에러 트래킹
└── debug.py               # 디버그 유틸리티
```

## 핵심 컴포넌트

### client.py - Claude Agent SDK 클라이언트

**중요: Anthropic API를 직접 사용하지 않습니다!**

```python
from core.client import create_client

client = create_client(
    project_dir=project_dir,
    spec_dir=spec_dir,
    model="claude-sonnet-4-5-20250929",
    agent_type="coder",  # planner, coder, qa_reviewer, qa_fixer
    max_thinking_tokens=16000
)
```

### auth.py - OAuth 토큰 관리

- macOS Keychain / Windows Credential Manager 자동 감지
- `/login` 명령으로 OAuth 인증

### platform/ - 크로스 플랫폼 추상화

```python
from core.platform import isWindows, findExecutable, getPathDelimiter

# 직접 플랫폼 체크하지 않음
if isWindows():
    # Windows 로직
```

### workspace/ - Git Worktree 격리

- 각 spec별 독립 워크스페이스
- 메인 브랜치와 완전 분리
- 안전한 실험 환경

## 사용 예시

### SDK 클라이언트 생성

```python
from core.client import create_client

# Coder 에이전트용 클라이언트
client = create_client(
    project_dir="/path/to/project",
    spec_dir="/path/to/spec",
    model="claude-sonnet-4-5-20250929",
    agent_type="coder",
    max_thinking_tokens=16000
)

# 에이전트 세션 실행
response = client.create_agent_session(
    name="coder-session",
    starting_message="Implement the feature"
)
```

### 워크스페이스 관리

```python
from core.workspace import create_isolated_workspace

# 격리된 워크스페이스 생성
workspace = create_isolated_workspace(
    project_dir="/path/to/project",
    spec_name="001-feature"
)
```

## 보안

3계층 보안 모델:
1. **OS 샌드박스**: Bash 명령어 격리
2. **파일시스템 권한**: 프로젝트 디렉토리 외부 차단
3. **동적 명령어 허용목록**: 프로젝트 스택 기반 허용

## 관련 파일

- `core/client.py`: SDK 클라이언트 (핵심)
- `core/auth.py`: 인증 관리
- `core/platform/`: 플랫폼 추상화
- `core/workspace/`: 워크스페이스 격리
