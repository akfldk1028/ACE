# 매스 최적화 SOTA 비교 — 8개 방식

**작성일**: 2026-04-30
**대상 발표**: 2026-05-06 랩미팅
**목적**: 우리 시스템(NSGA-II + SSIEA, AUA Discover 포팅)이 학계 SOTA 대비 어디 위치하는지 정직하게 평가
**근거**: WebSearch + arxiv-mcp 결과 (모든 출처 §끝 명시)

---

## 0. 우리 시스템 (베이스라인 — 비교 기준)

- 파일: `D:\Data\25_ACE\ARR\backend\design\engine\objects.py`
- **NSGA-II** `Job` 클래스 (legacy) + **SSIEA** `SSIEAJob` 클래스 (신규) 병행 구현
- 매스 인코딩: 5-box stacked(29 genes) + Subtractive(23) + Grid(22) 등 10종
- 평가: BCR/FAR/일조/이격/조경 (Shapely 폴리곤, Python pure)
- 인코딩 자유도: Continuous / Categorical / Series / Sequence 4종 mixed
- 평가 비용: ~수십 ms/개체 (시뮬레이션 없음, 폴리곤 연산만)
- 출처: AUA Discover (Danil Nagy, GPL-3.0) → Python 3.12 웹 포팅 + Wang+ 2020 SSIEA 추가 구현

---

## 1. NSGA-II / NSGA-III (Deb 2002 / Deb & Jain 2014) — 고전 다목적 GA

- **알고리즘 이름**: Non-dominated Sorting Genetic Algorithm II / III
- **대표 논문**:
  - Deb, K., Pratap, A., Agarwal, S., Meyarivan, T. (2002). *A fast and elitist multiobjective genetic algorithm: NSGA-II*. IEEE TEC, 6(2), 182-197.
  - Deb, K., Jain, H. (2014). *An evolutionary many-objective optimization algorithm using reference-point-based nondominated sorting approach: NSGA-III*. IEEE TEC, 18(4), 577-601.
  - Zhao+ 2022 *Applied Energy*: "PCA-ANN integrated NSGA-III framework for dormitory building design optimization" — 에너지 +41.27%, 일조 +42.24%
- **핵심 아이디어**:
  - NSGA-II: 비지배 정렬(non-dominated sorting) + crowding distance로 Pareto front 다양성 유지
  - NSGA-III: reference point 기반 — **3개 이상 목적**(many-objective)에서 NSGA-II의 약점(crowding distance 무력화) 극복
- **장점 (우리 대비)**:
  - **3개+ 목적**(에너지+일조+조망+열쾌적+비용)에서 우월. 우리는 2-3개 목적이 한계
  - 학계 표준 — 발표에서 "NSGA-II는 했다"보다 "NSGA-III까지 적용"이 더 강함
- **단점/제약 (우리 대비)**:
  - 2-3 목적이면 NSGA-II와 큰 차이 없음 (실용에선 BCR+FAR+일조가 대부분)
  - reference point 분포 설정이 추가 hyperparameter → tuning 부담
- **우리 위치**: NSGA-II는 **이미 구현**, NSGA-III는 **미구현** → 단기 보완 1순위

---

## 2. SSIEA — Steady-State Island EA (Wang+ 2020, Lou+ 2025) ★ 우리가 쓰는 것

- **알고리즘 이름**: Steady-State Island Evolutionary Algorithm
- **대표 논문**:
  - Wang, L., Janssen, P., Ji, G. (2020). *SSIEA: a hybrid evolutionary algorithm for supporting conceptual architectural design*. AI EDAM, Cambridge.
  - Lou et al. (2025). *Multi-objective optimization of daylighting performance and solar radiation for building geometry using a hybrid evolutionary algorithm*. Sci. Rep. 15:26644. DOI: 10.1038/s41598-025-12165-6
- **핵심 아이디어**: island model (5개 sub-population 병렬) + steady-state replacement (매 세대 1개체만 교체) → 다양성과 수렴 속도 동시 확보
- **장점 (우리 대비)**:
  - **이미 우리가 구현** (`SSIEAJob`) — 2025 SoTA 알고리즘 그대로 채용
  - NSGA-II 대비 local optima 회피 우월 (island migration)
  - adaptive mutation rate (0.35 → 0.10) 자동 hyperparameter 적응
- **단점**:
  - "many-objective"(4+)에서는 NSGA-III/MOEA/D가 더 적합 — SSIEA는 2-3 목적 최적
  - Pareto front 분포 균일성은 reference-point 기반보다 약함
- **우리 위치**: **이미 구현 완료**, 학계 응용 SoTA와 동급

---

## 3. MOEA/D — Multi-Objective EA by Decomposition (Zhang & Li 2007)

- **대표 논문**:
  - Zhang, Q., Li, H. (2007). *MOEA/D: A multiobjective evolutionary algorithm based on decomposition*. IEEE TEC, 11(6), 712-731. (피인용 12,000+)
  - Wang+ 2024 *Energy Informatics*: "Multi-agent-assisted MOEA/D approach for energy-efficient building design"
- **핵심 아이디어**: 다목적 문제를 N개의 단일목적 sub-problem으로 분해 → 이웃 sub-problem 정보만 사용해 동시 최적화 → NSGA-II보다 generation당 계산량 적음
- **장점 (우리 대비)**:
  - **계산 효율** 우월: 이웃만 사용해 NSGA-II보다 빠름 (특히 4+ 목적에서)
  - 분해 가중치 벡터로 Pareto front 분포 직접 제어 가능
- **단점/제약**:
  - sub-problem 분해 가중치 설정이 hyperparameter 부담
  - 우리 BCR/FAR/일조 같은 stiff constraint와 결합 시 weight tuning 까다로움
- **우리 위치**: 미구현. 단기 보완 후순위 (NSGA-III가 더 시급)

---

## 4. CMA-ES — Covariance Matrix Adaptation ES (Hansen+ 2003)

- **대표 논문**:
  - Hansen, N., Müller, S. D., Koumoutsakos, P. (2003). *Reducing the time complexity of the derandomized evolution strategy with covariance matrix adaptation (CMA-ES)*. Evolutionary Computation, 11(1), 1-18.
  - Building 분야 직접 응용은 적음 (검색 결과 검증) — facade kinetic 등 연속 변수 매개변수 최적화에서 사용
- **핵심 아이디어**: 진화 전략 + 공분산 행렬 적응 — **연속 매개변수 공간**에서 gradient-free, 학계 베스트 연속 최적화
- **장점 (우리 대비)**:
  - **연속 변수만** 있는 문제에서는 GA보다 빠른 수렴
  - 단일목적이면 압도적 성능 (BBOB benchmark 다수 우승)
- **단점/제약**:
  - **본질적으로 단일목적** (MO-CMA-ES 변형 있으나 NSGA-II/III만큼 성숙하지 않음)
  - Categorical / Series / Sequence 변수 처리 어려움 → 우리 4종 input type 중 1/4만 커버
  - Pareto front 직접 산출 불가 (scalarization 필요)
- **우리 위치**: 우리 input type 다양성 때문에 **CMA-ES만 단독 적용 불가**. 연속 부분만 hybrid 가능 (장기)

---

## 5. Bayesian Optimization + Surrogate Model (BO+SM)

- **대표 논문**:
  - Westermann, P., Evins, R. (2019/2020). *Surrogate modelling for sustainable building design — A review*. Energy & Buildings.
  - Zhang+ 2020 *J. Building Performance Simulation*: "Building energy optimization using surrogate model and active sampling"
  - Tian+ 2025 *Energy & Buildings*: "Deep RL with embedded GAN surrogate for dormitory optimization" (S0360132325003464)
- **핵심 아이디어**: 비싼 시뮬레이션(EnergyPlus, Radiance, CFD)을 GP/CNN/GAN surrogate로 대체 → BO가 acquisition function으로 다음 sample 선택
- **장점 (우리 대비)**:
  - **시뮬레이션 비용이 큰 경우** 압도적: 일조 분석(Radiance)이 30분/개체면 BO가 실용적, GA는 비실용
  - 적은 평가 횟수(50-200)로 우수 해 도출
- **단점/제약**:
  - **우리는 Shapely 폴리곤 평가가 ms 단위로 빠름** → BO 도입 효익 낮음
  - surrogate 학습 데이터 필요 (cold start 문제)
  - 고차원(20+ 변수)에서 GP 확장성 한계 — 우리 29-genes는 borderline
- **우리 위치**: **현재 부적합** — 시뮬레이션 통합(EnergyPlus 등) 시 도입 가치. 중기 검토

---

## 6. Differentiable Rendering + Gradient Descent (Mitsuba/Dr.Jit, 2024-2025)

- **대표 논문**:
  - Vicini+ SIGGRAPH Asia 2024: *A simple approach to differentiable rendering of SDFs*
  - Wang+ ICCV 2025: *Stochastic Gradient Estimation for Higher-order Differentiable Rendering*
  - Mitsuba 3 (Jakob+ 2022): inverse rendering framework
- **핵심 아이디어**: 일조/일사 시뮬레이션을 미분 가능하게 만들고 SGD/Adam으로 직접 매스 형태 미분 → 반복당 빠르게 수렴
- **장점 (우리 대비)**:
  - 이론적으로 **GA 대비 100-1000배 빠름** (gradient direction 확보)
  - 연속 매스 매개변수 → 매끄러운 형상 도출 (rounded mass)
- **단점/제약**:
  - **매우 어려움** — 폴리곤 부울 연산, Categorical 변수, 법규 제약은 미분 불가
  - 우리의 Subtractive/Grid 같은 이산 인코딩과 비호환
  - 학계에서도 건축 도메인 직접 응용 사례 거의 없음 (graphics 분야 위주)
  - 구현 인력 부담 (Mitsuba 통합 + 자동미분 디버깅)
- **우리 위치**: **현재 부적합** — 장기 비전, 실용성 낮음

---

## 7. Reinforcement Learning (Deep RL) for Massing (2024-2025)

- **대표 논문**:
  - Chen+ 2024 *Automation in Construction*: *Automated architectural spatial composition via multi-agent deep reinforcement learning for building renovation* (S0926580524004382)
  - SpaceLayoutGym (2024): RL agent가 wall placement 통한 layout 생성
  - Tian+ 2025 *Energy & Buildings*: GAN surrogate + DRL for dormitory optimization
  - Wang+ 2024 *J. Computational Design and Engineering* (qwae109)
- **핵심 아이디어**: agent가 매스 형태를 step-by-step 결정 → reward(BCR/FAR/일조) 학습 → 한 번 학습 후 추론은 빠름
- **장점 (우리 대비)**:
  - **학습 후 추론 매우 빠름** — 새 부지마다 GA 처음부터 돌릴 필요 없음
  - generalization — 비슷한 부지에 zero-shot 가능
  - sequential decision (층별 적층 등)에 자연스러움
- **단점/제약**:
  - **학습 데이터/시간 막대함** (수천-수만 episode)
  - reward shaping 매우 까다로움 (sparse reward 문제)
  - 학계 응용 아직 초기 (MADDPG는 2024 첫 적용)
  - 한국 법규처럼 hard constraint 다수면 RL은 제약 위반 학습 어려움
- **우리 위치**: **유망하나 초기단계** — 장기 비전. surrogate로 우리 GA 결과 학습 → DRL 부트스트랩 가능

---

## 8. Diffusion Model / GAN for Mass Generation (2024-2025)

- **대표 논문**:
  - Tsai+ WACV 2025: *3D Synthesis for Architectural Design*
  - Zhang+ 2024 *Frontiers of Architectural Research*: *A diffusion-based machine learning method for 3D architectural form-finding* (S2095263524001791)
  - LoRA-based mass generation: MDPI Buildings 15:3477 (2025)
  - Cui+ arxiv 2404.13353 (2024): *Generating Daylight-driven Architectural Design via Diffusion Models*
  - HouseGAN++ (Nauata+ CVPR 2021) — floor plan 영역
- **핵심 아이디어**: 학습된 prior로부터 매스/평면 직접 sample → 조건부(daylight, bounding box) 생성
- **장점 (우리 대비)**:
  - **창의적 형상** — GA가 못 발견하는 sculptural mass 생성
  - 텍스트/스케치 조건부 생성 (designer-friendly)
  - 1회 inference로 다양한 후보 (~초 단위)
- **단점/제약**:
  - **법규 제약 보장 불가** — diffusion 생성물이 BCR 60% 위반해도 알 수 없음
  - 학습 데이터(3D 매스 dataset) 매우 부족 — 한국 도시 데이터셋 거의 없음
  - 미세 조정 어려움 (LoRA로 일부 가능하나 도메인 특화 train 필요)
  - "최적해" 보장 없음 — 우리는 BCR=80%, FAR=1300% 정확히 활용해야 하는데 diffusion은 통계적 sampling
- **우리 위치**: **보완재** — GA 초기 population에 diffusion 후보 시드로 hybrid 가능 (장기)

---

## 9. Graph Neural Network (GNN) — 평면/공간 GNN

- **대표 논문**:
  - Hu+ 2020 SIGGRAPH: *Graph2Plan: learning floorplan generation from layout graphs*
  - Wu+ 2025 *GSDiff*: vector floorplan synthesis via geometry-aware diffusion
  - GenPlan (OpenReview 2024): Graph Transformer Network for floor plans
  - CAADRIA 2024_497: topology→spatial GNN
- **핵심 아이디어**: 방-방 인접 그래프(node=방, edge=도어)에서 GNN이 layout 생성
- **장점 (우리 대비)**:
  - **공간 토폴로지 명시** — 우리는 매스만, 평면은 별도
  - relational reasoning 강점 (방 종류, adjacency 제약)
- **단점/제약**:
  - **매스(3D outer envelope) 직접 다루지 않음** — GNN은 floor plan 영역 위주
  - 한국 건축 도면 dataset 부재
  - 우리 매스 인코딩(5-box 적층)과 다른 추상화 단계
- **우리 위치**: **다른 영역** — 매스가 아니라 평면 생성에 적용 가능 (mesh-packing 모듈에 가까움)

---

## 10. 비교 표 (한눈에)

| # | 방식 | 다목적 | 미분가능 평가 필요? | 학습 데이터 필요? | 실시간성 | 매스 인코딩 자유도 | 실무 적용 사례 | 우리 시스템 채용? |
|---|------|--------|----|----|------|------|------|------|
| 1 | **NSGA-II** | O (2-3) | X | X | 중 (수십초) | 높음 (4 type mixed) | 매우 많음 | YES (legacy `Job`) |
| 1' | **NSGA-III** | O (4+) | X | X | 중 | 높음 | Zhao+ 2022 dormitory | NO (단기 보완) |
| 2 | **SSIEA** | O (2-3) | X | X | 중 | 높음 | Lou+ 2025, Wang+ 2024 | YES (`SSIEAJob`) |
| 3 | **MOEA/D** | O (4+) | X | X | 빠름 | 중 (continuous 위주) | Wang+ 2024 energy | NO |
| 4 | **CMA-ES** | △ (단일 위주) | X | X | 매우 빠름 | 낮음 (continuous only) | facade tuning | NO |
| 5 | **BO + Surrogate** | O (acq fn 따라) | X | O (cold start) | 빠름 (학습 후) | 중 | EnergyPlus 통합 시 압도적 | NO |
| 6 | **Differentiable Rendering** | △ | **O** | O | 매우 빠름 | 낮음 (smooth only) | Graphics 위주, 건축 거의 없음 | NO |
| 7 | **Deep RL** | △ (reward shaping) | X | **O (수천-수만 ep)** | 추론 매우 빠름 | 중 | Chen+ 2024 renovation | NO |
| 8 | **Diffusion / GAN** | X (post-hoc) | X | **O (3D mass dataset)** | 추론 빠름 | **매우 높음 (창의)** | Tsai 2025, Zhang 2024 | NO |
| 9 | **GNN** | X (관계 학습) | X | O | 빠름 | 다름 (평면 위주) | Graph2Plan | NO (다른 영역) |

**범례**: O=완전 지원, △=부분/제한적, X=미지원

---

## 11. 출처 (URL)

### 알고리즘 원전 / 학계 표준
- [NSGA-II (Deb 2002, IEEE TEC)](https://ieeexplore.ieee.org/document/996017)
- [NSGA-III (Deb & Jain 2014, IEEE TEC)](https://ieeexplore.ieee.org/document/6600851)
- [MOEA/D (Zhang & Li 2007, IEEE TEC)](https://ieeexplore.ieee.org/document/4358754)
- [SSIEA Wang 2020 (AI EDAM, Cambridge)](https://www.cambridge.org/) (DOI 확인 필요)
- [Lou+ 2025 SSIEA Sci. Rep.](https://www.nature.com/articles/s41598-025-12165-6)
- [CMA-ES Hansen 2003](https://en.wikipedia.org/wiki/CMA-ES)

### 건축 응용 논문
- [PCA-ANN NSGA-III dormitory (Applied Energy 2022)](https://ideas.repec.org/a/eee/appene/v305y2022ics0306261921011569.html)
- [MOEA/D multi-agent building energy 2024](https://link.springer.com/article/10.1186/s42162-024-00406-3)
- [Surrogate building energy 2020](https://www.tandfonline.com/doi/full/10.1080/19401493.2020.1821094)
- [DRL renovation 2024 (Automation in Construction)](https://www.sciencedirect.com/science/article/abs/pii/S0926580524004382)
- [DRL+GAN dormitory 2025 (Energy & Buildings)](https://www.sciencedirect.com/science/article/abs/pii/S0360132325003464)

### Diffusion / GAN
- [3D Synthesis for Architectural Design WACV 2025](https://openaccess.thecvf.com/content/WACV2025/papers/Tsai_3D_Synthesis_for_Architectural_Design_WACV_2025_paper.pdf)
- [Diffusion 3D form-finding 2024 (Frontiers)](https://www.sciencedirect.com/science/article/pii/S2095263524001791)
- [LoRA Architectural Massing (MDPI 2025)](https://www.mdpi.com/2075-5309/15/19/3477)
- [Daylight-driven diffusion (arxiv 2404.13353)](https://arxiv.org/abs/2404.13353)
- [BuildingBlock arxiv 2505.04051](https://arxiv.org/html/2505.04051v1)
- [ArchiDiffusion (Building 2024)](https://www.sciencedirect.com/science/article/abs/pii/S2352710224029413)

### Differentiable Rendering
- [SDF Differentiable Rendering SIGGRAPH Asia 2024](https://dl.acm.org/doi/10.1145/3680528.3687573)
- [Higher-order Differentiable Rendering ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/papers/Wang_Stochastic_Gradient_Estimation_for_Higher-Order_Differentiable_Rendering_ICCV_2025_paper.pdf)

### GNN Floor Plan
- [Graph2Plan SIGGRAPH 2020](https://www.researchgate.net/publication/343625455_Graph2Plan_learning_floorplan_generation_from_layout_graphs)
- [GenPlan OpenReview 2024](https://openreview.net/forum?id=kA5egaJjya)
- [GSDiff vector floorplan 2025](https://wutomwu.github.io/publications/2025-GSDiff/paper.pdf)

### EvoMass + 다른 환경 변수
- [EvoMass + GH_Wind 2021](https://www.researchgate.net/publication/353906430)
- [EvoMass typology Frontiers 2024](https://www.sciencedirect.com/science/article/pii/S2095263524000797)
