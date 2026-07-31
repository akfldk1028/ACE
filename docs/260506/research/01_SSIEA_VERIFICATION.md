# SSIEA 인용 검증 — 핵심 문서

**검증 결론: SSIEA Nature Scientific Reports 2025 인용은 사실 (VERIFIED REAL)**
다만 *문장 표현*은 약간 오해의 소지가 있어, 알고리즘 원전(2020)과 응용 논문(2025)을 구분해 인용하는 게 안전함.

---

## 1. "SSIEA"라는 이름의 알고리즘이 학계에 존재하는가?

**Yes — 존재함, 명확히 확인됨.**

- 약어 풀이: **Steady-State Island Evolutionary Algorithm**
- 핵심 아이디어: **island model**(부분집단 병렬 진화 + 주기적 정보 교환) + **steady-state replacement**(매 세대 일부만 교체)를 합친 **hybrid evolutionary algorithm**
- 적용 도메인: 건축 conceptual design / 매스 최적화 / 다목적 (일조 + 일사 + UDI)

---

## 2. SSIEA를 처음 제시한 논문 (원전)

### 2-1. SSIEA 알고리즘의 원저자 = **Likai Wang (XJTLU)**

웹 검색으로 확인된 원전:

| 연도 | 저자 | 제목 | 학술지 / 컨퍼런스 |
|---|---|---|---|
| **2019** | Wang, Janssen, Ji | "Diversity and Efficiency — A Hybrid Evolutionary Algorithm Combining an Island Model with a Steady-state Replacement Strategy" | **CAADRIA 2019** (24th International Conference on Computer-Aided Architectural Design Research in Asia) |
| **2020** | Wang, Janssen, Ji | "SSIEA: a hybrid evolutionary algorithm for supporting conceptual architectural design" | **AI EDAM** (Artificial Intelligence for Engineering Design, Analysis and Manufacturing — Cambridge University Press) |

- Likai Wang 프로필: XJTLU(시안 자오통-리버풀 대학) 건축학과 조교수, **EvoMass** 플러그인 개발자
- 출처: https://www.xjtlu.edu.cn/en/study/departments/design-school/architecture/department-staff/academic-staff/staff/likai-wang
- LinkedIn: https://www.linkedin.com/in/likai-wang-77ab79185/

### 2-2. EvoMass와의 관계

- **EvoMass**: Rhino-Grasshopper 플러그인. 매스 디자인 생성 + 최적화 + 탐색 통합 도구.
- **SSIEA**는 EvoMass 내부의 **다목적 최적화 엔진**으로 탑재됨 (NSGA-II 대체로 자체 알고리즘 사용).
- Food4Rhino: https://www.food4rhino.com/en/app/evomass

---

## 3. Nature Scientific Reports 2025 인용은 사실인가?

**Yes — 실제 존재하는 논문임 (VERIFIED).**

### 3-1. 정확한 서지정보

| 항목 | 값 |
|---|---|
| 제목 | Multi-objective optimization of daylighting performance and solar radiation for building geometry using a hybrid evolutionary algorithm |
| 저자 | **S. Lou, X. Luo, Z. Chen, Zhiji Gao, Ruida Wang, Linjin Feng, Guoyi Zhang, Yanfei Zhang, Ye Zhao, Bei Li** |
| 저널 | **Scientific Reports** (Nature Publishing Group, Open Access) |
| 권/논문번호 | Vol. **15**, Article **26644** |
| 게시일 | **2025-07-22** |
| DOI | **10.1038/s41598-025-12165-6** |
| URL | https://www.nature.com/articles/s41598-025-12165-6 |
| PDF | https://www.nature.com/articles/s41598-025-12165-6.pdf |
| PMC | https://pmc.ncbi.nlm.nih.gov/articles/PMC12284102/ |
| Semantic Scholar | https://www.semanticscholar.org/paper/Multi-objective-optimization-of-daylighting-and-for-Lou-Luo/e103be1d101b5664c95fb987a8579e5a0ab869b9 |

### 3-2. 논문이 실제로 한 일

- 도구: **EvoMass** (Grasshopper) + **SSIEA** (다목적 최적화 엔진)
- 변수: 건물 길이/너비/높이/방향 + 매스 분포 (additive + subtractive 생성)
- 목적함수: (1) 여름-겨울 외피 일사량 변화 최소화, (2) UDI(Useful Daylight Illuminance) 최대화
- 사례연구: 항저우(중국) 공공건물
- 결과: reference building 대비 일사 균형 **+26.89%**, 일조 성능 **+19.85%**

### 3-3. **중요한 구분** — 논문이 SSIEA를 *발명*한 게 아님

이 논문은 **SSIEA의 응용 사례**임. 알고리즘 자체는 Wang/Janssen/Ji 2020에서 정의됨. 발표 자료에서:

- ❌ "SSIEA, Nature 2025에서 제안된 알고리즘" (오해 유발)
- ✅ "SSIEA(Wang+ 2020) 알고리즘을 일조-일사 매스 최적화에 적용한 Lou+ 2025"

---

## 4. 발표 자료에서 인용을 *어떻게* 수정해야 안전한가

### 현재 표기 (메모리 기준)
> "Steady-State Island Evolutionary Algorithm (SSIEA), Nature Scientific Reports 2025 기반"

### 권장 수정 (3가지 옵션 — 발표 톤에 맞게 선택)

**옵션 A — 응용 논문만 인용 (가장 안전, 간결)**
> "SSIEA(Steady-State Island Evolutionary Algorithm) — *Lou et al., Scientific Reports 15:26644 (2025)* 의 일조-일사 다목적 최적화 워크플로우 기반"

**옵션 B — 알고리즘 원전 + 응용 둘 다 인용 (가장 정확, 학술 발표 권장)**
> "본 시스템의 매스 최적화 엔진은 **SSIEA** *(Wang, Janssen & Ji, AI EDAM 2020)* 를 채용했으며, 일조-일사 다목적 응용 사례인 *Lou et al. (Sci. Rep. 15:26644, 2025)* 의 워크플로우를 참고했다."

**옵션 C — 슬라이드 한 줄 (캡션용)**
> "Based on SSIEA (Wang+ 2020) — as applied to daylighting/solar mass optimization in Lou+ 2025, *Sci. Rep.* 15:26644."

### 절대 쓰지 말아야 할 표현
- "Nature 2025 논문에서 *제안한* SSIEA" ← Nature지가 아니라 Sci. Rep.이고, *제안*이 아니라 *적용*
- "Nature Scientific Reports" ← 정확히는 그냥 *Scientific Reports* (Nature 그룹 산하 OA지). 학회 발표에서 "Nature 논문"이라고 하면 *Nature* 본지를 떠올리는 사람이 있어 오해 가능 → "*Scientific Reports* (Nature Publishing Group)" 로 명확히

---

## 5. 추가 확인 사항

- **알고리즘이 NSGA-II와 다른가?**: SSIEA는 NSGA-II와 다른 별개의 다목적 EA. NSGA-II는 비지배 정렬 기반, SSIEA는 island + steady-state 기반. 발표에서 "NSGA-II 변종"이라고 표현하면 *틀림*.
- **arxiv preprint가 있는가?**: 직접 검색 결과 **없음**. Lou 2025는 Sci. Rep. 직출판. Wang 2020(AI EDAM) 도 arxiv 미게재.
- **EvoMass vs 25_ACE 프로젝트의 design 모듈**: 이 프로젝트의 `ARR/backend/design/`은 AUA NSGA-II 포팅으로, SSIEA가 아닌 NSGA-II 기반임 (CLAUDE.md 참고). 발표에서 "우리 시스템의 매스 최적화는 NSGA-II — Lou+ 2025의 SSIEA 워크플로우에서 영감" 같은 표현이 가장 정확함.

---

## 6. 출처

- [Multi-objective optimization of daylighting performance and solar radiation for building geometry using a hybrid evolutionary algorithm | Scientific Reports](https://www.nature.com/articles/s41598-025-12165-6)
- [PMC mirror PMC12284102](https://pmc.ncbi.nlm.nih.gov/articles/PMC12284102/)
- [Semantic Scholar entry — Lou-Luo](https://www.semanticscholar.org/paper/Multi-objective-optimization-of-daylighting-and-for-Lou-Luo/e103be1d101b5664c95fb987a8579e5a0ab869b9)
- [Diversity and Efficiency — A Hybrid Evolutionary Algorithm Combining an Island Model with a Steady-state Replacement Strategy (CAADRIA 2019)](https://www.researchgate.net/publication/332543054)
- [Likai Wang — XJTLU staff page](https://www.xjtlu.edu.cn/en/study/departments/design-school/architecture/department-staff/academic-staff/staff/likai-wang)
- [EvoMass on Food4Rhino](https://www.food4rhino.com/en/app/evomass)
