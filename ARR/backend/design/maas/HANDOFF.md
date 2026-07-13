# MAAS Legal Envelope Handoff

Updated: 2026-06-25

## 2026-06-25 MAAS Paper-Style Diversity / Section Profile Verification

- User issue: 20 mass alternatives still looked too similar. The user correctly
  objected that a MAAS/paper-style implementation should not merely rename
  stacked boxes as `sloped`, `diagonal`, or `terrace`.
- Current implementation state:
  - `diversity.py` now includes MAAS-style verb sequence metrics:
    set Jaccard, token F1, ordered LCS, `sequence_distance`, and
    `sequence_diversity_score`.
  - `legal_mesh_optimizer.py` now uses a clone/MAAS-inspired representative
    selection pass: legal GeoJSON footprint distance + normalized mass metrics
    + verb sequence distance + concept distance. This is ARR's legal-runtime
    equivalent of the clone/MAAS diversity/K-medoids idea; ARR does not depend
    on STL mesh features in production.
  - Section-design verbs are preserved in selection:
    `diagonal_connect`, `terrace_link`, and `sloped_roof_mass` are not filtered
    out only because they share a legal ground footprint with another candidate.
  - New canonical field: `properties.section_profile` and
    `properties.maas_model.section_profile`. It is derived from
    `maas_verb_sequence`, not from a one-off visual overlay. Current kinds:
    `diagonal_connector`, `terrace_ribbon`, `sloped_roof`.
  - `benchmark_maas_algorithms` can render 20-candidate PNG grids with
    `--render-alt-png`. The renderer reads `section_profile`, so sloped roof,
    diagonal connector, and terrace ribbon are visible in the verification PNG.
- Latest verification command:
  ```bash
  cd /mnt/d/Data/25_ACE/ARR/backend
  .venv/bin/python manage.py benchmark_maas_algorithms \
    --out-dir /mnt/d/Data/25_ACE/docs/ai-session-memory/maas-benchmarks-fast \
    --max-variants 20 \
    --render-alt-png \
    --alt-grid-limit 20 \
    --case-id rect_legal_envelope \
    --skip-original-baseline \
    --operators grammar_terrace_ribbon_stepback grammar_sloped_roof_envelope grammar_diagonal_step_connector
  ```
- Latest benchmark result:
  - `successful_scenarios=4/4`
  - `feature_count=80`
  - `average_unique_shapes_per_scenario=20.0`
  - `unique_mass_shape_count=31`
  - `unique_verb_count=21`
  - `section_connector_feature_count=11`
  - `legal_pass_rate=1.0`
  - `preferred_survival_rate=1.0`
  - `preferred_top_rate=1.0`
- Latest PNG outputs:
  - `docs/ai-session-memory/maas-benchmarks-fast/alt_grids/rect_legal_envelope__baseline_legal_envelope.png`
  - `docs/ai-session-memory/maas-benchmarks-fast/alt_grids/rect_legal_envelope__preferred_grammar_terrace_ribbon_stepback.png`
  - `docs/ai-session-memory/maas-benchmarks-fast/alt_grids/rect_legal_envelope__preferred_grammar_sloped_roof_envelope.png`
  - `docs/ai-session-memory/maas-benchmarks-fast/alt_grids/rect_legal_envelope__preferred_grammar_diagonal_step_connector.png`
- Latest tests passed:
  ```bash
  cd /mnt/d/Data/25_ACE/ARR/backend
  .venv/bin/python -m py_compile \
    design/maas/diversity.py \
    design/maas/legal_mesh_optimizer.py \
    design/management/commands/benchmark_maas_algorithms.py
  .venv/bin/python manage.py test \
    design.test_maas_export.MaasLegalVariantsTest.test_maas_sequence_metrics_follow_reference_eval_contract \
    design.test_maas_export.MaasLegalVariantsTest.test_variant_selection_preserves_capacity_and_shape_diversity \
    design.test_maas_export.MaasLegalVariantsTest.test_maas_algorithm_benchmark_command_writes_latest_json \
    -v 2
  ```
- Important limitation:
  - Do not claim final paper-grade 3D geometry yet. The legal quantities still
    use vertical `mass_volumes` and floor plates. `section_profile` makes the
    design intent machine-readable and visible in benchmark PNGs, but Cesium
    and any downstream mesh export still need to convert that profile into true
    inclined/terraced surface geometry.
  - Next technical step: make the frontend/Cesium mass renderer and any export
    path read `section_profile` and build actual sloped/diagonal/terrace faces,
    while keeping legal FAR/BCR checks based on the conservative floor-plate
    accounting.

## 2026-06-26 Frontend Section Profile / Goal Alignment

- Goal reminder from `/mnt/d/Data/25_ACE/goal.md`:
  - The product target is not a generic BIM/CAD generator. It is a legal
    massing/design collaboration system where law, parking, MAAS geometry,
    design review, and final QA agents expose their reasoning in the `/design`
    UI.
  - Mesh/OpenSCAD/IFC-style outputs are useful as export or verification
    adapters, but the ARR design result remains the source of truth:
    `mass_geojson + maas_model + legal evidence + section_profile`.
- Implemented frontend bridge:
  - `ARR/frontend/src/design/lib/cesium/mass-entities.ts` now reads
    `properties.section_profile` or `properties.maas_model.section_profile`.
  - It overlays section-design geometry on top of existing legal extrusions:
    `sloped_roof` uses a per-position-height sloped roof plane and ribs;
    `diagonal_connector` uses a raised diagonal connector polyline;
    `terrace_ribbon` uses raised terrace band polylines.
  - Legal volume rendering was not replaced. FAR/BCR/height calculations still
    come from the conservative floor plates and `mass_volumes`.
  - `ARR/frontend/src/design/lib/types.ts` now types `section_profile`.
  - `ARR/frontend/src/design/lib/ag-light-collaboration.ts` now includes
    section profile kind/render hint in the `maas_geometry_agent` trace so the
    collaboration UI can explain the section-design choice.
- Verification:
  - `cd ARR/frontend && npm run type-check` passed.
  - WSL headless Playwright opened `/design`, queried PNU
    `1168011800104170004`, optimized, and saved
    `docs/playwright/design-route-live-verify/section-profile-cesium-check.png`.
    In WSL headless it fell back to `2D MASS PREVIEW` because WebGL was
    unavailable, so Cesium entity pixels were not verified there.
  - Backend shell check confirmed 20 MAAS candidates include section profiles:
    `grammar_diagonal_step_connector_layered -> diagonal_connector` and
    `grammar_sloped_roof_envelope_layered -> sloped_roof`.
- Next verification to run from Windows Chrome CDP:
  ```powershell
  cd D:\Data\25_ACE
  node docs\playwright\design-route-live-verify\windows-cdp-vworld-optimize-check.cjs
  ```
  Then inspect `window.__arrLastMassRender`, entity ids containing
  `section-profile`, and the screenshot. WSL headless cannot prove WebGL pixels.
- OpenAI/aesthetic boundary:
  - `gpt-image` already exists under
    `ARR/backend/design/maas/aesthetic/adapters/openai_image.py`.
  - It is for locked-geometry facade/material visualization only. It must not
    create, legalize, or mutate the mass. Keep geometry first, multi-view
    reference second, image/material generation third, projection/export last.

## 2026-06-26 Late Loop: User Rejection / Corrected Review Standard

- User rejected the first 20-alt PNG as still too close to stacked legal boxes:
  this was a valid criticism. Do not describe the earlier section-profile work
  as paper-grade mass geometry.
- Fixes now applied:
  - `legal_mesh_optimizer.py` has a final design-balanced 20-card selection.
    It preserves plan-diverse representatives (`interlock`, `overlap`,
    `split`, `branch`, `pinch`, `courtyard`, `void_notch`, `slender_bar`) before
    backfilling similar legal stepbacks.
  - For `max_variants >= 8`, the early K-medoid branch also injects those
    family representatives so they are not lost before final selection.
  - `mass-entities.ts` no longer draws elevated duplicate parking stall lines
    in the default Cesium review view. Parking guide lines are clamped to
    ground and labels are lowered.
  - `render-maas-20-alt.cjs` now renders section evidence less like arbitrary
    pink markup: diagonal connector is a width-bearing connector face, terrace
    ribbons are tighter edge bands, and sloped roof is closer to the mass top.
- Latest real-PNU evidence:
  - PNU `1168011800104170004`
  - PNG `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - 20 candidates, 19 unique `mass_shape`, 6 section-profile candidates.
  - Visible plan families now include interlock, overlap, split, branch, pinch,
    courtyard, void/open-court, slender bar, legal layered, and section-design
    grammar candidates.
  - `parkingPass=0`; still not permit-ready.
- Remaining hard problem:
  - Section-profile candidates are still conservative floor-plate stacks plus
    render/section evidence. True sloped/diagonal/terrace source geometry has
    not been implemented yet.
  - Next proper research step is to generate and validate source solids for
    sloped/diagonal/terrace forms and optimize those with parking feasibility,
    not to add more visual overlays.

## 2026-06-27 Backend Section Source Volumes

- First backend source-volume implementation is now in
  `legal_mesh_optimizer.py`.
- `properties.mass_volumes` and `properties.maas_model.volumes` are now
  materialized for section-profile candidates instead of relying only on
  frontend/PNG overlays.
- New metadata:
  - `properties.section_profile_materialized.status =
    materialized_inside_legal_floor_plates`
  - `section_source_sloped_roof`
  - `section_source_terrace_ribbon`
  - `section_source_diagonal_connector`
  - `section_source_diagonal_connector_bridge`
- The materialized volumes are clipped inside each legal floor-plate band.
  FAR/BCR/height accounting still uses conservative `floor_plates`.
- Diagonal candidates append a source bridge volume inside the union of legal
  floor-plate bands. The PNG renderer draws that real volume with a darker
  orange source-volume style; it is no longer a fake pink line overlay.
- Latest real-PNU evidence for `1168011800104170004`:
  - 20 candidates
  - 19 unique `mass_shape`
  - 6 section materialized candidates
  - 2 diagonal bridge source-volume candidates
  - `parkingPass=0`
- Important limitation: this is still a conservative stepped/shifted solid
  approximation, not a full non-orthogonal mesh optimizer. Next step is a true
  3D solid/mesh path for sloped faces and connector surfaces plus parking-
  feasible generation.

## 2026-06-28 Backend Section Source Surfaces

- Continued PNG review loop. The issue after source volumes was that
  sloped/terrace/diagonal candidates still read as coarse stepped solids.
- `legal_mesh_optimizer.py` now emits backend source surfaces:
  - `properties.section_source_surfaces`
  - `properties.maas_model.section_source_surfaces`
  - surface fields: `role`, `kind`, `surface_type`, `vertices_wgs84_h`
- Current generated surface roles:
  - `section_surface_sloped_roof_plane`
  - `section_surface_terrace_band_1..3`
  - `section_surface_diagonal_connector_deck`
- `render-maas-20-alt.cjs` draws those backend surfaces directly. Avoid going
  back to frontend-only fake overlays.
- Latest PNU `1168011800104170004` evidence:
  - 20 candidates
  - 19 unique `mass_shape`
  - 6 section materialized candidates
  - 6 surface candidates
  - 10 total source surfaces
  - `parkingPass=0`
- Visual judgment: visible improvement; still coarse and not final competition
  quality. Next loop should improve actual grammar/operator geometry or parking-
  feasible generation.

## 2026-06-25 MAAS Agent Modularization / AG-light Flow State

- User goal: the right-side "AI 설계 협업" must show a real law-to-design
  collaboration, not a decorative graph. The backend agent structure should be
  modular like official ADK/A2A examples: each agent owns a folder, card, and
  contract; the orchestrator owns the canonical flow.
- Current backend structure:
  - `agents/orchestrator/flow.py`: canonical handoff sequence
    `user -> design_orchestrator -> law_graph_agent -> parking_agent -> maas_geometry_agent -> review_agent -> design_orchestrator`.
  - `agents/orchestrator/agent.py`: top-level routing card/result.
  - `agents/law_graph_agent/agent.py`: FAR/BCR/height constraint review.
  - `agents/parking_agent/agent.py`: parking count/layout precheck review.
  - `agents/maas_geometry_agent/agent.py`: MAAS operation/shape explanation.
  - `agents/review_agent/agent.py`: rejected-candidate/final audit summary.
  - `agents/shared/types.py`: `AgentContext`, `AgentResult`, `AgentCard`, `MaasAgent`.
  - `agents/shared/registry.py`: registry/card builder and review runner.
  - `agents/shared/evidence.py`: shared feature/parking evidence helpers.
  - `agents/contracts.py`: compatibility wrapper for existing interactive endpoint; it delegates to the registry now.
- Current agent ids are intentionally aligned with
  `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json` and frontend
  `ARR/frontend/src/design/components/ag-light-flow/agents/*`:
  `law_graph_agent`, `parking_agent`, `maas_geometry_agent`, `review_agent`.
  Do not reintroduce old ids `law_agent`, `geometry_agent`, or
  `optimization_agent` in API output.
- `ARR/backend/design/scripts/ag_light_agent_flow_cli.py` imports
  `orchestrator.flow.FLOW_STEPS` instead of duplicating flow text. This keeps
  CLI, backend, and React Flow semantics aligned.
- Verified this session:
  - Python compile for modified agent/CLI files passed with `.venv/bin/python`.
  - Direct registry smoke check returned cards:
    `design_orchestrator, law_graph_agent, parking_agent, maas_geometry_agent, review_agent`.
  - Django targeted tests passed:
    `test_interactive_operation_endpoint_returns_synced_metrics`,
    `test_interactive_offset_edge_returns_agent_reviewed_legal_mass`,
    `test_maas_agent_registry_exposes_flow_cards`.
  - AG-light CLI live bus smoke passed:
    `.venv/bin/python design/scripts/ag_light_agent_flow_cli.py --runs 1 --delay 0 --base-url http://127.0.0.1:8200`
    returned `success_rate: 100.0%`.
- Next frontend work, if requested:
  - React Flow should display per-agent reasoning/evidence from `agent_reviews`
    and A2UI updates: cited legal limits/rule ids, parking count/layout evidence,
    MAAS operation/shape reason, and final review status.
  - Keep the graph visually simple and vertical. Lines must be readable; avoid
    dense crossed edges. The user expects the flow to show real-time progress
    when PNU lookup/optimization runs.

## 2026-06-15 Parking Layout / VWorld Resume State

- User issue: parking looked like odd diagonal/floating lines, stalls were visually unclear, adjacent small stalls were separated, and the sidebar did not explain why the legal count was what it was.
- Current implementation state:
  - Live Neo4j parking graph is available from WSL at
    `bolt://172.27.80.1:7687` with `NEO4J_PASSWORD=11111111`.
    The backend must be started with these env vars to avoid JSON fallback:
    `NEO4J_URI=bolt://172.27.80.1:7687 NEO4J_PASSWORD=11111111 .venv/bin/python manage.py runserver 127.0.0.1:18000`.
    Latest graph checks: `verify_parking_law_graph.py` `49/49 passed`,
    `check_parking_counts.py` `23/23 passed`.
  - `ARR/backend/design/maas/parking_layout.py`
    - Grid solver still operates at mass-stage feasibility, not final BIM.
    - Candidate selection now tries same-row contiguous stalls first.
    - Expected small-row result: `adjacency.status=row_contiguous`, `gap_pairs=0`, `max_gap_m=0`.
    - Layout result now includes `layout_formula`, `adjacency`, `column_clearance`, `drive_aisle_clearance`, and `turning_clearance`.
    - Grid result now includes `entrance_connection_type`, `entrance_verified`,
      and connector dimensions; `site_connector_v1` means a 3m-wide straight
      connector corridor from drive cell to road frontage stays inside the drive
      area and real `road_frontage_geometry` is present.
    - Piloti columns/cores are not read from structural drawings. Current status `column_clearance.status=deferred_structural_review` means record the assumed clear bay but do not display it as OK.
    - Turning is not a vehicle swept-path simulation. Current method `stall_frontage_and_entrance_connector_v1` checks whether stalls have enough frontage on the generated 6m drive aisle and whether that aisle connects to the entrance connector. For `grid_connected_90` row-contiguous stalls, `contiguous_row_frontage_relief` accepts a row with one generated 6m drive cell per stall to avoid false line-intersection failures.
    - For `공동주택`, `parking_requirements.py` now computes a mass-stage housing parking estimate from `주택건설기준 등에 관한 규정 제27조` and Seoul ordinance row 5. `legal_mesh_optimizer.py` supplies a `mass_stage_estimate` household/exclusive-area schedule from floor plates, or `num_floors * footprint_area` when floor plates are absent. This is a planning estimate until real household/exclusive-area schedules are supplied.
  - `ARR/frontend/src/design/lib/cesium/mass-entities.ts`
    - Exact stall polygons render as clean solid pink lines (`#ff2f92`) with dark shadow/raised visible line.
    - Raised stall lines are drawn higher/thicker (`groundH + 1.15m`) so they remain visible through translucent mass volumes.
    - Parking envelope/hatch/guide clutter is suppressed when exact stalls exist.
    - `grid_solver.entrance_connector_polygon_wgs84` renders as a low-alpha cyan corridor/outline plus thin centerline for the 3m road-to-drive connector.
    - Piloti support columns and `PILOTI VOID` labels are intentionally not rendered until explicit structural column/core polygons exist.
  - `ARR/frontend/src/design/components/DesignInspector.tsx`
    - Shows legal parking formula, rule id, layout mode, 11m/16m module formula, adjacency, aisle, entrance connector, and turning.
    - Column/core status is intentionally hidden for now; backend evidence may still record `deferred_structural_review`.
  - Playwright batch script:
    - `docs/playwright/design-route-live-verify/windows-cdp-vworld-pnu-batch.cjs`
    - Uses Windows Chrome CDP/VWorld and saves zoom PNGs.
- Latest verified command:
  ```bash
  powershell.exe -NoProfile -Command "node D:\\Data\\25_ACE\\docs\\playwright\\design-route-live-verify\\windows-cdp-vworld-pnu-batch.cjs --cases=D:\\Data\\25_ACE\\docs\\playwright\\design-route-live-verify\\parking-stall-cases.json"
  ```
- Latest live local URL: `http://127.0.0.1:5174/design`
- Latest JSON/PNG result paths:
  - `docs/playwright/design-route-live-verify/pnu-batch/01_gangnam-small-neighborhood-stalls_1168011800104170004.json`
  - `docs/playwright/design-route-live-verify/pnu-batch/02_gangnam-dogok-neighborhood-stalls_1168011800104670003.json`
  - `docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-neighborhood-stalls_1168011800104170004.png`
  - `docs/playwright/design-route-live-verify/pnu-batch/zoom_02_gangnam-dogok-neighborhood-stalls_1168011800104670003.png`
- Latest observed values:
  - PNU `1168011800104170004`: `piloti_ground`, required/provided `3/3`, `parkingStallEntities=3`, `parkingEntities=12`, `pilotiEntities=0`, `adjacency.status=row_contiguous`, `touching_pairs=2`, `gap_pairs=0`, `max_gap_m=0`, backend `column_clearance.status=deferred_structural_review` only, aisle `6m`, `turning_clearance.status=v1_pass`, `turning_clearance.frontage_connected_stalls=1/3`, `turning_clearance.contiguous_row_frontage_relief.available=true`, `grid_solver.entrance_verified=true`, `grid_solver.entrance_connection_type=site_connector_v1`, connector length `8m`, connector width `3m`, connector WGS84 polygon present/rendered, layout status `pass`.
  - PNU `1168011800104170004` with building type `공동주택`: default-apartment parking count/visual regression fixed. `required_count.status=computed_estimate`, `selected_rule_id=seoul_parking_appendix2_row_05`, `base_rule_id=parking_appendix1_row_05`, `source_ordinance=seoul_parking_ordinance`, `required_spaces=3`, `raw_spaces=2.4`, `unit_schedule.source=mass_stage_estimate`, `parkingStallEntities=3`, `parkingEntities=12`, `pilotiEntities=0`, selected strategy `ground_surface`, layout status `needs_swept_path_review`, and the PNG path is `docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-apartment-visual-stalls_1168011800104170004.png`. Count estimate is graph-backed; final turning/swept-path remains unresolved.
  - PNU `1168011800104670003`: `ground_surface`, required/provided `1/1`, `parkingStallEntities=1`, `column_clearance.status=not_applicable`, `drive_aisle_clearance.status=needs_review`, `turning_clearance.status=needs_swept_path_review`, layout status `needs_aisle_review`.
- Verification completed this session:
  - Django targeted parking tests passed:
    `design.test_maas_export.MaasLegalVariantsTest.test_parking_layout_grid_solver_prefers_adjacent_small_stalls`,
    `test_parking_layout_grid_solver_places_connected_drive_cells`,
    `test_parking_layout_candidate_places_internal_double_loaded_stalls`,
    and connector entrance tests.
  - Frontend `npm run type-check` passed.
  - Windows Chrome CDP Playwright batch passed for both parking-stall cases.
  - Visual PNG for `1168011800104170004` now shows the 3 contiguous stall lines and no piloti column helper entities. The remaining large translucent pink diagonal in some views is the pre-existing sunlight/legal envelope overlay, not parking.
- Review notes for next session:
  - Do not call this "final parking approval". It is a v1 mass-stage solver.
  - Main remaining work is replacing `site_connector_v1` with real entrance throat geometry, swept-path validation, and explicit column/core polygons. The row-frontage pass is a mass-stage v1 assumption, not a vehicle swept-path simulation.
  - Real structural column/core polygons, basement ramp geometry, mechanical equipment, accessible route, and swept-path vehicle simulation are still not implemented.
  - If the user complains about columns again, explain that columns are intentionally deferred now; implement actual `column_polygons/core_polygons` input before claiming real conflict clearance.

## 2026-06-05 Resume Result

- Recovered the interrupted MAAS `/design` work from the dirty tree.
- Verified backend `design.test_maas_export design.test_interactive_patch`: 22 tests passed before edits.
- Verified backend full `design`: 196 tests passed.
- Verified frontend `npm run type-check` and `npx vite build --mode web`: passed.
- Verified live API flow on `PNU 1168011800104170004`:
  - `site-boundary` -> `auto-constraints` -> `jobs` -> `run` -> `results`.
  - `maas_legal_envelope` returned 18 Pareto candidates.
- Fixed the tiny FAR-remainder floor issue:
  - Before: first `legal_layered_max` candidate produced a 6th floor plate of `6.44m2`.
  - After: first candidate is 5 floors, `17.5m`, FAR `136.78%`, floor plate areas `[102.93, 102.93, 74.99, 51.47, 28.96]`.
  - Rule: do not create a standalone floor plate below `min(24m2, ground_plate_area * 0.25)`.
- Added regression checks in `design.test_maas_export` so legal floor plates do not include tiny architectural remainder floors.

## Direction

- MAAS generation is legal-envelope-first.
- The old 10 mass algorithms are no longer the capacity source; they are seed/operator diversity sources after the legal layered candidate.
- `legal_layered_max` should be the primary candidate: it clips each floor plate by the legal envelope, then fills FAR/BCR as much as the constraints allow.

## 2026-06-29 Parking Mass-Stage Evidence Loop

- Added a separate parking feasibility layer:
  `parking_precheck.layout_candidate.mass_stage_parking`.
- `mass_stage_parking.status == pass` means the early massing candidate has
  enough stalls/accessibility, contiguous row or cluster, 6m aisle module,
  frontage/attached-parking relief, and entrance connection for design review.
  It is not final permit approval and does not replace vehicle swept-path,
  column/core, accessible route, or authority review.
- `legal_mesh_optimizer.py` now ranks mass-stage parking-pass candidates above
  plain review/fail candidates, while still ranking real `layout.status ==
  pass` highest.
- `render-maas-20-alt.cjs` now draws actual
  `layout_candidate.stalls[*].polygon_wgs84` as magenta stall outlines and
  labels. It also supports `REUSE_JSON=1` for fast PNG-only rerender.
- `DesignInspector.tsx` displays `mass_stage_pass` as `매스단계 가능`.
- Latest 20-alt check for PNU `1168011800104170004`, building type
  `공동주택`:
  - PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
  - `permitPass=0`, `massStagePass=1`, `parkingFail=18`,
    `uniqueShapes=19`, generation time about 124s.
  - `maas_01` is `P 5/5`, contiguous, `mass-stage pass /
    needs_drive_connectivity_review`.
  - `maas_19` is `P 6/6` but non-contiguous, so it correctly remains fail.
- Next session: improve the generator so more architectural/section-diverse
  masses remain parking-feasible. Do not solve this by hiding final review
  status or by drawing fake parking overlays.

## 2026-06-29 Continuous Parking/Design PNG Loop

- User asked to keep looping instead of stopping at one parking candidate.
- Implemented parking-preserving section variants:
  - `parking_repair_terrace_ribbon`
  - `parking_repair_sloped_roof_mass`
  - `parking_repair_diagonal_connector`
- These keep the verified repaired ground parking footprint, then vary upper
  mass/section so the PNG has more than one parking-feasible design option.
- `_operator_family()` maps these operators to the canonical MAAS section
  families, so `section_profile`, materialized source volumes, and
  `section_source_surfaces` are attached.
- `_final_design_balanced_selection()` keeps up to three distinct
  mass-stage-pass parking candidates in the 20-card review sheet.
- Latest PNU `1168011800104170004` / `공동주택` 20-alt PNG:
  - `massStagePass=3`, `permitPass=0`, `uniqueShapes=20`,
    `sectionMaterialized=9`, `surfaceCandidates=9`, generation about 146s.
  - Top three candidates are `P 5/5` and `mass-stage pass /
    needs_drive_connectivity_review`.
- Visual judgment: better loop behavior, but still not final design quality.
  The top parking-feasible options are low-FAR tower-like masses. Next loop
  should raise FAR/design quality while keeping `massStagePass >= 3`.

## 2026-06-29 Parking-Preserving FAR Loop

- Continued the PNG loop to improve FAR/capacity of the three
  parking-feasible variants.
- Current accepted implementation expands upper masses inside
  `envelope.buildable_footprint`:
  - `parking_repair_terrace_ribbon`: scale `1.55 x 1.08`
  - `parking_repair_sloped_roof_mass`: scale `1.48 x 1.04`
  - `parking_repair_diagonal_connector`: scale `1.65 x 0.98`
- Latest accepted 20-alt evidence for PNU `1168011800104170004`:
  - `massStagePass=3`
  - `parking_repair_terrace_ribbon`: FAR `106.24`, `P 5/5`
  - `parking_repair_sloped_roof_mass`: FAR `92.93`, `P 5/5`
  - `parking_repair_diagonal_connector`: FAR `92.67`, `P 5/5`
  - all still final `needs_drive_connectivity_review`.
- A broader offset-search helper was attempted but made the full
  API/Playwright loop exceed Node fetch header timeout twice. It was removed.
  Do not restore broad offset search in the request/response path; move deeper
  search to an async job or bounded benchmark first.

## 2026-06-29 MAAS Mass-Language / Parking-Feasible Review Loop

- User pointed out that ARR already has many architectural massing terms and
  the 20-alt PNG should show them, not only small stepped repair masses.
- Code review found that `parking_repair_terrace_ribbon`,
  `parking_repair_sloped_roof_mass`, and
  `parking_repair_diagonal_connector` were mapped to operator families, but
  their `maas_verb_sequence` still collapsed to `base + parking_repair_*`.
- Updated `legal_mesh_optimizer.py` so parking-feasible repair candidates now
  use explicit MAAS language:
  - `parking_repair_terrace_ribbon`: `base -> lift -> terrace_link -> shift`
  - `parking_repair_sloped_roof_mass`: `base -> sloped_roof_mass -> taper`
  - `parking_repair_diagonal_connector`: `base -> lift -> diagonal_connect -> taper`
  - `parking_repair_tapered_slab`: `base -> lift -> taper`
  - `parking_repair_split_bridge`: `base -> split -> lift -> taper`
  - `parking_repair_single_bar`: `base -> compress -> taper`
- `_operator_family()` now recognizes the additional parking-preserving
  families: `split`, `taper`, and `slender_bar`.
- `_final_design_balanced_selection()` now surfaces up to six mass-stage-pass
  parking candidates first, so the review PNG compares legal/parking feasible
  design language before showing high-FAR parking-fail candidates.
- Latest full Playwright/API PNG for PNU `1168011800104170004`:
  - PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
  - `massStagePass=6`, `uniqueShapes=20`, `sectionMaterialized=9`.
  - Top six are all `P 4/4`, `mass-stage pass /
    needs_drive_connectivity_review`.
- Visual judgment:
  - This is better for the user's stated design-review need because the top
    row now compares terrace, sloped, diagonal, taper, split, and single-bar
    language under the same parking feasibility gate.
  - It is still not final competition-grade massing. `split_bridge` and
    `single_bar` remain visually conservative because the true split/bar source
    solids are not yet as strong as the language labels. Next improvement should
    deepen source geometry/materialization for split/bridge and diagonal forms,
    not just change labels or ordering.

## 2026-06-29 Hardcoding Rejected / Grammar Frontier Finding

- User correctly rejected direct numeric geometry tuning such as `cx - width *
  0.34`. That approach is not scalable and should not be used to claim
  paper-style massing quality.
- Replaced the parking-preserving section tuple path with the existing
  data-backed grammar interpreter:
  - `_parking_preserving_section_candidates()` now calls
    `generate_grammar_variants(parking_footprint_utm)`.
  - Candidate upper masses come from `grammar/data/maas_sequences.v0.json`
    through `grammar/legal_interpreter.py`, not from per-operator `sx/sy/dx/dy`
    tuples.
  - Parking-preserving candidates are named `parking_repair_grammar_*` and keep
    their original `maas_verb_sequence` from the JSON sequence library.
- Latest PNG/JSON for PNU `1168011800104170004`, building type `공동주택`:
  - PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - `massStagePass=5`, `uniqueShapes=20`, `sectionMaterialized=9`.
  - Parking-feasible frontier:
    - `parking_repair_grammar_sloped_roof_envelope`: FAR `63.06`, `P 4/4`
    - `parking_repair_grammar_diagonal_step_connector`: FAR `54.99`, `P 4/4`
    - `parking_repair_grammar_overlap_shift_terrace`: FAR `54.20`, `P 4/4`
    - `parking_repair_grammar_terrace_ribbon_stepback`: FAR `46.23`, `P 4/4`
    - `parking_repair_shrink`: FAR `88.63`, `P 4/4`
  - High-FAR legal envelope candidates around FAR `219~249` require `7~12`
    parking spaces and fail with provided `0~4`.
- Architectural judgment:
  - The problem is not impossible in general.
  - For this specific tiny PNU + `공동주택` + surface/small attached parking
    assumption, high FAR, rich massing, and parking feasibility conflict hard.
  - To unlock richer/high-FAR design, the next real design branch must include
    basement parking, mechanical parking, a different building use/program, or
    explicit small-lot authority review. More hardcoded upper-mass tweaks will
    not solve the constraint frontier.

## 2026-06-29 Mechanical Parking Unlock / 20-Alt Evidence

- Added a separate `mechanical` parking strategy path in
  `parking_layout.py`.
  - It is conceptual only and returns
    `needs_mechanical_parking_review`, not final `pass`.
  - It exposes required authority/equipment evidence:
    mechanical equipment type, pit/lift clearance, entry queueing,
    manufacturer turning/safety clearance, and local authority acceptance.
  - It intentionally has no standard `stalls` polygons.
- Updated `_mass_stage_parking_summary()` so a mechanical candidate can keep a
  high-FAR mass alive at mass stage while marking
  `authority_review_required=True`.
- Updated `parking_strategy.py` so mechanical ranks below real surface/piloti
  stall layouts. Low-FAR candidates with visible parking lines should remain
  conventional review candidates.
- Updated `legal_mesh_optimizer.py` so:
  - `needs_mechanical_parking_review` counts as a reviewable parking status for
    candidate ordering,
  - each candidate exposes `operator_family`,
  - each candidate exposes `maas_sequence_verbs` for agent/UI explanation.
- Updated the PNG renderer so every card shows concept/family/verb evidence,
  not only geometry.

Latest verified PNG/JSON:

- PNU: `1168011800104170004`
- Building type: `공동주택`
- PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
- JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- `count=20`
- `massStagePass=17`
- `mechanical=14`
- statuses:
  - `needs_mechanical_parking_review`: 14
  - `needs_drive_connectivity_review`: 3
  - `fail`: 3
- Visible-stall candidates remain at low FAR:
  - `parking_repair_grammar_diagonal_step_connector`: FAR `54.99`, `P 4/4`
  - `parking_repair_grammar_terrace_ribbon_stepback`: FAR `46.23`, `P 4/4`
  - `parking_repair_grammar_sloped_roof_envelope`: FAR `63.06`, `P 4/4`
- High-FAR candidates survive only through conceptual mechanical review:
  `FAR 219~249`, usually `P 7/7` or `P 8/8`, mass-stage pass but not final
  parking permit pass.

Do not present this as "parking fully solved." The honest result is:

- surface/small attached parking gives a low-FAR frontier on this tiny
  `공동주택` PNU,
- mechanical parking opens a high-FAR design-review branch,
- final approval still requires authority/equipment evidence.

## 2026-06-29 Section-Synthesis Surface Loop

Purpose: make MAAS output read as architectural massing, not only a legal
stepback stack.

Current implemented state:

- `legal_mesh_optimizer.py`
  - `_final_design_balanced_selection()` keeps the 20-alt review sheet balanced:
    one legal max anchor, visible-stall review candidates, then reserved
    synthesis candidates for diagonal connector, terrace ribbon, and sloped
    roof.
  - Section synthesis is marked through `section_profile_materialized` with
    `design_synthesis=True` and `basis=maas_section_synthesis_v1`.
  - `section_source_surfaces` are generated from actual polygon exterior points,
    not bounding-box corners.
  - Surface families currently generated:
    - sloped roof polygon plane plus eave faces,
    - terrace ribbon skins/link surfaces,
    - diagonal connector fold/skin/deck surfaces.
- `docs/playwright/design-route-live-verify/render-maas-20-alt.cjs`
  - Includes section surfaces in render bounds.
  - Fades synthesis source volumes while drawing section surfaces strongly.
  - Shows `synthesis:<kind>` in each card.

Latest verified command:

```bash
node docs/playwright/design-route-live-verify/render-maas-20-alt.cjs
```

Latest verified output:

- PNU: `1168011800104170004`
- Building type: `공동주택`
- PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
- JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- `count=20`
- synthesis candidates: `10`
  - terrace ribbon `4`
  - sloped roof `3`
  - diagonal connector `3`
- parking statuses:
  - `needs_mechanical_parking_review`: `14`
  - `needs_drive_connectivity_review`: `4`
  - `fail`: `2`
- Critical geometry check:
  - all section-surface vertices were tested against each candidate's
    mass-volume union,
  - `surface_vertex_violations=0`.
- Regression tests now cover:
  - polygon-derived synthesis surfaces staying inside the mass-volume union,
  - generated synthesis candidates carrying `section_source_surfaces`,
  - mechanical parking staying review-only, not final pass.

Do not regress to bbox-corner surface generation. It leaks on slanted parcels.
Use polygon exterior points or clipped geometry for every future design surface.

## 2026-06-29 Typology-First Representative Sheet

The surface-synthesis direction was not enough. User rejected the PNG because
the masses still read as boxes with decoration. Current code now pivots the
review sheet to typology-first mass candidates.

Implemented in `legal_mesh_optimizer.py`:

- `TYPOLOGY_FIRST_FAMILIES` is the representative ordering for the 20-card
  review PNG.
- `_is_typology_first_candidate()` excludes `parking_repair_*` from design
  representative selection.
- `_upper_typology_is_viable()` rejects tiny upper footprints before they
  become pseudo-towers/connectors.
- `_is_reviewable_architectural_mass()` excludes:
  - parking repair candidates,
  - parking `fail` candidates,
  - too-thin plan candidates,
  - excessive height/min-plan-dimension candidates.
- `_final_design_balanced_selection()` now selects one reviewable candidate
  per typology family before backfilling, using `design_quality_score`,
  `diversity_score`, `maas_score`, and minimum plan dimension.
- `_should_use_floor_plate_stack()` now avoids rebuilding plan typologies into
  the same legal stack. This preserves interlock/overlap/split/courtyard/notch
  identity in `mass_volumes`.

Implemented in
`docs/playwright/design-route-live-verify/render-maas-20-alt.cjs`:

- `section_source_surfaces` are no longer included in render bounds.
- Section source surfaces and section profile overlays are not drawn as primary
  mass evidence in the 20-card sheet.
- Card metadata now emphasizes `typology:<family>`.

Latest verified command:

```bash
node docs/playwright/design-route-live-verify/render-maas-20-alt.cjs
```

Latest verified output:

- PNU: `1168011800104170004`
- Building type: `공동주택`
- PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
- JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- `count=20`
- visible families include:
  `legal_layered`, `interlock`, `overlap`, `split`, `courtyard`,
  `void_notch`, `pinch`, `terrace_link`, `sloped_roof`, `inset`,
  `legal_buildable`, and grammar variants.
- parking statuses:
  - `needs_mechanical_parking_review`: `20`
  - `fail`: `0`
- No `parking_repair_*` candidates appear in the representative PNG.

Latest focused tests:

```bash
cd /mnt/d/Data/25_ACE/ARR/backend
.venv/bin/python -m py_compile design/maas/legal_mesh_optimizer.py design/test_maas_export.py
.venv/bin/python manage.py test \
  design.test_maas_export.MaasLegalVariantsTest.test_typology_first_generator_produces_architectural_families \
  design.test_maas_export.MaasLegalVariantsTest.test_tiny_upper_mass_is_not_valid_typology \
  design.test_maas_export.MaasLegalVariantsTest.test_mechanical_parking_unlocks_high_far_mass_stage_without_final_pass \
  design.test_maas_export.MaasLegalVariantsTest.test_parking_strategy_attaches_layout_candidate_when_required_count_exists \
  -v 1
```

Judgment for next agent:

- Do not claim this is final paper/competition-grade massing.
- It is a cleaner legal-envelope-first typology review sheet.
- Next meaningful work is a typed grammar compiler and optimizer, not more
  coordinate-ratio patches. The grammar should produce source geometry that is
  checked against legal envelope, parking strategy, program/core viability, and
  rendered PNG/VWorld evidence.

2026-06-30 code review follow-up:

- Fixed two selection bugs found after review:
  - final selection no longer bypasses the typology/fail/repair filter when
    `len(selected) <= final_limit`;
  - `grammar_*` operators now map back to typology families, so grammar
    candidates are selected intentionally rather than only through backfill.
- Representative selection now prefers returning fewer reviewable candidates
  over padding the sheet with parking repair or parking-fail candidates.
- Added focused tests for grammar family mapping and under-limit fail/repair
  filtering.
- Playwright renderer retry hit a backend `HeadersTimeoutError` while waiting
  for `/design/maas/legal-variants/`. The code tests passed, but full PNG
  regeneration should be rerun after addressing endpoint runtime/timeout.

## Key Files

- `legal_envelope.py`: builds the legal envelope and per-floor `floor_plates`.
- `legal_mesh_optimizer.py`: ranks `legal_layered_max` and seed variants by FAR/BCR utilization plus diversity.
- `seed_library.py`: wraps legacy mass logic as seeds/operators.
- `interactive/`: operation schema, geometry seed mutation, and legal-repair orchestration.
- `agents/`: deterministic multi-agent review contract for Geometry/Law/Optimization/Review plus ARR A2UI message emission.
- `../services/mass_operations.py`: compatibility wrapper for the interactive MAAS orchestrator.

## Verification Notes

- Important PNU: `1168011800104170004`.
- Also checked: `1168011800104670003`, `1129010100103300000`, `1168010100106770000`, `1165010800113170029`.
- Django `design` tests passed: 196 tests on 2026-06-05.
- `design.test_maas_export` passed: 15 tests on 2026-06-05.
- Playwright/API operation request passed against backend `18001`.
- Frontend `npx vite build --mode web` passed on 2026-06-05.
- Official A2UI reference repo cloned to `/mnt/d/Data/25_ACE/clone/A2UI` at `e05dd969`.

## Current Limits

- Do not describe this logic as complete or perfect. It is a verified prototype path for legal-envelope-first mass generation.
- The UI has coarse `층+`, `층-`, `폭+`, `폭-`, and edge-offset operation buttons. Cesium mass entities now carry interaction metadata, but true click-drag face editing is still the next UI controller step.
- `buildable_footprint_from_setback_geometries()` uses line half-plane clipping with the site representative point. This worked in tested PNUs, but concave parcels and complex multi-road parcels need stronger edge-normal metadata or direct trusted buildable polygons.
- The tiny FAR-remainder floor issue has a first pass threshold now. It still needs architectural review for program-specific minimum plates, especially by building type and core feasibility.
- Headless Playwright verifies the React/API flow, not final Cesium/WebGL pixels in this environment.
- A candidate should be treated as reviewable only after API metrics, floor plates, legal datum/envelope basis, and real-browser VWorld placement all agree.

## 2026-06-30 MAAS PNG Loop Update

User asked to stop judging abstractly and keep looping through PNG evidence until the massing actually reads as architectural alternatives.

What changed in this loop:

- `legal_mesh_optimizer.py`
  - `grammar_sunlight_multi_step` now uses the legal floor-plate stack instead of being rejected as `not_enough_floor_bands_for_multi_step`.
  - Final review selection downranks pure capacity boxes (`bcr_fill`, `legal_buildable`) for the 20-card design evidence sheet.
  - Section families are preserved in default 20-card output: `diagonal_connect`, `terrace_link`, `sloped_roof`, `stepback_tower`.
  - Grammar candidates and visible multi-volume candidates are preferred over single-box morphology candidates within the same family.
  - Upper/lower mass candidates now create interpolated legal-inside volumes instead of only two crude slabs. This is geometry interpolation from lower footprint to upper footprint, not fixed-coordinate hardcoding.

- `render-maas-20-alt.cjs`
  - Sends `site_polygon`, `sunlight_envelope`, and `setback_geometries` to the backend so the PNG loop uses the same legal context as the design route.
  - Supports `PREFERRED_OPERATOR=...` for focused PNG/API checks.

Latest verified command:

```bash
cd /mnt/d/Data/25_ACE
MAX_VARIANTS=20 node docs/playwright/design-route-live-verify/render-maas-20-alt.cjs
```

Latest output:

- PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
- JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- PNU: `1168011800104170004`
- Building type: `공동주택`
- Count: `20`
- Notable selected candidates:
  - `legal_layered_max`: 5-volume legal envelope anchor.
  - `grammar_interlock_step_taper`: 5-volume grammar mass.
  - `grammar_split_lift_stepback`: 5-volume split/step grammar mass.
  - `grammar_sunlight_multi_step_layered`: 4-volume north daylight/sunlight step mass.
  - `grammar_terrace_ribbon_stepback`: 5-volume terrace ribbon synthesis.
  - `diagonal_connect_step_x`: 6-volume diagonal connector synthesis.
  - `grammar_sloped_roof_envelope` and `sloped_roof_mass`: 5-volume sloped-roof synthesis.

Latest focused tests passed:

```bash
cd /mnt/d/Data/25_ACE/ARR/backend
.venv/bin/python -m py_compile design/maas/legal_mesh_optimizer.py design/test_maas_export.py
.venv/bin/python manage.py test \
  design.test_maas_export.MaasLegalVariantsTest.test_legal_layered_visual_volumes_preserve_sunlight_steps \
  design.test_maas_export.MaasLegalVariantsTest.test_grammar_operator_family_maps_to_typology_family \
  design.test_maas_export.MaasLegalVariantsTest.test_typology_selection_filters_fail_and_repair_even_when_under_limit \
  -v 1
```

Current honest judgment:

- Better than the previous PNGs: the sheet no longer looks like only identical extruded boxes, and section/grammar candidates survive default selection.
- Still not final competition-grade architecture. Remaining issue is that some plan families (`overlap`, `void_notch`, `inset`, `slender_bar`) are still single-volume plan operations. Next real improvement is a typed grammar compiler/source mesh path for those families, plus legal envelope and parking checks after source mesh generation.
- Do not fake sloped/diagonal faces outside legal envelope. The current conservative method keeps volumes clipped inside the legal footprint/envelope; future work should add true mesh faces with explicit legal validation.

2026-06-30 follow-up after user noticed too many ordinary masses:

- Reduced plain single-volume review candidates from 9/20 to 2/20 by:
  - capping plain review masses in `_final_design_balanced_selection`;
  - widening small-lot grammar parameters for `grammar_courtyard_lift_taper`
    and `grammar_podium_tower_offset` so they survive upper-mass viability;
  - supplementing final review candidates from `legal_candidate_pool` with
    law-passing grammar/section candidates before final selection;
  - attaching parking precheck to those supplemental candidates so PNG cards
    do not show `P -/- no parking`.
- Latest PNG/JSON still use:
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
- Latest selected set is 20/20 candidates, with 2 plain single-volume masses
  by metric. One grammar candidate (`grammar_cave_inset_puncture`) is still
  visually plain-ish because it is currently a one-volume void/cave operation.
  Next improvement should make cave/notch/inset produce real section/source
  volumes rather than just a plan cut.

## 2026-06-30 ARR-Native Source Geometry Grammar V1

- Implemented the first ARR-native source geometry compiler in
  `design/maas/source_geometry/`.
- `grammar/legal_interpreter.py` now compiles MAAS `VerbSequence` into
  `SourceMass` before falling back to the older Shapely-only interpreter.
- `MorphologyVariant` now carries `source_geometry_status`,
  `source_verb_trace`, `source_signature`, and `source_volumes`.
- `legal_mesh_optimizer.py` preserves those fields into candidate properties
  and `properties.maas_model`, so agents/UI can explain which grammar verbs
  generated the mass.
- Runtime d4descent import is disabled by default. It remains a
  research/evidence reference; the legal endpoint must not import torch during
  normal candidate evaluation.
- Parking repair was guarded for performance:
  - PNU-less diversity tests no longer run parking repair.
  - PNU/explicit repair runs inspect a capped set of repair footprints.
- Verification:
  - `py_compile` passed for source geometry, interpreter, optimizer, and tests.
  - Focused Django tests passed:
    `test_grammar_sequences_generate_composite_variants`,
    `test_variant_selection_preserves_capacity_and_shape_diversity`,
    `test_d4descent_clone_backend_is_connected_as_research_optimizer`.
  - Latest PNG/JSON regenerated after backend restart:
    `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`,
    `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`.
  - Latest JSON summary for PNU `1168011800104170004`:
    20/20 candidates, 17 with source geometry evidence, 2 plain non-grammar
    single-volume candidates, elapsed about 7.1s.
- Honest visual judgment:
  - Better than the prior fake/label-only grammar state.
  - Still not competition-grade. Several families remain similar stacked
    grammar expressions because V1 produces legal-safe polygon/upper-mass
    approximations, not a full CSG mesh/rewrite optimizer.
  - Next real step is Source Geometry V2: source-signature diversity selection
    and rewrite/proposal generation before selection.

## 2026-06-30 Source Signature Diversity Selection

- Implemented source-signature-aware candidate distance in
  `legal_mesh_optimizer.py`.
- `_feature_distance()` now includes:
  - source geometry family distance;
  - source verb profile distance;
  - source volume-count distance;
  - upper-to-ground ratio distance;
  - source area-profile distance.
- Near-duplicate filtering now treats same source family + same source area
  profile + high footprint IoU as duplicate.
- Final 20-card balanced selection now caps repeated non-legal source families
  to at most 2 candidates by default.
- Added regression test:
  `test_source_signature_contributes_to_candidate_distance`.
- Verification:
  - `py_compile` passed for optimizer and tests.
  - Focused tests passed:
    `test_source_signature_contributes_to_candidate_distance`,
    `test_variant_selection_preserves_capacity_and_shape_diversity`.
  - Playwright PNG loop regenerated:
    `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`.
  - Latest PNU `1168011800104170004` summary:
    20 candidates, 17 source-geometry candidates, 2 plain candidates,
    source families capped to max 2 each, elapsed about 8.4s.
- Current limitation:
  - This improves selection and explanation, but it does not yet create new
    grammar proposals. True next step remains rewrite/proposal generation from
    source geometry, then PNG-loop validation.

## 2026-06-30 MassDSL Multi-Agent Loop V1

- Implemented the first deterministic MassDSL agent loop in
  `design/maas/agents/`.
- New backend agent folders:
  - `massdsl_agent/`: emits `arr.maas.massdsl.proposal.v1` from selected
    candidate `maas_verb_sequence`, `source_signature`, legal limits, and
    operation context.
  - `grammar_critic_agent/`: emits `arr.maas.grammar_review.v1` with grammar
    family, verbs, section-language flag, parking evidence flag, legal metrics,
    and issues.
- Canonical flow is now:
  `design_orchestrator -> law_graph_agent -> parking_agent -> massdsl_agent -> maas_geometry_agent -> grammar_critic_agent -> review_agent`.
- `/design/maas/legal-variants/` attaches:
  - response-level `agent_reviews`, `agent_trace`, `a2ui_messages`,
    `massdsl_proposals`, `grammar_review`, `grammar_reviews`;
  - candidate-level `properties.massdsl_proposal` and
    `properties.grammar_review`;
  - mirrored evidence inside `properties.maas_model` when that object exists.
- Frontend updates:
  - `DefaultAgentFlowPanel`, `DirectAgentChatPanel`,
    `ag-light-flow/agents/*`, and `ag-light-collaboration.ts` now expose
    MassDSL and grammar critic nodes.
  - `JSON_MODULES/teams/041_MAAS_Legal_Design_Team.json` now matches the six
    agent sequence and should remain the UI/team metadata source.
- Latest verification:
  - Backend py_compile passed for new agents, registry, A2UI surface,
    optimizer, and tests.
  - Focused Django tests passed:
    `test_maas_agent_registry_exposes_flow_cards`,
    `test_endpoint_returns_feature_collection`,
    `test_massdsl_agent_contract_compiles_from_candidate_evidence`,
    `test_grammar_sequences_generate_composite_variants`,
    `test_source_signature_contributes_to_candidate_distance`.
  - Frontend `npm run type-check` passed.
  - `node docs/playwright/design-route-live-verify/render-maas-20-alt.cjs`
    generated:
    `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
    and `.json`.
  - Latest 20-card JSON summary for PNU `1168011800104170004`:
    20 candidates, 20 MassDSL proposals, 20 grammar reviews, six-agent
    `agent_reviews`, and family repetition capped at max 2.
  - Visual PNG is better than the earlier repeated step-only state:
    interlock, split, courtyard, branch, terrace ribbon, diagonal connector,
    sloped roof, bar/notch, and sunlight-step families are present. It is still
    deterministic grammar massing, not yet a full LLM/freeform competition
    design generator.
  - AG-light Playwright verifier passed after Vite/Django restart:
    screenshot
    `docs/playwright/design-route-live-verify/ag-light/ag-light-current-1782807801354.png`,
    JSON
    `docs/playwright/design-route-live-verify/ag-light/ag-light-current-result.json`.
- Important Playwright caveat:
  - `/design` is proxied to Django unless navigation requests include an HTML
    Accept header. The verifier now sets that header only for navigation via
    `page.route`; do not use global `page.setExtraHTTPHeaders({Accept: ...})`
    because it makes `/@vite/client` or API fetches fail.

## 2026-06-30 Section Diversity Harness Update

- Do not add arbitrary mass-shaping constants as the design source. Numeric
  clamps are acceptable only as safety bounds; design intent must be derived
  from `maas_verb_sequence` parameters and clipped inside legal floor plates.
- `legal_mesh_optimizer.py` now derives section profiles from MAAS verbs:
  `split`, `overlap`, `interlock`, `branch`, `pinch`, `taper`,
  `notch/cave/puncture`, and `grade`, plus the existing
  `diagonal_connect`, `terrace_link`, and `sloped_roof_mass`.
- `_apply_variant_verb_sequence()` must re-run section synthesis after a grammar
  sequence is attached. A stale Django runserver can hide this change; restart
  backend before PNG validation.
- Fast validation loop:

```bash
node docs/playwright/design-route-live-verify/render-maas-20-alt.cjs
node docs/playwright/design-route-live-verify/verify-maas-20-alt-json.cjs
```

- Latest PNU `1168011800104170004` result:
  - PNG: `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`
  - JSON: `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`
  - `20/20` legal pass, `15` unique shapes, `14` unique families, `10` unique
    section profiles, `17/20` materialized section-source candidates.
- Current limitation: this proves legal-envelope mass diversity, not final
  parking approval. Latest fast run still has `parkingPass=0`, so parking repair
  remains a separate gate.

## 2026-07-01 Source Geometry V2 / Agent Evidence Loop

- Goal mode was attached for this continuation loop so Codex keeps checking the
  V2 integration target rather than stopping at a partial code change.
- Source Geometry V2 now extends the ARR-native grammar compiler:
  - `SourceSurface` added to `source_geometry/ir.py`;
  - compiler creates roof/facade source surfaces from each `SourceVolume`;
  - `SourceMass.signature()` includes `surface_count` and `surface_roles`;
  - `MorphologyVariant` carries `source_surfaces`.
- `legal_mesh_optimizer.py` now preserves `source_surfaces` into candidate
  properties and `maas_model`; source-profile distance includes
  `surface_count`; final selection preserves at least one section connector
  candidate even in small `max_variants` sets.
- Agent evidence now exposes the V2 contract:
  - MassDSL proposal includes `source_refs.source_surface_count`;
  - grammar critic includes `surface_count` and
    `has_source_surface_contract`;
  - AG-light collaboration trace shows the source surface count and grammar
    source-surface contract status.
- Latest JSON regenerated through the live backend:
  `docs/playwright/design-route-live-verify/maas-20-alt-latest.json`.
  Latest JSON evidence: `20` candidates, `17` source-geometry candidates,
  `17` candidates with source surface signatures, `20` MassDSL proposals,
  `20` grammar reviews, and `6` response-level agent reviews.
- Verified:
  - focused Django tests for grammar variants, source signature distance,
    variant selection, MassDSL/grammar contract, endpoint response, and agent
    registry;
  - frontend `npm run type-check`;
  - mass JSON gate, parking JSON gate, PNG freshness/nonblank gate, and
    workspace quick gate.
- Harness design status:
  - This is now a Mass/Agent/PNG regression harness, not a permit-final
    approval harness.
  - `verify-maas-20-alt-json.cjs` gates candidate count, legal envelope,
    diversity, materialized section profiles, and Source Geometry V2 evidence
    through source signature, MassDSL proposal, and grammar critic fields.
  - `verify-maas-parking-json.cjs` gates mass-stage parking count/formula
    evidence only; `permitParkingPass=0` remains expected and honest.
  - `verify-maas-png.py` gates the PNG artifact itself: expected dimensions,
    freshness against JSON, nonblank pixels, and visible mass/site color
    evidence.
- Important renderer caveat:
  - In this WSL session, Playwright screenshot capture times out even for a
    trivial page. `render-maas-20-alt.cjs` now has
    `SCREENSHOT_TIMEOUT_MS`; if Chromium capture fails, it invokes the Pillow
    fallback automatically instead of leaving a stale PNG.
  - Added browserless PNG fallback
    `docs/playwright/design-route-live-verify/render_maas_20_alt_png.py`.
    It renders the latest JSON directly with Pillow when Playwright cannot
    produce a screenshot.
  - Latest PNG regenerated:
    `docs/playwright/design-route-live-verify/maas-20-alt-latest.png`,
    2026-07-01 11:40 KST, `2200x1400`, pixel sanity
    `unique_colors=2086`, `non_bg=2590525`, `orange_pixels=65352`,
    `green_pixels=17526`. Visual inspection shows all 20 alternatives with
    mass volumes, site outlines, parking marks, and source-surface badges.
- Next meaningful work:
  1. make cave/notch/inset/branch/split V2 surfaces more architecturally
     legible, not merely contract-rich;
  2. keep parking language honest: current result is mass-stage parking, not
     permit-final parking.
