# AG-Research 4-Page Captions (Page 5–8)

**Project**: AG-Research — *When Should Multi-Agent LLM Teams Stop?*
**Venue**: COLM 2026 (Conference on Language Modeling)
**Author**: DongHyeon KIM
**Date**: 2026-05-02
**Tone**: 격식체 + 설명형 (Problem → Decision → Impact 구조), 학술 통계는 본문 inline 인용

---

## PAGE 5 — Hero · Problem Definition · Taxonomy

### 메인 헤드라인 (이미 시안에 존재)
**When should multi-agent LLM teams stop?**
*First systematic study of termination dynamics across 14 coordination topologies.*
2,200+ unified runs · 7 experiments · 5 LLMs

### 본문 단락
멀티 에이전트 시스템이 점차 정교해지는 한편, *언제 멈출 것인가*는 여전히 명확히 정의되지 않은 문제로 남아 있다. 4라운드 토론을 4라운드로 끝내는 것이 옳은지, 4라운드 채팅 파이프라인을 그대로 두어야 하는지에 대한 선행 연구는 토폴로지를 1~5개 수준으로만 다루었고, 그 결과 종료 시점 판단은 대부분 *직관*에 의존해 왔다.

본 연구는 이 공백을 정량적으로 채우기 위해 14개 coordination topology를 6개 카테고리(S/A/B1/B2/C/D)로 분류하고, 25개 task · 9개 도메인 · 4개 task type · 3회 반복으로 총 2,200건 이상의 통제 실험을 수행했다. 5개 LLM(Grok 3 Mini, GPT-4o-mini, Haiku 4.6, Gemini 2.0 Flash, GPT-5.4, Opus 4.6)에서 결과를 교차 검증했으며, Spearman ρ=0.900(p=0.037)으로 강한 일반화를 확인했다.

### KPI 박스 (4개)
- **14** TOPOLOGIES
- **2,200+** UNIFIED RUNS
- **7** EXPERIMENTS
- **5** LLMs

### Termination Regret 캡션 — `Three Failure Modes`
멀티 에이전트 LLM 시스템(AutoGen, LangGraph, CrewAI 등)은 공통적으로 `max_turns=10` 같은 정적 종료 한계에 의존한다. 그러나 2-agent 토론과 4-agent 디베이트는 본질적으로 다른 수렴 패턴을 가지며, 동일한 종료 규칙이 세 가지 실패 모드를 만든다. 본 연구는 이를 **termination regret**으로 명명하고, 토폴로지별로 정량화한다.

- **Over-termination** — 토론이 4라운드 동안 합의에 수렴하지 않은 채, 동일 의견을 반복하며 토큰만 소진한다.
- **Under-termination** — 순차 파이프라인이 초기 단계에서 정체되어, 후속 단계가 원래 의도한 정제(refinement)에 도달하지 못한다.
- **Topology mismatch** — Selector 기반 팀이 인간이 직접 만든 종료 기준에 의존해, 단일 에이전트가 중간에 부적절한 종결을 유도한다.

### Research Gap 표 캡션 — `Coverage of Prior Work`
선행 연구의 토폴로지 커버리지를 정리하면 다음과 같다. REFRAIN(2024)은 1개 토폴로지(single-agent CoT), Hu et al. NeurIPS 2025는 1개(debate-only), Aegean은 parallel dynamics만, MAST(Cemri 2025)는 ~5개 mixed 토폴로지를 다룬다. 본 연구는 이를 통일된 실험 프로토콜 위에서 14개 · 6개 카테고리로 확장하여, 토폴로지에 따른 종료 동역학을 비교 가능한 형태로 제시한다.

### 14 Topologies · 6 Categories 캡션 — `Taxonomy Grounded in Prior Theory`
Masterman et al.(2025)의 Chain/Star/Mesh 분류와 Tran et al.(2025)의 centralized/distributed 분리를 결합하여 6개 카테고리(S, A, B1, B2, C, D)로 통합 재구성했다. 본 분류는 B1/B2 분할을 도입한 첫 시도로, centralized selector(B1)와 decentralized swarm(B2)이 동일한 다중 에이전트 구조에 속함에도 불구하고 비용 곡선이 sub-linear와 super-linear로 분화됨을 보인다.

---

## PAGE 6 — Methodology · Experiment 1 (Pattern Efficiency)

### 메인 헤드라인
**METHODOLOGY**
*카테고리 환원 → 실험 설계 → 첫 측정. 토폴로지를 통제하는 세 층위.*

### 본문 단락
페이지는 세 영역으로 구성되어 있다. 좌상은 *어떤 구조를 비교하는가* — 14개 토폴로지를 6개 카테고리로 묶고, 다시 5개의 정형화된 메시지 흐름으로 환원한 결과다. 좌하는 *그 구조 위에서 어떤 실험을 설계했는가* — 5개의 상호 연결된 실험(E01–E05)이 데이터를 주고받으며 누적된 증거를 만드는 구조다. 우측은 *그 실험의 첫 결과* — 14개 토폴로지의 Execution Duration, Token Consumption, LLM Call Count, Per-Call Output Efficiency를 비교한 박스 플롯이다.

이 세 층위를 분리한 이유는 단순하다. 토폴로지를 공정하게 비교하려면 *메시지 전달 구조 자체*가 통제되어야 하고, 그 통제 위에서 실험이 *재현 가능한 인과 관계*로 연결되어야 하며, 최종적으로는 *동일한 평가자(G-Eval)와 task suite*에서 측정되어야 한다. 세 층위 중 어느 하나만 무너져도, 토폴로지 비교의 결론은 단일 모델·단일 task의 우연으로 환원된다.

### 좌상 캡션 — `Message Flow Architectures · Termination Regret`
**Figure 2** — 14개 토폴로지가 6개 카테고리(A/B1/B2/C/D)로 묶이고, 다시 5개의 정형화된 메시지 흐름으로 환원됨을 보인다. A(Flat Sequential)는 task → A1 → A2 → A3 → A4 → result의 round-robin 구조, B1(Centralized Routing Star)은 LLM Selector가 호스트가 되어 다음 발화자를 결정하는 star 구조, B2(Decentralized Handoff Mesh)는 에이전트들이 handoff tool을 호출해 자율 라우팅하는 mesh 구조다. C(Structured Feedback)는 Reflection(Gen ↔ Critic)과 Debate(D1 ↔ D2 ↔ D3) 두 변종을 포함하며, D(Composed/Nested)는 Pipeline(Stage 1 → 2 → 3)과 MoA(Mixture-of-Agents, P1 + P2 + P3 → Agg) 두 변종을 갖는다.

다이어그램 아래에 **termination regret**의 개념을 두었다. AutoGen·LangGraph·CrewAI 같은 멀티 에이전트 LLM 시스템은 모든 토폴로지에 동일한 `max_turns=10` 같은 정적 한계를 적용하지만, 2-agent chain과 4-agent debate는 본질적으로 다른 수렴 패턴을 가진다. 이 균질한 종료 규칙이 만드는 세 가지 실패 모드를 하단 박스(Over-termination / Under-termination / Topology mismatch)에 명시했다. 이는 본 연구가 정량화하려는 핵심 현상이다.

### 좌하 캡션 — `Experimental Design · Five Interconnected Experiments`
**Figure 3** — Total Experiment Budget 500 LLM calls(v2 기준)을 5개 실험에 분배한 의존 관계 그래프다. 입력은 25 Tasks × 9 Domains(science / CS / history / philosophy / law / gaming / eng / biz / med)와 8 Representative Patterns(A(1) + B1(2) + B2(2) + C(2) + D(1) topologies)이다. 출발점은 **E01 Pattern Efficiency**(200 runs, duration·tokens·turns per pattern)이며, 여기서 산출된 데이터가 세 갈래로 분기한다.

- **E02 Termination Quality** (100 runs) — per-turn G-Eval scoring으로 quality curve와 regret을 측정한다.
- **E03 Convergence Detection** (analysis runs) — KS-test로 claim stability를 평가한다.
- **E04 Error Attribution** (analysis runs) — 8 error types per pattern을 분류한다.

세 실험의 결과(quality scores, convergence, error patterns)는 모두 **E05 Adaptive Termination**(200 runs)으로 수렴하여, ΔU(t) = ΔQ(t) − λ·ΔC(t) 의사결정 규칙을 도출한다. 코드 레벨 실험은 exp01–07까지 7개로 확장되어 있으나, 본 figure는 그중 메소드 골격을 이루는 5개 의존 관계만 시각화한다.

### 우 전체 캡션 — `Experiment 01 · Pattern Efficiency Across Topologies`
14개 토폴로지를 8개 대표 패턴(rr3 / sel3 / sel4 / swm3 / swm4 / refl2 / debate3 / pipe)으로 환원하여 4개 지표 — (a) Execution Duration, (b) Token Consumption, (c) LLM Call Count, (d) Per-Call Output Efficiency — 를 비교한 박스 플롯이다. 카테고리별 색상은 좌상의 Figure 2와 동일하게 매핑되어 있다.

가장 반직관적인 결과는 (b)에서 드러난다. Round-Robin-2(2-agent chain)의 토큰 평균이 약 4,759인 반면, Swarm-3(3-agent mesh)는 3,203으로 *에이전트 수가 더 많은 쪽이 더 저렴*하다(U=95, p<0.001). 이는 "에이전트가 늘면 비용이 증가한다"는 일반 직관과 정면으로 충돌한다. (c)에서는 Swarm-4가 LLM Call 평균 ~25회로 단연 높은데, mesh handoff가 누적될수록 짧은 호출이 폭증하기 때문이다.

이 데이터로부터 새로운 비용 위계 **A ≈ B2 < B1 ≈ C ≪ D** 를 도출했다. B1(Selector)은 에이전트 수에 sub-linear(1.48×)하게 비용을 키우는 반면, B2(Swarm)는 super-linear(3.17×)하게 폭증한다. 동일한 "다중 에이전트" 카테고리에 속함에도, 라우팅 구조가 centralized인지 decentralized인지에 따라 비용 곡선이 분화된다는 것이 본 실험의 핵심 발견이다.

---

## PAGE 7 — Quality Dynamics · Optimal Stop Points

### 메인 헤드라인
**QUALITY DYNAMICS**
*턴마다 품질이 어떻게 변하는가, 그리고 어디에서 멈춰야 하는가.*

### 본문 단락
종료 시점의 정답은 토폴로지마다 다르다. Round-Robin은 평탄화(plateau)되고, Reflection은 2턴에서 정점을 찍은 뒤 유지되며, Debate는 단조 감소(monotonic decline)한다. 이를 정량화하기 위해 100개 task에서 276개 turn-level G-Eval 점수를 수집하고, 패턴별 *quality trajectory*를 도출했다.

본 페이지는 두 종류의 시각화로 구성된다. 상단의 Pattern × Task Category Interaction 히트맵은 패턴이 task 도메인(상식·창의·게임·역사·법률·의학·물리·사이언스 등 9개)에 따라 어떻게 비용 곡선을 바꾸는지 보여준다. 하단의 Quality Trajectory 라인 차트는 5개 대표 패턴(rr3, sel3, swm3, refl2, debate3)에서 turn별 G-Eval 점수와 *optimal stop point*(별표)를 표시한다. Reflection-2의 경우 t=2에서 정점에 도달하며, 이후 추가 턴은 평균 품질을 유지할 뿐 비용만 증가시킨다.

### Pattern × Task Heatmap 캡션 — `Domain Sensitivity`
좌측 Mean Duration 히트맵에서 사이언스(sci) 컬럼은 모든 패턴에서 가장 짙은 빨강을 보이며, 우측 Mean Total Tokens 히트맵에서는 pipe와 debate3가 사이언스·물리 도메인에서 25,000 토큰을 초과한다. 동일 패턴이 동일 비용으로 일정하게 작동하지 않으며, task의 기술적 복잡도가 토폴로지 선택보다 더 큰 분산을 설명한다는 점(η²: difficulty 0.363 vs pattern 0.039, 9.3×)이 본 데이터의 직접적 근거다.

### Quality Trajectory 차트 캡션 — `Three Trajectory Shapes`
하단의 5개 라인 차트는 turn별 G-Eval 점수의 변화를 보여주며, 모든 패턴의 곡선은 결국 세 가지 형태 중 하나로 수렴한다 — 단조 증가 후 평탄화, 정점 후 평탄, 그리고 단조 감소다. **rr3**는 첫 번째 형태에 해당한다. t=3에서 정점에 도달한 뒤 점수가 더 이상 유의미하게 오르지 않으며, 이후 턴은 redundant elaboration에 가까워 추가 비용이 품질로 환원되지 않는다. **sel3**는 t=4에서 최종 정점에 도달하지만 t=2~3 구간에서 약 0.50의 일시적 품질 하락이 관찰되는데, 이는 Selector 라우팅이 저품질 에이전트를 중간에 호출할 때 발생하는 비단조성으로, 토폴로지의 구조적 위험을 그대로 노출한다.

핸드오프 계열인 **swm3**와 토론 계열인 **debate3**는 모두 t=1에서 정점을 찍고 이후 단조 감소하는, 가장 직관에 반하는 형태를 보인다. Swarm은 핸드오프가 누적될수록 각 에이전트가 받는 컨텍스트가 희석되며, Debate는 같은 논점을 반복 검토하면서 평균 품질이 오히려 떨어진다. 특히 Debate의 quality monotonic decline은 Du et al. ICML 2024가 *추가 토론이 품질을 향상시킨다*고 보고한 결과를 본 task suite에서 반증하는 결과로, 토론 횟수를 무조건 늘리는 종래 관행에 대한 정량적 반례를 제시한다. 반면 **refl2**는 두 번째 형태인 정점 후 평탄을 따른다. t=2에서 가장 높은 점수를 기록한 뒤 추가 턴에서도 큰 손실 없이 유지되며, 다섯 패턴 중 termination regret이 +0.0으로 가장 작아 본 연구의 권장 baseline 위치를 차지한다.

### 핵심 수치 박스
- Pattern within difficulty: **all p<0.05**
- Effect size: η² difficulty=0.363 / pattern=0.039 → **9.3× larger**
- Refl-2 vs Solo (medium): Cohen's **d=1.26, p=0.003**

---

## PAGE 8 — Cross-Model Validation

### 메인 헤드라인
**CROSS-MODEL VALIDATION**
*결과는 모델에 종속되는가? 6개 LLM에서 같은 패턴이 재현되는가.*

### 본문 단락
단일 모델의 실험 결과는 종종 모델 고유의 편향을 반영한다. 본 연구는 Grok 3 Mini, GPT-4o-mini, Haiku 4.6, Gemini 2.0 Flash, GPT-5.4, Opus 4.6 — 총 6개 LLM에서 동일 task suite와 동일 토폴로지를 재실험하여, 결과의 일반화 가능성을 검증했다. 패턴 간 순위는 모델에 무관하게 유지되었으며(Spearman ρ=0.900, p=0.037), 모델별 절대 점수는 다르지만 *상대 순서*는 안정적이다.

본 페이지의 네 시각화는 그중 가장 직관에 반하는 발견을 정리한 것이다. (a) Solo Advantage 히트맵은 6개 모델 × 3개 난이도에서 solo가 multi-agent를 이긴 빈도를 보여주며, easy 난이도에서 6/6 모델 전부가 solo를 우위로 평가했다. (b) Multi-Agent Advantage by Difficulty와 (c) Feedback Advantage(Refl-2 vs Solo) 라인 차트는 multi-agent 우위가 medium 난이도에 집중됨을 시사하는 *inverted-U* 패턴을 시각화한다. (d) Solo Dominance Frequency 막대 차트는 이 발견을 한 줄로 요약한다 — easy에서는 6/6, medium에서는 2/6, hard에서는 3/6 모델이 solo를 최적해로 선택한다.

### (a) Solo Advantage Heatmap 캡션 — `Easy Tasks Favor Solo`
세로축은 6개 LLM, 가로축은 3개 난이도(easy/medium/hard)다. 셀 값은 *Solo가 최적 multi-agent 패턴을 능가한 정도*를 의미하며, 양수일수록 solo 우위다. Easy 컬럼은 6개 모델 모두 양수이며, hard 컬럼에서는 3개 모델만 양수다. 이는 H3 가설(*hard task일수록 multi-agent가 우위*)을 부분적으로 반증한다.

### (b) Multi-Agent Advantage by Difficulty 캡션 — `The Inverted-U`
모든 모델의 곡선이 medium 난이도에서 정점을 보이는 inverted-U 형태를 따른다. Easy task에서는 multi-agent overhead가 품질 이득을 상쇄하며, hard task에서는 모델 자체의 성능 한계가 협업 이득을 무력화한다. Medium 난이도에서만 multi-agent의 reasoning amplification이 비용을 정당화한다.

### (c) Feedback Advantage (Refl-2 vs Solo) 캡션 — `Reflection's Sweet Spot`
Reflection-2는 medium 난이도에서 가장 큰 품질 우위(Δ=+1.0, GPT-5.4)를 보이며, easy와 hard에서는 solo와 동등하거나 열위다. Reflection의 효과는 *충분히 어렵지만 모델이 풀 수 있는 범위*에 한정된다.

### (d) Solo Dominance Frequency 캡션 — `One-Line Summary`
6개 모델 중 solo가 최적해로 선택된 빈도를 난이도별로 집계한 결과다. Easy 6/6, Medium 2/6, Hard 3/6 — 이 한 그래프가 본 연구의 가장 반직관적인 결론을 압축한다. *대부분의 task에서 solo가 비용 효율의 절대 우위를 가지며, multi-agent는 특정 조건에서만 정당화된다.*

---

## Footer (4페이지 공통)
**AG-Research · DongHyeon KIM · 2026**
- COLM 2026 Paper: *When Should Multi-Agent LLM Teams Stop? Topology-Aware Termination Dynamics*
- Submission: openreview.net/group?id=colmweb.org/COLM/2026/Conference
- Code & Data: framework open-sourced (13 pattern implementations + 7 experiment runners)

---

## 참고: 4-Page Storyline

| 페이지 | 역할 | 핵심 메시지 |
|--------|------|-------------|
| **P5** Hero · Taxonomy | "왜 이 문제가 중요한가" | Termination regret 정의 + 14 토폴로지 분류 |
| **P6** Methodology · Exp1 | "어떻게 측정했는가" | 5개 메시지 흐름 + 7개 상호 연결 실험 + Pattern Efficiency |
| **P7** Quality Dynamics | "어디에서 멈춰야 하는가" | Quality trajectory 3가지 형태 + Optimal stop point |
| **P8** Cross-Model | "결과가 일반화되는가" | 6 LLM Spearman ρ=0.900 + Inverted-U + Solo dominance |

각 페이지는 독립적으로도 읽힐 수 있도록 본문 단락을 자기 완결적으로 작성했으며, 4장을 연속으로 읽을 경우 *Problem → Method → Result → Generalization*의 학술 논문 표준 구조와 동일한 흐름을 갖는다.

---

## 톤 가이드라인 (PORTFOLIO_4PAGE_CAPTIONS.md와 동일)

| 원칙 | 적용 방식 |
|------|-----------|
| Problem → Decision → Impact | 각 캡션을 "선행 한계 → 설계 결정 → 정량 결과"의 3단 구조로 통일 |
| 격식체 + 설명형 | "~다.", "~했다." 종결. 구어체 배제 |
| 다이어그램 비중복 | 다이어그램이 보여주는 노드/축은 캡션에서 반복하지 않음. 의사결정 이유와 정량 결과 중심 |
| 통계 수치 inline | U-test, p-value, η², Cohen's d, Spearman ρ, R² 등 학술 통계는 본문에 inline으로 포함 |
| 전문 용어 | 토폴로지 분류명(S/A/B1/B2/C/D), 패턴명(rr3/sel3/swm3/refl2/debate3) 그대로 사용 |
