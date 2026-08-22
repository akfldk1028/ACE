"""Deterministic, leakage-aware site selection for the architecture test split."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .io import sha256_json


_PNU = re.compile(r"^[0-9]{19}$")


@dataclass(frozen=True)
class SiteCandidate:
    pnu: str
    district_code: str
    parcel_area_m2: float
    boundary_available: bool
    law_available: bool
    parking_available: bool

    def __post_init__(self) -> None:
        if not _PNU.fullmatch(self.pnu):
            raise ValueError("site candidate PNU must contain exactly 19 digits")
        if not self.district_code.strip():
            raise ValueError("district_code must be nonempty")
        if self.parcel_area_m2 <= 0:
            raise ValueError("parcel_area_m2 must be positive")

    @property
    def area_bin(self) -> str:
        if self.parcel_area_m2 < 300.0:
            return "small"
        if self.parcel_area_m2 < 1000.0:
            return "medium"
        return "large"


@dataclass(frozen=True)
class SiteSelectionResult:
    selected: tuple[SiteCandidate, ...]
    excluded: dict[str, str]
    seed: int
    max_parcel_area_m2: float


DEV_SITES = (
    {
        "pnu": "1168011800104170004",
        "district_code": "11680",
        "parcel_area_m2": 264.126,
    },
    {
        "pnu": "1168011800104670003",
        "district_code": "11680",
        "parcel_area_m2": 437.85,
    },
)


def candidate_from_dict(payload: Mapping[str, Any]) -> SiteCandidate:
    """Parse a service-exported site candidate."""

    return SiteCandidate(
        pnu=str(payload.get("pnu") or ""),
        district_code=str(payload.get("district_code") or ""),
        parcel_area_m2=float(payload.get("parcel_area_m2") or 0.0),
        boundary_available=payload.get("boundary_available") is True,
        law_available=payload.get("law_available") is True,
        parking_available=payload.get("parking_available") is True,
    )


def registry_from_selection(
    result: SiteSelectionResult,
    *,
    inventory_commit: str,
    candidate_source_sha256: str,
    prior_pnus: set[str],
    repository_inventory_scanned: bool = True,
    inventory_exclude_paths: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Serialize development sites and an unfrozen selected test split."""

    test_sites = [
        {
            "pnu": site.pnu,
            "split": "test",
            "district_code": site.district_code,
            "parcel_area_m2": site.parcel_area_m2,
            "area_bin": site.area_bin,
            "artifacts": {},
        }
        for site in result.selected
    ]
    dev_sites = [
        {
            **site,
            "split": "dev",
            "area_bin": SiteCandidate(
                pnu=str(site["pnu"]),
                district_code=str(site["district_code"]),
                parcel_area_m2=float(site["parcel_area_m2"]),
                boundary_available=True,
                law_available=True,
                parking_available=True,
            ).area_bin,
            "artifacts": {},
        }
        for site in DEV_SITES
    ]
    selection_identity = {
        "seed": result.seed,
        "max_parcel_area_m2": result.max_parcel_area_m2,
        "inventory_commit": inventory_commit,
        "candidate_source_sha256": candidate_source_sha256,
        "prior_pnus_sha256": sha256_json(sorted(prior_pnus)),
        "inventory_exclude_paths": list(inventory_exclude_paths),
        "selected_pnus": [site.pnu for site in result.selected],
    }
    return {
        "schema_version": "ace.iclr2027.site_registry.v1",
        "version": f"selection-{result.seed}-{sha256_json(selection_identity)[:12]}",
        "frozen": False,
        "split_manifest_sha256": "",
        "selection": {
            **selection_identity,
            "repository_inventory_scanned": repository_inventory_scanned,
            "excluded": dict(sorted(result.excluded.items())),
        },
        "sites": [*dev_sites, *test_sites],
    }


def _eligibility_failure(
    candidate: SiteCandidate,
    prior_pnus: set[str],
    *,
    max_parcel_area_m2: float,
) -> str | None:
    if candidate.pnu in prior_pnus:
        return "seen_in_repository"
    if not candidate.boundary_available:
        return "boundary_unavailable"
    if not candidate.law_available:
        return "law_unavailable"
    if not candidate.parking_available:
        return "parking_unavailable"
    if candidate.parcel_area_m2 > max_parcel_area_m2:
        return "parcel_area_out_of_scope"
    return None


def _rank(candidate: SiteCandidate, seed: int) -> str:
    return hashlib.sha256(f"{seed}:{candidate.pnu}".encode("utf-8")).hexdigest()


def select_test_sites(
    candidates: Iterable[SiteCandidate],
    *,
    prior_pnus: set[str],
    seed: int = 20260818,
    count: int = 5,
    max_parcel_area_m2: float = 30_000.0,
) -> SiteSelectionResult:
    """Select sites reproducibly across area bins and districts."""

    if count < 3:
        raise ValueError("count must be at least three to cover all area bins")
    if max_parcel_area_m2 <= 0:
        raise ValueError("max_parcel_area_m2 must be positive")

    excluded: dict[str, str] = {}
    eligible_by_pnu: dict[str, SiteCandidate] = {}
    for candidate in candidates:
        failure = _eligibility_failure(
            candidate,
            prior_pnus,
            max_parcel_area_m2=max_parcel_area_m2,
        )
        if failure:
            excluded[candidate.pnu] = failure
            continue
        eligible_by_pnu.setdefault(candidate.pnu, candidate)
    eligible = list(eligible_by_pnu.values())
    if len(eligible) < count:
        raise ValueError(f"only {len(eligible)} eligible sites for requested count={count}")

    selected: list[SiteCandidate] = []
    selected_pnus: set[str] = set()
    selected_districts: set[str] = set()
    for area_bin in ("small", "medium", "large"):
        group = [item for item in eligible if item.area_bin == area_bin]
        if not group:
            raise ValueError(f"no eligible site in area bin: {area_bin}")
        chosen = min(
            group,
            key=lambda item: (item.district_code in selected_districts, _rank(item, seed)),
        )
        selected.append(chosen)
        selected_pnus.add(chosen.pnu)
        selected_districts.add(chosen.district_code)

    remaining = [item for item in eligible if item.pnu not in selected_pnus]
    while len(selected) < count:
        if not remaining:
            raise ValueError("eligible site pool exhausted")
        chosen = min(
            remaining,
            key=lambda item: (item.district_code in selected_districts, _rank(item, seed)),
        )
        selected.append(chosen)
        selected_pnus.add(chosen.pnu)
        selected_districts.add(chosen.district_code)
        remaining = [item for item in remaining if item.pnu != chosen.pnu]

    if len(selected_districts) < 3:
        raise ValueError("selected sites cover fewer than three districts")

    for candidate in eligible:
        if candidate.pnu not in selected_pnus:
            excluded[candidate.pnu] = "not_selected_by_stratified_sample"
    return SiteSelectionResult(
        tuple(selected),
        excluded,
        seed,
        float(max_parcel_area_m2),
    )
