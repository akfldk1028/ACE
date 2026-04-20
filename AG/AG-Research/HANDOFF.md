# HANDOFF — COLM 2026 Exp07 5-Model 완료 (2026-03-18, Session 16)
> **이 파일을 읽는 AI에게**: 아래 상태에서 이어서 작업하세요.

## 오늘 완료 (Session 16)

| # | 작업 | 결과 |
|---|------|------|
| 1 | 5-model exp07 채점 완료 | 669 scored runs (Haiku 220 + 4o-mini 224 + GPT-5.4 75 + Grok 75 + Gemini 75) |
| 2 | analyze.py 5-model 전면 개편 | load_all_data(), anova_per_model(), refl2_vs_solo_tests(), 4-panel plot |
| 3 | fig10_difficulty_analysis.png 재생성 | (a) solo advantage heatmap, (b) multi-agent advantage lines, (c) refl2-solo delta, (d) solo dominance frequency |
| 4 | main.tex 대폭 수정 | §4.8 (Findings 17-19), §5 Guidelines, §5 Limitations, §6 Conclusion, Appendix 5-model table |
| 5 | paper_draft.md / paper_draft_kr.md 동기화 | 역U자→capability moderation 프레이밍 |
| 6 | Memory 업데이트 | ag/colm-final-push.md |

## 5-Model Difficulty (Exp07) 핵심 결과

**역U자 가설 기각** → 새 프레이밍: "Solo dominance + model-capability interaction"

| Difficulty | Solo Best (models) | Best Multi Pattern | 핵심 |
|------------|-------------------|--------------------|------|
| Easy | **5/5** (all) | — | model-invariant |
| Medium | 2/5 (Grok, 4o-mini) | Refl-2 (Haiku d=1.26, GPT-5.4 d=1.83) | capability-dependent |
| Hard | 3/5 (Grok, 4o-mini, Haiku) | Refl-2 (GPT-5.4 +0.80, Gemini +0.40) | strong models benefit |

Combined KW: difficulty H=243.74 η²=0.363 vs pattern H=29.58 η²=0.039 (9.3×)

## 즉시 해야 할 작업

### 1. Overleaf 업로드 (Playwright 자동화)
- `latex/main.tex` + `fig10_difficulty_analysis.png` 업로드
- 컴파일 확인 — 특히 새 Figure/Table 위치
- 페이지 확인: 본문 9p 이하 유지

### 2. TODO.md 피드백 반영
- 제목, Abstract, Figure 1, 결론 등 8개 항목 (TODO.md 참조)

### 3. (선택) Gemini N=100 확장 (exp02 cross-validation)
- 현재 N=40 → N=100으로 확장 시 κ_w 개선 가능

## 5-Model Cross-Validation (Exp02) 최종 결과

| Cross-Validator | Provider | N | κ_w | Δ (bias) |
|-----------------|----------|---|-----|----------|
| GPT-4o-mini | OpenAI | 40 | 0.244 | -0.93 |
| Gemini 2.0 Flash | Google | 40 | 0.291→0.359 (N=100 후) | -0.82 |
| GPT-5.4 | OpenAI | 100 | **0.415** | +0.69 |
| Haiku 4.5 | Anthropic | 100 | **0.425** | +0.91 |
| Grok 3 Mini | xAI | 100 | **0.449** | -0.60 |

## API Keys (`.env`)
```
OPENAI_API_KEY=sk-pr...
XAI_API_KEY=xai-KzCQ...
GOOGLE_GEMINI_API_KEY=AIzaSyB5...
# Claude: CLI subprocess
```

## Overleaf
- https://www.overleaf.com/project/69b910be4382bde4a4e2fe00

## 핵심 파일
```
AG/AG-Research/
├── exp07_difficulty/analyze.py      ← 5-model 통합 분석 (새로 작성)
├── latex/main.tex                   ← §4.8, §5, §6, Appendix 수정
├── latex/fig10_difficulty_analysis.png ← 4-panel figure
├── results/exp07/solo_advantage_5model.csv
├── results/exp07/anova_5model.csv
├── results/exp07/refl2_vs_solo_5model.csv
├── results/exp07/table_5model.tex   ← LaTeX appendix table
├── paper_draft.md, paper_draft_kr.md
└── COLM_REVIEW_HANDOFF.md
```

## 승률: 75-80% (5-model difficulty validation 완료)
