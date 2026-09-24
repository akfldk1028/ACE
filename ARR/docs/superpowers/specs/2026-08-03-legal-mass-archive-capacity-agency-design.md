# Legal MASS Archive and Capacity Agency Design

## Objective

Preserve and display every materially valid, legally containable authored MASS before design-policy scoring. Capacity utilization and floor-distribution targets guide typed revision and portfolio selection; they do not erase otherwise legal geometry before VLM review.

## Problem

The current pipeline mixes three authorities:

1. Statutory legality and exact geometry validity.
2. Program/capacity design targets such as `0.70` minimum utilization, `0.90` preferred utilization, and per-floor target areas.
3. Competition-design judgment by the MASS agent and VLM.

Because capacity and per-floor targets participate in early hard filtering, legal authored masses disappear before they can be rendered, compared, revised, or selected. A failed portfolio therefore produces a title-only PNG even when several meaningful masses were materialized.

## Authority Model

### Deterministic geometry and law authority

These conditions may prevent a candidate from entering the legal MASS archive:

- GeometryProgram/AST does not compile to a valid authored manifold.
- The visual surface payload is missing, malformed, non-manifold, or not bound to the compiled authority.
- The mass cannot be placed through the principal-frame Matrix4 graph and exact polygon/CSG legal intersection.
- The resulting occupied geometry crosses the legal parcel, height, setback, BCR, or FAR upper limits.
- Required statutory parking cannot be demonstrated for a final selectable candidate.

The legal engine is deterministic. An LLM or VLM cannot waive these conditions.

### Design-policy authority

These values are measurements, objectives, and revision signals rather than early deletion gates:

- Feasible-capacity utilization, including values below or above `0.70`.
- Preferred utilization such as `0.90`.
- Per-floor target-area differences.
- Capacity-band balance across a portfolio.
- Program-fit depth, distribution, hierarchy, and public-space quality beyond statutory minima.

No fixed capacity target may remove a legally containable MASS from the archive. The run contract may still require the final selected portfolio to satisfy configurable program and capacity objectives. Failure to meet the final contract is reported without deleting the visible legal candidates.

## Pipeline

```text
UnitBox / BaseVolume / Matrix4
-> LLM GeometryProgram/AST
-> typed BOOK operations
-> compile and authored-surface certification
-> principal-frame placement and exact legal polygon/CSG intersection
-> LEGAL MASS ARCHIVE
-> capacity/shared-floor/parking measurements
-> typed capacity or program revision proposals
-> base VLM and final VLM
-> portfolio optimization and selected set
-> diagnostic board plus selected board
```

The legal MASS archive is immutable evidence for the run. Later revisions create descendants; they do not overwrite the archived parent.

## Capacity Contract

Capacity evaluation returns a typed result with separate fields:

- `legal_hard_pass`: geometry and statutory upper-bound compliance.
- `shared_floor_measured`: whether exact occupied floor plates were measured.
- `feasible_capacity_utilization`: measured total GFA divided by feasible legal capacity.
- `capacity_objective_status`: below, within, or above the requested design band.
- `per_floor_target_deltas_m2`: diagnostic differences from the current design allocation.
- `revision_recommended`: whether the capacity agent should propose a typed AST composition.

`per_floor_target_deltas_m2` never determines statutory legality. A total utilization miss never removes the archived candidate. Typed capacity composition must recompile and re-enter every geometry and law gate as a new descendant.

## Selection Contract

The final selected set remains fail-closed:

- Every selected candidate must come from the legal archive or a legally recertified descendant.
- Every selected candidate must satisfy statutory parking.
- Portfolio objectives may request a configurable capacity band and diversity targets.
- If fewer than the requested count satisfy all final objectives, the run reports the exact deficit and still renders all archived legal candidates as non-selected diagnostics.
- The VLM judges design quality and recommends typed edits; it never overrides law.

## Rendering Contract

Each full MASS run produces two visible artifacts:

1. `legal-mass-archive.png`: every legal archived MASS, including capacity/program misses, with badges for utilization, floor deltas, parking, VLM status, and rejection reason.
2. `selected-masses.png`: only final selected candidates. If selection is empty, this board may be empty, but the legal archive board must still show the available masses.

The existing summary/witness board may link to both artifacts. Title-only output is not sufficient evidence that generation ran.

## Base and Descendant Ordering

For an LLM-authored lineage:

1. Materialize, compile, contain, certify, and archive the BASE.
2. Register its exact post-BOOK geometry hash.
3. Materialize descendants and bind `parent_geometry_hash` from the certified BASE.
4. Run BASE VLM before descendant release.
5. Preserve exact identity fail-closed behavior for missing or conflicting hashes.

Coarse `parent_key` alone is never sufficient VLM identity.

## Non-Goals

- No weakening of parcel, height, setback, BCR, FAR, or parking law.
- No named-form hardcoding.
- No floorwise prism/loft visual fallback.
- No replacement of authored GeometryProgram authority with analysis plates.
- No elevation generation in this phase.

## Acceptance Criteria

- A legal candidate below a capacity objective remains in the legal MASS archive and appears on the archive PNG.
- Per-floor target deltas cannot remove a legal candidate from that archive.
- Illegal, malformed, unbound, or non-manifold candidates remain excluded.
- Capacity revisions are typed AST descendants and pass the full deterministic pipeline again.
- BASE is registered before descendants receive exact parent identity.
- A target-5 run always produces a non-title-only legal archive PNG when at least one legal candidate exists, even if final selection is `0/5`.
- Final selected candidates continue to satisfy law, parking, exact geometry authority, VLM, and the configured portfolio contract.
