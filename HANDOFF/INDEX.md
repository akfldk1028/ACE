# 25_ACE 프로젝트 핸드오프 문서

> **생성일**: 2026-02-06
> **목적**: 다음 AI가 프로젝트 컨텍스트를 빠르게 파악할 수 있도록 정리

---

## 빠른 시작

```bash
# AutoGen Studio 실행 (필수)
"C:/Users/SOGANG1/AppData/Roaming/Python/Python313/Scripts/autogenstudio.exe" ui --port 8081 --host 0.0.0.0

# 브라우저 접속
http://localhost:8081/
```

---

## 문서 목록

| # | 파일 | 설명 | 중요도 |
|---|------|------|--------|
| 1 | [01_PROJECT_OVERVIEW.md](./01_PROJECT_OVERVIEW.md) | 프로젝트 전체 구조 및 목표 | ★★★ |
| 2 | [02_JSON_MODULES.md](./02_JSON_MODULES.md) | JSON 모듈화 구조 (61개 파일) | ★★★ |
| 3 | [03_AUTOGEN_PATTERNS.md](./03_AUTOGEN_PATTERNS.md) | 14개 패턴 + Provider 매핑 | ★★★ |
| 4 | [04_TEST_RESULTS.md](./04_TEST_RESULTS.md) | Playwright E2E 테스트 결과 | ★★☆ |
| 5 | [05_AGENT_ARCHITECTURE.md](./05_AGENT_ARCHITECTURE.md) | 20 에이전트 아키텍처 | ★★☆ |
| 6 | [06_PENDING_TASKS.md](./06_PENDING_TASKS.md) | 남은 작업 목록 | ★★★ |

---

## 핵심 경로

```
D:\Data\25_ACE\
├── JSON_MODULES/           # ★ JSON 모듈 통합 폴더 (61개)
│   ├── patterns/           # 14개 패턴
│   ├── models/             # 7개 모델
│   ├── agents/             # 12개 에이전트
│   ├── teams/              # 20개 팀
│   └── README.md
│
├── AG/Auto-Claude/         # Auto-Claude CLI 소스
│   ├── src/                # 핵심 코드
│   └── tests/              # 테스트 (작성 중)
│
├── AG/autogen_a2a_kit/     # AutoGen + A2A 통합
│   └── AG_Cohub/           # 패턴 라이브러리
│
└── HANDOFF/                # ★ 이 폴더 (핸드오프 문서)
```

---

## 현재 상태 요약

### 완료됨 ✅
- JSON 모듈화 구조 정리 (61개 파일)
- AutoGen Studio UI 정상 작동 확인
- ClaudeCLIChatCompletionClient OAuth 작동 확인
- Sequential 패턴 테스트 (insights_agent 응답 확인)

### 진행 중 🔄
- Playwright E2E 테스트 (패턴별)
- Calculator 코드 생성 파이프라인

### 미완료 ❌
- Debate 패턴 테스트
- Reflection 패턴 테스트
- 전체 파이프라인 완료 (insights → coder → QA)
- Calculator 실제 파일 생성 검증

---

## 다음 AI 권장 작업

1. **Sequential 파이프라인 완료 실행**
   - Run #146 재실행 (Replay Run)
   - 전체 에이전트 협업 완료까지 대기
   - Calculator 코드 파일 생성 확인

2. **다른 패턴 테스트**
   - Debate 패턴 (SelectorGroupChat)
   - Reflection 패턴 (generator-critic)

3. **테스트 코드 작성**
   - `AG/Auto-Claude/tests/cli/` 단위 테스트
   - `AG/Auto-Claude/tests/e2e/` E2E 테스트

---

## 연락처 / 참조

- **AutoGen Studio**: http://localhost:8081/
- **API Health**: http://localhost:8081/api/health
- **Teams API**: http://localhost:8081/api/teams/?user_id=guestuser@gmail.com
