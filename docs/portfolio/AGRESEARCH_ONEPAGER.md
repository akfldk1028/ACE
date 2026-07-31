# Multi-Agent Termination Dynamics — One-Page Portfolio

**When Should Multi-Agent LLM Teams Stop?** First systematic study across 14 coordination topologies. COLM 2026 target.

---

## Numbers

```
┌───────────┬───────────┬───────────┬───────────┬───────────┐
│   14      │  2,200+   │    7      │    5      │   669     │
│ patterns  │   runs    │experiments│   LLMs    │ scored    │
│ 6 categs  │ unified   │ Exp01-07  │  tested   │ runs (E7) │
└───────────┴───────────┴───────────┴───────────┴───────────┘
```

---

## Pattern Taxonomy (6 Categories)

```
S   Baseline       solo (1 agent)
A   Sequential     rr-2  rr-3  rr-4         Chain      (Masterman 2025)
B1  Centralized    sel-3 sel-4              Star       (router picks speaker)
B2  Decentralized  swm-3 swm-4              Mesh       (peer handoff)
C   Feedback       refl-2 refl-3            Reflexion  (Shinn NeurIPS 2024)
                   debate-3 debate-4         Debate     (Du ICML 2024)
D   Composed       pipe (5)  moa (4)        Pipeline / MoA  (Li ICLR 2025)
```

---

## Cost Hierarchy (Exp01, mean tokens/run)

```
Solo (1,287) < Swm-3 (3,203) < RR-2 (4,759) < Refl-2 (5,237) < Sel-3 (7,851)
< Deb-3 (9,313) < RR-3 (10,121) < Sel-4 (11,621) < Deb-4 (11,637)
< Swm-4 (13,321) < Pipe (13,856) < RR-4 (17,671) < MoA (22,333)
                                                              17.4× gap
```

**New hierarchy** (B1/B2 split): `A ≈ B2 < B1 ≈ C ≪ D`

---

## 7 Findings — Effect-Size Calibrated

| # | Finding | Statistic | Why it matters |
|---|---|---|---|
| 1 | **Cost inversion**: Swm-3 (3 agents) < RR-2 (2 agents) | U=95, p<0.001 | More agents can cost less — communication pattern matters |
| 2 | **Debate quality decline**: 3.8 → 3.4 → 3.3 monotonic | G-Eval (Sonnet 4.5) | Du et al. ICML 2024 contradicted on this point |
| 3 | **B1 vs B2 split**: 1.48× sub-linear vs 3.17× super-linear scaling | Exp01 980 runs | "Dynamic routing" decomposes into 2 distinct regimes |
| 4 | **Keyword TERMINATE optimal for 7/8** | 800-run controlled exp | ΔU adaptive only wins on Swm-4 (−70%); +258% on Refl-2. Negative result with practical value |
| 5 | **Cost predictable from topology**: R²=0.54 | RF, 5-fold CV | `agent_count × max_messages` is strongest predictor. 46% remains task-content |
| 6 | **Difficulty dominates pattern**: η²=0.363 vs 0.039 | Kruskal-Wallis | 9.3× larger effect. Solo dominates cost-efficiency at all difficulties |
| 7 | **Capability moderation**: Refl-2 helps Haiku@medium d=1.26, GPT-5.4 d=1.83 | Cohen's d (5 LLMs) | Multi-agent only justified near model's capability frontier |

---

## ΔU Diagnostic Framework

```
ΔU(t) = ΔQ(t) − λ·ΔC(t)

Saturates within 1.1–2.4 turns across all patterns.
λ-insensitive (0.0 → 0.5 yields ≤0.1 turn difference).

Use as diagnostic, NOT replacement. Hybrid: keyword + ΔU only for B2 (handoff).
```

---

## Why this matters (interview answer)

> Multi-agent LLM systems are exploding (AutoGen, CrewAI, LangGraph), yet **no one studied when they should stop** in a unified way. We did. The findings are counterintuitive: simple beats sophisticated for 7/8 patterns, more agents can cost less, debate quality declines, and Solo dominates whenever the task isn't at the model's capability frontier. Practitioners now have an evidence-based recommendation matrix instead of guessing max_turns.

---

## Stack & Reproducibility

**Engineering**: Python 3.13 · AutoGen (autogen-agentchat, autogen-ext) · anthropic + openai SDKs · sentence-transformers (Sentence-BERT for Exp03) · scipy · matplotlib

**Statistics**: Kruskal-Wallis · Mann-Whitney U · Cohen's d · 5-fold CV · Spearman ρ=0.900 cross-model

**Models tested**: Claude Haiku 4.5 (agent) · Claude Sonnet 4.5 (G-Eval judge) · GPT-4o-mini (cross-validation, n=125) · Gemini · GPT-5.4

**Released**: 13 pattern implementations · 7 experiment runners · analysis scripts · 9 figure generators
