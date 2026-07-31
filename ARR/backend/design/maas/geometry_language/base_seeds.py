"""Normalized architectural base seeds, separate from parcel scope fractions.

A p.3 scope answers *how much of the site is available*. A base seed answers
*what normalized starting proportion enters the recursive solid program*.
Most seeds deliberately expand from the exact same unit Box; they are semantic
priors for agents, not completed-building templates or extra kernel types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .affine_matrix import matrix4_to_lists, scale_matrix4
from .ast import GeometryNode, GeometryProgram


@dataclass(frozen=True)
class BaseSeedSpec:
    seed_id: str
    label: str
    primitive_operator: str
    normalized_scale: tuple[float, float, float]
    architectural_use: str
    core_expansion: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed_id": self.seed_id,
            "label": self.label,
            "primitive_operator": self.primitive_operator,
            "normalized_scale": list(self.normalized_scale),
            "architectural_use": self.architectural_use,
            "core_expansion": self.core_expansion,
        }


BASE_SEED_SPECS: tuple[BaseSeedSpec, ...] = (
    BaseSeedSpec("block", "BLOCK", "box", (1.0, 1.0, 1.0), "neutral compact host", "Scale(UnitBox, [1, 1, 1])"),
    BaseSeedSpec("slab", "SLAB", "box", (2.2, 1.45, 0.28), "wide low plate or hall datum", "Scale(UnitBox, [2.2, 1.45, 0.28])"),
    BaseSeedSpec("bar", "BAR", "box", (2.8, 0.62, 0.48), "linear wing or bent ribbon seed", "Scale(UnitBox, [2.8, 0.62, 0.48])"),
    BaseSeedSpec("tower", "TOWER", "box", (0.68, 0.68, 2.5), "vertical tapered or leaning seed", "Scale(UnitBox, [0.68, 0.68, 2.5])"),
    BaseSeedSpec("profiled_prism", "PROFILED PRISM", "extruded_polygon", (1.6, 1.2, 0.75), "non-rectangular footprint seed", "Extrude(PolygonProfile, height)"),
)


# One kernel primitive can carry several plan languages.  These are normalized
# profiles, not completed building templates: synthesis chooses a profile and
# every later BOOK/site/program operation still receives the same SolidNode.
# Keeping this alphabet here prevents triangular/chamfered plans from being
# scattered as one-off coordinate recipes across candidate generators.
PROFILED_PRISM_FAMILIES: tuple[tuple[str, tuple[tuple[float, float], ...]], ...] = (
    (
        "faceted",
        ((0.0, 0.0), (1.6, 0.0), (1.35, 1.15), (0.35, 1.2), (-0.15, 0.55)),
    ),
    (
        "triangular",
        ((0.0, 0.0), (1.6, 0.0), (0.72, 1.2)),
    ),
    (
        "trapezoidal",
        ((0.0, 0.0), (1.6, 0.0), (1.28, 1.2), (0.24, 1.2)),
    ),
    (
        "chamfered",
        ((0.0, 0.0), (1.28, 0.0), (1.6, 0.32), (1.6, 1.2), (0.0, 1.2)),
    ),
    (
        "kite",
        ((0.0, 0.46), (0.62, 0.0), (1.6, 0.5), (0.68, 1.2)),
    ),
)


def profiled_prism_parameters(variation_index: int = 0) -> dict[str, Any]:
    """Return one deterministic normalized polygon-profile parameter set."""

    index = max(0, int(variation_index)) % len(PROFILED_PRISM_FAMILIES)
    family, points = PROFILED_PRISM_FAMILIES[index]
    return {
        "points": [list(point) for point in points],
        "height": 0.75,
        "profile_family": family,
        "profile_variant_index": index,
    }


def base_seed_catalog() -> tuple[dict[str, Any], ...]:
    return tuple(spec.to_dict() for spec in BASE_SEED_SPECS)


def base_seed_program(seed_id: str, *, variation_index: int = 0) -> GeometryProgram:
    spec = next((item for item in BASE_SEED_SPECS if item.seed_id == seed_id), None)
    if spec is None:
        raise KeyError(f"unknown base seed: {seed_id}")
    provenance = {
        "source": "normalized_base_seed_catalog",
        "seed_id": spec.seed_id,
        "architectural_use": spec.architectural_use,
        "not_a_building_template": True,
    }
    if spec.primitive_operator == "box":
        unit = GeometryNode(
            "unit_box", "primitive", "box",
            parameters={"width": 1.0, "depth": 1.0, "height": 1.0},
            semantic_role="base_seed", provenance=provenance,
        )
        scaled = GeometryNode(
            f"seed_{spec.seed_id}", "transform", "matrix4", inputs=(unit.id,),
            parameters={
                "matrix4": matrix4_to_lists(
                    scale_matrix4(spec.normalized_scale),
                ),
            },
            semantic_role="base_seed",
            provenance={**provenance, "core_expansion": spec.core_expansion},
        )
        nodes = (unit, scaled)
        root = scaled.id
    else:
        prism_parameters = profiled_prism_parameters(variation_index)
        prism = GeometryNode(
            f"seed_{spec.seed_id}", "primitive", "extruded_polygon",
            parameters=prism_parameters,
            semantic_role="base_seed",
            provenance={**provenance, "core_expansion": spec.core_expansion},
        )
        nodes = (prism,)
        root = prism.id
    return GeometryProgram(
        nodes, root, name=f"base_seed_{spec.seed_id}",
        metadata={
            "language_layer": "architectural_base_seed",
            "base_seed": spec.to_dict(),
            "plan_profile_family": (
                prism_parameters["profile_family"]
                if spec.primitive_operator == "extruded_polygon"
                else "rectangular"
            ),
            "site_scope_is_separate": True,
            "canonical_root": "1/1 UnitBox",
            "basevolume_affine_authority": (
                "explicit_matrix4"
                if spec.primitive_operator == "box"
                else "derived_topology"
            ),
        },
    )


def base_seed_programs() -> tuple[GeometryProgram, ...]:
    return tuple(base_seed_program(spec.seed_id) for spec in BASE_SEED_SPECS)


def box_derived_base_seed_programs() -> tuple[GeometryProgram, ...]:
    """Return the four seeds that provably share one identical UnitBox core."""
    return tuple(base_seed_program(spec.seed_id) for spec in BASE_SEED_SPECS if spec.primitive_operator == "box")


__all__ = [
    "BASE_SEED_SPECS", "PROFILED_PRISM_FAMILIES", "BaseSeedSpec", "base_seed_catalog",
    "base_seed_program", "base_seed_programs", "box_derived_base_seed_programs",
    "profiled_prism_parameters",
]
