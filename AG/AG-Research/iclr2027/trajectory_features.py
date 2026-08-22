"""Leakage-safe prefix features and private labels for the CATS study."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields
import hashlib
import math
import re
from types import MappingProxyType
from typing import Any, Literal

from sklearn.feature_extraction.text import TfidfVectorizer

from config import PATTERN_MAX_MESSAGES

from .io import sha256_json
from .study_contract import StudyContract


NUMERIC_FEATURES = (
    "turn_index",
    "normalized_turn",
    "agent_count",
    "speaker_count",
    "turn_tokens",
    "cumulative_tokens",
    "token_delta_1",
    "token_delta_2",
    "word_count",
    "unique_ratio",
    "repeated_ngram_ratio",
    "tfidf_distance_prev",
    "tfidf_distance_prefix",
    "reported_confidence",
    "checked_domain_count",
    "evidence_count",
    "blocking_issue_count",
    "missing_evidence_count",
)
CATEGORICAL_FEATURES = (
    "pattern",
    "pattern_category",
    "source",
    "recommended_decision",
    "parse_complete",
    "site_evidence_present",
    "geometry_evidence_present",
    "law_evidence_present",
    "parking_evidence_present",
    "program_evidence_present",
)
MODEL_FEATURES = (*NUMERIC_FEATURES, *CATEGORICAL_FEATURES)

Partition = Literal["train", "calibration", "development_gate"]
_WORD = re.compile(r"\b\w+\b", flags=re.UNICODE)


@dataclass(frozen=True)
class SiteGroupAssignment:
    site_ref: str
    group_id: str
    partition: Partition


@dataclass(frozen=True)
class PrefixRuntimeFeature:
    row_id: str
    trajectory_id: str
    turn_index: int
    normalized_turn: float
    agent_count: int
    speaker_count: int
    turn_tokens: int
    cumulative_tokens: int
    token_delta_1: int
    token_delta_2: int
    word_count: int
    unique_ratio: float
    repeated_ngram_ratio: float
    tfidf_distance_prev: float
    tfidf_distance_prefix: float
    reported_confidence: float
    checked_domain_count: int
    evidence_count: int
    blocking_issue_count: int
    missing_evidence_count: int
    pattern: str
    pattern_category: str
    source: str
    recommended_decision: str
    parse_complete: bool
    site_evidence_present: bool
    geometry_evidence_present: bool
    law_evidence_present: bool
    parking_evidence_present: bool
    program_evidence_present: bool

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return tuple(field.name for field in fields(cls))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PrivatePrefixLabel:
    row_id: str
    quality_t: float
    future_max_quality: float
    beneficial_future: bool

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return tuple(field.name for field in fields(cls))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrajectoryGroupAssignment:
    trajectory_id: str
    group_id: str
    partition: Partition
    site_ref: str
    case_id: str
    condition: str
    mutation_family: str
    repeat: int
    final_turn_count: int
    final_tokens: int

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return tuple(field.name for field in fields(cls))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetManifest:
    schema_version: str
    snapshot_receipt_sha256: str
    transaction_set_sha256: str
    split_manifest_sha256: str
    projection_identity_commitment: str
    study_contract_sha256: str
    epsilon: float
    trajectory_count: int
    prefix_count: int
    site_partition_counts: Mapping[str, int]
    trajectory_partition_counts: Mapping[str, int]
    prefix_partition_counts: Mapping[str, int]
    runtime_schema: tuple[str, ...]
    private_label_schema: tuple[str, ...]
    assignment_schema: tuple[str, ...]
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    model_features: tuple[str, ...]
    transformer: Mapping[str, Any]
    access_policy: Mapping[str, Any]
    artifact_receipt: Mapping[str, Any]
    artifacts: Mapping[str, Mapping[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FittedTextDistance:
    """A train-fitted, transform-only TF-IDF interface."""

    _vectorizer: TfidfVectorizer
    vocabulary_sha256: str

    @property
    def vocabulary(self) -> Mapping[str, int]:
        return MappingProxyType(dict(self._vectorizer.vocabulary_))

    def transform(self, texts: Sequence[str]):
        return self._vectorizer.transform(tuple(str(text) for text in texts))


def _site_ref(value: object) -> str:
    if isinstance(value, str):
        site_ref = value
    elif isinstance(value, Mapping):
        site_ref = str(value.get("site_ref") or "")
    else:
        site_ref = str(getattr(value, "site_ref", "") or "")
    if not re.fullmatch(r"site:[0-9a-f]{64}", site_ref):
        raise ValueError("development cases require opaque site_ref identities")
    return site_ref


def assign_site_groups(
    development_cases: Sequence[object] | Mapping[object, object],
    *,
    seed: int,
) -> tuple[SiteGroupAssignment, ...]:
    """Assign every development site to exactly one frozen study partition."""

    values = (
        tuple(development_cases.values())
        if isinstance(development_cases, Mapping)
        else tuple(development_cases)
    )
    site_refs = sorted({_site_ref(value) for value in values})
    contract = StudyContract.primary()
    expected_sites = sum(contract.site_partition_counts)
    if len(site_refs) != expected_sites:
        raise ValueError(f"expected exactly {expected_sites} development sites")
    if type(seed) is not int:
        raise TypeError("group seed must be a native integer")
    ranked = sorted(
        site_refs,
        key=lambda site_ref: hashlib.sha256(
            f"{seed}\0{site_ref}".encode("utf-8")
        ).hexdigest(),
    )
    train_count, calibration_count, _ = contract.site_partition_counts
    partition_by_site: dict[str, Partition] = {}
    for index, site_ref in enumerate(ranked):
        if index < train_count:
            partition: Partition = "train"
        elif index < train_count + calibration_count:
            partition = "calibration"
        else:
            partition = "development_gate"
        partition_by_site[site_ref] = partition
    return tuple(
        SiteGroupAssignment(
            site_ref=site_ref,
            group_id=f"group:{sha256_json({'site_ref': site_ref})}",
            partition=partition_by_site[site_ref],
        )
        for site_ref in site_refs
    )


def fit_text_distance(texts: Sequence[str]) -> FittedTextDistance:
    """Fit the preregistered TF-IDF transform on caller-supplied train text."""

    train_texts = tuple(str(text) for text in texts)
    if not train_texts:
        raise ValueError("train text must not be empty")
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        norm="l2",
    )
    vectorizer.fit(train_texts)
    vocabulary = dict(sorted(vectorizer.vocabulary_.items()))
    return FittedTextDistance(vectorizer, sha256_json(vocabulary))


def trajectory_id_from_resume_key(resume_key: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", str(resume_key)):
        raise ValueError("resume key must be a lowercase SHA-256")
    return f"trajectory:{resume_key}"


def prefix_row_id(trajectory_id: str, turn_index: int) -> str:
    if type(turn_index) is not int or turn_index <= 0:
        raise ValueError("turn index must be a positive native integer")
    return f"row:{sha256_json({'trajectory_id': trajectory_id, 'turn_index': turn_index})}"


def _nonnegative_token_count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    if not math.isfinite(float(value)) or float(value) < 0.0:
        return 0
    return int(value)


def _cosine_distance(left, right) -> float:
    similarity = float((left @ right.T).toarray()[0, 0])
    return min(1.0, max(0.0, 1.0 - similarity))


def _repeated_ngram_ratio(words: Sequence[str]) -> float:
    if len(words) < 2:
        return 0.0
    ngrams = tuple(zip(words, words[1:]))
    return 1.0 - (len(set(ngrams)) / len(ngrams))


def runtime_features(
    prefix: Mapping[str, Any],
    *,
    fitted: FittedTextDistance,
) -> PrefixRuntimeFeature:
    """Compute one runtime-safe row from the explicitly selected prefix only."""

    if not isinstance(prefix, Mapping):
        raise TypeError("prefix must be a mapping")
    pattern = str(prefix.get("pattern") or "")
    if pattern not in PATTERN_MAX_MESSAGES:
        raise ValueError("prefix has an unsupported topology pattern")
    turn_index = prefix.get("prefix_turn_index")
    if type(turn_index) is not int or turn_index <= 0:
        raise ValueError("prefix_turn_index must be a positive native integer")
    raw_turns = prefix.get("turns")
    parsed = prefix.get("parsed")
    if (
        isinstance(raw_turns, (str, bytes))
        or not isinstance(raw_turns, Sequence)
        or isinstance(parsed, (str, bytes))
        or not isinstance(parsed, Sequence)
    ):
        raise ValueError("prefix turns and parsed states must be sequences")
    agent_turns = tuple(
        turn
        for turn in raw_turns
        if isinstance(turn, Mapping) and str(turn.get("source") or "").lower() != "user"
    )
    if turn_index > len(agent_turns) or turn_index > len(parsed):
        raise ValueError("prefix turn exceeds available agent states")
    visible_turns = agent_turns[:turn_index]
    current_turn = visible_turns[-1]
    parsed_state = parsed[turn_index - 1]
    if not isinstance(parsed_state, Mapping):
        raise ValueError("parsed prefix state must be a mapping")
    state = parsed_state.get("state")
    state = state if isinstance(state, Mapping) else {}

    turn_tokens = tuple(
        _nonnegative_token_count(turn.get("tokens_in"))
        + _nonnegative_token_count(turn.get("tokens_out"))
        for turn in visible_turns
    )
    current_tokens = turn_tokens[-1]
    token_delta_1 = current_tokens - turn_tokens[-2] if len(turn_tokens) >= 2 else 0
    token_delta_2 = current_tokens - turn_tokens[-3] if len(turn_tokens) >= 3 else 0
    text = str(current_turn.get("content") or "")
    words = tuple(word.lower() for word in _WORD.findall(text))
    previous_text = (
        str(visible_turns[-2].get("content") or "")
        if len(visible_turns) >= 2
        else ""
    )
    prefix_text = " ".join(
        str(turn.get("content") or "") for turn in visible_turns[:-1]
    )
    current_vector, previous_vector, prefix_vector = fitted.transform(
        (text, previous_text, prefix_text)
    )
    previous_distance = (
        _cosine_distance(current_vector, previous_vector)
        if previous_text.strip()
        else 0.0
    )
    prefix_distance = (
        _cosine_distance(current_vector, prefix_vector)
        if prefix_text.strip()
        else 0.0
    )
    evidence_ids = tuple(str(value) for value in state.get("evidence_ids", ()))
    checked_domains = tuple(str(value) for value in state.get("checked_domains", ()))
    blocking = tuple(str(value) for value in state.get("blocking_issue_codes", ()))
    missing = tuple(str(value) for value in state.get("missing_evidence_codes", ()))
    confidence = state.get("confidence", 0.0)
    reported_confidence = (
        float(confidence)
        if isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and math.isfinite(float(confidence))
        else 0.0
    )
    trajectory_id = str(prefix.get("trajectory_id") or "")
    return PrefixRuntimeFeature(
        row_id=prefix_row_id(trajectory_id, turn_index),
        trajectory_id=trajectory_id,
        turn_index=turn_index,
        normalized_turn=turn_index / PATTERN_MAX_MESSAGES[pattern],
        agent_count=_nonnegative_token_count(prefix.get("agent_count")),
        speaker_count=len(
            {str(turn.get("source") or "") for turn in visible_turns}
        ),
        turn_tokens=current_tokens,
        cumulative_tokens=sum(turn_tokens),
        token_delta_1=token_delta_1,
        token_delta_2=token_delta_2,
        word_count=len(words),
        unique_ratio=(len(set(words)) / len(words)) if words else 0.0,
        repeated_ngram_ratio=_repeated_ngram_ratio(words),
        tfidf_distance_prev=previous_distance,
        tfidf_distance_prefix=prefix_distance,
        reported_confidence=reported_confidence,
        checked_domain_count=len(checked_domains),
        evidence_count=len(evidence_ids),
        blocking_issue_count=len(blocking),
        missing_evidence_count=len(missing),
        pattern=pattern,
        pattern_category=str(prefix.get("pattern_category") or ""),
        source=str(current_turn.get("source") or ""),
        recommended_decision=str(state.get("recommended_decision") or ""),
        parse_complete=bool(parsed_state.get("parse_complete")),
        site_evidence_present="evidence:site_agent" in evidence_ids,
        geometry_evidence_present="evidence:geometry_agent" in evidence_ids,
        law_evidence_present="evidence:law_graph_agent" in evidence_ids,
        parking_evidence_present="evidence:parking_agent" in evidence_ids,
        program_evidence_present="evidence:program_agent" in evidence_ids,
    )


def private_prefix_labels(
    trajectory_id: str,
    qualities: Sequence[float],
    *,
    epsilon: float,
) -> tuple[PrivatePrefixLabel, ...]:
    """Materialize private future-benefit labels without joining runtime fields."""

    if isinstance(epsilon, bool) or not isinstance(epsilon, (int, float)):
        raise TypeError("epsilon must be numeric")
    quality_values = tuple(float(value) for value in qualities)
    if not quality_values or any(not math.isfinite(value) for value in quality_values):
        raise ValueError("qualities must be a nonempty finite sequence")
    labels: list[PrivatePrefixLabel] = []
    for offset, quality_t in enumerate(quality_values):
        future_max = max(quality_values[offset + 1 :], default=quality_t)
        labels.append(
            PrivatePrefixLabel(
                row_id=prefix_row_id(trajectory_id, offset + 1),
                quality_t=quality_t,
                future_max_quality=future_max,
                beneficial_future=future_max - quality_t > float(epsilon),
            )
        )
    return tuple(labels)


__all__ = (
    "CATEGORICAL_FEATURES",
    "DatasetManifest",
    "FittedTextDistance",
    "MODEL_FEATURES",
    "NUMERIC_FEATURES",
    "PrefixRuntimeFeature",
    "PrivatePrefixLabel",
    "SiteGroupAssignment",
    "TrajectoryGroupAssignment",
    "assign_site_groups",
    "fit_text_distance",
    "prefix_row_id",
    "private_prefix_labels",
    "runtime_features",
    "trajectory_id_from_resume_key",
)
