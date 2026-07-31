# 📄 COLM 2026 Submission Checklists & Research Memory

## 🚨 Critical Memo (Original User Feedback)
- **P4**: 어떤 카테고리에 어떤 프롬프트/질문을 했는지 구체적 누락 (Appendix A 보강 필요)
- **P5-7**: "라우팅이 에이전트를 이긴다" 이상의 유의미한 결론(Insight) 도출 필요 (Inference Scaling 관련)
- **P8**: 품질 궤적 실험 시 구체적 질문 명시 및 `refl-2`, `refl-3` 등 에이전트 수별 비교 라인 차트 추가
- **P9**: 결과 도출 시 사용된 프롬프트/질문 상세화
- **P10**: 한계효용($\Delta U$) 수식의 작동 원리 및 작용 기전 상세 설명
- **P11**: 패턴별/에이전트 수별/카테고리별 설명 보강
- **P12**: OpenAI vs. Claude 비교 도표 및 통계적 근거(κ 등) 전무 -> **현재 최우선 순위**

---

## 🚀 Gemini's 80%+ Accept Strategy (Last 14 Days)

### Phase A: 평가 신뢰도($\kappa$) 강화 [Critical]
- [ ] **GPT-5.4 재채점**: `cross_validate_scoring.py` 수정 (n=100, 모델 업그레이드)
- [ ] **$\kappa$ 점수 0.40+ 달성**: Moderate 이상의 신뢰도 확보 및 논문 반영
- [ ] **정성적 분석**: 모델 간 불일치 샘플 3개 분석 (왜 점수가 다른가?)

### Phase B: 하이브리드 종료 실험 [High]
- [ ] **로직 구현**: `Keyword OR $\Delta U$` 하이브리드 종료 조건 코딩
- [ ] **Fast-Track 런**: `swm4`, `debate3` 대상으로 하이브리드 실효성 입증 (50 runs)
- [ ] **품질 보존 증명**: "일찍 멈춰도 품질($Q$)은 그대로"임을 T-test로 증명

### Phase C: COLM 프레이밍 (Framing) [High]
- [ ] **용어 전환**: Agent System -> **Inference-time Scaling & Saturation Analysis**
- [ ] **Abstract 수정**: "멀티 에이전트 구조가 추론 시간 확장에 미치는 영향"으로 강조

### Phase D: 통계 및 9페이지 압축 [Medium]
- [ ] **Bonferroni 교정**: 다중 비교에 대한 통계적 엄밀함 문구 삽입
- [ ] **9p 메인 바디**: 그림/표 재배치 및 압축 (Appendix 적극 활용)

---

## 📅 Submission Schedule
- **Abstract Due**: 2026-03-26 (D-9)
- **Full Paper Due**: 2026-03-31 (D-14)
- **Goal**: 3/25까지 모든 실험 데이터 및 LaTeX 초안 완성

---
*Created by Gemini CLI for AG-Research Project.*
