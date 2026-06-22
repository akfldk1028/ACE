# 검색 결과 요약 — SSIEA 기반 건축 매스 최적화 인용 검증

**작성일**: 2026-04-30
**대상 발표**: 2026-05-06 랩미팅 (SSIEA 기반 건축 매스 최적화)
**검증 도구**: arxiv-mcp (`search_papers`) + WebSearch (Nature/PMC/Semantic Scholar)

---

## 1. 핵심 결론 (TL;DR)

**SSIEA Nature Scientific Reports 2025 인용 — 검증 결과: 실제 존재함 (VERIFIED REAL)**

- 정확한 논문 제목: *"Multi-objective optimization of daylighting performance and solar radiation for building geometry using a hybrid evolutionary algorithm"*
- 저자: **Lou S., Luo X., Chen Z. et al.** (S. Lou 외 9명)
- 저널: **Scientific Reports** (Nature 산하), Volume 15, Article **26644** (2025)
- DOI: **10.1038/s41598-025-12165-6**
- 게시일: **2025-07-22**
- URL: https://www.nature.com/articles/s41598-025-12165-6
- PMC 미러: https://pmc.ncbi.nlm.nih.gov/articles/PMC12284102/

**알고리즘 정확한 정의**: 이 논문이 SSIEA를 새로 만든 게 아니라, **기존 SSIEA(Wang/Janssen/Ji 2020)**를 EvoMass(Grasshopper 플러그인)에 통합해 일조-일사 다목적 최적화에 적용한 *응용* 연구. SSIEA 알고리즘 자체의 원전은 아래 §3 참조.

---

## 2. 사용한 검색어 + 결과 개수

### arxiv-mcp 검색 (총 7개 키워드)

| # | 검색어 | 총 결과 수 | 관련 논문 (sample) |
|---|---|---|---|
| 1 | `Steady-State Island Evolutionary Algorithm` | 366,180 | **0건 직접 일치** (모두 evolutionary 일반 / 우주 steady-state) |
| 2 | `SSIEA daylighting solar building` | 200,902 | **0건** (solar physics만 매칭됨) |
| 3 | `SSIEA architectural mass optimization` | 676,456 | **0건** (math.OC 일반 최적화) |
| 4 | `multi-objective genetic algorithm building daylight` | 422,545 | 0건 직접, 일부 일반 다목적 |
| 5 | `NSGA-II architectural design optimization` | 607,654 | 0건 (CS 일반) |
| 6 | `island model evolutionary algorithm building geometry` | 1,559,147 | 0건 직접 |
| 7 | `Pareto multi-objective building mass form-finding` | 429,510 | 0건 직접 |

**결론**: arxiv에는 SSIEA / 건축 매스 최적화 분야 논문이 **사실상 없음**. 이 분야는 *Building & Environment, Energy & Buildings, Scientific Reports, Sustainable Cities and Society* 같은 응용 학술지가 주류. arxiv 검색만으로는 발표 인용 검증 불가능.

### WebSearch 보조 검증 (3개 쿼리)

| # | 검색어 | 결과 |
|---|---|---|
| 1 | `"Steady-State Island Evolutionary Algorithm" SSIEA Nature Scientific Reports 2025 daylighting` | **Hit**: nature.com/articles/s41598-025-12165-6 (1순위) |
| 2 | `"SSIEA" "Steady-State Island" multi-objective daylight solar radiation` | **Hit** 동일 논문 + EvoMass 매칭 |
| 3 | `Likai Wang EvoMass Steady-State Island algorithm 2020` | **Hit**: SSIEA 원전 = Wang/Janssen/Ji 2020 AI EDAM |

---

## 3. 발표 자료에 즉시 인용 가능한 논문 Top 3

### Tier 1 (반드시 인용)

1. **Lou et al. 2025** (*Scientific Reports*) — 발표의 핵심 인용. SSIEA + EvoMass + 일조 + UDI 26.89%/19.85% 개선. → 발표 자료의 "SSIEA Nature 2025" 인용은 **이 논문을 가리킴**.

2. **Wang, Janssen, Ji 2020** (*AI EDAM* / Cambridge) — SSIEA **알고리즘의 원전**. 제목: *"SSIEA: a hybrid evolutionary algorithm for supporting conceptual architectural design"*. 발표에서 "Lou 2025가 적용한 SSIEA의 원본 알고리즘" 표현을 정확히 쓰려면 함께 인용해야 함.

3. **Wang, Janssen, Ji 2019 (CAADRIA)** — SSIEA 초기 발표: *"Diversity and Efficiency — A Hybrid Evolutionary Algorithm Combining an Island Model with a Steady-state Replacement Strategy"* (24th CAADRIA Proceedings).

### Tier 2 (배경 인용 가능)

4. **Likai Wang 2022** (*International Journal of Architectural Computing*) — *"Workflow for applying optimization-based design exploration to early-stage architectural design — Case study based on EvoMass"*. EvoMass 워크플로우 설명.

5. **Wang et al. 2023** (*IJAC*) — *"Reverse passive strategy exploration for building massing design — An optimization-aided approach"*.

자세한 리스트는 `02_RELATED_PAPERS.md` 참고.

---

## 4. 발표 자료에서 인용을 *어떻게* 표기해야 하는지

현재 표기 (메모리 기준):
> "Steady-State Island Evolutionary Algorithm (SSIEA), Nature Scientific Reports 2025 기반"
> "Multi-objective optimization of daylighting & solar radiation for building geometry using SSIEA"

**검증 후 안전한 표기 (둘 다 정확)**:

옵션 A — Lou 2025만 인용 (간결):
```
[Lou et al. 2025] Multi-objective optimization of daylighting performance
and solar radiation for building geometry using a hybrid evolutionary algorithm.
Scientific Reports 15:26644. https://doi.org/10.1038/s41598-025-12165-6
```

옵션 B — SSIEA 원전 + 응용 둘 다 인용 (정확):
```
SSIEA 알고리즘 [Wang, Janssen & Ji 2020]을 건축 매스 일조-UDI 다목적
최적화에 적용한 [Lou et al. 2025] (Sci. Rep. 15:26644) 워크플로우 기반.
```

옵션 C — 발표 슬라이드 한 줄용:
```
Based on SSIEA (Wang+ 2020), as applied to daylighting/solar mass
optimization in Lou et al., Sci. Rep. 15:26644 (2025).
```

**권장**: 옵션 B 또는 C. 발표 자료에 "Nature Scientific Reports 2025 기반"만 쓰면 *알고리즘 자체*가 2025 논문에서 새로 만들어졌다는 오해를 줄 수 있음. 정확히는 "Lou 2025가 적용한 SSIEA"가 맞음.

---

## 5. 그 밖의 메모

- arxiv는 이 분야(건축 매스 최적화)에 빈약함 → 발표에 arxiv 인용을 끼워넣기는 부자연스러움. Sci. Rep / IJAC / B&E / E&B 위주로 인용 구성하는 게 자연스러움.
- arxiv 외 발견된 매우 관련성 높은 EvoMass 후속 연구는 `02_RELATED_PAPERS.md`에 정리.
- Lou 2025 PDF 직접 다운로드: https://www.nature.com/articles/s41598-025-12165-6.pdf (오픈액세스)
