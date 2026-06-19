# 25_ACE AI Session Memory

Read this folder before touching the legal-design visualization work.

## Read Order

1. `PROJECT_MAP.md` - three connected projects and ownership.
2. `DESIGN_FLOW.md` - actual `/design` data path.
3. `FULL_REVIEW_2026-05-18.md` - current blunt review verdict, verified gates, and remaining gaps.
4. `LEGAL_COVERAGE.md` - what is implemented vs missing.
5. `VERIFY.md` - CLI and browser verification steps.
6. `OPENCODE.md` - how OpenCode was used in this session.
7. `REPO_CLEANUP.md` - dirty worktree triage and safe cleanup policy.
8. `../../ARR/backend/design/maas/HANDOFF.md` - current MAAS legal-envelope mass generation state.
9. `MAAS_RESEARCH.md` - research-backed direction for making MAAS robust.
10. `MULTI_AGENT_LEGAL_DESIGN_WORKFLOW.md` - AutoGen/A2A-style legal-to-design collaboration target, agent roles, graph boundaries, and parking-law priority.
11. `MAAS_EVIDENCE_BUNDLE.md` - proposed canonical evidence JSON for MAAS/AG-light/Graph DB review.
12. `MAAS_TERM_ONTOLOGY.md` - architecture terms mapped to MAAS grammar verbs/operators.
13. `MAAS_FINE_TUNING_PLAN.md` - fine-tuning plan: intent-to-sequence/review model, not raw mesh generation.
14. `maas-aesthetic-texturing/` - research/code/method memory for multi-view facade generation and texture projection.

## Current Priority

The current verified local target is `http://127.0.0.1:5174/design`, not `/land`.

The key correctness gate is datum/elevation first:

- `datum_result` must exist.
- `datum_result.elevation_source` must be `ngii_local_dem` for the covered Seoul test cases.
- If datum falls back to `open_meteo`, do not trust sunlight/daylight height envelopes.

## Current MAAS Reality Check

Do not call the MAAS massing logic complete or legally perfect.

AG-light is the current multi-agent integration target, not the full `AG/` tree.
Use `AG-light/server/.venv` for the Python server because the base Python
environment does not include `mcp`. The verified local server command is:

```bash
cd /mnt/d/Data/25_ACE/AG-light/server
ARR_BACKEND_URL=http://127.0.0.1:18000 .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8200
```

Expected: `http://127.0.0.1:8200/health` reports MCP mounted at `/mcp/mcp`,
and MCP `list_tools` includes `arr_maas_evidence` and `arr_maas_review`.

Professor discussion update on 2026-06-11:

- The target is an AutoGen/A2A-style collaborative workflow, not a single
  agent/tool call.
- AG-light agents should call ARR deterministic tools and debate/review evidence.
- The agent-to-agent collaboration must be visible in the `/design` frontend,
  using the `AG-frontend/src` agent-flow/playground pattern as reference:
  active agent graph, handoff/tool-call timeline, per-agent message filtering,
  decisions, evidence refs, and an AG-light offline state.
- Graph DB should store law basis, durable evidence/provenance, final/important
  decisions, candidate lineage, rejected constraints, and requested repairs.
- Graph DB should not store every raw agent-to-agent chat message; raw dialogue
  belongs in MessageBus/SharedMemory/log artifacts unless summarized.
- Parking law is the first sequential implementation gate: load/verify
  `ARR/backend/law/data/api/주차장법_법률.json`,
  `주차장법_시행령.json`, and `주차장법_시행규칙.json` into Neo4j first;
  then add relationship/domain/search coverage; then connect deterministic ARR
  parking validators and the AG-light `parking_agent`. Missing parking evidence
  keeps MAAS status as `needs_evidence`.
- Parking law first pass is now loaded in Neo4j:
  `주차장법(법률)`, `주차장법(시행령)`, `주차장법(시행규칙)`.
  Verified semantic chain:
  `법 제19조 -> 시행령 제6조 -> 시행령 별표1`
  and `시행령 제6조 -> 시행규칙 제11조`.
  Domain `parking_regulation` exists with 198 linked nodes.
  Remaining blocker: `[별표 1]` has an `APPENDIX` node but the actual table rows
  still need structured parsing before deterministic parking-count validation.
- Accessible parking is now part of the same graph track. Loaded
  `장애인ㆍ노인ㆍ임산부 등의 편의증진 보장에 관한 법률`
  법률/시행령/시행규칙 into Neo4j, added `accessible_parking_regulation`,
  and verified `32/32` parking graph checks. Statutory disabled stall minimum is
  stored as `3.3m x 5.0m` from `주차장법 시행규칙 제3조제1항제2호`; do not
  replace it with `3.5m x 5.0m` unless a newer official source is loaded. Treat
  `3.5m` as a possible design/BF/project recommendation layer, separate from the
  legal minimum.
- Parking appendix structured seed is now loaded:
  `주차장법 시행령 [별표 1]` has 11 `ParkingRequirementRule` rows, and
  편의증진법 시행규칙 `[별표 1]` has 2 `AccessibleParkingFacilityRule` rows.
  Official PDFs are stored under `docs/legal-sources/`. The rows are graph-ready
  structured seed data backed by the PDFs; future OCR/HWP parsing should confirm
  them before marking them fully machine-parsed.

Parking grid solver / VWorld PNG update on 2026-06-15:

- The ARR mass-stage parking solver now includes a first grid solver:
  selected stall candidates (`x`), adjacent drive aisle cells (`y`), drive cell
  component connectivity, and entrance edge connection metadata.
- The small-stall selector now prefers same-row contiguous stalls before the
  looser compact graph fallback. Do not regress this to "nearby but separated"
  stall selection. JSON must show `adjacency.status=row_contiguous`,
  `gap_pairs=0`, and `max_gap_m=0` when a small same-row arrangement is possible.
- `ARR/backend/design/views.py` chooses `best_geojson` with a parking-aware score
  when parking data exists: nonzero required/provided stalls, layout pass, required
  count satisfaction, contiguous small rows, verified entrance, and frontage count
  are preferred before original order.
- It is not a full CPLEX/OR-Tools global MIP and not a BIM parking model.
- Road frontage geometry is used when available. `sharedEdge` can arrive as a
  raw coordinate array from VWorld; this is converted to a LineString and then
  from WGS84 to UTM before distance checks.
- Backend fallback now infers `parking_road_context` from
  `land.services.road_frontage.fetch_neighbor_roads(site_polygon)` when the
  frontend job options do not carry it. This backend fallback is the reliable
  path; frontend injection is only auxiliary.
- Latest Windows Chrome CDP / VWorld PNG batch:
  `docs/playwright/design-route-live-verify/windows-cdp-vworld-pnu-batch.cjs`
  with cases in
  `docs/playwright/design-route-live-verify/parking-stall-cases.json`.
- Latest frontend visual patch for the user complaint "parking lines disappeared /
  columns are ambiguous":
  `ARR/frontend/src/design/lib/cesium/mass-entities.ts` no longer calls the
  piloti support/label renderer, so Cesium `pilotiEntities` must be `0` until
  explicit structural column/core geometry exists. Exact parking stall raised
  lines are now drawn at `groundH + 1.15m` with thicker pink polylines so they
  remain visible through the translucent mass.
- `ARR/frontend/src/design/components/DesignInspector.tsx` intentionally hides
  the column/core row for now. Backend `column_clearance` may still exist as
  deferred evidence, but the UI should not imply column clearance was checked.
- Apartment/common-housing (`공동주택`) now has a mass-stage housing parking
  estimator. `ARR/backend/design/maas/parking_requirements.py` computes
  `computed_estimate` using `주택건설기준 등에 관한 규정 제27조` plus Seoul
  ordinance row 5: special-city area ratios and Seoul household minimums.
  `ARR/backend/design/maas/legal_mesh_optimizer.py` supplies a
  `mass_stage_estimate` unit schedule from floor plates, or from
  `num_floors * footprint_area` when floor plates are absent. This is better
  than the old `unresolved_visual_layout_only`, but still not final approval
  until real household/exclusive-area schedules are provided.
- Neo4j is now verified live for parking law again. From WSL use
  `NEO4J_URI=bolt://172.27.80.1:7687` and `NEO4J_PASSWORD=11111111`.
  `verify_parking_law_graph.py` passed `49/49`; `check_parking_counts.py`
  passed `23/23`. The live `/design` backend was restarted with these env vars,
  and the apartment result source now reports
  `source_ordinance=seoul_parking_ordinance`,
  `source_appendix=서울특별시 주차장 설치 및 관리 조례::별표2`.
- Latest zoom PNGs:
  `docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-neighborhood-stalls_1168011800104170004.png`
  and
  `docs/playwright/design-route-live-verify/pnu-batch/zoom_02_gangnam-dogok-neighborhood-stalls_1168011800104670003.png`.
- Latest results:
  - PNU `1168011800104170004`: `piloti_ground`, required/provided `3/3`,
    `parkingStallEntities=3`, `pilotiEntities=0`, `grid_connected_90`,
    `adjacency.status=row_contiguous`, `touching_pairs=2`, `gap_pairs=0`,
    `max_gap_m=0`, `drive_aisle_clearance.status=pass`,
    `drive_aisle_clearance.provided_width_m=6`,
    `turning_clearance.status=v1_pass`,
    `turning_clearance.method=stall_frontage_and_entrance_connector_v1`,
    `turning_clearance.frontage_connected_stalls=1/3`,
    `turning_clearance.contiguous_row_frontage_relief.available=true`,
    `column_clearance.status=deferred_structural_review` in backend evidence
    only; UI column/core display and piloti helper columns are intentionally
    hidden for now,
    `grid_solver.entrance_connection_type=site_connector_v1`,
    `grid_solver.entrance_verified=true`,
    `grid_solver.entrance_connector_length_m=8`,
    `grid_solver.entrance_connector_width_m=3`,
    `grid_solver.entrance_connector_polygon_wgs84` present,
    layout status `pass`.
  - PNU `1168011800104170004` with building type `공동주택`: housing parking
    requirement now computes as `required_count.status=computed_estimate`,
    `required_spaces=3`, `raw_spaces=2.4`, `unit_schedule.source=mass_stage_estimate`.
    Neo4j-selected rule is `seoul_parking_appendix2_row_05` overriding
    `parking_appendix1_row_05`.
    Current selected layout renders `parkingStallEntities=3`, `parkingEntities=12`,
    `pilotiEntities=0`, strategy `ground_surface`, layout status
    `needs_swept_path_review`. The count estimate is attached, but turning/swept
    path is not final.
  - PNU `1168011800104670003`: `ground_surface`, required/provided `1/1`,
    `parkingStallEntities=1`, `adjacency.status=single_or_none`,
    `column_clearance.status=not_applicable`,
    `drive_aisle_clearance.status=needs_review`,
    `turning_clearance.status=needs_swept_path_review`,
    layout status `needs_aisle_review`.
- Interpretation: both test PNUs render actual parking stall polygons in VWorld
  PNGs. They must not be described as final parking approvals. The first now has
  same-row contiguous stalls plus a 6m aisle check, intentionally hidden
  column/core visuals, and a v1 3m-wide straight site connector to road frontage.
  The connector is rendered in Cesium as a low-alpha cyan helper corridor/centerline.
  The first is now a mass-stage parking `pass` because row-contiguous grid stalls
  with one generated 6m drive cell per stall are accepted by
  `contiguous_row_frontage_relief`; it is still not final authority approval or a
  real vehicle swept-path simulation. The second is a one-stall
  single-row case and still needs aisle/road-as-aisle review.

Parking loop update on 2026-06-16:

- User asked to keep looping until parking is visually and legally convincing
  for apartment/common-housing PNU `1168011800104170004`.
- Verified current law basis against official law.go.kr pages:
  `주차장법 시행규칙 제3조` has ordinary parallel stall `2.0m x 6.0m`,
  residential undivided-road parallel stall `2.0m x 5.0m`, ordinary non-parallel
  stall `2.5m x 5.0m`, and continuous stall total-width/length multiplication.
  `제11조제5항` has small attached self-parking rules: 8 spaces or fewer, aisle
  widths by parking form, road-as-aisle exceptions, 5-or-fewer perpendicular
  road-as-aisle on separated 12m+ road subject to use/no-obstruction review, and
  tandem depth up to two stalls for 5 spaces or fewer.
- Implemented in `ARR/backend/design/maas/parking_layout.py`:
  exhaustive small-grid combination selector, cluster/tandem adjacency metrics,
  road-as-aisle wide-road option when sidewalk separation is unknown but requires
  authority/site evidence, parallel stall dimensions, and a residential 5m
  parallel authority-review candidate.
- Implemented in `ARR/frontend/src/design/lib/cesium/mass-entities.ts`:
  exact stalls now get raised pink lines plus small stall labels so PNG review
  can see whether a line exists.
- Added Playwright debug fields in
  `docs/playwright/design-route-live-verify/windows-cdp-vworld-pnu-batch.cjs`:
  `parkingPrecheckSummaries` and `selectedMassFeature`.
- Current result after multiple Playwright loops:
  `docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-apartment-visual-stalls_1168011800104170004.png`
  shows much more visible pink parking lines and labels, but the selected layout
  is still `strategy=ground_surface`, `required/provided=3/3`,
  `parkingStallEntities=3`, `pilotiEntities=0`,
  `layout_candidate.status=needs_swept_path_review`.
- Direct backend strategy checks for this exact selected mass show that the open
  ground-surface parking envelope can only place 2 fully valid road-as-aisle

Purpose-aligned parking/massing correction on 2026-06-16:

- User corrected the direction: `/design` is MAAS legal/parking-aware mass
  exploration, not a final permit/BIM parking approval system. Do not over-rotate
  into idealized authority/column/swept-path work before preserving useful mass
  candidates.
- Fixed `ARR/backend/design/maas/legal_mesh_optimizer.py` so parking review scans
  a broader legal MAAS candidate pool before the UI/result max-variant cut. This
  prevents `max_variants=1` from keeping only `legal_layered_max`, failing
  parking, and then selecting an over-shrunk `parking_repair_shrink` fallback.
- Parking repair candidates remain available, but are ranked as a fallback behind
  original legal MAAS candidates that already satisfy parking. Pure shrink repair
  now has a stronger score penalty than ground-void repair.
- Latest verified target PNU `1168011800104170004`:
  selected `mass_shape=notch_south_west`, `maas_concept=코너/오픈코트`,
  `height=8.4m`, `num_floors=3`, `footprint_area=97.82m2`,
  `floor_area=293.46m2`, `bcr=37.04`, `far=111.11`, `maas_score=0.426`,
  `parking_repair=None`.
- Latest selected parking layout for that PNU:
  `strategy=piloti_ground`, `placement_mode=grid_connected_90`,
  `status=pass`, `required/provided=3/3`, `unmet_spaces=0`,
  `adjacency.status=row_contiguous`, `touching_pairs=2`, `gap_pairs=0`,
  `row_groups=1`, `connected_components=1`, `contiguous_ok=true`.
- Frontend/visual state:
  `parkingEntities=15`, `parkingStallEntities=6` because each of 3 stalls has
  outline + label entities, `pilotiEntities=0` because structural piloti columns
  remain intentionally hidden/deferred. PNG pixel check found `pink_pixels=18617`.
- Latest PNG:
  `docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-piloti_1168011800104170004.png`.
- Latest JSON:
  `docs/playwright/design-route-live-verify/pnu-batch/01_gangnam-small-piloti_1168011800104170004.json`.
- Verification passed:
  `cd ARR/backend && .venv/bin/python manage.py test design.test_maas_export -v 1`
  passed 51 tests, and `cd ARR/frontend && npm run type-check` passed.
- Windows Playwright batch status:
  first two small PNU cases passed (`1168011800104170004` piloti, and
  `1168011800104670003` ground surface). Two larger default batch cases still
  fail visual parking checks with `strategy=missing`; treat those as the next
  separate work item, not as a regression in the small-lot parking fix.

PNU/API-key and site-containment correction on 2026-06-16:

- User correctly rejected a screenshot where parking appeared visible but the
  parcel/PNU context was suspect. Do not accept a PNG as valid just because
  pink parking lines render. The verification gate must prove that requested
  PNU, returned boundary PNU, selected mass geometry, and parking stall points
  are spatially aligned.
- `/land/map-config/` now returns HTTP 503 with
  `{"configured": false, "error": "VWORLD_API_KEY is not configured"}` when
  `VWORLD_API_KEY` is absent. The VWorld hook treats a missing/empty key as a
  hard error instead of loading VWorld with an empty key and later showing
  misleading "API key lookup" failures.
- `/design/site-boundary/` and frontend geometry helpers no longer blindly use
  `MultiPolygon[0]`. Backend and frontend now select the largest polygon part
  for parcel/site display, camera fit, candidate filtering, Cesium mass render,
  design-list thumbnails, floor-plan previews, and reverse-geocoded parcel
  geometry. This avoids using a small/irrelevant split parcel part as the active
  design site.
- `docs/playwright/design-route-live-verify/windows-cdp-vworld-pnu-batch.cjs`
  now records `siteContainment`: requested PNU, boundary PNU, site area, mass
  outside point count, and parking outside point count. A case fails if mass or
  parking points fall outside the requested PNU boundary.
- Verified live local API:
  `/land/map-config/` returns `configured=true` with an API key present, and
  `/design/site-boundary/` for `1168011800104170004` returns `area_m2=264.13`.
- Latest Playwright run with `parking-stall-cases.json`:
  `1168011800104170004` passed with `boundaryPnu=1168011800104170004`,
  `siteAreaM2=264.13`, mass `outside_points=0`, parking `outside_points=0`,
  `strategy=piloti_ground`, `required/provided=2/2`.
  `1168011800104670003` passed with `boundaryPnu=1168011800104670003`,
  `siteAreaM2=437.85`, mass `outside_points=0`, parking `outside_points=0`,
  `strategy=ground_surface`, `required/provided=2/2`.
- Latest PNGs:
  `docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-neighborhood-stalls_1168011800104170004.png`
  and
  `docs/playwright/design-route-live-verify/pnu-batch/zoom_02_gangnam-dogok-neighborhood-stalls_1168011800104670003.png`.
  stalls even after trying ordinary parallel and residential 5m parallel. Other
  strategies (`piloti_ground`, `basement`, `semi_basement`, `mechanical`, `mixed`)
  place 0 conventional stalls because this selected footprint is too narrow for
  the current deterministic module solver.
- Do not mark this apartment/common-housing case as final parking pass yet. The
  next real fix is parking-aware mass repair or generation: shrink/move/split the
  selected footprint or generate a different candidate so 3 legal stalls plus
  aisle/road-as-aisle access fit without overlap. Do not simply relabel the
  current `needs_swept_path_review` as pass.

Parking-aware repair update on 2026-06-16:

- Implemented parking-aware repair in
  `ARR/backend/design/maas/legal_mesh_optimizer.py`.
  After normal MAAS candidate selection and parking requirement attachment, a
  failing parking candidate now gets an additional
  `mass_shape=parking_repair_shrink` candidate. The repair searches conservative
  footprint scale/translation combinations inside the site, reattaches graph
  parking requirements, then lets `_parking_priority_key` select the candidate
  with actual parking pass.
- Latest Playwright loop for PNU `1168011800104170004`, building type
  `공동주택`, selected:
  `mass_shape=parking_repair_shrink`, `variant_id=maas_01`,
  `strategy=ground_surface`, `layout_candidate.status=pass`,
  `placement_mode=road_as_aisle_tandem`, `required/provided=3/3`,
  `parkingStallEntities=3`, `parkingEntities=9`, `pilotiEntities=0`.
- The selected parking layout has `adjacency.status=row_contiguous`,
  `touching_pairs=2`, `row_groups=1`, `connected_components=1`,
  `gap_pairs=0`, `max_gap_m=0`, `row_contiguous_ok=true`,
  `contiguous_ok=true`. This addresses the user complaint that parking stalls
  were separated or invisible.
- Final count still uses the graph-backed common-housing estimator:
  `selected_rule_id=seoul_parking_appendix2_row_05`,
  `base_rule_id=parking_appendix1_row_05`, `required_spaces=3`, `raw_spaces=3`,
  `unit_schedule.source=mass_stage_estimate`. This is not final permit-grade
  household evidence until actual unit/exclusive-area schedules are supplied.
- The pass is a mass-stage road-as-aisle/tandem v1 pass:
  `turning_clearance.status=v1_pass`,
  `turning_clearance.method=road_as_aisle_exception_v1`,
  `authority_review=true`. Do not describe it as a real swept-path simulation or
  final authority approval.
- Latest PNG:
  `docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-apartment-visual-stalls_1168011800104170004.png`.

Authority-review automation update on 2026-06-16:

- The prior caveat is now handled as structured data instead of only prose.
  `ARR/backend/design/maas/parking_layout.py` attaches
  `authority_review_check` to road-as-aisle layouts and mirrors it under
  `turning_clearance.authority_review_check`.
- For the current apartment PNU `1168011800104170004`, latest JSON shows:
  `authority_review_check.status=prechecked_needs_external_evidence`,
  all machine-checkable conditions true:
  `required_count_placed`, `within_8_space_small_attached_limit`,
  `road_as_aisle_option_available`, `tandem_depth_count_ok`,
  `stalls_contiguous`, `v1_turning_status_ok`.
  Remaining external evidence is exactly:
  `sidewalk_or_roadway_separation_evidence` and
  `authority_no_traffic_obstruction_confirmation`.
- Frontend now surfaces this in both parking inspector and the visible VWorld
  `BUILDING MASS` overlay. Latest Playwright state confirms:
  `hasAuthorityReviewText=true`, `hasEvidenceNeededText=true`, with screen text
  `관청검토 / 증빙필요 2`.
- Frontend Vite server was restarted after the UI patch. Current local URL is
  still `http://127.0.0.1:5174/design`.
- Latest Playwright/VWorld run still passes:
  `layout_candidate.status=pass`, `required/provided=3/3`,
  `parkingStallEntities=6` after label entity counting, `pilotiEntities=0`,
  PNG pink-pixel check about `9442`.
- Visual correction after user review: the cyan
  `entrance_connector_polygon_wgs84` was only a solver/debug helper for road
  access, not a parking stall or required parking bay. It is now hidden in the
  default Cesium view and only appears with `?parkingDebug=1` or `?layers=all`.
  Default PNG review should judge the solid pink stall outlines and labels only.
  For small attached parking, front-road/road-as-aisle use is handled in the
  evidence/status path, not by rendering a cyan parking-looking rectangle.
- Verified after Vite restart with the single current-PNU case file
  `docs/playwright/design-route-live-verify/parking-stall-current-pnu.json`.
  PNU `1168011800104170004` passed with `parkingEntities=8`,
  `parkingStallEntities=4`, `pilotiEntities=0`; the prior three cyan connector
  entities are gone from the default PNG. Latest PNG:
  `docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-current-pnu_1168011800104170004.png`.
- Separate common-housing verification is stored in
  `docs/playwright/design-route-live-verify/parking-stall-current-pnu-housing.json`.
  For the same PNU `1168011800104170004`, building type `공동주택` passed with
  `strategy=piloti_ground`, `required/provided=3/3`, `parkingEntities=12`,
  `parkingStallEntities=6`, `pilotiEntities=0`, `connectorEntities=[]`, and no
  mass/parking points outside the requested PNU boundary. The selected rule is
  `seoul_parking_appendix2_row_05` over base `parking_appendix1_row_05`, metric
  `household_or_unit_area`, `metric_value=293.46`, `raw_spaces=3`, source
  `서울특별시 주차장 설치 및 관리 조례::별표2`. The unit schedule is still
  `mass_stage_estimate`, so do not call it final permit-grade household evidence.
  Latest PNG:
  `docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-current-pnu-housing_1168011800104170004.png`.
- North-sunlight validation is now included in the Windows Chrome CDP verifier.
  `ARR/frontend/src/design/components/SiteMapPanel.tsx` exposes
  `window.__arrDesignSetbackGeometries`, and
  `docs/playwright/design-route-live-verify/windows-cdp-vworld-pnu-batch.cjs`
  writes `state.sunlightContainment` and fails a case when an applicable
  sunlight envelope has `inside=false`.
  Latest common-housing run for PNU `1168011800104170004`:
  `sunlightContainment.applies=true`, `datumCase=neighbor_avg_86`,
  `datumElevationM=17.2293387484479`, `baseSetbackM=1.5`, `slope=2`,
  `baseHeightM=10`, `maxMassTopM=8.4`, `method=base_1_5m_ring`,
  `checked_points=7`, `outside_points=0`, `inside=true`. This validates the
  current selected mass against the H<=10m north-sunlight base ring. Future
  taller candidates still need the height-layer check to be upgraded beyond the
  current `needs_height_layer_check` marker.
- Follow-up code review tightened this gate: if a future selected volume exceeds
  `baseHeightM=10m`, `sunlightContainment.status` becomes
  `needs_height_layer_check` and `inside=false`, so the Playwright summary no
  longer passes taller candidates until height-layer containment is implemented.
  Re-ran the current common-housing case and it still passes with
  `sunlightContainment.status=pass`.
- Datum review note: current verified datum values for this PNU are from the
  converted NGII local DEM (`ngii_local_dem`, UI text
  `NGII 수치지형도 SHP→DEM (5m)`), not Open-Meteo. The calculator implements
  boundary length-weighted §119 datum as `Σ(L_i*h_i)/Σ(L_i)`, with long-edge
  sub-sampling and a median filter. For north-sunlight, the rendered H=0 uses
  the §86 neighbor average when available. Do not call it "perfect": it is
  trustworthy only for parcels covered by the configured local DEM and still
  depends on VWorld parcel/neighbor/road geometry quality. Fixed a stale frontend
  label in `DatumInfoCard.tsx` that still said slope `≤8m/>8m`; it now matches
  the NGII-era §119 threshold `≤3m/>3m`.

Current verified state:

- Test PNU: `1168011800104170004`.
- `maas_legal_envelope` live API flow works through:
  `site-boundary -> auto-constraints -> jobs -> run -> results`.
- Playwright live browser verification on `http://127.0.0.1:5174/design` works through:
  `open route -> fill PNU -> lookup -> optimize -> results`.
- Windows Chrome remote-debugging verification confirms VWorld/WebGL can load outside WSL headless:
  - command path used: `C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222`
  - WebGL renderer: `ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Ti, Direct3D11)`
  - VWorld scripts loaded, including `webglMapInit.js.do`, `WSViewerStartup.js`, `VWViewerStartup.v30.min.js`, `vw.ol3WebGL.v30.js`.
  - `window.Cesium`, `window.vw`, and `window.ws3d` are present.
  - wide-window lookup capture: `docs/playwright/design-route-live-verify/windows_chrome_vworld_check.png`
  - wide-window optimize capture: `docs/playwright/design-route-live-verify/windows_chrome_vworld_optimize.png`
  - result JSON: `docs/playwright/design-route-live-verify/windows-chrome-vworld-check.json`
- Current VWorld visual status from Windows Chrome capture:
  - The earlier narrow map was caused by the Chrome capture window being only about 929px wide; after left `410px` and right `400px` panels, the center map had almost no width.
  - After resizing the remote-debugging Chrome window to `1800x1100`, VWorld canvas renders wide: main canvas around `966x976`.
  - After optimize, Cesium viewer contains `design-mass-*` entities and the blue MAAS mass is visible on VWorld.
  - Verified mass entities include `design-mass-floor-group-*`, `design-mass-floor-*`, `design-mass-footprint-*`, and `design-mass-edge-*`.
- Latest Playwright captures:
  - `docs/playwright/design-route-live-verify/03_after_lookup_cdp.png`
  - `docs/playwright/design-route-live-verify/04_after_optimize_cdp.png`
- Browser-verified output after optimize:
  - `OPTIMIZATION COMPLETE`
  - `18 pareto`
  - `DESIGN LIST 18`
  - selected candidate `legal_layered_max`
  - `16.8m`, `6F`, BCR `39.0%`, FAR `175.5%`, floor area `463m2`
- Latest verified first candidate:
  - `legal_layered_max`
  - 5 floors
  - `17.5m`
  - FAR `136.78%`
  - BCR `38.97%`
  - floor plates `[102.93, 102.93, 74.99, 51.47, 28.96]`
- Tiny FAR-remainder floors are blocked by a first-pass minimum plate threshold:
  `min(24m2, ground_plate_area * 0.25)`.

Current limits:

- Headless Playwright in this environment cannot verify Cesium/WebGL mass pixels; it reports `WebGL을 사용할 수 없어 3D 지도를 비활성화했습니다.`
- Root cause verified on 2026-06-10:
  - `ARR/frontend/src/land/hooks/use-vworld-3d.ts` intentionally returns false when `navigator.webdriver` or `HeadlessChrome` is detected.
  - `xvfb-run` headed Chromium with `navigator.webdriver=false` still reports WebGL context creation as false in this WSL automation environment.
  - VWorld script does not load in this condition; no Cesium canvas is created.
- Use Windows Chrome remote-debugging for true VWorld checks from this environment; WSL headless Playwright is only valid for API/DOM/fallback checks.
- The browser-verified fallback is `2D MASS PREVIEW · WebGL fallback · legal MAAS geometry from mass_geojson`.
- API and React E2E can verify candidate generation and 2D fallback rendering, but final VWorld/Cesium 3D mass placement still needs a real GPU browser check.
- The minimum floor plate threshold is pragmatic, not a full architectural/program legal rule.
- `buildable_footprint_from_setback_geometries()` still needs stronger handling for concave parcels and complex multi-road cases.
- Do not present this as a complete legal code checker until datum, road, neighbor, sunlight/daylight, and VWorld visual placement all pass together.

## Current MAAS AI Contract

Do not say the LLM directly creates MAAS mesh geometry.

The current AI path is:

1. User architectural language, such as "북측 일조 때문에 상부를 계단식으로 후퇴".
2. Intent resolver or future fine-tuned model maps it to a strict MAAS grammar sequence.
3. Deterministic MAAS code in `ARR/backend/design/maas` creates/rebuilds geometry.
4. Legal repair/check/evidence decides whether the candidate is pass, fail, or needs evidence.
5. Agent/LLM reviews evidence and requests deterministic tools; it does not claim legal pass without evidence.

Implemented contract files:

- `ARR/backend/design/maas/grammar/data/maas_terms.v0.json`
- `ARR/backend/design/maas/grammar/data/maas_sequences.v0.json`
- `ARR/backend/design/maas/grammar/intent.py`
- `ARR/backend/design/maas/training/`
- `ARR/backend/design/management/commands/export_maas_training_data.py`

Training data command:

```bash
cd /mnt/d/Data/25_ACE/ARR/backend
env -u NEO4J_URI .venv/bin/python manage.py export_maas_training_data --limit 2
```

Expected outputs:

- `docs/ai-session-memory/datasets/maas_intent_sft_seed.jsonl`
- `docs/ai-session-memory/datasets/maas_evidence_review_sft.jsonl`

## Current MAAS Aesthetic Image Contract

Do not say GPT Image or Nano Banana creates or legalizes the MAAS mass.

The current aesthetic image path is:

1. Deterministic MAAS code produces a legal/evidence-backed candidate.
2. `mass_geojson`, floor count, height, silhouette, setbacks, and legal envelope
   are locked as source of truth.
3. The backend renders a deterministic multi-view reference PNG from the locked
   mass, floor plates, and mass volumes.
4. GPT Image or Nano Banana may generate facade/material/window rhythm and
   presentation quality from that reference.
5. Generated imagery is attached as evidence/visualization only; it cannot
   change legal status or replace the geometry.

Implemented live endpoint:

```text
POST /design/jobs/<job_id>/results/<design_id>/aesthetic/
GET  /design/maas/aesthetic-assets/<asset_path>
```

Frontend status:

- `/design` right-side candidate panel has an `외관 이미지 생성` section.
- Providers: `placeholder`, `gpt-image`, `nano-banana`.
- The UI sends provider/style to the backend and displays the locked reference
  image plus generated provider image when available.

Provider configuration:

- `OPENAI_API_KEY` enables `gpt-image` through the OpenAI image adapter.
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` enables `nano-banana` through Gemini.
- `NANO_BANANA_ENDPOINT` + `NANO_BANANA_API_KEY` enables the HTTP fallback.
- If no provider key is configured, the endpoint returns `needs_provider` and
  still produces the locked reference PNG.

Research-backed direction:

- Do not treat a single pretty image as the end product.
- WACV 2025 `3D Synthesis for Architectural Design`, CAADRIA 2025
  `Multi-View Depth Consistent Image Generation`, and CVPR 2026 `UniTEX`
  all support the same direction: explicit 3D geometry first, multi-view
  conditioning second, facade/texture generation third, and projection back
  onto the same geometry last.
- Current implementation starts this path with
  `MultiViewReferencePackRenderer`: front/right/back/left/axon/top sheet plus
  `arr.maas.scene_graph.v0` metadata.
- Still missing for true facade texture projection:
  depth maps, normal maps, silhouette masks, facade UV/projection mapping, and
  multi-view consistency validation.

Latest verification on 2026-06-10:

```bash
cd /mnt/d/Data/25_ACE/ARR/backend
env -u NEO4J_URI .venv/bin/python manage.py test design.test_maas_export --verbosity 1

cd /mnt/d/Data/25_ACE/ARR/frontend
npm run type-check
```

Expected: backend MAAS/export/aesthetic tests pass and frontend type-check
passes. A live dry-run for job `4056a042-dad8-4bf3-bd3b-6ccec4f716e1` and
design `900000` returned a 1024x1024 PNG under:

```text
/design/maas/aesthetic-assets/references/ac88c855be467167.png
```

Windows Chrome Playwright/CDP verification after Vite restart:

- Script: `docs/playwright/design-route-live-verify/windows-cdp-aesthetic-check.cjs`
- Screenshot: `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_check.png`
- JSON: `docs/playwright/design-route-live-verify/windows-chrome-aesthetic-check.json`
- Verified on `http://127.0.0.1:5174/design`:
  - PNU lookup and MAAS optimize complete.
  - candidate row `design-row-0` selected.
  - `외관 이미지 생성` section renders in the right AI collaboration panel.
  - provider options render: `Reference only`, `GPT Image`, `Nano Banana`.
  - placeholder dry-run returns `needs_provider`.
- `legal_status_effect: none` is shown.
- locked reference image loads as 1536x1536 multi-view PNG from
    `/design/maas/aesthetic-assets/references/*.multi-view.png`.

VWorld overlay status:

- The latest aesthetic result is lifted from `InteractiveDesignPanel` to
  `DesignPage` and passed into `SiteMapPanel`.
- `SiteMapPanel` renders the generated image URL, or the locked reference URL
  if no provider image exists, as a Cesium billboard above the selected MAAS
  mass.
- Verified entity id: `design-mass-aesthetic-overlay-900000`.
- This is an in-map preview overlay, not yet true facade texture projection.
  True projection still requires multi-view orthographic renders, camera poses,
  depth/normal/silhouette masks, and facade/UV mapping.

Important dev-server note:

- The Vite server running since 2026-06-09 served a stale transformed
  `InteractiveDesignPanel.tsx` module after the aesthetic UI edit.
- Restarting Vite on `127.0.0.1:5174` fixed it. If a newly added UI does not
  appear, check the served source with:

```bash
curl -s http://127.0.0.1:5174/src/design/components/InteractiveDesignPanel.tsx | rg "외관 이미지 생성|createMaasAesthetic"
```

AG-light collaboration UI note from 2026-06-16:

- AG-light server runs on `http://127.0.0.1:8200`; health endpoint returned
  `status: true` with MCP mounted at `/mcp/mcp`.
- `/design` right panel now has an `AG-light 협업모드` section inside
  `InteractiveDesignPanel`.
- The panel reads ARR evidence from
  `/design/jobs/{job_id}/results/{design_id}/evidence/`, summarizes five agents
  (`law_agent`, `parking_agent`, `sunlight_agent`, `datum_agent`,
  `design_critic`), sends each summary to AG-light `/bus/send`, then renders
  recent bus messages.
- `DesignPage` now opens the collaboration panel from the active displayed
  mass even when the user has not explicitly clicked a DESIGN LIST row. This
  avoids the old state where the center showed `BUILDING MASS` but the right
  panel still said "후보를 선택하면...".
- Vite served a stale transformed `InteractiveDesignPanel.tsx` after the first
  AG-light edits. Fix was:

```bash
rm -rf ARR/frontend/node_modules/.vite
cd ARR/frontend && npm run dev -- --host 127.0.0.1 --port 5174
curl -s http://127.0.0.1:5174/src/design/components/InteractiveDesignPanel.tsx | rg "evidenceParking|required_count"
```

- Playwright verification after Vite cache clear:
  - JSON: `docs/playwright/design-route-live-verify/ag-light/ag-light-final-new-code.json`
  - PNG: `docs/playwright/design-route-live-verify/ag-light/ag-light-final-new-code.png`
  - PNU `1168011800104170004`, building type `공동주택`, generations `5`,
    population `10`.
  - Verified `AG-light 협업모드` renders, all five agent rows render, AG-light
    bus log receives messages, and parking summary reads `3/3대 · piloti_ground`.
- Follow-up Playwright verification after adding React Flow mini graph:
  - JSON: `docs/playwright/design-route-live-verify/ag-light/ag-light-react-flow.json`
  - PNG: `docs/playwright/design-route-live-verify/ag-light/ag-light-react-flow.png`
  - Verified `data-testid="ag-light-react-flow"` contains React Flow DOM,
    `reactFlowNodes: 6`, `reactFlowEdges: 5`, all five review rows render, and
    parking summary still reads `3/3대 · piloti_ground`.
- Follow-up refactor on 2026-06-16:
  - Copied the AutoGen Studio agent-flow structure into
    `ARR/frontend/src/design/components/ag-light-flow/`
    (`AGLightFlow.tsx`, `agentnode.tsx`, `edge.tsx`, `types.ts`).
  - The new flow now renders in the `/design` right panel as a React Flow
    collaboration surface with `ag-light-react-flow` test id.
  - Type-check passed after loosening the custom node data typing to match
    `@xyflow/react`.
  - Verified with Playwright on PNU `1168011800104170004` after search +
    optimize + design selection; screenshot saved at
    `docs/playwright/design-route-live-verify/ag-light/ag-light-reactflow-selected.png`.
- Scope clarification: this is now React Flow based like the AutoGen-style
  visual collaboration surface, and the embedded graph should be treated as
  the canonical editable entry point for future AG-light UI changes. Next step
  is interactive node selection, live per-node status from AG-light bus, and
  team/pattern templates from `AG-light/data/teams` and
  `AG-light/data/patterns`.
- Research alignment note from `AG/AG-Research`:
  - This UI is supposed to visualize real multi-agent collaboration, not a
    decorative chat widget. The research folder studies coordination topologies
    such as flat sequential, selector/star routing, swarm/mesh handoff,
    reflection/debate feedback, pipeline, and mixture-of-agents.
  - For MAAS `/design`, the intended topology is closest to selector/star plus
    structured feedback: `orchestrator` routes between `law_agent`,
    `parking_agent`, `sunlight_agent`, `datum_agent`, and `design_critic`, and
    agents should exchange evidence and review decisions over AG-light bus.
  - Current implementation only visualizes this collaboration as a React Flow
    graph and streams recent bus messages. It does not yet implement topology
    switching, termination criteria, marginal utility stopping, or real
    selector/swarm handoff behavior from the AG research experiments.
  - Next frontend/backend step should therefore be explicit: wire React Flow
    node selection to per-agent bus messages/evidence, expose agent status
    transitions, and add a termination/decision state so the user can see
    whether the team reached `pass`, `needs_evidence`, or `repair_requested`.
- Commit/push caution from 2026-06-19 review:
  - This workspace has nested git repositories: root `ACE`, `ARR`, `AG`, `AUA`,
    `korean-law-mcp`, and more. Do not make a broad root commit.
  - The current AG-light UI work primarily belongs in `ARR` for frontend/backend
    code and in root `ACE` for `AG-light/` plus `docs/ai-session-memory`.
  - `ARR` currently has many untracked files because the project was assembled
    with large generated/experimental directories. Before commit/push, stage
    only the AG-light UI and MAAS files intentionally touched; do not use
    `git add .`.
  - Verified on 2026-06-19:
    `cd ARR/frontend && npm run type-check` passed, AG-light health passed, and
    Playwright rechecked `/design` through PNU lookup, optimize, design select,
    and AG-light React Flow render. Latest artifacts:
    `docs/playwright/design-route-live-verify/ag-light/ag-light-ui-full-recheck-20260619.png`
    and `.json`.
- Remaining issue: AG-light datum/sunlight review still shows
  `datum_result 없음` / `적용 외 또는 envelope 없음` in the right panel even
  though the left legal basis panel has NGII datum and 정북일조 values. Next
  session should pass the already-loaded `setbackGeometries.datum_result` and
  `sunlight_envelope` into the AG-light review path more reliably, or include
  those values in ARR evidence.

Parking/VWorld note from 2026-06-14:

- Exact parking stalls should read as clean solid pink stall outlines in Cesium
  (`#ff2f92`) with a dark shadow/raised visible line. Earlier white/decal/corridor
  experiments are obsolete.
- When stall polygons exist, suppress the parking envelope boundary, hatch
  guides, and teal mass edge helper lines; otherwise VWorld PNG captures make
  them look like messy parking lines.
- If a parking style change does not appear in PNG verification, restart Vite
  on `127.0.0.1:5174` before rerunning the Windows Chrome CDP batch.
- Parking inspector must show legal count formula, layout module formula,
  adjacency, aisle, turning, and column/core v1 status. The current frontend
  source is `ARR/frontend/src/design/components/DesignInspector.tsx`.

## Quick Check

```bash
node cli/design-regulation-check/start-local.mjs
node cli/design-regulation-check/run-all.mjs --base http://127.0.0.1:8000
node cli/design-regulation-check/check-design.mjs
```

Expected: `start-local.mjs` opens the local backend/frontend pair and prints `http://127.0.0.1:5174/design`; all bundled verification gates should PASS.

If the browser/VWorld frontend is unreliable, render API-derived section diagrams:

```bash
node cli/design-regulation-check/render-section.mjs --base http://127.0.0.1:8000
ARR/backend/.venv/bin/python cli/design-regulation-check/render_section.py --base http://127.0.0.1:8000
```

Expected: PASS and visual files under `cli/design-regulation-check/out/sections/` or `cli/design-regulation-check/out/pysections/`.
