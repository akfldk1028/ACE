# Multi-Agent Termination Dynamics — 14장 한글 발표 스크립트

**데크**: NotebookLM "Multi-Agent Termination Dynamics Across Coordination Topologies" (V1)
**소요**: 1장당 30~60초, 총 10~15분
**용도**: AI/ML 엔지니어 면접 / 교수 발표 / COLM 2026 데모

---

## 1. Hero — 인트로 (30초)

> "안녕하세요. 'When Should Multi-Agent Teams Stop?' 라는 연구 발표하겠습니다.
> 한 줄 요약: **14가지 멀티에이전트 토폴로지의 종료 역학을 처음으로 통합 비교한 연구**입니다.
> COLM 2026 제출 타깃. 2,200회 이상 실험. 7가지 발견 모두 직관과 다릅니다."

**핵심 메시지**: 학회급 정량 연구. 첫 통합 비교.

---

## 2. Problem — 종료 후회의 3 시나리오 (45초)

> "AutoGen이나 LangGraph 만들 때 max_turns=10으로 박는 게 흔합니다. 근데 2명 팀과 4명 토론 팀에 같은 기준 쓰는 건 말이 안 됩니다.
>
> 결과 — **종료 후회 (termination regret)** 3가지:
> 1. **과잉 종료**: 합의 후 4라운드 더 토론 → 토큰 낭비
> 2. **과소 종료**: 파이프라인 초안에서 멈춤 → 오류 미수정
> 3. **토폴로지 불일치**: 셀렉터 라우팅 중 강제 종료 → 기능 손실
>
> 이 당연한 문제를 아무도 체계적으로 안 다뤘습니다."

**핵심 메시지**: 갭 명확. 후회 정의.

---

## 3. Research Gap — 선행 연구 비교표 (45초)

> "관련 연구들 비교표:
> | 연구 | 패턴 수 | 토폴로지 | 종료 다룸? |
> |---|---|---|---|
> | REFRAIN (2025) | 1 | 단일 CoT | ✓ |
> | Hu NeurIPS 2025 | 1 | 토론 전용 | ✓ |
> | MAST (Cemri 2025) | ~5 | 혼합 | ✗ |
> | **본 연구** | **14** | **6 카테고리** | **✓ 토폴로지-인지** |
>
> 각자의 섬에 있던 연구를 한 프레임워크에서 통합 비교했습니다."

**핵심 메시지**: 우리만 통합. 14는 압도적.

---

## 4. 14 Patterns Taxonomy (60초)

> "14개 패턴, 6 카테고리. Masterman 2025의 Chain/Star/Mesh + Tran 2025의 centralized/distributed 분리 결합:
>
> - **S**: Solo (1명 baseline)
> - **A** Sequential Chain: RR-2, RR-3, RR-4
> - **B1** Star (Centralized Routing): Sel-3, Sel-4 — 셀렉터가 다음 발화자 픽
> - **B2** Mesh (Decentralized Handoff): Swm-3, Swm-4 — 피어 간 핸드오프
> - **C** Feedback: Refl-2/3 (Reflexion) + Deb-3/4 (Debate)
> - **D** Composed: Pipe(5명), MoA(4명)
>
> **B1과 B2를 처음으로 분리**한 게 핵심 분류 기여."

**핵심 메시지**: B1/B2 분리가 새 분류.

---

## 5. Experimental Design (45초)

> "실험 규모:
> - **14 patterns × 25 tasks × 9 domains × 4 task types × 3 reps = 2,200회 이상**
> - **5 LLMs**: Haiku 4.5 (에이전트), Sonnet 4.5 (G-Eval 채점), GPT-4o-mini (교차 검증 ρ=0.900), Gemini, GPT-5.4
> - **7 실험** (Exp01~07): 비용/품질/수렴/오류/적응종료/비용예측/난이도"

**핵심 메시지**: 학술급 통제 실험. 5 LLM 교차 검증.

---

## 6. ⭐ Finding 1 — 비용 위계 뒤집힘 (60초)

> "첫 번째 반직관 결과 — **3-에이전트 swarm이 2-에이전트 RR보다 싸다**.
>
> Swm-3: **3,203 토큰** vs RR-2: **4,759 토큰**.
> Mann-Whitney **U=95, p<0.001**.
>
> 이유: 핸드오프는 짧은 메시지 (~337 tok/turn). RR은 매번 풀 컨텍스트.
> **에이전트 수가 아니라 통신 패턴이 비용을 정한다**는 게 결론."

**핵심 메시지**: 토폴로지 > 에이전트 수. 통계 강력.

---

## 7. ⭐ Finding 2 — 토론 품질 단조 하락 (45초)

> "두 번째 — **토론하면 좋아진다**는 통념 정면 반박.
>
> Debate-3 G-Eval 점수 라운드별: **3.8 → 3.4 → 3.3** 단조 하락.
> Du et al. ICML 2024는 'multi-agent debate improves quality' 주장. 우리는 정량 측정으로 반박.
>
> 이유: 매 턴 새 논점 생성 → 의미적 수렴 0% (Exp03)."

**핵심 메시지**: 학회 논문 정면 반박 가능. Sonnet 4.5 G-Eval로 측정.

---

## 8. ⭐ Finding 3 — B1 vs B2 분리 (75초)

> "세 번째 — **'동적 라우팅'이라고 묶였던 B를 둘로 쪼갰더니 정반대 행동**.
>
> | | B1 (Star, Sel) | B2 (Mesh, Swm) |
> |---|---|---|
> | 스케일링 | **1.48× 준선형** | **3.17× 초선형** |
> | 토큰/턴 | ~2,114 (긴 독백) | ~337 (짧은 핸드오프, 많은 턴) |
>
> **새 비용 위계**: A ≈ B2 < B1 ≈ C ≪ D.
> 통계: A vs B2 p=0.857 (동등), B2 vs C p=0.028 (유의 차).
> 분류 기여 + 정량 검증 동시 달성."

**핵심 메시지**: 분류학에 새 분기 박았음.

---

## 9. ⭐ Finding 4 — 키워드가 최적 (Negative Result) (60초)

> "네 번째 — **TERMINATE 키워드가 7/8에서 최적**. Negative result지만 실용 가치 큼.
>
> 800회 통제 실험. ΔU 적응적 종료를 키워드 대체로 썼을 때:
> - Swm-4: **−70% 절감** (유일한 성공. 키워드는 28% 성공률)
> - RR-3: +32% (악화)
> - Sel-3: +63%
> - Refl-2: +258%
>
> => **'sophisticated > simple'은 7/8 패턴에서 틀림**.
> ΔU는 진단 도구로만 쓰고, 실제 종료는 키워드 + B2만 ΔU 보강."

**핵심 메시지**: 실용 가이드. 학술계 적응형 종료 트렌드 반박.

---

## 10. ⭐ Finding 5 — 비용 예측 모델 (60초)

> "다섯 번째 — **토폴로지로 비용을 사전 예측 가능**.
>
> Random Forest, 718회 학습, 5-fold CV → **R²=0.54**.
>
> Top features:
> 1. task_technical (0.27)
> 2. pat_D 더미 (0.17)
> 3. **agent_count × max_messages (0.16)** ← 핵심 상호작용
>
> 결론: **토폴로지만으로 54% 분산 설명**. 나머지 46%는 과제 내용 복잡도 (정직한 경계).
> 실용 가치: max_turns 설정 전에 토큰 예산 추정 가능."

**핵심 메시지**: 알고리즘 contribution. 토폴로지 = 절반 이상 설명.

---

## 11. ⭐ Finding 6 — 난이도가 패턴을 압도 (75초)

> "여섯 번째 — **과제 난이도가 패턴 선택보다 9.3배 중요**.
>
> Kruskal-Wallis:
> - 난이도 main effect: **η²=0.363 (large)**
> - 패턴 main effect: η²=0.039 (작음)
>
> 난이도별 최적 (Haiku 4.5):
> - **Easy**: Solo 4.73 > Refl-2 4.67
> - **Medium**: Refl-2 3.93 > Swm-3 3.80
> - **Hard**: Solo 3.67 > Sel-3=Refl-2 3.47
>
> Cohen's d (Refl-2 vs Solo @ medium): Haiku **d=1.26**, GPT-5.4 **d=1.83**.
> => **모델 능력 frontier 부근에서만 멀티에이전트 정당화됨**.
> 약한 모델에 medium 난이도 → 멀티에이전트로 보강. 그 외엔 Solo가 비용효율 압도."

**핵심 메시지**: 추천 매트릭스. 5 LLM 검증. 실무 직접 적용 가능.

---

## 12. ΔU Diagnostic Framework (45초)

> "ΔU 수식의 진짜 가치는 종료 알고리즘이 아니라 **진단 렌즈**입니다.
>
> ΔU(t) = ΔQ(t) − λ·ΔC(t)
>
> 모든 패턴 1.1~2.4턴 안에 saturate. λ를 0.0~0.5로 바꿔도 0.1턴 차이만.
> = **품질 saturation은 패턴마다 다른 속도로 일어나지만, 일어난다는 사실 자체는 보편적**.
>
> 하이브리드 전략: 키워드 + B2 패턴만 ΔU 보강."

**핵심 메시지**: 수식의 의미. 진단 도구.

---

## 13. Engineering Stack (45초)

> "스택:
> - **Python 3.13** · **AutoGen** (agentchat, ext) · anthropic + openai SDKs
> - **sentence-transformers** (Sentence-BERT, Exp03 의미 수렴)
> - **scipy** (Kruskal-Wallis, Mann-Whitney U), Cohen's d, 5-fold CV
> - **5 LLMs**: Haiku 4.5 / Sonnet 4.5 / GPT-4o-mini / Gemini / GPT-5.4
> - matplotlib (9 figure 자동 생성)
>
> 모든 코드 + 데이터 + 분석 스크립트 공개 예정."

**핵심 메시지**: 재현 가능. 학술 표준.

---

## 14. Conclusions + What I Built (45초)

> "**7 contributions**:
> 1. Cross-topology termination 첫 통합 연구
> 2. Termination regret 메트릭
> 3. Claim-level 의미 수렴 탐지
> 4. 패턴별 오류 분류
> 5. ΔU 진단 프레임워크 (negative + positive 동시)
> 6. 비용 예측 모델 (R²=0.54)
> 7. 난이도-패턴 추천 매트릭스
>
> 핵심 message:
> > **'Termination strategy should be a first-class design decision.'**
> > **'종료 전략은 일급 설계 결정이어야 한다.'**
>
> 13 pattern 구현 + 7 experiment runner + 분석 스크립트 오픈소스 공개.
> 감사합니다. 질문 받겠습니다."

**핵심 메시지**: 7개 명확한 기여. 실용 + 학술 동시.

---

## 발표 시간별 단축본

### 5분 버전 (면접 라이트닝)
- 1 Hero / 2 Problem / 6 Cost Inversion / 8 B1/B2 / 11 Difficulty / 14 Conclusions

### 10분 버전 (기술 인터뷰)
- 1, 2, 4, 5, 6, 8, 9 Keyword Optimal, 10 Cost Prediction, 11, 14

### 15분 버전 (전체)
- 14장 모두

---

## 청중별 강조 포인트

- **AI/ML 엔지니어 면접**: 6, 8, 9, 10, 13 (effect size, RF, 통계)
- **교수/학회 (COLM)**: 3, 4, 9, 11, 12 (gap, taxonomy, negative result, ΔU)
- **PM / 투자자**: 2, 6, 11, 14 (스토리, 추천 매트릭스, 가치)

---

## 자주 받는 질문 4개

**Q1. 왜 14 패턴? 더 많이 했어야 하지 않나?**
→ "Masterman 2025 Chain/Star/Mesh 토폴로지 논문에 근거. 6 카테고리 × 평균 2-3 변형 = 14. 더 많으면 통계 분산 폭증 (과제당 3 rep × 25 task → 패턴당 75 runs). 5 LLM으로 교차검증해서 Spearman ρ=0.900 확보."

**Q2. κ=0.244 (인간 평가 일치도 약함). 어떻게 정당화?**
→ "정직한 한계로 명시했음. n=1 평가자 한계. G-Eval (Sonnet 4.5)로 LLM-as-Judge 채점이 main, 인간 평가는 spot-check 30 샘플만. 향후 작업 P1 (TODO에 명시)."

**Q3. Solo 결과 이상하지 않나? 정말 단일 에이전트가 항상 최고?**
→ "비용효율 차원에서만. 절대 품질에선 medium 난이도 + 약한 모델 (Haiku) 조합에서 Refl-2가 d=1.26로 의미 차이 큼. 결론은 'capability frontier 부근에서만 멀티 정당화', Solo가 default."

**Q4. AutoGen만? LangGraph/CrewAI는?**
→ "정직한 한계. 단일 프레임워크 한정. 단 AutoGen Studio가 토폴로지 가장 많이 지원 (selector, swarm, debate, pipeline). LangGraph는 그래프 기반이라 정의 자체가 달라서 직접 비교 어려움. Future work."

---

## 데크 위치

NotebookLM → 새 노트북 "Multi-Agent Termination Dynamics Across Coordination Topologies" → Studio → "When Should AI Teams Stop" 슬라이드 클릭 → Expand → 14장 thumbnail navigation.

PPTX export: 우상단 ⋯ → "Download as PowerPoint".
