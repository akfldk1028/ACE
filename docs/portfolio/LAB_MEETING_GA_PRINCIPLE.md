# 유전 알고리즘 기반 건축 매스 최적화 — 원리

**Lab Meeting · 5-Slide Presentation**
**Author**: DongHyeon KIM
**Date**: 2026-05-06

---

## 1. Why Genetic Algorithm?

건축 매스 디자인은 본질적으로 *다목적 trade-off* 문제다. 동일 부지 위에서도 **연면적**(법정 용적률 한도까지 채우려는 압력), **일조**(정북일조 사선 + 주변 건물 그림자), **이격**(인접대지 경계선·도로 경계선 후퇴), **조경 면적** 같은 지표가 서로 충돌한다. 어떤 매스는 면적을 최대화하지만 일조를 잃고, 어떤 매스는 일조를 확보하지만 연면적을 포기한다.

이런 문제는 **단일 최적해**가 존재하지 않는다. 그래서 *Pareto-optimal solution set* 을 탐색하는 접근이 필요하고, **NSGA-II(Non-dominated Sorting Genetic Algorithm II)** 가 그 표준 도구다. NSGA-II는 한 번의 실행으로 trade-off 곡선 전체를 제시하며, 사용자가 그 위에서 사업 목표에 맞는 후보를 직접 선택하도록 한다.

---

## 2. NSGA-II 작동 원리 (4단계 루프)

NSGA-II는 다음 네 단계를 30세대 동안 반복한다.

1. **Initialization** — Population 30개의 random genome을 생성한다. 각 genome은 매스 형태를 결정하는 실수 벡터다.
2. **Evaluation** — 각 genome을 polygon으로 디코딩한 뒤, 두 개의 목적함수(예: floor_area, daylight_score)로 평가한다.
3. **Non-dominated Sorting** — 모든 개체를 *지배 관계*에 따라 frontier로 분류한다. 어떤 개체도 모든 목적함수에서 더 우월하지 않은 개체들이 첫 번째 frontier(Pareto front)를 이룬다.
4. **Selection · Crossover · Mutation** — Crossover 0.9 + Mutation 0.1 비율로 다음 세대를 생성한다. *Crowding distance* 를 사용해 frontier 내에서도 다양성을 유지한다.

핵심 하이퍼파라미터: **Population 30, Generations 30, Crossover 0.9, Mutation 0.1.** 30 × 30 = 900회의 평가로 한 부지의 trade-off 공간을 안정적으로 도출한다.

---

## 3. Genome 설계 — 3종 매스 알고리즘

매스 형태마다 *서로 다른 gene encoding*을 사용한다. 모든 알고리즘은 마지막 4개의 **global gene**을 공유한다 — `num_floors`, `rotation`, `upper_scale`(상층부 축소율), `step_fraction`(단차 위치).

| 알고리즘 | Genome 길이 | 구조 | 강점 |
|----------|------------|------|------|
| **Additive (Box-Stacking)** | 29 genes | 5 boxes × 5 params (x, y, w, d, rotation) + 4 global | L자, T자, 불규칙형 |
| **Subtractive (Void Carving)** | 23 genes | 4 block params + 3 voids × 5 + 4 global | 중정형, ㅁ자, ㄷ자 |
| **Grid (3×3 Subdivision)** | 22 genes | 9 cells × 2 (on/off + height ratio) + 4 global | 격자형, 모듈식 |

디코딩은 모두 **Shapely Polygon** 위에서 수행된다. Additive는 `unary_union()` 으로 박스를 합성하고, Subtractive는 대지 bbox에서 `difference()` 로 void를 제거하며, Grid는 임계값을 넘는 셀만 활성화한 뒤 `unary_union()` 으로 통합한다. 알고리즘이 달라도 평가 단계는 동일한 BCR/FAR/daylight/setback 함수를 거치므로, *다른 형태의 매스를 같은 잣대로 비교*할 수 있다.

**Step-back 메커니즘**: `upper_scale < 0.98` 이면 `step_fraction` 위치에서 매스를 두 단으로 분리하고, 상층부를 centroid 기준으로 축소한다. 이 단순한 규칙 하나로 정북일조 사선에 대응하는 setback 매스를 자동 생성한다.

---

## 4. Multi-Objective Function — 용도별 동적 매핑

NSGA-II의 목적함수는 **용도지역과 건물 용도에 따라 동적으로 바뀐다**. 이는 단일 fitness 함수로 모든 부지를 평가하는 기존 GA 접근과의 핵심 차이다.

| 건물 용도 | Objective 1 | Objective 2 | 의미 |
|-----------|-------------|-------------|------|
| 주거·숙박·의료·교육 | `floor_area` | `daylight_score` | 채광 중시 |
| 상업·업무·공장·창고 | `floor_area` | `landscaping_pct` | 외부 공간 중시 |
| 문화시설 | `floor_area` | `setback` | 이격 중시 |

목적함수 매핑은 `_TYPE_OBJECTIVES` 테이블에서 관리되며, `constraint_bridge.py` 에서 `building_type` 입력에 따라 자동 선택된다. 동일한 매스 알고리즘이 *주거지역에서는 일조 우선, 상업지역에서는 조경 우선*으로 다른 Pareto front를 그린다는 뜻이다.

또한 **자동 제약조건 강화 루프**(Harness "생성-검증" 패턴)가 결합되어 있다. Pareto front 상위 N개 후보를 법규(BCR/FAR/높이/이격)와 대조 검증한 뒤, 위반 사항이 있으면 5% margin으로 constraint를 자동 강화하고 GA를 재실행한다. 결과적으로 *법규 통과*와 *목적함수 최적화*를 한 루프 안에서 수행한다.

---

## 5. Pareto Front · 결과와 시각화

30세대 동안 누적된 900개 평가의 결과는 **Pareto front 산점도**로 제시된다. 가로축은 floor_area, 세로축은 두 번째 목적함수(daylight 또는 landscaping 또는 setback)다. 단일 최적해가 아닌 *trade-off 곡선*을 사용자에게 직접 보여주는 것이 본 시스템의 의도다.

시각화는 AUA-style HSL rainbow 컬러 매핑을 사용한다. 세대 0은 blue(hue 240), 세대 30은 red(hue 0)으로 매핑되어 *수렴 과정 자체가 색의 그라데이션으로 드러난다*. Pareto 위의 점은 cyan→orange 그라데이션과 radial glow로 강조되고, infeasible solution은 hollow square로 구분 표시된다.

사용자는 Pareto front 위의 한 점을 클릭해 해당 매스를 3D 뷰에서 확인하고, 동일 부지에서 *면적 우선 vs 일조 우선*의 trade-off를 시각적으로 비교한다. 이 인터페이스가 NSGA-II의 핵심 기여 — *결정을 알고리즘이 아닌 사용자에게 위임* — 를 그대로 구현한 부분이다.

---

## 부록: 시스템 통합

- **Backend**: `ARR/backend/design/` — `mass_evaluator.py`, `constraint_bridge.py`, `regulation_validator.py`, `mass_renderer.py`
- **Frontend**: `ARR/frontend/src/design/` — Cesium 3D 뷰어, Canvas Pareto 차트, SSE 실시간 진행
- **API**: `POST /design/jobs/` (작업 생성+시작), `GET /design/jobs/<id>/stream/` (SSE 진행), `POST /design/jobs/<id>/validate/` (규제 검증 + 자동 강화)
- **테스트**: 116 Django tests (매스 57 + 평면 47 + validator 12)
- **원본**: AUA Discover 프레임워크 (Grasshopper Python 2.7 → Python 3.12 웹 포팅)

---

## 발표 톤 가이드

- 슬라이드 1: 문제 정의에서 시작 — *"왜 단일 최적해가 안 되는가"*
- 슬라이드 2: NSGA-II 4단계는 한 호흡에 — 청중이 GA 익숙하면 빠르게 통과
- 슬라이드 3: Genome 표가 핵심 — 알고리즘별로 *왜 다른 gene 길이를 썼는지* 강조
- 슬라이드 4: 동적 목적함수 매핑이 가장 큰 차별점 — *용도별로 다른 Pareto*
- 슬라이드 5: 결론은 *알고리즘이 결정하지 않고 사용자가 선택한다* — 이 한 문장으로 마무리
