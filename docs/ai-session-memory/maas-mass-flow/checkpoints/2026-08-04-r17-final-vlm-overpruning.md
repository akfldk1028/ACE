# MASS checkpoint: r17 final VLM over-pruning correction

Date: 2026-08-04 KST

## Project contract

- Primary goal: diverse, competition-grade MASS candidates that satisfy actual law.
- Flow: UnitBox/BaseVolume/Matrix4 -> LLM GeometryProgram AST -> typed BOOK -> compile -> principal-frame placement and exact legal polygon/CSG -> BASE VLM -> BOOK descendants -> final VLM -> selected MASS and legal archive boards.
- Facade is deferred. Capacity utilization and shared-floor targets are design diagnostics, not statutory hard-pruning gates.
- Stepped forms are allowed, but must coexist with courts, carved voids, plates, bars, curved/elliptic families and other authored identities.

## r16 root-cause evidence

- Legal archive: 10 visible MASS candidates.
- Final VLM input/scored: 2/2 with real OpenAI response IDs and zero provider-call failures.
- Final VLM hard pass: 0.
- Candidate 1 received two typed geometry edits but repair failed with `final_authority_vlm_repair_canonical_reprojection_unsupported`.
- Candidate 2 was visually strong (`gesture_clarity=0.83`, `hierarchy=0.79`, `good_step_mass`, `good_void`) but was rejected only by `book_stage_feasible_capacity_below_competition_floor` and `final_book_unresolved_pyramidal_program_relation`.
- Root cause: non-statutory capacity and a static `pyramidal_like` heuristic overruled the actual VLM judgment.

## r17 correction and result

- `design/maas/book_language/vlm_review.py`: capacity utilization no longer contributes to VLM hard-pass failures; `pyramidal_like` no longer overrides typed VLM quality/program judgment.
- `design/test_maas_book_language.py`: policy regression expectations updated.
- Focused tests: 2 passed.
- Full live command completed in 181.6 seconds.
- Result: `BOOK program portfolios: fail - neighborhood 1/5 (1 ops)`.
- Initial final VLM gate: input 2, scored 2, hard pass 1.
- Remaining rejected candidate has genuine visual/program issues: program fit, too box-like, gesture clarity and hierarchy.
- The zero-selection regression is fixed, but target 5 and morphology diversity are not complete.

## PNG paths

- Selected board: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r17\maas-book-neighborhood-5.png`
- Legal archive board: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r17\maas-book-neighborhood-0-legal-archive.png`
- Summary board: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r17\maas-book-programs-60-summary.png`
- Machine summary: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r17\maas-book-programs-summary.json`

## Next blocker

Connect final-authority VLM typed edits back through the existing canonical Matrix4 and floorwise legal materializer instead of rejecting them or applying a hardcoded geometric patch. Then rerun the target-5 live flow and inspect selected plus archive PNGs.

## r18-r26 continuation

- Final-authority VLM typed repair now enters canonical floorwise Matrix4/legal CSG projection instead of failing at the placeholder `canonical_reprojection_unsupported` branch.
- Final projected surface, authored AST, legal execution, and semantic hashes were separated through artifact validation and authoritative mesh measurement.
- LLM seed scheduling now probes up to three distinct BOOK kinds per approved BASE lineage instead of one descendant only.
- r25 completed end-to-end: 11 legal archive masses, 3 final-VLM inputs, 2 final-VLM hard passes, 1 selected because the two passes were silhouette near-duplicates (`distance=0.0855`, required `0.1`).
- r25 selected board: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r25\maas-book-neighborhood-5.png`.
- r25 witness board: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r25\maas-book-neighborhood-5-witness.png`.
- r25 legal archive: `D:\Data\25_ACE\docs\playwright\design-route-live-verify\book-program-portfolios-legal-archive-target5-r25\maas-book-neighborhood-0-legal-archive.png`.
- r26 bounded target-5 budget test: exact materialization 48, BASE input 8, BASE reviewed 5, descendants generated 5, descendants routed to final VLM 4, final-VLM hard passes 2, selected 1.
- r26 proves more budget alone is not the solution. Terminal failures were `book_projection=17`, `authored_visual_authority=9`, `floor_affine_fit=7`.
- Structural failure certificates are collected, but `bounded_parent_replenishment` is null. The next required change is to feed those typed failures and final-VLM critiques to a bounded LLM replenishment author, producing new ASTs rather than relaxing law or silhouette diversity.

## r27 bounded LLM replenishment

- Target-5 compile budget is partitioned into initial 48 plus replenishment reserve 12, cumulative limit 60.
- The replenishment cycle executed instead of being starved: initial usage 48, cycle usage 3, remaining 9.
- One live replenishment author request ran with 12 authored-visual failure certificates and BASE VLM feedback in context.
- The LLM produced three cache-miss AST families: `llm_bend_notch`, `llm_shear_notch`, and `llm_twist_lift`.
- `llm_shear_notch` failed `profiled_legal_clip_midplane_topology_mismatch`.
- `llm_bend_notch` failed `unproven_authored_mesh_completeness` during Matrix4 projection.
- `llm_twist_lift` materialized but did not reach clean/program hard pass.
- No new final hard-pass candidate entered the selection pool, so the visible result remained 1/5.
- Next action: translate these exact typed topology/completeness failures into explicit LLM AST repair constraints and request topology-safe authored variants; do not lower the silhouette diversity threshold or statutory gates.
