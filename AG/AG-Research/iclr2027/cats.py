"""Leakage-safe CATS fitting and trajectory-level conformal calibration."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Literal
import warnings

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .artifact_receipts import verify_artifact_receipt_bytes
from .io import canonical_json, sha256_json, write_json_atomic, write_jsonl_atomic
from .study_contract import StudyContract
from .secure_files import AuthenticatedTree
from .trajectory_features import (
    CATEGORICAL_FEATURES,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    PrefixRuntimeFeature,
    PrivatePrefixLabel,
    TrajectoryGroupAssignment,
)


DATASET_MANIFEST_SCHEMA = "ace.iclr2027.cats_dataset_manifest.v1"
DATASET_RECEIPT_SCHEMA = "ace.iclr2027.cats_dataset_artifacts.v1"
ASSIGNMENTS_SCHEMA = "ace.iclr2027.cats_group_assignments.v1"
MODEL_MANIFEST_SCHEMA = "ace.iclr2027.cats_model_manifest.v1"
MODEL_REGISTRY_SCHEMA = "ace.iclr2027.cats_model_registry.v1"
SEMANTIC_DETERMINISM_SCHEMA = "ace.iclr2027.cats_semantic_determinism.v1"
EXPECTED_DATASET_FILES = (
    "private/group_assignments.json",
    "private/private_labels.jsonl",
    "runtime/runtime_features.jsonl",
)
RUNTIME_SCHEMA = PrefixRuntimeFeature.field_names()
PRIVATE_LABEL_SCHEMA = PrivatePrefixLabel.field_names()
ASSIGNMENT_SCHEMA = TrajectoryGroupAssignment.field_names()
Partition = Literal["train", "calibration", "development_gate"]
ModelFamily = Literal["histgb", "logistic"]


@dataclass(frozen=True)
class FrozenVariantSpec:
    """One preregistered point-estimator and calibration configuration."""

    name: str
    family: ModelFamily
    epsilon: float
    alpha: float


FROZEN_VARIANTS = (
    FrozenVariantSpec("cats-primary", "histgb", 0.02, 0.10),
    FrozenVariantSpec("cats-logistic", "logistic", 0.02, 0.10),
    FrozenVariantSpec("cats-epsilon-0p01", "histgb", 0.01, 0.10),
    FrozenVariantSpec("cats-epsilon-0p05", "histgb", 0.05, 0.10),
    FrozenVariantSpec("cats-alpha-0p05", "histgb", 0.02, 0.05),
    FrozenVariantSpec("cats-alpha-0p20", "histgb", 0.02, 0.20),
)


@dataclass(frozen=True)
class FrozenCATSData:
    """Verified, physically separate development tables and row-ID mapping."""

    runtime: pd.DataFrame
    labels: pd.DataFrame
    assignments: pd.DataFrame
    partition_by_row: pd.DataFrame
    manifest: Mapping[str, Any]
    source_receipts: Mapping[str, Any]


@dataclass(frozen=True)
class FittedCATSClassifier:
    """Train-fitted preprocessing and one frozen binary classifier."""

    transformer: ColumnTransformer
    classifier: HistGradientBoostingClassifier | LogisticRegression
    feature_order: tuple[str, ...]
    family: ModelFamily

    def predict_probabilities(self, features: pd.DataFrame) -> np.ndarray:
        selected = features.loc[:, self.feature_order]
        transformed = np.asarray(self.transformer.transform(selected), dtype=float)
        if transformed.ndim != 2 or not np.isfinite(transformed).all():
            raise ValueError("non-finite transformed model inputs")
        raw = np.asarray(self.classifier.predict_proba(transformed), dtype=float)
        if raw.ndim != 2 or raw.shape[1] != 2:
            raise ValueError("binary classifier probability shape mismatch")
        return ensure_finite_probabilities(raw[:, 1], expected=len(selected))

    def predict_improvement(self, state: Mapping[str, object]) -> float:
        frame = pd.DataFrame([{feature: state.get(feature) for feature in self.feature_order}])
        return float(self.predict_probabilities(frame)[0])


@dataclass(frozen=True)
class FrozenVariantResult:
    """In-memory fitted result before artifact serialization."""

    spec: FrozenVariantSpec
    fitted: FittedCATSClassifier
    predictions: pd.DataFrame
    calibration_scores: tuple[float, ...]
    q_alpha: float
    class_balance: Mapping[str, Mapping[str, int]]
    row_census: Mapping[str, int]
    trajectory_census: Mapping[str, int]
    site_census: Mapping[str, int]
    train_trajectory_ids: tuple[str, ...]
    calibration_trajectory_ids: tuple[str, ...]
    development_gate_trajectory_ids: tuple[str, ...]


@dataclass(frozen=True)
class StopDecision:
    """One sequential CATS policy decision."""

    stop: bool
    reason: str
    p_improve: float
    calibrated_no_future_gain: bool
    admissible: bool
    streak: int


def finite_sample_quantile(scores: np.ndarray, alpha: float) -> float:
    """Return the exact finite-sample corrected split-conformal quantile."""

    values = np.asarray(scores, dtype=float)
    if values.ndim != 1:
        raise ValueError("calibration scores must be one-dimensional")
    if values.size == 0:
        raise ValueError("calibration scores must not be empty")
    if not np.isfinite(values).all():
        raise ValueError("calibration scores contain non-finite values")
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
        raise TypeError("alpha must be numeric")
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must lie strictly between zero and one")
    rank = math.ceil((len(values) + 1) * (1.0 - float(alpha)))
    if rank > len(values):
        return math.inf
    return float(np.partition(values, rank - 1)[rank - 1])


def ensure_finite_probabilities(values: np.ndarray, *, expected: int) -> np.ndarray:
    """Validate one positive-class probability per requested row."""

    probabilities = np.asarray(values, dtype=float)
    if probabilities.ndim != 1 or probabilities.shape[0] != expected:
        raise ValueError("model prediction count mismatch")
    if not np.isfinite(probabilities).all():
        raise ValueError("non-finite model predictions")
    if ((probabilities < 0.0) | (probabilities > 1.0)).any():
        raise ValueError("model predictions outside the zero-one interval")
    return probabilities


def trajectory_nonconformity(rows: pd.DataFrame) -> float:
    """Return the maximum positive-prefix nonconformity for one trajectory."""

    required = {"beneficial_future", "p_improve"}
    if not required.issubset(rows.columns):
        raise ValueError("trajectory rows lack calibration columns")
    probabilities = ensure_finite_probabilities(
        rows["p_improve"].to_numpy(dtype=float),
        expected=len(rows),
    )
    positive = probabilities[rows["beneficial_future"].to_numpy() == 1]
    return 0.0 if positive.size == 0 else float(np.max(1.0 - positive))


def admissibility_guard(state: Mapping[str, object]) -> bool:
    """Apply the frozen evidence-completeness and terminal-verdict hard guard."""

    evidence_complete = all(
        _is_true_boolean(state.get(field))
        for field in (
            "site_evidence_present",
            "geometry_evidence_present",
            "law_evidence_present",
            "parking_evidence_present",
            "program_evidence_present",
        )
    )
    if not _is_true_boolean(state.get("parse_complete")) or not evidence_complete:
        return False
    if _native_count(state.get("missing_evidence_count")) != 0:
        return False
    blocking_count = _native_count(state.get("blocking_issue_count"))
    decision = state.get("recommended_decision")
    return (decision == "STOP_ACCEPT" and blocking_count == 0) or (
        decision == "STOP_REJECT" and blocking_count > 0
    )


class CATSStopPolicy:
    """Sequential calibrated STOP rule with patience and hard guard."""

    def __init__(
        self,
        *,
        model: Callable[[Mapping[str, object]], float] | FittedCATSClassifier,
        q_alpha: float,
        patience: int,
    ) -> None:
        if isinstance(q_alpha, bool) or not isinstance(q_alpha, (int, float)):
            raise TypeError("q_alpha must be numeric")
        if math.isnan(float(q_alpha)) or float(q_alpha) < 0.0:
            raise ValueError("q_alpha must be nonnegative")
        if type(patience) is not int or patience <= 0:
            raise ValueError("patience must be a positive native integer")
        self.model = model
        self.q_alpha = float(q_alpha)
        self.patience = patience
        self.streak = 0

    def _predict_improvement(self, state: Mapping[str, object]) -> float:
        predictor = getattr(self.model, "predict_improvement", None)
        value = predictor(state) if callable(predictor) else self.model(state)
        return float(ensure_finite_probabilities(np.array([value]), expected=1)[0])

    def observe(self, state: Mapping[str, object]) -> StopDecision:
        p_improve = self._predict_improvement(state)
        no_gain = (1.0 - p_improve) > self.q_alpha
        safe = admissibility_guard(state)
        self.streak = self.streak + 1 if no_gain and safe else 0
        stop = self.streak >= self.patience
        return StopDecision(
            stop=stop,
            reason="cats" if stop else "continue",
            p_improve=p_improve,
            calibrated_no_future_gain=no_gain,
            admissible=safe,
            streak=self.streak,
        )

    def reset(self) -> None:
        self.streak = 0


def _native_count(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        return -1
    return int(value)


def _is_true_boolean(value: object) -> bool:
    return isinstance(value, (bool, np.bool_)) and bool(value)


def _require_exact_columns(
    frame: pd.DataFrame,
    expected: Sequence[str],
    *,
    name: str,
) -> pd.DataFrame:
    expected_set = set(expected)
    actual_set = set(frame.columns)
    if actual_set != expected_set or len(frame.columns) != len(expected):
        raise ValueError(f"{name} schema mismatch")
    return frame.loc[:, expected].copy()


def _require_unique_ids(frame: pd.DataFrame, column: str, *, name: str) -> None:
    values = frame[column]
    if values.isna().any() or any(not isinstance(value, str) or not value for value in values):
        raise ValueError(f"missing {name} {column}")
    if values.duplicated().any():
        raise ValueError(f"duplicate {name} {column}")


def _validate_numeric_inputs(runtime: pd.DataFrame, labels: pd.DataFrame) -> None:
    for column in NUMERIC_FEATURES:
        converted = pd.to_numeric(runtime[column], errors="raise").to_numpy(dtype=float)
        if np.isinf(converted).any():
            raise ValueError("runtime numeric features contain infinite values")
    for column in ("quality_t", "future_max_quality"):
        converted = pd.to_numeric(labels[column], errors="raise").to_numpy(dtype=float)
        if not np.isfinite(converted).all():
            raise ValueError("private quality labels must be finite")


def assemble_frozen_dataset(
    runtime: pd.DataFrame,
    labels: pd.DataFrame,
    assignments: pd.DataFrame,
    *,
    manifest: Mapping[str, Any] | None = None,
    source_receipts: Mapping[str, Any] | None = None,
    frozen_epsilon: float | None = None,
) -> FrozenCATSData:
    """Validate separation and reconstruct identity only through opaque row IDs."""

    runtime_checked = _require_exact_columns(runtime, RUNTIME_SCHEMA, name="runtime")
    labels_checked = _require_exact_columns(labels, PRIVATE_LABEL_SCHEMA, name="private")
    assignments_checked = _require_exact_columns(
        assignments,
        ASSIGNMENT_SCHEMA,
        name="assignment",
    )
    _require_unique_ids(runtime_checked, "row_id", name="runtime")
    _require_unique_ids(labels_checked, "row_id", name="private")
    _require_unique_ids(assignments_checked, "trajectory_id", name="assignment")
    _validate_numeric_inputs(runtime_checked, labels_checked)
    if set(runtime_checked["row_id"]) != set(labels_checked["row_id"]):
        raise ValueError("runtime/private row_id mismatch")
    if any(type(value) not in (bool, np.bool_) for value in labels_checked["beneficial_future"]):
        raise ValueError("beneficial_future must be boolean")
    if frozen_epsilon is not None:
        expected_labels = (
            labels_checked["future_max_quality"].to_numpy(dtype=float)
            - labels_checked["quality_t"].to_numpy(dtype=float)
            > float(frozen_epsilon)
        )
        if not np.array_equal(
            expected_labels,
            labels_checked["beneficial_future"].to_numpy(dtype=bool),
        ):
            raise ValueError("private beneficial_future labels mismatch frozen epsilon")

    valid_partitions = {"train", "calibration", "development_gate"}
    if set(assignments_checked["partition"]) != valid_partitions:
        raise ValueError("all frozen partitions must be nonempty")
    runtime_trajectories = set(runtime_checked["trajectory_id"])
    assignment_trajectories = set(assignments_checked["trajectory_id"])
    unknown = runtime_trajectories - assignment_trajectories
    if unknown:
        raise ValueError("runtime trajectory_id missing from assignments")
    empty = assignment_trajectories - runtime_trajectories
    calibration_ids = set(
        assignments_checked.loc[
            assignments_checked["partition"] == "calibration", "trajectory_id"
        ]
    )
    if empty & calibration_ids:
        raise ValueError("empty calibration trajectories")
    if empty:
        raise ValueError("assignment trajectory missing runtime rows")

    for column in ("group_id", "site_ref"):
        partitions_by_value: defaultdict[str, set[str]] = defaultdict(set)
        for value, partition in assignments_checked[[column, "partition"]].itertuples(
            index=False,
            name=None,
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"missing assignment {column}")
            partitions_by_value[value].add(partition)
        if any(len(partitions) != 1 for partitions in partitions_by_value.values()):
            raise ValueError("group overlap across partitions")

    assignment_index = assignments_checked.set_index("trajectory_id", verify_integrity=True)
    row_mapping = runtime_checked[["row_id", "trajectory_id"]].copy()
    row_mapping["partition"] = row_mapping["trajectory_id"].map(
        assignment_index["partition"]
    )
    row_mapping["group_id"] = row_mapping["trajectory_id"].map(
        assignment_index["group_id"]
    )
    row_mapping["site_ref"] = row_mapping["trajectory_id"].map(
        assignment_index["site_ref"]
    )
    partition_by_row = row_mapping.set_index("row_id", verify_integrity=True)
    return FrozenCATSData(
        runtime=runtime_checked,
        labels=labels_checked,
        assignments=assignments_checked,
        partition_by_row=partition_by_row,
        manifest=dict(manifest or {}),
        source_receipts=dict(source_receipts or {}),
    )


def _assert_development_path(path: Path) -> None:
    for part in path.parts:
        lowered = part.lower()
        if lowered in {"test", "ood"} or lowered.startswith(
            ("test.", "test_", "test-", "ood.", "ood_", "ood-")
        ):
            raise PermissionError("held-out access is locked")


def _has_symlink_component(path: Path) -> bool:
    absolute = path.absolute()
    return any(component.is_symlink() for component in (absolute, *absolute.parents))


def _safe_dataset_manifest_paths(dataset: str | Path) -> tuple[Path, Path]:
    root = Path(dataset)
    _assert_development_path(root)
    if _has_symlink_component(root):
        raise ValueError("symlinked dataset roots are not allowed")
    resolved_root = root.resolve(strict=True)
    _assert_development_path(resolved_root)
    if not resolved_root.is_dir():
        raise ValueError("dataset root must be a directory")

    manifest_path = resolved_root / "feature_manifest.json"
    if manifest_path.is_symlink():
        raise ValueError("symlinked dataset manifests are not allowed")
    resolved_manifest = manifest_path.resolve(strict=True)
    _assert_development_path(resolved_manifest)
    try:
        resolved_manifest.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError("dataset manifest path escapes root") from error
    if not resolved_manifest.is_file():
        raise ValueError("dataset manifest must be a regular file")
    return resolved_root, resolved_manifest


def _load_jsonl_bytes(artifact: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in artifact.decode("utf-8").splitlines():
        if not line:
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("JSONL rows must be objects")
        records.append(value)
    return records


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_feature_manifest(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    if manifest.get("schema_version") != DATASET_MANIFEST_SCHEMA:
        raise ValueError("dataset manifest schema mismatch")
    access_policy = manifest.get("access_policy")
    if not isinstance(access_policy, Mapping) or (
        access_policy.get("allowed_split") != "dev"
        or access_policy.get("held_out_bundle_reads") != 0
        or access_policy.get("resolved_bundle_keys")
        != ["dev.challenged", "dev.native"]
    ):
        raise ValueError("dataset access policy mismatch")
    expected_sequences = {
        "runtime_schema": RUNTIME_SCHEMA,
        "private_label_schema": PRIVATE_LABEL_SCHEMA,
        "assignment_schema": ASSIGNMENT_SCHEMA,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "model_features": MODEL_FEATURES,
    }
    for field, expected in expected_sequences.items():
        if tuple(manifest.get(field, ())) != tuple(expected):
            raise ValueError(f"dataset {field} mismatch")
    receipt = manifest.get("artifact_receipt")
    if not isinstance(receipt, Mapping):
        raise ValueError("dataset artifact receipt missing")
    if receipt.get("schema_version") != DATASET_RECEIPT_SCHEMA:
        raise ValueError("dataset artifact receipt schema mismatch")
    if tuple(sorted(receipt.get("files", {}))) != EXPECTED_DATASET_FILES:
        raise ValueError("dataset artifact receipt file set mismatch")
    expected_contract_hash = sha256_json(asdict(StudyContract.primary()))
    if manifest.get("study_contract_sha256") != expected_contract_hash:
        raise ValueError("StudyContract receipt mismatch")
    bindings = receipt.get("bindings")
    if not isinstance(bindings, Mapping):
        raise ValueError("dataset receipt bindings missing")
    bound_fields = (
        "projection_identity_commitment",
        "snapshot_receipt_sha256",
        "split_manifest_sha256",
        "study_contract_sha256",
        "transaction_set_sha256",
    )
    if any(bindings.get(field) != manifest.get(field) for field in bound_fields):
        raise ValueError("dataset source receipt mismatch")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping) or tuple(sorted(artifacts)) != EXPECTED_DATASET_FILES:
        raise ValueError("dataset artifact metadata mismatch")
    for relative_path in EXPECTED_DATASET_FILES:
        metadata = artifacts.get(relative_path)
        if (
            not isinstance(metadata, Mapping)
            or metadata.get("sha256") != receipt["files"].get(relative_path)
        ):
            raise ValueError("dataset artifact metadata hash mismatch")
    return receipt


def load_frozen_dataset(dataset: str | Path) -> FrozenCATSData:
    """Verify and load only the three receipt-bound development artifacts."""

    root, manifest_path = _safe_dataset_manifest_paths(dataset)
    with AuthenticatedTree(root, label="frozen dataset root") as tree:
        manifest_bytes = tree.read_bytes(
            manifest_path.name,
            label="frozen dataset manifest",
        )
        manifest_value = json.loads(manifest_bytes.decode("utf-8"))
        if not isinstance(manifest_value, dict):
            raise ValueError("dataset manifest must be an object")
        receipt = _validate_feature_manifest(manifest_value)
        artifact_bytes = {
            relative_path: tree.read_bytes(
                relative_path,
                label=f"frozen dataset artifact {relative_path}",
            )
            for relative_path in EXPECTED_DATASET_FILES
        }
        verify_artifact_receipt_bytes(receipt, files=artifact_bytes)

    runtime = pd.DataFrame(
        _load_jsonl_bytes(artifact_bytes["runtime/runtime_features.jsonl"])
    )
    labels = pd.DataFrame(
        _load_jsonl_bytes(artifact_bytes["private/private_labels.jsonl"])
    )
    assignment_value = json.loads(
        artifact_bytes["private/group_assignments.json"].decode("utf-8")
    )
    if (
        not isinstance(assignment_value, dict)
        or set(assignment_value) != {"assignments", "schema_version"}
        or assignment_value.get("schema_version") != ASSIGNMENTS_SCHEMA
        or not isinstance(assignment_value.get("assignments"), list)
    ):
        raise ValueError("group assignment envelope mismatch")
    assignments = pd.DataFrame(assignment_value["assignments"])
    census = receipt.get("row_census")
    if not isinstance(census, Mapping) or (
        census.get("runtime_features") != len(runtime)
        or census.get("private_labels") != len(labels)
        or census.get("assignments") != len(assignments)
        or census.get("prefixes") != len(runtime)
    ):
        raise ValueError("dataset receipt row census mismatch")
    source_receipts = {
        "feature_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "dataset_artifact_sha256": receipt["artifact_sha256"],
        "dataset_file_sha256": dict(receipt["files"]),
        "upstream_bindings": dict(receipt["bindings"]),
    }
    return assemble_frozen_dataset(
        runtime,
        labels,
        assignments,
        manifest=manifest_value,
        source_receipts=source_receipts,
        frozen_epsilon=float(manifest_value["epsilon"]),
    )


def _build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        steps=(
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        )
    )
    categorical = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    return ColumnTransformer(
        transformers=(
            ("numeric", numeric, list(NUMERIC_FEATURES)),
            ("categorical", categorical, list(CATEGORICAL_FEATURES)),
        ),
        remainder="drop",
        sparse_threshold=0.0,
    )


def fit_cats_classifier(
    train_features: pd.DataFrame,
    train_labels: Sequence[int | bool],
    *,
    family: ModelFamily,
) -> FittedCATSClassifier:
    """Fit the complete preprocessing boundary and classifier on train rows only."""

    labels = np.asarray(tuple(train_labels), dtype=int)
    if len(train_features) != len(labels):
        raise ValueError("training feature/label count mismatch")
    if set(labels.tolist()) != {0, 1}:
        raise ValueError("training labels contain one class")
    selected = train_features.loc[:, MODEL_FEATURES]
    transformer = _build_preprocessor()
    transformed = np.asarray(transformer.fit_transform(selected), dtype=float)
    if transformed.ndim != 2 or not np.isfinite(transformed).all():
        raise ValueError("non-finite transformed training inputs")
    if family == "histgb":
        classifier: HistGradientBoostingClassifier | LogisticRegression = (
            HistGradientBoostingClassifier(
                max_iter=200,
                learning_rate=0.05,
                max_leaf_nodes=15,
                l2_regularization=1.0,
                random_state=20260819,
            )
        )
    elif family == "logistic":
        classifier = LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=20260819,
        )
    else:
        raise ValueError("unsupported frozen model family")
    classifier.fit(transformed, labels)
    probabilities = np.asarray(classifier.predict_proba(transformed), dtype=float)
    if probabilities.ndim != 2 or probabilities.shape != (len(labels), 2):
        raise ValueError("binary classifier probability shape mismatch")
    ensure_finite_probabilities(probabilities[:, 1], expected=len(labels))
    return FittedCATSClassifier(transformer, classifier, tuple(MODEL_FEATURES), family)


def _validate_variant_spec(spec: FrozenVariantSpec) -> None:
    if not spec.name or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in spec.name):
        raise ValueError("variant name must be a lowercase artifact slug")
    if spec.family not in {"histgb", "logistic"}:
        raise ValueError("unsupported frozen model family")
    if isinstance(spec.epsilon, bool) or not isinstance(spec.epsilon, (int, float)):
        raise TypeError("epsilon must be numeric")
    if not math.isfinite(float(spec.epsilon)) or float(spec.epsilon) < 0.0:
        raise ValueError("epsilon must be finite and nonnegative")
    if isinstance(spec.alpha, bool) or not isinstance(spec.alpha, (int, float)):
        raise TypeError("alpha must be numeric")
    if not 0.0 < float(spec.alpha) < 1.0:
        raise ValueError("alpha must lie strictly between zero and one")


def _partition_ids(frozen: FrozenCATSData, partition: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            frozen.assignments.loc[
                frozen.assignments["partition"] == partition,
                "trajectory_id",
            ]
        )
    )


def train_frozen_variant(
    frozen: FrozenCATSData,
    spec: FrozenVariantSpec,
) -> FrozenVariantResult:
    """Fit on train sites and calibrate one score per calibration trajectory."""

    _validate_variant_spec(spec)
    ordered_runtime = frozen.runtime.sort_values("row_id", kind="stable").reset_index(
        drop=True
    )
    row_ids = tuple(ordered_runtime["row_id"])
    label_index = frozen.labels.set_index("row_id", verify_integrity=True)
    metadata = frozen.partition_by_row.loc[list(row_ids)]
    quality_t = label_index.loc[list(row_ids), "quality_t"].to_numpy(dtype=float)
    future_max = label_index.loc[
        list(row_ids), "future_max_quality"
    ].to_numpy(dtype=float)
    targets = (future_max - quality_t > float(spec.epsilon)).astype(int)
    partitions = metadata["partition"].to_numpy()
    train_mask = partitions == "train"
    if not train_mask.any():
        raise ValueError("training partition is empty")
    fitted = fit_cats_classifier(
        ordered_runtime.loc[train_mask, MODEL_FEATURES],
        targets[train_mask],
        family=spec.family,
    )
    probabilities = fitted.predict_probabilities(ordered_runtime.loc[:, MODEL_FEATURES])
    predictions = pd.DataFrame(
        {
            "row_id": row_ids,
            "trajectory_id": metadata["trajectory_id"].to_numpy(),
            "partition": partitions,
            "p_improve": probabilities,
        }
    )
    calibration_ids = _partition_ids(frozen, "calibration")
    calibration_mask = partitions == "calibration"
    calibration = predictions.loc[calibration_mask].copy()
    calibration["beneficial_future"] = targets[calibration_mask]
    observed_calibration_ids = set(calibration["trajectory_id"])
    if set(calibration_ids) != observed_calibration_ids:
        raise ValueError("empty calibration trajectories")
    calibration_scores = tuple(
        trajectory_nonconformity(
            calibration.loc[calibration["trajectory_id"] == trajectory_id]
        )
        for trajectory_id in calibration_ids
    )
    q_alpha = finite_sample_quantile(
        np.asarray(calibration_scores, dtype=float),
        alpha=float(spec.alpha),
    )
    class_balance: dict[str, dict[str, int]] = {}
    row_census: dict[str, int] = {}
    trajectory_census: dict[str, int] = {}
    site_census: dict[str, int] = {}
    for partition in ("train", "calibration", "development_gate"):
        mask = partitions == partition
        counts = Counter(targets[mask].tolist())
        class_balance[partition] = {
            "0": int(counts.get(0, 0)),
            "1": int(counts.get(1, 0)),
        }
        row_census[partition] = int(mask.sum())
        selected_assignments = frozen.assignments[
            frozen.assignments["partition"] == partition
        ]
        trajectory_census[partition] = int(len(selected_assignments))
        site_census[partition] = int(selected_assignments["site_ref"].nunique())
    return FrozenVariantResult(
        spec=spec,
        fitted=fitted,
        predictions=predictions,
        calibration_scores=calibration_scores,
        q_alpha=q_alpha,
        class_balance=class_balance,
        row_census=row_census,
        trajectory_census=trajectory_census,
        site_census=site_census,
        train_trajectory_ids=_partition_ids(frozen, "train"),
        calibration_trajectory_ids=calibration_ids,
        development_gate_trajectory_ids=_partition_ids(frozen, "development_gate"),
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return [_jsonable(item) for item in value.tolist()]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _atomic_joblib_dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
        joblib.dump(value, temporary_path)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _prediction_records(predictions: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {
            "row_id": str(row.row_id),
            "trajectory_id": str(row.trajectory_id),
            "partition": str(row.partition),
            "p_improve": float(row.p_improve),
        }
        for row in predictions.itertuples(index=False)
    ]


def _semantic_manifest(
    result: FrozenVariantResult,
    frozen: FrozenCATSData,
    *,
    predictions_sha256: str,
) -> dict[str, Any]:
    transformed_feature_order = tuple(
        str(value) for value in result.fitted.transformer.get_feature_names_out()
    )
    classifier_parameters = _jsonable(
        result.fitted.classifier.get_params(deep=False)
    )
    return {
        "schema_version": "ace.iclr2027.cats_model_semantics.v1",
        "variant": result.spec.name,
        "family": result.spec.family,
        "epsilon": float(result.spec.epsilon),
        "alpha": float(result.spec.alpha),
        "q_alpha": (
            float(result.q_alpha) if math.isfinite(result.q_alpha) else "infinity"
        ),
        "patience": StudyContract.primary().patience,
        "random_state": 20260819,
        "feature_order": list(MODEL_FEATURES),
        "numeric_features": list(NUMERIC_FEATURES),
        "categorical_features": list(CATEGORICAL_FEATURES),
        "transformed_feature_order": list(transformed_feature_order),
        "preprocessing": {
            "fit_partition": "train",
            "transform_only_partitions": ["calibration", "development_gate"],
            "numeric": {
                "imputer": {
                    "class": "SimpleImputer",
                    "strategy": "median",
                    "add_indicator": True,
                },
                "scaler": {"class": "StandardScaler"},
            },
            "categorical": {
                "class": "OneHotEncoder",
                "handle_unknown": "ignore",
                "sparse_output": False,
            },
        },
        "classifier_parameters": classifier_parameters,
        "class_balance": _jsonable(result.class_balance),
        "row_census": _jsonable(result.row_census),
        "trajectory_census": _jsonable(result.trajectory_census),
        "site_census": _jsonable(result.site_census),
        "train_trajectory_ids": list(result.train_trajectory_ids),
        "calibration_trajectory_ids": list(result.calibration_trajectory_ids),
        "development_gate_trajectory_ids": list(
            result.development_gate_trajectory_ids
        ),
        "calibration_score_count": len(result.calibration_scores),
        "calibration_scores_sha256": sha256_json(list(result.calibration_scores)),
        "predictions_sha256": predictions_sha256,
        "source_receipts": _jsonable(frozen.source_receipts),
        "scikit_learn_version": sklearn.__version__,
    }


def write_frozen_variant(
    result: FrozenVariantResult,
    frozen: FrozenCATSData,
    output: str | Path,
) -> dict[str, Any]:
    """Write one model directory and return its registry entry."""

    variant_root = Path(output) / result.spec.name
    transformer_path = variant_root / "transformer.joblib"
    classifier_path = variant_root / "classifier.joblib"
    predictions_path = variant_root / "predictions.jsonl"
    manifest_path = variant_root / "manifest.json"
    _atomic_joblib_dump(transformer_path, result.fitted.transformer)
    _atomic_joblib_dump(classifier_path, result.fitted.classifier)
    write_jsonl_atomic(predictions_path, _prediction_records(result.predictions))
    transformer_sha256 = _sha256_file(transformer_path)
    classifier_sha256 = _sha256_file(classifier_path)
    predictions_sha256 = _sha256_file(predictions_path)
    semantic = _semantic_manifest(
        result,
        frozen,
        predictions_sha256=predictions_sha256,
    )
    semantic_sha256 = sha256_json(semantic)
    manifest = {
        "schema_version": MODEL_MANIFEST_SCHEMA,
        "semantic": semantic,
        "semantic_sha256": semantic_sha256,
        "artifacts": {
            "classifier.joblib": {
                "sha256": classifier_sha256,
                "size_bytes": classifier_path.stat().st_size,
            },
            "predictions.jsonl": {
                "sha256": predictions_sha256,
                "size_bytes": predictions_path.stat().st_size,
            },
            "transformer.joblib": {
                "sha256": transformer_sha256,
                "size_bytes": transformer_path.stat().st_size,
            },
        },
    }
    write_json_atomic(manifest_path, manifest)
    return {
        "name": result.spec.name,
        "family": result.spec.family,
        "epsilon": float(result.spec.epsilon),
        "alpha": float(result.spec.alpha),
        "q_alpha": semantic["q_alpha"],
        "path": result.spec.name,
        "manifest_sha256": _sha256_file(manifest_path),
        "semantic_sha256": semantic_sha256,
        "classifier_sha256": classifier_sha256,
        "transformer_sha256": transformer_sha256,
        "predictions_sha256": predictions_sha256,
    }


def write_all_frozen_variants(
    dataset: str | Path,
    output: str | Path,
) -> dict[str, Any]:
    """Train one complete preregistered CATS artifact matrix."""

    frozen = load_frozen_dataset(dataset)
    output_path = Path(output)
    entries = [
        write_frozen_variant(
            train_frozen_variant(frozen, spec),
            frozen,
            output_path,
        )
        for spec in FROZEN_VARIANTS
    ]
    registry = {
        "schema_version": MODEL_REGISTRY_SCHEMA,
        "source_receipts": _jsonable(frozen.source_receipts),
        "variant_count": len(entries),
        "variants": entries,
    }
    _write_model_registry(output_path, registry)
    return registry


def _write_model_registry(output: Path, registry: Mapping[str, Any]) -> None:
    """Atomically write Task 7's registry and a byte-identical compatibility alias."""

    write_json_atomic(output / "model_registry.json", registry)
    write_json_atomic(output / "registry.json", registry)
    if (output / "model_registry.json").read_bytes() != (
        output / "registry.json"
    ).read_bytes():
        raise ValueError("model registry compatibility alias mismatch")


def _canonical_prediction_artifact(path: Path) -> bytes:
    artifact = path.read_bytes()
    try:
        text = artifact.decode("utf-8")
        rows = [json.loads(line) for line in text.splitlines() if line]
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("prediction artifact is not canonical JSONL") from error
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError("prediction artifact is not canonical JSONL")
    canonical = "".join(f"{canonical_json(row)}\n" for row in rows).encode("utf-8")
    if canonical != artifact:
        raise ValueError("prediction artifact is not canonical JSONL")
    return artifact


def _validated_semantic_run(
    output: str | Path,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    root = Path(output).resolve(strict=True)
    registry_path = root / "model_registry.json"
    if registry_path.is_symlink() or not registry_path.is_file():
        raise ValueError("model registry is missing or symlinked")
    compatibility_path = root / "registry.json"
    if (
        compatibility_path.is_symlink()
        or not compatibility_path.is_file()
        or compatibility_path.read_bytes() != registry_path.read_bytes()
    ):
        raise ValueError("model registry compatibility alias mismatch")
    registry_value = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry_value, dict):
        raise ValueError("model registry must be an object")
    if (
        registry_value.get("schema_version") != MODEL_REGISTRY_SCHEMA
        or registry_value.get("variant_count") != len(FROZEN_VARIANTS)
        or not isinstance(registry_value.get("source_receipts"), Mapping)
        or not isinstance(registry_value.get("variants"), list)
    ):
        raise ValueError("model registry schema mismatch")
    entries = registry_value["variants"]
    expected_names = tuple(spec.name for spec in FROZEN_VARIANTS)
    if tuple(entry.get("name") for entry in entries) != expected_names:
        raise ValueError("model registry variant order mismatch")

    validated: dict[str, dict[str, Any]] = {}
    for entry in entries:
        relative_path = entry.get("path")
        if not isinstance(relative_path, str) or not relative_path:
            raise ValueError("model registry variant path mismatch")
        variant_root = (root / relative_path).resolve(strict=True)
        try:
            variant_root.relative_to(root)
        except ValueError as error:
            raise ValueError("model variant path escapes registry root") from error
        manifest_path = variant_root / "manifest.json"
        manifest_bytes = manifest_path.read_bytes()
        if hashlib.sha256(manifest_bytes).hexdigest() != entry.get("manifest_sha256"):
            raise ValueError("model manifest hash mismatch")
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        semantic = manifest.get("semantic")
        if not isinstance(semantic, dict):
            raise ValueError("model semantic manifest missing")
        semantic_sha256 = sha256_json(semantic)
        if (
            semantic_sha256 != manifest.get("semantic_sha256")
            or semantic_sha256 != entry.get("semantic_sha256")
        ):
            raise ValueError("model semantic manifest hash mismatch")
        predictions_path = variant_root / "predictions.jsonl"
        prediction_bytes = _canonical_prediction_artifact(predictions_path)
        prediction_sha256 = hashlib.sha256(prediction_bytes).hexdigest()
        prediction_metadata = manifest.get("artifacts", {}).get("predictions.jsonl", {})
        if (
            prediction_sha256 != prediction_metadata.get("sha256")
            or prediction_sha256 != semantic.get("predictions_sha256")
            or prediction_sha256 != entry.get("predictions_sha256")
        ):
            raise ValueError("prediction artifact hash mismatch")
        for filename, registry_field, error_message in (
            (
                "classifier.joblib",
                "classifier_sha256",
                "classifier artifact hash mismatch",
            ),
            (
                "transformer.joblib",
                "transformer_sha256",
                "transformer artifact hash mismatch",
            ),
        ):
            artifact_path = variant_root / filename
            if artifact_path.is_symlink() or not artifact_path.is_file():
                raise ValueError(error_message)
            artifact_sha256 = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            artifact_metadata = manifest.get("artifacts", {}).get(filename, {})
            if (
                artifact_sha256 != artifact_metadata.get("sha256")
                or artifact_sha256 != entry.get(registry_field)
            ):
                raise ValueError(error_message)
        if (
            semantic.get("variant") != entry.get("name")
            or semantic.get("family") != entry.get("family")
            or semantic.get("epsilon") != entry.get("epsilon")
            or semantic.get("alpha") != entry.get("alpha")
            or semantic.get("q_alpha") != entry.get("q_alpha")
            or semantic.get("source_receipts") != registry_value["source_receipts"]
        ):
            raise ValueError("model registry semantic binding mismatch")
        validated[str(entry["name"])] = {
            "entry": entry,
            "semantic": semantic,
            "prediction_bytes": prediction_bytes,
        }
    return registry_value, validated


def compare_semantic_training_runs(
    left: str | Path,
    right: str | Path,
) -> dict[str, Any]:
    """Compare two isolated training outputs without requiring joblib equality."""

    left_registry, left_variants = _validated_semantic_run(left)
    right_registry, right_variants = _validated_semantic_run(right)
    if left_registry["source_receipts"] != right_registry["source_receipts"]:
        raise ValueError("semantic determinism source receipt mismatch")
    comparisons: list[dict[str, Any]] = []
    for spec in FROZEN_VARIANTS:
        left_variant = left_variants[spec.name]
        right_variant = right_variants[spec.name]
        left_semantic = left_variant["semantic"]
        right_semantic = right_variant["semantic"]
        matching = {
            "alpha": left_semantic["alpha"] == right_semantic["alpha"],
            "canonical_predictions": left_variant["prediction_bytes"]
            == right_variant["prediction_bytes"],
            "classifier_parameters": left_semantic["classifier_parameters"]
            == right_semantic["classifier_parameters"],
            "epsilon": left_semantic["epsilon"] == right_semantic["epsilon"],
            "feature_order": (
                left_semantic["feature_order"] == right_semantic["feature_order"]
                and left_semantic["transformed_feature_order"]
                == right_semantic["transformed_feature_order"]
            ),
            "q_alpha": left_semantic["q_alpha"] == right_semantic["q_alpha"],
            "semantic_manifest": left_semantic == right_semantic,
            "source_receipts": left_semantic["source_receipts"]
            == right_semantic["source_receipts"],
        }
        failed = tuple(name for name, matches in matching.items() if not matches)
        if failed:
            raise ValueError(
                f"semantic determinism mismatch for {spec.name}: {','.join(failed)}"
            )
        comparisons.append(
            {
                "name": spec.name,
                "family": left_semantic["family"],
                "epsilon": left_semantic["epsilon"],
                "alpha": left_semantic["alpha"],
                "q_alpha": left_semantic["q_alpha"],
                "semantic_sha256": left_variant["entry"]["semantic_sha256"],
                "predictions_sha256": left_variant["entry"]["predictions_sha256"],
                "matching": matching,
            }
        )
    payload = {
        "schema_version": SEMANTIC_DETERMINISM_SCHEMA,
        "isolated_training_run_count": 2,
        "raw_joblib_equality_required": False,
        "source_receipts": left_registry["source_receipts"],
        "source_receipts_sha256": sha256_json(left_registry["source_receipts"]),
        "variant_count": len(comparisons),
        "variants": comparisons,
    }
    return {**payload, "receipt_sha256": sha256_json(payload)}


def _validate_bound_publication(output: Path) -> dict[str, Any]:
    registry, variants = _validated_semantic_run(output)
    binding = registry.get("semantic_determinism")
    if not isinstance(binding, Mapping) or (
        binding.get("path") != "semantic_determinism.json"
        or binding.get("schema_version") != SEMANTIC_DETERMINISM_SCHEMA
    ):
        raise ValueError("semantic determinism registry binding mismatch")
    receipt_path = output / "semantic_determinism.json"
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise ValueError("semantic determinism receipt missing")
    receipt_bytes = receipt_path.read_bytes()
    if hashlib.sha256(receipt_bytes).hexdigest() != binding.get("sha256"):
        raise ValueError("semantic determinism receipt file hash mismatch")
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    if not isinstance(receipt, dict):
        raise ValueError("semantic determinism receipt must be an object")
    payload = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if (
        receipt.get("schema_version") != SEMANTIC_DETERMINISM_SCHEMA
        or receipt.get("receipt_sha256") != sha256_json(payload)
        or receipt.get("receipt_sha256") != binding.get("receipt_sha256")
        or receipt.get("source_receipts") != registry.get("source_receipts")
        or receipt.get("isolated_training_run_count") != 2
        or receipt.get("variant_count") != len(FROZEN_VARIANTS)
        or receipt.get("raw_joblib_equality_required") is not False
        or receipt.get("published_output_matches_verified_run") is not True
        or not isinstance(receipt.get("variants"), list)
    ):
        raise ValueError("semantic determinism receipt binding mismatch")
    expected_matching = {
        "alpha": True,
        "canonical_predictions": True,
        "classifier_parameters": True,
        "epsilon": True,
        "feature_order": True,
        "q_alpha": True,
        "semantic_manifest": True,
        "source_receipts": True,
    }
    receipt_variants = receipt["variants"]
    if tuple(item.get("name") for item in receipt_variants) != tuple(
        spec.name for spec in FROZEN_VARIANTS
    ):
        raise ValueError("semantic determinism receipt variant mismatch")
    for item in receipt_variants:
        validated = variants[str(item["name"])]
        entry = validated["entry"]
        if (
            item.get("matching") != expected_matching
            or item.get("semantic_sha256") != entry.get("semantic_sha256")
            or item.get("predictions_sha256") != entry.get("predictions_sha256")
            or item.get("family") != entry.get("family")
            or item.get("epsilon") != entry.get("epsilon")
            or item.get("alpha") != entry.get("alpha")
            or item.get("q_alpha") != entry.get("q_alpha")
        ):
            raise ValueError("semantic determinism receipt variant mismatch")
    return registry


def _remove_staged_directory(path: Path, *, parent: Path, prefix: str) -> None:
    if not path.exists():
        return
    if path.is_symlink() or path.parent != parent or not path.name.startswith(prefix):
        raise ValueError("refusing unsafe staged-directory cleanup")
    shutil.rmtree(path)


def _directory_tree_digest(root: Path) -> str:
    """Preflight and digest a publication through retained directory handles."""

    directories: list[str] = []
    files: dict[str, str] = {}

    def scan(
        relative_parent: Path,
        authenticated: AuthenticatedTree,
    ) -> None:
        relative_directory = relative_parent if relative_parent.parts else None
        entries = authenticated.list_directory(
            relative_directory,
            label=(
                "publication tree root"
                if relative_directory is None
                else f"publication directory {relative_parent.as_posix()}"
            ),
        )
        for entry in entries:
            relative = relative_parent / entry.name
            relative_name = relative.as_posix()
            if entry.is_directory:
                directories.append(relative_name)
                scan(relative, authenticated)
                continue
            artifact = authenticated.read_bytes(
                relative_name,
                label=f"publication file {relative_name}",
            )
            files[relative_name] = hashlib.sha256(artifact).hexdigest()

    with AuthenticatedTree(root, label="publication tree") as authenticated:
        scan(Path(), authenticated)
    return sha256_json(
        {
            "directories": directories,
            "files": files,
        }
    )


def _cleanup_committed_backup(backup: Path, *, output: Path, suffix: str) -> None:
    if not backup.exists():
        return
    cleanup = output.parent / f".{output.name}.cleanup-{suffix}"
    try:
        os.replace(backup, cleanup)
    except BaseException as error:
        warnings.warn(
            f"post-commit backup cleanup rename failed; residue={backup.name}: {error}",
            RuntimeWarning,
            stacklevel=2,
        )
        return
    try:
        shutil.rmtree(cleanup)
    except BaseException as error:
        warnings.warn(
            f"post-commit backup cleanup failed; residue={cleanup.name}: {error}",
            RuntimeWarning,
            stacklevel=2,
        )


def _restore_backup_by_copy(
    backup: Path,
    output: Path,
    *,
    suffix: str,
) -> None:
    parent = output.parent
    restoration = parent / f".{output.name}.restore-{suffix}"
    if os.path.lexists(output) or os.path.lexists(restoration):
        raise ValueError("publication copy restoration path already exists")
    expected_digest = _directory_tree_digest(backup)
    try:
        shutil.copytree(backup, restoration, copy_function=shutil.copy2)
        if _directory_tree_digest(restoration) != expected_digest:
            raise ValueError("publication copy restoration digest mismatch")
        os.replace(restoration, output)
        if _directory_tree_digest(output) != expected_digest:
            raise ValueError("authoritative copy restoration digest mismatch")
    finally:
        _remove_staged_directory(
            restoration,
            parent=parent,
            prefix=f".{output.name}.restore-",
        )


def _restore_moved_backup(backup: Path, output: Path, *, suffix: str) -> None:
    try:
        os.replace(backup, output)
    except BaseException:
        _restore_backup_by_copy(backup, output, suffix=suffix)
        _cleanup_committed_backup(backup, output=output, suffix=suffix)


def _publish_candidate_directory(candidate: Path, output: Path) -> None:
    parent = output.parent
    suffix = candidate.name.removeprefix(f".{output.name}.candidate-")
    backup = parent / f".{output.name}.backup-{suffix}"
    if os.path.lexists(backup):
        raise ValueError("publication backup path already exists")
    previous_exists = os.path.lexists(output)
    if previous_exists:
        original_digest = _directory_tree_digest(output)
        os.replace(output, backup)
        try:
            backup_digest = _directory_tree_digest(backup)
            if backup_digest != original_digest:
                raise ValueError(
                    "authoritative publication changed between preflight and backup "
                    "validation"
                )
        except BaseException as validation_error:
            _restore_moved_backup(backup, output, suffix=suffix)
            raise validation_error
    try:
        os.replace(candidate, output)
    except BaseException as publication_error:
        if previous_exists:
            _restore_moved_backup(backup, output, suffix=suffix)
        raise publication_error
    if not previous_exists:
        return
    _cleanup_committed_backup(backup, output=output, suffix=suffix)


def write_verified_frozen_variants(
    dataset: str | Path,
    output: str | Path,
    *,
    verification_hook: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Verify a complete staged candidate, then atomically publish its directory."""

    requested_output = Path(output).absolute()
    parent = requested_output.parent
    parent.mkdir(parents=True, exist_ok=True)
    if requested_output.is_symlink():
        raise ValueError("authoritative model output must not be symlinked")
    candidate = Path(
        tempfile.mkdtemp(
            prefix=f".{requested_output.name}.candidate-",
            dir=parent,
        )
    )
    try:
        candidate_registry = write_all_frozen_variants(dataset, candidate)
        with tempfile.TemporaryDirectory(
            prefix=f".{requested_output.name}.verification-",
            dir=parent,
        ) as temporary:
            temporary_root = Path(temporary)
            left = temporary_root / "run1"
            right = temporary_root / "run2"
            write_all_frozen_variants(dataset, left)
            write_all_frozen_variants(dataset, right)
            receipt = compare_semantic_training_runs(left, right)
            candidate_comparison = compare_semantic_training_runs(candidate, left)
            if receipt["variants"] != candidate_comparison["variants"]:
                raise ValueError("candidate model output differs from verified isolated run")

        receipt_payload = {
            key: value for key, value in receipt.items() if key != "receipt_sha256"
        }
        receipt_payload["published_output_matches_verified_run"] = True
        receipt = {
            **receipt_payload,
            "receipt_sha256": sha256_json(receipt_payload),
        }
        receipt_path = candidate / "semantic_determinism.json"
        write_json_atomic(receipt_path, receipt)
        bound_registry = {
            **candidate_registry,
            "semantic_determinism": {
                "path": "semantic_determinism.json",
                "schema_version": SEMANTIC_DETERMINISM_SCHEMA,
                "sha256": _sha256_file(receipt_path),
                "receipt_sha256": receipt["receipt_sha256"],
            },
        }
        _write_model_registry(candidate, bound_registry)
        validated_registry = _validate_bound_publication(candidate)
        if verification_hook is not None:
            verification_hook()
        _publish_candidate_directory(candidate, requested_output)
        return validated_registry
    finally:
        _remove_staged_directory(
            candidate,
            parent=parent,
            prefix=f".{requested_output.name}.candidate-",
        )


__all__ = (
    "CATSStopPolicy",
    "FROZEN_VARIANTS",
    "FittedCATSClassifier",
    "FrozenCATSData",
    "FrozenVariantResult",
    "FrozenVariantSpec",
    "StopDecision",
    "admissibility_guard",
    "assemble_frozen_dataset",
    "compare_semantic_training_runs",
    "ensure_finite_probabilities",
    "finite_sample_quantile",
    "fit_cats_classifier",
    "load_frozen_dataset",
    "train_frozen_variant",
    "trajectory_nonconformity",
    "write_all_frozen_variants",
    "write_frozen_variant",
    "write_verified_frozen_variants",
)
