"""Immutable boundaries shared by creative family recipes and orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .geometry_language.ast import GeometryProgram


@dataclass(frozen=True)
class CreativeRecipeContext:
    variation_index: int
    book_scope_label: str
    capacity_band: str


@dataclass(frozen=True)
class CreativeRecipeResult:
    program: GeometryProgram
    contact_type: str
    contact_node_id: str
    form_class: str
    recipe_parameters: dict[str, Any]


@dataclass(frozen=True)
class CreativeFamilySpec:
    family_id: str
    recipe_id: str
    form_class: str
    contact_type: str


__all__ = [
    "CreativeFamilySpec",
    "CreativeRecipeContext",
    "CreativeRecipeResult",
]
