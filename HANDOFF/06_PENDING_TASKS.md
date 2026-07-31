# 06. 남은 작업 목록

## 우선순위 1: 패턴 테스트 완료

### 1.1 Sequential 파이프라인 완료 실행
```
상태: 🔄 진행 중 (첫 에이전트만 완료)
예상 시간: 5-10분
```

**작업 내용**:
1. AutoGen Studio 접속: http://localhost:8081/
2. Run #146 찾기 (또는 "Replay Run" 클릭)
3. 전체 파이프라인 완료까지 대기
4. 결과 확인: 8개 에이전트 모두 응답했는지
5. Calculator 코드 파일 생성 확인

**검증 항목**:
- [ ] insights_agent 응답 ✅ (완료됨)
- [ ] deep_research_agent 응답
- [ ] spec_writer_agent 응답
- [ ] planner_agent 응답
- [ ] coder_agent 응답 (실제 코드 생성)
- [ ] qa_reviewer_agent 응답
- [ ] qa_fixer_agent 응답
- [ ] TERMINATE로 종료

---

### 1.2 Debate 패턴 테스트
```
상태: ❌ 미시작
예상 시간: 3-5분
```

**작업 내용**:
1. New Session 클릭
2. 팀 선택: "Multi-Agent Debate" 또는 "Debate Team"
3. 메시지 입력: "Python 계산기 앱의 장단점을 토론해줘"
4. 에이전트 간 토론 관찰

**검증 항목**:
- [ ] Advocate (찬성) 발언
- [ ] Critic (반대) 발언
- [ ] Judge (판정) 최종 결론
- [ ] SelectorGroupChat 작동 확인

---

### 1.3 Reflection 패턴 테스트
```
상태: ❌ 미시작
예상 시간: 3-5분
```

**작업 내용**:
1. New Session 클릭
2. 팀 선택: "Reflection Pattern" 또는 "Reflection Team"
3. 메시지 입력: "Python 계산기 함수를 작성해줘"
4. Generator-Critic 루프 관찰

**검증 항목**:
- [ ] Generator 초기 결과 생성
- [ ] Critic 피드백 제공
- [ ] Generator 개선된 결과 생성
- [ ] Critic "APPROVED" 출력으로 종료

---

## 우선순위 2: 코드 생성 검증

### 2.1 Calculator 파일 생성 확인
```
상태: ❌ 미시작
조건: Sequential 파이프라인 완료 후
```

**작업 내용**:
1. `D:\Data\25_ACE\Calculator\` 디렉토리 확인
2. 생성된 파일 목록 확인

**예상 파일**:
```
Calculator/
├── main.py         # 메인 진입점
├── operations.py   # 사칙연산 로직
├── parser.py       # 입력 파싱
├── ui.py           # CLI 인터페이스
└── README.md       # 문서
```

**검증 항목**:
- [ ] 디렉토리 존재
- [ ] 3개 이상 파일 (모놀리스 아님)
- [ ] 각 파일 500줄 미만
- [ ] cross-module import 존재
- [ ] 실행 가능 (`python main.py`)

---

## 우선순위 3: 테스트 코드 작성

### 3.1 CLI 단위 테스트
```
위치: AG/Auto-Claude/tests/cli/
상태: ❌ 미시작
```

**생성할 파일**:
| 파일 | 대상 | 테스트 수 |
|------|------|----------|
| conftest.py | 공통 fixtures | - |
| test_models.py | src/utils/models.py | ~15 |
| test_task_queue.py | src/coordinator/task_queue.py | ~25 |
| test_capabilities.py | src/registry/capabilities.py | ~15 |
| test_auto_claude_oauth.py | OAuth 토큰 관리 | ~20 |

---

### 3.2 E2E 테스트
```
위치: AG/Auto-Claude/tests/e2e/
상태: ❌ 미시작
```

**생성할 파일**:
| 파일 | 내용 |
|------|------|
| test_autogen_studio_full.py | Playwright Gallery/Team/협업 |
| test_code_modularization.py | Calculator 출력 구조 검증 |

---

## 명령어 참조

### AutoGen Studio 시작
```bash
"C:/Users/SOGANG1/AppData/Roaming/Python/Python313/Scripts/autogenstudio.exe" ui --port 8081 --host 0.0.0.0
```

### API 테스트
```bash
# 헬스 체크
curl http://localhost:8081/api/health

# 세션 목록
curl "http://localhost:8081/api/sessions/?user_id=guestuser@gmail.com"

# 팀 정보
curl "http://localhost:8081/api/teams/37?user_id=guestuser@gmail.com"
```

### Playwright MCP 도구
```
mcp__playwright__browser_navigate  # 페이지 이동
mcp__playwright__browser_snapshot  # 스냅샷 (접근성 트리)
mcp__playwright__browser_click     # 클릭
mcp__playwright__browser_fill_form # 폼 입력
mcp__playwright__browser_take_screenshot # 스크린샷
```

---

## 참고 파일

| 파일 | 설명 |
|------|------|
| `AG/Auto-Claude/tests/conftest.py` | 기존 fixtures (1144줄) |
| `AG/Auto-Claude/src/utils/models.py` | Pydantic 모델 (303줄) |
| `AG/Auto-Claude/src/registry/capabilities.py` | 에이전트 레지스트리 (689줄) |
| `JSON_MODULES/README.md` | JSON 모듈 구조 설명 |

---

## 체크리스트 요약

### 필수 (교수님 요구사항)
- [ ] 각 패턴이 제대로 동작하는지 확인
- [ ] 모듈화된 코드 생성 확인
- [ ] JSON 모듈화 구조 문서화 ✅

### 선택
- [ ] 전체 테스트 코드 작성
- [ ] 다른 A2A 에이전트 테스트
- [ ] Git 커밋 및 PR 생성
