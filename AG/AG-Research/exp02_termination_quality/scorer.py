"""
G-Eval LLM-as-Judge Scorer
===========================
Evaluates multi-agent output quality per turn using an LLM judge.

Metrics: accuracy, completeness, coherence, usefulness, overall (1-5 scale)
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import MODEL_JUDGE
from experiment_utils import RunResult, _make_client


@dataclass
class TurnScore:
    turn_index: int
    accuracy: float
    completeness: float
    coherence: float
    usefulness: float
    overall: float


SCORING_PROMPT = """You are evaluating a multi-agent conversation output.

## Task
{task}

## Evaluation Rubric
{rubric}

## Cumulative Response (up to turn {turn_index})
{cumulative_text}

## Instructions
Rate the cumulative response on these 5 dimensions (1-5 scale each):
1. **Accuracy**: Correctness of facts and claims
2. **Completeness**: How thoroughly the task is addressed
3. **Coherence**: Logical flow and consistency
4. **Usefulness**: Practical value of the answer
5. **Overall**: Overall quality considering all factors

Return ONLY a JSON object with exactly these keys:
{{"accuracy": N, "completeness": N, "coherence": N, "usefulness": N, "overall": N}}

where N is an integer from 1 to 5.
"""


async def score_single_turn(
    task_text: str,
    rubric: str,
    cumulative_text: str,
    turn_index: int,
) -> TurnScore:
    """Score a single turn's cumulative output using LLM judge."""
    client = _make_client(MODEL_JUDGE)

    prompt = SCORING_PROMPT.format(
        task=task_text,
        rubric=rubric,
        turn_index=turn_index,
        cumulative_text=cumulative_text[:3000],
    )

    from autogen_core.models import UserMessage

    try:
        result = await client.create(messages=[UserMessage(content=prompt, source="user")])
        text = str(result.content).strip()

        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', text)
        if json_match:
            scores = json.loads(json_match.group())
        else:
            scores = {"accuracy": 3, "completeness": 3, "coherence": 3, "usefulness": 3, "overall": 3}

        return TurnScore(
            turn_index=turn_index,
            accuracy=max(1, min(5, int(scores.get("accuracy", 3)))),
            completeness=max(1, min(5, int(scores.get("completeness", 3)))),
            coherence=max(1, min(5, int(scores.get("coherence", 3)))),
            usefulness=max(1, min(5, int(scores.get("usefulness", 3)))),
            overall=max(1, min(5, int(scores.get("overall", 3)))),
        )
    except Exception as e:
        print(f"  Scoring error at turn {turn_index}: {e}", file=sys.stderr)
        return TurnScore(turn_index=turn_index, accuracy=0, completeness=0,
                         coherence=0, usefulness=0, overall=0)


def _is_handoff_turn(content: str) -> bool:
    """Check if a turn is a handoff/function-call metadata turn (no substantive content)."""
    indicators = [
        "FunctionCall(",
        "FunctionExecutionResult(",
        "Transferred to ",
        "transfer_to_",
    ]
    return any(ind in content for ind in indicators)


async def score_all_turns(
    run: RunResult,
    task_meta: dict,
) -> list[TurnScore]:
    """Score each turn cumulatively for a single run.

    Handoff/function-call turns are excluded from scoring but still
    accumulated into context. Scoring only happens when substantive
    content is added (non-handoff turns with >20 chars of content).
    """
    scores = []
    cumulative = ""
    substantive_index = 0

    for turn in run.turns:
        if turn.source == "user":
            continue

        content = str(turn.content)

        # Skip handoff metadata turns entirely (don't accumulate or score)
        if _is_handoff_turn(content):
            continue

        # Skip very short turns (likely routing noise)
        if len(content.strip()) < 20:
            continue

        cumulative += f"\n[{turn.source}]: {content}\n"
        substantive_index += 1

        score = await score_single_turn(
            task_text=task_meta["task"],
            rubric=task_meta.get("eval_rubric", "General quality"),
            cumulative_text=cumulative,
            turn_index=substantive_index,
        )
        scores.append(score)

    return scores
