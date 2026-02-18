# Multi-Agent Termination Criteria & Quality Scoring Research

> 연구 목적: 멀티에이전트가 "끝"이라고 판단하는 근거/수치 조사
> 작성일: 2026-02-09

---

## 핵심 발견

**현재 프로덕션 프레임워크(AutoGen, CrewAI, LangGraph)는 품질 기반 종료가 없다.**
- 리소스 한계(메시지 수, 토큰, 시간) 또는 키워드 감지("TERMINATE", "APPROVED")에 의존
- 품질 인식 종료는 **연구 시스템**에서만 발견됨 (G-Eval, KS-statistic, 다수결 투표)

**연구와 프로덕션 사이의 격차가 크다** - 수학적 도구(Beta-Binomial 혼합 모델, 신뢰도 가중 투표, Kolmogorov-Smirnov 통계)는 존재하지만 주류 프레임워크에 미통합

---

## 1. AutoGen 종료 조건 (우리 프로젝트 - 소스코드 분석)

### 1.1 내장 종료 조건 11가지

| 클래스 | 로직 | 수치 기반 |
|--------|------|-----------|
| **MaxMessageTermination** | `message_count >= max_messages` | 정수 카운터 |
| **TextMentionTermination** | 특정 텍스트 감지 ("APPROVED", "TERMINATE") | 문자열 매칭 (이진) |
| **TokenUsageTermination** | `prompt_tokens + completion_tokens >= limit` | 토큰 카운터 |
| **TimeoutTermination** | `time.monotonic() - start_time >= timeout` | 벽시계 비교 |
| **StopMessageTermination** | StopMessage 수신 시 | 메시지 타입 체크 |
| **HandoffTermination** | 특정 target으로 HandoffMessage 감지 | ID 매칭 |
| **FunctionCallTermination** | 특정 함수 실행 시 | 함수명 매칭 |
| **SourceMatchTermination** | 특정 에이전트가 응답 시 | 소스 매칭 |
| **TextMessageTermination** | TextMessage 수신 시 | 타입 체크 |
| **ExternalTermination** | 외부에서 `.set()` 호출 | Boolean 플래그 |
| **FunctionalTermination** | 커스텀 Python 함수 | 임의 로직 |

소스 위치: `autogen_agentchat/conditions/_terminations.py` (lines 20-615)

### 1.2 우리 프로젝트 팀별 종료 조건

```
Reflection Team (품질 개선):
  TextMentionTermination("APPROVED") OR MaxMessageTermination(6)
  -> critic이 "APPROVED" 말하면 종료, 아니면 최대 6턴

Debate Team (찬반 토론):
  TextMentionTermination("TERMINATE") OR MaxMessageTermination(10)
  -> judge가 "TERMINATE" 말하면 종료, 아니면 최대 10턴

Handoff Team (고객 서비스):
  HandoffTermination(target) OR MaxMessageTermination(10)
  -> 특정 에이전트로 핸드오프 또는 최대 10턴
```

### 1.3 종료 시 반환 데이터

```python
# StopMessage (종료 메시지)
class StopMessage:
    content: str         # WHY: "Maximum messages reached" 등
    source: str          # WHO: "MaxMessageTermination" 등
    models_usage: RequestUsage  # 토큰 사용량

# TaskResult (최종 결과)
class TaskResult:
    messages: List[...]  # 전체 대화 메시지
    stop_reason: str     # StopMessage.content에서 추출

# RequestUsage (토큰 메트릭)
class RequestUsage:
    prompt_tokens: int
    completion_tokens: int
```

### 1.4 핵심: AutoGen에 없는 것

- **신뢰도 점수 (Confidence Score)**: 없음
- **품질 메트릭**: 없음 - 시맨틱 마커("APPROVED")에 의존
- **Logprobs**: `CreateResult.logprobs`에 존재하지만 종료 결정에 미사용
- **Thought/Reasoning**: `CreateResult.thought` 필드 존재 (추론 모델용)

---

## 2. 학술 연구: 품질 기반 종료 메커니즘

### 2.1 G-Eval (Liu et al., EMNLP 2023) - 확률 가중 스코어링

가장 널리 채택된 LLM-as-Judge 스코어링 공식.

**핵심 수식:**
```
score = Sum_{i=1}^{n} p(s_i) * s_i
```
- `s_i` = 미리 정의된 점수 (예: 1~5점)
- `p(s_i)` = LLM이 각 점수 토큰에 부여하는 확률
- 결과: 가중 합산으로 연속 점수

**워크플로우:**
1. 루브릭에서 chain-of-thought 평가 단계 생성
2. LLM에게 이산 척도(1-5)로 평가 요청
3. 각 가능한 점수의 토큰 레벨 확률 추출
4. 가중 합산으로 세밀한 연속 점수 계산

**성능**: GPT-4 기반 요약 평가에서 인간 판단과 Spearman 상관 0.514
**통과 임계값**: DeepEval 구현에서 기본 0.5

> 논문: https://arxiv.org/abs/2303.16634

### 2.2 Self-Consistency + Majority Voting (Wang et al., 2023)

**핵심 원리**: N개 추론 경로 샘플링 -> 최종 답변 추출 -> 다수결 투표

**수학적 기반 (이항 모델):**
```
X ~ Binomial(N, p)
P(다수결 정답) = P(X > N/2)
```
p=0.6, N=40이면 다수결 정답 확률이 거의 1에 수렴

**신뢰도 가중 확장 (CISC, Taubenfeld et al., ACL 2025):**
```
Answer = argmax_{a} Sum_{RP_i: Answer(RP_i)=a} CS_i
```
- `CS_i ∈ [0,1]` = 각 추론 경로의 신뢰도 점수
- 표준 self-consistency 대비 필요 샘플 **40% 이상 감소**

> 논문: https://aclanthology.org/2025.findings-acl.1030/

### 2.3 Dynamic Self-Consistency (Aggarwal & Welleck, NAACL 2025)

고정 샘플 수 없이 **중단 기준** 도입:

**버퍼 정의:** `B = {RP_i | CS_i >= T}`
**중단 규칙:** `|B| >= N일 때 샘플링 중단`

**최적 파라미터:**
- 신뢰도 임계값 T = **0.1**
- 버퍼 용량 N = **3**
- 손실 함수: cross-entropy

> 논문: https://arxiv.org/abs/2408.17017

---

## 3. 멀티에이전트 토론 & 합의 메커니즘

### 3.1 Adaptive Stability Detection (Hu et al., 2025) - 가장 수학적으로 엄밀

**판단 정확도 모델 (Beta-Binomial 혼합):**
```
S^t ~ w^t * BB(k, alpha_1^t, beta_1^t) + (1-w^t) * BB(k, alpha_2^t, beta_2^t)
```

**안정성 감지 (Kolmogorov-Smirnov 통계):**
```
D_t = sup_{psi in [0,1]} |F^t(psi) - F^{t-1}(psi)|
```

**종료 조건:**
```
D_t < 0.05가 2 연속 라운드이면 중단
```

**정리 4.2**: 토론 정확도가 다수결 투표보다 증명 가능하게 우월:
```
P(D(Z^T) = y) > P(MV(Z^0) = y)
```

> 논문: https://arxiv.org/abs/2510.12697

### 3.2 투표 프로토콜 비교 (ACL 2025)

| 프로토콜 | 메커니즘 | 임계값 |
|----------|----------|--------|
| Simple Voting | 1인 1표, 다수결 | >50% |
| Ranked Voting | 순위 매기기, 최저 누적순위 승리 | 서수 비교 |
| Cumulative Voting | 각 에이전트 25포인트 분배 | 최고 점수 |
| Approval Voting | 복수 승인 | 최다 승인 |
| Supermajority | 2/3 이상 동의 필요 | 66% |
| Unanimity | 만장일치 | 100% |

> 논문: https://arxiv.org/abs/2502.19130

### 3.3 핵심 발견: "Debate or Vote" (2025)

**다수결 투표만으로도 멀티에이전트 토론의 성능 향상 대부분을 설명 가능.**
토론 자체는 확률적으로 마팅게일(martingale) - 기대 정확도를 개선하지 않음.

> 논문: https://arxiv.org/abs/2508.17536

---

## 4. Self-Evaluation & Reflection 스코어링

### 4.1 Reflexion (Shinn et al., NeurIPS 2023)

**평가 신호:** 이진 보상 `r_t = M_e(tau_t)`

**휴리스틱 규칙:**
- 반복 감지: 동일 행동+응답 3회 연속 -> 자기 성찰 트리거
- 비효율 감지: 궤적 30단계 초과 -> 자기 성찰 트리거
- 실패 상한: 동일 태스크 3회 연속 실패 시 종료

> 논문: https://arxiv.org/abs/2303.11366

### 4.2 LLM 신뢰도 캘리브레이션 (NAACL 2024)

**핵심 발견:**
- LLM은 빈번하게 **잘못 캘리브레이션**됨 - 틀린 출력에 과신, 맞는 출력에 과소신뢰
- 프롬프트 프레이밍, 방해요소, 학습 목표에 크게 영향
- "Calibrated Reflection" 접근: 루브릭 기반 초기 신뢰도 생성 -> 추론 성찰 -> 거리 인식 캘리브레이션으로 점수 업데이트

> 논문: https://aclanthology.org/2024.naacl-long.366/

---

## 5. 벤치마크 수준 평가 메트릭

### 5.1 MultiAgentBench / MARBLE (ACL 2025 Main)

**마일스톤 KPI:**
```
KPI_overall = (1/N) * Sum_{j=1}^{N} (n_j / M)
```
- N = 에이전트 수, M = 총 마일스톤, n_j = 에이전트 j 기여 마일스톤

**협력 점수:**
```
CS = (Communication_score + Planning_score) / 2
```
- 각각 LLM judge가 1-5 리커트 척도로 평가

> 논문: https://arxiv.org/abs/2503.01935

### 5.2 CLEAR Framework (2025) - 기업용 다목적 평가

| 차원 | 측정 대상 |
|------|-----------|
| **Cost** | API 토큰 소비, 추론 비용, 비용 정규화 정확도 |
| **Latency** | 응답 시간, 처리량 |
| **Efficacy** | 태스크 정확도, 단계별 정확성 |
| **Assurance** | 안전성, 규정 준수 |
| **Reliability** | 일관성, 다양한 조건에서의 견고성 |

> 논문: https://arxiv.org/abs/2511.14136

---

## 6. 종합 분류표

| 카테고리 | 방법 | 수치 기반 | 품질 인식? |
|----------|------|-----------|-----------|
| 리소스 한계 | MaxMessage, Timeout, TokenUsage | 정수/실수 임계값 | X |
| 키워드 감지 | TextMention("TERMINATE") | 문자열 매칭 (이진) | X |
| 다수결 투표 | Self-Consistency | Binomial(N,p) | 암묵적 |
| 가중 투표 | G-Eval, CISC | `Sum p(s_i)*s_i` | O |
| 안정성 감지 | KS-statistic | D_t < 0.05 연속 2라운드 | O |
| 이진 피드백 | Reflexion, 유닛 테스트 | Pass/Fail (0/1) | O (이진) |
| 휴리스틱 | 반복/비효율 감지 | 행동 주기 >3, 단계 >30 | X |
| 마일스톤 | MultiAgentBench KPI | n_j / M 비율 | O |
| LLM-as-Judge | G-Eval 루브릭 | 1-5 리커트 또는 0-100 | O |
| 합의 임계값 | 다수/초다수/만장일치 | 50% / 66% / 100% | 암묵적 |

---

## 7. 연구 제안: 우리 프로젝트에서 할 수 있는 것

### 7.1 즉시 측정 가능한 수치
- **토큰 사용량** (prompt_tokens, completion_tokens) - 이미 수집 중
- **메시지 수** (턴 카운트) - 이미 수집 중
- **종료 이유** (StopMessage.content) - 이미 수집 중
- **종료 에이전트** (StopMessage.source) - Flow Monitor에 "by {agent}" 표시 중

### 7.2 추가 구현 가능한 메트릭
1. **G-Eval 스코어링**: 최종 답변에 LLM-as-Judge 적용 (logprobs 활용)
2. **자기 일관성 점수**: 동일 질문 N회 실행 -> 답변 일치율 측정
3. **토론 안정성**: KS-statistic로 에이전트 믿음 분포 수렴 감지
4. **Reflection 품질 추적**: critic의 "APPROVED" 전 수정 횟수

### 7.3 실험 설계
1. 동일 태스크를 5개 패턴(Sequential, Selector, Reflection, Debate, Handoff)으로 실행
2. 각 패턴별 수집: 턴 수, 토큰 사용량, 종료 이유, 실행 시간
3. 최종 답변 품질을 G-Eval로 평가 (1-5점)
4. 패턴별 품질/비용 트레이드오프 분석

---

## References

1. Liu et al., "G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment", EMNLP 2023 - https://arxiv.org/abs/2303.16634
2. Wang et al., "Self-Consistency Improves Chain of Thought Reasoning in Language Models", 2023 - https://arxiv.org/abs/2203.11171
3. Hu et al., "Multi-Agent Debate with Adaptive Stability Detection", 2025 - https://arxiv.org/abs/2510.12697
4. Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning", NeurIPS 2023 - https://arxiv.org/abs/2303.11366
5. Taubenfeld et al., "Confidence Improves Self-Consistency", ACL 2025 - https://aclanthology.org/2025.findings-acl.1030/
6. Aggarwal & Welleck, "Dynamic Self-Consistency", NAACL 2025 - https://arxiv.org/abs/2408.17017
7. "Voting or Consensus? Decision-Making in Multi-Agent Debate", ACL 2025 - https://arxiv.org/abs/2502.19130
8. "Debate or Vote: Which Yields Better Decisions?", 2025 - https://arxiv.org/abs/2508.17536
9. CONSENSAGENT, ACL 2025 - https://aclanthology.org/2025.findings-acl.1141/
10. Free-MAD: Consensus-Free Multi-Agent Debate, 2025 - https://arxiv.org/abs/2509.11035
11. MAR: Multi-Agent Reflexion, 2025 - https://arxiv.org/abs/2512.20845
12. MultiAgentBench / MARBLE, ACL 2025 - https://arxiv.org/abs/2503.01935
13. Beyond Task Completion Framework, 2025 - https://arxiv.org/abs/2512.12791
14. CLEAR Framework, 2025 - https://arxiv.org/abs/2511.14136
15. Confidence Estimation and Calibration Survey, NAACL 2024 - https://aclanthology.org/2024.naacl-long.366/
16. AutoGen Termination Docs - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html
