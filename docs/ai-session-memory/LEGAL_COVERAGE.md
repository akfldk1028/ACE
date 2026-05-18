# Legal Coverage Status

This file is intentionally blunt: not every legal diagram in the user's references is implemented.

## Implemented Enough To Verify In `/design`

- Parcel boundary from VWorld cadastral geometry.
- NGII local DEM datum result for covered Seoul parcels.
- Adjacent-lot setback line.
- Road/building-line setback visualization from neighboring road parcels, with fallback heuristics.
- Corner cutoff visualization where regulation data says it applies.
- North sunlight envelope for applicable residential zones.
- Daylight diagonal envelope for `공동주택`.

## Not Fully Implemented

### Front Road Diagonal / 전면도로 사선제한

The reference image about front-road diagonal limits is not fully implemented.

Current code now renders a 3D front-road reference plane in `/design` from
`front_road_diagonal_profile`, `road_frontages`, and `datum_result`.

Important: this is a visual reference/context plane, not a complete current-law
hard constraint. When `road_diagonal_multiplier` is null, the frontend labels it
as `전면도로 참고` and draws it faintly/dashed. Use `?roadDiag=0` to hide it or
`?roadDiag=1` / `?layers=all` to emphasize it.

Still not fully implemented: the practical envelope from:

- opposite-side road boundary,
- road width,
- road center/level,
- site-vs-road relation,
- piloti relaxation,
- 가로구역별 최고높이 미지정 condition,
- and per-case diagram variants

is not modeled as a complete height envelope.

Do not claim this is complete.

### Datum Article 119 3m Segmentation

ARR computes datum using NGII DEM and weighted edge sampling.

Current improvement:

- `SLOPE_GT3M` no longer silently returns only a single weighted average.
- `split_bands` are returned in `datum_result` for covered steep parcels.
- CLI verifies this with `강남구 대치동 1028`.

Still incomplete:

- `split_bands` are DEM boundary-profile metadata, not true contour-clipped area polygons.
- Actual 3m area partition geometry must still be implemented before claiming full Article 119 compliance.

The user's statement is correct: if datum is wrong, every height envelope after it is suspect.

### Split Zoning

Multi-zone parcels are still treated mostly by strictest limits, not true area-ratio overlay subdivision.

### Building Line Numeric Source

Actual building-designation/limit line data is not extracted from district-unit plan geometry. Some visualization still uses fallback/default values.

## Correct Mental Model

Current implementation is a strong visualization prototype for parcel-level checks, not a legally complete architectural code checker.

For future legal review, require all three visual checks before saying a case is correct:

- Plan view: parcel, roads, adjacent lots, and legal offset lines.
- Section view: road level, parcel datum, adjacent-lot datum, §86 average plane, slope ratios, and sample mass pass/fail.
- VWorld/Cesium view: the same legal geometry projected on the real cadastral map.

2026-05-18 VWorld rendering update:

- `daylight_diagonal_envelope` is shown by default in `/design`, but it must be rendered as a sloped `polygon` with per-position heights, not as Cesium `wall`. The backend shape is boundary edge `H=0` + inward edge `H=distance*multiplier`; rendering those four points as a wall creates folded purple fence artifacts. Use `?daylight=0` to hide or `?daylight=detail` to emphasize.
- `front_road_diagonal_profile` has an opt-in compact 3D Cesium reference ribbon based on the widest detected road frontage and road datum; use `?roadDiag=1`.
- `sunlight_envelope` surface fill is off by default because the 10m threshold can create a legal plateau in the computed allowed volume, but the user-facing VWorld should read as vertical wall -> diagonal slope. Use `?surface=1` or `?surface=detail` only for debug. Keep the `north_setback` 2D legal line visible even when the 3D surface is hidden; note that `north_setback.geometry` can be a `FeatureCollection` of LineStrings.
- The API gate confirmed both bundled Gangnam cases return `front_road_diagonal_profile`, `road_frontages`, `daylight_diagonal_envelope`, `sunlight_envelope`, and `datum_result`.

Important daylight caveat:

- The current VWorld `daylight_diagonal_envelope` is only a reference/debug surface.
- Article 86(3) daylight checks require the actual mass wall with daylight windows and the perpendicular distance from that wall to the adjacent lot boundary, or the facing distance between buildings on the same site.
- Do not present a site-boundary-only purple plane as final legal compliance. The correct next implementation is mass-aware: selected mass footprint/wall orientation -> daylight-window wall candidates -> perpendicular distance rays -> pass/fail section and 3D clipped face.

Slope labels must be vertical:horizontal. 정북일조 `H/2` and 공동주택 채광사선 multiplier `2` are `2:1`, not `1:2`. This interpretation was user-confirmed after checking the law text: distance >= height/2 is equivalent to height <= distance*2. The section PNG should show equal x/y aspect and an explicit slope marker (`수평 1`, `수직 2`, `2:1`) on the line. A mismatch between Python PNG and VWorld means datum/geometry is suspect.

Next priority should be:

1. Finish datum correctness, especially true Article 119 `>3m` polygon partitioning.
2. Implement front-road diagonal / 가로구역 height envelope only after datum is trusted.
3. Add legal-case CLI checks per diagram type.
4. Only then tune VWorld rendering aesthetics.
