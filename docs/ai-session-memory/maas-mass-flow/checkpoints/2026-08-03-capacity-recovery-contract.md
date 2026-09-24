# 2026-08-03 MASS capacity recovery contract

## Observed failure

- r338/r340 produced only one `capacity + shared-floor` survivor.
- A `3/8` candidate measured near `0.3425`, matching `0.9133 * 3/8`.
- Shared-floor was not inventing the loss. It measured the authored BaseVolume before later composition recovered the final program yield.

## Root contract

- BOOK `BaseVolume` is the complete initial authored mass state.
- Scope and final capacity are orthogonal.
- BASE VLM uses the developmental floor `0.40 * scope_fraction`.
- A final candidate still uses the unscaled legal capacity floor and must reach the source minimum, currently `0.70`.
- Legal envelope, BCR, FAR, parking, shared-floor, authored visual authority, and typed AST identity are never relaxed.

## Recovery path

1. Keep the LLM-authored BaseVolume and BOOK identity.
2. Measure the exact shared-floor capacity deficit.
3. Recompose the authored body with the generic typed `related_array` / `pack` operator. Do not select a named finished form.
4. Recompile and rematerialize the changed GeometryProgram.
5. Accept the replacement only when shared-floor and final capacity both hard-pass and utilization strictly improves.
6. Render and run VLM only after those deterministic gates.

## Code scope

- `candidate_generation.py`: activates measured typed-AST capacity composition and requires recertification before replacement.
- `vlm_review.py`: enforces the already-computed stage capacity floor, including scope-normalized BASE review.
- Focused regressions cover typed composition, retry selection, shared-floor remeasurement, and BASE/final VLM capacity floors.

## Non-goals

- No named-form hardcoding.
- No floorwise prism/loft visual fallback.
- No normalization of the final `0.70` capacity authority by BaseVolume scope.
- No elevation work in this phase.
