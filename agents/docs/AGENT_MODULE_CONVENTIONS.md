# Agent folder & module conventions (2026-09-24)

한 소유자 문서. 각 에이전트의 `docs/STRUCTURE.md`는 이 문서를 **자기 폴더에 대조한 결과**만 적는다
(무엇이 맞고 무엇이 빠졌는지). 규칙을 여기서 복사해 가지 않는다.

## 1. 무엇을 조사했나 (2026-09-24 실제로 읽은 것)

| 출처 | 제안 구조 | 우리에게 남는 것 |
|---|---|---|
| LangGraph application structure ([docs.langchain.com](https://docs.langchain.com/langgraph-platform/application-structure)) | `my_agent/{agent.py, utils/{tools,nodes,state}.py}` + `langgraph.json` + `.env` + `requirements.txt` | **그래프 구성(agent.py) / 노드 / 도구 / 상태를 파일로 분리**. 배포 매니페스트가 그래프·의존성·env를 한 파일에 선언 |
| Google agents-cli / ADK ([google.github.io/agents-cli](https://google.github.io/agents-cli/guide/project-structure/)) | `app/{__init__,agent,fast_api_app}.py`, `app/app_utils/{services,a2a}.py`, `tests/{unit,integration,eval}/`, `pyproject.toml`, `GEMINI.md`, `Makefile`, `.env` | **에이전트 정의와 HTTP/A2A 서버를 다른 파일에**; 테스트를 unit / integration / **eval**로 3분; 코딩 에이전트용 안내 파일(GEMINI.md ≈ 우리 `<AGENT>.md`) |
| better-agents ([langwatch/better-agents STRUCTURE.md](https://github.com/langwatch/better-agents/blob/main/docs/STRUCTURE.md)) | `app|src/`, `tests/{evaluations,scenarios}/`, `prompts/` + `prompts.json`, `AGENTS.md`, `CLAUDE.md`, `.mcp.json` | **프롬프트는 버전 관리되는 별도 파일**; 시나리오(end-to-end 대화) 테스트를 평가 노트북과 구분 |
| LangChain Managed Deep Agents ([docs.langchain.com](https://docs.langchain.com/langsmith/python/managed-deep-agents-project-structure)) | `agent.py`, `instructions.md`, `skills/*/SKILL.md`, `tools/`, `channels/`, `sandbox/`, `evals/` | **시스템 프롬프트는 `instructions.md`**, 작업별 지시는 `skills/`; 도구는 평범한 모듈 |
| A2A python samples ([a2a-samples](https://github.com/a2aproject/a2a-samples/tree/main/samples/python/agents)) | `app/__main__.py`(서버 진입), `agent.py`, `agent_executor.py`, `test_client.py`, `pyproject.toml`, `.env` | **진입점 / 에이전트 로직 / A2A 실행기 3분리** — 우리 `a2a_service/{server,protocol,tools}.py`와 같은 골격 |
| 12-Factor Agents ([humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)) | 원칙 12개 | 4 *tools are structured outputs*, 5 *unify execution state and business state*, 8 *own your control flow*, 10 *small, focused agents*, 12 *stateless reducer* |
| Python packaging: src vs flat layout ([packaging.python.org](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)) | `src/pkg/` vs `pkg/` | 테스트가 로컬 복사본을 몰래 임포트하는 함정. 우리는 flat + `sys.path` 삽입이라 **`paths.py` 한 곳**이 그 역할을 대신한다 |
| dev.to "clean folder structure for real agent systems" ([dev.to](https://dev.to/raju_dandigam/stop-messy-ai-projects-a-clean-folder-structure-for-real-agent-systems-502f)) | `src/{agents,tools,memory,workflows,mcp,prompts,middleware,types}` | 도구는 **명시적 경계층**(등록된 도구만 호출 가능); 워크플로(조정)와 실행을 분리; 미들웨어(로깅·추적·예산)는 별도 층 |

공통분모는 넷이다: **① 로직·전송·진입점 분리, ② 도구는 구조화된 입출력이 있는 얇은 경계, ③ 테스트를 단위/통합(와이어)/평가로 나눔, ④ 프롬프트와 설정은 코드 밖.**

## 2. 이 저장소에 이미 있는 골격 (바꾸지 않는다)

에이전트 하나 = 저장소 하나(nested git, origin은 gitagent 템플릿, push 금지).

```
<Agent>/
├── <agent>agent/          규칙 패키지 — 이 에이전트가 소유한 판단. 전송을 모른다.
│   └── paths.py           (필요할 때만) 바깥 세계 위치를 아는 유일한 파일
├── a2a_service/           전송만. server.py(진입·카드) / protocol.py(공유 어댑터) / tools.py(도구 표면·인자 정책)
├── mcp/                   (있으면) 같은 TOOLS 표를 MCP로 노출 — 도구 표는 한 곳
├── config/<agent>.env     포트·URL·외부 서비스 — 값은 여기, 규칙은 아니다
├── tests/                 단위(규칙) / 와이어(실물 도구 출력을 Orchestrator normalize_reply에 통과) / 골든셋
├── docs/                  계약·조사·구현 기록(날짜 붙임), STRUCTURE.md(이 문서와의 대조)
├── memory/MEMORY.md       진입점: 최신 절이 맨 위, 이전 절은 역사. 큰 결정은 memory/decisions/
├── scripts/               serve-a2a.sh, verify_*.py — 실행과 재현
├── runs/ runtime/         산출물, git 밖
├── SOUL.md RULES.md       LLM 프런트엔드용 지시(=instructions.md). 결정론 규칙은 여기 두지 않는다
└── <AGENT>.md             사람과 코딩 에이전트가 먼저 읽는 역할 경계(=GEMINI.md/AGENTS.md)
```

`OrchestratorAgent`는 `orchestrator/`가 규칙 패키지이고 그래프(`graph.py`) / 노드 흐름(`*_flow.py`) /
어댑터(`adapters/`) / 계약(`contracts.py`, `policy.py`)로 이미 LangGraph식 분리를 하고 있다.

## 3. 모듈 규칙 (이번에 확정)

1. **규칙 패키지는 전송을 임포트하지 않는다.** `a2a_service/tools.py`가 규칙을 부르지, 반대는 없다.
   MCP·CLI·A2A는 같은 `TOOLS` 표를 본다(ProgramAgent `program_tools.TOOLS`가 예).
2. **파일은 ~500줄 아래, 나눌 때는 크기가 아니라 책임으로.** 레지스트리는 "조회/카탈로그"와
   "데이터(레시피)"로, 데이터는 **조사 배치(=출처 묶음)당 파일 하나**로(`typologies_base / _ext / _ext_ab`).
   500을 넘는 파일에 **더하기 전에** 쪼갠다, 더한 뒤가 아니라.
3. **한 사실은 한 파일이 소유한다.** 별칭 표·소유권 지도·포트 번호를 두 번 적지 않는다. 파생은 코드로
   (`registry.profiles()`가 `policy.OWNERS`에서 파생하듯).
4. **바깥 세계는 `paths.py`/`config/*.env` 한 곳.** `sys.path.insert`가 여러 파일에 흩어지면
   src-layout이 막아 주는 "로컬 복사본 몰래 임포트"가 그대로 돌아온다.
5. **출처가 있는 데이터는 출처 레코드와 같은 배치 파일에.** 읽은 범위·날짜·검증 수준(`read` /
   `abstract_only`)을 기록하고, 출처의 숫자는 기본값이 아니라 노트로.
6. **테스트 세 켜.** `tests/test_<rules>.py`(순수 규칙), `test_*_wire.py`(실물 도구 출력이 상대
   에이전트의 검증기를 통과하는지 — 가짜 caller는 이 결함을 못 잡았다), 골든셋(`*_golden_cases.json`).
7. **12-factor 대응:** 도구 응답은 JSON 봉투(4) · 상태는 Orchestrator 스토어 한 곳, 도구는
   무상태(5·12) · 제어 흐름은 `graph.py`가 소유하고 owner는 소견을 낼 뿐(8) · 한 owner 한 슬라이스(10).
8. **프롬프트는 코드 밖**: `SOUL.md`/`RULES.md`/`skills/*/SKILL.md`. 결정론 규칙을 프롬프트에 적지 말고,
   프롬프트를 파이썬 문자열에 박지 않는다.

## 4. 알려진 공통 잔재 (지우지 않았다 — 사용자 결정)

gitagent 템플릿에서 온 `rust/`, `src/`(TS), `test/`(TS), `package*.json`, `tsconfig.json`,
`GitAgent_Redesigned.pptx`, `gitagent-logo.png`, `gaps.md`, `Documentation.md`, `install.sh`,
`skills/gmail-email/`, `README.md`(gitagent 것)가 모든 에이전트에 있다. 이 저장소의 실물은
`<agent>agent/`·`a2a_service/`·`tests/`·`docs/`·`memory/`뿐이다. 각 `STRUCTURE.md`가 그 목록을 든다.
