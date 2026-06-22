# Verification

## API CLI Gate

Local one-command launcher:

```bash
node cli/design-regulation-check/start-local.mjs
```

It starts the ARR backend on `http://127.0.0.1:18000`, starts the Vite frontend at `http://127.0.0.1:5174/design` with `VITE_ARR_BACKEND_URL` pointed to that backend, then runs the all-in-one gate below. Use `--no-verify` only for quick browser inspection.

Default all-in-one gate:

```bash
node cli/design-regulation-check/run-all.mjs --base http://127.0.0.1:18000
```

Latest observed all-in-one result after installing `rasterio` and restricting bundled cases to DEM-covered parcels: PASS for API regulation gate, SVG section render gate, Python matplotlib section gate, Python PNG pixel verification gate, and backend datum/setback unit tests. The gate now also includes the Python matplotlib plan gate.

Plan-view datum QA:

```bash
ARR/backend/.venv/bin/python cli/design-regulation-check/render_plan.py --base http://127.0.0.1:18000
```

Outputs:

```text
cli/design-regulation-check/out/plan/Gangnam_Dogok_467-3.png
cli/design-regulation-check/out/plan/Gangnam_Daechi_1028.png
cli/design-regulation-check/out/plan/summary.json
```

Latest observed plan result: PASS for Dogok 467-3 and Daechi 1028. The summary records parcel/road/neighbor datum values plus `roadFrontages`, `neighborParcels`, `parcelSamples`, and `roadSamples`. This is the first gate for verifying whether the §119 weighted average and §86 neighbor average are attached to the correct geometry before trusting the VWorld overlay.

Important user-confirmed VWorld display rule:

- Do not show the old surrounding elevation grid as the legal datum indicator.
- VWorld/Cesium should mirror the plan PNG marker logic:
  - `대지 §119`: at the parcel weighted-sample basis.
  - `도로레벨`: at the road centerline / road sample basis.
  - `인접대지레벨`: at the north shared-boundary / selected neighbor basis.
  - `§86 평균`: between the parcel basis and north-neighbor basis.
- Implementation check: `npx vite build --mode web` passed after the VWorld marker change. For Gangnam Daechi 1028, backend marker inputs were `parcelSamples=112`, `roadSamples=3`, `neighborSamples=47`, producing four marker values: parcel §119 `15.00m`, road `15.00m`, neighbor `16.365m`, §86 average `15.683m`.
- Reference PNGs:
  - `D:\Data\25_ACE\cli\design-regulation-check\out\plan\Gangnam_Dogok_467-3.png`
  - `D:\Data\25_ACE\cli\design-regulation-check\out\plan\Gangnam_Daechi_1028.png`

Run:

```bash
node cli/design-regulation-check/check-design.mjs
```

The CLI calls:

- `POST http://127.0.0.1:8000/design/site-boundary/`
- `POST http://127.0.0.1:8000/design/auto-constraints/`

It checks:

- parcel boundary exists,
- `datum_result` exists,
- `datum_result.elevation_source === "ngii_local_dem"`,
- `road_setback` exists when expected,
- `adjacent_setback` exists,
- `daylight_diagonal_envelope` exists for `공동주택`,
- `sunlight_envelope` exists only where expected/applicable.
- `sunlight_envelope.datum_elevation_m` matches `datum_result.neighbor_avg_datum_m` when applicable.
- `sunlight_envelope.datum_case === "neighbor_avg_86"` when using the neighbor average.
- `daylight_diagonal_envelope.walls` contains valid relative heights.
- `expectSunlight:false` / `expectDaylight:false` cases fail if the envelope is unexpectedly returned.

Latest observed PASS cases:

- `강남구 도곡동 467-3` -> PNU `1168011800104670003`, datum `15m/ngii_local_dem`, north sunlight present.
- `강남구 대치동 1028` -> PNU `1168010600110280000`, datum `15m/ngii_local_dem`, north sunlight present.
  With the actual local DEM loaded through `rasterio`, this case is currently `flat`; do not expect `split_bands` for it.

`강남구 역삼동 677` is currently outside the configured local `seoul_dem.tif` coverage and must not be treated as a valid NGII datum regression case until another DEM tile is added.

The full gate also writes `cli/design-regulation-check/out/dem-coverage.json`, which records:

- `강남구 도곡동 467-3`: covered
- `강남구 대치동 1028`: covered
- `강남구 역삼동 677`: not covered

2026-05-13 local verification against patched backend:

```bash
node cli/design-regulation-check/check-design.mjs --base http://127.0.0.1:18000 --out /tmp/design-check-18000.json
```

Result: PASS for all three cases.

## Section SVG Gate

Use this when the frontend map is visually suspect, Playwright MCP is unavailable, or Cesium hangs:

```bash
node cli/design-regulation-check/render-section.mjs --base http://127.0.0.1:18000
```

Output:

```text
cli/design-regulation-check/out/sections/Gangnam_Yeoksam_677.svg
cli/design-regulation-check/out/sections/Gangnam_Dogok_467-3.svg
cli/design-regulation-check/out/sections/Gangnam_Daechi_1028.svg
cli/design-regulation-check/out/sections/summary.json
```

Latest observed section render result: PASS for all three cases.
The section renderer now treats datum source mismatch, missing expected envelopes, and unexpectedly returned false-case envelopes as hard failures.

Important expected values:

- `강남구 도곡동 467-3`: parcel `15.00`, road `15.00`, neighbor `15.00`, §86 average `15.00`, sunlight `15.00`.
- `강남구 대치동 1028`: parcel `15.00`, road `15.00`, neighbor `16.37`, §86 average `15.68`, sunlight `15.68`.

This SVG gate does not replace VWorld/Cesium QA, but it verifies the legal datum/envelope basis independently from frontend rendering.

## Python Matplotlib Gate

Use this when the user wants a Python-side visual/test artifact instead of SVG:

```bash
ARR/backend/.venv/bin/python cli/design-regulation-check/render_section.py --base http://127.0.0.1:18000
```

Output:

```text
cli/design-regulation-check/out/pysections/Gangnam_Yeoksam_677.png
cli/design-regulation-check/out/pysections/Gangnam_Dogok_467-3.png
cli/design-regulation-check/out/pysections/Gangnam_Daechi_1028.png
cli/design-regulation-check/out/pysections/summary.json
```

Latest observed Python render result: PASS for all three cases. The script auto-loads available Korean fonts from `~/.fonts` to avoid missing glyphs in the PNG.

`run-all.mjs` also reopens those PNG files with Pillow via `verify_images.py` and checks that the expected colored datum/envelope lines and mass pixels exist. Latest observed image pixel check: PASS for all three cases.

Important visual QA rule from user feedback:

- Do not rely on CLI pass/fail alone for legal-review work.
- Always produce and inspect a PNG section before claiming a regulation diagram is correct.
- Use the three-view review set:
  - plan view / 평면: parcel, roads, adjacent lots, legal lines.
  - section view / 단면: road datum, parcel §119 datum, adjacent datum, §86 average plane, slope ratios, and sample mass pass/fail.
  - VWorld/Cesium view: same geometry projected onto the real cadastral map.
- Ratio labels in section drawings must use vertical:horizontal. Therefore:
  - 정북일조 H/2 이격 is `H = 2x`, label `2:1`.
  - 공동주택 채광사선 multiplier 2 is `H = 2x`, label `2:1`.
  - old/reference front-road diagonal with multiplier 1.5 is `H = 1.5x`, label `1.5:1`.
- The slope itself is now considered correct when drawn as above. To prevent a repeat of the 1:2 vs 2:1 confusion, section PNGs must use equal x/y aspect and draw a small slope marker on the line:
  - `수평 1`, `수직 2`, `2:1` for 정북일조 and 채광사선.
  - `수평 1`, `수직 1.5`, `1.5:1` for the old/reference front-road diagonal.
- Current implementation point: `cli/design-regulation-check/render_section.py` uses `ax.set_aspect("equal", adjustable="box")` and `slope_marker(...)` for this.
- If a PNG and a VWorld overlay disagree, debug datum/geometry first; do not tune the VWorld rendering blindly.

Additional proxy/API check through patched Vite:

- Run frontend with `VITE_ARR_BACKEND_URL=http://127.0.0.1:18000 npm run dev -- --host 127.0.0.1 --port 5174`.
- `POST http://127.0.0.1:5174/design/auto-constraints/` for `강남구 도곡동 467-3` returned:
  - `parcelDatum`: `15`
  - `neighborDatum`: `15`
  - `neighborAvg`: `15`
  - `sunlightDatum`: `15`
  - `sunlightCase`: `neighbor_avg_86`
  - `daylightWalls`: `1`

## Browser Gate

Open:

```text
http://127.0.0.1:5173/design
```

If the latest backend is running on another port, set `VITE_ARR_BACKEND_URL`.
Example verified URL:

```text
http://127.0.0.1:5174/design
```

Search cases from `cli/design-regulation-check/cases.json`.

Use devtools Network to inspect `/design/auto-constraints/`.

Pass criteria:

- Response keys match CLI output.
- Datum card/plane uses `ngii_local_dem`.
- VWorld shows returned overlays, especially road, adjacent, north sunlight, and daylight where present.

Playwright MCP was blocked in this environment because it requires `/opt/google/chrome/chrome` and `npx playwright install chrome` requires sudo. Direct Playwright with bundled Chromium was also unstable on the Cesium page. Manual Windows browser verification is expected.

## MAAS Massing Gate

Use this to verify the current MAAS legal-envelope mass generation path, separate from Cesium pixel rendering.

Servers:

```bash
cd ARR/backend
.venv/bin/python manage.py runserver 127.0.0.1:18000

cd ARR/frontend
VITE_ARR_BACKEND_URL=http://127.0.0.1:18000 npm run dev -- --host 127.0.0.1 --port 5174
```

Browser/API test PNU:

```text
1168011800104170004
```

Expected API flow:

```text
POST /design/site-boundary/
POST /design/auto-constraints/
POST /design/jobs/
POST /design/jobs/<job_id>/run/
GET  /design/jobs/<job_id>/results/
```

Latest verified result:

- `maas_legal_envelope` returned 18 Pareto candidates.
- First candidate:
  - `mass_shape = legal_layered_max`
  - `num_floors = 5`
  - `height = 17.5`
  - `far = 136.78`
  - `bcr = 38.97`
  - `floor_plates = [102.93, 102.93, 74.99, 51.47, 28.96]`
  - `mass_volumes = 2`
  - all generated floor groups had `program_packing.status = ok`.

Important Playwright caveat:

- Do not set global `Accept: text/html` headers in Playwright when testing `/design?e2e=1`; that also affects `fetch()` and can make API calls receive SPA HTML instead of JSON.
- Headless Chromium in this environment cannot currently verify Cesium 3D pixels. The main `/design` route loads, but reports `WebGL을 사용할 수 없어 3D 지도를 비활성화했습니다.` with normal headless settings, and forced WebGL can hang.
- Therefore Playwright can verify React/API mass generation here, but final VWorld/Cesium mass appearance still requires a real browser check.

## Parking Grid Solver / VWorld PNG Gate

Latest verified on 2026-06-15 with Windows Chrome CDP and VWorld/Cesium:

```bash
powershell.exe -NoProfile -Command "node D:\\Data\\25_ACE\\docs\\playwright\\design-route-live-verify\\windows-cdp-vworld-pnu-batch.cjs --cases=D:\\Data\\25_ACE\\docs\\playwright\\design-route-live-verify\\parking-stall-cases.json"
```

Case file:

```text
docs/playwright/design-route-live-verify/parking-stall-cases.json
```

Neo4j parking-law graph must be live for graph-backed runs:

```bash
cd ARR/backend
NEO4J_URI=bolt://172.27.80.1:7687 NEO4J_PASSWORD=11111111 .venv/bin/python law/scripts/verify_parking_law_graph.py
NEO4J_URI=bolt://172.27.80.1:7687 NEO4J_PASSWORD=11111111 .venv/bin/python law/scripts/check_parking_counts.py
```

Latest observed: `verify_parking_law_graph.py` passed `49/49`, and
`check_parking_counts.py` passed `23/23`. Run the backend with the same env:

```bash
cd ARR/backend
NEO4J_URI=bolt://172.27.80.1:7687 NEO4J_PASSWORD=11111111 .venv/bin/python manage.py runserver 127.0.0.1:18000
```

Pass criteria for these cases:

- VWorld canvas exists and is not fallback/disabled.
- `OPTIMIZATION COMPLETE` is reached.
- MAAS `design-mass-*` entities exist.
- Parking overlay entities exist.
- `requireParkingStalls: true` means at least one `design-mass-parking-stall-*` Cesium polygon entity must exist.
- PNG is written and must be visually inspected.

Latest PNG outputs:

```text
docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-neighborhood-stalls_1168011800104170004.png
docs/playwright/design-route-live-verify/pnu-batch/zoom_02_gangnam-dogok-neighborhood-stalls_1168011800104670003.png
docs/playwright/design-route-live-verify/pnu-batch/zoom_01_gangnam-small-apartment-visual-stalls_1168011800104170004.png
docs/playwright/design-route-live-verify/pnu-batch/summary.json
```

Latest observed result:

- PNU `1168011800104170004`
  - strategy: `piloti_ground`
  - layout status: `pass`
  - required/provided: `3/3`
  - placement: `grid_connected_90`
  - `parkingStallEntities: 3`
  - `pilotiEntities: 0`
  - `adjacency.status: row_contiguous`
  - `adjacency.gap_pairs: 0`
  - `adjacency.max_gap_m: 0`
  - `column_clearance.status: deferred_structural_review` remains in backend evidence only.
    Frontend column/core row and piloti helper columns are intentionally hidden
    until explicit structural column/core geometry exists.
  - `drive_aisle_clearance.status: pass`
  - `drive_aisle_clearance.provided_width_m: 6`
  - `turning_clearance.status: v1_pass`
  - `turning_clearance.method: stall_frontage_and_entrance_connector_v1`
  - `turning_clearance.frontage_connected_stalls: 1`
  - `turning_clearance.frontage_total_stalls: 3`
  - `turning_clearance.contiguous_row_frontage_relief.available: true`
  - `turning_clearance.contiguous_row_frontage_relief.basis: contiguous grid row with one generated 6m drive cell per stall`
  - `grid_solver.entrance_connected: true`
  - `grid_solver.entrance_verified: true`
  - `grid_solver.entrance_connection_type: site_connector_v1`
  - `grid_solver.entrance_min_distance_m: 8`
  - `grid_solver.entrance_connector_length_m: 8`
  - `grid_solver.entrance_connector_width_m: 3`
  - `grid_solver.entrance_connector_polygon_wgs84: present`
  - Interpretation: stall polygons render under/around piloti, legal count is met, the three stalls are one contiguous row, the 3m straight site connector is recorded/rendered, and column/core visuals are excluded for now. The v1 turning/frontage status is `pass` because row-contiguous grid stalls with one generated 6m drive cell per stall are accepted as row frontage connected. This is still not final authority approval or a real vehicle swept-path simulation.
- PNU `1168011800104670003`
  - strategy: `ground_surface`
  - layout status: `needs_aisle_review`
  - required/provided: `1/1`
  - placement: `single_row_aisle_review`
  - `parkingStallEntities: 1`
  - `adjacency.status: single_or_none`
  - `column_clearance.status: not_applicable`
  - `drive_aisle_clearance.status: needs_review`
  - `turning_clearance.status: needs_swept_path_review`
  - Interpretation: exterior surface stall renders, but aisle/road-as-aisle and swept-path review remain.
- PNU `1168011800104170004` with building type `공동주택`
  - case file: `docs/playwright/design-route-live-verify/parking-stall-apartment-case.json`
  - strategy: `piloti_ground`
  - current selected strategy after housing estimator: `ground_surface`
  - legal parking count: `computed_estimate` from mass-stage household/exclusive-area schedule.
  - Neo4j selected rule: `seoul_parking_appendix2_row_05`, base rule `parking_appendix1_row_05`.
  - source: `서울특별시 주차장 설치 및 관리 조례::별표2`.
  - required count: `3`
  - raw count basis: area ratio `1.3352`, Seoul household minimum `2.4`, ceil/max => `3`.
  - layout status: `needs_swept_path_review`
  - `parkingStallEntities: 3`
  - `parkingEntities: 12`
  - `pilotiEntities: 0`
  - Interpretation: this fixes the default apartment UI where parking lines
    disappeared and attaches a housing-law estimate. The remaining failure mode
    is not parking count; it is final turning/swept-path review.

Visual overlay update on 2026-06-15:

- Files changed:
  - `ARR/frontend/src/design/lib/cesium/mass-entities.ts`
  - `ARR/frontend/src/design/components/DesignInspector.tsx`
- Exact parking stalls now render as solid pink (`#ff2f92`) outline polylines
  with dark shadow lines and a raised `groundH + 1.15m` visible line so small stalls remain
  legible in VWorld PNGs.
- Piloti support columns and the `PILOTI VOID` label are intentionally not
  rendered. The current parking solver has no real structural column/core
  polygons, so showing guessed columns was misleading.
- The mass inspector no longer shows a column/core clearance row. Backend
  `column_clearance` remains evidence-only until structural geometry is modeled.
- The blue/review parking envelope fill was suppressed when exact stall
  polygons exist.
- The parking envelope boundary, hatch/guide lines, and teal mass edge helper
  lines are hidden when exact stall polygons exist, because they visually read
  as messy parking lines in VWorld PNG captures.
- The parking count/status label is also hidden when exact stall polygons exist;
  the left sidebar and mass inspector keep the legal/planned parking numbers.
- The 3m site connector corridor now renders from
  `grid_solver.entrance_connector_polygon_wgs84` as a low-alpha cyan polygon/outline
  plus a thin cyan centerline, so it reads as a helper and not as a parking stall line.
- Vite on `127.0.0.1:5174` had to be restarted before PNG verification reflected
  the changed Cesium entity code. When this module stays stale, delete
  `ARR/frontend/node_modules/.vite` and restart Vite with `--force`, then verify
  the served source with `curl`.
- Verified after restart/reload with the same Windows Chrome CDP batch:
  - PNU `1168011800104170004`: `parkingStallEntities=3`, `parkingEntities=12`, `pilotiEntities=0`.
  - PNU `1168011800104670003`: `parkingStallEntities=1`, `parkingEntities=3`, `pilotiEntities=0`.
  - Latest PNGs are the same paths listed above.
- Visual note: the large translucent pink diagonal surface visible in some PNGs
  is the existing sunlight/legal envelope overlay, not a parking stall. It was
  not changed because `design/lib/envelopes/sunlight.ts` is marked as a locked
  visual spec; if it confuses parking QA, add a layer toggle/focus mode rather
  than altering the envelope geometry.

Implementation facts to preserve:

- `ARR/backend/design/maas/parking_layout.py` grid solver records `x` stall candidates, `y` drive aisle cells, drive-cell component connectivity, and entrance edge connection metadata.
- `ARR/backend/design/maas/parking_layout.py` now also records formula metadata,
  row-contiguous adjacency metrics, `column_clearance`, `drive_aisle_clearance`,
  `turning_clearance`, and `grid_solver.entrance_connection_type`. `turning_clearance.method=stall_frontage_and_entrance_connector_v1`
  checks each stall's frontage against the generated 6m drive aisle and verifies
  the aisle entrance connection before allowing parking status to remain `pass`.
  For row-contiguous `grid_connected_90` stalls, `contiguous_row_frontage_relief`
  accepts the row when there is one generated 6m drive cell per stall; this avoids
  false failures from line-boundary intersection precision while preserving the
  explicit note that this is not swept-path simulation.
  `site_connector_v1`
  means a 3m-wide straight connector corridor from drive cell to road frontage is
  covered by the drive area and `road_frontage_geometry` is present; it is not a swept-path simulation. `column_clearance.status=deferred_structural_review`
  means no structural drawing/core polygons are available, so it must not be displayed as OK.
- `ARR/backend/design/maas/parking_strategy.py` converts WGS84 road frontage/sharedEdge geometry to UTM before parking layout checks.
- `ARR/backend/design/views.py` has a backend fallback that infers `parking_road_context` from `land.services.road_frontage.fetch_neighbor_roads(site_polygon)` when the frontend job options do not provide it.
- `ARR/backend/design/views.py` now chooses `best_geojson` by parking-aware score
  when parking precheck data exists, preferring nonzero required/provided stalls,
  layout pass, count satisfaction, contiguous small rows, verified entrance, and
  frontage count before falling back to original candidate order.
- VWorld road frontage `sharedEdge` may arrive as a raw coordinate array, not a GeoJSON LineString; the solver must keep supporting both.

Current expected limitation:

- This is still a mass-stage grid feasibility solver, not a BIM parking model.
- Do not claim ramp geometry, real swept-path simulation, real column/core
  conflicts, basement/mechanical equipment, or final authority approval are
  complete. The current column/turning values are v1 assumptions.
- Next quality step is to replace `site_connector_v1` with actual entrance
  throat geometry, swept-path checks, and column/core polygons.
