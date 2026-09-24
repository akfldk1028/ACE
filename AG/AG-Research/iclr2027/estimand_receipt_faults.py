"""Deterministic public fault census with evaluator/gold separation."""

from __future__ import annotations

import itertools
from collections import Counter
from dataclasses import dataclass

from iclr2027.estimand_receipt_generator import (
    CleanBenchmarkV1,
    ObservedArtifactV1,
    PolicyRecordV1,
    ScoreWeightV1,
    TrustRootV1,
)
from iclr2027.io import canonical_json, sha256_json


_FAMILY_FAULTS = {
    "E": (
        "execution_omit_geometry",
        "execution_omit_law",
        "execution_omit_parking",
        "execution_omit_program",
        "execution_omit_site_evidence",
    ),
    "B": (
        "target_rebind_same_site_same_assignment",
        "target_rebind_same_site_other_assignment",
        "target_rebind_other_site_same_assignment",
        "target_rebind_other_site_other_assignment",
    ),
    "T": (
        "terminal_stale_owner",
        "terminal_stale_value",
        "terminal_stale_owner_and_value",
    ),
    "S": (
        "scorer_drop_geometry",
        "scorer_duplicate_geometry_as_shadow",
        "scorer_shift_geometry_to_law",
        "scorer_replace_program_with_shadow",
    ),
    "G": (
        "protocol_stale_incompatible",
        "protocol_future_incompatible",
    ),
    "P": (
        "policy_menu_drift",
        "policy_information_snapshot_drift",
        "policy_cost_drift",
        "policy_decision_event_drift",
    ),
}
_PRIMARY_FAMILY_ORDER = ("E", "B", "T", "S", "G", "P")
_REPRESENTATIVE = {family: names[0] for family, names in _FAMILY_FAULTS.items()}
_FAMILY_BY_FAULT = {
    name: family for family, names in _FAMILY_FAULTS.items() for name in names
}

ATOMIC_FAULTS = tuple(sorted(_FAMILY_BY_FAULT, key=lambda value: value.encode("utf-8")))
INVARIANCE_CONTROLS = tuple(
    sorted(
        (
            "protocol_registered_compatible",
            "scorer_add_zero_mass_shadow",
            "target_registered_within_stratum",
        ),
        key=lambda value: value.encode("utf-8"),
    )
)

_EXPECTED_CASE_COUNTS = {
    "clean": 64,
    "single": 1_408,
    "ordered_compound": 1_920,
    "invariance": 192,
}
_EXPECTED_STATUSES = frozenset(("CERTIFIED", "NOT_CERTIFIED"))
_BLOCKING_FAMILIES = {
    "tau_itt": frozenset(("B", "T", "S", "G")),
    "tau_cb": frozenset(("E", "B", "T", "S", "G")),
    "psi_natural": frozenset(("B", "T", "S", "G", "P")),
}


def _require_nonempty_string(value: object, label: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(label)
    return value


def _require_string_tuple(
    value: object, label: str, *, unique: bool = True
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(label)
    checked = tuple(_require_nonempty_string(item, label) for item in value)
    if unique and len(set(checked)) != len(checked):
        raise ValueError(label)
    return checked


def _require_digest(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(label)
    return value


@dataclass(frozen=True)
class PublicMutationOracleV1:
    """Gold metadata serialized outside the evaluator-visible artifact."""

    schema_version: str
    case_id: str
    case_kind: str
    mutation_names: tuple[str, ...]
    families: tuple[str, ...]
    partner_unit_ids: tuple[str, ...]
    expected_statuses: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != "public-mutation-oracle/v1":
            raise ValueError("oracle schema")
        _require_nonempty_string(self.case_id, "case id")
        if self.case_kind not in _EXPECTED_CASE_COUNTS:
            raise ValueError("case kind")
        names = _require_string_tuple(self.mutation_names, "mutation names")
        families = _require_string_tuple(self.families, "families")
        partners = _require_string_tuple(self.partner_unit_ids, "partner unit ids")
        statuses = _require_string_tuple(
            self.expected_statuses, "expected statuses", unique=False
        )
        if any(family not in _PRIMARY_FAMILY_ORDER for family in families):
            raise ValueError("families")
        if len(statuses) != 3 or any(
            status not in _EXPECTED_STATUSES for status in statuses
        ):
            raise ValueError("expected statuses")
        if len(partners) > 1:
            raise ValueError("partner unit ids")
        if self.case_kind == "clean" and (names or families or partners):
            raise ValueError("clean oracle")
        if self.case_kind == "single" and (len(names) != 1 or len(families) != 1):
            raise ValueError("single oracle")
        if self.case_kind == "ordered_compound" and (
            len(names) != 2 or len(families) != 2
        ):
            raise ValueError("compound oracle")
        if self.case_kind == "invariance" and (len(names) != 1 or families):
            raise ValueError("invariance oracle")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "case_kind": self.case_kind,
            "mutation_names": list(self.mutation_names),
            "families": list(self.families),
            "partner_unit_ids": list(self.partner_unit_ids),
            "expected_statuses": list(self.expected_statuses),
        }


@dataclass(frozen=True)
class PublicMutationRowV1:
    """One sealed public artifact paired with a non-visible oracle record."""

    schema_version: str
    case_id: str
    artifact: ObservedArtifactV1
    artifact_sha256: str
    oracle: PublicMutationOracleV1

    def __post_init__(self) -> None:
        if self.schema_version != "public-mutation-row/v1":
            raise ValueError("mutation row schema")
        _require_nonempty_string(self.case_id, "case id")
        if type(self.artifact) is not ObservedArtifactV1:
            raise ValueError("artifact")
        ObservedArtifactV1.from_dict(self.artifact.to_dict())
        digest = _require_digest(self.artifact_sha256, "artifact digest")
        if digest != sha256_json(self.artifact.to_dict()):
            raise ValueError("artifact digest mismatch")
        if type(self.oracle) is not PublicMutationOracleV1:
            raise ValueError("oracle")
        if self.oracle.case_id != self.case_id:
            raise ValueError("oracle case id")

    def public_to_dict(self) -> dict[str, object]:
        """Return a label-free anonymous transport row."""

        return {
            "schema_version": "public-artifact-row/v1",
            "case_id": self.case_id,
            "artifact": self.artifact.to_dict(),
        }

    def oracle_to_dict(self) -> dict[str, object]:
        """Return the separately serializable gold channel."""

        return self.oracle.to_dict()

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "artifact_sha256": self.artifact_sha256,
            "artifact": self.artifact.to_dict(),
            "oracle": self.oracle.to_dict(),
        }


@dataclass(frozen=True)
class PublicMutationCensusV1:
    """The frozen 3,584-row public engineering census."""

    schema_version: str
    trust_root: TrustRootV1
    rows: tuple[PublicMutationRowV1, ...]

    def __post_init__(self) -> None:
        if self.schema_version != "public-mutation-census/v1":
            raise ValueError("census schema")
        if type(self.trust_root) is not TrustRootV1:
            raise ValueError("trust root")
        TrustRootV1.from_dict(self.trust_root.to_dict())
        if type(self.rows) is not tuple or any(
            type(row) is not PublicMutationRowV1 for row in self.rows
        ):
            raise ValueError("census rows")
        if len(self.rows) != 3_584:
            raise ValueError("census size")
        if self.counts != _EXPECTED_CASE_COUNTS:
            raise ValueError("census counts")

        rows_by_artifact: dict[bytes, list[PublicMutationRowV1]] = {}
        bytes_by_digest: dict[str, bytes] = {}
        for row in self.rows:
            artifact_bytes = canonical_json(row.artifact.to_dict()).encode("utf-8")
            prior_bytes = bytes_by_digest.setdefault(
                row.artifact_sha256, artifact_bytes
            )
            if prior_bytes != artifact_bytes:
                raise ValueError("artifact digest collision")
            rows_by_artifact.setdefault(artifact_bytes, []).append(row)

        anonymous_rows: list[PublicMutationRowV1] = []
        for byte_identical_rows in rows_by_artifact.values():
            decisions = {row.oracle.expected_statuses for row in byte_identical_rows}
            if len(decisions) != 1:
                raise ValueError("ambiguous census oracle decisions")
            artifact_sha256 = byte_identical_rows[0].artifact_sha256
            for occurrence_rank, row in enumerate(byte_identical_rows):
                case_id = sha256_json(
                    {
                        "schema_version": "public-case-id/v1",
                        "artifact_sha256": artifact_sha256,
                        "occurrence_rank": occurrence_rank,
                    }
                )
                oracle = PublicMutationOracleV1(
                    schema_version=row.oracle.schema_version,
                    case_id=case_id,
                    case_kind=row.oracle.case_kind,
                    mutation_names=row.oracle.mutation_names,
                    families=row.oracle.families,
                    partner_unit_ids=row.oracle.partner_unit_ids,
                    expected_statuses=row.oracle.expected_statuses,
                )
                anonymous_rows.append(
                    PublicMutationRowV1(
                        schema_version=row.schema_version,
                        case_id=case_id,
                        artifact=row.artifact,
                        artifact_sha256=row.artifact_sha256,
                        oracle=oracle,
                    )
                )
        anonymous_rows.sort(key=lambda row: row.case_id.encode("utf-8"))
        case_ids = tuple(row.case_id for row in anonymous_rows)
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("case ids")
        object.__setattr__(self, "rows", tuple(anonymous_rows))

    @property
    def artifacts(self) -> tuple[ObservedArtifactV1, ...]:
        return tuple(row.artifact for row in self.rows)

    @property
    def oracle_records(self) -> tuple[PublicMutationOracleV1, ...]:
        return tuple(row.oracle for row in self.rows)

    @property
    def counts(self) -> dict[str, int]:
        observed = Counter(row.oracle.case_kind for row in self.rows)
        return {kind: observed[kind] for kind in _EXPECTED_CASE_COUNTS}

    def public_to_dict(self) -> dict[str, object]:
        """Serialize artifacts without any oracle labels."""

        return {
            "schema_version": "public-mutation-artifacts/v1",
            "trust_root": self.trust_root.to_dict(),
            "artifact_rows": [row.public_to_dict() for row in self.rows],
        }

    def oracle_to_dict(self) -> dict[str, object]:
        """Serialize the isolated oracle sidecar."""

        records = [row.oracle_to_dict() for row in self.rows]
        records.sort(key=lambda record: sha256_json(record).encode("utf-8"))
        return {
            "schema_version": "public-mutation-oracles/v1",
            "oracle_records": records,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "public": self.public_to_dict(),
            "oracle": self.oracle_to_dict(),
        }


def _unit_coordinates(unit_id: str) -> tuple[int, int]:
    try:
        prefix, site_text, target_text = unit_id.rsplit("-", 2)
        site = int(site_text)
        target = int(target_text)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("synthetic unit id") from exc
    if (
        prefix != "syn-target"
        or not 0 <= site < 8
        or not 0 <= target < 8
        or unit_id != f"syn-target-{site:02d}-{target:02d}"
    ):
        raise ValueError("synthetic unit id")
    return site, target


def _expected_partner_coordinates(
    unit_id: str, mutation_name: str
) -> tuple[int, int] | None:
    site, target = _unit_coordinates(unit_id)
    if mutation_name == "target_rebind_same_site_same_assignment":
        return site, target ^ 4
    if mutation_name == "target_rebind_same_site_other_assignment":
        return site, target ^ 1
    if mutation_name == "target_rebind_other_site_same_assignment":
        return site ^ 1, target
    if mutation_name == "target_rebind_other_site_other_assignment":
        return site ^ 1, target ^ 1
    if mutation_name == "target_registered_within_stratum":
        return site, target ^ 2
    return None


def _validate_partner(
    artifact: ObservedArtifactV1,
    mutation_name: str,
    partner: ObservedArtifactV1,
) -> None:
    expected = _expected_partner_coordinates(artifact.unit_id, mutation_name)
    if expected is not None and _unit_coordinates(partner.unit_id) != expected:
        raise ValueError("mutation partner")


def _weights(values: dict[str, float]) -> list[dict[str, object]]:
    return [
        ScoreWeightV1(
            schema_version="score-weight/v1",
            key=key,
            weight=values[key],
        ).to_dict()
        for key in sorted(values, key=lambda value: value.encode("utf-8"))
    ]


def _reseal(
    artifact: ObservedArtifactV1, changes: dict[str, object]
) -> ObservedArtifactV1:
    payload = artifact.to_dict()
    del payload["payload_sha256"]
    payload.update(changes)
    return ObservedArtifactV1.from_dict(
        {**payload, "payload_sha256": sha256_json(payload)}
    )


def _mutated_policy(artifact: ObservedArtifactV1, name: str) -> dict[str, object]:
    value = artifact.policy_record.to_dict()
    if name == "policy_menu_drift":
        value["action_menu"] = [
            "action-baseline-v1",
            "action-receipt-v1",
            "action-shadow-v1",
        ]
    elif name == "policy_information_snapshot_drift":
        value["information_snapshot_sha256"] = sha256_json(
            {
                "schema_version": "fault-policy-information-snapshot/v1",
                "unit_id": artifact.unit_id,
                "source_information_snapshot_sha256": (
                    artifact.policy_record.information_snapshot_sha256
                ),
            }
        )
    elif name == "policy_cost_drift":
        value["realized_cost"] = artifact.policy_record.realized_cost + 1.0
    elif name == "policy_decision_event_drift":
        value["decision_event_sha256"] = sha256_json(
            {
                "schema_version": "fault-policy-decision-event/v1",
                "unit_id": artifact.unit_id,
                "source_decision_event_sha256": (
                    artifact.policy_record.decision_event_sha256
                ),
            }
        )
    else:
        raise ValueError("policy fault")
    return PolicyRecordV1.from_dict(value).to_dict()


def apply_fault(
    artifact: ObservedArtifactV1,
    name: str,
    *,
    partner: ObservedArtifactV1,
) -> ObservedArtifactV1:
    """Apply one registered harmful fault and fully reseal the artifact."""

    if type(artifact) is not ObservedArtifactV1:
        raise TypeError("artifact")
    if type(partner) is not ObservedArtifactV1:
        raise TypeError("partner")
    if name not in _FAMILY_BY_FAULT:
        raise ValueError("fault name")
    _validate_partner(artifact, name, partner)

    if name.startswith("execution_omit_"):
        domain = name.removeprefix("execution_omit_")
        changes: dict[str, object] = {
            "executed_action_id": f"partial-action-omit-{domain}-v1"
        }
    elif name.startswith("target_rebind_"):
        changes = {"target_binding_sha256": partner.target_binding_sha256}
    elif name.startswith("terminal_"):
        changes = {}
        if name in ("terminal_stale_owner", "terminal_stale_owner_and_value"):
            changes["terminal_owner_id"] = f"{artifact.terminal_owner_id}-stale"
        if name in ("terminal_stale_value", "terminal_stale_owner_and_value"):
            changes["terminal_value_sha256"] = sha256_json(
                {
                    "schema_version": "fault-terminal/v1",
                    "unit_id": artifact.unit_id,
                    "source_terminal_value_sha256": artifact.terminal_value_sha256,
                }
            )
    elif name == "scorer_drop_geometry":
        changes = {
            "scorer_weights": _weights(
                {
                    "law": 0.25,
                    "parking": 0.25,
                    "program": 0.25,
                    "site_evidence": 0.25,
                }
            )
        }
    elif name == "scorer_duplicate_geometry_as_shadow":
        changes = {
            "scorer_weights": _weights(
                {
                    "geometry": 0.1,
                    "geometry_shadow": 0.1,
                    "law": 0.2,
                    "parking": 0.2,
                    "program": 0.2,
                    "site_evidence": 0.2,
                }
            )
        }
    elif name == "scorer_shift_geometry_to_law":
        changes = {
            "scorer_weights": _weights(
                {
                    "geometry": 0.3,
                    "law": 0.1,
                    "parking": 0.2,
                    "program": 0.2,
                    "site_evidence": 0.2,
                }
            )
        }
    elif name == "scorer_replace_program_with_shadow":
        changes = {
            "scorer_weights": _weights(
                {
                    "geometry": 0.2,
                    "law": 0.2,
                    "parking": 0.2,
                    "program_shadow": 0.2,
                    "site_evidence": 0.2,
                }
            )
        }
    elif name == "protocol_stale_incompatible":
        changes = {"protocol_version": "estimand-receipt-protocol-v0-stale"}
    elif name == "protocol_future_incompatible":
        changes = {"protocol_version": "estimand-receipt-protocol-v2-future"}
    else:
        changes = {"policy_record": _mutated_policy(artifact, name)}
    return _reseal(artifact, changes)


def _apply_invariance(
    artifact: ObservedArtifactV1,
    name: str,
    *,
    partner: ObservedArtifactV1,
) -> ObservedArtifactV1:
    if name not in INVARIANCE_CONTROLS:
        raise ValueError("invariance name")
    _validate_partner(artifact, name, partner)
    if name == "protocol_registered_compatible":
        changes: dict[str, object] = {
            "protocol_version": "estimand-receipt-protocol-v1-compatible"
        }
    elif name == "scorer_add_zero_mass_shadow":
        changes = {
            "scorer_weights": _weights(
                {
                    "geometry": 0.2,
                    "law": 0.2,
                    "parking": 0.2,
                    "program": 0.2,
                    "site_evidence": 0.2,
                    "zero_mass_shadow": 0.0,
                }
            )
        }
    else:
        changes = {"target_binding_sha256": partner.target_binding_sha256}
    return _reseal(artifact, changes)


def _expected_statuses(families: tuple[str, ...]) -> tuple[str, ...]:
    family_set = frozenset(families)
    return tuple(
        "NOT_CERTIFIED" if family_set & blocked else "CERTIFIED"
        for blocked in _BLOCKING_FAMILIES.values()
    )


def materialize_public_census(clean: CleanBenchmarkV1) -> PublicMutationCensusV1:
    """Materialize clean, single, ordered-compound, and invariance rows."""

    if type(clean) is not CleanBenchmarkV1:
        raise TypeError("clean benchmark")
    source_by_coordinates = {
        _unit_coordinates(artifact.unit_id): artifact for artifact in clean.artifacts
    }
    rows: list[PublicMutationRowV1] = []

    def partner_for(
        source: ObservedArtifactV1, mutation_name: str
    ) -> ObservedArtifactV1:
        coordinates = _expected_partner_coordinates(source.unit_id, mutation_name)
        return source if coordinates is None else source_by_coordinates[coordinates]

    def append_row(
        artifact: ObservedArtifactV1,
        case_kind: str,
        mutation_names: tuple[str, ...],
        families: tuple[str, ...],
        partner_unit_ids: tuple[str, ...],
    ) -> None:
        case_id = f"public-mutation-case-{len(rows):04d}"
        oracle = PublicMutationOracleV1(
            schema_version="public-mutation-oracle/v1",
            case_id=case_id,
            case_kind=case_kind,
            mutation_names=mutation_names,
            families=families,
            partner_unit_ids=partner_unit_ids,
            expected_statuses=_expected_statuses(families),
        )
        rows.append(
            PublicMutationRowV1(
                schema_version="public-mutation-row/v1",
                case_id=case_id,
                artifact=artifact,
                artifact_sha256=sha256_json(artifact.to_dict()),
                oracle=oracle,
            )
        )

    for source in clean.artifacts:
        append_row(source, "clean", (), (), ())

    for name in ATOMIC_FAULTS:
        family = _FAMILY_BY_FAULT[name]
        for source in clean.artifacts:
            partner = partner_for(source, name)
            partner_ids = (partner.unit_id,) if family == "B" else ()
            append_row(
                apply_fault(source, name, partner=partner),
                "single",
                (name,),
                (family,),
                partner_ids,
            )

    for left, right in itertools.combinations(_PRIMARY_FAMILY_ORDER, 2):
        for family_order in ((left, right), (right, left)):
            names = tuple(_REPRESENTATIVE[family] for family in family_order)
            for source in clean.artifacts:
                artifact = source
                partner_ids: tuple[str, ...] = ()
                for family, name in zip(family_order, names, strict=True):
                    partner = partner_for(source, name)
                    if family == "B":
                        partner_ids = (partner.unit_id,)
                    artifact = apply_fault(artifact, name, partner=partner)
                append_row(
                    artifact,
                    "ordered_compound",
                    names,
                    family_order,
                    partner_ids,
                )

    for name in INVARIANCE_CONTROLS:
        for source in clean.artifacts:
            partner = partner_for(source, name)
            partner_ids = (
                (partner.unit_id,) if name == "target_registered_within_stratum" else ()
            )
            append_row(
                _apply_invariance(source, name, partner=partner),
                "invariance",
                (name,),
                (),
                partner_ids,
            )

    return PublicMutationCensusV1(
        schema_version="public-mutation-census/v1",
        trust_root=clean.trust_root,
        rows=tuple(rows),
    )


__all__ = [
    "ATOMIC_FAULTS",
    "INVARIANCE_CONTROLS",
    "PublicMutationCensusV1",
    "PublicMutationOracleV1",
    "PublicMutationRowV1",
    "apply_fault",
    "materialize_public_census",
]
