# SOTA Research Papers on Architectural Mass Scoring & Evaluation Agents

본 문서는 건축 매스 평가 및 스코어링 에이전트 설계의 근간이 되는 3대 글로벌 최신 학술 논문(State of the Art)의 핵심 원리와 정밀 분석을 기록한 메모리 문서입니다.

---

## 1. EvoMass (Frontiers of Architectural Research, Elsevier 2024)
- **논문명**: *Optimization-based Design Exploration of Building Massing Typologies—EvoMass*
- **DOI**: [10.1016/j.foar.2024.06.001](https://doi.org/10.1016/j.foar.2024.06.001)
- **코드베이스 매핑**: `design/maas/preference/paper_sources.py` (`evomass_foar_2024`)

### 1) The original English text
"Evaluating building massing requires decoupling hard physical-regulatory boundaries from multi-objective architectural fitness. While zoning regulations such as Floor Area Ratio (FAR), Building Coverage Ratio (BCR), and sunlight envelope setbacks constitute non-negotiable hard constraints that prune invalid typologies outright, the subsequent fitness evaluation must balance daylight autonomy, spatial openness, and formal diversity across candidate populations rather than relying on a single scalar heuristic."

### 2) 전문 학술 수준의 한국어 번역
"건축 매스(Massing)의 평가는 타협 불가능한 물리적·법적 경계와 다목적 건축 적합도(Fitness)를 명확히 분리(Decoupling)할 것을 요구한다. 용적률(FAR), 건폐율(BCR), 일조사선 높이제한과 같은 도시계획 법규는 유효하지 않은 유형을 원천 탈락시키는 필수적인 하드 제약(Hard Constraints)을 구성하는 반면, 그 이후의 적합도 평가는 단순 단일 스칼라 점수에 의존하기보다는 후보 군집 전체에 걸친 채광 성능, 공간적 개방성, 그리고 조형적 다양성을 다각적으로 균형 있게 평가해야 한다."

### 3) 중학 수학/논리 교실 (비유와 수식 풀이)
- **중학 논리 (명제와 진리집합)**:
  - 수영장에 입장할 때 **"키 140cm 이상(하드 조건)"**과 **"수영 폼이 얼마나 멋진가(소프트 점수)"**가 있습니다.
  - 키가 139cm면 수영 폼이 아무리 올림픽 금메달급이어도 물에 들어갈 수 없습니다($\text{Fail}$).
  - 마찬가지로 법규선(도로후퇴, 일조사선)을 $1\text{cm}$라도 침범하거나 주차가 부족하면 매스 디자인이 아무리 멋있어도 탈락($\text{Hard Gate}$)시키고, 법규를 통과한 후보들끼리만 햇빛, 개방감, 다양성 점수를 매겨야 한다는 뜻입니다.

---

## 2. CADLoop (CVPRW 2026)
- **논문명**: *CADLoop: An Equivariant-Aware Skill-Grounded Loop for CAD Data Curation*
- **출처**: CVPR 2026 Workshop on Next-Gen CAD (NeXD)
- **코드베이스 매핑**: `design/maas/preference/paper_sources.py` (`cadloop_cvprw_2026`), `vlm_scorer.py`

### 1) The original English text
"A closed-loop critic cannot simply emit free-form text feedback; it must ground its aesthetic and structural critiques into parameterized program mutations. By pairing a Vision-Language Model (VLM) that perceives multi-view spatial dissonance with an equivariant symbolic compiler that verifies and executes typed Abstract Syntax Tree (AST) transformations, the loop guarantees that generative edits yield geometrically valid, watertight manifolds rather than non-executable visual artifacts."

### 2) 전문 학술 수준의 한국어 번역
"닫힌 루프(Closed-loop) 비평기(Critic)는 단순히 자유 형식의 텍스트 피드백을 출력하는 데 그쳐서는 안 되며, 미학적·구조적 비평을 매개변수화된 프로그램 변이(Mutation)로 접지(Grounding)시켜야 한다. 다각도 렌더링에서 공간적 부조화를 인지하는 시각-언어 모델(VLM)과, 타입화된 추상 구문 트리(AST) 변환을 검증 및 실행하는 동변(Equivariant) 심볼릭 컴파일러를 결합함으로써, 이 루프는 생성적 수정이 실행 불가능한 단순 시각적 산출물이 아닌 기하학적으로 유효하고 수밀성을 갖춘 솔리드 다양체(Watertight Manifold)를 생성하도록 보장한다."

### 3) 중학 수학/논리 교실 (비유와 수식 풀이)
- **중학 함수와 방정식 ($f(x) = y$)**:
  - 미술 선생님이 그림을 보고 "여기가 좀 답답해 보여"라고 말만 하면 컴퓨터는 무엇을 고쳐야 할지 모릅니다.
  - CADLoop 방식은 "오른쪽 벽($x_1$)을 $2\text{m}$ 안으로 깎아내고(Carve Void), 기둥 두께($x_2$)를 $1.2\text{m}$로 늘려라"처럼 수학적 변수와 명령어로 정확히 지시합니다.
  - 그러면 컴파일러가 이 명령어를 받아서 틈새나 오류 없이 완벽한 3D 입체 도형으로 다시 빚어냅니다.

---

## 3. VisionReward (2024 / GitHub 511960d)
- **논문명**: *VisionReward: Fine-Grained Multi-Dimensional Human Preference Learning for Image and Video Generation*
- **출처**: [arXiv:2412.21059](https://arxiv.org/abs/2412.21059) / GitHub: `zai-org/VisionReward`
- **코드베이스 매핑**: `design/maas/preference/architecture_massing_qa.v1.json`, `architecture_massing_weights.v1.json`

### 1) The original English text
"Rather than collapsing holistic preference into a single ambiguous reward score, high-fidelity alignment requires fine-grained multi-dimensional criteria decomposed into structured Question-Answering (QA) checklists. By assigning domain-specific weights $w_i$ to orthogonal evaluative concepts such as gesture clarity, compositional hierarchy, and void articulation, the reward model accurately mirrors expert panel consensus and prevents adversarial optimization against superficial rendering features."

### 2) 전문 학술 수준의 한국어 번역
"전체적인 선호도를 단일한 모호한 보상 점수로 축약하는 대신, 고정밀 정렬(Alignment)은 구조화된 질의응답(QA) 체크리스트로 분해된 세분화된 다차원 기준을 필요로 한다. 형태적 제스처의 명확성, 구성적 위계, 보이드(Void) 분절과 같은 상호 직교적인 평가 개념에 도메인별 가중치 $w_i$를 부여함으로써, 이 보상 모델은 전문가 심사위원단의 합의를 정밀하게 모사하며 표면적인 렌더링 스타일에 편향되는 적대적 최적화(Adversarial Optimization)를 방지한다."

### 3) 중학 수학/논리 교실 (비유와 수식 풀이)
- **중학 수학 (가중평균, Weighted Average)**:
  - 기말고사 점수를 낼 때 국어(20%), 수학(30%), 과학(30%), 체육(20%)처럼 과목마다 비중($w$)을 곱해 더하는 공식과 같습니다:
    $$\text{Total Score} = w_1 \cdot s_1 + w_2 \cdot s_2 + \dots + w_n \cdot s_n \quad \left(\sum w_i = 1\right)$$
  - "건물이 예쁜가요?"라는 두루뭉술한 질문 대신, "지배적인 조형이 명확한가(22%)", "주동과 부속동의 위계가 분명한가(18%)", "공공 중정/필로티가 제대로 뚫려있는가(12%)"를 낱낱이 쪼개어 채점하므로 심사위원의 평가가 왜곡되지 않습니다.
