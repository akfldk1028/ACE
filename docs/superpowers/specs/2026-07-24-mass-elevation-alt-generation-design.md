# MASS 10개와 MASS별 생성형 입면 검증 설계

## 목표

서로 다른 건축 MASS 10개를 실제 Geometry Program으로 생성하고, 각
MASS의 정확한 형상 조건을 보존하는 생성형 입면 ALT를 한 장씩 만든다.
이번 검증의 유료 이미지 호출 상한은 10회다. 결과가 좋은 MASS에 대한
추가 ALT 생성은 이번 범위에 포함하지 않는다.

## 범위

- 새 `fresh_synthesis` MASS 10개
- MASS마다 독립 Geometry Program, program hash, geometry hash, PNG,
  passport, graph trace
- MASS마다 기술 입면 condition pack
- MASS마다 유료 생성형 입면 ALT 1개
- 프론트엔드에서 MASS를 클릭하면 해당 기술 입면과 생성형 ALT 표시
- 생성 실패 시 자동 유료 재시도 없음
- 포트폴리오 VLM, 보드 평가, 추가 입면 ALT는 제외

## MASS 생성

모든 형상은 하나의 `1/1 UnitBox`에서 시작한다. 크기·위치·회전·전단은
동차좌표 Matrix4로 표현하고, BOOK 언어와 재귀 Geometry Macro가 그 뒤를
잇는다. 10개는 최소한 다음과 같이 다른 공간 관계를 가져야 한다.

1. 휘어진 긴 매스
2. 열린 중정 매스
3. 십자 또는 방사형 날개
4. 계단식 setback
5. taper 또는 leaning tower
6. 대각 절단 매스
7. 면 부착형 매스
8. 변화하는 단면의 profiled span
9. split-wing 또는 bridge
10. nested 또는 offset composition

후보는 문법 검증, 참조 무결성, 양수 치수, closed/watertight/manifold,
self-intersection, 연결 컴포넌트, bounding box를 통과해야 한다.
program hash와 geometry hash가 모두 달라야 한다. 동일 해시, 거의 같은
실루엣, 찢어진 조각, 건축 스케일로 읽히지 않는 후보는 무료 로컬
단계에서 폐기하고 다른 variation으로 보충한다.

## 입면 조건팩

`elevationAgent`는 MASS mesh를 다시 설계하지 않는다. 다음의 구조화된
조건팩만 만든다.

- MASS program hash와 geometry hash
- front, rear, left, right, axon 기술 뷰
- silhouette mask와 depth
- 각 외피 face의 normal, 면적, 방향, 층 밴드
- 개구 가능 영역과 solid 유지 영역
- 중정, 캔틸레버 하부, 코어 및 접지부 보호 mask
- 프로그램 용도와 채광 방향
- 선택된 입면 재료 전략

모든 좌표는 해당 MASS의 evaluated bounds 및 face-local 좌표를 사용한다.
고정된 세계좌표나 MASS별 숫자 하드코딩을 금지한다.

## MASS별 입면 전략

10개에 동일한 커튼월을 반복하지 않는다. `elevationAgent`는 형상과 방향을
보고 유리 커튼월, 불투명 패널, 수직 루버, 수평 차양, 깊은 개구부,
테라코타/금속/노출 콘크리트 및 혼합 외피 중 하나의 주전략을 고른다.
선택 근거는 condition pack과 함께 저장한다.

생성형 Image Agent는 기술 뷰, silhouette mask, depth와 재료 전략을 입력으로
받는다. 입면 재료·개구 리듬·깊이만 생성할 수 있고 MASS의 외곽선, 높이,
setback, 중정, bridge, cantilever를 변경할 수 없다.

## 유료 호출 정책

- MASS당 생성형 입면 호출 정확히 1회
- 전체 상한 10회
- 네트워크 오류를 포함해 자동 재시도 없음
- 응답 ID, 모델, 입력 이미지 hash, 프롬프트 버전, 비용 사용량을 기록
- 실패는 실패 카드로 남기고 다른 MASS의 호출을 계속
- 생성된 이미지를 통과로 간주하지 않으며, 형상 보존 검사는 별도 기록

## 프론트엔드

하단에는 최신 MASS 10개가 시간순으로 나온다. 카드를 클릭하면 하나의
그래프에서 다음 경로만 강조한다.

`1/1 UnitBox → Matrix4 → BOOK → Geometry AST → Compiler/GATE → MASS PNG
→ elevationAgent condition pack → Image Agent → elevation ALT 01`

오른쪽 패널은 선택된 MASS의 실제 MASS PNG, 기술 입면, 생성형 입면 ALT,
형상 보존 상태, 실행 ID를 표시한다. 다른 MASS의 입면을 섞어 표시하지
않는다.

## 실패 처리

- Geometry GATE 실패: 유료 호출 전에 폐기하고 무료 후보 보충
- 중복 형상: 유료 호출 전에 폐기
- condition pack 불완전: 해당 MASS 유료 호출 차단
- 이미지 생성 실패: 자동 재시도 없이 실패 기록
- 이미지 형상 보존 불명확: `needs_review`; 승인으로 표시하지 않음
- 프론트 이미지 로드 실패: 해당 artifact와 API 경로를 오류 카드로 표시

## 검증 기준

- 새 MASS 10개, geometry hash 10개, program hash 10개
- 최소 10개 형상군 및 실루엣 중복 검사 통과
- 모든 MASS Geometry GATE 통과
- condition pack 10개가 각 geometry hash에 정확히 결합
- 유료 이미지 호출 10회 이하
- 프론트에서 최신 MASS 10개와 MASS별 ALT 매핑 확인
- MASS 카드 10개를 순회하며 이미지 로드, 선택 그래프, 콘솔 오류 확인
- 법규·주차·대지·VLM 미평가는 승인으로 표시하지 않음
