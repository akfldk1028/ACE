# r339-r340 target5: lineage reaches missing base-VLM artifact

Date: 2026-08-03 KST

## Changes before the runs

- Shared-floor materialization now preserves all Polygon/MultiPolygon components and courtyard holes.
- Full union geometry owns GFA, clear-depth, legal retention, and vertical-support measurements.
- Capacity replenishment gives the LLM typed per-floor GFA deficits and required utilization; named forms, deterministic geometry replacement, and gate lowering remain forbidden.
- Progressive target 5 is first-class with bounded provider and compile partitions.
- Proven LLM pre-BOOK parents can register their canonical lineage key only when program/geometry hashes, compilation, containment, and parent key match.

## r339

- Selected: 0/5
- Directed materialized: 4
- Projection materialized: 4
- Capacity plus shared-floor hard pass: 1
- Base VLM calls: 0
- The valid post-BOOK descendant was removed because its proven pre-BOOK parent key was not registered.

## r340

- Selected: 0/5
- Directed materialized: 6
- Projection materialized: 6
- Capacity plus shared-floor hard pass: 1
- Lineage gate: PASS; retained descendant via four known proven base keys.
- Base VLM calls: 0
- Base-stage VLM status: `no_viable_base_stage_candidates`.

The lineage gate now receives proof of the pre-BOOK parent, but the base-stage VLM gate receives only the post-BOOK descendant candidate. It needs the actual proven pre-BOOK GeometryProgram materialized as a base candidate with its own render. A key alone cannot be image-reviewed.

## Next exact repair

At the LLM BOOK projection boundary, preserve a bounded pre-BOOK base candidate artifact alongside the post-BOOK descendant. Feed that exact base candidate/render to the base-stage VLM audit. Release descendants only when their matching base candidate passes. Do not synthesize a proxy, reuse the descendant image, bypass base VLM, or restore obsolete aliases.

After focused lineage/base-VLM transport tests, run target5 once and inspect selected count, final VLM evidence, law/GFA/parking, morphology diversity, and PNG.
