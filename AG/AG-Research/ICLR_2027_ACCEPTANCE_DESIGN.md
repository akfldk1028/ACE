# ICLR 2027 Acceptance-Oriented Research Design

> 상태: 설계 확정안 · 2026-08-18
>
> 대상 저장소: `D:/Data/25_ACE/AG/AG-Research`

## 1. 결론부터

현재 초안 그대로는 ICLR 제출을 권하지 않는다. 이유는 건축 도메인이 없어서가 아니라 다음 세 문제가 동시에 있기 때문이다.

1. 논문은 “알고리즘 기여가 아니다”라고 하면서 Exp05를 학습된 estimator처럼 설명한다.
2. 실제 Exp05는 어휘량과 중복도를 사용한 ΔU heuristic이라 최근 ICLR의 adaptive-compute 연구와 비교하면 방법 기여가 약하다.
3. 39개 finding, pattern 수 표현, 교차 모델 token 비교, 미완료 human evaluation 등 논문 내부 정합성 문제가 남아 있다.

가장 현실적인 제출안은 기존 연구를 폐기하지 않고 다음 세 층으로 재구성하는 것이다.

> **대규모 topology 실증 + 작은 위험통제형 종료 방법 + 건축 hard-constraint 검증**

이는 “건축 사례만 하나 붙인 논문”보다 강하고, 5-action RL orchestration을 새로 만드는 것보다 마감 위험이 낮다.

## 2. 논문 정체성

### 작업 제목

**When Should Multi-Agent Teams Stop? Risk-Controlled Termination Across Coordination Topologies and Hard-Constraint Design**

### 한 문장 thesis

Multi-agent topology는 답의 품질뿐 아니라 “이제 충분하다”는 상태를 얼마나 관측 가능하게 만드는지도 바꾸며, topology-aware trajectory calibration과 외부 hard constraints를 결합하면 품질을 유지하면서 불필요한 팀 대화를 줄일 수 있다.

### 본문 기여 세 개

1. **Empirical map:** 13개 multi-agent topology와 solo baseline에서 종료 시점·overshoot·비용·오류를 체계적으로 측정한다.
2. **CATS:** future-benefit prediction을 궤적 단위로 calibration하는 judge-free runtime `STOP/CONTINUE` 정책을 제안한다.
3. **Architecture stress test:** 법규·주차·프로그램·형상 validator가 있는 실제 건축 설계 파이프라인에서 종료 안전성과 비용 절감을 검증한다.

본 논문은 새로운 범용 multi-agent router, 전체 설계 생성 모델, 미학 평가 모델을 주장하지 않는다.

## 3. 기존 연구에서 반드시 고칠 사실

### 패턴 수

`config.PATTERNS_ALL`에는 14개 시스템이 있다.

- 13 multi-agent topologies: `rr2`, `rr3`, `rr4`, `sel3`, `sel4`, `swm3`, `swm4`, `refl2`, `refl3`, `debate3`, `debate4`, `pipe`, `moa`
- 1 solo baseline: `solo`

따라서 본문 표현은 항상 **13 multi-agent topologies + solo baseline**으로 통일한다.

### Exp05

실제 runtime proxy는 다음과 같다.

`Q(text) = min(word_count, 500) / 50 × unique_word_ratio`

이는 learned quality estimator가 아니다. 기존 ΔU 조건은 앞으로 **legacy lexical-ΔU baseline**으로 부른다.

### 기존 결과의 사용 범위

- Exp02의 turn score는 5 patterns × 20 tasks에서 625개 state가 있는 `scores_v1.csv`를 우선 사용한다.
- split은 turn이 아니라 task/trajectory 단위로 한다.
- model이 다른 token 수를 직접 우열 비교하지 않는다.
- 비어 있는 human-evaluation sheet에 근거한 주장은 모두 삭제한다.
- Exp07의 model별 반복 수 차이를 표와 caption에 명시한다.

## 4. CATS 방법 설계

### 이름

**CATS: Constraint-Aware Team Stopping**

### 문제 정의

한 팀의 자연 종료 시점까지 관측된 궤적을 `τ = {(x_t, Q_t)}_{t=1}^T`라 한다. 각 turn에 대해 다음 label을 만든다.

`y_t = 1[max_{k>t} Q_k - Q_t > ε]`

- `y_t=1`: 계속하면 유의미한 개선이 남아 있음
- `y_t=0`: 관측된 미래에서 유의미한 개선이 없음
- primary `ε=0.02` on normalized quality
- sensitivity: `ε∈{0.01, 0.05}`

정책은 기존 자연 종료보다 더 일찍 멈출 수만 있다. 즉 offline prefix replay가 인과적으로 정당하다. 정책이 대화 내용을 바꾸거나 새로운 agent를 routing하지 않으므로, 중단 전 prefix는 원래 궤적과 동일하다.

### runtime feature

미래 점수와 LLM judge 출력은 feature에서 금지한다.

- 진행 상태: normalized turn index, max-message budget, 마지막 speaker, 고유 speaker 수
- topology: pattern category, agent count, structured-feedback 여부
- 비용: 현재·누적 input/output token, 최근 2-turn token 변화
- 표면 변화: word count, unique-token ratio, repeated n-gram ratio
- 의미 변화: 직전 state 및 누적 summary와의 embedding distance
- 종료 신호: legacy `TERMINATE` 언급, reported confidence, parsed state completeness
- 건축 전용: geometry/law/parking/program evidence completeness 및 validator status

건축 feature는 독립 validator가 runtime에 실제로 제공하는 값만 쓴다. mutation manifest, gold issue label, 미래 quality는 절대 노출하지 않는다.

### predictor

복잡한 neural model을 새로 학습하지 않는다.

- 단순 baseline: logistic regression
- primary predictor: `HistGradientBoostingClassifier`
- hyperparameter 선택은 train/development split에서만 수행
- test set을 본 뒤 model 또는 threshold를 바꾸지 않음

### trajectory-level calibration

분류기가 `p_t = P(y_t=1 | x_t)`를 출력한다고 하자. calibration trajectory `j`마다 다음 최대 nonconformity를 계산한다.

`S_j = max_{t:y_jt=1}(1-p_jt)`

개선이 남은 state가 없는 trajectory는 `S_j=0`으로 둔다. `q_α`는 finite-sample corrected `(1-α)` quantile이며 primary `α=0.10`, sensitivity `α∈{0.05,0.20}`를 쓴다.

test turn에서 class `y=1`을 prediction set에서 제외할 조건은 다음과 같다.

`1 - p_t > q_α`

개별 state가 아니라 trajectory 최대값으로 보정하므로, exchangeability가 성립하는 새 trajectory에서 개선이 남은 어느 시점이든 잘못 제외할 확률을 trajectory 수준으로 통제한다. 이는 이론적 무조건 보장이 아니라 split-conformal의 marginal guarantee이며, topology·task·model OOD에서는 empirical coverage를 별도로 보고한다.

### 최종 STOP rule

`STOP_t = calibrated_no_future_gain_t ∧ admissible_t ∧ patience_2`

건축의 `admissible_t`는 다음 중 하나다.

- `STOP_ACCEPT`: geometry/law/parking/program evidence가 완전하고 모든 hard gate가 pass이며 현재 verdict와 hash가 일치
- `STOP_REJECT`: evidence가 완전하고 최소 한 개의 검증된 blocking violation이 현재 verdict에 정확히 인용됨

그 외에는 classifier가 멈추라고 해도 CONTINUE한다.

## 5. 건축 benchmark 설계

### 연구 대상

AG가 건축 형상을 새로 생성하는 실험이 아니다. ARR가 이미 생성·compile·검증한 설계 상태를 모든 topology에 동일하게 제공하고, specialist collaboration의 검토 품질과 종료 시점을 비교한다.

이 분리는 중요하다.

- geometry source of truth는 ARR에 하나만 존재한다.
- 모든 topology가 같은 evidence와 같은 validator outcome을 본다.
- 설계 생성 차이가 topology 효과를 오염시키지 않는다.
- 논문의 중심 질문인 termination을 직접 측정한다.

### EvidencePacket

각 case는 다음 두 파일로 분리한다.

1. `public_packet`: agent에게 제공되는 evidence, hashes, program brief
2. `gold_record`: 정답 issue codes, expected verdict, mutation provenance

공개 packet 필수 영역:

- site/PNU metadata와 실행 identity
- geometry compilation status, geometry hash, manifold/watertight 관련 gate
- law graph, BCR/FAR/height/use evidence
- parking requirement, evaluated supply, hard-pass state
- program ID, capacity, adjacency/space evidence, program hash
- evidence ID와 provenance link

### 실제 도메인 범위

프로그램 세 종류를 사용한다.

- `neighborhood_living` / 근린생활시설
- `gymnasium` / 체육관
- `cultural` / 문화시설

각 case는 site, law, parking, program, geometry를 모두 포함한다. MASS 하나만 평가하는 실험으로 축소하지 않는다.

### 개발/테스트 분할

| Split | PNU | 프로그램 | 상태 | cases | 용도 |
|---|---:|---:|---:|---:|---|
| Development | 기존 2 | 3 | native + challenged | 12 | parser, feature, calibration, threshold |
| Frozen test | 신규 5 | 3 | native + challenged | 30 | 최종 보고 |

개발 PNU는 ARR에서 반복 검증된 `1168011800104170004`, `1168011800104670003`으로 고정한다. 최종 테스트 5개는 2026-08-18 저장소 snapshot에 PNU 문자열이 없고 live boundary/law/parking 조회가 성공하는 신규 대지로 2026-08-21까지 동결한다. parcel area 3개 구간과 최소 3개 행정구역을 포함하도록 deterministic stratified sampling하고, selection log와 제외 이유를 남긴다. 신규 5개 확보에 실패하면 기존 PNU를 evaluation-only group split으로 사용할 수 있지만, 이 경우 system-development 기준의 held-out site/OOD 주장은 삭제한다.

### challenged state

부정 사례를 만들기 위해 evidence payload에 한 개의 typed fault를 주입하되, ARR validator를 다시 실행해 실제 fail 상태를 만든다. 문자열 label만 바꾸는 조작은 금지한다.

fault family는 site/program에 균형 배정한다.

- stale/mismatched execution hash
- law graph 또는 legal projection failure
- parking shortage 또는 missing evaluated evidence
- program capacity/adjacency hard failure
- geometry compilation/manifold failure

mutation manifest는 gold file에만 저장한다.

### Agent output contract

모든 agent message는 자연어 분석 뒤 하나의 `ARCH_REVIEW_STATE` JSON block을 출력한다.

```json
{
  "checked_domains": ["law", "parking"],
  "blocking_issue_codes": [],
  "missing_evidence_codes": ["geometry_hash"],
  "evidence_ids": ["evidence:law_graph_agent"],
  "recommended_decision": "CONTINUE",
  "confidence": 0.72
}
```

parser는 마지막 valid block만 state로 사용하고, prefix accumulator는 이전 turn의 확인 영역과 valid citation을 보존한다. parse 실패는 임의의 pass로 바꾸지 않고 incomplete state로 처리한다.

### 역할 설계

3-agent controlled subset에서는 동일한 세 역할을 사용한다.

1. code/site + law specialist
2. parking + program specialist
3. geometry/provenance + final reviewer

대상은 `rr3`, `sel3`, `swm3`, `refl3`, `debate3`다. 이 subset에서 agent 수와 role bank를 고정해 topology 효과를 분리한다.

전체 14-system 실험에서는 각 topology의 구조에 맞게 동일 discipline을 병합/분리한다. solo는 모든 discipline을 한 prompt에 포함하고, 2-agent는 constraints와 synthesis로 묶고, 4-agent는 네 discipline을 분리한다. `pipe`와 `moa`도 같은 evidence packet과 output contract를 사용한다.

## 6. 품질 함수

건축 turn quality `Q_t∈[0,1]`는 prefix state를 gold record와 결정론적으로 비교해 계산한다.

`Q_t = 0.30 issue_F1 + 0.25 evidence_F1 + 0.20 domain_coverage + 0.25 verdict_score`

- `issue_F1`: blocking/missing issue code macro F1
- `evidence_F1`: 유효 evidence citation precision/recall
- `domain_coverage`: site/law/parking/program/geometry 확인 비율
- `verdict_score`: gold verdict와 일치하고 그 verdict의 필수 evidence가 존재할 때 1

가중치는 development 실행 전 고정한다. `0.25`씩 동일 가중한 버전을 sensitivity로 보고한다.

unsafe stop은 다음 중 하나다.

- hard gate fail인데 `STOP_ACCEPT`
- 모든 evidence가 완전하지 않은데 terminal decision
- verified blocking issue 없이 `STOP_REJECT`
- current decision의 identity/hash가 packet과 불일치

미학, 공간 경험, “좋은 형태”는 primary outcome에 포함하지 않는다. 따라서 전문가 human study는 필수가 아니다. 건축적 선호를 주장하고 싶다면 제출 이후 별도의 blinded architect study로 확장한다.

## 7. 실험 행렬

### 신규 LLM 실행

| Stage | Systems/patterns | Cases | Repeats | Runs |
|---|---:|---:|---:|---:|
| Pilot | 5 | 12 dev | 3 | 180 |
| Primary architecture | 14 | 30 test | 3 | 1,260 |
| Cross-model | 5 | 30 test | 2 | 300 |
| Canonical ARR fixed-flow | 1 | 30 test | deterministic × 1 | 30 |
| **Total** |  |  |  | **1,770** |

cross-model 5개 pattern은 controlled subset과 같은 `rr3`, `sel3`, `swm3`, `refl3`, `debate3`를 사용한다. 두 번째 model은 pilot 후 비용·API 안정성을 확인해 동결한다.

### Offline policy replay

같은 trajectory에 다음 정책을 모두 적용한다. 추가 LLM 호출은 없다.

1. full natural termination
2. max-message cap
3. keyword termination
4. legacy lexical-ΔU
5. semantic-stability patience
6. logistic predictor
7. uncalibrated gradient-boosting predictor
8. state-wise conformal ablation
9. trajectory-calibrated CATS
10. CATS without architecture hard guard
11. hindsight oracle peak stop

### Online parity

offline truncation 구현 오류를 확인하기 위해 development에서 20개 trajectory를 CATS online mode로 다시 실행한다. stop 이전 message hash, token sum, selected stop turn이 offline replay와 일치해야 한다. online parity는 새 성능 표가 아니라 구현 검증이다.

## 8. 평가 지표

### Primary

- `ΔQ = Q_stop - Q_full`
- token reduction ratio
- unsafe-stop rate
- premature-stop rate: `y_t=1`인 turn에서 stop
- overshoot: oracle peak 이후 추가 turn 수
- oracle regret: `Q_oracle - Q_stop`

### Calibration

- trajectory risk coverage
- Brier score
- expected calibration error
- topology/category별 empirical coverage
- held-out PNU/program/model coverage degradation

### Efficiency

- input/output/total tokens
- wall-clock latency
- model call count
- parse failure와 retry count
- 실제 API cost; pilot에서 측정한 가격표와 model version을 고정

## 9. 통계 계획

- primary unit: case × pattern × repeat trajectory
- 동일 case/repeat의 policy 결과를 paired 비교
- 10,000회 cluster bootstrap; 최소 clustering unit은 case, site 일반화 표에서는 PNU
- 95% confidence interval
- 여러 baseline 대비 primary comparison에 Holm correction
- 평균과 median을 모두 보고하고, heavy-tail token은 median/IQR을 주 표로 사용
- test 결과를 본 뒤 margin, ε, α, quality weight를 바꾸지 않음

zero unsafe event는 두 수준으로 보고한다.

1. run-level Wilson interval
2. PNU/case-cluster interval

30개 case가 독립인 것처럼 “위험 <1%”를 주장하지 않는다.

## 10. 사전 성공 기준과 중단 gate

### Pilot gate

다음을 모두 만족해야 primary 1,260회를 실행한다.

- structured-state parse success ≥ 95%
- API/run error < 5%
- safe와 unsafe gold state가 각각 30–70%
- 모든 fault family가 최소 development case 하나에서 validator fail을 재현
- CATS development median token reduction ≥ 15%
- CATS development mean `ΔQ`의 95% CI 하한 > -0.03
- 예상 전체 비용과 wall-clock이 2026-09-02 이전 완료 가능

### Paper success gate

권장 primary claim은 다음을 만족할 때만 쓴다.

- median token reduction ≥ 20%
- mean `ΔQ` 95% CI 하한 > -0.02
- recommended CATS의 frozen architecture test 관측 unsafe stop 0건
- 최소 3개 topology category에서 같은 방향의 절감
- held-out model에서 quality margin 위반 없음

하나라도 실패하면 수치를 숨기거나 threshold를 사후 변경하지 않는다. 방법 주장을 “risk-controlled savings”에서 calibration/diagnostic finding으로 낮추고, 실패 이유를 분석한다.

## 11. 필요한 ablation

- topology feature 제거
- semantic change feature 제거
- cost feature 제거
- trajectory calibration → state calibration
- hard guard 제거
- patience 2 → patience 1
- legacy lexical-ΔU 대비
- domain-specific architecture feature 제거
- ε와 α sensitivity
- actual native vs injected challenged cases 분리

## 12. ICLR 본문 구조

9페이지 본문 기준으로 다음 분량을 고정한다.

1. Introduction: 1.0 page
2. Related work: 0.75 page
3. Existing empirical benchmark and problem setup: 1.25 pages
4. CATS method: 1.5 pages
5. General-domain results: 1.25 pages
6. Architecture benchmark/results: 1.5 pages
7. Ablation/calibration/OOD: 1.0 page
8. Limitations/conclusion: 0.75 page

39개 finding, 세부 topology 표, 모든 prompt, extra models, full fault tables는 appendix로 이동한다.

### 핵심 figure 네 개

1. topology → trajectory → CATS → hard guard pipeline
2. quality–token Pareto frontier
3. topology별 natural stop과 CATS stop 비교
4. architecture native/challenged case의 unsafe-stop 및 coverage

## 13. 선례가 주는 기준

ICLR 본회의의 accepted work는 human evaluation 없이도 객관적 validator가 강하면 채택됐다.

- MAC-AMP: multi-agent closed-loop, multi-objective predictors와 module ablation
- cadrille: executable CAD, Chamfer/IoU/invalidity
- SymPoint: 건축 CAD floorplan, panoptic/instance metrics
- Compositional Generative Inverse Design: physics objectives, OOD, CI

반대로 adaptive compute/agent 논문은 단순 savings 숫자만이 아니라 learned decision, 강한 baseline, OOD, calibration 또는 광범위한 benchmark를 보였다. 그러므로 이 계획은 건축 미학 대신 독립 validator를 사용하고, legacy heuristic 위에 trajectory-calibrated stopping을 추가한다.

## 14. 객관적 채택 판단

- **현재 초안:** no-go. 내부 불일치와 방법 novelty 부족 때문에 건축 결과를 붙여도 위험하다.
- **건축 Exp08만 추가:** 여전히 weak. domain case study로 읽힐 가능성이 크다.
- **본 설계가 성공 기준 통과:** ICLR에 제출할 만한 경쟁력 있는 상태. 다만 accepted를 보장할 수는 없다.

ICLR 2026 전체 acceptance rate 27.4%는 base rate일 뿐 이 논문의 확률이 아니다. 이 계획의 목적은 숫자 예측이 아니라 reviewer가 거절할 명확한 이유인 “heuristic only”, “domain leakage”, “no hard validation”, “unfair comparison”, “underpowered statistics”를 선제적으로 제거하는 것이다.

## 15. 마감 위험

전체 완성 위험은 **중간–높음**이다.

| 영역 | 위험 | 이유 |
|---|---|---|
| ARR validator/loop | 중간 이하 | 핵심 구현이 이미 존재 |
| AG adapter와 CATS | 중간 | 작은 범위지만 새 parser/calibration 필요 |
| 누수 없는 7-PNU data split | 중간–높음 | 추가 PNU와 fault validation 필요 |
| 1,770 runs | 높음 | 비용, rate limit, retry, 결과 완결성 |
| 통계와 9-page rewrite | 높음 | 현재 39 findings를 3 claims로 압축해야 함 |

마감 위험이 “좋다”는 뜻은 아니다. 기술적으로 가능하지만, pilot gate와 날짜별 freeze를 지키지 않으면 논문 작성 시간이 사라지는 구조다.

## 16. 고정 일정

- 2026-08-18: 설계·계획 freeze
- 2026-08-19~21: 논문 감사 수정, PNU registry, case builder, tests
- 2026-08-22~23: 180-run pilot
- 2026-08-24: pilot gate와 비용 결정
- 2026-08-25~27: CATS training/calibration, offline replay, online parity
- 2026-08-28: method/threshold/data split freeze
- 2026-08-29~09-02: 1,260 primary runs
- 2026-09-03~06: cross-model 300 + deterministic ARR baseline 30 + ablation
- 2026-09-07~12: 분석, figure/table, 본문 전면 재작성
- 2026-09-13~17: 내부 review, 재현 패키지, 익명화
- 2026-09-18 AoE: abstract deadline
- 2026-09-19~24: final polish
- 2026-09-25 AoE: paper deadline

공식 일정:

- https://iclr.cc/Conferences/2027/CallForPapers
- https://iclr.cc/Conferences/2027/AuthorGuidelines
- https://iclr.cc/Conferences/2027/ReviewerGuidelines

## 17. 최종 범위 보호 규칙

마감 전에는 다음 기능을 추가하지 않는다.

- multi-action RL
- 새로운 설계 생성 engine
- UI/dashboard
- 주관적 미학 metric
- 세 번째 API model
- 7개를 넘는 PNU 확장
- primary table에 필요하지 않은 새 topology

이 문서와 충돌하는 아이디어는 ICLR 제출 이후 backlog로 보낸다.
