"""Shared editable MassDSL parameter contract for every authoring agent."""

from __future__ import annotations


PARAMETER_BOUNDS: dict[str, tuple[float, float]] = {
    "factor": (0.18, 0.90),
    "ratio": (0.12, 0.90),
    "upper_ratio": (0.18, 0.95),
    "top_ratio": (0.18, 0.95),
    "width_ratio": (0.05, 0.90),
    "lane_width_ratio": (0.045, 0.16),
    "arm_ratio": (0.10, 0.90),
    "branch_ratio": (0.10, 0.90),
    "width_gradient": (-0.30, 0.30),
    "width_start_ratio": (0.45, 1.35),
    "width_mid_ratio": (0.65, 1.55),
    "width_end_ratio": (0.45, 1.35),
    "width_wave": (-0.28, 0.28),
    "branch_point_ratio": (0.22, 0.58),
    "height_start_ratio": (0.40, 1.00),
    "height_mid_ratio": (0.50, 1.00),
    "height_end_ratio": (0.40, 1.00),
    "height_wave": (-0.24, 0.24),
    "depth_ratio": (0.10, 0.90),
    "slab_ratio": (0.12, 0.70),
    "distance_ratio": (-0.34, 0.34),
    "shift_ratio": (-0.34, 0.34),
    "curvature": (-0.18, 0.18),
    "vertical_overlap": (0.0, 0.34),
    "lower_floor_fraction": (0.12, 0.88),
    "gap_ratio": (0.04, 0.48),
    "angle": (-55.0, 55.0),
    "n": (2.0, 4.0),
    "lane_count": (2.0, 3.0),
    "field_samples": (5.0, 9.0),
}


def bounded_parameter(name: str, value: float) -> float:
    low, high = PARAMETER_BOUNDS[name]
    bounded = max(low, min(high, float(value)))
    if name in {"n", "lane_count", "field_samples"}:
        return int(round(bounded))
    return round(bounded, 4)


__all__ = ["PARAMETER_BOUNDS", "bounded_parameter"]
