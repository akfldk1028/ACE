"""Immutable target-aware constraints for final competition portfolios."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


CAPACITY_BANDS = (
    "spatial_reserve",
    "balanced_yield",
    "brief_target",
    "maximum_feasible",
)
BASE_SCOPES = ("1/1", "1/2", "3/8", "1/4", "1/8", "1/16")


def _counts(**values: int) -> Mapping[str, int]:
    return MappingProxyType(dict(values))


@dataclass(frozen=True)
class CompetitionPortfolioContract:
    target_count: int
    capacity_band_exact_counts: Mapping[str, int]
    capacity_band_minimum_counts: Mapping[str, int]
    capacity_band_maximum_counts: Mapping[str, int]
    base_scopes: tuple[str, ...]
    base_scope_minimum_each: int
    base_scope_maximum_each: int | None
    visible_stepped_minimum: int
    visible_stepped_maximum: int | None
    upper_band_stepped_bands: tuple[str, ...]
    upper_band_stepped_minimum: int
    body_phenotype_minimum_distinct: int
    body_phenotype_maximum_each: int | None
    roof_archetype_minimum_distinct: int
    roof_archetype_maximum_each: int | None
    chassis_family_minimum_distinct: int
    chassis_family_maximum_each: int | None
    plan_family_minimum_distinct: int
    plan_family_maximum_each: int | None
    body_roof_signature_minimum_distinct: int
    body_roof_signature_maximum_each: int | None
    minimum_pair_distance: float
    shared_language_minimum_composite_distance: float


def competition_portfolio_contract(
    target_count: int,
) -> CompetitionPortfolioContract:
    """Return the fail-closed final-set contract for a requested target."""

    target = int(target_count)
    if target <= 0:
        raise ValueError("target_count must be positive")
    empty = MappingProxyType({})
    if target == 3:
        return CompetitionPortfolioContract(
            target_count=3,
            capacity_band_exact_counts=empty,
            capacity_band_minimum_counts=empty,
            capacity_band_maximum_counts=empty,
            base_scopes=(),
            base_scope_minimum_each=0,
            base_scope_maximum_each=None,
            visible_stepped_minimum=0,
            visible_stepped_maximum=1,
            upper_band_stepped_bands=(),
            upper_band_stepped_minimum=0,
            body_phenotype_minimum_distinct=3,
            body_phenotype_maximum_each=1,
            roof_archetype_minimum_distinct=0,
            roof_archetype_maximum_each=None,
            chassis_family_minimum_distinct=0,
            chassis_family_maximum_each=None,
            plan_family_minimum_distinct=0,
            plan_family_maximum_each=None,
            body_roof_signature_minimum_distinct=3,
            body_roof_signature_maximum_each=1,
            minimum_pair_distance=0.16,
            shared_language_minimum_composite_distance=0.0,
        )
    if target == 20:
        exact_bands = _counts(
            spatial_reserve=5,
            balanced_yield=5,
            brief_target=5,
            maximum_feasible=5,
        )
        return CompetitionPortfolioContract(
            target_count=20,
            capacity_band_exact_counts=exact_bands,
            capacity_band_minimum_counts=empty,
            capacity_band_maximum_counts=empty,
            base_scopes=BASE_SCOPES,
            base_scope_minimum_each=3,
            base_scope_maximum_each=4,
            visible_stepped_minimum=1,
            visible_stepped_maximum=3,
            upper_band_stepped_bands=(),
            upper_band_stepped_minimum=0,
            body_phenotype_minimum_distinct=5,
            body_phenotype_maximum_each=4,
            roof_archetype_minimum_distinct=7,
            roof_archetype_maximum_each=3,
            chassis_family_minimum_distinct=6,
            chassis_family_maximum_each=4,
            plan_family_minimum_distinct=5,
            plan_family_maximum_each=4,
            body_roof_signature_minimum_distinct=0,
            body_roof_signature_maximum_each=None,
            minimum_pair_distance=0.14,
            shared_language_minimum_composite_distance=0.22,
        )
    if target == 10:
        return CompetitionPortfolioContract(
            target_count=10,
            capacity_band_exact_counts=empty,
            capacity_band_minimum_counts=_counts(
                spatial_reserve=2,
                balanced_yield=2,
                brief_target=2,
                maximum_feasible=2,
            ),
            capacity_band_maximum_counts=_counts(
                spatial_reserve=3,
                balanced_yield=3,
                brief_target=3,
                maximum_feasible=3,
            ),
            base_scopes=BASE_SCOPES,
            base_scope_minimum_each=1,
            base_scope_maximum_each=None,
            visible_stepped_minimum=1,
            visible_stepped_maximum=3,
            upper_band_stepped_bands=(
                "brief_target",
                "maximum_feasible",
            ),
            upper_band_stepped_minimum=1,
            body_phenotype_minimum_distinct=0,
            body_phenotype_maximum_each=3,
            roof_archetype_minimum_distinct=0,
            roof_archetype_maximum_each=3,
            chassis_family_minimum_distinct=0,
            chassis_family_maximum_each=None,
            plan_family_minimum_distinct=0,
            plan_family_maximum_each=None,
            body_roof_signature_minimum_distinct=0,
            body_roof_signature_maximum_each=None,
            minimum_pair_distance=0.10,
            shared_language_minimum_composite_distance=0.0,
        )
    return CompetitionPortfolioContract(
        target_count=target,
        capacity_band_exact_counts=empty,
        capacity_band_minimum_counts=empty,
        capacity_band_maximum_counts=empty,
        base_scopes=(),
        base_scope_minimum_each=0,
        base_scope_maximum_each=None,
        visible_stepped_minimum=0,
        visible_stepped_maximum=None,
        upper_band_stepped_bands=(),
        upper_band_stepped_minimum=0,
        body_phenotype_minimum_distinct=0,
        body_phenotype_maximum_each=None,
        roof_archetype_minimum_distinct=0,
        roof_archetype_maximum_each=None,
        chassis_family_minimum_distinct=0,
        chassis_family_maximum_each=None,
        plan_family_minimum_distinct=0,
        plan_family_maximum_each=None,
        body_roof_signature_minimum_distinct=0,
        body_roof_signature_maximum_each=None,
        minimum_pair_distance=0.10,
        shared_language_minimum_composite_distance=0.0,
    )


__all__ = [
    "CompetitionPortfolioContract",
    "competition_portfolio_contract",
]
