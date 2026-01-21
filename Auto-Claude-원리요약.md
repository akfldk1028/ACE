# Auto Claude 동작 원리 요약 (v2.7.5)

## 24/7 자동 실행이 맞는가?

**YES.** `coder.py`의 `run_autonomous_agent()` 함수에 `while True:` 무한 루프가 있음.
- 에러 발생 시 자동 재시도
- 서브태스크 완료 시 다음 태스크로 자동 이동
- `Ctrl+C` 한 번 → 일시정지 / 두 번 → 종료

---

## 핵심 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    Auto Claude 파이프라인                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [1] SPEC 생성 ──→ [2] PLANNER ──→ [3] CODER ──→ [4] QA LOOP   │
│      (사용자)        (계획)         (구현)        (검증)        │
│                                                                 │
│                         ↑                                       │
│                         └─────────── [5] QA FIXER ─────────────┘│
│                                      (이슈가 있으면 수정 후 재검증)│
│                                                                 │
│  [6] MERGE ←─────────────────────────────────────────────────────│
│      (승인 후 메인 브랜치에 병합)                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 프로젝트 구조

```
Auto-Claude/
├── apps/
│   ├── backend/           # Python 백엔드/CLI - 모든 에이전트 로직
│   │   ├── core/          # Client, Auth, Security, Platform
│   │   │   ├── client.py      # Claude Agent SDK 클라이언트 팩토리
│   │   │   ├── auth.py        # OAuth 토큰 관리
│   │   │   ├── platform/      # 크로스 플랫폼 추상화
│   │   │   └── workspace/     # Worktree 관리
│   │   ├── agents/        # 에이전트 구현
│   │   │   ├── coder.py       # 메인 자율 에이전트 루프
│   │   │   ├── planner.py     # 계획 수립 에이전트
│   │   │   ├── memory_manager.py  # Graphiti 메모리 관리
│   │   │   └── session.py     # 세션 관리
│   │   ├── integrations/  # 외부 연동
│   │   │   ├── graphiti/      # 메모리 시스템 (LadybugDB)
│   │   │   ├── linear/        # Linear 작업 추적
│   │   │   └── github/        # GitHub Issues/PRs
│   │   └── prompts/       # 에이전트 시스템 프롬프트
│   └── frontend/          # Electron 데스크톱 앱
│       └── src/
│           ├── main/          # Electron 메인 프로세스
│           │   └── platform/  # 플랫폼별 코드
│           └── shared/i18n/   # 국제화 (en, fr)
├── guides/                # 문서
├── tests/                 # 테스트 스위트
└── scripts/               # 빌드/유틸리티
```

---

## 단계별 상세 설명

### 1단계: Spec 생성 (사용자 입력)
```bash
python spec_runner.py --interactive
# 또는
python spec_runner.py --task "로그인 기능 추가"
```

**생성되는 파일들:**
```
.auto-claude/specs/001-feature-name/
├── spec.md                 # 기능 명세서
├── requirements.json       # 구조화된 요구사항
└── context.json           # 코드베이스 분석 결과
```

**복잡도에 따른 단계:**
- SIMPLE (3단계): Discovery → Quick Spec → Validate
- STANDARD (6-7단계): Discovery → Requirements → [Research] → Context → Spec → Plan → Validate
- COMPLEX (8단계): 전체 파이프라인 + Self-Critique (ultrathink)

---

### 2단계: Planner Agent (계획 수립)
**역할:** `spec.md`를 읽고 `implementation_plan.json` 생성

**생성되는 계획 구조:**
```json
{
  "feature": "로그인 기능",
  "workflow_type": "standard",
  "phases": [
    {
      "id": "phase-1",
      "name": "Backend API",
      "subtasks": [
        {"id": "1.1", "description": "User 모델 생성", "status": "pending"},
        {"id": "1.2", "description": "Auth 엔드포인트 생성", "status": "pending"}
      ]
    },
    {
      "id": "phase-2",
      "name": "Frontend UI",
      "subtasks": [
        {"id": "2.1", "description": "로그인 폼 컴포넌트", "status": "pending"},
        {"id": "2.2", "description": "인증 상태 관리", "status": "pending"}
      ]
    }
  ]
}
```

---

### 3단계: Coder Agent (구현) - 핵심 루프

**`coder.py` - `run_autonomous_agent()` 핵심 로직:**

```python
# 초기화
recovery_manager = RecoveryManager(spec_dir, project_dir)  # 메모리 지속성
status_manager = StatusManager(project_dir)                # ccstatusline 상태
task_logger = get_task_logger(spec_dir)                    # 로그 기록

while True:  # ← 24/7 무한 루프
    iteration += 1

    # 1. 다음 서브태스크 가져오기
    next_subtask = get_next_subtask(spec_dir)

    # 2. Phase별 모델/thinking 설정 가져오기
    phase_model = get_phase_model(spec_dir, current_phase, model)
    phase_thinking_budget = get_phase_thinking_budget(spec_dir, current_phase)

    # 3. Claude Agent SDK 클라이언트 생성 (NOT Anthropic API!)
    client = create_client(
        project_dir,
        spec_dir,
        phase_model,
        agent_type="planner" if first_run else "coder",
        max_thinking_tokens=phase_thinking_budget,
    )

    # 4. 서브태스크용 프롬프트 생성
    prompt = generate_subtask_prompt(spec_dir, project_dir, subtask, phase)

    # 5. Graphiti 메모리에서 컨텍스트 로드 (이전 세션 학습)
    graphiti_context = await get_graphiti_context(spec_dir, project_dir, next_subtask)

    # 6. 에이전트 세션 실행
    status, response = await run_agent_session(client, prompt, spec_dir, verbose)

    # 7. 후처리 (커밋, 메모리 저장, 상태 업데이트)
    await post_session_processing(spec_dir, project_dir, subtask_id, ...)

    # 8. 상태에 따른 분기
    if status == "complete":
        break  # 모든 서브태스크 완료
    elif status == "continue":
        await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)  # 다음 태스크로
    elif status == "error":
        await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)  # 재시도
```

**자동 실행 특징:**
- `AUTO_CONTINUE_DELAY_SECONDS` (기본 3초) 후 자동으로 다음 태스크
- 에러 발생 시 자동 재시도
- 3번 실패 시 "STUCK" 마킹 후 다음 태스크로 이동
- `PAUSE` 파일 생성으로 수동 일시정지 가능

---

### 4단계: QA Validation Loop (품질 검증)

```bash
python run.py --spec 001 --qa
```

**QA 루프 동작:**
```
┌──────────────────────────────────────────────────────┐
│              QA VALIDATION LOOP                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  [QA Reviewer] ──→ 테스트 실행 & 검증               │
│        │            (E2E 테스팅 via Electron MCP)    │
│        │                                             │
│        ├─→ APPROVED? ──→ 완료!                       │
│        │                                             │
│        └─→ REJECTED? ──→ [QA Fixer] ──→ 재검증 루프 │
│                              │                       │
│                              └──→ (최대 5회 반복)    │
│                                                      │
│  MAX_QA_ITERATIONS = 5                               │
│  반복 이슈 감지 시 Human Escalation                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**E2E 테스팅 (Electron MCP):**
```bash
# .env 설정
ELECTRON_MCP_ENABLED=true
ELECTRON_DEBUG_PORT=9222
```

QA 에이전트가 Chrome DevTools Protocol로 실제 앱과 상호작용:
- 스크린샷 캡처
- 버튼 클릭, 폼 입력
- 페이지 구조 검사
- 콘솔 로그 읽기

**생성되는 파일:**
```
.auto-claude/specs/001-feature/
├── qa_report.md           # QA 검증 결과
├── QA_FIX_REQUEST.md      # 수정 필요 사항 (rejected 시)
└── implementation_plan.json  # qa_status 필드 업데이트
```

---

### 5단계: QA Fixer (이슈 수정)

- `QA_FIX_REQUEST.md`를 읽고 자동 수정
- 수정 후 QA Reviewer 재실행
- 반복 이슈 감지 시 `escalate_to_human()` 호출

---

### 6단계: Merge (병합)

```bash
python run.py --spec 001 --merge
```

**워크플로우:**
1. 모든 변경사항은 `auto-claude/{spec-name}` 브랜치에서 진행
2. Git Worktree로 메인 브랜치와 완전 분리
3. 사용자 승인 후에만 `main` 브랜치로 병합
4. **자동 push 없음** - 사용자가 직접 push

---

## Claude Agent SDK 통합

**중요: Auto Claude는 Anthropic API를 직접 사용하지 않음!**

```python
# ❌ 잘못된 방법
from anthropic import Anthropic
client = Anthropic()

# ✅ 올바른 방법
from core.client import create_client
client = create_client(
    project_dir=project_dir,
    spec_dir=spec_dir,
    model="claude-sonnet-4-5-20250929",
    agent_type="coder",  # planner, coder, qa_reviewer, qa_fixer
    max_thinking_tokens=16000
)
```

**SDK 사용 이유:**
- 사전 구성된 보안 (샌드박스, allowlist, hooks)
- 자동 MCP 서버 통합 (Context7, Linear, Graphiti, Electron, Puppeteer)
- 에이전트 역할별 도구 권한
- 세션 관리 및 복구
- 프로젝트 인덱스 캐싱 (5분 TTL)

---

## 보안 모델

```
┌─────────────────────────────────────────────────────────────────┐
│                    3-Layer Security                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: OS Sandbox                                            │
│           └─ Bash 명령어 격리 실행                               │
│                                                                 │
│  Layer 2: Filesystem Permissions                                │
│           └─ 프로젝트 디렉토리 외부 접근 차단                     │
│                                                                 │
│  Layer 3: Dynamic Command Allowlist                             │
│           └─ 프로젝트 스택 분석 후 허용 명령어만 실행             │
│              (security.py + project_analyzer.py)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**보안 프로필:** `.auto-claude-security.json`에 캐싱

---

## 메모리 시스템 (Graphiti + LadybugDB)

**Docker 불필요!** LadybugDB가 내장되어 있음.

```
┌──────────────────────────────────────────────────────┐
│                 Graphiti Memory                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Session 1 ──→ 패턴/인사이트 저장 ──→ Memory Graph   │
│                                          │           │
│  Session 2 ──→ Memory Graph 조회 ←───────┘           │
│              └─ 이전 세션의 학습 내용 활용            │
│                                                      │
│  저장 위치: .auto-claude/specs/XXX/graphiti/         │
│                                                      │
│  Multi-Provider 지원:                                │
│  - LLM: OpenAI, Anthropic, Azure, Ollama, Google AI  │
│  - Embedders: OpenAI, Voyage AI, Azure, Ollama       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**구성 파일:** `apps/backend/.env`
```bash
GRAPHITI_ENABLED=true
ANTHROPIC_API_KEY=sk-...
# 또는 다른 provider 키
```

---

## 크로스 플랫폼 지원

**Windows, macOS, Linux 모두 지원**

```typescript
// ❌ 잘못된 방법 - 직접 플랫폼 체크
if (process.platform === 'win32') { ... }

// ✅ 올바른 방법 - 플랫폼 추상화 사용
import { isWindows, findExecutable, joinPaths } from './platform';
```

**플랫폼 모듈 API:**

| 함수 | 용도 |
|------|------|
| `isWindows()` / `isMacOS()` / `isLinux()` | OS 감지 |
| `getPathDelimiter()` | `;` (Windows) 또는 `:` (Unix) |
| `getExecutableExtension()` | `.exe` (Windows) 또는 공백 (Unix) |
| `findExecutable(name)` | 플랫폼별 실행파일 찾기 |
| `getBinaryDirectories()` | 플랫폼별 bin 경로 |

**CI:** 3개 플랫폼 모두에서 테스트 (ubuntu, windows, macos)

---

## 외부 통합

### Linear 연동
```bash
# .env
LINEAR_API_KEY=lin_...
LINEAR_TEAM_ID=...
```
- 작업 진행 상태 자동 업데이트
- "In Progress", "Done" 상태 동기화

### GitHub 연동
- Issues 가져오기
- PR 자동 생성
- AI 기반 조사

---

## 에이전트 프롬프트

| 프롬프트 파일 | 역할 |
|--------------|------|
| `planner.md` | 서브태스크 기반 구현 계획 생성 |
| `coder.md` | 개별 서브태스크 구현 |
| `coder_recovery.md` | STUCK 태스크 복구 |
| `qa_reviewer.md` | 인수 조건 검증 |
| `qa_fixer.md` | QA 이슈 수정 |
| `spec_gatherer.md` | 사용자 요구사항 수집 |
| `spec_researcher.md` | 외부 연동 검증 |
| `spec_writer.md` | spec.md 문서 생성 |
| `spec_critic.md` | ultrathink로 셀프 비평 |
| `complexity_assessor.md` | AI 기반 복잡도 평가 |

---

## 실행 명령어 요약

```bash
cd apps/backend

# 1. Spec 생성 (대화형)
python spec_runner.py --interactive

# 2. Spec 생성 (태스크 직접 입력)
python spec_runner.py --task "로그인 기능 추가" --complexity standard

# 3. 자율 빌드 실행 (24/7 루프)
python run.py --spec 001

# 4. QA 검증
python run.py --spec 001 --qa

# 5. QA 상태 확인
python run.py --spec 001 --qa-status

# 6. 변경사항 확인
python run.py --spec 001 --review

# 7. 메인 브랜치로 병합
python run.py --spec 001 --merge

# 8. 빌드 삭제
python run.py --spec 001 --discard

# 9. 모든 spec 목록
python run.py --list
```

---

## Electron 앱 실행

```bash
# 개발 모드 (E2E 테스팅용 디버그 포트 포함)
npm run dev

# 프로덕션 빌드
npm start

# 패키징
npm run package:win   # Windows
npm run package:mac   # macOS
npm run package:linux # Linux
```

---

## 필수 요구사항

| 항목 | 요구사항 |
|------|---------|
| Claude 구독 | Pro 또는 Max 필수 |
| Claude Code CLI | `npm install -g @anthropic-ai/claude-code` |
| OAuth 토큰 | `claude` 실행 후 `/login` |
| Git | 프로젝트가 Git repo여야 함 |
| Python | 3.12+ |
| Node.js | 24.0+ (권장, 22.x도 동작함) |

---

## 핵심 관리자 클래스

| 클래스 | 역할 |
|--------|------|
| `RecoveryManager` | 메모리 지속성, 복구 관리 |
| `StatusManager` | ccstatusline 상태 업데이트 |
| `TaskLogger` | 영구 로그 기록 |
| `GraphitiMemory` | 세션 간 지식 그래프 |
| `SpecValidator` | 스펙/계획 유효성 검증 |

---

## 결론

Auto Claude는 **완전 자율 코딩 프레임워크**로:
- **Claude Agent SDK** 기반 (Anthropic API 직접 사용 X)
- Planner → Coder → QA → Fixer 루프가 **24/7 자동 실행**
- **E2E 테스팅** 지원 (Electron MCP via Chrome DevTools)
- **크로스 플랫폼** (Windows, macOS, Linux)
- 에러 발생 시 **자동 재시도**
- Git Worktree로 **안전한 격리 환경**
- Graphiti + LadybugDB로 **세션 간 학습** (Docker 불필요)
- Linear/GitHub **통합**
- 사용자는 최종 **리뷰 & 머지만** 하면 됨
