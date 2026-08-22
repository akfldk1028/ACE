"""Frozen primary-study constants for the ICLR 2027 development pipeline."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StudyContract:
    epsilon: float
    alpha: float
    patience: int
    group_seed: int
    site_partition_counts: tuple[int, int, int]
    epsilon_sensitivity: tuple[float, ...]
    alpha_sensitivity: tuple[float, ...]

    @classmethod
    def primary(cls) -> "StudyContract":
        return cls(0.02, 0.10, 2, 20260819, (2, 1, 2), (0.01, 0.05), (0.05, 0.20))
