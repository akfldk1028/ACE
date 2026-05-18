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

Current code has `road_diagonal_*` fields in static regulation data, but the practical envelope from:

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

Slope labels must be vertical:horizontal. 정북일조 `H/2` and 공동주택 채광사선 multiplier `2` are `2:1`, not `1:2`. This interpretation was user-confirmed after checking the law text: distance >= height/2 is equivalent to height <= distance*2. The section PNG should show equal x/y aspect and an explicit slope marker (`수평 1`, `수직 2`, `2:1`) on the line. A mismatch between Python PNG and VWorld means datum/geometry is suspect.

Next priority should be:

1. Finish datum correctness, especially true Article 119 `>3m` polygon partitioning.
2. Implement front-road diagonal / 가로구역 height envelope only after datum is trusted.
3. Add legal-case CLI checks per diagram type.
4. Only then tune VWorld rendering aesthetics.
