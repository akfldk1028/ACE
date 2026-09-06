# 프로젝트 에이전트

매스 파이프라인의 실행과 역할 정본은 **MassAgent/**에 둔다. ARR는 형상·법규 엔진과 산출물의 소유자다. 별도 위치에 같은 역할이나 숫자 규칙을 복제하지 않는다.

| 폴더 | 책임 |
|---|---|
| `MassAgent/` | 총괄 실행기. 아래 다섯 구성 요소를 한 사이클로 완주한다. |
| `MassAgent/agents/parti-author/` | 대지·프로그램의 질문을 LLM 저작 문장으로 번역한다. |
| `MassAgent/agents/book-author/` | BaseVolume 문법으로 BOOK payload를 직접 저작한다. |
| `MassAgent/agents/legal-auditor/` | 엔진 증거와 원문 법규를 대조하고 확인/미확인 범위를 기록한다. |
| `MassAgent/agents/juror/` | 익명 이미지와 고정 루브릭만 읽는 독립 VLM 배심원. 매회 별도 세션 3개. |
| `MassAgent/agents/developer/` | 판정에서 드러난 공간 문제를 수정하고 부모와 쌍비교한다. |
| `MassAgent/docs/` | 역할 계약, 작업 계획, 검증 보고. |

먼저 [AGENTS.md](AGENTS.md)의 HANDOFF → FLOW → 나머지 0번대 전부의 읽기 순서를 빠짐없이 따른다. 시작 문서: [MassAgent/MASSAGENT.md](MassAgent/MASSAGENT.md), [운영 계약](MassAgent/docs/agent-architecture.md).

실행은 `MassAgent` 디렉터리에서 `bash skills/mass-cycle/scripts/cycle.sh <round> [count] --agent-mode external` 하나다. LLM 저작·BOOK 탐색·BaseVolume 문법·VLM 배심·develop 중 하나라도 끝나지 않으면 사이클 완료가 아니다. 중간 단계 스크립트를 손으로 호출해 이어 붙이지 않는다.

사용자 지정 구조이므로 `.cursor/agents`나 개인 홈에 프로젝트 역할의 별도 사본을 만들지 않는다. MassAgent는 Git submodule이며 상위 저장소와 분리 커밋한다. upstream push 금지.
