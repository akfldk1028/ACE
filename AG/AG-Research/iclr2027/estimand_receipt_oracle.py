"""Private family oracle and exact score aggregation for frozen outputs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from iclr2027.estimand_receipt_evaluators import (
    CONFIGURATIONS,
    PublicEvaluatorDecisionV1,
    parse_frozen_evaluator_outputs,
)
from iclr2027.estimand_receipt_faults import PublicMutationRowV1
from iclr2027.estimand_receipt_generator import CleanConstructionRowV1
from iclr2027.estimand_receipts import ESTIMANDS, TrustRootV1


_FAMILY_ORDER = ("E", "B", "T", "S", "G", "P")
_BLOCKING_FAMILIES = {
    "tau_itt": frozenset(("B", "T", "S", "G")),
    "tau_cb": frozenset(("E", "B", "T", "S", "G")),
    "psi_natural": frozenset(("B", "T", "S", "G", "P")),
}
_HEX = frozenset("0123456789abcdef")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_digest(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX for character in value)
    ):
        raise ValueError(label)
    return value


def _pairs_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _load_canonical(value: object, label: str) -> object:
    if type(value) is not bytes:
        raise ValueError(label)
    try:
        parsed = json.loads(
            value.decode("utf-8"),
            object_pairs_hook=_pairs_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(label) from exc
    try:
        canonical = _canonical_bytes(parsed)
    except (TypeError, ValueError) as exc:
        raise ValueError(label) from exc
    if canonical != value:
        raise ValueError(label)
    return parsed


@dataclass(frozen=True)
class OracleDecisionV1:
    schema_version: str
    public_case_id: str
    estimand: str
    status: str
    blocking_families: tuple[str, ...]

    _KEYS = (
        "schema_version",
        "public_case_id",
        "estimand",
        "status",
        "blocking_families",
    )

    def __post_init__(self) -> None:
        if self.schema_version != "oracle-decision/v1":
            raise ValueError("oracle decision schema")
        _require_digest(self.public_case_id, "public case id")
        if self.estimand not in ESTIMANDS:
            raise ValueError("oracle estimand")
        if self.status not in ("CERTIFIED", "NOT_CERTIFIED"):
            raise ValueError("oracle status")
        families = self.blocking_families
        if type(families) is not tuple or any(
            item not in _FAMILY_ORDER for item in families
        ):
            raise ValueError("blocking families")
        if families != tuple(item for item in _FAMILY_ORDER if item in families):
            raise ValueError("blocking families")
        if (self.status == "CERTIFIED") != (not families):
            raise ValueError("oracle status closure")

    @classmethod
    def from_dict(cls, value: object) -> OracleDecisionV1:
        if type(value) is not dict or set(value) != set(cls._KEYS):
            raise ValueError("oracle decision")
        if type(value["blocking_families"]) is not list:
            raise ValueError("oracle decision")
        return cls(
            schema_version=value["schema_version"],
            public_case_id=value["public_case_id"],
            estimand=value["estimand"],
            status=value["status"],
            blocking_families=tuple(value["blocking_families"]),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "public_case_id": self.public_case_id,
            "estimand": self.estimand,
            "status": self.status,
            "blocking_families": list(self.blocking_families),
        }


@dataclass(frozen=True)
class ExactRateV1:
    numerator: int | None
    denominator: int | None

    def __post_init__(self) -> None:
        if self.numerator is None or self.denominator is None:
            if self.numerator is not None or self.denominator is not None:
                raise ValueError("exact rate")
            return
        if (
            type(self.numerator) is not int
            or type(self.denominator) is not int
            or self.numerator < 0
            or self.denominator <= 0
            or self.numerator > self.denominator
        ):
            raise ValueError("exact rate")

    def to_dict(self) -> dict[str, int | None]:
        return {"numerator": self.numerator, "denominator": self.denominator}


@dataclass(frozen=True)
class ScoreCellV1:
    configuration: str
    estimand: str
    total: int
    truth_certified: int
    truth_not_certified: int
    reported: int
    false_reported: int
    eligible_retained: int
    abstained: int
    exact_decisions: int
    false_reportability_rate: ExactRateV1
    eligible_retention_rate: ExactRateV1
    abstention_rate: ExactRateV1
    conditional_report_accuracy: ExactRateV1
    joint_decision_accuracy: ExactRateV1

    def __post_init__(self) -> None:
        if self.configuration not in CONFIGURATIONS or self.estimand not in ESTIMANDS:
            raise ValueError("score cell identity")
        counts = (
            self.total,
            self.truth_certified,
            self.truth_not_certified,
            self.reported,
            self.false_reported,
            self.eligible_retained,
            self.abstained,
            self.exact_decisions,
        )
        if any(
            type(item) is not int or item < 0 or item > self.total for item in counts
        ):
            raise ValueError("score counts")
        if self.truth_certified + self.truth_not_certified != self.total:
            raise ValueError("truth counts")
        if self.reported + self.abstained != self.total:
            raise ValueError("report counts")

    def to_dict(self) -> dict[str, object]:
        return {
            "configuration": self.configuration,
            "estimand": self.estimand,
            "total": self.total,
            "truth_certified": self.truth_certified,
            "truth_not_certified": self.truth_not_certified,
            "reported": self.reported,
            "false_reported": self.false_reported,
            "eligible_retained": self.eligible_retained,
            "abstained": self.abstained,
            "exact_decisions": self.exact_decisions,
            "false_reportability_rate": self.false_reportability_rate.to_dict(),
            "eligible_retention_rate": self.eligible_retention_rate.to_dict(),
            "abstention_rate": self.abstention_rate.to_dict(),
            "conditional_report_accuracy": self.conditional_report_accuracy.to_dict(),
            "joint_decision_accuracy": self.joint_decision_accuracy.to_dict(),
        }


@dataclass(frozen=True)
class BenchmarkScoreV1:
    schema_version: str
    cells: tuple[ScoreCellV1, ...]

    def __post_init__(self) -> None:
        if self.schema_version != "benchmark-score/v1":
            raise ValueError("benchmark score schema")
        expected = tuple(
            (configuration, estimand)
            for configuration in CONFIGURATIONS
            for estimand in ESTIMANDS
        )
        if (
            tuple((item.configuration, item.estimand) for item in self.cells)
            != expected
        ):
            raise ValueError("benchmark score cells")

    def cell(self, configuration: str, estimand: str) -> ScoreCellV1:
        try:
            return next(
                item
                for item in self.cells
                if item.configuration == configuration and item.estimand == estimand
            )
        except StopIteration as exc:
            raise KeyError((configuration, estimand)) from exc

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "cells": [item.to_dict() for item in self.cells],
        }


def oracle_reportability(
    trust_root: TrustRootV1,
    construction_row: CleanConstructionRowV1,
    mutation_row: PublicMutationRowV1,
) -> tuple[OracleDecisionV1, ...]:
    """Derive gold truth from registered family effects, never expected labels."""

    if type(trust_root) is not TrustRootV1:
        raise TypeError("trust root")
    if type(construction_row) is not CleanConstructionRowV1:
        raise TypeError("construction row")
    if type(mutation_row) is not PublicMutationRowV1:
        raise TypeError("mutation row")
    TrustRootV1.from_dict(trust_root.to_dict())
    if (
        construction_row.study_id != trust_root.study_id
        or mutation_row.artifact.study_id != trust_root.study_id
        or mutation_row.artifact.unit_id != construction_row.unit_id
        or mutation_row.artifact.site_id != construction_row.site_id
        or mutation_row.artifact.stratum_id != construction_row.stratum_id
    ):
        raise ValueError("oracle identity join")
    commitments = {
        commitment.unit_id: commitment for commitment in trust_root.commitments
    }
    commitment = commitments.get(construction_row.unit_id)
    if commitment is None or construction_row.commitment_sha256 != _sha256_json(
        commitment.to_dict()
    ):
        raise ValueError("oracle commitment join")
    family_set = frozenset(mutation_row.oracle.families)
    return tuple(
        OracleDecisionV1(
            schema_version="oracle-decision/v1",
            public_case_id=mutation_row.case_id,
            estimand=estimand,
            status=(
                "NOT_CERTIFIED"
                if family_set & _BLOCKING_FAMILIES[estimand]
                else "CERTIFIED"
            ),
            blocking_families=tuple(
                family
                for family in _FAMILY_ORDER
                if family in family_set and family in _BLOCKING_FAMILIES[estimand]
            ),
        )
        for estimand in ESTIMANDS
    )


def _validate_oracle_lattice(
    rows: tuple[OracleDecisionV1, ...],
) -> tuple[OracleDecisionV1, ...]:
    if (
        type(rows) is not tuple
        or not rows
        or any(type(item) is not OracleDecisionV1 for item in rows)
    ):
        raise ValueError("oracle decisions")
    for item in rows:
        OracleDecisionV1.from_dict(item.to_dict())
    identities = tuple((item.public_case_id, item.estimand) for item in rows)
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate oracle decision")
    case_ids = {item.public_case_id for item in rows}
    expected = {(case_id, estimand) for case_id in case_ids for estimand in ESTIMANDS}
    if set(identities) != expected:
        raise ValueError("incomplete oracle decisions")
    return rows


def freeze_oracle_decisions(rows: tuple[OracleDecisionV1, ...]) -> bytes:
    checked = _validate_oracle_lattice(rows)
    ordered = sorted(
        checked,
        key=lambda row: (
            row.public_case_id.encode("utf-8"),
            ESTIMANDS.index(row.estimand),
        ),
    )
    return _canonical_bytes(
        {
            "schema_version": "estimand-oracle-decisions/v1",
            "rows": [item.to_dict() for item in ordered],
        }
    )


def _parse_oracle_decisions(value: bytes) -> tuple[OracleDecisionV1, ...]:
    raw = _load_canonical(value, "oracle decision bytes")
    if (
        type(raw) is not dict
        or set(raw) != {"schema_version", "rows"}
        or raw["schema_version"] != "estimand-oracle-decisions/v1"
        or type(raw["rows"]) is not list
    ):
        raise ValueError("oracle decision bytes")
    try:
        rows = tuple(OracleDecisionV1.from_dict(item) for item in raw["rows"])
    except (TypeError, ValueError) as exc:
        raise ValueError("oracle decision bytes") from exc
    return _validate_oracle_lattice(rows)


def _rate(numerator: int, denominator: int) -> ExactRateV1:
    if denominator == 0:
        return ExactRateV1(numerator=None, denominator=None)
    return ExactRateV1(numerator=numerator, denominator=denominator)


def _score_cell(
    configuration: str,
    estimand: str,
    case_ids: tuple[str, ...],
    outputs: dict[tuple[str, str, str], PublicEvaluatorDecisionV1],
    truth: dict[tuple[str, str], OracleDecisionV1],
) -> ScoreCellV1:
    pairs = tuple(
        (outputs[(case_id, configuration, estimand)], truth[(case_id, estimand)])
        for case_id in case_ids
    )
    total = len(pairs)
    truth_certified = sum(item[1].status == "CERTIFIED" for item in pairs)
    truth_not_certified = total - truth_certified
    reported = sum(item[0].status == "CERTIFIED" for item in pairs)
    false_reported = sum(
        observed.status == "CERTIFIED" and expected.status == "NOT_CERTIFIED"
        for observed, expected in pairs
    )
    eligible_retained = sum(
        observed.status == "CERTIFIED" and expected.status == "CERTIFIED"
        for observed, expected in pairs
    )
    abstained = total - reported
    exact_decisions = sum(
        observed.status == expected.status for observed, expected in pairs
    )
    return ScoreCellV1(
        configuration=configuration,
        estimand=estimand,
        total=total,
        truth_certified=truth_certified,
        truth_not_certified=truth_not_certified,
        reported=reported,
        false_reported=false_reported,
        eligible_retained=eligible_retained,
        abstained=abstained,
        exact_decisions=exact_decisions,
        false_reportability_rate=_rate(false_reported, truth_not_certified),
        eligible_retention_rate=_rate(eligible_retained, truth_certified),
        abstention_rate=_rate(abstained, total),
        conditional_report_accuracy=_rate(reported - false_reported, reported),
        joint_decision_accuracy=_rate(exact_decisions, total),
    )


def score_frozen_outputs(
    evaluator_output_bytes: bytes, oracle_decision_bytes: bytes
) -> BenchmarkScoreV1:
    """Join frozen public outputs to truth only by anonymous ID and estimand."""

    output_rows = parse_frozen_evaluator_outputs(evaluator_output_bytes)
    oracle_rows = _parse_oracle_decisions(oracle_decision_bytes)
    output_case_ids = {item.public_case_id for item in output_rows}
    oracle_case_ids = {item.public_case_id for item in oracle_rows}
    if output_case_ids != oracle_case_ids:
        raise ValueError("public case id join")
    case_ids = tuple(sorted(oracle_case_ids, key=lambda item: item.encode("utf-8")))
    outputs = {
        (item.public_case_id, item.configuration, item.estimand): item
        for item in output_rows
    }
    truth = {(item.public_case_id, item.estimand): item for item in oracle_rows}
    cells = tuple(
        _score_cell(configuration, estimand, case_ids, outputs, truth)
        for configuration in CONFIGURATIONS
        for estimand in ESTIMANDS
    )
    return BenchmarkScoreV1(schema_version="benchmark-score/v1", cells=cells)


__all__ = [
    "BenchmarkScoreV1",
    "ExactRateV1",
    "OracleDecisionV1",
    "ScoreCellV1",
    "freeze_oracle_decisions",
    "oracle_reportability",
    "score_frozen_outputs",
]
