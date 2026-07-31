# Multi-Agent Termination Study

**"When Should Multi-Agent Teams Stop?"**
14가지 협력 토폴로지의 종료 역학 체계적 연구 | 2,000회+ 실험

**Target**: COLM 2026 (Abstract 3/26, Paper 3/31)

---

## 핵심 발견

| # | 발견 | 근거 | 강도 |
|---|------|------|------|
| 1 | **비용 위계 뒤집힘**: Swm-3(3명) < RR-2(2명) | Exp01, 980회 | 신규 |
| 2 | **Debate 품질 하락**: 턴↑ → 3.8→3.3 | Exp02, 276턴 점수 | 신규 (Du et al. 반론) |
| 3 | B1/B2 스케일링 정량 확인: 1.48배 vs 3.17배 | Exp01 | 기존 분류 확인 |
| 4 | 키워드 종료 7/8 최적, Swm만 ΔU 필요 | Exp05, 800회 | negative result |
| 5 | **비용 예측**: agents×maxmsg → R²=0.54 | Exp06, 718회 학습 | 알고리즘 contribution |
| 6 | **역U자**: Solo(Easy/Hard), Refl-2(Medium만) | Exp07, 220회 | 신규 (H2, H3 기각) |
| 7 | **Solo 비용효율 지배**: 전 난이도 최고 | Exp07 | 실용 가이드 |

---

## 14개 패턴 (6범주)

```
S  Baseline     solo(1)
A  순차 체인     rr2(2) rr3(3) rr4(4)        Chain (Masterman 2025)
B1 중앙 라우팅   sel3(3) sel4(4)              Star (Masterman 2025)
B2 분산 핸드오프  swm3(3) swm4(4)             Mesh (Masterman 2025)
C  피드백       refl2(2) refl3(3)            Reflexion (Shinn, NeurIPS 2024)
               debate3(3) debate4(4)         Debate (Du, ICML 2024)
D  복합         pipe(5) moa(4)              Pipeline / MoA (Li, ICLR 2025)
```

학술적 근거: Masterman et al. (2025) 3대 토폴로지 + Tran et al. (2025) centralized/distributed 분리

---

## 7개 실험

| 실험 | 목적 | 실행 | 데이터 |
|------|------|------|--------|
| **Exp01** | 패턴별 비용(토큰/시간/턴) 비교 | v1: 780회 (13패턴×20과제×3반복), v2: 200회 (8패턴×25과제) | `results/exp01/` |
| **Exp02** | 턴별 G-Eval 품질 궤적 + 종료 후회 | 100회, 276턴 점수 | `results/exp02/` |
| **Exp03** | 의미 수렴 탐지 (Sentence-BERT) | Exp01/02 데이터 재분석 | `results/exp03/` |
| **Exp04** | 종료 실패 유형 분류 | Exp01 데이터 재분석 | `results/exp04/` |
| **Exp05** | ΔU(t) 적응적 종료 통제실험 | baseline 200 + adaptive 600 = 800회 | `results/exp05/` |
| **Exp06** | 비용 예측 회귀 모델 | Exp01 데이터 학습, 5-fold CV | `results/exp06/` |
| **Exp07** | 난이도별 최적 패턴 실험 | 220회 (5패턴×15과제×3반복) | `results/exp07/` |

**모델**: Claude Haiku 4.5 (에이전트), Claude Sonnet 4.5 (G-Eval), GPT-4o-mini (교차 검증 125회)
**과제**: 25개 × 9도메인 (과학/CS/역사/철학/법정치/게임/공학/경영/의학) × 4유형 (사실/분석/기술/창의)
**난이도 과제**: 15개 × 5도메인 × 3난이도(Easy/Medium/Hard)

---

## 실험별 주요 결과

### Exp01: 비용 랭킹
```
Solo(1,287) < Swm3(4,196) < RR2(4,759) < Refl2(5,237) < Sel3(7,851)
< Deb3(9,313) < RR3(10,121) < Sel4(11,621) < Deb4(11,637)
< Swm4(13,321) < Pipe(13,856) < RR4(17,671) < MoA(22,333)
= 17.4배 격차
```
- 에이전트 수 증가 스케일링: A(기하급수), B1(1.48배 준선형), B2(3.17배 초선형), C-반성(2.31배), C-토론(1.25배)
- Kruskal-Wallis turn_count: H=118.341, p<0.001

### Exp02: 품질 궤적
```
3가지 궤적 유형:
  고원형(RR-3):  3.9 → 4.5 → 4.1   후회 2.6턴, 손실 0.05
  정점형(Refl-2): 3.9 → 4.8 → 4.0   후회 0.6턴, 손실 0.00
  하락형(Debate-3): 3.8 → 3.4 → 3.3   후회 2.0턴, 손실 0.65
```
- 품질 히트맵 (패턴 × 과제유형): 기술형에서 refl2=5.0 vs sel3=2.2 (2.3배 격차)
- 사실형: 패턴 간 차이 작음 / 기술형: 격차 극대화

### Exp03: 의미 수렴
```
수렴율: pipe(32%) > B1(26%) > A(16%) > B2(12%) > C(0%)
```
- Debate-3 cosine 0.673 (최고)인데 수렴 0% → 매 턴 새 논점 생성 → 의미 수렴 종료 불가

### Exp04: 종료 실패
```
3가지 실패 유형:
  토큰 폭발: A(RR-4) 72%   — context 초과
  턴 폭발:  B2(Swm-4) 76%  — 핸드오프 순환
  키워드 실종: D(MoA) 100%  — TERMINATE 미출력
  무실패:   B1, C          — 0%
```
- 과제별: 사실형 0%, 기술형 RR-2=33%→RR-3=53%→RR-4=100%

### Exp05: ΔU 적응적 종료
```
ΔU(t) = ΔQ(t) − λ·ΔC(t)
모든 패턴 1.1~2.4턴 수렴, λ=0.0~0.5 변경해도 0.1턴 차이뿐

통제실험 (키워드 대체):
  Swm-4:  −70% 절감 (유일한 성공)
  RR-3:   +32%
  Sel-3:  +63%
  Refl-2: +258%
→ 7/8 패턴에서 TERMINATE 키워드가 이미 최적
```

### Exp06: 비용 예측
```
Random Forest R² = 0.54 (5-fold CV, total_tokens)
Top features: task_technical(0.27) > pat_D(0.17) > agents×maxmsg(0.16)
Holdout (→Exp05): R²=0.29 (task suite 다르면 재보정 필요)
→ 토폴로지만으로 54% 설명, 나머지 46%는 과제 내용 복잡도
```

### Exp07: 난이도 × 패턴 상호작용
```
난이도 주효과: H=55.95, p<0.000001 ★★★
패턴 주효과: H=8.24, p=0.083 (유의하지 않음)

난이도별 최적 패턴:
  Easy:   Solo(4.73) > Refl-2(4.67) > Debate-3(4.40)   gap=0.92
  Medium: Refl-2(3.93) > Swm-3(3.80) > Debate-3(3.67)  gap=0.67
  Hard:   Solo(3.67) > Sel-3=Refl-2(3.47) > Debate-3(2.93)  gap=0.73

→ 역U자 관계: 멀티에이전트는 Medium에서만 효과적
→ Solo가 비용효율 전 난이도 지배
→ Debate-3 품질 하락 최대 (4.40→2.93, Δ=−1.47)
```

### 교차 모델 검증
- GPT-4o-mini 5패턴 × 25과제 = 125회
- Spearman ρ=0.900 (p=0.037) — 비용 순서 보존됨
- 한계: n=5만 비교

---

## 패턴별 종료 행동

| 패턴 | 평균 턴 | 종료 키워드 | max_msg | 키워드 성공률 | 오류율 |
|------|--------|-----------|---------|------------|-------|
| Solo | 2.0 | TERMINATE | 5 | 100% | 0% |
| RR-2 | ~3 | TERMINATE | 10 | 높음 | 8% |
| RR-3 | 4.6 | TERMINATE | 10 | 높음 | 23% |
| RR-4 | ~6 | TERMINATE | 12 | 낮음 | 72% |
| Sel-3 | 3.7 | TERMINATE | 10 | 100% | 0% |
| Sel-4 | 4.2 | TERMINATE | 12 | 100% | 0% |
| Swm-3 | 8.8 | TERMINATE | 10 | 1~6% | 11% |
| Swm-4 | 26.1 | TERMINATE | 12 | 28% | 76% |
| Refl-2 | 3.2 | APPROVED | 8 | 100% | 0% |
| Debate-3 | 4.6 | VERDICT | 10 | 100% | 0% |
| Pipe | 6.0 | ANALYSIS_DONE→TERMINATE | 14 | 100% | 0% |
| MoA | ~8 | (없음) | 11 | 0% | 100% |

---

## 프로젝트 구조

```
AG-Research/
├── config.py                    # 14패턴 정의, 모델 설정, 경로
├── run_experiment.py            # CLI 진입점 (--exp, --category, --model, --dry-run)
├── experiment_utils.py          # TeamFactory, ExperimentRunner, RunResult
├── task_suite.json              # 25과제 × 9도메인 × 4유형
│
├── exp01_pattern_efficiency/    # Exp01: 비용 비교
│   ├── runner.py
│   └── analyze.py
├── exp02_termination_quality/   # Exp02: 품질 궤적
│   ├── runner.py
│   ├── scorer.py                # G-Eval LLM-as-Judge
│   └── analyze.py
├── exp03_convergence_detection/ # Exp03: 의미 수렴
│   ├── embeddings.py            # Sentence-BERT
│   └── analyze.py
├── exp04_error_attribution/     # Exp04: 종료 실패 분류
│   ├── classifier.py            # ErrorType enum (7종)
│   └── analyze.py
├── exp05_adaptive_termination/  # Exp05: ΔU 종료
│   ├── runner.py
│   ├── adaptive_condition.py    # ΔU(t) = ΔQ(t) − λ·ΔC(t)
│   └── analyze.py
├── exp06_cost_prediction/       # Exp06: 비용 예측 회귀
│   └── analyze.py               # RF, Ridge, Lasso, Linear
├── exp07_difficulty/             # Exp07: 난이도 × 패턴
│   ├── runner.py
│   ├── scorer.py                # G-Eval 난이도 과제 채점
│   └── analyze.py               # Kruskal-Wallis + heatmap + recommendation
│
├── results/
│   ├── exp01/                   # raw.json, summary_all.csv, stats.md, plots/
│   ├── exp01_v1/                # 레거시 780회 데이터
│   ├── exp02/                   # scores.csv (276턴), human_eval, cross_validation
│   ├── exp03/                   # convergence_semantic.csv, plots/
│   ├── exp04/                   # classified_errors.csv, error_report.md, plots/
│   ├── exp05/                   # exp05_analysis.csv, adaptive_stats.json
│   ├── exp05_v1/                # 이전 버전
│   ├── exp06/                   # cost_prediction_results.csv, feature_importance.csv
│   └── exp07/                   # scores.csv, anova_results.csv, recommendation_matrix.csv
│
├── figures/                     # 시각화 생성 스크립트 (9개)
│   ├── fig1_taxonomy.py         # 패턴 분류 트리
│   ├── fig4_exp01_main.py       # 비용 4-panel
│   ├── fig5_quality_trajectories.py  # 품질 궤적
│   ├── fig8_pareto.py           # Pareto frontier
│   └── ...
│
├── latex/                       # COLM 2026 논문
│   ├── main.tex                 # 9페이지 본문
│   ├── references.bib           # 23 citations
│   └── *.png                    # 논문 삽입 그림
│
├── 분석 스크립트 (루트)
│   ├── compute_ci.py            # 신뢰구간 계산
│   ├── compute_marginal_utility.py  # ΔU 계산
│   ├── analyze_convergence_semantic.py  # Sentence-BERT 수렴
│   ├── analyze_errors.py        # 오류 분류
│   ├── analyze_domain_pattern.py # 도메인 × 패턴
│   ├── analyze_exp05.py         # 적응적 종료 분석
│   ├── analyze_human_eval.py    # 인간 평가 κ 계산
│   ├── cross_validate_scoring.py # G-Eval 교차 검증
│   ├── export_human_eval_kit.py # 30샘플 추출
│   └── validate_results.py      # 데이터 무결성 검증
│
├── 문서
│   ├── paper_draft.md           # 영문 초안 (104KB)
│   ├── paper_draft_kr.md        # 한글 초안 (102KB)
│   ├── notebooklm_source_kr.md  # NotebookLM 소스 (67KB)
│   ├── NOTEBOOKLM_PROMPTS.md    # PPT 생성 프롬프트 (15장)
│   ├── COLM_2026_PLAN.md        # 제출 타임라인
│   ├── COLM_PPT_OUTLINE.md      # PPT 구조
│   ├── TODO.md                  # 남은 작업
│   ├── HANDOFF.md               # 세션 인수인계
│   ├── VENUE_ANALYSIS.md        # 학회 분석
│   ├── paper_strengthening_plan.md  # 보강 계획
│   ├── literature_review_2025-2026.md  # 문헌 조사
│   ├── memo.md                  # 교수님 피드백
│   └── ...
│
└── presentation_kr.pptx         # 생성된 PPT (레거시)
```

---

## 실행 방법

### 실험 실행
```bash
cd D:/Data/25_ACE/AG/AG-Research

# 단일 실험
C:/Python313/python run_experiment.py --exp 01

# 특정 패턴만
C:/Python313/python run_experiment.py --exp 01 --pattern rr2 rr3

# 카테고리별
C:/Python313/python run_experiment.py --exp 01 --category A

# 모델 오버라이드
C:/Python313/python run_experiment.py --exp 01 --model gpt-4o-mini

# 드라이런 (1과제 × 1패턴)
C:/Python313/python run_experiment.py --exp 01 --dry-run

# 전체
C:/Python313/python run_experiment.py --all
```

### 분석
```bash
C:/Python313/python run_analysis.py              # 전체 분석
C:/Python313/python compute_ci.py                # 신뢰구간
C:/Python313/python analyze_convergence_semantic.py  # Sentence-BERT 수렴
C:/Python313/python analyze_errors.py            # 오류 분류
C:/Python313/python analyze_exp05.py             # ΔU 분석
```

### 시각화
```bash
cd figures
C:/Python313/python fig4_exp01_main.py           # 비용 4-panel
C:/Python313/python fig5_quality_trajectories.py # 품질 궤적
C:/Python313/python fig8_pareto.py               # Pareto frontier
```

---

## 환경

- **Python**: 3.13 (`C:/Python313/python`)
- **의존성**: autogen-agentchat, autogen-ext, anthropic, openai, sentence-transformers, scipy, matplotlib
- **API 키**: ANTHROPIC_API_KEY (Claude), OPENAI_API_KEY (GPT 교차 검증)
- **모델**: claude-haiku-4-5-20251001 (에이전트), claude-sonnet-4-5-20250929 (G-Eval)

---

## 실제 보유 데이터 vs 미보유

### 실험으로 확보된 데이터
| 데이터 | 출처 | 파일 |
|--------|------|------|
| 14패턴 비용(토큰/시간/턴) | Exp01 | `results/exp01/summary_all.csv` |
| 5패턴 × 4유형 품질(G-Eval) | Exp02 | `results/exp02/scores.csv` |
| 패턴별 평균 턴 수 | Exp01 | `results/exp01/raw.json` |
| 수렴율 (Sentence-BERT) | Exp03 | `results/exp03/convergence_semantic.csv` |
| 오류율 + 실패 유형 | Exp04 | `results/exp04/classified_errors.csv` |
| ΔU 적응적 종료 전/후 | Exp05 | `results/exp05/exp05_analysis.csv` |
| 교차 모델 (GPT 5패턴) | Exp01 변형 | `results/exp02/cross_validation_summary.csv` |
| 도메인별 비용 (9도메인×8패턴) | Exp01 v2 | `results/exp01/domain_analysis.csv` |

### 미보유 데이터 (추가 실험 필요)
| 데이터 | 필요 이유 | 상태 |
|--------|---------|------|
| 교차 모델 전체 (13패턴 GPT) | n=5 약함 | TODO (P1) |
| 하이브리드 종료 (키워드+ΔU) | 제안만, 미검증 | TODO |
| ~~과제 난이도별 패턴 성능~~ | ~~실용 가이드라인~~ | **DONE** (Exp07, 220회) |
| ~~비용 예측 모델~~ | ~~알고리즘 contribution~~ | **DONE** (Exp06, R²=0.54) |

---

## 한계점

1. **κ=0.244** — 인간 평가자 1명, 일치도 약함
2. **단일 프레임워크** (AutoGen) — LangGraph, CrewAI 미검증
3. **2~5명 팀만** — 대규모 팀 미검증
4. **교차 모델 n=5** — Spearman ρ=0.900이지만 표본 부족
5. **하이브리드 종료 미검증** — 제안만 하고 실험 안 함
6. ~~과제 난이도 축 없음~~ → **Exp07에서 해결** (Easy/Med/Hard 3단계, 220회)

---

## 논문 관련 파일

| 용도 | 파일 |
|------|------|
| 영문 초안 | `paper_draft.md` |
| 한글 초안 | `paper_draft_kr.md` |
| LaTeX 본문 | `latex/main.tex` |
| 참고문헌 | `latex/references.bib` (23편) |
| NotebookLM 소스 | `notebooklm_source_kr.md` |
| PPT 프롬프트 | `NOTEBOOKLM_PROMPTS.md` (15장) |
| PPT 구조 | `COLM_PPT_OUTLINE.md` |
| 제출 계획 | `COLM_2026_PLAN.md` |
| 남은 작업 | `TODO.md` |
