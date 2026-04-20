# AG-Research TODO — COLM 2026 (Abstract 3/26, Paper 3/31)

## 핵심 발견 (현재 확보)
1. 비용 위계 뒤집힘: Swm-3(3명) < RR-2(2명). 기존 상식 A<B<C<D 틀림
2. Debate 품질 하락: 턴 증가 → 3.8→3.4→3.3. "더 대화=더 좋다" 틀림
3. B1/B2 스케일링 정량 확인: 1.48배 vs 3.17배 (기존 분류 확인 수준)
4. 키워드 종료 7/8 최적 (negative result)
5. 비용 예측: R²=0.54, agents×maxmsg 상호작용이 핵심 (Exp06)
6. 역U자 관계: Solo(Easy/Hard), Refl-2(Medium만) — 멀티에이전트는 중간 난이도에서만 효과적 (Exp07)
7. Solo 비용효율 전 난이도 지배 (Exp07)

## P0 — 반드시 해야 함

### [DONE] 방향 C: 비용 예측 회귀 모델 (Exp06)
- [x] Feature 추출 스크립트 작성
- [x] Linear/Ridge/RF 학습 + 5-fold CV
- [x] R² / MAE 리포트 → R²=0.54 (RF best)
- [x] Feature importance 시각화 → fig9_cost_prediction.png
- [x] 논문 Section 4.7 추가

### [DONE] 방향 A: 난이도 실험 (Exp07)
- [x] Easy/Med/Hard 과제 15개 설계
- [x] task_suite_difficulty.json 작성
- [x] 225회 실험 실행 (220회 성공)
- [x] G-Eval 채점 완료
- [x] Kruskal-Wallis 통계 검정 + 시각화
- [x] 논문 Section 4.8 작성
- [x] Conclusion/Discussion 업데이트
- [x] 방향 C 모델로 비용 예측 → 실측 비교 (교차 검증 R²=0.12)

### [DONE] 교수 피드백 반영 (memo.md 7개 항목)
- [x] p4: 25개 과제+프롬프트 → Appendix A + Section 3.2 설명 강화
- [x] p5-7: 결론 약함 → Discussion 5.2 핵심 메시지 3개 추가
- [x] p8: 품질궤적 질문 연결 → Finding 22 구체적 과제 예시 추가
- [x] p9: 프롬프트 스펙 → Section 3.2.1 Agent System Prompts 추가
- [x] p10: ΔU 수식 설명 → 직관적 해석 문단 추가
- [x] p11: 패턴/에이전트/카테고리 분리 → Table 16a 요약 추가
- [x] p12: Claude vs GPT 비교 → Table 31b 추가

### [PARTIAL] Human Eval 보강
- κ=0.244 → 논문에서 방어 논리 대폭 강화 (3/12):
  - κ_w가 낮은 이유: 체계적 척도 차이(GPT 관대편향), 순서 일치는 양호
  - Spearman ρ (0.38-0.62)가 ordinal 분석에 적절한 지표임을 명시
  - Liu et al. (2023) G-Eval 선행연구와 비교하여 norms 내에 있음을 입증
  - 모든 발견이 비교적(comparative) 주장임을 강조 → ordinal claim에 강건
  - LLM cross-validation을 삼각검증(triangulation)으로 재프레이밍
- **여전히 필요**: 추가 인간 평가자 1명 (κ≥0.60 목표) → P1으로 강등
- **소요**: ~1일

### [DONE] 논문 약점 보강 Phase 1 (3/12)
- [x] 4.2.1 평가검증: κ=0.244 방어 논리 3단계 (척도차이, ordinal적합, 선행연구비교)
- [x] 3.2 과제설계: 개방형 과제 선택의 방법론적 근거 추가
- [x] 기여#5 ΔU: "부정적 결과의 가치" 프레이밍 강화 (진단도구 → 이중기여)
- [x] 5.3 한계: 약점 인정 → 선제적 방어로 전환 (11개 항목)
- [x] R²=0.54: Cohen(1988) 기준 맥락화 (사회과학 R²>0.50 = strong)
- [x] 참고문헌: Cohen(1988), Zheng(2023), Wang(2024) 추가
- [x] 영/한 동기화 완료

### [DONE] 논문 약점 보강 Phase 2 (3/12)
- [x] Abstract 축약: ~350단어→~280단어, 반직관적 발견 선도형으로 재작성
- [x] Section 1.4 포지셔닝: "empirical benchmarking study" 명시 (GLUE/HELM 비유)
- [x] Section 4.8 effect sizes: η²_H 계산 추가 (난이도 0.249 large vs 패턴 0.020 small)
- [x] Finding 43: η² 비율 12.6x, 패턴 내 난이도 민감도 차이 신규 분석
- [x] Finding 44: 95% CI + Cohen's d + Mann-Whitney U 추가 (refl2 vs solo d=1.26)
- [x] paper_stats.txt: 전체 통계 보고서 생성 (SD/CI/effect sizes/post-hoc)
- [x] 영/한 동기화 완료

### [TODO] 9-page COLM 포맷팅
- paper_draft.md → LaTeX main.tex 동기화
- Abstract 300단어 이내
- **소요**: ~1일

## P1 — 하면 좋음

### [TODO] 교차 모델 확장
- n=5 → n=8~10 GPT-4o-mini 비교
- **소요**: ~1일

### [DONE] PPT 프롬프트 업데이트
- [x] NOTEBOOKLM_PROMPTS_V2.md 슬라이드 10-13 실측값 반영
- [x] Exp06/07 결과 + 교수 피드백 반영

### [DONE] README/TODO 현행화
- [x] 5 experiments → 7 experiments
- [x] Exp06/07 결과 테이블 추가
- [x] 미보유 데이터 업데이트

## 타임라인
```
2/25-3/3   방향 C+A 실험+분석 — DONE
3/4-10     논문 draft 통합 + 교수 피드백 반영 — DONE (3/11)
3/11-15    LaTeX 동기화 + 9-page 포맷팅
3/16-20    Human Eval 보강 + 교차모델 확장 + PPT 최종본
3/21-25    최종 교정
3/26       Abstract 제출
3/31       Paper 제출
```

일단 봣는데 제목이 이어져야지되고 
abstract 가 전반적으로 좀 임팩트강벗어 그리고 a<b2 이거는 뒤에명시되잇는데 abstarct 에명시 되잇는게 말이안되고 

autogen 을반복해야해 ? 이것도 약점가틍ㄴ데 

그리고 1.4 에 알고리즘위한게 아니다 이걸 굳이 넣거나 이렇게 약점이 될껄 적나라하게넣어야해? 알고리즘을 위한거맞긴하자 

그리고 (참조 논문 이걸 ) 계속 풀논문명넣어야해? 뭐 abcd 이건안되나 ?

그리고 figure 1 아예 하나도안보임 가시성좋게 제대로 생성해야해 이게 젤중요한데 
그리고 도메인질문 어떤거햇는지 뒤에만잇는데 이렇게만 끝내는게 맞는지 ?

6번결론도 조오오온나 약한데 순차적으로 생각해봐 논문 기깔란거 찾아서 좀 참조도하고 논문mcp로 
