"""Event-based, development-only usage accounting for CATS trajectories."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import math
from typing import Any, Literal

from .trajectory_features import trajectory_id_from_resume_key


USAGE_EVENT_SCHEMA = "ace.iclr2027.usage_event.v1"
USAGE_AVAILABILITY_SCHEMA = "ace.iclr2027.usage_availability.v1"
_EVENT_KINDS = frozenset(
    {
        "agent_inference",
        "selector_inference",
        "deterministic_control",
        "retry_attempt",
    }
)
_ATTEMPT_STATUSES = frozenset({"successful", "failed", "unavailable"})
VISIBLE_AGENT_TOKEN_BOUNDARY = (
    "Persisted non-user agent-turn input/output tokens only; excludes selector "
    "inference, deterministic control, failed retries, cached tokens, duration, "
    "and cost."
)


@dataclass(frozen=True)
class UsageEvent:
    """One attributable usage record, including explicit unavailable coverage."""

    schema_version: str
    event_kind: Literal[
        "agent_inference",
        "selector_inference",
        "deterministic_control",
        "retry_attempt",
    ]
    attempt_status: Literal["successful", "failed", "unavailable"]
    trajectory_id: str
    turn_index: int | None
    control_index: int | None
    retry_attempt: int | None
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    cached_tokens: int | None
    duration_sec: float | None
    cost_usd: float | None
    cumulative_visible_agent_tokens: int | None
    unavailable_reason: str | None

    def __post_init__(self) -> None:
        if self.schema_version != USAGE_EVENT_SCHEMA:
            raise ValueError("unsupported usage event schema")
        if self.event_kind not in _EVENT_KINDS:
            raise ValueError("unsupported usage event kind")
        if self.attempt_status not in _ATTEMPT_STATUSES:
            raise ValueError("unsupported usage attempt status")
        if not self.trajectory_id:
            raise ValueError("usage event trajectory ID is required")
        if (self.turn_index is None) == (self.control_index is None):
            raise ValueError("usage event must bind exactly one turn/control index")
        for value, label in (
            (self.turn_index, "turn index"),
            (self.control_index, "control index"),
            (self.retry_attempt, "retry attempt"),
        ):
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"usage event {label} is invalid")
        for value, label in (
            (self.duration_sec, "duration sec"),
            (self.cost_usd, "cost usd"),
        ):
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) < 0.0
            ):
                raise ValueError(f"usage event {label} is invalid")
        if self.event_kind == "retry_attempt":
            if self.retry_attempt is None or self.control_index != self.retry_attempt:
                raise ValueError("retry usage event lineage is invalid")
        elif self.retry_attempt is not None:
            raise ValueError("non-retry usage event has retry lineage")
        if not self.provider or not self.model:
            raise ValueError("usage event provider/model is required")
        for value, label in (
            (self.input_tokens, "input tokens"),
            (self.output_tokens, "output tokens"),
            (self.cached_tokens, "cached tokens"),
            (self.cumulative_visible_agent_tokens, "cumulative visible tokens"),
        ):
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"usage event {label} is invalid")
        if self.unavailable_reason is None and self.cost_usd is None:
            raise ValueError("usage event requires cost or unavailable reason")
        if self.unavailable_reason is not None and not self.unavailable_reason.strip():
            raise ValueError("usage event unavailable reason is invalid")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UsageAvailability:
    """Claim permissions and their explicit coverage boundary."""

    schema_version: str
    visible_agent_tokens: bool
    visible_agent_token_boundary: str
    invoice_grade_cost: bool
    total_compute: bool
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != USAGE_AVAILABILITY_SCHEMA:
            raise ValueError("unsupported usage availability schema")
        if not self.visible_agent_token_boundary:
            raise ValueError("visible-agent boundary is required")
        if any(not reason for reason in self.reasons):
            raise ValueError("usage availability reason is invalid")

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "reasons": list(self.reasons)}


@dataclass(frozen=True)
class UsageLedger:
    events: tuple[UsageEvent, ...]
    availability: UsageAvailability
    cumulative_visible_agent_tokens: Mapping[tuple[str, int], int]


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"validated transaction {label} is invalid")
    return value


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"validated transaction {label} is invalid")
    return value


def _nonnegative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"validated transaction {label} is invalid")
    return value


def _trajectory_id(
    transaction: Mapping[str, Any], trajectory_ids: Mapping[str, str] | None
) -> str:
    resume_identity = _nonempty_string(
        transaction.get("resume_identity_sha256"), "resume identity"
    )
    if trajectory_ids is not None:
        trajectory_id = trajectory_ids.get(resume_identity)
        if trajectory_id is None:
            raise ValueError("validated transaction trajectory ID is unavailable")
        return _nonempty_string(trajectory_id, "trajectory ID")
    return trajectory_id_from_resume_key(resume_identity)


def _provider(raw: Mapping[str, Any]) -> str:
    value = raw.get("provider")
    return value.strip() if isinstance(value, str) and value.strip() else "unavailable"


def _availability(events: Sequence[UsageEvent]) -> UsageAvailability:
    agent_events = [
        event
        for event in events
        if event.event_kind == "agent_inference" and event.attempt_status == "successful"
    ]
    visible_agent_tokens = bool(agent_events) and all(
        event.input_tokens is not None and event.output_tokens is not None
        for event in agent_events
    )
    reasons: list[str] = []
    if any(
        event.event_kind == "selector_inference"
        and event.attempt_status == "unavailable"
        for event in events
    ):
        reasons.append("selector_usage_unavailable")
    if any(
        event.event_kind == "deterministic_control"
        and event.attempt_status == "unavailable"
        for event in events
    ):
        reasons.append("deterministic_control_usage_unavailable")
    if any(event.provider == "unavailable" for event in events):
        reasons.append("provider_usage_unavailable")
    if any(event.cached_tokens is None for event in events):
        reasons.append("cached_token_usage_unavailable")
    if any(event.cost_usd is None for event in events):
        reasons.append("cost_usage_unavailable")
    if any(event.duration_sec is None for event in events):
        reasons.append("duration_usage_unavailable")
    if any(event.event_kind == "retry_attempt" for event in events):
        reasons.append("retry_usage_unavailable")
    if not visible_agent_tokens:
        reasons.append("visible_agent_token_usage_unavailable")
    claim_blocked = bool(reasons)
    return UsageAvailability(
        schema_version=USAGE_AVAILABILITY_SCHEMA,
        visible_agent_tokens=visible_agent_tokens,
        visible_agent_token_boundary=VISIBLE_AGENT_TOKEN_BOUNDARY,
        invoice_grade_cost=not claim_blocked,
        total_compute=not claim_blocked,
        reasons=tuple(reasons),
    )


_EVENT_KIND_ORDER = {
    "agent_inference": 0,
    "retry_attempt": 1,
    "selector_inference": 2,
    "deterministic_control": 3,
}


def _usage_event_identity(event: UsageEvent) -> tuple[object, ...]:
    return (
        event.trajectory_id,
        event.event_kind,
        event.attempt_status,
        event.turn_index,
        event.control_index,
        event.retry_attempt,
    )


def _canonical_usage_events(events: Sequence[UsageEvent]) -> tuple[UsageEvent, ...]:
    identities: set[tuple[object, ...]] = set()
    for event in events:
        identity = _usage_event_identity(event)
        if identity in identities:
            raise ValueError("duplicate usage event identity")
        identities.add(identity)
    return tuple(
        sorted(
            events,
            key=lambda event: (
                event.trajectory_id,
                _EVENT_KIND_ORDER[event.event_kind],
                -1 if event.turn_index is None else event.turn_index,
                -1 if event.control_index is None else event.control_index,
                -1 if event.retry_attempt is None else event.retry_attempt,
            ),
        )
    )


def build_usage_ledger(
    transactions: Sequence[Mapping[str, Any]],
    *,
    trajectory_ids: Mapping[str, str] | None = None,
) -> UsageLedger:
    """Build immutable usage events from validated development transactions."""

    events: list[UsageEvent] = []
    cumulative: dict[tuple[str, int], int] = {}
    for transaction in transactions:
        raw = _mapping(transaction.get("raw"), "raw payload")
        result = _mapping(raw.get("result"), "raw result")
        trajectory_id = _trajectory_id(transaction, trajectory_ids)
        model = _nonempty_string(raw.get("model"), "model")
        provider = _provider(raw)
        total_visible_tokens = 0
        turns = result.get("turns")
        if isinstance(turns, (str, bytes)) or not isinstance(turns, Sequence):
            raise ValueError("validated transaction turns are invalid")
        for turn in turns:
            turn_row = _mapping(turn, "turn")
            if str(turn_row.get("source") or "").lower() == "user":
                continue
            turn_index = _nonnegative_int(turn_row.get("index"), "turn index")
            input_tokens = _nonnegative_int(turn_row.get("tokens_in"), "input tokens")
            output_tokens = _nonnegative_int(turn_row.get("tokens_out"), "output tokens")
            total_visible_tokens += input_tokens + output_tokens
            cumulative[(trajectory_id, turn_index)] = total_visible_tokens
            events.append(
                UsageEvent(
                    schema_version=USAGE_EVENT_SCHEMA,
                    event_kind="agent_inference",
                    attempt_status="successful",
                    trajectory_id=trajectory_id,
                    turn_index=turn_index,
                    control_index=None,
                    retry_attempt=None,
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cached_tokens=None,
                    duration_sec=None,
                    cost_usd=None,
                    cumulative_visible_agent_tokens=total_visible_tokens,
                    unavailable_reason="cached_token_duration_and_cost_usage_unavailable",
                )
            )
        errors = transaction.get("errors")
        if isinstance(errors, (str, bytes)) or not isinstance(errors, Sequence):
            raise ValueError("validated transaction errors are invalid")
        for error in errors:
            error_row = _mapping(error, "error lineage")
            attempt = _nonnegative_int(error_row.get("attempt"), "retry attempt")
            if attempt == 0:
                raise ValueError("validated transaction retry attempt is invalid")
            _nonempty_string(error_row.get("error"), "retry error")
            events.append(
                UsageEvent(
                    schema_version=USAGE_EVENT_SCHEMA,
                    event_kind="retry_attempt",
                    attempt_status="failed",
                    trajectory_id=trajectory_id,
                    turn_index=None,
                    control_index=attempt,
                    retry_attempt=attempt,
                    provider=provider,
                    model=model,
                    input_tokens=None,
                    output_tokens=None,
                    cached_tokens=None,
                    duration_sec=None,
                    cost_usd=None,
                    cumulative_visible_agent_tokens=None,
                    unavailable_reason="retry_usage_unavailable",
                )
            )
        for event_kind, reason in (
            ("selector_inference", "selector_usage_unavailable"),
            ("deterministic_control", "deterministic_control_usage_unavailable"),
        ):
            events.append(
                UsageEvent(
                    schema_version=USAGE_EVENT_SCHEMA,
                    event_kind=event_kind,
                    attempt_status="unavailable",
                    trajectory_id=trajectory_id,
                    turn_index=None,
                    control_index=0,
                    retry_attempt=None,
                    provider="unavailable",
                    model="unavailable",
                    input_tokens=None,
                    output_tokens=None,
                    cached_tokens=None,
                    duration_sec=None,
                    cost_usd=None,
                    cumulative_visible_agent_tokens=None,
                    unavailable_reason=reason,
                )
            )
    canonical_events = _canonical_usage_events(events)
    return UsageLedger(
        events=canonical_events,
        availability=_availability(canonical_events),
        cumulative_visible_agent_tokens=cumulative,
    )


def summarize_usage(transactions: Sequence[Mapping[str, Any]]) -> UsageAvailability:
    """Return claim availability without turning unavailable coverage into zero."""

    return build_usage_ledger(transactions).availability


__all__ = (
    "USAGE_AVAILABILITY_SCHEMA",
    "USAGE_EVENT_SCHEMA",
    "UsageAvailability",
    "UsageEvent",
    "UsageLedger",
    "VISIBLE_AGENT_TOKEN_BOUNDARY",
    "build_usage_ledger",
    "summarize_usage",
)
