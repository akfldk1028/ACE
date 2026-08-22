"""Deterministic, leakage-safe policy replay for the development gate.

The module consumes only the frozen Exp08 development snapshot, Task 3 dataset,
Task 4 usage ledger, and Task 5 model artifacts.  Non-oracle policies receive a
``RuntimePrefix`` that cannot contain private quality/future fields.  Private
labels are joined only after every stop selection has been fixed; the sole
exception is the explicitly named hindsight oracle.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import stat
from types import MappingProxyType
from typing import Any, Protocol

from . import cats as cats_module
from .artifact_receipts import verify_artifact_receipt
from .cats import admissibility_guard, finite_sample_quantile, load_frozen_dataset
from .io import canonical_json, sha256_json, write_json_atomic, write_jsonl_atomic
from .protocol import PILOT_TERMINAL_SIGNALS
from .study_contract import StudyContract
from .secure_files import read_authenticated_file
from .trajectory_features import trajectory_id_from_resume_key
from .trajectory_ingest import (
    DEVELOPMENT_SNAPSHOT_SCHEMA,
    load_development_snapshot,
)
from .usage_ledger import (
    USAGE_AVAILABILITY_SCHEMA,
    USAGE_EVENT_SCHEMA,
    VISIBLE_AGENT_TOKEN_BOUNDARY,
    UsageEvent,
)


DEVELOPMENT_GATE_SCHEMA = "ace.iclr2027.development_gate.v1"
AUTHORIZED_PARTITION = "development_gate"
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 20260819
EXPECTED_TRAJECTORIES = 180
EXPECTED_REPLAY_ROWS = 1_980

REPLAY_IMPLEMENTATION_FILES = (
    "config.py",
    "iclr2027/__init__.py",
    "iclr2027/architecture_metrics.py",
    "iclr2027/artifact_receipts.py",
    "iclr2027/audit.py",
    "iclr2027/cats.py",
    "iclr2027/exp08.py",
    "iclr2027/io.py",
    "iclr2027/pilot_gate.py",
    "iclr2027/policy_replay.py",
    "iclr2027/prompts.py",
    "iclr2027/protocol.py",
    "iclr2027/review_state.py",
    "iclr2027/run_manifest.py",
    "iclr2027/schema.py",
    "iclr2027/study_contract.py",
    "iclr2027/trajectory_features.py",
    "iclr2027/trajectory_ingest.py",
    "iclr2027/usage_ledger.py",
    "iclr2027/validators.py",
    "replay_exp09_policies.py",
)

EXPECTED_INPUT_SHA256 = MappingProxyType(
    {
        "snapshot_receipt.json": (
            "63556ffe60f0cfbbc7f5bea4f2d75e4bbafa67566a3bd9a8f61d22ad298b5a4d"
        ),
        "feature_manifest.json": (
            "7afe02f50c7b179c659b19042413d45d6940fa68444831359177e422262136a1"
        ),
        "runtime_features.jsonl": (
            "b7876d535316e31bdb00a5c514fba6ab0fa1ea5c8029dd6c62ed8e5d6f91d45f"
        ),
        "private_labels.jsonl": (
            "3adc2b1afe484926d1825d34211bf86b5089af742868d0935c45ba3e7503a967"
        ),
        "group_assignments.json": (
            "77b7caf3369f429ff9aefb7636192cfd3476f3ab8b5cd873b230e9904d2b52c4"
        ),
        "usage_events.jsonl": (
            "01854249bac9c5d476e351f45035013c0a090dd783e5f4047c92f824dbf1f048"
        ),
        "claim_availability.json": (
            "8bb7844c2a6f3f6c83944698f94d9933d151e07ca959a4c7202d63d7a6db1286"
        ),
        "model_registry.json": (
            "c30e5abd4b82ac652ae684376251b8b0bd836f28ebe84e8c815180f16ab702d8"
        ),
        "semantic_determinism.json": (
            "2584b1438e20e60571f38042ef3ac7f291dff47f52406c354db97a3a0a30658f"
        ),
    }
)

KEYWORD_SIGNALS = PILOT_TERMINAL_SIGNALS
_PRIVATE_DECISION_FIELDS = frozenset(
    {
        "beneficial_future",
        "condition",
        "final_outcome",
        "final_quality",
        "final_token_count",
        "final_tokens",
        "final_trajectory_length",
        "final_turn_count",
        "future_max_quality",
        "future_quality",
        "gold_issue",
        "mutation_family",
        "oracle_quality",
        "quality_t",
        "raw_pnu",
    }
)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")

POLICY_PARAMETERS: dict[str, dict[str, Any]] = {
    "natural": {"selection": "full_natural_trajectory"},
    "max_cap": {"max_agent_turns": 3},
    "keyword": {
        "match": "exact_final_line",
        "signals": {
            pattern: tuple(sorted(signals))
            for pattern, signals in sorted(KEYWORD_SIGNALS.items())
        },
    },
    "lexical_du": {
        "cost_proxy": {
            "actual_usage": (
                "prompt_tokens + completion_tokens when their sum is positive"
            ),
            "fallback": "len(text) / 4",
        },
        "delta_utility": "delta_quality - lambda_cost * cost",
        "epsilon": 0.0,
        "lambda_cost": 0.1,
        "min_turns": 2,
        "patience": 2,
        "quality_proxy": {
            "empty_text": 0.0,
            "formula": "min(word_count, 500) / 50 * unique_word_ratio",
            "tokenization": "lowercase regex \\w+",
            "unique_word_ratio": "unique_word_count / word_count",
        },
    },
    "semantic_patience": {"cosine_similarity_gte": 0.85, "patience": 2},
    "logistic": {
        "hard_guard": False,
        "p_improve_lt": 0.5,
        "patience": 2,
        "variant": "cats-logistic",
    },
    "uncalibrated_histgb": {
        "hard_guard": False,
        "p_improve_lt": 0.5,
        "patience": 2,
        "variant": "cats-primary",
    },
    "state_conformal": {
        "alpha": 0.10,
        "calibration_unit": "positive_calibration_row",
        "comparison": "1-p_improve > q_alpha",
        "finite_sample_rule": "ceil((n+1)*(1-alpha)) order statistic",
        "hard_guard": True,
        "patience": 2,
        "variant": "cats-primary",
    },
    "cats": {
        "alpha": 0.10,
        "calibration_unit": (
            "maximum_positive_nonconformity_per_calibration_trajectory"
        ),
        "comparison": "1-p_improve > q_alpha",
        "epsilon": 0.02,
        "hard_guard": True,
        "patience": 2,
        "variant": "cats-primary",
    },
    "cats_no_guard": {
        "alpha": 0.10,
        "calibration_unit": (
            "maximum_positive_nonconformity_per_calibration_trajectory"
        ),
        "comparison": "1-p_improve > q_alpha",
        "epsilon": 0.02,
        "hard_guard": False,
        "patience": 2,
        "variant": "cats-primary",
    },
    "oracle_peak": {"selection": "earliest_maximum_quality_prefix"},
}


@dataclass(frozen=True)
class RuntimePrefix:
    """The complete and only interface visible to a non-oracle policy."""

    trajectory_id: str
    turn_index: int
    pattern: str
    content: str
    turn_tokens: int
    cumulative_visible_tokens: int
    message_hash: str
    runtime_state: Mapping[str, object]
    histgb_p_improve: float
    logistic_p_improve: float
    turn_tokens_from_usage: bool = True

    def __post_init__(self) -> None:
        if type(self.turn_index) is not int or self.turn_index <= 0:
            raise ValueError("runtime turn index must be a positive native integer")
        if type(self.turn_tokens) is not int or self.turn_tokens < 0:
            raise ValueError("runtime turn token count is invalid")
        if type(self.turn_tokens_from_usage) is not bool:
            raise ValueError("runtime turn token provenance must be a native boolean")
        if (
            type(self.cumulative_visible_tokens) is not int
            or self.cumulative_visible_tokens < self.turn_tokens
        ):
            raise ValueError("runtime cumulative token count is invalid")
        if not isinstance(self.runtime_state, Mapping):
            raise TypeError("runtime state must be a mapping")
        forbidden = _PRIVATE_DECISION_FIELDS & set(self.runtime_state)
        if forbidden:
            raise ValueError("private/future fields cannot enter policy decisions")
        if not _SHA256.fullmatch(self.message_hash):
            raise ValueError("runtime message hash must be a lowercase SHA-256")
        for value in (self.histgb_p_improve, self.logistic_p_improve):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or not 0.0 <= float(value) <= 1.0
            ):
                raise ValueError("runtime probabilities must be finite within [0, 1]")
        object.__setattr__(self, "runtime_state", MappingProxyType(dict(self.runtime_state)))


@dataclass(frozen=True)
class RuntimeTrajectory:
    """Immutable source trajectory with no private outcomes."""

    trajectory_id: str
    group_id: str
    site_ref: str
    case_id: str
    condition: str
    mutation_family: str
    repeat: int
    pattern: str
    prefixes: tuple[RuntimePrefix, ...]

    def __post_init__(self) -> None:
        if not self.prefixes:
            raise ValueError("runtime trajectory must contain an agent prefix")
        expected = tuple(range(1, len(self.prefixes) + 1))
        if tuple(prefix.turn_index for prefix in self.prefixes) != expected:
            raise ValueError("runtime prefixes must be complete and ordered")
        if any(prefix.trajectory_id != self.trajectory_id for prefix in self.prefixes):
            raise ValueError("runtime prefix trajectory identity mismatch")
        if any(prefix.pattern != self.pattern for prefix in self.prefixes):
            raise ValueError("runtime prefix pattern mismatch")
        prior = 0
        for prefix in self.prefixes:
            if prefix.cumulative_visible_tokens != prior + prefix.turn_tokens:
                raise ValueError("runtime prefix token lineage mismatch")
            prior = prefix.cumulative_visible_tokens


@dataclass(frozen=True)
class EvaluationLabels:
    """Private post-decision quality labels, physically separate from runtime."""

    qualities: tuple[float, ...]
    beneficial_future: tuple[bool, ...]

    def __post_init__(self) -> None:
        if not self.qualities or len(self.qualities) != len(self.beneficial_future):
            raise ValueError("evaluation labels must have equal nonempty sequences")
        if any(not math.isfinite(float(value)) for value in self.qualities):
            raise ValueError("evaluation qualities must be finite")
        if any(type(value) is not bool for value in self.beneficial_future):
            raise ValueError("beneficial-future labels must be native booleans")
        if self.beneficial_future[-1]:
            raise ValueError("terminal beneficial-future label must be false")


@dataclass(frozen=True)
class StopDecision:
    stop: bool
    reason: str
    p_improve: float | None = None
    calibrated_no_future_gain: bool | None = None
    admissible: bool | None = None
    streak: int = 0


@dataclass(frozen=True)
class StopSelection:
    stop_turn: int
    reason: str


@dataclass(frozen=True)
class ReplayOutcome:
    trajectory_id: str
    policy: str
    group_id: str
    site_ref: str
    case_id: str
    condition: str
    mutation_family: str
    repeat: int
    pattern: str
    stop_reason: str
    stop_turn: int
    natural_turns: int
    stopped_quality: float
    natural_quality: float
    full_quality: float
    oracle_quality: float
    oracle_stop_turn: int
    visible_agent_tokens: int
    natural_visible_agent_tokens: int
    full_visible_agent_tokens: int
    visible_agent_token_reduction: float
    quality_delta: float
    hard_guard_admissible: bool
    unsafe_stop: bool
    premature_stop: bool
    empirical_trajectory_covered: bool
    overshoot_turns: int
    oracle_regret: float
    message_hashes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["message_hashes"] = list(self.message_hashes)
        return payload


@dataclass(frozen=True)
class StateConformalDerivation:
    alpha: float
    finite_sample_rank: int
    q_alpha: float
    score_count: int
    scores_sha256: str
    calibration_row_ids_sha256: str
    positive_row_ids_sha256: str
    source_partition: str
    probability_variant: str
    label_rule: str
    comparison: str
    empirical_calibration_coverage: float

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if not math.isfinite(self.q_alpha):
            payload["q_alpha"] = "infinity"
        return payload


class Policy(Protocol):
    name: str

    def observe(self, prefix: RuntimePrefix) -> StopDecision: ...


class NaturalPolicy:
    name = "natural"

    def observe(self, prefix: RuntimePrefix) -> StopDecision:
        return StopDecision(False, "continue")


class MaxCapPolicy:
    name = "max_cap"

    def __init__(self, *, max_agent_turns: int = 3) -> None:
        self.max_agent_turns = max_agent_turns

    def observe(self, prefix: RuntimePrefix) -> StopDecision:
        stop = prefix.turn_index >= self.max_agent_turns
        return StopDecision(stop, "max_cap" if stop else "continue")


class KeywordPolicy:
    name = "keyword"

    def observe(self, prefix: RuntimePrefix) -> StopDecision:
        lines = prefix.content.rstrip().splitlines()
        final_line = lines[-1] if lines else ""
        stop = final_line in KEYWORD_SIGNALS.get(prefix.pattern, frozenset())
        return StopDecision(stop, "keyword" if stop else "continue")


class LexicalDeltaUtilityPolicy:
    name = "lexical_du"

    def __init__(
        self,
        *,
        lambda_cost: float = 0.1,
        epsilon: float = 0.0,
        min_turns: int = 2,
        patience: int = 2,
    ) -> None:
        self.lambda_cost = lambda_cost
        self.epsilon = epsilon
        self.min_turns = min_turns
        self.patience = patience
        self._prior_quality: float | None = None
        self._streak = 0

    @staticmethod
    def _quality_proxy(text: str) -> float:
        words = re.findall(r"\w+", text.lower())
        if not words:
            return 0.0
        unique_ratio = len(set(words)) / len(words)
        return min(len(words), 500) / 50.0 * unique_ratio

    @staticmethod
    def _cost_proxy(text: str, usage_tokens: int | None) -> float:
        if usage_tokens is not None and usage_tokens > 0:
            return float(usage_tokens)
        return len(text) / 4.0

    def observe(self, prefix: RuntimePrefix) -> StopDecision:
        quality = self._quality_proxy(prefix.content)
        delta_quality = (
            quality if self._prior_quality is None else quality - self._prior_quality
        )
        self._prior_quality = quality
        usage_tokens = prefix.turn_tokens if prefix.turn_tokens_from_usage else None
        cost = self._cost_proxy(prefix.content, usage_tokens)
        delta_utility = delta_quality - self.lambda_cost * cost
        if prefix.turn_index < self.min_turns:
            return StopDecision(False, "continue", streak=self._streak)
        self._streak = self._streak + 1 if delta_utility <= self.epsilon else 0
        stop = self._streak >= self.patience
        return StopDecision(
            stop,
            "lexical_du" if stop else "continue",
            streak=self._streak,
        )


class SemanticPatiencePolicy:
    name = "semantic_patience"

    def __init__(self, *, threshold: float = 0.85, patience: int = 2) -> None:
        self.threshold = threshold
        self.patience = patience
        self._streak = 0

    def observe(self, prefix: RuntimePrefix) -> StopDecision:
        distance = prefix.runtime_state.get("tfidf_distance_prev")
        if (
            prefix.turn_index == 1
            or isinstance(distance, bool)
            or not isinstance(distance, (int, float))
            or not math.isfinite(float(distance))
        ):
            stable = False
        else:
            stable = 1.0 - float(distance) >= self.threshold
        self._streak = self._streak + 1 if stable else 0
        stop = self._streak >= self.patience
        return StopDecision(
            stop,
            "semantic_patience" if stop else "continue",
            streak=self._streak,
        )


class LearnedThresholdPolicy:
    def __init__(self, *, name: str, probability_field: str, patience: int = 2) -> None:
        self.name = name
        self.probability_field = probability_field
        self.patience = patience
        self._streak = 0

    def observe(self, prefix: RuntimePrefix) -> StopDecision:
        probability = float(getattr(prefix, self.probability_field))
        self._streak = self._streak + 1 if probability < 0.5 else 0
        stop = self._streak >= self.patience
        return StopDecision(
            stop,
            self.name if stop else "continue",
            p_improve=probability,
            streak=self._streak,
        )


class ConformalPolicy:
    def __init__(
        self,
        *,
        name: str,
        q_alpha: float,
        patience: int = 2,
        hard_guard: bool,
    ) -> None:
        if isinstance(q_alpha, bool) or not isinstance(q_alpha, (int, float)):
            raise TypeError("q_alpha must be numeric")
        if math.isnan(float(q_alpha)) or float(q_alpha) < 0.0:
            raise ValueError("q_alpha must be nonnegative")
        self.name = name
        self.q_alpha = float(q_alpha)
        self.patience = patience
        self.hard_guard = hard_guard
        self._streak = 0

    def observe(self, prefix: RuntimePrefix) -> StopDecision:
        probability = float(prefix.histgb_p_improve)
        no_gain = 1.0 - probability > self.q_alpha
        admissible = admissibility_guard(prefix.runtime_state)
        eligible = no_gain and (admissible or not self.hard_guard)
        self._streak = self._streak + 1 if eligible else 0
        stop = self._streak >= self.patience
        return StopDecision(
            stop,
            self.name if stop else "continue",
            p_improve=probability,
            calibrated_no_future_gain=no_gain,
            admissible=admissible,
            streak=self._streak,
        )


class OraclePeakPolicy:
    name = "oracle_peak"

    def observe(
        self,
        prefix: RuntimePrefix,
        *,
        future_quality: Sequence[float],
    ) -> StopDecision:
        qualities = tuple(float(value) for value in future_quality)
        if prefix.turn_index > len(qualities) or not qualities:
            raise ValueError("oracle future quality does not match runtime prefixes")
        earliest_peak = qualities.index(max(qualities)) + 1
        stop = prefix.turn_index == earliest_peak
        return StopDecision(stop, "oracle_peak" if stop else "continue")


def _natural_factory() -> NaturalPolicy:
    return NaturalPolicy()


def _max_cap_factory() -> MaxCapPolicy:
    return MaxCapPolicy(max_agent_turns=3)


def _keyword_factory() -> KeywordPolicy:
    return KeywordPolicy()


def _lexical_factory() -> LexicalDeltaUtilityPolicy:
    return LexicalDeltaUtilityPolicy(
        lambda_cost=0.1,
        epsilon=0.0,
        min_turns=2,
        patience=2,
    )


def _semantic_factory() -> SemanticPatiencePolicy:
    return SemanticPatiencePolicy(threshold=0.85, patience=2)


def _logistic_factory() -> LearnedThresholdPolicy:
    return LearnedThresholdPolicy(
        name="logistic",
        probability_field="logistic_p_improve",
        patience=2,
    )


def _histgb_factory() -> LearnedThresholdPolicy:
    return LearnedThresholdPolicy(
        name="uncalibrated_histgb",
        probability_field="histgb_p_improve",
        patience=2,
    )


def _state_conformal_factory(*, q_alpha: float = 0.0) -> ConformalPolicy:
    return ConformalPolicy(
        name="state_conformal",
        q_alpha=q_alpha,
        patience=2,
        hard_guard=True,
    )


def _cats_factory(*, q_alpha: float = 0.0) -> ConformalPolicy:
    return ConformalPolicy(
        name="cats",
        q_alpha=q_alpha,
        patience=2,
        hard_guard=True,
    )


def _cats_no_guard_factory(*, q_alpha: float = 0.0) -> ConformalPolicy:
    return ConformalPolicy(
        name="cats_no_guard",
        q_alpha=q_alpha,
        patience=2,
        hard_guard=False,
    )


def _oracle_factory() -> OraclePeakPolicy:
    return OraclePeakPolicy()


POLICY_REGISTRY: dict[str, Callable[..., Any]] = {
    "natural": _natural_factory,
    "max_cap": _max_cap_factory,
    "keyword": _keyword_factory,
    "lexical_du": _lexical_factory,
    "semantic_patience": _semantic_factory,
    "logistic": _logistic_factory,
    "uncalibrated_histgb": _histgb_factory,
    "state_conformal": _state_conformal_factory,
    "cats": _cats_factory,
    "cats_no_guard": _cats_no_guard_factory,
    "oracle_peak": _oracle_factory,
}


def decide_stop(
    trajectory: RuntimeTrajectory,
    policy: Policy | OraclePeakPolicy,
    *,
    future_quality: Sequence[float] | None = None,
) -> StopSelection:
    """Fix one stop prefix without exposing evaluation labels to non-oracles."""

    is_oracle = isinstance(policy, OraclePeakPolicy)
    if is_oracle and future_quality is None:
        raise TypeError("oracle policy requires future_quality")
    if not is_oracle and future_quality is not None:
        raise TypeError("only oracle policy may receive future_quality")
    for prefix in trajectory.prefixes:
        decision = (
            policy.observe(prefix, future_quality=future_quality)  # type: ignore[call-arg]
            if is_oracle
            else policy.observe(prefix)
        )
        if decision.stop:
            return StopSelection(prefix.turn_index, decision.reason)
    return StopSelection(len(trajectory.prefixes), "natural_fallback")


def _evaluate_selection(
    trajectory: RuntimeTrajectory,
    policy_name: str,
    selection: StopSelection,
    labels: EvaluationLabels,
) -> ReplayOutcome:
    if len(labels.qualities) != len(trajectory.prefixes):
        raise ValueError("runtime/evaluation trajectory length mismatch")
    stop_offset = selection.stop_turn - 1
    stop_prefix = trajectory.prefixes[stop_offset]
    natural_prefix = trajectory.prefixes[-1]
    oracle_quality = max(labels.qualities)
    oracle_stop_turn = labels.qualities.index(oracle_quality) + 1
    stopped_quality = labels.qualities[stop_offset]
    full_quality = labels.qualities[-1]
    full_tokens = natural_prefix.cumulative_visible_tokens
    visible_tokens = stop_prefix.cumulative_visible_tokens
    reduction = 0.0 if full_tokens == 0 else (full_tokens - visible_tokens) / full_tokens
    unsafe = labels.beneficial_future[stop_offset]
    return ReplayOutcome(
        trajectory_id=trajectory.trajectory_id,
        policy=policy_name,
        group_id=trajectory.group_id,
        site_ref=trajectory.site_ref,
        case_id=trajectory.case_id,
        condition=trajectory.condition,
        mutation_family=trajectory.mutation_family,
        repeat=trajectory.repeat,
        pattern=trajectory.pattern,
        stop_reason=selection.reason,
        stop_turn=selection.stop_turn,
        natural_turns=len(trajectory.prefixes),
        stopped_quality=stopped_quality,
        natural_quality=full_quality,
        full_quality=full_quality,
        oracle_quality=oracle_quality,
        oracle_stop_turn=oracle_stop_turn,
        visible_agent_tokens=visible_tokens,
        natural_visible_agent_tokens=full_tokens,
        full_visible_agent_tokens=full_tokens,
        visible_agent_token_reduction=reduction,
        quality_delta=stopped_quality - full_quality,
        hard_guard_admissible=admissibility_guard(stop_prefix.runtime_state),
        unsafe_stop=unsafe,
        premature_stop=selection.stop_turn < oracle_stop_turn,
        empirical_trajectory_covered=not unsafe,
        overshoot_turns=max(0, selection.stop_turn - oracle_stop_turn),
        oracle_regret=oracle_quality - stopped_quality,
        message_hashes=tuple(
            prefix.message_hash for prefix in trajectory.prefixes[: selection.stop_turn]
        ),
    )


def replay(
    trajectory: RuntimeTrajectory,
    policy: Policy | OraclePeakPolicy,
    *,
    evaluation_labels: EvaluationLabels,
) -> ReplayOutcome:
    """Select a source prefix, then join private outcomes for evaluation only."""

    if isinstance(policy, OraclePeakPolicy):
        selection = decide_stop(
            trajectory,
            policy,
            future_quality=evaluation_labels.qualities,
        )
    else:
        selection = decide_stop(trajectory, policy)
    return _evaluate_selection(trajectory, policy.name, selection, evaluation_labels)


def replay_registry(
    trajectory: RuntimeTrajectory,
    labels: EvaluationLabels,
    *,
    cats_q_alpha: float,
    state_q_alpha: float,
) -> tuple[ReplayOutcome, ...]:
    """Fix all policy selections before any post-decision outcome is evaluated."""

    selections: dict[str, StopSelection] = {}
    for name, factory in POLICY_REGISTRY.items():
        if name == "oracle_peak":
            continue
        if name == "cats" or name == "cats_no_guard":
            policy = factory(q_alpha=cats_q_alpha)
        elif name == "state_conformal":
            policy = factory(q_alpha=state_q_alpha)
        else:
            policy = factory()
        selections[name] = decide_stop(trajectory, policy)
    oracle = POLICY_REGISTRY["oracle_peak"]()
    selections["oracle_peak"] = decide_stop(
        trajectory,
        oracle,
        future_quality=labels.qualities,
    )
    return tuple(
        _evaluate_selection(trajectory, name, selections[name], labels)
        for name in POLICY_REGISTRY
    )


def derive_state_conformal(
    predictions: Sequence[Mapping[str, object]],
    labels_by_row: Mapping[str, Mapping[str, object]],
    *,
    alpha: float,
) -> StateConformalDerivation:
    """Derive the frozen state-unit ablation from calibration positives only."""

    calibration: list[tuple[str, float, bool]] = []
    for row in predictions:
        if row.get("partition") != "calibration":
            continue
        row_id = str(row.get("row_id") or "")
        label = labels_by_row.get(row_id)
        if not row_id or label is None:
            raise ValueError("calibration prediction/label identity mismatch")
        probability = row.get("p_improve")
        if (
            isinstance(probability, bool)
            or not isinstance(probability, (int, float))
            or not math.isfinite(float(probability))
            or not 0.0 <= float(probability) <= 1.0
        ):
            raise ValueError("calibration probability is invalid")
        beneficial = label.get("beneficial_future")
        if type(beneficial) is not bool:
            raise ValueError("calibration beneficial-future label is invalid")
        calibration.append((row_id, float(probability), beneficial))
    calibration.sort(key=lambda item: item[0])
    if not calibration:
        raise ValueError("calibration rows are empty")
    positive = tuple(item for item in calibration if item[2])
    if not positive:
        raise ValueError("positive calibration rows are empty")
    scores = tuple(1.0 - probability for _, probability, _ in positive)
    q_alpha = finite_sample_quantile(
        cats_module.np.asarray(scores, dtype=float),
        alpha=alpha,
    )
    rank = math.ceil((len(scores) + 1) * (1.0 - alpha))
    coverage = sum(score <= q_alpha for score in scores) / len(scores)
    return StateConformalDerivation(
        alpha=float(alpha),
        finite_sample_rank=rank,
        q_alpha=q_alpha,
        score_count=len(scores),
        scores_sha256=sha256_json(list(scores)),
        calibration_row_ids_sha256=sha256_json([item[0] for item in calibration]),
        positive_row_ids_sha256=sha256_json([item[0] for item in positive]),
        source_partition="calibration",
        probability_variant="cats-primary",
        label_rule="beneficial_future == true",
        comparison="1-p_improve > q_alpha",
        empirical_calibration_coverage=coverage,
    )


def _percentile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("percentile values must not be empty")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def site_cluster_bootstrap(
    rows: Sequence[Mapping[str, object]],
    *,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    """Bootstrap complete site clusters, never independent replay rows."""

    if type(draws) is not int or draws <= 0:
        raise ValueError("bootstrap draws must be a positive native integer")
    grouped: defaultdict[str, list[float]] = defaultdict(list)
    for row in rows:
        site_ref = row.get("site_ref")
        value = row.get("quality_delta")
        if not isinstance(site_ref, str) or not site_ref:
            raise ValueError("bootstrap row lacks site_ref")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            raise ValueError("bootstrap row quality delta is invalid")
        grouped[site_ref].append(float(value))
    site_refs = tuple(sorted(grouped))
    if len(site_refs) != 2:
        raise ValueError("development bootstrap requires exactly two site groups")
    generator = random.Random(seed)
    statistics: list[float] = []
    for _ in range(draws):
        sampled = tuple(site_refs[generator.randrange(2)] for _ in range(2))
        values = [value for site in sampled for value in grouped[site]]
        statistics.append(sum(values) / len(values))
    all_values = [value for site in site_refs for value in grouped[site]]
    return {
        "draws": draws,
        "seed": seed,
        "site_count": 2,
        "site_refs_sha256": sha256_json(list(site_refs)),
        "resampling_unit": "site_ref",
        "nested_clusters_kept_together": True,
        "statistic": "mean_quality_delta",
        "observed_mean": sum(all_values) / len(all_values),
        "lower_95": _percentile(statistics, 0.025),
        "upper_95": _percentile(statistics, 0.975),
        "distinct_draw_statistics": sorted(set(statistics)),
    }


def authorize_partition(
    partition: str,
    *,
    pre_read_hook: Callable[[], None] | None = None,
) -> None:
    """Reject every non-development-gate request before any input read."""

    if partition != AUTHORIZED_PARTITION:
        raise PermissionError("only the frozen development_gate partition is authorized")
    if pre_read_hook is not None:
        pre_read_hook()


def _is_reparse_or_link(path: Path) -> bool:
    try:
        item_stat = os.lstat(path)
    except OSError:
        return False
    attributes = getattr(item_stat, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    is_junction = getattr(path, "is_junction", lambda: False)
    return bool(
        stat.S_ISLNK(item_stat.st_mode)
        or attributes & reparse_flag
        or path.is_symlink()
        or is_junction()
    )


def _reject_link_components(path: Path, *, label: str) -> None:
    absolute = path.absolute()
    components = tuple(reversed((absolute, *absolute.parents)))
    for component in components:
        if os.path.lexists(component) and _is_reparse_or_link(component):
            raise ValueError(f"{label} contains a symlink or reparse point")


def safe_input_file(path: str | Path, *, label: str) -> Path:
    """Resolve one regular input file only after link-component rejection."""

    candidate = Path(path)
    _reject_link_components(candidate, label=label)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"{label} does not exist") from error
    _reject_link_components(resolved, label=label)
    if not resolved.is_file():
        raise ValueError(f"{label} must be a regular file")
    read_authenticated_file(candidate, label=label)
    return resolved


def _safe_input_directory(path: str | Path, *, label: str) -> Path:
    candidate = Path(path)
    _reject_link_components(candidate, label=label)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"{label} does not exist") from error
    _reject_link_components(resolved, label=label)
    if not resolved.is_dir():
        raise ValueError(f"{label} must be a regular directory")
    return resolved


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(
        read_authenticated_file(path, label=f"SHA-256 input {path.name}")
    ).hexdigest()


def _require_hash(path: Path, expected: str, *, label: str) -> str:
    observed = _sha256_file(path)
    if observed != expected:
        raise ValueError(f"{label} SHA-256 mismatch")
    return observed


def _read_canonical_json(path: Path, *, label: str) -> dict[str, Any]:
    artifact = read_authenticated_file(path, label=label)
    try:
        value = json.loads(artifact.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not readable JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    if artifact != (canonical_json(value) + "\n").encode("utf-8"):
        raise ValueError(f"{label} is not canonical JSON")
    return value


def _read_canonical_jsonl(path: Path, *, label: str) -> list[dict[str, Any]]:
    artifact = read_authenticated_file(path, label=label)
    try:
        text = artifact.decode("utf-8")
        values = [json.loads(line) for line in text.splitlines() if line]
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not readable JSONL") from error
    if any(not isinstance(value, dict) for value in values):
        raise ValueError(f"{label} rows must be objects")
    canonical = "".join(f"{canonical_json(value)}\n" for value in values).encode(
        "utf-8"
    )
    if canonical != artifact:
        raise ValueError(f"{label} is not canonical JSONL")
    return values


@dataclass(frozen=True)
class _ModelInputs:
    registry: Mapping[str, Any]
    primary_manifest: Mapping[str, Any]
    primary_predictions: tuple[Mapping[str, Any], ...]
    logistic_predictions: tuple[Mapping[str, Any], ...]
    source_hashes: Mapping[str, str]


def _load_models(models: Path) -> _ModelInputs:
    models = _safe_input_directory(models, label="model root")
    cats_module._directory_tree_digest(models)  # noqa: SLF001
    registry_path = safe_input_file(
        models / "model_registry.json", label="model registry"
    )
    _require_hash(
        registry_path,
        EXPECTED_INPUT_SHA256["model_registry.json"],
        label="model registry",
    )
    alias_path = safe_input_file(models / "registry.json", label="model registry alias")
    if read_authenticated_file(
        alias_path, label="model registry alias"
    ) != read_authenticated_file(registry_path, label="model registry"):
        raise ValueError("model registry compatibility alias mismatch")
    determinism_path = safe_input_file(
        models / "semantic_determinism.json",
        label="semantic determinism receipt",
    )
    _require_hash(
        determinism_path,
        EXPECTED_INPUT_SHA256["semantic_determinism.json"],
        label="semantic determinism receipt",
    )
    registry = cats_module._validate_bound_publication(models)  # noqa: SLF001
    source_hashes: dict[str, str] = {
        "models/model_registry.json": _sha256_file(registry_path),
        "models/registry.json": _sha256_file(alias_path),
        "models/semantic_determinism.json": _sha256_file(determinism_path),
    }
    entries = {str(entry["name"]): entry for entry in registry["variants"]}
    for entry in registry["variants"]:
        variant_root = models / str(entry["path"])
        for filename in (
            "classifier.joblib",
            "transformer.joblib",
            "manifest.json",
            "predictions.jsonl",
        ):
            artifact = safe_input_file(
                variant_root / filename,
                label=f"model artifact {entry['name']}/{filename}",
            )
            source_hashes[f"models/{entry['path']}/{filename}"] = _sha256_file(
                artifact
            )
    primary_entry = entries["cats-primary"]
    logistic_entry = entries["cats-logistic"]
    primary_root = models / str(primary_entry["path"])
    logistic_root = models / str(logistic_entry["path"])
    primary_manifest = _read_canonical_json(
        primary_root / "manifest.json", label="primary model manifest"
    )
    primary_predictions = tuple(
        _read_canonical_jsonl(
            primary_root / "predictions.jsonl", label="primary predictions"
        )
    )
    logistic_predictions = tuple(
        _read_canonical_jsonl(
            logistic_root / "predictions.jsonl", label="logistic predictions"
        )
    )
    for name, rows in (
        ("primary", primary_predictions),
        ("logistic", logistic_predictions),
    ):
        identities: set[str] = set()
        for row in rows:
            if set(row) != {"row_id", "trajectory_id", "partition", "p_improve"}:
                raise ValueError(f"{name} prediction schema mismatch")
            row_id = row["row_id"]
            probability = row["p_improve"]
            if not isinstance(row_id, str) or row_id in identities:
                raise ValueError(f"{name} prediction identity mismatch")
            if (
                isinstance(probability, bool)
                or not isinstance(probability, (int, float))
                or not math.isfinite(float(probability))
                or not 0.0 <= float(probability) <= 1.0
            ):
                raise ValueError(f"{name} prediction probability mismatch")
            identities.add(row_id)
        if len(rows) != 1_524:
            raise ValueError(f"{name} prediction census mismatch")
    return _ModelInputs(
        registry=registry,
        primary_manifest=primary_manifest,
        primary_predictions=primary_predictions,
        logistic_predictions=logistic_predictions,
        source_hashes=MappingProxyType(dict(sorted(source_hashes.items()))),
    )


@dataclass(frozen=True)
class _UsageInputs:
    events_by_turn: Mapping[tuple[str, int], UsageEvent]
    claim: Mapping[str, Any]
    source_hashes: Mapping[str, str]


def _load_usage(dataset: Path) -> _UsageInputs:
    usage_root = _safe_input_directory(dataset / "usage", label="usage root")
    events_path = safe_input_file(usage_root / "usage_events.jsonl", label="usage events")
    claim_path = safe_input_file(
        usage_root / "claim_availability.json", label="usage claim availability"
    )
    _require_hash(
        events_path,
        EXPECTED_INPUT_SHA256["usage_events.jsonl"],
        label="usage events",
    )
    _require_hash(
        claim_path,
        EXPECTED_INPUT_SHA256["claim_availability.json"],
        label="usage claim availability",
    )
    event_rows = _read_canonical_jsonl(events_path, label="usage events")
    expected_keys = {field.name for field in fields(UsageEvent)}
    events: list[UsageEvent] = []
    for row in event_rows:
        if set(row) != expected_keys or row.get("schema_version") != USAGE_EVENT_SCHEMA:
            raise ValueError("usage event schema mismatch")
        events.append(UsageEvent(**row))
    claim = _read_canonical_json(claim_path, label="usage claim availability")
    if (
        claim.get("schema_version") != USAGE_AVAILABILITY_SCHEMA
        or claim.get("usage_events_sha256") != _sha256_file(events_path)
        or claim.get("visible_agent_tokens") is not True
        or claim.get("visible_agent_token_boundary") != VISIBLE_AGENT_TOKEN_BOUNDARY
        or claim.get("invoice_grade_cost") is not False
        or claim.get("total_compute") is not False
    ):
        raise ValueError("usage claim availability mismatch")
    observed_counts = Counter(
        f"{event.event_kind}.{event.attempt_status}" for event in events
    )
    if dict(sorted(observed_counts.items())) != claim.get("event_counts"):
        raise ValueError("usage event census mismatch")
    by_turn: dict[tuple[str, int], UsageEvent] = {}
    for event in events:
        if event.event_kind != "agent_inference" or event.attempt_status != "successful":
            continue
        assert event.turn_index is not None
        key = (event.trajectory_id, event.turn_index)
        if key in by_turn:
            raise ValueError("duplicate visible-agent usage event")
        by_turn[key] = event
    if len(by_turn) != 1_524:
        raise ValueError("visible-agent usage event census mismatch")
    return _UsageInputs(
        events_by_turn=MappingProxyType(by_turn),
        claim=MappingProxyType(dict(claim)),
        source_hashes=MappingProxyType(
            {
                "dataset/usage/claim_availability.json": _sha256_file(claim_path),
                "dataset/usage/usage_events.jsonl": _sha256_file(events_path),
            }
        ),
    )


@dataclass(frozen=True)
class _SnapshotInputs:
    snapshot: Any
    receipt: Mapping[str, Any]
    source_hashes: Mapping[str, str]


def _load_snapshot(snapshot_path: Path) -> _SnapshotInputs:
    snapshot_path = safe_input_file(snapshot_path, label="development snapshot receipt")
    _require_hash(
        snapshot_path,
        EXPECTED_INPUT_SHA256["snapshot_receipt.json"],
        label="development snapshot receipt",
    )
    receipt = _read_canonical_json(snapshot_path, label="development snapshot receipt")
    receipt_payload = {
        key: value for key, value in receipt.items() if key != "receipt_sha256"
    }
    if (
        receipt.get("schema_version") != DEVELOPMENT_SNAPSHOT_SCHEMA
        or receipt.get("receipt_sha256") != sha256_json(receipt_payload)
        or receipt.get("transaction_count") != 450
        or receipt.get("pilot_gate_passed") is not False
    ):
        raise ValueError("development snapshot receipt mismatch")
    source_receipt = receipt.get("source_artifact_receipt")
    if not isinstance(source_receipt, Mapping):
        raise ValueError("development snapshot source receipt missing")
    project_root = Path(__file__).resolve().parents[1]
    source_root = _safe_input_directory(
        project_root / "results/exp08_architecture/pilot_full_v12_clean_recovery",
        label="development transaction root",
    )
    verify_artifact_receipt(source_receipt, root=source_root)
    snapshot = load_development_snapshot(source_root)
    expected_messages = {
        key: list(value) for key, value in sorted(snapshot.message_hashes.items())
    }
    if (
        receipt.get("message_hashes") != expected_messages
        or receipt.get("transaction_set_sha256") != snapshot.transaction_set_sha256
        or receipt.get("run_plan_sha256") != snapshot.run_plan_sha256
        or receipt.get("code_runtime_identity") != snapshot.code_runtime_identity
    ):
        raise ValueError("development snapshot semantic binding mismatch")
    return _SnapshotInputs(
        snapshot=snapshot,
        receipt=MappingProxyType(dict(receipt)),
        source_hashes=MappingProxyType(
            {
                "development_snapshot/snapshot_receipt.json": _sha256_file(
                    snapshot_path
                ),
                "development_snapshot/source_artifact_sha256": str(
                    source_receipt["artifact_sha256"]
                ),
                "development_snapshot/source_file_set_sha256": str(
                    source_receipt["file_set_sha256"]
                ),
            }
        ),
    )


def _dataset_source_hashes(dataset: Path) -> dict[str, str]:
    paths = {
        "dataset/feature_manifest.json": (
            dataset / "feature_manifest.json",
            EXPECTED_INPUT_SHA256["feature_manifest.json"],
        ),
        "dataset/runtime/runtime_features.jsonl": (
            dataset / "runtime/runtime_features.jsonl",
            EXPECTED_INPUT_SHA256["runtime_features.jsonl"],
        ),
        "dataset/private/private_labels.jsonl": (
            dataset / "private/private_labels.jsonl",
            EXPECTED_INPUT_SHA256["private_labels.jsonl"],
        ),
        "dataset/private/group_assignments.json": (
            dataset / "private/group_assignments.json",
            EXPECTED_INPUT_SHA256["group_assignments.json"],
        ),
    }
    hashes: dict[str, str] = {}
    for name, (raw_path, expected) in paths.items():
        path = safe_input_file(raw_path, label=name)
        hashes[name] = _require_hash(path, expected, label=name)
    return hashes


def _trajectory_calibration_coverage(
    model_inputs: _ModelInputs,
    labels_by_row: Mapping[str, Mapping[str, object]],
) -> dict[str, Any]:
    semantic = model_inputs.primary_manifest.get("semantic")
    if not isinstance(semantic, Mapping):
        raise ValueError("primary model semantic manifest missing")
    calibration_ids = tuple(semantic.get("calibration_trajectory_ids", ()))
    grouped: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in model_inputs.primary_predictions:
        if row["partition"] == "calibration":
            grouped[str(row["trajectory_id"])].append(row)
    if set(grouped) != set(calibration_ids):
        raise ValueError("primary calibration trajectory identity mismatch")
    scores: list[float] = []
    for trajectory_id in calibration_ids:
        positive = [
            1.0 - float(row["p_improve"])
            for row in grouped[trajectory_id]
            if labels_by_row[str(row["row_id"])]["beneficial_future"] is True
        ]
        scores.append(max(positive, default=0.0))
    if sha256_json(scores) != semantic.get("calibration_scores_sha256"):
        raise ValueError("primary trajectory calibration score hash mismatch")
    q_alpha = finite_sample_quantile(
        cats_module.np.asarray(scores, dtype=float), alpha=float(semantic["alpha"])
    )
    persisted_q = semantic.get("q_alpha")
    if persisted_q == "infinity":
        persisted_q = math.inf
    if q_alpha != float(persisted_q):
        raise ValueError("primary trajectory calibration quantile mismatch")
    return {
        "alpha": float(semantic["alpha"]),
        "calibration_unit": "trajectory",
        "q_alpha": q_alpha if math.isfinite(q_alpha) else "infinity",
        "score_count": len(scores),
        "scores_sha256": sha256_json(scores),
        "empirical_calibration_coverage": (
            sum(score <= q_alpha for score in scores) / len(scores)
        ),
        "target_coverage": 1.0 - float(semantic["alpha"]),
    }


def _build_development_trajectories(
    frozen: Any,
    snapshot_inputs: _SnapshotInputs,
    usage_inputs: _UsageInputs,
    model_inputs: _ModelInputs,
) -> tuple[tuple[RuntimeTrajectory, EvaluationLabels], ...]:
    assignments = frozen.assignments.loc[
        frozen.assignments["partition"] == AUTHORIZED_PARTITION
    ].sort_values("trajectory_id", kind="stable")
    if len(assignments) != EXPECTED_TRAJECTORIES:
        raise ValueError("development-gate trajectory census mismatch")
    runtime_by_trajectory = {
        trajectory_id: rows.sort_values("turn_index", kind="stable")
        for trajectory_id, rows in frozen.runtime.groupby("trajectory_id", sort=False)
    }
    labels_by_row = frozen.labels.set_index("row_id", verify_integrity=True)
    transaction_by_trajectory = {
        trajectory_id_from_resume_key(str(transaction["resume_identity_sha256"])): transaction
        for transaction in snapshot_inputs.snapshot.transactions
    }
    primary_by_row = {
        str(row["row_id"]): row for row in model_inputs.primary_predictions
    }
    logistic_by_row = {
        str(row["row_id"]): row for row in model_inputs.logistic_predictions
    }
    built: list[tuple[RuntimeTrajectory, EvaluationLabels]] = []
    for assignment in assignments.to_dict(orient="records"):
        trajectory_id = str(assignment["trajectory_id"])
        transaction = transaction_by_trajectory.get(trajectory_id)
        runtime_rows = runtime_by_trajectory.get(trajectory_id)
        if transaction is None or runtime_rows is None:
            raise ValueError("development trajectory source identity mismatch")
        raw = transaction["raw"]
        raw_result = raw["result"]
        agent_turns = tuple(
            turn
            for turn in raw_result["turns"]
            if str(turn["source"]).lower() != "user"
        )
        runtime_records = runtime_rows.to_dict(orient="records")
        message_hashes = snapshot_inputs.snapshot.message_hashes[
            str(transaction["resume_identity_sha256"])
        ]
        if not (
            len(agent_turns)
            == len(runtime_records)
            == len(message_hashes)
            == int(assignment["final_turn_count"])
        ):
            raise ValueError("development trajectory prefix census mismatch")
        if (
            raw["case_id"] != assignment["case_id"]
            or raw["repeat"] != assignment["repeat"]
        ):
            raise ValueError("development trajectory paired identity mismatch")
        cumulative = 0
        prefixes: list[RuntimePrefix] = []
        qualities: list[float] = []
        beneficial_future: list[bool] = []
        for position, (turn, runtime_row, message_hash) in enumerate(
            zip(agent_turns, runtime_records, message_hashes), start=1
        ):
            row_id = str(runtime_row["row_id"])
            primary = primary_by_row.get(row_id)
            logistic = logistic_by_row.get(row_id)
            if primary is None or logistic is None:
                raise ValueError("development prediction row is missing")
            if (
                primary["partition"] != AUTHORIZED_PARTITION
                or logistic["partition"] != AUTHORIZED_PARTITION
                or primary["trajectory_id"] != trajectory_id
                or logistic["trajectory_id"] != trajectory_id
            ):
                raise ValueError("development prediction partition mismatch")
            source_hash = sha256_json(
                {
                    field: turn[field]
                    for field in ("index", "source", "content", "tokens_in", "tokens_out")
                }
            )
            if source_hash != message_hash:
                raise ValueError("source agent-message hash mismatch")
            usage = usage_inputs.events_by_turn.get(
                (trajectory_id, int(turn["index"]))
            )
            if usage is None:
                raise ValueError("source visible-agent usage event is missing")
            turn_tokens = int(turn["tokens_in"]) + int(turn["tokens_out"])
            cumulative += turn_tokens
            if (
                usage.input_tokens != turn["tokens_in"]
                or usage.output_tokens != turn["tokens_out"]
                or usage.cumulative_visible_agent_tokens != cumulative
                or int(runtime_row["turn_index"]) != position
                or int(runtime_row["turn_tokens"]) != turn_tokens
                or int(runtime_row["cumulative_tokens"]) != cumulative
            ):
                raise ValueError("source prefix token parity mismatch")
            label = labels_by_row.loc[row_id]
            prefixes.append(
                RuntimePrefix(
                    trajectory_id=trajectory_id,
                    turn_index=position,
                    pattern=str(raw["pattern"]),
                    content=str(turn["content"]),
                    turn_tokens=turn_tokens,
                    cumulative_visible_tokens=cumulative,
                    message_hash=str(message_hash),
                    runtime_state=runtime_row,
                    histgb_p_improve=float(primary["p_improve"]),
                    logistic_p_improve=float(logistic["p_improve"]),
                )
            )
            qualities.append(float(label["quality_t"]))
            beneficial_future.append(bool(label["beneficial_future"]))
        if cumulative != int(assignment["final_tokens"]):
            raise ValueError("source final visible-agent token parity mismatch")
        built.append(
            (
                RuntimeTrajectory(
                    trajectory_id=trajectory_id,
                    group_id=str(assignment["group_id"]),
                    site_ref=str(assignment["site_ref"]),
                    case_id=str(assignment["case_id"]),
                    condition=str(assignment["condition"]),
                    mutation_family=str(assignment["mutation_family"]),
                    repeat=int(assignment["repeat"]),
                    pattern=str(raw["pattern"]),
                    prefixes=tuple(prefixes),
                ),
                EvaluationLabels(
                    qualities=tuple(qualities),
                    beneficial_future=tuple(beneficial_future),
                ),
            )
        )
    return tuple(built)


def _summary(values: Sequence[float]) -> dict[str, Any]:
    return {
        "mean": sum(values) / len(values),
        "median": _percentile(values, 0.5),
        "iqr": [_percentile(values, 0.25), _percentile(values, 0.75)],
    }


def _policy_statistics(rows: Sequence[ReplayOutcome]) -> list[dict[str, Any]]:
    statistics: list[dict[str, Any]] = []
    for policy_name in POLICY_REGISTRY:
        selected = [row for row in rows if row.policy == policy_name]
        if len(selected) != EXPECTED_TRAJECTORIES:
            raise ValueError("policy descriptive-statistic census mismatch")
        statistics.append(
            {
                "policy": policy_name,
                "trajectory_count": len(selected),
                "stop_turns": _summary([float(row.stop_turn) for row in selected]),
                "natural_turns": _summary(
                    [float(row.natural_turns) for row in selected]
                ),
                "stopped_quality": _summary(
                    [row.stopped_quality for row in selected]
                ),
                "full_quality": _summary([row.full_quality for row in selected]),
                "natural_quality": _summary(
                    [row.natural_quality for row in selected]
                ),
                "oracle_quality": _summary([row.oracle_quality for row in selected]),
                "visible_agent_tokens": _summary(
                    [float(row.visible_agent_tokens) for row in selected]
                ),
                "natural_visible_agent_tokens": _summary(
                    [float(row.natural_visible_agent_tokens) for row in selected]
                ),
                "visible_agent_token_reduction": _summary(
                    [row.visible_agent_token_reduction for row in selected]
                ),
                "quality_delta": _summary([row.quality_delta for row in selected]),
                "hard_guard_admissible_count": sum(
                    row.hard_guard_admissible for row in selected
                ),
                "hard_guard_admissible_rate": sum(
                    row.hard_guard_admissible for row in selected
                )
                / len(selected),
                "unsafe_stops": sum(row.unsafe_stop for row in selected),
                "unsafe_stop_rate": sum(row.unsafe_stop for row in selected)
                / len(selected),
                "premature_stops": sum(row.premature_stop for row in selected),
                "premature_stop_rate": sum(row.premature_stop for row in selected)
                / len(selected),
                "overshoot_turns": _summary(
                    [float(row.overshoot_turns) for row in selected]
                ),
                "oracle_regret": _summary([row.oracle_regret for row in selected]),
                "empirical_trajectory_coverage": sum(
                    row.empirical_trajectory_covered for row in selected
                )
                / len(selected),
            }
        )
    return statistics


def _validate_replay_closure(rows: Sequence[ReplayOutcome]) -> None:
    if len(rows) != EXPECTED_REPLAY_ROWS:
        raise ValueError("replay row census mismatch")
    identities = {(row.trajectory_id, row.policy) for row in rows}
    if len(identities) != EXPECTED_REPLAY_ROWS:
        raise ValueError("duplicate replay row identity")
    grouped: defaultdict[str, list[ReplayOutcome]] = defaultdict(list)
    for row in rows:
        grouped[row.trajectory_id].append(row)
    if len(grouped) != EXPECTED_TRAJECTORIES:
        raise ValueError("replay trajectory census mismatch")
    for trajectory_rows in grouped.values():
        if tuple(row.policy for row in trajectory_rows) != tuple(POLICY_REGISTRY):
            raise ValueError("replay policy key set/order mismatch")
        source_identities = {
            (
                row.group_id,
                row.site_ref,
                row.case_id,
                row.condition,
                row.mutation_family,
                row.repeat,
                row.pattern,
                row.natural_turns,
                row.natural_visible_agent_tokens,
                row.full_quality,
            )
            for row in trajectory_rows
        }
        if len(source_identities) != 1:
            raise ValueError("paired replay source identity mismatch")


def _resolved_policy_parameters(
    *, cats_q_alpha: float, state_q_alpha: float
) -> dict[str, Any]:
    parameters = json.loads(canonical_json(POLICY_PARAMETERS))
    parameters["cats"]["q_alpha"] = cats_q_alpha
    parameters["cats_no_guard"]["q_alpha"] = cats_q_alpha
    parameters["state_conformal"]["q_alpha"] = state_q_alpha
    return parameters


@dataclass(frozen=True)
class _ReplayBuild:
    outcomes: tuple[ReplayOutcome, ...]
    row_payloads: tuple[dict[str, Any], ...]
    rows_bytes: bytes
    gate: Mapping[str, Any]


def _build_development_replay(
    *,
    snapshot: str | Path,
    dataset: str | Path,
    models: str | Path,
    partition: str,
) -> _ReplayBuild:
    """Recompute the complete replay and gate semantics without writing output."""

    authorize_partition(partition)
    snapshot_inputs = _load_snapshot(Path(snapshot))
    dataset_root = _safe_input_directory(dataset, label="dataset root")
    dataset_hashes = _dataset_source_hashes(dataset_root)
    frozen = load_frozen_dataset(dataset_root)
    usage_inputs = _load_usage(dataset_root)
    model_inputs = _load_models(Path(models))

    labels_by_row = {
        str(row["row_id"]): {
            "beneficial_future": bool(row["beneficial_future"]),
            "quality_t": float(row["quality_t"]),
            "future_max_quality": float(row["future_max_quality"]),
        }
        for row in frozen.labels.to_dict(orient="records")
    }
    state_derivation = derive_state_conformal(
        model_inputs.primary_predictions,
        labels_by_row,
        alpha=StudyContract.primary().alpha,
    )
    primary_entry = next(
        entry
        for entry in model_inputs.registry["variants"]
        if entry["name"] == "cats-primary"
    )
    state_derivation_payload = {
        **state_derivation.to_dict(),
        "adapted_after_development_outcomes": False,
        "source_bindings": {
            "group_assignments_sha256": dataset_hashes[
                "dataset/private/group_assignments.json"
            ],
            "primary_predictions_sha256": primary_entry["predictions_sha256"],
            "private_labels_sha256": dataset_hashes[
                "dataset/private/private_labels.jsonl"
            ],
        },
    }
    trajectory_calibration = _trajectory_calibration_coverage(
        model_inputs, labels_by_row
    )
    semantic = model_inputs.primary_manifest["semantic"]
    cats_q_alpha = float(semantic["q_alpha"])
    trajectories = _build_development_trajectories(
        frozen,
        snapshot_inputs,
        usage_inputs,
        model_inputs,
    )
    outcomes = tuple(
        outcome
        for trajectory, labels in trajectories
        for outcome in replay_registry(
            trajectory,
            labels,
            cats_q_alpha=cats_q_alpha,
            state_q_alpha=state_derivation.q_alpha,
        )
    )
    _validate_replay_closure(outcomes)
    row_payloads = tuple(outcome.to_dict() for outcome in outcomes)
    rows_bytes = "".join(
        f"{canonical_json(row)}\n" for row in row_payloads
    ).encode("utf-8")
    rows_sha256 = hashlib.sha256(rows_bytes).hexdigest()
    policy_statistics = _policy_statistics(outcomes)
    cats_rows = [outcome for outcome in outcomes if outcome.policy == "cats"]
    bootstrap = site_cluster_bootstrap(
        [outcome.to_dict() for outcome in cats_rows],
        draws=BOOTSTRAP_DRAWS,
        seed=BOOTSTRAP_SEED,
    )
    cats_statistics = next(
        item for item in policy_statistics if item["policy"] == "cats"
    )
    cats_coverage = cats_statistics["empirical_trajectory_coverage"]
    checks = {
        "cats_empirical_trajectory_coverage_present": {
            "observed": cats_coverage,
            "operator": "is_not_null",
            "threshold": None,
            "passed": cats_coverage is not None and len(cats_rows) > 0,
        },
        "cats_mean_quality_delta_bootstrap_lower_gt_negative_0p03": {
            "observed": bootstrap["lower_95"],
            "operator": ">",
            "threshold": -0.03,
            "passed": bootstrap["lower_95"] > -0.03,
        },
        "cats_median_visible_agent_token_reduction_gte_0p15": {
            "observed": cats_statistics["visible_agent_token_reduction"]["median"],
            "operator": ">=",
            "threshold": 0.15,
            "passed": (
                cats_statistics["visible_agent_token_reduction"]["median"] >= 0.15
            ),
        },
        "cats_observed_unsafe_stops_eq_0": {
            "observed": cats_statistics["unsafe_stops"],
            "operator": "==",
            "threshold": 0,
            "passed": cats_statistics["unsafe_stops"] == 0,
        },
    }
    failures = sorted(name for name, check in checks.items() if not check["passed"])
    project_root = Path(__file__).resolve().parents[1]
    implementation_files = {
        name: safe_input_file(
            project_root / name,
            label=f"replay implementation dependency {name}",
        )
        for name in REPLAY_IMPLEMENTATION_FILES
    }
    lexical_by_trajectory = {
        outcome.trajectory_id: outcome.stop_turn
        for outcome in outcomes
        if outcome.policy == "lexical_du"
    }
    max_cap_by_trajectory = {
        outcome.trajectory_id: outcome.stop_turn
        for outcome in outcomes
        if outcome.policy == "max_cap"
    }
    if set(lexical_by_trajectory) != set(max_cap_by_trajectory):
        raise ValueError("lexical/max-cap contrast identity mismatch")
    collision_vector = [
        [
            trajectory_id,
            lexical_by_trajectory[trajectory_id],
            max_cap_by_trajectory[trajectory_id],
            lexical_by_trajectory[trajectory_id]
            == max_cap_by_trajectory[trajectory_id],
        ]
        for trajectory_id in sorted(lexical_by_trajectory)
    ]
    matching_stop_turns = sum(bool(item[3]) for item in collision_vector)
    source_hashes = {
        **snapshot_inputs.source_hashes,
        **dataset_hashes,
        **usage_inputs.source_hashes,
        **model_inputs.source_hashes,
    }
    payload: dict[str, Any] = {
        "schema_version": DEVELOPMENT_GATE_SCHEMA,
        "partition": AUTHORIZED_PARTITION,
        "passed": not failures,
        "failures": failures,
        "checks": checks,
        "policy_registry": list(POLICY_REGISTRY),
        "policy_parameters": _resolved_policy_parameters(
            cats_q_alpha=cats_q_alpha,
            state_q_alpha=state_derivation.q_alpha,
        ),
        "definitions": {
            "unsafe_stop": (
                "beneficial_future is true at the selected stop; the frozen label "
                "means future_max_quality - quality_t > epsilon"
            ),
            "premature_stop": "selected stop precedes the earliest maximum-quality prefix",
            "empirical_trajectory_coverage": (
                "fraction of selected stops with beneficial_future false"
            ),
            "overshoot_turns": (
                "max(0, selected stop turn - earliest maximum-quality turn)"
            ),
            "oracle_regret": "maximum trajectory quality - stopped quality",
            "quality_delta": "stopped quality - full natural quality",
        },
        "frozen_contract": {
            "alpha": StudyContract.primary().alpha,
            "bootstrap_draws": BOOTSTRAP_DRAWS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "epsilon": StudyContract.primary().epsilon,
            "patience": StudyContract.primary().patience,
        },
        "state_conformal_derivation": state_derivation_payload,
        "calibration_coverage": {
            "cats_trajectory": trajectory_calibration,
            "state_conformal": state_derivation_payload,
            "cats_development_empirical_trajectory_coverage": cats_coverage,
        },
        "bootstrap": bootstrap,
        "policy_statistics": policy_statistics,
        "policy_contrasts": {
            "lexical_du_vs_max_cap": {
                "algorithmically_distinct": True,
                "collision_vector_definition": (
                    "trajectory_id-sorted [trajectory_id, lexical_du stop turn, "
                    "max_cap stop turn, equal]"
                ),
                "collision_vector_sha256": sha256_json(collision_vector),
                "empirically_identical_to_max_cap": (
                    matching_stop_turns == len(collision_vector)
                ),
                "matching_stop_turns": matching_stop_turns,
                "trajectory_count": len(collision_vector),
            }
        },
        "row_census": {
            "development_gate_sites": 2,
            "policies": len(POLICY_REGISTRY),
            "replay_rows": len(outcomes),
            "trajectories": len(trajectories),
        },
        "replay_rows_sha256": rows_sha256,
        "replay_row_identity_sha256": sha256_json(
            [[row.trajectory_id, row.policy] for row in outcomes]
        ),
        "source_hashes": dict(sorted(source_hashes.items())),
        "source_receipts": {
            "dataset_artifact_sha256": frozen.source_receipts[
                "dataset_artifact_sha256"
            ],
            "model_semantic_determinism_receipt_sha256": model_inputs.registry[
                "semantic_determinism"
            ]["receipt_sha256"],
            "snapshot_receipt_sha256": _sha256_file(Path(snapshot).resolve()),
            "snapshot_source_artifact_sha256": snapshot_inputs.receipt[
                "source_artifact_receipt"
            ]["artifact_sha256"],
        },
        "replay_implementation": {
            name: _sha256_file(path) for name, path in implementation_files.items()
        },
        "usage_claims": {
            "visible_agent_tokens": usage_inputs.claim["visible_agent_tokens"],
            "visible_agent_token_boundary": usage_inputs.claim[
                "visible_agent_token_boundary"
            ],
            "invoice_grade_cost": usage_inputs.claim["invoice_grade_cost"],
            "total_compute": usage_inputs.claim["total_compute"],
            "reasons": usage_inputs.claim["reasons"],
        },
        "access_audit": {
            "authorized_partition": AUTHORIZED_PARTITION,
            "held_out_bundle_reads": 0,
            "llm_calls": 0,
            "model_refits": 0,
            "transformer_refits": 0,
        },
    }
    gate = {**payload, "receipt_sha256": sha256_json(payload)}
    return _ReplayBuild(
        outcomes=outcomes,
        row_payloads=row_payloads,
        rows_bytes=rows_bytes,
        gate=MappingProxyType(gate),
    )


def run_development_replay(
    *,
    snapshot: str | Path,
    dataset: str | Path,
    models: str | Path,
    partition: str,
    output: str | Path,
) -> dict[str, Any]:
    """Build, write, then source-recompute-verify the development replay."""

    build = _build_development_replay(
        snapshot=snapshot,
        dataset=dataset,
        models=models,
        partition=partition,
    )
    output_path = Path(output)
    _reject_link_components(output_path, label="replay output")
    if output_path.exists() and not output_path.is_dir():
        raise ValueError("replay output must be a directory")
    output_path.mkdir(parents=True, exist_ok=True)
    write_jsonl_atomic(output_path / "replay_rows.jsonl", build.row_payloads)
    write_json_atomic(output_path / "development_gate.json", build.gate)
    return verify_replay_outputs(
        output_path,
        snapshot=snapshot,
        dataset=dataset,
        models=models,
    )


def verify_replay_outputs(
    output: str | Path,
    *,
    snapshot: str | Path | None = None,
    dataset: str | Path | None = None,
    models: str | Path | None = None,
    expected_gate_file_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify outputs against trusted sources or a trusted gate-file digest.

    A receipt cannot authenticate itself.  Callers must provide either all three
    frozen source roots for a complete scientific reconstruction or an external
    expected digest for the canonical gate file.
    """

    source_arguments = (snapshot, dataset, models)
    source_mode = all(value is not None for value in source_arguments)
    partial_source_mode = any(value is not None for value in source_arguments)
    digest_mode = expected_gate_file_sha256 is not None
    if partial_source_mode and not source_mode:
        raise ValueError("source verification requires snapshot, dataset, and models")
    if source_mode == digest_mode:
        raise ValueError("select exactly one trusted replay verification mode")
    if digest_mode and (
        not isinstance(expected_gate_file_sha256, str)
        or not _SHA256.fullmatch(expected_gate_file_sha256)
    ):
        raise ValueError("trusted gate-file SHA-256 is invalid")

    root = _safe_input_directory(output, label="replay output")
    rows_path = safe_input_file(root / "replay_rows.jsonl", label="replay rows")
    gate_path = safe_input_file(root / "development_gate.json", label="gate receipt")
    gate = _read_canonical_json(gate_path, label="gate receipt")
    payload = {key: value for key, value in gate.items() if key != "receipt_sha256"}
    if (
        gate.get("schema_version") != DEVELOPMENT_GATE_SCHEMA
        or gate.get("receipt_sha256") != sha256_json(payload)
    ):
        raise ValueError("development gate self hash mismatch")
    if gate.get("replay_rows_sha256") != _sha256_file(rows_path):
        raise ValueError("replay rows hash mismatch")
    rows = _read_canonical_jsonl(rows_path, label="replay rows")
    census = gate.get("row_census")
    if (
        not isinstance(census, Mapping)
        or census.get("replay_rows") != len(rows)
        or len(rows) != EXPECTED_REPLAY_ROWS
    ):
        raise ValueError("replay rows census mismatch")
    identities = [(row.get("trajectory_id"), row.get("policy")) for row in rows]
    if (
        len(set(identities)) != EXPECTED_REPLAY_ROWS
        or sha256_json(identities) != gate.get("replay_row_identity_sha256")
    ):
        raise ValueError("replay row identity hash mismatch")
    if digest_mode:
        if _sha256_file(gate_path) != expected_gate_file_sha256:
            raise ValueError("trusted gate-file SHA-256 mismatch")
        return gate

    expected = _build_development_replay(
        snapshot=snapshot,
        dataset=dataset,
        models=models,
        partition=AUTHORIZED_PARTITION,
    )
    if read_authenticated_file(rows_path, label="replay rows") != expected.rows_bytes:
        raise ValueError("replay rows differ from source reconstruction")
    expected_gate_bytes = (canonical_json(expected.gate) + "\n").encode("utf-8")
    if read_authenticated_file(gate_path, label="gate receipt") != expected_gate_bytes:
        raise ValueError("development gate differs from source reconstruction")
    return gate


__all__ = (
    "AUTHORIZED_PARTITION",
    "BOOTSTRAP_DRAWS",
    "BOOTSTRAP_SEED",
    "DEVELOPMENT_GATE_SCHEMA",
    "EvaluationLabels",
    "KEYWORD_SIGNALS",
    "POLICY_PARAMETERS",
    "POLICY_REGISTRY",
    "ReplayOutcome",
    "RuntimePrefix",
    "RuntimeTrajectory",
    "StateConformalDerivation",
    "authorize_partition",
    "decide_stop",
    "derive_state_conformal",
    "replay",
    "replay_registry",
    "run_development_replay",
    "safe_input_file",
    "site_cluster_bootstrap",
    "verify_replay_outputs",
)
