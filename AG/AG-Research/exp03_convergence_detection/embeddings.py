"""
Convergence Detection via Claim Extraction + Jaccard Similarity
===============================================================
No embedding API needed - uses LLM claim extraction + set similarity.

Process:
1. For each turn, extract key claims (bullet points)
2. Compare claim sets between consecutive rounds using Jaccard similarity
3. Convergence = similarity > θ for K consecutive rounds
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import MODEL
from experiment_utils import RunResult, TurnRecord, _make_client


CLAIM_EXTRACTION_PROMPT = """Extract the key claims and assertions from this text as a bullet list.
Each claim should be a short, self-contained statement (one sentence).
Return ONLY the bullet points, one per line, starting with "- ".

Text:
{text}
"""


async def extract_claims(text: str) -> set[str]:
    """Extract key claims from text using LLM."""
    if not text.strip():
        return set()

    client = _make_client(MODEL)
    from autogen_core.models import UserMessage

    try:
        prompt = CLAIM_EXTRACTION_PROMPT.format(text=text[:2000])
        result = await client.create(messages=[UserMessage(content=prompt, source="user")])
        response = str(result.content)

        claims = set()
        for line in response.strip().split("\n"):
            line = line.strip()
            if line.startswith("- "):
                claim = line[2:].strip().lower()
                claim = re.sub(r'[^\w\s]', '', claim)
                if len(claim) > 10:
                    claims.add(claim)

        return claims
    except Exception:
        return _extract_claims_heuristic(text)


def _extract_claims_heuristic(text: str) -> set[str]:
    """Fallback: extract key phrases without LLM."""
    sentences = re.split(r'[.!?]\s+', text)
    claims = set()
    for s in sentences:
        s = s.strip().lower()
        s = re.sub(r'[^\w\s]', '', s)
        if len(s) > 20:
            claims.add(s[:100])
    return claims


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def word_overlap_similarity(text_a: str, text_b: str) -> float:
    """Simple word overlap as backup similarity measure."""
    words_a = set(re.findall(r'\w{3,}', text_a.lower()))
    words_b = set(re.findall(r'\w{3,}', text_b.lower()))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


async def compute_convergence_curve(
    run: RunResult,
    use_llm: bool = False,
    theta: float = 0.6,
    k_consecutive: int = 2,
) -> dict:
    """Compute convergence curve for a single run.

    Returns:
        {
            "similarities": [float],    # Jaccard sim between consecutive agent turns
            "converged_at": int | None,  # Turn index where convergence detected
            "final_similarity": float,
        }
    """
    agent_turns = [t for t in run.turns if t.source != "user"]

    if len(agent_turns) < 2:
        return {"similarities": [], "converged_at": None, "final_similarity": 0.0}

    similarities = []
    prev_claims: set[str] | None = None

    for turn in agent_turns:
        if use_llm:
            claims = await extract_claims(turn.content)
        else:
            claims = _extract_claims_heuristic(turn.content)

        if prev_claims is not None:
            sim = jaccard_similarity(prev_claims, claims)
            similarities.append(sim)
        prev_claims = claims

    # Detect convergence: similarity > theta for k consecutive rounds
    converged_at = None
    consecutive = 0
    for i, sim in enumerate(similarities):
        if sim >= theta:
            consecutive += 1
            if consecutive >= k_consecutive:
                converged_at = i - k_consecutive + 2  # index of first in the streak
                break
        else:
            consecutive = 0

    return {
        "similarities": similarities,
        "converged_at": converged_at,
        "final_similarity": similarities[-1] if similarities else 0.0,
    }
