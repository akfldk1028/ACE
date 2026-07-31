# 발표 자료에 바로 추가 가능한 인용문 5개

**용도**: 2026-05-06 랩미팅 슬라이드 / 발표문에 *그대로* 복사해서 쓸 수 있는 인용 문장.
**원칙**: 추측 금지, 검증된 서지정보(P1=Lou 2025, P2=Wang 2020, P3=Wang 2019)만 사용.

---

## 인용 1 — 발표 도입부 (가장 권장)

> 본 시스템의 매스 최적화 모듈은 **SSIEA(Steady-State Island Evolutionary Algorithm)** 를
> 일조-일사 다목적 최적화에 적용한 **Lou et al. (2025, *Sci. Rep.* 15:26644)** 의
> 워크플로우에서 영감을 받아 설계되었다.

**참고문헌 표기**:
> Lou, S., Luo, X., Chen, Z., et al. (2025). Multi-objective optimization of daylighting
> performance and solar radiation for building geometry using a hybrid evolutionary algorithm.
> *Scientific Reports*, **15**, 26644. https://doi.org/10.1038/s41598-025-12165-6

---

## 인용 2 — 알고리즘 설명 슬라이드 (가장 정확)

> SSIEA는 **island model**(부분집단 병렬 진화 + 주기적 교환)과 **steady-state replacement
> strategy**(매 세대 일부 개체만 교체)를 결합한 hybrid evolutionary algorithm으로,
> NSGA-II 대비 **다양성 보존**과 **수렴 효율**을 동시에 확보하도록 설계되었다
> [Wang, Janssen & Ji, *AI EDAM*, 2020].

**참고문헌 표기**:
> Wang, L., Janssen, P., & Ji, G. (2020). SSIEA: a hybrid evolutionary algorithm for
> supporting conceptual architectural design. *Artificial Intelligence for Engineering
> Design, Analysis and Manufacturing*, Cambridge University Press.

---

## 인용 3 — 결과/성능 비교 슬라이드

> Lou et al. (2025) 의 사례연구에서, EvoMass + SSIEA를 적용한 매스 형상은 reference
> building 대비 **여름-겨울 일사 변동을 26.89% 감소**시키고 **UDI(Useful Daylight
> Illuminance) 를 19.85% 향상**시켰다 [Lou et al., 2025, *Sci. Rep.* 15:26644].

---

## 인용 4 — 도구 설명 (EvoMass 언급)

> SSIEA는 **EvoMass** (Likai Wang, XJTLU 개발 Grasshopper 플러그인) 의
> 다목적 최적화 엔진으로 통합되어 있으며, additive/subtractive 매스 생성과
> 결합해 초기 설계 단계 성능 기반 탐색을 지원한다 [Wang, *IJAC*, 2022].

**참고문헌 표기**:
> Wang, L. (2022). Workflow for applying optimization-based design exploration to
> early-stage architectural design — Case study based on EvoMass. *International
> Journal of Architectural Computing*, 20(2). https://doi.org/10.1177/14780771221082254

---

## 인용 5 — 우리 프로젝트와 차별점 강조 (가장 안전, 정확한 표현)

> 본 연구의 매스 최적화 엔진은 NSGA-II 기반(AUA Discover v2 포팅)으로 구현되어
> 있으며, 향후 **Lou et al. (2025)** 의 SSIEA 워크플로우 — *island model + steady-state
> replacement* — 를 도입하여 다양성 보존을 강화하는 방향을 검토 중이다.

> [근거: 알고리즘 원전은 Wang, Janssen & Ji (2020); 건축 매스 일조-일사 응용은
> Lou et al. (2025); EvoMass 통합 워크플로우는 Wang (2022).]

---

## 부록 — Bibtex 한 번에 복사용

```bibtex
@article{Lou2025SSIEA,
  title   = {Multi-objective optimization of daylighting performance and solar
             radiation for building geometry using a hybrid evolutionary algorithm},
  author  = {Lou, S. and Luo, X. and Chen, Z. and Gao, Zhiji and Wang, Ruida and
             Feng, Linjin and Zhang, Guoyi and Zhang, Yanfei and Zhao, Ye and Li, Bei},
  journal = {Scientific Reports},
  volume  = {15},
  pages   = {26644},
  year    = {2025},
  doi     = {10.1038/s41598-025-12165-6},
  url     = {https://www.nature.com/articles/s41598-025-12165-6}
}

@article{Wang2020SSIEA,
  title   = {SSIEA: a hybrid evolutionary algorithm for supporting conceptual
             architectural design},
  author  = {Wang, Likai and Janssen, Patrick and Ji, Guohua},
  journal = {Artificial Intelligence for Engineering Design, Analysis and Manufacturing},
  publisher = {Cambridge University Press},
  year    = {2020}
}

@inproceedings{Wang2019CAADRIA,
  title     = {Diversity and Efficiency: A Hybrid Evolutionary Algorithm Combining an
               Island Model with a Steady-state Replacement Strategy},
  author    = {Wang, Likai and Janssen, Patrick and Ji, Guohua},
  booktitle = {Proceedings of the 24th International Conference on Computer-Aided
               Architectural Design Research in Asia (CAADRIA 2019)},
  year      = {2019}
}

@article{Wang2022EvoMassWorkflow,
  title   = {Workflow for applying optimization-based design exploration to
             early-stage architectural design — Case study based on EvoMass},
  author  = {Wang, Likai},
  journal = {International Journal of Architectural Computing},
  year    = {2022},
  doi     = {10.1177/14780771221082254}
}
```

---

## 발표 자료 적용 체크리스트

- [ ] 슬라이드에 "Nature 2025"라고만 쓰지 말 것 → "*Scientific Reports* (Nature 그룹)" 명시
- [ ] "SSIEA를 *제안한* 논문"이라는 표현 금지 → "*적용한*" 또는 "*활용한*" 사용
- [ ] 알고리즘 인용 시 P1(Lou 2025) + P2(Wang 2020) **둘 다** 적기
- [ ] 우리 시스템이 NSGA-II 기반이라면 "SSIEA 기반"이 아니라 "SSIEA 워크플로우 영감" 표현 사용 (인용 5번 참조)
- [ ] DOI는 모두 `10.1038/s41598-025-12165-6` 형태로 표기 (Nature 표준)
