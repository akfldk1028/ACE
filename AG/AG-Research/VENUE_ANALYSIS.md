# Venue & Publishability Analysis

> Last updated: 2026-02-19
> Paper: "When Should Multi-Agent Teams Stop? A Systematic Study of Termination Dynamics Across 13 Coordination Topologies"

---

## 1. Publishability Assessment

### 1.1 Overall Verdict: **Conditionally Publishable (B+ tier)**

The paper addresses a real and timely gap. Termination in multi-agent LLM systems is an acknowledged open problem (Cemri et al., NeurIPS 2025). However, current form has critical weaknesses that must be addressed before submission to a top venue.

### 1.2 Strengths (What reviewers will like)

| # | Strength | Evidence |
|---|----------|----------|
| S1 | **First systematic cross-topology study** | 14 patterns x 6 categories x 2000+ runs. No prior work compares this many topologies for termination behavior. |
| S2 | **Non-trivial finding: swm3 > rr2** | 3-agent swarm more efficient than 2-agent chain (4196 vs 4759 tokens). Counterintuitive and novel. |
| S3 | **New cost hierarchy** | A ~ B2 < B1 ~ C << D replaces prior assumption A << B ~ C << D |
| S4 | **Practical guidelines** | 4 actionable design guidelines for practitioners |
| S5 | **Unified framework** | Single AutoGen framework, controlled variables, reproducible |
| S6 | **Cross-model validation** | Claude + GPT-4o-mini, Spearman rho=0.900 |

### 1.3 Weaknesses (What reviewers will attack)

| # | Weakness | Severity | Fix Difficulty |
|---|----------|----------|----------------|
| W1 | **Hybrid keyword+deltaU never tested** | Critical | Hard (800 runs needed) |
| W2 | **deltaU fails as replacement in 7/8 patterns** | Critical | Already reframed as diagnostic |
| W3 | **Cohen's kappa_w = 0.244 ("fair")** | High | Medium (add 2nd evaluator) |
| W4 | **Single human evaluator** | High | Medium (recruit annotator) |
| W5 | **No confidence intervals** | Medium | Easy (add std/CI to tables) |
| W6 | **n=5 for cross-model Spearman** | Medium | Medium (test more patterns) |
| W7 | **39 findings = too many** | Medium | Easy (compress to ~15) |
| W8 | **Single task type (open-ended Q&A)** | High | Hard (new experiments needed) |
| W9 | **Single framework (AutoGen)** | Medium | Acknowledged in limitations |

### 1.4 Competitive Landscape

#### Direct Competitors

| Paper | Venue | Topologies | Termination Focus | Overlap |
|-------|-------|-----------|-------------------|---------|
| [Hu et al. 2025 - Adaptive Stability Detection](https://arxiv.org/abs/2510.12697) | NeurIPS 2025 | Debate only | KS-test for debate convergence | **High** - our exp03 extends this to 8 topologies |
| [Cemri et al. 2025 - Why MAS Fail](https://arxiv.org/abs/2503.13657) | NeurIPS 2025 | 7 frameworks, 14 failure modes | Termination as one failure mode | **Medium** - identifies problem, we provide solutions |
| [Kim et al. 2025 - Scaling Agent Systems](https://arxiv.org/abs/2512.08296) | arXiv | 5 topologies (SAS/Ind/Cent/Dec/Hyb) | No termination study | **Medium** - similar topology comparison, different focus |
| [Zhou et al. 2025 - Multi-Agent Design (MASS)](https://arxiv.org/abs/2502.02533) | ICLR 2026 | Prompt+topology co-optimization | No termination study | **Low** - optimizes topology, doesn't study when to stop |
| [MultiAgentBench (MARBLE)](https://arxiv.org/abs/2503.01935) | ACL 2025 | Star/chain/tree/graph | No termination study | **Low** - benchmark, not termination-focused |
| [Emergent Convergence in MAS Annotation](https://arxiv.org/abs/2512.00047) | BlackboxNLP 2025 | Annotation agents | Cosine + intrinsic dimensionality | **Medium** - convergence detection, different context |

#### Key Differentiation
- **Hu et al.** = debate-only KS-test. We cover 14 topologies + quality-cost tradeoff (deltaU). Our exp03 directly extends their work.
- **Cemri et al.** = identifies termination as a failure mode. We provide systematic analysis + solutions.
- **Kim et al.** = predicts best topology for task type. We study when each topology should stop.
- **No existing paper** combines topology-aware termination + quality trajectory + marginal utility framework across 14 patterns.

### 1.5 Novelty Assessment

| Claim | Novelty | Prior Art |
|-------|---------|-----------|
| 14-topology termination comparison | **High** | Max prior: 5 topologies (Kim et al.) |
| deltaU marginal utility framework | **Medium** | Utility-based stopping exists in economics/RL, new to MAS-LLM |
| Quality trajectory shapes (monotone/spike/decay) | **Medium-High** | No systematic categorization exists |
| Termination regret metric | **Medium** | Related to "over-computation" in prior work |
| swm3 > rr2 efficiency finding | **High** | Counterintuitive, not in any prior work |
| Cost hierarchy revision | **High** | No prior empirical hierarchy across 14 patterns |

---

## 2. Venue Recommendations

### Tier 1: Best Fit (Primary Targets)

#### COLM 2026 - Conference on Language Modeling
- **Fit**: Topic 16 explicitly lists "multi-agents learning"
- **Deadline**: Abstract Mar 26, Full paper Mar 31, 2026
- **Format**: 9 pages + unlimited references
- **Location**: San Francisco, Oct 6-9, 2026
- **Pros**: Broad LM scope includes multi-agent; peer conference to NeurIPS/ICML; Hu et al.'s debate paper was cited from NeurIPS
- **Cons**: Core focus is still LM training/architecture; reviewers may want more LM-specific contribution
- **Verdict**: **SUBMIT HERE** - deadline is 5 weeks away, feasible
- **URL**: https://colmweb.org/cfp.html

#### AAMAS 2026 - Autonomous Agents and Multiagent Systems
- **Fit**: **Perfect** - multi-agent coordination is core scope
- **Deadline**: ~~Abstract Oct 1, Paper Oct 8, 2025~~ **PASSED**
- **Location**: Paphos, Cyprus, May 25-29, 2026
- **Cons**: Deadline already passed
- **Verdict**: Missed. Consider AAMAS 2027
- **URL**: https://cyprusconferences.org/aamas2026/

### Tier 2: Strong Fit (Backup Targets)

#### IJCAI-ECAI 2026
- **Fit**: Multi-agent systems is explicit topic area
- **Deadline**: ~~Abstract Jan 12, Paper Jan 19, 2026~~ **PASSED**
- **Location**: Bremen, Germany, Aug 15-21, 2026
- **Format**: 7 pages + 2 references
- **Verdict**: Missed. Consider IJCAI 2027
- **URL**: https://2026.ijcai.org/

#### ACL 2026 (Main or Workshop)
- **Fit**: If framed as NLP/dialogue system termination
- **Deadline**: Via ARR rolling review (Jan/Apr cycles)
- **Location**: California, 2026
- **Cons**: Needs stronger NLP framing; multi-agent is secondary topic
- **URL**: https://2026.aclweb.org/

#### EMNLP 2026
- **Fit**: Similar to ACL; "agents" workshops emerging
- **Deadline**: TBD (typically ~June for main, ~Aug for workshops)
- **Location**: Budapest, Hungary, Oct 24-29, 2026
- **URL**: (not yet announced)

### Tier 3: Workshop Opportunities (Lower bar, faster feedback)

| Workshop | Venue | Deadline | Status |
|----------|-------|----------|--------|
| ICLR 2026 Workshop on Multi-Agent Learning & GenAI | ICLR 2026 | ~~Feb 5-10, 2026~~ | **PASSED** |
| WMAC 2026 (LLM-Based Multi-Agent Collaboration) | AAAI 2026 | ~~Jan 2026~~ | **PASSED** |
| ICML 2026 Workshops | ICML 2026, Seoul | Workshop notification: May 15 | **TBD** - watch for MAS workshops |
| NeurIPS 2026 Workshops | NeurIPS 2026 | ~Sep 2026 | **TBD** |

### Recommended Strategy

```
Priority 1: COLM 2026 (Mar 31 deadline) - 5 weeks to fix critical issues
Priority 2: EMNLP 2026 (main or workshop, ~Jun-Aug deadline)
Priority 3: ICML 2026 Workshop (if MAS workshop announced, ~Apr deadline)
Priority 4: NeurIPS 2026 Workshop (~Sep deadline)
Fallback:   AAMAS 2027 / IJCAI 2027 (Oct 2026 deadlines)
```

---

## 3. COLM 2026 Submission Plan (Priority 1)

### 3.1 Timeline (5 weeks: Feb 19 - Mar 31)

| Week | Dates | Tasks |
|------|-------|-------|
| 1 | Feb 19-25 | Fix W5 (add CI to all tables), Fix W7 (compress findings 39->15) |
| 2 | Feb 26-Mar 4 | Fix W3/W4 (recruit 2nd evaluator, re-annotate 30 samples) |
| 3 | Mar 5-11 | Fix W1 (hybrid keyword+deltaU experiment, 800 runs) |
| 4 | Mar 12-18 | Integrate results, rewrite Section 4.5 + conclusion |
| 5 | Mar 19-26 | LaTeX polish, 9-page formatting, abstract submission (Mar 26) |
| +3d | Mar 27-31 | Final revisions, full paper submission (Mar 31) |

### 3.2 Critical Fixes for COLM

1. **[P0] Hybrid experiment** (W1): Run keyword+deltaU combined, show improvement over keyword-alone
2. **[P0] 2nd evaluator** (W3/W4): One more person annotates same 30 samples, compute inter-rater kappa
3. **[P1] Confidence intervals** (W5): Add std and 95% CI to Tables 14-16, 22, 28
4. **[P1] Finding compression** (W7): 39 -> ~15 core findings + appendix
5. **[P2] Framing**: Emphasize LM interaction patterns (COLM Topic 16), not just MAS

### 3.3 Page Budget (9 pages)

```
1. Introduction + RQs:       1.5 pages
2. Related Work:              1.0 page
3. Methodology:               1.5 pages  (14 topologies, 5 experiments)
4. Results:                   3.5 pages  (key findings only, details in appendix)
5. Discussion + Guidelines:   1.0 page
6. Conclusion:                0.5 page
References:                   unlimited
Appendix:                     unlimited (39 findings, full tables, etc.)
```

---

## 4. Related Work Summary

### 4.1 Multi-Agent Termination (Direct)

- **Hu et al. (2025)** - KS-test for debate convergence. NeurIPS 2025. We extend to 14 topologies.
- **Cemri et al. (2025)** - MAST framework: 14 failure modes incl. termination gaps. NeurIPS 2025 D&B.
- **Emergent Convergence (2025)** - Cosine + intrinsic dimensionality for annotation convergence. BlackboxNLP.

### 4.2 Multi-Agent Topology Comparison (Indirect)

- **Kim et al. (2025)** - 5 topologies, predict optimal with R^2=0.524. Task-type aware.
- **Zhou et al. (2025)** - MASS: prompt+topology co-optimization. ICLR 2026.
- **MultiAgentBench (2025)** - Star/chain/tree/graph benchmark. ACL 2025.
- **AgentArch (2025)** - Enterprise agent architecture benchmark.

### 4.3 Cost-Quality Tradeoff (Tangential)

- **Transcending Cost-Quality Tradeoff (2025)** - Session-aware model selection. GPT-4o quality at 16.5% cost.
- **LLM Agents for Bargaining (2025)** - Utility-based feedback framework.

### 4.4 Multi-Agent Failure & Robustness

- **"Why Do MAS Fail?" (2025)** - 1600+ traces, 7 frameworks, kappa=0.88.
- **"Can LLM Agents Really Debate?" (2025)** - Critique of debate effectiveness.
- **"From Debate to Equilibrium" (2025)** - Bayesian Nash Equilibrium framing.

---

## 5. Key Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Reviewer says "incremental over Hu et al." | Medium | High | Emphasize: 14 vs 1 topology, quality trajectory, deltaU framework |
| "Single task type" rejection | Medium | High | Acknowledge limitation, argue controlled study value |
| "deltaU doesn't work" objection | High | Critical | Already reframed as diagnostic. Add hybrid experiment. |
| "Weak evaluation" (kappa=0.244) | High | Medium | Get 2nd evaluator. Report honest kappa. |
| COLM reviewers unfamiliar with MAS | Medium | Medium | Frame around LM interaction patterns, cite AutoGen (COLM 2024) |
| 9-page limit too tight for 5 experiments | Medium | Low | Move details to appendix, focus on 3 key experiments |

---

## 6. Bottom Line

**Is this paper publishable?**

- **As-is**: Borderline reject at top venues. Too many findings, weak evaluation, untested hybrid.
- **With P0 fixes (hybrid + 2nd evaluator + CI)**: Solid workshop paper, possible main conference.
- **With all fixes**: Competitive for COLM/EMNLP/AAMAS-tier venues.

**Unique contribution that no other paper has**:
The cross-topology termination analysis (14 patterns, quality trajectories, termination regret) is genuinely novel. The closest competitor (Hu et al.) covers only debate. Kim et al. compare topologies but don't study termination. This paper sits at the intersection.

**Recommendation**: Submit to COLM 2026 (Mar 31) with P0 fixes. Even if rejected, reviewer feedback will be invaluable for EMNLP 2026 or AAMAS 2027 submission.
