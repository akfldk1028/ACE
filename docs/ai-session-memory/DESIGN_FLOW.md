# `/design` Data Flow

Final target route:

```text
ARR frontend /design
  -> POST /design/site-boundary/
  -> POST /design/auto-constraints/
  -> ARR backend land services
  -> VWorld/Cesium rendering in SiteMapPanel
```

## Frontend

Key files:

- `ARR/frontend/src/design/DesignPage.tsx`
- `ARR/frontend/src/design/hooks/use-design-job.ts`
- `ARR/frontend/src/design/lib/api-client.ts`
- `ARR/frontend/src/design/components/SiteMapPanel.tsx`
- `ARR/frontend/src/design/lib/envelopes/sunlight.ts`

Important current behavior:

- Address/PNU input calls `loadSiteBoundary`.
- The returned resolved PNU must be used for `loadConstraints`.
- `setback_geometries` drives the VWorld/Cesium legal overlays.
- `daylight_diagonal_envelope` is now rendered in `SiteMapPanel`.
- Future legal QA must compare three views for the same backend response: plan view, Python/matplotlib section PNG, and VWorld/Cesium overlay. Do not treat a CLI pass as enough if the section or VWorld picture looks legally wrong.

## Backend

Key files:

- `ARR/backend/design/views.py`
- `ARR/backend/design/services/site_geometry.py`
- `ARR/backend/land/services/regulation_calculator.py`
- `ARR/backend/land/services/setback_geometry.py`
- `ARR/backend/land/services/road_frontage.py`
- `ARR/backend/land/services/datum/elevation_api.py`
- `ARR/backend/land/services/datum/calculator.py`

Important current behavior:

- `/design/site-boundary/` resolves address/PNU and fetches VWorld cadastral geometry.
- `/design/auto-constraints/` computes zones, regulation result, setback geometry, road frontage, and datum.
- Road frontage must pass only `roads_result["roads"]` into `compute_setback_lines`.
- Runtime datum uses converted GeoTIFF `D:/Data/NGII_DEM/seoul_dem.tif`, resolved to WSL `/mnt/d/Data/NGII_DEM/seoul_dem.tif`.
- `datum_result` intentionally separates `parcel_datum_m`, `road_datum_m`, `neighbor_datum_m`, and `neighbor_avg_datum_m`.
- North sunlight envelope uses `neighbor_avg_datum_m` as the §86 평균수평면 when available.
- Building mass and `daylight_diagonal_envelope` use the parcel §119 datum, not the north-sunlight neighbor average.
- `/design` no longer auto-renders the surrounding elevation grid by default because users confused it with the legal site datum plane.
- Section and VWorld renderers must label slopes as vertical:horizontal: 정북일조 `H/2` -> `H = 2x` -> `2:1`; 공동주택 채광사선 multiplier `2` -> `2:1`; front-road diagonal reference multiplier `1.5` -> `1.5:1`.
- VWorld datum display should follow the plan PNG output, not a grid: `대지 §119` marker at parcel weighted-sample basis, `도로레벨` at road centerline/sample basis, `인접대지레벨` at north shared-boundary/selected neighbor basis, and `§86 평균` between parcel and north-neighbor basis.
- Implemented in `/design` VWorld/Cesium: `SiteMapPanel` now builds datum markers from `datum_result.parcel_segments`, `road_samples`, and `neighbor_segments`; `datum-plane.ts` renders point/stem/label entities instead of the old default wide datum plane/grid display.
