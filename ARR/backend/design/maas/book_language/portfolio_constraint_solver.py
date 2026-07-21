"""Small exact solver for the final, already hard-gated BOOK portfolio.

Generation and VLM review can produce at most a few dozen final candidates.
At that scale an exact branch-and-bound search is preferable to letting an
early greedy pick block several mutually compatible later candidates.  The
caller supplies typed cap keys and a measured pairwise compatibility matrix;
this module has no geometry, program or VLM authority of its own.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class ConstraintCandidateFacts:
    score: float
    cap_keys: tuple[str, ...]
    coverage_tags: tuple[str, ...] = ()


def solve_maximum_compatible_subset(
    facts: list[ConstraintCandidateFacts],
    compatibility: list[list[bool]],
    *,
    target_count: int,
    maximum_key_counts: dict[str, int],
    required_coverage_tags: tuple[str, ...] = (),
) -> tuple[int, ...]:
    """Return a maximum-cardinality subset without relaxing any supplied cap."""
    count = len(facts)
    if count == 0 or target_count <= 0 or len(compatibility) != count:
        return ()
    if any(len(row) != count for row in compatibility):
        return ()

    order = sorted(
        range(count),
        key=lambda index: (
            -sum(not compatibility[index][other] for other in range(count) if other != index),
            facts[index].score,
        ),
        reverse=True,
    )
    required = set(required_coverage_tags)
    best_feasible: tuple[int, ...] = ()
    best_any: tuple[int, ...] = ()

    def quality(indices: tuple[int, ...]) -> tuple[int, int, float]:
        covered = {
            tag for index in indices for tag in facts[index].coverage_tags
        }
        return (
            len(indices),
            len(covered & required),
            sum(facts[index].score for index in indices),
        )

    def visit(
        position: int,
        chosen: tuple[int, ...],
        usage: Counter[str],
        covered: set[str],
    ) -> None:
        nonlocal best_any, best_feasible
        if quality(chosen) > quality(best_any):
            best_any = chosen
        if required.issubset(covered) and quality(chosen) > quality(best_feasible):
            best_feasible = chosen
        if position >= len(order) or len(chosen) >= target_count:
            return
        remaining = len(order) - position
        incumbent_count = len(best_feasible or best_any)
        if len(chosen) + remaining < incumbent_count:
            return

        candidate_index = order[position]
        candidate = facts[candidate_index]
        allowed = all(
            usage[key] < max(0, int(maximum_key_counts.get(key, target_count)))
            for key in candidate.cap_keys
        ) and all(compatibility[candidate_index][other] for other in chosen)
        if allowed:
            for key in candidate.cap_keys:
                usage[key] += 1
            visit(
                position + 1,
                (*chosen, candidate_index),
                usage,
                covered | set(candidate.coverage_tags),
            )
            for key in candidate.cap_keys:
                usage[key] -= 1
        visit(position + 1, chosen, usage, covered)

    visit(0, (), Counter(), set())
    winner = best_feasible or best_any
    return tuple(sorted(winner))


def solve_bounded_compatible_subset(
    facts: list[ConstraintCandidateFacts],
    compatibility: list[list[bool]],
    *,
    target_count: int,
    maximum_key_counts: dict[str, int],
    required_coverage_tags: tuple[str, ...] = (),
    beam_width: int = 512,
) -> tuple[int, ...]:
    """Beam-search a large hard-gated pool without exponential backtracking.

    Required coverage is ranked before score, and low-conflict/rare-coverage
    candidates are visited first. Every retained state still satisfies the
    caller's exact pairwise compatibility matrix and typed cap counts.
    """

    count = len(facts)
    if count == 0 or target_count <= 0 or len(compatibility) != count:
        return ()
    if any(len(row) != count for row in compatibility):
        return ()
    required = set(required_coverage_tags)
    coverage_supply = Counter(
        tag for fact in facts for tag in fact.coverage_tags if tag in required
    )
    order = sorted(
        range(count),
        key=lambda index: (
            min(
                (coverage_supply[tag] for tag in facts[index].coverage_tags if tag in required),
                default=count + 1,
            ),
            sum(not compatibility[index][other] for other in range(count) if other != index),
            -len(set(facts[index].coverage_tags) & required),
            -facts[index].score,
        ),
    )
    # chosen, usage, covered, score
    states: list[tuple[tuple[int, ...], Counter[str], frozenset[str], float]] = [
        ((), Counter(), frozenset(), 0.0)
    ]

    def rank(state: tuple[tuple[int, ...], Counter[str], frozenset[str], float]) -> tuple[int, int, float]:
        chosen, _usage, covered, score = state
        return len(covered & required), len(chosen), score

    for candidate_index in order:
        candidate = facts[candidate_index]
        expanded = list(states)
        for chosen, usage, covered, score in states:
            if len(chosen) >= target_count:
                continue
            if not all(
                usage[key] < max(0, int(maximum_key_counts.get(key, target_count)))
                for key in candidate.cap_keys
            ):
                continue
            if not all(compatibility[candidate_index][other] for other in chosen):
                continue
            next_usage = usage.copy()
            next_usage.update(candidate.cap_keys)
            expanded.append((
                (*chosen, candidate_index),
                next_usage,
                covered | frozenset(candidate.coverage_tags),
                score + float(candidate.score),
            ))
        states = sorted(expanded, key=rank, reverse=True)[:max(8, int(beam_width))]
        complete = [
            state for state in states
            if len(state[0]) >= target_count and required.issubset(state[2])
        ]
        if complete:
            return tuple(sorted(max(complete, key=rank)[0]))

    feasible = [state for state in states if required.issubset(state[2])]
    winner = max(feasible or states, key=rank)
    return tuple(sorted(winner[0]))


def solve_milp_compatible_subset(
    facts: list[ConstraintCandidateFacts],
    compatibility: list[list[bool]],
    *,
    target_count: int,
    maximum_key_counts: dict[str, int],
    required_coverage_tags: tuple[str, ...] = (),
    time_limit_seconds: float = 45.0,
) -> tuple[int, ...]:
    """Solve the large final portfolio as a binary linear program.

    Each candidate is one binary variable. Incompatible silhouettes become
    pair constraints, typed diversity limits become cardinality constraints,
    and required scopes/capacity/program tags become coverage constraints.
    This reports the actual best feasible cardinality instead of presenting a
    narrow beam approximation as if it were a maximum set.
    """

    count = len(facts)
    if count == 0 or target_count <= 0 or len(compatibility) != count:
        return ()
    if any(len(row) != count for row in compatibility):
        return ()
    try:
        import numpy as np
        from scipy.optimize import Bounds, LinearConstraint, milp
        from scipy.sparse import lil_matrix
    except ImportError:
        return ()

    rows: list[tuple[dict[int, float], float, float]] = []
    rows.append((
        {index: 1.0 for index in range(count)},
        0.0,
        float(target_count),
    ))
    for left in range(count):
        for right in range(left + 1, count):
            if not compatibility[left][right]:
                rows.append(({left: 1.0, right: 1.0}, 0.0, 1.0))
    candidates_by_key: dict[str, list[int]] = {}
    for index, fact in enumerate(facts):
        for key in fact.cap_keys:
            candidates_by_key.setdefault(key, []).append(index)
    for key, indices in sorted(candidates_by_key.items()):
        rows.append((
            {index: 1.0 for index in indices},
            0.0,
            float(max(0, int(maximum_key_counts.get(key, target_count)))),
        ))
    for tag in dict.fromkeys(required_coverage_tags):
        indices = [
            index for index, fact in enumerate(facts)
            if tag in fact.coverage_tags
        ]
        if not indices:
            return ()
        rows.append((
            {index: 1.0 for index in indices},
            1.0,
            np.inf,
        ))

    matrix = lil_matrix((len(rows), count), dtype=float)
    lower = np.empty(len(rows), dtype=float)
    upper = np.empty(len(rows), dtype=float)
    for row_index, (coefficients, low, high) in enumerate(rows):
        for candidate_index, value in coefficients.items():
            matrix[row_index, candidate_index] = value
        lower[row_index] = low
        upper[row_index] = high
    scores = np.asarray([float(fact.score) for fact in facts], dtype=float)
    if scores.size and float(np.max(scores) - np.min(scores)) > 1e-12:
        scores = (scores - np.min(scores)) / (np.max(scores) - np.min(scores))
    objective = -(np.ones(count, dtype=float) + scores * 1e-4)
    result = milp(
        c=objective,
        integrality=np.ones(count, dtype=int),
        bounds=Bounds(np.zeros(count), np.ones(count)),
        constraints=LinearConstraint(matrix.tocsr(), lower, upper),
        options={"time_limit": max(1.0, float(time_limit_seconds)), "presolve": True},
    )
    if result.x is None:
        return ()
    selected = tuple(index for index, value in enumerate(result.x) if value >= 0.5)
    # Reaching the caller's target proves cardinality optimal even if HiGHS
    # stops before closing a tiny score tie. Below target, accept only a solver
    # result explicitly reported as optimal; a time-limited incumbent is not a
    # proof of candidate-supply failure.
    if len(selected) >= target_count or bool(result.success):
        return selected
    return ()


__all__ = [
    "ConstraintCandidateFacts",
    "solve_bounded_compatible_subset",
    "solve_milp_compatible_subset",
    "solve_maximum_compatible_subset",
]
