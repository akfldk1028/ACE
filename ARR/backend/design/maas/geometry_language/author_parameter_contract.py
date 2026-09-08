"""One shared value contract for authored geometry operator parameters."""

from __future__ import annotations

from typing import Any

from .mutation import NUMERIC_BOUNDS, STRING_PARAMETER_VALUES, VECTOR_LENGTHS


_STRUCTURED_PARAMETERS = frozenset({
    "exterior",
    "holes",
    "matrices",
    "matrix4",
    "path",
    "points",
    "profiles",
    "section_controls",
    "top_surface",
    "bottom_surface",
})


def author_parameter_value_contract(
    operator: str,
    parameter: str,
) -> dict[str, Any]:
    if parameter == "matrix4":
        return {"type": "matrix4"}
    allowed = STRING_PARAMETER_VALUES.get((operator, parameter))
    if allowed is not None:
        return {"type": "string", "enum": sorted(allowed)}
    if parameter == "axis":
        return {"type": "string", "enum": ["x", "y", "z"]}
    if parameter in VECTOR_LENGTHS:
        return {
            "type": "numeric_vector",
            "lengths": list(VECTOR_LENGTHS[parameter]),
        }
    if parameter in NUMERIC_BOUNDS:
        lower, upper = NUMERIC_BOUNDS[parameter]
        return {"type": "number", "minimum": lower, "maximum": upper}
    if parameter in {"x", "y", "z"}:
        return {"type": "number", "minimum": -4.0, "maximum": 4.0}
    if parameter in {"center", "bridge", "ground_spine", "require_connected"}:
        return {"type": "boolean"}
    if parameter in _STRUCTURED_PARAMETERS:
        return {"type": "structured_literal"}
    return {"type": "literal"}


__all__ = ["author_parameter_value_contract"]
