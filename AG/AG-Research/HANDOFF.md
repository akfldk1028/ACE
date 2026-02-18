# AG-Research Handoff Document
> Last updated: 2026-02-17, session 13
> For the next Claude Code session to continue seamlessly.

## What Is This Project?

Multi-Agent Termination Study - a research paper with real experiments.
- **Paper**: `paper_draft.md` (English) + `paper_draft_kr.md` (Korean)
- **Summary**: `paper_summary.md` (presentation brief for professor)
- **13 patterns** across 5 categories (A=Chain, B1=Star, B2=Mesh, C=Feedback, D=Composed)
- **5 experiments**: exp01(efficiency), exp02(quality), exp03(convergence), exp04(errors), exp05(adaptive)
- **Target venue**: COLM 2026 (abstract 3/26, full 3/31)

## Session 13 Changes (2026-02-17)

### Completed in session 13 (consistency fixes + LaTeX conversion):
1. **Abstract run count FIXED (EN+KR)** → "over 1,480 runs" → "over 1,880 runs" (780 v1 + 200 v2 + 100 exp02 + 800 exp05)
2. **Guideline 4 keyword rate FIXED (EN+KR)** → swm4 "24%" → "28%" to match Table 20 (28.3%).
3. **EN/KR cross-validation** → 9 discrepancies found and fixed:
   - KR missing: Table 6, Table 9, sel4 in Table 20, 2 rows in Table 1, 6 references
   - KR labels: "Finding 21-23" → "발견", "Table 13/14" → "표", 12c rounding (8758→8759)
4. **Tran et al. arXiv ID FIXED (EN+KR)** → 2502.11078 (wrong paper!) → 2501.06322 (correct)
5. **COLM 2026 format checked** → 9-page main text, unlimited refs+appendix, LaTeX template required
6. **LaTeX conversion DONE** → `latex/main.tex` (1005 lines) + `latex/references.bib` (160 lines, 23 refs)
   - Main text: 6 tables + 4 figures (9 pages target)
   - Appendix: 20+ tables moved from main text
   - Template: COLM 2026 official (colm2026_conference.sty)
   - Double-blind: Anonymous authors
   - Needs: pdflatex compilation (no TeX installed on this machine → use Overleaf)

## Session 12 Changes (2026-02-16)

### Completed in sessions 12-13 (Table 15 + exp05 completion + consistency):
1. **Table 15 FIXED (EN+KR)** → All 9×8 domain×pattern values recomputed from summary.csv. Many cells were wrong (e.g., pipe history 18.9→8.9, medicine 10.1→29.6, refl2 philosophy 5.4→2.8).
2. **Table 16 VERIFIED** → Mean-of-domain-means approach confirmed correct. No changes needed (CVs match exactly).
3. **Finding 24 FIXED (EN+KR)** → swm3 example: "1,600 history / 7,900 medicine" → "1,400 history / 9,200 business"
4. **Finding 25 FIXED (EN+KR)** → refl2: "most efficient (4,600 law, 5,400 phil)" → "among most efficient (4,800 law, 2,800 phil)". Factual domain mean 5,400→4,200.
5. **Finding 26 VERIFIED** → Domain ranking unchanged, ratio still 1.88×.
6. **exp05 v2 COMPLETE** → 800/800 runs, 0% errors. All 8 patterns done. `results/exp05/summary.csv`.
7. **exp05 analysis COMPLETE** → `analyze_exp05.py` run with 800 data. Key: swm4 -65%/-70%, λ≥0.1 avg -13%.
8. **Tables 17-18 UPDATED (EN+KR)** → Table 17 expanded to 8 rows, Table 18 N=200 with new percentages.
9. **Findings 27-29 REWRITTEN (EN+KR)** → New narrative: topology-dependent benefit, swm4 validates ΔU where keyword fails.
10. **Conclusion point 5 UPDATED (EN+KR)** → 800 runs, topology-dependent benefit, 70% savings, 13% average.
11. **fig8_pareto.py REGENERATED** → Full 800-run data.
12. **figures/README.md UPDATED** → 5-category taxonomy (was still 4-category).
13. **Sections 4.3/4.4 VERIFIED** → Both have real data, no placeholders.
14. **HANDOFF.md UPDATED** → This file.

## Session 11 Changes (2026-02-15–16)

### Completed in session 11 (COLM audit + consistency fixes):
1. **Professor feedback 4/4 VERIFIED** → All reflected in EN+KR papers.
2. **EN B1/B2 justification ADDED** → Blockquote with Tran et al. (2025) citation after Cat B2 definition.
3. **Table 14 SYNCED** → λ sensitivity table added to EN paper (was KR-only).
4. **exp04 analyze_errors.py RE-RUN** → v2 data confirmed matching Section 4.4.
5. **Figures REGENERATED** → fig4 (v2 200 runs), fig8 (exp05 400 runs), exp04 plots (3 PNGs).
6. **Table 17/18 Δ% ALL FIXED (EN+KR)** → All percentage values were wrong. Recomputed from summary.csv.
7. **Table 11b swm3 FIXED (EN+KR)** → Sub-dimensions (3.50,3.35,3.70,3.75) → (4.25,3.80,4.45,4.35).
8. **Table 8 pipe FIXED (EN+KR)** → tok_in 4587→4275, tok_out 9269→9581, turns 5.0→6.0.
9. **Finding 12 FIXED** → pipe output share 67%→69%.
10. **Finding 27/28 FIXED (EN+KR)** → Updated to match corrected Table 17/18.
11. **Conclusion point 5 FIXED** → 59-531% → 32-258%.
12. **Table 12 → 12d RENAMED** → Fixed numbering collision (two tables both called "Table 12").
13. **References COMPLETE** → Added Masterman, MoA/Li, Du, Hong/MetaGPT, Zheng, Tran. Completed 3 incomplete entries. Alphabetized.
14. **Human eval note UPDATED** → Submission-ready language (was "will be reported upon completion").
15. **exp03 UPGRADED** → Jaccard → Sentence-BERT (all-MiniLM-L6-v2). Key inversion: pipe(32%)>B1(26%)>A(16%)>B2(12%)>C(0%).
16. **Cross-validation DONE** → GPT-4o-mini scoring (40 samples). Pearson r=0.43-0.62. Leniency bias confirmed.

## Session 10 Changes (2026-02-14)

### Completed in session 10 (consistency audit):
1. **Guideline 4 FIXED** → Both EN + KR now say "Use ΔU as complement to keyword termination, not replacement" (was "Prefer adaptive over fixed"). Reflects exp05 Finding 27.
2. **Abstract UPDATED** → Both EN + KR: added 5th contribution (keyword effective, hybrid strategy). Run count fixed 1,760→1,480.
3. **Conclusion UPDATED** → Both EN + KR: added 5th point about keyword effectiveness + hybrid approach.
4. **EN Section 3.2 FIXED** → Updated from old 20-task suite to 25-task v2 with 9 domains (was still describing v1).
5. **exp02 run count FIXED** → Both EN + KR: Section 3.4 changed 260→100 runs.
6. **exp05 run count FIXED** → Both EN + KR: Section 3.4 changed 200→400 runs with accurate description.
7. **EN Table 13 FIXED** → Q values now match Table 10 (was using wrong values). Columns aligned with KR version.
8. **EN Appendix A summary FIXED** → factual(6→7), technical(4→3).
9. **KR pipe agent turns FIXED** → 5.0→4.0 (was copying turns instead of agent turns).
10. **KR rr3 Regret FIXED** → Table 13: 2.5→2.6 (matches Table 10).
11. **EN rr2 tech/fact ratio FIXED** → 1.94x→1.47x (matches KR, 1.94x was duplicate of pipe).

## Session 9 Changes (2026-02-14)

### Completed in session 9:
1. **exp01 v2 COMPLETE** → 200/200, 0 errors, 20,718s (5.75h). All 8 patterns × 25 tasks. `results/exp01/summary.csv` + `raw.json`.
2. **Domain × pattern analysis** → `analyze_domain_pattern.py` executed. Key: debate3 CV=0.14 (domain-invariant), swm3 CV=0.67 (domain-sensitive). 5/9 domains significant (p<0.05). Figures: heatmap, time, tokens/turn.
3. **exp01 v2 main analysis** → `exp01_pattern_efficiency/analyze.py` updated to read `summary.csv` (was `summary_all.csv`). 12 plots + stats.md regenerated with v2 data.
4. **Section 4.1.6 POPULATED** → Both EN + KR papers filled with Tables 15, 16 + Findings 24-26 from real data. No more placeholders.
5. **Paper fixes** → KR "8 도메인" → "9 도메인", EN exp05 "720 runs" → "200 runs".
6. **exp05 v2 LAUNCHED** → 4 patterns (rr3,sel3,swm3,refl2) × 25 tasks × 3λ (0.0,0.1,0.5) = 400 runs. Background task b6ea7d8. Config LAMBDA_VALUES reduced from 5 to 3.

### exp05 v2 progress: 0/400 (just started), background task b6ea7d8.

## Session 8 Changes (2026-02-13 continued)

### Completed in session 8:
1. **adaptive_condition.py** → Updated from old U(t) to ΔU(t) = ΔQ(t) - λ·ΔC(t). Termination: ΔU(t) ≤ epsilon for `patience` turns.
2. **exp05 runner.py** → Added 3-retry + exponential backoff + crash detection (exit code 3221226091) + circuit breaker (5 consecutive failures → 60s pause). Fixed to save adaptive_stats.json with ΔU trajectories.
3. **5-category statistics** → Recomputed Kruskal-Wallis with df=4, N=718 from v1 data. Key: A vs B2 p=0.857 (ns!). New hierarchy: A ≈ B2 ≲ B1 ≈ C ≪ D.
4. **Paper updates** → All three papers (EN, KR, summary) fully updated for 5-category, ΔU(t), B1/B2 tables. Zero stale references.
5. **fig3 regenerated** → 25-task/8-pattern/ΔU(t) experiment design diagram.
6. **fig6 generated** → Convergence detection (from exp03 data).
7. **paper_strengthening_plan.md** → Comprehensive status update with progress tracking.
8. **Section 4.1.6 template** → Domain × Pattern cross-analysis placeholder in both EN + KR papers.
9. **analyze_domain_pattern.py** → Ready for exp01 v2 results. Generates heatmaps + Kruskal-Wallis + CV.
10. **analyze_exp05.py** → Ready for exp05 v2 results. Cost savings, λ sensitivity, ΔU trajectories.
11. **exp05 v1 backed up** → `results/exp05_v1/`. Cleared `results/exp05/` for v2.

### exp01 v2 progress: ~44/200 (22%), zero errors, sel3 pattern in progress.

## Session 7 Changes (2026-02-13): Professor's 4 Critiques

### Critique 1: U(t) must converge to 0
- **Problem**: Original U(t) = Q(t) - lambda*C(t) does NOT converge to 0. As C(t) grows, U(t) goes to negative infinity.
- **Fix**: Reformulate to **marginal utility** Delta-U(t) = Delta-Q(t) - lambda*Delta-C(t). This naturally converges to 0 as quality gains plateau while marginal cost remains constant.
- **exp05 updated**: Termination condition is now Delta-U(t) -> 0 (when marginal benefit no longer exceeds marginal cost), not U(t) threshold.
- **Paper RQ5 updated**: "Can marginal utility Delta-U(t) -> 0 serve as a topology-aware termination signal?"

### Critique 2: Domain-specific analysis needed
- **Problem**: 20 tasks across 4 generic categories (factual/analytical/creative/technical) lack domain diversity.
- **Fix**: New **25-task suite** across **8 domains**: science, CS, history, philosophy, law_politics, gaming, engineering, business (+ medicine if needed).
- Each domain has 3-4 tasks of varying difficulty.
- Enables domain x pattern cross-analysis (e.g., "Does debate excel in law/philosophy but fail in engineering?").

### Critique 3: Category B split into B1 + B2
- **Problem**: Selector (centralized router picks next speaker) and Swarm (decentralized agents hand off to each other) have fundamentally different topologies, yet were lumped together as "Dynamic Routing."
- **Fix**: Split into:
  - **B1: Centralized Routing (Star/Hub-and-Spoke)** - sel3, sel4. A central router LLM selects the next speaker. Uses `SelectorGroupChat`.
  - **B2: Decentralized Handoff (Mesh/Swarm)** - swm3, swm4. Agents autonomously decide handoffs via `Handoff` tool calls. Uses `Swarm` class.
- **Key implementation detail**: Debate also uses `SelectorGroupChat` (same underlying class as Selector), but with a debate-structured prompt. Swarm uses `Swarm` class with `HandoffTermination` and agent-level `Handoff` tool definitions.

### Critique 4: Categories need academic grounding
- **Problem**: Category names (Flat/Dynamic/Feedback/Composed) are ad-hoc, not grounded in MAS topology theory.
- **Fix**: Revised **5-category taxonomy** with academic citations:
  - **A: Sequential Chain** - Round-robin token passing (cf. chain topology in distributed systems)
  - **B1: Centralized Routing (Star)** - Hub-and-spoke with central coordinator (Masterman et al., 2025)
  - **B2: Decentralized Handoff (Mesh)** - Peer-to-peer autonomous handoffs (swarm intelligence literature)
  - **C: Structured Feedback** - Iterative refinement loops (Du et al., ICML 2024 for debate; NeurIPS 2024 reflection workshop)
  - **D: Composed/Nested** - Pipeline and mixture-of-agents (meta-architectures combining simpler topologies)

### config.py already updated
- `PATTERNS_CENTRALIZED = ["sel3", "sel4"]` (B1)
- `PATTERNS_DECENTRALIZED = ["swm3", "swm4"]` (B2)
- `PATTERNS_REPRESENTATIVE = ["rr3", "sel3", "sel4", "swm3", "swm4", "refl2", "debate3", "pipe"]` (8 patterns)
- `REPEAT_COUNT = 1` (200 runs = 8 patterns x 25 tasks x 1 repeat)
- `CATEGORY_NAMES` updated with topology names

## Current State: exp01 v2 COMPLETE (200/200), exp02 COMPLETE (100/100), exp05 v2 IN PROGRESS (425/800, 375 running)

### exp01 v1 Results (legacy 13 patterns x 20 tasks x 3 repeats)
| Category | Patterns | Runs | Errors | Status |
|----------|----------|------|--------|--------|
| A (Chain) | rr2, rr3, rr4 | 180/180 | 62 (34.4%)* | DONE |
| B (Dynamic, old) | sel3, sel4, swm3, swm4 | 240/240 | 0 (0%) | DONE |
| C (Feedback) | refl2, refl3, debate3, debate4 | 240/240 | 0 (0%) | DONE |
| D (Composed) | pipe, moa | 120/120 | 0 (0%) | DONE |

*Cat A errors due to _sys bug (fixed before Cat B). Cat B/C/D use fixed code.

### exp05 v1: FAILED (712/720 errors)
- **Exit code 3221226091** (0xC000041B) = Windows STATUS_FATAL_USER_CALLBACK_EXCEPTION
- SDK/subprocess crash, NOT a Python error. Only 8/720 runs succeeded.
- Must fix SDK stability before re-running exp05.
- This is a known Windows issue with the claude-agent-sdk subprocess spawning.

### Results Files (from v1 runs)
| File | Rows | Contents |
|------|------|----------|
| `results/exp01/summary_all.csv` | 780 | ALL 13 patterns merged (v1) |
| `results/exp01/summary_A.csv` | 180 | rr2, rr3, rr4 |
| `results/exp01/summary_B.csv` | 240 | sel3, sel4, swm3, swm4 |
| `results/exp01/summary_C.csv` | 240 | refl2, refl3, debate3, debate4 |
| `results/exp01/summary_D_pipe.csv` | 60 | pipe only |
| `results/exp01/summary_D.csv` | 60 | moa only |
| `results/exp02/summary.csv` | 100 | 5 patterns x 20 tasks (v1) |
| `results/exp02/scores.csv` | 276 | Turn-level G-Eval scores (276 substantive turns) |
| `results/exp02/raw.json` | 100 | Full turn data with quality scores |

## Key Findings (from v1 experiments)

### Category A (Sequential Chain)
- rr2: 55/60 ok, 52.4s, 4,759 tok, 1,583 out/turn
- rr3: 46/60 ok, 96.6s, 10,121 tok, 1,711 out/turn
- rr4: 17/60 ok, 118.8s, 12,040 tok, 1,942 out/turn (71.7% error from bug)
- **Collaborative amplification**: output/turn increases with team size
- **Superlinear error scaling**: rr2=8.3% -> rr3=23.3% -> rr4=71.7%

### Category B1 (Centralized Routing / Star)
- sel3: 60/60, 115.2s, 7,851 tok, 2,114 out/turn
- sel4: 60/60, 161.9s, 11,595 tok, 2,616 out/turn
- **Selector scales sub-linearly** (sel4/sel3 = 1.48x tokens for +1 agent)
- Uses SelectorGroupChat: central router LLM picks next speaker each turn

### Category B2 (Decentralized Handoff / Mesh)
- swm3: 60/60, 75.2s, 4,196 tok, 337 out/turn
- swm4: 60/60, 185.0s, 13,321 tok, 330 out/turn
- **swm3 = best overall efficiency** (beats rr2 despite more agents!)
- **Swarm scales super-linearly** (swm4/swm3 = 3.17x tokens, turn explosion 10->25)
- Uses Swarm class: agents decide handoffs via Handoff tool calls

### B1 vs B2 comparison (KEY INSIGHT for paper)
- Same agent count (3), opposite scaling behavior
- Centralized (sel3): few long monologues, 2,114 tok/turn
- Decentralized (swm3): many short handoffs, 337 tok/turn
- Centralized scales sub-linearly (router absorbs coordination cost)
- Decentralized scales super-linearly (handoff chains explode)

### Category C (Structured Feedback)
- refl2: 60/60, 60.2s, 5,237 tok, 1,622 out/turn
- refl3: 60/60, 120.2s, 12,095 tok, 2,440 out/turn
- debate3: 60/60, 156.6s, 9,313 tok, 1,719 out/turn
- debate4: 60/60, 180.9s, 11,637 tok, 1,440 out/turn
- **refl2 = second most efficient** (5,237 tok, only swm3 beats it)
- **debate4 out/turn DECREASES** (1,440 vs debate3's 1,719) = diminishing returns in larger debates
- Note: Debate uses SelectorGroupChat (same class as Selector) but with debate prompt structure

### Category D (Composed/Nested)
- pipe: 60/60, 129.6s, 13,856 tok, 1,588 out/turn, 0% errors
- moa: 60/60, 103.0s, 22,333 tok, 1,587 out/turn, 0% errors
- **moa = MOST EXPENSIVE overall** (22,333 avg tokens, tech tasks reach 37,844)

## exp02 Results: Termination Quality (100/100, 276 turn scores)

### Key Findings (Findings 15-17)

**Finding 15 -- Three quality trajectory shapes**:
- **Monotonic-then-plateau** (rr3): Quality rises to ~4.35 by turn 3, plateaus through turn 6. Only 0.05 quality loss from over-computation.
- **Peak-at-turn-2** (refl2): Quality jumps to 4.80 at turn 2 (critic approval), holds. Zero quality loss, zero regret.
- **Monotonic-decline** (debate3): Quality peaks at turn 1 (4.00), degrades to 3.35 by turn 3-4. Loses 0.65 quality points from over-computation.

**Finding 16 -- Termination regret varies 13x across topologies**:
| Pattern | Avg Final Q | Q at Peak | t_optimal | t_actual | Regret | Q_loss |
|---------|-------------|-----------|-----------|----------|--------|--------|
| refl2 | 4.80 | 4.80 | 2 | 2 | +0.0 | 0.00 |
| swm3 | 4.05 | 4.20 | 1 | 1.3 | +0.2 | 0.15 |
| rr3 | 4.35 | 4.40 | 3 | 5.6 | +2.6 | 0.05 |
| sel3 | 3.50 | 4.00 | 1 | 2.8 | +1.8 | 0.50 |
| debate3 | 3.45 | 4.00 | 1 | 3.8 | +2.8 | 0.65 |

**Finding 17 -- Reflection achieves best quality with zero regret**: refl2 is the only topology where t_actual = t_optimal. The critic's APPROVED signal is a natural, reliable termination signal.

### Marginal utility from exp02 (NEW - for Critique 1)
- exp02 turn-level scores can be used to compute Delta-Q(t) = Q(t) - Q(t-1)
- Combined with token cost per turn, this gives Delta-U(t) = Delta-Q(t) - lambda * Delta-C(t)
- This can be computed from EXISTING data without new experiments
- Key question: Does Delta-U(t) -> 0 at t_optimal for each pattern?

## ★ WHAT TO DO NEXT (In Order)

### 1. ~~Compute marginal utility Delta-U(t) from existing exp02 data~~ ✅ DONE
- `compute_marginal_utility.py` created and run
- Output: `results/exp02/marginal_utility.csv`, `marginal_utility_summary.csv`
- Figures: `fig_marginal_utility.png`, `fig_marginal_utility_heatmap.png`, `fig_utility_U_vs_dU.png`
- **Key finding: ΔU(t) → 0 within 1.1-2.4 turns for all 5 patterns**
- **Key finding: λ-insensitivity (ΔQ saturation is dominant signal)**
- Paper Section 4.5 updated with Findings 21-23, Tables 13-14

### 2. ~~Regenerate figures with 5-category structure~~ ✅ DONE
- fig1_taxonomy.png (5-category tree)
- fig2_architectures.png (B1 Star + B2 Mesh diagrams)
- fig4_exp01_main.png (780 v1 runs, 13 patterns)
- fig5_quality_trajectories.png (276 turn scores with B1/B2 fix)

### 3. exp01 v2 RUNNING (background task b1453c9)
- 8 patterns x 25 tasks = 200 runs, ~50s/run avg
- Progress: ~44/200 (22%) as of session 8 late, zero errors
- rr3 complete (25/25), sel3 in progress (~19/25, on eng_02)
- task_suite.json has 25 tasks (9 domains incl. medicine)
- v1 results backed up to `results/exp01_v1/`
- Monitor: Read output file for latest progress

### 4. After exp01 v2 completes: Domain x Pattern cross-analysis
- New 25-task suite has domain tags (science, CS, history, philosophy, law_politics, gaming, engineering, business, medicine)
- Key questions:
  - Does debate excel in argumentative domains (law, philosophy)?
  - Does sequential chain suffice for factual domains (science, history)?
  - Which patterns are domain-invariant vs domain-sensitive?
- Output: domain x pattern heatmap, statistical significance tests

### 5. Fix SDK stability for exp05 ✅ MITIGATION DONE
- exp05 v1 failed with 712/720 errors (exit code 3221226091)
- **Fixed**: runner.py now has 3-retry + exponential backoff + crash detection + circuit breaker
- **Fixed**: runner.py now saves adaptive_stats.json with ΔU trajectories
- **v1 data backed up** to `results/exp05_v1/`, `results/exp05/` cleared for v2
- **analysis script ready**: `analyze_exp05.py`
- **Next**: Pilot test after exp01 v2 completes (to avoid SDK resource contention)

### 6. ~~Run new exp05 with Delta-U(t) -> 0 termination condition~~ ✅ DONE (800/800)
- 800 runs = 8 patterns × 3 λ × 25 tasks (200 baseline + 600 adaptive), 0% errors
- Results: `results/exp05/summary.csv`, `adaptive_stats.json`, `exp05_analysis.csv`
- Key: Topology-dependent benefit. swm4: -65%/-70% savings. λ≥0.1 avg: -13% tokens.
- Paper Section 4.5 fully populated in both EN + KR (Findings 27-29, Tables 17-18)

### 7. ~~Update paper for all new findings~~ ✅ DONE
- Section 4.1.2: B1/B2 split ✅ DONE
- Section 4.1.5: 5-category cross-analysis ✅ DONE (Findings 18-20 recomputed)
- Section 4.1.6: Domain × pattern cross-analysis ✅ DONE (Findings 24-26, Tables 15-16)
- Section 4.5: ΔU(t) pre-validation ✅ DONE (Findings 21-23, Tables 13-14)
- Section 4.5: exp05 controlled experiment ✅ DONE (Findings 27-29, Tables 17-18)
- Abstract, RQ5, taxonomy, conclusion: ✅ ALL updated in both EN + KR
- Section 3.2: 25-task suite with 9 domains ✅ DONE (EN + KR)
- Appendix A: 25-task table ✅ DONE (EN + KR)
- Section 5.1 Guidelines: Guideline 4 fixed to reflect exp05 ✅ DONE
- Section 5.2 Discussion: B1/B2 cost analysis ✅ DONE (EN + KR)
- Consistency audit (session 10): 11 fixes applied ✅ DONE

### 8. Remaining before COLM submission
- ~~**exp05 v2 completion**~~: ✅ DONE (800/800, 0% errors)
- ~~**analyze_exp05.py with 800 data**~~: ✅ DONE (Tables 17-18 updated, fig8 regenerated)
- ~~**Tran et al. arXiv ID**~~: ✅ FIXED (2502.11078 was WRONG → 2501.06322)
- ~~**COLM format**~~: ✅ LaTeX converted (`latex/main.tex`, 9-page main + appendix)
- **Human evaluation**: 30 expert-annotated samples still pending manual review.
- **LaTeX compilation**: Upload `latex/` to Overleaf → compile → verify 9-page fit → adjust if needed.

## Key Files

| File | Purpose |
|------|---------|
| `paper_draft.md` | English paper (6 sections + appendices) |
| `paper_draft_kr.md` | Korean paper (full translation) |
| `paper_summary.md` | Presentation summary for professor |
| `docs/Termination.md` | GPT's venue/strategy analysis |
| `config.py` | All constants, patterns, model configs (B1/B2 split done) |
| `experiment_utils.py` | TeamFactory, ExperimentRunner, I/O |
| `task_suite.json` | 25 tasks across 9 domains (v2, updated in-place) |
| `run_experiment.py` | CLI orchestrator |
| `run_all_exp01.py` | Per-category runner with checkpoint + skip |
| `merge_results.py` | Merges summary_*.csv + raw_*.json |
| `results/exp01/` | v1 output (780 runs) |
| `results/exp02/` | v1 output (100 runs, 276 turn scores) |
| `figures/` | Figure scripts (fig1-fig8) + generated PNGs |
| `paper_strengthening_plan.md` | Roadmap to COLM submission |
| `HANDOFF.md` | This file |

## Important Technical Details

### Python Environment
- **USE**: `C:/Python313/python` (Python 3.13.7) - has all deps
- **NEVER**: Use venv (`D:\Data\25_ACE\venv\`) - nearly empty
- **NEVER**: Use pytest for files in `mcp/` dir (name conflict)

### model_factory.py (FIXED)
- Line 89: `import sys as _sys`
- Line 237: `file=_sys.stderr`
- Prompt truncation at 28K chars (first 8K + last 20K)
- All new processes use fixed code

### Implementation details for patterns
- **SelectorGroupChat** used by: sel3, sel4 (B1) AND debate3, debate4 (C)
  - Selector: router picks best specialist
  - Debate: router enforces turn-taking among debaters + moderator
- **Swarm** class used by: swm3, swm4 (B2)
  - Agents have `Handoff` tool definitions
  - `HandoffTermination` ends when no more handoffs
  - Agents autonomously decide who to hand off to

### matplotlib
- Use `tick_labels=` NOT `labels=` in boxplot (deprecated in 3.9+)

### exp05 crash details
- Exit code 3221226091 = 0xC000041B (STATUS_FATAL_USER_CALLBACK_EXCEPTION)
- 712/720 runs failed with this Windows-specific crash
- Occurs in SDK subprocess spawning, not in Python logic
- Only 8 runs succeeded (all with lambda=0.0)

## Paper Status

### Taxonomy revised (5 categories with academic grounding)
- **A: Sequential Chain** - token-passing ring (distributed systems)
- **B1: Centralized Routing (Star)** - hub-and-spoke (Masterman et al., 2025)
- **B2: Decentralized Handoff (Mesh)** - peer-to-peer swarm (swarm intelligence)
- **C: Structured Feedback** - iterative refinement (Du et al. ICML 2024; NeurIPS 2024 Reflection)
- **D: Composed/Nested** - meta-architectures (pipeline, mixture-of-agents)

### RQ5 updated (marginal utility)
- Old: "Can U(t) = Q(t) - lambda*C(t) serve as a termination signal?"
- New: "Can marginal utility Delta-U(t) = Delta-Q(t) - lambda*Delta-C(t) -> 0 serve as a topology-aware termination signal?"

### Sections Complete with Data
- **Section 4.1.1** (Cat A): Tables 3, 3b, 4 + Findings 1-4
- **Section 4.1.2** (Cat B, old): Tables 5, 6 + Findings 5-7 (needs B1/B2 split)
- **Section 4.1.3** (Cat C): Tables 7, 7b + Findings 8-11
- **Section 4.1.4** (Cat D): Tables 8, 8b, 9 + Findings 12-14
- **Section 4.1.5** (Cross-category): Tables 12, 12b, 12c + Findings 18-20 (needs 5-cat update)
- **Section 4.2** (exp02 quality): Tables 10, 11, 11b + Findings 15-17
- **Section 5.2**: Collaborative amplification discussion

### Sections Awaiting Update/Data
- **Section 4.1.2**: B1/B2 split ✅ DONE in both EN + KR
- **Section 4.1.5**: 5-category Kruskal-Wallis ✅ DONE (df=4)
- **Section 4.5**: ΔU(t) pre-validation ✅ DONE. Awaiting exp05 controlled results (SDK fix needed)
- **Section 3**: Taxonomy + task suite ✅ DONE (5-category, 25-task, 9 domains)
- **All sections**: Awaiting domain-specific analysis from exp01 v2 (running)

### Figures Generated (need refresh)
- `figures/fig_preliminary_catA.png` - 3-pattern comparison
- `results/exp01/plots/` - 12 Cat A analysis plots
- `results/exp03/` - convergence curves
- `results/exp04/` - error distribution plots

## Task List
- #15 [completed]: exp01 Category A (180/180)
- #16 [completed]: exp01 Category B (240/240)
- #17 [completed]: exp01 Category C (240/240)
- #18 [completed]: exp01 Category D - pipe 60/60 + moa 60/60
- #19 [completed]: Full exp01 analysis (all 13 patterns in summary_all.csv)
- #20 [completed]: Write paper Section 4.1.3 (Cat C) + 4.1.4 (Cat D)
- #21 [completed]: Cross-category comparison (Section 4.1.5, Tables 12/12b/12c, Findings 18-20)
- #22 [completed]: exp02 quality trajectories (100/100, 276 turn scores, Findings 15-17)
- #23 [FAILED]: exp05 adaptive termination (712/720 errors, exit code 3221226091)
- #25 [completed]: Korean paper draft
- #26 [completed]: Presentation summary
- #27 [pending]: Fix SDK stability for exp05 (exit code 3221226091 blocker)
- #28 [completed]: Create 25-task suite (task_suite.json updated in-place, 9 domains)
- #29 [completed]: Run exp01 v2 (200/200, 0 errors, 20718s, all 8 patterns)
- #30 [completed]: Compute ΔU(t) from existing exp02 scores → marginal_utility.csv + figures
- #31 [completed]: Run exp05 v2 first 400 runs (4 patterns × 100 each)
- #32 [completed]: Domain × pattern cross-analysis (debate3 CV=0.14 invariant, swm3 CV=0.67 sensitive)
- #33 [completed]: Regenerate figures (fig1-6, fig8, marginal_utility, pareto + domain heatmaps)
- #34 [completed]: Update paper Sections 4.1.6 (domain analysis) with real data (EN+KR)
- #35-41 [completed]: Various config/script/paper updates (sessions 8-10)
- #42 [in_progress]: exp05 v2 remaining 375 runs (sel4 adaptive + swm4 + debate3 + pipe). Background task b2ce704.
- #43 [completed]: Regenerate fig4 with v2 data
- #44 [completed]: COLM consistency audit (Tables 8/11b/15/17/18 fixed, refs complete, Table 14 synced)
- #45 [pending]: After exp05 completes: re-analyze + update Section 4.5 + regenerate fig8
