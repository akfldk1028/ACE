# MAAS r293 / exact replay v5 checkpoint — 2026-07-28

This is the active handoff for the interrupted authored-polygon MASS recovery.
Read it before rerunning MASS, changing legal projection, replay identity,
elevation, parking, or `/design/language`.

## User intent

- Restore multiple visibly distinct authored polygon MASSes like the original
  12-card reference, rather than returning only two accepted cards or generic
  boxes.
- Current phase is design MASS + law + parking + elevation. Floor capacity is
  advisory design evidence, not permission to erase the authored MASS.
- Keep separate MASS, law Graph DB, parking, review/selector and elevation
  agents, and show the exact chain in the frontend graph.
- Put inspectable PNG evidence in `D:\Data\25_ACE\docs\mass`.
- Preserve honest truth: no VLM evaluation means no final acceptance claim.

## Current verified result

Portfolio run:

`book-program-portfolios-r293-authored-stable-legal-elevation-ten`

- 10 selected / 10 visible / 10 unique visual hashes.
- 10/10 legal hard pass.
- 10/10 geometry-retention pass.
- 10/10 parking hard pass according to the current local parking rule.
- Phenotypes: curved 2, stepped 4, voided 3, winged 1.
- No empty cards and no near-duplicate visual hashes.
- Overall portfolio is still `FAIL`, not final:
  - only 5/6 Base Volume scopes; selected set misses `1/16`;
  - stepped share is 4/10, above the final 30% limit.

Primary portfolio PNG:

`D:\Data\25_ACE\docs\mass\r293-10-authored-legal-masses-scope5of6.png`

SHA-256:

`580ED31E8A4C5D2FBAD14E36D7B25D44493E555B15E99FC63A31F790029B915A`

Reference and prior failure:

- `D:\Data\25_ACE\docs\mass\REFERENCE-original-12-authored-polygon-masses.png`
- `D:\Data\25_ACE\docs\mass\r287-FAILED-only-2-of-10.png`

## Final exact-replay evidence

Current replay:

`D:\Data\25_ACE\docs\ai-session-memory\maas-service-cache\single-executions\r293-selected-01-exact-replay-v5`

v5 deliberately replays through v4 and then the original r293 portfolio. It
therefore exercises the entire replay provenance chain after the floor-plan
identity guard was fixed.

Immutable identity:

- program hash:
  `e7c1c15fff6f9151522ffe3ed47c40abfc7a3fb09be31035918782d9c5a021c8`
- certified authored visual geometry hash:
  `8440f0a1106d97a885f43ce8ade2ecdc4a684d4673dd271cac2c6b57f0b35045`
- floor-capacity-plan hash:
  `9b82b925857b4561b54cde2dbc0b75f5c7dcb9baf4f8c0e3421217d6dd2126fc`

The same three hashes are present in the execution manifest/passport,
specialist-agent collaboration, elevation manifest and elevation condition
pack.

Physical/elevation evidence:

- authored XY coordinate authority is preserved:
  `source_footprint_centroid_local_xy_physical_z_m`;
- identity coordinate authority remains:
  `source_footprint_centroid_local_xy_normalized_z`;
- exact mesh Z bounds: 0.0–14.0 m;
- physical Z scale: 14.0 m;
- floor guides: 0, 3.5, 7, 10.5, 14 m;
- six generated 720×720 views: front, right, back, left, top, axon;
- elevation geometry mutation is forbidden.

Current v5 PNGs:

- `D:\Data\25_ACE\docs\mass\r293-selected-01-mass-v5.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-front-v5.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-right-v5.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-back-v5.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-left-v5.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-top-v5.png`
- `D:\Data\25_ACE\docs\mass\r293-selected-01-elevation-axon-v5.png`

The unversioned elevation copies in the same folder also point to v5.

Frontend proof:

- `D:\Data\25_ACE\docs\mass\r293-design-language-v5-full-graph.png`
- `D:\Data\25_ACE\docs\mass\r293-design-language-v5-selected-path.png`
- route: `http://127.0.0.1:5178/design/language`
- browser assertions found v5, program/floor/geometry hashes, LAW, PARKING,
  ELEVATION and 6-VIEW evidence with no identity/hash warning.
- the UI correctly shows `SINGLE_MASS_GEOMETRY_READY` and
  `VLM NOT EVALUATED · NO CLAIM`.

## Law Graph DB and parking truth

The v5 live specialist sequence executed:

`design_orchestrator -> maas_geometry_agent -> law_graph_agent ->
parking_agent -> review_agent -> selector`

Law evidence:

- Neo4j attempted and available at `neo4j://127.0.0.1:7687`;
- 6/6 requested articles resolved, missing 0;
- law-domain search at `localhost:8011` returned 3 results;
- numeric legal preflight and geometry retention passed.

This is not yet a permit-final law claim. Parking remains an explicit caveat:

- current artifact calculation: facility area 147.18 m²;
- local rule value: 134 m² per space;
- raw result: 1.098388;
- current half-up rule gives required 1 / provided 1;
- `source_ordinance` and `source_appendix` are still null;
- this conflicts with the earlier project statement that 2 spaces were
  required.

Do not claim that “two required spaces are satisfied.” Confirm and persist the
official Seoul ordinance/appendix and rounding authority, then rerun the
parking agent.

## Code changes in this checkpoint

1. `ARR/backend/design/maas/book_language/candidate_generation.py`
   - Builds one stable legal host from the intersection of every valid
     floor-containment section.
   - Fits the authored plan once through height, with no upper-frame morph.
   - Re-certifies the indexed visual mesh against every original floor section.
   - Missing, invalid or empty legal sections fail closed.

2. `ARR/backend/design/maas/geometry_language/floorwise_visual_projection.py`
   - Adds a per-certificate lazy buffered-section cache.
   - Reuses the same buffered legal section for point, boundary and triangle
     coverage checks without changing samples, splits, order or hash.

3. `ARR/backend/design/maas/single_execution/pipeline.py`
   - Accepts both capacity-centroid and authored source-centroid normalized-Z
     certified meshes.
   - Converts normalized Z using trusted shared-floor heights, not normalized
     capacity-compiler bounds.
   - Preserves authored coordinate labels after physicalization.
   - Allows a failed utilization target to remain advisory for elevation only
     when the shared-floor contract, site, law, parking, program-fit and
     selector gates are hard-pass and the floor-plan identity matches.
   - Validates program, certified visual geometry and floor-capacity-plan
     identities across every replay manifest/passport link.
   - Validates the terminal floor-plan identity from the original archive's
     `executionPassport.floor_capacity_plan_hash`; missing terminal identity
     fails closed.

4. Tests:
   - `ARR/backend/design/test_maas_mass_stage.py`
   - `ARR/backend/design/test_maas_single_execution.py`

## Verification completed

Latest backend command:

`C:\Python313\python.exe manage.py test design.test_maas_mass_stage design.test_maas_book_language design.test_maas_shared_floor_contract design.test_maas_geometry_language design.test_maas_flow_regressions design.test_maas_single_execution --verbosity 1`

Result: 417 tests, all passed.

Frontend focused tests:

`npm exec vitest -- run src/design/components/book-language-flow/selected-runtime-passport.test.ts src/design/components/book-language-flow/elevation-proposal.test.ts src/design/components/book-language-flow/multi-view-elevation.test.ts test/unit/design/maas-single-execution-api.test.ts`

Result: 4 files / 14 tests, all passed.

Original-resolution visual checks completed for:

- 10-card r293 MASS board;
- corrected v4/v5 front elevation;
- corrected v4/v5 axon elevation;
- selected frontend graph.

## Honest remaining work

1. Confirm and persist the official Seoul parking ordinance/appendix and the
   rounding rule; resolve 1-space versus 2-space conflict.
2. Restore all six Base Volume scopes in the selected 10 without lowering
   legal, geometry-retention or visual-distinctness gates.
3. Align the selection roof cap with the final 30% roof-concentration rule
   (current selector admitted 4/10 stepped).
4. Run required VLM critique if final product acceptance is requested. Until
   then `full_flow_complete=false`, `final_hard_pass=false`, status
   `in_progress`.
5. Do not present the internal collaboration selector's `accepted` status as
   final product acceptance; top-level truth policy is authoritative.
6. Archive `authored_visual_legal_fit_evidence` in the final artifact so the
   stable-host/no-upper-morph mode is directly auditable after the run.

## Workspace/process notes

- The nested ARR worktree is dirty and contains user work. Do not reset,
  checkout or remove unrelated files.
- Source edits are uncommitted.
- Backend used by the verified frontend is on port 18000; law search is on
  8011; Neo4j is on 7687; frontend verification is on 5178.
- Before claiming completion, rerun the backend and frontend commands above and
  inspect the current PNGs at original resolution.
