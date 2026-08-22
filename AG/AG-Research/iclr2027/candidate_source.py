"""Deterministic, dependency-injected collection of site candidates."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping


SCHEMA_VERSION = "ace.iclr2027.candidate_source.v1"
MAX_PROBES = 10_000
_PNU = re.compile(r"^[0-9]{19}$")
_DISTRICT_CODE = re.compile(r"^[0-9]{5}$")


@dataclass(frozen=True)
class BoundingBox:
    """An explicit WGS84 rectangle used to map Halton unit coordinates."""

    west: float
    south: float
    east: float
    north: float

    def __post_init__(self) -> None:
        values = (self.west, self.south, self.east, self.north)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("bbox coordinates must be finite")
        if not (-180.0 <= self.west < self.east <= 180.0):
            raise ValueError("bbox west/east must form a valid longitude interval")
        if not (-90.0 <= self.south < self.north <= 90.0):
            raise ValueError("bbox south/north must form a valid latitude interval")

    def to_dict(self) -> dict[str, float | str]:
        return {
            "west": self.west,
            "south": self.south,
            "east": self.east,
            "north": self.north,
            "crs": "EPSG:4326",
        }


@dataclass(frozen=True)
class CoordinateProbe:
    """One deterministic point in a Halton probe sequence."""

    index: int
    longitude: float
    latitude: float


@dataclass(frozen=True)
class CandidateObservation:
    """Selection-compatible facts observed for one parcel."""

    pnu: str
    district_code: str
    parcel_area_m2: float
    boundary_available: bool
    law_available: bool
    parking_available: bool

    def __post_init__(self) -> None:
        if not _PNU.fullmatch(self.pnu):
            raise ValueError("candidate PNU must contain exactly 19 digits")
        if not _DISTRICT_CODE.fullmatch(self.district_code):
            raise ValueError("candidate district_code must contain exactly five digits")
        if not math.isfinite(self.parcel_area_m2) or self.parcel_area_m2 <= 0:
            raise ValueError("candidate parcel_area_m2 must be positive and finite")
        availability = (
            self.boundary_available,
            self.law_available,
            self.parking_available,
        )
        if not all(type(value) is bool for value in availability):
            raise TypeError("candidate availability fields must be booleans")

    def to_candidate_dict(self) -> dict[str, Any]:
        """Return exactly the fields consumed by ``select_iclr2027_sites.py``."""

        return {
            "pnu": self.pnu,
            "district_code": self.district_code,
            "parcel_area_m2": self.parcel_area_m2,
            "boundary_available": self.boundary_available,
            "law_available": self.law_available,
            "parking_available": self.parking_available,
        }


class ExclusionCode(str, Enum):
    """Non-sensitive reasons why a coordinate did not yield a candidate."""

    NO_PARCEL = "no_parcel"
    INVALID_PNU = "invalid_pnu"
    OUTSIDE_SEOUL = "outside_seoul"
    PARCEL_AREA_UNAVAILABLE = "parcel_area_unavailable"
    DUPLICATE_PNU = "duplicate_pnu"
    INSPECTION_ERROR = "inspection_error"
    INVALID_OBSERVATION = "invalid_observation"


@dataclass(frozen=True)
class ProbeExclusion:
    code: ExclusionCode
    pnu: str | None = None

    def __post_init__(self) -> None:
        if self.pnu is not None and not _PNU.fullmatch(self.pnu):
            raise ValueError("exclusion PNU must contain exactly 19 digits")


ProbeInspection = CandidateObservation | ProbeExclusion
ProbeInspector = Callable[[CoordinateProbe], ProbeInspection]


def _radical_inverse(index: int, base: int) -> float:
    value = 0.0
    denominator = 1.0
    while index:
        index, remainder = divmod(index, base)
        denominator *= base
        value += remainder / denominator
    return value


def _validate_sampling(seed: int, max_probes: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if type(max_probes) is not int or not 1 <= max_probes <= MAX_PROBES:
        raise ValueError(f"max_probes must be between 1 and {MAX_PROBES}")


def halton_probes(
    *,
    bbox: BoundingBox,
    seed: int,
    max_probes: int,
) -> tuple[CoordinateProbe, ...]:
    """Return a bounded Halton(2,3) sequence offset by ``seed``."""

    _validate_sampling(seed, max_probes)
    longitude_span = bbox.east - bbox.west
    latitude_span = bbox.north - bbox.south
    probes = []
    for index in range(seed + 1, seed + max_probes + 1):
        probes.append(
            CoordinateProbe(
                index=index,
                longitude=bbox.west + longitude_span * _radical_inverse(index, 2),
                latitude=bbox.south + latitude_span * _radical_inverse(index, 3),
            )
        )
    return tuple(probes)


def _exclusion_record(probe: CoordinateProbe, exclusion: ProbeExclusion) -> dict[str, Any]:
    record: dict[str, Any] = {
        "probe_index": probe.index,
        "code": exclusion.code.value,
    }
    if exclusion.pnu is not None:
        record["pnu"] = exclusion.pnu
    return record


def collect_candidate_source(
    *,
    bbox: BoundingBox,
    seed: int,
    max_probes: int,
    inspect_probe: ProbeInspector,
    collector: str,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Inspect deterministic probes without coupling the core to ARR or network I/O."""

    if not collector.strip():
        raise ValueError("collector must be nonempty")
    probes = halton_probes(bbox=bbox, seed=seed, max_probes=max_probes)
    candidates: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    seen_pnus: set[str] = set()

    for probe in probes:
        try:
            observation = inspect_probe(probe)
        except Exception:
            observation = ProbeExclusion(ExclusionCode.INSPECTION_ERROR)

        if isinstance(observation, CandidateObservation):
            if observation.pnu in seen_pnus:
                exclusions.append(
                    _exclusion_record(
                        probe,
                        ProbeExclusion(ExclusionCode.DUPLICATE_PNU, observation.pnu),
                    )
                )
                continue
            seen_pnus.add(observation.pnu)
            candidates.append(observation.to_candidate_dict())
            continue

        if not isinstance(observation, ProbeExclusion):
            observation = ProbeExclusion(ExclusionCode.INVALID_OBSERVATION)
        exclusions.append(_exclusion_record(probe, observation))

    exclusion_counts = Counter(record["code"] for record in exclusions)
    extra_provenance = dict(provenance or {})
    reserved = {
        "collector",
        "probe_strategy",
        "halton_bases",
        "seed",
        "max_probes",
        "bbox",
        "probes_attempted",
        "unique_candidate_count",
        "exclusion_counts",
    }
    overlap = reserved.intersection(extra_provenance)
    if overlap:
        raise ValueError(f"provenance cannot override reserved fields: {sorted(overlap)}")
    return {
        "schema_version": SCHEMA_VERSION,
        "candidates": candidates,
        "exclusions": exclusions,
        "provenance": {
            **extra_provenance,
            "collector": collector,
            "probe_strategy": "seeded_halton",
            "halton_bases": [2, 3],
            "seed": seed,
            "max_probes": max_probes,
            "bbox": bbox.to_dict(),
            "probes_attempted": len(probes),
            "unique_candidate_count": len(candidates),
            "exclusion_counts": dict(sorted(exclusion_counts.items())),
        },
    }


__all__ = [
    "BoundingBox",
    "CandidateObservation",
    "CoordinateProbe",
    "ExclusionCode",
    "MAX_PROBES",
    "ProbeExclusion",
    "collect_candidate_source",
    "halton_probes",
]
