"""Bounded shared pair analysis for one evolving MASS selection pool."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Iterable
import weakref


DistanceEvaluator = Callable[[Any, Any], float]


@dataclass(frozen=True)
class _PairMeasurement:
    left_ref: weakref.ReferenceType[Any]
    right_ref: weakref.ReferenceType[Any]
    distance: float


class CompatibilityAnalysis:
    """Memoize exact unordered pairs across selection and replenishment stages."""

    def __init__(
        self,
        candidates: Iterable[Any],
        *,
        threshold: float,
        distance_evaluator: DistanceEvaluator,
        maximum_pairs: int = 131_072,
    ) -> None:
        self.threshold = float(threshold)
        self.distance_evaluator = distance_evaluator
        self.maximum_pairs = max(1, int(maximum_pairs))
        self._pairs: OrderedDict[tuple[int, int], _PairMeasurement] = (
            OrderedDict()
        )
        self._candidate_ids = {id(candidate) for candidate in candidates}
        self._exact_pair_evaluation_count = 0
        self._pair_cache_hit_count = 0

    def _prune_dead_pairs(self) -> None:
        dead = [
            key
            for key, measurement in self._pairs.items()
            if (
                measurement.left_ref() is None
                or measurement.right_ref() is None
            )
        ]
        for key in dead:
            self._pairs.pop(key, None)

    def distance(self, left: Any, right: Any) -> float:
        if left is right:
            return 0.0
        if id(right) < id(left):
            left, right = right, left
        key = (id(left), id(right))
        cached = self._pairs.get(key)
        if (
            cached is not None
            and cached.left_ref() is left
            and cached.right_ref() is right
        ):
            self._pairs.move_to_end(key)
            self._pair_cache_hit_count += 1
            return cached.distance
        distance = float(self.distance_evaluator(left, right))
        self._exact_pair_evaluation_count += 1
        self._candidate_ids.update((id(left), id(right)))
        try:
            left_ref = weakref.ref(left)
            right_ref = weakref.ref(right)
        except TypeError:
            # Never retain a non-weak-referenceable extension object or test
            # double merely to accelerate diagnostics. Production _Candidate
            # instances support weak references and use the cache below.
            return distance
        self._pairs[key] = _PairMeasurement(left_ref, right_ref, distance)
        self._pairs.move_to_end(key)
        while len(self._pairs) > self.maximum_pairs:
            self._pairs.popitem(last=False)
        return distance

    def compatible(self, left: Any, right: Any) -> bool:
        return left is right or self.distance(left, right) >= self.threshold

    def compatibility_matrix(
        self,
        candidates: Iterable[Any],
    ) -> list[list[bool]]:
        items = list(candidates)
        return [
            [self.compatible(left, right) for right in items]
            for left in items
        ]

    def nearest_distances(
        self,
        candidates: Iterable[Any],
        selected: Iterable[Any],
    ) -> dict[int, float]:
        selected_items = list(selected)
        return {
            id(candidate): min(
                (
                    self.distance(candidate, other)
                    for other in selected_items
                    if other is not candidate
                ),
                default=1.0,
            )
            for candidate in candidates
        }

    def evidence(self) -> dict[str, Any]:
        self._prune_dead_pairs()
        return {
            "schema_version": "arr.maas.compatibility_analysis.v1",
            "compatibility_threshold": self.threshold,
            "candidate_identity_count": len(self._candidate_ids),
            "cached_pair_count": len(self._pairs),
            "exact_pair_evaluation_count": self._exact_pair_evaluation_count,
            "pair_cache_hit_count": self._pair_cache_hit_count,
            "maximum_pair_count": self.maximum_pairs,
        }


__all__ = ["CompatibilityAnalysis"]
