# 멀티 에이전트 팀은 언제 멈춰야 하는가?
## NotebookLM 오디오 개요 소스 문서

> 논문 제목: "When Should Multi-Agent Teams Stop? A Systematic Study of Termination Dynamics Across 14 Coordination Topologies"
> 연구자: AutoGen + Claude Haiku 4.5 기반 실험, 2026년 2월
> 총 실험 실행: 2,000회 이상

---

## 1. 연구의 핵심 질문: 왜 이 문제가 중요한가?

AI 에이전트 여러 개가 팀을 이루어 일하는 시스템이 급속도로 확산되고 있습니다. ChatGPT, Claude 같은 단일 AI가 아니라, 여러 전문 AI들이 서로 협력하는 멀티 에이전트 시스템 말입니다.

그런데 이 팀들에는 아무도 제대로 답하지 못한 근본적인 질문이 있습니다.

**"이 팀, 언제 멈춰야 하나요?"**

지금 현장에서 사용하는 방법은 세 가지입니다.
- 최대 10턴이 되면 강제로 끊는다
- "TERMINATE"라는 단어를 에이전트가 출력하면 멈춘다
- 외부에서 타이머를 설정해 강제 종료한다

이 방법들의 문제는 뭘까요? **에이전트들이 어떻게 협력하는지와 무관하게 똑같이 적용한다는 것**입니다.

생각해 보세요. 2명이 사실 확인을 하는 팀과 4명이 토론을 벌이는 팀이 있다면, 둘 다 "10턴 되면 끝"으로 관리하는 건 말이 안 됩니다.

이 불일치에서 발생하는 것을 연구팀은 **종료 후회(termination regret)**라고 부릅니다. 실제로 멈춘 시점과 멈췄어야 했던 최적 시점 사이의 낭비나 손실입니다.

세 가지 시나리오를 생각해 봅시다.

**과잉 종료**: 토론 팀이 이미 합의에 도달했음에도 4라운드를 더 교환합니다. 품질 개선은 없는데 비용만 낭비됩니다.

**과소 종료**: 순차 파이프라인이 초안 단계에서 멈춰버립니다. 사실 오류를 잡아냈을 검토 단계에 아예 도달하지 못합니다.

**토폴로지 불일치**: 선택자 기반 라우팅 팀에 고정 턴 한도를 적용하면, 라우팅 에이전트가 적절한 전문가를 선택하기 전에 강제 종료됩니다.

---

## 2. 연구의 독창성: 무엇이 처음인가?

이 연구 이전에 비슷한 연구들이 있었습니다.
- Hu et al. (NeurIPS 2025): 토론 패턴 하나만 다뤘습니다
- REFRAIN (2025): 단일 에이전트 전용이었습니다
- Aegean (2025): 병렬 합의 전용이었습니다

**이 연구의 핵심 차별점**: 14가지 협력 방식을 동일한 프레임워크, 동일한 AI 모델, 동일한 25개 과제로 동시에 비교한 **최초의 연구**입니다.

AutoGen 프레임워크를 사용하여 총 2,000회 이상의 실험을 통해 "어떤 협력 방식이든 언제 멈춰야 하는가"에 대한 체계적인 답을 찾았습니다.

6대 기여:
1. 14패턴 × 6범주 × 1프레임워크: 최초 교차 토폴로지 비교
2. 단일 에이전트 기준선(Solo) 도입으로 멀티 에이전트 부가가치 정량화
3. G-Eval 턴별 품질 궤적으로 종료 후회 측정 방법 제안
4. 중앙 라우팅(B1)과 분산 핸드오프(B2)가 정반대로 확장됨을 처음 규명
5. 한계 효용 진단 공식 ΔU(t) = ΔQ(t) − λ·ΔC(t) 제안
6. GPT-4o-mini 교차 검증으로 일반화 가능성 확인 (Spearman ρ=0.900)

---

## 3. 14가지 협력 방식: 에이전트들이 어떻게 일하는가

### 왜 이렇게 6개 범주로 나눴는가? (분류 근거)

이 6개 범주는 임의로 정한 것이 아닙니다. **기존 멀티 에이전트 연구의 표준 분류법**에 기반하고, **실험 데이터가 분리를 정당화**합니다.

**근거 1: MAS 토폴로지 이론에 기반한 분류**

**Masterman et al. (2025, "The Landscape of Emerging AI Agent Architectures")** 는 멀티 에이전트 시스템의 **3대 정규 토폴로지**를 제시합니다:
- **Chain (체인)** — 고정 순서로 메시지 전달 → 본 연구의 **범주 A**
- **Star / Hub-and-Spoke (스타)** — 중앙 조정자가 라우팅 결정 → 본 연구의 **범주 B1**
- **Mesh / Swarm (메시)** — 중앙 없이 P2P 직접 통신 → 본 연구의 **범주 B2**

**Tran et al. (2025, "Multi-Agent Collaboration Mechanisms: A Survey of LLMs")** 의 5차원 협업 프레임워크에서도 *구조(Structure)* 차원에서 "중앙 집중형(centralized) vs. 분산형(distributed)"을 **명시적으로 분리**하여, B1/B2 구분의 학술적 정당성을 지지합니다.

본 연구는 Masterman et al.의 3대 토폴로지에 **2개 범주를 추가**합니다:
- **C(구조화 피드백)**: Reflexion (Shinn et al., NeurIPS 2024)의 생성-비평 루프, Du et al. (ICML 2024)의 토론 패턴. 양방향 순환 구조로 Chain/Star/Mesh 어디에도 속하지 않음.
- **D(복합/중첩)**: MoA (Li et al., ICLR 2025)의 병렬+집약, Pipeline의 순차 정제. 단일 팀이 아닌 다단계 구조.

정리하면:
- **A(고정 순차, Chain)**: 화자 순서가 사전에 고정됨. 결정적(deterministic) 경로.
- **B1(중앙 집중, Star)**: 중앙 조정자가 모든 라우팅 결정. Hub-and-Spoke 토폴로지.
- **B2(탈중앙, Mesh)**: 중앙 조정자 없이 자율 핸드오프. P2P 직접 전달.
- **C(구조화 피드백)**: 생성-비평 루프(반성) 또는 찬반-판정 구조(토론).
- **D(복합/중첩)**: 여러 팀이 순차(파이프라인) 또는 병렬(MoA)로 결합.

**근거 2: 실험 데이터가 B1/B2 분리를 강제함**

원래는 B1과 B2를 하나의 "B(동적 라우팅)"으로 묶었습니다. 그러나 실험 결과:
- 3→4 에이전트 확장 시 B1은 토큰 **1.28배(준선형)**, B2는 **3.37배(초선형)**로 정반대 스케일링
- 턴당 토큰: B1=2,270~2,538(긴 독백) vs B2=523~544(짧은 핸드오프) — 대화 패턴이 6배 차이
- 오류율: B1=0% vs B2=11~76%
- 이 데이터를 보고 B1/B2로 분리하기로 결정했습니다. **분류가 먼저가 아니라, 데이터가 분류를 강제한 것**입니다.

**에이전트 수(2/3/4명) 선택 근거**: 2명=최소 협업 단위, 3명=가장 일반적 팀 크기, 4명=스케일링 효과 측정. 같은 범주 내에서 n→n+1 확장 비교를 위한 체계적 그리드 설계입니다.

---

### 범주 S: 단일 에이전트 기준선 (Solo)

혼자 일하는 AI입니다. 비교 기준점으로 사용됩니다.
- 평균 토큰: 1,287개 / 걸리는 시간: 18.7초
- 100% 스스로 "다 했다"고 말하고 끝냄 (키워드 종료율 100%)

멀티 에이전트 시스템이 정말 가치 있으려면 이 기준을 뛰어넘어야 합니다.

---

### 범주 A: 고정 순차 체인 (RR-2, RR-3, RR-4)

에이전트들이 줄지어 순서대로 일하는 방식입니다. 첫 번째 에이전트가 답하면, 두 번째가 그걸 보고 답하고, 세 번째가 또 그걸 보고 답하는 식입니다. 각 에이전트는 이전 모든 대화를 전부 다 읽어야 합니다.

**RR-2**: 작성자 → 연구자, 2명이 교대 → 4,759 토큰, 52초, 오류율 8.3%
**RR-3**: 작성자 → 연구자 → 검토자 → 10,121 토큰, 97초, 오류율 23.3%
**RR-4**: 4명 순환 → 12,040 토큰, 119초, 오류율 71.7%

놀라운 사실: 에이전트를 하나씩 추가할 때마다 오류율이 기하급수적으로 뛰었습니다. 2명에서 4명으로 늘리면 오류율이 8.6배 증가합니다. 이유는 각 에이전트는 이전 모든 대화를 다 읽어야 하는데, 팀이 커질수록 이 "읽어야 할 분량"이 폭발적으로 늘어나기 때문입니다 (입력 토큰이 2.59배 초선형 증가).

또 흥미로운 현상도 있습니다. 팀이 커질수록 각 에이전트가 더 길고 풍부한 응답을 생성합니다 (LLM 호출당 출력 토큰: RR-2=930, RR-3=1,189, RR-4=1,544). 더 많은 선행 기여를 읽을수록 더 상세하게 답합니다. 이를 **협력적 증폭(collaborative amplification)**이라 부릅니다. 하지만 이 이점이 폭발적으로 늘어나는 입력 비용을 상쇄하지는 못합니다.

---

### 범주 B1: 중앙 집중형 라우팅 (Sel-3, Sel-4)

교통 경찰 같은 조정자(Selector) 에이전트가 중앙에 있고, "이번엔 네가 말해", "다음엔 저 전문가한테 넘겨" 식으로 모든 결정을 합니다.

**Sel-3**: 조정자 1 + 전문가 3 → 7,851 토큰, 115초, 오류율 0%
**Sel-4**: 조정자 1 + 전문가 4 → 11,595 토큰, 162초, 오류율 0%

에이전트 1명 추가했을 때 비용: 1.48배 증가 (준선형). 중앙 조정자가 있으니 아무도 길을 잃지 않습니다. 오류율 완벽하게 0%.

특징: 각 에이전트가 턴당 2,114~2,616 토큰의 긴 독백을 씁니다. 적은 턴, 많은 내용.

---

### 범주 B2: 탈중앙 핸드오프 (Swm-3, Swm-4)

중앙 조정자 없이 각 에이전트가 스스로 "이 다음은 내가 아니라 저 친구한테 넘겨야지"를 판단합니다. 마치 축구팀에서 패스를 스스로 결정하는 것처럼요.

**Swm-3**: 핸드오프 전문가 3명 → **4,196 토큰**, 75초 → **전체 멀티 에이전트 중 최고 효율!**
**Swm-4**: 핸드오프 전문가 4명 → 13,321 토큰, 185초 → 비용 3.17배 폭발!

이것이 이 연구의 가장 놀라운 발견 중 하나입니다. Swm-3는 3명 팀인데도 2명 팀(RR-2, 4,759 토큰)보다 **12% 더 저렴**합니다. 지능적인 핸드오프가 추가 인원의 오버헤드를 상쇄한 것입니다.

하지만 Swm-4는 악몽입니다. 4명째 에이전트를 추가하면 핸드오프 체인이 폭주합니다. 평균 턴 수가 10.2에서 25.0으로 뛰어버립니다.

특징: 각 에이전트가 턴당 330~337 토큰의 짧은 핸드오프 메시지만 씁니다. B1과 정반대.

---

### 범주 C: 구조화 피드백 (Refl-2, Refl-3, Deb-3, Deb-4)

에이전트들이 서로의 결과물을 비판하고 개선하는 방식입니다.

**Refl-2**: 생성자(초안) + 비평가(검토·개선) → 5,237 토큰, 60초, **품질 4.80/5.0**, 오류율 0%
**Refl-3**: 생성자 + 비평가 + 정제자 → 12,095 토큰, 120초
**Deb-3**: 토론자 3명 + 중재자 1명 → 9,313 토큰, 157초
**Deb-4**: 토론자 4명 + 중재자 1명 → 11,637 토큰, 181초

반성 패턴과 토론 패턴의 확장 방식이 정반대입니다.
- 반성(Refl): 에이전트 추가 시 비용 2.31배 증가 (초선형)
- 토론(Deb): 에이전트 추가 시 비용 1.25배만 증가 (준선형)

토론에서는 에이전트가 많아질수록 각자 말하는 양이 줄어드는 "턴 규율" 효과가 있습니다. 에이전트 턴당 출력이 Deb-3=1,691 토큰 → Deb-4=1,448 토큰으로 오히려 감소합니다.

---

### 범주 D: 복합/중첩 구조 (Pipe, MoA)

**Pipe (파이프라인)**: 2단계로 나뉜 팀. 1단계가 초안을 만들면, 2단계가 정제합니다. 총 5에이전트. → 13,856 토큰, 130초

**MoA (혼합 에이전트)**: 3명이 동시에 병렬로 각자 답을 만들고, 집약자 1명이 합칩니다. → **22,333 토큰**, 103초 → **전체 최고 비용! Solo의 17.35배**

MoA의 비용이 이렇게 높은 이유: 3명이 동시에 완전한 답을 각각 독립적으로 만들기 때문에 출력 토큰이 입력 토큰의 3.58배나 됩니다.

---

## 4. 5가지 실험의 핵심 발견

### 실험 01: 어느 방식이 가장 효율적인가? (780회 + 200회 실행)

> **데이터 소스 안내**
> - 본문 및 순위표: **Exp01-V1** (13 패턴 × 20 과제 × 3 반복 = 780회, 오류 실행 제외)
> - 차트 5: **Exp01-V2** (8 패턴 × 25 도메인 과제 = 200회, 새로운 9개 도메인 기반 과제셋)
> - 차트 6: **Exp02** (5 패턴 × 20 과제 = 100회, 품질 점수 포함)
> - V1과 V2는 과제셋이 다르므로 동일 패턴의 토큰 수치가 약간 다를 수 있음

**전체 비용 순위** (Solo에서 MoA까지, 17.4배 차이, Exp01-V1 기준):

| 순위 | 패턴 | 범주 | 총 토큰 | Solo 대비 |
|------|------|------|---------|---------|
| 0 | Solo | S | 1,287 | 1.00x |
| 1 | Swm-3 | B2 | 4,196 | 3.26x |
| 2 | RR-2 | A | 4,759 | 3.70x |
| 3 | Refl-2 | C | 5,237 | 4.07x |
| 4 | Sel-3 | B1 | 7,851 | 6.10x |
| 5 | Deb-3 | C | 9,313 | 7.23x |
| 6 | RR-3 | A | 10,121 | 7.86x |
| 7 | Sel-4 | B1 | 11,595 | 9.01x |
| 8 | Deb-4 | C | 11,637 | 9.04x |
| 9 | Refl-3 | C | 12,095 | 9.40x |
| 10 | Swm-4 | B2 | 13,321 | 10.35x |
| 11 | Pipe | D | 13,856 | 10.76x |
| 12 | MoA | D | 22,333 | 17.35x |

통계 검증(Kruskal-Wallis, N=718): 5개 모든 지표에서 p<0.001. 토폴로지 범주가 효율의 강력한 예측 변수임이 확인되었습니다.

**새로운 비용 위계 확립**: A ≈ B2 < B1 ≈ C ≪ D

이는 기존에 학계에서 가정하던 "A < B ≈ C < D"를 완전히 뒤집는 결과입니다. A와 B2가 통계적으로 구분 불가능(p=0.857)하고, B2가 C보다 유의하게 저렴합니다(p=0.028).

도메인별 분석에서 흥미로운 추가 발견:
- Debate-3만이 도메인이 바뀌어도 비용이 일정합니다 (변동계수 CV=0.14). 토론의 고정 라운드 구조 덕분입니다.
- Swm-3는 가장 도메인 민감합니다 (CV=0.67). 역사 과제에서는 1,400 토큰이지만 경영 과제에서는 9,200 토큰.

---

### 실험 02: 언제 끝내야 가장 좋은가? (100회 실행, 276개 턴별 품질 점수)

각 에이전트 턴마다 품질을 5점 척도로 측정했습니다. Claude Sonnet 4.5를 평가자로 사용해서 정확성, 완전성, 일관성, 유용성, 종합 5개 차원을 측정했습니다.

그리고 "언제 최고 품질에 달했는가"(t_optimal)와 "실제로 언제 끝났는가"(t_actual)를 비교했습니다.

**세 가지 품질 궤적 패턴이 발견되었습니다:**

**패턴 1 - 단조 증가 후 고원형 (RR-3)**

| 턴 | t1 | t2 | t3 | t4 | t5 | t6 |
|----|----|----|----|----|----|----|
| 품질 | 3.9 | 4.2 | 4.5 | 4.1 | 4.1 | 4.1 |

3턴에서 최고점 4.5에 도달, 그 이후 변화 없음.
후회: 2.6턴 (즉, 2.6턴을 쓸데없이 더 함)
하지만 품질 손실은 0.05로 미미 → "안전한 낭비"

**패턴 2 - 2턴 정점형 (Refl-2, 반성 패턴)**

| 턴 | t1 | t2 | t3 | t4 |
|----|----|----|----|-----|
| 품질 | 3.9 | 4.8 | 4.0 | 4.0 |

비평가의 첫 피드백 사이클이 품질을 3.9 → 4.8로 급상승시킵니다.
비평가가 "승인(APPROVED)"하는 순간이 자연적 종료 신호.
후회: 0.6턴, 품질 손실: 0.00 → **완벽한 패턴**

**패턴 3 - 단조 하락형 (Debate-3, 토론 패턴)**

| 턴 | t1 | t2 | t3 | t4 |
|----|----|----|----|-----|
| 품질 | 3.8 | 3.4 | 3.3 | 3.3 |

각 토론 라운드가 품질을 점진적으로 감소시킵니다!
품질 손실: 0.65 → **가장 위험한 패턴**

**종료 후회 비교**:

| 패턴 | 최고 품질 | 최종 품질 | 후회(턴) | 품질 손실 |
|------|---------|---------|---------|---------|
| Swm-3 | 4.15 | 4.05 | +0.2 | 0.10 |
| Refl-2 | 4.80 | 4.80 | +0.6 | 0.00 |
| Sel-3 | 3.90 | 3.40 | +1.6 | 0.50 |
| Debate-3 | 4.00 | 3.35 | +2.0 | 0.65 |
| RR-3 | 4.50 | 4.45 | +2.6 | 0.05 |

같은 "너무 오래 계속함" 문제라도, 토론 방식의 품질 손실이 RR 방식보다 13배 큽니다.

Refl-2는 최고 품질(4.80)과 제로 품질 손실(0.00)을 동시에 달성합니다. 비평가의 승인 신호가 내장된 종료 메커니즘으로 작동하기 때문입니다.

**평가 신뢰도에 대한 솔직한 고백**:
GPT-4o-mini로 40개 표본을 교차 검증한 결과, Pearson r = 0.43~0.62로 중간 수준의 상관을 보였습니다. Cohen's κ_w = 0.244~0.388로 "보통(fair)" 수준입니다. GPT는 체계적으로 Claude보다 높은 점수를 줍니다 (평균 차이 -0.93점). 이 때문에 비교는 절대값이 아닌 상대적 순위에 근거합니다.

---

### 실험 03: 에이전트들이 의미적으로 수렴하는가? (분석 실험)

Sentence-BERT(all-MiniLM-L6-v2, 384차원)를 사용하여 각 턴의 의미를 수치화하고, 연속 턴 간 코사인 유사도를 측정했습니다. 코사인 유사도가 임계값 0.85를 2번 연속 초과하면 "수렴"으로 판정합니다.

**수렴율 (θ=0.85)**:
- Pipe (파이프라인): **32%** → 가장 잘 수렴
- Sel-4 (B1): 28%
- Sel-3 (B1): 24%
- RR-3 (A): 16%
- Swm-4 (B2): 16%
- Swm-3 (B2): 8%
- Refl-2 (C): **0%** (!)
- Debate-3 (C): **0%** (!!)

놀라운 발견: 피드백 패턴(반성, 토론)은 의미적으로 **전혀 수렴하지 않습니다**.

Debate-3는 전체 패턴 중 평균 코사인 유사도가 가장 높은데(0.673), 그러면서도 수렴하지 않습니다. 이유는 각 턴마다 항상 새로운 논점이나 정제가 추가되기 때문입니다. 의미적으로 비슷한 주제를 다루지만 결코 안정화되지 않습니다.

중앙 라우팅(Sel)은 대화가 진행될수록 의미가 점점 비슷해지는 강한 양의 추세를 보입니다(Sel-3: +0.397). 반면 분산 핸드오프(Swm-3)는 오히려 흩어지는 음의 추세(-0.560).

**실무 의미**: 피드백 패턴에는 의미 수렴 기반 종료가 작동하지 않습니다. 품질 기반 신호가 필요합니다.

---

### 실험 04: 어떤 방식이 어떤 방식으로 실패하는가? (분석 실험)

세 가지 종료 실패 유형:

**유형 1 - 맥락 폭발 (범주 A)**: 에이전트가 늘수록 읽어야 할 이전 대화가 너무 많아져서 처리 불가. RR-2=8.3% → RR-3=23.3% → RR-4=71.7%

**유형 2 - 턴 폭발 (범주 B2)**: 핸드오프 체인이 끝없이 이어짐. Swm-4는 71.7%가 최대 턴 한도(25턴)에 걸려 강제 종료.

**유형 3 - 키워드 실종 (MoA)**: 집약자가 "TERMINATE"를 한 번도 출력하지 않아 100%가 강제 종료.

과제 유형별 차이도 극명합니다.
- 사실형 과제(역사 연도, 과학 사실): 어떤 팀 크기에서도 0% 오류
- 기술형 과제(코드 작성): RR-2=33% → RR-3=53% → RR-4=100% 오류

스웜 에이전트의 통신 방식은 다른 패턴과 구조적으로 다릅니다.
- 메시지 길이: 205~322자 vs 다른 패턴 1,787~1,982자 (6분의 1 수준)
- TERMINATE 포함률: 1~6% vs 다른 패턴 9~18%

결론: 키워드 기반 종료는 스웜 방식에 적합하지 않습니다.

---

### 실험 05: 한계 효용 공식 ΔU(t)가 종료 신호로 작동하는가? (800회 실행)

연구팀이 제안한 공식:

**ΔU(t) = ΔQ(t) − λ·ΔC(t)**

- ΔQ(t): 이번 턴에서 품질이 얼마나 개선되었는가?
- ΔC(t): 이번 턴의 비용(킬로토큰)은 얼마인가?
- λ: 품질 vs 비용의 균형 파라미터
- ΔU(t) ≤ 0 → 더 계속해봤자 손해 → 지금 멈춰라!

**발견 1: 모든 토폴로지에서 1.1~2.4턴 내에 수렴 (λ=0.1)**

| 패턴 | ΔU 수렴 시점 | 최적 종료 시점 | 실제 종료 시점 |
|------|-----------|------------|------------|
| Swm-3 | 1.1턴 | 1.0턴 | 1.2턴 |
| Refl-2 | 2.0턴 | 1.7턴 | 2.3턴 |
| Sel-3 | 2.0턴 | 1.1턴 | 2.8턴 |
| Debate-3 | 2.2턴 | 1.3턴 | 3.3턴 |
| RR-3 | 2.4턴 | 1.6턴 | 4.2턴 |

**발견 2: λ 값을 바꿔도 결과가 거의 안 변합니다 (λ 둔감성)**

λ를 0.0에서 0.5까지 바꿔도 수렴 시점이 1.9 → 1.8턴으로 0.1턴 차이밖에 없습니다. 이유는 "품질이 더 이상 안 오른다"는 품질 포화 자체가 가장 강력한 수렴 신호이기 때문입니다. λ 정밀 튜닝 없이도 ΔQ(t) ≈ 0 감지만으로 충분합니다.

**핵심 반전 - ΔU를 키워드 종료의 대체로 쓰면 오히려 역효과!**

800회 통제 실험 (ΔU를 키워드 대체로 사용):

| 패턴 | 기준선 턴 | 적응적 턴 | 턴 변화 | 기준선 토큰 | 적응적 토큰 | 토큰 변화 |
|------|---------|---------|---------|-----------|-----------|---------|
| Refl-2 | 3.3 | 6.4 | **+92%** | 5,509 | 19,693 | **+258%** |
| Sel-3 | 3.7 | 4.7 | +27% | 7,901 | 12,840 | +63% |
| Sel-4 | 4.3 | 5.4 | +26% | 11,136 | 16,315 | +47% |
| RR-3 | 4.6 | 5.5 | +19% | 11,546 | 15,278 | +32% |
| Debate-3 | 4.4 | 4.6 | +5% | 9,042 | 9,752 | +8% |
| Pipe | 5.8 | 5.8 | +1% | 10,853 | 12,092 | +11% |
| Swm-3 | 9.6 | 8.2 | -15% | 3,223 | 9,818 | +205% |
| Swm-4 | 25.6 | 9.1 | **-65%** | 15,327 | 4,656 | **-70%** |

7개 패턴에서 오히려 더 많은 자원 소비, 단 하나(Swm-4)에서만 극적 절감.

λ 값이 결과를 바꿉니다. λ=0에서는 평균 +10% 턴, +131% 토큰. λ=0.1 이상에서는 평균 -33% 턴, -13% 토큰.

**결론**: "TERMINATE" 키워드가 7/8 패턴에서 거의 최적으로 작동합니다. 이 자체가 가치 있는 발견입니다. ΔU는 키워드가 28%밖에 성공하지 않는 Swm-4의 보조 수단으로 써야 합니다.

---

## 5. 교차 모델 검증: 다른 AI에서도 같은 결과가 나오는가?

GPT-4o-mini로 5개 패턴을 25개 과제에서 125회 실행했습니다.

| 패턴 | Claude 토큰 | GPT 토큰 | 비율 |
|------|-----------|---------|------|
| Solo | 1,287 | 697 | 0.54x |
| Sel-3 | 7,851 | 3,598 | 0.46x |
| Swm-3 | 4,196 | 3,203 | 0.76x |
| Refl-2 | 5,237 | 5,105 | 0.97x |
| RR-3 | 10,121 | 14,325 | 1.42x |

절대적 수치는 차이가 있습니다. 하지만 **상대적 순서가 강하게 보존됩니다**: Spearman ρ = 0.900 (p = 0.037)

두 AI 모두 같은 결론: Solo < Swm-3 < {Sel-3, Refl-2} < RR-3

Swm-3가 Solo 3배보다 효율적이라는 핵심 발견은 두 모델에서 모두 유지됩니다.

주의사항: n=5 패턴에서 산출된 상관이므로 표본이 작습니다. 통계적으로 유의하지만 전체 13개 패턴으로 확장하면 결과가 달라질 수 있습니다.

---

## 6. 15개 핵심 발견 요약 (C1~C15)

**C1** | 멀티 에이전트 조정은 3.3~17.4배 토큰 오버헤드를 발생시킵니다. 비용은 준선형, 오류율은 초선형으로 증가합니다.

**C2** | 중앙 라우팅(B1)은 에이전트 추가 시 1.48배(준선형) 증가. 분산 핸드오프(B2)는 3.17배(초선형) 폭발. 정반대 스케일링.

**C3** | Swm-3(3명)이 RR-2(2명)보다 12% 저렴. 라우팅 방식이 에이전트 수를 이깁니다.

**C4** | 반성 패턴은 에이전트 추가 시 비용 2.31배 증가. 토론 패턴은 1.25배만 증가. 동일 에이전트 수에서 반성이 빠르고 토론이 저렴합니다.

**C5** | 복합 패턴(MoA, Pipe)이 가장 비싸지만 에이전트 턴당 출력 밀도는 가장 높습니다.

**C6** | 새로운 비용 위계: A ≈ B2 < B1 ≈ C ≪ D. 기존 가정(A < B ≈ C < D) 폐기.

**C7** | Debate-3만이 도메인 불변(CV=0.14). 과제 복잡도가 비용 차이를 토폴로지와 독립적으로 최대 2배 증폭.

**C8** | 세 가지 품질 궤적: RR-3=단조증가-고원, Refl-2=2턴 정점, Debate-3=단조 하락.

**C9** | 종료 후회가 패턴별로 13배 차이. Refl-2가 최고 품질(4.80)과 제로 품질 손실을 동시 달성.

**C10** | Sentence-BERT 의미 수렴: 피드백 패턴 수렴율 0%. 피드백에는 품질 기반 종료가 필요.

**C11** | 사실형 과제는 오류 면역, 기술형은 오류 취약. 스웜 통신은 구조적으로 독특(메시지 6분의 1 길이).

**C12** | ΔU 공식은 모든 토폴로지에서 1.1~2.4턴 내 수렴. λ 값에 둔감(품질 포화 지배).

**C13** | ΔU의 효과: 7/8 패턴에서 오버헤드. Swm-4에서만 -70% 토큰 절감.

**C14** | ΔU는 키워드 종료를 대체가 아닌 보완해야 합니다. 하이브리드 전략 제안, 단 실험 검증은 향후 과제.

**C15** | 토폴로지 의존 역학은 모델 불변(Spearman ρ=0.900, p=0.037). 키워드 신뢰도와 라우팅 효율은 모델에 따라 다름.

---

## 7. 솔직한 한계 인정

**통계적 약점**
- 교차 모델 검증의 Spearman ρ=0.900은 고작 n=5 데이터 포인트에서 나왔습니다. 더 많은 패턴·모델로 확장이 필요합니다.
- 평가자 간 일치도 κ_w=0.244~0.388은 "보통(fair)" 수준입니다. 절대 점수 비교에 주의가 필요합니다.

**미검증 제안**
- 하이브리드 종료 전략(키워드 + ΔU 보조)을 제안했지만, 실제로 구현해서 테스트하지는 않았습니다.

**범위 제한**
- 2~5명 팀만 연구했습니다. 10명 이상 팀에서는 다른 역학이 나타날 수 있습니다.
- 코드 실행 피드백이 있는 과제, 멀티모달 과제는 포함하지 않았습니다.

**평가자 신뢰도**
- 인간 평가가 단 1명의 전문가에 의존합니다. 2명 이상으로 검증해야 진정한 평가자 간 신뢰도를 주장할 수 있습니다.

---

## 8. 실무 가이드라인: 어떤 팀에 어떤 종료 전략?

**비용 최소화**: Swm-3 (3명 팀, 가장 저렴) 또는 Refl-2 (내장 종료 신호 보유)

**최고 품질**: Refl-2 (4.80/5.0, 제로 품질 손실)

**예측 가능한 비용**: Debate-3 (도메인 불변, CV=0.14)

**대규모 팀**: B1(Sel-4)이 B2(Swm-4)보다 안전. Swm-4는 비용 3배 폭발 위험.

**스웜 방식 사용 시**: 3명(Swm-3)으로 고정. Swm-4에는 ΔU(λ≥0.1) 보조 종료 신호 추가.

**순차 체인 사용 시**: 에이전트 수 n에 대해 max_messages = 2n을 기준선으로. 3명 이상은 기술형 과제에서 오류 급증 주의.

---

## 9. 결론

멀티 에이전트 LLM 시스템에서 **종료는 일급 설계 결정**입니다.

이 연구는 세 가지를 2,000회 이상의 실험으로 실증했습니다.

**첫째**: 토폴로지가 종료를 결정합니다. 에이전트 수가 아니라 어떻게 연결되는지가 언제 멈춰야 하는지를 근본적으로 결정합니다.

**둘째**: 기존 키워드 종료는 대부분의 경우 놀랍도록 잘 작동합니다. 7/8 패턴에서 "TERMINATE" 방식이 거의 최적이었습니다. 이 자체가 중요한 발견입니다.

**셋째**: 예외가 있습니다. 분산 핸드오프(스웜, 특히 4명)는 키워드가 잘 작동하지 않습니다. 이 경우 ΔU 공식이 70%의 비용 절감을 달성합니다.

종료 전략이 조정 토폴로지에 의해 정보를 받는 **일급 설계 결정**이어야 함을 강조합니다. 어떤 토폴로지를 선택할 것인가 못지않게, 선택한 토폴로지 내에서 팀이 언제 멈춰야 하는가도 함께 설계해야 합니다.

---

*데이터 요약: 총 2,000+ 실행. 실험01: 780회(v1) + 200회(v2), Solo: 25회, 실험02: 100회(276턴 품질 점수), 실험05: 800회, 교차모델: 125회. 기본 모델: Claude Haiku 4.5. 교차 검증: GPT-4o-mini. 품질 평가: Claude Sonnet 4.5 (G-Eval). 25개 과제 × 9개 도메인(과학, CS, 역사, 철학, 법/정치, 게임, 공학, 경영, 의학).*

---

## [차트 데이터] 교수님 요청 4가지 검증 결과

> 아래 데이터 테이블은 차트/그래프 생성용입니다. PPT 슬라이드에 시각화해주세요.

---

### 차트 1: ΔU(t) → 0 수렴 (교수님 요청 #1)

한계 효용 ΔU(t) = ΔQ(t) - λ·ΔC(t)가 0으로 수렴하는 턴 수 (t_mu_zero).
모든 패턴에서 1.1~2.4턴 이내에 수렴 확인됨. λ 값에 둔감.

**차트 유형: 막대 그래프 (패턴별 수렴 턴) + 선 그래프 (λ별 변화)**

| 패턴 | λ=0.0 | λ=0.05 | λ=0.1 | λ=0.2 | λ=0.5 | 평균 regret | 품질 손실 |
|------|-------|--------|-------|-------|-------|-----------|---------|
| swm3 (B2) | 1.15 | 1.15 | 1.15 | 1.15 | 1.15 | 0.25 | 0.10 |
| refl2 (C) | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | 0.60 | 0.00 |
| sel3 (B1) | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | 1.65 | 0.50 |
| debate3 (C) | 2.20 | 2.20 | 2.20 | 2.20 | 2.00 | 2.00 | 0.65 |
| rr3 (A) | 2.40 | 2.40 | 2.40 | 2.35 | 2.00 | 2.55 | 0.05 |

**핵심**: swm3가 가장 빠르게 수렴(1.1턴), rr3가 가장 느림(2.4턴). λ 값을 바꿔도 수렴 턴은 거의 안 변함 → 품질 포화가 ΔU 수렴을 지배.

---

### 차트 2: 도메인(주제)별 패턴 효율 (교수님 요청 #2)

9개 도메인 × 8개 패턴의 평균 토큰 소비.

**차트 유형: 히트맵 또는 그룹 막대 그래프 (도메인 × 패턴)**

| 도메인 | debate3 | pipe | refl2 | rr3 | sel3 | sel4 | swm3 | swm4 |
|--------|---------|------|-------|-----|------|------|------|------|
| CS | 8,667 | 13,544 | 4,862 | 13,392 | 8,539 | 11,604 | 5,270 | 7,896 |
| 경영 | 8,907 | 15,723 | 3,550 | 15,520 | 4,362 | 13,894 | 9,163 | 14,806 |
| 공학 | 9,805 | 12,214 | 5,004 | 8,803 | 12,475 | 17,781 | 3,939 | 8,164 |
| 게임 | 10,587 | 16,468 | 6,860 | 20,574 | 15,101 | 14,670 | 2,634 | 13,116 |
| 역사 | 8,623 | 8,872 | 9,096 | 6,966 | 4,228 | 5,239 | 1,384 | 12,094 |
| 법/정치 | 8,354 | 10,376 | 4,823 | 17,444 | 10,009 | 17,373 | 1,947 | 12,281 |
| 의학 | 9,194 | 29,621 | 10,603 | 7,910 | 10,703 | 9,471 | 1,733 | 27,069 |
| 철학 | 7,695 | 8,592 | 2,791 | 7,919 | 3,305 | 3,164 | 7,981 | 20,692 |
| 과학 | 6,441 | 14,224 | 3,488 | 9,513 | 9,264 | 6,983 | 3,283 | 9,601 |

**핵심 발견**:
- debate3만 도메인 불변 (std가 낮음, 어떤 주제든 비슷한 비용)
- 의학(medicine)에서 pipe가 29,621 토큰으로 폭발 (복잡한 주제)
- 법/정치에서 rr3가 17,444으로 높음 (긴 분석 필요)
- swm3는 역사(1,384), 의학(1,733)에서 극도로 적은 토큰 (→ 조기 종료 의심)
- 과제 복잡도가 비용 차이를 토폴로지와 독립적으로 약 2배 증폭

---

### 차트 3: B1(Selector) vs B2(Swarm) 정반대 스케일링 (교수님 요청 #3)

**차트 유형: 이중 축 막대 그래프 (토큰 + 턴 수) 또는 스케일링 비율 비교**

| 패턴 | 범주 | 평균 토큰 | 평균 턴 | 평균 시간(초) | 턴당 토큰 |
|------|------|----------|---------|------------|----------|
| sel3 | B1 (중앙) | 8,665 | 3.7 | 96.2 | 2,270 |
| sel4 | B1 (중앙) | 11,131 | 4.2 | 122.0 | 2,538 |
| swm3 | B2 (분산) | 4,148 | 8.6 | 43.9 | 523 |
| swm4 | B2 (분산) | 13,969 | 26.0 | 149.0 | 544 |

**스케일링 비율 (3→4 에이전트 확장 시)**:
- sel4/sel3 = **1.28× 토큰** (준선형, 안정적 확장)
- swm4/swm3 = **3.37× 토큰** (초선형, 위험한 확장)
- sel4/sel3 턴 = 1.14× (거의 동일)
- swm4/swm3 턴 = **3.02×** (턴 폭발)

**핵심**: B1(Selector)은 Host Agent가 중앙에서 분배 → 에이전트 추가해도 안정. B2(Swarm)는 분배 없이 자율 핸드오프 → 에이전트 추가하면 턴 폭발. "동적 라우팅"으로 묶으면 안 되고, 반드시 B1/B2로 분리해야 함.

**턴당 토큰 비교**: B1은 2,270~2,538 (긴 독백), B2는 523~544 (짧은 핸드오프). 같은 "라우팅"이지만 대화 패턴이 완전히 다름.

---

### 차트 4: 대화 로그 통계 (교수님 요청 #4)

모든 실행의 대화 원문이 JSON으로 저장됨. 각 턴마다 {에이전트명, 발화 전문, 타임스탬프, 토큰 수} 기록.

**차트 유형: 대화 길이 분포 히스토그램 또는 턴별 토큰 추이**

| 실험 | 실행 수 | 저장 파일 | 턴 데이터 | 비고 |
|------|---------|----------|----------|------|
| Exp01 v2 | 200회 | raw_A_B1_B2_C_D.json | 각 턴: source, content, tokens | 8패턴 × 25과제 |
| Exp01 v1 | 780회 | raw_A.json, raw_B.json 등 | 동일 구조 | 13패턴 × 20과제 × 3반복 |
| Exp02 | 100회 | raw.json | 턴 + 품질 점수 | 5패턴, G-Eval 포함 |
| Exp05 | 800회 | raw.json | 턴 데이터 | 8패턴 × 25과제 × 4λ |
| Solo | 25회 | raw_S.json | 단일 에이전트 | 베이스라인 |
| **합계** | **1,905회** | **12개 JSON** | **전체 대화 원문 보존** | |

**패턴별 평균 대화 길이 (턴 수)**:
- Solo: 2.0턴
- refl2: 3.2턴
- sel3: 3.7턴
- debate3: 4.6턴
- rr3: 4.6턴
- sel4: 4.2턴
- pipe: 6.0턴
- swm3: 8.8턴
- swm4: **26.1턴** (폭발)

---

### 차트 5: 전체 비용 랭킹 (종합, Exp01-V2 기준)

**차트 유형: 수평 막대 그래프 (토큰 적은 순)**
> Exp01-V2: 8 패턴 × 25 도메인 과제. 본문 순위표(13 패턴, V1)와 수치 차이는 과제셋 차이 때문.

| 순위 | 패턴 | 범주 | 에이전트 | 평균 토큰 | 대비 Solo |
|------|------|------|---------|----------|----------|
| 1 | Solo | S | 1 | 1,287 | 1.0× |
| 2 | swm3 | B2 | 3 | 4,341 | 3.4× |
| 3 | refl2 | C | 2 | 5,281 | 4.1× |
| 4 | sel3 | B1 | 3 | 8,502 | 6.6× |
| 5 | debate3 | C | 3 | 8,657 | 6.7× |
| 6 | sel4 | B1 | 4 | 11,264 | 8.8× |
| 7 | rr3 | A | 3 | 12,332 | 9.6× |
| 8 | swm4 | B2 | 4 | 12,921 | 10.0× |
| 9 | pipe | D | 5 | 13,186 | 10.2× |

---

### 차트 6: 품질 vs 비용 트레이드오프 (파레토 프론티어, Exp02 기준)

**차트 유형: 산점도 (X=토큰, Y=품질 점수)**
> Exp02: 5 패턴 × 20 과제, G-Eval 5차원 품질 평가. Exp01과 과제셋 동일하나 별도 실행.

| 패턴 | 평균 토큰 | 평균 품질 | 품질/1000토큰 |
|------|----------|----------|-------------|
| refl2 | 7,186 | 4.80 | 0.668 |
| rr3 | 13,949 | 4.45 | 0.319 |
| swm3 | 6,575 | 4.05 | 0.616 |
| sel3 | 8,646 | 3.40 | 0.393 |
| debate3 | 8,887 | 3.35 | 0.377 |

**파레토 최적**: refl2 (최고 품질 + 최저 비용). swm3는 refl2 다음으로 효율적 (품질/1000토큰 0.616).

---

### 차트 7: 오류율 비교 (Exp04)

**차트 유형: 막대 그래프**

| 패턴 | 범주 | 총 실행 | 오류 수 | 오류율 |
|------|------|---------|---------|--------|
| debate3 | C | 45 | 0 | 0% |
| pipe | D | 25 | 0 | 0% |
| refl2 | C | 45 | 0 | 0% |
| rr3 | A | 45 | 0 | 0% |
| sel3 | B1 | 45 | 0 | 0% |
| sel4 | B1 | 25 | 0 | 0% |
| swm3 | B2 | 45 | 5 | 11.1% |
| swm4 | B2 | 25 | 19 | **76.0%** |

**핵심**: 오류는 B2(분산 핸드오프)에만 집중. swm4는 76%가 TERMINATE 키워드를 출력하지 못함.

---

### 차트 8: 수렴 감지 비율 (Exp03, Sentence-BERT)

**차트 유형: 막대 그래프**

| 패턴 | 범주 | 수렴율 | 평균 cosine 유사도 | 추세 |
|------|------|--------|------------------|------|
| pipe | D | 32% | 0.662 | +0.169 |
| sel4 | B1 | 28% | 0.502 | +0.382 |
| sel3 | B1 | 24% | 0.403 | +0.397 |
| rr3 | A | 16% | 0.576 | +0.250 |
| swm4 | B2 | 16% | 0.485 | -0.029 |
| swm3 | B2 | 8% | 0.458 | -0.560 |
| debate3 | C | 0% | 0.673 | +0.044 |
| refl2 | C | 0% | 0.462 | +0.052 |

**핵심**: 피드백 패턴(C)은 의미적으로 수렴하지 않음 (0%). 이는 피드백 루프가 계속 새로운 관점을 생성하기 때문. pipe가 32%로 최고 수렴 (순차 정제 특성).

---

### 차트 9: 패턴별 × 과제유형별 품질 점수 (G-Eval, 5점 만점)

동일한 25개 과제를 5개 패턴에 각각 던져서 Claude Sonnet 4.5가 5점 척도(정확성·완전성·일관성·유용성·종합)로 평가한 결과.

**차트 유형: 히트맵 또는 그룹 막대 그래프 (패턴 × 과제유형)**

| 패턴 | 전체 평균 | 사실형(Factual) | 분석형(Analytical) | 기술형(Technical) | 창의형(Creative) |
|------|----------|----------------|-------------------|------------------|-----------------|
| **refl2** | **4.80** | 4.8 | 4.8 | **5.0** | 4.6 |
| rr3 | 4.45 | 4.8 | 4.0 | 4.6 | 4.4 |
| swm3 | 4.05 | 4.4 | 4.0 | 3.2 | 4.6 |
| debate3 | 3.35 | 3.6 | 3.8 | 2.8 | 3.2 |
| sel3 | 3.40 | 3.2 | 3.8 | **2.2** | 4.4 |

**과제 예시 (실제 사용된 25개 중)**:
- 사실형: "열역학 3법칙과 공학적 응용을 설명하라" (sci_01)
- 분석형: "로마 제국의 몰락과 대영제국의 쇠퇴를 구조적으로 비교하라" (hist_02)
- 기술형: "O(1) get/put의 LRU 캐시를 구현하고 자료구조 선택을 설명하라" (cs_02)
- 창의형: "구텐베르크 대신 송나라에서 인쇄술이 발명됐다면?" (hist_03)

**핵심 발견**:
- **refl2가 모든 과제유형에서 최고 품질** — 기술형에서 5.0 만점 (비평가의 코드 리뷰 효과)
- **기술형(코드 작성)에서 패턴 간 격차 극대화**: refl2=5.0 vs sel3=2.2 (2.3배 차이!)
- **사실형에서는 패턴 간 차이 적음**: refl2=4.8, rr3=4.8 (사실 확인은 구조에 덜 의존)
- **sel3은 사실형에서 3.2로 유독 낮음** — Selector가 잘못된 전문가를 선택하는 경우
- **swm3는 창의형에서 4.6으로 높음** — 자율적 핸드오프가 다양한 관점 생성에 유리

---

## [부록 A] 실험에 사용된 실제 에이전트 프롬프트 (System Messages)

> 아래는 experiment_utils.py에서 각 패턴의 에이전트에게 주입된 **실제 시스템 프롬프트** 전문입니다. 모든 프롬프트는 영어로 작성되었으며, Claude Haiku 4.5 모델에 전달됩니다.

---

### Solo (범주 S, 에이전트 1명)

**solo_agent** (General-purpose assistant):
```
You are a knowledgeable assistant. Answer the given question thoroughly and concisely.
When your answer is complete, end with TERMINATE.
```

종료 조건: `TERMINATE` 키워드 또는 max_messages=5

---

### RoundRobin-2 (범주 A, 에이전트 2명)

**researcher** (Research and analysis specialist):
```
You are a researcher. Investigate the given topic and provide key facts and analysis.
```

**writer** (Writer and synthesizer):
```
You are a writer. Based on the research, compose a clear and comprehensive answer.
When the answer is complete and sufficient, end with TERMINATE.
```

종료 조건: `TERMINATE` 키워드 또는 max_messages=10. writer만 TERMINATE 권한 보유.

---

### RoundRobin-3 (범주 A, 에이전트 3명)

**researcher**: `You are a researcher. Investigate the topic and organize key facts and arguments.`
**writer**: `You are a writer. Based on the research, compose a structured answer.`
**reviewer**: `You are a reviewer. Evaluate the answer for accuracy and completeness. If sufficient, say TERMINATE. If not, suggest specific improvements.`

종료 조건: reviewer가 `TERMINATE` 판단 또는 max_messages=10. 순서: researcher → writer → reviewer → (반복).

---

### RoundRobin-4 (범주 A, 에이전트 4명)

**researcher** → **analyst** → **writer** → **reviewer** 순환

- researcher: `Collect key facts, data, and examples about the topic.`
- analyst: `Analyze the collected information and organize it logically.`
- writer: `Based on the analysis, compose a comprehensive answer.`
- reviewer: `Check accuracy, completeness, and coherence. If sufficient, say TERMINATE. If not, point out specific issues.`

종료 조건: `TERMINATE` 또는 max_messages=12. 문제점: 에이전트 4명이 돌아가면서 이전 대화를 전부 읽어야 하므로 입력 토큰이 기하급수적으로 폭발 → 오류율 71.7%.

---

### Selector-3 (범주 B1, 에이전트 3명 + Selector LLM)

3명의 전문가가 있고, **별도의 LLM(Selector)**이 "다음에 누가 말할 차례인지" 결정합니다.

**expert_a** (Technical analysis expert): `You are a technical expert. Analyze from a technical perspective.`
**expert_b** (Business and strategy expert): `You are a business expert. Analyze from a business/market perspective.`
**expert_c** (Synthesis and conclusion expert): `You are a synthesis expert. Combine analyses into a final conclusion. When sufficient, say TERMINATE.`

**Selector LLM에게 주는 프롬프트** (실제 코드):
```
You are in a role play game. The following roles are available:
{roles}.
Read the following conversation. Then select the next role from {participants} to play.
Only return the role name.

{history}

Read the above conversation. Then select the next role from {participants} to play.
Only return the role name.
```

핵심: `allow_repeated_speaker=False` → 같은 에이전트가 연속으로 말할 수 없음.
종료 조건: `TERMINATE` 또는 max_messages=10.

---

### Selector-4 (범주 B1, 에이전트 4명 + Selector LLM)

Sel-3에 **expert_c** (Creative and alternative expert) 추가: `Propose alternative approaches and novel perspectives.`
expert_d가 종합: `Combine all analyses into a final conclusion. When sufficient, say TERMINATE.`

---

### Swarm-3 (범주 B2, 에이전트 3명 + Handoff)

중앙 조정자 없이 에이전트 간 **직접 핸드오프**로 작업을 전달합니다. AutoGen의 `Handoff` 객체를 사용합니다.

**triage** (Initial triage and routing):
```
You are a triage agent. Analyze the task and delegate to the right specialist.
Use handoff to transfer to specialist_a (technical) or specialist_b (synthesis).
```
→ Handoff 대상: specialist_a, specialist_b

**specialist_a** (Technical specialist):
```
You are a technical specialist. Provide technical analysis.
When done, hand off back to triage for next steps.
```
→ Handoff 대상: triage

**specialist_b** (Synthesis specialist):
```
You are a synthesis specialist. Produce the final comprehensive answer.
When complete, say TERMINATE.
```
→ Handoff 대상: triage (더 작업이 필요하면)

종료 조건: `TERMINATE` 또는 max_messages=10.

**핵심 메커니즘**: Handoff는 `FunctionCall` + `FunctionExecutionResult` 메시지 쌍으로 구현됩니다. 에이전트가 `transfer_to_specialist_a()`를 호출하면 다음 턴이 specialist_a로 넘어갑니다. 이 핸드오프 메시지는 실제 내용 없이 라우팅만 수행하므로 **턴당 토큰이 330~337로 매우 짧습니다** (B1의 2,270~2,538과 6배 차이).

---

### Swarm-4 (범주 B2, 에이전트 4명 + Handoff)

triage → specialist_a, specialist_b, specialist_c 세 방향으로 핸드오프. specialist_c가 QA 담당.

**문제점**: 4명일 때 핸드오프 체인이 순환합니다 (triage→A→triage→B→triage→C→triage→A→...). 평균 턴 수가 **25.0턴**으로 폭발, 76%가 max_messages에 걸려 강제 종료됩니다.

---

### Reflection-2 (범주 C, 에이전트 2명)

생성자-비평가 피드백 루프입니다.

**generator** (Content generator):
```
You are a content generator. Create or improve the answer based on the task.
If the critic provided feedback, incorporate it into your revision.
```

**critic** (Quality critic):
```
You are a quality critic. Review the generator's output carefully.
Provide specific, actionable feedback for improvement.
If the quality is sufficient and no major issues remain, say APPROVED.
```

종료 조건: `APPROVED` 또는 `TERMINATE` 또는 max_messages=8.

**핵심**: critic의 `APPROVED`가 자연적 종료 신호로 작동 → 종료 후회가 0.6턴, 품질 손실 0.00. 이것이 Refl-2가 "완벽한 패턴"인 이유입니다.

---

### Reflection-3 (범주 C, 에이전트 3명)

generator → critic → **editor** (최종 편집자)의 3단계 피드백. editor가 `APPROVED` 판단.

---

### Debate-3 (범주 C, 에이전트 3명 + Selector LLM)

찬성-반대-판정의 구조화 토론입니다.

**advocate** (Proponent): `Present strong arguments in favor. Highlight benefits, opportunities, and supporting evidence.`
**critic** (Opponent): `Present counterarguments and identify weaknesses. Highlight risks, costs, and potential problems.`
**judge** (Impartial judge): `After hearing both sides, deliver a balanced verdict. When ready, state your conclusion starting with VERDICT:`

**Selector 프롬프트** (토론 전용):
```
You are in a role play game. The following roles are available:
{roles}.
Read the following conversation. Rules:
1. advocate and critic should alternate (2-3 turns each)
2. After sufficient debate, judge delivers the final verdict
Select the next role from {participants}. Only return the role name.
```

종료 조건: `VERDICT` 또는 `TERMINATE` 또는 max_messages=10.

---

### Debate-4 (범주 C, 에이전트 4명)

Deb-3에 **moderator** (토론 진행자) 추가: `Summarize key points, identify gaps, and guide the discussion. When both sides have been heard, invite the judge.`

---

### Pipeline (범주 D, 에이전트 5명, 2단계)

2개의 독립 팀이 순차 실행됩니다.

**Stage 1**: SelectorGroupChat (3명) — analyst_tech, analyst_biz, analyst_lead
- analyst_lead가 `ANALYSIS_DONE` 출력 시 1단계 종료 (max 8턴)
- Stage 1 출력이 Stage 2의 입력으로 전달됨

**Stage 2**: RoundRobinGroupChat (2명) — synthesizer, finalizer
- 1단계 분석 결과를 받아 최종 답변 정제
- finalizer가 `TERMINATE` 출력 시 종료 (max 6턴)

**Stage 간 연결 프롬프트**:
```
Based on the following analysis, compose a comprehensive final answer:
{stage1_output}
```

---

### MoA - Mixture of Agents (범주 D, 에이전트 4명, 2레이어)

3명이 **병렬로** 각자 독립 답변을 생성하고, 1명이 종합합니다.

**Layer 1** (병렬): proposer_a(기술), proposer_b(비판), proposer_c(창의) — 각각 max 3턴
**Layer 2** (직렬): aggregator가 3개 답변을 종합

**Aggregator에게 주는 프롬프트**:
```
Three experts provided their perspectives. Synthesize them into a balanced final answer:

[proposer_a]: {technical_answer}
---
[proposer_b]: {critical_answer}
---
[proposer_c]: {creative_answer}
```

**비용 폭발 원인**: 3명이 각각 완전한 답을 독립 생성 → 출력 토큰이 입력의 3.58배. 전체 최고 비용(22,333 토큰, Solo의 17.35배).

---

## [부록 B] 수식 상세: ΔU(t) 한계 효용 프레임워크

### B.1 기본 공식

매 에이전트 턴 t에서의 **한계 효용(Marginal Utility)**:

```
ΔU(t) = ΔQ(t) − λ · ΔC(t)
```

각 항의 의미:

| 기호 | 의미 | 계산 방법 |
|------|------|----------|
| Q(t) | t턴까지의 누적 품질 점수 (1~5) | G-Eval의 overall 점수 |
| ΔQ(t) | t턴의 품질 증분 = Q(t) - Q(t-1) | Q(0) = 0으로 설정 |
| C(t) | t턴의 비용 (킬로토큰, kT) | (input_tokens + output_tokens) / 1000 |
| ΔC(t) | t턴의 비용 증분 | = C(t) (각 턴은 이미 증분 비용) |
| λ | 품질 대비 비용 민감도 파라미터 | 0.0 (비용 무시) ~ 0.5 (비용 중시) |

### B.2 종료 판단

```
ΔU(t) ≤ 0 → "이번 턴의 품질 개선이 비용을 정당화하지 못함" → 종료 신호
```

직관적 해석:
- ΔQ(t) = 0.3 (품질 약간 개선), λ·ΔC(t) = 0.5 (비용 부담) → ΔU = -0.2 → 멈춰야 함
- ΔQ(t) = 1.0 (품질 대폭 개선), λ·ΔC(t) = 0.2 (비용 적당) → ΔU = +0.8 → 계속해야 함

### B.3 절대 효용 U(t)

```
U(t) = Q(t) − λ · Σᵢ₌₁ᵗ C(i)
```

누적 비용을 반영한 절대 효용. U(t)의 피크 시점이 **최적 종료 시점**입니다.

### B.4 종료 후회 (Termination Regret)

```
Regret = t_actual − t_optimal
```

- t_optimal: Q(t)가 최대인 턴 (= 더 계속해도 품질이 안 오르는 시점)
- t_actual: 실제 종료된 턴
- Regret > 0: 과잉 계산 (unnecessary over-computation)
- Regret < 0: 과소 계산 (premature termination)

### B.5 λ 둔감성 (핵심 발견)

실험 결과 λ를 0.0에서 0.5까지 변경해도 ΔU 수렴 턴은 0.1턴 이내로 변합니다.

| λ 값 | 평균 수렴 턴 (t_mu_zero) | 해석 |
|------|------------------------|------|
| 0.0 | 1.9턴 | 비용 무시, 순수 품질 포화만 감지 |
| 0.05 | 1.9턴 | 거의 동일 |
| 0.1 | 1.9턴 | 표준값 |
| 0.2 | 1.9턴 | 거의 동일 |
| 0.5 | 1.8턴 | 약간 빨라짐 |

**이유**: ΔQ(t) ≈ 0 (품질 포화)이 ΔU 수렴의 주된 원인이므로, λ·ΔC(t) 항의 영향은 미미합니다. 즉 **"품질이 더 이상 안 오른다"가 가장 강력한 종료 신호**이며, λ 정밀 튜닝 없이도 작동합니다.

---

## [부록 C] G-Eval 품질 평가 시스템

### C.1 평가 모델

- **Judge 모델**: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)
- 실험 에이전트(Claude Haiku 4.5)보다 상위 모델을 사용하여 평가의 질을 확보

### C.2 평가 프롬프트 (실제 코드)

```
You are evaluating a multi-agent conversation output.

## Task
{원래 과제 텍스트}

## Evaluation Rubric
{과제별 평가 기준}

## Cumulative Response (up to turn {턴 번호})
{1턴부터 현재 턴까지 누적된 에이전트 응답}

## Instructions
Rate the cumulative response on these 5 dimensions (1-5 scale each):
1. Accuracy: Correctness of facts and claims
2. Completeness: How thoroughly the task is addressed
3. Coherence: Logical flow and consistency
4. Usefulness: Practical value of the answer
5. Overall: Overall quality considering all factors

Return ONLY a JSON object with exactly these keys:
{"accuracy": N, "completeness": N, "coherence": N, "usefulness": N, "overall": N}

where N is an integer from 1 to 5.
```

### C.3 핸드오프 턴 필터링

Swarm 패턴의 핸드오프 메시지(`FunctionCall`, `Transferred to`, `transfer_to_`)는 실질적 내용이 아니므로 품질 평가에서 **자동 제외**됩니다. 20자 미만의 매우 짧은 턴도 필터링됩니다.

### C.4 누적 평가 방식

각 턴을 독립 평가하는 것이 아니라, **1턴부터 현재 턴까지의 누적 텍스트**를 평가합니다. 이를 통해 "3턴째에 품질이 정점에 도달하고 이후 정체"와 같은 **궤적(trajectory)**을 측정할 수 있습니다.

### C.5 교차 검증 결과

GPT-4o-mini를 2차 평가자로 40개 표본을 교차 검증:
- Pearson r = 0.43~0.62 (중간 수준 상관)
- Cohen's κ_w = 0.244~0.388 ("보통" 수준)
- GPT는 Claude보다 체계적으로 높은 점수를 줌 (평균 차이 -0.93점)
- 따라서 절대값 비교는 불가능하며, **상대적 순위**에 근거하여 비교

---

## [부록 D] 실험 과제(Task Suite) 상세

### D.1 과제 구성

25개 과제, 9개 도메인, 3가지 난이도, 4가지 과제 유형

| 도메인 | 과제 수 | 과제 ID | 과제 유형 |
|--------|---------|---------|----------|
| 과학 (science) | 3 | sci_01~03 | 사실/분석/창의 |
| 컴퓨터과학 (CS) | 3 | cs_01~03 | 사실/기술/분석 |
| 역사 (history) | 3 | hist_01~03 | 사실/분석/창의 |
| 철학 (philosophy) | 3 | phil_01~03 | 사실/분석/창의 |
| 법/정치 (law_politics) | 3 | law_01~03 | 사실/분석/창의 |
| 게임 (gaming) | 3 | game_01~03 | 사실/기술/창의 |
| 공학 (engineering) | 3 | eng_01~03 | 사실/기술/분석 |
| 경영 (business) | 3 | biz_01~03 | 창의/분석/분석 |
| 의학 (medicine) | 1 | med_01 | 분석 |

### D.2 과제 유형 정의

| 유형 | 설명 | 예시 |
|------|------|------|
| factual | 사실 확인, 정확한 정보 전달 | "열역학 3법칙 설명" |
| analytical | 비교분석, 논증 구성 | "마이크로서비스 vs 모놀리식 비교" |
| technical | 코드 작성, 시스템 설계 | "LRU 캐시 O(1) 구현" |
| creative | 독창적 아이디어, 대안 제시 | "AI 시대 인격 동일성 사고 실험 설계" |

### D.3 과제 예시 (3개)

**사실형** (sci_01):
> "Explain the three laws of thermodynamics and their practical implications in engineering."
> 평가 기준: Accuracy of law definitions, real-world engineering examples, logical flow

**기술형** (cs_02):
> "Implement an LRU cache with O(1) get and put operations. Explain the data structure choices and edge cases."
> 평가 기준: Algorithm correctness, complexity analysis, edge case handling

**창의형** (hist_03):
> "Write an alternate history scenario: What if the printing press had been invented in Song Dynasty China instead of Gutenberg's Europe?"
> 평가 기준: Historical plausibility, butterfly effect reasoning, narrative coherence

### D.4 과제 유형별 오류 패턴 (Exp04 발견)

| 과제 유형 | RR-2 오류율 | RR-3 오류율 | RR-4 오류율 | 해석 |
|----------|-----------|-----------|-----------|------|
| factual | 0% | 0% | 0% | 사실 확인은 팀 크기와 무관하게 안전 |
| technical | 33% | 53% | 100% | 코드 작성은 팀이 커질수록 실패 |
| analytical | 0% | 14% | 71% | 분석 과제는 중간 수준 |
| creative | 0% | 24% | 67% | 창의 과제도 위험 증가 |

---

## [부록 E] 실험 인프라 상세

### E.1 모델 설정

| 역할 | 모델 | 용도 |
|------|------|------|
| 에이전트 실행 | Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | 14개 패턴의 모든 에이전트 |
| 품질 평가 (Judge) | Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) | G-Eval 5차원 평가 |
| Selector LLM | Claude Haiku 4.5 | SelectorGroupChat의 화자 선택 |
| 교차 검증 | GPT-4o-mini | 모델 일반화 검증 |

### E.2 종료 조건 정리

| 패턴 | 키워드 종료 | max_messages | 비고 |
|------|-----------|-------------|------|
| solo | TERMINATE | 5 | |
| rr2~rr4 | TERMINATE | 10/10/12 | 마지막 에이전트만 TERMINATE 권한 |
| sel3/sel4 | TERMINATE | 10/12 | Selector LLM이 화자 선택 |
| swm3/swm4 | TERMINATE | 10/12 | Handoff 기반 자율 라우팅 |
| refl2/refl3 | APPROVED 또는 TERMINATE | 8/10 | critic/editor가 승인 |
| debate3/debate4 | VERDICT 또는 TERMINATE | 10/12 | judge가 판결 |
| pipe | Stage1: ANALYSIS_DONE, Stage2: TERMINATE | 8+6=14 | 2단계 순차 |
| moa | (max_messages만) | 3×3+2=11 | proposer는 키워드 종료 없음 |

### E.3 AutoGen 프레임워크 구조

```
AutoGen AgentChat
├── RoundRobinGroupChat    ← Solo, RR-2/3/4, Refl-2/3 사용
├── SelectorGroupChat      ← Sel-3/4, Debate-3/4 사용
└── Swarm                  ← Swm-3/4 사용

종료 조건 조합 (OrTerminationCondition):
├── TextMentionTermination("TERMINATE")  ← 키워드 감지
├── TextMentionTermination("APPROVED")   ← 반성 패턴 전용
├── TextMentionTermination("VERDICT")    ← 토론 패턴 전용
└── MaxMessageTermination(max_messages)  ← 안전장치
```

복합 팀 (자체 구현):
- **PipelineTeam**: Stage1.run() → 결과 추출 → Stage2.run(결과)
- **MoATeam**: asyncio.gather(*[proposer.run() for each]) → aggregator.run(결합)

### E.4 실험 실행 수

| 실험 | 실행 수 | 구성 | 데이터 |
|------|---------|------|--------|
| Exp01 v1 | 780회 | 13패턴 × 20과제 × 3반복 | summary_all.csv |
| Exp01 v2 | 200회 | 8패턴 × 25과제 × 1반복 | summary_A_B1_B2_C_D.csv |
| Solo | 25회 | 1패턴 × 25과제 | summary_S.csv |
| Exp02 | 100회 | 5패턴 × 20과제, 276 품질 점수 | scores.csv |
| Exp03 | (Exp01 데이터 재분석) | Sentence-BERT 수렴 | convergence_summary_semantic.csv |
| Exp04 | (Exp01 데이터 재분석) | 오류 귀인 | error_report.md |
| Exp05 | 800회 | 8패턴 × 25과제 × 4λ값 | summary.csv |
| 교차 모델 | 125회 | 5패턴 × 25과제 (GPT-4o-mini) | cross_validation_summary.csv |
| **합계** | **~2,030회** | | **12개 JSON + 다수 CSV** |

---

## [PPT 수정 지시사항] 교수님 피드백 반영 (★ 반드시 반영)

> memo.md 피드백을 슬라이드별로 정리. PPT 재생성 시 아래 내용을 **반드시** 포함해야 합니다.

---

### 슬라이드 4 수정 (14개 패턴 분류 체계) — "어떤 프롬프트/질문 사용했는지 누락"

**문제**: 6개 범주를 설명하면서 각 에이전트에게 어떤 프롬프트를 줬는지 안 보여줌.

**추가해야 할 것**: 범주별 대표 프롬프트를 1~2줄씩 표시. 실험에 사용한 25개 과제 중 대표 질문 예시도 명시.

**범주별 핵심 프롬프트 (부록 A에서 발췌)**:

| 범주 | 에이전트 구성 | 핵심 프롬프트 요약 |
|------|------------|-----------------|
| S (Solo) | solo_agent 1명 | "Answer thoroughly and concisely. When complete, end with TERMINATE." |
| A (순차 체인) | researcher→writer→reviewer | researcher: "Investigate and organize key facts" / writer: "Compose structured answer" / reviewer: "If sufficient, say TERMINATE" |
| B1 (중앙 라우팅) | Selector LLM + expert 3~4명 | Selector: "Read conversation, select next role" / expert_c: "Combine into final conclusion. When sufficient, TERMINATE" |
| B2 (분산 핸드오프) | triage + specialist 2~3명 | triage: "Analyze task, delegate via handoff" / specialist_b: "Produce final answer. When complete, TERMINATE" |
| C-반성 | generator + critic | generator: "Create or improve answer" / critic: "Review, provide feedback. If sufficient, say APPROVED" |
| C-토론 | advocate + critic + judge | advocate: "Arguments in favor" / critic: "Counterarguments" / judge: "Balanced verdict → VERDICT:" |
| D-Pipe | Stage1(sel3) → Stage2(rr2) | Stage1: "ANALYSIS_DONE when ready" → Stage2: "Synthesize into final answer, TERMINATE" |
| D-MoA | 3 proposer (병렬) + aggregator | 각 proposer가 독립 답변 → aggregator: "Synthesize three perspectives into balanced answer" |

**실험 과제 예시 (25개 중 대표 4개)**:
- 사실형(sci_01): "Explain the three laws of thermodynamics and their practical implications in engineering."
- 분석형(hist_02): "Compare the fall of the Roman Empire with the decline of the British Empire."
- 기술형(cs_02): "Implement an LRU cache with O(1) get and put operations."
- 창의형(hist_03): "What if the printing press had been invented in Song Dynasty China instead of Gutenberg's Europe?"

---

### 슬라이드 5,6,7 수정 (실험01 결과) — "라우팅이 에이전트를 이긴다 말고 더 유의미한 결론"

**문제**: "Swm-3 < RR-2" 하나만 강조. 더 풍부한 해석이 필요.

**보강할 결론 3가지**:

**결론 1 — 비용 위계가 뒤집혔다**:
기존 가정: "A(순차) < B(동적) ≈ C(피드백) < D(복합)"
실험 결과: **A ≈ B2 < B1 ≈ C ≪ D** (Mann-Whitney p=0.857 for A vs B2)
→ 분산 핸드오프(B2)가 순차 체인(A)과 동일 비용 수준. "동적 라우팅은 비싸다"는 가정 폐기.

**결론 2 — 확장 방향이 토폴로지에 의해 결정된다**:
| 비교 | 3명→4명 비용 변화 | 해석 |
|------|-----------------|------|
| B1 (Sel): 7,851→11,595 | **1.48배 (준선형)** | 중앙 라우터가 조정 비용 흡수 |
| B2 (Swm): 4,196→13,321 | **3.17배 (초선형)** | 핸드오프 체인 폭발 (턴 10→25) |
| C-반성: 5,237→12,095 | **2.31배** | 피드백 루프 1회 추가 |
| C-토론: 9,313→11,637 | **1.25배** | "턴 규율" — 참여자↑ 발언량↓ |
→ "에이전트 추가 비용"은 고정이 아니라 토폴로지 함수. 팀 설계 시 에이전트 수가 아니라 확장 계수를 먼저 확인해야 함.

**결론 3 — 대화 패턴이 근본적으로 다르다 (같은 "동적 라우팅"인데)**:
| 지표 | B1 (Selector) | B2 (Swarm) |
|------|-------------|-----------|
| 턴당 토큰 | 2,114~2,616 (긴 독백) | 337~330 (짧은 핸드오프) |
| 평균 턴 수 | 3.5~4.1 (적은 턴) | 10.2~25.0 (많은 턴) |
| 오류율 | 0% | 11~76% |
| TERMINATE 출현 | 높음 | 1~6% |
→ B1과 B2를 묶으면 안 되는 이유가 모든 지표에서 확인됨. "동적 라우팅"이라는 레이블이 학술적으로 부정확.

---

### 슬라이드 8 수정 (품질 궤적) — "패턴별 agent 수별 여러 선 필요, refl-2/refl-3 없음"

**문제**: 5개 패턴만 1개 선씩 그려놓음. 같은 범주 내에서 에이전트 수별 비교가 안 됨.

**차트 수정 요구사항**:
1. **범주별로 에이전트 수 변화를 보여주는 다중 선 그래프** 필요
2. 각 범주별 서브차트 또는 색상으로 구분:

**범주 A (순차 체인)** — 에이전트 수별 비용 + 오류율:
| 패턴 | 에이전트 | 총 토큰 | 시간(초) | 오류율 | 턴당출력 |
|------|---------|---------|---------|--------|---------|
| RR-2 | 2명 | 4,759 | 52.4 | 8.3% | 1,583 |
| RR-3 | 3명 | 10,121 | 96.6 | 23.3% | 1,711 |
| RR-4 | 4명 | 12,040 | 118.8 | 71.7% | 1,942 |
→ 선 3개: 토큰(상승), 오류율(급상승), 턴당출력(완만 상승=협력적 증폭)

**범주 B1 (중앙 라우팅)** — Sel-3 vs Sel-4:
| 패턴 | 에이전트 | 총 토큰 | 턴 | 턴당 토큰 |
|------|---------|---------|-----|----------|
| Sel-3 | 3명 | 7,851 | 3.5 | 2,114 |
| Sel-4 | 4명 | 11,595 | 4.1 | 2,616 |
→ 준선형 확장 (1.48배)

**범주 B2 (분산 핸드오프)** — Swm-3 vs Swm-4:
| 패턴 | 에이전트 | 총 토큰 | 턴 | 턴당 토큰 |
|------|---------|---------|------|----------|
| Swm-3 | 3명 | 4,196 | 10.2 | 337 |
| Swm-4 | 4명 | 13,321 | 25.0 | 330 |
→ 초선형 폭발 (3.17배), 턴당 토큰은 일정 (순수 턴 폭발)

**범주 C-반성** — Refl-2 vs Refl-3 (★ 이것이 누락되었던 것):
| 패턴 | 에이전트 | 총 토큰 | 시간(초) | 품질(G-Eval) |
|------|---------|---------|---------|------------|
| Refl-2 | 2명 | 5,237 | 60.2 | **4.80** |
| Refl-3 | 3명 | 12,095 | 120.2 | (미측정) |
→ 2.31배 폭발. Refl-2가 최고 효율+최고 품질. 3명은 비용만 2배.

**범주 C-토론** — Debate-3 vs Debate-4:
| 패턴 | 에이전트 | 총 토큰 | 턴당출력 | 품질(G-Eval) |
|------|---------|---------|---------|------------|
| Deb-3 | 3명 | 9,313 | 1,719 | 3.35 |
| Deb-4 | 4명 | 11,637 | 1,440 | (미측정) |
→ 1.25배 증가(준선형). 턴당출력 오히려 감소 = "턴 규율" 효과.

**범주 D** — Pipe vs MoA:
| 패턴 | 에이전트 | 총 토큰 | 구조 |
|------|---------|---------|------|
| Pipe | 5명 | 13,856 | 순차 2단계 |
| MoA | 4명 | 22,333 | 병렬+집약 |
→ MoA가 에이전트 적은데 비용 1.6배. 병렬 실행이 비용 폭발의 원인.

---

### 슬라이드 9 수정 (평가 신뢰도) — "어떤 프롬프트/질문으로 평가했는지 빠짐"

**문제**: 교차 검증 결과만 있고, G-Eval 평가 시 어떤 프롬프트를 썼는지 안 보여줌.

**추가해야 할 것**:

**G-Eval 평가 프롬프트 (실제 사용):**
```
You are evaluating a multi-agent conversation output.

## Task
{원래 과제 텍스트, 예: "Explain the three laws of thermodynamics..."}

## Evaluation Rubric
{과제별 평가 기준, 예: "Accuracy of law definitions, real-world engineering examples..."}

## Cumulative Response (up to turn {N})
{1턴부터 N턴까지 누적된 에이전트 응답 전문}

## Instructions
Rate on 5 dimensions (1-5 scale):
1. Accuracy  2. Completeness  3. Coherence  4. Usefulness  5. Overall
Return JSON: {"accuracy": N, "completeness": N, "coherence": N, "usefulness": N, "overall": N}
```

- **평가 모델**: Claude Sonnet 4.5 (에이전트보다 상위 모델)
- **평가 방식**: 턴별 누적 평가 (각 턴을 독립 평가가 아님 → 궤적 측정 가능)
- **필터링**: 핸드오프 메시지(FunctionCall), 20자 미만 턴 자동 제외
- **교차 검증 모델**: GPT-4o-mini (40개 표본)

---

### 슬라이드 10 수정 (수렴 감지) — "ΔU 수식 정확히 설명해야 함"

**문제**: 이 슬라이드는 Exp03 의미 수렴인데, ΔU 수식 설명이 필요하다는 피드백. 슬라이드 12(ΔU 검증)와 연결하여 수식을 정확히 설명.

**ΔU 수식 완전 설명 (슬라이드 10 또는 12에 삽입)**:

**Step 1 — 각 항의 정의**:
```
ΔU(t) = ΔQ(t) − λ · ΔC(t)

ΔQ(t) = Q(t) − Q(t−1)    ← t턴에서 품질이 얼마나 개선됐는가 (G-Eval overall 점수 차이)
ΔC(t) = C(t)              ← t턴의 토큰 비용 (킬로토큰 단위, 입력+출력)
λ                          ← 비용 민감도 (0.0=비용 무시, 0.5=비용 중시)
```

**Step 2 — 작동 원리 (예시)**:
| 상황 | ΔQ(t) | λ·ΔC(t) | ΔU(t) | 판단 |
|------|-------|---------|-------|------|
| 품질 대폭 개선, 비용 적당 | +1.0 | 0.2 | **+0.8** | 계속 |
| 품질 미미, 비용 부담 | +0.3 | 0.5 | **−0.2** | 멈춰야 함 |
| 품질 포화 (더 이상 개선 없음) | 0.0 | 0.3 | **−0.3** | 확실히 멈춰야 함 |

**Step 3 — 왜 수렴하는가?**:
- 초반: ΔQ(t) > 0 (품질 개선 중) → ΔU(t) > 0 → 계속할 가치 있음
- 후반: ΔQ(t) → 0 (품질 포화) → ΔU(t) → −λ·ΔC(t) ≤ 0 → 자연적 종료 신호
- 핵심: **품질이 더 이상 안 오르면** 비용 항에 관계없이 ΔU ≤ 0

**Step 4 — λ가 왜 안 중요한가?**:
| λ 값 | 수렴 턴 | 해석 |
|------|---------|------|
| 0.0 | 1.9턴 | 비용 무시, 순수 품질 포화만 감지 |
| 0.1 | 1.9턴 | 표준값, 거의 동일 |
| 0.5 | 1.8턴 | 0.1턴 차이뿐 |
→ ΔQ(t) ≈ 0이 지배적 신호. λ 튜닝 불필요.

---

### 슬라이드 11 수정 (종료 실패 유형) — "패턴별/에이전트별/카테고리별 설명 매우 누락"

**문제**: 3가지 실패 유형만 나열하고 구체적 수치가 부족.

**카테고리별 상세 분석 추가**:

**범주 A (순차 체인) — 맥락 폭발**:
| 패턴 | 에이전트 | 성공 | 실패 | 오류율 | 실패 원인 |
|------|---------|------|------|--------|---------|
| RR-2 | 2명 | 55/60 | 5 | 8.3% | 입력 토큰 초과 (기술형 과제) |
| RR-3 | 3명 | 46/60 | 14 | 23.3% | 맥락 축적 2.59배 초선형 |
| RR-4 | 4명 | 17/60 | 43 | 71.7% | 28K 프롬프트 절단 한계 도달 |
→ 오류율 2명→3명→4명: **8%→23%→72%** (기하급수적). 과제별: 사실형 0%, 기술형 33→53→100%.

**범주 B1 (중앙 라우팅) — 무결**:
| 패턴 | 에이전트 | 오류율 | TERMINATE 종료율 |
|------|---------|--------|---------------|
| Sel-3 | 3명 | **0%** | 100% |
| Sel-4 | 4명 | **0%** | 100% |
→ 중앙 라우터가 대화 흐름을 통제하므로 오류 없음. 가장 안전한 패턴.

**범주 B2 (분산 핸드오프) — 턴 폭발**:
| 패턴 | 에이전트 | 오류율 | MaxMsg 도달 | TERMINATE 성공 |
|------|---------|--------|-----------|--------------|
| Swm-3 | 3명 | 11.1% | — | 89% |
| Swm-4 | 4명 | **76.0%** | **71.7%** | 28% |
→ Swm-4: 핸드오프 순환(triage→A→triage→B→triage→C→...) 25턴까지 폭주. TERMINATE 메시지 자체가 구조적으로 희귀 (1~6%).

**범주 C (피드백) — 안전**:
| 패턴 | 에이전트 | 오류율 | 종료 방식 |
|------|---------|--------|---------|
| Refl-2 | 2명 | 0% | APPROVED (비평가 승인) |
| Refl-3 | 3명 | 0% | APPROVED |
| Debate-3 | 3명 | 0% | VERDICT (판사 판결) |
| Debate-4 | 4명 | 0% | VERDICT |
→ 구조화된 종료 신호(APPROVED/VERDICT)가 내장 → 키워드 종료가 100% 작동.

**범주 D (복합) — MoA만 문제**:
| 패턴 | 에이전트 | 오류율 | 문제 |
|------|---------|--------|------|
| Pipe | 5명 | 0% | Stage 구조가 종료를 강제 |
| MoA | 4명 | 100%(MaxMsg) | 집약자가 TERMINATE를 한 번도 출력 안 함 |

**스웜 에이전트의 통신 구조가 근본적으로 다른 이유**:
| 지표 | 스웜 (B2) | 나머지 (A,B1,C,D) |
|------|----------|------------------|
| 메시지 길이 | 205~322자 | 1,787~1,982자 |
| TERMINATE 포함률 | 1~6% | 9~18% |
| 핸드오프 메시지 비율 | 60%+ | 0% |
→ 스웜은 "실질 대화"보다 "라우팅 메시지"가 대부분. 키워드 종료 구조와 근본적 불일치.

---

### 슬라이드 12 수정 (ΔU 검증 + 교차 모델) — "OpenAI/GPT 비교 도표 하나도 없음"

**문제**: Claude vs GPT 비교를 말만 하고 도표가 없음.

**추가해야 할 도표 1 — Claude vs GPT-4o-mini 비용 비교**:

| 패턴 | Claude 토큰 | GPT 토큰 | GPT/Claude 비율 | 순위 변동 |
|------|-----------|---------|---------------|---------|
| Solo | 1,287 | 697 | 0.54x | 동일 (1위) |
| Swm-3 | 4,196 | 3,203 | 0.76x | 동일 (2위) |
| Refl-2 | 5,237 | 5,105 | 0.97x | 동일 (3위) |
| Sel-3 | 7,851 | 3,598 | 0.46x | 동일 (4위) |
| RR-3 | 10,121 | 14,325 | 1.42x | 동일 (5위) |

**Spearman ρ = 0.900 (p = 0.037)** — 비용 순서 강하게 보존됨.

차트: **이중 막대 그래프** (Claude 파랑 vs GPT 초록, 패턴별 나란히)

**추가해야 할 도표 2 — 모델 간 차이 분석**:

| 발견 | Claude | GPT | 보존 여부 |
|------|--------|-----|---------|
| Swm-3 < RR-2 | 4,196 < 4,759 ✅ | 3,203 < ? (RR-2 미실행) | 부분 확인 |
| B2 초선형 확장 | Swm-4/Swm-3 = 3.17x | (GPT Swm-4 미실행) | 미확인 |
| 비용 순서 | Solo<Swm3<Refl2<Sel3<RR3 | Solo<Swm3<Sel3<Refl2<RR3 | **거의 동일** |
| 절대 비용 | 기준선 | GPT가 평균 0.63x 저렴 | 모델 의존 |

**한계점 명시**: n=5 패턴만 비교. 전체 13패턴으로 확장 필요. Swm-4 확장 비율은 GPT에서 미검증.
