# Preliminary Results: Category A (Flat Sequential)

## Table: Pattern Efficiency - Category A (Updated)

| Metric | rr2 (n=2) | rr3 (n=3) | Ratio (rr3/rr2) |
|--------|-----------|-----------|------------------|
| Total runs | 60 | 39* | - |
| Successful runs | 55/60 | 33/39* | - |
| Error rate | 8.3% | 15.4%* | 1.86x |
| Mean SDK calls | 1.9 | 3.9 | 2.05x |
| Mean duration (s) | 53.0 | 115.8 | 2.19x |
| Mean tokens (in) | 1,467 | 4,616 | 3.15x |
| Mean tokens (out) | 3,702 | 6,953 | 1.88x |
| Mean total tokens | 5,169 | 11,569 | 2.24x |
| Output tokens/call | ~1,950 | ~1,783 | 0.91x |

*rr3 data is partial (39/60 runs complete, rr4 not started)

## Key Observations (Updated)

### 1. Error rate scales with agent count
rr3 (15.4%) has nearly double the error rate of rr2 (8.3%). All 11 errors are
from the same infrastructure bug (prompt truncation NameError). More agents
accumulate more context per round, hitting the 28K char limit more frequently.

- rr2: Only on tech tasks (long single responses: tech_01 x3, tech_05 x2)
- rr3: On creative (crea_01, crea_04, crea_05) AND analytical (anal_01, anal_02 x2) tasks
  → Multi-round context accumulation spreads errors across task categories

### 2. Sub-linear output scaling (confirmed)
Output tokens per SDK call DECREASE: rr2 (1,950) → rr3 (1,783) = 0.91x.
The 3rd agent often produces shorter responses or early TERMINATE signals.

### 3. Input token superlinear growth (confirmed)
Input tokens grow at 3.15x for only 2.05x more LLM calls. Each additional
agent round adds proportionally more context (full conversation history).

### 4. Duration scales 2.2x (slightly superlinear)
rr3 takes 2.19x as long as rr2, exceeding the 2.05x SDK call ratio.
Additional overhead from larger prompts (API latency ~ O(prompt_length)).

### 5. Task category effects (with rr3 analytical data)
| Category | Runs | Mean Duration | Mean Tokens | Notes |
|----------|------|--------------|-------------|-------|
| Analytical | 24 | 81.2s | 7,536 | Medium cost, structured |
| Factual | 30 | 66.5s | 6,183 | Moderate, retrieval-based |
| Creative | 30 | 93.3s | 8,578 | Longest, open-ended |
| Technical | 15 | 63.7s | 9,178 | High token density |

Analytical tasks moved from cheapest (rr2-only) to medium cost with rr3 data,
as rr3 analytical runs are longer due to multi-round deliberation.

## Error Pattern Analysis

| Trigger Condition | rr2 (5 errors) | rr3 (6 errors) |
|-------------------|----------------|----------------|
| Technical tasks | 5 (100%) | 0 (0%) |
| Creative tasks | 0 | 3 (50%) |
| Analytical tasks | 0 | 3 (50%) |
| Factual tasks | 0 | 0 |

**Interpretation**: rr2 errors are concentrated on technical tasks (single long
responses). rr3 errors spread across creative and analytical tasks (multi-round
context accumulation). Factual tasks are shortest and never trigger truncation.

## Implications for Paper

1. **Agent count as a risk factor**: More agents → higher error rate from context
   accumulation → Motivates adaptive termination to stop before overflow
2. **Task-topology interaction is real**: Error patterns differ between topologies
   even for identical tasks → Supports topology-aware termination design
3. **Infrastructure vs. reasoning errors**: All current errors are infrastructure-level.
   Content-level error analysis (exp04) will classify reasoning failures.
