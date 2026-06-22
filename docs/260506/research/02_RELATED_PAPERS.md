# 발표 관련 논문 리스트 — Top 10

**목적**: SSIEA 기반 건축 매스 최적화 발표에서 인용할 만한 논문 모음
**선정 기준**: SSIEA 알고리즘 원전 / EvoMass 워크플로우 / 건축 매스 다목적 최적화 / 일조-일사 통합

---

## Tier 1 — 반드시 인용 (3편)

### [P1] Lou et al. 2025 (Sci. Rep.) ★★★ 핵심 인용
- **제목**: Multi-objective optimization of daylighting performance and solar radiation for building geometry using a hybrid evolutionary algorithm
- **저자**: S. Lou, X. Luo, Z. Chen, Zhiji Gao, Ruida Wang, Linjin Feng, Guoyi Zhang, Yanfei Zhang, Ye Zhao, Bei Li
- **발행**: 2025-07-22, *Scientific Reports* 15:26644
- **DOI**: 10.1038/s41598-025-12165-6 / **arxiv ID**: 없음 (preprint 미게재)
- **URL**: https://www.nature.com/articles/s41598-025-12165-6
- **요약 1줄**: SSIEA + EvoMass로 매스 형상을 다목적 최적화 → 일사 균형 +26.89%, UDI +19.85%
- **발표와 연결점**: 발표 자료의 "SSIEA Nature 2025 기반" 인용이 정확히 이 논문. **워크플로우 도식**(Fig. 1, 3)을 발표 슬라이드에 차용 가능 (오픈액세스).

### [P2] Wang, Janssen, Ji 2020 (AI EDAM) ★★★ 알고리즘 원전
- **제목**: SSIEA: a hybrid evolutionary algorithm for supporting conceptual architectural design
- **저자**: Likai Wang, Patrick Janssen, Guohua Ji
- **발행**: 2020, *AI EDAM* (Artificial Intelligence for Engineering Design, Analysis and Manufacturing), Cambridge University Press
- **DOI**: 10.1017/S0890060420000281 (확인 필요 — 후속 검증 권장)
- **arxiv ID**: 없음
- **요약 1줄**: SSIEA 알고리즘을 처음 정식 정의 — island + steady-state replacement 결합으로 다양성과 수렴 속도 동시 확보
- **발표와 연결점**: SSIEA 알고리즘 자체를 인용할 때 **반드시 같이** 등장해야 함. P1만 인용하면 "Lou가 알고리즘을 만들었다"는 오해 발생.

### [P3] Wang, Janssen, Ji 2019 (CAADRIA) ★★ 알고리즘 초기 제시
- **제목**: Diversity and Efficiency — A Hybrid Evolutionary Algorithm Combining an Island Model with a Steady-state Replacement Strategy
- **저자**: Likai Wang, Patrick Janssen, Guohua Ji
- **발행**: 2019, Proceedings of CAADRIA 2019 (24th)
- **URL**: https://www.researchgate.net/publication/332543054
- **요약 1줄**: SSIEA의 첫 제시. 컨퍼런스 페이퍼 → 이후 P2(AI EDAM)에서 저널 확장.
- **발표와 연결점**: 알고리즘 *기원* 강조 시 인용. 학회지 발표에선 P2만으로 충분.

---

## Tier 2 — 배경 / 워크플로우 인용 (4편)

### [P4] Wang 2022 (IJAC) — EvoMass 워크플로우
- **제목**: Workflow for applying optimization-based design exploration to early-stage architectural design — Case study based on EvoMass
- **저자**: Likai Wang
- **발행**: 2022, *International Journal of Architectural Computing*, SAGE
- **DOI**: 10.1177/14780771221082254
- **URL**: https://journals.sagepub.com/doi/abs/10.1177/14780771221082254
- **요약 1줄**: 초기 설계 단계에서 EvoMass 활용 워크플로우. 발표의 "초기 설계 + 최적화 통합" 주장 보강.
- **연결점**: 발표가 *조기 설계 단계* 도구임을 강조할 때 인용.

### [P5] Wang et al. 2024 (Frontiers of Architectural Research) — EvoMass 매스 typology
- **제목**: Optimization-based design exploration of building massing typologies — EvoMass and a typology-oriented computational design optimization method for early-stage performance-based building massing design
- **저자**: Likai Wang et al.
- **발행**: 2024, *Frontiers of Architectural Research*
- **URL**: https://www.sciencedirect.com/science/article/pii/S2095263524000797
- **요약 1줄**: EvoMass의 typology(매스 유형) 기반 최적화 확장. additive/subtractive 양쪽 사례.
- **연결점**: 25_ACE의 "mass shape expansion" (4종 → 확장)과 직접 연결 가능. `arr/mass-shape-expansion.md` 참조.

### [P6] Wang, Luo, Shao, Ji 2023 (IJAC) — 패시브 전략 역방향 탐색
- **제목**: Reverse passive strategy exploration for building massing design — An optimization-aided approach
- **저자**: Likai Wang, Ting Luo, Tong Shao, Guohua Ji
- **발행**: 2023, *International Journal of Architectural Computing*
- **DOI**: 10.1177/14780771231177514
- **URL**: https://journals.sagepub.com/doi/10.1177/14780771231177514
- **요약 1줄**: SSIEA + EvoMass로 패시브 디자인 전략을 *역으로* 탐색 (성능 → 형태).
- **연결점**: 발표에서 "성능 기반 형태 도출" 부분 인용 가능.

### [P7] Wang & Janssen 2018 — 건축 EA에서 제약 조건 처리
- **제목**: Utility of Evolutionary Design in Architectural Form Finding: An Investigation into Constraint Handling Strategies
- **저자**: Likai Wang, Patrick Janssen
- **발행**: 2018 (Semantic Scholar 등재)
- **URL**: https://www.semanticscholar.org/paper/Utility-of-Evolutionary-Design-in-Architectural-An-Wang-Janssen/d76cd4e8690e257431ebdd98af00d794bf8bbffc
- **요약 1줄**: 건축 형태 탐색 EA에서 제약 처리 전략 비교 → SSIEA 설계 결정의 배경.
- **연결점**: 25_ACE에서 "건폐율/용적률/일조 제약을 어떻게 EA에 통합?" 부분의 학술 근거.

---

## Tier 3 — 비교/배경 (3편 — 발표 자료에 *맥락 인용* 가능)

### [P8] EvoMass + GH_Wind 통합 (2021, ResearchGate)
- **제목**: EvoMass + GH_Wind — An agile wind-driven building massing design optimization framework
- **URL**: https://www.researchgate.net/publication/353906430
- **연결점**: 풍환경까지 매스 최적화에 통합한 사례 (CFD + EA). 발표에서 "다른 환경 변수 확장 가능성" 언급할 때 인용.

### [P9] Multi-objective external shading optimization (Sci. Rep. 2025)
- **제목**: Multiobjective optimization of external shading for west facing university dormitories in Kunming considering solar radiation and daylighting
- **발행**: 2025, *Scientific Reports* 15
- **URL**: https://www.nature.com/articles/s41598-025-04465-8
- **연결점**: Lou+ 2025와 *비슷한 시기*의 비슷한 주제 — SSIEA 대신 NSGA-II 사용. 비교 인용 가능.

### [P10] Daylighting assessment of window layouts (Sci. Rep. 2025)
- **제목**: Daylighting assessment of window layouts and architectural elements in early design stages
- **발행**: 2025, *Scientific Reports* 15
- **URL**: https://www.nature.com/articles/s41598-025-23389-x
- **연결점**: 매스가 아닌 창호 레이아웃 분석. 발표의 "초기 설계 단계 일조 평가" 흐름에 추가 가능.

---

## arxiv 검색 결과 — 빈손

7개 키워드(`Steady-State Island Evolutionary Algorithm`, `SSIEA daylighting solar`, `SSIEA architectural mass`, `multi-objective genetic algorithm building daylight`, `NSGA-II architectural design`, `island model evolutionary algorithm building geometry`, `Pareto multi-objective building mass form-finding`)로 arxiv를 검색했지만 **건축 매스 최적화 + SSIEA 관련 직접 매칭 0건**. 이 분야는 arxiv 비주류이고 *Scientific Reports / IJAC / Building & Environment / Energy & Buildings / Frontiers of Architectural Research* 가 주력 저널.

발표 자료에 arxiv 인용을 굳이 끼워넣을 필요 없음.

---

## 사용 출처 (URL 모음)

- https://www.nature.com/articles/s41598-025-12165-6 (P1)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12284102/ (P1 PMC)
- https://www.semanticscholar.org/paper/Multi-objective-optimization-of-daylighting-and-for-Lou-Luo/e103be1d101b5664c95fb987a8579e5a0ab869b9 (P1 SS)
- https://www.researchgate.net/publication/332543054 (P3)
- https://journals.sagepub.com/doi/abs/10.1177/14780771221082254 (P4)
- https://www.sciencedirect.com/science/article/pii/S2095263524000797 (P5)
- https://journals.sagepub.com/doi/10.1177/14780771231177514 (P6)
- https://www.semanticscholar.org/paper/Utility-of-Evolutionary-Design-in-Architectural-An-Wang-Janssen/d76cd4e8690e257431ebdd98af00d794bf8bbffc (P7)
- https://www.researchgate.net/publication/353906430 (P8)
- https://www.nature.com/articles/s41598-025-04465-8 (P9)
- https://www.nature.com/articles/s41598-025-23389-x (P10)
- https://www.food4rhino.com/en/app/evomass (EvoMass)
- https://www.xjtlu.edu.cn/en/study/departments/design-school/architecture/department-staff/academic-staff/staff/likai-wang (Wang profile)
