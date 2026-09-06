# 프로젝트 에이전트 시작 지침

이 파일의 범위는 `agents/`다. 매스 작업의 지속 역할·스킬·운영 기록은 `MassAgent/`에 두고, ARR는 형상·법규 엔진과 실제 산출물을 소유한다. 개인 홈이나 다른 에이전트 폴더에 같은 역할·수치 규칙을 복제하지 않는다.

## 읽는 순서

1. [HANDOFF](../ARR/backend/tmp_mass_check/_massv2/HANDOFF.md): 현재 상태와 이어서 할 일.
2. [FLOW](../ARR/backend/tmp_mass_check/_massv2/FLOW.md): 생산 흐름과 반드시 함께 완료할 구성 요소.
3. HANDOFF의 **0번대 문서 표**에 지정된 나머지 문서를 빠짐없이 순서대로 전부 읽는다. 문서부터 확인하고, 2·3·4번대 코드는 해당 구현을 수정·검증할 때 필요한 부분만 읽는다.
4. [MassAgent 시작 안내](MassAgent/MASSAGENT.md), [역할·운영 계약](MassAgent/docs/agent-architecture.md), 해당 스킬과 역할 지침.

문서에 과거 승인 대기 상태가 남아 있어도 현재 대화에서 이미 받은 사용자 승인과 선호를 먼저 적용한다. 승인된 수정·검증·복구를 다시 허락받기 위해 멈추지 않는다. 범위를 벗어나는 새 외부 발송·공개·파괴적 작업은 별도 요청으로 취급한다.

## 생산과 책임

사용자의 지속 요구는 [공통 서비스 요구사항](MassAgent/docs/user-requirements.md)에 저장한다. 여러 대지에 적용되는 건축 매스 서비스이며 운영 프롬프트는 영어다. 각 alt는 필요한 원리/조작 1~3개만 사용해도 되지만 전체 BOOK 선택 범위와 필수 다섯 단계의 흐름은 모두 작동해야 한다. 모든 어휘를 한 alt에 강제하지 않는다.

생산 시작·재개는 MassAgent 디렉터리에서 `bash skills/mass-cycle/scripts/cycle.sh <round> [count]` 하나로 한다. LLM 문장 저작, 실제 BOOK payload 탐색, BaseVolume 문법, 독립 VLM 배심, 쌍비교·채점·피드백을 마친 develop이 모두 있어야 완료다. 개별 단계 스크립트를 손으로 이어 실행하지 않는다.

Exit 75는 외부 저작/배심 체크포인트다. `pending.json`의 지정 파일을 채운 뒤 **동일 명령과 동일 구성**으로 재개한다. `--from`은 완료 영수증을 건너뛰는 옵션이며 누락 단계를 대신하지 않는다. 구체적 옵션·복구 범위는 [mass-cycle](MassAgent/skills/mass-cycle/SKILL.md)이 안내하고 실행 코드는 [cycle.py](MassAgent/skills/mass-cycle/scripts/cycle.py)가 소유한다.

배심원은 매회 새 독립 컨텍스트에서 자기 private 폴더의 고정 PROMPT와 익명 이미지만 읽는다. key, 기존 점수, 다른 배심원의 판정, 저자 설명과 공유 메모리를 전달하지 않는다. 엔진 변경은 baseline 보존 → 재굽기·픽셀 비교 → 변경 형상 재스테이징·재심사로 검증하고, 큰 변경은 새 era에서 BOOK도 복원한다.

법규·형상 임계값과 기본값을 이 문서나 스킬에 수동 복제하지 않는다. [단일 코드 소유자 목록](MassAgent/docs/agent-architecture.md#코드와-구성의-단일-소유자)을 따른다. 예쁜 그림이나 자체 점수는 법규 증거가 아니다.

MassAgent는 상위 저장소와 분리된 Git submodule이다. 사용자 작업과 담당 범위를 보존하고, 커밋이 승인된 작업이면 상위와 submodule을 나눠 처리한다. **upstream push는 하지 않는다.**
