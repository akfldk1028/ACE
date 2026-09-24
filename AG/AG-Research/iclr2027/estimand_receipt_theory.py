"""Exact finite specialization for estimand-specific receipt obligations."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import TypeAlias


PhysicalValue: TypeAlias = str | int | Fraction | tuple[object, ...]
Field: TypeAlias = tuple[str, PhysicalValue]
Atom: TypeAlias = tuple[Field, ...]
FiniteLaw: TypeAlias = tuple[tuple[Atom, Fraction], ...]
PhysicalObject: TypeAlias = tuple[Field, ...]
FunctionalImage: TypeAlias = tuple[PhysicalObject, ...]
RationalInput: TypeAlias = Fraction | int | float

_COMPONENT_ORDER = ("Z", "A", "E", "B", "T", "S", "G", "P")


def _exact_fraction(value: object, label: str) -> Fraction:
    if type(value) is Fraction:
        return value
    if type(value) is int:
        return Fraction(value)
    raise ValueError(label)


def _unit_interval_fraction(value: object, label: str) -> Fraction:
    exact = _exact_fraction(value, label)
    if exact < 0 or exact > 1:
        raise ValueError(label)
    return exact


def _public_unit_interval_fraction(value: object, label: str) -> Fraction:
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(label)
        exact = Fraction(str(value))
    else:
        exact = _exact_fraction(value, label)
    if exact < 0 or exact > 1:
        raise ValueError(label)
    return exact


def _validate_manifest(manifest: object) -> tuple[Field, ...]:
    if type(manifest) is not tuple:
        raise ValueError("authenticated manifest")
    for field in manifest:
        if (
            type(field) is not tuple
            or len(field) != 2
            or type(field[0]) is not str
            or not field[0]
            or type(field[1]) is not str
        ):
            raise ValueError("authenticated manifest")
    keys = tuple(key for key, _ in manifest)
    if len(set(keys)) != len(keys) or manifest != tuple(sorted(manifest)):
        raise ValueError("authenticated manifest")
    return manifest


def _validate_physical_value(value: object, label: str) -> None:
    if type(value) in (str, int, Fraction):
        if type(value) is str and not value:
            raise ValueError(label)
        return
    if type(value) is tuple:
        for item in value:
            _validate_physical_value(item, label)
        return
    raise ValueError(label)


def _record(value: object, label: str) -> dict[str, PhysicalValue]:
    if type(value) is not tuple:
        raise ValueError(label)
    record: dict[str, PhysicalValue] = {}
    for field in value:
        if (
            type(field) is not tuple
            or len(field) != 2
            or type(field[0]) is not str
            or not field[0]
        ):
            raise ValueError(label)
        _validate_physical_value(field[1], label)
        if field[0] in record:
            raise ValueError(label)
        record[field[0]] = field[1]
    if tuple(record) != tuple(sorted(record)):
        raise ValueError(label)
    return record


def _validate_law(law: object, component: str, label: str) -> FiniteLaw:
    if type(law) is not tuple or not law:
        raise ValueError(label)
    seen_atoms: set[Atom] = set()
    total = Fraction(0)
    for weighted_atom in law:
        if type(weighted_atom) is not tuple or len(weighted_atom) != 2:
            raise ValueError(label)
        atom, mass = weighted_atom
        if type(atom) is not tuple or not atom:
            raise ValueError(label)
        for field in atom:
            if (
                type(field) is not tuple
                or len(field) != 2
                or type(field[0]) is not str
                or not field[0]
            ):
                raise ValueError(label)
            _validate_physical_value(field[1], label)
        keys = tuple(key for key, _ in atom)
        if (
            len(set(keys)) != len(keys)
            or keys.count(component) != 1
            or atom != tuple(sorted(atom))
            or atom in seen_atoms
        ):
            raise ValueError(label)
        if type(mass) is not Fraction or mass <= 0:
            raise ValueError(label)
        seen_atoms.add(atom)
        total += mass
    if total != 1:
        raise ValueError(label)
    return law


def _project_law(law: FiniteLaw, component: str) -> FiniteLaw:
    totals: dict[Atom, Fraction] = {}
    for atom, mass in law:
        retained = tuple(field for field in atom if field[0] != component)
        totals[retained] = totals.get(retained, Fraction(0)) + mass
    return tuple(sorted(totals.items(), key=lambda item: repr(item[0])))


def _arm_contrast(
    law: FiniteLaw,
    outcome_from_atom,
) -> Fraction:
    arm_mass = {0: Fraction(0), 1: Fraction(0)}
    arm_total = {0: Fraction(0), 1: Fraction(0)}
    for atom, mass in law:
        row = dict(atom)
        arm = row.get("Z")
        if type(arm) is not int or arm not in (0, 1):
            raise ValueError("estimand arm")
        outcome = _unit_interval_fraction(outcome_from_atom(row), "estimand outcome")
        arm_mass[arm] += mass
        arm_total[arm] += mass * outcome
    if arm_mass[0] == 0 or arm_mass[1] == 0:
        raise ValueError("estimand arm support")
    return arm_total[1] / arm_mass[1] - arm_total[0] / arm_mass[0]


def _tau_itt(component: str, law: FiniteLaw) -> Fraction:
    if component == "B":
        arm_mass = {0: Fraction(0), 1: Fraction(0)}
        arm_total = {0: Fraction(0), 1: Fraction(0)}
        for atom, mass in law:
            row = dict(atom)
            assignments = dict(row["assignment_objects"])
            outcomes = dict(row["outcome_objects"])
            for assignment_id, outcome_id in row["B"]:
                arm = assignments[assignment_id]
                if type(arm) is not int or arm not in (0, 1):
                    raise ValueError("B assignment")
                outcome = _unit_interval_fraction(outcomes[outcome_id], "B outcome")
                arm_mass[arm] += mass
                arm_total[arm] += mass * outcome
        if arm_mass[0] == 0 or arm_mass[1] == 0:
            raise ValueError("B arm support")
        return arm_total[1] / arm_mass[1] - arm_total[0] / arm_mass[0]

    def outcome(row: dict[str, PhysicalValue]) -> Fraction:
        if component == "Z":
            return _unit_interval_fraction(row["Y"], "Y")
        if component == "T":
            terminal = _record(row["T"], "T")
            return _unit_interval_fraction(
                dict(terminal["value_map"])[row["terminal_token"]],
                "terminal value",
            )
        if component == "S":
            scores = dict(row["key_scores"])
            weights = row["S"]
            if sum(weight for _, weight in weights) != 1:
                raise ValueError("scorer weights")
            return sum(
                _unit_interval_fraction(weight, "scorer weight")
                * _unit_interval_fraction(scores[key], "key score")
                for key, weight in weights
            )
        if component == "G":
            protocol = _record(row["G"], "G")
            return _unit_interval_fraction(
                dict(protocol["truth_map"])[row["protocol_token"]],
                "protocol value",
            )
        raise ValueError("tau ITT component")

    return _arm_contrast(law, outcome)


def _tau_cb(law: FiniteLaw) -> Fraction:
    def outcome(row: dict[str, PhysicalValue]) -> Fraction:
        requested = _record(row["A"], "A")
        execution = _record(row["E"], "E")
        requested_bundle = requested["bundle"]
        slot = dict(execution["regime_map"])[requested_bundle]
        return _unit_interval_fraction(
            dict(row["outcome_slots"])[slot],
            "bundle outcome",
        )

    return _arm_contrast(law, outcome)


def _psi_natural(law: FiniteLaw) -> Fraction:
    value = Fraction(0)
    for atom, mass in law:
        row = dict(atom)
        policy = _record(row["P"], "P")
        menu = policy["action_menu"]
        action = dict(policy["decision_rule"])[row["context"]]
        if action not in menu:
            raise ValueError("policy action")
        propensity = _unit_interval_fraction(policy["propensity"], "propensity")
        if propensity == 0:
            raise ValueError("propensity")
        outcome = _unit_interval_fraction(
            dict(row["potential_outcomes"])[action],
            "policy outcome",
        )
        value += mass * outcome
    return value


def _registered_estimand(
    component: str,
    estimand: str,
    law: FiniteLaw,
) -> Fraction:
    expected = (
        "tau_CB"
        if component in ("A", "E")
        else "Psi_N"
        if component == "P"
        else "tau_ITT"
    )
    if estimand != expected:
        raise ValueError("component estimand")
    if estimand == "tau_ITT":
        return _tau_itt(component, law)
    if estimand == "tau_CB":
        return _tau_cb(law)
    return _psi_natural(law)


@dataclass(frozen=True)
class PairedWorldWitness:
    """Exact paired worlds for one omitted receipt component."""

    component: str
    estimand: str
    full_law_p: FiniteLaw
    full_law_q: FiniteLaw
    authenticated_manifest: tuple[Field, ...]

    def __post_init__(self) -> None:
        if self.component not in _COMPONENT_ORDER:
            raise ValueError("component")
        if type(self.estimand) is not str or not self.estimand:
            raise ValueError("estimand")
        law_p = _validate_law(self.full_law_p, self.component, "full law p")
        law_q = _validate_law(self.full_law_q, self.component, "full law q")
        object.__setattr__(self, "full_law_p", law_p)
        object.__setattr__(self, "full_law_q", law_q)
        manifest = _validate_manifest(self.authenticated_manifest)
        object.__setattr__(self, "authenticated_manifest", manifest)
        if self.component in {key for key, _ in manifest}:
            raise ValueError("manifest recovers component")
        if self.projected_law_p != self.projected_law_q:
            raise ValueError("projected laws differ")
        if self.estimand_p == self.estimand_q:
            raise ValueError("estimands equal")
        if self.recoverable_from_retained:
            raise ValueError("component recoverable")

    @property
    def estimand_p(self) -> Fraction:
        return _registered_estimand(self.component, self.estimand, self.full_law_p)

    @property
    def estimand_q(self) -> Fraction:
        return _registered_estimand(self.component, self.estimand, self.full_law_q)

    @property
    def projected_law_p(self) -> FiniteLaw:
        return _project_law(self.full_law_p, self.component)

    @property
    def projected_law_q(self) -> FiniteLaw:
        return _project_law(self.full_law_q, self.component)

    @property
    def recoverable_from_retained(self) -> bool:
        manifest = {key: value for key, value in self.authenticated_manifest}
        if self.component in manifest:
            return True
        possible_values: dict[Atom, set[PhysicalValue]] = {}
        for law in (self.full_law_p, self.full_law_q):
            for atom, mass in law:
                if mass == 0:
                    continue
                retained = tuple(field for field in atom if field[0] != self.component)
                omitted = next(value for key, value in atom if key == self.component)
                possible_values.setdefault(retained, set()).add(omitted)
        return all(len(values) == 1 for values in possible_values.values())


def _point_law(*fields: Field) -> FiniteLaw:
    return ((tuple(fields), Fraction(1)),)


_A_COMPLETE = (("bundle", "complete"), ("members", ("m1", "m2")))
_A_PARTIAL = (("bundle", "partial"), ("members", ("m1",)))
_E_IDENTITY = (
    ("order", ("m1", "m2")),
    (
        "regime_map",
        (("complete", "slot-complete"), ("partial", "slot-partial")),
    ),
    ("version", "exec-v1"),
)
_E_SWAPPED = (
    ("order", ("m1", "m2")),
    (
        "regime_map",
        (("complete", "slot-partial"), ("partial", "slot-complete")),
    ),
    ("version", "exec-v2"),
)
_SLOT_OUTCOMES = (
    (("slot-complete", Fraction(0)), ("slot-partial", Fraction(0))),
    (("slot-complete", Fraction(1)), ("slot-partial", Fraction(0))),
)


def _bundle_law(requested: PhysicalValue, execution: PhysicalValue) -> FiniteLaw:
    return tuple(
        (
            (
                ("A", requested),
                ("E", execution),
                ("Z", arm),
                ("outcome_slots", _SLOT_OUTCOMES[arm]),
            ),
            Fraction(1, 2),
        )
        for arm in (0, 1)
    )


_T_IDENTITY = (
    ("owner", "canonical"),
    ("value_map", (("high", Fraction(1)), ("low", Fraction(0)))),
)
_T_REVERSED = (
    ("owner", "reversed"),
    ("value_map", (("high", Fraction(0)), ("low", Fraction(1)))),
)
_S_A = (("key-a", Fraction(1)), ("key-b", Fraction(0)))
_S_B = (("key-a", Fraction(0)), ("key-b", Fraction(1)))
_G_IDENTITY = (
    ("protocol_id", "success-v1"),
    ("truth_map", (("fail", Fraction(0)), ("pass", Fraction(1)))),
)
_G_REVERSED = (
    ("protocol_id", "reversed-v2"),
    ("truth_map", (("fail", Fraction(1)), ("pass", Fraction(0)))),
)


def _measurement_law(component: str, physical: PhysicalValue) -> FiniteLaw:
    laws = {
        "T": (
            (("T", physical), ("Z", 0), ("terminal_token", "low")),
            (("T", physical), ("Z", 1), ("terminal_token", "high")),
        ),
        "S": (
            (
                ("S", physical),
                ("Z", 0),
                (
                    "key_scores",
                    (("key-a", Fraction(0)), ("key-b", Fraction(1))),
                ),
            ),
            (
                ("S", physical),
                ("Z", 1),
                (
                    "key_scores",
                    (("key-a", Fraction(1)), ("key-b", Fraction(0))),
                ),
            ),
        ),
        "G": (
            (("G", physical), ("Z", 0), ("protocol_token", "fail")),
            (("G", physical), ("Z", 1), ("protocol_token", "pass")),
        ),
    }
    return tuple((atom, Fraction(1, 2)) for atom in laws[component])


_POLICY_A = (
    ("action_menu", ("a", "b")),
    ("decision_rule", (("x0", "a"), ("x1", "a"))),
    ("information_snapshot", "x"),
    ("policy_id", "policy-a"),
    ("propensity", Fraction(1, 2)),
)
_POLICY_B = (
    ("action_menu", ("a", "b")),
    ("decision_rule", (("x0", "a"), ("x1", "b"))),
    ("information_snapshot", "x"),
    ("policy_id", "policy-b"),
    ("propensity", Fraction(1, 2)),
)


def _policy_law(policy: PhysicalValue) -> FiniteLaw:
    return (
        (
            (
                ("P", policy),
                ("action", "a"),
                ("context", "x0"),
                (
                    "potential_outcomes",
                    (("a", Fraction(1)), ("b", Fraction(0))),
                ),
            ),
            Fraction(1, 2),
        ),
        (
            (
                ("P", policy),
                ("action", "a"),
                ("context", "x1"),
                (
                    "potential_outcomes",
                    (("a", Fraction(0)), ("b", Fraction(1))),
                ),
            ),
            Fraction(1, 2),
        ),
    )


_PAIRED_WORLD_WITNESSES = (
    PairedWorldWitness(
        component="Z",
        estimand="tau_ITT",
        full_law_p=(
            ((("Y", Fraction(0)), ("Z", 0)), Fraction(1, 2)),
            ((("Y", Fraction(1)), ("Z", 1)), Fraction(1, 2)),
        ),
        full_law_q=(
            ((("Y", Fraction(0)), ("Z", 1)), Fraction(1, 2)),
            ((("Y", Fraction(1)), ("Z", 0)), Fraction(1, 2)),
        ),
        authenticated_manifest=(
            ("assignment_design", "balanced-half"),
            ("manifest_scope", "design-only"),
        ),
    ),
    PairedWorldWitness(
        component="A",
        estimand="tau_CB",
        full_law_p=_bundle_law(_A_COMPLETE, _E_IDENTITY),
        full_law_q=_bundle_law(_A_PARTIAL, _E_IDENTITY),
        authenticated_manifest=(("manifest_scope", "retained-records-only"),),
    ),
    PairedWorldWitness(
        component="E",
        estimand="tau_CB",
        full_law_p=_bundle_law(_A_COMPLETE, _E_IDENTITY),
        full_law_q=_bundle_law(_A_COMPLETE, _E_SWAPPED),
        authenticated_manifest=(("manifest_scope", "retained-records-only"),),
    ),
    PairedWorldWitness(
        component="B",
        estimand="tau_ITT",
        full_law_p=_point_law(
            ("B", (("assignment-0", "outcome-0"), ("assignment-1", "outcome-1"))),
            ("assignment_objects", (("assignment-0", 0), ("assignment-1", 1))),
            (
                "outcome_objects",
                (("outcome-0", Fraction(0)), ("outcome-1", Fraction(1))),
            ),
        ),
        full_law_q=_point_law(
            ("B", (("assignment-0", "outcome-1"), ("assignment-1", "outcome-0"))),
            ("assignment_objects", (("assignment-0", 0), ("assignment-1", 1))),
            (
                "outcome_objects",
                (("outcome-0", Fraction(0)), ("outcome-1", Fraction(1))),
            ),
        ),
        authenticated_manifest=(("manifest_scope", "unjoined-object-multisets"),),
    ),
    PairedWorldWitness(
        component="T",
        estimand="tau_ITT",
        full_law_p=_measurement_law("T", _T_IDENTITY),
        full_law_q=_measurement_law("T", _T_REVERSED),
        authenticated_manifest=(("manifest_scope", "scalar-without-owner-semantics"),),
    ),
    PairedWorldWitness(
        component="S",
        estimand="tau_ITT",
        full_law_p=_measurement_law("S", _S_A),
        full_law_q=_measurement_law("S", _S_B),
        authenticated_manifest=(("manifest_scope", "scalar-without-key-map"),),
    ),
    PairedWorldWitness(
        component="G",
        estimand="tau_ITT",
        full_law_p=_measurement_law("G", _G_IDENTITY),
        full_law_q=_measurement_law("G", _G_REVERSED),
        authenticated_manifest=(("manifest_scope", "scalar-without-protocol-map"),),
    ),
    PairedWorldWitness(
        component="P",
        estimand="Psi_N",
        full_law_p=_policy_law(_POLICY_A),
        full_law_q=_policy_law(_POLICY_B),
        authenticated_manifest=(
            ("manifest_scope", "actions-without-policy-provenance"),
        ),
    ),
)


def paired_world_witnesses() -> tuple[PairedWorldWitness, ...]:
    """Return the eight registered exact paired-world witnesses."""

    return _PAIRED_WORLD_WITNESSES


@dataclass(frozen=True)
class InvarianceCertificate:
    """Exact functional equality despite a changed physical field."""

    component: str
    physical_object_p: PhysicalObject
    physical_object_q: PhysicalObject

    def __post_init__(self) -> None:
        if self.component not in ("B", "S", "G"):
            raise ValueError("invariance component")
        _record(self.physical_object_p, "physical object p")
        _record(self.physical_object_q, "physical object q")
        if not self.preserves_estimand:
            raise ValueError("invalid invariance certificate")

    @property
    def functional_image_p(self) -> FunctionalImage:
        return _invariance_image(self.component, self.physical_object_p)

    @property
    def functional_image_q(self) -> FunctionalImage:
        return _invariance_image(self.component, self.physical_object_q)

    @property
    def estimand_p(self) -> Fraction:
        return _invariance_estimand(self.component, self.functional_image_p)

    @property
    def estimand_q(self) -> Fraction:
        return _invariance_estimand(self.component, self.functional_image_q)

    @property
    def preserves_estimand(self) -> bool:
        return (
            self.physical_object_p != self.physical_object_q
            and self.functional_image_p == self.functional_image_q
            and self.estimand_p == self.estimand_q
        )


def _invariance_image(
    component: str,
    physical_object: PhysicalObject,
) -> FunctionalImage:
    physical = _record(physical_object, "physical object")
    if component == "B":
        return tuple(
            (
                ("analysis_weight", _record(row, "B row")["analysis_weight"]),
                ("outcome", _record(row, "B row")["outcome"]),
                ("stratum", _record(row, "B row")["stratum"]),
            )
            for row in physical["rows"]
        )
    if component == "S":
        scores = dict(physical["scores"])
        return tuple(
            (("key", key), ("score", scores[key]), ("weight", weight))
            for key, weight in physical["weights"]
            if weight > 0
        )
    if component == "G":
        truth = dict(physical["truth_map"])
        return tuple(
            (("mass", mass), ("terminal", terminal), ("value", truth[terminal]))
            for terminal, mass in physical["evaluation_mass"]
        )
    raise ValueError("invariance component")


def _invariance_estimand(component: str, image: FunctionalImage) -> Fraction:
    if component == "B":
        return sum(
            _exact_fraction(_record(row, "B image")["analysis_weight"], "B weight")
            * _unit_interval_fraction(_record(row, "B image")["outcome"], "B outcome")
            for row in image
        )
    if component == "S":
        return sum(
            _unit_interval_fraction(_record(row, "S image")["weight"], "S weight")
            * _unit_interval_fraction(_record(row, "S image")["score"], "S score")
            for row in image
        )
    if component == "G":
        return sum(
            _unit_interval_fraction(_record(row, "G image")["mass"], "G mass")
            * _unit_interval_fraction(_record(row, "G image")["value"], "G value")
            for row in image
        )
    raise ValueError("invariance component")


_B_ROWS_P = (
    (
        ("analysis_weight", Fraction(1, 2)),
        ("outcome", Fraction(0)),
        ("stratum", "s0"),
        ("target_id", "target-0"),
        ("unit_id", "u0"),
    ),
    (
        ("analysis_weight", Fraction(1, 2)),
        ("outcome", Fraction(1)),
        ("stratum", "s0"),
        ("target_id", "target-1"),
        ("unit_id", "u1"),
    ),
)
_B_ROWS_Q = (
    (
        ("analysis_weight", Fraction(1, 2)),
        ("outcome", Fraction(0)),
        ("stratum", "s0"),
        ("target_id", "target-1"),
        ("unit_id", "u0"),
    ),
    (
        ("analysis_weight", Fraction(1, 2)),
        ("outcome", Fraction(1)),
        ("stratum", "s0"),
        ("target_id", "target-0"),
        ("unit_id", "u1"),
    ),
)


_INVARIANCE_CERTIFICATES = (
    InvarianceCertificate(
        component="B",
        physical_object_p=(("rows", _B_ROWS_P),),
        physical_object_q=(("rows", _B_ROWS_Q),),
    ),
    InvarianceCertificate(
        component="S",
        physical_object_p=(
            (
                "scores",
                (("key-a", Fraction(3, 4)), ("unused", Fraction(1, 4))),
            ),
            ("weights", (("key-a", Fraction(1)), ("unused", Fraction(0)))),
        ),
        physical_object_q=(
            ("scores", (("key-a", Fraction(3, 4)),)),
            ("weights", (("key-a", Fraction(1)),)),
        ),
    ),
    InvarianceCertificate(
        component="G",
        physical_object_p=(
            (
                "evaluation_mass",
                (("terminal-0", Fraction(3, 4)), ("terminal-1", Fraction(1, 4))),
            ),
            ("protocol_id", "protocol-v1"),
            (
                "truth_map",
                (("terminal-0", Fraction(0)), ("terminal-1", Fraction(1))),
            ),
        ),
        physical_object_q=(
            (
                "evaluation_mass",
                (("terminal-0", Fraction(3, 4)), ("terminal-1", Fraction(1, 4))),
            ),
            ("protocol_id", "protocol-v2-compatible"),
            (
                "truth_map",
                (("terminal-0", Fraction(0)), ("terminal-1", Fraction(1))),
            ),
        ),
    ),
)


def invariance_certificates() -> tuple[InvarianceCertificate, ...]:
    """Return exact counterexamples to field-change-only rejection."""

    return _INVARIANCE_CERTIFICATES


@dataclass(frozen=True)
class BoundRow:
    """One in-domain weighted row for the overlap-aware contrast bound."""

    arm: int
    analysis_weight: Fraction
    replacement: int
    omitted_mass: Fraction
    residual_tv: Fraction
    unit_deleted: bool = False
    denominator_changed: bool = False
    cross_arm_movement: bool = False
    score_lower: Fraction = Fraction(0)
    score_upper: Fraction = Fraction(1)

    def __post_init__(self) -> None:
        if type(self.arm) is not int or self.arm not in (0, 1):
            raise ValueError("arm")
        if type(self.replacement) is not int or self.replacement not in (0, 1):
            raise ValueError("replacement")
        analysis_weight = _unit_interval_fraction(
            self.analysis_weight,
            "analysis weight",
        )
        omitted_mass = _unit_interval_fraction(self.omitted_mass, "omitted mass")
        residual_tv = _unit_interval_fraction(self.residual_tv, "residual tv")
        score_lower = _unit_interval_fraction(self.score_lower, "score lower")
        score_upper = _unit_interval_fraction(self.score_upper, "score upper")
        object.__setattr__(self, "analysis_weight", analysis_weight)
        object.__setattr__(self, "omitted_mass", omitted_mass)
        object.__setattr__(self, "residual_tv", residual_tv)
        object.__setattr__(self, "score_lower", score_lower)
        object.__setattr__(self, "score_upper", score_upper)
        for flag, label in (
            (self.unit_deleted, "unit deletion"),
            (self.denominator_changed, "denominator change"),
            (self.cross_arm_movement, "cross-arm movement"),
        ):
            if type(flag) is not bool:
                raise ValueError(label)
            if flag:
                raise ValueError(f"{label} is outside the bound domain")
        if score_lower > score_upper:
            raise ValueError("score domain")

    @property
    def exact_term(self) -> Fraction:
        uncovered = min(Fraction(1), self.omitted_mass + self.residual_tv)
        return Fraction(self.replacement) + (1 - self.replacement) * uncovered


def _revalidated_rows(rows: Sequence[BoundRow]) -> tuple[BoundRow, ...]:
    try:
        supplied = tuple(rows)
    except TypeError as error:
        raise ValueError("bound rows") from error
    if not supplied or any(type(row) is not BoundRow for row in supplied):
        raise ValueError("bound rows")
    return tuple(
        BoundRow(
            arm=row.arm,
            analysis_weight=row.analysis_weight,
            replacement=row.replacement,
            omitted_mass=row.omitted_mass,
            residual_tv=row.residual_tv,
            unit_deleted=row.unit_deleted,
            denominator_changed=row.denominator_changed,
            cross_arm_movement=row.cross_arm_movement,
            score_lower=row.score_lower,
            score_upper=row.score_upper,
        )
        for row in supplied
    )


def contrast_error_bound_exact(rows: Sequence[BoundRow]) -> Fraction:
    """Return the exact two-arm overlap-aware error bound."""

    checked = _revalidated_rows(rows)
    arm_sums: dict[int, Fraction] = {}
    arm_bounds: dict[int, Fraction] = {}
    for row in checked:
        arm_sums[row.arm] = arm_sums.get(row.arm, Fraction(0)) + row.analysis_weight
        arm_bounds[row.arm] = arm_bounds.get(row.arm, Fraction(0)) + (
            row.analysis_weight * row.exact_term
        )
    if set(arm_sums) != {0, 1} or any(total != 1 for total in arm_sums.values()):
        raise ValueError("analysis weights must normalize exactly within each arm")
    return min(Fraction(2), arm_bounds[1] + arm_bounds[0])


def contrast_error_bound(rows: Sequence[BoundRow]) -> float:
    """Serialize the exact two-arm error bound as a float."""

    return float(contrast_error_bound_exact(rows))


def terminal_measured_contrast_exact(
    mu0: RationalInput,
    mu1: RationalInput,
    se0: RationalInput,
    sp0: RationalInput,
    se1: RationalInput,
    sp1: RationalInput,
) -> Fraction:
    """Return the exact arm-specific terminal-misclassification contrast."""

    mu_0 = _public_unit_interval_fraction(mu0, "mu0")
    mu_1 = _public_unit_interval_fraction(mu1, "mu1")
    sensitivity_0 = _public_unit_interval_fraction(se0, "se0")
    specificity_0 = _public_unit_interval_fraction(sp0, "sp0")
    sensitivity_1 = _public_unit_interval_fraction(se1, "se1")
    specificity_1 = _public_unit_interval_fraction(sp1, "sp1")
    kappa_0 = sensitivity_0 + specificity_0 - 1
    kappa_1 = sensitivity_1 + specificity_1 - 1
    return specificity_0 - specificity_1 + kappa_1 * mu_1 - kappa_0 * mu_0


def terminal_measured_contrast(
    mu0: RationalInput,
    mu1: RationalInput,
    se0: RationalInput,
    sp0: RationalInput,
    se1: RationalInput,
    sp1: RationalInput,
) -> float:
    """Serialize the exact arm-specific measured contrast as a float."""

    return float(terminal_measured_contrast_exact(mu0, mu1, se0, sp0, se1, sp1))


_SELECTION_STATUS = {
    "full_sample": "FULL_SAMPLE_RANDOMIZED_ESTIMAND",
    "mcar": "IDENTIFIED_WITHOUT_RECEIPT_CONDITIONING",
    "mar+positivity": "IDENTIFIED_BY_STANDARDIZATION_OR_IPW",
    "mnar": "BOUNDS_OR_SENSITIVITY_ONLY",
    "post-treatment_compliance": (
        "KEEP_RANDOMIZED_ESTIMAND_DO_NOT_CONDITION_ON_POST_TREATMENT_COMPLIANCE"
    ),
}


def selection_estimand_status(mechanism: str) -> str:
    """Return the registered identification boundary for receipt selection."""

    if type(mechanism) is not str or mechanism not in _SELECTION_STATUS:
        raise ValueError("selection mechanism")
    return _SELECTION_STATUS[mechanism]
