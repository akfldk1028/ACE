# COLM 2026 제출 계획

> **학회**: COLM 2026 (Conference on Language Modeling)
> **논문**: "When Should Multi-Agent Teams Stop? A Systematic Study of Termination Dynamics Across 14 Coordination Topologies"
> **마감**: Abstract 3/26, Paper 3/31 (AoE)
> **학회 일정**: San Francisco, Oct 6-9, 2026
> **포맷**: 9 pages + unlimited references/appendix
> **작성일**: 2026-02-24

---

## 왜 COLM?

- Topic 16에 "multi-agents learning" 명시
- 2024년 시작 신생 학회 → 경쟁률 상대적으로 낮음
- 9 pages + unlimited appendix = 이 논문 분량에 적합
- 데이터 2000+ runs, LaTeX 이미 완성 → 최소 수정으로 제출 가능
- Reject 되더라도 리뷰어 피드백 → 다음 학회(EMNLP/AAMAS 2027) 보강 자료

---

## 현재 상태 (2026-02-24)

### 완료된 것
- [x] 실험 전체 완료 (Exp01~05, 2000+ runs)
- [x] Solo baseline (25 runs)
- [x] Cross-model validation (GPT-4o-mini, 125 runs, ρ=0.900)
- [x] LaTeX 초안 (main.tex, figures, tables)
- [x] 한국어/영어 draft 완료
- [x] 비판적 검토 반영 (9 limitations, 톤 다운)
- [x] CI/std Table 12/18에 추가
- [x] Finding 39→15 압축 (Appendix D)

### 미완료 (해결 필요)
- [ ] Human evaluation 완료 (human_eval_sheet.csv 빈칸)
- [ ] 2nd evaluator 섭외 + 평가
- [ ] Hybrid 실험 (keyword + ΔU)
- [ ] swm3 해석 재프레이밍
- [ ] Cross-model n=5 → n=25+ 보강
- [ ] 9 pages 포맷팅 (현재 초과 상태)

---

## 논문 강점 (리뷰어에게 어필할 것)

1. **최초의 cross-topology 종료 비교** — 14 patterns, 6 categories, 1 framework
2. **규모**: 2000+ runs (기존 MAS 논문 대비 대규모)
3. **반직관적 발견**: swm3(3-agent) > rr2(2-agent) 효율
4. **ΔU 진단 프레임워크**: 기존 keyword 종료의 적합성을 정량 진단
5. **Cross-model 일반화**: Claude + GPT-4o-mini, ρ=0.900

## 논문 약점 (리뷰어가 공격할 것)

1. **Evaluation 신뢰도**: κ=0.244 (fair), human eval 미완
2. **새로운 알고리즘 없음**: empirical study (비교 분석)
3. **ΔU가 7/8 패턴에서 keyword와 동일** → 실용적 개선 불분명
4. **Single framework (AutoGen), single task type (open-ended Q&A)**
5. **swm3 "효율"의 모호함**: 실제로는 조기 종료 경향일 수 있음

---

## 5주 작업 계획

### Week 1 (2/24 ~ 3/2): 핵심 보강

| 작업 | 소요 | 우선순위 |
|------|------|---------|
| Human eval sheet 본인이 채우기 | 30분 | **P0** |
| swm3 해석 수정: "efficient" → "premature termination tendency" | 반나절 | **P0** |
| Finding 15개 최종 확정 + narrative 정리 | 1일 | **P0** |

### Week 2 (3/3 ~ 3/9): 실험 보강 (가능하면)

| 작업 | 소요 | 우선순위 |
|------|------|---------|
| Hybrid 실험 (keyword + ΔU) — 시간 되면 | 2-3일 | P1 |
| 안 되면 → Discussion에 "future work"로 명시 | - | |
| 2nd evaluator 섭외 시도 | - | P1 |

### Week 3 (3/10 ~ 3/16): LaTeX 9페이지 맞추기

| 작업 | 소요 |
|------|------|
| 본문 9 pages 이내로 압축 | 2일 |
| 나머지 → appendix로 이동 | 1일 |
| Figures/Tables 최적화 | 1일 |

### Week 4 (3/17 ~ 3/26): Abstract + 최종 교정

| 작업 | 마감 |
|------|------|
| Abstract 작성 (250 words) | 3/24 |
| 공저자 리뷰 | 3/25 |
| **Abstract 제출** | **3/26** |

### Week 5 (3/27 ~ 3/31): 최종 제출

| 작업 | 마감 |
|------|------|
| 최종 교정 + 포맷 확인 | 3/29 |
| PDF 생성 + 테스트 | 3/30 |
| **Full paper 제출** | **3/31** |

---

## 9-Page Budget

```
Section 1. Introduction + RQs          1.5 pages
Section 2. Related Work                1.0 page
Section 3. Methodology (14 topologies) 1.5 pages
Section 4. Results (핵심 findings만)    3.5 pages
Section 5. Discussion + Guidelines     1.0 page
Section 6. Conclusion                  0.5 page
References                             unlimited
Appendix                               unlimited (전체 tables, 39 findings, etc.)
```

---

## Reject 시 후속 계획

| 학회 | 마감 (예상) | 전략 |
|------|------------|------|
| EMNLP 2026 (via ARR) | ~5-6월 | COLM 리뷰 피드백 반영 + hybrid 실험 추가 |
| NeurIPS 2026 Workshop | ~9월 | MAS 워크숍 있으면 제출 |
| AAMAS 2027 | ~10월 | 풀 보강 (P0+P1+P2). 교수님 원래 추천 학회 |

---

## 체크리스트 (제출 전 최종)

- [ ] 9 pages 이내 (references/appendix 제외)
- [ ] COLM 2026 formatting guidelines 준수
- [ ] Double-blind 준수 (저자 정보 제거)
- [ ] Human evaluation 결과 포함
- [ ] All figures/tables have captions
- [ ] References 완전성 확인
- [ ] Abstract 250 words 이내
- [ ] PDF 파일 크기 확인
- [ ] OpenReview 제출 테스트
