---
name: icce-basevolume-spec
description: "논문용 base volume(IR) 형식 명세 초안 — 코드 실물(form.py Placement / source_geometry/ir.py SourceVolume)에서 옮김. LaTeX 템플릿 도착 시 §Method의 IR 소절로 붙일 것. 요건: '교수님이 base volume 상세히 명시하라'(2026-08-31)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 825f1db0-1a1a-4dd8-a776-b763093bf569
  modified: 2026-08-31T10:38:05.302Z
---

## Base Volume IR — 논문 서술용 명세 (코드가 원본, 이 파일은 파생)

### 1. Placement (저작·실행 층의 원자) — `form.py`
하나의 매스는 Placement의 유한 집합. 각 Placement:

- **M ∈ R^{4×4}**: 아핀 포즈 행렬. 단위 입체 [0,1]³ → 세계 좌표. 회전·기울임(lean)·
  비균등 스케일을 전부 M이 담당 (테스트 `test_maas_affine_matrix_exactness.py`가
  비트 단위 정확성 보증).
- **plan ∈ P**: 단위 평면 가족 이름 (square·triangular·trapezoidal·chamfered·kite·oval·
  stadium·concave_l·hexagon·faceted — `profiles.plan_names()`가 소유, 원 반쪽 등 절단
  파생 평면은 `cut_plan`이 이름으로 등록). "쐐기와 원은 변환이 아니라 다른 기저 형상 —
  어떤 행렬도 한 평면을 다른 평면으로 못 바꾼다."
- **kind ∈ {additive, subtractive}**: 몸/절삭.
- **occupiable ∈ {0,1}**: 방인가, 방을 받치는 구조인가. 게이트(2.4m 유효깊이 방 규칙)의
  분기 스위치. canopy·lift 다리가 false를 씀.
- **단면 항 (한 축 프로파일 IR)** — 프리즘 언어가 지붕을 말하게 한 핵심:
  - `top_drop ∈ [0,1]`: 윗면이 자기 높이의 이 몫만큼 떨어짐 (0 = 평지붕 프리즘)
  - `drop_toward ∈ S¹`: 한 방향 셰드 (세계 단위벡터)
  - `ridge_along ∈ S¹`: 용마루 선 — 양쪽으로 낙하하는 집 단면을 **한 볼륨**으로
    (반쪽 쐐기 2개 조립은 후속 변환에서 용마루가 벌어져 실패했던 이력 포함)
  - `top_profile = ((s_i, h_i))_i, s,h ∈ [0,1]`: `profile_across` 축 위 꺾은선 높이장 —
    셰드·박공은 특수 경우, saltbox·mansard·butterfly·fold(2n+1점)·vault(17점 샘플 곡선)가
    일반 경우. 점수 > MAX_CREASED_PROFILE_POINTS(8)이면 샘플 곡선으로 읽어 이음선을
    안 그림. top_drop = 1−min(h)를 항상 동반해 "기울었는가" 게이트가 한 필드만 읽음.

### 2. SourceVolume (컴파일 층의 원자) — `source_geometry/ir.py`
컴파일러가 Placement 집합을 **수평 밴드**로 절단한 결과. 각 밴드:
role / footprint(Shapely Polygon, 구멍 = 중정) / bottom·top_fraction(전체 높이 대비) /
verb(만든 동사) / 단면 항 승계(top_drop·drop_toward·ridge_along·top_profile·profile_across).
법규 산정은 항상 **풀 프리즘**(기운 윗면 무시) — 엄격한 쪽으로 읽음.
`structural_bands` 메타데이터: occupiable=false만 있는 밴드 목록 → 방 게이트 면제 채널.

### 3. 논문에서 강조할 설계 논거 3개
1. **동사 = 행렬 위의 연산자**: 37동사가 M·plan·단면 항만 조작 → 결정적·재현 가능·
   법규 검증 가능 (생성형 메시 대비 차별점).
2. **단면은 조립이 아니라 기저 항**: 지붕을 계단 근사(5계단 0.29 → 24계단 0.09로 악화
   실측)나 반쪽 조립(변환에 찢어짐)이 아닌 IR 항으로 — "A section is a base shape,
   not an assembly."
3. **occupiable 비트 하나가 게이트 체계를 관통**: 방 규칙·구조 면제·plausibility가
   전부 이 스위치를 읽음 — canopy(얇은 판) 어휘가 IR 변경 없이 성립한 이유.

한계(정직 서술용): 프로파일은 한 축 — 힙(2축) 불가. 자유곡면 평면 불가(샘플 다각형까지).
관련: [[icce-asia-2026-massv2-paper]]
