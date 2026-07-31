# Floorwise Replay Candidate Rejection Design

## Context

The proper same-PNU publishable-20 run for PNU
`1168011800104170004` reached replenishment cycle 3 with ten retained
candidates, then aborted when one candidate contained a floorwise volume whose
footprint could not be repaired for exact GeometryProgram replay:

`ValueError: floorwise volume has no replayable footprint`

The replay serializer is correct to reject that volume. The defect is that the
candidate-specific rejection escapes `_materialize_directed_geometry` and
terminates the entire portfolio run.

## Decision

Handle only the known candidate-degeneracy error at the boundary that converts
the materialized floorwise source into its exact replay GeometryProgram.

- Keep `floorwise_source_to_geometry_program` strict. It must not omit invalid
  floor bands or silently alter GFA.
- When the serializer raises exactly
  `floorwise volume has no replayable footprint`,
  `_materialize_directed_geometry` logs a candidate rejection and returns
  `None`.
- Other `ValueError` messages still propagate. Missing matrix stacks,
  non-positive height bands, and structural contract corruption must remain
  visible as run-level failures.
- `_program_pool` already treats a `None` materialization as a rejected
  candidate and continues bounded replenishment.

## Alternatives Rejected

1. Skip the invalid floor volume inside the serializer. This changes the
   building, floor count, GFA, and identity while pretending replay succeeded.
2. Catch every exception in replenishment. This hides programming and contract
   errors unrelated to candidate geometry.
3. Reduce the run to two replenishment cycles. This avoids the observed
   candidate but does not fix the failure boundary or complete the requested
   test.

## Test and Verification

1. Add a regression test with a real `SourceMass` containing a materialized
   matrix stack and a sub-tolerance floor footprint.
2. Verify RED: the candidate replay boundary raises instead of returning a
   rejection.
3. Implement the narrow error classifier and candidate-level rejection.
4. Verify GREEN and run the focused geometry/shared-floor tests.
5. Re-run the same proper PNU publishable-20 command with no paid providers.
6. Only after at least three final deterministic survivors exist, render the
   three-card shortlist and allow one bounded VLM request.

## Truth Boundary

This fix makes replenishment robust; it does not make a degenerate candidate
valid. The candidate remains rejected. It also does not add physical
stairs/elevator cores, egress routes, or room packing to the current MASS hard
gate.
