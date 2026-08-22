"""Parse-gated termination conditions for architecture review teams."""

from __future__ import annotations

from collections.abc import Sequence

from autogen_agentchat.base import TerminatedException, TerminationCondition
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    StopMessage,
    TextMessage,
)

from .review_state import parse_review_state


class ParseGatedSignalTermination(TerminationCondition):
    """Stop only on a parse-valid terminal state from an authorized source."""

    def __init__(
        self,
        *,
        signals: Sequence[str],
        sources: Sequence[str],
        allowed_evidence_ids: Sequence[str],
        required_prior_sources: Sequence[str] = (),
    ) -> None:
        self._signals = frozenset(signals)
        self._sources = frozenset(sources)
        if not self._signals or any(not signal for signal in self._signals):
            raise ValueError("termination signals must be nonempty")
        if not self._sources or any(not source for source in self._sources):
            raise ValueError("termination sources must be nonempty")
        self._allowed_evidence_ids = frozenset(allowed_evidence_ids)
        if not self._allowed_evidence_ids or any(
            not evidence_id for evidence_id in self._allowed_evidence_ids
        ):
            raise ValueError("allowed evidence IDs must be nonempty")
        self._required_prior_sources = frozenset(required_prior_sources)
        if any(not source for source in self._required_prior_sources):
            raise ValueError("required prior sources must be nonempty strings")
        self._observed_sources: set[str] = set()
        self._terminated = False

    @property
    def terminated(self) -> bool:
        return self._terminated

    async def __call__(
        self,
        messages: Sequence[BaseAgentEvent | BaseChatMessage],
    ) -> StopMessage | None:
        if self._terminated:
            raise TerminatedException("Termination condition has already been reached")
        self._observed_sources.update(
            message.source for message in messages if isinstance(message, TextMessage)
        )
        latest = next(
            (
                message
                for message in reversed(messages)
                if isinstance(message, BaseChatMessage)
            ),
            None,
        )
        if latest is None or latest.source not in self._sources:
            return None
        if not self._required_prior_sources.issubset(self._observed_sources):
            return None
        content = latest.to_text()
        lines = content.rstrip().splitlines()
        if not lines or lines[-1] not in self._signals:
            return None
        parsed = parse_review_state(
            content,
            known_evidence_ids=self._allowed_evidence_ids,
        )
        if (
            not parsed.complete
            or parsed.state.recommended_decision
            not in {"STOP_ACCEPT", "STOP_REJECT"}
        ):
            return None
        self._terminated = True
        return StopMessage(
            content="Parse-valid terminal architecture review state received",
            source=type(self).__name__,
        )

    async def reset(self) -> None:
        self._terminated = False
        self._observed_sources.clear()


__all__ = ["ParseGatedSignalTermination"]
