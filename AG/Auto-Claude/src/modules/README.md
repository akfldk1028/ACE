# Modules

AG/Auto-Claude 외부 모듈 래퍼.

## 개요

Git submodule로 추가된 외부 프로젝트들을 Python에서 사용할 수 있도록 래핑합니다.

```
modules/                    # Git Submodules (루트)
└── Auto-Claude/            # AndyMik90/Auto-Claude

src/modules/                # Python Wrappers (여기)
├── __init__.py             # Path setup
└── auto_claude_prompts.py  # Prompt loader
```

## 파일 설명

### `__init__.py`

Auto-Claude submodule 경로를 Python path에 추가합니다.

```python
from src.modules import AUTO_CLAUDE_AVAILABLE, AUTO_CLAUDE_PATH

if AUTO_CLAUDE_AVAILABLE:
    print(f"Auto-Claude 경로: {AUTO_CLAUDE_PATH}")
```

### `auto_claude_prompts.py`

Auto-Claude의 시스템 프롬프트를 로드합니다.

```python
from src.modules.auto_claude_prompts import (
    get_planner_prompt,
    get_coder_prompt,
    get_qa_reviewer_prompt,
    get_qa_fixer_prompt,
    list_available_prompts,
)

# 사용 가능한 프롬프트 목록
prompts = list_available_prompts()
# {'planner': True, 'coder': True, ...}

# 프롬프트 로드
planner_prompt = get_planner_prompt()
```

## 사용 가능한 프롬프트

| 프롬프트 | 파일 | 용도 |
|---------|------|------|
| planner | planner.md | 계획 수립 |
| coder | coder.md | 코드 구현 |
| qa_reviewer | qa_reviewer.md | QA 리뷰 |
| qa_fixer | qa_fixer.md | 버그 수정 |
| spec_gatherer | spec_gatherer.md | 요구사항 수집 |
| spec_writer | spec_writer.md | 스펙 작성 |
| spec_critic | spec_critic.md | 스펙 검토 |

## Submodule 관리

```bash
# 초기화
git submodule update --init --recursive

# 업데이트
cd modules/Auto-Claude && git pull origin develop

# 특정 커밋으로 고정
cd modules/Auto-Claude && git checkout <commit-hash>
git add modules/Auto-Claude
git commit -m "Update Auto-Claude submodule"
```

## 관련 파일

- `/modules/Auto-Claude/` - Git submodule 위치
- `/.gitmodules` - Submodule 설정
- `/.claude/ARCHITECTURE_DECISIONS.md` - 아키텍처 결정 기록
