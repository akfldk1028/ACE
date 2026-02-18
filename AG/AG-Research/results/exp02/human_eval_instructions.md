# Human Evaluation Instructions

## Overview
You are evaluating 30 samples of multi-agent conversation outputs.
Each sample contains a **task prompt** and the **agents' cumulative response**.

## Rating Scale (1-5)
For each sample, rate on 5 dimensions:

| Score | Meaning |
|-------|---------|
| 5 | Excellent - comprehensive, accurate, well-structured |
| 4 | Good - mostly complete with minor gaps |
| 3 | Adequate - covers basics but misses important aspects |
| 2 | Poor - significant errors or omissions |
| 1 | Very Poor - fundamentally wrong or irrelevant |

## Dimensions
1. **Accuracy**: Are the facts and claims correct?
2. **Completeness**: Does the response thoroughly address all parts of the task?
3. **Coherence**: Is the response logically organized and consistent?
4. **Usefulness**: Does the response provide practical, actionable value?
5. **Overall**: Holistic quality considering all factors above.

## Procedure
1. Read the **task prompt** carefully.
2. Read the **agent response** in full.
3. Assign integer scores (1-5) for each dimension.
4. Optionally add brief comments in the **comments** column.
5. Do NOT look at the answer key until you have finished all 30 samples.

## Important Notes
- Rate based on the response content alone, not on formatting or language.
- If the response is in Korean or mixed language, evaluate content quality equally.
- Some responses may be truncated - evaluate what is present.
- Samples are randomized - do not assume any ordering by quality.

## Time Estimate
~30-45 minutes (1-1.5 min per sample)

## After Completion
Save the filled CSV and run:
```bash
C:/Python313/python analyze_human_eval.py
```
This will compute inter-rater agreement metrics (Pearson, Spearman, Cohen's kappa).
