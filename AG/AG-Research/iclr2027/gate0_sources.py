"""Minimal, no-I/O trust roots for the current-state Gate 0 audit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class Gate0TopSourceSpec:
    logical_name: str
    relative_path: str
    sha256: str
    declared_members: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.logical_name) is not str or not self.logical_name:
            raise TypeError("logical_name must be a nonempty native string")
        if type(self.relative_path) is not str or not self.relative_path:
            raise TypeError("relative_path must be a nonempty native string")
        if type(self.sha256) is not str or _SHA256.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be a lowercase SHA-256")
        if type(self.declared_members) is not tuple or any(
            type(member) is not str or not member for member in self.declared_members
        ):
            raise TypeError("declared_members must be a tuple of nonempty strings")
        if len(self.declared_members) != len(set(self.declared_members)):
            raise ValueError("declared_members must be unique")


GATE0_TOP_SOURCES: tuple[Gate0TopSourceSpec, ...] = (
    Gate0TopSourceSpec(
        "snapshot_receipt",
        "results/exp09_cats/development_snapshot/snapshot_receipt.json",
        "63556ffe60f0cfbbc7f5bea4f2d75e4bbafa67566a3bd9a8f61d22ad298b5a4d",
        (
            "pilot_gate.json",
            "run_manifest.json",
            "run_plan.json",
            "run_transactions/<64-lowercase-sha256>.json",
        ),
    ),
    Gate0TopSourceSpec(
        "pilot_gate",
        "results/exp08_architecture/pilot_full_v12_clean_recovery/pilot_gate.json",
        "d534eeb379e4fbe8793ff986fa2e583eca7b6783d561f968a606be0139b945a6",
        (),
    ),
    Gate0TopSourceSpec(
        "dataset_manifest",
        "results/exp09_cats/dataset/feature_manifest.json",
        "7afe02f50c7b179c659b19042413d45d6940fa68444831359177e422262136a1",
        (
            "private/group_assignments.json",
            "private/private_labels.jsonl",
            "runtime/runtime_features.jsonl",
        ),
    ),
    Gate0TopSourceSpec(
        "development_gate",
        "results/exp09_cats/replay/development/development_gate.json",
        "e4f64639991b617955b4e2f2821a46205e0d7dd5f9b79aef4fd883b729c565b5",
        (),
    ),
)


@dataclass(frozen=True, slots=True)
class Gate0RawSourcePaths:
    snapshot_receipt: str
    pilot_gate: str
    dataset_manifest: str
    development_gate: str


@dataclass(frozen=True, slots=True)
class _Gate0ValidatedSourcePaths:
    snapshot_receipt: Path
    pilot_gate: Path
    dataset_manifest: Path
    development_gate: Path


def _checked_specs() -> tuple[Gate0TopSourceSpec, ...]:
    specs = GATE0_TOP_SOURCES
    if type(specs) is not tuple or len(specs) != 4:
        raise ValueError("Gate 0 top source contract must contain exactly four specs")
    expected = ("snapshot_receipt", "pilot_gate", "dataset_manifest", "development_gate")
    if tuple(spec.logical_name for spec in specs) != expected:
        raise ValueError("Gate 0 top source order is invalid")
    if any(type(spec) is not Gate0TopSourceSpec for spec in specs):
        raise TypeError("Gate 0 top sources must be exact specs")
    return specs


def validate_gate0_raw_source_paths(raw: Gate0RawSourcePaths) -> _Gate0ValidatedSourcePaths:
    """Reject every noncanonical raw spelling before constructing any Path."""

    if type(raw) is not Gate0RawSourcePaths:
        raise TypeError("sources must be an exact Gate0RawSourcePaths")
    values = (
        raw.snapshot_receipt,
        raw.pilot_gate,
        raw.dataset_manifest,
        raw.development_gate,
    )
    specs = _checked_specs()
    for value, spec in zip(values, specs, strict=True):
        if type(value) is not str:
            raise TypeError(f"{spec.logical_name} must be a native string")
        if value != spec.relative_path:
            raise ValueError(f"{spec.logical_name} must use the exact canonical raw path")
    return _Gate0ValidatedSourcePaths(*(Path(value) for value in values))


__all__ = (
    "GATE0_TOP_SOURCES",
    "Gate0RawSourcePaths",
    "Gate0TopSourceSpec",
    "validate_gate0_raw_source_paths",
)
