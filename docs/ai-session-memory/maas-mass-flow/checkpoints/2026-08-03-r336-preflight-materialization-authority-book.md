# r336 preflight: materialization, visual authority, BOOK, replenishment

Date: 2026-08-03 (Asia/Seoul)

## Goal

Restore the MASS-first pipeline without reintroducing stepped legal-floor replay:

`UnitBox/Matrix4 BaseVolume -> LLM GeometryProgram/AST -> typed BOOK -> authored legal projection -> legal/GFA/parking -> render/VLM -> typed revision -> diverse selection`

Legal floor volumes remain analysis-only. The authored post-BOOK program and its certified projected surface are the only final program/visual authorities.

## r335 attrition root causes and repairs

### 1. `floor_affine_fit` (4 candidates)

Root cause: floorwise CSG bisection retained the upper, over-target candidate while the immediate legality contract accepted only `achieved <= target`. Valid lower candidates were discarded.

Repair:

- Return the maximal positive legal lower projection at or below target.
- Keep strict overfill rejection.
- Preserve actual legal polygon hash separately from any claimed hash.
- Preserve typed terminal evidence.

Review: Task 7A `SPEC PASS / QUALITY PASS`.

### 2. `authored_identity_collapse` (2 candidates)

Root cause: visual morphology used `SourceMass.volumes`, which are stepped legal/GFA proxy volumes. The gate therefore mistook legal floor variation for collapse of the authored MASS.

Repair:

- Compare authored visual surface against authored visual surface only.
- Keep proxy volumes out of visual identity.
- Preserve real AST and BOOK no-op hash gates.
- Preserve vertical proportions with one global normalization scale.
- Fail closed for degenerate, open, edge-nonmanifold, vertex-nonmanifold, or inconsistently wound triangle shells.

Focused result: 10 Task 7B tests passed. Independent review: `SPEC PASS / QUALITY PASS`.

### 3. `authored_visual_authority` (5 candidates)

Root causes:

- Detailed projection/certificate causes were collapsed into one terminal label.
- Revalidation still emitted the obsolete `visual_projection_or_replay` stage.
- Legal-floor prism replay remained an executable/final geometry authority in downstream contracts.
- Projection certificates hashed exact coordinates while live surface records used three-decimal diagnostic signatures.
- Downstream identity incorrectly required upstream authored compilation hash to equal the post-projection visual hash.

Repair:

- Preserve bounded typed evidence for matrix4 projection, profiled clip, empty/no-valid surface, CSG/midplane/certificate, and revalidation.
- Send typed causes to LLM replenishment without stale node IDs or mesh payloads.
- Emit `authored_visual_authority`; read the old stage only for persisted compatibility.
- Keep post-BOOK authored AST as final program authority.
- Bind `authored input hash + legal floor field hash -> projected surface hash` through a projection certificate.
- Bind render, VLM, preference, spatial, and elevation identities to the projected surface hash.
- Keep legal floor volumes only for legal/GFA/parking/containment analysis.
- Remove legal-floor loft/prism replay from visual/final authority.
- Use exact finite surface authority records; keep rounded signatures diagnostic-only.
- Accept obsolete authority aliases only at explicitly marked persisted-record ingestion.

Focused result: Task 7C plus no-replay regression, 8/8 passed after cleanup. Static review found the production authority model consistent. A broader production-consumer fixture remains deferred because the synthetic gymnasium source lacks a real semantic carrier graph; this is a test-fixture gap, not a production defect.

## Task 7D: r335 BOOK no-op

Root cause: `_body_program_for_book_projection()` skipped BOOK for every program marked `openai_llm_geometry_author` or `llm_geometry_author_active`. The same LLM AST was compiled before and after BOOK, so both program and exact geometry hashes were equal.

Repair:

- Apply BOOK whenever typed BOOK calls are present, independent of provider, family, or named form.
- Pass the live LLM `GeometryProgram` through the generic BOOK adapter.
- Keep the dedicated hard failures for inactive adapter metadata, post-BOOK compile failure, equal program hash, and equal exact geometry hash.
- Keep three identities separate: pre-BOOK LLM AST, post-BOOK authored AST, and projected final surface.
- Preserve LLM provider/model/response provenance only for true LLM candidates.
- Remove stale LLM provenance from procedural candidates.
- Keep post-BOOK AST as final program authority and prohibit floorwise replay.

Regressions include the r335-shaped generic scopes:

- `carve + offset`, scope `1/4`
- `overlap + expand`, scope `1/2`

Focused result: Task 7C/7D 16 passed plus 2 subtests after final provenance repair. Independent review: `SPEC PASS / QUALITY PASS`.

## Task 6C: provider partitions and replenishment

Contracts:

- Target 3: provider/live `16/13`
- Target 10: provider/live `44/39`
- Target 20: provider/live `77/69`
- Hard partitions: `author_initial`, `author_replenishment`, `base_candidate`, `exact_candidate`, `portfolio_board`
- Recursive compiler repair inherits its author stage.
- Base VLM feedback is bounded and removes stale node IDs.
- Author exhaustion and consumption evidence are typed and truthful.

Focused integration now proves the real path:

`author -> seed -> _program_pool -> _Candidate -> run_replenishment_cycle.generated_pool`

Observed contract: `generated_pool=1`, `evaluated=compiled=clean=program_passed=1`, initial/replenishment requests `2/1`, three bounded HTTP calls, one exact compile, no VLM partition borrowing, typed replenishment exhaustion and stop.

Independent review: `SPEC PASS / QUALITY PASS`.

## r336 execution gate

Run one bounded neighborhood target-3 full MASS test with small but nonzero VLM partitions. Do not run elevation generation.

Required report:

- authored seeds and replenishment seeds
- materialization terminal reasons with typed subreasons
- materialized candidate count
- legal/floor/program hard-pass count
- base VLM reviewed/pass count
- exact VLM reviewed/pass count
- selected count
- exact output directory and board PNG path
- direct PNG inspection for visible MASS and diversity

Do not claim success from a blank diagnostic board. If selection remains zero, use the new typed evidence and change approach before another full run.
