# Prompt For The Other Local AI

Use this when asking another AI session to verify the Windows local app.

```text
We are working in D:\Data\25_ACE.

Do not test /land as the final target. Test /design.

Architecture:
- /design visual data is computed by ARR Django backend, not by Hermes/agent.
- UI path: ARR frontend /design -> ARR backend /design/site-boundary + /design/auto-constraints -> ARR backend land services.
- Agent path is separate: gateway/Hermes land_analyst -> ARR backend /land/analyze.
- If /design rendering is wrong, inspect ARR backend/frontend first.

Goal:
- The /design VWorld/Cesium screen must draw legal building constraints on the parcel:
  - parcel boundary from VWorld cadastral geometry
  - datum/대지레벨 from NGII local DEM, source must be ngii_local_dem
  - adjacent-lot setback
  - road/building-line setback from neighboring road frontage
  - corner cutoff where applicable
  - north sunlight envelope when applicable
  - daylight diagonal envelope for 공동주택

First run the CLI regression:
  node cli/design-regulation-check/run-all.mjs --base http://127.0.0.1:8000
  node cli/design-regulation-check/check-design.mjs

This calls:
  POST http://127.0.0.1:8000/design/site-boundary/
  POST http://127.0.0.1:8000/design/auto-constraints/

If the patched backend is running on another local port:
  node cli/design-regulation-check/check-design.mjs --base http://127.0.0.1:18000

If the frontend is broken or visually suspicious, also render section diagrams from the same API:
  node cli/design-regulation-check/render-section.mjs --base http://127.0.0.1:18000
  ARR/backend/.venv/bin/python cli/design-regulation-check/render_section.py --base http://127.0.0.1:18000

Inspect:
  cli/design-regulation-check/out/sections/summary.json
  cli/design-regulation-check/out/sections/*.svg
  cli/design-regulation-check/out/pysections/summary.json
  cli/design-regulation-check/out/pysections/*.png
  cli/design-regulation-check/out/pysections/image-check.json

Fail the check if:
- datum_result is missing
- datum_result.elevation_source is not ngii_local_dem
- a case with `expectSplitBands` does not return non-empty datum_result.split_bands
- road_setback or adjacent_setback is missing for the listed Seoul cases
- daylight_diagonal_envelope is missing for 공동주택
- sunlight_envelope.datum_elevation_m does not match datum_result.neighbor_avg_datum_m when north sunlight and neighbor average exist
- sunlight_envelope.datum_case is not neighbor_avg_86 when using neighbor average
- an envelope is returned when the case says expectSunlight:false or expectDaylight:false
- /design visually omits returned setback_geometries

Known legal/data risks to keep visible:
- Building Act Enforcement Decree Article 119 requires weighted datum and 3m segmentation when ground height difference exceeds 3m. ARR now exposes `split_bands` for SLOPE_GT3M using DEM boundary profile metadata, but true contour-clipped area polygons are still not complete.
- Runtime uses converted GeoTIFF `D:/Data/NGII_DEM/seoul_dem.tif`, not raw SHP directly. Raw SHP is offline source material for DEM generation.
- Road/building-line frontage currently uses neighboring VWorld cadastral road parcels first, then falls back to geometry heuristics if road lookup fails.

Then open http://127.0.0.1:5173/design and search each case in cli/design-regulation-check/cases.json.
Use the browser devtools/network panel to confirm /design/auto-constraints returns the same keys printed by the CLI.

If the frontend must point to a non-8000 backend, run it with:
  VITE_ARR_BACKEND_URL=http://127.0.0.1:18000 npm run dev -- --host 127.0.0.1 --port 5174

Important datum contract:
- datum_result.parcel_datum_m = 대지 §119 기준면.
- datum_result.road_datum_m = 전면도로 기준면 metadata.
- datum_result.neighbor_datum_m = 인접대지 기준면 metadata.
- datum_result.neighbor_avg_datum_m = §86 평균수평면.
- sunlight_envelope.datum_elevation_m should equal neighbor_avg_datum_m when available.
- building mass and daylight_diagonal_envelope should use parcel_datum_m, not the north-sunlight average.

Relevant files:
- ARR/backend/design/views.py
- ARR/backend/land/services/setback_geometry.py
- ARR/backend/land/services/road_frontage.py
- ARR/backend/land/services/datum/elevation_api.py
- ARR/frontend/src/design/components/SiteMapPanel.tsx
- ARR/frontend/src/design/lib/envelopes/sunlight.ts

Do not treat a pretty screen as pass unless the CLI says datum source is ngii_local_dem.
```
