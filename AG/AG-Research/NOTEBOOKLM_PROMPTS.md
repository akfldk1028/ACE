# NotebookLM PPT 생성 프롬프트

> 소스 파일: `notebooklm_source_kr.md` 를 NotebookLM에 업로드한 후 아래 프롬프트 복붙

---

```
이 논문을 기반으로 연구 발표용 PPT 슬라이드를 만들어줘.

## 필수 조건
- 한국어, 흰색 배경
- 각 슬라이드: 제목 + 핵심 포인트 + 발표자 노트(대본)
- 모든 수치는 소스 문서의 실제 데이터 사용 (반올림/추정 금지)
- 정확히 15장
- 모든 실험 결과에는 반드시 차트/도표가 있어야 함 (숫자만 나열 금지)

## ★★★ 절대로 빠뜨리면 안 되는 4가지 ★★★

### 필수 1: 실험에 사용한 실제 질문을 카테고리별로 보여줘야 함
- 25개 과제 × 9개 도메인(과학/CS/역사/철학/법정치/게임/공학/경영/의학)
- 모든 14개 팀 구조에 **완전히 동일한 25개 질문** 투입. 차이는 팀 구조에서만 발생
- 질문 예시 4개 원문:
  - 사실형: "Explain the three laws of thermodynamics and their practical implications in engineering."
  - 분석형: "Compare the fall of the Roman Empire with the decline of the British Empire."
  - 기술형: "Implement an LRU cache with O(1) get and put operations."
  - 창의형: "What if the printing press had been invented in Song Dynasty China instead of Gutenberg's Europe?"
- 카테고리별 에이전트 프롬프트:
  - Solo: "Answer thoroughly. When complete, TERMINATE"
  - RR-3: researcher→writer→reviewer. reviewer: "If sufficient, say TERMINATE"
  - Sel-3: Selector LLM → 3명 expert. "Select the next role. Only return the role name"
  - Swm-3: triage → handoff. "Delegate to the right specialist. Use handoff"
  - Refl-2: generator⇄critic. "If quality sufficient, say APPROVED"
  - Debate-3: advocate↔critic→judge. "Deliver balanced VERDICT"
  - Pipeline: [Stage1]→[Stage2]. "ANALYSIS_DONE" / "TERMINATE"
  - MoA: 3명 병렬→aggregator. "Synthesize three perspectives"

### 필수 2: 14개 패턴의 학술적 근거
  | 범주 | 패턴 | 학술적 근거 | AutoGen 구현 |
  |------|------|-----------|-------------|
  | S | Solo(1명) | single-agent baseline | AssistantAgent |
  | A | RR-2/3/4 | Chain (Masterman 2025) | RoundRobinGroupChat |
  | B1 | Sel-3/4 | Star (Masterman 2025) | SelectorGroupChat |
  | B2 | Swm-3/4 | Mesh (Masterman 2025) | Swarm + Handoff |
  | C | Refl-2/3 | Reflexion (Shinn, NeurIPS 2024) | RoundRobinGroupChat |
  | C | Deb-3/4 | Debate (Du, ICML 2024) | SelectorGroupChat |
  | D | Pipeline(5명) | 순차 정제 | 자체 PipelineTeam |
  | D | MoA(4명) | Li et al. (ICLR 2025) | 자체 MoATeam |
- Tran et al. (2025) centralized vs distributed 분리 → B1/B2 분리 정당화

### 필수 3: 패턴별 종료 행동 — "어떻게 멈췄고, 몇 턴 걸렸는지"
- 논문 제목이 "언제 멈춰야 하는가"이므로 이 도표가 반드시 있어야 함:
  | 패턴 | 평균 턴 | 종료 키워드 | 키워드 성공률 | 오류율 |
  |------|--------|-----------|------------|-------|
  | Solo | 2.0 | TERMINATE | 100% | 0% |
  | RR-2 | ~3 | TERMINATE | 높음 | 8% |
  | RR-3 | 4.6 | TERMINATE | 높음 | 23% |
  | RR-4 | ~6 | TERMINATE | 낮음 | 72% |
  | Sel-3 | 3.7 | TERMINATE | 100% | 0% |
  | Sel-4 | 4.2 | TERMINATE | 100% | 0% |
  | Swm-3 | 8.8 | TERMINATE | 1~6% | 11% |
  | Swm-4 | 26.1 | TERMINATE | 28% | 76% |
  | Refl-2 | 3.2 | APPROVED | 100% | 0% |
  | Debate-3 | 4.6 | VERDICT | 100% | 0% |
  | Pipe | 6.0 | ANALYSIS_DONE→TERMINATE | 100% | 0% |
  | MoA | ~8 | (없음) | 0% | 100% |

### 필수 4: 결론은 "refl-2가 짱"이 아님
- 핵심 발견 2가지:
  1. **비용 위계 뒤집힘**: Swm-3(3명) < RR-2(2명). 에이전트 수 ≠ 비용
  2. **Debate 품질 하락**: 턴↑ → 품질 3.8→3.3 하락. "더 대화 = 더 좋다"는 틀림
- 트레이드오프 표:
  | 목표 | 추천 | 이유 | 주의 |
  |------|------|------|------|
  | 최고 품질 | Refl-2 | 4.80, 손실 0.00 | 비용 4배, 확장 시 2.31배 |
  | 최저 비용 | Swm-3 | 멀티에이전트 최저 | 4명 시 3.17배, CV=0.67 |
  | 예측 가능 | Debate-3 | CV=0.14 | 품질 최악(3.35) |
  | 안전 확장 | Sel-3/4 | 오류 0%, 1.48배 | 품질 중간 |

---

## 슬라이드 구성 (15장)

### 1. 제목
- "멀티 에이전트 팀은 언제 멈춰야 하는가?"
- 부제: 14가지 토폴로지의 종료 역학 체계적 연구 | 2,000회+ 실험

### 2. 연구 동기 + 선행 연구 갭
- 현행 종료: max턴, TERMINATE, 타이머 → 토폴로지 무관 획일 적용
- 종료 후회 3가지: 과잉/과소/토폴로지 불일치
- Hu et al.(토론만), REFRAIN(단일만), Aegean(합의만) → 14패턴 비교 연구 없음

### 3. 14개 패턴 학술적 근거 + 토폴로지 다이어그램 (★ 필수 2)
- 필수 2의 표 전체 넣기
- 토폴로지 다이어그램 6개 (노드-화살표):
  - S: [Agent] 단독
  - A: [R]→[W]→[Rev]→... 순환
  - B1: ★[Selector]★ → [A/B/C] 방사형
  - B2: [Triage]↔[Spec A]↔[Spec B] 메시
  - C: [Gen]⇄[Critic] 루프 / [Adv]↔[Cri]→[Judge]
  - D: [팀1]→[팀2] 순차 / [P1][P2][P3]→[Agg] 병렬

### 4. 실제 질문 + 카테고리별 처리 방식 (★ 필수 1)
- 질문 예시 4개 원문 반드시 표시
- 카테고리별 에이전트 프롬프트 표

### 5. 실험 설계
- ★ **표**: 5개 실험 요약
  | 실험 | 목적 | 횟수 | 측정 |
  |------|------|------|------|
  | 01 | 비용 비교 | 980회 | 토큰, 시간 |
  | 02 | 품질 궤적 | 100회(276턴) | G-Eval 5점 |
  | 03 | 의미 수렴 | 분석 | Sentence-BERT |
  | 04 | 종료 실패 | 분석 | 오류 유형 |
  | 05 | ΔU 종료 | 800회 | 턴/토큰 변화 |

### 6. 패턴별 종료 행동 (★ 필수 3 전체)
- ★ **차트 A**: 패턴별 평균 턴 수 막대그래프 (Solo 2.0 ~ Swm-4 26.1)
- ★ **차트 B**: 키워드 종료 성공률 누적 막대 (성공 vs MaxMsg 강제)
- 필수 3의 표 전체
- 핵심: B1=100% 안정, B2=1~28% 불안정, C=내장 신호로 100%, MoA=0%

### 7. Exp01 — 비용 랭킹 + 에이전트수별 스케일링
- ★ **차트 A**: 14패턴 총 토큰 바차트 (Solo 빨간 점선)
  Solo(1,287) < Swm3(4,196) < RR2(4,759) < ... < MoA(22,333) = 17.4배
- ★ **차트 B**: 범주별 에이전트 수 증가 다중 선 그래프
  - A: 2→3→4명 (오류 8→23→72%)
  - B1: 3→4명 **1.48배** (준선형)
  - B2: 3→4명 **3.17배** (초선형)
  - C-반성: 2→3명 2.31배
  - C-토론: 3→4명 1.25배 ("턴 규율")

### 8. Exp02 — 품질: 패턴별 + 과제유형별 (두 뷰)
- ★ **차트 A (패턴 중심)**: 5패턴 × 4유형 히트맵
  | 패턴 | 전체 | 사실 | 분석 | 기술 | 창의 |
  |------|------|-----|------|------|------|
  | Refl-2 | 4.80 | 4.8 | 4.6 | 5.0 | 4.8 |
  | RR-3 | 4.50 | 4.8 | 4.6 | 4.8 | 3.8 |
  | Swm-3 | 3.65 | 4.2 | 3.0 | 3.8 | 3.6 |
  | Sel-3 | 3.40 | 3.4 | 4.0 | 2.2 | 4.0 |
  | Debate-3 | 3.35 | 3.8 | 3.2 | 2.6 | 3.8 |
- ★ **차트 B (과제유형 중심)**: 유형별 그룹 막대 — 같은 유형 내 패턴 비교
  - 사실형: 패턴 간 차이 작음 (4.8~3.4) → 아무거나 OK
  - 분석형: rr3=4.6, refl2=4.6 우위 / swm3=3.0 최저
  - 기술형: refl2=**5.0** vs sel3=**2.2** → 격차 2.3배! 반드시 refl-2
  - 창의형: refl2=4.8 우위, 나머지 3.6~4.0 균등

### 9. Exp02 — 품질 궤적 + 종료 후회
- ★ **차트 A**: 5개 패턴 궤적 라인그래프 (x=턴, y=G-Eval)
  - RR-3: 3.9→4.5→4.1 (고원형)
  - Refl-2: 3.9→**4.8**→4.0 (정점형, 손실 0.00)
  - Debate-3: 3.8→3.4→3.3 (**하락형**, 손실 0.65)
  - Sel-3, Swm-3 궤적도 포함
- ★ **차트 B**: 종료 후회 비교 막대
  | 패턴 | 후회(턴) | 품질 손실 |
  |------|---------|---------|
  | Swm-3 | +0.2 | 0.20 |
  | Refl-2 | +0.6 | **0.00** |
  | Debate-3 | +2.0 | 0.65 |
  | RR-3 | +2.6 | 0.05 |
- 핵심: Debate는 더 대화할수록 나빠진다

### 10. B1 vs B2 — 정반대 스케일링
- ★ **차트**: B1/B2 지표 비교 이중 막대
  | 지표 | Sel-3 | Sel-4 | Swm-3 | Swm-4 |
  |------|-------|-------|-------|-------|
  | 총 토큰 | 7,851 | 11,621 | 4,196 | 13,321 |
  | 평균 턴 | 3.5 | 4.1 | 10.2 | 25.0 |
  | 턴당 토큰 | 2,270 | 2,538 | 523 | 544 |
  | 오류율 | 0% | 0% | 11% | 76% |
- B1=적은 턴+긴 독백, B2=많은 턴+짧은 핸드오프. 완전히 다른 대화 패턴

### 11. Exp03+04 — 수렴 분석 + 종료 실패 유형
- ★ **차트 A**: 수렴율 + cosine 이중 축
  | 패턴 | 수렴율 | 평균 cosine |
  |------|-------|-----------|
  | Pipe | 32% | 0.612 |
  | B1 | 26% | 0.428 |
  | A | 16% | 0.351 |
  | B2 | 12% | 0.348 |
  | C | **0%** | 0.673 |
  핵심: Debate cosine 가장 높은데 수렴 0% → 의미 수렴 종료 불가
- ★ **차트 B**: 종료 실패 유형 3가지 + 과제유형별 오류율
  | 실패 유형 | 범주 | 메커니즘 |
  |----------|------|---------|
  | 토큰 폭발 | A(RR-4) | context 초과, 72% |
  | 턴 폭발 | B2(Swm-4) | 핸드오프 순환, 76% |
  | 키워드 실종 | D(MoA) | TERMINATE 미출력, 100% |
  과제유형별: 사실형 0% / 기술형 RR-4=100% (가장 위험)

### 12. Exp05 — ΔU 수식 + 800회 통제실험
- ΔU(t) = ΔQ(t) − λ·ΔC(t). 모든 패턴 1.1~2.4턴 수렴. λ 튜닝 불필요
- ★ **차트 A**: 패턴별 ΔU 수렴 턴 막대
- ★ **차트 B**: ΔU 적용 전/후 토큰 변화 이중 막대
  | 패턴 | 기준선 | 적응적 | 변화 |
  |------|-------|-------|------|
  | Swm-4 | 13,321 | 3,941 | **−70%** |
  | RR-3 | 10,121 | 13,381 | +32% |
  | Sel-3 | 7,851 | 12,837 | +63% |
  | Refl-2 | 5,237 | 18,783 | +258% |
- 핵심 반전: 7/8 패턴에서 역효과. TERMINATE가 이미 최적. ΔU는 Swm 전용 보조

### 13. Cost-Aware Topology Selection — 비용 예측 모델 (★ 알고리즘 contribution)
- **핵심 아이디어**: 멀티에이전트 시스템을 실행하기 전에, 토폴로지 특성만으로 비용을 예측할 수 있는가?
- ★ **차트 A**: 예측 vs 실측 산점도 (R² 표시)
- ★ **차트 B**: Feature Importance 막대 (어떤 특성이 비용을 가장 잘 설명하는가)
- Features: topology_type, n_agents, max_messages, tokens_per_turn
- Targets: total_tokens, turn_count, error_rate
- 모델: Linear Regression → Ridge → Random Forest 비교
- **실무 가치**: 실행 전 비용 추정 → 토폴로지 사전 선택 가능

### 14. 과제 난이도별 최적 패턴 (★ 실용 contribution)
- **핵심 질문**: 간단한 과제와 복잡한 과제에 같은 패턴을 써야 하는가?
- Easy/Medium/Hard × 5패턴 × 3반복 = 225회 추가 실험
- ★ **차트 A**: 난이도 × 패턴 품질 히트맵
- ★ **차트 B**: 난이도별 비용효율곡선 (x=토큰, y=품질) — Pareto frontier
- 기대 결과:
  - Easy → solo/swm-3 충분 (비용 대비 품질 차이 미미)
  - Hard → refl-2 필수 (품질 격차 극대화)
  - Medium → 토폴로지별 갈림 (가장 흥미로운 구간)
- **실무 가치**: 과제 복잡도 판단 → 최적 패턴 자동 선택 가이드

### 15. 핵심 결론 + 한계점
- **Contribution 1 (알고리즘)**: 토폴로지 특성 기반 비용 예측 모델 — 실행 전 사전 추정
- **Contribution 2 (실용)**: 과제 난이도별 최적 패턴 가이드 — Easy→solo, Hard→refl-2
- **발견 1**: 비용 위계 뒤집힘 — Swm-3(3명) < RR-2(2명)
- **발견 2**: Debate 품질 하락 — 턴↑ → 3.8→3.3
- **한계**: κ=0.244, 단일 프레임워크, 교차 모델 n=5
- **종료는 토폴로지에 종속된다. 비용은 예측 가능하고, 최적 패턴은 과제 난이도에 따라 다르다.**
```
