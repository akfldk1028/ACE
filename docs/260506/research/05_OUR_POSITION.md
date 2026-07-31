# 우리 시스템(25_ACE) 학계 SOTA 대비 위치 평가

**작성일**: 2026-04-30
**작성자 시각**: 정직한 평가 (과대평가 금지)
**근거**: `04_SOTA_COMPARISON.md` 8개 방식 비교 결과

---

## 1. 한 줄 결론

**현재 학계 SOTA인가?** → **부분적 YES — 알고리즘 측면(SSIEA)은 2025 응용 SoTA와 동급, 시스템 측면(법규 자동검증 + 실시간 SSE + 한국 행정/지리 통합)은 학계 어디에도 없는 독자적 강점.**

다만 *알고리즘 자체의 절대 성능*만 본다면 NSGA-III, MOEA/D, BO+Surrogate 일부에 뒤짐.

---

## 2. 우리 시스템 강점 (정직 평가)

### 2-1. 알고리즘 측면

| 강점 | 근거 | SOTA 대비 |
|------|------|----------|
| SSIEA 구현 완료 (`SSIEAJob`) | `objects.py:394-614`, 5 islands + ring migration + adaptive mutation | Wang+ 2020, Lou+ 2025와 동일 알고리즘 |
| NSGA-II 병행 (`Job` legacy) | `objects.py:251-391` | Deb 2002, 학계 표준 |
| 인코딩 자유도 4종 (Continuous/Categorical/Series/Sequence) | `Design.generate_random()` | CMA-ES/BO보다 풍부 |
| Pareto front 캐싱 + ring migration | `_pareto_cache`, `_migrate()` | 일반 EA 구현보다 효율적 |

### 2-2. 시스템/엔지니어링 측면 (학계 논문에 없는 부분)

| 강점 | 근거 | 학계 비교 |
|------|------|----------|
| **법규 자동 검증 루프** | `land/zoning_mapper.py` + `law_enricher.py` (BCR/FAR 21 zones, 170+ 법조항 자동 검증) | EvoMass 등은 BCR/FAR을 *입력*으로만 받음. 우리는 *법조항까지 자동 도출* |
| **실시간 SSE 스트리밍** | `/design/jobs/<id>/stream/` (generation별 progress) | 학계 데모는 batch result만 |
| **한국 PNU/Vworld 통합** | `pnu_resolver.py` + Vworld API → 주소→PNU→폴리곤 자동 | 학계 어디에도 없음 (한국 특화) |
| **10종 매스 인코딩** | 5-box stacked / Subtractive / Grid / etc | EvoMass 매스 typology(2024)와 동급 |
| **8종 규제선 자동 적용** | 정북일조 + 도로사선(폐지) + datum elevation | 학계 논문은 일조만 |
| **Multi-agent 통합** | `039_Land_Swarm_Analysis_Team` (6→3 agent SelectorGroupChat) | 학계 매스 최적화는 single-tool |
| **End-to-end 자동화** | "주소 하나 → 41규제 + 매스 + Pareto" | 학계는 "매스 모델 입력 → 최적화" (한 단계만) |

### 2-3. 정직하게 말하면

**알고리즘은 SOTA의 ‘응용판’ — 진짜 강점은 시스템 통합과 한국 행정/법규 자동화.**

발표에서 "우리는 SSIEA를 새로 발명했다"고 말하면 거짓말. 정확히는 **"Lou+ 2025 SSIEA를 채용해 한국 건축법규 자동 검증 + 실시간 SSE 시스템에 통합했다"**.

---

## 3. 우리 시스템 약점 (학계 SOTA 대비 뒤지는 부분)

### 3-1. 알고리즘 측면 (인정해야 할 약점)

| 약점 | 학계 우월 사례 | 영향 |
|------|--------------|------|
| **Many-objective(4+) 약함** | NSGA-III (Deb 2014), MOEA/D (Zhang 2007) | 에너지+일조+조망+열쾌적+비용 동시 최적화 시 NSGA-II/SSIEA는 crowding distance 무력화 |
| **Surrogate Model 미구현** | Westermann 2019, Tian 2025 | 만약 EnergyPlus/Radiance 시뮬레이션 통합 시 우리 GA는 비실용적으로 느림 |
| **시뮬레이션 평가 부재** | 모든 학계 논문 | 우리는 폴리곤 BCR/FAR/이격만 — *진짜 일조 시뮬레이션*(Radiance) 미통합. "일조"라 부르지만 정북일조선 기하학적 검증일 뿐 |
| **DRL/Diffusion 미적용** | Chen 2024, Tsai 2025 | 학습 기반 generalization 없음 — 새 부지마다 GA 처음부터 |
| **NSGA-III 미구현** | Zhao 2022 dormitory (에너지+일조 +41%) | 가장 시급한 누락 |

### 3-2. 평가 함수 측면 (가장 큰 약점 — 솔직히)

**우리 "일조 평가"는 *진짜 일조 시뮬레이션이 아니다.***

- 정북일조선 기하학적 검증 = "건물이 정북일조 envelope 안에 들어가는가"만 체크
- 학계 논문(Lou+ 2025, Zhao+ 2022)은 **Radiance/Daysim으로 UDI/sDA/일사량 실제 시뮬레이션**
- 우리 BCR/FAR도 `Shapely.area * ratio` 단순 산수 — 학계는 EnergyPlus로 에너지/난방/냉방까지 평가

→ 발표에서 "우리는 일조 최적화를 한다" 표현 주의. 정확히는 **"우리는 정북일조선 envelope 내 매스 부피를 최대화한다"**.

### 3-3. 시스템 측면 약점

- **Cesium 3D 뷰어 미연동** (CLAUDE.md: "SiteMapPanel: placeholder")
- **Pareto front 시각화는 2D scatter** — 학계 standard interactive 3D plot 미만
- **GA hyperparameter 자동 튜닝 없음** — `num_islands=5`, `pop_per_island=15` 등 hardcoded

---

## 4. 발표 시 교수님 도전 질문 시뮬레이션

### Q1: "왜 NSGA-II/SSIEA만 썼나? NSGA-III나 MOEA/D는 왜 안 썼나?"

**답변 (권장)**:
> "현재 다루는 목적함수가 **BCR + FAR + 매스 부피** 세 개로 NSGA-II와 SSIEA의 sweet spot입니다. 4개 이상 목적(에너지/조망/열쾌적 추가)으로 확장하는 다음 단계에서 NSGA-III를 도입할 계획입니다. 단기 작업으로 1-2주 내 가능합니다 (`pymoo.algorithms.moo.nsga3` 통합). MOEA/D는 분해 가중치 튜닝 부담이 있어 검토 중입니다."

### Q2: "왜 진짜 일조 시뮬레이션(Radiance) 안 쓰나? 이 평가가 의미있나?"

**답변 (정직)**:
> "현재 평가는 정북일조선 envelope 기반 기하학적 검증입니다. 한국 건축법 86조 기준은 정북일조선 자체이므로 *법규 준수* 검증으로는 충분합니다. *건축 성능* 측면 일조량 시뮬레이션은 다음 단계에서 EnergyPlus/Radiance 통합으로 추가 예정이며, 그때 BO+Surrogate 도입 검토가 필요합니다 (시뮬레이션이 분 단위면 GA 비실용)."

### Q3: "Diffusion/DRL이 더 미래 아닌가? 왜 GA 같은 클래식만?"

**답변 (정직 + 야심)**:
> "Diffusion/DRL은 *generative*에 강하지만 **법규 hard constraint 보장이 본질적으로 어렵습니다** (Tsai 2025 WACV도 BCR 위반 감지 못 함). 우리 시스템은 한국 건축법 41 규제 자동 준수가 핵심이라 *constraint-driven optimization*인 GA가 적합합니다. 단, **GA가 도출한 Pareto front 결과를 DRL training data로 재사용하는 hybrid pipeline** (장기)이 자연스러운 발전 방향이며, ‘surrogate-bootstrapped DRL’ 형태로 Tian+ 2025 (Energy & Buildings)에서 유사 구조 제시되었습니다."

### Q4: "Lou+ 2025 SSIEA 논문은 *적용*했지 *발명*한 게 아니다. 새로움이 뭐냐?"

**답변 (정직)**:
> "맞습니다. 알고리즘 자체는 Wang+ 2020 SSIEA, Lou+ 2025 응용을 그대로 채용했습니다. **새로움은 알고리즘이 아니라 시스템 레벨**입니다 — (1) 한국 PNU 19자리 → 41 법규 → 8 규제선 → 매스 GA의 *end-to-end 자동화*, (2) 실시간 SSE 스트리밍 멀티에이전트, (3) Neo4j 31K 법조항 노드 + Vectorize와 GA 결과 자동 매핑. *학계 어디에도 없는* 통합 파이프라인입니다."

### Q5: "이게 진짜 SOTA냐?"

**답변 (가장 정직)**:
> "**알고리즘 단일 성능**은 SoTA가 아닙니다 — Lou+ 2025 응용판입니다. 그러나 **시스템 통합 + 법규 자동화 + end-to-end 파이프라인**은 학계에 비교 대상이 없는 독자적 강점입니다. ‘우리는 SSIEA를 더 잘 푼 게 아니라, **SSIEA를 한국 건축 실무에 처음으로 자동화 가능한 형태로 통합**한 것’이 정확한 표현입니다."

---

## 5. 한줄 정리

| 측면 | 평가 |
|------|------|
| 알고리즘 SOTA | **부분 SOTA** (SSIEA 응용 동급, NSGA-III/MOEA/D는 미구현) |
| 시스템 통합 SOTA | **YES — 독자 강점** (법규 자동 + 한국 행정 + 실시간 SSE) |
| 평가 함수 깊이 | **약점** (정북일조선 기하만, Radiance 미통합) |
| 학습/Generative | **부재** (DRL/Diffusion 미적용) |
| 실무 적용성 | **YES — 학계 어디에도 없는 강점** (주소→매스 30초 내) |

---

## 6. 발표 톤 권장

- ❌ "우리 시스템이 SOTA다"
- ❌ "SSIEA를 우리가 발명했다"
- ✅ "Lou+ 2025 SSIEA 응용 워크플로우를 한국 건축법규 자동화에 통합"
- ✅ "알고리즘은 SoTA 응용 동급, **시스템 통합은 학계에 없는 영역**"
- ✅ "다음 단계: NSGA-III 추가, Radiance 통합 검토"
