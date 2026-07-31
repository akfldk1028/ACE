# 더 나은 방향 추천 — 단기/중기/장기

**작성일**: 2026-04-30
**대상 발표**: 2026-05-06 랩미팅
**근거**: `04_SOTA_COMPARISON.md` + `05_OUR_POSITION.md` 정직 평가
**원칙**: 구체적 작업량 + 인용 논문 + 우리 코드 적용 위치까지 명시

---

## (a) 단기 보완 — 1-2주 작업

### A1. NSGA-III 추가 구현 ★ 1순위

**왜?**
- many-objective(4+)로 확장 시 NSGA-II의 crowding distance가 무력화됨
- 발표에서 교수님 가장 흔한 질문 = "NSGA-III는 안 써봤나?"에 즉답 가능
- 학계 응용 검증: Zhao+ 2022 dormitory에서 에너지 +41.27%, 일조 +42.24%

**구체 작업** (1주):
```python
# ARR/backend/design/engine/objects.py 에 NSGA3Job 클래스 추가
# 또는 pymoo 라이브러리 통합:
#   from pymoo.algorithms.moo.nsga3 import NSGA3
#   from pymoo.util.ref_dirs import get_reference_directions
```
- pymoo 통합 (이미 검증된 NSGA-III 구현 있음)
- reference points: Das-Dennis 또는 Riesz energy
- objectives 4-5개 (BCR/FAR/일조/이격/조경)로 확장 테스트

**참고 논문**:
- Deb & Jain 2014 IEEE TEC 18(4):577-601
- Zhao+ 2022 Applied Energy 305: PCA-ANN integrated NSGA-III for dormitory
  - URL: https://ideas.repec.org/a/eee/appene/v305y2022ics0306261921011569.html

**예상 효과**: 발표에서 "NSGA-II → NSGA-III 비교 실험까지 했음" 차별점

---

### A2. Radiance 일조 시뮬레이션 통합 (lite) ★ 2순위

**왜?**
- 현재 우리 "일조 평가"는 정북일조선 *envelope* 기하학적 검증일 뿐 (= 법규 준수만)
- 학계 표준은 Radiance/Daysim으로 UDI/sDA/일사량 *실제 시뮬레이션*
- 교수님이 "이 일조 평가가 의미있나?" 물었을 때 단호한 답 가능

**구체 작업** (1주):
```python
# ARR/backend/design/services/mass_evaluator.py 에 추가
# pyradiance 또는 honeybee-radiance 통합
# 평가: 매스마다 Radiance 시뮬 (~30초/매스) → BO+Surrogate 필요
```
- 평가 함수 업그레이드: 단순 BCR/FAR → UDI(Useful Daylight Illuminance)
- 시뮬 비용 큰 만큼 Surrogate Model 도입 검토 트리거

**참고 논문**:
- Lou+ 2025 Sci. Rep. 15:26644 (UDI +19.85%)
- 한국 건축법 정북일조 vs 실제 일조량 차이 명시 가능

**현실 제약**: Radiance 실행시간 = GA 비실용화 → A3와 결합 필요

---

### A3. Constraint Penalty 정교화

**왜?**
- 현재 `Design.set_outputs()`의 penalty는 violation 1개당 +1 (단순 카운트)
- 학계 표준: `g(x) ≤ 0` 위반 정도(magnitude)에 비례한 penalty
- Wang & Janssen 2018 (Semantic Scholar) 제약 처리 비교 분석에 따른 권장

**구체 작업** (3일):
```python
# ARR/backend/design/engine/objects.py:189-205 수정
# 현재: self.penalty += 1
# 개선: self.penalty += max(0, _o - goal_val) / goal_val  (정규화 violation)
```

**참고 논문**: Wang & Janssen 2018 — Constraint Handling Strategies in Architectural EA

---

## (b) 중기 개선 — 1-2개월 작업

### B1. Bayesian Optimization + GP/CNN Surrogate 통합 ★

**왜?**
- A2에서 Radiance 통합하면 GA가 비실용화 (1매스 30초 × 30 indiv × 50 gen = 12.5시간)
- BO+Surrogate가 50-200 평가로 동등 결과 도달
- Tian+ 2025 *Energy & Buildings* (S0360132325003464): GAN surrogate + DRL 사례

**구체 작업** (1개월):
- Step 1: GA로 1000+ 매스 + Radiance 결과 데이터셋 생성
- Step 2: CNN/GP surrogate 학습 (input=29 genes, output=UDI/sDA)
- Step 3: BO acquisition function (EI/UCB) + surrogate로 search
- Step 4: 검증: surrogate-BO vs GA 동등 결과 도달 횟수 비교

**참고 논문**:
- Westermann & Evins 2019 *Energy & Buildings*: surrogate review
- Zhang+ 2020 J. Building Performance Simulation
- Tian+ 2025 *Energy & Buildings* — GAN+DRL embedded

**예상 효과**: 평가 효율 50-100배. 발표 다음 라운드의 main topic.

---

### B2. NSGA-II + SSIEA Hybrid (Island Heterogeneous EA)

**왜?**
- 현재 우리 SSIEA의 모든 island가 동일 알고리즘 → 알고리즘 다양성 결여
- 학계 hybrid trend: island별 다른 algorithm (NSGA-II + SSIEA + DE)
- 더 broad search → Pareto front 다양성 향상

**구체 작업** (3주):
- `SSIEAJob`을 `HeterogeneousIslandJob`로 일반화
- island마다 algorithm config 다르게 (NSGA-II / SSIEA / DE / CMA-ES)
- migration 시 algorithm-aware 전환

**참고 논문**:
- Wang+ 2020 SSIEA AI EDAM (island model 원전)
- 추가 검색 필요: heterogeneous island MOEA

---

### B3. Mass Typology + Surrogate-Guided Search

**왜?**
- 현재 매스 인코딩 10종이 hardcoded — 사용자가 typology 선택 후 GA
- Wang+ 2024 *Frontiers* (S2095263524000797): typology-oriented 자동 선택
- typology 선택 자체를 meta-learning으로

**구체 작업** (1개월):
- 부지 특성(면적/방향/주변 건물) → 최적 typology 추천 surrogate
- 사용자 input 줄여 자동화 강화

**참고 논문**: Wang et al. 2024 Frontiers of Architectural Research, EvoMass typology

---

## (c) 장기 비전 — 6개월+ 작업

### C1. GA → DRL Bootstrap Hybrid

**왜?**
- GA는 새 부지마다 처음부터 시작 (no generalization)
- DRL은 학습 후 추론 매우 빠름, 그러나 reward shaping 어려움
- **Hybrid**: GA가 도출한 Pareto front를 DRL training data로 → 새 부지 zero-shot

**구체 작업** (4-6개월):
- Phase 1: 1000+ 부지에 대해 GA 실행 → (부지 특징, 최적 매스) 데이터셋
- Phase 2: Imitation Learning (BC/GAIL)으로 policy 부트스트랩
- Phase 3: PPO/MADDPG로 fine-tune (실제 법규 reward로)
- Phase 4: 새 PNU 입력 → policy 추론 (~ms) → GA 검증

**참고 논문**:
- Chen+ 2024 *Automation in Construction* (S0926580524004382): MADDPG renovation
- Tian+ 2025 *Energy & Buildings* (S0360132325003464): GAN surrogate + DRL
- SpaceLayoutGym (2024): RL agent layout via wall placement
- Wang+ 2024 *J. Computational Design and Engineering* qwae109

**예상 효과**: 부지→매스 30초 → ms 단위. 실시간 도시계획 시뮬레이터 가능.

---

### C2. Diffusion Model Mass Prior + GA Refinement

**왜?**
- GA는 random init → 초반 generation 낭비
- Diffusion이 학습된 prior로 "그럴듯한" 초기 매스 sample → GA가 그 위에서 fine-tune
- 학계 trend: DM as initialization for optimization (Tsai 2025 WACV)

**구체 작업** (4-6개월):
- Phase 1: 한국 건물 3D 매스 데이터셋 구축 (V-World 3D, 도시건축통합지도)
- Phase 2: Diffusion model 학습 (LoRA on Stable Diffusion 3D 또는 PointE 변형)
- Phase 3: 부지 조건 → DM sample → GA 초기 population
- Phase 4: 비교 실험 (random init GA vs DM-init GA)

**참고 논문**:
- Tsai+ WACV 2025: 3D Synthesis for Architectural Design
- Zhang+ 2024 *Frontiers*: Diffusion 3D form-finding (S2095263524001791)
- Cui+ 2024 arxiv 2404.13353: Daylight-driven diffusion
- LoRA Architectural Massing MDPI 2025: https://www.mdpi.com/2075-5309/15/19/3477

**예상 효과**: GA 수렴 generation 30→10 단축. 발표에서 "차세대 hybrid" 명분.

---

### C3. Differentiable Building Performance + Hybrid GA-Gradient

**왜?**
- GA는 gradient-free → high-dim에서 비효율적
- 일조/일사 일부는 미분 가능 표현 가능 (SDF, NeRF surface)
- Hybrid: GA로 typology 결정 → gradient로 매개변수 fine-tune

**구체 작업** (6개월+):
- Phase 1: 매스를 SDF로 표현 (Vicini+ SIGGRAPH Asia 2024)
- Phase 2: 일조 평가를 Mitsuba 3로 미분 가능화
- Phase 3: GA outer loop + gradient inner loop
- Phase 4: 비교: pure GA vs GA+gradient

**참고 논문**:
- Vicini+ SIGGRAPH Asia 2024 SDF Differentiable Rendering
- Wang+ ICCV 2025 Higher-order Differentiable Rendering
- Mitsuba 3 (Jakob+ 2022)

**현실 제약**: 매우 어려움. Categorical/Series 변수 미분 불가 → 부분적 적용만.

---

## (d) 우선순위 정리

| 우선 | 작업 | 기간 | 효과 | 난이도 |
|---|------|------|------|--------|
| 1 | A1 NSGA-III 추가 | 1주 | 발표 즉시 차별화, many-objective 가능 | 낮음 (pymoo 통합) |
| 2 | A3 Constraint penalty 정교화 | 3일 | 학계 표준 준수, 결과 품질 향상 | 매우 낮음 |
| 3 | A2 Radiance lite 통합 | 1주 | 일조 평가 학계 표준화 | 중간 |
| 4 | B1 BO+Surrogate | 1개월 | A2 후 필수, 평가 50-100배 빠름 | 중간 |
| 5 | B2 Heterogeneous Island | 3주 | 알고리즘 다양성, 논문 가능 | 중간 |
| 6 | C1 GA→DRL Bootstrap | 6개월 | 차세대, 실시간 도시 시뮬 | 높음 |
| 7 | C2 Diffusion + GA Hybrid | 6개월 | 차세대 hybrid, 데이터셋 필요 | 높음 |
| 8 | C3 Differentiable Hybrid | 6개월+ | 매우 어려움, 부분 적용만 | 매우 높음 |

---

## (e) 발표 시 활용 멘트

### 단기 보완 한 줄
> "1-2주 내 NSGA-III를 pymoo로 통합해 many-objective(4+)까지 확장 예정입니다. Zhao+ 2022 (Applied Energy) dormitory 사례에서 에너지 +41%, 일조 +42% 효과 검증되어 우리 시스템에도 동등 적용 기대합니다."

### 중기 방향 한 줄
> "Radiance 시뮬레이션 통합 시 GA가 비실용화되므로 Bayesian Optimization + GP/CNN surrogate를 도입 (Westermann 2019, Tian 2025). 이후 surrogate가 DRL bootstrap의 자연스러운 stepping stone이 됩니다."

### 장기 비전 한 줄
> "GA가 도출한 Pareto front를 DRL training data로 재사용해 새 부지 zero-shot 매스 추론 — Tian+ 2025 *Energy & Buildings*가 GAN surrogate + DRL hybrid로 비슷한 구조 제시했고, 한국 행정 데이터(31K Neo4j 법조항 + Vworld PNU)와 결합한 형태가 본 연구실의 next contribution."

---

## (f) 출처 (URL)

### 단기 (A 시리즈)
- [Zhao+ 2022 NSGA-III dormitory (Applied Energy)](https://ideas.repec.org/a/eee/appene/v305y2022ics0306261921011569.html)
- [pymoo NSGA-III docs](https://pymoo.org/algorithms/moo/nsga3.html)
- [honeybee-radiance](https://github.com/ladybug-tools/honeybee-radiance)

### 중기 (B 시리즈)
- [Westermann 2019 surrogate review](https://www.sciencedirect.com/science/article/abs/pii/S037877881831556X)
- [Zhang 2020 Building Performance Simulation surrogate](https://www.tandfonline.com/doi/full/10.1080/19401493.2020.1821094)
- [Tian+ 2025 GAN surrogate + DRL (Energy & Buildings)](https://www.sciencedirect.com/science/article/abs/pii/S0360132325003464)
- [Wang+ 2024 EvoMass typology (Frontiers)](https://www.sciencedirect.com/science/article/pii/S2095263524000797)

### 장기 (C 시리즈)
- [Chen+ 2024 MADDPG renovation (Automation in Construction)](https://www.sciencedirect.com/science/article/abs/pii/S0926580524004382)
- [SpaceLayoutGym 2024 RL layout](https://www.sciencedirect.com/) (검색 필요)
- [Tsai+ WACV 2025 3D Synthesis](https://openaccess.thecvf.com/content/WACV2025/papers/Tsai_3D_Synthesis_for_Architectural_Design_WACV_2025_paper.pdf)
- [Zhang+ 2024 Diffusion 3D form-finding (Frontiers)](https://www.sciencedirect.com/science/article/pii/S2095263524001791)
- [Daylight diffusion arxiv 2404.13353](https://arxiv.org/abs/2404.13353)
- [LoRA Massing MDPI 2025](https://www.mdpi.com/2075-5309/15/19/3477)
- [Vicini+ SIGGRAPH Asia 2024 SDF DR](https://dl.acm.org/doi/10.1145/3680528.3687573)
- [Wang+ ICCV 2025 Higher-order DR](https://openaccess.thecvf.com/content/ICCV2025/papers/Wang_Stochastic_Gradient_Estimation_for_Higher-Order_Differentiable_Rendering_ICCV_2025_paper.pdf)

### EvoMass 환경 변수 확장
- [EvoMass + GH_Wind 2021](https://www.researchgate.net/publication/353906430)
