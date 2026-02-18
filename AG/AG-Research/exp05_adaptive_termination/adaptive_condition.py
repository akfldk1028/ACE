"""
Adaptive Termination Condition
==============================
Marginal utility: ΔU(t) = ΔQ(t) - λ·ΔC(t)
- ΔQ(t) = Q(t) - Q(t-1) = quality improvement at turn t
- ΔC(t) = per-turn cost (token count for this turn)
- λ = cost sensitivity parameter

ΔU(t) naturally converges to 0 as quality gains plateau while
per-turn cost remains roughly constant. When ΔU(t) ≤ 0 for
`patience` consecutive turns → STOP.

Implements FunctionalTermination compatible interface.
"""

import re
from dataclasses import dataclass, field


@dataclass
class AdaptiveTerminationState:
    """Track quality and cost across turns for adaptive termination."""

    lambda_cost: float = 0.1          # Cost sensitivity
    patience: int = 2                  # Consecutive declining turns before stop
    min_turns: int = 2                 # Minimum turns before considering stop

    epsilon: float = 0.0              # ΔU threshold (0 = strict non-positive)

    # Internal state
    _qualities: list[float] = field(default_factory=list)
    _costs: list[float] = field(default_factory=list)
    _delta_utilities: list[float] = field(default_factory=list)
    _decline_count: int = 0
    _turn_count: int = 0

    def _quality_proxy(self, text: str) -> float:
        """Compute quality proxy from text.

        Q = normalized(word_count × unique_word_ratio)
        Higher = more informative content.
        """
        words = re.findall(r'\w+', text.lower())
        if not words:
            return 0.0

        word_count = len(words)
        unique_ratio = len(set(words)) / word_count

        # Normalize: word_count capped at 500, scaled to [0, 10]
        q = min(word_count, 500) / 50.0 * unique_ratio
        return q

    def _cost_proxy(self, text: str, usage=None) -> float:
        """Compute cost from actual tokens (models_usage) or estimate from text."""
        if usage is not None:
            prompt = getattr(usage, "prompt_tokens", 0) or 0
            completion = getattr(usage, "completion_tokens", 0) or 0
            if prompt + completion > 0:
                return float(prompt + completion)
        return len(text) / 4.0

    def update(self, source: str, content: str, usage=None) -> bool:
        """Process a new turn and decide whether to stop.

        Computes ΔU(t) = ΔQ(t) - λ·ΔC(t).
        Returns True when ΔU(t) ≤ epsilon for `patience` consecutive turns.
        """
        if source == "user":
            return False

        self._turn_count += 1

        q = self._quality_proxy(content)
        c = self._cost_proxy(content, usage=usage)

        # Marginal quality improvement
        delta_q = q - self._qualities[-1] if self._qualities else q
        # Per-turn cost (= ΔC(t), already marginal)
        delta_c = c
        # Marginal utility
        delta_u = delta_q - self.lambda_cost * delta_c

        self._qualities.append(q)
        self._costs.append(c)
        self._delta_utilities.append(delta_u)

        # Don't terminate before min_turns
        if self._turn_count < self.min_turns:
            return False

        # Check for non-positive marginal utility
        if delta_u <= self.epsilon:
            self._decline_count += 1
        else:
            self._decline_count = 0

        return self._decline_count >= self.patience

    def should_terminate(self, messages) -> bool:
        """FunctionalTermination-compatible interface.

        Processes the LATEST message only (messages is cumulative list).
        """
        if not messages:
            return False

        msg = messages[-1]
        source = getattr(msg, "source", "unknown")
        content = str(getattr(msg, "content", ""))
        usage = getattr(msg, "models_usage", None)

        return self.update(source, content, usage=usage)

    def reset(self):
        """Reset state for a new run."""
        self._qualities.clear()
        self._costs.clear()
        self._delta_utilities.clear()
        self._decline_count = 0
        self._turn_count = 0

    @property
    def stats(self) -> dict:
        """Return current state statistics."""
        return {
            "turn_count": self._turn_count,
            "qualities": list(self._qualities),
            "costs": list(self._costs),
            "delta_utilities": list(self._delta_utilities),
            "decline_count": self._decline_count,
            "cumulative_cost": sum(self._costs),
            "final_delta_u": self._delta_utilities[-1] if self._delta_utilities else None,
        }
