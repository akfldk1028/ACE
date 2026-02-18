# arXiv 논문 분석: 우리 데이터로 할 수 있는 연구

> 검색일: 2026-02-09
> 키워드: multi-agent termination, LLM-as-Judge, token efficiency, convergence, debate quality

---

## 1. 수집된 핵심 논문 (18편)

### A. 토큰 효율성 & 런타임 최적화

| # | 논문 | 날짜 | 핵심 |
|---|------|------|------|
| 1 | **Stop Wasting Your Tokens** (2510.26585) | 2025-10 | SupervisorAgent: 실시간 토큰 낭비 감지 + 개입. MAS의 excessive token consumption 문제 정량화 |
| 2 | **Augmented Runtime Collaboration** (2512.00740) | 2025-11 | AAAI 2026 채택. Bi-criteria routing: 성능+효율 동시 최적화. Static topology vs Dynamic 비교 |
| 3 | **DyTopo: Dynamic Topology Routing** (2602.06039) | 2026-02 | Manager가 매 라운드 sparse communication graph 재구성. 라운드별 need/offer 매칭 |

### B. 종료/수렴 판단 & 품질 평가

| # | 논문 | 날짜 | 핵심 |
|---|------|------|------|
| 4 | **Agentic Uncertainty** (2602.06948) | 2026-02 | 에이전트의 자기 성공 예측: 22% 성공률인데 77% 예측 (과신). pre/during/after 불확실성 측정 |
| 5 | **Verification-Aware Planning (VeriMAP)** (2510.17109) | 2025-10 | handoff 실패 = 종료 이유의 핵심. output format + task interpretation 오정렬 정량화 |
| 6 | **Reliability-Aware Adaptive Self-Consistency (ReASC)** (2601.02970) | 2026-01 | count-based stopping → evidence sufficiency 전환. 샘플링 비용 42% 절감 |
| 7 | **Self-Consistency Tradeoffs** (2601.06423) | 2026-01 | 정확도↑ ≠ 추론 품질↑. 다수결 정답 ≠ 올바른 추론 경로. Faithfulness 분석 |

### C. LLM-as-Judge (품질 자동 평가)

| # | 논문 | 날짜 | 핵심 |
|---|------|------|------|
| 8 | **FairJudge** (2602.06625) | 2026-02 | position/length/format bias 제거한 debiased LLM judge. pointwise vs pairwise 일관성 |
| 9 | **IRT for LLM Judge** (2602.00521) | 2026-01 | Item Response Theory로 LLM judge 신뢰도 진단. 관찰 출력 수준 → 잠재 능력 수준 분석 |
| 10 | **Rethinking Rubric Generation** (2602.05125) | 2026-02 | Rubric-guided judge → reward signal로 확장. 주관적·다차원 평가 체계화 |

### D. 에러 귀인 & 디버깅

| # | 논문 | 날짜 | 핵심 |
|---|------|------|------|
| 11 | **ECHO: Hierarchical Error Attribution** (2510.04886) | 2025-10 | agent-level + step-level 실패 귀인. binary search 대비 정확도/일관성↑ |
| 12 | **DiLLS: Layered Summary** (2602.05446) | 2026-02 | CHI 2025. raw log → layered summary 변환. 개발자 디버깅 시간 단축 |

### E. MAS 아키텍처 & 과학적 프레임워크

| # | 논문 | 날짜 | 핵심 |
|---|------|------|------|
| 13 | **Towards a Science of Collective AI** (2602.05289) | 2026-02 | MAS를 "trial-and-error" → "rigorous science"로. Attribution 모호성 = 핵심 병목 |
| 14 | **Dynamic Role Assignment for Debate** (2601.17152) | 2026-01 | Meta-Debate로 역할 배정 최적화. 전문성 기반 agent 선택 |
| 15 | **Evolutionary Generation of MAS** (2602.06511) | 2026-02 | 진화 알고리즘으로 MAS 아키텍처 자동 생성. rigid template 대 expressive 구조 |
| 16 | **Among Us: Malicious Contributions** (2602.05176) | 2026-02 | multi-agent debate에서 악의적 에이전트 영향 정량화. routing/debate/merging 4가지 협업 방식 비교 |
| 17 | **Data-Centric Interpretability for MARL** (2602.05183) | 2026-02 | SAE + LLM-summarizer로 훈련 중 행동 변화 해석. Meta-Autointerp 도입 |
| 18 | **AutoGen Studio** (2408.15247) | 2024-08 | 우리 플랫폼의 기반. No-code multi-agent prototyping + debugging |

---

## 2. 우리가 수집하는 파라미터 (코드 수정 후)

### 실행마다 자동 수집되는 파라미터

| 파라미터 | 변수명 | 타입 | 수집 위치 |
|----------|--------|------|-----------|
| **종료 이유** | `stopReason` | string | `msg.data.task_result.stop_reason` |
| **실행 시간** | `duration` | number (초) | `msg.data.duration` |
| **입력 토큰 합계** | `totalTokensIn` | number | `turns[].tokensIn` 합산 |
| **출력 토큰 합계** | `totalTokensOut` | number | `turns[].tokensOut` 합산 |
| **총 턴 수** | `turnCount` | number | `turns.length` |
| **에이전트 턴 수** | `agentTurnCount` | number | agent 타입만 필터 |
| **마지막 에이전트** | `terminatedBy` | string | 마지막 agent turn의 source |
| **팀 패턴** | `teamProvider` | string | `RoundRobinGroupChat`, `SelectorGroupChat`, etc. |
| **에이전트별 메시지** | `turns[]` | array | source + content + timestamp + messageType |
| **에이전트별 토큰** | `turns[].tokensIn/Out` | number | 개별 LLM 호출 단위 |
| **타임스탬프** | `turns[].timestamp` | ISO string | 각 메시지 시점 |
| **LLM 호출 상세** | `llm_call_event` | JSON | 모델명, usage, response |
| **세션 ID** | `currentSessionId` | number | 다회 실행 추적 |
| **런 ID** | `currentRunId` | string | 개별 실행 식별 |

### 도출 가능한 2차 파라미터 (수집된 데이터에서 계산)

| 도출 파라미터 | 계산 방법 | 단위 |
|---------------|-----------|------|
| **토큰 효율성** | `totalTokens / agentTurnCount` | tokens/turn |
| **토큰 비용** | `totalTokens × model_price` | USD |
| **평균 응답 시간** | `timestamps 간격 평균` | 초 |
| **에이전트 참여도** | `agent별 턴수 / 전체 턴수` | % |
| **응답 길이 추세** | `content.length per turn` | chars |
| **토큰 소비 추세** | `tokensIn+Out per turn` (누적 곡선) | tokens |
| **에이전트 활성 순서** | `turns[].source 시퀀스` | sequence |
| **수렴 속도** | `마지막 N턴의 응답 유사도 변화율` | cosine delta |
| **종료 패턴 분포** | `stopReason 빈도 히스토그램` | categorical |

---

## 3. 연구 제안: 우리 데이터로 할 수 있는 것

### 연구 1: 패턴별 종료 효율성 비교 (즉시 가능)

**RQ**: AutoGen의 6가지 팀 패턴(RoundRobin, Selector, Swarm, MagenticOne, Reflection, A2A)은 종료 효율에서 어떤 차이를 보이는가?

**방법**:
- 동일 태스크 셋 (10~20개) × 6패턴 × 3회 반복 = 180~360 실행
- 측정: `duration`, `totalTokens`, `agentTurnCount`, `stopReason` 분포

**측정 지표** (모두 우리가 수집 중):
| 지표 | 파라미터 | 통계 |
|------|----------|------|
| 실행 시간 | `duration` | mean ± std |
| 토큰 비용 | `totalTokensIn + totalTokensOut` | mean, median |
| 턴 효율 | `agentTurnCount` | mean |
| 종료 원인 | `stopReason` | chi-square 분포 |
| 토큰/턴 | `totalTokens / agentTurnCount` | 효율성 비율 |

**관련 논문**: [1] Stop Wasting Tokens, [2] Augmented Runtime Collaboration, [13] Science of Collective AI

**참신성**: 기존 논문은 커스텀 프레임워크를 비교. AutoGen Studio의 6개 내장 패턴을 동일 조건에서 비교하는 연구는 없음

---

### 연구 2: 종료 시점 품질 검증 - "너무 일찍? 너무 늦게?" (LLM-as-Judge 필요)

**RQ**: 현재 rule-based 종료가 최적 시점에 일어나는가? 일찍 끝나면 품질 하락, 늦게 끝나면 토큰 낭비.

**방법**:
1. 실행 로그에서 각 턴의 content 수집 (이미 수집 중)
2. 마지막 에이전트 응답에 LLM-as-Judge 점수 매기기 (G-Eval 방식)
3. 중간 턴들에도 소급 점수 매기기 → "최적 종료 시점" 도출
4. `실제 종료 턴 - 최적 종료 턴 = 종료 지연(overshoot)` 계산

**추가 수집 필요**:
- G-Eval score: 별도 LLM API 호출 (GPT-4o-mini로 저비용 가능)
- 턴별 점수 곡선

**측정 지표**:
| 지표 | 의미 |
|------|------|
| `overshoot` | 최적 대비 몇 턴 더 돌았는가 (양수=낭비, 음수=조기종료) |
| `wasted_tokens` | overshoot × avg_tokens_per_turn |
| `quality_at_stop` | 실제 종료 시점 품질 점수 |
| `quality_at_optimal` | 최적 시점 품질 점수 |
| `pattern_overshoot_avg` | 패턴별 평균 overshoot |

**관련 논문**: [4] Agentic Uncertainty, [6] ReASC, [7] Self-Consistency Tradeoffs, [8] FairJudge

**참신성**: rule-based 종료의 "정확도"를 quality-aware 기준으로 사후 평가하는 연구. 매우 새로운 접근.

---

### 연구 3: 에이전트 수렴 감지 - 반복 탐지 & 안정성 분석 (즉시 가능)

**RQ**: 멀티에이전트 토론에서 "수렴"은 언제 일어나며, 어떤 신호로 감지할 수 있는가?

**방법**:
1. 에이전트별 응답 시퀀스에서 cosine similarity 계산 (턴 간)
2. `similarity[t] - similarity[t-1]` = 수렴 속도 (delta)
3. delta < threshold가 K라운드 연속 → "수렴 감지"
4. KS-statistic으로 라운드별 분포 안정성 측정

**우리 데이터에서 바로 계산 가능**:
| 파라미터 | 계산 | 소스 |
|----------|------|------|
| 턴별 임베딩 | `content` → embedding API | turns[].content |
| 코사인 유사도 | `sim(emb[t], emb[t-1])` | 연속 턴 비교 |
| 수렴 delta | `sim[t] - sim[t-1]` | 시계열 |
| 반복 감지 | 동일 agent의 유사 응답 카운트 | source 필터링 |
| 라운드별 분포 | 각 라운드 에이전트 응답 분포 | agentTurnCount |
| KS-statistic | `scipy.stats.ks_2samp()` | 연속 라운드 비교 |

**관련 논문**: [3] DyTopo, [14] Dynamic Role Assignment, [7] Self-Consistency Tradeoffs

---

### 연구 4: 에러 귀인과 종료 관계 (즉시 가능)

**RQ**: 실행이 error로 끝나는 경우, 어떤 에이전트가 어떤 단계에서 실패를 일으키는가?

**방법**:
1. `status === 'error'`인 실행만 필터
2. `turns[]`의 마지막 몇 턴 분석 → 어떤 에이전트에서 에러 발생?
3. 패턴별 에러율 비교
4. 에러 원인 분류: tool_call 실패, handoff 실패, timeout, 키워드 미감지

**우리 데이터**:
| 파라미터 | 소스 |
|----------|------|
| 에러 발생 여부 | `status === 'error'` |
| 에러 메시지 | `error` 필드 |
| 마지막 활성 에이전트 | `terminatedBy` |
| 에이전트별 턴 히스토리 | `turns[]` filtered by source |
| 패턴 타입 | `teamProvider` |

**관련 논문**: [11] ECHO, [12] DiLLS, [5] VeriMAP

---

### 연구 5: Adaptive 종료 전략 제안 (구현 필요)

**RQ**: rule-based 종료를 quality-aware 종료로 대체하면 토큰 비용 대비 품질이 개선되는가?

**방법**:
1. 연구 1-4의 데이터 기반으로 "adaptive stopping rule" 설계
2. 조건: `if (convergence_detected AND quality_score > θ) → STOP`
3. baseline (MaxMessages=10) vs adaptive 비교
4. Pareto frontier: Quality vs Token Cost

**새로운 종료 파라미터 (연구가 제안할 것)**:
| 파라미터 | 수식 | 의미 |
|----------|------|------|
| θ_quality | G-Eval score threshold | 품질 임계값 |
| θ_convergence | cosine delta threshold | 수렴 임계값 |
| K_patience | 연속 수렴 라운드 수 | 안정성 기준 |
| λ_cost | token cost weight | 비용 가중치 |
| 종합 점수 | `Q(t) - λ·C(t)` | 품질-비용 트레이드오프 |

**관련 논문**: [1] Stop Wasting Tokens, [6] ReASC, [4] Agentic Uncertainty, [13] Science of Collective AI

**참신성**: AutoGen Studio에서 직접 실험 가능한 adaptive termination. 논문 [1]은 SupervisorAgent라는 별도 프레임워크 필요. 우리는 기존 AutoGen termination API에 플러그인 형태로 구현 가능.

---

## 4. 파라미터 종합 매핑

### 독립변수 (실험 조건)

| 변수 | 값 범위 | 설명 |
|------|---------|------|
| `team_pattern` | RoundRobin, Selector, Swarm, MagenticOne, Reflection, A2A | 팀 구성 패턴 |
| `num_agents` | 2, 3, 4, 5 | 에이전트 수 |
| `max_messages` | 5, 10, 15, 20, 30 | 최대 메시지 종료 조건 |
| `task_type` | coding, math, creative, analysis, debate | 태스크 난이도/유형 |
| `model` | gpt-4o-mini, gpt-4o, claude-sonnet, etc. | LLM 모델 |
| `termination_type` | MaxMessage, TextMention, Token, Timeout, Adaptive(new) | 종료 조건 |

### 종속변수 (측정 결과) - 모두 자동 수집

| 변수 | 단위 | 논문 대응 |
|------|------|-----------|
| `duration` | 초 | [1][2] runtime efficiency |
| `total_tokens` | count | [1] token consumption |
| `tokens_per_turn` | tokens/turn | [1] efficiency ratio |
| `agent_turn_count` | count | [3] communication rounds |
| `stop_reason` | categorical | [5][13] termination attribution |
| `terminated_by` | agent name | [11] error attribution |
| `error_rate` | % | [11][12] failure analysis |
| `participation_balance` | Gini coefficient | [14][16] agent contribution fairness |

### 도출 변수 (추가 분석 필요)

| 변수 | 계산 방법 | 논문 대응 |
|------|-----------|-----------|
| `quality_score` | LLM-as-Judge (G-Eval) | [8][9][10] |
| `convergence_round` | cosine delta < 0.05 연속 2회 | [3][7] |
| `overshoot` | actual_stop - optimal_stop | [4][6] |
| `response_diversity` | Vendi Score of agent responses | [16] |
| `faithfulness` | 추론 경로 정확성 | [7] |

---

## 5. 논문 작성 로드맵

### Phase 1: 데이터 수집 (1~2주)
- 태스크 셋 구성: 5 유형 × 4개 = 20개 태스크
- 6 패턴 × 20 태스크 × 3회 = 360 실행
- 자동 로깅: executionStore → JSON export 기능 추가 필요

### Phase 2: 기초 분석 (1~2주) - 연구 1, 4
- 패턴별 효율성 비교 (ANOVA/Kruskal-Wallis)
- 에러 귀인 분석 (confusion matrix by pattern)
- 종료 원인 분포 (chi-square test)

### Phase 3: 품질 분석 (2~3주) - 연구 2, 3
- G-Eval 점수 매기기 (API 비용 발생)
- 수렴 감지 알고리즘 구현
- 최적 종료 시점 분석

### Phase 4: Adaptive Termination (2~3주) - 연구 5
- AutoGen TerminationCondition 커스텀 구현
- Quality-aware stopping rule
- A/B 비교 실험

### Phase 5: 논문 작성 (2~3주)
- 타깃 학회: EMNLP 2026, ACL 2026 Workshop, AAAI 2027
- 제목 후보:
  1. "When Should Multi-Agent Systems Stop? An Empirical Study of Termination Patterns in LLM-based Collaborative Systems"
  2. "Quality-Aware Adaptive Termination for Multi-Agent LLM Systems: Beyond Rule-Based Stopping"
  3. "Overshoot or Undershoot? Measuring Termination Efficiency in AutoGen Multi-Agent Patterns"

---

## 6. 핵심 인사이트: 왜 이 연구가 중요한가

### 기존 논문의 Gap (우리가 채울 수 있는 것)

1. **[1] Stop Wasting Tokens**: 별도 SupervisorAgent 프레임워크 필요 → 우리는 **AutoGen 내장 패턴에서 직접 측정**
2. **[4] Agentic Uncertainty**: single-agent의 자기 예측만 연구 → 우리는 **multi-agent 간 합의 과정에서의 불확실성**
3. **[13] Science of Collective AI**: "attribution ambiguity" 문제 제기만 → 우리는 **stop_reason + agent turn + token으로 실증 분석**
4. **[11] ECHO**: 사후 에러 귀인만 → 우리는 **실시간 수렴 감지 + 사전 종료**
5. **[6] ReASC**: single-model self-consistency만 → 우리는 **multi-agent 합의 기반 adaptive stopping**

### 우리만의 차별점

- **실제 프로덕션 프레임워크** (AutoGen Studio) 위에서 실험
- **6개 패턴 동시 비교** (기존 논문은 대부분 1~2개 패턴만)
- **프론트엔드 시각화** (Flow Monitor)로 실시간 관찰 가능
- **end-to-end 파이프라인**: 데이터 수집 → 분석 → adaptive stopping → 재실험
